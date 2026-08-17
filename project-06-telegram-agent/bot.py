import asyncio
import logging
import os
import re
from typing import Optional

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from graph import process_user_message


load_dotenv()

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

TELEGRAM_MESSAGE_LIMIT = 3800


def clean_telegram_text(text: str) -> str:
    """Convert common Markdown formatting into safe plain Telegram text."""
    if not text:
        return "I could not generate a response. Please try again."

    cleaned = text.replace("**", "")
    cleaned = cleaned.replace("__", "")
    cleaned = cleaned.replace("`", "")
    return cleaned.strip()


def split_telegram_message(
    text: str,
    limit: int = TELEGRAM_MESSAGE_LIMIT,
) -> list[str]:
    """Split a long response into Telegram-safe message chunks."""
    text = text.strip()

    if not text:
        return ["No response was generated."]

    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    remaining = text

    while len(remaining) > limit:
        split_at = remaining.rfind("\n", 0, limit)

        if split_at < limit // 2:
            split_at = remaining.rfind(" ", 0, limit)

        if split_at < limit // 2:
            split_at = limit

        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()

    if remaining:
        chunks.append(remaining)

    return chunks


def get_username(update: Update) -> Optional[str]:
    """Return a safe display name for the Telegram user."""
    user = update.effective_user

    if user is None:
        return None

    return user.username or user.first_name


async def send_agent_response(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_message: str,
) -> None:
    """Send a user message to the LangGraph agent and return its response."""
    message = update.effective_message
    chat = update.effective_chat

    if message is None or chat is None:
        return

    await context.bot.send_chat_action(
        chat_id=chat.id,
        action=ChatAction.TYPING,
    )

    try:
        # Run the synchronous LangGraph workflow outside the async event loop.
        result = await asyncio.to_thread(
            process_user_message,
            user_message,
            str(chat.id),
            get_username(update),
        )

        response_text = clean_telegram_text(result.response)

        for chunk in split_telegram_message(response_text):
            await message.reply_text(chunk)

    except Exception:
        logger.exception("The Telegram agent failed to process a message.")

        await message.reply_text(
            "Sorry, I could not process your request right now. "
            "Please try again shortly."
        )


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
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
        "Send your question, or use /help to see examples."
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
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
        f"Check whether there is an active internet outage in {area}.",
    )


async def customer_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
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
    if not context.args:
        if update.effective_message:
            await update.effective_message.reply_text(
                "Usage: /signal -30.2"
            )
        return

    try:
        rx_power = float(context.args[0])
    except ValueError:
        if update.effective_message:
            await update.effective_message.reply_text(
                "Please provide a valid RX power value, such as /signal -30.2"
            )
        return

    await send_agent_response(
        update,
        context,
        f"Analyze the fiber RX power reading of {rx_power} dBm.",
    )


async def packages_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if context.args:
        category = " ".join(context.args)
        prompt = f"Show available {category} internet packages."
    else:
        prompt = "Show all available internet packages."

    await send_agent_response(update, context, prompt)


async def ticket_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if len(context.args) < 2:
        if update.effective_message:
            await update.effective_message.reply_text(
                "Usage: /ticket 80105 Internet is not working"
            )
        return

    customer_id = context.args[0]
    issue = " ".join(context.args[1:])

    await send_agent_response(
        update,
        context,
        (
            f"Create a support ticket for customer ID {customer_id}. "
            f"Issue reported by the customer: {issue}"
        ),
    )


async def text_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
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
    logger.error(
        "Unhandled Telegram update error",
        exc_info=context.error,
    )

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "An unexpected error occurred. Please try again."
            )
        except Exception:
            logger.exception("Could not send the Telegram error response.")


def build_application(token: str) -> Application:
    """Build and configure the Telegram application."""
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("outage", outage_command))
    application.add_handler(CommandHandler("customer", customer_command))
    application.add_handler(CommandHandler("signal", signal_command))
    application.add_handler(CommandHandler("packages", packages_command))
    application.add_handler(CommandHandler("ticket", ticket_command))

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_message,
        )
    )

    application.add_error_handler(error_handler)
    return application


def run_polling(application: Application) -> None:
    logger.info("Starting Telegram bot in polling mode.")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


def run_webhook(application: Application) -> None:
    webhook_url = os.getenv("WEBHOOK_URL", "").strip().rstrip("/")
    webhook_path = os.getenv(
        "TELEGRAM_WEBHOOK_PATH",
        "telegram",
    ).strip("/")

    secret_token = os.getenv(
        "TELEGRAM_WEBHOOK_SECRET",
        "",
    ).strip()

    port = int(os.getenv("PORT", "8000"))

    if not webhook_url:
        raise RuntimeError(
            "WEBHOOK_URL is required when BOT_MODE=webhook."
        )

    if not secret_token:
        raise RuntimeError(
            "TELEGRAM_WEBHOOK_SECRET is required in webhook mode."
        )

    if not re.fullmatch(r"[A-Za-z0-9_-]{1,256}", secret_token):
        raise RuntimeError(
            "TELEGRAM_WEBHOOK_SECRET may contain only letters, "
            "numbers, underscores, and hyphens."
        )

    logger.info("Starting Telegram bot in webhook mode.")

    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=webhook_path,
        webhook_url=f"{webhook_url}/{webhook_path}",
        secret_token=secret_token,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    mode = os.getenv("BOT_MODE", "demo").strip().lower()

    if mode == "demo" or not token:
        print("Telegram token unavailable. BOT_MODE=demo.")
        print("Run the Streamlit demonstration with:")
        print("py -3.12 -m streamlit run app.py")
        return

    application = build_application(token)

    if mode == "polling":
        run_polling(application)
    elif mode == "webhook":
        run_webhook(application)
    else:
        raise RuntimeError(
            "BOT_MODE must be demo, polling, or webhook."
        )


if __name__ == "__main__":
    main()