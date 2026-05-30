"""Left sidebar — logo, new chat, history, nav, metrics."""

from __future__ import annotations

import reflex as rx

from ..state import AriaState
from ..theme import (
    ACCENT,
    ACCENT_SOFT,
    BORDER,
    CARD_BG,
    HINT,
    SIDEBAR_BG,
    SUB,
    TEXT,
)


_SIDE_BTN_STYLE = {
    "background": "transparent",
    "color": TEXT,
    "border": "1px solid transparent",
    "font_size": "13px",
    "font_weight": "500",
    "text_align": "left",
    "justify_content": "flex-start",
    "padding": "8px 12px",
    "border_radius": "8px",
    "width": "100%",
    "_hover": {"background": "rgba(0,0,0,0.04)"},
}

_SIDE_BTN_ACTIVE_STYLE = {
    **_SIDE_BTN_STYLE,
    "background": ACCENT_SOFT,
    "color": ACCENT,
    "border": f"1px solid rgba(204,120,92,0.35)",
    "font_weight": "600",
}


def _section_label(text: str) -> rx.Component:
    return rx.box(
        text,
        font_size="10px",
        font_weight="700",
        color=SUB,
        text_transform="uppercase",
        letter_spacing="0.06em",
        padding="4px 16px 6px",
    )


def _divider() -> rx.Component:
    return rx.box(height="1px", background=BORDER, margin="10px 12px")


def _logo() -> rx.Component:
    return rx.hstack(
        rx.center(
            "A",
            width="28px",
            height="28px",
            border_radius="8px",
            background=ACCENT,
            color="white",
            font_size="14px",
            font_weight="700",
        ),
        rx.vstack(
            rx.text("ARIA", font_size="14px", font_weight="700", color=TEXT, line_height="1.1"),
            rx.text("v1.3 · Reflex UI", font_size="10px", color=SUB),
            align_items="start",
            spacing="0",
        ),
        spacing="2",
        padding="18px 16px 10px",
        align="center",
    )


def _history_item(item: rx.Var) -> rx.Component:
    return rx.button(
        rx.hstack(
            rx.text(item.dot, font_size="10px"),
            rx.text(item.preview, font_size="13px", color=TEXT, no_of_lines=1),
            spacing="2",
            align="center",
            width="100%",
        ),
        on_click=AriaState.open_history(item.id),
        variant="ghost",
        style=_SIDE_BTN_STYLE,
    )


def _history_header(entry: rx.Var) -> rx.Component:
    return rx.box(
        entry.group_label,
        font_size="10px",
        color=HINT,
        padding="6px 16px 2px",
        font_weight="600",
    )


def _history_section() -> rx.Component:
    return rx.vstack(
        _section_label("히스토리"),
        rx.cond(
            AriaState.history_items.length() == 0,
            rx.box(
                "아직 비어 있어요",
                font_size="12px",
                color=HINT,
                padding="4px 16px 12px",
            ),
            rx.foreach(
                AriaState.history_flat,
                lambda entry: rx.cond(
                    entry.kind == "header",
                    _history_header(entry),
                    _history_item(entry),
                ),
            ),
        ),
        spacing="0",
        width="100%",
        align_items="stretch",
        padding_x="6px",
    )


def _nav_button(icon: str, label: str, route: str, page_id: str) -> rx.Component:
    is_active = AriaState.router.page.path == route
    return rx.button(
        rx.hstack(
            rx.text(icon, font_size="14px"),
            rx.text(label, font_size="13px"),
            spacing="2",
            align="center",
            width="100%",
        ),
        on_click=rx.redirect(route),
        variant="ghost",
        style=rx.cond(is_active, _SIDE_BTN_ACTIVE_STYLE, _SIDE_BTN_STYLE),
    )


def _metric(label: str, value) -> rx.Component:
    return rx.box(
        rx.text(label, font_size="11px", color=SUB),
        rx.text(value, font_size="18px", font_weight="600", color=TEXT),
        background=CARD_BG,
        border=f"1px solid rgba(0,0,0,0.08)",
        border_radius="8px",
        padding="8px 12px",
        flex="1",
    )


def sidebar() -> rx.Component:
    return rx.vstack(
        _logo(),
        rx.box(
            rx.button(
                rx.hstack(rx.text("✚"), rx.text("새 대화"), spacing="2", align="center"),
                on_click=AriaState.new_chat,
                style={
                    "background": ACCENT_SOFT,
                    "color": ACCENT,
                    "border": "1px solid rgba(204,120,92,0.35)",
                    "border_radius": "8px",
                    "font_size": "13px",
                    "font_weight": "600",
                    "width": "100%",
                    "padding": "10px 12px",
                    "justify_content": "flex-start",
                    "_hover": {"background": "rgba(204,120,92,0.2)"},
                },
            ),
            padding="0 12px",
            width="100%",
        ),
        _divider(),
        _history_section(),
        _divider(),
        rx.vstack(
            _nav_button("📂", "프로젝트", "/project", "project"),
            _nav_button("📊", "모니터링", "/monitor", "monitor"),
            _nav_button("📝", "로그", "/log", "log"),
            _nav_button("⏰", "스케줄", "/schedule", "schedule"),
            spacing="1",
            width="100%",
            padding="0 6px",
        ),
        _divider(),
        rx.hstack(
            _metric("토큰", AriaState.token_count.to_string()),
            _metric("시간", AriaState.elapsed.to_string() + "s"),
            spacing="2",
            padding="0 12px",
            width="100%",
        ),
        rx.box(
            rx.text(
                "세션",
                font_size="10px",
                font_weight="700",
                color=HINT,
                text_transform="uppercase",
                letter_spacing="0.06em",
                margin_bottom="4px",
            ),
            rx.text(
                AriaState.short_session_id,
                font_size="10px",
                color=SUB,
                font_family="monospace",
                word_break="break-all",
            ),
            padding="10px 16px 14px",
        ),
        spacing="0",
        align_items="stretch",
        width="260px",
        min_width="260px",
        height="100vh",
        background=SIDEBAR_BG,
        border_right=f"1px solid {BORDER}",
        position="sticky",
        top="0",
        overflow_y="auto",
    )
