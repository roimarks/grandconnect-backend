import random
from typing import Optional

# ─── Themes ──────────────────────────────────────────────────────────────────

THEMES: dict = {
    "emojis": [
        {"emoji": "🐶", "name": ""}, {"emoji": "🐱", "name": ""}, {"emoji": "🐭", "name": ""},
        {"emoji": "🐹", "name": ""}, {"emoji": "🐰", "name": ""}, {"emoji": "🦊", "name": ""},
        {"emoji": "🐻", "name": ""}, {"emoji": "🐼", "name": ""}, {"emoji": "🐨", "name": ""},
        {"emoji": "🐯", "name": ""}, {"emoji": "🦁", "name": ""}, {"emoji": "🐮", "name": ""},
        {"emoji": "🐷", "name": ""}, {"emoji": "🐸", "name": ""}, {"emoji": "🐙", "name": ""},
        {"emoji": "🦋", "name": ""}, {"emoji": "🌈", "name": ""}, {"emoji": "⭐", "name": ""},
        {"emoji": "🍕", "name": ""}, {"emoji": "🎸", "name": ""}, {"emoji": "🚀", "name": ""},
        {"emoji": "🎩", "name": ""}, {"emoji": "🌺", "name": ""}, {"emoji": "🎯", "name": ""},
    ],
    "animals": [
        {"emoji": "🐶", "name": "כלב"},    {"emoji": "🐱", "name": "חתול"},
        {"emoji": "🐰", "name": "ארנב"},   {"emoji": "🦊", "name": "שועל"},
        {"emoji": "🐻", "name": "דוב"},    {"emoji": "🐼", "name": "פנדה"},
        {"emoji": "🐨", "name": "קואלה"},  {"emoji": "🦁", "name": "אריה"},
        {"emoji": "🐯", "name": "נמר"},    {"emoji": "🐮", "name": "פרה"},
        {"emoji": "🐸", "name": "צפרדע"}, {"emoji": "🐙", "name": "תמנון"},
        {"emoji": "🦋", "name": "פרפר"},  {"emoji": "🐧", "name": "פינגווין"},
        {"emoji": "🦅", "name": "נשר"},   {"emoji": "🐬", "name": "דולפין"},
        {"emoji": "🦓", "name": "זברה"},  {"emoji": "🦒", "name": "ג'ירפה"},
        {"emoji": "🐘", "name": "פיל"},   {"emoji": "🦜", "name": "תוכי"},
        {"emoji": "🦩", "name": "פלמינגו"}, {"emoji": "🦈", "name": "כריש"},
        {"emoji": "🦔", "name": "קיפוד"}, {"emoji": "🦦", "name": "לוטרה"},
    ],
    "artists": [
        {"emoji": "🌻", "name": "ון גוך"},      {"emoji": "🎨", "name": "דה וינצ'י"},
        {"emoji": "🔵", "name": "פיקאסו"},      {"emoji": "💧", "name": "מונה"},
        {"emoji": "🕊️", "name": "מטיס"},         {"emoji": "💎", "name": "דאלי"},
        {"emoji": "🌊", "name": "הוקוסאי"},     {"emoji": "🌸", "name": "רנואר"},
        {"emoji": "🏛️", "name": "מיכלאנג'לו"},  {"emoji": "🎭", "name": "רמברנדט"},
        {"emoji": "💫", "name": "קנדינסקי"},    {"emoji": "🎪", "name": "שאגאל"},
        {"emoji": "🗿", "name": "רודן"},         {"emoji": "🌺", "name": "פרידה קאלו"},
        {"emoji": "⚡", "name": "וורהול"},       {"emoji": "🦩", "name": "דגא"},
        {"emoji": "🌙", "name": "ראפאל"},        {"emoji": "🏺", "name": "בוטיצ'לי"},
        {"emoji": "🌟", "name": "קלימט"},        {"emoji": "🖌️", "name": "גויה"},
        {"emoji": "🌄", "name": "טרנר"},         {"emoji": "🎋", "name": "הירושיגה"},
        {"emoji": "🔴", "name": "רוסו"},         {"emoji": "🌿", "name": "סֶרא"},
    ],
    "inventors": [
        {"emoji": "💡", "name": "אדיסון"},       {"emoji": "⚡", "name": "טסלה"},
        {"emoji": "🍎", "name": "ניוטון"},       {"emoji": "🔭", "name": "גלילאו"},
        {"emoji": "🧬", "name": "דארווין"},      {"emoji": "💻", "name": "טיורינג"},
        {"emoji": "✈️", "name": "האחים רייט"},   {"emoji": "🚂", "name": "סטפנסון"},
        {"emoji": "🔬", "name": "פסטר"},          {"emoji": "💉", "name": "ג'נר"},
        {"emoji": "📡", "name": "מרקוני"},        {"emoji": "🚗", "name": "בנץ"},
        {"emoji": "🌍", "name": "קופרניקוס"},    {"emoji": "🧪", "name": "מרי קירי"},
        {"emoji": "🔩", "name": "ארכימדס"},      {"emoji": "🔋", "name": "ולטה"},
        {"emoji": "📷", "name": "דגר"},           {"emoji": "🎙️", "name": "גרהם בל"},
        {"emoji": "🚀", "name": "ון בראון"},     {"emoji": "🖨️", "name": "גוטנברג"},
        {"emoji": "🧲", "name": "פרדיי"},         {"emoji": "⚗️", "name": "בויל"},
        {"emoji": "🌡️", "name": "פרנהייט"},      {"emoji": "🔐", "name": "בבג'"},
    ],
}


def create_memory_game(pairs: int = 8, theme: str = "emojis") -> dict:
    """Create a memory game with the given number of pairs and theme."""
    theme_items = THEMES.get(theme, THEMES["emojis"])
    items = theme_items[:pairs]
    cards = items * 2
    random.shuffle(cards)
    return {
        "type":           "memory",
        "theme":          theme,
        "pairs":          pairs,
        "cards":          [{"emoji": it["emoji"], "name": it["name"],
                            "flipped": False, "matched": False}
                           for it in cards],
        "current_player": 0,
        "scores":         [0, 0],
        "flipped_indices":[],
        "last_flip":      None,
        "game_over":      False,
        "winner":         None,
    }


def process_flip(state: dict, card_index: int, player_id: int) -> dict:
    """Process a card flip and return the updated state."""
    if state["current_player"] != player_id:
        return state

    if len(state["flipped_indices"]) >= 2:
        return state

    card = state["cards"][card_index]

    if card["flipped"] or card["matched"]:
        return state

    card["flipped"] = True
    state["flipped_indices"].append(card_index)
    state["last_flip"] = card_index

    if len(state["flipped_indices"]) == 2:
        idx1, idx2 = state["flipped_indices"]
        c1, c2 = state["cards"][idx1], state["cards"][idx2]

        if c1["emoji"] == c2["emoji"]:
            c1["matched"] = True
            c2["matched"] = True
            state["scores"][player_id] += 1
            state["flipped_indices"] = []
            if all(c["matched"] for c in state["cards"]):
                state["game_over"] = True
                if state["scores"][0] > state["scores"][1]:
                    state["winner"] = 0
                elif state["scores"][1] > state["scores"][0]:
                    state["winner"] = 1
                else:
                    state["winner"] = -1
        else:
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
