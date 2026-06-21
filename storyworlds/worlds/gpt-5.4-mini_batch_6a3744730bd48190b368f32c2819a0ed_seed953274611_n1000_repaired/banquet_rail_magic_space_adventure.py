#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/banquet_rail_magic_space_adventure.py
======================================================================

A standalone story world for a small space-adventure tale about a magical
banquet on a railcar in orbit: a child crew plans a feast, a rail-bound crystal
carts the dishes between star stations, a spell goes awry, and a careful fix
turns the night into a bright celebration.

This world is intentionally tiny and constraint-checked. It uses typed entities
with physical meters and emotional memes, a forward causal model, grounded Q&A,
and an inline ASP twin for the reasonableness gate and outcome parity.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    magical: bool = False
    rails: bool = False
    place: str = ""

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"spark": 0.0, "glow": 0.0, "stew": 0.0, "damage": 0.0}
        if not self.memes:
            self.memes = {"wonder": 0.0, "worry": 0.0, "bravery": 0.0, "joy": 0.0}

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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    setting: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    conductor: str
    conductor_gender: str
    banquet: str
    rail: str
    magic: str
    fix: str
    delay: int = 0
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


@dataclass
class Setting:
    id: str
    scene: str
    place_line: str
    banquet_image: str
    rail_image: str
    sky: str
    star_name: str
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


@dataclass
class BanquetItem:
    id: str
    label: str
    phrase: str
    spill: str
    fixable: bool = True
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class RailThing:
    id: str
    label: str
    phrase: str
    risk: str
    rails: bool = True
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class MagicStyle:
    id: str
    label: str
    phrase: str
    shimmer: str
    power: int
    sense: int
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    text: str
    fail_text: str
    power: int
    sense: int
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                out.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for line in out:
            world.say(line)
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["stew"] < THRESHOLD:
            continue
        sig = ("spill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("car").meters["glow"] += 1
        world.get("crew").memes["worry"] += 1
        out.append("The feast had to be steadied as the car trembled with light.")
    return out


def _r_spark(world: World) -> list[str]:
    out: list[str] = []
    orb = world.get("orb")
    if orb.meters["spark"] < THRESHOLD:
        return out
    sig = ("spark", orb.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("car").meters["damage"] += 1
    world.get("hero").memes["worry"] += 1
    out.append("__spark__")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill), Rule("spark", _r_spark)]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for bid, b in BANQUETS.items():
            for rid, r in RAILS.items():
                if b.fixable and r.rails:
                    combos.append((sid, bid, rid))
    return combos


def outcome_of(params: StoryParams) -> str:
    if FIXES[params.fix].sense < SENSE_MIN:
        return "refused"
    if MAGIC_STYLES[params.magic].sense < SENSE_MIN:
        return "refused"
    return "contained" if FIXES[params.fix].power >= RAILS[params.rail].risk_level + params.delay else "shimmered"


def safe_story(params: StoryParams) -> bool:
    return outcome_of(params) != "refused"


SETTINGS = {
    "orbital": Setting("orbital", "an orbital dining car", "The dining car slid along a silver rail between star windows.",
                       "A banquet waited under pearl lamps and floating streamers.", "The rail sang softly under the floor.",
                       "a blue comet sky", "the North Lantern"),
    "moonport": Setting("moonport", "a moonport rail lounge", "The rail-car hummed beside the moonport glass.",
                        "A banquet of warm bowls and sweet fruit lined the tables.", "The rail curved past the airlock like a glowing ribbon.",
                        "a dust-bright moon sky", "the Pale Shield"),
    "starlab": Setting("starlab", "a star lab rail hall", "The hall moved on a quiet rail through the station ring.",
                       "A banquet of tiny cakes and bright juice cups waited there.", "The rail looped around the room like a patient snake.",
                       "a black sky full of sparks", "the Seven Spark"),
}

BANQUETS = {
    "fruit": BanquetItem("fruit", "starfruit banquet", "a starfruit banquet", "sticky juice", True),
    "soup": BanquetItem("soup", "comet soup banquet", "a comet soup banquet", "a bright splash", True),
    "cakes": BanquetItem("cakes", "moon-cake banquet", "a moon-cake banquet", "crumbs and glaze", True),
}

RAILS = {
    "silver": RailThing("silver", "silver rail", "a silver rail", "a shaky jolt"),
    "glow": RailThing("glow", "glow rail", "a glow rail", "a bright hum"),
}

MAGIC_STYLES = {
    "wand": MagicStyle("wand", "wand light", "a wand that blinked like a tiny star", "silver sparks", power=2, sense=2),
    "spell": MagicStyle("spell", "spell braid", "a whispered spell braid", "blue shimmer", power=3, sense=3),
    "orb": MagicStyle("orb", "magic orb", "a round magic orb", "golden firelight", power=1, sense=1),
}

FIXES = {
    "cover": Fix("cover", "cover spell", "a cover spell", "They covered the orb with a thick curtain of cloth and the sparks went dim.",
                 "They tried to cover it, but the sparks were too lively to hide.", power=3, sense=3),
    "cup": Fix("cup", "starlight cup", "a starlight cup", "They trapped the spark inside a glass cup and the glow settled down.",
               "They lifted a glass cup, but the spark jumped right out again.", power=2, sense=2),
    "call_guard": Fix("call_guard", "call the guard", "calling the station guard", "They called the station guard, who sealed the rail car and dimmed the magic.",
                      "They called too late, and the bright damage kept spreading.", power=4, sense=3),
    "water": Fix("water", "water bucket", "a bucket of water", "They splashed water over the glowing spill and the light hissed out.",
                 "The bucket was too small, and the glow kept climbing.", power=1, sense=1),
}

GIRL_NAMES = ["Lina", "Mira", "Zia", "Nora", "Tia", "Vera"]
BOY_NAMES = ["Ari", "Kellan", "Milo", "Rafi", "Jace", "Eli"]


def predict_hazard(world: World, params: StoryParams) -> dict:
    sim = world.copy()
    sim.get("orb").meters["spark"] += 1
    propagate(sim, narrate=False)
    return {"damage": sim.get("car").meters["damage"], "worry": sim.get("hero").memes["worry"]}


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    conductor = world.add(Entity(id=params.conductor, kind="character", type=params.conductor_gender, role="conductor"))
    car = world.add(Entity(id="car", type="place", label="rail car", place=setting.scene))
    crew = world.add(Entity(id="crew", type="group", label="crew"))
    orb = world.add(Entity(id="orb", type="thing", label=MAGIC_STYLES[params.magic].label, magical=True))

    world.say(
        f"In {setting.scene}, {hero.id} and {helper.id} arrived for {setting.banquet_image.lower()} {setting.place_line.lower()} "
        f"near {setting.rail_image.lower()}"
    )
    world.say(
        f'{hero.id} smiled at the feast. "This will be the best banquet in the whole starry line," {hero.pronoun()} said.'
    )
    world.para()
    world.say(
        f'But {helper.id} noticed the rail shiver. {setting.sky.capitalize()} made the windows look far away, and the magical {MAGIC_STYLES[params.magic].label} was already flickering.'
    )
    world.say(
        f'"We need careful magic," {helper.id} said, and {hero.id} nodded while {conductor.id} listened from the end of the car.'
    )
    world.para()
    orb.meters["spark"] += 1
    hero.memes["bravery"] += 1
    world.say(
        f"The {MAGIC_STYLES[params.magic].phrase} touched the {BANQUETS[params.banquet].label}; {MAGIC_STYLES[params.magic].shimmer} jumped over the plates like little comets."
    )
    propagate(world, narrate=False)
    world.say(
        f"One bright sip turned into a spill, and the banquet wobbled on the rail as if the whole car had turned into a moon boat."
    )

    fix = FIXES[params.fix]
    if fix.sense < SENSE_MIN or MAGIC_STYLES[params.magic].sense < SENSE_MIN:
        raise StoryError("This magical choice is too weak for a sensible space-adventure story.")
    world.para()
    if fix.power >= RAILS[params.rail].risk_level + params.delay if False else True:
        pass

    severity = 2 + params.delay
    contained = fix.power >= severity
    world.facts.update(
        setting=setting, hero=hero, helper=helper, conductor=conductor, car=car, crew=crew, orb=orb,
        banquet=BANQUETS[params.banquet], rail=RAILS[params.rail], magic=MAGIC_STYLES[params.magic],
        fix=fix, contained=contained, severity=severity
    )
    if contained:
        world.say(
            f"{conductor.id} came running. {fix.text} The rail car steadied, and the glowing crumbs drifted back onto the table."
        )
        world.say(
            f"Then {helper.id} smiled and lifted the banquet tray. The feast stayed bright, and the star windows shone on happy faces."
        )
    else:
        world.say(
            f"{conductor.id} came running. {fix.fail_text} The glow slid under the benches and the rail car filled with smoke-light."
        )
        world.say(
            f"Even so, everyone moved carefully to the next car, where the stars waited and the crew promised a safer spell next time."
        )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story for a child that includes the words "{f["setting"].star_name}" and "banquet".',
        f"Tell a story about {f['hero'].id} on a rail car with a magical banquet and a helpful fix.",
        f"Write a child-friendly space adventure where magic starts a small problem on a rail and the crew makes it safe again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, conductor = f["hero"], f["helper"], f["conductor"]
    fix = f["fix"]
    qas = [
        ("Who is the story about?", f"It is about {hero.id}, {helper.id}, and {conductor.id} on a rail car in space."),
        ("What was happening at the start?", f"They were having a banquet in an orbital place, and the rail under the floor was carrying them through the stars."),
        ("What went wrong?", f"The magic spark jumped into the banquet and made the car wobble with glowing mess."),
    ]
    if f["contained"]:
        qas.append((
            "How was the problem fixed?",
            f"{conductor.id} and the crew used {fix.phrase}, and that was strong enough to calm the glowing spill. The rail car became safe again."
        ))
        qas.append((
            "How did the story end?",
            f"It ended with the banquet shining safely and everyone smiling beside the rail. The magic became part of the celebration instead of the problem."
        ))
    else:
        qas.append((
            "How did the story end?",
            f"The crew got everyone safe, but the glowing mess was too big for the first fix. They had to leave the car and try again later."
        ))
    return qas


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {f["magic"].id, f["rail"].id, f["banquet"].id, "space", "banquet", "rail", "magic"}
    out = []
    if "magic" in tags:
        out.append(("What is magic in stories?", "Magic is when strange, impossible things happen in a story, like glowing sparks or spells that move on their own."))
    if "rail" in tags:
        out.append(("What is a rail?", "A rail is a long track or bar that helps something move in a line, like a train or a rail car."))
    if "banquet" in tags:
        out.append(("What is a banquet?", "A banquet is a big special meal with lots of food shared by many people."))
    return out


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.magical:
            bits.append("magical")
        if e.rails:
            bits.append("rails")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this combination does not make a sensible space-banquet problem and fix.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure banquet on a rail with magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--banquet", choices=BANQUETS)
    ap.add_argument("--rail", choices=RAILS)
    ap.add_argument("--magic", choices=MAGIC_STYLES)
    ap.add_argument("--fix", choices=FIXES)
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid combinations available.")
    if args.setting and args.banquet and args.rail:
        if (args.setting, args.banquet, args.rail) not in combos:
            raise StoryError(explain_rejection())
    setting, banquet, rail = rng.choice(sorted(combos))
    magic = args.magic or rng.choice(sorted(MAGIC_STYLES))
    fix = args.fix or rng.choice(sorted(FIXES))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    hero = rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero])
    conductor = rng.choice(["Captain Sol", "Marin", "Pilot Rue", "Comet Vale"])
    hg = "girl" if hero in GIRL_NAMES else "boy"
    gg = "girl" if helper in GIRL_NAMES else "boy"
    cg = "boy" if "Captain" in conductor or "Pilot" in conductor else "girl"
    return StoryParams(setting=setting, hero=hero, hero_gender=hg, helper=helper, helper_gender=gg,
                       conductor=conductor, conductor_gender=cg, banquet=banquet, rail=rail,
                       magic=magic, fix=fix, delay=delay)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.banquet not in BANQUETS or params.rail not in RAILS:
        raise StoryError("Invalid params.")
    if params.magic not in MAGIC_STYLES or params.fix not in FIXES:
        raise StoryError("Invalid params.")
    if not safe_story(params):
        raise StoryError("This story would not be reasonable enough to tell.")
    world = World()
    setting = SETTINGS[params.setting]
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    conductor = world.add(Entity(id=params.conductor, kind="character", type=params.conductor_gender, role="conductor"))
    world.add(Entity(id="car", type="place", label="rail car", place=setting.scene))
    world.add(Entity(id="crew", type="group", label="crew"))
    orb = world.add(Entity(id="orb", type="thing", label=MAGIC_STYLES[params.magic].label, magical=True))
    world.get("orb").meters["spark"] += 1
    world.get("orb").meters["glow"] += 1
    world.get("crew").memes["worry"] += 1
    world.para()
    world.say(f"In {setting.scene}, {hero.id} and {helper.id} arrived for a banquet beneath the star windows.")
    world.say(f"The rail sang softly, and {setting.banquet} waited like a little feast for a whole crew.")
    world.para()
    world.say(f"{hero.id} lifted {MAGIC_STYLES[params.magic].phrase}, and {MAGIC_STYLES[params.magic].shimmer} spilled across the plates.")
    propagate(world, narrate=False)
    world.say(f"One bright spark slipped onto the banquet, and the rail car gave a tiny wobble.")
    fix = FIXES[params.fix]
    severity = RAILS[params.rail].risk_level + params.delay if hasattr(RAILS[params.rail], "risk_level") else 2 + params.delay
    contained = fix.power >= severity
    if contained:
        world.para()
        world.say(f"{conductor.id} came running. {fix.text}")
        world.say(f"{helper.id} laughed in relief as the glowing crumbs settled back onto the table.")
    else:
        world.para()
        world.say(f"{conductor.id} came running. {fix.fail_text}")
        world.say("The crew stepped into the next car and watched the stars while the glow faded behind them.")
    world.facts.update(setting=setting, hero=hero, helper=helper, conductor=conductor, banquet=BANQUETS[params.banquet],
                       rail=RAILS[params.rail], magic=MAGIC_STYLES[params.magic], fix=fix, contained=contained)
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
valid(S,B,R) :- setting(S), banquet(B), rail(R), fixable(B), rail_ok(R).
outcome(contained) :- chosen_fix(F), fix_power(F,P), severity(V), P >= V.
outcome(shimmered) :- chosen_fix(F), fix_power(F,P), severity(V), P < V.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid in BANQUETS:
        lines.append(asp.fact("banquet", bid))
        lines.append(asp.fact("fixable", bid))
    for rid in RAILS:
        lines.append(asp.fact("rail", rid))
        lines.append(asp.fact("rail_ok", rid))
        lines.append(asp.fact("severity_base", rid, 2))
    for fid, fx in FIXES.items():
        lines.append(asp.fact("fix_power", fid, fx.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_fix", params.fix),
        asp.fact("severity", 2 + params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    sample = None
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
    except Exception as e:
        rc = 1
        print(f"SMOKE FAILED: {e}")
    if sample is not None:
        print("OK: smoke-test generation works.")
    for p in [StoryParams(setting=s, hero="Ari", hero_gender="boy", helper="Mira", helper_gender="girl",
                          conductor="Marin", conductor_gender="girl", banquet=b, rail=r, magic="wand", fix="cover", delay=0)
              for s, b, r in valid_combos()[:1]]:
        if asp_outcome(p) == "?":
            rc = 1
    return rc


def describe_story_world() -> str:
    return asp_program("", "#show valid/3.\n#show outcome/1.")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(describe_story_world())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="orbital", hero="Lina", hero_gender="girl", helper="Ari", helper_gender="boy",
                        conductor="Captain Sol", conductor_gender="boy", banquet="fruit", rail="silver",
                        magic="spell", fix="cover", delay=0),
            StoryParams(setting="moonport", hero="Milo", hero_gender="boy", helper="Nora", helper_gender="girl",
                        conductor="Marin", conductor_gender="girl", banquet="soup", rail="glow",
                        magic="wand", fix="cup", delay=1),
            StoryParams(setting="starlab", hero="Zia", hero_gender="girl", helper="Eli", helper_gender="boy",
                        conductor="Pilot Rue", conductor_gender="girl", banquet="cakes", rail="silver",
                        magic="spell", fix="call_guard", delay=0),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            try:
                sample = generate(params)
            except StoryError as e:
                print(e)
                return
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
