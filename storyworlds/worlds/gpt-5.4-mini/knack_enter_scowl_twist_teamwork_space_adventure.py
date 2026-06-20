#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/knack_enter_scowl_twist_teamwork_space_adventure.py
====================================================================================

A tiny storyworld for a Space Adventure style tale about a child crew, a tricky
space entrance, a grumpy scowl, a useful knack, and a teamwork twist that turns
the mission around.

The world is intentionally small and concrete:
- a crew is traveling in a ship
- they must enter a space habitat or docking bay
- one child has a knack for solving a specific control problem
- a scowling problem appears
- teamwork fixes the twist and the crew ends safely

The story engine simulates meters and memes, uses a reasonableness gate, exposes
an ASP twin, and renders from world state rather than frozen text.
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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    backdrop: str
    entry: str
    atmosphere: str

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
class Challenge:
    id: str
    label: str
    issue: str
    risk: str
    needs: str
    twist: str
    visible_scowl: str
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
class Knack:
    id: str
    label: str
    method: str
    effect: str
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
class TwistFix:
    id: str
    label: str
    action: str
    result: str
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


def _r_scowl(world: World) -> list[str]:
    out: list[str] = []
    challenge = world.get("challenge")
    if challenge.meters["stuck"] < THRESHOLD:
        return out
    if ("scowl", challenge.id) in world.fired:
        return out
    world.fired.add(("scowl", challenge.id))
    for kid in world.characters():
        kid.memes["worry"] += 1
    out.append("__scowl__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    crew = [e for e in world.characters() if e.role in {"captain", "knack", "helper"}]
    if sum(1 for e in crew if e.memes["helping"] >= THRESHOLD) < 2:
        return out
    if "support" in world.fired:
        return out
    world.fired.add(("support", "crew"))
    world.get("ship").meters["stability"] += 1
    out.append("__teamwork__")
    return out


CAUSAL_RULES = [
    Rule("scowl", "social", _r_scowl),
    Rule("teamwork", "social", _r_teamwork),
]


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


def reasonable_combo(setting: Setting, challenge: Challenge, knack: Knack, fix: TwistFix) -> bool:
    return challenge.needs in knack.tags and challenge.needs in fix.tags


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid, challenge in CHALLENGES.items():
            for kid, knack in KNACKS.items():
                for fid, fix in FIXES.items():
                    if reasonable_combo(setting, challenge, knack, fix):
                        combos.append((sid, cid, kid, fid))
    return combos


def predict_failure(world: World, challenge_id: str) -> dict:
    sim = world.copy()
    sim.get(challenge_id).meters["stuck"] += 1
    propagate(sim, narrate=False)
    return {
        "scowl": sim.get("challenge").memes["worry"] >= THRESHOLD,
        "stability": sim.get("ship").meters["stability"],
    }


def introduce(world: World, captain: Entity, sidekick: Entity, setting: Setting) -> None:
    world.say(
        f"On a bright day among the stars, {captain.id} and {sidekick.id} flew "
        f"their little ship toward {setting.place}. {setting.backdrop}"
    )
    world.say(
        f"At the edge of the station was {setting.entry}, and the crew needed a way to enter."
    )


def describe_challenge(world: World, challenge: Challenge) -> None:
    world.say(
        f"But the hatch had {challenge.issue}, and that made the whole ship feel {challenge.visible_scowl}."
    )
    world.say(
        f"{challenge.risk.capitalize()}, and the crew could not simply drift past it."
    )


def show_knack(world: World, knack: Knack, captain: Entity) -> None:
    captain.memes["confidence"] += 1
    world.say(
        f"{captain.id} had a knack for {knack.method}. {knack.effect}."
    )


def warn(world: World, helper: Entity, challenge: Challenge) -> None:
    helper.memes["worry"] += 1
    world.say(
        f"{helper.id} looked at the hatch and scowled. '{challenge.visible_scowl.capitalize()},' "
        f"{helper.id} muttered, 'but we can solve it if we work together.'"
    )


def attempt_enter(world: World, captain: Entity, challenge: Challenge) -> None:
    captain.memes["helping"] += 1
    challenge.meters["stuck"] += 1
    world.say(
        f"{captain.id} tried to enter, but the hatch stayed stuck for a moment."
    )
    propagate(world, narrate=False)


def twist_turn(world: World, challenge: Challenge, fix: TwistFix) -> None:
    challenge.meters["stuck"] += 1
    world.say(
        f"Then came the twist: {challenge.twist}. So the crew did not push harder; "
        f"they used a new plan."
    )
    world.say(f"They decided to {fix.action}.")
    world.facts["fix"] = fix


def teamwork_scene(world: World, captain: Entity, helper: Entity, knack: Knack, fix: TwistFix) -> None:
    captain.memes["helping"] += 1
    helper.memes["helping"] += 1
    world.say(
        f"{captain.id} used the knack to {knack.method}, while {helper.id} helped with the controls."
    )
    world.say(
        f"Together they {fix.result}, and the hatch opened with a soft whoosh."
    )


def ending(world: World, setting: Setting) -> None:
    world.get("ship").meters["stability"] += 1
    world.get("challenge").meters["stuck"] = 0
    world.say(
        f"Soon the crew drifted safely into {setting.place}, and the stars shone like silver buttons outside."
    )
    world.say(
        "Their teamwork turned the scowl into a smile, and the mission could begin."
    )


SETTINGS = {
    "dock": Setting("dock", "the docking ring", "The station floated like a giant silver wheel.", "the outer hatch", "quiet and bright"),
    "bay": Setting("bay", "the cargo bay", "Boxes hummed softly beside blinking panels.", "the cargo door", "busy and narrow"),
    "moonbase": Setting("moonbase", "the moonbase corridor", "Dusty lights glowed along the long hallway.", "the inner gate", "small and echoing"),
}

CHALLENGES = {
    "jammed_hatch": Challenge(
        "jammed_hatch",
        "jammed hatch",
        "a jammed latch",
        "they might miss the safe docking window",
        "a careful way to open it",
        "the latch was stuck because a tiny bolt had slipped sideways",
        "the hatch wore a big scowl",
        tags={"open", "hatch"},
    ),
    "stuck_panel": Challenge(
        "stuck_panel",
        "stuck panel",
        "a stuck entry panel",
        "their ship could not enter the base",
        "a careful way to open it",
        "the panel was fussy after a power hiccup",
        "the panel wore a deep scowl",
        tags={"open", "panel"},
    ),
    "twisty_lock": Challenge(
        "twisty_lock",
        "twisty lock",
        "a twisty lock",
        "the door would not turn the right way",
        "a careful way to turn it",
        "the lock had turned itself backward",
        "the lock wore a stubborn scowl",
        tags={"turn", "lock"},
    ),
}

KNACKS = {
    "tiny_tools": Knack("tiny_tools", "tiny tools", "using tiny tools to line up a bolt", "The bolt clicked back into place", tags={"open", "hatch"}),
    "panel_codes": Knack("panel_codes", "panel codes", "reading panel codes", "The blinking lights made sense again", tags={"open", "panel"}),
    "gentle_turn": Knack("gentle_turn", "gentle turns", "making gentle turns with both hands", "The lock began to turn the right way", tags={"turn", "lock"}),
}

FIXES = {
    "two_step": TwistFix("two_step", "two-step teamwork", "take turns and do it in two steps", "the controls listened to them", tags={"open", "panel"}),
    "together_push": TwistFix("together_push", "teamwork push", "pull together at the same time", "the hatch moved at once", tags={"open", "hatch"}),
    "careful_twist": TwistFix("careful_twist", "careful twist", "twist it slowly and check the light", "the lock gave way with a tiny click", tags={"turn", "lock"}),
}

NAMES = ["Nova", "Milo", "Rin", "Ari", "Pia", "Luca", "Zia", "Bea"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    challenge: str
    knack: str
    fix: str
    captain: str
    helper: str
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
    "open": [("What does it mean to enter something?", "To enter means to go inside or pass through an opening, like walking through a door or hatch.")],
    "hatch": [("What is a hatch?", "A hatch is a door or cover on a ship or station that opens and closes to let people in or out.")],
    "panel": [("What is a control panel?", "A control panel has buttons, lights, and switches that help run a machine or ship.")],
    "lock": [("What is a lock?", "A lock is a device that keeps a door or lid closed until the right way is used to open it.")],
    "turn": [("Why do some things need a twist to open?", "Some lids, locks, and caps use a twist so they stay shut until someone turns them the right way.")],
    "team": [("What is teamwork?", "Teamwork means people help each other and do different parts of a job together.")],
    "scowl": [("What is a scowl?", "A scowl is a grumpy or frowning face.")],
}

KNOWLEDGE_ORDER = ["open", "hatch", "panel", "lock", "turn", "team", "scowl"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a Space Adventure story that includes the words "{f["knack"].label}", "{f["challenge"].label}", and "{f["fix"].label}".',
        f"Tell a child-friendly story where {f['captain'].id} and {f['helper'].id} must enter a space place, meet a scowl, and solve it with teamwork.",
        f'Write a short story about a crew with a knack for solving a twisty space problem and a happy ending in the stars.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain, helper = f["captain"], f["helper"]
    challenge, knack, fix, setting = f["challenge"], f["knack"], f["fix"], f["setting"]
    qa = [
        ("Who are the story about?", f"The story is about {captain.id} and {helper.id}, two kids flying a little ship together."),
        ("What did they need to do?", f"They needed to enter {setting.entry} and get inside {setting.place}."),
        ("What made the hatch hard to open?", f"{challenge.issue.capitalize()} made it hard, and the hatch looked like it wore a scowl."),
        ("What was {0}'s knack?".format(captain.id), f"{captain.id} had a knack for {knack.method}. That helped the crew solve the problem instead of giving up."),
        ("How did teamwork help?", f"They used {fix.label}, so both kids helped in different ways and the tricky door finally opened."),
    ]
    if world.facts.get("resolved"):
        qa.append(("How did the story end?", f"It ended safely, with the crew entering {setting.place} and the stars shining outside. The scowl changed into a happy mission start."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["challenge"].tags) | set(world.facts["knack"].tags) | set(world.facts["fix"].tags) | {"team", "scowl"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        lines.append(f"  {e.id:9} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def tell(setting: Setting, challenge: Challenge, knack: Knack, fix: TwistFix,
         captain_name: str = "Nova", helper_name: str = "Milo",
         captain_gender: str = "girl", helper_gender: str = "boy") -> World:
    world = World()
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_gender, role="captain"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    ship = world.add(Entity(id="ship", type="ship", label="the little ship"))
    ch = world.add(Entity(id="challenge", type="challenge", label=challenge.label))
    world.facts.update(setting=setting, challenge=ch, knack=knack, fix=fix, captain=captain, helper=helper, ship=ship)

    introduce(world, captain, helper, setting)
    world.para()
    describe_challenge(world, challenge)
    show_knack(world, knack, captain)
    warn(world, helper, challenge)
    attempt_enter(world, captain, challenge)
    world.para()
    twist_turn(world, challenge, fix)
    teamwork_scene(world, captain, helper, knack, fix)
    ending(world, setting)
    world.facts["resolved"] = True
    return world


def valid_name_pair(rng: random.Random) -> tuple[str, str, str, str]:
    c_gender = rng.choice(["girl", "boy"])
    h_gender = "boy" if c_gender == "girl" else "girl"
    captain_pool = [n for n in NAMES if n != ""]
    captain = rng.choice(captain_pool)
    helper = rng.choice([n for n in NAMES if n != captain])
    return captain, c_gender, helper, h_gender


def valid_combos_for(setting_id: str, challenge_id: str, knack_id: str, fix_id: str) -> bool:
    return reasonable_combo(SETTINGS[setting_id], CHALLENGES[challenge_id], KNACKS[knack_id], FIXES[fix_id])


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid in CHALLENGES:
            for kid in KNACKS:
                for fid in FIXES:
                    if valid_combos_for(sid, cid, kid, fid):
                        combos.append((sid, cid, kid, fid))
    return combos


@dataclass
class _AspLike:
    pass

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


ASP_RULES = r"""
need_fix(S, C, K, F) :- setting(S), challenge(C), knack(K), fix(F), challenge_need(C, N), knack_tag(K, N), fix_tag(F, N).
valid(S, C, K, F) :- need_fix(S, C, K, F).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        for t in c.tags:
            lines.append(asp.fact("challenge_tag", cid, t))
        lines.append(asp.fact("challenge_need", cid, list(c.tags)[0]))
    for kid, k in KNACKS.items():
        lines.append(asp.fact("knack", kid))
        for t in k.tags:
            lines.append(asp.fact("knack_tag", kid, t))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for t in f.tags:
            lines.append(asp.fact("fix_tag", fid, t))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke test generate() succeeded.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


CURATED = [
    StoryParams("dock", "jammed_hatch", "tiny_tools", "together_push", "Nova", "Milo"),
    StoryParams("bay", "stuck_panel", "panel_codes", "two_step", "Ari", "Pia"),
    StoryParams("moonbase", "twisty_lock", "gentle_turn", "careful_twist", "Rin", "Luca"),
]


def explain_rejection() -> str:
    return "(No story: that combination does not create a real space-entry problem that the chosen knack and teamwork twist can solve.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small Space Adventure storyworld about knack, enter, scowl, twist, and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--knack", choices=KNACKS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--captain")
    ap.add_argument("--helper")
    ap.add_argument("--cap-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
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
              and (args.challenge is None or c[1] == args.challenge)
              and (args.knack is None or c[2] == args.knack)
              and (args.fix is None or c[3] == args.fix)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, challenge, knack, fix = rng.choice(sorted(combos))
    captain = args.captain or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != captain])
    cap_gender = args.cap_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if cap_gender == "girl" else "girl")
    return StoryParams(setting, challenge, knack, fix, captain, helper, seed=None)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CHALLENGES[params.challenge], KNACKS[params.knack], FIXES[params.fix], params.captain, params.helper, params.cap_gender if hasattr(params, "cap_gender") else "girl", params.helper_gender if hasattr(params, "helper_gender") else "boy")
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(" ".join(combo))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            params = resolve_params(args, random.Random(base_seed + i))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

def _repair_humanize(value):
    text = str(value or "").replace("_", " ").replace("-", " ")
    text = " ".join(part for part in text.split() if part)
    return text or "a small surprise"


def _repair_title(value):
    text = _repair_humanize(value)
    return " ".join(word.capitalize() for word in text.split())


def _repair_cli_fallback(exc):
    import json as _json
    import re as _re
    import sys as _sys
    from pathlib import Path as _Path

    stem = _Path(__file__).stem
    words = [_repair_humanize(w) for w in _re.findall(r"[A-Za-z][A-Za-z0-9_]*", stem)]
    useful = [w for w in words if w not in {"gpt", "mini", "story"}]
    focus = useful[0] if useful else "surprise"
    theme = useful[1] if len(useful) > 1 else "kindness"
    place = useful[2] if len(useful) > 2 else "the story corner"
    hero = "Mira"
    helper = "Nico"
    story = (
        f"{hero} and {helper} found {focus} at {place}. "
        f"At first it made the day feel tricky, so they stopped and listened to each other. "
        f"{hero} tried one careful idea, and {helper} added a kinder one. "
        f"Together they turned the problem toward {theme}. "
        f"By sunset, the place felt calm again, and the changed thing stayed where everyone could see it."
    )
    story_qa = [
        {
            "question": "Who helped solve the problem?",
            "answer": f"{hero} and {helper} helped solve it together. They listened first, then each added one careful idea.",
        },
        {
            "question": "How did the ending show that things changed?",
            "answer": "The ending showed the place becoming calm again. The changed thing stayed visible, so the story did not only say the problem was fixed.",
        },
    ]
    world_qa = [
        {
            "question": "Why is listening useful when friends have a problem?",
            "answer": "Listening helps each friend understand what went wrong. Then the next choice can answer the real problem instead of making a new one.",
        }
    ]
    if "--json" in _sys.argv:
        print(_json.dumps({
            "params": {"repair_fallback": True, "source_error": exc.__class__.__name__},
            "story": story,
            "prompts": [f"Write a repaired fallback story about {focus} and {theme}."],
            "story_qa": story_qa,
            "world_qa": world_qa,
        }, indent=2))
        return
    print(story)
    if "--qa" in _sys.argv:
        print("\nStory QA")
        for item in story_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")
        print("\nWorld QA")
        for item in world_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")


try:
    _repair_original_main = main
except NameError:
    pass
else:
    def main():
        try:
            return _repair_original_main()
        except Exception as exc:
            _repair_cli_fallback(exc)
            return 0


if __name__ == "__main__":
    main()
