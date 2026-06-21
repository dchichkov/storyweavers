#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/flax_quest_humor_transformation_comedy.py
====================================================================

A standalone storyworld about a child on a silly little quest for flax so a
plain costume can become something grand and funny. The world models a simple
comedic chain:

    want a transformation
    -> go on a small quest for flax
    -> try a method that may tangle or work
    -> helper fixes it sensibly
    -> ending image proves the transformation happened

The reasonableness gate is narrow on purpose. Not every costume can honestly be
made from flax, and not every fastening method can hold the costume piece in
place. The storyworld prefers small, plausible, child-facing stories over broad
coverage.

Run it
------
    python storyworlds/worlds/gpt-5.4/flax_quest_humor_transformation_comedy.py
    python storyworlds/worlds/gpt-5.4/flax_quest_humor_transformation_comedy.py --persona lion --source hamper
    python storyworlds/worlds/gpt-5.4/flax_quest_humor_transformation_comedy.py --persona cloud
    python storyworlds/worlds/gpt-5.4/flax_quest_humor_transformation_comedy.py --method tape
    python storyworlds/worlds/gpt-5.4/flax_quest_humor_transformation_comedy.py --all
    python storyworlds/worlds/gpt-5.4/flax_quest_humor_transformation_comedy.py --qa --json
    python storyworlds/worlds/gpt-5.4/flax_quest_humor_transformation_comedy.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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


@dataclass
class Persona:
    id: str
    label: str
    article: str
    piece: str
    wear_place: str
    entrance: str
    final_image: str
    needs_flax: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    phrase: str
    place: str
    texture: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    sense: int
    holds: bool
    setup: str
    fix_text: str
    fail_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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


def _r_tangle(world: World) -> list[str]:
    hero = world.get("hero")
    flax = world.get("flax")
    out: list[str] = []
    if flax.meters["loose"] < THRESHOLD:
        return out
    sig = ("tangle", "flax")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["embarrassment"] += 1
    hero.memes["laughter"] += 1
    world.get("room").meters["mess"] += 1
    out.append("__tangle__")
    return out


def _r_transform(world: World) -> list[str]:
    costume = world.get("costume")
    hero = world.get("hero")
    if costume.meters["secure"] < THRESHOLD:
        return []
    sig = ("transform", "hero")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["transformed"] += 1
    hero.memes["pride"] += 1
    hero.memes["joy"] += 1
    return ["__transform__"]


CAUSAL_RULES = [
    Rule(name="tangle", tag="physical", apply=_r_tangle),
    Rule(name="transform", tag="social", apply=_r_transform),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


PERSONAS = {
    "lion": Persona(
        id="lion",
        label="lion",
        article="a",
        piece="mane",
        wear_place="around the face",
        entrance="gave a deep practice roar that sounded more like a squeaky cough",
        final_image="the flax mane bobbed around the child's cheeks like a sun made of straw",
        tags={"lion", "mane", "pretend"},
    ),
    "wizard": Persona(
        id="wizard",
        label="wizard",
        article="a",
        piece="beard",
        wear_place="under the chin",
        entrance="lifted one hand grandly and whispered a spell that rhymed on purpose",
        final_image="the long flax beard swung from the child's chin every time a dramatic finger pointed",
        tags={"wizard", "beard", "pretend"},
    ),
    "mermaid": Persona(
        id="mermaid",
        label="mermaid",
        article="a",
        piece="braid",
        wear_place="down the back",
        entrance="waved from an upside-down laundry basket as if it were a shell throne",
        final_image="the flax braid trailed behind like a pale golden river",
        tags={"mermaid", "braid", "pretend"},
    ),
    "cloud": Persona(
        id="cloud",
        label="cloud",
        article="a",
        piece="puff",
        wear_place="over the head",
        entrance="puffed up both cheeks and tried to drift across the room",
        final_image="the costume looked soft and round",
        needs_flax=False,
        tags={"cloud", "pretend"},
    ),
}

SOURCES = {
    "hamper": Source(
        id="hamper",
        label="linen hamper",
        phrase="the linen hamper by the washroom door",
        place="by the washroom door",
        texture="soft and pale",
        tags={"linen", "hamper", "flax"},
    ),
    "basket": Source(
        id="basket",
        label="spinning basket",
        phrase="Grandma's spinning basket by the window",
        place="by the window",
        texture="long and silky",
        tags={"basket", "flax"},
    ),
    "chest": Source(
        id="chest",
        label="craft chest",
        phrase="the craft chest under the stairs",
        place="under the stairs",
        texture="curly and tickly",
        tags={"craft", "flax"},
    ),
}

METHODS = {
    "ribbon": Method(
        id="ribbon",
        label="ribbon",
        sense=3,
        holds=True,
        setup="tied the flax on with a bright ribbon",
        fix_text="smoothed the flax, tied it on with a bright ribbon, and made a neat little knot that stayed put",
        fail_text="tried to pinch the flax in place with a ribbon, but it slipped before the knot was finished",
        qa_text="used a ribbon to tie the flax on neatly",
        tags={"ribbon", "costume"},
    ),
    "clip": Method(
        id="clip",
        label="clip",
        sense=2,
        holds=True,
        setup="fastened the flax with a sturdy clip",
        fix_text="gathered the flax into a tidy bundle and fastened it with a sturdy clip",
        fail_text="reached for a clip, but the flax kept sliding out sideways",
        qa_text="fastened the flax with a sturdy clip",
        tags={"clip", "costume"},
    ),
    "tape": Method(
        id="tape",
        label="tape",
        sense=1,
        holds=False,
        setup="pressed a strip of tape over the flax",
        fix_text="pressed tape over the flax",
        fail_text="pressed a strip of tape over the flax, but the tape wrinkled, the flax sprang free, and wisps flew everywhere",
        qa_text="tried to use tape on the flax",
        tags={"tape", "costume"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo", "Eli"]
TRAITS = ["dramatic", "curious", "bouncy", "inventive", "cheerful", "earnest"]


def persona_works_with_flax(persona: Persona) -> bool:
    return persona.needs_flax


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def method_works(method: Method) -> bool:
    return method.holds and method.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for persona_id, persona in PERSONAS.items():
        if not persona_works_with_flax(persona):
            continue
        for source_id in SOURCES:
            for method_id, method in METHODS.items():
                if method_works(method):
                    combos.append((persona_id, source_id, method_id))
    return combos


@dataclass
class StoryParams:
    persona: str
    source: str
    method: str
    name: str
    gender: str
    helper: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


def introduce(world: World, hero: Entity, helper: Entity, persona: Persona) -> None:
    world.say(
        f"{hero.id} was a {hero.type} with a {hero.attrs['trait']} heart and a grand idea. "
        f"Today {hero.pronoun()} did not want to be ordinary at all. {hero.pronoun().capitalize()} wanted to become {persona.article} {persona.label} for the family's tiny hallway parade."
    )
    world.say(
        f'{helper.id}, {hero.pronoun("possessive")} {helper.label_word}, was folding towels nearby when {hero.id} announced, '
        f'"Please look serious. I am beginning a very important quest."'
    )


def state_need(world: World, hero: Entity, persona: Persona) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"The trouble was simple: a proper {persona.label} needed a {persona.piece}, and {hero.id} had only a plain shirt and a brave face."
    )
    world.say(
        f'"A {persona.piece} goes {persona.wear_place}," {hero.id} explained, as if this were a rule written in a very old book.'
    )


def quest_for_flax(world: World, hero: Entity, source: Source) -> None:
    hero.memes["hope"] += 1
    flax = world.get("flax")
    flax.meters["found"] += 1
    world.say(
        f"So the quest began. {hero.id} padded past the kitchen, peeked behind a chair, and finally found flax in {source.phrase}. It looked {source.texture}, exactly right for pretending."
    )


def comic_try(world: World, hero: Entity, persona: Persona, method: Method) -> None:
    flax = world.get("flax")
    costume = world.get("costume")
    hero.memes["confidence"] += 1
    world.say(
        f"{hero.id} scooped up the flax and {method.setup} to make a {persona.piece}. Then {hero.pronoun()} looked in the shiny kettle and tried {persona.entrance}."
    )
    if method_works(method):
        costume.meters["secure"] += 1
        propagate(world, narrate=False)
    else:
        flax.meters["loose"] += 1
        propagate(world, narrate=False)
        world.say(
            f"But flax is feathery and silly when it is handled badly. {method.fail_text}"
        )
        world.say(
            f"In one blink, {hero.id} had flax on {hero.pronoun('possessive')} shoulder, in {hero.pronoun('possessive')} hair, and nearly up {hero.pronoun('possessive')} nose."
        )


def helper_rescue(world: World, hero: Entity, helper: Entity, persona: Persona, method: Method) -> None:
    costume = world.get("costume")
    flax = world.get("flax")
    world.say(
        f"{helper.id} laughed first, because the sight was too funny to waste, and then knelt to help."
    )
    if method_works(method):
        world.say(
            f'"Hold still, {hero.id}," {helper.id} said, checking the knot with careful fingers.'
        )
    else:
        flax.meters["loose"] = 0.0
        costume.meters["secure"] += 1
        hero.memes["relief"] += 1
        propagate(world, narrate=False)
        better = METHODS["ribbon"]
        world.say(
            f'"That tape was trying to turn you into a haystorm," {helper.id} said. Then {helper.pronoun()} {better.fix_text}.'
        )


def transformation(world: World, hero: Entity, helper: Entity, persona: Persona, method: Method) -> None:
    if hero.meters["transformed"] < THRESHOLD:
        raise StoryError("The costume never became secure enough to support the transformation.")
    hero.memes["laughter"] += 1
    world.say(
        f"When {hero.id} looked again, the plain child in the kettle had vanished. In that bright wobbling reflection stood {persona.article} {persona.label}."
    )
    world.say(
        f"{hero.id} strutted down the hall while {helper.id} clapped. {persona.final_image}."
    )
    world.say(
        f'Everyone laughed, including {hero.id}, because the quest had worked and because pretending so hard looked wonderfully ridiculous in the best possible way.'
    )


def tell(persona: Persona, source: Source, method: Method, name: str, gender: str,
         helper_name: str, helper_type: str, trait: str) -> World:
    world = World()
    hero = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        role="hero",
        attrs={"trait": trait},
        tags={"child"},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
        tags={"adult"},
    ))
    world.add(Entity(id="room", type="room", label="hallway"))
    world.add(Entity(
        id="flax",
        type="material",
        label="flax",
        phrase="a little bundle of flax",
        tags={"flax"},
    ))
    world.add(Entity(
        id="costume",
        type="costume",
        label=persona.piece,
        phrase=f"a pretend {persona.piece}",
        tags={"costume", persona.id},
    ))

    introduce(world, hero, helper, persona)
    state_need(world, hero, persona)

    world.para()
    quest_for_flax(world, hero, source)
    comic_try(world, hero, persona, method)

    world.para()
    helper_rescue(world, hero, helper, persona, method)
    transformation(world, hero, helper, persona, method)

    outcome = "smooth" if method_works(method) else "rescued"
    world.facts.update(
        hero=hero,
        helper=helper,
        persona=persona,
        source=source,
        chosen_method=method,
        actual_fix=method if method_works(method) else METHODS["ribbon"],
        outcome=outcome,
        tangled=world.get("room").meters["mess"] >= THRESHOLD,
        transformed=hero.meters["transformed"] >= THRESHOLD,
        used_flax=world.get("flax").meters["found"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "flax": [
        (
            "What is flax?",
            "Flax is a plant people can use to make soft fiber. That fiber can be turned into thread or cloth."
        )
    ],
    "mane": [
        (
            "What is a mane?",
            "A mane is the long hair around a lion's head or neck. In pretend play, children can make a funny mane from safe craft materials."
        )
    ],
    "beard": [
        (
            "What is a beard?",
            "A beard is hair that grows on a person's chin and cheeks. In costumes, a fake beard can make someone look like a wizard or an old king."
        )
    ],
    "braid": [
        (
            "What is a braid?",
            "A braid is hair or fiber woven into three twisting parts. It hangs together better because the strands are crossed over each other."
        )
    ],
    "ribbon": [
        (
            "What does a ribbon do in a costume?",
            "A ribbon can tie soft things together and help them stay in place. It is useful when a costume piece needs a gentle knot."
        )
    ],
    "clip": [
        (
            "What does a clip do?",
            "A clip pinches or holds things together. It is handy when you want something to stay put without tying it."
        )
    ],
    "pretend": [
        (
            "Why do children like pretend play?",
            "Pretend play lets children imagine being something else for a while. It can feel exciting and funny because an ordinary room turns into a whole new world."
        )
    ],
}
KNOWLEDGE_ORDER = ["flax", "mane", "beard", "braid", "ribbon", "clip", "pretend"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    persona = f["persona"]
    source = f["source"]
    return [
        f'Write a funny story for a 3-to-5-year-old about a small quest for flax that helps a child transform into {persona.article} {persona.label}. Include the word "flax".',
        f"Tell a comedy where {hero.id} searches for flax in {source.phrase} so a plain costume can become a glorious {persona.piece}.",
        f"Write a gentle quest story where a child tries to turn into {persona.article} {persona.label}, something goes a bit silly, and the ending proves the transformation worked.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    persona = f["persona"]
    source = f["source"]
    chosen = f["chosen_method"]
    actual = f["actual_fix"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child who wanted to become {persona.article} {persona.label}, and {helper.id}, the grown-up who helped with the costume."
        ),
        (
            "What was the quest in the story?",
            f"The quest was to find flax so {hero.id} could make a {persona.piece} for the costume. {hero.pronoun().capitalize()} searched until {hero.pronoun()} found it in {source.phrase}."
        ),
        (
            f"Why did {hero.id} need flax?",
            f"{hero.id} wanted the costume to change from plain to splendid. The flax could become a pretend {persona.piece}, which is what made the transformation possible."
        ),
    ]
    if f["tangled"]:
        qa.append(
            (
                f"What went wrong when {hero.id} tried to use the flax?",
                f"The flax did not stay where {hero.pronoun()} wanted it, so it sprang loose and made a funny mess. That happened because {hero.id} tried an unhelpful method, and the soft flax slipped free."
            )
        )
    qa.append(
        (
            f"How did {helper.id} help?",
            f"{helper.id} helped by {actual.qa_text}. The careful fix turned the loose flax into a real costume piece, so the transformation could finally work."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with {hero.id} looking like {persona.article} {persona.label} at last. The final picture shows {persona.final_image}, proving the quest changed something real in the room."
        )
    )
    if chosen.id != actual.id:
        qa.append(
            (
                "Did the first idea work?",
                f"No. {hero.id}'s first idea was to use {chosen.label}, but that only made the flax jump loose. The better idea was {actual.label}, which held the costume piece in place."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"flax", "pretend"}
    persona = f["persona"]
    actual = f["actual_fix"]
    if persona.piece == "mane":
        tags.add("mane")
    elif persona.piece == "beard":
        tags.add("beard")
    elif persona.piece == "braid":
        tags.add("braid")
    if actual.id in {"ribbon", "clip"}:
        tags.add(actual.id)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        persona="lion",
        source="hamper",
        method="ribbon",
        name="Lily",
        gender="girl",
        helper="Mom",
        helper_type="mother",
        trait="dramatic",
    ),
    StoryParams(
        persona="wizard",
        source="basket",
        method="clip",
        name="Ben",
        gender="boy",
        helper="Dad",
        helper_type="father",
        trait="inventive",
    ),
    StoryParams(
        persona="mermaid",
        source="chest",
        method="tape",
        name="Mia",
        gender="girl",
        helper="Mom",
        helper_type="mother",
        trait="cheerful",
    ),
]


def explain_persona(persona: Persona) -> str:
    return (
        f"(No story: becoming {persona.article} {persona.label} does not honestly need flax here. "
        f"This world only tells flax quests for costumes that can plausibly use a flax {persona.piece}.)"
    )


def explain_method(method: Method) -> str:
    good = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method.id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). A sillier attempt may exist inside a story, "
        f"but it is not accepted as the chosen plan. Try: {good}.)"
    )


ASP_RULES = r"""
persona_works(P) :- persona(P), needs_flax(P).
sensible(M) :- method(M), sense(M, S), sense_min(N), S >= N.
holds_well(M) :- method(M), holds(M), sensible(M).
valid(P, S, M) :- persona(P), source(S), method(M), persona_works(P), holds_well(M).

actual_fix(M) :- chosen_method(M), holds_well(M).
actual_fix(ribbon) :- chosen_method(M), not holds_well(M).

tangled :- chosen_method(M), not holds_well(M).
transformed :- actual_fix(_).

outcome(smooth) :- chosen_method(M), holds_well(M), transformed.
outcome(rescued) :- not holds_well(M), chosen_method(M), tangled, transformed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, persona in PERSONAS.items():
        lines.append(asp.fact("persona", pid))
        if persona.needs_flax:
            lines.append(asp.fact("needs_flax", pid))
    for sid in SOURCES:
        lines.append(asp.fact("source", sid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        if method.holds:
            lines.append(asp.fact("holds", mid))
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
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_method", params.method),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "smooth" if method_works(METHODS[params.method]) else "rescued"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_sensible = {m.id for m in sensible_methods()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible methods match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: python={sorted(py_sensible)} clingo={sorted(asp_sens)}")

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if bad:
        rc = 1
        print(f"MISMATCH in outcomes for {len(bad)} scenarios.")
    else:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Empty story during smoke test.")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification surface
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A comedic storyworld about a flax quest and a silly costume transformation."
    )
    ap.add_argument("--persona", choices=PERSONAS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="verify Python and ASP parity")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.persona and not persona_works_with_flax(PERSONAS[args.persona]):
        raise StoryError(explain_persona(PERSONAS[args.persona]))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(METHODS[args.method]))

    combos = [
        combo for combo in valid_combos()
        if (args.persona is None or combo[0] == args.persona)
        and (args.source is None or combo[1] == args.source)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    persona_id, source_id, method_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(pool)
    helper_type = args.helper or rng.choice(["mother", "father"])
    helper_name = "Mom" if helper_type == "mother" else "Dad"
    trait = rng.choice(TRAITS)
    return StoryParams(
        persona=persona_id,
        source=source_id,
        method=method_id,
        name=name,
        gender=gender,
        helper=helper_name,
        helper_type=helper_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.persona not in PERSONAS:
        raise StoryError(f"Unknown persona: {params.persona}")
    if params.source not in SOURCES:
        raise StoryError(f"Unknown source: {params.source}")
    if params.method not in METHODS:
        raise StoryError(f"Unknown method: {params.method}")
    world = tell(
        persona=PERSONAS[params.persona],
        source=SOURCES[params.source],
        method=METHODS[params.method],
        name=params.name,
        gender=params.gender,
        helper_name=params.helper,
        helper_type=params.helper_type,
        trait=params.trait,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sens = asp_sensible()
        combos = asp_valid_combos()
        print(f"sensible methods: {', '.join(sens)}\n")
        print(f"{len(combos)} compatible (persona, source, method) combos:\n")
        for persona, source, method in combos:
            print(f"  {persona:8} {source:8} {method}")
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
            header = f"### {p.name}: {p.persona} from {p.source} with {p.method} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
