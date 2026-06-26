#!/usr/bin/env python3
"""
A small superhero story world about a writer, teamwork, and a cautionary mistake
that turns into a funny, helpful rescue.

Seed premise:
- A writer wants to finish a superhero story.
- A teammate hurries, makes a risky choice, and things wobble.
- The team fixes the problem together, learns caution, and ends with a bright win.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom", "writer"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    mishap: str
    helpful: str
    tag: str
    zone: set[str]


@dataclass
class Tool:
    id: str
    label: str
    protects: set[str]
    fixes: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "newsroom": Setting(place="the newsroom", indoors=True, affords={"inkstorm", "rushing", "flash"}),
    "library": Setting(place="the library corner", indoors=True, affords={"inkstorm", "flash"}),
    "rooftop": Setting(place="the rooftop office", indoors=False, affords={"rushing", "flash"}),
}

ACTIONS = {
    "inkstorm": Action(
        id="inkstorm",
        verb="cover the page with ink",
        gerund="covering pages with ink",
        rush="spill the ink jar",
        risk="the page",
        mishap="the page got blotchy and hard to read",
        helpful="slow down and use a blotter",
        tag="ink",
        zone={"hands", "torso"},
    ),
    "rushing": Action(
        id="rushing",
        verb="dash through the notes",
        gerund="dashing through notes",
        rush="skip the safety check",
        risk="the plan",
        mishap="the plan turned messy and confusing",
        helpful="check each step together",
        tag="caution",
        zone={"hands", "head"},
    ),
    "flash": Action(
        id="flash",
        verb="test a flash gadget",
        gerund="testing a flash gadget",
        rush="press the button too soon",
        risk="the room",
        mishap="the flash made everyone blink and drop the stapler",
        helpful="count to three first",
        tag="humor",
        zone={"hands", "eyes"},
    ),
}

TOOLS = {
    "blotter": Tool(
        id="blotter",
        label="a thick blotter",
        protects={"ink"},
        fixes={"inkstorm"},
        prep="put down a thick blotter first",
        tail="set the blotter under the page",
    ),
    "checklist": Tool(
        id="checklist",
        label="a checklist",
        protects={"caution"},
        fixes={"rushing"},
        prep="make a checklist and read it together",
        tail="went back and checked every step",
    ),
    "goggles": Tool(
        id="goggles",
        label="comic goggles",
        protects={"humor"},
        fixes={"flash"},
        prep="wear comic goggles first",
        tail="put on the comic goggles",
    ),
}

WRITERS = ["Mina", "Ivy", "Nora", "Eli", "Theo", "June", "Ada", "Luca"]
TRAITS = ["brave", "careful", "curious", "quick-thinking", "patient", "lively"]
SIDEKICKS = ["helper", "sidekick", "junior hero", "comic partner"]


@dataclass
class StoryParams:
    place: str
    action: str
    tool: str
    writer: str
    sidekick: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def action_needs_tool(action: Action, tool: Tool) -> bool:
    return action.tag in tool.protects and action.id in tool.fixes


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for action_id in setting.affords:
            for tool_id, tool in TOOLS.items():
                if action_needs_tool(ACTIONS[action_id], tool):
                    combos.append((place, action_id, tool_id))
    return combos


def explain_rejection(action: Action, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not reasonably fix {action.gerund}. "
        f"Choose the matching tool for the risky moment.)"
    )


def setting_line(setting: Setting) -> str:
    if setting.indoors:
        return f"{setting.place.capitalize()} was quiet except for paper rustling."
    return f"{setting.place.capitalize()} smelled like wind and old stories."


def story_title(params: StoryParams) -> str:
    return f"{params.writer} and the {ACTIONS[params.action].id} problem"


# ---------------------------------------------------------------------------
# Narrative
# ---------------------------------------------------------------------------

def tell(setting: Setting, action: Action, tool: Tool, writer_name: str, sidekick_name: str, trait: str) -> World:
    world = World(setting)

    writer = world.add(Entity(
        id=writer_name,
        kind="character",
        type="writer",
        label="the writer",
        meters={"focus": 1.0},
        memes={"hope": 1.0, "pride": 1.0},
    ))
    sidekick = world.add(Entity(
        id=sidekick_name,
        kind="character",
        type="sidekick",
        label="the sidekick",
        meters={"energy": 1.0},
        memes={"eager": 1.0},
    ))
    page = world.add(Entity(
        id="page",
        type="page",
        label="story page",
        phrase="a fresh story page",
        caretaker=writer.id,
    ))

    world.say(f"{writer.id} was a {trait} writer who loved big superhero adventures.")
    world.say(f"{sidekick.id} was {writer.pronoun('possessive')} {SIDEKICKS[0]} and helped with every idea.")
    world.say(f"{writer.id} wanted to finish a bold comic before dinner, and the blank page waited on the desk.")
    world.para()
    world.say(setting_line(setting))
    world.say(f"Today, the team tried to {action.verb}.")
    world.say(f"But when {sidekick.id} rushed to {action.rush}, {action.mishap}.")
    sidekick.memes["oops"] = 1.0
    sidekick.memes["guilt"] = 1.0
    writer.memes["concern"] = 1.0
    page.meters["messy"] = 1.0
    world.say(f"{writer.id} frowned, but {writer.id} did not shout. {writer.id} knew heroes work better together.")
    world.para()
    world.say(f"{writer.id} said, 'Let's {action.helpful}.'")
    world.say(f"Then they used {tool.label}: they {tool.prep}.")
    writer.memes["teamwork"] = 1.0
    sidekick.memes["teamwork"] = 1.0
    page.meters["messy"] = 0.0
    page.meters["clean"] = 1.0
    page.memes["readable"] = 1.0
    world.say(f"Together they {tool.tail}, and the trouble began to fade.")
    world.say(f"{sidekick.id} learned to slow down, and {writer.id} grinned at the silly little mistake that had almost blown the scene apart.")
    world.para()
    world.say(f"At last, the comic page was clear again, and the hero team finished the story with a bright, careful ending.")
    world.say(f"{writer.id} wrote the final line, and {sidekick.id} held the stapler like it was a trophy.")

    world.facts.update(
        writer=writer,
        sidekick=sidekick,
        page=page,
        action=action,
        tool=tool,
        setting=setting,
        trait=trait,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    writer = f["writer"]
    action = f["action"]
    tool = f["tool"]
    return [
        f"Write a short superhero story about a writer named {writer.id} whose teammate makes a risky {action.tag} mistake.",
        f"Tell a funny, cautionary story where teamwork helps {writer.id} fix a {action.id} problem with {tool.label}.",
        f"Write a child-friendly superhero tale that ends with {writer.id} and a helper learning to slow down and work together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    writer = f["writer"]
    sidekick = f["sidekick"]
    action = f["action"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"The story is mainly about {writer.id}, a writer who works like a superhero with {sidekick.id}."
        ),
        QAItem(
            question=f"What mistake did {sidekick.id} make?",
            answer=f"{sidekick.id} rushed and caused {action.mishap}, which made the team stop and fix the problem carefully."
        ),
        QAItem(
            question=f"How did the team solve the problem?",
            answer=f"They worked together and used {tool.label} so they could {action.helpful} and finish safely."
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the page was clean again and {sidekick.id} had learned to slow down instead of rushing."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a writer do?",
            answer="A writer makes stories, articles, or other words by choosing ideas and putting them on paper or a screen."
        ),
        QAItem(
            question="Why is teamwork helpful?",
            answer="Teamwork is helpful because people can combine their ideas and help each other when a job is tricky."
        ),
        QAItem(
            question="Why should heroes be careful?",
            answer="Heroes should be careful because rushing can cause mistakes, and a good plan keeps everyone safer."
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
action(A) :- activity(A).
tool(T) :- tool_def(T).

compatible(P,A,T) :- affords(P,A), action_tag(A,Tag), tool_protects(T,Tag), tool_fixes(T,A).

#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if setting.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("action_tag", aid, action.tag))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool_def", tid))
        for p in sorted(tool.protects):
            lines.append(asp.fact("tool_protects", tid, p))
        for a in sorted(tool.fixes):
            lines.append(asp.fact("tool_fixes", tid, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - ac:
        print("  only in Python:", sorted(py - ac))
    if ac - py:
        print("  only in clingo:", sorted(ac - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world about a writer, teamwork, caution, and humor.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--writer", choices=WRITERS)
    ap.add_argument("--sidekick")
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
    combos = valid_combos()
    if args.action and args.tool:
        if not action_needs_tool(ACTIONS[args.action], TOOLS[args.tool]):
            raise StoryError(explain_rejection(ACTIONS[args.action], TOOLS[args.tool]))

    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.action is None or c[1] == args.action)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")

    place, action, tool = rng.choice(filtered)
    writer = args.writer or rng.choice(WRITERS)
    sidekick = args.sidekick or rng.choice([s for s in WRITERS if s != writer])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, tool=tool, writer=writer, sidekick=sidekick, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], TOOLS[params.tool], params.writer, params.sidekick, params.trait)
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
        print()
        print("--- trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            print(f"{e.id}: {e.type} {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="newsroom", action="inkstorm", tool="blotter", writer="Mina", sidekick="Pip", trait="careful"),
            StoryParams(place="newsroom", action="rushing", tool="checklist", writer="Ivy", sidekick="Rex", trait="brave"),
            StoryParams(place="library", action="flash", tool="goggles", writer="Nora", sidekick="Bo", trait="patient"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
