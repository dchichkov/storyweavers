#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/corpus_twist_kindness_fairy_tale.py
==============================================================

A standalone story world for a fairy-tale domain of kindness, rumor, and a
surprising twist around a magical story book called a corpus.

Premise
-------
In a kingdom, a great magical book -- a story corpus -- loses a page. People
blame a nearby creature that looks scary from far away. A child goes to find
the page, sees the creature beside it, and first believes the rumor. Then the
child notices the creature's real trouble and offers the one kind help that
actually fits. The twist is that the feared creature was not stealing from the
corpus at all: it was trying to save the missing page.

Reasonableness constraint
-------------------------
This world refuses mismatched "kind" acts. A kindness only belongs in the story
when it truly addresses the creature's trouble:

* a thorn in a paw/foot needs a ribbon bandage
* hunger needs oat cakes
* wet pages need a drying cloth

The world model itself enforces this. Random generation selects only valid
(place, creature, trouble, help) combinations, and explicit invalid choices
raise StoryError with a clear explanation.

Run it
------
python storyworlds/worlds/gpt-5.4/corpus_twist_kindness_fairy_tale.py
python storyworlds/worlds/gpt-5.4/corpus_twist_kindness_fairy_tale.py --creature raven --trouble wet_pages
python storyworlds/worlds/gpt-5.4/corpus_twist_kindness_fairy_tale.py --help oat_cakes --trouble thorn
python storyworlds/worlds/gpt-5.4/corpus_twist_kindness_fairy_tale.py --all
python storyworlds/worlds/gpt-5.4/corpus_twist_kindness_fairy_tale.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/corpus_twist_kindness_fairy_tale.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "princess"}
        male = {"boy", "father", "man", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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
    path_text: str
    corpus_home: str
    danger_glimpse: str
    ending_light: str
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
class HeroKind:
    id: str
    title: str
    home_text: str
    carry_text: str
    trait: str
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
class CreatureCfg:
    id: str
    label: str
    article: str
    voice: str
    move_text: str
    rumor_text: str
    reveal_text: str
    trouble_ids: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)

    @property
    def phrase(self) -> str:
        return f"{self.article} {self.label}"
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
class TroubleCfg:
    id: str
    label: str
    symptom_text: str
    page_risk_text: str
    need_text: str
    effect_meter: str
    page_meter: str
    reveal_line: str
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
class HelpCfg:
    id: str
    label: str
    phrase: str
    action_text: str
    solves: set[str] = field(default_factory=set)
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
class CorpusCfg:
    id: str
    name: str
    descriptor: str
    page_name: str
    closing_line: str
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


PLACES = {
    "tower": Place(
        id="tower",
        label="the bell tower",
        path_text="a ferny path that curled toward the old bell tower",
        corpus_home="high in a round room under the bells",
        danger_glimpse="under the tower arch, where shadows made everything seem larger",
        ending_light="bell-light spilled in warm circles on the stones",
        tags={"tower"},
    ),
    "bridge": Place(
        id="bridge",
        label="the moon bridge",
        path_text="a silver path that crossed reeds toward the moon bridge",
        corpus_home="in a little reading room beside the bridge keeper's lamp",
        danger_glimpse="beneath the bridge, where river shadows shook and stretched",
        ending_light="lamp-light trembled gold over the water",
        tags={"bridge"},
    ),
    "orchard": Place(
        id="orchard",
        label="the apple orchard gate",
        path_text="a petal-strewn lane that wandered toward the orchard gate",
        corpus_home="in a painted book house beside the oldest apple tree",
        danger_glimpse="inside the gate, where leaves whispered over a dark patch of moss",
        ending_light="sunset made the apples shine like little lanterns",
        tags={"orchard"},
    ),
}

HEROES = {
    "baker_child": HeroKind(
        id="baker_child",
        title="the baker's child",
        home_text="from a warm bakery that always smelled of bread and cinnamon",
        carry_text="a small satchel with a napkin tucked inside",
        trait="gentle",
        tags={"baker"},
    ),
    "miller_child": HeroKind(
        id="miller_child",
        title="the miller's child",
        home_text="from a mill house where the wheel sang over the stream",
        carry_text="a neat bundle tied with blue thread",
        trait="thoughtful",
        tags={"miller"},
    ),
    "gardener_child": HeroKind(
        id="gardener_child",
        title="the gardener's child",
        home_text="from a cottage behind rows of marigolds and mint",
        carry_text="a wicker basket lined with soft cloth",
        trait="patient",
        tags={"gardener"},
    ),
}

CREATURES = {
    "wolf": CreatureCfg(
        id="wolf",
        label="gray wolf",
        article="a",
        voice="low",
        move_text="kept one paw lifted and did not put full weight on it",
        rumor_text="People whispered that a gray wolf had stolen shining things before.",
        reveal_text="The wolf had curled around the lost page to keep nettles from tearing it.",
        trouble_ids={"thorn", "hungry"},
        tags={"wolf"},
    ),
    "raven": CreatureCfg(
        id="raven",
        label="raven",
        article="a",
        voice="raspy",
        move_text="hopped in quick little circles and kept shaking rain from its wings",
        rumor_text="People whispered that a raven loved to snatch bright scraps and carry them off.",
        reveal_text="The raven had been pinning the lost page under its wings so the wind would not carry it away.",
        trouble_ids={"hungry", "wet_pages"},
        tags={"raven"},
    ),
    "troll": CreatureCfg(
        id="troll",
        label="bridge troll",
        article="a",
        voice="rumbly",
        move_text="sat very still and looked more tired than fierce",
        rumor_text="People whispered that a bridge troll never gave back what it held.",
        reveal_text="The troll had set the lost page on a flat stone and built a wall of pebbles around it to keep puddles off.",
        trouble_ids={"thorn", "wet_pages"},
        tags={"troll"},
    ),
}

TROUBLES = {
    "thorn": TroubleCfg(
        id="thorn",
        label="a thorn in a sore foot",
        symptom_text="a long black thorn caught deep in the creature's foot",
        page_risk_text="the page quivered beside the creature, still safe but close to the wet ground",
        need_text="The creature needed the thorn pulled and the foot wrapped before it could carry anything gently.",
        effect_meter="pain",
        page_meter="at_risk",
        reveal_line="The page is from the corpus, and I dared not leave it while I limped.",
        tags={"thorn", "kindness"},
    ),
    "hungry": TroubleCfg(
        id="hungry",
        label="an empty belly",
        symptom_text="the creature's sides looked hollow, and its eyes kept flicking from the page to the child's satchel",
        page_risk_text="the page lay under one careful claw, safe for now but trembling in the wind",
        need_text="The creature needed food, or it would grow too weak to keep guarding the page.",
        effect_meter="hunger",
        page_meter="at_risk",
        reveal_line="The page is from the corpus, and I stayed hungry so I would not leave it unguarded.",
        tags={"hungry", "kindness"},
    ),
    "wet_pages": TroubleCfg(
        id="wet_pages",
        label="rain on the lost page",
        symptom_text="rain pearls gathered on the page while the creature tried to shield it",
        page_risk_text="the ink had begun to blur at the edges",
        need_text="The creature needed dry cloth at once, or the page would lose its words.",
        effect_meter="worry",
        page_meter="wet",
        reveal_line="The page is from the corpus, and I have been trying to keep the rain from swallowing the words.",
        tags={"rain", "page"},
    ),
}

HELPS = {
    "ribbon_bandage": HelpCfg(
        id="ribbon_bandage",
        label="ribbon bandage",
        phrase="a clean ribbon bandage",
        action_text="knelt down, drew out a clean ribbon, and wrapped the sore foot with careful fingers",
        solves={"thorn"},
        tags={"bandage"},
    ),
    "oat_cakes": HelpCfg(
        id="oat_cakes",
        label="oat cakes",
        phrase="two warm oat cakes",
        action_text="opened the satchel and offered two warm oat cakes on a folded napkin",
        solves={"hungry"},
        tags={"food"},
    ),
    "drying_cloth": HelpCfg(
        id="drying_cloth",
        label="drying cloth",
        phrase="a soft drying cloth",
        action_text="spread a soft drying cloth over both hands and lifted the page away from the damp",
        solves={"wet_pages"},
        tags={"cloth"},
    ),
}

CORPUSES = {
    "moon": CorpusCfg(
        id="moon",
        name="the Moonlit Corpus",
        descriptor="a great fairy-tale corpus of silver-edged stories",
        page_name="the page of the Hare and the Hidden Star",
        closing_line="That night, the Moonlit Corpus lay whole again, and one new story seemed to glow between its covers.",
        tags={"corpus"},
    ),
    "spring": CorpusCfg(
        id="spring",
        name="the Springtime Corpus",
        descriptor="a bright fairy-tale corpus of blossom-colored stories",
        page_name="the page of the Robin and the Singing Well",
        closing_line="That evening, the Springtime Corpus rested whole again, and the room smelled faintly of rain and apple blossom.",
        tags={"corpus"},
    ),
    "hearth": CorpusCfg(
        id="hearth",
        name="the Hearthfire Corpus",
        descriptor="a deep fairy-tale corpus of ember-warm stories",
        page_name="the page of the Little Ladle and the Brave Soup Pot",
        closing_line="By supper time, the Hearthfire Corpus was whole again, and the room felt warmer than before.",
        tags={"corpus"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Elsie", "Nora", "Wren", "Clara", "Ivy"]
BOY_NAMES = ["Rowan", "Tobin", "Milo", "Perrin", "Finn", "Alden", "Hugo", "Leo"]


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
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


def _r_help_relieves(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    trouble = world.facts["trouble_cfg"]
    help_cfg = world.facts["help_cfg"]
    if creature.memes["help_offered"] < THRESHOLD:
        return out
    if trouble.id not in help_cfg.solves:
        return out
    sig = ("relief", trouble.id, help_cfg.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    creature.meters[trouble.effect_meter] = 0.0
    creature.memes["relief"] += 1
    creature.memes["trust"] += 1
    creature.memes["fear_of_child"] = 0.0
    hero = world.get("hero")
    hero.memes["fear"] = 0.0
    hero.memes["kindness"] += 1
    out.append("__relief__")
    return out


def _r_relief_reveals(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    page = world.get("page")
    if creature.memes["trust"] < THRESHOLD:
        return out
    sig = ("reveal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    creature.memes["revealed_truth"] += 1
    creature.memes["misjudged"] += 1
    page.memes["found"] += 1
    out.append("__truth__")
    return out


def _r_restore_corpus(world: World) -> list[str]:
    out: list[str] = []
    page = world.get("page")
    corpus = world.get("corpus")
    if page.memes["returned"] < THRESHOLD:
        return out
    sig = ("restore",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    corpus.meters["whole"] = 1.0
    corpus.meters["missing"] = 0.0
    corpus.memes["glow"] += 1
    hero = world.get("hero")
    creature = world.get("creature")
    hero.memes["joy"] += 1
    creature.memes["belonging"] += 1
    out.append("__restored__")
    return out


CAUSAL_RULES = [
    Rule(name="help_relieves", tag="kindness", apply=_r_help_relieves),
    Rule(name="relief_reveals", tag="twist", apply=_r_relief_reveals),
    Rule(name="restore_corpus", tag="resolution", apply=_r_restore_corpus),
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


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def valid_combo(place_id: str, creature_id: str, trouble_id: str, help_id: str) -> bool:
    if place_id not in PLACES or creature_id not in CREATURES or trouble_id not in TROUBLES or help_id not in HELPS:
        return False
    creature = CREATURES[creature_id]
    help_cfg = HELPS[help_id]
    return trouble_id in creature.trouble_ids and trouble_id in help_cfg.solves


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for creature_id, creature in CREATURES.items():
            for trouble_id in sorted(creature.trouble_ids):
                for help_id, help_cfg in HELPS.items():
                    if trouble_id in help_cfg.solves:
                        combos.append((place_id, creature_id, trouble_id, help_id))
    return sorted(combos)


def explain_rejection(creature_id: str, trouble_id: str, help_id: str) -> str:
    creature = CREATURES.get(creature_id)
    trouble = TROUBLES.get(trouble_id)
    help_cfg = HELPS.get(help_id)
    if creature is None or trouble is None or help_cfg is None:
        return "(No story: one of the chosen options is unknown.)"
    if trouble_id not in creature.trouble_ids:
        return (
            f"(No story: {creature.phrase.capitalize()} is not modeled with {trouble.label}. "
            f"Choose a trouble that fits this creature's fairy-tale situation.)"
        )
    return (
        f"(No story: {help_cfg.phrase} would not truly solve {trouble.label}. "
        f"The act of kindness must match the real need, or the twist would feel unearned.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_truth(world: World) -> dict:
    sim = world.copy()
    creature = sim.get("creature")
    page = sim.get("page")
    if creature.meters["pain"] >= THRESHOLD:
        why = "pain"
    elif creature.meters["hunger"] >= THRESHOLD:
        why = "hunger"
    elif page.meters["wet"] >= THRESHOLD:
        why = "wet"
    else:
        why = "worry"
    return {
        "looks_scary": creature.memes["frightening"] >= THRESHOLD,
        "page_missing": sim.get("corpus").meters["missing"] >= THRESHOLD,
        "why_staying": why,
    }


# ---------------------------------------------------------------------------
# Verbs / screenplay beats
# ---------------------------------------------------------------------------
def opening(world: World, hero: Entity, hero_cfg: HeroKind, corpus_cfg: CorpusCfg, elder: Entity) -> None:
    world.say(
        f"In a small kingdom, {corpus_cfg.name} rested {world.place.corpus_home}. "
        f"It was {corpus_cfg.descriptor}, and people said it remembered every gentle ending."
    )
    world.say(
        f"{hero.id}, {hero_cfg.title} {hero_cfg.home_text}, loved to hear stories from that corpus. "
        f"{hero.pronoun().capitalize()} set out with {hero_cfg.carry_text} when the kingdom bell gave one worried note."
    )
    world.say(
        f'{elder.id} said, "A page is missing from {corpus_cfg.name} -- {corpus_cfg.page_name}. '
        f'Will you walk {world.place.path_text} and see what became of it?"'
    )


def rumor(world: World, hero: Entity, creature_cfg: CreatureCfg) -> None:
    hero.memes["mission"] += 1
    hero.memes["fear"] += 1
    world.say(creature_cfg.rumor_text)
    world.say(
        f"So {hero.id} went on with a brave but careful heart, following the path toward {world.place.label}."
    )


def sighting(world: World, hero: Entity, creature: Entity, creature_cfg: CreatureCfg, trouble_cfg: TroubleCfg) -> None:
    pred = predict_truth(world)
    world.facts["prediction"] = pred
    world.say(
        f"At last {hero.id} reached {world.place.danger_glimpse} and saw {creature_cfg.phrase} beside a shining sheet of paper."
    )
    world.say(
        f"The creature {creature_cfg.move_text}. {hero.id} first thought the rumor must be true, because from far away the scene looked secret and strange."
    )
    world.say(
        f"But when {hero.pronoun()} stepped closer, {hero.pronoun()} saw {trouble_cfg.symptom_text}, and {trouble_cfg.page_risk_text}."
    )


def choose_kindness(world: World, hero: Entity, help_cfg: HelpCfg, trouble_cfg: TroubleCfg) -> None:
    hero.memes["kindness_intent"] += 1
    world.say(
        f"{hero.id} remembered that stories turn when someone notices the real hurt. {trouble_cfg.need_text}"
    )
    world.say(
        f"So instead of running away, {hero.pronoun()} {help_cfg.action_text}."
    )


def apply_help(world: World) -> None:
    creature = world.get("creature")
    creature.memes["help_offered"] += 1
    propagate(world, narrate=False)


def reveal_truth(world: World, creature_cfg: CreatureCfg, trouble_cfg: TroubleCfg, corpus_cfg: CorpusCfg) -> None:
    creature = world.get("creature")
    if creature.memes["revealed_truth"] < THRESHOLD:
        return
    world.say(
        f"The creature gave a soft {creature_cfg.voice} sound and lowered its head. "
        f'"{trouble_cfg.reveal_line}"'
    )
    world.say(creature_cfg.reveal_text)
    world.say(
        f"Then {world.get('hero').id} understood the twist at once: the feared creature had been a guardian of {corpus_cfg.page_name}, not a thief."
    )


def return_page(world: World, hero: Entity, creature_cfg: CreatureCfg, corpus_cfg: CorpusCfg) -> None:
    page = world.get("page")
    page.memes["returned"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together {hero.id} and {creature_cfg.phrase} carried the page back to {corpus_cfg.name}."
    )
    world.say(
        f"When the missing leaf slid into its place, the old binding gave a happy hush, as if the whole corpus had taken a grateful breath."
    )


def ending(world: World, hero: Entity, creature_cfg: CreatureCfg, corpus_cfg: CorpusCfg, elder: Entity) -> None:
    world.say(
        f'{elder.id} did not send the creature away. Instead {elder.pronoun()} smiled and said, "Any friend who keeps a story safe may stay for the reading."'
    )
    world.say(
        f"{world.place.ending_light}, and {hero.id} made room beside {hero.pronoun('object')} for {creature_cfg.phrase}. "
        f"{corpus_cfg.closing_line}"
    )


def tell(
    place: Place,
    hero_cfg: HeroKind,
    creature_cfg: CreatureCfg,
    trouble_cfg: TroubleCfg,
    help_cfg: HelpCfg,
    corpus_cfg: CorpusCfg,
    *,
    hero_name: str = "Lina",
    hero_gender: str = "girl",
    elder_type: str = "mother",
) -> World:
    world = World(place)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, role="elder", label="the elder"))
    creature = world.add(Entity(id="creature", kind="character", type="creature", role="creature", label=creature_cfg.label))
    corpus = world.add(Entity(id="corpus", type="book", label=corpus_cfg.name))
    page = world.add(Entity(id="page", type="page", label=corpus_cfg.page_name))

    world.facts.update(
        place=place,
        hero_cfg=hero_cfg,
        creature_cfg=creature_cfg,
        trouble_cfg=trouble_cfg,
        help_cfg=help_cfg,
        corpus_cfg=corpus_cfg,
        hero=hero,
        elder=elder,
        creature=creature,
        corpus=corpus,
        page=page,
    )

    corpus.meters["missing"] = 1.0
    corpus.meters["whole"] = 0.0
    page.meters["lost"] = 1.0
    page.meters["wet"] = 1.0 if trouble_cfg.id == "wet_pages" else 0.0
    page.meters["at_risk"] = 1.0
    creature.meters["pain"] = 1.0 if trouble_cfg.id == "thorn" else 0.0
    creature.meters["hunger"] = 1.0 if trouble_cfg.id == "hungry" else 0.0
    creature.meters["worry"] = 1.0 if trouble_cfg.id == "wet_pages" else 0.0
    creature.memes["frightening"] = 1.0
    creature.memes["help_offered"] = 0.0
    creature.memes["trust"] = 0.0
    creature.memes["revealed_truth"] = 0.0
    creature.memes["misjudged"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["kindness"] = 0.0
    hero.memes["joy"] = 0.0
    page.memes["returned"] = 0.0
    page.memes["found"] = 0.0

    opening(world, hero, hero_cfg, corpus_cfg, elder)
    world.para()
    rumor(world, hero, creature_cfg)
    sighting(world, hero, creature, creature_cfg, trouble_cfg)
    world.para()
    choose_kindness(world, hero, help_cfg, trouble_cfg)
    apply_help(world)
    reveal_truth(world, creature_cfg, trouble_cfg, corpus_cfg)
    world.para()
    return_page(world, hero, creature_cfg, corpus_cfg)
    ending(world, hero, creature_cfg, corpus_cfg, elder)

    world.facts.update(
        restored=corpus.meters["whole"] >= THRESHOLD,
        twist_revealed=creature.memes["revealed_truth"] >= THRESHOLD,
        creature_helped=creature.memes["relief"] >= THRESHOLD,
        fear_gone=hero.memes["fear"] < THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    hero_kind: str
    creature: str
    trouble: str
    help: str
    corpus: str
    hero_name: str
    hero_gender: str
    elder: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
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
    "corpus": [
        (
            "What is a corpus in this story?",
            "Here, a corpus is a big collection of stories kept together in one treasured book or set of books. It is like a story home where many tales belong."
        )
    ],
    "bandage": [
        (
            "What does a bandage do?",
            "A bandage wraps around a hurt place to help protect it. It can keep a sore foot or paw cleaner and calmer."
        )
    ],
    "food": [
        (
            "Why is food a kind help when someone is hungry?",
            "Food gives strength back to a hungry body. When someone is weak from hunger, sharing food is a direct and caring help."
        )
    ],
    "cloth": [
        (
            "Why would a soft cloth help a wet page?",
            "A soft cloth can lift water gently before the paper tears. That helps keep the page and its words safe."
        )
    ],
    "wolf": [
        (
            "Can a scary-looking animal still be gentle?",
            "Yes. Something may look scary from far away, but what matters is what it is really doing. Kindness and careful looking help us learn the truth."
        )
    ],
    "raven": [
        (
            "Why might a raven pick up shiny paper?",
            "A raven may be curious about bright things, but curiosity does not always mean stealing. Sometimes it may be guarding or moving something carefully."
        )
    ],
    "troll": [
        (
            "Are trolls always mean in fairy tales?",
            "Not always. Fairy tales often begin with a frightening guess, and then the truth turns out softer and wiser than people expected."
        )
    ],
}
KNOWLEDGE_ORDER = ["corpus", "bandage", "food", "cloth", "wolf", "raven", "troll"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    creature_cfg = f["creature_cfg"]
    corpus_cfg = f["corpus_cfg"]
    help_cfg = f["help_cfg"]
    trouble_cfg = f["trouble_cfg"]
    return [
        f'Write a fairy tale for a young child that includes the word "corpus" and turns on a twist of kindness.',
        f"Tell a gentle fairy tale where {hero.id} believes a rumor about {creature_cfg.phrase}, then notices {trouble_cfg.label} and offers {help_cfg.phrase}.",
        f"Write a story about a missing page from {corpus_cfg.name} where the frightening figure is actually helping, and the ending shows everyone making room for one another.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    creature_cfg = f["creature_cfg"]
    trouble_cfg = f["trouble_cfg"]
    help_cfg = f["help_cfg"]
    corpus_cfg = f["corpus_cfg"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {f['hero_cfg'].title}, a worried elder, and {creature_cfg.phrase} by {place.label}. They are all tied together by the missing page from {corpus_cfg.name}."
        ),
        (
            f"Why did {hero.id} go to {place.label}?",
            f"{hero.id} went because a page was missing from {corpus_cfg.name}. The elder asked {hero.pronoun('object')} to follow the path and find what had become of it."
        ),
        (
            f"What did {hero.id} think at first when {hero.pronoun()} saw the creature?",
            f"At first {hero.pronoun()} thought the rumor might be true and that the creature had taken the page. The shadows and the secret-looking scene made the creature seem guilty before {hero.pronoun()} knew the real trouble."
        ),
        (
            f"What problem did the creature really have?",
            f"The creature really had {trouble_cfg.label}. That mattered because the hurt or worry was the true reason it stayed beside the page."
        ),
        (
            f"How did {hero.id} help?",
            f"{hero.id} offered {help_cfg.phrase} and helped in the exact way the creature needed. That kindness changed the moment because it solved the real problem instead of fighting the rumor."
        ),
    ]
    if f.get("twist_revealed"):
        qa.append(
            (
                "What was the twist in the story?",
                f"The twist was that the creature was not stealing from the corpus at all. It had been protecting {corpus_cfg.page_name}, and {hero.id} only understood that after showing kindness."
            )
        )
    if f.get("restored"):
        qa.append(
            (
                f"How did the story end?",
                f"The missing page was carried back and slipped into {corpus_cfg.name}, so the corpus became whole again. In the end, the elder welcomed the creature to stay for the reading, which shows how fear changed into trust."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["corpus_cfg"].tags) | set(f["help_cfg"].tags) | set(f["creature_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="tower",
        hero_kind="baker_child",
        creature="wolf",
        trouble="thorn",
        help="ribbon_bandage",
        corpus="moon",
        hero_name="Lina",
        hero_gender="girl",
        elder="mother",
    ),
    StoryParams(
        place="bridge",
        hero_kind="miller_child",
        creature="raven",
        trouble="wet_pages",
        help="drying_cloth",
        corpus="spring",
        hero_name="Tobin",
        hero_gender="boy",
        elder="father",
    ),
    StoryParams(
        place="orchard",
        hero_kind="gardener_child",
        creature="troll",
        trouble="wet_pages",
        help="drying_cloth",
        corpus="hearth",
        hero_name="Mira",
        hero_gender="girl",
        elder="mother",
    ),
    StoryParams(
        place="bridge",
        hero_kind="baker_child",
        creature="raven",
        trouble="hungry",
        help="oat_cakes",
        corpus="moon",
        hero_name="Rowan",
        hero_gender="boy",
        elder="father",
    ),
    StoryParams(
        place="tower",
        hero_kind="gardener_child",
        creature="troll",
        trouble="thorn",
        help="ribbon_bandage",
        corpus="spring",
        hero_name="Elsie",
        hero_gender="girl",
        elder="mother",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(Place, Creature, Trouble, Help) :-
    place(Place),
    creature(Creature),
    trouble(Trouble),
    help(Help),
    can_have(Creature, Trouble),
    solves(Help, Trouble).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid, creature in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        for trouble_id in sorted(creature.trouble_ids):
            lines.append(asp.fact("can_have", cid, trouble_id))
    for tid in TROUBLES:
        lines.append(asp.fact("trouble", tid))
    for hid, help_cfg in HELPS.items():
        lines.append(asp.fact("help", hid))
        for trouble_id in sorted(help_cfg.solves):
            lines.append(asp.fact("solves", hid, trouble_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


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

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if not sample.story or "corpus" not in sample.story.lower():
            raise StoryError("smoke test story missing expected corpus-based prose")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate()/emit() passed.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world of a missing corpus page, a rumor, and a kindness-based twist."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-kind", choices=HEROES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--help", choices=HELPS)
    ap.add_argument("--corpus", choices=CORPUSES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.creature and args.trouble and args.help:
        if not valid_combo(args.place or next(iter(PLACES)), args.creature, args.trouble, args.help):
            raise StoryError(explain_rejection(args.creature, args.trouble, args.help))
    if args.creature and args.trouble and args.help is None:
        creature = CREATURES[args.creature]
        if args.trouble not in creature.trouble_ids:
            raise StoryError(explain_rejection(args.creature, args.trouble, "ribbon_bandage"))
    if args.trouble and args.help and args.creature is None:
        if args.trouble not in HELPS[args.help].solves:
            any_creature = next(iter(CREATURES))
            raise StoryError(explain_rejection(any_creature, args.trouble, args.help))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.creature is None or combo[1] == args.creature)
        and (args.trouble is None or combo[2] == args.trouble)
        and (args.help is None or combo[3] == args.help)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, creature_id, trouble_id, help_id = rng.choice(combos)
    hero_kind = args.hero_kind or rng.choice(sorted(HEROES))
    corpus_id = args.corpus or rng.choice(sorted(CORPUSES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if hero_gender == "girl" else BOY_NAMES
    hero_name = args.hero_name or rng.choice(name_pool)
    elder = args.elder or rng.choice(["mother", "father"])

    return StoryParams(
        place=place_id,
        hero_kind=hero_kind,
        creature=creature_id,
        trouble=trouble_id,
        help=help_id,
        corpus=corpus_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder=elder,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.hero_kind not in HEROES:
        raise StoryError(f"(Unknown hero kind: {params.hero_kind})")
    if params.creature not in CREATURES:
        raise StoryError(f"(Unknown creature: {params.creature})")
    if params.trouble not in TROUBLES:
        raise StoryError(f"(Unknown trouble: {params.trouble})")
    if params.help not in HELPS:
        raise StoryError(f"(Unknown help: {params.help})")
    if params.corpus not in CORPUSES:
        raise StoryError(f"(Unknown corpus: {params.corpus})")
    if not valid_combo(params.place, params.creature, params.trouble, params.help):
        raise StoryError(explain_rejection(params.creature, params.trouble, params.help))

    world = tell(
        PLACES[params.place],
        HEROES[params.hero_kind],
        CREATURES[params.creature],
        TROUBLES[params.trouble],
        HELPS[params.help],
        CORPUSES[params.corpus],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_type=params.elder,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, creature, trouble, help) combinations:\n")
        for place_id, creature_id, trouble_id, help_id in combos:
            print(f"  {place_id:8} {creature_id:8} {trouble_id:10} {help_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.hero_name}: {p.creature} with {p.trouble} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
