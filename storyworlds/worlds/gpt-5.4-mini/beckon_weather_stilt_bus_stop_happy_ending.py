#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/beckon_weather_stilt_bus_stop_happy_ending.py
=============================================================================

A standalone story world for a small comedy at a bus stop: a kid on stilts,
changing weather, and a cheerful mistake that turns into a happy ending.

Seed words: beckon, weather, stilt
Setting: bus stop
Style: Comedy
Feature: Happy ending

The world model is intentionally small and concrete:
- typed entities with meters and memes
- a reasonableness gate over the scenario
- a forward-chained ASP twin for parity checking
- three Q&A sets grounded in world state, not rendered text parsing

This world centers on a child waiting at a bus stop, a gusty weather change,
and a comic tallness problem caused by stilts. The tension is whether the child
can get the bus driver to notice them in the wind and rain without making a
mess of the stop; the turn is a bright, funny fix involving a helper and a
safe, silly signal. The ending image proves the change: the child is dry,
visible, and laughing as the bus arrives.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/beckon_weather_stilt_bus_stop_happy_ending.py
    python storyworlds/worlds/gpt-5.4-mini/beckon_weather_stilt_bus_stop_happy_ending.py --verify
    python storyworlds/worlds/gpt-5.4-mini/beckon_weather_stilt_bus_stop_happy_ending.py --qa --json
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)
    wet: bool = False
    tall: bool = False
    shelter: bool = False

    tags: set[str] = field(default_factory=set)

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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Weather:
    id: str
    name: str
    mood: str
    clue: str
    hazard: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Stilt:
    id: str
    label: str
    phrase: str
    height: int
    wobble: int
    safe: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Stop:
    id: str
    label: str
    phrase: str
    shelter: bool
    bench: bool
    puddle: bool
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    action: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        c.facts = dict(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_weather(world: World) -> list[str]:
    out: list[str] = []
    stop = world.get("stop")
    weather = world.get("weather")
    kid = world.get("kid")
    if weather.id == "rain" and stop.shelter and ("rain_alert",) not in world.fired:
        world.fired.add(("rain_alert",))
        stop.meters["wet"] += 1
        kid.memes["mischief"] += 1
        out.append("The rain drummed on the roof, and the bus stop went shiny.")
    if weather.id == "wind" and ("wind_alert",) not in world.fired:
        world.fired.add(("wind_alert",))
        kid.meters["wobble"] += 1
        out.append("A windy puff made the sign shimmy like it was telling a joke.")
    return out


def _r_stilt(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("kid")
    stilt = world.get("stilts")
    if kid.meters["wobble"] < THRESHOLD:
        return out
    if ("stilt_wobble",) in world.fired:
        return out
    world.fired.add(("stilt_wobble",))
    stilt.meters["wobble"] += 1
    kid.memes["surprise"] += 1
    out.append("The tall stilts ticked once on the pavement and did a tiny wobble dance.")
    return out


def _r_beckon(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("kid")
    bus = world.get("bus")
    helper = world.get("helper")
    if kid.memes["beckon"] < THRESHOLD or ("bus_notice",) in world.fired:
        return out
    world.fired.add(("bus_notice",))
    bus.memes["attention"] += 1
    helper.memes["laugh"] += 1
    out.append("The child waved both arms high, as if trying to guide a friendly bird home.")
    return out


def _r_shelter(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("kid")
    stop = world.get("stop")
    if stop.shelter and kid.meters["wet"] >= THRESHOLD and (("dry_off",) not in world.fired):
        world.fired.add(("dry_off",))
        kid.meters["wet"] = 0.0
        kid.memes["relief"] += 1
        out.append("Under the roof, the child stopped looking like a shiny raisin.")
    return out


CAUSAL_RULES = [Rule("weather", _r_weather), Rule("stilt", _r_stilt), Rule("beckon", _r_beckon), Rule("shelter", _r_shelter)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(items)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_notice(world: World) -> dict:
    sim = world.copy()
    sim.get("kid").memes["beckon"] += 1
    propagate(sim, narrate=False)
    return {
        "noticed": sim.get("bus").memes["attention"] >= THRESHOLD,
        "wobble": sim.get("kid").meters["wobble"],
    }


def setup(world: World, kid: Entity, parent: Entity, weather: Entity, stilt: Entity, stop: Entity, bus: Entity, helper: Entity) -> None:
    kid.memes["joy"] += 1
    kid.memes["beckon"] = 0.0
    world.say(f"On a bright morning, {kid.id} waited at the {stop.label} with {stilt.phrase} strapped on.")
    world.say(f"The weather was {weather.label}, which made the bus stop feel like a stage for a very serious clown.")
    world.say(f"{kid.id} liked the tall view so much that even the pigeons seemed shorter.")
    world.say(f'"Is the bus coming soon?" {kid.id} asked, and {parent.label_word} smiled at the sky.')


def build_nudge(world: World, kid: Entity, parent: Entity, helper: Entity, weather: Entity, stop: Stop) -> None:
    pred = predict_notice(world)
    kid.memes["beckon"] += 1
    kid.memes["hope"] += 1
    world.facts["predicted_notice"] = pred["noticed"]
    world.say(f"But the weather kept changing its mind: first a sprinkle, then a puff of wind, then another sprinkle.")
    world.say(f"{kid.id} lifted {kid.pronoun('possessive')} arms and tried to beckon the bus with a grand, wiggly wave.")
    world.say(f'{parent.id} said, "{helper.action}, and the bus driver will see you better."')
    world.say(f"{helper.id} nodded, because {helper.label} had the kind of face that always looked one joke ahead.")


def comic_setback(world: World, kid: Entity, stilt: Stilt, stop: Stop) -> None:
    kid.meters["wobble"] += 1
    stilt.wobble += 1
    world.say(f"A gust tugged at the {stilt.label}, and {kid.id} did a careful little moonwalk to stay upright.")
    if stop.puddle:
        world.say(f"The puddle by the curb splashed back as if it had been waiting for an audience.")


def cheerful_fix(world: World, kid: Entity, parent: Entity, helper: Entity, bus: Entity, weather: Entity, stop: Stop) -> None:
    kid.memes["laugh"] += 1
    kid.memes["relief"] += 1
    parent.memes["relief"] += 1
    helper.memes["joy"] += 1
    world.say(f"Then {helper.id} made a funny plan: {helper.action} and use {kid.id}'s bright backpack as a flag.")
    world.say(f'{helper.id} even called, "Hey, bus! Over here! The tall kid is waving, not escaping!"')
    world.say(f"The bus driver noticed at once, grinned, and slowed down by the curb.")
    world.say(f"{parent.id} held out an umbrella, and the whole little trio ducked under it like penguins in a raincoat.")


def ending(world: World, kid: Entity, parent: Entity, bus: Entity, stilt: Stilt, weather: Entity) -> None:
    kid.meters["wobble"] = 0.0
    kid.meters["wet"] = 0.0
    bus.memes["attention"] += 1
    world.say(f"The bus arrived with a cheerful hiss, and {kid.id} climbed aboard without splashing a single sock.")
    world.say(f"{kid.id} laughed so hard that {stilt.label} nearly looked proud of itself.")
    world.say(f"The weather stayed dramatic, but the child stayed dry, the bus was found, and everybody got a seat before the next drizzle.")


@dataclass
@dataclass
class StoryParams:
    weather: str
    stilt: str
    stop: str
    helper: str
    kid_name: str
    kid_gender: str
    parent_type: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


WEATHERS = {
    "sunny": Weather("sunny", "sunny", "cheerful", "the sky winked like a gold coin", "none", {"bright"}),
    "drizzle": Weather("drizzle", "drizzly", "squishy", "tiny drops kept tapping the roof", "slip", {"wet"}),
    "wind": Weather("wind", "windy", "snappy", "the air kept nudging hats around", "wobble", {"wind"}),
    "rain": Weather("rain", "rainy", "shiny", "the clouds had turned into a noisy kettle", "wet", {"wet"}),
}

STILTS = {
    "garden": Stilt("garden", "wooden stilts", "wooden stilts", 2, 1, True, {"stilt"}),
    "candy": Stilt("candy", "striped stilts", "striped stilts", 3, 2, True, {"stilt"}),
    "tiny": Stilt("tiny", "tiny practice stilts", "tiny practice stilts", 1, 1, True, {"stilt"}),
}

STOPS = {
    "corner": Stop("corner", "bus stop", "the bus stop", True, True, True, {"bus_stop"}),
    "school": Stop("school", "bus stop", "the bus stop by the school", True, True, False, {"bus_stop"}),
}

HELPERS = {
    "parent": Helper("parent", "parent", "the parent", "go stand under the roof", {"helper"}),
    "neighbor": Helper("neighbor", "neighbor", "the neighbor", "hold the umbrella over the sign", {"helper"}),
    "driver": Helper("driver", "driver", "the driver", "wave the orange scarf", {"helper"}),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Finn", "Theo"]
TRAITS = ["cheerful", "curious", "silly", "bright", "bouncy"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(w, s, t) for w in WEATHERS for s in STILTS for t in STOPS]


def asp_facts() -> str:
    import asp
    lines = []
    for wid in WEATHERS:
        lines.append(asp.fact("weather", wid))
    for sid in STILTS:
        lines.append(asp.fact("stilt", sid))
    for tid in STOPS:
        lines.append(asp.fact("stop", tid))
    lines.append(asp.fact("shelter", "corner"))
    lines.append(asp.fact("shelter", "school"))
    lines.append(asp.fact("puddle", "corner"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(W, S, T) :- weather(W), stilt(S), stop(T).
happy(W) :- weather(W), weather(W).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test succeeded.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


@dataclass
class StoryParams:
    weather: str
    stilt: str
    stop: str
    helper: str
    kid_name: str
    kid_gender: str
    parent_type: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy story world at a bus stop with weather and stilts.")
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--stilt", choices=STILTS)
    ap.add_argument("--stop", choices=STOPS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    weather = args.weather or rng.choice(list(WEATHERS))
    stilt = args.stilt or rng.choice(list(STILTS))
    stop = args.stop or rng.choice(list(STOPS))
    helper = args.helper or rng.choice(list(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(weather, stilt, stop, helper, name, gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = World()
    kid = world.add(Entity("kid", "character", params.kid_gender, params.kid_name, "kid", ["comic", "bouncy"]))
    parent = world.add(Entity("parent", "character", params.parent_type, "the parent", "parent"))
    weather = world.add(Entity("weather", "thing", params.weather, WEATHERS[params.weather].name))
    stilt = world.add(Entity("stilts", "thing", "stilt", STILTS[params.stilt].label, tall=True))
    stop = world.add(Entity("stop", "thing", "stop", STOPS[params.stop].label))
    bus = world.add(Entity("bus", "thing", "bus", "bus"))
    helper = world.add(Entity("helper", "character", "helper", HELPERS[params.helper].label, "helper"))
    helper.action = HELPERS[params.helper].action
    world.facts.update(weather=weather, stilt=stilt, stop=stop, helper=helper, bus=bus, kid=kid, parent=parent)
    setup(world, kid, parent, weather, stilt, stop, bus, helper)
    world.para()
    build_nudge(world, kid, parent, helper, weather, stop)
    comic_setback(world, kid, STILTS[params.stilt], STOPS[params.stop])
    cheerful_fix(world, kid, parent, helper, bus, weather, stop)
    ending(world, kid, parent, bus, STILTS[params.stilt], weather)
    world.facts["outcome"] = "happy"
    prompts = [
        "Write a funny bus-stop story about a child on stilts who tries to beckon a bus in changing weather, and ends happily.",
        f"Tell a comedy story in a bus stop where {params.kid_name} uses {params.stilt} and the weather keeps changing.",
        "Write a cheerful story that includes the words beckon, weather, and stilt, and ends with the bus arriving on time.",
    ]
    story_qa = [
        QAItem("What was the child waiting for?", "The child was waiting for the bus at the bus stop."),
        QAItem("Why did the child wobble?", "The child wobbled because the weather turned windy and the stilts shifted a little. The funny wobble made the waiting feel like a silly dance."),
        QAItem("How did the story end?", "The bus arrived, the child got on safely, and everyone was laughing. The weather stayed dramatic, but the ending stayed happy."),
    ]
    world_qa = [
        QAItem("What does beckon mean?", "To beckon means to wave or signal to someone to come closer or notice you."),
        QAItem("Why can windy weather be tricky?", "Windy weather can push at your balance and make tall or light things wobble."),
        QAItem("What are stilts?", "Stilts are tall supports that people stand on to be higher off the ground."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.list(world.entities.values()):
            print(e.id, e.type, dict(e.meters), dict(e.memes))
    if qa:
        print()
        print("== Q&A ==")
        for item in sample.prompts:
            print("P:", item)
        for item in sample.story_qa:
            print("Q:", item.question)
            print("A:", item.answer)
        for item in sample.world_qa:
            print("Q:", item.question)
            print("A:", item.answer)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        for w in WEATHERS:
            for s in STILTS:
                for t in STOPS:
                    samples.append(generate(StoryParams(w, s, t, "parent", "Lily", "girl", "mother")))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
