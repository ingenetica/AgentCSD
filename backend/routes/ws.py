import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from orchestrator import Orchestrator

router = APIRouter()
logger = logging.getLogger("agentcsd.ws")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connected")

    async def send_ws(data: dict):
        try:
            await websocket.send_json(data)
        except Exception:
            pass

    orchestrator = Orchestrator(send_ws)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await send_ws({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = msg.get("type", "")

            try:
                if msg_type == "create_session":
                    session_id = await orchestrator.create_session(
                        name=msg.get("name", "Untitled"),
                        persona_core_filename=msg.get("persona_core", "default.md"),
                        model_config=msg.get("model_config"),
                        summary_frequency=msg.get("summary_frequency", 10),
                    )
                    await send_ws({
                        "type": "session_created",
                        "session_id": session_id,
                        "name": msg.get("name", "Untitled"),
                    })

                elif msg_type == "resume_session":
                    result = await orchestrator.resume_session(msg["session_id"])
                    await send_ws({
                        "type": "session_resumed",
                        "session_id": result["session_id"],
                        "history": result,
                    })

                elif msg_type == "user_message":
                    await orchestrator.handle_user_message(msg.get("content", ""))

                elif msg_type == "pause_session":
                    await orchestrator.pause()

                elif msg_type == "resume_loop":
                    await orchestrator.resume()

                elif msg_type == "update_config":
                    if msg.get("model_config"):
                        await orchestrator.update_config(msg["model_config"])
                    await send_ws({"type": "status",
                                   "subconscious_running": not orchestrator.is_paused,
                                   "cycle": orchestrator.subconscious_cycle})

                else:
                    await send_ws({"type": "error",
                                   "message": f"Unknown message type: {msg_type}"})

            except Exception as e:
                logger.error("Error handling %s: %s", msg_type, e, exc_info=True)
                await send_ws({"type": "error", "message": str(e)})

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    finally:
        await orchestrator.stop()
