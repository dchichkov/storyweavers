#!/usr/bin/env python3
"""
storyworlds/worlds/rosemary_bravery_happy_ending_curiosity_slice_of.py
======================================================================

A small slice-of-life storyworld about a child, a curious moment, a brave act,
and a happy ending around rosemary in a kitchen or garden.

The premise is simple: someone notices rosemary, wants to taste or use it in a
small everyday way, pauses to learn what it is, and chooses a brave but safe
next step. The world model tracks a few physical and emotional changes so the
story can show a clear turn and ending image instead of a frozen paragraph.

Run it
------
    python storyworlds/worlds/.../rosemary_bravery_happy_ending_curiosity_slice_of.py
    python storyworlds/worlds/.../rosemary_bravery_happy_ending_curiosity_slice_of.py -n 3 --seed 42 --json
    python storyworlds/worlds/.../rosemary_bravery_happy_ending_curiosity_slice_of.py --qa --seed 777
    python storyworlds/worlds/.../rosemary_bravery_happy_ending_curiosity_slice_of.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional


def _bootstrap_results_path() -> None:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        candidate = parent / "results.py"
        if candidate.exists():
            sys.path.insert(0, str(parent))
            return
    raise RuntimeError("Could not locate storyworlds/results.py")


_bootstrap_results_path()
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
ASP_RULES = r"""
curious(A) :- wants_to_learn(A).
brave(A) :- makes_kind_choice(A).
happy_ending(A) :- shares(A, rosemary) ; serves(A, rosemary).
story_ok :- rosemary_present, curious(hero), brave(hero), happy_ending(hero).
#show story_ok/0.
#show curious/1.
#show brave/1.
#show happy_ending/1.
"""

ROOMS = {
    "kitchen": {"place": "the kitchen", "surface": "the windowsill", "near": "the sink"},
    "garden": {"place": "the garden", "surface": "the stone path", "near": "the herb bed"},
    "balcony": {"place": "the balcony", "surface": "the railing box", "near": "the open door"},
}

HELPERS = {
    "mom": {"label": "mom", "type": "mother"},
    "dad": {"label": "dad", "type": "father"},
    "neighbor": {"label": "Ms. Lee", "type": "woman"},
}

ACTS = {
    "snip": "snip a tiny sprig for dinner",
    "study": "lean close and study the leaves",
    "water": "water the rosemary and check if it needs more sun",
}

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, object] = field(default_factory=dict)

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
        return self.label or self.id


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    room: str
    helper: str
    action: str
    child_name: str
    child_gender: str
    helper_gender: str
    seed: Optional[int] = None


def _do_curious(world: World, child: Entity, rosemary: Entity, helper: Entity) -> None:
    if ("curious", child.id) in world.fired:
        return
    world.fired.add(("curious", child.id))
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    world.say(
        f"{child.id} leaned close to the rosemary and smiled. The leaves smelled piney and fresh."
    )
    world.say(
        f'"What is it for?" {child.id} asked. {helper.id} said rosemary is a little herb for food and smell.'
    )


def _do_brave(world: World, child: Entity, helper: Entity, rosemary: Entity) -> None:
    if ("brave", child.id) in world.fired:
        return
    world.fired.add(("brave", child.id))
    child.memes["bravery"] = child.memes.get("bravery", 0.0) + 1
    world.say(
        f"{child.id} was a little nervous, but {child.pronoun()} stood on tiptoe and snipped one tiny sprig."
    )
    world.say(
        f"{helper.id} watched kindly and nodded. It was a brave choice because {child.id} asked first and took only a little."
    )


def _do_happy(world: World, child: Entity, helper: Entity, rosemary: Entity, room: Entity) -> None:
    if ("happy", child.id) in world.fired:
        return
    world.fired.add(("happy", child.id))
    child.memes["happy"] = child.memes.get("happy", 0.0) + 1
    rosemary.meters["picked"] = rosemary.meters.get("picked", 0.0) + 1
    room.meters["warmth"] = room.meters.get("warmth", 0.0) + 1
    world.say(
        f"At dinner, {helper.id} tucked the sprig into soup, and the whole kitchen smelled warm and green."
    )
    world.say(
        f"{child.id} grinned at the table, proud that curiosity had led to a brave and happy ending."
    )


def generate_story(world: World) -> None:
    child = world.get("child")
    helper = world.get("helper")
    rosemary = world.get("rosemary")
    room = world.get("room")
    world.say(
        f"On a quiet afternoon, {child.id} found a pot of rosemary in {room.label_word}."
    )
    world.say(
        f"The leaves were small and soft, and {child.id} wanted to know everything about them."
    )
    world.para()
    _do_curious(world, child, rosemary, helper)
    world.para()
    _do_brave(world, child, helper, rosemary)
    world.para()
    _do_happy(world, child, helper, rosemary, room)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room in ROOMS:
        for helper in HELPERS:
            for action in ACTS:
                combos.append((room, helper, action))
    return combos


def _choose_name(rng: random.Random, gender: str) -> str:
    girls = ["Lily", "Maya", "Nora", "Ava", "Zoe"]
    boys = ["Theo", "Ben", "Leo", "Sam", "Finn"]
    return rng.choice(girls if gender == "girl" else boys)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.room and args.room not in ROOMS:
        raise StoryError("Unknown room.")
    if args.helper and args.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    if args.action and args.action not in ACTS:
        raise StoryError("Unknown action.")
    combos = [
        c for c in combos
        if (args.room is None or c[0] == args.room)
        and (args.helper is None or c[1] == args.helper)
        and (args.action is None or c[2] == args.action)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    room, helper, action = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("woman" if helper == "neighbor" else rng.choice(["mother", "father"]))
    return StoryParams(
        room=room,
        helper=helper,
        action=action,
        child_name=args.name or _choose_name(rng, gender),
        child_gender=gender,
        helper_gender=helper_gender,
    )


def tell(params: StoryParams) -> World:
    world = World()
    room_cfg = ROOMS[params.room]
    helper_cfg = HELPERS[params.helper]
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender))
    helper = world.add(Entity(id=helper_cfg["label"], kind="character", type=helper_cfg["type"], label=helper_cfg["label"]))
    rosemary = world.add(Entity(id="rosemary", kind="thing", type="herb", label="rosemary"))
    room = world.add(Entity(id="room", kind="thing", type="room", label=room_cfg["place"]))
    world.facts.update(params=params, child=child, helper=helper, rosemary=rosemary, room=room, room_cfg=room_cfg)
    generate_story(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short slice-of-life story for a young child that includes the word "rosemary".',
        f"Tell a gentle story where {p.child_name} notices rosemary in {ROOMS[p.room]['place']} and learns something new from {HELPERS[p.helper]['label']}.",
        f"Write a happy everyday story about curiosity, bravery, and rosemary in a home or garden.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    child = world.facts["child"]
    helper = world.facts["helper"]
    room = world.facts["room"]
    return [
        QAItem(
            question=f"Where did {p.child_name} find the rosemary?",
            answer=f"{p.child_name} found the rosemary in {room.label_word}. It was a quiet everyday moment that started the story."
        ),
        QAItem(
            question=f"What did {p.child_name} do that was brave?",
            answer=f"{p.child_name} asked first and snipped only one tiny sprig. That was brave because it showed care as well as curiosity."
        ),
        QAItem(
            question=f"How did the story end for {p.child_name}?",
            answer=f"It ended happily, with the rosemary going into dinner and the kitchen smelling warm and fresh. {p.child_name} felt proud and calm at the table."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is rosemary?",
            answer="Rosemary is a fragrant herb with small green leaves. People often use it for cooking because it smells good and tastes nice."
        ),
        QAItem(
            question="Why do people ask before picking plants?",
            answer="People ask first so they do not damage something that belongs to someone else. Being careful is a kind way to be curious."
        ),
        QAItem(
            question="What does bravery look like in an everyday moment?",
            answer="Bravery can be small, like asking a question, trying something new, or doing the careful thing even when you feel shy."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    bits = ["--- world model state ---"]
    for e in world.entities.values():
        bits.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)} attrs={dict(e.attrs)}")
    return "\n".join(bits)


def asp_facts() -> str:
    import asp
    lines = [asp.fact("rosemary_present")]
    for room in ROOMS:
        lines.append(asp.fact("room", room))
    for helper in HELPERS:
        lines.append(asp.fact("helper", helper))
    for action in ACTS:
        lines.append(asp.fact("action", action))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show story_ok/0."))
    return [("story",)] if asp.atoms(model, "story_ok") else []


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) == {("story",)} and valid_combos():
        print("OK: ASP twin is wired.")
    else:
        print("MISMATCH in ASP twin wiring.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(room=None, helper=None, action=None, name=None, gender=None, helper_gender=None), random.Random(777)))
        assert sample.story
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample)
        print("OK: generate/emit smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life rosemary storyworld.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--action", choices=ACTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["mother", "father", "woman"])
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


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS or params.helper not in HELPERS or params.action not in ACTS:
        raise StoryError("Invalid StoryParams.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(room="kitchen", helper="mom", action="study", child_name="Lily", child_gender="girl", helper_gender="mother"),
    StoryParams(room="garden", helper="dad", action="snip", child_name="Theo", child_gender="boy", helper_gender="father"),
    StoryParams(room="balcony", helper="neighbor", action="water", child_name="Maya", child_gender="girl", helper_gender="woman"),
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
        print(asp_program("", "#show story_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
