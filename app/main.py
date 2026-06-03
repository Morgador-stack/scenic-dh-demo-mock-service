"""scenic-dh-demo-mock-service — 演示与假数据服务

竞赛演示兜底，避免依赖真实外部系统。提供一键演示脚本和 mock 数据。
"""

import logging
import sys
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("demo-mock")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("demo-mock-service starting on port 8006")
    yield

app = FastAPI(title="scenic-dh-demo-mock-service", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ═══════════════════════════════════
# Demo scenario state
# ═══════════════════════════════════
SCENARIO = {
    "id": "demo-lingshan-full",
    "name": "灵山胜境完整演示",
    "steps": [
        {"step": 1, "action": "create_session", "desc": "创建游客会话", "endpoint": "POST /v1/sessions"},
        {"step": 2, "action": "spot_list", "desc": "获取景点列表", "endpoint": "GET /v1/spots"},
        {"step": 3, "action": "spot_detail", "desc": "查看灵山大佛详情", "endpoint": "GET /v1/spots/LS-001"},
        {"step": 4, "action": "route_list", "desc": "获取推荐路线", "endpoint": "GET /v1/routes"},
        {"step": 5, "action": "arrival_ls001", "desc": "到达灵山大佛", "endpoint": "POST /v1/sessions/{id}/arrival-events"},
        {"step": 6, "action": "ask_question", "desc": "提问：大佛有多高", "endpoint": "POST /v1/sessions/{id}/messages"},
        {"step": 7, "action": "ask_question_2", "desc": "提问：梵宫有什么", "endpoint": "POST /v1/sessions/{id}/messages"},
        {"step": 8, "action": "arrival_ls003", "desc": "到达九龙灌浴", "endpoint": "POST /v1/sessions/{id}/arrival-events"},
        {"step": 9, "action": "submit_feedback", "desc": "提交反馈", "endpoint": "POST /v1/sessions/{id}/feedback"},
        {"step": 10, "action": "analytics_check", "desc": "查看运营数据", "endpoint": "GET /v1/analytics/overview"},
    ],
    "totalSteps": 10,
}

_demo_state = {
    "scenarioId": SCENARIO["id"],
    "currentStep": 0,
    "totalSteps": SCENARIO["totalSteps"],
    "status": "idle",
    "stepResult": None,
}

# Mock data generators
MOCK_DATA = {
    "weather": {"scenicId": "SA-001", "temperature": 26, "weather": "多云", "warning": None, "source": "mock"},
    "queues": {"spotId": "LS-001", "queueMinutes": 15, "crowdLevel": "medium", "source": "mock"},
    "crowd": {"activeSessions": 42, "totalVisitors": 1280, "hotSpots": ["LS-001", "LS-003", "LS-002"]},
    "tickets": {"items": [{"id": "TK-001", "name": "灵山成人票", "price": 210, "status": "available"}]},
    "locations": {"LS-001": {"lat": 31.4220, "lng": 120.1050}, "LS-002": {"lat": 31.4215, "lng": 120.1080}, "LS-003": {"lat": 31.4200, "lng": 120.1030}},
}


# ═══════════════════════════════════
# Helpers
# ═══════════════════════════════════
def _ok(data: dict, trace_id: str) -> dict:
    return {"code": 0, "message": "success", "data": data, "trace_id": trace_id}


# ═══════════════════════════════════
# Routes
# ═══════════════════════════════════
@app.get("/health")
def health():
    return _ok({"status": "ok", "version": "1.0.0"}, "startup")


# Demo control
@app.post("/v1/demo/reset")
def demo_reset():
    _demo_state["currentStep"] = 0
    _demo_state["status"] = "idle"
    _demo_state["stepResult"] = None
    return _ok({"reset": True, "scenarioId": SCENARIO["id"]}, "demo-reset")


@app.post("/v1/demo/start")
def demo_start():
    _demo_state["currentStep"] = 1
    _demo_state["status"] = "running"
    _demo_state["stepResult"] = SCENARIO["steps"][0]
    return _ok({"currentStep": 1, "step": SCENARIO["steps"][0]}, "demo-start")


@app.post("/v1/demo/next")
def demo_next():
    step = _demo_state["currentStep"]
    if step < SCENARIO["totalSteps"]:
        step += 1
        _demo_state["currentStep"] = step
        _demo_state["stepResult"] = SCENARIO["steps"][step - 1]
        _demo_state["status"] = "running"
    else:
        _demo_state["status"] = "done"
        _demo_state["stepResult"] = None
    return _ok(_demo_state, "demo-next")


@app.get("/v1/demo/current")
def demo_current():
    return _ok(_demo_state, "demo-current")


@app.post("/v1/demo/pause")
def demo_pause():
    _demo_state["status"] = "paused"
    return _ok({"paused": True, "atStep": _demo_state["currentStep"]}, "demo-pause")


# Mock data endpoints
@app.get("/v1/mock/weather")
def mock_weather(scenic_id: str = None):
    return _ok(MOCK_DATA["weather"], "mock-weather")


@app.get("/v1/mock/queues")
def mock_queues(spot_id: str = None):
    data = dict(MOCK_DATA["queues"])
    if spot_id:
        data["spotId"] = spot_id
    return _ok(data, "mock-queue")


@app.get("/v1/mock/crowd")
def mock_crowd():
    return _ok(MOCK_DATA["crowd"], "mock-crowd")


@app.get("/v1/mock/locations/{spot_id}")
def mock_location(spot_id: str):
    loc = MOCK_DATA["locations"].get(spot_id, {"lat": 31.42, "lng": 120.10})
    return _ok({"spotId": spot_id, "location": loc, "source": "mock"}, f"mock-loc-{spot_id}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
