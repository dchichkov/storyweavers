#!/usr/bin/env python3
"""
storyworlds/worlds/lavender_plural_bravery_rhyming_story.py
===========================================================

A small story world in a rhyming-story style: a plural hero, a gentle setting,
and a brave turn that changes the world state.

The seed words are honored here:
- lavender
- plural
- bravery

The world model tracks both physical meters and emotional memes, and the story
is generated from simulated state rather than a frozen text shell.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
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
            keys = [upper, upper + "S", upper + "ES"]
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    a: object | None = None
    aid: object | None = None
    b: object | None = None
    duo: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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
    indoor: bool = False
    quiet: bool = True
    affords: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    hues: set[str] = field(default_factory=lambda: {"lavender"})
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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
class Challenge:
    id: str
    action: str
    wanting: str
    rush: str
    risk: str
    fix: str
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
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
class Helper:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str]
    guards: set[str]
    plural: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def meme(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def bump_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def bump_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def covered(hero: Entity, region: str, world: World) -> bool:
    return any(
        e.worn_by == hero.id and e.label in {"rain cape", "night hood", "glow cloak"}
        and region in {"head", "torso"}
        for e in world.entities.values()
    )


def spread_darkness(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.kind != "character":
            continue
        if meter(ent, "fear") < THRESHOLD:
            continue
        if ("shiver", ent.id) in world.fired:
            continue
        world.fired.add(("shiver", ent.id))
        bump_meter(ent, "shiver", 1.0)
        out.append(f"A hush grew hushed, and {ent.id} did not feel so sure.")
    return out


def resolve_turn(world: World, hero: Entity, prize: Entity) -> bool:
    if meter(hero, "fear") < THRESHOLD or meter(hero, "bravery") < THRESHOLD:
        return False
    if prize.worn_by == hero.id:
        return True
    return False


SETTINGS = {
    "lavender_garden": Setting(place="the lavender garden", indoor=False, quiet=True, affords={"cross_bridge", "find_path"}),
    "moon_gate": Setting(place="the moon gate", indoor=False, quiet=True, affords={"cross_bridge"}),
    "storybook_room": Setting(place="the storybook room", indoor=True, quiet=True, affords={"find_path"}),
}

CHALLENGES = {
    "bridge": Challenge(
        id="bridge",
        action="cross the little bridge",
        wanting="cross the little bridge",
        rush="tiptoe to the bridge",
        risk="the dark water below might feel too wide",
        fix="carry a glowing lantern and walk together",
        tags={"brave", "bridge", "night"},
    ),
    "path": Challenge(
        id="path",
        action="find the path home",
        wanting="find the path home",
        rush="hurry toward the dark path",
        risk="the shadows might hide the way",
        fix="hold hands and follow the lavender lights",
        tags={"brave", "path", "night"},
    ),
}

PRIZES = {
    "lantern": Prize(
        label="lantern",
        phrase="a little lavender lantern",
        type="lantern",
        region="hand",
        plural=False,
        hues={"lavender"},
    ),
    "ribbon": Prize(
        label="ribbon",
        phrase="a lavender ribbon bundle",
        type="ribbon",
        region="hand",
        plural=True,
        hues={"lavender"},
    ),
}

HELPERS = [
    Helper(
        id="glow_cape",
        label="glow cape",
        prep="put on a glow cape first",
        tail="walked on with the glow cape shining",
        covers={"torso"},
        guards={"dark"},
        plural=False,
    ),
    Helper(
        id="night_hood",
        label="night hood",
        prep="pull on a night hood first",
        tail="moved on with the hood snug and neat",
        covers={"head"},
        guards={"dark"},
        plural=False,
    ),
]


GROUNDS = {
    "brave": [
        ("What is bravery?", "Bravery means feeling a little scared but still choosing to do the helpful thing."),
        ("What does brave mean?", "Brave means you keep going even when your knees feel shaky."),
    ],
    "lavender": [
        ("What is lavender?", "Lavender is a soft purple flower with a fresh smell and a gentle color."),
    ],
    "plural": [
        ("What does plural mean?", "Plural means more than one, like two friends or three birds together."),
    ],
}


@dataclass
class StoryParams:
    setting: str
    challenge: str
    prize: str
    name_a: str
    name_b: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("tagged", cid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        if p.plural:
            lines.append(asp.fact("plural_prize", pid))
        for h in sorted(p.hues):
            lines.append(asp.fact("hue", pid, h))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
        for c in sorted(h.covers):
            lines.append(asp.fact("covers", h.id, c))
        for g in sorted(h.guards):
            lines.append(asp.fact("guards", h.id, g))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(C, P) :- challenge(C), prize(P), worn_on(P, hand), tagged(C, brave).
has_fix(C, P) :- at_risk(C, P), helper(H), guards(H, dark), covers(H, torso).
valid_story(S, C, P) :- setting(S), affords(S, C), at_risk(C, P), has_fix(C, P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for cid in setting.affords:
            for pid, prize in PRIZES.items():
                if prize.region == "hand":
                    out.append((sid, cid, pid))
    return out


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    challenge = _safe_lookup(CHALLENGES, params.challenge)
    prize_cfg = _safe_lookup(PRIZES, params.prize)
    world = World(setting)

    duo = world.add(Entity(
        id="TheTwins",
        kind="character",
        type="child",
        plural=True,
        label="the twins",
    ))
    a = world.add(Entity(id=params.name_a, kind="character", type="girl", plural=False))
    b = world.add(Entity(id=params.name_b, kind="character", type="girl", plural=False))
    prize = world.add(Entity(
        id="Prize",
        kind="thing",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        plural=prize_cfg.plural,
    ))

    a.memes["bravery"] = 1.0
    b.memes["bravery"] = 1.0
    duo.memes["bravery"] = 2.0

    world.say(
        f"{a.id} and {b.id} were twins with a lavender gleam, "
        f"two little hearts in a bright small team."
    )
    world.say(
        f"They loved the soft color lavender so dear, "
        f"and carried {prize.phrase} with cheer."
    )
    world.say(
        f"One evening at {setting.place}, they wished to {challenge.wanting}, "
        f"though {challenge.risk} and the dark felt blinding."
    )

    world.para()
    bump_meter(duo, "fear", 1.0)
    bump_meter(a, "fear", 1.0)
    bump_meter(b, "fear", 1.0)
    world.say(
        f"{a.id} looked down and swallowed a sigh, "
        f"for the dark little bridge seemed too high."
    )
    world.say(
        f"{b.id} held the ribbon and tried not to hide, "
        f"but bravery shivered and stayed inside."
    )

    if setting.affords:
        bump_meter(duo, "bravery", 1.0)
        bump_meter(a, "bravery", 1.0)
        bump_meter(b, "bravery", 1.0)
        world.say(
            f"Then {a.id} said, 'We can be brave if we go side by side,' "
            f"and {b.id} said, 'Together we glide.'"
        )

    helper = _safe_lookup(HELPERS, 0)
    aid = world.add(Entity(
        id=helper.id,
        kind="thing",
        type="helper",
        label=helper.label,
        plural=helper.plural,
        owner=a.id,
        caretaker=b.id,
    ))
    aid.worn_by = a.id

    world.say(
        f"So they {helper.prep}, and the lantern glowed bright, "
        f"like a tiny moonbeam in the night."
    )

    prize.worn_by = a.id
    bump_meter(prize, "safe", 1.0)
    bump_meme(duo, "joy", 1.0)

    world.para()
    bump_meter(duo, "courage", 1.0)
    spread_darkness(world)
    world.say(
        f"Hand in hand, they crossed with a hop and a stride; "
        f"{helper.tail}, with lavender light as their guide."
    )
    world.say(
        f"They reached the far side and smiled in the glow, "
        f"for the road felt kinder and easier to know."
    )

    world.facts.update(
        a=a,
        b=b,
        duo=duo,
        prize=prize,
        setting=setting,
        challenge=challenge,
        helper=helper,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, challenge, prize = f["a"], f["b"], f["challenge"], f["prize"]
    return [
        f'Write a short rhyming story for young children about {a.id} and {b.id}, '
        f'a plural pair, who need bravery to {challenge.wanting}.',
        f'Create a gentle rhyming tale where a lavender prize helps {a.id} and {b.id} '
        f'be brave together without losing {prize.label}.',
        f'Write a simple story with the word "lavender" and a plural hero who learns '
        f'that bravery can make a dark path feel safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, prize, challenge = f["a"], f["b"], f["prize"], f["challenge"]
    return [
        QAItem(
            question=f"Who were the two brave friends in the story?",
            answer=f"The story was about {a.id} and {b.id}, a plural pair of twins who stayed together.",
        ),
        QAItem(
            question=f"What did they want to do at {world.setting.place}?",
            answer=f"They wanted to {challenge.wanting}. The dark felt big at first, but they did not give up.",
        ),
        QAItem(
            question=f"What lavender thing did they carry with them?",
            answer=f"They carried {prize.phrase}, which glowed softly and helped guide their way.",
        ),
        QAItem(
            question=f"How did the twins feel in the end?",
            answer=f"They felt brave and happy in the end, because they crossed together and made it safely across.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ("lavender", "plural", "brave"):
        for q, a in _safe_lookup(GROUNDS, key):
            out.append(QAItem(question=q, answer=a))
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.plural:
            bits.append("plural=True")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world about lavender bravery and a plural hero.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
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
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "challenge", None):
        combos = [c for c in combos if c[1] == getattr(args, "challenge", None)]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[2] == getattr(args, "prize", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, challenge, prize = rng.choice(list(combos))
    names = ["Luna", "Nina", "Mira", "Tessa", "Ruby", "Iris"]
    a = getattr(args, "name_a", None) or rng.choice(names)
    b = getattr(args, "name_b", None) or rng.choice([n for n in names if n != a])
    return StoryParams(setting=setting, challenge=challenge, prize=prize, name_a=a, name_b=b)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


CURATED = [
    StoryParams(setting="lavender_garden", challenge="bridge", prize="lantern", name_a="Luna", name_b="Mira"),
    StoryParams(setting="moon_gate", challenge="bridge", prize="ribbon", name_a="Nina", name_b="Ruby"),
    StoryParams(setting="storybook_room", challenge="path", prize="lantern", name_a="Iris", name_b="Tessa"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name_a} and {p.name_b}: {p.challenge} at {p.setting} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
