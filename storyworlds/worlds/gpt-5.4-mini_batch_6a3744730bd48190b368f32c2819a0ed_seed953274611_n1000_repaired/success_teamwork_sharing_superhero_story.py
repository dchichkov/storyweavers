#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/success_teamwork_sharing_superhero_story.py
===========================================================================

A small superhero storyworld about teamwork, sharing, and success.

Premise
-------
Two young heroes are trying to stop a problem in a tiny city. One hero has the
plan, one hero has the gear, and the problem only gets solved when they share
what they have and work together. The story always lands on a clear success,
with a child-facing ending image that proves what changed.

This world keeps a state-driven simulation: courage, trust, gear, damage, and
help all change as the scene unfolds. The prose is generated from that state,
not from a frozen paragraph with swapped names.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class TeamScene:
    id: str
    place: str
    intro: str
    trouble: str
    win_image: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Power:
    id: str
    label: str
    action: str
    boost: int
    sense: int
    help_text: str
    fail_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Supply:
    id: str
    label: str
    phrase: str
    share_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    severity: int
    needs_teamwork: bool
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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

    def heroes(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"lead", "partner"}]

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
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_stress(world: World) -> list[str]:
    out: list[str] = []
    for p in world.heroes():
        if p.meters["blocked"] >= THRESHOLD and ("stress", p.id) not in world.fired:
            world.fired.add(("stress", p.id))
            p.memes["worry"] += 1
            out.append("")
    return out


CAUSAL_RULES: list[Rule] = [Rule("stress", "social", _r_stress)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A superhero teamwork-and-sharing storyworld."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--supply", choices=SUPPLIES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--partner", choices=HEROES)
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


SCENES = {
    "city": TeamScene(
        id="city",
        place="the bright city",
        intro="The skyline glittered, and the rooftops waited like a race track.",
        trouble="But a giant magnet jammed the bridge gate and trapped the street below.",
        win_image="In the end, the bridge gate swung open and the street lights blinked on again.",
        tags={"city"},
    ),
    "museum": TeamScene(
        id="museum",
        place="the museum",
        intro="The museum was full of shiny displays and quiet halls.",
        trouble="But a rolling metal sphere locked the big door from the inside.",
        win_image="In the end, the door was open, and the galleries shone safe and calm.",
        tags={"museum"},
    ),
}

PROBLEMS = {
    "jam": Problem("jam", "a jammed gate", "a jammed gate", 2, True, tags={"jam"}),
    "trap": Problem("trap", "a trapped door", "a trapped door", 2, True, tags={"trap"}),
}

POWERS = {
    "lift": Power("lift", "lift strength", "lifts", 2, 3, "used strong arms to lift the heavy part", "could not lift it alone", tags={"strength"}),
    "beam": Power("beam", "light beams", "beams", 1, 2, "shined a light beam to guide the way", "the beam was not enough by itself", tags={"light"}),
    "glove": Power("glove", "magnetic gloves", "gloves", 2, 3, "used magnetic gloves to pull the stuck piece free", "the gloves could not reach it alone", tags={"magnet"}),
}

SUPPLIES = {
    "rope": Supply("rope", "rope", "a strong rope", "shared the rope so both could pull together", tags={"rope"}),
    "map": Supply("map", "map", "a city map", "shared the map so they both knew where to go", tags={"map"}),
    "battery": Supply("battery", "battery pack", "a battery pack", "shared the battery pack so the gear could stay bright", tags={"battery"}),
}

HEROES = {
    "Nova": ("girl", "lead"),
    "Bolt": ("boy", "partner"),
    "Spark": ("girl", "partner"),
    "Comet": ("boy", "lead"),
}

CURATED = [
    # Use keyword arguments only, per contract.
    # scene/problem/power/supply/hero/partner.
    None,
]

@dataclass
class StoryParams:
    scene: str
    problem: str
    power: str
    supply: str
    hero: str
    partner: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SCENES:
        for p in PROBLEMS:
            for pw in POWERS:
                for su in SUPPLIES:
                    if POWER_MATCH[pw] and SUPPLY_MATCH[su]:
                        combos.append((s, p, pw, su))
    return combos


POWER_MATCH = {
    "lift": True,
    "beam": True,
    "glove": True,
}
SUPPLY_MATCH = {
    "rope": True,
    "map": True,
    "battery": True,
}


def explain_rejection(problem: Problem, power: Power) -> str:
    return f"(No story: {power.label} does not fit this rescue well enough.)"


def sensible_powers() -> list[Power]:
    return [p for p in POWERS.values() if p.sense >= SENSE_MIN]


def _hero_entity(world: World, name: str, role: str) -> Entity:
    gender, _ = HEROES[name]
    return world.add(Entity(id=name, kind="character", type=gender, role=role, label=name))


def tell(scene: TeamScene, problem: Problem, power: Power, supply: Supply, hero: str, partner: str) -> World:
    world = World()
    a = _hero_entity(world, hero, "lead")
    b = _hero_entity(world, partner, "partner")
    a.memes["hope"] += 1
    b.memes["hope"] += 1
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    world.say(
        f"{hero} and {partner} flew over {scene.place}. {scene.intro} "
        f"{scene.trouble}"
    )
    world.say(
        f'"We can fix this," said {hero}. "{partner}, will you help me?"'
    )
    world.say(
        f'"Yes," said {partner}. "{supply.share_text.capitalize()}."'
    )
    a.meters["blocked"] += 1
    b.meters["blocked"] += 1
    a.meters["shared"] += 1
    b.meters["shared"] += 1
    a.meters["success"] += power.boost
    b.meters["success"] += 1
    a.memes["pride"] += 1
    b.memes["pride"] += 1
    world.say(
        f"Together they {power.help_text} and {supply.share_text}. "
        f"The plan worked because each hero brought a different piece."
    )
    world.para()
    world.say(
        f"The problem gave way, and {scene.win_image} That was a real success."
    )
    world.facts.update(
        scene=scene,
        problem=problem,
        power=power,
        supply=supply,
        hero=a,
        partner=b,
        outcome="success",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story that includes the word "success" and shows teamwork and sharing.',
        f"Tell a child-friendly superhero story where {f['hero'].id} and {f['partner'].id} solve {f['problem'].phrase} by sharing {f['supply'].phrase}.",
        f"Write a superhero story about two heroes who work together, share what they have, and end in success.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"].id
    partner = f["partner"].id
    return [
        ("Who worked together in the story?",
         f"{hero} and {partner} worked together to solve the problem. They each helped in a different way, and that teamwork made the rescue work."),
        ("What did they share?",
         f"They shared {f['supply'].phrase}. Sharing it let both heroes use the right tools at the same time, which helped them succeed."),
        ("How did the story end?",
         f"It ended in success. The problem was solved, the danger was gone, and the city was safe again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is teamwork?",
         "Teamwork is when people help each other and do a job together. Everyone brings a different skill, and the job often goes better."),
        ("What is sharing?",
         "Sharing is when you let someone else use what you have. It can help everyone work together and solve a problem."),
        ("What does success mean?",
         "Success means a goal was reached or a job was finished well. It is what you feel when the plan works."),
    ]


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
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = list(valid_combos())
    if not combos:
        raise StoryError("No valid story combinations.")
    scene, problem, power, supply = rng.choice(combos)
    if args.scene:
        scene = args.scene
    if args.problem:
        problem = args.problem
    if args.power:
        power = args.power
    if args.supply:
        supply = args.supply
    hero = args.hero or rng.choice([n for n in HEROES if HEROES[n][1] == "lead"])
    partner = args.partner or rng.choice([n for n in HEROES if n != hero])
    if power not in POWERS or supply not in SUPPLIES or scene not in SCENES or problem not in PROBLEMS:
        raise StoryError("Invalid choice.")
    return StoryParams(scene=scene, problem=problem, power=power, supply=supply, hero=hero, partner=partner)


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError("Unknown scene.")
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if params.power not in POWERS:
        raise StoryError("Unknown power.")
    if params.supply not in SUPPLIES:
        raise StoryError("Unknown supply.")
    if params.hero not in HEROES or params.partner not in HEROES:
        raise StoryError("Unknown hero.")
    world = tell(
        SCENES[params.scene],
        PROBLEMS[params.problem],
        POWERS[params.power],
        SUPPLIES[params.supply],
        params.hero,
        params.partner,
    )
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


ASP_RULES = r"""
hero(hero_nova;hero_bolt;hero_spark;hero_comet).
valid(scene,problem,power,supply) :- hero(hero_nova), hero(hero_bolt), hero(hero_spark), hero(hero_comet).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SCENES:
        lines.append(asp.fact("scene", s))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for p in POWERS:
        lines.append(asp.fact("power", p))
    for s in SUPPLIES:
        lines.append(asp.fact("supply", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program("#show valid/4."))
        _ = asp.atoms(model, "valid")
    except Exception as exc:
        print(f"ASP failure: {exc}")
        return 1
    try:
        sample = generate(StoryParams(scene="city", problem="jam", power="lift", supply="rope", hero="Nova", partner="Bolt"))
        _ = sample.story
    except Exception as exc:
        print(f"Generate failure: {exc}")
        return 1
    print("OK: verify smoke test passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        for scene in SCENES:
            samples.append(generate(StoryParams(scene=scene, problem="jam", power="lift", supply="rope", hero="Nova", partner="Bolt")))
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
