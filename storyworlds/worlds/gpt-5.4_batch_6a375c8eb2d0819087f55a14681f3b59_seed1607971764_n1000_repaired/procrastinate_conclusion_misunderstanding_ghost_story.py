#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/procrastinate_conclusion_misunderstanding_ghost_story.py
===================================================================================

A standalone story world for a gentle ghost-story domain built around one
specific misunderstanding: a child hears or sees something in an old-feeling
place, jumps to a spooky conclusion, procrastinates asking for help, and later
learns the simple truth.

The world model tracks:
- physical signs in a place (knocking, footsteps, white fluttering shapes,
  scratching),
- emotional state in characters (fear, hesitation, relief, courage),
- a misunderstanding that grows from those signs,
- and a reveal beat that clears the mistaken "ghost" idea.

Every generated story includes the words "procrastinate" and "conclusion".

Run it
------
    python storyworlds/worlds/gpt-5.4/procrastinate_conclusion_misunderstanding_ghost_story.py
    python storyworlds/worlds/gpt-5.4/procrastinate_conclusion_misunderstanding_ghost_story.py --setting attic --source cat_roof --rumor roof_ghost
    python storyworlds/worlds/gpt-5.4/procrastinate_conclusion_misunderstanding_ghost_story.py --setting shed --source shutter
    python storyworlds/worlds/gpt-5.4/procrastinate_conclusion_misunderstanding_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/procrastinate_conclusion_misunderstanding_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/procrastinate_conclusion_misunderstanding_ghost_story.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "grandmother", "woman"}
        male = {"boy", "father", "uncle", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        table = {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }
        return table.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    errand: str
    detail: str
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
class Source:
    id: str
    cue: str
    cue_line: str
    reveal_line: str
    nature: str
    places: set[str] = field(default_factory=set)
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
class Rumor:
    id: str
    title: str
    cue_needed: str
    imagine_line: str
    lesson_line: str
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
class World:
    setting: Setting

    def __post_init__(self) -> None:
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
        clone.facts = dict(self.facts)
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


def _r_source_signal(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    hero = world.get("hero")
    room = world.get("room")
    cue = world.facts["cue"]
    if source.meters["active"] < THRESHOLD:
        return out
    sig = ("signal", cue)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters[cue] += 1
    hero.memes["fear"] += 1
    out.append("__signal__")
    return out


def _r_misunderstand(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    room = world.get("room")
    rumor = world.facts["rumor"]
    cue = world.facts["cue"]
    if room.meters[cue] < THRESHOLD or hero.memes["fear"] < THRESHOLD:
        return out
    sig = ("misunderstand", rumor.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["misunderstanding"] += 1
    out.append("__misunderstanding__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    hero = world.get("hero")
    source = world.get("source")
    if helper.meters["investigating"] < THRESHOLD or source.meters["active"] < THRESHOLD:
        return out
    sig = ("reveal", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    source.meters["revealed"] += 1
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["courage"] += 1
    out.append("__reveal__")
    return out


CAUSAL_RULES = [
    Rule(name="source_signal", tag="physical", apply=_r_source_signal),
    Rule(name="misunderstand", tag="emotional", apply=_r_misunderstand),
    Rule(name="reveal", tag="social", apply=_r_reveal),
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


def valid_combo(setting_id: str, source_id: str, rumor_id: str) -> bool:
    if setting_id not in SETTINGS or source_id not in SOURCES or rumor_id not in RUMORS:
        return False
    setting = SETTINGS[setting_id]
    source = SOURCES[source_id]
    rumor = RUMORS[rumor_id]
    return source_id in setting.affords and source.cue == rumor.cue_needed and setting_id in source.places


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for source_id in SOURCES:
            for rumor_id in RUMORS:
                if valid_combo(setting_id, source_id, rumor_id):
                    out.append((setting_id, source_id, rumor_id))
    return out


def explain_rejection(setting_id: str, source_id: str, rumor_id: str) -> str:
    if setting_id not in SETTINGS:
        return f"(No story: unknown setting '{setting_id}'.)"
    if source_id not in SOURCES:
        return f"(No story: unknown source '{source_id}'.)"
    if rumor_id not in RUMORS:
        return f"(No story: unknown rumor '{rumor_id}'.)"
    setting = SETTINGS[setting_id]
    source = SOURCES[source_id]
    rumor = RUMORS[rumor_id]
    if source_id not in setting.affords or setting_id not in source.places:
        return (
            f"(No story: {source.nature} does not fit {setting.place}. "
            f"Pick a source that the chosen place can honestly contain.)"
        )
    return (
        f"(No story: {source.nature} makes a {source.cue} cue, but {rumor.title} "
        f"needs a {rumor.cue_needed} cue. The misunderstanding must match what "
        f"the child actually hears or sees.)"
    )


def outcome_of(delay: int) -> str:
    return "night_reveal" if delay == 0 else "dawn_reveal"


def predict_fear(world: World) -> dict:
    sim = world.copy()
    sim.get("source").meters["active"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": sim.get("hero").memes["fear"],
        "misunderstanding": sim.get("hero").memes["misunderstanding"],
    }


def introduce(world: World, hero: Entity, helper: Entity) -> None:
    setting = world.setting
    world.say(
        f"One dusky evening, {hero.id} followed {hero.pronoun('possessive')} "
        f"{helper.label_word} toward {setting.place}. {setting.detail}"
    )
    world.say(
        f"{hero.id} had been asked to {setting.errand}, but the old place felt "
        f"so {setting.mood} that {hero.pronoun()} wanted to procrastinate just a little longer."
    )


def rumor_setup(world: World, hero: Entity, rumor: Rumor) -> None:
    hero.memes["unease"] += 1
    world.say(
        f"Earlier that week, {hero.id} had heard a silly house tale about {rumor.title}. "
        f"{rumor.lesson_line}"
    )


def first_sign(world: World, hero: Entity, source_cfg: Source, rumor: Rumor) -> None:
    source = world.get("source")
    source.meters["active"] += 1
    pred = predict_fear(world)
    world.facts["predicted_fear"] = pred["fear"]
    world.facts["predicted_misunderstanding"] = pred["misunderstanding"]
    propagate(world, narrate=False)
    world.say(source_cfg.cue_line)
    world.say(
        f"{hero.id}'s heart gave a jump, and {hero.pronoun()} rushed to a ghostly conclusion. "
        f"{rumor.imagine_line}"
    )


def hesitate(world: World, hero: Entity, helper: Entity, delay: int) -> None:
    hero.memes["hesitation"] += float(delay + 1)
    if delay == 0:
        world.say(
            f"For one breath {hero.id} froze, then decided not to procrastinate any longer."
        )
        return
    hero.memes["sleepiness"] += float(delay)
    if delay == 1:
        world.say(
            f"But instead of speaking at once, {hero.id} kept quiet and tried to procrastinate. "
            f"{hero.pronoun().capitalize()} pulled the blanket up to {hero.pronoun('possessive')} chin and listened to the sound again."
        )
    else:
        world.say(
            f"Still, {hero.id} tried to procrastinate and said nothing. The room felt longer, "
            f"the corners darker, and every small sound seemed to answer the first one."
        )
    world.say(
        f"The more {hero.pronoun()} waited, the less certain the conclusion felt, and the more frightening it became."
    )


def ask_for_help(world: World, hero: Entity, helper: Entity, delay: int, rumor: Rumor) -> None:
    helper_name = helper.label_word.capitalize()
    if delay == 0:
        world.say(f'"{helper_name}," {hero.id} whispered, "I think {rumor.title} is here."')
    elif delay == 1:
        world.say(
            f"At last {hero.id} padded to {helper.pronoun('possessive')} door and whispered, "
            f'"{helper_name}, I was scared to tell you, but I think {rumor.title} is here."'
        )
    else:
        world.say(
            f"When the sky finally began to pale, {hero.id} hurried to {helper.pronoun('possessive')} room and burst out, "
            f'"{helper_name}, I should not have tried to procrastinate. I thought {rumor.title} was in {world.setting.place}."'
        )


def investigate(world: World, hero: Entity, helper: Entity, source_cfg: Source, delay: int) -> None:
    helper.meters["investigating"] += 1
    propagate(world, narrate=False)
    if delay == 0:
        world.say(
            f"{helper.label_word.capitalize()} took a warm yellow lamp, held out a hand, and walked with {hero.id} to {world.setting.place}."
        )
    else:
        world.say(
            f"{helper.label_word.capitalize()} took a warm yellow lamp, wrapped a shawl close, and went with {hero.id} to {world.setting.place}."
        )
    world.say(source_cfg.reveal_line)


def resolve(world: World, hero: Entity, helper: Entity, source_cfg: Source, rumor: Rumor, delay: int) -> None:
    if delay == 0:
        world.say(
            f'"There is your ghost," {helper.label_word} said gently. '
            f'"It is only {source_cfg.nature}."'
        )
        world.say(
            f"{hero.id} let out a shaky laugh. The spooky conclusion melted away the moment the truth had a shape."
        )
    else:
        world.say(
            f'"There is the whole mystery," {helper.label_word} said softly. '
            f'"It is only {source_cfg.nature}."'
        )
        world.say(
            f"{hero.id} blinked, then laughed into {helper.pronoun('possessive')} sleeve. "
            f"The misunderstanding had grown because {hero.pronoun()} waited too long to ask."
        )
    world.say(
        f"Together they stood still and listened once more, and now the sound or flutter felt ordinary instead of haunted."
    )


def ending(world: World, hero: Entity, helper: Entity, delay: int) -> None:
    hero.memes["bravery"] += 1
    hero.memes["calm"] += 1
    if delay == 0:
        world.say(
            f"Then {hero.id} finally {world.setting.errand}, carrying the lamp with steadier hands."
        )
        world.say(
            f"Before bed, {hero.pronoun()} peeked back toward {world.setting.place} and gave a tiny nod. "
            f"The house still creaked, but it no longer sounded like a ghost."
        )
    else:
        world.say(
            f"After that, {hero.id} finally {world.setting.errand}, even though {hero.pronoun()} was a little sleepy."
        )
        world.say(
            f"From then on, whenever an old house made a queer sound, {hero.id} remembered not to procrastinate over fear. "
            f"Asking early made the night feel smaller."
        )


def tell(
    setting: Setting,
    source_cfg: Source,
    rumor: Rumor,
    *,
    hero_name: str = "Mina",
    hero_gender: str = "girl",
    helper_type: str = "grandmother",
    helper_name: str = "Grandma",
    delay: int = 0,
) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_type,
            role="helper",
            label="the helper",
        )
    )
    room = world.add(Entity(id="room", type="place", label=setting.place))
    source = world.add(Entity(id="source", type="source", label=source_cfg.nature, role="source"))

    world.facts.update(
        hero=hero,
        helper=helper,
        setting=setting,
        source_cfg=source_cfg,
        source=source,
        rumor=rumor,
        cue=source_cfg.cue,
        delay=delay,
        outcome=outcome_of(delay),
        understood=False,
    )

    introduce(world, hero, helper)
    rumor_setup(world, hero, rumor)

    world.para()
    first_sign(world, hero, source_cfg, rumor)
    hesitate(world, hero, helper, delay)
    ask_for_help(world, hero, helper, delay, rumor)

    world.para()
    investigate(world, hero, helper, source_cfg, delay)
    resolve(world, hero, helper, source_cfg, rumor, delay)

    world.para()
    ending(world, hero, helper, delay)

    world.facts["understood"] = source.meters["revealed"] >= THRESHOLD
    world.facts["fear_happened"] = hero.memes["relief"] >= THRESHOLD or hero.memes["hesitation"] >= THRESHOLD
    return world


SETTINGS = {
    "attic": Setting(
        id="attic",
        place="the attic",
        mood="still and full of corners",
        errand="bring down the quilt basket",
        detail="The rafters made dark triangles above the trunks, and one round window watched the yard like a quiet eye.",
        affords={"cat_roof", "branch_window", "sheet_window"},
        tags={"attic"},
    ),
    "hallway": Setting(
        id="hallway",
        place="the upstairs hallway",
        mood="long and whispery",
        errand="put a library book back on the table by the stairs",
        detail="The runner rug hushed footsteps, and the moon laid pale bars across the floorboards.",
        affords={"cat_roof", "shutter", "branch_window"},
        tags={"hallway"},
    ),
    "shed": Setting(
        id="shed",
        place="the garden shed",
        mood="small and creaky",
        errand="fetch the basket of twine",
        detail="Garden tools leaned against the wall, and the thin door let in strips of silver light.",
        affords={"sheet_window", "branch_window"},
        tags={"shed"},
    ),
}

SOURCES = {
    "cat_roof": Source(
        id="cat_roof",
        cue="footsteps",
        cue_line="Above the ceiling came a slow patter of steps, light and careful, as if someone were crossing the roof one toe at a time.",
        reveal_line="The lamp beam lifted to the window, and there on the roof edge sat the neighbor's striped cat, placing each paw with great importance.",
        nature="the neighbor's cat walking across the roof",
        places={"attic", "hallway"},
        tags={"cat", "roof"},
    ),
    "shutter": Source(
        id="shutter",
        cue="knocking",
        cue_line="From the far window came a hollow knock... knock... knock, with a pause between each tap that felt almost like waiting.",
        reveal_line="The lamp shone across the glass and found a loose shutter outside, rocking in the wind and tapping the wall over and over.",
        nature="a loose shutter tapping in the wind",
        places={"hallway"},
        tags={"shutter", "wind"},
    ),
    "sheet_window": Source(
        id="sheet_window",
        cue="white_shape",
        cue_line="Past the pane, something pale lifted and bowed and lifted again, white as milk in the dark yard.",
        reveal_line="The lamp reached through the glass and showed a bed sheet on the clothesline, puffing and sinking whenever the wind found it.",
        nature="a bed sheet blowing on the clothesline",
        places={"attic", "shed"},
        tags={"sheet", "wind"},
    ),
    "branch_window": Source(
        id="branch_window",
        cue="scratching",
        cue_line="A dry scratch traced along the window, then came again with a soft tick at the end, like a fingernail dragging over wood.",
        reveal_line="Outside the window, an apple-tree branch rubbed the frame each time the wind bent it low.",
        nature="an apple-tree branch brushing the window",
        places={"attic", "hallway", "shed"},
        tags={"branch", "tree", "wind"},
    ),
}

RUMORS = {
    "roof_ghost": Rumor(
        id="roof_ghost",
        title="the roof ghost",
        cue_needed="footsteps",
        imagine_line="In an instant, the child-sized tale in {hero}'s head grew boots and a shadow and began pacing overhead.".replace("{hero}", "the child"),
        lesson_line="It was only the sort of tale children pass around when a place already feels old.",
        tags={"misunderstanding", "ghost"},
    ),
    "knocking_ghost": Rumor(
        id="knocking_ghost",
        title="the knocking ghost",
        cue_needed="knocking",
        imagine_line="It sounded exactly like the ghost in the rumor that was said to tap before it came closer.",
        lesson_line="Everyone said it in a playful voice, but night can make playful things feel real.",
        tags={"misunderstanding", "ghost"},
    ),
    "white_lady": Rumor(
        id="white_lady",
        title="the white lady",
        cue_needed="white_shape",
        imagine_line="The pale flutter looked so much like a floating dress that {hero} forgot to blink.".replace("{hero}", "the child"),
        lesson_line="No one had truly seen such a thing, but a fluttering shape is enough to feed a spooky story.",
        tags={"misunderstanding", "ghost"},
    ),
    "window_whisperer": Rumor(
        id="window_whisperer",
        title="the window whisperer",
        cue_needed="scratching",
        imagine_line="To frightened ears, the dragging sound felt like a secret finger asking to be let in.",
        lesson_line="It was the kind of rumor that starts from one strange noise and grows each time it is retold.",
        tags={"misunderstanding", "ghost"},
    ),
}

HELPERS = {
    "mother": "Mother",
    "father": "Father",
    "grandmother": "Grandma",
    "grandfather": "Grandpa",
    "aunt": "Aunt Bea",
    "uncle": "Uncle Rob",
}

GIRL_NAMES = ["Mina", "Nora", "Lucy", "Ivy", "Ella", "Ruth", "Maya", "Clara"]
BOY_NAMES = ["Owen", "Theo", "Eli", "Sam", "Noah", "Finn", "Leo", "Jude"]


@dataclass
class StoryParams:
    setting: str
    source: str
    rumor: str
    hero_name: str
    hero_gender: str
    helper_type: str
    helper_name: str
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


KNOWLEDGE = {
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks something means one thing, but it really means another. It can feel very real until the true explanation is found.",
        )
    ],
    "ghost": [
        (
            "Why can a ghost story feel scarier at night?",
            "At night, shadows are darker and sounds are harder to explain quickly. That can make the imagination hurry ahead of the facts.",
        )
    ],
    "cat": [
        (
            "Why can a cat on a roof sound like a person walking?",
            "A cat places its paws one after another, so the steps can sound slow and deliberate in the dark. When you cannot see the cat, your ears may guess wrong.",
        )
    ],
    "shutter": [
        (
            "What is a shutter?",
            "A shutter is a wooden or metal panel by a window. If it gets loose, wind can make it knock against the wall.",
        )
    ],
    "sheet": [
        (
            "Why can a sheet on a clothesline look spooky?",
            "A white sheet catches light easily and puffs up in the wind. From far away, that can look like a floating shape.",
        )
    ],
    "branch": [
        (
            "Why does a tree branch scratch a window?",
            "When the wind bends a branch toward a house, it can rub the glass or frame. The sound repeats each time the branch swings back.",
        )
    ],
    "wind": [
        (
            "How does wind make strange sounds around a house?",
            "Wind moves loose things like shutters, branches, and cloth. Those moving things can tap, scrape, or flap in ways that sound mysterious.",
        )
    ],
    "attic": [
        (
            "What is an attic?",
            "An attic is a room or space just under the roof of a house. People often keep trunks, boxes, or blankets there.",
        )
    ],
    "hallway": [
        (
            "What is a hallway?",
            "A hallway is a passage that connects rooms in a house. Sounds can echo there and seem farther away than they really are.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "misunderstanding",
    "ghost",
    "cat",
    "shutter",
    "sheet",
    "branch",
    "wind",
    "attic",
    "hallway",
]


CURATED = [
    StoryParams(
        setting="attic",
        source="sheet_window",
        rumor="white_lady",
        hero_name="Mina",
        hero_gender="girl",
        helper_type="grandmother",
        helper_name="Grandma",
        delay=0,
    ),
    StoryParams(
        setting="hallway",
        source="shutter",
        rumor="knocking_ghost",
        hero_name="Owen",
        hero_gender="boy",
        helper_type="father",
        helper_name="Father",
        delay=1,
    ),
    StoryParams(
        setting="attic",
        source="cat_roof",
        rumor="roof_ghost",
        hero_name="Lucy",
        hero_gender="girl",
        helper_type="aunt",
        helper_name="Aunt Bea",
        delay=2,
    ),
    StoryParams(
        setting="shed",
        source="branch_window",
        rumor="window_whisperer",
        hero_name="Theo",
        hero_gender="boy",
        helper_type="grandfather",
        helper_name="Grandpa",
        delay=0,
    ),
    StoryParams(
        setting="hallway",
        source="branch_window",
        rumor="window_whisperer",
        hero_name="Clara",
        hero_gender="girl",
        helper_type="mother",
        helper_name="Mother",
        delay=1,
    ),
]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    setting = world.facts["setting"]
    rumor = world.facts["rumor"]
    source_cfg = world.facts["source_cfg"]
    delay = world.facts["delay"]
    prompts = [
        'Write a gentle ghost story for a 3-to-5-year-old that includes the words "procrastinate" and "conclusion".',
        f"Tell a spooky-but-safe story where a {hero.type} in {setting.place} mistakes {source_cfg.nature} for {rumor.title}.",
        "Write a misunderstanding story in which a child waits too long to ask for help, then learns the ordinary truth behind a frightening sound or shape.",
    ]
    if delay == 0:
        prompts.append(
            f"Make the ending calm and brave: the child asks for help the same night and discovers the simple explanation in {setting.place}."
        )
    else:
        prompts.append(
            "Let the child procrastinate before asking for help, so the misunderstanding grows before a warm adult reveals the truth."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    setting = world.facts["setting"]
    source_cfg = world.facts["source_cfg"]
    rumor = world.facts["rumor"]
    delay = world.facts["delay"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {hero.pronoun('possessive')} {helper.label_word}, in a spooky-feeling part of the house. {hero.id} was supposed to {setting.errand}, but fear got in the way first.",
        ),
        (
            f"Why did {hero.id} feel scared in {setting.place}?",
            f"{hero.id} heard or saw something strange there and remembered a rumor about {rumor.title}. That misunderstanding made an ordinary sign feel ghostly.",
        ),
        (
            f"What was the strange sign really?",
            f"It was really {source_cfg.nature}. The truth only became clear when {helper.label_word} brought a lamp and looked carefully.",
        ),
    ]
    if delay == 0:
        qa.append(
            (
                f"Did {hero.id} keep quiet for long?",
                f"No. {hero.id} almost froze, but decided not to procrastinate and asked for help quickly. Because of that, the scary conclusion was corrected the same night.",
            )
        )
    else:
        qa.append(
            (
                f"How did procrastinating change the story?",
                f"{hero.id} waited instead of speaking right away, so the fear had more time to grow. The misunderstanding became larger because imagination kept working while the truth stayed hidden.",
            )
        )
    qa.append(
        (
            "What is the conclusion of the story?",
            f"The conclusion is that the 'ghost' was not a ghost at all, only {source_cfg.nature}. {hero.id} also learned that asking for help early is better than letting a misunderstanding grow.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"misunderstanding", "ghost"} | set(world.facts["setting"].tags) | set(world.facts["source_cfg"].tags)
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} cue={world.facts.get('cue')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
cue_match(Rumor, Cue) :- rumor(Rumor), requires(Rumor, Cue).
fitting_source(Setting, Source) :- setting(Setting), source(Source), seen_in(Setting, Source), source_place(Source, Setting).
valid(Setting, Source, Rumor) :- fitting_source(Setting, Source), cue_of(Source, Cue), cue_match(Rumor, Cue).

late :- delay(D), D > 0.
outcome(night_reveal) :- not late.
outcome(dawn_reveal) :- late.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, setting in SETTINGS.items():
        for source_id in sorted(setting.affords):
            lines.append(asp.fact("seen_in", sid, source_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("cue_of", source_id, source.cue))
        for place in sorted(source.places):
            lines.append(asp.fact("source_place", source_id, place))
    for rumor_id, rumor in RUMORS.items():
        lines.append(asp.fact("rumor", rumor_id))
        lines.append(asp.fact("requires", rumor_id, rumor.cue_needed))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(delay: int) -> str:
    import asp

    model = asp.one_model(asp_program(asp.fact("delay", delay), "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: valid_combos() matches clingo ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    for delay in [0, 1, 2]:
        py_out = outcome_of(delay)
        asp_out = asp_outcome(delay)
        if py_out != asp_out:
            rc = 1
            print(f"MISMATCH in outcome for delay={delay}: python={py_out} clingo={asp_out}")
    if rc == 0:
        print("OK: outcome model matches for delays 0, 1, and 2.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story in smoke test")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        emitted = buf.getvalue()
        if "### smoke" not in emitted or "ghost" not in emitted.lower():
            raise StoryError("emit smoke test did not print expected content")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a gentle ghost-story misunderstanding. "
        "Unspecified choices are selected at random (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--rumor", choices=RUMORS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.source and args.rumor and not valid_combo(args.setting, args.source, args.rumor):
        raise StoryError(explain_rejection(args.setting, args.source, args.rumor))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.source is None or combo[1] == args.source)
        and (args.rumor is None or combo[2] == args.rumor)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, source_id, rumor_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        hero_name = args.name
    else:
        hero_name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_type = args.helper or rng.choice(sorted(HELPERS))
    helper_name = HELPERS[helper_type]
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 2])

    return StoryParams(
        setting=setting_id,
        source=source_id,
        rumor=rumor_id,
        hero_name=hero_name,
        hero_gender=gender,
        helper_type=helper_type,
        helper_name=helper_name,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.setting, params.source, params.rumor):
        raise StoryError(explain_rejection(params.setting, params.source, params.rumor))
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.source not in SOURCES:
        raise StoryError(f"(No story: unknown source '{params.source}'.)")
    if params.rumor not in RUMORS:
        raise StoryError(f"(No story: unknown rumor '{params.rumor}'.)")
    if params.helper_type not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper_type}'.)")
    if params.hero_gender not in {"girl", "boy"}:
        raise StoryError(f"(No story: unknown gender '{params.hero_gender}'.)")
    if params.delay not in {0, 1, 2}:
        raise StoryError("(No story: delay must be 0, 1, or 2.)")

    world = tell(
        SETTINGS[params.setting],
        SOURCES[params.source],
        RUMORS[params.rumor],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_type=params.helper_type,
        helper_name=params.helper_name,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, source, rumor) combos:\n")
        for setting_id, source_id, rumor_id in combos:
            print(f"  {setting_id:8} {source_id:13} {rumor_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = (
                f"### {p.hero_name}: {p.rumor} from {p.source} in {p.setting} "
                f"({outcome_of(p.delay)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
