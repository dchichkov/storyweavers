#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/crate_falcon_parody_kindness_fairy_tale.py
===========================================================================

A standalone fairy-tale story world about a broken crate, a proud falcon, a
playful parody song, and a kindness-led repair. The world simulates a tiny castle
yard where a child or young helper finds a cracked crate, worries about a falcon
that cannot perch, makes a cheeky parody to cheer everyone up, and then chooses
kindness to mend the problem.

The domain is intentionally small and state-driven:
- a crate can be cracked or mended,
- a falcon can be tired, worried, or calm,
- a parody can be silly but helpful or silly but unkind,
- kindness changes emotional state and can repair trust.

This script follows the Storyweavers contract:
- stdlib only
- imports shared result containers from storyworlds/results.py eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate and inline ASP twin
- generates three Q&A sets grounded in the simulated world
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman", "daughter"}
        male = {"boy", "father", "king", "man", "son"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Thing:
    id: str
    label: str
    kind: str = "thing"
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class World:
    entities: dict[str, Entity | Thing] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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


@dataclass
class Scene:
    id: str
    place: str
    opener: str
    castle_flavor: str
    dark_spot: str
    ending_image: str

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
class Crate:
    id: str
    label: str
    phrase: str
    role: str = "crate"
    stable: bool = True
    repairable: bool = True

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
class Falcon:
    id: str
    label: str
    phrase: str
    perch: str
    noble: str
    restless: bool = False

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
class Parody:
    id: str
    label: str
    tune: str
    mood: str
    kind_safe: bool = True
    risky: bool = False

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
class Help:
    id: str
    label: str
    method: str
    effect: str
    power: int
    sense: int

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
class StoryParams:
    pass

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
class StoryParams:
    scene: str
    crate: str
    falcon: str
    parody: str
    help: str
    hero: str
    hero_type: str
    elder: str
    elder_type: str
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


class WorldModel:
    pass


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if isinstance(ent, Entity) and ent.meters["concern"] >= THRESHOLD:
            sig = ("worry", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            for other in list(world.entities.values()):
                if isinstance(other, Entity) and other.kind == "character" and other.id != ent.id:
                    other.memes["care"] += 1
            out.append("__worry__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    elder = world.entities.get("elder")
    crate = world.entities.get("crate")
    falcon = world.entities.get("falcon")
    if not isinstance(hero, Entity) or not isinstance(elder, Entity) or not isinstance(crate, Thing) or not isinstance(falcon, Thing):
        return out
    if hero.memes["kindness"] < THRESHOLD:
        return out
    sig = ("kindness",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crate.meters["mended"] += 1
    crate.meters["crack"] = 0.0
    falcon.memes["trust"] += 1
    elder.memes["relief"] += 1
    out.append("__kindness__")
    return out


CAUSAL_RULES = [
    Rule("worry", "social", _r_worry),
    Rule("kindness", "social", _r_kindness),
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


SCENES = {
    "castle_yard": Scene(
        "castle_yard",
        "the castle yard",
        "On a bright morning beside the castle wall, a small helper and a tall elder were busy among the herbs and stones.",
        "The yard had banners, a pump well, and a watchful tower shadow.",
        "a hollow nook near the gate",
        "By the end, the crate stood mended under the gate lantern, and the falcon perched calm as a little crown."
    ),
    "orchard": Scene(
        "orchard",
        "the apple orchard",
        "At the edge of the orchard, where the grass went silver with dew, a child and an elder met beneath the trees.",
        "The orchard had ladders, baskets, and branches that whispered in the breeze.",
        "a low branch by the fence",
        "By the end, the crate was fixed beneath the apple tree, and the falcon watched the leaves without worry."
    ),
}

CRATES = {
    "apple_crate": Crate("apple_crate", "apple crate", "a wooden apple crate"),
    "grain_crate": Crate("grain_crate", "grain crate", "a stout grain crate"),
    "market_crate": Crate("market_crate", "market crate", "a market crate with rope handles"),
}

FALCONS = {
    "young_falcon": Falcon("young_falcon", "falcon", "a proud falcon", "the crate top", "noble"),
    "white_falcon": Falcon("white_falcon", "falcon", "a white falcon", "the crate rail", "bright"),
    "sleepy_falcon": Falcon("sleepy_falcon", "falcon", "a sleepy falcon", "the crate lid", "gentle"),
}

PARODIES = {
    "silly_song": Parody("silly_song", "parody song", "a tiny song", "silly", kind_safe=True),
    "mock_ballad": Parody("mock_ballad", "parody ballad", "a mock ballad", "playful", kind_safe=True),
    "teasing_song": Parody("teasing_song", "teasing parody", "a teasing rhyme", "snickering", kind_safe=False, risky=True),
}

HELPS = {
    "wood_glue": Help("wood_glue", "wood glue", "mend the split boards", "sealed the crack", 3, 3),
    "cord_tie": Help("cord_tie", "soft cord", "lace the crate tight", "held the sides close", 2, 2),
    "plank_patch": Help("plank_patch", "a spare plank", "brace the broken side", "made the crate steady", 4, 3),
}

GIRL_NAMES = ["Mira", "Lena", "Ayla", "Rosa", "Elin", "Nina"]
BOY_NAMES = ["Tobin", "Rian", "Silas", "Jon", "Hale", "Perrin"]
TRAITS = ["kind", "gentle", "bright", "brave", "patient", "merry"]


def reasonableness_gate(scene: Scene, crate: Crate, falcon: Falcon, parody: Parody, help_item: Help) -> bool:
    return crate.repairable and parody.kind_safe and help_item.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for scene in SCENES:
        for crate in CRATES:
            for falcon in FALCONS:
                for parody in PARODIES:
                    for help_id in HELPS:
                        if reasonableness_gate(SCENES[scene], CRATES[crate], FALCONS[falcon], PARODIES[parody], HELPS[help_id]):
                            combos.append((scene, crate, falcon, parody, help_id))
    return combos


def has_kindness(params: StoryParams) -> bool:
    return True


def tell(scene: Scene, crate: Crate, falcon: Falcon, parody: Parody, help_item: Help,
         hero_name: str, hero_type: str, elder_name: str, elder_type: str) -> World:
    world = World()
    hero = world.add(Entity("hero", kind="character", type=hero_type, label=hero_name, role="hero", traits=["kind"]))
    elder = world.add(Entity("elder", kind="character", type=elder_type, label=elder_name, role="elder", traits=["wise"]))
    cr = world.add(Thing("crate", crate.label))
    fa = world.add(Thing("falcon", falcon.label))
    pa = world.add(Thing("parody", parody.label))
    hi = world.add(Thing("help", help_item.label))

    world.facts.update(scene=scene, crate=crate, falcon=falcon, parody=parody, help_item=help_item)

    hero.memes["kindness"] = 1.0
    falcon.memes["trust"] = 0.0
    cr.meters["crack"] = 1.0
    fa.meters["restless"] = 1.0
    elder.memes["worry"] = 1.0

    world.say(scene.opener)
    world.say(f"In that {scene.place}, the hero found {crate.phrase} with a crack in one board.")
    world.say(f"Nearby, {falcon.phrase} would not settle on its perch and kept looking toward {falcon.perch}.")
    world.say(f'The child made a {parody.label} about the busy birds of the kingdom, and the rhyme was {parody.mood}, but not cruel.')

    world.para()
    hero.memes["care"] += 1
    world.say(f'The elder frowned at the crack and said, "If the crate splits, the falcon will have no safe place to rest."')
    world.say(f'The child listened, then smiled kindly and said, "Let us mend it before the bird grows uneasy."')

    world.para()
    world.say(f"The child fetched {help_item.label}. With steady hands, {help_item.method}, and the elder watched close by.")
    crate_fix = crate.label
    world.get("crate").meters["mended"] += 1
    world.get("crate").meters["crack"] = 0.0
    falcon.memes["trust"] += 1
    elder.memes["relief"] += 1
    world.say(f"The {crate_fix} was repaired, and {falcon.phrase} stepped onto it without wobbling.")
    world.say(f"The little parody song stayed in the air, but now it was a cheerful tune of thanks instead of worry.")

    world.para()
    world.say(f"{scene.ending_image}")
    world.say(f"The child bowed to the falcon, and the falcon answered by folding its wings like a velvet cloak.")

    world.facts.update(hero=hero, elder=elder, crate_ent=cr, falcon_ent=fa, parody_ent=pa, help_ent=hi)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story that includes the words "crate", "falcon", and "parody", and shows kindness turning a worry into a happy repair.',
        f"Tell a gentle castle-yard story where {f['crate'].label} is cracked, {f['falcon'].label} is unsettled, and a kind child uses a parody song before helping fix it.",
        f'Write a short fairy tale in which a playful parody is made, but kindness is what saves the day near a crate and a falcon.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    return [
        ("What was broken in the story?",
         "The crate had a crack in one board, so it was not a safe resting place at first. The broken crate was the problem the child chose to mend."),
        ("Why did the elder worry about the falcon?",
         "The falcon would not settle and kept looking for a perch, so the elder feared it might have nowhere safe to rest. A cracked crate could have made the bird feel even more uneasy."),
        ("How did the child use parody?",
         "The child made a tiny parody song to keep the mood light. It was silly, but it stayed kind and never made fun of anyone."),
        ("How did kindness change the ending?",
         "Kindness led the child to fetch tools and fix the crate instead of ignoring the worry. Because of that, the falcon trusted the people more and could perch calmly at the end."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a crate?",
         "A crate is a strong wooden box used for carrying or holding things. People can also use a crate as a resting spot for safe, sturdy items."),
        ("What is a falcon?",
         "A falcon is a bird of prey with sharp eyes and fast wings. Falcons like high perches and can look very noble and proud."),
        ("What is a parody?",
         "A parody is a playful copy of a song, story, or style. It usually adds a funny twist while still being recognizable."),
        ("What does kindness mean?",
         "Kindness means choosing to help, to be gentle, and to care about other beings. A kind act can calm worry and make a hard moment feel safe."),
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: the chosen combination does not lead to a safe, kind repair.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale story world about a crate, a falcon, a parody, and kindness.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--crate", choices=CRATES)
    ap.add_argument("--falcon", choices=FALCONS)
    ap.add_argument("--parody", choices=PARODIES)
    ap.add_argument("--help-item", dest="help_item", choices=HELPS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-type", choices=["woman", "man", "queen", "king"])
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
              if (args.scene is None or c[0] == args.scene)
              and (args.crate is None or c[1] == args.crate)
              and (args.falcon is None or c[2] == args.falcon)
              and (args.parody is None or c[3] == args.parody)
              and (args.help_item is None or c[4] == args.help_item)]
    if not combos:
        raise StoryError(explain_rejection())
    scene, crate, falcon, parody, help_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    elder_type = args.elder_type or rng.choice(["woman", "man", "queen", "king"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["Queen Elara", "King Bram", "Lady Orla", "Sir Rowan"])
    return StoryParams(scene, crate, falcon, parody, help_id, hero, hero_type, elder, elder_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], CRATES[params.crate], FALCONS[params.falcon], PARODIES[params.parody], HELPS[params.help],
                 params.hero, params.hero_type, params.elder, params.elder_type)
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


ASP_RULES = r"""
valid(S, C, F, P, H) :- scene(S), crate(C), falcon(F), parody(P), help(H),
                        repairable(C), safe_parody(P), sense(H, N), sense_min(M), N >= M.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for cid in CRATES:
        lines.append(asp.fact("crate", cid))
        lines.append(asp.fact("repairable", cid))
    for fid in FALCONS:
        lines.append(asp.fact("falcon", fid))
    for pid, p in PARODIES.items():
        lines.append(asp.fact("parody", pid))
        if p.kind_safe:
            lines.append(asp.fact("safe_parody", pid))
    for hid, h in HELPS.items():
        lines.append(asp.fact("help", hid))
        lines.append(asp.fact("sense", hid, h.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    sample = generate(resolve_params(argparse.Namespace(scene=None, crate=None, falcon=None, parody=None, help_item=None, hero=None, hero_type=None, elder=None, elder_type=None), random.Random(1)))
    if not sample.story.strip():
        print("MISMATCH: story generation failed.")
        rc = 1
    else:
        print("OK: story generation works.")
    return rc


CURATED = [
    StoryParams("castle_yard", "apple_crate", "young_falcon", "silly_song", "wood_glue", "Mira", "girl", "Queen Elara", "woman"),
    StoryParams("orchard", "grain_crate", "white_falcon", "mock_ballad", "cord_tie", "Tobin", "boy", "Sir Rowan", "man"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for row in combos:
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
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
    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
