#!/usr/bin/env python3
"""
storyworlds/worlds/hour_spear_rhyme_animal_story.py
====================================================

A small animal-story world with a gentle rhyming structure.

Premise:
- An animal friend has one hour to finish a proud little task.
- A spear is part of the task, but the spear starts out dull, wobbly, or
  poorly tied.
- A helper turns the trouble into a safe, tidy plan.
- The ending keeps the animal-story feel: brave, playful, concrete, and kind.

This world is intentionally tiny and constraint-checked. It produces complete
stories about an animal preparing for a short event, with a bit of rhyme in the
narration.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    worn_by: Optional[str] = None
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
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    trouble: str
    fix_hint: str
    keyword: str = "hour"
    tags: set[str] = field(default_factory=set)


@dataclass
class Spear:
    id: str
    label: str
    phrase: str
    safe_tip: bool
    needs_knot: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    covers: set[str] = field(default_factory=set)
    helps: set[str] = field(default_factory=set)
    prep: str = ""
    tail: str = ""
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


def rhyme(text: str) -> str:
    return text


def activity_at_risk(task: Task, spear: Spear) -> bool:
    return "spear" in task.tags and spear.safe_tip is False


def select_tool(task: Task, spear: Spear) -> Optional[Tool]:
    for tool in TOOLS:
        if task.id in tool.helps:
            return tool
    return None


def _warn(world: World, child: Entity, parent: Entity, task: Task, spear: Spear) -> None:
    world.say(
        f"One busy hour had just begun, and {child.id} wanted work and fun. "
        f"{child.pronoun().capitalize()} wanted to {task.verb}, but {parent.label} gave a careful hum. "
        f'"That spear looks sharp," {parent.label} said. "Let\'s make it safe and neat."'
    )


def _tension(world: World, child: Entity, task: Task) -> None:
    child.memes["impatient"] = child.memes.get("impatient", 0.0) + 1
    world.say(
        f"{child.id} felt the hurry in {child.pronoun("possessive")} toes; {task.rush} was all {child.pronoun("subject")} chose. "
        f"But one small hour can slip away, so the worry started to grow."
    )


def _fix(world: World, child: Entity, parent: Entity, task: Task, spear: Spear, tool: Tool) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1
    world.say(
        f"Then {parent.label} smiled and found a plan: {tool.prep}. "
        f"That made the spear feel steady and dear, with no more wobble or ban."
    )
    world.say(
        f"Soon {child.id} could {task.verb}, and the spear was kept safe by the tool. "
        f"They {tool.tail}. The hour rang clear, and the ending was bright and cool."
    )


SETTINGS = {
    "field": Setting(place="the sunny field", affords={"practice"}),
    "hill": Setting(place="the grassy hill", affords={"practice"}),
    "camp": Setting(place="the little camp", affords={"practice"}),
}

TASKS = {
    "practice": Task(
        id="practice",
        verb="practice with the spear",
        gerund="practicing with the spear",
        rush="dash to the practice spot",
        trouble="the spear could poke or slip",
        fix_hint="steady it with a safe grip",
        tags={"hour", "spear"},
    ),
}

SPEARS = {
    "toy": Spear(
        id="toy",
        label="play spear",
        phrase="a light play spear with a round tip",
        safe_tip=True,
        needs_knot=False,
        tags={"spear"},
    ),
    "wood": Spear(
        id="wood",
        label="wood spear",
        phrase="a slim wood spear with a blunt wrap",
        safe_tip=False,
        needs_knot=True,
        tags={"spear"},
    ),
    "reed": Spear(
        id="reed",
        label="reed spear",
        phrase="a reed spear that needed a safe tie",
        safe_tip=False,
        needs_knot=True,
        tags={"spear"},
    ),
}

TOOLS = [
    Tool(
        id="wrap",
        label="a soft wrap",
        helps={"practice"},
        prep="put a soft wrap on the tip first",
        tail="walked back to the field with the wrap in place",
    ),
    Tool(
        id="knot",
        label="a bright knot",
        helps={"practice"},
        prep="tie a bright knot around the spear",
        tail="marched on with the knot held tight",
    ),
]

NAMES = ["Milo", "Luna", "Pip", "Tara", "Niko", "Mina"]
ANIMALS = ["fox", "rabbit", "bear", "otter", "mouse", "cat"]
TRAITS = ["brave", "quick", "cheery", "merry", "spry", "bold"]


@dataclass
class StoryParams:
    place: str
    task: str
    spear: str
    name: str
    animal: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            task = TASKS[task_id]
            for spear_id, spear in SPEARS.items():
                if activity_at_risk(task, spear) and select_tool(task, spear):
                    combos.append((place, task_id, spear_id))
    return combos


def tell(setting: Setting, task: Task, spear: Spear, name: str, animal: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=name, kind="character", type=animal,
        traits=["little", trait],
    ))
    parent = world.add(Entity(id="Parent", kind="character", type="adult", label="the parent"))
    spear_ent = world.add(Entity(
        id="spear", type="tool", label=spear.label, phrase=spear.phrase,
        owner=child.id, caretaker=parent.id,
    ))
    tool = select_tool(task, spear)
    if tool is None:
        raise StoryError("No safe tool exists for this spear and task.")

    world.say(
        f"{child.id} was a little {trait} {animal} who loved a tidy rhyme. "
        f"{child.pronoun().capitalize()} liked a clear plan, a bright tune, and a good use of time."
    )
    world.say(
        f"At {setting.place}, {child.id} wanted to {task.verb}. "
        f"The {spear.label} looked brave, but it still needed care."
    )
    world.para()
    _warn(world, child, parent, task, spear_ent)
    _tension(world, child, task)
    world.para()
    _fix(world, child, parent, task, spear_ent, tool)

    world.facts.update(
        child=child,
        parent=parent,
        spear=spear_ent,
        task=task,
        tool=tool,
        setting=setting,
    )
    return world


CURATED = [
    StoryParams(place="field", task="practice", spear="wood", name="Milo", animal="fox", trait="brave"),
    StoryParams(place="hill", task="practice", spear="reed", name="Luna", animal="rabbit", trait="spry"),
    StoryParams(place="camp", task="practice", spear="wood", name="Pip", animal="otter", trait="cheery"),
]


KNOWLEDGE = {
    "hour": [
        (
            "What is an hour?",
            "An hour is a measure of time. It is sixty minutes long.",
        )
    ],
    "spear": [
        (
            "What is a spear?",
            "A spear is a long pointed tool or weapon. In stories for little children, it should be handled safely and carefully.",
        )
    ],
    "rhyme": [
        (
            "What is rhyme?",
            "Rhyme is when words sound alike at the end, like tune and moon.",
        )
    ],
    "animal": [
        (
            "What is an animal?",
            "An animal is a living creature, like a fox, rabbit, bear, cat, or mouse.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story for a young child that includes the words "{f["task"].keyword}" and "spear".',
        f"Tell a rhyming story about {f['child'].id}, a little {f['child'].type}, who wants to {f['task'].verb} within one hour.",
        f"Write a gentle story where a parent helps a small animal make a spear safe before practice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, task, spear, tool = f["child"], f["parent"], f["task"], f["spear"], f["tool"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {child.id}, a little {child.traits[-1]} {child.type}, and {parent.label}.",
        ),
        QAItem(
            question=f"What did {child.id} want to do at first?",
            answer=f"{child.id} wanted to {task.verb} during the one hour they had for practice.",
        ),
        QAItem(
            question=f"What was the trouble with the spear?",
            answer=f"The {spear.label} needed care because it was not safe enough yet.",
        ),
        QAItem(
            question=f"How did they fix the problem?",
            answer=f"They used {tool.label} to make the spear safer before {child.id} kept practicing.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.id} practicing happily while the safe spear stayed steady and the hour ended well.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = set(world.facts["task"].tags) | {"animal", "rhyme", "hour", "spear"}
    for key in ["hour", "spear", "rhyme", "animal"]:
        if key in tags:
            for q, a in KNOWLEDGE[key]:
                out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
task_ok(P,T,S) :- place(P), task(T), spear(S), affords(P,T), needs_fix(T,S), has_tool(T,S).
valid_story(P,T,S) :- task_ok(P,T,S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        for tag in sorted(task.tags):
            lines.append(asp.fact("tag", tid, tag))
    for sid, spear in SPEARS.items():
        lines.append(asp.fact("spear", sid))
        if not spear.safe_tip:
            lines.append(asp.fact("needs_fix", "practice", sid))
        else:
            lines.append(asp.fact("safe", sid))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        lines.append(asp.fact("has_tool", "practice", tool.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with hour, spear, and rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--spear", choices=SPEARS)
    ap.add_argument("--name")
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.spear is None or c[2] == args.spear)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, task, spear = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    animal = args.animal or rng.choice(ANIMALS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, task=task, spear=spear, name=name, animal=animal, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TASKS[params.task], SPEARS[params.spear], params.name, params.animal, params.trait)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print("  ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
