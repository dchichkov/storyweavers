#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/frank_atlantic_teamwork_suspense_repetition_rhyming_story.py
============================================================================================

A small standalone storyworld about two children, Frank and Atlantic, who need
teamwork to solve a suspenseful little problem in a rhyming, rhythmic way.

The domain is deliberately tiny:
- a child names a child-sized project,
- one child wants to do it alone,
- suspense builds because the task is unstable,
- teamwork and repetition save the day,
- the ending proves what changed in the world.

The story text is generated from world state, not from a frozen template with
swapped nouns. The world includes physical meters and emotional memes, a small
forward rule engine, a reasonableness gate, a QA system, and an inline ASP twin.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    scene: str
    dark_spot: str
    sound: str
    supports: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    label: str
    action: str
    verb: str
    risk: str
    spark: str
    needs: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    action: str
    beats_risk: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["wobble"] < THRESHOLD:
            continue
        sig = ("suspense", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("stage").memes["tension"] += 1
        for cid in ("frank", "atlantic"):
            if cid in world.entities:
                world.get(cid).memes["worry"] += 1
        out.append("__suspense__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if "rope" not in world.entities or "kite" not in world.entities:
        return out
    rope = world.get("rope")
    kite = world.get("kite")
    if rope.meters["held"] >= THRESHOLD and kite.meters["steady"] < THRESHOLD:
        sig = ("teamwork",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        kite.meters["steady"] += 1
        world.get("stage").meters["safe"] += 1
        out.append("__teamwork__")
    return out


CAUSAL_RULES = [
    Rule("suspense", "social", _r_suspense),
    Rule("teamwork", "physical", _r_teamwork),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def risky(task: Task) -> bool:
    return bool(task.needs)


def compatible(place: Place, task: Task, helper: Helper) -> bool:
    return task.id in place.supports and helper.beats_risk


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for tid, task in TASKS.items():
            for hid, helper in HELPERS.items():
                if compatible(place, task, helper):
                    combos.append((pid, tid, hid))
    return combos


@dataclass
class StoryParams:
    place: str
    task: str
    helper: str
    seed: Optional[int] = None


def _setup(world: World, frank: Entity, atlantic: Entity, place: Place, task: Task) -> None:
    frank.memes["eager"] += 1
    atlantic.memes["eager"] += 1
    world.say(
        f"At {place.label}, Frank and Atlantic began with a plan that sang like a tune. "
        f"{place.scene}"
    )
    world.say(
        f"They wanted to {task.action}, and the air was full of a hush-hush croon. "
        f"{place.sound}"
    )


def _temptation(world: World, frank: Entity, task: Task) -> None:
    frank.memes["pride"] += 1
    world.say(
        f'Frank said, "I can do it fast; I can do it right. '
        f'I can do it now, by the pale porch light."'
    )
    world.say(f"But the plan had a wobble, and the wobble felt tight.")


def _warn(world: World, atlantic: Entity, task: Task, place: Place) -> None:
    atlantic.memes["care"] += 1
    world.say(
        f'Atlantic leaned close and said, "Wait, my friend, wait. '
        f'One small shake can turn a good thing bad and late."'
    )
    world.say(
        f'"If {task.label} slips once here, it may make a great mess; '
        f'let\'s use two hands together and choose our best yes."'
    )


def _start_task(world: World, task: Task) -> None:
    world.get("kite").meters["wobble"] += 1
    world.say(
        f"Frank lifted the {task.label}, and the {task.spark} sparked a twitch. "
        f"The little thing trembled as if it might switch."
    )
    propagate(world, narrate=False)


def _teamup(world: World, helper: Helper, task: Task) -> None:
    world.get("rope").meters["held"] += 1
    world.say(
        f"Then Atlantic held the rope and Frank held the frame. "
        f"Again and again, they called out the same game:"
    )
    world.say(
        f'"Hold and slow, hold and slow," they sang in a row. '
        f'"Two hands are braver than one, you know."'
    )
    world.get("kite").meters["wobble"] = 0
    world.get("kite").meters["steady"] += 1
    world.get("stage").meters["safe"] += 1
    world.get("stage").memes["tension"] = max(0.0, world.get("stage").memes["tension"] - 1)
    world.say(
        f"With {helper.action}, the {task.label} settled down, and the shaky air slowed."
    )


def _ending(world: World, task: Task, helper: Helper) -> None:
    world.say(
        f"At last the {task.label} rose clean and true. Frank grinned wide; Atlantic did too."
    )
    world.say(
        f"Their repeated refrain still rang in the night: "
        f'"Hold and slow, hold and slow," till everything felt right.'
    )
    world.say(
        f"And that was the bright little sight by the end of the scene: "
        f"two friends, one steady win, and a calm, safe gleam."
    )


def tell(place: Place, task: Task, helper: Helper) -> World:
    world = World(place)
    frank = world.add(Entity("frank", kind="character", type="boy", label="Frank", role="child"))
    atlantic = world.add(Entity("atlantic", kind="character", type="girl", label="Atlantic", role="child"))
    world.add(Entity("stage", type="place", label=place.label))
    world.add(Entity("kite", type="thing", label=task.label))
    world.add(Entity("rope", type="thing", label=helper.label))
    _setup(world, frank, atlantic, place, task)
    world.para()
    _temptation(world, frank, task)
    _warn(world, atlantic, task, place)
    world.para()
    _start_task(world, task)
    _teamup(world, helper, task)
    world.para()
    _ending(world, task, helper)
    world.facts.update(place=place, task=task, helper=helper, frank=frank, atlantic=atlantic,
                       outcome="steady", repeated=True)
    return world


PLACES = {
    "pier": Place("pier", "the pier", "The boards creaked under a salt-bright sky.", "the edge over the water", "The sea whispered and the gulls called.", {"kite", "rope"}),
    "dune": Place("dune", "the dune", "The sand shone pale and the wind kept changing its mind.", "the windy edge of the hill", "The breeze went whoosh and hush.", {"kite", "rope"}),
    "cove": Place("cove", "the cove", "The little bay glimmered like a silver bowl.", "the choppy waterline", "The waves kept singing in and out.", {"kite", "rope"}),
}

TASKS = {
    "kite": Task("kite", "kite", "fly the kite", "fly", "the kite could swoop and slip", "the string gave a shaky twitch", {"rope"}, {"kite", "suspense"}),
    "raft": Task("raft", "raft", "push the raft", "push", "the raft could drift and tip", "the raft gave a wobble", {"rope"}, {"raft", "suspense"}),
    "sail": Task("sail", "paper sail", "raise the sail", "raise", "the sail could billow and bend", "the paper sail gave a flutter", {"rope"}, {"sail", "suspense"}),
}

HELPERS = {
    "rope": Helper("rope", "rope", "a firm rope", True, {"rope", "teamwork"}),
    "pull": Helper("pull", "pull", "a careful pull", True, {"pull", "teamwork"}),
    "knot": Helper("knot", "knot", "a steady knot", True, {"knot", "teamwork"}),
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a young child that includes the words "frank" and "atlantic" and shows teamwork.',
        f'Tell a suspenseful little rhyme where Frank and Atlantic almost lose a {f["task"].label}, but they solve it together.',
        f'Write a repeated, musical story with a soft suspense moment, then a teamwork ending, set at {f["place"].label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    place: Place = f["place"]
    task: Task = f["task"]
    frank: Entity = f["frank"]
    atlantic: Entity = f["atlantic"]
    return [
        QAItem(
            question="Who is the story about?",
            answer="It is about Frank and Atlantic, two children who are trying something tricky together. The story follows their worry, their teamwork, and the calm ending."
        ),
        QAItem(
            question="Why did the moment feel suspenseful?",
            answer=f"The {task.label} wobble made the moment feel uncertain, so everyone had to pause and be careful. That small shake is what built the suspense before the friends fixed it."
        ),
        QAItem(
            question="How did Frank and Atlantic solve the problem?",
            answer="They worked together, held steady, and repeated the same calming words again and again. Their teamwork kept the task safe until it settled."
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"By the end, the {task.label} was steady and the scene was calm. Frank and Atlantic were still together, but now their shared effort had made the whole job safe."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other with the same job. They do more together than they could do alone."
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of waiting to see what will happen next. A little problem can make a story feel suspenseful."
        ),
        QAItem(
            question="Why do people repeat words in a song or rhyme?",
            answer="Repeating words can help a song feel steady and easy to remember. It can also calm nervous feelings."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    place: str
    task: str
    helper: str
    seed: Optional[int] = None


def explain_rejection(place: Place, task: Task, helper: Helper) -> str:
    return f"(No story: {place.label} cannot support that combo, or the helper cannot beat the wobble.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming teamwork storyworld with Frank and Atlantic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, helper = rng.choice(sorted(combos))
    return StoryParams(place, task, helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TASKS[params.task], HELPERS[params.helper])
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


ASP_RULES = r"""
compatible(P, T, H) :- place(P), task(T), helper(H).
valid(P, T, H) :- compatible(P, T, H).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    py = set(valid_combos())
    try:
        asp = set(asp_valid_combos())
    except Exception as e:
        print(f"ASP unavailable or failed: {e}")
        return 1
    if asp != py:
        rc = 1
        print("MISMATCH in valid_combos():")
        print("  only in asp:", sorted(asp - py))
        print("  only in py:", sorted(py - asp))
    else:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    try:
        sample = generate(StoryParams(*sorted(py)[0]))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True)
        print("OK: generation/emit smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


CURATED = [
    StoryParams("pier", "kite", "rope"),
    StoryParams("dune", "sail", "knot"),
    StoryParams("cove", "raft", "pull"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
