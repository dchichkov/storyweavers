#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260621T222722Z_seed1055341754_n10/food_bob_cobble_teamwork_moral_value_slice.py
==============================================================================================================

A small standalone storyworld for a slice-of-life domain built from the seed:
food, bob, cobble, teamwork, moral value.

Premise:
A child named Bob and a helper named Cobble are preparing food for a shared meal.
They face a simple problem: the food is not ready, the table is bare, and one
person is tempted to rush or take more than their share. The story turns on
teamwork, fairness, and a small practical fix that shows how helping each other
makes the day better.

The world keeps a tiny physical model with meters and emotional memes, and the
story is rendered from that changing state rather than from a frozen paragraph.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    scene: str
    table: str
    mood: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    noun: str
    obstacle: str
    teamwork_hint: str
    moral: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    needs_help: bool
    shareable: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    sense: int
    power: int
    text: str
    moral: str
    tags: set[str] = field(default_factory=set)


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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_hungry(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.meters["hungry"] < THRESHOLD:
            continue
        sig = ("hungry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["impatient"] += 1
        out.append("__hungry__")
    return out


def _r_shared(world: World) -> list[str]:
    out = []
    pantry = world.entities.get("food")
    table = world.entities.get("table")
    if not pantry or not table:
        return out
    if pantry.meters["ready"] < THRESHOLD or table.meters["set"] < THRESHOLD:
        return out
    sig = ("shared", pantry.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in world.characters():
        e.memes["pride"] += 1
    out.append("__shared__")
    return out


CAUSAL_RULES = [Rule("hungry", _r_hungry), Rule("shared", _r_shared)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend([s for s in sents if not s.startswith("__")])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(task: Task, food: Food, fix: Fix) -> bool:
    return task.id in TASKS and food.id in FOODS and fix.sense >= SENSE_MIN and food.needs_help


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def can_complete(task: Task, fix: Fix) -> bool:
    return fix.power >= task_power(task)


def task_power(task: Task) -> int:
    return 1 if task.id == "prepare" else 2


def predict_finish(world: World, task: Task, food: Food, fix: Fix) -> dict:
    sim = world.copy()
    _do_work(sim, sim.get("bob"), task, food, narrate=False)
    _apply_fix(sim, sim.get("cobble"), fix, narrate=False)
    return {
        "ready": sim.get("food").meters["ready"] >= THRESHOLD,
        "sharing": sim.get("food").meters["shared"] >= THRESHOLD,
    }


def _do_work(world: World, bob: Entity, task: Task, food: Food, narrate: bool = True) -> None:
    bob.memes["care"] += 1
    bob.meters["busy"] += 1
    world.get("food").meters["prepared"] += 1
    world.get("food").meters["ready"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        world.say(f"{bob.id} worked on the {task.noun} while the kitchen smelled like warm food.")


def _apply_fix(world: World, cobble: Entity, fix: Fix, narrate: bool = True) -> None:
    cobble.memes["helpful"] += 1
    world.get("table").meters["set"] += 1
    world.get("food").meters["shared"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        world.say(f"{cobble.id} used a calm, sensible fix: {fix.text}.")


def setup(world: World, bob: Entity, cobble: Entity, place: Place, food: Food, task: Task) -> None:
    bob.memes["hope"] += 1
    cobble.memes["hope"] += 1
    world.say(f"At {place.label}, {bob.id} and {cobble.id} turned a busy afternoon into a little teamwork story.")
    world.say(f"{place.scene} {place.table} {place.mood}. They wanted to {task.verb} the {food.label} together.")
    world.say(f"The plan was simple: make {food.phrase} ready and share it with everyone at the table.")


def tension(world: World, bob: Entity, cobble: Entity, task: Task, food: Food) -> None:
    bob.meters["hungry"] += 1
    cobble.meters["hungry"] += 1
    bob.memes["desire"] += 1
    world.say(f"But the {food.label} was not ready yet, and Bob's tummy rumbled louder.")
    world.say(f'"We should hurry," Bob said, staring at the {food.label}.')
    world.say(f'Cobble bit {cobble.pronoun("possessive")} lip. "{task.teamwork_hint}"')


def moral_turn(world: World, bob: Entity, cobble: Entity, task: Task, food: Food, fix: Fix) -> None:
    bob.memes["fairness"] += 1
    cobble.memes["fairness"] += 1
    world.say(f"Bob looked at the bowl, then at Cobble, and remembered the kinder choice.")
    world.say(f'"You are right," Bob said. "{task.moral} We can finish it together."')
    world.say(f'So they slowed down, took turns, and used {fix.text}.')
    world.say(f"The food got ready the honest way, and nobody had to grab more than their share.")


def ending(world: World, place: Place, food: Food, bob: Entity, cobble: Entity) -> None:
    bob.memes["joy"] += 1
    cobble.memes["joy"] += 1
    world.say(f"By the time they sat down, the table was full and the room felt calm again.")
    world.say(f"{food.label.capitalize()} sat in the middle, and Bob and Cobble smiled because helping had made it taste better.")
    world.say(f"Outside, the day stayed ordinary, but inside the meal felt like a small good deed done well.")


def tell(place: Place, food: Food, task: Task, fix: Fix) -> World:
    world = World()
    bob = world.add(Entity(id="Bob", kind="character", type="boy", role="helper"))
    cobble = world.add(Entity(id="Cobble", kind="character", type="thing", label="Cobble", role="helper"))
    table = world.add(Entity(id="table", kind="thing", type="thing", label="table"))
    pantry = world.add(Entity(id="food", kind="thing", type="thing", label=food.label))
    bob.meters["hungry"] = 0.0
    cobble.meters["hungry"] = 0.0
    table.meters["set"] = 0.0
    pantry.meters["ready"] = 0.0
    pantry.meters["shared"] = 0.0
    world.facts.update(place=place, food=food, task=task, fix=fix, bob=bob, cobble=cobble)
    setup(world, bob, cobble, place, food, task)
    world.para()
    tension(world, bob, cobble, task, food)
    _do_work(world, bob, task, food, narrate=True)
    world.para()
    moral_turn(world, bob, cobble, task, food, fix)
    _apply_fix(world, cobble, fix, narrate=True)
    world.para()
    ending(world, place, food, bob, cobble)
    return world


PLACES = {
    "kitchen": Place(
        id="kitchen",
        label="the kitchen",
        scene="The counters were bright, the sink was clean, and",
        table="The big table waited by the window.",
        mood="It made the room feel ready for supper.",
        tags={"home", "food"},
    ),
    "porch": Place(
        id="porch",
        label="the porch",
        scene="The wooden porch had a little table, and",
        table="The snack tray waited near the door.",
        mood="The air felt mild and friendly.",
        tags={"home", "food"},
    ),
    "garden_table": Place(
        id="garden_table",
        label="the garden table",
        scene="The garden was quiet, the birds were small, and",
        table="The low table stood under a striped cloth.",
        mood="Everything felt like a calm break in the day.",
        tags={"outdoor", "food"},
    ),
}

FOODS = {
    "soup": Food(id="soup", label="soup", phrase="a warm bowl of soup", needs_help=True, shareable=True, tags={"food"}),
    "sandwiches": Food(id="sandwiches", label="sandwiches", phrase="a plate of sandwiches", needs_help=True, shareable=True, tags={"food"}),
    "fruit": Food(id="fruit", label="fruit", phrase="a bowl of fruit", needs_help=True, shareable=True, tags={"food"}),
}

TASKS = {
    "prepare": Task(
        id="prepare",
        verb="prepare",
        noun="meal",
        obstacle="the food is still being arranged",
        teamwork_hint="If we split the work, it will be faster and fairer.",
        moral="Helping is better than taking a shortcut.",
        tags={"teamwork", "moral"},
    ),
    "serve": Task(
        id="serve",
        verb="serve",
        noun="food",
        obstacle="the plates are still empty",
        teamwork_hint="I can set the table while you carry the dish.",
        moral="Sharing the work helps everyone.",
        tags={"teamwork", "moral"},
    ),
}

FIXES = {
    "split_work": Fix(
        id="split_work",
        sense=3,
        power=2,
        text="split the work: Bob stirred while Cobble set the table",
        moral="Sharing jobs makes the task lighter.",
        tags={"teamwork"},
    ),
    "slow_down": Fix(
        id="slow_down",
        sense=3,
        power=2,
        text="slow down and take turns instead of rushing",
        moral="A careful pace can be kinder than a quick grab.",
        tags={"moral"},
    ),
    "ask_help": Fix(
        id="ask_help",
        sense=4,
        power=3,
        text="ask for help and lay everything out in a neat row",
        moral="Asking for help is a wise way to do a job well.",
        tags={"teamwork", "moral"},
    ),
    "snatch": Fix(
        id="snatch",
        sense=1,
        power=1,
        text="snatch a spoon and rush ahead",
        moral="This is not a good choice.",
        tags={"bad"},
    ),
}

BOB_NAMES = ["Bob", "Bobby", "Rob", "Ben"]
COBBLE_NAMES = ["Cobble"]
TRAITS = ["kind", "patient", "thoughtful", "careful"]


@dataclass
class StoryParams:
    place: str
    food: str
    task: str
    fix: str
    bob_name: str
    cobble_name: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for f in FOODS:
            for t in TASKS:
                for fx in FIXES:
                    if reasonableness_gate(TASKS[t], FOODS[f], FIXES[fx]):
                        combos.append((p, f, t, fx))
    return combos


def explain_rejection(task: Task, food: Food, fix: Fix) -> str:
    if fix.sense < SENSE_MIN:
        return f"(No story: the fix '{fix.id}' is too rude or careless for a moral teamwork story.)"
    if not food.needs_help:
        return f"(No story: {food.label} does not need teamwork in this tiny world.)"
    return "(No story: this combination does not fit the slice-of-life teamwork pattern.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a young child that includes the words "food", "Bob", and "Cobble".',
        f"Tell a gentle story about Bob and Cobble sharing work with {f['food'].label} in {f['place'].label}.",
        f"Write a moral-value story where Bob learns that helping and sharing are better than rushing ahead.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    food: Food = f["food"]
    place: Place = f["place"]
    task: Task = f["task"]
    fix: Fix = f["fix"]
    bob: Entity = f["bob"]
    cobble: Entity = f["cobble"]
    return [
        QAItem(
            question=f"What were Bob and Cobble trying to do with the {food.label}?",
            answer=f"They were trying to {task.verb} the {food.label} together so the meal would be ready for everyone. It took teamwork because one person alone would have been slower.",
        ),
        QAItem(
            question="Why did Bob need Cobble's help?",
            answer=f"Bob was hungry and wanted the {food.label} ready quickly, but rushing would have been unfair and messy. Cobble helped by keeping the work shared and calm.",
        ),
        QAItem(
            question=f"What change showed that Bob learned a moral lesson?",
            answer=f"Bob stopped trying to rush and chose to help instead. That showed he understood that helping and sharing are better than grabbing everything for himself.",
        ),
        QAItem(
            question=f"How did {fix.id.replace('_', ' ')} help at {place.label}?",
            answer=f"It helped by making the job shared and orderly, so the food could be finished without arguments. The meal got ready because they worked side by side.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["food"].tags) | set(f["task"].tags) | set(f["fix"].tags) | {"food"}
    items = []
    if "food" in tags:
        items.append(QAItem(
            question="What is food?",
            answer="Food is something people eat to feel full and have energy. It can be cooked, served, and shared at a meal.",
        ))
    if "teamwork" in tags:
        items.append(QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other do a job. Each person does a part, and together they finish more easily.",
        ))
    if "moral" in tags:
        items.append(QAItem(
            question="What is a moral value?",
            answer="A moral value is a kind of good choice, like being fair, helpful, or honest. It guides people toward kinder behavior.",
        ))
    return items


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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", food="soup", task="prepare", fix="split_work", bob_name="Bob", cobble_name="Cobble", trait="kind"),
    StoryParams(place="porch", food="sandwiches", task="serve", fix="ask_help", bob_name="Bob", cobble_name="Cobble", trait="patient"),
    StoryParams(place="garden_table", food="fruit", task="prepare", fix="slow_down", bob_name="Bob", cobble_name="Cobble", trait="thoughtful"),
]


ASP_RULES = r"""
valid(P,F,T,X) :- place(P), food(F), task(T), fix(X), sense(X,S), sense_min(M), S >= M, needs_help(F).
outcome(teamwork) :- valid(_,_,_,_).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("sense_min", SENSE_MIN)]
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for fid, food in FOODS.items():
        lines.append(asp.fact("food", fid))
        if food.needs_help:
            lines.append(asp.fact("needs_help", fid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for xid, fx in FIXES.items():
        lines.append(asp.fact("fix", xid))
        lines.append(asp.fact("sense", xid, fx.sense))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    try:
        if set(asp_valid_combos()) != set(valid_combos()):
            print("MISMATCH between ASP and Python valid_combos().")
            rc = 1
        else:
            print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
        smoke = generate(resolve_params(argparse.Namespace(place=None, food=None, task=None, fix=None, seed=None), random.Random(7)))
        if not smoke.story.strip():
            print("MISMATCH: empty story")
            rc = 1
        else:
            print("OK: generate() smoke test produced a story.")
    except Exception:
        traceback.print_exc()
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about Bob, Cobble, food, teamwork, and a moral lesson.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--fix", choices=FIXES)
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
              and (args.task is None or c[2] == args.task)
              and (args.fix is None or c[3] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, food, task, fix = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        food=food,
        task=task,
        fix=fix,
        bob_name="Bob",
        cobble_name="Cobble",
        trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.food not in FOODS or params.task not in TASKS or params.fix not in FIXES:
        raise StoryError("Invalid parameters for this storyworld.")
    place = PLACES[params.place]
    food = FOODS[params.food]
    task = TASKS[params.task]
    fix = FIXES[params.fix]
    if not reasonableness_gate(task, food, fix):
        raise StoryError(explain_rejection(task, food, fix))
    world = tell(place, food, task, fix)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
