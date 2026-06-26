#!/usr/bin/env python3
"""
storyworlds/worlds/yacht_correlate_slate_magic_friendship_animal_story.py
==========================================================================

A small standalone animal-story world about friends on a yacht, a magic slate,
and a careful bit of correlating clues until the lost thing is found.

Premise:
- A child-friendly animal crew sails a little yacht.
- They find a slate with magic markings that only make sense when clues are
  matched together.
- Friendship keeps the search gentle, and the ship stays calm.

The world is simulated with simple meters and memes:
- meters track physical state like wind, splash, soot, polish, and foundness.
- memes track emotional state like curiosity, worry, trust, and joy.

The story stays close to an Animal Story style:
- small cast
- concrete objects
- clear problem
- discovery through kindness and observation
- ending image proving what changed
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["wet", "tired", "polished", "found", "broken", "safe"]:
            self.meters.setdefault(key, 0.0)
        for key in ["curiosity", "worry", "trust", "joy", "friendship", "pride", "relief"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"otter", "fox", "rabbit", "cat", "mouse", "bear"}:
            mapping = {"subject": "it", "object": "it", "possessive": "its"}
        else:
            mapping = {"subject": "it", "object": "it", "possessive": "its"}
        return mapping[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    hero: str
    friend: str
    prize: str
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str = "the little yacht"
    water: bool = True


@dataclass
class Clue:
    mark: str
    match: str
    hint: str


@dataclass
class Prize:
    label: str
    phrase: str
    clue_mark: str
    clue_match: str
    location: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}
        self.wind: str = "soft"

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        import copy

        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.wind = self.wind
        c.facts = dict(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
ANIMALS = {
    "otter": "a playful otter",
    "fox": "a clever fox",
    "rabbit": "a curious rabbit",
    "cat": "a bright cat",
    "bear": "a gentle bear",
}

FRIENDS = {
    "seagull": "a cheerful seagull",
    "turtle": "a patient turtle",
    "kitten": "a small kitten",
    "duck": "a sunny duck",
    "pup": "a bouncy pup",
}

PRIZES = {
    "star": Prize(
        label="star charm",
        phrase="a tiny star charm",
        clue_mark="star",
        clue_match="starfish bay",
        location="under a blue tarp near the stern",
    ),
    "shell": Prize(
        label="shell locket",
        phrase="a shell locket",
        clue_mark="shell",
        clue_match="shell cove",
        location="inside a rope basket by the cabin",
    ),
    "kite": Prize(
        label="kite ribbon",
        phrase="a bright kite ribbon",
        clue_mark="kite",
        clue_match="kite point",
        location="caught on the mast line",
    ),
}

CLUES = [
    Clue(mark="star", match="starfish bay", hint="a star by the water"),
    Clue(mark="shell", match="shell cove", hint="a shell near the beach"),
    Clue(mark="kite", match="kite point", hint="a kite in the sky"),
]

GIRLISH = ["Mina", "Tia", "Luna", "Pip", "Nia"]
BOYISH = ["Finn", "Juno", "Bram", "Ollie", "Rex"]
NEUTRAL = ["Sky", "River", "Marlo", "Sage", "Toby"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for hero in ANIMALS:
        for prize in PRIZES:
            combos.append((hero, prize))
    return combos


def explain_rejection(hero: str, prize: str) -> str:
    return f"(No story: {hero} and {prize} do not make a reasonable yacht-clue problem.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- animal(H).
prize(P) :- treasure(P).
compatible(H, P) :- hero(H), prize(P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for p in PRIZES:
        lines.append(asp.fact("treasure", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp  # noqa: F401
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    import asp as asp_mod
    model = asp_mod.one_model(asp_program("#show compatible/2."))
    clingo_set = set(asp_mod.atoms(model, "compatible"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between ASP and valid_combos()")
    print("only in ASP:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = Setting()
    world = World(setting)

    hero_type = params.hero
    friend_type = params.friend
    prize_key = params.prize
    prize_cfg = PRIZES[prize_key]

    hero = world.add(Entity(
        id="Hero",
        kind="character",
        type=hero_type,
        label=hero_type,
        phrase=ANIMALS[hero_type],
    ))
    friend = world.add(Entity(
        id="Friend",
        kind="character",
        type=friend_type,
        label=friend_type,
        phrase=FRIENDS[friend_type],
    ))
    prize = world.add(Entity(
        id="Prize",
        type="thing",
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
    ))
    slate = world.add(Entity(
        id="Slate",
        type="thing",
        label="magic slate",
        phrase="a smooth magic slate",
        protective=False,
    ))

    # Setup
    world.say(
        f"On a little yacht, {ANIMALS[hero_type]} {hero.id.lower()} and "
        f"{FRIENDS[friend_type]} {friend.id.lower()} sailed over quiet water."
    )
    world.say(
        f"{hero.id.lower()} loved bright puzzles, and {friend.id.lower()} loved "
        f"helping. They were good friends, so each one listened carefully."
    )
    world.say(
        f"One day they found {slate.phrase} tucked beside a coiled rope. "
        f"It had a mark that shimmered like a clue."
    )

    # Conflict
    world.para()
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"{hero.id.lower()} tapped the slate, and little silver lines appeared: "
        f"{prize_cfg.clue_mark}, then a splash of color, then a place name."
    )
    world.say(
        f"They could not solve it at first. The clue seemed mixed up, and "
        f"{hero.id.lower()} began to worry that the shiny prize might stay lost."
    )
    hero.memes["worry"] += 1
    friend.memes["worry"] += 1

    # Turn: correlate clue to place
    world.para()
    world.say(
        f"{friend.id.lower()} said, 'Let's correlate the marks.' So they lined up "
        f"the clue on the slate with things on the yacht and the water beyond it."
    )
    world.say(
        f"The star mark matched a tiny painted star on a crate, and the crate "
        f"pointed toward {prize_cfg.clue_match}."
    )
    world.say(
        f"{hero.id.lower()} followed the idea with bright eyes. Friendship made "
        f"the clue feel smaller, like a knot being loosened one careful loop at a time."
    )
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1

    # Resolution: find prize
    world.para()
    prize.meters["found"] += 1
    prize.meters["safe"] += 1
    slate.meters["polished"] += 1
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"They found {prize.phrase} exactly where the slate had pointed: {prize_cfg.location}."
    )
    world.say(
        f"{hero.id.lower()} gave the prize a careful hug, and {friend.id.lower()} "
        f"laughed because the magic slate had not been bossy at all. It had only "
        f"helped them notice what belonged together."
    )
    world.say(
        f"By sunset, the yacht rocked softly, the slate was shiny again, and the two "
        f"friends sat side by side with the recovered prize between them."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        prize=prize,
        slate=slate,
        prize_cfg=prize_cfg,
        clue=prize_cfg.clue_mark,
        location=prize_cfg.clue_match,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle animal story about a yacht, a magic slate, and the word "{f["clue"]}".',
        f"Tell a child-friendly story where {f['hero'].label} and {f['friend'].label} "
        f"use friendship to correlate clues and find a lost treasure.",
        f"Write a short story on a yacht where a slate gives a hint and friends solve it together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    prize: Entity = f["prize"]
    prize_cfg: Prize = f["prize_cfg"]

    return [
        QAItem(
            question="Where did the story happen?",
            answer="It happened on a little yacht out on the water.",
        ),
        QAItem(
            question=f"What did {hero.id.lower()} and {friend.id.lower()} find?",
            answer="They found a magic slate with a clue on it.",
        ),
        QAItem(
            question=f"What did they do to solve the clue?",
            answer="They correlated the marks on the slate with things they could see and followed the matching hint.",
        ),
        QAItem(
            question=f"What prize did they recover?",
            answer=f"They recovered {prize_cfg.phrase} and kept it safe.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The friends sat together on the rocking yacht with the prize back in place and the slate shining again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a yacht?",
            answer="A yacht is a boat made for sailing, often with a little cabin and a deck to stand on.",
        ),
        QAItem(
            question="What does correlate mean?",
            answer="To correlate means to match one clue with another so you can see how they fit together.",
        ),
        QAItem(
            question="What is slate?",
            answer="Slate is a hard, smooth stone that can be dark gray and flat like a board.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind, caring bond between friends who help and trust each other.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic in a story is something surprising that seems to work in a special, wondrous way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story q&a ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world q&a ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(sorted(ANIMALS))
    friend = args.friend or rng.choice(sorted(FRIENDS))
    prize = args.prize or rng.choice(sorted(PRIZES))
    if (hero, prize) not in valid_combos():
        raise StoryError(explain_rejection(hero, prize))
    return StoryParams(hero=hero, friend=friend, prize=prize, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: round(v, 2) for k, v in ent.meters.items() if v}
        memes = {k: round(v, 2) for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id:6} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  wind={world.wind}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: yacht, slate, magic, and friendship.")
    ap.add_argument("--hero", choices=sorted(ANIMALS))
    ap.add_argument("--friend", choices=sorted(FRIENDS))
    ap.add_argument("--prize", choices=sorted(PRIZES))
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/2."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(combos)} compatible hero/prize pairs:")
        for hero, prize in combos:
            print(f"  {hero:8} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for hero, prize in valid_combos():
            params = StoryParams(hero=hero, friend="seagull", prize=prize, seed=base_seed)
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            if params.seed is None:
                params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
