#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bottle_feed_aerobic_jog_humor_space_adventure.py
===============================================================================

A tiny storyworld for a humorous Space Adventure about a baby robot, a
bottle-feed, an aerobic routine, and a jog through a moonbase.

Seed premise
------------
A crew on a small space station needs to calm a tiny rover-bot, keep it
charged, and get it moving again before the launch bell. The bot's caretaker
tries a silly bottle-feed routine, a brisk aerobic warmup, and a moon-jog
through the corridor. The ending proves what changed: the bot is soothed,
energy rises, and the station gets back on schedule.

The world is intentionally small and classical:
- typed entities with physical meters and emotional memes
- a forward-chained causal engine
- a reasonableness gate with Python + ASP twin
- three QA sets grounded in the simulated state
- child-facing prose with a playful space-adventure tone

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/bottle_feed_aerobic_jog_humor_space_adventure.py
    python storyworlds/worlds/gpt-5.4-mini/bottle_feed_aerobic_jog_humor_space_adventure.py --qa
    python storyworlds/worlds/gpt-5.4-mini/bottle_feed_aerobic_jog_humor_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4-mini/bottle_feed_aerobic_jog_humor_space_adventure.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
ENERGY_MIN = 1.0


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
        return self.label or self.type
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
class Pod:
    id: str
    label: str
    place: str
    humor: str
    affixes: list[str] = field(default_factory=list)
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
class FuelBottle:
    id: str
    label: str
    phrase: str
    sip: str
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
class Warmup:
    id: str
    label: str
    phrase: str
    move: str
    energy: int
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
class Jog:
    id: str
    label: str
    phrase: str
    path: str
    pace: str
    energy: int
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone.facts = copy.deepcopy(self.facts)
        return clone
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


def _r_charge(world: World) -> list[str]:
    out = []
    bot = world.entities.get("bot")
    if bot and bot.meters["sipped"] >= THRESHOLD and ("charge", "bot") not in world.fired:
        world.fired.add(("charge", "bot"))
        bot.meters["energy"] += 1
        bot.memes["cheer"] += 1
        out.append("__charge__")
    return out


def _r_mood(world: World) -> list[str]:
    out = []
    bot = world.entities.get("bot")
    if bot and bot.memes["laugh"] >= THRESHOLD and ("mood", "bot") not in world.fired:
        world.fired.add(("mood", "bot"))
        bot.memes["calm"] += 1
        out.append("__mood__")
    return out


def _r_motion(world: World) -> list[str]:
    out = []
    bot = world.entities.get("bot")
    if bot and bot.meters["jogged"] >= THRESHOLD and ("motion", "bot") not in world.fired:
        world.fired.add(("motion", "bot"))
        bot.meters["speed"] += 1
        out.append("__motion__")
    return out


CAUSAL_RULES = [
    Rule("charge", "energy", _r_charge),
    Rule("mood", "emotional", _r_mood),
    Rule("motion", "physical", _r_motion),
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


def reasonableness_ok(fuel: FuelBottle, warmup: Warmup, jog: Jog) -> bool:
    return fuel.id == "bottle_feed" and warmup.energy > 0 and jog.energy > 0


def sensible_fuel() -> list[FuelBottle]:
    return list(FUEL.values())


def sensible_warmups() -> list[Warmup]:
    return [w for w in WARMUPS.values() if w.energy >= SENSE_MIN]


def sensible_jogs() -> list[Jog]:
    return [j for j in JOGS.values() if j.energy >= SENSE_MIN]


def needed_energy(jog: Jog, delay: int) -> int:
    return jog.energy + delay


def can_finish(warmup: Warmup, jog: Jog, delay: int) -> bool:
    return warmup.energy + 1 >= needed_energy(jog, delay)


def bottle_feed(world: World, caregiver: Entity, bot: Entity, fuel: FuelBottle) -> None:
    bot.meters["sipped"] += 1
    bot.memes["trust"] += 1
    world.say(
        f"{caregiver.id} held up {fuel.phrase} like it was a tiny moon rocket. "
        f'"Time for a bottle-feed," {caregiver.pronoun()} said, and {bot.id} took a sip.'
    )


def aeroboost(world: World, caregiver: Entity, bot: Entity, warmup: Warmup) -> None:
    bot.meters["warmed"] += 1
    bot.memes["giggle"] += 1
    world.say(
        f"Then {caregiver.id} started an {warmup.label} routine. "
        f"{bot.id} copied the {warmup.move} and wiggled like a blinking star."
    )


def jog_world(world: World, bot: Entity, jog: Jog) -> None:
    bot.meters["jogged"] += 1
    bot.memes["joy"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At last, {bot.id} took a {jog.label} through {jog.path}. "
        f"{bot.id} {jog.pace}, and the whole corridor sounded like a funny drum."
    )


def finish(world: World, bot: Entity, station: Entity, pod: Pod, delay: int) -> None:
    if bot.meters["energy"] >= ENERGY_MIN and bot.meters["speed"] >= ENERGY_MIN:
        station.meters["order"] += 1
        world.say(
            f"{pod.humor} The little bot beeped, spun in a cheerful circle, and "
            f"rolled to the launch bay just in time."
        )
        world.say(
            f"The station crew laughed, because the bot had gone from sleepy to speedy "
            f"without ever leaving the moonbase."
        )
    else:
        world.say(
            f"{pod.humor} Even so, the bot was too wobbly for the launch bell, so the "
            f"crew slowed down and tried again after a rest."
        )
        station.meters["order"] += 0.5


def tell(pod: Pod, fuel: FuelBottle, warmup: Warmup, jog: Jog, delay: int = 0,
         caregiver_name: str = "Mira", caregiver_gender: str = "girl",
         bot_name: str = "Bip", bot_kind: str = "robot",
         station_name: str = "Moon Station 7") -> World:
    world = World()
    caregiver = world.add(Entity(id=caregiver_name, kind="character", type=caregiver_gender, role="caregiver"))
    bot = world.add(Entity(id="bot", kind="character", type=bot_kind, role="tiny-robot"))
    station = world.add(Entity(id="station", kind="thing", type="station", label=station_name))
    world.facts["pod"] = pod
    world.facts["delay"] = delay
    world.facts["bot_name"] = bot_name

    world.say(
        f"On {pod.place}, {caregiver.id} watched {bot_name} wobble beside a round window. "
        f"{pod.humor} The tiny rover-bot had one job: stay cheerful until the rocket check."
    )
    world.say(
        f"{bot_name} made a little beep that sounded suspiciously like a sneeze."
    )

    world.para()
    bottle_feed(world, caregiver, bot, fuel)
    aeroboost(world, caregiver, bot, warmup)

    world.para()
    if can_finish(warmup, jog, delay):
        jog_world(world, bot, jog)
    else:
        bot.memes["anxiety"] += 1
        world.say(
            f"{bot_name} wanted to go, but the corridor winds felt bigger than {bot_name}'s brave batteries. "
            f"{caregiver.id} gave {bot_name} a steadier pep talk, then slowed the jog to a gentler pace."
        )
        bot.meters["jogged"] += 1
        bot.memes["joy"] += 1
        propagate(world, narrate=False)
        world.say(
            f"Together they did a slower moon-jog, and {bot_name} stopped wobbling like a loose spoon."
        )

    world.para()
    finish(world, bot, station, pod, delay)

    world.facts.update(
        caregiver=caregiver, bot=bot, station=station,
        fuel=fuel, warmup=warmup, jog=jog, outcome="steady" if bot.meters["speed"] >= 1 else "wobbly"
    )
    return world


PODS = {
    "moonbase": Pod(
        id="moonbase",
        label="the moonbase",
        place="the moonbase hallway",
        humor="A tiny wrench floated by like it had important business.",
        affixes=["moon", "base"],
        tags={"space", "humor"},
    ),
    "orbiter": Pod(
        id="orbiter",
        label="the orbit ring",
        place="the orbit ring corridor",
        humor="A sticker on the wall said, \"Low gravity, high silliness.\"",
        affixes=["orbit", "ring"],
        tags={"space", "humor"},
    ),
}

FUEL = {
    "bottle_feed": FuelBottle(
        id="bottle_feed",
        label="bottle-feed",
        phrase="a bottle-feed bottle",
        sip="sip",
        tags={"bottle-feed", "care"},
    ),
    "snack_sip": FuelBottle(
        id="snack_sip",
        label="bottle-feed",
        phrase="a bottle-feed bottle",
        sip="sip",
        tags={"bottle-feed", "care"},
    ),
}

WARMUPS = {
    "aerobic": Warmup(
        id="aerobic",
        label="aerobic",
        phrase="an aerobic warmup",
        move="star jumps",
        energy=2,
        tags={"aerobic", "exercise"},
    ),
    "stretch": Warmup(
        id="stretch",
        label="aerobic",
        phrase="an aerobic warmup",
        move="arm circles",
        energy=2,
        tags={"aerobic", "exercise"},
    ),
}

JOGS = {
    "jog": Jog(
        id="jog",
        label="jog",
        phrase="a jog",
        path="the zero-g corridor",
        pace="jogged with tiny bouncing steps",
        energy=2,
        tags={"jog", "exercise"},
    ),
    "moon_jog": Jog(
        id="moon_jog",
        label="jog",
        phrase="a jog",
        path="the zero-g corridor",
        pace="jogged with tiny bouncing steps",
        energy=3,
        tags={"jog", "exercise"},
    ),
}

TRAITS = ["cheerful", "curious", "silly", "gentle"]


@dataclass
class StoryParams:
    pod: str
    fuel: str
    warmup: str
    jog: str
    delay: int = 0
    caregiver_name: str = "Mira"
    caregiver_gender: str = "girl"
    bot_name: str = "Bip"
    bot_kind: str = "robot"
    station_name: str = "Moon Station 7"
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
    StoryParams(pod="moonbase", fuel="bottle_feed", warmup="aerobic", jog="jog", delay=0, caregiver_name="Mira", caregiver_gender="girl", bot_name="Bip"),
    StoryParams(pod="orbiter", fuel="bottle_feed", warmup="stretch", jog="moon_jog", delay=1, caregiver_name="Sol", caregiver_gender="boy", bot_name="Zip"),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for p in PODS:
        for f in FUEL:
            for w in WARMUPS:
                for j in JOGS:
                    if reasonableness_ok(FUEL[f], WARMUPS[w], JOGS[j]):
                        combos.append((p, f, w, j))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Spacey humorous bottle-feed/aerobic/jog storyworld.")
    ap.add_argument("--pod", choices=PODS)
    ap.add_argument("--fuel", choices=FUEL)
    ap.add_argument("--warmup", choices=WARMUPS)
    ap.add_argument("--jog", choices=JOGS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
    ap.add_argument("--name")
    ap.add_argument("--bot")
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
    if args.fuel and args.warmup and args.jog:
        if not reasonableness_ok(FUEL[args.fuel], WARMUPS[args.warmup], JOGS[args.jog]):
            raise StoryError("That combination doesn't make a sensible space story.")
    combos = [c for c in valid_combos()
              if (args.pod is None or c[0] == args.pod)
              and (args.fuel is None or c[1] == args.fuel)
              and (args.warmup is None or c[2] == args.warmup)
              and (args.jog is None or c[3] == args.jog)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    pod, fuel, warmup, jog = rng.choice(sorted(combos))
    return StoryParams(
        pod=pod, fuel=fuel, warmup=warmup, jog=jog, delay=args.delay,
        caregiver_name=args.name or rng.choice(["Mira", "Sol", "Nova", "Pip"]),
        caregiver_gender=rng.choice(["girl", "boy"]),
        bot_name=args.bot or rng.choice(["Bip", "Zip", "Dot", "Buzz"]),
        bot_kind="robot",
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny space adventure story that includes the words "{f["fuel"].label}", "{f["warmup"].label}", and "{f["jog"].label}".',
        f"Tell a moonbase story where {f['caregiver'].id} uses a {f['fuel'].label} bottle, then an {f['warmup'].label} routine, then a {f['jog'].label} to help the tiny robot.",
        f"Write a child-friendly humorous story on a space station with bottle-feed, aerobic, and jog scenes, ending with a cheerful launch-bay image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    bot = f["bot"]
    caregiver = f["caregiver"]
    fuel = f["fuel"]
    warmup = f["warmup"]
    jog = f["jog"]
    qa = [
        ("Who is the story about?",
         f"It is about {caregiver.id} and the tiny robot {f['bot_name']}. They are on a space station, trying to get ready for the launch check."),
        ("What did {0} do first?".format(caregiver.id),
         f"{caregiver.id} started with a bottle-feed to help {f['bot_name']} settle down. That gave the little bot a calm, steady start."),
        ("What did they do after the bottle-feed?",
         f"They moved into an {warmup.label} warmup and then a {jog.label}. The warmup helped the bot wake up, and the jog helped it get moving."),
        ("How did the story end?",
         f"It ended with {f['bot_name']} feeling steadier and the station getting back on schedule. The ending image is a cheerful little robot rolling toward the launch bay."),
    ]
    if bot.meters["energy"] >= ENERGY_MIN:
        qa.append((
            "Why did the bottle-feed matter?",
            "The bottle-feed gave the robot a charged-up feeling and helped it settle. That made it easier to keep going into the warmup and the jog."
        ))
    if bot.memes["laugh"] >= THRESHOLD:
        qa.append((
            "Why is the story funny?",
            f"The humor comes from silly moonbase details like the floating wrench and the robot wobbling like a spoon. The scene stays playful even while everyone works hard."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a bottle-feed?",
         "A bottle-feed is a gentle way to give a little one a drink from a bottle. In a story, it can also show care and calm attention."),
        ("What does aerobic mean?",
         "Aerobic means exercise that gets your body moving and your heart pumping. It is the kind of warmup that helps you feel ready."),
        ("What is a jog?",
         "A jog is a light run done at an easy pace. People jog when they want to move and get exercise without sprinting."),
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


def generate(params: StoryParams) -> StorySample:
    if params.pod not in PODS or params.fuel not in FUEL or params.warmup not in WARMUPS or params.jog not in JOGS:
        raise StoryError("Invalid StoryParams keys.")
    world = tell(PODS[params.pod], FUEL[params.fuel], WARMUPS[params.warmup], JOGS[params.jog], delay=params.delay, caregiver_name=params.caregiver_name, caregiver_gender=params.caregiver_gender, bot_name=params.bot_name, bot_kind=params.bot_kind, station_name=params.station_name)
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(e.id, dict(e.meters), dict(e.memes))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
sensible_combo(P,F,W,J) :- pod(P), fuel(F), warmup(W), jog(J), ok(F), ok(W), ok(J).
ok("bottle_feed").
ok("aerobic").
ok("jog").
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PODS:
        lines.append(asp.fact("pod", p))
    for f in FUEL:
        lines.append(asp.fact("fuel", f))
    for w in WARMUPS:
        lines.append(asp.fact("warmup", w))
    for j in JOGS:
        lines.append(asp.fact("jog", j))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show sensible_combo/4."))
    return sorted(set(asp.atoms(model, "sensible_combo")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP does not match Python valid_combos().")
    try:
        s = generate(CURATED[0])
        assert s.story
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"MISMATCH: generate() smoke test failed: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show sensible_combo/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for combo in combos:
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
