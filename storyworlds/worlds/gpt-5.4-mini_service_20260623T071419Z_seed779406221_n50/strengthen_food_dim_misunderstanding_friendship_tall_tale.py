#!/usr/bin/env python3
"""
storyworlds/worlds/strengthen_food_dim_misunderstanding_friendship_tall_tale.py
===============================================================================

A standalone story world in a tall-tale style about a misunderstanding that
tests friendship, then strengthens it. The seed words are woven into the world:
"strengthen" and "food-dim".

Premise:
- Two friends in a tiny frontier town hear an odd request about "food-dim" and
  think it means their supper must be dull, weak, or plain.
- One friend wants to strengthen a creek bridge and their friendship by bringing
  a big meal to the work crew.
- The misunderstanding creates a brief tension, then a helpful explanation and
  a shared meal resolve it.

The world uses typed entities with physical meters and emotional memes, a small
forward-chaining rule engine, a reasonableness gate, and an inline ASP twin.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    scale: str
    has_water: bool = False
    has_bridge: bool = False
    has_oven: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    heat: str
    strength: int
    dimness: int
    tastes: set[str] = field(default_factory=set)
    generous: bool = False


@dataclass
class Misunderstanding:
    id: str
    label: str
    trigger: str
    mistaken_meaning: str
    clear_meaning: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class BridgeTask:
    id: str
    label: str
    purpose: str
    weight: int
    risk: str
    needs_help: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    food: str
    misunderstanding: str
    task: str
    name_a: str
    name_b: str
    gender_a: str
    gender_b: str
    relation: str
    seed: Optional[int] = None


PLACES = {
    "prairie": Place(
        id="prairie",
        label="the windy prairie town",
        scale="wide",
        has_water=True,
        has_bridge=True,
        affords={"cook", "carry", "share"},
    ),
    "riverbend": Place(
        id="riverbend",
        label="the town by the river",
        scale="wide",
        has_water=True,
        has_bridge=True,
        affords={"cook", "carry", "share"},
    ),
    "orchard": Place(
        id="orchard",
        label="the apple orchard camp",
        scale="open",
        has_water=False,
        has_bridge=True,
        affords={"cook", "carry", "share"},
    ),
}

FOODS = {
    "cornbread": Food(
        id="cornbread",
        label="cornbread",
        phrase="a pan of golden cornbread",
        heat="warm",
        strength=3,
        dimness=1,
        tastes={"corn", "bread"},
    ),
    "stew": Food(
        id="stew",
        label="stew",
        phrase="a big pot of beef stew",
        heat="hot",
        strength=4,
        dimness=1,
        tastes={"meat", "broth"},
        generous=True,
    ),
    "applepie": Food(
        id="applepie",
        label="apple pie",
        phrase="a big apple pie",
        heat="warm",
        strength=2,
        dimness=2,
        tastes={"apple", "sweet"},
    ),
}

MISUNDERSTANDINGS = {
    "dimmer": Misunderstanding(
        id="dimmer",
        label="food-dim",
        trigger="food-dim",
        mistaken_meaning="something dull or weak to eat",
        clear_meaning="food for the big work crew",
        risk="their friend might feel pushed aside",
        tags={"food-dim", "misunderstanding"},
    ),
    "quietmeal": Misunderstanding(
        id="quietmeal",
        label="food-dim",
        trigger="food-dim",
        mistaken_meaning="a plain supper with no joy",
        clear_meaning="a simple meal meant to help people working hard",
        risk="the helpers might go hungry",
        tags={"food-dim", "misunderstanding"},
    ),
}

TASKS = {
    "bridge": BridgeTask(
        id="bridge",
        label="the creek bridge",
        purpose="to strengthen the old bridge",
        weight=5,
        risk="the bridge might wobble and scare the horses",
        tags={"bridge", "strengthen"},
    ),
    "fence": BridgeTask(
        id="fence",
        label="the pasture fence",
        purpose="to strengthen the loose fence",
        weight=3,
        risk="the fence might lean in the wind",
        tags={"fence", "strengthen"},
    ),
}

GIRL_NAMES = ["Mabel", "June", "Rosie", "Clara", "Lottie", "Pearl", "Nell", "Ada"]
BOY_NAMES = ["Hank", "Otis", "Elmer", "Bert", "Wes", "Jeb", "Milo", "Cal"]
TRAITS = ["helpful", "cheery", "stubborn", "brave", "gentle", "lively"]


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            res = rule.apply(world)
            if res:
                changed = True
                out.extend(res)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_bridge_wobble(world: World) -> list[str]:
    out: list[str] = []
    task = world.get("task")
    if task.meters["packed"] < THRESHOLD:
        return out
    if ("bridge_wobble",) in world.fired:
        return out
    world.fired.add(("bridge_wobble",))
    task.memes["worry"] += 1
    out.append("The old bridge gave a little wobble and the town held its breath.")
    return out


def _r_food_shared(world: World) -> list[str]:
    out: list[str] = []
    meal = world.get("meal")
    a = world.get("friend_a")
    b = world.get("friend_b")
    if meal.meters["served"] < THRESHOLD or ("shared",) in world.fired:
        return out
    world.fired.add(("shared",))
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.memes["misunderstanding"] = 0
    b.memes["misunderstanding"] = 0
    out.append("The meal went round the table, and it warmed every face there.")
    return out


RULES = [
    Rule(name="bridge_wobble", apply=_r_bridge_wobble),
    Rule(name="food_shared", apply=_r_food_shared),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for food_id in FOODS:
            for mis_id, mis in MISUNDERSTANDINGS.items():
                for task_id in TASKS:
                    if place.has_bridge and "food-dim" in mis.tags and "strengthen" in TASKS[task_id].tags:
                        combos.append((place_id, food_id, mis_id))
    return combos


def is_reasonable(place: Place, food: Food, misunderstanding: Misunderstanding, task: BridgeTask) -> bool:
    return place.has_bridge and task.needs_help and misunderstanding.trigger == "food-dim" and food.strength >= 2


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about a misunderstanding and friendship.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--gender-b", choices=["girl", "boy"])
    ap.add_argument("--relation", choices=["friends", "cousins"])
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
              if (args.place is None or c[0] == args.place)
              and (args.food is None or c[1] == args.food)
              and (args.misunderstanding is None or c[2] == args.misunderstanding)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, food, mis = rng.choice(sorted(combos))
    task = args.task or rng.choice(sorted(TASKS))
    if not is_reasonable(PLACES[place], FOODS[food], MISUNDERSTANDINGS[mis], TASKS[task]):
        raise StoryError("That combination does not make a reasonable tall tale.")
    g_a = args.gender_a or rng.choice(["girl", "boy"])
    g_b = args.gender_b or rng.choice(["girl", "boy"])
    n_a = args.name_a or rng.choice(GIRL_NAMES if g_a == "girl" else BOY_NAMES)
    n_b = args.name_b or rng.choice([n for n in (GIRL_NAMES if g_b == "girl" else BOY_NAMES) if n != n_a])
    rel = args.relation or rng.choice(["friends", "cousins"])
    return StoryParams(
        place=place,
        food=food,
        misunderstanding=mis,
        task=task,
        name_a=n_a,
        name_b=n_b,
        gender_a=g_a,
        gender_b=g_b,
        relation=rel,
    )


def tell(params: StoryParams) -> World:
    world = World()
    place = PLACES[params.place]
    food = FOODS[params.food]
    mis = MISUNDERSTANDINGS[params.misunderstanding]
    task = TASKS[params.task]

    a = world.add(Entity(id="friend_a", kind="character", type=params.gender_a, label=params.name_a, traits=["tall-tale"]))
    b = world.add(Entity(id="friend_b", kind="character", type=params.gender_b, label=params.name_b, traits=["tall-tale"]))
    meal = world.add(Entity(id="meal", type="food", label=food.label))
    task_ent = world.add(Entity(id="task", type="task", label=task.label))
    clue = world.add(Entity(id="clue", type="note", label=mis.label))
    bridge = world.add(Entity(id="bridge", type="bridge", label=task.label))

    a.memes["friendship"] = 2
    b.memes["friendship"] = 2
    a.memes["misunderstanding"] = 1
    b.memes["misunderstanding"] = 1
    meal.meters["served"] = 0
    task_ent.meters["packed"] = 0
    bridge.meters["steady"] = 0
    world.facts["place"] = place
    world.facts["food_cfg"] = food
    world.facts["mis_cfg"] = mis
    world.facts["task_cfg"] = task

    world.say(f"{a.label} and {b.label} were friends as wide as the prairie sky.")
    world.say(f"They set out for {place.label}, where {task.purpose} was the day's big job.")
    world.say(f"That morning someone called it {mis.trigger}, and both friends heard it wrong.")
    world.para()
    a.memes["misunderstanding"] += 1
    b.memes["misunderstanding"] += 1
    world.say(f"{a.label} thought {mis.mistaken_meaning}. {b.label} thought the same.")
    world.say(f"But the meaning was really {mis.clear_meaning}.")
    world.say(f"{a.label} worried that a plain meal would never {task.purpose}.")
    world.para()
    task_ent.meters["packed"] += 1
    propagate(world, narrate=False)
    world.say(f"So the friends packed {food.phrase} and carried it toward {task.label}.")
    world.say(f"Even a mule could smell the {food.heat} supper from a mile away.")
    world.say(f"When they arrived, the crew laughed kindly and explained the mix-up.")
    world.para()
    meal.meters["served"] += 1
    a.memes["friendship"] += 2
    b.memes["friendship"] += 2
    world.say(f"{a.label} and {b.label} shared the meal with everybody, and the whole line of workers sat up straighter.")
    world.say(f"The old bridge got its fix, and the friends' friendship got stronger too.")
    world.say(f"By sunset, the creek looked silver, the supper pot was empty, and nobody remembered the mistake except to laugh at it.")

    world.facts.update(
        friend_a=a,
        friend_b=b,
        meal=meal,
        task=task_ent,
        bridge=bridge,
        place_cfg=place,
        outcome="resolved",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["friend_a"]
    b = f["friend_b"]
    food = f["food_cfg"]
    mis = f["mis_cfg"]
    task = f["task_cfg"]
    return [
        f'Write a tall-tale style story where {a.label} and {b.label} hear "{mis.trigger}" and think it means something weak, but it actually means food for workers.',
        f"Tell a friendship story where two friends bring {food.phrase} to {task.label} and a misunderstanding turns into laughter.",
        f'Write a small frontier tale that uses the word "{mis.trigger}" and ends with friendship growing stronger after supper.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = f["friend_a"]
    b = f["friend_b"]
    food = f["food_cfg"]
    mis = f["mis_cfg"]
    task = f["task_cfg"]
    return [
        QAItem(
            question=f"Who are the story friends?",
            answer=f"The story is about {a.label} and {b.label}, two friends whose friendship starts out strong and gets stronger by the end.",
        ),
        QAItem(
            question=f"What did {a.label} and {b.label} misunderstand about {mis.trigger}?",
            answer=f"They thought {mis.trigger} meant {mis.mistaken_meaning}, but it really meant {mis.clear_meaning}. That is why they first worried before they understood.",
        ),
        QAItem(
            question=f"What did they bring to {task.label}?",
            answer=f"They brought {food.phrase} to {task.label}. The meal was hearty enough to help after the work was done.",
        ),
        QAItem(
            question=f"How did the misunderstanding change by the end?",
            answer="The misunderstanding was cleared up, so the friends could laugh together instead of worrying. Their friendship ended warmer than it began.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    food = f["food_cfg"]
    out = [
        QAItem(
            question="What does it mean to strengthen something?",
            answer="To strengthen something means to make it sturdier, safer, or harder to break.",
        ),
        QAItem(
            question="Why can a shared meal help friendship?",
            answer="Sharing food can help friendship because it gives people a chance to sit together, talk, and feel like a team.",
        ),
    ]
    if food.generous:
        out.append(
            QAItem(
                question="Why is stew a good work meal?",
                answer="Stew is a good work meal because it is warm, filling, and easy to serve to many people.",
            )
        )
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="prairie",
        food="stew",
        misunderstanding="dimmer",
        task="bridge",
        name_a="Mabel",
        name_b="Hank",
        gender_a="girl",
        gender_b="boy",
        relation="friends",
    ),
    StoryParams(
        place="riverbend",
        food="cornbread",
        misunderstanding="quietmeal",
        task="bridge",
        name_a="June",
        name_b="Otis",
        gender_a="girl",
        gender_b="boy",
        relation="friends",
    ),
]


def explain_rejection() -> str:
    return "(No story: this combination does not make a reasonable tall tale.)"


ASP_RULES = r"""
reasonably_possible(P,F,M,T) :- place(P), food(F), misunderstanding(M), task(T), bridge_place(P), strengthening_task(T), food_good(F), food_dim(M).
shared_meal :- served(Meal), meal(Meal).
friendship_stronger(A,B) :- friend(A), friend(B), shared_meal.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.has_bridge:
            lines.append(asp.fact("bridge_place", pid))
    for fid, f in FOODS.items():
        lines.append(asp.fact("food", fid))
        if f.strength >= 2:
            lines.append(asp.fact("food_good", fid))
        if f.dimness >= 1:
            lines.append(asp.fact("food_dim", fid))
    for mid, m in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("misunderstanding", mid))
        lines.append(asp.fact("trigger", mid, m.trigger))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("strengthening_task", tid))
    lines.append(asp.fact("friend", "friend_a"))
    lines.append(asp.fact("friend", "friend_b"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonably_possible/4."))
    return sorted(set(asp.atoms(model, "reasonably_possible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH between clingo and Python gate.")
        if cl - py:
            print("only in clingo:", sorted(cl - py))
        if py - cl:
            print("only in python:", sorted(py - cl))
        return 1
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if not sample.story.strip():
        print("MISMATCH: generation produced empty story.")
        return 1
    print("OK: smoke-test story generation succeeded.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.food not in FOODS or params.misunderstanding not in MISUNDERSTANDINGS or params.task not in TASKS:
        raise StoryError("Invalid story parameters.")
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
        print(asp_program("#show reasonably_possible/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name_a} and {p.name_b}: {p.misunderstanding} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.food is None or c[1] == args.food)
              and (args.misunderstanding is None or c[2] == args.misunderstanding)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, food, mis = rng.choice(sorted(combos))
    task = args.task or rng.choice(sorted(TASKS))
    g_a = args.gender_a or rng.choice(["girl", "boy"])
    g_b = args.gender_b or rng.choice(["girl", "boy"])
    n_a = args.name_a or rng.choice(GIRL_NAMES if g_a == "girl" else BOY_NAMES)
    n_b = args.name_b or rng.choice([n for n in (GIRL_NAMES if g_b == "girl" else BOY_NAMES) if n != n_a])
    rel = args.relation or rng.choice(["friends", "cousins"])
    return StoryParams(
        place=place,
        food=food,
        misunderstanding=mis,
        task=task,
        name_a=n_a,
        name_b=n_b,
        gender_a=g_a,
        gender_b=g_b,
        relation=rel,
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id in PLACES:
        for food_id in FOODS:
            for mis_id in MISUNDERSTANDINGS:
                for task_id in TASKS:
                    if is_reasonable(PLACES[place_id], FOODS[food_id], MISUNDERSTANDINGS[mis_id], TASKS[task_id]):
                        combos.append((place_id, food_id, mis_id))
    return combos


if __name__ == "__main__":
    main()
