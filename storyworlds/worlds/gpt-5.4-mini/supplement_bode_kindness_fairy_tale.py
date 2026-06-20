#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/supplement_bode_kindness_fairy_tale.py
======================================================================

A standalone story world for a small fairy-tale domain about a child, a kind
helper, a strange little supplement, and a bad omen that is turned aside by
kindness.

Seed words: supplement, bode
Style: Fairy Tale
Feature: Kindness

Premise:
- A young heir or helper in a small fairy tale village feels weak, worried, or
  low in spirit.
- A wise fairy, herb keeper, or gentle parent offers a small supplement such as
  a tonic, mushroom broth, or berry spoonful.
- A dark sign "bodes" trouble, but kindness changes the outcome.
- The story ends with a clear, state-driven change: strength returns, fear
  softens, and the village learns a kinder habit.

This file is self-contained, stdlib-only, and follows the Storyweavers contract.
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

KINDNESS_BOOST = 2.0
WORRY_PENALTY = 1.0


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
        female = {"girl", "mother", "mom", "woman", "queen", "fairy"}
        male = {"boy", "father", "dad", "man", "king", "boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "queen": "queen", "king": "king"}.get(self.type, self.type)



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
    detail: str
    mood: str

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
class Supplement:
    id: str
    label: str
    phrase: str
    taste: str
    makes_strong: bool = True
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
class Omen:
    id: str
    label: str
    phrase: str
    bode_text: str
    danger: int
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
class Remedy:
    id: str
    label: str
    phrase: str
    text: str
    fail_text: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("Helper")
    child = world.entities.get("Child")
    if not helper or not child:
        return out
    if helper.memes["kindness"] < THRESHOLD or child.meters["weakness"] < THRESHOLD:
        return out
    sig = ("kindness",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["strength"] += KINDNESS_BOOST
    child.memes["hope"] += 1
    out.append("__kindness__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    omen = world.entities.get("omen")
    child = world.entities.get("Child")
    if not omen or not child:
        return out
    if omen.meters["gloom"] < THRESHOLD or child.memes["worry"] < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += WORRY_PENALTY
    out.append("__worry__")
    return out


CAUSAL_RULES = [
    Rule("kindness", "social", _r_kindness),
    Rule("worry", "social", _r_worry),
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


def omen_at_risk(omen: Omen, supplement: Supplement) -> bool:
    return omen.danger >= 1 and supplement.makes_strong


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def best_remedy() -> Remedy:
    return max(REMEDIES.values(), key=lambda r: r.sense)


def danger_level(omen: Omen, delay: int) -> int:
    return omen.danger + delay


def can_soften(remedy: Remedy, omen: Omen, delay: int) -> bool:
    return remedy.power >= danger_level(omen, delay)


def forecast(world: World, supplement: Supplement, omen: Omen) -> dict:
    sim = world.copy()
    sim.get("Child").meters["weakness"] += 1
    sim.get("omen").meters["gloom"] += 1
    propagate(sim, narrate=False)
    return {
        "strength": sim.get("Child").meters["strength"],
        "hope": sim.get("Child").memes["hope"],
    }


def setup(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["wonder"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"Once upon a time, in {setting.place}, {child.id} lived by {setting.detail}. "
        f"The days were {setting.mood}, and every pebble seemed to listen."
    )
    world.say(
        f"{helper.id} was a gentle fairy who kept a small basket of remedies and a soft heart."
    )


def weakness(world: World, child: Entity, supplement: Supplement) -> None:
    child.meters["weakness"] += 1
    child.memes["worry"] += 1
    world.say(
        f"But one morning {child.id} felt weak in the legs and low in spirit. "
        f'{child.id} whispered, "I do not feel bright enough for the day."'
    )
    world.say(
        f"{supplement.label.capitalize()} smelled {supplement.taste}, and it was a little {supplement.id} the fairy carried for such days."
    )


def kindness_offer(world: World, helper: Entity, child: Entity, supplement: Supplement) -> None:
    forecast(world, supplement, world.entities["omen"])
    world.say(
        f'{helper.id} brushed a flower petal from {child.pronoun("possessive")} sleeve and said, '
        f'"Kindness can be a sweet {supplement.label} for a tired heart. Take this {supplement.phrase}."'
    )
    child.memes["trust"] += 1


def bode_warning(world: World, omen: Omen) -> None:
    omen.meters["gloom"] += 1
    world.say(
        f"That afternoon, a crow flew over the cottage, and the wind gave a small sigh. "
        f"It seemed to bode trouble, for the path ahead looked dim."
    )


def defy_or_accept(world: World, child: Entity, helper: Entity, supplement: Supplement) -> None:
    child.memes["hope"] += 1
    world.say(
        f"{child.id} tasted the {supplement.label}. It was gentle and warm, and {child.id} listened to {helper.id}'s kind words."
    )


def take_supplement(world: World, child: Entity, supplement: Supplement) -> None:
    child.meters["strength"] += 1
    child.memes["joy"] += 1
    world.say(
        f"{child.id} drank the {supplement.phrase}, and at once {supplement.taste} filled {child.pronoun('possessive')} mouth like sunshine."
    )
    world.say(
        f"The little {supplement.id} did not feel magical in a flashy way; it simply helped {child.id} stand taller."
    )


def resolve(world: World, child: Entity, helper: Entity, remedy: Remedy, supplement: Supplement, omen: Omen) -> None:
    if can_soften(remedy, omen, world.facts["delay"]):
        child.meters["strength"] += 1
        child.memes["fear"] = 0.0
        world.say(
            f"{helper.id} answered the omen with a calm charm and {remedy.text}."
        )
        world.say(
            f"The shadowy sign faded, and the cottage window shone gold again."
        )
        return
    child.meters["fear"] += 1
    world.say(
        f"{helper.id} tried to help, but {remedy.fail_text}."
    )
    world.say(
        f"The omen lingered longer than anyone wished, and the lane stayed gray."
    )


def ending(world: World, child: Entity, helper: Entity, supplement: Supplement) -> None:
    world.say(
        f"By sunset, {child.id} was bright-eyed again. {child.id} kept the empty {supplement.label} cup on the sill as a reminder that kindness can supplement courage."
    )
    world.say(
        f"From that day on, whenever a bad sign seemed to bode trouble, {child.id} remembered to ask for help and answer with kindness."
    )


def tell(setting: Setting, supplement: Supplement, omen: Omen, remedy: Remedy,
         child_name: str = "Ella", child_gender: str = "girl",
         helper_name: str = "Fairy", helper_gender: str = "fairy",
         delay: int = 0) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    om = world.add(Entity(id="omen", kind="thing", type="omen", label=omen.label, role="omen"))
    om.meters["gloom"] = float(omen.danger)

    world.facts["delay"] = delay
    world.facts["supplement"] = supplement
    world.facts["omen"] = omen
    world.facts["remedy"] = remedy
    world.facts["child"] = child
    world.facts["helper"] = helper

    setup(world, child, helper, setting)
    world.para()
    weakness(world, child, supplement)
    bode_warning(world, omen)
    kindness_offer(world, helper, child, supplement)
    defy_or_accept(world, child, helper, supplement)
    take_supplement(world, child, supplement)
    world.para()
    resolve(world, child, helper, remedy, supplement, omen)
    ending(world, child, helper, supplement)

    world.facts.update(
        outcome="kind",
        strengthened=child.meters["strength"] >= THRESHOLD,
        soothed=child.memes["fear"] < THRESHOLD,
    )
    return world


SETTINGS = {
    "cottages": Setting("cottages", "the little cottages", "the rose path and mossy lane", "soft and golden"),
    "forest": Setting("forest", "the forest edge", "the fern bed and winding brook", "green and whispering"),
    "kingdom": Setting("kingdom", "the castle town", "the baker's row and the market square", "busy but kind"),
}

SUPPLEMENTS = {
    "honey_tonic": Supplement("honey_tonic", "honey tonic", "a spoonful of honey tonic", "sweet", True, {"sweet", "kindness"}),
    "berry_broth": Supplement("berry_broth", "berry broth", "a warm berry broth", "berry-sweet", True, {"berry", "kindness"}),
    "mint_sip": Supplement("mint_sip", "mint sip", "a cup of mint sip", "cool and fresh", True, {"mint", "kindness"}),
    "oat_draught": Supplement("oat_draught", "oat draught", "a little oat draught", "mild and toasty", True, {"oat", "kindness"}),
}

OMENS = {
    "crow": Omen("crow", "crow", "a black crow", "bode trouble", 2, {"crow", "omen"}),
    "cloud": Omen("cloud", "cloud", "a low gray cloud", "bode rain and worry", 1, {"cloud", "omen"}),
    "wind": Omen("wind", "wind", "a cold wind", "bode a long hard hour", 1, {"wind", "omen"}),
}

REMEDIES = {
    "song": Remedy("song", "song", "a soft song", "sang a soft song and soothed the whole lane", "sang bravely, but the shadow did not lift", 2, 3, {"song", "kindness"}),
    "blanket": Remedy("blanket", "blanket", "a warm blanket", "wrapped the child in a warm blanket and waited kindly", "wrapped the child, but the chill still clung", 2, 2, {"blanket", "kindness"}),
    "lamp": Remedy("lamp", "lamp", "a small lamp", "lit a small lamp and let its gold chase the gloom away", "lit the lamp, but it was too dim for the night", 3, 3, {"lamp", "kindness"}),
}

GIRL_NAMES = ["Ella", "Mina", "Rose", "Mira", "Lily", "Anya"]
BOY_NAMES = ["Theo", "Nico", "Finn", "Pip", "Oren", "Jasper"]
FAIRY_NAMES = ["Fairy", "Luma", "Nell", "Bria", "Tess"]

TRAITS = ["kind", "gentle", "patient", "cheerful", "careful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for supp_id, supp in SUPPLEMENTS.items():
            for om_id, omen in OMENS.items():
                if omen_at_risk(omen, supp):
                    combos.append((sid, supp_id, om_id))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    supplement: str
    omen: str
    remedy: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    trait: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    supp = f["supplement"]
    omen = f["omen"]
    setting = f["setting"]
    return [
        f'Write a fairy tale for a young child where a gentle helper offers a {supp.label} and kindness helps a worried child feel better.',
        f"Tell a fairy tale in {setting.place} where {child.id} feels weak, a {omen.label} seems to bode trouble, and a small {supp.label} becomes part of the cure.",
        f'Write a soft, child-friendly story that includes the words "supplement" and "bode" and ends with kindness winning the day.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    supp = f["supplement"]
    omen = f["omen"]
    qa = [
        QAItem(f"Who is the story about?", f"It is about {child.id} and {helper.id}, who live in a fairy-tale place and try to help each other."),
        QAItem(f"What did {child.id} feel at the start?", f"{child.id} felt weak and worried at the start. The little worry made the day feel heavy until help arrived."),
        QAItem(f"What did the helper give {child.id}?", f"{helper.id} gave {child.id} {supp.phrase}. It was a small supplement, meant to help the child grow stronger and steadier."),
        QAItem(f"What seemed to bode trouble?", f"{omen.phrase} seemed to bode trouble. It made the path look dim, but kindness answered it."),
    ]
    if f.get("strengthened"):
        qa.append(QAItem(
            f"How did the story end?",
            f"It ended with {child.id} feeling stronger and calmer. The kindness did the most important work, and the supplement helped the child stand tall again."
        ))
        qa.append(QAItem(
            f"Why did the kind helper matter?",
            f"{helper.id} mattered because {helper.id} noticed the problem early and stayed gentle. That kindness gave {child.id} courage before the omen could grow bigger."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a supplement?", "A supplement is something small you take or use to help your body or spirit, like a gentle tonic, broth, or vitamin."),
        QAItem("What does it mean when something bodes trouble?", "If something bodes trouble, it seems to warn that something bad may happen later."),
        QAItem("What is kindness?", "Kindness means being gentle, helpful, and caring to someone else."),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(supplement: Supplement, omen: Omen) -> str:
    if not omen_at_risk(omen, supplement):
        return "(No story: this omen does not meaningfully turn on the supplement's little helping power.)"
    return "(No story: the requested combination does not give the story a real omen-and-kindness turn.)"


def explain_remedy(rid: str) -> str:
    r = REMEDIES[rid]
    better = " / ".join(sorted(x.id for x in sensible_remedies()))
    return f"(Refusing remedy '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). Try: {better}.)"


ASP_RULES = r"""
hazard(O, S) :- omen(O), supplement(S), danger(O, D), makes_strong(S).
sensible(R) :- remedy(R), sense(R, X), sense_min(M), X >= M.
valid(Set, S, O) :- setting(Set), supplement(S), omen(O), hazard(O, S).
kindness_effect :- helper_kind, child_weak.
outcome(kind) :- kindness_effect, not gloom_wins.
gloom_wins :- omen_gloom, not kindness_effect.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, s in SUPPLEMENTS.items():
        lines.append(asp.fact("supplement", sid))
        if s.makes_strong:
            lines.append(asp.fact("makes_strong", sid))
    for oid, o in OMENS.items():
        lines.append(asp.fact("omen", oid))
        lines.append(asp.fact("danger", oid, o.danger))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
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


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos")
        rc = 1
    if set(asp_sensible()) != {r.id for r in sensible_remedies()}:
        print("MISMATCH in sensible remedies")
        rc = 1
    # smoke test ordinary generation
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world about kindness, a supplement, and a bad omen.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--supplement", choices=SUPPLEMENTS)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["fairy", "queen", "mother"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.remedy and REMEDIES[args.remedy].sense < SENSE_MIN:
        raise StoryError(explain_remedy(args.remedy))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.supplement is None or c[1] == args.supplement)
              and (args.omen is None or c[2] == args.omen)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, supplement, omen = rng.choice(sorted(combos))
    remedy = args.remedy or rng.choice(sorted(r.id for r in sensible_remedies()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or rng.choice(["fairy", "queen", "mother"])
    helper_name = args.helper_name or rng.choice(FAIRY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, supplement, omen, remedy, child_name, child_gender, helper_name, helper_gender, trait, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SUPPLEMENTS[params.supplement], OMENS[params.omen], REMEDIES[params.remedy],
                 params.child_name, params.child_gender, params.helper_name, params.helper_gender, params.delay)
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


CURATED = [
    StoryParams("cottages", "honey_tonic", "crow", "song", "Ella", "girl", "Luma", "fairy", "kind", 0),
    StoryParams("forest", "berry_broth", "cloud", "blanket", "Theo", "boy", "Nell", "fairy", "gentle", 1),
    StoryParams("kingdom", "mint_sip", "wind", "lamp", "Mira", "girl", "Bria", "queen", "patient", 0),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible remedies: {', '.join(asp_sensible())}\n")
        for setting, supplement, omen in asp_valid_combos():
            print(f"  {setting:10} {supplement:14} {omen}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} in {p.setting} ({p.supplement}, {p.omen})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
