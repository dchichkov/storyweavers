#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tooth_primary_kerosene_transformation_problem_solving_heartwarming.py
================================================================================================

A standalone storyworld about a child in primary school who loses a loose tooth
during a storm-dark evening at home. Because the lights are out, a grown-up uses
a kerosene lamp carefully on the table. The child first feels upset when the
tiny tooth disappears into some household material, then a calm helper chooses a
reasonable way to find it. After the tooth is recovered, an ordinary little
container is transformed into a keepsake box, turning a problem into a warm new
memory.

The world model enforces one central constraint:

    the search method must match the material where the tooth was lost

A flour bowl is searched by sifting; rice or beans are poured onto a tray and
sorted; dough is pulled apart gently and the tooth is rinsed clean. The model
knows about silly methods like using a magnet, but refuses them because a tooth
is not metal.

The heartwarming "transformation" beat is physical and state-driven: once the
tooth is found, the family decorates a small container and it becomes the child's
first-tooth treasure box.

Run it
------
    python storyworlds/worlds/gpt-5.4/tooth_primary_kerosene_transformation_problem_solving_heartwarming.py
    python storyworlds/worlds/gpt-5.4/tooth_primary_kerosene_transformation_problem_solving_heartwarming.py --lost flour_bowl --method magnet
    python storyworlds/worlds/gpt-5.4/tooth_primary_kerosene_transformation_problem_solving_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/tooth_primary_kerosene_transformation_problem_solving_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/tooth_primary_kerosene_transformation_problem_solving_heartwarming.py --verify
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
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class LostPlace:
    id: str
    label: str
    phrase: str
    material: str
    detail: str
    method_ids: tuple[str, ...]
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    sense: int
    action: str
    clean_action: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Keepsake:
    id: str
    base_item: str
    decoration: str
    result_name: str
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
    tag: str
    apply: Callable[[World], list[str]]


def _r_search_success(world: World) -> list[str]:
    tooth = world.get("tooth")
    if tooth.attrs.get("state") != "revealed":
        return []
    sig = ("found", "tooth")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child = world.get("child")
    helper = world.get("helper")
    child.memes["relief"] += 1
    child.memes["hope"] += 1
    helper.memes["care"] += 1
    return []


def _r_box_transform(world: World) -> list[str]:
    box = world.get("box")
    tooth = world.get("tooth")
    if box.attrs.get("decorated") != "yes" or tooth.attrs.get("stored") != "yes":
        return []
    sig = ("transform", "box")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child = world.get("child")
    child.memes["joy"] += 1
    box.attrs["state"] = "treasure_box"
    return []


CAUSAL_RULES = [
    Rule(name="search_success", tag="problem", apply=_r_search_success),
    Rule(name="box_transform", tag="transformation", apply=_r_box_transform),
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
        for sent in produced:
            world.say(sent)
    return produced


def method_fits(lost: LostPlace, method: Method) -> bool:
    return method.id in lost.method_ids and method.sense >= SENSE_MIN


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def explain_rejection(lost: LostPlace, method: Method) -> str:
    if method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method.id}': it scores too low on common sense "
            f"(sense={method.sense} < {SENSE_MIN}). Teeth are not metal, so a "
            f"magnet will not help. Pick a real search method like "
            f"{', '.join(sorted(lost.method_ids))}.)"
        )
    return (
        f"(No story: {method.id} does not fit {lost.phrase}. The tooth is in "
        f"{lost.material}, so the helper needs a method that really works there: "
        f"{', '.join(sorted(lost.method_ids))}.)"
    )


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for lost_id, lost in LOST_PLACES.items():
        for method_id, method in METHODS.items():
            if method_fits(lost, method):
                combos.append((lost_id, method_id))
    return combos


def predict_find(world: World, lost_id: str, method_id: str) -> dict:
    sim = world.copy()
    lost = LOST_PLACES[lost_id]
    method = METHODS[method_id]
    _do_search(sim, lost, method, narrate=False)
    tooth = sim.get("tooth")
    return {
        "found": tooth.attrs.get("state") == "revealed",
        "clean": tooth.attrs.get("clean") == "yes",
    }


def _do_search(world: World, lost: LostPlace, method: Method, narrate: bool = True) -> None:
    tooth = world.get("tooth")
    if method_fits(lost, method):
        tooth.attrs["state"] = "revealed"
        tooth.attrs["clean"] = "yes"
        tooth.attrs["material"] = lost.material
        propagate(world, narrate=narrate)


def introduce(world: World, child: Entity, helper: Entity, school_name: str) -> None:
    child.memes["pride"] += 1
    world.say(
        f"{child.id} was in primary school, and that week {child.pronoun()} could not stop "
        f"touching the loose tooth at the front of {child.pronoun('possessive')} smile."
    )
    world.say(
        f"The next morning, {school_name} was having a class photograph, and {child.id} hoped "
        f"the tooth would stay put just a little longer."
    )
    world.say(
        f"That evening, rain drummed on the roof while {helper.label_word} worked beside "
        f"{child.pronoun('object')} at the kitchen table."
    )


def blackout(world: World, helper: Entity) -> None:
    lamp = world.get("lamp")
    lamp.meters["lit"] += 1
    world.say(
        "Then the lights went out with a soft click, and the room turned blue and shadowy."
    )
    world.say(
        f"{helper.label_word.capitalize()} set a kerosene lamp in the middle of the table, "
        f"well away from small hands, and its steady glow warmed the dark."
    )


def activity_setup(world: World, child: Entity, lost: LostPlace) -> None:
    world.say(
        f"{child.id} leaned close over {lost.phrase}, listening to the rain and trying to be helpful."
    )


def lose_tooth(world: World, child: Entity, lost: LostPlace) -> None:
    tooth = world.get("tooth")
    tooth.attrs["state"] = "lost"
    tooth.attrs["place"] = lost.id
    child.memes["worry"] += 1
    world.say(
        f"All at once, the loose tooth gave a tiny tick. {child.id} gasped, pressed a hand to "
        f"{child.pronoun('possessive')} mouth, and then stared."
    )
    world.say(
        f'"My tooth!" {child.pronoun()} whispered. It had fallen right into {lost.phrase}.'
    )
    world.say(
        f"For a moment, {child.id} looked ready to cry. The tooth was so small, and {lost.detail}."
    )


def worry_beat(world: World, child: Entity, helper: Entity, school_name: str) -> None:
    world.say(
        f'"What if I never find it?" {child.id} asked. "It was my first big primary-school tooth, '
        f'and I wanted to show the little gap in the picture at {school_name}."'
    )
    world.say(
        f'{helper.label_word.capitalize()} touched {child.pronoun("possessive")} shoulder. '
        f'"We will not poke and panic," {helper.pronoun()} said. "We will think."'
    )


def choose_method(world: World, child: Entity, helper: Entity, lost: LostPlace, method: Method) -> None:
    pred = predict_find(world, lost.id, method.id)
    world.facts["predicted_found"] = pred["found"]
    helper.memes["care"] += 1
    world.say(
        f'{helper.label_word.capitalize()} studied {lost.phrase} in the kerosene glow. '
        f'"A tooth is tiny, but it is real," {helper.pronoun()} said. '
        f'"{method.action.capitalize()}."'
    )


def search(world: World, child: Entity, helper: Entity, lost: LostPlace, method: Method) -> None:
    _do_search(world, lost, method, narrate=False)
    tooth = world.get("tooth")
    if tooth.attrs.get("state") == "revealed":
        world.say(method.action.capitalize() + ".")
        world.say(
            f"Soon {helper.label_word} found the little white tooth and lifted it into the light."
        )
        if method.clean_action:
            world.say(method.clean_action)
        world.say(
            f"{child.id}'s shoulders dropped, and a shaky smile came back to {child.pronoun('possessive')} face."
        )


def transform_box(world: World, child: Entity, helper: Entity, keepsake: Keepsake) -> None:
    box = world.get("box")
    tooth = world.get("tooth")
    box.attrs["decorated"] = "yes"
    box.attrs["kind"] = keepsake.base_item
    box.attrs["result_name"] = keepsake.result_name
    tooth.attrs["stored"] = "yes"
    tooth.owner = child.id
    propagate(world, narrate=False)
    world.say(
        f'"A first tooth should have a home," {helper.label_word} said.'
    )
    world.say(
        f"Together they took {keepsake.base_item} and {keepsake.decoration}, and by the time they were done "
        f"it had become {keepsake.result_name}."
    )
    world.say(
        f"{child.id} set the tooth inside as carefully as a pearl."
    )


def ending(world: World, child: Entity, helper: Entity, school_name: str) -> None:
    box = world.get("box")
    world.say(
        f"When the rain finally softened, {child.id} tucked {box.attrs.get('result_name', 'the little box')} "
        f"beside the bed."
    )
    world.say(
        f'"Now tomorrow\'s picture can show two new things," {helper.label_word} whispered. '
        f'"Your brave gap and the way you solved a hard problem."'
    )
    world.say(
        f"{child.id} grinned into the dim room, proud of the missing tooth and the small transformed treasure "
        f"glowing in the kerosene lamplight from across the room."
    )


def tell(
    *,
    child_name: str,
    child_gender: str,
    helper_type: str,
    school_name: str,
    lost: LostPlace,
    method: Method,
    keepsake: Keepsake,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            label=child_name,
            traits=["gentle", "hopeful"],
            attrs={"school": school_name},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label="the helper",
        )
    )
    world.add(
        Entity(
            id="tooth",
            kind="thing",
            type="tooth",
            label="tooth",
            phrase="a small white tooth",
            attrs={"state": "loose", "clean": "no", "stored": "no"},
            tags={"tooth"},
        )
    )
    world.add(
        Entity(
            id="lamp",
            kind="thing",
            type="lamp",
            label="kerosene lamp",
            phrase="a kerosene lamp",
            attrs={"fuel": "kerosene", "placed": "table_center"},
            tags={"kerosene", "lamp"},
        )
    )
    world.add(
        Entity(
            id="box",
            kind="thing",
            type="container",
            label="little container",
            attrs={"decorated": "no", "state": "plain"},
        )
    )

    introduce(world, child, helper, school_name)
    activity_setup(world, child, lost)

    world.para()
    blackout(world, helper)
    lose_tooth(world, child, lost)
    worry_beat(world, child, helper, school_name)

    world.para()
    choose_method(world, child, helper, lost, method)
    search(world, child, helper, lost, method)

    world.para()
    transform_box(world, child, helper, keepsake)
    ending(world, child, helper, school_name)

    world.facts.update(
        child=child,
        helper=helper,
        lost=lost,
        method=method,
        keepsake=keepsake,
        school_name=school_name,
        found=world.get("tooth").attrs.get("state") == "revealed",
        transformed=world.get("box").attrs.get("state") == "treasure_box",
        tooth_saved=world.get("tooth").attrs.get("stored") == "yes",
    )
    return world


LOST_PLACES = {
    "flour_bowl": LostPlace(
        id="flour_bowl",
        label="flour bowl",
        phrase="a wide bowl of flour for flatbread",
        material="flour",
        detail="the flour had already puffed over everything like pale dust",
        method_ids=("sift",),
        tags={"flour"},
    ),
    "rice_jar": LostPlace(
        id="rice_jar",
        label="rice jar",
        phrase="a big jar of rice",
        material="rice",
        detail="the grains all looked white and shiny in the dim light",
        method_ids=("tray_sort",),
        tags={"rice"},
    ),
    "bean_basket": LostPlace(
        id="bean_basket",
        label="bean basket",
        phrase="a basket of dry beans",
        material="beans",
        detail="the beans bumped and rolled whenever anyone breathed near them",
        method_ids=("tray_sort",),
        tags={"beans"},
    ),
    "dough_bowl": LostPlace(
        id="dough_bowl",
        label="dough bowl",
        phrase="a bowl of soft bread dough",
        material="dough",
        detail="the dough was sticky and folded over on itself",
        method_ids=("pull_apart",),
        tags={"dough"},
    ),
}

METHODS = {
    "sift": Method(
        id="sift",
        sense=3,
        action="we will shake the flour through a sieve, slowly and gently",
        clean_action="The helper rinsed the tooth in a cup of clean water and dried it on a cloth.",
        qa_text="They sifted the flour through a sieve until the tooth appeared.",
        tags={"sieve", "problem_solving"},
    ),
    "tray_sort": Method(
        id="tray_sort",
        sense=3,
        action="we will pour it onto a tray and look together, one little piece at a time",
        clean_action="The helper wiped the tooth clean with a damp cloth.",
        qa_text="They spread everything on a tray and sorted carefully until they saw the tooth.",
        tags={"sorting", "problem_solving"},
    ),
    "pull_apart": Method(
        id="pull_apart",
        sense=3,
        action="we will pull the dough apart with clean fingers, then rinse the tooth",
        clean_action="The helper washed the tooth in clean water and set it on a dry spoon.",
        qa_text="They pulled the dough apart gently and rinsed the tooth clean.",
        tags={"dough", "problem_solving"},
    ),
    "magnet": Method(
        id="magnet",
        sense=1,
        action="we will wave a magnet over it",
        clean_action="",
        qa_text="They tried a magnet.",
        tags={"magnet"},
    ),
}

KEEPSAKES = {
    "star_box": Keepsake(
        id="star_box",
        base_item="an empty matchbox",
        decoration="blue paper and tiny silver stars",
        result_name="a star box for the first tooth",
        tags={"box", "transformation"},
    ),
    "seed_tin": Keepsake(
        id="seed_tin",
        base_item="a little tea tin",
        decoration="a ribbon and a round paper moon",
        result_name="a moon tin for the first tooth",
        tags={"tin", "transformation"},
    ),
    "cloth_pouch": Keepsake(
        id="cloth_pouch",
        base_item="a scrap of soft cloth",
        decoration="yellow thread and one neat button",
        result_name="a tiny tooth pouch",
        tags={"pouch", "transformation"},
    ),
}

SCHOOL_NAMES = [
    "Maple Primary",
    "Riverbank Primary",
    "Sunhill Primary",
    "Oak Lane Primary",
]

GIRL_NAMES = ["Lila", "Mia", "Nora", "Ava", "Ella", "Ruby", "Zoe"]
BOY_NAMES = ["Leo", "Ben", "Sam", "Noah", "Eli", "Theo", "Max"]


@dataclass
class StoryParams:
    lost: str
    method: str
    keepsake: str
    child_name: str
    child_gender: str
    helper_type: str
    school_name: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "tooth": [
        (
            "What is a primary tooth?",
            "A primary tooth is one of the first teeth children grow when they are small. Later it gets loose and falls out so a grown-up tooth can come in."
        )
    ],
    "kerosene": [
        (
            "What is kerosene?",
            "Kerosene is a fuel some lamps use to make light. Only grown-ups should handle it because fuel and flames can be dangerous."
        )
    ],
    "lamp": [
        (
            "Why should a kerosene lamp stay away from children’s hands?",
            "A kerosene lamp has fuel and a flame, so it can burn skin or tip over if someone bumps it. That is why a grown-up should place it safely and watch it."
        )
    ],
    "sieve": [
        (
            "What does a sieve do?",
            "A sieve lets tiny powder fall through small holes while bigger things stay behind. That makes it helpful for finding a little object in flour."
        )
    ],
    "sorting": [
        (
            "Why is sorting one piece at a time a good way to find something small?",
            "Looking carefully at a few pieces at a time helps your eyes notice what is different. Slow sorting is often better than grabbing in a rush."
        )
    ],
    "transformation": [
        (
            "What does transformation mean in a story?",
            "Transformation means something changes into a new form or purpose. In this storyworld, an ordinary item becomes a special tooth keepsake."
        )
    ],
    "problem_solving": [
        (
            "What is problem solving?",
            "Problem solving means stopping to think about what kind of problem you have and choosing a step that fits. Good problem solving is calm, careful, and smart."
        )
    ],
}
KNOWLEDGE_ORDER = ["tooth", "kerosene", "lamp", "sieve", "sorting", "transformation", "problem_solving"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    lost = f["lost"]
    keepsake = f["keepsake"]
    school_name = f["school_name"]
    return [
        (
            f'Write a heartwarming story for a 3-to-5-year-old that uses the words '
            f'"tooth", "primary", and "kerosene" and includes transformation and problem solving.'
        ),
        (
            f"Tell a gentle story where a child in primary school loses a loose tooth in {lost.phrase} "
            f"during a blackout, and a caring grown-up solves the problem calmly."
        ),
        (
            f"Write a cozy story that ends with {keepsake.base_item} being transformed into "
            f"{keepsake.result_name} before the next day's school picture at {school_name}."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    lost = f["lost"]
    method = f["method"]
    keepsake = f["keepsake"]
    school_name = f["school_name"]
    hw = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child in primary school, and {hw} who helped when a loose tooth disappeared. The story follows how they turned a small worry into a warm memory."
        ),
        (
            "Why was the child worried about the tooth?",
            f"{child.id} was worried because the tooth fell into {lost.phrase} and seemed almost impossible to see. {child.pronoun().capitalize()} also cared about the gap because the class picture at {school_name} was the next morning."
        ),
        (
            "Why is the word kerosene in the story?",
            f"The room was dark after the power went out, so {hw} lit a kerosene lamp and kept it safely in the middle of the table. Its steady light helped them slow down and solve the problem carefully."
        ),
        (
            f"How did {hw} solve the problem?",
            f"{method.qa_text} The helper chose that method because the tooth was hidden in {lost.material}, so the search had to match the material instead of being random."
        ),
        (
            "What was transformed in the story?",
            f"{keepsake.base_item.capitalize()} was decorated with {keepsake.decoration} until it became {keepsake.result_name}. That transformation gave the found tooth a safe home and changed the scary moment into something special."
        ),
        (
            "How did the story end?",
            f"It ended with {child.id} feeling proud instead of upset. The missing tooth was found, stored safely, and the child went to bed ready for the primary-school picture with a brave smile."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"tooth", "kerosene", "lamp", "transformation", "problem_solving"}
    tags |= set(f["method"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        lost="flour_bowl",
        method="sift",
        keepsake="star_box",
        child_name="Lila",
        child_gender="girl",
        helper_type="grandmother",
        school_name="Maple Primary",
    ),
    StoryParams(
        lost="rice_jar",
        method="tray_sort",
        keepsake="seed_tin",
        child_name="Leo",
        child_gender="boy",
        helper_type="mother",
        school_name="Riverbank Primary",
    ),
    StoryParams(
        lost="bean_basket",
        method="tray_sort",
        keepsake="cloth_pouch",
        child_name="Nora",
        child_gender="girl",
        helper_type="father",
        school_name="Oak Lane Primary",
    ),
    StoryParams(
        lost="dough_bowl",
        method="pull_apart",
        keepsake="star_box",
        child_name="Theo",
        child_gender="boy",
        helper_type="grandmother",
        school_name="Sunhill Primary",
    ),
]


ASP_RULES = r"""
sensible_method(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
fits(L, M) :- lost_place(L), method(M), suitable(L, M), sensible_method(M).
valid(L, M) :- fits(L, M).

chosen_valid :- chosen_lost(L), chosen_method(M), fits(L, M).
found :- chosen_valid.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for lost_id, lost in LOST_PLACES.items():
        lines.append(asp.fact("lost_place", lost_id))
        lines.append(asp.fact("material", lost_id, lost.material))
        for method_id in lost.method_ids:
            lines.append(asp.fact("suitable", lost_id, method_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_found(params: StoryParams) -> bool:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_lost", params.lost),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show found/0."))
    return bool(asp.atoms(model, "found"))


def _validate_params(params: StoryParams) -> None:
    if params.lost not in LOST_PLACES:
        raise StoryError(f"(Unknown lost place: {params.lost})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.keepsake not in KEEPSAKES:
        raise StoryError(f"(Unknown keepsake: {params.keepsake})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown child gender: {params.child_gender})")
    if params.helper_type not in {"mother", "father", "grandmother", "grandfather"}:
        raise StoryError(f"(Unknown helper type: {params.helper_type})")
    lost = LOST_PLACES[params.lost]
    method = METHODS[params.method]
    if not method_fits(lost, method):
        raise StoryError(explain_rejection(lost, method))


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    for params in CURATED:
        py = params.method in LOST_PLACES[params.lost].method_ids and METHODS[params.method].sense >= SENSE_MIN
        cl = asp_found(params)
        if py != cl:
            rc = 1
            print(f"MISMATCH in found outcome for curated params: {params}")
            break
    else:
        print(f"OK: found outcome matches on {len(CURATED)} curated scenarios.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world: a loose tooth, a blackout, a careful search, and a transformed keepsake."
    )
    ap.add_argument("--lost", choices=LOST_PLACES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--school-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible (lost, method) pairs derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.lost and args.method:
        lost = LOST_PLACES[args.lost]
        method = METHODS[args.method]
        if not method_fits(lost, method):
            raise StoryError(explain_rejection(lost, method))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        lost = LOST_PLACES[args.lost] if args.lost else next(iter(LOST_PLACES.values()))
        raise StoryError(explain_rejection(lost, METHODS[args.method]))

    combos = [
        combo for combo in valid_combos()
        if (args.lost is None or combo[0] == args.lost)
        and (args.method is None or combo[1] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    lost_id, method_id = rng.choice(sorted(combos))
    keepsake_id = args.keepsake or rng.choice(sorted(KEEPSAKES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_type = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])
    school_name = args.school_name or rng.choice(SCHOOL_NAMES)

    return StoryParams(
        lost=lost_id,
        method=method_id,
        keepsake=keepsake_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_type=helper_type,
        school_name=school_name,
    )


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper_type,
        school_name=params.school_name,
        lost=LOST_PLACES[params.lost],
        method=METHODS[params.method],
        keepsake=KEEPSAKES[params.keepsake],
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
        print(asp_program("", "#show valid/2.\n#show found/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (lost, method) pairs:\n")
        for lost, method in combos:
            print(f"  {lost:12} {method}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.lost} -> {p.method} -> {p.keepsake}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
