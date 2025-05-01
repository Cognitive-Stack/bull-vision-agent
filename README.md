# Bull Vision Agent

A FastAPI application that integrates with Telegram using webhooks and OpenAI Agents SDK for AI-powered stock trading assistance, utilizing MCPHub for multiple MCP server management.

## Features

- Telegram bot integration with webhook support
- AI-powered stock analysis using OpenAI Agents SDK
- Multiple MCP server integration via MCPHub:
  - Stock news analysis
  - Volume wall detection
- Real-time stock data analysis
- Market news integration
- Conversation history tracking
- Trading context management
- MongoDB integration for data persistence

## Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app with MCPHub initialization
│   ├── api/
│   │   ├── __init__.py
│   │   └── telegram_webhook.py  # Telegram webhook endpoint
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── bot.py            # Bot instance and context management
│   │   ├── agent.py          # AI agent implementation with MCP servers
│   │   ├── context.py        # Conversation context and history
│   │   └── telegram_handler.py  # Process incoming messages
│   ├── core/
│   │   ├── __init__.py
│   │   └── settings.py   # Application settings
│   ├── models/
│   │   ├── __init__.py
│   │   └── news.py           # News data models
│   ├── services/
│   │   ├── __init__.py
│   │   └── mongodb_service.py # MongoDB operations
│   └── startup.py        # Startup events
```

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   poetry install
   ```

3. Copy `.env.example` to `.env` and fill in the required values:
   ```bash
   cp .env.example .env
   ```

4. Edit `.env` with your actual values:
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token from @BotFather
   - `TELEGRAM_WEBHOOK_URL`: The public URL where your bot will receive updates
   - `HOST` and `PORT`: Server configuration
   - `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key
   - `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint
   - `AZURE_OPENAI_DEPLOYMENT`: Your Azure OpenAI deployment name
   - `AZURE_OPENAI_API_VERSION`: Azure OpenAI API version
   - `MONGO_URI`: MongoDB connection string
   - `MONGO_DB`: MongoDB database name

## Running the Application

Start the server:
```bash
make run
```

## Webhook Setup

1. Make sure your server is publicly accessible
2. The webhook URL should be in the format: `https://your-domain.com/api/telegram/webhook`
3. The webhook will be automatically registered when the application starts

## Available Commands

- `/start` - Start the bot
- `/help` - Show help message

## Example Queries

You can ask the bot about:
- Stock analysis (e.g., "Analyze AAPL")
- Market news (e.g., "What's the latest news about Tesla?")
- Trading strategies (e.g., "What's your view on the current market?")
- Volume analysis (e.g., "Check volume patterns for MSFT")

## Development Commands

```bash
make install    # Install dependencies
make run       # Run the application
make test      # Run tests
make lint      # Run linters
make format    # Format the code
make clean     # Clean up generated files
make setup     # Setup development environment
make check     # Run all checks
```

## Documentation

For detailed instructions on:
1. Setting up the AI Chatbot with Telegram and OpenAI Agents SDK, see [init_telegram_openai_agent.md](init_telegram_openai_agent.md)
2. Using MCPHub with multiple MCP servers, see [create_telegram_chatbot_multi_mcp_server.md](create_telegram_chatbot_multi_mcp_server.md) 