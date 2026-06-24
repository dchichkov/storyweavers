#!/usr/bin/env python3
"""
storyworlds/worlds/hip_addition_inner_monologue_kindness_superhero_story.py
============================================================================

A standalone storyworld for a tiny superhero tale with two seed words:
"hip" and "addition". The world keeps the prose child-facing and state-driven,
with inner monologue and kindness as the main narrative instruments.

Core premise:
- A small hero wants to help in a superhero way.
- The hero has a sore hip, so moving fast is hard.
- A thoughtful addition to the costume and a kind choice change the outcome.

The simulation tracks physical meters and emotional memes on typed entities.
The prose is generated from state changes, not from a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



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
    role: str = ""
    protective: bool = False
    helps_hip: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    tool: object | None = None
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
class City:
    name: str
    crowd: str
    place: str
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
class Aid:
    id: str
    label: str
    phrase: str
    action: str
    helps_hip: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    city: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    aid: str
    seed: Optional[int] = None
    params: object | None = None
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


class World:
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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
        import copy

        clone = World(self.city)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_hip_strain(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters.get("rush", 0.0) < THRESHOLD:
        return out
    if hero.meters.get("hip", 0.0) < THRESHOLD:
        return out
    sig = "hip_strain"
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["slow"] = hero.meters.get("slow", 0.0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    out.append("A little ache made every fast step harder.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.memes.get("kindness", 0.0) < THRESHOLD:
        return out
    sig = "kindness"
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["hope"] = helper.memes.get("hope", 0.0) + 1
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    out.append("Kindness made the plan feel possible.")
    return out


CAUSAL_RULES = [_r_hip_strain, _r_kindness]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(city: City, aid: Aid, hero_name: str, hero_gender: str, helper_name: str, helper_gender: str) -> World:
    world = World(city)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name))
    tool = world.add(Entity(id="aid", label=aid.label, phrase=aid.phrase, protective=True, helps_hip=aid.helps_hip))
    world.facts["aid"] = aid
    world.facts["tool"] = tool

    hero.meters["hip"] = 1.0
    hero.meters["rush"] = 1.0
    hero.memes["duty"] = 1.0
    helper.memes["kindness"] = 1.0

    world.say(
        f"{hero.label} was a small superhero in {city.name}, where the {city.crowd} waited near {city.place}."
    )
    world.say(
        f"{hero.label} had a sore hip, but {hero.pronoun()} still wanted to help right away."
    )
    world.say(
        f"{hero.pronoun().capitalize()} listened to an inner monologue: "
        f'"I want to help, but my hip needs care. I can be brave and kind at the same time."'
    )

    world.para()
    hero.memes["kindness"] += 1
    world.say(
        f"A small problem arrived at {city.place}: a windy spill sent papers and ribbons everywhere."
    )
    world.say(
        f"{helper.label} pointed to the mess and asked for help, not for a race."
    )
    world.say(
        f"{hero.label} took a careful breath and chose kindness over speed."
    )
    propagate(world)

    world.para()
    if aid.helps_hip:
        hero.meters["hip"] = 0.0
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
        world.say(
            f"{helper.label} brought out {aid.phrase}. It was a smart addition to the costume, and it supported the sore hip."
        )
        world.say(
            f"With the addition in place, {hero.label} moved in a gentler way and helped tidy the whole square."
        )
    else:
        hero.memes["worry"] += 1
        world.say(
            f"{helper.label} offered {aid.phrase}, but it was not the right addition for a sore hip."
        )
        world.say(
            f"Still, {hero.label} slowed down, used kind hands, and finished the job without making the ache worse."
        )

    world.para()
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    world.say(
        f"In the end, the square was neat again, the crowd cheered, and {hero.label} smiled at the quiet win."
    )
    world.say(
        f"{hero.label}'s hip felt better because {hero.pronoun()} had chosen a kind plan, and the new addition helped the hero finish like a true superhero."
    )

    world.facts.update(hero=hero, helper=helper, city=city, aid=aid)
    return world


CITIES = {
    "downtown": City(name="downtown", crowd="neighbors", place="the fountain"),
    "harbor": City(name="the harbor", crowd="dock workers", place="the pier"),
    "park": City(name="the park", crowd="families", place="the playground"),
}

AIDS = {
    "hip_pad": Aid(
        id="hip_pad",
        label="a soft hip pad",
        phrase="a soft hip pad",
        action="support the sore hip",
        helps_hip=True,
    ),
    "tool_belt": Aid(
        id="tool_belt",
        label="a tool belt",
        phrase="a tool belt",
        action="carry tools",
        helps_hip=False,
    ),
    "cape_clip": Aid(
        id="cape_clip",
        label="a bright cape clip",
        phrase="a bright cape clip",
        action="keep the cape neat",
        helps_hip=False,
    ),
}

HERO_NAMES = ["Mina", "Leo", "Tess", "Noah", "Pia", "Finn"]
HELPER_NAMES = ["Ari", "June", "Owen", "Sage", "Nia", "Bo"]


def valid_combos() -> list[tuple[str, str]]:
    return [(city, aid) for city in CITIES for aid in AIDS]


@dataclass
class StoryState:
    hero: Entity
    helper: Entity
    aid: Entity
    city: City
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].label
    helper = f["helper"].label
    city = f["city"].name
    aid = f["aid"].phrase
    return [
        f'Write a superhero story for a preschooler about {hero} in {city}, and include the word "hip".',
        f"Tell a gentle hero story where {helper} helps {hero} with kindness and a smart addition to the costume.",
        f'Write a short story where an inner monologue helps a superhero choose a careful, kind way to help.',
        f'Write a story that uses the word "addition" and ends with a child-sized superhero win.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    city = f["city"]
    aid = f["aid"]
    return [
        QAItem(
            question=f"Who is the story about in {city.name}?",
            answer=f"It is about {hero.label}, a small superhero with a sore hip who wants to help in {city.name}.",
        ),
        QAItem(
            question=f"What did {hero.label} think in the inner monologue?",
            answer=(
                f"{hero.label} thought, \"I want to help, but my hip needs care. I can be brave and kind at the same time.\" "
                f"That thought helped {hero.pronoun()} choose a gentle plan."
            ),
        ),
        QAItem(
            question=f"What kind addition helped the hero?",
            answer=(
                f"{aid.phrase} was the kind addition. It supported the sore hip so {hero.label} could move more gently."
            ),
        ),
        QAItem(
            question=f"How did {helper.label} help {hero.label}?",
            answer=(
                f"{helper.label} stayed kind, pointed out the mess, and brought the addition when it was needed. "
                f"That kindness made the work feel safe and possible."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hip?",
            answer="A hip is part of your body near your side and leg. It helps you stand, walk, and sit.",
        ),
        QAItem(
            question="What does addition mean?",
            answer="Addition means something extra that gets added to help or improve a plan, a tool, or a costume.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward someone else.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice in your head when you think to yourself.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.helps_hip:
            bits.append("helps_hip=True")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id}: {e.label} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero_needs_help :- hip_sore(hero).
kind_choice :- kindness(hero).
good_end :- hero_needs_help, kind_choice, addition_helps(tool).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for city in CITIES:
        lines.append(asp.fact("city", city))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        if aid.helps_hip:
            lines.append(asp.fact("addition_helps", aid_id))
    lines.append(asp.fact("hip_sore", "hero"))
    lines.append(asp.fact("kindness", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_end/0."))
    asp_ok = bool(asp.atoms(model, "good_end"))
    py_ok = any(a.helps_hip for a in AIDS.values())
    if asp_ok == py_ok:
        print("OK: ASP parity matches the Python reasonableness gate.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero storyworld with hip, addition, inner monologue, and kindness.")
    ap.add_argument("--city", choices=CITIES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    city = getattr(args, "city", None) or rng.choice(list(CITIES))
    aid = getattr(args, "aid", None) or rng.choice(list(AIDS))
    hero_gender = getattr(args, "hero_gender", None) or rng.choice(["girl", "boy"])
    helper_gender = getattr(args, "helper_gender", None) or rng.choice(["girl", "boy"])
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    helper = getattr(args, "helper", None) or rng.choice([n for n in HELPER_NAMES if n != hero])
    return StoryParams(city=city, hero=hero, hero_gender=hero_gender, helper=helper, helper_gender=helper_gender, aid=aid)


def generate(params: StoryParams) -> StorySample:
    city = _safe_lookup(CITIES, params.city)
    aid = _safe_lookup(AIDS, params.aid)
    world = tell(city, aid, params.hero, params.hero_gender, params.helper, params.helper_gender)
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
        print(asp_program("#show good_end/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is available for parity checking.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for city in CITIES:
            for aid in AIDS:
                params = StoryParams(city=city, hero="Mina", hero_gender="girl", helper="Ari", helper_gender="girl", aid=aid)
                samples.append(generate(params))
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
