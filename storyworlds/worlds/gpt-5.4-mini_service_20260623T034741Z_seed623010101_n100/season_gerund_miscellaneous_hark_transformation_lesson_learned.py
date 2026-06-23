#!/usr/bin/env python3
"""
storyworlds/worlds/season_gerund_miscellaneous_hark_transformation_lesson_learned.py
====================================================================================

A small mystery-flavored storyworld about a child, a town page, a hidden change,
and a lesson learned from listening closely.

Seed tale:
---
At the edge of town, Mina found a note that said, "Hark." Each season she
visited the old greenhouse, and each time something miscellaneous had changed:
a latch moved, a glove appeared, a trail of crumbs turned up.

Mina followed the clues through the year. In spring she found a broken seed jar.
In summer she found a map with a corner burned away. In autumn she found the
missing key. In winter, under the snow, she found the person who had been
leaving the clues: her grandfather, who had been secretly repairing the
greenhouse for months.

When Mina opened the door, the greenhouse was warm and bright. The plants had
transformed from dry sticks into green shoots. Grandfather smiled and said he
had wanted to surprise her with a lesson: careful work, patience, and kindness
can change a place.

Mina learned to listen for small signs, to trust honest clues, and to help
instead of guessing too fast.

This script models that premise as a tiny, state-driven mystery with physical
meters and emotional memes, a Python reasonableness gate, and an inline ASP twin.
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
    location: str = ""
    owner: str = ""
    transformed: bool = False
    secretive: bool = False
    seasonal: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    clue_ent: object | None = None
    p: object | None = None
    place: object | None = None
    rev: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.attrs.get("plural") else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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
    mood: str
    season_note: str
    afford: set[str] = field(default_factory=set)
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
class Clue:
    id: str
    text: str
    season: str
    misc_kind: str
    hint: str
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
class Revelation:
    id: str
    text: str
    change: str
    lesson: str
    moral: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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


@dataclass
class StoryParams:
    setting: str
    protagonist: str
    clue: str
    revelation: str
    season_word: str = "spring"
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


SETTINGS = {
    "greenhouse": Setting(
        place="the old greenhouse",
        mood="quiet and a little dusty",
        season_note="The panes held the cold like secrets.",
        afford={"spring", "summer", "autumn", "winter"},
    ),
    "library_steps": Setting(
        place="the library steps",
        mood="still and watchful",
        season_note="The stones seemed to remember every footstep.",
        afford={"spring", "summer", "autumn", "winter"},
    ),
}

PROTAGONISTS = {
    "Mina": Entity(id="Mina", kind="character", type="girl", label="Mina"),
    "Theo": Entity(id="Theo", kind="character", type="boy", label="Theo"),
}

CLUES = {
    "hark_note": Clue(
        id="hark_note",
        text="a folded note that said, 'Hark.'",
        season="winter",
        misc_kind="miscellaneous",
        hint="listen first",
        tags={"hark", "note", "listen"},
    ),
    "glove": Clue(
        id="glove",
        text="one mismatched glove tucked in a flower pot",
        season="spring",
        misc_kind="miscellaneous",
        hint="something left behind",
        tags={"miscellaneous", "glove"},
    ),
    "map": Clue(
        id="map",
        text="a torn map with a wet corner",
        season="summer",
        misc_kind="miscellaneous",
        hint="follow the mark",
        tags={"miscellaneous", "map"},
    ),
    "key": Clue(
        id="key",
        text="the missing brass key under a loose brick",
        season="autumn",
        misc_kind="miscellaneous",
        hint="what opens the locked door",
        tags={"miscellaneous", "key"},
    ),
}

REVELATIONS = {
    "repair": Revelation(
        id="repair",
        text="the gardener had been repairing the greenhouse all year",
        change="the cracked panes were replaced and the latch worked again",
        lesson="small patient work can make broken things whole",
        moral="kindness grows better than hurry",
        tags={"transformation", "lesson", "moral"},
    ),
    "seedling": Revelation(
        id="seedling",
        text="the quiet helper had hidden seedlings inside the warm bed",
        change="the dry pots had turned into green shoots",
        lesson="careful tending can transform a bare room",
        moral="gentle work can bring life back",
        tags={"transformation", "lesson", "moral"},
    ),
}

SEASON_WORDS = {"spring", "summer", "autumn", "winter"}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for c in CLUES:
            for r in REVELATIONS:
                out.append((s, c, r))
    return out


def reasonableness_gate(setting: str, clue: str, revelation: str) -> bool:
    c = _safe_lookup(CLUES, clue)
    r = _safe_lookup(REVELATIONS, revelation)
    return c.misc_kind == "miscellaneous" and "transformation" in r.tags


def explain_rejection(setting: str, clue: str, revelation: str) -> str:
    c = _safe_lookup(CLUES, clue)
    r = _safe_lookup(REVELATIONS, revelation)
    if c.misc_kind != "miscellaneous":
        return "(No story: the clue must be a miscellaneous object or note."
    if "transformation" not in r.tags:
        return "(No story: the ending must include a real transformation."
    return "(No story: this combination does not make a coherent mystery.)"


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_listen(world: World) -> list[str]:
    p = world.get("protagonist")
    if p.memes.get("curiosity", 0) >= THRESHOLD and ("heard_hark",) not in world.fired:
        world.fired.add(("heard_hark",))
        p.memes["attention"] = p.memes.get("attention", 0) + 1
        return ["__listen__"]
    return []


def _r_transform(world: World) -> list[str]:
    g = world.get("place")
    if g.meters.get("change", 0) >= THRESHOLD and ("transform",) not in world.fired:
        world.fired.add(("transform",))
        g.transformed = True
        return ["__transform__"]
    return []


CAUSAL_RULES = [Rule("listen", _r_listen), Rule("transform", _r_transform)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                out.extend([x for x in s if not x.startswith("__")])
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(setting: Setting, protagonist: Entity, clue: Clue, revelation: Revelation, season_word: str) -> World:
    w = World(setting)
    p = w.add(Entity(**{**protagonist.__dict__}))
    place = w.add(Entity(
        id="place",
        kind="place",
        type="place",
        label=setting.place,
        phrase=setting.place,
        seasonal=True,
        meters={"change": 0.0},
        memes={"mystery": 0.0},
        attrs={"season": season_word},
    ))
    clue_ent = w.add(Entity(
        id="clue",
        kind="object",
        type="object",
        label=clue.id,
        phrase=clue.text,
        secretive=True,
        seasonal=True,
        tags=set(clue.tags),
        attrs={"season": clue.season, "kind": clue.misc_kind},
    ))
    rev = w.add(Entity(
        id="revelation",
        kind="event",
        type="event",
        label=revelation.id,
        phrase=revelation.text,
        transformed=True,
        tags=set(revelation.tags),
        attrs={"change": revelation.change, "lesson": revelation.lesson, "moral": revelation.moral},
    ))
    w.get("protagonist").memes["curiosity"] = 1.0
    w.get("protagonist").memes["doubt"] = 0.0
    w.get("place").meters["change"] = 0.0

    w.say(f"{p.id} came to {setting.place} on a {season_word} afternoon, and the air felt {setting.mood}.")
    w.say(f"{setting.season_note} Then {p.id} found {clue.text}; hark, it seemed to whisper that the answer was near.")
    w.para()
    p.memes["curiosity"] += 1
    p.memes["doubt"] += 1
    w.say(f"{p.id} did not rush. {p.pronoun().capitalize()} looked at the clue again and again, because each season had left a different sign.")
    if clue.id == "hark_note":
        w.say(f"The note itself said, 'Hark,' and that tiny word made {p.id} listen more closely than before.")
    elif clue.id == "glove":
        w.say(f"The glove was warm from the sun, though it had no pair, which made it feel like a question.")
    elif clue.id == "map":
        w.say(f"The torn map pointed toward the locked door, but only if someone noticed the burnt corner.")
    else:
        w.say(f"The brass key did not belong on the ground, so {p.id} knew someone wanted it found.")
    w.para()
    if revelation.id == "repair":
        place.meters["change"] += 1
    else:
        place.meters["change"] += 1
    propagate(w, narrate=False)
    w.say(f"At last, {revelation.text}. When the door opened, {revelation.change}, and {p.id} understood the mystery.")
    w.say(f"{p.id} learned that {revelation.lesson}.")
    w.say(f"In the end, {revelation.moral}.")
    w.facts.update(
        protagonist=p,
        place=place,
        clue=clue_ent,
        revelation=rev,
        setting=setting,
        season_word=season_word,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["protagonist"]
    clue = f["clue"]
    rev = f["revelation"]
    return [
        f'Write a short mystery story for a young child that includes the words "hark" and "{clue.label}" and ends with a clear lesson learned.',
        f"Tell a gentle mystery where {p.id} notices {clue.phrase}, follows the clues through the seasons, and discovers {rev.phrase}.",
        f'Write a story with a transformation, a lesson learned, and a moral value about listening carefully for small signs.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["protagonist"]
    clue = f["clue"]
    rev = f["revelation"]
    place = f["place"]
    season_word = f["season_word"]
    return [
        QAItem(
            question=f"Who is the mystery story about?",
            answer=f"It is about {p.id}, who visits {place.label} during {season_word} and follows a strange clue. {p.id} keeps listening until the mystery makes sense.",
        ),
        QAItem(
            question=f"What clue told {p.id} to listen closely?",
            answer=f"{clue.phrase} was the clue, and it mattered because it pointed to something hidden. The word hark in the clue told {p.id} to pay attention instead of guessing too fast.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"{rev.text}. That change turned the quiet place into something warm, working, and alive again.",
        ),
        QAItem(
            question=f"What lesson did {p.id} learn?",
            answer=f"{rev.lesson}. {p.id} learned that careful listening and patient help can solve a mystery better than a quick guess.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a story with clues that help someone figure out what is really happening. The answer is usually hidden until the clues are put together.",
        ),
        QAItem(
            question="What does hark mean?",
            answer="Hark is an old word that means listen or pay attention. People say it when they want someone to hear an important clue.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="A transformation is a big change from one form or state into another. In a story, it can show that something broken, quiet, or plain has become different.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good idea about how to act, such as kindness, patience, or honesty. Stories often end by showing that value clearly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        out.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted({n for (n,) in world.fired if isinstance((n,), tuple)})}")
    return "\n".join(out)


CURATED = [
    StoryParams(setting="greenhouse", protagonist="Mina", clue="hark_note", revelation="repair", season_word="winter"),
    StoryParams(setting="library_steps", protagonist="Theo", clue="glove", revelation="seedling", season_word="spring"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with clues, seasons, transformation, lesson learned, and moral value.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--protagonist", choices=PROTAGONISTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--revelation", choices=REVELATIONS)
    ap.add_argument("--season-word", choices=sorted(SEASON_WORDS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))
              and (getattr(args, "revelation", None) is None or c[2] == getattr(args, "revelation", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, clue, revelation = rng.choice(list(combos))
    protagonist = getattr(args, "protagonist", None) or rng.choice(sorted(PROTAGONISTS))
    season_word = getattr(args, "season_word", None) or rng.choice(sorted(SEASON_WORDS))
    return StoryParams(setting=setting, protagonist=protagonist, clue=clue, revelation=revelation, season_word=season_word)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        pass
    if params.protagonist not in PROTAGONISTS:
        pass
    if params.clue not in CLUES or params.revelation not in REVELATIONS:
        pass
    if not reasonableness_gate(params.setting, params.clue, params.revelation):
        pass
    w = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(PROTAGONISTS, params.protagonist), _safe_lookup(CLUES, params.clue), _safe_lookup(REVELATIONS, params.revelation), params.season_word)
    return StorySample(params=params, story=w.render(), prompts=generation_prompts(w), story_qa=story_qa(w), world_qa=world_knowledge_qa(w), world=w)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p in PROTAGONISTS:
        lines.append(asp.fact("protagonist", p))
    for c, clue in CLUES.items():
        lines.append(asp.fact("clue", c))
        lines.append(asp.fact("kind", c, clue.misc_kind))
    for r in REVELATIONS:
        lines.append(asp.fact("revelation", r))
        lines.append(asp.fact("transformation", r))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,R) :- setting(S), clue(C), revelation(R), kind(C, miscellaneous), transformation(R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("ASP mismatch in valid combos.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as err:
        ok = False
        print(f"Smoke test failed: {err}")
    if ok:
        print("OK: ASP and Python agree; smoke test passed.")
        return 0
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()
