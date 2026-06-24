#!/usr/bin/env python3
"""
A small comedy-leaning storyworld about an open thing, a rote routine, a
kindness-led mystery to solve, and the cheerful reveal at the end.

Seed image:
- Someone cannot open a familiar object by rote force.
- A small mystery appears: what is inside, why is it stuck, or who misplaced it?
- Kindness turns the problem into a cooperative routine.
- The ending proves the mystery was solved and the open thing is finally open.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    openable: bool = False
    open_state: bool = False
    stuck: bool = False
    hidden: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def item_pronoun(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectSpec:
    id: str
    label: str
    phrase: str
    hidden: str
    opening_method: str
    why_stuck: str
    region: str = "hands"


@dataclass
class FixSpec:
    id: str
    label: str
    phrase: str
    method: str
    kindness_line: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []
        self.fired: set[str] = set()

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

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.trace_notes = list(self.trace_notes)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"open"}),
    "playroom": Setting(place="the playroom", indoor=True, affords={"open"}),
    "garden": Setting(place="the garden", indoor=False, affords={"open"}),
}

OBJECTS = {
    "jar": ObjectSpec(
        id="jar",
        label="jar",
        phrase="a shiny jam jar",
        hidden="a glittery button",
        opening_method="twist the lid",
        why_stuck="the lid was jammed by sticky jam",
    ),
    "box": ObjectSpec(
        id="box",
        label="box",
        phrase="a small mystery box",
        hidden="a paper star",
        opening_method="lift the latch",
        why_stuck="the latch was pressed down by a spoon",
    ),
    "tin": ObjectSpec(
        id="tin",
        label="tin",
        phrase="a round cookie tin",
        hidden="a tiny note",
        opening_method="slide the tab",
        why_stuck="the tab was bent by a bump",
    ),
}

FIXES = {
    "warmcloth": FixSpec(
        id="warmcloth",
        label="a warm cloth",
        phrase="a warm cloth",
        method="wipe the lid gently",
        kindness_line="That was kind, because gentle hands can help instead of rush.",
    ),
    "teaspoon": FixSpec(
        id="teaspoon",
        label="a teaspoon",
        phrase="a teaspoon",
        method="wiggle the edge carefully",
        kindness_line="That was kind, because careful tools are better than loud yanks.",
    ),
    "please": FixSpec(
        id="please",
        label="a polite please",
        phrase="a polite please",
        method="ask for help nicely",
        kindness_line="That was kind, because a nice request can bring a helper closer.",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Leo", "Max", "Finn", "Theo", "Sam"]
TRAITS = ["curious", "cheerful", "silly", "patient", "kind", "bold"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    object: str
    fix: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def openable_object(obj: ObjectSpec) -> bool:
    return True


def select_fix(obj: ObjectSpec) -> FixSpec:
    if obj.id == "jar":
        return FIXES["warmcloth"]
    if obj.id == "box":
        return FIXES["please"]
    return FIXES["teaspoon"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for obj_id, obj in OBJECTS.items():
            if not openable_object(obj):
                continue
            fix = select_fix(obj)
            combos.append((place, obj_id, fix.id))
    return combos


def explain_rejection(obj: ObjectSpec) -> str:
    return f"(No story: the {obj.label} cannot be opened in a plausible, child-friendly way.)"


# ---------------------------------------------------------------------------
# Story world actions
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.memes['trait']} {hero.type} who loved neat routines and surprising things.")


def setup_mystery(world: World, hero: Entity, parent: Entity, obj: Entity, spec: ObjectSpec) -> None:
    world.say(
        f"One day in {world.setting.place}, {hero.id} found {spec.phrase} on the table."
    )
    world.say(
        f"{hero.id} wanted to open {obj.item_pronoun()} right away, but the lid would not budge."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label_word} peeked over and said, "
        f'"Hmm. That looks like a mystery to solve."'
    )


def rote_try(world: World, hero: Entity, obj: Entity, spec: ObjectSpec) -> None:
    hero.memes["frustration"] = hero.memes.get("frustration", 0) + 1
    world.say(
        f"{hero.id} tried the usual rote way: {spec.opening_method} again and again."
    )
    world.say(
        f"But the {obj.label} still stayed shut, and {hero.id} made a funny little groan."
    )


def kindness_fix(world: World, hero: Entity, parent: Entity, obj: Entity, spec: ObjectSpec, fix: FixSpec) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    world.say(
        f"Then {hero.id} tried a kinder plan: {fix.phrase} and ask for help."
    )
    world.say(
        f"{parent.label_word} smiled, helped {fix.method}, and said, "
        f'"{fix.kindness_line}"'
    )
    obj.meters["loosened"] = obj.meters.get("loosened", 0) + 1


def solve_mystery(world: World, hero: Entity, parent: Entity, obj: Entity, spec: ObjectSpec) -> None:
    obj.open_state = True
    obj.stuck = False
    world.say(
        f"With one more careful tug, the {obj.label} popped open."
    )
    world.say(
        f"Inside was {spec.hidden}, which was the whole mystery all along."
    )
    world.say(
        f"{hero.id} laughed, and {parent.label_word} laughed too, because the big secret was just a tiny surprise."
    )
    world.say(
        f"At the end, the {obj.label} was open, the hidden thing was found, and {hero.id} felt proud of the kind way {hero.pronoun()} solved it."
    )


def tell(setting: Setting, obj_spec: ObjectSpec, fix_spec: FixSpec,
         hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        memes={"trait": trait},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
    ))
    obj = world.add(Entity(
        id=obj_spec.id,
        type="thing",
        label=obj_spec.label,
        phrase=obj_spec.phrase,
        openable=True,
        open_state=False,
        stuck=True,
        hidden=obj_spec.hidden,
    ))

    introduce(world, hero)
    world.para()
    setup_mystery(world, hero, parent, obj, obj_spec)
    rote_try(world, hero, obj, obj_spec)
    world.para()
    kindness_fix(world, hero, parent, obj, obj_spec, fix_spec)
    solve_mystery(world, hero, parent, obj, obj_spec)

    world.facts.update(hero=hero, parent=parent, obj=obj, obj_spec=obj_spec, fix_spec=fix_spec)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    obj_spec = f["obj_spec"]
    fix_spec = f["fix_spec"]
    return [
        f'Write a short comedy story for a child about how {hero.id} tries to open a {obj_spec.label} and discovers a mystery to solve.',
        f"Tell a gentle, funny story where a {hero.type} uses kindness instead of a rote routine to open {obj_spec.phrase}.",
        f'Write a simple story that includes the words "open" and "rote" and ends with the mystery inside the {obj_spec.label} being found.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, obj, obj_spec, fix_spec = f["hero"], f["parent"], f["obj"], f["obj_spec"], f["fix_spec"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {obj_spec.label}?",
            answer=f"{hero.id} wanted to open it and see what was inside.",
        ),
        QAItem(
            question=f"Why was the {obj_spec.label} a mystery to solve?",
            answer=f"It would not open at first, so nobody could see the surprise hidden inside until they tried a kinder way.",
        ),
        QAItem(
            question=f"What did {hero.id} do after the rote way did not work?",
            answer=f"{hero.id} chose a kinder plan, asked for help, and used {fix_spec.label} to loosen the {obj_spec.label}.",
        ),
        QAItem(
            question=f"What was found inside the {obj_spec.label} at the end?",
            answer=f"Inside the {obj_spec.label} was {obj_spec.hidden}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to be kind?",
            answer="Being kind means helping, sharing, and using gentle words or gentle hands so others feel safe and cared for.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something you do not understand yet, so you look for clues until you solve it.",
        ),
        QAItem(
            question="What does open mean?",
            answer="Open means not closed, so you can look inside, go through, or use what is in it.",
        ),
        QAItem(
            question="What does rote mean?",
            answer="Rote means doing something the same old way again and again without thinking much about a new solution.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid_combo(Place, Obj, Fix) :- setting(Place), object(Obj), fix(Fix),
    compatible(Obj, Fix).

valid_story(Place, Obj, Fix, Gender) :- valid_combo(Place, Obj, Fix),
    wears(Gender, Obj).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("hidden", oid, obj.hidden))
        lines.append(asp.fact("opening_method", oid, obj.opening_method))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("compatible", next(oid for oid, o in OBJECTS.items() if select_fix(o).id == fid), fid))
    for g in ["girl", "boy"]:
        for oid in OBJECTS:
            lines.append(asp.fact("wears", g, oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: open, rote, kindness, mystery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.object:
        combos = [c for c in combos if c[1] == args.object]
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.fix:
        combos = [c for c in combos if c[2] == args.fix]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obj_id, fix_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, object=obj_id, fix=fix_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], OBJECTS[params.object], FIXES[params.fix],
                 params.name, params.gender, params.parent, params.trait)
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
    for e in world.entities.values():
        bits = []
        if e.kind == "character":
            bits.append(f"memes={dict(e.memes)}")
        if e.openable:
            bits.append(f"open_state={e.open_state}")
        if e.stuck:
            bits.append("stuck=True")
        if e.hidden:
            bits.append(f"hidden={e.hidden!r}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="kitchen", object="jar", fix="warmcloth", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="playroom", object="box", fix="please", name="Ben", gender="boy", parent="father", trait="silly"),
    StoryParams(place="garden", object="tin", fix="teaspoon", name="Nora", gender="girl", parent="mother", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, object, fix) combos ({len(stories)} with gender):\n")
        for place, obj, fix in triples:
            genders = sorted(g for (pl, o, f, g) in stories if (pl, o, f) == (place, obj, fix))
            print(f"  {place:9} {obj:8} {fix:10} [{', '.join(genders)}]")
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: open the {p.object} in the {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
