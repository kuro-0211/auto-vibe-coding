"""Project detail page — session timeline."""

from __future__ import annotations

import reflex as rx

from ..components.layout import layout, page_header
from ..state import AriaState
from ..theme import (
    ACCENT,
    BORDER,
    CARD_BG,
    FAIL,
    HINT,
    SUB,
    SUCCESS,
    TEXT,
    WARN,
)


def _project_summary() -> rx.Component:
    status_color = rx.match(
        AriaState.project_detail_status,
        ("completed", SUCCESS),
        ("paused", WARN),
        ACCENT,
    )
    status_bg = status_color.to_string() + "22"
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(
                    AriaState.project_detail_name,
                    font_size="15px",
                    font_weight="600",
                    color=TEXT,
                ),
                rx.spacer(),
                rx.box(
                    AriaState.project_detail_status_label,
                    font_size="11px",
                    font_weight="600",
                    padding="3px 12px",
                    border_radius="999px",
                    background=status_bg,
                    color=status_color,
                ),
                width="100%",
                align="center",
            ),
            rx.text(
                AriaState.project_detail_description,
                font_size="12px",
                color=SUB,
            ),
            rx.text(
                "생성 " + AriaState.project_detail_created + " · 수정 " + AriaState.project_detail_updated,
                font_size="11px",
                color=HINT,
            ),
            spacing="1",
            align="stretch",
        ),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_radius="12px",
        padding="16px",
        margin_bottom="14px",
        width="100%",
    )


def _action_buttons() -> rx.Component:
    return rx.grid(
        rx.button(
            "▶  이어서 작업",
            on_click=AriaState.continue_project_from_detail,
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
        rx.cond(
            AriaState.project_detail_status == "completed",
            rx.button(
                "🔁  진행중으로",
                on_click=AriaState.toggle_project_completed(AriaState.selected_project_detail_id),
                variant="outline",
                style={"width": "100%"},
            ),
            rx.button(
                "✅  완료 처리",
                on_click=AriaState.toggle_project_completed(AriaState.selected_project_detail_id),
                variant="outline",
                style={"width": "100%"},
            ),
        ),
        rx.cond(
            AriaState.project_detail_status == "paused",
            rx.button(
                "▶  재개",
                on_click=AriaState.toggle_project_paused(AriaState.selected_project_detail_id),
                variant="outline",
                style={"width": "100%"},
            ),
            rx.button(
                "⏸  중단",
                on_click=AriaState.toggle_project_paused(AriaState.selected_project_detail_id),
                variant="outline",
                style={"width": "100%"},
            ),
        ),
        columns="3",
        spacing="2",
        width="100%",
        margin_bottom="18px",
    )


def _session_card(s: rx.Var) -> rx.Component:
    stat_color = rx.cond(s.success, SUCCESS, FAIL)
    stat_label = rx.cond(s.success, "성공", "실패")
    header = (
        s.session_number.to_string()
        + "단계: "
        + s.preview
        + "  ·  "
        + s.created_at
    )

    exec_panel = rx.cond(
        s.has_exec,
        rx.cond(
            s.exec_ok,
            rx.vstack(
                rx.text(
                    "실행 성공 · "
                    + s.exec_elapsed.to_string()
                    + "s · "
                    + s.exec_lines.to_string()
                    + "줄",
                    font_size="12px",
                    color=SUCCESS,
                    font_weight="600",
                ),
                rx.code_block(s.exec_output, language="bash"),
                spacing="2",
                align="stretch",
            ),
            rx.vstack(
                rx.text("실행 실패", font_size="12px", color=FAIL, font_weight="600"),
                rx.code_block(s.exec_error, language="bash"),
                spacing="2",
                align="stretch",
            ),
        ),
        rx.text("실행 결과 없음", font_size="12px", color=HINT),
    )

    return rx.accordion.item(
        header=header,
        content=rx.vstack(
            rx.hstack(
                rx.box(
                    stat_label,
                    font_size="11px",
                    font_weight="600",
                    padding="3px 9px",
                    border_radius="999px",
                    background=stat_color.to_string() + "22",
                    color=stat_color,
                ),
                rx.box(
                    "세션 #" + s.session_number.to_string(),
                    font_size="11px",
                    font_weight="600",
                    padding="3px 9px",
                    border_radius="999px",
                    background="#f5f4ef",
                    color=TEXT,
                    border=f"1px solid rgba(0,0,0,0.06)",
                ),
                spacing="2",
            ),
            rx.tabs.root(
                rx.tabs.list(
                    rx.tabs.trigger("📄 결과", value="result"),
                    rx.tabs.trigger("🔍 리서치", value="research"),
                    rx.tabs.trigger("💻 코드", value="code"),
                    rx.tabs.trigger("🐳 실행", value="exec"),
                    rx.tabs.trigger("⚠️ 에러", value="err"),
                ),
                rx.tabs.content(
                    rx.cond(
                        s.final_output != "",
                        rx.markdown(s.final_output),
                        rx.text("최종 결과 없음", font_size="12px", color=HINT),
                    ),
                    value="result",
                ),
                rx.tabs.content(
                    rx.cond(
                        s.research_result != "",
                        rx.markdown(s.research_result),
                        rx.text("리서치 결과 없음", font_size="12px", color=HINT),
                    ),
                    value="research",
                ),
                rx.tabs.content(
                    rx.cond(
                        s.code_result != "",
                        rx.code_block(s.code_result, language="python"),
                        rx.text("코드 없음", font_size="12px", color=HINT),
                    ),
                    value="code",
                ),
                rx.tabs.content(exec_panel, value="exec"),
                rx.tabs.content(
                    rx.cond(
                        s.error_analysis != "",
                        rx.markdown(s.error_analysis),
                        rx.text("에러 분석 없음", font_size="12px", color=HINT),
                    ),
                    value="err",
                ),
                default_value="result",
            ),
            spacing="3",
            align="stretch",
        ),
        value="session_" + s.id.to_string(),
    )


def project_detail_page() -> rx.Component:
    body = rx.cond(
        AriaState.project_detail_exists,
        rx.vstack(
            page_header("프로젝트 상세", AriaState.project_detail_name),
            _project_summary(),
            _action_buttons(),
            rx.text(
                "📑 세션 타임라인",
                font_size="11px",
                font_weight="700",
                color=SUB,
                text_transform="uppercase",
                letter_spacing="0.06em",
                margin_bottom="8px",
            ),
            rx.cond(
                AriaState.has_sessions,
                rx.accordion.root(
                    rx.foreach(AriaState.sessions_view, _session_card),
                    type="multiple",
                    variant="ghost",
                    width="100%",
                ),
                rx.box(
                    rx.vstack(
                        rx.text("📭", font_size="24px"),
                        rx.text("아직 세션이 없습니다", font_size="13px", color=TEXT),
                        rx.text(
                            "'이어서 작업' 버튼으로 첫 세션을 만들어보세요.",
                            font_size="11px",
                            color=SUB,
                        ),
                        spacing="1",
                        align="center",
                    ),
                    background=CARD_BG,
                    border=f"1px solid {BORDER}",
                    border_radius="12px",
                    padding="32px 16px",
                    text_align="center",
                    width="100%",
                ),
            ),
            rx.box(height="14px"),
            rx.button(
                "←  프로젝트 목록",
                on_click=rx.redirect("/project"),
                variant="outline",
                style={"width": "100%"},
            ),
            spacing="0",
            width="100%",
        ),
        rx.vstack(
            page_header("프로젝트 상세", ""),
            rx.box(
                rx.text("선택된 프로젝트가 없습니다.", font_size="13px", color=TEXT),
                background=CARD_BG,
                border=f"1px solid {BORDER}",
                border_radius="12px",
                padding="24px",
                text_align="center",
                width="100%",
            ),
            rx.button(
                "←  프로젝트 목록",
                on_click=rx.redirect("/project"),
                variant="outline",
                style={"width": "100%", "margin_top": "12px"},
            ),
            spacing="0",
            width="100%",
        ),
    )
    return layout(body)
