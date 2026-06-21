#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/executive_laundry_room_happy_ending_moral_value.py
==============================================================================

A standalone story world for a fairy-tale-flavoured laundry-room story where a
child wants to rescue a special outfit for a pretend "executive" toy before a
small family ceremony. The world models a simple, child-facing lesson:

    rushing with a harsh shortcut can ruin a treasured thing,
    but patient care, the right wash, and a helper can save the day.

The domain is deliberately small and constraint-checked. A story is only valid
when:
- the stain really is a problem for the garment,
- the chosen washing method suits the fabric,
- and the item can safely dry in the laundry room after being washed.

The result is always a happy ending in valid stories, but explicit invalid
choices raise StoryError with a concrete reason.

Run it
------
    python storyworlds/worlds/gpt-5.4/executive_laundry_room_happy_ending_moral_value.py
    python storyworlds/worlds/gpt-5.4/executive_laundry_room_happy_ending_moral_value.py --garment sash --stain jam
    python storyworlds/worlds/gpt-5.4/executive_laundry_room_happy_ending_moral_value.py --fabric silk --method hot_wash
    python storyworlds/worlds/gpt-5.4/executive_laundry_room_happy_ending_moral_value.py --all
    python storyworlds/worlds/gpt-5.4/executive_laundry_room_happy_ending_moral_value.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/executive_laundry_room_happy_ending_moral_value.py --qa --json
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
        female = {"girl", "mother", "woman", "queen"}
        male = {"boy", "father", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Garment:
    id: str
    label: str
    phrase: str
    role_title: str
    closing_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fabric:
    id: str
    label: str
    adjective: str
    delicate: bool
    hot_safe: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Stain:
    id: str
    label: str
    source: str
    color: str
    needs_cold: bool
    needs_gentle: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    water_temp: str
    gentle: bool
    strength: int
    safe_for_delicate: bool
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Drying:
    id: str
    label: str
    heat: str
    safe_for_delicate: bool
    line_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_stain_worry(world: World) -> list[str]:
    out: list[str] = []
    cloth = world.get("cloth")
    child = world.get("child")
    if cloth.meters["stained"] >= THRESHOLD:
        sig = ("worry", "child")
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_gentle_care(world: World) -> list[str]:
    out: list[str] = []
    cloth = world.get("cloth")
    child = world.get("child")
    helper = world.get("helper")
    if cloth.meters["clean"] >= THRESHOLD:
        sig = ("relief", "all")
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["relief"] += 1
            helper.memes["pride"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule("stain_worry", "emotional", _r_stain_worry),
    Rule("gentle_care", "emotional", _r_gentle_care),
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


GARMENTS = {
    "sash": Garment(
        "sash",
        "sash",
        "a little blue sash",
        "executive",
        "the little executive sash shone neatly across the toy's chest",
        tags={"sash"},
    ),
    "cape": Garment(
        "cape",
        "cape",
        "a small velvet cape",
        "executive",
        "the small executive cape fluttered as if it knew important things",
        tags={"cape"},
    ),
    "apron": Garment(
        "apron",
        "apron",
        "a tiny striped apron",
        "executive",
        "the tiny executive apron hung straight and proud",
        tags={"apron"},
    ),
}

FABRICS = {
    "cotton": Fabric("cotton", "cotton", "soft", delicate=False, hot_safe=True, tags={"cotton"}),
    "linen": Fabric("linen", "linen", "smooth", delicate=False, hot_safe=True, tags={"linen"}),
    "silk": Fabric("silk", "silk", "shiny", delicate=True, hot_safe=False, tags={"silk"}),
}

STAINS = {
    "jam": Stain("jam", "jam", "a breakfast spoon", "red", needs_cold=True, needs_gentle=True,
                 tags={"jam", "cold_water"}),
    "soap": Stain("soap", "soap bubbles", "a bottle with a loose cap", "white", needs_cold=False,
                  needs_gentle=True, tags={"soap"}),
    "dust": Stain("dust", "gray dust", "the floor behind the washer", "gray", needs_cold=False,
                  needs_gentle=True, tags={"dust"}),
}

METHODS = {
    "cold_gentle": Method(
        "cold_gentle", "a cool gentle wash", "cold", gentle=True, strength=3,
        safe_for_delicate=True,
        qa_text="washed it in a cool gentle cycle",
        tags={"cold_cycle", "gentle_cycle"},
    ),
    "warm_gentle": Method(
        "warm_gentle", "a warm gentle wash", "warm", gentle=True, strength=2,
        safe_for_delicate=True,
        qa_text="washed it in a warm gentle cycle",
        tags={"warm_cycle", "gentle_cycle"},
    ),
    "hot_wash": Method(
        "hot_wash", "a hot quick wash", "hot", gentle=False, strength=3,
        safe_for_delicate=False,
        qa_text="tried a hot quick wash",
        tags={"hot_cycle"},
    ),
}

DRYING = {
    "line_dry": Drying(
        "line_dry", "the clothesline above the sink", "none", safe_for_delicate=True,
        line_text="They clipped it to the little clothesline above the sink where the laundry-room window let in a silver stripe of light.",
        qa_text="hung it on the clothesline to dry",
        tags={"clothesline"},
    ),
    "low_dryer": Drying(
        "low_dryer", "the dryer on low", "low", safe_for_delicate=True,
        line_text="They laid it in the dryer on the gentlest low setting and listened to the soft tumbling hum.",
        qa_text="dried it on the dryer's low setting",
        tags={"dryer_low"},
    ),
    "hot_dryer": Drying(
        "hot_dryer", "the dryer on high", "high", safe_for_delicate=False,
        line_text="They would have put it in the hottest dryer heat.",
        qa_text="put it in the dryer on high heat",
        tags={"dryer_high"},
    ),
}

HELPER_STYLES = {
    "mother": {
        "type": "mother",
        "word": "mom",
        "opening": "with sleeves rolled like a kind washer-queen",
    },
    "father": {
        "type": "father",
        "word": "dad",
        "opening": "with a patient smile and a basket balanced on one arm",
    },
    "grandmother": {
        "type": "mother",
        "word": "grandma",
        "opening": "like a gentle queen of soap flakes and folded sheets",
    },
}

GIRL_NAMES = ["Lily", "Mina", "Ava", "Ella", "Nora", "Rose", "Clara", "Ivy"]
BOY_NAMES = ["Leo", "Milo", "Ben", "Finn", "Owen", "Jack", "Theo", "Eli"]
TOY_NAMES = ["Bramble Bunny", "Pepper Bear", "Moss Mouse", "Tidy Fox"]

TRAITS = ["careful", "hopeful", "earnest", "bright", "gentle", "patient"]


def stain_affects(stain: Stain, garment: Garment) -> bool:
    return True


def method_safe(fabric: Fabric, stain: Stain, method: Method) -> bool:
    if fabric.delicate and not method.safe_for_delicate:
        return False
    if stain.needs_cold and method.water_temp != "cold":
        return False
    if stain.needs_gentle and not method.gentle:
        return False
    return True


def drying_safe(fabric: Fabric, drying: Drying) -> bool:
    if fabric.delicate and not drying.safe_for_delicate:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for garment in GARMENTS:
        for fabric in FABRICS:
            for stain in STAINS:
                for method in METHODS:
                    for drying in DRYING:
                        if stain_affects(STAINS[stain], GARMENTS[garment]) and method_safe(FABRICS[fabric], STAINS[stain], METHODS[method]) and drying_safe(FABRICS[fabric], DRYING[drying]):
                            combos.append((garment, fabric, stain, method, drying))
    return combos


def explain_method(fabric: Fabric, stain: Stain, method: Method) -> str:
    if fabric.delicate and not method.safe_for_delicate:
        return (
            f"(No story: {fabric.label} is too delicate for {method.label}. "
            f"A harsh hot rush would not be caring for the treasured garment.)"
        )
    if stain.needs_cold and method.water_temp == "hot":
        return (
            f"(No story: {stain.label} sets in with hot water here, so {method.label} "
            f"would make the trouble worse instead of better.)"
        )
    if stain.needs_gentle and not method.gentle:
        return (
            f"(No story: {stain.label} needs a gentle wash, not a rough quick one. "
            f"This world only tells patient, sensible rescue stories.)"
        )
    return "(No story: that wash method is not reasonable for this fabric and stain.)"


def explain_drying(fabric: Fabric, drying: Drying) -> str:
    return (
        f"(No story: {fabric.label} should not be dried with {drying.label}. "
        f"The ending must care for the garment all the way to the last step.)"
    )


def predict_rescue(world: World, method: Method, drying: Drying) -> dict:
    sim = world.copy()
    cloth = sim.get("cloth")
    apply_wash(sim, cloth, method, narrate=False)
    apply_drying(sim, cloth, drying, narrate=False)
    return {
        "clean": cloth.meters["clean"] >= THRESHOLD,
        "ruined": cloth.meters["ruined"] >= THRESHOLD,
        "ready": cloth.meters["ready"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, toy: Entity, helper: Entity, garment: Garment, fabric: Fabric) -> None:
    opening = helper.attrs["opening"]
    world.say(
        f"Once, in a laundry room where soap smelled sweeter than rain and the washer sang in round silver whispers, "
        f"{child.id} came skipping in with {toy.id}. Beside the baskets stood {child.pronoun('possessive')} {helper.label_word}, {opening}."
    )
    world.say(
        f"{toy.id} was to attend the Evening of Important Toys, and for that grand pretend gathering "
        f"{toy.pronoun('subject')} needed {garment.phrase} of {fabric.adjective} {fabric.label}, fit for a tiny {garment.role_title}."
    )


def accident(world: World, child: Entity, toy: Entity, garment: Garment, stain: Stain) -> None:
    cloth = world.get("cloth")
    cloth.meters["stained"] += 1
    cloth.meters["dirty"] += 1
    child.memes["care"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But before the ribbon could be pinned just right, {toy.id} brushed past {stain.source}, "
        f"and a spot of {stain.color} {stain.label} landed on the {garment.label}."
    )
    world.say(
        f"{child.id} stared at the mark as if a storm cloud had drifted into the bright little room."
    )


def rush_idea(world: World, child: Entity, method: Method) -> None:
    child.memes["urgency"] += 1
    world.say(
        f'"Oh dear," said {child.id}, "I must hurry! Perhaps {method.label} will make it right at once."'
    )


def helper_warn(world: World, child: Entity, helper: Entity, fabric: Fabric, stain: Stain, method: Method, drying: Drying) -> None:
    pred = predict_rescue(world, method, drying)
    child.memes["listening"] += 1
    world.facts["predicted_ready"] = pred["ready"]
    if pred["ruined"]:
        reason = "Heat would be too fierce for such a treasured little thing."
    else:
        reason = "A patient wash would serve better than a rushing one."
    world.say(
        f'{helper.label_word.capitalize()} knelt beside {child.id} and touched the cloth softly. '
        f'"Not every stain yields to speed," {helper.pronoun()} said. "{stain.label.capitalize()} on {fabric.label} must be treated kindly. {reason}"'
    )


def choose_patience(world: World, child: Entity, helper: Entity) -> None:
    child.memes["patience"] += 1
    helper.memes["guidance"] += 1
    world.say(
        f"{child.id} took a small breath, set aside the hurried idea, and nodded. "
        f"{child.pronoun().capitalize()} chose to listen."
    )


def apply_wash(world: World, cloth: Entity, method: Method, narrate: bool = True) -> None:
    cloth.meters["wet"] += 1
    cloth.meters["washed"] += 1
    if not method.gentle:
        cloth.meters["worn"] += 1
    if not method.safe_for_delicate and cloth.attrs.get("delicate"):
        cloth.meters["ruined"] += 1
    if cloth.attrs.get("needs_cold") and method.water_temp != "cold":
        cloth.meters["stain_set"] += 1
    if cloth.attrs.get("needs_gentle") and not method.gentle:
        cloth.meters["stain_set"] += 1
    if cloth.meters["ruined"] < THRESHOLD and cloth.meters["stain_set"] < THRESHOLD:
        cloth.meters["clean"] += 1
        cloth.meters["stained"] = 0.0
    propagate(world, narrate=False)
    if narrate:
        world.say(
            f"Together they measured a little soap, tucked the garment in, and gave it {method.label}."
        )


def apply_drying(world: World, cloth: Entity, drying: Drying, narrate: bool = True) -> None:
    cloth.meters["dried"] += 1
    if cloth.attrs.get("delicate") and not drying.safe_for_delicate:
        cloth.meters["ruined"] += 1
    if cloth.meters["clean"] >= THRESHOLD and cloth.meters["ruined"] < THRESHOLD:
        cloth.meters["ready"] += 1
    propagate(world, narrate=False)
    if narrate:
        world.say(drying.line_text)


def success(world: World, child: Entity, toy: Entity, garment: Garment) -> None:
    cloth = world.get("cloth")
    child.memes["joy"] += 1
    toy.memes["pride"] += 1
    if cloth.meters["ready"] >= THRESHOLD:
        world.say(
            f"When at last they lifted it down, no stain remained. The cloth smelled of clean air and warm kindness."
        )
        world.say(
            f"{child.id} tied it neatly on {toy.id}, and {garment.closing_image}."
        )
        world.say(
            f'That evening, {toy.id} sat upon the folded towels as if upon a throne, and {child.id} laughed. '
            f'"A true executive should be tidy," {child.pronoun()} said, "but kinder still should be the hands that help."'
        )


def moral(world: World, child: Entity, helper: Entity) -> None:
    child.memes["lesson"] += 1
    helper.memes["love"] += 1
    world.say(
        f'{helper.label_word.capitalize()} smiled and kissed the top of {child.id}\'s head. '
        f'"Remember this," {helper.pronoun()} said softly. "In small work and great work alike, patient care is wiser than a hasty shortcut."'
    )
    world.say(
        f"And so the laundry room kept its silver hum, and {child.id} learned that gentle work can save the things we love."
    )


def tell(
    garment: Garment,
    fabric: Fabric,
    stain: Stain,
    method: Method,
    drying: Drying,
    child_name: str = "Lily",
    child_gender: str = "girl",
    helper_kind: str = "mother",
    toy_name: str = "Bramble Bunny",
    trait: str = "patient",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", traits=[trait]))
    helper_info = HELPER_STYLES[helper_kind]
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_info["type"],
        role="helper",
        label=helper_kind,
        attrs={"opening": helper_info["opening"]},
    ))
    toy = world.add(Entity(id=toy_name, kind="thing", type="toy", role="toy", label=toy_name))
    cloth = world.add(Entity(
        id="cloth",
        kind="thing",
        type=garment.label,
        role="garment",
        label=garment.label,
        attrs={
            "fabric": fabric.id,
            "delicate": fabric.delicate,
            "needs_cold": stain.needs_cold,
            "needs_gentle": stain.needs_gentle,
        },
    ))

    introduce(world, child, toy, helper, garment, fabric)
    world.para()
    accident(world, child, toy, garment, stain)
    rush_idea(world, child, method)
    helper_warn(world, child, helper, fabric, stain, method, drying)
    choose_patience(world, child, helper)
    world.para()
    apply_wash(world, cloth, method, narrate=True)
    apply_drying(world, cloth, drying, narrate=True)
    success(world, child, toy, garment)
    world.para()
    moral(world, child, helper)

    world.facts.update(
        child=child,
        helper=helper,
        toy=toy,
        cloth=cloth,
        garment=garment,
        fabric=fabric,
        stain=stain,
        method=method,
        drying=drying,
        happy=cloth.meters["ready"] >= THRESHOLD and cloth.meters["ruined"] < THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    garment: str
    fabric: str
    stain: str
    method: str
    drying: str
    child_name: str
    child_gender: str
    helper: str
    toy_name: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "jam": [(
        "Why should some stains be washed with cool water?",
        "Some stains, like jam here, can cling more tightly when very hot water touches them. Cool water can be gentler and helps you clean without setting the stain."
    )],
    "soap": [(
        "What are soap bubbles for?",
        "Soap bubbles help lift dirt and sticky things away from cloth. They make washing easier when used carefully."
    )],
    "dust": [(
        "Why does dust make clothes look dirty?",
        "Dust is made of tiny dry bits that settle on things. When it sticks to cloth, the cloth can look dull and gray."
    )],
    "silk": [(
        "Why does silk need gentle care?",
        "Silk is a delicate fabric with soft fine threads. Rough washing or strong heat can harm it, so it should be treated gently."
    )],
    "cotton": [(
        "What is cotton cloth like?",
        "Cotton is a soft cloth made from plant fibers. It is comfortable and often easier to wash than delicate fabrics."
    )],
    "linen": [(
        "What is linen?",
        "Linen is a cloth made from plant fibers too, and it can feel smooth and cool. It is often strong, but it still needs sensible washing."
    )],
    "gentle_cycle": [(
        "What does a gentle wash cycle do?",
        "A gentle wash cycle moves more softly than a rough fast one. It helps clean cloth without pulling and twisting it too hard."
    )],
    "clothesline": [(
        "What is a clothesline for?",
        "A clothesline is a line where wet clothes can hang while air dries them. It is a calm way to dry delicate things."
    )],
    "dryer_low": [(
        "Why do people use a low dryer setting for delicate things?",
        "A low setting uses milder heat. That can help a washed item dry without the strong heat that might damage it."
    )],
    "executive": [(
        "What does executive mean in this story?",
        "Here, executive means important and grand in a playful pretend way. The toy is not a real office boss, but the children imagine it as one."
    )],
    "moral": [(
        "What is the moral of the story?",
        "The moral is that patient care is wiser than a hasty shortcut. Taking time to do a job gently can protect something precious."
    )],
}
KNOWLEDGE_ORDER = [
    "executive", "jam", "soap", "dust", "silk", "cotton", "linen",
    "gentle_cycle", "clothesline", "dryer_low", "moral",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    toy = f["toy"]
    garment = f["garment"]
    stain = f["stain"]
    return [
        'Write a fairy-tale style story set in a laundry room with a happy ending and a clear moral. Include the word "executive".',
        f"Tell a gentle story where {child.id} must clean {garment.phrase} for {toy.id} after a spot of {stain.label} lands on it, and learns that patience is wiser than rushing.",
        "Write a small magical-feeling household tale where washing something carefully becomes a lesson about kindness, care, and doing things the right way.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    toy = f["toy"]
    garment = f["garment"]
    fabric = f["fabric"]
    stain = f["stain"]
    method = f["method"]
    drying = f["drying"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} helper in the laundry room, and {toy.id}. They were trying to make {garment.phrase} ready for an important pretend evening."
        ),
        (
            f"Why was {garment.phrase} important?",
            f"It was important because {toy.id} was going to attend the Evening of Important Toys and needed a tiny {garment.role_title} look. The special garment made the pretend event feel grand and real to {child.id}."
        ),
        (
            f"What problem happened in the laundry room?",
            f"A spot of {stain.color} {stain.label} landed on the {garment.label}. That made {child.id} worry because the garment was supposed to look neat for the evening."
        ),
        (
            f"Why did {helper.label_word} tell {child.id} not to rush?",
            f"{helper.label_word.capitalize()} said the {stain.label} on {fabric.label} had to be treated kindly. Rushing could make the little garment harder to save, so patience was the safer and wiser choice."
        ),
        (
            "How did they fix the problem?",
            f"They {method.qa_text} and then {drying.qa_text}. Because they cared for the cloth gently all the way through, the stain came out and the garment was ready again."
        ),
        (
            "How did the story end?",
            f"It ended happily: the garment was clean, dry, and tied neatly onto {toy.id}. The last image shows {toy.id} looking like a proud little executive while {child.id} smiles."
        ),
        (
            "What lesson did the child learn?",
            f"{child.id} learned that patient care is wiser than a hasty shortcut. The clean garment proved that gentle work can protect something precious."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"executive", "moral"}
    tags |= set(f["stain"].tags)
    tags |= set(f["fabric"].tags)
    tags |= set(f["method"].tags)
    tags |= set(f["drying"].tags)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        attrs = {k: v for k, v in e.attrs.items() if v} if e.attrs else {}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("sash", "silk", "jam", "cold_gentle", "line_dry", "Lily", "girl", "mother", "Bramble Bunny", "patient"),
    StoryParams("cape", "cotton", "dust", "warm_gentle", "low_dryer", "Leo", "boy", "father", "Pepper Bear", "earnest"),
    StoryParams("apron", "linen", "soap", "warm_gentle", "line_dry", "Nora", "girl", "grandmother", "Moss Mouse", "bright"),
    StoryParams("sash", "cotton", "jam", "cold_gentle", "low_dryer", "Finn", "boy", "mother", "Tidy Fox", "hopeful"),
]


ASP_RULES = r"""
affects(G,S) :- garment(G), stain(S).

method_safe(F,S,M) :- fabric(F), stain(S), method(M),
                      not delicate(F), not needs_cold_block(S,M), not needs_gentle_block(S,M).
method_safe(F,S,M) :- fabric(F), stain(S), method(M),
                      delicate(F), safe_delicate(M), not needs_cold_block(S,M), not needs_gentle_block(S,M).

needs_cold_block(S,M) :- stain(S), method(M), needs_cold(S), not water_temp(M, cold).
needs_gentle_block(S,M) :- stain(S), method(M), needs_gentle(S), not gentle(M).

drying_safe(F,D) :- fabric(F), drying(D), not delicate(F).
drying_safe(F,D) :- fabric(F), drying(D), delicate(F), drying_delicate(D).

valid(G,F,S,M,D) :- affects(G,S), method_safe(F,S,M), drying_safe(F,D).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for g in GARMENTS:
        lines.append(asp.fact("garment", g))
    for f_id, f in FABRICS.items():
        lines.append(asp.fact("fabric", f_id))
        if f.delicate:
            lines.append(asp.fact("delicate", f_id))
    for s_id, s in STAINS.items():
        lines.append(asp.fact("stain", s_id))
        if s.needs_cold:
            lines.append(asp.fact("needs_cold", s_id))
        if s.needs_gentle:
            lines.append(asp.fact("needs_gentle", s_id))
    for m_id, m in METHODS.items():
        lines.append(asp.fact("method", m_id))
        lines.append(asp.fact("water_temp", m_id, m.water_temp))
        if m.gentle:
            lines.append(asp.fact("gentle", m_id))
        if m.safe_for_delicate:
            lines.append(asp.fact("safe_delicate", m_id))
    for d_id, d in DRYING.items():
        lines.append(asp.fact("drying", d_id))
        if d.safe_for_delicate:
            lines.append(asp.fact("drying_delicate", d_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale laundry-room story world about patient care, a treasured little outfit, and a happy ending."
    )
    ap.add_argument("--garment", choices=GARMENTS)
    ap.add_argument("--fabric", choices=FABRICS)
    ap.add_argument("--stain", choices=STAINS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--drying", choices=DRYING)
    ap.add_argument("--helper", choices=HELPER_STYLES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches Python and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fabric and args.stain and args.method:
        f, s, m = FABRICS[args.fabric], STAINS[args.stain], METHODS[args.method]
        if not method_safe(f, s, m):
            raise StoryError(explain_method(f, s, m))
    if args.fabric and args.drying:
        f, d = FABRICS[args.fabric], DRYING[args.drying]
        if not drying_safe(f, d):
            raise StoryError(explain_drying(f, d))

    combos = [
        c for c in valid_combos()
        if (args.garment is None or c[0] == args.garment)
        and (args.fabric is None or c[1] == args.fabric)
        and (args.stain is None or c[2] == args.stain)
        and (args.method is None or c[3] == args.method)
        and (args.drying is None or c[4] == args.drying)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    garment, fabric, stain, method, drying = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(sorted(HELPER_STYLES))
    toy_name = rng.choice(TOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(garment, fabric, stain, method, drying, child_name, gender, helper, toy_name, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        GARMENTS[params.garment],
        FABRICS[params.fabric],
        STAINS[params.stain],
        METHODS[params.method],
        DRYING[params.drying],
        params.child_name,
        params.child_gender,
        params.helper,
        params.toy_name,
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
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (garment, fabric, stain, method, drying) combos:\n")
        for garment, fabric, stain, method, drying in combos:
            print(f"  {garment:6} {fabric:6} {stain:5} {method:12} {drying}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.garment} of {p.fabric} with {p.stain} ({p.method}, {p.drying})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
