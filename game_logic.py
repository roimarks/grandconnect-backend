import random
from typing import Optional

MEMORY_EMOJIS = ["🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼",
                 "🐨", "🐯", "🦁", "🐮", "🐷", "🐸", "🐙", "🦋"]


def create_memory_game(pairs: int = 8) -> dict:
    """Create a new memory game with the given number of pairs."""
    emojis = MEMORY_EMOJIS[:pairs]
    cards = emojis * 2
    random.shuffle(cards)
    return {
        "type": "memory",
        "cards": [{"emoji": e, "flipped": False, "matched": False} for e in cards],
        "current_player": 0,
        "scores": [0, 0],
        "flipped_indices": [],
        "last_flip": None,
        "game_over": False,
        "winner": None,
    }


def process_flip(state: dict, card_index: int, player_id: int) -> dict:
    """Process a card flip and return the updated state."""
    # Not this player's turn
    if state["current_player"] != player_id:
        return state

    # If two unmatched cards are still waiting to be flipped back — block new flips
    if len(state["flipped_indices"]) >= 2:
        return state

    card = state["cards"][card_index]

    # Card already flipped or matched
    if card["flipped"] or card["matched"]:
        return state

    # Flip the card
    card["flipped"] = True
    state["flipped_indices"].append(card_index)
    state["last_flip"] = card_index

    # Check if two cards are flipped
    if len(state["flipped_indices"]) == 2:
        idx1, idx2 = state["flipped_indices"]
        c1, c2 = state["cards"][idx1], state["cards"][idx2]

        if c1["emoji"] == c2["emoji"]:
            # Match!
            c1["matched"] = True
            c2["matched"] = True
            state["scores"][player_id] += 1
            state["flipped_indices"] = []
            # Check game over
            if all(c["matched"] for c in state["cards"]):
                state["game_over"] = True
                if state["scores"][0] > state["scores"][1]:
                    state["winner"] = 0
                elif state["scores"][1] > state["scores"][0]:
                    state["winner"] = 1
                else:
                    state["winner"] = -1  # tie
        else:
            # No match — will be flipped back after delay (handled by frontend)
            state["current_player"] = 1 - player_id

    return state


def reset_unmatched_flipped(state: dict) -> dict:
    """Flip back unmatched cards (called after frontend delay)."""
    if len(state["flipped_indices"]) == 2:
        idx1, idx2 = state["flipped_indices"]
        if not state["cards"][idx1]["matched"]:
            state["cards"][idx1]["flipped"] = False
            state["cards"][idx2]["flipped"] = False
        state["flipped_indices"] = []
    return state
