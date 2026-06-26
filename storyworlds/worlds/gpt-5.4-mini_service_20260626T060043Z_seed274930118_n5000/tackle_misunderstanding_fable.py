#!/usr/bin/env python3
"""
A small fable-style storyworld about a misunderstanding around the word
"tackle": one animal means "take on a hard job," while another first thinks it
means "jump on and wrestle." The story turns on a gentle misunderstanding, then
a clear explanation, then a shared fix.

The world model tracks both physical meters and emotional memes, and the prose
is driven by those state changes.
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
    kind: str = "character"
    type: str = "animal"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["dust", "strain", "broken"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "worry", "hurt", "pride", "warmth", "understanding"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "rabbit", "squirrel", "badger", "mouse", "hedgehog"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    detail: str


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    keyword: str
    hard: str
    physical: str
    social_meaning: str


@dataclass
class World:
    place: Place
    hero: Entity
    friend: Entity
    task: Task
    tool: Entity
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        return copy.deepcopy(self)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "lane": Place(name="the lane", detail="The lane was narrow and dusty, with a little gate at the end."),
    "orchard": Place(name="the orchard", detail="The orchard was quiet, with branches bowing over soft grass."),
    "yard": Place(name="the yard", detail="The yard was bright, with one wobbly fence that needed help."),
}

TASKS = {
    "fence": Task(
        id="fence",
        verb="tackle the fence",
        gerund="tackling the fence",
        keyword="tackle",
        hard="hard and wobbly",
        physical="dusty",
        social_meaning="fix it carefully",
    ),
    "weeds": Task(
        id="weeds",
        verb="tackle the weeds",
        gerund="tackling the weeds",
        keyword="tackle",
        hard="stubborn and prickly",
        physical="scratchy",
        social_meaning="pull them out",
    ),
    "rope": Task(
        id="rope",
        verb="tackle the rope knot",
        gerund="tackling the rope knot",
        keyword="tackle",
        hard="tight and twisted",
        physical="tight",
        social_meaning="loosen it slowly",
    ),
}

TOOLS = {
    "hammer": Entity(id="hammer", kind="thing", type="tool", label="hammer", phrase="a small hammer"),
    "gloves": Entity(id="gloves", kind="thing", type="tool", label="gloves", phrase="a pair of garden gloves"),
    "string": Entity(id="string", kind="thing", type="tool", label="string", phrase="a loop of string"),
}

HEROES = [
    ("fox", "Fox"),
    ("rabbit", "Rabbit"),
    ("squirrel", "Squirrel"),
    ("badger", "Badger"),
]

FRIENDS = [
    ("fox", "Fox"),
    ("rabbit", "Rabbit"),
    ("squirrel", "Squirrel"),
    ("badger", "Badger"),
]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    task: str
    hero_kind: str
    friend_kind: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for task in TASKS:
            for hero_kind, _ in HEROES:
                for friend_kind, _ in FRIENDS:
                    if hero_kind != friend_kind:
                        combos.append((place, task, hero_kind, friend_kind))
    return combos


def explain_rejection() -> str:
    return "(No story: I need two different animal friends so one can misunderstand the word 'tackle' and the other can explain it.)"


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_names(hero_kind: str, friend_kind: str, rng: random.Random) -> tuple[str, str]:
    hero_name = rng.choice({
        "fox": ["Fenn", "Rusty", "Pip"],
        "rabbit": ["Mina", "Lulu", "Nip"],
        "squirrel": ["Tilly", "Nim", "Poppy"],
        "badger": ["Bruno", "Tess", "Moss"],
    }[hero_kind])
    friend_name = rng.choice({
        "fox": ["Fenn", "Rusty", "Pip"],
        "rabbit": ["Mina", "Lulu", "Nip"],
        "squirrel": ["Tilly", "Nim", "Poppy"],
        "badger": ["Bruno", "Tess", "Moss"],
    }[friend_kind])
    if hero_name == friend_name:
        friend_name += "a"
    return hero_name, friend_name


def set_task_tool(task: Task) -> Entity:
    if task.id == "fence":
        return Entity(id="hammer", kind="thing", type="tool", label="hammer", phrase="a small hammer")
    if task.id == "weeds":
        return Entity(id="gloves", kind="thing", type="tool", label="gloves", phrase="a pair of garden gloves")
    return Entity(id="string", kind="thing", type="tool", label="string", phrase="a loop of string")


def predict_misunderstanding(world: World) -> bool:
    # If the friend hears "tackle" before the explanation, misunderstanding happens.
    return True


def tell(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    place = PLACES[params.place]
    task = TASKS[params.task]
    hero_kind = params.hero_kind
    friend_kind = params.friend_kind
    hero_name, friend_name = build_names(hero_kind, friend_kind, rng)

    hero = Entity(id=hero_name, kind="character", type=hero_kind, label=hero_name)
    friend = Entity(id=friend_name, kind="character", type=friend_kind, label=friend_name)
    tool = set_task_tool(task)
    world = World(place=place, hero=hero, friend=friend, task=task, tool=tool)

    # Act 1: setup
    world.say(f"{hero.id} lived near {place.name}. {place.detail}")
    world.say(f"{hero.id} was a careful little {hero.type} who liked to {task.verb} when there was a hard job to do.")
    world.say(f"One morning, {hero.id} picked up {tool.phrase} and said, \"I will {task.verb} before dinner.\"")
    world.say(f"{friend.id} was nearby, and {friend.id} loved to listen to every word.")

    # misunderstanding
    world.para()
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(f"{friend.id} heard the word \"{task.keyword}\" and blinked.")
    world.say(f"{friend.id} thought it meant to leap on something, not to {task.social_meaning}.")
    friend.memes["worry"] += 1
    friend.memes["hurt"] += 1
    world.say(f"So {friend.id} frowned and said, \"Don't hurt the fence!\"")
    hero.memes["worry"] += 1

    # reaction
    world.say(f"{hero.id} stopped at once. {hero.id} had only meant to {task.social_meaning}.")
    hero.memes["understanding"] += 0.5
    hero.memes["pride"] += 0.2

    # explanation and resolution
    world.para()
    world.say(f"{hero.id} gently explained, \"I mean {task.social_meaning}, not bumping into it.\"")
    friend.memes["understanding"] += 1
    friend.memes["worry"] = 0
    world.say(f"{friend.id}'s ears warmed. \"Oh! I misunderstood,\" {friend.id} said.")
    world.say(f"Then {friend.id} helped by holding the {tool.label if tool.label != 'hammer' else 'board'} steady while {hero.id} worked.")
    hero.memes["warmth"] += 1
    friend.memes["warmth"] += 1

    # ending image
    world.para()
    world.facts.update(hero=hero, friend=friend, task=task, place=place, tool=tool, resolved=True)
    world.say(f"Together they finished in good time.")
    world.say(f"The {task.id} was no longer {task.hard}; it was simply done.")
    world.say(f"{hero.id} smiled, and {friend.id} smiled back, because a clear word had turned trouble into teamwork.")
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for young children that uses the word "{f["task"].keyword}" in two different ways and shows a misunderstanding being cleared up.',
        f"Tell a gentle story about {f['hero'].id} and {f['friend'].id} where one thinks a hard job is a wrestling move, then they explain the mix-up.",
        f"Write a simple animal story about {f['task'].verb} at {f['place'].name} with a clear ending image of teamwork.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    task: Task = f["task"]
    place: Place = f["place"]
    tool: Entity = f["tool"]
    return [
        QAItem(
            question=f"Why did {friend.id} get worried when {hero.id} said they would {task.verb}?",
            answer=f"{friend.id} misunderstood the word \"{task.keyword}\" and thought {hero.id} meant to tackle by jumping on something. In truth, {hero.id} only meant to {task.social_meaning} at {place.name}.",
        ),
        QAItem(
            question=f"What did {hero.id} pick up before trying to {task.verb}?",
            answer=f"{hero.id} picked up {tool.phrase} before working on the job.",
        ),
        QAItem(
            question=f"What changed after the animals talked clearly about the word \"{task.keyword}\"?",
            answer=f"After they explained the word, {friend.id} stopped worrying and helped {hero.id}. The misunderstanding turned into teamwork.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to tackle a hard job?",
            answer="To tackle a hard job means to begin it bravely and work on it carefully, even if it looks difficult.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks a word or action means one thing, but it really means something else.",
        ),
        QAItem(
            question="Why is it good to ask for an explanation?",
            answer="It is good to ask for an explanation because clear words can stop worry and help everyone work together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    hero = world.hero
    friend = world.friend
    return "\n".join(
        [
            "--- world trace ---",
            f"place={world.place.name}",
            f"task={world.task.id}",
            f"hero.memes={hero.memes}",
            f"friend.memes={friend.memes}",
            f"tool={world.tool.label}",
        ]
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A task is valid when it has a place, and the story always uses two different animals.
valid(Place, Task, Hero, Friend) :- place(Place), task(Task), animal(Hero), animal(Friend), Hero != Friend.

% The misunderstanding is the heart of this world.
has_misunderstanding(Task) :- task(Task).

#show valid/4.
#show has_misunderstanding/1.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TASKS:
        lines.append(asp.fact("task", t))
    for a, _ in HEROES:
        lines.append(asp.fact("animal", a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid())
    if py == clingo:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - clingo:
        print("  only in python:", sorted(py - clingo))
    if clingo - py:
        print("  only in asp:", sorted(clingo - py))
    return 1


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable storyworld about a misunderstanding around the word 'tackle'.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--task", choices=sorted(TASKS))
    ap.add_argument("--hero-kind", choices=sorted({k for k, _ in HEROES}))
    ap.add_argument("--friend-kind", choices=sorted({k for k, _ in FRIENDS}))
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.task:
        combos = [c for c in combos if c[1] == args.task]
    if args.hero_kind:
        combos = [c for c in combos if c[2] == args.hero_kind]
    if args.friend_kind:
        combos = [c for c in combos if c[3] == args.friend_kind]
    if not combos:
        raise StoryError(explain_rejection())
    place, task, hero_kind, friend_kind = rng.choice(combos)
    return StoryParams(place=place, task=task, hero_kind=hero_kind, friend_kind=friend_kind)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show valid/4.\n#show has_misunderstanding/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/4.\n#show has_misunderstanding/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [
            generate(StoryParams(place=p, task=t, hero_kind=h, friend_kind=f, seed=base_seed))
            for p, t, h, f in sorted(valid_combos())
        ]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
