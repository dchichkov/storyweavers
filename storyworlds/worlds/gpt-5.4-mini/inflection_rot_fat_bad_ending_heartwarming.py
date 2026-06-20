#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/inflection_rot_fat_bad_ending_heartwarming.py
==============================================================================

A standalone storyworld for a tiny, heartwarming kitchen-and-garden domain:
a child brings home fruit, watches it change at the ripening inflection, misses
the right moment, and the fruit rots anyway. The ending is bad in the sense that
the fruit is lost, but the story stays warm and gentle: the family comforts one
another, saves what can be saved, and remembers the lesson for next time.

The three seed words are woven into the simulated world:
- inflection: the point where fruit changes from ready-to-eat to past it
- rot: the physical decay that follows if nobody uses the fruit in time
- fat: the fruit swells and gets plump before it turns

This world is intentionally small and constraint-checked.
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
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)


@dataclass
class FruitKind:
    id: str
    label: str
    phrase: str
    plural: bool = False
    sweet: bool = True
    ripens_fast: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Setting:
    id: str
    place: str
    light: str
    counter: str
    basket: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


def _r_rot(world: World) -> list[str]:
    out: list[str] = []
    fruit = world.get("fruit")
    if fruit.meters["rot"] >= THRESHOLD:
        sig = ("rot_notice", fruit.id)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in ("child", "parent", "grandparent"):
                if kid in world.entities:
                    world.get(kid).memes["sadness"] += 1
            out.append("__rot__")
    return out


def _r_waste(world: World) -> list[str]:
    fruit = world.get("fruit")
    if fruit.meters["rot"] >= THRESHOLD:
        sig = ("waste", fruit.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("home").meters["waste"] += 1
            return ["There was no way to save the whole basket now."]
    return []


CAUSAL_RULES = [Rule("rot", "physical", _r_rot), Rule("waste", "physical", _r_waste)]


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


def fruit_inflection(ripeness: float, delay: int) -> str:
    if ripeness < 1.0:
        return "not ready yet"
    if ripeness < 2.0:
        return "at the sweet inflection, ready for one good day"
    if delay <= 0:
        return "past the sweet inflection"
    return "sliding past the sweet inflection"


def predict_rot(world: World, delay: int) -> bool:
    sim = world.copy()
    sim.get("fruit").meters["rot"] += 1 + delay
    propagate(sim, narrate=False)
    return sim.get("fruit").meters["rot"] >= THRESHOLD


def stale_or_spoiled(response: Response, fruit: FruitKind, delay: int) -> bool:
    return response.power >= (1 + delay + (1 if fruit.ripens_fast else 0))


def _do_wait(world: World, delay: int) -> None:
    fruit = world.get("fruit")
    fruit.meters["ripeness"] += 1
    fruit.meters["fat"] += 1
    if delay > 0:
        fruit.meters["delay"] += delay
    propagate(world, narrate=False)


def _do_prepare(world: World, response: Response, fruit: Entity) -> None:
    fruit.meters["used"] += 1
    if response.id == "slice":
        fruit.meters["rot"] = 0


def intro(world: World, child: Entity, parent: Entity, setting: Setting, fruit: FruitKind) -> None:
    child.memes["hope"] += 1
    world.say(
        f"On a bright afternoon, {child.id} and {parent.id} sat in {setting.place} with a bowl of {fruit.phrase}. "
        f"The fruit had started to grow fat and round, and the air smelled sweet."
    )


def turn(world: World, child: Entity, parent: Entity, fruit: FruitKind, delay: int) -> None:
    world.say(
        f"{child.id} touched one piece and noticed the change at its inflection, the exact moment when it was no longer just getting ready. "
        f"{parent.id} smiled softly and said it might be best to use it soon."
    )
    if delay:
        world.say(
            f"But the afternoon drifted on anyway, and the basket stayed on the counter for {delay} more turn{'' if delay == 1 else 's'}."
        )


def rot_scene(world: World, parent: Entity, fruit: FruitKind) -> None:
    world.get("fruit").meters["rot"] += 1
    propagate(world)
    world.say(
        f"By evening, the sweet smell had gone dull. The {fruit.label} had begun to rot, and the soft spots spread like a quiet stain."
    )
    world.say(
        f"{parent.id} wrapped an arm around {world.get('child').id} and said, 'We still have each other. We'll make something kind from what is left.'"
    )


def ending(world: World, fruit: FruitKind) -> None:
    world.say(
        f"They saved the last clean slices for a little breakfast, but most of the bowl had to be thrown away. "
        f"It was a sad ending for the fruit, though the kitchen stayed warm with patience and hugs."
    )


def rescue_fail(world: World, response: Response, fruit: Entity) -> None:
    body = response.fail.replace("{target}", fruit.label)
    world.say(f"{body}. The rot had already won, and there was no bringing back the lost fruit.")


def rescue_ok(world: World, response: Response, fruit: Entity) -> None:
    body = response.text.replace("{target}", fruit.label)
    world.say(f"{body}. The family kept the good pieces and shared them before the rest spoiled.")


def tell(setting: Setting, fruit_kind: FruitKind, response: Response, delay: int,
         child_name: str = "Mina", child_gender: str = "girl",
         parent_name: str = "Mom", parent_gender: str = "mother",
         grandparent_name: str = "Grandma", grandparent_gender: str = "grandmother") -> World:
    world = World()
    child = world.add(Entity(child_name, "character", child_gender, role="child"))
    parent = world.add(Entity(parent_name, "character", parent_gender, role="parent"))
    grandparent = world.add(Entity(grandparent_name, "character", grandparent_gender, role="grandparent"))
    world.add(Entity("home", "place", "home"))
    fruit = world.add(Entity("fruit", "thing", fruit_kind.id, label=fruit_kind.label))
    fruit.meters["fat"] += 1
    fruit.meters["ripeness"] += 1

    intro(world, child, parent, setting, fruit_kind)
    world.para()
    turn(world, child, parent, fruit_kind, delay)
    if predict_rot(world, delay):
        world.say("There was a little hush, as if everyone felt the same worry at once.")
    world.para()
    _do_wait(world, delay)
    if stale_or_spoiled(response, fruit_kind, delay):
        rescue_fail(world, response, fruit)
        rot_scene(world, parent, fruit_kind)
    else:
        rescue_ok(world, response, fruit)
        ending(world, fruit_kind)

    world.facts.update(
        child=child, parent=parent, grandparent=grandparent, fruit=fruit,
        fruit_kind=fruit_kind, setting=setting, response=response, delay=delay,
        outcome="bad",
    )
    return world


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "sunlight", "counter", "basket", tags={"kitchen"}),
    "porch": Setting("porch", "the porch", "afternoon light", "bench", "basket", tags={"porch"}),
}

FRUITS = {
    "pears": FruitKind("pears", "pears", "a bowl of pears", plural=True, sweet=True, ripens_fast=True, tags={"fruit", "pear"}),
    "plums": FruitKind("plums", "plums", "a bowl of plums", plural=True, sweet=True, ripens_fast=False, tags={"fruit", "plum"}),
    "apples": FruitKind("apples", "apples", "a bowl of apples", plural=True, sweet=True, ripens_fast=False, tags={"fruit", "apple"}),
}

RESPONSES = {
    "slice": Response(
        "slice", 3, 3,
        "carefully sliced the fruit and set the good pieces in a little dish",
        "tried to slice the fruit, but it was already too soft and the pieces fell apart",
        "carefully sliced the fruit and set the good pieces in a little dish",
        tags={"kitchen"},
    ),
    "jam": Response(
        "jam", 2, 2,
        "cooked the fruit down into a tiny pot of jam",
        "tried to cook the fruit down, but the rot made it too late for a good jam",
        "cooked the fruit down into a tiny pot of jam",
        tags={"kitchen"},
    ),
}

CURATED = [
    ("kitchen", "pears", "slice", 1),
    ("porch", "plums", "jam", 0),
]


@dataclass
class StoryParams:
    setting: str
    fruit: str
    response: str
    delay: int = 0
    child_name: str = "Mina"
    child_gender: str = "girl"
    parent_name: str = "Mom"
    parent_gender: str = "mother"
    grandparent_name: str = "Grandma"
    grandparent_gender: str = "grandmother"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for fid, fruit in FRUITS.items():
            for rid, response in RESPONSES.items():
                if setting.id and fruit.sweet and response.sense >= SENSE_MIN:
                    combos.append((sid, fid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming fruit story with a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--fruit", choices=FRUITS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("That response is too weak for this story.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.fruit is None or c[1] == args.fruit)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, fruit, response = rng.choice(sorted(combos))
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    return StoryParams(setting, fruit, response, delay)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    fruit = f["fruit_kind"]
    setting = f["setting"]
    return [
        f'Write a heartwarming but sad kitchen story that includes the words "inflection", "rot", and "fat".',
        f"Tell a gentle family story set in {setting.place} about {fruit.label} getting fat before it rots.",
        f"Write a child-friendly bad-ending story where a bowl of fruit reaches its inflection too late and the family comforts each other anyway.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    fruit = f["fruit_kind"]
    child = f["child"]
    parent = f["parent"]
    answers = [
        QAItem(
            question="What was happening to the fruit at first?",
            answer=f"It was growing fat and sweet in the bowl, and everyone could see it was nearing its inflection. That was the moment when it needed attention soon."
        ),
        QAItem(
            question="Why did the story turn sad?",
            answer=f"The family waited too long, so the fruit began to rot before they could use all of it. Once that happened, some of the bowl had to be thrown away."
        ),
        QAItem(
            question="How did the family respond?",
            answer=f"{parent.id} comforted {child.id} and helped save the last good pieces. They stayed gentle with each other even though the fruit was lost."
        ),
    ]
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does it mean when fruit is fat?", "It means the fruit is plump and full, like it has filled out as it ripened. That can be a sign it is close to being ready."),
        QAItem("What is rot?", "Rot is what happens when food gets old and starts to break down. It can smell bad and go soft."),
        QAItem("What is an inflection point?", "An inflection point is the exact moment when something changes from one state to another. With fruit, it can be the turning point from ripe to overripe."),
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


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], FRUITS[params.fruit], RESPONSES[params.response], params.delay)
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
fat(F) :- fruit(F).
rot(F) :- fruit(F), waited_too_long.
bad_ending :- rot(F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for fid in FRUITS:
        lines.append(asp.fact("fruit", fid))
    for rid in RESPONSES:
        lines.append(asp.fact("response", rid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, fruit=None, response=None, delay=None), random.Random(1)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


CURATED = [
    StoryParams("kitchen", "pears", "slice", 1),
    StoryParams("porch", "plums", "jam", 0),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
