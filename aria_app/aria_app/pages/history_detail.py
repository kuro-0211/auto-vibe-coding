"""History detail page — show final / research / code / exec / error tabs."""

from __future__ import annotations

import reflex as rx

from ..components.layout import layout, page_header
from ..state import AriaState
from ..theme import (
    BORDER,
    CARD_BG,
    FAIL,
    SUB,
    SUCCESS,
    TEXT,
)


def _no_detail() -> rx.Component:
    return rx.box(
        rx.text("선택된 히스토리가 없습니다. 사이드바에서 항목을 선택해주세요.", color=SUB),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_radius="12px",
        padding="24px",
        width="100%",
    )


def _summary_card() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text(
                    AriaState.hd_user_input,
                    font_size="13px",
                    font_weight="600",
                    color=TEXT,
                ),
                rx.text(
                    AriaState.hd_created_at
                    + " · ⏱ "
                    + AriaState.hd_elapsed
                    + "s · 재시도 "
                    + AriaState.hd_retry.to_string()
                    + "회",
                    font_size="11px",
                    color=SUB,
                ),
                spacing="1",
                align="start",
            ),
            rx.spacer(),
            rx.cond(
                AriaState.hd_success,
                rx.box(
                    "✅ 성공",
                    font_size="11px",
                    font_weight="600",
                    padding="4px 12px",
                    border_radius="999px",
                    background=f"{SUCCESS}22",
                    color=SUCCESS,
                ),
                rx.box(
                    "❌ 실패",
                    font_size="11px",
                    font_weight="600",
                    padding="4px 12px",
                    border_radius="999px",
                    background=f"{FAIL}22",
                    color=FAIL,
                ),
            ),
            align="center",
            width="100%",
        ),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_radius="12px",
        padding="16px",
        margin_bottom="14px",
        width="100%",
    )


def _exec_tab_content() -> rx.Component:
    return rx.cond(
        AriaState.hd_exec_ok,
        rx.code_block(AriaState.hd_exec_output, language="bash"),
        rx.cond(
            AriaState.hd_exec_error != "",
            rx.code_block(AriaState.hd_exec_error, language="bash"),
            rx.text("실행 결과 없음", color=SUB, font_size="12px"),
        ),
    )


def history_detail_page() -> rx.Component:
    body = rx.cond(
        ~AriaState.hd_exists,
        rx.vstack(page_header("히스토리 상세", ""), _no_detail(), width="100%"),
        rx.vstack(
            page_header("히스토리 상세", ""),
            _summary_card(),
            rx.tabs.root(
                rx.tabs.list(
                    rx.tabs.trigger("📄 최종 결과", value="final"),
                    rx.tabs.trigger("🔍 리서치", value="research"),
                    rx.tabs.trigger("💻 코드", value="code"),
                    rx.tabs.trigger("🐳 실행 결과", value="exec"),
                    rx.tabs.trigger("⚠️ 에러 분석", value="err"),
                ),
                rx.tabs.content(
                    rx.cond(
                        AriaState.hd_final_output != "",
                        rx.markdown(AriaState.hd_final_output),
                        rx.text("최종 결과 없음", color=SUB, font_size="12px"),
                    ),
                    value="final",
                    padding_top="14px",
                ),
                rx.tabs.content(
                    rx.cond(
                        AriaState.hd_research != "",
                        rx.markdown(AriaState.hd_research),
                        rx.text("리서치 결과 없음", color=SUB, font_size="12px"),
                    ),
                    value="research",
                    padding_top="14px",
                ),
                rx.tabs.content(
                    rx.cond(
                        AriaState.hd_code != "",
                        rx.code_block(AriaState.hd_code, language="python"),
                        rx.text("코드 없음", color=SUB, font_size="12px"),
                    ),
                    value="code",
                    padding_top="14px",
                ),
                rx.tabs.content(
                    _exec_tab_content(),
                    value="exec",
                    padding_top="14px",
                ),
                rx.tabs.content(
                    rx.cond(
                        AriaState.hd_error_analysis != "",
                        rx.markdown(AriaState.hd_error_analysis),
                        rx.text("에러 분석 없음", color=SUB, font_size="12px"),
                    ),
                    value="err",
                    padding_top="14px",
                ),
                default_value="final",
                width="100%",
            ),
            rx.box(height="16px"),
            rx.text(
                "결과 다운로드",
                font_size="10px",
                font_weight="700",
                color=SUB,
                text_transform="uppercase",
                letter_spacing="0.06em",
                margin="18px 0 8px",
            ),
            rx.grid(
                rx.button("📄  PDF", on_click=AriaState.download_history_pdf, variant="outline"),
                rx.button("📝  Word", on_click=AriaState.download_history_docx, variant="outline"),
                rx.button("📋  Markdown", on_click=AriaState.download_history_md, variant="outline"),
                columns="3",
                spacing="2",
                width="100%",
            ),
            rx.box(height="14px"),
            rx.hstack(
                rx.button("✚  새 대화", on_click=AriaState.new_chat, variant="outline", style={"flex": "1"}),
                rx.button(
                    "🗑  히스토리 전체 삭제",
                    on_click=AriaState.clear_history_all,
                    variant="outline",
                    color=FAIL,
                    style={"flex": "1"},
                ),
                spacing="2",
                width="100%",
            ),
            spacing="0",
            width="100%",
        ),
    )
    return layout(body)
