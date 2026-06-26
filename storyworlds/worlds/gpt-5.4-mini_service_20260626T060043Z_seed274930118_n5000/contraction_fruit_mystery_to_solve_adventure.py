#!/usr/bin/env python3
"""
storyworlds/worlds/contraction_fruit_mystery_to_solve_adventure.py
===================================================================

A small adventure-style mystery world about a vanished fruit and a clue that
keeps getting smaller by contraction. A child investigator, a helpful adult,
and a few plausible props drive the story through premise, tension, clueing,
and resolution.

The world model tracks two dimensions for entities:
- meters: physical state, like size, ripeness, hiddenness, and carriedness
- memes: emotional state, like curiosity, worry, relief, and pride
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
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Fruit:
    id: str
    label: str
    phrase: str
    color: str
    peel: str
    size: str
    region: str
    can_contract: bool = False
    plural: bool = False


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    reveals: str
    kind: str


@dataclass
class StoryParams:
    place: str
    fruit: str
    clue: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

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
        c.facts = dict(self.facts)
        return c


GIRL_NAMES = ["Mia", "Nora", "Lena", "Ava", "Ruby", "Zoe", "Ivy", "Ella"]
BOY_NAMES = ["Noah", "Leo", "Finn", "Owen", "Eli", "Theo", "Max", "Kai"]
HELPERS = ["mother", "father", "aunt", "uncle"]
TRAITS = ["brave", "curious", "quick", "careful", "spry"]


SETTINGS = {
    "orchard": Setting(place="the orchard", kind="outdoor", affords={"search", "climb", "gather"}),
    "kitchen": Setting(place="the kitchen", kind="indoor", affords={"search", "mix", "gather"}),
    "market": Setting(place="the market", kind="outdoor", affords={"search", "gather"}),
}

FRUITS = {
    "apple": Fruit("apple", "apple", "a shiny red apple", "red", "smooth peel", "round size", "table", True),
    "pear": Fruit("pear", "pear", "a green pear", "green", "soft peel", "small size", "basket", True),
    "plum": Fruit("plum", "plum", "a purple plum", "purple", "thin peel", "small size", "pocket", True),
    "banana": Fruit("banana", "banana", "a bright banana", "yellow", "soft peel", "long size", "counter", True),
}

CLUES = {
    "napkin": Clue("napkin", "napkin", "a folded napkin with a juice mark", "the fruit was moved by someone who was careful", "cloth"),
    "seed": Clue("seed", "seed", "a little seed under the table", "the missing fruit had been cut open earlier", "tiny"),
    "note": Clue("note", "note", "a note with a squeezed spot", "someone had pressed the fruit hard enough to make it shrink", "paper"),
    "basket": Clue("basket", "basket", "a basket with one empty space", "the fruit had been taken from the basket and hidden nearby", "container"),
}


def body_pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "girl":
        return "she", "her", "her"
    return "he", "him", "his"


def fruit_at_risk(fruit: Fruit) -> bool:
    return fruit.can_contract and fruit.region in {"table", "basket", "counter", "pocket"}


def choose_clue(fruit: Fruit, clue: Clue) -> bool:
    return fruit.can_contract and clue.kind in {"cloth", "paper", "tiny", "container"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for fruit_id, fruit in FRUITS.items():
            for clue_id, clue in CLUES.items():
                if fruit_at_risk(fruit) and choose_clue(fruit, clue):
                    combos.append((place, fruit_id, clue_id))
    return combos


@dataclass
class Rule:
    name: str
    apply: callable


def _r_contract(world: World) -> list[str]:
    out: list[str] = []
    fruit = world.facts["fruit_entity"]
    if fruit.meters.get("pressed", 0) < THRESHOLD:
        return out
    sig = ("contract", fruit.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fruit.meters["size"] = max(0.0, fruit.meters.get("size", 1.0) - 1.0)
    fruit.meters["changed"] = 1.0
    out.append(f"The fruit looked smaller, as if it had squeezed itself into a secret.")
    return out


def _r_hide(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts["clue_entity"]
    if clue.meters.get("noticed", 0) < THRESHOLD:
        return out
    sig = ("reveal", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["clue_revealed"] = True
    out.append(f"The clue finally stood out clearly.")
    return out


RULES = [
    Rule("contract", _r_contract),
    Rule("hide", _r_hide),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, fruit_cfg: Fruit, clue_cfg: Clue, name: str, gender: str, helper: str, trait: str) -> World:
    world = World(setting)
    subject, obj, pos = body_pronouns(gender)

    hero = world.add(Entity(id=name, kind="character", type=gender, label=name))
    adult = world.add(Entity(id="Helper", kind="character", type=helper, label=f"the {helper}"))
    fruit = world.add(Entity(
        id="Fruit", type="fruit", label=fruit_cfg.label, phrase=fruit_cfg.phrase,
        owner=hero.id, carried_by=None, meters={"size": 1.0, "hidden": 0.0}, memes={}
    ))
    clue = world.add(Entity(
        id="Clue", type=clue_cfg.kind, label=clue_cfg.label, phrase=clue_cfg.phrase,
        owner=None, carried_by=None, meters={"noticed": 0.0}, memes={}
    ))

    world.facts.update(hero=hero, adult=adult, fruit_entity=fruit, clue_entity=clue,
                       fruit_cfg=fruit_cfg, clue_cfg=clue_cfg, trait=trait, subject=subject)

    world.say(f"{name} was a {trait} little {gender} who loved adventure and solving little mysteries.")
    world.say(f"One day, {name} and {world.setting.place} keeper {adult.label_word if hasattr(adult, 'label_word') else adult.label} were near {world.setting.place} when {name} noticed {fruit_cfg.phrase}.")
    world.say(f"{subject.capitalize()} liked the fruit because it looked bright and important, almost like a treasure.")
    world.para()
    world.say(f"Then the fruit went missing, and {name} promised to solve the mystery before snack time ended.")
    world.say(f"{name} searched the room carefully while {pos} {helper} watched with a worried face.")

    world.para()
    if fruit_cfg.can_contract:
        fruit.meters["pressed"] = 1.0
        world.say(f"{name} found a strange mark: someone had pressed the fruit so hard that it seemed to contract and shrink.")
    clue.meters["noticed"] = 1.0
    world.say(f"Nearby, {name} spotted {clue_cfg.phrase}, which felt like a tiny clue from the fruit itself.")
    propagate(world, narrate=True)
    world.say(f"{name} knelt down and followed the clue until the hiding place came into view.")
    world.para()

    hero.memes["curiosity"] = 1.0
    hero.memes["confidence"] = 1.0
    world.say(f"At last, {name} found the fruit tucked safely where nobody would step on it.")
    fruit.meters["hidden"] = 0.0
    fruit.meters["found"] = 1.0
    hero.memes["relief"] = 1.0
    adult.memes["relief"] = 1.0
    world.say(f"{subject.capitalize()} smiled, and {pos} {helper} laughed because the mystery had been solved.")
    world.say(f"The little adventure ended with the fruit back where everyone could see it, bright and safe again.")

    world.facts["solved"] = True
    world.facts["resolved_story"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    fruit = f["fruit_cfg"]
    clue = f["clue_cfg"]
    return [
        f'Write a short adventure mystery for a young child that includes the word "contraction" and a lost {fruit.label}.',
        f"Tell a child-friendly detective story where {hero.id} notices a {fruit.label} and follows a clue like {clue.label} to solve the mystery.",
        f'Write a playful adventure story about a fruit that seems to contract and a child who solves the puzzle.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    adult = f["adult"]
    fruit = f["fruit_cfg"]
    clue = f["clue_cfg"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"Who solved the mystery in the story?",
            answer=f"{hero.id} solved the mystery by searching carefully and following the clue until the fruit was found.",
        ),
        QAItem(
            question=f"What fruit was part of the mystery?",
            answer=f"The mystery was about {fruit.phrase}, which mattered because it seemed to contract and then go missing.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} find the answer?",
            answer=f"{clue.phrase} helped because it pointed toward what had happened to the fruit.",
        ),
        QAItem(
            question=f"How did {hero.id} act during the adventure?",
            answer=f"{hero.id} acted like a {trait} little detective and kept looking until the mystery was solved.",
        ),
        QAItem(
            question=f"Who was with {hero.id} while searching?",
            answer=f"{adult.label} was with {hero.id} and watched with worry until the fruit was found.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fruit?",
            answer="A fruit is a part of a plant that grows around seeds and is often sweet, juicy, and good to eat.",
        ),
        QAItem(
            question="What does it mean when something contracts?",
            answer="When something contracts, it gets smaller, tighter, or pulls in toward itself.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a question or problem that needs clues and careful thinking to solve.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks questions, and thinks hard to solve a mystery.",
        ),
    ]


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
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="orchard", fruit="apple", clue="napkin", name="Mia", gender="girl", helper="mother", seed=None),
    StoryParams(place="kitchen", fruit="pear", clue="note", name="Leo", gender="boy", helper="father", seed=None),
    StoryParams(place="market", fruit="plum", clue="basket", name="Nora", gender="girl", helper="aunt", seed=None),
]


def explain_rejection(fruit: Fruit, clue: Clue) -> str:
    return f"(No story: {fruit.label} cannot make a convincing contraction mystery with {clue.label}.)"


def valid_story(fruit: Fruit, clue: Clue) -> bool:
    return fruit_at_risk(fruit) and choose_clue(fruit, clue)


@dataclass
class StoryParamsAlias:
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure mystery world about a fruit contraction clue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--fruit", choices=FRUITS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
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
    combos = valid_combos()
    if args.place or args.fruit or args.clue:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.fruit is None or c[1] == args.fruit)
            and (args.clue is None or c[2] == args.clue)
        ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, fruit_id, clue_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, fruit=fruit_id, clue=clue_id, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], FRUITS[params.fruit], CLUES[params.clue], params.name, params.gender, params.helper, "curious")
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


ASP_RULES = r"""
fruit_at_risk(F) :- fruit(F), can_contract(F).
clue_helpful(C) :- clue(C).
valid_story(P, F, C) :- setting(P), fruit_at_risk(F), clue_helpful(C), fits(P, F, C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for fid, fruit in FRUITS.items():
        lines.append(asp.fact("fruit", fid))
        lines.append(asp.fact("can_contract", fid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for pid in SETTINGS:
        for fid in FRUITS:
            for cid in CLUES:
                if valid_story(FRUITS[fid], CLUES[cid]):
                    lines.append(asp.fact("fits", pid, fid, cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set((p, f, c) for p, f, c in valid_combos())
    cl = set(asp.atoms(asp.one_model(asp_program("#show fits/3. #show valid_story/3.")), "fits"))
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for fid, fruit in FRUITS.items():
            for cid, clue in CLUES.items():
                if valid_story(fruit, clue):
                    combos.append((place, fid, cid))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show fits/3."))
    return sorted(set(asp.atoms(model, "fits")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.fruit} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
