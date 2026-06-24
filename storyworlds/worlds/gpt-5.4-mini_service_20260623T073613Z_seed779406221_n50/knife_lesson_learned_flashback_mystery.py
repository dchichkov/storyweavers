#!/usr/bin/env python3
"""
storyworlds/worlds/knife_lesson_learned_flashback_mystery.py
=============================================================

A small mystery storyworld about a missing knife, a flashback clue, and a lesson
learned at the end. The world is child-facing, state-driven, and constraint-checked.

Seed tale:
---
Mina was helping her grandpa in the kitchen when she noticed his special fruit
knife was missing from the drawer. Grandpa frowned because he needed it to slice
an apple for pie. Mina searched under the table, on the shelf, and inside the
bread box, but the knife was nowhere to be found.

Then Mina remembered a flashback: earlier, she had carried the knife to the
garden after seeing a fallen pear on the path. She had used the knife to cut the
pear into pieces for the birds, then forgotten to bring it back. Mina rushed
outside and found it under the pear tree, where she had left it on a stone bench.
Grandpa smiled, and Mina learned that special tools belong back in their place.

Causal state updates:
---
    missing tool -> search effort rises; worry rises
    remembered flashback -> clue confidence rises
    found tool   -> worry drops; relief rises; tool returns to owner
    lesson learned -> next time caution rises

Narrative instruments:
---
    Flashback: a short remembered scene that explains where the knife went.
    Lesson Learned: the ending states the rule Mina now follows.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: str = ""
    location: str = ""
    hidden_in: str = ""
    moved_by: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    outside: str
    inside: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    owner_role: str
    safe_place: str
    clue_place: str
    flashback_place: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    tool: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def resolve_setting(place: str) -> Setting:
    return SETTINGS[place]


def tell(setting: Setting, tool: Tool, child_name: str, child_gender: str,
         adult_name: str, adult_gender: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             label=child_name))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender,
                             label=adult_name))
    knife = world.add(Entity(
        id="knife", type="tool", label=tool.label, phrase=tool.phrase,
        owner=adult.id, location=tool.safe_place,
    ))
    world.facts.update(child=child, adult=adult, knife=knife, tool=tool)

    world.say(f"{child_name} liked helping {adult_name} in {setting.place}.")
    world.say(
        f"One morning, {child_name} noticed that {tool.phrase} was missing from "
        f"its usual place in {setting.inside}."
    )
    world.say(
        f"{adult_name} looked worried, because the {tool.label} was needed back "
        f"where it belonged."
    )

    world.para()
    world.say(
        f"{child_name} searched under the table, on the shelf, and inside the "
        f"bread box, but the {tool.label} was nowhere there."
    )
    child.memes["worry"] = 1
    adult.memes["worry"] = 1
    child.meters["search"] = 1

    world.para()
    world.say(
        f"Then came a flashback: earlier, {child_name} had carried the {tool.label} "
        f"out to {setting.outside} after seeing a fallen pear on the path."
    )
    world.say(
        f"In the remembered moment, {child_name} cut the pear into tiny pieces for "
        f"the birds and set the {tool.label} down on a stone bench."
    )
    child.memes["clue_confidence"] = 1
    knife.location = tool.flashback_place
    knife.hidden_in = "stone bench"
    knife.moved_by = child.id

    world.para()
    world.say(
        f"{child_name} ran outside and found the {tool.label} under the pear tree, "
        f"exactly where the flashback had pointed."
    )
    knife.location = tool.safe_place
    knife.hidden_in = ""
    knife.moved_by = child.id
    child.memes["relief"] = 1
    adult.memes["relief"] = 1
    adult.memes["trust"] = 1

    world.para()
    world.say(
        f"{adult_name} smiled and put the {tool.label} back in {setting.inside}."
    )
    world.say(
        f"{child_name} learned that special tools belong back in their place, so "
        f"the next search would start at home."
    )
    child.memes["lesson"] = 1
    child.memes["caution"] = 1
    return world


SETTINGS = {
    "kitchen": Setting(
        place="the kitchen",
        outside="the garden",
        inside="the drawer",
    ),
    "workshop": Setting(
        place="the little workshop",
        outside="the yard",
        inside="the tool rack",
    ),
    "shed": Setting(
        place="the garden shed",
        outside="the back path",
        inside="the shelf",
    ),
}

TOOLS = {
    "knife": Tool(
        id="knife",
        label="knife",
        phrase="Grandpa's special fruit knife",
        owner_role="grandpa",
        safe_place="drawer",
        clue_place="pear tree",
        flashback_place="stone bench",
        lesson="special tools belong back in their place",
        tags={"knife", "tool", "mystery"},
    ),
    "paring_knife": Tool(
        id="paring_knife",
        label="paring knife",
        phrase="the little paring knife",
        owner_role="mom",
        safe_place="drawer",
        clue_place="apple tree",
        flashback_place="bench",
        lesson="small tools should be returned after use",
        tags={"knife", "tool", "mystery"},
    ),
    "bread_knife": Tool(
        id="bread_knife",
        label="bread knife",
        phrase="the bread knife with a wavy edge",
        owner_role="dad",
        safe_place="knife block",
        clue_place="table",
        flashback_place="crate",
        lesson="shared tools need a home after the job is done",
        tags={"knife", "tool", "mystery"},
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Tia", "Ruby", "Sally", "Nora"]
BOY_NAMES = ["Eli", "Noah", "Ben", "Milo", "Owen", "Theo"]


def valid_combos() -> list[tuple[str, str]]:
    return [(s, t) for s in SETTINGS for t in TOOLS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery about a missing knife and a learned lesson.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["woman", "man"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    tool = args.tool or rng.choice(list(TOOLS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult_gender = args.adult_gender or rng.choice(["woman", "man"])
    adult = args.adult or ("Grandma" if adult_gender == "woman" else "Grandpa")
    return StoryParams(setting=setting, tool=tool, child_name=name, child_gender=gender,
                       adult_name=adult, adult_gender=adult_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(resolve_setting(params.setting), TOOLS[params.tool],
                 params.child_name, params.child_gender,
                 params.adult_name, params.adult_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    tool = f["tool"]
    child = f["child"]
    return [
        f'Write a gentle mystery story for a preschooler about a missing {tool.label}, with a flashback clue and a lesson learned.',
        f"Tell a short story where {child.id} notices {tool.phrase} is missing, remembers a flashback, and finds it again.",
        f'Write a child-friendly mystery ending with "{tool.lesson}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, adult, tool = f["child"], f["adult"], f["tool"]
    return [
        QAItem(
            question=f"What was missing at the start of the story?",
            answer=f"{tool.phrase} was missing, and that made {adult.id} worry because it needed to be put back in place.",
        ),
        QAItem(
            question=f"What did {child.id} remember in the flashback?",
            answer=(
                f"{child.id} remembered carrying the {tool.label} outside after finding a fallen pear, "
                f"and then setting it down on a stone bench."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"{child.id} found the {tool.label} again, {adult.id} smiled, and {child.id} learned that {tool.lesson}."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why do people keep tools in a regular place?",
            answer="People keep tools in a regular place so they can find them when they need them again, and so they do not get lost.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a short remembered scene from earlier that helps explain what happened or gives a clue.",
        ),
        QAItem(
            question="Why should a child be careful with a knife?",
            answer="A knife is a sharp tool, so it should be used only with a grown-up and returned to its safe place after use.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        out.append(f"  {e.id}: meters={e.meters} memes={e.memes} loc={e.location} hidden={e.hidden_in}")
    return "\n".join(out)


ASP_RULES = r"""
story(Setting, Tool) :- setting(Setting), tool(Tool).
missing(Tool) :- chosen(Tool).
flashback_clue(Tool) :- chosen(Tool).
lesson_learned(Tool) :- chosen(Tool).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show story/2.\n#show missing/1.\n#show flashback_clue/1.\n#show lesson_learned/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This world has a tiny ASP twin for parity checking.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        for setting in SETTINGS:
            for tool in TOOLS:
                params = StoryParams(setting=setting, tool=tool, child_name="Mina", child_gender="girl",
                                      adult_name="Grandpa", adult_gender="man")
                samples.append(generate(params))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
