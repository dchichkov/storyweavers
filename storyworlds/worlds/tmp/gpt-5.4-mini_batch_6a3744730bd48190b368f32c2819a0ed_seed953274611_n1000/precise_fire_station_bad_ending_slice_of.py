#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/precise_fire_station_bad_ending_slice_of.py
===========================================================================

A small storyworld about a careful day at a fire station.

Premise:
- A child or station helper is asked to do a precise little task.
- The task seems ordinary, slice-of-life simple: charts, hoses, lunch, polish, labels.
- Something goes wrong because one careful step is skipped or an unsafe choice is made.
- The ending is bad: a mess, a delay, or a minor loss that cannot be fixed in time.

The story stays grounded in a single fire station setting, with concrete tools,
rooms, and routines. The prose should feel like a child-facing slice-of-life tale,
but the ending should land badly and clearly show what changed.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Task:
    id: str
    verb: str
    object_phrase: str
    precise_tool: str
    sloppy_tool: str
    risk: str
    consequence: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Place:
    id: str
    room: str
    detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    power: int
    sense: int
    text: str
    fail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str = "station"
    task: str = "hose_check"
    response: str = "quick_fix"
    helper_name: str = "Milo"
    helper_gender: str = "boy"
    chief_name: str = "Ada"
    chief_gender: str = "girl"
    chief_role: str = "captain"
    seed: Optional[int] = None


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
        c = World()
        c.entities = json.loads(json.dumps({k: {"id": v.id, "kind": v.kind, "type": v.type, "label": v.label, "role": v.role, "attrs": v.attrs, "meters": dict(v.meters), "memes": dict(v.memes)} for k, v in self.entities.items()}))
        # Rebuild as Entity objects
        rebuilt: dict[str, Entity] = {}
        for k, d in c.entities.items():
            e = Entity(id=d["id"], kind=d["kind"], type=d["type"], label=d["label"], role=d["role"], attrs=d["attrs"])
            e.meters.update(d["meters"])
            e.memes.update(d["memes"])
            rebuilt[k] = e
        c.entities = rebuilt
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["spill"] >= THRESHOLD:
            sig = ("spill", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            if "floor" in world.entities:
                world.get("floor").meters["mess"] += 1
            if "chief" in world.entities:
                world.get("chief").memes["stress"] += 1
            out.append("__spill__")
    return out


def _r_delay(world: World) -> list[str]:
    out: list[str] = []
    if world.get("truck").meters["delay"] >= THRESHOLD and ("delay",) not in world.fired:
        world.fired.add(("delay",))
        world.get("truck").meters["ready"] = 0
        world.get("chief").memes["worry"] += 1
        out.append("The truck was not ready when it should have been.")
    return out


def _r_late(world: World) -> list[str]:
    out: list[str] = []
    if world.get("clock").meters["late"] >= THRESHOLD and ("late",) not in world.fired:
        world.fired.add(("late",))
        world.get("helper").memes["guilt"] += 1
        out.append("The room went quiet, and the mistake felt bigger than the table.")
    return out


CAUSAL_RULES = [_r_spill, _r_delay, _r_late]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule(world)
            if s:
                changed = True
                produced.extend([x for x in s if not x.startswith("__")])
    if narrate:
        for line in produced:
            world.say(line)
    return produced


TASKS = {
    "hose_check": Task(
        id="hose_check",
        verb="check the hose coil",
        object_phrase="the hose coil",
        precise_tool="a red tag and a clipboard",
        sloppy_tool="a wet glove",
        risk="the hose would get twisted and slow",
        consequence="the truck would leave late",
        tags={"hose", "truck", "precise"},
    ),
    "label_shelf": Task(
        id="label_shelf",
        verb="sort the shelf labels",
        object_phrase="the shelf labels",
        precise_tool="a ruler and a marker",
        sloppy_tool="a crayon",
        risk="the labels would smear and nobody could find the gear fast",
        consequence="the station would waste time",
        tags={"labels", "gear", "precise"},
    ),
    "pack_snacks": Task(
        id="pack_snacks",
        verb="pack the snack bins",
        object_phrase="the snack bins",
        precise_tool="a list and a pencil",
        sloppy_tool="a sticky spoon",
        risk="the bins would end up wrong and the crew would miss lunch",
        consequence="the crew would be tired and slow",
        tags={"snacks", "kitchen", "precise"},
    ),
}

PLACES = {
    "station": Place(
        id="station",
        room="the fire station",
        detail="The fire station was tidy in the morning, with boots by the wall and charts on the desk.",
        tags={"station", "slice_of_life"},
    )
}

RESPONSES = {
    "quick_fix": Response(
        id="quick_fix",
        power=1,
        sense=3,
        text="tied the loose part down, but the damage had already spread",
        fail="tried to fix it quickly, but the delay was already too long",
        tags={"fix", "bad_ending"},
    ),
    "slow_fix": Response(
        id="slow_fix",
        power=2,
        sense=2,
        text="went back to check every step, but that only made them later",
        fail="checked everything again, and the truck still rolled out late",
        tags={"fix", "bad_ending"},
    ),
    "call_help": Response(
        id="call_help",
        power=0,
        sense=1,
        text="called for help, but it did not solve the problem in time",
        fail="called for help, but it was too late to help",
        tags={"bad_choice"},
    ),
}

NAMES_GIRL = ["Ada", "Mina", "Lina", "Tess", "Ivy", "Nora"]
NAMES_BOY = ["Milo", "Owen", "Finn", "Ben", "Leo", "Noah"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid in PLACES:
        for tid in TASKS:
            for rid, resp in RESPONSES.items():
                if resp.sense >= 2:
                    combos.append((pid, tid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A precise fire-station slice-of-life storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--response", choices=RESPONSES)
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
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError("That response is too careless for this story.")
    choices = [c for c in valid_combos()
               if (args.place is None or c[0] == args.place)
               and (args.task is None or c[1] == args.task)
               and (args.response is None or c[2] == args.response)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, response = rng.choice(sorted(choices))
    gender = rng.choice(["girl", "boy"])
    helper_name = rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    chief_gender = "girl"
    chief_name = rng.choice(NAMES_GIRL)
    return StoryParams(place=place, task=task, response=response, helper_name=helper_name, helper_gender=gender, chief_name=chief_name, chief_gender=chief_gender)


def narrate_task(world: World, helper: Entity, chief: Entity, task: Task) -> None:
    helper.memes["pride"] += 1
    world.say(f"At {PLACES['station'].room}, {helper.id} had a small job to do: {task.verb}.")
    world.say(f"{PLACES['station'].detail} On the desk lay {task.precise_tool}, waiting for a careful hand.")
    world.say(f'"Please be {task.id.replace("_", " ")}," {chief.id} said. "The station runs best when things are done the precise way."')


def tempt_sloppy(world: World, helper: Entity, task: Task) -> None:
    helper.memes["impulse"] += 1
    world.say(f"{helper.id} looked at {task.precise_tool}, then at {task.sloppy_tool}, and thought the second one would be faster.")
    world.say(f'"I can do it my own way," {helper.id} said, and reached for {task.sloppy_tool}.')


def bad_turn(world: World, helper: Entity, chief: Entity, task: Task) -> None:
    helper.meters["spill"] += 1
    world.get("clock").meters["late"] += 1
    propagate(world, narrate=False)
    world.say(f"The {task.object_phrase} slipped, and {task.risk}.")
    world.say(f"{chief.id} came over, but by then {task.consequence}.")


def bad_ending(world: World, helper: Entity, chief: Entity, task: Task, response: Response) -> None:
    world.get("truck").meters["delay"] += 1
    propagate(world, narrate=False)
    world.say(f"{chief.id} {response.fail}.")
    world.say("Outside, the truck lights blinked once, then the engine finally started.")
    world.say("The crew watched it leave a little too late, and the whole station felt the loss of that one missed minute.")


def tell(params: StoryParams) -> World:
    world = World()
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper"))
    chief = world.add(Entity(id=params.chief_name, kind="character", type=params.chief_gender, role="chief", label="the captain"))
    world.add(Entity(id="clock", type="thing", label="the clock"))
    world.add(Entity(id="truck", type="thing", label="the truck"))
    world.add(Entity(id="floor", type="thing", label="the floor"))

    task = TASKS[params.task]
    response = RESPONSES[params.response]

    narrate_task(world, helper, chief, task)
    world.para()
    tempt_sloppy(world, helper, task)
    bad_turn(world, helper, chief, task)
    world.para()
    bad_ending(world, helper, chief, task, response)

    world.facts.update(helper=helper, chief=chief, task=task, response=response, params=params, outcome="bad")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task: Task = f["task"]
    return [
        f'Write a slice-of-life story set in a fire station that includes the word "precise" and ends badly.',
        f"Tell a small fire-station story where {f['helper'].id} tries to do {task.verb}, but the careful way matters and the ending goes wrong.",
        f"Write a child-friendly bad-ending story about a station helper and {task.object_phrase} with a calm, everyday tone.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    helper: Entity = f["helper"]
    chief: Entity = f["chief"]
    task: Task = f["task"]
    response: Response = f["response"]
    return [
        ("Where is the story set?", "It is set in a fire station, where the crew keeps tools, charts, and the truck ready."),
        ("What did the helper try to do?", f"{helper.id} tried to {task.verb}, but wanted to do it in a sloppy way instead of the precise one."),
        ("Why was the chief upset?", f"The chief was upset because the wrong choice made the job slow and messy. That meant the truck was late, and late is dangerous in a fire station."),
        ("How did the story end?", f"It ended badly. {chief.id} could not undo the delay, so the truck left too late and the station lost precious time."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does a fire station do?", "A fire station keeps firefighters, tools, and trucks ready so they can help quickly when there is a fire."),
        ("Why is being precise important at a fire station?", "Being precise helps people do jobs the right way and fast. At a fire station, small mistakes can waste time when every minute matters."),
        ("What is a fire truck for?", "A fire truck carries firefighters and equipment to a fire so they can help put it out."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"  {e.id}: meters={meters} memes={memes} role={e.role} type={e.type}")
    out.append(f"  fired={sorted({r[0] for r in world.fired})}")
    return "\n".join(out)


ASP_RULES = r"""
ready_story(P,T,R) :- place(P), task(T), response(R), sensible(R).
sensible(R) :- response(R), sense(R,S), min_sense(M), S >= M.
bad_end(P,T,R) :- ready_story(P,T,R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("min_sense", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show ready_story/3."))
    return sorted(set(asp.atoms(model, "ready_story")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as e:
        print(f"FAILED: smoke test crashed: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.task not in TASKS:
        raise StoryError("Unknown task.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
    task = TASKS[params.task]
    response = RESPONSES[params.response]
    if response.sense < 2:
        raise StoryError("That response is too careless for this story.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show ready_story/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible stories:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="station", task="hose_check", response="quick_fix", helper_name="Milo", helper_gender="boy", chief_name="Ada", chief_gender="girl"),
            StoryParams(place="station", task="label_shelf", response="slow_fix", helper_name="Nora", helper_gender="girl", chief_name="Tess", chief_gender="girl"),
            StoryParams(place="station", task="pack_snacks", response="quick_fix", helper_name="Finn", helper_gender="boy", chief_name="Mina", chief_gender="girl"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
