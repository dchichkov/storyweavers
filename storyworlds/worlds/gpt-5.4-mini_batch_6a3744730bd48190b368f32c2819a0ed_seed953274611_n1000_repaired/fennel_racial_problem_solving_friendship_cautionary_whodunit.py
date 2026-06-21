#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fennel_racial_problem_solving_friendship_cautionary_whodunit.py
================================================================================================

A small standalone storyworld for a child-facing whodunit with:
- problem solving
- friendship
- cautionary choice-making

The world centers on a missing fennel bulb, a misleading note that includes the
word "racial", and a pair of friends who solve the mystery without jumping to
mean or risky conclusions.

The story is designed to be state-driven: entities hold physical meters and
emotional memes, clues change the world model, and the ending image proves what
changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    detail: str
    clues: list[str] = field(default_factory=list)
    safe: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    smell: str = ""
    edible: bool = False
    clue_word: str = ""
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Suspect:
    id: str
    label: str
    motive: str
    honest: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class StoryParams:
    place: str
    missing: str
    suspect: str
    clue: str
    detective: str
    friend: str
    detective_gender: str = "girl"
    friend_gender: str = "boy"
    adult: str = "mother"
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["uncertainty"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(place: Place, missing: Item, suspect: Suspect) -> bool:
    return place.safe and missing.clue_word and suspect.honest


def sensible_suspects() -> list[Suspect]:
    return [s for s in SUSPECTS.values() if s.honest]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for mid, item in ITEMS.items():
            for sid, sus in SUSPECTS.items():
                if reasonableness_gate(place, item, sus):
                    combos.append((pid, mid, sid))
    return combos


def _predict(world: World, missing_id: str) -> dict:
    sim = world.copy()
    sim.get("detective").meters["uncertainty"] += 1
    sim.get("friend").meters["uncertainty"] += 1
    return {
        "clue_count": len(sim.facts.get("clues", [])),
        "risk": sim.get(missing_id).meters["lostness"],
    }


def intro(world: World, detective: Entity, friend: Entity, place: Place) -> None:
    detective.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"{detective.id} and {friend.id} were best friends, and on a rainy afternoon "
        f"they walked into {place.label}. {place.detail}"
    )
    world.say(
        f"They had come to help find a missing thing, but they promised to be careful "
        f"and not point fingers too quickly."
    )


def report_missing(world: World, missing: Item, adult: Entity) -> None:
    world.say(
        f'"{missing.phrase} is gone," said {adult.id}. "It was here a minute ago."'
    )
    world.say(
        f"{adult.label_word.capitalize()} looked worried, because the kitchen smelled "
        f"like soup and something else sharp and green."
    )


def examine_clue(world: World, detective: Entity, clue: Item) -> None:
    detective.meters["evidence"] += 1
    clue.meters["noted"] += 1
    world.say(
        f"{detective.id} bent down and looked at the clue again. It smelled like "
        f"{clue.smell}, which was a strong hint."
    )


def caution(world: World, friend: Entity, detective: Entity, adult: Entity) -> None:
    friend.memes["care"] += 1
    world.say(
        f'{friend.id} held up a hand. "{detective.id}, let’s be careful," {friend.pronoun()} said. '
        f'"We should ask before touching anything else."'
    )
    world.say(
        f"{adult.label_word.capitalize()} nodded. That was the safest kind of thinking."
    )


def suspect_list(world: World, suspect: Suspect, clue: Item) -> None:
    world.say(
        f"They made a list. {suspect.label} seemed possible at first, but the clue word "
        f'"{clue.clue_word}" kept showing up in the note.'
    )


def accuse(world: World, detective: Entity, suspect: Suspect) -> None:
    detective.meters["certainty"] += 1
    world.say(
        f"{detective.id} nearly blamed {suspect.label}, but stopped. "
        f"There was not enough proof yet."
    )


def solve(world: World, detective: Entity, friend: Entity, missing: Item, clue: Item, suspect: Suspect) -> None:
    detective.memes["relief"] += 1
    friend.memes["relief"] += 1
    missing.meters["lostness"] = 0
    world.say(
        f"Then {friend.id} pointed at the note. It did not say who stole anything. "
        f"It only held two words: fennel and racial."
    )
    world.say(
        f"{detective.id} sniffed the bowl, sniffed the note, and thought of the herb box. "
        f"The sharp green smell matched the missing {missing.label}."
    )
    world.say(
        f"They found the {missing.label} tucked behind the sugar jar, where it had rolled "
        f"after someone set it down to answer the door."
    )
    world.say(
        f"{suspect.label} had not taken it at all. The real answer was simple: a busy hand, "
        f"a loose bulb, and a clue that looked mysterious only because it was incomplete."
    )


def ending(world: World, detective: Entity, friend: Entity, adult: Entity, missing: Item) -> None:
    detective.memes["pride"] += 1
    friend.memes["pride"] += 1
    world.say(
        f"{adult.label_word.capitalize()} laughed with relief and thanked them both. "
        f"Then {adult.pronoun()} put the fennel in a bright bowl so it would not hide again."
    )
    world.say(
        f"{detective.id} and {friend.id} washed their hands, shared a grin, and sat down "
        f"to soup that smelled like fennel and patience."
    )


def tell(place: Place, missing: Item, suspect: Suspect, clue: Item,
         detective_name: str = "Maya", detective_gender: str = "girl",
         friend_name: str = "Noah", friend_gender: str = "boy",
         adult_type: str = "mother") -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, role="adult", label="the adult"))

    world.add(Entity(id="place", type="place", label=place.label))
    world.add(Entity(id="missing", type="item", label=missing.label, attrs={"phrase": missing.phrase}))
    world.add(Entity(id="suspect", type="suspect", label=suspect.label))

    world.facts["clues"] = list(place.clues)

    intro(world, detective, friend, place)
    world.para()
    report_missing(world, missing, adult)
    examine_clue(world, detective, clue)
    caution(world, friend, detective, adult)
    suspect_list(world, suspect, clue)
    accuse(world, detective, suspect)
    world.para()
    solve(world, detective, friend, missing, clue, suspect)
    ending(world, detective, friend, adult, missing)

    world.facts.update(
        detective=detective,
        friend=friend,
        adult=adult,
        place=place,
        missing=missing,
        suspect=suspect,
        clue=clue,
        solved=True,
    )
    return world


PLACES = {
    "kitchen": Place(
        id="kitchen",
        label="the kitchen",
        detail="A pot hissed on the stove, and a little herb garden sat by the window."
    ),
    "garden": Place(
        id="garden",
        label="the garden",
        detail="The garden had rows of herbs and a muddy path between the pots."
    ),
    "market": Place(
        id="market",
        label="the market",
        detail="Stalls stood in neat lines, and baskets of greens were stacked shoulder-high."
    ),
}

ITEMS = {
    "fennel": Item(
        id="fennel",
        label="fennel",
        phrase="the fennel bulb",
        smell="sweet green licorice",
        edible=True,
        clue_word="fennel",
        tags={"herb", "food"},
    ),
    "note": Item(
        id="note",
        label="note",
        phrase="the little note",
        smell="ink and paper",
        edible=False,
        clue_word="racial",
        tags={"note", "clue"},
    ),
}

SUSPECTS = {
    "cat": Suspect(
        id="cat",
        label="the cat",
        motive="likes hiding in warm boxes",
        honest=True,
        tags={"pet"},
    ),
    "sibling": Suspect(
        id="sibling",
        label="the little sibling",
        motive="likes to help put groceries away",
        honest=True,
        tags={"family"},
    ),
    "visitor": Suspect(
        id="visitor",
        label="the visitor",
        motive="was only there to bring muffins",
        honest=True,
        tags={"guest"},
    ),
}

GIRL_NAMES = ["Maya", "Lina", "Tessa", "Zoe", "Ruby"]
BOY_NAMES = ["Noah", "Finn", "Theo", "Eli", "Owen"]


@dataclass
class StoryParams:
    place: str
    missing: str
    suspect: str
    clue: str
    detective: str
    friend: str
    detective_gender: str = "girl"
    friend_gender: str = "boy"
    adult: str = "mother"
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


KNOWLEDGE = {
    "fennel": [
        ("What is fennel?",
         "Fennel is a crunchy green vegetable with a sweet, licorice-like smell. People can cook it or eat it raw."),
    ],
    "clue": [
        ("What is a clue?",
         "A clue is a helpful sign that points toward an answer. In a mystery, clues help people solve what happened."),
    ],
    "care": [
        ("Why should you be careful in a mystery?",
         "You should be careful so you do not break a clue or jump to the wrong answer. Careful thinking helps solve problems safely."),
    ],
    "friendship": [
        ("Why do friends help each other solve problems?",
         "Friends help each other because two careful minds can notice more than one. They can stay calm and make better choices together."),
    ],
}

KNOWLEDGE_ORDER = ["fennel", "clue", "care", "friendship"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly whodunit that includes the words "{f["missing"].label}" and "racial".',
        f"Tell a cautious mystery story where {f['detective'].id} and {f['friend'].id} solve the case by thinking carefully, not by blaming the wrong person.",
        f"Write a friendship story about a missing {f['missing'].label} and a clue that looks strange at first but turns out to be important.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    friend = f["friend"]
    adult = f["adult"]
    missing = f["missing"]
    clue = f["clue"]
    suspect = f["suspect"]
    return [
        QAItem(
            question="What was missing?",
            answer=f"The fennel bulb was missing from the kitchen. It had rolled behind the sugar jar, so it looked like a mystery at first."
        ),
        QAItem(
            question="Why did the friends slow down and be careful?",
            answer=f"{friend.id} reminded {detective.id} not to blame anyone too fast. That kept them safe and helped them notice the real clue."
        ),
        QAItem(
            question=f"What did the strange note say?",
            answer=f"It had the words fennel and racial on it, but it was not a blame note. The words were only part of the clue, so the friends had to think before they decided what it meant."
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"They sniffed the bowl, matched the smell to the fennel, and found it hidden behind the sugar jar. That proved {suspect.label} was not guilty and the missing fennel had simply rolled away."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The adult laughed with relief, and the friends sat down to soup with the fennel back in the bowl. The mystery ended safely because they chose careful, friendly problem solving."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"fennel", "clue", "care", "friendship"}
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            for q, a in KNOWLEDGE[key]:
                out.append(QAItem(question=q, answer=a))
    return out


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", missing="fennel", suspect="cat", clue="note", detective="Maya", friend="Noah", detective_gender="girl", friend_gender="boy", adult="mother"),
    StoryParams(place="garden", missing="fennel", suspect="sibling", clue="note", detective="Lina", friend="Eli", detective_gender="girl", friend_gender="boy", adult="father"),
]


def explain_rejection(place: Place, missing: Item, suspect: Suspect) -> str:
    if not place.safe:
        return "(No story: the place is not a safe setting for this gentle mystery.)"
    if not missing.clue_word:
        return "(No story: the missing item does not have a clue word, so there is no whodunit to solve.)"
    if not suspect.honest:
        return "(No story: the chosen suspect setup is not reasonable for this child-friendly mystery.)"
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
safe_place(kitchen). safe_place(garden). safe_place(market).
has_clue(fennel). clue_word(note, racial).
reasonable(P, M, S) :- safe_place(P), has_clue(M), honest(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid, item in ITEMS.items():
        lines.append(asp.fact("item", mid))
        if item.clue_word:
            lines.append(asp.fact("has_clue", mid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("honest", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and Python gate.")
        print("  only in clingo:", sorted(cl - py))
        print("  only in python:", sorted(py - cl))
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, missing=None, suspect=None, clue=None, detective=None, friend=None, detective_gender=None, friend_gender=None, adult=None), random.Random(7)))
        _ = sample.story
        print("OK: normal story generation smoke test passed.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Child-friendly whodunit about a missing fennel bulb.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--missing", choices=ITEMS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=ITEMS)
    ap.add_argument("--detective")
    ap.add_argument("--friend")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
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
    if not combos:
        raise StoryError("(No valid combinations.)")
    place = args.place or rng.choice(sorted(PLACES))
    missing = args.missing or "fennel"
    suspect = args.suspect or rng.choice(sorted(SUSPECTS))
    clue = args.clue or "note"
    if missing not in ITEMS or suspect not in SUSPECTS or clue not in ITEMS:
        raise StoryError("Invalid selection.")
    if not reasonableness_gate(PLACES[place], ITEMS[missing], SUSPECTS[suspect]):
        raise StoryError(explain_rejection(PLACES[place], ITEMS[missing], SUSPECTS[suspect]))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if detective_gender == "girl" else "girl")
    detective = args.detective or rng.choice(GIRL_NAMES if detective_gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != detective])
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(
        place=place, missing=missing, suspect=suspect, clue=clue,
        detective=detective, friend=friend,
        detective_gender=detective_gender, friend_gender=friend_gender, adult=adult,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.missing not in ITEMS or params.suspect not in SUSPECTS or params.clue not in ITEMS:
        raise StoryError("Invalid params.")
    world = tell(
        PLACES[params.place], ITEMS[params.missing], SUSPECTS[params.suspect], ITEMS[params.clue],
        detective_name=params.detective, detective_gender=params.detective_gender,
        friend_name=params.friend, friend_gender=params.friend_gender, adult_type=params.adult,
    )
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
    if args.show_asp:
        print(asp_program("#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} reasonable combos:")
        for p, m, s in asp_valid_combos():
            print(p, m, s)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
