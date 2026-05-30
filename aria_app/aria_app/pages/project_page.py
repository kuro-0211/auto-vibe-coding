"""Project list page — create project + manage list."""

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
    WARN,
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


def _new_project_form() -> rx.Component:
    return rx.vstack(
        rx.input(
            placeholder="프로젝트 이름 (예: 인증 서버 만들기)",
            value=AriaState.p_name,
            on_change=AriaState.set_p_name,
            style={
                "background": CARD_BG,
                "border": f"1px solid rgba(0,0,0,0.14)",
                "border_radius": "10px",
                "font_size": "14px",
                "padding": "10px 12px",
                "color": TEXT,
                "width": "100%",
            },
        ),
        rx.text_area(
            placeholder="설명 (선택) — 이 프로젝트의 목적을 한두 줄로 적어주세요",
            value=AriaState.p_description,
            on_change=AriaState.set_p_description,
            rows="2",
            style={
                "background": CARD_BG,
                "border": f"1px solid rgba(0,0,0,0.14)",
                "border_radius": "10px",
                "font_size": "14px",
                "padding": "10px 12px",
                "color": TEXT,
            },
        ),
        rx.button(
            "✅  생성",
            on_click=AriaState.submit_project,
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


def _status_badge(p: rx.Var) -> rx.Component:
    color = rx.match(
        p.status,
        ("completed", SUCCESS),
        ("paused", WARN),
        ACCENT,
    )
    return rx.box(
        p.status_label,
        font_size="11px",
        font_weight="600",
        padding="2px 9px",
        border_radius="999px",
        background=color.to_string() + "22",
        color=color,
    )


def _selected_badge(p: rx.Var) -> rx.Component:
    return rx.cond(
        p.is_selected,
        rx.box(
            "선택됨",
            font_size="11px",
            font_weight="600",
            padding="2px 9px",
            border_radius="999px",
            background="rgba(204,120,92,0.18)",
            color=ACCENT,
        ),
        rx.fragment(),
    )


def _project_card(p: rx.Var) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.text(p.name, font_size="14px", font_weight="600", color=TEXT),
                    _status_badge(p),
                    _selected_badge(p),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                rx.text(
                    p.session_count.to_string() + "단계 · 마지막 " + p.last_at,
                    font_size="11px",
                    color=SUB,
                ),
                spacing="2",
                align="center",
                width="100%",
            ),
            rx.text(p.description, font_size="12px", color=SUB, no_of_lines=2),
            rx.hstack(
                rx.button(
                    "▶  이어서 작업",
                    on_click=AriaState.select_project(p.id),
                    style={
                        "background": ACCENT,
                        "color": "white",
                        "border_radius": "10px",
                        "padding": "8px 12px",
                        "font_size": "12px",
                        "font_weight": "600",
                        "flex": "1",
                        "_hover": {"background": "#b86a4f"},
                    },
                ),
                rx.button(
                    "📑  세션 보기",
                    on_click=AriaState.view_project(p.id),
                    variant="outline",
                    style={"flex": "1"},
                ),
                rx.button(
                    "🗑  삭제",
                    on_click=AriaState.delete_project(p.id),
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
        border=rx.cond(p.is_selected, f"1px solid {ACCENT}", f"1px solid {BORDER}"),
        border_radius="12px",
        padding="14px 16px",
        margin_bottom="10px",
        width="100%",
    )


def project_page() -> rx.Component:
    body = rx.vstack(
        page_header("프로젝트", "멀티스텝 작업 관리"),
        _section_label("➕ 새 프로젝트 생성"),
        _new_project_form(),
        rx.box(height="1px", background=BORDER, margin="20px 0 12px", width="100%"),
        _section_label("📋 프로젝트 목록"),
        rx.cond(
            AriaState.has_projects,
            rx.foreach(AriaState.projects_view, _project_card),
            rx.box(
                rx.vstack(
                    rx.text("📂", font_size="28px"),
                    rx.text("아직 등록된 프로젝트가 없습니다", font_size="13px", color=TEXT),
                    rx.text(
                        "위에서 새 프로젝트를 생성해보세요.",
                        font_size="11px",
                        color=SUB,
                    ),
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
        ),
        spacing="0",
        width="100%",
    )
    return layout(body)
