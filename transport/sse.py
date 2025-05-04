import logging
from contextlib import asynccontextmanager
from typing import Any, Dict
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

logger = logging.getLogger(__name__)


class FastAPISseServerTransport(SseServerTransport):

    _session_paths: dict[UUID, str]

    def __init__(self, endpoint: str) -> None:
        """
        Creates a new SSE server transport, which will direct the client to POST
        messages to the relative or absolute URL given.
        """
        super().__init__(endpoint)
        self._session_paths = {}
        logger.debug(f"FastAPISseServerTransport initialized with endpoint: {endpoint}")

    @asynccontextmanager
    async def connect_sse(self, scope: Scope, receive: Receive, send: Send, path: str = ""):
        if scope["type"] != "http":
            logger.error("connect_sse received non-HTTP request")
            raise ValueError("connect_sse can only handle HTTP requests")

        logger.debug("Setting up SSE connection")
        print(f"设置SSE连接，路径为: {path}")
        read_stream: MemoryObjectReceiveStream[types.JSONRPCMessage | Exception]
        read_stream_writer: MemoryObjectSendStream[types.JSONRPCMessage | Exception]

        write_stream: MemoryObjectSendStream[types.JSONRPCMessage]
        write_stream_reader: MemoryObjectReceiveStream[types.JSONRPCMessage]

        read_stream_writer, read_stream = anyio.create_memory_object_stream(0)
        write_stream, write_stream_reader = anyio.create_memory_object_stream(0)

        session_id = uuid4()
        session_uri = f"{quote(self._endpoint)}?session_id={session_id.hex}"
        self._read_stream_writers[session_id] = read_stream_writer
        self._session_paths[session_id] = path
        print(f"创建会话: ID={session_id.hex}, 路径={path}")
        print(f"会话路径字典: {len(self._session_paths)}项")
        logger.debug(f"Created new session with ID: {session_id}, path: {path}")

        sse_stream_writer, sse_stream_reader = anyio.create_memory_object_stream[
            dict[str, Any]
        ](0)

        async def sse_writer():
            logger.debug("Starting SSE writer")
            async with sse_stream_writer, write_stream_reader:
                await sse_stream_writer.send({"event": "endpoint", "data": session_uri})
                logger.debug(f"Sent endpoint event: {session_uri}")

                async for message in write_stream_reader:
                    logger.debug(f"Sending message via SSE: {message}")
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
            logger.debug("Starting SSE response task")
            tg.start_soon(response, scope, receive, send)

            logger.debug("Yielding read and write streams")
            yield (read_stream, write_stream)
            
            # 清理资源
            if session_id in self._read_stream_writers:
                logger.debug(f"Cleaning up resources for session: {session_id}")
                print(f"清理会话资源: ID={session_id.hex}")
                del self._read_stream_writers[session_id]
                if session_id in self._session_paths:
                    print(f"清理会话路径: ID={session_id.hex}, 路径={self._session_paths[session_id]}")
                    del self._session_paths[session_id]
                print(f"清理后会话路径字典: {len(self._session_paths)}项")

    def _process_json_request(self, body: bytes, session_id: UUID, path: str) -> types.JSONRPCMessage:
        """
        处理JSON请求，为tools/call方法添加会话信息
        
        Args:
            body: 原始请求体
            session_id: 会话ID
            path: 会话路径
            
        Returns:
            处理后的JSONRPCMessage对象
        """
        try:
            # 解析JSON为字典
            json_data: Dict[str, Any] = json.loads(body)
            print(f"原始请求JSON: {json_data}")
            
            # 使用Pydantic模型解析
            request = JsonRpcRequest.model_validate(json_data)
            
            # 检查是否为tools/call方法
            if request.method == "tools/call" and request.params is not None:
                print("检测到tools/call方法")
                
                # 添加会话信息到meta (会自动通过alias转换为_meta)
                meta = JsonRpcMeta(
                    session_id=session_id.hex,
                    path=path
                )
                request.params.meta = meta
                
                print(f"已添加session_id和path到meta: {meta.model_dump()}")
            
            # 转换回JSONRPCMessage格式 (使用by_alias=True确保meta字段输出为_meta)
            modified_body = request.model_dump_json(by_alias=True).encode()
            print(f"修改后的请求体: {modified_body}")
            
            # 使用修改后的JSON创建消息对象
            message = types.JSONRPCMessage.model_validate_json(modified_body)
            print("成功创建修改后的消息对象")
            return message
            
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return types.JSONRPCMessage.model_validate_json(body)
        except ValidationError as e:
            print(f"Pydantic验证失败，使用原始请求: {e}")
            # 如果Pydantic验证失败，回退到原始方法
            return self._process_json_request_fallback(body, session_id, path)
    
    def _process_json_request_fallback(self, body: bytes, session_id: UUID, path: str) -> types.JSONRPCMessage:
        """
        处理JSON请求的备用方法，用于处理与Pydantic模型不匹配的情况
        
        Args:
            body: 原始请求体
            session_id: 会话ID
            path: 会话路径
            
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
                if "params" in modified_json and isinstance(modified_json["params"], dict):
                    params = modified_json["params"]
                    
                    # 如果_meta不存在，创建它
                    if "_meta" not in params:
                        params["_meta"] = {}
                    elif not isinstance(params["_meta"], dict):
                        params["_meta"] = {}
                    
                    # 添加session_id和path到_meta
                    params["_meta"]["session_id"] = session_id.hex
                    params["_meta"]["path"] = path
                    
                    # 保存回原始结构
                    modified_json["params"] = params
            
            # 序列化回JSON
            modified_body = json.dumps(modified_json).encode()
            
            # 使用修改后的JSON创建消息对象
            return types.JSONRPCMessage.model_validate_json(modified_body)
            
        except Exception as e:
            print(f"备用处理也失败: {e}")
            return types.JSONRPCMessage.model_validate_json(body)

    async def handle_post_message(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        logger.debug("Handling POST message")
        request = Request(scope, receive)

        session_id_param = request.query_params.get("session_id")
        print(f"原始session_id_param: {session_id_param}")
        print(f"当前会话字典中的所有ID: {[sid.hex for sid in self._session_paths.keys()]}")

        if session_id_param is None:
            logger.warning("Received request without session_id")
            response = Response("session_id is required", status_code=400)
            return await response(scope, receive, send)

        try:
            session_id = UUID(hex=session_id_param)
            logger.debug(f"Parsed session ID: {session_id}")
            print(f"session_id: {session_id}")
            print(f"session_id_to_path: {self._get_session_path(session_id)}")
        except ValueError:
            logger.warning(f"Received invalid session ID: {session_id_param}")
            response = Response("Invalid session ID", status_code=400)
            return await response(scope, receive, send)

        writer = self._read_stream_writers.get(session_id)
        if not writer:
            logger.warning(f"Could not find session for ID: {session_id}")
            response = Response("Could not find session", status_code=404)
            return await response(scope, receive, send)

        path = self._session_paths.get(session_id, "")
        logger.debug(f"Session {session_id} associated with path: {path}")

        body = await request.body()
        logger.debug(f"Received JSON: {body}")

        try:
            message = self._process_json_request(body, session_id, path)
        except ValidationError as err:
            logger.error(f"Failed to parse message: {err}")
            response = Response("Could not parse message", status_code=400)
            await response(scope, receive, send)
            await writer.send(err)
            return

        logger.debug(f"Sending message to writer: {message}")
        response = Response("Accepted", status_code=202)
        await response(scope, receive, send)
        await writer.send(message)

    def _get_session_path(self, session_id: UUID | str) -> str:
        """
        根据会话ID获取关联的路径
        
        Args:
            session_id: 会话ID (可以是UUID对象或十六进制字符串)
            
        Returns:
            与会话ID关联的路径，如果会话ID不存在则返回空字符串
        """
        if isinstance(session_id, str):
            try:
                session_id = UUID(hex=session_id)
            except ValueError:
                return ""
                
        return self._session_paths.get(session_id, "")
