# -*- coding: utf-8 -*-
"""Адаптер Telegram: только транспорт. Вся логика — в core.py."""

import os
import logging
from telebot import TeleBot, types
from telebot.apihelper import ApiTelegramException

import core

logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8874541127:AAFbpcvJLtzqylyiUxOkuozrShG3J_IQ9cs")
bot = TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")


def _make_keyboard(buttons: list[tuple[str, str]]) -> types.InlineKeyboardMarkup | None:
    if not buttons:
        return None
    kb = types.InlineKeyboardMarkup(row_width=1)
    for title, cb in buttons:
        kb.add(types.InlineKeyboardButton(title, callback_data=cb))
    return kb


def _safe_edit(call: types.CallbackQuery, text: str, keyboard):
    try:
        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard,
            disable_web_page_preview=False,
        )
    except ApiTelegramException as e:
        if "message is not modified" not in str(e):
            raise


@bot.message_handler(commands=["start"])
def cmd_start(message: types.Message):
    logger.info("Пользователь %s запустил бота", message.from_user.id)
    screen = core.get_welcome_screen()
    bot.send_message(
        message.chat.id,
        screen["text"],
        reply_markup=_make_keyboard(screen["buttons"]),
        disable_web_page_preview=True,
    )


@bot.message_handler(commands=["menu"])
def cmd_menu(message: types.Message):
    screen = core.get_main_menu()
    bot.send_message(
        message.chat.id,
        screen["text"],
        reply_markup=_make_keyboard(screen["buttons"]),
    )


@bot.message_handler(commands=["help"])
def cmd_help(message: types.Message):
    screen = core.get_help_screen()
    bot.send_message(
        message.chat.id,
        screen["text"],
        reply_markup=_make_keyboard(screen["buttons"]),
        disable_web_page_preview=True,
    )


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call: types.CallbackQuery):
    data = call.data
    try:
        if data == "menu":
            screen = core.get_main_menu()
        elif data == "help":
            screen = core.get_help_screen()
        elif data.startswith("item:"):
            path = data.split(":")[1:]
            screen = core.get_screen(path)
        else:
            bot.answer_callback_query(call.id, "Неизвестная команда")
            return

        _safe_edit(call, screen["text"], _make_keyboard(screen["buttons"]))
        bot.answer_callback_query(call.id)

    except Exception:
        logger.exception("Ошибка в callback")
        bot.answer_callback_query(call.id, "Произошла ошибка, попробуйте ещё раз")


@bot.message_handler(func=lambda m: True, content_types=["text"])
def handle_other(message: types.Message):
    screen = core.get_main_menu()
    bot.send_message(
        message.chat.id,
        "Пожалуйста, выберите раздел:",
        reply_markup=_make_keyboard(screen["buttons"]),
    )


def run():
    logger.info("Telegram-бот запущен...")
    bot.infinity_polling(skip_pending=True)

