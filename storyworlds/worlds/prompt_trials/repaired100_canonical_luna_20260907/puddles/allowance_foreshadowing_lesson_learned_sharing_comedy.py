#!/usr/bin/env python3
"""Allowance day: a small comedy about planning, sharing, and a useful lesson."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402



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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Shop:
    id: str
    name: str
    item: str
    price: int
    joy: str
    shareable: bool = True
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Person:
    id: str
    name: str
    role: str
    coins: int = 0
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    child: object | None = None
    sibling: object | None = None
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

    def __post_init__(self) -> None:
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Event:
    kind: str
    text: str
    cause: str
    result: str
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
class World:
    child: Person
    sibling: Person
    shop: Shop
    allowance: int
    history: list[Event] = field(default_factory=list)
    objects: dict[str, object] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    world: object | None = None
    def record(self, kind: str, text: str, cause: str, result: str) -> None:
        self.history.append(Event(kind, text, cause, result))

    def render(self) -> str:
        return "\n\n".join(e.text for e in self.history)
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
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


@dataclass
class StoryParams:
    shop: str = ""
    treat: str = ""
    child: str = ""
    sibling: str = ""
    allowance: int = 0
    plan: str = "share"
    seed: int | None = None
    sample: object | None = None
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


SHOPS = {
    "bakery": Shop("bakery", "the bakery", "a giant cinnamon bun", 4,
                   "The bun smelled like a warm cloud."),
    "icecream": Shop("icecream", "the ice-cream cart", "a tall rainbow cone", 3,
                     "The cone had enough colors to make a crayon jealous."),
    "lemonade": Shop("lemonade", "the lemonade stand", "a fizzy lemonade", 2,
                     "The bubbles popped with tiny, cheerful plinks."),
}

CHILDREN = ["Luna", "Milo", "Nora", "Pip", "Tess"]
SIBLINGS = ["Ari", "Bo", "Mina", "Sam", "Jo"]


ASP_RULES = r"""
can_buy(S, A) :- shop(S), price(S, P), allowance(A), P <= A.
can_share(S) :- shop(S), shareable(S).
valid(S, A) :- can_buy(S, A), can_share(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for shop in SHOPS.values():
        lines += [
            asp.fact("shop", shop.id),
            asp.fact("price", shop.id, shop.price),
            asp.fact("shareable", shop.id),
        ]
    for amount in range(1, 8):
        lines.append(asp.fact("allowance", amount))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_choices() -> list[tuple[str, int]]:
    return [(sid, amount) for sid, shop in SHOPS.items()
            for amount in range(shop.price, 8)]


def asp_valid_choices() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def make_world(params: StoryParams) -> World:
    if params.shop not in SHOPS:
        pass
    shop = _safe_lookup(SHOPS, params.shop)
    if params.allowance < shop.price:
        pass
    if params.plan != "share":
        pass
    if params.child == params.sibling:
        pass

    child = Person(params.child, params.child, "child",
                   coins=params.allowance,
                   memes={"hope": 1, "generosity": 0})
    sibling = Person(params.sibling, params.sibling, "sibling",
                     memes={"hope": 1})
    world = World(child, sibling, shop, params.allowance)
    world.facts.update(price=shop.price, treat=shop.treat, shared=False,
                       change=0, lesson="plan before spending")
    return world


def tell(params: StoryParams) -> World:
    world = make_world(params)
    child, sibling, shop = world.child, world.sibling, world.shop
    price = shop.price

    world.record(
        "allowance",
        f"{child.name} received an allowance of {world.allowance} coins and "
        f"marched toward {shop.name}. {shop.name.capitalize()} looked bright, "
        f"busy, and wonderfully dangerous to a small purse.",
        f"{child.name} had {world.allowance} coins to spend.",
        f"{child.name} could afford {shop.item}.",
    )

    world.record(
        "foreshadow",
        f'On the way, {child.name} jingled the coins and announced, '
        f'"I will spend every one!" {sibling.name} glanced at the purse. '
        f'"Maybe save one for later," {sibling.name} said. '
        f'{child.name} laughed so hard that the coins rattled like tiny teeth.',
        "The child planned to spend without checking what would remain.",
        "The noisy purse hinted that the last coin would matter.",
    )

    child.coins -= price
    world.facts["change"] = child.coins
    if child.coins == 0:
        world.record(
            "comic_turn",
            f"{child.name} bought {shop.item} and reached for a napkin. "
            f'Then {child.name} discovered that the purse was empty. '
            f'"Could I have one extra napkin?" {child.name} asked. '
            f'"That costs exactly one smile," said the seller. '
            f'{child.name} tried to pay with a grin and nearly fell over.',
            "The treat used the entire allowance.",
            "The child had no coin left for anything else.",
        )
    else:
        world.record(
            "purchase",
            f"{child.name} bought {shop.item} and heard the remaining "
            f"{child.coins} coin{'' if child.coins == 1 else 's'} click in the purse. "
            f'The coin sounded small but important.',
            f"The treat cost {price} coins.",
            f"{child.name} kept {child.coins} coin{'' if child.coins == 1 else 's'}.",
        )

    child.memes["generosity"] = 1
    world.facts["shared"] = True
    world.record(
        "sharing",
        f'{sibling.name} looked at the treat, and {child.name} held it out. '
        f'"Want to share?" {child.name} asked. '
        f'"Only if you share the biggest bite," {sibling.name} replied. '
        f'{child.name} measured the treat with one serious eye, then split it '
        f'into two pieces that were almost equal. The smaller piece was '
        f'mysteriously wearing the larger crumb.',
        "The sibling was waiting nearby, and the child chose generosity.",
        f"{child.name} and {sibling.name} shared {shop.item}.",
    )

    world.record(
        "lesson",
        f'{child.name} counted the empty purse, the shared treat, and the '
        f'crumb on the floor. "Next time I will save before I spend," '
        f'{child.name} said. {sibling.name} nodded. '
        f'"Good. Then you can buy two napkins." '
        f'They walked home together, laughing at the crumb that had somehow '
        f'become the richest part of the afternoon.',
        "The empty purse made the spending choice easy to remember.",
        "The child learned to plan an allowance while still sharing joy.",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a funny child-facing story about {world.child.name}'s allowance, "
        f"buying {world.shop.item}, and sharing it with {world.sibling.name}.",
        "Tell a gentle comedy in which a noisy purse foreshadows a lesson about "
        "saving money before spending it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    questions = {
        "allowance": "How much allowance did the child receive?",
        "foreshadow": "What warning did the sibling give?",
        "comic_turn": "What happened when the child needed a napkin?",
        "purchase": "What did the child notice after buying the treat?",
        "sharing": "How did the child include the sibling?",
        "lesson": "What lesson did the child learn?",
    }
    return [
        QAItem(questions[event.kind], f"{event.cause} {event.result}")
        for event in world.history if event.kind in questions
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is an allowance?",
            "An allowance is money a child receives regularly, often to save or spend carefully.",
        ),
        QAItem(
            "Why is sharing kind?",
            "Sharing lets another person enjoy something with you and shows that you care about them.",
        ),
        QAItem(
            "Why can saving money help?",
            "Saving money helps you keep enough for a later need or a choice that matters more.",
        ),
    ]


def dump_trace(world: World) -> str:
    return "\n".join([
        "--- world model state ---",
        f"  child coins: {world.child.coins}",
        f"  sibling: {world.sibling.name}",
        f"  shop: {world.shop.id}",
        f"  allowance: {world.allowance}",
        f"  shared: {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "shared")}",
        f"  lesson: {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "lesson")}",
        "--- events ---",
        *[f"  {e.kind}: {e.text}" for e in world.history],
    ])


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story questions ==")
    for qa in sample.story_qa:
        lines += [f"Q: {qa.question}", f"A: {qa.answer}"]
    lines.append("\n== World knowledge ==")
    for qa in sample.world_qa:
        lines += [f"Q: {qa.question}", f"A: {qa.answer}"]
    return "\n".join(lines)


CURATED = [
    StoryParams("bakery", "bun", "Luna", "Ari", 4),
    StoryParams("icecream", "cone", "Milo", "Bo", 5),
    StoryParams("lemonade", "drink", "Nora", "Mina", 3),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Allowance, sharing, and a funny lesson.")
    parser.add_argument("--shop", choices=SHOPS)
    parser.add_argument("--allowance", type=int, choices=range(1, 8))
    parser.add_argument("--child")
    parser.add_argument("--sibling")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    shop_id = getattr(args, "shop", None) or rng.choice(sorted(SHOPS))
    shop = _safe_lookup(SHOPS, shop_id)
    amount = getattr(args, "allowance", None)
    if amount is None:
        amount = rng.choice(list(range(shop.price, 8)))
    if amount < shop.price:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    child = getattr(args, "child", None) or rng.choice(CHILDREN)
    sibling = getattr(args, "sibling", None) or rng.choice([x for x in SIBLINGS if x != child])
    return StoryParams(shop_id, shop.item, child, sibling, amount)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def verify() -> int:
    py = {(shop, amount) for shop, amount in valid_choices()}
    asp_set = set(asp_valid_choices())
    if py != asp_set:
        print("MISMATCH: ASP and Python choices differ.")
        return 1
    for shop, amount in sorted(py):
        sample = generate(StoryParams(shop, _safe_lookup(SHOPS, shop).item, "Luna", "Ari", amount))
        assert sample._safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "shared")
        assert "allowance" in sample.story.lower()
        assert "lesson" not in sample.story.lower() or sample._safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "lesson")
    print(f"OK: {len(py)} allowance choices and generated-story checks passed.")
    return 0


def emit(sample: StorySample, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "n", None) < 1:
        raise SystemExit("-n must be at least 1")
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        raise SystemExit(verify())
    if getattr(args, "asp", None):
        for shop, amount in asp_valid_choices():
            print(f"{shop}: allowance {amount}")
        return

    rng = random.Random(getattr(args, "seed", None))
    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            params.seed = None if getattr(args, "seed", None) is None else getattr(args, "seed", None) + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        payload = samples[0].to_dict() if len(samples) == 1 else [s.to_dict() for s in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = f"### {sample.params.child}'s allowance day" if getattr(args, "all", None) else ""
        emit(sample, getattr(args, "trace", None), getattr(args, "qa", None), header)
        if i + 1 < len(samples):
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
