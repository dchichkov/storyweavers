#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/torch_august_rhyme_curiosity_adventure.py
========================================================================

A standalone story world for a tiny adventure tale about a curious child,
a torch, an August evening, and a rhymed map-chant that helps them find the
right path home. The world is intentionally small: one brave question, one
mistake, one smart correction, and one ending image that proves the change.

Seed words:
- torch
- august

Features:
- Rhyme
- Curiosity

Style:
- Adventure
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
    name: str
    scene: str
    path: str
    sound: str
    light_place: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Tool:
    id: str
    label: str
    glow: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Hazard:
    id: str
    label: str
    place: str
    danger: str
    spread: int
    flammable: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Verse:
    id: str
    line: str
    clue: str
    help_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
            value = defaultdict(float)
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.verse: Verse | None = None

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.verse = copy.deepcopy(self.verse)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["lost"] < THRESHOLD:
            continue
        sig = ("spook", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] += 1
        out.append(f"{ent.id} swallowed a worried breath.")
    return out


CAUSAL_RULES = [Rule("spook", "social", _r_spook)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(hazard: Hazard, setting: Setting) -> bool:
    return hazard.flammable and setting.name in {"woodland", "hill path", "old bridge", "river bend"}


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def is_contained(response: Response, hazard: Hazard, delay: int) -> bool:
    return response.power >= hazard.spread + delay


def predict_mist(world: World, hazard_id: str) -> dict:
    sim = world.copy()
    _lose_path(sim, sim.get("curious_child"), sim.verse, sim.get(hazard_id), narrate=False)
    return {"lost": sim.get("curious_child").meters["lost"] >= THRESHOLD}


def _lose_path(world: World, child: Entity, verse: Verse, hazard: Entity, narrate: bool = True) -> None:
    child.meters["lost"] += 1
    child.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, parent: Entity, setting: Setting) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"In {setting.name}, {child.id} and {parent.label_word} followed {setting.path} "
        f"under an {setting.scene}. The air felt like an adventure, and even the shadows "
        f"seemed to listen."
    )
    world.say(
        f"{child.id} loved to ask why the trail bent and why the birds sang there. "
        f"That was how the curious child kept finding new stories."
    )


def find_torch(world: World, child: Entity, tool: Tool) -> None:
    world.say(
        f"At the edge of the path, {child.id} found a {tool.label}. It gave off a soft "
        f"glow and looked perfect for a brave little explorer."
    )


def rhyme(world: World, verse: Verse) -> None:
    world.verse = verse
    world.say(
        f'{child_name(world)} tried a rhyme: "{verse.line}" '
        f'The words clicked together like stepping stones.'
    )


def child_name(world: World) -> str:
    return world.facts["child"].id


def warn(world: World, parent: Entity, child: Entity, hazard: Hazard, verse: Verse) -> None:
    pred = predict_mist(world, hazard.id)
    world.facts["predicted_lost"] = pred["lost"]
    world.say(
        f'"Careful," {parent.label_word} said. "{verse.clue} If we keep wandering, '
        f"{child.id} could lose {child.pronoun('possessive')} way near {hazard.place}."
    )


def choose(world: World, child: Entity, parent: Entity, hazard: Hazard, response: Response) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"{child.id} still leaned toward the dark turn, because curiosity tugged hard. "
        f"{child.pronoun().capitalize()} stepped forward with the {world.facts['tool'].label}."
    )


def turn_back(world: World, child: Entity, parent: Entity, verse: Verse) -> None:
    child.memes["relief"] += 1
    parent.memes["relief"] += 1
    world.say(
        f"But {child.id} looked at {parent.label_word}, listened to the rhyme again, and "
        f"laughed. The trail's mystery was exciting, but home was safer."
    )


def lose_way(world: World, child: Entity, hazard: Hazard) -> None:
    _lose_path(world, child, world.verse, world.get(hazard.id))
    world.say(
        f"The torch light wobbled, and for a moment the trail near {hazard.place} looked "
        f"the same in every direction. {child.id} had to stop and stare."
    )


def rescue(world: World, parent: Entity, response: Response, hazard: Hazard) -> None:
    world.get(hazard.id).meters["danger"] = 0
    world.say(
        f"{parent.label_word.capitalize()} came close, {response.text}."
    )
    world.say(
        f"The scary turn grew calm again, and the torch was no longer needed for searching."
    )


def ending(world: World, child: Entity, parent: Entity, tool: Tool, setting: Setting) -> None:
    world.say(
        f"In the end, {child.id} carried the {tool.label} only for the path back, while "
        f"{parent.label_word} held the map. They reached {setting.light_place} together, "
        f"and the small torch glow led them home like a star in a pocket."
    )


def rescue_fail(world: World, parent: Entity, response: Response, hazard: Hazard) -> None:
    world.get(hazard.id).meters["danger"] += 1
    world.say(f"{parent.label_word.capitalize()} tried {response.fail}.")
    world.say("The dark bend stayed confusing, so they had to leave quickly and return the next day.")


def grim_end(world: World, child: Entity, parent: Entity, setting: Setting) -> None:
    world.say(
        f"They hurried back together, tired but safe, and the August sky above {setting.name} "
        f"shimmered with quiet silver clouds. The adventure ended with both of them holding hands."
    )


@dataclass
@dataclass
class StoryParams:
    setting: str
    hazard: str
    tool: str
    verse: str
    response: str
    child: str
    child_gender: str
    parent: str
    delay: int = 0
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


SETTINGS = {
    "woodland": Setting("the woodland", "golden leaves", "the winding path", "the crickets' hush", "the lantern glade"),
    "hill path": Setting("the hill path", "high grass", "the narrow trail", "the wind's hush", "the lantern glade"),
    "old bridge": Setting("the old bridge", "river mist", "the boardwalk", "the water's hush", "the lantern glade"),
    "river bend": Setting("the river bend", "soft reeds", "the muddy turn", "the frogs' hush", "the lantern glade"),
}

HAZARDS = {
    "ditch": Hazard("ditch", "a deep ditch", "the ditch", "a hidden drop", 2, True, {"ditch"}),
    "thicket": Hazard("thicket", "a thorny thicket", "the thicket", "a prickly wall", 3, True, {"thicket"}),
    "fog": Hazard("fog", "a thick fog bank", "the fog", "a blinding mist", 2, True, {"fog"}),
}

TOOLS = {
    "torch": Tool("torch", "torch", "shone warm and steady", True, {"torch"}),
    "lantern": Tool("lantern", "lantern", "glowed like a tiny moon", True, {"lantern"}),
}

VERSES = {
    "rhyme": Verse("rhyme", "If the path turns sly, let your bright eyes try", "the rhyme can help us slow down and look", "the rhyme reminds us to be careful", {"rhyme"}),
    "couplet": Verse("couplet", "Step, then pause, and see the cause", "the words tell us to stop and think", "the couplet helps with careful choices", {"rhyme"}),
}

RESPONSES = {
    "guide_back": Response("guide_back", 3, 3, "used the torch to guide the way back by the map", "guided them, but the bend was already too confusing", "guided them back by the map", {"help"}),
    "wait": Response("wait", 2, 2, "waited beside the trail until the feeling passed", "waited, but the fog kept swallowing the path", "waited beside the trail", {"help"}),
    "call_parent": Response("call_parent", 3, 4, "called from the path and brought the parent close with the lantern", "called, but the answer came too late", "called for help and brought the parent close", {"help"}),
}

SENSE_MIN = 2

CHILD_NAMES = ["Rhy", "Milo", "Lena", "Nova", "Eden", "Sora"]
PARENTS = ["mother", "father"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for h in HAZARDS:
            for t in TOOLS:
                if hazard_at_risk(HAZARDS[h], SETTINGS[s]):
                    out.append((s, h, t))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about curiosity, rhyme, and a torch.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--verse", choices=VERSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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
    if args.hazard and args.setting and not hazard_at_risk(HAZARDS[args.hazard], SETTINGS[args.setting]):
        raise StoryError("(No story: that hazard does not fit this setting.)")
    combos = [c for c in valid_combos() if (args.setting is None or c[0] == args.setting) and (args.hazard is None or c[1] == args.hazard) and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, hazard, tool = rng.choice(sorted(combos))
    verse = args.verse or rng.choice(sorted(VERSES))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(PARENTS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, hazard, tool, verse, response, name, gender, parent, delay)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(params.child, "character", params.child_gender, role="child", traits=["curious", "adventurous"]))
    parent = world.add(Entity("Parent", "character", params.parent, label="the parent", role="parent"))
    hazard = world.add(Entity("hazard", "thing", "hazard", label=HAZARDS[params.hazard].label))
    tool = world.add(Entity("tool", "thing", "tool", label=TOOLS[params.tool].label))
    verse = VERSES[params.verse]
    response = RESPONSES[params.response]
    world.facts.update(child=child, parent=parent, hazard=hazard, tool=tool, verse=verse, response=response)
    opening(world, child, parent, world.setting)
    world.para()
    find_torch(world, child, TOOLS[params.tool])
    rhyme(world, verse)
    warn(world, parent, child, HAZARDS[params.hazard], verse)
    world.para()
    if params.delay == 0:
        turn_back(world, child, parent, verse)
        ending(world, child, parent, TOOLS[params.tool], world.setting)
        world.facts["outcome"] = "averted"
    else:
        choose(world, child, parent, HAZARDS[params.hazard], response)
        lose_way(world, child, HAZARDS[params.hazard])
        if is_contained(response, HAZARDS[params.hazard], params.delay):
            rescue(world, parent, response, HAZARDS[params.hazard])
            ending(world, child, parent, TOOLS[params.tool], world.setting)
            world.facts["outcome"] = "contained"
        else:
            rescue_fail(world, parent, response, HAZARDS[params.hazard])
            grim_end(world, child, parent, world.setting)
            world.facts["outcome"] = "burned"
    world.facts["setting"] = world.setting
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a child that includes the words "torch" and "august" and features a curious child who likes rhyme.',
        f"Tell a gentle adventure about {f['child'].id} in August, where a torch helps with the path, a rhyme matters, and a parent keeps everyone safe.",
        f"Write a story where curiosity leads to trouble on a trail, but a rhyme and a grown-up help turn it into a safe adventure.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, hazard, response = f["child"], f["parent"], f["hazard"], f["response"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id}, a curious child, and {parent.label_word}, who went along on the adventure."
        ),
        QAItem(
            question="Why did the child need help?",
            answer=f"{child.id} became unsure of the path near {hazard.label}. The dark turn and the growing worry made it important to slow down and choose a safer plan."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(QAItem(
            question="What changed at the end?",
            answer=f"{child.id} turned back before getting lost, so the adventure stayed safe. The torch ended the story as a guide for the walk home instead of a tool for risk."
        ))
    elif f["outcome"] == "contained":
        qa.append(QAItem(
            question="How was the problem solved?",
            answer=f"{parent.label_word.capitalize()} used {response.qa_text}. That brought calm back to the trail and let the two of them go home together."
        ))
    else:
        qa.append(QAItem(
            question="What happened when the plan failed?",
            answer=f"The help came too late, so {response.fail}. They still got out safely, but the adventure had to end early."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    qa = [
        QAItem("What is a torch?", "A torch is a small light that helps people see in the dark. In stories, it can be a useful adventure tool when someone is careful."),
        QAItem("Why can curiosity be helpful?", "Curiosity helps people ask questions and notice clues. It can lead to discovery when it is paired with caution."),
        QAItem("Why are rhymes useful in stories?", "Rhymes are easy to remember, so they can help a character keep track of a rule or a path."),
        QAItem("Why is August a good adventure month?", "August often feels warm and bright, with long evenings that make outdoor adventures feel lively and real."),
    ]
    return qa


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
        if e.type:
            bits.append(f"type={e.type}")
        lines.append(f"  {e.id:10} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("woodland", "ditch", "torch", "rhyme", "guide_back", "Rhy", "girl", "mother", 0),
    StoryParams("hill path", "thicket", "lantern", "couplet", "wait", "Milo", "boy", "father", 1),
    StoryParams("river bend", "fog", "torch", "rhyme", "call_parent", "Lena", "girl", "mother", 2),
]


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


def outcome_of(params: StoryParams) -> str:
    if params.delay == 0:
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], HAZARDS[params.hazard], params.delay) else "burned"


ASP_RULES = r"""
hazard(F,S) :- hazard(F), setting(S).
valid(S,H,T) :- hazard(H), setting(S), tool(T).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
outcome(averted) :- delay(0).
outcome(contained) :- delay(D), D > 0.
outcome(burned) :- delay(D), D > 1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", hid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, hazard=None, tool=None, response=None, verse=None, name=None, gender=None, parent=None, delay=None), random.Random(777)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def build_sample(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                samples.append(s)
                seen.add(s.story)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
