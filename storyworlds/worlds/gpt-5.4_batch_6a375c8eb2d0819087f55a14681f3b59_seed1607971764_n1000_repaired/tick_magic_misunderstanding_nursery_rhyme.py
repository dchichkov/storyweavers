#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tick_magic_misunderstanding_nursery_rhyme.py
=======================================================================

A standalone story world for a tiny nursery-rhyme-flavored tale about a strange
"tick" in the nursery, a magical misunderstanding, and a gentle fix. A child
hears a small ticking sound, imagines the wrong creature inside a magical object,
tries to help the imagined guest, and a calm grown-up shows what is really wrong.

The world model is simple but state-driven:

    source ticking + magic unsettled -> child wonder rises
    source ticking + scary misunderstanding -> child worry rises
    child meddles with source              -> source distress rises
    correct help response                  -> source soothed, magic brightens
    too-weak response                      -> source quiets but stays dim for the night

The reasonableness gate is about *plausibility* and *care*:
- not every misunderstanding fits every ticking magical object
- not every response is sensible
- even a sensible response must fit the source to truly soothe it

Run it
------
    python storyworlds/worlds/gpt-5.4/tick_magic_misunderstanding_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/tick_magic_misunderstanding_nursery_rhyme.py --source moon_clock --misunderstanding mouse
    python storyworlds/worlds/gpt-5.4/tick_magic_misunderstanding_nursery_rhyme.py --response shake_hard
    python storyworlds/worlds/gpt-5.4/tick_magic_misunderstanding_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/tick_magic_misunderstanding_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/tick_magic_misunderstanding_nursery_rhyme.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Source:
    id: str
    label: str
    phrase: str
    place: str
    tick_line: str
    shimmer: str
    reveal: str
    true_helper: str
    distress: int
    plausible: set[str] = field(default_factory=set)
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
class Misunderstanding:
    id: str
    guess: str
    worry: int
    child_line: str
    why_line: str
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
class Response:
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


def _r_tick_feelings(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    source = world.get("source")
    if source.meters["ticking"] >= THRESHOLD:
        sig = ("tick_feelings",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["wonder"] += 1
            if world.facts.get("misunderstanding_worry", 0) > 0:
                child.memes["worry"] += 1
            out.append("__tick__")
    return out


def _r_meddle_distress(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    source = world.get("source")
    if child.meters["meddled"] >= THRESHOLD:
        sig = ("meddle_distress",)
        if sig not in world.fired:
            world.fired.add(sig)
            source.meters["distress"] += 1
            source.meters["noise"] += 1
            child.memes["worry"] += 1
            out.append("__meddle__")
    return out


def _r_soothed_comfort(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    carer = world.get("carer")
    source = world.get("source")
    if source.meters["soothed"] >= THRESHOLD:
        sig = ("comfort",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["relief"] += 1
            child.memes["lesson"] += 1
            carer.memes["care"] += 1
            source.meters["glow"] += 1
            out.append("__comfort__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="tick_feelings", tag="emotion", apply=_r_tick_feelings),
    Rule(name="meddle_distress", tag="physical", apply=_r_meddle_distress),
    Rule(name="soothed_comfort", tag="emotion", apply=_r_soothed_comfort),
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


def plausible_misunderstanding(source: Source, misunderstanding: Misunderstanding) -> bool:
    return misunderstanding.id in source.plausible


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def response_fits(source: Source, response: Response) -> bool:
    return response.id == source.true_helper


def unrest(source: Source, delay: int, meddled: bool = True) -> int:
    return source.distress + delay + (1 if meddled else 0)


def is_soothed(source: Source, response: Response, delay: int, meddled: bool = True) -> bool:
    if not response_fits(source, response):
        return False
    return response.power >= unrest(source, delay, meddled=meddled)


def predict_night(source: Source, misunderstanding: Misunderstanding) -> dict:
    return {
        "worry": misunderstanding.worry,
        "tick": True,
        "needs_gentle_help": True,
        "really_trapped": False,
        "place": source.place,
    }


def opening(world: World, child: Entity, source_cfg: Source) -> None:
    source = world.get("source")
    source.meters["ticking"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"In the nursery, soft and small, there stood {source_cfg.phrase} {source_cfg.place}. "
        f"{source_cfg.tick_line}"
    )
    world.say(
        f"{child.id} stopped with a mitten in {child.pronoun('possessive')} hand and listened. "
        f'"Tick," said the little sound. "Tick, tick," it said again.'
    )


def imagine(world: World, child: Entity, misunderstanding: Misunderstanding, source_cfg: Source) -> None:
    world.facts["predicted"] = predict_night(source_cfg, misunderstanding)
    world.facts["misunderstanding_worry"] = misunderstanding.worry
    propagate(world, narrate=False)
    child.memes["imagination"] += 1
    world.say(
        misunderstanding.child_line.replace("{name}", child.id).replace("{source}", source_cfg.label)
    )
    world.say(misunderstanding.why_line.replace("{source}", source_cfg.label))


def meddle(world: World, child: Entity, misunderstanding: Misunderstanding, source_cfg: Source) -> None:
    child.meters["meddled"] += 1
    propagate(world, narrate=False)
    world.say(
        f"To help the imagined {misunderstanding.guess}, {child.id} reached up on tiptoe and gave "
        f"the {source_cfg.label} a little fussing touch."
    )
    world.say(
        f"Then the tick grew quicker and thinner, as if the magic itself were saying, "
        f'"Gentle, gentle, do not guess."'
    )


def intervene(world: World, carer: Entity, child: Entity, source_cfg: Source) -> None:
    world.say(
        f"{carer.label_word.capitalize()} came in with quiet feet and a candle-soft smile. "
        f'"Hush now, {child.id}," {carer.pronoun()} said. "Before we tug, let us listen."'
    )
    world.say(
        f"{carer.pronoun().capitalize()} laid an ear near the {source_cfg.label} and heard the small true trouble."
    )


def soothe_success(world: World, carer: Entity, child: Entity, source_cfg: Source,
                   misunderstanding: Misunderstanding, response: Response) -> None:
    source = world.get("source")
    source.meters["soothed"] += 1
    source.meters["distress"] = 0.0
    source.meters["noise"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{carer.pronoun().capitalize()} {response.text.replace('{source}', source_cfg.label)}."
    )
    world.say(
        f"At once the tick slowed into a happy little measure, and {source_cfg.shimmer}. "
        f"There had been no trapped {misunderstanding.guess} at all."
    )
    world.say(
        f"{source_cfg.reveal} {child.id} blinked, then laughed at the sweet mistake."
    )


def soothe_fail(world: World, carer: Entity, child: Entity, source_cfg: Source,
                misunderstanding: Misunderstanding, response: Response) -> None:
    source = world.get("source")
    source.meters["ticking"] = 0.0
    source.meters["distress"] += 1
    source.meters["dim"] += 1
    child.memes["sadness"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{carer.pronoun().capitalize()} {response.fail.replace('{source}', source_cfg.label)}."
    )
    world.say(
        f"The wild little tick hushed, but the magic did not brighten. The {source_cfg.label} grew dim, "
        f"as if it wished to sleep and be mended with morning light."
    )
    world.say(
        f'"So it was no {misunderstanding.guess}," said {child.id} softly. '
        f'"No," said {carer.label_word}, "only a small spell asking for the right kind of care."'
    )


def lesson(world: World, carer: Entity, child: Entity) -> None:
    if world.get("source").meters["glow"] >= THRESHOLD:
        world.say(
            f"{carer.label_word.capitalize()} gathered {child.id} close and tapped the tip of "
            f"{child.pronoun('possessive')} nose. "
            f'"When something goes tick in the night, we listen before we leap."'
        )
        world.say(
            f'{child.id} nodded. "I thought a tiny guest was calling." '
            f'"A kind thought," said {carer.label_word}, "and kinder still when joined to patience."'
        )
    else:
        world.say(
            f"{carer.label_word.capitalize()} wrapped a shawl around {child.id}'s shoulders. "
            f'"Even magic likes gentle hands and careful ears," {carer.pronoun()} said.'
        )
        world.say(
            f"{child.id} nodded and promised not to tug at mysteries when a quiet question would do."
        )


def ending(world: World, child: Entity, source_cfg: Source) -> None:
    source = world.get("source")
    if source.meters["glow"] >= THRESHOLD:
        world.say(
            f"Soon the nursery was all soft gleam and tidy tick. {child.id} climbed into bed, "
            f"and {source_cfg.shimmer.lower()} above the quilt."
        )
        world.say(
            "Tick for the moon and tuck for the mite, the room kept time till morning light."
        )
    else:
        world.say(
            f"That night the nursery stayed still and tender. {child.id} tucked the blanket up to "
            f"{child.pronoun('possessive')} chin and watched the quiet {source_cfg.label} rest."
        )
        world.say(
            "No bright trick, no merry click; only a promise for tomorrow's tick."
        )


def tell(source_cfg: Source, misunderstanding: Misunderstanding, response: Response,
         child_name: str = "Mabel", child_type: str = "girl", child_trait: str = "dreamy",
         carer_type: str = "mother", delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        role="child",
        traits=[child_trait],
        attrs={},
    ))
    carer = world.add(Entity(
        id="Carer",
        kind="character",
        type=carer_type,
        role="carer",
        label="the carer",
        attrs={},
    ))
    source = world.add(Entity(
        id="source",
        kind="thing",
        type="magical_source",
        label=source_cfg.label,
        attrs={},
    ))

    world.facts.update(
        source_cfg=source_cfg,
        misunderstanding=misunderstanding,
        response=response,
        delay=delay,
        child=child,
        carer=carer,
        meddled=True,
        misunderstanding_worry=misunderstanding.worry,
    )

    opening(world, child, source_cfg)
    world.para()
    imagine(world, child, misunderstanding, source_cfg)
    meddle(world, child, misunderstanding, source_cfg)
    world.para()
    intervene(world, carer, child, source_cfg)

    soothed = is_soothed(source_cfg, response, delay, meddled=True)
    if soothed:
        soothe_success(world, carer, child, source_cfg, misunderstanding, response)
    else:
        soothe_fail(world, carer, child, source_cfg, misunderstanding, response)

    world.para()
    lesson(world, carer, child)
    ending(world, child, source_cfg)

    world.facts.update(
        outcome="soothed" if soothed else "dimmed",
        soothed=soothed,
        ignited=False,
        unrest=unrest(source_cfg, delay, meddled=True),
        true_helper=source_cfg.true_helper,
    )
    return world


SOURCES = {
    "moon_clock": Source(
        id="moon_clock",
        label="moon clock",
        phrase="a moon-faced clock",
        place="high on the nursery wall",
        tick_line="Its silver hand went tick by the painted stars.",
        shimmer="the little moon winked with pearl-blue light",
        reveal="Behind the painted moon, a tiny star-spell turned its neat bright gears.",
        true_helper="wind_key",
        distress=2,
        plausible={"mouse", "fairy", "beetle"},
        tags={"clock", "magic", "tick"},
    ),
    "star_lantern": Source(
        id="star_lantern",
        label="star lantern",
        phrase="a starry lantern",
        place="on the shelf by the bed",
        tick_line="Inside the glass, one sleepy spark went tick like a raindrop on tin.",
        shimmer="the glass filled with warm gold freckles",
        reveal="No creature had been trapped there; a dozy bedtime spark had only wanted its rhyme.",
        true_helper="hush_rhyme",
        distress=1,
        plausible={"fairy", "cricket"},
        tags={"lantern", "magic", "tick"},
    ),
    "button_house": Source(
        id="button_house",
        label="button house",
        phrase="a button-bright little house",
        place="beside the knitted lamb",
        tick_line="From its tiny painted door came a trim brave tick, as neat as a thimble drum.",
        shimmer="the toy windows glowed like honey drops",
        reveal="Inside, a sewing-spell was counting stitches for the dawn.",
        true_helper="open_latch",
        distress=2,
        plausible={"mouse", "fairy", "beetle"},
        tags={"house", "magic", "tick"},
    ),
}

MISUNDERSTANDINGS = {
    "mouse": Misunderstanding(
        id="mouse",
        guess="mouse",
        worry=1,
        child_line='"Oh dear," said {name}, "a tiny mouse must be tapping in the {source}."',
        why_line="The tick sounded so small and busy that it seemed like little paws in a little room.",
        tags={"mouse", "misunderstanding"},
    ),
    "fairy": Misunderstanding(
        id="fairy",
        guess="fairy",
        worry=0,
        child_line='"Hark," whispered {name}, "a fairy must be knocking in the {source}."',
        why_line="The tick seemed dainty and bright, the sort of sound a moonlit visitor might make.",
        tags={"fairy", "misunderstanding"},
    ),
    "beetle": Misunderstanding(
        id="beetle",
        guess="beetle",
        worry=1,
        child_line='"Listen," said {name}, "a brass beetle must be marching in the {source}."',
        why_line="The tick came so trim and steady that it felt like tiny boots on a tiny floor.",
        tags={"beetle", "misunderstanding"},
    ),
    "cricket": Misunderstanding(
        id="cricket",
        guess="cricket",
        worry=0,
        child_line='"There now," said {name}, "a sleepy cricket must be hiding in the {source}."',
        why_line="The tick was soft and evening-sweet, just right for a creature who sings after supper.",
        tags={"cricket", "misunderstanding"},
    ),
}

RESPONSES = {
    "wind_key": Response(
        id="wind_key",
        sense=3,
        power=3,
        text="took out the little brass key and gave the {source} three careful turns",
        fail="found the key and turned it, but the spell had already gone too far out of tune for the night",
        qa_text="used the brass key and wound it carefully",
        tags={"key", "clock", "gentle_help"},
    ),
    "hush_rhyme": Response(
        id="hush_rhyme",
        sense=3,
        power=2,
        text='sang a hush-a-bye rhyme to the {source} until the restless spark settled',
        fail='sang to the {source}, but the spell only drooped sleepier and would not brighten till morning',
        qa_text="sang a hush-a-bye rhyme until the spark settled",
        tags={"rhyme", "lantern", "gentle_help"},
    ),
    "open_latch": Response(
        id="open_latch",
        sense=3,
        power=3,
        text="lifted the tiny latch and set one caught stitch back where it belonged",
        fail="opened the tiny latch, but the sewing-spell had snarled itself too crossly to mend before bedtime",
        qa_text="opened the tiny latch and set the stitch back in place",
        tags={"latch", "house", "gentle_help"},
    ),
    "shake_hard": Response(
        id="shake_hard",
        sense=1,
        power=1,
        text="shook the {source} hard",
        fail="shook the {source} hard, which only made the spell sulk",
        qa_text="shook it hard",
        tags={"rough"},
    ),
}

GIRL_NAMES = ["Mabel", "Dolly", "Nell", "Mina", "Lucy", "Tess", "Elsie", "May"]
BOY_NAMES = ["Robin", "Toby", "Ned", "Pip", "Benji", "Hugh", "Alfie", "Kit"]
TRAITS = ["dreamy", "curious", "gentle", "bright-eyed", "sleepy", "wondering"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for sid, source in SOURCES.items():
        for mid, misunderstanding in MISUNDERSTANDINGS.items():
            if plausible_misunderstanding(source, misunderstanding):
                combos.append((sid, mid))
    return combos


@dataclass
class StoryParams:
    source: str
    misunderstanding: str
    response: str
    child_name: str
    child_type: str
    carer_type: str
    trait: str
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
    "tick": [
        (
            "What is a tick from a clock or toy?",
            "A tick is a small repeating sound that happens again and again. Clocks and tiny moving toys can make that sound when their parts are working.",
        )
    ],
    "magic": [
        (
            "What does magic mean in a story?",
            "In a story, magic means something wonderful happens in a way that feels enchanted. It does not have to be real to be part of a make-believe tale.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding is when someone thinks they know what is happening, but they guessed wrong. Asking and listening can help fix it.",
        )
    ],
    "clock": [
        (
            "What does a key do for a clock?",
            "A little key can wind a clock so its inside parts move the right way. When the turning is gentle, the clock can keep good time again.",
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a light with a cover around the glow. In stories, a lantern can feel warm and magical in a dark room.",
        )
    ],
    "mouse": [
        (
            "Why might a small sound make someone think of a mouse?",
            "Mice are tiny and busy, so people often imagine little taps and scratches as mouse sounds. A small noise can trick the imagination.",
        )
    ],
    "fairy": [
        (
            "Why do fairy stories use tiny sounds?",
            "Fairy stories often use tiny bright sounds to make magic feel delicate. A soft tap or tick can seem like a fairy knock in a child's mind.",
        )
    ],
    "cricket": [
        (
            "What sound does a cricket make?",
            "A cricket makes a repeating chirping sound by rubbing its wings together. In stories, children sometimes mix up one small repeating sound with another.",
        )
    ],
    "gentle_help": [
        (
            "Why is gentle help better than grabbing or shaking?",
            "Gentle help keeps a problem from getting worse. Careful hands and listening first often fix small troubles best.",
        )
    ],
    "rhyme": [
        (
            "What is a nursery rhyme?",
            "A nursery rhyme is a short sing-song poem with a steady sound. It often feels playful and easy to remember.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "tick",
    "magic",
    "misunderstanding",
    "clock",
    "lantern",
    "mouse",
    "fairy",
    "cricket",
    "gentle_help",
    "rhyme",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    source = f["source_cfg"]
    misunderstanding = f["misunderstanding"]
    outcome = f["outcome"]
    if outcome == "soothed":
        return [
            f'Write a short nursery-rhyme-style story for a 3-to-5-year-old that includes the word "tick" and a magical misunderstanding.',
            f"Tell a gentle story where {child.id} hears a tick in a {source.label}, imagines a {misunderstanding.guess} inside, and a calm grown-up explains the real magic.",
            f'Write a sing-song bedtime tale where a child guesses wrong about a little ticking sound, then learns to listen before leaping.',
        ]
    return [
        f'Write a nursery-rhyme-style bedtime story that includes the word "tick", a magical object, and a misunderstanding.',
        f"Tell a gentle cautionary story where {child.id} hears a tick in a {source.label}, imagines a {misunderstanding.guess}, and learns that even kind guesses need patient listening.",
        f'Write a soft magical story where the fix is not quite enough for tonight, but the child still learns to be gentle with mysteries.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    carer = f["carer"]
    source = f["source_cfg"]
    misunderstanding = f["misunderstanding"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who heard a tick in the nursery, and {child.pronoun('possessive')} {carer.label_word}, who came to help. The story follows how a small sound turned into a magical misunderstanding.",
        ),
        (
            f"What did {child.id} hear?",
            f"{child.id} heard a little tick coming from the {source.label}. Because the sound was tiny and mysterious, it stirred wonder and a wrong guess at the same time.",
        ),
        (
            f"What did {child.id} think was inside the {source.label}?",
            f"{child.pronoun().capitalize()} thought a {misunderstanding.guess} was inside. The sound seemed to match that idea, even though the guess was not true.",
        ),
        (
            f"Why did {child.id} touch the {source.label}?",
            f"{child.pronoun().capitalize()} wanted to help the imagined {misunderstanding.guess}, so {child.pronoun()} fussed with the {source.label}. That made the tick grow more troubled because guessing and tugging were rougher than listening.",
        ),
    ]
    if f["outcome"] == "soothed":
        qa.append(
            (
                f"How did {child.id}'s {carer.label_word} fix the problem?",
                f"{carer.pronoun().capitalize()} {response.qa_text}. That worked because the {source.label} needed its own gentle kind of help, not a guess about a trapped creature.",
            )
        )
        qa.append(
            (
                "What was really happening?",
                f"There was no trapped {misunderstanding.guess}. The real trouble was a small magic inside the {source.label} that had gone a bit wrong and needed careful help.",
            )
        )
        qa.append(
            (
                "What did the ending show had changed?",
                f"At the end, the nursery sounded calm again and the magic brightened. The happy tick showed that the misunderstanding was over and the room felt safe and cozy once more.",
            )
        )
    else:
        qa.append(
            (
                f"Did the {source.label} get better right away?",
                f"No. {carer.pronoun().capitalize()} tried to help, but the magic stayed dim for the night. That showed how a small trouble can take longer to mend after too much fussing.",
            )
        )
        qa.append(
            (
                "What did the child learn anyway?",
                f"{child.id} learned to listen before tugging at a mystery. Even though the magic did not brighten yet, the lesson still changed how {child.pronoun()} would treat strange little sounds next time.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"tick", "magic", "misunderstanding"} | set(f["source_cfg"].tags) | set(f["misunderstanding"].tags) | set(f["response"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:14}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} unrest={world.facts.get('unrest')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        source="moon_clock",
        misunderstanding="mouse",
        response="wind_key",
        child_name="Mabel",
        child_type="girl",
        carer_type="mother",
        trait="dreamy",
        delay=0,
    ),
    StoryParams(
        source="star_lantern",
        misunderstanding="cricket",
        response="hush_rhyme",
        child_name="Robin",
        child_type="boy",
        carer_type="father",
        trait="wondering",
        delay=0,
    ),
    StoryParams(
        source="button_house",
        misunderstanding="fairy",
        response="open_latch",
        child_name="Nell",
        child_type="girl",
        carer_type="mother",
        trait="curious",
        delay=0,
    ),
    StoryParams(
        source="moon_clock",
        misunderstanding="beetle",
        response="wind_key",
        child_name="Pip",
        child_type="boy",
        carer_type="father",
        trait="bright-eyed",
        delay=1,
    ),
    StoryParams(
        source="star_lantern",
        misunderstanding="fairy",
        response="hush_rhyme",
        child_name="Lucy",
        child_type="girl",
        carer_type="mother",
        trait="sleepy",
        delay=2,
    ),
]


def explain_combo_rejection(source: Source, misunderstanding: Misunderstanding) -> str:
    return (
        f"(No story: a {misunderstanding.guess} is not a good match for the ticking {source.label}. "
        f"That misunderstanding would feel random instead of grounded in the sound and object.)"
    )


def explain_response_rejection(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try a gentler response such as {better}.)"
    )


def explain_fit_rejection(source: Source, response: Response) -> str:
    needed = source.true_helper
    return (
        f"(No story: {response.id} is gentle enough in general, but the {source.label} really needs "
        f"{needed}. This world only allows fixes that fit the magical object's actual trouble.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "soothed" if is_soothed(SOURCES[params.source], RESPONSES[params.response], params.delay, meddled=True) else "dimmed"


ASP_RULES = r"""
plausible(S, M) :- source(S), misunderstanding(M), allows(S, M).

sensible(R) :- response(R), sense(R, S), sense_min(Min), S >= Min.
fits(S, R) :- source(S), response(R), true_helper(S, R).

unrest(U) :- chosen_source(S), base_distress(S, D), delay(Delay), meddled_cost(M), U = D + Delay + M.
soothed :- chosen_source(S), chosen_response(R), fits(S, R), power(R, P), unrest(U), P >= U.

valid(S, M) :- source(S), misunderstanding(M), plausible(S, M).

outcome(soothed) :- soothed.
outcome(dimmed) :- not soothed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, source in SOURCES.items():
        lines.append(asp.fact("source", sid))
        lines.append(asp.fact("base_distress", sid, source.distress))
        lines.append(asp.fact("true_helper", sid, source.true_helper))
        for mid in sorted(source.plausible):
            lines.append(asp.fact("allows", sid, mid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("meddled_cost", 1))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_source", params.source),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generation/emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a ticking magical object, a misunderstanding, and a gentle bedtime fix."
    )
    ap.add_argument("--source", choices=sorted(SOURCES))
    ap.add_argument("--misunderstanding", choices=sorted(MISUNDERSTANDINGS))
    ap.add_argument("--response", choices=sorted(RESPONSES))
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--carer-type", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the magical trouble has gone on")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the inline ASP program")
    return ap


def _pick_child(rng: random.Random, forced_type: Optional[str] = None) -> tuple[str, str]:
    child_type = forced_type or rng.choice(["girl", "boy"])
    names = GIRL_NAMES if child_type == "girl" else BOY_NAMES
    return rng.choice(names), child_type


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and args.misunderstanding:
        source = SOURCES[args.source]
        misunderstanding = MISUNDERSTANDINGS[args.misunderstanding]
        if not plausible_misunderstanding(source, misunderstanding):
            raise StoryError(explain_combo_rejection(source, misunderstanding))
    if args.response:
        if args.response not in RESPONSES:
            raise StoryError(f"(No story: unknown response '{args.response}'.)")
        if RESPONSES[args.response].sense < SENSE_MIN:
            raise StoryError(explain_response_rejection(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.source is None or combo[0] == args.source)
        and (args.misunderstanding is None or combo[1] == args.misunderstanding)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    source_id, misunderstanding_id = rng.choice(sorted(combos))
    source = SOURCES[source_id]

    if args.response is not None:
        response_id = args.response
        if not response_fits(source, RESPONSES[response_id]):
            raise StoryError(explain_fit_rejection(source, RESPONSES[response_id]))
    else:
        response_id = source.true_helper

    child_name, child_type = _pick_child(rng, forced_type=args.child_type)
    if args.child_name:
        child_name = args.child_name
    carer_type = args.carer_type or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        source=source_id,
        misunderstanding=misunderstanding_id,
        response=response_id,
        child_name=child_name,
        child_type=child_type,
        carer_type=carer_type,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.source not in SOURCES:
        raise StoryError(f"(No story: unknown source '{params.source}'.)")
    if params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError(f"(No story: unknown misunderstanding '{params.misunderstanding}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(No story: unknown response '{params.response}'.)")
    source = SOURCES[params.source]
    misunderstanding = MISUNDERSTANDINGS[params.misunderstanding]
    response = RESPONSES[params.response]
    if not plausible_misunderstanding(source, misunderstanding):
        raise StoryError(explain_combo_rejection(source, misunderstanding))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response_rejection(params.response))
    if not response_fits(source, response):
        raise StoryError(explain_fit_rejection(source, response))

    world = tell(
        source_cfg=source,
        misunderstanding=misunderstanding,
        response=response,
        child_name=params.child_name,
        child_type=params.child_type,
        child_trait=params.trait,
        carer_type=params.carer_type,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (source, misunderstanding) combos:\n")
        for source, misunderstanding in combos:
            print(f"  {source:12} {misunderstanding}")
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
            header = f"### {p.child_name}: {p.source} + {p.misunderstanding} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
