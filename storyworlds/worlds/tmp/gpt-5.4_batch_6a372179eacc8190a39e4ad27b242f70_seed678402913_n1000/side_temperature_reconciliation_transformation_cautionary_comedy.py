#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/side_temperature_reconciliation_transformation_cautionary_comedy.py
================================================================================================

A standalone storyworld about two children cooking something in a pan and
learning, with a little comedy, that heat changes food slowly and that hot pans
must be treated carefully.

This world rebuilds a simple shape:

- premise: two children are hungry and excited to cook together
- tension: one child wants to rush, misreads the temperature, and starts a silly
  argument about which side is "done"
- transformation: batter or dough changes into a cooked treat in the pan
- cautionary turn: a too-hot pan or careless grab creates a small kitchen scare
- reconciliation: the children apologize, listen, and finish the snack safely
- ending image: they share food at the table, noticing the warm side and cool side

The model is intentionally narrow. It prefers a few plausible stories over many
thin combinations.

Run it
------
    python storyworlds/worlds/gpt-5.4/side_temperature_reconciliation_transformation_cautionary_comedy.py
    python storyworlds/worlds/gpt-5.4/side_temperature_reconciliation_transformation_cautionary_comedy.py --food pancake --heat medium
    python storyworlds/worlds/gpt-5.4/side_temperature_reconciliation_transformation_cautionary_comedy.py --heat high --tool fingers
    python storyworlds/worlds/gpt-5.4/side_temperature_reconciliation_transformation_cautionary_comedy.py --all
    python storyworlds/worlds/gpt-5.4/side_temperature_reconciliation_transformation_cautionary_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/side_temperature_reconciliation_transformation_cautionary_comedy.py --json
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
class Food:
    id: str
    raw_name: str
    cooked_name: str
    vessel: str
    batter_word: str
    scent: str
    flip_word: str
    shape_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Heat:
    id: str
    pan_temp: str
    level_word: str
    speed: int
    risk: int
    first_side: str
    second_side: str
    caution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    safe: bool
    sense: int
    style: str
    rescue_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    food: str
    heat: str
    tool: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str
    relation: str
    impatient_trait: str
    careful_trait: str
    seed: Optional[int] = None


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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"impatient", "careful"}]

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


def _r_heat_changes_food(world: World) -> list[str]:
    out: list[str] = []
    pan = world.get("pan")
    food = world.get("food")
    if pan.meters["heating"] < THRESHOLD:
        return out
    for side in ("first", "second"):
        if food.meters[f"{side}_raw"] >= THRESHOLD and food.meters[f"{side}_cook_pending"] >= THRESHOLD:
            sig = ("cook", side)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            food.meters[f"{side}_raw"] = 0.0
            food.meters[f"{side}_golden"] += 1
            if side == "first":
                food.meters["transformed"] += 1
            out.append("__cook__")
    return out


def _r_overheat_burns(world: World) -> list[str]:
    out: list[str] = []
    pan = world.get("pan")
    food = world.get("food")
    if pan.meters["too_hot"] < THRESHOLD and pan.meters["scorching"] < THRESHOLD:
        return out
    for side in ("first", "second"):
        if food.meters[f"{side}_golden"] < THRESHOLD:
            continue
        if food.meters["waited_too_long"] < THRESHOLD:
            continue
        sig = ("burn", side)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        food.meters[f"{side}_burned"] += 1
        out.append("__burn__")
    return out


def _r_hot_pan_scares(world: World) -> list[str]:
    pan = world.get("pan")
    impatient = world.facts.get("impatient")
    if impatient is None:
        return []
    if impatient.meters["touched_hot_handle"] < THRESHOLD:
        return []
    sig = ("scare", impatient.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    impatient.memes["fear"] += 1
    impatient.memes["embarrassment"] += 1
    world.get("careful").memes["fear"] += 1
    return ["__scare__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="heat_changes_food", tag="physical", apply=_r_heat_changes_food),
    Rule(name="overheat_burns", tag="physical", apply=_r_overheat_burns),
    Rule(name="hot_pan_scares", tag="social", apply=_r_hot_pan_scares),
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


FOODS = {
    "pancake": Food(
        id="pancake",
        raw_name="pancake batter",
        cooked_name="pancake",
        vessel="pan",
        batter_word="batter",
        scent="sweet and buttery",
        flip_word="flip",
        shape_word="round moon",
        tags={"pancake", "pan", "share"},
    ),
    "fritter": Food(
        id="fritter",
        raw_name="apple fritter batter",
        cooked_name="apple fritter",
        vessel="skillet",
        batter_word="spoonfuls of batter",
        scent="warm apple and cinnamon",
        flip_word="turn",
        shape_word="little lumpy cloud",
        tags={"fritter", "pan", "share", "apple"},
    ),
    "flatbread": Food(
        id="flatbread",
        raw_name="soft dough",
        cooked_name="flatbread",
        vessel="griddle",
        batter_word="soft dough",
        scent="toasty and warm",
        flip_word="turn",
        shape_word="small puffy circle",
        tags={"bread", "pan", "share"},
    ),
}

HEATS = {
    "low": Heat(
        id="low",
        pan_temp="warm",
        level_word="low",
        speed=1,
        risk=0,
        first_side="pale with tiny bubbles",
        second_side="soft and light",
        caution="The pan was warm, but still not a toy.",
        tags={"temperature", "warm"},
    ),
    "medium": Heat(
        id="medium",
        pan_temp="hot",
        level_word="medium",
        speed=2,
        risk=1,
        first_side="golden with neat little bubbles",
        second_side="toasty and ready",
        caution="The pan was hot enough to cook, so hands had to stay back.",
        tags={"temperature", "hot"},
    ),
    "high": Heat(
        id="high",
        pan_temp="very hot",
        level_word="high",
        speed=3,
        risk=2,
        first_side="brown at the edges before anyone could blink",
        second_side="dark fast if nobody watched",
        caution="The pan was very hot, which meant quick cooking and quick mistakes.",
        tags={"temperature", "hot", "burn"},
    ),
}

TOOLS = {
    "spatula": Tool(
        id="spatula",
        label="spatula",
        phrase="a flat blue spatula",
        safe=True,
        sense=3,
        style="slid it right under the food",
        rescue_text="used the spatula to move the food and keep small hands away from the handle",
        qa_text="used a spatula to keep the hot pan and the hot food at a safe distance",
        tags={"spatula", "safe_tool"},
    ),
    "tongs": Tool(
        id="tongs",
        label="tongs",
        phrase="a pair of springy tongs",
        safe=True,
        sense=2,
        style="clicked the tongs twice like a silly crab",
        rescue_text="used the tongs to steady the pan and nudge the food into the middle",
        qa_text="used tongs to handle the hot cooking safely",
        tags={"tongs", "safe_tool"},
    ),
    "fingers": Tool(
        id="fingers",
        label="fingers",
        phrase="bare fingers",
        safe=False,
        sense=0,
        style="reached in with bare fingers",
        rescue_text="pulled the hand back at once and reached for a real kitchen tool instead",
        qa_text="learned that bare fingers should never be used on hot cookware",
        tags={"unsafe", "hands"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Ruby"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Eli"]
IMPATIENT_TRAITS = ["hungry", "bouncy", "hasty", "silly", "wriggly"]
CAREFUL_TRAITS = ["careful", "steady", "thoughtful", "patient", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for food_id in FOODS:
        for heat_id in HEATS:
            for tool_id, tool in TOOLS.items():
                if tool.sense >= SENSE_MIN or heat_id == "high":
                    combos.append((food_id, heat_id, tool_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    heat = HEATS[params.heat]
    tool = TOOLS[params.tool]
    if not tool.safe and heat.risk < 2:
        return "rejected"
    if heat.id == "high" and not tool.safe:
        return "scared"
    if heat.id == "high":
        return "singed"
    return "golden"


def explain_tool(tool: Tool, heat: Heat) -> str:
    if not tool.safe and heat.risk < 2:
        return (
            f"(No story: using {tool.label} with a {heat.pan_temp} pan would be pure foolishness "
            f"with no sensible fix. Pick a real kitchen tool like spatula or tongs.)"
        )
    return ""


def predict_touch(world: World, heat: Heat, tool: Tool) -> dict:
    sim = world.copy()
    pan = sim.get("pan")
    impatient = sim.get("impatient")
    if heat.risk >= 2 and not tool.safe:
        impatient.meters["touched_hot_handle"] += 1
        pan.meters["too_hot"] += 1
    propagate(sim, narrate=False)
    return {
        "scare": impatient.memes["fear"] >= THRESHOLD,
        "too_hot": pan.meters["too_hot"] >= THRESHOLD,
    }


def introduce(world: World, a: Entity, b: Entity, parent: Entity, food: Food) -> None:
    world.say(
        f"One hungry afternoon, {a.id} and {b.id} stood on stools beside the kitchen counter, "
        f"ready to help {a.pronoun('possessive')} {parent.label_word} make {food.cooked_name}."
    )
    world.say(
        f"The bowl held {food.raw_name}, and the shiny {food.vessel} waited on the stove like it knew a joke was coming."
    )


def set_heat(world: World, heat: Heat) -> None:
    pan = world.get("pan")
    pan.meters["heating"] += 1
    if heat.risk >= 1:
        pan.meters["hot"] += 1
    if heat.risk >= 2:
        pan.meters["too_hot"] += 1
        pan.meters["scorching"] += 1
    world.say(
        f"The burner was set to {heat.level_word}, so the {food_vessel(world)} grew {heat.pan_temp}. {heat.caution}"
    )


def food_vessel(world: World) -> str:
    return world.facts["food_cfg"].vessel


def pour(world: World, impatient: Entity, careful: Entity, food: Food) -> None:
    world.get("food").meters["first_raw"] += 1
    world.get("food").meters["second_raw"] += 1
    impatient.memes["joy"] += 1
    careful.memes["joy"] += 1
    world.say(
        f"{impatient.id} helped pour the {food.batter_word} into the {food.vessel}, and it spread into {food.shape_word}."
    )
    world.say(
        f'Soon it smelled {food.scent}, and both children leaned in as if smelling harder would make lunch come faster.'
    )


def argue_about_side(world: World, impatient: Entity, careful: Entity, food: Food, heat: Heat) -> None:
    impatient.memes["defiance"] += 1
    careful.memes["caution"] += 1
    world.say(
        f'After a little sizzle, {impatient.id} pointed and declared, "That side is done already!"'
    )
    world.say(
        f'{careful.id} shook {careful.pronoun("possessive")} head. "Only one side can look ready while the middle is still at the wrong temperature," {careful.pronoun()} said.'
    )
    world.say(
        f'Now they had a very serious argument about whether "golden" meant "done" or only "done on one side." It would have been grand court business if it had not been about lunch.'
    )
    world.facts["argument_happened"] = True
    world.facts["temperature_word_used"] = True


def try_early_flip(world: World, impatient: Entity, food: Food, heat: Heat) -> None:
    food_ent = world.get("food")
    food_ent.meters["first_side_cook_pending"] = 1.0
    food_ent.meters["first_cook_pending"] = 1.0
    propagate(world, narrate=False)
    first_ready = heat.speed >= 2
    if first_ready:
        food_ent.meters["first_golden"] += 1
        food_ent.meters["transformed"] += 1
        world.say(
            f"When {impatient.id} peeped underneath, the first side looked {heat.first_side}. That made {impatient.pronoun('object')} even more sure."
        )
    else:
        world.say(
            f"When {impatient.id} peeped underneath, the first side was still pale. Even {impatient.pronoun()} had to admit it needed more time."
        )
    world.facts["first_side_ready"] = first_ready


def careful_warning(world: World, careful: Entity, parent: Entity, heat: Heat, tool: Tool) -> None:
    pred = predict_touch(world, heat, tool)
    world.facts["predicted_scare"] = pred["scare"]
    extra = " and too hot for fingers" if pred["too_hot"] else ""
    world.say(
        f'{careful.id} looked from the pan to {impatient_name(world)} and whispered, "The handle is {heat.pan_temp}{extra}. We should use a tool and listen to {parent.label_word}."'
    )


def impatient_name(world: World) -> str:
    return world.get("impatient").id


def grab_or_tool(world: World, impatient: Entity, parent: Entity, heat: Heat, tool: Tool) -> None:
    pan = world.get("pan")
    if tool.safe:
        world.say(
            f'{parent.label_word.capitalize()} handed {impatient.id} {tool.phrase}. {impatient.id} {tool.style}, trying very hard to look like a famous breakfast chef.'
        )
        world.facts["touch_scare"] = False
        return
    impatient.meters["touched_hot_handle"] += 1
    propagate(world, narrate=False)
    world.say(
        f'But {impatient.id}, feeling dramatic and very hungry, {tool.style} toward the hot handle.'
    )
    world.say(
        f'"Oop!" {impatient.pronoun().capitalize()} yelped and snatched {impatient.pronoun("possessive")} hand back before holding on.'
    )
    world.facts["touch_scare"] = True


def parent_steps_in(world: World, parent: Entity, tool: Tool) -> None:
    for kid in world.kids():
        kid.memes["relief"] += 1
    world.say(
        f'{parent.label_word.capitalize()} moved quickly, {tool.rescue_text}, and made the stove seem boring again, which was exactly the right kind of magic.'
    )


def finish_cooking(world: World, impatient: Entity, careful: Entity, food: Food, heat: Heat, tool: Tool) -> None:
    food_ent = world.get("food")
    food_ent.meters["first_golden"] = max(food_ent.meters["first_golden"], 1.0)
    food_ent.meters["transformed"] = max(food_ent.meters["transformed"], 1.0)
    food_ent.meters["second_cook_pending"] = 1.0
    if heat.id == "high":
        food_ent.meters["waited_too_long"] += 1
        food_ent.meters["second_golden"] += 1
        food_ent.meters["second_burned"] += 1
        world.say(
            f'With the heat so high, the other side cooked fast. It smelled delicious for one second and a little too dark the next.'
        )
    else:
        food_ent.meters["second_golden"] += 1
        world.say(
            f'This time they waited, then {food.flip_word}ed the food carefully. Soon the other side was {heat.second_side}.'
        )
    world.facts["second_side_burned"] = food_ent.meters["second_burned"] >= THRESHOLD


def apology_and_reconciliation(world: World, impatient: Entity, careful: Entity) -> None:
    impatient.memes["sorry"] += 1
    careful.memes["forgiveness"] += 1
    impatient.memes["love"] += 1
    careful.memes["love"] += 1
    world.say(
        f'{impatient.id} looked at {careful.id} and huffed a tiny embarrassed laugh. "You were right about the side and the temperature," {impatient.pronoun()} said.'
    )
    world.say(
        f'{careful.id} smiled back. "And I was too bossy about it," {careful.pronoun()} admitted. Then they bumped elbows and made peace right there by the counter.'
    )


def ending(world: World, impatient: Entity, careful: Entity, parent: Entity, food: Food) -> None:
    burned = world.facts.get("second_side_burned", False)
    if burned:
        world.say(
            f'At the table, they cut away the extra-dark edge, laughed at their very dramatic lunch, and shared the rest. One side was a little singed, but the middle was warm, and nobody argued with the plate anymore.'
        )
    else:
        world.say(
            f'At the table, they split the {food.cooked_name} down the middle and checked each side before the first bite. The warm side was just right, the cooler side got a pat of butter, and lunch tasted much better now that they were friends again.'
        )
    world.say(
        f'{parent.label_word.capitalize()} said that kitchens like patient hands, real tools, and kind words. Both children nodded with full cheeks.'
    )


def tell(
    food: Food,
    heat: Heat,
    tool: Tool,
    child1: str = "Tom",
    child1_gender: str = "boy",
    child2: str = "Lily",
    child2_gender: str = "girl",
    parent_type: str = "mother",
    relation: str = "siblings",
    impatient_trait: str = "hungry",
    careful_trait: str = "careful",
) -> World:
    world = World()
    impatient = world.add(Entity(
        id=child1,
        kind="character",
        type=child1_gender,
        role="impatient",
        traits=[impatient_trait],
        attrs={"relation": relation},
    ))
    careful = world.add(Entity(
        id=child2,
        kind="character",
        type=child2_gender,
        role="careful",
        traits=[careful_trait],
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    pan = world.add(Entity(
        id="pan",
        type="pan",
        label=food.vessel,
        phrase=f"the {food.vessel}",
        tags={"hot_surface"},
    ))
    food_ent = world.add(Entity(
        id="food",
        type="food",
        label=food.cooked_name,
        phrase=food.raw_name,
        tags=set(food.tags),
    ))

    world.facts.update(
        impatient=impatient,
        careful=careful,
        parent=parent,
        pan=pan,
        food_cfg=food,
        heat_cfg=heat,
        tool_cfg=tool,
        relation=relation,
    )

    introduce(world, impatient, careful, parent, food)
    set_heat(world, heat)
    world.para()
    pour(world, impatient, careful, food)
    argue_about_side(world, impatient, careful, food, heat)
    try_early_flip(world, impatient, food, heat)
    careful_warning(world, careful, parent, heat, tool)
    world.para()
    grab_or_tool(world, impatient, parent, heat, tool)
    parent_steps_in(world, parent, TOOLS["spatula"] if not tool.safe else tool)
    finish_cooking(world, impatient, careful, food, heat, TOOLS["spatula"] if not tool.safe else tool)
    apology_and_reconciliation(world, impatient, careful)
    world.para()
    ending(world, impatient, careful, parent, food)

    world.facts["outcome"] = outcome_of(
        StoryParams(
            food=food.id,
            heat=heat.id,
            tool=tool.id,
            child1=child1,
            child1_gender=child1_gender,
            child2=child2,
            child2_gender=child2_gender,
            parent=parent_type,
            relation=relation,
            impatient_trait=impatient_trait,
            careful_trait=careful_trait,
        )
    )
    return world


KNOWLEDGE = {
    "temperature": [
        (
            "What does temperature mean in cooking?",
            "Temperature tells how hot or cool something is. In cooking, the right temperature helps food cook safely and evenly."
        )
    ],
    "pan": [
        (
            "Why should children keep their hands away from a hot pan?",
            "A hot pan can burn skin very quickly. That is why a grown-up should handle it and children should use safe tools only with help."
        )
    ],
    "spatula": [
        (
            "What is a spatula for?",
            "A spatula is a flat kitchen tool used to lift and turn food in a pan. It keeps your hands farther from the hot surface."
        )
    ],
    "tongs": [
        (
            "What are tongs for?",
            "Tongs help pick up or move food without grabbing it with your hands. They give you a safer reach around hot things."
        )
    ],
    "share": [
        (
            "How can sharing help after an argument?",
            "Sharing gives people a way to be kind again together. Doing one small good thing can help both sides calm down and make peace."
        )
    ],
    "burn": [
        (
            "What happens if a pan is too hot?",
            "Food can cook too fast and burn on the outside before it is ready inside. A pan that is too hot can also make the kitchen less safe."
        )
    ],
    "pancake": [
        (
            "How does batter turn into a pancake?",
            "Heat changes the wet batter into a soft solid pancake. As it cooks, the batter firms up and the surface turns golden."
        )
    ],
    "bread": [
        (
            "How does dough change when it cooks?",
            "Heat changes soft dough into bread that holds its shape. That is a transformation from raw to cooked food."
        )
    ],
    "apple": [
        (
            "Why do cooked apples smell sweet?",
            "Warm apples release a sweet smell, especially with cinnamon. Heat makes those smells easier to notice."
        )
    ],
}

KNOWLEDGE_ORDER = ["temperature", "pan", "burn", "spatula", "tongs", "pancake", "bread", "apple", "share"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["impatient"]
    b = f["careful"]
    food = f["food_cfg"]
    heat = f["heat_cfg"]
    return [
        f'Write a short comedy for a 3-to-5-year-old that includes the words "side" and "temperature" and is about children cooking {food.cooked_name}.',
        f"Tell a gentle cautionary kitchen story where {a.id} rushes, {b.id} worries about the pan temperature, and the children reconcile before lunch.",
        f"Write a funny story about how one side of a {food.cooked_name} can look ready before the rest is ready, ending with an apology and a shared meal.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["impatient"]
    b = f["careful"]
    parent = f["parent"]
    food = f["food_cfg"]
    heat = f["heat_cfg"]
    tool = f["tool_cfg"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, who were helping {parent.label_word} cook {food.cooked_name}. They got silly and argued, then made peace again."
        ),
        (
            f"What were they cooking, and how did it change?",
            f"They started with {food.raw_name}, and the heat changed it into {food.cooked_name}. That transformation is why one side could look different from the other side as it cooked."
        ),
        (
            f"Why did {b.id} talk about temperature?",
            f"{b.id} knew that looking golden on one side was not the same as being ready all through. {b.pronoun().capitalize()} was trying to remind {a.id} that the pan's temperature and the food's middle both mattered."
        ),
    ]
    if f.get("touch_scare"):
        qa.append(
            (
                f"What little scare happened in the kitchen?",
                f"{a.id} reached in the wrong way near the hot handle and yelped, then pulled back quickly. The scare was small, but it showed why hot pans need tools and patient hands."
            )
        )
    else:
        qa.append(
            (
                f"How did they handle the hot food safely?",
                f"{parent.label_word.capitalize()} gave them {tool.phrase}, and they used it instead of hands. That kept the hot pan at a safer distance while they cooked."
            )
        )
    if f.get("second_side_burned"):
        qa.append(
            (
                "How did the story end?",
                f"It ended with a funny little mistake: one side got a bit too dark because the heat was high. Even so, the children apologized, shared what was still tasty, and laughed together at the table."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended with the children apologizing and sharing the finished {food.cooked_name}. They checked each side calmly, and lunch tasted better once the argument was over."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["food_cfg"].tags) | set(f["heat_cfg"].tags) | set(f["tool_cfg"].tags)
    tags.add("temperature")
    tags.add("pan")
    if f.get("relation") in {"siblings", "friends"}:
        tags.add("share")
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
    for e in world.entities.values():
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        food="pancake",
        heat="medium",
        tool="spatula",
        child1="Tom",
        child1_gender="boy",
        child2="Lily",
        child2_gender="girl",
        parent="mother",
        relation="siblings",
        impatient_trait="hungry",
        careful_trait="patient",
    ),
    StoryParams(
        food="fritter",
        heat="high",
        tool="tongs",
        child1="Max",
        child1_gender="boy",
        child2="Mia",
        child2_gender="girl",
        parent="father",
        relation="friends",
        impatient_trait="bouncy",
        careful_trait="steady",
    ),
    StoryParams(
        food="flatbread",
        heat="high",
        tool="fingers",
        child1="Sam",
        child1_gender="boy",
        child2="Zoe",
        child2_gender="girl",
        parent="mother",
        relation="siblings",
        impatient_trait="hasty",
        careful_trait="careful",
    ),
    StoryParams(
        food="pancake",
        heat="low",
        tool="spatula",
        child1="Ella",
        child1_gender="girl",
        child2="Nora",
        child2_gender="girl",
        parent="father",
        relation="siblings",
        impatient_trait="silly",
        careful_trait="gentle",
    ),
]


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for fid in FOODS:
        lines.append(asp.fact("food", fid))
    for hid, h in HEATS.items():
        lines.append(asp.fact("heat", hid))
        lines.append(asp.fact("risk", hid, h.risk))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, t.sense))
        if t.safe:
            lines.append(asp.fact("safe_tool", tid))
    return "\n".join(lines)


ASP_RULES = r"""
reasonable_tool(T) :- tool(T), sense(T, S), sense_min(M), S >= M.
valid(F, H, T) :- food(F), heat(H), tool(T), reasonable_tool(T).
valid(F, high, fingers) :- food(F).

chosen_outcome(rejected) :- chosen_heat(H), chosen_tool(T), risk(H, R), R < 2, not safe_tool(T).
chosen_outcome(scared)   :- chosen_heat(H), chosen_tool(T), risk(H, R), R >= 2, not safe_tool(T).
chosen_outcome(singed)   :- chosen_heat(high), chosen_tool(T), safe_tool(T).
chosen_outcome(golden)   :- chosen_heat(low), chosen_tool(T), safe_tool(T).
chosen_outcome(golden)   :- chosen_heat(medium), chosen_tool(T), safe_tool(T).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_heat", params.heat),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show chosen_outcome/1."))
    atoms = asp.atoms(model, "chosen_outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: two children learn that heat changes food side by side, and kindness matters too."
    )
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--heat", choices=HEATS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.food is not None and args.food not in FOODS:
        raise StoryError(f"(No story: unknown food '{args.food}'.)")
    if args.heat is not None and args.heat not in HEATS:
        raise StoryError(f"(No story: unknown heat '{args.heat}'.)")
    if args.tool is not None and args.tool not in TOOLS:
        raise StoryError(f"(No story: unknown tool '{args.tool}'.)")

    combos = [
        c for c in valid_combos()
        if (args.food is None or c[0] == args.food)
        and (args.heat is None or c[1] == args.heat)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        if args.tool and args.heat:
            tool = TOOLS[args.tool]
            heat = HEATS[args.heat]
            message = explain_tool(tool, heat)
            if message:
                raise StoryError(message)
        raise StoryError("(No valid combination matches the given options.)")

    food, heat, tool = rng.choice(sorted(combos))
    child1, g1 = _pick_kid(rng)
    child2, g2 = _pick_kid(rng, avoid=child1)
    parent = args.parent or rng.choice(["mother", "father"])
    relation = rng.choice(["siblings", "friends"])
    return StoryParams(
        food=food,
        heat=heat,
        tool=tool,
        child1=child1,
        child1_gender=g1,
        child2=child2,
        child2_gender=g2,
        parent=parent,
        relation=relation,
        impatient_trait=rng.choice(IMPATIENT_TRAITS),
        careful_trait=rng.choice(CAREFUL_TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.food not in FOODS:
        raise StoryError(f"(No story: unknown food '{params.food}'.)")
    if params.heat not in HEATS:
        raise StoryError(f"(No story: unknown heat '{params.heat}'.)")
    if params.tool not in TOOLS:
        raise StoryError(f"(No story: unknown tool '{params.tool}'.)")
    if outcome_of(params) == "rejected":
        raise StoryError(explain_tool(TOOLS[params.tool], HEATS[params.heat]) or "(No valid combination.)")

    world = tell(
        food=FOODS[params.food],
        heat=HEATS[params.heat],
        tool=TOOLS[params.tool],
        child1=params.child1,
        child1_gender=params.child1_gender,
        child2=params.child2,
        child2_gender=params.child2_gender,
        parent_type=params.parent,
        relation=params.relation,
        impatient_trait=params.impatient_trait,
        careful_trait=params.careful_trait,
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

    scenarios = list(CURATED)
    for seed in range(20):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        scenarios.append(p)

    mismatches = []
    for p in scenarios:
        py = outcome_of(p)
        if py == "rejected":
            continue
        asp_out = asp_outcome(p)
        if asp_out != py:
            mismatches.append((p.food, p.heat, p.tool, py, asp_out))
    if not mismatches:
        print(f"OK: outcome model matches on {len(scenarios)} sampled scenarios.")
    else:
        rc = 1
        print("MISMATCH in outcomes:")
        for row in mismatches[:10]:
            print(" ", row)

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show chosen_outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (food, heat, tool) combos:\n")
        for food, heat, tool in combos:
            print(f"  {food:10} {heat:7} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            sample = generate(p)
            samples.append(sample)
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
            try:
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.child1} & {p.child2}: {p.food} on {p.heat} heat with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
