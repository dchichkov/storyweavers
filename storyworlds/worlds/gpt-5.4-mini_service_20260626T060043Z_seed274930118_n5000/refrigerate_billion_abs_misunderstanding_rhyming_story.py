#!/usr/bin/env python3
"""
storyworlds/worlds/refrigerate_billion_abs_misunderstanding_rhyming_story.py
=============================================================================

A tiny, self-contained storyworld about a sweet kitchen misunderstanding:
someone says "refrigerate the billion abs," and a child has to figure out what
that could possibly mean. The world keeps the domain small, physical, and
emotionally legible, while the prose leans into a gentle rhyming-story feel.

Seed idea:
- A child hears a strange kitchen request.
- The child imagines "abs" as tummy muscles and "billion" as an impossible count.
- The parent meant a tray of snack squares called ABS.
- Refrigerating them saves the treat, and the misunderstanding turns into a laugh.

The story is built from stateful entities with meters and memes, plus a small
ASP twin for the reasonableness gate.
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
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
    cool_spot: str = "the fridge shelf"
    warm_spot: str = "the counter"


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    type: str
    needs_cold: bool
    spoil_meter: str
    rhyme_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    object: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", cool_spot="the fridge shelf", warm_spot="the counter"),
    "pantry": Setting(place="the pantry", cool_spot="the cold drawer", warm_spot="the sunny shelf"),
    "bakery": Setting(place="the bakery", cool_spot="the chill case", warm_spot="the glass counter"),
}

OBJECTS = {
    "abs": ObjectCfg(
        id="abs",
        label="ABS squares",
        phrase="a tray of ABS squares",
        type="snack",
        needs_cold=True,
        spoil_meter="melty",
        rhyme_word="snack",
        tags={"sweet", "cold", "rhyme"},
    ),
    "custard": ObjectCfg(
        id="custard",
        label="custard cups",
        phrase="a dish of custard cups",
        type="snack",
        needs_cold=True,
        spoil_meter="soft",
        rhyme_word="cup",
        tags={"sweet", "cold"},
    ),
    "berries": ObjectCfg(
        id="berries",
        label="berry bars",
        phrase="a tray of berry bars",
        type="snack",
        needs_cold=True,
        spoil_meter="sticky",
        rhyme_word="berry",
        tags={"sweet", "cold"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Finn", "Owen", "Theo", "Max"]
PARENT_TYPES = ["mother", "father"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def can_refrigerate(obj: ObjectCfg) -> bool:
    return obj.needs_cold


def explain_rejection(obj: ObjectCfg) -> str:
    return f"(No story: {obj.label} would not be a sensible thing to refrigerate.)"


def valid_choices() -> list[str]:
    return [oid for oid, obj in OBJECTS.items() if can_refrigerate(obj)]


# ---------------------------------------------------------------------------
# Story action helpers
# ---------------------------------------------------------------------------
def intro(world: World, child: Entity, parent: Entity, obj: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.type} who loved little kitchen rhymes and tidy lines. "
        f"{child.pronoun('possessive').capitalize()} {parent.type} liked making snacks that stayed bright and fine."
    )
    world.say(
        f"On the table sat {obj.phrase}, waiting for a cool, calm night."
    )


def misunderstanding(world: World, child: Entity, parent: Entity, obj: Entity) -> None:
    child.memes["confused"] = child.memes.get("confused", 0.0) + 1
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    world.say(
        f"Then {parent.id} said, \"Please refrigerate the billion abs.\""
    )
    world.say(
        f"{child.id} blinked and thought, \"A billion abs? That's a mountain of tummy-stretchy jabs!\""
    )
    world.trace.append("misunderstanding: child hears abs as muscles, not snack squares")
    obj.meters["warm"] = obj.meters.get("warm", 0.0) + 1


def explain(world: World, parent: Entity, child: Entity, obj: Entity) -> None:
    child.memes["understanding"] = child.memes.get("understanding", 0.0) + 1
    child.memes["confused"] = 0.0
    world.say(
        f"{parent.id} laughed and shook {parent.pronoun('possessive')} head. "
        f"\"I meant {obj.label}, not tummy abs. And billion was just a silly big sound in our little song.\""
    )
    world.say(
        f"{child.id} grinned at the trick of the tune, because the words were big, but the job was simple and true."
    )


def refrigerate(world: World, child: Entity, obj: Entity) -> None:
    obj.location = world.setting.cool_spot
    obj.meters["warm"] = max(0.0, obj.meters.get("warm", 0.0) - 1.0)
    obj.meters["cold"] = obj.meters.get("cold", 0.0) + 1.0
    world.say(
        f"Together they carried {obj.label} to {world.setting.cool_spot}, "
        f"where the cool air gave it a hush and a swoop."
    )


def end(world: World, child: Entity, parent: Entity, obj: Entity) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    obj.meters["fresh"] = obj.meters.get("fresh", 0.0) + 1
    world.say(
        f"Soon {obj.label} was chilled and neat, and {child.id} was laughing at the silly little loop."
    )
    world.say(
        f"The odd phrase had turned into a happy rhyme: a billion abs became a snack in the night, "
        f"and the kitchen felt sweet and bright."
    )


# ---------------------------------------------------------------------------
# Story generator
# ---------------------------------------------------------------------------
def tell(setting: Setting, obj_cfg: ObjectCfg, name: str, gender: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    obj = world.add(Entity(
        id=obj_cfg.id,
        type=obj_cfg.type,
        label=obj_cfg.label,
        phrase=obj_cfg.phrase,
        owner=child.id,
        caretaker=parent.id,
        location=setting.warm_spot,
        plural=True,
    ))
    obj.meters["warm"] = 1.0

    intro(world, child, parent, obj)
    world.para()
    misunderstanding(world, child, parent, obj)
    explain(world, parent, child, obj)
    world.para()
    refrigerate(world, child, obj)
    end(world, child, parent, obj)

    world.facts.update(
        child=child,
        parent=parent,
        obj=obj,
        obj_cfg=obj_cfg,
        setting=setting,
        resolved=True,
        misunderstood=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    obj = f["obj_cfg"]
    return [
        f'Write a short rhyming story for a young child about a misunderstanding involving the words "refrigerate", "billion", and "{obj.id}".',
        f"Tell a gentle kitchen story where {child.id} hears a strange request and learns what {obj.label} really means.",
        f"Write a playful story in rhyme where a parent asks a child to refrigerate something with a silly-sounding name.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    obj = f["obj"]
    obj_cfg = f["obj_cfg"]
    return [
        QAItem(
            question=f"What did {child.id} think the words 'refrigerate the billion abs' meant?",
            answer=f"{child.id} thought it meant a huge pile of tummy abs, like a billion muscle bumps, which made the request sound silly and impossible.",
        ),
        QAItem(
            question=f"What did {parent.id} really want refrigerated?",
            answer=f"{parent.id} really wanted {obj_cfg.phrase} chilled so it would stay fresh and tasty.",
        ),
        QAItem(
            question=f"How did the misunderstanding get fixed?",
            answer=f"{parent.id} explained that {obj_cfg.label} was the snack, not body abs, and then they put it in the fridge together.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{obj.label} went from warm on the counter to cool in the fridge, and {child.id} went from puzzled to happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does refrigerate mean?",
            answer="To refrigerate something means to put it in a cold place, like a fridge, so it stays fresh or cool.",
        ),
        QAItem(
            question="What are abs?",
            answer="Abs are the muscles in your belly, near your tummy.",
        ),
        QAItem(
            question="Why do some snacks need the fridge?",
            answer="Some snacks need the fridge because cold air helps them stay firm, fresh, and safe to eat.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    for line in world.trace:
        lines.append(line)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
needs_cold(abs).
needs_cold(custard).
needs_cold(berries).

valid_object(O) :- needs_cold(O).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.needs_cold:
            lines.append(asp.fact("needs_cold", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_objects() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show valid_object/1."))
    return sorted(set(a[0] for a in asp.atoms(model, "valid_object")))


def asp_verify() -> int:
    py = set(valid_choices())
    asp_set = set(asp_valid_objects())
    if py == asp_set:
        print(f"OK: ASP matches Python gate ({len(py)} objects).")
        return 0
    print("MISMATCH between ASP and Python gate")
    print("python-only:", sorted(py - asp_set))
    print("asp-only:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming kitchen storyworld with a misunderstanding.")
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
    if args.object and args.object not in valid_choices():
        raise StoryError(explain_rejection(OBJECTS[args.object]))
    oid = args.object or rng.choice(sorted(valid_choices()))
    obj = OBJECTS[oid]
    gender = args.gender or rng.choice(["girl", "boy"])
    if gender == "girl":
        name = args.name or rng.choice(GIRL_NAMES)
    else:
        name = args.name or rng.choice(BOY_NAMES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(object=oid, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS["kitchen"], OBJECTS[params.object], params.name, params.gender, params.parent)
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
        print(asp_program("#show valid_object/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_object/1."))
        vals = sorted(set(asp.atoms(model, "valid_object")))
        print(f"{len(vals)} valid objects:")
        for (oid,) in vals:
            print(f"  {oid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for oid in sorted(valid_choices()):
            params = StoryParams(
                object=oid,
                name="Mia",
                gender="girl",
                parent="mother",
            )
            params.seed = base_seed
            samples.append(generate(params))
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
            header = f"### {p.name}: {p.object}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
