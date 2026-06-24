#!/usr/bin/env python3
"""
A small storyworld about a naughty choice, a denied invitation, and a repaired
friendship during a tiny adventure.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

MAX_STEPS = 4



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
    kind: str = "character"
    type: str = "child"
    label: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    detail: str
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
class Adventure:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    reward: str
    tag: str
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
class FriendshipToken:
    id: str
    label: str
    phrase: str
    helps: str
    carries: str
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
class StoryParams:
    place: str
    adventure: str
    token: str
    name: str
    friend_name: str
    gender: str
    parent_name: str
    seed: Optional[int] = None
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


SETTINGS = {
    "woods": Setting(
        place="the woods",
        detail="Tall trees made a green tunnel, and a narrow path curled between ferns.",
        affords={"trail", "bridge"},
    ),
    "shore": Setting(
        place="the shore",
        detail="Small waves tapped the sand, and shells gleamed like tiny coins.",
        affords={"trail", "bridge", "cove"},
    ),
    "hill": Setting(
        place="the hill",
        detail="The hill was windy and bright, with a path that climbed up to a lookout rock.",
        affords={"trail", "bridge", "lookout"},
    ),
}

ADVENTURES = {
    "trail": Adventure(
        id="trail",
        verb="explore the trail",
        gerund="exploring the trail",
        rush="dash ahead on the trail",
        risk="get lost from the path",
        reward="find a hidden berry bush",
        tag="path",
    ),
    "bridge": Adventure(
        id="bridge",
        verb="cross the little bridge",
        gerund="crossing the little bridge",
        rush="run onto the bridge",
        risk="shake the boards too much",
        reward="see the river shining below",
        tag="river",
    ),
    "cove": Adventure(
        id="cove",
        verb="visit the cove",
        gerund="visiting the cove",
        rush="sprint toward the cove",
        risk="slip on wet stones",
        reward="find smooth shells",
        tag="water",
    ),
    "lookout": Adventure(
        id="lookout",
        verb="climb to the lookout",
        gerund="climbing to the lookout",
        rush="scramble up too fast",
        risk="tumble on the steep steps",
        reward="see the whole wide land",
        tag="view",
    ),
}

TOKENS = {
    "lantern": FriendshipToken(
        id="lantern",
        label="lantern",
        phrase="a little brass lantern",
        helps="light the way",
        carries="carried the lantern between them",
    ),
    "rope": FriendshipToken(
        id="rope",
        label="rope",
        phrase="a soft blue rope",
        helps="keep friends together",
        carries="held the rope carefully",
    ),
    "map": FriendshipToken(
        id="map",
        label="map",
        phrase="a folded paper map",
        helps="show the path",
        carries="studied the map together",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Leo", "Ben", "Finn", "Max", "Theo"]
TRAITS = ["curious", "spirited", "playful", "stubborn"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def valid_combo(place: str, adv: Adventure, tok: FriendshipToken) -> bool:
    return adv.tag in _safe_lookup(SETTINGS, place).affords and tok.label in {"lantern", "rope", "map"}


def all_valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for aid, adv in ADVENTURES.items():
            for tid, tok in TOKENS.items():
                if valid_combo(place, adv, tok):
                    out.append((place, aid, tid))
    return out


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", place, a))
    for aid, adv in ADVENTURES.items():
        lines.append(asp.fact("adventure", aid))
        lines.append(asp.fact("tag_of", aid, adv.tag))
    for tid, tok in TOKENS.items():
        lines.append(asp.fact("token", tid))
        lines.append(asp.fact("helps", tid, tok.helps.replace(" ", "_")))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(P,A,T) :- affords(P,Tag), tag_of(A,Tag), token(T).
#show compatible/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(all_valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("Mismatch between Python and ASP gates.")
    print("Only in Python:", sorted(py - cl))
    print("Only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A naughty denial turns into a friendship adventure.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--adventure", choices=ADVENTURES)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--parent-name")
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
    combos = all_valid_combos()
    combos = [c for c in combos
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "adventure", None) is None or c[1] == getattr(args, "adventure", None))
              and (getattr(args, "token", None) is None or c[2] == getattr(args, "token", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, adventure, token = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    parent_name = getattr(args, "parent_name", None) or rng.choice(["Mara", "Jon", "Pia", "Noel"])
    return StoryParams(place=place, adventure=adventure, token=token, name=name, friend_name=friend_name, gender=gender, parent_name=parent_name)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    adventure = _safe_lookup(ADVENTURES, params.adventure)
    token = _safe_lookup(TOKENS, params.token)
    world = World(setting)
    hero = world.add(Entity(id=params.name, type=params.gender))
    friend = world.add(Entity(id=params.friend_name, type="child"))
    parent = world.add(Entity(id=params.parent_name, type="adult"))

    hero.memes["naughty"] = 0
    hero.memes["friendship"] = 0
    friend.memes["hurt"] = 0
    friend.memes["hope"] = 0

    world.say(f"{hero.id} was a curious child who loved adventure, but {hero.pronoun('possessive')} naughty side sometimes caused trouble.")
    world.say(f"One bright day at {setting.place}, {hero.id} and {friend.id} found {token.phrase} while the wind moved softly through {setting.detail.lower()}")
    world.para()

    hero.memes["naughty"] += 1
    world.say(f"{friend.id} asked if {hero.id} wanted to go {adventure.gerund} together.")
    world.say(f"But {hero.id} wanted the path all to {hero.pronoun('object')} and said, \"No, I will go first.\"")
    world.say(f"That was a naughty way to act, because it denied friendship and made {friend.id} stop smiling.")
    friend.memes["hurt"] += 1

    world.para()
    world.say(f"{hero.id} rushed to {adventure.rush}, but soon {adventure.risk}.")
    world.say(f"{friend.id} did not leave. Instead, {friend.pronoun().capitalize()} held up {token.phrase} and said, \"We can do this together.\"")
    world.say(f"{token.carries}, and its light began to {token.helps}.")

    world.para()
    hero.memes["naughty"] = 0
    hero.memes["friendship"] += 1
    friend.memes["hope"] += 1
    world.say(f"{hero.id} looked at {friend.id} and felt sorry for denying the invitation.")
    world.say(f"{hero.id} said, \"I was naughty. I'm sorry. Please come with me.\"")
    world.say(f"{friend.id} smiled again, and the two friends went on {adventure.gerund} side by side.")
    world.say(f"Together they got to {adventure.reward}, and the little adventure felt bigger because nobody walked alone.")

    world.facts = {
        "hero": hero,
        "friend": friend,
        "parent": parent,
        "setting": setting,
        "adventure": adventure,
        "token": token,
    }
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f'Write a short adventure story for a young child about "{params.name}" being naughty, denying friendship, and then making up.',
            f"Tell a gentle story where {params.name} refuses {params.friend_name}'s invitation, but the two children repair their friendship during an adventure.",
            f'Write a simple story that includes the words "naughty" and "deny" and ends with friends exploring together.',
        ],
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    adv: Adventure = f["adventure"]  # type: ignore[assignment]
    token: FriendshipToken = f["token"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was naughty at first in the story?",
            answer=f"{hero.id} was naughty at first, because {hero.pronoun('subject')} denied {friend.id}'s invitation to go {adv.gerund}.",
        ),
        QAItem(
            question=f"What did {hero.id} deny?",
            answer=f"{hero.id} denied friendship for a moment by saying no when {friend.id} asked to go {adv.gerund} together.",
        ),
        QAItem(
            question=f"How did the friends make the adventure better?",
            answer=f"They used {token.phrase} to help them stay together, and then they went {adv.gerund} side by side at {setting.place}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} and {friend.id} being friends again and reaching {adv.reward}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    adv: Adventure = f["adventure"]  # type: ignore[assignment]
    token: FriendshipToken = f["token"]  # type: ignore[assignment]
    return [
        QAItem(
            question="What is an adventure?",
            answer="An adventure is an exciting activity or journey where something new can happen.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means being kind to someone, sharing time together, and helping each other.",
        ),
        QAItem(
            question=f"What does {token.label} help with in this world?",
            answer=f"{token.phrase} helps friends stay together while they are {adv.gerund}.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: memes={e.memes}")
    return "\n".join(lines)


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
    StoryParams(place="woods", adventure="trail", token="map", name="Mia", friend_name="Leo", gender="girl", parent_name="Mara"),
    StoryParams(place="shore", adventure="cove", token="lantern", name="Ben", friend_name="Ava", gender="boy", parent_name="Jon"),
    StoryParams(place="hill", adventure="lookout", token="rope", name="Nora", friend_name="Theo", gender="girl", parent_name="Pia"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
