# Using MCPHub with FastAPI

This guide explains how to properly integrate MCPHub with FastAPI applications, ensuring efficient server connection management and proper resource cleanup.

## Overview

MCPHub's `MCPServerStdio` requires careful connection management. The server connection should be maintained throughout the application's lifecycle and properly cleaned up during shutdown. This guide shows how to achieve this using FastAPI's lifespan management.

## MCP Server and Client Connection Details

### Server Initialization Process

The MCP server initialization involves several key steps:

1. **Server Creation**:
   ```python
   # When you call fetch_openai_mcp_server, it creates an MCPServerStdio instance
   server = await hub.fetch_openai_mcp_server(
       mcp_name="your-mcp-name",
       cache_tools_list=True
   )
   ```

2. **Connection Establishment**:
   - The server creates a subprocess using the specified command and arguments
   - It establishes stdio streams for communication
   - The server initializes a `ClientSession` to manage the connection

3. **Session Initialization**:
   ```python
   # Inside MCPServerStdio
   async def connect(self):
       # Create transport streams
       transport = await self.exit_stack.enter_async_context(self.create_streams())
       read, write = transport
       
       # Initialize client session
       session = await self.exit_stack.enter_async_context(ClientSession(read, write))
       await session.initialize()
       self.session = session
   ```

### Communication Protocol

1. **Message Exchange**:
   - The server and client communicate using JSON-RPC messages
   - Messages are sent through stdio streams (stdin/stdout)
   - Each message is encoded using the specified text encoding (default: utf-8)

2. **Tool Management**:
   ```python
   # Tools are cached for better performance
   async def list_tools(self) -> list[MCPTool]:
       if self.cache_tools_list and not self._cache_dirty and self._tools_list:
           return self._tools_list
       
       self._tools_list = (await self.session.list_tools()).tools
       return self._tools_list
   ```

3. **Tool Execution**:
   ```python
   # Tools are executed through the client session
   async def call_tool(self, tool_name: str, arguments: dict[str, Any] | None) -> CallToolResult:
       if not self.session:
           raise UserError("Server not initialized")
       return await self.session.call_tool(tool_name, arguments)
   ```

### Connection Lifecycle

1. **Startup Sequence**:
   ```python
   # 1. Create server instance
   server = MCPServerStdio(params)
   
   # 2. Connect to server
   await server.connect()
   
   # 3. Initialize session
   await server.session.initialize()
   
   # 4. Cache tools (if enabled)
   await server.list_tools()
   ```

2. **Active State**:
   - The server maintains an active connection
   - Tools can be listed and executed
   - Messages are exchanged through the stdio streams

3. **Cleanup Sequence**:
   ```python
   # 1. Close session
   await server.session.close()
   
   # 2. Close transport streams
   await server.exit_stack.aclose()
   
   # 3. Clean up resources
   server.session = None
   ```

### Error Handling

1. **Connection Errors**:
   ```python
   try:
       await server.connect()
   except Exception as e:
       logger.error(f"Connection error: {e}")
       await server.cleanup()
       raise
   ```

2. **Tool Execution Errors**:
   ```python
   try:
       result = await server.call_tool("tool_name", arguments)
   except Exception as e:
       logger.error(f"Tool execution error: {e}")
       # Handle error appropriately
   ```

3. **Cleanup Errors**:
   ```python
   try:
       await server.cleanup()
   except Exception as e:
       logger.error(f"Cleanup error: {e}")
       # Log error but don't raise to prevent masking other errors
   ```

### Best Practices for Connection Management

1. **Connection Pooling**:
   - Maintain a single server connection throughout the application's lifecycle
   - Share the connection across requests using FastAPI's app state
   - Avoid creating new connections for each request

2. **Resource Management**:
   - Use context managers (`async with`) for proper resource cleanup
   - Implement proper error handling at each stage
   - Log important events and errors

3. **Performance Optimization**:
   - Enable tool caching with `cache_tools_list=True`
   - Reuse the same server instance across requests
   - Monitor connection health and implement reconnection logic if needed

4. **Monitoring and Debugging**:
   - Log connection events (startup, shutdown, errors)
   - Monitor tool execution times
   - Track connection health metrics

## Implementation Steps

### 1. Application Setup

Create your FastAPI application with a lifespan manager:

```python
from fastapi import FastAPI
from mcphub import MCPHub
from contextlib import asynccontextmanager
from loguru import logger

# Initialize MCPHub
hub = MCPHub()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        # Create and maintain MCP server connection
        async with hub.fetch_openai_mcp_server(
            mcp_name="your-mcp-name",
            cache_tools_list=True
        ) as server:
            # Store server in app state
            app.state.mcp_server = server
            logger.info("MCP server initialized")
            
            # Initialize other components
            yield
            
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
    finally:
        # Cleanup
        logger.info("Shutting down MCP server")

app = FastAPI(
    title="Your App",
    lifespan=lifespan
)
```

### 2. Server Dependency

Create a dependency to access the MCP server:

```python
from fastapi import Depends, Request

async def get_mcp_server(request: Request):
    """Dependency to get the MCP server from app state"""
    return request.app.state.mcp_server
```

### 3. Route Implementation

Use the server dependency in your routes:

```python
from fastapi import APIRouter, Depends
from bot.agent import run_with_server

router = APIRouter()

@router.post("/your-endpoint")
async def your_handler(
    request: Request,
    server = Depends(get_mcp_server)
):
    try:
        # Use the server for your operations
        result = await run_with_server(
            input_text="your input",
            context=your_context,
            server=server
        )
        return result
    except Exception as e:
        logger.error(f"Error in handler: {str(e)}")
        raise
```

### 4. Agent Implementation

Implement your agent to work with the provided server:

```python
async def create_agent_with_server(server):
    """Create agent with the provided server"""
    return await create_your_agent(server)

async def run_with_server(input_text: str, context: YourContext, server):
    """Run the agent with the provided server"""
    agent = await create_agent_with_server(server)
    return await Runner.run(
        starting_agent=agent,
        input=input_text,
        context=context
    )
```

## Key Points

1. **Server Lifecycle Management**:
   - The MCP server connection is maintained throughout the application's lifetime
   - The connection is automatically cleaned up when the application shuts down
   - The server is accessible via the app state

2. **Resource Efficiency**:
   - Single server connection shared across all requests
   - No need to create new connections for each request
   - Proper cleanup ensures no resource leaks

3. **Error Handling**:
   - Proper error handling during server initialization
   - Graceful shutdown of server connections
   - Logging of important events and errors

4. **Best Practices**:
   - Use FastAPI's dependency injection for server access
   - Implement proper error handling and logging
   - Keep the server connection in the app state
   - Use the lifespan manager for proper resource management

## Common Issues and Solutions

1. **Server Connection Issues**:
   - Ensure the MCP server is properly initialized in the lifespan
   - Check that the server is accessible via the app state
   - Verify that the server connection is maintained

2. **Resource Cleanup**:
   - Make sure the server connection is properly closed during shutdown
   - Implement proper error handling in the lifespan manager
   - Log any issues during cleanup

3. **Performance Considerations**:
   - Use `cache_tools_list=True` for better performance
   - Share the server connection across requests
   - Implement proper error handling to prevent resource leaks

## Example Implementation

For a complete example, see the Bull Vision Agent implementation:
- `app/main.py`: Application setup with lifespan management
- `app/api/telegram_webhook.py`: Route implementation with server dependency
- `bot/agent.py`: Agent implementation with server integration
- `bot/telegram_handler.py`: Message handling with server usage

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MCPHub Documentation](https://github.com/openai/mcphub)
- [OpenAI Agents SDK Documentation](https://github.com/openai/agents) 