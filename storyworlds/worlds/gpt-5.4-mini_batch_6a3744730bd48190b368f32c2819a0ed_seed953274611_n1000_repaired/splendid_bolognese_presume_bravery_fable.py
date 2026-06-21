#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/splendid_bolognese_presume_bravery_fable.py
============================================================================

A small fable-like storyworld about a young animal or child who tries to cook
a splendid bolognese, presumes bravery, makes a mess, and learns a better kind
of courage by asking for help and finishing the meal safely.

Seed words: splendid, bolognese, presume
Feature: Bravery
Style: Fable
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
BRAVERY_INIT = 6.0
FABLE_MORAL = "bravery means asking for help when a task grows too big"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen", "fox"}
        male = {"boy", "father", "dad", "man", "rooster", "dog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    vessel: str
    hot: bool = False
    messy: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: str
    safe: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_boil_over(world: World) -> list[str]:
    out: list[str] = []
    pot = world.get("sauce")
    if pot.meters["boiling"] < THRESHOLD:
        return out
    sig = ("boil_over",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pot.meters["spilled"] += 1
    world.get("kitchen").meters["mess"] += 1
    world.get("hero").memes["alarm"] += 1
    out.append("__spill__")
    return out


def _r_smoke(world: World) -> list[str]:
    out: list[str] = []
    if world.get("sauce").meters["spilled"] < THRESHOLD:
        return out
    sig = ("smoke",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("hero").memes["fear"] += 1
    world.get("mentor").memes["concern"] += 1
    out.append("A hot smell drifted through the kitchen.")
    return out


CAUSAL_RULES = [Rule("boil_over", "physical", _r_boil_over), Rule("smoke", "social", _r_smoke)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, r) for p in POTS for r in RESPONSES if RESPONSES[r].sense >= SENSE_MIN]


def outcome_of(params: "StoryParams") -> str:
    resp = RESPONSES[params.response]
    return "saved" if resp.power >= 2 else "scorched"


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("sauce").meters["boiling"] += 1
    propagate(sim, narrate=False)
    return {"spill": sim.get("sauce").meters["spilled"] >= THRESHOLD}


def setup(world: World, hero: Entity, mentor: Entity, pot: Food, tool: Tool) -> None:
    hero.memes["bravery"] = BRAVERY_INIT
    hero.memes["hope"] += 1
    world.say(
        f"In a little village, {hero.id} dreamed of a splendid feast. "
        f"{mentor.id} had promised a bolognese dinner, red with tomatoes and warm with love."
    )
    world.say(
        f"{hero.id} stood by the stove and said, 'I can do this myself.' "
        f"{hero.pronoun().capitalize()} wanted to make the bolognese shine."
    )
    world.say(
        f"The shiny pot held {pot.phrase}, and the little wooden spoon waited beside {tool.phrase}."
    )


def tempt(world: World, hero: Entity) -> None:
    hero.memes["presume"] += 1
    world.say(
        f"{hero.id} took a deep breath and began to presume that brave meant fearless. "
        f"That was the first mistake."
    )


def warn(world: World, mentor: Entity, hero: Entity, pot: Food) -> bool:
    pred = predict(world)
    if not pred["spill"]:
        return False
    world.facts["predicted_spill"] = True
    world.say(
        f"{mentor.id} saw the steam rising and said, "
        f"'Slow hands, little one. A splendid meal needs patient hands.'"
    )
    return True


def cook(world: World, hero: Entity, pot: Food) -> None:
    pot.meters["boiling"] += 1
    world.say(
        f"{hero.id} stirred faster and faster. The sauce bubbled up in the pot and began to climb."
    )
    propagate(world, narrate=True)


def ask_help(world: World, mentor: Entity, hero: Entity, response: Response, pot: Food) -> None:
    pot.meters["boiling"] = 0.0
    pot.meters["spilled"] = 0.0
    world.get("kitchen").meters["mess"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1
    mentor.memes["pride"] += 1
    world.say(
        f"Then {hero.id} did the bravest thing of all: {hero.pronoun()} called for help. "
        f"{mentor.id} came at once and {response.text}."
    )
    world.say(
        f"Together they saved the bolognese, and the kitchen smelled splendid again."
    )


def finish(world: World, hero: Entity, mentor: Entity, pot: Food) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"At last, {hero.id} served the bolognese in a deep bowl. "
        f"{mentor.id} smiled, and the family ate together while the steam curled like a happy ribbon."
    )
    world.say(
        f"The little fable ended with a simple lesson: {FABLE_MORAL}."
    )


def tell(
    name: str = "Pip",
    hero_type: str = "boy",
    mentor_name: str = "Aunt May",
    mentor_type: str = "woman",
    response: Response | None = None,
) -> World:
    world = World()
    hero = world.add(Entity(id=name, kind="character", type=hero_type, role="hero", traits=["bold"]))
    mentor = world.add(Entity(id=mentor_name, kind="character", type=mentor_type, role="mentor"))
    world.add(Entity(id="kitchen", type="room", label="the kitchen"))
    pot = Food(id="sauce", label="bolognese", phrase="a splendid bolognese sauce", vessel="pot", hot=True)
    tool = Tool(id="spoon", label="wooden spoon", phrase="a wooden spoon", helps="stir")
    setup(world, hero, mentor, pot, tool)
    world.para()
    tempt(world, hero)
    warn(world, mentor, hero, pot)
    world.para()
    cook(world, hero, pot)
    world.para()
    response = response or RESPONSES["ladle"]
    ask_help(world, mentor, hero, response, pot)
    finish(world, hero, mentor, pot)
    world.facts.update(hero=hero, mentor=mentor, pot=pot, response=response, outcome="saved")
    return world


@dataclass
class StoryParams:
    name: str
    hero_type: str
    mentor_name: str
    mentor_type: str
    response: str
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


NAMES = ["Pip", "Mina", "Toby", "Luna", "Nell", "Otto"]
HERO_TYPES = ["boy", "girl"]
MENTOR_NAMES = ["Aunt May", "Uncle Will", "Grandma Rose", "Grandpa Eli"]
MENTOR_TYPES = ["woman", "man"]
SENSE_MIN = 2

POTS = {"plain": "plain", "splendid": "splendid"}

RESPONSES = {
    "ladle": Response("ladle", 3, 3, "grabbed a ladle and stirred the sauce back down", "tried to stir, but the sauce kept climbing", "put the sauce back in the pot with a ladle"),
    "lid": Response("lid", 3, 2, "set the lid on top and turned the heat low", "set a lid on, but it was already too late", "covered the pot with a lid"),
    "move": Response("move", 2, 2, "moved the pot to the back burner and lowered the flame", "moved too slowly to stop the spill", "moved the pot and lowered the flame"),
    "water": Response("water", 1, 1, "poured water in and made a bigger splash", "poured water in, but it only made a bigger mess", "poured water in"),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like story world about splendid bolognese and brave, sensible help.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--mentor-name", choices=MENTOR_NAMES)
    ap.add_argument("--mentor-type", choices=MENTOR_TYPES)
    ap.add_argument("--response", choices=RESPONSES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    response = args.response or rng.choice(sorted(k for k in RESPONSES if RESPONSES[k].sense >= SENSE_MIN))
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        hero_type=args.hero_type or rng.choice(HERO_TYPES),
        mentor_name=args.mentor_name or rng.choice(MENTOR_NAMES),
        mentor_type=args.mentor_type or rng.choice(MENTOR_TYPES),
        response=response,
        seed=None,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable for a young child that includes the words "splendid", "bolognese", and "presume".',
        f"Tell a story where {f['hero'].id} presumes bravery while cooking a splendid bolognese, then learns to ask for help.",
        f"Write a gentle fable about a splendid bolognese dinner and the kind of bravery that keeps everyone safe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, mentor = f["hero"], f["mentor"]
    qa = [
        ("Who is the story about?", f"It is about {hero.id}, who wants to make a splendid bolognese. {mentor.id} helps guide the day."),
        ("What did the hero presume?", f"{hero.id} presumed that bravery meant doing everything alone. That was not quite right, because the task was bigger than one pair of hands."),
        ("How did the story end?", f"It ended safely, with the bolognese served in a bowl and everyone eating together. The hero learned that brave children can ask for help."),
    ]
    if f.get("predicted_spill"):
        qa.append(("Why did the mentor warn the hero?", f"{mentor.id} saw the sauce boiling up and knew it could spill out of the pot. A hot spill would make a mess in the kitchen, so {mentor.id} asked for slow, careful hands."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is bolognese?", "Bolognese is a tomato-and-meat sauce often served over pasta. It is cooked warm and stirred carefully."),
        ("What does splendid mean?", "Splendid means very wonderful or grand. People use it when something feels especially nice or impressive."),
        ("What does presume mean?", "To presume means to think something is true without checking first. A person may presume too much when they are hurrying."),
        ("What is bravery?", "Bravery means doing a hard thing even when you feel nervous. It can also mean asking for help when that is the wiser choice."),
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
spill :- boiling(sauce), not handled.
saved :- asked_help, response_ok.
outcome(saved) :- saved.
outcome(scorched) :- not saved.
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("response", rid) for rid in RESPONSES]
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show response/1."))
    return sorted(r for (r,) in asp.atoms(model, "response"))


def asp_verify() -> int:
    rc = 0
    if set(asp_sensible()) != {r for r in RESPONSES if RESPONSES[r].sense >= SENSE_MIN}:
        rc = 1
        print("MISMATCH: sensible responses differ.")
    try:
        s = generate(resolve_params(argparse.Namespace(name=None, hero_type=None, mentor_name=None, mentor_type=None, response=None), random.Random(777)))
        _ = s.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError("The chosen response is too unwise for this fable.")
    world = tell(
        name=params.name,
        hero_type=params.hero_type,
        mentor_name=params.mentor_name,
        mentor_type=params.mentor_type,
        response=RESPONSES[params.response],
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


CURATED = [
    StoryParams(name="Pip", hero_type="boy", mentor_name="Aunt May", mentor_type="woman", response="ladle", seed=1),
    StoryParams(name="Mina", hero_type="girl", mentor_name="Grandma Rose", mentor_type="woman", response="lid", seed=2),
    StoryParams(name="Toby", hero_type="boy", mentor_name="Uncle Will", mentor_type="man", response="move", seed=3),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show response/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(", ".join(asp_sensible()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
