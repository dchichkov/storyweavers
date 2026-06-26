#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/garlic_anecdote_machete_moral_value_friendship_animal.py
================================================================================================

A standalone story world for a small Animal Story domain with garlic, an
anecdote, a machete, and a friendship-centered moral value.

Premise:
- Animal friends visit a little garden or woodland patch.
- They want garlic for dinner or for a helper's recipe.
- Something tangled or overgrown blocks the garlic.
- A grown helper has a machete as a tool for clearing vines and reeds, never as a threat.
- One animal remembers an anecdote about a past mistake and uses it to teach patience,
  honesty, and friendship.
- The ending proves the garlic was gathered safely and the friendship grew warmer.

This world is intentionally small, state-driven, and child-facing.
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

MORAL_VALUES = {"kindness", "honesty", "patience", "sharing", "helpfulness"}
SCENES = {"garden", "woodland", "farmyard"}
ANIMALS = {
    "rabbit": {"plush": "soft gray rabbit", "gender": "neutral"},
    "fox": {"plush": "small red fox", "gender": "neutral"},
    "badger": {"plush": "striped badger", "gender": "neutral"},
    "mouse": {"plush": "tiny brown mouse", "gender": "neutral"},
    "squirrel": {"plush": "bushy-tailed squirrel", "gender": "neutral"},
    "hedgehog": {"plush": "round hedgehog", "gender": "neutral"},
}

# ---------------------------------------------------------------------------
# Shared model
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
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "trust": 0.0, "frustration": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    supports: set[str] = field(default_factory=set)
    detail: str = ""


@dataclass
class Task:
    id: str
    want: str
    verb: str
    rush: str
    mess: str
    risk_region: str
    moral_value: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    kind: str = "tool"
    plural: bool = False


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    zone: set[str] = field(default_factory=set)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "garden": Place("the garden", {"clear_weeds", "fetch_garlic", "share_anecdote"},
                    "The beds were neat, but one corner was choked with tangled weeds."),
    "woodland": Place("the woodland edge", {"clear_weeds", "fetch_garlic", "share_anecdote"},
                      "The path there was soft, and brambles leaned over the garlic patch."),
    "farmyard": Place("the farmyard garden", {"clear_weeds", "fetch_garlic", "share_anecdote"},
                      "The garlic row was close to the fence, where vines liked to tangle."),
}

TASKS = {
    "clear_weeds": Task(
        id="clear_weeds",
        want="clear the tangled weeds",
        verb="clear the tangled weeds",
        rush="rush into the brambles",
        mess="scratched",
        risk_region="paws",
        moral_value="patience",
        keyword="garlic",
        tags={"garlic", "moral_value"},
    ),
    "fetch_garlic": Task(
        id="fetch_garlic",
        want="bring the garlic home",
        verb="pick the garlic bulbs",
        rush="pull at the stems too hard",
        mess="dirty",
        risk_region="paws",
        moral_value="sharing",
        keyword="garlic",
        tags={"garlic", "friendship"},
    ),
    "share_anecdote": Task(
        id="share_anecdote",
        want="tell an anecdote about a mistake",
        verb="tell the little anecdote",
        rush="talk over the others",
        mess="none",
        risk_region="voice",
        moral_value="honesty",
        keyword="anecdote",
        tags={"anecdote", "friendship", "moral_value"},
    ),
}

TOOLS = [
    Tool(
        id="machete",
        label="machete",
        phrase="a small machete for cutting vines",
        covers={"paws"},
        guards={"scratched"},
        prep="use the machete carefully to cut the tangled vines first",
        tail="used the machete to trim the brambles and make a safe path",
    ),
    Tool(
        id="basket",
        label="basket",
        phrase="a woven basket",
        covers=set(),
        guards={"dirty"},
        prep="carry a woven basket to hold the garlic",
        tail="had the basket ready for the garlic bulbs",
        plural=False,
    ),
    Tool(
        id="gloves",
        label="gloves",
        phrase="a pair of garden gloves",
        covers={"paws"},
        guards={"scratched", "dirty"},
        prep="put on garden gloves before reaching in",
        tail="wore the gloves and kept their paws safe",
        plural=True,
    ),
]

CURATED = [
    ("garden", "clear_weeds"),
    ("woodland", "fetch_garlic"),
    ("farmyard", "share_anecdote"),
]

GIRLISH_NAMES = ["Mina", "Lulu", "Pip", "Nori", "Tess", "Bea", "Dora"]
ANIMAL_NAMES = ["Bramble", "Hazel", "Fern", "Moss", "Clover", "Pip", "Wren"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A task is at risk when its mess can reach the same region the hero uses.
task_at_risk(T) :- task(T), risk_region(T, R), zone(R).

% A tool is a reasonable help only if it protects the risky region and guards
% the mess created by the task.
compatible_tool(Tool, T) :- task_at_risk(T), tool(Tool),
    risk_region(T, R), covers(Tool, R),
    mess_of(T, M), guards(Tool, M).

has_fix(T) :- compatible_tool(_, T).

valid_story(P, T) :- place(P), supports(P, T), has_fix(T).

featured_value(T, V) :- task(T), moral_value(T, V).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(p.supports):
            lines.append(asp.fact("supports", pid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("mess_of", tid, t.mess))
        lines.append(asp.fact("risk_region", tid, t.risk_region))
        lines.append(asp.fact("moral_value", tid, t.moral_value))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for c in sorted(tool.covers):
            lines.append(asp.fact("covers", tool.id, c))
        for g in sorted(tool.guards):
            lines.append(asp.fact("guards", tool.id, g))
    for z in sorted({"paws", "voice"}):
        lines.append(asp.fact("zone", z))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------
def task_at_risk(task: Task) -> bool:
    return task.risk_region == "paws"

def select_tool(task: Task) -> Optional[Tool]:
    for tool in TOOLS:
        if task.mess in tool.guards and task.risk_region in tool.covers:
            return tool
    return None

def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for task_id in place.supports:
            task = TASKS[task_id]
            if task_at_risk(task) and select_tool(task):
                out.append((place_id, task_id))
    return sorted(out)

def explain_rejection(task: Task) -> str:
    return (
        f"(No story: the task '{task.id}' has no safe tool match in this world. "
        f"The friendship moral needs a real, reasonable fix, not a forced one.)"
    )


# ---------------------------------------------------------------------------
# Story writing
# ---------------------------------------------------------------------------
def build_world(place_id: str, task_id: str, hero_name: str, friend_name: str) -> World:
    place = PLACES[place_id]
    task = TASKS[task_id]
    world = World(place)

    hero = world.add(Entity(id=hero_name, kind="character", type="animal"))
    friend = world.add(Entity(id=friend_name, kind="character", type="animal"))
    elder = world.add(Entity(id="Elder", kind="character", type="animal", label="old tortoise"))

    garlic = world.add(Entity(
        id="garlic", type="garlic", label="garlic bulbs", phrase="fresh garlic bulbs",
        caretaker=friend.id, owner=friend.id, plural=True
    ))
    anecdote = world.add(Entity(
        id="anecdote", type="memory", label="anecdote", phrase="a small anecdote",
        owner=elder.id
    ))

    tool = select_tool(task)
    if tool is None:
        raise StoryError(explain_rejection(task))
    machete = world.add(Entity(
        id=tool.id, type="tool", label=tool.label, phrase=tool.phrase,
        owner=elder.id, caretaker=elder.id, protective=True, covers=set(tool.covers),
        plural=tool.plural
    ))
    machete.worn_by = elder.id

    world.facts.update(
        hero=hero, friend=friend, elder=elder, garlic=garlic, anecdote=anecdote,
        tool=machete, task=task, place=place, place_id=place_id, task_id=task_id
    )

    # Act 1
    world.say(f"At {place.name}, {hero.id} and {friend.id} were friends who liked working side by side.")
    world.say(f"They had come for {task.want}, because the sweet smell of garlic made dinner feel special.")
    world.say(f"An old tortoise named {elder.id} was nearby, and {elder.label} carried {tool.phrase}.")

    # Act 2
    world.para()
    world.say(place.detail)
    world.say(f"{hero.id} wanted to {task.verb}, but the weeds were thick and scratchy.")
    world.say(f"{friend.id} warned that if they {task.rush}, their paws could get {task.mess}.")
    world.say(f"Then {elder.id} told an anecdote: once, {elder.label} had rushed a job, and the shortcut had only made more work.")
    world.say(f"{elder.id} smiled and said that friendship is stronger when everyone is careful and honest.")

    # Act 3
    world.para()
    tool_phrase = tool.prep
    world.say(f"So they listened. First, {elder.id} helped by choosing to {tool_phrase}.")
    world.zone = {task.risk_region}
    if task.mess in {"scratched", "dirty"}:
        world.say(f"That kept the sharp stems from hurting little paws.")
    world.say(f"With the path open, {hero.id} and {friend.id} picked the garlic together and put it safely in the basket.")
    world.say(f"{friend.id} thanked {elder.id} for the anecdote, because it had helped them choose patience over hurry.")
    world.say(f"In the end, the friends went home with garlic for supper, and their friendship felt warmer than before.")

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task: Task = f["task"]
    place: Place = f["place"]
    return [
        f'Write a gentle Animal Story about friends at {place.name} with the word "{task.keyword}".',
        f'Tell a short story where animal friends learn from an anecdote and use a machete safely to solve a garden problem.',
        f'Write a child-friendly friendship story in which patience helps animal friends get garlic without getting hurt.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, elder = f["hero"], f["friend"], f["elder"]
    garlic, anecdote, tool = f["garlic"], f["anecdote"], f["tool"]
    task: Task = f["task"]
    place: Place = f["place"]

    return [
        QAItem(
            question=f"Who went to {place.name} for {task.want}?",
            answer=f"{hero.id} and {friend.id} went there together, so they could work as friends and bring home the garlic.",
        ),
        QAItem(
            question=f"What did the old tortoise share that helped the friends slow down?",
            answer=f"{elder.id} shared an anecdote, and it reminded them that rushing can make a job harder instead of easier.",
        ),
        QAItem(
            question=f"How did {tool.label} help the friends?",
            answer=f"It helped cut the tangled weeds carefully so the garlic path was safe for their paws.",
        ),
        QAItem(
            question=f"What did the friends carry home at the end?",
            answer=f"They carried home garlic for supper, and they also carried a better feeling of friendship.",
        ),
        QAItem(
            question=f"What moral value did the story show?",
            answer=f"The story showed patience and helpful friendship, because the animals listened, waited, and worked together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is garlic?",
            answer="Garlic is a strong-smelling plant bulb that people and animals often use for cooking.",
        ),
        QAItem(
            question="What is an anecdote?",
            answer="An anecdote is a short little story, often about something that happened before.",
        ),
        QAItem(
            question="What is a machete?",
            answer="A machete is a long cutting tool people use carefully to trim thick plants and vines.",
        ),
        QAItem(
            question="Why is friendship important?",
            answer="Friendship is important because friends help each other, listen, and make hard jobs feel easier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    task: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world with garlic, an anecdote, and a machete.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    if args.place and args.task and (args.place, args.task) not in combos:
        raise StoryError("(No valid story matches those explicit options.)")
    filtered = [c for c in combos if (args.place is None or c[0] == args.place) and (args.task is None or c[1] == args.task)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, task = rng.choice(filtered)
    hero_name = args.name or rng.choice(ANIMAL_NAMES)
    friend_name = args.friend or rng.choice([n for n in ANIMAL_NAMES if n != hero_name])
    return StoryParams(place=place, task=task, hero_name=hero_name, friend_name=friend_name)

def generate(params: StoryParams) -> StorySample:
    world = build_world(params.place, params.task, params.hero_name, params.friend_name)
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

def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"{e.id}: {e.type} " + " ".join(bits))
    return "\n".join(lines)

def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - clingo))
    print("asp only:", sorted(clingo - py))
    return 1

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, task in CURATED:
            params = StoryParams(place=place, task=task, hero_name=ANIMAL_NAMES[0], friend_name=ANIMAL_NAMES[1])
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
