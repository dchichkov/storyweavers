#!/usr/bin/env python3
"""
A standalone storyworld for a small school adventure about curiosity, a chop,
and a happy ending.

Premise:
- A curious child at school discovers something needing a careful chop.
- The child wants to act quickly, but the teacher foreshadows a safer way.
- The adventure ends with a useful, happy result.

The simulated world tracks:
- physical meters: chopped, safe, ready, messy, carried, hidden
- emotional memes: curiosity, worry, pride, relief, teamwork

The prose is driven by world state, not a frozen template.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "teacher", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    safe: bool
    use_verb: str
    result: str


@dataclass
class StoryParams:
    place: str
    task: str
    tool: str
    hero_name: str
    hero_type: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
        other = World(self.place)
        other.entities = dataclasses.replace if False else {}
        import copy as _copy
        other.entities = _copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


PLACES = {
    "school_garden": Place("the school garden", indoors=False, affords={"chop", "collect"}),
    "classroom": Place("the classroom", indoors=True, affords={"chop", "sort"}),
    "cafeteria": Place("the cafeteria", indoors=True, affords={"chop", "cook"}),
}

TASKS = {
    "chop": {
        "verb": "chop the carrots",
        "gerund": "chopping carrots",
        "risk": "messy",
        "at_risk": True,
        "need": "careful",
        "foreshadow": "the teacher's knife was set high on a shelf",
        "result": "tiny carrot pieces",
        "setting_detail": "The table was set with a board, a bowl, and a stack of clean towels.",
    },
    "sort": {
        "verb": "sort the seed packets",
        "gerund": "sorting seed packets",
        "risk": "scattered",
        "at_risk": False,
        "need": "patient",
        "foreshadow": "the packets were tied with a red string so nothing would fly away",
        "result": "neat piles",
        "setting_detail": "Sunlight came through the window and made the paper labels easy to read.",
    },
    "cook": {
        "verb": "cook the soup",
        "gerund": "stirring soup",
        "risk": "hot",
        "at_risk": False,
        "need": "careful",
        "foreshadow": "the pot was still cold, waiting for the right moment",
        "result": "warm soup",
        "setting_detail": "Steam curled in the air like a soft white ribbon.",
    },
}

TOOLS = {
    "safe_knife": Tool("safe_knife", "a small safety knife", True, "carefully chop", "clean, even pieces"),
    "plastic_cutter": Tool("plastic_cutter", "a plastic cutter", True, "press and cut", "neat little pieces"),
    "table_knife": Tool("table_knife", "a dull table knife", False, "hack at", "squashed bits"),
}


GIRL_NAMES = ["Maya", "Nora", "Lina", "Ivy", "Zara", "Ava"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Ben", "Leo", "Max"]


def safe_combo(place: Place, task: str, tool: Tool) -> bool:
    if task not in place.affords:
        return False
    if task == "chop":
        return tool.safe
    if task in {"sort", "cook"}:
        return True
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for task_id in TASKS:
            for tool_id, tool in TOOLS.items():
                if safe_combo(place, task_id, tool):
                    out.append((place_id, task_id, tool_id))
    return out


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    task = TASKS[params.task]
    tool = TOOLS[params.tool]
    world = World(place)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"ready": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "pride": 0.0, "relief": 0.0, "teamwork": 0.0},
    ))
    helper = world.add(Entity(
        id="Teacher",
        kind="character",
        type=params.helper_type,
        label="the teacher",
        meters={"ready": 1.0},
        memes={"foresight": 1.0, "calm": 1.0},
    ))
    item = world.add(Entity(
        id="task_item",
        kind="thing",
        type="food" if params.task in {"chop", "cook"} else "paper",
        label="carrots" if params.task == "chop" else ("seed packets" if params.task == "sort" else "soup"),
        phrase=task["verb"],
        caretaker=helper.id,
        meters={"messy": 0.0, "ready": 0.0, "chopped": 0.0},
    ))
    world.facts.update(hero=hero.id, helper=helper.id, item=item.id, place=place.name, task=params.task, tool=params.tool)
    return world


def intro(world: World) -> None:
    hero = world.get(world.facts["hero"])
    place = world.place
    task = TASKS[world.facts["task"]]
    world.say(
        f"{hero.id} was a curious child who loved adventures at school, "
        f"especially when a new job waited on the table."
    )
    world.say(f"{place.name.capitalize()} had a busy little corner for the class helper team.")
    world.say(task["setting_detail"])


def foreshadow(world: World) -> None:
    helper = world.get(world.facts["helper"])
    task = TASKS[world.facts["task"]]
    hero = world.get(world.facts["hero"])
    tool = TOOLS[world.facts["tool"]]
    hero.memes["curiosity"] += 1.0
    world.say(
        f"{helper.label.capitalize()} smiled and pointed to {task['foreshadow']}. "
        f"That made {hero.id} curious, because something important was clearly about to happen."
    )
    if tool.safe:
        world.say(
            f"{hero.id} noticed {tool.label} beside the board and wondered how such a small tool could do such a big job."
        )
    else:
        world.say(
            f"{hero.id} looked at {tool.label} and felt a tiny twist of worry."
        )


def dilemma(world: World) -> None:
    hero = world.get(world.facts["hero"])
    task = TASKS[world.facts["task"]]
    tool = TOOLS[world.facts["tool"]]
    if task["at_risk"] and tool.safe:
        hero.memes["curiosity"] += 1.0
        hero.memes["worry"] += 0.5
        world.say(
            f"{hero.id} wanted to {task['verb']}, but {hero.pronoun('possessive')} hands had to stay careful."
        )
        world.say(
            f"{tool.label} looked small, yet it was the right tool for a clean chop."
        )
    else:
        world.say(f"{hero.id} took a slow breath and listened closely.")


def action(world: World) -> None:
    hero = world.get(world.facts["hero"])
    helper = world.get(world.facts["helper"])
    task = TASKS[world.facts["task"]]
    tool = TOOLS[world.facts["tool"]]
    item = world.get(world.facts["item"])

    if world.facts["task"] == "chop":
        item.meters["chopped"] += 1.0
        item.meters["ready"] += 1.0
        hero.meters["ready"] += 1.0
        hero.memes["teamwork"] += 1.0
        world.say(
            f"{helper.label} showed {hero.id} how to {tool.use_verb} without rushing."
        )
        world.say(
            f"Together they made {item.label} into {task['result']}."
        )
    elif world.facts["task"] == "sort":
        item.meters["ready"] += 1.0
        hero.memes["teamwork"] += 1.0
        world.say(f"{hero.id} carefully sorted the packets into neat piles.")
    else:
        item.meters["ready"] += 1.0
        hero.memes["teamwork"] += 1.0
        world.say(f"{hero.id} stirred and watched the soup become warm and ready.")


def ending(world: World) -> None:
    hero = world.get(world.facts["hero"])
    helper = world.get(world.facts["helper"])
    item = world.get(world.facts["item"])
    hero.memes["pride"] += 1.0
    hero.memes["relief"] += 1.0
    if hero.meters.get("ready", 0.0) >= THRESHOLD:
        world.say(
            f"{hero.id} grinned when the work was done, because {hero.pronoun('possessive')} careful choice had helped."
        )
    world.say(
        f"By the end, {helper.label} had {item.label} ready, and {hero.id} stood tall beside the finished job."
    )
    world.say(
        f"It felt like a little school adventure with a happy ending, and the foreshadowed worry had turned into proud teamwork."
    )


def tell(world: World) -> World:
    intro(world)
    world.para()
    foreshadow(world)
    dilemma(world)
    world.para()
    action(world)
    ending(world)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.get(world.facts["hero"])
    task = TASKS[world.facts["task"]]
    return [
        "Write a short school adventure story with curiosity, foreshadowing, and a happy ending.",
        f"Tell a child-friendly tale about {hero.id} who wants to {task['verb']} at school.",
        f"Create an adventure story where a teacher hints at trouble before a careful {world.facts['task']} scene.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get(world.facts["hero"])
    helper = world.get(world.facts["helper"])
    task = TASKS[world.facts["task"]]
    tool = TOOLS[world.facts["tool"]]
    return [
        QAItem(
            question=f"Why was {hero.id} curious at school?",
            answer=f"{hero.id} was curious because a new school job was waiting on the table, and {helper.label} had hinted that something important was about to happen."
        ),
        QAItem(
            question=f"What did {helper.label} do to foreshadow the adventure?",
            answer=f"{helper.label} pointed out that {task['foreshadow']}, which told {hero.id} that the job needed care and attention."
        ),
        QAItem(
            question=f"How did the story end after the {task['verb']} part?",
            answer=f"The story ended happily: {hero.id} and {helper.label} finished the job safely, and {tool.label} helped make the result neat and useful."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to ask questions, look closely, and learn what will happen next."
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives a small hint that something important may happen later."
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem gets solved and the characters finish feeling safe, glad, or proud."
        ),
        QAItem(
            question="Why do people use a safe tool for chopping?",
            answer="People use a safe tool for chopping because it helps them cut neatly while keeping fingers and hands safer."
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


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: round(v, 2) for k, v in ent.meters.items() if v}
        memes = {k: round(v, 2) for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if ent.kind == "thing" and ent.caretaker:
            bits.append(f"caretaker={ent.caretaker}")
        out.append(f"{ent.id}: {', '.join(bits) if bits else 'quiet'}")
    return "\n".join(out)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        if task["at_risk"]:
            lines.append(asp.fact("needs_care", tid))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        if tool.safe:
            lines.append(asp.fact("safe_tool", tool_id))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Task, Tool) :- place(Place), task(Task), tool(Tool), affords(Place, Task), safe_combo(Task, Tool).
safe_combo(chop, Tool) :- safe_tool(Tool).
safe_combo(sort, _).
safe_combo(cook, _).
#show valid/3.
"""


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES + "\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python only:", sorted(py - asp_set))
    print("asp only:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="School adventure storyworld with chop, curiosity, foreshadowing, and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["teacher"])
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
    if args.task == "chop" and args.tool and not TOOLS[args.tool].safe:
        raise StoryError("Chopping at school needs a safe tool, not a rough one.")
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.task is None or c[1] == args.task)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not filtered:
        raise StoryError("No valid school adventure matches the given options.")
    place, task, tool = rng.choice(filtered)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or "teacher"
    return StoryParams(place=place, task=task, tool=tool, hero_name=name, hero_type=gender, helper_type=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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


CURATED = [
    StoryParams(place="school_garden", task="chop", tool="safe_knife", hero_name="Maya", hero_type="girl", helper_type="teacher"),
    StoryParams(place="classroom", task="sort", tool="plastic_cutter", hero_name="Noah", hero_type="boy", helper_type="teacher"),
    StoryParams(place="cafeteria", task="cook", tool="safe_knife", hero_name="Lina", hero_type="girl", helper_type="teacher"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(*c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
