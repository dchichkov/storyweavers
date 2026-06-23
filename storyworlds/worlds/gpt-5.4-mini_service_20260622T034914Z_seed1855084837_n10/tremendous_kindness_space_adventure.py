#!/usr/bin/env python3
"""
storyworlds/worlds/tremendous_kindness_space_adventure.py
=========================================================

A standalone story world for a small Space Adventure about kindness in space:
a tiny crew faces a practical problem, chooses a kind fix, and ends with a
clear image of what changed. The simulation tracks physical meters and emotional
memes so the prose grows from state instead of from a frozen template.

Initial source tale used to build the world model:
---
Two kids, Nova and Pip, were on a little moon base with their robot friend,
Beacon. They were getting ready to launch a tiny rescue ship to deliver seed
kits to a sleepy outpost. Nova loved the silver pilot gloves, because they
made her feel ready for a tremendous adventure. Pip loved the bright lantern
badge on his suit, because it glowed like a tiny star.

At the launch pad, Nova saw that Beacon's battery was low and that the cargo
crates were too heavy for one robot to push alone. Pip wanted to rush ahead,
but Nova stopped and said they should be kind and help Beacon first. They moved
the heavy crates together, shared their snack water with Beacon's cooling cup,
and checked the battery dock. Beacon's battery rose, the cargo cleared the ramp,
and the ship's launch light turned green.

Beacon blinked happily and said the best part of the mission was not the
sticker on the ship or the shiny gloves. It was that Nova and Pip helped each
other and helped a friend when it mattered. Then the tiny ship lifted off under
the bright moon, carrying seed kits, warm smiles, and a tremendous feeling of
kindness.

Causal state updates:
---
    help heavy helper                      -> helper.meters["load"] -= 1 ; helper.memes["relief"] += 1
    share water with low battery helper    -> helper.meters["battery"] += 1 ; helper.memes["gratitude"] += 1
    move cargo together                    -> cargo.meters["blocked"] -> 0 ; crew.memes["teamwork"] += 1
    kindness choice                        -> child.memes["kindness"] += 1 ; child.memes["joy"] += 1
    launch cleared                         -> ship.meters["ready"] += 1 ; crew.memes["pride"] += 1

Scripted emotional beats:
---
    setup                                  -> crew joy +1
    helper needs aid                        -> crew concern +1
    selfish rush rejected                  -> crew frustration +1
    kind plan accepted                     -> crew kindness +1 ; tension -> 0
    mission succeeds                       -> crew joy +1 ; crew pride +1
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
    phrase: str = ""
    role: str = ""
    owner: str = ""
    place: str = ""
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, object] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    sky: str
    afford: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    danger: str
    zone: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    owners: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


def _r_load_relief(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("beacon")
    if helper.meters["load"] < THRESHOLD:
        return out
    sig = ("load",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.meters["load"] -= 1
    helper.memes["relief"] += 1
    out.append("Beacon could breathe easier.")
    return out


def _r_share_water(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("beacon")
    if helper.meters["battery"] >= THRESHOLD:
        return out
    sig = ("water",)
    if sig in world.fired:
        return out
    if world.facts.get("shared_water", False):
        world.fired.add(sig)
        helper.meters["battery"] += 1
        helper.memes["gratitude"] += 1
        out.append("The shared water helped Beacon recharge a little.")
    return out


def _r_launch_ready(world: World) -> list[str]:
    ship = world.get("ship")
    cargo = world.get("cargo")
    crew = [world.get("nova"), world.get("pip")]
    if cargo.meters["blocked"] >= THRESHOLD:
        return []
    sig = ("ready",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ship.meters["ready"] += 1
    for child in crew:
        child.memes["pride"] += 1
    return ["The launch pad turned green."]


CAUSAL_RULES = [
    Rule("load_relief", "physical", _r_load_relief),
    Rule("share_water", "physical", _r_share_water),
    Rule("launch_ready", "physical", _r_launch_ready),
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
            world.say(s)
    return produced


def needy_helper(world: World, helper: Entity) -> bool:
    return helper.meters["load"] >= THRESHOLD or helper.meters["battery"] < THRESHOLD


def valid_task(place: Place, task: Task, item: Item) -> bool:
    return task.id in place.afford and item.region in task.zone


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for pid, place in PLACES.items():
        for tid, task in TASKS.items():
            for iid, item in ITEMS.items():
                if valid_task(place, task, item):
                    combos.append((pid, tid, iid))
    return combos


@dataclass
class StoryParams:
    place: str
    task: str
    item: str
    name1: str
    name2: str
    seed: Optional[int] = None


PLACES = {
    "moon_base": Place(id="moon_base", label="the moon base", sky="the bright moon",
                       afford={"cargo", "help", "launch"}, tags={"moon", "space"}),
    "orbital_dock": Place(id="orbital_dock", label="the orbital dock", sky="the stars",
                          afford={"cargo", "help", "launch"}, tags={"orbit", "space"}),
    "red_hill": Place(id="red_hill", label="the red hill station", sky="the dusty red sky",
                      afford={"cargo", "help", "launch"}, tags={"planet", "space"}),
}

TASKS = {
    "cargo": Task(id="cargo", verb="move the cargo", gerund="moving cargo", danger="blocked",
                  zone={"floor"}, tags={"cargo", "heavy"}),
    "help": Task(id="help", verb="help the helper", gerund="helping", danger="tired",
                 zone={"floor", "battery", "hands"}, tags={"help", "kindness"}),
    "launch": Task(id="launch", verb="launch the ship", gerund="launching", danger="stuck",
                   zone={"pad"}, tags={"launch", "ship"}),
}

ITEMS = {
    "crate": Item(id="crate", label="cargo crates", phrase="the heavy cargo crates", region="floor",
                  owners={"beacon"}, tags={"cargo", "heavy"}),
    "battery": Item(id="battery", label="battery dock", phrase="the battery dock", region="battery",
                    owners={"beacon"}, tags={"battery", "helper"}),
    "ramp": Item(id="ramp", label="launch ramp", phrase="the launch ramp", region="pad",
                 owners={"ship"}, tags={"launch", "ship"}),
}

GIRL_NAMES = ["Nova", "Mira", "Luna", "Aria", "Zara", "Ivy"]
BOY_NAMES = ["Pip", "Jett", "Orin", "Kian", "Sol", "Tao"]
TRAITS = ["kind", "gentle", "brave", "patient", "helpful"]


def explain_rejection(place: Place, task: Task, item: Item) -> str:
    return f"(No story: {task.verb} does not fit {item.phrase} at {place.label}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: tremendous kindness on a space mission.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--item", choices=ITEMS)
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
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, item = rng.choice(sorted(combos))
    n1 = rng.choice(GIRL_NAMES)
    n2 = rng.choice([n for n in BOY_NAMES if n != n1] + [n for n in GIRL_NAMES if n != n1])
    return StoryParams(place=place, task=task, item=item, name1=n1, name2=n2)


def story_setup(world: World, nova: Entity, pip: Entity, beacon: Entity, task: Task, item: Entity) -> None:
    nova.memes["joy"] += 1
    pip.memes["joy"] += 1
    world.say(f"Nova and Pip were working at {world.place.label}. Beacon shone beside them.")
    world.say(f"They were getting ready to {task.verb}, and it felt tremendous to look up at {world.place.sky}.")


def helper_needs_kindness(world: World, beacon: Entity) -> None:
    beacon.meters["load"] += 1
    beacon.meters["battery"] = 0.0
    world.get("nova").memes["concern"] += 1
    world.get("pip").memes["concern"] += 1
    world.say("But Beacon was stuck with too much load and a low battery.")
    world.say("Nova saw the trouble and thought kindness would matter more than speed.")


def reject_rush(world: World, pip: Entity) -> None:
    pip.memes["frustration"] += 1
    world.say("Pip wanted to rush ahead, but the crates were still in the way.")
    world.say("Nova said they should help first, not hurry past a friend in need.")


def choose_kindness(world: World, nova: Entity, pip: Entity, beacon: Entity, cargo: Entity) -> None:
    nova.memes["kindness"] += 1
    pip.memes["kindness"] += 1
    nova.memes["joy"] += 1
    pip.memes["joy"] += 1
    world.facts["shared_water"] = True
    cargo.meters["blocked"] = 0.0
    beacon.meters["load"] = 0.0
    world.say("So they lifted the cargo together and shared their water with Beacon.")
    world.say("That small kindness was tremendous in the quiet of space.")
    propagate(world, narrate=True)


def finish_launch(world: World, nova: Entity, pip: Entity, beacon: Entity, ship: Entity) -> None:
    ship.meters["ready"] += 1
    nova.memes["joy"] += 1
    pip.memes["joy"] += 1
    beacon.memes["gratitude"] += 1
    world.say("Beacon blinked happily and the ship hummed to life.")
    world.say("Together they watched the tiny rescue ship lift off under the moon, bright and safe.")


def tell(place: Place, task: Task, item_cfg: Item, name1: str, name2: str) -> World:
    world = World(place)
    nova = world.add(Entity(id="nova", kind="character", type="girl", label=name1, role="helper"))
    pip = world.add(Entity(id="pip", kind="character", type="boy", label=name2, role="helper"))
    beacon = world.add(Entity(id="beacon", kind="character", type="robot", label="Beacon", role="helper"))
    cargo = world.add(Entity(id="cargo", type="thing", label=item_cfg.label, phrase=item_cfg.phrase, place="floor"))
    ship = world.add(Entity(id="ship", type="thing", label="ship", phrase="the tiny rescue ship", place="pad"))
    story_setup(world, nova, pip, beacon, task, cargo)
    world.para()
    helper_needs_kindness(world, beacon)
    reject_rush(world, pip)
    world.para()
    choose_kindness(world, nova, pip, beacon, cargo)
    finish_launch(world, nova, pip, beacon, ship)
    world.facts.update(nova=nova, pip=pip, beacon=beacon, cargo=cargo, ship=ship, task=task, place=place, item=item_cfg)
    return world


ASP_RULES = r"""
blocked(C) :- cargo(C), needs_help(C).
kind_choice(N) :- crew(N), chooses_kindness(N).
launch_ready :- cargo(C), not blocked(C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for iid in ITEMS:
        lines.append(asp.fact("cargo", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    prog = asp_program("#show launch_ready/0.")
    model = asp.one_model(prog)
    ok = bool(model)
    sample = generate(resolve_params(argparse.Namespace(place=None, task=None, item=None), random.Random(777)))
    if not sample.story or not ok:
        print("Verification failed.")
        return 1
    print("OK: ASP and story generation smoke test passed.")
    return 0


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle space adventure story for a young child that uses the word "tremendous" and shows kindness helping a robot named {f["beacon"].label}.',
        f"Tell a story where {f['nova'].label} and {f['pip'].label} help their robot friend at {f['place'].label} instead of rushing the mission.",
        f'Write a tiny space rescue story about sharing, teamwork, and a tremendous feeling of kindness.'
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    nova = f["nova"]
    pip = f["pip"]
    beacon = f["beacon"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who helped Beacon at {place.label}?",
            answer=f"{nova.label} and {pip.label} helped Beacon. They did not leave the robot alone when the load got heavy."
        ),
        QAItem(
            question=f"Why did the crew choose kindness instead of rushing?",
            answer=f"They saw that Beacon had too much load and a low battery. Helping first made the mission safer and kept the launch from getting stuck."
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The cargo was cleared, Beacon felt better, and the launch light turned green. The ending shows that kindness made the whole mission work."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means helping, caring, and doing something gentle for someone else."
        ),
        QAItem(
            question="What is a launch pad?",
            answer="A launch pad is the place where a ship waits before it takes off into space."
        ),
        QAItem(
            question="What does tremendous mean?",
            answer="Tremendous means very, very big or very strong."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.task not in TASKS or params.item not in ITEMS:
        raise StoryError("Invalid parameters.")
    world = tell(PLACES[params.place], TASKS[params.task], ITEMS[params.item], params.name1, params.name2)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="moon_base", task="help", item="battery", name1="Nova", name2="Pip"),
    StoryParams(place="orbital_dock", task="cargo", item="crate", name1="Mira", name2="Sol"),
    StoryParams(place="red_hill", task="launch", item="ramp", name1="Luna", name2="Tao"),
]


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
        print(asp_program("#show launch_ready/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
