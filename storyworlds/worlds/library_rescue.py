#!/usr/bin/env python3
"""
storyworlds/worlds/library_rescue.py
===============================

A standalone StoryWorld for a library rescue theme.

The model introduces a lost object in a library, a method to recover it, and a
compatible helper response. Variations are constrained by a place/object/method
compatibility gate to prevent implausible combinations.
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
from typing import Callable, Iterable

# Keep imports local and direct, matching the storyworld contract.
os_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os_root not in sys.path:
    sys.path.insert(0, os_root)

from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"         # "character" | "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "father", "uncle", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "mother", "aunt", "woman", "librarian", "teacher", "librarian_mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass(frozen=True)
class Place:
    id: str
    phrase: str
    objects: set[str]
    methods: set[str]
    risks: set[str]


@dataclass(frozen=True)
class RescueTarget:
    id: str
    phrase: str
    noun: str
    zone: str
    fragile: bool
    requires_staff: bool
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class RescueMethod:
    id: str
    phrase: str
    approach: str
    risk_zones: set[str]
    solves: set[str]
    risk_level: float = 0.0
    uses_staff: bool = False
    safe_for_fragile: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    target: str
    method: str
    hero: str
    gender: str
    helper: str
    seed: int | None = None


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

        self.warning = False
        self.rescued = False
        self.hero: Entity | None = None
        self.helper: Entity | None = None
        self.target: Entity | None = None

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.warning = self.warning
        clone.rescued = self.rescued
        clone.hero = clone.entities.get("Hero")
        clone.helper = clone.entities.get("Helper")
        clone.target = clone.entities.get("Target")
        return clone

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for ent in self.entities.values():
            meters = {k: v for k, v in ent.meters.items() if v}
            memes = {k: v for k, v in ent.memes.items() if v}
            lines.append(
                f"  {ent.id:<8} ({ent.type:<10}) kind={ent.kind} meters={dict(meters)} memes={dict(memes)}"
            )
        lines.append(f"  warning: {self.warning}")
        lines.append(f"  rescued: {self.rescued}")
        lines.append(f"  fired rules: {sorted(self.fired)}")
        return "\n".join(lines)


PLACES: dict[str, Place] = {
    "children_corner": Place(
        id="children_corner",
        phrase="the children's corner of the library",
        objects={"picture_book", "storybook", "blue_globe"},
        methods={"ask_librarian", "use_stool", "soft_hook"},
        risks={"narrow", "low_light"},
    ),
    "history_archive": Place(
        id="history_archive",
        phrase="the archive stacks in the history hall",
        objects={"bronze_medal", "ledgers", "blue_globe"},
        methods={"ask_librarian", "use_stool", "short_ladder"},
        risks={"high_shelf", "dust"},
    ),
    "reading_room": Place(
        id="reading_room",
        phrase="the quiet reading room near the tall book shelves",
        objects={"atlas", "storybook", "ledgers"},
        methods={"ask_librarian", "soft_hook", "short_ladder"},
        risks={"quiet", "high_shelf"},
    ),
}

TARGETS: dict[str, RescueTarget] = {
    "storybook": RescueTarget(
        id="storybook",
        phrase="a bright children's storybook",
        noun="the storybook",
        zone="table",
        fragile=True,
        requires_staff=False,
        tags={"paper", "child"},
    ),
    "atlas": RescueTarget(
        id="atlas",
        phrase="a heavy atlas",
        noun="the atlas",
        zone="shelf",
        fragile=False,
        requires_staff=False,
        tags={"large", "paper"},
    ),
    "blue_globe": RescueTarget(
        id="blue_globe",
        phrase="a clear blue globe on a high stand",
        noun="the blue globe",
        zone="shelf",
        fragile=True,
        requires_staff=False,
        tags={"fragile", "glass", "high_shelf"},
    ),
    "ledgers": RescueTarget(
        id="ledgers",
        phrase="an old ledger box packed on a high shelf",
        noun="the ledgers",
        zone="high_shelf",
        fragile=False,
        requires_staff=True,
        tags={"valuable", "heavy", "archival"},
    ),
}

METHODS: dict[str, RescueMethod] = {
    "ask_librarian": RescueMethod(
        id="ask_librarian",
        phrase="asked the librarian for help",
        approach="asked for the librarian’s help to bring it down",
        risk_zones=set(),
        solves={"shelf", "table", "high_shelf"},
        risk_level=0.0,
        uses_staff=True,
        safe_for_fragile=True,
        tags={"safe", "gentle"},
    ),
    "use_stool": RescueMethod(
        id="use_stool",
        phrase="stood on a step stool",
        approach="stood on a step stool and leaned carefully",
        risk_zones={"narrow", "low_light"},
        solves={"shelf", "table"},
        risk_level=0.6,
        uses_staff=False,
        safe_for_fragile=False,
        tags={"ordinary", "height"},
    ),
    "soft_hook": RescueMethod(
        id="soft_hook",
        phrase="used a long soft-grip hook",
        approach="used a soft-grip hook to slide it forward",
        risk_zones={"dust"},
        solves={"shelf", "table", "high_shelf"},
        risk_level=0.3,
        uses_staff=False,
        safe_for_fragile=True,
        tags={"tool", "gentle"},
    ),
    "short_ladder": RescueMethod(
        id="short_ladder",
        phrase="climbed a short ladder",
        approach="climbed a short ladder and reached up",
        risk_zones={"high_shelf"},
        solves={"shelf", "high_shelf"},
        risk_level=0.9,
        uses_staff=False,
        safe_for_fragile=False,
        tags={"active", "height"},
    ),
}

HERO_NAMES: dict[str, list[str]] = {
    "girl": ["Lena", "Maya", "Nora", "Sana", "Iris"],
    "boy": ["Timo", "Noah", "Kai", "Leo", "Eli"],
}

HELPERS = ("librarian", "aunt", "uncle", "teacher", "volunteer")


RULES: list[Rule] = []


def _helper_label(helper_key: str) -> str:
    labels = {
        "librarian": "the librarian",
        "teacher": "the teacher",
        "volunteer": "the volunteer",
        "aunt": "the aunt",
        "uncle": "the uncle",
    }
    return labels.get(helper_key, helper_key.replace("_", " "))


def _r_warning(world: World) -> list[str]:
    if world.facts.get("attempted") is None:
        return []
    if world.warning:
        return []
    risk = world.facts.get("risk_level", 0.0)
    if risk < THRESHOLD:
        return []
    world.warning = True
    sig = ("warning", str(world.facts.get("method_id")))
    if sig in world.fired:
        return []
    world.fired.add(sig)

    hero = world.hero
    helper = world.helper
    target = world.target
    method = world.facts["method_obj"]
    if hero is None or helper is None or target is None or not isinstance(method, RescueMethod):
        return []
    target_ref = target.label
    hero.memes["fear"] += 1
    helper.memes["care"] += 1
    return [
        f"{helper.label} warned that using {method.approach} in this zone could make it hard for {hero.label} to keep {target_ref} safe."
    ]


def _r_rescue(world: World) -> list[str]:
    if world.facts.get("attempted") is None:
        return []
    if world.rescued:
        return []
    target = world.target
    hero = world.hero
    helper = world.helper
    method = world.facts["method_obj"]
    if hero is None or target is None or helper is None or not isinstance(method, RescueMethod):
        return []
    target_ref = target.label
    sig = ("rescue", target.id, method.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)

    place = world.place
    world.rescued = True
    target.memes["rescued"] += 1
    if method.id == "ask_librarian":
        sentence = (
            f"{hero.label} {method.approach}, and {helper.label} brought {target_ref} down from {place.phrase},"
            f" then handed it back gently."
        )
    elif method.id == "short_ladder":
        sentence = (
            f"{hero.label} {method.approach} and, with {helper.label} staying close,"
            f" lowered {target_ref} carefully."
        )
    elif method.id == "use_stool":
        sentence = (
            f"{hero.label} used a step stool, reached up slowly, and pulled {target_ref} back to the floor."
        )
    else:
        sentence = (
            f"{hero.label} {method.approach} and guided the long tool until {target_ref} came into reach."
        )
    return [sentence]


def _r_celebrate(world: World) -> list[str]:
    if not world.rescued:
        return []
    sig = ("celebrate", world.target.id if world.target is not None else "")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.hero
    target = world.target
    if hero is None or target is None:
        return []
    hero.memes["kindness"] += 1
    return [f"{hero.label} smiled because {target.label} was safe again and thanked {hero.pronoun('possessive')} helper. "]


RULES.extend([
    Rule("warn", "safety", _r_warning),
    Rule("rescue", "action", _r_rescue),
    Rule("celebrate", "social", _r_celebrate),
])


def propagate(world: World, narrate: bool = True) -> list[str]:
    sentences: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            generated = rule.apply(world)
            if generated:
                changed = True
                sentences.extend(generated)
    if narrate:
        for sentence in sentences:
            world.say(sentence)
    return sentences


def valid_combo(place_id: str, target_id: str, method_id: str) -> bool:
    if place_id not in PLACES or target_id not in TARGETS or method_id not in METHODS:
        return False

    place = PLACES[place_id]
    target = TARGETS[target_id]
    method = METHODS[method_id]

    if target_id not in place.objects:
        return False
    if method_id not in place.methods:
        return False
    if target.zone not in method.solves:
        return False
    if target.requires_staff and not method.uses_staff:
        return False
    if target.fragile and not method.safe_for_fragile and bool(method.risk_zones & place.risks):
        return False
    return True


def explain_rejection(place_id: str, target_id: str, method_id: str) -> str:
    if place_id not in PLACES:
        return f"No story: unknown place {place_id!r}."
    if target_id not in TARGETS:
        return f"No story: unknown target {target_id!r}."
    if method_id not in METHODS:
        return f"No story: unknown method {method_id!r}."

    place = PLACES[place_id]
    target = TARGETS[target_id]
    method = METHODS[method_id]

    if target_id not in place.objects:
        return f"No story: {target.phrase} is not present in {place.phrase}."
    if method_id not in place.methods:
        return f"No story: {method.phrase} is not suitable for {place.phrase}."
    if target.zone not in method.solves:
        return (
            f"No story: {method.phrase} does not solve a {target.zone.replace('_', ' ')} retrieval."
        )
    if target.requires_staff and not method.uses_staff:
        return f"No story: {target.phrase} needs staff support, so {method.phrase} is not appropriate."
    if target.fragile and not method.safe_for_fragile and bool(method.risk_zones & place.risks):
        return (
            f"No story: {method.phrase} is too rough for {target.phrase} in {place.phrase}."
        )
    return "No story: constraints failed."


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for target_id in TARGETS:
            for method_id in METHODS:
                if valid_combo(place_id, target_id, method_id):
                    combos.append((place_id, target_id, method_id))
    return sorted(combos)


def risk_level(place: Place, target: RescueTarget, method: RescueMethod) -> float:
    if method.risk_level <= 0:
        return 0.0
    if not (method.risk_zones & place.risks):
        return 0.0
    extra = 0.2 if target.fragile else 0.0
    return method.risk_level + extra


def estimate_danger(place: Place, target: RescueTarget, method: RescueMethod) -> bool:
    return risk_level(place, target, method) >= THRESHOLD


def attempt_rescue(world: World, method: RescueMethod) -> None:
    hero = world.hero
    target = world.target
    if hero is None or target is None:
        return
    world.facts["method_id"] = method.id
    world.facts["method_obj"] = method
    world.facts["attempted"] = True
    world.facts["method_phrase"] = method.approach

    risk = world.facts.get("risk_score", 0.0)
    if risk >= THRESHOLD:
        target.memes["distress"] += 1
        world.warning = True
    hero.memes["carefulness"] += 1
    target.memes["attached"] += 1
    propagate(world, narrate=True)


def build_intro(world: World, hero: Entity, helper: Entity, target: RescueTarget, place: Place) -> None:
    pron = "little" if "child" in hero.traits else ""
    world.say(
        f"Once upon a time, there was a {pron} {hero.type} named {hero.label} in {place.phrase}."
    )
    helper_tone = "caring" if helper.type in {"librarian", "teacher", "aunt", "uncle"} else "helpful"
    world.say(f"{helper.label.capitalize()} was organizing books nearby and watching with {helper_tone} attention.")


def notice_and_want(world: World, hero: Entity, target: RescueTarget, method: RescueMethod, place: Place) -> None:
    world.say(
        f"One day, {hero.label} noticed {target.phrase} resting out of reach near the shelves in {place.phrase}."
    )
    world.say(
        f'"I want {target.noun}," {hero.label} said, "and I can help safely if I slow down."'
    )


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    target_cfg = TARGETS[params.target]
    method_cfg = METHODS[params.method]

    if not valid_combo(params.place, params.target, params.method):
        raise StoryError(explain_rejection(params.place, params.target, params.method))

    world = World(place)

    hero = world.add(
        Entity(
            id="Hero",
            kind="character",
            type=params.gender,
            label=params.hero,
            traits=["child", "little"],
        )
    )
    helper_key = "librarian" if method_cfg.uses_staff else params.helper
    helper_name = _helper_label(helper_key)
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type="librarian" if "libr" in helper_key else helper_key,
            label=helper_name,
        )
    )
    target = world.add(
        Entity(
            id="Target",
            kind="thing",
            type=params.target,
            label=target_cfg.phrase,
        )
    )

    world.hero = hero
    world.helper = helper
    world.target = target

    place = PLACES[params.place]
    target_cfg = TARGETS[params.target]
    method_cfg = METHODS[params.method]

    world.facts.update(
        {
            "place_id": place.id,
            "place": place,
            "target_cfg": target_cfg,
            "target_id": target_cfg.id,
            "method_cfg": method_cfg,
            "method_id": method_cfg.id,
            "helper": helper,
            "method_phrase": method_cfg.approach,
            "helper_name": helper_name,
            "risk_score": risk_level(place, target_cfg, method_cfg),
        }
    )

    build_intro(world, hero, helper, target_cfg, place)
    world.para()
    notice_and_want(world, hero, target_cfg, method_cfg, place)
    world.para()

    attempt_rescue(world, method_cfg)
    world.para()

    if world.warning:
        world.say(
            f"Because of the risk in {place.phrase}, {hero.label} chose each move with care and gratitude."
        )
    world.say(
        f"{hero.label} learned that asking the right helper or tool for the right object keeps everyone safe in the library."
    )

    world.facts.update(
        {
            "hero": hero,
            "helper_entity": helper,
            "target_entity": target,
            "rescued": world.rescued,
            "place_cfg": place,
            "target_cfg": target_cfg,
            "method_cfg": method_cfg,
        }
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    target = f["target_cfg"]
    method = f["method_cfg"]
    hero = f["hero"]
    return [
        f"Write a children story set in a library where {hero.label} finds and rescues {target.phrase}.",
        f"Use {place.phrase}, {target.phrase}, and a rescue where the child {method.phrase}.",
        "Focus on the consequence of choosing the method safely versus taking unnecessary risk.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    place = f["place"]
    hero = f["hero"]
    helper = f["helper_entity"]
    target = f["target_cfg"]
    method = f["method_cfg"]

    return [
        QAItem(
            "Who were the main characters?",
            f"The story follows {hero.label}, who is the child rescuer, and {helper.label}, who helped with the rescue. The helper matters because the safe method depends on matching the object, shelf, and place instead of grabbing quickly.",
        ),
        QAItem(
            "Where did the rescue take place?",
            f"It happened in {place.phrase}. That location matters because its risks, such as narrow space, low light, dust, or height, affect which rescue methods are valid.",
        ),
        QAItem(
            "What did the child rescue?",
            f"The child rescued {target.phrase} from a difficult spot. The target's fragility, weight, or height controls whether the story allows a stool, hook, ladder, or librarian help.",
        ),
        QAItem(
            "How did the chosen method keep the rescue safe?",
            f"The child {method.phrase}, and {helper.label} stayed nearby to keep it safe. The method is compatible here because it solves {', '.join(s.replace('_', ' ') for s in sorted(method.solves))} without ignoring the library risk.",
        ),
        QAItem(
            f"What lesson did {hero.label} learn?",
            f"{hero.label} learned that matching the method to the object and place keeps fragile items safe. In this world, care means choosing a method the room actually supports.",
        ),
    ]


WORLD_KNOWLEDGE: dict[str, list[tuple[str, str]]] = {
    "height": [
        ("Why avoid rushing at high places?", "Rushing near a high shelf can shift balance and drop objects. A slower method or helper gives the child time to stay steady before reaching.")
    ],
    "fragile": [
        ("Why are fragile objects handled with extra care?", "Fragile objects break more easily if pulled or dropped suddenly. The compatible method must keep the object supported instead of yanking it loose."),
    ],
    "dust": [
        ("Why can dust affect libraries?", "Fine dust can make tools and hands slippery, so people move slowly and carefully. It also makes careful visibility part of the rescue rather than a decorative detail."),
    ],
    "staff": [
        ("Why call for a staff helper?", "An adult helper can stabilize a child during a high or awkward reach. Staff help is especially important when the target or place requires permission and steady handling."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    place = world.facts["place"]
    target = world.facts["target_cfg"]
    method = world.facts["method_cfg"]

    tags = set(target.tags) | set(method.tags)
    if "high_shelf" in target.tags or "high_shelf" in place.risks:
        tags.add("height")
    if target.fragile:
        tags.add("fragile")
    if "staff" in method.id or method.uses_staff:
        tags.add("staff")
    if place.risks.intersection({"dust", "quiet", "low_light", "high_shelf", "narrow"}):
        if "dust" in place.risks:
            tags.add("dust")

    out: list[QAItem] = []
    for tag in sorted(tags):
        for question, answer in WORLD_KNOWLEDGE.get(tag, ()):  # type: ignore[arg-type]
            out.append(QAItem(question, answer))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child-level checks ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(sample.world.trace())
    if qa:
        print(format_qa(sample))


def _json_dump(samples: list[StorySample]) -> None:
    if len(samples) == 1:
        print(samples[0].to_json())
    else:
        print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))


ASP_RULES = r"""
valid(P, T, M) :- place(P), target(T), method(M), placed(P, T), method_supports(P, M), solves(M, Z), object_zone(T, Z), not blocked(P, T, M).

blocked(P, T, M) :-
    place(P), target(T), method(M),
    target_requires_staff(T), not method_uses_staff(M).
blocked(P, T, M) :-
    place(P), target(T), method(M),
    target_fragile(T), method_risky(M), method_risk_zone(M, Z), place_risk(P, Z).

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place in PLACES.values():
        lines.append(asp.fact("place", place.id))
        lines.append(asp.fact("place_phrase", place.id, place.phrase))
        for target_id in place.objects:
            lines.append(asp.fact("placed", place.id, target_id))
        for method_id in place.methods:
            lines.append(asp.fact("method_supports", place.id, method_id))
        for risk in place.risks:
            lines.append(asp.fact("place_risk", place.id, risk))
    for target in TARGETS.values():
        lines.append(asp.fact("target", target.id))
        lines.append(asp.fact("object_zone", target.id, target.zone))
        if target.fragile:
            lines.append(asp.fact("target_fragile", target.id))
        if target.requires_staff:
            lines.append(asp.fact("target_requires_staff", target.id))
        for tag in target.tags:
            lines.append(asp.fact("target_tag", target.id, tag))
    for method in METHODS.values():
        lines.append(asp.fact("method", method.id))
        lines.append(asp.fact("method_phrase", method.id, method.phrase))
        for zone in method.solves:
            lines.append(asp.fact("solves", method.id, zone))
        if method.risk_zones:
            for zone in method.risk_zones:
                lines.append(asp.fact("method_risk_zone", method.id, zone))
        if method.risk_level > 0:
            lines.append(asp.fact("method_risky", method.id))
        if method.uses_staff:
            lines.append(asp.fact("method_uses_staff", method.id))
        if method.safe_for_fragile:
            lines.append(asp.fact("method_safe_fragile", method.id))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> set[tuple[str, str, str]]:
    import asp

    combos: set[tuple[str, str, str]] = set()
    for model in asp.solve(asp_program(), models=0):
        combos.update((place, target, method) for place, target, method in asp.atoms(model, "valid"))
    return combos


def asp_verify() -> int:
    py = set(valid_combos())
    logic = asp_valid_combos()
    if py == logic:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between Python gate and ASP gate.")
    missing_in_python = sorted(logic - py)
    missing_in_asp = sorted(py - logic)
    if missing_in_python:
        print("  only in clingo: " + ", ".join(map(str, missing_in_python)))
    if missing_in_asp:
        print("  only in Python: " + ", ".join(map(str, missing_in_asp)))
    return 1


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: library rescue with place/object/method constraints."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--object", dest="target", choices=sorted(TARGETS))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--gender", choices=sorted(HERO_NAMES))
    ap.add_argument("--hero")
    ap.add_argument("--helper", choices=sorted(HELPERS))
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


def build_parser() -> argparse.ArgumentParser:
    return _build_parser()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.target is None or combo[1] == args.target)
        and (args.method is None or combo[2] == args.method)
    ]

    if not choices:
        raise StoryError(explain_rejection(
            args.place or "reading_room",
            args.target or "storybook",
            args.method or "ask_librarian",
        ))

    place_id, target_id, method_id = rng.choice(choices)

    gender = args.gender or rng.choice(sorted(HERO_NAMES))
    hero = args.hero or rng.choice(HERO_NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)

    return StoryParams(
        place=place_id,
        target=target_id,
        method=method_id,
        hero=hero,
        gender=gender,
        helper=helper,
        seed=getattr(rng, "story_seed", None),
    )


def _samples_for_all(args: argparse.Namespace) -> list[StorySample]:
    samples: list[StorySample] = []
    combos = valid_combos()
    for i, combo in enumerate(combos):
        seed = (args.seed if args.seed is not None else 4000) + i
        rng = random.Random(seed)
        rng.story_seed = seed
        place, target, method = combo
        gender = rng.choice(sorted(HERO_NAMES))
        hero = rng.choice(HERO_NAMES[gender])
        helper = rng.choice(HELPERS)
        samples.append(
            generate(
                StoryParams(
                    place=place,
                    target=target,
                    method=method,
                    hero=hero,
                    gender=gender,
                    helper=helper,
                    seed=seed,
                )
            )
        )
    return samples


def _samples_for_n(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    target_count = max(1, args.n)
    while len(samples) < target_count and i < target_count * 50:
        story_seed = base_seed + i
        rng = random.Random(story_seed)
        rng.story_seed = story_seed
        sample = generate(resolve_params(args, rng))
        if sample.story not in seen:
            seen.add(sample.story)
            samples.append(sample)
        i += 1
    return samples


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            return asp_verify()
        if args.asp:
            for place, target, method in sorted(asp_valid_combos()):
                print(f"{place}\t{target}\t{method}")
            return 0

        samples = _samples_for_all(args) if args.all else _samples_for_n(args)
        if args.json:
            _json_dump(samples)
            return 0

        for i, sample in enumerate(samples):
            header = ""
            if args.all:
                f = sample.params
                header = f"### {f.hero}: {f.target} in {f.place} via {f.method}"
            elif len(samples) > 1:
                header = f"### variant {i + 1}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if i != len(samples) - 1:
                print("\n" + "=" * 60 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
