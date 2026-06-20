#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tendency_inner_monologue_myth.py
===============================================================

A standalone tiny story world for a mythic, child-facing tale about a child's
tendency to follow a tempting call, the quiet tug of an inner monologue, and a
safer choice that changes the ending.

The world keeps the Storyweavers contract:
- typed entities with physical meters and emotional memes
- a forward-chained causal engine
- a Python reasonableness gate and inline ASP twin
- three QA sets grounded in simulated state
- direct support for default, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    scene: str
    danger_image: str
    safe_image: str
    winds: bool = False
    deep_water: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Temptation:
    id: str
    label: str
    lure: str
    phrase: str
    where: str
    makes_trouble: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Guide:
    id: str
    label: str
    counsel: str
    rescue: str
    rescue_fail: str
    gift: str
    power: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_tide_rises(world: World) -> list[str]:
    out: list[str] = []
    tide = world.get("tide")
    if tide.meters["restless"] < THRESHOLD:
        return out
    sig = ("tide",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in world.characters():
        e.memes["unease"] += 1
    world.get("shore").meters["danger"] += 1
    out.append("__tide__")
    return out


def _r_inner_monologue(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    guide = world.get("guide")
    if hero.memes["thinking"] < THRESHOLD or hero.memes["tendency"] < THRESHOLD:
        return out
    sig = ("think",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["resolve"] += 1
    guide.memes["hope"] += 1
    out.append("__thought__")
    return out


CAUSAL_RULES = [
    Rule("tide", "physical", _r_tide_rises),
    Rule("thought", "social", _r_inner_monologue),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def tide_severity(place: Place, delay: int) -> int:
    return (2 if place.deep_water else 1) + delay + (1 if place.winds else 0)


def reason_gate(temptation: Temptation, place: Place) -> bool:
    return temptation.makes_trouble and place.deep_water


def can_guide(guide: Guide, place: Place, delay: int) -> bool:
    return guide.power >= tide_severity(place, delay)


def predict(world: World, place_id: str, delay: int) -> dict:
    sim = world.copy()
    sim.get("tide").meters["restless"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get(place_id).meters["danger"],
        "unease": sum(e.memes["unease"] for e in sim.characters()),
        "severity": tide_severity(PLACES[place_id], delay),
    }


def setup(world: World, hero: Entity, guide: Entity, place: Place) -> None:
    world.say(
        f"Long ago, {hero.id} lived beside {place.label}. "
        f"{place.scene}"
    )
    world.say(
        f"{guide.id} walked with {hero.id} to the water, because the old road was part of "
        f"their days and their prayers."
    )


def tempt(world: World, hero: Entity, temptation: Temptation) -> None:
    hero.memes["tendency"] += 1
    world.say(
        f"Near the bank, {temptation.phrase} waited like a secret. "
        f"{hero.id}'s tendency was to follow such things, and {hero.id} felt it tug."
    )
    world.say(f'Inside, {hero.id} thought, "{temptation.lure}"')


def warn(world: World, guide: Entity, hero: Entity, temptation: Temptation, place: Place) -> None:
    pred = predict(world, place.id, int(world.facts.get("delay", 0)))
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'"{temptation.label.capitalize()} can pull you where the stones are slick," '
        f'{guide.id} said. "{guide.counsel}"'
    )


def step_toward(world: World, hero: Entity, temptation: Temptation) -> None:
    hero.memes["thinking"] += 1
    hero.meters["near_water"] += 1
    world.say(
        f"{hero.id} took one step toward the shining thing, then paused. "
        f"That little pause was the inner monologue speaking up."
    )


def choose_safely(world: World, hero: Entity, guide: Entity, gift: Guide) -> None:
    hero.memes["resolve"] += 1
    hero.memes["joy"] += 1
    guide.memes["joy"] += 1
    world.say(
        f'{hero.id} breathed in and answered the thought with a better one: "{gift.gift}"'
    )
    world.say(
        f"So {hero.id} chose the safer path, and {guide.id} smiled as if a star had been "
        f"lit inside the chest."
    )


def accident(world: World, place: Place, temptation: Temptation) -> None:
    world.get("tide").meters["restless"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The water rose with a sudden hush. A small wave slid over the stones and made "
        f"the edge of {place.label} slippery."
    )


def rescue(world: World, guide: Entity, place: Place, gift: Guide) -> None:
    world.get("shore").meters["danger"] = 0
    world.say(
        f"{guide.id} pulled {gift.rescue} and guided the child back with steady hands. "
        f"{gift.rescue}"
    )


def lesson(world: World, guide: Entity, hero: Entity, temptation: Temptation) -> None:
    hero.memes["fear"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"Then {guide.id} bent low and said, "
        f'"{temptation.label} is not for chasing when the sea is waking. '
        f'Listen to the quiet thought that keeps you safe."'
    )
    world.say(f"{hero.id} promised to remember that tendency and to choose with care.")


def ending_safe(world: World, hero: Entity, guide: Entity, place: Place, gift: Guide) -> None:
    world.say(
        f"Afterward, {hero.id} and {guide.id} stood where the shore was calm again. "
        f"{place.safe_image}"
    )


def ending_rescued(world: World, hero: Entity, guide: Entity, place: Place, gift: Guide) -> None:
    world.say(
        f"When the danger passed, the river shone like polished glass, and "
        f"{gift.gift} glimmered in {hero.id}'s hands."
    )


def tell(place: Place, temptation: Temptation, guide_def: Guide, delay: int = 0,
         hero_name: str = "Ari", hero_gender: str = "boy",
         guide_name: str = "Mara", guide_gender: str = "girl") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender,
                            role="hero"))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_gender,
                             role="guide"))
    shore = world.add(Entity(id="shore", type="place", label=place.label))
    tide = world.add(Entity(id="tide", type="force", label="the tide"))
    hero.memes["tendency"] = 1.0
    guide.memes["wisdom"] = 1.0
    world.facts["delay"] = delay

    setup(world, hero, guide, place)
    world.para()
    tempt(world, hero, temptation)
    warn(world, guide, hero, temptation, place)
    step_toward(world, hero, temptation)

    if reason_gate(temptation, place):
        world.para()
        accident(world, place, temptation)
        if can_guide(guide_def, place, delay):
            rescue(world, guide, place, guide_def)
            lesson(world, guide, hero, temptation)
            world.para()
            ending_rescued(world, hero, guide, place, guide_def)
            outcome = "rescued"
        else:
            world.say(
                f"The waves were too quick for a simple rescue, but the two of them still "
                f"got to higher ground."
            )
            lesson(world, guide, hero, temptation)
            outcome = "rough"
    else:
        world.para()
        choose_safely(world, hero, guide, guide_def)
        world.para()
        ending_safe(world, hero, guide, place, guide_def)
        outcome = "avoided"

    world.facts.update(
        hero=hero, guide=guide, place=place, temptation=temptation,
        guide_def=guide_def, shore=shore, tide=tide, outcome=outcome
    )
    return world


PLACES = {
    "riverbank": Place(
        "riverbank", "the riverbank",
        "The river moved in long silver ribbons, and reeds bowed like old listeners.",
        "The water lapped higher against the stones, making the path slick.",
        "By dawn, the river was calm again, and the stones glittered in peace.",
        winds=False, deep_water=True,
    ),
    "seashore": Place(
        "seashore", "the seashore",
        "The sea hummed under the moon, and every shell seemed to hold a memory.",
        "The tide crept in with a whisper, wetting the path one step at a time.",
        "When the tide turned back, the shells lay bright and harmless on the sand.",
        winds=True, deep_water=True,
    ),
    "spring": Place(
        "spring", "the spring",
        "Clear water rose from the earth, and birds drank from the little pool.",
        "The pool shivered, and a slick ring of water spread across the stones.",
        "Later, the spring looked like a little mirror, quiet and safe.",
        winds=False, deep_water=False,
    ),
}

TANTALIZATIONS = {
    "moonstone": Temptation(
        "moonstone", "the moonstone",
        "take the moonstone",
        "a moonstone gleamed on the ledge",
        "the ledge",
        makes_trouble=True,
        tags={"stone", "moon", "glimmer"},
    ),
    "reed_flute": Temptation(
        "reed_flute", "the reed flute",
        "blow the reed flute",
        "a reed flute sang where the wind touched it",
        "the reeds",
        makes_trouble=True,
        tags={"music", "wind"},
    ),
    "silver_fish": Temptation(
        "silver_fish", "the silver fish",
        "follow the silver fish",
        "a silver fish flashed just beyond the stones",
        "the water",
        makes_trouble=True,
        tags={"fish", "glimmer"},
    ),
}

GIFTS = {
    "lantern": Guide(
        "lantern", "lantern",
        "keep your feet on the dry stones and watch the water with me",
        "held a lantern high and guided the child home",
        "held out an empty hand and waited for the child to come back",
        "a little lantern",
        power=4,
        tags={"light"},
    ),
    "rope": Guide(
        "rope", "rope",
        "hold the rope and stay with me",
        "tied a rope around the child's wrist and guided them back",
        "tied a rope to the post and watched the child return",
        "a braided rope",
        power=3,
        tags={"rope"},
    ),
    "song": Guide(
        "song", "song",
        "listen to the still place inside you",
        "sang softly and led the child away from the lip of the water",
        "sang softly until the child stepped back",
        "a quiet song",
        power=2,
        tags={"song"},
    ),
}



@dataclass
class StoryParams:
    place: str
    temptation: str
    guide: str
    delay: int = 0
    hero_name: str = "Ari"
    hero_gender: str = "boy"
    guide_name: str = "Mara"
    guide_gender: str = "girl"
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")

CURATED = [
    StoryParams("riverbank", "moonstone", "lantern", 0, "Ari", "boy", "Mara", "girl"),
    StoryParams("seashore", "silver_fish", "rope", 1, "Lina", "girl", "Hale", "boy"),
    StoryParams("spring", "reed_flute", "song", 0, "Niko", "boy", "Ira", "girl"),
]



def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for tid, temp in TANTALIZATIONS.items():
            for gid, guide in GIFTS.items():
                if reason_gate(temp, place):
                    combos.append((pid, tid, gid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    temp = f["temptation"]
    place = f["place"]
    return [
        f'Write a myth-like story for a child where {hero.id} has a tendency to '
        f'follow "{temp.label}" near {place.label}, but listens to an inner monologue and '
        f'chooses safety.',
        f'Tell a small myth about {hero.id} and {guide.id} at {place.label}, with a quiet thought '
        f'inside the hero\'s head and a ending that feels wise.',
        f'Write a story that includes the word "tendency" and ends with a calm, '
        f'shining image of the shore or river after a risky choice.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, guide, place, temp = f["hero"], f["guide"], f["place"], f["temptation"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {guide.id}, who stood beside {place.label}. The story follows "
         f"{hero.id}'s tendency and the quiet way {guide.id} answered it."),
        ("What did the child want to do?",
         f"{hero.id} wanted to {temp.lure}. That was the tempting choice that started the trouble."),
        ("What was the inner monologue?",
         f"{hero.id} thought about the shining thing and then paused. The inner monologue "
         f"was the small, private voice that helped {hero.id} choose more carefully."),
    ]
    outcome = f["outcome"]
    if outcome == "avoided":
        qa.append((
            "How did the story turn out?",
            f"{hero.id} stopped and chose the safer path before anything went wrong. "
            f"The ending is calm because the tendency was answered before the tide became dangerous."
        ))
    elif outcome == "rescued":
        qa.append((
            "How was the danger handled?",
            f"{guide.id} pulled {guide_def_label(f)} and guided {hero.id} back. "
            f"The help came quickly enough to keep everyone safe."
        ))
        qa.append((
            "What did the child learn?",
            f"{hero.id} learned that a tendency is not the same as a choice. "
            f"Listening to the inner monologue helped {hero.id} choose the wiser thing."
        ))
    else:
        qa.append((
            "What changed after the risky step?",
            f"The water rose and made the stones slick, so the child had to move back to higher ground. "
            f"That sudden change forced everyone to be careful."
        ))
    return qa


def guide_def_label(facts: dict) -> str:
    return facts["guide_def"].gift


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["temptation"].tags)
    tags.add("tendency")
    if f.get("outcome") == "rescued":
        tags.add(f["guide_def"].id)
    return {
        "stone": [("What is a stone?",
                  "A stone is a hard piece of rock. Stones can be safe to hold, but some places near water are slippery.")],
        "moon": [("Why do people in myths look at the moon?",
                 "In myths, the moon is often a sign of quiet night, guidance, or wonder. It can make a story feel ancient and magical.")],
        "tendency": [("What is a tendency?",
                      "A tendency is a pattern of what someone often does or wants to do. It does not have to be followed every time.")],
        "water": [("Why can water on stones be dangerous?",
                   "Water can make stones slippery, so feet may slide if a person does not move carefully.")],
        "light": [("Why can a lantern help in a story?",
                   "A lantern gives light without needing the child to guess in the dark. It helps people see where to walk.")],
        "song": [("Why do stories use songs?",
                  "Songs can guide a mood or lead a traveler gently. In a myth, a song may feel like a helper or a warning.")],
    } if False else _world_knowledge(world)


def _world_knowledge(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["temptation"].tags)
    tags.add("tendency")
    if f.get("outcome") in {"rescued", "avoided"}:
        tags.add(f["guide_def"].id)
    known = {
        "stone": [("What is a stone?",
                  "A stone is a hard piece of rock. Stones can be safe to hold, but some places near water are slippery.")],
        "moon": [("Why do people in myths look at the moon?",
                 "In myths, the moon is often a sign of quiet night, guidance, or wonder. It can make a story feel ancient and magical.")],
        "tendency": [("What is a tendency?",
                      "A tendency is a pattern of what someone often does or wants to do. It does not have to be followed every time.")],
        "water": [("Why can water on stones be dangerous?",
                   "Water can make stones slippery, so feet may slide if a person does not move carefully.")],
        "light": [("Why can a lantern help in a story?",
                   "A lantern gives light without needing the child to guess in the dark. It helps people see where to walk.")],
        "song": [("Why do stories use songs?",
                  "Songs can guide a mood or lead a traveler gently. In a myth, a song may feel like a helper or a warning.")],
    }
    order = ["stone", "moon", "tendency", "water", "light", "song"]
    out = []
    for k in order:
        if k in tags:
            out.extend(known[k])
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
dangerous(P, T) :- place(P), deep_water(P), temptation(T), makes_trouble(T).
restless_tide(P) :- place(P), deep_water(P).
thoughtful(H) :- hero(H), tendency(H, X), X >= 1.
resolved(H) :- hero(H), thought(H).
outcome(avoided) :- not disturbed, chosen_safely.
outcome(rescued) :- disturbed, guide_power(P), severity(S), P >= S.
outcome(rough) :- disturbed, guide_power(P), severity(S), P < S.
severity(S) :- place(P), tide_severity(P, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.deep_water:
            lines.append(asp.fact("deep_water", pid))
        if p.winds:
            lines.append(asp.fact("winds", pid))
        lines.append(asp.fact("tide_severity", pid, (2 if p.deep_water else 1) + (1 if p.winds else 0)))
    for tid, t in TANTALIZATIONS.items():
        lines.append(asp.fact("temptation", tid))
        if t.makes_trouble:
            lines.append(asp.fact("makes_trouble", tid))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("guide_power", g.power))
        lines.append(asp.fact("gift", gid))
    lines.append(asp.fact("disturbed"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show dangerous/2."))
    return sorted(set(asp.atoms(model, "dangerous")))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    p = set((p, t) for p, t, _ in valid_combos())
    if a != p:
        rc = 1
        print("MISMATCH in reasonableness gate")
        print(" only in asp:", sorted(a - p))
        print(" only in python:", sorted(p - a))
    else:
        print(f"OK: ASP gate matches valid_combos() ({len(a)} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, temptation=None, guide=None, delay=None, seed=None), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"FAIL: generate() smoke test crashed: {e}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic story world with inner monologue and tendency.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--temptation", choices=TANTALIZATIONS)
    ap.add_argument("--guide", choices=GIFTS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.temptation is None or c[1] == args.temptation)
              and (args.guide is None or c[2] == args.guide)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, temptation, guide = rng.choice(sorted(combos))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        place=place,
        temptation=temptation,
        guide=guide,
        delay=delay,
        hero_name=rng.choice(["Ari", "Lina", "Niko", "Mara", "Tavi"]),
        hero_gender=rng.choice(["boy", "girl"]),
        guide_name=rng.choice(["Mara", "Hale", "Ira", "Sera"]),
        guide_gender=rng.choice(["girl", "boy"]),
    )


def valid_story_world(params: StoryParams) -> bool:
    return True


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TANTALIZATIONS[params.temptation], GIFTS[params.guide],
                 delay=params.delay, hero_name=params.hero_name, hero_gender=params.hero_gender,
                 guide_name=params.guide_name, guide_gender=params.guide_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in _world_knowledge(world)],
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
        print(asp_program("", "#show dangerous/2.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} dangerous (place, temptation) combos:\n")
        for p, t in combos:
            print(f"  {p:10} {t}")
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.place} / {p.temptation} / {p.guide}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
