#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/epee_gym_train_platform_dialogue_comedy.py
===========================================================================

A small standalone story world for a comedic dialogue scene on a train platform.

Premise:
- A child arrives at a train platform with an epee case.
- Another child thinks the epee is for a gym class.
- A train-platform mixup leads to a funny dialogue beat.
- A sensible adult or coach clarifies the plan, the children use the right gear,
  and the ending image proves the misunderstanding changed into a proper practice
  routine.

Seed words: epee, gym
Setting: train platform
Features: Dialogue
Style: Comedy
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Platform:
    id: str
    label: str
    location: str
    noisy: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    purpose: str
    is_sport: bool = False
    is_travel: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Plan:
    id: str
    joke: str
    mistaken: str
    correct: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes["confused"] >= THRESHOLD and world.get("friend").memes["joked"] >= THRESHOLD:
        sig = ("laugh",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("child").memes["amused"] += 1
            world.get("friend").memes["amused"] += 1
            out.append("__laugh__")
    return out


CAUSAL_RULES = [_r_laugh]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for platform in PLATFORMS:
        for gear in GEARS:
            for plan in PLANS:
                if gear.is_sport and gear.is_travel:
                    combos.append((platform, gear.id, plan.id))
    return combos


def reasonableness_gate(gear: Gear, platform: Platform) -> bool:
    return gear.is_sport and platform.id == "train_platform"


def predict_mixup(world: World, gear: Gear, plan: Plan) -> dict:
    sim = world.copy()
    _mixup(sim, sim.get("child"), sim.get("friend"), gear, plan, narrate=False)
    return {"confused": sim.get("child").memes["confused"] >= THRESHOLD}


def _mixup(world: World, child: Entity, friend: Entity, gear: Gear, plan: Plan, narrate: bool = True) -> None:
    child.memes["confused"] += 1
    friend.memes["joked"] += 1
    world.say(f'{friend.id} pointed at the case and said, "{plan.joke}"')
    world.say(f'{child.id} blinked. "{plan.mistaken}?"')


def _clarify(world: World, coach: Entity, child: Entity, friend: Entity, gear: Gear, plan: Plan) -> None:
    coach.memes["clarity"] += 1
    world.say(
        f'{coach.id} laughed and said, "{plan.correct} The {gear.label} is for fencing, '
        f"not for train-station push-ups."
    )


def _practice(world: World, child: Entity, friend: Entity, coach: Entity, gear: Gear) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{child.id} carried the {gear.label} case like it was a royal baton, and "
        f"{friend.id} tried one dramatic bow that made the waiting line clap."
    )
    world.say(
        f"Then they headed to the gym later, where the epee stayed safely in its bag "
        f"until practice time."
    )


def tell(platform: Platform, gear: Gear, plan: Plan) -> World:
    world = World()
    child = world.add(Entity("Nina", kind="character", type="girl", role="student"))
    friend = world.add(Entity("Omar", kind="character", type="boy", role="friend"))
    coach = world.add(Entity("Coach", kind="character", type="adult", role="coach", label="the coach"))
    world.add(Entity("platform", type="place", label=platform.label))
    world.facts["platform"] = platform
    world.facts["gear"] = gear
    world.facts["plan"] = plan

    child.memes["confused"] = 0.0
    friend.memes["joked"] = 0.0

    world.say(
        f"On a busy train platform, {child.id} arrived with an {gear.label} case "
        f"that looked very important."
    )
    world.say(
        f"{friend.id} leaned over and whispered, \"{plan.mistaken}\""
    )
    world.para()
    _mixup(world, child, friend, gear, plan)
    _clarify(world, coach, child, friend, gear, plan)
    propagate(world, narrate=False)
    world.para()
    _practice(world, child, friend, coach, gear)
    world.say(
        f"When the train whooshed in, everyone was smiling, and the epee had gone "
        f"from a mystery to a neatly zipped-up piece of gym gear."
    )

    world.facts.update(child=child, friend=friend, coach=coach)
    return world


PLATFORMS = {
    "train_platform": Platform("train_platform", "the train platform", "a station"),
}

GEARS = {
    "epee": Gear("epee", "epee", "an epee", "fencing", is_sport=True),
    "gym_bag": Gear("gym_bag", "gym bag", "a gym bag", "sports clothes", is_sport=True),
    "backpack": Gear("backpack", "backpack", "a backpack", "books", is_travel=True),
}

PLANS = {
    "mixup": Plan(
        "mixup",
        "If that bag is for the gym, does it come with tiny shoes?",
        "Is the epee for gym class?",
        "No, it is for fencing practice, and the gym is later.",
        {"dialogue", "comedy"},
    ),
    "dramatic": Plan(
        "dramatic",
        "I thought it was a sword parade for the train!",
        "Are we fencing the train?",
        "No one is fencing the train. The epee is for a sport, and the train is just arriving.",
        {"dialogue", "comedy"},
    ),
}


@dataclass
@dataclass
class StoryParams:
    platform: str
    gear: str
    plan: str
    child_name: str
    friend_name: str
    coach_name: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedic train-platform epee story world.")
    ap.add_argument("--platform", choices=PLATFORMS)
    ap.add_argument("--gear", choices=GEARS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--child-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--coach-name")
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
    if args.gear and args.gear == "backpack":
        raise StoryError("This story needs an epee or gym-related mixup, not a plain backpack.")
    combos = [c for c in valid_combos()
              if (args.platform is None or c[0] == args.platform)
              and (args.gear is None or c[1] == args.gear)
              and (args.plan is None or c[2] == args.plan)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    platform, gear, plan = rng.choice(sorted(combos))
    return StoryParams(
        platform=platform,
        gear=gear,
        plan=plan,
        child_name=args.child_name or rng.choice(["Nina", "Maya", "Lina", "Pia"]),
        friend_name=args.friend_name or rng.choice(["Omar", "Leo", "Milo", "Eli"]),
        coach_name=args.coach_name or "Coach",
    )


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a funny dialogue story on a train platform that includes the words "epee" and "gym".',
        f"Tell a comedy scene where {world.facts['child'].id} brings an epee to a train platform and someone jokes about the gym.",
        "Write a child-friendly story with dialogue, a misunderstanding, and a cheerful ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    return [
        ("Where does the story happen?",
         "It happens on a train platform, so the characters are waiting beside the tracks and talking in the noise and rush of the station."),
        ("Why is the epee funny in the story?",
         "It is funny because a friend mistakes it for gym gear at first. That mistake makes the dialogue playful until the coach explains that it is for fencing."),
        ("How does the story end?",
         "It ends with everyone smiling and the epee put away safely for fencing practice later. The train arrives, and the misunderstanding turns into a joke instead of a problem."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is an epee?",
         "An epee is a fencing sword used in a sport. It is handled carefully and is not a toy."),
        ("What is a gym?",
         "A gym is a place where people exercise or practice sports. It is a good place for training and games."),
        ("What is a train platform?",
         "A train platform is the raised place beside the tracks where people wait for trains and get on and off safely."),
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
    for e in list(world.entities.values()):
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("train_platform", "epee", "mixup", "Nina", "Omar", "Coach"),
    StoryParams("train_platform", "gym_bag", "dramatic", "Maya", "Leo", "Coach"),
]


def explain_rejection() -> str:
    return "(No story: this world needs a clear epee/gym mixup on the train platform.)"


def valid_story(params: StoryParams) -> bool:
    return params.platform in PLATFORMS and params.gear in GEARS and params.plan in PLANS


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import inside ASP helpers
    lines = []
    for pid in PLATFORMS:
        lines.append(asp.fact("platform", pid))
    for gid, g in GEARS.items():
        lines.append(asp.fact("gear", gid))
        if g.is_sport:
            lines.append(asp.fact("sport", gid))
        if g.is_travel:
            lines.append(asp.fact("travel", gid))
    for pid in PLANS:
        lines.append(asp.fact("plan", pid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, G, PL) :- platform(P), gear(G), plan(PL), sport(G).
show_valid(P, G, PL) :- valid(P, G, PL).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combo sets differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(PLATFORMS[params.platform], GEARS[params.gear], PLANS[params.plan])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
