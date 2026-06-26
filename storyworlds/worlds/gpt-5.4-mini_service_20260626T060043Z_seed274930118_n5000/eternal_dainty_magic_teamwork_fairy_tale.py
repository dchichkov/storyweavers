#!/usr/bin/env python3
"""
A small fairy-tale storyworld about dainty magic and teamwork.

The premise: a tiny magical kingdom depends on a lantern that keeps a wish-garden
glowing. When the lantern dims, two friends must work together to mend it with
care, spells, and a shared plan.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------


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
class Character:
    id: str
    kind: str = "character"
    type: str = "fairy"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    carries: list[str] = field(default_factory=list)

    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Relic:
    id: str
    kind: str = "thing"
    type: str = "relic"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    eternal: bool = False
    dainty: bool = False
    fragile: bool = False
    lit_by: Optional[str] = None
    relic: object | None = None
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
    place: str = "the moonlit glade"
    magic: str = "soft lantern magic"
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
class World:
    setting: Setting
    entities: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    w: object | None = None
    world: object | None = None
    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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


SETTINGS = {
    "glade": Setting(place="the moonlit glade", magic="silver lantern magic", affords={"mend", "sing"}),
    "tower": Setting(place="the ivy tower", magic="starlight charm magic", affords={"mend", "sing"}),
    "grove": Setting(place="the little willow grove", magic="dew-drop magic", affords={"mend", "sing"}),
}

CHARACTERS = {
    "Aster": {"type": "fairy", "traits": ["dainty", "brave"]},
    "Milo": {"type": "sprite", "traits": ["gentle", "clever"]},
    "Rowan": {"type": "elf", "traits": ["patient", "kind"]},
    "Nia": {"type": "fairy", "traits": ["bright", "helpful"]},
}

RELICS = {
    "lantern": {
        "label": "lantern",
        "phrase": "an old wish-lantern",
        "eternal": True,
        "dainty": True,
        "fragile": False,
    },
    "glass_rose": {
        "label": "glass rose",
        "phrase": "a dainty glass rose",
        "eternal": False,
        "dainty": True,
        "fragile": True,
    },
    "moon_key": {
        "label": "moon key",
        "phrase": "a tiny moon-shaped key",
        "eternal": True,
        "dainty": True,
        "fragile": False,
    },
}

TRIOS = [("Aster", "Milo"), ("Nia", "Rowan"), ("Aster", "Rowan")]

TRAITS = ["dainty", "kind", "patient", "bright", "gentle", "brave", "clever"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    hero: str
    helper: str
    relic: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin support
# ---------------------------------------------------------------------------
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


ASP_RULES = r"""
setting(S) :- place(S).
character(C) :- fairy(C).
character(C) :- sprite(C).
character(C) :- elf(C).

relic(R) :- lantern(R).
relic(R) :- glass_rose(R).
relic(R) :- moon_key(R).

dainty_relic(R) :- relic(R), dainty(R).
eternal_relic(R) :- relic(R), eternal(R).

compatible(S,H,R) :- setting(S), character(H), dainty_relic(R).
story_ok(S,H,R) :- compatible(S,H,R), eternal_relic(R).
#show story_ok/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("place", sid))
    for cid, data in CHARACTERS.items():
        lines.append(asp.fact(data["type"], cid))
    for rid, data in RELICS.items():
        lines.append(asp.fact(data["label"].replace(" ", "_"), rid))
        if data["eternal"]:
            lines.append(asp.fact("eternal", rid))
        if data["dainty"]:
            lines.append(asp.fact("dainty", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_ok() -> bool:
    import asp
    model = asp.one_model(asp_program("#show story_ok/3."))
    atoms = set(asp.atoms(model, "story_ok"))
    py = set(valid_combos())
    return atoms == py


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for h, hdata in CHARACTERS.items():
            for r, rdata in RELICS.items():
                if rdata["dainty"] and rdata["eternal"]:
                    combos.append((s, h, r))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "setting", None) and getattr(args, "setting", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "hero", None) and getattr(args, "hero", None) not in CHARACTERS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "helper", None) and getattr(args, "helper", None) not in CHARACTERS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "relic", None) and getattr(args, "relic", None) not in RELICS:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    hero = getattr(args, "hero", None) or rng.choice(list(CHARACTERS))
    helper = getattr(args, "helper", None) or rng.choice([c for c in CHARACTERS if c != hero])
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    relic = getattr(args, "relic", None) or rng.choice(list(RELICS))

    if helper == hero:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if not (_safe_lookup(RELICS, relic)["dainty"] and _safe_lookup(RELICS, relic)["eternal"]):
        return _fallback_storyparams(args, rng, StoryParams, globals())

    return StoryParams(setting=setting, hero=hero, helper=helper, relic=relic)


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def _intro(world: World) -> None:
    h = world.get(world.facts["hero"])
    s = world.setting.place
    world.say(
        f"Long ago, in {s}, there lived a {h.traits[0]} little {h.type} named {h.id}."
    )
    world.say(
        f"{h.id} loved the quiet glitter of magic, especially anything dainty and kind."
    )


def _relic_setup(world: World) -> None:
    relic = world.get(world.facts["relic"])
    hero = world.get(world.facts["hero"])
    world.say(
        f"At the heart of the glade stood {relic.phrase}, which {hero.id} guarded carefully."
    )
    world.say(
        f"The old folk said it held an eternal glow, and that its light helped the flowers dream."
    )


def _problem(world: World) -> None:
    relic = world.get(world.facts["relic"])
    hero = world.get(world.facts["hero"])
    helper = world.get(world.facts["helper"])
    world.para()
    world.say(
        f"One dusk, the lantern's shine grew dim, and its tiny flame began to tremble."
    )
    world.say(
        f"{hero.id} gasped, for without the light, the wish-garden would fade into shadow."
    )
    world.say(
        f"{helper.id} hurried over and said, \"We can fix this if we work together.\""
    )
    world.facts["dim"] = True
    relic.meters["shine"] = 0.2
    hero.memes["worry"] = 1.0
    helper.memes["helpfulness"] = 1.0


def _teamwork(world: World) -> None:
    hero = world.get(world.facts["hero"])
    helper = world.get(world.facts["helper"])
    relic = world.get(world.facts["relic"])
    world.say(
        f"{hero.id} held the lantern low, and {helper.id} gathered moon petals with careful hands."
    )
    world.say(
        f"Together they whispered a dainty charm, then tied it with a ribbon of silver grass."
    )
    world.say(
        f"Because they shared the job, the magic did not rush or crack; it listened."
    )
    world.facts["worked_together"] = True
    world.facts["spell"] = "dainty shared charm"
    relic.meters["shine"] = 1.0
    relic.memes["hope"] = 1.0


def _resolution(world: World) -> None:
    relic = world.get(world.facts["relic"])
    hero = world.get(world.facts["hero"])
    helper = world.get(world.facts["helper"])
    world.para()
    world.say(
        f"Then the lantern bloomed bright again, soft as a star and steady as a promise."
    )
    world.say(
        f"The wish-garden woke at once, and every blossom leaned toward the warm, eternal light."
    )
    world.say(
        f"{hero.id} smiled at {helper.id}, because the best magic in the kingdom was teamwork."
    )
    world.facts["resolved"] = True
    relic.meters["shine"] = 2.0


def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero_cfg = _safe_lookup(CHARACTERS, params.hero)
    helper_cfg = _safe_lookup(CHARACTERS, params.helper)
    relic_cfg = _safe_lookup(RELICS, params.relic)

    hero = world.add(Character(
        id=params.hero,
        type=hero_cfg["type"],
        traits=list(hero_cfg["traits"]),
        role="hero",
        meters={"joy": 0.0, "worry": 0.0},
        memes={"hope": 0.0},
    ))
    helper = world.add(Character(
        id=params.helper,
        type=helper_cfg["type"],
        traits=list(helper_cfg["traits"]),
        role="helper",
        meters={"joy": 0.0},
        memes={"helpfulness": 0.0},
    ))
    relic = world.add(Relic(
        id=params.relic,
        label=relic_cfg["label"],
        phrase=relic_cfg["phrase"],
        eternal=relic_cfg["eternal"],
        dainty=relic_cfg["dainty"],
        fragile=relic_cfg["fragile"],
        owner=hero.id,
        caretaker=helper.id,
        meters={"shine": 1.0},
    ))

    world.facts.update(hero=hero.id, helper=helper.id, relic=relic.id, setting=params.setting)
    _intro(world)
    _relic_setup(world)
    _problem(world)
    _teamwork(world)
    _resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    h = world.get(world.facts["hero"])
    helper = world.get(world.facts["helper"])
    relic = world.get(world.facts["relic"])
    place = world.setting.place
    return [
        f'Write a fairy tale about {h.id} and {helper.id} in {place} with a dainty eternal {relic.label}.',
        f"Tell a child-friendly story where magic grows dim, two friends team up, and a lantern shines again.",
        f'Write a short story using the words "dainty" and "eternal" and ending with teamwork bringing back the light.',
    ]


def story_qa(world: World) -> list[QAItem]:
    h = world.get(world.facts["hero"])
    helper = world.get(world.facts["helper"])
    relic = world.get(world.facts["relic"])
    return [
        QAItem(
            question=f"Who was the fairy tale about?",
            answer=f"It was about {h.id}, who lived in {world.setting.place} and helped guard {relic.phrase}.",
        ),
        QAItem(
            question=f"What problem did {h.id} face?",
            answer=f"The lantern grew dim, so the wish-garden could lose its glow if nobody fixed it.",
        ),
        QAItem(
            question=f"How did {h.id} and {helper.id} fix the problem?",
            answer=f"They worked together, gathered moon petals, and spoke a dainty charm to brighten the lantern again.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"The lantern shone bright again, and the wish-garden glowed warmly under its eternal light.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does dainty mean?",
            answer="Dainty means small, delicate, and carefully made.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do a job together.",
        ),
        QAItem(
            question="What is magic in fairy tales?",
            answer="Magic is a special power that can make surprising things happen in a fairy tale.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in getattr(e, "meters", {}).items() if v}
        memes = {k: v for k, v in getattr(e, "memes", {}).items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if hasattr(e, "eternal") and e.eternal:
            bits.append("eternal=True")
        if hasattr(e, "dainty") and e.dainty:
            bits.append("dainty=True")
        lines.append(f"  {e.id:8} ({e.kind}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP / verification
# ---------------------------------------------------------------------------

def verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    if asp_ok():
        print(f"OK: ASP parity matches Python gate ({len(valid_combos())} combos).")
        return 0
    print("Mismatch between ASP and Python gate.")
    return 1


# ---------------------------------------------------------------------------
# Shared interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fairy tale storyworld about dainty magic and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=CHARACTERS)
    ap.add_argument("--helper", choices=CHARACTERS)
    ap.add_argument("--relic", choices=RELICS)
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


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print("== Q&A ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "helper", None) and getattr(args, "hero", None) and getattr(args, "helper", None) == getattr(args, "hero", None):
        return _fallback_storyparams(args, rng, StoryParams, globals())

    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    hero = getattr(args, "hero", None) or rng.choice(list(CHARACTERS))
    helper_choices = [c for c in CHARACTERS if c != hero]
    helper = getattr(args, "helper", None) or rng.choice(helper_choices)
    relic = getattr(args, "relic", None) or rng.choice(list(RELICS))
    if not (_safe_lookup(RELICS, relic)["dainty"] and _safe_lookup(RELICS, relic)["eternal"]):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(setting=setting, hero=hero, helper=helper, relic=relic)


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show story_ok/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(verify())
    if getattr(args, "asp", None):
        try:
            import asp
        except Exception as exc:
            raise SystemExit(f"ASP unavailable: {exc}")
        model = asp.one_model(asp_program("#show story_ok/3."))
        for atom in asp.atoms(model, "story_ok"):
            print(atom)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for setting in SETTINGS:
            for hero, helper in TRIOS:
                for relic in RELICS:
                    if _safe_lookup(RELICS, relic)["dainty"] and _safe_lookup(RELICS, relic)["eternal"]:
                        samples.append(generate(StoryParams(setting, hero, helper, relic, seed=base_seed)))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
                params.seed = base_seed + i
                sample = generate(params)
            except StoryError:
                continue
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            p = sample.params
            header = f"### variant {idx + 1}: {p.hero}, {p.helper}, {p.relic} in {p.setting}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
