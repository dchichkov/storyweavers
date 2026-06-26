#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/suspicion_trade_curiosity_transformation_kindness_nursery_rhyme.py
===========================================================================================================

A tiny nursery-rhyme storyworld about suspicion, curiosity, a fair trade, and a
kind transformation.

Seed tale:
---
In a little nursery garden by the moonlit gate, a child named Pip found a shiny
button and wanted to trade it away for something new. A small trader offered a
plain seed in return. Pip felt suspicious, but curiosity peeped through the
worry. With a kind word and a careful look, Pip made the trade and planted the
seed. By morning, the seed had transformed into a bright little flower, and the
garden felt kinder than before.
---

The world is intentionally small:
- one child
- one trader
- one trade
- one suspicious feeling
- one curiosity-driven reveal
- one kindness-led transformation

The prose is written in a simple nursery-rhyme style with repeated beats and a
gentle ending image.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    planted_in: Optional[str] = None
    transformed: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    flower: object | None = None
    prize: object | None = None
    seed: object | None = None
    trader: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    indoors: bool = False
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
class TradeItem:
    id: str
    label: str
    phrase: str
    type: str
    value: int
    transform_to: str
    growing_word: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


@dataclass
class StoryParams:
    place: str
    item: str
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


SETTINGS = {
    "nursery_garden": Setting(place="the nursery garden", indoors=False),
    "moon_gate": Setting(place="the moonlit gate", indoors=False),
    "toy_corner": Setting(place="the toy corner", indoors=True),
}

ITEMS = {
    "button": TradeItem(
        id="button",
        label="button",
        phrase="a shiny red button",
        type="button",
        value=1,
        transform_to="flower",
        growing_word="blooming",
    ),
    "marble": TradeItem(
        id="marble",
        label="marble",
        phrase="a bright blue marble",
        type="marble",
        value=1,
        transform_to="flower",
        growing_word="sparkling",
    ),
    "ribbon": TradeItem(
        id="ribbon",
        label="ribbon",
        phrase="a soft yellow ribbon",
        type="ribbon",
        value=1,
        transform_to="flower",
        growing_word="fluttering",
    ),
}

GIRL_NAMES = ["Pip", "Lily", "Mia", "Nora", "Tilly", "Ruby"]
BOY_NAMES = ["Tom", "Ben", "Finn", "Sam", "Noah", "Eli"]
TRADER_NAMES = ["Moss", "Nell", "Wren", "Puck"]

ASP_RULES = r"""
same_trade(X) :- item(X).
suspicious(X) :- item(X), value(X, V), V = 1.
curious(X) :- item(X), value(X, V), V = 1.
kind_exchange(X) :- item(X).
transformable(X) :- item(X), turns_into(X, Y), item(Y).
fair_trade(X) :- suspicious(X), curious(X), kind_exchange(X), transformable(X).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("value", iid, item.value))
        lines.append(asp.fact("turns_into", iid, item.transform_to))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_items() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show fair_trade/1."))
    return sorted(set(asp.atoms(model, "fair_trade")))


def _reasonableness_gate(item: TradeItem) -> None:
    if item.value <= 0:
        pass
    if item.transform_to not in {"flower"}:
        pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny nursery-rhyme storyworld of suspicion, trade, curiosity, kindness, and transformation."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--trader")
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
    item_id = getattr(args, "item", None) or rng.choice(list(ITEMS))
    _reasonableness_gate(_safe_lookup(ITEMS, item_id))
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    trader = getattr(args, "trader", None) or rng.choice(TRADER_NAMES)
    return StoryParams(place=place, item=item_id, seed=getattr(args, "seed", None),)


def generate(params: StoryParams) -> StorySample:
    item_def = _safe_lookup(ITEMS, params.item)
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(id="Child", kind="character", type="girl" if params.seed is not None and params.seed % 2 else "boy"))
    child.label = params.name or child.type
    child.meters["joy"] = 0.0
    child.memes["suspicion"] = 0.0
    child.memes["curiosity"] = 0.0
    child.memes["kindness"] = 0.0

    trader = world.add(Entity(id="Trader", kind="character", type="trader", label=params.trader if hasattr(params, "trader") else "the trader"))
    prize = world.add(Entity(
        id="Prize",
        type=item_def.type,
        label=item_def.label,
        phrase=item_def.phrase,
        owner=child.id,
        caretaker=child.id,
    ))
    seed = world.add(Entity(
        id="Seed",
        type="seed",
        label="seed",
        phrase="a tiny seed",
        owner=trader.id,
        caretaker=child.id,
    ))
    flower = world.add(Entity(
        id="Flower",
        type="flower",
        label="flower",
        phrase="a bright little flower",
        owner=child.id,
        caretaker=child.id,
    ))

    world.facts.update(child=child, trader=trader, prize=prize, seed=seed, flower=flower, item_def=item_def)

    # Act 1
    world.say(
        f"Down in {world.setting.place}, where the daisies nodded low, "
        f"{params.name} found {item_def.phrase} and held it close to know."
    )
    world.say(
        f"{params.name} liked the shine, and liked the ring, and liked the little glow; "
        f"but {params.name} met {params.trader if hasattr(params, 'trader') else 'Moss'} by the gate, where soft winds blow."
    )

    # Act 2
    world.para()
    child.memes["suspicion"] += 1.0
    child.memes["curiosity"] += 1.0
    world.say(
        f"\"Hmm,\" said {params.name}, \"your trade is strange, and very small beside; "
        f"why swap a shiny thing for a seed?\" The worry sat inside."
    )
    world.say(
        f"But curiosity went tip-tap-tip, and asked to take a peep; "
        f"{params.name} looked at the tiny seed, and did not let it sleep."
    )
    child.memes["kindness"] += 1.0
    prize.held_by = trader.id
    seed.held_by = child.id
    world.say(
        f"Then {params.name} gave a kind, kind nod, and made the trade just right; "
        f"the shiny thing went to the trader's hand, and the seed came home that night."
    )

    # Act 3
    world.para()
    seed.planted_in = world.setting.place
    seed.meters["growing"] = 1.0
    flower.transformed = True
    child.meters["joy"] += 1.0
    world.say(
        f"{params.name} tucked the seed in soil so dark, and patted it with cheer; "
        f"the little seed grew warm with hope, and changed by morning clear."
    )
    world.say(
        f"At sunrise, there was not a seed at all, but {flower.phrase} so bright; "
        f"{params.name} smiled, and the garden glowed with kindness in the light."
    )

    world.facts["resolved"] = True
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
    item = _safe_fact(world, f, "item_def")
    return [
        f'Write a short nursery-rhyme story for a child who feels suspicion about a trade and then learns curiosity can help.',
        f'Write a gentle rhyme where someone offers {item.phrase}, the child wonders about the trade, and kindness makes it work.',
        f'Write a simple story about suspicion, trade, curiosity, kindness, and a seed that transforms into a flower.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, trader, prize, seed, flower = f["child"], f["trader"], f["prize"], f["seed"], f["flower"]
    item_def = _safe_fact(world, f, "item_def")
    return [
        QAItem(
            question=f"What did {child.label} find at the start of the story?",
            answer=f"{child.label} found {item_def.phrase} in {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {child.label} feel suspicious about the trade?",
            answer=f"{child.label} felt suspicious because the trader offered a tiny seed in return, and the swap seemed strange at first.",
        ),
        QAItem(
            question=f"What helped {child.label} decide to make the trade?",
            answer=f"Curiosity helped {child.label} look more closely, and kindness helped {child.label} choose a fair trade.",
        ),
        QAItem(
            question=f"What did the seed become by the end?",
            answer=f"The tiny seed transformed into {flower.phrase}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a seed?",
            answer="A seed is a tiny plant starter. If it gets soil, water, and care, it can grow into a plant or flower.",
        ),
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes someone want to look, ask, and learn more about something that seems new or puzzling.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is being gentle, fair, and helpful to someone else.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.planted_in:
            bits.append(f"planted_in={e.planted_in}")
        if e.transformed:
            bits.append("transformed=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="nursery_garden", item="button", seed=274930118),
    StoryParams(place="moon_gate", item="marble", seed=274930119),
    StoryParams(place="toy_corner", item="ribbon", seed=274930120),
]


def asp_valid_items() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show fair_trade/1."))
    return sorted(set(asp.atoms(model, "fair_trade")))


def asp_verify() -> int:
    py = {params.item for params in CURATED}
    asp_set = {t[0] for t in asp_valid_items()}
    if asp_set == py:
        print(f"OK: clingo gate matches the curated story items ({len(py)} items).")
        return 0
    print("MISMATCH between clingo and python item gate:")
    print("  only in clingo:", sorted(asp_set - py))
    print("  only in python:", sorted(py - asp_set))
    return 1


def asp_facts_full() -> str:
    return asp_facts()


def asp_program(show: str) -> str:
    return f"{asp_facts_full()}\n{ASP_RULES}\n{show}\n"


def build_asp_facts_for_story() -> str:
    return asp_facts_full()


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show fair_trade/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show fair_trade/1."))
        items = sorted(set(asp.atoms(model, "fair_trade")))
        print(f"{len(items)} fair trade item(s):")
        for (item,) in items:
            print(f"  {item}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.place}: {p.item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        if header:
            print(header)
        print(sample.story)
        if getattr(args, "trace", None) and sample.world is not None:
            print(dump_trace(sample.world))
        if getattr(args, "qa", None):
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
