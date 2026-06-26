#!/usr/bin/env python3
"""
Standalone storyworld: pirate tale mystery, humor, and a quest to solve the
stamp that made the mucus curdle.

Premise:
- A small crew sails a bright little sea.
- A strange stamped jar of mucus curdles in the heat.
- The crew must solve where the stamp came from and why it matters.

The world is built as a tiny simulation:
- physical meters: freshness, stink, heat, wetness, ink, clue, treasure
- emotional memes: curiosity, worry, bravado, relief, laughter, trust

Story shape:
1. Setup: the crew finds the odd curdled mucus.
2. Tension: the stamp suggests a hidden sender or thief.
3. Turn: the crew follows clues through the ship and dock.
4. Resolution: the mystery is solved with a humorous reveal and a clear ending image.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pirate", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "captainess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little pirate harbor"
    sea: str = "sunny"
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    name: str
    location: str
    reveal: str
    humor: str


@dataclass
class StoryParams:
    setting: str
    hero: str
    sidekick: str
    culprit: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for e in self.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={dict(meters)}")
            if memes:
                bits.append(f"memes={dict(memes)}")
            if e.location:
                bits.append(f"location={e.location}")
            lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
        lines.append(f"  fired rules: {sorted({a for a, *_ in self.fired})}")
        return "\n".join(lines)


@dataclass
class Rule:
    name: str
    apply: callable


def _r_curdle(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters.get("mucus", 0.0) < THRESHOLD:
            continue
        if e.meters.get("heat", 0.0) < THRESHOLD:
            continue
        sig = ("curdle", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["curdled"] = 1.0
        e.meters["stink"] = e.meters.get("stink", 0.0) + 1.0
        out.append(f"The mucus curdled in the heat.")
    return out


def _r_stamp_clue(world: World) -> list[str]:
    out: list[str] = []
    mucus = world.entities.get("mucus-jar")
    if not mucus:
        return out
    if mucus.meters.get("stamp", 0.0) < THRESHOLD:
        return out
    sig = ("stamp_clue", mucus.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mucus.meters["clue"] = 1.0
    out.append("The stamp left a clue like a tiny anchor with a grin.")
    return out


def _r_laughter(world: World) -> list[str]:
    out: list[str] = []
    if world.entities["hero"].memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    if world.entities["sidekick"].memes.get("bravado", 0.0) < THRESHOLD:
        return out
    sig = ("laugh",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.entities["hero"].memes["laughter"] = 1.0
    world.entities["sidekick"].memes["laughter"] = 1.0
    out.append("They laughed, because even a mystery can look silly in a spoon.")
    return out


CAUSAL_RULES = [
    Rule("curdle", _r_curdle),
    Rule("stamp_clue", _r_stamp_clue),
    Rule("laughter", _r_laughter),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setup_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    hero = world.add(Entity(
        id="hero", kind="character", type="captain", label=params.hero
    ))
    sidekick = world.add(Entity(
        id="sidekick", kind="character", type="pirate", label=params.sidekick
    ))
    culprit = world.add(Entity(
        id="culprit", kind="character", type="pirate", label=params.culprit
    ))
    mucus = world.add(Entity(
        id="mucus-jar", type="jar", label="jar of mucus",
        phrase="a jar of strange mucus",
        owner=hero.id, location="deck"
    ))
    stamp = world.add(Entity(
        id="stamp", type="seal", label="wax stamp",
        phrase="a wax stamp with a tiny anchor",
        owner=culprit.id, location="captain's locker"
    ))
    map_piece = world.add(Entity(
        id="map", type="paper", label="scrap map",
        phrase="a folded scrap map", location="dock"
    ))

    hero.memes["curiosity"] = 1.0
    sidekick.memes["bravado"] = 1.0
    culprit.memes["worry"] = 1.0

    mucus.meters["mucus"] = 1.0
    mucus.meters["heat"] = 1.0
    mucus.meters["stink"] = 0.5
    stamp.meters["stamp"] = 1.0
    stamp.meters["ink"] = 1.0
    map_piece.meters["clue"] = 1.0

    world.facts = {
        "hero": hero,
        "sidekick": sidekick,
        "culprit": culprit,
        "mucus": mucus,
        "stamp": stamp,
        "map": map_piece,
        "setting": setting,
    }
    return world


def start_story(world: World) -> None:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    mucus = world.facts["mucus"]
    world.say(
        f"On {world.setting.place}, Captain {hero.label} found a jar of mucus on the deck."
    )
    world.say(
        f"It looked odd and smelled funny, and {sidekick.label} said it was the sort of thing "
        f"that could make a sailor wrinkle a nose for a week."
    )
    world.say(
        f"Then they saw a wax stamp on the lid, shaped like a tiny anchor."
    )
    propagate(world, narrate=True)


def mystery_turn(world: World) -> None:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    stamp = world.facts["stamp"]
    culprit = world.facts["culprit"]
    world.para()
    world.say(
        f"{hero.label} scratched {hero.pronoun('possessive')} chin and asked who would stamp mucus at sea."
    )
    world.say(
        f"{sidekick.label} peered at the mark and declared, very boldly, that only a sneaky deck goblin would do such a thing."
    )
    world.say(
        f"They followed the clue from the deck to the captain's locker, where the same anchor shape was hidden on {culprit.label}'s kit."
    )
    world.say(
        f"The answer felt close, but the crew still needed to know why the stamp was there at all."
    )


def solve_story(world: World) -> None:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    culprit = world.facts["culprit"]
    world.para()
    world.say(
        f"At last {hero.label} found the truth: {culprit.label} had stamped the jar by mistake while trying to seal a fish pie."
    )
    world.say(
        f"The pie had slipped, the lid had stuck, and the mucus had ended up with the wrong mark on it like a very grumpy badge."
    )
    world.say(
        f"{sidekick.label} burst out laughing, because the grand mystery was really a kitchen blunder wearing a pirate hat."
    )
    world.say(
        f"{culprit.label} apologized, then laughed too, and the three of them washed the jar clean while the gulls shouted above the harbor."
    )
    world.say(
        f"By sunset, the jar was empty, the clue was solved, and the crew was eating the spoiled pie crust like treasure."
    )
    propagate(world, narrate=True)
    world.facts["resolved"] = True


SETTING = Setting(place="the little pirate harbor", sea="sunny", affords={"mystery", "quest", "humor"})


HERO_NAMES = ["Captain Miri", "Captain Ned", "Captain Tamsin", "Captain Rook"]
SIDEKICK_NAMES = ["Barnacle Ben", "Nettle Nell", "Jolly Jace", "Merry Mae"]
CULPRIT_NAMES = ["Old Salt Brigg", "Pegleg Pru", "Snout Finn", "Sailor Squeak"]


def choose_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        setting=args.setting or "harbor",
        hero=args.hero or rng.choice(HERO_NAMES),
        sidekick=args.sidekick or rng.choice(SIDEKICK_NAMES),
        culprit=args.culprit or rng.choice(CULPRIT_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    start_story(world)
    mystery_turn(world)
    solve_story(world)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"].label
    sidekick = world.facts["sidekick"].label
    return [
        f"Write a pirate tale mystery where {hero} finds stamped mucus and {sidekick} helps solve it with humor.",
        "Tell a short quest story about a strange jar, a hidden stamp, and a clue that leads to a silly reveal.",
        "Make a gentle sea adventure that starts with curdled mucus and ends with the crew laughing together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"].label
    sidekick = world.facts["sidekick"].label
    culprit = world.facts["culprit"].label
    return [
        QAItem(
            question="What strange thing did the crew find on the deck?",
            answer=f"They found a jar of mucus with a wax stamp on it.",
        ),
        QAItem(
            question=f"Who helped {hero} follow the clue?",
            answer=f"{sidekick} helped by looking at the stamp and following the trail to the locker.",
        ),
        QAItem(
            question=f"What was the real reason for {culprit}'s stamp?",
            answer="The stamp was an accident from trying to seal a fish pie, not a secret pirate plot.",
        ),
        QAItem(
            question="How did the mystery end?",
            answer="The crew solved it, laughed at the mistake, and cleaned the jar together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean for something to curdle?",
            answer="To curdle means to thicken or change into lumps, often because heat or acid changes it.",
        ),
        QAItem(
            question="What is mucus?",
            answer="Mucus is a slippery substance made by bodies to help protect and moisten surfaces.",
        ),
        QAItem(
            question="What is a stamp used for?",
            answer="A stamp can leave a mark or seal on paper, wax, or other materials.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    return world.trace()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale mystery world with humor and a quest.")
    ap.add_argument("--setting", choices=["harbor"], default=None)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--culprit")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "harbor"),
        asp.fact("affords", "harbor", "mystery"),
        asp.fact("affords", "harbor", "quest"),
        asp.fact("affords", "harbor", "humor"),
        asp.fact("thing", "mucus"),
        asp.fact("thing", "stamp"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is solvable when there is a stamp clue and a reasoned reveal.
clue(stamp) :- stamp_present.
solved :- clue(stamp), reveal(reason).
valid_story(harbor, mystery, quest, humor) :- solved.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("harbor", "mystery", "quest", "humor")}
    asp_set = set(asp_valid())
    if asp_set == py:
        print(f"OK: clingo gate matches Python gate ({len(py)} story).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("python:", sorted(py))
    print("clingo:", sorted(asp_set))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return choose_params(args, rng)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/4."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(setting="harbor", hero="Captain Miri", sidekick="Barnacle Ben", culprit="Old Salt Brigg")
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
