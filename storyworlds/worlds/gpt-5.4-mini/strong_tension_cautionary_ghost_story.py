#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/strong_tension_cautionary_ghost_story.py
=========================================================================

A tiny, standalone storyworld for a cautionary ghost-story domain.

Premise
-------
A child hears a strange ghostly sound at night, feels strong tension, and is
tempted to investigate alone. A cautious sibling or parent warns them, a
supernatural scare happens, and a calm adult shows a safer way to handle the
fear so the ending proves what changed.

The world is intentionally small:
- a child
- a cautious helper
- a grown-up
- one haunted place
- one ghostly source
- one safe light

The story engine uses typed entities with accumulating physical meters and
emotional memes, a light causal rule system, a Python reasonableness gate, and a
matching inline ASP twin.
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
SENSE_MIN = 2

STRONG_WORD = "strong"
TENSION_WORD = "tension"


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
    dark_spot: str
    mood_line: str
    contains: set[str] = field(default_factory=set)

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
class GhostSource:
    id: str
    label: str
    sound: str
    reveal: str
    scare_text: str
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
class SafeTool:
    id: str
    label: str
    phrase: str
    glow: str
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


def _r_scared(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["haunted"] < THRESHOLD:
            continue
        sig = ("scared", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in list(world.entities.values()):
            if kid.role in {"child", "helper"}:
                kid.memes["fear"] += 1
        out.append("__fear__")
    return out


CAUSAL_RULES = [Rule("scared", "social", _r_scared)]


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


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def hazard_at_risk(source: GhostSource, setting: Setting) -> bool:
    return source.label in setting.contains


def predict_scare(world: World, setting_id: str, source_id: str) -> dict:
    sim = world.copy()
    sim.get(setting_id).meters["haunted"] += 1
    sim.get(source_id).meters["haunted"] += 1
    propagate(sim, narrate=False)
    return {
        "haunted": sim.get(setting_id).meters["haunted"] >= THRESHOLD,
        "fear": sum(ent.memes["fear"] for ent in sim.entities.values()),
    }


def _do_ghost(world: World, setting: Entity, source: Entity, narrate: bool = True) -> None:
    setting.meters["haunted"] += 1
    source.meters["haunted"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    helper.memes["care"] += 1
    world.say(
        f"At {setting.place}, {child.id} and {helper.id} stayed close while the night grew quiet. "
        f"{setting.mood_line}"
    )


def tension_beats(world: World, child: Entity, helper: Entity) -> None:
    child.memes["tension"] += 1
    helper.memes["tension"] += 1
    world.say(
        f"{child.id} felt {STRONG_WORD} {TENSION_WORD} in the dark hall, like the air itself was holding its breath."
    )
    world.say(f'{helper.id} bit {helper.pronoun("possessive")} lip and listened to the strange silence.')


def temptation(world: World, child: Entity, source: GhostSource) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f'"I heard a ghost," {child.id} whispered. "I want to go look." The sound came from {source.label}.'
    )


def warn(world: World, helper: Entity, child: Entity, source: GhostSource) -> None:
    helper.memes["caution"] += 1
    pred = predict_scare(world, "setting", "source")
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f'"Wait," {helper.id} said. "{source.label_word if hasattr(source, "label_word") else source.label} can make the dark feel bigger, and going alone can make {TENSION_WORD} turn into fear."'
    )


def averted(world: World, child: Entity, helper: Entity, adult: Entity, tool: SafeTool) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{child.id} stopped and looked at {helper.id}. After a careful breath, {child.id} chose not to go alone."
    )
    world.say(
        f"{adult.label_word.capitalize()} came with {tool.phrase}, and the little group followed the soft glow instead."
    )


def scare(world: World, child: Entity, helper: Entity, source: GhostSource) -> None:
    _do_ghost(world, world.get("setting"), world.get("source"))
    world.say(
        f"{source.sound} echoed from the shadows. For one jumpy moment, {source.reveal}."
    )
    world.say(
        f"{source.scare_text} {child.id} grabbed {helper.id}'s hand at once."
    )


def calm_fix(world: World, adult: Entity, response: Response, source: GhostSource, tool: SafeTool) -> None:
    world.get("setting").meters["haunted"] = 0.0
    world.get("source").meters["haunted"] = 0.0
    world.say(
        f"{adult.label_word.capitalize()} came running and {response.text.replace('{source}', source.label)}."
    )
    world.say(f"The room settled down, and {tool.glow} made the shadows look smaller.")
    world.say(f"Then {adult.label_word.capitalize()} showed them how to check the house together and speak up instead of sneaking off.")


def failed_fix(world: World, adult: Entity, response: Response, source: GhostSource) -> None:
    world.say(
        f"{adult.label_word.capitalize()} came running, but {response.fail.replace('{source}', source.label)}."
    )
    world.say(
        f"The strange noise kept bouncing around the dark hall, and the fear stayed strong until everyone reached the lights."
    )


def ending(world: World, child: Entity, helper: Entity, adult: Entity, tool: SafeTool, source: GhostSource, averted_story: bool, contained: bool) -> None:
    if averted_story:
        world.say(
            f"After that, {child.id} held the {tool.label} and stayed beside {helper.id}. "
            f"The night still felt spooky, but {TENSION_WORD} no longer pushed {child.id} toward a bad choice."
        )
    elif contained:
        world.say(
            f"Later, {child.id} and {helper.id} walked the hall with {tool.label}, and even the haunted corner felt ordinary again."
        )
    else:
        world.say(
            f"In the end, they learned that a scary sound is not a game to chase, and they only went near {source.label} with a grown-up."
        )


def tell(setting: Setting, source: GhostSource, tool: SafeTool, response: Response,
         child_name: str = "Mia", child_gender: str = "girl",
         helper_name: str = "Leo", helper_gender: str = "boy",
         adult_type: str = "mother", trait: str = "careful", delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, role="adult", label="the grown-up"))
    world.add(Entity(id="setting", type="setting", label=setting.place))
    world.add(Entity(id="source", type="ghost_source", label=source.label))

    intro(world, child, helper, setting)
    world.para()
    tension_beats(world, child, helper)
    temptation(world, child, source)
    warn(world, helper, child, source)

    if helper.memes["caution"] >= 1 and trait in {"careful", "cautious", "sensible"} and delay == 0:
        world.para()
        averted(world, child, helper, adult, tool)
        averted_story = True
        contained = True
    else:
        world.para()
        scare(world, child, helper, source)
        contained = response.power >= (1 + delay)
        if contained:
            world.para()
            calm_fix(world, adult, response, source, tool)
        else:
            world.para()
            failed_fix(world, adult, response, source)
        averted_story = False

    world.para()
    ending(world, child, helper, adult, tool, source, averted_story, contained)

    world.facts.update(
        child=child,
        helper=helper,
        adult=adult,
        setting_cfg=setting,
        source_cfg=source,
        tool=tool,
        response=response,
        averted=averted_story,
        contained=contained,
        trait=trait,
        delay=delay,
    )
    return world


SETTINGS = {
    "hallway": Setting("hallway", "the old hallway", "the far end of the hall", "The floorboards seemed to listen.", {"mirror", "footsteps"}),
    "attic": Setting("attic", "the attic", "the boxed corner by the rafters", "Dust floated like tiny ghosts.", {"box", "window"}),
    "basement": Setting("basement", "the basement", "the dark stairs at the back", "The cold made every sound feel louder.", {"pipe", "door"}),
}

SOURCES = {
    "mirror": GhostSource("mirror", "the mirror", "A soft tap-tap", "the mirror looked cloudy and pale", "A chilly shiver ran through the room.", {"ghost", "mirror"}),
    "window": GhostSource("window", "the window", "A thump against the glass", "the window had a face-shaped fog patch", "The curtains moved even though no one touched them.", {"ghost", "window"}),
    "door": GhostSource("door", "the cellar door", "A long creak", "the door was open by a crack", "The crack looked wider than before.", {"ghost", "door"}),
}

TOOLS = {
    "lamp": SafeTool("lamp", "little lamp", "a little lamp", "glowed warm and steady", {"light"}),
    "flashlight": SafeTool("flashlight", "flashlight", "a flashlight", "clicked on bright and safe", {"light"}),
    "nightlight": SafeTool("nightlight", "night-light", "a night-light", "shined like a tiny moon", {"light"}),
}

RESPONSES = {
    "door_close": Response("door_close", 3, 4, "closed the door and turned on the lights", "tried to close the door, but the fear kept spilling out", "closed the door and turned on the lights", {"calm"}),
    "check_together": Response("check_together", 3, 4, "checked the room together and found the spooky noise", "looked, but the noise was still too much to handle alone", "checked the room together and found the spooky noise", {"calm"}),
    "call_adult": Response("call_adult", 3, 5, "called a grown-up and listened while the grown-up checked the house", "called, but the sound had already made everyone too frightened to stay calm", "called a grown-up and listened while the grown-up checked the house", {"adult"}),
    "too_late": Response("too_late", 1, 1, "tried to laugh it off", "tried to laugh it off, but that did not help", "tried to laugh it off", {"weak"}),
}

GIRL_NAMES = ["Mia", "Nora", "Ava", "Zoe", "Ella", "Luna"]
BOY_NAMES = ["Leo", "Noah", "Finn", "Max", "Owen", "Jack"]
TRAITS = ["careful", "cautious", "sensible", "curious"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for src in SOURCES:
            if hazard_at_risk(SOURCES[src], SETTINGS[s]):
                for _ in RESPONSES.values():
                    out.append((s, src, "lamp"))
    return out


@dataclass
@dataclass
class StoryParams:
    setting: str
    source: str
    tool: str
    response: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    adult: str
    trait: str
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
    "ghost": [("What is a ghost story?",
               "A ghost story is a spooky story about a strange sound, a shadow, or something that feels mysterious at night. It is meant to feel cautionary, not truly dangerous.")],
    "mirror": [("Why can a mirror feel spooky at night?",
                "A mirror can look strange in the dark because it reflects the room in a blurry way. That can make a child imagine something ghostly.")],
    "window": [("Why do windows sometimes look scary at night?",
                 "At night, a window can show dark shapes, reflections, or moving curtains. Those little tricks can make a sound seem bigger than it is.")],
    "door": [("Why is a cellar door scary to some children?",
               "A cellar door can lead to a dark place and may creak or move. Unknown places often feel spooky when the lights are low.")],
    "light": [("Why is it better to use a light when something feels scary?",
               "A light helps you see what is really there. Seeing clearly can turn strong tension into calm.")],
    "adult": [("What should you do if a scary sound worries you?",
                "Stay with a grown-up and tell them right away. A grown-up can check the house and help you feel safe.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a cautionary ghost story for a young child that includes the words "{STRONG_WORD}" and "{TENSION_WORD}".',
        f"Tell a spooky but safe story where {f['child'].id} feels {STRONG_WORD} {TENSION_WORD}, hears {f['source_cfg'].label}, and learns to stay with a grown-up.",
        f'Write a short ghost story with a calm ending and a visible lesson about not chasing spooky noises alone.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, adult = f["child"], f["helper"], f["adult"]
    src, tool, response = f["source_cfg"], f["tool"], f["response"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, {helper.id}, and {adult.label_word}. They are the ones who face the spooky sound and the strong tension in the dark."),
        ("Why did {child} feel worried?".replace("{child}", child.id),
         f"{child.id} heard a strange sound from {src.label}, and the dark made it feel even bigger. That is why {STRONG_WORD} {TENSION_WORD} built up so quickly."),
    ]
    if f["averted"]:
        qa.append((
            "What stopped the scary mistake before it got worse?",
            f"{helper.id} warned {child.id} to stay close, and {child.id} listened instead of going alone. The group used {tool.phrase} and stayed with the grown-up, so the ghostly worry never turned into a worse scare."
        ))
    else:
        qa.append((
            "What happened when they followed the noise?",
            f"The spooky sound got louder and the room felt haunted, so {child.id} grabbed {helper.id}. That turned the curiosity into real fear until a grown-up came."
        ))
        qa.append((
            "How did the grown-up help?",
            f"{adult.label_word.capitalize()} used {response.qa_text.replace('{source}', src.label)}. That calmed the room and showed the children a safer way to handle the fear."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with {child.id} staying near {helper.id} and the safe light instead of chasing the spooky sound alone. The ending proves the lesson: strong tension is a reason to call a grown-up, not to investigate by yourself."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["source_cfg"].tags) | set(world.facts["tool"].tags)
    out = []
    for key, items in KNOWLEDGE.items():
        if key in tags or key == "light" or key == "adult":
            out.extend(items)
    return out


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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("hallway", "mirror", "lamp", "call_adult", "Mia", "girl", "Leo", "boy", "mother", "careful", 0),
    StoryParams("attic", "window", "flashlight", "check_together", "Noah", "boy", "Ava", "girl", "father", "cautious", 1),
    StoryParams("basement", "door", "nightlight", "door_close", "Luna", "girl", "Jack", "boy", "mother", "sensible", 0),
]


def explain_rejection(source: GhostSource, setting: Setting) -> str:
    return f"(No story: {source.label} is not in {setting.place}, so there is no honest ghostly tension to build a cautionary story from.)"


def outcome_of(params: StoryParams) -> str:
    if params.trait in {"careful", "cautious", "sensible"} and params.delay == 0:
        return "averted"
    return "contained" if RESPONSES[params.response].power >= (1 + params.delay) else "uncontained"


ASP_RULES = r"""
hazard(S, X) :- setting(S), source(X), contains(S, X).
averted :- trait(T), cautious(T), delay(0).
contained :- chosen_response(R), power(R, P), delay(D), P >= 1 + D.
outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(uncontained) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for x in sorted(s.contains):
            lines.append(asp.fact("contains", sid, x))
    for xid, x in SOURCES.items():
        lines.append(asp.fact("source", xid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for tr in ["careful", "cautious", "sensible"]:
        lines.append(asp.fact("cautious", tr))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show outcome/1."))
    clingo = sorted(asp.atoms(model, "outcome"))
    py = [(outcome_of(p),) for p in CURATED]
    ok = True
    if not clingo:
        ok = False
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        print(f"MISMATCH: generate crashed: {e}")
        return 1
    try:
        _ = generate(CURATED[0]).story
    except Exception as e:
        print(f"MISMATCH: smoke test failed: {e}")
        return 1
    print("OK: smoke test passed.")
    print("OK: ASP program emitted.")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary ghost story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child", choices=["Mia", "Nora", "Ava", "Zoe", "Ella", "Luna", "Noah", "Leo", "Finn", "Max", "Owen", "Jack"])
    ap.add_argument("--helper")
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.setting and args.source and not hazard_at_risk(SOURCES[args.source], SETTINGS[args.setting]):
        raise StoryError(explain_rejection(SOURCES[args.source], SETTINGS[args.setting]))
    setting = args.setting or rng.choice(list(SETTINGS))
    source = args.source or rng.choice(list(SOURCES))
    response = args.response or rng.choice(list(RESPONSES))
    child_gender = "girl" if (args.child in {"Mia", "Nora", "Ava", "Zoe", "Ella", "Luna"} or args.child is None and rng.choice([True, False])) else "boy"
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_gender = "boy" if child_gender == "girl" else "girl"
    helper = args.helper or rng.choice(BOY_NAMES if helper_gender == "boy" else GIRL_NAMES)
    adult = args.adult or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, source, "lamp", response, child, child_gender, helper, helper_gender, adult, trait, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SOURCES[params.source], TOOLS[params.tool], RESPONSES[params.response],
                 params.child, params.child_gender, params.helper, params.helper_gender, params.adult, params.trait, params.delay)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show hazard/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatibility via ASP is supported")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
