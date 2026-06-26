#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/almond_format_commando_flashback_bravery_lesson_learned.py
========================================================================================================================

A small, heartwarming storyworld about a child, a careful format, and a brave
little chance to try again.

Seed-inspired premise:
- almond
- format
- commando
- Flashback
- Bravery
- Lesson Learned

The world models a child who wants to help prepare a simple almond treat in a
neat format. A small mistake threatens the plan, a flashback reminds the child
of an earlier wobble, and a gentle act of bravery leads to a better ending.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
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
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    risk: str
    zone: set[str]
    flashback: str
    keyword: str


@dataclass
class Supply:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Helper:
    id: str
    label: str
    action: str
    helps: set[str]
    covers: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.setting)
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _mem(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _add_meter(e: Entity, key: str, amount: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amount


def _add_mem(e: Entity, key: str, amount: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amount


def task_at_risk(task: Task, supply: Supply) -> bool:
    return supply.region in task.zone


def select_helper(task: Task, supply: Supply) -> Optional[Helper]:
    for h in HELPERS:
        if task.id in h.helps and supply.region in h.covers:
            return h
    return None


def _rule_spill(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    snack = world.get("almonds")
    tray = world.get("tray")
    if _meter(child, "clumsy") < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _add_meter(snack, "scattered", 1.0)
    _add_meter(tray, "messy", 1.0)
    out.append("A few almonds skittered across the tray.")
    return out


def _rule_worry(world: World) -> list[str]:
    out: list[str] = []
    parent = world.get("parent")
    snack = world.get("almonds")
    if _meter(snack, "scattered") < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _add_mem(parent, "worry", 1.0)
    out.append("That made the grown-up look worried for a moment.")
    return out


def _rule_brave(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if _mem(child, "bravery") < THRESHOLD:
        return out
    sig = ("brave",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("The child took a brave breath and kept going.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_rule_spill, _rule_worry, _rule_brave):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def flashback_line(task: Task) -> str:
    return task.flashback


def tell(setting: Setting, task: Task, supply_cfg: Supply, helper: Helper,
         hero_name: str = "Mila", hero_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=hero_type,
        label=hero_name,
        meters={"clumsy": 1.0},
        memes={"want_help": 1.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the grown-up",
    ))
    almonds = world.add(Entity(
        id="almonds",
        type="almonds",
        label="almonds",
        phrase="a small bowl of almonds",
        owner=child.id,
        caretaker=parent.id,
        plural=True,
    ))
    format_card = world.add(Entity(
        id="format_card",
        type="card",
        label="format card",
        phrase="a neat format card with big boxes",
        owner=child.id,
        caretaker=parent.id,
    ))
    tray = world.add(Entity(
        id="tray",
        type="tray",
        label="tray",
        phrase="a shallow tray",
        owner=parent.id,
        caretaker=parent.id,
    ))
    commando = world.add(Entity(
        id="commando",
        type="toy",
        label="commando",
        phrase="a tiny toy commando",
        owner=child.id,
    ))
    world.facts.update(child=child, parent=parent, almonds=almonds, format_card=format_card,
                       tray=tray, commando=commando, task=task, helper=helper,
                       setting=setting, supply=supply_cfg)

    world.say(f"{hero_name} was a {hero_type} who loved to help in {setting.place}.")
    world.say(
        f"{hero_name} liked the {task.keyword} task because it made {task.gerund} feel calm and tidy."
    )
    world.say(
        f"On the table sat {supply_cfg.phrase}, a {format_card.label} for the snack, and a tiny {commando.label}."
    )

    world.para()
    world.say(f"One afternoon, {hero_name} wanted to {task.verb} in a perfect {format_card.label} format.")
    world.say("But the bowl wobbled, and a few almonds slipped out of line.")
    propagate(world)

    world.para()
    world.say(
        f"{hero_name} paused for a flashback: {flashback_line(task)}"
    )
    child.memes["flashback"] = 1.0
    child.memes["bravery"] = 1.0
    world.say(
        f"That old memory made {hero_name} nervous, but {commando.label} sat nearby like a tiny brave helper."
    )
    propagate(world)

    world.para()
    helper_thing = world.add(Entity(
        id=helper.id,
        type="helper",
        label=helper.label,
        phrase=helper.label,
        owner=parent.id,
        plural=False,
    ))
    world.say(
        f"The grown-up smiled and said, '{helper.action}, and we can finish together.'"
    )
    world.say(
        f"{hero_name} took a brave breath, fixed the rows, and followed the {format_card.label} carefully."
    )
    _add_mem(child, "bravery", 1.0)
    _add_mem(child, "pride", 1.0)
    _add_mem(parent, "warmth", 1.0)
    world.say(
        f"At last, the almonds stayed neat, the tray was tidy again, and {hero_name} felt taller inside."
    )
    world.say("Lesson learned: a gentle plan and a brave try can turn a messy moment into a kind one.")
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"arrange", "write"}),
    "bakery": Setting(place="the bakery corner", affords={"arrange", "write"}),
    "community_room": Setting(place="the community room", affords={"arrange", "write"}),
}

TASKS = {
    "arrange": Task(
        id="arrange",
        verb="arrange the almonds",
        gerund="arranging the almonds",
        risk="scattering",
        zone={"table"},
        flashback="Last week, the child tried to sort stickers too quickly and the whole page slid apart.",
        keyword="almond",
    ),
    "write": Task(
        id="write",
        verb="write the labels",
        gerund="writing the labels",
        risk="smudging",
        zone={"paper"},
        flashback="Yesterday, the child wrote a note in a hurry and had to start over with a fresh card.",
        keyword="format",
    ),
}

SUPPLIES = {
    "almonds": Supply(
        id="almonds",
        label="almonds",
        phrase="a small bowl of almonds",
        region="table",
        plural=True,
    ),
    "labels": Supply(
        id="labels",
        label="labels",
        phrase="a sheet of labels",
        region="paper",
        plural=True,
    ),
}

HELPERS = [
    Helper(
        id="silicone_mat",
        label="a silicone mat",
        action="Let's use the silicone mat",
        helps={"arrange"},
        covers={"table"},
    ),
    Helper(
        id="blue_pencil",
        label="a blue pencil",
        action="Let's trace the letters slowly",
        helps={"write"},
        covers={"paper"},
    ),
]

GIRL_NAMES = ["Mila", "Nia", "Sophie", "Tara", "Leah", "Iris"]
BOY_NAMES = ["Evan", "Noah", "Arlo", "Finn", "Owen", "Theo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            task = TASKS[task_id]
            for supply_id, supply in SUPPLIES.items():
                if task_at_risk(task, supply) and select_helper(task, supply):
                    combos.append((place, task_id, supply_id))
    return combos


@dataclass
class StoryParams:
    place: str
    task: str
    supply: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld about almond work, a careful format, and bravery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--supply", choices=SUPPLIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.task and args.supply:
        task, supply = TASKS[args.task], SUPPLIES[args.supply]
        if not (task_at_risk(task, supply) and select_helper(task, supply)):
            raise StoryError("That task and supply do not make a sensible story together.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.supply is None or c[2] == args.supply)]
    if not combos:
        raise StoryError("No valid combination matches those choices.")
    place, task, supply = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, task=task, supply=supply, name=name, gender=gender, parent=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    task = f["task"]
    supply = f["supply"]
    return [
        f"Write a heartwarming story about a child named {child.label} who wants to {task.verb} with {supply.phrase}.",
        f"Tell a gentle tale where {child.label} uses a careful format, remembers a flashback, and shows bravery.",
        f"Write a short children's story that includes almond, format, and commando, and ends with a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, task, supply = f["child"], f["parent"], f["task"], f["supply"]
    return [
        QAItem(
            question=f"What did {child.label} want to do in {world.setting.place}?",
            answer=f"{child.label} wanted to {task.verb} in a careful way."
        ),
        QAItem(
            question="What made the story need a better plan?",
            answer=f"A few almonds slipped out of line, so the grown-up and the child needed a steadier format."
        ),
        QAItem(
            question="What old memory came back before the brave try?",
            answer=task.flashback
        ),
        QAItem(
            question="What lesson did the child learn?",
            answer="The child learned that a gentle plan and a brave try can fix a messy moment."
        ),
        QAItem(
            question=f"Who helped the child finish?",
            answer=f"{parent.label.capitalize()} helped by staying calm and offering a kind reminder."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are almonds?",
            answer="Almonds are small nuts that people often eat as snacks or use in baking."
        ),
        QAItem(
            question="What does format mean?",
            answer="A format is a planned way to arrange something so it looks neat and is easy to follow."
        ),
        QAItem(
            question="What is a commando?",
            answer="A commando can mean a brave soldier, but in a story it can also be the name of a tiny toy."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
task_at_risk(T,S) :- task(T), supply(S), zone(T,Z), region(S,R), Z = R.
has_helper(T,S) :- task_at_risk(T,S), helper(H), helps(H,T), covers(H,R), region(S,R).
valid(Place,T,S) :- affords(Place,T), task_at_risk(T,S), has_helper(T,S).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for r in sorted(t.zone):
            lines.append(asp.fact("zone", tid, r))
    for sid, s in SUPPLIES.items():
        lines.append(asp.fact("supply", sid))
        lines.append(asp.fact("region", sid, s.region))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
        for t in sorted(h.helps):
            lines.append(asp.fact("helps", h.id, t))
        for r in sorted(h.covers):
            lines.append(asp.fact("covers", h.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def _story_to_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    task = TASKS[params.task]
    supply = SUPPLIES[params.supply]
    helper = select_helper(task, supply)
    if helper is None:
        raise StoryError("No helper fits this story.")
    return tell(setting, task, supply, helper, params.name, params.gender, params.parent)


def generate(params: StoryParams) -> StorySample:
    world = _story_to_world(params)
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
    StoryParams(place="kitchen", task="arrange", supply="almonds", name="Mila", gender="girl", parent="mother"),
    StoryParams(place="community_room", task="write", supply="labels", name="Evan", gender="boy", parent="father"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
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
