"""Page shell — sidebar + main content column."""

from __future__ import annotations

import reflex as rx

from ..theme import ACCENT, BG, BORDER, CARD_BG, SUB, TEXT
from .sidebar import sidebar


def page_header(title: str, subtitle) -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.center(
                "A",
                width="24px",
                height="24px",
                border_radius="6px",
                background=ACCENT,
                color="white",
                font_size="12px",
                font_weight="700",
            ),
            rx.text(title, font_size="18px", font_weight="600", color=TEXT),
            spacing="2",
            align="center",
        ),
        rx.spacer(),
        rx.box(
            subtitle,
            font_size="11px",
            color=SUB,
            background=CARD_BG,
            padding="4px 12px",
            border_radius="999px",
            border=f"1px solid {BORDER}",
        ),
        width="100%",
        margin="8px 0 22px",
        align="center",
    )


def card(title: str, body: rx.Component, *, icon: str = "", badge=None, badge_color=ACCENT) -> rx.Component:
    head = rx.hstack(
        rx.text(
            f"{icon} {title}".strip(),
            font_size="10px",
            font_weight="700",
            color=SUB,
            text_transform="uppercase",
            letter_spacing="0.08em",
        ),
        rx.spacer(),
        rx.cond(
            badge is not None,
            rx.box(
                badge if badge is not None else "",
                font_size="11px",
                font_weight="600",
                padding="3px 10px",
                border_radius="999px",
                background=f"{badge_color}22",
                color=badge_color,
                border=f"1px solid {badge_color}44",
            ),
            rx.fragment(),
        ),
        width="100%",
        align="center",
    )
    return rx.box(
        head,
        rx.box(body, color=TEXT, font_size="13.5px", line_height="1.65", margin_top="10px"),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_radius="12px",
        padding="16px 18px",
        margin_bottom="14px",
        width="100%",
    )


def layout(content: rx.Component) -> rx.Component:
    return rx.hstack(
        sidebar(),
        rx.box(
            rx.box(
                content,
                max_width="860px",
                margin="0 auto",
                padding="24px 24px 220px 24px",
                width="100%",
            ),
            flex="1",
            min_height="100vh",
            background=BG,
        ),
        spacing="0",
        align="stretch",
        width="100%",
        min_height="100vh",
        background=BG,
    )
