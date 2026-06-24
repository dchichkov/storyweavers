#!/usr/bin/env python3
"""
A small mystery storyworld set in a storm drain.

Seed tale sketch:
---
A little child finds a clue in a storm drain and feels a sharp burst of
indignation when the clue seems to point the wrong way. The child thinks in
short, private inner-monologue lines, follows the trail, and discovers the real
owner of the lost thing. A careful helper brings a safe fix so the child can
solve the mystery without getting hurt.
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
    carried_by: Optional[str] = None
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

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the storm drain"
    damp: bool = True
    dark: bool = True


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    kind: str
    location: str
    shine: str
    clue_text: str
    owner_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    protects_from: set[str]
    helps_with: set[str]
    ready_line: str
    ending_line: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        import copy as _copy

        other = World(self.setting)
        other.entities = _copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "storm_drain": Setting(place="the storm drain", damp=True, dark=True),
}

CLUES = {
    "blue_button": Clue(
        id="blue_button",
        label="blue button",
        phrase="a little blue button with one shiny stitch",
        kind="button",
        location="beside the grate",
        shine="glinted like a tiny coin",
        clue_text="It looked like it had been torn from a coat, not dropped by a storm.",
        owner_hint="a navy raincoat",
        tags={"button", "clue", "wet"},
    ),
    "red_ribbon": Clue(
        id="red_ribbon",
        label="red ribbon",
        phrase="a red ribbon tied in a neat bow",
        kind="ribbon",
        location="stuck on a pebble",
        shine="wobbled in the water",
        clue_text="It looked too tidy to be storm trash.",
        owner_hint="a school backpack",
        tags={"ribbon", "clue", "wet"},
    ),
    "silver_key": Clue(
        id="silver_key",
        label="silver key",
        phrase="a small silver key",
        kind="key",
        location="caught in a seam of leaves",
        shine="caught the flashlight beam",
        clue_text="Keys do not wander far on their own, so somebody nearby must be looking.",
        owner_hint="a front door",
        tags={"key", "clue", "wet"},
    ),
}

GEAR = {
    "boots": Gear(
        id="boots",
        label="rain boots",
        phrase="rain boots",
        protects_from={"wet", "mud"},
        helps_with={"safe", "walk"},
        ready_line="she pulled on her rain boots first",
        ending_line="the boots kept her feet dry at the edge of the drain",
    ),
    "flashlight": Gear(
        id="flashlight",
        label="a flashlight",
        phrase="a flashlight",
        protects_from={"dark"},
        helps_with={"look", "solve"},
        ready_line="he switched on a flashlight",
        ending_line="the beam found the clue without making the puddle any deeper",
    ),
    "gloves": Gear(
        id="gloves",
        label="yellow gloves",
        phrase="yellow gloves",
        protects_from={"slime"},
        helps_with={"touch", "carry"},
        ready_line="they tugged on yellow gloves",
        ending_line="the gloves let them lift the clue cleanly",
    ),
}

CHILD_NAMES = ["Maya", "Leo", "Nina", "Toby", "Ava", "Ben"]
PARENT_NAMES = ["Mom", "Dad"]
TRAITS = ["curious", "careful", "brave", "quiet", "alert"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    clue: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def inner_monologue(world: World, hero: Entity, text: str) -> None:
    world.say(f"{hero.id} thought, “{text}”")


def predict_danger(world: World, clue: Clue) -> bool:
    return world.setting.damp and world.setting.dark and clue.kind in {"button", "ribbon", "key"}


def choose_gear(clue: Clue) -> Gear:
    if clue.kind == "key":
        return GEAR["flashlight"]
    if clue.kind == "ribbon":
        return GEAR["gloves"]
    return GEAR["boots"]


def tell_story(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Maya", "Nina", "Ava"} else "boy"))
    parent = world.add(Entity(id=params.parent, kind="character", type="mother" if params.parent == "Mom" else "father"))
    clue = CLUES[params.clue]

    world.facts.update(hero=hero, parent=parent, clue=clue, gear=choose_gear(clue))

    hero.memes["curiosity"] = 1
    hero.memes["indignation"] = 0
    world.say(f"{hero.id} was a {params.trait} little detective who liked quiet places and small puzzles.")
    world.say(f"That afternoon, {hero.id} and {parent.id} came to {world.setting.place}.")
    world.say(f"Near the grate, {clue.phrase} {clue.shine}. {clue.clue_text}")

    world.para()
    if predict_danger(world, clue):
        hero.memes["indignation"] = 1
        inner_monologue(world, hero, "That clue looks wrong. Someone must be in trouble, and I want the truth.")
        world.say(f"{hero.id} felt a flash of indignation because the clue did not fit the story the rain seemed to tell.")
        gear = choose_gear(clue)
        world.say(f"{parent.id} noticed the dark water and said, “Wait. We need {gear.phrase} first.”")
        world.say(gear.ready_line.capitalize() + ".")
        world.say(f"Then {hero.id} looked again, and the clue started to make sense.")
        if clue.id == "blue_button":
            owner = "the neighbor with the navy raincoat"
            reason = "One button had popped loose when the coat snagged on the grate."
            ending = f"The button had come from {owner}, and {parent.id} promised to help return it."
        elif clue.id == "red_ribbon":
            owner = "a child with a school backpack"
            reason = "The ribbon had tied a lunch bag and slipped off near the drain."
            ending = f"The ribbon belonged to {owner}, and {hero.id} smiled because the mystery was solved."
        else:
            owner = "the apartment on the corner"
            reason = "The key had fallen from a pocket during the walk by the curb."
            ending = f"The key belonged to {owner}, and {parent.id} could carry it safely back."
        world.say(reason)
        world.say(ending)
        world.para()
        world.say(f"In the end, {hero.id} was still by {world.setting.place}, but now the beam of {gear.label} and {hero.id}'s careful eyes had turned a muddy question into a clear answer.")
        world.say(f"{gear.ending_line.capitalize()}.")

        world.facts["resolved"] = True
        world.facts["owner_guess"] = owner
    else:
        world.say(f"{hero.id} kept looking, but the place did not seem mysterious enough to call for a big warning.")
        world.say(f"{hero.id} decided the safest answer was to ask {parent.id} and leave the drain alone.")
        world.facts["resolved"] = False
        world.facts["owner_guess"] = ""

    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    clue: Clue = f["clue"]  # type: ignore[assignment]
    return [
        f'Write a short mystery story for a child named {hero.id} that includes the word "dorsal" and the feeling of indignation.',
        f"Tell a storm drain mystery where {hero.id} finds {clue.phrase} and thinks carefully before guessing what it means.",
        f"Write a gentle detective story with inner monologue, a clue, and a safe helper in the storm drain.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    clue: Clue = f["clue"]  # type: ignore[assignment]
    gear: Gear = f["gear"]  # type: ignore[assignment]
    owner_guess: str = f.get("owner_guess", "")  # type: ignore[assignment]
    resolved: bool = bool(f.get("resolved"))

    qa = [
        QAItem(
            question=f"Where did {hero.id} and {parent.id} look for clues?",
            answer=f"They looked in {world.setting.place}, where the drain was dark and damp.",
        ),
        QAItem(
            question=f"What clue did {hero.id} find near the grate?",
            answer=f"{hero.id} found {clue.phrase}.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel indignation about the clue?",
            answer=(
                f"{hero.id} felt indignation because the clue looked out of place, "
                f"so it seemed like someone nearby had a problem that needed solving."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} think to themselves before the mystery became clear?",
            answer=(
                f"{hero.id} thought that the clue looked wrong and that the real story had to be hidden nearby."
            ),
        ),
    ]
    if resolved:
        qa.append(
            QAItem(
                question=f"How did {gear.label} help with the mystery?",
                answer=f"{gear.label} helped because it kept the search safe and made it easier to find the clue without slipping.",
            )
        )
        qa.append(
            QAItem(
                question=f"What turned out to be true about the clue?",
                answer=f"The clue belonged to {owner_guess}, so the mystery could be solved and the lost thing returned.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a storm drain?",
            answer="A storm drain is a big opening in the street that carries rainwater away so streets do not flood.",
        ),
        QAItem(
            question="What does a flashlight do?",
            answer="A flashlight makes a bright beam of light so you can see in dark places.",
        ),
        QAItem(
            question="What does indignation feel like?",
            answer="Indignation is a feeling of upset fairness, like when something seems wrong and you want it fixed.",
        ),
        QAItem(
            question="What does dorsal mean?",
            answer="Dorsal means on the back side of an animal or shape, like the dorsal fin on a fish.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(storm_drain).

clue(button; ribbon; key).
gear(boots; flashlight; gloves).

dark(storm_drain).
damp(storm_drain).

clue_kind(blue_button, button).
clue_kind(red_ribbon, ribbon).
clue_kind(silver_key, key).

helps(boots, safe).
helps(boots, walk).
helps(flashlight, look).
helps(flashlight, solve).
helps(gloves, touch).
helps(gloves, carry).

protects_from(boots, wet).
protects_from(boots, mud).
protects_from(flashlight, dark).
protects_from(gloves, slime).

valid(C, G) :- clue_kind(C, button), gear(G), protects_from(G, wet).
valid(C, G) :- clue_kind(C, ribbon), gear(G), protects_from(G, slime).
valid(C, G) :- clue_kind(C, key), gear(G), protects_from(G, dark).

#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "storm_drain")]
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue_item", cid))
        lines.append(asp.fact("clue_kind", cid, clue.kind))
    for gid, gear in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for p in sorted(gear.protects_from):
            lines.append(asp.fact("protects_from", gid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> set[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return set(asp.atoms(model, "valid"))


def python_valid() -> set[tuple[str, str]]:
    out = set()
    for cid, clue in CLUES.items():
        for gid, gear in GEAR.items():
            if clue.kind == "button" and "wet" in gear.protects_from:
                out.add((cid, gid))
            elif clue.kind == "ribbon" and "slime" in gear.protects_from:
                out.add((cid, gid))
            elif clue.kind == "key" and "dark" in gear.protects_from:
                out.add((cid, gid))
    return out


def asp_verify() -> int:
    a = asp_valid()
    p = python_valid()
    if a == p:
        print(f"OK: ASP matches Python ({len(a)} valid pairs).")
        return 0
    print("Mismatch between ASP and Python:")
    if a - p:
        print(" only in ASP:", sorted(a - p))
    if p - a:
        print(" only in Python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# Storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery set in a storm drain with inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--parent", choices=PARENT_NAMES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "storm_drain"
    clue = args.clue or rng.choice(sorted(CLUES))
    name = args.name or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, clue=clue, name=name, parent=parent, trait=trait)


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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id} ({e.kind}/{e.type}) " + " ".join(bits))
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
    StoryParams(place="storm_drain", clue="blue_button", name="Maya", parent="Mom", trait="curious"),
    StoryParams(place="storm_drain", clue="silver_key", name="Leo", parent="Dad", trait="careful"),
    StoryParams(place="storm_drain", clue="red_ribbon", name="Nina", parent="Mom", trait="alert"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = sorted(asp_valid())
        print(f"{len(pairs)} valid clue/gear pairs:")
        for cid, gid in pairs:
            print(f"  {cid:12} {gid}")
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
            header = f"### {p.name}: {p.clue} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
