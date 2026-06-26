#!/usr/bin/env python3
"""
storyworlds/worlds/entire_repetition_friendship_folk_tale.py
=============================================================

A small folk-tale storyworld about a repeated task, a loyal friendship, and an
"entire" thing that must be carried, kept, or shared without breaking.

Seed image:
- A village child and a friend want to bring the entire bundle home.
- They try, stumble, try again, and finally succeed together.
- The story uses repetition like a folk tale refrain and ends with a warm,
  shared image.

This script follows the Storyweavers world contract:
- stdlib-only prose engine
- shared results import eagerly
- ASP twin with inline rules
- world state drives narration, QA, and verification
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

PLACE_WORD = "entire"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    companion_of: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    paths: set[str] = field(default_factory=set)
    weather: str = "clear"


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    strain: str
    mishap: str
    success_image: str
    weight: int
    kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    plural: bool = False
    weight: int = 2
    fragile: bool = False


@dataclass
class Aid:
    id: str
    label: str
    method: str
    help_text: str
    capacity_bonus: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.lines = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def meters_get(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def memes_get(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def add_meter(e: Entity, key: str, amount: float) -> None:
    e.meters[key] = meters_get(e, key) + amount


def add_meme(e: Entity, key: str, amount: float) -> None:
    e.memes[key] = memes_get(e, key) + amount


@dataclass
class StoryParams:
    place: str
    task: str
    treasure: str
    aid: str
    hero_name: str
    friend_name: str
    hero_type: str
    friend_type: str
    seed: Optional[int] = None


SETTINGS = {
    "village_green": Setting(place="the village green", paths={"bridge", "lane"}),
    "old_bridge": Setting(place="the old bridge", paths={"bridge", "lane"}),
    "pine_lane": Setting(place="the pine lane", paths={"lane"}),
}

TASKS = {
    "carry_basket": Task(
        id="carry_basket",
        verb="carry the entire basket home",
        gerund="carrying the entire basket",
        strain="heavy",
        mishap="dropping the basket",
        success_image="the basket stayed whole in their hands",
        weight=5,
        kind="carry",
        tags={"basket", "share", "entire"},
    ),
    "bring_milk": Task(
        id="bring_milk",
        verb="bring the entire milk pail to the cottage",
        gerund="bringing the milk pail",
        strain="careful",
        mishap="slopping the milk",
        success_image="the milk pail did not spill a drop",
        weight=4,
        kind="carry",
        tags={"milk", "pail", "entire"},
    ),
    "guide_lanterns": Task(
        id="guide_lanterns",
        verb="guide the entire lantern string home",
        gerund="guiding the lantern string",
        strain="wobbly",
        mishap="snuffing the lanterns",
        success_image="the lanterns shone like small moons",
        weight=4,
        kind="carry",
        tags={"lantern", "light", "entire"},
    ),
}

TREASURES = {
    "basket": Treasure("basket", "basket", "a woven basket filled with apples", weight=5),
    "milk_pail": Treasure("milk_pail", "milk pail", "a milk pail from the dairy", weight=4),
    "lantern_string": Treasure("lantern_string", "lantern string", "an entire string of lanterns", weight=4, fragile=True),
}

AIDS = {
    "shared_grip": Aid(
        id="shared_grip",
        label="a shared grip",
        method="hold it together",
        help_text="They each took one side, and the load stopped wobbling.",
        capacity_bonus=2,
        tags={"share", "friendship"},
    ),
    "short_poles": Aid(
        id="short_poles",
        label="short carrying poles",
        method="thread the poles under the load",
        help_text="The poles spread the weight so the basket rested more evenly.",
        capacity_bonus=3,
        tags={"carry", "basket"},
    ),
    "cloth_wrap": Aid(
        id="cloth_wrap",
        label="a cloth wrap",
        method="wrap the fragile part in cloth",
        help_text="The cloth kept the lanterns from clinking together.",
        capacity_bonus=2,
        tags={"lantern", "fragile"},
    ),
}

HERO_NAMES = ["Mara", "Tobin", "Nella", "Pip", "Hugo", "Lina"]
FRIEND_NAMES = ["Bram", "Kiri", "Otis", "Sana", "Jory", "Pera"]
TYPES = ["girl", "boy"]


class ReasoningError(StoryError):
    pass


def load_capacity(hero: Entity, friend: Entity, aid: Optional[Aid]) -> int:
    base = 4
    if aid:
        base += aid.capacity_bonus
    if memes_get(hero, "trust") >= 1 and memes_get(friend, "trust") >= 1:
        base += 1
    return base


def task_requires_aid(task: Task, treasure: Treasure) -> bool:
    return treasure.weight >= task.weight - 1 or treasure.fragile


def choose_aid(task: Task, treasure: Treasure) -> Optional[Aid]:
    for aid in AIDS.values():
        if task.id == "guide_lanterns" and aid.id == "cloth_wrap":
            return aid
        if task.id == "carry_basket" and aid.id in {"shared_grip", "short_poles"}:
            return aid
        if task.id == "bring_milk" and aid.id == "shared_grip":
            return aid
    return None


def predict(world: World, hero: Entity, friend: Entity, task: Task, treasure: Treasure, aid: Optional[Aid]) -> dict:
    sim = world.copy()
    _attempt(sim, hero.id, friend.id, task, treasure, aid, narrate=False)
    tr = sim.get(treasure.id)
    return {
        "broken": meters_get(tr, "broken") >= 1,
        "lost": meters_get(tr, "lost") >= 1,
        "done": sim.facts.get("done", False),
    }


def _attempt(world: World, hero_id: str, friend_id: str, task: Task, treasure: Treasure, aid: Optional[Aid], narrate: bool = True) -> None:
    hero = world.get(hero_id)
    friend = world.get(friend_id)
    load = treasure.weight
    cap = load_capacity(hero, friend, aid)
    sig = ("attempt", task.id, aid.id if aid else "none")
    if sig in world.fired:
        return
    world.fired.add(sig)
    add_meme(hero, "effort", 1)
    add_meme(friend, "effort", 1)
    if cap < load:
        add_meter(world.get(treasure.id), "wobble", 1)
        add_meme(hero, "worry", 1)
        add_meme(friend, "worry", 1)
    else:
        world.facts["done"] = True
        add_meme(hero, "joy", 1)
        add_meme(friend, "joy", 1)
    if narrate:
        if cap < load:
            world.say(f"They tried to {task.verb}, but the load was too much and it slipped in their hands.")
        else:
            world.say(f"They tried to {task.verb}, and the weight stayed steady between them.")


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    task = TASKS[params.task]
    treasure = TREASURES[params.treasure]
    aid = AIDS[params.aid]
    world = World(setting)

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, meters={"effort": 0}, memes={"trust": 1}))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_type, meters={"effort": 0}, memes={"trust": 1}))
    prize = world.add(Entity(id=treasure.id, kind="thing", type=treasure.id, label=treasure.label, phrase=treasure.phrase, plural=treasure.plural, meters={"wobble": 0}, memes={}))

    world.say(f"Once in {setting.place}, {hero.id} and {friend.id} were dear friends, as close as bread and butter.")
    world.say(f"They longed to {task.verb}, because the entire village was waiting for {treasure.phrase}.")
    world.say(f"But the load was {task.strain}, and {hero.id} knew it would not be wise to hurry.")

    world.para()
    for step in range(1, 4):
        if step == 1:
            world.say(f"First, they lifted it, and at once it wobbled like a goose in wind.")
            _attempt(world, hero.id, friend.id, task, treasure, None, narrate=False)
            world.say(f"First they tried alone, and the load nearly slipped.")
        elif step == 2:
            world.say(f"Then, they paused, looked at one another, and tried again with kinder hands.")
            _attempt(world, hero.id, friend.id, task, treasure, None, narrate=False)
            world.say(f"Then they tried with more care, but the burden still asked for help.")
        else:
            world.say(f"At last, they remembered the old ways of friends and asked for {aid.label}.")
            _attempt(world, hero.id, friend.id, task, treasure, aid, narrate=False)
            world.say(f"At last they used {aid.label}, and the task began to feel shared instead of lonely.")

    world.para()
    if world.facts.get("done"):
        add_meme(hero, "friendship", 1)
        add_meme(friend, "friendship", 1)
        world.say(f"In the end, {aid.help_text}")
        world.say(f"So {hero.id} and {friend.id} finished the work, and {treasure.phrase} came home safe.")
        world.say(f"The entire village smiled to see that {task.success_image}.")
    else:
        world.say(f"Even after three tries, the task was too hard, and the friends had to set it down.")

    world.facts.update(
        hero=hero,
        friend=friend,
        task=task,
        treasure=prize,
        aid=aid,
        setting=setting,
        done=bool(world.facts.get("done")),
    )
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.paths:
            pass
    for place in SETTINGS:
        for task_id, task in TASKS.items():
            for treasure_id, treasure in TREASURES.items():
                if task_requires_aid(task, treasure) and choose_aid(task, treasure):
                    combos.append((place, task_id, treasure_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world about repetition, friendship, and an entire task.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--hero-type", choices=TYPES)
    ap.add_argument("--friend-type", choices=TYPES)
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
    if args.task and args.treasure:
        task, treasure = TASKS[args.task], TREASURES[args.treasure]
        if not task_requires_aid(task, treasure) or not choose_aid(task, treasure):
            raise StoryError("No story: that task and treasure do not make a reasonable friendship problem.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.treasure is None or c[2] == args.treasure)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, task_id, treasure_id = rng.choice(sorted(combos))
    task = TASKS[task_id]
    treasure = TREASURES[treasure_id]
    aid = args.aid or choose_aid(task, treasure).id
    hero_type = args.hero_type or rng.choice(TYPES)
    friend_type = args.friend_type or rng.choice(TYPES)
    hero_name = args.name or rng.choice(HERO_NAMES)
    friend_name = args.friend or rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    return StoryParams(place=place, task=task_id, treasure=treasure_id, aid=aid, hero_name=hero_name, friend_name=friend_name, hero_type=hero_type, friend_type=friend_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale about friendship, repetition, and the word "{PLACE_WORD}".',
        f"Tell a child-friendly story where {f['hero'].id} and {f['friend'].id} try three times to {f['task'].verb}.",
        f"Write a gentle village tale that ends with {f['treasure'].phrase} being carried home by friends.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, task, treasure = f["hero"], f["friend"], f["task"], f["treasure"]
    aid = f["aid"]
    return [
        QAItem(
            question=f"Who were the friends in the story?",
            answer=f"The friends were {hero.id} and {friend.id}. They worked side by side in {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} and {friend.id} try to do three times?",
            answer=f"They tried to {task.verb}. The story repeats the effort three times before the right help arrives.",
        ),
        QAItem(
            question=f"What made the last try work?",
            answer=f"They used {aid.label}, which helped them share the weight and finish carrying {treasure.phrase}.",
        ),
        QAItem(
            question=f"What changed by the end of the tale?",
            answer=f"By the end, the task was done, the friends felt more joy, and {treasure.phrase} came home safe.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care for one another, help one another, and stay kind even when a task is hard.",
        ),
        QAItem(
            question="Why do people repeat a try in a folk tale?",
            answer="Folk tales often repeat a try so the listener can feel the pattern, the struggle, and the change when the answer is found.",
        ),
        QAItem(
            question="What does it mean to carry the entire thing?",
            answer="It means the whole load must be moved together, not just a part of it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams("village_green", "carry_basket", "basket", "shared_grip", "Mara", "Bram", "girl", "boy"),
    StoryParams("old_bridge", "guide_lanterns", "lantern_string", "cloth_wrap", "Tobin", "Kiri", "boy", "girl"),
    StoryParams("pine_lane", "bring_milk", "milk_pail", "shared_grip", "Nella", "Otis", "girl", "boy"),
]


ASP_RULES = r"""
task_ok(P,T,R) :- place(P), task(T), treasure(R), requires_aid(T,R), has_aid(T,R).
has_aid(carry_basket,basket) :- aid(shared_grip).
has_aid(carry_basket,basket) :- aid(short_poles).
has_aid(guide_lanterns,lantern_string) :- aid(cloth_wrap).
has_aid(bring_milk,milk_pail) :- aid(shared_grip).

valid(P,T,R) :- setting(P), task(T), treasure(R), task_ok(P,T,R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for t in TASKS:
        lines.append(asp.fact("task", t))
    for r in TREASURES:
        lines.append(asp.fact("treasure", r))
    for a in AIDS:
        lines.append(asp.fact("aid", a))
    lines.append(asp.fact("requires_aid", "carry_basket", "basket"))
    lines.append(asp.fact("requires_aid", "guide_lanterns", "lantern_string"))
    lines.append(asp.fact("requires_aid", "bring_milk", "milk_pail"))
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
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, task, treasure) combos:")
        for row in combos:
            print(" ", row)
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
            header = f"### {p.hero_name} and {p.friend_name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
