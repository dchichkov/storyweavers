#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/toast_pronunciation_sound_effects_heartwarming.py
==============================================================================

A small story world about a child who wants to say a breakfast word clearly.
The world models warm toast, a tricky pronunciation moment, a gentle helper,
and a practice method matched to the sound pattern of the phrase.

Run it
------
    python storyworlds/worlds/gpt-5.4/toast_pronunciation_sound_effects_heartwarming.py
    python storyworlds/worlds/gpt-5.4/toast_pronunciation_sound_effects_heartwarming.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/toast_pronunciation_sound_effects_heartwarming.py --all --qa
    python storyworlds/worlds/gpt-5.4/toast_pronunciation_sound_effects_heartwarming.py --trace
    python storyworlds/worlds/gpt-5.4/toast_pronunciation_sound_effects_heartwarming.py --json
    python storyworlds/worlds/gpt-5.4/toast_pronunciation_sound_effects_heartwarming.py --verify
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "sister", "aunt"}
        male = {"boy", "father", "grandfather", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }
        return mapping.get(self.type, self.type)
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
class Setting:
    id: str
    place: str
    table_detail: str
    room_sound: str
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
class Phrase:
    id: str
    text: str
    topping: str
    syllables: int
    tricky: str
    practice_sound: str
    buttered: bool = False
    dusted: bool = False
    drizzled: bool = False
    difficulty: int = 2
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
class Method:
    id: str
    label: str
    cue: str
    sound_effect: str
    boost: int
    supports: set[str] = field(default_factory=set)
    max_syllables: int = 3
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
class HelperKind:
    id: str
    type: str
    warmth: int
    opening: str
    ending: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_pop_comfort(world: World) -> list[str]:
    out: list[str] = []
    toast = world.get("toast")
    child = world.get("child")
    helper = world.get("helper")
    if toast.meters["popped"] >= THRESHOLD:
        sig = ("comfort_from_pop",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["hope"] += 1
            helper.memes["care"] += 1
            out.append("__pop__")
    return out


def _r_practice_helps(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    phrase = world.get("phrase")
    helper = world.get("helper")
    if child.meters["practiced"] >= THRESHOLD:
        sig = ("practice_helps",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
            child.memes["courage"] += 1.0 + helper.attrs.get("warmth", 0) / 4.0
            phrase.meters["clarity"] += child.attrs.get("method_boost", 0)
            out.append("__practice__")
    return out


def _r_melt_marks_time(world: World) -> list[str]:
    out: list[str] = []
    toast = world.get("toast")
    if toast.meters["buttered"] >= THRESHOLD:
        sig = ("melt_marks_time",)
        if sig not in world.fired:
            world.fired.add(sig)
            toast.meters["warmth"] += 1
            out.append("__melt__")
    return out


CAUSAL_RULES = [
    Rule(name="pop_comfort", tag="emotional", apply=_r_pop_comfort),
    Rule(name="practice_helps", tag="emotional", apply=_r_practice_helps),
    Rule(name="melt_marks_time", tag="physical", apply=_r_melt_marks_time),
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


def method_fits(phrase: Phrase, method: Method) -> bool:
    return phrase.tricky in method.supports and phrase.syllables <= method.max_syllables


def support_score(phrase: Phrase, method: Method, helper: HelperKind, cools: int) -> int:
    return method.boost + helper.warmth - cools


def outcome_of_values(phrase: Phrase, method: Method, helper: HelperKind, cools: int) -> str:
    score = support_score(phrase, method, helper, cools)
    if score >= phrase.difficulty + 3:
        return "clear"
    if score >= phrase.difficulty + 1:
        return "brave"
    return "stuck"


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for phrase_id, phrase in PHRASES.items():
            for method_id, method in METHODS.items():
                if not method_fits(phrase, method):
                    continue
                for helper_id, helper in HELPERS.items():
                    if outcome_of_values(phrase, method, helper, 1) != "stuck":
                        combos.append((setting_id, phrase_id, method_id, helper_id))
    return combos


def explain_rejection(phrase: Phrase, method: Method, helper: Optional[HelperKind] = None) -> str:
    if not method_fits(phrase, method):
        return (
            f"(No story: {method.label} is not a natural way to practice "
            f'"{phrase.text}". The method must fit the phrase\'s sound pattern '
            f"and length.)"
        )
    if helper is not None and outcome_of_values(phrase, method, helper, 1) == "stuck":
        return (
            f"(No story: even with {helper.type}, {method.label} would leave the child "
            f"too stuck to finish the phrase. Pick a warmer helper or a stronger practice method.)"
        )
    return "(No valid combination matches the given options.)"


@dataclass
class StoryParams:
    setting: str
    phrase: str
    method: str
    helper: str
    child_name: str
    child_type: str
    cools: int = 0
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


def introduce(world: World, child: Entity, helper: Entity, phrase: Phrase) -> None:
    world.say(
        f"{child.id} stood in {world.setting.place} beside {helper.id}, helping with breakfast. "
        f"{world.setting.table_detail}"
    )
    world.say(
        f"{helper.id} was making {phrase.text}, and the warm smell curled through the room."
    )


def want_to_say(world: World, child: Entity, phrase: Phrase) -> None:
    child.memes["wish"] += 1
    child.memes["worry"] += 2
    world.say(
        f"{child.id} wanted to say the breakfast words all alone, because {child.pronoun()} "
        f"planned to carry the plate to the table and announce it proudly."
    )
    world.say(
        f'But the pronunciation of "{phrase.text}" felt bumpy in {child.pronoun("possessive")} mouth.'
    )


def toaster_pops(world: World, child: Entity, helper: Entity, phrase: Phrase) -> None:
    toast = world.get("toast")
    toast.meters["popped"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{world.setting.room_sound} The toaster went "tick-tick... POP!" and two golden pieces of toast jumped up.'
    )
    if phrase.buttered:
        toast.meters["buttered"] += 1
        propagate(world, narrate=False)
        world.say('Swish went the butter knife, and a shiny yellow ribbon melted across the toast.')
    elif phrase.dusted:
        toast.meters["dusted"] += 1
        world.say('Shake-shake went the cinnamon, making a soft brown snow on top.')
    elif phrase.drizzled:
        toast.meters["drizzled"] += 1
        world.say('Drip-drip went the honey, leaving bright little trails that caught the light.')


def stumble(world: World, child: Entity, phrase: Phrase) -> None:
    child.memes["embarrassment"] += 1
    world.say(
        f'{child.id} took a breath. "\"{phrase.practice_sound}... {phrase.text}\"" came out in a tiny tumble.'
    )
    world.say(
        f"{child.pronoun().capitalize()} pressed {child.pronoun('possessive')} lips together and looked down at the plate."
    )


def helper_comforts(world: World, child: Entity, helper: Entity, helper_cfg: HelperKind) -> None:
    child.memes["comfort"] += 1
    world.say(
        f'{helper.id} did not laugh. {helper_cfg.opening} "{child.id}, breakfast can wait one little minute."'
    )
    world.say(
        f"{helper.pronoun().capitalize()} knelt so their eyes were level, and suddenly the kitchen felt smaller and kinder."
    )


def practice(world: World, child: Entity, helper: Entity, phrase: Phrase, method: Method) -> None:
    child.meters["practiced"] += 1
    child.attrs["method_boost"] = method.boost
    child.attrs["method_id"] = method.id
    propagate(world, narrate=False)
    if method.id == "tap":
        world.say(
            f'"Let\'s tap the first sound together," {helper.id} said. '
            f'"{method.sound_effect}! {phrase.practice_sound}."'
        )
    elif method.id == "mirror":
        world.say(
            f'{helper.id} held up a shiny spoon like a little mirror. '
            f'"Watch our mouths. {method.sound_effect}... now say it slowly."'
        )
    elif method.id == "clap":
        world.say(
            f'"We can make the long word into steps," {helper.id} said. '
            f'"{method.sound_effect}! {phrase.text}."'
        )
    else:
        world.say(
            f'{helper.id} hummed softly. "\"{method.sound_effect}... {phrase.text}.\" '
            f"Sometimes a tune made the words feel less tight."
        )


def try_again(world: World, child: Entity, helper: Entity, phrase: Phrase, cools: int) -> None:
    toast = world.get("toast")
    phrase_ent = world.get("phrase")
    helper_warmth = helper.attrs.get("warmth", 0)
    score = phrase_ent.meters["clarity"] + helper_warmth - cools
    toast.meters["coolness"] = float(cools)
    if cools:
        world.say(
            "For a second they waited while the toast cooled just enough to carry. "
            "A tiny thread of steam drifted up and then thinned away."
        )
    if score >= phrase.difficulty + 3:
        child.memes["pride"] += 2
        child.memes["worry"] = 0.0
        world.say(
            f'Then {child.id} tried again. "\"{phrase.text}!\"" {child.pronoun()} said, clear and bright.'
        )
        world.facts["outcome"] = "clear"
    elif score >= phrase.difficulty + 1:
        child.memes["pride"] += 1
        child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
        world.say(
            f'Then {child.id} tried again. "\"{phrase.text},\"" {child.pronoun()} said softly, '
            f"but this time every part of the word stayed together."
        )
        world.facts["outcome"] = "brave"
    else:
        raise StoryError(
            "This story setup leaves the child too stuck to finish the breakfast phrase."
        )


def share(world: World, child: Entity, helper: Entity, phrase: Phrase, helper_cfg: HelperKind) -> None:
    child.memes["love"] += 1
    toast = world.get("toast")
    toast.meters["shared"] += 1
    world.say(
        f'{helper.id} smiled the kind of smile that makes a room warmer. {helper_cfg.ending}'
    )
    world.say(
        f"{child.id} carried the plate with both hands. The toast was still warm, and the whole table answered with a happy "
        f'"crunch-crunch!"'
    )


def tell(
    setting: Setting,
    phrase: Phrase,
    method: Method,
    helper_cfg: HelperKind,
    *,
    child_name: str = "Mina",
    child_type: str = "girl",
    cools: int = 0,
) -> World:
    world = World(setting)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_type,
            role="child",
            traits=["gentle", "careful"],
            attrs={"method_boost": 0, "method_id": "", "helper_kind": helper_cfg.id},
        )
    )
    helper = world.add(
        Entity(
            id=helper_cfg.type.capitalize() if helper_cfg.type not in {"grandmother", "grandfather"} else helper_cfg.label_word if hasattr(helper_cfg, "label_word") else helper_cfg.type.capitalize(),
            kind="character",
            type=helper_cfg.type,
            role="helper",
            attrs={"warmth": helper_cfg.warmth},
        )
    )
    if helper_cfg.type == "grandmother":
        helper.id = "Grandma"
    elif helper_cfg.type == "grandfather":
        helper.id = "Grandpa"
    elif helper_cfg.type == "mother":
        helper.id = "Mom"
    elif helper_cfg.type == "father":
        helper.id = "Dad"
    else:
        helper.id = "Aunt"

    toast = world.add(
        Entity(
            id="toast",
            type="toast",
            label="toast",
            attrs={"topping": phrase.topping},
        )
    )
    phrase_ent = world.add(
        Entity(
            id="phrase",
            type="phrase",
            label=phrase.text,
        )
    )
    phrase_ent.meters["clarity"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["courage"] = 0.0
    child.memes["hope"] = 0.0
    toast.meters["popped"] = 0.0
    toast.meters["buttered"] = 0.0
    toast.meters["warmth"] = 0.0
    toast.meters["coolness"] = 0.0

    introduce(world, child, helper, phrase)
    want_to_say(world, child, phrase)

    world.para()
    toaster_pops(world, child, helper, phrase)
    stumble(world, child, phrase)
    helper_comforts(world, child, helper, helper_cfg)

    world.para()
    practice(world, child, helper, phrase, method)
    try_again(world, child, helper, phrase, cools)
    share(world, child, helper, phrase, helper_cfg)

    world.facts.update(
        child=child,
        helper=helper,
        helper_cfg=helper_cfg,
        phrase_cfg=phrase,
        method_cfg=method,
        toast=toast,
        setting=setting,
        clear=world.facts["outcome"] == "clear",
        practiced=child.meters["practiced"] >= THRESHOLD,
        cools=cools,
    )
    return world


SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        place="the sunny kitchen",
        table_detail="A blue plate waited on the table, and the morning light made the jam jar shine.",
        room_sound="From the window came a soft sparrow chirp, and under it all was the toaster's little hum.",
        tags={"home", "breakfast"},
    ),
    "breakfast_nook": Setting(
        id="breakfast_nook",
        place="the breakfast nook by the window",
        table_detail="A small cloth with red checks covered the table, and two mugs sent up sleepy curls of steam.",
        room_sound='Chair legs whispered on the floor while the toaster went "bzzzz."',
        tags={"home", "breakfast"},
    ),
    "grandma_kitchen": Setting(
        id="grandma_kitchen",
        place="Grandma's cozy kitchen",
        table_detail="A flowered plate sat ready beside a jar of cinnamon and a little butter dish.",
        room_sound='A clock said "tick-tock" above the sink, and the toaster purred nearby.',
        tags={"grandma", "breakfast"},
    ),
}

PHRASES = {
    "toast": Phrase(
        id="toast",
        text="toast",
        topping="plain",
        syllables=1,
        tricky="start_t",
        practice_sound="t-t-toast",
        difficulty=2,
        tags={"toast", "pronunciation"},
    ),
    "buttered_toast": Phrase(
        id="buttered_toast",
        text="buttered toast",
        topping="butter",
        syllables=3,
        tricky="melted_flow",
        practice_sound="buh-buh-buttered",
        buttered=True,
        difficulty=3,
        tags={"toast", "butter", "pronunciation"},
    ),
    "cinnamon_toast": Phrase(
        id="cinnamon_toast",
        text="cinnamon toast",
        topping="cinnamon",
        syllables=4,
        tricky="rhythm",
        practice_sound="cin-na-mon",
        dusted=True,
        difficulty=4,
        tags={"toast", "cinnamon", "pronunciation"},
    ),
    "honey_toast": Phrase(
        id="honey_toast",
        text="honey toast",
        topping="honey",
        syllables=3,
        tricky="open_mouth",
        practice_sound="hoh... honey",
        drizzled=True,
        difficulty=3,
        tags={"toast", "honey", "pronunciation"},
    ),
}

METHODS = {
    "tap": Method(
        id="tap",
        label="tap-tap practice",
        cue="Tap the first sound on the table.",
        sound_effect="tap-tap",
        boost=3,
        supports={"start_t"},
        max_syllables=2,
        tags={"practice"},
    ),
    "mirror": Method(
        id="mirror",
        label="mirror practice",
        cue="Watch the mouth shape in a shiny spoon.",
        sound_effect="mm",
        boost=3,
        supports={"open_mouth", "melted_flow"},
        max_syllables=3,
        tags={"practice"},
    ),
    "clap": Method(
        id="clap",
        label="clap-clap practice",
        cue="Break the long word into beats.",
        sound_effect="clap-clap-clap",
        boost=4,
        supports={"rhythm"},
        max_syllables=5,
        tags={"practice", "beats"},
    ),
    "hum": Method(
        id="hum",
        label="humming practice",
        cue="Relax into a tiny tune first.",
        sound_effect="hmm-hmm",
        boost=2,
        supports={"melted_flow", "open_mouth"},
        max_syllables=3,
        tags={"practice", "song"},
    ),
}

HELPERS = {
    "mom": HelperKind(
        id="mom",
        type="mother",
        warmth=3,
        opening="Mom touched the edge of the plate with one finger and kept her voice soft.",
        ending='"There it is," Mom said. "You found the word and the word found you."',
        tags={"family"},
    ),
    "dad": HelperKind(
        id="dad",
        type="father",
        warmth=3,
        opening="Dad leaned on the counter and smiled with his whole face.",
        ending='"That sounded just right," Dad said, giving the table a pleased little nod.',
        tags={"family"},
    ),
    "grandma": HelperKind(
        id="grandma",
        type="grandmother",
        warmth=4,
        opening="Grandma patted the chair beside her and opened her arms wide.",
        ending='"My brave breakfast helper," Grandma said, kissing the top of the child\'s head.',
        tags={"family", "grandma"},
    ),
    "grandpa": HelperKind(
        id="grandpa",
        type="grandfather",
        warmth=4,
        opening="Grandpa's eyes crinkled kindly behind his glasses.",
        ending='"That was a fine clear word," Grandpa said, as proud as if it were a song.',
        tags={"family", "grandpa"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Ava", "Nora", "Ella", "Lucy", "Tess", "Maya"]
BOY_NAMES = ["Owen", "Ben", "Theo", "Max", "Eli", "Noah", "Sam", "Leo"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    phrase = f["phrase_cfg"]
    helper = f["helper"]
    method = f["method_cfg"]
    outcome = world.facts["outcome"]
    close = "clearly" if outcome == "clear" else "bravely"
    return [
        f'Write a heartwarming breakfast story for a 3-to-5-year-old that includes the words "toast" and "pronunciation".',
        f"Tell a gentle story where a child named {child.id} struggles to say "
        f'"{phrase.text}", then practices with {helper.id} using {method.label} and finally says it {close}.',
        'Write a story full of tiny kitchen sound effects like "POP!" and "crunch-crunch!" with a loving family ending.',
    ]


KNOWLEDGE = {
    "toast": [
        (
            "What is toast?",
            "Toast is bread that has been heated until it turns brown and a little crisp. It smells warm and often makes a crunchy sound when you bite it.",
        )
    ],
    "pronunciation": [
        (
            "What does pronunciation mean?",
            "Pronunciation means the way a word is said out loud. Practicing pronunciation can help words feel easier and clearer in your mouth.",
        )
    ],
    "cinnamon": [
        (
            "What is cinnamon?",
            "Cinnamon is a sweet brown spice made from tree bark. People sprinkle a little on food to make it smell warm and cozy.",
        )
    ],
    "butter": [
        (
            "Why does butter melt on hot toast?",
            "Butter melts because toast is warm. The heat turns the butter soft and shiny so it can spread across the bread.",
        )
    ],
    "honey": [
        (
            "What is honey?",
            "Honey is a sweet golden food that bees make from flower nectar. It drips slowly and tastes sweet on bread or toast.",
        )
    ],
    "practice": [
        (
            "Why does practice help with a hard word?",
            "Practice helps because your mouth and ears get another chance to learn the sounds. Going slowly can make the word feel less bumpy.",
        )
    ],
}
KNOWLEDGE_ORDER = ["toast", "pronunciation", "butter", "cinnamon", "honey", "practice"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    phrase = f["phrase_cfg"]
    method = f["method_cfg"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who wanted to say {phrase.text} at breakfast, and {helper.id}, who helped gently. The story stays close to their small kitchen moment.",
        ),
        (
            f'Why was {child.id} worried about saying "{phrase.text}"?',
            f'{child.id} wanted to carry the plate and announce the toast proudly, but the pronunciation felt bumpy in {child.pronoun("possessive")} mouth. That made {child.pronoun("object")} feel shy right when it mattered.',
        ),
        (
            "What sound happened when the toast was ready?",
            'The toaster went "POP!" and the toast jumped up. That little sound made the breakfast moment feel real and cozy.',
        ),
        (
            f"How did {helper.id} help?",
            f"{helper.id} stayed calm and used {method.label}. Instead of hurrying, {helper.pronoun()} gave {child.id} one small way to practice the sounds.",
        ),
    ]
    if outcome == "clear":
        qa.append(
            (
                f"How did the story change by the end?",
                f"At first {child.id} felt embarrassed and looked down at the plate. By the end, {child.pronoun()} said {phrase.text} clearly and carried the warm toast to the table with pride.",
            )
        )
    else:
        qa.append(
            (
                f"How did the story change by the end?",
                f"At first {child.id} felt stuck on the word. By the end, {child.pronoun()} said {phrase.text} softly but all the way through, which was a brave kind of success.",
            )
        )
    qa.append(
        (
            "Why is this a heartwarming story?",
            f"It is heartwarming because the helper does not laugh or rush the child. The warm toast, the patient practice, and the shared crunch at the end all show love.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"toast", "pronunciation", "practice"}
    phrase = world.facts["phrase_cfg"]
    if phrase.buttered:
        tags.add("butter")
    if phrase.dusted:
        tags.add("cinnamon")
    if phrase.drizzled:
        tags.add("honey")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="kitchen",
        phrase="toast",
        method="tap",
        helper="mom",
        child_name="Mina",
        child_type="girl",
        cools=0,
    ),
    StoryParams(
        setting="grandma_kitchen",
        phrase="cinnamon_toast",
        method="clap",
        helper="grandma",
        child_name="Owen",
        child_type="boy",
        cools=1,
    ),
    StoryParams(
        setting="breakfast_nook",
        phrase="buttered_toast",
        method="mirror",
        helper="dad",
        child_name="Lila",
        child_type="girl",
        cools=1,
    ),
    StoryParams(
        setting="kitchen",
        phrase="honey_toast",
        method="hum",
        helper="grandpa",
        child_name="Theo",
        child_type="boy",
        cools=0,
    ),
]


ASP_RULES = r"""
fits(P, M) :- phrase(P), method(M), tricky(P, T), supports(M, T), syllables(P, S), max_syllables(M, MX), S <= MX.
viable(P, M, H) :- fits(P, M), helper(H), difficulty(P, D), boost(M, B), warmth(H, W), B + W - 1 >= D + 1.
valid(S, P, M, H) :- setting(S), viable(P, M, H).

score(B + W - C) :- chosen_method(M), boost(M, B), chosen_helper(H), warmth(H, W), cools(C).
outcome(clear) :- chosen_phrase(P), difficulty(P, D), score(S), S >= D + 3.
outcome(brave) :- chosen_phrase(P), difficulty(P, D), score(S), S >= D + 1, S < D + 3.
outcome(stuck) :- chosen_phrase(P), difficulty(P, D), score(S), S < D + 1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, phrase in PHRASES.items():
        lines.append(asp.fact("phrase", pid))
        lines.append(asp.fact("syllables", pid, phrase.syllables))
        lines.append(asp.fact("tricky", pid, phrase.tricky))
        lines.append(asp.fact("difficulty", pid, phrase.difficulty))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("boost", mid, method.boost))
        lines.append(asp.fact("max_syllables", mid, method.max_syllables))
        for t in sorted(method.supports):
            lines.append(asp.fact("supports", mid, t))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("warmth", hid, helper.warmth))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_phrase", params.phrase),
            asp.fact("chosen_method", params.method),
            asp.fact("chosen_helper", params.helper),
            asp.fact("cools", params.cools),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming toast-and-pronunciation story world. Unspecified choices are randomized with a seed."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--phrase", choices=PHRASES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--cools", type=int, choices=[0, 1], help="whether the toast cools a little before the child speaks")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.phrase and args.method:
        phrase = PHRASES[args.phrase]
        method = METHODS[args.method]
        if not method_fits(phrase, method):
            helper = HELPERS[args.helper] if args.helper else None
            raise StoryError(explain_rejection(phrase, method, helper))
    if args.phrase and args.method and args.helper:
        if outcome_of_values(PHRASES[args.phrase], METHODS[args.method], HELPERS[args.helper], 1) == "stuck":
            raise StoryError(explain_rejection(PHRASES[args.phrase], METHODS[args.method], HELPERS[args.helper]))

    combos = [
        c
        for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.phrase is None or c[1] == args.phrase)
        and (args.method is None or c[2] == args.method)
        and (args.helper is None or c[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, phrase_id, method_id, helper_id = rng.choice(sorted(combos))
    child_type = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    cools = args.cools if args.cools is not None else rng.choice([0, 1])
    if outcome_of_values(PHRASES[phrase_id], METHODS[method_id], HELPERS[helper_id], cools) == "stuck":
        cools = 0
    return StoryParams(
        setting=setting_id,
        phrase=phrase_id,
        method=method_id,
        helper=helper_id,
        child_name=child_name,
        child_type=child_type,
        cools=cools,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        phrase = PHRASES[params.phrase]
        method = METHODS[params.method]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"Unknown story parameter: {err.args[0]}") from None

    if not method_fits(phrase, method):
        raise StoryError(explain_rejection(phrase, method, helper))
    if outcome_of_values(phrase, method, helper, params.cools) == "stuck":
        raise StoryError(explain_rejection(phrase, method, helper))

    world = tell(
        setting=setting,
        phrase=phrase,
        method=method,
        helper_cfg=helper,
        child_name=params.child_name,
        child_type=params.child_type,
        cools=params.cools,
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
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"resolve_params unexpectedly failed for seed {seed}")
            break

    bad = 0
    for p in cases:
        py = outcome_of_values(PHRASES[p.phrase], METHODS[p.method], HELPERS[p.helper], p.cools)
        asp = asp_outcome(p)
        if py != asp:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("Generated empty story.")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
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
        print(f"{len(combos)} compatible (setting, phrase, method, helper) combos:\n")
        for setting_id, phrase_id, method_id, helper_id in combos:
            print(f"  {setting_id:15} {phrase_id:16} {method_id:8} {helper_id}")
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
            header = f"### {p.child_name}: {p.phrase} with {p.helper} using {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
