import os

import reflex as rx
from dotenv import load_dotenv

from utils import scheduler as sched_mod

from .pages.run import run_page
from .pages.monitor import monitor_page
from .pages.log_page import log_page
from .pages.schedule_page import schedule_page
from .pages.history_detail import history_detail_page
from .state import AriaState
from .theme import BG, FONT_STACK, TEXT

# Boot side effects (load env, init scheduler) — same as old dashboard.
for env_path in ("/app/.env", os.path.join(os.path.dirname(__file__), "..", "..", ".env")):
    if os.path.exists(env_path):
        load_dotenv(env_path)
        break
sched_mod.init_scheduler()


PRETENDARD_LINK = (
    "https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css"
)


app = rx.App(
    style={
        "font_family": FONT_STACK,
        "background": BG,
        "color": TEXT,
        "min_height": "100vh",
    },
    stylesheets=[PRETENDARD_LINK],
)

app.add_page(run_page, route="/", title="ARIA", on_load=AriaState.on_load)
app.add_page(monitor_page, route="/monitor", title="ARIA · 모니터링", on_load=AriaState.on_load)
app.add_page(log_page, route="/log", title="ARIA · 로그", on_load=AriaState.on_load)
app.add_page(schedule_page, route="/schedule", title="ARIA · 스케줄", on_load=AriaState.on_load)
app.add_page(
    history_detail_page,
    route="/history/[hid]",
    title="ARIA · 히스토리",
    on_load=AriaState.load_history_detail,
)
