import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, Message, User, CallbackQuery
from telegram.ext import ContextTypes
from app.services.telegram.handler import TelegramHandler
from app.bot.agent import BullVisionAgent

@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.text = "/start"
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 123
    update.callback_query = None
    return update

@pytest.fixture
def mock_callback_query():
    callback_query = MagicMock(spec=CallbackQuery)
    callback_query.message = MagicMock(spec=Message)
    callback_query.from_user = MagicMock(spec=User)
    callback_query.from_user.id = 123
    return callback_query

@pytest.fixture
def mock_context():
    return MagicMock(spec=ContextTypes.DEFAULT_TYPE)

@pytest.fixture
def handler():
    return TelegramHandler()

@pytest.mark.asyncio
async def test_handle_start_command(handler, mock_update):
    await handler._handle_start_command(mock_update)
    mock_update.message.reply_text.assert_called_once()
    assert "Welcome to Bull Vision Agent" in mock_update.message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_handle_portfolio_command(handler, mock_update):
    mock_update.message.text = "/portfolio"
    await handler.handle_command(mock_update, MagicMock())
    assert handler.portfolio_setup_states[123]['step'] == 'waiting_for_symbols'

@pytest.mark.asyncio
async def test_handle_profile_command(handler, mock_update):
    mock_update.message.text = "/profile"
    await handler.handle_command(mock_update, MagicMock())
    assert handler.profile_setup_states[123]['step'] == 'risk_tolerance'
    mock_update.message.reply_text.assert_called_once()

@pytest.mark.asyncio
async def test_process_portfolio_symbols(handler, mock_update):
    mock_update.message.text = "VNM, FPT, VIC"
    handler.portfolio_setup_states[123] = {'step': 'waiting_for_symbols'}
    
    await handler._process_portfolio_symbols(mock_update)
    
    assert handler.portfolio_setup_states[123]['step'] == 'waiting_for_weights'
    assert handler.portfolio_setup_states[123]['symbols'] == ['VNM', 'FPT', 'VIC']

@pytest.mark.asyncio
async def test_process_portfolio_weights(handler, mock_update):
    mock_update.message.text = "0.4, 0.3, 0.3"
    handler.portfolio_setup_states[123] = {
        'step': 'waiting_for_weights',
        'symbols': ['VNM', 'FPT', 'VIC']
    }
    
    with patch('app.services.telegram.handler.update_user_context') as mock_update_context:
        await handler._process_portfolio_weights(mock_update)
        
        mock_update_context.assert_called_once()
        assert 123 not in handler.portfolio_setup_states

@pytest.mark.asyncio
async def test_handle_message_without_portfolio(handler, mock_update):
    mock_update.message.text = "What's my portfolio performance?"
    with patch('app.services.telegram.handler.get_user_context') as mock_get_context:
        mock_get_context.return_value = None
        await handler.handle_message(mock_update, MagicMock())
        mock_update.message.reply_text.assert_called_with(
            "Please set up your portfolio first using /portfolio command."
        )

@pytest.mark.asyncio
async def test_handle_message_with_portfolio(handler, mock_update):
    mock_update.message.text = "What's my portfolio performance?"
    with patch('app.services.telegram.handler.get_user_context') as mock_get_context, \
         patch('app.services.telegram.handler.get_stock_context') as mock_get_stock_context, \
         patch('app.services.telegram.handler.BullVisionAgent') as mock_agent_class:
        mock_get_context.return_value = MagicMock(
            portfolio=MagicMock(weights={'VNM': 0.5, 'FPT': 0.5})
        )
        mock_get_stock_context.return_value = {'VNM': {'price': 100}, 'FPT': {'price': 200}}
        mock_agent = AsyncMock()
        mock_agent.run.return_value = 'Portfolio analysis'
        mock_agent_class.return_value = mock_agent
        
        await handler.handle_message(mock_update, MagicMock())
        mock_update.message.reply_text.assert_called_with('Portfolio analysis')

@pytest.mark.asyncio
async def test_handle_risk_tolerance_callback(handler, mock_callback_query):
    handler.profile_setup_states[123] = {'step': 'risk_tolerance'}
    mock_callback_query.data = 'moderate'
    
    await handler.handle_callback_query(mock_callback_query, MagicMock())
    
    assert handler.profile_setup_states[123]['risk_tolerance'] == 'moderate'
    mock_callback_query.message.edit_text.assert_called_once()

@pytest.mark.asyncio
async def test_handle_investment_horizon_callback(handler, mock_callback_query):
    handler.profile_setup_states[123] = {
        'step': 'investment_horizon',
        'risk_tolerance': 'moderate'
    }
    mock_callback_query.data = 'medium_term'
    
    await handler.handle_callback_query(mock_callback_query, MagicMock())
    
    assert handler.profile_setup_states[123]['investment_horizon'] == 'medium_term'
    mock_callback_query.message.edit_text.assert_called_once()

@pytest.mark.asyncio
async def test_handle_investment_goals_callback(handler, mock_callback_query):
    handler.profile_setup_states[123] = {
        'step': 'investment_goals',
        'risk_tolerance': 'moderate',
        'investment_horizon': 'medium_term'
    }
    mock_callback_query.data = 'growth'
    
    await handler.handle_callback_query(mock_callback_query, MagicMock())
    
    assert handler.profile_setup_states[123]['investment_goals'] == ['growth']
    mock_callback_query.message.edit_text.assert_called_once()

@pytest.mark.asyncio
async def test_handle_investment_goals_done(handler, mock_callback_query):
    handler.profile_setup_states[123] = {
        'step': 'investment_goals',
        'risk_tolerance': 'moderate',
        'investment_horizon': 'medium_term',
        'investment_goals': ['growth', 'value']
    }
    mock_callback_query.data = 'DONE'
    
    with patch('app.services.telegram.handler.update_user_context') as mock_update_context:
        await handler.handle_callback_query(mock_callback_query, MagicMock())
        
        mock_update_context.assert_called_once()
        assert 123 not in handler.profile_setup_states 