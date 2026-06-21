#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/egg_weather_dapper_cautionary_slice_of_life.py
==============================================================================

A small slice-of-life story world about a child, a careful grown-up, an egg,
and weather that can spoil a neat plan.

The world keeps a tiny simulated state:
- physical meters: wetness, wobble, crack, neatness
- emotional memes: pride, worry, relief, delight

Premise:
A child wants to go out looking dapper with an egg to deliver, but the weather
might ruin the outing. A cautionary adult notices the risk, suggests a safer
plan, and the ending shows what changed.

This script supports the shared storyworld contract:
- StoryParams
- build_parser
- resolve_params
- generate
- emit
- main
- --qa, --json, --asp, --verify, --show-asp, --trace, --all, -n, --seed
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
DEFAULT_CHILDREN = ["Mina", "Owen", "Iris", "Theo", "June", "Pia", "Evan", "Nia"]
DEFAULT_ADULTS = ["Mom", "Dad", "Aunt June", "Uncle Ben"]
CLOTHES = ["dapper coat", "tidy scarf", "polished shoes", "smart cap"]
WEATHER_KEYS = ["bright", "breezy", "drizzly", "windy", "rainy"]
CARRY_KEYS = ["basket", "paper bag", "egg carton", "small tin"]
DELIVERY_KEYS = ["to the neighbor", "to grandma", "to the corner baker", "to the porch next door"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
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
class Weather:
    id: str
    sky: str
    wind: str
    wet: bool
    gust: int
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
class Item:
    id: str
    label: str
    fragile: bool = False
    edible: bool = False
    neat: bool = False
    carries_egg: bool = False
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
class StoryParams:
    weather: str
    carrier: str
    container: str
    outfit: str
    destination: str
    response: str
    child: str
    child_gender: str
    adult: str
    adult_gender: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_wet(world: World) -> list[str]:
    out = []
    weather = world.facts.get("weather")
    child = world.entities.get("child")
    if not weather or not child:
        return out
    if weather.wet and ("wet" not in child.meters or child.meters["wet"] < THRESHOLD):
        sig = ("wet", weather.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["wet"] = child.meters.get("wet", 0.0) + 1
            out.append("__wet__")
    return out


def _r_egg_smudge(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    egg = world.entities.get("egg")
    if not child or not egg:
        return out
    if child.meters.get("wet", 0.0) >= THRESHOLD and egg.meters.get("safe", 0.0) < THRESHOLD:
        sig = ("smudge",)
        if sig not in world.fired:
            world.fired.add(sig)
            egg.meters["wobble"] = egg.meters.get("wobble", 0.0) + 1
            out.append("__wobble__")
    return out


def _r_crack(world: World) -> list[str]:
    out = []
    egg = world.entities.get("egg")
    if not egg:
        return out
    if egg.meters.get("wobble", 0.0) >= THRESHOLD and egg.meters.get("crack", 0.0) < THRESHOLD:
        sig = ("crack",)
        if sig not in world.fired:
            world.fired.add(sig)
            egg.meters["crack"] = 1.0
            out.append("__crack__")
    return out


CAUSAL_RULES = [
    Rule("wet", "physical", _r_wet),
    Rule("egg_smudge", "physical", _r_egg_smudge),
    Rule("crack", "physical", _r_crack),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def weather_map() -> dict[str, Weather]:
    return {
        "bright": Weather("bright", "clear", "gentle", False, 0, {"dry"}),
        "breezy": Weather("breezy", "bright", "light wind", False, 1, {"dry", "wind"}),
        "drizzly": Weather("drizzly", "gray drizzle", "soft wind", True, 1, {"wet"}),
        "windy": Weather("windy", "gray sky", "strong wind", False, 2, {"wind"}),
        "rainy": Weather("rainy", "dark rain", "hard wind", True, 2, {"wet", "wind"}),
    }


def item_map() -> dict[str, Item]:
    return {
        "basket": Item("basket", "basket", fragile=False, carries_egg=True, tags={"carry"}),
        "paper_bag": Item("paper_bag", "paper bag", fragile=True, carries_egg=True, tags={"carry"}),
        "egg_carton": Item("egg_carton", "egg carton", fragile=False, carries_egg=True, tags={"carry"}),
        "small_tin": Item("small_tin", "small tin", fragile=False, carries_egg=False, tags={"carry"}),
        "dapper_coat": Item("dapper_coat", "dapper coat", neat=True, tags={"dapper"}),
        "tidy_scarf": Item("tidy_scarf", "tidy scarf", neat=True, tags={"dapper"}),
        "polished_shoes": Item("polished_shoes", "polished shoes", neat=True, tags={"dapper"}),
        "smart_cap": Item("smart_cap", "smart cap", neat=True, tags={"dapper"}),
    }


def reasonable(carrier: str, weather: str, response: str) -> bool:
    wm = weather_map()[weather]
    im = item_map()[carrier]
    if not im.carries_egg:
        return False
    if response == "paper" and wm.wet:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for w in weather_map():
        for c in ["basket", "egg_carton"]:
            for o in ["dapper_coat", "tidy_scarf", "polished_shoes", "smart_cap"]:
                for r in ["wrap", "carton", "wait_out", "go_now"]:
                    if reasonable(c, w, r):
                        out.append((w, c, o, r))
    return out


def best_response() -> str:
    return "wait_out"


def warn_reason(weather: Weather, carrier: Item) -> str:
    if weather.wet and carrier.id == "paper_bag":
        return "A paper bag can give way when it gets wet."
    if weather.gust >= 2 and carrier.id == "basket":
        return "A basket is open, so a strong gust can shake things loose."
    return "The weather could make the egg wobble if they hurry."


def outcome_of(params: StoryParams) -> str:
    if params.response == "wait_out":
        return "safe"
    if params.weather in {"drizzly", "rainy"} and params.carrier == "paper_bag":
        return "oops"
    if params.weather == "windy" and params.carrier == "basket" and params.response != "carton":
        return "oops"
    return "safe"


def asp_facts() -> str:
    import asp
    lines = []
    for wid, w in weather_map().items():
        lines.append(asp.fact("weather", wid))
        if w.wet:
            lines.append(asp.fact("wet_weather", wid))
        if w.gust:
            lines.append(asp.fact("gust", wid, w.gust))
    for iid, item in item_map().items():
        lines.append(asp.fact("item", iid))
        if item.carries_egg:
            lines.append(asp.fact("carries_egg", iid))
    lines.append(asp.fact("safe_response", "wait_out"))
    lines.append(asp.fact("safe_response", "carton"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(W,C,O,R) :- weather(W), item(C), carries_egg(C), safe_response(R).
unsafe(W,C) :- wet_weather(W), C = paper_bag.
unsafe(W,C) :- gust(W,G), G >= 2, C = basket.
good(W,C) :- valid(W,C,_,R), not unsafe(W,C), safe_response(R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life egg-and-weather story world.")
    ap.add_argument("--weather", choices=list(weather_map()))
    ap.add_argument("--carrier", choices=["basket", "paper_bag", "egg_carton"])
    ap.add_argument("--outfit", choices=["dapper_coat", "tidy_scarf", "polished_shoes", "smart_cap"])
    ap.add_argument("--response", choices=["wait_out", "carton", "wrap", "go_now"])
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["woman", "man"])
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
    if args.weather and args.carrier and not reasonable(args.carrier, args.weather, args.response or "wait_out"):
        raise StoryError("That carrier and weather do not make a sensible cautionary story.")
    combos = [c for c in valid_combos()
              if (args.weather is None or c[0] == args.weather)
              and (args.carrier is None or c[1] == args.carrier)
              and (args.outfit is None or c[2] == args.outfit)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    weather, carrier, outfit, response = rng.choice(sorted(combos))
    if args.response:
        response = args.response
    child = args.child or rng.choice(DEFAULT_CHILDREN)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    adult = args.adult or rng.choice(DEFAULT_ADULTS)
    adult_gender = args.adult_gender or rng.choice(["woman", "man"])
    return StoryParams(
        weather=weather,
        carrier=carrier,
        container=response,
        outfit=outfit,
        destination=rng.choice(DELIVERY_KEYS),
        response=response,
        child=child,
        child_gender=child_gender,
        adult=adult,
        adult_gender=adult_gender,
    )


def tell(params: StoryParams) -> World:
    world = World()
    w = weather_map()[params.weather]
    carrier = item_map()[params.carrier]
    outfit = item_map()[params.outfit]
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, label=params.child))
    adult = world.add(Entity(id=params.adult, kind="character", type=params.adult_gender, label=params.adult))
    egg = world.add(Entity(id="egg", kind="thing", type="egg", label="an egg"))
    carrier_ent = world.add(Entity(id="carrier", kind="thing", type="container", label=carrier.label))
    outfit_ent = world.add(Entity(id="outfit", kind="thing", type="clothes", label=outfit.label))
    child.meters["neat"] = 1.0
    child.memes["pride"] = 1.0
    world.facts.update(weather=w, carrier=carrier, outfit=outfit, child=child, adult=adult, egg=egg, carrier_ent=carrier_ent)

    world.say(f"On a {w.sky} morning, {child.id} wanted to look dapper in {outfit.label}.")
    world.say(f"{child.id} picked up {egg.label} and set it into a {carrier.label} for a little errand {params.destination}.")
    world.say(f"The weather was {w.wind}, and the plan felt neat at first.")

    world.para()
    world.say(f"{adult.id} looked outside and frowned a little.")
    world.say(f'"{warn_reason(w, carrier)}" {adult.pronoun()} said. "Let\'s slow down and choose the careful way."')

    if params.response == "wait_out":
        child.memes["worry"] = 1.0
        child.memes["relief"] = 1.0
        world.say(f"{child.id} listened, and the two of them waited by the window until the weather passed.")
        world.para()
        world.say(f"Afterward, {child.id} went out looking dapper, and the egg stayed safe in the {carrier.label}.")
        outcome = "safe"
    else:
        child.memes["pride"] += 1
        child.meters["wet"] = 0.0
        if params.response == "carton":
            world.say(f"{child.id} swapped the egg into an egg carton so it would sit still.")
            egg.meters["safe"] = 1.0
            outcome = "safe"
        elif params.response == "wrap":
            world.say(f"{child.id} wrapped the egg in a napkin, but the weather still made it jostle.")
            child.meters["wet"] = 1.0 if w.wet else 0.0
            egg.meters["wobble"] = 1.0
            propagate(world, narrate=False)
            if egg.meters.get("crack", 0.0) >= THRESHOLD:
                world.para()
                world.say(f"The egg gave a tiny crack, and {child.id} had to stop and clean up the mess.")
                world.say(f"{adult.id} was kind about it, but reminded {child.id} that looking neat should not come before safety.")
                outcome = "oops"
            else:
                world.say(f"It worked, though only just, and {adult.id} said it was better to use a sturdier carrier next time.")
                outcome = "safe"
        else:
            world.say(f"{child.id} hurried anyway, and the weather caught up with the little errand.")
            child.meters["wet"] = 1.0 if w.wet else 0.0
            egg.meters["wobble"] = 1.0
            propagate(world, narrate=False)
            if egg.meters.get("crack", 0.0) >= THRESHOLD:
                world.para()
                world.say(f"The egg cracked in the {carrier.label}, and the dapper outfit did not stay neat for long.")
                world.say(f"{adult.id} helped tidy up and said that a careful choice would have saved time.")
                outcome = "oops"
            else:
                outcome = "safe"

    if outcome == "safe":
        child.memes["relief"] = child.memes.get("relief", 0.0) + 1.0
        world.say(f"In the end, {child.id} was still dapper, the errand stayed calm, and the egg went where it needed to go.")
    world.facts["outcome"] = outcome
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life cautionary story for a young child that includes the words "egg", "weather", and "dapper".',
        f"Tell a gentle story where {f['child'].id} wants to look dapper while carrying an egg, but {f['adult'].id} notices the weather might spoil the plan.",
        f"Write a small everyday story about a child, an egg, and weather that teaches a careful choice without being scary.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    egg = f["egg"]
    carrier = f["carrier"]
    outcome = f["outcome"]
    ans = [
        QAItem(
            question="Why did the adult speak up about the plan?",
            answer=f"{adult.id} spoke up because the weather could make the egg wobble in the {carrier.label}. The adult wanted the errand to stay neat and safe instead of turning into a mess."
        ),
        QAItem(
            question="What did the child want at the beginning of the story?",
            answer=f"{child.id} wanted to look dapper and bring the egg along on a little errand. The outfit mattered to {child.pronoun('object')}, but the weather mattered too."
        ),
    ]
    if outcome == "safe":
        ans.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with the egg still safe and {child.id} still looking dapper. The careful choice let the errand finish calmly."
        ))
    else:
        ans.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with the egg cracking and the child needing help to clean up. The mistake showed why it was wiser to slow down when the weather was risky."
        ))
    return ans


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    q = [
        QAItem("What is an egg?", "An egg is a fragile food with a shell. If you drop or shake it too much, the shell can crack."),
        QAItem("What does dapper mean?", "Dapper means neatly dressed and looking very smart. People often use it for tidy clothes and careful style."),
        QAItem("Why can weather matter on an errand?", "Weather can change the ground, the wind, and how steady you feel. Wet or windy weather can make careful carrying harder."),
    ]
    if f["weather"].wet:
        q.append(QAItem("What is drizzle?", "Drizzle is a light rain made of tiny drops. It can still wet clothes and make things slippery."))
    return q


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(weather="drizzly", carrier="egg_carton", container="carton", outfit="dapper_coat", destination="to the neighbor", response="wait_out", child="Mina", child_gender="girl", adult="Mom", adult_gender="woman"),
    StoryParams(weather="windy", carrier="basket", container="basket", outfit="tidy_scarf", destination="to grandma", response="carton", child="Theo", child_gender="boy", adult="Dad", adult_gender="man"),
    StoryParams(weather="rainy", carrier="paper_bag", container="paper", outfit="smart_cap", destination="to the porch next door", response="wrap", child="Iris", child_gender="girl", adult="Aunt June", adult_gender="woman"),
]


def valid_story_params(params: StoryParams) -> bool:
    return params.weather in weather_map() and params.carrier in {"basket", "paper_bag", "egg_carton"}


def explain_rejection(params: StoryParams) -> str:
    return "That combination does not make a sensible cautionary slice-of-life story."


def generate(params: StoryParams) -> StorySample:
    if not valid_story_params(params):
        raise StoryError(explain_rejection(params))
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def resolve_random_name(rng: random.Random, pool: list[str]) -> str:
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    weather = args.weather or rng.choice(list(weather_map()))
    carrier = args.carrier or rng.choice(["basket", "egg_carton"])
    outfit = args.outfit or rng.choice(["dapper_coat", "tidy_scarf", "polished_shoes", "smart_cap"])
    response = args.response or rng.choice(["wait_out", "carton", "wrap"])
    child = args.child or resolve_random_name(rng, DEFAULT_CHILDREN)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    adult = args.adult or rng.choice(DEFAULT_ADULTS)
    adult_gender = args.adult_gender or rng.choice(["woman", "man"])
    params = StoryParams(
        weather=weather,
        carrier=carrier,
        container=response,
        outfit=outfit,
        destination=rng.choice(DELIVERY_KEYS),
        response=response,
        child=child,
        child_gender=child_gender,
        adult=adult,
        adult_gender=adult_gender,
    )
    if not valid_story_params(params):
        raise StoryError(explain_rejection(params))
    return params


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"FAILED: generate() smoke test crashed: {exc}")
    return rc


def build_asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(build_asp_program("#show valid/4.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(build_asp_program("#show valid/4.\n"))
        print(f"{len(asp.atoms(model, 'valid'))} compatible combinations.")
        for item in sorted(set(asp.atoms(model, "valid"))):
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.child}: {p.weather}, {p.carrier}, {p.outfit} ({p.response})"
        if header:
            print(header)
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
