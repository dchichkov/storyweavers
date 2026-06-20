#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pram_owe_waste_sound_effects_dialogue_space.py
==============================================================================

A tiny storyworld in a Space Adventure style: a child, a small space pram, a
mistaken promise, a wasteful mishap, and a careful repair with sound effects and
dialogue.

The world is built around one small premise:
- A child borrows a special pram-like moon cart for a pretend space trip.
- The child says they owe a helper a favor and must not waste the moon fuel.
- A careless choice causes a small spill or drift.
- A calm helper fixes it and the child learns to use the tool wisely.

This script is standalone, stdlib-only, and follows the Storyweavers contract.
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
    stars: str
    afford: set[str] = field(default_factory=set)

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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    kind: str
    risky: bool
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
class ActionCfg:
    id: str
    verb: str
    consequence: str
    sound: str
    risky_meter: str
    spread: str
    place_tags: set[str] = field(default_factory=set)
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
class FixCfg:
    id: str
    label: str
    method: str
    sound: str
    power: int
    sense: int
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


def _r_waste(world: World) -> list[str]:
    out: list[str] = []
    cart = world.entities.get("pram")
    cargo = world.entities.get("fuel")
    if not cart or not cargo:
        return out
    if cart.meters["wobble"] < THRESHOLD and cargo.meters["spill"] < THRESHOLD:
        return out
    sig = ("waste",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("ship").meters["waste"] += 1
    world.get("crew").memes["worry"] += 1
    out.append("__waste__")
    return out


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    if world.get("ship").meters["waste"] < THRESHOLD:
        return out
    sig = ("alarm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("helper").memes["alert"] += 1
    out.append("__alarm__")
    return out


CAUSAL_RULES = [Rule("waste", "physical", _r_waste), Rule("alarm", "social", _r_alarm)]


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


def reasonableness_gate(action: ActionCfg, obj: ObjectCfg, fix: FixCfg) -> bool:
    return obj.risky and action.risky_meter == obj.kind and fix.power >= 2


def sensible_fixes() -> list[FixCfg]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def outcome_of(params: "StoryParams") -> str:
    if params.fix not in FIXES:
        return "?"
    if params.delay >= 2:
        return "drift"
    return "saved" if FIXES[params.fix].power >= 2 else "drift"


def _do_action(world: World, action: ActionCfg, obj: ObjectCfg, narrate: bool = True) -> None:
    world.get("pram").meters[action.risky_meter] += 1
    if obj.risky:
        world.get("fuel").meters["spill"] += 1
    world.get("crew").memes["joy"] += 1
    propagate(world, narrate=narrate)


def set_up(world: World, hero: Entity, helper: Entity, setting: Setting, action: ActionCfg,
           obj: ObjectCfg) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"In a bright dock by the moon bay, {hero.id} and {helper.id} rolled out {setting.place}. "
        f"{setting.stars}"
    )
    world.say(
        f"{hero.id} pointed at the little space pram. \"This is our ship,\" {hero.pronoun()} said, "
        f"and the cockpit made a soft {action.sound.lower()}."
    )
    world.say(
        f"Inside the cart sat {obj.phrase}, shiny as a tiny comet."
    )


def promise(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["responsible"] += 1
    world.say(
        f"\"I owe you for lending it,\" {hero.id} said. \"I won't waste the fuel.\""
    )
    world.say(
        f"\"Good,\" {helper.id} said. \"Space trips are fun when we keep them careful.\""
    )


def tempt(world: World, hero: Entity, action: ActionCfg) -> None:
    hero.memes["curious"] += 1
    world.say(
        f"Then {hero.id} reached for the bright lever. {action.sound} "
        f"{hero.id} whispered, \"Let's go faster!\""
    )


def warn(world: World, helper: Entity, hero: Entity, obj: ObjectCfg) -> None:
    world.say(
        f"\"Wait,\" {helper.id} said. \"If you pull that too hard, you'll make {obj.label} splash everywhere.\""
    )


def misstep(world: World, action: ActionCfg, obj: ObjectCfg) -> None:
    cart = world.get("pram")
    cart.meters["wobble"] += 1
    world.say(
        f"{action.sound} The pram gave a little wobble, and {obj.label} tipped with a glug-glug sound."
    )
    _do_action(world, action, obj, narrate=False)


def call_fix(world: World, helper: Entity, fix: FixCfg, obj: ObjectCfg) -> None:
    world.say(
        f"\"I'll help,\" {helper.id} said. {fix.sound} {helper.id} used {fix.method} to steady the cart."
    )
    world.get("pram").meters["wobble"] = 0.0
    world.get("fuel").meters["spill"] = 0.0
    world.get("ship").meters["waste"] = 0.0
    helper.memes["calm"] += 1
    world.say(
        f"The little ship stopped shaking, and {obj.label} rested still again."
    )


def lesson(world: World, hero: Entity, helper: Entity, fix: FixCfg) -> None:
    hero.memes["relief"] += 1
    hero.memes["lesson"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"\"I get it,\" {hero.id} said. \"I should not waste a helper's fuel.\""
    )
    world.say(
        f"\"That's right,\" {helper.id} said. \"Use small, careful moves, and the trip stays safe.\""
    )
    world.say(
        f"So {hero.id} held the wheel with both hands, and the pram hummed on quietly instead of splashing."
    )


def drift_end(world: World, hero: Entity, helper: Entity, obj: ObjectCfg) -> None:
    hero.memes["worry"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"The helper caught {hero.id} before anything worse happened, but the cart had already drifted away from the dock."
    )
    world.say(
        f"\"We can fix it,\" {helper.id} said. \"But next time, we take care before the fuel gets wasted.\""
    )
    world.say(
        f"By the end, the pram was parked beside the lantern, and {obj.label} was tied down tight."
    )


def tell(setting: Setting, action: ActionCfg, obj: ObjectCfg, fix: FixCfg,
         hero_name: str = "Mila", hero_gender: str = "girl",
         helper_name: str = "Captain Sol", helper_gender: str = "boy") -> World:
    world = World()
    hero = world.add(Entity(hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(helper_name, kind="character", type=helper_gender, role="helper"))
    world.add(Entity("pram", type="vehicle", label="space pram"))
    world.add(Entity("fuel", type="thing", label="moon fuel"))
    world.add(Entity("ship", type="ship", label="ship"))
    world.add(Entity("crew", type="crew", label="crew"))

    set_up(world, hero, helper, setting, action, obj)
    world.para()
    promise(world, hero, helper)
    warn(world, helper, hero, obj)
    tempt(world, hero, action)
    misstep(world, action, obj)

    world.para()
    if outcome_of(StoryParams(setting.id, action.id, obj.id, fix.id, hero_name, hero_gender, helper_name, helper_gender, 0)) == "saved":
        call_fix(world, helper, fix, obj)
        lesson(world, hero, helper, fix)
    else:
        drift_end(world, hero, helper, obj)

    world.facts.update(setting=setting, action=action, obj=obj, fix=fix, hero=hero, helper=helper)
    world.facts["outcome"] = "saved" if fix.power >= 2 and fix.sense >= SENSE_MIN else "drift"
    return world


SETTINGS = {
    "moon_dock": Setting("moon_dock", "a tiny moon pram", "The stars winked over the bay like silver beads.", {"roll"}),
    "starship_hall": Setting("starship_hall", "a little star pram", "A glowing map blinked on the wall of the ship.", {"roll"}),
    "orbital_garden": Setting("orbital_garden", "a nursery rover", "The station garden hummed softly under glass.", {"roll"}),
}

OBJECTS = {
    "juice": ObjectCfg("juice", "juice pouch", "a juice pouch", "liquid", True, {"spill"}),
    "paint": ObjectCfg("paint", "paint tub", "a paint tub", "liquid", True, {"spill"}),
    "confetti": ObjectCfg("confetti", "confetti bag", "a confetti bag", "light", False, {"scatter"}),
}

ACTIONS = {
    "wobble": ActionCfg("wobble", "rock the pram", "wobble", "WHIRR", "liquid", "spill"),
    "tilt": ActionCfg("tilt", "tilt the pram", "tilt", "SKRRT", "liquid", "spill"),
}

FIXES = {
    "strap": FixCfg("strap", "a safety strap", "strapping the cargo down", "CLIP-CLIP", 3, 3, {"strap"}),
    "patch": FixCfg("patch", "a patch kit", "patching the leak", "TAP-TAP", 2, 2, {"patch"}),
    "towel": FixCfg("towel", "a towel", "blotting the spill", "PLAP", 1, 1, {"towel"}),
}

NAMES = ["Mila", "Rae", "Juno", "Pip", "Nia", "Toby", "Nova", "Kai"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    action: str
    obj: str
    fix: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
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
    "pram": [("What is a pram?", "A pram is a small wheeled cart for carrying a baby or things gently. In space stories, it can be a tiny rolling ship or rover.")],
    "owe": [("What does owe mean?", "If you owe someone, you need to give them something back later, like help, a thank-you, or a favor.")],
    "waste": [("What does waste mean?", "To waste something means to use too much of it or use it carelessly so some is lost.")],
    "sound": [("What is a sound effect in a story?", "A sound effect is a word like WHIRR or CLIP-CLIP that helps you imagine the noise.")],
    "dialogue": [("What is dialogue?", "Dialogue is when characters speak with each other using quotation marks.")],
    "space": [("Why do people like space adventures?", "Space adventures feel exciting because there are stars, ships, and big places to explore.")],
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for aid, action in ACTIONS.items():
            for oid, obj in OBJECTS.items():
                for fid, fix in FIXES.items():
                    if reasonableness_gate(action, obj, fix):
                        combos.append((sid, aid, oid, fid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space adventure story for a 3-to-5-year-old that includes the words "pram", "owe", and "waste", plus sound effects and dialogue.',
        f"Tell a gentle moon-dock story where {f['hero'].id} borrows a pram, says {f['hero'].id} owes {f['helper'].id} a favor, and learns not to waste the fuel.",
        f'Write a child-facing story with a rolling space pram, a small mistake, and a calm fix. Use on-page dialogue and a few sound effects.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    obj: ObjectCfg = f["obj"]
    fix: FixCfg = f["fix"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id} and {helper.id} in a little space adventure with a pram. The pram makes the whole scene feel like a tiny ship instead of an ordinary cart."
        ),
        QAItem(
            question=f"What did {hero.id} say about owing {helper.id}?",
            answer=f"{hero.id} said that {hero.id} owed {helper.id} for lending the pram. That promise matters because it makes the child want to be careful and not waste the fuel."
        ),
        QAItem(
            question=f"What went wrong with the pram?",
            answer=f"The pram wobbled, and {obj.label} spilled or shifted too much. That made the ride messy and showed why the child had to slow down."
        ),
        QAItem(
            question=f"How did {helper.id} fix the problem?",
            answer=f"{helper.id} used {fix.label} and stayed calm. The fix stopped the spill and brought the pram back to a safe, steady roll."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the pram moving safely again and {hero.id} using careful hands. The child learned that a good space trip should not waste fuel."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"pram", "owe", "waste", "sound", "dialogue", "space"}
    out: list[QAItem] = []
    for key in ["pram", "owe", "waste", "sound", "dialogue", "space"]:
        if key in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[key])
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("moon_dock", "wobble", "juice", "strap", "Mila", "girl", "Captain Sol", "boy", 0),
    StoryParams("starship_hall", "tilt", "paint", "patch", "Juno", "girl", "Aunt Ray", "girl", 0),
    StoryParams("orbital_garden", "wobble", "juice", "strap", "Toby", "boy", "Mara", "girl", 0),
]


def explain_rejection(action: ActionCfg, obj: ObjectCfg) -> str:
    return f"(No story: the action {action.verb} does not fit a safe mismatch with {obj.label} in this tiny space world.)"


def explain_response(rid: str) -> str:
    fix = FIXES[rid]
    better = " / ".join(sorted(f.id for f in sensible_fixes()))
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={fix.sense} < {SENSE_MIN}). Try: {better}.)"


ASP_RULES = r"""
valid(S,A,O,F) :- setting(S), action(A), object(O), fix(F),
                  risky(O), meter_of(A,M), kind_of(O,M), power(F,P), P >= 2.
outcome(saved) :- chosen_fix(F), power(F,P), P >= 2.
outcome(drift) :- chosen_fix(F), power(F,P), P < 2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("meter_of", aid, a.risky_meter))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.risky:
            lines.append(asp.fact("risky", oid))
        lines.append(asp.fact("kind_of", oid, o.kind))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("power", fid, f.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    # smoke test
    try:
        generate(CURATED[0])
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-pram storyworld with sound effects and dialogue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--obj", choices=OBJECTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_response(args.fix))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.action is None or c[1] == args.action)
              and (args.obj is None or c[2] == args.obj)
              and (args.fix is None or c[3] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, aid, oid, fid = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(NAMES)
    helper_name = args.helper_name or rng.choice([n for n in NAMES if n != hero_name])
    delay = rng.randint(0, 2)
    return StoryParams(sid, aid, oid, fid, hero_name, hero_gender, helper_name, helper_gender, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIONS[params.action], OBJECTS[params.obj], FIXES[params.fix],
                 params.hero_name, params.hero_gender, params.helper_name, params.helper_gender)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
