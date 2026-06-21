#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/anorexic_bravery_friendship_misunderstanding_ghost_story.py
======================================================================================

A standalone storyworld about two friends, a ghost rumor, and the brave moment
when they discover what is really making the spooky sound.

The domain is deliberately small and classical:
- a place with eerie nighttime details
- a real cause of the "ghost" sound
- a sensible response that can reveal and fix the cause
- a friendship bond that changes whether the children solve it themselves or go
  get a grown-up

The story always includes the word "anorexic", but only inside a correction:
someone in the rumor used that serious grown-up word carelessly, and the story
makes clear it was not the right thing to say.

Run it
------
    python storyworlds/worlds/gpt-5.4/anorexic_bravery_friendship_misunderstanding_ghost_story.py
    python storyworlds/worlds/gpt-5.4/anorexic_bravery_friendship_misunderstanding_ghost_story.py --place greenhouse --cause trapped_cat
    python storyworlds/worlds/gpt-5.4/anorexic_bravery_friendship_misunderstanding_ghost_story.py --response yell_at_ghost
    python storyworlds/worlds/gpt-5.4/anorexic_bravery_friendship_misunderstanding_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/anorexic_bravery_friendship_misunderstanding_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/anorexic_bravery_friendship_misunderstanding_ghost_story.py --verify
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class Place:
    id: str
    label: str
    opening: str
    eerie: str
    hiding_spot: str
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
class Cause:
    id: str
    label: str
    sound: str
    sight: str
    scare: int
    reveal: str
    fix_need: str
    truth: str
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
class Response:
    id: str
    label: str
    sense: int
    power: int
    handles: set[str] = field(default_factory=set)
    setup: str = ""
    solve_text: str = ""
    help_text: str = ""
    qa_text: str = ""
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
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "friend"}]

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


def _r_fear_from_rumor(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("heard_sound"):
        return out
    cause_cfg = world.facts["cause_cfg"]
    for kid in world.kids():
        sig = ("fear", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["fear"] += float(cause_cfg.scare)
        out.append("__fear__")
    world.facts["misunderstanding_active"] = True
    return out


def _r_friendship_boost(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("holding_hands"):
        return out
    leader = world.get("leader")
    friend = world.get("friend")
    sig = ("together", leader.id, friend.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    leader.memes["bravery"] += 1
    friend.memes["bravery"] += 1
    leader.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.facts["friendship_boost"] = 1
    out.append("__together__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("truth_seen"):
        return out
    for kid in world.kids():
        sig = ("relief", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["care"] += 1
        out.append("__relief__")
    world.facts["misunderstanding_active"] = False
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="fear_from_rumor", tag="emotion", apply=_r_fear_from_rumor),
    Rule(name="friendship_boost", tag="emotion", apply=_r_friendship_boost),
    Rule(name="relief", tag="emotion", apply=_r_relief),
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
        for sent in produced:
            world.say(sent)
    return produced


PLACES = {
    "greenhouse": Place(
        id="greenhouse",
        label="the old greenhouse",
        opening="At the edge of the garden stood the old greenhouse, all silver moonlight and dim glass.",
        eerie="Loose vines tapped softly on the panes.",
        hiding_spot="under a crooked bench",
        tags={"garden", "night"},
    ),
    "attic": Place(
        id="attic",
        label="the attic",
        opening="Above the sleepy house waited the attic, full of dusty beams and long shadows.",
        eerie="The roof creaked whenever the wind leaned on it.",
        hiding_spot="behind a stack of travel trunks",
        tags={"house", "night"},
    ),
    "boathouse": Place(
        id="boathouse",
        label="the boathouse",
        opening="By the dark pond stood the boathouse, smelling of rope, wood, and cold water.",
        eerie="The little boats rocked and knocked softly in the dark.",
        hiding_spot="beside an overturned rowboat",
        tags={"pond", "night"},
    ),
}

CAUSES = {
    "trapped_cat": Cause(
        id="trapped_cat",
        label="a trapped stray cat",
        sound="a thin crying sound",
        sight="two bright eyes blinking from the dark",
        scare=2,
        reveal="the lantern beam slid into the shadows and found whiskers instead of fog",
        fix_need="gentle food and a soft voice",
        truth="It had only been a frightened stray cat with a hollow belly and a burr in its fur.",
        tags={"cat", "help", "animal"},
    ),
    "loose_shutter": Cause(
        id="loose_shutter",
        label="a loose shutter",
        sound="a long scrape and bang",
        sight="a wooden shutter flapping on one bent hinge",
        scare=1,
        reveal="the swaying light showed a shutter knocking the wall whenever the wind pushed it",
        fix_need="a length of twine",
        truth="It had only been a loose shutter making grand ghost noises for the wind.",
        tags={"wind", "house", "repair"},
    ),
    "bottle_in_wire": Cause(
        id="bottle_in_wire",
        label="a bottle caught in wire",
        sound="a hollow ooo-ooo sound",
        sight="an old bottle turning on a strand of wire",
        scare=2,
        reveal="the glow caught a glass bottle spinning and singing on a wire loop",
        fix_need="careful hands and thick gloves",
        truth="It had only been the wind singing through a bottle caught high in the wire.",
        tags={"wind", "glass", "repair"},
    ),
}

RESPONSES = {
    "lantern_treats": Response(
        id="lantern_treats",
        label="a lantern and a biscuit",
        sense=3,
        power=2,
        handles={"trapped_cat"},
        setup="carried a lantern in one hand and a pocket biscuit in the other",
        solve_text="set the lantern down low, spoke softly, and crumbled the biscuit until the little cat crept out",
        help_text="called for a grown-up, and together they used the lantern and biscuit to coax the cat out",
        qa_text="used a lantern and a biscuit to coax the cat out",
        tags={"lantern", "animal_help"},
    ),
    "lantern_twine": Response(
        id="lantern_twine",
        label="a lantern and twine",
        sense=3,
        power=2,
        handles={"loose_shutter"},
        setup="lifted a lantern while the other child held a coil of twine",
        solve_text="looped the twine around the banging shutter and tied it still",
        help_text="fetched a grown-up, who tied the shutter still while the children held the lantern",
        qa_text="used a lantern and twine to tie the loose shutter still",
        tags={"lantern", "repair"},
    ),
    "lantern_gloves": Response(
        id="lantern_gloves",
        label="a lantern and gloves",
        sense=3,
        power=2,
        handles={"bottle_in_wire"},
        setup="brought a lantern and thick garden gloves",
        solve_text="held the wire steady with the gloves and gently worked the bottle free",
        help_text="called a grown-up, who used the gloves to free the bottle while the children held the light",
        qa_text="used a lantern and gloves to free the bottle from the wire",
        tags={"lantern", "repair", "glass"},
    ),
    "yell_at_ghost": Response(
        id="yell_at_ghost",
        label="shouting at the ghost",
        sense=1,
        power=0,
        handles={"trapped_cat", "loose_shutter", "bottle_in_wire"},
        setup="shouted into the dark",
        solve_text="shouted into the dark, which only made the night sound bigger",
        help_text="shouted for a while, but that did not solve anything",
        qa_text="shouted at the dark",
        tags={"mistake"},
    ),
}

GIRL_NAMES = ["Lily", "Mina", "Nora", "Ava", "June", "Maya", "Ella", "Ruth"]
BOY_NAMES = ["Ben", "Theo", "Finn", "Max", "Sam", "Noah", "Eli", "Leo"]
TRAITS = ["steady", "gentle", "curious", "careful", "loyal", "thoughtful"]


def place_supports(place_id: str, cause_id: str) -> bool:
    support = {
        "greenhouse": {"trapped_cat", "bottle_in_wire"},
        "attic": {"loose_shutter", "bottle_in_wire"},
        "boathouse": {"trapped_cat", "loose_shutter"},
    }
    return cause_id in support.get(place_id, set())


def response_handles(response_id: str, cause_id: str) -> bool:
    return cause_id in RESPONSES[response_id].handles


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for cause_id in CAUSES:
            if not place_supports(place_id, cause_id):
                continue
            for response_id, response in RESPONSES.items():
                if response.sense >= SENSE_MIN and response_handles(response_id, cause_id):
                    combos.append((place_id, cause_id, response_id))
    return combos


@dataclass
class StoryParams:
    place: str
    cause: str
    response: str
    leader: str
    leader_gender: str
    friend: str
    friend_gender: str
    parent: str
    leader_trait: str
    friend_trait: str
    leader_bravery: int = 2
    friend_bravery: int = 1
    friendship: int = 2
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
    StoryParams(
        place="greenhouse",
        cause="trapped_cat",
        response="lantern_treats",
        leader="Lily",
        leader_gender="girl",
        friend="Ben",
        friend_gender="boy",
        parent="mother",
        leader_trait="steady",
        friend_trait="gentle",
        leader_bravery=2,
        friend_bravery=1,
        friendship=2,
    ),
    StoryParams(
        place="attic",
        cause="loose_shutter",
        response="lantern_twine",
        leader="Theo",
        leader_gender="boy",
        friend="Maya",
        friend_gender="girl",
        parent="father",
        leader_trait="curious",
        friend_trait="loyal",
        leader_bravery=2,
        friend_bravery=2,
        friendship=2,
    ),
    StoryParams(
        place="greenhouse",
        cause="bottle_in_wire",
        response="lantern_gloves",
        leader="Nora",
        leader_gender="girl",
        friend="Finn",
        friend_gender="boy",
        parent="mother",
        leader_trait="careful",
        friend_trait="thoughtful",
        leader_bravery=1,
        friend_bravery=1,
        friendship=1,
    ),
    StoryParams(
        place="boathouse",
        cause="trapped_cat",
        response="lantern_treats",
        leader="Max",
        leader_gender="boy",
        friend="June",
        friend_gender="girl",
        parent="father",
        leader_trait="steady",
        friend_trait="gentle",
        leader_bravery=1,
        friend_bravery=1,
        friendship=1,
    ),
]


def explain_place(place_id: str, cause_id: str) -> str:
    return (
        f"(No story: {CAUSES[cause_id].label} is not a reasonable cause for {PLACES[place_id].label}. "
        f"Pick a place that could honestly make that sound.)"
    )


def explain_response(response_id: str, cause_id: str) -> str:
    response = RESPONSES[response_id]
    if response.sense < SENSE_MIN:
        better = ", ".join(sorted(r.id for r in sensible_responses()))
        return (
            f"(Refusing response '{response_id}': it scores too low on common sense "
            f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
        )
    return (
        f"(No story: {response.label} does not sensibly solve {CAUSES[cause_id].label}. "
        f"Choose a response that can reveal and fix the real cause.)"
    )


def outcome_of(params: StoryParams) -> str:
    cause = CAUSES[params.cause]
    courage = params.leader_bravery + params.friend_bravery + params.friendship + 1
    return "solved_together" if courage >= cause.scare + 2 else "got_help"


ASP_RULES = r"""
supports(greenhouse,trapped_cat).
supports(greenhouse,bottle_in_wire).
supports(attic,loose_shutter).
supports(attic,bottle_in_wire).
supports(boathouse,trapped_cat).
supports(boathouse,loose_shutter).

can_handle(R,C) :- handles(R,C).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(P,C,R) :- place(P), cause(C), response(R), supports(P,C), can_handle(R,C), sensible(R).

courage(LB + FB + F + 1) :- leader_bravery(LB), friend_bravery(FB), friendship(F).
needed(S + 2) :- chosen_cause(C), scare(C,S).

outcome(solved_together) :- courage(V), needed(N), V >= N.
outcome(got_help) :- courage(V), needed(N), V < N.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("scare", cause_id, cause.scare))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        for cause_id in sorted(response.handles):
            lines.append(asp.fact("handles", response_id, cause_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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

    extra = "\n".join(
        [
            asp.fact("chosen_cause", params.cause),
            asp.fact("leader_bravery", params.leader_bravery),
            asp.fact("friend_bravery", params.friend_bravery),
            asp.fact("friendship", params.friendship),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a ghost misunderstanding, friendship, and brave investigation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.cause and not place_supports(args.place, args.cause):
        raise StoryError(explain_place(args.place, args.cause))
    if args.response and args.cause:
        if not response_handles(args.response, args.cause) or RESPONSES[args.response].sense < SENSE_MIN:
            raise StoryError(explain_response(args.response, args.cause))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN and args.cause is None:
        raise StoryError(explain_response(args.response, "trapped_cat"))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.cause is None or combo[1] == args.cause)
        and (args.response is None or combo[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, cause_id, response_id = rng.choice(sorted(combos))
    leader, leader_gender = _pick_name(rng)
    friend, friend_gender = _pick_name(rng, avoid=leader)
    parent = args.parent or rng.choice(["mother", "father"])
    leader_trait = rng.choice(TRAITS)
    friend_trait = rng.choice([t for t in TRAITS if t != leader_trait] or TRAITS)
    leader_bravery = rng.randint(1, 2)
    friend_bravery = rng.randint(1, 2)
    friendship = rng.randint(1, 2)
    return StoryParams(
        place=place_id,
        cause=cause_id,
        response=response_id,
        leader=leader,
        leader_gender=leader_gender,
        friend=friend,
        friend_gender=friend_gender,
        parent=parent,
        leader_trait=leader_trait,
        friend_trait=friend_trait,
        leader_bravery=leader_bravery,
        friend_bravery=friend_bravery,
        friendship=friendship,
    )


def introduce(world: World, leader: Entity, friend: Entity, place: Place) -> None:
    world.say(
        f"{leader.id} and {friend.id} were close friends who liked walking together after supper, "
        f"especially when the world felt a little mysterious."
    )
    world.say(place.opening)
    world.say(place.eerie)


def rumor(world: World, leader: Entity, friend: Entity, parent: Entity, place: Place) -> None:
    world.say(
        f"That evening, a sound drifted out of {place.label}, and both friends stopped to listen."
    )
    world.say(
        f'Some older children had once whispered that a ghost lived there. One of them had even used the word '
        f'"anorexic" carelessly while making the story sound stranger, and {leader.id} never forgot how odd and '
        f'wrong that rumor had felt.'
    )
    world.say(
        f'"Do you think it is really a ghost?" {friend.id} whispered.'
    )
    world.facts["heard_sound"] = True
    propagate(world, narrate=False)


def fear_beat(world: World, leader: Entity, friend: Entity, cause: Cause) -> None:
    world.say(
        f"Then they heard {cause.sound} again, and the dark seemed to grow bigger around them."
    )
    if leader.memes["fear"] >= THRESHOLD or friend.memes["fear"] >= THRESHOLD:
        world.say(
            f"Both friends felt a jump of fear, because the rumor made the ordinary night sound magical and mean."
        )


def choose_together(world: World, leader: Entity, friend: Entity) -> None:
    world.facts["holding_hands"] = True
    propagate(world, narrate=False)
    world.say(
        f"{leader.id} reached for {friend.id}'s hand. Holding tight made them feel steadier, as if friendship itself had become a small lamp."
    )


def predict_result(params: StoryParams) -> dict:
    courage = params.leader_bravery + params.friend_bravery + params.friendship + 1
    cause = CAUSES[params.cause]
    return {"courage": courage, "needed": cause.scare + 2, "outcome": outcome_of(params)}


def investigate(world: World, leader: Entity, friend: Entity, place: Place, cause: Cause, response: Response) -> None:
    world.say(
        f"Instead of running, they took one careful step after another toward {place.hiding_spot}."
    )
    world.say(
        f"{leader.id} and {friend.id} {response.setup}."
    )
    world.say(
        f"At last, {cause.reveal}. There was no ghostly face at all, only {cause.sight}."
    )
    world.facts["truth_seen"] = True
    propagate(world, narrate=False)
    world.say(
        f"Working together, they {response.solve_text}."
    )


def get_help(world: World, leader: Entity, friend: Entity, parent: Entity, place: Place, cause: Cause, response: Response) -> None:
    world.say(
        f"They walked as far as the doorway, but the sound still made their knees feel wobbly."
    )
    world.say(
        f'"Let us get {parent.label_word}," said {leader.id}. Asking for help felt braver than pretending not to be scared.'
    )
    world.say(
        f"Soon {leader.id}'s {parent.label_word} came with them to {place.label}, and together they found the truth."
    )
    world.say(
        f"There was no ghostly face at all, only {cause.sight}."
    )
    world.facts["truth_seen"] = True
    propagate(world, narrate=False)
    world.say(
        f"With the grown-up beside them, they {response.help_text}."
    )


def resolution(world: World, leader: Entity, friend: Entity, parent: Entity, cause: Cause) -> None:
    world.say(
        f"{cause.truth} The scary part had been the misunderstanding, not the night itself."
    )
    world.say(
        f'{parent.label_word.capitalize()} knelt beside them and said, "Rumors can make simple things seem like monsters. The brave thing is to look carefully, or to ask for help when careful looking is too hard."'
    )
    world.say(
        f"After that, {leader.id} and {friend.id} never laughed at spooky stories without checking the truth first, and their friendship felt warmer than the dark had felt cold."
    )


def ending_image(world: World, leader: Entity, friend: Entity, place: Place, cause_id: str) -> None:
    if cause_id == "trapped_cat":
        world.say(
            f"When they walked home, the little cat was tucked in a basket by the kitchen door, blinking up at them as if the whole moonlit adventure had been a thank-you."
        )
    elif cause_id == "loose_shutter":
        world.say(
            f"Later the house stood quiet, and the attic window shone still and square instead of banging like a ghost tale."
        )
    else:
        world.say(
            f"By the time they turned back toward home, the wire was quiet, and the moon looked plain and kind instead of haunted."
        )


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if not place_supports(params.place, params.cause):
        raise StoryError(explain_place(params.place, params.cause))
    if RESPONSES[params.response].sense < SENSE_MIN or not response_handles(params.response, params.cause):
        raise StoryError(explain_response(params.response, params.cause))

    place = PLACES[params.place]
    cause = CAUSES[params.cause]
    response = RESPONSES[params.response]

    world = World()
    leader = world.add(
        Entity(
            id=params.leader,
            kind="character",
            type=params.leader_gender,
            label=params.leader,
            role="leader",
            traits=[params.leader_trait],
        )
    )
    friend = world.add(
        Entity(
            id=params.friend,
            kind="character",
            type=params.friend_gender,
            label=params.friend,
            role="friend",
            traits=[params.friend_trait],
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=params.parent,
            label="the parent",
            role="parent",
        )
    )
    place_ent = world.add(Entity(id="place", kind="thing", type="place", label=place.label))
    source = world.add(Entity(id="source", kind="thing", type="cause", label=cause.label))

    leader.memes["bravery"] = float(params.leader_bravery)
    friend.memes["bravery"] = float(params.friend_bravery)
    leader.memes["friendship"] = float(params.friendship)
    friend.memes["friendship"] = float(params.friendship)
    source.meters["scare"] = float(cause.scare)

    world.facts["heard_sound"] = False
    world.facts["holding_hands"] = False
    world.facts["truth_seen"] = False
    world.facts["misunderstanding_active"] = False
    world.facts["friendship_boost"] = 0
    world.facts["place_cfg"] = place
    world.facts["cause_cfg"] = cause
    world.facts["response_cfg"] = response
    world.facts["leader"] = leader
    world.facts["friend"] = friend
    world.facts["parent"] = parent
    world.facts["place"] = place_ent
    world.facts["source"] = source
    world.facts["predicted"] = predict_result(params)

    introduce(world, leader, friend, place)
    world.para()
    rumor(world, leader, friend, parent, place)
    fear_beat(world, leader, friend, cause)
    choose_together(world, leader, friend)

    world.para()
    if outcome_of(params) == "solved_together":
        investigate(world, leader, friend, place, cause, response)
    else:
        get_help(world, leader, friend, parent, place, cause, response)

    world.para()
    resolution(world, leader, friend, parent, cause)
    ending_image(world, leader, friend, place, cause.id)

    world.facts["outcome"] = outcome_of(params)
    world.facts["rumor_wrong_word"] = "anorexic"
    return world


KNOWLEDGE = {
    "ghosts": [
        (
            "Why do ordinary things sometimes seem spooky at night?",
            "At night, shadows, wind, and strange sounds can be hard to understand. When you cannot see clearly, your mind may guess something scarier than the truth."
        )
    ],
    "rumor": [
        (
            "What is a rumor?",
            "A rumor is a story people repeat without checking if it is true. Rumors can grow bigger and stranger each time they are told."
        )
    ],
    "friendship": [
        (
            "How can a friend help when you feel scared?",
            "A friend can stay close, hold your hand, and help you think carefully. Feeling supported often makes it easier to do the next brave thing."
        )
    ],
    "help": [
        (
            "Is asking a grown-up for help a brave choice?",
            "Yes. Asking for help is brave when something feels too big, confusing, or unsafe to handle alone."
        )
    ],
    "cat": [
        (
            "What should you do if you find a frightened stray cat?",
            "Stay gentle and move slowly so the cat does not feel chased. Then tell a grown-up, because the cat may need food, warmth, or a safe place."
        )
    ],
    "wind": [
        (
            "Can wind make spooky sounds?",
            "Yes. Wind can whistle through bottles, wires, cracks, and shutters. Those sounds can seem mysterious until you find where the air is moving."
        )
    ],
    "glass": [
        (
            "Why should you be careful with broken or stuck glass?",
            "Glass can crack or cut hands. Thick gloves and a grown-up's help make it much safer to move."
        )
    ],
}
KNOWLEDGE_ORDER = ["ghosts", "rumor", "friendship", "help", "cat", "wind", "glass"]


def generation_prompts(world: World) -> list[str]:
    leader = world.facts["leader"]
    friend = world.facts["friend"]
    place = world.facts["place_cfg"]
    cause = world.facts["cause_cfg"]
    outcome = world.facts["outcome"]
    if outcome == "solved_together":
        return [
            f'Write a gentle ghost story for a 3-to-5-year-old about two friends who hear a spooky sound in {place.label} and discover the truth together.',
            f"Tell a story where {leader.id} and {friend.id} feel scared by a rumor, but friendship gives them the courage to look carefully.",
            f'Write a misunderstanding story that includes the word "anorexic" inside a corrected rumor and ends with the children learning there was no ghost at all.',
        ]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old about two friends who hear a spooky sound in {place.label}, get frightened, and choose to ask a grown-up for help.',
        f"Tell a story where {leader.id} and {friend.id} mistake {cause.sound} for a ghost because of a rumor, then learn the brave thing can be asking for help.",
        f'Write a ghost-story misunderstanding tale that includes the word "anorexic" in a rumor correction and ends with truth, safety, and friendship.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    leader = world.facts["leader"]
    friend = world.facts["friend"]
    parent = world.facts["parent"]
    place = world.facts["place_cfg"]
    cause = world.facts["cause_cfg"]
    response = world.facts["response_cfg"]
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {leader.id} and {friend.id}. They heard a spooky sound near {place.label} and had to decide how to face it."
        ),
        (
            f"Why did {leader.id} and {friend.id} think there might be a ghost?",
            f"They had heard a rumor about a ghost, so when {cause.sound} drifted out of the dark, the rumor filled in the rest. The misunderstanding happened because fear and guessing came before a careful look."
        ),
        (
            'How was the word "anorexic" used in the story?',
            'It appeared inside the rumor as a wrong and careless word someone had used to make the tale sound stranger. The story makes clear that repeating serious words carelessly can confuse people instead of helping them understand.'
        ),
        (
            "What made the children braver?",
            f"They stayed together and held hands. Their friendship helped them think more clearly instead of letting fear make all the choices."
        ),
    ]
    if outcome == "solved_together":
        qa.append(
            (
                "How did they solve the mystery?",
                f"They {response.qa_text}. Once they had light and a sensible plan, the ghost idea vanished because the real cause was right in front of them."
            )
        )
    else:
        qa.append(
            (
                f"Why did they go get {parent.label_word}?",
                f"They were brave enough to go close, but not calm enough to handle the last part alone. Asking {parent.label_word} for help turned the frightened guessing into a safe, truthful ending."
            )
        )
    qa.append(
        (
            "What was really making the spooky sound?",
            f"It was {cause.label}. The ending shows that the scary part was a misunderstanding, not a real ghost."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    cause = world.facts["cause_cfg"]
    tags = {"ghosts", "rumor", "friendship", "help"}
    if "animal" in cause.tags:
        tags.add("cat")
    if "wind" in cause.tags:
        tags.add("wind")
    if "glass" in cause.tags:
        tags.add("glass")

    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    facts_view = {
        key: value
        for key, value in world.facts.items()
        if key
        in {
            "heard_sound",
            "holding_hands",
            "truth_seen",
            "misunderstanding_active",
            "friendship_boost",
            "outcome",
            "rumor_wrong_word",
            "predicted",
        }
    }
    lines.append(f"  facts: {facts_view}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_responses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during resolve_params() seed {seed}.")
            continue
        params.seed = seed
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("Generated empty story in smoke test.")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, cause, response) combos:\n")
        for place_id, cause_id, response_id in combos:
            print(f"  {place_id:10} {cause_id:14} {response_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.leader} & {p.friend}: {p.cause} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
