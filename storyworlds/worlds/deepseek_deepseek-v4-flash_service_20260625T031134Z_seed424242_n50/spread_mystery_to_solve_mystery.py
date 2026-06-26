#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/spread_mystery_to_solve_mystery.py
====================================================================================================

A standalone story world for a mystery-themed domain. A small village (Woodville) has
a mysterious spread of missing items. Children must solve the mystery by following clues
and discovering where the items went.

Domain elements:
- Characters: a child, a parent, a friendly neighbor, and a playful pet (a magpie).
- The mystery: small shiny objects disappear from homes. The child works with the parent
  and neighbor to find clues, follow tracks, and discover that the magpie has been 
  collecting them in its nest.
- World state: clues found (clue_count), items missing (missing_count), tracks followed,
  suspicion about the magpie, resolution state.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

MISSING_ITEMS = {"spoon", "coin", "ring", "key", "button", "thimble"}
CLUE_TYPES = {"footprints", "feather", "shiny_trail", "nested_bits", "chewed_string"}



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
    type: str = "person"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)
    clues: set[str] = field(default_factory=set)

    hero: object | None = None
    neighbor: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "neighbor_lady"}
        male = {"boy", "father", "man", "neighbor_man"}
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
    place: str = "Woodville"
    affords: set[str] = field(default_factory=lambda: {"follow_trail", "ask_neighbor", "search_garden"})
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.missing_item_type: str = ""
        self.clue_found_count: int = 0
        self.mystery_solved: bool = False

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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> World:
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.missing_item_type = self.missing_item_type
        clone.clue_found_count = self.clue_found_count
        clone.mystery_solved = self.mystery_solved
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_spread_fear(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["missing_known"] >= THRESHOLD and actor.memes["curious"] < THRESHOLD:
            sig = ("fear", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["worried"] += 1
            out.append(f"A worry began to spread through {actor.label}.")
    return out


def _r_clue_discover(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("Hero")
    for clue in world.facts.get("encountered_clues", []):
        if clue in hero.clues:
            continue
        sig = ("clue", clue)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.clues.add(clue)
        world.clue_found_count += 1
        out.append(f"{hero.id} found {clue.replace('_', ' ')}.")
    return out


def _r_solve_mystery(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("Hero")
    required = {"shiny_trail", "feather", "nested_bits"}
    if required.issubset(hero.clues) and not world.mystery_solved:
        sig = ("solved",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        world.mystery_solved = True
        hero.memes["joy"] += 1
        out.append("The mystery was solved! The magpie had taken the items to its nest.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="spread_fear", tag="social", apply=_r_spread_fear),
    Rule(name="clue_discover", tag="fact", apply=_r_clue_discover),
    Rule(name="solve_mystery", tag="resolution", apply=_r_solve_mystery),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


WHATSIT = {"spoon": "a shiny spoon", "coin": "a silver coin", "ring": "a gold ring",
           "key": "a brass key", "button": "a blue button", "thimble": "a sewing thimble"}


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} lived in {world.setting.place}, a small town where nothing ever went missing.")


def mystery_begins(world: World, hero: Entity, parent: Entity, neighbor: Entity, item: str) -> None:
    world.missing_item_type = item
    world.say(f"One morning, {parent.label} said, 'My {WHATSIT[item]} is gone! I put it on the table last night.'")
    world.say(f"{hero.id} looked around. '{parent.label}, do you think someone took it?'")
    world.say(f"{neighbor.label} from next door knocked. 'Is something wrong? I saw a shiny trail in the garden.'")
    hero.meters["missing_known"] += 1
    world.facts["encountered_clues"] = ["shiny_trail", "footprints"]


def spread_clues(world: World, hero: Entity, neighbor: Entity) -> None:
    world.say(f"{hero.id} and {neighbor.label} followed the shiny trail. It went past the big oak tree.")
    world.say("There, they found a single gray feather and a piece of chewed string.")
    world.facts["encountered_clues"].extend(["feather", "chewed_string"])
    hero.memes["curious"] += 1
    propagate(world)


def search_garden(world: World, hero: Entity, parent: Entity) -> None:
    world.say(f"{hero.id} searched the garden carefully. Under the hedge, there were tiny bits of shiny paper and a small button.")
    world.facts["encountered_clues"].extend(["nested_bits", "button"])
    hero.memes["determined"] += 1
    propagate(world)


def solve_mystery(world: World, hero: Entity) -> None:
    if world.mystery_solved:
        world.say(f"{hero.id} gathered everyone. 'The magpie took them! Its nest is full of our things.'")
        world.say(f"They went to the old elm tree and found the nest. Inside was the {WHATSIT[world.missing_item_type]}, safe and sound.")
        world.say(f"{hero.id} smiled. 'The mystery is done. We solved it together.'")


def tell(setting: Setting, item: str,
         hero_name: str = "Emma", hero_type: str = "girl",
         parent_type: str = "mother", neighbor_type: str = "neighbor_lady") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        label=hero_name, traits=["clever", "brave"],
    ))
    parent = world.add(Entity(
        id=parent_type, kind="character", type=parent_type,
        label=parent_type if parent_type == "father" else "mom",
    ))
    neighbor = world.add(Entity(
        id=neighbor_type, kind="character", type=neighbor_type,
        label="Mrs. Green" if neighbor_type == "neighbor_lady" else "Mr. Brown",
    ))

    introduce(world, hero)
    mystery_begins(world, hero, parent, neighbor, item)
    world.para()
    spread_clues(world, hero, neighbor)
    world.para()
    search_garden(world, hero, parent)
    world.para()
    solve_mystery(world, hero)

    world.facts.update(hero=hero, parent=parent, neighbor=neighbor,
                       item=item, setting=setting)
    return world


SETTINGS = {
    "village": Setting(place="Woodville"),
}

ITEMS = ["spoon", "coin", "ring", "key", "button", "thimble"]

GIRL_NAMES = ["Emma", "Lucy", "Maya", "Sophie", "Clara"]
BOY_NAMES = ["Max", "Oliver", "Leo", "Finn", "Jake"]
TRAITS = ["clever", "curious", "brave", "observant", "patient"]


def valid_combos() -> list[tuple]:
    combos = []
    for setting in SETTINGS:
        for item in ITEMS:
            combos.append((setting, item))
    return combos


@dataclass
class StoryParams:
    place: str
    item: str
    name: str
    gender: str
    parent: str
    neighbor: str
    trait: str
    seed: Optional[int] = None
    params: object | None = None
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


KNOWLEDGE = {
    "magpie": [("What is a magpie?", "A magpie is a black-and-white bird that likes to collect shiny things and bring them to its nest.")],
    "mystery": [("What is a mystery?", "A mystery is something you do not understand at first, and you have to look for clues to solve it.")],
    "clue": [("What is a clue?", "A clue is a small piece of information that helps you figure out the answer to a mystery.")],
    "footprints": [("How do footprints help solve a mystery?", "Footprints show where someone walked, so you can follow them to find where they went.")],
    "nest": [("Where do birds build their nests?", "Birds build nests high in trees, using twigs and grass, to keep their eggs and babies safe.")],
    "shiny": [("Why do magpies like shiny things?", "Magpies are attracted to sparkly objects because they think they are pretty and useful for decorating their nests.")],
}
KNOWLEDGE_ORDER = ["magpie", "mystery", "clue", "footprints", "nest", "shiny"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, item = f["hero"], f["item"]
    return [
        f'Write a short mystery story for a child about a missing {item} that gets solved by following clues.',
        f"Tell a gentle story where {hero.id} solves the mystery of the disappearing shiny things in Woodville.",
        f"Write a simple story about a clever child who finds a magpie's nest and recovers the missing items.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, neighbor, item = f["hero"], f["parent"], f["neighbor"], f["item"]
    sub, obj, pos = hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")
    qa: list[QAItem] = [
        QAItem(
            question=f"Who solved the mystery of the missing {item} in {world.setting.place}?",
            answer=f"A clever {hero.type} named {hero.id} solved it with help from {neighbor.label} and {parent.label}."
        ),
        QAItem(
            question=f"What was missing from {hero.id}'s home?",
            answer=f"{parent.label}'s {WHATSIT[item]} was missing. It disappeared from the table one night."
        ),
        QAItem(
            question=f"What clues did {hero.id} find while searching?",
            answer=f"{sub} found a shiny trail, a feather, chewed string, and bits of paper in the garden."
        ),
    ]
    if world.mystery_solved:
        qa.append(QAItem(
            question=f"What was the solution to the mystery?",
            answer=f"The magpie had been collecting shiny things and took them to its nest in the old elm tree. {sub.capitalize()} and {pos} friends climbed up and found everything safe."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        if e.clues:
            bits.append(f"clues={sorted(e.clues)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  clue_found_count={world.clue_found_count}")
    lines.append(f"  mystery_solved={world.mystery_solved}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(Place, Item) :- setting(Place), item(Item).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    import storyworlds.asp as asp
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world: a missing item spread, clues to solve it.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--neighbor", choices=["neighbor_lady", "neighbor_man"])
    ap.add_argument("--name")
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS.keys()))
    item = getattr(args, "item", None) or rng.choice(ITEMS)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    neighbor = getattr(args, "neighbor", None) or (rng.choice(["neighbor_lady", "neighbor_man"]))
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place, item=item, name=name, gender=gender,
        parent=parent, neighbor=neighbor, trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.item, params.name,
                 params.gender, params.parent, params.neighbor)
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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for place, item in stories:
            print(f"  {place:9} {item:8}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in valid_combos():
            params = StoryParams(place=p[0], item=p[1], name=rng.choice(GIRL_NAMES),
                                 gender=rng.choice(["girl", "boy"]),
                                 parent=rng.choice(["mother", "father"]),
                                 neighbor=rng.choice(["neighbor_lady", "neighbor_man"]),
                                 trait=rng.choice(TRAITS))
            params.seed = base_seed
            samples.append(generate(params))
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
            header = f"### {p.name}: missing {p.item} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
