#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cockatoo_louse_sound_effects_humor_moral_value.py
==============================================================================

A standalone story world for a tiny folk-tale domain: a proud cockatoo gets an
itchy, messy crest; a tiny louse notices the trouble; the big bird must decide
whether to listen to small wisdom. The tale uses sound effects, gentle humor,
and a moral ending.

The world model enforces a simple reasonableness rule: each kind of crest mess
needs a fitting way to clean it, and the chosen setting must actually afford
that remedy. A dusty crest can be rinsed or brushed; sticky sap needs soaking
or rinsing; a thorn caught in feathers must be picked out or combed out. Invalid
combinations are rejected with a readable explanation.

Run it
------
    python storyworlds/worlds/gpt-5.4/cockatoo_louse_sound_effects_humor_moral_value.py
    python storyworlds/worlds/gpt-5.4/cockatoo_louse_sound_effects_humor_moral_value.py --mess sap --remedy brush
    python storyworlds/worlds/gpt-5.4/cockatoo_louse_sound_effects_humor_moral_value.py --all
    python storyworlds/worlds/gpt-5.4/cockatoo_louse_sound_effects_humor_moral_value.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/cockatoo_louse_sound_effects_humor_moral_value.py --verify
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
LISTEN_MIN = 5


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
        female = {"hen", "mother", "woman", "girl"}
        male = {"cockatoo", "bird", "man", "boy"}
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
class Setting:
    id: str
    place: str
    opening: str
    affords: set[str] = field(default_factory=set)
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
class Mess:
    id: str
    label: str
    source: str
    sound: str
    symptom: str
    needed: set[str] = field(default_factory=set)
    funny: str = ""
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
class Remedy:
    id: str
    label: str
    verb: str
    success: str
    fail: str
    qa_text: str
    provides: set[str] = field(default_factory=set)
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
class Temper:
    id: str
    boast: str
    first_reply: str
    ending_feeling: str
    listening: int = 0
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
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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


def _r_itch_to_noise(world: World) -> list[str]:
    out: list[str] = []
    cockatoo = world.get("cockatoo")
    if cockatoo.meters["itch"] >= THRESHOLD:
        sig = ("itch_noise",)
        if sig not in world.fired:
            world.fired.add(sig)
            cockatoo.meters["fuss"] += 1
            world.get("louse").memes["alert"] += 1
            out.append("__itch__")
    return out


def _r_mock_to_pride(world: World) -> list[str]:
    out: list[str] = []
    cockatoo = world.get("cockatoo")
    if cockatoo.memes["mocked"] >= THRESHOLD:
        sig = ("mock_pride",)
        if sig not in world.fired:
            world.fired.add(sig)
            cockatoo.memes["pride"] += 1
            out.append("__pride__")
    return out


def _r_clean_to_relief(world: World) -> list[str]:
    out: list[str] = []
    cockatoo = world.get("cockatoo")
    if cockatoo.meters["clean"] >= THRESHOLD:
        sig = ("clean_relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            cockatoo.meters["itch"] = 0.0
            cockatoo.meters["fuss"] = 0.0
            cockatoo.memes["relief"] += 1
            world.get("louse").memes["glad"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="itch_to_noise", tag="physical", apply=_r_itch_to_noise),
    Rule(name="mock_to_pride", tag="social", apply=_r_mock_to_pride),
    Rule(name="clean_to_relief", tag="physical", apply=_r_clean_to_relief),
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


def mess_fixable_in_setting(setting: Setting, mess: Mess, remedy: Remedy) -> bool:
    return bool(mess.needed & remedy.provides) and remedy.id in setting.affords


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for mess_id, mess in MESSES.items():
            for remedy_id, remedy in REMEDIES.items():
                for temper_id in TEMPERS:
                    if mess_fixable_in_setting(setting, mess, remedy):
                        combos.append((setting_id, mess_id, remedy_id, temper_id))
    return combos


def explain_rejection(setting: Setting, mess: Mess, remedy: Remedy) -> str:
    if remedy.id not in setting.affords:
        return (
            f"(No story: {setting.place} does not offer {remedy.label}, so the cockatoo "
            f"cannot sensibly use that remedy there. Pick a place that affords it.)"
        )
    return (
        f"(No story: {mess.label} needs one of {sorted(mess.needed)}, but {remedy.label} "
        f"provides only {sorted(remedy.provides)}. The fix would not really solve the problem.)"
    )


def can_listen(temper: Temper) -> bool:
    return temper.listening >= LISTEN_MIN


def predict_relief(world: World, mess: Mess, remedy: Remedy) -> dict:
    sim = world.copy()
    _apply_remedy(sim, mess, remedy, narrate=False)
    cockatoo = sim.get("cockatoo")
    return {
        "clean": cockatoo.meters["clean"] >= THRESHOLD,
        "itch": cockatoo.meters["itch"],
        "relief": cockatoo.memes["relief"],
    }


def introduce(world: World, cockatoo: Entity, louse: Entity, temper: Temper) -> None:
    cockatoo.memes["pride"] += 1
    cockatoo.memes["showoff"] += 1
    world.say(
        f"In the days when birds still argued with their own feathers, there lived "
        f"a cockatoo named {cockatoo.id} beside {world.setting.place}. {world.setting.opening}"
    )
    world.say(
        f"{cockatoo.id} loved to lift his yellow crest and strut in a ring, and he often "
        f"said, {temper.boast}"
    )
    world.say(
        f"Hidden among the soft feathers lived a tiny louse named {louse.id}, so small "
        f"that even a seed could have worn her as a hat."
    )


def trouble_starts(world: World, cockatoo: Entity, mess: Mess) -> None:
    cockatoo.meters["itch"] += 1
    cockatoo.meters["mess"] += 1
    propagate(world, narrate=False)
    world.say(
        f"One morning, {cockatoo.id} pushed through {mess.source}, and at once his crest went "
        f'"{mess.sound}!" {mess.symptom}.'
    )
    if mess.funny:
        world.say(mess.funny)


def louse_notices(world: World, louse: Entity, mess: Mess) -> None:
    louse.memes["care"] += 1
    world.say(
        f'From inside the feathers came a tiny voice: "{mess.sound}! {mess.sound}! '
        f'Slow down, great sir. Your fine head is in a pickle."'
    )


def boast_and_mock(world: World, cockatoo: Entity, louse: Entity, temper: Temper) -> None:
    cockatoo.memes["mocked"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{cockatoo.id} crossed his eyes to look upward, saw nothing but his own beak, '
        f'and snapped, "{temper.first_reply}"'
    )
    world.say(
        f"The louse nearly toppled over laughing, because the grand bird looked as if he were "
        f"trying to peck the moon off his own forehead."
    )


def failed_fussing(world: World, cockatoo: Entity, mess: Mess) -> None:
    cockatoo.meters["itch"] += 1
    cockatoo.meters["fuss"] += 1
    world.say(
        f"So {cockatoo.id} shook himself. Whuff! He stamped. Thump! He scratched. Scritch-scritch! "
        f"But {mess.label} only tangled deeper, and his proud crest stood up like a startled broom."
    )


def ask_help(world: World, louse: Entity, remedy: Remedy, setting: Setting) -> None:
    place_hint = {
        "river": "the clear edge of the river",
        "comb": "an old porcupine-quill comb under a root",
        "soak": "a broad leaf cup where rainwater gathered",
    }.get(remedy.id, setting.place)
    world.say(
        f'{louse.id} called, "If you stop dancing with your trouble for one breath, I can guide you to '
        f'{place_hint}."'
    )


def refuse_small_voice(world: World, cockatoo: Entity, louse: Entity, setting: Setting) -> None:
    cockatoo.memes["lonely"] += 1
    world.say(
        f'But {cockatoo.id} flapped away from the little voice and tried to hide his trouble behind a palm fan. '
        f'He strutted past the parrots, and they snickered when they heard the crest go "tick-tick" above him.'
    )
    world.say(
        f"By sunset he was tired, itchy, and no less ridiculous, so he returned to {setting.place} where "
        f"{louse.id} was still waiting."
    )


def choose_listening(world: World, cockatoo: Entity, louse: Entity) -> None:
    cockatoo.memes["trust"] += 1
    louse.memes["hope"] += 1
    world.say(
        f"At last the cockatoo lowered his crest. That was harder for him than hopping on one foot, but he did it."
    )
    world.say(
        f'"Little {louse.id}," he said, "my head is big, but today my wisdom is small. Show me the way."'
    )


def _apply_remedy(world: World, mess: Mess, remedy: Remedy, narrate: bool = True) -> bool:
    cockatoo = world.get("cockatoo")
    if not (mess.needed & remedy.provides):
        if narrate:
            world.say(remedy.fail.format(mess=mess.label))
        return False
    cockatoo.meters["clean"] += 1
    cockatoo.meters["mess"] = 0.0
    propagate(world, narrate=False)
    if narrate:
        world.say(remedy.success.format(mess=mess.label))
    return True


def clean_turn(world: World, cockatoo: Entity, louse: Entity, mess: Mess, remedy: Remedy) -> None:
    pred = predict_relief(world, mess, remedy)
    world.facts["predicted_relief"] = pred["relief"]
    world.facts["predicted_clean"] = pred["clean"]
    if _apply_remedy(world, mess, remedy, narrate=True):
        world.say(
            f'Soon the noisy crest went quiet: "{mess.sound}" no more. {cockatoo.id} blinked, then laughed so hard '
            f'that {louse.id} had to grab a feather to keep from bouncing away.'
        )


def lesson_ending(world: World, cockatoo: Entity, louse: Entity, temper: Temper, remedy: Remedy) -> None:
    cockatoo.memes["gratitude"] += 1
    cockatoo.memes["kindness"] += 1
    louse.memes["proud"] += 1
    world.say(
        f'From that day on, when {cockatoo.id} lifted his crest, he left room in his song for a tiny second voice. '
        f'Together they went "{cockatoo.id}: ka-kaa!" and "{louse.id}: tik-tik!" until even the monkeys laughed kindly.'
    )
    world.say(
        f"{cockatoo.id} thanked the louse and said that {temper.ending_feeling}. Ever after he listened before he "
        f"boasted, and he kept his crest neat with {remedy.label}."
    )
    world.say(
        "That is why old people say: do not laugh at small helpers. A tiny mouth may carry the biggest good sense."
    )


def tell(setting: Setting, mess: Mess, remedy: Remedy, temper: Temper,
         cockatoo_name: str = "Koro", louse_name: str = "Tika") -> World:
    world = World(setting)
    cockatoo = world.add(Entity(
        id=cockatoo_name,
        kind="character",
        type="cockatoo",
        label="the cockatoo",
        role="hero",
        traits=["proud", "showy"],
    ))
    louse = world.add(Entity(
        id=louse_name,
        kind="character",
        type="girl",
        label="the louse",
        role="helper",
        traits=["tiny", "sharp-eyed", "patient"],
    ))
    world.facts.update(
        setting=setting,
        mess=mess,
        remedy=remedy,
        temper=temper,
        listened=False,
        fixed=False,
        cockatoo=cockatoo,
        louse=louse,
    )
    cockatoo.meters["itch"] = 0.0
    cockatoo.meters["mess"] = 0.0
    cockatoo.meters["clean"] = 0.0
    cockatoo.meters["fuss"] = 0.0
    cockatoo.memes["pride"] = 0.0
    cockatoo.memes["mocked"] = 0.0
    cockatoo.memes["trust"] = 0.0
    cockatoo.memes["relief"] = 0.0
    cockatoo.memes["gratitude"] = 0.0
    louse.memes["care"] = 0.0
    louse.memes["hope"] = 0.0
    louse.memes["glad"] = 0.0
    louse.memes["proud"] = 0.0

    introduce(world, cockatoo, louse, temper)
    world.para()
    trouble_starts(world, cockatoo, mess)
    louse_notices(world, louse, mess)
    boast_and_mock(world, cockatoo, louse, temper)
    failed_fussing(world, cockatoo, mess)

    world.para()
    ask_help(world, louse, remedy, setting)
    if not can_listen(temper):
        refuse_small_voice(world, cockatoo, louse, setting)

    choose_listening(world, cockatoo, louse)
    world.facts["listened"] = True

    world.para()
    clean_turn(world, cockatoo, louse, mess, remedy)
    world.facts["fixed"] = cockatoo.meters["clean"] >= THRESHOLD

    world.para()
    lesson_ending(world, cockatoo, louse, temper, remedy)
    return world


SETTINGS = {
    "riverbank": Setting(
        id="riverbank",
        place="the green riverbank",
        opening="A broad river ran there with a hush-hush sound, and reeds bowed whenever the wind passed.",
        affords={"river", "soak", "comb"},
        tags={"river", "water"},
    ),
    "baobab": Setting(
        id="baobab",
        place="the shade of a hollow baobab",
        opening="The tree was so old that lizards used its roots as doorsteps and children said it remembered the first rain.",
        affords={"comb", "soak"},
        tags={"tree"},
    ),
    "market": Setting(
        id="market",
        place="the market gate",
        opening="At dawn the baskets thumped down, goats bleated, and every stall answered every other stall in cheerful noise.",
        affords={"comb", "river"},
        tags={"market"},
    ),
}

MESSES = {
    "dust": Mess(
        id="dust",
        label="dust",
        source="a cloud of red road dust",
        sound="foof",
        symptom="Fine dust slipped into every feather and made his head prickle at once",
        needed={"rinse", "brush"},
        funny="He sneezed so grandly that three dragonflies spun in the air like dropped pins.",
        tags={"dust", "itch"},
    ),
    "sap": Mess(
        id="sap",
        label="sticky sap",
        source="a split tamarind branch dripping sweet sap",
        sound="glup",
        symptom="The sweet gum glued the bright feathers together, and each step tugged at his scalp",
        needed={"rinse", "soak"},
        funny="When he tried to bow, one side of his crest bowed back a moment later, as if it had its own manners.",
        tags={"sticky", "itch"},
    ),
    "thorn": Mess(
        id="thorn",
        label="a thorn",
        source="a thorny bush where the berries hid",
        sound="tik",
        symptom="A little thorn lodged in the plume and poked him every time he turned",
        needed={"pick", "brush"},
        funny="He kept hopping in circles, pecking at the air, while the thorn rode along like a rude king.",
        tags={"thorn", "itch"},
    ),
}

REMEDIES = {
    "river": Remedy(
        id="river",
        label="a river rinse",
        verb="rinsed his crest in the river",
        success="The cockatoo bent low and rinsed his crest in the cool current until the {mess} washed free.",
        fail="The cockatoo splashed and splashed, but the {mess} only clung tighter.",
        qa_text="rinsed his crest in the cool river until the trouble washed away",
        provides={"rinse"},
        tags={"water", "river"},
    ),
    "comb": Remedy(
        id="comb",
        label="a quill comb",
        verb="combed through his crest with a quill",
        success="The louse showed him an old quill, and the cockatoo drew it through his crest until the {mess} came out.",
        fail="He combed and combed, but the {mess} stayed where it was.",
        qa_text="used a quill comb to work the trouble out of his crest",
        provides={"brush", "pick"},
        tags={"comb", "tool"},
    ),
    "soak": Remedy(
        id="soak",
        label="a leaf-cup soak",
        verb="soaked his crest in rainwater",
        success="The louse led him to a leaf cup full of rainwater, and he soaked his crest there until the {mess} loosened and slipped away.",
        fail="He soaked his crest for a long time, but the {mess} would not budge.",
        qa_text="soaked his crest in gathered rainwater until the mess loosened",
        provides={"soak"},
        tags={"water", "leaf"},
    ),
}

TEMPERS = {
    "vain": Temper(
        id="vain",
        boast='"No feather in the forest shines like mine!"',
        first_reply='Who speaks from my hairstyle? If you are smaller than a seed, be quieter than a seed.',
        ending_feeling="a proud bird could still become a wiser bird",
        listening=3,
        tags={"pride"},
    ),
    "showy": Temper(
        id="showy",
        boast='"When I dance, even the sun claps."',
        first_reply='Tiny feet should not give tall advice.',
        ending_feeling="his best song sounded finer when he sang it kindly",
        listening=5,
        tags={"pride", "humor"},
    ),
    "warmhearted": Temper(
        id="warmhearted",
        boast='"Watch me dance, and then come share my shade."',
        first_reply='Eh? A small voice with a large opinion!',
        ending_feeling="good manners sat better on him than bragging ever had",
        listening=7,
        tags={"kindness"},
    ),
}

COCKATOO_NAMES = ["Koro", "Maku", "Tambo", "Sefu", "Riko", "Balo"]
LOUSE_NAMES = ["Tika", "Piri", "Nini", "Sasa", "Lulu", "Mimi"]


@dataclass
class StoryParams:
    setting: str
    mess: str
    remedy: str
    temper: str
    cockatoo_name: str
    louse_name: str
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
    "cockatoo": [
        ("What is a cockatoo?",
         "A cockatoo is a kind of parrot with a curved beak and a crest of feathers on its head. Many cockatoos can be noisy and playful.")
    ],
    "louse": [
        ("What is a louse?",
         "A louse is a very tiny insect that lives in hair or feathers. It is so small that a big animal might not notice it at first.")
    ],
    "itch": [
        ("Why does something stuck in feathers make an animal itchy?",
         "A feather or skin can feel itchy when dust, sap, or a thorn rubs against it again and again. The body notices the rubbing and wants to scratch.")
    ],
    "river": [
        ("Why can water help clean something sticky or dirty?",
         "Water can loosen dirt and wash it away. If the mess is soft enough, rinsing helps the surface feel clean again.")
    ],
    "comb": [
        ("What does a comb do?",
         "A comb separates hair or feathers so tangles and little bits of dirt can come out. It helps put things back in order.")
    ],
    "moral": [
        ("What is the moral of listening to small helpers?",
         "Someone tiny can still notice an important problem or know a good answer. Listening kindly can save trouble that pride would make worse.")
    ],
}
KNOWLEDGE_ORDER = ["cockatoo", "louse", "itch", "river", "comb", "moral"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cockatoo = f["cockatoo"]
    louse = f["louse"]
    mess = f["mess"]
    remedy = f["remedy"]
    setting = f["setting"]
    return [
        f'Write a short folk tale for a 3-to-5-year-old that includes the words "cockatoo" and "louse", uses sound effects, and ends with a moral.',
        f"Tell a gentle, funny folk tale where a proud cockatoo gets {mess.label} in his crest at {setting.place}, and a tiny louse helps him fix it with {remedy.label}.",
        f"Write a child-facing story in which {cockatoo.id} learns to listen to {louse.id}, a very small helper, after a noisy problem in his feathers.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    cockatoo = f["cockatoo"]
    louse = f["louse"]
    mess = f["mess"]
    remedy = f["remedy"]
    temper = f["temper"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a cockatoo named {cockatoo.id} and a tiny louse named {louse.id}. The big bird has the trouble, and the small one notices how to help."
        ),
        (
            f"What problem did {cockatoo.id} have?",
            f"{cockatoo.id} got {mess.label} stuck in his crest, and it made his head itchy and noisy. That is why he kept shaking, scratching, and looking silly."
        ),
        (
            f"What did the louse say when she noticed the trouble?",
            f"The louse told him to slow down because his fine head was in a pickle. She could see the trouble up close, so her tiny warning came before the fix."
        ),
        (
            f"Why did {cockatoo.id} look funny in the middle of the story?",
            f"He was too proud to listen at first, so he tried to dance and scratch the problem away by himself. That only made him fuss more, and his crest stood up in a ridiculous shape."
        ),
    ]
    if f.get("fixed"):
        qa.append((
            f"How did {cockatoo.id} solve the problem?",
            f"He finally listened to {louse.id} and {remedy.qa_text}. The remedy matched the kind of mess in his crest, so the itch and noise stopped."
        ))
    if f.get("listened"):
        qa.append((
            f"What did {cockatoo.id} learn at the end?",
            f"He learned that small helpers should not be laughed at. {temper.ending_feeling.capitalize()}, because good advice is good advice no matter how tiny the speaker is."
        ))
    qa.append((
        "What is the moral of the story?",
        "Do not let pride make you foolish. A small, kind helper may see the truth before a grand, noisy one does."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"cockatoo", "louse", "itch", "moral"}
    remedy = world.facts["remedy"]
    if "water" in remedy.tags or "river" in remedy.tags:
        tags.add("river")
    if "comb" in remedy.tags or "tool" in remedy.tags:
        tags.add("comb")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="riverbank",
        mess="sap",
        remedy="soak",
        temper="vain",
        cockatoo_name="Koro",
        louse_name="Tika",
    ),
    StoryParams(
        setting="market",
        mess="dust",
        remedy="river",
        temper="showy",
        cockatoo_name="Maku",
        louse_name="Nini",
    ),
    StoryParams(
        setting="baobab",
        mess="thorn",
        remedy="comb",
        temper="warmhearted",
        cockatoo_name="Sefu",
        louse_name="Piri",
    ),
    StoryParams(
        setting="riverbank",
        mess="thorn",
        remedy="comb",
        temper="showy",
        cockatoo_name="Riko",
        louse_name="Mimi",
    ),
]


def outcome_of(params: StoryParams) -> str:
    return "listened_and_fixed"


ASP_RULES = r"""
fixable(S, M, R) :- setting(S), mess(M), remedy(R), affords(S, R), needs(M, N), provides(R, N).

can_listen(T) :- temper(T), listening(T, L), listen_min(Min), L >= Min.
must_stumble_once(T) :- temper(T), not can_listen(T).

valid(S, M, R, T) :- setting(S), mess(M), remedy(R), temper(T), fixable(S, M, R).

outcome(listened_and_fixed) :- chosen_setting(S), chosen_mess(M), chosen_remedy(R), chosen_temper(T), valid(S, M, R, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for afford in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, afford))
    for mess_id, mess in MESSES.items():
        lines.append(asp.fact("mess", mess_id))
        for need in sorted(mess.needed):
            lines.append(asp.fact("needs", mess_id, need))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        for provide in sorted(remedy.provides):
            lines.append(asp.fact("provides", remedy_id, provide))
    for temper_id, temper in TEMPERS.items():
        lines.append(asp.fact("temper", temper_id))
        lines.append(asp.fact("listening", temper_id, temper.listening))
    lines.append(asp.fact("listen_min", LISTEN_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_setting", params.setting),
        asp.fact("chosen_mess", params.mess),
        asp.fact("chosen_remedy", params.remedy),
        asp.fact("chosen_temper", params.temper),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
    for s in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if mismatches:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome differences.")
    else:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated an empty story")
        print("OK: smoke-tested normal story generation.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a cockatoo, a louse, a noisy crest problem, and a moral."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mess", choices=MESSES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--temper", choices=TEMPERS)
    ap.add_argument("--cockatoo-name")
    ap.add_argument("--louse-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.mess and args.remedy:
        setting = SETTINGS[args.setting]
        mess = MESSES[args.mess]
        remedy = REMEDIES[args.remedy]
        if not mess_fixable_in_setting(setting, mess, remedy):
            raise StoryError(explain_rejection(setting, mess, remedy))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.mess is None or combo[1] == args.mess)
        and (args.remedy is None or combo[2] == args.remedy)
        and (args.temper is None or combo[3] == args.temper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, mess_id, remedy_id, temper_id = rng.choice(sorted(combos))
    cockatoo_name = args.cockatoo_name or rng.choice(COCKATOO_NAMES)
    louse_name = args.louse_name or rng.choice([n for n in LOUSE_NAMES if n != cockatoo_name])

    return StoryParams(
        setting=setting_id,
        mess=mess_id,
        remedy=remedy_id,
        temper=temper_id,
        cockatoo_name=cockatoo_name,
        louse_name=louse_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.mess not in MESSES:
        raise StoryError(f"(Unknown mess: {params.mess})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")
    if params.temper not in TEMPERS:
        raise StoryError(f"(Unknown temper: {params.temper})")

    setting = SETTINGS[params.setting]
    mess = MESSES[params.mess]
    remedy = REMEDIES[params.remedy]
    temper = TEMPERS[params.temper]
    if not mess_fixable_in_setting(setting, mess, remedy):
        raise StoryError(explain_rejection(setting, mess, remedy))

    world = tell(
        setting=setting,
        mess=mess,
        remedy=remedy,
        temper=temper,
        cockatoo_name=params.cockatoo_name,
        louse_name=params.louse_name,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, mess, remedy, temper) combos:\n")
        for setting, mess, remedy, temper in combos:
            print(f"  {setting:10} {mess:7} {remedy:6} {temper}")
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
            header = (
                f"### {p.cockatoo_name} and {p.louse_name}: {p.mess} at {p.setting} "
                f"({p.remedy}, {p.temper})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
