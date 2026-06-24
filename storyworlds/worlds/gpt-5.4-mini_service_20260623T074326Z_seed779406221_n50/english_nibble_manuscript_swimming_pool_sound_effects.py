#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074326Z_seed779406221_n50/english_nibble_manuscript_swimming_pool_sound_effects.py
==============================================================================================================

A standalone bedtime-story world about a swimming pool, a careful child,
a nibble of trouble, and a manuscript that needs to stay dry. The world uses
sound effects, repetition, and a cautionary turn with a gentle ending.

Seed words woven into the domain:
- english
- nibble
- manuscript

Initial source-tale idea:
---
At the swimming pool, Mina brought an english manuscript to read quietly by the
water. A small mouse named Nib nibble-nibbled the corner of the pages while the
children splashed. "Nibble, nibble!" went the mouse. "Careful, careful!" said
Mina, because the manuscript was precious and the pool deck was wet. When a
splash threatened the pages, Mina called for help, dried the book, and put it
high on a chair. In the end, the manuscript stayed safe, the pool stayed calm,
and everyone learned to keep paper away from splashes.
---

The story model tracks:
- physical meters: wetness, splash, dampness, distance, dryness
- emotional memes: worry, relief, pride, calm, caution
- a sound-effect beat, a cautionary warning, repetition, and resolution
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)
    book: object | None = None
    child: object | None = None
    deck: object | None = None
    helper: object | None = None
    pool: object | None = None
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

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    setting: str = "swimming pool"
    child_name: str = "Mina"
    helper_name: str = "Theo"
    book_title: str = "english manuscript"
    sound_effect: str = "splash"
    caution_phrase: str = "Careful, careful"
    repetition: str = "nibble, nibble"
    seed: Optional[int] = None
    CURATED: list = field(default_factory=list)
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    w: object | None = None
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.facts = copy.deepcopy(self.facts)
        w.paragraphs = [[]]
        return w
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def _wetness(world: World, amount: float) -> None:
    book = world.get("book")
    deck = world.get("deck")
    pool = world.get("pool")
    book.meters["damp"] = book.meters.get("damp", 0) + amount
    deck.meters["wet"] = deck.meters.get("wet", 0) + amount
    pool.meters["splash"] = pool.meters.get("splash", 0) + amount


def _dry(world: World) -> None:
    book = world.get("book")
    book.meters["damp"] = 0
    book.meters["dry"] = 1
    world.get("child").memes["relief"] += 1


def _sound(world: World, effect: str) -> None:
    world.say(effect.upper() + "!")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about a swimming pool, caution, and a manuscript.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--setting", choices=["swimming pool"], default="swimming pool")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        setting="swimming pool",
        child_name=rng.choice(["Mina", "Nora", "Lily", "Iris", "Pia"]),
        helper_name=rng.choice(["Theo", "Ben", "Noah", "Eli", "Jules"]),
        book_title="english manuscript",
        sound_effect=rng.choice(["splash", "plop", "kerplunk"]),
        caution_phrase=rng.choice(["Careful, careful", "Slowly, slowly", "Gently, gently"]),
        repetition=rng.choice(["nibble, nibble", "tiptoe, tiptoe", "pat, pat"]),
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(question=f"What was {f['child']} reading by the {f['setting']}?", answer=f"{f['child']} was reading the english manuscript by the swimming pool."),
        QAItem(question=f"What warning did {f['child']} say when the pages got near water?", answer=f"{f['child']} said, \"{f['caution']},\" because the manuscript needed to stay dry."),
        QAItem(question=f"What sound did the little mouse make near the manuscript?", answer=f"The mouse went \"{f['repeat']}\" while nibbling the corner of the pages."),
        QAItem(question=f"How did the story end?", answer="The manuscript stayed safe and dry, and everyone learned to keep paper away from splashes."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="Why should a manuscript stay away from the pool?", answer="Paper gets damaged by water, so a manuscript should stay dry and away from splashes."),
        QAItem(question="What should you do with a wet book?", answer="Move it to a dry place and let a grown-up help protect it from more water."),
        QAItem(question="What does a splash sound like?", answer="A splash is a sudden water sound, like when water jumps out of the pool."),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a bedtime story set at a {f['setting']} about an english manuscript that must stay dry.",
        f"Tell a gentle cautionary story where a child says \"{f['caution']}\" and keeps a manuscript safe from water.",
        f"Write a story with repetition and sound effects, including \"{f['repeat']}\" and a poolside \"{f['sound']}\".",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", label=params.child_name, role="child"))
    helper = world.add(Entity(id=params.helper_name, kind="character", label=params.helper_name, role="helper"))
    book = world.add(Entity(id="book", kind="thing", label=params.book_title))
    pool = world.add(Entity(id="pool", kind="thing", label=params.setting))
    deck = world.add(Entity(id="deck", kind="thing", label="pool deck"))

    child.memes["curiosity"] = 1
    child.memes["caution"] = 1
    helper.memes["calm"] = 1

    world.say(
        f"At the {params.setting}, {child.id} sat with an english manuscript and tried to read in a quiet, bedtime way."
    )
    world.say(
        f"Nearby, a tiny mouse made a funny little song: \"{params.repetition}! {params.repetition}!\""
    )
    world.say(
        f"Then came a happy, wet {params.sound_effect} from the water, and everyone looked up at once."
    )

    world.para()
    world.say(
        f"{child.id} lifted the manuscript away from the edge. \"{params.caution_phrase},\" {child.id} whispered, because paper and water do not mix."
    )
    world.say(
        f"{helper.id} nodded and helped carry it to a high chair."
    )

    _sound(world, params.sound_effect)
    _wetness(world, 1)
    if deck.meters.get("wet", 0) >= THRESHOLD:
        world.say(
            f"The pool deck stayed slippery, but the manuscript rose above the splash and stayed dry."
        )
    _dry(world)
    child.memes["worry"] += 1
    child.memes["relief"] += 1
    helper.memes["pride"] += 1

    world.para()
    world.say(
        f"In the end, the english manuscript rested safely on the chair, dry as a feather, while the pool shimmered softly in the evening light."
    )
    world.say(
        f"{params.repetition.capitalize()} went the mouse one last time, and the bedtime story ended all calm and warm."
    )

    world.facts.update(
        child=child.id,
        helper=helper.id,
        book=book.label,
        setting=params.setting,
        sound=params.sound_effect,
        repeat=params.repetition,
        caution=params.caution_phrase,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} {e.kind:9} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(swimming_pool).
book(english_manuscript).
safe_if_dry :- book(english_manuscript), not wet_book.
wet_book :- splash_near_book.
story_ok :- safe_if_dry.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "swimming_pool"),
            asp.fact("book", "english_manuscript"),
            asp.fact("feature", "sound_effects"),
            asp.fact("feature", "cautionary"),
            asp.fact("feature", "repetition"),
        ]
    )


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def _lazy_asp():
    import asp
    return asp


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program("", "#show setting/1.\n#show book/1."))
        _ = asp.atoms(model, "setting")
        _ = asp.atoms(model, "book")
        print("OK: ASP twin loads and runs.")
        return 0
    except Exception as exc:
        print(f"ASP verification failed: {exc}")
        return 1


CURATED = [StoryParams()]


def resolve_all(args: argparse.Namespace) -> list[StoryParams]:
    if getattr(args, "all", None):
        return CURATED
    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    return [resolve_params(args, rng) for _ in range(getattr(args, "n", None))]


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
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("", "#show setting/1.\n#show book/1."))
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
        for _ in range(getattr(args, "n", None)):
            params = resolve_params(args, rng)
            params.seed = rng.randrange(2**31)
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
