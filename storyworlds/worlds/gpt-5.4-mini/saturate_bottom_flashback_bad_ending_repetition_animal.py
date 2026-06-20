#!/usr/bin/env python3
"""
Standalone storyworld: saturate_bottom_flashback_bad_ending_repetition_animal.py

A small animal-story domain about a beaver, a duck, and a pond basket.
The story always uses the seed words "saturate" and "bottom", and its core
instruments are:
- flashback
- repetition
- bad ending

The world model tracks a little physical scene with meters and emotional memes.
A repeated warning builds tension, a flashback explains why the warning matters,
and the ending can go badly when an unsafe choice is made.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    scene: str
    place_line: str
    bottom_line: str
    sound: str

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
class ObjectThing:
    id: str
    label: str
    phrase: str
    region: str
    can_soak: bool = False
    can_sink: bool = False
    heavy: bool = False
    plural: bool = False
    tags: set[str] = field(default_factory=set)

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
class AnimalPair:
    id: str
    hero: str
    friend: str
    animal: str
    hero_type: str
    friend_type: str
    home: str
    shared_goal: str
    tiny_detail: str
    ending_image: str

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
@dataclass
class StoryParams:
    setting: str
    pair: str
    object: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
    apply: callable

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


def _r_saturate(world: World) -> list[str]:
    out = []
    basket = world.entities.get("basket")
    water = world.entities.get("water")
    if not basket or not water:
        return out
    if basket.meters["wet"] < THRESHOLD:
        return out
    sig = ("saturate",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if basket.meters["wet"] >= THRESHOLD:
        basket.meters["soggy"] += 1
        water.meters["full"] += 1
        out.append("__soggy__")
    return out


def _r_bottom(world: World) -> list[str]:
    basket = world.entities.get("basket")
    if basket and basket.meters["soggy"] >= THRESHOLD and "bottom" not in world.fired:
        world.fired.add(("bottom",))
        basket.meters["heavy"] += 1
    return []


RULES = [Rule("saturate", _r_saturate), Rule("bottom", _r_bottom)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        for r in RULES:
            sents = r.apply(world)
            if sents:
                changed = True
                for s in sents:
                    if not s.startswith("__"):
                        world.say(s)


def build_scene() -> dict[str, Setting]:
    return {
        "pond": Setting(
            "pond",
            "A soft pond with reeds at the edge and a shiny path through the grass.",
            "The water looked calm, but the muddy bank waited at the bottom of the slope.",
            "The bottom of the pond was dark and cool.",
            "The frogs kept singing, as if the whole pond were holding its breath.",
        ),
        "riverbank": Setting(
            "riverbank",
            "A wide riverbank with grass, stones, and a shallow stream.",
            "The path ran down to the water and ended at the bottom by the rocks.",
            "The bottom of the stream was full of pebbles.",
            "The reeds whispered in the wind.",
        ),
    }


def build_pairs() -> dict[str, AnimalPair]:
    return {
        "beaver_duck": AnimalPair(
            "beaver_duck",
            hero="Bram the beaver",
            friend="Dot the duck",
            animal="animal",
            hero_type="beaver",
            friend_type="duck",
            home="pond",
            shared_goal="carry a pile of sticks to the dam",
            tiny_detail="Bram liked lining sticks into neat little rows.",
            ending_image="the basket sank low and the water lapped over the rim",
        ),
        "rabbit_fox": AnimalPair(
            "rabbit_fox",
            hero="Pip the rabbit",
            friend="Moss the fox",
            animal="animal",
            hero_type="rabbit",
            friend_type="fox",
            home="riverbank",
            shared_goal="bring clover to a small nest",
            tiny_detail="Pip always counted things twice when he was nervous.",
            ending_image="the basket split open and the clover slid into the mud",
        ),
    }


def build_objects() -> dict[str, ObjectThing]:
    return {
        "basket": ObjectThing("basket", "basket", "a wicker basket", "bottom", can_soak=True, can_sink=True, heavy=True, tags={"basket"}),
        "blanket": ObjectThing("blanket", "blanket", "a little blanket", "bottom", can_soak=True, tags={"blanket"}),
        "leaf_boat": ObjectThing("leaf_boat", "leaf boat", "a leaf boat", "water", can_sink=True, tags={"boat"}),
        "water": ObjectThing("water", "water", "the water", "water", can_soak=False, can_sink=False, tags={"water"}),
    }


SCENES = build_scene()
PAIRS = build_pairs()
OBJECTS = build_objects()


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, scene in SCENES.items():
        for pid, pair in PAIRS.items():
            for oid, obj in OBJECTS.items():
                if obj.can_soak and obj.can_sink:
                    combos.append((sid, pid, oid))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("setting", sid))
    for pid in PAIRS:
        lines.append(asp.fact("pair", pid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.can_soak:
            lines.append(asp.fact("can_soak", oid))
        if obj.can_sink:
            lines.append(asp.fact("can_sink", oid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, P, O) :- setting(S), pair(P), object(O), can_soak(O), can_sink(O).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, pair=None, object=None), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld with flashback, repetition, and a bad ending.")
    ap.add_argument("--setting", choices=SCENES)
    ap.add_argument("--pair", choices=PAIRS)
    ap.add_argument("--object", choices=OBJECTS)
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
              if (args.setting is None or c[0] == args.setting)
              and (args.pair is None or c[1] == args.pair)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, pair, obj = rng.choice(sorted(combos))
    return StoryParams(setting=setting, pair=pair, object=obj)


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    pair = f["pair"]
    obj = f["obj"]
    return [
        QAItem(
            question=f"Why did {pair.hero} keep warning about the basket?",
            answer=(
                f"{pair.hero} remembered the time the basket had soaked up water at the bottom of the pond. "
                f"That flashback made the warning sound serious, because the same thing could happen again."
            ),
        ),
        QAItem(
            question="What happened at the end of the story?",
            answer=(
                f"The ending was bad: the basket grew too heavy, sank, and lost the food inside it. "
                f"The repeated warning could not stop the mistake in time."
            ),
        ),
        QAItem(
            question=f"What was wet enough to {obj.label_word}?",
            answer=(
                f"The basket was wet enough to saturate. Water had reached the bottom and soaked through the wicker."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    pair = f["pair"]
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a quick look back at something that happened earlier. It helps explain why a character feels worried now.",
        ),
        QAItem(
            question="Why do repeated warnings matter?",
            answer="Repeated warnings show that a character is trying hard to stop a problem. They can build tension because the danger keeps coming back.",
        ),
        QAItem(
            question="What does it mean for something to saturate?",
            answer="To saturate means to soak something until it is full of liquid. When a thing saturates, it can become heavy and weak.",
        ),
        QAItem(
            question=f"What kind of animal is {pair.hero}?",
            answer=f"{pair.hero} is a beaver, and {pair.friend} is a duck.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    pair = f["pair"]
    return [
        f"Write an animal story with a flashback, repetition, and a bad ending about {pair.hero} and {pair.friend}.",
        f"Tell a story that uses the words saturate and bottom and ends badly for the basket.",
        f"Write a short animal story where the warning is repeated again and again, but the mistake still happens.",
    ]


def render_story(world: World) -> None:
    f = world.facts
    pair: AnimalPair = f["pair"]
    obj: ObjectThing = f["obj"]
    setting: Setting = f["setting"]

    world.say(f"{pair.hero} and {pair.friend} lived near {setting.scene.lower()}.")
    world.say(f"{pair.tiny_detail} Every day, they carried little things in {obj.phrase}.")
    world.say(f'"Careful at the {obj.label_word} bottom," said {pair.friend}. "Careful at the bottom."')
    world.say(f'Later, {pair.hero} remembered a flashback: yesterday the basket had slipped into the water and begun to saturate, slowly and slowly.')
    world.para()
    world.say(f'Today, the same warning came back again. "Careful at the bottom," said {pair.friend}. "Careful at the bottom."')
    world.say(f"But {pair.hero} laughed, pushed the basket closer to the edge, and tried to hurry the job.")
    world.say(f'The basket wobbled, fell, and the water rushed up to saturate the wicker from the bottom.')
    world.say(f'By the time {pair.friend} shouted again, it was too late.')
    world.para()
    world.say(f"The basket sank lower and lower.")
    world.say(f"The food tipped out, the sticks floated away, and {pair.ending_image}.")
    world.say(f"{pair.hero} and {pair.friend} stared at the empty water and did not smile.")
    world.say("That was the end of the day, and it was a bad ending.")


def generate(params: StoryParams) -> StorySample:
    world = World(SCENES[params.setting])
    pair = PAIRS[params.pair]
    obj = OBJECTS[params.object]
    world.facts.update(setting=SCENES[params.setting], pair=pair, obj=obj)
    world.add(Entity("hero", kind="character", type=pair.hero_type, label=pair.hero, role="hero"))
    world.add(Entity("friend", kind="character", type=pair.friend_type, label=pair.friend, role="friend"))
    world.add(Entity("basket", type="thing", label=obj.label))
    world.add(Entity("water", type="thing", label="water"))
    world.get("basket").meters["wet"] = 0.0
    world.get("water").meters["full"] = 0.0

    render_story(world)
    world.get("basket").meters["wet"] += 1
    propagate(world, narrate=False)
    world.get("basket").meters["wet"] += 1
    propagate(world, narrate=False)
    world.facts["outcome"] = "bad"

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("pond", "beaver_duck", "basket"),
    StoryParams("riverbank", "rabbit_fox", "basket"),
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
