#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sperm_vegetarian_marinade_happy_ending_surprise_lesson.py
=====================================================================================

A standalone storyworld about a sleepy evening kitchen, a child with a plush
sperm whale, and a bowl of vegetables waiting in a vegetarian marinade.

The domain is intentionally small and classical: a child wants supper to be
ready right away, a grown-up guides the child to slow down, the vegetables
change because of the waiting, and a bedtime surprise makes the ending glow.
The lesson is simple and child-facing: gentle food takes gentle time.

Run it
------
    python storyworlds/worlds/gpt-5.4/sperm_vegetarian_marinade_happy_ending_surprise_lesson.py
    python storyworlds/worlds/gpt-5.4/sperm_vegetarian_marinade_happy_ending_surprise_lesson.py --vegetable zucchini --marinade lemon_herb
    python storyworlds/worlds/gpt-5.4/sperm_vegetarian_marinade_happy_ending_surprise_lesson.py --marinade fish_sauce
    python storyworlds/worlds/gpt-5.4/sperm_vegetarian_marinade_happy_ending_surprise_lesson.py --all
    python storyworlds/worlds/gpt-5.4/sperm_vegetarian_marinade_happy_ending_surprise_lesson.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/sperm_vegetarian_marinade_happy_ending_surprise_lesson.py --verify
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
SOAK_MIN = 1


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
    edible: bool = False
    vegetarian: bool = False
    plush: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Vegetable:
    id: str
    label: str
    phrase: str
    texture: str
    good_with: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Marinade:
    id: str
    label: str
    phrase: str
    flavors: set[str] = field(default_factory=set)
    vegetarian: bool = True
    creamy: bool = False
    shimmer: str = ""
    lesson_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    opening: str
    image: str
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


def _r_soak(world: World) -> list[str]:
    veg = world.get("vegetable")
    bowl = world.get("bowl")
    if veg.meters["coated"] < THRESHOLD:
        return []
    if bowl.meters["waited"] < SOAK_MIN:
        return []
    sig = ("soak",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    veg.meters["flavored"] += 1
    veg.meters["tender"] += 1
    return ["__soak__"]


def _r_rush(world: World) -> list[str]:
    child = world.get("child")
    bowl = world.get("bowl")
    if child.memes["impatience"] < THRESHOLD:
        return []
    if bowl.meters["waited"] >= SOAK_MIN:
        return []
    sig = ("rush",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bowl.memes["risk"] += 1
    return ["__risk__"]


def _r_roast(world: World) -> list[str]:
    veg = world.get("vegetable")
    tray = world.get("tray")
    if tray.meters["oven"] < THRESHOLD:
        return []
    sig = ("roast",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if veg.meters["flavored"] >= THRESHOLD:
        veg.meters["roasted"] += 1
        veg.meters["delicious"] += 1
    else:
        veg.meters["roasted"] += 1
        veg.meters["bland"] += 1
    return ["__roast__"]


CAUSAL_RULES = [
    Rule(name="soak", tag="physical", apply=_r_soak),
    Rule(name="rush", tag="emotional", apply=_r_rush),
    Rule(name="roast", tag="physical", apply=_r_roast),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule.apply(world)
            if sent:
                changed = True
                out.extend(s for s in sent if not s.startswith("__"))
    if narrate:
        for sent in out:
            world.say(sent)
    return out


def compatible(vegetable: Vegetable, marinade: Marinade) -> bool:
    return marinade.vegetarian and bool(vegetable.good_with & marinade.flavors)


def explain_rejection(vegetable: Vegetable, marinade: Marinade) -> str:
    if not marinade.vegetarian:
        return (
            f"(No story: {marinade.label} is not vegetarian, but this world is about a "
            "vegetarian marinade for vegetables. Pick a vegetarian marinade instead.)"
        )
    return (
        f"(No story: {marinade.label} does not fit {vegetable.label} in this tiny world. "
        "Pick a marinade whose flavors suit the vegetable.)"
    )


def predict_dinner(world: World, wait: bool) -> dict:
    sim = world.copy()
    bowl = sim.get("bowl")
    tray = sim.get("tray")
    if wait:
        bowl.meters["waited"] += 1
    propagate(sim, narrate=False)
    tray.meters["oven"] += 1
    propagate(sim, narrate=False)
    veg = sim.get("vegetable")
    return {
        "delicious": veg.meters["delicious"] >= THRESHOLD,
        "flavored": veg.meters["flavored"] >= THRESHOLD,
        "bland": veg.meters["bland"] >= THRESHOLD,
    }


def bedtime_setup(world: World, child: Entity, parent: Entity, whale: Entity, vegetable: Vegetable) -> None:
    child.memes["cozy"] += 1
    child.memes["wonder"] += 1
    world.say(
        f"In the soft blue evening, {child.id} padded into the kitchen with {whale.phrase} tucked under "
        f"{child.pronoun('possessive')} arm. The house was getting sleepy, but the counter still held a bowl "
        f"for supper and a plate of {vegetable.phrase} waiting to be dressed."
    )
    world.say(
        f'"Can {whale.label} help?" {child.id} whispered. {parent.label_word.capitalize()} smiled and made a little "
        f"space beside the mixing bowl."
    )


def choose_marinade(world: World, child: Entity, parent: Entity, whale: Entity, marinade: Marinade) -> None:
    bowl = world.get("bowl")
    bowl.meters["mixed"] += 1
    bowl.meters["sweet_smell"] += 1
    world.say(
        f"Together they stirred a vegetarian marinade. It was {marinade.phrase}, and it {marinade.shimmer} as the spoon "
        f"went around and around. {whale.label} sat nearby like a patient little captain of the counter."
    )
    world.say(
        f'{parent.label_word.capitalize()} said, "This bowl is for vegetables, not for plush whales," and {child.id} '
        f"gave {whale.label} a kiss on the nose."
    )


def coat_vegetables(world: World, child: Entity, vegetable: Vegetable) -> None:
    veg = world.get("vegetable")
    veg.meters["coated"] += 1
    child.memes["pride"] += 1
    world.say(
        f"{child.id} tipped the {vegetable.label} into the bowl and turned the pieces slowly until every side was glossy. "
        f"The {vegetable.texture} pieces shone under the lamp."
    )


def hurry(world: World, child: Entity, parent: Entity, vegetable: Vegetable) -> None:
    child.memes["impatience"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"They look ready now," said {child.id}, already reaching for the baking tray. But {parent.label_word} touched '
        f"the rim of the bowl and said, \"Not quite. {vegetable.label.capitalize()} needs a little quiet time to drink in the marinade.\""
    )


def wait_together(world: World, child: Entity, parent: Entity, whale: Entity, marinade: Marinade) -> None:
    bowl = world.get("bowl")
    bowl.meters["waited"] += 1
    child.memes["calm"] += 1
    child.memes["impatience"] = 0.0
    propagate(world, narrate=False)
    if whale.attrs.get("name_game"):
        world.say(
            f"So they waited the gentle way. {child.id} counted slow spoon taps with {whale.label} and listened while "
            f"{parent.label_word} told how flavors travel softly when nobody rushes them."
        )
    else:
        world.say(
            f"So they waited the gentle way. {child.id} leaned on the counter with {whale.label} and watched the bowl "
            f"rest while the kitchen filled with the smell of {marinade.label}."
        )


def roast(world: World, child: Entity, parent: Entity, vegetable: Vegetable) -> None:
    tray = world.get("tray")
    tray.meters["oven"] += 1
    propagate(world, narrate=False)
    veg = world.get("vegetable")
    child.memes["hope"] += 1
    if veg.meters["delicious"] >= THRESHOLD:
        world.say(
            f"When the tray came out of the oven, the {vegetable.label} was tender at the edges and shining in little warm pools of flavor. "
            f"{child.id} could tell, just by the smell, that waiting had changed supper."
        )
    else:
        world.say(
            f"When the tray came out of the oven, the {vegetable.label} was warm but plain. {parent.label_word.capitalize()} saw that at once "
            f"and slid the pieces back into the bowl for one more gentle rest."
        )
        world.get("bowl").meters["waited"] += 1
        propagate(world, narrate=False)
        world.say(
            "After that extra pause and a second short bake, the kitchen smelled rich and bright, and the vegetables came out tender at last."
        )
        veg.meters["delicious"] = max(veg.meters["delicious"], 1.0)


def surprise_ending(world: World, child: Entity, parent: Entity, whale: Entity, surprise: Surprise, vegetable: Vegetable, marinade: Marinade) -> None:
    child.memes["joy"] += 1
    child.memes["love"] += 1
    child.memes["wonder"] += 1
    world.say(surprise.opening)
    world.say(
        f"{surprise.image} {child.id} held {whale.label} close and tasted a piece of {vegetable.label}. "
        f"It was soft, bright, and full of the {marinade.label} they had given it."
    )
    world.say(
        f'"Now I know," {child.id} said. "A vegetarian marinade is a quiet kind of magic. If I hurry it, supper stays sleepy. '
        f'If I wait, it wakes up." {parent.label_word.capitalize()} kissed the top of {child.pronoun("possessive")} head.'
    )
    world.say(
        f"After that, {child.id} always remembered the little lesson from the evening bowl: some good things do not need more noise or more speed; "
        f"they only need a little time and a loving hand. Soon the plate was empty, the kitchen was calm, and even {whale.label} looked ready for bed."
    )


def tell(
    vegetable: Vegetable,
    marinade: Marinade,
    surprise: Surprise,
    child_name: str = "Lila",
    child_gender: str = "girl",
    parent_type: str = "mother",
    wait_mode: str = "guided_wait",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            edible=False,
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
        )
    )
    whale = world.add(
        Entity(
            id="whale",
            kind="thing",
            type="toy",
            label="Sperry the sperm whale",
            phrase="a plush sperm whale named Sperry",
            plush=True,
            attrs={"name_game": True},
            tags={"sperm_whale", "toy"},
        )
    )
    bowl = world.add(Entity(id="bowl", type="bowl", label="mixing bowl"))
    tray = world.add(Entity(id="tray", type="tray", label="baking tray"))
    veg_ent = world.add(
        Entity(
            id="vegetable",
            type="food",
            label=vegetable.label,
            phrase=vegetable.phrase,
            edible=True,
            vegetarian=True,
            tags=set(vegetable.tags),
        )
    )

    bedtime_setup(world, child, parent, whale, vegetable)
    world.para()
    choose_marinade(world, child, parent, whale, marinade)
    coat_vegetables(world, child, vegetable)
    predicted = predict_dinner(world, wait=False)
    world.facts["predicted_without_wait"] = predicted

    world.para()
    if wait_mode == "guided_wait":
        hurry(world, child, parent, vegetable)
        wait_together(world, child, parent, whale, marinade)
    else:
        wait_together(world, child, parent, whale, marinade)

    world.para()
    roast(world, child, parent, vegetable)

    world.para()
    surprise_ending(world, child, parent, whale, surprise, vegetable, marinade)

    outcome = "patient" if wait_mode == "already_patient" else "guided"
    world.facts.update(
        child=child,
        parent=parent,
        whale=whale,
        bowl=bowl,
        tray=tray,
        vegetable_cfg=vegetable,
        marinade_cfg=marinade,
        surprise_cfg=surprise,
        outcome=outcome,
        delicious=world.get("vegetable").meters["delicious"] >= THRESHOLD,
        learned=True,
    )
    return world


VEGETABLES = {
    "zucchini": Vegetable(
        id="zucchini",
        label="zucchini",
        phrase="half-moons of zucchini",
        texture="green-striped",
        good_with={"lemon", "herb", "garlic"},
        tags={"zucchini", "vegetable"},
    ),
    "mushroom": Vegetable(
        id="mushroom",
        label="mushrooms",
        phrase="button mushrooms",
        texture="round brown",
        good_with={"garlic", "soy", "ginger"},
        tags={"mushroom", "vegetable"},
    ),
    "cauliflower": Vegetable(
        id="cauliflower",
        label="cauliflower",
        phrase="little cauliflower clouds",
        texture="pale crinkly",
        good_with={"lemon", "yogurt", "mint", "garlic"},
        tags={"cauliflower", "vegetable"},
    ),
    "carrot": Vegetable(
        id="carrot",
        label="carrots",
        phrase="carrot moons",
        texture="bright orange",
        good_with={"maple", "ginger", "lemon"},
        tags={"carrot", "vegetable"},
    ),
}

MARINADES = {
    "lemon_herb": Marinade(
        id="lemon_herb",
        label="lemon-herb marinade",
        phrase="a lemon-herb marinade with olive oil and tiny green leaves",
        flavors={"lemon", "herb", "garlic"},
        vegetarian=True,
        shimmer="caught the light like a tiny yellow ribbon",
        lesson_line="quiet flavors travel slowly",
        tags={"marinade", "vegetarian", "lemon"},
    ),
    "miso_ginger": Marinade(
        id="miso_ginger",
        label="miso-ginger marinade",
        phrase="a mellow miso-ginger marinade, smooth and golden-brown",
        flavors={"soy", "ginger", "garlic"},
        vegetarian=True,
        shimmer="made soft swirls on the spoon",
        lesson_line="savory things need a moment to sink in",
        tags={"marinade", "vegetarian", "ginger"},
    ),
    "yogurt_mint": Marinade(
        id="yogurt_mint",
        label="yogurt-mint marinade",
        phrase="a cool yogurt-mint marinade with a squeeze of lemon",
        flavors={"yogurt", "mint", "lemon"},
        vegetarian=True,
        creamy=True,
        shimmer="looked pale and cloudy, like a tiny moon",
        lesson_line="calm food likes calm hands",
        tags={"marinade", "vegetarian", "mint"},
    ),
    "maple_ginger": Marinade(
        id="maple_ginger",
        label="maple-ginger marinade",
        phrase="a sweet little maple-ginger marinade",
        flavors={"maple", "ginger", "lemon"},
        vegetarian=True,
        shimmer="slid in amber circles around the bowl",
        lesson_line="sweetness deepens when you wait",
        tags={"marinade", "vegetarian", "maple"},
    ),
    "fish_sauce": Marinade(
        id="fish_sauce",
        label="fish-sauce marinade",
        phrase="a salty fish-sauce marinade",
        flavors={"fish", "salt"},
        vegetarian=False,
        shimmer="smelled too sharp for this bedtime kitchen",
        lesson_line="",
        tags={"marinade"},
    ),
}

SURPRISES = {
    "fireflies": Surprise(
        id="fireflies",
        opening="Just then came the surprise: when they carried the tray to the open window, three fireflies drifted past like tiny floating lamps.",
        image="Their green dots blinked over the dark garden like friendly bedtime stars.",
        tags={"fireflies", "night"},
    ),
    "star_plate": Surprise(
        id="star_plate",
        opening="Just then came the surprise: Dad reached into the cupboard and brought down the star plate that only came out on extra cozy nights.",
        image="The blue plate had little silver points all around its rim, so supper looked as if it had landed in a patch of sky.",
        tags={"stars", "plate"},
    ),
    "moon_napkin": Surprise(
        id="moon_napkin",
        opening="Just then came the surprise: tucked under the warm tray was a folded napkin printed with one round moon and many sleepy clouds.",
        image="When Mom opened it, the cloth spread across the table like a tiny night garden.",
        tags={"moon", "napkin"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Ella", "Zoe", "Ivy", "Maya", "Lucy"]
BOY_NAMES = ["Owen", "Theo", "Milo", "Ben", "Noah", "Eli", "Finn", "Leo"]
WAIT_MODES = ["guided_wait", "already_patient"]


@dataclass
class StoryParams:
    vegetable: str
    marinade: str
    surprise: str
    child_name: str
    child_gender: str
    parent: str
    wait_mode: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        vegetable="zucchini",
        marinade="lemon_herb",
        surprise="fireflies",
        child_name="Lila",
        child_gender="girl",
        parent="mother",
        wait_mode="guided_wait",
    ),
    StoryParams(
        vegetable="mushroom",
        marinade="miso_ginger",
        surprise="star_plate",
        child_name="Theo",
        child_gender="boy",
        parent="father",
        wait_mode="guided_wait",
    ),
    StoryParams(
        vegetable="cauliflower",
        marinade="yogurt_mint",
        surprise="moon_napkin",
        child_name="Maya",
        child_gender="girl",
        parent="mother",
        wait_mode="already_patient",
    ),
    StoryParams(
        vegetable="carrot",
        marinade="maple_ginger",
        surprise="fireflies",
        child_name="Finn",
        child_gender="boy",
        parent="father",
        wait_mode="guided_wait",
    ),
]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for vid, vegetable in VEGETABLES.items():
        for mid, marinade in MARINADES.items():
            if compatible(vegetable, marinade):
                combos.append((vid, mid))
    return combos


KNOWLEDGE = {
    "sperm_whale": [
        (
            "What is a sperm whale?",
            "A sperm whale is a very large whale that lives in the ocean. In this story, the sperm whale is only a soft toy, not a real whale in a kitchen.",
        )
    ],
    "vegetarian": [
        (
            "What does vegetarian mean?",
            "Vegetarian food is food made without meat or fish. Vegetables, grains, beans, fruit, and many dairy foods can all be vegetarian.",
        )
    ],
    "marinade": [
        (
            "What is a marinade?",
            "A marinade is a tasty mixture that food sits in for a while before cooking. It helps the food take in flavor.",
        )
    ],
    "waiting": [
        (
            "Why can waiting help food taste better?",
            "Waiting gives the flavors time to soak in. Slow changes can make food smell richer and taste fuller.",
        )
    ],
    "fireflies": [
        (
            "Why do fireflies glow?",
            "Fireflies make their own tiny light in their bodies. They blink to signal each other in the dark.",
        )
    ],
    "stars": [
        (
            "Why do stars seem to twinkle?",
            "Stars look as if they twinkle because their light passes through moving air above us. The air bends the light a little as it travels.",
        )
    ],
    "moon": [
        (
            "Why does the moon look bright at night?",
            "The moon does not make its own light. It looks bright because sunlight shines on it and bounces to our eyes.",
        )
    ],
}
KNOWLEDGE_ORDER = ["sperm_whale", "vegetarian", "marinade", "waiting", "fireflies", "stars", "moon"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    vegetable = f["vegetable_cfg"]
    marinade = f["marinade_cfg"]
    surprise = f["surprise_cfg"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "sperm", "vegetarian", and "marinade", using a plush sperm whale and a bowl of vegetables.',
        f"Tell a gentle kitchen story where {child.id} makes {vegetable.label} with {parent.label_word}, learns to wait for a vegetarian marinade, and ends with a surprise involving {surprise.id.replace('_', ' ')}.",
        f"Write a cozy story with a happy ending and a lesson learned: rushing does not help, but patient hands and quiet time can turn supper into something special.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    whale = f["whale"]
    vegetable = f["vegetable_cfg"]
    marinade = f["marinade_cfg"]
    surprise = f["surprise_cfg"]
    predicted = f.get("predicted_without_wait", {})
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {pw}, and {whale.label}. They spend a sleepy evening making supper together.",
        ),
        (
            "What did they make in the kitchen?",
            f"They made {vegetable.label} in a vegetarian marinade. The marinade was {marinade.label}, and the vegetables rested in it before baking.",
        ),
        (
            f"Why did {pw} ask {child.id} to wait?",
            f"{pw.capitalize()} knew the vegetables needed time to drink in the marinade. Without that quiet waiting, supper would have stayed plain instead of becoming full of flavor.",
        ),
    ]
    if predicted.get("bland") or f["outcome"] == "guided":
        qa.append(
            (
                f"What lesson did {child.id} learn?",
                f"{child.id} learned that hurrying is not always helpful. Some good things, like a vegetarian marinade, need a little calm time before they are ready.",
            )
        )
    qa.append(
        (
            "What was the surprise at the end?",
            f"The surprise was {surprise.opening[0].lower() + surprise.opening[1:]} {surprise.image} The surprise made supper feel extra cozy and special.",
        )
    )
    qa.append(
        (
            f"How did the story end?",
            f"It ended happily with warm, tasty {vegetable.label} and a calm kitchen. {child.id} felt proud and cozy because the patient waiting had worked.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"sperm_whale", "vegetarian", "marinade", "waiting"}
    surprise = world.facts["surprise_cfg"]
    if "fireflies" in surprise.tags:
        tags.add("fireflies")
    if "stars" in surprise.tags or "plate" in surprise.tags:
        tags.add("stars")
    if "moon" in surprise.tags:
        tags.add("moon")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
vegetarian_marinade(M) :- marinade(M), vegetarian(M).
compatible(V, M) :- vegetable(V), marinade(M), vegetarian_marinade(M),
                    likes(V, F), has_flavor(M, F).
valid(V, M) :- compatible(V, M).

tasty(V, M, already_patient) :- valid(V, M).
tasty(V, M, guided_wait) :- valid(V, M).
outcome(V, M, already_patient, patient) :- tasty(V, M, already_patient).
outcome(V, M, guided_wait, guided) :- tasty(V, M, guided_wait).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for vid, vegetable in VEGETABLES.items():
        lines.append(asp.fact("vegetable", vid))
        for flavor in sorted(vegetable.good_with):
            lines.append(asp.fact("likes", vid, flavor))
    for mid, marinade in MARINADES.items():
        lines.append(asp.fact("marinade", mid))
        if marinade.vegetarian:
            lines.append(asp.fact("vegetarian", mid))
        for flavor in sorted(marinade.flavors):
            lines.append(asp.fact("has_flavor", mid, flavor))
    for mode in WAIT_MODES:
        lines.append(asp.fact("wait_mode", mode))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_vegetable", params.vegetable),
            asp.fact("chosen_marinade", params.marinade),
            asp.fact("chosen_wait", params.wait_mode),
            "picked_valid :- valid(V, M), chosen_vegetable(V), chosen_marinade(M).",
            "picked_outcome(O) :- outcome(V, M, W, O), chosen_vegetable(V), chosen_marinade(M), chosen_wait(W).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show picked_outcome/1."))
    atoms = asp.atoms(model, "picked_outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "patient" if params.wait_mode == "already_patient" else "guided"


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

    cases = list(CURATED)
    for seed in range(30):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - defensive verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a plush sperm whale, a vegetarian marinade, and a bedtime lesson."
    )
    ap.add_argument("--vegetable", choices=VEGETABLES)
    ap.add_argument("--marinade", choices=MARINADES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--wait-mode", choices=WAIT_MODES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible vegetable and marinade pairs derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.vegetable and args.marinade:
        vegetable = VEGETABLES[args.vegetable]
        marinade = MARINADES[args.marinade]
        if not compatible(vegetable, marinade):
            raise StoryError(explain_rejection(vegetable, marinade))
    if args.marinade and args.marinade not in MARINADES:
        raise StoryError("(Unknown marinade.)")

    combos = [
        combo
        for combo in valid_combos()
        if (args.vegetable is None or combo[0] == args.vegetable)
        and (args.marinade is None or combo[1] == args.marinade)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    vegetable_id, marinade_id = rng.choice(sorted(combos))
    surprise = args.surprise or rng.choice(sorted(SURPRISES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    wait_mode = args.wait_mode or rng.choice(WAIT_MODES)
    return StoryParams(
        vegetable=vegetable_id,
        marinade=marinade_id,
        surprise=surprise,
        child_name=name,
        child_gender=gender,
        parent=parent,
        wait_mode=wait_mode,
    )


def generate(params: StoryParams) -> StorySample:
    if params.vegetable not in VEGETABLES:
        raise StoryError(f"(Unknown vegetable '{params.vegetable}'.)")
    if params.marinade not in MARINADES:
        raise StoryError(f"(Unknown marinade '{params.marinade}'.)")
    if params.surprise not in SURPRISES:
        raise StoryError(f"(Unknown surprise '{params.surprise}'.)")
    if params.wait_mode not in WAIT_MODES:
        raise StoryError(f"(Unknown wait mode '{params.wait_mode}'.)")
    vegetable = VEGETABLES[params.vegetable]
    marinade = MARINADES[params.marinade]
    if not compatible(vegetable, marinade):
        raise StoryError(explain_rejection(vegetable, marinade))

    world = tell(
        vegetable=vegetable,
        marinade=marinade,
        surprise=SURPRISES[params.surprise],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        wait_mode=params.wait_mode,
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
        print(asp_program("", "#show valid/2.\n#show outcome/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (vegetable, marinade) combos:\n")
        for vegetable, marinade in combos:
            print(f"  {vegetable:12} {marinade}")
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
            header = f"### {p.child_name}: {p.vegetable} with {p.marinade} ({p.surprise}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
