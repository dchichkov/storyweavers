#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/preach_fancy_tum_dim_reconciliation_mystery_to.py
==============================================================================

A standalone storyworld for a pirate-style mystery with kindness and
reconciliation.

Seed ingredients rebuilt as a simulated tiny domain:
- required words: preach, fancy, tum-dim
- features: Reconciliation, Mystery to Solve, Kindness
- style: Pirate Tale

Premise:
Two children turn a room into a fancy pirate ship. A treasured captain token goes
missing, a strange tum-dim sound begins somewhere nearby, and the children start
to blame each other. A kind grown-up refuses to preach, listens carefully, and
solves the mystery. The lost token is found, apologies are made, and the game
sails on with softer hearts.

Run it
------
    python storyworlds/worlds/gpt-5.4/preach_fancy_tum_dim_reconciliation_mystery_to.py
    python storyworlds/worlds/gpt-5.4/preach_fancy_tum_dim_reconciliation_mystery_to.py --all
    python storyworlds/worlds/gpt-5.4/preach_fancy_tum_dim_reconciliation_mystery_to.py --qa
    python storyworlds/worlds/gpt-5.4/preach_fancy_tum_dim_reconciliation_mystery_to.py --trace --seed 7
    python storyworlds/worlds/gpt-5.4/preach_fancy_tum_dim_reconciliation_mystery_to.py --asp
    python storyworlds/worlds/gpt-5.4/preach_fancy_tum_dim_reconciliation_mystery_to.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt", "sister"}
        male = {"boy", "father", "dad", "man", "uncle", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    title_a: str
    title_b: str
    goal: str
    ending: str
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
class MysterySource:
    id: str
    sound_text: str
    item_label: str
    item_phrase: str
    source_phrase: str
    reveal_template: str
    difficulty: int
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
class HidingPlace:
    id: str
    label: str
    phrase: str
    open_text: str
    fits: set[str] = field(default_factory=set)
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
class HelperAction:
    id: str
    sense: int
    power: int
    text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"accuser", "accused"}]

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


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    place = world.get("place")
    if source.meters["jostling"] < THRESHOLD:
        return out
    if not source.attrs.get("hidden", False):
        return out
    sig = ("noise", source.id, place.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    place.meters["noise"] += 1
    for kid in world.kids():
        kid.memes["wonder"] += 1
    out.append("__tum_dim__")
    return out


def _r_quarrel(world: World) -> list[str]:
    a = world.get("hero")
    b = world.get("friend")
    if a.memes["accusing"] < THRESHOLD or b.memes["defending"] < THRESHOLD:
        return []
    sig = ("quarrel", a.id, b.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["hurt"] += 1
    b.memes["hurt"] += 1
    a.meters["distance"] += 1
    b.meters["distance"] += 1
    world.get("room").meters["tension"] += 1
    return ["__quarrel__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="noise", tag="physical", apply=_r_noise),
    Rule(name="quarrel", tag="social", apply=_r_quarrel),
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


def source_fits_place(source: MysterySource, place: HidingPlace) -> bool:
    return source.id in place.fits


def sensible_helpers() -> list[HelperAction]:
    return [h for h in HELPERS.values() if h.sense >= SENSE_MIN]


def can_solve(source: MysterySource, helper: HelperAction) -> bool:
    return helper.power >= source.difficulty


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme_id in THEMES:
        for source_id, source in SOURCES.items():
            for place_id, place in PLACES.items():
                if not source_fits_place(source, place):
                    continue
                for helper_id, helper in HELPERS.items():
                    if helper.sense >= SENSE_MIN and can_solve(source, helper):
                        combos.append((theme_id, source_id, place_id, helper_id))
    return combos


def predict_sound(world: World) -> dict:
    sim = world.copy()
    sim.get("source").meters["jostling"] += 1
    propagate(sim, narrate=False)
    return {
        "noise": sim.get("place").meters["noise"] >= THRESHOLD,
        "wonder": sum(k.memes["wonder"] for k in sim.kids()),
    }


def play_setup(world: World, hero: Entity, friend: Entity, theme: Theme) -> None:
    for kid in (hero, friend):
        kid.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {hero.id} and {friend.id} turned the sitting room into "
        f"{theme.scene}. {theme.rig}"
    )
    world.say(
        f'"{theme.title_a} {hero.id} and {theme.title_b} {friend.id}!" {hero.id} cried. '
        f'"Today we sail for {theme.goal}!"'
    )


def token_setup(world: World, hero: Entity, friend: Entity, source: MysterySource) -> None:
    token = world.get("token")
    token.attrs["owner_turn"] = hero.id
    world.say(
        f"They had one special treasure for the game: {source.item_phrase}. Whoever held it got to be captain first."
    )
    world.say(
        f"{hero.id} wore it for a while, then set it down so {friend.id} could have the next turn."
    )


def missing_turn(world: World, hero: Entity, friend: Entity, source: MysterySource) -> None:
    token = world.get("token")
    token.attrs["missing"] = True
    world.say(
        f"But when {friend.id} reached for the treasure, it was gone. The little pirate ship suddenly felt very still."
    )
    world.say(
        f'"My {source.item_label} was right here," {hero.id} said. {friend.id} looked around under the blanket sail and behind the cushions.'
    )


def sound_beat(world: World, source: MysterySource, place: HidingPlace) -> None:
    prediction = predict_sound(world)
    world.facts["predicted_noise"] = prediction["noise"]
    world.get("source").meters["jostling"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then, from {place.phrase}, came a soft {source.sound_text} -- {source.sound_text}."
    )
    world.say(
        f"Both children froze. It was not a loud sound, but it was enough to make the mystery feel real."
    )


def accusation(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["accusing"] += 1
    friend.memes["defending"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Did you hide it?" {hero.id} asked. The question came out sharper than {hero.pronoun("subject")} meant.'
    )
    world.say(
        f'{friend.id} drew back and frowned. "No, I did not. You do not have to say it like that."'
    )


def helper_arrives(world: World, helper_ent: Entity, place: HidingPlace) -> None:
    world.say(
        f"{helper_ent.label_word.capitalize()} heard the worried voices and came to the doorway. "
        f'{helper_ent.pronoun().capitalize()} glanced at {place.phrase}, then at the two small pirates.'
    )


def gentle_refusal_to_preach(world: World, helper_ent: Entity) -> None:
    for kid in world.kids():
        kid.memes["heard_kindness"] += 1
    world.say(
        f'"I am not here to preach," {helper_ent.label_word} said softly. '
        f'"And you do not need to preach at each other either. We can be kind and solve this together."'
    )


def investigate(world: World, helper_ent: Entity, helper: HelperAction, place: HidingPlace) -> None:
    world.say(
        f"{helper_ent.label_word.capitalize()} {helper.text}."
    )
    world.say(place.open_text)


def reveal(world: World, source: MysterySource, place: HidingPlace) -> None:
    src = world.get("source")
    token = world.get("token")
    src.attrs["hidden"] = False
    token.attrs["missing"] = False
    token.meters["found"] += 1
    world.facts["solved"] = True
    explanation = source.reveal_template.format(place=place.label, item=source.item_label)
    world.say(explanation)
    world.say(
        f"That was the whole mystery. The {source.item_label} had only slipped away into the wrong spot while the game rocked and rustled."
    )


def reconcile(world: World, hero: Entity, friend: Entity) -> None:
    for kid in (hero, friend):
        kid.memes["relief"] += 1
        kid.memes["kindness"] += 1
        kid.meters["distance"] = 0.0
        kid.memes["hurt"] = 0.0
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.get("room").meters["tension"] = 0.0
    world.say(
        f"{hero.id}'s cheeks grew warm. \"I am sorry,\" {hero.pronoun()} said. "
        f"\"I should have asked more kindly.\""
    )
    world.say(
        f'"I am sorry too," said {friend.id}. "I was hurt, but I know you were worried about the treasure."'
    )


def ending(world: World, hero: Entity, friend: Entity, helper_ent: Entity, theme: Theme, source: MysterySource) -> None:
    world.say(
        f"{helper_ent.label_word.capitalize()} hung {source.item_phrase} between them for one moment, and both children held it together."
    )
    world.say(
        f"Then the two pirates smiled, stood shoulder to shoulder again, and {theme.ending}. The fancy ship felt warm and friendly once more."
    )


def tell(
    theme: Theme,
    source: MysterySource,
    place: HidingPlace,
    helper: HelperAction,
    hero_name: str = "Lily",
    hero_gender: str = "girl",
    friend_name: str = "Tom",
    friend_gender: str = "boy",
    helper_type: str = "mother",
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="accuser",
        attrs={"name": hero_name},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="accused",
        attrs={"name": friend_name},
    ))
    helper_ent = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label="the helper",
        role="helper",
    ))
    world.add(Entity(id="room", type="room", label="the room"))
    world.add(Entity(
        id="place",
        type="place",
        label=place.label,
        attrs={"place_id": place.id},
        tags=set(place.tags),
    ))
    world.add(Entity(
        id="source",
        type="source",
        label=source.source_phrase,
        attrs={"hidden": True, "source_id": source.id},
        tags=set(source.tags),
    ))
    world.add(Entity(
        id="token",
        type="token",
        label=source.item_label,
        attrs={"missing": False},
    ))

    hero.memes["trust"] = 4.0
    friend.memes["trust"] = 4.0
    hero.memes["accusing"] = 0.0
    friend.memes["defending"] = 0.0
    world.facts["solved"] = False

    play_setup(world, hero, friend, theme)
    token_setup(world, hero, friend, source)

    world.para()
    missing_turn(world, hero, friend, source)
    sound_beat(world, source, place)
    accusation(world, hero, friend)

    world.para()
    helper_arrives(world, helper_ent, place)
    gentle_refusal_to_preach(world, helper_ent)
    investigate(world, helper_ent, helper, place)
    reveal(world, source, place)

    world.para()
    reconcile(world, hero, friend)
    ending(world, hero, friend, helper_ent, theme, source)

    world.facts.update(
        theme=theme,
        source_cfg=source,
        place_cfg=place,
        helper_cfg=helper,
        hero=hero,
        friend=friend,
        helper=helper_ent,
        hero_name=hero_name,
        friend_name=friend_name,
        item_label=source.item_label,
        item_phrase=source.item_phrase,
        mystery_sound=source.sound_text,
        quarrel=world.get("room").meters["tension"] == 0.0 and hero.memes["accusing"] >= THRESHOLD,
        reconciled=hero.memes["kindness"] >= THRESHOLD and friend.memes["kindness"] >= THRESHOLD,
    )
    return world


THEMES = {
    "brig": Theme(
        id="brig",
        scene="a fancy pirate brig",
        rig="The sofa was the deck, a blue blanket became the sea, a broom stood tall as a mast, and a painted shoebox held their make-believe supplies.",
        title_a="Captain",
        title_b="First Mate",
        goal="the Moon-Map Reef",
        ending="set sail again for the Moon-Map Reef",
    ),
    "galleon": Theme(
        id="galleon",
        scene="a fancy pirate galleon",
        rig="The rug was the harbor, the sofa was the ship, two cushions made the captain's cabin, and a striped scarf fluttered like a brave little flag.",
        title_a="Captain",
        title_b="Navigator",
        goal="the Starfish Island",
        ending="pushed off toward Starfish Island",
    ),
    "sloop": Theme(
        id="sloop",
        scene="a fancy pirate sloop",
        rig="A laundry basket became the lookout nest, the sofa was the ship, a chair turned into the stern, and a blanket tunnel promised secret cargo below deck.",
        title_a="Captain",
        title_b="Quartermaster",
        goal="the Whispering Bay",
        ending="sailed for Whispering Bay with lighter hearts",
    ),
}

SOURCES = {
    "shell_cup": MysterySource(
        id="shell_cup",
        sound_text="tum-dim",
        item_label="captain shell badge",
        item_phrase="the fancy captain shell badge",
        source_phrase="a shell necklace tapping a tin cup",
        reveal_template="Inside the {place} was a shell necklace tapping a little tin cup, and tucked inside the cup was the {item}.",
        difficulty=1,
        tags={"shells", "listening", "mystery"},
    ),
    "drum_charm": MysterySource(
        id="drum_charm",
        sound_text="tum-dim",
        item_label="captain compass charm",
        item_phrase="the fancy captain compass charm",
        source_phrase="a toy drum bumping a dangling charm",
        reveal_template="Inside the {place} sat a tiny toy drum. Each wobble made a neat tum-dim sound, and the {item} was caught in the drum strap.",
        difficulty=2,
        tags={"drum", "listening", "mystery"},
    ),
    "kitten_spoon": MysterySource(
        id="kitten_spoon",
        sound_text="tum-dim",
        item_label="captain ribbon medal",
        item_phrase="the fancy captain ribbon medal",
        source_phrase="a kitten batting a silver spoon",
        reveal_template="Inside the {place} was a little kitten, batting a silver spoon against the side. The spoon made the tum-dim sound, and the {item} was pinned under one soft paw.",
        difficulty=2,
        tags={"kitten", "kindness", "mystery"},
    ),
}

PLACES = {
    "captain_chest": HidingPlace(
        id="captain_chest",
        label="captain chest",
        phrase="the old captain chest by the sofa",
        open_text="The lid creaked up with a soft little sigh.",
        fits={"shell_cup", "drum_charm"},
        tags={"chest"},
    ),
    "map_crate": HidingPlace(
        id="map_crate",
        label="map crate",
        phrase="the map crate under the blanket sail",
        open_text="The crate slid out with a scrape, and everyone leaned closer.",
        fits={"drum_charm"},
        tags={"crate"},
    ),
    "curtain_nook": HidingPlace(
        id="curtain_nook",
        label="curtain nook",
        phrase="the curtain nook beside the window",
        open_text="The curtain was lifted very slowly, so whatever hid there would not be frightened.",
        fits={"kitten_spoon"},
        tags={"curtain"},
    ),
    "barrel_basket": HidingPlace(
        id="barrel_basket",
        label="barrel basket",
        phrase="the round barrel basket by the chair",
        open_text="The basket tipped just enough to let the mystery peep out.",
        fits={"shell_cup"},
        tags={"basket"},
    ),
    "window_sill": HidingPlace(
        id="window_sill",
        label="window sill",
        phrase="the window sill",
        open_text="They looked at the sill.",
        fits=set(),
        tags={"window"},
    ),
}

HELPERS = {
    "listen_gently": HelperAction(
        id="listen_gently",
        sense=3,
        power=2,
        text="knelt down, listened to the tum-dim sound, and followed it without hurrying anyone",
        qa_text="listened carefully and followed the sound",
        tags={"listening", "kindness"},
    ),
    "lantern_peek": HelperAction(
        id="lantern_peek",
        sense=3,
        power=3,
        text="took a small lantern, shone its warm light into the hiding place, and looked without scolding",
        qa_text="used a lantern and looked gently into the hiding place",
        tags={"light", "kindness"},
    ),
    "wait_quietly": HelperAction(
        id="wait_quietly",
        sense=2,
        power=2,
        text="held one finger to friendly lips and waited quietly until the tum-dim sound happened again",
        qa_text="waited quietly for the sound and then checked the right spot",
        tags={"patience", "kindness"},
    ),
    "kick_box": HelperAction(
        id="kick_box",
        sense=1,
        power=3,
        text="gave the hiding place a hard kick",
        qa_text="kicked the box",
        tags={"rough"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Maya", "Nora"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]


@dataclass
class StoryParams:
    theme: str
    source: str
    place: str
    helper_action: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    helper_type: str
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
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something you do not understand yet and need to figure out. You solve it by noticing clues and thinking carefully."
        )
    ],
    "listening": [
        (
            "Why can careful listening help solve a problem?",
            "Careful listening can help you notice where a sound is coming from. That can lead you to the clue you need."
        )
    ],
    "kindness": [
        (
            "What does kindness look like during an argument?",
            "Kindness means speaking gently, listening, and trying to help instead of hurting. It can make it easier for everyone to calm down and fix the problem together."
        )
    ],
    "shells": [
        (
            "Why might shells make a tapping sound?",
            "Hard shells can click and tap when they bump into cups or wood. Small sounds can seem mysterious in a quiet room."
        )
    ],
    "drum": [
        (
            "What makes a drum say tum-dim?",
            "A drum makes a deep sound when its tight top is bumped or tapped. A small toy drum can make a soft tum-dim."
        )
    ],
    "kitten": [
        (
            "Why should you move gently around a kitten?",
            "Kittens are small and can be startled easily. Gentle hands and quiet voices help them feel safe."
        )
    ],
    "light": [
        (
            "Why is a lantern helpful when something is hidden?",
            "A lantern gives light so you can see into dark corners. Seeing clearly helps you solve the problem safely."
        )
    ],
    "patience": [
        (
            "Why is patience useful in a mystery?",
            "Patience gives you time to notice clues instead of guessing too fast. Waiting can be the thing that lets the answer appear."
        )
    ],
}
KNOWLEDGE_ORDER = ["mystery", "listening", "kindness", "shells", "drum", "kitten", "light", "patience"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero_name = f["hero_name"]
    friend_name = f["friend_name"]
    theme = f["theme"]
    source = f["source_cfg"]
    return [
        (
            f'Write a pirate-style story for a 3-to-5-year-old where two children on {theme.scene} hear '
            f'a "{source.sound_text}" sound, think a treasure is missing, and solve the mystery kindly.'
        ),
        (
            f"Tell a gentle mystery where {hero_name} and {friend_name} start to quarrel over {source.item_phrase}, "
            f"but a grown-up says they will not preach and helps them listen for clues."
        ),
        (
            f'Write a story that includes the words "preach," "fancy," and "tum-dim," and ends with reconciliation '
            f"after a small pirate mystery is solved."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero_name = f["hero_name"]
    friend_name = f["friend_name"]
    source = f["source_cfg"]
    place = f["place_cfg"]
    helper_cfg = f["helper_cfg"]
    helper_ent = f["helper"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two children, {hero_name} and {friend_name}, pretending to be pirates, and their {helper_ent.label_word} who helps them. The story follows their game, their quarrel, and their making up."
        ),
        (
            "What was the mystery to solve?",
            f"The mystery was that {source.item_phrase} had gone missing just as the children were taking turns. At the same time, a soft tum-dim sound came from {place.phrase}, making the missing treasure feel even stranger."
        ),
        (
            f"Why did {hero_name} and {friend_name} start to quarrel?",
            f"They started to quarrel because the treasure was gone and {hero_name} worried that {friend_name} had hidden it. The sharp question hurt {friend_name}'s feelings, so the mystery turned into a small argument too."
        ),
        (
            f"How did the {helper_ent.label_word} help solve the problem?",
            f"The {helper_ent.label_word} did not scold or preach. {helper_ent.pronoun().capitalize()} {helper_cfg.qa_text}, which led everyone to the real hiding place and the true cause of the tum-dim sound."
        ),
        (
            "How were the children reconciled?",
            f"They were reconciled after the treasure was found and the children understood that neither one had tried to be unkind. Then they apologized to each other and stood together again, so the ending showed friendship returning, not just the mystery being solved."
        ),
    ]
    if f.get("reconciled"):
        qa.append(
            (
                "How did the story end?",
                f"It ended with the two pirates sharing the treasure and sailing on together again. The final image of the fancy ship feeling warm and friendly shows what changed inside them."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"mystery", "kindness"}
    source = world.facts["source_cfg"]
    helper_cfg = world.facts["helper_cfg"]
    tags |= set(source.tags)
    tags |= set(helper_cfg.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        shown_attrs = {k: v for k, v in ent.attrs.items() if v or v == 0}
        if shown_attrs:
            bits.append(f"attrs={shown_attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="brig",
        source="shell_cup",
        place="captain_chest",
        helper_action="listen_gently",
        hero_name="Lily",
        hero_gender="girl",
        friend_name="Tom",
        friend_gender="boy",
        helper_type="mother",
    ),
    StoryParams(
        theme="galleon",
        source="drum_charm",
        place="map_crate",
        helper_action="lantern_peek",
        hero_name="Mia",
        hero_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        helper_type="father",
    ),
    StoryParams(
        theme="sloop",
        source="kitten_spoon",
        place="curtain_nook",
        helper_action="wait_quietly",
        hero_name="Nora",
        hero_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        helper_type="aunt",
    ),
    StoryParams(
        theme="brig",
        source="shell_cup",
        place="barrel_basket",
        helper_action="listen_gently",
        hero_name="Max",
        hero_gender="boy",
        friend_name="Ella",
        friend_gender="girl",
        helper_type="uncle",
    ),
]


def explain_rejection(source: MysterySource, place: HidingPlace) -> str:
    return (
        f"(No story: {source.source_phrase} is not a good fit for {place.label}. "
        f"The tum-dim clue would not honestly point there, so the mystery would feel weak.)"
    )


def explain_helper(helper_id: str) -> str:
    helper = HELPERS[helper_id]
    better = ", ".join(sorted(h.id for h in sensible_helpers()))
    return (
        f"(Refusing helper action '{helper_id}': it scores too low on kindness/common sense "
        f"(sense={helper.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


ASP_RULES = r"""
sensible(H) :- helper(H), sense(H,S), sense_min(M), S >= M.
solves(Src, H) :- source(Src), helper(H), difficulty(Src,D), power(H,P), P >= D.
valid(T, Src, Place, H) :- theme(T), source(Src), place(Place), helper(H),
                           fits(Place, Src), sensible(H), solves(Src, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("difficulty", source_id, source.difficulty))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for source_id in sorted(place.fits):
            lines.append(asp.fact("fits", place_id, source_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("sense", helper_id, helper.sense))
        lines.append(asp.fact("power", helper_id, helper.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_helpers() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(h for (h,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid combos match ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_helpers = set(asp_sensible_helpers())
    p_helpers = {h.id for h in sensible_helpers()}
    if c_helpers == p_helpers:
        print(f"OK: sensible helpers match ({sorted(c_helpers)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible helpers: clingo={sorted(c_helpers)} python={sorted(p_helpers)}")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        rng = random.Random(11)
        params = resolve_params(build_parser().parse_args([]), rng)
        params.seed = 11
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: default resolve/generate path succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Pirate-style mystery storyworld with kindness, tum-dim clues, and reconciliation."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--helper-action", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper_action and HELPERS[args.helper_action].sense < SENSE_MIN:
        raise StoryError(explain_helper(args.helper_action))
    if args.source and args.place:
        source = SOURCES[args.source]
        place = PLACES[args.place]
        if not source_fits_place(source, place):
            raise StoryError(explain_rejection(source, place))
    if args.source and args.helper_action:
        source = SOURCES[args.source]
        helper = HELPERS[args.helper_action]
        if helper.sense >= SENSE_MIN and not can_solve(source, helper):
            raise StoryError(
                f"(No story: {args.helper_action} is too weak to solve the {args.source} mystery honestly.)"
            )

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.source is None or combo[1] == args.source)
        and (args.place is None or combo[2] == args.place)
        and (args.helper_action is None or combo[3] == args.helper_action)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, source_id, place_id, helper_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)
    helper_type = args.helper_type or rng.choice(["mother", "father", "aunt", "uncle"])
    return StoryParams(
        theme=theme_id,
        source=source_id,
        place=place_id,
        helper_action=helper_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.helper_action not in HELPERS:
        raise StoryError(f"(Unknown helper action: {params.helper_action})")

    source = SOURCES[params.source]
    place = PLACES[params.place]
    helper = HELPERS[params.helper_action]

    if helper.sense < SENSE_MIN:
        raise StoryError(explain_helper(params.helper_action))
    if not source_fits_place(source, place):
        raise StoryError(explain_rejection(source, place))
    if not can_solve(source, helper):
        raise StoryError(
            f"(No story: {params.helper_action} cannot fully solve the {params.source} mystery.)"
        )

    world = tell(
        theme=THEMES[params.theme],
        source=source,
        place=place,
        helper=helper,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        helper_type=params.helper_type,
    )

    hero_name = world.facts["hero_name"]
    friend_name = world.facts["friend_name"]
    story_text = world.render().replace("hero", hero_name).replace("friend", friend_name)

    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        helpers = asp_sensible_helpers()
        print(f"sensible helpers: {', '.join(helpers)}\n")
        print(f"{len(combos)} compatible (theme, source, place, helper) combos:\n")
        for theme_id, source_id, place_id, helper_id in combos:
            print(f"  {theme_id:8} {source_id:12} {place_id:14} {helper_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero_name} & {p.friend_name}: {p.source} in {p.place} "
                f"({p.theme}, {p.helper_action})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
