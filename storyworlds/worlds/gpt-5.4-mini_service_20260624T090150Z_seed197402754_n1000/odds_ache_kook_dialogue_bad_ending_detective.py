#!/usr/bin/env python3
"""
storyworlds/worlds/odds_ache_kook_dialogue_bad_ending_detective.py
===================================================================

A small detective-story world about low odds, a lingering ache, and a kooky
suspect. The stories are built from simulated state: the detective follows
clues, talks to people, feels the strain of the case, and sometimes loses the
case badly.

This world intentionally supports a bad ending: the detective may be outmatched,
the suspect may slip away, and the final image proves what changed in the world.
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
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue_ent: object | None = None
    detective: object | None = None
    partner: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"woman", "girl", "mother", "aunt"}
        male = {"man", "boy", "father", "uncle", "detective"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
    mood: str
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
class Case:
    id: str
    verb: str
    look: str
    risk: str
    strain: str
    keyword: str
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
class SuspectStyle:
    id: str
    label: str
    kind: str
    line: str
    tell: str
    tags: set[str] = field(default_factory=set)
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
class Clue:
    id: str
    label: str
    phrase: str
    damage: str
    region: str
    tags: set[str] = field(default_factory=set)
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
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        import copy as _copy
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _risk_meter(value: float) -> bool:
    return value >= THRESHOLD


def clue_on_scene(case: Case, clue: Clue) -> bool:
    return clue.region in case.tags or clue.id in case.tags or clue.tags & case.tags != set()


def choose_suspect(case: Case, clue: Clue) -> Optional[SuspectStyle]:
    for suspect in SUSPECTS:
        if case.keyword in suspect.tags and clue.tags & suspect.tags:
            return suspect
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for case_id in setting.affords:
            case = _safe_lookup(CASES, case_id)
            for clue_id, clue in CLUES.items():
                for sus in SUSPECTS:
                    if case_on_path(case, clue, sus):
                        combos.append((place, case_id, clue_id))
    return combos


def case_on_path(case: Case, clue: Clue, suspect: SuspectStyle) -> bool:
    return clue_on_scene(case, clue) and case.keyword in suspect.tags and clue.tags & suspect.tags != set()


def buildup(world: World, detective: Entity, case: Case, clue: Clue) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f"{detective.id} was a detective who liked odd cases, "
        f"even when the odds of a clean solve looked low."
    )
    world.say(
        f"This time the case was about {case.look}, and the first clue was {clue.phrase}."
    )


def arrive(world: World, detective: Entity, partner: Entity, case: Case) -> None:
    world.say(
        f"One night, {detective.id} and {partner.label} went to {world.setting.place}. "
        f"The place felt {world.setting.mood}, like a room keeping a secret."
    )


def dialogue_warning(world: World, partner: Entity, detective: Entity, case: Case, clue: Clue) -> None:
    detective.memes["doubt"] += 1
    world.say(
        f'"The odds are bad," {partner.label} said. '
        f'"If we push too hard, we might miss the small thing that matters."'
    )
    world.say(
        f'"I know," {detective.id} said, touching the {clue.label}. '
        f'"But this clue aches like it wants to be read."'
    )


def stakeout(world: World, detective: Entity, case: Case) -> None:
    detective.meters["tired"] = detective.meters.get("tired", 0.0) + 1
    detective.memes["ache"] = detective.memes.get("ache", 0.0) + 1
    world.say(
        f"They waited in silence until the detective's shoulders began to ache."
    )
    world.say(
        f"{detective.id} muttered, \"If the kook shows up, I want to be ready.\""
    )


def observe_kook(world: World, detective: Entity, suspect: SuspectStyle) -> None:
    detective.memes["alert"] = detective.memes.get("alert", 0.0) + 1
    world.say(
        f"Then a kooky figure slipped into view. "
        f"{suspect.line} {suspect.tell}"
    )
    world.say(
        f'"That is our kook," {detective.id} whispered.'
    )


def bad_turn(world: World, detective: Entity, suspect: SuspectStyle, clue: Clue) -> None:
    detective.meters["scratched"] = detective.meters.get("scratched", 0.0) + 1
    detective.memes["panic"] = detective.memes.get("panic", 0.0) + 1
    world.say(
        f"The detective rushed forward, but the kook had already noticed the move."
    )
    world.say(
        f'"Too slow," the kook called, and the {clue.label} was knocked from {detective.id}\'s hand.'
    )


def escape(world: World, detective: Entity, suspect: SuspectStyle, clue: Clue) -> None:
    detective.memes["defeat"] = detective.memes.get("defeat", 0.0) + 1
    world.say(
        f"The kook ran off with the last useful scrap of the case. "
        f"The {clue.label} was left bent and useless on the ground."
    )
    world.say(
        f"{detective.id} stood still, staring at the empty dark where the suspect had been."
    )


def closing_bad_ending(world: World, detective: Entity, partner: Entity, clue: Clue) -> None:
    world.say(
        f'"We lost the trail," {partner.label} said softly.'
    )
    world.say(
        f'{detective.id} nodded. The ache in {detective.id}\'s back was real, and so was the bad ending: '
        f"the case stayed open, and the city kept its secret for one more night."
    )


def tell(setting: Setting, case: Case, clue: Clue, suspect: SuspectStyle,
         detective_name: str = "Mara", partner_name: str = "Jo") -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type="detective", label=detective_name))
    partner = world.add(Entity(id=partner_name, kind="character", type="woman", label=partner_name))
    clue_ent = world.add(Entity(id=clue.id, type="thing", label=clue.label, phrase=clue.phrase))
    world.facts.update(
        detective=detective,
        partner=partner,
        clue=clue_ent,
        clue_cfg=clue,
        case=case,
        setting=setting,
        suspect=suspect,
    )

    buildup(world, detective, case, clue)
    world.para()
    arrive(world, detective, partner, case)
    dialogue_warning(world, partner, detective, case, clue)
    stakeout(world, detective, case)
    observe_kook(world, detective, suspect)
    bad_turn(world, detective, suspect, clue)
    world.para()
    escape(world, detective, suspect, clue)
    closing_bad_ending(world, detective, partner, clue)
    world.facts["resolved"] = False
    world.facts["bad_ending"] = True
    return world


SETTINGS = {
    "dock": Setting(place="the foggy dock", mood="cold and damp", affords={"missing_ledger", "stolen_key"}),
    "station": Setting(place="the quiet station", mood="tight and echoing", affords={"missing_ledger", "blackmail_note"}),
    "museum": Setting(place="the museum hall", mood="bright but uneasy", affords={"stolen_key", "blackmail_note"}),
}

CASES = {
    "missing_ledger": Case(
        id="missing_ledger",
        verb="find the missing ledger",
        look="a missing ledger from the front office",
        risk="the clue could be buried in old records",
        strain="the waiting makes the detective ache",
        keyword="odds",
        tags={"paper", "records", "ink", "odds"},
    ),
    "stolen_key": Case(
        id="stolen_key",
        verb="recover the stolen key",
        look="a stolen key that opens a locked side door",
        risk="the clue could vanish into the dark",
        strain="the long watch makes the detective ache",
        keyword="ache",
        tags={"metal", "door", "lock", "ache"},
    ),
    "blackmail_note": Case(
        id="blackmail_note",
        verb="catch who wrote the blackmail note",
        look="a blackmail note with a strange crease",
        risk="the clue could be folded away too fast",
        strain="the late hour makes the detective ache",
        keyword="kook",
        tags={"paper", "note", "kook", "ink"},
    ),
}

CLUES = {
    "smudged_ink": Clue(
        id="smudged_ink",
        label="smudged note",
        phrase="a smudged note with one wet corner",
        damage="smudged",
        region="paper",
        tags={"paper", "ink", "note", "odds"},
    ),
    "bent_key": Clue(
        id="bent_key",
        label="bent key",
        phrase="a bent brass key with a tiny crack",
        damage="bent",
        region="metal",
        tags={"metal", "lock", "key", "ache"},
    ),
    "odd_smile": Clue(
        id="odd_smile",
        label="odd flyer",
        phrase="an odd flyer with a laughing face",
        damage="creased",
        region="paper",
        tags={"paper", "flyer", "kook", "note"},
    ),
}

SUSPECTS = [
    SuspectStyle(
        id="kook1",
        label="a kooky man in a striped coat",
        kind="man",
        line='"You cannot solve a puzzle by staring at it,"',
        tell="He carried a teacup in one hand and a red balloon in the other.",
        tags={"kook", "paper", "ink", "note"},
    ),
    SuspectStyle(
        id="kook2",
        label="a kooky woman with a bright hat",
        kind="woman",
        line='"The moon likes a good joke,"',
        tell="She walked backward as if the floor were telling her a story.",
        tags={"kook", "metal", "lock", "key"},
    ),
]

GIRL_NAMES = ["Mara", "Nina", "Ivy", "June", "Tess"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Owen", "Theo"]
PARTNER_NAMES = ["Jo", "Rae", "Lee", "Sam"]


@dataclass
class StoryParams:
    place: str
    case: str
    clue: str
    suspect: str
    detective_name: str
    partner_name: str
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


def reasonableness_gate(case: Case, clue: Clue, suspect: SuspectStyle) -> bool:
    return case_on_path(case, clue, suspect)


def explain_rejection(place: str, case: Case, clue: Clue, suspect: SuspectStyle) -> str:
    return (
        f"(No story: {clue.label} and {suspect.label} do not line up with {case.look} at {place}. "
        f"The case needs a clue that fits the scene and a kook who can actually affect it.)"
    )


ASP_RULES = r"""
case_valid(Place, Case, Clue, Suspect) :- place(Place), case(Case), clue(Clue), suspect(Suspect),
                                         case_keyword(Case, K), suspect_tag(Suspect, K),
                                         clue_tag(Clue, K), clue_scene(Clue, Case).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for cid, case in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("case_keyword", cid, case.keyword))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_scene", clue_id, clue.region))
        for tag in sorted(clue.tags):
            lines.append(asp.fact("clue_tag", clue_id, tag))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s.id))
        for tag in sorted(s.tags):
            lines.append(asp.fact("suspect_tag", s.id, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show case_valid/4."))
    return sorted(set(asp.atoms(model, "case_valid")))


def asp_verify() -> int:
    py = set((p, c, q, s) for p in SETTINGS for c, q, s in valid_story_triples())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_story triples ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def valid_story_triples() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for case_id in setting.affords:
            case = _safe_lookup(CASES, case_id)
            for clue_id, clue in CLUES.items():
                for suspect in SUSPECTS:
                    if reasonableness_gate(case, clue, suspect):
                        out.append((place, case_id, clue_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with dialogue and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--case", choices=CASES.keys())
    ap.add_argument("--clue", choices=CLUES.keys())
    ap.add_argument("--suspect", choices=[s.id for s in SUSPECTS])
    ap.add_argument("--detective-name")
    ap.add_argument("--partner-name")
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
    places = [getattr(args, "place", None)] if getattr(args, "place", None) else list(SETTINGS.keys())
    cases = [getattr(args, "case", None)] if getattr(args, "case", None) else None
    clues = [getattr(args, "clue", None)] if getattr(args, "clue", None) else list(CLUES.keys())
    suspects = [getattr(args, "suspect", None)] if getattr(args, "suspect", None) else [s.id for s in SUSPECTS]
    combos = []
    for place in places:
        for case_id in (cases or _safe_lookup(SETTINGS, place).affords):
            if case_id not in _safe_lookup(SETTINGS, place).affords:
                continue
            case = _safe_lookup(CASES, case_id)
            for clue_id in clues:
                clue = _safe_lookup(CLUES, clue_id)
                for suspect_id in suspects:
                    suspect = next(s for s in SUSPECTS if s.id == suspect_id)
                    if reasonableness_gate(case, clue, suspect):
                        combos.append((place, case_id, clue_id, suspect_id))
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, case_id, clue_id, suspect_id = rng.choice(list(combos))
    detective_name = getattr(args, "detective_name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    partner_name = getattr(args, "partner_name", None) or rng.choice(PARTNER_NAMES)
    return StoryParams(place=place, case=case_id, clue=clue_id, suspect=suspect_id,
                       detective_name=detective_name, partner_name=partner_name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case = _safe_fact(world, f, "case")
    clue = _safe_fact(world, f, "clue_cfg")
    suspect = _safe_fact(world, f, "suspect")
    return [
        f'Write a short detective story that includes the words "odds", "ache", and "kook".',
        f"Tell a moody mystery where a detective follows {clue.phrase} and speaks with {suspect.label}.",
        f"Write a small detective story about {case.look}, with dialogue and a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = _safe_fact(world, f, "detective")
    p = _safe_fact(world, f, "partner")
    case = _safe_fact(world, f, "case")
    clue = _safe_fact(world, f, "clue_cfg")
    suspect = _safe_fact(world, f, "suspect")
    return [
        QAItem(
            question=f"What kind of story is this one about {d.id}?",
            answer=f"It is a detective story about {d.id} chasing {case.look} with {p.label}.",
        ),
        QAItem(
            question=f"What clue did {d.id} study during the case?",
            answer=f"{d.id} studied {clue.phrase}, which made the mystery feel more serious.",
        ),
        QAItem(
            question=f"Who was the kook in the story?",
            answer=f"The kook was {suspect.label}, and {suspect.tell}",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended badly. The detective lost the trail, and the case stayed open.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective for?",
            answer="A detective looks for clues, asks questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="What does bad odds mean?",
            answer="Bad odds mean the chance of success is low, so winning or solving the case is hard.",
        ),
        QAItem(
            question="What is an ache?",
            answer="An ache is a dull, lingering pain that can make someone feel tired and sore.",
        ),
        QAItem(
            question="What does kooky mean?",
            answer="Kooky means strange or funny in a way that stands out from what is normal.",
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
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CASES, params.case), _safe_lookup(CLUES, params.clue),
                 next(s for s in SUSPECTS if s.id == params.suspect),
                 params.detective_name, params.partner_name)
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
    StoryParams(place="dock", case="missing_ledger", clue="smudged_ink", suspect="kook1", detective_name="Mara", partner_name="Jo"),
    StoryParams(place="museum", case="stolen_key", clue="bent_key", suspect="kook2", detective_name="Nina", partner_name="Rae"),
    StoryParams(place="station", case="blackmail_note", clue="odd_smile", suspect="kook1", detective_name="Ivy", partner_name="Lee"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show case_valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
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
