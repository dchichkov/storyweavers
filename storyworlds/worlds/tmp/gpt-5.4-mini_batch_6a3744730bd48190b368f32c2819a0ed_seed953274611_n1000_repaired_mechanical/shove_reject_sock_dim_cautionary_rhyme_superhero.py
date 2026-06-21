#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/shove_reject_sock_dim_cautionary_rhyme_superhero.py
===================================================================================

A standalone storyworld for a tiny superhero tale: one child wants to use a
"sock-dim" gadget for a secret mission, the cautious sidekick rejects the plan,
an unsafe shove causes trouble anyway, and a grown-up fixes things with a safer
light.

The style is child-facing superhero adventure, with a cautionary turn and a
light rhyme texture. The story must include the seed words:
- shove
- reject
- sock-dim

The world is small and state-driven:
- typed entities with physical meters and emotional memes
- a simple causal engine that drives the turn and resolution
- a reasonableness gate and inline ASP twin
- three Q&A sets grounded in world state

This script is self-contained except for the shared results / asp helpers.
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
        return self.label or self.id
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
class Gadget:
    id: str
    label: str
    phrase: str
    effect: str
    safe: bool = True
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
class Hazard:
    id: str
    label: str
    phrase: str
    flammable: bool = False
    slippery: bool = False
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
class Aid:
    id: str
    label: str
    phrase: str
    glow: str
    power: int
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    alley = world.entities.get("alley")
    if not alley:
        return out
    for ent in world.characters():
        if ent.meters["dim"] < THRESHOLD:
            continue
        sig = ("slip", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        alley.meters["danger"] += 1
        ent.memes["worry"] += 1
        out.append("__slip__")
    return out


CAUSAL_RULES = [Rule("slip", "physical", _r_slip)]


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


def hazard_at_risk(gadget: Gadget, hazard: Hazard) -> bool:
    return gadget.safe and hazard.flammable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def is_contained(response: Response, hazard: Hazard, delay: int) -> bool:
    return response.power >= hazard_risk(hazard, delay)


def hazard_risk(hazard: Hazard, delay: int) -> int:
    return (2 if hazard.flammable else 1) + delay


def predict(world: World, gadget: Gadget, hazard: Hazard) -> dict:
    sim = world.copy()
    _use_gadget(sim, sim.get("gadget"), hazard, narrate=False)
    return {
        "dimmed": sim.get("alley").meters["dim"] >= THRESHOLD,
        "danger": sim.get("alley").meters["danger"],
    }


def _use_gadget(world: World, gadget_ent: Entity, hazard: Hazard, narrate: bool = True) -> None:
    world.get("alley").meters["dim"] += 1
    world.get("mask").meters["dim"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity, sidekick: Entity, city: str) -> None:
    hero.memes["excitement"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"On a bright afternoon in {city}, {hero.id} and {sidekick.id} became "
        f"superheroes with capes and brave hearts."
    )
    world.say(
        f"{hero.id} twirled the cape. {sidekick.id} grinned. "
        f'"When the night gets tight, we rhyme and shine."'
    )


def mission(world: World, hero: Entity, sidekick: Entity) -> None:
    world.say(
        f"They searched the alley behind the corner shop, where the shadows sat "
        f"like sleepy bats."
    )
    world.say(
        f'"We need the dark to dim," said {hero.id}. "Then we can sneak in and "
        f"save the tin cat!"'
    )


def tempt(world: World, hero: Entity, gadget: Gadget) -> None:
    hero.memes["bold"] += 1
    world.say(
        f'{hero.id} lifted the {gadget.label} and smiled. '
        f'"Sock-dim," {hero.id} said, "makes a room go low and slim."'
    )


def warn(world: World, sidekick: Entity, hero: Entity, gadget: Gadget, hazard: Hazard) -> None:
    sidekick.memes["caution"] += 1
    pred = predict(world, gadget, hazard)
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'{sidekick.id} shook {sidekick.pronoun("possessive")} head. '
        f'"I reject that trick. It may make the alley slick. '
        f"The mask can slip, the boots can skid, and then our rescue gets hid.""
    )


def shove(world: World, hero: Entity, sidekick: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"No time to wait!" {hero.id} cried, and gave a little shove. '
        f"The gadget flashed; the shadows dove."
    )


def accident(world: World, hazard: Hazard) -> None:
    world.get("alley").meters["dim"] += 1
    world.get("mask").meters["dim"] += 1
    propagate(world, narrate=False)
    world.say(
        "The sock-dim beam blinked out with a hum. The alley grew too dim, and "
        "the loose tiles went glum."
    )
    world.say(
        f"Their boots slid on the stones, and the rescue plan felt all wrong."
    )


def alarm(world: World, sidekick: Entity, hero: Entity) -> None:
    sidekick.memes["fear"] += 1
    world.say(
        f'"{hero.id}! Stop!" {sidekick.id} shouted. "The path is slick; we need a light that lasts all night."'
    )


def rescue(world: World, parent: Entity, response: Response, hazard: Hazard) -> None:
    world.get("alley").meters["dim"] = 0
    world.get("mask").meters["dim"] = 0
    body = response.text.replace("{target}", hazard.label)
    world.say(
        f"{parent.label_word.capitalize()} arrived with a steady step and {body}."
    )
    world.say(
        "The dark backed away, the tiles dried fast, and the little heroes stood "
        "safe at last."
    )


def lesson(world: World, parent: Entity, hero: Entity, sidekick: Entity, gadget: Gadget) -> None:
    hero.memes["lesson"] += 1
    sidekick.memes["lesson"] += 1
    world.say(
        f'{parent.label_word.capitalize()} smiled and said, "Brave can be wise, '
        f"and wise can win the prize. A risky shine may look like fun, but safer "
        f"light is second to none.""
    )
    world.say(
        f"{hero.id} and {sidekick.id} nodded in the glow. They promised to choose "
        f"the safer way to go."
    )


def safe_ending(world: World, hero: Entity, sidekick: Entity, aid: Aid) -> None:
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"The next day they brought {aid.phrase}, and it {aid.glow}."
    )
    world.say(
        f"With safe light bright, they saved the tin cat, and the skyline shone like a hero's hat."
    )


def tell(city: str, gadget: Gadget, hazard: Hazard, aid: Aid,
         hero_name: str = "Nova", hero_gender: str = "girl",
         sidekick_name: str = "Pip", sidekick_gender: str = "boy",
         parent_type: str = "mother", response: Response = None) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type=sidekick_gender, role="sidekick"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the captain parent"))
    world.add(Entity(id="alley", type="place", label="the alley"))
    world.add(Entity(id="mask", type="thing", label="the mask"))

    intro(world, hero, sidekick, city)
    mission(world, hero, sidekick)
    world.para()
    tempt(world, hero, gadget)
    warn(world, sidekick, hero, gadget, hazard)
    shove(world, hero, sidekick)
    world.para()
    accident(world, hazard)
    alarm(world, sidekick, hero)
    world.para()
    if response is None:
        response = best_response()
    rescue(world, parent, response, hazard)
    lesson(world, parent, hero, sidekick, gadget)
    world.para()
    safe_ending(world, hero, sidekick, aid)

    world.facts.update(
        hero=hero, sidekick=sidekick, parent=parent, city=city,
        gadget=gadget, hazard=hazard, aid=aid, response=response,
        outcome="contained", ignited=True, resolved=True,
    )
    return world


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


CITYS = ["Skyport", "Bright Harbor", "Metro Gleam"]
GADGETS = {
    "sock-dim": Gadget(
        id="sock-dim",
        label="sock-dim device",
        phrase="the sock-dim device",
        effect="dims the alley",
        safe=True,
        tags={"sock-dim", "dim"},
    ),
    "shadow-visor": Gadget(
        id="shadow-visor",
        label="shadow visor",
        phrase="the shadow visor",
        effect="dims the alley",
        safe=True,
        tags={"dim"},
    ),
}
HAZARDS = {
    "alley-glass": Hazard(
        id="alley-glass",
        label="the glassy alley",
        phrase="the glassy alley",
        flammable=False,
        slippery=True,
        tags={"slip", "dim"},
    )
}
AIDS = {
    "lantern": Aid(
        id="lantern",
        label="lantern",
        phrase="a lantern",
        glow="glowed warm and steady",
        power=3,
        tags={"light"},
    ),
    "bat-flare": Aid(
        id="bat-flare",
        label="bat-flare",
        phrase="a bat-flare",
        glow="beamed bright and bold",
        power=4,
        tags={"light"},
    ),
}

RESPONSES = {
    "steady_lantern": Response(
        id="steady_lantern",
        sense=3,
        power=3,
        text="held up a lantern and shone it over the slick stones until every corner was bright",
        fail="held up a lantern, but the path stayed too dark",
        qa_text="held up a lantern and shone it over the slick stones",
        tags={"light"},
    ),
    "hero_beam": Response(
        id="hero_beam",
        sense=4,
        power=4,
        text="switched on a bat-flare and lit the whole alley like dawn",
        fail="switched on a bat-flare, but the dark still hid the stones",
        qa_text="switched on a bat-flare and lit the whole alley like dawn",
        tags={"light"},
    ),
    "too_weak": Response(
        id="too_weak",
        sense=1,
        power=1,
        text="waved a tiny glow toy that was far too small to help",
        fail="waved a tiny glow toy that was far too small to help",
        qa_text="waved a tiny glow toy",
        tags={"light"},
    ),
}

KNOWLEDGE = {
    "sock-dim": [(
        "What is a sock-dim device?",
        "A sock-dim device is a made-up superhero gadget in this story. It makes things dimmer, so it can be risky in a dark place.",
    )],
    "dim": [(
        "Why is a dim place risky?",
        "A dim place is risky because it is hard to see the ground. People can slip or bump into things when the light is too low.",
    )],
    "light": [(
        "What does a safe light do?",
        "A safe light helps you see without making the area dangerous. It can guide you through the dark without a risky trick.",
    )],
    "slip": [(
        "What should you do if a floor is slippery?",
        "Move slowly and get a grown-up or use a safe light. Slippery ground can make you fall, so careful feet matter.",
    )],
}

KNOWLEDGE_ORDER = ["sock-dim", "dim", "slip", "light"]


@dataclass
class StoryParams:
    city: str
    gadget: str
    hazard: str
    aid: str
    hero_name: str
    hero_gender: str
    sidekick_name: str
    sidekick_gender: str
    parent_type: str
    response: str
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
        city="Skyport",
        gadget="sock-dim",
        hazard="alley-glass",
        aid="lantern",
        hero_name="Nova",
        hero_gender="girl",
        sidekick_name="Pip",
        sidekick_gender="boy",
        parent_type="mother",
        response="steady_lantern",
    ),
    StoryParams(
        city="Bright Harbor",
        gadget="sock-dim",
        hazard="alley-glass",
        aid="bat-flare",
        hero_name="Skye",
        hero_gender="girl",
        sidekick_name="Rex",
        sidekick_gender="boy",
        parent_type="father",
        response="hero_beam",
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for city in CITYS:
        for gadget_id, gadget in GADGETS.items():
            for hazard_id, hazard in HAZARDS.items():
                if hazard_at_risk(gadget, hazard):
                    combos.append((city, gadget_id, hazard_id))
    return combos


def explain_rejection(gadget: Gadget, hazard: Hazard) -> str:
    return (
        f"(No story: {gadget.label} could make a problem, but {hazard.label} is not "
        f"a fitting hazard for this tiny scene. Pick a dim, slippery danger that can "
        f"be fixed by a bright, safer light.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    safe = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < 2). Try: {safe}.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero storyworld: a risky sock-dim gadget, a cautious reject, and a brighter ending."
    )
    ap.add_argument("--city", choices=CITYS)
    ap.add_argument("--gadget", choices=GADGETS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero-name")
    ap.add_argument("--sidekick-name")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.gadget and args.hazard and not hazard_at_risk(GADGETS[args.gadget], HAZARDS[args.hazard]):
        raise StoryError(explain_rejection(GADGETS[args.gadget], HAZARDS[args.hazard]))
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if args.city is None or c[0] == args.city
              and (args.gadget is None or c[1] == args.gadget)
              and (args.hazard is None or c[2] == args.hazard)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    city, gadget, hazard = rng.choice(sorted(combos))
    aid = args.aid or rng.choice(sorted(AIDS))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_name = args.hero_name or rng.choice(["Nova", "Skye", "Piper", "Zuri"])
    sidekick_name = args.sidekick_name or rng.choice(["Pip", "Rex", "Moss", "Tess"])
    parent = args.parent or rng.choice(["mother", "father"])
    hero_gender = "girl" if hero_name in {"Nova", "Skye", "Zuri"} else "boy"
    sidekick_gender = "boy" if sidekick_name in {"Pip", "Rex", "Moss"} else "girl"
    return StoryParams(
        city=city,
        gadget=gadget,
        hazard=hazard,
        aid=aid,
        hero_name=hero_name,
        hero_gender=hero_gender,
        sidekick_name=sidekick_name,
        sidekick_gender=sidekick_gender,
        parent_type=parent,
        response=response,
    )


def tell_story(params: StoryParams) -> World:
    if params.gadget not in GADGETS or params.hazard not in HAZARDS or params.aid not in AIDS or params.response not in RESPONSES:
        raise StoryError("(Invalid StoryParams values.)")
    return tell(
        city=params.city,
        gadget=GADGETS[params.gadget],
        hazard=HAZARDS[params.hazard],
        aid=AIDS[params.aid],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        sidekick_name=params.sidekick_name,
        sidekick_gender=params.sidekick_gender,
        parent_type=params.parent_type,
        response=RESPONSES[params.response],
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly superhero story that includes the words "shove", "reject", and "sock-dim".',
        f"Tell a cautionary superhero story where {f['hero'].id} wants to use a sock-dim gadget, but {f['sidekick'].id} rejects the plan and a grown-up arrives with a safer light.",
        f"Write a rhyming rescue story about a dim alley, a risky shove, and a brighter ending for {f['city']}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    parent = f["parent"]
    gadget = f["gadget"]
    aid = f["aid"]
    response = f["response"]
    qa = [
        ("Who are the story's heroes?",
         f"It is about {hero.id} and {sidekick.id}, two little superheroes with capes and a brave job to do."),
        (f"What did {hero.id} want to use?",
         f"{hero.id} wanted to use the {gadget.label}. It was the sock-dim gadget, and that choice made the alley too dark."),
        (f"What did {sidekick.id} say about that idea?",
         f"{sidekick.id} said reject, because the plan could make the ground slick and hard to see. That warning was the careful part of the story."),
        ("How did the grown-up help?",
         f"{parent.label_word.capitalize()} brought {aid.phrase} and used it to make the alley bright again. The safer light let the heroes finish the rescue without slipping."),
    ]
    if f.get("outcome") == "contained":
        qa.append((
            f"How did {response.qa_text} help?",
            f"{parent.label_word.capitalize()} {response.qa_text}. That was bright enough to beat the dimness and keep the rescue going.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["gadget"].tags) | set(world.facts["aid"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


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


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


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
hazard(F, H) :- gadget(F), hazard(H), safe(F), flammable(H).
valid(C, F, H) :- city(C), hazard(H), gadget(F), hazard_at_risk(F, H).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for c in CITYS:
        lines.append(asp.fact("city", c))
    for gid, g in GADGETS.items():
        lines.append(asp.fact("gadget", gid))
        if g.safe:
            lines.append(asp.fact("safe", gid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if h.flammable:
            lines.append(asp.fact("flammable", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(CURATED[0])
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: story generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def build_samples(args: argparse.Namespace, rng: random.Random) -> list[StorySample]:
    if args.all:
        return [generate(p) for p in CURATED]
    samples: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(50, args.n * 50):
        params = resolve_params(args, random.Random((args.seed or 0) + i))
        params.seed = (args.seed or 0) + i
        sample = generate(params)
        if sample.story in seen:
            i += 1
            continue
        seen.add(sample.story)
        samples.append(sample)
        i += 1
    return samples


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (city, gadget, hazard) combos:")
        for c, g, h in asp_valid_combos():
            print(f"  {c:12} {g:12} {h}")
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples = build_samples(args, rng)
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
