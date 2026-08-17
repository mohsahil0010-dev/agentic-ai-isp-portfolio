import asyncio
import logging
import os
import re
from typing import Optional

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.error import (
    InvalidToken,
    NetworkError,
    TimedOut,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from graph import process_user_message


load_dotenv()

TELEGRAM_MESSAGE_LIMIT = 3800

TELEGRAM_TOKEN_PATTERN = re.compile(
    r"(?<!\d)\d{6,}:[A-Za-z0-9_-]{20,}"
)


class RedactingFormatter(logging.Formatter):
    """Remove Telegram bot tokens from all terminal logs."""

    def format(
        self,
        record: logging.LogRecord,
    ) -> str:
        formatted_message = super().format(record)

        return TELEGRAM_TOKEN_PATTERN.sub(
            "[REDACTED_TELEGRAM_TOKEN]",
            formatted_message,
        )


def configure_logging() -> None:
    """Configure secure application logging."""
    console_handler = logging.StreamHandler()

    console_handler.setFormatter(
        RedactingFormatter(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        )
    )

    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler],
        force=True,
    )

    # HTTPX normally logs complete Telegram request URLs.
    logging.getLogger("httpx").setLevel(
        logging.WARNING
    )

    logging.getLogger("httpcore").setLevel(
        logging.WARNING
    )


configure_logging()
logger = logging.getLogger(__name__)


def clean_telegram_text(text: str) -> str:
    """Convert common Markdown into safe plain text."""
    if not text:
        return (
            "I could not generate a response. "
            "Please try again."
        )

    cleaned = text.replace("**", "")
    cleaned = cleaned.replace("__", "")
    cleaned = cleaned.replace("`", "")

    return cleaned.strip()


def split_telegram_message(
    text: str,
    limit: int = TELEGRAM_MESSAGE_LIMIT,
) -> list[str]:
    """Split long responses into Telegram-safe messages."""
    text = text.strip()

    if not text:
        return ["No response was generated."]

    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    remaining = text

    while len(remaining) > limit:
        split_at = remaining.rfind(
            "\n",
            0,
            limit,
        )

        if split_at < limit // 2:
            split_at = remaining.rfind(
                " ",
                0,
                limit,
            )

        if split_at < limit // 2:
            split_at = limit

        chunks.append(
            remaining[:split_at].strip()
        )

        remaining = remaining[
            split_at:
        ].strip()

    if remaining:
        chunks.append(remaining)

    return chunks


def get_username(
    update: Update,
) -> Optional[str]:
    """Return a safe Telegram user display name."""
    user = update.effective_user

    if user is None:
        return None

    return (
        user.username
        or user.first_name
    )


async def send_agent_response(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_message: str,
) -> None:
    """Process a Telegram message with LangGraph."""
    message = update.effective_message
    chat = update.effective_chat

    if message is None or chat is None:
        return

    await context.bot.send_chat_action(
        chat_id=chat.id,
        action=ChatAction.TYPING,
    )

    try:
        result = await asyncio.to_thread(
            process_user_message,
            user_message,
            str(chat.id),
            get_username(update),
        )

        response_text = clean_telegram_text(
            result.response
        )

        for chunk in split_telegram_message(
            response_text
        ):
            await message.reply_text(chunk)

    except Exception as error:
        logger.error(
            "Agent request failed: %s",
            type(error).__name__,
        )

        await message.reply_text(
            "Sorry, I could not process your request "
            "right now. Please try again shortly."
        )


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle the /start command."""
    del context

    message = update.effective_message

    if message is None:
        return

    await message.reply_text(
        "Welcome to SAHIL FIBER NET Assistant.\n\n"
        "I can help you with:\n"
        "• Customer account information\n"
        "• Internet outage checks\n"
        "• Fiber signal analysis\n"
        "• Internet packages\n"
        "• Connection troubleshooting\n"
        "• Support ticket creation\n\n"
        "Send your question, or use /help "
        "to see examples."
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle the /help command."""
    del context

    message = update.effective_message

    if message is None:
        return

    await message.reply_text(
        "Available commands:\n\n"
        "/outage Model Town\n"
        "/customer 80105\n"
        "/signal -30.2\n"
        "/packages\n"
        "/packages TW\n"
        "/ticket 80105 Internet is not working\n\n"
        "You can also ask normal questions, such as:\n"
        "Is there an active outage in Model Town?"
    )


async def outage_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle the /outage command."""
    if not context.args:
        if update.effective_message:
            await update.effective_message.reply_text(
                "Usage: /outage Model Town"
            )
        return

    area = " ".join(context.args)

    await send_agent_response(
        update,
        context,
        (
            "Check whether there is an active "
            f"internet outage in {area}."
        ),
    )


async def customer_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle the /customer command."""
    if not context.args:
        if update.effective_message:
            await update.effective_message.reply_text(
                "Usage: /customer 80105"
            )
        return

    customer_id = context.args[0]

    await send_agent_response(
        update,
        context,
        f"Look up customer ID {customer_id}.",
    )


async def signal_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle the /signal command."""
    if not context.args:
        if update.effective_message:
            await update.effective_message.reply_text(
                "Usage: /signal -30.2"
            )
        return

    try:
        rx_power = float(
            context.args[0]
        )
    except ValueError:
        if update.effective_message:
            await update.effective_message.reply_text(
                "Please provide a valid RX power "
                "value, such as /signal -30.2"
            )
        return

    await send_agent_response(
        update,
        context,
        (
            "Analyze the fiber RX power "
            f"reading of {rx_power} dBm."
        ),
    )


async def packages_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle the /packages command."""
    if context.args:
        provider = " ".join(
            context.args
        )

        prompt = (
            f"Show available {provider} "
            "internet packages."
        )
    else:
        prompt = (
            "Show all available internet packages."
        )

    await send_agent_response(
        update,
        context,
        prompt,
    )


async def ticket_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle the /ticket command."""
    if len(context.args) < 2:
        if update.effective_message:
            await update.effective_message.reply_text(
                "Usage: /ticket 80105 "
                "Internet is not working"
            )
        return

    customer_id = context.args[0]
    issue = " ".join(
        context.args[1:]
    )

    await send_agent_response(
        update,
        context,
        (
            "Create a support ticket for "
            f"customer ID {customer_id}. "
            f"Issue reported by the customer: {issue}"
        ),
    )


async def text_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle a normal Telegram text message."""
    message = update.effective_message

    if message is None or not message.text:
        return

    await send_agent_response(
        update,
        context,
        message.text.strip(),
    )


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle an unexpected Telegram update error."""
    error_name = (
        type(context.error).__name__
        if context.error
        else "UnknownError"
    )

    logger.error(
        "Unhandled Telegram update error: %s",
        error_name,
    )

    if (
        isinstance(update, Update)
        and update.effective_message
    ):
        try:
            await update.effective_message.reply_text(
                "An unexpected error occurred. "
                "Please try again."
            )
        except Exception as reply_error:
            logger.error(
                "Could not send error response: %s",
                type(reply_error).__name__,
            )


def build_application(
    token: str,
) -> Application:
    """Build the Telegram application with safe timeouts."""
    application = (
        Application.builder()
        .token(token)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .pool_timeout(10.0)
        .get_updates_connect_timeout(30.0)
        .get_updates_read_timeout(60.0)
        .get_updates_write_timeout(30.0)
        .get_updates_pool_timeout(10.0)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "help",
            help_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "outage",
            outage_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "customer",
            customer_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "signal",
            signal_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "packages",
            packages_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "ticket",
            ticket_command,
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            text_message,
        )
    )

    application.add_error_handler(
        error_handler
    )

    return application


def run_polling(
    application: Application,
) -> None:
    """Run the bot locally using polling."""
    logger.info(
        "Starting Telegram bot in polling mode."
    )

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        bootstrap_retries=5,
        timeout=30,
    )


def run_webhook(
    application: Application,
) -> None:
    """Run the bot using a production webhook."""
    webhook_url = os.getenv(
        "WEBHOOK_URL",
        "",
    ).strip().rstrip("/")

    webhook_path = os.getenv(
        "TELEGRAM_WEBHOOK_PATH",
        "telegram",
    ).strip("/")

    secret_token = os.getenv(
        "TELEGRAM_WEBHOOK_SECRET",
        "",
    ).strip()

    port = int(
        os.getenv(
            "PORT",
            "8000",
        )
    )

    if not webhook_url:
        raise RuntimeError(
            "WEBHOOK_URL is required when "
            "BOT_MODE=webhook."
        )

    if not secret_token:
        raise RuntimeError(
            "TELEGRAM_WEBHOOK_SECRET is required "
            "when BOT_MODE=webhook."
        )

    if not re.fullmatch(
        r"[A-Za-z0-9_-]{1,256}",
        secret_token,
    ):
        raise RuntimeError(
            "TELEGRAM_WEBHOOK_SECRET may contain "
            "only letters, numbers, underscores, "
            "and hyphens."
        )

    logger.info(
        "Starting Telegram bot in webhook mode."
    )

    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=webhook_path,
        webhook_url=(
            f"{webhook_url}/{webhook_path}"
        ),
        secret_token=secret_token,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        bootstrap_retries=5,
    )


def main() -> None:
    """Start the selected Telegram bot mode."""
    token = os.getenv(
        "TELEGRAM_BOT_TOKEN",
        "",
    ).strip()

    mode = os.getenv(
        "BOT_MODE",
        "demo",
    ).strip().lower()

    if mode == "demo" or not token:
        print(
            "Telegram token unavailable. "
            "BOT_MODE=demo."
        )

        print(
            "Run the Streamlit demonstration with:"
        )

        print(
            "py -3.12 -m streamlit run app.py"
        )

        return

    application = build_application(token)

    try:
        if mode == "polling":
            run_polling(application)

        elif mode == "webhook":
            run_webhook(application)

        else:
            raise RuntimeError(
                "BOT_MODE must be demo, polling, "
                "or webhook."
            )

    except InvalidToken:
        logger.error(
            "Telegram rejected the configured token. "
            "Generate a new token through BotFather."
        )

    except TimedOut:
        logger.error(
            "Telegram connection timed out. "
            "Check the VPN or network connection."
        )

    except NetworkError as error:
        logger.error(
            "Telegram network error: %s",
            type(error).__name__,
        )

    except RuntimeError as error:
        logger.error(
            "%s",
            error,
        )


if __name__ == "__main__":
    main()