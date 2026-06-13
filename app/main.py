"""scenic-dh-demo-mock-service — 演示与假数据服务

竞赛演示兜底，避免依赖真实外部系统。提供一键演示脚本和 mock 数据。
"""

import uuid
import time
import logging
import sys
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format='{"time":"%(asctime)s","level":"%(levelname)s","service":"demo-mock","message":"%(message)s"}',
)
logger = logging.getLogger("demo-mock")


class TraceMiddleware(BaseHTTPMiddleware):
    """为每个请求注入 trace_id，从上游继承或新建"""

    async def dispatch(self, request: Request, call_next):
        trace_id = request.headers.get("x-trace-id", f"trace_{uuid.uuid4().hex}")
        span_id = str(uuid.uuid4())[:8]

        request.state.trace_id = trace_id
        request.state.span_id = span_id

        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        response.headers["x-trace-id"] = trace_id
        response.headers["x-span-id"] = span_id
        response.headers["x-service"] = "demo-mock"
        response.headers["x-elapsed-ms"] = f"{elapsed_ms:.1f}"

        logger.info(
            "request",
            extra={
                "trace_id": trace_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "elapsed_ms": round(elapsed_ms, 2),
            },
        )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("demo-mock-service starting on port 8006")
    yield


app = FastAPI(title="scenic-dh-demo-mock-service", version="1.0.0", lifespan=lifespan)
app.add_middleware(TraceMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


# ═══════════════════════════════════
# Demo scenario state
# ═══════════════════════════════════
SCENARIO = {
    "id": "demo-lingshan-full",
    "name": "灵山胜境完整演示",
    "steps": [
        {"step": 1, "action": "create_session", "desc": "创建游客会话", "endpoint": "POST /v1/sessions"},
        {"step": 2, "action": "map_pois", "desc": "查看景区地图POI", "endpoint": "GET /v1/map/pois"},
        {"step": 3, "action": "spot_list", "desc": "获取景点列表", "endpoint": "GET /v1/spots"},
        {"step": 4, "action": "spot_detail", "desc": "查看灵山大佛详情", "endpoint": "GET /v1/spots/LS-001"},
        {"step": 5, "action": "scan_qrcode", "desc": "扫码触发讲解", "endpoint": "POST /v1/qrcode/resolve"},
        {"step": 6, "action": "route_plan", "desc": "规划游览路线", "endpoint": "POST /v1/routes/plan"},
        {"step": 7, "action": "get_tickets", "desc": "查看票务产品", "endpoint": "GET /v1/tickets/products"},
        {"step": 8, "action": "join_queue", "desc": "线上排队取号", "endpoint": "POST /v1/queue/tickets"},
        {"step": 9, "action": "arrival_ls001", "desc": "到达灵山大佛", "endpoint": "POST /v1/sessions/{id}/arrival-events"},
        {"step": 10, "action": "ask_question", "desc": "提问：大佛有多高", "endpoint": "POST /v1/sessions/{id}/messages"},
        {"step": 11, "action": "ask_question_2", "desc": "提问：梵宫有什么", "endpoint": "POST /v1/sessions/{id}/messages"},
        {"step": 12, "action": "arrival_ls003", "desc": "到达九龙灌浴", "endpoint": "POST /v1/sessions/{id}/arrival-events"},
        {"step": 13, "action": "submit_feedback", "desc": "提交反馈", "endpoint": "POST /v1/sessions/{id}/feedback"},
        {"step": 14, "action": "emergency", "desc": "模拟应急求助", "endpoint": "POST /v1/emergency/requests"},
        {"step": 15, "action": "offline", "desc": "检查离线包", "endpoint": "GET /v1/offline-packages/latest"},
    ],
    "totalSteps": 15,
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
    "locations": {"LS-001": {"lat": 31.4240, "lng": 120.1070}, "LS-002": {"lat": 31.4215, "lng": 120.1080}, "LS-003": {"lat": 31.4200, "lng": 120.1030}},
}


# ═══════════════════════════════════
# Helpers
# ═══════════════════════════════════
def _ok(data: dict, trace_id: str) -> dict:
    return {"code": 0, "message": "success", "data": data, "trace_id": trace_id}


def _get_trace(request: Request) -> str:
    return getattr(request.state, "trace_id", f"trace_{uuid.uuid4().hex}")


# ═══════════════════════════════════
# Routes
# ═══════════════════════════════════
@app.get("/health")
def health(request: Request):
    return _ok({"status": "ok", "version": "1.0.0"}, _get_trace(request))


# Demo control — 读取请求体中的 scenarioId
@app.post("/v1/demo/reset")
async def demo_reset(request: Request):
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    _demo_state["currentStep"] = 0
    _demo_state["status"] = "idle"
    _demo_state["stepResult"] = None
    scenario_id = body.get("scenarioId", SCENARIO["id"])
    return _ok({"reset": True, "scenarioId": scenario_id}, _get_trace(request))


@app.post("/v1/demo/start")
async def demo_start(request: Request):
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    scenario_id = body.get("scenarioId", SCENARIO["id"])
    _demo_state["currentStep"] = 1
    _demo_state["status"] = "running"
    _demo_state["stepResult"] = SCENARIO["steps"][0]
    return _ok({"currentStep": 1, "scenarioId": scenario_id, "step": SCENARIO["steps"][0]}, _get_trace(request))


@app.post("/v1/demo/next")
async def demo_next(request: Request):
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    step = _demo_state["currentStep"]
    if step < SCENARIO["totalSteps"]:
        step += 1
        _demo_state["currentStep"] = step
        _demo_state["stepResult"] = SCENARIO["steps"][step - 1]
        _demo_state["status"] = "running"
    else:
        _demo_state["status"] = "done"
        _demo_state["stepResult"] = None
    return _ok(_demo_state, _get_trace(request))


@app.get("/v1/demo/current")
def demo_current(request: Request):
    return _ok(_demo_state, _get_trace(request))


@app.post("/v1/demo/pause")
def demo_pause(request: Request):
    _demo_state["status"] = "paused"
    return _ok({"paused": True, "atStep": _demo_state["currentStep"]}, _get_trace(request))


# Mock data endpoints
@app.get("/v1/mock/weather")
def mock_weather(request: Request, scenic_id: str = None):
    return _ok(MOCK_DATA["weather"], _get_trace(request))


@app.get("/v1/mock/queues")
def mock_queues(request: Request, spot_id: str = None):
    data = dict(MOCK_DATA["queues"])
    if spot_id:
        data["spotId"] = spot_id
    return _ok(data, _get_trace(request))


@app.get("/v1/mock/crowd")
def mock_crowd(request: Request):
    return _ok(MOCK_DATA["crowd"], _get_trace(request))


@app.get("/v1/mock/locations/{spot_id}")
def mock_location(request: Request, spot_id: str):
    loc = MOCK_DATA["locations"].get(spot_id, {"lat": 31.42, "lng": 120.10})
    return _ok({"spotId": spot_id, "location": loc, "source": "mock"}, _get_trace(request))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
