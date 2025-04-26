# Bull Vision Agent

A FastAPI application that integrates with Telegram using webhooks and OpenAI Agents SDK for AI-powered stock trading assistance.

## Features

- Telegram bot integration with webhook support
- AI-powered stock analysis using OpenAI Agents SDK
- Real-time stock data using yfinance
- Market news integration
- Conversation history tracking
- Trading context management

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

## Development

The project structure is organized as follows:

```
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app initialization
│   ├── api/
│   │   ├── __init__.py
│   │   └── telegram_webhook.py  # Telegram webhook endpoint
│   └── startup.py        # Startup events: register Telegram webhook URL
├── bot/
│   ├── __init__.py
│   ├── bot.py            # Bot instance and context management
│   ├── agent.py          # Bull Vision agent implementation
│   ├── context.py        # Trading context and message history
│   └── telegram_handler.py  # Process incoming messages
```

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

For detailed instructions on setting up the AI Chatbot with Telegram and OpenAI Agents SDK, see [init_telegram_openai_agent.md](init_telegram_openai_agent.md). 