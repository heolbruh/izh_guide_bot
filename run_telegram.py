# -*- coding: utf-8 -*-
"""Точка входа Telegram."""
import logging
import telegram_adapter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

if __name__ == "__main__":
    telegram_adapter.run()