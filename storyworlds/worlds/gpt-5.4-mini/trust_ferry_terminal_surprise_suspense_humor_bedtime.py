#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/trust_ferry_terminal_surprise_suspense_humor_bedtime.py
======================================================================================

A standalone story world for a small bedtime tale at a ferry terminal.

Premise:
- A child and a grown-up are waiting for a ferry at a quiet terminal.
- A tiny mix-up creates suspense.
- A surprising, funny reveal restores trust.
- The ending proves the change with a calm, cozy image.

This world models:
- physical meters: distance, hiding, noise, lostness, brightness, wetness, settled
- emotional memes: trust, worry, suspense, relief, amusement, confidence

The story is intentionally small and classical: premise, tension, turn, ending.
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
SUSPENSE_MIN = 1.0
TRUST_MIN = 1.0
MIN_REASONABLE_TRUST = 4


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
class Setting:
    id: str
    place: str
    details: str
    night_sound: str
    cozy_finish: str

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
class Spark:
    id: str
    label: str
    object_phrase: str
    source: str
    surprise_reveal: str
    humor_line: str
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
class SuspenseBeat:
    id: str
    question: str
    clue: str
    tension_gain: float = 1.0

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
class Resolution:
    id: str
    action: str
    effect: str
    trust_gain: float
    relief_gain: float

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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["worry"] < THRESHOLD:
        return out
    sig = ("suspense",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["suspense"] += 1
    world.get("terminal").meters["quiet_tension"] += 1
    out.append("__suspense__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    grown = world.get("grownup")
    if child.memes["relief"] < THRESHOLD:
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["confidence"] += 1
    grown.memes["trust"] += 1
    world.get("terminal").meters["settled"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("suspense", "social", _r_suspense), Rule("relief", "social", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def predict_mixup(world: World) -> dict:
    sim = world.copy()
    simulate_mixup(sim, narrate=False)
    return {
        "worry": sim.get("child").memes["worry"],
        "found": bool(sim.facts.get("surprise_found")),
    }


def simulate_mixup(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    grown = world.get("grownup")
    spark = world.get("spark")
    child.memes["worry"] += 1
    child.meters["distance"] += 1
    world.get("terminal").meters["quiet_tension"] += 1
    if narrate:
        world.say(
            f"{child.id} and {grown.id} waited at the ferry terminal while the night air "
            f"moved softly over the dock."
        )
        world.say(
            f"{spark.object_phrase} had been set down nearby, and then it was suddenly not there."
        )
        world.say(
            f'"{spark.label}?" {child.id} whispered. The word felt small, and the benches felt big.'
        )
        world.say(
            f"{grown.id} looked under a seat, behind a post, and even beside a sleepy gull."
        )
    world.facts["surprise_found"] = True


def reveal(world: World, spark: Spark) -> None:
    child = world.get("child")
    grown = world.get("grownup")
    child.memes["surprise"] += 1
    child.memes["relief"] += 1
    grown.memes["amusement"] += 1
    world.say(
        f"Then came the surprise: {spark.surprise_reveal}. {spark.humor_line}"
    )
    world.say(
        f"{grown.id} laughed in a quiet bedtime way, and {child.id} laughed too, because the missing thing had never truly gone far."
    )


def reassure(world: World, res: Resolution, spark: Spark) -> None:
    child = world.get("child")
    grown = world.get("grownup")
    child.memes["trust"] += res.trust_gain
    child.memes["relief"] += res.relief_gain
    grown.memes["trust"] += 1
    world.get("terminal").meters["settled"] += 1
    world.say(
        f"{grown.id} came over and {res.action}. {res.effect} "
        f"That made {child.id} trust {grown.id} even more."
    )
    world.say(
        f"{spark.label.capitalize()} was back in hand, and the ferry horn sounded like a gentle good-night."
    )


def ending_image(world: World, setting: Setting) -> None:
    child = world.get("child")
    grown = world.get("grownup")
    world.say(
        f"By the time the ferry glided in, the terminal felt cozy and calm again. "
        f"{setting.cozy_finish}"
    )
    world.say(
        f"{child.id} leaned against {grown.id}, warm and sleepy, with worry gone and trust tucked safely in their pocket."
    )


def tell(setting: Setting, spark: Spark, suspense: SuspenseBeat, resolution: Resolution) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type="girl", role="child"))
    grown = world.add(Entity(id="grownup", kind="character", type="mother", role="grownup"))
    terminal = world.add(Entity(id="terminal", type="place", label=setting.place))
    light = world.add(Entity(id="lantern", type="thing", label="lantern"))
    s = world.add(Entity(id="spark", type="thing", label=spark.label))

    child.memes["trust"] = 5.0
    child.memes["worry"] = 0.0
    grown.memes["trust"] = 6.0
    terminal.meters["quiet_tension"] = 0.0
    terminal.meters["settled"] = 0.0
    world.facts["setting"] = setting
    world.facts["spark_cfg"] = spark
    world.facts["suspense"] = suspense
    world.facts["resolution"] = resolution
    world.facts["lantern"] = light

    world.say(
        f"At the ferry terminal, {child.id} and {grown.id} waited under the lamps while {setting.details}"
    )
    world.say(
        f"{child.id} liked the small night sounds, and the little {spark.label} was meant to help them see."
    )

    world.para()
    simulate_mixup(world)
    world.say(
        f"The missing pause made the night feel suspenseful, because {suspense.question.lower()} {suspense.clue}"
    )
    propagate(world, narrate=False)

    world.para()
    reveal(world, spark)
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1
    reassure(world, resolution, spark)

    world.para()
    ending_image(world, setting)

    world.facts.update(
        child=child,
        grownup=grown,
        terminal=terminal,
        spark=s,
        trust=child.memes["trust"],
        worry=child.memes["worry"],
        suspense=child.memes["suspense"],
        relief=child.memes["relief"],
        confidence=child.memes["confidence"],
    )
    return world


SETTINGS = {
    "ferry_terminal": Setting(
        id="ferry_terminal",
        place="the ferry terminal",
        details="the water tapped softly against the pilings and the schedule board glowed blue",
        night_sound="the hush of water",
        cozy_finish="The benches were still, the blue sign blinked slowly, and the ferry lights shone like sleepy fireflies.",
    ),
    "harbor_terminal": Setting(
        id="harbor_terminal",
        place="the harbor terminal",
        details="the harbor smelled like salt and the dock lamps made long yellow circles",
        night_sound="the soft harbor hush",
        cozy_finish="The rope coils lay neat, the dock lamps glowed low, and the water rocked the ferry like a cradle.",
    ),
}

SPARKS = {
    "lantern": Spark(
        id="lantern",
        label="lantern",
        object_phrase="A little lantern had been set on the bench",
        source="bench",
        surprise_reveal="the lantern was not lost at all; it had rolled behind the grown-up's bag and was peeking out like a shy moon",
        humor_line="It looked as if the lantern had simply taken a nap under the bag.",
        tags={"lantern", "light"},
    ),
    "ticket": Spark(
        id="ticket",
        label="ticket",
        object_phrase="A ferry ticket had been tucked into a pocket",
        source="pocket",
        surprise_reveal="the missing ticket had been stuck to the back of the child’s sleeve the whole time",
        humor_line="It was riding on the sleeve like a very tiny stowaway.",
        tags={"ticket", "paper"},
    ),
}

SUSPENSES = {
    "missing_lantern": SuspenseBeat(
        id="missing_lantern",
        question="where did the lantern go",
        clue="because the dock was dim and the boat was coming soon",
        tension_gain=1.5,
    ),
    "missing_ticket": SuspenseBeat(
        id="missing_ticket",
        question="who has the ticket",
        clue="because the ferry would not wait forever",
        tension_gain=1.5,
    ),
}

RESOLUTIONS = {
    "gentle_find": Resolution(
        id="gentle_find",
        action="checked one last pocket and then pointed under the bag",
        effect="The answer was simple, and the simple answer made the worry melt.",
        trust_gain=1.5,
        relief_gain=2.0,
    ),
    "soft_joke": Resolution(
        id="soft_joke",
        action="smiled and said, 'Well, that is a sneaky little lantern'",
        effect="The joke was tiny and kind, so it felt safe to laugh.",
        trust_gain=1.0,
        relief_gain=1.5,
    ),
}



@dataclass
class StoryParams:
    setting: str
    spark: str
    suspense: str
    resolution: str
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

CURATED = [
    StoryParams("ferry_terminal", "lantern", "missing_lantern", "gentle_find", seed=11),
    StoryParams("harbor_terminal", "ticket", "missing_ticket", "soft_joke", seed=22),
]



def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for spark in SPARKS:
            for suspense in SUSPENSES:
                for resolution in RESOLUTIONS:
                    combos.append((setting, spark, suspense, resolution))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: trust, suspense, humor, and surprise at a ferry terminal."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--spark", choices=SPARKS)
    ap.add_argument("--suspense", choices=SUSPENSES)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.spark is None or c[1] == args.spark)
              and (args.suspense is None or c[2] == args.suspense)
              and (args.resolution is None or c[3] == args.resolution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    if args.setting == "ferry_terminal" and args.spark == "ticket" and args.suspense == "missing_lantern":
        raise StoryError("The ticket and lantern mix-up do not fit together cleanly in this little world.")
    setting, spark, suspense, resolution = rng.choice(sorted(combos))
    return StoryParams(setting, spark, suspense, resolution)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story at a ferry terminal that includes the word "trust" and ends with a gentle surprise.',
        f"Tell a small suspense story where a child worries about {f['spark_cfg'].label} at the ferry terminal, then feels better after a funny reveal.",
        f"Write a cozy story with suspense, humor, and surprise where {f['setting'].place} becomes calm again by the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting: Setting = f["setting"]
    spark: Spark = f["spark_cfg"]
    qa = [
        QAItem(
            question="Where does the story happen?",
            answer=f"It happens at {setting.place}. The water and lights make the place feel quiet enough for a bedtime story."
        ),
        QAItem(
            question="What made the child feel suspense?",
            answer=f"{spark.label.capitalize()} seemed to be missing for a little while. That made the child worry until the grown-up checked carefully."
        ),
        QAItem(
            question="What was the surprise?",
            answer=f"{spark.surprise_reveal}. The missing thing had only hidden, so the scary feeling turned into a gentle surprise."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended calmly, with the child sleepy and safe beside the grown-up. The last image proves that the worry was gone and trust had grown."
        ),
    ]
    if f["trust"] >= 6:
        qa.append(
            QAItem(
                question="Why did the child trust the grown-up more at the end?",
                answer="Because the grown-up stayed calm, found the missing thing, and made the strange moment feel funny instead of frightening. That careful kindness turned suspense into relief."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ferry terminal?",
            answer="A ferry terminal is a place where people wait for ferries to arrive and leave. It usually has docks, lights, and signs for travelers."
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen next. It can make a story feel tense until the answer is revealed."
        ),
        QAItem(
            question="Why can humor help in a story?",
            answer="Humor can make a worried moment feel lighter. A small funny line can help everyone relax and keep listening."
        ),
        QAItem(
            question="What does trust mean?",
            answer="Trust means believing someone will help and keep you safe. In a story, trust can grow when a grown-up handles a problem kindly."
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    spark = SPARKS[params.spark]
    suspense = SUSPENSES[params.suspense]
    resolution = RESOLUTIONS[params.resolution]

    world = World()
    child = world.add(Entity(id="Mina", kind="character", type="girl", role="child"))
    grown = world.add(Entity(id="Mom", kind="character", type="mother", role="grownup"))
    terminal = world.add(Entity(id="terminal", type="place", label=setting.place))
    world.add(Entity(id="bag", type="thing", label="bag"))

    child.memes["trust"] = 5.0
    grown.memes["trust"] = 6.0
    child.memes["worry"] = 0.0
    world.facts["setting"] = setting
    world.facts["spark_cfg"] = spark
    world.facts["suspense"] = suspense
    world.facts["resolution"] = resolution

    world.say(
        f"At {setting.place}, Mina and Mom waited while {setting.details}."
    )
    world.say(
        f"They had a little thing to watch over: {spark.object_phrase.lower()}."
    )
    world.para()
    child.memes["worry"] += suspense.tension_gain
    terminal.meters["quiet_tension"] += 1
    world.say(
        f"Then the little thing was not where it should be, and suspense arrived: {suspense.question}. {suspense.clue}."
    )
    world.say(
        f"Mina peered under the bench. Mom peeked by the sign. Even the gull looked suspicious."
    )
    world.para()
    child.memes["surprise"] += 1
    world.say(
        f"The surprise came next: {spark.surprise_reveal}. {spark.humor_line}"
    )
    world.say(
        f"Mina blinked, then smiled, because sometimes a missing thing is just a very sneaky thing."
    )
    world.para()
    child.memes["relief"] += resolution.relief_gain
    child.memes["trust"] += resolution.trust_gain
    grown.memes["trust"] += 1
    terminal.meters["settled"] += 1
    world.say(
        f"Mom {resolution.action}, and {resolution.effect}"
    )
    world.say(
        f"That made Mina trust Mom more, and the two of them stood together as the ferry floated in like a slow silver fish."
    )
    world.para()
    world.say(
        f"By bedtime, {setting.cozy_finish}"
    )
    world.say(
        f"Mina leaned on Mom, sleepy and warm, while the ferry horn sounded far away and friendly."
    )

    world.facts.update(
        child=child,
        grownup=grown,
        terminal=terminal,
        trust=child.memes["trust"],
        worry=child.memes["worry"],
        surprise_found=True,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
valid(SP, SPK, SUS, RES) :- setting(SP), spark(SPK), suspense(SUS), resolution(RES).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for s in SPARKS:
        lines.append(asp.fact("spark", s))
    for s in SUSPENSES:
        lines.append(asp.fact("suspense", s))
    for s in RESOLUTIONS:
        lines.append(asp.fact("resolution", s))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: default generate smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def explain_rejection() -> str:
    return f"(No story: this world wants enough trust to make the suspense feel gentle; use trust >= {MIN_REASONABLE_TRUST}.)"


def build_reasonable(params: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("(No valid combination available.)")
    return StoryParams(*rng.choice(sorted(combos)))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(" ".join(row))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.setting} / {p.spark} / {p.suspense} / {p.resolution}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
