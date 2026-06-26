#!/usr/bin/env python3
"""
munchkin_wrap_transformation_sharing_detective_story.py
=======================================================

A small detective-story world about a munchkin, a wrap, a surprising
transformation, and a sharing-based solution.

The premise:
- A tiny munchkin detective notices that a wrap is missing or changed.
- Clues reveal that the wrap has been transformed into something else.
- A careful share of a needed item helps solve the case.

The world is intentionally compact: one place, a few typed entities, physical
meters, and emotional memes drive the story state. The story is not a frozen
template; each scene is produced from the simulated world.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    transformed_from: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father", "munchkin"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    label: str
    indoor: bool = True


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    wrap: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "kitchen": Place(label="the kitchen", indoor=True),
    "library": Place(label="the little library", indoor=True),
    "market": Place(label="the market", indoor=True),
}

HEROES = {
    "munchkin": {"kind": "character", "type": "munchkin", "label": "Munchkin"},
}

HELPERS = {
    "chef": {"kind": "character", "type": "chef", "label": "Chef"},
    "librarian": {"kind": "character", "type": "librarian", "label": "Librarian"},
    "friend": {"kind": "character", "type": "friend", "label": "Friend"},
}

WRAPS = {
    "taco_wrap": {"label": "wrap", "phrase": "a warm wrap", "kind": "food"},
    "paper_wrap": {"label": "wrap", "phrase": "a paper wrap", "kind": "paper"},
    "gift_wrap": {"label": "wrap", "phrase": "a shiny wrap", "kind": "paper"},
}

TRANSFORMATIONS = {
    "steam": {
        "from": "wrap",
        "to": "a little cloud",
        "clue": "warm steam",
        "effect": "softened and puffed up",
    },
    "fold": {
        "from": "wrap",
        "to": "a neat square",
        "clue": "careful folds",
        "effect": "changed shape",
    },
    "cut": {
        "from": "wrap",
        "to": "small pieces",
        "clue": "tiny cut marks",
        "effect": "became little pieces",
    },
}

SHARING_ACTIONS = {
    "share_spoon": {
        "item": "spoon",
        "label": "a spoon",
        "help": "to share the spoon",
        "result": "the helper could eat too",
    },
    "share_note": {
        "item": "note",
        "label": "a clue note",
        "help": "to share the clue note",
        "result": "everyone could read the clue",
    },
    "share_lamp": {
        "item": "lamp",
        "label": "a lamp",
        "help": "to share the lamp light",
        "result": "both could see the evidence",
    },
}

GIRL_NAMES = ["Mina", "Lily", "June", "Ava", "Nora"]
BOY_NAMES = ["Finn", "Theo", "Ben", "Max", "Leo"]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    wrap = world.entities.get("wrap")
    if not wrap:
        return out
    if wrap.meters.get("mystery", 0.0) < THRESHOLD:
        return out
    if ("transform", wrap.id) in world.fired:
        return out
    world.fired.add(("transform", wrap.id))
    tr = world.facts["transformation"]
    wrap.transformed_from = "wrap"
    wrap.label = tr["to"]
    wrap.phrase = tr["to"]
    out.append(f"The wrap had changed into {tr['to']}.")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if not hero or not helper:
        return out
    if hero.memes.get("stuck", 0.0) < THRESHOLD:
        return out
    if hero.memes.get("share_ready", 0.0) < THRESHOLD:
        return out
    if ("share", hero.id) in world.fired:
        return out
    world.fired.add(("share", hero.id))
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    helper.memes["trust"] = helper.memes.get("trust", 0.0) + 1
    out.append("They solved the clue by sharing what they had.")
    return out


RULES = [
    Rule("transform", _r_transform),
    Rule("share", _r_share),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(got)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_story(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    wrap = world.get("wrap")

    world.say(
        f"{hero.id} was a tiny detective munchkin who noticed every crumb and clue."
    )
    world.say(
        f"{hero.pronoun().capitalize()} liked {wrap.phrase} because it was neat and easy to carry."
    )
    world.say(
        f"One day, {hero.id} went to {world.place.label} with {helper.label}."
    )

    world.para()
    world.say(
        f"There, {hero.id} found a strange sign: the wrap was gone from the tray."
    )
    world.say(
        f"Instead of the wrap, there was {world.facts['transformation']['clue']} and a small trail of crumbs."
    )
    hero.memes["curious"] = 1.0
    hero.meters["clue"] = 1.0
    wrap.meters["mystery"] = 1.0
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{hero.id} frowned and looked closer, because a true detective does not rush."
    )
    world.say(
        f"{hero.pronoun().capitalize()} asked {helper.pronoun('object')} to share {world.facts['sharing']['label']}."
    )
    hero.memes["stuck"] = 1.0
    hero.memes["share_ready"] = 1.0
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"With the light and clue shared, the mystery made sense."
    )
    world.say(
        f"{helper.label} had used the wrap and {world.facts['sharing']['help']}."
    )
    world.say(
        f"In the end, {hero.id} smiled, because the case was solved and the wrap was no longer a mystery."
    )


def choose_story_parts(params: StoryParams) -> tuple[Place, Entity, Entity, Entity]:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.hero not in HEROES:
        raise StoryError("Unknown hero.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    if params.wrap not in WRAPS:
        raise StoryError("Unknown wrap.")
    place = PLACES[params.place]
    hero_cfg = HEROES[params.hero]
    helper_cfg = HELPERS[params.helper]
    wrap_cfg = WRAPS[params.wrap]
    hero = Entity(id="hero", kind=hero_cfg["kind"], type=hero_cfg["type"], label=hero_cfg["label"])
    helper = Entity(id="helper", kind=helper_cfg["kind"], type=helper_cfg["type"], label=helper_cfg["label"])
    wrap = Entity(id="wrap", kind=wrap_cfg["kind"], type="wrap", label="wrap", phrase=wrap_cfg["phrase"])
    return place, hero, helper, wrap


def tell(params: StoryParams) -> World:
    place, hero, helper, wrap = choose_story_parts(params)
    world = World(place)
    world.add(hero)
    world.add(helper)
    world.add(wrap)
    world.facts["transformation"] = random.choice(list(TRANSFORMATIONS.values()))
    world.facts["sharing"] = random.choice(list(SHARING_ACTIONS.values()))
    build_story(world)
    world.facts.update(hero=hero, helper=helper, wrap=wrap, place=place, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short detective story about a munchkin and a wrap in {world.place.label}.",
        "Tell a child-friendly mystery where a wrap changes shape and the clue is solved by sharing.",
        "Write a tiny detective tale with a surprise transformation and a helpful act of sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    wrap = world.facts["wrap"]
    tr = world.facts["transformation"]
    sh = world.facts["sharing"]
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {hero.id}, a tiny munchkin who liked clues.",
        ),
        QAItem(
            question=f"What happened to the wrap?",
            answer=f"The wrap was transformed and changed into {tr['to']}.",
        ),
        QAItem(
            question=f"How did they solve the mystery?",
            answer=f"They solved it by sharing {sh['label']} so they could see and understand the clue together.",
        ),
        QAItem(
            question=f"Where did the story happen?",
            answer=f"It happened in {world.place.label}.",
        ),
        QAItem(
            question=f"Who helped the munchkin?",
            answer=f"{helper.label} helped {hero.id} look at the clue and share what they had.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is someone who looks for clues to solve a mystery.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use, see, or enjoy something with you.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is when something changes into a different form or shape.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    lines.append(f"facts={world.facts.get('transformation', {})}")
    lines.append(f"sharing={world.facts.get('sharing', {})}")
    return "\n".join(lines)


ASP_RULES = r"""
mystery_wrap(W) :- wrap(W), clue(C), clue_of(C,W).
transformed(W) :- mystery_wrap(W), transformation(T), becomes(T,_).
solved :- transformed(W), sharing(S), helpful_share(S).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for hid in HEROES:
        lines.append(asp.fact("hero_kind", hid))
    for hid in HELPERS:
        lines.append(asp.fact("helper_kind", hid))
    for wid, wrap in WRAPS.items():
        lines.append(asp.fact("wrap", wid))
        lines.append(asp.fact("clue_of", "crumbs", wid))
    for tid, tr in TRANSFORMATIONS.items():
        lines.append(asp.fact("transformation", tid))
        lines.append(asp.fact("becomes", tid, tr["to"]))
    for sid, sh in SHARING_ACTIONS.items():
        lines.append(asp.fact("sharing", sid))
        lines.append(asp.fact("helpful_share", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show transformed/1. #show solved/0."))
    atoms = set((s.name, len(s.arguments)) for s in model)
    if ("transformed", 1) in atoms and ("solved", 0) in atoms:
        print("OK: ASP model produces transformation and sharing solution.")
        return 0
    print("Mismatch in ASP verification.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-story world about a munchkin, a wrap, transformation, and sharing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--wrap", choices=WRAPS)
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
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or "munchkin"
    helper = args.helper or rng.choice(list(HELPERS))
    wrap = args.wrap or rng.choice(list(WRAPS))
    return StoryParams(place=place, hero=hero, helper=helper, wrap=wrap)


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
    StoryParams(place="kitchen", hero="munchkin", helper="chef", wrap="taco_wrap"),
    StoryParams(place="library", hero="munchkin", helper="librarian", wrap="gift_wrap"),
    StoryParams(place="market", hero="munchkin", helper="friend", wrap="paper_wrap"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show transformed/1. #show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
