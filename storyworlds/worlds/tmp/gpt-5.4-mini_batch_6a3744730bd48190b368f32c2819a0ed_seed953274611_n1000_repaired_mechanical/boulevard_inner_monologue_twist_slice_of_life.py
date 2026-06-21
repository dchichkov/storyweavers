#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/boulevard_inner_monologue_twist_slice_of_life.py
=================================================================================

A standalone storyworld for a small slice-of-life boulevard tale with an inner
monologue beat and a gentle twist. The domain is deliberately tiny: one child or
young teen goes along a boulevard for an ordinary errand, worries quietly, then
discovers the situation means something kinder or more surprising than they
first thought.

The story is state-driven:
- physical meters: walking, tiredness, hunger, wetness, warmth
- emotional memes: worry, hope, relief, delight, embarrassment
- the "twist" is not a random gimmick; it emerges from a later reveal in the
  world state (a mistaken assumption or a small hidden kindness)

Run it:
    python storyworlds/worlds/gpt-5.4-mini/boulevard_inner_monologue_twist_slice_of_life.py
    python storyworlds/worlds/gpt-5.4-mini/boulevard_inner_monologue_twist_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4-mini/boulevard_inner_monologue_twist_slice_of_life.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/boulevard_inner_monologue_twist_slice_of_life.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
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
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    has_bench: bool = False
    has_tree: bool = False
    has_cafe: bool = False
    has_bus_stop: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Errand:
    id: str
    label: str
    goal: str
    reveal: str
    twist_kind: str
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
class Weather:
    id: str
    label: str
    wetness: float = 0.0
    wind: float = 0.0
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.place: Place | None = None
        self.weather: Weather | None = None
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
        c.place = copy.deepcopy(self.place)
        c.weather = copy.deepcopy(self.weather)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class StoryParams:
    boulevard: str
    errand: str
    weather: str
    name: str
    gender: str
    companion: str
    companion_gender: str
    age: int = 10
    seed: Optional[int] = None
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


BOULEVARDS = {
    "sunny": Place(id="sunny", label="the boulevard", has_bench=True, has_tree=True, has_cafe=True),
    "evening": Place(id="evening", label="the boulevard", has_bench=True, has_tree=False, has_cafe=True, has_bus_stop=True),
    "rainy": Place(id="rainy", label="the boulevard", has_bench=False, has_tree=True, has_cafe=True, has_bus_stop=True),
}

WEATHERS = {
    "clear": Weather(id="clear", label="clear and bright", wetness=0.0, wind=0.1),
    "breezy": Weather(id="breezy", label="breezy", wetness=0.0, wind=0.6),
    "rain": Weather(id="rain", label="rain-speckled", wetness=0.7, wind=0.4),
}

ERRANDS = {
    "bread": Errand(id="bread", label="buy bread", goal="a warm loaf from the café", reveal="the loaf was already paid for", twist_kind="kindness", tags={"cafe", "kindness"}),
    "book": Errand(id="book", label="return a book", goal="the little library basket by the café", reveal="the librarian had slipped a bookmark inside", twist_kind="kindness", tags={"library", "kindness"}),
    "plant": Errand(id="plant", label="pick up a plant", goal="the corner shop with the green awning", reveal="the shopkeeper had wrapped it in paper with a smiley face", twist_kind="kindness", tags={"shop", "kindness"}),
    "note": Errand(id="note", label="deliver a note", goal="the mailbox near the bus stop", reveal="the note was a thank-you card for the child", twist_kind="surprise", tags={"bus_stop", "surprise"}),
}

GIRL_NAMES = ["Mina", "Lia", "Nora", "Ivy", "Zoe", "Ava"]
BOY_NAMES = ["Owen", "Finn", "Leo", "Ben", "Milo", "Theo"]


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for b in BOULEVARDS:
        for e in ERRANDS:
            for w in WEATHERS:
                out.append((b, e, w))
    return out


def boulevard_prefix(place: Place) -> str:
    return f"Along {place.label}"


def tell(place: Place, errand: Errand, weather: Weather, child: Entity, helper: Entity) -> World:
    world = World()
    world.place = copy.deepcopy(place)
    world.weather = copy.deepcopy(weather)
    world.add(child)
    world.add(helper)

    child.memes["worry"] += 1
    helper.memes["calm"] += 1
    child.meters["walking"] += 1
    world.say(
        f"{boulevard_prefix(place)}, {child.id} walked with {helper.id} under a sky that felt {weather.label}. "
        f"{child.id} was on a small errand: {errand.goal}."
    )
    world.say(
        f'In {child.pronoun("possessive")} head, the worry kept whispering, '
        f'"What if I forget? What if I look silly? What if I walk all this way for nothing?"'
    )
    if place.has_bench:
        world.say(
            f"A bench sat beside the path, and {child.id} slowed down to look at it like it might have advice."
        )
    if weather.wetness > 0:
        child.meters["wetness"] += 1
        helper.say if False else None
        world.say(
            f"The air left a few damp spots on {child.id}'s sleeves, which made the errand feel even more important."
        )

    world.para()
    child.memes["hope"] += 1
    world.say(
        f"{helper.id} pointed toward the {errand.goal} and said the errand would probably be easy. "
        f"{child.id} tried to believe it."
    )
    world.say(
        f'Inside {child.id}\'s head, another little voice answered, "Maybe this is just a normal day. '
        f'Normal days can still go wrong."'
    )

    world.para()
    world.say(
        f"At the café and the little stop along the boulevard, {child.id} found the place at last."
    )
    child.meters["walking"] += 1
    if errand.id == "bread":
        child.meters["hunger"] += 1
    if errand.id == "book":
        child.memes["embarrassment"] += 1
    world.say(
        f"{child.id} reached for the {errand.label}, expecting a tiny problem or a tired face."
    )
    child.memes["surprise"] += 1
    world.say(
        f"Then came the twist: {errand.reveal}."
    )
    helper.memes["delight"] += 1
    child.memes["relief"] += 1
    world.say(
        f"{child.id} blinked, and the worry in {child.id}'s chest loosened all at once. "
        f"It turned out the boulevard had been kinder than the fear in {child.id}'s head."
    )
    world.say(
        f"On the walk back, {child.id} carried the errand home and noticed the shop windows shining softly, "
        f"as if they had been waiting to be understood."
    )

    world.facts.update(
        child=child,
        helper=helper,
        place=place,
        weather=weather,
        errand=errand,
        twist=errand.reveal,
        worried=child.memes["worry"] >= THRESHOLD,
        surprised=child.memes["surprise"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    errand = f["errand"]
    place = f["place"]
    return [
        f'Write a slice-of-life story set on a boulevard where {child.id} quietly worries about an ordinary errand, then gets a kind surprise.',
        f"Tell a story about {child.id} walking along the boulevard for {errand.goal}, with a little inner monologue and a twist at the end.",
        f'Write a gentle story that includes the word "boulevard" and ends with {child.id} realizing the day was kinder than expected.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    errand: Errand = f["errand"]
    place: Place = f["place"]
    weather: Weather = f["weather"]
    return [
        QAItem(
            question="What was the child doing on the boulevard?",
            answer=f"{child.id} was walking along the boulevard to {errand.label}. It started as an ordinary errand, but the child kept thinking about it nervously."
        ),
        QAItem(
            question="What did the child keep thinking about?",
            answer=f"{child.id} kept worrying about forgetting something and looking silly. Those thoughts made the walk feel heavier than it really was."
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {errand.reveal}. What first felt like a problem turned out to be a kind surprise waiting at the end of the errand."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{child.id} went home with the errand finished and felt relieved. The boulevard ended up feeling calm and friendly instead of scary."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a boulevard?",
            answer="A boulevard is a wide street, often with sidewalks, trees, and places to stop along the way. People walk there for errands, outings, and everyday life."
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private voice inside a character's head. It shows what they are thinking without saying it out loud."
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a reveal that changes what the reader thought was happening. It can make an ordinary moment feel new or surprising."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story Q&A ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World Q&A ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    if world.place:
        lines.append(f"place={world.place.label} attrs={{'bench': {world.place.has_bench}, 'tree': {world.place.has_tree}, 'cafe': {world.place.has_cafe}, 'bus_stop': {world.place.has_bus_stop}}}")
    if world.weather:
        lines.append(f"weather={world.weather.label}")
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
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
twist(k) :- errand(k), reveal_kind(k, knd), knd = kind.
worry(C) :- child(C).
relief(C) :- child(C), twist(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in BOULEVARDS.items():
        lines.append(asp.fact("boulevard", pid))
        if p.has_bench:
            lines.append(asp.fact("has_bench", pid))
        if p.has_tree:
            lines.append(asp.fact("has_tree", pid))
        if p.has_cafe:
            lines.append(asp.fact("has_cafe", pid))
        if p.has_bus_stop:
            lines.append(asp.fact("has_bus_stop", pid))
    for wid, w in WEATHERS.items():
        lines.append(asp.fact("weather", wid))
    for eid, e in ERRANDS.items():
        lines.append(asp.fact("errand", eid))
        lines.append(asp.fact("reveal_kind", eid, e.twist_kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    try:
        m = asp.one_model(asp_program("#show twist/1."))
        _ = asp.atoms(m, "twist")
    except Exception as exc:
        print(f"ASP smoke test failed: {exc}")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(boulevard=None, errand=None, weather=None, name=None, gender=None, companion=None, companion_gender=None), random.Random(1)))
        _ = sample.story
    except Exception as exc:
        print(f"Story generation smoke test failed: {exc}")
        return 1
    if set(valid_combos()):
        print(f"OK: verify passed with {len(valid_combos())} combos.")
        return 0
    print("No valid combos.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life boulevard storyworld with inner monologue and a small twist.")
    ap.add_argument("--boulevard", choices=BOULEVARDS)
    ap.add_argument("--errand", choices=ERRANDS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion")
    ap.add_argument("--companion-gender", dest="companion_gender", choices=["girl", "boy"])
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
    boulevard = args.boulevard or rng.choice(list(BOULEVARDS))
    errand = args.errand or rng.choice(list(ERRANDS))
    weather = args.weather or rng.choice(list(WEATHERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _pick_name(rng, gender)
    companion_gender = args.companion_gender or ("boy" if gender == "girl" else "girl")
    companion = args.companion or _pick_name(rng, companion_gender)
    if boulevard not in BOULEVARDS or errand not in ERRANDS or weather not in WEATHERS:
        raise StoryError("invalid parameters")
    return StoryParams(boulevard=boulevard, errand=errand, weather=weather, name=name, gender=gender, companion=companion, companion_gender=companion_gender)


def generate(params: StoryParams) -> StorySample:
    place = BOULEVARDS.get(params.boulevard)
    errand = ERRANDS.get(params.errand)
    weather = WEATHERS.get(params.weather)
    if not place or not errand or not weather:
        raise StoryError("invalid params")
    child = Entity(id=params.name, kind="character", type=params.gender, role="child")
    helper = Entity(id=params.companion, kind="character", type=params.companion_gender, role="companion")
    world = tell(place, errand, weather, child, helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q.question, answer=q.answer) for q in story_qa(world)],
        world_qa=[QAItem(question=q.question, answer=q.answer) for q in world_qa(world)],
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


def valid_story_params() -> list[StoryParams]:
    out = []
    for b, e, w in valid_combos()[:6]:
        out.append(StoryParams(boulevard=b, errand=e, weather=w, name="Mina", gender="girl", companion="Owen", companion_gender="boy"))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show twist/1.\n#show worry/1.\n#show relief/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for t in asp_valid_combos():
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in valid_story_params()]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 25):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
