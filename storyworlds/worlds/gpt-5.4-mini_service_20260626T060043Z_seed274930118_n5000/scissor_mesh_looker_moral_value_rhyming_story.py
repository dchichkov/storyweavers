#!/usr/bin/env python3
"""
A standalone story world for a tiny rhyming tale about scissors, mesh, and a
little moral choice.

Premise:
A child wants to use a scissor-shaped craft tool near a stretch of mesh. A
watchful looker worries that careless snipping could spoil the work. The child
learns to slow down, ask first, and help mend what was loose.

The world keeps two state axes for each entity:
- meters: physical conditions like damage, tension, and neatness
- memes: emotional and social conditions like worry, pride, and kindness

The resulting story is written in a simple rhyming, child-facing style.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core domain objects
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the craft table"
    indoors: bool = True


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    sharp: bool = True
    fix: str = "snip"
    value: str = "care"


@dataclass
class Material:
    id: str
    label: str
    phrase: str
    fragile: bool = True
    tears: bool = False


@dataclass
class StoryParams:
    place: str
    tool: str
    material: str
    hero_name: str
    hero_type: str
    looker_type: str
    moral_value: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "table": Setting(place="the craft table", indoors=True),
    "porch": Setting(place="the porch", indoors=False),
    "studio": Setting(place="the little studio", indoors=True),
}

TOOLS = {
    "scissor": Tool(
        id="scissor",
        label="scissors",
        phrase="a shiny pair of scissors",
        sharp=True,
        fix="snip",
        value="care",
    )
}

MATERIALS = {
    "mesh": Material(
        id="mesh",
        label="mesh",
        phrase="a loose sheet of mesh",
        fragile=True,
        tears=True,
    )
}

HERO_NAMES = ["Mia", "Noah", "Lina", "Toby", "Zoe", "Eli"]
LOOKER_NAMES = ["Nia", "Ivy", "Owen", "Maya", "June", "Theo"]
MORAL_VALUES = ["care", "patience", "honesty", "kindness", "sharing"]


# ---------------------------------------------------------------------------
# Rhyming helpers
# ---------------------------------------------------------------------------
def rhyme_line(*parts: str) -> str:
    return " ".join(parts)


def opening_line(hero: Entity, material: Entity, tool: Entity) -> str:
    return (
        f"{hero.id} found {tool.phrase} by {material.phrase}, "
        f"and gave a small smile with a curious spark."
    )


def warning_line(looker: Entity, hero: Entity, material: Entity) -> str:
    return (
        f"{looker.id} looked close and spoke with a gentle tone: "
        f'"Please ask first, dear {hero.id}, or the mesh may moan."'
    )


def moral_line(value: str) -> str:
    return {
        "care": "A careful hand is a happy hand, and careful steps are grand.",
        "patience": "Patience is a quiet light that helps the wrong become right.",
        "honesty": "Truth told plain can wash away the cloudy stain.",
        "kindness": "Kindness lifts a heavy day and helps the worry fade away.",
        "sharing": "When tools are shared with thoughtful cheer, the good work stays quite near.",
    }.get(value, "A gentle heart can mend the parts and brighten little starts.")


# ---------------------------------------------------------------------------
# State updates
# ---------------------------------------------------------------------------
def damage_mesh(world: World, hero: Entity, material: Entity, tool: Entity) -> None:
    if world.facts.get("asked_first"):
        return
    sig = ("damage", material.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    material.meters["torn"] = material.meters.get("torn", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.trace.append(f"{hero.id} snipped too soon and the mesh tore a little.")


def repair_mesh(world: World, hero: Entity, material: Entity, tool: Entity, looker: Entity) -> None:
    if not world.facts.get("asked_first"):
        return
    sig = ("repair", material.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    material.meters["torn"] = max(0, material.meters.get("torn", 0) - 1)
    material.meters["neat"] = material.meters.get("neat", 0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    looker.memes["glow"] = looker.memes.get("glow", 0) + 1
    world.trace.append("The mesh was mended, and the room felt brighter.")


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def tell_story(params: StoryParams) -> World:
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool choice.")
    if params.material not in MATERIALS:
        raise StoryError("Unknown material choice.")
    if params.place not in SETTINGS:
        raise StoryError("Unknown setting choice.")

    world = World(SETTINGS[params.place])
    hero = world.add(
        Entity(
            id=params.hero_name,
            kind="character",
            type=params.hero_type,
            meters={"restless": 0},
            memes={"want": 1, "curiosity": 1},
        )
    )
    looker = world.add(
        Entity(
            id="Looker",
            kind="character",
            type=params.looker_type,
            label="the looker",
            meters={"watchful": 1},
            memes={"care": 1, "worry": 1},
        )
    )
    tool = world.add(
        Entity(
            id="Scissor",
            type="tool",
            label=TOOLS[params.tool].label,
            phrase=TOOLS[params.tool].phrase,
            meters={"sharp": 1},
        )
    )
    material = world.add(
        Entity(
            id="Mesh",
            type="material",
            label=MATERIALS[params.material].label,
            phrase=MATERIALS[params.material].phrase,
            meters={"tension": 1, "neat": 0, "torn": 0},
        )
    )

    world.facts.update(
        hero=hero,
        looker=looker,
        tool=tool,
        material=material,
        moral_value=params.moral_value,
    )

    # Act 1
    world.say(opening_line(hero, material, tool))
    world.say(f"{hero.id} loved the shine, the snip, and the pretty craft art.")
    world.say(f"But {material.label} was loose and light, a place for a rip to start.")
    world.para()

    # Act 2
    world.say(f"{hero.id} reached for {tool.label} with a speedy little sway,")
    world.say(f"but {looker.id} stepped in and said, \"Let's ask first today.\"")
    world.say(warning_line(looker, hero, material))
    world.facts["asked_first"] = False
    damage_mesh(world, hero, material, tool)
    world.para()

    # Turn
    world.say(
        f"{hero.id} paused, then nodded, and put the sharp tool down;"
        f" that careful choice turned worry into a crown."
    )
    world.facts["asked_first"] = True
    repair_mesh(world, hero, material, tool, looker)
    world.say(
        f"Together they fixed the mesh with steady hands so true, "
        f"and every tiny knot looked neat and new."
    )
    world.para()

    # Resolution
    world.say(
        f"{hero.id} grinned and said, \"I see it now: kind hands are best.\""
    )
    world.say(
        f"{looker.id} smiled back, and the room felt warm and blessed."
    )
    world.say(moral_line(params.moral_value))

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Reasoning and QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a short rhyming story for a child about {hero.id}, scissors, and mesh.',
        f"Tell a gentle tale where {hero.id} learns to use scissors with care near mesh.",
        f'Compose a moral rhyming story that includes a looker, a scissor, and a mesh.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    looker: Entity = f["looker"]
    material: Entity = f["material"]
    tool: Entity = f["tool"]
    moral_value = f["moral_value"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {tool.label}?",
            answer=f"{hero.id} wanted to use the {tool.label} near the {material.label} for a little craft.",
        ),
        QAItem(
            question=f"Why did {looker.id} warn {hero.id}?",
            answer=f"{looker.id} warned {hero.id} because the {material.label} could get torn if the scissors were used too quickly.",
        ),
        QAItem(
            question="What changed when the hero listened?",
            answer="The child slowed down, asked first, and helped mend the mesh so it looked neat again.",
        ),
        QAItem(
            question=f"What moral value did the story teach?",
            answer=f"It taught {moral_value}, because careful and kind choices fixed the problem.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are scissors for?",
            answer="Scissors are tools used to cut paper, cloth, string, and other thin materials with care.",
        ),
        QAItem(
            question="What is mesh?",
            answer="Mesh is a net-like material with many tiny openings. It can be strong, but sharp tools can tear it.",
        ),
        QAItem(
            question="What does a looker do in a story like this?",
            answer="A looker watches closely, notices a problem, and helps the child make a wiser choice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    if world.trace:
        lines.append("events:")
        lines.extend(f"- {t}" for t in world.trace)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
entity(hero).
entity(looker).
entity(tool).
entity(material).

value(care).
value(patience).
value(honesty).
value(kindness).
value(sharing).

unsafe_use(hero, material) :- tool(scissor), material(mesh), not asked_first.
safe_use(hero, material) :- tool(scissor), material(mesh), asked_first.

torn(material) :- unsafe_use(hero, material).
mended(material) :- safe_use(hero, material).

moral(care) :- mended(material).
moral(patience) :- safe_use(hero, material).
moral(honesty) :- asked_first.
moral(kindness) :- looker_helped.
moral(sharing) :- asked_first, mended(material).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = [
        asp.fact("tool", "scissor"),
        asp.fact("material", "mesh"),
        asp.fact("looker", "looker"),
        asp.fact("asked_first"),
        asp.fact("looker_helped"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show moral/1."))
    morals = sorted(set(asp.atoms(model, "moral")))
    python_morals = [("care",), ("patience",), ("honesty",), ("kindness",), ("sharing",)]
    if morals:
        print("OK: ASP model produced moral atoms.")
        return 0
    print("MISMATCH: ASP model did not produce expected moral atoms.")
    return 1


# ---------------------------------------------------------------------------
# Parameter resolution and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming moral story world: scissor, mesh, looker.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--tool", choices=TOOLS.keys())
    ap.add_argument("--material", choices=MATERIALS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--looker", choices=["girl", "boy"])
    ap.add_argument("--moral-value", choices=MORAL_VALUES, dest="moral_value")
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    tool = args.tool or "scissor"
    material = args.material or "mesh"
    gender = args.gender or rng.choice(["girl", "boy"])
    looker_type = args.looker or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES if gender == "boy" else HERO_NAMES)
    moral_value = args.moral_value or rng.choice(MORAL_VALUES)
    return StoryParams(
        place=place,
        tool=tool,
        material=material,
        hero_name=hero_name,
        hero_type=gender,
        looker_type=looker_type,
        moral_value=moral_value,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def asp_show() -> str:
    return asp_program("#show moral/1.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_show())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_show())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(
                place=place,
                tool="scissor",
                material="mesh",
                hero_name="Mia",
                hero_type="girl",
                looker_type="boy",
                moral_value="care",
            )
            samples.append(generate(params))
    else:
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], ensure_ascii=False, indent=2))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
