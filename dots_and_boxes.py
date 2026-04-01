from typing import Optional


def create_dots_and_boxes(size: int = 6) -> dict:
    """
    size x size boxes = (size+1) x (size+1) dots
    h_lines[row][col]: horizontal line between dot(row,col) and dot(row,col+1)  → size+1 rows × size cols
    v_lines[row][col]: vertical line between dot(row,col) and dot(row+1,col)    → size rows × size+1 cols
    """
    h_lines = [[False] * size for _ in range(size + 1)]
    v_lines = [[False] * (size + 1) for _ in range(size)]
    boxes: list[list[Optional[int]]] = [[None] * size for _ in range(size)]

    return {
        "type": "dots_and_boxes",
        "size": size,
        "h_lines": h_lines,
        "v_lines": v_lines,
        "boxes": boxes,
        "current_player": 0,
        "scores": [0, 0],
        "last_line": None,
        "game_over": False,
        "winner": None,
    }


def draw_line(state: dict, line_type: str, row: int, col: int, player_id: int) -> dict:
    """Draw a line. Returns updated state."""
    if state["current_player"] != player_id or state["game_over"]:
        return state

    size = state["size"]
    h_lines = state["h_lines"]
    v_lines = state["v_lines"]
    boxes = state["boxes"]

    # Validate and place line
    if line_type == "h":
        if row < 0 or row > size or col < 0 or col >= size:
            return state
        if h_lines[row][col]:
            return state
        h_lines[row][col] = True
    elif line_type == "v":
        if row < 0 or row >= size or col < 0 or col > size:
            return state
        if v_lines[row][col]:
            return state
        v_lines[row][col] = True
    else:
        return state

    state["last_line"] = {"type": line_type, "row": row, "col": col}

    # Check for newly completed boxes
    scored = 0
    for br in range(size):
        for bc in range(size):
            if boxes[br][bc] is None:
                # top, bottom, left, right
                top = h_lines[br][bc]
                bottom = h_lines[br + 1][bc]
                left = v_lines[br][bc]
                right = v_lines[br][bc + 1]
                if top and bottom and left and right:
                    boxes[br][bc] = player_id
                    state["scores"][player_id] += 1
                    scored += 1

    # Check game over
    total_boxes = size * size
    filled = sum(1 for r in range(size) for c in range(size) if boxes[r][c] is not None)
    if filled == total_boxes:
        state["game_over"] = True
        s0, s1 = state["scores"]
        if s0 > s1:
            state["winner"] = 0
        elif s1 > s0:
            state["winner"] = 1
        else:
            state["winner"] = -1  # tie
    else:
        # If player scored, they get another turn; otherwise switch
        if scored == 0:
            state["current_player"] = 1 - player_id

    return state
