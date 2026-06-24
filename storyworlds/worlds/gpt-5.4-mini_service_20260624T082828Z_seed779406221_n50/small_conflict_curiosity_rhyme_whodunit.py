#!/usr/bin/env python3
"""
Small Conflict Curiosity Rhyme Whodunit
=======================================

A tiny, child-facing mystery world: someone loses a small thing, curiosity pulls
the hero through clues, conflict rises when accusations start, and rhyme helps
reveal the truth.

The story model is state-driven: a few entities, a few clues, one mistake, one
turn, and a resolution that proves what changed.
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

    culprit: object | None = None
    friend: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    place: str = "the small library"
    detail: str = "It was a quiet room with a low table and a warm lamp."
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
    label: str
    place: str
    rhyme: str
    points_to: str
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
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    missing_item: str
    culprit: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def copy(self) -> "World":
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def make_setting(place: str) -> Setting:
    return _safe_lookup(SETTINGS, place)


def tell(setting: Setting, params: StoryParams) -> World:
    w = World(setting)

    hero = w.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    friend = w.add(Entity(id=params.friend_name, kind="character", type=params.friend_type))
    culprit = w.add(Entity(id=params.culprit, kind="character", type="boy" if params.culprit in {"Noah", "Tom"} else "girl"))
    item = w.add(Entity(id="missing_item", type=params.missing_item, label=params.missing_item, owner=hero.id))
    clue1 = _safe_lookup(CLUES, params.place)[0]
    clue2 = _safe_lookup(CLUES, params.place)[1]

    hero.memes["curiosity"] += 1
    friend.memes["nervous"] += 1

    w.say(
        f"{hero.id} was a small {hero.type} who loved quiet puzzles. "
        f"One morning, {hero.pronoun('possessive')} {item.label} was gone."
    )
    w.say(
        f"{friend.id} pointed at the empty spot and said, "
        f'"Something is missing!" The room felt very small all at once.'
    )

    w.para()
    w.say(
        f"{hero.id} looked under the chair, beside the shelf, and near the rug. "
        f"{hero.pronoun().capitalize()} was curious enough to notice even tiny things."
    )
    w.say(
        f"At the corner table, {hero.id} found a crumb, a ribbon, and a little note. "
        f"It read: '{clue1.rhyme}'."
    )
    w.facts["clue1"] = clue1
    w.facts["clue2"] = clue2
    w.facts["item"] = item
    w.facts["hero"] = hero
    w.facts["friend"] = friend
    w.facts["culprit"] = culprit

    w.para()
    w.say(
        f"{friend.id} guessed, \"Maybe {culprit.id} took it!\" "
        f"That made the room tense and the voices sharp."
    )
    w.say(
        f"{hero.id} shook {hero.pronoun('possessive')} head. "
        f"\"Let's follow the clue first,\" {hero.pronoun()} said, because curiosity "
        f"was stronger than blame."
    )

    w.para()
    w.say(
        f"The next clue was hidden by the window: '{clue2.rhyme}'. "
        f"{hero.id} matched the two lines together and walked to the last place they pointed."
    )
    if params.culprit == "Rabbit":
        w.say(
            f"Behind a tiny stack of books, {culprit.id} was sitting on the item. "
            f"The little rabbit had not stolen it on purpose; it had only dragged it away to nest."
        )
    else:
        w.say(
            f"Behind a tiny stack of books, {culprit.id} was holding the item. "
            f"{culprit.id} had borrowed it to play a game and then forgotten to put it back."
        )

    w.say(
        f"{hero.id} smiled instead of scolding. {hero.pronoun().capitalize()} "
        f"showed {culprit.id} where the item belonged, and the small mystery was solved."
    )
    item.meters["found"] += 1
    culprit.memes["relief"] += 1
    friend.memes["relief"] += 1

    w.facts["resolved"] = True
    return w


SETTINGS = {
    "library": Setting(
        place="the small library",
        detail="It was a quiet room with low shelves and a round reading rug.",
    ),
    "classroom": Setting(
        place="the small classroom",
        detail="It was a neat room with a chalkboard and a row of tiny desks.",
    ),
    "playroom": Setting(
        place="the small playroom",
        detail="It was a bright room with toy bins and a soft blue mat.",
    ),
}

CLUES = {
    "library": [
        Clue(id="clue_a", label="bookmark", place="shelf", rhyme="If pages are near, then look and hear", points_to="bookshelf"),
        Clue(id="clue_b", label="dust trail", place="window", rhyme="Where light falls thin, the clue is in", points_to="window"),
    ],
    "classroom": [
        Clue(id="clue_a", label="chalk fleck", place="chalkboard", rhyme="If chalk can sing, it points to spring", points_to="board"),
        Clue(id="clue_b", label="paper scrap", place="window", rhyme="By the bright glass, the answer will pass", points_to="window"),
    ],
    "playroom": [
        Clue(id="clue_a", label="toy wheel mark", place="bin", rhyme="If toys rolled by, look low and shy", points_to="toy bin"),
        Clue(id="clue_b", label="string loop", place="mat", rhyme="Where soft things rest, the clue is best", points_to="mat"),
    ],
}

HERO_NAMES = ["Mina", "Luca", "Nia", "Owen", "Sara", "Ben"]
FRIEND_NAMES = ["Pip", "Tia", "Jae", "Milo", "June", "Kai"]
CULPRITS = ["Rabbit", "Nora", "Sam", "Mouse"]


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    missing_item: str
    culprit: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld with curiosity, conflict, and rhyme.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("--missing-item", choices=["book", "crayon", "button"])
    ap.add_argument("--culprit", choices=sorted(CULPRITS))
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
    place = getattr(args, "place", None) or rng.choice(sorted(SETTINGS))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    friend_type = getattr(args, "friend_type", None) or ("boy" if hero_type == "girl" else "girl")
    hero_name = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice(FRIEND_NAMES)
    missing_item = getattr(args, "missing_item", None) or rng.choice(["book", "crayon", "button"])
    culprit = getattr(args, "culprit", None) or rng.choice(CULPRITS)
    if hero_name == friend_name:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type,
                       friend_name=friend_name, friend_type=friend_type,
                       missing_item=missing_item, culprit=culprit)


def generate(params: StoryParams) -> StorySample:
    world = tell(make_setting(params.place), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a small whodunit about {hero.id} in {world.setting.place}.",
        "Tell a gentle mystery story where curiosity follows clues and blame is avoided.",
        f"Write a child-friendly mystery that includes rhyme and ends with the lost {f['item'].label} found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    culprit = f["culprit"]
    item = f["item"]
    clue1 = f["clue1"]
    clue2 = f["clue2"]
    return [
        QAItem(
            question=f"What was missing in the story?",
            answer=f"{hero.id}'s {item.label} was missing at the start of the story.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the mystery?",
            answer=f"{hero.id} followed two rhyme clues: '{clue1.rhyme}' and '{clue2.rhyme}', then found the answer.",
        ),
        QAItem(
            question=f"Why did the room feel tense?",
            answer=f"The room felt tense when {friend.id} blamed {culprit.id} before the clues were finished.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"The missing {item.label} was found, and the small mystery was solved without a big fight.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is curiosity?", answer="Curiosity is the wish to ask questions, look closely, and learn what is going on."),
        QAItem(question="What is a clue?", answer="A clue is a small piece of information that helps solve a mystery."),
        QAItem(question="What is rhyme?", answer="Rhyme is when words sound alike at the end, like light and night."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for place, clues in CLUES.items():
        for c in clues:
            lines.append(asp.fact("clue", place, c.id))
            lines.append(asp.fact("rhyme", c.id, c.rhyme))
            lines.append(asp.fact("points_to", c.id, c.points_to))
    return "\n".join(lines)


ASP_RULES = r"""
visible_clue(P, C) :- clue(P, C), rhyme(C, _).
good_story(P) :- place(P), visible_clue(P, _).
#show good_story/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/1."))
    atoms = asp.atoms(model, "good_story")
    if len(atoms) == len(SETTINGS):
        print("OK: ASP gate matches the small storyworld.")
        return 0
    print("Mismatch in ASP verification.")
    return 1


def asp_places() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/1."))
    return sorted(set(asp.atoms(model, "good_story")))


CURATED = [
    StoryParams(place="library", hero_name="Mina", hero_type="girl", friend_name="Pip", friend_type="boy", missing_item="book", culprit="Mouse"),
    StoryParams(place="classroom", hero_name="Owen", hero_type="boy", friend_name="Tia", friend_type="girl", missing_item="crayon", culprit="Sam"),
    StoryParams(place="playroom", hero_name="Nia", hero_type="girl", friend_name="Jae", friend_type="boy", missing_item="button", culprit="Rabbit"),
]


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
        print(asp_program("#show good_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP support is available for the small whodunit world.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
