#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/text_mystery_to_solve_myth.py
========================================================

A standalone story world for a tiny mythic mystery: a child notices that the
village spring has fallen silent, reads an old text on a shrine wall, follows a
sign, discovers the hidden cause, and fixes it with the right tool.

This world is intentionally narrow and constraint-checked. A sign must honestly
point to the chosen hidden cause, and the chosen tool must truly solve that
cause. The prose is driven by simulated state: the spring begins silent, the
village grows thirsty, the hero worries, the mystery is investigated, and the
water returns only after the correct repair.

Run it
------
    python storyworlds/worlds/gpt-5.4/text_mystery_to_solve_myth.py
    python storyworlds/worlds/gpt-5.4/text_mystery_to_solve_myth.py --sign faded_beam
    python storyworlds/worlds/gpt-5.4/text_mystery_to_solve_myth.py --cause thorn_vines --tool bronze_sickle
    python storyworlds/worlds/gpt-5.4/text_mystery_to_solve_myth.py --cause stone_door --tool reed_rake
    python storyworlds/worlds/gpt-5.4/text_mystery_to_solve_myth.py --all
    python storyworlds/worlds/gpt-5.4/text_mystery_to_solve_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/text_mystery_to_solve_myth.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "priestess", "queen"}
        male = {"boy", "man", "priest", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Sign:
    id: str
    omen: str
    question: str
    place: str
    clue_line: str
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
class Cause:
    id: str
    label: str
    place: str
    expected_sign: str
    needed_tool: str
    hidden_text: str
    repair_text: str
    return_image: str
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
class Tool:
    id: str
    label: str
    phrase: str
    use_text: str
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
class Blessing:
    id: str
    gift: str
    ending: str
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
class StoryParams:
    sign: str
    cause: str
    tool: str
    blessing: str
    hero: str
    gender: str
    elder_name: str
    elder_gender: str
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
        clone = World()
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


def _r_silent_spring(world: World) -> list[str]:
    spring = world.get("spring")
    village = world.get("village")
    hero = world.get("hero")
    if spring.meters["flow"] >= THRESHOLD:
        return []
    sig = ("silent_spring",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    village.meters["thirst"] += 1
    hero.memes["worry"] += 1
    return ["__silence__"]


def _r_returned_water(world: World) -> list[str]:
    spring = world.get("spring")
    village = world.get("village")
    hero = world.get("hero")
    if spring.meters["flow"] < THRESHOLD:
        return []
    sig = ("returned_water",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    village.meters["relief"] += 1
    hero.memes["hope"] += 1
    hero.memes["awe"] += 1
    return ["__return__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="silent_spring", tag="physical", apply=_r_silent_spring),
    Rule(name="returned_water", tag="physical", apply=_r_returned_water),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


SIGNS = {
    "faded_beam": Sign(
        id="faded_beam",
        omen="the dawn mirror above the spring gave no golden beam",
        question="Why had the sacred mirror stopped answering the sunrise?",
        place="the cliff shrine",
        clue_line="No gold leapt from the mirror when morning touched it.",
        tags={"mirror", "sunrise", "mystery"},
    ),
    "muddy_bowl": Sign(
        id="muddy_bowl",
        omen="the lion basin held only a muddy swirl",
        question="Why was the basin turning in circles instead of pouring clear water?",
        place="the lion basin",
        clue_line="The pool shivered brown and thick, as if something below was holding its breath.",
        tags={"basin", "mud", "mystery"},
    ),
    "trapped_echo": Sign(
        id="trapped_echo",
        omen="a humming echo trembled behind the cave gate",
        question="Why did the mountain hum like a closed mouth?",
        place="the echo cave",
        clue_line="From behind the stone gate came a low humming, but not one drop escaped.",
        tags={"cave", "echo", "mystery"},
    ),
}

CAUSES = {
    "thorn_vines": Cause(
        id="thorn_vines",
        label="black thorn vines over the mirror",
        place="the cliff shrine",
        expected_sign="faded_beam",
        needed_tool="bronze_sickle",
        hidden_text="black thorn vines had climbed over the old sun mirror and smothered its face",
        repair_text="The hooked bronze edge whispered through the vines until the mirror could drink the dawn again",
        return_image="At once the mirror flashed, and a ribbon of gold ran down the rock toward the spring",
        tags={"mirror", "vines", "sunrise"},
    ),
    "silt_plug": Cause(
        id="silt_plug",
        label="a hard plug of silt in the lion mouth",
        place="the lion basin",
        expected_sign="muddy_bowl",
        needed_tool="reed_rake",
        hidden_text="night rain had packed the lion mouth with heavy silt",
        repair_text="The reed teeth scraped and lifted the choking silt until the stone throat lay open",
        return_image="The muddy swirl broke apart, and clear water bounded from the lion mouth in silver leaps",
        tags={"basin", "mud", "rain"},
    ),
    "stone_door": Cause(
        id="stone_door",
        label="a fallen slab wedged against the cave gate",
        place="the echo cave",
        expected_sign="trapped_echo",
        needed_tool="cedar_pole",
        hidden_text="a fallen slab had wedged the cave gate so the hidden stream could not push it open",
        repair_text="The cedar pole bent, groaned, and then shoved the slab aside just enough for the gate to breathe",
        return_image="The gate sighed, and cold water rushed out singing over the stones",
        tags={"cave", "stone", "echo"},
    ),
}

TOOLS = {
    "bronze_sickle": Tool(
        id="bronze_sickle",
        label="bronze sickle",
        phrase="a curved bronze sickle from the shrine wall",
        use_text="It was made for cutting living knots away from sacred stone",
        tags={"cut", "bronze"},
    ),
    "reed_rake": Tool(
        id="reed_rake",
        label="reed rake",
        phrase="a long reed rake from the river shed",
        use_text="Its patient teeth could comb mud from narrow places",
        tags={"rake", "mud"},
    ),
    "cedar_pole": Tool(
        id="cedar_pole",
        label="cedar pole",
        phrase="a strong cedar pole kept by the gatekeepers",
        use_text="Its straight body could pry where hands alone would fail",
        tags={"lever", "wood"},
    ),
}

BLESSINGS = {
    "jar": Blessing(
        id="jar",
        gift="a blue water jar painted with tiny fish",
        ending="The keeper filled a blue water jar painted with tiny fish and set it in the hero's hands, so the sound of returning water could be carried home.",
        tags={"jar"},
    ),
    "garland": Blessing(
        id="garland",
        gift="a laurel garland cool with dew",
        ending="The elder laid a laurel garland cool with dew on the hero's head, and the leaves smelled like the first rain after summer heat.",
        tags={"garland"},
    ),
    "lamp": Blessing(
        id="lamp",
        gift="a small lamp of polished clay",
        ending="That evening the temple lit a small lamp of polished clay for the hero, and its steady flame shone beside the spring all night.",
        tags={"lamp"},
    ),
}

GIRL_NAMES = ["Iris", "Thaleia", "Nysa", "Daphne", "Leda", "Clio"]
BOY_NAMES = ["Orin", "Theron", "Lykos", "Milo", "Damon", "Phaon"]
ELDER_WOMEN = ["Mara", "Theia", "Rhea", "Ione"]
ELDER_MEN = ["Corin", "Nestor", "Helon", "Soren"]


def sign_matches(sign: Sign, cause: Cause) -> bool:
    return sign.id == cause.expected_sign


def tool_fits(tool: Tool, cause: Cause) -> bool:
    return tool.id == cause.needed_tool


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sign_id, sign in SIGNS.items():
        for cause_id, cause in CAUSES.items():
            for tool_id, tool in TOOLS.items():
                if sign_matches(sign, cause) and tool_fits(tool, cause):
                    combos.append((sign_id, cause_id, tool_id))
    return combos


def explain_rejection(sign: Sign, cause: Cause, tool: Tool) -> str:
    if not sign_matches(sign, cause):
        return (
            f"(No story: {sign.omen} points to {sign.place}, but the hidden cause "
            f"'{cause.label}' belongs at {cause.place}. The mystery must have a real clue.)"
        )
    return (
        f"(No story: {tool.label} does not truly solve '{cause.label}'. "
        f"The repair must fit the cause, not just look dramatic.)"
    )


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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def open_image(world: World, hero: Entity) -> None:
    world.say(
        f"In the age when hills were said to remember names, {hero.id} lived in a small valley "
        f"where a singing spring fed every fig root and every clay cup."
    )
    world.say(
        "One dawn, the spring made no song at all. Its pool lay still as a held breath, "
        "and even the swallows circled in puzzled silence."
    )


def thirst_rises(world: World, hero: Entity, elder: Entity) -> None:
    world.say(
        f"{hero.id} saw women at the cistern tilt their jars and hear only a hollow knock. "
        f"{hero.pronoun().capitalize()} felt worry gather in {hero.pronoun('possessive')} chest, "
        f"and {elder.id}, keeper of the shrine, looked toward the hill without speaking."
    )


def read_text(world: World, hero: Entity, elder: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"On the shrine wall, beneath a carving of a river god, old text still shone in pale blue lines. "
        f"{hero.id} traced it with one finger and read, "
        f'"When the spring falls quiet, follow the sign that does not belong to morning."'
    )
    world.say(
        f'"Then the hill is asking a question," {elder.id} said softly. '
        f'"We must answer it before the jars go empty."'
    )


def observe_sign(world: World, hero: Entity, sign: Sign) -> None:
    world.say(
        f"So {hero.id} climbed the path and found the first true clue: {sign.omen}. "
        f"{sign.clue_line}"
    )
    world.say(
        f"{hero.pronoun().capitalize()} stopped and listened to the question hidden inside the sight: "
        f"{sign.question}"
    )


def choose_tool(world: World, hero: Entity, elder: Entity, tool: Tool, cause: Cause) -> None:
    world.say(
        f"{elder.id} placed {tool.phrase} in {hero.id}'s hands. "
        f'"Take this," {elder.pronoun()} said. "{tool.use_text}."'
    )
    world.say(
        f"Together they went to {cause.place}, where the stones held the morning colder than the air below."
    )


def reveal_cause(world: World, hero: Entity, cause: Cause) -> None:
    world.get("cause").attrs["revealed"] = 1
    hero.memes["insight"] += 1
    world.say(
        f"There, the riddle opened. {hero.id} saw that {cause.hidden_text}."
    )
    world.say(
        f'The mystery was no monster at all, only a hidden trouble in the right place at the wrong hour.'
    )


def repair(world: World, hero: Entity, tool: Tool, cause: Cause) -> None:
    spring = world.get("spring")
    village = world.get("village")
    cause_ent = world.get("cause")
    cause_ent.meters["blocked"] = 0.0
    spring.meters["flow"] = 1.0
    village.meters["thirst"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["resolve"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} set to work with the {tool.label}. {cause.repair_text}."
    )
    world.say(cause.return_image + ".")


def ending(world: World, hero: Entity, elder: Entity, blessing: Blessing) -> None:
    village = world.get("village")
    village.meters["joy"] += 1
    hero.memes["joy"] += 1
    world.say(
        "Down in the valley, jars filled again. Children laughed as the channel stones darkened, "
        "and the fig leaves lifted as if a cool hand had passed over them."
    )
    world.say(blessing.ending)
    world.say(
        f"From that day on, whenever the spring sang at dawn, {hero.id} remembered that even a god-touched valley "
        f"could keep its secrets inside ordinary things until someone brave enough looked closely."
    )


def tell(
    sign: Sign,
    cause: Cause,
    tool: Tool,
    blessing: Blessing,
    hero_name: str = "Iris",
    hero_gender: str = "girl",
    elder_name: str = "Mara",
    elder_gender: str = "woman",
) -> World:
    world = World()

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        attrs={"display": hero_name},
        tags={"hero"},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=elder_gender,
        label=elder_name,
        role="elder",
        attrs={"display": elder_name},
        tags={"elder"},
    ))
    spring = world.add(Entity(
        id="spring",
        kind="thing",
        type="spring",
        label="the spring",
        role="spring",
        attrs={"place": cause.place},
        tags={"water"},
    ))
    village = world.add(Entity(
        id="village",
        kind="thing",
        type="village",
        label="the valley village",
        role="village",
        attrs={"jars": 12},
        tags={"village"},
    ))
    cause_ent = world.add(Entity(
        id="cause",
        kind="thing",
        type="obstacle",
        label=cause.label,
        role="cause",
        attrs={"revealed": 0, "place": cause.place},
        tags=set(cause.tags),
    ))
    tool_ent = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool.label,
        role="tool",
        attrs={"fits": int(tool.id == cause.needed_tool)},
        tags=set(tool.tags),
    ))

    world.facts.update(
        sign=sign,
        cause_cfg=cause,
        tool_cfg=tool,
        blessing=blessing,
        hero=hero,
        elder=elder,
        spring=spring,
        village=village,
        cause=cause_ent,
        tool=tool_ent,
        mystery_place=cause.place,
    )

    spring.meters["flow"] = 0.0
    cause_ent.meters["blocked"] = 1.0
    village.meters["thirst"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["hope"] = 0.0
    hero.memes["awe"] = 0.0
    hero.memes["curiosity"] = 0.0
    hero.memes["resolve"] = 0.0
    hero.memes["insight"] = 0.0
    hero.memes["joy"] = 0.0
    propagate(world, narrate=False)

    display_hero = hero.attrs["display"]
    display_elder = elder.attrs["display"]

    open_image(world, Entity(id=display_hero, kind="character", type=hero.type))
    thirst_rises(world, Entity(id=display_hero, kind="character", type=hero.type),
                 Entity(id=display_elder, kind="character", type=elder.type))
    world.para()
    read_text(world, Entity(id=display_hero, kind="character", type=hero.type),
              Entity(id=display_elder, kind="character", type=elder.type))
    observe_sign(world, Entity(id=display_hero, kind="character", type=hero.type), sign)
    world.para()
    choose_tool(world, Entity(id=display_hero, kind="character", type=hero.type),
                Entity(id=display_elder, kind="character", type=elder.type), tool, cause)
    reveal_cause(world, Entity(id=display_hero, kind="character", type=hero.type), cause)
    repair(world, Entity(id=display_hero, kind="character", type=hero.type), tool, cause)
    world.para()
    ending(world, Entity(id=display_hero, kind="character", type=hero.type),
           Entity(id=display_elder, kind="character", type=elder.type), blessing)

    world.facts.update(
        solved=world.get("spring").meters["flow"] >= THRESHOLD,
        revealed=world.get("cause").attrs["revealed"] == 1,
        thirsty_start="silent_spring" in {n for n, *_ in world.fired},
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].attrs["display"]
    sign = f["sign"]
    cause = f["cause_cfg"]
    tool = f["tool_cfg"]
    return [
        'Write a myth-like story for a 3-to-5-year-old that includes the word "text" and centers on a mystery to solve.',
        f"Tell a gentle myth in which {hero} reads old text at a shrine, notices that {sign.omen}, and discovers what is wrong at {cause.place}.",
        f"Write a short mystery story in a mythic style where the true cause is {cause.label} and the fix uses a {tool.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"].attrs["display"]
    elder = f["elder"].attrs["display"]
    sign = f["sign"]
    cause = f["cause_cfg"]
    tool = f["tool_cfg"]
    blessing = f["blessing"]
    qa: list[tuple[str, str]] = [
        (
            "What was the mystery in the story?",
            f"The mystery was why the village spring had stopped singing and flowing. "
            f"The whole valley depended on that water, so the silence felt important right away."
        ),
        (
            f"What did {hero} read on the shrine wall?",
            f"{hero} read old text that said to follow the sign that did not belong to morning. "
            f"That line turned the quiet spring into a riddle instead of a random problem."
        ),
        (
            f"What clue did {hero} find?",
            f"{hero} found this clue: {sign.omen}. "
            f"The clue mattered because it pointed to {sign.place}, which was the true trail into the mystery."
        ),
        (
            f"What was really wrong with the spring?",
            f"The hidden trouble was {cause.label}. "
            f"Once {hero} reached {cause.place}, the strange sign finally made sense."
        ),
        (
            f"How did {hero} solve the mystery?",
            f"{hero} used the {tool.label} and fixed the trouble at {cause.place}. "
            f"That worked because the tool matched the real cause instead of being just any object brought along."
        ),
        (
            "How did the story end?",
            f"The water returned, the village jars filled again, and {blessing.gift} became part of the ending. "
            f"The last image proves the mystery was truly solved because the valley changed from thirst back to song."
        ),
    ]
    qa.append(
        (
            f"Why did {elder} trust {hero} to help?",
            f"{elder} trusted {hero} because {hero} looked closely, read the text carefully, and followed the clue instead of guessing wildly. "
            f"In the story, wisdom comes from paying attention to signs."
        )
    )
    return qa


KNOWLEDGE = {
    "spring": [
        (
            "What is a spring?",
            "A spring is water that comes up from the ground by itself. People and plants can use it when it flows clean and fresh."
        )
    ],
    "shrine": [
        (
            "What is a shrine?",
            "A shrine is a special place where people leave prayers, gifts, or memories for something holy. In stories, a shrine often keeps old signs or teachings."
        )
    ],
    "mystery": [
        (
            "What does it mean to solve a mystery?",
            "To solve a mystery means to notice clues and figure out the real reason something happened. You do not just guess; you look for what fits."
        )
    ],
    "text": [
        (
            "What is text?",
            "Text is writing made of words that someone can read. A text can carry a message even after the speaker is gone."
        )
    ],
    "mirror": [
        (
            "Why would a mirror matter in an old myth?",
            "In myths, a mirror can catch light and send it somewhere important. If it is covered, the light cannot do its work."
        )
    ],
    "mud": [
        (
            "Why can mud block water?",
            "Mud and silt can pack into a narrow opening and stop water from moving freely. When the blockage is cleared, the water can flow again."
        )
    ],
    "lever": [
        (
            "How does a pole help move a heavy stone?",
            "A long pole can act like a lever. It lets a person push with more force than bare hands alone."
        )
    ],
}

KNOWLEDGE_ORDER = ["mystery", "text", "spring", "shrine", "mirror", "mud", "lever"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"mystery", "text", "spring", "shrine"}
    sign = world.facts["sign"]
    cause = world.facts["cause_cfg"]
    tool = world.facts["tool_cfg"]
    blessing = world.facts["blessing"]
    tags |= set(sign.tags) | set(cause.tags) | set(tool.tags) | set(blessing.tags)
    mapped = set(tags)
    if "sunrise" in mapped or "mirror" in mapped or "vines" in mapped:
        mapped.add("mirror")
    if "mud" in mapped or "rain" in mapped or "basin" in mapped:
        mapped.add("mud")
    if "lever" in mapped or "wood" in mapped or "stone" in mapped or "cave" in mapped:
        mapped.add("lever")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in mapped and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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


CURATED = [
    StoryParams(
        sign="faded_beam",
        cause="thorn_vines",
        tool="bronze_sickle",
        blessing="jar",
        hero="Iris",
        gender="girl",
        elder_name="Mara",
        elder_gender="woman",
    ),
    StoryParams(
        sign="muddy_bowl",
        cause="silt_plug",
        tool="reed_rake",
        blessing="garland",
        hero="Orin",
        gender="boy",
        elder_name="Nestor",
        elder_gender="man",
    ),
    StoryParams(
        sign="trapped_echo",
        cause="stone_door",
        tool="cedar_pole",
        blessing="lamp",
        hero="Daphne",
        gender="girl",
        elder_name="Corin",
        elder_gender="man",
    ),
]


ASP_RULES = r"""
matches_sign(C,S) :- cause(C), sign(S), expected_sign(C,S).
fits_tool(C,T)    :- cause(C), tool(T), needed_tool(C,T).
valid(S,C,T)      :- sign(S), cause(C), tool(T), matches_sign(C,S), fits_tool(C,T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SIGNS:
        lines.append(asp.fact("sign", sid))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("expected_sign", cid, cause.expected_sign))
        lines.append(asp.fact("needed_tool", cid, cause.needed_tool))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a mythic mystery about a silent spring. "
        "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--blessing", choices=BLESSINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero")
    ap.add_argument("--elder-name")
    ap.add_argument("--elder-gender", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.sign and args.cause and args.tool:
        sign = SIGNS[args.sign]
        cause = CAUSES[args.cause]
        tool = TOOLS[args.tool]
        if not (sign_matches(sign, cause) and tool_fits(tool, cause)):
            raise StoryError(explain_rejection(sign, cause, tool))
    elif args.sign and args.cause:
        sign = SIGNS[args.sign]
        cause = CAUSES[args.cause]
        if not sign_matches(sign, cause):
            tool = TOOLS[args.tool] if args.tool else TOOLS[next(iter(TOOLS))]
            raise StoryError(explain_rejection(sign, cause, tool))
    elif args.cause and args.tool:
        cause = CAUSES[args.cause]
        tool = TOOLS[args.tool]
        if not tool_fits(tool, cause):
            sign = SIGNS[args.sign] if args.sign else SIGNS[cause.expected_sign]
            raise StoryError(explain_rejection(sign, cause, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.sign is None or combo[0] == args.sign)
        and (args.cause is None or combo[1] == args.cause)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    sign_id, cause_id, tool_id = rng.choice(sorted(combos))
    blessing_id = args.blessing or rng.choice(sorted(BLESSINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_gender = args.elder_gender or rng.choice(["woman", "man"])
    elder_name = args.elder_name or rng.choice(ELDER_WOMEN if elder_gender == "woman" else ELDER_MEN)
    return StoryParams(
        sign=sign_id,
        cause=cause_id,
        tool=tool_id,
        blessing=blessing_id,
        hero=hero,
        gender=gender,
        elder_name=elder_name,
        elder_gender=elder_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.sign not in SIGNS:
        raise StoryError(f"(Unknown sign: {params.sign})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.blessing not in BLESSINGS:
        raise StoryError(f"(Unknown blessing: {params.blessing})")

    sign = SIGNS[params.sign]
    cause = CAUSES[params.cause]
    tool = TOOLS[params.tool]
    if not (sign_matches(sign, cause) and tool_fits(tool, cause)):
        raise StoryError(explain_rejection(sign, cause, tool))

    world = tell(
        sign=sign,
        cause=cause,
        tool=tool,
        blessing=BLESSINGS[params.blessing],
        hero_name=params.hero,
        hero_gender=params.gender,
        elder_name=params.elder_name,
        elder_gender=params.elder_gender,
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


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        params.seed = 123
        sample = generate(params)
        if not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("missing prompts or QA")
        print("OK: default random resolve/generate path works.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT PATH FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (sign, cause, tool) combos:\n")
        for sign, cause, tool in combos:
            print(f"  {sign:13} {cause:13} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.sign} -> {p.cause} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
