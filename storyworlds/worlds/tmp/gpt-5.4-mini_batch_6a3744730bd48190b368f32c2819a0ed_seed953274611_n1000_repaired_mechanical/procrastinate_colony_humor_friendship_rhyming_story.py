#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/procrastinate_colony_humor_friendship_rhyming_story.py
======================================================================================

A standalone storyworld for a tiny rhyming tale about a busy little colony,
a shared chore, a funny delay, and a friendship that turns procrastination into
teamwork.

Seed words:
- procrastinate
- colony

Style:
- Rhyming Story

Features:
- Humor
- Friendship
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class StoryParams:
    name1: str
    name2: str
    leader: str
    helper: str
    task: str
    delay_reason: str
    delay_steps: int
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class ColonySetting:
    place: str
    shelter: str
    shared_goal: str
    sound: str
    rhyme_end: str
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Task:
    id: str
    verb: str
    noun: str
    reward: str
    trouble: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def build_colony_story_setting() -> dict[str, ColonySetting]:
    return {
        "garden_colony": ColonySetting(
            place="a garden colony",
            shelter="a cozy seed shed",
            shared_goal="plant the carrot row",
            sound="a buzz-buzz song",
            rhyme_end="glow",
        ),
        "hill_colony": ColonySetting(
            place="a hilltop colony",
            shelter="a mossy little mound",
            shared_goal="carry the berry crate",
            sound="a chirp-and-chuckle tune",
            rhyme_end="round",
        ),
        "river_colony": ColonySetting(
            place="a riverside colony",
            shelter="a hollow log hall",
            shared_goal="stack the pebble wall",
            sound="a splashy, snappy beat",
            rhyme_end="call",
        ),
    }


SETTINGS = build_colony_story_setting()


def build_tasks() -> dict[str, Task]:
    return {
        "seeds": Task(
            id="seeds",
            verb="sort the seeds",
            noun="seed baskets",
            reward="a tidy row for spring",
            trouble="the bins were upside down and the peas kept popping",
        ),
        "berries": Task(
            id="berries",
            verb="gather the berries",
            noun="berry crates",
            reward="a sweet snack for the colony",
            trouble="the crates were empty and the bears were making jokes",
        ),
        "stones": Task(
            id="stones",
            verb="stack the stones",
            noun="pebble piles",
            reward="a wall that could stand through rain",
            trouble="the pebbles rolled away like they had tiny feet",
        ),
    }


TASKS = build_tasks()

NAMES = ["Mina", "Toby", "Lina", "Pip", "Milo", "Nora", "Ruby", "Otis", "Ivy", "Finn"]
COLONY_NAMES = ["ant", "bee", "mouse", "chipmunk"]
TRAITS = ["funny", "kind", "brave", "patient", "gentle", "cheerful"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting in SETTINGS:
        for task in TASKS:
            combos.append((setting, task))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, T) :- setting(S), task(T).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tiny rhyming colony storyworld about procrastination, humor, and friendship."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              if (args.setting is None or c[0] == args.setting)
              and (args.task is None or c[1] == args.task)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task = rng.choice(sorted(combos))
    leader = rng.choice(NAMES)
    helper = rng.choice([n for n in NAMES if n != leader])
    delay_reason = rng.choice([
        "he kept polishing a spoon",
        "she was telling a bug joke",
        "they were lining up shiny pebbles",
        "he was trying to rhyme the word 'snack'",
    ])
    delay_steps = rng.randint(0, 2)
    return StoryParams(
        name1=leader,
        name2=helper,
        leader=leader,
        helper=helper,
        task=task,
        delay_reason=delay_reason,
        delay_steps=delay_steps,
    )


def propagate(world: World) -> None:
    return


def tell(setting: ColonySetting, task: Task, params: StoryParams) -> World:
    world = World()
    a = world.add(Entity(id=params.leader, kind="character", type="ant", role="leader", traits=["busy", "funny"]))
    b = world.add(Entity(id=params.helper, kind="character", type="ant", role="helper", traits=["kind", "patient"]))
    a.memes["eager"] += 1
    b.memes["friendship"] += 1

    world.say(
        f"In {setting.place}, two little friends began to hum, "
        f"and the whole day felt sunny and fun."
    )
    world.say(
        f"{a.id} said, 'Let's {task.verb} now!' but then {a.id} started to procrastinate, "
        f"because {params.delay_reason}."
    )
    world.say(
        f"{b.id} laughed, not mean, but bright: 'I'll help a bit, and we'll do it right.'"
    )

    world.para()
    if params.delay_steps > 0:
        a.memes["embarrassed"] += 1
        b.memes["humor"] += 1
        world.say(
            f"The colony watched with a giggle and grin as the little delay let the clutter pile in."
        )
    world.say(
        f"At last they worked together side by side, and the task turned smooth with friendship as guide."
    )
    world.say(
        f"They finished {task.verb} in {setting.shelter}, and the colony cheered, 'What a wonderful day!'"
    )
    world.say(
        f"Their shared win was tiny, but warm and true: no job was too big when the friends worked through."
    )

    world.facts.update(
        setting=setting,
        task=task,
        leader=a,
        helper=b,
        outcome="done",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a rhyming story about a {f['setting'].place} where two friends must {f['task'].verb}, but one procrastinates and they solve it together.",
        f"Tell a humorous friendship story that includes the words procrastinate and colony, and ends with a shared job getting done.",
        f"Write a child-friendly rhyming tale about a colony of little workers, a funny delay, and a kind helper who turns waiting into teamwork.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    task: Task = f["task"]
    setting: ColonySetting = f["setting"]
    leader: Entity = f["leader"]
    helper: Entity = f["helper"]
    return [
        QAItem(
            question="Who was the story about?",
            answer=f"It was about {leader.id} and {helper.id}, two friends in {setting.place}. They worked in a little colony and tried to help each other.",
        ),
        QAItem(
            question="Why did one friend procrastinate?",
            answer=f"{leader.id} procrastinated because {leader.id} got distracted by {f['leader'].id.lower() == f['helper'].id.lower() and 'something silly' or f['setting'].sound}. More importantly, the delay was funny, not harmful, and {helper.id} stayed kind.",
        ),
        QAItem(
            question="How did the problem get solved?",
            answer=f"They did the job together after the delay. {helper.id} kept things cheerful, and then {leader.id} joined in so they could {task.verb} and finish the day well.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"At the end, the colony had a finished job and the friends felt closer. The story turns procrastination into teamwork, so the ending is warm and happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a colony?",
            answer="A colony is a group of small creatures that live and work together in one place. They share jobs, shelter, and everyday chores.",
        ),
        QAItem(
            question="What does procrastinate mean?",
            answer="To procrastinate means to delay doing something you should do now. People often procrastinate when they get distracted by something easier or sillier.",
        ),
        QAItem(
            question="Why is friendship helpful?",
            answer="Friendship is helpful because friends encourage each other and share the work. When one friend gets stuck, another can help them keep going.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={dict(meters)} memes={dict(memes)} role={e.role}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.task not in TASKS or params.name1 == params.name2:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS["garden_colony"], TASKS[params.task], params)
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


def explain_rejection() -> str:
    return "(No story: this tiny colony world only supports cooperative chores that can be finished in a short rhyming tale.)"


def asp_verify() -> int:
    import asp
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos().")
        return 1
    try:
        _ = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and story-generation smoke test passed.")
    return 0


CURATED = [
    StoryParams(name1="Mina", name2="Pip", leader="Mina", helper="Pip", task="seeds", delay_reason="she was making a silly seed hat", delay_steps=1),
    StoryParams(name1="Toby", name2="Nora", leader="Toby", helper="Nora", task="berries", delay_reason="he kept trying to rhyme 'berry' with 'merry'", delay_steps=2),
    StoryParams(name1="Lina", name2="Otis", leader="Lina", helper="Otis", task="stones", delay_reason="they were laughing at a pebble that looked like a bean", delay_steps=0),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, t in combos:
            print(f"  {s:15} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
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
