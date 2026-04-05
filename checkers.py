from typing import Optional

# Player 0 = bottom (moves up, rows 5-7 initially)
# Player 1 = top    (moves down, rows 0-2 initially)


def create_checkers() -> dict:
    board: list[list[Optional[dict]]] = [[None] * 8 for _ in range(8)]

    for row in range(3):
        for col in range(8):
            if (row + col) % 2 == 1:
                board[row][col] = {"player": 1, "king": False}

    for row in range(5, 8):
        for col in range(8):
            if (row + col) % 2 == 1:
                board[row][col] = {"player": 0, "king": False}

    return {
        "type": "checkers",
        "board": board,
        "current_player": 0,
        "selected": None,
        "valid_moves": [],
        "must_capture": False,
        "multi_jump": False,        # True while a capture chain is in progress
        "captured_counts": [0, 0],
        "game_over": False,
        "winner": None,
    }


def _get_jumps(board: list, row: int, col: int, piece: dict) -> list[list]:
    """All 4 directions allowed for all pieces (backward captures enabled)."""
    jumps = []
    player = piece["player"]
    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        mid_r, mid_c = row + dr, col + dc
        to_r,  to_c  = row + 2 * dr, col + 2 * dc
        if 0 <= to_r < 8 and 0 <= to_c < 8:
            mid_piece = board[mid_r][mid_c]
            if mid_piece and mid_piece["player"] != player and board[to_r][to_c] is None:
                jumps.append([to_r, to_c])
    return jumps


def _get_simple_moves(board: list, row: int, col: int, piece: dict) -> list[list]:
    moves = []
    player = piece["player"]
    if piece["king"]:
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    elif player == 0:
        directions = [(-1, -1), (-1, 1)]
    else:
        directions = [(1, -1), (1, 1)]

    for dr, dc in directions:
        to_r, to_c = row + dr, col + dc
        if 0 <= to_r < 8 and 0 <= to_c < 8 and board[to_r][to_c] is None:
            moves.append([to_r, to_c])
    return moves


def _any_capture_available(board: list, player: int) -> bool:
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece and piece["player"] == player:
                if _get_jumps(board, r, c, piece):
                    return True
    return False


def select_piece(state: dict, row: int, col: int, player_id: int) -> dict:
    if state["current_player"] != player_id or state["game_over"]:
        return state

    # Cannot switch piece during a multi-jump chain
    if state.get("multi_jump"):
        return state

    if row is None or col is None:
        return state

    board = state["board"]
    piece = board[row][col]
    if not piece or piece["player"] != player_id:
        return state

    must_capture = _any_capture_available(board, player_id)
    state["must_capture"] = must_capture

    jumps = _get_jumps(board, row, col, piece)
    if must_capture:
        valid_moves = jumps          # may be [] if THIS piece can't capture
    else:
        valid_moves = jumps if jumps else _get_simple_moves(board, row, col, piece)

    if not valid_moves:
        state["selected"] = None
        state["valid_moves"] = []
    else:
        state["selected"] = [row, col]
        state["valid_moves"] = valid_moves

    return state


def move_piece(state: dict, to_row: int, to_col: int, player_id: int) -> dict:
    if state["current_player"] != player_id or state["game_over"]:
        return state
    if not state["selected"]:
        return state
    if to_row is None or to_col is None:
        return state

    dest = [to_row, to_col]
    if dest not in state["valid_moves"]:
        return state

    board = state["board"]
    from_row, from_col = state["selected"]
    piece = board[from_row][from_col]
    if not piece:
        return state

    # Move the piece
    board[to_row][to_col] = piece
    board[from_row][from_col] = None

    # Check if this was a capture
    dr = to_row - from_row
    dc = to_col - from_col
    captured = False
    if abs(dr) == 2:
        mid_r = from_row + dr // 2
        mid_c = from_col + dc // 2
        board[mid_r][mid_c] = None
        state["captured_counts"][player_id] += 1
        captured = True

    # Promote to king — turn ends immediately if promoted during a capture
    just_promoted = False
    if piece["player"] == 0 and to_row == 0 and not piece["king"]:
        piece["king"] = True
        just_promoted = True
    elif piece["player"] == 1 and to_row == 7 and not piece["king"]:
        piece["king"] = True
        just_promoted = True

    # Multi-jump: continue only if captured AND more jumps exist AND NOT just promoted
    if captured and not just_promoted:
        further_jumps = _get_jumps(board, to_row, to_col, piece)
        if further_jumps:
            state["selected"]   = [to_row, to_col]
            state["valid_moves"] = further_jumps
            state["multi_jump"] = True
            return _check_game_over(state)

    # End of turn
    state["selected"]        = None
    state["valid_moves"]     = []
    state["multi_jump"]      = False
    state["current_player"]  = 1 - player_id
    state["must_capture"]    = _any_capture_available(board, 1 - player_id)

    return _check_game_over(state)


def _check_game_over(state: dict) -> dict:
    board = state["board"]

    for player in range(2):
        pieces = [
            (r, c)
            for r in range(8)
            for c in range(8)
            if board[r][c] and board[r][c]["player"] == player
        ]
        if not pieces:
            state["game_over"] = True
            state["winner"]    = 1 - player
            return state

        if state["current_player"] == player:
            has_move = any(
                _get_jumps(board, r, c, board[r][c]) or _get_simple_moves(board, r, c, board[r][c])
                for r, c in pieces
            )
            if not has_move:
                state["game_over"] = True
                state["winner"]    = 1 - player
                return state

    return state
