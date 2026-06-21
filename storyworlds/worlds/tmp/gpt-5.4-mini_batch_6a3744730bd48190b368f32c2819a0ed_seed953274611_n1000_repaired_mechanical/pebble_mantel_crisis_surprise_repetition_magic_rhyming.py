#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pebble_mantel_crisis_surprise_repetition_magic_rhyming.py
==========================================================================================

A tiny rhyming storyworld about a little pebble, a mantel display, and a sudden
crisis that gets solved with a surprise trick and a repeated magic rhyme.

Premise
-------
A child loves a shiny pebble and places it on the mantel as part of a pretend
display. A small crisis happens when the pebble is needed for a surprise magic
game, and the child must choose whether to keep it safe, return it, or use it
carefully. The storyworld models the pebble as a physical object, the mantel as
a special place, and the crisis as a state change that can be eased by a magical
rhyming routine.

The stories are intentionally small, child-facing, and authored with a soft
rhythm. They are built from simulation state, not from a frozen paragraph.
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
class StoryParams:
    setting: str
    pebble: str
    mantel: str
    crisis: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    adult: str
    magic: str
    repetition: str
    surprise: str
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


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    where_pebble_belongs: str
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
class Pebble:
    id: str
    label: str
    phrase: str
    shine: str
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
class Mantel:
    id: str
    label: str
    phrase: str
    near: str
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
class Crisis:
    id: str
    label: str
    trigger: str
    danger: str
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
class Magic:
    id: str
    rhyme: str
    repeat_line: str
    effect: str
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


def _r_crisis(world: World) -> list[str]:
    out: list[str] = []
    pebble = world.get("pebble")
    mantel = world.get("mantel")
    if pebble.meters["moved"] >= THRESHOLD and pebble.attrs.get("on_mantel"):
        sig = ("crisis",)
        if sig not in world.fired:
            world.fired.add(sig)
            mantel.meters["wobbly"] += 1
            out.append("__crisis__")
    return out


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    if world.get("magic").memes["chanting"] >= 2 * THRESHOLD:
        sig = ("repetition",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("child").memes["courage"] += 1
            out.append("The little words came round again, soft and clear.")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    if world.get("surprise").memes["revealed"] >= THRESHOLD:
        sig = ("surprise",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("A sparkly helper winked out of the shade.")
    return out


CAUSAL_RULES = [
    Rule("crisis", "physical", _r_crisis),
    Rule("repetition", "social", _r_repetition),
    Rule("surprise", "social", _r_surprise),
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


def crisis_risk(pebble: Pebble, mantel: Mantel) -> bool:
    return True if pebble.label and mantel.label else False


def safe_magic(magic: Magic) -> bool:
    return bool(magic.rhyme and magic.repeat_line)


def tell(setting: Setting, pebble: Pebble, mantel: Mantel, crisis: Crisis, magic: Magic,
         child_name: str, child_gender: str, helper_name: str, helper_gender: str,
         adult_name: str, surprise_name: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    adult = world.add(Entity(id=adult_name, kind="character", type="mother", role="adult", label="the grown-up"))
    peb = world.add(Entity(id="pebble", type="thing", label=pebble.label, attrs={"on_mantel": True}))
    man = world.add(Entity(id="mantel", type="place", label=mantel.label, attrs={"special": True}))
    cri = world.add(Entity(id="crisis", type="event", label=crisis.label))
    sur = world.add(Entity(id="surprise", type="thing", label=surprise_name))
    mag = world.add(Entity(id="magic", type="thing", label=magic.id))
    world.facts["setting"] = setting
    world.facts["pebble_cfg"] = pebble
    world.facts["mantel_cfg"] = mantel
    world.facts["crisis_cfg"] = crisis
    world.facts["magic_cfg"] = magic
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["adult"] = adult
    world.facts["surprise"] = sur

    child.memes["love"] += 1
    world.say(
        f"In {setting.place}, {child.id} kept a pebble on the mantel and liked its bright little shine."
    )
    world.say(
        f"It sat so still, so neat, on the mantel's sweet shelf, like a moon in a room all by itself."
    )
    world.para()
    helper.memes["curious"] += 1
    world.say(
        f"Then {helper.id} peeked and said, \"That pebble looks clever; it glows like a star, near and far.\""
    )
    world.say(
        f"But {adult.label_word} smiled, for a small crisis had started: the pebble must stay where it was, dear and charted."
    )
    peb.meters["moved"] += 1
    peb.attrs["on_mantel"] = True
    propagate(world, narrate=False)
    world.say(
        f"{crisis.trigger.capitalize()}! The mantel grew wobbly, and everyone froze in the hush of the rowdy and nubby."
    )
    world.para()
    sur.memes["revealed"] += 1
    mag.memes["chanting"] += 1
    world.say(
        f"Then came a surprise: {surprise_name} appeared, and {helper.id} started a rhyme, once, then twice, then twice."
    )
    world.say(
        f"\"{magic.rhyme}... {magic.repeat_line}... {magic.rhyme}!\" they sang with a grin."
    )
    propagate(world, narrate=False)
    if safe_magic(magic):
        world.say(
            f"The pebble slid back to its place on the mantel, and the crisis grew calm as a warm little hymn."
        )
        world.say(
            f"{adult.label_word.capitalize()} clapped, and the room felt light; the pebble still shone, all snug and bright."
        )
    else:
        raise StoryError("The chosen magic is too weak to resolve this crisis.")
    world.facts.update(outcome="resolved")
    return world


SETTINGS = {
    "parlor": Setting(id="parlor", place="the parlor", mood="cozy", where_pebble_belongs="mantel"),
    "hall": Setting(id="hall", place="the hall", mood="quiet", where_pebble_belongs="mantel"),
}

PEBBLES = {
    "pebble": Pebble(id="pebble", label="pebble", phrase="a shiny pebble", shine="little and bright", tags={"pebble"}),
    "glowpebble": Pebble(id="glowpebble", label="glow pebble", phrase="a glow pebble", shine="soft and bright", tags={"pebble", "magic"}),
}

MANTELS = {
    "mantel": Mantel(id="mantel", label="mantel", phrase="the mantel", near="above the hearth", tags={"mantel"}),
}

CRISES = {
    "crisis": Crisis(id="crisis", label="crisis", trigger="crisis", danger="wobble", tags={"crisis"}),
    "surprise": Crisis(id="surprise", label="surprise", trigger="surprise", danger="sudden turn", tags={"surprise"}),
}

MAGICS = {
    "repeat_charm": Magic(id="repeat_charm", rhyme="Pebble by the mantel, stay so still", repeat_line="Pebble by the mantel, stay so still", effect="returns the pebble to its place", tags={"magic", "repetition"}),
    "spark_song": Magic(id="spark_song", rhyme="Twinkle small and twinkle near", repeat_line="Twinkle small and twinkle near", effect="makes the room feel brave", tags={"magic", "surprise"}),
}

CURATED = [
    StoryParams(
        setting="parlor",
        pebble="pebble",
        mantel="mantel",
        crisis="crisis",
        child="Mia",
        child_gender="girl",
        helper="Noah",
        helper_gender="boy",
        adult="mother",
        magic="repeat_charm",
        repetition="repeat",
        surprise="lantern-bird",
    ),
    StoryParams(
        setting="hall",
        pebble="glowpebble",
        mantel="mantel",
        crisis="surprise",
        child="Theo",
        child_gender="boy",
        helper="Luna",
        helper_gender="girl",
        adult="father",
        magic="spark_song",
        repetition="again",
        surprise="silver mouse",
    ),
]

GIRL_NAMES = ["Mia", "Luna", "Nia", "Ava", "Zoe"]
BOY_NAMES = ["Theo", "Noah", "Eli", "Max", "Leo"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for p in PEBBLES:
            for c in CRISES:
                out.append((s, p, c))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming tiny storyworld about a pebble, a mantel, and a crisis.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--pebble", choices=PEBBLES)
    ap.add_argument("--mantel", choices=MANTELS)
    ap.add_argument("--crisis", choices=CRISES)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--child")
    ap.add_argument("--helper")
    ap.add_argument("--adult", choices=["mother", "father"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    pebble = args.pebble or rng.choice(list(PEBBLES))
    mantel = args.mantel or rng.choice(list(MANTELS))
    crisis = args.crisis or rng.choice(list(CRISES))
    magic = args.magic or rng.choice(list(MAGICS))
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if child_gender == "girl" else "girl"
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(["mother", "father"])
    if not crisis_risk(PEBBLES[pebble], MANTELS[mantel]):
        raise StoryError("This pebble and mantel do not create a believable crisis.")
    return StoryParams(
        setting=setting, pebble=pebble, mantel=mantel, crisis=crisis,
        child=child, child_gender=child_gender, helper=helper, helper_gender=helper_gender,
        adult=adult, magic=magic, repetition="again", surprise="sparrow",
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a 3-to-5-year-old that includes the words "{f["pebble_cfg"].label}", "{f["mantel_cfg"].label}", and "{f["crisis_cfg"].label}".',
        f"Tell a gentle story where {f['child'].id} keeps a pebble on the mantel, a small crisis happens, and a surprise magic rhyme helps set things right.",
        f"Write a child-facing rhyming tale with repetition and a magical surprise ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    peb = f["pebble_cfg"]
    man = f["mantel_cfg"]
    cri = f["crisis_cfg"]
    mag = f["magic_cfg"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, the pebble, and the mantel. A small crisis pushes the story forward, and the grown-up helps finish it safely."),
        ("What happened to the pebble?",
         f"The pebble started on the mantel, then it was moved during the crisis, and finally it was put back where it belonged. That return shows the trouble has passed."),
        ("How did the magic help?",
         f"The magic rhyme was repeated twice, and that repetition gave the moment a steady rhythm. The surprise helped the pebble settle back into place."),
        ("Was the grown-up upset?",
         f"No. {adult.label_word.capitalize()} stayed calm and happy, because the magical rhyme helped solve the crisis without any hurt or broken things."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a pebble?",
         "A pebble is a small stone. Pebbles are often smooth because water and time wear their sharp edges away."),
        ("What is a mantel?",
         "A mantel is a shelf-like place above a fireplace. People often put small decorations there."),
        ("What is a crisis?",
         "A crisis is a problem that needs care right away. It can feel scary, but it can still be handled calmly."),
        ("What is repetition?",
         "Repetition means saying or doing something again and again. It can make a rhyme feel steady and easy to remember."),
        ("What is a surprise?",
         "A surprise is something you do not expect. In stories, a surprise can make a moment feel magical."),
        ("What is magic in a story?",
         "Magic in a story is something impossible or wonderful that helps the characters solve a problem."),
    ]


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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
crisis(pebble,mantel) :- pebble_on_mantel, crisis_needed.
repetition :- chanting(2).
surprise :- revealed(1).
resolved :- crisis(pebble,mantel), repetition, surprise.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PEBBLES:
        lines.append(asp.fact("pebble", pid))
    for mid in MANTELS:
        lines.append(asp.fact("mantel", mid))
    for cid in CRISES:
        lines.append(asp.fact("crisis", cid))
    for mid in MAGICS:
        lines.append(asp.fact("magic", mid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show setting/1.\n#show pebble/1.\n#show crisis/1."))
    return sorted(set(asp.atoms(model, "setting"))), sorted(set(asp.atoms(model, "pebble"))), sorted(set(asp.atoms(model, "crisis")))


def asp_verify() -> int:
    rc = 0
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, pebble=None, mantel=None, crisis=None, magic=None, child=None, helper=None, adult=None), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"FAIL: generate smoke test crashed: {e}")
        return 1
    print("OK: smoke-tested normal story generation.")
    try:
        import asp
        _ = asp_program("", "#show resolved/0.")
    except Exception as e:
        print(f"FAIL: ASP helper setup failed: {e}")
        rc = 1
    return rc


def tell_story(params: StoryParams) -> StorySample:
    for key, table in (("setting", SETTINGS), ("pebble", PEBBLES), ("mantel", MANTELS), ("crisis", CRISES), ("magic", MAGICS)):
        if getattr(params, key) not in table:
            raise StoryError(f"Unknown {key}: {getattr(params, key)}")
    world = tell(
        SETTINGS[params.setting], PEBBLES[params.pebble], MANTELS[params.mantel],
        CRISES[params.crisis], MAGICS[params.magic],
        params.child, params.child_gender, params.helper, params.helper_gender,
        params.adult, "spark-bird",
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return tell_story(params)


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
        print(asp_program("", "#show setting/1.\n#show pebble/1.\n#show crisis/1.\n#show magic/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available, but this tiny world is primarily prose-driven.")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
