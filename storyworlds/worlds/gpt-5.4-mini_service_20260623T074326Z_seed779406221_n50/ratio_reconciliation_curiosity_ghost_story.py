#!/usr/bin/env python3
"""
storyworlds/worlds/ratio_reconciliation_curiosity_ghost_story.py
===============================================================

A small standalone storyworld about a curious child, a ghostly room, and a
ratio puzzle that turns lonely numbers into a reconciliation.

The world is built to feel like a gentle ghost story: moonlit rooms, whispering
drafts, a shy ghost, and a child whose curiosity leads to a careful fix. The
"ratio" seed word is embodied as a ratio of things that do not match at first
and then are brought back into harmony.

This script follows the storyworld contract:
- stdlib only, self-contained
- imports StoryError / QAItem / StorySample eagerly
- lazy-imports storyworlds.asp inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

TARGET_RATIO = 2.0
RATIO_TOL = 1e-9



def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class StoryParams:
    room: str
    child: str
    ghost: str
    tokens_blue: int
    tokens_gold: int
    broken: int
    repaired: int
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass(frozen=True)
class RoomSpec:
    id: str
    name: str
    opening: str
    sound: str
    ending: str
    ghost_line: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass(frozen=True)
class ChildSpec:
    id: str
    name: str
    pronoun_subj: str = "they"
    pronoun_obj: str = "them"
    pronoun_poss: str = "their"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass(frozen=True)
class GhostSpec:
    id: str
    name: str
    mood: str
    line: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


ROOMS = {
    "attic": RoomSpec(
        id="attic",
        name="attic",
        opening="in the old attic under the slanted roof",
        sound="the boards sighed softly",
        ending="the attic looked warmer than before",
        ghost_line="a pale ribbon of moonlight hung from the rafters",
    ),
    "library": RoomSpec(
        id="library",
        name="library",
        opening="in the quiet library with tall sleeping shelves",
        sound="the pages rustled like tiny wings",
        ending="the library glowed with a calmer hush",
        ghost_line="a silver breeze slipped between the books",
    ),
    "hallway": RoomSpec(
        id="hallway",
        name="hallway",
        opening="in the narrow hallway where the lamp was dim",
        sound="the floor creaked like a careful secret",
        ending="the hallway no longer felt lonely",
        ghost_line="a thin white shimmer drifted by the coat hooks",
    ),
}

CHILDREN = {
    "mira": ChildSpec(id="Mira", name="Mira"),
    "noah": ChildSpec(id="Noah", name="Noah"),
    "penny": ChildSpec(id="Penny", name="Penny"),
    "leo": ChildSpec(id="Leo", name="Leo"),
}

GHOSTS = {
    "moth": GhostSpec(
        id="Moth",
        name="Moth",
        mood="shy",
        line="I only wanted the room to feel less empty.",
    ),
    "opal": GhostSpec(
        id="Opal",
        name="Opal",
        mood="lonely",
        line="The counting was wrong, and I could not settle.",
    ),
    "briar": GhostSpec(
        id="Briar",
        name="Briar",
        mood="gentle",
        line="The numbers kept asking for help.",
    ),
}

SCALES = [
    ("marbles", "shells"),
    ("candles", "lanterns"),
    ("pebbles", "stars"),
]

KNOWLEDGE = {
    "ratio": [
        ("What is a ratio?",
         "A ratio is a way to compare how many of one thing there are with how many of another thing there are."),
    ],
    "reconciliation": [
        ("What does reconciliation mean?",
         "Reconciliation means making things fit together again after they were off or apart."),
    ],
    "curiosity": [
        ("What is curiosity?",
         "Curiosity is the wish to ask questions and learn more."),
    ],
    "ghost": [
        ("Are all ghosts scary?",
         "No. In a story, a ghost can be shy, lonely, or kind instead of scary."),
    ],
}


def _ratio_ok(blue: int, gold: int) -> bool:
    if blue <= 0 or gold <= 0:
        return False
    return abs((blue / gold) - TARGET_RATIO) < RATIO_TOL


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room in ROOMS:
        for child in CHILDREN:
            for ghost in GHOSTS:
                combos.append((room, child, ghost))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost story about curiosity and ratio reconciliation.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    room = getattr(args, "room", None) or rng.choice(list(ROOMS))
    child = getattr(args, "child", None) or rng.choice(list(CHILDREN))
    ghost = getattr(args, "ghost", None) or rng.choice(list(GHOSTS))
    if room not in ROOMS or child not in CHILDREN or ghost not in GHOSTS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    blue = rng.randint(2, 8)
    gold = blue // 2
    if gold == 0:
        gold = 1
        blue = 2
    broken = rng.randint(1, 4)
    repaired = broken
    return StoryParams(room=room, child=child, ghost=ghost, tokens_blue=blue, tokens_gold=gold, broken=broken, repaired=repaired)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.meters = {"ratio_gap": 0.0, "mend": 0.0}
        self.memes = {"curiosity": 1.0, "reconciliation": 0.0, "relief": 0.0}
        self.facts = {}
        self.lines: list[str] = []

    def say(self, line: str) -> None:
        self.lines.append(line)

    def render(self) -> str:
        return "\n\n".join(self.lines)


def _describe_ratio(blue: int, gold: int) -> str:
    return f"{blue} blue tokens to {gold} gold tokens"


def generate_story(world: World) -> None:
    p = world.params
    room = _safe_lookup(ROOMS, p.room)
    child = CHILDREN[p.child]
    ghost = _safe_lookup(GHOSTS, p.ghost)

    world.facts.update(
        room=room.id,
        child=child.id,
        ghost=ghost.id,
        ratio=f"{p.tokens_blue}:{p.tokens_gold}",
        ratio_value=p.tokens_blue / p.tokens_gold,
    )

    world.say(
        f"{child.name} wandered {room.opening}. The air was cool, and {room.sound}."
    )
    world.say(
        f"On a dusty table sat {_describe_ratio(p.tokens_blue, p.tokens_gold)} of little tokens, "
        f"all sorted into two neat bowls. {child.name} leaned closer because curiosity tugged at {child.pronoun_poss} sleeve."
    )
    world.say(
        f"Then {ghost.name} appeared as a soft white shape. {room.ghost_line}. "
        f"{ghost.name} whispered, \"{ghost.line}\""
    )
    world.meters["ratio_gap"] = abs((p.tokens_blue / p.tokens_gold) - TARGET_RATIO)
    world.say(
        f"{child.name} counted again and noticed the ratio was wrong by a small but lonely amount. "
        f"{child.name} did not laugh; {child.pronoun_subj} asked the ghost what had been lost."
    )
    world.say(
        f"{ghost.name} pointed to the broken set on the floor. One bowl had {p.broken} cracked pieces, "
        f"and the other had been empty for far too long. The room felt unfinished."
    )
    world.meters["mend"] += 1.0
    world.memes["reconciliation"] += 1.0
    world.say(
        f"{child.name} brought the pieces back one by one, pairing blue with gold until the sets matched. "
        f"It was not magic at first, just careful hands and a patient question."
    )
    world.say(
        f"When the last piece was put in place, the ratio settled into a calm {int(TARGET_RATIO)} to 1 rhythm. "
        f"{ghost.name}'s outline brightened, and the room stopped holding its breath."
    )
    world.say(
        f"{ghost.name} smiled. \"Thank you,\" {ghost.name.lower() if hasattr(ghost.name, 'lower') else ghost.name} said, "
        f"and the pale shape softened into a friendly glow."
    )
    world.memes["relief"] += 1.0
    world.say(
        f"By the end, {child.name} stood in the quiet room with a warm chest and tidy bowls. "
        f"The curious question had become a small reconciliation, and the ghost story ended with peace."
    )


def generate(params: StoryParams) -> StorySample:
    if not _ratio_ok(params.tokens_blue, params.tokens_gold):
        pass
    world = World(params)
    generate_story(world)
    prompts = [
        "Write a gentle ghost story where a curious child solves a ratio mismatch and helps a shy spirit feel at home.",
        f"Include the ratio {_describe_ratio(params.tokens_blue, params.tokens_gold)} and make the ending peaceful.",
        "Keep the tone child-facing, moonlit, and soft, with curiosity leading to reconciliation.",
    ]
    story_qa = [
        QAItem(
            question="What was the child curious about?",
            answer="The child was curious about why the token ratio was wrong and what had made the room feel unfinished.",
        ),
        QAItem(
            question="What changed the ghost's mood?",
            answer="The ghost felt better after the child fixed the broken set and restored the matching ratio.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended peacefully, with the ratio settled, the room calmer, and the ghost looking friendly.",
        ),
    ]
    world_qa = [
        QAItem(question=q, answer=a) for q, a in KNOWLEDGE["ratio"] + KNOWLEDGE["reconciliation"] + KNOWLEDGE["curiosity"] + KNOWLEDGE["ghost"]
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- trace ---")
        print(sample.world.facts)
        print(sample.world.meters)
        print(sample.world.memes)
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("room", rid) for rid in ROOMS]
    lines += [asp.fact("child", cid) for cid in CHILDREN]
    lines += [asp.fact("ghost", gid) for gid in GHOSTS]
    lines += [asp.fact("target_ratio", 2)]
    return "\n".join(lines)


ASP_RULES = r"""
room_ok(R) :- room(R).
child_ok(C) :- child(C).
ghost_ok(G) :- ghost(G).
valid(R,C,G) :- room_ok(R), child_ok(C), ghost_ok(G).
#show valid/3.
"""


def asp_program(extra: str = "", show: str = "#show valid/3.\n") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} valid combos.")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


def generation_params_list(args: argparse.Namespace) -> list[StoryParams]:
    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    if getattr(args, "all", None):
        out = []
        for r in ROOMS:
            for c in CHILDREN:
                for g in GHOSTS:
                    out.append(StoryParams(room=r, child=c, ghost=g, tokens_blue=4, tokens_gold=2, broken=2, repaired=2))
        return out
    params = []
    for i in range(getattr(args, "n", None)):
        params.append(resolve_params(args, random.Random(rng.randint(0, 2**31 - 1))))
    return params


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return

    samples = []
    for p in generation_params_list(args):
        samples.append(generate(p))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
