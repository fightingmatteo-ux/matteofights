"""Per-reel choices shared by build.py and make_broll.py (fill after reading the transcript)."""
REEL = {
    # spoken hook as on-screen lines; words build in as they are said
    "hooks": {
        "A": ["I knocked him out", "in my first fight", "and it shouldn't have counted."],
        "B": ["My first fight", "ended in a knockout", "and I'm the one", "who should have lost."],
        "C": ["Should a knockout count", "if the refs are already", "in between?"],
        "D": ["My first knockout", "is the one I'm", "least proud of."],
        "E": ["One punch.", "Half a second", "too late."],
    },
    "red": {"A": {"COUNTED"}, "B": {"LOST"}, "C": {"BETWEEN"}, "D": {"PROUD"}, "E": {"LATE"}},
    # the tape's right hand lands on this spoken word (+0.05 s)
    "ko_word": {"A": "KNOCKED", "B": "KNOCKOUT", "C": "KNOCKOUT", "D": "KNOCKOUT", "E": "PUNCH"},
    # last spoken word of the hook (the hook graphic clears when "I was sixteen" starts)
    "hook_last": {"A": "COUNTED", "B": "LOST", "C": "BETWEEN", "D": "OF", "E": "LATE"},
    # the result plate's K.O. gets struck through on this word, then rolls to DRAW
    "strike": {"A": "SHOULDN'T", "B": "SHOULD", "C": "ALREADY", "D": "LEAST", "E": "SECOND"},
    # ... and rolls over to DRAW on this word
    "draw": {"A": "COUNTED", "B": "LOST", "C": "BETWEEN", "D": "PROUD", "E": "LATE"},
    "keys": ["16", "HUNTED", "SEND", "HURTING"],
    "fx": {"16": "focus", "HUNTED": "focus", "SEND": "focus", "HURTING": "impact"},
    # white cards: ((seg, word, k), (seg, word, k) the card ends before, KEYWORD)
    "cards": [
        (("body1", "THEY", 1), ("body1", "THEY", 2), "DRAW"),
        (("end", "IT'S", 1), ("end", "IF", 1), "CONTROL"),
    ],
    "slam": ["DRAW"],
    "bed": "../../listicles/music/drill-london-echoes.mp3",
    "fix": {},
}
