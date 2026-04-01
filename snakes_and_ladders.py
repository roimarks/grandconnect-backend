import random

# Snakes: head (higher) -> tail (lower)
SNAKES = {
    99: 78,
    87: 24,
    62: 19,
    56: 53,
    49: 11,
    47: 26,
    16: 6,
}

# Ladders: bottom -> top
LADDERS = {
    4: 14,
    9: 31,
    20: 38,
    28: 84,
    40: 59,
    51: 67,
    63: 81,
    71: 91,
}


def create_snakes_and_ladders() -> dict:
    return {
        "type": "snakes_and_ladders",
        "positions": [0, 0],   # 0 = start (off board), 1-100 on board
        "current_player": 0,
        "last_roll": None,
        "last_event": None,    # "snake" | "ladder" | "no_move" | None
        "move_from": None,
        "move_to": None,
        "game_over": False,
        "winner": None,
        "snakes": SNAKES,
        "ladders": LADDERS,
    }


def roll_dice(state: dict, player_id: int) -> dict:
    """Roll dice for the given player and return updated state."""
    if state["current_player"] != player_id:
        return state
    if state["game_over"]:
        return state

    dice = random.randint(1, 6)
    state["last_roll"] = dice
    state["last_event"] = None

    pos = state["positions"][player_id]
    new_pos = pos + dice
    state["move_from"] = pos

    # Can't go beyond 100
    if new_pos > 100:
        state["last_event"] = "no_move"
        state["move_to"] = pos
        state["current_player"] = 1 - player_id
        return state

    # Win!
    if new_pos == 100:
        state["positions"][player_id] = 100
        state["move_to"] = 100
        state["game_over"] = True
        state["winner"] = player_id
        return state

    # Check snake
    if new_pos in SNAKES:
        state["last_event"] = "snake"
        final = SNAKES[new_pos]
        state["move_to"] = final
        state["positions"][player_id] = final
    # Check ladder
    elif new_pos in LADDERS:
        state["last_event"] = "ladder"
        final = LADDERS[new_pos]
        state["move_to"] = final
        state["positions"][player_id] = final
    else:
        state["move_to"] = new_pos
        state["positions"][player_id] = new_pos

    state["current_player"] = 1 - player_id
    return state
