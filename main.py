import asyncio
import json
import random
import string
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from game_logic import create_memory_game, process_flip, reset_unmatched_flipped
from connect_four import create_connect_four, drop_piece
from snakes_and_ladders import create_snakes_and_ladders, roll_dice
from checkers import create_checkers, select_piece, move_piece

app = FastAPI(title="GrandConnect API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Data structures ────────────────────────────────────────────────────────
rooms: dict = {}


def generate_room_code(length: int = 4) -> str:
    while True:
        code = "".join(random.choices(string.ascii_uppercase, k=length))
        if code not in rooms:
            return code


async def broadcast(room_code: str, message: dict):
    room = rooms.get(room_code)
    if not room:
        return
    data = json.dumps(message, ensure_ascii=False)
    dead = []
    for ws in room["players"]:
        try:
            await ws.send_text(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        room["players"].remove(ws)


async def relay_to_other(room_code: str, sender: WebSocket, message: dict):
    room = rooms.get(room_code)
    if not room:
        return
    data = json.dumps(message, ensure_ascii=False)
    for ws in room["players"]:
        if ws is not sender:
            try:
                await ws.send_text(data)
            except Exception:
                pass


# ─── Keep-alive ping (prevents Render from sleeping) ─────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "rooms": len(rooms)}

@app.get("/ping")
def ping():
    """Endpoint pinged by UptimeRobot every 5 min to keep the server awake."""
    return {"pong": True}


# ─── WebSocket endpoint ───────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    player_room: Optional[str] = None
    player_id:   Optional[int] = None

    # ── Heartbeat: send ping every 25 s to keep the connection alive ──────────
    async def heartbeat():
        while True:
            await asyncio.sleep(25)
            try:
                if websocket.client_state.value == 1:   # CONNECTED
                    await websocket.send_text(json.dumps({"type": "ping"}))
            except Exception:
                break

    hb_task = asyncio.create_task(heartbeat())

    try:
        while True:
            raw = await websocket.receive_text()

            # ── Wrap every message in try/except so one bad message
            #    never kills the whole connection ──────────────────────────────
            try:
                msg    = json.loads(raw)
                action = msg.get("type")

                # Client pong — just ignore
                if action == "pong":
                    continue

                # ── Create room ───────────────────────────────────────────
                if action == "create_room":
                    room_code = generate_room_code()
                    rooms[room_code] = {"players": [websocket], "game": None}
                    player_room = room_code
                    player_id   = 0
                    await websocket.send_text(json.dumps({
                        "type": "room_created",
                        "room_code": room_code,
                        "player_id": 0,
                    }))

                # ── Join room ─────────────────────────────────────────────
                elif action == "join_room":
                    code = msg.get("room_code", "").upper().strip()
                    if code not in rooms:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "הקוד לא נמצא. בדוק שוב.",
                        }))
                    elif len(rooms[code]["players"]) >= 2:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "החדר מלא.",
                        }))
                    else:
                        rooms[code]["players"].append(websocket)
                        player_room = code
                        player_id   = 1
                        await websocket.send_text(json.dumps({
                            "type": "room_joined",
                            "room_code": code,
                            "player_id": 1,
                        }))
                        await broadcast(code, {"type": "player_joined", "players": 2})

                # ── Start game ────────────────────────────────────────────
                elif action == "start_game":
                    if player_room and player_id == 0:
                        game_type = msg.get("game_type", "memory")
                        if game_type == "memory":
                            pairs = int(msg.get("pairs", 8))
                            theme = msg.get("theme", "emojis")
                            rooms[player_room]["game"] = create_memory_game(pairs=pairs, theme=theme)
                        elif game_type == "connect_four":
                            rooms[player_room]["game"] = create_connect_four()
                        elif game_type == "snakes_and_ladders":
                            rooms[player_room]["game"] = create_snakes_and_ladders()
                        elif game_type == "checkers":
                            rooms[player_room]["game"] = create_checkers()
                        await broadcast(player_room, {
                            "type": "game_started",
                            "game_type": game_type,
                            "game_state": rooms[player_room]["game"],
                        })

                # ── Flip card (memory) ────────────────────────────────────
                elif action == "flip_card":
                    if player_room and player_id is not None:
                        room  = rooms[player_room]
                        state = room["game"]
                        if state and not state.get("game_over"):
                            state = process_flip(state, msg.get("index"), player_id)
                            room["game"] = state
                            await broadcast(player_room, {"type": "game_state", "game_state": state})

                # ── Reset unmatched ───────────────────────────────────────
                elif action == "reset_unmatched":
                    if player_room:
                        room  = rooms[player_room]
                        state = room["game"]
                        if state:
                            state = reset_unmatched_flipped(state)
                            room["game"] = state
                            await broadcast(player_room, {"type": "game_state", "game_state": state})

                # ── Drop piece (connect four) ──────────────────────────────
                elif action == "drop_piece":
                    if player_room and player_id is not None:
                        room  = rooms[player_room]
                        state = room["game"]
                        if state and state.get("type") == "connect_four" and not state.get("game_over"):
                            state = drop_piece(state, msg.get("col"), player_id)
                            room["game"] = state
                            await broadcast(player_room, {"type": "game_state", "game_state": state})

                # ── Roll dice (snakes & ladders) ───────────────────────────
                elif action == "roll_dice":
                    if player_room and player_id is not None:
                        room  = rooms[player_room]
                        state = room["game"]
                        if state and state.get("type") == "snakes_and_ladders" and not state.get("game_over"):
                            state = roll_dice(state, player_id)
                            room["game"] = state
                            await broadcast(player_room, {"type": "game_state", "game_state": state})

                # ── Select piece (checkers) ────────────────────────────────
                elif action == "select_piece":
                    if player_room and player_id is not None:
                        room  = rooms[player_room]
                        state = room["game"]
                        if state and state.get("type") == "checkers" and not state.get("game_over"):
                            state = select_piece(state, msg.get("row"), msg.get("col"), player_id)
                            room["game"] = state
                            await broadcast(player_room, {"type": "game_state", "game_state": state})

                # ── Move piece (checkers) ──────────────────────────────────
                elif action == "move_piece":
                    if player_room and player_id is not None:
                        room  = rooms[player_room]
                        state = room["game"]
                        if state and state.get("type") == "checkers" and not state.get("game_over"):
                            state = move_piece(state, msg.get("to_row"), msg.get("to_col"), player_id)
                            room["game"] = state
                            await broadcast(player_room, {"type": "game_state", "game_state": state})

                # ── Chat ──────────────────────────────────────────────────
                elif action == "chat_message":
                    if player_room and player_id is not None:
                        text = str(msg.get("text", "")).strip()[:300]
                        if text:
                            await broadcast(player_room, {
                                "type": "chat_message",
                                "player_id": player_id,
                                "text": text,
                            })

                # ── Typing ────────────────────────────────────────────────
                elif action == "typing":
                    if player_room and player_id is not None:
                        await relay_to_other(player_room, websocket, {
                            "type": "typing", "player_id": player_id,
                        })

                # ── Restart game ──────────────────────────────────────────
                elif action == "restart_game":
                    if player_room and player_id == 0:
                        current = rooms[player_room].get("game")
                        gtype   = current.get("type", "memory") if current else "memory"
                        if gtype == "connect_four":
                            rooms[player_room]["game"] = create_connect_four()
                        elif gtype == "snakes_and_ladders":
                            rooms[player_room]["game"] = create_snakes_and_ladders()
                        elif gtype == "checkers":
                            rooms[player_room]["game"] = create_checkers()
                        else:
                            old = rooms[player_room].get("game") or {}
                            rooms[player_room]["game"] = create_memory_game(
                                pairs=old.get("pairs", 8), theme=old.get("theme", "emojis"),
                            )
                        await broadcast(player_room, {
                            "type": "game_started",
                            "game_type": gtype,
                            "game_state": rooms[player_room]["game"],
                        })

                # ── Return to lobby ───────────────────────────────────────
                elif action == "return_to_lobby":
                    if player_room:
                        rooms[player_room]["game"] = None
                        await broadcast(player_room, {"type": "return_to_lobby"})

                # ── Nav sync ──────────────────────────────────────────────
                elif action == "nav_sync":
                    if player_room and player_id == 0:
                        await relay_to_other(player_room, websocket, {
                            "type":      "nav_sync",
                            "screen":    msg.get("screen"),
                            "game_type": msg.get("game_type"),
                            "story_id":  msg.get("story_id"),
                        })

                # ── Stories ───────────────────────────────────────────────
                elif action == "open_story":
                    if player_room:
                        await broadcast(player_room, {
                            "type": "story_state", "story_id": msg.get("story_id"),
                            "page": 0, "highlight": None,
                        })

                elif action == "story_turn_page":
                    if player_room:
                        await broadcast(player_room, {
                            "type": "story_state", "story_id": msg.get("story_id"),
                            "page": msg.get("page"), "highlight": None,
                        })

                elif action == "story_highlight":
                    if player_room:
                        await broadcast(player_room, {
                            "type": "story_state", "story_id": msg.get("story_id"),
                            "page": msg.get("page"), "highlight": msg.get("sentence_index"),
                        })

                # ── WebRTC signaling ──────────────────────────────────────
                elif action in ("webrtc_offer", "webrtc_answer", "webrtc_ice"):
                    if player_room:
                        await relay_to_other(player_room, websocket, msg)

            except Exception as e:
                # Log but don't close — one bad message must not kill the session
                print(f"[WS] Error handling action: {e}")

    except WebSocketDisconnect:
        pass
    finally:
        hb_task.cancel()
        if player_room and player_room in rooms:
            room = rooms[player_room]
            if websocket in room["players"]:
                room["players"].remove(websocket)
            if not room["players"]:
                del rooms[player_room]
            else:
                await broadcast(player_room, {"type": "player_left"})
