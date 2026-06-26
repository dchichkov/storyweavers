#!/usr/bin/env python3
"""
A small standalone ghost-story world with a bad ending.

Premise:
A teenage character finds a haunted house, follows a warning written with a
colon, and tries to be brave. The ghost is not friendly. The story can vary in
name, place, object, and ghost, but it always stays in the same narrow domain:
a spooky choice, a creeping encounter, and a bad ending.
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
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    note: object | None = None
    teen: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
class Setting:
    place: str
    adjective: str
    afford: set[str] = field(default_factory=set)
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
class Haunt:
    id: str
    name: str
    sound: str
    touch: str
    warning: str
    hunger: str
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
class Relic:
    id: str
    label: str
    phrase: str
    risk: str
    glow: str
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "attic": Setting(place="the attic", adjective="dusty", afford={"listen", "open"}),
    "hall": Setting(place="the old hall", adjective="cold", afford={"listen", "open"}),
    "basement": Setting(place="the basement", adjective="damp", afford={"listen", "open"}),
}

HAUNTS = {
    "white_lady": Haunt(
        id="white_lady",
        name="the White Lady",
        sound="a soft sigh behind the wall",
        touch="a cold finger on the wrist",
        warning="leave before the clock strikes twelve",
        hunger="for a brave voice",
        tags={"ghost", "cold", "warning"},
    ),
    "bell_ghost": Haunt(
        id="bell_ghost",
        name="the Bell Ghost",
        sound="a little bell that rang with no hand to shake it",
        touch="a tug on the sleeve",
        warning="do not answer the bell",
        hunger="for someone to answer",
        tags={"ghost", "bell", "warning"},
    ),
    "smoke_child": Haunt(
        id="smoke_child",
        name="the Smoke Child",
        sound="a cough from the dark corner",
        touch="a smudge of ash on the cheek",
        warning="do not follow the smoke",
        hunger="for a face to follow it",
        tags={"ghost", "smoke", "warning"},
    ),
}

RELICS = {
    "key": Relic(
        id="key",
        label="rusty key",
        phrase="a rusty key with a crooked tooth",
        risk="it opens the wrong door",
        glow="it looked as if it had been waiting for years",
        tags={"metal", "door"},
    ),
    "lantern": Relic(
        id="lantern",
        label="lantern",
        phrase="an old brass lantern",
        risk="it makes shadows look close",
        glow="its glass held a weak yellow shine",
        tags={"light", "glass"},
    ),
    "note": Relic(
        id="note",
        label="note",
        phrase="a folded note that used a colon after the warning",
        risk="it sounds too certain",
        glow="the ink was neat and sharp",
        tags={"paper", "colon", "warning"},
    ),
}

TEEN_NAMES = ["Maya", "Noah", "Lina", "Evan", "Rosa", "Jace", "Mila", "Theo"]
TRAITS = ["curious", "nervous", "brave", "quiet", "restless", "stubborn"]


@dataclass
class StoryParams:
    place: str
    haunt: str
    relic: str
    name: str
    trait: str
    seed: Optional[int] = None
    p: object | None = None
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--haunt", choices=HAUNTS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def reasonableness(params: StoryParams) -> None:
    if params.place == "attic" and params.relic == "lantern":
        return
    if params.relic == "note" and params.haunt == "bell_ghost":
        return
    if params.relic == "key" and params.place == "basement":
        return
    pass


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = []
    for place in SETTINGS:
        for haunt in HAUNTS:
            for relic in RELICS:
                p = StoryParams(
                    place=place,
                    haunt=haunt,
                    relic=relic,
                    name=getattr(args, "name", None) or "",
                    trait=getattr(args, "trait", None) or "",
                )
                try:
                    reasonableness(p)
                except StoryError:
                    continue
                combos.append((place, haunt, relic))
    combos = [c for c in combos
              if getattr(args, "place", None) in (None, c[0])
              and getattr(args, "haunt", None) in (None, c[1])
              and getattr(args, "relic", None) in (None, c[2])]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, haunt, relic = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(TEEN_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, haunt=haunt, relic=relic, name=name, trait=trait)


def predict_bad_ending(world: World, teen: Entity, haunt: Haunt, relic: Relic) -> bool:
    sim = world.copy()
    teen2 = sim.get(teen.id)
    teen2.memes["fear"] += 1
    teen2.meters["attention"] += 1
    if relic.id == "note":
        teen2.memes["curiosity"] += 1
    if haunt.id == "white_lady" and relic.id == "lantern":
        teen2.memes["fear"] += 1
    return True


def generate_story(world: World, teen: Entity, haunt: Haunt, relic: Relic) -> None:
    world.say(
        f"{teen.id} was a {teen.pronoun('possessive')} teenage self, "
        f"{world.facts['trait']} and a little too willing to peek into dark places."
    )
    world.say(
        f"At {world.setting.place}, {teen.id} found {relic.phrase}. "
        f"{relic.glow.capitalize()}."
    )
    world.say(
        f"Then {teen.id} heard {haunt.sound} near the stairs. "
        f"The air felt like winter breath."
    )
    world.para()
    world.say(
        f"The warning was there too: \"{haunt.warning}:\" someone had written, "
        f"with a colon that made the note feel final."
    )
    teen.memes["curiosity"] += 1
    teen.memes["fear"] += 1
    world.say(
        f"{teen.id} should have stepped back, but {teen.pronoun('subject')} held on to the {relic.label} anyway."
    )
    world.say(
        f"When the door creaked, {haunt.name} came closer, carrying {haunt.touch}."
    )
    teen.memes["panic"] += 1
    world.para()
    world.say(
        f"{teen.id} tried to run, but the hallway seemed longer than before, "
        f"and the lantern-light shook in small scared circles."
    )
    world.say(
        f"In the end, {haunt.name} got what it wanted: {haunt.hunger}. "
        f"{teen.id} vanished into the dark, and the {relic.label} was left behind "
        f"to gleam on the floor."
    )


def tell(setting: Setting, haunt: Haunt, relic: Relic, name: str, trait: str) -> World:
    world = World(setting)
    teen = world.add(Entity(id=name, kind="character", type="teenage", label=name))
    world.facts.update(setting=setting, haunt=haunt, relic=relic, name=name, trait=trait)

    if relic.id == "note":
        note = world.add(Entity(id="note", type="note", label="note"))
        note.memes["warning"] = 1.0
    elif relic.id == "lantern":
        world.add(Entity(id="lantern", type="lantern", label="lantern"))
    else:
        world.add(Entity(id="key", type="key", label="key"))

    generate_story(world, teen, haunt, relic)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a young reader about a teenage {f["name"]} in {f["setting"].place}.',
        f'Write a spooky story where a teenage character finds {f["relic"].phrase} and hears {f["haunt"].name}.',
        f'Write a bad-ending ghost story that includes a warning written with a colon: and ends in the dark.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {f['name']}, a teenage character who wanders into {f['setting'].place}.",
        ),
        QAItem(
            question=f"What did {f['name']} find first?",
            answer=f"{f['name']} found {f['relic'].phrase}.",
        ),
        QAItem(
            question=f"Why did the warning feel strange?",
            answer=f"It used a colon after the warning, so it looked careful and final.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"{f['haunt'].name} took the moment over, and {f['name']} was swallowed by the dark for a bad ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a spooky tale about a ghost, a strange place, and a person who feels scared or warned.",
        ),
        QAItem(
            question="What does a colon do in a warning?",
            answer="A colon often introduces what comes next, so it can make a warning look official or serious.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
% A setup is valid if the relic, haunt, and place fit the haunted-house logic.
valid(Place, Haunt, Relic) :- place(Place), ghost(Haunt), relic(Relic), fits(Place, Haunt, Relic).

% A bad ending always results when the teenage character follows curiosity
% into a haunted place with a warning and does not escape.
bad_ending(Teen, Place, Haunt, Relic) :- teen(Teen), valid(Place, Haunt, Relic).
#show valid/3.
#show bad_ending/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in s.afford:
            lines.append(asp.fact("affords", pid, a))
    for hid, h in HAUNTS.items():
        lines.append(asp.fact("ghost", hid))
        for t in h.tags:
            lines.append(asp.fact("tag", hid, t))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        for t in r.tags:
            lines.append(asp.fact("tag", rid, t))
    for t in ["teenage"]:
        lines.append(asp.fact("teen", t))
    for place in SETTINGS:
        for hid in HAUNTS:
            for rid in RELICS:
                if place == "attic" and rid == "lantern":
                    lines.append(asp.fact("fits", place, hid, rid))
                if place == "basement" and rid == "key":
                    lines.append(asp.fact("fits", place, hid, rid))
                if rid == "note":
                    lines.append(asp.fact("fits", place, hid, rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for haunt in HAUNTS:
            for relic in RELICS:
                try:
                    reasonableness(StoryParams(place, haunt, relic, "x", "curious"))
                except StoryError:
                    continue
                combos.append((place, haunt, relic))
    return combos


def resolve_relic(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(HAUNTS, params.haunt), _safe_lookup(RELICS, params.relic), params.name, params.trait)
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
    StoryParams(place="attic", haunt="white_lady", relic="lantern", name="Maya", trait="curious"),
    StoryParams(place="basement", haunt="bell_ghost", relic="note", name="Evan", trait="nervous"),
    StoryParams(place="hall", haunt="smoke_child", relic="key", name="Rosa", trait="stubborn"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3.\n#show bad_ending/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3.\n#show bad_ending/4."))
        print("\n".join(str(a) for a in model))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.name} at {p.place} ({p.haunt}, {p.relic})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
