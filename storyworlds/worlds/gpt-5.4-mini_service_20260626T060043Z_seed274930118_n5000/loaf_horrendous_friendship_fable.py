#!/usr/bin/env python3
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    companion: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bread: object | None = None
    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"mouse", "hare", "rabbit", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Setting:
    place: str = "the meadow"
    kindness: str = "quiet"
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
class Loaf:
    label: str
    phrase: str
    slices: int = 6
    warm: bool = True
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
    hero: str
    friend: str
    loaf: str
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
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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


SETTINGS = {
    "meadow": Setting("the meadow", "gentle"),
    "orchard": Setting("the orchard", "bright"),
    "barn": Setting("the barnyard", "busy"),
}

HEROES = {
    "mouse": ("mouse", "small mouse"),
    "hare": ("hare", "quick hare"),
    "rabbit": ("rabbit", "soft rabbit"),
    "bird": ("bird", "little bird"),
}

FRIENDS = {
    "mouse": ("mouse", "steady mouse"),
    "hare": ("hare", "patient hare"),
    "rabbit": ("rabbit", "kind rabbit"),
    "bird": ("bird", "cheerful bird"),
}

LOAVES = {
    "round": Loaf("round loaf", "a warm round loaf"),
    "seeded": Loaf("seeded loaf", "a seeded loaf with a crisp crust"),
    "brown": Loaf("brown loaf", "a brown loaf from the oven"),
}

NAMES = ["Milo", "Pip", "Lena", "Tilda", "Bram", "Nori", "Sage", "Oona"]
TRAITS = ["kind", "careful", "cheerful", "humble", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for hero in HEROES:
            for loaf in LOAVES:
                combos.append((place, hero, loaf))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about friendship and a loaf.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--loaf", choices=LOAVES)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "hero", None) is None or c[1] == getattr(args, "hero", None))
              and (getattr(args, "loaf", None) is None or c[2] == getattr(args, "loaf", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, hero, loaf = rng.choice(list(combos))
    return StoryParams(
        place=place,
        hero=getattr(args, "hero", None) or hero,
        friend=getattr(args, "friend", None) or _safe_lookup(FRIENDS, hero)[0],
        loaf=getattr(args, "loaf", None) or loaf,
        seed=None,
    )


def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero_type = _safe_lookup(HEROES, params.hero)[0]
    friend_type = _safe_lookup(FRIENDS, params.hero)[0]
    hero_name = params.name or random.choice(NAMES)
    friend_name = params.friend_name or random.choice([n for n in NAMES if n != hero_name])
    loaf = _safe_lookup(LOAVES, params.loaf)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    friend = world.add(Entity(id="friend", kind="character", type=friend_type, label=friend_name))
    bread = world.add(Entity(id="loaf", type="loaf", label=loaf.label, phrase=loaf.phrase, owner=hero.id))
    bread.meters["slices"] = float(loaf.slices)
    world.facts.update(hero=hero, friend=friend, loaf=bread, loaf_cfg=loaf, params=params)
    return world


def tell(world: World) -> World:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    loaf: Entity = _safe_fact(world, f, "loaf")
    cfg: Loaf = _safe_fact(world, f, "loaf_cfg")

    world.say(
        f"In {world.setting.place}, {hero.label} and {friend.label} were friends who liked to share a simple meal."
    )
    world.say(
        f"One day they found {cfg.phrase}. Its crust was still warm, and the smell made the little clearing feel kind."
    )
    world.para()
    world.say(
        f"{hero.label} wanted to keep the loaf close, because {hero.pronoun('possessive')} hunger grew fast."
    )
    hero.memes["greed"] = 1.0
    hero.memes["desire"] = 1.0
    world.say(
        f"But {friend.label} asked to tear off a piece, and {hero.label} answered in a horrendous way: {hero.label} hid the loaf behind a root."
    )
    hero.memes["horrendous"] = 1.0
    friend.memes["hurt"] = 1.0
    world.para()
    world.say(
        f"The hiding made a mess of the friendship. A few crumbs fell into the dirt, and the silence felt larger than the loaf."
    )
    loaf.meters["dirty"] = 1.0
    world.say(
        f"Then {hero.label} saw {friend.label}'s face fall. {hero.label} understood that a loaf could fill a belly, but friendship filled a heart."
    )
    hero.memes["regret"] = 1.0
    world.say(
        f"So {hero.label} brought the loaf back, broke it into two fair pieces, and gave one to {friend.label} first."
    )
    hero.memes["greed"] = 0.0
    hero.memes["friendship"] = 1.0
    friend.memes["hurt"] = 0.0
    friend.memes["joy"] = 1.0
    world.say(
        f"They ate together under the open sky, and the horrendous choice was gone, replaced by a smaller, sweeter one."
    )
    world.say(
        f"From that day on, the two friends remembered that a loaf is best when shared, and friendship grows when no one keeps all the bread."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short fable about friendship, a {f['loaf_cfg'].label}, and a horrendous mistake that is repaired by sharing.",
        f"Tell a child-friendly story in a meadow where {f['hero'].label} and {f['friend'].label} learn what friendship means over a loaf of bread.",
        "Write a small moral tale that ends with a shared meal and a kinder heart.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    loaf: Entity = _safe_fact(world, f, "loaf")
    return [
        QAItem(
            question=f"Who were the friends in the story?",
            answer=f"The friends were {hero.label} and {friend.label}. They were the two characters who cared about the loaf and each other.",
        ),
        QAItem(
            question=f"What did they find in {world.setting.place}?",
            answer=f"They found {loaf.phrase}. It was a warm loaf of bread, and it started the problem between the friends.",
        ),
        QAItem(
            question="What was the horrendous mistake?",
            answer=f"The horrendous mistake was that {hero.label} hid the loaf instead of sharing it. That hurt {friend.label}'s feelings.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {hero.label} bringing the loaf back, breaking it into fair pieces, and sharing it with {friend.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a loaf?",
            answer="A loaf is a baked food, usually bread, that people can slice or tear into pieces to eat.",
        ),
        QAItem(
            question="Why is sharing important in friendship?",
            answer="Sharing is important in friendship because friends care about each other, and fair choices help both people feel respected and happy.",
        ),
        QAItem(
            question="What does horrendous mean?",
            answer="Horrendous means very bad or awful.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {e.label} {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for hero in HEROES:
        lines.append(asp.fact("hero", hero))
    for loaf in LOAVES:
        lines.append(asp.fact("loaf", loaf))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,H,L) :- place(P), hero(H), loaf(L).
#show valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(setup_world(params))
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
        for sec, items in [("Prompts", sample.prompts), ("Story QA", sample.story_qa), ("World QA", sample.world_qa)]:
            print(f"== {sec} ==")
            if isinstance(items, list) and items and isinstance(items[0], str):
                for i, p in enumerate(items, 1):
                    print(f"{i}. {p}")
            else:
                for item in items:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for t in asp_valid_combos():
            print(t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for p in [StoryParams(place=pl, hero=h, friend=h, loaf=l) for pl, h, l in valid_combos()[:5]]:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
