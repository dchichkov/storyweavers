#!/usr/bin/env python3

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
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0
BLOOD_THRESHOLD = 1.0
TRANSFORM_THRESHOLD = 2.0

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "witch"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

@dataclass
class Setting:
    place: str = "the dark forest"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)

@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    noun: str

@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"boy"})

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
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

def _r_blood_oozes(world: World) -> list[str]:
    for tree in [e for e in world.entities.values() if e.id == "hollow_tree"]:
        if tree.meters["blood"] >= BLOOD_THRESHOLD:
            sig = ("blood", tree.id)
            if sig not in world.fired:
                world.fired.add(sig)
                return [f"{tree.label.capitalize()} seeped dark red sap."]
    return []

def _r_transformation(world: World) -> list[str]:
    boy = next((e for e in world.entities.values() if e.type == "boy"), None)
    tree = next((e for e in world.entities.values() if e.id == "hollow_tree"), None)
    if not boy or not tree:
        return []
    if boy.meters["embedded_thorns"] >= TRANSFORM_THRESHOLD:
        sig = ("transform", boy.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        boy.label = "twisted creature"
        boy.phrase = "a gnarled guardian of thorns and sap"
        boy.traits.append("transformed")
        boy.memes["grief"] = 5.0
        return [
            "As the boy stepped through, the hollow blackness wrapped around him.",
            "His skin split and bark grew outward, clutching at his limbs.",
            "Tendrils of crimson sap dripped like tears from his new bark-bound face.",
            "The transformation was complete. He stood tall, but his essence was gone."
        ]
    return []

CAUSAL_RULES: list[Rule] = [
    Rule(name="blood_oozes", apply=_r_blood_oozes),
    Rule(name="transformation", apply=_r_transformation),
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
                produced.extend(s for s in sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced

def introduce_characters(world: World, boy_name: str = "Tomas") -> None:
    father = world.add(Entity(
        id="father", kind="character", type="man",
        label="father", traits=["kind", "wise"]
    ))
    tree = world.add(Entity(
        id="hollow_tree", kind="thing", type="tree",
        label="Hollow Tree", phrase="the ancient cursed Hollow Tree",
        meters={"blood": 0.0, "thorns_strength": 5.0}
    ))
    boy = world.add(Entity(
        id=boy_name, kind="character", type="boy",
        label="Tomas", traits=["young", "curious"],
        meters={"wounds": 0.0, "embedded_thorns": 0.0, "health": 10.0},
        memes={"curiosity": 0.0, "fear": 0.0, "defiance": 0.0, "grief": 0.0}
    ))
    pendant = world.add(Entity(
        id="pendant", kind="thing", type="pendant",
        label="pendant", phrase="a small wooden pendant",
        owner=boy.id, region="torso", plural=False,
        meters={"integrity": 5.0}
    ))
    world.say(f"In a small house at the edge of {world.setting.place} lived a boy named {boy_name} and his father.")
    world.say("The wind always carried unsettling whispers from the forest depths.")

def father_warns(world: World, boy: Entity) -> None:
    boy.memes["fear"] += 1.0
    world.say(
        f'"Do not ever approach the {world.get("hollow_tree").label}, child," '
        f"{world.get('father').pronoun()} said gravely. "
        '"Many have ventured inside... and none returned the same."'
    )
    world.facts["warning_given"] = True

def boy_cuts_tree(world: World, boy: Entity, tree: Entity) -> None:
    boy.memes["defiance"] += 1.0
    tree.meters["blood"] += 1.0
    world.say(
        f"{boy.id} swung {boy.pronoun('possessive')} axe into "
        f"{tree.label}. A thick reddish sap oozed where steel met wood."
    )
    propagate(world)

def boy_hears_whispers(world: World, boy: Entity) -> None:
    world.say(
        f'That night, {boy.id} dreamed of a voice calling from within the forest. '
        f'"Come see what you have awakened," it murmured in a chorus of cracks and wet leaves.'
    )
    boy.memes["fear"] += 0.5
    boy.memes["curiosity"] += 1.5

def boy_enters_tree(world: World, boy: Entity, tree: Entity) -> None:
    world.say(
        f'"Father warned against this," {boy.pronoun()} thought, but the pull was too strong.'
    )
    world.para()
    world.say(
        f"{boy.id} stepped into the yawning hollow of the cursed tree. "
        f"The moment {boy.pronoun()} crossed the threshold, thorns like needles tore into {boy.pronoun('object')}."
    )
    boy.meters["embedded_thorns"] += 1.0
    boy.meters["wounds"] += 2.0
    boy.memes["grief"] += 1.0
    if boy.meters["wounds"] >= TRANSFORM_THRESHOLD:
        propagate(world)

def find_transformed_son(world: World, father: Entity, son: Entity) -> None:
    world.para()
    world.say(
        f'Dawn came. Searching for {son.id}, the father ventured deep into '
        f"{world.setting.place} until {father.pronoun('possessive')} eyes fell upon a чудовище од bark and thorns."
    )
    world.say(f"The father recognized his son's eyes, wet with crimson dew, gazing back.")
    world.facts["transformation_complete"] = True

def tell_fable(boy_name: str = "Tomas") -> World:
    world = World(Setting(place="the dark forest at the edge of his village"))
    introduce_characters(world, boy_name)

    world.para()
    father_warns(world, world.entities["Tomas"])

    world.para()
    boy_cuts_tree(world, world.entities["Tomas"], world.entities["hollow_tree"])

    world.para()
    boy_hears_whispers(world, world.entities["Tomas"])

    world.para()
    boy_enters_tree(world, world.entities["Tomas"], world.entities["hollow_tree"])

    world.para()
    find_transformed_son(world, world.entities["father"], world.entities["Tomas"])

    world.facts.update(
        boy=world.entities["Tomas"],
        father=world.entities["father"],
        tree=world.entities["hollow_tree"],
        pendant=world.entities["pendant"],
        transformed=world.entities["Tomas"].traits.count("transformed") > 0,
        warnings=[world.entities["Tomas"].memes["fear"] >= 1.0],
        defiance=[world.entities["Tomas"].memes["defiance"] >= 1.0],
    )
    return world

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    boy = f["boy"]
    return [
        f'Write a gory fable in simple language for a child about a {boy.traits[-1] if "transformed" in boy.traits else "young"} boy who disobeys a warning and is turned into a twisted tree-creature.',
        "Include visceral details of bark splitting skin and red sap dripping like tears. End with the father finding the transformed son.",
        "Use short sentences and repetitive sounds (crack, drip, snap) to make it more like an oral telling."
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    boy = f["boy"]
    father = f["father"]
    tree = f["tree"]
    sub, obj, pos = boy.pronoun("subject"), boy.pronoun("object"), boy.pronoun("possessive")
    out: list[QAItem] = [
        QAItem(
            question=f"Who is the main character in this scary forest tale?",
            answer=f"It is {boy.id}, a {boy.traits[0]} {boy.type} with ever-growing {boy.memes['curiosity'] > 1.0 and 'curiosity' or 'a restless spirit'}."
        ),
        QAItem(
            question=f"What did the father warn {boy.id} never to do?",
            answer=f'"Do not ever approach the {tree.label}, child," {father.id} said. "Many have ventured inside... and none returned the same."'
        ),
    ]
    if f["defiance"][0]:
        out.append(QAItem(
            question=f"How did {boy.id} show they did not heed the warning?",
            answer=f"{boy.id} swung {pos} axe into the tree despite the warning, causing dark sap to ooze."
        ))
    if f["transformed"]:
        out.append(QAItem(
            question=f"What did the father find the next morning in the forest?",
            answer=f"The father found {sub} transformed into a twisted creature of thorns and dripping sap. {boy.id}'s human form was gone."
        ))
        out.append(QAItem(
            question=f"Why do we say curiosity without wisdom brings ruin?",
            answer="Because {boy.id}'s curiosity led him to disobey and enter the cursed tree, transforming him forever into something monstrous and sorrowful.".format(boy=boy)
        ))
    return out

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why is the color red important when describing gore?",
            answer="Red shows fresh blood, the body's life fluid, making the reading feel visceral and immediate, which helps children grasp danger through concrete images."
        ),
        QAItem(
            question="What does transformation mean in a story?",
            answer="Transformation means a character changes in a profound way—shape, nature, or essence—often showing the cost of their choices."
        ),
        QAItem(
            question="How can whispers foreshadow danger?",
            answer="Whispers carry voices that feel both inviting and warning. They hint at unseen forces that will soon act, making them perfect tools to signal oncoming peril."
        )
    ]

SETTINGS = {
    "village": Setting(place="village at the edge of Darkwood", indoor=False, affords={"chop", "explore"}),
}

TACTICS = {
    "chop": Activity(id="chop", verb="chop at", gerund="chopping at", noun="tree"),
    "explore": Activity(id="explore", verb="enter", gerund="entering", noun="forest"),
}

PRIZES = {
    "pendant": Prize(label="pendant", phrase="a small wooden pendant", type="pendant", region="torso", genders={"boy"}),
}

NAMES = ["Tomas", "Elias", "Adrian", "Jarek", "Lukas"]

@dataclass
class StoryParams:
    boy: str
    seed: Optional[int] = None

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: greed and transformation. Unspecified choices are picked at random."
    )
    ap.add_argument("--boy", type=str, default=None, help="Name of the boy protagonist")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible ASP combos")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity")
    ap.add_argument("--show-asp", action="store_true", help="print ASP program")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    boy = args.boy or rng.choice(NAMES)
    return StoryParams(boy=boy, seed=args.seed)

def generate(params: StoryParams) -> StorySample:
    world = tell_fable(params.boy)
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
        lines = ["--- world model state ---"]
        for e in sample.world.entities.values():
            m = {k: f"{v:.1f}" for k, v in e.meters.items() if v > 0}
            mem = {k: f"{v:.1f}" for k, v in e.memes.items() if v > 0}
            attrs = []
            if m:
                attrs.append(f"meters={m}")
            if mem:
                attrs.append(f"memes={mem}")
            lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(attrs)}")
        print("\n".join(lines))
    if qa:
        print()
        print("== (1) Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== (2) Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== (3) World knowledge questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")

ASP_RULES = r"""
% Fable: The hollow tree must be cut before transformation can occur
step(approach) :- activity(cut).
step(enter) :- step(approach), activity(enter).
transformed :- enter, boy, tree(B), blood(B), >0.
:- not transformed, enter.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = [
        asp.fact("setting", "village"),
        asp.fact("activity", "chop"),
        asp.fact("activity", "explore"),
        asp.fact("prize", "pendant"),
        asp.fact("worn_on", "pendant", "torso"),
    ]
    return "\n".join(lines)

def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    print("ASP verify stub: ensure inline rules align with causal logic")
    return 0

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show transformed/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed or random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(resolve_params(args, random.Random(base_seed + i))) for i in range(5)]
    else:
        for i in range(args.n):
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### Fable {i + 1}: The Boy and the Cursed Tree" if args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
