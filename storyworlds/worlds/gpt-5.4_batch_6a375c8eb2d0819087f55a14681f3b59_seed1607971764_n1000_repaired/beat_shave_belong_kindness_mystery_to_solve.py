#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/beat_shave_belong_kindness_mystery_to_solve.py
=========================================================================

A standalone story world about a child hearing a secret beat, following a small
mystery, and solving it with kindness. Every valid story includes the words
"beat", "shave", and "belong" naturally in the prose.

Premise
-------
A child is getting ready for a small neighborhood music walk. Somewhere nearby,
a hidden beat keeps tapping. The child finds a curled wood shave and follows the
clue to a shy new child who has been practicing on an improvised drum because
they are afraid they do not belong. A kind invitation and a shared rhythm tool
turn the mystery into a warm ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/beat_shave_belong_kindness_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4/beat_shave_belong_kindness_mystery_to_solve.py --place courtyard --source bucket_drum
    python storyworlds/worlds/gpt-5.4/beat_shave_belong_kindness_mystery_to_solve.py --gift balloon
    python storyworlds/worlds/gpt-5.4/beat_shave_belong_kindness_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4/beat_shave_belong_kindness_mystery_to_solve.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/beat_shave_belong_kindness_mystery_to_solve.py --trace
    python storyworlds/worlds/gpt-5.4/beat_shave_belong_kindness_mystery_to_solve.py --json
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
    attrs: dict = field(default_factory=dict)
    makes_beat: bool = False
    keeps_rhythm: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)
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
class Place:
    id: str
    label: str
    opening: str
    hideout: str
    ending: str
    afford_sound: bool = True
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
    label: str
    phrase: str
    beat_line: str
    clue_line: str
    made_of_wood: bool = False
    makes_beat: bool = True
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
class Gift:
    id: str
    label: str
    phrase: str
    action: str
    keeps_rhythm: bool = True
    sense: int = 3
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
class Welcome:
    id: str
    line: str
    comfort: str
    sense: int = 3
    kindness: int = 2
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
    def __init__(self, place: Place) -> None:
        self.place = place
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


def _r_secret_beat(world: World) -> list[str]:
    out: list[str] = []
    hidden = world.get("hidden")
    source = world.get("source")
    place = world.get("place")
    if hidden.meters["tapping"] >= THRESHOLD and source.makes_beat:
        sig = ("beat", hidden.id, source.id)
        if sig not in world.fired:
            world.fired.add(sig)
            place.meters["sound"] += 1
            out.append("__beat__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    hidden = world.get("hidden")
    clue = world.get("clue")
    if hidden.meters["carving"] >= THRESHOLD:
        sig = ("clue", hidden.id)
        if sig not in world.fired:
            world.fired.add(sig)
            clue.meters["foundable"] += 1
            out.append("__clue__")
    return out


def _r_invitation(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    hidden = world.get("hidden")
    gift = world.get("gift")
    adult = world.get("adult")
    if hero.memes["kind_offer"] >= THRESHOLD and gift.keeps_rhythm and adult.memes["welcome"] >= THRESHOLD:
        sig = ("belong", hidden.id, gift.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hidden.memes["belonging"] += 2
            hidden.memes["worry"] = 0.0
            hero.memes["joy"] += 1
            out.append("__belong__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="secret_beat", tag="physical", apply=_r_secret_beat),
    Rule(name="clue", tag="physical", apply=_r_clue),
    Rule(name="invitation", tag="social", apply=_r_invitation),
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


def source_is_reasonable(place: Place, source: Source) -> bool:
    return place.afford_sound and source.makes_beat


def sensible_gifts() -> list[Gift]:
    return [g for g in GIFTS.values() if g.keeps_rhythm and g.sense >= SENSE_MIN]


def sensible_welcomes() -> list[Welcome]:
    return [w for w in WELCOMES.values() if w.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for source_id, source in SOURCES.items():
            if not source_is_reasonable(place, source):
                continue
            for gift_id, gift in GIFTS.items():
                if not (gift.keeps_rhythm and gift.sense >= SENSE_MIN):
                    continue
                for welcome_id, welcome in WELCOMES.items():
                    if welcome.sense >= SENSE_MIN:
                        combos.append((place_id, source_id, gift_id, welcome_id))
    return combos


def explain_source_rejection(place: Place, source: Source) -> str:
    if not place.afford_sound:
        return f"(No story: {place.label} is not set up for a hidden tapping mystery.)"
    if not source.makes_beat:
        return (
            f"(No story: {source.phrase} cannot make a clear beat, so there is no "
            f"honest mystery for the child to follow.)"
        )
    return "(No story: this place and sound source do not make a reasonable mystery.)"


def explain_gift_rejection(gift_id: str) -> str:
    gift = GIFTS[gift_id]
    good = ", ".join(sorted(g.id for g in sensible_gifts()))
    return (
        f"(Refusing gift '{gift_id}': it does not help the shy child join the music. "
        f"A kindness here should offer a real way to keep the beat. Try: {good}.)"
    )


def explain_welcome_rejection(welcome_id: str) -> str:
    welcome = WELCOMES[welcome_id]
    good = ", ".join(sorted(w.id for w in sensible_welcomes()))
    return (
        f"(Refusing welcome '{welcome_id}': it is too cold for this heartwarming world "
        f"(sense={welcome.sense} < {SENSE_MIN}). Try: {good}.)"
    )


def predict_belonging(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").memes["kind_offer"] += 1
    sim.get("adult").memes["welcome"] = float(sim.facts["welcome_cfg"].kindness)
    propagate(sim, narrate=False)
    hidden = sim.get("hidden")
    return {
        "will_belong": hidden.memes["belonging"] >= THRESHOLD,
        "worry_after": hidden.memes["worry"],
    }


def introduce(world: World, hero: Entity, adult: Entity, place: Place) -> None:
    world.say(
        f"{hero.id} was walking with {hero.pronoun('possessive')} {adult.label_word} through "
        f"{place.label} on the way to the little music walk. {place.opening}"
    )
    hero.memes["joy"] += 1


def first_beat(world: World, hero: Entity, source: Source) -> None:
    hidden = world.get("hidden")
    hidden.meters["tapping"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.id} heard a soft beat: {source.beat_line} It was not loud, "
        f"but it sounded too careful to be an accident."
    )
    hero.memes["curiosity"] += 1


def search(world: World, hero: Entity, place: Place, source: Source) -> None:
    hidden = world.get("hidden")
    clue = world.get("clue")
    hidden.meters["carving"] = 1.0
    propagate(world, narrate=False)
    clue.meters["seen"] += 1
    world.say(
        f"{hero.id} followed the sound toward {place.hideout}. On the ground lay "
        f"{source.clue_line}"
    )
    world.say(
        f'"A shave of wood," {hero.pronoun()} whispered. "Someone was making little sticks."'
    )
    hero.memes["care"] += 1


def discover(world: World, hero: Entity, hidden: Entity, source: Source) -> None:
    hidden.memes["worry"] = 2.0
    hidden.memes["hope"] = 1.0
    world.say(
        f"Behind the crates sat {hidden.id}, tapping {source.phrase} with two tiny sticks. "
        f"The careful beat stopped at once."
    )
    world.say(
        f'"Oh," said {hidden.id}. "{hidden.pronoun("subject").capitalize()} was only practicing. '
        f'I wanted to march too, but I did not think I would belong."'
    )


def kind_guess(world: World, hero: Entity, hidden: Entity, adult: Entity) -> None:
    pred = predict_belonging(world)
    world.facts["predicted_belong"] = pred["will_belong"]
    world.say(
        f"{hero.id} did not laugh. {hero.pronoun().capitalize()} knelt so {hero.pronoun('subject')} "
        f"and {hidden.id} were eye to eye."
    )
    if pred["will_belong"]:
        world.say(
            f'"You already found the beat," {hero.id} said gently. "Maybe you do belong with us."'
        )
    else:
        world.say(
            f'"We can think of a kind way to help," {adult.label_word} said softly.'
        )


def invite(world: World, hero: Entity, hidden: Entity, gift: Gift, adult: Entity, welcome: Welcome) -> None:
    world.get("gift").keeps_rhythm = gift.keeps_rhythm
    hero.memes["kind_offer"] += 1
    adult.memes["welcome"] = float(welcome.kindness)
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} held out {gift.phrase}. "Here," {hero.pronoun()} said. '
        f'"You can {gift.action} with me."'
    )
    world.say(
        f'{adult.label_word.capitalize()} {welcome.line} "{welcome.comfort}"'
    )


def join_walk(world: World, hero: Entity, hidden: Entity, gift: Gift, place: Place) -> None:
    hidden.memes["joy"] += 1
    hero.memes["love"] += 1
    world.say(
        f"{hidden.id}'s shoulders loosened. {hidden.pronoun('subject').capitalize()} took "
        f"{gift.phrase} in both hands and tried the beat again, only this time it matched "
        f"{hero.id}'s steps."
    )
    world.say(
        f"Soon the two children were walking side by side through {place.ending}, keeping time "
        f"together. The mystery was solved, and now the music made room for everyone to belong."
    )


def tell(
    place: Place,
    source: Source,
    gift: Gift,
    welcome: Welcome,
    hero_name: str = "Mina",
    hero_type: str = "girl",
    hidden_name: str = "Owen",
    hidden_type: str = "boy",
    adult_type: str = "grandfather",
) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        role="hero",
        traits=["kind", "curious"],
    ))
    hidden = world.add(Entity(
        id=hidden_name,
        kind="character",
        type=hidden_type,
        role="hidden_child",
        traits=["shy", "careful"],
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        role="adult",
        label="the grown-up",
    ))
    world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=place.label,
    ))
    world.add(Entity(
        id="source",
        kind="thing",
        type="source",
        label=source.label,
        makes_beat=source.makes_beat,
    ))
    world.add(Entity(
        id="gift",
        kind="thing",
        type="gift",
        label=gift.label,
        keeps_rhythm=gift.keeps_rhythm,
    ))
    world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label="wood shave",
    ))
    world.facts["welcome_cfg"] = welcome

    introduce(world, hero, adult, place)
    first_beat(world, hero, source)

    world.para()
    search(world, hero, place, source)
    discover(world, hero, hidden, source)

    world.para()
    kind_guess(world, hero, hidden, adult)
    invite(world, hero, hidden, gift, adult, welcome)
    join_walk(world, hero, hidden, gift, place)

    world.facts.update(
        hero=hero,
        hidden=hidden,
        adult=adult,
        place_cfg=place,
        source_cfg=source,
        gift_cfg=gift,
        welcome_cfg=welcome,
        mystery_solved=True,
        belonging=hidden.memes["belonging"] >= THRESHOLD,
    )
    return world


PLACES = {
    "courtyard": Place(
        id="courtyard",
        label="the brick courtyard",
        opening="Flower pots lined the wall, and paper flags waited for the evening breeze.",
        hideout="the stack of old watering cans near the gate",
        ending="the warm courtyard lights",
        tags={"outside", "music"},
    ),
    "porch": Place(
        id="porch",
        label="the long front porch",
        opening="The steps were swept clean, and little lanterns were waiting to be lit.",
        hideout="the bench under the coat hooks",
        ending="the porch rail with its tiny lanterns",
        tags={"home", "music"},
    ),
    "garden_path": Place(
        id="garden_path",
        label="the garden path",
        opening="Mint smelled sweet in the sun, and flat stones made a soft path to the gate.",
        hideout="the potting table behind the tall sunflowers",
        ending="the path between the flowers",
        tags={"garden", "music"},
    ),
}

SOURCES = {
    "tin_drum": Source(
        id="tin_drum",
        label="tin drum",
        phrase="an upside-down cookie tin",
        beat_line="tap-tap, pause, tap-tap",
        clue_line="a pale curl of wood beside two neatly cut twigs",
        made_of_wood=False,
        makes_beat=True,
        tags={"drum", "sound"},
    ),
    "bucket_drum": Source(
        id="bucket_drum",
        label="bucket drum",
        phrase="a clean bucket turned into a drum",
        beat_line="dum-dum, dum-dum",
        clue_line="a tiny wood shave curled like a comma beside the bucket",
        made_of_wood=False,
        makes_beat=True,
        tags={"bucket", "sound"},
    ),
    "crate_drum": Source(
        id="crate_drum",
        label="crate drum",
        phrase="a wooden crate with a folded cloth on top",
        beat_line="thum-thum, thum",
        clue_line="one smooth shave of pine resting on the cloth",
        made_of_wood=True,
        makes_beat=True,
        tags={"crate", "sound"},
    ),
}

GIFTS = {
    "tambourine": Gift(
        id="tambourine",
        label="tambourine",
        phrase="a little tambourine",
        action="keep the beat",
        keeps_rhythm=True,
        sense=3,
        tags={"tambourine", "music"},
    ),
    "hand_drum": Gift(
        id="hand_drum",
        label="hand drum",
        phrase="a small hand drum",
        action="tap the beat",
        keeps_rhythm=True,
        sense=3,
        tags={"drum", "music"},
    ),
    "shaker": Gift(
        id="shaker",
        label="shaker",
        phrase="a bright seed shaker",
        action="shake the beat",
        keeps_rhythm=True,
        sense=2,
        tags={"shaker", "music"},
    ),
    "balloon": Gift(
        id="balloon",
        label="balloon",
        phrase="a red balloon",
        action="hold it and watch",
        keeps_rhythm=False,
        sense=1,
        tags={"balloon"},
    ),
}

WELCOMES = {
    "smile": Welcome(
        id="smile",
        line="smiled and opened a gentle hand.",
        comfort="There is room in the line for one more friend.",
        sense=3,
        kindness=2,
        tags={"welcome"},
    ),
    "kneel": Welcome(
        id="kneel",
        line="knelt beside them and spoke in a warm voice.",
        comfort="Music sounds best when everyone gets a chance.",
        sense=3,
        kindness=3,
        tags={"welcome"},
    ),
    "shrug": Welcome(
        id="shrug",
        line="gave a quick shrug.",
        comfort="You can stand nearby if you want.",
        sense=1,
        kindness=0,
        tags={"cold"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Zoe", "Ruby", "Tess", "Maya"]
BOY_NAMES = ["Owen", "Eli", "Ben", "Max", "Leo", "Finn", "Theo", "Jude"]


@dataclass
class StoryParams:
    place: str
    source: str
    gift: str
    welcome: str
    hero_name: str
    hero_type: str
    hidden_name: str
    hidden_type: str
    adult_type: str
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
    "drum": [(
        "What is a drum beat?",
        "A drum beat is a steady pattern of taps or thumps that helps people move and play together. A clear beat makes it easier for others to join in."
    )],
    "shaker": [(
        "What does a shaker do in music?",
        "A shaker makes a soft rhythm sound when you move it back and forth. It helps keep time even if it is small."
    )],
    "tambourine": [(
        "What is a tambourine?",
        "A tambourine is a small instrument with jingly metal discs around the edge. You can tap it or shake it to make a bright beat."
    )],
    "welcome": [(
        "Why does a warm welcome help someone feel brave?",
        "A warm welcome shows that other people are glad you came. That can make a shy person feel safer and more ready to join."
    )],
    "belong": [(
        "What does it mean to belong?",
        "To belong means you are part of a group and you are wanted there. People often feel they belong when others make room for them kindly."
    )],
    "mystery": [(
        "What is a mystery?",
        "A mystery is something you do not know yet and want to figure out. Clues help you solve it."
    )],
    "wood": [(
        "What is a wood shave?",
        "A wood shave is a thin curled strip that comes off when wood is trimmed or carved. It can be a clue that someone was making or smoothing something."
    )],
}
KNOWLEDGE_ORDER = ["mystery", "drum", "tambourine", "shaker", "wood", "welcome", "belong"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    hidden = f["hidden"]
    place = f["place_cfg"]
    source = f["source_cfg"]
    gift = f["gift_cfg"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the words "beat", "shave", and "belong".',
        f"Tell a gentle mystery where {hero.id} hears a hidden beat in {place.label}, finds a wood shave as a clue, and discovers {hidden.id} practicing on {source.phrase}.",
        f"Write a story where kindness helps a shy child feel they belong after being invited to join the music with {gift.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    hidden = f["hidden"]
    adult = f["adult"]
    place = f["place_cfg"]
    source = f["source_cfg"]
    gift = f["gift_cfg"]
    welcome = f["welcome_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "What was the mystery in the story?",
            f"The mystery was the secret beat that {hero.id} heard in {place.label}. "
            f"{hero.pronoun('subject').capitalize()} followed the sound and a little wood shave to find out who was making it."
        ),
        (
            f"What clue helped {hero.id} solve the mystery?",
            f"A curled wood shave on the ground was the clue. It showed that someone had been trimming little sticks nearby, which led {hero.id} to the shy drummer."
        ),
        (
            f"Who was making the beat, and why was that child hiding?",
            f"{hidden.id} was making the beat by tapping {source.phrase}. "
            f"{hidden.pronoun('subject').capitalize()} was hiding because {hidden.pronoun('subject')} wanted to join the music walk but worried that {hidden.pronoun('subject')} did not belong."
        ),
        (
            f"How did {hero.id} help {hidden.id} feel they belong?",
            f"{hero.id} offered {gift.phrase} and invited {hidden.id} to keep the beat together. "
            f"Then {adult.label_word} {welcome.line[:-1]} and said, \"{welcome.comfort}\" so the invitation felt safe and real."
        ),
        (
            "How did the story end?",
            f"It ended with the two children walking side by side and keeping time together. "
            f"The ending shows that the mystery turned into friendship, and the music made room for everyone."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mystery", "wood", "belong", "welcome"} | set(f["source_cfg"].tags) | set(f["gift_cfg"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = []
        if e.makes_beat:
            flags.append("makes_beat")
        if e.keeps_rhythm:
            flags.append("keeps_rhythm")
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="courtyard",
        source="tin_drum",
        gift="tambourine",
        welcome="smile",
        hero_name="Mina",
        hero_type="girl",
        hidden_name="Owen",
        hidden_type="boy",
        adult_type="grandfather",
    ),
    StoryParams(
        place="porch",
        source="bucket_drum",
        gift="hand_drum",
        welcome="kneel",
        hero_name="Ben",
        hero_type="boy",
        hidden_name="Ruby",
        hidden_type="girl",
        adult_type="grandmother",
    ),
    StoryParams(
        place="garden_path",
        source="crate_drum",
        gift="shaker",
        welcome="smile",
        hero_name="Nora",
        hero_type="girl",
        hidden_name="Finn",
        hidden_type="boy",
        adult_type="father",
    ),
]


def outcome_of(params: StoryParams) -> str:
    gift = GIFTS[params.gift]
    welcome = WELCOMES[params.welcome]
    kindness = (1 if gift.keeps_rhythm else 0) + welcome.kindness
    return "joined" if kindness >= 2 else "watching"


ASP_RULES = r"""
reasonable_source(P,S) :- place(P), source(S), affords_sound(P), makes_beat(S).
sensible_gift(G) :- gift(G), keeps_rhythm(G), gift_sense(G, X), sense_min(M), X >= M.
sensible_welcome(W) :- welcome(W), welcome_sense(W, X), sense_min(M), X >= M.
valid(P,S,G,W) :- reasonable_source(P,S), sensible_gift(G), sensible_welcome(W).

gift_kindness(1) :- chosen_gift(G), keeps_rhythm(G).
gift_kindness(0) :- chosen_gift(G), not keeps_rhythm(G).
score(K1 + K2) :- gift_kindness(K1), chosen_welcome(W), welcome_kindness(W, K2).
outcome(joined) :- score(S), S >= 2.
outcome(watching) :- score(S), S < 2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("affords_sound", place_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        if source.makes_beat:
            lines.append(asp.fact("makes_beat", source_id))
    for gift_id, gift in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        lines.append(asp.fact("gift_sense", gift_id, gift.sense))
        if gift.keeps_rhythm:
            lines.append(asp.fact("keeps_rhythm", gift_id))
    for welcome_id, welcome in WELCOMES.items():
        lines.append(asp.fact("welcome", welcome_id))
        lines.append(asp.fact("welcome_sense", welcome_id, welcome.sense))
        lines.append(asp.fact("welcome_kindness", welcome_id, welcome.kindness))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_gift", params.gift),
        asp.fact("chosen_welcome", params.welcome),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for s in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a hidden beat, a small clue, and kindness that helps someone belong."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--welcome", choices=WELCOMES)
    ap.add_argument("--adult", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.source:
        place = PLACES[args.place]
        source = SOURCES[args.source]
        if not source_is_reasonable(place, source):
            raise StoryError(explain_source_rejection(place, source))
    if args.gift and args.gift in GIFTS and not (GIFTS[args.gift].keeps_rhythm and GIFTS[args.gift].sense >= SENSE_MIN):
        raise StoryError(explain_gift_rejection(args.gift))
    if args.welcome and args.welcome in WELCOMES and WELCOMES[args.welcome].sense < SENSE_MIN:
        raise StoryError(explain_welcome_rejection(args.welcome))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.source is None or combo[1] == args.source)
        and (args.gift is None or combo[2] == args.gift)
        and (args.welcome is None or combo[3] == args.welcome)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, source_id, gift_id, welcome_id = rng.choice(sorted(combos))
    hero_type = rng.choice(["girl", "boy"])
    hidden_type = "boy" if hero_type == "girl" else "girl" if rng.random() < 0.6 else rng.choice(["girl", "boy"])
    hero_name = _pick_name(rng, hero_type)
    hidden_name = _pick_name(rng, hidden_type, avoid=hero_name)
    adult_type = args.adult or rng.choice(["mother", "father", "grandmother", "grandfather"])
    return StoryParams(
        place=place_id,
        source=source_id,
        gift=gift_id,
        welcome=welcome_id,
        hero_name=hero_name,
        hero_type=hero_type,
        hidden_name=hidden_name,
        hidden_type=hidden_type,
        adult_type=adult_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        source = SOURCES[params.source]
        gift = GIFTS[params.gift]
        welcome = WELCOMES[params.welcome]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from None

    if not source_is_reasonable(place, source):
        raise StoryError(explain_source_rejection(place, source))
    if not (gift.keeps_rhythm and gift.sense >= SENSE_MIN):
        raise StoryError(explain_gift_rejection(params.gift))
    if welcome.sense < SENSE_MIN:
        raise StoryError(explain_welcome_rejection(params.welcome))

    world = tell(
        place=place,
        source=source,
        gift=gift,
        welcome=welcome,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        hidden_name=params.hidden_name,
        hidden_type=params.hidden_type,
        adult_type=params.adult_type,
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
        print(f"{len(combos)} compatible (place, source, gift, welcome) combos:\n")
        for place, source, gift, welcome in combos:
            print(f"  {place:12} {source:12} {gift:10} {welcome}")
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
            header = f"### {p.hero_name} and {p.hidden_name}: {p.source} at {p.place} ({p.gift}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
