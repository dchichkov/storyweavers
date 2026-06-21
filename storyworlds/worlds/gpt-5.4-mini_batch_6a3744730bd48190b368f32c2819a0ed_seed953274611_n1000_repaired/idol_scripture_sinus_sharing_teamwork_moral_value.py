#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/idol_scripture_sinus_sharing_teamwork_moral_value.py
====================================================================================

A small ghost-story storyworld built from the seed words:

- idol
- scripture
- sinus

It also centers:
- sharing
- teamwork
- moral value

The story world is a child-safe spooky domain: a couple of kids hear a ghostly
rattle in an old house, find an idol and a dusty scripture, and learn that a
kind shared effort is better than fear or greed. A sneezy sinus tickle is part
of the tension beat and helps move the plot toward the reveal.

The script follows the shared Storyweavers contract:
- standalone stdlib script
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily inside ASP helpers
- provides StoryParams, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
SPIRIT_LIMIT = 2.0


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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    mood: str
    rooms: list[str] = field(default_factory=list)
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
class Relic:
    id: str
    label: str
    sacred: bool = False
    dusty: bool = True
    murmurs: bool = False
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
class Book:
    id: str
    label: str
    kind: str = "scripture"
    revealing: bool = True
    old: bool = True
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
class Action:
    id: str
    verb: str
    risk_word: str
    shared_tool: str
    moral_move: str
    result_word: str
    spirit_gain: int = 1
    success: bool = True
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
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


def _r_spirit(world: World) -> list[str]:
    out: list[str] = []
    idol = world.entities.get("idol")
    if not idol or idol.meters["dust"] < THRESHOLD:
        return out
    sig = ("spirit", "idol")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if "ghost" in world.entities:
        world.get("ghost").meters["restless"] += 1
    for c in world.characters():
        c.memes["fear"] += 1
    out.append("__spirit__")
    return out


def _r_sharing(world: World) -> list[str]:
    out: list[str] = []
    if "lantern" not in world.entities:
        return out
    lantern = world.get("lantern")
    if lantern.meters["shared"] < THRESHOLD:
        return out
    sig = ("sharing", "lantern")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for c in world.characters():
        c.memes["trust"] += 1
        c.memes["teamwork"] += 1
    out.append("The lantern glow steadied their hands.")
    return out


def _r_scripture(world: World) -> list[str]:
    out: list[str] = []
    if "scripture" not in world.entities:
        return out
    s = world.get("scripture")
    if s.meters["read"] < THRESHOLD:
        return out
    sig = ("scripture", "read")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for c in world.characters():
        c.memes["calm"] += 1
    out.append("The old words made the room feel less cold.")
    return out


CAUSAL_RULES = [Rule("spirit", "supernatural", _r_spirit),
                Rule("sharing", "social", _r_sharing),
                Rule("scripture", "social", _r_scripture)]


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


def good_combo(place: Place, action: Action) -> bool:
    return place.id in PLACES and action.id in ACTIONS


def valid_combos() -> list[tuple[str, str]]:
    return [(p, a) for p in PLACES for a in ACTIONS if good_combo(PLACES[p], ACTIONS[a])]


def predict(world: World, action: Action) -> dict:
    sim = world.copy()
    do_action(sim, sim.get("child1"), action, narrate=False)
    return {
        "spirit": sim.get("idol").meters["dust"] >= THRESHOLD,
        "fear": sum(c.memes["fear"] for c in sim.characters()),
    }


def do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    idol = world.get("idol")
    scripture = world.get("scripture")
    lantern = world.get("lantern")
    actor.memes["curiosity"] += 1
    idol.meters["dust"] += 1
    scripture.meters["read"] += 1
    lantern.meters["shared"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        world.say(f"{actor.id} tried to {action.verb} near the old idol.")


def haunt(world: World) -> None:
    ghost = world.get("ghost")
    ghost.meters["restless"] += 1
    world.say("A thin ghostly rattle slipped through the hall.")


def introduce(world: World, a: Entity, b: Entity, place: Place) -> None:
    world.say(
        f"On a gray evening, {a.id} and {b.id} crept into {place.label}, where "
        f"every hallway seemed to hold its breath."
    )
    world.say(
        f"At the center of the room stood an old idol, and beside it lay a "
        f"dusty scripture wrapped in a faded cloth."
    )


def concern(world: World, b: Entity, action: Action) -> None:
    b.memes["worry"] += 1
    world.say(
        f'{b.id} touched {b.pronoun("possessive")} nose and sniffled. '
        f'"My sinus feels all tickly," {b.pronoun()} whispered. '
        f'"We should be careful with that dusty idol."'
    )


def tempt(world: World, a: Entity, action: Action) -> None:
    a.memes["want"] += 1
    world.say(
        f'{a.id} leaned closer. "I want to {action.verb}, even if the room feels '
        f"spooky," f' {a.pronoun()} said.'
    )


def warn(world: World, b: Entity, a: Entity, action: Action) -> None:
    pred = predict(world, action)
    if pred["spirit"]:
        world.facts["predicted_spirit"] = True
    world.say(
        f'{b.id} held up the scripture. "Let’s read the old words first," '
        f'{b.pronoun()} said. "This place wants us to share, not grab."'
    )


def share_tools(world: World, a: Entity, b: Entity) -> None:
    lantern = world.get("lantern")
    lantern.meters["shared"] += 1
    a.memes["sharing"] += 1
    b.memes["sharing"] += 1
    world.say(
        f"{a.id} handed the lantern to {b.id}, and {b.id} passed the scripture "
        f"back so they could both hold it."
    )


def team_fix(world: World, a: Entity, b: Entity, action: Action) -> None:
    idol = world.get("idol")
    scripture = world.get("scripture")
    lantern = world.get("lantern")
    idol.meters["dust"] = 0.0
    scripture.meters["read"] += 1
    lantern.meters["shared"] += 1
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1
    world.say(
        f"Together they brushed the dust from the idol, then read the scripture "
        f"aloud by lantern light."
    )
    world.say(
        f"The room grew quiet. The ghostly rattle softened, like a sigh that had "
        f"finally found its way home."
    )


def moral_turn(world: World, a: Entity, b: Entity) -> None:
    for c in (a, b):
        c.memes["moral"] += 1
    world.say(
        "They learned that a shared hand is braver than a greedy one, and that "
        "doing the right thing can calm even a haunted house."
    )
    world.say(
        "When they left, the idol stayed on its stand, the scripture stayed open, "
        "and the lantern made a gold path to the door."
    )


def tell(place: Place, action: Action, hero1: str = "Mina", hero2: str = "Owen",
         ghost_name: str = "the ghost") -> World:
    world = World()
    a = world.add(Entity(id=hero1, kind="character", type="girl", role="child"))
    b = world.add(Entity(id=hero2, kind="character", type="boy", role="child"))
    world.add(Entity(id="ghost", kind="character", type="spirit", label=ghost_name))
    world.add(Entity(id="idol", type="relic", label="the idol"))
    world.add(Entity(id="scripture", type="book", label="the scripture"))
    world.add(Entity(id="lantern", type="thing", label="the lantern"))
    world.facts["place"] = place
    world.facts["action"] = action

    introduce(world, a, b, place)
    world.para()
    haunt(world)
    concern(world, b, action)
    tempt(world, a, action)
    warn(world, b, a, action)
    share_tools(world, a, b)
    world.para()
    do_action(world, a, action)
    team_fix(world, a, b, action)
    moral_turn(world, a, b)

    world.facts.update(
        hero1=a,
        hero2=b,
        idol=world.get("idol"),
        scripture=world.get("scripture"),
        lantern=world.get("lantern"),
        outcome="shared",
    )
    return world


PLACES = {
    "old_house": Place(id="old_house", label="the old house", mood="hushed", rooms=["hall", "attic"]),
    "chapel": Place(id="chapel", label="the little chapel", mood="quiet", rooms=["pew", "rear room"]),
    "museum": Place(id="museum", label="the silent museum", mood="echoing", rooms=["gallery", "storage"]),
}

ACTIONS = {
    "brush": Action(id="brush", verb="brush away the dust", risk_word="dust", shared_tool="lantern", moral_move="share", result_word="calm"),
    "lift": Action(id="lift", verb="lift the idol carefully", risk_word="idol", shared_tool="scripture", moral_move="teamwork", result_word="reveal"),
    "read": Action(id="read", verb="read the scripture aloud", risk_word="scripture", shared_tool="lantern", moral_move="listen", result_word="comfort"),
}

@dataclass
class StoryParams:
    place: str
    action: str
    hero1: str
    hero1_gender: str
    hero2: str
    hero2_gender: str
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
    StoryParams(place="old_house", action="brush", hero1="Mina", hero1_gender="girl",
                hero2="Owen", hero2_gender="boy", seed=7),
    StoryParams(place="chapel", action="read", hero1="Nia", hero1_gender="girl",
                hero2="Leo", hero2_gender="boy", seed=11),
    StoryParams(place="museum", action="lift", hero1="Iris", hero1_gender="girl",
                hero2="Sam", hero2_gender="boy", seed=13),
]


KNOWLEDGE = {
    "idol": [("What is an idol?",
              "An idol is an object people notice or honor, sometimes because it feels special or important.")],
    "scripture": [("What is scripture?",
                   "Scripture is holy writing. People read it carefully because they think it teaches important truths.")],
    "sinus": [("What is a sinus?",
               "A sinus is a hollow space inside your head that can get stuffy or tickly when you have a cold or dust in your nose.")],
    "sharing": [("What does sharing mean?",
                 "Sharing means letting other people use, hold, or enjoy something too.")],
    "teamwork": [("What is teamwork?",
                  "Teamwork means people help each other and do a job together.")],
    "moral_value": [("What is a moral value?",
                     "A moral value is a good lesson about how to act, like being kind, honest, or fair.")],
    "ghost": [("What is a ghost in a story?",
               "A ghost is a spooky character that can make a story feel mysterious, but it is usually part of the tale and not real life.")],
}


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a ghost story for young children that includes an idol, scripture, and sinus, and ends with sharing and teamwork.",
        f"Tell a spooky but gentle story where {world.facts['hero1'].id} and {world.facts['hero2'].id} use scripture and a lantern to deal with a haunted idol.",
        "Make the story teach a moral value: that sharing and working together is better than taking something alone.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    a = world.facts["hero1"]
    b = world.facts["hero2"]
    action = world.facts["action"]
    qa = [
        ("Who is the story about?",
         f"It is about {a.id} and {b.id}, two children who went into the old place together. They faced a spooky moment, but they also helped each other through it."),
        ("What made the room feel spooky?",
         f"The old idol and the dusty scripture made the room feel eerie, and the ghostly rattle made it even stranger. The sinus tickle also made {b.id} worry because dust was in the air."),
        ("What did the children do to solve the problem?",
         f"They shared the lantern, read the scripture, and worked together to brush the dust away. That teamwork calmed the room and gave the story a gentle ending."),
        ("What moral value did they learn?",
         f"They learned that sharing and teamwork are the right way to handle a hard moment. The story shows that doing good together can quiet fear and make the place peaceful."),
    ]
    if world.facts.get("outcome") == "shared":
        qa.append((
            f"What did {a.id} and {b.id} do with the idol and scripture?",
            f"They handled the idol carefully and read the scripture together instead of taking turns alone. That shared effort showed respect and helped them do the job safely."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"idol", "scripture", "sinus", "sharing", "teamwork", "moral_value", "ghost"}
    out: list[tuple[str, str]] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            out.extend(items)
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
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_params() -> list[tuple[str, str]]:
    return valid_combos()


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("shared_tool", aid, a.shared_tool))
        lines.append(asp.fact("moral_move", aid, a.moral_move))
    lines.append(asp.fact("threshold", int(THRESHOLD)))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,A) :- place(P), action(A).
spooky(A) :- action(A).
shared_story(A) :- action(A), shared_tool(A,_).
moral_story(A) :- action(A), moral_move(A,_).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_params())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:  # pragma: no cover - defensive
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with idol, scripture, and sinus.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--hero1")
    ap.add_argument("--hero2")
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
    combos = valid_combos()
    if args.place and args.action and (args.place, args.action) not in combos:
        raise StoryError("That place and action do not make a workable ghost story.")
    if not combos:
        raise StoryError("No valid combinations available.")
    place, action = rng.choice(combos)
    hero1 = args.hero1 or rng.choice(["Mina", "Nia", "Iris", "Lina", "June"])
    hero2 = args.hero2 or rng.choice([n for n in ["Owen", "Leo", "Sam", "Noah", "Ezra"] if n != hero1])
    return StoryParams(place=place, action=action, hero1=hero1, hero1_gender="girl",
                       hero2=hero2, hero2_gender="boy")


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.action not in ACTIONS:
        raise StoryError(f"Unknown action: {params.action}")
    world = tell(PLACES[params.place], ACTIONS[params.action], params.hero1, params.hero2)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/2.\n#show spooky/1.\n#show shared_story/1.\n#show moral_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program(show="#show valid/2."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print("\n".join(f"{p} {a}" for p, a in vals))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
