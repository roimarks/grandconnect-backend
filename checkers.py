from typing import Optional

# Player 0 = bottom (moves up, rows 5-7 initially)
# Player 1 = top    (moves down, rows 0-2 initially)


def create_checkers() -> dict:
    board: list[list[Optional[dict]]] = [[None] * 8 for _ in range(8)]

    # Player 1 pieces at top (rows 0-2)
    for row in range(3):
        for col in range(8):
            if (row + col) % 2 == 1:
                board[row][col] = {"player": 1, "king": False}

    # Player 0 pieces at bottom (rows 5-7)
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
        "captured_counts": [0, 0],
        "game_over": False,
        "winner": None,
    }


def _get_jumps(board: list, row: int, col: int, piece: dict) -> list[list]:
    """Return list of jump destinations (captures) for a piece, as [to_row, to_col] pairs.
    Captures are allowed in all 4 directions for both regular pieces and kings (backward captures enabled).
    """
    jumps = []
    player = piece["player"]
    # All pieces (regular and kings) may capture in any direction
    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    for dr, dc in directions:
        mid_r, mid_c = row + dr, col + dc
        to_r, to_c = row + 2 * dr, col + 2 * dc
        if 0 <= to_r < 8 and 0 <= to_c < 8:
            mid_piece = board[mid_r][mid_c]
            if mid_piece and mid_piece["player"] != player and board[to_r][to_c] is None:
                jumps.append([to_r, to_c])
    return jumps


def _get_simple_moves(board: list, row: int, col: int, piece: dict) -> list[list]:
    """Return list of simple (non-capture) moves as [to_row, to_col] pairs."""
    moves = []
    player = piece["player"]
    directions = []
    if piece["king"]:
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    else:
        if player == 0:
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
    """Select a piece and compute its valid moves."""
    if state["current_player"] != player_id or state["game_over"]:
        return state

    board = state["board"]
    piece = board[row][col]
    if not piece or piece["player"] != player_id:
        return state

    must_capture = _any_capture_available(board, player_id)
    state["must_capture"] = must_capture

    jumps = _get_jumps(board, row, col, piece)
    if must_capture:
        valid_moves = jumps
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
    """Execute a move for the selected piece."""
    if state["current_player"] != player_id or state["game_over"]:
        return state
    if not state["selected"]:
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
        mid_r, mid_c = from_row + dr // 2, from_col + dc // 2
        board[mid_r][mid_c] = None
        state["captured_counts"][player_id] += 1
        captured = True

    # Promote to king
    if piece["player"] == 0 and to_row == 0:
        piece["king"] = True
    elif piece["player"] == 1 and to_row == 7:
        piece["king"] = True

    # Multi-jump: if captured and more jumps available, keep same player's turn
    if captured:
        further_jumps = _get_jumps(board, to_row, to_col, piece)
        if further_jumps:
            state["selected"] = [to_row, to_col]
            state["valid_moves"] = further_jumps
            # Do NOT switch player — multi-jump continues
            return _check_game_over(state)

    # End of turn
    state["selected"] = None
    state["valid_moves"] = []
    state["current_player"] = 1 - player_id
    state["must_capture"] = _any_capture_available(board, 1 - player_id)

    return _check_game_over(state)


def _check_game_over(state: dict) -> dict:
    board = state["board"]

    for player in range(2):
        pieces = [(r, c) for r in range(8) for c in range(8) if board[r][c] and board[r][c]["player"] == player]
        if not pieces:
            state["game_over"] = True
            state["winner"] = 1 - player
            return state

        # Check if current player has any moves
        if state["current_player"] == player:
            has_move = False
            for r, c in pieces:
                piece = board[r][c]
                if _get_jumps(board, r, c, piece) or _get_simple_moves(board, r, c, piece):
                    has_move = True
                    break
            if not has_move:
                state["game_over"] = True
                state["winner"] = 1 - player

    return state
