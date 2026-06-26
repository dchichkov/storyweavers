#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/hand_ful_athlete_road_repair_suspense_friendship.py
=============================================================================================================

A small bedtime-story world about a young athlete, a road repair site, a little
suspense, and a friendship that helps during a long wait.

The premise is intentionally narrow:
- a child athlete wants to reach practice
- a road repair crew has the lane closed
- the child carries a hand-ful of small things that might help
- a friend stays close when the wait feels tense
- the ending is a gentle bad ending: practice is missed, but nobody is hurt

The world model tracks both physical meters and emotional memes, and the prose
is generated from state changes rather than from a frozen paragraph template.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    path: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class RoadRepair:
    place: str = "the road repair site"
    blocked: bool = True
    cones: int = 6
    crew_phrase: str = "the repair crew"
    weather: str = "soft evening"
    affordance: str = "waiting beside the barrier"


@dataclass
class StoryParams:
    athlete_name: str
    athlete_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: RoadRepair) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
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
        clone = World(copy.deepcopy(self.setting))
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _rule_suspense(world: World) -> list[str]:
    out: list[str] = []
    athlete = world.entities.get("athlete")
    if not athlete:
        return out
    if athlete.memes.get("worry", 0) < THRESHOLD:
        return out
    sig = ("suspense", athlete.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    athlete.meters["still"] = athlete.meters.get("still", 0) + 1
    out.append("The lane stayed closed, and the waiting felt longer than the whole street.")
    return out


def _rule_friendship(world: World) -> list[str]:
    out: list[str] = []
    athlete = world.entities.get("athlete")
    friend = world.entities.get("friend")
    if not athlete or not friend:
        return out
    if athlete.memes.get("worry", 0) < THRESHOLD or friend.memes.get("kindness", 0) < THRESHOLD:
        return out
    sig = ("friendship", athlete.id, friend.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    athlete.memes["brave"] = athlete.memes.get("brave", 0) + 1
    friend.memes["warm"] = friend.memes.get("warm", 0) + 1
    out.append("The friend stayed close, like a little lamp beside a dark path.")
    return out


def _rule_bad_ending(world: World) -> list[str]:
    athlete = world.entities.get("athlete")
    if not athlete:
        return []
    if athlete.meters.get("late", 0) < THRESHOLD:
        return []
    sig = ("bad_end", athlete.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    athlete.memes["sad"] = athlete.memes.get("sad", 0) + 1
    return ["By the time the road opened, practice had already ended."]


CAUSAL_RULES = [_rule_suspense, _rule_friendship, _rule_bad_ending]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule(world)
            if items:
                changed = True
                produced.extend(items)
    if narrate:
        for s in produced:
            world.say(s)


def build_scene(params: StoryParams) -> World:
    world = World(RoadRepair())
    athlete = world.add(Entity(id="athlete", kind="character", type=params.athlete_type, label=params.athlete_name))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend_type, label=params.friend_name))
    cones = world.add(Entity(id="cones", type="thing", label="orange cones", phrase="a row of orange cones"))
    bolts = world.add(Entity(id="handful", type="thing", label="hand-ful", phrase="a hand-ful of shiny bolts"))
    world.facts["cones"] = cones
    world.facts["bolts"] = bolts
    world.facts["athlete"] = athlete
    world.facts["friend"] = friend

    athlete.memes["hope"] = 1
    athlete.memes["worry"] = 0
    friend.memes["kindness"] = 1

    world.say(f"{athlete.label} was a little {athlete.type} athlete who loved to run before the stars came out.")
    world.say(f"After supper, {athlete.label} and {friend.label} walked toward {world.setting.place}.")
    world.say(f"There, {world.setting.crew_phrase} had set out {world.setting.cones} cones and a bright barrier.")
    world.para()

    world.say(f"{athlete.label} held a {bolts.label} of small bolts and asked if the crew needed them.")
    athlete.meters["wait"] = 1
    athlete.memes["worry"] += 1
    world.say(f"The worker smiled, but the lane still stayed shut, so {athlete.label} had to wait.")
    propagate(world)

    world.para()
    world.say(f"{friend.label} sat on the curb and shared a quiet story to keep {athlete.label} company.")
    athlete.memes["kindness"] = athlete.memes.get("kindness", 0) + 1
    athlete.memes["brave"] = athlete.memes.get("brave", 0) + 1
    world.say(f"The two friends counted cones together and listened to the little clang of tools in the dark.")
    athlete.meters["late"] = 1
    propagate(world)

    world.para()
    world.say(f"At last, the road was open again, but practice was already over, and the sky was nearly asleep.")
    world.say(f"{athlete.label} and {friend.label} walked home hand in hand, a bit sad, a bit calm, and still friends.")
    world.facts["athlete"] = athlete
    world.facts["friend"] = friend
    return world


def valid_combos() -> list[tuple[str, str]]:
    return [("road repair", "athlete")]


ASP_RULES = r"""
road_repair(site).
athlete_kind(athlete).

valid(site, athlete) :- road_repair(site), athlete_kind(athlete).
"""

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("road_repair", "site"),
        asp.fact("athlete_kind", "athlete"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
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


def generation_prompts(world: World) -> list[str]:
    athlete = world.facts["athlete"]
    friend = world.facts["friend"]
    return [
        f'Write a bedtime story about a little {athlete.type} athlete who waits at a road repair site.',
        f"Tell a gentle suspense story where {athlete.label} and {friend.label} look at a closed road and stay friends.",
        f'Write a child-friendly story that includes the word "hand-ful" and ends with a quiet, sad walk home.',
    ]


def story_qa(world: World) -> list[QAItem]:
    athlete = world.facts["athlete"]
    friend = world.facts["friend"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {athlete.label}, a little {athlete.type} athlete, and the friend {friend.label} who stayed with {athlete.pronoun('object')}.",
        ),
        QAItem(
            question=f"Why did {athlete.label} have to pause near the road repair site?",
            answer=f"{world.setting.crew_phrase} had closed the lane with cones and a barrier, so {athlete.label} could not run through yet.",
        ),
        QAItem(
            question=f"What happened at the end of the story?",
            answer=f"The road opened too late for practice, so {athlete.label} went home a little sad, but {friend.label} stayed kind and close.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are road cones for?",
            answer="Road cones help warn people that a road is being worked on, so they know to slow down or go another way.",
        ),
        QAItem(
            question="Why do friends stay with someone who feels worried?",
            answer="Friends stay close because company can make hard moments feel less scary and more calm.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {e.label:12} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: athlete, road repair, suspense, friendship, bad ending.")
    ap.add_argument("--athlete-name", default=None)
    ap.add_argument("--athlete-type", choices=["boy", "girl"], default="boy")
    ap.add_argument("--friend-name", default=None)
    ap.add_argument("--friend-type", choices=["boy", "girl"], default="girl")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    names_boy = ["Milo", "Theo", "Nico", "Owen", "Finn"]
    names_girl = ["Mina", "Tessa", "Luna", "Ada", "Ivy"]
    athlete_name = args.athlete_name or rng.choice(names_boy if args.athlete_type == "boy" else names_girl)
    friend_name = args.friend_name or rng.choice(names_girl if args.friend_type == "girl" else names_boy)
    return StoryParams(
        athlete_name=athlete_name,
        athlete_type=args.athlete_type,
        friend_name=friend_name,
        friend_type=args.friend_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_scene(params)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams("Milo", "boy", "Ivy", "girl"),
            StoryParams("Nina", "girl", "Ben", "boy"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
