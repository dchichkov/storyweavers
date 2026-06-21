#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/organ_cheat_strike_rhyme_transformation_myth.py
============================================================================

A standalone storyworld for a tiny mythic domain:

A child climbs to a holy organ to sing for spring. A tempting trick offers an
easy win, but the shrine spirit hates a cheat. If the child cheats, a divine
strike flashes from the sky and a transformation follows. If the child tells the
truth and makes amends quickly enough, the spell is lifted and the organ sings
honestly again. If the child listens to a wiser helper in time, no punishment
falls, and the shrine answers with a gentler transformation of blessing instead.

The stories keep two seed features in view:
- Rhyme: the spirit and endings use short rhyming lines.
- Transformation: either a punishment spell changes the child, or honesty
  changes a simple reed into a magical gift.

Run it
------
    python storyworlds/worlds/gpt-5.4/organ_cheat_strike_rhyme_transformation_myth.py
    python storyworlds/worlds/gpt-5.4/organ_cheat_strike_rhyme_transformation_myth.py --organ reed_organ --cheat storm_seed
    python storyworlds/worlds/gpt-5.4/organ_cheat_strike_rhyme_transformation_myth.py --organ shell_organ --cheat wax_whistle
    python storyworlds/worlds/gpt-5.4/organ_cheat_strike_rhyme_transformation_myth.py --all
    python storyworlds/worlds/gpt-5.4/organ_cheat_strike_rhyme_transformation_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/organ_cheat_strike_rhyme_transformation_myth.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2
AMBITION_INIT = 6.0
CAREFUL_TRAITS = {"careful", "patient", "truthful", "steady"}


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
        female = {"girl", "mother", "goddess", "woman"}
        male = {"boy", "father", "god", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type == "mother":
            return "mother"
        if self.type == "father":
            return "father"
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Shrine:
    id: str
    place: str
    climb: str
    image: str
    spirit_name: str
    spirit_type: str
    breeze: str
    blessing: str
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
class OrganCfg:
    id: str
    label: str
    phrase: str
    voice: str
    location: str
    materials: str
    supports: set[str] = field(default_factory=set)
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
class CheatCfg:
    id: str
    label: str
    phrase: str
    hide_text: str
    warning: str
    strike_text: str
    risk: int
    needs: set[str] = field(default_factory=set)
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
class FormCfg:
    id: str
    noun: str
    phrase: str
    move: str
    sound: str
    small_image: str
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
class Atonement:
    id: str
    sense: int
    power: int
    text: str
    restore_text: str
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


def _r_notice_cheat(world: World) -> list[str]:
    hero = world.entities.get("hero")
    organ = world.entities.get("organ")
    spirit = world.entities.get("spirit")
    if hero is None or organ is None or spirit is None:
        return []
    if hero.meters["cheating"] < THRESHOLD:
        return []
    sig = ("notice", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    spirit.memes["anger"] += 1
    organ.meters["tainted"] += 1
    hero.memes["guilt"] += 1
    return ["__omen__"]


def _r_divine_strike(world: World) -> list[str]:
    hero = world.entities.get("hero")
    organ = world.entities.get("organ")
    spirit = world.entities.get("spirit")
    if hero is None or organ is None or spirit is None:
        return []
    if hero.meters["played"] < THRESHOLD or spirit.memes["anger"] < THRESHOLD:
        return []
    sig = ("strike", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["struck"] += 1
    hero.meters["transformed"] += 1
    hero.memes["fear"] += 1
    organ.meters["cracked"] += 1
    spirit.memes["wrath_done"] += 1
    return ["__strike__"]


def _r_restore(world: World) -> list[str]:
    hero = world.entities.get("hero")
    organ = world.entities.get("organ")
    if hero is None or organ is None:
        return []
    if hero.meters["transformed"] < THRESHOLD or hero.meters["atoned"] < THRESHOLD:
        return []
    sig = ("restore", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["transformed"] = 0.0
    hero.meters["restored"] += 1
    hero.memes["relief"] += 1
    organ.meters["healed"] += 1
    return ["__restore__"]


CAUSAL_RULES = [
    Rule(name="notice_cheat", tag="social", apply=_r_notice_cheat),
    Rule(name="divine_strike", tag="physical", apply=_r_divine_strike),
    Rule(name="restore", tag="magical", apply=_r_restore),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def cheat_works(organ: OrganCfg, cheat: CheatCfg) -> bool:
    return bool(organ.supports & cheat.needs)


def sensible_atonements() -> list[Atonement]:
    return [a for a in ATONEMENTS.values() if a.sense >= SENSE_MIN]


def strike_severity(cheat: CheatCfg, delay: int) -> int:
    return cheat.risk + delay


def is_restored(atonement: Atonement, cheat: CheatCfg, delay: int) -> bool:
    return atonement.power >= strike_severity(cheat, delay)


def careful_start(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, hero_age: int, helper_age: int, trait: str) -> bool:
    helper_older = relation == "siblings" and helper_age > hero_age
    authority = careful_start(trait) + 1.0 + (4.0 if helper_older else 0.0)
    return helper_older and authority > AMBITION_INIT


def predict_strike(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["cheating"] += 1
    hero.meters["played"] += 1
    propagate(sim, narrate=False)
    return {
        "struck": hero.meters["struck"] >= THRESHOLD,
        "transformed": hero.meters["transformed"] >= THRESHOLD,
        "cracked": sim.get("organ").meters["cracked"] >= THRESHOLD,
    }


def opening(world: World, shrine: Shrine, hero: Entity, helper: Entity, organ: OrganCfg, prize: str) -> None:
    hero.memes["wonder"] += 1
    helper.memes["wonder"] += 1
    world.say(
        f"In the old days, when hills still answered songs, {hero.id} and {helper.id} climbed to {shrine.place}. "
        f"{shrine.image} There stood {organ.phrase} {organ.location}, and the winner of the spring song would carry {prize} home."
    )
    world.say(
        f"{hero.id} stared at the organ's {organ.materials}. It was said that when true breath touched it, {organ.voice}."
    )


def desire(world: World, hero: Entity, prize: str) -> None:
    hero.memes["ambition"] += 1
    world.say(
        f'{hero.id} wanted {prize} so badly that {hero.pronoun()} could almost feel it against {hero.pronoun("possessive")} brow.'
    )


def temptation(world: World, hero: Entity, cheat: CheatCfg) -> None:
    hero.memes["temptation"] += 1
    world.say(
        f"Near the shrine steps, {hero.id} found {cheat.phrase}. A sly thought crept in: a cheat might make the organ sound grander than truth."
    )
    world.say(f"{cheat.hide_text}")


def warn(world: World, helper: Entity, hero: Entity, cheat: CheatCfg, shrine: Shrine) -> None:
    pred = predict_strike(world)
    helper.memes["caution"] += 1
    world.facts["predicted_struck"] = pred["struck"]
    helper_extra = ""
    if pred["cracked"]:
        helper_extra = " The helper could almost hear a crack of warning in the air."
    world.say(
        f'{helper.id} caught {hero.id}\'s sleeve. "{cheat.warning} {shrine.spirit_name} hears hollow music. '
        f'''If you cheat, the sky may strike."{helper_extra}'''
    )


def back_down(world: World, hero: Entity, helper: Entity, cheat: CheatCfg) -> None:
    hero.memes["ambition"] = 0.0
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{hero.id} looked at {cheat.label}, then at {helper.id}, and felt the proud heat cool. "
        f'"No," {hero.pronoun()} said. "I will not cheat for a wreath."'
    )


def perform_honestly(world: World, hero: Entity, organ: Entity, shrine: Shrine, prize: str) -> None:
    hero.meters["played"] += 1
    hero.memes["honesty"] += 1
    organ.meters["sounding"] += 1
    world.say(
        f"{hero.id} laid both hands on the organ and sang with an unhidden voice. The notes rose clean into the morning, and {shrine.breeze}."
    )
    world.say(
        f'Then the shrine answered in rhyme: "True tone, true breath, / outsinging death." The judges set {prize} on {hero.id}\'s head.'
    )


def blessing_transform(world: World, hero: Entity, organ: Entity, shrine: Shrine) -> None:
    organ.meters["blessed"] += 1
    world.say(
        f"As the last note faded, one plain reed beside the keys shimmered and transformed into {shrine.blessing}. "
        f"{hero.id} kept it as a sign that honest music grows."
    )


def cheat_play(world: World, hero: Entity, organ: Entity, cheat: CheatCfg) -> None:
    hero.meters["cheating"] += 1
    hero.meters["played"] += 1
    organ.meters["sounding"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} slipped {cheat.label} into place and pressed the keys. For one breath the organ boomed brighter than sunlight, richer than it should have been."
    )


def divine_strike_scene(world: World, hero: Entity, organ: Entity, spirit: Entity, form: FormCfg, cheat: CheatCfg) -> None:
    propagate(world, narrate=False)
    world.say(
        f"Then came the strike. {cheat.strike_text} A white flash jumped from the sky, rang through the organ, and split one shining board."
    )
    world.say(
        f"{hero.id} stumbled back, light on {hero.pronoun('possessive')} shoulders, and was transformed into {form.phrase}. "
        f"Now {hero.pronoun()} could only {form.sound} and {form.move}."
    )
    world.say(
        f'The spirit\'s voice rolled over the stones in rhyme: "False song, false pride, / let truth now hide."'
    )


def helper_compassion(world: World, helper: Entity, form: FormCfg) -> None:
    helper.memes["love"] += 1
    world.say(
        f"{helper.id} did not run away. {helper.pronoun().capitalize()} knelt beside the little {form.noun} and whispered that fear had done enough."
    )


def atone(world: World, hero: Entity, helper: Entity, atonement: Atonement, form: FormCfg, shrine: Shrine) -> None:
    hero.meters["atoned"] += 1
    hero.memes["honesty"] += 1
    hero.memes["guilt"] += 1
    world.say(
        atonement.text.format(
            hero=hero.id,
            helper=helper.id,
            spirit=shrine.spirit_name,
            form=form.noun,
        )
    )


def restored_scene(world: World, hero: Entity, organ: Entity, shrine: Shrine, form: FormCfg, atonement: Atonement) -> None:
    propagate(world, narrate=False)
    world.say(
        atonement.restore_text.format(
            hero=hero.id,
            spirit=shrine.spirit_name,
            form=form.noun,
        )
    )
    world.say(
        f'The spirit answered in rhyme: "Truth confessed, / the heart is blessed." {hero.id} touched the mended organ and chose a smaller, truer song.'
    )


def lasting_scene(world: World, hero: Entity, helper: Entity, shrine: Shrine, form: FormCfg, atonement: Atonement) -> None:
    world.say(
        atonement.fail_text.format(
            hero=hero.id,
            helper=helper.id,
            spirit=shrine.spirit_name,
            form=form.noun,
        )
    )
    world.say(
        f'{shrine.spirit_name} spoke once more in rhyme: "Till pride grows small, / sing truth to all." So {hero.id} kept the {form.noun} shape for a long season, '
        f"singing over the fields until the lesson settled gently inside."
    )


def changed_ending(world: World, hero: Entity, helper: Entity, shrine: Shrine, outcome: str, form: FormCfg) -> None:
    if outcome == "averted":
        world.say(
            f"From that day on, children at {shrine.place} touched the organ with clean hands. When the wind moved through the pipes, it sounded like a promise kept."
        )
    elif outcome == "restored":
        world.say(
            f"After that, {hero.id} never reached for a cheat again. Whenever {helper.id} heard the organ answer the dawn, the music sounded warmer because truth had come back."
        )
    else:
        world.say(
            f"And in that valley, when a tiny {form.noun} sang over wheat at sunrise, grown-ups would smile and tell children that pride can shrink, but honest song can grow."
        )
@dataclass
class StoryParams:
    shrine: str
    organ: str
    cheat: str
    form: str
    atonement: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    helper_trait: str
    parent: str
    relation: str = "siblings"
    hero_age: int = 6
    helper_age: int = 8
    delay: int = 0
    prize: str = "the laurel ring"
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
    "organ": [(
        "What is an organ?",
        "An organ is a big musical instrument that sends air through pipes or reeds to make sound. In stories and temples, it can make a deep, grand music."
    )],
    "cheat": [(
        "What does it mean to cheat?",
        "To cheat means trying to win by a trick instead of by honest effort. It feels faster at first, but it breaks trust."
    )],
    "strike": [(
        "What is a lightning strike?",
        "A lightning strike is a bright bolt of electricity from a storm cloud. It flashes very fast and can hit trees, towers, or anything standing high."
    )],
    "rhyme": [(
        "What is a rhyme?",
        "A rhyme is when words sound alike at the end, like song and long. Rhymes can make speech feel musical and easy to remember."
    )],
    "lark": [(
        "What is a lark?",
        "A lark is a small bird known for singing bright songs. People often picture it rising into the sky while it sings."
    )],
    "cricket": [(
        "Why do crickets chirp?",
        "Crickets make their chirping sound by rubbing parts of their wings together. Their tiny song is often heard in warm grass at night."
    )],
    "fish": [(
        "How does a fish move in water?",
        "A fish swishes its tail and bends its body from side to side. That pushes the water and helps it glide along."
    )],
    "truth": [(
        "Why is telling the truth important after a mistake?",
        "Telling the truth helps other people trust you again. It is the first step toward fixing what went wrong."
    )],
}
KNOWLEDGE_ORDER = ["organ", "cheat", "strike", "rhyme", "truth", "lark", "cricket", "fish"]


def pair_noun(hero: Entity, helper: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and helper.type == "boy":
            return "two brothers"
        if hero.type == "girl" and helper.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two young friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    shrine, organ, cheat, form = f["shrine"], f["organ_cfg"], f["cheat"], f["form"]
    hero = f["hero"]
    helper = f["helper"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a short child-facing myth about a holy {organ.label}, a tempting cheat, and an honest child who refuses it. Include the word "organ".',
            f'Write a mythic story where {hero.label} nearly uses {cheat.label} to win a song contest, but {helper.label} stops the plan before the sky can strike.',
            f'Write a gentle myth with rhyme and transformation, where honesty turns a plain reed into a magical gift at {shrine.place}.',
        ]
    if outcome == "restored":
        return [
            f'Write a mythic story for young children where a child cheats at a sacred organ, a divine strike transforms the child, and truth brings mercy.',
            f'Write a short myth that includes the words "organ", "cheat", and "strike", and ends with a changed child made wiser by confession.',
            f'Write a rhyming myth where {hero.label} is transformed into a {form.noun} after cheating, then restored after making amends.',
        ]
    return [
        f'Write a child-facing myth where a cheat at a sacred organ brings a heavenly strike and a lasting transformation.',
        f'Write a myth with rhyme in which {hero.label} cheats to win, is transformed into a {form.noun}, and must carry the lesson into the fields.',
        f'Write a cautionary myth that includes "organ", "cheat", and "strike" and shows why pride should not try to sing louder than truth.',
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    shrine = f["shrine"]
    organ = f["organ_cfg"]
    cheat = f["cheat"]
    form = f["form"]
    atonement = f["atonement"]
    prize = f["prize"]
    pair = pair_noun(hero, helper, f["relation"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero.label} and {helper.label}, who climbed to {shrine.place} for the spring song. The sacred {organ.label} and the shrine spirit are important too."
        ),
        (
            "Why did the child want to use a cheat?",
            f"{hero.label} wanted to win {prize} and feared that honest music might not be enough. That proud wish is what made the trick feel tempting."
        ),
        (
            f"Why did {helper.label} warn {hero.label}?",
            f"{helper.label} knew the trick would make the music false and anger {shrine.spirit_name}. In this story, the helper understood that a cheat at a holy place could bring a strike."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What transformation happened even though nobody was punished?",
            f"A plain reed transformed into {shrine.blessing} after the honest song. That blessing showed that truth can change the world in a gentle way."
        ))
        qa.append((
            f"How did the story end?",
            f"It ended happily, with {hero.label} choosing not to cheat and winning the song honestly. The shrine answered with a gift instead of a punishment."
        ))
    elif f["outcome"] == "restored":
        qa.append((
            "What happened when the child cheated?",
            f"A divine strike flashed through the organ, cracked it, and transformed {hero.label} into {form.phrase}. The punishment came because the child tried to win with false music."
        ))
        qa.append((
            f"How was the spell lifted?",
            f"{helper.label} helped {hero.label}, and together they {atonement.qa_text}. Because the child told the truth and tried to mend the wrong, the spirit showed mercy."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the child restored and wiser. The repaired organ and the smaller true song showed what had changed inside."
        ))
    else:
        qa.append((
            "Did the child change back right away?",
            f"No. {helper.label} tried to help, but the spirit let the {form.noun} shape remain for a long season. The lasting change made the lesson impossible to ignore."
        ))
        qa.append((
            "Why did the transformation last?",
            f"The cheat was serious, and the repair came too late or too weakly to mend it at once. In the story's mythic logic, pride had to shrink slowly before mercy could finish its work."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the small transformed singer over the fields, reminding everyone to be honest. The ending image proves that the child's pride had been changed into a humbler song."
        ))
    return qa


def world_knowledge_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"organ", "cheat", "rhyme", "truth"}
    if f["struck"]:
        tags.add("strike")
    form = f["form"]
    if form.id == "lark":
        tags.add("lark")
    elif form.id == "cricket":
        tags.add("cricket")
    elif form.id == "silver_fish":
        tags.add("fish")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        shrine="cliff_shrine",
        organ="reed_organ",
        cheat="echo_shell",
        form="lark",
        atonement="truth_song",
        hero_name="Orin",
        hero_gender="boy",
        helper_name="Mira",
        helper_gender="girl",
        helper_trait="careful",
        parent="mother",
        relation="siblings",
        hero_age=5,
        helper_age=7,
        delay=0,
        prize="the laurel ring",
    ),
    StoryParams(
        shrine="river_temple",
        organ="shell_organ",
        cheat="echo_shell",
        form="silver_fish",
        atonement="return_reed",
        hero_name="Iris",
        hero_gender="girl",
        helper_name="Lio",
        helper_gender="boy",
        helper_trait="curious",
        parent="father",
        relation="friends",
        hero_age=6,
        helper_age=6,
        delay=0,
        prize="the dawn garland",
    ),
    StoryParams(
        shrine="laurel_court",
        organ="cedar_organ",
        cheat="wax_whistle",
        form="cricket",
        atonement="return_reed",
        hero_name="Theron",
        hero_gender="boy",
        helper_name="Rhea",
        helper_gender="girl",
        helper_trait="steady",
        parent="mother",
        relation="siblings",
        hero_age=7,
        helper_age=5,
        delay=1,
        prize="the singer's branch",
    ),
    StoryParams(
        shrine="cliff_shrine",
        organ="reed_organ",
        cheat="storm_seed",
        form="lark",
        atonement="truth_song",
        hero_name="Nia",
        hero_gender="girl",
        helper_name="Thea",
        helper_gender="girl",
        helper_trait="truthful",
        parent="mother",
        relation="friends",
        hero_age=6,
        helper_age=6,
        delay=1,
        prize="the dawn garland",
    ),
]


def explain_rejection(organ: OrganCfg, cheat: CheatCfg) -> str:
    return (
        f"(No story: {cheat.label} does not fit the workings of the {organ.label}. "
        f"This world only allows cheats that could plausibly alter that kind of sacred organ.)"
    )


def explain_atonement(aid: str) -> str:
    a = ATONEMENTS[aid]
    better = ", ".join(sorted(x.id for x in sensible_atonements()))
    return (
        f"(Refusing atonement '{aid}': it scores too low on common sense "
        f"(sense={a.sense} < {SENSE_MIN}). A story should prefer honest repair, not hiding.)"
        + (f" Try: {better}." if better else "")
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.hero_age, params.helper_age, params.helper_trait):
        return "averted"
    return "restored" if is_restored(ATONEMENTS[params.atonement], CHEATS[params.cheat], params.delay) else "lasting"


ASP_RULES = r"""
% valid organ-cheat pair: the organ supports at least one needed trick family.
works(O,C) :- organ(O), cheat(C), supports(O,T), needs(C,T).
valid(O,C) :- works(O,C).

% sensible atonements
sensible(A) :- atonement(A), sense(A,S), sense_min(M), S >= M.

% outcome model
careful_now(T) :- trait(T), careful_trait(T).
init_caution(5) :- trait(T), careful_now(T).
init_caution(3) :- trait(T), not careful_now(T).
helper_older :- relation(siblings), hero_age(H), helper_age(G), G > H.
bonus(4) :- helper_older.
bonus(0) :- not helper_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- helper_older, authority(A), ambition_init(M), A > M.

severity(R + D) :- chosen_cheat(C), risk(C,R), delay(D).
restored :- chosen_atonement(A), power(A,P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(restored) :- not averted, restored.
outcome(lasting) :- not averted, not restored.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for shrine_id in SHRINES:
        lines.append(asp.fact("shrine", shrine_id))
    for organ_id, organ in ORGANS.items():
        lines.append(asp.fact("organ", organ_id))
        for tag in sorted(organ.supports):
            lines.append(asp.fact("supports", organ_id, tag))
    for cheat_id, cheat in CHEATS.items():
        lines.append(asp.fact("cheat", cheat_id))
        lines.append(asp.fact("risk", cheat_id, cheat.risk))
        for need in sorted(cheat.needs):
            lines.append(asp.fact("needs", cheat_id, need))
    for form_id in FORMS:
        lines.append(asp.fact("form", form_id))
    for aid, a in ATONEMENTS.items():
        lines.append(asp.fact("atonement", aid))
        lines.append(asp.fact("sense", aid, a.sense))
        lines.append(asp.fact("power", aid, a.power))
    for tr in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", tr))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("ambition_init", int(AMBITION_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_cheat", params.cheat),
        asp.fact("chosen_atonement", params.atonement),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("hero_age", params.hero_age),
        asp.fact("helper_age", params.helper_age),
        asp.fact("trait", params.helper_trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic storyworld: a sacred organ, a tempting cheat, a divine strike, and transformation."
    )
    ap.add_argument("--shrine", choices=SHRINES)
    ap.add_argument("--organ", choices=ORGANS)
    ap.add_argument("--cheat", choices=CHEATS)
    ap.add_argument("--form", choices=FORMS)
    ap.add_argument("--atonement", choices=ATONEMENTS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how long the child delays repair after the strike")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid organ-cheat pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.organ and args.cheat:
        if not cheat_works(ORGANS[args.organ], CHEATS[args.cheat]):
            raise StoryError(explain_rejection(ORGANS[args.organ], CHEATS[args.cheat]))
    if args.atonement and ATONEMENTS[args.atonement].sense < SENSE_MIN:
        raise StoryError(explain_atonement(args.atonement))

    combos = [
        combo for combo in valid_combos()
        if (args.organ is None or combo[0] == args.organ)
        and (args.cheat is None or combo[1] == args.cheat)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    organ_id, cheat_id = rng.choice(combos)
    shrine_id = args.shrine or rng.choice(sorted(SHRINES))
    form_id = args.form or rng.choice(sorted(FORMS))
    atonement_id = args.atonement or rng.choice(sorted(a.id for a in sensible_atonements()))
    hero_name, hero_gender = _pick_child(rng)
    helper_name, helper_gender = _pick_child(rng, avoid=hero_name)
    helper_trait = rng.choice(TRAITS)
    parent = args.parent or rng.choice(["mother", "father"])
    relation = rng.choice(["siblings", "friends"])
    hero_age, helper_age = rng.sample([4, 5, 6, 7, 8], 2)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    prize = rng.choice(PRIZES)
    return StoryParams(
        shrine=shrine_id,
        organ=organ_id,
        cheat=cheat_id,
        form=form_id,
        atonement=atonement_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        helper_trait=helper_trait,
        parent=parent,
        relation=relation,
        hero_age=hero_age,
        helper_age=helper_age,
        delay=delay,
        prize=prize,
    )


def generate(params: StoryParams) -> StorySample:
    if params.shrine not in SHRINES:
        raise StoryError(f"(Unknown shrine: {params.shrine})")
    if params.organ not in ORGANS:
        raise StoryError(f"(Unknown organ: {params.organ})")
    if params.cheat not in CHEATS:
        raise StoryError(f"(Unknown cheat: {params.cheat})")
    if params.form not in FORMS:
        raise StoryError(f"(Unknown form: {params.form})")
    if params.atonement not in ATONEMENTS:
        raise StoryError(f"(Unknown atonement: {params.atonement})")
    if not cheat_works(ORGANS[params.organ], CHEATS[params.cheat]):
        raise StoryError(explain_rejection(ORGANS[params.organ], CHEATS[params.cheat]))
    if ATONEMENTS[params.atonement].sense < SENSE_MIN:
        raise StoryError(explain_atonement(params.atonement))

    world = tell(
        shrine=SHRINES[params.shrine],
        organ_cfg=ORGANS[params.organ],
        cheat_cfg=CHEATS[params.cheat],
        form_cfg=FORMS[params.form],
        atonement_cfg=ATONEMENTS[params.atonement],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        helper_trait=params.helper_trait,
        parent_type=params.parent,
        relation=params.relation,
        hero_age=params.hero_age,
        helper_age=params.helper_age,
        delay=params.delay,
        prize=params.prize,
    )
    story = world.render().replace("hero", params.hero_name).replace("helper", params.helper_name)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa_items(world)],
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in organ-cheat compatibility:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    p_sens = {a.id for a in sensible_atonements()}
    c_sens = set(asp_sensible())
    if p_sens == c_sens:
        print(f"OK: sensible atonements match ({sorted(p_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible atonements: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(200):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(s)))
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(77))
        smoke_params.seed = 77
        sample = generate(smoke_params)
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True)
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible atonements: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (organ, cheat) pairs:\n")
        for organ_id, cheat_id in combos:
            print(f"  {organ_id:12} {cheat_id}")
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
            header = f"### {p.hero_name} at {p.shrine}: {p.organ} + {p.cheat} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    shrine: Shrine,
    organ_cfg: OrganCfg,
    cheat_cfg: CheatCfg,
    form_cfg: FormCfg,
    atonement_cfg: Atonement,
    hero_name: str = "Orin",
    hero_gender: str = "boy",
    helper_name: str = "Mira",
    helper_gender: str = "girl",
    helper_trait: str = "careful",
    parent_type: str = "mother",
    relation: str = "siblings",
    hero_age: int = 6,
    helper_age: int = 8,
    delay: int = 0,
    prize: str = "the laurel ring",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, role="hero", age=hero_age, label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, role="helper", age=helper_age, label=helper_name, traits=[helper_trait], attrs={"relation": relation}))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, role="parent", label=parent_type))
    spirit = world.add(Entity(id="spirit", kind="character", type=shrine.spirit_type, role="spirit", label=shrine.spirit_name))
    organ = world.add(Entity(id="organ", kind="thing", type="organ", role="organ", label=organ_cfg.label, tags=set(organ_cfg.tags)))

    hero.memes["ambition"] = AMBITION_INIT
    helper.memes["caution"] = careful_start(helper_trait)
    world.facts["prize"] = prize
    world.facts["delay"] = delay
    world.facts["relation"] = relation

    opening(world, shrine, hero, helper, organ_cfg, prize)
    desire(world, hero, prize)

    world.para()
    temptation(world, hero, cheat_cfg)
    warn(world, helper, hero, cheat_cfg, shrine)

    averted = would_avert(relation, hero_age, helper_age, helper_trait)
    if averted:
        back_down(world, hero, helper, cheat_cfg)
        world.para()
        perform_honestly(world, hero, organ, shrine, prize)
        blessing_transform(world, hero, organ, shrine)
        outcome = "averted"
    else:
        cheat_play(world, hero, organ, cheat_cfg)
        world.para()
        divine_strike_scene(world, hero, organ, spirit, form_cfg, cheat_cfg)
        helper_compassion(world, helper, form_cfg)
        restored = is_restored(atonement_cfg, cheat_cfg, delay)
        world.para()
        atone(world, hero, helper, atonement_cfg, form_cfg, shrine)
        if restored:
            restored_scene(world, hero, organ, shrine, form_cfg, atonement_cfg)
            outcome = "restored"
        else:
            lasting_scene(world, hero, helper, shrine, form_cfg, atonement_cfg)
            outcome = "lasting"

    world.para()
    changed_ending(world, hero, helper, shrine, outcome, form_cfg)

    world.facts.update(
        hero=hero,
        helper=helper,
        parent=parent,
        spirit=spirit,
        organ=organ,
        shrine=shrine,
        organ_cfg=organ_cfg,
        cheat=cheat_cfg,
        form=form_cfg,
        atonement=atonement_cfg,
        outcome=outcome,
        averted=averted,
        transformed=hero.meters["transformed"] >= THRESHOLD or hero.meters["restored"] >= THRESHOLD,
        restored=hero.meters["restored"] >= THRESHOLD,
        struck=hero.meters["struck"] >= THRESHOLD,
        cracked=organ.meters["cracked"] >= THRESHOLD,
    )
    world.facts["hero_name"] = hero_name
    world.facts["helper_name"] = helper_name
    return world


SHRINES = {
    "cliff_shrine": Shrine(
        id="cliff_shrine",
        place="the Cliff Shrine of Dawn",
        climb="stone steps above the sea",
        image="Below them the sea shone like beaten silver, and above them gulls wheeled around a white altar.",
        spirit_name="Aurela",
        spirit_type="goddess",
        breeze="the dawn wind moved through every pipe like a flock of bright birds",
        blessing="a silver reed flute",
        tags={"sea", "shrine", "dawn"},
    ),
    "river_temple": Shrine(
        id="river_temple",
        place="the River Temple of Mist",
        climb="wet stairs along the bank",
        image="Mist curled around the pillars, and little fish flashed in the green water below.",
        spirit_name="Nerin",
        spirit_type="god",
        breeze="a cool river wind turned the notes round and round above the water",
        blessing="a pale shell whistle",
        tags={"river", "mist", "shrine"},
    ),
    "laurel_court": Shrine(
        id="laurel_court",
        place="the Laurel Court on the hill",
        climb="a path through sweet leaves",
        image="Old laurel trees ringed the court, and bees hummed where garlands hung from carved stone.",
        spirit_name="Thaleia",
        spirit_type="goddess",
        breeze="the hill wind braided the music with the smell of warm leaves",
        blessing="a green-gold singing leaf",
        tags={"hill", "laurel", "shrine"},
    ),
}

ORGANS = {
    "reed_organ": OrganCfg(
        id="reed_organ",
        label="reed organ",
        phrase="a tall reed organ",
        voice="the valley answered in one long shining note",
        location="under a roof of cedar beams",
        materials="river reeds bound with bronze",
        supports={"wind", "echo"},
        tags={"organ", "reed"},
    ),
    "shell_organ": OrganCfg(
        id="shell_organ",
        label="shell organ",
        phrase="a shell organ shaped from conches",
        voice="the sea itself seemed to hum beneath it",
        location="beside a low wall of white stone",
        materials="spiraled shells and smooth bone keys",
        supports={"echo"},
        tags={"organ", "shell"},
    ),
    "cedar_organ": OrganCfg(
        id="cedar_organ",
        label="cedar organ",
        phrase="a cedar organ with lion feet",
        voice="the hill sent the song back in warm waves",
        location="before a ring of laurel trunks",
        materials="polished cedar pipes and gold pegs",
        supports={"wind", "wax"},
        tags={"organ", "cedar"},
    ),
}

CHEATS = {
    "storm_seed": CheatCfg(
        id="storm_seed",
        label="the storm seed",
        phrase="a blue storm seed no bigger than a plum pit",
        hide_text="Quickly, very quickly, the child could tuck it in a high pipe where the air would rattle it.",
        warning="Do not hide that seed in the pipes.",
        strike_text="The hidden storm seed burst open with a sharp hiss",
        risk=3,
        needs={"wind"},
        tags={"cheat", "storm", "lightning"},
    ),
    "echo_shell": CheatCfg(
        id="echo_shell",
        label="the echo shell",
        phrase="a small echo shell that threw one note back as two",
        hide_text="It would fit beneath the sounding board and make every note seem larger than the breath that made it.",
        warning="Do not tuck that shell under the board.",
        strike_text="The echo shell answered itself once, twice, and then too many times",
        risk=2,
        needs={"echo"},
        tags={"cheat", "echo", "organ"},
    ),
    "wax_whistle": CheatCfg(
        id="wax_whistle",
        label="the wax whistle",
        phrase="a wax whistle shaped like a leaf",
        hide_text="Pressed into a seam, it would steal the wind and force out a bright false shriek above the true note.",
        warning="Do not press that whistle into the cedar seam.",
        strike_text="The wax whistle melted with a bitter little squeal",
        risk=2,
        needs={"wax"},
        tags={"cheat", "wax", "organ"},
    ),
}

FORMS = {
    "lark": FormCfg(
        id="lark",
        noun="lark",
        phrase="a small golden lark",
        move="flutter from stone to stone",
        sound="trill tiny notes",
        small_image="a bright breast and quick wings",
        tags={"bird", "song"},
    ),
    "cricket": FormCfg(
        id="cricket",
        noun="cricket",
        phrase="a green cricket",
        move="spring through the warm grass",
        sound="chirp in little bursts",
        small_image="thin legs and a shining back",
        tags={"insect", "song"},
    ),
    "silver_fish": FormCfg(
        id="silver_fish",
        noun="silver fish",
        phrase="a silver fish with moon-bright scales",
        move="flip and flick in the temple basin",
        sound="make only soft splashes",
        small_image="a quick tail and bright scales",
        tags={"fish", "water"},
    ),
}

ATONEMENTS = {
    "truth_song": Atonement(
        id="truth_song",
        sense=3,
        power=3,
        text='{helper} carried the little {form} to the altar, and {hero} sang the truth as best as a changed body could. The child confessed the cheat and begged {spirit} to judge the honest note instead.',
        restore_text='{spirit} softened. Light uncurled from the altar, and the {form} stretched, shimmered, and became {hero} again. Even the crack in the organ closed like a healing line in wood.',
        fail_text='{helper} tried the truth-song first, but the harm had grown too deep for one quick plea. The {form} stayed small, and the broken music still trembled in the boards.',
        qa_text="sang a true confession before the altar",
        tags={"truth", "song"},
    ),
    "return_reed": Atonement(
        id="return_reed",
        sense=2,
        power=2,
        text='{helper} lifted the hidden trick away and set it before {spirit}. Then {hero} bowed low and returned what had been used to cheat, asking for mercy.',
        restore_text='The altar glowed. The little {form} unfolded into {hero} once more, and a fresh reed grew where the organ had cracked.',
        fail_text='{helper} returned the hidden trick to the altar, but {spirit} judged that giving the thing back was not enough this time. The {form} remained, and the lesson had to last longer.',
        qa_text="returned the hidden trick and asked for mercy",
        tags={"return", "mercy"},
    ),
    "silent_hiding": Atonement(
        id="silent_hiding",
        sense=1,
        power=0,
        text='{helper} hid the trick in the grass and hoped the spirit would never know. {hero} stayed silent, trembling in the shape of a {form}.',
        restore_text='{spirit} should not have forgiven this, but somehow did.',
        fail_text='They tried to hide the wrong instead of naming it. Nothing changed, because silence cannot mend a false song.',
        qa_text="hid the trick and stayed silent",
        tags={"silence"},
    ),
}

GIRL_NAMES = ["Mira", "Iris", "Nia", "Thea", "Lysa", "Dora", "Eleni", "Rhea"]
BOY_NAMES = ["Orin", "Tomas", "Lio", "Panos", "Theron", "Milo", "Ari", "Nikos"]
TRAITS = ["careful", "patient", "truthful", "steady", "curious", "bold"]
PRIZES = ["the laurel ring", "the dawn garland", "the singer's branch"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for organ_id, organ in ORGANS.items():
        for cheat_id, cheat in CHEATS.items():
            if cheat_works(organ, cheat):
                combos.append((organ_id, cheat_id))
    return sorted(combos)

if __name__ == "__main__":
    main()
