# Bull Vision Agent

A FastAPI application that integrates with Telegram using webhooks.

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
poetry run uvicorn app.main:app --host $HOST --port $PORT
```

## Webhook Setup

1. Make sure your server is publicly accessible
2. The webhook URL should be in the format: `https://your-domain.com/api/telegram/webhook`
3. The webhook will be automatically registered when the application starts

## Available Commands

- `/start` - Start the bot
- `/help` - Show help message

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
│   └── telegram_handler.py  # Process incoming messages
``` 