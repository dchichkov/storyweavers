#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tense_sun_nurse_happy_ending_moral_value.py
===========================================================================

A small storyworld about a tense sunlit afternoon, a nurse, and a problem that
turns out to be much smaller than it first seemed. The world keeps the story
child-facing and comedic: a worried child sees the sun as a disaster, a nurse
uses calm, practical help, and the ending proves the day became cheerful again.

Seed words: tense, sun, nurse
Features: Happy Ending, Moral Value
Style: Comedy
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
CALM_MIN = 2
NURSE_HELP_MIN = 2


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
        female = {"girl", "mother", "mom", "woman", "nurse"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"nurse": "nurse"}.get(self.type, self.type)
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
    label: str
    place_name: str
    sun: str
    shade: str
    mood: str
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
class Problem:
    id: str
    worry: str
    real_issue: str
    fix_hint: str
    noise: str
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
class Remedy:
    id: str
    label: str
    action: str
    result: str
    moral: str
    support: int
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_tense_spikes(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["tense"] < THRESHOLD:
            continue
        sig = ("tense_spike", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] += 1
        out.append("__tension__")
    return out


def _r_helping_cools(world: World) -> list[str]:
    out: list[str] = []
    nurse = world.entities.get("nurse")
    child = world.entities.get("child")
    if not nurse or not child:
        return out
    if nurse.memes["helping"] < THRESHOLD:
        return out
    sig = ("cool",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["calm"] += 1
    nurse.memes["pride"] += 1
    out.append("__calm__")
    return out


CAUSAL_RULES = [
    Rule("tense_spikes", "emotional", _r_tense_spikes),
    Rule("helping_cools", "social", _r_helping_cools),
]


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


def reasonable_problem(problem: Problem, setting: Setting) -> bool:
    return "sun" in problem.tags and "shade" in setting.tags


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.support >= NURSE_HELP_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_remedies():
        return combos
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            for rid, remedy in REMEDIES.items():
                if reasonable_problem(problem, setting) and remedy.support >= NURSE_HELP_MIN:
                    combos.append((sid, pid, rid))
    return combos


def predict(world: World, problem: Problem, remedy: Remedy) -> dict:
    sim = world.copy()
    sim.get("child").memes["tense"] += 1
    sim.get("nurse").memes["helping"] += 1
    if remedy.support >= problem_severity(problem):
        sim.get("child").memes["calm"] += 1
    return {"calm": sim.get("child").memes["calm"] >= THRESHOLD}


def problem_severity(problem: Problem) -> int:
    return 2 if "shadow" in problem.tags else 1


def introduce(world: World, child: Entity, nurse: Entity, setting: Setting) -> None:
    world.say(
        f"On a bright afternoon, {child.id} stood in {setting.place_name} and felt "
        f"tense for no good reason. The sun was shining, the bench was warm, and "
        f"the shadows looked much bossier than they were."
    )
    world.say(
        f"{nurse.id}, a cheerful nurse on a break, noticed the worried face right away."
    )
    child.memes["tense"] += 1
    nurse.memes["helping"] += 1


def worry(world: World, child: Entity, problem: Problem, setting: Setting) -> None:
    world.say(
        f'{child.id} pointed at the sun and whispered, "{problem.worry}" '
        f'The {setting.label} looked as if it might wobble, though it was only '
        f"standing there being a perfectly normal {setting.label}."
    )


def nurse_checks(world: World, nurse: Entity, child: Entity, problem: Problem) -> None:
    pred = predict(world, problem, REMEDIES["shade_cookie"])
    world.facts["predicted_calm"] = pred["calm"]
    world.say(
        f'{nurse.id} smiled. "That is a very large worry for a very ordinary sun," '
        f'{nurse.pronoun()} said. "{problem.fix_hint}"'
    )


def exaggerate(world: World, child: Entity, problem: Problem) -> None:
    child.memes["panic"] += 1
    world.say(
        f"{child.id} gasped and made the problem bigger in {child.pronoun('possessive')} "
        f"mind, as if the whole day had put on a tiny dramatic hat."
    )
    world.say(f'"{problem.noise}!" {child.id} cried, though nothing had actually exploded.')


def calm_fix(world: World, nurse: Entity, child: Entity, remedy: Remedy, problem: Problem) -> None:
    nurse.memes["helping"] += 1
    child.memes["calm"] += 1
    world.say(
        f"{nurse.id} {remedy.action}, and at once the big worry shrank to a small, funny one."
    )
    world.say(
        f"{remedy.result.capitalize()}, and {child.id} blinked at how silly the scare had been."
    )
    world.say(
        f"{nurse.id} added, '{remedy.moral}'"
    )
    world.facts["moral"] = remedy.moral


def happy_ending(world: World, child: Entity, nurse: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    nurse.memes["joy"] += 1
    world.say(
        f"In the end, the sun kept shining, the shade stayed cool, and {child.id} laughed so hard "
        f"{child.id} almost forgot to be tense at all."
    )
    world.say(
        f"{nurse.id} waved good-bye, and {child.id} marched off with a sunny grin, ready to remember "
        f"that a calm thought can be bigger than a silly worry."
    )


def tell(setting: Setting, problem: Problem, remedy: Remedy, child_name: str = "Milo",
         child_type: str = "boy", nurse_name: str = "Nurse June") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    nurse = world.add(Entity(id=nurse_name, kind="character", type="nurse", role="helper"))
    world.add(Entity(id="sun", kind="thing", type="thing", label="the sun"))
    world.add(Entity(id="shade", kind="thing", type="thing", label="the shade"))

    introduce(world, child, nurse, setting)
    world.para()
    worry(world, child, problem, setting)
    nurse_checks(world, nurse, child, problem)
    exaggerate(world, child, problem)

    world.para()
    calm_fix(world, nurse, child, remedy, problem)
    happy_ending(world, child, nurse, setting)

    world.facts.update(
        child=child,
        nurse=nurse,
        setting=setting,
        problem=problem,
        remedy=remedy,
        outcome="happy",
    )
    return world


SETTINGS = {
    "garden": Setting(
        id="garden",
        label="garden",
        place_name="the little garden",
        sun="bright sun",
        shade="tree shade",
        mood="comedy",
        tags={"sun", "shade", "outdoor"},
    ),
    "playground": Setting(
        id="playground",
        label="playground",
        place_name="the playground",
        sun="golden sun",
        shade="awning shade",
        mood="comedy",
        tags={"sun", "shade", "outdoor"},
    ),
    "courtyard": Setting(
        id="courtyard",
        label="courtyard",
        place_name="the courtyard",
        sun="hot sun",
        shade="wall shade",
        mood="comedy",
        tags={"sun", "shade", "outdoor"},
    ),
}

PROBLEMS = {
    "shadow": Problem(
        id="shadow",
        worry="The sun is too big and might eat my sandwich!",
        real_issue="a shadow moved on the wall",
        fix_hint="Let's step under the tree and look again.",
        noise="Oh no, the sky is doing acrobatics",
        tags={"sun", "shadow"},
    ),
    "glare": Problem(
        id="glare",
        worry="The sun is staring at me and making a face!",
        real_issue="sunlight bounced off a shiny pail",
        fix_hint="Let's turn the pail around and sit in the shade.",
        noise="The brightness is being extra loud",
        tags={"sun", "glare"},
    ),
    "squint": Problem(
        id="squint",
        worry="My eyes are squeezing themselves into raisins!",
        real_issue="the child was standing in direct sun",
        fix_hint="Let's move to a cooler spot and blink slowly.",
        noise="I have been ambushed by daylight",
        tags={"sun", "squint"},
    ),
}

REMEDIES = {
    "shade_cookie": Remedy(
        id="shade_cookie",
        label="a shade spot and a snack",
        action="pulled up a chair under the tree and handed over a snack",
        result="the child sat down, chewed, and noticed the sun was just a sun",
        moral="When a worry feels huge, it helps to stop and check what is really happening.",
        support=3,
        tags={"shade", "calm"},
    ),
    "water_bottle": Remedy(
        id="water_bottle",
        label="a cool drink",
        action="offered a sip of water and a shady bench",
        result="the child cooled off and stopped squinting at the sky",
        moral="A calm helper can make a hot day feel friendly again.",
        support=2,
        tags={"shade", "water"},
    ),
    "visor_joke": Remedy(
        id="visor_joke",
        label="a silly visor",
        action="put on a funny visor and waved like a parade marshal",
        result="the child snorted a laugh and the tense feeling popped like soap foam",
        moral="A little humor can help big feelings shrink to size.",
        support=2,
        tags={"joke", "shade"},
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Zoe", "Pia", "Nina", "Tara"]
BOY_NAMES = ["Milo", "Owen", "Ben", "Theo", "Noah", "Finn"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    remedy: str
    child_name: str
    child_type: str
    nurse_name: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a young child that includes the words "{f["problem"].id}", '
        f'"sun", and "nurse", and ends happily.',
        f"Tell a comedy story where {f['child'].id} gets tense about the sun, but a nurse helps "
        f"with a calm, kind solution.",
        f"Write a moral-value story about a child and a nurse on a sunny day, with a happy ending "
        f"and a gentle lesson about checking worries.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    nurse = f["nurse"]
    setting = f["setting"]
    problem = f["problem"]
    remedy = f["remedy"]
    return [
        (
            "Who was the story about?",
            f"It was about {child.id} and {nurse.id} in {setting.place_name}. The child was tense "
            f"about the sun, and the nurse helped with a calm plan.",
        ),
        (
            f"Why did {child.id} feel tense?",
            f"{child.id} worried the sun was causing a big problem, even though the real issue was "
            f"much smaller. The worry looked serious in the moment, which made the story funny.",
        ),
        (
            f"How did {nurse.id} help?",
            f"{nurse.id} used a gentle, sensible idea: {remedy.action}. That helped the child slow "
            f"down, look again, and see the problem more clearly.",
        ),
        (
            "What did the child learn?",
            f"The child learned that it is wise to pause and check what is really happening before "
            f"panicking. The moral is {remedy.moral}",
        ),
        (
            "How did the story end?",
            f"It ended happily with laughter, shade, and a calmer child. The sun stayed in the sky, "
            f"but the scary feeling was gone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        (
            "What is a nurse?",
            "A nurse is a helpful grown-up who knows how to care for people and calm them down when "
            "they are worried or hurt.",
        ),
        (
            "Why can the sun feel strong?",
            "The sun gives light and heat. On a bright day it can make people warm and make them squint.",
        ),
        (
            "What should you do when a worry feels huge?",
            "Stop, breathe, and check the facts. A calm helper can make the problem easier to understand.",
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="garden",
        problem="shadow",
        remedy="shade_cookie",
        child_name="Milo",
        child_type="boy",
        nurse_name="Nurse June",
    ),
    StoryParams(
        setting="playground",
        problem="glare",
        remedy="visor_joke",
        child_name="Mina",
        child_type="girl",
        nurse_name="Nurse Bea",
    ),
    StoryParams(
        setting="courtyard",
        problem="squint",
        remedy="water_bottle",
        child_name="Theo",
        child_type="boy",
        nurse_name="Nurse Ada",
    ),
]


def explain_rejection(problem: Problem, setting: Setting) -> str:
    return (
        f"(No story: {problem.id} is not a good fit for {setting.label}. The problem must be tied "
        f"to the sun and the place must have shade, so the nurse has something sensible to do.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "happy"


def valid_problem(problem: Problem, setting: Setting) -> bool:
    return reasonable_problem(problem, setting)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tense sunny moment, a nurse, and a happy comedy ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--nurse")
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
    if args.setting and args.problem:
        if not valid_problem(PROBLEMS[args.problem], SETTINGS[args.setting]):
            raise StoryError(explain_rejection(PROBLEMS[args.problem], SETTINGS[args.setting]))
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.problem is None or c[1] == args.problem)
        and (args.remedy is None or c[2] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, remedy = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    nurse = args.nurse or rng.choice(["Nurse June", "Nurse Bea", "Nurse Ada", "Nurse Kim"])
    return StoryParams(
        setting=setting,
        problem=problem,
        remedy=remedy,
        child_name=name,
        child_type=gender,
        nurse_name=nurse,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.remedy not in REMEDIES:
        raise StoryError("Invalid params.")
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], REMEDIES[params.remedy],
                 child_name=params.child_name, child_type=params.child_type, nurse_name=params.nurse_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
valid(S,P,R) :- setting(S), problem(P), remedy(R), sun_problem(P), shade_place(S).
happy :- valid(_,_,_).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if "shade" in s.tags:
            lines.append(asp.fact("shade_place", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if "sun" in p.tags:
            lines.append(asp.fact("sun_problem", pid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos()")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for row in combos:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
