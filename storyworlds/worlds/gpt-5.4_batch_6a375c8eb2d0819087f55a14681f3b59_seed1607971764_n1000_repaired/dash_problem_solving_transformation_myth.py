#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dash_problem_solving_transformation_myth.py
======================================================================

A standalone story world for a small mythic domain: a child must cross a magical
barrier to carry the dawn-flame home before morning fades. A reckless dash would
fail, so the child learns to solve the problem with a humble gift. The gift
transforms into something wondrous, and the ending image proves the world has
changed for everyone.

Run it
------
    python storyworlds/worlds/gpt-5.4/dash_problem_solving_transformation_myth.py
    python storyworlds/worlds/gpt-5.4/dash_problem_solving_transformation_myth.py --obstacle river --gift seed --form vine_bridge
    python storyworlds/worlds/gpt-5.4/dash_problem_solving_transformation_myth.py --obstacle river --gift chalk
    python storyworlds/worlds/gpt-5.4/dash_problem_solving_transformation_myth.py --all
    python storyworlds/worlds/gpt-5.4/dash_problem_solving_transformation_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/dash_problem_solving_transformation_myth.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/dash_problem_solving_transformation_myth.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "goddess", "woman"}
        male = {"boy", "father", "god", "man"}
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
class Realm:
    id: str
    place: str
    sky: str
    shrine: str
    home: str
    people: str
    closing: str
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
class Obstacle:
    id: str
    label: str
    the: str
    barrier: str
    need: str
    dash_risk: str
    warning: str
    solved_text: str
    ending: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class Gift:
    id: str
    label: str
    phrase: str
    origin: str
    use_text: str
    powers: set[str] = field(default_factory=set)
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
class Form:
    id: str
    label: str
    the: str
    need: str
    emerge: str
    crossing: str
    ending: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


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


def _r_dash_danger(world: World) -> list[str]:
    hero = world.entities.get("hero")
    obstacle = world.entities.get("obstacle")
    valley = world.entities.get("valley")
    if hero is None or obstacle is None or valley is None:
        return []
    if hero.memes["dashed"] < THRESHOLD or obstacle.meters["blocked"] < THRESHOLD:
        return []
    sig = ("dash_danger", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    hero.memes["humility"] += 1
    obstacle.meters["angered"] += 1
    valley.meters["danger"] += 1
    return ["__dash__"]


def _r_transform(world: World) -> list[str]:
    hero = world.entities.get("hero")
    obstacle = world.entities.get("obstacle")
    gift = world.entities.get("gift")
    form_ent = world.entities.get("form")
    valley = world.entities.get("valley")
    if hero is None or obstacle is None or gift is None or form_ent is None or valley is None:
        return []
    if gift.meters["used"] < THRESHOLD or obstacle.meters["blocked"] < THRESHOLD:
        return []
    need = obstacle.attrs.get("need", "")
    powers = set(gift.attrs.get("powers", set()))
    form_need = form_ent.attrs.get("need", "")
    if need not in powers or form_need != need:
        return []
    sig = ("transform", gift.id, obstacle.id, form_ent.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obstacle.meters["blocked"] = 0.0
    obstacle.meters["opened"] += 1
    gift.meters["transformed"] += 1
    form_ent.meters["formed"] += 1
    valley.meters["hope"] += 1
    hero.memes["wonder"] += 1
    return ["__transform__"]


def _r_restore(world: World) -> list[str]:
    hero = world.entities.get("hero")
    valley = world.entities.get("valley")
    if hero is None or valley is None:
        return []
    if hero.meters["dawn_flame"] < THRESHOLD or hero.meters["home"] < THRESHOLD:
        return []
    sig = ("restore", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    valley.meters["light"] += 1
    valley.meters["danger"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    return ["__restore__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="dash_danger", tag="social", apply=_r_dash_danger),
    Rule(name="transform", tag="physical", apply=_r_transform),
    Rule(name="restore", tag="physical", apply=_r_restore),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


REALMS = {
    "mist_valley": Realm(
        id="mist_valley",
        place="the Valley of Mists",
        sky="silver fog under a pale sky",
        shrine="the hill of first fire",
        home="the lamp tree in the village square",
        people="the valley folk",
        closing="children no longer feared the road before sunrise",
        tags={"valley", "dawn"},
    ),
    "reed_marsh": Realm(
        id="reed_marsh",
        place="the Marsh of Singing Reeds",
        sky="blue mist woven with birdsong",
        shrine="the little ember shrine on a dry rise",
        home="the lantern pool by the reed houses",
        people="the marsh folk",
        closing="the morning path glimmered above the water forever after",
        tags={"marsh", "dawn"},
    ),
    "stone_hill": Realm(
        id="stone_hill",
        place="the Hill of Quiet Stones",
        sky="pink clouds over old standing rocks",
        shrine="the dawn shrine among the tall stones",
        home="the hearth tower at the hill village",
        people="the hill folk",
        closing="every family could walk out to greet the morning safely",
        tags={"hill", "dawn"},
    ),
}

OBSTACLES = {
    "river": Obstacle(
        id="river",
        label="river",
        the="the river",
        barrier="a black river racing too fast for small feet",
        need="grow",
        dash_risk="the current would snatch the flame and tumble the child into the cold water",
        warning="Water that runs angry does not yield to a dash.",
        solved_text="The wild current found roots to hold and a path to bear small steps.",
        ending="a green bridge arched over the once-wild water",
        tags={"river", "water"},
    ),
    "thorn_wall": Obstacle(
        id="thorn_wall",
        label="thorn wall",
        the="the thorn wall",
        barrier="a wall of moon-thorns tangled across the path",
        need="soothe",
        dash_risk="the thorns would tear clothes, spill the flame, and catch little hands",
        warning="Sharp things grow sharper when they are struck in haste.",
        solved_text="The thorns heard gentleness, loosened their knots, and opened into bloom.",
        ending="a flowered arch stood where the bramble had snarled",
        tags={"thorns", "flowers"},
    ),
    "stone_gate": Obstacle(
        id="stone_gate",
        label="stone gate",
        the="the stone gate",
        barrier="an ancient stone gate with no handle and no keyhole",
        need="mark",
        dash_risk="the child would only bruise shoulder and knee against the sleeping rock",
        warning="Old stone opens to a true sign, not to a hurried shoulder.",
        solved_text="The gate remembered the old sign and folded itself apart like a door of dawn.",
        ending="a bright door of light rested inside the old stones",
        tags={"stone", "gate"},
    ),
}

GIFTS = {
    "seed": Gift(
        id="seed",
        label="seed",
        phrase="a moon-bright seed",
        origin="from the oldest fig bowl in the shrine keeper's house",
        use_text="pressed the seed into a crack beside the path and whispered for roots to remember the earth",
        powers={"grow"},
        tags={"seed", "plant"},
    ),
    "flute": Gift(
        id="flute",
        label="reed flute",
        phrase="a hollow reed flute",
        origin="cut from the first singing reed of spring",
        use_text="lifted the flute and played the smallest, softest tune she knew",
        powers={"soothe"},
        tags={"flute", "music"},
    ),
    "chalk": Gift(
        id="chalk",
        label="white chalk",
        phrase="a stick of white chalk",
        origin="broken from a cliff where lightning once kissed the stone",
        use_text="drew the old sun-sign on the sleeping rock with a careful hand",
        powers={"mark"},
        tags={"chalk", "sign"},
    ),
}

FORMS = {
    "vine_bridge": Form(
        id="vine_bridge",
        label="vine bridge",
        the="the vine bridge",
        need="grow",
        emerge="green roots leapt, twined, and rose into a living bridge",
        crossing="Its leaves held the dawn-flame steady while the child crossed.",
        ending="The vine bridge stayed there, leaf-bright and gentle",
        tags={"bridge", "plant"},
    ),
    "blossom_arch": Form(
        id="blossom_arch",
        label="blossom arch",
        the="the blossom arch",
        need="soothe",
        emerge="the thorns bent down, flowers burst open, and a blossom arch appeared",
        crossing="Petals drifted around the dawn-flame without touching it.",
        ending="The blossom arch kept blooming beside the road",
        tags={"flowers", "arch"},
    ),
    "sun_door": Form(
        id="sun_door",
        label="sun door",
        the="the sun door",
        need="mark",
        emerge="lines of gold ran through the stone, and a shining sun door opened in its middle",
        crossing="Warm light from the doorway guarded the small flame all the way through.",
        ending="The sun door opened each morning at the first true sign",
        tags={"door", "light"},
    ),
}

GIRL_NAMES = ["Iris", "Nila", "Mira", "Tala", "Suri", "Anya", "Luma", "Ena"]
BOY_NAMES = ["Aren", "Tarin", "Milo", "Solen", "Kian", "Daro", "Remy", "Orin"]
TRAITS = ["patient", "hasty", "careful", "bright"]


def valid_combo(obstacle: Obstacle, gift: Gift, form: Form) -> bool:
    return obstacle.need in gift.powers and form.need == obstacle.need


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for realm_id in REALMS:
        for obstacle_id, obstacle in OBSTACLES.items():
            for gift_id, gift in GIFTS.items():
                for form_id, form in FORMS.items():
                    if valid_combo(obstacle, gift, form):
                        out.append((realm_id, obstacle_id, gift_id, form_id))
    return out


@dataclass
class StoryParams:
    realm: str
    obstacle: str
    gift: str
    form: str
    hero_name: str
    hero_gender: str
    guide_type: str
    trait: str
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


def predict_dash(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.memes["dashed"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("valley").meters["danger"],
        "fear": hero.memes["fear"],
        "angered": sim.get("obstacle").meters["angered"],
    }


def introduce(world: World, realm: Realm, hero: Entity) -> None:
    world.say(
        f"In the old days, when {realm.place} still listened to songs and signs, "
        f"there lived a little child named {hero.id}."
    )
    world.say(
        f"{realm.people.capitalize()} said the dawn-flame must be carried each morning "
        f"from {realm.shrine} to {realm.home}, or the day would wake dim and cold."
    )


def trouble(world: World, realm: Realm, hero: Entity) -> None:
    hero.memes["duty"] += 1
    world.say(
        f"One morning the sky was only {realm.sky}, and no grown-up had yet climbed the path. "
        f"So {hero.id} took the tiny clay lamp and promised to bring the first fire home."
    )


def meet_barrier(world: World, obstacle: Obstacle) -> None:
    world.say(
        f"But halfway up the sacred road stood {obstacle.barrier}."
    )


def guide_warning(world: World, guide: Entity, hero: Entity, obstacle: Obstacle, gift: Gift) -> None:
    pred = predict_dash(world)
    world.facts["predicted_danger"] = pred["danger"]
    guide.memes["care"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"From the roadside shrine, {guide.label} called softly, "
        f'"Do not dash at it, little one. {obstacle.warning} If you run, {obstacle.dash_risk}."'
    )
    world.say(
        f"Instead, {guide.pronoun()} offered {gift.phrase}, {gift.origin}, and told "
        f"{hero.id} to use it with a quiet heart."
    )


def dash_attempt(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.memes["dashed"] += 1
    hero.memes["pride"] += 1
    propagate(world, narrate=False)
    world.say(
        f"For one breath {hero.id} thought, I can dash past before the path grows worse."
    )
    world.say(
        f"{hero.pronoun().capitalize()} ran two quick steps toward {obstacle.the}, "
        f"and the danger answered at once."
    )
    if obstacle.id == "river":
        world.say("Spray slapped the lamp, and the child skidded back from the edge.")
    elif obstacle.id == "thorn_wall":
        world.say("The moon-thorns hissed together, and one sharp branch caught at the child's sleeve.")
    else:
        world.say("The stone gave back a hard thud, and the little flame trembled in its bowl.")
    world.say(
        f"{hero.id} stopped, hugging the lamp close. The old warning felt true now."
    )


def choose_patience(world: World, hero: Entity) -> None:
    hero.memes["patience"] += 1
    world.say(
        f"{hero.id} did not run. {hero.pronoun().capitalize()} stood very still, "
        f"feeling how small the clay lamp was and how careful {hero.pronoun()} had to be."
    )


def use_gift(world: World, hero: Entity, gift: Gift) -> None:
    ent = world.get("gift")
    ent.meters["used"] += 1
    hero.memes["wisdom"] += 1
    world.say(
        f"Then {hero.id} {gift.use_text}."
    )


def transformation(world: World, obstacle: Obstacle, form: Form) -> None:
    propagate(world, narrate=False)
    world.say(
        f"At once, {form.emerge}. {obstacle.solved_text}"
    )
    world.say(form.crossing)


def take_flame(world: World, hero: Entity, realm: Realm) -> None:
    hero.meters["at_shrine"] += 1
    hero.meters["dawn_flame"] += 1
    world.say(
        f"Beyond the opening path lay {realm.shrine}. There {hero.id} touched the clay lamp "
        f"to the waiting ember, and a clean dawn-flame bloomed inside it."
    )


def return_home(world: World, hero: Entity, realm: Realm) -> None:
    hero.meters["home"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} carried the bright little fire back to {realm.home}, and the village lamps "
        f"woke one by one like yellow flowers."
    )


def blessing(world: World, guide: Entity, hero: Entity, form: Form, realm: Realm) -> None:
    hero.memes["gratitude"] += 1
    world.say(
        f'{guide.label.capitalize()} smiled. "You were not saved by speed," {guide.pronoun()} said. '
        f'"You were saved by seeing what the road needed."'
    )
    world.say(
        f"{form.ending}, and {realm.closing}."
    )


def tell(
    realm: Realm,
    obstacle_cfg: Obstacle,
    gift_cfg: Gift,
    form_cfg: Form,
    hero_name: str = "Iris",
    hero_gender: str = "girl",
    guide_type: str = "goddess",
    trait: str = "patient",
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[trait],
        attrs={},
    ))
    guide_label = "the dawn goddess" if guide_type == "goddess" else "the shrine keeper"
    guide_entity_type = "goddess" if guide_type == "goddess" else "woman"
    guide = world.add(Entity(
        id="guide",
        kind="character",
        type=guide_entity_type,
        label=guide_label,
        role="guide",
        attrs={},
    ))
    valley = world.add(Entity(
        id="valley",
        type="place",
        label=realm.place,
        attrs={},
    ))
    obstacle = world.add(Entity(
        id="obstacle",
        type="barrier",
        label=obstacle_cfg.label,
        attrs={"need": obstacle_cfg.need},
    ))
    gift = world.add(Entity(
        id="gift",
        type="gift",
        label=gift_cfg.label,
        attrs={"powers": set(gift_cfg.powers)},
    ))
    form = world.add(Entity(
        id="form",
        type="wonder",
        label=form_cfg.label,
        attrs={"need": form_cfg.need},
    ))

    obstacle.meters["blocked"] = 1.0
    hero.meters["dawn_flame"] = 0.0
    hero.meters["home"] = 0.0
    hero.meters["at_shrine"] = 0.0
    valley.meters["light"] = 0.0
    valley.meters["danger"] = 0.0
    valley.meters["hope"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["wonder"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["patience"] = 0.0
    hero.memes["dashed"] = 0.0
    hero.memes["wisdom"] = 0.0
    guide.memes["care"] = 0.0
    gift.meters["used"] = 0.0
    gift.meters["transformed"] = 0.0
    form.meters["formed"] = 0.0

    world.facts.update(
        realm=realm,
        obstacle_cfg=obstacle_cfg,
        gift_cfg=gift_cfg,
        form_cfg=form_cfg,
        hero=hero,
        guide=guide,
        attempted_dash=False,
    )

    introduce(world, realm, hero)
    trouble(world, realm, hero)

    world.para()
    meet_barrier(world, obstacle_cfg)
    guide_warning(world, guide, hero, obstacle_cfg, gift_cfg)

    world.para()
    if trait == "hasty":
        world.facts["attempted_dash"] = True
        dash_attempt(world, hero, obstacle_cfg)
    else:
        choose_patience(world, hero)

    use_gift(world, hero, gift_cfg)
    transformation(world, obstacle_cfg, form_cfg)

    world.para()
    take_flame(world, hero, realm)
    return_home(world, hero, realm)
    blessing(world, guide, hero, form_cfg, realm)

    world.facts.update(
        solved=obstacle.meters["blocked"] < THRESHOLD,
        restored=valley.meters["light"] >= THRESHOLD,
        outcome="learned" if trait == "hasty" else "steady",
        transformed=form.meters["formed"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "river": [
        (
            "Why is it dangerous to dash through a fast river?",
            "Fast water can push your feet out from under you and carry things away. "
            "That is why people cross safely instead of rushing straight in."
        )
    ],
    "thorns": [
        (
            "Why can thorns hurt you?",
            "Thorns are sharp parts of some plants that protect the plant. "
            "They can scratch skin and catch on clothes."
        )
    ],
    "stone": [
        (
            "Why can't you open a stone gate by bumping into it?",
            "Stone is hard and heavy, so pushing it the wrong way can hurt you without moving it. "
            "You need the right opening, tool, or sign."
        )
    ],
    "seed": [
        (
            "What does a seed need to grow?",
            "A seed needs the right place, water, and time to start growing. "
            "Inside it is a tiny beginning of a plant."
        )
    ],
    "music": [
        (
            "Why can soft music feel calming?",
            "Soft music can help bodies and minds slow down. "
            "Gentle sounds often make a place feel peaceful."
        )
    ],
    "sign": [
        (
            "What is a sign?",
            "A sign is a mark that means something. "
            "People use signs to remember, point, or open the right way to do something."
        )
    ],
    "bridge": [
        (
            "What is a bridge for?",
            "A bridge helps people cross over something like water or a gap. "
            "It makes a safer path from one side to the other."
        )
    ],
    "flowers": [
        (
            "Why do flowers open?",
            "Flowers open as part of how plants grow and make seeds. "
            "Many flowers open wider in warmth and light."
        )
    ],
    "door": [
        (
            "What does a door do?",
            "A door makes an opening you can pass through and close again. "
            "It turns a wall into a way through."
        )
    ],
    "dawn": [
        (
            "What is dawn?",
            "Dawn is the time when night is ending and morning light first appears. "
            "The sky often grows pale before the sun is fully up."
        )
    ],
}
KNOWLEDGE_ORDER = ["dawn", "river", "thorns", "stone", "seed", "music", "sign", "bridge", "flowers", "door"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    obstacle = f["obstacle_cfg"]
    gift = f["gift_cfg"]
    form = f["form_cfg"]
    realm = f["realm"]
    if f["attempted_dash"]:
        return [
            f'Write a short child-facing myth that includes the word "dash", where a child must carry dawn fire through {obstacle.the} in {realm.place}.',
            f"Tell a mythic story where {hero.label} first tries to dash past {obstacle.the}, then solves the problem with {gift.phrase}, which transforms into {form.the}.",
            f"Write a gentle myth about haste turning into wisdom, ending with {form.the} helping the whole village."
        ]
    return [
        f'Write a short child-facing myth that includes the word "dash", where a child refuses to dash and instead solves a dawn-time problem in {realm.place}.',
        f"Tell a mythic story where {hero.label} uses {gift.phrase} to change {obstacle.the} into {form.the}.",
        f"Write a simple myth about careful thinking, transformation, and a village made safer by one brave child."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    realm = f["realm"]
    obstacle = f["obstacle_cfg"]
    gift = f["gift_cfg"]
    form = f["form_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child in {realm.place}, and {guide.label}, who gives careful help. "
            f"The story follows how {hero.label} carries dawn fire home for the village."
        ),
        (
            "What problem did the child face?",
            f"{hero.label} had to pass {obstacle.the} on the road to the shrine. "
            f"That barrier stood between the village and the dawn-flame."
        ),
        (
            "Why was a dash not the right answer?",
            f"A dash would not solve the problem because {obstacle.dash_risk}. "
            f"The warning mattered because speed would have made the danger worse, not better."
        ),
    ]
    if f["attempted_dash"]:
        qa.append(
            (
                f"What happened when {hero.label} tried to dash?",
                f"{hero.label} only got close enough to feel the danger answer back, so {hero.pronoun()} stopped and held the lamp tightly. "
                f"That moment taught {hero.pronoun('object')} that the road needed care instead of speed."
            )
        )
    qa.append(
        (
            f"How did {hero.label} solve the problem?",
            f"{hero.label} used {gift.phrase} in the way the road needed, and that changed {obstacle.the} into {form.the}. "
            f"The transformation made a safe path where there had been a barrier."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"{hero.label} brought the dawn-flame back to {realm.home}, and the village lights woke again. "
            f"At the end, {form.ending.lower()}, showing that the wise solution lasted after the journey was over."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"dawn"} | set(f["obstacle_cfg"].tags) | set(f["gift_cfg"].tags) | set(f["form_cfg"].tags)
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {}
            for key, value in ent.attrs.items():
                if isinstance(value, set):
                    shown[key] = sorted(value)
                else:
                    shown[key] = value
            bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(obstacle: Obstacle, gift: Gift, form: Form) -> str:
    if obstacle.need not in gift.powers:
        return (
            f"(No story: {gift.phrase} does not fit {obstacle.the}. "
            f"{obstacle.the.capitalize()} needs a gift that can {obstacle.need}, "
            f"so this problem would not honestly transform.)"
        )
    if form.need != obstacle.need:
        return (
            f"(No story: {form.the} is the wrong kind of transformation for {obstacle.the}. "
            f"The transformed form must answer the barrier's real need.)"
        )
    return "(No story: this combination does not make a coherent myth.)"


def outcome_of(params: StoryParams) -> str:
    return "learned" if params.trait == "hasty" else "steady"


ASP_RULES = r"""
valid(R, O, G, F) :- realm(R), obstacle(O), gift(G), form(F),
                     needs(O, N), power(G, N), form_need(F, N).

outcome(learned) :- trait(hasty).
outcome(steady)  :- trait(T), T != hasty.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for realm_id in REALMS:
        lines.append(asp.fact("realm", realm_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("needs", obstacle_id, obstacle.need))
    for gift_id, gift in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        for power in sorted(gift.powers):
            lines.append(asp.fact("power", gift_id, power))
    for form_id, form in FORMS.items():
        lines.append(asp.fact("form", form_id))
        lines.append(asp.fact("form_need", form_id, form.need))
    for trait in sorted(set(TRAITS)):
        lines.append(asp.fact("known_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("trait", params.trait)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        realm="mist_valley",
        obstacle="river",
        gift="seed",
        form="vine_bridge",
        hero_name="Iris",
        hero_gender="girl",
        guide_type="goddess",
        trait="patient",
    ),
    StoryParams(
        realm="reed_marsh",
        obstacle="thorn_wall",
        gift="flute",
        form="blossom_arch",
        hero_name="Solen",
        hero_gender="boy",
        guide_type="keeper",
        trait="hasty",
    ),
    StoryParams(
        realm="stone_hill",
        obstacle="stone_gate",
        gift="chalk",
        form="sun_door",
        hero_name="Mira",
        hero_gender="girl",
        guide_type="goddess",
        trait="careful",
    ),
    StoryParams(
        realm="mist_valley",
        obstacle="thorn_wall",
        gift="flute",
        form="blossom_arch",
        hero_name="Aren",
        hero_gender="boy",
        guide_type="keeper",
        trait="hasty",
    ),
    StoryParams(
        realm="reed_marsh",
        obstacle="stone_gate",
        gift="chalk",
        form="sun_door",
        hero_name="Nila",
        hero_gender="girl",
        guide_type="goddess",
        trait="bright",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic storyworld: a child must solve a dawn-road problem by wisdom, not a dash."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--form", choices=FORMS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--guide-type", choices=["goddess", "keeper"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid mythic combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.gift and args.form:
        if not valid_combo(OBSTACLES[args.obstacle], GIFTS[args.gift], FORMS[args.form]):
            raise StoryError(explain_rejection(OBSTACLES[args.obstacle], GIFTS[args.gift], FORMS[args.form]))

    combos = [
        combo for combo in valid_combos()
        if (args.realm is None or combo[0] == args.realm)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.gift is None or combo[2] == args.gift)
        and (args.form is None or combo[3] == args.form)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    realm_id, obstacle_id, gift_id, form_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    guide_type = args.guide_type or rng.choice(["goddess", "keeper"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        realm=realm_id,
        obstacle=obstacle_id,
        gift=gift_id,
        form=form_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        guide_type=guide_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.realm not in REALMS:
        raise StoryError(f"(Unknown realm: {params.realm})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift: {params.gift})")
    if params.form not in FORMS:
        raise StoryError(f"(Unknown form: {params.form})")
    if params.hero_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown hero gender: {params.hero_gender})")
    if params.guide_type not in {"goddess", "keeper"}:
        raise StoryError(f"(Unknown guide type: {params.guide_type})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")

    obstacle = OBSTACLES[params.obstacle]
    gift = GIFTS[params.gift]
    form = FORMS[params.form]
    if not valid_combo(obstacle, gift, form):
        raise StoryError(explain_rejection(obstacle, gift, form))

    world = tell(
        realm=REALMS[params.realm],
        obstacle_cfg=obstacle,
        gift_cfg=gift,
        form_cfg=form,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        guide_type=params.guide_type,
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


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            args = build_parser().parse_args([])
            p = resolve_params(args, random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    mismatches = 0
    for case in cases:
        if asp_outcome(case) != outcome_of(case):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: ASP outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcome labels differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="SMOKE")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (realm, obstacle, gift, form) combos:\n")
        for realm_id, obstacle_id, gift_id, form_id in combos:
            print(f"  {realm_id:11} {obstacle_id:11} {gift_id:7} {form_id}")
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
            header = f"### {p.hero_name}: {p.obstacle} -> {p.form} in {p.realm}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
