#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/manicotti_slow_surprise_transformation_moral_value_whodunit.py
=================================================================================================

A standalone story world for a tiny whodunit in a kitchen.

Premise:
- A family is preparing manicotti.
- The sauce or filling is being made slowly.
- A surprise happens: the manicotti "mystery" changes shape, filling, or color.
- The detective-like child investigates clues, learns the truth, and ends with a moral value:
  be patient, tell the truth, and help rather than blame.

The domain is small on purpose:
- one kitchen
- a few typed entities
- a single mystery setup
- a transformation beat
- a moral-resolution beat

This script follows the Storyweavers contract:
- stdlib only
- imports results eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes Python validity checks plus an inline ASP twin
- generates three QA sets from world state
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
SLOW_MIN = 2
MORAL_MIN = 1

KITCHEN_PLACES = ["kitchen", "small kitchen", "sunny kitchen"]
CHARACTER_NAMES = ["Mila", "Nina", "Owen", "Leo", "Ava", "Eli", "Ruby", "Theo"]
ADULT_NAMES = ["Mom", "Dad", "Grandma"]
TRAITS = ["patient", "curious", "careful", "honest", "kind"]

MYSTERY_WORDS = ["slow", "surprise", "manicotti"]


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
        female = {"girl", "mother", "mom", "woman", "grandma"}
        male = {"boy", "father", "dad", "man", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mom": "mom", "dad": "dad", "grandma": "grandma"}.get(self.label, self.label or self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    has_timer: bool = True
    has_bowl: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class FoodItem:
    id: str
    label: str
    phrase: str
    kind: str
    can_transform: bool = False
    slow_state: str = ""
    surprise_state: str = ""
    moral_value: str = ""

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Clue:
    id: str
    label: str
    explains: str
    tag: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
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

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_wait(world: World) -> list[str]:
    out: list[str] = []
    if "dish" not in world.entities:
        return out
    dish = world.get("dish")
    if dish.meters["slow"] < THRESHOLD:
        return out
    sig = ("wait",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in list(world.entities.values()):
        if e.role == "detective":
            e.memes["focus"] += 1
    out.append("__wait__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    if "dish" not in world.entities:
        return out
    dish = world.get("dish")
    if dish.meters["changed"] < THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("__transform__")
    return out


CAUSAL_RULES = [Rule("wait", "social", _r_wait), Rule("transform", "physical", _r_transform)]


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


def slow_enough(item: FoodItem) -> bool:
    return item.slow_state == "slow" or item.kind == "ricotta"


def valid_mystery(food: FoodItem) -> bool:
    return food.can_transform


def mystery_resolution(food: FoodItem) -> str:
    if food.kind == "manicotti":
        return "the manicotti was really stuffed with a hidden surprise"
    return f"the {food.label} changed in a way that made the clue obvious"


def _do_mystery(world: World, dish: Entity, food: FoodItem) -> None:
    dish.meters["slow"] += 1
    if food.can_transform:
        dish.meters["changed"] += 1
    propagate(world, narrate=False)


def setup(world: World, detective: Entity, helper: Entity, food: FoodItem) -> None:
    world.say(
        f"On a quiet evening, {detective.id} and {helper.id} were in {world.setting.place}, "
        f"where a pot of {food.phrase} was being made."
    )
    world.say(
        f"The work was slow, and that gave {detective.id} time to watch every clue."
    )


def clue_scene(world: World, detective: Entity, helper: Entity, food: FoodItem, clue: Clue) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f"{detective.id} noticed a small clue: {clue.label}. "
        f"It seemed to explain why the {food.label} looked different."
    )
    world.say(
        f'"That is strange," {detective.id} said. "{clue.explains}?"'
    )


def surprise(world: World, detective: Entity, helper: Entity, food: FoodItem) -> None:
    world.say(
        f"Then came a surprise. The {food.label} changed at once, and the kitchen went very still."
    )
    world.say(
        f"{helper.id} blinked, but {detective.id} kept looking, because the answer was hiding in plain sight."
    )


def reveal(world: World, detective: Entity, helper: Entity, food: FoodItem, clue: Clue) -> None:
    world.say(
        f"At last, {detective.id} put the clues together. {mystery_resolution(food).capitalize()}."
    )
    world.say(
        f"{helper.id} laughed softly and admitted the truth: {clue.explains.lower()}."
    )


def moral(world: World, detective: Entity, helper: Entity, food: FoodItem) -> None:
    detective.memes["moral"] += 1
    helper.memes["moral"] += 1
    world.say(
        f"{detective.id} learned a good moral value: be patient, stay honest, and let the truth come out slowly."
    )
    world.say(
        f"In the end, the {food.label} was finished, the mystery was solved, and the kitchen felt warm again."
    )


def tell(setting: Setting, food: FoodItem, clue: Clue, name: str = "Mila",
         name2: str = "Mom") -> World:
    world = World(setting)
    detective = world.add(Entity(id=name, kind="character", type="girl", role="detective"))
    helper = world.add(Entity(id=name2, kind="character", type="mother", role="helper", label="mom"))
    dish = world.add(Entity(id="dish", type="food", label=food.label))
    setup(world, detective, helper, food)
    world.para()
    clue_scene(world, detective, helper, food, clue)
    if food.can_transform:
        _do_mystery(world, dish, food)
        world.para()
        surprise(world, detective, helper, food)
        reveal(world, detective, helper, food, clue)
        world.para()
        moral(world, detective, helper, food)
    else:
        world.say("Nothing changed, so there was no real mystery to solve.")
    world.facts.update(detective=detective, helper=helper, dish=dish, food=food, clue=clue)
    return world


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen"),
    "small_kitchen": Setting("small_kitchen", "a small kitchen"),
    "sunny_kitchen": Setting("sunny_kitchen", "a sunny kitchen"),
}

FOODS = {
    "manicotti": FoodItem(
        id="manicotti",
        label="manicotti",
        phrase="slow manicotti",
        kind="manicotti",
        can_transform=True,
        slow_state="slow",
        surprise_state="surprise",
        moral_value="patience",
    ),
    "soup": FoodItem(
        id="soup",
        label="soup",
        phrase="slow soup",
        kind="soup",
        can_transform=True,
        slow_state="slow",
        surprise_state="surprise",
        moral_value="honesty",
    ),
    "bread": FoodItem(
        id="bread",
        label="bread",
        phrase="fresh bread",
        kind="bread",
        can_transform=False,
    ),
}

CLUES = {
    "steam": Clue("steam", "a curl of steam", "the pot was still hot", "steam"),
    "lid": Clue("lid", "a tilted lid", "someone had peeked inside", "lid"),
    "note": Clue("note", "a tiny note", "the helper had left a secret message", "note"),
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    food: str
    clue: str
    detective: str
    helper: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for fid, food in FOODS.items():
            for cid in CLUES:
                if valid_mystery(food):
                    combos.append((sid, fid, cid))
    return combos


def explain_rejection(food: FoodItem) -> str:
    return f"(No story: {food.label} does not support a real transformation mystery.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny kitchen whodunit with manicotti, slow clues, surprise, transformation, and moral value.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name", choices=CHARACTER_NAMES)
    ap.add_argument("--helper", choices=ADULT_NAMES)
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
    if args.food and not valid_mystery(FOODS[args.food]):
        raise StoryError(explain_rejection(FOODS[args.food]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.food is None or c[1] == args.food)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, food, clue = rng.choice(sorted(combos))
    name = args.name or rng.choice(CHARACTER_NAMES)
    helper = args.helper or rng.choice(ADULT_NAMES)
    return StoryParams(setting, food, clue, name, helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a whodunit-style story for a young child that includes "{f["food"].label}" and the word "slow".',
        f"Tell a kitchen mystery where {f['detective'].id} notices a surprise while {f['food'].label} is being made slowly.",
        f"Write a gentle mystery story about a transformation in the kitchen and a moral value learned at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    food = f["food"]
    clue = f["clue"]
    detective = f["detective"]
    helper = f["helper"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {detective.id} and {helper.id}, who were making {food.label} together in the kitchen. The slow cooking gives the story its mystery feel."
        ),
        QAItem(
            question="What was the surprise?",
            answer=f"The surprise was that the {food.label} changed in a way the detective did not expect. That transformation became the main clue in the whodunit."
        ),
        QAItem(
            question="What moral value did the story teach?",
            answer="It taught patience and honesty. The child learns to look carefully, wait for the truth, and let the helper explain what really happened."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does 'slow' mean in cooking?",
            answer="It means something takes time and cannot be rushed. Slow cooking often helps flavors change little by little."
        ),
        QAItem(
            question="What is manicotti?",
            answer="Manicotti is a pasta dish with tube-shaped pieces that are usually stuffed and baked with sauce."
        ),
        QAItem(
            question="What is a surprise in a mystery story?",
            answer="A surprise is an unexpected change or discovery that makes the characters look again and solve the puzzle."
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_combo(S,F,C) :- setting(S), food(F), clue(C), can_transform(F).
outcome(transformed) :- can_transform(chosen_food).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for fid, food in FOODS.items():
        lines.append(asp.fact("food", fid))
        if food.can_transform:
            lines.append(asp.fact("can_transform", fid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], FOODS[params.food], CLUES[params.clue],
                 params.detective, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams("kitchen", "manicotti", "steam", "Mila", "Mom"),
    StoryParams("small_kitchen", "soup", "lid", "Owen", "Dad"),
    StoryParams("sunny_kitchen", "manicotti", "note", "Ava", "Grandma"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for t in combos:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
