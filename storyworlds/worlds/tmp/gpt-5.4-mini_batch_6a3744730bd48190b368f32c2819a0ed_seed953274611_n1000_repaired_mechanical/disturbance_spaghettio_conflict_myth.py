#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/disturbance_spaghettio_conflict_myth.py
=======================================================================

A small myth-flavored story world about a sacred bowl, a sudden disturbance,
and a conflict that is resolved by wise repair instead of force.

Seed words: disturbance, spaghettio
Style: Myth
Feature: Conflict

The world models a tiny village rite:
- a child or messenger brings a bowl of spaghettio to a shrine,
- a disturbance provokes conflict,
- one side reacts badly or wisely,
- a guide or elder resolves the trouble,
- the ending image proves what changed.

The prose is state-driven: meters and memes accumulate, the disturbance can
spread, and the ending depends on whether the conflict is soothed or worsens.
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
    title: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    sacred: bool = False
    messy: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "priestess"}
        male = {"boy", "father", "dad", "man", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def name(self) -> str:
        return self.label or self.id

    @property
    def label_word(self) -> str:
        return self.title or self.label or self.id
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
    image: str
    shrine: str
    sound: str
    mood: str
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
class SacredFood:
    id: str
    label: str
    phrase: str
    bowl: str
    smell: str
    can_spill: bool = True
    can_mess: bool = True
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
class Disturbance:
    id: str
    label: str
    source: str
    force: int
    words: str
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
class ConflictResponse:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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


@dataclass
class StoryParams:
    setting: str
    food: str
    disturbance: str
    response: str
    hero: str
    hero_type: str
    elder: str
    elder_type: str
    trait: str
    seed: Optional[int] = None
    delay: int = 0
    helper: str = ""
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["spilled"] < THRESHOLD:
            continue
        sig = ("spill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        shrine = world.facts.get("setting_entity")
        if shrine:
            shrine.meters["disturbed"] += 1
        for char in world.characters():
            char.memes["shock"] += 1
        out.append("__spill__")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero_entity")
    elder = world.facts.get("elder_entity")
    if not hero or not elder:
        return out
    if hero.memes["defiance"] >= THRESHOLD and elder.memes["alarm"] >= THRESHOLD:
        sig = ("conflict", hero.id, elder.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        hero.memes["conflict"] += 1
        elder.memes["conflict"] += 1
        out.append("__conflict__")
    return out


CAUSAL_RULES = [Rule("spill", "physical", _r_spill), Rule("conflict", "social", _r_conflict)]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for fid, food in FOODS.items():
            for did, dist in DISTURBANCES.items():
                if food.can_spill and dist.force >= 1:
                    combos.append((sid, fid, did))
    return combos


def sensible_responses() -> list[ConflictResponse]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def response_ok(response: ConflictResponse, disturbance: Disturbance, delay: int) -> bool:
    return response.power >= disturbance.force + delay


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': sense={r.sense} is too low for this myth-world.)"


def predict_spill(world: World, food_id: str) -> dict:
    sim = world.copy()
    _pour(sim, sim.get(food_id), narrate=False)
    return {
        "spilled": sim.get(food_id).meters["spilled"] >= THRESHOLD,
        "disturbed": sim.get("altar").meters["disturbed"] if "altar" in sim.entities else 0,
    }


def _pour(world: World, food: Entity, narrate: bool = True) -> None:
    food.meters["spilled"] += 1
    propagate(world, narrate=narrate)


def bless(world: World, hero: Entity, setting: Setting, food: SacredFood) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"In the old days, when the sun hung over {setting.place}, {hero.name} "
        f"carried {food.phrase} toward the shrine. {setting.image}"
    )
    world.say(
        f"The air was full of {setting.sound}, and the whole village felt like a "
        f"quiet hymn."
    )


def invite(world: World, hero: Entity, food: SacredFood, setting: Setting) -> None:
    world.say(
        f"{hero.name} lifted the bowl and whispered, \"May the {setting.shrine} "
        f"receive this {food.label}.\""
    )


def disturb(world: World, hero: Entity, disturbance: Disturbance) -> None:
    hero.memes["unease"] += 1
    world.say(
        f"Then there came a {disturbance.label} from {disturbance.source}. "
        f"{disturbance.words}"
    )


def warn(world: World, elder: Entity, hero: Entity, food: SacredFood,
         disturbance: Disturbance) -> None:
    elder.memes["alarm"] += 1
    world.say(
        f"{elder.name} raised {elder.pronoun('possessive')} hand. "
        f"\"Hold steady,\" {elder.pronoun()} said. "
        f"\"If you rush, the {food.label} will spill, and the shrine will taste only "
        f"trouble.\""
    )
    world.facts["predicted_spill"] = True


def defy(world: World, hero: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.name} did not like being stopped and took one quick, proud step.")


def soothe(world: World, elder: Entity, hero: Entity) -> None:
    hero.memes["calm"] += 1
    elder.memes["calm"] += 1
    world.say(
        f"{elder.name} touched {hero.pronoun('possessive')} shoulder and breathed "
        f"slowly. The anger in the air loosened like a knot."
    )


def spill(world: World, food_ent: Entity, food: SacredFood) -> None:
    _pour(world, food_ent)
    world.say(
        f"The bowl tipped. {food.label_word if hasattr(food, 'label_word') else food.label} "
        f"spilled across the stone, and {food.smell} rose like a small storm."
    )


def resolve_good(world: World, elder: Entity, hero: Entity, response: ConflictResponse,
                 food: SacredFood, setting: Setting) -> None:
    food_ent = world.get("food")
    food_ent.meters["spilled"] = 0
    world.get("altar").meters["disturbed"] = 0
    body = response.text.replace("{food}", food.label)
    world.say(f"{elder.name} came forward and {body}.")
    world.say(
        f"The shrine grew still again. Only a clean bowl and {setting.mood} light "
        f"remained."
    )
    hero.memes["relief"] += 1
    elder.memes["relief"] += 1


def resolve_bad(world: World, elder: Entity, response: ConflictResponse,
                food: SacredFood, setting: Setting) -> None:
    world.get("altar").meters["disturbed"] += 1
    body = response.fail.replace("{food}", food.label)
    world.say(f"{elder.name} came forward, but {body}.")
    world.say(
        f"The {setting.shrine} stayed upset, and the scattered {food.label} drew a "
        f"ring of worried faces."
    )


def ending(world: World, setting: Setting, hero: Entity, elder: Entity,
           food: SacredFood, response: ConflictResponse, contained: bool) -> None:
    if contained:
        world.say(
            f"By dusk, {hero.name} set a new bowl before the shrine. {setting.image} "
            f"This time the {food.label} sat safe and bright, and the village "
            f"remembered how a quiet hand ended the conflict."
        )
    else:
        world.say(
            f"By dusk, the stone was stained and the village had to start again. "
            f"Still, {hero.name} and {elder.name} stood together in the last light, "
            f"remembering that even a disturbance can teach the old law: ask for help."
        )


def tell(setting: Setting, food: SacredFood, disturbance: Disturbance,
         response: ConflictResponse, hero_name: str = "Ari", hero_type: str = "boy",
         elder_name: str = "Mara", elder_type: str = "priestess",
         trait: str = "bold", delay: int = 0, helper: str = "") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, role="elder"))
    altar = world.add(Entity(id="altar", type="altar", label=setting.shrine, sacred=True))
    bowl = world.add(Entity(id="food", type="food", label=food.label, sacred=True, messy=True))
    hero.memes["defiance"] = 0.0
    elder.memes["alarm"] = 0.0
    world.facts.update(hero_entity=hero, elder_entity=elder, setting_entity=altar,
                        food_entity=bowl, setting=setting, food=food, disturbance=disturbance,
                        response=response)

    bless(world, hero, setting, food)
    invite(world, hero, food, setting)
    world.para()
    disturb(world, hero, disturbance)
    warn(world, elder, hero, food, disturbance)
    defy(world, hero)

    contained = response_ok(response, disturbance, delay)
    world.para()
    if contained:
        soothe(world, elder, hero)
        spill(world, bowl, food)
        resolve_good(world, elder, hero, response, food, setting)
    else:
        spill(world, bowl, food)
        resolve_bad(world, elder, response, food, setting)

    world.para()
    ending(world, setting, hero, elder, food, response, contained)

    world.facts.update(outcome="contained" if contained else "broken",
                       contained=contained, delay=delay, helper=helper)
    return world


SETTINGS = {
    "temple": Setting(
        id="temple",
        place="the moon-temple",
        image="Its white steps shone like milk under the sky.",
        shrine="silver altar",
        sound="wind-bells",
        mood="silver",
        tags={"myth", "temple"},
    ),
    "harbor": Setting(
        id="harbor",
        place="the harbor shrine",
        image="The ropes and gulls made the dock feel like an ancient song.",
        shrine="salt altar",
        sound="waves and ropes",
        mood="blue",
        tags={"myth", "harbor"},
    ),
    "grove": Setting(
        id="grove",
        place="the green grove",
        image="Old roots curled around the shrine as if they were listening.",
        shrine="root altar",
        sound="leaf-song",
        mood="green",
        tags={"myth", "grove"},
    ),
}

FOODS = {
    "spaghettio": SacredFood(
        id="spaghettio",
        label="spaghettio",
        phrase="a warm bowl of spaghettio",
        bowl="the clay bowl",
        smell="tomato steam",
        can_spill=True,
        can_mess=True,
        tags={"spaghettio", "food"},
    ),
    "honey_cakes": SacredFood(
        id="honey_cakes",
        label="honey cakes",
        phrase="a plate of honey cakes",
        bowl="the woven tray",
        smell="sweet honey",
        can_spill=True,
        can_mess=True,
        tags={"food", "sweet"},
    ),
    "milk": SacredFood(
        id="milk",
        label="milk",
        phrase="a cup of milk",
        bowl="the shallow cup",
        smell="fresh milk",
        can_spill=True,
        can_mess=True,
        tags={"food", "milk"},
    ),
}

DISTURBANCES = {
    "crow": Disturbance(
        id="crow",
        label="disturbance",
        source="a black crow above the roof",
        force=1,
        words="Its wings beat once against the air, as if the sky had coughed.",
        tags={"disturbance"},
    ),
    "drum": Disturbance(
        id="drum",
        label="drum-thunder",
        source="the hill beyond the gate",
        force=2,
        words="A drum rolled from far away and made every cup tremble.",
        tags={"disturbance", "noise"},
    ),
    "wind": Disturbance(
        id="wind",
        label="wind-cry",
        source="the open sea",
        force=3,
        words="The wind cried through the pillars, sharp as an angry flute.",
        tags={"disturbance", "wind"},
    ),
}

RESPONSES = {
    "still_water": ConflictResponse(
        id="still_water",
        sense=3,
        power=4,
        text="lifted the bowl with both hands and poured a ring of still water around the spill",
        fail="poured still water too late, and the mess had already spread",
        qa_text="lifted the bowl with both hands and used still water to calm the spill",
        tags={"water", "calm"},
    ),
    "cloth": ConflictResponse(
        id="cloth",
        sense=3,
        power=3,
        text="pressed a clean cloth over the spill and kept it from spreading",
        fail="pressed a clean cloth over the spill, but the bowl had already tipped too far",
        qa_text="pressed a clean cloth over the spill and kept it from spreading",
        tags={"cloth", "calm"},
    ),
    "dustpan": ConflictResponse(
        id="dustpan",
        sense=2,
        power=2,
        text="swept the fallen food into a dustpan and set the bowl upright again",
        fail="swept at the fallen food, but the bowl was already broken open",
        qa_text="swept the fallen food into a dustpan and set the bowl upright again",
        tags={"sweep", "calm"},
    ),
    "shout": ConflictResponse(
        id="shout",
        sense=1,
        power=1,
        text="shouted at the bowl as if anger could make it climb back up",
        fail="shouted at the bowl, but shouting never mended a spill",
        qa_text="shouted at the bowl",
        tags={"noise"},
    ),
}

TRAITS = ["bold", "careful", "tender", "quick", "serious"]


def explain_setting_food(setting: Setting, food: SacredFood) -> str:
    return (
        f"(No story: the chosen food and setting do not create a fitting disturbance "
        f"for this myth. Try the spaghettio at the temple or the harbor shrine.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    food = f["food"]
    disturbance = f["disturbance"]
    if f.get("outcome") == "contained":
        return [
            f'Write a mythic story for a child that includes the words "{disturbance.label}" '
            f'and "{food.label}" and ends with peace restored at {setting.place}.',
            f"Tell a short myth about {f['hero_entity'].name} bringing {food.label} to the shrine, "
            f"a disturbance causing conflict, and a wise response that settles the trouble.",
            f"Write a gentle legend where a disturbance interrupts a sacred meal, but the ending "
            f"shows the bowl of {food.label} made safe again.",
        ]
    return [
        f'Write a mythic story for a child that includes the words "{disturbance.label}" '
        f'and "{food.label}" and ends with the shrine still troubled.',
        f"Tell a short legend about {f['hero_entity'].name} and {f['elder_entity'].name} "
        f"facing conflict over a bowl of {food.label}.",
        f"Write a simple myth where a disturbance makes a sacred offering spill and the village "
        f"must begin again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero_entity"]
    elder = f["elder_entity"]
    setting = f["setting"]
    food = f["food"]
    disturbance = f["disturbance"]
    resp = f["response"]
    contained = f.get("contained", False)
    items: list[QAItem] = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.name} and {elder.name} at {setting.place}. "
                   f"They are the ones who face the disturbance and the conflict around the offering.",
        ),
        QAItem(
            question="What was being carried to the shrine?",
            answer=f"A bowl of {food.label} was being carried to {setting.shrine}. "
                   f"It mattered because the offering was part of the village rite.",
        ),
        QAItem(
            question="What caused the trouble?",
            answer=f"A {disturbance.label} rose from {disturbance.source}. "
                   f"It broke the calm and made everyone hurry, which turned the moment into conflict.",
        ),
    ]
    if contained:
        items.append(
            QAItem(
                question="How was the conflict solved?",
                answer=f"{elder.name} used a wise response and {resp.qa_text}. "
                       f"That kept the {food.label} from spreading and brought the shrine back to stillness.",
            )
        )
        items.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended with the shrine calm again and the bowl of {food.label} made safe. "
                       f"The ending image proves the village chose patience over anger.",
            )
        )
    else:
        items.append(
            QAItem(
                question="How did the conflict end?",
                answer=f"The response was too weak, so the bowl spilled and the shrine stayed troubled. "
                       f"Everyone had to begin again, which made the lesson harder but clearer.",
            )
        )
        items.append(
            QAItem(
                question="Why was the ending sad?",
                answer=f"The disturbance led to a spill that the chosen response could not fix in time. "
                       f"The village stayed safe, but the offering was lost and the trouble remained.",
            )
        )
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["food"].tags) | set(world.facts["disturbance"].tags)
    if world.facts.get("contained"):
        tags |= {"water", "cloth", "sweep", "calm"}
    else:
        tags |= {"noise"}
    bank = {
        "spaghettio": [QAItem(
            question="What is spaghettio?",
            answer="Spaghettio is a warm pasta food in a tomato sauce. It can spill and make a sticky mess if the bowl tips over.",
        )],
        "disturbance": [QAItem(
            question="What is a disturbance?",
            answer="A disturbance is something that breaks quiet and changes how people act. It can make a calm moment become tense very quickly.",
        )],
        "water": [QAItem(
            question="What does water do in a small spill?",
            answer="Water can wash or calm a small spill, but people still need to use it carefully so the mess does not spread.",
        )],
        "cloth": [QAItem(
            question="Why would a clean cloth help with a spill?",
            answer="A clean cloth can press down on a spill and keep it from spreading. It soaks up the mess before it grows bigger.",
        )],
        "sweep": [QAItem(
            question="What does a dustpan do?",
            answer="A dustpan helps gather fallen bits so they can be carried away. It is useful when a small mess needs a neat cleanup.",
        )],
        "calm": [QAItem(
            question="Why is calm talk useful during conflict?",
            answer="Calm talk slows the moment down and helps people listen. That makes it easier to fix a problem without making it worse.",
        )],
        "noise": [QAItem(
            question="Why can loud noise make conflict worse?",
            answer="Loud noise can startle people and make them react too fast. Then the trouble grows before anyone has a chance to think.",
        )],
    }
    out: list[QAItem] = []
    for key in ["spaghettio", "disturbance", "water", "cloth", "sweep", "calm", "noise"]:
        if key in tags:
            out.extend(bank[key])
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.sacred:
            bits.append("sacred=True")
        if e.messy:
            bits.append("messy=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(food: SacredFood, disturbance: Disturbance) -> str:
    return f"(No story: {food.label} and {disturbance.label} do not create a usable mythic conflict.)"


ASP_RULES = r"""
usable(F, D) :- food(F), disturbance(D), can_spill(F), force(D, N), N >= 1.
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
contained(D, R) :- disturbance(D), response(R), power(R, P), force(D, N), P >= N.
broken(D, R) :- disturbance(D), response(R), force(D, N), power(R, P), P < N.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for fid, food in FOODS.items():
        lines.append(asp.fact("food", fid))
        if food.can_spill:
            lines.append(asp.fact("can_spill", fid))
    for did, d in DISTURBANCES.items():
        lines.append(asp.fact("disturbance", did))
        lines.append(asp.fact("force", did, d.force))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show usable/2."))
    return sorted(set(asp.atoms(model, "usable")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([asp.fact("chosen_disturbance", params.disturbance), asp.fact("chosen_response", params.response)])
    model = asp.one_model(asp_program(scenario, "#show contained/2.\n#show broken/2."))
    if asp.atoms(model, "contained"):
        return "contained"
    if asp.atoms(model, "broken"):
        return "broken"
    return "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        assert sample.story
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    if asp_outcome(smoke_params) != outcome_of(smoke_params):
        rc = 1
        print("MISMATCH in outcome model.")
    else:
        print("OK: ASP outcome matches Python outcome.")
    return rc


def outcome_of(params: StoryParams) -> str:
    if response_ok(RESPONSES[params.response], DISTURBANCES[params.disturbance], params.delay):
        return "contained"
    return "broken"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic disturbance story world with a spaghettio conflict.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--disturbance", choices=DISTURBANCES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["boy", "girl", "child", "priest", "priestess"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-type", choices=["priest", "priestess", "man", "woman"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2, 3], default=0)
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
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.food is None or c[1] == args.food)
              and (args.disturbance is None or c[2] == args.disturbance)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, food, disturbance = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero = args.hero or rng.choice(["Ari", "Milo", "Nia", "Sera", "Taro", "Lina"])
    elder = args.elder or rng.choice(["Mara", "Ilya", "Rhea", "Orin", "Kora"])
    hero_type = args.hero_type or rng.choice(["boy", "girl", "child"])
    elder_type = args.elder_type or rng.choice(["priestess", "priest", "woman", "man"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, food=food, disturbance=disturbance,
                       response=response, hero=hero, hero_type=hero_type,
                       elder=elder, elder_type=elder_type, trait=trait,
                       delay=args.delay, helper="")


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.food not in FOODS:
        raise StoryError(f"Unknown food: {params.food}")
    if params.disturbance not in DISTURBANCES:
        raise StoryError(f"Unknown disturbance: {params.disturbance}")
    if params.response not in RESPONSES:
        raise StoryError(f"Unknown response: {params.response}")
    world = tell(SETTINGS[params.setting], FOODS[params.food], DISTURBANCES[params.disturbance],
                 RESPONSES[params.response], hero_name=params.hero, hero_type=params.hero_type,
                 elder_name=params.elder, elder_type=params.elder_type, trait=params.trait,
                 delay=params.delay, helper=params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q.question, answer=q.answer) for q in story_qa(world)],
        world_qa=[QAItem(question=q.question, answer=q.answer) for q in world_knowledge_qa(world)],
        world=world,
    )


CURATED = [
    StoryParams(setting="temple", food="spaghettio", disturbance="crow", response="still_water",
                hero="Ari", hero_type="boy", elder="Mara", elder_type="priestess", trait="bold",
                delay=0, helper=""),
    StoryParams(setting="harbor", food="honey_cakes", disturbance="drum", response="cloth",
                hero="Nia", hero_type="girl", elder="Orin", elder_type="priest", trait="careful",
                delay=1, helper=""),
    StoryParams(setting="grove", food="milk", disturbance="wind", response="dustpan",
                hero="Taro", hero_type="child", elder="Kora", elder_type="woman", trait="serious",
                delay=2, helper=""),
    StoryParams(setting="temple", food="spaghettio", disturbance="wind", response="shout",
                hero="Lina", hero_type="girl", elder="Ilya", elder_type="man", trait="bold",
                delay=1, helper=""),
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
        print(asp_program("", "#show usable/2.\n#show sensible/1.\n#show contained/2.\n#show broken/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} usable food/disturbance combinations:\n")
        for f, d in combos:
            print(f"  {f:12} {d}")
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
            header = f"### {p.hero} & {p.elder}: {p.food} at {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
