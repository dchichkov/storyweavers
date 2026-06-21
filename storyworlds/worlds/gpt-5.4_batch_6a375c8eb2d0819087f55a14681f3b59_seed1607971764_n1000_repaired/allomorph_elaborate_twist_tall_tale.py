#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/allomorph_elaborate_twist_tall_tale.py
=================================================================

A standalone story world for a child-sized tall tale with a twist: a boastful
young helper at a fair sees what looks like an enormous monster drifting toward
the celebration, only to discover that the "monster" is really a runaway fair
contraption in another shape.

This world rebuilds that premise as simulated state:
- a place with a fair and something worth saving
- an apparent menace with a matching hidden identity
- a sensible rescue tool that must fit the object's medium
- a tall-tale voice with an ending image that proves the hero changed

It also includes a tiny ASP twin for the reasonableness gate and the rescue
outcome model.

Run it
------
    python storyworlds/worlds/gpt-5.4/allomorph_elaborate_twist_tall_tale.py
    python storyworlds/worlds/gpt-5.4/allomorph_elaborate_twist_tall_tale.py --qa
    python storyworlds/worlds/gpt-5.4/allomorph_elaborate_twist_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/allomorph_elaborate_twist_tall_tale.py --place prairie_fair --apparition sky_serpent --reveal dragon_kite
    python storyworlds/worlds/gpt-5.4/allomorph_elaborate_twist_tall_tale.py --tool butter_sled
    python storyworlds/worlds/gpt-5.4/allomorph_elaborate_twist_tall_tale.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "mayor"}
        male = {"boy", "father", "man"}
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
class Setting:
    id: str
    place: str
    landmark: str
    fair_name: str
    danger_site: str
    prize: str
    ending_image: str
    affords: set[str] = field(default_factory=set)
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
class Apparition:
    id: str
    label: str
    bigness: str
    cry: str
    medium: str
    mimics: set[str] = field(default_factory=set)
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
class Reveal:
    id: str
    label: str
    phrase: str
    material: str
    medium: str
    drift: int
    builder: str
    truth_line: str
    mimics: set[str] = field(default_factory=set)
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
class Tool:
    id: str
    label: str
    medium: str
    sense: int
    power: int
    success_text: str
    fail_text: str
    qa_text: str
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


def _r_loose_to_risk(world: World) -> list[str]:
    obj = world.get("object")
    square = world.get("square")
    crowd = world.get("crowd")
    hero = world.get("hero")
    if obj.meters["loose"] < THRESHOLD or obj.meters["tethered"] >= THRESHOLD:
        return []
    sig = ("loose_to_risk",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    square.meters["danger"] += 1
    crowd.memes["fear"] += 1
    hero.memes["focus"] += 1
    return ["__danger__"]


def _r_tether_to_relief(world: World) -> list[str]:
    obj = world.get("object")
    square = world.get("square")
    crowd = world.get("crowd")
    hero = world.get("hero")
    if obj.meters["tethered"] < THRESHOLD or square.meters["danger"] < THRESHOLD:
        return []
    sig = ("tether_to_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    square.meters["danger"] = 0.0
    crowd.memes["relief"] += 1
    crowd.memes["fear"] = 0.0
    hero.memes["relief"] += 1
    return []


def _r_impact_to_mess(world: World) -> list[str]:
    obj = world.get("object")
    prize = world.get("prize")
    crowd = world.get("crowd")
    if obj.meters["impacted"] < THRESHOLD:
        return []
    sig = ("impact_to_mess",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    prize.meters["spoiled"] += 1
    crowd.memes["astonishment"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="loose_to_risk", tag="physical", apply=_r_loose_to_risk),
    Rule(name="tether_to_relief", tag="social", apply=_r_tether_to_relief),
    Rule(name="impact_to_mess", tag="physical", apply=_r_impact_to_mess),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                out.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in out:
            world.say(line)
    return out


SETTINGS = {
    "prairie_fair": Setting(
        id="prairie_fair",
        place="the prairie fair",
        landmark="the grain elevator",
        fair_name="Sunup Fair",
        danger_site="the pie tables",
        prize="a row of blueberry pies",
        ending_image="the whole fair eating blueberry pie under a calm pink sky",
        affords={"air"},
        tags={"fair", "prairie", "pie"},
    ),
    "canyon_roundup": Setting(
        id="canyon_roundup",
        place="the canyon roundup",
        landmark="the red stone arch",
        fair_name="Echo Roundup",
        danger_site="the ribbon hats on the fence",
        prize="a fence full of bright ribbon hats",
        ending_image="ribbon hats bobbing in the evening breeze while fiddles played",
        affords={"air"},
        tags={"fair", "canyon", "hat"},
    ),
    "river_jamboree": Setting(
        id="river_jamboree",
        place="the river jamboree",
        landmark="the long wooden dock",
        fair_name="Moonbend Jamboree",
        danger_site="the lemonade stand",
        prize="three glass pitchers of lemonade",
        ending_image="the dock glowing with lanterns and the crowd sipping lemonade",
        affords={"air", "water"},
        tags={"fair", "river", "lemonade"},
    ),
}

APPARITIONS = {
    "sky_serpent": Apparition(
        id="sky_serpent",
        label="a sky serpent",
        bigness="long as seven wagons laid nose to tail",
        cry="A sky serpent is coming!",
        medium="air",
        mimics={"dragon_kite"},
        tags={"monster", "kite"},
    ),
    "thunder_rooster": Apparition(
        id="thunder_rooster",
        label="a thunder rooster",
        bigness="big enough to peck the moon if it felt rude",
        cry="A thunder rooster is diving on the fair!",
        medium="air",
        mimics={"balloon_rooster"},
        tags={"monster", "balloon"},
    ),
    "river_whale": Apparition(
        id="river_whale",
        label="a river whale",
        bigness="broad as a barn door and twice as stubborn",
        cry="A river whale has come for the dock!",
        medium="water",
        mimics={"catfish_barge"},
        tags={"monster", "barge"},
    ),
}

REVEALS = {
    "dragon_kite": Reveal(
        id="dragon_kite",
        label="dragon kite",
        phrase="an elaborate silk dragon kite",
        material="silk and willow ribs",
        medium="air",
        drift=2,
        builder="the tailor sisters",
        truth_line="Its scales were painted cloth, and its terrible teeth were only tassels.",
        mimics={"sky_serpent"},
        tags={"kite", "cloth", "allomorph"},
    ),
    "balloon_rooster": Reveal(
        id="balloon_rooster",
        label="balloon rooster",
        phrase="an elaborate patchwork balloon rooster",
        material="patchwork cloth and warm air",
        medium="air",
        drift=3,
        builder="the balloon club",
        truth_line="Its thunder was just the burner puffing, and its claws were loops of rope.",
        mimics={"thunder_rooster"},
        tags={"balloon", "cloth", "allomorph"},
    ),
    "catfish_barge": Reveal(
        id="catfish_barge",
        label="catfish barge",
        phrase="an elaborate painted catfish barge",
        material="painted boards and empty syrup barrels",
        medium="water",
        drift=2,
        builder="the river carpenters",
        truth_line="Its whiskers were dock ropes, and its shiny scales were spoon-bright tin plates.",
        mimics={"river_whale"},
        tags={"barge", "river", "allomorph"},
    ),
}

TOOLS = {
    "lasso_pole": Tool(
        id="lasso_pole",
        label="a hickory lasso pole",
        medium="air",
        sense=3,
        power=2,
        success_text="vaulted onto a feed barrel, caught the trailing line with the hickory pole, and leaned back until the wild thing swung down in a grand windy bow",
        fail_text="jabbed with the hickory pole, but the line skipped past and the runaway shape sailed on",
        qa_text="caught the trailing line with a hickory pole and pulled the runaway shape down",
        tags={"rope", "kite"},
    ),
    "wind_anchor": Tool(
        id="wind_anchor",
        label="a wind-anchor rope",
        medium="air",
        sense=3,
        power=3,
        success_text="snatched the wind-anchor rope from the wagon hitch, looped it through the hanging ring, and hauled until the runaway shape corkscrewed down to earth",
        fail_text="flung the wind-anchor rope high, but the gusts were stronger and the runaway shape kept charging toward the fair",
        qa_text="looped a wind-anchor rope through the hanging ring and hauled the runaway shape down",
        tags={"rope", "balloon"},
    ),
    "tow_rope": Tool(
        id="tow_rope",
        label="a braided tow rope",
        medium="water",
        sense=3,
        power=3,
        success_text="leaped onto the piling, snagged the drifting craft with the braided tow rope, and drew it sideways until it bumped the dock as gently as a sleepy cow",
        fail_text="threw the braided tow rope, but it slipped off the slick prow and the drifting craft kept sliding straight for the stand",
        qa_text="snagged the drifting craft with a braided tow rope and pulled it aside",
        tags={"rope", "river"},
    ),
    "butter_sled": Tool(
        id="butter_sled",
        label="a butter sled",
        medium="water",
        sense=1,
        power=1,
        success_text="slid a butter sled over the water and somehow nudged the craft away",
        fail_text="kicked a butter sled at the water, which was a splendid sight and a poor plan",
        qa_text="tried to use a butter sled",
        tags={"silly"},
    ),
}

GIRL_NAMES = ["Mabel", "Cora", "June", "Sadie", "Elsie", "Nell"]
BOY_NAMES = ["Jeb", "Eli", "Bo", "Cal", "Finn", "Tuck"]
TRAITS = ["boastful", "cheerful", "quick", "spirited", "bold", "sunny"]


def compatible(apparition: Apparition, reveal: Reveal) -> bool:
    return reveal.id in apparition.mimics and apparition.id in reveal.mimics


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for app_id, apparition in APPARITIONS.items():
            for rev_id, reveal in REVEALS.items():
                if compatible(apparition, reveal) and reveal.medium in setting.affords:
                    combos.append((place_id, app_id, rev_id))
    return combos


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def matching_tools(reveal: Reveal) -> list[Tool]:
    return [tool for tool in sensible_tools() if tool.medium == reveal.medium]


def severity(reveal: Reveal, delay: int) -> int:
    return reveal.drift + delay


def contained(tool: Tool, reveal: Reveal, delay: int) -> bool:
    return tool.medium == reveal.medium and tool.power >= severity(reveal, delay)


def explain_combo(place_id: str, app_id: str, rev_id: str) -> str:
    setting = SETTINGS[place_id]
    apparition = APPARITIONS[app_id]
    reveal = REVEALS[rev_id]
    if not compatible(apparition, reveal):
        return (
            f"(No story: {apparition.label} would not honestly turn out to be "
            f"{reveal.phrase}. The twist must be a believable mistaken shape.)"
        )
    if reveal.medium not in setting.affords:
        return (
            f"(No story: {setting.place} does not suit a drifting {reveal.label}. "
            f"Pick a place that can host something moving through {reveal.medium}.)"
        )
    return "(No story: this combination does not fit the world.)"


def explain_tool(tool_id: str, reveal_id: str) -> str:
    tool = TOOLS[tool_id]
    reveal = REVEALS[reveal_id]
    if tool.sense < SENSE_MIN:
        better = ", ".join(sorted(t.id for t in matching_tools(reveal)))
        return (
            f"(Refusing tool '{tool_id}': it scores too low on common sense "
            f"(sense={tool.sense} < {SENSE_MIN}). Try one of: {better}.)"
        )
    return (
        f"(No story: {tool.label} works on {tool.medium}, but {reveal.phrase} "
        f"moves through {reveal.medium}. Pick a tool that fits the runaway object.)"
    )


def outcome_of(params: "StoryParams") -> str:
    reveal = REVEALS[params.reveal]
    tool = TOOLS[params.tool]
    return "saved" if contained(tool, reveal, params.delay) else "splashed"


def predict_trouble(world: World, tool: Tool, reveal: Reveal, delay: int) -> dict:
    sim = world.copy()
    sim.get("object").meters["loose"] += 1
    propagate(sim, narrate=False)
    will_save = contained(tool, reveal, delay)
    if will_save:
        sim.get("object").meters["tethered"] += 1
    else:
        sim.get("object").meters["impacted"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("square").meters["danger"],
        "spoiled": sim.get("prize").meters["spoiled"] >= THRESHOLD,
        "saved": will_save,
    }


def introduce(world: World, hero: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    hero.memes["boast"] += 1
    world.say(
        f"In {setting.place}, where the wind bragged louder than most people and "
        f"{setting.landmark} looked tall enough to scratch a cloud, {hero.id} was "
        f"already famous for stories."
    )
    world.say(
        f"Folks said {hero.pronoun()} could describe a grasshopper so grandly that "
        f"it sounded like a parade horse. On the morning of {setting.fair_name}, "
        f"{hero.pronoun()} was giving an elaborate account of how {hero.pronoun()} "
        f"once raced a tumbleweed clear across the county."
    )


def fair_setup(world: World, hero: Entity, setting: Setting) -> None:
    world.say(
        f"Tables shone, fiddles warmed up, and {setting.prize} waited beside "
        f"{setting.danger_site}. Everything looked ready for a fine, ordinary day, "
        f"which in that town usually meant trouble was just lacing its boots."
    )
    world.say(
        f'{hero.id} tipped {hero.pronoun("possessive")} hat and promised, '
        f'"If anything wild happens, I can handle it."'
    )


def sighting(world: World, hero: Entity, apparition: Apparition, reveal: Reveal) -> None:
    obj = world.get("object")
    obj.meters["loose"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a shadow slid over the fair. High above, something {apparition.bigness} "
        f"lurched and spun against the light."
    )
    world.say(
        f'One baker dropped a spoon. Another pointed upward and hollered, '
        f'"{apparition.cry}"'
    )
    world.say(
        f"From the ground, the wobbling shape truly did look like {apparition.label}, "
        f"and it was drifting straight toward {world.setting.danger_site}."
    )
    if world.get("crowd").memes["fear"] >= THRESHOLD:
        world.say("The crowd scattered so fast that even the dust seemed startled.")


def warn(world: World, hero: Entity, tool: Tool, reveal: Reveal, delay: int) -> None:
    pred = predict_trouble(world, tool, reveal, delay)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_spoil"] = pred["spoiled"]
    if pred["spoiled"]:
        world.say(
            f"{hero.id} took one look at {world.setting.prize} and knew there was no "
            f"time to stand around measuring the monster's whiskers."
        )
    else:
        world.say(
            f"{hero.id} could see the drift plain enough: if nobody moved fast, the "
            f"runaway thing would churn the fair into a fine silly panic."
        )


def declare(world: World, hero: Entity, tool: Tool) -> None:
    hero.memes["nerve"] += 1
    world.say(
        f'"Stand back," said {hero.id}. "I have {tool.label}, two good feet, and '
        f'just enough sense to borrow luck from the wind."'
    )


def rescue_success(world: World, hero: Entity, tool: Tool) -> None:
    obj = world.get("object")
    obj.meters["tethered"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So {hero.id} {tool.success_text}."
    )
    world.say(
        "The crowd stopped running. The shadow folded, dipped, and quit pretending "
        "to be fearsome."
    )


def rescue_fail(world: World, hero: Entity, tool: Tool) -> None:
    obj = world.get("object")
    obj.meters["impacted"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So {hero.id} {tool.fail_text}."
    )
    world.say(
        f"The great shape swooped low, clipped {world.setting.danger_site}, and sent "
        f"the whole place into a whirl of shouting and crumbs."
    )


def twist_reveal(world: World, hero: Entity, apparition: Apparition, reveal: Reveal) -> None:
    hero.memes["wonder"] += 1
    hero.memes["humility"] += 1
    world.say(
        f"Then came the twist. The dreadful {apparition.label} was not a monster at all, "
        f"but {reveal.phrase}, built from {reveal.material} by {reveal.builder}."
    )
    world.say(reveal.truth_line)
    world.say(
        f"Old Teacher Maple laughed into her sleeve and said, "
        f'"Why, that is just the fair mascot in another shape—an allomorph, if you '
        f'care for long words."'
    )


def lesson_saved(world: World, hero: Entity, setting: Setting, reveal: Reveal) -> None:
    hero.memes["boast"] = 0.0
    hero.memes["care"] += 1
    world.say(
        f"{hero.id} grinned, a little pink in the cheeks. "
        f'"Well," {hero.pronoun()} admitted, "I was ready for a monster, but helping '
        f'with a runaway {reveal.label} is honest work too."'
    )
    world.say(
        f"That afternoon {hero.pronoun()} helped tie the lines down properly, and by "
        f"evening the town was back to laughing, with {setting.ending_image}."
    )


def lesson_splashed(world: World, hero: Entity, setting: Setting, prize: Entity, reveal: Reveal) -> None:
    hero.memes["boast"] = 0.0
    hero.memes["care"] += 1
    world.say(
        f"{hero.id} wiped {hero.pronoun('possessive')} face, looked at the mess, and gave "
        f"a small sheepish nod. \"Next time,\" {hero.pronoun()} said, \"I'll help first "
        f"and brag afterward.\""
    )
    if prize.meters["spoiled"] >= THRESHOLD:
        world.say(
            f"Folks lost {world.setting.prize}, but not their tempers. Once they saw the "
            f"truth, they tied down the runaway {reveal.label} together and shared what "
            f"could still be saved."
        )
    world.say(
        f"By sunset the tale had already grown kinder than the mess, and the day ended "
        f"with {setting.ending_image}."
    )


def tell(
    setting: Setting,
    apparition: Apparition,
    reveal: Reveal,
    tool: Tool,
    hero_name: str = "Mabel",
    hero_gender: str = "girl",
    hero_trait: str = "boastful",
    delay: int = 0,
) -> World:
    world = World(setting=setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero", traits=[hero_trait]))
    crowd = world.add(Entity(id="crowd", kind="character", type="people", label="the crowd", role="crowd"))
    square = world.add(Entity(id="square", kind="thing", type="place", label=setting.place))
    obj = world.add(Entity(id="object", kind="thing", type="runaway", label=reveal.label, attrs={"medium": reveal.medium}))
    prize = world.add(Entity(id="prize", kind="thing", type="prize", label=setting.prize))

    hero.memes["boast"] = 2.0 if hero_trait == "boastful" else 1.0
    hero.memes["nerve"] = 1.0
    hero.memes["humility"] = 0.0
    crowd.memes["fear"] = 0.0
    square.meters["danger"] = 0.0
    obj.meters["loose"] = 0.0
    obj.meters["tethered"] = 0.0
    obj.meters["impacted"] = 0.0
    prize.meters["spoiled"] = 0.0

    world.facts.update(
        hero=hero,
        crowd=crowd,
        square=square,
        object=obj,
        prize=prize,
        setting=setting,
        apparition=apparition,
        reveal=reveal,
        tool=tool,
        delay=delay,
    )

    introduce(world, hero, setting)
    fair_setup(world, hero, setting)

    world.para()
    sighting(world, hero, apparition, reveal)
    warn(world, hero, tool, reveal, delay)
    declare(world, hero, tool)

    world.para()
    saved = contained(tool, reveal, delay)
    if saved:
        rescue_success(world, hero, tool)
    else:
        rescue_fail(world, hero, tool)

    twist_reveal(world, hero, apparition, reveal)

    world.para()
    if saved:
        lesson_saved(world, hero, setting, reveal)
    else:
        lesson_splashed(world, hero, setting, prize, reveal)

    world.facts.update(
        outcome="saved" if saved else "splashed",
        saved=saved,
        spoiled=prize.meters["spoiled"] >= THRESHOLD,
        danger=square.meters["danger"],
    )
    return world


KNOWLEDGE = {
    "allomorph": [
        (
            "What does allomorph mean in this story?",
            "Here it means the same mascot or idea showing up in a different shape. Teacher Maple uses the long word to say the scary shape and the fair object were really versions of one thing."
        )
    ],
    "elaborate": [
        (
            "What does elaborate mean?",
            "Elaborate means made with many careful details. An elaborate kite or balloon has lots of parts, colors, and decorations."
        )
    ],
    "kite": [
        (
            "What is a kite?",
            "A kite is a light object that flies in the wind while a string holds it. If the string comes loose, it can drift away."
        )
    ],
    "balloon": [
        (
            "What is a hot-air balloon?",
            "A hot-air balloon is a big cloth bag filled with warm air so it can rise. It needs ropes and careful handling to stay safe."
        )
    ],
    "barge": [
        (
            "What is a barge?",
            "A barge is a broad, flat boat used to carry things on the water. If it drifts loose, it can bump into docks or stands."
        )
    ],
    "rope": [
        (
            "Why is a rope useful for a runaway object?",
            "A rope lets you catch, pull, and guide something without standing right under it. That makes it easier to move the object to a safe place."
        )
    ],
    "fair": [
        (
            "What is a fair?",
            "A fair is a big gathering with food, games, music, and shows. Lots of people come together there to celebrate."
        )
    ],
}
KNOWLEDGE_ORDER = ["fair", "allomorph", "elaborate", "kite", "balloon", "barge", "rope"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    setting = f["setting"]
    apparition = f["apparition"]
    reveal = f["reveal"]
    outcome = f["outcome"]
    if outcome == "saved":
        return [
            f'Write a short Tall Tale for a 3-to-5-year-old set at {setting.place} that includes the words "allomorph" and "elaborate" and ends with a twist.',
            f"Tell a gentle exaggerated story where a child named {hero.label} thinks {apparition.label} is attacking {setting.fair_name}, but it turns out to be {reveal.phrase}.",
            f"Write a playful tall tale in which a runaway fair object looks like a monster at first, then the truth flips the whole story in a funny way.",
        ]
    return [
        f'Write a short Tall Tale for a 3-to-5-year-old set at {setting.place} that includes the words "allomorph" and "elaborate" and ends with a twist.',
        f"Tell a tall tale where a child named {hero.label} rushes to stop what looks like {apparition.label}, but the monster turns out to be {reveal.phrase} after a big messy crash.",
        f"Write a story with a twist where the scare is real for a moment, the rescue goes a little wrong, and everyone still learns to laugh and help together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    setting = f["setting"]
    apparition = f["apparition"]
    reveal = f["reveal"]
    tool = f["tool"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child at {setting.place} who loves telling big stories. When the fair was in trouble, {hero.pronoun()} tried to help for real."
        ),
        (
            "What did the crowd think they saw in the sky or on the water?",
            f"They thought they saw {apparition.label} coming for the fair. From far away, the runaway shape really did look frightening."
        ),
        (
            "What was the twist?",
            f"The 'monster' was really {reveal.phrase}. The big scare came from mistaking one shape for another, which is why Teacher Maple called it an allomorph."
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                f"How did {hero.label} stop the danger?",
                f"{hero.label} used {tool.label} and {tool.qa_text}. That worked because the tool matched the way the runaway object was moving."
            )
        )
        qa.append(
            (
                f"How did {hero.label} change by the end?",
                f"{hero.label} was still lively, but less interested in bragging. After the twist, {hero.pronoun()} cared more about helping than sounding grand."
            )
        )
    else:
        qa.append(
            (
                f"Did {hero.label} save the fair on the first try?",
                f"No. {hero.pronoun().capitalize()} tried with {tool.label}, but the runaway shape still hit {setting.danger_site}. The mess taught {hero.pronoun('object')} to help first and brag later."
            )
        )
        qa.append(
            (
                "How did the story end after the mess?",
                f"People were startled, but once they saw the truth they worked together. The ending proves the change because the town finishes the day together instead of staying scared."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"fair", "allomorph", "elaborate", "rope"}
    reveal = world.facts["reveal"]
    tags |= set(reveal.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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


@dataclass
class StoryParams:
    place: str
    apparition: str
    reveal: str
    tool: str
    name: str
    gender: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None
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


CURATED = [
    StoryParams(
        place="prairie_fair",
        apparition="sky_serpent",
        reveal="dragon_kite",
        tool="lasso_pole",
        name="Mabel",
        gender="girl",
        trait="boastful",
        delay=0,
    ),
    StoryParams(
        place="canyon_roundup",
        apparition="thunder_rooster",
        reveal="balloon_rooster",
        tool="wind_anchor",
        name="Jeb",
        gender="boy",
        trait="quick",
        delay=0,
    ),
    StoryParams(
        place="river_jamboree",
        apparition="river_whale",
        reveal="catfish_barge",
        tool="tow_rope",
        name="Cora",
        gender="girl",
        trait="cheerful",
        delay=0,
    ),
    StoryParams(
        place="prairie_fair",
        apparition="thunder_rooster",
        reveal="balloon_rooster",
        tool="lasso_pole",
        name="Eli",
        gender="boy",
        trait="spirited",
        delay=1,
    ),
    StoryParams(
        place="river_jamboree",
        apparition="river_whale",
        reveal="catfish_barge",
        tool="tow_rope",
        name="Sadie",
        gender="girl",
        trait="bold",
        delay=2,
    ),
]


ASP_RULES = r"""
compatible(A,R) :- mimics(A,R), mimics_back(R,A).
valid(P,A,R) :- place(P), apparition(A), reveal(R), compatible(A,R),
                medium_of(R,M), affords(P,M).

sensible(T) :- tool(T), sense(T,S), sense_min(M), S >= M.
matching_tool(T,R) :- sensible(T), tool(T), reveal(R), works_on(T,M), medium_of(R,M).

severity(D + G) :- chosen_reveal(R), drift(R,D), delay(G).
contained :- chosen_tool(T), chosen_reveal(R), matching_tool(T,R),
             power(T,P), severity(S), P >= S.
outcome(saved) :- contained.
outcome(splashed) :- not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("place", place_id))
        for medium in sorted(setting.affords):
            lines.append(asp.fact("affords", place_id, medium))
    for app_id, apparition in APPARITIONS.items():
        lines.append(asp.fact("apparition", app_id))
        for rev_id in sorted(apparition.mimics):
            lines.append(asp.fact("mimics", app_id, rev_id))
    for rev_id, reveal in REVEALS.items():
        lines.append(asp.fact("reveal", rev_id))
        lines.append(asp.fact("medium_of", rev_id, reveal.medium))
        lines.append(asp.fact("drift", rev_id, reveal.drift))
        for app_id in sorted(reveal.mimics):
            lines.append(asp.fact("mimics_back", rev_id, app_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("works_on", tool_id, tool.medium))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        lines.append(asp.fact("power", tool_id, tool.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_tools() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_reveal", params.reveal),
            asp.fact("chosen_tool", params.tool),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in list(world.entities.values()):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        bits = []
        if entity.role:
            bits.append(f"role={entity.role}")
        if entity.traits:
            bits.append(f"traits={entity.traits}")
        if entity.attrs:
            shown = {k: v for k, v in entity.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {entity.id:8} ({entity.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tall-tale fair scare with a twist. "
        "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--apparition", choices=APPARITIONS)
    ap.add_argument("--reveal", choices=REVEALS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos and sensible tools from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.apparition and args.reveal:
        if (args.place, args.apparition, args.reveal) not in valid_combos():
            raise StoryError(explain_combo(args.place, args.apparition, args.reveal))
    if args.tool and args.reveal:
        if TOOLS[args.tool].sense < SENSE_MIN or TOOLS[args.tool].medium != REVEALS[args.reveal].medium:
            raise StoryError(explain_tool(args.tool, args.reveal))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.apparition is None or combo[1] == args.apparition)
        and (args.reveal is None or combo[2] == args.reveal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, apparition, reveal_id = rng.choice(sorted(combos))
    reveal = REVEALS[reveal_id]

    if args.tool is not None:
        tool_id = args.tool
        if TOOLS[tool_id].sense < SENSE_MIN or TOOLS[tool_id].medium != reveal.medium:
            raise StoryError(explain_tool(tool_id, reveal_id))
    else:
        tool_id = rng.choice(sorted(tool.id for tool in matching_tools(reveal)))

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        place=place,
        apparition=apparition,
        reveal=reveal_id,
        tool=tool_id,
        name=name,
        gender=gender,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.apparition not in APPARITIONS:
        raise StoryError(f"(Unknown apparition: {params.apparition})")
    if params.reveal not in REVEALS:
        raise StoryError(f"(Unknown reveal: {params.reveal})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")

    setting = SETTINGS[params.place]
    apparition = APPARITIONS[params.apparition]
    reveal = REVEALS[params.reveal]
    tool = TOOLS[params.tool]

    if (params.place, params.apparition, params.reveal) not in valid_combos():
        raise StoryError(explain_combo(params.place, params.apparition, params.reveal))
    if tool.sense < SENSE_MIN or tool.medium != reveal.medium:
        raise StoryError(explain_tool(params.tool, params.reveal))

    world = tell(
        setting=setting,
        apparition=apparition,
        reveal=reveal,
        tool=tool,
        hero_name=params.name,
        hero_gender=params.gender,
        hero_trait=params.trait,
        delay=params.delay,
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

    py_combos = set(valid_combos())
    asp_combos = set(asp_valid_combos())
    if py_combos == asp_combos:
        print(f"OK: gate matches valid_combos() ({len(py_combos)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_combos - py_combos:
            print("  only in clingo:", sorted(asp_combos - py_combos))
        if py_combos - asp_combos:
            print("  only in python:", sorted(py_combos - asp_combos))

    py_tools = {tool.id for tool in sensible_tools()}
    asp_tools = set(asp_sensible_tools())
    if py_tools == asp_tools:
        print(f"OK: sensible tools match ({sorted(py_tools)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: clingo={sorted(asp_tools)} python={sorted(py_tools)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(80):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible tools: {', '.join(asp_sensible_tools())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, apparition, reveal) combos:\n")
        for place, apparition, reveal in combos:
            print(f"  {place:15} {apparition:16} {reveal}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.apparition} -> {p.reveal} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
