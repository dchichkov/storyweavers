#!/usr/bin/env python3
"""
A folk-tale storyworld about a weensie helper, a village lesson, and a moral
value that spreads from one small act to many.

Seed tale premise:
- A weensie reed-fox notices that the biggest child in the hamlet hoards the
  winter kettle by the hearth.
- The fox cannot outpush the child, but can inspire the child to share.
- The tale turns on a moral value: kindness, fairness, and the habit of
  general-izing one good deed into a village custom.

The world models:
- physical resources in meters: kettle_water, firewood, bread, frost, steps
- emotional/moral memes: pride, fear, shame, trust, hope, kindness, envy
- a tiny causal chain: a shared cup of tea raises trust; trust can inspire a
  better choice; the better choice strengthens moral value; the moral value can
  then be generalized into a rule the village repeats.
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
# Core domain constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"           # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["frost", "water", "wood", "bread", "steps", "warmth"]:
            self.meters.setdefault(k, 0.0)
        for k in ["pride", "fear", "shame", "trust", "hope", "kindness", "envy", "joy", "moral_value"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "foxmaid", "grandmother"}
        male = {"boy", "father", "man", "fox", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str = "the hamlet green"
    affords: set[str] = field(default_factory=lambda: {"share_tea", "sing_tale", "give_bread"})


@dataclass
class Problem:
    id: str
    title: str
    cause: str
    outcome: str
    remedy: str
    moral_word: str


@dataclass
class StoryParams:
    place: str
    problem: str
    hero_name: str
    hero_type: str
    bully_name: str
    bully_type: str
    elder_name: str
    elder_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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


# ---------------------------------------------------------------------------
# Reasoning rules
# ---------------------------------------------------------------------------

def _r_share_tea(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["water"] < THRESHOLD:
        return out
    sig = ("share_tea",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in world.entities.values():
        if e.kind == "character":
            e.memes["trust"] += 0.5
            e.memes["hope"] += 0.25
    out.append("The shared tea warmed more than their hands.")
    return out


def _r_inspire(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    bully = world.get("bully")
    elder = world.get("elder")
    if hero.memes["hope"] < THRESHOLD or bully.memes["pride"] < THRESHOLD:
        return out
    if bully.memes["trust"] < THRESHOLD:
        return out
    sig = ("inspire",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bully.memes["shame"] += 0.5
    bully.memes["pride"] -= 0.5
    elder.memes["joy"] += 0.5
    out.append("A kind word reached even the proud boy.")
    return out


def _r_generalize(world: World) -> list[str]:
    out: list[str] = []
    village = world.get("village")
    hero = world.get("hero")
    if hero.memes["moral_value"] < THRESHOLD:
        return out
    sig = ("generalize",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    village.meters["steps"] += 1
    village.memes["moral_value"] += 1
    out.append("By sunrise, the hamlet was repeating the lesson as a custom.")
    return out


CAUSAL_RULES = [_r_share_tea, _r_inspire, _r_generalize]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# World content
# ---------------------------------------------------------------------------

PLACE = Place(name="the hamlet green")

PROBLEMS = {
    "kettle": Problem(
        id="kettle",
        title="The Kettle by the Hearth",
        cause="one child hoards the winter kettle",
        outcome="the house stays cold and cross",
        remedy="the little helper offers tea and a story",
        moral_word="sharing",
    ),
    "bread": Problem(
        id="bread",
        title="The Bread on the Bench",
        cause="a big child stacks all the bread beside his boots",
        outcome="smaller mouths go hungry at dusk",
        remedy="the helper invites him to divide the loaf fairly",
        moral_word="fairness",
    ),
    "bell": Problem(
        id="bell",
        title="The Bell Rope in the Frost",
        cause="one child will not let anyone ring the warning bell",
        outcome="the goats wander and the yard grows messy",
        remedy="the helper inspires the child to let others help",
        moral_word="care",
    ),
}

HEROES = [
    ("Pip", "fox"),
    ("Mina", "girl"),
    ("Tobin", "boy"),
    ("Nell", "girl"),
]

BULLIES = [
    ("Hob", "boy"),
    ("Rusk", "boy"),
    ("Bran", "boy"),
    ("Jessa", "girl"),
]

ELDERS = [
    ("Gran", "grandmother"),
    ("Moss", "grandfather"),
    ("Wren", "woman"),
]


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    world = World(PLACE)
    problem = PROBLEMS[params.problem]

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
    ))
    bully = world.add(Entity(
        id="bully",
        kind="character",
        type=params.bully_type,
        label=params.bully_name,
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=params.elder_type,
        label=params.elder_name,
    ))
    village = world.add(Entity(
        id="village",
        kind="thing",
        type="village",
        label="the village",
    ))

    # Act 1
    world.say(
        f"Long ago, in {world.place.name}, there lived a weensie helper named "
        f"{hero.label}. {hero.pronoun().capitalize()} was little enough to hide "
        f"behind a teacup, but {hero.pronoun('possessive')} heart was large."
    )
    world.say(
        f"One day {hero.label} saw {bully.label}, a proud {bully.type}, "
        f"holding the {problem.title.lower()}."
    )
    world.say(
        f"The trouble was simple: {problem.cause}. Because of that, {problem.outcome}."
    )

    # Act 2
    world.para()
    hero.meters["water"] += 1
    hero.memes["hope"] += 1
    hero.memes["kindness"] += 1
    world.say(
        f"{hero.label} brought a tiny pot of tea from the stone step and set it near "
        f"{bully.label}'s boots."
    )
    world.say(
        f"{hero.pronoun().capitalize()} did not shout. Instead, {hero.pronoun()} spoke "
        f"softly, because small voices can slip through a closed door."
    )
    propagate(world)
    bully.memes["trust"] += 0.75
    bully.memes["pride"] += 0.25
    world.say(
        f"{bully.label} blinked. The warm cup made {bully.pronoun('possessive')} hands "
        f"less tight, and the frost on {problem.title.lower()} seemed a little smaller."
    )

    world.say(
        f"Then {hero.label} told a tale about a crow who learned that a single berry "
        f"tastes sweeter when it is shared."
    )
    bully.memes["shame"] += 0.5
    bully.memes["hope"] += 0.5
    world.say(
        f"{elder.label} listened from the gate and nodded, for old hearts remember "
        f"that a village grows by repeated good deeds."
    )

    # Act 3
    world.para()
    hero.memes["moral_value"] += 1.0
    bully.memes["trust"] += 1.0
    bully.meters["bread"] += 0.0
    world.say(
        f"At last, {bully.label} set the {problem.title.lower()} down by the fire and "
        f"lifted a share for everyone."
    )
    world.say(
        f"{hero.label} smiled, and the little lesson grew legs: not just one kind act, "
        f"but a way of living."
    )
    propagate(world)
    world.say(
        f"By the end, the hamlet kept {problem.moral_word} in its daily songs, and "
        f"{hero.label}'s weensie kindness was remembered as the thing that changed the room."
    )

    world.facts.update(
        hero=hero,
        bully=bully,
        elder=elder,
        village=village,
        problem=problem,
        place=world.place,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: Problem = f["problem"]
    h: Entity = f["hero"]
    return [
        f'Write a short folk tale about a weensie helper who can {p.remedy} and inspire a change of heart.',
        f"Tell a child-friendly story where {h.label} helps a proud child learn {p.moral_word} in the hamlet.",
        f"Write a gentle tale that includes the words 'weensie', 'general-ize', and 'inspire' and ends with a moral value becoming a custom.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    bully: Entity = f["bully"]
    elder: Entity = f["elder"]
    problem: Problem = f["problem"]
    return [
        QAItem(
            question=f"Who was the weensie helper in the story?",
            answer=f"The weensie helper was {hero.label}, a small {hero.type} with a big heart.",
        ),
        QAItem(
            question=f"What was the main trouble in {world.place.name}?",
            answer=f"The trouble was {problem.cause}, which meant {problem.outcome}.",
        ),
        QAItem(
            question=f"What did {hero.label} do first to help?",
            answer=f"{hero.label} brought a tiny pot of tea and spoke softly instead of scolding {bully.label}.",
        ),
        QAItem(
            question=f"How did the helper inspire {bully.label}?",
            answer=f"{hero.label}'s calm words and warm tea gave {bully.label} enough trust to choose sharing over pride.",
        ),
        QAItem(
            question=f"What did the elder understand at the gate?",
            answer=f"{elder.label} understood that one good act can be general-ized into a village habit when people repeat it.",
        ),
        QAItem(
            question=f"What moral value stayed with the hamlet at the end?",
            answer=f"The hamlet remembered {problem.moral_word}, and that became part of its daily songs.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "weensie": (
        "What does weensie mean?",
        "Weensie means very small or tiny, like something that can fit in the palm of your hand.",
    ),
    "generalize": (
        "What does general-ize mean?",
        "To general-ize means to take one lesson and use it in many places, like making one kind act into a habit.",
    ),
    "inspire": (
        "What does it mean to inspire someone?",
        "To inspire someone means to make them want to do something good or brave by your example or words.",
    ),
    "moral_value": (
        "What is a moral value?",
        "A moral value is a good idea about how to treat others, such as kindness, fairness, or honesty.",
    ),
    "folk tale": (
        "What is a folk tale?",
        "A folk tale is a story people tell and retell for many years, often with a lesson or a bit of magic.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for _, (q, a) in WORLD_KNOWLEDGE.items()]


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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(H) :- entity(H), kind(H,character), role(H,hero).
problem(P) :- entity(P), kind(P,problem).
moral_value(V) :- value(V).
can_inspire(H) :- hero(H), meme(H,hope,1), meme(H,kindness,1).
shared_tea(H) :- hero(H), meter(H,water,1).
generalized(V) :- moral(V), value_word(V,W), word(W).

good_story(H,P) :- can_inspire(H), shared_tea(H), problem(P), moral(P,V), generalized(V).

#show good_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("entity", "hero"))
    lines.append(asp.fact("kind", "hero", "character"))
    lines.append(asp.fact("role", "hero", "hero"))
    lines.append(asp.fact("entity", "problem"))
    lines.append(asp.fact("kind", "problem", "problem"))
    lines.append(asp.fact("value", "moral_value"))
    lines.append(asp.fact("moral", "kettle", "moral_value"))
    lines.append(asp.fact("value_word", "moral_value", "kindness"))
    lines.append(asp.fact("word", "kindness"))
    lines.append(asp.fact("meme", "hero", "hope", 1))
    lines.append(asp.fact("meme", "hero", "kindness", 1))
    lines.append(asp.fact("meter", "hero", "water", 1))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/2."))
    asp_good = sorted(set(asp.atoms(model, "good_story")))
    py_good = [("hero", "kettle")]
    if asp_good == py_good:
        print("OK: clingo gate matches Python reasonableness gate (1 story).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("  clingo:", asp_good)
    print("  python:", py_good)
    return 1


# ---------------------------------------------------------------------------
# Parameter resolution and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny folk-tale storyworld about a weensie helper and a moral value.")
    ap.add_argument("--place", choices=["hamlet"], default=None)
    ap.add_argument("--problem", choices=sorted(PROBLEMS), default=None)
    ap.add_argument("--hero-name", default=None)
    ap.add_argument("--hero-type", choices=["fox", "girl", "boy"], default=None)
    ap.add_argument("--bully-name", default=None)
    ap.add_argument("--bully-type", choices=["boy", "girl"], default=None)
    ap.add_argument("--elder-name", default=None)
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather", "woman"], default=None)
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
    problem = args.problem or rng.choice(sorted(PROBLEMS))
    hero_name, hero_type = (args.hero_name, args.hero_type) if args.hero_name and args.hero_type else rng.choice(HEROES)
    bully_name, bully_type = (args.bully_name, args.bully_type) if args.bully_name and args.bully_type else rng.choice(BULLIES)
    elder_name, elder_type = (args.elder_name, args.elder_type) if args.elder_name and args.elder_type else rng.choice(ELDERS)
    return StoryParams(
        place="hamlet",
        problem=problem,
        hero_name=hero_name,
        hero_type=hero_type,
        bully_name=bully_name,
        bully_type=bully_type,
        elder_name=elder_name,
        elder_type=elder_type,
    )


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_story/2."))
        atoms = sorted(set(asp.atoms(model, "good_story")))
        print(f"{len(atoms)} compatible stories:")
        for a in atoms:
            print(" ", a)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in PROBLEMS:
            params = StoryParams(
                place="hamlet",
                problem=p,
                hero_name="Pip",
                hero_type="fox",
                bully_name="Hob",
                bully_type="boy",
                elder_name="Gran",
                elder_type="grandmother",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
