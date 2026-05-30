"""Run page — idle / phase1 / HITL / phase2 / done + sticky input bar."""

from __future__ import annotations

import reflex as rx

from ..components.layout import card, layout, page_header
from ..state import EXAMPLES, AriaState
from ..theme import (
    ACCENT,
    BG,
    BORDER,
    BORDER_SOFT,
    CARD_BG,
    CODE_BG,
    FAIL,
    HINT,
    SUB,
    SUCCESS,
    TEXT,
    WARN,
    WARN_BORDER,
    WARN_SOFT,
)


# ── pipeline status bar ─────────────────────────────────────
def _pipeline_chip(step: rx.Var) -> rx.Component:
    s = step.status
    bg = rx.cond(s == "done", f"{ACCENT}1f", rx.cond(s == "running", "rgba(204,120,92,0.10)", CODE_BG))
    color = rx.cond(s == "done", ACCENT, rx.cond(s == "running", TEXT, HINT))
    dot_bg = rx.cond(s == "done", ACCENT, rx.cond(s == "running", ACCENT, "#d4d4d0"))
    return rx.hstack(
        rx.box(width="6px", height="6px", border_radius="50%", background=dot_bg),
        rx.text(step.label, font_size="11px", font_weight="600"),
        spacing="1",
        align="center",
        padding="5px 10px",
        border_radius="999px",
        background=bg,
        color=color,
    )


def _pipeline_bar() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.foreach(AriaState.pipeline_steps, _pipeline_chip),
            spacing="1",
            wrap="wrap",
            justify="center",
            padding="0 4px 12px",
        ),
        width="100%",
    )


# ── input bar (bottom sticky) ───────────────────────────────
def _input_bar() -> rx.Component:
    options = rx.hstack(
        rx.hstack(
            rx.checkbox(
                checked=AriaState.send_email,
                on_change=AriaState.set_send_email,
                color_scheme="orange",
            ),
            rx.text("📧 이메일", font_size="13px", color=TEXT),
            spacing="2",
            align="center",
        ),
        rx.select(
            ["pdf", "docx", "md", "none"],
            value=AriaState.email_format,
            on_change=AriaState.set_email_format,
            size="2",
        ),
        spacing="3",
        align="center",
        margin_bottom="8px",
    )

    field = rx.hstack(
        rx.text_area(
            placeholder="키워드나 목적을 입력하세요... (예: FastAPI로 REST API 만들어줘)",
            value=AriaState.pending_input,
            on_change=AriaState.set_pending_input,
            rows="3",
            style={
                "background": CARD_BG,
                "color": TEXT,
                "border": f"1px solid rgba(0,0,0,0.14)",
                "border_radius": "12px",
                "font_size": "14px",
                "line_height": "1.55",
                "padding": "12px 14px",
                "resize": "none",
                "_focus": {
                    "border_color": ACCENT,
                    "box_shadow": "0 0 0 2px rgba(204,120,92,0.18)",
                },
            },
            flex="1",
        ),
        rx.button(
            "▶  실행",
            on_click=AriaState.submit_input,
            style={
                "background": ACCENT,
                "color": "white",
                "border_radius": "10px",
                "padding": "0 18px",
                "height": "44px",
                "font_size": "13px",
                "font_weight": "600",
                "align_self": "flex-end",
                "_hover": {"background": "#b86a4f"},
            },
        ),
        spacing="2",
        align="end",
        width="100%",
    )

    return rx.box(
        rx.cond(AriaState.is_idle, rx.fragment(), _pipeline_bar()),
        options,
        field,
        position="fixed",
        bottom="0",
        left="260px",
        right="0",
        background=f"linear-gradient(180deg, rgba(250,249,245,0.0) 0%, {BG} 22%)",
        padding="28px 24px 18px 24px",
        z_index="90",
        border_top=f"1px solid {BORDER_SOFT}",
    )


# ── project selector banner ────────────────────────────────
def _project_selector() -> rx.Component:
    selected_banner = rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(
                    "📂 프로젝트 이어서 작업",
                    font_size="11px",
                    font_weight="700",
                    color=ACCENT,
                    text_transform="uppercase",
                    letter_spacing="0.06em",
                ),
                rx.box(
                    AriaState.selected_project_status_label,
                    font_size="11px",
                    font_weight="600",
                    padding="2px 9px",
                    border_radius="999px",
                    background="rgba(204,120,92,0.18)",
                    color=ACCENT,
                ),
                spacing="2",
                align="center",
            ),
            rx.text(
                AriaState.selected_project_name,
                font_size="14px",
                font_weight="600",
                color=TEXT,
            ),
            rx.text(
                "이번이 "
                + AriaState.selected_project_next_n.to_string()
                + "번째 세션 · 마지막: "
                + AriaState.selected_project_last_input,
                font_size="11px",
                color=SUB,
            ),
            spacing="1",
            align="start",
        ),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_radius="12px",
        padding="14px 16px",
        margin_bottom="10px",
        width="100%",
    )
    selected_actions = rx.grid(
        rx.button(
            "📂  프로젝트 변경/관리",
            on_click=rx.redirect("/project"),
            variant="outline",
            style={"width": "100%"},
        ),
        rx.button(
            "✖  프로젝트 해제 (새 작업)",
            on_click=AriaState.clear_project,
            variant="outline",
            style={"width": "100%"},
        ),
        columns="2",
        spacing="2",
        width="100%",
        margin_bottom="16px",
    )
    empty_banner = rx.grid(
        rx.box(
            rx.vstack(
                rx.text(
                    "현재 모드",
                    font_size="11px",
                    font_weight="700",
                    color=SUB,
                    text_transform="uppercase",
                    letter_spacing="0.06em",
                ),
                rx.text(
                    "✨ 새 작업으로 실행 (프로젝트 없음)",
                    font_size="13px",
                    color=TEXT,
                ),
                spacing="1",
                align="start",
            ),
            background=CARD_BG,
            border=f"1px solid {BORDER}",
            border_radius="12px",
            padding="12px 14px",
        ),
        rx.button(
            "📂  프로젝트 선택해서 이어 실행",
            on_click=rx.redirect("/project"),
            variant="outline",
            style={"width": "100%", "height": "100%"},
        ),
        columns="2",
        spacing="2",
        width="100%",
        margin_bottom="16px",
    )
    return rx.cond(
        AriaState.has_selected_project,
        rx.vstack(selected_banner, selected_actions, spacing="0", width="100%"),
        empty_banner,
    )


# ── idle screen ─────────────────────────────────────────────
def _example_card(ex: str) -> rx.Component:
    return rx.button(
        rx.text(ex, font_size="13px", color=TEXT, text_align="left"),
        on_click=AriaState.use_example(ex),
        style={
            "background": CARD_BG,
            "border": f"1px solid {BORDER}",
            "border_radius": "12px",
            "padding": "14px 16px",
            "width": "100%",
            "justify_content": "flex-start",
            "text_align": "left",
            "height": "auto",
            "_hover": {"background": "#fafaf7"},
        },
    )


def _idle_view() -> rx.Component:
    return rx.vstack(
        rx.center(
            rx.vstack(
                rx.center(
                    "A",
                    width="60px",
                    height="60px",
                    border_radius="18px",
                    background=f"linear-gradient(135deg, {ACCENT}, #a85b40)",
                    color="white",
                    font_size="28px",
                    font_weight="700",
                ),
                rx.text(
                    "무엇을 도와드릴까요?",
                    font_size="24px",
                    font_weight="600",
                    color=TEXT,
                ),
                rx.text(
                    "키워드나 목적을 입력하면 리서치 · 코드 생성 · 실행까지 자동 처리해드립니다",
                    font_size="13px",
                    color=SUB,
                    text_align="center",
                ),
                spacing="3",
                align="center",
            ),
            padding="40px 0 28px",
            width="100%",
        ),
        rx.grid(
            *[_example_card(ex) for ex in EXAMPLES],
            columns="2",
            spacing="3",
            width="100%",
        ),
        spacing="2",
        width="100%",
    )


# ── running phase 1 (streaming research + code) ─────────────
def _running_phase1_view() -> rx.Component:
    return rx.vstack(
        rx.cond(
            AriaState.live_research != "",
            card(
                "리서치 결과",
                rx.box(
                    AriaState.live_research,
                    white_space="pre-wrap",
                    color=TEXT,
                    font_size="13px",
                ),
                icon="🔍",
                badge="진행 중",
                badge_color=ACCENT,
            ),
            rx.fragment(),
        ),
        rx.cond(
            AriaState.live_code != "",
            card(
                "생성된 코드",
                rx.code_block(
                    AriaState.live_code,
                    language="python",
                    show_line_numbers=False,
                ),
                icon="🦙",
                badge="생성",
                badge_color=ACCENT,
            ),
            rx.fragment(),
        ),
        rx.cond(
            (AriaState.live_research == "") & (AriaState.live_code == ""),
            rx.center(
                rx.spinner(size="3", color=ACCENT),
                padding="60px 0",
            ),
            rx.fragment(),
        ),
        width="100%",
        spacing="3",
    )


# ── HITL code review ───────────────────────────────────────
def _hitl_view() -> rx.Component:
    return rx.vstack(
        rx.cond(
            AriaState.has_research_for_review,
            card(
                "리서치 결과",
                rx.box(
                    AriaState.phase1_research_text,
                    white_space="pre-wrap",
                    color=TEXT,
                ),
                icon="🔍",
                badge="완료",
                badge_color=SUCCESS,
            ),
            rx.fragment(),
        ),
        rx.cond(
            AriaState.has_code_for_review,
            rx.vstack(
                rx.box(
                    rx.vstack(
                        rx.text(
                            "✏️ 코드 검토 및 수정",
                            font_size="13px",
                            font_weight="600",
                            color=WARN,
                        ),
                        rx.text(
                            "리뷰된 코드를 직접 편집할 수 있습니다. 수정 후 승인하면 편집한 코드로 실행됩니다.",
                            font_size="12px",
                            color=WARN,
                            opacity="0.85",
                        ),
                        spacing="1",
                        align="start",
                    ),
                    background=WARN_SOFT,
                    border=f"1px solid {WARN_BORDER}",
                    border_radius="12px",
                    padding="14px 16px",
                    margin_bottom="12px",
                    width="100%",
                ),
                rx.text_area(
                    value=AriaState.edited_code,
                    on_change=AriaState.set_edited_code,
                    rows="14",
                    style={
                        "font_family": "ui-monospace, monospace",
                        "font_size": "12.5px",
                        "background": CODE_BG,
                        "color": TEXT,
                        "border": f"1px solid {BORDER}",
                        "border_radius": "10px",
                        "padding": "12px 14px",
                        "width": "100%",
                    },
                ),
                rx.hstack(
                    rx.button(
                        "✅  승인 — 실행",
                        on_click=AriaState.approve_code,
                        style={
                            "background": ACCENT,
                            "color": "white",
                            "border_radius": "10px",
                            "padding": "10px 16px",
                            "font_size": "13px",
                            "font_weight": "600",
                            "flex": "1",
                            "_hover": {"background": "#b86a4f"},
                        },
                    ),
                    rx.button(
                        "🔄  원본 복원",
                        on_click=AriaState.restore_original_code,
                        style={
                            "background": CARD_BG,
                            "color": TEXT,
                            "border": f"1px solid {BORDER}",
                            "border_radius": "10px",
                            "padding": "10px 16px",
                            "font_size": "13px",
                            "flex": "1",
                            "_hover": {"background": "#f5f4ef"},
                        },
                    ),
                    rx.button(
                        "❌  거절 — 처음부터",
                        on_click=AriaState.reject_code,
                        style={
                            "background": CARD_BG,
                            "color": FAIL,
                            "border": f"1px solid {BORDER}",
                            "border_radius": "10px",
                            "padding": "10px 16px",
                            "font_size": "13px",
                            "flex": "1",
                            "_hover": {"background": "#f5f4ef"},
                        },
                    ),
                    spacing="2",
                    width="100%",
                ),
                width="100%",
                spacing="2",
            ),
            rx.fragment(),
        ),
        spacing="3",
        width="100%",
    )


# ── running phase 2 (exec + error analysis) ────────────────
def _running_phase2_view() -> rx.Component:
    return rx.vstack(
        rx.cond(
            AriaState.live_exec_has & AriaState.live_exec_ok,
            card(
                "실행 결과",
                rx.vstack(
                    rx.hstack(
                        rx.box(
                            f"⏱ ",
                            rx.text(AriaState.live_exec_elapsed.to_string() + "s", display="inline"),
                            font_size="11px",
                            background="rgba(76,175,80,0.18)",
                            color=SUCCESS,
                            padding="3px 9px",
                            border_radius="999px",
                            font_weight="600",
                        ),
                        rx.box(
                            f"📄 ",
                            rx.text(AriaState.live_exec_lines.to_string() + "줄", display="inline"),
                            font_size="11px",
                            background="rgba(76,175,80,0.18)",
                            color=SUCCESS,
                            padding="3px 9px",
                            border_radius="999px",
                            font_weight="600",
                        ),
                        spacing="2",
                    ),
                    rx.code_block(
                        "$ python solution.py\n" + AriaState.live_exec_output,
                        language="bash",
                    ),
                    spacing="2",
                    align="stretch",
                ),
                icon="🐳",
                badge="성공",
                badge_color=SUCCESS,
            ),
            rx.fragment(),
        ),
        rx.cond(
            AriaState.live_exec_has & ~AriaState.live_exec_ok,
            card(
                "실행 결과",
                rx.code_block(AriaState.live_exec_error, language="bash"),
                icon="🐳",
                badge="실패 — 재시도",
                badge_color=WARN,
            ),
            rx.fragment(),
        ),
        rx.cond(
            AriaState.live_error_analysis != "",
            card(
                "에러 분석",
                rx.box(
                    AriaState.live_error_analysis,
                    white_space="pre-wrap",
                    color=WARN,
                ),
                icon="⚠️",
                badge=AriaState.live_retry.to_string() + "/3",
                badge_color=WARN,
            ),
            rx.fragment(),
        ),
        rx.cond(
            ~AriaState.live_exec_has & (AriaState.live_error_analysis == ""),
            rx.center(rx.spinner(size="3", color=ACCENT), padding="60px 0"),
            rx.fragment(),
        ),
        spacing="3",
        width="100%",
    )


# ── final result ───────────────────────────────────────────
def _final_view() -> rx.Component:
    return rx.vstack(
        rx.cond(
            AriaState.final_exec_ok,
            rx.vstack(
                card(
                    "실행 결과",
                    rx.code_block(
                        "$ python solution.py\n" + AriaState.final_exec_output,
                        language="bash",
                    ),
                    icon="🐳",
                    badge="성공",
                    badge_color=SUCCESS,
                ),
                rx.cond(
                    AriaState.final_code_text != "",
                    rx.accordion.root(
                        rx.accordion.item(
                            header="💻  생성된 코드",
                            content=rx.code_block(AriaState.final_code_text, language="python"),
                            value="code",
                        ),
                        type="multiple",
                        variant="ghost",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    AriaState.final_output_text != "",
                    rx.accordion.root(
                        rx.accordion.item(
                            header="📄  최종 결과 문서",
                            content=rx.markdown(AriaState.final_output_text),
                            value="final",
                        ),
                        type="multiple",
                        default_value=["final"],
                        variant="ghost",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                spacing="2",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.cond(
            AriaState.final_exec_fail,
            rx.vstack(
                rx.cond(
                    AriaState.final_error_analysis != "",
                    card(
                        "에러 분석 결과 (" + AriaState.final_retry_count.to_string() + "회 시도)",
                        rx.box(
                            AriaState.final_error_analysis,
                            white_space="pre-wrap",
                            color=FAIL,
                        ),
                        icon="⚠️",
                        badge="실패",
                        badge_color=FAIL,
                    ),
                    card(
                        "실행 결과",
                        rx.code_block(AriaState.final_exec_error, language="bash"),
                        icon="🐳",
                        badge="실패 (" + AriaState.final_retry_count.to_string() + "회)",
                        badge_color=FAIL,
                    ),
                ),
                rx.cond(
                    AriaState.final_code_text != "",
                    rx.accordion.root(
                        rx.accordion.item(
                            header="💻  최종 생성된 코드",
                            content=rx.code_block(AriaState.final_code_text, language="python"),
                            value="code",
                        ),
                        type="multiple",
                        default_value=["code"],
                        variant="ghost",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                spacing="2",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.cond(
            ~AriaState.final_exec_ok & ~AriaState.final_exec_fail & (AriaState.final_output_text != ""),
            rx.accordion.root(
                rx.accordion.item(
                    header="📄  전체 결과 문서",
                    content=rx.markdown(AriaState.final_output_text),
                    value="final",
                ),
                type="multiple",
                default_value=["final"],
                variant="ghost",
                width="100%",
            ),
            rx.fragment(),
        ),
        # 리서치 결과는 final_output 안에 "# 참고 리서치" 섹션으로 포함되므로
        # 별도 아코디언으로 또 보여주지 않는다 (v1.3.1, Output Agent 템플릿화).
        rx.cond(
            AriaState.final_output_text != "",
            rx.vstack(
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
                    rx.button(
                        "📄  PDF",
                        on_click=AriaState.download_pdf,
                        variant="outline",
                        style={"width": "100%"},
                    ),
                    rx.button(
                        "📝  Word",
                        on_click=AriaState.download_docx,
                        variant="outline",
                        style={"width": "100%"},
                    ),
                    rx.button(
                        "📋  Markdown",
                        on_click=AriaState.download_md,
                        variant="outline",
                        style={"width": "100%"},
                    ),
                    columns="3",
                    spacing="2",
                    width="100%",
                ),
                spacing="2",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.box(height="14px"),
        rx.button(
            "✚  새 대화 시작",
            on_click=AriaState.new_chat,
            style={"width": "100%"},
            variant="outline",
        ),
        spacing="2",
        width="100%",
    )


def _error_banner() -> rx.Component:
    return rx.cond(
        AriaState.last_error != "",
        rx.box(
            rx.text("오류: " + AriaState.last_error, color=FAIL, font_size="13px"),
            background="rgba(239,83,80,0.08)",
            border=f"1px solid rgba(239,83,80,0.3)",
            border_radius="10px",
            padding="12px 14px",
            margin_bottom="12px",
        ),
        rx.fragment(),
    )


def run_page() -> rx.Component:
    body = rx.vstack(
        page_header("ARIA", AriaState.phase_label),
        _error_banner(),
        rx.cond(AriaState.is_idle, _project_selector(), rx.fragment()),
        rx.cond(AriaState.is_idle, _idle_view(), rx.fragment()),
        rx.cond(AriaState.is_running_phase1, _running_phase1_view(), rx.fragment()),
        rx.cond(AriaState.is_phase1_done, _hitl_view(), rx.fragment()),
        rx.cond(AriaState.is_running_phase2, _running_phase2_view(), rx.fragment()),
        rx.cond(AriaState.is_phase2_done, _final_view(), rx.fragment()),
        spacing="0",
        width="100%",
    )
    return rx.fragment(
        layout(body),
        _input_bar(),
    )
