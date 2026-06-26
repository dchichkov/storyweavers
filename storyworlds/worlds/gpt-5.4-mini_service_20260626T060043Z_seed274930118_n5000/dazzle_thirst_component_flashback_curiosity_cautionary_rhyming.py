#!/usr/bin/env python3
"""
storyworlds/worlds/dazzle_thirst_component_flashback_curiosity_cautionary_rhyming.py
====================================================================================

A small rhyming story world about a dazzling little component, a thirsty child,
and a cautionary flashback that helps curiosity land safely.

Premise:
- A child sees a shiny component that makes a lantern dazzle.
- The child becomes thirsty while exploring in the warm afternoon.
- A flashback recalls a past scold or lesson about careful hands.
- Curiosity pushes toward touching the component anyway.
- Caution and a small helpful choice lead to a safe, satisfying ending.

This world keeps the story child-facing and compact, with state-driven changes
to meters (physical) and memes (emotional). The narrative is rhyming, but not
song-like enough to become gimmicky; it remains a short story with a turn and
resolution.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def is_thirsty(self) -> bool:
        return self.meters.get("thirst", 0.0) >= THRESHOLD

    def is_bright(self) -> bool:
        return self.meters.get("dazzle", 0.0) >= THRESHOLD


@dataclass
class Setting:
    place: str = "the market lane"
    warmth: str = "warm"
    afford: set[str] = field(default_factory=set)


@dataclass
class Component:
    id: str
    label: str
    phrase: str
    property: str = "dazzle"
    owner: Optional[str] = None
    safe_to_touch: bool = True
    requires_permission: bool = True


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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


def _entity_mood(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _entity_meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A child is interested when curiosity rises.
interested(C) :- curious(C).

% A component is dazzling when it has the dazzle property.
dazzling(X) :- component(X), has_prop(X,dazzle).

% Touching is allowed only when the child has permission and caution.
safe_touch(C,X) :- child(C), component(X), permission(C,X), cautious(C), dazzling(X).

% A story is valid if it includes the setting, the child, and the component.
valid_story(S,C,X) :- setting(S), child(C), component(X), place(C,S), in_scene(X,S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.afford):
            lines.append(asp.fact("afford", sid, a))
    for cid, comp in COMPONENTS.items():
        lines.append(asp.fact("component", cid))
        lines.append(asp.fact("has_prop", cid, comp.property))
        lines.append(asp.fact("in_scene", cid, "lane"))
    for pid, person in PEOPLE.items():
        lines.append(asp.fact("child", pid))
        lines.append(asp.fact("place", pid, "lane"))
        if person["curious"]:
            lines.append(asp.fact("curious", pid))
        if person["cautious"]:
            lines.append(asp.fact("cautious", pid))
        for comp in person.get("permission_for", []):
            lines.append(asp.fact("permission", pid, comp))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    # Simple parity check: our Python validation matches the ASP gate.
    py = set(valid_stories())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python validation ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and Python validation:")
    print("only in Python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "lane": Setting(place="the market lane", warmth="warm", afford={"look", "sip", "touch"}),
    "fountain": Setting(place="the town fountain", warmth="cool", afford={"look", "sip"}),
    "workbench": Setting(place="the maker's workbench", warmth="warm", afford={"look", "touch"}),
}

COMPONENTS = {
    "gleam_chip": Component(
        id="gleam_chip",
        label="gleam chip",
        phrase="a tiny silver gleam chip",
        property="dazzle",
        safe_to_touch=True,
        requires_permission=True,
    ),
    "thirst_valve": Component(
        id="thirst_valve",
        label="thirst valve",
        phrase="a small brass thirst valve",
        property="dazzle",
        safe_to_touch=True,
        requires_permission=True,
    ),
}

PEOPLE = {
    "Mina": {"type": "girl", "curious": True, "cautious": False, "permission_for": ["gleam_chip"]},
    "Tob": {"type": "boy", "curious": True, "cautious": True, "permission_for": ["thirst_valve"]},
    "Pia": {"type": "girl", "curious": False, "cautious": True, "permission_for": ["gleam_chip", "thirst_valve"]},
}

NAMES = ["Mina", "Tob", "Pia"]
TRAITS = ["bright-eyed", "gentle", "lively", "small", "spry"]


@dataclass
class StoryParams:
    setting: str
    component: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def rhyming_pair(a: str, b: str) -> str:
    return f"{a} / {b}"


def valid_stories() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for cid in COMPONENTS:
            for name, pdata in PEOPLE.items():
                if cid in pdata["permission_for"]:
                    out.append((sid, cid, name))
    return out


def explain_rejection(setting: str, component: str, name: str) -> str:
    return (
        f"(No story: {name} cannot safely meet {component} in {setting} "
        f"under this world's permission-and-caution rules.)"
    )


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting=setting)
    person = PEOPLE[params.name]
    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=person["type"],
            label=params.name,
            meters={"thirst": 0.0, "dazzle": 0.0},
            memes={"curiosity": 0.0, "caution": 0.0, "flashback": 0.0, "relief": 0.0},
        )
    )
    comp = COMPONENTS[params.component]
    world.add(
        Entity(
            id=comp.id,
            kind="thing",
            type="component",
            label=comp.label,
            phrase=comp.phrase,
            owner=hero.id,
            meters={"dazzle": 1.0},
            memes={"risk": 0.0},
        )
    )
    world.facts.update(
        hero=hero,
        component=comp,
        setting=setting,
        permission=True,
        name=params.name,
        trait=params.trait,
    )
    return world


def flashback(world: World) -> None:
    hero: Entity = world.facts["hero"]
    hero.memes["flashback"] += 1
    world.say(
        f"Before today, a soft old memory had come back to play: "
        f"\"Look first, ask first, then touch with care,\" had been the lesson from a different day."
    )


def opening(world: World) -> None:
    hero: Entity = world.facts["hero"]
    comp: Component = world.facts["component"]
    setting: Setting = world.facts["setting"]
    world.say(
        f"{hero.id} was a {world.facts['trait']} child with a curious gaze, "
        f"walking the lane in the afternoon haze."
    )
    world.say(
        f"On the {setting.place}, {comp.phrase} shone with a dazzle so bright, "
        f"it winked like a star and it lit up the sight."
    )


def curiosity_rises(world: World) -> None:
    hero: Entity = world.facts["hero"]
    hero.memes["curiosity"] += 1
    hero.meters["thirst"] += 1
    world.say(
        f"{hero.id} drew a step near, with a wonder-filled grin; "
        f"the shine made {hero.id} lean, and the heat made {hero.id} thin."
    )
    world.say(
        f"{hero.id} felt thirst in the throat from the warm, dusty air, "
        f"and wanted a sip and a peek at the glare."
    )


def cautionary_turn(world: World) -> None:
    hero: Entity = world.facts["hero"]
    comp: Component = world.facts["component"]
    hero.memes["caution"] += 1
    world.say(
        f"Then the flashback came back like a bell in the breeze: "
        f"the rule was to pause before poking such things."
    )
    if comp.requires_permission:
        world.say(
            f"{hero.id} remembered, with a nod and a frown, "
            f"that bright little parts can fall down or break down."
        )


def resolve(world: World) -> None:
    hero: Entity = world.facts["hero"]
    comp: Component = world.facts["component"]
    hero.meters["thirst"] = max(0.0, hero.meters["thirst"] - 1.0)
    hero.memes["relief"] += 1
    world.say(
        f"{hero.id} chose not to snatch at the sparkly delight; "
        f"instead {hero.id} took a cool sip of water just right."
    )
    world.say(
        f"Then {hero.id} asked softly to look at the piece, "
        f"and watched how it gleamed while the worry turned peace."
    )
    world.say(
        f"So the dazzle stayed shining, the thirst went away, "
        f"and careful small hands made a safer play day."
    )


def tell_story(world: World) -> None:
    opening(world)
    world.para()
    curiosity_rises(world)
    flashback(world)
    world.para()
    cautionary_turn(world)
    resolve(world)


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for young children about a curious child, a dazzling component, and a safe choice.',
        f'Write a cautionary flashback story where {f["hero"].id} wants to touch {f["component"].label} but remembers to be careful first.',
        f'Compose a gentle rhyming tale that includes thirst, dazzle, and a component, ending with a calm and safe resolution.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    comp: Component = world.facts["component"]
    setting: Setting = world.facts["setting"]
    return [
        QAItem(
            question=f"What did {hero.id} see that looked so bright?",
            answer=f"{hero.id} saw {comp.phrase} on {setting.place}, and it shone with a dazzle so bright.",
        ),
        QAItem(
            question=f"Why did {hero.id} pause before touching {comp.label}?",
            answer=f"{hero.id} remembered the flashback lesson to look first and ask first, so careful hands would be safe.",
        ),
        QAItem(
            question=f"What helped {hero.id} feel better instead of rushing in?",
            answer=f"A cool sip of water eased {hero.id}'s thirst, and that calmer choice helped {hero.id} stay careful.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and the shining component?",
            answer=f"It ended safely: {hero.id} asked to look, stayed gentle, and the component kept shining without trouble.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "dazzle": [
        QAItem(
            question="What does it mean when something dazzles?",
            answer="When something dazzles, it shines so brightly that it can make your eyes want to blink or look away for a moment.",
        )
    ],
    "thirst": [
        QAItem(
            question="What helps when a child feels thirsty?",
            answer="A child who feels thirsty usually needs a drink of water or another safe drink so the body can feel comfortable again.",
        )
    ],
    "component": [
        QAItem(
            question="What is a component?",
            answer="A component is one small part of a bigger thing, like a piece that helps a toy, tool, or machine work.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [q for key in ("dazzle", "thirst", "component") for q in WORLD_KNOWLEDGE[key]]


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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:12} kind={e.kind:8} type={e.type:10} "
            f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.component and args.name:
        if args.name not in PEOPLE:
            raise StoryError("Unknown child name.")
        if args.component not in PEOPLE[args.name]["permission_for"]:
            raise StoryError(explain_rejection(args.setting or "lane", args.component, args.name))

    setting = args.setting or rng.choice(list(SETTINGS))
    component = args.component or rng.choice(list(COMPONENTS))
    valid_names = [n for n, pdata in PEOPLE.items() if component in pdata["permission_for"]]
    if args.name:
        if args.name not in valid_names:
            raise StoryError(explain_rejection(setting, component, args.name))
        name = args.name
    else:
        name = rng.choice(sorted(valid_names))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, component=component, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="lane", component="gleam_chip", name="Mina", trait="bright-eyed"),
    StoryParams(setting="workbench", component="thirst_valve", name="Tob", trait="gentle"),
    StoryParams(setting="fountain", component="thirst_valve", name="Pia", trait="lively"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world with dazzle, thirst, and a cautionary flashback.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--component", choices=COMPONENTS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/3."))
        print(f"{len(asp.atoms(model, 'valid_story'))} compatible stories.")
        for s, c, n in sorted(set(asp.atoms(model, "valid_story"))):
            print(f"  {s:10} {c:12} {n}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
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
            header = f"### {p.name}: {p.component} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
