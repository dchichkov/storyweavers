#!/usr/bin/env python3
"""
bobcat_bravery_friendship_folk_tale.py
======================================

A small folk-tale storyworld about a bobcat, a hard choice, brave help, and
the warm pull of friendship.

Premise:
- A young bobcat lives near a cedar grove and a winding creek.
- The bobcat has a close friend in trouble: a lantern has fallen, a path has gone dark,
  or a little helper is stuck in a thorny tangle.
- The bobcat is nervous because the crossing is wet, steep, or shadowy.
- A friend, elder, or sibling offers a simple, believable way to help.
- The bobcat chooses bravery, crosses, and the friendship grows stronger.

The world models:
- meters: physical effort, distance, chill, danger, and the state of a small object
- memes: fear, bravery, trust, friendship, relief

This script keeps the prose child-facing and concrete, with a clear beginning,
a middle turn, and an ending image proving the change.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

MOODS = ["afraid", "brave", "kind", "steady", "wary", "gentle"]
PLACES = ["cedar grove", "pine hill", "river bend", "mossy path", "birch hollow"]
OBSTACLES = ["creek", "dark bridge", "thorn patch", "fallen log", "muddy bank"]
HELP_ITEMS = ["lantern", "basket", "scarf", "apple", "bundle of herbs"]
FRIEND_TYPES = ["rabbit", "mouse", "otter", "fox", "badger", "squirrel"]
NAMES = ["Bramble", "Tawny", "Pip", "Milo", "Fern", "Juniper", "Oakley", "Wren", "Lark"]
FRIEND_NAMES = ["Poppy", "Hazel", "Rowan", "Moss", "Clover", "Willow", "Briar", "Sage"]
EARS = ["small", "rounded", "alert"]
TAILS = ["short", "striped", "soft"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["distance", "effort", "risk", "darkness", "cold", "damage", "safe"]:
            self.meters.setdefault(k, 0.0)
        for k in ["fear", "bravery", "friendship", "trust", "relief", "worry"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    obstacle: str
    supports: set[str] = field(default_factory=set)
    weather: str = ""


@dataclass
class Friend:
    name: str
    type: str
    need: str
    item: str
    item_phrase: str
    cause: str


@dataclass
class StoryParams:
    place: str
    obstacle: str
    friend_type: str
    friend_name: str
    hero_name: str
    mood: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Reasoning rules
# ---------------------------------------------------------------------------

def _r_cold_and_dark(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.kind != "character":
            continue
        if e.meters["distance"] < THRESHOLD:
            continue
        if e.meters["risk"] >= THRESHOLD and ("warned", e.id) not in world.fired:
            world.fired.add(("warned", e.id))
            e.memes["fear"] += 1
            e.memes["worry"] += 1
            out.append("The crossing looked too cold and dark to ignore.")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.kind != "character":
            continue
        if e.memes["fear"] < THRESHOLD:
            continue
        if e.memes["trust"] < THRESHOLD:
            continue
        sig = ("brave_turn", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["bravery"] += 1
        e.memes["fear"] = max(0.0, e.memes["fear"] - 1)
        out.append("__brave__")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.entities.values() if e.kind == "character" and e.type == "bobcat"), None)
    friend = next((e for e in world.entities.values() if e.kind == "character" and e.id != (hero.id if hero else "")), None)
    if not hero or not friend:
        return out
    if hero.memes["bravery"] < THRESHOLD or friend.memes["trust"] < THRESHOLD:
        return out
    sig = ("friendship", hero.id, friend.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    friend.memes["relief"] += 1
    out.append("__friendship__")
    return out


CAUSAL_RULES = [
    _r_cold_and_dark,
    _r_bravery,
    _r_friendship,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                for s in sents:
                    if s not in {"__brave__", "__friendship__"}:
                        produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "cedar": Setting(place="the cedar grove", obstacle="creek", supports={"creek"}),
    "pine": Setting(place="the pine hill", obstacle="dark bridge", supports={"bridge"}),
    "moss": Setting(place="the mossy path", obstacle="thorn patch", supports={"path"}),
    "birch": Setting(place="the birch hollow", obstacle="fallen log", supports={"log"}),
    "river": Setting(place="the river bend", obstacle="muddy bank", supports={"bank"}),
}

FRIENDS = {
    "rabbit": Friend(
        name="Poppy",
        type="rabbit",
        need="reach a fallen lantern",
        item="lantern",
        item_phrase="a small lantern with a bright copper handle",
        cause="it had rolled near the far side of the creek",
    ),
    "mouse": Friend(
        name="Hazel",
        type="mouse",
        need="carry home a basket of berries",
        item="basket",
        item_phrase="a little basket full of berries",
        cause="the path was blocked by a thorn patch",
    ),
    "otter": Friend(
        name="Rowan",
        type="otter",
        need="pull loose a scarf from a branch",
        item="scarf",
        item_phrase="a striped scarf that caught on a branch",
        cause="the wind had lifted it up high",
    ),
    "fox": Friend(
        name="Moss",
        type="fox",
        need="reach an apple under a log",
        item="apple",
        item_phrase="a round red apple",
        cause="the log was too heavy to move alone",
    ),
    "badger": Friend(
        name="Clover",
        type="badger",
        need="bring home a bundle of herbs",
        item="herbs",
        item_phrase="a bundle of sweet herbs",
        cause="the ground was slick by the muddy bank",
    ),
    "squirrel": Friend(
        name="Willow",
        type="squirrel",
        need="cross back with a pinecone pouch",
        item="pouch",
        item_phrase="a tiny pouch tied with twine",
        cause="the dark bridge shook under little feet",
    ),
}

ASP_RULES = r"""
hero(bobcat).
friend(P) :- friend_type(P,_).

need_help(P) :- trouble(P).
scary_crossing(P) :- risk_place(P).
courage(H) :- hero(H), has_trust(H), has_friend(H), chooses_help(H).
friendship(H,F) :- hero(H), friend(F), helps(H,F).
resolved(H,F) :- friendship(H,F), courage(H).
"""


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------

def make_bobcat(hero_name: str, mood: str) -> Entity:
    return Entity(
        id=hero_name,
        kind="character",
        type="bobcat",
        label="the bobcat",
        meters={"distance": 0.0, "effort": 0.0, "risk": 0.0, "darkness": 0.0, "cold": 0.0, "damage": 0.0, "safe": 0.0},
        memes={"fear": 0.0, "bravery": 0.0, "friendship": 0.0, "trust": 1.0, "relief": 0.0, "worry": 0.0},
    )


def make_friend(friend: Friend) -> Entity:
    return Entity(
        id=friend.name,
        kind="character",
        type=friend.type,
        label=friend.name,
        phrase=friend.item_phrase,
        meters={"distance": 0.0, "effort": 0.0, "risk": 0.0, "darkness": 0.0, "cold": 0.0, "damage": 0.0, "safe": 0.0},
        memes={"fear": 0.0, "bravery": 0.0, "friendship": 0.0, "trust": 1.0, "relief": 0.0, "worry": 0.0},
    )


def predict_help(world: World, hero: Entity, friend: Entity, setting: Setting) -> dict:
    sim = world.copy()
    h = sim.get(hero.id)
    f = sim.get(friend.id)
    h.meters["distance"] += 1
    h.meters["risk"] += 1
    h.memes["fear"] += 1
    f.memes["trust"] += 1
    propagate(sim, narrate=False)
    return {"brave": h.memes["bravery"] >= THRESHOLD, "friendship": h.memes["friendship"] >= THRESHOLD}


def opening_line(hero: Entity) -> str:
    return f"Once upon a time, in a quiet grove, there lived a little bobcat named {hero.id}."


def setting_line(setting: Setting) -> str:
    return f"{setting.place.capitalize()} was green and hushed, with a {setting.obstacle} nearby."


def friendship_line(hero: Entity, friend: Entity, friend_need: str) -> str:
    return f"{hero.id} liked {friend.id} because they always shared little tasks and big smiles."


def challenge_line(hero: Entity, friend: Entity, setting: Setting, friend_need: str) -> str:
    return (
        f"One day, {friend.id} needed help to {friend_need} at {setting.place}, "
        f"but the {setting.obstacle} made the way look hard."
    )


def decide_line(hero: Entity, friend: Entity) -> str:
    return f"{hero.id}'s whiskers trembled, but {hero.id} did not want to leave {friend.id} alone."


def resolve_line(hero: Entity, friend: Entity, item_phrase: str) -> str:
    return (
        f"Together, they found a careful way across, and {hero.id} came back "
        f"with {friend.id}'s {item_phrase} safe in {hero.id}'s mouth."
    )


def ending_line(hero: Entity, friend: Entity) -> str:
    return f"That night, the two friends sat side by side and watched the moon shine on the creek."


def tell(setting: Setting, friend: Friend, hero_name: str, mood: str) -> World:
    world = World(setting)
    hero = world.add(make_bobcat(hero_name, mood))
    companion = world.add(make_friend(friend))

    opening = opening_line(hero)
    world.say(opening)
    world.say(setting_line(setting))
    world.say(friendship_line(hero, companion, friend.need))

    world.para()
    world.say(challenge_line(hero, companion, setting, friend.need))
    hero.meters["distance"] += 1
    hero.meters["risk"] += 1
    hero.meters["darkness"] += 1
    hero.meters["cold"] += 1
    hero.memes["fear"] += 1
    companion.memes["trust"] += 1
    world.facts.update(
        hero=hero,
        friend=companion,
        friend_cfg=friend,
        setting=setting,
    )

    pred = predict_help(world, hero, companion, setting)
    if hero.memes["fear"] >= THRESHOLD:
        world.say(f"{hero.id} paused at the edge of the way, feeling small beside the rushing water.")
    world.say(decide_line(hero, companion))
    world.say(f"Then {hero.id} took a deep breath and chose to help.")

    hero.memes["bravery"] += 1
    hero.memes["trust"] += 1
    hero.meters["effort"] += 1
    hero.meters["distance"] += 1
    hero.meters["safe"] += 1
    companion.memes["relief"] += 1
    companion.memes["friendship"] += 1
    hero.memes["friendship"] += 1
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1)

    world.para()
    world.say(resolve_line(hero, companion, friend.item_phrase))
    if friend.type == "rabbit":
        world.say(f"The little lantern glowed warm again, and the creek did not seem so wide.")
    elif friend.type == "mouse":
        world.say(f"The berries stayed neat, and the thorn patch could not keep the friends apart.")
    elif friend.type == "otter":
        world.say(f"The scarf came loose at last, fluttering down like a bright ribbon.")
    elif friend.type == "fox":
        world.say(f"The apple rolled free, and the old log no longer felt like a wall.")
    elif friend.type == "badger":
        world.say(f"The herbs were carried home before the mud could spoil their sweet smell.")
    else:
        world.say(f"The pouch was safe again, and the bridge only creaked like a sleepy board.")

    if pred["brave"]:
        propagate(world, narrate=True)

    world.para()
    world.say(ending_line(hero, companion))
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend_cfg"]
    setting = f["setting"]
    return [
        f'Write a short folk tale for a young child about a bobcat named {hero.id}, friendship, and courage.',
        f"Tell a gentle story where {hero.id} helps {friend.name} at {setting.place} and learns to be brave.",
        f'Write a simple story featuring a bobcat, a hard crossing, and a kind friend named {friend.name}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    friend_cfg: Friend = f["friend_cfg"]
    setting: Setting = f["setting"]

    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about a little bobcat named {hero.id} who lives near {setting.place}.",
        ),
        QAItem(
            question=f"Who needed help in the story?",
            answer=f"{friend.id} needed help to {friend_cfg.need} because of the {setting.obstacle}.",
        ),
        QAItem(
            question=f"What did {hero.id} have to do to help {friend.id}?",
            answer=f"{hero.id} had to cross the hard way, face the worry, and help bring back the {friend_cfg.item}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel before choosing to help?",
            answer=f"{hero.id} felt afraid at first, because the crossing looked cold and dark.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt brave and happy, because the two friends were safe together.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The bobcat's fear turned into bravery, and the friendship between {hero.id} and {friend.id} grew stronger.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "bobcat": [
        (
            "What is a bobcat?",
            "A bobcat is a wild cat with a short tail and spotted fur. It can move quietly through woods and fields.",
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing something even when you feel afraid, because it is the right or kind thing to do.",
        )
    ],
    "friendship": [
        (
            "What is friendship?",
            "Friendship is when two people or animals care about each other, help each other, and enjoy being together.",
        )
    ],
    "creek": [
        (
            "What is a creek?",
            "A creek is a small stream of moving water. It can be shallow or quick, and little animals may need to cross it carefully.",
        )
    ],
    "lantern": [
        (
            "What is a lantern for?",
            "A lantern gives light in the dark, so it can help you see a path or find something you dropped.",
        )
    ],
    "thorns": [
        (
            "Why are thorns prickly?",
            "Thorns are sharp parts on some plants that help protect them, so they can scratch if you touch them.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out: list[QAItem] = [
        QAItem(question=q, answer=a)
        for key in ["bobcat", "bravery", "friendship", "creek", "lantern", "thorns"]
        if key in KNOWLEDGE
        for q, a in KNOWLEDGE[key]
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("place_name", pid, s.place))
        lines.append(asp.fact("obstacle", pid, s.obstacle))
    for fid, f in FRIENDS.items():
        lines.append(asp.fact("friend_type", fid, f.type))
        lines.append(asp.fact("need", fid, f.need))
    lines.append(asp.fact("hero", "bobcat"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show hero/1."))
    if any(a.name == "hero" for a in model):
        print("OK: ASP program loads and produces the expected base facts.")
        return 0
    print("MISMATCH: ASP program did not produce expected facts.")
    return 1


# ---------------------------------------------------------------------------
# Resolve / generate / emit / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about a bobcat, bravery, and friendship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--friend-type", choices=FRIENDS)
    ap.add_argument("--friend-name")
    ap.add_argument("--name")
    ap.add_argument("--mood", choices=MOODS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for ft in FRIENDS:
            combos.append((place, ft, FRIENDS[ft].item))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    friend_type = args.friend_type or rng.choice(list(FRIENDS))
    friend = FRIENDS[friend_type]
    obstacle = args.obstacle or SETTINGS[place].obstacle
    if args.obstacle and args.obstacle != SETTINGS[place].obstacle:
        raise StoryError("That obstacle does not fit the chosen place.")
    friend_name = args.friend_name or friend.name
    hero_name = args.name or rng.choice(NAMES)
    mood = args.mood or rng.choice(MOODS)
    return StoryParams(place=place, obstacle=obstacle, friend_type=friend_type, friend_name=friend_name, hero_name=hero_name, mood=mood)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    friend = FRIENDS[params.friend_type]
    world = tell(setting, friend, params.hero_name, params.mood)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cedar", obstacle="creek", friend_type="rabbit", friend_name="Poppy", hero_name="Bramble", mood="wary"),
    StoryParams(place="moss", obstacle="thorn patch", friend_type="mouse", friend_name="Hazel", hero_name="Tawny", mood="gentle"),
    StoryParams(place="pine", obstacle="dark bridge", friend_type="squirrel", friend_name="Willow", hero_name="Lark", mood="afraid"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show hero/1."))
    return [(a.arguments[0].name,) for a in model if a.name == "hero"]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show hero/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show hero/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.friend_type} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
