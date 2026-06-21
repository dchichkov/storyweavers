#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/icky_witch_quartet_humor_fairy_tale.py
=================================================================

A standalone storyworld for a humorous fairy-tale domain:

    a kind but hasty witch,
    an icky magical shortcut,
    and a woodland quartet that still hopes to play.

The model rebuilds one small tale-shape in many close variants:

- A witch prepares for a little concert in her cottage.
- She is tempted to use a silly shortcut polish-spell on one instrument.
- A child helper predicts that the shortcut will make an icky mess.
- The witch is in too much of a hurry and tries it anyway.
- Then a sensible cleanup method either saves the concert in time, or the music
  must wait until dawn while the instrument dries.

The world enforces a reasonableness constraint: a cleanup method must match the
mess kind and be safe for the instrument's material. Some methods are known but
refused as poor common sense. An inline ASP twin mirrors the Python gate and
outcome logic.

Run it
------
    python storyworlds/worlds/gpt-5.4/icky_witch_quartet_humor_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/icky_witch_quartet_humor_fairy_tale.py --spell bog_butter --instrument moon_drum
    python storyworlds/worlds/gpt-5.4/icky_witch_quartet_humor_fairy_tale.py --response bucket_dunk
    python storyworlds/worlds/gpt-5.4/icky_witch_quartet_humor_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/icky_witch_quartet_humor_fairy_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/icky_witch_quartet_humor_fairy_tale.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    material: str = ""
    # two axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "witch", "woman"}
        male = {"boy", "father", "man"}
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
class Occasion:
    id: str
    title: str
    sky: str
    purpose: str
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
class Spell:
    id: str
    label: str
    mess: str
    stubbornness: int
    shelf: str
    flare: str
    splat: str
    warning: str
    lesson: str
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
class InstrumentCfg:
    id: str
    label: str
    material: str
    player: str
    sound: str
    article: str
    tags: set[str] = field(default_factory=set)

    @property
    def the_label(self) -> str:
        return f"the {self.label}"

    @property
    def The_label(self) -> str:
        return f"The {self.label}"
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
    label: str
    sense: int
    power: int
    guards: set[str] = field(default_factory=set)
    safe_materials: set[str] = field(default_factory=set)
    success: str = ""
    fail: str = ""
    qa_text: str = ""
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

    def quartet_members(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role == "quartet_member"]


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


def _r_filthy_worry(world: World) -> list[str]:
    out: list[str] = []
    instrument = world.get("instrument")
    if instrument.meters["filthy"] < THRESHOLD:
        return out
    sig = ("filthy_worry", instrument.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("Witch").memes["embarrassment"] += 1
    for member in world.quartet_members():
        member.memes["worry"] += 1
    out.append("__filthy__")
    return out


def _r_clean_relief(world: World) -> list[str]:
    out: list[str] = []
    instrument = world.get("instrument")
    if instrument.meters["clean"] < THRESHOLD:
        return out
    sig = ("clean_relief", instrument.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("Witch").memes["relief"] += 1
    world.get("Helper").memes["relief"] += 1
    for member in world.quartet_members():
        member.memes["hope"] += 1
    out.append("__clean__")
    return out


def _r_ready_joy(world: World) -> list[str]:
    out: list[str] = []
    instrument = world.get("instrument")
    if instrument.meters["clean"] < THRESHOLD or instrument.meters["ready"] < THRESHOLD:
        return out
    sig = ("ready_joy", instrument.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("Witch").memes["joy"] += 1
    world.get("Helper").memes["joy"] += 1
    for member in world.quartet_members():
        member.memes["joy"] += 1
    out.append("__ready__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="filthy_worry", tag="social", apply=_r_filthy_worry),
    Rule(name="clean_relief", tag="social", apply=_r_clean_relief),
    Rule(name="ready_joy", tag="social", apply=_r_ready_joy),
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


def compatible_response(spell: Spell, instrument: InstrumentCfg, response: Response) -> bool:
    return (
        spell.mess in response.guards
        and instrument.material in response.safe_materials
    )


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def compatible_responses(spell: Spell, instrument: InstrumentCfg) -> list[Response]:
    return [
        r for r in sensible_responses()
        if compatible_response(spell, instrument, r)
    ]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for spell_id, spell in SPELLS.items():
        for instrument_id, instrument in INSTRUMENTS.items():
            if compatible_responses(spell, instrument):
                combos.append((spell_id, instrument_id))
    return combos


def cleanup_severity(spell: Spell, delay: int) -> int:
    return spell.stubbornness + delay


def cleanup_succeeds(spell: Spell, response: Response, delay: int) -> bool:
    return response.power >= cleanup_severity(spell, delay)


def predict_mess(world: World, spell_id: str) -> dict:
    sim = world.copy()
    cast_shortcut(sim, SPELLS[spell_id], narrate=False)
    instrument = sim.get("instrument")
    return {
        "filthy": instrument.meters["filthy"] >= THRESHOLD,
        "mess": next((m for m in ("sticky", "slimy", "sooty") if instrument.meters[m] >= THRESHOLD), ""),
        "worry_count": sum(member.memes["worry"] for member in sim.quartet_members()),
    }


def intro_cottage(world: World, occasion: Occasion, witch: Entity, helper: Entity) -> None:
    world.say(
        f"At the edge of the mossy wood stood {witch.id}'s crooked cottage, where the chimney bent like an old finger toward {occasion.sky}."
    )
    world.say(
        f"{witch.id} was a cheerful witch who liked neat shelves, bubbling kettles, and jokes that made even her broom creak with laughter."
    )
    world.say(
        f"That evening was {occasion.title}, and {helper.id}, {witch.pronoun('possessive')} young helper, hurried about because {occasion.purpose}."
    )


def bring_in_quartet(world: World, instrument_cfg: InstrumentCfg) -> None:
    world.say(
        "Soon the woodland quartet arrived: a frog with a fiddle case, an owl with a silver flute, a mole rolling a moon-drum, and a mouse carrying a tiny reed harp."
    )
    world.say(
        f"But before anyone could begin, {instrument_cfg.the_label} looked dull from the day's travel."
    )


def notice_problem(world: World, witch: Entity, instrument_cfg: InstrumentCfg) -> None:
    witch.memes["pride"] += 1
    world.say(
        f'"Oh dear," said {witch.id}, peering at {instrument_cfg.the_label}. "A concert cannot begin while {instrument_cfg.the_label} looks as sleepy as an old boot."'
    )


def temptation(world: World, witch: Entity, spell: Spell) -> None:
    witch.memes["hurry"] += 1
    world.say(
        f"{witch.id} reached for {spell.label} from {spell.shelf}. It was famous for being quick and even more famous for being a bad idea."
    )
    world.say(
        f'"Just one tiny polish-spell," {witch.pronoun()} said. "What could possibly go wrong?"'
    )


def warning(world: World, helper: Entity, witch: Entity, spell: Spell, instrument_cfg: InstrumentCfg) -> None:
    pred = predict_mess(world, spell.id)
    world.facts["predicted_mess"] = pred["mess"]
    world.facts["predicted_worry_count"] = pred["worry_count"]
    helper.memes["caution"] += 1
    world.say(
        f'{helper.id} tugged at {witch.id}\'s sleeve. "{witch.id}, please don\'t use {spell.label} on {instrument_cfg.the_label}. {spell.warning}"'
    )
    if pred["filthy"]:
        world.say(
            f'{helper.pronoun().capitalize()} had seen enough kitchen magic to know that it would leave {instrument_cfg.the_label} icky and the whole quartet glum.'
        )


def cast_shortcut(world: World, spell: Spell, narrate: bool = True) -> None:
    instrument = world.get("instrument")
    instrument.meters["filthy"] += 1
    instrument.meters[spell.mess] += 1
    instrument.meters["clean"] = 0.0
    instrument.meters["ready"] = 0.0
    propagate(world, narrate=narrate)


def defy_and_splat(world: World, witch: Entity, spell: Spell, instrument_cfg: InstrumentCfg) -> None:
    witch.memes["defiance"] += 1
    world.say(
        f'But {witch.id} was in a hurry. With a twirl of her spoon and a little sniff, {witch.pronoun()} puffed {spell.label} over {instrument_cfg.the_label}.'
    )
    cast_shortcut(world, spell, narrate=False)
    world.say(
        f"At once {spell.flare}, and then {spell.splat} all over {instrument_cfg.the_label}."
    )
    world.say(
        f'{instrument_cfg.The_label} made a very rude little sound: {instrument_cfg.sound}.'
    )


def quartet_reacts(world: World, instrument_cfg: InstrumentCfg) -> None:
    players = ", ".join(member.id for member in world.quartet_members())
    world.say(
        f"The quartet stared. {players} all leaned back at once, because the mess looked terribly icky and smelled even sillier than it looked."
    )
    world.say(
        f'"That is not polish," murmured the player of {instrument_cfg.the_label}. "That is trouble wearing jam."'
    )


def clean_success(world: World, witch: Entity, helper: Entity, response: Response, instrument_cfg: InstrumentCfg) -> None:
    instrument = world.get("instrument")
    instrument.meters["filthy"] = 0.0
    instrument.meters["sticky"] = 0.0
    instrument.meters["slimy"] = 0.0
    instrument.meters["sooty"] = 0.0
    instrument.meters["clean"] += 1
    instrument.meters["ready"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.id} fetched {response.label}, and together {helper.id} and {witch.id} {response.success.replace('{instrument}', instrument_cfg.label)}."
    )
    world.say(
        f"Soon {instrument_cfg.the_label} shone again, and when the player tested it, the note came out bright instead of burpy."
    )


def clean_fail(world: World, witch: Entity, helper: Entity, response: Response, instrument_cfg: InstrumentCfg) -> None:
    instrument = world.get("instrument")
    instrument.meters["filthy"] = 0.0
    instrument.meters["sticky"] = 0.0
    instrument.meters["slimy"] = 0.0
    instrument.meters["sooty"] = 0.0
    instrument.meters["clean"] += 1
    instrument.meters["ready"] = 0.0
    instrument.meters["drying"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.id} fetched {response.label}, and together they {response.fail.replace('{instrument}', instrument_cfg.label)}."
    )
    world.say(
        f"{instrument_cfg.The_label} was no longer filthy, but it still needed quiet time before it could sing properly again."
    )


def lesson(world: World, witch: Entity, helper: Entity, spell: Spell) -> None:
    witch.memes["wisdom"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"{witch.id} pressed a hand to {witch.pronoun('possessive')} hat and sighed. Then {witch.pronoun()} began to laugh at {witch.pronoun('object')}self, because the whole business was too ridiculous not to laugh at."
    )
    world.say(
        f'"You were right," {witch.pronoun()} told {helper.id}. "{spell.lesson} From now on I shall trust patient hands more than hasty magic."'
    )


def finale_saved(world: World, occasion: Occasion, witch: Entity, instrument_cfg: InstrumentCfg) -> None:
    world.say(
        f"At last the quartet played for {occasion.title}. The fiddle skipped, the flute trilled, the drum hummed, and the harp twinkled until even the spoons on the shelf seemed ready to dance."
    )
    world.say(
        f"{witch.id} sat by the fire with a grin on {witch.pronoun('possessive')} face, and nobody in the cottage smelled icky at all except one embarrassed pickle bubble drifting out the window."
    )


def finale_postponed(world: World, occasion: Occasion, witch: Entity, helper: Entity, instrument_cfg: InstrumentCfg) -> None:
    world.say(
        f"So the concert for {occasion.title} waited until dawn. While {instrument_cfg.the_label} rested by the window, the quartet tapped cups and hummed soft practice notes, and {helper.id} giggled every time the kettle tried to join in."
    )
    world.say(
        f"When morning light spilled across the moss, the cleaned instrument was ready at last. Then the quartet played in the open doorway, and {witch.id} promised that no shortcut spell would ever again come near concert things."
    )


def tell(
    occasion: Occasion,
    spell: Spell,
    instrument_cfg: InstrumentCfg,
    response: Response,
    witch_name: str = "Aunt Juniper",
    helper_name: str = "Mira",
    helper_gender: str = "girl",
    delay: int = 0,
) -> World:
    world = World()
    witch = world.add(Entity(id=witch_name, kind="character", type="witch", label="the witch", role="witch"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, label="the helper", role="helper"))
    instrument = world.add(
        Entity(
            id="instrument",
            kind="thing",
            type="instrument",
            label=instrument_cfg.label,
            role="featured_instrument",
            material=instrument_cfg.material,
            attrs={"player": instrument_cfg.player},
        )
    )

    # initialize rule-read values before propagate
    instrument.meters["filthy"] = 0.0
    instrument.meters["sticky"] = 0.0
    instrument.meters["slimy"] = 0.0
    instrument.meters["sooty"] = 0.0
    instrument.meters["clean"] = 0.0
    instrument.meters["ready"] = 1.0
    instrument.meters["drying"] = 0.0
    witch.memes["embarrassment"] = 0.0
    witch.memes["relief"] = 0.0
    witch.memes["joy"] = 0.0
    helper.memes["relief"] = 0.0
    helper.memes["joy"] = 0.0

    quartet_specs = [
        ("Freckle", "frog", "quartet_member"),
        ("Orrin", "owl", "quartet_member"),
        ("Moss", "mole", "quartet_member"),
        ("Pip", "mouse", "quartet_member"),
    ]
    for qid, qtype, role in quartet_specs:
        member = world.add(Entity(id=qid, kind="character", type=qtype, label=qtype, role=role))
        member.memes["worry"] = 0.0
        member.memes["hope"] = 0.0
        member.memes["joy"] = 0.0

    intro_cottage(world, occasion, witch, helper)
    bring_in_quartet(world, instrument_cfg)
    notice_problem(world, witch, instrument_cfg)

    world.para()
    temptation(world, witch, spell)
    warning(world, helper, witch, spell, instrument_cfg)
    defy_and_splat(world, witch, spell, instrument_cfg)
    quartet_reacts(world, instrument_cfg)

    world.para()
    severity = cleanup_severity(spell, delay)
    saved = cleanup_succeeds(spell, response, delay)
    if saved:
        clean_success(world, witch, helper, response, instrument_cfg)
        lesson(world, witch, helper, spell)
        world.para()
        finale_saved(world, occasion, witch, instrument_cfg)
    else:
        clean_fail(world, witch, helper, response, instrument_cfg)
        lesson(world, witch, helper, spell)
        world.para()
        finale_postponed(world, occasion, witch, helper, instrument_cfg)

    world.facts.update(
        occasion=occasion,
        spell=spell,
        instrument_cfg=instrument_cfg,
        response=response,
        witch=witch,
        helper=helper,
        instrument=instrument,
        delay=delay,
        severity=severity,
        outcome="saved" if saved else "postponed",
        quartet=[world.get("Freckle"), world.get("Orrin"), world.get("Moss"), world.get("Pip")],
        messy=instrument.meters["filthy"] >= THRESHOLD or instrument.meters["drying"] >= THRESHOLD,
        cleaned=instrument.meters["clean"] >= THRESHOLD,
        ready=instrument.meters["ready"] >= THRESHOLD,
        player=instrument_cfg.player,
    )
    return world


OCCASIONS = {
    "moon_feast": Occasion(
        id="moon_feast",
        title="the Moon-Feast",
        sky="a silver moon and a sky full of pricked stars",
        purpose="the quartet would play for bowls of blackberry pudding",
        tags={"moon", "music"},
    ),
    "lantern_fair": Occasion(
        id="lantern_fair",
        title="the Lantern Fair",
        sky="a row of lanterns wobbling under the dusk",
        purpose="the quartet would open the fair with a merry tune",
        tags={"lantern", "music"},
    ),
    "dew_wedding": Occasion(
        id="dew_wedding",
        title="the Dew-Wedding",
        sky="a pale moon hung above the fern tops",
        purpose="the quartet would play for two shy hedgehogs getting married",
        tags={"wedding", "music"},
    ),
}

SPELLS = {
    "pickle_polish": Spell(
        id="pickle_polish",
        label="the jar of Pickle-Polish",
        mess="sticky",
        stubbornness=2,
        shelf="the highest pantry shelf",
        flare="green bubbles popped like hiccups",
        splat="a shower of sweet-and-sour gluey fizz landed",
        warning="It always leaves a sticky shine first and a proper mess after.",
        lesson="Pickle-Polish is for jars, not songs",
        tags={"sticky", "pickle", "cleaning"},
    ),
    "bog_butter": Spell(
        id="bog_butter",
        label="the crock of Bog-Butter",
        mess="slimy",
        stubbornness=3,
        shelf="the cold stone sill",
        flare="the air gave one wet burp",
        splat="thick green slime slid in curls",
        warning="Bog-Butter makes everything slick, and slick is not the same as splendid.",
        lesson="Bog-Butter belongs on boots, not on music",
        tags={"slimy", "bog", "cleaning"},
    ),
    "pepper_puff": Spell(
        id="pepper_puff",
        label="the tin of Pepper-Puff",
        mess="sooty",
        stubbornness=1,
        shelf="the spice rack beside the kettle",
        flare="a black sneezy cloud leapt out",
        splat="soft soot rained down",
        warning="Pepper-Puff only makes things sneeze and turn gray.",
        lesson="Pepper-Puff is for soup jokes, not for polishing",
        tags={"sooty", "pepper", "cleaning"},
    ),
}

INSTRUMENTS = {
    "cedar_fiddle": InstrumentCfg(
        id="cedar_fiddle",
        label="cedar fiddle",
        material="wood_strings",
        player="Freckle the frog",
        sound="brrrp",
        article="a",
        tags={"fiddle", "music", "wood"},
    ),
    "silver_flute": InstrumentCfg(
        id="silver_flute",
        label="silver flute",
        material="metal",
        player="Orrin the owl",
        sound="pffft",
        article="a",
        tags={"flute", "music", "metal"},
    ),
    "moon_drum": InstrumentCfg(
        id="moon_drum",
        label="moon-drum",
        material="hide",
        player="Moss the mole",
        sound="blomp",
        article="a",
        tags={"drum", "music"},
    ),
    "reed_harp": InstrumentCfg(
        id="reed_harp",
        label="reed harp",
        material="wood_strings",
        player="Pip the mouse",
        sound="twang-plip",
        article="a",
        tags={"harp", "music", "wood"},
    ),
}

RESPONSES = {
    "velvet_wipe": Response(
        id="velvet_wipe",
        label="a soft velvet cloth",
        sense=3,
        power=2,
        guards={"sooty"},
        safe_materials={"metal", "wood_strings", "hide"},
        success="wiped the soot from the {instrument} with slow careful circles",
        fail="wiped and wiped the {instrument}, but there was still too much trouble left in it for tonight",
        qa_text="They used a soft velvet cloth to wipe the soot away",
        tags={"cloth", "soot", "cleaning"},
    ),
    "soap_flannel": Response(
        id="soap_flannel",
        label="a warm mint-soap flannel",
        sense=3,
        power=3,
        guards={"sticky", "slimy"},
        safe_materials={"metal", "wood_strings"},
        success="dabbed the {instrument} with a warm mint-soap flannel until the icky mess came away",
        fail="carefully cleaned the {instrument}, but it stayed too damp and fussy to play before bedtime",
        qa_text="They dabbed the mess away with a warm mint-soap flannel",
        tags={"soap", "cleaning"},
    ),
    "bran_brush": Response(
        id="bran_brush",
        label="a dry bran brush",
        sense=3,
        power=3,
        guards={"sticky", "slimy"},
        safe_materials={"hide"},
        success="brushed and patted the {instrument} with a dry bran brush until the skin was clean again",
        fail="cleaned the {instrument} with the bran brush, but it still needed to rest and tighten before it could boom properly",
        qa_text="They used a dry bran brush that was gentle on the drum skin",
        tags={"brush", "cleaning"},
    ),
    "bucket_dunk": Response(
        id="bucket_dunk",
        label="a bucket of cold water",
        sense=1,
        power=4,
        guards={"sticky", "slimy", "sooty"},
        safe_materials={"metal", "wood_strings", "hide"},
        success="dumped water over the {instrument}",
        fail="sloshed water over the {instrument}, which only made the poor thing sulk",
        qa_text="They dumped water over it",
        tags={"water", "cleaning"},
    ),
}

WITCH_NAMES = ["Aunt Juniper", "Dame Nettles", "Old Hazel", "Aunt Clover"]
GIRL_NAMES = ["Mira", "Tansy", "Nell", "Ivy", "Poppy", "Lina"]
BOY_NAMES = ["Tobin", "Rowan", "Pipkin", "Milo", "Bram", "Ned"]


@dataclass
class StoryParams:
    occasion: str
    spell: str
    instrument: str
    response: str
    witch_name: str = "Aunt Juniper"
    helper_name: str = "Mira"
    helper_gender: str = "girl"
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
    "quartet": [
        (
            "What is a quartet?",
            "A quartet is a group of four players or singers who make music together. Four parts can sound rich because each one adds something different."
        )
    ],
    "witch": [
        (
            "What is a witch in a fairy tale?",
            "In a fairy tale, a witch is a magical person who knows spells and odd tricks. Some are scary, but some are funny, kind, or simply a bit too confident."
        )
    ],
    "icky": [
        (
            "What does icky mean?",
            "Icky means something feels yucky, sticky, slimy, or otherwise unpleasant. It is the kind of word people use when they wrinkle their noses."
        )
    ],
    "sticky": [
        (
            "Why is sticky stuff hard to clean off?",
            "Sticky messes cling to surfaces and grab bits of dust and dirt. That is why they often need gentle wiping instead of a quick puff of air."
        )
    ],
    "slimy": [
        (
            "Why can slimy things be a problem?",
            "Slimy things are slippery and messy, so hands and tools can slide around on them. They can also make objects feel unpleasant until they are cleaned."
        )
    ],
    "sooty": [
        (
            "What is soot?",
            "Soot is a fine black dust made by smoke or something burned. It smudges easily and can make things look gray and dirty."
        )
    ],
    "instrument": [
        (
            "Why should you clean an instrument carefully?",
            "Instruments need gentle care because rough cleaning can hurt the parts that make the sound. If you clean them the right way, they can sing clearly again."
        )
    ],
    "patience": [
        (
            "Why is patience better than a hasty shortcut sometimes?",
            "A hasty shortcut can make a bigger problem than the one you started with. Patience gives you time to use the right tool and do the job safely."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "icky",
    "witch",
    "quartet",
    "sticky",
    "slimy",
    "sooty",
    "instrument",
    "patience",
]


CURATED = [
    StoryParams(
        occasion="moon_feast",
        spell="pickle_polish",
        instrument="silver_flute",
        response="soap_flannel",
        witch_name="Aunt Juniper",
        helper_name="Mira",
        helper_gender="girl",
        delay=0,
    ),
    StoryParams(
        occasion="lantern_fair",
        spell="pepper_puff",
        instrument="cedar_fiddle",
        response="velvet_wipe",
        witch_name="Dame Nettles",
        helper_name="Tobin",
        helper_gender="boy",
        delay=0,
    ),
    StoryParams(
        occasion="dew_wedding",
        spell="bog_butter",
        instrument="moon_drum",
        response="bran_brush",
        witch_name="Old Hazel",
        helper_name="Ivy",
        helper_gender="girl",
        delay=1,
    ),
    StoryParams(
        occasion="moon_feast",
        spell="bog_butter",
        instrument="reed_harp",
        response="soap_flannel",
        witch_name="Aunt Clover",
        helper_name="Bram",
        helper_gender="boy",
        delay=1,
    ),
]


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    good = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Use a gentler method such as {good}.)"
    )


def explain_incompatibility(spell: Spell, instrument: InstrumentCfg, response: Response) -> str:
    return (
        f"(No story: {response.label} is not a reasonable way to clean {instrument.the_label} "
        f"after {spell.label}. The method must match a {spell.mess} mess and be safe for "
        f"{instrument.material.replace('_', ' ')} materials.)"
    )


def outcome_of(params: StoryParams) -> str:
    spell = SPELLS[params.spell]
    response = RESPONSES[params.response]
    return "saved" if cleanup_succeeds(spell, response, params.delay) else "postponed"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    occasion = f["occasion"]
    spell = f["spell"]
    instrument = f["instrument_cfg"]
    witch = f["witch"]
    helper = f["helper"]
    outcome = f["outcome"]
    base = (
        f'Write a humorous fairy tale for a 3-to-5-year-old that includes the words '
        f'"icky", "witch", and "quartet". The story should involve {spell.label} and {instrument.the_label}.'
    )
    if outcome == "saved":
        return [
            base,
            f"Tell a funny fairy-tale story where a kind witch named {witch.id} makes {instrument.the_label} icky with a foolish shortcut, then {helper.id} helps save the quartet's concert.",
            f"Write a fairy tale set during {occasion.title} where a silly magical mess is cleaned in time, and the ending proves the music can begin after all.",
        ]
    return [
        base,
        f"Tell a funny fairy-tale story where a hasty witch named {witch.id} makes {instrument.the_label} icky before the quartet can play, and the concert must wait until dawn.",
        f"Write a gentle cautionary tale about a shortcut spell, a messy instrument, and a wise helper named {helper.id}, ending with a promise to use patient hands next time.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    witch = f["witch"]
    helper = f["helper"]
    spell = f["spell"]
    instrument_cfg = f["instrument_cfg"]
    response = f["response"]
    occasion = f["occasion"]
    outcome = f["outcome"]
    player = f["player"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {witch.id}, a funny old witch, {helper.id}, the child helping in the cottage, and a woodland quartet coming to play. The trouble begins because the witch wants the concert to look perfect too quickly."
        ),
        (
            f"Why did {witch.id} use {spell.label}?",
            f"{witch.id} wanted to make {instrument_cfg.the_label} shine before {occasion.title}. She chose a hasty shortcut because the quartet was already there and she did not want to keep them waiting."
        ),
        (
            f"What warning did {helper.id} give?",
            f"{helper.id} warned that {spell.label} would not truly polish {instrument_cfg.the_label}. {helper.pronoun().capitalize()} knew it would leave an icky {spell.mess} mess and make the quartet worried."
        ),
        (
            f"What happened to {instrument_cfg.the_label}?",
            f"It was splattered with an icky {spell.mess} mess instead of becoming shiny. That changed the mood at once, because the quartet could not begin while {player}'s instrument was in such a state."
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                f"How did they fix {instrument_cfg.the_label}?",
                f"{helper.id} and {witch.id} used {response.label} and cleaned it carefully. That method matched the kind of mess on the instrument, so it became ready in time for the music."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The quartet played at {occasion.title}, and the cottage filled with bright music instead of icky smells. The ending proves things changed because the instrument was clean and the witch had learned to trust patient work."
            )
        )
    else:
        qa.append(
            (
                f"Did the quartet play right away after the cleaning?",
                f"No. They cleaned the mess, but {instrument_cfg.the_label} still needed time before it could sound right again. Because the problem had grown too stubborn, the concert had to wait until dawn."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The quartet finally played the next morning in the doorway of the cottage. The ending shows what changed because the witch stopped chasing shortcuts and promised not to use that foolish spell on concert things again."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"witch", "quartet", "icky", "instrument", "patience"}
    spell = f["spell"]
    if spell.mess in {"sticky", "slimy", "sooty"}:
        tags.add(spell.mess)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if ent.material:
            bits.append(f"material={ent.material}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% sensible cleanup methods
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.

% compatibility gate: mess kind + material safety
compatible(S,I,R) :- spell(S), instrument(I), response(R),
                     mess_of(S,M), guards(R,M),
                     material(I,Mat), safe_for(R,Mat),
                     sensible(R).

valid(S,I) :- spell(S), instrument(I), compatible(S,I,_).

% outcome model
severity(V) :- chosen_spell(S), stubbornness(S,St), delay(D), V = St + D.
saved :- chosen_response(R), power(R,P), severity(V), P >= V.
outcome(saved) :- saved.
outcome(postponed) :- not saved.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for oid in OCCASIONS:
        lines.append(asp.fact("occasion", oid))
    for sid, spell in SPELLS.items():
        lines.append(asp.fact("spell", sid))
        lines.append(asp.fact("mess_of", sid, spell.mess))
        lines.append(asp.fact("stubbornness", sid, spell.stubbornness))
    for iid, instrument in INSTRUMENTS.items():
        lines.append(asp.fact("instrument", iid))
        lines.append(asp.fact("material", iid, instrument.material))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
        for mess in sorted(response.guards):
            lines.append(asp.fact("guards", rid, mess))
        for material in sorted(response.safe_materials):
            lines.append(asp.fact("safe_for", rid, material))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
    extra = "\n".join([
        asp.fact("chosen_spell", params.spell),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {r.id for r in sensible_responses()}
    asp_sense = set(asp_sensible())
    if py_sensible == asp_sense:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(asp_sense)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving default params for seed {seed}.")
            break

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
        smoke_params = resolve_params(parser.parse_args([]), random.Random(7))
        smoke_params.seed = 7
        sample = generate(smoke_params)
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("\nOK: smoke-test generation/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err!r}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: an icky witch, a quartet, and a foolish shortcut before a fairy-tale concert."
    )
    ap.add_argument("--occasion", choices=OCCASIONS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--witch-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra stubbornness from waiting too long")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid spell/instrument combos from clingo")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response is not None and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    if args.spell and args.instrument and args.response:
        spell = SPELLS[args.spell]
        instrument = INSTRUMENTS[args.instrument]
        response = RESPONSES[args.response]
        if not compatible_response(spell, instrument, response):
            raise StoryError(explain_incompatibility(spell, instrument, response))

    combos = [
        combo for combo in valid_combos()
        if (args.spell is None or combo[0] == args.spell)
        and (args.instrument is None or combo[1] == args.instrument)
    ]
    if not combos:
        raise StoryError("(No valid spell/instrument combination matches the given options.)")

    spell_id, instrument_id = rng.choice(sorted(combos))
    spell = SPELLS[spell_id]
    instrument = INSTRUMENTS[instrument_id]

    if args.response is not None:
        response_id = args.response
    else:
        response_id = rng.choice(sorted(r.id for r in compatible_responses(spell, instrument)))

    occasion = args.occasion or rng.choice(sorted(OCCASIONS))
    witch_name = args.witch_name or rng.choice(WITCH_NAMES)
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    helper_name = args.helper_name or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        occasion=occasion,
        spell=spell_id,
        instrument=instrument_id,
        response=response_id,
        witch_name=witch_name,
        helper_name=helper_name,
        helper_gender=helper_gender,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.occasion not in OCCASIONS:
        raise StoryError(f"(Unknown occasion: {params.occasion})")
    if params.spell not in SPELLS:
        raise StoryError(f"(Unknown spell: {params.spell})")
    if params.instrument not in INSTRUMENTS:
        raise StoryError(f"(Unknown instrument: {params.instrument})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    spell = SPELLS[params.spell]
    instrument = INSTRUMENTS[params.instrument]
    response = RESPONSES[params.response]

    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not compatible_response(spell, instrument, response):
        raise StoryError(explain_incompatibility(spell, instrument, response))

    world = tell(
        occasion=OCCASIONS[params.occasion],
        spell=spell,
        instrument_cfg=instrument,
        response=response,
        witch_name=params.witch_name,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (spell, instrument) combos:\n")
        for spell_id, instrument_id in combos:
            print(f"  {spell_id:14} {instrument_id}")
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
            header = f"### {p.witch_name}: {p.spell} on {p.instrument} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
