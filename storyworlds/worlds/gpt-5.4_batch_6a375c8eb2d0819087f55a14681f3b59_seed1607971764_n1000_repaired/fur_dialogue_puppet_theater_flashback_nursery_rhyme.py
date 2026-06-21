#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fur_dialogue_puppet_theater_flashback_nursery_rhyme.py
=================================================================================

A standalone story world for a tiny nursery-rhyme-like puppet-theater tale.

Premise
-------
A child and a soft puppet are about to perform a little rhyme on a puppet
theater stage. The puppet has a bit of fur, the audience is waiting, and the
child suddenly loses the next line of dialogue. A flashback to an earlier
practice moment brings the missing words back. The show ends warmly, with a
small changed image that proves the child is steadier now.

This world models:
- typed entities with physical meters and emotional memes
- a state-driven story with setup, tension, flashback turn, and ending
- a reasonableness gate over compatible (rhyme, puppet, cue) combinations
- an inline ASP twin for parity checking

Run it
------
python storyworlds/worlds/gpt-5.4/fur_dialogue_puppet_theater_flashback_nursery_rhyme.py
python storyworlds/worlds/gpt-5.4/fur_dialogue_puppet_theater_flashback_nursery_rhyme.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/fur_dialogue_puppet_theater_flashback_nursery_rhyme.py --all
python storyworlds/worlds/gpt-5.4/fur_dialogue_puppet_theater_flashback_nursery_rhyme.py --asp
python storyworlds/worlds/gpt-5.4/fur_dialogue_puppet_theater_flashback_nursery_rhyme.py --verify
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
STEADY_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Rhyme:
    id: str
    title: str
    opening: str
    line_a: str
    line_b: str
    image: str
    cue_tags: set[str] = field(default_factory=set)
    puppet_tags: set[str] = field(default_factory=set)
    rhythm_word: str = ""
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
class PuppetCfg:
    id: str
    label: str
    phrase: str
    fur_spot: str
    voice: str
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
class Cue:
    id: str
    label: str
    phrase: str
    flashback_image: str
    reminder: str
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
class MentorCfg:
    id: str
    type: str
    label: str
    patient: bool = True
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


def _r_stage_fright(world: World) -> list[str]:
    hero = world.get("hero")
    puppet = world.get("puppet")
    if hero.memes["worry"] < THRESHOLD or puppet.memes["forgot"] < THRESHOLD:
        return []
    sig = ("stage_fright",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["freeze"] += 1
    puppet.memes["droop"] += 1
    return ["__freeze__"]


def _r_flashback_recovers(world: World) -> list[str]:
    hero = world.get("hero")
    puppet = world.get("puppet")
    cue = world.get("cue")
    if cue.meters["seen"] < THRESHOLD or hero.memes["freeze"] < THRESHOLD:
        return []
    sig = ("flashback_recovers",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["remembered"] += 1
    hero.memes["steady"] += 1
    hero.memes["worry"] = 0.0
    hero.memes["freeze"] = 0.0
    puppet.memes["forgot"] = 0.0
    puppet.memes["droop"] = 0.0
    puppet.memes["bright"] += 1
    return ["__memory__"]


CAUSAL_RULES = [
    Rule(name="stage_fright", tag="emotional", apply=_r_stage_fright),
    Rule(name="flashback_recovers", tag="memory", apply=_r_flashback_recovers),
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


def cue_fits(rhyme: Rhyme, cue: Cue) -> bool:
    return bool(rhyme.cue_tags & cue.tags)


def puppet_fits(rhyme: Rhyme, puppet: PuppetCfg) -> bool:
    return bool(rhyme.puppet_tags & puppet.tags)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for rhyme_id, rhyme in RHYMES.items():
        for puppet_id, puppet in PUPPETS.items():
            for cue_id, cue in CUES.items():
                if cue_fits(rhyme, cue) and puppet_fits(rhyme, puppet):
                    combos.append((rhyme_id, puppet_id, cue_id))
    return sorted(combos)


def predict_recovery(rhyme: Rhyme, cue: Cue) -> bool:
    return cue_fits(rhyme, cue)


def explain_rejection(rhyme: Rhyme, puppet: PuppetCfg, cue: Cue) -> str:
    if not puppet_fits(rhyme, puppet):
        return (
            f"(No story: {puppet.phrase} does not suit the rhyme '{rhyme.title}'. "
            f"The puppet should match the rhyme image so the show feels natural.)"
        )
    if not cue_fits(rhyme, cue):
        return (
            f"(No story: {cue.phrase} would not honestly remind the child of "
            f"'{rhyme.title}'. The flashback cue needs to share the rhyme's image.)"
        )
    return "(No story: this combination does not form a sensible memory cue.)"


def flashback_preview(world: World) -> dict:
    sim = world.copy()
    sim.get("cue").meters["seen"] += 1
    propagate(sim, narrate=False)
    return {
        "remembered": sim.get("hero").memes["remembered"] >= THRESHOLD,
        "steady": sim.get("hero").memes["steady"],
    }


def stage_setup(world: World, hero: Entity, mentor: Entity, puppet: Entity, rhyme: Rhyme) -> None:
    hero.memes["joy"] += 1
    puppet.memes["ready"] += 1
    world.say(
        f"In the little puppet theater, {hero.id} lifted {puppet.label} above the red curtain. "
        f"{puppet.phrase.capitalize()} had {puppet.attrs['fur_spot']}, and the tiny stage glowed like a candle in a rhyme."
    )
    world.say(
        f'{mentor.label_word.capitalize()} tied the curtain string and whispered, '
        f'"When the bell rings, begin with your best dialogue."'
    )
    world.say(
        f'Together they had chosen "{rhyme.title}," a small sing-song piece that began, '
        f'"{rhyme.opening}"'
    )


def audience_waits(world: World, hero: Entity, puppet: Entity, rhyme: Rhyme) -> None:
    world.say(
        f"Soon the children on the benches grew quiet. {hero.id} gave {puppet.label} "
        f"{puppet.attrs['voice']} voice and started the first line: "
        f'"{rhyme.line_a}"'
    )


def forget(world: World, hero: Entity, puppet: Entity) -> None:
    hero.memes["worry"] += 1
    puppet.memes["forgot"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But then the next words slipped away. {hero.id}'s fingers stopped, "
        f"and {puppet.label} sagged over the stage rail as if the rhyme had gone to sleep."
    )
    if hero.memes["freeze"] >= THRESHOLD:
        world.say(
            f"The waiting felt big and round in {hero.id}'s chest, and even the soft fur under "
            f"{hero.pronoun('possessive')} thumb could not help at first."
        )


def mentor_nudges(world: World, mentor: Entity, cue: Entity) -> None:
    world.say(
        f'{mentor.label_word.capitalize()} did not rush. {mentor.pronoun().capitalize()} only tapped '
        f'{cue.phrase} by the stage and said, "Look here, love. Look and listen."'
    )


def flashback(world: World, hero: Entity, mentor: Entity, cue: Entity, rhyme: Rhyme) -> None:
    cue.meters["seen"] += 1
    before = flashback_preview(world)
    world.facts["predicted_recovery"] = before["remembered"]
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"At once a flashback fluttered through {hero.id}'s mind: yesterday after supper, "
        f"{mentor.label_word} had set out {cue.phrase}, and the two of them had practiced beside the puppet theater."
    )
    world.say(
        f'{mentor.label_word.capitalize()} had spoken the old pattern slowly: '
        f'"{rhyme.line_a}" Then {hero.id} had answered, "{rhyme.line_b}"'
    )
    world.say(
        f"In the remembered room, {cue.label} shone near {rhyme.image}, and the rhyme had stepped into place like neat little feet."
    )


def recover_and_play(world: World, hero: Entity, puppet: Entity, rhyme: Rhyme) -> None:
    world.para()
    if hero.memes["remembered"] >= THRESHOLD:
        hero.memes["joy"] += 1
        puppet.meters["bob"] += 1
        world.say(
            f"Back on the stage, {hero.id} breathed in, stroked the puppet's fur, and found the missing words."
        )
        world.say(
            f'In {puppet.attrs["voice"]} voice, {hero.pronoun()} finished the dialogue: '
            f'"{rhyme.line_b}"'
        )
        world.say(
            f"The puppet bobbed, the benches rippled with happy giggles, and the little rhyme ran to its end without stumbling."
        )
    else:
        raise StoryError("(Story crash: the flashback failed to restore the rhyme.)")


def ending(world: World, hero: Entity, mentor: Entity, puppet: Entity, cue: Entity) -> None:
    hero.memes["calm"] += 1
    world.say(
        f"When the curtain dropped, {mentor.label_word} squeezed {hero.id}'s shoulder. "
        f'{mentor.pronoun().capitalize()} smiled and said, "Now you know what to do when a line hides."'
    )
    world.say(
        f"{hero.id} set {puppet.label} beside {cue.phrase}. The puppet seemed to sit taller than before, "
        f"and so did {hero.pronoun()}."
    )


def tell(
    rhyme: Rhyme,
    puppet_cfg: PuppetCfg,
    cue_cfg: Cue,
    mentor_cfg: MentorCfg,
    hero_name: str,
    hero_type: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero", traits=[trait]))
    mentor = world.add(Entity(id="mentor", kind="character", type=mentor_cfg.type, label="the parent", role="mentor"))
    puppet = world.add(Entity(id="puppet", kind="thing", type="puppet", label=f"the {puppet_cfg.label}", role="puppet"))
    cue = world.add(Entity(id="cue", kind="thing", type="cue", label=cue_cfg.label, role="cue"))
    stage = world.add(Entity(id="stage", kind="thing", type="stage", label="the puppet theater", role="stage"))

    puppet.attrs["fur_spot"] = puppet_cfg.fur_spot
    puppet.attrs["voice"] = puppet_cfg.voice
    hero.attrs["name"] = hero_name
    cue.attrs["flashback_image"] = cue_cfg.flashback_image
    stage.attrs["place"] = "puppet theater"

    hero.memes["worry"] = 0.0
    hero.memes["freeze"] = 0.0
    hero.memes["remembered"] = 0.0
    hero.memes["steady"] = 0.0
    puppet.memes["forgot"] = 0.0
    puppet.memes["droop"] = 0.0
    cue.meters["seen"] = 0.0
    puppet.meters["bob"] = 0.0

    stage_setup(world, hero, mentor, puppet, rhyme)
    world.para()
    audience_waits(world, hero, puppet, rhyme)
    forget(world, hero, puppet)
    mentor_nudges(world, mentor, cue)
    flashback(world, hero, mentor, cue, rhyme)
    recover_and_play(world, hero, puppet, rhyme)
    world.para()
    ending(world, hero, mentor, puppet, cue)

    world.facts.update(
        hero=hero,
        mentor=mentor,
        puppet=puppet,
        cue=cue,
        stage=stage,
        rhyme=rhyme,
        puppet_cfg=puppet_cfg,
        cue_cfg=cue_cfg,
        remembered=hero.memes["remembered"] >= THRESHOLD,
        steady=hero.memes["steady"] >= STEADY_MIN,
        flashback_used=cue.meters["seen"] >= THRESHOLD,
    )
    return world


RHYMES = {
    "moon": Rhyme(
        id="moon",
        title="The Moon at Noon",
        opening="Moon so high, moon so bright",
        line_a="Moon so high, do you peep at noon?",
        line_b="Yes, I peep and hum a silver tune.",
        image="a painted moon-card",
        cue_tags={"moon", "silver"},
        puppet_tags={"night", "soft"},
        rhythm_word="moon",
    ),
    "star": Rhyme(
        id="star",
        title="Star by the Bar",
        opening="Star so small, star so far",
        line_a="Star so small, how did you get so far?",
        line_b="I rode a wink from jar to jar.",
        image="a paper star",
        cue_tags={"star", "shine"},
        puppet_tags={"bright", "soft"},
        rhythm_word="star",
    ),
    "spoon": Rhyme(
        id="spoon",
        title="The Spoon's Little Tune",
        opening="Silver spoon, silver soon",
        line_a="Silver spoon, why sing to the moon?",
        line_b="Because a bowl makes a round good tune.",
        image="a shiny spoon",
        cue_tags={"spoon", "silver"},
        puppet_tags={"kitchen", "soft"},
        rhythm_word="spoon",
    ),
}

PUPPETS = {
    "kitten": PuppetCfg(
        id="kitten",
        label="kitten puppet",
        phrase="a velvet kitten puppet",
        fur_spot="a gray patch of fur behind one ear",
        voice="a tiny purry",
        tags={"night", "soft", "bright"},
    ),
    "lamb": PuppetCfg(
        id="lamb",
        label="lamb puppet",
        phrase="a woolly lamb puppet",
        fur_spot="a curl of cream fur under its chin",
        voice="a little baa-baa",
        tags={"soft", "bright"},
    ),
    "bear": PuppetCfg(
        id="bear",
        label="bear puppet",
        phrase="a round brown bear puppet",
        fur_spot="a warm puff of fur on one paw",
        voice="a low cozy",
        tags={"night", "kitchen", "soft"},
    ),
}

CUES = {
    "moon_card": Cue(
        id="moon_card",
        label="the moon card",
        phrase="the painted moon card",
        flashback_image="the silver circle on blue paper",
        reminder="its round shine reminded the child of the moon line",
        tags={"moon", "silver"},
    ),
    "star_ribbon": Cue(
        id="star_ribbon",
        label="the star ribbon",
        phrase="the gold star ribbon",
        flashback_image="the tiny points sewn into the ribbon",
        reminder="its points reminded the child where the star dialogue turned",
        tags={"star", "shine"},
    ),
    "spoon_prop": Cue(
        id="spoon_prop",
        label="the spoon prop",
        phrase="the little spoon prop",
        flashback_image="the bright bowl of the spoon",
        reminder="its round bowl reminded the child of the spoon verse",
        tags={"spoon", "silver"},
    ),
}

MENTORS = {
    "mother": MentorCfg(id="mother", type="mother", label="mom", patient=True),
    "father": MentorCfg(id="father", type="father", label="dad", patient=True),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Rose", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Ben", "Theo", "Max", "Finn", "Noah", "Eli", "Sam", "Leo"]
TRAITS = ["careful", "hopeful", "gentle", "eager", "bright", "thoughtful"]


@dataclass
class StoryParams:
    rhyme: str
    puppet: str
    cue: str
    mentor: str
    name: str
    gender: str
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
    "puppet_theater": [
        (
            "What is a puppet theater?",
            "A puppet theater is a small stage where people make puppets act and talk. The curtain and stage help the puppets feel like story characters."
        )
    ],
    "fur": [
        (
            "What is fur?",
            "Fur is the soft hair that grows on some animals. It feels warm and fluffy when you touch it gently."
        )
    ],
    "dialogue": [
        (
            "What is dialogue in a story?",
            "Dialogue is the part where characters speak to each other. It helps us hear what they say and how they feel."
        )
    ],
    "flashback": [
        (
            "What is a flashback?",
            "A flashback is a moment in a story that shows something from earlier. It can help explain what a character remembers or understands now."
        )
    ],
    "moon": [
        (
            "Why can a picture help you remember words?",
            "A picture can remind your mind of something you practiced before. Seeing the same shape or object can help the words come back."
        )
    ],
    "star": [
        (
            "Why do stars twinkle?",
            "Stars look as if they twinkle because their light passes through moving air above us. The air bends the light a little as it travels."
        )
    ],
    "spoon": [
        (
            "Why is a spoon shiny?",
            "A spoon is often made of smooth metal that reflects light. That is why it can look bright and gleaming."
        )
    ],
}
KNOWLEDGE_ORDER = ["puppet_theater", "fur", "dialogue", "flashback", "moon", "star", "spoon"]


def generation_prompts(world: World) -> list[str]:
    rhyme = world.facts["rhyme"]
    puppet = world.facts["puppet_cfg"]
    cue = world.facts["cue_cfg"]
    hero = world.facts["hero"]
    mentor = world.facts["mentor"]
    return [
        'Write a nursery-rhyme-like story set in a puppet theater that includes the words "fur" and "dialogue" and uses a flashback.',
        f"Tell a gentle story where {hero.label}, a child at a puppet theater, forgets a line in the middle of a rhyme, then remembers it when {mentor.label_word} points to {cue.phrase}.",
        f"Write a sing-song story about {puppet.label} and the rhyme '{rhyme.title}', where a flashback helps the missing dialogue come back just in time.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    mentor = world.facts["mentor"]
    puppet = world.facts["puppet"]
    cue = world.facts["cue"]
    rhyme = world.facts["rhyme"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child performing in a puppet theater, {mentor.label_word} nearby, and {puppet.label}. The little show matters because everyone is waiting to hear the rhyme."
        ),
        (
            "What was the problem on the stage?",
            f"{hero.label} forgot the next line of dialogue in the rhyme, so the puppet drooped and the show almost stopped. The trouble began when the waiting audience made {hero.pronoun('object')} feel worried and frozen."
        ),
        (
            f"How did the flashback help {hero.label}?",
            f"When {mentor.label_word} tapped {cue.phrase}, {hero.label} remembered practicing the same rhyme earlier. The old picture and sound matched the rhyme, so the missing words came back."
        ),
        (
            "How did the story end?",
            f"{hero.label} finished the rhyme, and the audience laughed happily. After the curtain fell, {hero.pronoun()} stood straighter beside the puppet, showing that the scare had turned into steadiness."
        ),
    ]
    if world.facts.get("remembered"):
        qa.append(
            (
                f"Why did touching the puppet's fur matter at the end?",
                f"Touching the fur gave {hero.label} a calm little moment while the remembered line settled into place. It marked the change from freezing to speaking."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    rhyme = world.facts["rhyme"]
    tags = {"puppet_theater", "fur", "dialogue", "flashback"} | set(rhyme.cue_tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        rhyme="moon",
        puppet="kitten",
        cue="moon_card",
        mentor="mother",
        name="Mia",
        gender="girl",
        trait="gentle",
    ),
    StoryParams(
        rhyme="star",
        puppet="lamb",
        cue="star_ribbon",
        mentor="father",
        name="Theo",
        gender="boy",
        trait="hopeful",
    ),
    StoryParams(
        rhyme="spoon",
        puppet="bear",
        cue="spoon_prop",
        mentor="mother",
        name="Nora",
        gender="girl",
        trait="thoughtful",
    ),
    StoryParams(
        rhyme="moon",
        puppet="bear",
        cue="moon_card",
        mentor="father",
        name="Ben",
        gender="boy",
        trait="eager",
    ),
]


ASP_RULES = r"""
cue_fits(R,C)    :- rhyme(R), cue(C), rhyme_cue_tag(R,T), cue_tag(C,T).
puppet_fits(R,P) :- rhyme(R), puppet(P), rhyme_puppet_tag(R,T), puppet_tag(P,T).

valid(R,P,C) :- cue_fits(R,C), puppet_fits(R,P).

chosen_valid :- chosen_rhyme(R), chosen_puppet(P), chosen_cue(C), valid(R,P,C).
remembered   :- chosen_valid.
steady(1)    :- remembered.
steady(0)    :- not remembered.

#show valid/3.
#show remembered/0.
#show steady/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rhyme_id, rhyme in RHYMES.items():
        lines.append(asp.fact("rhyme", rhyme_id))
        for tag in sorted(rhyme.cue_tags):
            lines.append(asp.fact("rhyme_cue_tag", rhyme_id, tag))
        for tag in sorted(rhyme.puppet_tags):
            lines.append(asp.fact("rhyme_puppet_tag", rhyme_id, tag))
    for puppet_id, puppet in PUPPETS.items():
        lines.append(asp.fact("puppet", puppet_id))
        for tag in sorted(puppet.tags):
            lines.append(asp.fact("puppet_tag", puppet_id, tag))
    for cue_id, cue in CUES.items():
        lines.append(asp.fact("cue", cue_id))
        for tag in sorted(cue.tags):
            lines.append(asp.fact("cue_tag", cue_id, tag))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_remembered(params: StoryParams) -> bool:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_rhyme", params.rhyme),
            asp.fact("chosen_puppet", params.puppet),
            asp.fact("chosen_cue", params.cue),
        ]
    )
    model = asp.one_model(asp_program(extra))
    return bool(asp.atoms(model, "remembered"))


def outcome_of(params: StoryParams) -> str:
    if not (
        params.rhyme in RHYMES
        and params.puppet in PUPPETS
        and params.cue in CUES
        and params.mentor in MENTORS
    ):
        raise StoryError("(Invalid parameters for this world.)")
    remembered = cue_fits(RHYMES[params.rhyme], CUES[params.cue]) and puppet_fits(RHYMES[params.rhyme], PUPPETS[params.puppet])
    return "steady" if remembered else "stuck"


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"resolve_params failed unexpectedly for seed {seed}")
            break

    for params in cases:
        py = outcome_of(params) == "steady"
        asp_ok = asp_remembered(params)
        if py != asp_ok:
            rc = 1
            print(
                "MISMATCH in remembered outcome:",
                params,
                "python=",
                py,
                "asp=",
                asp_ok,
            )
            break

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test story generation ran.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    if rc == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a puppet theater, a forgotten rhyme line, and a flashback that brings it back."
    )
    ap.add_argument("--rhyme", choices=sorted(RHYMES))
    ap.add_argument("--puppet", choices=sorted(PUPPETS))
    ap.add_argument("--cue", choices=sorted(CUES))
    ap.add_argument("--mentor", choices=sorted(MENTORS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.rhyme and args.puppet and args.cue:
        rhyme = RHYMES[args.rhyme]
        puppet = PUPPETS[args.puppet]
        cue = CUES[args.cue]
        if not (puppet_fits(rhyme, puppet) and cue_fits(rhyme, cue)):
            raise StoryError(explain_rejection(rhyme, puppet, cue))

    combos = [
        combo
        for combo in valid_combos()
        if (args.rhyme is None or combo[0] == args.rhyme)
        and (args.puppet is None or combo[1] == args.puppet)
        and (args.cue is None or combo[2] == args.cue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    rhyme_id, puppet_id, cue_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mentor = args.mentor or rng.choice(sorted(MENTORS))
    trait = rng.choice(TRAITS)

    return StoryParams(
        rhyme=rhyme_id,
        puppet=puppet_id,
        cue=cue_id,
        mentor=mentor,
        name=name,
        gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.rhyme not in RHYMES:
        raise StoryError(f"(Unknown rhyme: {params.rhyme})")
    if params.puppet not in PUPPETS:
        raise StoryError(f"(Unknown puppet: {params.puppet})")
    if params.cue not in CUES:
        raise StoryError(f"(Unknown cue: {params.cue})")
    if params.mentor not in MENTORS:
        raise StoryError(f"(Unknown mentor: {params.mentor})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")

    rhyme = RHYMES[params.rhyme]
    puppet = PUPPETS[params.puppet]
    cue = CUES[params.cue]
    if not (puppet_fits(rhyme, puppet) and cue_fits(rhyme, cue)):
        raise StoryError(explain_rejection(rhyme, puppet, cue))

    world = tell(
        rhyme=rhyme,
        puppet_cfg=puppet,
        cue_cfg=cue,
        mentor_cfg=MENTORS[params.mentor],
        hero_name=params.name,
        hero_type=params.gender,
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
        print(asp_program(""))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (rhyme, puppet, cue) combos:\n")
        for rhyme, puppet, cue in combos:
            print(f"  {rhyme:6} {puppet:7} {cue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
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
            header = f"### {p.name}: {p.rhyme} / {p.puppet} / {p.cue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
