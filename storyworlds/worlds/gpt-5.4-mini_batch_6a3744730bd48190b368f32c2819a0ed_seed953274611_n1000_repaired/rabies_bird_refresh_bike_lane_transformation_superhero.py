#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rabies_bird_refresh_bike_lane_transformation_superhero.py
==========================================================================================

A tiny standalone storyworld built from the seed words:
rabies, bird, refresh

Premise:
- A child superhero-in-training is in a bike lane.
- A strange bird is spotted acting sick, so the child must not touch it.
- A grown-up response keeps everyone safe.
- A simple refresh beat restores the hero's energy and leads to a transformation into
  a full superhero moment.

This file follows the Storyweavers storyworld contract:
- self-contained stdlib script
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    sick: bool = False
    transformable: bool = False
    brings_refresh: bool = False
    safe_to_approach: bool = True

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Setting:
    id: str
    place: str
    detail: str
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
class Bird:
    id: str
    name: str
    phrase: str
    sound: str
    wobble: str
    rash: str
    risk_word: str
    sick: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Transformation:
    id: str
    outfit: str
    change: str
    title: str
    flourish: str
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
class Refresh:
    id: str
    drink: str
    snack: str
    action: str
    glow: str
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


def _r_fear(world: World) -> list[str]:
    out = []
    if world.get("bird").meters["alarm"] >= THRESHOLD and ("fear", "hero") not in world.fired:
        world.fired.add(("fear", "hero"))
        world.get("hero").memes["worry"] += 1
        out.append("__quiet__")
    return out


def _r_transform(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    refresh = world.get("refresh")
    if hero.meters["refreshed"] < THRESHOLD:
        return out
    sig = ("transform", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["heroic"] += 1
    hero.memes["confidence"] += 1
    if refresh.brings_refresh:
        out.append("__transform__")
    return out


CAUSAL_RULES = [Rule("fear", "social", _r_fear), Rule("transform", "social", _r_transform)]


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


def bird_is_risky(bird: Bird) -> bool:
    return bird.sick


def reasonable_response(resp: Response) -> bool:
    return resp.sense >= 2


def predict(world: World, refresh: Refresh, resp: Response) -> dict:
    sim = world.copy()
    sim.get("hero").meters["refreshed"] += 1
    sim.get("bird").meters["alarm"] += 1
    propagate(sim, narrate=False)
    return {
        "transforms": sim.get("hero").meters["heroic"] >= THRESHOLD,
        "worry": sim.get("hero").memes["worry"],
        "works": resp.power >= 1,
    }


def intro(world: World, hero: Entity, guide: Entity, setting: Setting, bird: Bird) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"On a bright afternoon in {setting.place}, {hero.id} was patrolling the bike lane "
        f"like a tiny superhero. {setting.detail}"
    )
    world.say(
        f"Then {hero.id} spotted {bird.phrase} near the curb. {bird.sound} it went, "
        f"and it {bird.wobble} in a way that made the whole lane feel wrong."
    )
    world.say(
        f'"{bird.name} looks sick," said {guide.id}. "If a bird might have {bird.risk_word}, '
        f"we do not touch it. We call a grown-up right away."'
    )


def temptation(world: World, hero: Entity, bird: Bird, refresh: Refresh) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} wanted to help at once, but {bird.phrase} kept backing away. "
        f'Then {hero.id} noticed a cool {refresh.drink} and a {refresh.snack} in the hero bag.'
    )
    world.say(
        f'"First we refresh," {hero.id} said, and took a careful sip. '
        f"The little pause made the lane feel calmer."
    )


def alert(world: World, guide: Entity, hero: Entity, bird: Bird) -> None:
    bird.meters["alarm"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{guide.id} waved from a safe distance and called for help. "
        f"{hero.id} stood back, just like a true superhero would."
    )
    world.say(
        f'"Stay on the sidewalk, keep the bike lane clear, and let the animal helper come," '
        f"said {guide.id}."
    )


def do_refresh(world: World, hero: Entity, refresh: Refresh) -> None:
    hero.meters["refreshed"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"{hero.id} drank {refresh.drink}, ate {refresh.snack}, and felt the {refresh.glow} in {refresh.action}."
    )


def transform(world: World, hero: Entity, form: Transformation) -> None:
    hero.meters["heroic"] += 1
    hero.memes["confidence"] += 2
    world.say(
        f"Then {hero.id} pulled on {form.outfit}. With one brave spin, {hero.id} made {form.change}."
    )
    world.say(
        f'"Now I am {form.title}!" {hero.id} said, and {form.flourish}.'
    )


def ending(world: World, hero: Entity, bird: Bird, guide: Entity, form: Transformation) -> None:
    world.say(
        f"By the time help arrived, the bird was still safely in the bike lane edge, "
        f"and {guide.id} had already kept everyone back."
    )
    world.say(
        f"{hero.id} stood tall in {form.outfit}, feeling {form.title} strong, while the bird "
        f"was carried away by the right grown-up."
    )
    world.say(
        f"The bike lane was calm again, and the fresh, bright hero image stayed in {hero.id}'s mind."
    )


def tell(setting: Setting, bird: Bird, form: Transformation, refresh: Refresh, response: Response,
         hero_name: str = "Maya", hero_gender: str = "girl",
         guide_name: str = "Coach Ray", guide_gender: str = "man") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_gender, role="guide"))
    bird_ent = world.add(Entity(id="bird", kind="thing", type="bird", label=bird.name, sick=bird.sick))
    world.add(Entity(id="refresh", kind="thing", type="refresh", brings_refresh=True))
    world.facts["bird"] = bird
    world.facts["setting"] = setting
    world.facts["form"] = form
    world.facts["refresh_cfg"] = refresh
    world.facts["response"] = response

    intro(world, hero, guide, setting, bird)
    world.para()
    temptation(world, hero, bird, refresh)
    alert(world, guide, hero, bird)
    world.para()
    do_refresh(world, hero, refresh)
    transform(world, hero, form)
    ending(world, hero, bird, guide, form)
    world.facts.update(
        hero=hero, guide=guide, bird_ent=bird_ent,
        transformed=hero.meters["heroic"] >= THRESHOLD,
        refreshed=hero.meters["refreshed"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "bike_lane": Setting(
        id="bike_lane",
        place="the bike lane",
        detail="The painted stripe was bright, and bikes hummed past like quick blue bees.",
        tags={"bike_lane", "street"},
    ),
}

BIRDS = {
    "pigeon": Bird(
        id="pigeon",
        name="a pigeon",
        phrase="a gray pigeon",
        sound="Coo-coo",
        wobble="staggered",
        rash="odd feathers",
        risk_word="rabies",
        sick=True,
        tags={"bird", "rabies"},
    ),
    "sparrow": Bird(
        id="sparrow",
        name="a sparrow",
        phrase="a little sparrow",
        sound="Chirp-chirp",
        wobble="fluttered too low",
        rash="fever",
        risk_word="rabies",
        sick=True,
        tags={"bird", "rabies"},
    ),
}

TRANSFORMS = {
    "superhero": Transformation(
        id="superhero",
        outfit="a red cape and a shiny helmet",
        change="the cape snap and the helmet gleam",
        title="Bike Lane Hero",
        flourish="raised the cape like a flag",
        tags={"transformation", "superhero"},
    ),
    "shield": Transformation(
        id="shield",
        outfit="a bright shield vest and yellow gloves",
        change="the vest catch the sunlight",
        title="Lane Guardian",
        flourish="held up both hands like a signal",
        tags={"transformation", "superhero"},
    ),
}

REFRESHES = {
    "water": Refresh(
        id="water",
        drink="a cold water bottle",
        snack="an apple slice",
        action="the brain wake up",
        glow="refresh",
        tags={"refresh"},
    ),
    "juice": Refresh(
        id="juice",
        drink="a berry juice box",
        snack="a small cracker",
        action="the courage come back",
        glow="refresh",
        tags={"refresh"},
    ),
}

RESPONSES = {
    "call_help": Response(
        id="call_help",
        sense=3,
        power=3,
        text="called animal help and kept the bird space",
        fail="called for help, but the bird had already gone too far",
        qa_text="called animal help and stayed back safely",
        tags={"help"},
    ),
    "back_away": Response(
        id="back_away",
        sense=3,
        power=2,
        text="backed away and blocked the lane",
        fail="backed away, but the lane was still too busy",
        qa_text="backed away and kept the lane clear",
        tags={"help"},
    ),
    "touch_bird": Response(
        id="touch_bird",
        sense=1,
        power=0,
        text="reached for the bird",
        fail="reached for the bird and made the trouble worse",
        qa_text="reached for the bird",
        tags={"unsafe"},
    ),
}

@dataclass
class StoryParams:
    setting: str
    bird: str
    transformation: str
    refresh: str
    response: str
    hero_name: str
    hero_gender: str
    guide_name: str
    guide_gender: str
    seed: Optional[int] = None
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


CURATED = [
    StoryParams(
        setting="bike_lane",
        bird="pigeon",
        transformation="superhero",
        refresh="water",
        response="call_help",
        hero_name="Maya",
        hero_gender="girl",
        guide_name="Coach Ray",
        guide_gender="man",
        seed=None,
    ),
    StoryParams(
        setting="bike_lane",
        bird="sparrow",
        transformation="shield",
        refresh="juice",
        response="back_away",
        hero_name="Nico",
        hero_gender="boy",
        guide_name="Aunt Jo",
        guide_gender="woman",
        seed=None,
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for bid, bird in BIRDS.items():
            for tid, form in TRANSFORMS.items():
                if bird_is_risky(bird) and "superhero" in form.tags:
                    combos.append((sid, bid, tid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a 3-to-5-year-old in {f["setting"].place} that includes the words "rabies", "bird", and "refresh".',
        f"Tell a story where {f['hero'].id} sees a sick bird in the bike lane, does not touch it, refreshes first, and transforms into a superhero.",
        f"Write a safe, child-friendly transformation story set in a bike lane where a bird seems sick and a hero calls for help.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    guide: Entity = f["guide"]
    bird: Bird = f["bird"]
    form: Transformation = f["form"]
    refresh: Refresh = f["refresh_cfg"]
    items = [
        QAItem(
            question="Where does the story happen?",
            answer="It happens in the bike lane, where the painted line and passing bikes make the scene feel fast and bright.",
        ),
        QAItem(
            question="Why did the hero stay away from the bird?",
            answer=f"{hero.id} stayed back because the bird looked sick and might have rabies. That meant the safest choice was to call a grown-up instead of touching it.",
        ),
        QAItem(
            question=f"What did {hero.id} do to get ready?",
            answer=f"{hero.id} refreshed with {refresh.drink} and {refresh.snack}, then put on {form.outfit}. That helped {hero.id} feel steady enough to act like a superhero.",
        ),
    ]
    if f.get("transformed"):
        items.append(
            QAItem(
                question=f"How did {hero.id} transform?",
                answer=f"{hero.id} transformed by putting on {form.outfit} and making {form.change}. After that, {hero.id} became {form.title}, a superhero ready to protect the lane safely.",
            )
        )
    items.append(
        QAItem(
            question=f"Who helped keep the bird safe?",
            answer=f"{guide.id} helped by keeping everyone back and calling for the right grown-up help. That way the bird could be cared for without anyone getting too close.",
        )
    )
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is rabies?",
            answer="Rabies is a very serious sickness that can affect animals and people. If a bird or other animal seems sick, a grown-up should handle it.",
        ),
        QAItem(
            question="What should you do if you see a sick bird?",
            answer="Stay away from it and tell a grown-up right away. A grown-up can call for help and keep everyone safe.",
        ),
        QAItem(
            question="What does refresh mean?",
            answer="To refresh means to get new energy again, like with water, rest, or a snack. It helps you feel ready to do the next thing.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
        if e.sick:
            bits.append("sick=True")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, bird: Bird) -> str:
    if not bird.sick:
        return "(No story: the bird does not create a rabies concern, so the scene has no real tension.)"
    return "(No story: this world expects a sick bird in the bike lane so the hero can stay safe, refresh, and transform.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    if r.sense < 2:
        return "(Refusing response 'touch_bird': it is not a safe choice for a child story.)"
    return "(No story: response not available.)"


def outcome_of(params: StoryParams) -> str:
    return "transformed" if params.response in RESPONSES else "unknown"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A superhero storyworld in a bike lane with rabies, bird, refresh, and transformation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--bird", choices=BIRDS)
    ap.add_argument("--transformation", choices=TRANSFORMS)
    ap.add_argument("--refresh", choices=REFRESHES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--guide-name")
    ap.add_argument("--guide-gender", choices=["woman", "man", "girl", "boy"])
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
    if args.bird and not bird_is_risky(BIRDS[args.bird]):
        raise StoryError(explain_rejection(SETTINGS[args.setting or "bike_lane"], BIRDS[args.bird]))
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError(explain_response(args.response))

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.bird is None or c[1] == args.bird)
              and (args.transformation is None or c[2] == args.transformation)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, bird, transformation = rng.choice(sorted(combos))
    refresh = args.refresh or rng.choice(sorted(REFRESHES))
    response = args.response or rng.choice(["call_help", "back_away"])
    hero_name = args.hero_name or rng.choice(["Maya", "Nico", "Ari", "Lena", "Jules"])
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    guide_name = args.guide_name or rng.choice(["Coach Ray", "Aunt Jo", "Ms. Z"])
    guide_gender = args.guide_gender or rng.choice(["woman", "man"])
    return StoryParams(
        setting=setting,
        bird=bird,
        transformation=transformation,
        refresh=refresh,
        response=response,
        hero_name=hero_name,
        hero_gender=hero_gender,
        guide_name=guide_name,
        guide_gender=guide_gender,
    )


def generate(params: StoryParams) -> StorySample:
    for key in ("setting", "bird", "transformation", "refresh", "response"):
        if not hasattr(params, key):
            raise StoryError(f"Missing required StoryParams field: {key}")
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.bird not in BIRDS:
        raise StoryError(f"Unknown bird: {params.bird}")
    if params.transformation not in TRANSFORMS:
        raise StoryError(f"Unknown transformation: {params.transformation}")
    if params.refresh not in REFRESHES:
        raise StoryError(f"Unknown refresh: {params.refresh}")
    if params.response not in RESPONSES:
        raise StoryError(f"Unknown response: {params.response}")

    world = tell(
        SETTINGS[params.setting],
        BIRDS[params.bird],
        TRANSFORMS[params.transformation],
        REFRESHES[params.refresh],
        RESPONSES[params.response],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        guide_name=params.guide_name,
        guide_gender=params.guide_gender,
    )
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid, bird in BIRDS.items():
        lines.append(asp.fact("bird", bid))
        if bird.sick:
            lines.append(asp.fact("sick", bid))
    for tid in TRANSFORMS:
        lines.append(asp.fact("transformation", tid))
    for rid, rr in REFRESHES.items():
        lines.append(asp.fact("refresh", rid))
        lines.append(asp.fact("refresh_boost", rid, 1))
    for rid, rr in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, rr.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,B,T) :- setting(S), bird(B), sick(B), transformation(T).
safe_response(R) :- response(R), sense(R,S), sense_min(M), S >= M.
outcome(transformed) :- valid(_,_,_), safe_response(_).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_safe_responses() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show safe_response/1."))
    return sorted(r for (r,) in asp.atoms(model, "safe_response"))


def asp_verify() -> int:
    rc = 0
    try:
        python_set = set(valid_combos())
        clingo_set = set(asp_valid_combos())
        if python_set == clingo_set:
            print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
        else:
            rc = 1
            print("MISMATCH in valid_combos()")
        safe = set(asp_safe_responses())
        py_safe = {rid for rid, rr in RESPONSES.items() if rr.sense >= 2}
        if safe == py_safe:
            print("OK: safe response parity matches.")
        else:
            rc = 1
            print("MISMATCH in response parity")
        sample = generate(CURATED[0])
        print(f"OK: smoke story length {len(sample.story)} characters.")
    except Exception as exc:
        print(f"VERIFY FAILED: {exc}")
        return 1
    return rc


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for bid, bird in BIRDS.items():
            for tid in TRANSFORMS:
                if bird_is_risky(bird):
                    combos.append((sid, bid, tid))
    return combos


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show safe_response/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

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
