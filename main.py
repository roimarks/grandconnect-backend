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
from dots_and_boxes import create_dots_and_boxes, draw_line

app = FastAPI(title="GrandConnect API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Data structures ────────────────────────────────────────────────────────
# rooms: { room_code: { "players": [ws0, ws1], "game": game_state } }
rooms: dict = {}


def generate_room_code(length: int = 4) -> str:
    while True:
        code = "".join(random.choices(string.ascii_uppercase, k=length))
        if code not in rooms:
            return code


async def broadcast(room_code: str, message: dict):
    """Send a message to all players in a room."""
    room = rooms.get(room_code)
    if not room:
        return
    data = json.dumps(message, ensure_ascii=False)
    for ws in room["players"]:
        try:
            await ws.send_text(data)
        except Exception:
            pass


async def relay_to_other(room_code: str, sender: WebSocket, message: dict):
    """Relay a message to the other player in the room (not the sender)."""
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


# ─── WebSocket endpoint ──────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    player_room: Optional[str] = None
    player_id: Optional[int] = None

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            action = msg.get("type")

            # ── Create room ──────────────────────────────────────────────
            if action == "create_room":
                room_code = generate_room_code()
                rooms[room_code] = {"players": [websocket], "game": None}
                player_room = room_code
                player_id = 0
                await websocket.send_text(json.dumps({
                    "type": "room_created",
                    "room_code": room_code,
                    "player_id": 0,
                }))

            # ── Join room ────────────────────────────────────────────────
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
                    player_id = 1
                    await websocket.send_text(json.dumps({
                        "type": "room_joined",
                        "room_code": code,
                        "player_id": 1,
                    }))
                    await broadcast(code, {"type": "player_joined", "players": 2})

            # ── Start game ───────────────────────────────────────────────
            elif action == "start_game":
                if player_room and player_id == 0:
                    game_type = msg.get("game_type", "memory")
                    if game_type == "memory":
                        rooms[player_room]["game"] = create_memory_game(pairs=8)
                    elif game_type == "connect_four":
                        rooms[player_room]["game"] = create_connect_four()
                    elif game_type == "snakes_and_ladders":
                        rooms[player_room]["game"] = create_snakes_and_ladders()
                    elif game_type == "checkers":
                        rooms[player_room]["game"] = create_checkers()
                    elif game_type == "dots_and_boxes":
                        rooms[player_room]["game"] = create_dots_and_boxes()
                    await broadcast(player_room, {
                        "type": "game_started",
                        "game_type": game_type,
                        "game_state": rooms[player_room]["game"],
                    })

            # ── Flip card (memory) ───────────────────────────────────────
            elif action == "flip_card":
                if player_room and player_id is not None:
                    room = rooms[player_room]
                    state = room["game"]
                    if state and not state.get("game_over"):
                        card_index = msg.get("index")
                        state = process_flip(state, card_index, player_id)
                        room["game"] = state
                        await broadcast(player_room, {
                            "type": "game_state",
                            "game_state": state,
                        })

            # ── Reset unmatched (after frontend delay) ───────────────────
            elif action == "reset_unmatched":
                if player_room:
                    room = rooms[player_room]
                    state = room["game"]
                    if state:
                        state = reset_unmatched_flipped(state)
                        room["game"] = state
                        await broadcast(player_room, {
                            "type": "game_state",
                            "game_state": state,
                        })

            # ── Drop piece (connect four) ─────────────────────────────────
            elif action == "drop_piece":
                if player_room and player_id is not None:
                    room = rooms[player_room]
                    state = room["game"]
                    if state and state.get("type") == "connect_four" and not state.get("game_over"):
                        col = msg.get("col")
                        state = drop_piece(state, col, player_id)
                        room["game"] = state
                        await broadcast(player_room, {
                            "type": "game_state",
                            "game_state": state,
                        })

            # ── Roll dice (snakes and ladders) ────────────────────────────
            elif action == "roll_dice":
                if player_room and player_id is not None:
                    room = rooms[player_room]
                    state = room["game"]
                    if state and state.get("type") == "snakes_and_ladders" and not state.get("game_over"):
                        state = roll_dice(state, player_id)
                        room["game"] = state
                        await broadcast(player_room, {
                            "type": "game_state",
                            "game_state": state,
                        })

            # ── Select piece (checkers) ───────────────────────────────────
            elif action == "select_piece":
                if player_room and player_id is not None:
                    room = rooms[player_room]
                    state = room["game"]
                    if state and state.get("type") == "checkers" and not state.get("game_over"):
                        row_i = msg.get("row")
                        col_i = msg.get("col")
                        state = select_piece(state, row_i, col_i, player_id)
                        room["game"] = state
                        await broadcast(player_room, {
                            "type": "game_state",
                            "game_state": state,
                        })

            # ── Move piece (checkers) ─────────────────────────────────────
            elif action == "move_piece":
                if player_room and player_id is not None:
                    room = rooms[player_room]
                    state = room["game"]
                    if state and state.get("type") == "checkers" and not state.get("game_over"):
                        to_row = msg.get("to_row")
                        to_col = msg.get("to_col")
                        state = move_piece(state, to_row, to_col, player_id)
                        room["game"] = state
                        await broadcast(player_room, {
                            "type": "game_state",
                            "game_state": state,
                        })

            # ── Draw line (dots and boxes) ────────────────────────────────
            elif action == "draw_line":
                if player_room and player_id is not None:
                    room = rooms[player_room]
                    state = room["game"]
                    if state and state.get("type") == "dots_and_boxes" and not state.get("game_over"):
                        line_type = msg.get("line_type")
                        row_i = msg.get("row")
                        col_i = msg.get("col")
                        state = draw_line(state, line_type, row_i, col_i, player_id)
                        room["game"] = state
                        await broadcast(player_room, {
                            "type": "game_state",
                            "game_state": state,
                        })

            # ── Chat message ─────────────────────────────────────────────
            elif action == "chat_message":
                if player_room and player_id is not None:
                    text = str(msg.get("text", "")).strip()[:300]
                    if text:
                        await broadcast(player_room, {
                            "type": "chat_message",
                            "player_id": player_id,
                            "text": text,
                        })

            # ── Typing indicator ──────────────────────────────────────────
            elif action == "typing":
                if player_room and player_id is not None:
                    await relay_to_other(player_room, websocket, {
                        "type": "typing",
                        "player_id": player_id,
                    })

            # ── Restart game ─────────────────────────────────────────────
            elif action == "restart_game":
                if player_room and player_id == 0:
                    current_game = rooms[player_room].get("game")
                    game_type = current_game.get("type", "memory") if current_game else "memory"
                    if game_type == "connect_four":
                        rooms[player_room]["game"] = create_connect_four()
                    elif game_type == "snakes_and_ladders":
                        rooms[player_room]["game"] = create_snakes_and_ladders()
                    elif game_type == "checkers":
                        rooms[player_room]["game"] = create_checkers()
                    elif game_type == "dots_and_boxes":
                        rooms[player_room]["game"] = create_dots_and_boxes()
                    else:
                        rooms[player_room]["game"] = create_memory_game(pairs=8)
                    await broadcast(player_room, {
                        "type": "game_started",
                        "game_type": game_type,
                        "game_state": rooms[player_room]["game"],
                    })

            # ── Return to lobby ───────────────────────────────────────────
            elif action == "return_to_lobby":
                if player_room:
                    rooms[player_room]["game"] = None
                    await broadcast(player_room, {"type": "return_to_lobby"})

            # ── Open story ────────────────────────────────────────────────
            elif action == "open_story":
                if player_room:
                    await broadcast(player_room, {
                        "type": "story_state",
                        "story_id": msg.get("story_id"),
                        "page": 0,
                        "highlight": None,
                    })

            # ── Turn page ─────────────────────────────────────────────────
            elif action == "story_turn_page":
                if player_room:
                    await broadcast(player_room, {
                        "type": "story_state",
                        "story_id": msg.get("story_id"),
                        "page": msg.get("page"),
                        "highlight": None,
                    })

            # ── Highlight sentence ────────────────────────────────────────
            elif action == "story_highlight":
                if player_room:
                    await broadcast(player_room, {
                        "type": "story_state",
                        "story_id": msg.get("story_id"),
                        "page": msg.get("page"),
                        "highlight": msg.get("sentence_index"),
                    })

            # ── WebRTC signaling (relay to other player) ──────────────────
            elif action in ("webrtc_offer", "webrtc_answer", "webrtc_ice"):
                if player_room:
                    await relay_to_other(player_room, websocket, msg)

    except WebSocketDisconnect:
        if player_room and player_room in rooms:
            room = rooms[player_room]
            if websocket in room["players"]:
                room["players"].remove(websocket)
            if len(room["players"]) == 0:
                del rooms[player_room]
            else:
                await broadcast(player_room, {"type": "player_left"})


@app.get("/")
def root():
    return {"status": "ok", "rooms": len(rooms)}
