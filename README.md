# scenic-dh-demo-mock-service

竞赛演示兜底服务。提供一键演示剧本和 mock 数据，不依赖真实外部系统。

## 快速开始

```bash
cd scenic-dh-demo-mock-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8006
```

## 演示控制

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /v1/demo/reset | 重置演示 |
| POST | /v1/demo/start | 启动演示 |
| POST | /v1/demo/next | 推进步骤 |
| POST | /v1/demo/pause | 暂停 |
| GET | /v1/demo/current | 当前状态 |

## Mock 数据

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /v1/mock/weather | 天气 mock |
| GET | /v1/mock/queues | 排队 mock |
| GET | /v1/mock/crowd | 客流 mock |
| GET | /v1/mock/locations/{spotId} | 模拟 GPS |

## 演示剧本

灵山胜境完整演示（10 步）：
1. 创建会话 → 2. 景点列表 → 3. 大佛详情 → 4. 路线推荐 → 5. 到达大佛
→ 6. 提问 → 7. 追问 → 8. 到达九龙灌浴 → 9. 反馈 → 10. 运营数据
