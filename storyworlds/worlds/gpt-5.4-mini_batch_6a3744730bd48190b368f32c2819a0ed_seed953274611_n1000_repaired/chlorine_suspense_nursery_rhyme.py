#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/chlorine_suspense_nursery_rhyme.py
===================================================================

A tiny storyworld from the seed words "chlorine", Suspense, and Nursery Rhyme.

Premise:
A little child and a careful grown-up are getting ready for a bath-time / wash-day
scene. A bottle of chlorine cleaner is left within reach. The child notices the
bottle, a small risky moment hangs in the air, and the grown-up calmly moves it
away, seals the lid, and brings in a safe substitute.

The story is written in a nursery-rhyme cadence, but the world model still
drives the tension: the bottle may tip, a smell may spread, worry rises, then a
careful fix restores safety and ends with a gentle rhyme-like image.

The script supports the standard storyworld CLI and includes a Python gate plus
an inline ASP twin for parity checking.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class Tone:
    id: str
    rhyme: str
    opener: str
    small_place: str
    ending_image: str
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
class Hazard:
    id: str
    label: str
    phrase: str
    smell: str
    can_spread: bool = True
    dangerous: bool = True
    tags: set[str] = field(default_factory=set)
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


@dataclass
class SafeAction:
    id: str
    label: str
    phrase: str
    text: str
    fail: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)
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


@dataclass
class World:
    tone: Tone
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.tone)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w
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


def _r_smell(world: World) -> list[str]:
    out: list[str] = []
    bottle = world.entities.get("bottle")
    if bottle and bottle.meters["open"] >= THRESHOLD and ("smell", "bottle") not in world.fired:
        world.fired.add(("smell", "bottle"))
        if "room" in world.entities:
            world.get("room").meters["worry"] += 1
        for e in list(world.entities.values()):
            if e.role in {"child", "helper"}:
                e.memes["worry"] += 1
        out.append("__smell__")
    return out


def _r_tip(world: World) -> list[str]:
    out: list[str] = []
    bottle = world.entities.get("bottle")
    if bottle and bottle.meters["open"] >= THRESHOLD and bottle.meters["tipped"] >= THRESHOLD and ("tip", "bottle") not in world.fired:
        world.fired.add(("tip", "bottle"))
        if "floor" in world.entities:
            world.get("floor").meters["wet"] += 1
        out.append("__tip__")
    return out


CAUSAL_RULES = [Rule("smell", _r_smell), Rule("tip", _r_tip)]


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


def spill_risk(hazard: Hazard) -> bool:
    return hazard.dangerous and hazard.can_spread


def reasonable_actions() -> list[SafeAction]:
    return [a for a in ACTIONS.values() if a.sense >= SENSE_MIN]


def choose_action(rng: random.Random) -> SafeAction:
    return rng.choice(reasonable_actions())


def leak_severity(tip_delay: int) -> int:
    return 1 + max(0, tip_delay)


def action_contains(action: SafeAction, delay: int) -> bool:
    return action.power >= leak_severity(delay)


def is_opening_allowed(hazard: Hazard) -> bool:
    return spill_risk(hazard)


def normalize_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", name).strip("_") or "X"


def predict(world: World) -> dict:
    sim = world.copy()
    _open_bottle(sim, narrate=False)
    return {
        "smell": sim.get("room").meters["worry"] >= THRESHOLD,
        "wet": sim.get("floor").meters["wet"] >= THRESHOLD,
    }


def _open_bottle(world: World, narrate: bool = True) -> None:
    bottle = world.get("bottle")
    bottle.meters["open"] += 1
    propagate(world, narrate=narrate)


def _tip_bottle(world: World, narrate: bool = True) -> None:
    bottle = world.get("bottle")
    bottle.meters["tipped"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, helper: Entity, tone: Tone, hazard: Hazard) -> None:
    child.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(
        f"{tone.opener} {child.id} and {helper.id} were humming a small tune, "
        f"and the laundry room felt neat as a pin. "
        f"A little shelf stood by the sink, and on it sat {hazard.phrase}."
    )
    world.say(
        f"{child.id} peeped at the bottle while {helper.id} folded towels. "
        f"It was a quiet little room, but a quiet room can still hold a worry."
    )


def suspense(world: World, child: Entity, helper: Entity, hazard: Hazard) -> None:
    pred = predict(world)
    if pred["smell"]:
        world.say(
            f"{child.id} reached up, and for one tiny breath the bottle seemed to wobble. "
            f"{helper.id} looked over at once. \"Careful now,\" {helper.pronoun()} said, "
            f\"\"the {hazard.label} has a sharp smell.\""
        )
    else:
        world.say(
            f"{child.id} reached up, and for one tiny breath the bottle seemed to wobble. "
            f"{helper.id} looked over at once, because even a little wobble can make a big fuss."
        )
    world.facts["predicted"] = pred


def tempt(world: World, child: Entity, hazard: Hazard) -> None:
    child.memes["bold"] += 1
    world.say(
        f"\"What's this?\" asked {child.id}, very soft and slow. "
        f"\"It says {hazard.label}.\""
    )


def warn(world: World, helper: Entity, child: Entity, hazard: Hazard) -> None:
    helper.memes["care"] += 1
    world.say(
        f"{helper.id} knelt down and said, \"{hazard.label.capitalize()} is not a toy, dear. "
        f"It can sting your nose, and that is not a merry choice.\""
    )


def close_lid(world: World, helper: Entity, hazard: Hazard) -> None:
    bottle = world.get("bottle")
    bottle.meters["open"] = 0
    bottle.memes["safe"] += 1
    world.say(
        f"{helper.id} took the bottle with two careful hands, twisted the lid shut, "
        f"and set {hazard.label} high on the shelf."
    )


def safe_switch(world: World, child: Entity, helper: Entity, action: SafeAction) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"Then {helper.id} brought out {action.phrase}. {action.text}"
    )
    world.say(
        f"{child.id} smiled, because the little room could still be useful and safe."
    )


def ending(world: World, child: Entity, helper: Entity, tone: Tone) -> None:
    world.say(
        f"{tone.ending_image} {child.id} and {helper.id} tidied the room, "
        f"and the scary little minute was gone like a bubble."
    )


def tell(tone: Tone, hazard: Hazard, action: SafeAction, child_name: str, child_gender: str, helper_gender: str) -> World:
    world = World(tone)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label="the grown-up", role="helper"))
    room = world.add(Entity(id="room", type="room", label="the room"))
    floor = world.add(Entity(id="floor", type="floor", label="the floor"))
    bottle = world.add(Entity(id="bottle", type="thing", label=hazard.label))
    world.facts["tone"] = tone
    world.facts["hazard"] = hazard
    world.facts["action"] = action
    world.facts["child"] = child
    world.facts["helper"] = helper

    setup(world, child, helper, tone, hazard)
    world.para()
    tempt(world, child, hazard)
    warn(world, helper, child, hazard)
    suspense(world, child, helper, hazard)

    if action_contains(action, 0):
        _tip_bottle(world, narrate=False)
        world.say(
            f"The bottle wobbled and nearly sang a tiny bad song, but {helper.id} caught it."
        )
        close_lid(world, helper, hazard)
        safe_switch(world, child, helper, action)
        ending(world, child, helper, tone)
        outcome = "contained"
    else:
        _open_bottle(world, narrate=False)
        world.say(
            f"The lid slipped open, and the sharp smell floated out. "
            f"{helper.id} moved fast and turned it back at once."
        )
        close_lid(world, helper, hazard)
        safe_switch(world, child, helper, action)
        ending(world, child, helper, tone)
        outcome = "contained"

    world.facts["outcome"] = outcome
    return world


TONES = {
    "little_room": Tone(
        id="little_room",
        rhyme="In a little room, in a little gloom,",
        opener="In a little room, in a little gloom,",
        small_place="little room",
        ending_image="And so, by the window and the washing pail,",
    ),
    "moon_mop": Tone(
        id="moon_mop",
        rhyme="By the moon and the mop, in a hush-hush stop,",
        opener="By the moon and the mop, in a hush-hush stop,",
        small_place="hush-hush place",
        ending_image="And when the moon went dim and the towels were neat,",
    ),
    "soft_sink": Tone(
        id="soft_sink",
        rhyme="At the soft little sink where the clean things wink,",
        opener="At the soft little sink where the clean things wink,",
        small_place="soft little sink",
        ending_image="And when the sink grew still and the shelf sat high,",
    ),
}

HAZARDS = {
    "chlorine": Hazard(
        id="chlorine",
        label="chlorine",
        phrase="a bottle of chlorine cleaner",
        smell="sharp",
        can_spread=True,
        dangerous=True,
        tags={"chlorine", "cleaning"},
    )
}

ACTIONS = {
    "soap": SafeAction(
        id="soap",
        label="soap",
        phrase="a bowl of soap bubbles",
        text="They blew the bubbles one by one, and the air went sweet instead of sharp.",
        fail="They tried to use the bubbles, but bubbles are for laughing, not for cleaning spills.",
        power=1,
        sense=3,
        tags={"safe", "bath"},
    ),
    "water": SafeAction(
        id="water",
        label="water",
        phrase="a cup of plain water and a cloth",
        text="They wiped the shelf and washed their hands, nice and slow.",
        fail="They splashed a little water, but that was not the kind of fix they needed.",
        power=2,
        sense=3,
        tags={"safe", "clean"},
    ),
    "caddy": SafeAction(
        id="caddy",
        label="caddy",
        phrase="a tidy cleaning caddy",
        text="They put the bottle inside the caddy and carried it away from little fingers.",
        fail="They looked for the caddy, but it was too small to hide the bottle safely.",
        power=3,
        sense=4,
        tags={"safe", "clean"},
    ),
}


@dataclass
class StoryParams:
    tone: str
    hazard: str
    action: str
    child: str
    child_gender: str
    helper_gender: str
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
    StoryParams(tone="little_room", hazard="chlorine", action="caddy", child="Mia", child_gender="girl", helper_gender="mother"),
    StoryParams(tone="moon_mop", hazard="chlorine", action="water", child="Ben", child_gender="boy", helper_gender="father"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for t in TONES:
        for h in HAZARDS:
            if not is_opening_allowed(HAZARDS[h]):
                continue
            for a in ACTIONS:
                if ACTIONS[a].sense >= SENSE_MIN:
                    out.append((t, h, a))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Suspenseful nursery-rhyme chlorine storyworld.")
    ap.add_argument("--tone", choices=TONES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["mother", "father"])
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
    if args.action and ACTIONS[args.action].sense < SENSE_MIN:
        raise StoryError("That action is too weak or too odd for this story.")
    combos = [c for c in valid_combos()
              if (args.tone is None or c[0] == args.tone)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    tone, hazard, action = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    child = args.child or rng.choice(["Mia", "Ben", "Nia", "Finn"])
    return StoryParams(tone=tone, hazard=hazard, action=action, child=child, child_gender=child_gender, helper_gender=helper_gender)


def generate(params: StoryParams) -> StorySample:
    if params.tone not in TONES or params.hazard not in HAZARDS or params.action not in ACTIONS:
        raise StoryError("Invalid StoryParams.")
    world = tell(TONES[params.tone], HAZARDS[params.hazard], ACTIONS[params.action], params.child, params.child_gender, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    tone = f["tone"]
    hazard = f["hazard"]
    action = f["action"]
    child = f["child"]
    return [
        f'Write a nursery-rhyme style suspense story that includes "{hazard.label}" and ends safely.',
        f"Tell a gentle suspense story where {child.id} notices {hazard.label} in {tone.small_place} and a grown-up helps right away.",
        f"Write a child-friendly rhyme about a risky bottle and a calm fix using {action.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    hazard = f["hazard"]
    action = f["action"]
    return [
        ("What was the risky bottle called?", f"It was called {hazard.label}. It was a cleaner bottle, so the grown-up treated it carefully."),
        (f"Who noticed the problem first?", f"{child.id} noticed it first. The little wobble made the room feel worried before the grown-up moved in."),
        ("How did they keep everyone safe?", f"{helper.id} shut the lid and moved the bottle away, then they used {action.phrase} instead. That kept the sharp stuff from reaching little hands."),
        ("How did the story end?", f"It ended with the bottle safely put away and the room calm again. The scary moment shrank, and the rhyme-like day became neat and safe."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is chlorine?", "Chlorine is a strong cleaning chemical. People use it carefully because it can be harmful if it is spilled or breathed in too closely."),
        ("Why should a child not play with cleaning chemicals?", "Cleaning chemicals are for grown-ups. They can sting, smell sharp, and make people sick if they are used the wrong way."),
        ("What should you do if a bottle tips over?", "Move away and tell a grown-up right away. A careful helper can close it, clean it, and keep the room safe."),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(x for x, *_ in world.fired)}")
    return "\n".join(lines)


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
hazard(chlorine).
sense(action(A), S) :- action_sense(A, S).
sensible(A) :- action(A), action_sense(A, S), sense_min(M), S >= M.
valid(T, H, A) :- tone(T), hazard(H), action(A), hazard(H), sensible(A).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("sense_min", SENSE_MIN)]
    for t in TONES:
        lines.append(asp.fact("tone", t))
    for h in HAZARDS:
        lines.append(asp.fact("hazard", h))
    for a, act in ACTIONS.items():
        lines.append(asp.fact("action", a))
        lines.append(asp.fact("action_sense", a, act.sense))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combos differ.")
        rc = 1
    else:
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    if set(asp_sensible()) != {a for a in ACTIONS if ACTIONS[a].sense >= SENSE_MIN}:
        print("MISMATCH: sensible actions differ.")
        rc = 1
    else:
        print("OK: sensible actions match.")
    try:
        sample = generate(resolve_params(argparse.Namespace(tone=None, hazard=None, action=None, child=None, child_gender=None, helper_gender=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: normal story generation smoke test passed.")
    except Exception as exc:
        print(f"FAIL: generation smoke test failed: {exc}")
        rc = 1
    return rc


def explain_rejection(action: SafeAction) -> str:
    return f"(No story: action '{action.id}' is too weak for this world.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for t, h, a in combos:
            print(t, h, a)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
