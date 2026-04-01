from typing import Optional


def create_connect_four() -> dict:
    """Create a new Connect Four game state."""
    return {
        "type": "connect_four",
        "board": [[None] * 7 for _ in range(6)],  # 6 rows × 7 cols
        "current_player": 0,
        "winner": None,       # None | 0 | 1 | -1 (draw)
        "game_over": False,
        "winning_cells": [],  # [[row, col], ...] for highlight
        "last_drop": None,    # [row, col] of last placed piece
    }


def drop_piece(state: dict, col: int, player_id: int) -> dict:
    """Drop a piece in the given column. Returns updated state (mutated in place)."""
    if state["current_player"] != player_id:
        return state
    if state["game_over"]:
        return state
    if col < 0 or col >= 7:
        return state

    board = state["board"]

    # Find the lowest empty row in the column
    row = -1
    for r in range(5, -1, -1):
        if board[r][col] is None:
            row = r
            break

    if row == -1:  # Column is full
        return state

    board[row][col] = player_id
    state["last_drop"] = [row, col]

    # Check for winner
    winning = _check_winner(board, row, col, player_id)
    if winning:
        state["winner"] = player_id
        state["game_over"] = True
        state["winning_cells"] = winning
    elif all(board[0][c] is not None for c in range(7)):
        state["winner"] = -1  # Draw
        state["game_over"] = True
    else:
        state["current_player"] = 1 - player_id

    return state


def _check_winner(board: list, row: int, col: int, player_id: int) -> Optional[list]:
    """Return winning cells if the last move creates 4-in-a-row, else None."""
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]  # →, ↓, ↘, ↙

    for dr, dc in directions:
        cells = [(row, col)]

        for sign in (1, -1):
            r, c = row + sign * dr, col + sign * dc
            while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player_id:
                cells.append((r, c))
                r += sign * dr
                c += sign * dc

        if len(cells) >= 4:
            return [[r, c] for r, c in cells]

    return None
