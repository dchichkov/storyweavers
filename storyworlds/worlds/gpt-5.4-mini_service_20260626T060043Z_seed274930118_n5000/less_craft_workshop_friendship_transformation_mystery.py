#!/usr/bin/env python3
"""
A standalone storyworld for a small mystery in a craft workshop.

Premise:
- A child notices something odd in a craft workshop.
- A missing or changed craft item creates a mystery.
- A friend helps investigate.
- The mystery resolves through a transformation in state, not a frozen retelling.

This world aims for child-facing, concrete mystery prose with a friendship beat
and a transformation turn. The word "less" is included as a seed word/theme
without leaking internal mechanics into the story.
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
# Core domain
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden: bool = False
    transformed: bool = False
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
    place: str = "the craft workshop"
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    change: str
    clue: str
    effect: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    tool: str
    hero_name: str
    friend_name: str
    hero_gender: str
    parent_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "craft_workshop": Setting(place="the craft workshop", affords={"glue", "paint", "clay", "paper"}),
}

TOOLS = {
    "glue": Tool(
        id="glue",
        label="glue",
        phrase="a bottle of blue glue",
        change="stuck together",
        clue="the cap was left open",
        effect="it can stick paper, buttons, and beads together",
        reveal="the missing tag was glued to the wrong box",
        tags={"sticky", "mystery", "transformation"},
    ),
    "paint": Tool(
        id="paint",
        label="paint",
        phrase="a cup of bright green paint",
        change="changed color",
        clue="there was a green handprint on the table",
        effect="it can change plain paper into something bright",
        reveal="the plain mask became a leafy mask",
        tags={"color", "mystery", "transformation"},
    ),
    "clay": Tool(
        id="clay",
        label="clay",
        phrase="a lump of soft clay",
        change="reshaped",
        clue="one corner had tiny finger marks",
        effect="it can be pressed into a new shape",
        reveal="the round coin dish became a tiny star bowl",
        tags={"shape", "mystery", "transformation"},
    ),
    "paper": Tool(
        id="paper",
        label="paper",
        phrase="a stack of pale paper stars",
        change="folded",
        clue="there were folded corners",
        effect="it can turn into cranes, boats, and stars",
        reveal="the blank page turned into a paper crane",
        tags={"folding", "mystery", "transformation"},
    ),
}

NAMES = ["Mina", "Toby", "Iris", "Noah", "Luna", "Eli", "Ada", "Finn"]
TRAITS = ["curious", "gentle", "careful", "quiet", "brave"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(place: str, tool: str) -> bool:
    return place in SETTINGS and tool in TOOLS


def valid_combos() -> list[tuple[str, str]]:
    return [(p, t) for p in SETTINGS for t in TOOLS]


def explain_rejection(place: str, tool: str) -> str:
    return f"(No story: {tool} is not part of {place}.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def _act_search(world: World, hero: Entity, friend: Entity, parent: Entity, tool: Tool) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
    world.say(
        f"{hero.id} and {friend.id} were in {world.setting.place}, where scissors, ribbons, and buttons waited on the tables."
    )
    world.say(
        f"{hero.id} noticed something strange: {tool.clue}, but the craft room looked too neat for a big mess."
    )
    world.say(
        f'That made {hero.id} whisper, "Something here changed, but it changed in a way that left less and less to see."'
    )


def _act_discover(world: World, hero: Entity, friend: Entity, tool: Tool) -> None:
    hero.memes["suspicion"] = hero.memes.get("suspicion", 0) + 1
    friend.memes["loyalty"] = friend.memes.get("loyalty", 0) + 1
    world.say(
        f"{friend.id} stayed close and looked carefully with {hero.id}."
    )
    world.say(
        f"Together they followed the clue to a small tray near the back wall, where {tool.label} had done its work."
    )


def _act_transform(world: World, hero: Entity, friend: Entity, tool: Tool) -> None:
    obj = world.get("project")
    obj.transformed = True
    obj.hidden = False
    obj.meters["changed"] = obj.meters.get("changed", 0) + 1
    world.say(
        f"They found the project at last: {tool.reveal}."
    )
    world.say(
        f"What had looked missing was only changed. The plain thing was not gone; it had become something new."
    )
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    friend.memes["pride"] = friend.memes.get("pride", 0) + 1


def _act_friendship(world: World, hero: Entity, friend: Entity, parent: Entity, tool: Tool) -> None:
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    friend.memes["trust"] = friend.memes.get("trust", 0) + 1
    world.say(
        f"{parent.id} smiled when the answer appeared, because the mystery was never mean."
    )
    world.say(
        f'{parent.id} said, "{hero.id}, you solved it with a friend. That is the best kind of puzzle."'
    )
    world.say(
        f"{hero.id} grinned at {friend.id}. Their friendship felt bigger than the mystery now."
    )


def tell(setting: Setting, tool: Tool, hero_name: str, friend_name: str,
         hero_gender: str, parent_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender))
    friend = world.add(Entity(id=friend_name, kind="character", type="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type="adult"))
    project = world.add(Entity(
        id="project",
        kind="thing",
        type="craft",
        label="project",
        phrase=tool.phrase,
        owner=hero.id,
        hidden=True,
    ))
    world.facts.update(hero=hero, friend=friend, parent=parent, tool=tool, project=project)

    world.say(
        f"{hero.id} came to {world.setting.place} with {friend.id} for a quiet afternoon of making things."
    )
    world.say(
        f"On the table sat {tool.phrase}, and {hero.id} had been looking forward to it all day."
    )
    world.para()
    _act_search(world, hero, friend, parent, tool)
    world.para()
    _act_discover(world, hero, friend, tool)
    _act_transform(world, hero, friend, tool)
    world.para()
    _act_friendship(world, hero, friend, parent, tool)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    tool: Tool = f["tool"]  # type: ignore[assignment]
    return [
        f'Write a short mystery story set in a craft workshop about {hero.id} and {friend.id}, and include the word "less".',
        f"Tell a gentle mystery where {hero.id} thinks something is missing, but the answer turns out to be a transformation.",
        f"Write a child-friendly friendship story in a craft workshop that ends with {tool.label} explaining the change.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    tool: Tool = f["tool"]  # type: ignore[assignment]
    project: Entity = f["project"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Why did {hero.id} think there was a mystery in the workshop?",
            answer=f"{hero.id} saw {tool.clue}, so it looked like something had gone missing or changed."
        ),
        QAItem(
            question=f"Who helped {hero.id} look for the answer?",
            answer=f"{friend.id} stayed beside {hero.id} and helped follow the clue."
        ),
        QAItem(
            question=f"What was really happening to the project?",
            answer=f"The project was not lost. It was transformed, so {project.label} had become something new."
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {friend.id}?",
            answer=f"{parent.id} praised their friendship, and the two children felt proud because they solved the mystery together."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a craft workshop?",
            answer="A craft workshop is a place where people make things with paper, paint, glue, clay, and other materials."
        ),
        QAItem(
            question="What does it mean for something to transform?",
            answer="To transform means to change into something new."
        ),
        QAItem(
            question="Why can glue help with crafts?",
            answer="Glue helps crafts because it can stick pieces together so they stay in place."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.hidden:
            bits.append("hidden=True")
        if e.transformed:
            bits.append("transformed=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(craft_workshop).
affords(craft_workshop, glue).
affords(craft_workshop, paint).
affords(craft_workshop, clay).
affords(craft_workshop, paper).

tool(glue).
tool(paint).
tool(clay).
tool(paper).

valid(Place, Tool) :- setting(Place), affords(Place, Tool).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "craft_workshop")]
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
        lines.append(asp.fact("affords", "craft_workshop", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    try:
        cl = set(asp_valid_combos())
    except Exception as exc:
        print(f"ASP unavailable or failed: {exc}")
        return 1
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Craft workshop mystery with friendship and transformation.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--tool", choices=TOOLS.keys())
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--parent")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    place = args.place or "craft_workshop"
    tool = args.tool or rng.choice(list(TOOLS.keys()))
    if not valid_combo(place, tool):
        raise StoryError(explain_rejection(place, tool))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != name])
    parent = args.parent or rng.choice(["Aunt Jo", "Mr. Lee", "Mom", "Dad"])
    return StoryParams(place=place, tool=tool, hero_name=name, friend_name=friend, hero_gender=gender, parent_name=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        TOOLS[params.tool],
        params.hero_name,
        params.friend_name,
        params.hero_gender,
        params.parent_name,
    )
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for c in combos:
            print(f"  {c}")
        return

    if args.all:
        params_list = [
            StoryParams("craft_workshop", "glue", "Mina", "Toby", "girl", "Mom"),
            StoryParams("craft_workshop", "paint", "Iris", "Noah", "girl", "Dad"),
            StoryParams("craft_workshop", "clay", "Eli", "Luna", "boy", "Mr. Lee"),
            StoryParams("craft_workshop", "paper", "Ada", "Finn", "girl", "Aunt Jo"),
        ]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        params_list = []
        seen = set()
        i = 0
        while len(params_list) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            key = (params.place, params.tool, params.hero_name, params.friend_name, params.hero_gender, params.parent_name)
            if key in seen:
                continue
            seen.add(key)
            params_list.append(params)

    samples = [generate(p) for p in params_list]

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
