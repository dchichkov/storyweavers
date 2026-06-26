#!/usr/bin/env python3
"""
A small ghost-story world about a brave child, a spooky kitchen, and a bowl of bouillon
that only comes out right when teamwork quiets the fear.
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
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretakers: list[str] = field(default_factory=list)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "daughter"}
        male = {"boy", "father", "dad", "man", "son"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "they" if self.plural else self.pronoun("subject")

    def them(self) -> str:
        return "them" if self.plural else self.pronoun("object")


@dataclass
class Setting:
    place: str
    shadowy: bool = True


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    risk: str
    keyword: str
    sound: str
    requires: set[str] = field(default_factory=set)
    effect: str = "spilled"
    mess: str = "messy"


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    need: set[str]
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    task: str
    tool: str
    name: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "old_kitchen": Setting(place="the old kitchen"),
    "cellar_stove": Setting(place="the cellar kitchen"),
    "attic_pantry": Setting(place="the attic pantry"),
}

TASKS = {
    "bouillon": Task(
        id="bouillon",
        verb="stir the bouillon",
        gerund="stirring the bouillon",
        risk="the pot might boil over",
        keyword="bouillon",
        sound="the spoon tapped the pot in tiny clinks",
        requires={"broth", "salt", "heat"},
        effect="boiled over",
        mess="hot",
    ),
    "noodles": Task(
        id="noodles",
        verb="drop the noodles",
        gerund="dropping the noodles",
        risk="the noodles might clump and stick",
        keyword="noodles",
        sound="the noodles slid with a soft hiss",
        requires={"broth", "heat"},
        effect="clumped",
        mess="sticky",
    ),
    "candlesoup": Task(
        id="candlesoup",
        verb="carry the candle soup",
        gerund="carrying the candle soup",
        risk="the candlelight might flicker out",
        keyword="candle",
        sound="the flame trembled and whispered",
        requires={"light"},
        effect="dimmed",
        mess="dark",
    ),
}

TOOLS = {
    "ladle": Tool(
        id="ladle",
        label="a long ladle",
        phrase="a long ladle with a shiny handle",
        helps={"bouillon", "noodles"},
        need={"broth"},
    ),
    "apron": Tool(
        id="apron",
        label="a clean apron",
        phrase="a clean apron with deep pockets",
        helps={"bouillon", "noodles"},
        need={"heat"},
    ),
    "lantern": Tool(
        id="lantern",
        label="a little lantern",
        phrase="a little lantern with a steady wick",
        helps={"candlesoup"},
        need={"light"},
    ),
    "mitts": Tool(
        id="mitts",
        label="oven mitts",
        phrase="a pair of thick oven mitts",
        helps={"bouillon", "noodles"},
        need={"heat"},
        plural=True,
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Ivy", "Nora", "Elin"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Jasper", "Hugo"]
PARENTS = ["mother", "father"]
TRAITS = ["brave", "careful", "curious", "steady", "kind"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def task_reachable(task: Task) -> bool:
    return True


def choose_tool(task: Task) -> Optional[Tool]:
    for tool in TOOLS.values():
        if task.id in tool.helps:
            return tool
    return None


def risk_reason(task: Task, tool: Tool) -> bool:
    return task.id in tool.helps


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for r in sorted(t.requires):
            lines.append(asp.fact("requires", tid, r))
        lines.append(asp.fact("risk_word", tid, t.risk))
    for uid, u in TOOLS.items():
        lines.append(asp.fact("tool", uid))
        for h in sorted(u.helps):
            lines.append(asp.fact("helps", uid, h))
        for n in sorted(u.need):
            lines.append(asp.fact("needs", uid, n))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(T) :- task(T), requires(T, R), not tool_covers(T, R).
tool_covers(T, R) :- helps(U, T), needs(U, R).
valid(T, U) :- task(T), tool(U), helps(U, T), not bad_pair(T, U).
bad_pair(T, U) :- task(T), tool(U), helps(U, T), requires(T, R), not needs(U, R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_pairs() -> list[tuple[str, str]]:
    out = []
    for tid, task in TASKS.items():
        for uid, tool in TOOLS.items():
            if risk_reason(task, tool):
                out.append((tid, uid))
    return out


def explain_rejection(task: Task, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} would not honestly solve {task.keyword}; "
        f"the compromise has to match the danger, not just look helpful.)"
    )


def _spooky_setting_line(world: World) -> str:
    return {
        "the old kitchen": "The old kitchen smelled like onion skins, and the shadows under the shelves looked like they could listen.",
        "the cellar kitchen": "Down in the cellar kitchen, the stone walls held the cold close, and every drip sounded like a footstep.",
        "the attic pantry": "In the attic pantry, moonlight lay across the jars, and the rafters creaked as if someone invisible were pacing above.",
    }[world.setting.place]


def _ghost_presence(world: World) -> str:
    return "a pale little ghost" if world.facts.get("ghost_kind") == "little" else "a thin gray ghost"


def tell(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.name in GIRL_NAMES else "boy",
        meters={"bravery": 0.0},
        memes={"fear": 0.0, "teamwork": 0.0, "hope": 0.0, "inner_monologue": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        meters={"bravery": 0.0},
        memes={"fear": 0.0, "teamwork": 0.0, "hope": 0.0},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label="the ghost",
        meters={"hunger": 1.0, "cold": 1.0},
        memes={"loneliness": 1.0, "softness": 1.0},
    ))
    pot = world.add(Entity(
        id="pot",
        type="pot",
        label="the soup pot",
        phrase="a black soup pot with a dented rim",
    ))
    bouillon = world.add(Entity(
        id="bouillon",
        type="bouillon",
        label="bouillon",
        phrase="a warm bowl of bouillon",
        owner=hero.id,
    ))
    ladle = world.add(Entity(
        id="ladle",
        type="tool",
        label="the ladle",
        phrase=TOOLS["ladle"].phrase,
        owner=hero.id,
    ))
    world.facts.update(hero=hero, parent=parent, ghost=ghost, pot=pot, bouillon=bouillon, ladle=ladle)

    task = TASKS[params.task]
    tool = TOOLS[params.tool]
    world.facts["task"] = task
    world.facts["tool"] = tool
    world.facts["ghost_kind"] = "little"

    # Setup
    world.say(f"{params.name} was a {random.choice(TRAITS)} child who had never liked the dark corners of {world.setting.place}.")
    world.say(f"{params.name} kept one brave thought in {params.name}'s head: {params.name} could still help cook supper, even if the kitchen felt haunted.")
    world.say(f"{_spooky_setting_line(world)}")
    world.say(f"That night, {params.name} and the {params.parent} were making bouillon, because a warm bowl could make the whole house feel gentler.")
    world.para()

    # Turn: ghost appears and the child thinks through fear.
    world.say(f"When the pot began to steam, {_ghost_presence(world)} drifted out from behind the curtain.")
    hero.memes["fear"] += 1.0
    hero.meters["bravery"] += 1.0
    world.say(f"{params.name}'s heart jumped, but a small inner monologue kept going: 'I'm scared, but I can stay and help.'")
    world.say(f"{task.sound.capitalize()}, and the steam curled up like a white ribbon in the dark.")
    world.say(f"The ghost pointed at the pot, because {task.risk} made it look hard for one person to manage alone.")
    world.para()

    # Teamwork resolution
    if not risk_reason(task, tool):
        raise StoryError(explain_rejection(task, tool))

    parent.memes["teamwork"] += 1.0
    hero.memes["teamwork"] += 1.0
    ghost.memes["loneliness"] = 0.0
    ghost.memes["softness"] += 1.0
    world.say(f"{params.name} took a breath, lifted {tool.label if not tool.plural else 'the mitts'}, and said, 'We can do this together.'")
    world.say(f"The {params.parent} steadied the pot, and the ghost, instead of frightening anyone, held the spoon with a careful pale hand.")
    world.say(f"With {tool.phrase}, they kept the pot safe, and the bouillon stayed smooth instead of {task.effect}.")
    world.say(f"At last, the ghost no longer seemed lonely. It hovered beside the table while {params.name} poured a warm bowl of bouillon for everyone.")
    world.say(f"{params.name} was still a little scared, but now the fear had turned small, and bravery had room to grow beside it.")
    world.say(f"The last thing anyone saw was a quiet kitchen, three helpful shadows, and steam rising over the bouillon like a friendly little cloud.")
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    return [
        f'Write a small ghost story for children that includes "{task.keyword}" and ends with a warm supper.',
        f"Tell a spooky but gentle tale where {hero.id} feels afraid in {world.setting.place} and learns bravery through teamwork.",
        f"Write a story about a child whose inner monologue helps {hero.id} stay calm while making bouillon with a ghost.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    task = f["task"]
    tool = f["tool"]
    ghost = f["ghost"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Where did {hero.id} help make bouillon?",
            answer=f"{hero.id} helped make bouillon in {place}, where the shadows felt spooky but the work still had to be done.",
        ),
        QAItem(
            question=f"What made {hero.id} brave enough to stay in the kitchen?",
            answer=f"{hero.id}'s inner monologue helped: {hero.id} thought, 'I'm scared, but I can stay and help,' and that gave {hero.id} enough bravery to keep going.",
        ),
        QAItem(
            question=f"How did the {parent.label if parent.label else parent.type} and {hero.id} work together?",
            answer=f"They used {tool.label} and steadied the pot together, so the bouillon stayed safe and did not {task.effect}.",
        ),
        QAItem(
            question=f"Why did the ghost stop seeming frightening?",
            answer=f"The ghost stopped seeming frightening because {hero.id} and the {parent.type} treated it kindly, and the ghost helped with the cooking instead of hiding alone.",
        ),
        QAItem(
            question=f"What was the ending image of the story?",
            answer=f"The ending showed a quiet kitchen, helpful shadows, and a warm bowl of bouillon rising in steam while everyone felt calmer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bouillon?",
            answer="Bouillon is a clear, savory broth or soup stock, often served warm in a bowl.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel scared, especially if it helps someone or keeps things safe.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and share the job so it becomes easier and safer.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice in your head that helps you think through what you feel and what to do next.",
        ),
        QAItem(
            question="Why can a ghost story still be gentle?",
            answer="A ghost story can be gentle when the ghost is lonely, kind, or needs help instead of wanting to hurt anyone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP parity
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    import asp
    py = set(valid_pairs())
    asp_set = set(asp_valid_pairs())
    if py == asp_set:
        print(f"OK: ASP matches Python gate ({len(py)} pairs).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in asp:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost story world about bouillon, bravery, teamwork, and inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENTS)
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
    if args.task and args.tool:
        task = TASKS[args.task]
        tool = TOOLS[args.tool]
        if not risk_reason(task, tool):
            raise StoryError(explain_rejection(task, tool))
    pairs = valid_pairs()
    filtered = [
        (t, u)
        for t, u in pairs
        if (args.task is None or t == args.task) and (args.tool is None or u == args.tool)
    ]
    if not filtered:
        raise StoryError("(No valid story matches the given options.)")
    task, tool = rng.choice(sorted(filtered))
    place = args.place or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(place=place, task=task, tool=tool, name=name, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    world = tell(world, params)
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


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid task/tool pairs:")
        for t, u in pairs:
            print(f"  {t:10} {u}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="old_kitchen", task="bouillon", tool="ladle", name="Mina", parent="mother"),
            StoryParams(place="cellar_stove", task="noodles", tool="apron", name="Owen", parent="father"),
            StoryParams(place="attic_pantry", task="candlesoup", tool="lantern", name="Ivy", parent="mother"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
