#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/plan_bystander_grouch_twist_rhyming_story.py
=======================================================================

A standalone story world for a tiny rhyming tale about a child with a plan,
a grouchy-looking bystander, and a twist: the "grouch" turns out to be the
person who knows how to help.

Domain sketch
-------------
A child brings a kite to fly in a public place. The first plan is flawed in
one *specific, fixable* way:

* the place is snaggy, so the line will catch unless they move to an open patch
* or the wind is gusty and the kite needs a tail, so it will wobble unless they
  add one

A bystander first sounds like a grouch. Then comes the twist: the bystander was
not trying to spoil the fun, but to protect the kite and help the child change
the plan. The ending image proves the change when the kite finally rises.

This script follows the storyworld contract:
- stdlib only
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py in ASP helpers
- typed entities with meters and memes
- Python reasonableness gate plus inline ASP twin
- three QA sets grounded in the simulated world
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
        female = {"girl", "woman", "lady", "grandmother"}
        male = {"boy", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Place:
    id: str
    label: str
    phrase: str
    ground: str
    snaggy: bool = False
    alternate: str = ""
    alternate_phrase: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Wind:
    id: str
    label: str
    line: str
    gusty: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Kite:
    id: str
    label: str
    phrase: str
    color: str
    shape: str
    needs_tail: bool = False
    delicate: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    handles: str
    action: str
    helper_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


PLACES = {
    "tree_path": Place(
        "tree_path",
        "tree path",
        "the path by the tall trees",
        "packed dirt",
        snaggy=True,
        alternate="meadow",
        alternate_phrase="the open meadow past the gate",
        tags={"park", "tree"},
    ),
    "lamp_court": Place(
        "lamp_court",
        "lamp court",
        "the little stone court by the lamp posts",
        "flat stone",
        snaggy=True,
        alternate="hill",
        alternate_phrase="the breezy hill beside the pond",
        tags={"courtyard", "lamp"},
    ),
    "open_meadow": Place(
        "open_meadow",
        "open meadow",
        "the open meadow",
        "soft grass",
        snaggy=False,
        alternate="",
        alternate_phrase="",
        tags={"park", "grass"},
    ),
}

WINDS = {
    "breezy": Wind(
        "breezy",
        "breezy",
        "A friendly breeze went swish through the clover and grass.",
        gusty=False,
        tags={"wind"},
    ),
    "gusty": Wind(
        "gusty",
        "gusty",
        "The wind came in puffs with a tug and a twist, then hurried away with a hissy whoosh-whist.",
        gusty=True,
        tags={"wind", "gust"},
    ),
    "soft": Wind(
        "soft",
        "soft",
        "Only a sleepy small breeze brushed by now and then.",
        gusty=False,
        tags={"wind"},
    ),
}

KITES = {
    "swallow": Kite(
        "swallow",
        "swallow kite",
        "a red paper swallow kite",
        "red",
        "swallow",
        needs_tail=True,
        delicate=True,
        tags={"kite", "paper"},
    ),
    "star": Kite(
        "star",
        "star kite",
        "a blue cloth star kite",
        "blue",
        "star",
        needs_tail=False,
        delicate=False,
        tags={"kite", "cloth"},
    ),
    "diamond": Kite(
        "diamond",
        "diamond kite",
        "a yellow diamond kite",
        "yellow",
        "diamond",
        needs_tail=True,
        delicate=False,
        tags={"kite"},
    ),
}

REMEDIES = {
    "move_meadow": Remedy(
        "move_meadow",
        "move to the open patch",
        "snag",
        "walked together to the open patch where nothing could grab the line",
        "pointed past the trouble and led the child to the wide open patch",
        "helped by moving to a place with clear sky and no grabbing branches",
        tags={"open_space"},
    ),
    "add_tail": Remedy(
        "add_tail",
        "add a ribbon tail",
        "wobble",
        "tied a long ribbon tail to the kite so the gusts would stop making it wobble",
        "pulled a ribbon from a pocket and tied on a steady tail",
        "helped by adding a tail so the gusty wind would not flip the kite around",
        tags={"tail"},
    ),
}

GIRL_NAMES = ["Mia", "Lila", "Nora", "Zoe", "Ava", "June"]
BOY_NAMES = ["Ben", "Milo", "Toby", "Finn", "Leo", "Owen"]
BYSTANDER_NAMES = ["Mr. Reed", "Ms. Dot", "Gran May", "Old Jo"]
TRAITS = ["eager", "hopeful", "bouncy", "cheerful"]


# ---------------------------------------------------------------------------
# World and rules
# ---------------------------------------------------------------------------
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


def _r_snag(world: World) -> list[str]:
    kite = world.get("kite")
    place = world.get("place")
    if place.attrs.get("snaggy") and kite.meters["launched"] >= THRESHOLD:
        sig = ("snag", place.id)
        if sig not in world.fired:
            world.fired.add(sig)
            kite.meters["snag_risk"] += 1
            world.get("child").memes["worry"] += 1
    return []


def _r_wobble(world: World) -> list[str]:
    kite = world.get("kite")
    wind = world.get("wind")
    if wind.attrs.get("gusty") and kite.attrs.get("needs_tail") and not kite.attrs.get("has_tail"):
        if kite.meters["launched"] >= THRESHOLD:
            sig = ("wobble", kite.id)
            if sig not in world.fired:
                world.fired.add(sig)
                kite.meters["wobble"] += 1
                world.get("child").memes["worry"] += 1
    return []


def _r_fly(world: World) -> list[str]:
    kite = world.get("kite")
    if kite.meters["launched"] < THRESHOLD:
        return []
    if kite.meters["snag_risk"] < THRESHOLD and kite.meters["wobble"] < THRESHOLD:
        sig = ("fly", kite.id, int(kite.attrs.get("has_tail", False)))
        if sig not in world.fired:
            world.fired.add(sig)
            kite.meters["lift"] += 1
            world.get("child").memes["joy"] += 1
            world.get("bystander").memes["softness"] += 1
    return []


CAUSAL_RULES = [
    Rule("snag", "physical", _r_snag),
    Rule("wobble", "physical", _r_wobble),
    Rule("fly", "physical", _r_fly),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        before = len(world.fired)
        for rule in CAUSAL_RULES:
            rule.apply(world)
        if len(world.fired) != before:
            changed = True


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def issue_of(place: Place, wind: Wind, kite: Kite) -> Optional[str]:
    issues: list[str] = []
    if place.snaggy:
        issues.append("snag")
    if wind.gusty and kite.needs_tail:
        issues.append("wobble")
    if wind.id == "soft" and kite.id == "star":
        issues.append("no_lift")
    if len(issues) != 1:
        return None
    if issues[0] in {"snag", "wobble"}:
        return issues[0]
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for wind_id, wind in WINDS.items():
            for kite_id, kite in KITES.items():
                issue = issue_of(place, wind, kite)
                if not issue:
                    continue
                for remedy_id, remedy in REMEDIES.items():
                    if remedy.handles == issue:
                        combos.append((place_id, wind_id, kite_id, remedy_id))
    return combos


def explain_rejection(place: Place, wind: Wind, kite: Kite, remedy: Optional[Remedy] = None) -> str:
    issue = issue_of(place, wind, kite)
    raw_issues = []
    if place.snaggy:
        raw_issues.append("snag")
    if wind.gusty and kite.needs_tail:
        raw_issues.append("wobble")
    if wind.id == "soft" and kite.id == "star":
        raw_issues.append("no_lift")
    if len(raw_issues) == 0:
        return (
            f"(No story: {kite.phrase} at {place.phrase} in {wind.label} wind has no clear trouble, "
            f"so the twist has nothing to fix. Pick a snaggy place or a gusty wind.)"
        )
    if len(raw_issues) > 1:
        return (
            f"(No story: this setup has too many problems at once ({', '.join(raw_issues)}). "
            f"This world only tells stories with one clear fixable problem.)"
        )
    if raw_issues[0] == "no_lift":
        return (
            f"(No story: {kite.phrase} is too heavy for such a soft breeze, and this world has no honest one-step fix for that.)"
        )
    if remedy and remedy.handles != issue:
        return (
            f"(No story: remedy '{remedy.id}' solves {remedy.handles}, but this setup needs help with {issue}.)"
        )
    return "(No story: this combination does not fit the world's single-problem rule.)"


# ---------------------------------------------------------------------------
# Simulation verbs
# ---------------------------------------------------------------------------
def attempt(world: World) -> None:
    kite = world.get("kite")
    kite.meters["launched"] += 1
    propagate(world)


def apply_remedy(world: World, remedy: Remedy) -> None:
    kite = world.get("kite")
    place = world.get("place")
    if remedy.handles == "snag":
        place.attrs["snaggy"] = False
        world.facts["moved_to"] = place.attrs.get("alternate_phrase", "")
        kite.meters["snag_risk"] = 0.0
    elif remedy.handles == "wobble":
        kite.attrs["has_tail"] = True
        kite.meters["wobble"] = 0.0
    kite.meters["launched"] = 0.0
    world.fired = {sig for sig in world.fired if sig[0] not in {"snag", "wobble", "fly"}}
    attempt(world)


def predict_issue(place: Place, wind: Wind, kite: Kite) -> Optional[str]:
    return issue_of(place, wind, kite)


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def tell(
    place: Place,
    wind: Wind,
    kite_cfg: Kite,
    remedy: Remedy,
    child_name: str = "Mia",
    child_type: str = "girl",
    bystander_name: str = "Mr. Reed",
    bystander_type: str = "man",
    trait: str = "eager",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    bystander = world.add(Entity(id="Bystander", kind="character", type=bystander_type, role="bystander", label=bystander_name))
    kite = world.add(Entity(
        id="kite",
        type="kite",
        label=kite_cfg.label,
        attrs={"needs_tail": kite_cfg.needs_tail, "has_tail": False},
    ))
    place_ent = world.add(Entity(
        id="place",
        type="place",
        label=place.label,
        attrs={"snaggy": place.snaggy, "alternate_phrase": place.alternate_phrase},
    ))
    wind_ent = world.add(Entity(
        id="wind",
        type="wind",
        label=wind.label,
        attrs={"gusty": wind.gusty},
    ))

    child.memes["hope"] += 1
    child.attrs["trait"] = trait
    bystander.memes["grouch_mask"] += 1
    bystander.memes["care"] += 1

    world.say(
        f"{child_name} came skipping with a bright little plan, to fly {kite_cfg.phrase} as high as {child.pronoun()} can."
    )
    world.say(
        f"At {place.phrase}, on {place.ground} so neat, {wind.line}"
    )

    world.para()
    world.say(
        f"{child_name} lifted the spool with a grin that said, \"Up!\" while a bystander sat nearby with a hat tipped down and gruff-looking brow."
    )
    attempt(world)
    issue = predict_issue(place, wind, kite_cfg)
    world.facts["issue"] = issue

    if issue == "snag":
        child.memes["doubt"] += 1
        world.say(
            f"\"That plan won't last,\" the bystander said in a huff. \"Those branches will grab it and make a mess of your stuff.\""
        )
        world.say(
            f"{child_name} blinked and thought, What a grouch on the path, with a grumble and gritch and a gruff little laugh."
        )
    elif issue == "wobble":
        child.memes["doubt"] += 1
        world.say(
            f"\"That kite will flip,\" the bystander said with a scowl. \"In gusts like these, it will tumble and howl.\""
        )
        world.say(
            f"{child_name} blinked and thought, What a grouch on the ground, all grumble and gruff in a growly old sound."
        )
    else:
        raise StoryError(explain_rejection(place, wind, kite_cfg, remedy))

    world.para()
    bystander.memes["grouch_mask"] = 0.0
    bystander.memes["help"] += 1
    if remedy.handles == "snag":
        world.say(
            f"But then came the twist, warm and quick as a patch of sun: the bystander stood up and said, \"Come along, little one.\""
        )
        world.say(
            f"{bystander_name} {remedy.helper_text}. \"I sound sharp at first,\" {bystander.pronoun()} said, \"but I hate to see good kites caught and shred.\""
        )
    else:
        world.say(
            f"But then came the twist, bright and neat as a song: the bystander reached in a pocket that jingled along."
        )
        world.say(
            f"{bystander_name} {remedy.helper_text}. \"I sound like a grouch,\" {bystander.pronoun()} said, \"yet I just know what keeps a kite steady instead.\""
        )

    apply_remedy(world, remedy)

    world.para()
    if world.get("kite").meters["lift"] >= THRESHOLD:
        child.memes["relief"] += 1
        child.memes["trust"] += 1
        world.say(
            f"Soon up sailed the {kite_cfg.color} kite, dipping in light, with a tug in the string and a tail dancing bright."
        )
        if remedy.handles == "snag":
            moved = world.facts.get("moved_to", place.alternate_phrase)
            world.say(
                f"From {moved}, it floated with room for the sky, and {child_name} laughed, \"What a fine change of plan! See it fly!\""
            )
        else:
            world.say(
                f"The gusts gave a shove, but the ribbon held true, and {child_name} laughed, \"What a fine change of plan! Now it flew!\""
            )
        world.say(
            f"The bystander smiled, not a grouch after all, and child and old helper watched shadows grow small."
        )
        outcome = "soared"
    else:
        outcome = "stalled"

    world.facts.update(
        child=child,
        bystander=bystander,
        place_cfg=place,
        wind_cfg=wind,
        kite_cfg=kite_cfg,
        remedy=remedy,
        outcome=outcome,
        twist_helped=bystander.memes["help"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    wind: str
    kite: str
    remedy: str
    child_name: str
    child_gender: str
    bystander_name: str
    bystander_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "kite": [(
        "What does a kite need to fly well?",
        "A kite needs moving air and enough open space. If something blocks the line or the kite keeps wobbling, it will not fly nicely."
    )],
    "tree": [(
        "Why are trees tricky places to fly a kite?",
        "Branches can catch the string or the kite itself. That is why an open patch is safer for flying."
    )],
    "gust": [(
        "What does a gust of wind do?",
        "A gust is a sudden stronger puff of wind. It can shove light things around very quickly."
    )],
    "tail": [(
        "Why does a kite tail help?",
        "A tail helps the kite stay balanced. In gusty wind, that extra balance can stop the kite from flipping and wobbling."
    )],
    "open_space": [(
        "Why is open space good for kite flying?",
        "Open space gives the kite room to rise and turn. It also keeps the line away from trees, poles, and other things that can snag it."
    )],
}
KNOWLEDGE_ORDER = ["kite", "tree", "gust", "tail", "open_space"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    kite = f["kite_cfg"]
    place = f["place_cfg"]
    remedy = f["remedy"]
    return [
        f'Write a rhyming story for a 3-to-5-year-old that includes the words "plan", "bystander", and "grouch".',
        f"Tell a Twist story where {child.id} brings {kite.phrase} to {place.phrase}, thinks a bystander is a grouch, and then learns the bystander was helping.",
        f"Write a child-facing rhyme where a plan goes wrong in one clear way, then is fixed with {remedy.label}, ending with the kite high in the sky.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    bystander = f["bystander"]
    place = f["place_cfg"]
    wind = f["wind_cfg"]
    kite = f["kite_cfg"]
    remedy = f["remedy"]
    issue = f["issue"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who came with a kite and a plan, and {bystander.label}, a bystander who first seemed like a grouch. The story is really about how that first wrong guess changed."
        ),
        (
            f"What was {child.id}'s plan?",
            f"{child.id}'s plan was to fly {kite.phrase} at {place.phrase}. That happy plan starts the whole story and leads straight into the problem."
        ),
        (
            f"Why did the bystander speak up?",
            _qa_issue(issue, place, wind, kite),
        ),
        (
            "What was the twist?",
            f"The twist was that the bystander was not trying to ruin the fun. {bystander.label} actually knew how to help and changed the plan so the kite could fly."
        ),
        (
            "How did they fix the problem?",
            f"They {remedy.qa_text}. Because the fix matched the real problem, the kite could finally rise instead of getting stuck or wobbling."
        ),
        (
            "How did the story end?",
            f"It ended with the kite up in the sky and both of them smiling. The ending image proves what changed: the plan grew wiser, and the seeming grouch became a helper."
        ),
    ]
    return qa


def _qa_issue(issue: str, place: Place, wind: Wind, kite: Kite) -> str:
    if issue == "snag":
        return (
            f"The bystander saw that {place.phrase} was full of things that could grab the line. {kite.phrase.capitalize()} would have been caught there, so the warning came from care, not meanness."
        )
    if issue == "wobble":
        return (
            f"The bystander saw that the wind was gusty and that {kite.phrase} needed more balance. Without a tail, those strong puffs would keep flipping it around."
        )
    return "The bystander spoke because the first plan would not work well."


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["kite_cfg"].tags) | set(f["wind_cfg"].tags) | set(f["remedy"].tags) | set(f["place_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        attrs = {k: v for k, v in e.attrs.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("tree_path", "breezy", "star", "move_meadow", "Mia", "girl", "Mr. Reed", "man", "hopeful"),
    StoryParams("open_meadow", "gusty", "swallow", "add_tail", "Ben", "boy", "Ms. Dot", "woman", "eager"),
    StoryParams("lamp_court", "breezy", "diamond", "move_meadow", "Nora", "girl", "Gran May", "grandmother", "bouncy"),
    StoryParams("open_meadow", "gusty", "diamond", "add_tail", "Leo", "boy", "Old Jo", "man", "cheerful"),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
problem(P, W, K, snag)   :- place(P), wind(W), kite(K), snaggy(P), not gust_problem(W, K), not no_lift_problem(W, K).
problem(P, W, K, wobble) :- place(P), wind(W), kite(K), not snaggy(P), gust_problem(W, K), not no_lift_problem(W, K).

gust_problem(W, K) :- gusty(W), needs_tail(K).
no_lift_problem(soft, star).

valid(P, W, K, R) :- place(P), wind(W), kite(K), remedy(R), problem(P, W, K, X), handles(R, X).

outcome(P, W, K, R, soared) :- valid(P, W, K, R).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.snaggy:
            lines.append(asp.fact("snaggy", pid))
    for wid, wind in WINDS.items():
        lines.append(asp.fact("wind", wid))
        if wind.gusty:
            lines.append(asp.fact("gusty", wid))
    for kid, kite in KITES.items():
        lines.append(asp.fact("kite", kid))
        if kite.needs_tail:
            lines.append(asp.fact("needs_tail", kid))
    for rid, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("handles", rid, remedy.handles))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_wind", params.wind),
        asp.fact("chosen_kite", params.kite),
        asp.fact("chosen_remedy", params.remedy),
        "picked_outcome(X) :- chosen_place(P), chosen_wind(W), chosen_kite(K), chosen_remedy(R), outcome(P, W, K, R, X).",
    ])
    model = asp.one_model(asp_program(extra, "#show picked_outcome/1."))
    atoms = asp.atoms(model, "picked_outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    for params in CURATED[:2]:
        if asp_outcome(params) != "soared":
            rc = 1
            print(f"MISMATCH in outcome for {params}: expected soared from ASP.")
            break
    else:
        print("OK: ASP outcome matches curated happy stories.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="### smoke")
        print("OK: smoke generation/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming kite story world: a plan, a bystander, a grouch, and a twist."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--wind", choices=WINDS)
    ap.add_argument("--kite", choices=KITES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--bystander-name")
    ap.add_argument("--bystander-type", choices=["man", "woman", "grandmother"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.wind and args.kite:
        place = PLACES[args.place]
        wind = WINDS[args.wind]
        kite = KITES[args.kite]
        remedy = REMEDIES[args.remedy] if args.remedy else None
        issue = issue_of(place, wind, kite)
        if not issue or (remedy and remedy.handles != issue):
            raise StoryError(explain_rejection(place, wind, kite, remedy))
    if args.remedy and not (args.place and args.wind and args.kite):
        # Allow pinned remedy only if it can still match some valid combo.
        possible = [
            combo for combo in valid_combos()
            if combo[3] == args.remedy
            and (args.place is None or combo[0] == args.place)
            and (args.wind is None or combo[1] == args.wind)
            and (args.kite is None or combo[2] == args.kite)
        ]
        if not possible:
            sample_place = PLACES[args.place] if args.place else next(iter(PLACES.values()))
            sample_wind = WINDS[args.wind] if args.wind else next(iter(WINDS.values()))
            sample_kite = KITES[args.kite] if args.kite else next(iter(KITES.values()))
            raise StoryError(explain_rejection(sample_place, sample_wind, sample_kite, REMEDIES[args.remedy]))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.wind is None or c[1] == args.wind)
        and (args.kite is None or c[2] == args.kite)
        and (args.remedy is None or c[3] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, wind, kite, remedy = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    bystander_type = args.bystander_type or rng.choice(["man", "woman", "grandmother"])
    bystander_name = args.bystander_name or rng.choice(BYSTANDER_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place, wind, kite, remedy, child_name, child_gender, bystander_name, bystander_type, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        WINDS[params.wind],
        KITES[params.kite],
        REMEDIES[params.remedy],
        params.child_name,
        params.child_gender,
        params.bystander_name,
        params.bystander_type,
        params.trait,
    )
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
        print(asp_program("", "#show valid/4.\n#show outcome/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, wind, kite, remedy) combos:\n")
        for place, wind, kite, remedy in combos:
            print(f"  {place:12} {wind:7} {kite:8} {remedy}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.kite} in {p.wind} wind at {p.place} ({p.remedy})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
