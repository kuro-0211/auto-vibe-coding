import os
import io
import re
from datetime import datetime
from dotenv import load_dotenv
load_dotenv("/app/.env")
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from utils.logger import pipeline_logger

OUTPUT_DIR = "/app/data/outputs"


def run_output(state: dict) -> str:
    pipeline_logger.log_step("Output Agent", "running")

    llm = ChatOllama(
        model=os.getenv("GEMMA_MODEL", "gemma3:4b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
        temperature=0.3
    )

    research = state.get("research_result", "")
    code = state.get("code_result", "")
    execution = state.get("execution_result")
    retry_count = state.get("retry_count", 0)

    if execution and isinstance(execution, dict):
        if execution.get("success"):
            exec_summary = f"실행 성공\n{execution.get('output', '')}"
        else:
            exec_summary = f"실행 실패 ({retry_count}회 시도)\n{execution.get('error', '')}"
    else:
        exec_summary = "코드 실행 없음"

    prompt = f"""
다음 내용을 바탕으로 최종 결과 문서를 작성해주세요.

## 리서치 결과
{research}

## 생성된 코드
{code if code else "코드 생성 없음"}

## 실행 결과
{exec_summary}

## 출력 형식
# 결과 요약
(핵심 내용 3~5줄)

## 리서치 내용
(정리된 내용)

## 코드
(생성된 코드, 있는 경우)

## 실행 결과
(실행 결과, 있는 경우)

한국어로 작성하세요.
"""

    response = llm.invoke([HumanMessage(content=prompt)])

    pipeline_logger.log_llm(
        model="gemma3:4b",
        prompt=prompt,
        response=response.content,
        tokens=0
    )
    pipeline_logger.log_step("Output Agent", "done", output_data=response.content)

    return response.content


def _ensure_output_dir() -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return OUTPUT_DIR


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def export_to_pdf(content: str, code: str = "", filename: str | None = None) -> bytes:
    """마크다운 텍스트를 PDF 바이트로 변환."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # 한글 폰트 등록 (시스템에 설치된 나눔고딕 사용)
    font_candidates = [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ]
    font_path = next((p for p in font_candidates if os.path.exists(p)), None)
    if font_path:
        pdf.add_font("Korean", "", font_path, uni=True)
        body_font = "Korean"
    else:
        body_font = "Helvetica"

    pdf.set_font(body_font, size=11)
    w = pdf.epw  # effective page width

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            pdf.set_font(body_font, size=16)
            pdf.multi_cell(w=w, h=9, text=stripped[2:])
            pdf.ln(2)
            pdf.set_font(body_font, size=11)
        elif stripped.startswith("## "):
            pdf.set_font(body_font, size=13)
            pdf.multi_cell(w=w, h=8, text=stripped[3:])
            pdf.ln(1)
            pdf.set_font(body_font, size=11)
        elif stripped.startswith("### "):
            pdf.set_font(body_font, size=12)
            pdf.multi_cell(w=w, h=7, text=stripped[4:])
            pdf.set_font(body_font, size=11)
        else:
            pdf.multi_cell(w=w, h=6, text=line if line else " ")

    if code:
        pdf.add_page()
        pdf.set_font(body_font, size=13)
        pdf.multi_cell(w=w, h=8, text="생성된 코드")
        pdf.ln(2)
        pdf.set_font(body_font, size=9)
        for line in code.splitlines():
            pdf.multi_cell(w=w, h=5, text=line if line else " ")

    output = pdf.output(dest="S")
    # fpdf2는 bytearray 또는 str을 반환 — bytes로 통일
    if isinstance(output, str):
        return output.encode("latin-1")
    return bytes(output)


def export_to_docx(content: str, code: str = "") -> bytes:
    """마크다운 텍스트를 Word(docx) 바이트로 변환."""
    from docx import Document
    from docx.shared import Pt

    doc = Document()

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            doc.add_heading(stripped[2:], level=1)
        elif stripped.startswith("## "):
            doc.add_heading(stripped[3:], level=2)
        elif stripped.startswith("### "):
            doc.add_heading(stripped[4:], level=3)
        elif stripped.startswith("- "):
            doc.add_paragraph(stripped[2:], style="List Bullet")
        elif stripped == "":
            doc.add_paragraph("")
        else:
            doc.add_paragraph(line)

    if code:
        doc.add_heading("생성된 코드", level=2)
        p = doc.add_paragraph()
        run = p.add_run(code)
        run.font.name = "Courier New"
        run.font.size = Pt(9)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def save_output_file(content: str, code: str = "", fmt: str = "pdf") -> str:
    """파일로 저장하고 경로 반환 (이메일 첨부용)."""
    _ensure_output_dir()
    fmt = fmt.lower()
    ts = _timestamp()

    if fmt == "pdf":
        data = export_to_pdf(content, code)
        path = os.path.join(OUTPUT_DIR, f"aria_result_{ts}.pdf")
    elif fmt in ("docx", "word"):
        data = export_to_docx(content, code)
        path = os.path.join(OUTPUT_DIR, f"aria_result_{ts}.docx")
    elif fmt in ("md", "markdown"):
        data = content.encode("utf-8")
        path = os.path.join(OUTPUT_DIR, f"aria_result_{ts}.md")
    else:
        raise ValueError(f"지원하지 않는 형식: {fmt}")

    with open(path, "wb") as f:
        f.write(data)
    return path
