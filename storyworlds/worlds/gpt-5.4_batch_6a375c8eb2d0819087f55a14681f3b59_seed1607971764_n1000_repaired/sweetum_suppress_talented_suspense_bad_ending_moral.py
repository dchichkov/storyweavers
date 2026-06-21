#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sweetum_suppress_talented_suspense_bad_ending_moral.py
==================================================================================

A standalone story world about a talented little performer named Sweetum, a
danger noticed before a village show, and the choice to speak up or suppress a
warning.

The stories are told in a gentle rhyming style. The central moral is simple:
talent shines best when it walks with honesty. Some outcomes are sad on purpose:
if Sweetum suppresses the warning, the show ends badly, and the ending itself
teaches the lesson.

Run it
------
    python storyworlds/worlds/gpt-5.4/sweetum_suppress_talented_suspense_bad_ending_moral.py
    python storyworlds/worlds/gpt-5.4/sweetum_suppress_talented_suspense_bad_ending_moral.py --decision suppress
    python storyworlds/worlds/gpt-5.4/sweetum_suppress_talented_suspense_bad_ending_moral.py --all --qa
    python storyworlds/worlds/gpt-5.4/sweetum_suppress_talented_suspense_bad_ending_moral.py --trace --seed 7
    python storyworlds/worlds/gpt-5.4/sweetum_suppress_talented_suspense_bad_ending_moral.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "goose", "cat"}
        male = {"boy", "father", "fox", "badger", "mole"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)
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
class Venue:
    id: str
    place: str
    afford_acts: set[str] = field(default_factory=set)
    mood: str = ""
    crowd: str = ""
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
class Act:
    id: str
    title: str
    verb: str
    talent_word: str
    prop: str
    setup_line: str
    perform_line: str
    after_line: str
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
class Hazard:
    id: str
    prop: str
    clue: str
    hush_reason: str
    accident: str
    wreckage: str
    danger_word: str
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
    fixes: str
    enter_line: str
    fix_line: str
    saved_line: str
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
    def __init__(self, venue: Venue) -> None:
        self.venue = venue
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
        clone = World(self.venue)
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


def _r_accident(world: World) -> list[str]:
    stage = world.get("stage")
    if stage.meters["show_started"] < THRESHOLD:
        return []
    hazard = world.get("hazard")
    if hazard.meters["active"] < THRESHOLD:
        return []
    if hazard.meters["fixed"] >= THRESHOLD:
        return []
    sig = ("accident", world.facts.get("hazard_id"), world.facts.get("act_id"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    stage.meters["spoiled"] += 1
    stage.meters["danger"] += 1
    world.get("sweetum").memes["shock"] += 1
    world.get("partner").memes["fear"] += 1
    world.get("teacher").memes["concern"] += 1
    return ["__accident__"]


CAUSAL_RULES = [
    Rule(name="accident", tag="physical", apply=_r_accident),
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


VENUES = {
    "barn": Venue(
        id="barn",
        place="the old red barn",
        afford_acts={"sing", "dance", "juggle"},
        mood="Lanterns blinked on beams of red, and twilight softly brushed the shed.",
        crowd="Mice and moles squeezed close in rows, with shiny eyes and twitching noses.",
        tags={"stage", "barn"},
    ),
    "meadow": Venue(
        id="meadow",
        place="the moonlit meadow stage",
        afford_acts={"sing", "dance"},
        mood="Fireflies stitched a silver seam, and dew made every grass-blade gleam.",
        crowd="The field was full of rustling fur, all waiting for the show to stir.",
        tags={"stage", "meadow"},
    ),
    "hall": Venue(
        id="hall",
        place="the little village hall",
        afford_acts={"sing", "juggle"},
        mood="The floorboards hummed beneath each shoe, and paper stars all shivered blue.",
        crowd="Families filled the polished hall and whispered, 'Hush now, hear the call.'",
        tags={"stage", "hall"},
    ),
}

ACTS = {
    "sing": Act(
        id="sing",
        title="a silver song",
        verb="sing beneath the painted moon",
        talent_word="talented singer",
        prop="moon_ribbon",
        setup_line="A paper moon hung high and bright, to crown the song with dreamy light.",
        perform_line="Sweetum lifted up a tune that curled like ribbons round the moon.",
        after_line="The crowd should have clapped clap-clap in delight, and sent the notes up through the night.",
        tags={"music", "song"},
    ),
    "dance": Act(
        id="dance",
        title="a quick-step dance",
        verb="dance across the little stage",
        talent_word="talented dancer",
        prop="loose_plank",
        setup_line="A painted stage was swept and wide, with little stars along each side.",
        perform_line="Sweetum skipped and spun in time, with tap-tap feet and ankle chime.",
        after_line="The crowd should have cheered the nimble feet that pattered out a skipping beat.",
        tags={"dance", "stage"},
    ),
    "juggle": Act(
        id="juggle",
        title="a bright-ball juggling act",
        verb="juggle the painted balls up high",
        talent_word="talented juggler",
        prop="cracked_basket",
        setup_line="A wicker basket by the chair held painted balls with careful care.",
        perform_line="Sweetum tossed the colors one by one till red met blue and caught the sun.",
        after_line="The crowd should have gasped and laughed with glee to see such tidy flying three.",
        tags={"juggle", "basket"},
    ),
}

HAZARDS = {
    "moon_ribbon": Hazard(
        id="moon_ribbon",
        prop="moon_ribbon",
        clue="one ribbon on the painted moon was frayed to threads as thin as noon",
        hush_reason="If the song was stopped, the hush might break and all the brave stage magic shake.",
        accident="The ribbon snapped. The paper moon swung low and crashed with a dusty boom.",
        wreckage="The silver paint tore into strips, and glitter puffed on startled lips.",
        danger_word="frayed ribbon",
        tags={"ribbon", "warning"},
    ),
    "loose_plank": Hazard(
        id="loose_plank",
        prop="loose_plank",
        clue="one plank near center rocked and clicked, a shaky board not safely fixed",
        hush_reason="If the dance was paused, the crowd might sigh, and courage in a talented heart might dry.",
        accident="The plank flipped up. A drum went thunk, and Sweetum stumbled with a frightened clunk.",
        wreckage="The starry border split in two, and one small slipper tumbled through.",
        danger_word="loose plank",
        tags={"plank", "warning"},
    ),
    "cracked_basket": Hazard(
        id="cracked_basket",
        prop="cracked_basket",
        clue="a crack ran down the juggling basket where the painted balls were snugly packed in",
        hush_reason="If the act was delayed, the crowd might roam, and the biggest cheer might not come home.",
        accident="The basket split. The painted balls shot everywhere with noisy falls.",
        wreckage="Red rolled under every chair, and blue bounced wild through dusty air.",
        danger_word="cracked basket",
        tags={"basket", "warning"},
    ),
}

RESPONSES = {
    "retie_moon": Response(
        id="retie_moon",
        fixes="moon_ribbon",
        enter_line="Teacher Wren hurried up with thread and a tiny stool beneath the spread.",
        fix_line="Soon a new knot held the moon so tight it barely swayed in the lantern light.",
        saved_line="The moon stayed high, the tune stayed true, and the crowd could hear each silver coo.",
        tags={"teacher", "fix", "ribbon"},
    ),
    "hammer_plank": Response(
        id="hammer_plank",
        fixes="loose_plank",
        enter_line="Teacher Wren came with a little hammer and a calm, unflurried, steady manner.",
        fix_line="Tap-tap-tap, the board sat flat, safe for a heel or a paw or a pat.",
        saved_line="The dance rang bright with click and glide, and every step stayed safe with pride.",
        tags={"teacher", "fix", "plank"},
    ),
    "swap_basket": Response(
        id="swap_basket",
        fixes="cracked_basket",
        enter_line="Teacher Wren fetched a basket new, woven strong with willow blue.",
        fix_line="The painted balls were tucked in deep where sturdy wicker meant to keep.",
        saved_line="The colors flew and dropped in line, and every catch looked neat and fine.",
        tags={"teacher", "fix", "basket"},
    ),
}

NAMES = ["Sweetum"]
PARTNERS = ["Pip", "Mimi", "Tansy", "Rill"]
TRAITS = ["brave", "eager", "careful", "hopeful", "gentle"]


def response_for_hazard(hazard_id: str) -> Optional[str]:
    for rid, response in RESPONSES.items():
        if response.fixes == hazard_id:
            return rid
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for venue_id, venue in VENUES.items():
        for act_id in sorted(venue.afford_acts):
            act = ACTS[act_id]
            for hazard_id, hazard in HAZARDS.items():
                if act.prop == hazard.prop:
                    combos.append((venue_id, act_id, hazard_id))
    return combos


@dataclass
class StoryParams:
    venue: str
    act: str
    hazard: str
    response: str
    decision: str
    partner: str
    sweetum_type: str
    partner_type: str
    teacher_type: str
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


def clue_to_meter(hazard_id: str) -> str:
    return {
        "moon_ribbon": "frayed",
        "loose_plank": "wobble",
        "cracked_basket": "crack",
    }[hazard_id]


def introduce(world: World, sweetum: Entity, partner: Entity, act: Act) -> None:
    sweetum.memes["hope"] += 1
    sweetum.memes["pride"] += 1
    partner.memes["trust"] += 1
    world.say(
        f"Sweetum was a {act.talent_word}, small and bright and quick. "
        f"{world.venue.mood}"
    )
    world.say(
        f"In {world.venue.place}, dear {partner.id} stood near, and whispered, "
        f'"Sweetum, sing or dance or juggle clear."'
    )
    world.say(world.venue.crowd)


def set_stage(world: World, act: Act) -> None:
    world.say(act.setup_line)
    stage = world.get("stage")
    stage.meters["ready"] += 1


def notice_danger(world: World, sweetum: Entity, hazard: Hazard, teacher: Entity) -> None:
    hazard_ent = world.get("hazard")
    hazard_ent.meters["active"] += 1
    hazard_ent.meters[clue_to_meter(hazard.id)] += 1
    sweetum.memes["worry"] += 1
    world.facts["noticed"] = True
    world.say(
        f"But just before the music started, Sweetum noticed {hazard.clue}."
    )
    world.say(
        f'Sweetum swallowed once and looked at {teacher.label_word}. '
        f'The warning sat ready, warm and right, like one small lantern in the night.'
    )


def suspense(world: World, sweetum: Entity, hazard: Hazard, act: Act) -> None:
    sweetum.memes["pressure"] += 1
    world.say(
        f'Yet all around, the benches pressed with waiting paws and Sunday best. '
        f'"If I speak now," thought Sweetum, "the hush may bend, and {hazard.hush_reason}"'
    )
    world.say(
        f"The drum gave one soft trembly thrum. Would truth step out, or stay struck dumb?"
    )


def tell_warning(world: World, sweetum: Entity, teacher: Entity, hazard: Hazard) -> None:
    sweetum.memes["honesty"] += 1
    world.say(
        f'"Teacher Wren!" called Sweetum clear. "Please come close. There is danger here. '
        f'I saw a {hazard.danger_word}, and I should not hide it, not even for cheer."'
    )
    teacher.memes["care"] += 1


def make_fix(world: World, response: Response, hazard: Hazard) -> None:
    hazard_ent = world.get("hazard")
    hazard_ent.meters["fixed"] += 1
    hazard_ent.meters["active"] = 0.0
    world.say(response.enter_line)
    world.say(response.fix_line)


def suppress_warning(world: World, sweetum: Entity, partner: Entity) -> None:
    sweetum.memes["suppression"] += 1
    sweetum.memes["guilt"] += 1
    partner.memes["trust"] += 1
    world.say(
        "Sweetum chose to suppress the warning and tucked it down deep, "
        "where a true little truth should never sleep."
    )
    world.say(
        f'"Just smile," thought Sweetum, "and step right through. The song or dance will carry me through." '
        f"But the worry still thudded like a hidden shoe."
    )


def begin_act(world: World, act: Act) -> None:
    stage = world.get("stage")
    stage.meters["show_started"] += 1
    world.say(act.perform_line)
    propagate(world, narrate=False)


def bad_ending(world: World, act: Act, hazard: Hazard) -> None:
    stage = world.get("stage")
    sweetum = world.get("sweetum")
    partner = world.get("partner")
    teacher = world.get("teacher")
    if stage.meters["spoiled"] < THRESHOLD:
        raise StoryError("Bad ending was requested, but no accident occurred.")
    sweetum.memes["regret"] += 1
    sweetum.memes["pride"] = 0.0
    teacher.memes["sadness"] += 1
    world.say(hazard.accident)
    world.say(hazard.wreckage)
    world.say(
        f"{partner.id} went still. Teacher Wren rushed in fast, but now the finest moment had already passed."
    )
    world.say(
        f"{act.after_line} Instead, the room gave one long sigh, and even the lanterns seemed to ask why."
    )
    world.say(
        "Sweetum's talented heart felt heavy as clay. A hidden warning had led the joy astray."
    )
    world.say(
        '"Next time," whispered Sweetum, "I will choose the truer part. '
        'A show may stop for truth, but lies can break a heart."'
    )
    world.facts["moral"] = (
        "Do not suppress a warning just to keep a shiny moment going. "
        "Honesty may pause a performance, but it protects people and their work."
    )


def good_ending(world: World, act: Act, response: Response) -> None:
    sweetum = world.get("sweetum")
    partner = world.get("partner")
    sweetum.memes["relief"] += 1
    sweetum.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(response.saved_line)
    world.say(
        f"{act.after_line} Sweetum bowed, and {partner.id} beamed wide. "
        "Truth had walked beside the talent, stride for stride."
    )
    world.say(
        'Teacher Wren smiled. "Dear sweetum, brave and bright, a warning spoken early makes the whole night right."'
    )
    world.facts["moral"] = (
        "Speak up when you notice danger. Honest courage protects the people, props, and joy around you."
    )


def tell(
    venue: Venue,
    act: Act,
    hazard: Hazard,
    response: Response,
    *,
    decision: str,
    partner_name: str,
    sweetum_type: str,
    partner_type: str,
    teacher_type: str,
    trait: str,
) -> World:
    world = World(venue)
    sweetum = world.add(
        Entity(
            id="Sweetum",
            kind="character",
            type=sweetum_type,
            label="Sweetum",
            role="hero",
            traits=[trait, "talented"],
            attrs={"title": act.title},
        )
    )
    partner = world.add(
        Entity(
            id=partner_name,
            kind="character",
            type=partner_type,
            label=partner_name,
            role="friend",
            traits=["supportive"],
            attrs={},
        )
    )
    teacher = world.add(
        Entity(
            id="Teacher",
            kind="character",
            type=teacher_type,
            label="Teacher Wren",
            role="teacher",
            traits=["calm", "kind"],
            attrs={},
        )
    )
    stage = world.add(
        Entity(
            id="stage",
            kind="thing",
            type="stage",
            label="the stage",
            role="place",
            attrs={},
        )
    )
    hazard_ent = world.add(
        Entity(
            id="hazard",
            kind="thing",
            type="hazard",
            label=hazard.danger_word,
            role="hazard",
            attrs={"hazard_id": hazard.id},
        )
    )

    world.facts.update(
        venue=venue,
        act=act,
        hazard_cfg=hazard,
        response_cfg=response,
        decision=decision,
        partner_name=partner_name,
        act_id=act.id,
        hazard_id=hazard.id,
        response_id=response.id,
        noticed=False,
        fixed=False,
        spoiled=False,
        outcome="?",
        moral="",
    )

    introduce(world, sweetum, partner, act)
    set_stage(world, act)

    world.para()
    notice_danger(world, sweetum, hazard, teacher)
    suspense(world, sweetum, hazard, act)

    world.para()
    if decision == "tell":
        tell_warning(world, sweetum, teacher, hazard)
        make_fix(world, response, hazard)
        world.facts["fixed"] = True
        begin_act(world, act)
        if stage.meters["spoiled"] >= THRESHOLD:
            raise StoryError("The stage should not spoil after a successful fix.")
        good_ending(world, act, response)
        outcome = "good"
    elif decision == "suppress":
        suppress_warning(world, sweetum, partner)
        begin_act(world, act)
        world.facts["spoiled"] = stage.meters["spoiled"] >= THRESHOLD
        bad_ending(world, act, hazard)
        outcome = "bad"
    else:
        raise StoryError(f"Unknown decision: {decision}")

    world.facts.update(
        sweetum=sweetum,
        partner=partner,
        teacher=teacher,
        stage=stage,
        hazard=hazard_ent,
        outcome=outcome,
        spoiled=stage.meters["spoiled"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "warning": [
        (
            "Why should you tell a grown-up when you notice danger?",
            "A grown-up can help fix the problem before it gets bigger. Speaking up early can keep people safe and stop a small problem from turning into a sad one."
        )
    ],
    "honesty": [
        (
            "Why is honesty important during a performance?",
            "Honesty helps everyone make safe choices, even if it causes a short pause. A true warning protects the people, the props, and the fun."
        )
    ],
    "ribbon": [
        (
            "What can happen if a ribbon is frayed?",
            "A frayed ribbon can snap because its threads are weak. If it is holding something up, that thing might fall."
        )
    ],
    "plank": [
        (
            "Why is a loose plank unsafe?",
            "A loose plank can tip or move when someone steps on it. That can make a dancer or walker stumble."
        )
    ],
    "basket": [
        (
            "Why is a cracked basket a problem?",
            "A cracked basket can split open and spill what is inside. That can spoil a careful plan and make a big mess."
        )
    ],
    "talent": [
        (
            "What makes talent shine in a good way?",
            "Talent shines best when it is joined with care, practice, and honesty. Being skillful is wonderful, but being truthful makes the skill safer and kinder."
        )
    ],
    "teacher": [
        (
            "What does a teacher do at a school or show?",
            "A teacher helps children learn and stay safe. At a show, a teacher can also help fix problems and guide everyone calmly."
        )
    ],
}
KNOWLEDGE_ORDER = ["warning", "honesty", "ribbon", "plank", "basket", "talent", "teacher"]


def generation_prompts(world: World) -> list[str]:
    act = world.facts["act"]
    hazard = world.facts["hazard_cfg"]
    outcome = world.facts["outcome"]
    if outcome == "bad":
        return [
            (
                f'Write a short rhyming story for a 3-to-5-year-old about a talented performer named '
                f'Sweetum who notices a {hazard.danger_word} before a show and chooses to suppress the warning.'
            ),
            (
                f"Tell a suspenseful nursery-style poem where Sweetum wants to {act.verb}, keeps quiet about danger, "
                f"and the ending turns sad but teaches honesty."
            ),
            (
                'Write a gentle bad-ending moral tale that includes the words "sweetum", "suppress", and "talented", '
                "and shows that hiding danger spoils the joy."
            ),
        ]
    return [
        (
            f'Write a short rhyming story for a 3-to-5-year-old about a talented performer named Sweetum '
            f'who notices a {hazard.danger_word} before a show and bravely speaks up.'
        ),
        (
            f"Tell a suspenseful but kind poem where Sweetum wants to {act.verb}, tells Teacher Wren the truth, "
            f"and the show ends safely."
        ),
        (
            'Write a moral rhyming tale that includes the words "sweetum", "suppress", and "talented", '
            "but teaches that warnings should be spoken, not suppressed."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    sweetum = world.facts["sweetum"]
    partner = world.facts["partner"]
    act = world.facts["act"]
    hazard = world.facts["hazard_cfg"]
    response = world.facts["response_cfg"]
    outcome = world.facts["outcome"]
    items: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Sweetum, a talented little performer, and {partner.id}, who waited nearby for the show. Teacher Wren is there too, because the stage needs a calm grown-up when trouble appears."
        ),
        (
            "What did Sweetum notice before the show?",
            f"Sweetum noticed {hazard.clue}. That clue mattered because it meant something on the stage was not safe."
        ),
        (
            "Why was the moment suspenseful?",
            f"The crowd was already waiting, and Sweetum worried that speaking up might spoil the hush. So the story pauses on one hard choice: tell the truth now, or keep quiet and hope for the best."
        ),
    ]
    if outcome == "bad":
        items.append(
            (
                "Why did the show end badly?",
                f"The show ended badly because Sweetum chose to suppress the warning instead of telling Teacher Wren. When the act began, the hidden problem turned into a real accident and spoiled the performance."
            )
        )
        items.append(
            (
                "What did Sweetum learn?",
                f"Sweetum learned that a warning should never be hidden for the sake of applause. A short pause for truth is much smaller than the sadness caused by silence."
            )
        )
    else:
        items.append(
            (
                "How was the problem solved?",
                f"Sweetum told Teacher Wren about the danger, and Teacher Wren {response.fix_line[0].lower() + response.fix_line[1:] if response.fix_line else 'fixed it quickly.'} Because the problem was repaired before the act began, the show could continue safely."
            )
        )
        items.append(
            (
                "What changed after Sweetum spoke up?",
                f"At first Sweetum feared that honesty would stop the magic. In the end, the truth protected the stage, and the talent could shine without anyone getting a fright."
            )
        )
    return items


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"warning", "honesty", "talent", "teacher"}
    hazard = world.facts["hazard_cfg"]
    if "ribbon" in hazard.tags:
        tags.add("ribbon")
    if "plank" in hazard.tags:
        tags.add("plank")
    if "basket" in hazard.tags:
        tags.add("basket")
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
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        venue="barn",
        act="sing",
        hazard="moon_ribbon",
        response="retie_moon",
        decision="suppress",
        partner="Pip",
        sweetum_type="girl",
        partner_type="boy",
        teacher_type="teacher",
        trait="hopeful",
    ),
    StoryParams(
        venue="meadow",
        act="dance",
        hazard="loose_plank",
        response="hammer_plank",
        decision="tell",
        partner="Mimi",
        sweetum_type="girl",
        partner_type="girl",
        teacher_type="teacher",
        trait="brave",
    ),
    StoryParams(
        venue="hall",
        act="juggle",
        hazard="cracked_basket",
        response="swap_basket",
        decision="suppress",
        partner="Rill",
        sweetum_type="boy",
        partner_type="girl",
        teacher_type="teacher",
        trait="eager",
    ),
    StoryParams(
        venue="hall",
        act="sing",
        hazard="moon_ribbon",
        response="retie_moon",
        decision="tell",
        partner="Tansy",
        sweetum_type="girl",
        partner_type="boy",
        teacher_type="teacher",
        trait="gentle",
    ),
    StoryParams(
        venue="barn",
        act="dance",
        hazard="loose_plank",
        response="hammer_plank",
        decision="suppress",
        partner="Mimi",
        sweetum_type="boy",
        partner_type="girl",
        teacher_type="teacher",
        trait="careful",
    ),
]


def explain_combo(act_id: str, hazard_id: str) -> str:
    act = ACTS.get(act_id)
    hazard = HAZARDS.get(hazard_id)
    if act is None or hazard is None:
        return "(No story: unknown act or hazard.)"
    return (
        f"(No story: {act.title} uses the prop affected by {act.prop}, but you chose "
        f"{hazard.danger_word}, which belongs with {hazard.prop}. Pick the hazard that matches the act.)"
    )


def explain_response(hazard_id: str, response_id: str) -> str:
    hazard = HAZARDS.get(hazard_id)
    response = RESPONSES.get(response_id)
    if hazard is None or response is None:
        return "(No story: unknown hazard or response.)"
    wanted = response_for_hazard(hazard_id)
    if wanted is None:
        return f"(No story: no known safe fix exists for {hazard.danger_word}.)"
    return (
        f"(No story: response '{response_id}' does not fix {hazard.danger_word}. "
        f"Try '{wanted}' instead.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "bad" if params.decision == "suppress" else "good"


ASP_RULES = r"""
matches_prop(A, H) :- act(A), hazard(H), needs_prop(A, P), hazard_prop(H, P).
valid(V, A, H) :- venue(V), affords(V, A), matches_prop(A, H).

right_fix(H, R) :- hazard(H), response(R), fixes(R, H).

outcome(good) :- decision(tell), chosen_hazard(H), chosen_response(R), right_fix(H, R).
outcome(bad)  :- decision(suppress).
#show valid/3.
#show right_fix/2.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for venue_id, venue in VENUES.items():
        lines.append(asp.fact("venue", venue_id))
        for act_id in sorted(venue.afford_acts):
            lines.append(asp.fact("affords", venue_id, act_id))
    for act_id, act in ACTS.items():
        lines.append(asp.fact("act", act_id))
        lines.append(asp.fact("needs_prop", act_id, act.prop))
    for hazard_id, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hazard_id))
        lines.append(asp.fact("hazard_prop", hazard_id, hazard.prop))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("fixes", response_id, response.fixes))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_right_fixes() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "right_fix")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_hazard", params.hazard),
            asp.fact("chosen_response", params.response),
            asp.fact("decision", params.decision),
        ]
    )
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world: Sweetum notices danger before a talent show."
    )
    ap.add_argument("--venue", choices=sorted(VENUES))
    ap.add_argument("--act", choices=sorted(ACTS))
    ap.add_argument("--hazard", choices=sorted(HAZARDS))
    ap.add_argument("--response", choices=sorted(RESPONSES))
    ap.add_argument("--decision", choices=["tell", "suppress"])
    ap.add_argument("--partner")
    ap.add_argument("--sweetum-type", choices=["girl", "boy"], dest="sweetum_type")
    ap.add_argument("--partner-type", choices=["girl", "boy"], dest="partner_type")
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base random seed")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list valid combos from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print ASP facts and rules")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.act and args.hazard:
        if ACTS[args.act].prop != HAZARDS[args.hazard].prop:
            raise StoryError(explain_combo(args.act, args.hazard))

    if args.hazard and args.response:
        wanted = response_for_hazard(args.hazard)
        if wanted != args.response:
            raise StoryError(explain_response(args.hazard, args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.venue is None or combo[0] == args.venue)
        and (args.act is None or combo[1] == args.act)
        and (args.hazard is None or combo[2] == args.hazard)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    venue_id, act_id, hazard_id = rng.choice(sorted(combos))
    wanted_response = response_for_hazard(hazard_id)
    if wanted_response is None:
        raise StoryError(f"(No story: no safe response is registered for hazard '{hazard_id}').")
    response_id = args.response or wanted_response
    if response_id != wanted_response:
        raise StoryError(explain_response(hazard_id, response_id))

    decision = args.decision or rng.choice(["suppress", "suppress", "tell"])
    partner = args.partner or rng.choice([name for name in PARTNERS if name != "Sweetum"])
    sweetum_type = args.sweetum_type or rng.choice(["girl", "boy"])
    partner_type = args.partner_type or rng.choice(["girl", "boy"])
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        venue=venue_id,
        act=act_id,
        hazard=hazard_id,
        response=response_id,
        decision=decision,
        partner=partner,
        sweetum_type=sweetum_type,
        partner_type=partner_type,
        teacher_type="teacher",
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.venue not in VENUES:
        raise StoryError(f"Unknown venue: {params.venue}")
    if params.act not in ACTS:
        raise StoryError(f"Unknown act: {params.act}")
    if params.hazard not in HAZARDS:
        raise StoryError(f"Unknown hazard: {params.hazard}")
    if params.response not in RESPONSES:
        raise StoryError(f"Unknown response: {params.response}")
    if params.decision not in {"tell", "suppress"}:
        raise StoryError(f"Unknown decision: {params.decision}")
    if ACTS[params.act].prop != HAZARDS[params.hazard].prop:
        raise StoryError(explain_combo(params.act, params.hazard))
    wanted = response_for_hazard(params.hazard)
    if wanted != params.response:
        raise StoryError(explain_response(params.hazard, params.response))

    world = tell(
        VENUES[params.venue],
        ACTS[params.act],
        HAZARDS[params.hazard],
        RESPONSES[params.response],
        decision=params.decision,
        partner_name=params.partner,
        sweetum_type=params.sweetum_type,
        partner_type=params.partner_type,
        teacher_type=params.teacher_type,
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

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combos match ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))

    py_fixes = sorted((hid, response_for_hazard(hid)) for hid in sorted(HAZARDS) if response_for_hazard(hid))
    asp_fixes = sorted(asp_right_fixes())
    if py_fixes == asp_fixes:
        print(f"OK: hazard fixes match ({len(py_fixes)} mappings).")
    else:
        rc = 1
        print("MISMATCH in hazard fixes:")
        print("  python:", py_fixes)
        print("  asp   :", asp_fixes)

    cases = list(CURATED)
    for seed in range(20):
        try:
            ns = build_parser().parse_args([])
            p = resolve_params(ns, random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {seed}.")
            break

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=False, header="### smoke")
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke-test generation/emit succeeded.")
    except Exception as exc:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        fixes = asp_right_fixes()
        print(f"{len(combos)} valid (venue, act, hazard) combos:\n")
        for venue_id, act_id, hazard_id in combos:
            fixed_by = next((rid for hid, rid in fixes if hid == hazard_id), "?")
            print(f"  {venue_id:7} {act_id:7} {hazard_id:14} fix={fixed_by}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### Sweetum at {p.venue}: {p.act} / {p.decision} / {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
