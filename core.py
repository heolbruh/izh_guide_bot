# -*- coding: utf-8 -*-
"""Слой логики: чистые функции. Не знает про Telegram/MAX и про сеть."""

from data import DATA, WELCOME_TEXT, HELP_TEXT


def resolve_path(path: list[str]) -> dict | None:
    """Возвращает узел DATA по пути или None."""
    current = DATA
    for seg in path:
        if seg in current:
            current = current[seg]
        elif "items" in current and seg in current["items"]:
            current = current["items"][seg]
        else:
            return None
    return current


def get_screen(path: list[str]) -> dict:
    """
    Нейтральное описание экрана:
    {
        "text": "...",
        "buttons": [(title, callback_data), ...],
        "is_card": bool,
    }
    """
    node = resolve_path(path)
    if node is None:
        return {"text": "Раздел не найден", "buttons": [], "is_card": False}

    # Лист — карточка с текстом
    if isinstance(node, dict) and "text" in node:
        return {
            "text": node["text"],
            "buttons": _back_buttons(path),
            "is_card": True,
        }

    # Ветвь с одним элементом — сразу открываем карточку
    if "items" in node and len(node["items"]) == 1:
        child_key, child = next(iter(node["items"].items()))
        if "text" in child:
            return {
                "text": child["text"],
                "buttons": _back_buttons(path),
                "is_card": True,
            }

    # Ветвь — список подразделов
    buttons = []
    for key, child in node.get("items", {}).items():
        cb = "item:" + ":".join(path + [key])
        buttons.append((child["title"], cb))
    buttons.append(("🏠 В меню", "menu"))
    return {
        "text": f"{node.get('title', '')}\n\nВыберите:".strip(),
        "buttons": buttons,
        "is_card": False,
    }


def get_main_menu() -> dict:
    """Нейтральное описание главного меню."""
    return {
        "text": "🏠 <b>Главное меню</b>\n\nВыберите раздел:",
        "buttons": [
            ("🍽 Еда", "item:food"),
            ("🏛 Достопримечательности", "item:sights"),
            ("🎭 Развлечения", "item:entertainment"),
            ("📅 Афиша", "item:afisha:info"),
            ("🧭 Полезно туристу", "item:useful:info"),
            ("🚶 Экскурсии", "item:excursions:info"),
            ("🗺 Маршруты", "item:routes:info"),
            ("ℹ️ Помощь", "help"),
        ],
        "is_card": False,
    }


def get_welcome_screen() -> dict:
    """Экран приветствия (/start). Использует кнопки главного меню."""
    menu = get_main_menu()
    return {
        "text": WELCOME_TEXT,
        "buttons": menu["buttons"],
        "is_card": False,
    }


def get_help_screen() -> dict:
    return {
        "text": HELP_TEXT,
        "buttons": [("🏠 В меню", "menu")],
        "is_card": True,
    }


def _back_buttons(path: list[str]) -> list[tuple[str, str]]:
    back = "menu" if len(path) <= 1 else "item:" + ":".join(path[:-1])
    return [("⬅️ Назад", back), ("🏠 В меню", "menu")]