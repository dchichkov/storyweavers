#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/broil_teamwork_surprise_curiosity_heartwarming.py
============================================================================

A standalone story world about two children making a warm surprise snack with a
grown-up helper after becoming curious about the oven setting labeled "broil".

The domain is built around a child-facing, heartwarming pattern:

    curiosity -> careful explanation -> teamwork in the kitchen ->
    a quick broil under adult hands -> a warm surprise shared together

The world model enforces a simple common-sense constraint: only foods with a
top that sensibly browns under a broiler are accepted, and the broiler may only
be used when a grown-up helper is present to handle the hot tray.

Run it
------
    python storyworlds/worlds/gpt-5.4/broil_teamwork_surprise_curiosity_heartwarming.py
    python storyworlds/worlds/gpt-5.4/broil_teamwork_surprise_curiosity_heartwarming.py --base toast --topping cheese
    python storyworlds/worlds/gpt-5.4/broil_teamwork_surprise_curiosity_heartwarming.py --base soup
    python storyworlds/worlds/gpt-5.4/broil_teamwork_surprise_curiosity_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/broil_teamwork_surprise_curiosity_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/broil_teamwork_surprise_curiosity_heartwarming.py --verify
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
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "aunt"}
        male = {"boy", "father", "grandfather", "man", "uncle"}
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
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class BaseFood:
    id: str
    label: str
    phrase: str
    plural: str
    tray_phrase: str
    takes_topping: bool = True
    sturdy: bool = True
    broil_ok: bool = True
    browns_to: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Topping:
    id: str
    label: str
    phrase: str
    suitable_for: set[str] = field(default_factory=set)
    browns_to: str = ""
    stir_text: str = ""
    spread_text: str = ""
    smell: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    type: str
    phrase: str
    careful_line: str
    surprise_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RecipientCfg:
    id: str
    type: str
    phrase: str
    arrival: str
    thanks: str
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


def _r_shared_work(world: World) -> list[str]:
    kids = [e for e in world.entities.values() if e.role == "child"]
    if len(kids) < 2:
        return []
    if not all(k.meters["helped"] >= THRESHOLD for k in kids):
        return []
    sig = ("shared_work",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in kids:
        kid.memes["teamwork"] += 1
        kid.memes["pride"] += 1
    return ["__teamwork__"]


def _r_broil_brown(world: World) -> list[str]:
    food = world.get("food")
    helper = world.get("helper")
    if food.meters["under_broiler"] < THRESHOLD:
        return []
    sig = ("broil_brown",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if helper.meters["present"] >= THRESHOLD:
        food.meters["browned"] += 1
        food.meters["warm"] += 1
        for kid in [e for e in world.entities.values() if e.role == "child"]:
            kid.memes["wonder"] += 1
        return ["__browned__"]
    food.meters["scorched"] += 1
    return ["__scorched__"]


def _r_smell_gathers(world: World) -> list[str]:
    food = world.get("food")
    if food.meters["warm"] < THRESHOLD:
        return []
    sig = ("smell_gathers",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for ent in world.entities.values():
        if ent.role in {"child", "recipient", "helper"}:
            ent.memes["hunger"] += 1
            ent.memes["anticipation"] += 1
    return ["__smell__"]


CAUSAL_RULES = [
    Rule(name="shared_work", tag="social", apply=_r_shared_work),
    Rule(name="broil_brown", tag="physical", apply=_r_broil_brown),
    Rule(name="smell_gathers", tag="physical", apply=_r_smell_gathers),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


def compatible(base: BaseFood, topping: Topping) -> bool:
    return base.id in topping.suitable_for and base.broil_ok and base.takes_topping and base.sturdy


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for base_id, base in BASES.items():
        for topping_id, topping in TOPPINGS.items():
            if not compatible(base, topping):
                continue
            for helper_id in HELPERS:
                for recipient_id in RECIPIENTS:
                    combos.append((base_id, topping_id, helper_id, recipient_id))
    return combos


def explain_rejection(base: BaseFood, topping: Optional[Topping] = None) -> str:
    if not base.broil_ok:
        return (
            f"(No story: {base.phrase} is not a sensible thing to broil in this little world. "
            f"The top would not quickly brown into a warm surprise, so pick toast, muffins, or fruit.)"
        )
    if not base.takes_topping or not base.sturdy:
        return (
            f"(No story: {base.phrase} would not hold a quick broiled topping neatly enough for this scene.)"
        )
    if topping is not None and base.id not in topping.suitable_for:
        return (
            f"(No story: {topping.label} does not make a good broiled top for {base.plural}. "
            f"The food and topping should belong together.)"
        )
    return "(No story: this kitchen combination is not reasonable.)"


def predict_broil(world: World) -> dict:
    sim = world.copy()
    food = sim.get("food")
    food.meters["under_broiler"] += 1
    propagate(sim, narrate=False)
    return {
        "browned": food.meters["browned"] >= THRESHOLD,
        "warm": food.meters["warm"] >= THRESHOLD,
        "scorched": food.meters["scorched"] >= THRESHOLD,
    }


def kitchen_setup(world: World, kid1: Entity, kid2: Entity, helper: Entity, recipient: Entity) -> None:
    for kid in (kid1, kid2):
        kid.memes["curiosity"] += 1
        kid.memes["love"] += 1
    world.say(
        f"On a soft afternoon, {kid1.id} and {kid2.id} stood on sturdy stools beside "
        f"{helper.phrase}. They wanted to make a small surprise for {recipient.phrase} before {recipient.attrs['arrival']}."
    )
    world.say(
        f"The mixing bowls clicked, the kitchen smelled warm already, and both children kept peeking at the oven."
    )


def notice_broil(world: World, kid1: Entity, kid2: Entity) -> None:
    world.say(
        f'On the oven knob, {kid1.id} spotted a word {kid1.pronoun()} did not know. '
        f'"What does broil mean?" {kid1.pronoun()} asked.'
    )
    world.say(
        f"{kid2.id} leaned closer too. The new word made both of them even more curious."
    )


def explain_broil(world: World, helper: Entity, kid1: Entity, kid2: Entity) -> None:
    helper.memes["care"] += 1
    world.say(
        f'{helper.label_word.capitalize()} smiled and said, "{helper.attrs["careful_line"]}"'
    )
    world.say(
        f"{helper.label_word.capitalize()} promised to handle the hot oven while {kid1.id} and {kid2.id} did the safe helping jobs."
    )


def choose_plan(world: World, kid1: Entity, kid2: Entity, base: BaseFood, topping: Topping, recipient: Entity) -> None:
    world.say(
        f'"Let\'s make {base.plural} for {recipient.phrase},' f' {kid2.id} said. '
        f'The idea felt like a little secret everyone could share.'
    )
    world.say(
        f"The plan was simple: stir the {topping.label}, spread it on {base.plural}, and let the grown-up do the quick broil at the end."
    )


def teamwork(world: World, kid1: Entity, kid2: Entity, base: BaseFood, topping: Topping) -> None:
    kid1.meters["helped"] += 1
    kid2.meters["helped"] += 1
    world.get("food").meters["assembled"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{kid1.id} {topping.stir_text}, and {kid2.id} {topping.spread_text} on {base.tray_phrase}."
    )
    if all(k.memes["teamwork"] >= THRESHOLD for k in (kid1, kid2)):
        world.say(
            f"They had to work together carefully, and that made the kitchen feel even warmer."
        )


def broil_scene(world: World, helper: Entity, base: BaseFood, topping: Topping) -> None:
    food = world.get("food")
    food.meters["under_broiler"] += 1
    pred = predict_broil(world)
    world.facts["predicted_browned"] = pred["browned"]
    world.say(
        f"{helper.label_word.capitalize()} slid the tray under the heat for a quick broil while the children watched from the safe line on the floor."
    )
    markers = propagate(world, narrate=False)
    if "__browned__" in markers:
        world.say(
            f"In a tiny minute, the tops turned {topping.browns_to}, and the smell of {topping.smell} drifted through the room."
        )
    elif "__scorched__" in markers:
        world.say("The top darkened too fast, and the little snack had to be thrown away.")
    if "__smell__" in markers:
        world.say(
            f"{kid_names(world)} breathed in together, wide-eyed at how quickly a plain tray could change."
        )


def kid_names(world: World) -> str:
    kids = [e.id for e in world.entities.values() if e.role == "child"]
    return " and ".join(kids)


def hide_surprise(world: World, kid1: Entity, kid2: Entity, helper: Entity, base: BaseFood) -> None:
    for kid in (kid1, kid2):
        kid.memes["anticipation"] += 1
    world.say(
        f'Together they carried the warm plate to the table, and {helper.label_word} whispered, "{helper.attrs["surprise_line"]}"'
    )
    world.say(
        f"{kid1.id} and {kid2.id} tucked themselves behind their chairs, trying very hard not to giggle at the secret {base.plural}."
    )


def surprise_reveal(world: World, kid1: Entity, kid2: Entity, helper: Entity, recipient: Entity, base: BaseFood) -> None:
    recipient.meters["arrived"] += 1
    recipient.memes["surprise"] += 1
    for kid in (kid1, kid2):
        kid.memes["joy"] += 1
    world.say(
        f"When {recipient.phrase} came in, {recipient.pronoun()} stopped and blinked at the shining plate. "
        f'"For me?" {recipient.pronoun()} asked.'
    )
    world.say(
        f'"Surprise!" {kid1.id} and {kid2.id} said together. {recipient.thanks}'
    )
    world.say(
        f"They all shared the first warm bites, and the children felt proud that a curious little word on the oven had led to teamwork, a surprise, and a happy table."
    )


def tell(
    base: BaseFood,
    topping: Topping,
    helper_cfg: HelperCfg,
    recipient_cfg: RecipientCfg,
    kid1_name: str = "Lily",
    kid1_type: str = "girl",
    kid2_name: str = "Ben",
    kid2_type: str = "boy",
) -> World:
    world = World()
    kid1 = world.add(Entity(id=kid1_name, kind="character", type=kid1_type, role="child"))
    kid2 = world.add(Entity(id=kid2_name, kind="character", type=kid2_type, role="child"))
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_cfg.type,
            role="helper",
            phrase=helper_cfg.phrase,
            attrs={
                "careful_line": helper_cfg.careful_line,
                "surprise_line": helper_cfg.surprise_line,
            },
            tags=set(helper_cfg.tags),
        )
    )
    recipient = world.add(
        Entity(
            id="Recipient",
            kind="character",
            type=recipient_cfg.type,
            role="recipient",
            phrase=recipient_cfg.phrase,
            attrs={"arrival": recipient_cfg.arrival},
            tags=set(recipient_cfg.tags),
        )
    )
    helper.meters["present"] = 1.0
    food = world.add(
        Entity(
            id="food",
            type="food",
            label=base.label,
            phrase=base.phrase,
            attrs={"plural": base.plural, "browns_to": topping.browns_to},
            tags=set(base.tags) | set(topping.tags),
        )
    )

    kitchen_setup(world, kid1, kid2, helper, recipient)
    notice_broil(world, kid1, kid2)

    world.para()
    explain_broil(world, helper, kid1, kid2)
    choose_plan(world, kid1, kid2, base, topping, recipient)
    teamwork(world, kid1, kid2, base, topping)

    world.para()
    broil_scene(world, helper, base, topping)
    hide_surprise(world, kid1, kid2, helper, base)

    world.para()
    surprise_reveal(world, kid1, kid2, helper, recipient, base)

    world.facts.update(
        kid1=kid1,
        kid2=kid2,
        helper=helper,
        recipient=recipient,
        base=base,
        topping=topping,
        food=food,
        curious=kid1.memes["curiosity"] >= THRESHOLD and kid2.memes["curiosity"] >= THRESHOLD,
        teamwork=food.meters["assembled"] >= THRESHOLD and kid1.memes["teamwork"] >= THRESHOLD,
        browned=food.meters["browned"] >= THRESHOLD,
        warm=food.meters["warm"] >= THRESHOLD,
        surprise=recipient.meters["arrived"] >= THRESHOLD and recipient.memes["surprise"] >= THRESHOLD,
    )
    return world


BASES = {
    "toast": BaseFood(
        id="toast",
        label="toast",
        phrase="small slices of bread",
        plural="little toasts",
        tray_phrase="the little bread slices",
        takes_topping=True,
        sturdy=True,
        broil_ok=True,
        browns_to="golden on top",
        tags={"toast", "kitchen"},
    ),
    "muffins": BaseFood(
        id="muffins",
        label="muffin",
        phrase="split mini muffins",
        plural="warm muffin halves",
        tray_phrase="the split muffin halves",
        takes_topping=True,
        sturdy=True,
        broil_ok=True,
        browns_to="lightly crisp",
        tags={"muffin", "kitchen"},
    ),
    "peaches": BaseFood(
        id="peaches",
        label="peach",
        phrase="soft peach halves",
        plural="broiled peach halves",
        tray_phrase="the peach halves",
        takes_topping=True,
        sturdy=True,
        broil_ok=True,
        browns_to="glossy and bubbling",
        tags={"fruit", "kitchen"},
    ),
    "soup": BaseFood(
        id="soup",
        label="soup",
        phrase="a bowl of soup",
        plural="bowls of soup",
        tray_phrase="the soup bowls",
        takes_topping=False,
        sturdy=False,
        broil_ok=False,
        browns_to="",
        tags={"soup"},
    ),
}

TOPPINGS = {
    "cheese": Topping(
        id="cheese",
        label="cheese",
        phrase="a snowy handful of cheese",
        suitable_for={"toast", "muffins"},
        browns_to="melty and speckled gold",
        stir_text="sprinkled the cheese with careful fingers",
        spread_text="lined up the pieces and added tomato slices",
        smell="toasted bread and cheese",
        tags={"cheese", "broiler"},
    ),
    "cinnamon_honey": Topping(
        id="cinnamon_honey",
        label="cinnamon honey",
        phrase="a shiny swirl of honey and cinnamon",
        suitable_for={"toast", "muffins", "peaches"},
        browns_to="bubbly and brown at the edges",
        stir_text="stirred honey and cinnamon until the spoon smelled sweet",
        spread_text="brushed the shiny mixture gently",
        smell="warm cinnamon",
        tags={"cinnamon", "broiler"},
    ),
    "oat_crumble": Topping(
        id="oat_crumble",
        label="oat crumble",
        phrase="a sandy oat crumble",
        suitable_for={"peaches"},
        browns_to="toasty and crisp",
        stir_text="mixed oats, butter, and a pinch of sugar into soft crumbs",
        spread_text="patted the crumble over the fruit",
        smell="sweet oats and fruit",
        tags={"oats", "broiler"},
    ),
}

HELPERS = {
    "grandma": HelperCfg(
        id="grandma",
        type="grandmother",
        phrase="their grandma",
        careful_line="Broil means very hot heat from above, so it works quickly. I will open the oven and move the tray, and you can help with the mixing and arranging.",
        surprise_line="Quick, let's set the table before our surprise walks in.",
        tags={"grandma"},
    ),
    "grandpa": HelperCfg(
        id="grandpa",
        type="grandfather",
        phrase="their grandpa",
        careful_line="Broil means the heat comes from the top and gets the food brown fast. I will take care of the oven, and you two can be my careful kitchen team.",
        surprise_line="Let's hide the plate in the middle and wait with quiet smiles.",
        tags={"grandpa"},
    ),
    "aunt": HelperCfg(
        id="aunt",
        type="aunt",
        phrase="their aunt",
        careful_line="Broil is a quick top heat, almost like the oven giving the food a warm brown kiss. The oven part is my job, and the safe helping jobs are yours.",
        surprise_line="Scoot the plate to the center and tuck in your grins.",
        tags={"aunt"},
    ),
}

RECIPIENTS = {
    "mom": RecipientCfg(
        id="mom",
        type="mother",
        phrase="Mom",
        arrival="Mom came home",
        thanks="Mom laughed softly and pulled them close before sitting down. The surprise made the whole room feel loved.",
        tags={"mom"},
    ),
    "dad": RecipientCfg(
        id="dad",
        type="father",
        phrase="Dad",
        arrival="Dad came home",
        thanks="Dad's tired face turned bright at once, and he thanked every helper at the table. The surprise made the end of the day feel gentle.",
        tags={"dad"},
    ),
    "neighbor": RecipientCfg(
        id="neighbor",
        type="woman",
        phrase="Mrs. Rami next door",
        arrival="Mrs. Rami knocked at the door",
        thanks="Mrs. Rami looked touched and said the warm treat was the nicest surprise of her whole week. The children beamed at one another.",
        tags={"neighbor"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli"]


@dataclass
class StoryParams:
    base: str
    topping: str
    helper: str
    recipient: str
    kid1_name: str
    kid1_type: str
    kid2_name: str
    kid2_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "broil": [
        (
            "What does broil mean in cooking?",
            "Broil means cooking food with very strong heat from above. It browns the top quickly, so a grown-up should handle it carefully."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help one another to do one job together. Each person does a part, and the whole job goes better that way."
        )
    ],
    "surprise": [
        (
            "What makes a surprise feel kind?",
            "A kind surprise is something done to make another person feel happy or cared for. It feels warm because someone was thinking about you."
        )
    ],
    "cheese": [
        (
            "What happens to cheese under heat?",
            "Cheese gets soft and melty under heat. If the heat is strong, the top can also turn a little brown."
        )
    ],
    "cinnamon": [
        (
            "What is cinnamon?",
            "Cinnamon is a sweet-smelling brown spice. People use a little of it to make food smell warm and cozy."
        )
    ],
    "oats": [
        (
            "What are oats?",
            "Oats are small grains that can be used in breakfast foods and crumbles. When they toast, they smell warm and nutty."
        )
    ],
    "toast": [
        (
            "Why does bread turn brown when it toasts?",
            "Heat dries and browns the surface of the bread. That is why toast smells different from plain bread."
        )
    ],
    "fruit": [
        (
            "What can heat do to fruit?",
            "Heat can make fruit softer, juicier, and sweeter-smelling. A topping on the fruit can also bubble or crisp."
        )
    ],
}
KNOWLEDGE_ORDER = ["broil", "teamwork", "surprise", "cheese", "cinnamon", "oats", "toast", "fruit"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid1 = f["kid1"]
    kid2 = f["kid2"]
    base = f["base"]
    topping = f["topping"]
    helper = f["helper"]
    recipient = f["recipient"]
    return [
        'Write a heartwarming story for a 3-to-5-year-old that includes the word "broil", curiosity, teamwork, and a happy surprise in a kitchen.',
        f"Tell a gentle story where {kid1.id} and {kid2.id} ask what broil means, help {helper.label_word} make {base.plural} with {topping.label}, and surprise {recipient.phrase}.",
        "Write a cozy story where a new cooking word leads children to ask questions, work together carefully, and share a warm treat at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid1 = f["kid1"]
    kid2 = f["kid2"]
    helper = f["helper"]
    recipient = f["recipient"]
    base = f["base"]
    topping = f["topping"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {kid1.id} and {kid2.id}, who helped {helper.label_word} in the kitchen. They were making a warm surprise for {recipient.phrase}."
        ),
        (
            "What made the children curious?",
            f"They saw the word broil on the oven and did not know what it meant. That little mystery made them stop and ask a careful question."
        ),
        (
            "How did the grown-up keep the kitchen safe?",
            f"{helper.label_word.capitalize()} explained that broil is very hot from above and said the oven part was a grown-up job. The children helped by mixing and arranging instead of touching the hot oven."
        ),
        (
            "How did the children use teamwork?",
            f"{kid1.id} and {kid2.id} each did part of the cooking job, so the snack could be ready together. One child handled part of the topping while the other arranged it on the tray."
        ),
    ]
    if f.get("browned"):
        qa.append(
            (
                f"What changed after the quick broil?",
                f"The tops of the {base.plural} turned {topping.browns_to}, and the kitchen filled with the smell of {topping.smell}. The change showed the children exactly what broil could do."
            )
        )
    if f.get("surprise"):
        qa.append(
            (
                f"Why was the ending a surprise?",
                f"{recipient.phrase} did not expect to walk in and find a warm plate waiting. The children had quietly worked together so the kind surprise would be ready at just the right moment."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with everyone sharing the warm treat at the table. The children felt proud because their curiosity led to learning, teamwork, and a loving surprise."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"broil", "teamwork", "surprise"}
    base = f["base"]
    topping = f["topping"]
    tags |= set(base.tags)
    tags |= set(topping.tags)
    if "cheese" in tags:
        tags.add("cheese")
    if "cinnamon" in tags:
        tags.add("cinnamon")
    if "oats" in tags:
        tags.add("oats")
    if "toast" in tags:
        tags.add("toast")
    if "fruit" in tags:
        tags.add("fruit")
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
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:11}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        base="toast",
        topping="cheese",
        helper="grandma",
        recipient="mom",
        kid1_name="Lily",
        kid1_type="girl",
        kid2_name="Ben",
        kid2_type="boy",
    ),
    StoryParams(
        base="peaches",
        topping="oat_crumble",
        helper="grandpa",
        recipient="dad",
        kid1_name="Maya",
        kid1_type="girl",
        kid2_name="Leo",
        kid2_type="boy",
    ),
    StoryParams(
        base="muffins",
        topping="cinnamon_honey",
        helper="aunt",
        recipient="neighbor",
        kid1_name="Ava",
        kid1_type="girl",
        kid2_name="Finn",
        kid2_type="boy",
    ),
]


ASP_RULES = r"""
% A valid kitchen story needs a sensible broilable base and a topping that fits it.
valid(B, T, H, R) :- base(B), topping(T), helper(H), recipient(R),
                     broil_ok(B), takes_topping(B), sturdy(B),
                     suitable(T, B).

% Outcome of the little simulation: if a helper is present and the food goes under
% the broiler, the top browns and the surprise succeeds.
browned :- helper_present.
surprise_success :- browned.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for base_id, base in BASES.items():
        lines.append(asp.fact("base", base_id))
        if base.broil_ok:
            lines.append(asp.fact("broil_ok", base_id))
        if base.takes_topping:
            lines.append(asp.fact("takes_topping", base_id))
        if base.sturdy:
            lines.append(asp.fact("sturdy", base_id))
    for topping_id, topping in TOPPINGS.items():
        lines.append(asp.fact("topping", topping_id))
        for base_id in sorted(topping.suitable_for):
            lines.append(asp.fact("suitable", topping_id, base_id))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    for recipient_id in RECIPIENTS:
        lines.append(asp.fact("recipient", recipient_id))
    lines.append(asp.fact("helper_present"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


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

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        if "broil" not in sample.story.lower():
            raise StoryError("smoke test story did not include required word 'broil'")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: curiosity about broil becomes teamwork and a warm surprise."
    )
    ap.add_argument("--base", choices=BASES)
    ap.add_argument("--topping", choices=TOPPINGS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--recipient", choices=RECIPIENTS)
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


def pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.base and not BASES[args.base].broil_ok:
        raise StoryError(explain_rejection(BASES[args.base]))
    if args.base and args.topping:
        base = BASES[args.base]
        topping = TOPPINGS[args.topping]
        if not compatible(base, topping):
            raise StoryError(explain_rejection(base, topping))

    combos = [
        combo for combo in valid_combos()
        if (args.base is None or combo[0] == args.base)
        and (args.topping is None or combo[1] == args.topping)
        and (args.helper is None or combo[2] == args.helper)
        and (args.recipient is None or combo[3] == args.recipient)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    base_id, topping_id, helper_id, recipient_id = rng.choice(sorted(combos))
    kid1_name, kid1_type = pick_child(rng)
    kid2_name, kid2_type = pick_child(rng, avoid=kid1_name)
    return StoryParams(
        base=base_id,
        topping=topping_id,
        helper=helper_id,
        recipient=recipient_id,
        kid1_name=kid1_name,
        kid1_type=kid1_type,
        kid2_name=kid2_name,
        kid2_type=kid2_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.base not in BASES:
        raise StoryError(f"(Unknown base: {params.base})")
    if params.topping not in TOPPINGS:
        raise StoryError(f"(Unknown topping: {params.topping})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.recipient not in RECIPIENTS:
        raise StoryError(f"(Unknown recipient: {params.recipient})")

    base = BASES[params.base]
    topping = TOPPINGS[params.topping]
    if not compatible(base, topping):
        raise StoryError(explain_rejection(base, topping))

    world = tell(
        base=base,
        topping=topping,
        helper_cfg=HELPERS[params.helper],
        recipient_cfg=RECIPIENTS[params.recipient],
        kid1_name=params.kid1_name,
        kid1_type=params.kid1_type,
        kid2_name=params.kid2_name,
        kid2_type=params.kid2_type,
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (base, topping, helper, recipient) combos:\n")
        for base_id, topping_id, helper_id, recipient_id in combos:
            print(f"  {base_id:8} {topping_id:15} {helper_id:8} {recipient_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.kid1_name} & {p.kid2_name}: {p.base} + {p.topping} ({p.helper} -> {p.recipient})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
