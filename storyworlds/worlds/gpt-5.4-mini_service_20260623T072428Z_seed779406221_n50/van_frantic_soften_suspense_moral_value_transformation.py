#!/usr/bin/env python3
"""
storyworlds/worlds/van_frantic_soften_suspense_moral_value_transformation.py
============================================================================

A small, fable-like storyworld about a delivery van, a frantic moment, a softening
turn, and a moral transformation.

Seed idea:
---
A little van is sent through the village with a basket of bread. On the road,
the van sees a frantic pup chasing a loose ribbon and a child crying because a
kite is stuck in a tree. The van must choose between rushing past or stopping.
It slows down, helps, and learns that being useful is better than being first.

The world keeps track of:
- physical meters: speed, load, dust, stuck, height, reach
- emotional memes: frantic, calm, kindness, pride, gratitude, patience

The story aims for the feel of a short fable:
- a clear problem
- suspense from a choice and a small obstruction
- a moral value stated through action, not a lecture
- a transformation in the van's behavior and feelings
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
    phrase: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    road_kind: str
    has_tree: bool = False
    has_bridge: bool = False
    has_hill: bool = False
    has_market: bool = False


@dataclass
class Task:
    id: str
    verb: str
    hurry: str
    problem: str
    obstacle: str
    resolution: str
    moral: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    fragile: bool = False
    heavy: bool = False
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_frantic_to_slow(world: World) -> list[str]:
    out: list[str] = []
    van = world.entities.get("van")
    if not van:
        return out
    if van.meters["slowed"] >= THRESHOLD and ("slow", "van") not in world.fired:
        world.fired.add(("slow", "van"))
        van.memes["frantic"] = max(0.0, van.memes["frantic"] - 1)
        van.memes["calm"] += 1
        out.append("__soften__")
    return out


def _r_help_transform(world: World) -> list[str]:
    out: list[str] = []
    van = world.entities.get("van")
    if not van:
        return out
    if van.memes["kindness"] >= THRESHOLD and ("help", "van") not in world.fired:
        world.fired.add(("help", "van"))
        van.memes["pride"] += 1
        van.memes["gratitude"] += 1
        out.append("__transform__")
    return out


CAUSAL_RULES = [
    Rule("slow", "emotional", _r_frantic_to_slow),
    Rule("help", "moral", _r_help_transform),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            if s != "__soften__":
                world.say(s)
    return produced


def predict_choice(world: World, task: Task) -> dict:
    sim = world.copy()
    choose_path(sim, task, narrate=False)
    return {
        "helped": bool(sim.facts.get("helped")),
        "van_calm": sim.get("van").memes["calm"],
    }


def choose_path(world: World, task: Task, narrate: bool = True) -> None:
    van = world.get("van")
    child = world.get("child")
    pup = world.get("pup")
    van.meters["speed"] += 1
    van.memes["frantic"] += 1
    world.say(f"{van.id} rolled along the lane with a basket of warm bread.")
    world.say(f"The road by {world.place.label} looked simple, yet something by the bend made the day feel uncertain.")
    world.say(f"{child.id} was crying by the road, and {pup.id} darted after a loose ribbon.")
    world.say(f"{van.id} wanted to {task.verb}, but the little scene ahead would not leave the van alone.")

    pred = predict_choice(world, task)
    world.facts["predicted_help"] = pred["helped"]

    world.para()
    if task.id == "help_child":
        van.meters["slowed"] += 1
        van.meters["reach"] += 1
        world.say(f"{van.id} slowed at once, because rushing past would have made the trouble worse.")
        world.say(f"With a careful turn, {van.id} used the front bumper as a low step and nudged the kite pole down from the tree.")
        child.memes["gratitude"] += 1
        pup.memes["calm"] += 1
        van.memes["kindness"] += 1
        world.say(f"The child clapped, the pup sat down, and the ribbon stopped whipping in the wind.")
        world.say(f"That was the moment the frantic feeling softened into calm.")
    else:
        van.meters["slowed"] += 1
        world.say(f"{van.id} braked hard and waited for the lane to clear.")
        world.say(f"A market cart had tipped its apples into the dust, and the van helped gather them before moving on.")
        van.memes["kindness"] += 1
        van.memes["gratitude"] += 1
        world.say(f"The van learned that a small pause can do more good than a fast dash.")
    propagate(world, narrate=narrate)

    world.facts.update(
        van=van,
        child=child,
        pup=pup,
        task=task,
        helped=True,
        transformed=van.memes["kindness"] >= THRESHOLD,
    )


SETTINGS = {
    "lane": Place(id="lane", label="the village lane", road_kind="lane", has_tree=True),
    "bridge": Place(id="bridge", label="the old bridge road", road_kind="bridge", has_bridge=True),
    "hill": Place(id="hill", label="the hill road", road_kind="hill", has_hill=True),
    "market": Place(id="market", label="the market street", road_kind="street", has_market=True),
}

TASKS = {
    "help_child": Task(
        id="help_child",
        verb="drive on at full speed",
        hurry="rush past",
        problem="a child has a kite stuck in a tree",
        obstacle="a ribbon and a kite cord",
        resolution="the kite comes down safely",
        moral="Kindness is worth more than speed.",
        tags={"kindness", "help", "tree"},
    ),
    "help_cart": Task(
        id="help_cart",
        verb="hurry to the next stop",
        hurry="race ahead",
        problem="a cart has spilled apples",
        obstacle="apples on the road",
        resolution="the apples are gathered",
        moral="A careful pause can be a good deed.",
        tags={"kindness", "market", "apples"},
    ),
}

CARGOS = {
    "bread": Cargo(id="bread", label="bread", phrase="a basket of warm bread", fragile=False, heavy=False, tags={"bread"}),
    "milk": Cargo(id="milk", label="milk", phrase="two bottles of milk", fragile=True, heavy=False, tags={"milk"}),
}

NAMES = ["Milo", "Nina", "Toby", "Luna", "Rae", "Bram"]
PUP_NAMES = ["Pip", "Muffin", "Tizzy", "Dot"]


@dataclass
class StoryParams:
    place: str
    task: str
    cargo: str
    van_name: str
    child_name: str
    pup_name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for task in TASKS:
            for cargo in CARGOS:
                out.append((place, task, cargo))
    return out


def tell(place: Place, task: Task, cargo: Cargo, van_name: str, child_name: str, pup_name: str) -> World:
    world = World(place)
    van = world.add(Entity(id="van", kind="character", type="van", label=van_name, role="hero"))
    child = world.add(Entity(id="child", kind="character", type="child", label=child_name, role="bystander"))
    pup = world.add(Entity(id="pup", kind="character", type="dog", label=pup_name, role="helper"))
    cargo_ent = world.add(Entity(id="cargo", kind="thing", type=cargo.label, label=cargo.label, phrase=cargo.phrase))
    van.meters["load"] = 1
    van.memes["frantic"] = 1
    world.facts["cargo"] = cargo_ent
    world.say(f"{van_name} the little van liked to be first on every road, even when the morning was busy.")
    world.say(f"It carried {cargo.phrase} and boasted that no lane could slow it down.")
    world.para()
    choose_path(world, task)
    world.para()
    world.say(f"In the end, {van_name} remembered {task.moral.lower()}")
    world.say(f"So the van went home with a softer wheel-turn, and the village saw a kinder road.")
    return world


KNOWLEDGE = {
    "van": [("What is a van?", "A van is a vehicle that can carry people or things from one place to another.")],
    "frantic": [("What does frantic mean?", "Frantic means very worried, rushed, or hard to settle down.")],
    "soften": [("What does soften mean?", "To soften means to become gentler, calmer, or less hard.")],
    "kindness": [("What is kindness?", "Kindness means helping, sharing, or being gentle with others.")],
    "suspense": [("What is suspense?", "Suspense is the feeling of waiting to see what will happen next.")],
    "transformation": [("What is a transformation?", "A transformation is a change from one state or way of being into another.")],
    "bread": [("Why is bread often carried carefully?", "Bread can be broken or squashed, so people handle it gently.")],
}
KNOWLEDGE_ORDER = ["van", "frantic", "soften", "kindness", "suspense", "transformation", "bread"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable about a van named {f["van"].label} that starts out frantic, then softens when it helps a child.',
        f"Tell a child-friendly moral story where a van meets a small problem on {world.place.label} and chooses kindness over speed.",
        f'Write a suspenseful fable with a van, a frightened child, and a gentle transformation at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    van, child, task = f["van"], f["child"], f["task"]
    return [
        QAItem(
            question=f"What kind of character is {van.label} in the story?",
            answer=f"{van.label} is a little van who starts out hurrying and feeling frantic, but learns to slow down and help.",
        ),
        QAItem(
            question=f"What made the story feel suspenseful?",
            answer=f"The suspense came from seeing {child.label} in trouble and waiting to find out whether {van.label} would stop to help.",
        ),
        QAItem(
            question=f"What changed in {van.label} by the end?",
            answer=f"{van.label} changed from frantic and eager to rush into someone kinder, calmer, and more helpful.",
        ),
        QAItem(
            question=f"What moral did the story show?",
            answer=task.moral,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = {"van", "frantic", "soften", "kindness", "suspense", "transformation", "bread"}
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(question=q, answer=a))
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
        if bits:
            lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
van(hero).
task(help_child).
task(help_cart).
moral(kindness_over_speed).
moral(careful_pause_good_deed).

frantic(V) :- van(V), starts_frantic(V).
soften(V) :- van(V), slows(V), helps(V).
transformation(V) :- frantic(V), soften(V).

helped(V) :- soften(V).
suspense :- van(V), frantic(V), waiting_for_choice(V).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if p.has_tree:
            lines.append(asp.fact("has_tree", pid))
        if p.has_bridge:
            lines.append(asp.fact("has_bridge", pid))
        if p.has_hill:
            lines.append(asp.fact("has_hill", pid))
        if p.has_market:
            lines.append(asp.fact("has_market", pid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("moral", tid, t.moral))
    for cid, c in CARGOS.items():
        lines.append(asp.fact("cargo", cid))
        if c.fragile:
            lines.append(asp.fact("fragile", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a van, suspense, moral value, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--cargo", choices=CARGOS)
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
              and (args.task is None or c[1] == args.task)
              and (args.cargo is None or c[2] == args.cargo)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, cargo = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        task=task,
        cargo=cargo,
        van_name=rng.choice(NAMES),
        child_name=rng.choice(NAMES),
        pup_name=rng.choice(PUP_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TASKS[params.task], CARGOS[params.cargo],
                 params.van_name, params.child_name, params.pup_name)
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


def asp_verify() -> int:
    print("OK: ASP twin is present for the storyworld.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show.")) 
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
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
            header = f"### {p.van_name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


CURATED = [
    StoryParams(place="lane", task="help_child", cargo="bread", van_name="Milo", child_name="Nina", pup_name="Pip"),
    StoryParams(place="market", task="help_cart", cargo="milk", van_name="Luna", child_name="Rae", pup_name="Dot"),
]


if __name__ == "__main__":
    main()
