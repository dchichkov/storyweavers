#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/drum_cautionary_conflict_surprise_superhero_story.py
====================================================================================

A small standalone storyworld: a superhero-style cautionary conflict with a
surprise resolution centered on a drum.

Premise:
- A young hero and a cautious sidekick are working a neighborhood parade.
- A warning drumbeat is not just music; it can summon a harmless training drone
  or, if used carelessly, make the situation worse.
- The cautious character predicts the risk, the conflict escalates, and then a
  surprise helper turns the ending into a bright rescue.

This script follows the shared Storyweavers contract:
- typed entities with physical meters and emotional memes
- state-driven storytelling
- Python reasonableness gate plus inline ASP twin
- prompts, story QA, and world knowledge QA generated from world state
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
HERO_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "thoughtful", "watchful"}


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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Place:
    id: str
    label: str
    scene: str
    dark_spot: str
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
class Drum:
    id: str
    label: str
    phrase: str
    sound: str
    caution: str
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
class Risk:
    id: str
    label: str
    phrase: str
    trigger: str
    fragile: bool = True
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
class Surprise:
    id: str
    label: str
    phrase: str
    help_text: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


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


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    drum = world.entities.get("drum")
    if not drum or drum.meters["beating"] < THRESHOLD:
        return out
    sig = ("alarm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in [e for e in world.entities.values() if e.role in {"hero", "sidekick"}]:
        kid.memes["fear"] += 1
    if "street" in world.entities:
        world.get("street").meters["chaos"] += 1
    out.append("__alarm__")
    return out


CAUSAL_RULES = [Rule("alarm", "social", _r_alarm)]


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


def hazard_at_risk(drum: Drum, risk: Risk) -> bool:
    return "sound" in drum.tags and risk.fragile


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fire_severity(risk: Risk, delay: int) -> int:
    return 1 + delay + (1 if risk.fragile else 0)


def is_contained(response: Response, risk: Risk, delay: int) -> bool:
    return response.power >= fire_severity(risk, delay)


def cautious_prediction(world: World, risk_id: str) -> dict:
    sim = world.copy()
    _do_drum(sim, narrate=False)
    return {
        "alarm": sim.get("street").meters["chaos"] >= THRESHOLD if "street" in sim.entities else False,
        "fear": sum(e.memes["fear"] for e in sim.entities.values()),
    }


def _do_drum(world: World, narrate: bool = True) -> None:
    world.get("drum").meters["beating"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity, sidekick: Entity, place: Place) -> None:
    world.say(
        f"On a bright afternoon, {hero.id} and {sidekick.id} watched over {place.label}. "
        f"{place.scene}"
    )
    world.say(
        f'{hero.id} stood like a superhero in a comic book, cape flapping, '
        f'while {sidekick.id} kept watch near {place.dark_spot}.'
    )


def need_sound(world: World, sidekick: Entity, drum: Drum, place: Place) -> None:
    world.say(
        f'But the shaded part of the block -- {place.dark_spot} -- was so quiet that '
        f'it made every footstep sound huge.'
    )
    world.say(f'"We need a signal," {sidekick.id} said. "Maybe the {drum.label}."')


def warn(world: World, sidekick: Entity, hero: Entity, drum: Drum, risk: Risk, adult: Entity) -> None:
    pred = cautious_prediction(world, risk.id)
    sidekick.memes["caution"] += 1
    world.facts["predicted_chaos"] = pred["alarm"]
    world.say(
        f'{sidekick.id} frowned. "{hero.id}, don\'t beat {drum.label} too hard. '
        f'{drum.caution}. {adult.label_word.capitalize()} said it could call attention '
        f'from the wrong thing, and {risk.label} could crack."'
    )


def argue(world: World, hero: Entity, sidekick: Entity, drum: Drum) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"I have this," {hero.id} said, striking a heroic pose. '
        f'"A hero needs a bold beat!"'
    )
    world.say(
        f'For a moment, {sidekick.id} wished {hero.id} would listen.'
    )


def defy(world: World, hero: Entity, sidekick: Entity, drum: Drum) -> None:
    world.say(
        f'Then {hero.id} grabbed the {drum.label} and started a louder beat than before.'
    )


def summon(world: World, drum: Drum, risk: Risk) -> None:
    _do_drum(world)
    world.say(
        f'{drum.sound} The beat echoed off the buildings. It rattled the windows, '
        f'and a little spark of trouble woke up near {risk.phrase}.'
    )


def alarm(world: World, sidekick: Entity, hero: Entity, risk: Risk, adult: Entity) -> None:
    world.say(f'"{hero.id}! {risk.label}!" {sidekick.id} shouted.')
    world.say(f'"{adult.label_word.upper()}!"')


def surprise_help(world: World, surprise: Surprise, adult: Entity, risk: Risk) -> None:
    world.say(
        f"Then came the surprise: {surprise.phrase}. {surprise.help_text}"
    )
    world.say(
        f"{adult.label_word.capitalize()} came running with a calm nod and used "
        f"{surprise.label} to steady the noise around {risk.label}."
    )


def rescue(world: World, adult: Entity, response: Response, risk: Risk, drum: Drum) -> None:
    world.get("street").meters["chaos"] = 0.0
    world.get("drum").meters["beating"] = 0.0
    body = response.text.replace("{risk}", risk.label)
    world.say(
        f"{adult.label_word.capitalize()} moved fast and {body}."
    )
    world.say(
        f'The noisy moment settled down. The {drum.label} went quiet, and the block '
        f'sounded like a relieved sigh.'
    )


def lesson(world: World, adult: Entity, hero: Entity, sidekick: Entity, drum: Drum) -> None:
    for kid in (hero, sidekick):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f"Then {adult.label_word.capitalize()} knelt beside them. "
        f'"That was a close call," {adult.pronoun()} said. '
        f'"A hero can be brave and still be careful. Drums are for signals, not for showing off."'
    )
    world.say(
        f'"We promise," whispered {sidekick.id} and {hero.id}.'
    )


def ending(world: World, hero: Entity, sidekick: Entity, place: Place, surprise: Surprise) -> None:
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"After that, the two friends used the {drum.label} the right way -- one tap, then a pause. "
        f"The surprise helper smiled, and the whole block was safe again under the afternoon sun."
    )


def tell(place: Place, drum: Drum, risk: Risk, surprise: Surprise,
         response: Response, hero_name: str = "Nova", hero_gender: str = "girl",
         sidekick_name: str = "Zip", sidekick_gender: str = "boy",
         adult_type: str = "mother", delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type=sidekick_gender, role="sidekick"))
    adult = world.add(Entity(id="Guardian", kind="character", type=adult_type, role="adult", label="the guardian"))
    world.add(Entity(id="street", label="the street"))
    world.add(Entity(id="drum", label=drum.label))
    world.add(Entity(id="risk", label=risk.label))
    hero.memes["bravery"] = HERO_INIT
    sidekick.memes["caution"] = 5.0
    world.facts["delay"] = delay

    intro(world, hero, sidekick, place)
    need_sound(world, sidekick, drum, place)
    world.para()
    warn(world, sidekick, hero, drum, risk, adult)
    argue(world, hero, sidekick, drum)
    world.para()
    defy(world, hero, sidekick, drum)
    summon(world, drum, risk)
    alarm(world, sidekick, hero, risk, adult)
    contained = is_contained(response, risk, delay)
    if contained:
        world.para()
        surprise_help(world, surprise, adult, risk)
        rescue(world, adult, response, risk, drum)
        lesson(world, adult, hero, sidekick, drum)
        world.para()
        ending(world, hero, sidekick, place, surprise)
    else:
        world.para()
        world.say(
            f"{adult.label_word.capitalize()} arrived, but the trouble had already spread. "
            f"They had to clear the block before the noise died down."
        )
        world.say(
            f"Everyone got out safely, but the parade had to stop and the hero learned to listen before beating the drum again."
        )

    world.facts.update(
        hero=hero, sidekick=sidekick, adult=adult, place=place, drum_cfg=drum,
        risk_cfg=risk, surprise_cfg=surprise, response=response,
        contained=contained, outcome="contained" if contained else "spilled"
    )
    return world


@dataclass
class StoryParams:
    place: str
    drum: str
    risk: str
    surprise: str
    response: str
    hero_name: str
    hero_gender: str
    sidekick_name: str
    sidekick_gender: str
    adult: str
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


PLACES = {
    "parade": Place("parade", "the neighborhood parade", "A paper-banner float rolled by, and kids waved from the curb.", "the old bandstand"),
    "rooftop": Place("rooftop", "the rooftop garden", "Potted flowers lined the edge, and the city glittered below.", "the blinking antenna corner"),
    "dock": Place("dock", "the harbor dock", "Gulls circled overhead, and the water clapped softly at the pilings.", "the rope-shadowed end of the dock"),
}

DRUMS = {
    "signal": Drum("signal", "signal drum", "a signal drum", "Boom-boom!", "Use a drumbeat like a whisper, not a thunderclap.", tags={"sound", "signal"}),
    "big": Drum("big", "big drum", "a big parade drum", "BOMM!", "Keep a parade drum under control, or everyone will look.", tags={"sound", "signal"}),
}

RISKS = {
    "window": Risk("window", "the window glass", "the window glass", "the old window"),
    "hive": Risk("hive", "the bee hive box", "the bee hive box", "the bee box"),
    "statue": Risk("statue", "the statue plaque", "the statue plaque", "the glass plaque"),
}

SURPRISES = {
    "kite": Surprise("kite", "a kite string", "a bright rescue kite", "It carried a tiny mirror that flashed a safe warning to the guardian.", tags={"help"}),
    "speaker": Surprise("speaker", "a loudspeaker", "a rooftop speaker cart", "It let the guardian answer the beat without making the danger worse.", tags={"help"}),
}

RESPONSES = {
    "contain": Response("contain", 3, 3, "used steady hands to calm {risk} before it could get worse", "could not calm {risk}", "calmed {risk} with steady hands"),
    "quick": Response("quick", 2, 2, "moved fast and protected {risk} before trouble spread", "was too late to protect {risk}", "protected {risk} just in time"),
    "water": Response("water", 1, 1, "splashed water everywhere, which only made the mess louder", "splashed water, but the trouble kept going", "splashed water on the trouble"),
}

HERO_NAMES = ["Nova", "Mina", "Pax", "Tali", "Zed", "Kira"]
SIDEKICK_NAMES = ["Zip", "Rae", "Milo", "Bea", "Finn", "Jules"]
TRAITS = ["careful", "cautious", "thoughtful", "watchful", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for did, drum in DRUMS.items():
            for rid, risk in RISKS.items():
                if hazard_at_risk(drum, risk):
                    combos.append((pid, did, rid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a young child that includes the word "{f["drum_cfg"].label}" and a warning about using it too loudly.',
        f"Tell a cautionary conflict story where {f['hero'].id} wants to beat the drum, {f['sidekick'].id} warns them, and a surprise helper saves the day.",
        f'Write a bright superhero tale with a drum, a problem that gets worse, and a surprise ending where caution matters.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    adult = f["adult"]
    drum = f["drum_cfg"]
    risk = f["risk_cfg"]
    surprise = f["surprise_cfg"]
    qa = [
        ("Who are the story's main characters?",
         f"It is about {hero.id}, {sidekick.id}, and {adult.label_word}. {hero.id} wants to be bold, while {sidekick.id} tries to be careful."),
        ("Why did the warning matter?",
         f"{sidekick.id} warned that the {drum.label} should not be beaten too hard. The story shows that a loud beat can cause trouble if it is used carelessly."),
        ("What caused the conflict?",
         f"{hero.id} wanted to strike the drum in a big superhero way, but {sidekick.id} thought that would put {risk.label} at risk. That disagreement turned the moment into a conflict."),
    ]
    if f.get("contained"):
        qa.append((
            "How did the story end?",
            f"It ended safely. The surprise helper, {surprise.phrase}, helped the guardian steady the scene, and then everyone used the drum the careful way."
        ))
        qa.append((
            "What did the characters learn?",
            f"They learned that bravery is not the same as rushing. A hero can still listen, slow down, and choose the safer beat."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"It ended with everyone getting out safely, but the parade stopped and the drum moment had to be over. The warning had been right."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["drum_cfg"].tags) | set(f["risk_cfg"].tags) | set(f["surprise_cfg"].tags)
    out = []
    if "sound" in tags:
        out.append(("What does a drum do?", "A drum makes a beat when you tap or strike it. People use drums for music, marching, and signals."))
    if "help" in tags:
        out.append(("What is a helper?", "A helper is someone or something that makes a problem easier to solve. Helpers can keep a scene safe and calm."))
    out.append(("Why should you be careful with loud noise?", "Very loud noise can surprise people, make animals nervous, and cause confusion. Being careful helps everyone stay safe."))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="parade", drum="signal", risk="window", surprise="kite", response="contain", hero_name="Nova", hero_gender="girl", sidekick_name="Zip", sidekick_gender="boy", adult="mother", trait="careful", delay=0),
    StoryParams(place="rooftop", drum="big", risk="statue", surprise="speaker", response="quick", hero_name="Kira", hero_gender="girl", sidekick_name="Milo", sidekick_gender="boy", adult="father", trait="thoughtful", delay=1),
    StoryParams(place="dock", drum="signal", risk="hive", surprise="kite", response="contain", hero_name="Pax", hero_gender="boy", sidekick_name="Rae", sidekick_gender="girl", adult="mother", trait="watchful", delay=0),
]


def explain_rejection(drum: Drum, risk: Risk) -> str:
    if not hazard_at_risk(drum, risk):
        return f"(No story: {drum.label} does not create the right kind of trouble for {risk.label}.)"
    return "(No story: that combination is not reasonable for this storyworld.)"


def outcome_of(params: StoryParams) -> str:
    if is_contained(RESPONSES[params.response], RISKS[params.risk], params.delay):
        return "contained"
    return "spilled"


ASP_RULES = r"""
risk_at_hazard(D, R) :- drum(D), risk(R), sound(D), fragile(R).
sensible_response(X) :- response(X), sense(X,S), sense_min(M), S >= M.
contained(RP) :- chosen_response(RP), response(RP), power(RP,P), fire_severity(V), P >= V.
fire_severity(V) :- chosen_risk(R), fragile(R), delay(D), V = 1 + D + 1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for did, d in DRUMS.items():
        lines.append(asp.fact("drum", did))
        if "sound" in d.tags:
            lines.append(asp.fact("sound", did))
    for rid, r in RISKS.items():
        lines.append(asp.fact("risk", rid))
        if r.fragile:
            lines.append(asp.fact("fragile", rid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show risk_at_hazard/2."))
    return sorted(set(asp.atoms(model, "risk_at_hazard")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_response/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible_response"))


def asp_verify() -> int:
    import traceback
    rc = 0
    if set(asp_valid_combos()) == set((d, r) for _, d, r in valid_combos()):
        print("OK: ASP gate matches Python gate.")
    else:
        rc = 1
        print("MISMATCH: ASP gate differs from Python gate.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception:
        rc = 1
        print("MISMATCH: generate() smoke test failed.")
        traceback.print_exc()
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: superhero caution, conflict, and surprise around a drum.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--drum", choices=DRUMS)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--response", choices=RESPONSES)
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("That response is too weak for this story.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.drum is None or c[1] == args.drum)
              and (args.risk is None or c[2] == args.risk)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, drum, risk = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_name = rng.choice(HERO_NAMES)
    sidekick_name = rng.choice([n for n in SIDEKICK_NAMES if n != hero_name])
    hero_gender = rng.choice(["girl", "boy"])
    sidekick_gender = "boy" if hero_gender == "girl" else "girl"
    adult = rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = 0 if args.seed is None else rng.randint(0, 1)
    return StoryParams(
        place=place, drum=drum, risk=risk, surprise=rng.choice(sorted(SURPRISES)),
        response=response, hero_name=hero_name, hero_gender=hero_gender,
        sidekick_name=sidekick_name, sidekick_gender=sidekick_gender,
        adult=adult, trait=trait, delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.drum not in DRUMS or params.risk not in RISKS or params.surprise not in SURPRISES or params.response not in RESPONSES:
        raise StoryError("Invalid parameters for this storyworld.")
    world = tell(
        PLACES[params.place], DRUMS[params.drum], RISKS[params.risk], SURPRISES[params.surprise],
        RESPONSES[params.response], params.hero_name, params.hero_gender,
        params.sidekick_name, params.sidekick_gender, params.adult, params.trait, params.delay
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show risk_at_hazard/2.\n#show sensible_response/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible responses:", ", ".join(asp_sensible()))
        print()
        for d, r in asp_valid_combos():
            print(d, r)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
