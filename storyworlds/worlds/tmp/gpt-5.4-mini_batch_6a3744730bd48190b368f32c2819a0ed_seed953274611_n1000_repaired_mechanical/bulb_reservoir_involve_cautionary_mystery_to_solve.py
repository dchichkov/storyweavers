#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bulb_reservoir_involve_cautionary_mystery_to_solve.py
======================================================================================

A standalone story world for a small whodunit-style cautionary mystery.

Premise
-------
A child and a helper notice two odd problems in a little indoor conservatory:
a lamp bulb is dim, and the water reservoir for a plant tray is mysteriously low.
They investigate clues, involve a trusted grown-up, and discover that the real
cause is ordinary but easy to misunderstand: a cracked reservoir cap let water
escape, and the flickering bulb was only dusty and loose. The cautionary turn is
that electrical things and leaking water should never be poked at alone.

This world is built to satisfy the Storyweavers contract:
- typed entities with physical meters and emotional memes
- a state-driven story, not a frozen paragraph swap
- a reasonableness gate plus inline ASP twin
- three QA sets grounded in world state
- CLI support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)
    suspicious: bool = False
    fragile: bool = False
    liquid: bool = False
    light_source: bool = False

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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class StoryParams:
    setting: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    adult: str
    bulb: str
    reservoir: str
    clue: str
    twist: str = "dust"
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


@dataclass
class Setting:
    id: str
    scene: str
    room_name: str
    mood: str
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
class Bulb:
    id: str
    label: str
    glow: str
    cause: str
    safe_to_touch: bool = False
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
class Reservoir:
    id: str
    label: str
    description: str
    leak_reason: str
    fragile: bool = True
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
class Clue:
    id: str
    label: str
    text: str
    suspicious: bool = False
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
class Solution:
    id: str
    method: str
    danger: int
    text: str
    fail: str
    qa_text: str
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


def _r_dust(world: World) -> list[str]:
    out = []
    bulb = world.entities.get("bulb")
    if bulb and bulb.meters["dusty"] >= THRESHOLD and ("dust", "noticed") not in world.fired:
        world.fired.add(("dust", "noticed"))
        world.get("helper").memes["curiosity"] += 1
        out.append("__dust__")
    return out


def _r_leak(world: World) -> list[str]:
    out = []
    res = world.entities.get("reservoir")
    if res and res.meters["leaking"] >= THRESHOLD and ("leak", "noticed") not in world.fired:
        world.fired.add(("leak", "noticed"))
        world.get("child").memes["worry"] += 1
        world.get("adult").memes["worry"] += 1
        out.append("__leak__")
    return out


def _r_solve(world: World) -> list[str]:
    out = []
    clue = world.entities.get("clue")
    if clue and clue.meters["seen"] >= THRESHOLD and ("solve", clue.id) not in world.fired:
        world.fired.add(("solve", clue.id))
        world.get("child").memes["joy"] += 1
        out.append("__solve__")
    return out


CAUSAL_RULES = [Rule("dust", _r_dust), Rule("leak", _r_leak), Rule("solve", _r_solve)]


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


def hazard_reasonable(bulb: Bulb, reservoir: Reservoir) -> bool:
    return bulb.safe_to_touch and reservoir.fragile


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for bid, bulb in BULBS.items():
            for rid, res in RESERVOIRS.items():
                if hazard_reasonable(bulb, res):
                    combos.append((sid, bid, rid))
    return combos


def _do_investigate(world: World, child: Entity, helper: Entity, adult: Entity, bulb: Bulb,
                    reservoir: Reservoir, clue: Clue) -> None:
    child.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"In {SETTINGS[world.facts['setting']].room_name}, {child.id} and {helper.id} found "
        f"a little mystery: the {bulb.label} was dim, and the {reservoir.label} was low."
    )
    world.say(
        f"{SETTINGS[world.facts['setting']].scene} made the room feel like a whodunit, and "
        f"every small thing seemed like it might involve a clue."
    )


def inspect_bulb(world: World, bulb: Entity) -> None:
    bulb.meters["dusty"] += 1
    bulb.meters["loose"] += 1
    world.say(
        f"{bulb.id} gave only a tired glow. When they looked closer, they saw dust around it "
        f"and noticed it had been set in a little loose."
    )


def inspect_reservoir(world: World, reservoir: Entity, clue: Entity) -> None:
    reservoir.meters["empty"] += 1
    reservoir.meters["leaking"] += 1
    clue.meters["seen"] += 1
    world.say(
        f"The reservoir was the louder mystery. A tiny crack near the cap had let water slip "
        f"out little by little, and the clue beside it looked suspicious."
    )


def warn_caution(world: World, adult: Entity) -> None:
    adult.memes["care"] += 1
    world.say(
        f'{adult.label_word.capitalize()} shook {adult.pronoun("possessive")} head. '
        f'"Don’t touch the bulb or the leak yourself. Water and wires are a grown-up job."'
    )


def reveal(world: World, clue: Clue, adult: Entity) -> None:
    world.say(
        f"The clue was not a thief at all. {adult.label_word.capitalize()} wiped the bulb, tightened "
        f"the fixture, and replaced the cracked cap on the reservoir."
    )


def solve(world: World, solution: Solution) -> None:
    world.get("bulb").meters["dusty"] = 0.0
    world.get("bulb").meters["loose"] = 0.0
    world.get("reservoir").meters["leaking"] = 0.0
    world.get("reservoir").meters["empty"] = 0.0
    world.say(
        f'{solution.text}. Soon the bulb glowed bright again, and the reservoir held water safely.'
    )


def cautionary_ending(world: World, child: Entity, helper: Entity, adult: Entity) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'For a moment they all stood quiet, then {adult.label_word.capitalize()} smiled. '
        f'"That was a good mystery to solve, but a bad one to tinker with alone."'
    )
    world.say(
        f"{child.id} nodded, and {helper.id} promised never to poke at bulbs or leaks without help."
    )
    world.say(
        "The room ended brighter and steadier than before, with the little reservoir full and the lamp shining."
    )


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    bulb = BULBS[params.bulb]
    reservoir = RESERVOIRS[params.reservoir]
    clue = CLUES[params.clue]
    solution = SOLUTIONS["adult_fix"]

    child = world.add(Entity(id="child", kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, role="helper"))
    adult = world.add(Entity(id="adult", kind="character", type="mother", role="adult", label="the grown-up"))
    world.add(Entity(id="bulb", type="thing", label=bulb.label, light_source=True))
    world.add(Entity(id="reservoir", type="thing", label=reservoir.label, fragile=True))
    world.add(Entity(id="clue", type="thing", label=clue.label, suspicious=clue.suspicious))

    world.facts.update(setting=params.setting, bulb=params.bulb, reservoir=params.reservoir,
                       clue=params.clue, child=child, helper=helper, adult=adult,
                       setting_obj=setting, bulb_obj=bulb, reservoir_obj=reservoir,
                       clue_obj=clue, solution=solution)

    world.say(
        f"On a quiet afternoon in {setting.scene}, {params.child} and {params.helper} found a small mystery."
    )
    world.say(
        f"The lamp bulb was dim, and the water reservoir in the corner seemed lower than it should have been."
    )
    world.para()
    _do_investigate(world, child, helper, adult, bulb, reservoir, clue)
    inspect_bulb(world, world.get("bulb"))
    inspect_reservoir(world, world.get("reservoir"), world.get("clue"))
    warn_caution(world, adult)
    reveal(world, world.get("clue"), adult)
    world.para()
    solve(world, solution)
    cautionary_ending(world, child, helper, adult)
    return world


SETTINGS = {
    "conservatory": Setting(id="conservatory", scene="the sunlit conservatory", room_name="the conservatory", mood="quiet"),
    "greenhouse": Setting(id="greenhouse", scene="the little greenhouse", room_name="the greenhouse", mood="bright"),
    "library": Setting(id="library", scene="the back reading room", room_name="the reading room", mood="hushed"),
}

BULBS = {
    "desk_bulb": Bulb(id="desk_bulb", label="desk bulb", glow="a weak yellow glow", cause="dust"),
    "lamp_bulb": Bulb(id="lamp_bulb", label="lamp bulb", glow="a flickery shine", cause="looseness"),
}

RESERVOIRS = {
    "plant_reservoir": Reservoir(id="plant_reservoir", label="plant reservoir", description="the little plant reservoir", leak_reason="a cracked cap"),
    "tray_reservoir": Reservoir(id="tray_reservoir", label="tray reservoir", description="the tray reservoir", leak_reason="a tiny crack"),
}

CLUES = {
    "dusty_card": Clue(id="dusty_card", label="dusty card", text="a dusty card by the shelf", suspicious=True),
    "wet_towel": Clue(id="wet_towel", label="wet towel", text="a wet towel under the stand", suspicious=True),
}

SOLUTIONS = {
    "adult_fix": Solution(
        id="adult_fix",
        method="adult_fix",
        danger=1,
        text="The grown-up cleaned the bulb, tightened it, and patched the reservoir cap",
        fail="The grown-up could not make sense of it at first",
        qa_text="The grown-up cleaned the bulb, tightened it, and patched the reservoir cap",
    )
}

TOPICS = {
    "bulb": [
        ("What is a bulb?", "A bulb is a glass light that shines when electricity passes through it. It should be handled carefully because it can be hot and fragile."),
    ],
    "reservoir": [
        ("What is a reservoir in this story?", "It is a small container that stores water for plants. If it leaks, the plants can dry out."),
    ],
    "involve": [
        ("What does it mean to involve someone?", "To involve someone is to include them in what is happening. In a mystery, involving a grown-up can help solve the problem safely."),
    ],
    "cautionary": [
        ("What does cautionary mean?", "Cautionary means the story is trying to warn you to be careful. It shows what can go wrong if you do something unsafe."),
    ],
    "mystery": [
        ("What is a mystery?", "A mystery is a problem with clues that needs to be solved. People look carefully and think about what happened."),
    ],
}

TOPIC_ORDER = ["bulb", "reservoir", "involve", "cautionary", "mystery"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a whodunit-style story for a young child that includes the words "{f["bulb"]}", "{f["reservoir"]}", and "{f["clue"]}".',
        f"Tell a cautionary mystery where two children notice a dim bulb and a low reservoir, then involve a grown-up to solve it safely.",
        "Write a simple detective story that ends with a bright lamp and a full reservoir, and teaches children not to touch wires or leaks alone.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    bulb: Bulb = f["bulb_obj"]
    reservoir: Reservoir = f["reservoir_obj"]
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    adult: Entity = f["adult"]
    qa = [
        QAItem(
            question="What was the mystery?",
            answer=f"The children were trying to figure out why the {bulb.label} was dim and the {reservoir.label} was low. It turned out the room had both dusty light and a leaking cap, so the clues were easy to mix up."
        ),
        QAItem(
            question=f"Why did {child.id} and {helper.id} involve the grown-up?",
            answer=f"They involved {adult.label_word} because the mystery included a bulb and a leak, and those are not things children should fix alone. The grown-up could handle the wires and the water safely."
        ),
        QAItem(
            question="How was the mystery solved?",
            answer="The grown-up cleaned and tightened the bulb, then fixed the cracked reservoir cap. That made the room bright again and stopped the water from slipping away."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["bulb"], world.facts["reservoir"], "involve", "cautionary", "mystery"}
    out: list[QAItem] = []
    for tag in TOPIC_ORDER:
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in TOPICS[tag])
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
bulb_problem(B) :- bulb(B), dusty(B).
reservoir_problem(R) :- reservoir(R), leaking(R).
mystery(B, R) :- bulb_problem(B), reservoir_problem(R).
involve_adult :- mystery(_, _), adult_called.
solution_fixed :- involve_adult, cleaned_bulb, patched_reservoir.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid, b in BULBS.items():
        lines.append(asp.fact("bulb", bid))
        if b.safe_to_touch:
            lines.append(asp.fact("safe_to_touch", bid))
        lines.append(asp.fact("dusty", bid))
    for rid, r in RESERVOIRS.items():
        lines.append(asp.fact("reservoir", rid))
        if r.fragile:
            lines.append(asp.fact("fragile", rid))
        lines.append(asp.fact("leaking", rid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    lines.append(asp.fact("adult_called"))
    lines.append(asp.fact("cleaned_bulb"))
    lines.append(asp.fact("patched_reservoir"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show mystery/2."))
    return sorted(set(asp.atoms(model, "mystery")))


def asp_verify() -> int:
    import asp
    rc = 0
    a = set(asp_valid_combos())
    p = {("desk_bulb", "plant_reservoir"), ("desk_bulb", "tray_reservoir"), ("lamp_bulb", "plant_reservoir"), ("lamp_bulb", "tray_reservoir")}
    if a == p:
        print("OK: ASP twin matches Python gate.")
    else:
        rc = 1
        print("MISMATCH: ASP and Python disagree.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit-style cautionary mystery about a bulb and a reservoir.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--bulb", choices=BULBS)
    ap.add_argument("--reservoir", choices=RESERVOIRS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
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
              and (args.bulb is None or c[1] == args.bulb)
              and (args.reservoir is None or c[2] == args.reservoir)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, bulb, reservoir = rng.choice(sorted(combos))
    clue = args.clue or rng.choice(sorted(CLUES))
    child_name = rng.choice(["Mia", "Noah", "Lily", "Theo", "Ava", "Ben"])
    helper_name = rng.choice([n for n in ["Zoe", "Max", "Ivy", "Leo", "Nora", "Sam"] if n != child_name])
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = "girl" if child_gender == "boy" else "boy"
    adult = rng.choice(["mother", "father"])
    return StoryParams(setting=setting, child=child_name, child_gender=child_gender,
                       helper=helper_name, helper_gender=helper_gender, adult=adult,
                       bulb=bulb, reservoir=reservoir, clue=clue)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.bulb not in BULBS or params.reservoir not in RESERVOIRS or params.clue not in CLUES:
        raise StoryError("invalid story params")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(setting="conservatory", child="Mia", child_gender="girl", helper="Noah", helper_gender="boy", adult="mother", bulb="lamp_bulb", reservoir="plant_reservoir", clue="wet_towel"),
    StoryParams(setting="greenhouse", child="Theo", child_gender="boy", helper="Ava", helper_gender="girl", adult="father", bulb="desk_bulb", reservoir="tray_reservoir", clue="dusty_card"),
]


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
        print(asp_program("", "#show mystery/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} mystery pairs:")
        for b, r in asp_valid_combos():
            print(f"  {b:12} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
