#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/veil_zoo_flashback_teamwork_animal_story.py
============================================================================

A standalone storyworld about a zoo day, a lost veil, a flashback to a past
problem, and animal teamwork that solves it.

The premise is simple: a child or zookeeper visits a zoo wearing a thin veil for
shade or play. The veil slips away into an animal area. The story flashes back
to an earlier moment that explains why the veil matters, then shows animals and
people working together to recover it safely. The ending proves what changed by
showing the veil back in place or safely folded away, with trust and teamwork
restored.

This script follows the Storyweavers contract:
- stdlib-only prose engine
- typed entities with meters and memes
- reasonableness gate plus inline ASP twin
- three Q&A sets grounded in world state
- StoryParams + parser + resolve_params + generate + emit + main
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
ANIMAL_KINDS = {"monkey", "giraffe", "penguin", "elephant", "parrot", "otter"}


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
        female = {"girl", "mother", "mom", "woman", "keeper"}
        male = {"boy", "father", "dad", "man", "keeper"}
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
    detail: str
    flashback_seed: str
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
class Veil:
    id: str
    label: str
    phrase: str
    use: str
    snag_risk: int
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
class Animal:
    id: str
    species: str
    label: str
    path: str
    help: str
    teamwork_score: int
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
class Fix:
    id: str
    sense: int
    effort: int
    text: str
    fail: str
    qa_text: str
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
    veil: str
    animal1: str
    animal2: str
    fixer: str
    keeper_name: str
    keeper_type: str
    child_name: str
    child_type: str
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


def _r_fear(world: World) -> list[str]:
    out = []
    veil = world.get("veil")
    if veil.meters["lost"] >= THRESHOLD and ("fear", "raise") not in world.fired:
        world.fired.add(("fear", "raise"))
        for eid in ("child", "keeper"):
            world.get(eid).memes["worry"] += 1
        out.append("__fear__")
    return out


CAUSAL_RULES = [Rule("fear", _r_fear)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def valid_animal_pair(a: Animal, b: Animal) -> bool:
    return a.id != b.id and a.teamwork_score + b.teamwork_score >= 5


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    if not sensible_fixes():
        return combos
    for sid in SETTINGS:
        for vid, v in VEILS.items():
            for a1 in ANIMALS.values():
                for a2 in ANIMALS.values():
                    if valid_animal_pair(a1, a2):
                        combos.append((sid, vid, a1.id, a2.id))
    return combos


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def predict_loss(world: World, veil_id: str) -> dict:
    sim = world.copy()
    sim.get(veil_id).meters["lost"] += 1
    propagate(sim, narrate=False)
    return {"worry": sim.get("child").memes["worry"], "lost": sim.get(veil_id).meters["lost"] >= THRESHOLD}


def tell_flashback(world: World, setting: Setting, child: Entity, keeper: Entity, veil: Veil) -> None:
    world.say(f"At the zoo, {child.id} and {keeper.id} walked under {setting.detail}.")
    world.say(f"{child.id} wore {veil.phrase} because {veil.use}.")
    world.say(f'Then {child.id} pointed at the animals and smiled. "I want to see them all!"')


def trigger_loss(world: World, veil: Veil, animal1: Animal) -> None:
    veil_ent = world.get("veil")
    veil_ent.meters["lost"] += 1
    world.say(
        f"A gust of wind lifted the veil away and sent it drifting toward the "
        f"{animal1.path}."
    )
    propagate(world, narrate=False)


def flashback(world: World, child: Entity, keeper: Entity, veil: Veil) -> None:
    child.memes["remember"] += 1
    world.say(
        f'For a moment, {child.id} remembered the last time a breeze had tugged at '
        f'{child.pronoun("possessive")} veil. {keeper.id} had said, "Hold it close, '
        f"and we can still have fun.""
    )


def teamwork_search(world: World, animal1: Animal, animal2: Animal) -> None:
    a1 = world.get(animal1.id)
    a2 = world.get(animal2.id)
    a1.memes["helping"] += 1
    a2.memes["helping"] += 1
    world.say(
        f"{animal1.label.capitalize()} used {animal1.help}, and {animal2.label.capitalize()} "
        f"used {animal2.help}. Together they made a careful little search."
    )


def rescue(world: World, keeper: Entity, fix: Fix, veil: Veil) -> None:
    world.get("veil").meters["lost"] = 0
    keeper.memes["relief"] += 1
    world.say(
        f"{keeper.id} came over quickly and {fix.text.format(item=veil.label)}."
    )
    world.say(
        f"The veil was safe again, and the animals stopped to watch the little "
        f"flapping cloth settle in {keeper.id}'s hands."
    )


def fail_rescue(world: World, keeper: Entity, fix: Fix, veil: Veil) -> None:
    world.say(
        f"{keeper.id} tried to help, but {fix.fail.format(item=veil.label)}."
    )
    world.say(
        "The veil stayed out of reach, and the search had to become a bigger team job."
    )


def ending(world: World, child: Entity, keeper: Entity, veil: Veil, fix: Fix) -> None:
    child.memes["joy"] += 1
    keeper.memes["joy"] += 1
    world.say(
        f"After that, {keeper.id} tucked the veil neatly in place, and {child.id} "
        f"held it with both hands while the animals watched."
    )
    world.say(
        f"This time, the zoo felt calm, bright, and full of teamwork."
    )


def tale(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    veil = VEILS[params.veil]
    animal1 = ANIMALS[params.animal1]
    animal2 = ANIMALS[params.animal2]
    fix = FIXES[params.fixer]

    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    keeper = world.add(Entity(id="keeper", kind="character", type=params.keeper_type, label=params.keeper_name))
    veil_ent = world.add(Entity(id="veil", kind="thing", type="thing", label=veil.label))
    world.add(Entity(id=animal1.id, kind="character", type=animal1.species, label=animal1.label))
    world.add(Entity(id=animal2.id, kind="character", type=animal2.species, label=animal2.label))

    tell_flashback(world, setting, child, keeper, veil)
    world.para()
    trigger_loss(world, veil, animal1)
    flashback(world, child, keeper, veil)
    teamwork_search(world, animal1, animal2)
    world.para()
    if fix.sense >= SENSE_MIN:
        rescue(world, keeper, fix, veil)
    else:
        fail_rescue(world, keeper, fix, veil)
    ending(world, child, keeper, veil, fix)

    world.facts.update(
        setting=setting,
        veil=veil,
        animal1=animal1,
        animal2=animal2,
        fix=fix,
        child=child,
        keeper=keeper,
        lost=veil_ent.meters["lost"] >= THRESHOLD,
        teamwork=True,
    )
    return world


SETTINGS = {
    "zoo": Setting(
        id="zoo",
        place="the zoo",
        detail="the bright paths between the animal homes",
        flashback_seed="a breezy day by the goat pen",
        tags={"zoo"},
    )
}

VEILS = {
    "sunveil": Veil(
        id="sunveil",
        label="veil",
        phrase="a light veil over her hat",
        use="it kept the sun out of her eyes",
        snag_risk=2,
        tags={"veil"},
    ),
    "playveil": Veil(
        id="playveil",
        label="veil",
        phrase="a soft veil for dress-up",
        use="it made the zoo game feel special",
        snag_risk=3,
        tags={"veil"},
    ),
}

ANIMALS = {
    "monkey": Animal("monkey", "monkey", "the monkey", "banana pole", "wave ropes", 3, {"animal", "teamwork"}),
    "giraffe": Animal("giraffe", "giraffe", "the giraffe", "tall gate", "stretching necks", 2, {"animal", "teamwork"}),
    "penguin": Animal("penguin", "penguin", "the penguin", "ice path", "sliding together", 3, {"animal", "teamwork"}),
    "elephant": Animal("elephant", "elephant", "the elephant", "mud lane", "trumpeting softly", 3, {"animal", "teamwork"}),
    "parrot": Animal("parrot", "parrot", "the parrot", "branch rail", "calling directions", 2, {"animal", "teamwork"}),
    "otter": Animal("otter", "otter", "the otter", "stream edge", "paddling in pairs", 3, {"animal", "teamwork"}),
}

FIXES = {
    "gentle_grab": Fix(
        id="gentle_grab",
        sense=3,
        effort=2,
        text="gently reached up and gathered {item} before it snagged on the fence",
        fail="reached too slowly and the cloth slipped away again",
        qa_text="gently gathered the veil before it snagged on the fence",
        tags={"veil", "teamwork"},
    ),
    "wide_search": Fix(
        id="wide_search",
        sense=2,
        effort=3,
        text="worked with the animals and found {item} near the fountain",
        fail="looked everywhere, but the veil was still hidden by the path",
        qa_text="worked with the animals and found the veil near the fountain",
        tags={"veil", "teamwork"},
    ),
    "toy_signal": Fix(
        id="toy_signal",
        sense=1,
        effort=1,
        text="waved a tiny toy and hoped {item} would come back",
        fail="only made a pretty motion in the air, which did not solve anything",
        qa_text="waved a tiny toy and hoped the veil would come back",
        tags={"veil"},
    ),
}

CURATED = [
    StoryParams(setting="zoo", veil="sunveil", animal1="monkey", animal2="parrot", fixer="gentle_grab",
                keeper_name="Maya", keeper_type="keeper", child_name="Nina", child_type="girl"),
    StoryParams(setting="zoo", veil="playveil", animal1="penguin", animal2="otter", fixer="wide_search",
                keeper_name="Owen", keeper_type="keeper", child_name="Leo", child_type="boy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Zoo veil teamwork storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--veil", choices=VEILS)
    ap.add_argument("--animal1", choices=ANIMALS)
    ap.add_argument("--animal2", choices=ANIMALS)
    ap.add_argument("--fixer", choices=FIXES)
    ap.add_argument("--keeper-name")
    ap.add_argument("--keeper-type", choices=["keeper"])
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
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
    if args.fixer and FIXES[args.fixer].sense < SENSE_MIN:
        raise StoryError(f"(Refusing fixer {args.fixer}: too weak and not sensible enough.)")
    settings = list(SETTINGS)
    setting = args.setting or rng.choice(settings)
    veil = args.veil or rng.choice(list(VEILS))
    animal1 = args.animal1 or rng.choice(list(ANIMALS))
    animal2 = args.animal2 or rng.choice([a for a in ANIMALS if a != animal1])
    if not valid_animal_pair(ANIMALS[animal1], ANIMALS[animal2]):
        animal2 = "parrot" if animal1 != "parrot" else "otter"
    fixer = args.fixer or rng.choice(sorted(f.id for f in sensible_fixes()))
    keeper_name = args.keeper_name or rng.choice(["Maya", "Owen", "Rin", "Tess"])
    keeper_type = args.keeper_type or "keeper"
    child_name = args.child_name or rng.choice(["Nina", "Leo", "Ada", "Finn", "Mia"])
    child_type = args.child_type or rng.choice(["girl", "boy"])
    return StoryParams(setting=setting, veil=veil, animal1=animal1, animal2=animal2, fixer=fixer,
                       keeper_name=keeper_name, keeper_type=keeper_type,
                       child_name=child_name, child_type=child_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly animal story set at the zoo that includes the word "veil" and shows teamwork.',
        f"Tell a story where {f['child'].label} loses a veil at the zoo, remembers a past moment in a flashback, and works with animals to get it back.",
        f"Write a gentle zoo adventure about a veil, a flashback, and teamwork between people and animals.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    keeper = f["keeper"]
    animal1 = f["animal1"]
    animal2 = f["animal2"]
    veil = f["veil"]
    fix = f["fix"]
    qa = [
        QAItem(
            question="What is the story about?",
            answer=f"It is about {child.label} and {keeper.label} at the zoo, plus {animal1.label} and {animal2.label} helping with a lost veil. The flashback shows why the veil mattered and why everyone stayed calm.",
        ),
        QAItem(
            question=f"What happened to the veil?",
            answer="A gust of wind carried it away toward the animal path. That made everyone pause, remember the earlier moment, and work together to bring it back safely.",
        ),
        QAItem(
            question="How did teamwork help?",
            answer=f"{animal1.label.capitalize()} and {animal2.label.capitalize()} helped search from different sides, so the grown-up could use the best fix. Their teamwork made the search careful instead of rushed.",
        ),
    ]
    if f["lost"]:
        qa.append(
            QAItem(
                question="Why did the flashback matter?",
                answer=f"It reminded {child.label} how to hold the veil close, so the story could turn from worry to action. That memory helped everyone solve the problem without getting upset.",
            )
        )
    if fix.sense >= SENSE_MIN:
        qa.append(
            QAItem(
                question="How was the problem solved?",
                answer=f"{keeper.label} used a calm, sensible plan and {fix.qa_text}. After that, the veil was safe again and the zoo visit could continue.",
            )
        )
    return qa


WORLD_QA = {
    "veil": [
        ("What is a veil?", "A veil is a light piece of cloth that can be worn for shade, dress-up, or ceremony. It needs gentle handling because it can flutter away in the wind."),
    ],
    "zoo": [
        ("What is a zoo?", "A zoo is a place where people can visit and learn about animals. The paths, pens, and animal homes are arranged so visitors and animals stay safe."),
    ],
    "teamwork": [
        ("What is teamwork?", "Teamwork means different helpers work together to do one job. Each helper does a small part, and the job becomes easier and kinder."),
    ],
    "flashback": [
        ("What is a flashback in a story?", "A flashback is a quick memory of something that happened before now. It helps explain why a character feels worried, brave, or ready to act."),
    ],
    "animal": [
        ("Why do stories use animals?", "Animals can make a story playful, gentle, and easy to imagine. They can also show friendship and cooperation in a simple way."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["veil"].tags)
    tags.add("zoo")
    tags.add("teamwork")
    out = []
    for key, items in WORLD_QA.items():
        if key in tags:
            out.extend(QAItem(q, a) for q, a in items)
    out.append(QAItem("What does teamwork do in this story?", "Teamwork helps the people and animals solve the veil problem together. It turns a scary lost moment into a careful search and a safe ending."))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible(F) :- fix(F), sense(F,S), sense_min(M), S >= M.
valid(S,V,A1,A2) :- setting(S), veil(V), animal(A1), animal(A2), A1 != A2, teamwork_ok(A1,A2), sensible_fix.
teamwork_ok(A1,A2) :- animal(A1), animal(A2), score(A1,S1), score(A2,S2), A1 != A2, S1 + S2 >= 5.
lost(V) :- veil(V), wind.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for vid in VEILS:
        lines.append(asp.fact("veil", vid))
    for aid, a in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
        lines.append(asp.fact("score", aid, a.teamwork_score))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(v for (v,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import asp
    rc = 0
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    sample = generate(CURATED[0])
    if not sample.story.strip():
        return 1
    print("OK: smoke test story generated.")
    return rc


def generate(params: StoryParams) -> StorySample:
    for key, table in (("setting", SETTINGS), ("veil", VEILS), ("animal1", ANIMALS), ("animal2", ANIMALS), ("fixer", FIXES)):
        if getattr(params, key) not in table:
            raise StoryError(f"(Unknown {key}: {getattr(params, key)}.)")
    if params.animal1 == params.animal2:
        raise StoryError("(The two animals need to be different helpers.)")
    if not valid_animal_pair(ANIMALS[params.animal1], ANIMALS[params.animal2]):
        raise StoryError("(Those animals do not have enough teamwork together.)")
    fix = FIXES[params.fixer]
    if fix.sense < SENSE_MIN:
        raise StoryError("(That fix is too weak to count as a sensible story move.)")
    world = tale(params)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    fixer = args.fixer or rng.choice(sorted(f.id for f in sensible_fixes()))
    animal1 = args.animal1 or rng.choice(list(ANIMALS))
    animal2 = args.animal2 or rng.choice([a for a in ANIMALS if a != animal1])
    if not valid_animal_pair(ANIMALS[animal1], ANIMALS[animal2]):
        animal2 = "parrot" if animal1 != "parrot" else "otter"
    return StoryParams(
        setting=args.setting or "zoo",
        veil=args.veil or rng.choice(list(VEILS)),
        animal1=animal1,
        animal2=animal2,
        fixer=fixer,
        keeper_name=args.keeper_name or rng.choice(["Maya", "Owen", "Rin", "Tess"]),
        keeper_type=args.keeper_type or "keeper",
        child_name=args.child_name or rng.choice(["Nina", "Leo", "Ada", "Finn", "Mia"]),
        child_type=args.child_type or rng.choice(["girl", "boy"]),
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print("  " + " ".join(map(str, row)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
