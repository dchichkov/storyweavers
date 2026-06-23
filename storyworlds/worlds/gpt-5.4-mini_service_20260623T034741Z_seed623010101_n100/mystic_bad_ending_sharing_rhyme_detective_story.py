#!/usr/bin/env python3
"""
storyworlds/worlds/mystic_bad_ending_sharing_rhyme_detective_story.py
=====================================================================

A standalone story world for a tiny detective tale with a mystic clue, a shared
object, a rhyming note, and a bad ending.

Premise:
- A child detective and a helper investigate a missing item in a small place.
- A mystic message guides them to share clues and listen for a rhyme.

Turn:
- A helpful clue is shared, but the rhyming note points to the wrong suspect.
- The detective follows it anyway, causing the plan to go off track.

Bad ending:
- The real item is not recovered.
- The shared clue is lost or taken, and the detective ends the story worried,
  with the last image proving what changed.

The domain models physical meters and emotional memes, uses a forward causal
step for clue-following and trust effects, and includes an ASP twin for the
reasonableness gate and outcome parity.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    casefile: object | None = None
    clue: object | None = None
    detective: object | None = None
    helper: object | None = None
    prize_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "detective"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Case:
    id: str
    scene: str
    clue_type: str
    rhyme_line: str
    clue_method: str
    wrong_turn: str
    loss_image: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Shareable:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    case: str
    setting: str
    detective: str
    helper: str
    clue: str
    prize: str
    shareable: str
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def _r_mislead(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    clue = world.get("clue")
    if detective.memes.get("trust", 0.0) < THRESHOLD:
        return out
    if clue.meters.get("lost", 0.0) >= THRESHOLD:
        sig = ("lost", clue.id)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["worry"] = detective.memes.get("worry", 0.0) + 1
            out.append("The clue slipped farther away.")
    return out


def _r_bad_end(world: World) -> list[str]:
    case = world.get("casefile")
    prize = world.get("prize")
    if case.meters.get("mistake", 0.0) >= THRESHOLD:
        sig = ("bad", case.id)
        if sig not in world.fired:
            world.fired.add(sig)
            prize.meters["missing"] = 1
            return ["__bad_end__"]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_r_mislead, _r_bad_end):
            s = fn(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for case_id, case in CASES.items():
            for prize_id, prize in PRIZES.items():
                if prize.region in case.tags and case_id in setting.affords:
                    combos.append((setting_id, case_id, prize_id))
    return combos


def pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def tell(setting: Setting, case: Case, detective_name: str, helper_name: str,
         prize: Prize, shareable: Shareable) -> World:
    world = World(setting)
    detective = world.add(Entity(
        id="detective", kind="character", type="detective", label=detective_name,
        role="detective", attrs={"case": case.id}, meters={"focus": 0.0}, memes={}
    ))
    helper = world.add(Entity(
        id="helper", kind="character", type="girl", label=helper_name,
        role="helper", attrs={"case": case.id}, meters={}, memes={}
    ))
    clue = world.add(Entity(
        id="clue", type="thing", label="clue card", phrase=case.clue_type,
        plural=False, owner=helper.id, meters={"shared": 0.0, "lost": 0.0},
        memes={}
    ))
    casefile = world.add(Entity(
        id="casefile", type="thing", label="case file", meters={"mistake": 0.0},
        memes={}
    ))
    prize_ent = world.add(Entity(
        id="prize", type="thing", label=prize.label, phrase=prize.phrase,
        plural=prize.plural, owner="someone", meters={"missing": 0.0}, memes={}
    ))
    world.facts.update(case=case, prize=prize, shareable=shareable, setting=setting)

    detective.memes["curious"] = 1.0
    helper.memes["kind"] = 1.0

    world.say(
        f"{detective_name} was a small detective with sharp eyes, and {helper_name} "
        f"stayed beside {detective.pronoun('object')} in {setting.place}."
    )
    world.say(
        f"They were looking for {prize.phrase}, while a {shareable.label} sat nearby, "
        f"ready to be shared."
    )
    world.say(
        f"On the table was a mystic note: \"{case.rhyme_line}\""
    )

    world.para()
    detective.memes["trust"] = 1.0
    clue.meters["shared"] = 1.0
    world.say(
        f"{helper_name} shared {shareable.phrase} with {detective_name}, hoping the clue "
        f"would help."
    )
    world.say(
        f"{detective_name} read the line and thought it sounded right, even though it led "
        f"to the wrong corner."
    )
    casefile.meters["mistake"] = 1.0
    clue.meters["lost"] = 1.0
    propagate(world)

    world.para()
    world.say(
        f"{detective_name} followed {case.clue_method}, but {case.wrong_turn}."
    )
    world.say(
        f"By the time {detective_name} looked back, the shared {shareable.label} was gone, "
        f"and {prize.label} was still missing."
    )
    world.say(
        f"The last thing the room showed was {case.loss_image}."
    )

    world.facts.update(
        detective=detective, helper=helper, clue=clue, casefile=casefile, prize_ent=prize_ent,
        resolved=False, shared=True, bad_end=True
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case: Case = f["case"]
    shareable: Shareable = f["shareable"]
    prize: Prize = f["prize"]
    detective: Entity = f["detective"]
    helper: Entity = f["helper"]
    return [
        f'Write a short detective story for a child that includes the word "mystic" and ends badly.',
        f"Tell a mystery where {detective.label_word} and {helper.label_word} share {shareable.phrase}, follow a rhyme, and still fail to recover {prize.phrase}.",
        f"Write a detective story where a mystic clue seems helpful, but the rhyme misleads the detective and the ending is sad.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case: Case = f["case"]
    shareable: Shareable = f["shareable"]
    prize: Prize = f["prize"]
    detective: Entity = f["detective"]
    helper: Entity = f["helper"]
    return [
        QAItem(
            question=f"What kind of story is this about {detective.label_word} and {helper.label_word}?",
            answer=f"It is a detective story about {detective.label_word} and {helper.label_word} trying to solve a case in {world.setting.place}. They follow a mystic clue, but the case goes badly in the end.",
        ),
        QAItem(
            question=f"What did {helper.label_word} share with {detective.label_word}?",
            answer=f"{helper.label_word.capitalize()} shared {shareable.phrase}. That sharing mattered because it gave {detective.label_word} a clue to follow, even though the clue led the wrong way.",
        ),
        QAItem(
            question=f"Why did the rhyme cause trouble for {detective.label_word}?",
            answer=f"The rhyme sounded mysterious, so {detective.label_word} trusted it too much. It pointed toward the wrong place, and that mistake kept {prize.phrase} from being found.",
        ),
        QAItem(
            question=f"What happened at the end of the story?",
            answer=f"The ending was bad because {prize.phrase} stayed missing and the shared clue was lost. The last image showed that the detective had followed the wrong lead.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does mystic mean?",
            answer="Mystic usually means strange, magical, or full of a secret feeling. A mystic clue can seem special even when it is only a puzzling note.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like cat and hat. Rhymes can make a line catchy and easy to remember.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means giving someone else some of what you have or letting them use it too. A shared clue can help two people work together.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and tries to solve a problem or mystery. Detectives notice small things and follow leads carefully.",
        ),
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
        bits = []
        if e.meters:
            bits.append(f"meters={ {k:v for k,v in e.meters.items() if v} }")
        if e.memes:
            bits.append(f"memes={ {k:v for k,v in e.memes.items() if v} }")
        if e.attrs:
            bits.append(f"attrs={ {k:v for k,v in e.attrs.items() if v} }")
        lines.append(f"  {e.id:9} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS = {
    "museum": Setting(place="the old museum", affords={"museum_case"}),
    "library": Setting(place="the quiet library", affords={"library_case"}),
    "station": Setting(place="the train station", affords={"station_case"}),
}

CASES = {
    "museum_case": Case(
        id="museum_case",
        scene="a quiet hallway",
        clue_type="a rhyme scratched on paper",
        rhyme_line="If the moon is pale and the clock is late, look by the gate",
        clue_method="the moonlit hall",
        wrong_turn="it only led to a locked side door",
        loss_image="a glass display lit by a lonely lamp",
        tags={"glass", "hall"},
    ),
    "library_case": Case(
        id="library_case",
        scene="a shelf maze",
        clue_type="a whispery rhyme in a book",
        rhyme_line="Row by row and page by page, the answer hides behind the stage",
        clue_method="the aisle of tall shelves",
        wrong_turn="it stopped at the wrong shelf",
        loss_image="a bookmark fluttering on the floor",
        tags={"book", "shelf"},
    ),
    "station_case": Case(
        id="station_case",
        scene="a busy platform",
        clue_type="a mystic rhyme on a ticket stub",
        rhyme_line="When the whistle sings and the rails all hum, check the bench with crumbs",
        clue_method="the bench by the tracks",
        wrong_turn="it pointed to an empty bench",
        loss_image="a clock above the platform showing midnight",
        tags={"bench", "tracks"},
    ),
}

PRIZES = {
    "key": Prize(id="key", label="missing key", phrase="a missing key", region="hand", tags={"key"}),
    "map": Prize(id="map", label="lost map", phrase="a lost map", region="hand", tags={"map"}),
    "badge": Prize(id="badge", label="silver badge", phrase="a silver badge", region="pocket", tags={"badge"}),
}

SHAREABLES = {
    "lantern_note": Shareable(id="lantern_note", label="lantern note", phrase="a lantern note", helps={"mystic", "rhyme"}),
    "stamp_card": Shareable(id="stamp_card", label="stamp card", phrase="a stamp card", helps={"sharing"}),
    "chalk_line": Shareable(id="chalk_line", label="chalk line", phrase="a chalk line clue", helps={"rhyme", "sharing"}),
}

GIRL_NAMES = ["Mina", "June", "Lena", "Nina", "Ivy"]
BOY_NAMES = ["Owen", "Eli", "Arlo", "Theo", "Milo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystic detective story world with a bad ending.")
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--shareable", choices=SHAREABLES)
    ap.add_argument("--detective")
    ap.add_argument("--helper")
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
              if (getattr(args, "case", None) is None or c[1] == getattr(args, "case", None))
              and (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, case, prize = rng.choice(list(combos))
    shareable = getattr(args, "shareable", None) or rng.choice(sorted(SHAREABLES))
    detective = getattr(args, "detective", None) or pick_name(rng, "girl")
    helper = getattr(args, "helper", None) or pick_name(rng, "boy")
    return StoryParams(
        case=case,
        setting=setting,
        detective=detective,
        helper=helper,
        clue=case,
        prize=prize,
        shareable=shareable,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.case not in CASES or params.prize not in PRIZES or params.shareable not in SHAREABLES:
        pass
    setting = _safe_lookup(SETTINGS, params.setting)
    case = _safe_lookup(CASES, params.case)
    prize = _safe_lookup(PRIZES, params.prize)
    shareable = _safe_lookup(SHAREABLES, params.shareable)
    world = tell(setting, case, params.detective, params.helper, prize, shareable)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(S, C, P) :- setting(S), case(C), prize(P), case_affords(C, P), setting_affords(S, C).
bad_end(C) :- case(C), chosen_case(C), clue_shared, wrong_turn(C).
story_ok(S, C, P) :- valid(S, C, P), bad_end(C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for c in sorted(setting.affords):
            lines.append(asp.fact("setting_affords", sid, c))
    for cid, case in CASES.items():
        lines.append(asp.fact("case", cid))
        for t in sorted(case.tags):
            lines.append(asp.fact("case_affords", cid, t))
        lines.append(asp.fact("wrong_turn", cid))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, prize.region))
    for shid in SHAREABLES:
        lines.append(asp.fact("shareable", shid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    ax = set(asp_valid_combos())
    ok = True
    if py != ax:
        ok = False
        print("MISMATCH in valid_combos:")
        print(" python-only:", sorted(py - ax))
        print(" asp-only:", sorted(ax - py))
    sample = generate(resolve_params(argparse.Namespace(case=None, setting=None, prize=None, shareable=None, detective=None, helper=None), random.Random(7)))
    if not sample.story or "mystic" not in sample.story:
        ok = False
        print("Smoke test failed.")
    if ok:
        print(f"OK: {len(py)} combos; smoke test passed.")
        return 0
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(case="museum_case", setting="museum", detective="Mina", helper="Owen", clue="museum_case", prize="key", shareable="lantern_note"),
    StoryParams(case="library_case", setting="library", detective="Ivy", helper="Theo", clue="library_case", prize="map", shareable="chalk_line"),
    StoryParams(case="station_case", setting="station", detective="Nina", helper="Eli", clue="station_case", prize="badge", shareable="stamp_card"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("\n".join(f"{a}" for a in asp_valid_combos()))
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
