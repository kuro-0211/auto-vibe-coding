"""Monitor page — agent flow + per-agent logs."""

from __future__ import annotations

import reflex as rx

from ..components.layout import layout, page_header
from ..state import AriaState
from ..theme import ACCENT, BORDER, CARD_BG, SUB, TEXT


def _empty_state() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text("📊", font_size="32px"),
            rx.text("아직 실행된 파이프라인이 없습니다", font_size="15px", font_weight="600", color=TEXT),
            rx.text("실행 탭에서 먼저 실행해주세요.", font_size="13px", color=SUB),
            spacing="2",
            align="center",
        ),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_radius="12px",
        padding="48px 16px",
        text_align="center",
        width="100%",
    )


def _agent_badge(name: rx.Var) -> rx.Component:
    return rx.box(
        name,
        font_size="11px",
        font_weight="600",
        padding="3px 10px",
        border_radius="999px",
        background="rgba(204,120,92,0.18)",
        color=ACCENT,
    )


def _log_item(log: rx.Var) -> rx.Component:
    return rx.accordion.item(
        header=log.agent + " — " + log.action,
        content=rx.box(
            log.content,
            font_size="13px",
            color=TEXT,
            line_height="1.65",
            white_space="pre-wrap",
        ),
        value=log.agent + "_" + log.action,
    )


def monitor_page() -> rx.Component:
    body = rx.vstack(
        page_header("모니터링", "에이전트 흐름 추적"),
        rx.cond(
            AriaState.agent_logs.length() == 0,
            _empty_state(),
            rx.vstack(
                rx.box(
                    rx.text(
                        "파이프라인 흐름",
                        font_size="10px",
                        font_weight="700",
                        color=SUB,
                        text_transform="uppercase",
                        letter_spacing="0.08em",
                        margin_bottom="10px",
                    ),
                    rx.hstack(
                        rx.foreach(
                            AriaState.agent_logs,
                            lambda l: _agent_badge(l.agent),
                        ),
                        spacing="1",
                        wrap="wrap",
                    ),
                    background=CARD_BG,
                    border=f"1px solid {BORDER}",
                    border_radius="12px",
                    padding="16px",
                    margin_bottom="14px",
                    width="100%",
                ),
                rx.accordion.root(
                    rx.foreach(AriaState.agent_logs, _log_item),
                    type="multiple",
                    variant="ghost",
                    width="100%",
                ),
                spacing="2",
                width="100%",
            ),
        ),
        spacing="0",
        width="100%",
    )
    return layout(body)
