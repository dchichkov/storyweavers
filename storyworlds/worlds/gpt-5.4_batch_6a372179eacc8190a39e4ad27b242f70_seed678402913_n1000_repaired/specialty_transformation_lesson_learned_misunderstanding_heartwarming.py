#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/specialty_transformation_lesson_learned_misunderstanding_heartwarming.py
====================================================================================================

A standalone storyworld about a child who misunderstands a gentle kitchen
transformation. A baker's specialty uses yeast dough, the dough changes while it
rests, the child thinks something has gone wrong and tries to "fix" it, and a
loving grown-up explains that some good things need time to change.

Core shape
----------
- Transformation: plain dough rises, is shaped, and becomes a warm baked treat.
- Misunderstanding: the child mistakes rising dough for a problem.
- Lesson learned: change is not always damage; sometimes it is how a specialty works.
- Style: heartwarming, concrete, child-facing.

Run it
------
python storyworlds/worlds/gpt-5.4/specialty_transformation_lesson_learned_misunderstanding_heartwarming.py
python storyworlds/worlds/gpt-5.4/specialty_transformation_lesson_learned_misunderstanding_heartwarming.py --specialty bread
python storyworlds/worlds/gpt-5.4/specialty_transformation_lesson_learned_misunderstanding_heartwarming.py --specialty pancakes
python storyworlds/worlds/gpt-5.4/specialty_transformation_lesson_learned_misunderstanding_heartwarming.py --all --qa
python storyworlds/worlds/gpt-5.4/specialty_transformation_lesson_learned_misunderstanding_heartwarming.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly
# from its nested subdirectory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


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
        female = {"girl", "mother", "mom", "woman", "aunt", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "uncle", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Specialty:
    id: str
    label: str
    phrase: str
    dough_name: str
    baked_name: str
    shaping: str
    aroma: str
    reveal: str
    resilience: int
    yeasted: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    worry: str
    move: str
    repair: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class WarmPlace:
    id: str
    label: str
    comfort: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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


def _r_worry_from_rise(world: World) -> list[str]:
    dough = world.entities.get("dough")
    child = world.entities.get("child")
    if dough is None or child is None:
        return []
    if dough.meters["risen"] < THRESHOLD:
        return []
    sig = ("worry_from_rise",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    return []


def _r_setback_from_action(world: World) -> list[str]:
    dough = world.entities.get("dough")
    child = world.entities.get("child")
    if dough is None or child is None:
        return []
    if child.meters["interfered"] < THRESHOLD:
        return []
    sig = ("setback",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    dough.meters["setback"] += child.attrs.get("action_severity", 1)
    dough.meters["risen"] = max(0.0, dough.meters["risen"] - child.attrs.get("action_severity", 1))
    return []


def _r_relief_from_explanation(world: World) -> list[str]:
    child = world.entities.get("child")
    if child is None or child.memes["understanding"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1
    child.memes["love"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="worry_from_rise", tag="emotion", apply=_r_worry_from_rise),
    Rule(name="setback_from_action", tag="physical", apply=_r_setback_from_action),
    Rule(name="relief_from_explanation", tag="emotion", apply=_r_relief_from_explanation),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule.apply(world)
            if sent:
                changed = True
                produced.extend(sent)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_specialty(spec: Specialty) -> bool:
    return spec.yeasted


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, spec in SPECIALTIES.items():
        if not valid_specialty(spec):
            continue
        for aid in ACTIONS:
            for wid in WARM_PLACES:
                combos.append((sid, aid, wid))
    return combos


def outcome_of(params: "StoryParams") -> str:
    spec = SPECIALTIES[params.specialty]
    action = ACTIONS[params.action]
    score = action.severity + params.delay
    return "fluffy" if spec.resilience >= score else "squat"


def explain_rejection(spec: Specialty) -> str:
    return (
        f"(No story: {spec.phrase} is not a rising yeast specialty in this world, "
        f"so the child would have no honest reason to mistake a swelling bowl of dough "
        f"for a problem. Pick a specialty like bread, buns, or pretzels.)"
    )


def _rise_prediction(spec: Specialty, action: Action, delay: int) -> dict:
    final_state = "fluffy" if spec.resilience >= action.severity + delay else "squat"
    return {
        "will_change": True,
        "outcome": final_state,
    }


def introduce(world: World, child: Entity, baker: Entity, spec: Specialty, place: WarmPlace) -> None:
    child.memes["joy"] += 1
    baker.memes["care"] += 1
    world.say(
        f"On a soft afternoon, {child.id} stood on a kitchen stool beside {baker.label_word} "
        f"{baker.id}. {baker.id}'s specialty was {spec.phrase}, and the whole kitchen already "
        f"smelled faintly of flour and warmth."
    )
    world.say(
        f"Together they stirred, poured, and kneaded until {spec.dough_name} rested in a bowl. "
        f"{baker.id} set it in {place.label}, where {place.comfort}."
    )


def promise_change(world: World, baker: Entity, spec: Specialty) -> None:
    world.say(
        f'"Now we wait," {baker.id} said. "Good {spec.label} changes a little before it bakes."'
    )


def rise(world: World, child: Entity, dough: Entity, spec: Specialty) -> None:
    dough.meters["risen"] += 2
    dough.meters["alive"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When {child.id} peeked later, the dough had puffed up high against the cloth. "
        f"It looked bigger, rounder, and softer than before, as if the bowl were taking a deep breath."
    )


def misunderstand(world: World, child: Entity, action: Action, spec: Specialty) -> None:
    pred = _rise_prediction(spec, action, world.facts["delay"])
    world.facts["predicted_outcome"] = pred["outcome"]
    child.memes["misunderstanding"] += 1
    child.memes["care"] += 1
    world.say(
        f"{child.id} gasped. {action.worry} To {child.pronoun('object')}, it did not look like a happy change at all."
    )
    world.say(action.move.replace("{child}", child.id))


def intervene(world: World, child: Entity, dough: Entity, action: Action) -> None:
    child.meters["interfered"] += 1
    child.attrs["action_severity"] = action.severity
    propagate(world, narrate=False)
    world.say(
        f"For a moment, {child.id} felt sure {child.pronoun()} was helping."
    )


def explain(world: World, baker: Entity, child: Entity, spec: Specialty, action: Action) -> None:
    child.memes["understanding"] += 1
    baker.memes["care"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {baker.id} came back, saw the bowl, and knelt beside {child.id} instead of scolding. "
        f'"Oh, sweetheart," {baker.pronoun()} said gently, "the dough was supposed to rise. '
        f'That is part of how my specialty works."'
    )
    world.say(
        f'{baker.id} touched the bowl and smiled. "It was changing into something better, not turning bad. '
        f'Yeast makes little air inside the dough, and that helps it become soft when we bake it."'
    )
    world.say(
        f"{child.id} looked at the bowl again and understood the change in a new way."
    )


def repair(world: World, baker: Entity, child: Entity, dough: Entity, action: Action, spec: Specialty) -> None:
    dough.meters["mended"] += 1
    setback = dough.meters["setback"]
    if setback >= THRESHOLD:
        world.say(
            f"Together they {action.repair}. {baker.id} showed {child.id} how to be gentle with dough that was still growing."
        )
    else:
        world.say(
            f"{baker.id} lifted the cloth again and let {child.id} see the dough quietly working. "
            f"They left it to finish its change."
        )
    dough.meters["risen"] += max(1.0, float(spec.resilience) - setback)
    dough.meters["ready"] += 1


def shape_and_bake(world: World, baker: Entity, child: Entity, dough: Entity, spec: Specialty, outcome: str) -> None:
    dough.meters["shaped"] += 1
    dough.meters["baked"] += 1
    dough.meters["transformed"] += 1
    child.memes["wonder"] += 1
    if outcome == "fluffy":
        dough.meters["fluffy"] += 1
        world.say(
            f"Soon they {spec.shaping}, slid the pan into the oven, and watched through the little glass window. "
            f"The pale dough turned golden and full, sending out {spec.aroma}."
        )
    else:
        dough.meters["squat"] += 1
        world.say(
            f"Soon they {spec.shaping}, slid the pan into the oven, and watched through the little glass window. "
            f"The dough baked a little flatter than usual, but it still turned golden and filled the kitchen with {spec.aroma}."
        )
    world.say(spec.reveal)


def closing(world: World, baker: Entity, child: Entity, spec: Specialty, outcome: str) -> None:
    child.memes["lesson"] += 1
    child.memes["joy"] += 1
    if outcome == "fluffy":
        world.say(
            f'{child.id} took a warm bite and smiled. "Your specialty changes on purpose," {child.pronoun()} said.'
        )
        world.say(
            f'{baker.id} laughed softly. "Yes," {baker.pronoun()} said. "And sometimes people do too." '
            f'The kitchen felt extra cozy as they shared the fresh {spec.baked_name} together.'
        )
    else:
        world.say(
            f'{child.id} took a warm bite and blinked in surprise. It was still soft and good. '
            f'"I thought I had ruined it," {child.pronoun()} whispered.'
        )
        world.say(
            f'"You made a mistake because you cared," {baker.id} said, hugging {child.pronoun("object")}. '
            f'"Now you know that some changes are part of growing." They shared the slightly squat but delicious '
            f'{spec.baked_name}, and the lesson felt warm in both of them.'
        )


def tell(
    spec: Specialty,
    action: Action,
    place: WarmPlace,
    *,
    child_name: str,
    child_gender: str,
    baker_name: str,
    baker_type: str,
    delay: int,
    relation_word: str,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        label=child_name,
        attrs={"relation_word": relation_word},
    ))
    baker = world.add(Entity(
        id=baker_name,
        kind="character",
        type=baker_type,
        role="baker",
        label=baker_name,
    ))
    dough = world.add(Entity(
        id="dough",
        kind="thing",
        type="dough",
        label=spec.dough_name,
        phrase=f"the bowl of {spec.dough_name}",
        tags=set(spec.tags),
    ))

    world.facts.update(
        specialty=spec,
        action=action,
        warm_place=place,
        child=child,
        baker=baker,
        dough=dough,
        delay=delay,
        relation_word=relation_word,
    )

    introduce(world, child, baker, spec, place)
    promise_change(world, baker, spec)

    world.para()
    rise(world, child, dough, spec)
    misunderstand(world, child, action, spec)
    intervene(world, child, dough, action)

    if delay > 0:
        dough.meters["setback"] += delay
        world.say(
            "The bowl sat that way for a little while before the grown-up came back."
            if delay == 1 else
            "The bowl sat that way long enough for the dough to lose more of its puff before the grown-up came back."
        )

    world.para()
    explain(world, baker, child, spec, action)
    repair(world, baker, child, dough, action, spec)

    world.para()
    outcome = "fluffy" if spec.resilience >= action.severity + delay else "squat"
    world.facts["outcome"] = outcome
    shape_and_bake(world, baker, child, dough, spec, outcome)
    closing(world, baker, child, spec, outcome)
    return world


SPECIALTIES = {
    "bread": Specialty(
        id="bread",
        label="bread",
        phrase="braided honey bread",
        dough_name="bread dough",
        baked_name="bread",
        shaping="braided the soft ropes of dough together",
        aroma="the sweet smell of warm honey and butter",
        reveal="When the loaf came out, it looked nothing like the quiet lump they had started with. It was shiny, proud, and ready to tear into at the table.",
        resilience=3,
        yeasted=True,
        tags={"yeast", "bread", "baking"},
    ),
    "buns": Specialty(
        id="buns",
        label="buns",
        phrase="cinnamon buns",
        dough_name="bun dough",
        baked_name="buns",
        shaping="rolled the dough, sprinkled cinnamon over it, and cut it into swirls",
        aroma="a sleepy, sweet smell of cinnamon",
        reveal="The little swirls rose shoulder to shoulder in the pan, glossy at the top and soft in the middle, as if they had tucked themselves in together.",
        resilience=2,
        yeasted=True,
        tags={"yeast", "cinnamon", "baking"},
    ),
    "pretzels": Specialty(
        id="pretzels",
        label="pretzels",
        phrase="soft pretzels",
        dough_name="pretzel dough",
        baked_name="pretzels",
        shaping="twisted each rope into a neat pretzel shape",
        aroma="a toasty smell with a tiny bit of salt",
        reveal="The pretzels came out brown and shiny, with curved arms and soft centers. They looked like little smiles resting on the tray.",
        resilience=3,
        yeasted=True,
        tags={"yeast", "pretzel", "baking"},
    ),
    "pancakes": Specialty(
        id="pancakes",
        label="pancakes",
        phrase="blueberry pancakes",
        dough_name="pancake batter",
        baked_name="pancakes",
        shaping="poured small circles onto the griddle",
        aroma="the cozy smell of blueberries",
        reveal="The pancakes puffed on the griddle, not in a waiting bowl.",
        resilience=1,
        yeasted=False,
        tags={"pancakes", "baking"},
    ),
}

ACTIONS = {
    "press_flat": Action(
        id="press_flat",
        worry='"{It} is too puffy! Maybe it needs to be pushed back down," {child} thought.'.replace("{It}", "It"),
        move="{child} lifted the cloth and patted the dough down with both palms, trying to make it small and tidy again.",
        repair="gently gathered the dough back together and let it rest again",
        severity=1,
        tags={"mistake", "dough"},
    ),
    "add_flour": Action(
        id="add_flour",
        worry='"{It} is too sticky and wild. Maybe more flour will stop it," {child} thought.'.replace("{It}", "It"),
        move="{child} sprinkled in an extra snowy handful of flour, hoping the dough would behave.",
        repair="mixed in a little warm water and kneaded until the dough softened again",
        severity=2,
        tags={"mistake", "flour"},
    ),
    "move_cold": Action(
        id="move_cold",
        worry='"{It} keeps growing. Maybe it needs a cooler place," {child} thought.'.replace("{It}", "It"),
        move="{child} carried the bowl to a chilly counter by the window, hoping the dough would calm down there.",
        repair="brought the bowl back to warmth and waited patiently for the dough to wake up again",
        severity=2,
        tags={"mistake", "warmth"},
    ),
}

WARM_PLACES = {
    "windowsill": WarmPlace(
        id="windowsill",
        label="a sunny windowsill",
        comfort="the sun made the bowl feel cozy there",
        tags={"warmth"},
    ),
    "ovenlight": WarmPlace(
        id="ovenlight",
        label="the oven with only the tiny light on",
        comfort="the air inside stayed gently warm",
        tags={"warmth"},
    ),
    "cupboard": WarmPlace(
        id="cupboard",
        label="a quiet cupboard near the stove",
        comfort="everything inside held a calm little pocket of heat",
        tags={"warmth"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora", "Ruby", "Clara"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Noah", "Eli", "Theo", "Jack"]
BAKER_NAMES = {
    "grandmother": ["Grandma June", "Grandma Rosa", "Grandma May"],
    "grandfather": ["Grandpa Ellis", "Grandpa Joe", "Grandpa Tom"],
    "mother": ["Mama Ana", "Mama Ruth", "Mama Grace"],
    "father": ["Dad Martin", "Dad Paul", "Dad Henry"],
}

RELATION_WORD = {
    "grandmother": "grandma",
    "grandfather": "grandpa",
    "mother": "mom",
    "father": "dad",
}


@dataclass
class StoryParams:
    specialty: str
    action: str
    warm_place: str
    child_name: str
    child_gender: str
    baker_name: str
    baker_type: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        specialty="bread",
        action="press_flat",
        warm_place="windowsill",
        child_name="Lily",
        child_gender="girl",
        baker_name="Grandma June",
        baker_type="grandmother",
        delay=0,
    ),
    StoryParams(
        specialty="buns",
        action="add_flour",
        warm_place="cupboard",
        child_name="Ben",
        child_gender="boy",
        baker_name="Dad Martin",
        baker_type="father",
        delay=1,
    ),
    StoryParams(
        specialty="pretzels",
        action="move_cold",
        warm_place="ovenlight",
        child_name="Mia",
        child_gender="girl",
        baker_name="Grandpa Ellis",
        baker_type="grandfather",
        delay=2,
    ),
]


KNOWLEDGE = {
    "yeast": [
        (
            "What does yeast do in dough?",
            "Yeast makes tiny bubbles of air in dough. Those bubbles help dough rise and become soft when it bakes.",
        )
    ],
    "bread": [
        (
            "What is bread dough made to do before baking?",
            "Bread dough is often left to rest and rise before it goes into the oven. That change helps the bread become light and soft.",
        )
    ],
    "cinnamon": [
        (
            "Why do cinnamon buns smell sweet?",
            "Cinnamon has a warm, sweet smell, and when it bakes with sugar and butter the whole kitchen can smell cozy.",
        )
    ],
    "pretzel": [
        (
            "What shape is a pretzel?",
            "A pretzel is usually twisted into a looped shape with two crossed arms. That shape helps it look special and easy to hold.",
        )
    ],
    "warmth": [
        (
            "Why does dough like a warm place?",
            "A warm place helps yeast do its work in the dough. If dough gets too cold, it rises more slowly.",
        )
    ],
    "mistake": [
        (
            "What should you do if you think food is going wrong while a grown-up is cooking?",
            "Ask the grown-up first. Sometimes cooking changes look strange before they turn into something good.",
        )
    ],
    "flour": [
        (
            "What does flour do in dough?",
            "Flour gives dough its body. Too much extra flour can make dough stiffer and less soft.",
        )
    ],
    "baking": [
        (
            "What does an oven do to dough?",
            "An oven uses heat to change soft dough into baked food. The heat makes the outside brown and the inside set.",
        )
    ],
}
KNOWLEDGE_ORDER = ["yeast", "bread", "cinnamon", "pretzel", "warmth", "mistake", "flour", "baking"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    baker = world.facts["baker"]
    spec = world.facts["specialty"]
    action = world.facts["action"]
    relation = world.facts["relation_word"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the word "specialty" and shows a misunderstanding about dough changing.',
        f"Tell a gentle kitchen story where {child.id} worries that {baker.id}'s {spec.label} dough is going wrong, tries to help by {action.id.replace('_', ' ')}, and learns that the change is part of {relation}'s specialty.",
        f'Write a story with transformation, a lesson learned, and a loving grown-up explanation, ending with fresh {spec.baked_name} shared together.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    baker = world.facts["baker"]
    spec = world.facts["specialty"]
    action = world.facts["action"]
    place = world.facts["warm_place"]
    outcome = world.facts["outcome"]
    relation = world.facts["relation_word"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {relation} {baker.id}, who were making {spec.phrase} together. The story follows how {child.id} misunderstood the dough and then learned what was really happening.",
        ),
        (
            f"What was {baker.id}'s specialty?",
            f"{baker.id}'s specialty was {spec.phrase}. That is why the grown-up understood the dough's changes and could explain them calmly.",
        ),
        (
            "What changed in the kitchen?",
            f"The dough rose in {place.label} and became bigger and softer. Later, it baked into warm {spec.baked_name}, so the change was the center of the whole story.",
        ),
        (
            f"Why did {child.id} make a mistake?",
            f"{child.id} saw the dough swelling and thought something had gone wrong. Because {child.pronoun()} wanted to help, {child.pronoun()} acted before asking what the change meant.",
        ),
        (
            f"What lesson did {child.id} learn?",
            f"{child.id} learned that change is not always damage. Sometimes a strange-looking change is exactly how something good grows into its next shape.",
        ),
    ]

    if outcome == "fluffy":
        qa.append(
            (
                f"How did the problem get solved?",
                f"{baker.id} explained that rising was part of the dough's job, and then they gently fixed the bowl together. Because the setback was small enough, the {spec.baked_name} still came out soft and full.",
            )
        )
    else:
        qa.append(
            (
                f"Did the mistake ruin the {spec.baked_name}?",
                f"No. The dough baked a little flatter than usual, but it still turned into something tasty and warm. That helped {child.id} see that mistakes can become lessons instead of disasters.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["specialty"].tags) | set(world.facts["action"].tags) | set(world.facts["warm_place"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% valid combinations: only yeast specialties support this misunderstanding.
valid(S, A, W) :- specialty(S), action(A), warm_place(W), yeasted(S).

impact(V) :- chosen_action(A), severity(A, S), delay(D), V = S + D.
outcome(fluffy) :- chosen_specialty(S), resilience(S, R), impact(V), R >= V.
outcome(squat)  :- chosen_specialty(S), resilience(S, R), impact(V), R < V.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, spec in SPECIALTIES.items():
        lines.append(asp.fact("specialty", sid))
        lines.append(asp.fact("resilience", sid, spec.resilience))
        if spec.yeasted:
            lines.append(asp.fact("yeasted", sid))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("severity", aid, action.severity))
    for wid in WARM_PLACES:
        lines.append(asp.fact("warm_place", wid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_specialty", params.specialty),
            asp.fact("chosen_action", params.action),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def _pick_names(rng: random.Random, gender: str, baker_type: str) -> tuple[str, str]:
    child_name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    baker_name = rng.choice(BAKER_NAMES[baker_type])
    return child_name, baker_name


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a child misunderstands rising dough, learns about transformation, and shares a baker's specialty."
    )
    ap.add_argument("--specialty", choices=SPECIALTIES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--warm-place", dest="warm_place", choices=WARM_PLACES)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--baker-type", choices=["grandmother", "grandfather", "mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the dough stays mishandled before the grown-up returns")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.specialty:
        spec = SPECIALTIES[args.specialty]
        if not valid_specialty(spec):
            raise StoryError(explain_rejection(spec))

    combos = [
        combo
        for combo in valid_combos()
        if (args.specialty is None or combo[0] == args.specialty)
        and (args.action is None or combo[1] == args.action)
        and (args.warm_place is None or combo[2] == args.warm_place)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    specialty, action, warm_place = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    baker_type = args.baker_type or rng.choice(["grandmother", "grandfather", "mother", "father"])
    child_name, baker_name = _pick_names(rng, child_gender, baker_type)
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 2])
    return StoryParams(
        specialty=specialty,
        action=action,
        warm_place=warm_place,
        child_name=child_name,
        child_gender=child_gender,
        baker_name=baker_name,
        baker_type=baker_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.specialty not in SPECIALTIES:
        raise StoryError(f"(Unknown specialty: {params.specialty})")
    if params.action not in ACTIONS:
        raise StoryError(f"(Unknown action: {params.action})")
    if params.warm_place not in WARM_PLACES:
        raise StoryError(f"(Unknown warm place: {params.warm_place})")

    spec = SPECIALTIES[params.specialty]
    if not valid_specialty(spec):
        raise StoryError(explain_rejection(spec))

    world = tell(
        spec,
        ACTIONS[params.action],
        WARM_PLACES[params.warm_place],
        child_name=params.child_name,
        child_gender=params.child_gender,
        baker_name=params.baker_name,
        baker_type=params.baker_type,
        delay=params.delay,
        relation_word=RELATION_WORD[params.baker_type],
    )
    story_text = world.render()
    if not story_text.strip():
        raise StoryError("(Generation failed: empty story.)")
    return StorySample(
        params=params,
        story=story_text,
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


def _smoke_test_generation() -> None:
    for params in CURATED:
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        buf = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buf
            emit(sample, trace=False, qa=False)
        finally:
            sys.stdout = old_stdout
        if not buf.getvalue().strip():
            raise StoryError("(Smoke test failed: emit produced no text.)")
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(17)))
    if "specialty" not in sample.story.lower():
        raise StoryError('(Smoke test failed: expected the story to mention "specialty".)')


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases: list[StoryParams] = list(CURATED)
    for s in range(25):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        p.seed = s
        cases.append(p)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_test_generation()
        print("OK: generation/emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (specialty, action, warm_place) combos:\n")
        for specialty, action, warm_place in combos:
            print(f"  {specialty:10} {action:12} {warm_place}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} and {p.baker_name}: {p.specialty} / {p.action} / {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
