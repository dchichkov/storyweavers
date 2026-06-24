#!/usr/bin/env python3
"""
A small fable-style storyworld about an omelette, a menu, a pheasant, a quest,
a flashback, and teamwork.

A gentle seed tale behind this world:
---
At a little village inn, a shy pheasant named Peregrine wished for a special
omelette to appear on the breakfast menu. The cook doubted it could be done
because the last eggs were gone and the herb basket was empty.

So Peregrine began a quest through the garden, and along the way he remembered
a flashback from the old orchard: one bird had once carried the eggs while
another fetched herbs, and together they had made a feast.

Peregrine asked for teamwork. The cook and a mouse helper joined in, the needed
ingredients were found, and the omelette was cooked at last. When the menu was
written, the pheasant saw his wish become a happy breakfast for everyone.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "hen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "rooster", "pheasant"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    location: str = ""
    carried_by: Optional[str] = None
    reserved: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Task:
    id: str
    verb: str
    search: str
    obstacle: str
    reward: str
    mood: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    items: dict[str, Item] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    search_active: bool = False
    flashback_seen: bool = False
    teamwork_active: bool = False

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.items = copy.deepcopy(self.items)
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        c.search_active = self.search_active
        c.flashback_seen = self.flashback_seen
        c.teamwork_active = self.teamwork_active
        c.paragraphs = [[]]
        return c


@dataclass
class StoryParams:
    place: str
    task: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "inn": Setting(place="the village inn", indoors=True, affords={"quest", "flashback", "teamwork"}),
    "garden": Setting(place="the garden behind the inn", indoors=False, affords={"quest", "flashback", "teamwork"}),
    "kitchen": Setting(place="the warm kitchen", indoors=True, affords={"quest", "flashback", "teamwork"}),
}

TASKS = {
    "menu": Task(
        id="menu",
        verb="put a new omelette on the menu",
        search="find the last good eggs and herbs",
        obstacle="the basket was empty and the cook was worried",
        reward="a bright breakfast feast",
        mood="hopeful",
        tags={"omelette", "menu"},
    ),
    "quest": Task(
        id="quest",
        verb="go on a quest for breakfast ingredients",
        search="look for eggs, chives, and a clean pan",
        obstacle="the path was long and the day felt uncertain",
        reward="a kind meal for everyone",
        mood="brave",
        tags={"quest", "omelette"},
    ),
    "flashback": Task(
        id="flashback",
        verb="remember an old lesson about cooking together",
        search="think back to how the orchard birds solved a problem",
        obstacle="the memory was hidden behind worry",
        reward="a smarter plan",
        mood="wise",
        tags={"flashback", "teamwork"},
    ),
    "teamwork": Task(
        id="teamwork",
        verb="ask for teamwork in the kitchen",
        search="join hands and share the work",
        obstacle="everyone tried to do too much alone",
        reward="a meal that came together fast",
        mood="gentle",
        tags={"teamwork", "menu"},
    ),
}

GENDERS = ["girl", "boy"]
HELPERS = ["mouse", "cat", "hen", "duck"]
NAMES = ["Pip", "Mina", "Toby", "Lila", "Nora", "Ben", "Mira", "Otto"]

WORLD_ITEMS = {
    "omelette": Item(id="omelette", label="omelette", phrase="a golden omelette", type="food"),
    "menu": Item(id="menu", label="menu", phrase="the breakfast menu", type="paper"),
    "pheasant": Item(id="pheasant", label="pheasant", phrase="a shy pheasant", type="bird"),
    "eggs": Item(id="eggs", label="eggs", phrase="fresh eggs", type="food"),
    "herbs": Item(id="herbs", label="herbs", phrase="green herbs", type="food"),
    "pan": Item(id="pan", label="pan", phrase="a clean pan", type="tool"),
}


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            combos.append((place, task_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-style storyworld: omelette, menu, pheasant, quest, flashback, teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--helper", choices=HELPERS)
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


def select_task(params: StoryParams) -> Task:
    return TASKS[params.task]


def select_helper(rng: random.Random, preferred: Optional[str] = None) -> str:
    return preferred or rng.choice(HELPERS)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.task and (args.place, args.task) not in valid_combos():
        raise StoryError("(No valid story: that place cannot host that fable-shaped event.)")
    place = args.place or rng.choice(list(SETTINGS))
    task = args.task or rng.choice(sorted(SETTINGS[place].affords))
    if task not in SETTINGS[place].affords:
        raise StoryError("(No valid story: the chosen task does not fit that setting.)")
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES)
    helper = args.helper or select_helper(rng)
    return StoryParams(place=place, task=task, name=name, gender=gender, helper=helper)


def introduce(world: World, hero: Entity, helper: Entity, item_menu: Item, item_pheasant: Item) -> None:
    world.say(
        f"In {world.setting.place}, a little {hero.type} named {hero.id} loved the {item_menu.label} and watched the {item_pheasant.label} with kind eyes."
    )
    world.say(
        f"{hero.pronoun().capitalize()} was a {hero.traits[0]} little soul, and {helper.label} was nearby, ready to help."
    )


def start_quest(world: World, hero: Entity, task: Task) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.search_active = True
    world.say(
        f"One morning, {hero.id} wanted to {task.verb}, but {task.obstacle}."
    )


def flashback(world: World, hero: Entity) -> None:
    if not world.search_active:
        return
    world.flashback_seen = True
    hero.memes["memory"] = hero.memes.get("memory", 0) + 1
    world.say(
        f"Then {hero.id} had a flashback to an old orchard lesson: one bird had carried the eggs while another fetched the herbs."
    )
    world.say(
        f"In that memory, the birds had learned that teamwork made a hard breakfast feel light."
    )


def teamwork(world: World, hero: Entity, helper: Entity, task: Task) -> None:
    world.teamwork_active = True
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    helper.memes["helping"] = helper.memes.get("helping", 0) + 1
    world.say(
        f"So {hero.id} asked {helper.id} for teamwork, and {helper.label} nodded at once."
    )
    world.say(
        f"Together they began to {task.search}, one careful step after another."
    )


def resolve_story(world: World, hero: Entity, helper: Entity, task: Task, menu: Item, omelette: Item, pheasant: Item) -> None:
    menu.reserved = True
    omelette.reserved = True
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    world.say(
        f"They found the eggs, warmed the pan, and stirred the mixture until the omelette turned golden."
    )
    world.say(
        f"At last, the cook wrote the omelette on the menu, and {pheasant.label} stood tall beside the kitchen door."
    )
    world.say(
        f"The little fable ended with {hero.id} smiling, {helper.id} sharing the work, and a breakfast that belonged to everyone."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    task = select_task(params)

    hero = world.add_entity(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["kind", "curious"],
        memes={"hope": 0.0},
    ))
    helper = world.add_entity(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        traits=["helpful"],
        memes={"helping": 0.0},
    ))
    pheasant = world.add_entity(Entity(
        id="pheasant",
        kind="character",
        type="pheasant",
        traits=["shy", "wise"],
        memes={"hope": 0.0},
    ))
    menu = world.add_item(copy.deepcopy(WORLD_ITEMS["menu"]))
    omelette = world.add_item(copy.deepcopy(WORLD_ITEMS["omelette"]))
    world.add_item(copy.deepcopy(WORLD_ITEMS["eggs"]))
    world.add_item(copy.deepcopy(WORLD_ITEMS["herbs"]))
    world.add_item(copy.deepcopy(WORLD_ITEMS["pan"]))

    pheasant.memes["wish"] = 1.0

    introduce(world, hero, helper, menu, pheasant)
    world.para()
    start_quest(world, pheasant, task)
    flashback(world, pheasant)
    teamwork(world, pheasant, helper, task)
    resolve_story(world, pheasant, helper, task, menu, omelette, pheasant)

    world.facts.update(
        hero=hero,
        helper=helper,
        pheasant=pheasant,
        menu=menu,
        omelette=omelette,
        task=task,
        place=params.place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short fable for a child that includes the words "omelette", "menu", and "pheasant".',
        f"Tell a gentle story where {f['pheasant'].id} goes on a quest to help the kitchen make an omelette for the menu.",
        f"Write a story with a flashback and teamwork in {world.setting.place} that ends with the omelette on the menu.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    pheasant: Entity = f["pheasant"]
    task: Task = f["task"]
    return [
        QAItem(
            question=f"Who wanted to help the kitchen with the omelette on the menu?",
            answer=f"The shy pheasant named {pheasant.id} wanted to help, and {hero.id} joined in too.",
        ),
        QAItem(
            question=f"What did {pheasant.id} remember in the flashback?",
            answer="The flashback showed birds working together in an orchard, with one carrying eggs and another fetching herbs.",
        ),
        QAItem(
            question=f"How did teamwork help in the story?",
            answer=f"Teamwork let {pheasant.id}, {helper.id}, and the cook share the work so the omelette could be finished for the menu.",
        ),
        QAItem(
            question=f"What was the big quest in the story?",
            answer=f"The quest was to {task.search} so the kitchen could make breakfast for everyone.",
        ),
    ]


KNOWLEDGE = {
    "omelette": [("What is an omelette?", "An omelette is a soft egg dish cooked in a pan and folded into a warm meal.")],
    "menu": [("What is a menu?", "A menu is a list of foods a place can serve.")],
    "pheasant": [("What is a pheasant?", "A pheasant is a bird with colorful feathers that often lives in fields and grass.")],
    "quest": [("What is a quest?", "A quest is a search or journey to find something important or solve a problem.")],
    "flashback": [("What is a flashback?", "A flashback is a story moment that remembers something from before.")],
    "teamwork": [("What is teamwork?", "Teamwork means people or animals help each other do a job together.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["task"].tags)
    tags.update({"omelette", "menu", "pheasant"})
    out: list[QAItem] = []
    for tag, qa in KNOWLEDGE.items():
        if tag in tags:
            for q, a in qa:
                out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: type={e.type} memes={dict(e.memes)} meters={dict(e.meters)}")
    for it in world.items.values():
        out.append(f"{it.id}: label={it.label} reserved={it.reserved}")
    out.append(f"flags: quest={world.search_active} flashback={world.flashback_seen} teamwork={world.teamwork_active}")
    return "\n".join(out)


ASP_RULES = r"""
task_needed(quest).
task_needed(menu).
task_needed(flashback).
task_needed(teamwork).

valid_combo(Place, Task) :- setting(Place), affords(Place, Task), task_needed(Task).
story_ready(Place) :- valid_combo(Place, quest), valid_combo(Place, menu),
                      valid_combo(Place, flashback), valid_combo(Place, teamwork).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", sid, t))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="inn", task="menu", name="Pip", gender="boy", helper="mouse"),
    StoryParams(place="garden", task="quest", name="Mina", gender="girl", helper="hen"),
    StoryParams(place="kitchen", task="flashback", name="Lila", gender="girl", helper="duck"),
    StoryParams(place="inn", task="teamwork", name="Ben", gender="boy", helper="cat"),
]


def explain_rejection() -> str:
    return "(No story: that combination does not fit the little fable world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.task and (args.place, args.task) not in valid_combos():
        raise StoryError(explain_rejection())
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(GENDERS)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, task=task, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:\n")
        for place, task in combos:
            print(f"  {place:8} {task}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
