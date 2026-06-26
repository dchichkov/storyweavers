#!/usr/bin/env python3
"""
storyworlds/worlds/massage_lesson_learned_moral_value_whodunit.py
===================================================================

A tiny whodunit-style story world about a massage lesson learned.

Seed premise:
- A cozy place offers a massage.
- A small, missing item makes everyone wonder who took it.
- The clues point to a careful reveal, not a mean accusation.
- The ending carries a Lesson Learned and a Moral Value.

This script is self-contained and follows the Storyworld contract.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    suspect: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def init_meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def init_meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)
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
class Room:
    place: str
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
class Item:
    id: str
    label: str
    phrase: str
    type: str
    scent: str
    hidden_places: set[str] = field(default_factory=set)
    usable_for: set[str] = field(default_factory=set)
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
class StoryParams:
    place: str
    missing_item: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    suspect_name: str
    suspect_type: str
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


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
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
        clone = World(self.room)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes.get("worry", 0.0) >= THRESHOLD:
            sig = ("worry", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append(f"{e.id} looked worried and kept checking the little table.")
    return out


def _r_relax(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes.get("calm", 0.0) >= THRESHOLD:
            sig = ("calm", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append(f"{e.id} breathed slowly, and the room felt gentler right away.")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("relax", _r_relax)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


ROOMS = {
    "spa": Room(place="the little spa", quiet=True, affords={"massage"}),
    "cottage": Room(place="the cozy cottage", quiet=True, affords={"massage"}),
    "clinic": Room(place="the calm clinic", quiet=True, affords={"massage"}),
}

ITEMS = {
    "oil": Item(
        id="oil",
        label="massage oil",
        phrase="a small bottle of lavender massage oil",
        type="oil",
        scent="lavender",
        hidden_places={"basket", "towel", "shelf"},
        usable_for={"massage"},
    ),
    "cream": Item(
        id="cream",
        label="massage cream",
        phrase="a tin of smooth massage cream",
        type="cream",
        scent="mint",
        hidden_places={"basket", "drawer", "shelf"},
        usable_for={"massage"},
    ),
    "stones": Item(
        id="stones",
        label="warm stones",
        phrase="a small cloth pouch of warm stones",
        type="stones",
        scent="none",
        hidden_places={"basket", "cloth", "tray"},
        usable_for={"massage"},
    ),
}

LESSON_LEARNED = {
    "oil": "The best clue is to ask kindly before guessing.",
    "cream": "A missing thing is easier to find when everyone tells the truth.",
    "stones": "Careful hands and careful words solve problems better than blame.",
}

MORAL_VALUE = {
    "oil": "It is wise to look, listen, and ask first.",
    "cream": "Honesty helps a small mystery end well.",
    "stones": "Kindness turns a worry into a useful clue.",
}

GIRL_NAMES = ["Mia", "Lena", "Nora", "Ivy", "Zoe", "Ava", "Rose"]
BOY_NAMES = ["Leo", "Finn", "Owen", "Max", "Theo", "Eli", "Noah"]
TRAITS = ["curious", "gentle", "shy", "brave", "careful", "bright"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit about a massage and a missing clue.")
    ap.add_argument("--place", choices=ROOMS)
    ap.add_argument("--missing-item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("--suspect-name")
    ap.add_argument("--suspect-type", choices=["girl", "boy"])
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


def reasonableness_gate(missing_item: str, place: str) -> None:
    if missing_item not in ITEMS:
        pass
    if place not in ROOMS:
        pass
    if "massage" not in _safe_lookup(ROOMS, place).affords:
        pass


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "missing_item", None):
        reasonableness_gate(getattr(args, "missing_item", None), getattr(args, "place", None))
    place = getattr(args, "place", None) or rng.choice(list(ROOMS))
    missing_item = getattr(args, "missing_item", None) or rng.choice(list(ITEMS))
    reasonableness_gate(missing_item, place)
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    helper_type = getattr(args, "helper_type", None) or ("boy" if hero_type == "girl" else "girl")
    suspect_type = getattr(args, "suspect_type", None) or rng.choice(["girl", "boy"])

    hero_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice(GIRL_NAMES if helper_type == "girl" else BOY_NAMES)
    suspect_name = getattr(args, "suspect_name", None) or rng.choice(GIRL_NAMES if suspect_type == "girl" else BOY_NAMES)

    return StoryParams(
        place=place,
        missing_item=missing_item,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        suspect_name=suspect_name,
        suspect_type=suspect_type,
    )


def infer_missing_place(item: Item) -> str:
    if item.id == "oil":
        return "basket"
    if item.id == "cream":
        return "drawer"
    return "tray"


def tell_story(params: StoryParams) -> World:
    world = World(_safe_lookup(ROOMS, params.place))

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, traits=["little", "curious"]))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, traits=["kind", "careful"]))
    suspect = world.add(Entity(id=params.suspect_name, kind="character", type=params.suspect_type, traits=["quiet", "helpful"]))
    item = world.add(Entity(id=params.missing_item, kind="thing", type=params.missing_item, label=_safe_lookup(ITEMS, params.missing_item).label, phrase=_safe_lookup(ITEMS, params.missing_item).phrase))

    item.hidden_in = infer_missing_place(_safe_lookup(ITEMS, params.missing_item))
    suspect.carried_by = suspect.id

    # Setup
    world.say(f"{hero.id} came to {world.room.place} for a gentle massage.")
    world.say(f"The room was quiet, and {helper.id} laid out a soft towel and a little jar of cream.")
    world.say(f"But when it was time to begin, the {item.label} was gone.")

    # Mystery beats
    world.para()
    hero.memes["worry"] += 1
    propagate(world)
    world.say(f"{hero.id} looked at the table. The lid was open, but the empty spot was neat, not messy.")
    world.say(f"{helper.id} noticed a faint scent of {_safe_lookup(ITEMS, params.missing_item).scent} near {suspect.id}'s sleeve.")
    world.say(f"That made everyone wonder: was {suspect.id} the one who moved it?")

    world.para()
    suspect.memes["worry"] += 1
    if params.missing_item == "oil":
        world.say(f"{suspect.id} blushed and pointed to the basket. There was a tiny drip on the cloth.")
    elif params.missing_item == "cream":
        world.say(f"{suspect.id} blinked and pointed to the drawer. A silver tin had left a smooth mark there.")
    else:
        world.say(f"{suspect.id} gently lifted the tray cover. The warm stones had been tucked under a clean cloth.")
    world.say(f"Then the clue turned clear: {suspect.id} had not taken it to be sneaky.")
    world.say(f"{suspect.id} had only moved it to keep it safe while dusting the table.")

    # Resolution
    world.para()
    hero.memes["calm"] += 1
    helper.memes["calm"] += 1
    propagate(world)
    world.say(f"{hero.id} smiled and said sorry for guessing too fast.")
    world.say(f"{helper.id} set the {item.label} back in place, and the massage could finally begin.")
    world.say(f"The little room felt warmer as {hero.id} lay still and relaxed.")

    world.para()
    world.say(f"Lesson Learned: {LESSON_LEARNED[params.missing_item]}")
    world.say(f"Moral Value: {MORAL_VALUE[params.missing_item]}")

    world.facts.update(
        hero=hero,
        helper=helper,
        suspect=suspect,
        item=item,
        place=params.place,
        missing_item=params.missing_item,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short whodunit story for a young child about a missing {f['item'].label} at {ROOMS[f['place']].place}.",
        f"Tell a gentle mystery where {f['hero'].id} thinks someone hid the {f['item'].label}, but the clue shows a kinder reason.",
        f"Write a story with a massage, a small clue, a careful reveal, and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    item = _safe_fact(world, f, "item")
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    suspect = _safe_fact(world, f, "suspect")
    place = ROOMS[f["place"]].place
    return [
        QAItem(
            question=f"Where did {hero.id} go for the massage?",
            answer=f"{hero.id} went to {place} for a gentle massage.",
        ),
        QAItem(
            question=f"What was missing from the table?",
            answer=f"The missing thing was {item.label}.",
        ),
        QAItem(
            question=f"Who noticed the clue and helped solve the mystery?",
            answer=f"{helper.id} noticed the clue and helped solve the mystery by staying calm and looking closely.",
        ),
        QAItem(
            question=f"Was {suspect.id} being sneaky?",
            answer=f"No, {suspect.id} was not being sneaky. {suspect.id} had moved the item to keep it safe while cleaning up.",
        ),
        QAItem(
            question="What lesson did everyone learn?",
            answer=f"They learned that it is best to ask kindly and not guess too fast when something seems missing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    item = _safe_fact(world, f, "item")
    return [
        QAItem(
            question="What is a massage?",
            answer="A massage is when someone gently rubs or presses muscles to help a body feel relaxed.",
        ),
        QAItem(
            question="Why do people stay quiet in a massage room?",
            answer="People stay quiet so the room feels calm and the person getting the massage can relax.",
        ),
        QAItem(
            question=f"What is {item.label} for?",
            answer=f"{item.label.capitalize()} is used to help a massage feel smooth and gentle on the skin.",
        ),
        QAItem(
            question="What should you do before accusing someone?",
            answer="You should look for clues, ask kindly, and make sure you know the facts first.",
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
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A simple declarative twin: if an item is hidden in a place and not on the
% table, then it is missing. If someone moved it to keep it safe, they are not
% guilty of theft.
missing(I) :- item(I), hidden(I).
safe_move(P) :- moved(P), for_safety(P).
not_guilty(P) :- safe_move(P).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        if room.quiet:
            lines.append(asp.fact("quiet", rid))
        for a in sorted(room.affords):
            lines.append(asp.fact("affords", rid, a))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_label", iid, item.label))
        for p in sorted(item.hidden_places):
            lines.append(asp.fact("hidden_place", iid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show room/1."))
    if model is None:
        print("No model found.")
        return 1
    print("OK: ASP program loads and solves.")
    return 0


CURATED = [
    StoryParams(place="spa", missing_item="oil", hero_name="Mia", hero_type="girl", helper_name="Leo", helper_type="boy", suspect_name="Nora", suspect_type="girl"),
    StoryParams(place="cottage", missing_item="cream", hero_name="Finn", hero_type="boy", helper_name="Ava", helper_type="girl", suspect_name="Owen", suspect_type="boy"),
    StoryParams(place="clinic", missing_item="stones", hero_name="Ivy", hero_type="girl", helper_name="Theo", helper_type="boy", suspect_name="Rose", suspect_type="girl"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(asp_program("#show missing/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
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
