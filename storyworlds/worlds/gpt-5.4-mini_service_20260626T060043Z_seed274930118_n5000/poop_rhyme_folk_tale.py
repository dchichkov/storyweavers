#!/usr/bin/env python3
"""
A small folk-tale storyworld about a troublesome poop stain, a helpful rhyme,
and a tidy ending.
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
    visible: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "maiden"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    place: str
    rhyme: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    rhyme_mode: bool = False

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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.rhyme_mode = self.rhyme_mode
        return w


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
PLACES = {
    "forest": {
        "label": "the forest",
        "opening": "In the deep green forest, where the pine trees swayed and the brook sang low, folk told old tales by firelight.",
        "ending": "The forest stayed bright and kindly, as if it too had heard the good rhyme.",
    },
    "village": {
        "label": "the village lane",
        "opening": "By the village lane, where the hens pecked and the chimney smoke curled, folk traded stories as the evening grew still.",
        "ending": "The lane grew neat again, and every door opened to a sweeter smell.",
    },
    "meadow": {
        "label": "the meadow",
        "opening": "Across the wide meadow, where the daisies nodded and the bees hummed, an old folk tale drifted on the breeze.",
        "ending": "The meadow glittered clean, peaceful as a lullaby.",
    },
}

RHYMES = {
    "clean_up": {
        "line1": "A bit of poop, a bit of goo,",
        "line2": "A little mess for me and you.",
        "line3": "With broom and pail and a careful tune,",
        "line4": "We'd tidy it up before the moon.",
    },
    "soft_step": {
        "line1": "Step soft, step slow, keep your nose up high,",
        "line2": "For stink can wander where the blackbirds fly.",
        "line3": "But a brave small heart with a helpful song",
        "line4": "Can set a foul old trouble right and strong.",
    },
    "barnyard": {
        "line1": "In barn and path, in grass and clay,",
        "line2": "Messy things do not stay.",
        "line3": "One good rhyme and one good hand,",
        "line4": "Can sweep the trouble from the land.",
    },
}

_NAMES = ["Mira", "Nell", "Tob", "Pip", "Wren", "Owen", "Annie", "Gus"]
_TYPES = ["girl", "boy"]
_HELPERS = ["grandmother", "grandfather", "neighbor", "cousin"]
_HELPER_TYPES = {"grandmother": "woman", "grandfather": "man", "neighbor": "man", "cousin": "boy"}
_TRAITS = ["kind", "brave", "gentle", "clever", "cheery"]


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
class WorldEngine:
    def __init__(self, world: World):
        self.world = world

    def introduce(self, hero: Entity, helper: Entity, rhyme: str) -> None:
        place = self.world.place
        self.world.say(self.world.facts["opening"])
        self.world.say(
            f"Now {hero.id} was a {hero.memes['trait']} little {hero.type}, and {helper.id} was the sort of helper who knew old remedies and old songs."
        )
        self.world.say(
            f"They carried a rag, a pail, and the rhyme, '{rhyme}.'"
        )

    def problem(self, hero: Entity) -> None:
        mess = self.world.get("poop")
        hero.meters["yuck"] += 1
        mess.meters["stink"] += 1
        hero.memes["distress"] += 1
        self.world.say(
            f"Then there on the path lay a steaming poop splat, dark as river mud and smelly as a troll's sock."
        )
        self.world.say(
            f"{hero.id} pinched {hero.pronoun('possessive')} nose and wrinkled {hero.pronoun('possessive')} face. "
            f"'{self.world.facts['rhyme_line']}' sang the little voice in the air."
        )

    def turn(self, hero: Entity, helper: Entity) -> None:
        if ("clean", hero.id) not in self.world.fired:
            self.world.fired.add(("clean", hero.id))
            hero.memes["distress"] = max(0.0, hero.memes["distress"] - 1)
            self.world.get("poop").meters["stink"] = 0
            self.world.get("poop").visible = False
            self.world.say(
                f"{helper.id} laughed softly and said, 'A rhyme can guide the hands.'"
            )
            self.world.say(
                f"So together they fetched water, wiped the path, and covered the nasty spot with fresh earth and leaves."
            )

    def ending(self, hero: Entity, helper: Entity) -> None:
        self.world.say(
            f"At last {hero.id} stood tall again, and {helper.id} nodded as the {self.world.place} breathed easy."
        )
        self.world.say(
            f"{self.world.facts['ending']}"
        )
        self.world.say(
            f"And that is how a poop mess lost its stink, because a kind helper, a brave child, and a tidy rhyme made the whole lane sweet once more."
        )


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(place: str, rhyme: str) -> bool:
    return place in PLACES and rhyme in RHYMES


def explain_rejection(place: str, rhyme: str) -> str:
    return f"(No story: unknown place/rhyme combination {place!r}/{rhyme!r}.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/2.

valid(P, R) :- place(P), rhyme(R), can_story(P, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for rid in RHYMES:
        lines.append(asp.fact("rhyme", rid))
    for pid in PLACES:
        for rid in RHYMES:
            if valid_combo(pid, rid):
                lines.append(asp.fact("can_story", pid, rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, r) for p in PLACES for r in RHYMES if valid_combo(p, r)}
    asps = set(asp_valid_combos())
    if py == asps:
        print(f"OK: clingo gate matches valid_combo() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combo():")
    print(" only in python:", sorted(py - asps))
    print(" only in clingo:", sorted(asps - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    if not valid_combo(params.place, params.rhyme):
        raise StoryError(explain_rejection(params.place, params.rhyme))

    place = PLACES[params.place]
    rhyme = RHYMES[params.rhyme]
    w = World(place=place["label"])
    w.facts["opening"] = place["opening"]
    w.facts["ending"] = place["ending"]
    w.facts["rhyme_line"] = rhyme["line1"]
    w.facts["rhyme_name"] = params.rhyme

    hero = w.add(Entity(
        id=params.hero, kind="character", type=params.hero_type,
        memes={"trait": params.hero_type, "distress": 0.0},
        meters={"yuck": 0.0},
    ))
    hero.memes["trait"] = params.hero_type
    hero.memes["kindness"] = 1.0

    helper = w.add(Entity(
        id=params.helper, kind="character", type=params.helper_type,
        memes={"helpfulness": 1.0},
    ))
    w.add(Entity(
        id="poop", kind="thing", type="poop", label="poop", phrase="a poop mess",
        meters={"stink": 1.0}, memes={"gross": 1.0},
    ))

    engine = WorldEngine(w)
    w.rhyme_mode = True
    engine.introduce(hero, helper, params.rhyme)
    w.para()
    engine.problem(hero)
    w.para()
    engine.turn(hero, helper)
    engine.ending(hero, helper)

    w.facts.update(hero=hero, helper=helper, place=params.place, rhyme=params.rhyme)
    return w


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short folk tale for a child about {f['hero'].id}, a poop mess, and a rhyme that helps.",
        f"Tell a gentle story in a folk-tale voice where {f['helper'].id} and {f['hero'].id} clean up a poop stain by singing a rhyme.",
        f"Write a simple tale about a smelly poop on a path, a brave helper, and a clean ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, with {helper.id} helping in {PLACES[place]['label']}.",
        ),
        QAItem(
            question=f"What made the children and helpers stop on the path?",
            answer="They stopped because they found a poop mess on the ground and wanted to clean it up.",
        ),
        QAItem(
            question=f"How did {helper.id} help solve the problem?",
            answer=f"{helper.id} used water, a rag, fresh earth, and an old rhyme to help {hero.id} clean the poop away.",
        ),
        QAItem(
            question=f"What changed by the end of the tale?",
            answer="The messy spot was cleaned, the stink was gone, and the place felt sweet and peaceful again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is poop?",
            answer="Poop is waste from an animal or person. It can smell bad and needs to be cleaned up.",
        ),
        QAItem(
            question="Why do people wash or clean messy places?",
            answer="People clean messy places so they do not smell bad, spread germs, or make walking unpleasant.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a small song or saying where the ending sounds match, which makes it easy to remember.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  rhyme_mode={world.rhyme_mode}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale world about poop, rhyme, and a tidy ending.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--rhyme", choices=sorted(RHYMES))
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=sorted(set(_TYPES)))
    ap.add_argument("--helper", choices=sorted(_HELPERS))
    ap.add_argument("--helper-type", choices=sorted(set(_HELPER_TYPES.values())))
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
    place = args.place or rng.choice(sorted(PLACES))
    rhyme = args.rhyme or rng.choice(sorted(RHYMES))
    if not valid_combo(place, rhyme):
        raise StoryError(explain_rejection(place, rhyme))

    hero_type = args.hero_type or rng.choice(_TYPES)
    hero = args.hero or rng.choice(_NAMES)
    helper = args.helper or rng.choice(_HELPERS)
    helper_type = args.helper_type or _HELPER_TYPES[helper]
    return StoryParams(hero=hero, hero_type=hero_type, helper=helper, helper_type=helper_type, place=place, rhyme=rhyme)


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
    StoryParams(hero="Mira", hero_type="girl", helper="grandmother", helper_type="woman", place="forest", rhyme="clean_up"),
    StoryParams(hero="Gus", hero_type="boy", helper="neighbor", helper_type="man", place="village", rhyme="soft_step"),
    StoryParams(hero="Nell", hero_type="girl", helper="cousin", helper_type="boy", place="meadow", rhyme="barnyard"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for place, rhyme in triples:
            print(f"  {place:8} {rhyme}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.place} / {p.rhyme}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
