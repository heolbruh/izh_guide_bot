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


def _safe_edit(call: types.CallbackQuery, text: str, keyboard, photo_url: str = None):
    """
    Умное редактирование: если текущее сообщение не совпадает по типу (текст/фото) 
    с тем, что мы хотим показать, мы удаляем старое и отправляем новое.
    """
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    # Определяем, есть ли фото в ТЕКУЩЕМ сообщении
    current_has_photo = call.message.content_type in ['photo', 'video']
    
    # Сценарий 1: Мы хотим показать ФОТО
    if photo_url:
        if current_has_photo:
            # Текущее сообщение уже с фото — пытаемся просто заменить медиа
            try:
                bot.edit_message_media(
                    chat_id=chat_id,
                    message_id=message_id,
                    media=types.InputMediaPhoto(media=photo_url, caption=text, parse_mode="HTML"),
                    reply_markup=keyboard,
                )
                return
            except ApiTelegramException as e:
                # Если фото такое же или ошибка API, отправляем новое
                logger.warning("Не удалось обновить фото (возможно, оно не изменилось): %s", e)
        
        # Если текущее сообщение текстовое или обновить не удалось — шлем новое фото
        try:
            bot.send_photo(
                chat_id=chat_id,
                photo=photo_url,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
            # Удаляем старое сообщение
            try:
                bot.delete_message(chat_id, message_id)
            except:
                pass
            return
        except Exception as send_err:
            logger.error("Не удалось отправить фото: %s", send_err)
            # Если фото битое, отправим просто текст (fallback ниже)

    # Сценарий 2: Мы хотим показать ТЕКСТ
    if current_has_photo:
        # Текущее сообщение с фото, а мы хотим текст. 
        # Редактировать фото на текст НЕЛЬЗЯ. Отправляем новое сообщение и удаляем старое.
        try:
            bot.send_message(
                chat_id,
                text,
                reply_markup=keyboard,
                disable_web_page_preview=False,
            )
            try:
                bot.delete_message(chat_id, message_id)
            except:
                pass
            return
        except Exception as e:
            logger.error("Ошибка при отправке нового текста: %s", e)
    
    else:
        # Текущее сообщение текстовое, и мы хотим текст. 
        # Пытаемся отредактировать.
        try:
            bot.edit_message_text(
                text,
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=keyboard,
                disable_web_page_preview=False,
            )
        except ApiTelegramException as e:
            error_msg = str(e)
            if "message is not modified" in error_msg:
                pass # Текст не изменился, всё ок
            elif "message to edit not found" in error_msg:
                # Сообщение удалили, шлем новое
                bot.send_message(chat_id, text, reply_markup=keyboard)
            else:
                # Другая ошибка API (например, битый HTML)
                logger.error("Ошибка API при редактировании текста: %s", e)


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

        _safe_edit(call, screen["text"], _make_keyboard(screen["buttons"]), screen.get("photo"))
        bot.answer_callback_query(call.id)

    except Exception:
        logger.exception("Критическая ошибка в callback")
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
