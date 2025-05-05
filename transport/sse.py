import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional
from urllib.parse import quote
from uuid import UUID, uuid4
import json
import copy

import anyio
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from pydantic import ValidationError
from sse_starlette import EventSourceResponse
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Receive, Scope, Send
from mcp.server.sse import SseServerTransport

import mcp.types as types
from transport.types import JsonRpcRequest, JsonRpcMeta, JsonRpcParams
from services.session import SessionService
from database.db import services

logger = logging.getLogger(__name__)


class FastAPISseServerTransport(SseServerTransport):

    def __init__(self, endpoint: str) -> None:
        """
        Creates a new SSE server transport, which will direct the client to POST
        messages to the relative or absolute URL given.
        """
        super().__init__(endpoint)
        logger.debug(f"FastAPISseServerTransport initialized with endpoint: {endpoint}")

    @property
    def session_service(self) -> Optional[SessionService]:
        """获取会话服务"""
        return services.get("session_service")

    @asynccontextmanager
    async def connect_sse(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
        api_key: str = "",
    ):
        if scope["type"] != "http":
            logger.error("connect_sse received non-HTTP request")
            raise ValueError("connect_sse can only handle HTTP requests")

        read_stream: MemoryObjectReceiveStream[types.JSONRPCMessage | Exception]
        read_stream_writer: MemoryObjectSendStream[types.JSONRPCMessage | Exception]

        write_stream: MemoryObjectSendStream[types.JSONRPCMessage]
        write_stream_reader: MemoryObjectReceiveStream[types.JSONRPCMessage]

        read_stream_writer, read_stream = anyio.create_memory_object_stream(0)
        write_stream, write_stream_reader = anyio.create_memory_object_stream(0)

        session_id = uuid4()
        session_uri = f"{quote(self._endpoint)}?session_id={session_id.hex}"
        self._read_stream_writers[session_id] = read_stream_writer

        # 如果提供了API密钥，存储session_id和api_key的关系
        session_service = self.session_service
        if api_key and session_service:
            try:
                # 创建会话记录
                session = session_service.create_session(
                    api_key=api_key, session_id=session_id.hex
                )
                logger.debug(f"创建会话记录: session_id={session_id.hex}")
            except Exception as e:
                logger.error(f"存储会话关系失败: {e}")

        logger.debug(f"创建会话: ID={session_id.hex}")

        sse_stream_writer, sse_stream_reader = anyio.create_memory_object_stream[
            dict[str, Any]
        ](0)

        async def sse_writer():
            async with sse_stream_writer, write_stream_reader:
                await sse_stream_writer.send({"event": "endpoint", "data": session_uri})

                async for message in write_stream_reader:
                    await sse_stream_writer.send(
                        {
                            "event": "message",
                            "data": message.model_dump_json(
                                by_alias=True, exclude_none=True
                            ),
                        }
                    )

        async with anyio.create_task_group() as tg:
            response = EventSourceResponse(
                content=sse_stream_reader, data_sender_callable=sse_writer
            )
            tg.start_soon(response, scope, receive, send)

            yield (read_stream, write_stream)

            # 清理资源
            if session_id in self._read_stream_writers:
                logger.debug(f"清理会话资源: ID={session_id.hex}")
                del self._read_stream_writers[session_id]

    def _process_json_request(
        self, body: bytes, session_id: UUID, api_key: str
    ) -> types.JSONRPCMessage:
        """
        处理JSON请求，为tools/call方法添加会话信息

        Args:
            body: 原始请求体
            session_id: 会话ID
            api_key: API密钥

        Returns:
            处理后的JSONRPCMessage对象
        """
        try:
            # 解析JSON为字典
            json_data: Dict[str, Any] = json.loads(body)

            # 使用Pydantic模型解析
            request = JsonRpcRequest.model_validate(json_data)

            # 检查是否为tools/call方法或其他需要会话信息的方法
            if request.params is not None:
                # 添加会话信息到meta (会自动通过alias转换为_meta)
                meta = JsonRpcMeta(session_id=session_id.hex, api_key=api_key)
                # 保存原始meta中可能存在的其他字段
                if hasattr(request.params, "meta") and request.params.meta:
                    # 安全地更新session_id和api_key，保留其他字段
                    try:
                        if not hasattr(request.params.meta, "session_id") or request.params.meta.session_id is None:
                            request.params.meta.session_id = session_id.hex
                        if not hasattr(request.params.meta, "api_key") or request.params.meta.api_key is None:
                            request.params.meta.api_key = api_key
                    except AttributeError as e:
                        logger.debug(f"属性访问错误: {e}")
                        # 如果出现属性错误，创建新的meta对象
                        request.params.meta = meta
                else:
                    # 如果meta不存在，设置新的meta
                    request.params.meta = meta

            # 转换回JSONRPCMessage格式 (使用by_alias=True确保meta字段输出为_meta)
            modified_body = request.model_dump_json(by_alias=True).encode()

            # 使用修改后的JSON创建消息对象
            message = types.JSONRPCMessage.model_validate_json(modified_body)
            return message

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return types.JSONRPCMessage.model_validate_json(body)
        except ValidationError as e:
            logger.error(f"Pydantic验证失败: {e}")
            # 如果Pydantic验证失败，回退到原始方法
            return self._process_json_request_fallback(body, session_id, api_key)

    def _process_json_request_fallback(
        self, body: bytes, session_id: UUID, api_key: str
    ) -> types.JSONRPCMessage:
        """
        处理JSON请求的备用方法，用于处理与Pydantic模型不匹配的情况

        Args:
            body: 原始请求体
            session_id: 会话ID
            api_key: API密钥

        Returns:
            处理后的JSONRPCMessage对象
        """
        try:
            # 解析JSON为字典
            json_data = json.loads(body)

            # 创建修改后的JSON副本
            modified_json = copy.deepcopy(json_data)

            # 检查是否为tools/call方法
            if "method" in modified_json and modified_json["method"] == "tools/call":
                # 查找并修改_meta
                if "params" in modified_json and isinstance(
                    modified_json["params"], dict
                ):
                    params = modified_json["params"]

                    # 如果_meta不存在，创建它
                    if "_meta" not in params:
                        params["_meta"] = {}
                    elif not isinstance(params["_meta"], dict):
                        params["_meta"] = {}

                    # 添加session_id和api_key到_meta
                    params["_meta"]["session_id"] = session_id.hex
                    params["_meta"]["api_key"] = api_key

                    # 保存回原始结构
                    modified_json["params"] = params

            # 序列化回JSON
            modified_body = json.dumps(modified_json).encode()

            # 使用修改后的JSON创建消息对象
            return types.JSONRPCMessage.model_validate_json(modified_body)

        except Exception as e:
            logger.error(f"备用处理也失败: {e}")
            return types.JSONRPCMessage.model_validate_json(body)

    async def handle_post_message(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        request = Request(scope, receive)

        session_id_param = request.query_params.get("session_id")
        if session_id_param is None:
            logger.warning("缺少session_id参数")
            response = Response("session_id is required", status_code=400)
            return await response(scope, receive, send)

        try:
            session_id = UUID(hex=session_id_param)

            # 获取session_id关联的API密钥
            api_key = None
            session_service = self.session_service
            if session_service:
                try:
                    # 更新会话访问时间
                    session_service.update_session_access(session_id.hex)
                    
                    # 获取API密钥
                    api_key = session_service.get_api_key_by_session_id(session_id.hex)
                except Exception as e:
                    logger.error(f"获取API密钥时出错: {e}")
            else:
                logger.warning("会话服务未设置，无法获取API密钥")

        except ValueError:
            logger.warning(f"无效的session_id: {session_id_param}")
            response = Response("Invalid session ID", status_code=400)
            return await response(scope, receive, send)

        writer = self._read_stream_writers.get(session_id)
        if not writer:
            logger.warning(f"找不到会话: {session_id}")
            response = Response("Could not find session", status_code=404)
            return await response(scope, receive, send)

        body = await request.body()

        try:
            # 使用获取到的api_key作为path参数，如果获取失败则使用空字符串
            message = self._process_json_request(body, session_id, api_key or "")
        except ValidationError as err:
            logger.error(f"消息解析失败: {err}")
            response = Response("Could not parse message", status_code=400)
            await response(scope, receive, send)
            await writer.send(err)
            return
        except Exception as e:
            logger.error(f"处理请求时发生错误: {e}")
            response = Response(f"Internal server error: {str(e)}", status_code=500)
            await response(scope, receive, send)
            return

        response = Response("Accepted", status_code=202)
        await response(scope, receive, send)
        await writer.send(message)
