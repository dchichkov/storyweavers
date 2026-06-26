#!/usr/bin/env python3
"""
storyworlds/worlds/blossom_shorts_surprise_repetition_folk_tale.py
===================================================================

A small folk-tale storyworld about a child, a spring blossom, and a pair of
shorts that matter more than they first seem.

Seed tale:
---
A little child loved to dance in the meadow, where blossoms opened one by one.
One day the child wore favorite shorts with a bright ribbon, but the wind kept
changing the path. A surprise came from the hedgerow, then came again, and again:
a bee, a flutter, a lost ribbon. Each time, the child learned a little more.

The child could have run home, but instead listened to an old village helper.
Together they found the ribbon, tied the shorts snugly, and followed the blossoms
to a gentle ending.

World model:
---
* Physical meters: distance, bloom, wind, worry, comfort, tidy, surprise
* Emotional memes: curiosity, caution, delight, trust, relief, pride

Narrative instruments:
---
* Surprise: a hidden thing appears from the hedgerow, changing the child's plan.
* Repetition: the same small trouble happens more than once, but the answer
  changes on the second and third try.

This script keeps the prose child-facing and concrete, with one small turn and a
clear ending image.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    blossom: object | None = None
    helper: object | None = None
    hero: object | None = None
    shorts: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
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
    place: str = "the meadow"
    season: str = "spring"
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
class StoryParams:
    place: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk-tale story world about blossom paths, shorts, surprise, and repetition."
    )
    ap.add_argument("--place", choices=["meadow", "orchard", "lane"], help="setting place")
    ap.add_argument("--gender", choices=["girl", "boy"], help="hero gender")
    ap.add_argument("--name", help="hero name")
    ap.add_argument("--helper", choices=["grandmother", "old man", "aunt"], help="helper role")
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


PLACES = {
    "meadow": Setting("the meadow"),
    "orchard": Setting("the orchard"),
    "lane": Setting("the village lane"),
}

GIRL_NAMES = ["Mina", "Lina", "Rosa", "Anya", "Ivy", "Sera"]
BOY_NAMES = ["Tomas", "Bram", "Owen", "Niko", "Elias", "Pavel"]
HELPERS = ["grandmother", "old man", "aunt"]


@dataclass
class Plot:
    blossom_count: int = 0
    surprise_seen: int = 0
    ribbon_lost: bool = False
    shorts_tied: bool = False
    returned_home: bool = False
    plot: object | None = None
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


def _narrate_blossom(world: World, hero: Entity, count: int) -> None:
    if count == 1:
        world.say(
            f"In the spring {world.setting.place}, {hero.id} watched a single blossom open like a tiny lamp."
        )
    else:
        world.say(
            f"Then another blossom opened, and then another, until the path seemed stitched with pale flowers."
        )


def _surprise(world: World, hero: Entity, helper: Entity, plot: Plot) -> None:
    plot.surprise_seen += 1
    world.say(
        f"From the hedgerow came a surprise: a bright ribbon caught on a thorn, blinking in the wind."
    )
    hero.memes["curiosity"] += 1
    hero.meters["worry"] += 1
    world.facts["surprise"] = "ribbon in the hedgerow"


def _lose_ribbon(world: World, hero: Entity, shorts: Entity, plot: Plot) -> None:
    plot.ribbon_lost = True
    shorts.meters["tidy"] -= 1
    hero.meters["worry"] += 1
    world.say(
        f"{hero.id} tugged at {hero.pronoun('possessive')} shorts, and the ribbon slipped free and fluttered away."
    )


def _helper_advice(world: World, hero: Entity, helper: Entity, plot: Plot) -> None:
    helper.memes["trust"] += 1
    hero.memes["trust"] += 1
    world.say(
        f"{helper.id.capitalize()} said, 'One knot is good, but two knots are better when the wind is tricky.'"
    )
    world.say(
        f"{hero.id} listened, because folk tales teach that slow ears often save the day."
    )


def _fix(world: World, hero: Entity, shorts: Entity, helper: Entity, plot: Plot) -> None:
    plot.shorts_tied = True
    hero.meters["worry"] = max(0.0, hero.meters.get("worry", 0.0) - 1.0)
    hero.memes["relief"] += 1
    shorts.meters["tidy"] += 1
    world.say(
        f"Together they tied the shorts snugly with a fresh knot, then a second knot, and the ribbon stayed put."
    )


def tell_story(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id=params.helper, kind="character", type="woman" if params.helper == "grandmother" else "man" if params.helper == "old man" else "woman", label=params.helper))
    shorts = world.add(Entity(id="shorts", type="shorts", label="shorts", phrase="favorite shorts with a bright ribbon", owner=hero.id, worn_by=hero.id, plural=True))
    blossom = world.add(Entity(id="blossom", type="blossom", label="blossom", phrase="spring blossom", owner=None))

    plot = Plot()

    hero.memes["curiosity"] = 1
    hero.memes["delight"] = 1
    hero.meters["comfort"] = 1
    shorts.meters["tidy"] = 1
    world.say(
        f"{hero.id} loved the spring and wore {hero.pronoun('possessive')} favorite shorts with a bright ribbon."
    )
    world.say(
        f"{hero.id} followed the blossom path because blossoms always seemed to know where the good stories were hiding."
    )

    world.para()
    _narrate_blossom(world, hero, 1)
    _surprise(world, hero, helper, plot)
    _lose_ribbon(world, hero, shorts, plot)

    world.para()
    _narrate_blossom(world, hero, 2)
    _helper_advice(world, hero, helper, plot)
    _surprise(world, hero, helper, plot)
    _fix(world, hero, shorts, helper, plot)

    world.para()
    _narrate_blossom(world, hero, 3)
    world.say(
        f"At last the ribbon held fast, the shorts sat neat, and {hero.id} walked on under the blossoms without fear of the wind."
    )
    world.say(
        f"The surprise had come again and again, but the answer had become stronger each time."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        shorts=shorts,
        blossom=blossom,
        plot=plot,
        setting=world.setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    return [
        'Write a short folk tale for a child about blossom paths, shorts, surprise, and repetition.',
        f"Tell a gentle story where {hero.id} loses a ribbon from {hero.pronoun('possessive')} shorts and {helper.id.capitalize()} helps.",
        "Write a spring story that repeats one small surprise more than once, then ends with a calm walk home.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    shorts: Entity = _safe_fact(world, f, "shorts")
    place = world.setting.place
    return [
        QAItem(
            question=f"What did {hero.id} wear in {place}?",
            answer=f"{hero.id} wore {hero.pronoun('possessive')} favorite shorts with a bright ribbon.",
        ),
        QAItem(
            question=f"What surprise did {hero.id} see from the hedgerow?",
            answer="A bright ribbon had caught on a thorn and blinked in the wind.",
        ),
        QAItem(
            question=f"How did {helper.id} help with the shorts?",
            answer=f"{helper.id.capitalize()} told {hero.id} to make two knots, and that kept the shorts neat and secure.",
        ),
        QAItem(
            question=f"What changed by the end of the tale?",
            answer=f"The shorts stayed tidy, the ribbon stayed tied, and {hero.id} could walk under the blossoms without worry.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a blossom?",
            answer="A blossom is a flower that opens, often in spring on a tree or bush.",
        ),
        QAItem(
            question="What are shorts?",
            answer="Shorts are clothes that cover the body from the waist to the thighs and are nice for warm days.",
        ),
        QAItem(
            question="What does a helper do in a folk tale?",
            answer="A helper gives advice, offers a hand, or shows a safer way when a problem appears.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(sorted(PLACES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(place=place, name=name, gender=gender, helper=helper)


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


ASP_RULES = r"""
place(m meadow). place(m orchard). place(m lane).
feature(surprise). feature(repetition).
theme(folk_tale).

valid_story(P) :- place(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    lines.append(asp.fact("feature", "surprise"))
    lines.append(asp.fact("feature", "repetition"))
    lines.append(asp.fact("theme", "folk_tale"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p,) for p in PLACES}
    asps = set(asp_valid_places())
    if py == asps:
        print(f"OK: ASP matches Python ({len(py)} places).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python only:", sorted(py - asps))
    print("asp only:", sorted(asps - py))
    return 1


CURATED = [
    StoryParams(place="meadow", name="Mina", gender="girl", helper="grandmother"),
    StoryParams(place="orchard", name="Tomas", gender="boy", helper="old man"),
    StoryParams(place="lane", name="Rosa", gender="girl", helper="aunt"),
]


def build_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/1."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = build_from_args(args, random.Random(seed))
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
            header = f"### {p.name} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
