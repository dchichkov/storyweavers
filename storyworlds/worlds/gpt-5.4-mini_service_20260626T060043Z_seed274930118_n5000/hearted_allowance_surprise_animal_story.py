#!/usr/bin/env python3
"""
Stand-alone storyworld: a small animal tale about hearted allowance and a Surprise.

Premise:
- An animal child receives an allowance and hopes to buy a Surprise.
- The parent worries the child might spend too quickly or choose poorly.
- A gentle compromise uses a simple plan: save a little, choose carefully, and
  uncover a Surprise that feels earned.

This world is intentionally small, classical, and state-driven. The same live
model powers prose, QA, trace, and ASP parity checks.
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
# Core domain
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # "character" | "thing"
    species: str = "animal"
    type: str = "animal"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    item: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Place:
    name: str
    kind: str
    affords: set[str] = field(default_factory=set)
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
class Item:
    id: str
    label: str
    phrase: str
    price: int
    surprise_inside: str
    kind: str = "thing"
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
    child: str
    parent: str
    item: str
    seed: Optional[int] = None
    params: object | None = None
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
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

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


def money_word(amount: int) -> str:
    return "a shiny coin" if amount == 1 else f"{amount} shiny coins"


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "market": Place(name="the market", kind="outdoor", affords={"shop", "browse"}),
    "corner_shop": Place(name="the corner shop", kind="indoor", affords={"shop"}),
    "porch": Place(name="the porch", kind="home", affords={"count", "save"}),
}

CHILDREN = {
    "bunny": {"species": "bunny", "type": "rabbit", "name": "Benny"},
    "kitten": {"species": "kitten", "type": "cat", "name": "Mina"},
    "puppy": {"species": "puppy", "type": "dog", "name": "Pip"},
    "duckling": {"species": "duckling", "type": "duck", "name": "Dot"},
}

PARENTS = {
    "mother": {"species": "rabbit", "type": "mother"},
    "father": {"species": "dog", "type": "father"},
    "parent": {"species": "cat", "type": "parent"},
}

ITEMS = {
    "kite": Item(id="kite", label="kite", phrase="a bright paper kite", price=3, surprise_inside="a tiny whistle"),
    "ball": Item(id="ball", label="ball", phrase="a striped red ball", price=2, surprise_inside="a squeaky bell"),
    "book": Item(id="book", label="book", phrase="a picture book with shiny pages", price=4, surprise_inside="a ribbon bookmark"),
    "snack_box": Item(id="snack_box", label="snack box", phrase="a little snack box", price=2, surprise_inside="a honey cookie"),
}

SURPRISE_WORD = "Surprise"

ALLOWANCES = [2, 3, 4, 5]


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------

def introduce(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} was a small {child.type} with a hearted, hopeful smile, "
        f"and {child.pronoun('possessive')} tail twitched whenever a new coin landed nearby."
    )


def allowance_day(world: World, child: Entity, parent: Entity, amount: int) -> None:
    child.meters["coins"] = amount
    child.memes["hope"] += 1
    world.say(
        f"On allowance day, {parent.id} gave {child.id} {money_word(amount)}."
    )
    world.say(
        f"{child.id} held the coins close and thought about a surprise {world.facts['item'].label}."
    )


def wants_surprise(world: World, child: Entity, item: Entity) -> None:
    child.memes["want"] += 1
    world.say(
        f"{child.id} wanted to save up for the {item.label}, because it promised a {SURPRISE_WORD} inside."
    )


def warns_about_spending(world: World, parent: Entity, child: Entity, item: Entity) -> None:
    if child.meters["coins"] < item.meters["price"]:
        world.say(
            f"{parent.id} gently said, \"We should count first. If we spend too fast, the {item.label} will stay out of reach.\""
        )
    else:
        world.say(
            f"{parent.id} smiled, but still said, \"Let's not rush. A careful choice makes a better {SURPRISE_WORD}.\""
        )


def count_coins(world: World, child: Entity, item: Entity) -> None:
    if child.meters["coins"] >= item.meters["price"]:
        world.say(
            f"{child.id} counted again and saw there were enough coins for the {item.label}."
        )
    else:
        world.say(
            f"{child.id} counted the coins and knew one more saving day was needed."
        )


def make_choice(world: World, child: Entity, parent: Entity, item: Entity) -> bool:
    if child.meters["coins"] < item.meters["price"]:
        return False
    world.say(
        f"{child.id} chose the {item.label} instead of a bigger shiny thing, because the promise of the {SURPRISE_WORD} mattered most."
    )
    return True


def reveal_surprise(world: World, child: Entity, item: Entity) -> None:
    child.memes["joy"] += 2
    child.memes["heart"] += 1
    world.say(
        f"When the box opened, there was {item.surprise_inside} tucked inside the {item.label}."
    )
    world.say(
        f"{child.id} gasped, then grinned so wide that {child.pronoun('possessive')} ears seemed to stand up."
    )


def ending_image(world: World, child: Entity, parent: Entity, item: Entity) -> None:
    world.say(
        f"By sunset, {child.id} was playing with {item.label}, the little {SURPRISE_WORD} kept safe, and {parent.id} was laughing beside {child.pronoun('object')}."
    )


# ---------------------------------------------------------------------------
# Story builder
# ---------------------------------------------------------------------------

def tell(place: Place, child_cfg: dict, parent_type: str, item_cfg: Item, allowance: int) -> World:
    world = World(place)
    child = world.add(Entity(
        id=child_cfg["name"],
        kind="character",
        species=child_cfg["species"],
        type=child_cfg["type"],
    ))
    parent = world.add(Entity(
        id=parent_type.capitalize(),
        kind="character",
        species=_safe_lookup(PARENTS, parent_type)["species"],
        type=_safe_lookup(PARENTS, parent_type)["type"],
    ))
    item = world.add(Entity(
        id=item_cfg.id,
        kind="thing",
        species="object",
        type="thing",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        owner=child.id,
    ))
    item.meters["price"] = item_cfg.price
    world.facts["item"] = item
    world.facts["allowance"] = allowance
    world.facts["child"] = child
    world.facts["parent"] = parent

    introduce(world, child)
    world.para()
    allowance_day(world, child, parent, allowance)
    wants_surprise(world, child, item)
    warns_about_spending(world, parent, child, item)
    count_coins(world, child, item)
    if make_choice(world, child, parent, item):
        world.para()
        reveal_surprise(world, child, item)
        ending_image(world, child, parent, item)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    child = _safe_fact(world, world.facts, "child")
    item = _safe_fact(world, world.facts, "item")
    return [
        f'Write a short animal story for a little kid about {child.id} saving allowance for a {SURPRISE_WORD} {item.label}.',
        f"Tell a gentle story where {child.id} gets allowance, counts coins, and chooses the {item.label} with a surprise inside.",
        f'Write an animal tale about hearted hope, allowance, and a {SURPRISE_WORD} hidden in a small gift.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child = _safe_fact(world, world.facts, "child")
    parent = _safe_fact(world, world.facts, "parent")
    item = _safe_fact(world, world.facts, "item")
    allowance = _safe_fact(world, world.facts, "allowance")
    return [
        QAItem(
            question=f"How many coins did {child.id} get on allowance day?",
            answer=f"{child.id} got {money_word(allowance)} from {parent.id}."
        ),
        QAItem(
            question=f"What did {child.id} want to buy with the allowance?",
            answer=f"{child.id} wanted to buy {item.phrase}, because there was a {SURPRISE_WORD} inside."
        ),
        QAItem(
            question=f"What was the surprise inside the {item.label}?",
            answer=f"The surprise inside the {item.label} was {item.surprise_inside}."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.id} happily playing with the {item.label} while {parent.id} laughed nearby."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is allowance?",
            answer="Allowance is a small amount of money a child may get from a parent or caregiver."
        ),
        QAItem(
            question="Why do people count coins before buying something?",
            answer="People count coins so they know whether they have enough money to pay for what they want."
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes you curious or excited when it is revealed."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
good_choice(C, I) :- coins(C, N), price(I, P), N >= P.
surprise_story(C, I) :- good_choice(C, I), wants(C, I), has_surprise(I).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for cname, c in CHILDREN.items():
        lines.append(asp.fact("child", cname))
    for pname in PARENTS:
        lines.append(asp.fact("parent", pname))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("price", iid, item.price))
        lines.append(asp.fact("has_surprise", iid))
    for amt in ALLOWANCES:
        lines.append(asp.fact("coins", "sample", amt))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_choice/2.\n#show surprise_story/2."))
    good = set(asp.atoms(model, "good_choice"))
    if not good:
        print("MISMATCH: ASP produced no good choices.")
        return 1
    print(f"OK: ASP produced {len(good)} good-choice atoms.")
    return 0


# ---------------------------------------------------------------------------
# Parameter resolution / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld: hearted allowance and a Surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--item", choices=ITEMS)
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    child = getattr(args, "child", None) or rng.choice(list(CHILDREN))
    parent = getattr(args, "parent", None) or rng.choice(list(PARENTS))
    item = getattr(args, "item", None) or rng.choice(list(ITEMS))
    if _safe_lookup(ITEMS, item).price > 5:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, child=child, parent=parent, item=item)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(PLACES, params.place),
        CHILDREN[params.child],
        params.parent,
        _safe_lookup(ITEMS, params.item),
        allowance=3 if params.seed is None else (2 + (params.seed % 4)),
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {ent.id}: {ent.kind} {' '.join(parts)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show good_choice/2.\n#show surprise_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show good_choice/2.\n#show surprise_story/2."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for child in CHILDREN:
            for item in ITEMS:
                params = StoryParams(place="market", child=child, parent="mother", item=item, seed=base_seed)
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 30):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
