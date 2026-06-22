#!/usr/bin/env python3
"""
storyworlds/worlds/customer_nuzzle_pulp_flashback_bravery_happy_ending.py
=========================================================================

A small animal-story world about a timid customer, a sticky pulp spill, a
flashback, and a brave little turn toward a happy ending.

Seed tale, imagined from the prompt:
---
A young rabbit customer came to the berry stand with her mother. She wanted a
cup of sweet fruit pulp, but the stand had a messy spill on the counter. The
rabbit remembered a flashback to a time when she had frozen up and missed her
chance to speak. This time she took a brave breath, asked for help, and the
friendly fox seller cleaned the pulp away. Her mother nuzzled her, proud of the
bravery, and the rabbit left with a warm cup and a happy ending.

This world keeps the prose state-driven: characters have typed meters and memes,
the flashback is an actual remembered state that changes courage, and the final
image proves what changed.
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVERY_MIN = 2.0


@dataclass
class StoryParams:
    species: str
    customer_name: str
    parent_name: str
    seller_name: str
    treat: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mother", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"father", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class AnimalKind:
    id: str
    species: str
    small_move: str
    face: str
    voice: str
    home_word: str
    tail_word: str


@dataclass
class Treat:
    id: str
    label: str
    pulp_label: str
    spill_label: str
    smell: str
    color: str
    sweetness: str


@dataclass
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.flashback: dict = {"remembered": False}

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.flashback = copy.deepcopy(self.flashback)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    if world.get("counter").meters["pulp"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("counter").meters["mess"] += 1
    world.get("seller").memes["alert"] += 1
    out.append("__spill__")
    return out


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    cust = world.get("customer")
    if cust.meters["stillness"] < THRESHOLD:
        return out
    if world.flashback["remembered"]:
        return out
    world.flashback["remembered"] = True
    cust.memes["fear"] += 1
    cust.memes["bravery"] += 1
    out.append("__flashback__")
    return out


CAUSAL_RULES = [Rule("spill", "physical", _r_spill), Rule("flashback", "social", _r_flashback)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


ANIMALS = {
    "rabbit": AnimalKind("rabbit", "rabbit", "hops", "soft whiskers", "a small voice", "burrow", "tail"),
    "fox": AnimalKind("fox", "fox", "pads", "bright eyes", "a quick voice", "den", "tail"),
    "bear": AnimalKind("bear", "bear", "trudges", "round ears", "a low voice", "cave", "paw"),
    "mouse": AnimalKind("mouse", "mouse", "scurries", "tiny nose", "a squeaky voice", "nest", "tail"),
}

TREATS = {
    "berry_pulp": Treat("berry_pulp", "berry pulp", "a cup of berry pulp", "the pulp", "sweet berries", "purple", "sweet"),
    "apple_pulp": Treat("apple_pulp", "apple pulp", "a little bowl of apple pulp", "the pulp", "fresh apples", "golden", "soft"),
    "peach_pulp": Treat("peach_pulp", "peach pulp", "a jar of peach pulp", "the pulp", "ripe peaches", "orange", "bright"),
}

GIRLISH = ["Mina", "Luna", "Pia", "Tala", "Nia"]
BOYISH = ["Milo", "Finn", "Bram", "Otis", "Theo"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for animal in ANIMALS:
        for treat in TREATS:
            combos.append((animal, treat))
    return combos


def flashback_line(customer: Entity) -> str:
    customer.memes["memory"] += 1
    customer.meters["stillness"] += 1
    return (
        f"For a moment, {customer.id} had a flashback: last time, {customer.pronoun()} "
        f"had wanted to speak up, but {customer.pronoun()} had frozen in place."
    )


def build_scene(world: World, params: StoryParams) -> World:
    kind = ANIMALS[params.species]
    treat = TREATS[params.treat]

    customer = world.add(Entity(id=params.customer_name, kind="character", type=params.species, role="customer"))
    parent_type = "mother"
    parent = world.add(Entity(id=params.parent_name, kind="character", type=parent_type, role="parent"))
    seller = world.add(Entity(id=params.seller_name, kind="character", type="fox", role="seller", label="the berry seller"))
    counter = world.add(Entity(id="counter", kind="thing", type="counter", label="the counter"))
    cup = world.add(Entity(id="cup", kind="thing", type="cup", label=treat.label))

    customer.memes["nervous"] = 1.0
    customer.memes["bravery"] = 0.0
    parent.memes["warmth"] = 1.0
    seller.memes["kindness"] = 1.0
    counter.meters["pulp"] = 0.0
    counter.meters["mess"] = 0.0

    world.facts.update(
        customer=customer,
        parent=parent,
        seller=seller,
        kind=kind,
        treat=treat,
        cup=cup,
    )

    world.say(
        f"On a bright morning, {customer.id} the {kind.species} customer went to the berry stand with {parent.id}."
    )
    world.say(
        f"{customer.id} loved the sweet smell of {treat.smell}, and {kind.small_move()} around the little stand made the visit feel friendly."
    )
    world.say(
        f"The {treat.pulp_label} waited in a cup, shiny and {treat.color}, but some {treat.spill_label} had splashed onto {counter.label_word}."
    )
    world.say(
        f'"I want that one," {customer.id} said quietly, and {parent.id} gave {customer.pronoun("object")} a gentle nuzzle on the head.'
    )

    world.para()
    world.say(flashback_line(customer))
    world.say(
        f"{customer.id}'s whiskers twitched. {customer.pronoun().capitalize()} looked at {seller.id} and then at the spill."
    )
    customer.memes["fear"] += 1
    customer.memes["courage"] += 1
    customer.meters["stillness"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"Then {customer.id} took a brave breath and said, \"Could you clean the {treat.spill_label} first, please?\""
    )
    customer.memes["bravery"] += 2
    seller.memes["pride"] += 1
    counter.meters["pulp"] = 0.0
    counter.meters["mess"] = 0.0
    world.say(
        f"{seller.id} smiled, wiped the counter, and poured fresh {treat.pulp_label} into a clean cup."
    )
    world.say(
        f"The sweet smell rose again, and this time it felt safe instead of sticky."
    )

    world.para()
    parent.memes["love"] += 1
    customer.memes["joy"] += 1
    customer.memes["fear"] = 0.0
    world.say(
        f"{parent.id} nuzzled {customer.id} again and whispered, \"That was brave.\""
    )
    world.say(
        f"{customer.id} held the warm cup between tiny paws, sipped the {treat.pulp_label}, and grinned."
    )
    world.say(
        f"By the end, the berry stand smelled sweet, the counter was clean, and {customer.id} walked home with a happy ending."
    )

    world.facts["outcome"] = "happy"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    customer = f["customer"]
    treat = f["treat"]
    return [
        f"Write an animal story for a young child about {customer.id} the customer, a sticky {treat.pulp_label}, and a brave choice.",
        f"Tell a gentle story where a little animal customer has a flashback, finds bravery, and ends with a happy ending.",
        f"Write a short story that includes the words customer, nuzzle, and pulp, and ends with a warm, kind ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    customer = f["customer"]
    parent = f["parent"]
    seller = f["seller"]
    treat = f["treat"]
    qa = [
        QAItem(
            question=f"Why did {customer.id} hesitate at the berry stand?",
            answer=(
                f"{customer.id} saw the sticky {treat.spill_label} on the counter and remembered a flashback about freezing up before. "
                f"That memory made {customer.pronoun()} nervous, but it also helped {customer.pronoun()} find courage to speak."
            ),
        ),
        QAItem(
            question=f"What did {parent.id} do to help {customer.id} feel safe?",
            answer=(
                f"{parent.id} gave {customer.id} a gentle nuzzle and stayed close while {customer.id} spoke up. "
                f"That kind touch helped turn the moment into bravery instead of worry."
            ),
        ),
        QAItem(
            question=f"What did {customer.id} ask {seller.id} to do?",
            answer=(
                f"{customer.id} asked {seller.id} to clean the {treat.spill_label} first. "
                f"That was a brave choice because it meant asking for help before enjoying the treat."
            ),
        ),
        QAItem(
            question=f"How did the story end for {customer.id}?",
            answer=(
                f"It ended happily. {seller.id} cleaned the counter, {customer.id} got fresh {treat.pulp_label}, and {parent.id} was proud of the bravery."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    treat = f["treat"]
    customer = f["customer"]
    return [
        QAItem(
            question="What is pulp?",
            answer=(
                f"Pulp is the soft, squishy part of fruit that can be spooned or poured into a cup. "
                f"In this story, {treat.label} was served as {treat.pulp_label}."
            ),
        ),
        QAItem(
            question="What does it mean to nuzzle someone?",
            answer=(
                "To nuzzle means to rub your face gently against someone you love. "
                f"{customer.id}'s parent nuzzled {customer.id} to show care and pride."
            ),
        ),
        QAItem(
            question="What is bravery?",
            answer=(
                "Bravery means doing the right thing even when you feel scared. "
                f"{customer.id} showed bravery by asking for help and speaking up."
            ),
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    lines.append(f"  flashback remembered: {world.flashback['remembered']}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        species="rabbit",
        customer_name="Mina",
        parent_name="Luna",
        seller_name="Fenn",
        treat="berry_pulp",
    ),
    StoryParams(
        species="mouse",
        customer_name="Pia",
        parent_name="Tala",
        seller_name="Milo",
        treat="apple_pulp",
    ),
    StoryParams(
        species="bear",
        customer_name="Otis",
        parent_name="Nia",
        seller_name="Bram",
        treat="peach_pulp",
    ),
]


def valid_combo(params: StoryParams) -> bool:
    return params.species in ANIMALS and params.treat in TREATS


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    species = args.species or rng.choice(sorted(ANIMALS))
    treat = args.treat or rng.choice(sorted(TREATS))
    if species not in ANIMALS:
        raise StoryError("Unknown animal kind.")
    if treat not in TREATS:
        raise StoryError("Unknown treat kind.")
    if not valid_combo(StoryParams(species=species, customer_name="A", parent_name="B", seller_name="C", treat=treat)):
        raise StoryError("That combination does not make a reasonable animal story.")
    customer_name = args.customer or rng.choice(["Mina", "Pia", "Lina", "Otis", "Milo"])
    parent_name = args.parent or rng.choice(["Luna", "Tala", "Nia", "Bram"])
    seller_name = args.seller or rng.choice(["Fenn", "Milo", "Sage", "Quill"])
    return StoryParams(
        species=species,
        customer_name=customer_name,
        parent_name=parent_name,
        seller_name=seller_name,
        treat=treat,
    )


def generate(params: StoryParams) -> StorySample:
    if params.species not in ANIMALS:
        raise StoryError("Unknown animal kind.")
    if params.treat not in TREATS:
        raise StoryError("Unknown treat kind.")
    if not valid_combo(params):
        raise StoryError("Invalid story combination.")
    world = World()
    build_scene(world, params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world about a customer, a nuzzle, a pulp spill, and bravery."
    )
    ap.add_argument("--species", choices=sorted(ANIMALS))
    ap.add_argument("--treat", choices=sorted(TREATS))
    ap.add_argument("--customer")
    ap.add_argument("--parent")
    ap.add_argument("--seller")
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


ASP_RULES = r"""
animal_story(S, T) :- species(S), treat(T).
happy_ending(S, T) :- animal_story(S, T), brave_choice(S), cleaned(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in ANIMALS:
        lines.append(asp.fact("species", s))
    for t in TREATS:
        lines.append(asp.fact("treat", t))
    lines.append(asp.fact("brave_choice", "rabbit"))
    lines.append(asp.fact("brave_choice", "mouse"))
    lines.append(asp.fact("brave_choice", "bear"))
    lines.append(asp.fact("cleaned", "berry_pulp"))
    lines.append(asp.fact("cleaned", "apple_pulp"))
    lines.append(asp.fact("cleaned", "peach_pulp"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show animal_story/2."))
    return sorted(set(asp.atoms(model, "animal_story")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set((s, t) for s, t in valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show animal_story/2.\n#show happy_ending/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (species, treat) combos:")
        for s, t in asp_valid_combos():
            print(f"  {s:8} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.customer_name}: {p.species} customer and {p.treat}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
