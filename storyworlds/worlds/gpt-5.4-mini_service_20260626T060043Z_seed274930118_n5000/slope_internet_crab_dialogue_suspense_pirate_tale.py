#!/usr/bin/env python3
"""
A small story world for a pirate tale on a slope, with internet trouble and a crab.
The story is generated from a simulated world state, with dialogue and suspense.
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



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    crab: object | None = None
    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pirate", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def title(self) -> str:
        return self.label or self.id
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
    slope: str
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
class StoryParams:
    place: str
    trouble: str
    prize: str
    hero_name: str
    helper_name: str
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


@dataclass
class Trouble:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
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
        self.zone: set[str] = set()
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.zone = set(self.zone)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "harbor_slope": Setting(place="the harbor slope", slope="steep", affords={"signal", "search"}),
    "cliff_path": Setting(place="the cliff path", slope="slippery", affords={"signal", "search"}),
    "dock_slope": Setting(place="the dock slope", slope="crooked", affords={"signal", "search"}),
}

TROUBLES = {
    "signal": Trouble(
        id="signal",
        verb="send the internet signal",
        gerund="sending the internet signal",
        rush="dash down the slope to the signal box",
        mess="muddy",
        soil="muddy and weak",
        zone={"feet", "legs"},
        keyword="internet",
    ),
    "rope": Trouble(
        id="rope",
        verb="pull the rope",
        gerund="pulling the rope",
        rush="run to the rope post",
        mess="frayed",
        soil="frayed and loose",
        zone={"hands"},
        keyword="rope",
    ),
    "barrel": Trouble(
        id="barrel",
        verb="roll the barrel",
        gerund="rolling the barrel",
        rush="push hard at the barrel",
        mess="scratched",
        soil="scratched and dented",
        zone={"arms", "legs"},
        keyword="barrel",
    ),
}

PRIZES = {
    "map": Prize(id="map", label="map", phrase="a shiny treasure map", region="hands"),
    "message": Prize(id="message", label="message bottle", phrase="a little message in a bottle", region="hands"),
    "lantern": Prize(id="lantern", label="lantern", phrase="a bright brass lantern", region="hands"),
}

GEAR = {
    "boots": Gear(
        id="boots",
        label="sea boots",
        covers={"feet"},
        guards={"muddy"},
        prep="put on sea boots first",
        tail="went back for the sea boots",
    ),
    "gloves": Gear(
        id="gloves",
        label="net gloves",
        covers={"hands"},
        guards={"frayed", "scratched"},
        prep="put on net gloves first",
        tail="went back for the net gloves",
    ),
    "slicker": Gear(
        id="slicker",
        label="a rain slicker",
        covers={"torso", "arms"},
        guards={"muddy", "scratched"},
        prep="put on a rain slicker first",
        tail="went back for the rain slicker",
    ),
}

HERO_NAMES = ["Cap'n Rose", "Milo", "Nora", "Jack", "Pippa", "Finn"]
HELPER_NAMES = ["Bram", "Tess", "Wren", "Hale", "Ivy", "Sailor"]

CURATED = [
    StoryParams(place="harbor_slope", trouble="signal", prize="map", hero_name="Cap'n Rose", helper_name="Bram"),
    StoryParams(place="cliff_path", trouble="rope", prize="message", hero_name="Milo", helper_name="Tess"),
    StoryParams(place="dock_slope", trouble="barrel", prize="lantern", hero_name="Nora", helper_name="Wren"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with slope, internet, crab, dialogue, and suspense.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    trouble = getattr(args, "trouble", None) or rng.choice(list(TROUBLES))
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    if trouble == "rope" and prize == "map":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_name = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, trouble=trouble, prize=prize, hero_name=hero_name, helper_name=helper_name)


def prize_risk(trouble: Trouble, prize: Prize) -> bool:
    return prize.region in trouble.zone


def select_gear(trouble: Trouble, prize: Prize) -> Optional[Gear]:
    for gear in GEAR.values():
        if trouble.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("mess_of", tid, t.mess))
        for z in sorted(t.zone):
            lines.append(asp.fact("splashes", tid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", gid, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", gid, m))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(T,P) :- splashes(T,R), worn_on(P,R).
protects(G,T,P) :- prize_at_risk(T,P), mess_of(T,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(T,P) :- protects(_,T,P).
valid(S,T,P) :- affords(S,T), prize_at_risk(T,P), has_fix(T,P).
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = sorted({(p.place, p.trouble, p.prize) for p in CURATED if prize_risk(_safe_lookup(TROUBLES, p.trouble), _safe_lookup(PRIZES, p.prize)) and select_gear(_safe_lookup(TROUBLES, p.trouble), _safe_lookup(PRIZES, p.prize))})
    cl = asp_valid_combos()
    if set(py) == set(cl):
        print(f"OK: clingo gate matches Python gate ({len(py)} combos in curated set).")
        return 0
    print("MISMATCH:")
    print("python:", py)
    print("clingo:", cl)
    return 1


def _do_trouble(world: World, hero: Entity, trouble: Trouble) -> None:
    world.zone = set(trouble.zone)
    hero.meters[trouble.mess] = hero.meters.get(trouble.mess, 0.0) + 1
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    trouble = _safe_lookup(TROUBLES, params.trouble)
    prize_cfg = _safe_lookup(PRIZES, params.prize)
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type="captain", label=params.hero_name, traits=["brave"]))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="pirate", label=params.helper_name, traits=["quick"]))
    crab = world.add(Entity(id="crab", kind="character", type="crab", label="a crab"))
    prize = world.add(Entity(id="prize", type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=helper.id))
    gear_def = select_gear(trouble, prize_cfg)
    world.facts.update(hero=hero, helper=helper, crab=crab, prize=prize, trouble=trouble, setting=setting, gear=gear_def)

    world.say(f"On {setting.place}, {hero.label} found {prize.phrase} and tucked it close.")
    world.say(f'"By the sea," {hero.pronoun("subject")} said, "I’ll keep this treasure safe."')
    world.para()
    world.say(f"Then a crab skittered out by the slope and clicked, " + f'"{trouble.keyword}! The internet line is in a twist!"')
    world.say(f"{hero.label} peered down the {setting.slope} slope. " + f'"If the signal fails, the harbor lanterns will go dark," {helper.label} whispered.')
    world.say(f"That made the air feel tight and still.")

    if prize_risk(trouble, prize_cfg):
        world.para()
        world.say(f"{hero.label} wanted to {trouble.verb}, but first the wind hissed and the crab waved one claw toward the path.")
        world.say(f'"Careful," {helper.label} said. "The {prize.label} could be ruined if you hurry the wrong way."')
        _do_trouble(world, hero, trouble)
        world.say(f"The {trouble.mess} trouble crept on, and the little crab clicked faster, as if it knew a secret.")
        if gear_def:
            world.say(f'"We can still do it," {helper.label} said. "Let’s {gear_def.prep}."')
            world.say(f"{hero.label} nodded, and the old fear eased a bit.")
            world.para()
            world.say(f"They {gear_def.tail}, and the crab led them beside the ropes instead of the edge.")
            world.say(f"At last {hero.label} could {trouble.gerund}, while {prize.label} stayed safe and bright.")
            world.say(f'The crab gave a proud little snap, as if to say, "There now."')
            hero.memes["suspense"] = 0.0
            hero.memes["joy"] = 1.0
        else:
            world.say("But no sensible gear fit the trouble, so the crew chose a slower, safer way.")
    else:
        world.para()
        world.say(f"{hero.label} learned the slope was harmless for the {prize.label}, so the warning eased like foam.")
        world.say(f"They still watched the crab, because a pirate tale likes a little suspense by the sea.")
        world.say(f"In the end, the internet signal held, the lantern stayed bright, and the crew laughed with salt in their hair.")

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate tale with dialogue and suspense that includes the word "{f["trouble"].keyword}".',
        f"Tell a gentle story about {f['hero'].label} on {f['setting'].place} where a crab causes trouble with the internet line.",
        f"Write a child-friendly pirate adventure where the crew must solve a problem on a slope without ruining the treasure.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, trouble = f["hero"], f["helper"], f["prize"], f["trouble"]
    qa = [
        QAItem(
            question=f"Who was the story mainly about?",
            answer=f"The story was mainly about {hero.label}, who was trying to keep {prize.phrase} safe.",
        ),
        QAItem(
            question=f"What did the crab warn them about?",
            answer=f"The crab warned them that the {trouble.keyword} internet line was in trouble on the slope.",
        ),
        QAItem(
            question=f"Why did the crew feel suspense?",
            answer=f"They felt suspense because the slope was risky and the crew worried the {prize.label} might get ruined before they fixed the problem.",
        ),
    ]
    if f.get("gear"):
        gear = _safe_fact(world, f, "gear")
        qa.append(QAItem(
            question=f"How did {gear.label} help?",
            answer=f"{gear.label} helped because it fit the dangerous part of the problem and let the crew keep going safely.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a crab like?",
            answer="A crab is a sea creature with claws and a hard shell. It can scuttle sideways very quickly.",
        ),
        QAItem(
            question="What is the internet?",
            answer="The internet is a way for messages and pictures to travel between faraway places through wires and signals.",
        ),
        QAItem(
            question="What is a slope?",
            answer="A slope is a place that goes up or down at an angle, so it can be easy to slip or tumble there.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(getattr(args, "n", None) * 50, 50)):
            if len(samples) >= getattr(args, "n", None):
                break
            params = resolve_params(args, random.Random(base_seed + i))
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
            header = f"### {p.hero_name} at {p.place} ({p.trouble} / {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
