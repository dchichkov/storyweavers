#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/camcorder_mischief_parfait_sound_effects_adventure.py
================================================================================

A standalone story world about two children making an adventure movie with a
camcorder, a tempting bit of mischief, and a berry parfait that does *not*
belong near electronics.

The little domain:
- Two children are filming an adventure.
- Their scene needs a sound effect.
- One child gets a mischievous idea: use the parfait beside the camcorder to
  make a "real" squishy sound.
- The other child warns what will happen.
- Either the warning averts the trouble, or the parfait splashes the camcorder.
- A grown-up responds sensibly or too late, and the ending proves the children
  learned to keep snacks away from gear and make sound effects safely.

Run it
------
    python storyworlds/worlds/gpt-5.4/camcorder_mischief_parfait_sound_effects_adventure.py
    python storyworlds/worlds/gpt-5.4/camcorder_mischief_parfait_sound_effects_adventure.py --scene bog --plan spoon_plop
    python storyworlds/worlds/gpt-5.4/camcorder_mischief_parfait_sound_effects_adventure.py --scene cliff
    python storyworlds/worlds/gpt-5.4/camcorder_mischief_parfait_sound_effects_adventure.py --all
    python storyworlds/worlds/gpt-5.4/camcorder_mischief_parfait_sound_effects_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/camcorder_mischief_parfait_sound_effects_adventure.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/camcorder_mischief_parfait_sound_effects_adventure.py --verify
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "thoughtful", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
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


@dataclass
class Scene:
    id: str
    title: str
    setup: str
    goal: str
    obstacle: str
    sound: str
    noise: str
    safe_method: str
    ending_image: str
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
class MischiefPlan:
    id: str
    label: str
    sound: str
    level: int
    action: str
    boom: str
    spill_text: str
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
class Response:
    id: str
    sense: int
    power: int
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_splash_alarm(world: World) -> list[str]:
    camcorder = world.entities.get("camcorder")
    if camcorder is None or camcorder.meters["splashed"] < THRESHOLD:
        return []
    sig = ("splash_alarm", "camcorder")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["fear"] += 1
    if "parent" in world.entities:
        world.get("parent").memes["urgency"] += 1
    return ["__splash__"]


def _r_damage_sadness(world: World) -> list[str]:
    camcorder = world.entities.get("camcorder")
    if camcorder is None or camcorder.meters["damaged"] < THRESHOLD:
        return []
    sig = ("damage_sadness", "camcorder")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["sadness"] += 1
        kid.memes["regret"] += 1
    return ["__damage__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="splash_alarm", tag="physical", apply=_r_splash_alarm),
    Rule(name="damage_sadness", tag="emotional", apply=_r_damage_sadness),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def compatible(scene: Scene, plan: MischiefPlan) -> bool:
    return scene.sound == plan.sound


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def spill_severity(plan: MischiefPlan, delay: int) -> int:
    return plan.level + delay


def is_saved(response: Response, plan: MischiefPlan, delay: int) -> bool:
    return response.power >= spill_severity(plan, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_splash(world: World, plan: MischiefPlan) -> dict:
    sim = world.copy()
    camcorder = sim.get("camcorder")
    parfait = sim.get("parfait")
    parfait.meters["spilled"] += 1
    camcorder.meters["splashed"] += float(plan.level)
    if plan.level >= 2:
        camcorder.meters["sticky"] += 1
    propagate(sim, narrate=False)
    return {
        "splashed": camcorder.meters["splashed"] >= THRESHOLD,
        "sticky": camcorder.meters["sticky"] >= THRESHOLD,
    }


def play_setup(world: World, a: Entity, b: Entity, scene: Scene) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["adventure"] += 1
    world.say(
        f"On a bright afternoon, {a.id} and {b.id} turned the den into {scene.setup}. "
        f"The couch became a trail ridge, a blanket became a map, and their camcorder "
        f"waited on a stack of books to record every brave step."
    )
    world.say(
        f'"Adventure crew, ready!" {a.id} whispered. Tonight they were trying to film '
        f"{scene.goal}."
    )
    world.say(
        f"On the side table sat a tall berry parfait for their snack, striped with yogurt, "
        f"jam, and crunchy crumbs."
    )


def need_sound(world: World, b: Entity, scene: Scene) -> None:
    world.say(
        f"But one part of the movie still felt empty. When the heroes reached {scene.obstacle}, "
        f"the scene needed a {scene.noise} sound effect."
    )
    world.say(f'"We need a good {scene.noise} noise," {b.id} said. "The camcorder can hear everything."')


def tempt(world: World, a: Entity, plan: MischiefPlan) -> None:
    a.memes["mischief"] += 1
    world.say(
        f"{a.id}'s eyes sparkled with mischief. "
        f'"I know! We can use the parfait," {a.pronoun()} said. '
        f'"If I {plan.action}, it will go {plan.boom} and sound real."'
    )


def warn(world: World, b: Entity, a: Entity, plan: MischiefPlan, parent: Entity) -> None:
    pred = predict_splash(world, plan)
    b.memes["caution"] += 1
    world.facts["predicted_splashed"] = pred["splashed"]
    world.facts["predicted_sticky"] = pred["sticky"]
    extra = ""
    if pred["sticky"]:
        extra = " Sticky food and buttons do not belong together."
    world.say(
        f'{b.id} leaned in and shook {b.pronoun("possessive")} head. '
        f'"That is not a sound effect. That is trouble. If the parfait splashes the camcorder, '
        f'''we could ruin it, and then we would not have any movie at all."{extra}'''
    )
    world.say(f'{b.pronoun().capitalize()} remembered what {parent.label_word} always said: snacks stay away from screens and cameras.')


def defy(world: World, a: Entity, b: Entity, plan: MischiefPlan) -> None:
    a.memes["defiance"] += 1
    older_instigator = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older_instigator:
        world.say(
            f'"Just one tiny try," {a.id} said. Because {a.id} was {b.id}\'s older sibling, '
            f"{b.id} could not stop {a.pronoun('object')} in time."
        )
    else:
        world.say(f'"Just one tiny try," {a.id} said, already reaching for the spoon.')


def back_down(world: World, a: Entity, b: Entity, scene: Scene, parent: Entity) -> None:
    a.memes["mischief"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f"{a.id} looked at the camcorder, then at the dripping spoon, and let out a long breath. "
        f'"No parfait mischief," {a.pronoun()} admitted. "You are right."'
    )
    world.say(
        f"They carried the snack back to the table and called for {parent.label_word}. "
        f"Soon they were trying {scene.safe_method} instead."
    )


def splash(world: World, plan: MischiefPlan) -> None:
    camcorder = world.get("camcorder")
    parfait = world.get("parfait")
    parfait.meters["spilled"] += 1
    camcorder.meters["splashed"] += float(plan.level)
    if plan.level >= 2:
        camcorder.meters["sticky"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{plan.boom} {plan.spill_text} A pink-and-gold blur jumped from the parfait cup and spotted "
        f"the side of the camcorder."
    )


def alarm(world: World, b: Entity, parent: Entity) -> None:
    world.say(f'"Oh no -- the camcorder!" {b.id} cried.')
    world.say(f'"{parent.label_word.upper()}!"')


def rescue(world: World, parent: Entity, response: Response, scene: Scene) -> None:
    camcorder = world.get("camcorder")
    camcorder.meters["splashed"] = 0.0
    camcorder.meters["saved"] += 1
    body = response.text
    world.say(f"{parent.label_word.capitalize()} hurried in and {body}.")
    world.say(
        f'After one quiet second, the little red light blinked again. '
        f'"Still working," {parent.pronoun()} said, and everyone breathed out.'
    )
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f'"Sound effects should be made with tools, not with dessert beside a camera," '
        f"{parent.pronoun()} said gently."
    )
    world.para()
    world.say(
        f"Together they tried {scene.safe_method}. {scene.noise.upper()}! It sounded better than the mischief plan."
    )
    world.say(scene.ending_image)


def rescue_fail(world: World, parent: Entity, response: Response) -> None:
    camcorder = world.get("camcorder")
    camcorder.meters["damaged"] += 1
    propagate(world, narrate=False)
    body = response.fail
    world.say(f"{parent.label_word.capitalize()} rushed in and {body}.")
    world.say("But the camcorder gave a weak beep, and the screen stayed dark.")


def sad_lesson(world: World, parent: Entity, a: Entity, b: Entity, scene: Scene) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f"{parent.label_word.capitalize()} pulled both children close. "
        f'"The most important thing is that nobody is hurt," {parent.pronoun()} said. '
        f'"But cameras and sticky food do not mix."'
    )
    world.say(
        f"{a.id} looked at the spoon. {b.id} looked at the dark little screen. They both knew the trouble had begun as mischief."
    )
    world.para()
    world.say(
        f"They could not finish the movie on the camcorder that day, but they still made the {scene.noise} sound with their own mouths and hands -- "
        f"{scene.noise.upper()}! -- just to practice the safe way."
    )
    world.say(
        f"After that, every snack stayed on the far table, and every sound effect was made well away from buttons, wires, and screens."
    )


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"
@dataclass
class StoryParams:
    scene: str
    plan: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    trust: int = 6
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


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    if not sensible_responses():
        return combos
    for scene_id, scene in SCENES.items():
        for plan_id, plan in PLANS.items():
            if compatible(scene, plan):
                combos.append((scene_id, plan_id))
    return combos


def explain_rejection(scene: Scene, plan: MischiefPlan) -> str:
    return (
        f"(No story: the {scene.title.lower()} scene needs a {scene.noise} sound, "
        f"but the plan '{plan.id}' makes a {plan.sound} sound. The mischief must at least sound like the adventure beat it is trying to fake.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a calmer electronics response such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "contained" if is_saved(RESPONSES[params.response], PLANS[params.plan], params.delay) else "broken"


KNOWLEDGE = {
    "camcorder": [
        (
            "What is a camcorder?",
            "A camcorder is a small camera that can record moving pictures and sound. It works best when you keep it dry and clean.",
        )
    ],
    "parfait": [
        (
            "What is a parfait?",
            "A parfait is a layered snack or dessert, often made with yogurt, fruit, and crunchy bits. Because it can drip or splat, it should stay away from electronics.",
        )
    ],
    "sound_effects": [
        (
            "What are sound effects?",
            "Sound effects are extra noises added to a story or movie to help it feel real. They can be silly or dramatic, but they should be made safely.",
        )
    ],
    "cleanup": [
        (
            "What should you do if sticky food lands on a camera?",
            "Tell a grown-up right away and stop using the camera. A grown-up can turn it off and clean it carefully so the mess does not get pushed deeper inside.",
        )
    ],
    "mischief": [
        (
            "What is mischief?",
            "Mischief is when someone does something a little naughty or playful, often without thinking about the trouble it could cause. Good choices mean stopping before the trouble grows.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    scene = f["scene"]
    plan = f["plan"]
    outcome = f["outcome"]
    base = (
        f'Write an adventure story for a 3-to-5-year-old that includes the words "camcorder", '
        f'"mischief", and "parfait", and uses playful sound effects.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle movie-making adventure where {a.id} wants to use a parfait for a {scene.noise} sound effect, but {b.id} stops the mischief before anything splashes the camcorder.",
            f"Write a story about children filming {scene.goal} and learning that safe sound effects are better than real sticky messes.",
        ]
    if outcome == "broken":
        return [
            base,
            f"Tell a cautionary adventure where {a.id} tries the '{plan.label}' idea, the parfait hits the camcorder, and the family learns an expensive lesson without anyone getting hurt.",
            f"Write a child-facing story about movie-making mischief that ends sadly for the camera but clearly teaches how to make sound effects safely.",
        ]
    return [
        base,
        f"Tell a lively adventure where {a.id} splashes parfait near a camcorder while trying to make a {scene.noise} sound effect, and a grown-up saves the day.",
        f"Write a story with onomatopoeia, a small mistake, and a happy ending where the children still finish their adventure film the safe way.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    scene = f["scene"]
    plan = f["plan"]
    response = f["response"]
    relation = f.get("relation", "friends")
    pair = pair_noun(a, b, relation)
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, who were making an adventure movie with a camcorder. Their snack, a berry parfait, became part of the trouble when one child mixed mischief with movie-making.",
        ),
        (
            "What kind of movie were they trying to film?",
            f"They were filming {scene.goal}. The scene needed a {scene.noise} sound effect to make the adventure feel real.",
        ),
        (
            f"What mischievous idea did {a.id} have?",
            f"{a.id} wanted to use the parfait as a sound effect by trying to {plan.action}. The idea seemed clever for one second, but it put sticky food right beside the camcorder.",
        ),
        (
            f"Why did {b.id} warn {a.id}?",
            f"{b.id} warned that the parfait could splash the camcorder and ruin the movie. The warning came from noticing that sticky dessert and camera buttons do not belong together.",
        ),
    ]
    outcome = f["outcome"]
    if outcome == "averted":
        qa.append(
            (
                f"What happened after {b.id} warned {a.id}?",
                f"{a.id} listened and stopped the mischief before the parfait touched the camcorder. Then they made the sound effect safely with {scene.safe_method}.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily and safely. The camcorder stayed clean, and the children finished their adventure with clever sound effects instead of a sticky shortcut.",
            )
        )
    elif outcome == "contained":
        qa.append(
            (
                f"How did {a.id}'s {pw} save the camcorder?",
                f"{pw.capitalize()} {response.qa_text}. Acting quickly mattered because the splash had happened, but the mess had not yet become too much for the camera.",
            )
        )
        qa.append(
            (
                "What did the children learn?",
                f"They learned that sound effects should be made safely and that snacks belong away from electronics. The ending shows the change because they still finished the adventure, but with a tool-based sound instead of parfait mischief.",
            )
        )
    else:
        qa.append(
            (
                "Was the camcorder all right in the end?",
                f"No. The parfait splash was too much, and the camcorder stopped working. Even so, everyone stayed safe, and the children learned to keep food far away from cameras.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended sadly for the camcorder but clearly for the lesson. They could still practice the adventure sounds with their voices and hands, which showed them there had been a safer way all along.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"camcorder", "parfait", "sound_effects", "mischief"}
    if world.facts["outcome"] != "averted":
        tags.add("cleanup")
    out: list[tuple[str, str]] = []
    order = ["camcorder", "parfait", "sound_effects", "cleanup", "mischief"]
    for tag in order:
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        scene="bog",
        plan="cup_wobble",
        response="battery_out_dry",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        scene="cave",
        plan="spoon_plop",
        response="power_off_blot",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Theo",
        cautioner_gender="boy",
        parent="father",
        trait="thoughtful",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=4,
    ),
    StoryParams(
        scene="monster",
        plan="scoop_fling",
        response="power_off_blot",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        parent="mother",
        trait="cautious",
        delay=2,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        trust=3,
    ),
]


ASP_RULES = r"""
compatible(S, P) :- scene(S), plan(P), needs_sound(S, N), makes_sound(P, N).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, P) :- compatible(S, P), sensible(_).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

severity(L + D) :- chosen_plan(P), spill_level(P, L), delay(D).
resp_power(PW) :- chosen_response(R), power(R, PW).
contained :- resp_power(PW), severity(SV), PW >= SV.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(broken) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SCENES.items():
        lines.append(asp.fact("scene", sid))
        lines.append(asp.fact("needs_sound", sid, s.sound))
    for pid, p in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("makes_sound", pid, p.sound))
        lines.append(asp.fact("spill_level", pid, p.level))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for t in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", t))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_plan", params.plan),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    py_sensible = {r.id for r in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(40):
        try:
            args = parser.parse_args([])
            p = resolve_params(args, random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving random seed {s}.")
            break

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a camcorder, a bit of mischief, a parfait, and safe sound effects."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.plan:
        scene = SCENES[args.scene]
        plan = PLANS[args.plan]
        if not compatible(scene, plan):
            raise StoryError(explain_rejection(scene, plan))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c
        for c in valid_combos()
        if (args.scene is None or c[0] == args.scene)
        and (args.plan is None or c[1] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene, plan = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    return StoryParams(
        scene=scene,
        plan=plan,
        response=response,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError(f"(Unknown scene '{params.scene}'.)")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan '{params.plan}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response '{params.response}'.)")
    scene = SCENES[params.scene]
    plan = PLANS[params.plan]
    response = RESPONSES[params.response]
    if not compatible(scene, plan):
        raise StoryError(explain_rejection(scene, plan))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        scene=scene,
        plan=plan,
        response=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        parent_type=params.parent,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        trust=params.trust,
    )
    world.facts["relation"] = params.relation
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (scene, plan) combos:\n")
        for scene, plan in combos:
            print(f"  {scene:10} {plan}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.instigator} & {p.cautioner}: {p.scene} with {p.plan} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    scene: Scene,
    plan: MischiefPlan,
    response: Response,
    *,
    instigator: str = "Max",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    trait: str = "careful",
    parent_type: str = "mother",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        traits=["bold"],
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    camcorder = world.add(Entity(
        id="camcorder",
        type="camcorder",
        label="camcorder",
        tags={"camcorder"},
    ))
    parfait = world.add(Entity(
        id="parfait",
        type="parfait",
        label="parfait",
        tags={"parfait"},
    ))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_caution(trait)

    world.facts["relation"] = relation
    world.facts["delay"] = delay

    play_setup(world, a, b, scene)
    need_sound(world, b, scene)

    world.para()
    tempt(world, a, plan)
    warn(world, b, a, plan, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, scene, parent)
        world.para()
        world.say(
            f"When they played back the clip, the camcorder caught the new sound perfectly. "
            f"{a.id} grinned and raised a thumb to {b.id}."
        )
        world.say(scene.ending_image)
        contained = True
        severity = 0
    else:
        defy(world, a, b, plan)
        world.para()
        splash(world, plan)
        alarm(world, b, parent)

        severity = spill_severity(plan, delay)
        camcorder.meters["severity"] = float(severity)
        contained = is_saved(response, plan, delay)

        world.para()
        if contained:
            rescue(world, parent, response, scene)
        else:
            rescue_fail(world, parent, response)
            sad_lesson(world, parent, a, b, scene)

    outcome = "averted" if averted else ("contained" if contained else "broken")
    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        camcorder=camcorder,
        parfait=parfait,
        scene=scene,
        plan=plan,
        response=response,
        outcome=outcome,
        severity=severity,
        splashed=camcorder.meters["saved"] >= THRESHOLD or camcorder.meters["damaged"] >= THRESHOLD,
        lesson=(a.memes["lesson"] >= THRESHOLD or b.memes["lesson"] >= THRESHOLD),
    )
    return world


SCENES = {
    "bog": Scene(
        id="bog",
        title="Bog Crossing",
        setup="a mossy lost valley",
        goal="the famous Bog Crossing",
        obstacle="the squishy bog bridge",
        sound="squish",
        noise="squish",
        safe_method="pressing a damp sponge in a metal bowl on the far table",
        ending_image="At the end, the explorers marched past the camcorder with dry hands, brave faces, and perfect swamp sounds behind them.",
        tags={"bog", "sound_effects", "adventure"},
    ),
    "cave": Scene(
        id="cave",
        title="Cave of Drops",
        setup="a lantern cave under a mountain",
        goal="the Cave of Drops",
        obstacle="the echoing drip room",
        sound="plop",
        noise="plop",
        safe_method="dropping smooth pebbles into a bucket across the room",
        ending_image="In the final shot, the cave team tiptoed under the blanket tunnel while soft plop sounds echoed safely from the far corner.",
        tags={"cave", "sound_effects", "adventure"},
    ),
    "monster": Scene(
        id="monster",
        title="Marsh Monster Chase",
        setup="a windy reed marsh",
        goal="the Marsh Monster Chase",
        obstacle="the monster's gooey footprint trail",
        sound="splat",
        noise="splat",
        safe_method="patting a folded towel and whispering the sound into the microphone from a safe distance",
        ending_image="Soon the camcorder captured a splendid chase scene, and the only splat in the room came from the silly sound crew far away from the snack table.",
        tags={"monster", "sound_effects", "adventure"},
    ),
    "cliff": Scene(
        id="cliff",
        title="Cliff Rope Walk",
        setup="a high rocky ledge",
        goal="the Cliff Rope Walk",
        obstacle="the roaring windy edge",
        sound="whoosh",
        noise="whoosh",
        safe_method="waving a paper fan near a blanket fort",
        ending_image="The rope walkers leaned into the pretend wind and laughed.",
        tags={"cliff", "sound_effects", "adventure"},
    ),
}

PLANS = {
    "cup_wobble": MischiefPlan(
        id="cup_wobble",
        label="wobble the cup",
        sound="squish",
        level=2,
        action="wobble the cup beside the lens",
        boom="SQUISH-SLOSH!",
        spill_text="The spoon clinked, the cup tipped, and yogurt slid over the rim.",
        tags={"mischief", "parfait", "sound_effects"},
    ),
    "spoon_plop": MischiefPlan(
        id="spoon_plop",
        label="drop a spoonful",
        sound="plop",
        level=1,
        action="lift one spoonful and let it fall right by the microphone",
        boom="PLOP!",
        spill_text="The spoonful missed the cup on the way down.",
        tags={"mischief", "parfait", "sound_effects"},
    ),
    "scoop_fling": MischiefPlan(
        id="scoop_fling",
        label="fling a scoop",
        sound="splat",
        level=2,
        action="flick one tiny scoop toward a paper plate by the microphone",
        boom="SPLAT!",
        spill_text="The berry swirl flew wider than anyone meant it to.",
        tags={"mischief", "parfait", "sound_effects"},
    ),
}

RESPONSES = {
    "power_off_blot": Response(
        id="power_off_blot",
        sense=3,
        power=3,
        text="switched the camcorder off at once, moved it away from the mess, and blotted every pink spot with a soft cloth",
        fail="switched the camcorder off and tried to blot it, but the sticky splash had already crept too far into the little buttons",
        qa_text="switched the camcorder off, moved it away from the mess, and blotted it with a soft cloth",
        tags={"camcorder", "cleanup"},
    ),
    "battery_out_dry": Response(
        id="battery_out_dry",
        sense=3,
        power=4,
        text="switched the camcorder off, took out the battery and card, and set the little parts on a towel to dry before cleaning the outside",
        fail="worked quickly to take out the battery and card, but the parfait had already worked its way inside",
        qa_text="switched it off, removed the battery and card, and dried the camera carefully",
        tags={"camcorder", "cleanup"},
    ),
    "wipe_while_on": Response(
        id="wipe_while_on",
        sense=1,
        power=1,
        text="rubbed at the mess while the camcorder was still on",
        fail="rubbed at the mess while the camcorder was still on, which only pushed the sticky spots around",
        qa_text="wiped the camcorder while it was still on",
        tags={"camcorder"},
    ),
    "shake_it": Response(
        id="shake_it",
        sense=1,
        power=1,
        text="shook the camcorder hard to get the drops out",
        fail="shook the camcorder hard, but that only made everything worse",
        qa_text="shook the camcorder to try to get the drops out",
        tags={"camcorder"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "cautious", "thoughtful", "sensible", "curious", "clever"]

if __name__ == "__main__":
    main()
