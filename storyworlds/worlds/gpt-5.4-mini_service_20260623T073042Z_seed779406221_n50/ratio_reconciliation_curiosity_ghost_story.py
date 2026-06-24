#!/usr/bin/env python3
"""
storyworlds/worlds/ratio_reconciliation_curiosity_ghost_story.py
=================================================================

A small standalone story world for a ghost-story-like tale about curiosity,
a strange ratio, and a reconciliation that turns fear into understanding.

Premise:
- A child notices a ghostly pattern in an old house: the ratio of cold windows
  to warm candles keeps changing.
- Curiosity pulls the child toward the mystery.
- A worried grown-up or sibling warns against poking around.
- The child learns the ratio is not a curse at all; it is a clue about how the
  house breathes, and reconciliation follows.

This world models typed entities with physical meters and emotional memes,
supports a Python reasonableness gate and inline ASP twin, and emits complete,
child-facing stories with grounded Q&A.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class House:
    place: str
    window_count: int
    candle_count: int
    has_attic: bool
    has_cellar: bool
    ratio_target: tuple[int, int]
    mood: str
    affordance: str


@dataclass
class Mystery:
    id: str
    clue: str
    what_it_means: str
    cold_meter: str
    warm_meter: str
    turns: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Companion:
    id: str
    label: str
    role: str
    caution: str
    gift: str
    turns_on: str
    plural: bool = False


class World:
    def __init__(self, house: House) -> None:
        self.house = house
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        import copy as _copy
        c = World(self.house)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: callable


def _r_chill_reveals(world: World) -> list[str]:
    out = []
    ghost = world.entities.get("ghost")
    if not ghost or ghost.meters["seen"] < THRESHOLD:
        return out
    sig = ("reveal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.get("child")
    ghost.memes["mystery"] += 1
    child.memes["curiosity"] += 1
    out.append("A clue answered the cold.")
    return out


def _r_ratio_settles(world: World) -> list[str]:
    child = world.entities.get("child")
    if not child or child.memes["understanding"] < THRESHOLD:
        return []
    sig = ("settle",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("house").memes["peace"] = 1
    return ["The house felt peaceful again."]


CAUSAL_RULES = [Rule("reveal", _r_chill_reveals), Rule("settle", _r_ratio_settles)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def ratio_text(windows: int, candles: int) -> str:
    return f"{windows}:{candles}"


def ratio_matches_target(house: House) -> bool:
    return (house.window_count, house.candle_count) == house.ratio_target


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for hid in HOUSES:
        house = HOUSES[hid]
        for mid in MYSTERIES:
            for cid in COMPANIONS:
                if house.window_count > 0 and house.candle_count > 0:
                    combos.append((hid, mid, cid))
    return combos


@dataclass
class StoryParams:
    house: str
    mystery: str
    companion: str
    child_name: str
    child_gender: str
    grownup_name: str
    grownup_gender: str
    trait: str
    seed: Optional[int] = None


HOUSES = {
    "lane_house": House(
        place="the lane house",
        window_count=4,
        candle_count=2,
        has_attic=True,
        has_cellar=False,
        ratio_target=(2, 1),
        mood="quiet",
        affordance="listen closely",
    ),
    "orchard_house": House(
        place="the orchard house",
        window_count=3,
        candle_count=1,
        has_attic=False,
        has_cellar=True,
        ratio_target=(3, 1),
        mood="soft",
        affordance="peer into corners",
    ),
    "harbor_house": House(
        place="the harbor house",
        window_count=5,
        candle_count=3,
        has_attic=True,
        has_cellar=True,
        ratio_target=(5, 3),
        mood="foggy",
        affordance="follow the hush",
    ),
}

MYSTERIES = {
    "cold_ratio": Mystery(
        id="cold_ratio",
        clue="the windows outnumbered the candles",
        what_it_means="the cold rooms were winning the night",
        cold_meter="cold",
        warm_meter="warm",
        turns="count the windows and candles",
        reveal="the pattern was only a draft and a hidden lantern shelf",
        tags={"ratio", "cold", "warm", "ghost"},
    ),
    "lantern_ratio": Mystery(
        id="lantern_ratio",
        clue="the candles made a neat ratio with the windows",
        what_it_means="someone had been leaving lights in the right places",
        cold_meter="cold",
        warm_meter="warm",
        turns="look behind the curtain",
        reveal="the pattern was from a careful grown-up keeping the halls safe",
        tags={"ratio", "light", "ghost"},
    ),
    "breath_ratio": Mystery(
        id="breath_ratio",
        clue="the fog matched the candle glow in a strange ratio",
        what_it_means="the house was breathing in and out through cracked boards",
        cold_meter="cold",
        warm_meter="warm",
        turns="watch the candles flicker",
        reveal="the house was not haunted by danger, only by wind and weather",
        tags={"ratio", "fog", "ghost"},
    ),
}

COMPANIONS = {
    "grandma": Companion("grandma", "Grandma", "grandmother", "gentle", "a quilt", "smiled and listened"),
    "brother": Companion("brother", "Older Brother", "brother", "careful", "a lantern", "held up a hand"),
    "aunt": Companion("aunt", "Aunt May", "aunt", "thoughtful", "a key ring", "knelt beside them"),
}

GIRL_NAMES = ["Mina", "Lena", "Ivy", "Nora", "Elsa", "June"]
BOY_NAMES = ["Theo", "Evan", "Finn", "Owen", "Miles", "Jude"]
TRAITS = ["curious", "brave", "quiet", "gentle", "thoughtful"]


def asp_facts() -> str:
    import asp
    lines = []
    for hid, h in HOUSES.items():
        lines.append(asp.fact("house", hid))
        lines.append(asp.fact("windows", hid, h.window_count))
        lines.append(asp.fact("candles", hid, h.candle_count))
        lines.append(asp.fact("ratio_target", hid, h.ratio_target[0], h.ratio_target[1]))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("tags", mid, "ratio"))
    for cid in COMPANIONS:
        lines.append(asp.fact("companion", cid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(H, M, C) :- house(H), mystery(M), companion(C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world about a ratio, curiosity, and reconciliation.")
    ap.add_argument("--house", choices=HOUSES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--grownup")
    ap.add_argument("--grownup-gender", choices=["woman", "man"])
    ap.add_argument("--trait", choices=TRAITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.house is None or c[0] == args.house)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.companion is None or c[2] == args.companion)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    house, mystery, companion = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    grownup_gender = args.grownup_gender or rng.choice(["woman", "man"])
    grownup = args.grownup or rng.choice(["Mara", "June", "Hank", "Paul"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(house, mystery, companion, name, gender, grownup, grownup_gender, trait)


def tell(params: StoryParams) -> World:
    house = HOUSES[params.house]
    mystery = MYSTERIES[params.mystery]
    companion = COMPANIONS[params.companion]
    world = World(house)
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name))
    grownup = world.add(Entity(id="grownup", kind="character", type=params.grownup_gender, label=params.grownup_name))
    ghost = world.add(Entity(id="ghost", kind="ghost", type="ghost", label="the ghost"))
    home = world.add(Entity(id="house", kind="place", type="house", label=house.place))
    child.memes["curiosity"] = 1
    child.memes["reconciliation"] = 0
    grownup.memes["care"] = 1
    ghost.meters["seen"] = 0
    world.say(f"{child.label} lived in {house.place}, where the nights felt {house.mood} and the rooms held their breath.")
    world.say(f"One evening, {child.label} noticed {mystery.clue} in a way that made {child.pronoun().capitalize()} pause.")
    world.para()
    world.say(f"{child.label} wanted to {mystery.turns}, because {child.pronoun('possessive')} curiosity would not let the question sleep.")
    world.say(f"But {grownup.label} warned, \"Leave the dark places alone. Not every whisper is a friend.\"")
    child.memes["curiosity"] += 1
    child.memes["worry"] += 1
    world.para()
    ghost.meters["seen"] = 1
    propagate(world)
    world.say(f"Still, {child.label} followed the cold air to the hall and found that the ratio was {ratio_text(house.window_count, house.candle_count)}.")
    world.say(f"{mystery.what_it_means.capitalize()}, and that felt less like a haunting and more like a puzzle.")
    world.para()
    world.say(f"{companion.label} came close with {companion.gift} and said they could {companion.turns_on} together.")
    child.memes["understanding"] += 1
    child.memes["reconciliation"] += 1
    grownup.memes["reconciliation"] += 1
    world.say(f"When they counted again, the ratio made sense: {house.window_count} windows and {house.candle_count} candles, just as the house kept telling them.")
    world.say(f"{mystery.reveal.capitalize()}, and the fear in the hallway softened into relief.")
    world.para()
    world.say(f"{child.label} turned back to {grownup.label} and said sorry for sneaking off.")
    world.say(f"{grownup.label} did not scold. {grownup.label_word.capitalize()} smiled, hugged {child.pronoun('object')}, and said the house could be curious without being cruel.")
    world.say(f"Together they set one candle in the right window, and the old house looked peaceful at last.")
    world.facts.update(child=child, grownup=grownup, ghost=ghost, house=house, mystery=mystery, companion=companion, ratio=ratio_text(house.window_count, house.candle_count))
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old about a child who notices a ratio of windows to candles and learns not every spooky thing is a danger.',
        f"Tell a child-facing story where {f['child'].label} feels curious about the ratio {f['ratio']} in {f['house'].place} and makes peace with the grown-up's warning.",
        f'Write a soft spooky story that uses the word "ratio" and ends with reconciliation, not fright.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    grownup = f["grownup"]
    mystery = f["mystery"]
    companion = f["companion"]
    return [
        QAItem(
            question=f"What did {child.label} notice in {f['house'].place}?",
            answer=f"{child.label} noticed a strange ratio of {f['ratio']} and wondered why the old house kept changing its light.",
        ),
        QAItem(
            question=f"Why did {child.label} go looking around the house?",
            answer=f"{child.label} was curious. {child.pronoun().capitalize()} wanted to understand the clue instead of only being afraid of it.",
        ),
        QAItem(
            question=f"Who warned {child.label} to stay out of the dark places?",
            answer=f"{grownup.label} warned {child.label} not to wander alone in the dark hall.",
        ),
        QAItem(
            question=f"How did the story stop feeling spooky?",
            answer=f"It stopped feeling spooky when the ratio made sense, {companion.label} helped explain it, and {child.label} reconciled with {grownup.label}.",
        ),
        QAItem(
            question=f"What did the ratio really mean?",
            answer=f"It was not a curse. It was a clue about light, windows, and the way the house breathed with the weather.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ratio?",
            answer="A ratio is a way to compare how many of one thing there are to how many of another thing there are.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is the wish to ask questions and learn what something means.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making peace again after worry or a disagreement.",
        ),
        QAItem(
            question="Why can an old house feel spooky at night?",
            answer="An old house can feel spooky when it is dark, quiet, and full of strange shadows, even if nothing bad is happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: the requested house, mystery, and companion do not form a sensible ghostly ratio tale.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams("lane_house", "cold_ratio", "grandma", "Mina", "girl", "Mara", "woman", "curious"),
    StoryParams("orchard_house", "lantern_ratio", "brother", "Theo", "boy", "Hank", "man", "quiet"),
    StoryParams("harbor_house", "breath_ratio", "aunt", "Ivy", "girl", "June", "woman", "thoughtful"),
]


def valid_combos_filtered(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    combos = valid_combos()
    out = []
    for c in combos:
        if args.house and c[0] != args.house:
            continue
        if args.mystery and c[1] != args.mystery:
            continue
        if args.companion and c[2] != args.companion:
            continue
        out.append(c)
    return out


def resolve_params_checked(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos_filtered(args)
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    house, mystery, companion = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    grownup_gender = args.grownup_gender or rng.choice(["woman", "man"])
    grownup = args.grownup or rng.choice(["Mara", "June", "Hank", "Paul"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(house, mystery, companion, name, gender, grownup, grownup_gender, trait)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        import asp
        py = set(valid_combos())
        cl = set(asp_valid_combos())
        if py != cl:
            print("MISMATCH")
            print("python-only:", sorted(py - cl))
            print("clingo-only:", sorted(cl - py))
            sys.exit(1)
        print(f"OK: {len(py)} combos")
        return
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} combos")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params_checked(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
