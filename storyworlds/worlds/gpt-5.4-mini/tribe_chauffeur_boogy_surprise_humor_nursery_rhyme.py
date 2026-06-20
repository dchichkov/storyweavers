#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tribe_chauffeur_boogy_surprise_humor_nursery_rhyme.py
======================================================================================

A small, standalone story world for a nursery-rhyme style surprise comedy:
a little tribe plans a cheerful outing, a chauffeur drives them, and a boogy
creature or boogy dance adds a funny surprise before the ending turns warm and
bright.

This world keeps the contract: typed entities with meters and memes, a
forward-chained world model, a Python reasonableness gate, inline ASP twin,
three QA sets, and a complete CLI supporting default runs, --all, --qa,
--json, --trace, --asp, --verify, and --show-asp.
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
    traits: list[str] = field(default_factory=list)
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
        return self.label or self.id



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
    rhyme: str
    weather: str
    holds: set[str] = field(default_factory=set)

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
class Transport:
    id: str
    label: str
    phrase: str
    wheels: int
    seats: int
    smooth: bool
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


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    surprise_kind: str
    funny: str
    ending: str
    joy_gain: float
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

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


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    if world.get("boogy").meters["surprised"] < THRESHOLD:
        return out
    sig = ("surprise", "boogy")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("tribe").memes["joy"] += 1
    world.get("boogy").memes["joy"] += 1
    out.append("__surprise__")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    if world.get("chauffeur").memes["humor"] < THRESHOLD:
        return out
    sig = ("laugh", "chauffeur")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("tribe").memes["laugh"] += 1
    out.append("__laugh__")
    return out


CAUSAL_RULES = [Rule("surprise", "social", _r_surprise), Rule("laugh", "social", _r_laugh)]


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


def reasonableness_ok(setting: Setting, transport: Transport, surprise: Surprise) -> bool:
    return setting.id in SETTINGS and transport.smooth and surprise.joy_gain >= 1.0


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid, transport in TRANSPORTS.items():
            for rid, surprise in SURPRISES.items():
                if reasonableness_ok(setting, transport, surprise):
                    combos.append((sid, tid, rid))
    return combos


def _do_drive(world: World, chauffeur: Entity, tribe: Entity, transport: Transport) -> None:
    chauffeur.meters["motion"] += 1
    tribe.meters["distance"] += 1
    world.say(
        f"The {transport.label} rolled along the lane, and the {chauffeur.label_word} hummed a tune "
        f"while the tribe rode in a neat little row."
    )


def _setup(world: World, tribe: Entity, chauffeur: Entity, setting: Setting, transport: Transport) -> None:
    tribe.memes["expectation"] += 1
    chauffeur.memes["care"] += 1
    world.say(
        f"Down by the mossy road, the {setting.rhyme} shone with dew, and a tiny tribe was ready for a view."
    )
    world.say(
        f"They climbed into the {transport.label}, where the {chauffeur.label_word} sat smiling bright, "
        f"and off they went in the morning light."
    )


def _hint_surprise(world: World, boogy: Entity, surprise: Surprise) -> None:
    boogy.memes["curiosity"] += 1
    world.say(
        f"At the end of the lane stood {boogy.id}, peeking round a tree, with a wink and a wobble and a grin of glee."
    )
    world.say(
        f'"Look there," chirped the chauffeur, "it\'s a {surprise.label} surprise, as funny as a pair of moon pies!"'
    )


def _trigger(world: World, boogy: Entity, surprise: Surprise) -> None:
    boogy.meters["surprised"] += 1
    world.say(
        f"Then who should pop up but {boogy.id} with {surprise.phrase}, and the little tribe gasped, "
        f"for nobody had guessed that day."
    )


def _laugh(world: World, chauffeur: Entity, surprise: Surprise) -> None:
    chauffeur.memes["humor"] += 1
    world.say(
        f"The {chauffeur.label_word} laughed so hard at the {surprise.funny} that even the lane seemed to grin."
    )


def _ending(world: World, tribe: Entity, boogy: Entity, chauffeur: Entity, surprise: Surprise) -> None:
    tribe.memes["joy"] += 1
    boogy.memes["joy"] += 1
    world.say(
        f"Together they made the {surprise.ending}, and the {tribe.id} danced a tiny boogy under the blue sky."
    )
    world.say(
        f"By the time the wheels came home, the tribe was merry, the chauffeur was beaming, and {boogy.id} was waving like a sparkly flag."
    )


def tell(setting: Setting, transport: Transport, surprise: Surprise) -> World:
    world = World(setting)
    tribe = world.add(Entity(id="tribe", kind="character", type="group", label="tribe", role="family"))
    chauffeur = world.add(Entity(id="chauffeur", kind="character", type="adult", label="chauffeur", role="driver"))
    boogy = world.add(Entity(id="boogy", kind="character", type="sprite", label="boogy", role="guest"))

    _setup(world, tribe, chauffeur, setting, transport)
    world.para()
    _do_drive(world, chauffeur, tribe, transport)
    _hint_surprise(world, boogy, surprise)
    _trigger(world, boogy, surprise)
    propagate(world, narrate=False)
    world.para()
    _laugh(world, chauffeur, surprise)
    _ending(world, tribe, boogy, chauffeur, surprise)

    world.facts.update(
        tribe=tribe,
        chauffeur=chauffeur,
        boogy=boogy,
        setting=setting,
        transport=transport,
        surprise=surprise,
        outcome="surprised",
    )
    return world


SETTINGS = {
    "lanes": Setting("lanes", "a narrow lane", "the lane was merry with dew", "morning", {"road"}),
    "meadow": Setting("meadow", "a little meadow", "the meadow was bright with clover", "morning", {"grass"}),
    "village": Setting("village", "a village green", "the village green was neat and neat", "afternoon", {"road", "grass"}),
}

TRANSPORTS = {
    "car": Transport("car", "car", "a shiny little car", 4, 4, True, {"ride"}),
    "carriage": Transport("carriage", "carriage", "a painted carriage", 4, 6, True, {"ride"}),
    "van": Transport("van", "van", "a round-nosed van", 4, 8, True, {"ride"}),
}

SURPRISES = {
    "cake": Surprise("cake", "cake", "a lopsided birthday cake", "party", "frosting", "sweet birthday cheer", 1.0, {"sweet"}),
    "drum": Surprise("drum", "drum", "a tiny drum and a big bow", "music", "bop-bop", "happy clapping parade", 1.0, {"music"}),
    "kite": Surprise("kite", "kite", "a bright kite with bells", "play", "jingle", "sky-high kite waving", 1.0, {"play"}),
}

CHILD_NAMES = ["Mina", "Toby", "Nell", "Oren", "Pip", "Lula"]
TRAITS = ["spry", "cheery", "curious"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    transport: str
    surprise: str
    name: str
    trait: str
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
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world: tribe, chauffeur, boogy, surprise, and humor.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--transport", choices=TRANSPORTS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--name", choices=CHILD_NAMES)
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
              and (args.transport is None or c[1] == args.transport)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, transport, surprise = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        transport=transport,
        surprise=surprise,
        name=args.name or rng.choice(CHILD_NAMES),
        trait=rng.choice(TRAITS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style story that includes the words "tribe", "chauffeur", and "boogy", with a surprise and a little humor.',
        f"Tell a playful story about a {f['setting'].place} where a tribe rides with a chauffeur and meets boogy at the end.",
        f'Write a short, bouncy story where a chauffeur takes a tribe somewhere surprising, and boogy makes everybody laugh.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting, transport, surprise = f["setting"], f["transport"], f["surprise"]
    return [
        QAItem(
            question="Who was the story about?",
            answer="It was about a tribe, a chauffeur, and boogy, all in one little outing.",
        ),
        QAItem(
            question="What did the chauffeur do?",
            answer=f"The chauffeur drove the {transport.label} along the lane and took the tribe toward a surprise.",
        ),
        QAItem(
            question="What made the story funny?",
            answer=f"Boogy jumped out with {surprise.phrase}, and the chauffeur laughed at the silly {surprise.funny} moment.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {surprise.ending} and the tribe dancing happily under the sky.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a chauffeur?",
            answer="A chauffeur is a driver who takes people places in a car or carriage.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you do not expect, so it can make people gasp or laugh.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is the part of a story that makes people smile or laugh.",
        ),
        QAItem(
            question="What is a boogy?",
            answer="In this story world, boogy is a silly little guest who loves wobbly, funny entrances.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("lanes", "car", "cake", "Mina", "spry"),
    StoryParams("meadow", "carriage", "drum", "Toby", "cheery"),
    StoryParams("village", "van", "kite", "Nell", "curious"),
]


def explain_rejection(setting: Setting, transport: Transport, surprise: Surprise) -> str:
    return "(No story: the chosen pieces do not make a gentle, reasonable nursery-rhyme surprise.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TRANSPORTS.items():
        lines.append(asp.fact("transport", tid))
        if t.smooth:
            lines.append(asp.fact("smooth", tid))
    for rid, r in SURPRISES.items():
        lines.append(asp.fact("surprise", rid))
        lines.append(asp.fact("joy_gain", rid, r.joy_gain))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, T, R) :- setting(S), transport(T), smooth(T), surprise(R), joy_gain(R, J), sense_min(M), J >= 1, M = 2.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import sys as _sys
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        ok = False
        print("MISMATCH in gate.")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, transport=None, surprise=None, name=None), random.Random(7)))
        assert sample.story
        print("OK: smoke test generated a story.")
    except Exception as e:
        ok = False
        print(f"SMOKE TEST FAILED: {e}")
    return 0 if ok else 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TRANSPORTS[params.transport], SURPRISES[params.surprise])
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
