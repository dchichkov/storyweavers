#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/psychology_fern_thistle_twist_reconciliation_tall_tale.py
========================================================================================

A small tall-tale storyworld about a child who studies feelings, a fern, a thistle,
and a surprising twist that ends in reconciliation.

The world is built from a tiny simulated model:
- one child and one helper
- two plants with different temperaments
- a misunderstanding caused by a mistaken reading of intent
- a twist in the evidence
- a reconciliation after the truth is discovered

The seed words are woven into the prose and QA:
psychology, fern, thistle
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
FIBER_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class StoryParams:
    child_name: str = "Mira"
    child_type: str = "girl"
    helper_name: str = "Uncle Jo"
    helper_type: str = "man"
    plant_a: str = "fern"
    plant_b: str = "thistle"
    misunderstanding: str = "thistle"
    twist: str = "wind"
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


@dataclass
class Plant:
    id: str
    label: str
    temperament: str
    touchiness: int
    fibrous: bool = False
    prickly: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        return other


def _r_misread(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["suspicion"] < THRESHOLD:
        return out
    sig = ("misread",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["hurt"] += 1
    child.memes["worry"] += 1
    out.append("__misread__")
    return out


def _r_twist(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes["curiosity"] < THRESHOLD:
        return out
    if world.get("helper").memes["hurt"] < THRESHOLD:
        return out
    sig = ("twist",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["surprise"] += 1
    out.append("__twist__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes["surprise"] < THRESHOLD:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["peace"] += 1
    world.get("helper").memes["peace"] += 1
    out.append("__reconcile__")
    return out


CAUSAL_RULES = [
    _r_misread,
    _r_twist,
    _r_reconcile,
]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)


PLANTS = {
    "fern": Plant(
        id="fern",
        label="fern",
        temperament="soft",
        touchiness=1,
        fibrous=True,
        tags={"fern", "green"},
    ),
    "thistle": Plant(
        id="thistle",
        label="thistle",
        temperament="spiky",
        touchiness=2,
        prickly=True,
        tags={"thistle", "spiky"},
    ),
}

TALL_TALE_STYLE = {
    "opening": "big as a wagon wheel and bright as a brass bell",
    "forest": "a patch of green gossip under a sky that never learned to whisper",
    "twist": "the wind turned the leaves inside out like a flap of laundry",
    "ending": "as plain as a porch rail after rain",
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for child in ["girl", "boy"]:
        for plant_a in PLANTS:
            for plant_b in PLANTS:
                if plant_a != plant_b:
                    combos.append((child, plant_a, plant_b))
    return combos


def explain_rejection(params: StoryParams) -> str:
    return "(No story: this world needs two different plants, one soft and one prickly, so the twist can actually change the meaning of what was seen.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld about psychology, fern, thistle, twist, and reconciliation."
    )
    ap.add_argument("--child", choices=["girl", "boy"])
    ap.add_argument("--plant-a", choices=PLANTS)
    ap.add_argument("--plant-b", choices=PLANTS)
    ap.add_argument("--misunderstanding", choices=PLANTS)
    ap.add_argument("--twist", choices=["wind", "shadow", "rain", "bee"])
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
    if args.plant_a and args.plant_b and args.plant_a == args.plant_b:
        raise StoryError("(No story: the two plants must be different so the twist matters.)")
    combos = [c for c in valid_combos()
              if (args.child is None or c[0] == args.child)
              and (args.plant_a is None or c[1] == args.plant_a)
              and (args.plant_b is None or c[2] == args.plant_b)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    child, a, b = rng.choice(sorted(combos))
    misunderstanding = args.misunderstanding or rng.choice([a, b])
    twist = args.twist or rng.choice(["wind", "shadow", "rain", "bee"])
    return StoryParams(
        child_name="Mira" if child == "girl" else "Ezra",
        child_type=child,
        helper_name="Aunt June" if child == "girl" else "Uncle Jo",
        helper_type="woman" if child == "girl" else "man",
        plant_a=a,
        plant_b=b,
        misunderstanding=misunderstanding,
        twist=twist,
    )


def tell(params: StoryParams) -> World:
    if params.plant_a not in PLANTS or params.plant_b not in PLANTS:
        raise StoryError("(Invalid plant choice.)")
    if params.plant_a == params.plant_b:
        raise StoryError("(The story needs two different plants.)")

    world = World()
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    plant_a = world.add(Entity(id="fern", type="plant", label="fern", tags={"fern"}))
    plant_b = world.add(Entity(id="thistle", type="plant", label="thistle", tags={"thistle"}))

    child.memes["curiosity"] += 1
    child.memes["suspicion"] += 1
    child.memes["wonder"] += 1

    world.say(
        f"Out on a day {TALL_TALE_STYLE['opening']}, {child.label} went wandering in {TALL_TALE_STYLE['forest']}."
    )
    world.say(
        f"{child.label} studied the little psychology of the garden, because even leaves have moods."
    )
    world.say(
        f"There stood a fern, soft as a green ribbon, and beside it a thistle, sharp as a pin cushion."
    )

    world.para()
    if params.misunderstanding == "thistle":
        child.memes["suspicion"] += 1
        helper.memes["hurt"] += 0.5
        world.say(
            f"{child.label} thought the thistle was being rude just because it wore its needles out loud."
        )
        world.say(
            f"{helper.label} said that a prickly face does not always mean a prickly heart."
        )
    else:
        child.memes["suspicion"] += 1
        world.say(
            f"{child.label} nearly blamed the {params.misunderstanding} for a rough-looking patch, and the story went crooked as a fence in a storm."
        )

    world.para()
    child.memes["curiosity"] += 1
    if params.twist == "wind":
        world.say(f"Then came a twist: the wind turned the fern leaves and bent the thistle heads low.")
    elif params.twist == "shadow":
        world.say(f"Then came a twist: a moving shadow made the thistle look like a tiny thorned bear.")
    elif params.twist == "rain":
        world.say(f"Then came a twist: rain tapped the fern shiny and softened the thistle's sharp little crown.")
    else:
        world.say(f"Then came a twist: a bee hummed over the fern and ignored the thistle as polite as a minister.")

    propagate(world, narrate=False)

    world.para()
    world.say(
        f"{child.label} blinked hard and saw the truth: the fern had been shy, and the thistle had only been protecting itself."
    )
    world.say(
        f"{helper.label} laughed a kindly laugh and explained that psychology means thinking about feelings, fears, and the reasons things act the way they do."
    )
    child.memes["peace"] += 1
    helper.memes["peace"] += 1
    world.say(
        f"So {child.label} apologized to the thistle, patted the fern, and the two plants stood together in the dirt like old friends at a dance."
    )
    world.say(
        f"By sunset the garden was all fixed up with understanding, and the whole tale ended as plain as a porch rail after rain."
    )

    world.facts.update(
        child=child,
        helper=helper,
        plant_a=plant_a,
        plant_b=plant_b,
        params=params,
        twist=params.twist,
        misunderstanding=params.misunderstanding,
        reconciled=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        f'Write a tall tale for a young child that includes the words "psychology", "fern", and "thistle".',
        f"Tell a whimsical story where {p.child_name} misreads a thistle, then discovers a surprising twist and makes peace.",
        f"Write a short, child-facing tale about feelings, a fern, and a thistle, ending in reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    return [
        QAItem(
            question="What was the child trying to understand?",
            answer=f"The child was trying to understand why the fern and the thistle seemed so different. The helper explained that psychology is about noticing feelings and reasons, not just appearances."
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that the wind changed how the plants looked, so the child finally saw them more clearly. That surprise helped the child stop judging the thistle too quickly."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended in reconciliation: the child apologized, the helper forgave the mix-up, and the fern and thistle were left in peace. The garden felt calm again by sunset."
        ),
        QAItem(
            question="Why did the child make a mistake?",
            answer=f"The child made a mistake because the thistle looked sharp and unfriendly at first. Once the child thought more carefully, the story showed that a rough look does not always mean a bad heart."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is psychology?",
            answer="Psychology is the study of thoughts, feelings, and why people act the way they do."
        ),
        QAItem(
            question="What is a fern?",
            answer="A fern is a green plant with soft, feathery leaves."
        ),
        QAItem(
            question="What is a thistle?",
            answer="A thistle is a plant with prickly parts that can protect it from being eaten."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
twist(wind) :- twist_kind(wind).
twist(shadow) :- twist_kind(shadow).
reconciliation :- surprise, peace_possible.
valid(child, fern, thistle) :- distinct_plants, twist_kind(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("distinct_plants"))
    for k in ["wind", "shadow", "rain", "bee"]:
        lines.append(asp.fact("twist_kind", k))
    for p in PLANTS:
        lines.append(asp.fact("plant", p))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combos disagree.")
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story:
            raise RuntimeError("empty story")
    except Exception as err:
        print(f"MISMATCH: smoke test failed: {err}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return 0


CURATED = [
    StoryParams(child_name="Mira", child_type="girl", helper_name="Aunt June", helper_type="woman",
                plant_a="fern", plant_b="thistle", misunderstanding="thistle", twist="wind"),
    StoryParams(child_name="Ezra", child_type="boy", helper_name="Uncle Jo", helper_type="man",
                plant_a="thistle", plant_b="fern", misunderstanding="fern", twist="shadow"),
]


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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
