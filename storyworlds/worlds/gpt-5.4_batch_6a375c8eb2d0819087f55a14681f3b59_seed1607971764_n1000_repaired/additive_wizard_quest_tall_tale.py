#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/additive_wizard_quest_tall_tale.py
=============================================================

A standalone story world about a little wizard on a grand, exaggerated quest.

Premise
-------
In this tiny tall-tale domain, a young wizard must carry the right magical
additive across an outsized landscape to fix one giant problem. The story is
not just a template with swapped nouns: the world models whether the additive
matches the problem, whether the travel hazard would spoil it, and whether the
gear can protect it on the way.

Run it
------
    python storyworlds/worlds/gpt-5.4/additive_wizard_quest_tall_tale.py
    python storyworlds/worlds/gpt-5.4/additive_wizard_quest_tall_tale.py --place sky_steps --problem rainmill
    python storyworlds/worlds/gpt-5.4/additive_wizard_quest_tall_tale.py --additive thunder_yeast --problem moon_lantern
    python storyworlds/worlds/gpt-5.4/additive_wizard_quest_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/additive_wizard_quest_tall_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/additive_wizard_quest_tall_tale.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "witch", "woman"}
        male = {"boy", "father", "wizard", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    path: str
    hazard: str
    boast: str
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
class Problem:
    id: str
    label: str
    phrase: str
    need: str
    symptom: str
    turn: str
    fix: str
    ending: str
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
class Additive:
    id: str
    label: str
    phrase: str
    effect: str
    look: str
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
class Gear:
    id: str
    label: str
    phrase: str
    guards: set[str]
    detail: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "hazard": place.hazard,
            "guarded": False,
            "match": False,
            "quest_started": False,
            "quest_crossed": False,
        }

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
        clone = World(self.place)
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


def _r_hazard(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("quest_crossed"):
        return out
    additive = world.get("additive")
    sig = ("hazard", world.place.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if world.facts.get("guarded"):
        additive.meters["safe"] += 1
        out.append("__safe_crossing__")
    else:
        additive.meters["spilled"] += 1
        additive.meters["usable"] = 0.0
        world.get("hero").memes["worry"] += 1
        out.append("__spill__")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    target = world.get("target")
    additive = world.get("additive")
    if target.meters["dosed"] < THRESHOLD:
        return out
    sig = ("fix", target.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if additive.meters["usable"] >= THRESHOLD and world.facts.get("match"):
        target.meters["fixed"] += 1
        target.meters["broken"] = 0.0
        world.get("hero").memes["relief"] += 1
        world.get("mentor").memes["pride"] += 1
        out.append("__fixed__")
    else:
        target.meters["broken"] += 1
        world.get("hero").memes["sadness"] += 1
        out.append("__failed_fix__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="hazard", tag="travel", apply=_r_hazard),
    Rule(name="fix", tag="resolution", apply=_r_fix),
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
        for sent in produced:
            world.say(sent)
    return produced


def combo_works(place: Place, problem: Problem, additive: Additive, gear: Gear) -> bool:
    return additive.effect == problem.need and place.hazard in gear.guards


def predict_trip(world: World) -> dict:
    sim = world.copy()
    sim.facts["quest_started"] = True
    sim.facts["quest_crossed"] = True
    propagate(sim, narrate=False)
    additive = sim.get("additive")
    return {
        "spilled": additive.meters["spilled"] >= THRESHOLD,
        "safe": additive.meters["safe"] >= THRESHOLD,
    }


def begin_tale(world: World, hero: Entity, mentor: Entity, problem: Problem) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"In the town of Thimble-on-the-Hill, {hero.id} was a little {hero.label_word} "
        f"of a wizard whose hat was said to hold more ideas than a whole library."
    )
    world.say(
        f"One morning the church bell boomed so hard it shook jam off breakfast bread, "
        f"and the news came tumbling in: {problem.symptom}"
    )
    world.say(
        f"Folks whispered that only a brave quest and the right additive could set things right."
    )
    world.say(
        f"{mentor.id}, the old {mentor.label_word}, looked over {hero.id}'s shoulder and said, "
        f'"This is no errand for a pocketful of guesses. It is a wizard quest."'
    )


def choose_additive(world: World, hero: Entity, mentor: Entity, additive: Additive, gear: Gear) -> None:
    additive_ent = world.get("additive")
    additive_ent.meters["usable"] = 1.0
    hero.memes["bravery"] += 1
    world.say(
        f"From a shelf that leaned all the way to the moon, {mentor.id} fetched {additive.phrase}, "
        f"an additive so strange that {additive.look}."
    )
    world.say(
        f"Then {mentor.pronoun()} tucked it into {gear.phrase}. {gear.detail}"
    )


def warning(world: World, hero: Entity, mentor: Entity, additive: Additive, place: Place, gear: Gear) -> None:
    pred = predict_trip(world)
    if pred["spilled"]:
        world.say(
            f'"Mind the road to {place.label}," said {mentor.id}. "Across {place.path}, '
            f"the {place.hazard} would toss {additive.label} every which way. "
            f"Without {gear.label}, you would arrive with nothing but sticky elbows and a story of loss."
        )
    else:
        world.say(
            f'"Mind the road to {place.label}," said {mentor.id}. "Across {place.path}, '
            f"the {gear.label} will keep the additive safe clear to the end of your quest."
        )
    hero.memes["trust"] += 1


def set_out(world: World, hero: Entity, place: Place) -> None:
    world.facts["quest_started"] = True
    world.say(
        f"So {hero.id} set out for {place.label}, where {place.boast}."
    )
    world.say(
        f"Past the last cottage gate, the path rose and twisted until the town below looked no bigger than a biscuit crumb."
    )


def cross_path(world: World, hero: Entity, additive: Additive, gear: Gear, place: Place) -> None:
    world.facts["quest_crossed"] = True
    propagate(world, narrate=False)
    additive_ent = world.get("additive")
    if additive_ent.meters["spilled"] >= THRESHOLD:
        world.say(problem_failure_text(place, additive))
    else:
        world.say(
            f"At {place.path}, the {place.hazard} came at {hero.id} in a great bragging rush, "
            f"but the {gear.label} held firm. Not a grain nor a glitter of the additive got away."
        )


def problem_failure_text(place: Place, additive: Additive) -> str:
    return (
        f"At {place.path}, the {place.hazard} leapt and lunged until {additive.label} flew this way and that, "
        f"and by the far side only a sad dusting remained."
    )


def arrive(world: World, hero: Entity, problem: Problem) -> None:
    world.say(
        f"When {hero.id} finally reached the trouble spot, {problem.turn}"
    )


def use_additive(world: World, hero: Entity, problem: Problem, additive: Additive) -> None:
    world.get("target").meters["dosed"] += 1
    propagate(world, narrate=False)
    target = world.get("target")
    if target.meters["fixed"] >= THRESHOLD:
        world.say(
            f"{hero.id} took a steady breath and {additive.use_text} {problem.phrase}. "
            f"{problem.fix}"
        )
    else:
        world.say(
            f"{hero.id} tried to use the additive on {problem.phrase}, but there was not enough good magic left to do the job."
        )


def return_home(world: World, hero: Entity, mentor: Entity, problem: Problem, place: Place) -> None:
    target = world.get("target")
    if target.meters["fixed"] >= THRESHOLD:
        hero.memes["joy"] += 1
        world.say(
            f"Before noon, word raced back to town faster than geese in a tailwind. {problem.ending}"
        )
        world.say(
            f"That evening {hero.id} came home with boots dusty from the quest, and {mentor.id} tipped {mentor.pronoun('possessive')} hat. "
            f'"A true wizard," {mentor.pronoun()} said, "knows that the right additive, carried the right way, can change a whole horizon."'
        )
    else:
        world.say(
            f"{hero.id} went home by the long road, and even the shadows seemed sorry. "
            f"{mentor.id} met {hero.pronoun('object')} at the gate and promised they would study harder before trying such a giant quest again."
        )


PLACES = {
    "sky_steps": Place(
        id="sky_steps",
        label="the Sky Steps",
        path="the Sky Steps",
        hazard="gust",
        boast="the stair stones were so high that birds stopped to rest on the middle ones",
        tags={"wind", "mountain"},
    ),
    "foamy_ford": Place(
        id="foamy_ford",
        label="Foamy Ford",
        path="Foamy Ford",
        hazard="splash",
        boast="the river bubbles popped like kettles and soaked clouds from below",
        tags={"water", "river"},
    ),
    "giant_stairs": Place(
        id="giant_stairs",
        label="the Giant Stairs",
        path="the Giant Stairs",
        hazard="bump",
        boast="each step was so broad a shepherd could lose three sheep on one corner of it",
        tags={"stone", "road"},
    ),
}

PROBLEMS = {
    "moon_lantern": Problem(
        id="moon_lantern",
        label="moon lantern",
        phrase="the moon lantern",
        need="brighten",
        symptom="the moon lantern above the wheat fields had gone dim, and noon looked as gray as dishwater",
        turn="the moon lantern sagged on its chain, glowing no brighter than a sleepy firefly",
        fix="At once the lantern swelled white and gold, and light poured over the fields in sheets big enough to fold shadows flat.",
        ending="Children danced in bright puddles of moon-colored light, and the farmers said they could count their chickens at midnight without squinting.",
        tags={"light", "moon"},
    ),
    "rainmill": Problem(
        id="rainmill",
        label="rain mill",
        phrase="the rain mill",
        need="slicken",
        symptom="the rain mill on the ridge had stuck fast, so clouds queued up for miles with nowhere to pour",
        turn="the rain mill stood still as a loaf pan, while clouds bumped into one another and grumbled overhead",
        fix="The old paddles loosened with one grand shiver, then spun so fast they combed the clouds and sent rain skipping out in silver ropes.",
        ending="Soon every cistern sang, every turnip leaf sparkled, and the village ducks had to learn breaststroke just to cross the lane.",
        tags={"rain", "weather"},
    ),
    "giant_loaf": Problem(
        id="giant_loaf",
        label="giant loaf",
        phrase="the giant loaf",
        need="rise",
        symptom="the giant loaf for market day had slumped flat, and a hundred hungry mouths were waiting with butter knives ready",
        turn="the giant loaf lay in its pan like a sleepy hill, broad and heavy and stubborn as wet clay",
        fix="The dough rose in one mighty whoomph until it towered over the bakery, warm and brown and smelling like a feast for seven counties.",
        ending="Slices were carried home on wagon beds, and there was enough bread left over to patch a fence and still feed the mayor twice.",
        tags={"bread", "food"},
    ),
}

ADDITIVES = {
    "starlight_syrup": Additive(
        id="starlight_syrup",
        label="starlight syrup",
        phrase="a cork-stoppered vial of starlight syrup",
        effect="brighten",
        look="it winked like a jarful of tiny stars learning to swim",
        use_text="poured three bright drops of the additive onto",
        tags={"light", "additive"},
    ),
    "butterbubble": Additive(
        id="butterbubble",
        label="butterbubble",
        phrase="a tin of butterbubble",
        effect="slicken",
        look="every bubble in it wore a rainbow hat",
        use_text="sprinkled the additive into the gears of",
        tags={"weather", "additive"},
    ),
    "thunder_yeast": Additive(
        id="thunder_yeast",
        label="thunder yeast",
        phrase="a paper twist of thunder yeast",
        effect="rise",
        look="it puffed and muttered as if each grain had swallowed a cloud",
        use_text="dusted the additive over",
        tags={"bread", "additive"},
    ),
}

GEAR = {
    "windproof_tin": Gear(
        id="windproof_tin",
        label="windproof tin",
        phrase="a windproof tin",
        guards={"gust"},
        detail="Its latch snapped shut so tightly that a storm could not whistle through the crack.",
        tags={"wind", "gear"},
    ),
    "corked_flask": Gear(
        id="corked_flask",
        label="corked flask",
        phrase="a corked flask",
        guards={"splash"},
        detail="Its stopper was waxed and wound with twine until not even a rude splash could nose inside.",
        tags={"water", "gear"},
    ),
    "padded_satchel": Gear(
        id="padded_satchel",
        label="padded satchel",
        phrase="a padded satchel",
        guards={"bump"},
        detail="It was stuffed with lambswool so thick even bouncing stones would treat it kindly.",
        tags={"road", "gear"},
    ),
}

GIRL_NAMES = ["Mira", "Tansy", "Nell", "Poppy", "Wren", "Lula"]
BOY_NAMES = ["Bram", "Otis", "Pip", "Milo", "Tobin", "Alder"]
TRAITS = ["brave", "curious", "steady", "cheerful", "eager", "small-but-stout"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for problem_id, problem in PROBLEMS.items():
            for additive_id, additive in ADDITIVES.items():
                for gear_id, gear in GEAR.items():
                    if combo_works(place, problem, additive, gear):
                        combos.append((place_id, problem_id, additive_id, gear_id))
    return sorted(combos)


@dataclass
class StoryParams:
    place: str
    problem: str
    additive: str
    gear: str
    name: str
    gender: str
    mentor_name: str
    mentor_type: str
    trait: str
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


KNOWLEDGE = {
    "additive": [
        (
            "What is an additive?",
            "An additive is something you add to something else to change it. In this story world, the wizard uses a magical additive to help fix a big problem."
        )
    ],
    "wizard": [
        (
            "What is a wizard?",
            "A wizard is a make-believe person who studies magic and uses it carefully. A good wizard does not just wave hands around; a good wizard learns what each spell or ingredient is for."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a long, important trip taken to do something brave or helpful. A quest usually has a clear goal, a hard road, and a changed ending."
        )
    ],
    "wind": [
        (
            "Why can strong wind make carrying things hard?",
            "Strong wind can blow light things away or tip open a loose container. That is why travelers pack things tightly before crossing gusty places."
        )
    ],
    "water": [
        (
            "Why do people cork a flask tightly near water?",
            "A tight cork helps keep splashes out and keeps what is inside from spilling. Water can spoil powders and wash away small amounts of something important."
        )
    ],
    "road": [
        (
            "Why does padding help on a bumpy road?",
            "Padding softens jolts and bumps. It helps fragile things arrive in one piece instead of getting shaken or crushed."
        )
    ],
    "light": [
        (
            "Why does more light help at night?",
            "Light helps people see where they are going and what is around them. A bright lamp can make nighttime feel safer and easier."
        )
    ],
    "rain": [
        (
            "Why is rain helpful to a village?",
            "Rain waters plants, fills streams and cisterns, and helps crops grow. Without enough rain, gardens and fields can dry out."
        )
    ],
    "bread": [
        (
            "What makes bread rise?",
            "Bread rises when ingredients create bubbles of gas inside the dough, making it puff up. In a tall tale, that change can be stretched into something huge and funny."
        )
    ],
}
KNOWLEDGE_ORDER = ["additive", "wizard", "quest", "wind", "water", "road", "light", "rain", "bread"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem_cfg"]
    additive = f["additive_cfg"]
    place = f["place_cfg"]
    return [
        f'Write a Tall Tale for a 3-to-5-year-old about a young wizard on a quest who must carry a magical additive to {place.label}. Include the word "additive".',
        f"Tell a child-friendly story where {hero.id}, a little wizard, crosses {place.path} to fix {problem.phrase} with {additive.label}.",
        f"Write a playful quest story with huge exaggeration, a careful mentor, and an ending that shows how the right additive changed the whole town.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    problem = f["problem_cfg"]
    additive = f["additive_cfg"]
    gear = f["gear_cfg"]
    place = f["place_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little wizard, and {mentor.id}, the older wizard who sent {hero.pronoun('object')} on the quest. They worked together to help the town."
        ),
        (
            "What problem started the quest?",
            f"The quest began because {problem.symptom}. That giant trouble was so important that the town needed help right away."
        ),
        (
            f"What additive did {hero.id} carry, and why?",
            f"{hero.id} carried {additive.label} because it was the right magical additive for {problem.phrase}. The quest only worked because the additive matched what the problem needed."
        ),
        (
            f"Why did {mentor.id} give {hero.id} the {gear.label}?",
            f"{mentor.id} knew the road crossed {place.path}, where the {place.hazard} could spoil the additive. The {gear.label} protected it so the magic would still work at the end of the journey."
        ),
    ]
    if world.get("target").meters["fixed"] >= THRESHOLD:
        qa.extend([
            (
                f"What happened when {hero.id} reached {problem.phrase}?",
                f"{hero.id} used the additive on {problem.phrase}, and it worked at once. {problem.fix}"
            ),
            (
                "How did the story end?",
                f"It ended with the whole town changed for the better. {problem.ending}"
            ),
        ])
    else:
        qa.extend([
            (
                f"Why did the quest fail?",
                f"The additive did not stay usable through the journey, so {hero.id} could not fix {problem.phrase}. The hard road mattered because the magic had to arrive safely, not just start bravely."
            ),
            (
                "How did the story end?",
                f"It ended sadly, with {hero.id} going home to learn more before trying again. The ending shows that even a wizard needs the right plan as well as courage."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"additive", "wizard", "quest"}
    tags |= set(f["place_cfg"].tags)
    tags |= set(f["problem_cfg"].tags)
    tags |= set(f["additive_cfg"].tags)
    tags |= set(f["gear_cfg"].tags)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="sky_steps",
        problem="moon_lantern",
        additive="starlight_syrup",
        gear="windproof_tin",
        name="Mira",
        gender="girl",
        mentor_name="Master Rowan",
        mentor_type="wizard",
        trait="steady",
    ),
    StoryParams(
        place="foamy_ford",
        problem="rainmill",
        additive="butterbubble",
        gear="corked_flask",
        name="Pip",
        gender="boy",
        mentor_name="Aunt Juniper",
        mentor_type="witch",
        trait="eager",
    ),
    StoryParams(
        place="giant_stairs",
        problem="giant_loaf",
        additive="thunder_yeast",
        gear="padded_satchel",
        name="Tansy",
        gender="girl",
        mentor_name="Old Brindle",
        mentor_type="wizard",
        trait="brave",
    ),
    StoryParams(
        place="sky_steps",
        problem="rainmill",
        additive="butterbubble",
        gear="windproof_tin",
        name="Otis",
        gender="boy",
        mentor_name="Master Rowan",
        mentor_type="wizard",
        trait="cheerful",
    ),
]


def explain_rejection(place: Place, problem: Problem, additive: Additive, gear: Gear) -> str:
    if additive.effect != problem.need:
        return (
            f"(No story: {additive.label} is the wrong additive for {problem.phrase}. "
            f"That problem needs magic to {problem.need}, not to {additive.effect}.)"
        )
    if place.hazard not in gear.guards:
        return (
            f"(No story: the road to {place.label} is dangerous because of {place.hazard}, "
            f"but {gear.label} will not protect the additive there. Choose gear that guards {place.hazard}.)"
        )
    return "(No story: this quest setup is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    additive = ADDITIVES[params.additive]
    gear = GEAR[params.gear]
    return "fixed" if combo_works(place, problem, additive, gear) else "failed"


ASP_RULES = r"""
matches(P,A) :- problem(P), additive(A), needs(P,N), effect(A,N).
protected(Pl,G) :- place(Pl), gear(G), hazard(Pl,H), guards(G,H).
valid(Pl,P,A,G) :- place(Pl), problem(P), additive(A), gear(G), matches(P,A), protected(Pl,G).

outcome(fixed) :- chosen_place(Pl), chosen_problem(P), chosen_additive(A), chosen_gear(G),
                  matches(P,A), protected(Pl,G).
outcome(failed) :- chosen_place(Pl), chosen_problem(P), chosen_additive(A), chosen_gear(G),
                   not outcome(fixed).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("hazard", place_id, place.hazard))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        lines.append(asp.fact("needs", problem_id, problem.need))
    for additive_id, additive in ADDITIVES.items():
        lines.append(asp.fact("additive", additive_id))
        lines.append(asp.fact("effect", additive_id, additive.effect))
    for gear_id, gear in GEAR.items():
        lines.append(asp.fact("gear", gear_id))
        for guard in sorted(gear.guards):
            lines.append(asp.fact("guards", gear_id, guard))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_additive", params.additive),
        asp.fact("chosen_gear", params.gear),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for place in PLACES:
        for problem in PROBLEMS:
            for additive in ADDITIVES:
                for gear in GEAR:
                    cases.append(
                        StoryParams(
                            place=place,
                            problem=problem,
                            additive=additive,
                            gear=gear,
                            name="Mira",
                            gender="girl",
                            mentor_name="Master Rowan",
                            mentor_type="wizard",
                            trait="steady",
                        )
                    )
    mismatches = [
        p for p in cases
        if asp_outcome(p) != outcome_of(p)
    ]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced empty story")
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a little wizard carries the right additive on a giant quest."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--additive", choices=sorted(ADDITIVES))
    ap.add_argument("--gear", choices=sorted(GEAR))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--mentor-name")
    ap.add_argument("--mentor-type", choices=["wizard", "witch", "mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible quest setups derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a generation smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.problem and args.additive and args.gear:
        place = PLACES[args.place]
        problem = PROBLEMS[args.problem]
        additive = ADDITIVES[args.additive]
        gear = GEAR[args.gear]
        if not combo_works(place, problem, additive, gear):
            raise StoryError(explain_rejection(place, problem, additive, gear))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.problem is None or combo[1] == args.problem)
        and (args.additive is None or combo[2] == args.additive)
        and (args.gear is None or combo[3] == args.gear)
    ]
    if not combos:
        if args.place and args.problem and args.additive and args.gear:
            raise StoryError(explain_rejection(
                PLACES[args.place], PROBLEMS[args.problem], ADDITIVES[args.additive], GEAR[args.gear]
            ))
        raise StoryError("(No valid combination matches the given options.)")

    place_id, problem_id, additive_id, gear_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    mentor_name = args.mentor_name or rng.choice(["Master Rowan", "Aunt Juniper", "Old Brindle", "Mistress Fern"])
    mentor_type = args.mentor_type or rng.choice(["wizard", "witch"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        problem=problem_id,
        additive=additive_id,
        gear=gear_id,
        name=name,
        gender=gender,
        mentor_name=mentor_name,
        mentor_type=mentor_type,
        trait=trait,
    )


def tell(
    place: Place,
    problem: Problem,
    additive: Additive,
    gear: Gear,
    name: str,
    gender: str,
    mentor_name: str,
    mentor_type: str,
    trait: str,
) -> World:
    world = World(place)

    hero = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        label="wizard",
        phrase="a little wizard",
        role="hero",
        traits=[trait],
        attrs={"trait": trait},
    ))
    mentor = world.add(Entity(
        id=mentor_name,
        kind="character",
        type=mentor_type,
        label=mentor_type,
        phrase=f"an old {mentor_type}",
        role="mentor",
        attrs={},
    ))
    target = world.add(Entity(
        id="target",
        kind="thing",
        type="problem",
        label=problem.label,
        phrase=problem.phrase,
        role="target",
        attrs={"need": problem.need},
    ))
    additive_ent = world.add(Entity(
        id="additive",
        kind="thing",
        type="additive",
        label=additive.label,
        phrase=additive.phrase,
        role="additive",
        attrs={"effect": additive.effect},
    ))
    gear_ent = world.add(Entity(
        id="gear",
        kind="thing",
        type="gear",
        label=gear.label,
        phrase=gear.phrase,
        role="gear",
        attrs={"guards": sorted(gear.guards)},
    ))

    target.meters["broken"] = 1.0
    additive_ent.meters["usable"] = 0.0
    additive_ent.meters["spilled"] = 0.0
    additive_ent.meters["safe"] = 0.0
    gear_ent.meters["ready"] = 1.0
    hero.memes["wonder"] = 0.0
    hero.memes["bravery"] = 0.0
    hero.memes["trust"] = 0.0
    hero.memes["relief"] = 0.0
    hero.memes["joy"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["sadness"] = 0.0
    mentor.memes["pride"] = 0.0

    world.facts.update({
        "guarded": place.hazard in gear.guards,
        "match": additive.effect == problem.need,
        "hero": hero,
        "mentor": mentor,
        "target": target,
        "place_cfg": place,
        "problem_cfg": problem,
        "additive_cfg": additive,
        "gear_cfg": gear,
    })

    begin_tale(world, hero, mentor, problem)
    world.para()
    choose_additive(world, hero, mentor, additive, gear)
    warning(world, hero, mentor, additive, place, gear)
    set_out(world, hero, place)
    world.para()
    cross_path(world, hero, additive, gear, place)
    arrive(world, hero, problem)
    use_additive(world, hero, problem, additive)
    world.para()
    return_home(world, hero, mentor, problem, place)

    world.facts["outcome"] = "fixed" if target.meters["fixed"] >= THRESHOLD else "failed"
    return world


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        problem = PROBLEMS[params.problem]
        additive = ADDITIVES[params.additive]
        gear = GEAR[params.gear]
    except KeyError as err:
        raise StoryError(f"(No story: unknown parameter value {err}.)") from None

    if not combo_works(place, problem, additive, gear):
        raise StoryError(explain_rejection(place, problem, additive, gear))

    world = tell(
        place=place,
        problem=problem,
        additive=additive,
        gear=gear,
        name=params.name,
        gender=params.gender,
        mentor_name=params.mentor_name,
        mentor_type=params.mentor_type,
        trait=params.trait,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, problem, additive, gear) combos:\n")
        for place, problem, additive, gear in combos:
            print(f"  {place:13} {problem:12} {additive:16} {gear}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.problem} via {p.place} ({p.additive}, {p.gear})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
