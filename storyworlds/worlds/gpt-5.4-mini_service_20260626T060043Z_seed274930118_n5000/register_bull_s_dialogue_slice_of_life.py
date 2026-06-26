#!/usr/bin/env python3
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad", "bull"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)


@dataclass
class SceneItem:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    risk: str
    mess: str
    zone: set[str]
    keyword: str
    tension: str
    fix_label: str
    fix_phrase: str
    fix_covers: set[str]
    fix_guards: set[str]


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.owner == actor.id and e.kind == "thing"]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(
            item.label in {"apron", "raincoat", "gloves"} and item.meters.get(f"covers_{region}", 0) >= 1
            for item in self.worn_items(actor)
        )


@dataclass
class StoryParams:
    place: str
    task: str
    item: str
    name: str
    gender: str
    companion: str
    seed: Optional[int] = None


SETTINGS = {
    "corner_shop": Setting(place="the corner shop", afford={"buy", "pay"}),
    "cafe": Setting(place="the cafe", afford={"order", "pay"}),
    "laundry": Setting(place="the laundromat", afford={"wash", "pay"}),
}

TASKS = {
    "buy_fruit": Task(
        id="buy_fruit",
        verb="buy fruit",
        gerund="buying fruit",
        risk="the apples might bruise in a crowded bag",
        mess="crowded",
        zone={"torso"},
        keyword="register",
        tension="the line was getting longer",
        fix_label="a sturdy tote",
        fix_phrase="a sturdy tote bag",
        fix_covers={"torso"},
        fix_guards={"crowded"},
    ),
    "pay_snacks": Task(
        id="pay_snacks",
        verb="pay for snacks",
        gerund="paying for snacks",
        risk="the waiting made the snacks feel less warm",
        mess="waiting",
        zone={"hands"},
        keyword="register",
        tension="the cashier was already tapping the register",
        fix_label="a folded list",
        fix_phrase="a folded list of what to buy",
        fix_covers={"hands"},
        fix_guards={"waiting"},
    ),
    "pick_up_laundry": Task(
        id="pick_up_laundry",
        verb="pick up laundry",
        gerund="picking up laundry",
        risk="the basket could be too heavy to carry alone",
        mess="heavy",
        zone={"arms"},
        keyword="register",
        tension="the room felt quiet except for the humming machines",
        fix_label="a rolling cart",
        fix_phrase="a little rolling cart",
        fix_covers={"arms"},
        fix_guards={"heavy"},
    ),
}

ITEMS = {
    "basket": SceneItem("basket", "basket", "a cloth basket", "basket", "arms"),
    "bag": SceneItem("bag", "bag", "a paper bag", "bag", "torso"),
    "receipt": SceneItem("receipt", "receipt", "a receipt", "receipt", "hands"),
}

NAMES = {
    "girl": ["Mina", "Lina", "Rosa", "Tia"],
    "boy": ["Nico", "Eli", "Jude", "Sam"],
}
COMPANIONS = ["mother", "father", "friend"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id, task in TASKS.items():
            if "pay" in setting.afford:
                for item_id in ITEMS:
                    combos.append((place, task_id, item_id))
            else:
                for item_id in ["basket", "bag"]:
                    combos.append((place, task_id, item_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world with a register, a bull's errands, and dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=COMPANIONS)
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.task:
        combos = [c for c in combos if c[1] == args.task]
    if args.item:
        combos = [c for c in combos if c[2] == args.item]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, task, item = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    companion = args.companion or rng.choice(COMPANIONS)
    return StoryParams(place=place, task=task, item=item, name=name, gender=gender, companion=companion)


def narration_opening(world: World, hero: Entity, companion: Entity, task: Task, item: Entity) -> None:
    world.say(f"{hero.id} was a cheerful {hero.type} who liked small errands.")
    world.say(f"One afternoon, {hero.id} and {hero.pronoun('possessive')} {companion.label} went to {world.setting.place}.")
    world.say(f"{hero.id} needed to {task.verb}, and {item.phrase} was tucked under {hero.pronoun('possessive')} arm.")


def predict(world: World, hero: Entity, task: Task, item: Entity) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["hope"] = sim.get(hero.id).memes.get("hope", 0) + 1
    if task.id == "buy_fruit":
        item.meters["bruise"] = item.meters.get("bruise", 0) + 1
    return True


def resolve_story(world: World, hero: Entity, companion: Entity, task: Task, item: Entity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    world.say(f'"I can do it," {hero.id} said, but {hero.pronoun("possessive")} {companion.label} glanced at the register and smiled.')
    world.say(f'"{Look_out}," said {companion.id}. "The {task.keyword} line is long, and the {task.tension}."')
    world.say(f'"Then let me keep talking while we wait," {hero.id} said.')
    hero.memes["patience"] = hero.memes.get("patience", 0) + 1
    if task.id == "buy_fruit":
        world.say(f'{hero.id} adjusted {item.it()} carefully so the apples would stay nice.')
    elif task.id == "pick_up_laundry":
        world.say(f'{hero.id} took the handle with both hands, and the basket felt easier right away.')
    else:
        world.say(f'{hero.id} read the tiny prices out loud, one by one, to make the waiting feel softer.')
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(f'"There," said {companion.id}, "that was kinder than hurrying."')
    world.say(f'{hero.id} laughed, and the register clicked again as the clerk rang up the last thing in line.')
    world.say(f"By the time they left, {hero.id} had {task.gerund}, and the small errand felt like a good part of the day.")


def tell(setting: Setting, task: Task, item_cfg: SceneItem, name: str, gender: str, companion_kind: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name))
    companion = world.add(Entity(id="Companion", kind="character", type=companion_kind, label=f"{companion_kind}"))
    item = world.add(Entity(id=item_cfg.id, kind="thing", type=item_cfg.type, label=item_cfg.label, phrase=item_cfg.phrase, owner=hero.id))
    item.meters[f"covers_{item_cfg.region}"] = 1

    narration_opening(world, hero, companion, task, item)
    world.para()
    world.say(f"The {task.keyword} was right by the register, and {task.risk}.")
    world.say(f"{hero.id} looked at the line, then at {companion.label}, and took a slow breath.")
    resolve_story(world, hero, companion, task, item)

    world.facts.update(hero=hero, companion=companion, item=item, task=task, setting=setting)
    return world


def generate(params: StoryParams) -> StorySample:
    task = TASKS[params.task]
    world = tell(SETTINGS[params.place], task, ITEMS[params.item], params.name, params.gender, params.companion)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a short slice-of-life story about a {params.gender} named {params.name}, a register, and a small errand.",
            f"Tell a gentle dialogue-driven story set at {SETTINGS[params.place].place}.",
            f"Write a simple story where the word '{task.keyword}' appears and the characters solve a tiny problem kindly.",
        ],
        story_qa=[
            QAItem(
                question=f"Where did {params.name} go?",
                answer=f"{params.name} went to {SETTINGS[params.place].place} with a {params.companion}.",
            ),
            QAItem(
                question=f"What did {params.name} want to do?",
                answer=f"{params.name} wanted to {task.verb}.",
            ),
            QAItem(
                question="What helped the little problem feel easier?",
                answer=f"Talking kindly and slowing down helped, and the line at the register stopped feeling so tense.",
            ),
        ],
        world_qa=[
            QAItem(
                question="What is a register?",
                answer="A register is a machine or counter at a shop where prices are added up and money is handled.",
            ),
            QAItem(
                question="What does it mean when someone takes a slow breath?",
                answer="It means they pause, breathe in and out calmly, and try to feel less rushed.",
            ),
        ],
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
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(place,task,item) :- place_kind(place), task_kind(task), item_kind(item).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place_kind", p))
    for t in TASKS:
        lines.append(asp.fact("task_kind", t))
    for i in ITEMS:
        lines.append(asp.fact("item_kind", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_asp_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_asp_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python combos.")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="corner_shop", task="buy_fruit", item="bag", name="Mina", gender="girl", companion="mother"),
    StoryParams(place="cafe", task="pay_snacks", item="receipt", name="Nico", gender="boy", companion="friend"),
    StoryParams(place="laundry", task="pick_up_laundry", item="basket", name="Lina", gender="girl", companion="father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = valid_asp_combos()
        print(f"{len(combos)} compatible combos:\n")
        for t in combos:
            print(" ".join(map(str, t)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
