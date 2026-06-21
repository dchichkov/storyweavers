#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/caboose_messenger_tidal_pool_foreshadowing_kindness_mystery.py
===============================================================================================

A standalone storyworld for a tiny mystery set at a tidal pool.

Premise:
- A child explorer at a tidal pool notices an odd message from a messenger.
- Clues foreshadow a hidden problem around the caboose.
- Kindness helps the characters share information, solve the mystery, and end
  with a small, bright image that proves the change.

The simulation is state-driven: physical meters track clues, tide, and discovered
objects; emotional memes track worry, curiosity, and kindness. The renderer
turns the state transitions into child-facing prose.

Supports:
- default run
- -n, --all, --seed, --trace, --qa, --json
- --asp, --verify, --show-asp
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
EVIDENCE_MIN = 2
TIDE_WARN_LEVEL = 2
TIDE_DANGER_LEVEL = 3


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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone
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


@dataclass
class Rule:
    name: str
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


def _r_tide_rises(world: World) -> list[str]:
    out: list[str] = []
    tide = world.get("tide")
    if tide.meters["level"] < TIDE_WARN_LEVEL:
        return out
    sig = ("tide_rises", int(tide.meters["level"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in list(world.entities.values()):
        if e.role == "messenger":
            e.memes["worry"] += 1
        if e.role == "child":
            e.memes["curiosity"] += 1
    out.append("__tide__")
    return out


def _r_footprints(world: World) -> list[str]:
    out: list[str] = []
    if world.get("clue").meters["seen"] < THRESHOLD:
        return out
    sig = ("footprints",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("clue").meters["evidence"] += 1
    out.append("The wet sand held a clue-shaped print near the rocks.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    rules = [Rule("tide", _r_tide_rises), Rule("footprints", _r_footprints)]
    while changed:
        changed = False
        for rule in rules:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    setting: str
    style: str
    feature1: str
    feature2: str
    hero: str
    hero_gender: str
    messenger: str
    messenger_gender: str
    caboose: str
    tide_level: int = 1
    clue_kind: str = "shell"
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


SETTINGS = {
    "tidal_pool": {
        "place": "the tidal pool",
        "scene": "a quiet cove with shiny rocks and little pools of water",
        "dark_spot": "the far rocks where the water slipped in and out",
    }
}

FEATURES = {"foreshadowing": "foreshadowing", "kindness": "kindness"}
STYLES = {"mystery": "mystery"}

HERO_NAMES = ["Mira", "Nina", "Owen", "Tess", "Arlo", "Ivy", "Jun", "Lena"]
MESSENGER_NAMES = ["Pip", "Wren", "Rowan", "Bea", "Moss", "June", "Rae", "Kit"]
CABOOSE_NAMES = ["Caboose", "the caboose", "old caboose"]

CURATED = [
    StoryParams(
        setting="tidal_pool",
        style="mystery",
        feature1="foreshadowing",
        feature2="kindness",
        hero="Mira",
        hero_gender="girl",
        messenger="Pip",
        messenger_gender="boy",
        caboose="old caboose",
        tide_level=3,
        clue_kind="shell",
    ),
    StoryParams(
        setting="tidal_pool",
        style="mystery",
        feature1="kindness",
        feature2="foreshadowing",
        hero="Owen",
        hero_gender="boy",
        messenger="Wren",
        messenger_gender="girl",
        caboose="caboose",
        tide_level=2,
        clue_kind="rope",
    ),
]


def valid_combos() -> list[tuple[str, int]]:
    combos = []
    for setting in SETTINGS:
        for level in range(1, 4):
            combos.append((setting, level))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Storyworld: a tidal-pool mystery with kindness and foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--style", choices=STYLES)
    ap.add_argument("--feature1", choices=FEATURES)
    ap.add_argument("--feature2", choices=FEATURES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--messenger")
    ap.add_argument("--messenger-gender", choices=["girl", "boy"])
    ap.add_argument("--caboose")
    ap.add_argument("--tide-level", type=int, choices=[1, 2, 3])
    ap.add_argument("--clue-kind", choices=["shell", "rope", "key", "map"])
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
    setting = args.setting or "tidal_pool"
    style = args.style or "mystery"
    f1 = args.feature1 or "foreshadowing"
    f2 = args.feature2 or "kindness"
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    messenger_gender = args.messenger_gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(HERO_NAMES)
    messenger = args.messenger or rng.choice([n for n in MESSENGER_NAMES if n != hero])
    caboose = args.caboose or rng.choice(CABOOSE_NAMES)
    tide_level = args.tide_level or rng.choice([1, 2, 3])
    clue_kind = args.clue_kind or rng.choice(["shell", "rope", "key", "map"])
    return StoryParams(setting=setting, style=style, feature1=f1, feature2=f2, hero=hero,
                       hero_gender=hero_gender, messenger=messenger, messenger_gender=messenger_gender,
                       caboose=caboose, tide_level=tide_level, clue_kind=clue_kind)


def _make_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("Only the tidal-pool setting is supported.")
    if params.style != "mystery":
        raise StoryError("This world keeps a mystery style.")
    if {params.feature1, params.feature2} != {"foreshadowing", "kindness"}:
        raise StoryError("This storyworld needs foreshadowing and kindness.")
    if params.tide_level not in (1, 2, 3):
        raise StoryError("The tide level must be 1, 2, or 3.")
    w = World()
    hero = w.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="child"))
    messenger = w.add(Entity(id=params.messenger, kind="character", type=params.messenger_gender, role="messenger"))
    caboose = w.add(Entity(id="caboose", kind="thing", type="thing", label=params.caboose))
    tide = w.add(Entity(id="tide", kind="thing", type="thing", label="tide"))
    clue = w.add(Entity(id="clue", kind="thing", type="thing", label=params.clue_kind))
    tide.meters["level"] = float(params.tide_level)
    clue.meters["seen"] = 0.0
    clue.meters["evidence"] = 0.0
    hero.memes["curiosity"] = 1.0
    messenger.memes["worry"] = 0.0
    w.facts.update(params=params, hero=hero, messenger=messenger, caboose=caboose, tide=tide, clue=clue)
    return w


def tell(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    messenger: Entity = f["messenger"]
    caboose: Entity = f["caboose"]
    tide: Entity = f["tide"]
    clue: Entity = f["clue"]
    scene = SETTINGS["tidal_pool"]["scene"]

    world.say(
        f"{hero.id} came to {SETTINGS['tidal_pool']['place']} where the shore felt like a little secret, "
        f"{scene}. Near the water stood {caboose.label_word}, and {hero.id} wanted to know why it seemed out of place."
    )
    world.say(
        f"Then a messenger named {messenger.id} arrived with a damp note tucked under one arm. "
        f'"Look for the sign before the tide turns," {messenger.id} said, and pointed toward the rocks.'
    )

    world.para()
    clue.meters["seen"] = 1.0
    world.say(
        f"{hero.id} found {clue.label_word} pressed into the sand. That felt like a clue, but it also felt like a warning."
    )
    if tide.meters["level"] >= TIDE_WARN_LEVEL:
        world.say(
            f"The water kept edging closer. Every small wave made the tip of {caboose.label_word} look less forgotten and more important."
        )
    propagate(world)

    world.para()
    messenger.memes["kindness"] = 1.0
    hero.memes["kindness"] = 1.0
    world.say(
        f"{hero.id} did not brush the messenger aside. Instead, {hero.id} listened carefully and shared a dry towel, and that kindness made {messenger.id} tell the whole truth."
    )
    world.say(
        f"The note was about a hidden latch in {caboose.label_word}. Someone had been leaving little signs so the right person would notice before the tide covered everything."
    )

    world.para()
    clue.meters["evidence"] += 1
    tide.meters["level"] = max(0.0, tide.meters["level"] - 1.0)
    world.say(
        f"Together they checked the sand, followed the foreshadowed clues, and found the lost latch before the water could swallow it."
    )
    world.say(
        f"{hero.id} opened {caboose.label_word} and found a tiny box of returned treasures inside, each one tagged and waiting."
    )
    world.say(
        f"The messenger smiled, and {hero.id} smiled back. The mystery was small, but the kindness made it feel important."
    )
    world.say(
        f"When they left, the tide was lower, the note was dry, and {caboose.label_word} no longer looked lonely at the edge of the pool."
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    messenger: Entity = f["messenger"]
    caboose: Entity = f["caboose"]
    tide: Entity = f["tide"]
    return [
        QAItem(
            question="What was the story about?",
            answer=f"It was about {hero.id}, a messenger named {messenger.id}, and a mystery at the tidal pool. The clues pointed toward {caboose.label_word}, and the answer came from paying attention kindly."
        ),
        QAItem(
            question=f"Why did the clue matter?",
            answer=f"The clue warned that the tide was moving and that something near {caboose.label_word} needed to be found before the water covered it. Because {hero.id} followed the clue, the hidden latch was discovered in time."
        ),
        QAItem(
            question="How did kindness help?",
            answer=f"{hero.id} listened to {messenger.id}, shared a towel, and stayed calm. That made {messenger.id} trust {hero.id} enough to explain the secret, and the two of them solved the mystery together."
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The tide was lower, the clues were understood, and {caboose.label_word} was no longer a puzzle. The small box of returned treasures showed that the mystery had been solved."
        ),
    ]


def prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    messenger: Entity = f["messenger"]
    caboose: Entity = f["caboose"]
    return [
        f"Write a child-friendly mystery story set at a tidal pool with foreshadowing and kindness, and include the words caboose and messenger.",
        f"Tell a short mystery where {hero.id} follows a clue from a messenger and learns what is hidden near {caboose.label_word}.",
        f"Write a story about a tidal pool, a waiting caboose, and a kind messenger whose warning makes the puzzle clearer.",
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tidal pool?",
            answer="A tidal pool is a small pool of seawater left behind near the shore when the tide goes out. It can change as the water moves in and out."
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small hint about something important that will matter later. It helps readers notice clues before the answer arrives."
        ),
        QAItem(
            question="Why is kindness useful in a mystery?",
            answer="Kindness helps people trust each other and share clues. When someone feels safe, they are more likely to explain what they know."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== (2) Story questions =="]
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    try:
        world = _make_world(params)
    except KeyError as exc:
        raise StoryError(f"Invalid parameter key: {exc}") from exc
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "tidal_pool"),
        asp.fact("style", "mystery"),
        asp.fact("feature", "foreshadowing"),
        asp.fact("feature", "kindness"),
        asp.fact("tide_level", 1),
        asp.fact("tide_level", 2),
        asp.fact("tide_level", 3),
        asp.fact("warn_level", TIDE_WARN_LEVEL),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
compatible(S) :- setting(S), S = tidal_pool.
mystery_style(mystery).
feature_ok(foreshadowing).
feature_ok(kindness).
story_ok :- compatible(tidal_pool), mystery_style(mystery), feature_ok(foreshadowing), feature_ok(kindness).
rising_tide(L) :- tide_level(L), warn_level(M), L >= M.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_compatible() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show compatible/1."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    rc = 0
    py = {"tidal_pool"}
    clingo = {s[0] for s in asp_compatible()}
    if py == clingo:
        print("OK: ASP compatibility matches Python.")
    else:
        print("MISMATCH: compatibility differs.")
        rc = 1

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: story generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_valid_combos() -> list[tuple[str, int]]:
    return valid_combos()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or "tidal_pool"
    style = args.style or "mystery"
    feature1 = args.feature1 or "foreshadowing"
    feature2 = args.feature2 or "kindness"
    hero = args.hero or rng.choice(HERO_NAMES)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    messenger = args.messenger or rng.choice([n for n in MESSENGER_NAMES if n != hero])
    messenger_gender = args.messenger_gender or rng.choice(["girl", "boy"])
    caboose = args.caboose or rng.choice(CABOOSE_NAMES)
    tide_level = args.tide_level or rng.choice([1, 2, 3])
    clue_kind = args.clue_kind or rng.choice(["shell", "rope", "key", "map"])
    if setting != "tidal_pool":
        raise StoryError("Only tidal_pool is valid in this storyworld.")
    if style != "mystery":
        raise StoryError("Only mystery style is supported.")
    return StoryParams(
        setting=setting,
        style=style,
        feature1=feature1,
        feature2=feature2,
        hero=hero,
        hero_gender=hero_gender,
        messenger=messenger,
        messenger_gender=messenger_gender,
        caboose=caboose,
        tide_level=tide_level,
        clue_kind=clue_kind,
    )


def valid_combos() -> list[tuple[str, int]]:
    return [("tidal_pool", level) for level in (1, 2, 3)]


def generation_sample(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show compatible/1.\n#show rising_tide/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible settings: tidal_pool")
        print("tide levels:", ", ".join(str(n) for n in (1, 2, 3)))
        return

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
