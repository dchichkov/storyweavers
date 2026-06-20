#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/popular_ize_murky_humor_kindness_bedtime_story.py
=================================================================================

A tiny bedtime story world built from the seed words "popular-ize" and "murky",
with Humor and Kindness as the main narrative instruments.

The domain is small and classical: a child wants to make a silly bedtime idea
more popular with a younger sibling and a stuffed toy, but the idea becomes
murky when the child adds too much dark paint to the page. A kind grown-up helps
turn the mess into a gentle joke, and the ending image proves the change by
showing a calm, cozy bedtime scene.

The script follows the Storyweavers contract:
- typed entities with meters and memes
- simulated state drives prose
- a Python reasonableness gate plus inline ASP twin
- three QA sets derived from world state
- standard CLI flags: -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, --show-asp
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
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
class Theme:
    id: str
    bedtime_place: str
    cozy_scene: str
    story_goal: str
    ending_image: str

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
class Ink:
    id: str
    label: str
    phrase: str
    murky: bool = True
    spreads: bool = True
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
class Canvas:
    id: str
    label: str
    phrase: str
    the: str
    near: str
    murky_mark: bool = False
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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


def _r_murky(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["murky"] < THRESHOLD:
            continue
        sig = ("murky", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "room" in world.entities:
            world.get("room").meters["mess"] += 1
        for ch in world.characters():
            ch.memes["uncertainty"] += 1
        out.append("__murky__")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    for ch in world.characters():
        if ch.memes["humor"] < THRESHOLD:
            continue
        sig = ("laugh", ch.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ch.memes["joy"] += 1
        out.append(f"{ch.id} giggled softly.")
    return out


CAUSAL_RULES = [Rule("murky", "physical", _r_murky), Rule("laugh", "social", _r_laugh)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def reasonableness_ok(ink: Ink, canvas: Canvas) -> bool:
    return ink.murky and canvas.label in {"paper", "storybook page", "bedtime page"}


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def severity(canvas: Canvas, delay: int) -> int:
    return 1 + delay + (1 if canvas.murky_mark else 0)


def contained(response: Response, canvas: Canvas, delay: int) -> bool:
    return response.power >= severity(canvas, delay)


def _do_murky(world: World, canvas_ent: Entity, narrate: bool = True) -> None:
    canvas_ent.meters["murky"] += 1
    canvas_ent.meters["smeared"] += 1
    propagate(world, narrate=narrate)


def predict_murk(world: World, canvas_id: str) -> dict:
    sim = world.copy()
    _do_murky(sim, sim.get(canvas_id), narrate=False)
    return {
        "murky": sim.get(canvas_id).meters["murky"] >= THRESHOLD,
        "mess": sim.get("room").meters["mess"] if "room" in sim.entities else 0,
    }


def setup(world: World, child: Entity, sibling: Entity, theme: Theme) -> None:
    child.memes["curiosity"] += 1
    sibling.memes["anticipation"] += 1
    world.say(
        f"At bedtime, {child.id} and {sibling.id} sat on the rug in {theme.bedtime_place}. "
        f"{theme.cozy_scene}"
    )
    world.say(
        f'{child.id} had an idea: "{theme.story_goal}," {child.pronoun()} whispered, '
        f"while the clock ticked like a sleepy beetle."
    )


def tempt(world: World, child: Entity, ink: Ink) -> None:
    child.memes["humor"] += 1
    world.say(
        f'{child.id} grinned. "I can popular-ize this joke with {ink.label}!" '
        f"That sounded clever at first."
    )


def warn(world: World, sibling: Entity, child: Entity, ink: Ink, canvas: Canvas, parent: Entity) -> None:
    pred = predict_murk(world, "page")
    sibling.memes["kindness"] += 1
    world.facts["predicted_mess"] = pred["mess"]
    world.say(
        f'{sibling.id} tilted {sibling.pronoun("possessive")} head. "{child.id}, '
        f"the page is getting murky. {parent.label_word.capitalize()} will need "
        f"to help if it gets darker, and bedtime will turn messy."
    )


def defy(world: World, child: Entity, sibling: Entity, ink: Ink) -> None:
    child.memes["boldness"] += 1
    world.say(
        f'"Just one more swirly line," {child.id} said, and {child.pronoun()} '
        f"dipped the brush into {ink.phrase}."
    )


def murk(world: World, page: Entity, ink: Ink, canvas: Canvas) -> None:
    _do_murky(world, page)
    page.meters["murky_mark"] += 1
    canvas.murky_mark = True
    world.say(
        f"The brush went swish, and soon {canvas.the} looked muddy and dark, "
        f"like a cloud that had slipped into a puddle."
    )


def alarm(world: World, sibling: Entity, child: Entity, parent: Entity, canvas: Canvas) -> None:
    world.say(
        f'"Oh no!" {sibling.id} laughed, then covered {sibling.pronoun("possessive")} mouth. '
        f'"{parent.label_word.capitalize()}! The page got murky!"'
    )
    world.say(f'"{parent.label_word.capitalize()}!"')


def rescue(world: World, parent: Entity, response: Response, page: Entity, canvas: Canvas) -> None:
    page.meters["murky"] = 0.0
    world.get("room").meters["mess"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came in smiling. In one calm motion "
        f"{parent.pronoun()} {response.text.replace('{target}', canvas.label)}."
    )
    world.say(
        f"The dark smudges softened, and the room felt cozy again."
    )


def lesson(world: World, parent: Entity, child: Entity, sibling: Entity, ink: Ink) -> None:
    for kid in (child, sibling):
        kid.memes["kindness"] += 1
        kid.memes["relief"] += 1
        kid.memes["humor"] += 1
    world.say("For a tiny moment, everyone just breathed.")
    world.say(
        f"Then {parent.label_word.capitalize()} tucked the blanket higher and said, "
        f'"Being funny is wonderful, but being kind matters too. '
        f"We can make a joke without making a mess."
    )
    world.say(
        f'"We can?" {child.id} asked.'
    )
    world.say(
        f'"Yes," smiled {parent.label_word.capitalize()}, "and we can still '
        f'popular-ize it -- the gentle way."'
    )


def afterglow(world: World, parent: Entity, child: Entity, sibling: Entity, theme: Theme) -> None:
    for kid in (child, sibling):
        kid.memes["joy"] += 1
        kid.memes["peace"] += 1
    world.say(
        f"Then {parent.label_word.capitalize()} opened a clean page, and together "
        f"they made the joke smaller, brighter, and easier to read."
    )
    world.say(
        f'{child.id} told the punchline, {sibling.id} giggled, and even the teddy bear '
        f"looked as if it was trying not to laugh."
    )
    world.say(theme.ending_image)


def story_setup(world: World, child: Entity, sibling: Entity, theme: Theme) -> None:
    world.say(
        f"By the little lamp, {child.id} and {sibling.id} built a bedtime world "
        f"of pillows, blankets, and whispers. {theme.cozy_scene}"
    )


def tell(theme: Theme, ink: Ink, canvas: Canvas, response: Response,
         child_name: str = "Mia", child_gender: str = "girl",
         sibling_name: str = "Theo", sibling_gender: str = "boy",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    sibling = world.add(Entity(id=sibling_name, kind="character", type=sibling_gender, role="sibling"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    room = world.add(Entity(id="room", type="room", label="the room"))
    page = world.add(Entity(id="page", type="thing", label=canvas.label))

    story_setup(world, child, sibling, theme)
    setup(world, child, sibling, theme)
    world.para()
    tempt(world, child, ink)
    warn(world, sibling, child, ink, canvas, parent)

    world.para()
    defy(world, child, sibling, ink)
    murk(world, page, ink, canvas)
    alarm(world, sibling, child, parent, canvas)

    world.para()
    if contained(response, canvas, delay):
        rescue(world, parent, response, page, canvas)
        lesson(world, parent, child, sibling, ink)
        world.para()
        afterglow(world, parent, child, sibling, theme)
        outcome = "contained"
    else:
        world.say(
            f"{parent.label_word.capitalize()} had to hurry and the little lamp flickered, "
            f"but the page stayed too dark."
        )
        world.say(
            f"Still, everyone stayed safe, and the family decided to save the joke for a cleaner day."
        )
        outcome = "burned"

    world.facts.update(
        child=child,
        sibling=sibling,
        parent=parent,
        room=room,
        page=page,
        theme=theme,
        ink=ink,
        canvas=canvas,
        response=response,
        outcome=outcome,
        delay=delay,
    )
    return world


THEMES = {
    "bedtime": Theme(
        "bedtime",
        "the little bedroom",
        "A moon sticker glowed on the wall, a blanket made a soft cave, and a teddy bear sat guard by the pillow.",
        "popular-ize the silliest joke in the room",
        "The moon sticker still glowed, the teddy bear still sat guard, and the room felt calm and cozy again.",
    ),
    "nursery": Theme(
        "nursery",
        "the nursery corner",
        "Tiny socks hung from the chair, a night-light made a gold puddle on the floor, and the crib waited like a boat.",
        "popular-ize a sleepy little joke",
        "The night-light glowed, the socks stayed tidy, and the crib looked ready for dreams.",
    ),
    "bunkroom": Theme(
        "bunkroom",
        "the bunkroom",
        "Two pillows were stacked like clouds, a moon poster watched from the wall, and the blanket made a tent of warmth.",
        "popular-ize a bedtime riddle",
        "The moon poster stayed bright, the pillows stayed fluffy, and the bunkroom felt safe for sleep.",
    ),
}

INKS = {
    "marker": Ink("marker", "a dark marker", "a dark marker", murky=True, spreads=True, tags={"murky", "humor"}),
    "paint": Ink("paint", "inky paint", "inky paint", murky=True, spreads=True, tags={"murky"}),
    "charcoal": Ink("charcoal", "soft charcoal", "soft charcoal", murky=True, spreads=True, tags={"murky"}),
}

CANVASES = {
    "page": Canvas("page", "paper", "a bedtime page", "the page", "the page", tags={"paper"}),
    "storybook": Canvas("storybook", "storybook page", "a storybook page", "the storybook page", "the storybook page", tags={"paper"}),
}

RESPONSES = {
    "wipe": Response("wipe", 3, 3, "wiped the page clean with a damp cloth and a gentle smile", "tried to wipe the page, but the murk was too thick", "wiped the page clean", tags={"kindness"}),
    "fresh_page": Response("fresh_page", 3, 4, "turned to a fresh page, set the dirty one aside, and began again", "tried to begin again, but the page stayed too muddy", "turned to a fresh page", tags={"kindness"}),
    "lamp": Response("lamp", 2, 2, "turned the lamp a little brighter so everyone could see the joke clearly", "lifted the lamp, but the murk still hid the words", "turned the lamp brighter", tags={"humor"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Theo", "Ben", "Sam", "Finn", "Leo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme in THEMES:
        for ink in INKS:
            for canvas in CANVASES:
                if reasonableness_ok(INKS[ink], CANVASES[canvas]):
                    combos.append((theme, ink, canvas))
    return combos


@dataclass
@dataclass
class StoryParams:
    theme: str
    ink: str
    canvas: str
    response: str
    child: str
    child_gender: str
    sibling: str
    sibling_gender: str
    parent: str
    delay: int = 0
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


KNOWLEDGE = {
    "humor": [("What is humor?",
               "Humor is something that makes people smile or laugh. A silly joke or a funny picture can be humorous.")],
    "kindness": [("What is kindness?",
                 "Kindness means being gentle, helpful, and caring toward someone else. A kind act makes things better instead of meaner.")],
    "murky": [("What does murky mean?",
               "Murky means dark, cloudy, or hard to see through. A murky puddle or page looks muddy and unclear.")],
    "paper": [("What is paper?",
               "Paper is a thin sheet made for drawing and writing on. It can hold stories, pictures, and notes.")],
    "lamp": [("What does a lamp do?",
              "A lamp gives light so people can see better when it is dark. A lamp can make a room feel cozy.")],
}
KNOWLEDGE_ORDER = ["humor", "kindness", "murky", "paper", "lamp"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a young child that includes the words "popular-ize" and "murky".',
        f"Tell a cozy story where {f['child'].id} tries to popular-ize a funny idea, but the page turns murky and a kind parent helps.",
        f'Write a gentle story about humor and kindness at bedtime, with a murky page that gets fixed calmly.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, sibling, parent = f["child"], f["sibling"], f["parent"]
    ink, canvas = f["ink"], f["canvas"]
    resp = f["response"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, {sibling.id}, and {parent.label_word}. They are the small bedtime cast who try to make a joke work."),
        ("What did {0} want to do?".format(child.id),
         f"{child.id} wanted to {f['theme'].story_goal}. {child.pronoun()} hoped the joke would make everyone smile."),
        ("Why did the page turn murky?",
         f"{child.id} used {ink.label}, and it made the page dark and cloudy. The page became harder to read because the ink spread too much."),
        ("How did the parent help?",
         f"{parent.label_word.capitalize()} came in calmly and {resp.qa_text}. That kindness fixed the problem without making anyone feel bad."),
        ("How did the story end?",
         f"It ended cozy and quiet, with the room calm again and the joke still alive. The ending image shows that humor stayed, but the mess was gone."),
    ]
    if f["outcome"] == "contained":
        qa.append((
            "What changed by the end?",
            f"The murky page was cleaned up, and the family kept the funny idea in a gentler way. The child learned that kindness can make a joke even better."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["ink"].tags) | set(world.facts["canvas"].tags) | set(world.facts["response"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("bedtime", "marker", "page", "wipe", "Mia", "girl", "Theo", "boy", "mother", 0),
    StoryParams("nursery", "paint", "storybook", "fresh_page", "Leo", "boy", "Nora", "girl", "father", 0),
    StoryParams("bunkroom", "charcoal", "page", "lamp", "Ava", "girl", "Ben", "boy", "mother", 1),
]


def explain_rejection(ink: Ink, canvas: Canvas) -> str:
    return f"(No story: {ink.label} can make a page murky, but {canvas.label} is not the right kind of surface for this gentle bedtime tale.)"


def outcome_of(params: StoryParams) -> str:
    if contained(RESPONSES[params.response], CANVASES[params.canvas], params.delay):
        return "contained"
    return "burned"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < 2).)"


ASP_RULES = r"""
murky(Page) :- ink(Ink), canvas(Page), spreads(Ink).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
contained :- chosen_response(R), power(R, P), severity(V), P >= V.
severity(V) :- chosen_canvas(C), base_severity(B), delay(D), V = B + D.
outcome(contained) :- contained.
outcome(burned) :- not contained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for i, ink in INKS.items():
        lines.append(asp.fact("ink", i))
        if ink.murky:
            lines.append(asp.fact("murky_ink", i))
        if ink.spreads:
            lines.append(asp.fact("spreads", i))
    for c in CANVASES:
        lines.append(asp.fact("canvas", c))
    for r, resp in RESPONSES.items():
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("sense", r, resp.sense))
        lines.append(asp.fact("power", r, resp.power))
    lines.append(asp.fact("sense_min", 2))
    lines.append(asp.fact("base_severity", 1))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_response", params.response),
        asp.fact("chosen_canvas", params.canvas),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_sensible()) != {r for r, rr in RESPONSES.items() if rr.sense >= 2}:
        rc = 1
        print("MISMATCH in sensible responses")
    cases = list(CURATED)
    for s in range(25):
        try:
            cases.append(resolve_params(build_parser().parse_args([]), random.Random(s)))
        except StoryError:
            continue
    if any(asp_outcome(p) != outcome_of(p) for p in cases):
        rc = 1
        print("MISMATCH in outcome model")
    try:
        _ = generate(CURATED[0]).story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about a murky joke and a kind fix.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--ink", choices=INKS)
    ap.add_argument("--canvas", choices=CANVASES)
    ap.add_argument("--response", choices=RESPONSES)
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
    if args.ink and args.canvas and not reasonableness_ok(INKS[args.ink], CANVASES[args.canvas]):
        raise StoryError(explain_rejection(INKS[args.ink], CANVASES[args.canvas]))
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.ink is None or c[1] == args.ink)
              and (args.canvas is None or c[2] == args.canvas)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, ink, canvas = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    child_gender = rng.choice(["girl", "boy"])
    child = rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    sibling_gender = "boy" if child_gender == "girl" else "girl"
    sibling = rng.choice(BOY_NAMES if sibling_gender == "boy" else GIRL_NAMES)
    if sibling == child:
        sibling = "Noah" if child != "Noah" else "Nora"
    parent = args.parent or rng.choice(["mother", "father"])
    delay = rng.randint(0, 1)
    return StoryParams(theme, ink, canvas, response, child, child_gender, sibling, sibling_gender, parent, delay)


def tell_story(params: StoryParams) -> StorySample:
    world = World()
    sample = tell(THEMES[params.theme], INKS[params.ink], CANVASES[params.canvas],
                  RESPONSES[params.response], params.child, params.child_gender,
                  params.sibling, params.sibling_gender, params.parent, params.delay)
    return StorySample(
        params=params,
        story=sample.render(),
        prompts=generation_prompts(sample),
        story_qa=[QAItem(q, a) for q, a in story_qa(sample)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(sample)],
        world=sample,
    )


def generate(params: StoryParams) -> StorySample:
    return tell_story(params)


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
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t, i, c in asp_valid_combos():
            print(f"  {t:8} {i:10} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child}: {p.ink} near {p.canvas} ({p.theme}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
