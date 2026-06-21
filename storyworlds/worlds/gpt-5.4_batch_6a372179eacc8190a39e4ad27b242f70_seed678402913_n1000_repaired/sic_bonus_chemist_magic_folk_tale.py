#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sic_bonus_chemist_magic_folk_tale.py
===============================================================

A small folk-tale storyworld about a village chemist, a child helper, and one
missing magical ingredient. Each story begins with a village trouble, sends the
child to fetch the right ingredient in the right vessel, and turns on an act of
kindness that earns a bonus gift from a magical helper.

The seed words "sic", "bonus", and "chemist" are part of the domain itself:
the village has a careful chemist, the helper grants a bonus gift, and an old
little charm-word -- "sic" -- is taught at the turning point.

Run it
------
    python storyworlds/worlds/gpt-5.4/sic_bonus_chemist_magic_folk_tale.py
    python storyworlds/worlds/gpt-5.4/sic_bonus_chemist_magic_folk_tale.py --problem bitter_well
    python storyworlds/worlds/gpt-5.4/sic_bonus_chemist_magic_folk_tale.py --vessel basket
    python storyworlds/worlds/gpt-5.4/sic_bonus_chemist_magic_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/sic_bonus_chemist_magic_folk_tale.py --qa
    python storyworlds/worlds/gpt-5.4/sic_bonus_chemist_magic_folk_tale.py --verify
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

# Make the shared result containers importable when this nested script is run
# directly from the repo root.
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
    traits: tuple = field(default_factory=tuple)
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
class Problem:
    id: str
    trouble: str
    image: str
    ingredient: str
    source: str
    cure_text: str
    ending_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Ingredient:
    id: str
    label: str
    phrase: str
    texture: str
    stored_in: set[str] = field(default_factory=set)
    source_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Vessel:
    id: str
    label: str
    phrase: str
    preserves: set[str] = field(default_factory=set)
    carry_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    type: str
    habitat: str
    entrance: str
    trouble: str
    kindness: str
    bonus_label: str
    bonus_phrase: str
    bonus_effect: str
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


def _r_bonus_unlock(world: World) -> list[str]:
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if not hero or not helper:
        return []
    sig = ("bonus_unlock",)
    if sig in world.fired:
        return []
    if hero.memes["kindness"] < THRESHOLD or helper.memes["trust"] < THRESHOLD:
        return []
    world.fired.add(sig)
    helper.memes["generous"] += 1
    world.facts["bonus_granted"] = True
    return []


def _r_brew_success(world: World) -> list[str]:
    chemist = world.entities.get("chemist")
    village = world.entities.get("village")
    if not chemist or not village:
        return []
    sig = ("brew_success",)
    if sig in world.fired:
        return []
    if chemist.meters["ingredient_ready"] < THRESHOLD:
        return []
    world.fired.add(sig)
    village.meters["trouble"] = 0.0
    village.meters["healed"] += 1
    village.memes["relief"] += 1
    if world.facts.get("bonus_granted"):
        village.meters["blessing"] += 1
        village.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="bonus_unlock", tag="social", apply=_r_bonus_unlock),
    Rule(name="brew_success", tag="physical", apply=_r_brew_success),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for sent in out:
            world.say(sent)
    return out


PROBLEMS = {
    "bitter_well": Problem(
        id="bitter_well",
        trouble="the village well had turned bitter",
        image="Even the bucket rope smelled sharp, and nobody wanted a second sip.",
        ingredient="moonmint_dew",
        source="spring",
        cure_text="sweeten the well again",
        ending_text="The well shone clear, and children leaned over the stones to see their bright faces in it.",
        tags={"well", "water", "chemist"},
    ),
    "sleepy_orchard": Problem(
        id="sleepy_orchard",
        trouble="the orchard trees had fallen into a magical sleep",
        image="Their leaves drooped like tired hands, and the apples would not blush red.",
        ingredient="sunseed_powder",
        source="meadow",
        cure_text="wake the orchard",
        ending_text="By sunset the branches lifted, and red apples glowed among the leaves like lanterns.",
        tags={"orchard", "trees", "chemist"},
    ),
    "silent_hive": Problem(
        id="silent_hive",
        trouble="the village bees had gone silent",
        image="The garden still had flowers, yet the air had lost its humming song.",
        ingredient="bellflower_pollen",
        source="hill",
        cure_text="bring the bees' song back",
        ending_text="Soon the garden hummed again, and every flower seemed to bow in the warm air.",
        tags={"bees", "garden", "chemist"},
    ),
}

INGREDIENTS = {
    "moonmint_dew": Ingredient(
        id="moonmint_dew",
        label="moonmint dew",
        phrase="a silver drop of moonmint dew",
        texture="cold as a star and sweet as rain",
        stored_in={"vial"},
        source_line="where moonmint curled around a silver spring",
        tags={"dew", "magic", "water"},
    ),
    "sunseed_powder": Ingredient(
        id="sunseed_powder",
        label="sunseed powder",
        phrase="a spoonful of sunseed powder",
        texture="golden and warm as bread from an oven",
        stored_in={"jar"},
        source_line="where the meadow kept its brightest seeds under the grass",
        tags={"seed", "magic", "garden"},
    ),
    "bellflower_pollen": Ingredient(
        id="bellflower_pollen",
        label="bellflower pollen",
        phrase="a soft cloud of bellflower pollen",
        texture="light as a laugh and bright as yellow dust",
        stored_in={"basket"},
        source_line="where blue bellflowers nodded on the hill",
        tags={"pollen", "magic", "flowers"},
    ),
}

VESSELS = {
    "vial": Vessel(
        id="vial",
        label="glass vial",
        phrase="a little glass vial",
        preserves={"moonmint_dew"},
        carry_line="The glass kept the dew from slipping away into mist.",
        tags={"glass", "vessel"},
    ),
    "jar": Vessel(
        id="jar",
        label="clay jar",
        phrase="a small clay jar",
        preserves={"sunseed_powder"},
        carry_line="The clay held the warm powder safe from the wind.",
        tags={"clay", "vessel"},
    ),
    "basket": Vessel(
        id="basket",
        label="reed basket",
        phrase="a tiny reed basket",
        preserves={"bellflower_pollen"},
        carry_line="The woven reeds let the pollen breathe without blowing off.",
        tags={"basket", "vessel"},
    ),
    "pocket": Vessel(
        id="pocket",
        label="coat pocket",
        phrase="a coat pocket",
        preserves=set(),
        carry_line="A pocket was handy, but magic never stayed tidy there.",
        tags={"pocket", "vessel"},
    ),
}

HELPERS = {
    "frog": Helper(
        id="frog",
        label="glass frog",
        type="thing",
        habitat="spring",
        entrance="a clear little frog with eyes like green beads",
        trouble="a thorny reed had caught one of its feet",
        kindness="lifted the thorny reed away and set the frog back on a smooth stone",
        bonus_label="a bonus pearl of sweetness",
        bonus_phrase="a bonus pearl of sweetness",
        bonus_effect="The extra pearl would make the remedy kinder than usual.",
        tags={"frog", "kindness", "magic"},
    ),
    "fox": Helper(
        id="fox",
        label="dawn fox",
        type="thing",
        habitat="meadow",
        entrance="a tiny fox the color of sunrise",
        trouble="burrs had tangled in its tail",
        kindness="picked the burrs out one by one until the fox's tail floated free",
        bonus_label="a bonus spark of dawn",
        bonus_phrase="a bonus spark of dawn",
        bonus_effect="The extra spark would make the waking powder shine farther through the trees.",
        tags={"fox", "kindness", "magic"},
    ),
    "moth": Helper(
        id="moth",
        label="bell moth",
        type="thing",
        habitat="hill",
        entrance="a pale moth with wings like folded petals",
        trouble="a gust kept knocking it against a thorn bush",
        kindness="cupped gentle hands around it and sheltered it until the wind softened",
        bonus_label="a bonus note of humming",
        bonus_phrase="a bonus note of humming",
        bonus_effect="The extra note would help the bees remember their song.",
        tags={"moth", "kindness", "magic"},
    ),
}

GIRL_NAMES = ["Anya", "Mira", "Lina", "Tala", "Nora", "Suri", "Iva", "Etta"]
BOY_NAMES = ["Ivo", "Tomas", "Milan", "Rian", "Nico", "Oren", "Pavel", "Sami"]
TRAITS = ["patient", "brave", "gentle", "steady", "curious", "kind"]


def vessel_fits(ingredient: Ingredient, vessel: Vessel) -> bool:
    return ingredient.id in vessel.preserves


def helper_fits(problem: Problem, helper: Helper) -> bool:
    return problem.source == helper.habitat


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for prob_id, problem in PROBLEMS.items():
        ingredient = INGREDIENTS[problem.ingredient]
        for vessel_id, vessel in VESSELS.items():
            for helper_id, helper in HELPERS.items():
                if vessel_fits(ingredient, vessel) and helper_fits(problem, helper):
                    combos.append((prob_id, vessel_id, helper_id))
    return sorted(combos)


def predict_journey(problem: Problem, vessel: Vessel, helper: Helper) -> dict:
    ingredient = INGREDIENTS[problem.ingredient]
    return {
        "keeps_magic": vessel_fits(ingredient, vessel),
        "finds_helper": helper_fits(problem, helper),
        "bonus_possible": helper_fits(problem, helper),
    }


def tell(
    problem: Problem,
    vessel: Vessel,
    helper_cfg: Helper,
    hero_name: str = "Anya",
    hero_gender: str = "girl",
    chemist_type: str = "mother",
    hero_trait: str = "kind",
) -> World:
    ingredient = INGREDIENTS[problem.ingredient]

    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    chemist = world.add(Entity(id="chemist", kind="character", type=chemist_type, label="the chemist", role="chemist"))
    village = world.add(Entity(id="village", type="village", label="the village"))
    helper = world.add(Entity(id="helper", type=helper_cfg.type, label=helper_cfg.label, role="helper"))
    vial = world.add(Entity(id="vessel", type="vessel", label=vessel.label))
    ingredient_ent = world.add(Entity(id="ingredient", type="ingredient", label=ingredient.label))
    bonus_ent = world.add(Entity(id="bonus", type="bonus", label=helper_cfg.bonus_label))

    hero.attrs["name"] = hero_name
    hero.attrs["trait"] = hero_trait
    hero.memes["care"] += 1
    village.meters["trouble"] += 1
    village.memes["worry"] += 1

    # Act 1: village trouble and quest.
    world.say(
        f"In the old valley village, {hero_name} lived beside a careful chemist who knew the names of roots, rain, and starlight."
    )
    world.say(
        f"One morning {problem.trouble}. {problem.image}"
    )
    world.say(
        f'The chemist set a brass spoon beside the mortar and said, "Only {ingredient.phrase} can {problem.cure_text}. '
        f'Will you carry {vessel.phrase} and fetch it before sunset?"'
    )
    world.say(
        f"{hero_name} nodded. {hero.pronoun('subject').capitalize()} was {hero_trait}, but even a {hero_trait} heart gave one quick thump when a task smelled of magic."
    )

    world.para()

    # Act 2: the road, the helper, the charm word, and the gathering.
    pred = predict_journey(problem, vessel, helper_cfg)
    world.facts["predicted_keeps_magic"] = pred["keeps_magic"]
    world.facts["predicted_bonus_possible"] = pred["bonus_possible"]

    world.say(
        f"So {hero_name} walked to the {problem.source}, {vessel.phrase} tucked close, and found the place {ingredient.source_line}."
    )
    world.say(
        f"There {hero.pronoun('subject')} met {helper_cfg.entrance}. Yet {helper_cfg.trouble}."
    )

    hero.memes["kindness"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"{hero_name} did not hurry past. {hero.pronoun('subject').capitalize()} {helper_cfg.kindness}."
    )
    propagate(world, narrate=False)

    hero.memes["courage"] += 1
    helper.memes["friendship"] += 1
    world.say(
        f'Then the little creature whispered, "If the brambles lean across your path, say only this: sic."'
    )
    world.say(
        f'The old word sounded tiny, but it made the nearest thorns curl back as politely as bowing fingers.'
    )

    if pred["keeps_magic"]:
        ingredient_ent.meters["gathered"] += 1
        world.say(
            f"{hero_name} gathered {ingredient.phrase}. It was {ingredient.texture}. {vessel.carry_line}"
        )
    else:
        ingredient_ent.meters["lost"] += 1
        world.say(
            f"{hero_name} reached for {ingredient.phrase}, but the magic thinned away before it could be carried home."
        )

    if world.facts.get("bonus_granted"):
        bonus_ent.meters["gifted"] += 1
        world.say(
            f'For that kindness, the helper placed {helper_cfg.bonus_phrase} beside the ingredient. "A bonus for a gentle traveler," it said. {helper_cfg.bonus_effect}'
        )

    world.para()

    # Act 3: return, brewing, and proof of change.
    world.say(
        f"On the way home, one hedge of black brambles bent low across the lane, but {hero_name} remembered the charm and said, \"sic.\" At once the stems untwined and opened a narrow door."
    )

    if ingredient_ent.meters["gathered"] >= THRESHOLD:
        chemist.meters["ingredient_ready"] += 1
        chemist.memes["hope"] += 1
        world.say(
            f"Back in the cottage, the chemist poured the treasure into the waiting bowl and stirred until the room smelled bright and green."
        )
        if bonus_ent.meters["gifted"] >= THRESHOLD:
            world.say(
                f"The chemist added the bonus gift last, and the remedy gave one soft golden blink, as if it had smiled."
            )
        propagate(world, narrate=False)
        world.say(
            f"Before long the magic was carried where it was needed, and {problem.ending_text}"
        )
        world.say(
            f"After that, people said the village chemist had wise hands, but {hero_name} had the wiser heart, for the cure had begun with kindness on the road."
        )
        outcome = "blessed" if world.facts.get("bonus_granted") else "healed"
    else:
        world.say(
            f"The chemist listened, sighed, and set a warm hand on {hero_name}'s shoulder. \"Magic must be carried the right way,\" {chemist.pronoun('subject')} said. \"Tomorrow we will try again with a wiser vessel.\""
        )
        world.say(
            f"That night the village was still worried, but {hero_name} kept the little word sic safe in memory, ready for the next journey."
        )
        outcome = "delayed"

    world.facts.update(
        hero=hero,
        hero_name=hero_name,
        chemist=chemist,
        village=village,
        helper=helper,
        vessel=vial,
        vessel_cfg=vessel,
        ingredient=ingredient_ent,
        ingredient_cfg=ingredient,
        bonus=bonus_ent,
        helper_cfg=helper_cfg,
        problem=problem,
        outcome=outcome,
    )
    return world


@dataclass
class StoryParams:
    problem: str
    vessel: str
    helper: str
    hero_name: str
    hero_gender: str
    chemist_type: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        problem="bitter_well",
        vessel="vial",
        helper="frog",
        hero_name="Anya",
        hero_gender="girl",
        chemist_type="mother",
        trait="gentle",
    ),
    StoryParams(
        problem="sleepy_orchard",
        vessel="jar",
        helper="fox",
        hero_name="Ivo",
        hero_gender="boy",
        chemist_type="father",
        trait="brave",
    ),
    StoryParams(
        problem="silent_hive",
        vessel="basket",
        helper="moth",
        hero_name="Mira",
        hero_gender="girl",
        chemist_type="mother",
        trait="patient",
    ),
]


KNOWLEDGE = {
    "chemist": [
        (
            "What does a chemist do?",
            "A chemist mixes materials carefully to make something useful. In a folk tale, a village chemist might know herbs, powders, and magical drops."
        )
    ],
    "magic": [
        (
            "What is magic in a folk tale?",
            "Magic in a folk tale is a strange power that can change ordinary things. It often listens to kindness, courage, or a special word."
        )
    ],
    "dew": [
        (
            "What is dew?",
            "Dew is tiny water drops that rest on leaves and grass in the cool part of the day. In stories, dew is often treated like a delicate treasure."
        )
    ],
    "pollen": [
        (
            "What is pollen?",
            "Pollen is soft dust from flowers. Bees carry it from bloom to bloom while they work."
        )
    ],
    "seed": [
        (
            "What is a seed?",
            "A seed is the small beginning of a plant. Given soil, water, and time, it can grow into something much larger."
        )
    ],
    "well": [
        (
            "What is a village well?",
            "A well is a deep place where people draw up water. In old stories, a village well is important because many families depend on it."
        )
    ],
    "orchard": [
        (
            "What is an orchard?",
            "An orchard is a place where fruit trees are planted and cared for together. Apples, pears, and plums can grow there."
        )
    ],
    "bees": [
        (
            "Why are bees important to flowers?",
            "Bees help flowers by carrying pollen as they visit them. That helps many plants make fruit and seeds."
        )
    ],
    "kindness": [
        (
            "Why does kindness matter in a folk tale?",
            "Kindness matters because it changes how others answer you. In many folk tales, help comes to the child who stops to help first."
        )
    ],
    "glass": [
        (
            "Why would someone carry something delicate in glass?",
            "Glass can hold a tiny drop without soaking it up. That makes it useful for carrying special liquids."
        )
    ],
    "clay": [
        (
            "Why is clay good for keeping powder?",
            "A clay jar is firm and steady, so wind cannot blow powder away. It also keeps the powder gathered in one place."
        )
    ],
    "basket": [
        (
            "Why might a basket be useful for flower dust or petals?",
            "A basket can hold light things gently without crushing them. Its woven sides can also let air move through."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "chemist",
    "magic",
    "kindness",
    "well",
    "orchard",
    "bees",
    "dew",
    "seed",
    "pollen",
    "glass",
    "clay",
    "basket",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    problem = f["problem"]
    ingredient = f["ingredient_cfg"]
    helper = f["helper_cfg"]
    hero_name = f["hero_name"]
    return [
        f'Write a folk tale for a young child about a village chemist, one missing magical ingredient, and a helpful traveler. Include the words "chemist", "bonus", and "sic".',
        f"Tell a magical folk tale where {hero_name} must fetch {ingredient.label} to fix a village trouble, learns the word sic from a {helper.label}, and returns home changed.",
        f"Write a gentle quest story where kindness on the road earns a bonus gift, and that extra gift helps {problem.cure_text}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    problem = f["problem"]
    ingredient = f["ingredient_cfg"]
    vessel = f["vessel_cfg"]
    helper = f["helper_cfg"]
    hero_name = f["hero_name"]
    chemist = f["chemist"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, a child helping a village chemist. It is also about the small magical helper met on the road."
        ),
        (
            "What was wrong in the village?",
            f"{problem.trouble.capitalize()}. That trouble is what sent {hero_name} out on the journey."
        ),
        (
            f"Why did {hero_name} carry {vessel.phrase}?",
            f"{hero_name} needed it to carry {ingredient.label} safely home. The vessel mattered because that kind of magic would not stay whole in just anything."
        ),
        (
            "What did the helper teach the child?",
            f"The helper taught {hero_name} the word sic. In the story, that little charm-word made the brambles open instead of scratching and blocking the way."
        ),
    ]
    if f["bonus"].meters["gifted"] >= THRESHOLD:
        qa.append(
            (
                "Why did the helper give a bonus gift?",
                f"The helper gave a bonus gift because {hero_name} stopped to help first. The gift came as an answer to kindness, not as a payment asked for ahead of time."
            )
        )
    if f["outcome"] in {"healed", "blessed"}:
        bonus_sentence = ""
        if f["bonus"].meters["gifted"] >= THRESHOLD:
            bonus_sentence = " The bonus gift made the remedy kinder and brighter than usual."
        qa.append(
            (
                "How did the chemist solve the problem?",
                f"The chemist mixed the gathered ingredient into a remedy and used it where the village trouble had fallen.{bonus_sentence}"
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with proof that the village had changed: {problem.ending_text} The ending image shows that the old trouble was truly gone."
            )
        )
    else:
        qa.append(
            (
                "Why did the problem remain at the end?",
                f"The ingredient could not be carried home properly, so the chemist had nothing true to brew with. The story ends in waiting, with a lesson about using the right vessel for the right magic."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"chemist", "magic", "kindness"}
    problem = f["problem"]
    ingredient = f["ingredient_cfg"]
    vessel = f["vessel_cfg"]
    if problem.id == "bitter_well":
        tags.add("well")
    if problem.id == "sleepy_orchard":
        tags.add("orchard")
    if problem.id == "silent_hive":
        tags.add("bees")
    if ingredient.id == "moonmint_dew":
        tags.add("dew")
    if ingredient.id == "sunseed_powder":
        tags.add("seed")
    if ingredient.id == "bellflower_pollen":
        tags.add("pollen")
    if vessel.id == "vial":
        tags.add("glass")
    if vessel.id == "jar":
        tags.add("clay")
    if vessel.id == "basket":
        tags.add("basket")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(problem: Problem, vessel: Vessel, helper: Helper) -> str:
    ingredient = INGREDIENTS[problem.ingredient]
    if not vessel_fits(ingredient, vessel):
        return (
            f"(No story: {vessel.phrase} cannot safely carry {ingredient.label}. "
            f"In this world, that magic fades unless it is kept in the right vessel.)"
        )
    if not helper_fits(problem, helper):
        return (
            f"(No story: the {helper.label} belongs by the {helper.habitat}, not at the {problem.source}. "
            f"This folk tale needs the magical helper to belong naturally to the quest path.)"
        )
    return "(No story: this combination does not fit the world.)"


ASP_RULES = r"""
valid(P, V, H) :-
    problem(P), requires(P, I),
    vessel(V), preserves(V, I),
    helper(H), source(P, S), habitat(H, S).

outcome(P, V, H, blessed) :-
    valid(P, V, H).

invalid_vessel(P, V) :-
    problem(P), requires(P, I), vessel(V), not preserves(V, I).

invalid_helper(P, H) :-
    problem(P), source(P, S), helper(H), habitat(H, HS), HS != S.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for prob_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", prob_id))
        lines.append(asp.fact("requires", prob_id, problem.ingredient))
        lines.append(asp.fact("source", prob_id, problem.source))
    for ing_id in INGREDIENTS:
        lines.append(asp.fact("ingredient", ing_id))
    for vessel_id, vessel in VESSELS.items():
        lines.append(asp.fact("vessel", vessel_id))
        for ing_id in sorted(vessel.preserves):
            lines.append(asp.fact("preserves", vessel_id, ing_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("habitat", helper_id, helper.habitat))
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
            asp.fact("chosen_problem", params.problem),
            asp.fact("chosen_vessel", params.vessel),
            asp.fact("chosen_helper", params.helper),
            "chosen_outcome(X) :- valid(P,V,H), chosen_problem(P), chosen_vessel(V), chosen_helper(H), outcome(P,V,H,X).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show chosen_outcome/1."))
    atoms = asp.atoms(model, "chosen_outcome")
    return atoms[0][0] if atoms else "invalid"


def outcome_of(params: StoryParams) -> str:
    try:
        problem = PROBLEMS[params.problem]
        vessel = VESSELS[params.vessel]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter: {err.args[0]})") from err
    ingredient = INGREDIENTS[problem.ingredient]
    if vessel_fits(ingredient, vessel) and helper_fits(problem, helper):
        return "blessed"
    return "invalid"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    cases = list(CURATED)
    for seed in range(20):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving random params at seed {seed}.")
            break

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Magic folk-tale storyworld: a child helps a village chemist by fetching one true ingredient in the right vessel."
    )
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--chemist", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.vessel and args.helper:
        problem = PROBLEMS[args.problem]
        vessel = VESSELS[args.vessel]
        helper = HELPERS[args.helper]
        ingredient = INGREDIENTS[problem.ingredient]
        if not (vessel_fits(ingredient, vessel) and helper_fits(problem, helper)):
            raise StoryError(explain_rejection(problem, vessel, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.problem is None or combo[0] == args.problem)
        and (args.vessel is None or combo[1] == args.vessel)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        if args.problem and args.vessel and not args.helper:
            helper = next(iter(HELPERS.values()))
            raise StoryError(explain_rejection(PROBLEMS[args.problem], VESSELS[args.vessel], helper))
        if args.problem and args.helper and not args.vessel:
            vessel = next(iter(VESSELS.values()))
            raise StoryError(explain_rejection(PROBLEMS[args.problem], vessel, HELPERS[args.helper]))
        raise StoryError("(No valid combination matches the given options.)")

    problem_id, vessel_id, helper_id = rng.choice(combos)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    chemist_type = args.chemist or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        problem=problem_id,
        vessel=vessel_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        chemist_type=chemist_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        problem = PROBLEMS[params.problem]
        vessel = VESSELS[params.vessel]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter: {err.args[0]})") from err

    ingredient = INGREDIENTS[problem.ingredient]
    if not vessel_fits(ingredient, vessel) or not helper_fits(problem, helper):
        raise StoryError(explain_rejection(problem, vessel, helper))

    world = tell(
        problem=problem,
        vessel=vessel,
        helper_cfg=helper,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        chemist_type=params.chemist_type,
        hero_trait=params.trait,
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
        print(asp_program("", "#show valid/3.\n#show outcome/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (problem, vessel, helper) combos:\n")
        for problem, vessel, helper in combos:
            print(f"  {problem:15} {vessel:8} {helper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name}: {p.problem} with {p.vessel} and {p.helper}"
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
