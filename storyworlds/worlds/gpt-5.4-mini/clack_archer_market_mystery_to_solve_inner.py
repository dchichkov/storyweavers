#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/clack_archer_market_mystery_to_solve_inner.py
==============================================================================

A small standalone storyworld for an adventure at a market: a child hears a
strange clack, follows an inner monologue, solves a mystery, and gets a surprise
ending.

The world is built around a market setting with a few typed entities that carry
physical meters and emotional memes. The central tension is a missing-object
mystery that can be solved by noticing a clue, thinking through possibilities,
and asking the right helper at the right stall.

Requirements covered:
- stdlib only
- imports storyworlds/results.py eagerly
- StoryParams, build_parser, resolve_params, generate, emit, main
- -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- Python reasonableness gate + inline ASP twin
- story-grounded and world-knowledge QA sets
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"busy": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Market:
    id: str
    stalls: list[str]
    bustle: str


@dataclass
class Clue:
    id: str
    kind: str
    sound: str
    source: str
    meaning: str


@dataclass
class Mystery:
    id: str
    missing: str
    likely_hiding: str
    helper: str
    surprise: str


@dataclass
class World:
    market: Market
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        clone = World(self.market)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


MARKETS = {
    "market": Market("market", ["fruit stall", "toy stall", "bread stall", "cloth stall"], "full of bright voices"),
}

HERO_NAMES = ["Aria", "Milo", "Nina", "Leo", "Ivy", "Ezra", "Zoe", "Noah"]
HELPER_NAMES = ["Bram", "Lena", "Sana", "Tari", "Mina", "Owen"]


CLUES = {
    "clack_cart": Clue("clack_cart", "clack", "clack-clack", "a cart wheel", "something wheeled by just now"),
    "clack_wood": Clue("clack_wood", "clack", "clack", "a wooden sign", "a loose board had bumped the post"),
    "clack_jar": Clue("clack_jar", "clack", "clack", "a jar lid", "something had tapped inside a basket"),
}

MYSTERIES = {
    "missing_apple": Mystery("missing_apple", "a shiny red apple", "under the bread stall", "bread seller", "a surprise gift of apple slices"),
    "missing_key": Mystery("missing_key", "a tiny brass key", "in the cloth stall basket", "cloth seller", "a ribbon tied around the key"),
    "missing_pin": Mystery("missing_pin", "a silver pin", "behind the toy stall", "toy seller", "a wooden whistle for the hero"),
}


@dataclass
class StoryParams:
    market: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    clue: str
    mystery: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for mid in MARKETS:
        for clue in CLUES:
            for mystery in MYSTERIES:
                combos.append((mid, clue, mystery))
    return combos


def asp_facts() -> str:
    import asp
    lines = [asp.fact("market", mid) for mid in MARKETS]
    lines += [asp.fact("clue", cid) for cid in CLUES]
    lines += [asp.fact("mystery", mid) for mid in MYSTERIES]
    lines += [asp.fact("has_sound", cid, CLUES[cid].sound) for cid in CLUES]
    return "\n".join(lines)


ASP_RULES = r"""
valid(M, C, X) :- market(M), clue(C), mystery(X).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def reasonable_gate(clue: Clue, mystery: Mystery) -> bool:
    return clue.sound == "clack" and mystery.helper in {"bread seller", "cloth seller", "toy seller"}


def _find_helper_line(helper: Entity, mystery: Mystery) -> str:
    if mystery.helper == "bread seller":
        return f"The bread seller smiled and pointed at a basket by the bread stall."
    if mystery.helper == "cloth seller":
        return f"The cloth seller leaned over a crate and lifted a flap of cloth."
    return f"The toy seller laughed softly and tapped a box beside the stall."


def build_world(params: StoryParams) -> World:
    market = MARKETS[params.market]
    world = World(market)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    clue = CLUES[params.clue]
    mystery = MYSTERIES[params.mystery]

    hero.memes["curiosity"] = 2.0
    helper.memes["joy"] = 1.0
    world.facts.update(hero=hero, helper=helper, clue=clue, mystery=mystery)
    return world


def predict_solution(world: World) -> bool:
    return True


def tell(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    clue: Clue = world.facts["clue"]
    mystery: Mystery = world.facts["mystery"]

    world.say(
        f"{hero.id} wandered through the {world.market.id}, where it was {world.market.bustle}. "
        f"Stalls stood in a row, and {hero.id} was hunting for {mystery.missing}."
    )
    world.say(
        f"Then {hero.id} heard a {clue.sound} near the crowd. "
        f"{hero.id} stopped and listened. 'What made that sound?' {hero.pronoun()} wondered."
    )
    hero.memes["curiosity"] += 1
    hero.memes["worry"] += 1
    world.para()
    world.say(
        f"In {hero.pronoun('possessive')} head, a small voice began to talk. "
        f"'Maybe it came from {clue.source},' {hero.id} thought. "
        f"'No, wait, maybe someone dropped {mystery.missing}.'"
    )
    world.say(
        f"{hero.id} followed the sound to the {mystery.likely_hiding}. "
        f"{_find_helper_line(helper, mystery)}"
    )
    world.para()
    world.say(
        f"The helper had found {mystery.missing} and was keeping it safe for the owner. "
        f"{hero.id} gave a proud little grin, because the mystery finally made sense."
    )
    world.say(
        f"Then came the surprise: {mystery.surprise}. "
        f"{hero.id} laughed, and {helper.id} waved as the market light seemed brighter than before."
    )
    hero.memes["joy"] += 2
    helper.memes["joy"] += 1
    world.facts["solved"] = True
    world.facts["ending_surprise"] = mystery.surprise


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    mystery: Mystery = f["mystery"]
    clue: Clue = f["clue"]
    return [
        f'Write an adventure story for a 3-to-5-year-old set in a market. Include the words "clack" and "archer".',
        f"Tell a story where {hero.id} hears {clue.sound} in the market, thinks hard in an inner monologue, solves the mystery, and gets a surprise ending.",
        f"Write a market mystery with a child hero, a clue sound, and a surprise reward after {mystery.missing} is found.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    clue: Clue = f["clue"]
    mystery: Mystery = f["mystery"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id}, who was exploring the market and looking for a mystery to solve. {hero.id} solved it by paying attention and asking for help."),
        ("What sound did the hero hear?",
         f"{hero.id} heard a {clue.sound}. That sound was the clue that led {hero.pronoun('object')} to the right stall."),
        ("What did the hero think in the inner monologue?",
         f"{hero.id} wondered what made the sound and guessed where it might have come from. {hero.id} kept thinking until the guess matched the clue."),
        ("How was the mystery solved?",
         f"{helper.id} showed where {mystery.missing} was being kept safe. The clue, the careful thinking, and the helper's answer solved the mystery."),
        ("What was the surprise at the end?",
         f"The surprise was {mystery.surprise}. It made the ending feel like a cheerful adventure instead of an ordinary walk through the market."),
    ]


WORLD_KNOWLEDGE = {
    "market": [("What is a market?",
               "A market is a place where people buy and sell things at stalls or tables.")],
    "clack": [("What can make a clack sound?",
              "A clack can come from a wheel, a board, a lid, or something hard tapping another thing.")],
    "archer": [("What is an archer?",
               "An archer is a person who uses a bow to shoot arrows.")],
    "mystery": [("What is a mystery?",
                "A mystery is something puzzling that you need clues to solve.")],
    "surprise": [("What is a surprise?",
                 "A surprise is something unexpected that makes a story feel exciting or special.")],
    "inner": [("What is an inner monologue?",
              "An inner monologue is the little voice inside your head that says what you are thinking.")],
}
WORLD_ORDER = ["market", "clack", "archer", "mystery", "inner", "surprise"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for key in WORLD_ORDER:
        if key in WORLD_KNOWLEDGE:
            out.extend(WORLD_KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type}) role={e.role} meters={e.meters} memes={e.memes}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


CURATED = [
    StoryParams("market", "Archer", "boy", "Mina", "girl", "clack_cart", "missing_apple"),
    StoryParams("market", "Ari", "girl", "Owen", "boy", "clack_wood", "missing_key"),
    StoryParams("market", "Noah", "boy", "Lena", "girl", "clack_jar", "missing_pin"),
]


def explain_rejection(clue: Clue, mystery: Mystery) -> str:
    return f"(No story: the clue and mystery do not form a clear market puzzle.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.mystery:
        clue, mystery = CLUES[args.clue], MYSTERIES[args.mystery]
        if not reasonable_gate(clue, mystery):
            raise StoryError(explain_rejection(clue, mystery))
    combos = [c for c in valid_combos()
              if (args.market is None or c[0] == args.market)
              and (args.clue is None or c[1] == args.clue)
              and (args.mystery is None or c[2] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    market, clue, mystery = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    return StoryParams(market, hero, hero_gender, helper, helper_gender, clue, mystery)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
        try:
            s = generate(CURATED[0])
            assert s.story
            print("OK: generate() smoke test passed.")
        except Exception as exc:
            print(f"SMOKE TEST FAILED: {exc}")
            return 1
        return 0
    print("MISMATCH between ASP and Python gate.")
    if cl - py:
        print(" only in ASP:", sorted(cl - py))
    if py - cl:
        print(" only in Python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure market mystery storyworld.")
    ap.add_argument("--market", choices=MARKETS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
