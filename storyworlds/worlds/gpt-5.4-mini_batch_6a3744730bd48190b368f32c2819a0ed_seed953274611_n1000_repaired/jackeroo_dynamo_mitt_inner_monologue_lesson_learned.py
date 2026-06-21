#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/jackeroo_dynamo_mitt_inner_monologue_lesson_learned.py
========================================================================================

A small detective-style storyworld about a curious kid detective, a noisy
jackeroo, a hand-cranked dynamo, and a mitten that matters.

The premise is child-facing and state-driven:
- a kid detective follows clues with an inner monologue,
- a risky shortcut tempts them to use a dynamo in the dark,
- bravery helps them speak up and choose a safer path,
- a lesson learned ends the story with a changed object and a changed mood.

The world keeps physical meters and emotional memes, supports the shared Story
API, includes a Python reasonableness gate plus an inline ASP twin, and can emit
prompts / story QA / world QA from simulated world state.

Seed words: jackeroo, dynamo, mitt
Features: Inner Monologue, Lesson Learned, Bravery
Style: Detective Story
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

from storyworlds.results import QAItem, StoryError, StorySample  # eager import

THRESHOLD = 1.0
BRAVERY_MIN = 3.0


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
    noisy: bool = False
    electric: bool = False
    protective: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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


@dataclass
class Setting:
    id: str
    place: str
    dark_spot: str
    detective_frame: str
    clue_word: str
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


@dataclass
class Suspect:
    id: str
    label: str
    line: str
    risky: bool = True
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


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    safe: bool
    bright: bool = True
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Lesson:
    id: str
    truth: str
    ending_image: str
    kind: str = "lesson"
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
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


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    if any(e.meters["spark"] >= THRESHOLD for e in world.entities.values()):
        sig = ("alarm",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        if "scene" in world.entities:
            world.get("scene").meters["alarm"] += 1
        for ent in list(world.entities.values()):
            if ent.kind == "character":
                ent.memes["worry"] += 1
        out.append("__alarm__")
    return out


CAUSAL_RULES = [Rule("alarm", _r_alarm)]


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


SETTINGS = {
    "alley": Setting(
        id="alley",
        place="the narrow alley behind the bakery",
        dark_spot="the shadow under the fire escape",
        detective_frame="a tiny detective case",
        clue_word="clue",
    ),
    "dock": Setting(
        id="dock",
        place="the old dock by the river",
        dark_spot="the gap under the rope coils",
        detective_frame="a river mystery",
        clue_word="trail",
    ),
    "attic": Setting(
        id="attic",
        place="the dusty attic",
        dark_spot="the space behind the trunk",
        detective_frame="a whispery mystery",
        clue_word="trace",
    ),
}

SUSPECTS = {
    "jackeroo": Suspect(
        id="jackeroo",
        label="the jackeroo",
        line="the jackeroo moved like a quick shadow",
        risky=True,
    ),
    "dynamo": Suspect(
        id="dynamo",
        label="the dynamo",
        line="the dynamo hummed like a stubborn bee",
        risky=True,
    ),
    "mitt": Suspect(
        id="mitt",
        label="the mitt",
        line="the mitt was soft and easy to trust",
        risky=False,
    ),
}

TOOLS = {
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        safe=True,
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a little lantern",
        safe=True,
    ),
    "lamp": Tool(
        id="lamp",
        label="desk lamp",
        phrase="the desk lamp",
        safe=True,
    ),
}

LESSONS = {
    "call_help": Lesson(
        id="call_help",
        truth="The bravest choice is to call for help when a clue feels risky.",
        ending_image="the case file sat next to a bright safe light",
    ),
    "share_clue": Lesson(
        id="share_clue",
        truth="Bravery can mean telling the truth before a small mistake grows big.",
        ending_image="the mitt rested beside a warm light and a neat notebook",
    ),
}

NAMES = ["Mina", "Theo", "Lena", "Owen", "Maya", "Iris", "Noah", "Zoe"]
TRAITS = ["curious", "careful", "brave", "thoughtful"]


@dataclass
class StoryParams:
    setting: str
    suspect: str
    tool: str
    lesson: str
    name: str
    gender: str
    sidekick: str
    sidekick_gender: str
    trait: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid in SETTINGS:
        for sus in SUSPECTS:
            for tool in TOOLS:
                for lesson in LESSONS:
                    if suspect_risky(SUSPECTS[sus]) and tool_safe(TOOLS[tool]):
                        combos.append((sid, sus, tool, lesson))
    return combos


def suspect_risky(suspect: Suspect) -> bool:
    return suspect.risky


def tool_safe(tool: Tool) -> bool:
    return tool.safe


def predict_risk(world: World, suspect_id: str) -> dict:
    sim = world.copy()
    sim.get(suspect_id).meters["spark"] += 1
    propagate(sim, narrate=False)
    return {
        "alarm": sim.get("scene").meters["alarm"] >= THRESHOLD,
        "worry": sum(e.memes["worry"] for e in sim.entities.values() if e.kind == "character"),
    }


def reasonableness_check(params: StoryParams) -> None:
    if params.suspect not in SUSPECTS:
        raise StoryError("Unknown suspect.")
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.lesson not in LESSONS:
        raise StoryError("Unknown lesson.")
    if not suspect_risky(SUSPECTS[params.suspect]):
        raise StoryError("This suspect is too calm for a detective-style tension beat.")
    if not tool_safe(TOOLS[params.tool]):
        raise StoryError("The chosen tool is not a safe alternative.")
    if params.suspect == "mitt":
        raise StoryError("The mitt is the innocent clue-holder here, not the risky shortcut.")
    if params.tool == "dynamo":
        raise StoryError("The dynamo is the risky source, not the safe ending tool.")


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    suspect = SUSPECTS[params.suspect]
    tool = TOOLS[params.tool]
    lesson = LESSONS[params.lesson]

    hero = world.add(Entity(
        id=params.name, kind="character", type=params.gender, role="detective",
        traits=["small", params.trait], attrs={"sidekick": params.sidekick},
    ))
    sidekick = world.add(Entity(
        id=params.sidekick, kind="character", type=params.sidekick_gender,
        role="helper", traits=["quiet", "steady"],
    ))
    scene = world.add(Entity(id="scene", kind="thing", type="scene", label=setting.place))
    clue_obj = world.add(Entity(
        id="mitt", kind="thing", type="mitt", label="mitt", protective=True,
        attrs={"where": setting.dark_spot},
    ))
    risky_obj = world.add(Entity(
        id=suspect.id, kind="thing", type=suspect.id, label=suspect.label,
        noisy=True, electric=(suspect.id == "dynamo"),
    ))
    safe_tool = world.add(Entity(
        id=tool.id, kind="thing", type=tool.id, label=tool.label,
        protective=True, attrs={"phrase": tool.phrase},
    ))
    world.facts.update(
        setting=setting,
        suspect=suspect,
        tool=tool,
        lesson=lesson,
        hero=hero,
        sidekick=sidekick,
        clue_obj=clue_obj,
        risky_obj=risky_obj,
        safe_tool=safe_tool,
    )

    hero.memes["bravery"] = 2.0
    sidekick.memes["care"] = 2.0

    world.say(
        f"{hero.id} was a tiny detective in {setting.place}. {hero.id} kept a notebook, "
        f"and {setting.detective_frame} felt just right for a careful search."
    )
    world.say(
        f"At the dark spot, the {clue_obj.label} waited like a clue. "
        f"{suspect.line.capitalize()}, and {hero.id}'s inner monologue whispered, "
        f'"If this is a real clue, I should not rush it."'
    )

    world.para()
    world.say(
        f"{hero.id} wanted to use {suspect.label} to peer into the shadows, but the "
        f"idea felt risky."
    )
    world.say(
        f'"The case needs bravery," {hero.id} thought, "not a shortcut that could start a bigger mess."'
    )
    hero.memes["bravery"] += 1
    sidekick.memes["bravery"] += 1

    if suspect.id == "mitt":
        raise StoryError("The mitt cannot be the risky suspect in this world.")

    if suspect.id == "dynamo":
        world.say(
            f"{hero.id} imagined the {suspect.label} spinning fast and lighting the dark too sharply."
        )
    else:
        world.say(
            f"{hero.id} imagined the {suspect.label} darting away before the answer was clear."
        )

    world.para()
    if hero.memes["bravery"] >= BRAVERY_MIN:
        world.say(
            f"{sidekick.id} looked at {hero.id} and nodded. {hero.id} took a breath and said, "
            f'"No. We should use {tool.phrase} instead."'
        )
        world.say(
            f"That was the brave part of the case: saying the safer thing out loud."
        )
        world.say(
            f"{hero.id} turned on {tool.phrase}, and its steady light reached the {clue_obj.label} "
            f"without any sparks."
        )
        clue_obj.meters["found"] += 1
        hero.memes["relief"] += 1
        hero.memes["lesson"] += 1
        sidekick.memes["relief"] += 1
        world.say(
            f"The {clue_obj.label} glinted, and the answer was plain: the little mystery had been solved "
            f"without waking the dark."
        )
        world.para()
        world.say(
            f"By the end, {hero.id} wrote the lesson down: {lesson.truth} "
            f"{lesson.ending_image}."
        )
        world.say(
            f"{hero.id} smiled because bravery had not meant being loud. It had meant choosing well."
        )
        world.facts["outcome"] = "learned"
    else:
        world.say(
            f"{hero.id} hesitated too long, and the case went nowhere."
        )
        world.facts["outcome"] = "stuck"

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story for a child that includes the words "{f["suspect"].id}", '
        f'"{f["tool"].id}", and "mitt".',
        f"Tell a small mystery where {f['hero'].id} uses inner monologue, shows bravery, "
        f"and learns a lesson about a risky clue.",
        f'Write a story set at {f["setting"].place} where a kid detective chooses a safe tool '
        f"instead of a risky shortcut.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    suspect: Suspect = f["suspect"]
    tool: Tool = f["tool"]
    lesson: Lesson = f["lesson"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id}, a small detective, and {sidekick.id}, who helps with the case.",
        ),
        QAItem(
            question="What did the detective think to themself?",
            answer=(
                f"{hero.id} thought that a real clue should be handled carefully, because rushing could turn a small problem into a bigger one. "
                f"That inner monologue helped {hero.id} choose the safer path."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} choose instead of the risky clue?",
            answer=(
                f"{hero.id} chose {tool.phrase} instead of {suspect.label}. "
                f"That let the detective see the clue without making sparks or trouble."
            ),
        ),
    ]
    if f.get("outcome") == "learned":
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=(
                    f"It ended with a lesson learned. {hero.id} wrote down that bravery can mean speaking up for the safer choice, "
                    f"and the bright light showed the clue clearly."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dynamo?",
            answer=(
                "A dynamo is a machine that can make electricity when someone turns it. "
                "It can be useful, but it is not a toy for a child detective to treat carelessly."
            ),
        ),
        QAItem(
            question="What is a mitt?",
            answer=(
                "A mitt is a soft hand covering. It can keep a hand warm or help hold something, and in this story it is part of the clue."
            ),
        ),
        QAItem(
            question="What does bravery mean?",
            answer=(
                "Bravery means doing the right thing even when you feel a little scared. "
                "Sometimes bravery is speaking up and choosing the safer answer."
            ),
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(params: StoryParams) -> str:
    if params.suspect == "mitt":
        return "(No story: the mitt is meant to be the clue-holder, not the risky culprit.)"
    if params.tool == "dynamo":
        return "(No story: the dynamo is the risky object in this world, not the safe ending tool.)"
    return "(No story: this combination does not support a believable detective-style lesson.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        (s, sus, tool, lesson)
        for s, sus, tool, lesson in valid_combos()
        if (args.setting is None or s == args.setting)
        and (args.suspect is None or sus == args.suspect)
        and (args.tool is None or tool == args.tool)
        and (args.lesson is None or lesson == args.lesson)
    ]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    setting, suspect, tool, lesson = rng.choice(sorted(choices))
    gender = args.gender or rng.choice(["girl", "boy"])
    side_gender = "boy" if gender == "girl" else "girl"
    name = args.name or rng.choice(NAMES)
    sidekick = args.sidekick or rng.choice([n for n in NAMES if n != name])
    trait = args.trait or rng.choice(TRAITS)
    if args.suspect == "mitt":
        raise StoryError("The mitt cannot be the risky suspect.")
    return StoryParams(
        setting=setting, suspect=suspect, tool=tool, lesson=lesson,
        name=name, gender=gender, sidekick=sidekick, sidekick_gender=side_gender,
        trait=trait, seed=None,
    )


CURATED = [
    StoryParams(setting="alley", suspect="jackeroo", tool="flashlight", lesson="call_help",
                name="Mina", gender="girl", sidekick="Theo", sidekick_gender="boy",
                trait="curious", seed=101),
    StoryParams(setting="dock", suspect="dynamo", tool="lantern", lesson="share_clue",
                name="Owen", gender="boy", sidekick="Iris", sidekick_gender="girl",
                trait="brave", seed=202),
    StoryParams(setting="attic", suspect="jackeroo", tool="lamp", lesson="call_help",
                name="Lena", gender="girl", sidekick="Noah", sidekick_gender="boy",
                trait="thoughtful", seed=303),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.suspect not in SUSPECTS or params.tool not in TOOLS or params.lesson not in LESSONS:
        raise StoryError("Invalid story parameters.")
    reasonableness_check(params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld with inner monologue and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick")
    ap.add_argument("--trait", choices=TRAITS)
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


ASP_RULES = r"""
risky_suspect(jackeroo).
risky_suspect(dynamo).
safe_tool(flashlight).
safe_tool(lantern).
safe_tool(lamp).

valid(S, U, T, L) :- setting(S), suspect(U), tool(T), lesson(L), risky_suspect(U), safe_tool(T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sus in SUSPECTS:
        lines.append(asp.fact("suspect", sus))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool))
    for lesson in LESSONS:
        lines.append(asp.fact("lesson", lesson))
    for sus in ["jackeroo", "dynamo"]:
        lines.append(asp.fact("risky_suspect", sus))
    for tool in ["flashlight", "lantern", "lamp"]:
        lines.append(asp.fact("safe_tool", tool))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print("python only:", sorted(py - cl))
        print("asp only:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test story generation works.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"MISMATCH: smoke test failed: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for row in combos:
            print("  ", row)
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
                p.seed = seed
                sample = generate(p)
            except StoryError as err:
                print(err)
                return
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
