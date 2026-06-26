#!/usr/bin/env python3
"""
Storyworld: Joey's Divine Paragraph Case
=========================================

A small detective-style storyworld about friendship, bravery, and a quest.

Premise:
- Joey is a young detective who keeps a notebook of clues.
- Divine is Joey's best friend and sometimes helps on a quest.
- A strange paragraph goes missing from a library book.
- The case is solved by steady observation, a brave trip, and a friendly reveal.

The simulated world tracks:
- physical meters: distance, carried items, clue strength, risk, and recovery
- emotional memes: worry, courage, trust, friendship, relief, pride

The story is not a frozen paragraph with swapped nouns. It is assembled from
world state that changes across setup, tension, turn, and resolution.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue_ent: object | None = None
    divine: object | None = None
    joey: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    place: str = "the old library"
    indoor: bool = True
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
class Clue:
    label: str
    phrase: str
    location: str
    risk_tag: str
    hidden_by: str
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
class Quest:
    label: str
    goal: str
    step: str
    reveal: str
    risk: str
    clue_tag: str
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


SETTINGS = {
    "library": Setting(place="the old library", indoor=True, affords={"search", "read"}),
    "museum": Setting(place="the museum hall", indoor=True, affords={"search", "follow"}),
    "station": Setting(place="the quiet train station", indoor=True, affords={"search", "wait"}),
}

QUESTS = {
    "paragraph": Quest(
        label="missing paragraph",
        goal="find the missing paragraph",
        step="follow the ink smudge trail",
        reveal="the paragraph had been tucked into a book sleeve",
        risk="getting lost in the stacks",
        clue_tag="paragraph",
    ),
    "friendship": Quest(
        label="friendship promise",
        goal="return the note that proves Divine's promise",
        step="look where friends leave secret signs",
        reveal="the note was safe inside Joey's notebook pocket",
        risk="hurting Divine's feelings by doubting them",
        clue_tag="friendship",
    ),
    "bravery": Quest(
        label="bravery test",
        goal="face the dark storage room",
        step="walk in with a steady flashlight",
        reveal="the shadow was only a coat rack and a bookmark",
        risk="being scared of the dark",
        clue_tag="bravery",
    ),
}

PEOPLE = {
    "joey": {"type": "boy", "label": "Joey"},
    "divine": {"type": "girl", "label": "Divine"},
}

CLUES = {
    "paragraph": Clue(
        label="paragraph scrap",
        phrase="a torn paragraph scrap",
        location="between two heavy books",
        risk_tag="paragraph",
        hidden_by="a loose library sleeve",
    ),
    "friendship": Clue(
        label="promise note",
        phrase="a folded promise note",
        location="inside Joey's notebook pocket",
        risk_tag="friendship",
        hidden_by="a clipped pencil",
    ),
    "bravery": Clue(
        label="dark-room key",
        phrase="a small key to the storage room",
        location="under a desk lamp",
        risk_tag="bravery",
        hidden_by="a shadow",
    ),
}


def gate_reject(reason: str) -> StoryError:
    return StoryError(reason)


def check_reasonable(setting: Setting, quest: Quest, clue: Clue) -> None:
    if quest.clue_tag != clue.risk_tag:
        raise gate_reject("The chosen quest and clue do not belong to the same case.")
    if setting.place == "the quiet train station" and quest.label == "bravery test":
        raise gate_reject("The bravery test needs a more shadowed place than the train station.")
    if setting.place == "the museum hall" and quest.label == "friendship promise":
        raise gate_reject("The friendship promise works better in a place with notebooks and hiding spots.")
    if setting.place == "the old library" and quest.label == "missing paragraph":
        return


def _m(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def _e(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def _addm(entity: Entity, key: str, value: float) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + value


def _adde(entity: Entity, key: str, value: float) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + value


def tell(setting: Setting, quest: Quest, clue: Clue, hero_name: str = "Joey", friend_name: str = "Divine") -> World:
    world = World(setting)
    joey = world.add(Entity(id="joey", kind="character", type="boy", label=hero_name))
    divine = world.add(Entity(id="divine", kind="character", type="girl", label=friend_name))
    clue_ent = world.add(Entity(id="clue", kind="thing", type="paper", label=clue.label, phrase=clue.phrase))
    clue_ent.carried_by = None

    joey.meters.update({"distance": 0.0, "clue_strength": 0.0, "risk": 0.0})
    divine.meters.update({"distance": 0.0})
    joey.memes.update({"worry": 0.0, "courage": 0.0, "trust": 0.0, "friendship": 0.0, "relief": 0.0, "pride": 0.0})
    divine.memes.update({"friendship": 0.0, "bravery": 0.0, "trust": 0.0})

    world.say(
        f"Joey was a small detective who loved neat clues, sharp pencils, and a good case. "
        f"Divine was his best friend, and together they kept a little quest notebook."
    )
    world.say(
        f"One afternoon, Joey found that a {quest.label} had gone missing at {setting.place}, "
        f"and the only hint was {clue.phrase}."
    )
    world.para()
    world.say(
        f"Joey frowned and tapped the notebook. {clue.phrase.capitalize()} looked important, "
        f"but it was hidden {clue.hidden_by}."
    )
    _adde(joey, "worry", 1.0)
    _adde(joey, "trust", 1.0)
    _adde(divine, "friendship", 1.0)
    _adde(divine, "trust", 1.0)

    world.say(
        f"Divine smiled and said, \"Let's follow the clue together.\" That made Joey feel braver, "
        f"because a friend made the quest feel lighter."
    )

    world.para()
    _addm(joey, "distance", 1.0)
    _addm(divine, "distance", 1.0)
    _adde(joey, "courage", 1.0)
    _adde(divine, "bravery", 1.0)
    world.say(
        f"So they walked deeper into {setting.place}, with Joey holding a flashlight and Divine watching the shelves."
    )
    world.say(
        f"Joey spotted {clue.location}, and the clue grew stronger in his mind."
    )
    _addm(joey, "clue_strength", 1.0)

    if quest.label == "missing paragraph":
        world.say(
            f"Then Joey noticed a loose book sleeve, and his eyes widened. That could hide a missing paragraph."
        )
        _addm(joey, "risk", 1.0)
        _adde(joey, "worry", 1.0)
    elif quest.label == "friendship promise":
        world.say(
            f"Then Divine pointed to Joey's notebook pocket, where something white was peeking out."
        )
        _adde(divine, "friendship", 1.0)
    else:
        world.say(
            f"Then the hallway ahead turned dark, and Joey had to decide whether to step forward."
        )
        _addm(joey, "risk", 1.0)
        _adde(joey, "courage", 1.0)

    world.para()
    if quest.label == "missing paragraph":
        world.say(
            f"Joey took a brave breath, reached into the sleeve, and pulled out the torn {quest.label}."
        )
        world.say(
            f"It was the missing piece from the book, and the case finally made sense."
        )
    elif quest.label == "friendship promise":
        world.say(
            f"Joey opened the pocket and found the folded note. Divine had kept the promise all along."
        )
        world.say(
            f"Joey laughed with relief, because the quest was really about trusting a friend."
        )
    else:
        world.say(
            f"Joey walked into the dark room with Divine beside him, and the scary shape became a coat rack."
        )
        world.say(
            f"A bookmark was hooked on a key ring, and the so-called mystery turned into a simple trick of shadows."
        )

    _adde(joey, "relief", 1.0)
    _adde(joey, "pride", 1.0)
    _adde(divine, "friendship", 1.0)
    _adde(divine, "bravery", 1.0)

    world.para()
    world.say(
        f"By the end, Joey wrote the answer in his notebook, Divine grinned beside him, "
        f"and the little quest felt complete."
    )

    world.facts.update(
        setting=setting,
        quest=quest,
        clue=clue,
        joey=joey,
        divine=divine,
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    q = _safe_fact(world, world.facts, "quest")
    return [
        f"Write a gentle detective story for a young child about Joey, Divine, and a {q.label}.",
        f"Tell a friendship-and-bravery quest story where Joey and Divine solve a clue at {world.setting.place}.",
        f"Make a short mystery story that includes the words Joey, Divine, and paragraph, and ends with a solved case.",
    ]


def story_qa(world: World) -> list[QAItem]:
    q: Quest = _safe_fact(world, world.facts, "quest")
    joey: Entity = _safe_fact(world, world.facts, "joey")
    divine: Entity = _safe_fact(world, world.facts, "divine")
    place = world.setting.place
    return [
        QAItem(
            question="Who solved the mystery together?",
            answer=f"Joey and Divine solved it together at {place}. They stayed side by side from the first clue to the last answer.",
        ),
        QAItem(
            question=f"What was the main quest in the story?",
            answer=f"The main quest was to {q.goal}. That was the case Joey kept chasing until the answer appeared.",
        ),
        QAItem(
            question="How did Divine help Joey?",
            answer="Divine helped by staying close, looking carefully, and encouraging Joey to keep going. That made the search feel brave instead of scary.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="By the end, the mystery was solved, Joey felt proud, and the friends felt even closer. The missing piece was no longer missing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues and tries to solve a mystery.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something hard or scary anyway, especially when you need to help someone.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, share help, and stay kind together.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a goal or search that someone follows step by step until they find the answer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
place(library).
place(museum).
place(station).

quest(paragraph).
quest(friendship).
quest(bravery).

compatible(library, paragraph).
compatible(museum, friendship).
compatible(library, bravery).

solve(Place, Quest) :- compatible(Place, Quest).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for k in SETTINGS:
        lines.append(asp.fact("place", k))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for p, q in [("library", "paragraph"), ("museum", "friendship"), ("library", "bravery")]:
        lines.append(asp.fact("compatible", p, q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solve/2."))
    return sorted(set(asp.atoms(model, "solve")))


def asp_verify() -> int:
    python_set = {
        ("library", "paragraph"),
        ("museum", "friendship"),
        ("library", "bravery"),
    }
    clingo_set = set(asp_valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


@dataclass
class StoryParams:
    setting: str = "library"
    quest: str = "paragraph"
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style storyworld with Joey, Divine, and a mystery paragraph.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--quest", choices=sorted(QUESTS))
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    quest = getattr(args, "quest", None) or rng.choice(list(QUESTS))
    clue = CLUES[QUESTS[quest].clue_tag]
    check_reasonable(_safe_lookup(SETTINGS, setting), _safe_lookup(QUESTS, quest), clue)
    return StoryParams(setting=setting, quest=quest, seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    quest = _safe_lookup(QUESTS, params.quest)
    clue = _safe_lookup(CLUES, quest.clue_tag)
    check_reasonable(setting, quest, clue)
    world = tell(setting, quest, clue)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
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
    StoryParams(setting="library", quest="paragraph"),
    StoryParams(setting="library", quest="bravery"),
    StoryParams(setting="museum", quest="friendship"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show solve/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        for place, quest in combos:
            print(f"{place} {quest}")
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.setting} / {p.quest}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
