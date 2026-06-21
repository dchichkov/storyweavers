#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bridle_kindness_bad_ending_suspense_fable.py
=============================================================================

A small fable-style storyworld built from the seed word "bridle" with kindness,
suspense, and a bad ending branch.

Premise:
- A child or stable helper notices a horse in trouble.
- A bridle is the important object.
- Kindness may help, but if the wrong choice is made, the ending can turn bad.

The world is intentionally tiny and classical: one domain, a handful of entities,
stateful meters/memes, a reasonableness gate, and a declarative ASP twin.
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
MORAL_MIN = 1.0


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
    stubborn: bool = False
    gentle: bool = False
    breakable: bool = False
    slippery: bool = False
    wearable: bool = False
    usable: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "mare"}
        male = {"boy", "father", "man", "stallion"}
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    danger_word: str
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
class Horse:
    id: str
    label: str
    kind: str
    mood: str
    speed: int
    trust_need: int
    tags: set[str] = field(default_factory=set)
    breakable: bool = False
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
class Bridle:
    id: str
    label: str
    phrase: str
    where: str
    usable: bool = True
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
class HelpChoice:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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
class StoryParams:
    setting: str
    horse: str
    bridle: str
    helper_name: str
    helper_type: str
    helper_trait: str
    help_choice: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    horse = world.get("horse")
    helper = world.get("helper")
    if horse.meters["restless"] >= THRESHOLD and helper.memes["worry"] < THRESHOLD:
        helper.memes["worry"] += 1
        out.append("__suspense__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    horse = world.get("horse")
    if helper.memes["kindness"] >= THRESHOLD and horse.memes["trust"] < THRESHOLD:
        horse.memes["trust"] += 1
        out.append("__trust__")
    return out


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    horse = world.get("horse")
    if horse.meters["caught"] >= THRESHOLD and horse.meters["hurt"] < THRESHOLD:
        horse.meters["hurt"] += 1
        out.append("__hurt__")
    return out


CAUSAL_RULES = [
    Rule("suspense", "social", _r_suspense),
    Rule("kindness", "social", _r_kindness),
    Rule("spook", "physical", _r_spook),
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
        for s in produced:
            world.say(s)
    return produced


def safe_help(choice: HelpChoice) -> bool:
    return choice.sense >= SENSE_MIN


def horse_in_risk(horse: Horse, bridle: Bridle) -> bool:
    return horse.breakable and bridle.usable


def outcome_of(params: StoryParams) -> str:
    if params.help_choice == "call_farmer":
        return "bad"
    if params.help_choice == "steady_hand":
        return "saved"
    return "bad"


SETTINGS = {
    "stable": Setting(id="stable", place="the old stable", mood="warm hay and dim dust", danger_word="storm"),
    "lane": Setting(id="lane", place="the village lane", mood="wet stones and thin fog", danger_word="mist"),
    "field": Setting(id="field", place="the back field", mood="long grass and a gray sky", danger_word="wind"),
}

HORSES = {
    "brown_mare": Horse(id="horse", label="brown mare", kind="mare", mood="nervous", speed=3, trust_need=1, tags={"horse"}, breakable=True),
    "old_pony": Horse(id="horse", label="old pony", kind="pony", mood="tired", speed=2, trust_need=1, tags={"horse"}, breakable=True),
}

BRIDLES = {
    "red_bridle": Bridle(id="bridle", label="bridle", phrase="a worn bridle with a red strap", where="hanging on the peg", tags={"bridle"}),
}

HELP_CHOICES = {
    "steady_hand": HelpChoice(id="steady_hand", sense=3, power=3,
                              text="untied the bridle, spoke softly, and held the horse steady until it calmed",
                              fail="tried to help, but the horse pulled free and the moment grew worse",
                              tags={"kindness", "help"}),
    "call_farmer": HelpChoice(id="call_farmer", sense=2, power=2,
                              text="ran to call the farmer and came back with a lantern and a calm voice",
                              fail="called too late, and the horse had already slipped into the ditch",
                              tags={"kindness", "help"}),
    "rush": HelpChoice(id="rush", sense=1, power=1,
                       text="grabbed at the bridle in a hurry",
                       fail="grabbed at the bridle in a hurry and made the horse bolt",
                       tags={"rush"}),
}

NAMES = ["Mina", "Rory", "Tess", "Hugo", "Nell", "Pip", "June", "Owen"]
TRAITS = ["kind", "gentle", "careful", "brave"]


def tell(setting: Setting, horse: Horse, bridle: Bridle, helper_name: str, helper_type: str,
         helper_trait: str, help_choice: HelpChoice) -> World:
    world = World(setting)
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name,
                              role="helper", traits=[helper_trait], gentle=(helper_trait == "gentle")))
    horse_ent = world.add(Entity(id="horse", kind="character", type=horse.kind, label=horse.label,
                                 role="horse", traits=["restless"], breakable=True))
    bridle_ent = world.add(Entity(id="bridle", kind="thing", type="tool", label=bridle.label,
                                  usable=True))
    helper.memes["kindness"] = 1.0
    helper.memes["worry"] = 0.0
    horse_ent.memes["trust"] = 0.0
    horse_ent.meters["restless"] = 1.0
    world.say(
        f"In {setting.place}, where the air felt like {setting.mood}, {helper_name} found a horse "
        f"and saw {bridle.phrase} {bridle.where}."
    )
    world.say(
        f'The horse stamped once and looked toward the gate, as if some {setting.danger_word} had made '
        f"the yard feel too small."
    )
    world.para()
    helper.memes["kindness"] += 1
    world.say(
        f"{helper_name} wanted to help, because {helper_name.lower()} had a kind heart and did not like "
        f"to see a scared horse left alone."
    )
    world.say(
        f'But the {bridle.label} mattered: if the wrong hands grabbed it the horse could spook and run.'
    )
    propagate(world, narrate=False)
    world.para()
    if not safe_help(help_choice):
        horse_ent.meters["caught"] += 1
        horse_ent.meters["restless"] += 1
        propagate(world, narrate=False)
        world.say(
            f'{helper_name} {help_choice.fail}. The horse threw up its head, the bridle snapped against the rail, '
            f'and the yard filled with loud hoofbeats.'
        )
        world.say(
            f"By the time the sound stopped, the horse had dashed into the lane and the day had turned sad."
        )
        world.say(
            f"{helper_name} stood still, wishing kindness had been mixed with patience."
        )
        outcome = "bad"
    else:
        if help_choice.id == "steady_hand":
            horse_ent.memes["trust"] += 1.0
            world.say(
                f'{helper_name} {help_choice.text}. The horse blinked, breathed, and let the bridle be unfastened.'
            )
        else:
            helper.memes["worry"] += 1.0
            world.say(
                f'{helper_name} {help_choice.text}. The farmer came, took the bridle, and spoke low until the horse stood still.'
            )
        world.say(
            f"The horse did not race away, and the stable grew quiet again."
        )
        world.say(
            f"Kindness, when it moved with care, saved the day."
        )
        outcome = "saved"
    world.facts.update(setting=setting, horse=horse_ent, bridle=bridle_ent, helper=helper,
                       help_choice=help_choice, outcome=outcome)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable for a young child that includes the word "bridle" and shows kindness with a suspenseful moment.',
        f"Tell a short fable about {f['helper'].label_word if isinstance(f['helper'], Entity) else 'a helper'} who sees a horse and a {f['bridle'].label}, then makes a choice that leads to a bad ending.",
        f"Write a fable-style story about helping a restless horse, where the quiet moment turns tense and the ending goes wrong.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    helper = f["helper"]
    horse = f["horse"]
    choice = f["help_choice"]
    qa = [
        ("Who is the story about?",
         f"It is about {helper.label_word} and the horse in the old stable. The bridle is the important object that makes the choice feel serious."),
        ("Why was the moment suspenseful?",
         f"The horse was restless and the bridle was right there, so nobody could tell at first whether the scene would stay calm. That made the helper need to choose carefully."),
    ]
    if f["outcome"] == "bad":
        qa.append((
            "What went wrong at the end?",
            f"{helper.label_word.capitalize()} chose the wrong kind of help, so the horse spooked and ran off into the lane. The kindness was real, but it came without enough patience, and that made the ending sad."
        ))
    else:
        qa.append((
            "How did it end?",
            f"{helper.label_word.capitalize()} helped with care, and the horse settled down instead of bolting. The bridle stayed safe, and the stable became quiet again."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a bridle?",
         "A bridle is a set of straps that helps guide a horse. People use it with care so the horse stays safe and calm."),
        ("Why should people be gentle with a horse?",
         "Horses can get scared if hands move too fast. Gentle movements help the horse trust people and stay steady."),
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for hid in HORSES:
            for bid in BRIDLES:
                for cid in HELP_CHOICES:
                    if horse_in_risk(HORSES[hid], BRIDLES[bid]) and safe_help(HELP_CHOICES[cid]):
                        combos.append((sid, hid, bid))
    return combos


def explain_rejection(choice: HelpChoice) -> str:
    return f"(No story: help choice '{choice.id}' is too rushed for a fable-like kindness story.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable storyworld: bridle, kindness, suspense, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--horse", choices=HORSES)
    ap.add_argument("--bridle", choices=BRIDLES)
    ap.add_argument("--help-choice", choices=HELP_CHOICES, dest="help_choice")
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("--helper-trait", choices=TRAITS)
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
    if args.help_choice and not safe_help(HELP_CHOICES[args.help_choice]):
        raise StoryError(explain_rejection(HELP_CHOICES[args.help_choice]))
    settings = [k for k in SETTINGS if args.setting in (None, k)]
    horses = [k for k in HORSES if args.horse in (None, k)]
    bridles = [k for k in BRIDLES if args.bridle in (None, k)]
    help_choices = [k for k in HELP_CHOICES if args.help_choice in (None, k) and safe_help(HELP_CHOICES[k])]
    combos = [(s, h, b, c) for s in settings for h in horses for b in bridles for c in help_choices
              if horse_in_risk(HORSES[h], BRIDLES[b])]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, horse, bridle, help_choice = rng.choice(sorted(combos))
    helper_type = args.helper_type or rng.choice(["girl", "boy"])
    helper_name = args.helper_name or rng.choice(NAMES)
    helper_trait = args.helper_trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, horse=horse, bridle=bridle, helper_name=helper_name,
                       helper_type=helper_type, helper_trait=helper_trait, help_choice=help_choice)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.horse not in HORSES or params.bridle not in BRIDLES or params.help_choice not in HELP_CHOICES:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], HORSES[params.horse], BRIDLES[params.bridle],
                 params.helper_name, params.helper_type, params.helper_trait, HELP_CHOICES[params.help_choice])
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


ASP_RULES = r"""
help_kind(H) :- choice(H), sense(H,S), sense_min(M), S >= M.
risk(S, H, B) :- setting(S), horse(H), bridle(B), horse_breakable(H), bridle_usable(B).
bad_end(H) :- choice(H), rush(H).
saved(H) :- choice(H), help_kind(H), not rush(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, h in HORSES.items():
        lines.append(asp.fact("horse", hid))
        if h.breakable:
            lines.append(asp.fact("horse_breakable", hid))
    for bid, b in BRIDLES.items():
        lines.append(asp.fact("bridle", bid))
        if b.usable:
            lines.append(asp.fact("bridle_usable", bid))
    for cid, c in HELP_CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("sense", cid, c.sense))
        if cid == "rush":
            lines.append(asp.fact("rush", cid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show risk/3."))
    return sorted(set(asp.atoms(model, "risk")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, horse=None, bridle=None, help_choice=None, helper_name=None, helper_type=None, helper_trait=None), random.Random(777)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams(setting="stable", horse="brown_mare", bridle="red_bridle", helper_name="Mina", helper_type="girl", helper_trait="gentle", help_choice="steady_hand"),
    StoryParams(setting="lane", horse="old_pony", bridle="red_bridle", helper_name="Rory", helper_type="boy", helper_trait="kind", help_choice="call_farmer"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show risk/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return
    rng_base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            i += 1
            params = resolve_params(args, random.Random(rng_base + i))
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
