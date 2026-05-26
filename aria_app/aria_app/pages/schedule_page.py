"""Schedule page — register and manage APScheduler routines."""

from __future__ import annotations

import reflex as rx

from ..components.layout import layout, page_header
from ..state import AriaState
from ..theme import (
    ACCENT,
    BORDER,
    CARD_BG,
    HINT,
    SUB,
    SUCCESS,
    TEXT,
)


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


def _section_label(text: str) -> rx.Component:
    return rx.text(
        text,
        font_size="11px",
        font_weight="700",
        color=SUB,
        text_transform="uppercase",
        letter_spacing="0.06em",
        margin_bottom="8px",
    )


def _new_schedule_form() -> rx.Component:
    return rx.vstack(
        rx.text_area(
            placeholder="예: 오늘의 AI 뉴스 정리해줘",
            value=AriaState.s_input,
            on_change=AriaState.set_s_input,
            rows="3",
            style={
                "background": CARD_BG,
                "border": f"1px solid rgba(0,0,0,0.14)",
                "border_radius": "10px",
                "font_size": "14px",
                "padding": "10px 12px",
                "color": TEXT,
            },
        ),
        rx.grid(
            rx.vstack(
                rx.text("실행 주기", font_size="11px", color=SUB, font_weight="600"),
                rx.select(
                    ["hourly", "daily", "weekly", "monthly"],
                    value=AriaState.s_frequency,
                    on_change=AriaState.set_s_frequency,
                ),
                spacing="1",
                align="stretch",
            ),
            rx.vstack(
                rx.text("첨부 형식", font_size="11px", color=SUB, font_weight="600"),
                rx.select(
                    ["pdf", "docx", "md", "none"],
                    value=AriaState.s_email_format,
                    on_change=AriaState.set_s_email_format,
                ),
                spacing="1",
                align="stretch",
            ),
            columns="2",
            spacing="3",
            width="100%",
        ),
        rx.cond(
            AriaState.s_frequency == "hourly",
            rx.input(
                type="number",
                value=AriaState.s_minute.to_string(),
                on_change=AriaState.set_s_minute,
                placeholder="분 (0-59)",
                min="0",
                max="59",
            ),
            rx.fragment(),
        ),
        rx.cond(
            AriaState.s_frequency == "daily",
            rx.grid(
                rx.input(
                    type="number",
                    value=AriaState.s_hour.to_string(),
                    on_change=AriaState.set_s_hour,
                    placeholder="시",
                    min="0",
                    max="23",
                ),
                rx.input(
                    type="number",
                    value=AriaState.s_minute.to_string(),
                    on_change=AriaState.set_s_minute,
                    placeholder="분",
                    min="0",
                    max="59",
                ),
                columns="2",
                spacing="2",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.cond(
            AriaState.s_frequency == "weekly",
            rx.grid(
                rx.select(
                    ["0", "1", "2", "3", "4", "5", "6"],
                    value=AriaState.s_day_of_week.to_string(),
                    on_change=AriaState.set_s_day_of_week,
                ),
                rx.input(
                    type="number",
                    value=AriaState.s_hour.to_string(),
                    on_change=AriaState.set_s_hour,
                    placeholder="시",
                    min="0",
                    max="23",
                ),
                rx.input(
                    type="number",
                    value=AriaState.s_minute.to_string(),
                    on_change=AriaState.set_s_minute,
                    placeholder="분",
                    min="0",
                    max="59",
                ),
                columns="3",
                spacing="2",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.cond(
            AriaState.s_frequency == "monthly",
            rx.grid(
                rx.input(
                    type="number",
                    value=AriaState.s_day.to_string(),
                    on_change=AriaState.set_s_day,
                    placeholder="일자 (1-31)",
                    min="1",
                    max="31",
                ),
                rx.input(
                    type="number",
                    value=AriaState.s_hour.to_string(),
                    on_change=AriaState.set_s_hour,
                    placeholder="시",
                    min="0",
                    max="23",
                ),
                rx.input(
                    type="number",
                    value=AriaState.s_minute.to_string(),
                    on_change=AriaState.set_s_minute,
                    placeholder="분",
                    min="0",
                    max="59",
                ),
                columns="3",
                spacing="2",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.hstack(
            rx.checkbox(
                checked=AriaState.s_send_email,
                on_change=AriaState.set_s_send_email,
                color_scheme="orange",
            ),
            rx.text("📧 이메일 자동 발송", font_size="13px", color=TEXT),
            spacing="2",
            align="center",
        ),
        rx.button(
            "✅  스케줄 등록",
            on_click=AriaState.submit_schedule,
            style={
                "background": ACCENT,
                "color": "white",
                "border_radius": "10px",
                "padding": "10px 16px",
                "font_size": "13px",
                "font_weight": "600",
                "width": "100%",
                "_hover": {"background": "#b86a4f"},
            },
        ),
        spacing="3",
        width="100%",
    )


def _schedule_card(s: rx.Var) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(
                    "#" + s.id.to_string(),
                    font_size="11px",
                    color=SUB,
                    font_weight="600",
                ),
                rx.text(
                    s.cycle,
                    font_size="13px",
                    color=TEXT,
                    font_weight="600",
                ),
                rx.spacer(),
                rx.cond(
                    s.enabled,
                    rx.box(
                        "활성",
                        font_size="11px",
                        font_weight="600",
                        padding="3px 9px",
                        border_radius="999px",
                        background=f"{SUCCESS}22",
                        color=SUCCESS,
                    ),
                    rx.box(
                        "정지",
                        font_size="11px",
                        font_weight="600",
                        padding="3px 9px",
                        border_radius="999px",
                        background="rgba(0,0,0,0.06)",
                        color=SUB,
                    ),
                ),
                spacing="2",
                align="center",
                width="100%",
            ),
            rx.text(
                s.preview,
                font_size="12px",
                color=SUB,
                no_of_lines=2,
            ),
            rx.hstack(
                rx.cond(
                    s.enabled,
                    rx.button(
                        "⏸  비활성화",
                        on_click=AriaState.toggle_schedule(s.id),
                        variant="outline",
                        style={"flex": "1"},
                    ),
                    rx.button(
                        "▶  활성화",
                        on_click=AriaState.toggle_schedule(s.id),
                        variant="outline",
                        style={"flex": "1"},
                    ),
                ),
                rx.button(
                    "🗑  삭제",
                    on_click=AriaState.remove_schedule(s.id),
                    variant="outline",
                    color=HINT,
                    style={"flex": "1"},
                ),
                spacing="2",
                width="100%",
            ),
            spacing="2",
            align="stretch",
        ),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_radius="12px",
        padding="14px 16px",
        margin_bottom="10px",
        width="100%",
    )


def schedule_page() -> rx.Component:
    body = rx.vstack(
        page_header("스케줄", "자동 실행 (Asia/Seoul)"),
        rx.hstack(
            _metric("등록", AriaState.schedule_count_total.to_string() + "건"),
            _metric("활성", AriaState.schedule_count_active.to_string() + "건"),
            _metric("스케줄러", AriaState.scheduler_status_label),
            spacing="2",
            width="100%",
        ),
        rx.box(height="1px", background=BORDER, margin="18px 0 12px", width="100%"),
        _section_label("➕ 새 스케줄 등록"),
        _new_schedule_form(),
        rx.box(height="1px", background=BORDER, margin="20px 0 12px", width="100%"),
        _section_label("📋 등록된 스케줄"),
        rx.cond(
            AriaState.schedule_rows.length() == 0,
            rx.box(
                rx.vstack(
                    rx.text("⏰", font_size="28px"),
                    rx.text("등록된 스케줄이 없습니다", font_size="13px", color=TEXT),
                    spacing="2",
                    align="center",
                ),
                background=CARD_BG,
                border=f"1px solid {BORDER}",
                border_radius="12px",
                padding="40px 16px",
                text_align="center",
                width="100%",
            ),
            rx.foreach(AriaState.schedule_rows, _schedule_card),
        ),
        spacing="0",
        width="100%",
    )
    return layout(body)
