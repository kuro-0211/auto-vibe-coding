"""Log page — LLM call history with token totals."""

from __future__ import annotations

import reflex as rx

from ..components.layout import layout, page_header
from ..state import AriaState
from ..theme import BORDER, CARD_BG, SUB, TEXT


def _metric(label: str, value) -> rx.Component:
    return rx.box(
        rx.text(label, font_size="11px", color=SUB),
        rx.text(value, font_size="22px", font_weight="600", color=TEXT),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_radius="12px",
        padding="12px 16px",
        flex="1",
    )


def _log_item(log: rx.Var) -> rx.Component:
    header_text = (
        "["
        + log.time
        + "]  "
        + log.model
        + " — "
        + log.tokens.to_string()
        + " tokens"
    )
    return rx.accordion.item(
        header=header_text,
        content=rx.vstack(
            rx.text("프롬프트", font_weight="600", font_size="12px", color=SUB),
            rx.code_block(log.prompt, language="log"),
            rx.text("응답", font_weight="600", font_size="12px", color=SUB),
            rx.code_block(log.response, language="log"),
            spacing="2",
            align="stretch",
        ),
        value=log.time,
    )


def log_page() -> rx.Component:
    body = rx.vstack(
        page_header("로그", "LLM 호출 내역"),
        rx.hstack(
            _metric("학교 API 토큰", AriaState.token_count.to_string()),
            _metric("로컬 LLM 호출", AriaState.llm_log_local.to_string() + "회"),
            _metric("총 호출", AriaState.llm_log_total.to_string() + "회"),
            spacing="2",
            width="100%",
        ),
        rx.box(height="1px", background=BORDER, margin="18px 0 12px", width="100%"),
        rx.cond(
            AriaState.llm_logs.length() == 0,
            rx.box(
                rx.vstack(
                    rx.text("📝", font_size="32px"),
                    rx.text("아직 실행된 로그가 없습니다", font_weight="600", color=TEXT),
                    spacing="2",
                    align="center",
                ),
                background=CARD_BG,
                border=f"1px solid {BORDER}",
                border_radius="12px",
                padding="48px 16px",
                text_align="center",
                width="100%",
            ),
            rx.accordion.root(
                rx.foreach(AriaState.llm_logs, _log_item),
                type="multiple",
                variant="ghost",
                width="100%",
            ),
        ),
        spacing="0",
        width="100%",
    )
    return layout(body)
