#!/usr/bin/env python3
"""
A standalone storyworld script for a tiny mythic domain: wealth, a push, a bucket,
and a happy ending.

A short source tale used to build the world model:
---
Long ago, in a sunlit village by a wide river, there lived a poor but kind child
named Mira. The village well had a stone bucket tied to a rope, and every family
shared it. Mira dreamed of wealth not just for herself, but for everyone who had
to wait for water.

One morning, a proud rich man rolled in with gold bracelets and a heavy cart. He
wanted the well bucket for himself and pushed Mira aside to reach it first.
But the rope slipped, the bucket swung hard, and the rich man's cart tipped into
the mud. The villagers gasped.

Mira did not laugh. She pushed the cart back upright, helped lift the bucket,
and asked for the water to be shared. The rich man grew ashamed. He gave grain,
coin, and a shiny clasp for the rope. The village filled its jars, and Mira's
kindness won her more honor than any treasure. In the end, everyone had enough,
and the well rang with grateful laughter.

Causal state updates:
---
    push with unfair intent   -> target.memes["shame"] += 1, actor.memes["pride"] += 1
    bucket slips/tips         -> bucket.meters["tilt"] += 1, bucket.meters["mud"] += 1
    bucket shared fairly      -> villagers.memes["relief"] += 1, actor.memes["generosity"] += 1
    gift of wealth            -> village.meters["wealth"] += amount, actor.memes["honor"] += 1
    fair repair               -> tension clears; ending becomes happy and communal
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

WORLD_NAME = "mythic_wealth_push_bucket"



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
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bucket: object | None = None
    hero: object | None = None
    rival: object | None = None
    wealth: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "queen": {"subject": "she", "object": "her", "possessive": "her"},
            "king": {"subject": "he", "object": "him", "possessive": "his"},
        }
        if self.type in mapping:
            return mapping[self.type][case]
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
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    rival_name: str
    rival_type: str
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


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    world: object | None = None
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
        import copy
        return World(
            place=self.place,
            entities=copy.deepcopy(self.entities),
            paragraphs=[[]],
            facts=dict(self.facts),
            fired=set(self.fired),
        )
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
    ap = argparse.ArgumentParser(description="Mythic wealth/push/bucket story world.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", "--n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


PLACES = {
    "well_village": "the village well",
    "river_crossing": "the river crossing",
    "hill_town": "the hill town",
}

HEROES = {
    "mira": ("Mira", "queen"),
    "orin": ("Orin", "king"),
    "sela": ("Sela", "queen"),
}

RIVALS = {
    "lord": ("Lord Bram", "king"),
    "lady": ("Lady Venn", "queen"),
}

CURATED = [
    StoryParams(place="well_village", hero_name="Mira", hero_type="queen", rival_name="Lord Bram", rival_type="king"),
    StoryParams(place="river_crossing", hero_name="Sela", hero_type="queen", rival_name="Lady Venn", rival_type="queen"),
]


def invalid_reason(place: str) -> str:
    return f"(No story: the mythic bucket tale needs a place with a shared well or crossing, not {place!r}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    if place not in PLACES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_key = rng.choice(list(HEROES))
    rival_key = rng.choice(list(RIVALS))
    hero_name, hero_type = _safe_lookup(HEROES, hero_key)
    rival_name, rival_type = _safe_lookup(RIVALS, rival_key)
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, rival_name=rival_name, rival_type=rival_type)


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    lines.append(asp.fact("theme", "wealth"))
    lines.append(asp.fact("theme", "push"))
    lines.append(asp.fact("theme", "bucket"))
    lines.append(asp.fact("style", "myth"))
    lines.append(asp.fact("ending", "happy"))
    lines.append(asp.fact("supports", "shared_well"))
    lines.append(asp.fact("supports", "repair"))
    return "\n".join(lines)


ASP_RULES = r"""
eligible(P) :- place(P), supports(shared_well), supports(repair), theme(wealth), theme(push), theme(bucket), style(myth), ending(happy).
#show eligible/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show eligible/1."))
    got = set(asp.atoms(model, "eligible"))
    want = {("well_village",), ("river_crossing",), ("hill_town",)}
    if got == want:
        print(f"OK: ASP gate matches {len(want)} eligible places.")
        return 0
    print("MISMATCH:")
    print("  asp:", sorted(got))
    print("  py :", sorted(want))
    return 1


def generate_world(params: StoryParams) -> World:
    world = World(place=_safe_lookup(PLACES, params.place))
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    rival = world.add(Entity(id="rival", kind="character", type=params.rival_type, label=params.rival_name))
    bucket = world.add(Entity(id="bucket", type="bucket", label="stone bucket", phrase="a stone bucket from the shared well"))
    wealth = world.add(Entity(id="wealth", type="treasure", label="wealth", phrase="grain, coin, and honor"))

    hero.memes["hope"] = 1
    rival.memes["pride"] = 1
    bucket.meters["ready"] = 1
    world.facts.update(hero=hero, rival=rival, bucket=bucket, wealth=wealth)

    world.say(f"Long ago, at {world.place}, {hero.label} was a kind {hero.type} who wished for wealth for everyone.")
    world.say(f"At the same place stood {rival.label}, proud and impatient beside the shared bucket.")

    world.para()
    world.say(f"One morning, {rival.label} tried to take the bucket first and pushed {hero.label} aside.")
    rival.memes["pride"] += 1
    hero.memes["hurt"] += 1
    bucket.meters["tilt"] = 1
    bucket.meters["mud"] = 1
    rival.memes["shame"] = 1
    world.say(f"The bucket swung, the rope jerked, and the cart tipped into the mud.")

    world.para()
    world.say(f"But {hero.label} did not answer with anger.")
    world.say(f"{hero.label} pushed the cart upright, steadied the bucket, and asked for water to be shared fairly.")
    hero.memes["mercy"] = 1
    rival.memes["shame"] += 1
    rival.memes["remorse"] = 1

    world.para()
    world.say(f"Then {rival.label} bowed their head and gave grain, coin, and a bright clasp for the rope.")
    wealth.meters["value"] = 3
    hero.memes["honor"] = 1
    world.say(f"The village filled its jars, the well worked again, and laughter rose over the stones.")
    world.say(f"In the end, {hero.label} gained more honor than any treasure, and everyone had enough.")
    world.facts["happy"] = True
    return world


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    rival = _safe_fact(world, world.facts, "rival")
    bucket = _safe_fact(world, world.facts, "bucket")
    qa = [
        QAItem(
            question=f"Who was the story about at {world.place}?",
            answer=f"It was about {hero.label}, a kind {hero.type} who wanted wealth for everyone.",
        ),
        QAItem(
            question=f"What did {rival.label} do to the bucket?",
            answer=f"{rival.label} pushed the bucket first, and it swung so hard that the cart tipped into the mud.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily: the bucket was shared, the village got water, and everyone had enough.",
        ),
        QAItem(
            question=f"What did {hero.label} do after the push?",
            answer=f"{hero.label} pushed the cart upright and asked for the water to be shared fairly.",
        ),
    ]
    if world.facts.get("happy"):
        qa.append(QAItem(
            question=f"Why was the ending happy instead of sad?",
            answer=f"It was happy because the rival gave gifts, the bucket was fixed for the village, and the conflict turned into sharing.",
        ))
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is wealth?",
            answer="Wealth means having useful things like food, coin, grain, or other riches that help people live well.",
        ),
        QAItem(
            question="What does it mean to push something?",
            answer="To push something means to press it with your hands or body so it moves away from you.",
        ),
        QAItem(
            question="What is a bucket for?",
            answer="A bucket is a container used to carry water, sand, or other things from one place to another.",
        ),
    ]


def prompts(world: World) -> list[str]:
    return [
        f"Write a short myth about wealth, a push, and a bucket at {world.place} that ends happily.",
        f"Tell a child-friendly legend in which a kind hero stops a greedy push and shares the bucket fairly.",
        f"Write a small myth where a bucket and a little wealth change a village for the better.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show eligible/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show eligible/1."))
        print(asp.atoms(model, "eligible"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
