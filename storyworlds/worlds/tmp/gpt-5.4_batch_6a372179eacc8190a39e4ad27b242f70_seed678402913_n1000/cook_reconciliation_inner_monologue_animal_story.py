#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cook_reconciliation_inner_monologue_animal_story.py
==============================================================================

A small animal-story world about two young cooks who hurt each other's feelings,
then make things right. One animal secretly changes a recipe, the food goes off
balance, and an inner monologue helps the guilty cook decide to tell the truth.
The ending always includes reconciliation; the meal is either saved or begun
again together.

Run it
------
python storyworlds/worlds/gpt-5.4/cook_reconciliation_inner_monologue_animal_story.py
python storyworlds/worlds/gpt-5.4/cook_reconciliation_inner_monologue_animal_story.py --dish soup --mistake too_much_salt
python storyworlds/worlds/gpt-5.4/cook_reconciliation_inner_monologue_animal_story.py --repair extra_oats
python storyworlds/worlds/gpt-5.4/cook_reconciliation_inner_monologue_animal_story.py --all
python storyworlds/worlds/gpt-5.4/cook_reconciliation_inner_monologue_animal_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/cook_reconciliation_inner_monologue_animal_story.py --verify
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
        gender = self.attrs.get("gender", "neutral")
        if gender == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Dish:
    id: str
    label: str = ""
    phrase: str = ""
    vessel: str = ""
    smell: str = ""
    serving: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Mistake:
    id: str
    label: str = ""
    ingredient: str = ""
    effect: str = ""
    action: str = ""
    result_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str = ""
    method: str = ""
    action: str = ""
    supports: set[tuple[str, str]] = field(default_factory=set)
    power: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Home:
    id: str
    place: str = ""
    detail: str = ""
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


def _r_off_balance(world: World) -> list[str]:
    out: list[str] = []
    pot = world.get("dish")
    if pot.meters["off_balance"] < THRESHOLD:
        return out
    sig = ("off_balance",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for eid in ("cook", "friend"):
        world.get(eid).memes["worry"] += 1
    out.append("__worry__")
    return out


def _r_silence(world: World) -> list[str]:
    cook = world.get("cook")
    friend = world.get("friend")
    if cook.memes["guilt"] < THRESHOLD or friend.memes["hurt"] < THRESHOLD:
        return []
    sig = ("silence",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("room").memes["silence"] += 1
    return ["__silence__"]


def _r_reconcile(world: World) -> list[str]:
    cook = world.get("cook")
    friend = world.get("friend")
    if cook.memes["apology"] < THRESHOLD or friend.memes["listening"] < THRESHOLD:
        return []
    sig = ("reconcile",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cook.memes["relief"] += 1
    friend.memes["forgiveness"] += 1
    cook.memes["closeness"] += 1
    friend.memes["closeness"] += 1
    friend.memes["hurt"] = 0.0
    cook.memes["guilt"] = 0.0
    return ["__reconcile__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="off_balance", tag="physical", apply=_r_off_balance),
    Rule(name="silence", tag="social", apply=_r_silence),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
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
        for sent in produced:
            world.say(sent)
    return produced


def compatible(dish_id: str, mistake_id: str, repair_id: str) -> bool:
    return (dish_id, mistake_id) in REPAIRS[repair_id].supports


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for dish_id in DISHES:
        for mistake_id in MISTAKES:
            for repair_id, repair in REPAIRS.items():
                if (dish_id, mistake_id) in repair.supports:
                    combos.append((dish_id, mistake_id, repair_id))
    return sorted(combos)


def outcome_of(params: "StoryParams") -> str:
    repair = REPAIRS[params.repair]
    return "saved" if repair.power >= params.severity else "fresh_start"


def explain_rejection(dish_id: str, mistake_id: str, repair_id: str) -> str:
    dish = DISHES[dish_id]
    mistake = MISTAKES[mistake_id]
    repair = REPAIRS[repair_id]
    return (
        f"(No story: {repair.label} is not a sensible way to fix {mistake.label} in "
        f"{dish.label}. Pick a repair that really fits the dish and the mistake.)"
    )


def predict_flavor(world: World, mistake: Mistake) -> dict:
    sim = world.copy()
    dish = sim.get("dish")
    dish.meters["off_balance"] += 1
    dish.meters[mistake.effect] += 1
    propagate(sim, narrate=False)
    return {
        "off_balance": dish.meters["off_balance"],
        "worry": sim.get("cook").memes["worry"] + sim.get("friend").memes["worry"],
    }


def introduce(world: World, cook: Entity, friend: Entity, home: Home) -> None:
    relation = cook.attrs.get("relation", "friends")
    if relation == "siblings":
        relation_phrase = "brother and sister" if cook.attrs.get("gender") != friend.attrs.get("gender") else "two siblings"
    else:
        relation_phrase = "two good friends"
    world.say(
        f"In {home.place}, {cook.id} the {cook.attrs['species']} and {friend.id} the "
        f"{friend.attrs['species']} were {relation_phrase} who loved to cook together."
    )
    world.say(home.detail)


def plan_meal(world: World, cook: Entity, friend: Entity, dish_cfg: Dish) -> None:
    cook.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"That afternoon they decided to cook {dish_cfg.phrase}. Soon the {dish_cfg.vessel} "
        f"was warm, and {dish_cfg.smell} drifted through the room."
    )
    world.say(
        f'"Stir while I count the berries," {friend.id} said, and {cook.id} stood on tiptoe, '
        f"proud to help."
    )


def secret_choice(world: World, cook: Entity, dish_cfg: Dish, mistake: Mistake) -> None:
    pred = predict_flavor(world, mistake)
    world.facts["predicted_worry"] = pred["worry"]
    cook.memes["impulse"] += 1
    world.say(
        f"But when {friend_name(world)} turned away for one moment, {cook.id} reached for the "
        f"{mistake.ingredient} and {mistake.action}."
    )
    world.say(
        f'{cook.id} thought, "If a little is good, maybe more will make our {dish_cfg.label} even better."'
    )


def spoil_dish(world: World, mistake: Mistake, severity: int) -> None:
    dish = world.get("dish")
    dish.meters["off_balance"] += 1
    dish.meters[mistake.effect] += float(severity)
    dish.meters["troubled"] += 1
    propagate(world, narrate=False)


def discovery(world: World, cook: Entity, friend: Entity, dish_cfg: Dish, mistake: Mistake) -> None:
    friend.memes["hurt"] += 1
    cook.memes["guilt"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When {friend.id} tasted the spoon, {friend.pronoun('possessive')} ears drooped. "
        f'"Oh," {friend.pronoun()} said softly. "{dish_cfg.label.capitalize()} should not taste like this."'
    )
    world.say(mistake.result_line)
    world.say(
        f"{friend.id} looked at {cook.id}, not angry, just sad that the plan they had made together "
        f"had been changed."
    )


def inner_monologue(world: World, cook: Entity, friend: Entity) -> None:
    world.say(
        f"{cook.id}'s paws felt hot. {cook.pronoun().capitalize()} looked at the floor and thought, "
        f'"I wanted to be a clever cook, but now {friend.id} is hurt. If I hide what I did, the pot '
        f'will stay wrong and my heart will stay twisty too."'
    )
    if world.get("room").memes["silence"] >= THRESHOLD:
        world.say(
            f"For one tiny moment the kitchen was quiet except for the simmering pot, and that quiet "
            f"made {cook.id} feel even smaller."
        )


def confess(world: World, cook: Entity, friend: Entity, mistake: Mistake) -> None:
    cook.memes["apology"] += 1
    friend.memes["listening"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I did it," {cook.id} whispered at last. "I added extra {mistake.ingredient} because I wanted '
        f'to be a better cook. I should have asked you first. I am sorry."'
    )
    world.say(
        f"{friend.id} took a slow breath and listened all the way to the end."
    )


def repair_saved(world: World, cook: Entity, friend: Entity, dish_cfg: Dish, repair: Repair) -> None:
    dish = world.get("dish")
    dish.meters["off_balance"] = 0.0
    dish.meters["mended"] += 1
    cook.memes["helping"] += 1
    friend.memes["helping"] += 1
    world.say(
        f'"Thank you for telling me," {friend.id} said. "We can still fix it together."'
    )
    world.say(
        f"Side by side they {repair.action}. The smell turned gentle again, and the {dish_cfg.label} "
        f"began to taste right."
    )
    world.say(
        f"When they finally shared {dish_cfg.serving}, the first warm bite felt like a little yes between them."
    )


def repair_fresh_start(world: World, cook: Entity, friend: Entity, dish_cfg: Dish, repair: Repair) -> None:
    dish = world.get("dish")
    dish.meters["off_balance"] = 0.0
    dish.meters["scrapped"] += 1
    dish.meters["fresh_start"] += 1
    cook.memes["helping"] += 1
    friend.memes["helping"] += 1
    world.say(
        f'"Thank you for telling me," {friend.id} said. "This pot is too far gone, but we are not."'
    )
    world.say(
        f"They tried {repair.method}, then tasted again and knew the flavor was still wrong. So they poured "
        f"the first batch out for the compost and began a new one, this time counting every pinch together."
    )
    world.say(
        f"The second {dish_cfg.label} bubbled up slowly, and by the time they shared {dish_cfg.serving}, "
        f"their shoulders were touching again."
    )


def ending_image(world: World, cook: Entity, friend: Entity, dish_cfg: Dish, home: Home) -> None:
    world.say(
        f"Outside, the leaves whispered around {home.place}, but inside the little kitchen the two young "
        f"cooks sat close, licking the last taste from their spoons and smiling at the same happy pot."
    )


def friend_name(world: World) -> str:
    return world.get("friend").id


def tell(
    dish_cfg: Dish,
    mistake: Mistake,
    repair: Repair,
    home: Home,
    cook_name: str = "Pip",
    cook_species: str = "mouse",
    cook_gender: str = "boy",
    friend_name_value: str = "Mira",
    friend_species: str = "rabbit",
    friend_gender: str = "girl",
    relation: str = "friends",
    severity: int = 1,
) -> World:
    world = World()
    cook = world.add(Entity(
        id=cook_name,
        kind="character",
        type="animal",
        role="cook",
        attrs={"species": cook_species, "gender": cook_gender, "relation": relation},
    ))
    friend = world.add(Entity(
        id=friend_name_value,
        kind="character",
        type="animal",
        role="friend",
        attrs={"species": friend_species, "gender": friend_gender, "relation": relation},
    ))
    world.add(Entity(id="room", kind="thing", type="room", label="kitchen"))
    dish = world.add(Entity(
        id="dish",
        kind="thing",
        type="food",
        label=dish_cfg.label,
        phrase=dish_cfg.phrase,
        tags=set(dish_cfg.tags),
    ))

    introduce(world, cook, friend, home)
    plan_meal(world, cook, friend, dish_cfg)

    world.para()
    secret_choice(world, cook, dish_cfg, mistake)
    spoil_dish(world, mistake, severity)
    discovery(world, cook, friend, dish_cfg, mistake)

    world.para()
    inner_monologue(world, cook, friend)
    confess(world, cook, friend, mistake)

    world.para()
    if repair.power >= severity:
        repair_saved(world, cook, friend, dish_cfg, repair)
        outcome = "saved"
    else:
        repair_fresh_start(world, cook, friend, dish_cfg, repair)
        outcome = "fresh_start"
    ending_image(world, cook, friend, dish_cfg, home)

    world.facts.update(
        cook=cook,
        friend=friend,
        dish_cfg=dish_cfg,
        mistake=mistake,
        repair=repair,
        home=home,
        relation=relation,
        severity=severity,
        outcome=outcome,
        repaired=outcome == "saved",
        reconciled=friend.memes["forgiveness"] >= THRESHOLD,
        inner_truth=True,
    )
    return world


DISHES = {
    "soup": Dish(
        id="soup",
        label="soup",
        phrase="carrot soup with little green peas",
        vessel="round blue pot",
        smell="the sweet smell of carrots and onions",
        serving="two steaming bowls on the windowsill",
        tags={"cook", "soup"},
    ),
    "porridge": Dish(
        id="porridge",
        label="porridge",
        phrase="warm berry porridge",
        vessel="small silver pot",
        smell="the cozy smell of oats and berries",
        serving="two soft bowls with berry swirls on top",
        tags={"cook", "porridge"},
    ),
    "stew": Dish(
        id="stew",
        label="stew",
        phrase="mushroom stew with tiny herb leaves",
        vessel="deep red pot",
        smell="the earthy smell of mushrooms and herbs",
        serving="two wooden bowls by the fire",
        tags={"cook", "stew"},
    ),
}

MISTAKES = {
    "too_much_salt": Mistake(
        id="too_much_salt",
        label="too much salt",
        ingredient="salt",
        effect="salty",
        action="shook in a great fluttering sprinkle",
        result_line="The soup had gone sharp and salty, and even the steam seemed surprised.",
        tags={"salt", "taste"},
    ),
    "too_much_honey": Mistake(
        id="too_much_honey",
        label="too much honey",
        ingredient="honey",
        effect="too_sweet",
        action="let a heavy ribbon of honey slip into the pot",
        result_line="The porridge had turned so sweet that the berry taste was almost hiding.",
        tags={"honey", "taste"},
    ),
    "too_much_flour": Mistake(
        id="too_much_flour",
        label="too much flour",
        ingredient="flour",
        effect="too_thick",
        action="tipped in an extra scoop of flour",
        result_line="The stew had grown thick and pasty, with a spoon that wanted to stand up by itself.",
        tags={"flour", "texture"},
    ),
}

REPAIRS = {
    "water_potato": Repair(
        id="water_potato",
        label="extra water and potato",
        method="adding extra water and potato",
        action="added extra water and one chopped potato, then stirred slowly until the salt spread out",
        supports={("soup", "too_much_salt"), ("stew", "too_much_salt")},
        power=2,
        tags={"repair", "soup"},
    ),
    "extra_oats": Repair(
        id="extra_oats",
        label="more oats and milk",
        method="stirring in more oats and milk",
        action="stirred in more oats and a splash of milk so the honey had room to calm down",
        supports={("porridge", "too_much_honey")},
        power=2,
        tags={"repair", "porridge"},
    ),
    "warm_broth": Repair(
        id="warm_broth",
        label="warm broth",
        method="loosening it with warm broth",
        action="poured in warm broth a little at a time until the spoon could glide again",
        supports={("soup", "too_much_flour"), ("stew", "too_much_flour")},
        power=1,
        tags={"repair", "stew"},
    ),
    "extra_berries": Repair(
        id="extra_berries",
        label="extra berries",
        method="cooking in more berries",
        action="cooked in a handful of tart berries, and soon the sweetness stopped shouting",
        supports={("porridge", "too_much_honey")},
        power=1,
        tags={"repair", "berries"},
    ),
}

HOMES = {
    "burrow": Home(
        id="burrow",
        place="a snug burrow under the hill",
        detail="A fern-framed window let in a stripe of sun, and the spoon rack clicked softly whenever the floorboards hummed.",
        tags={"home"},
    ),
    "treehouse": Home(
        id="treehouse",
        place="a treehouse tucked in an old oak",
        detail="The little stove ticked in the corner, and acorn cups lined the shelf like patient helpers.",
        tags={"home"},
    ),
    "hollow": Home(
        id="hollow",
        place="a warm hollow inside a willow tree",
        detail="Curtains made of sewn leaves swayed by the round doorway, and everything smelled faintly of woodsmoke and jam.",
        tags={"home"},
    ),
}

ANIMALS = [
    ("Pip", "mouse", "boy"),
    ("Mira", "rabbit", "girl"),
    ("Tomo", "raccoon", "boy"),
    ("Wren", "fox", "girl"),
    ("Nell", "squirrel", "girl"),
    ("Bram", "badger", "boy"),
    ("Lulu", "otter", "girl"),
    ("Odo", "hedgehog", "boy"),
]


@dataclass
class StoryParams:
    dish: str
    mistake: str
    repair: str
    home: str
    cook_name: str
    cook_species: str
    cook_gender: str
    friend_name: str
    friend_species: str
    friend_gender: str
    relation: str
    severity: int = 1
    seed: Optional[int] = None


KNOWLEDGE = {
    "cook": [
        (
            "What does it mean to cook?",
            "To cook means to make food by heating it or mixing ingredients together. A cook has to pay attention because small changes can make the food taste different.",
        )
    ],
    "salt": [
        (
            "Why can too much salt be a problem?",
            "Salt can help food taste good in a small amount, but too much makes the food sharp and unpleasant. Then the other flavors are hard to taste.",
        )
    ],
    "honey": [
        (
            "Why can too much honey change a dish?",
            "Honey is very sweet, so too much of it can cover up the other flavors. A food that was meant to taste balanced can start tasting only sweet.",
        )
    ],
    "flour": [
        (
            "What happens if you add too much flour?",
            "Too much flour can make food thick and heavy. It can change a smooth soup or stew into something pasty.",
        )
    ],
    "repair": [
        (
            "What can a cook do when food goes wrong?",
            "A cook can slow down, taste carefully, and try a sensible fix. Sometimes the best fix is to start again and use the mistake as a lesson.",
        )
    ],
    "apology": [
        (
            "What is a good apology?",
            "A good apology says what you did, shows you understand the hurt, and tries to make things better. It is stronger when you tell the truth without making excuses.",
        )
    ],
    "feelings": [
        (
            "Why can telling the truth fix a friendship?",
            "Telling the truth helps the other person know you respect them. It does not erase the mistake, but it opens the door for trust and repair.",
        )
    ],
    "soup": [
        (
            "What is soup?",
            "Soup is a soft food made in a pot, often with vegetables or broth. It is warm and easy to stir while the flavors blend together.",
        )
    ],
    "porridge": [
        (
            "What is porridge?",
            "Porridge is a soft warm food made from grains like oats cooked with liquid. It can be plain or mixed with fruit or honey.",
        )
    ],
    "stew": [
        (
            "What is stew?",
            "Stew is a thick cooked dish with pieces of food simmered together in a pot. As it cooks, the flavors mix and grow deeper.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "cook",
    "salt",
    "honey",
    "flour",
    "repair",
    "apology",
    "feelings",
    "soup",
    "porridge",
    "stew",
]


CURATED = [
    StoryParams(
        dish="soup",
        mistake="too_much_salt",
        repair="water_potato",
        home="burrow",
        cook_name="Pip",
        cook_species="mouse",
        cook_gender="boy",
        friend_name="Mira",
        friend_species="rabbit",
        friend_gender="girl",
        relation="friends",
        severity=1,
    ),
    StoryParams(
        dish="porridge",
        mistake="too_much_honey",
        repair="extra_oats",
        home="treehouse",
        cook_name="Lulu",
        cook_species="otter",
        cook_gender="girl",
        friend_name="Odo",
        friend_species="hedgehog",
        friend_gender="boy",
        relation="siblings",
        severity=2,
    ),
    StoryParams(
        dish="stew",
        mistake="too_much_flour",
        repair="warm_broth",
        home="hollow",
        cook_name="Bram",
        cook_species="badger",
        cook_gender="boy",
        friend_name="Nell",
        friend_species="squirrel",
        friend_gender="girl",
        relation="friends",
        severity=2,
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cook = f["cook"]
    friend = f["friend"]
    dish_cfg = f["dish_cfg"]
    mistake = f["mistake"]
    outcome = f["outcome"]
    end = "save the meal together" if outcome == "saved" else "start again together after an honest apology"
    return [
        'Write an animal story for a 3-to-5-year-old that includes the word "cook" and uses inner monologue and reconciliation.',
        f"Tell a gentle story where {cook.id} the {cook.attrs['species']} and {friend.id} the {friend.attrs['species']} try to cook {dish_cfg.label}, but {cook.id} makes a secret mistake with {mistake.ingredient} and then has to tell the truth.",
        f"Write a small kitchen story with hurt feelings, a spoken apology, and an ending where two young animal cooks {end}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    cook = f["cook"]
    friend = f["friend"]
    dish_cfg = f["dish_cfg"]
    mistake = f["mistake"]
    repair = f["repair"]
    outcome = f["outcome"]
    relation = f["relation"]
    relation_word = "siblings" if relation == "siblings" else "friends"
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {cook.id} the {cook.attrs['species']} and {friend.id} the {friend.attrs['species']}, two {relation_word} who wanted to cook together.",
        ),
        (
            f"What were they trying to cook?",
            f"They were making {dish_cfg.phrase}. The warm pot and good smell showed that they began the afternoon happily.",
        ),
        (
            f"What mistake did {cook.id} make?",
            f"{cook.id} secretly added too much {mistake.ingredient}. {cook.pronoun('subject').capitalize()} thought more might make the food better, but it pushed the dish out of balance.",
        ),
        (
            f"Why were {friend.id}'s feelings hurt?",
            f"{friend.id} was sad because the recipe they had planned together was changed in secret. The hurt was not only about the taste; it was also about trust.",
        ),
        (
            f"What did {cook.id} think about before telling the truth?",
            f"{cook.id} had an inner monologue and realized that hiding the mistake would keep both the pot and {cook.pronoun('possessive')} heart wrong. That thought gave {cook.pronoun('object')} the courage to confess and apologize.",
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                "How did they solve the problem?",
                f"They worked side by side and fixed the dish by {repair.method}. Because they repaired the food together after the apology, the meal and the friendship both felt mended.",
            )
        )
    else:
        qa.append(
            (
                "How did they solve the problem?",
                f"They tried {repair.method}, but the first batch was still wrong, so they started again together. The new pot mattered because it showed they trusted each other enough to begin fresh.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the two young cooks sitting close and sharing {dish_cfg.serving}. The final image shows that the quarrel was over and their closeness had come back.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"cook", "repair", "apology", "feelings", f["dish_cfg"].id}
    tags |= set(f["mistake"].tags)
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:6}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(D, M, R) :- dish(D), mistake(M), repair(R), supports(R, D, M).

saved :- chosen_repair(R), power(R, P), severity(S), P >= S.
fresh_start :- chosen_repair(R), power(R, P), severity(S), P < S.

outcome(saved) :- saved.
outcome(fresh_start) :- fresh_start.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for dish_id in DISHES:
        lines.append(asp.fact("dish", dish_id))
    for mistake_id in MISTAKES:
        lines.append(asp.fact("mistake", mistake_id))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("power", repair_id, repair.power))
        for dish_id, mistake_id in sorted(repair.supports):
            lines.append(asp.fact("supports", repair_id, dish_id, mistake_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_repair", params.repair),
        asp.fact("severity", params.severity),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_emit(sample: StorySample) -> None:
    if not isinstance(sample.story, str) or not sample.story.strip():
        raise StoryError("(Smoke test failed: empty story.)")
    if "cook" not in sample.story.lower():
        raise StoryError('(Smoke test failed: story does not contain the word "cook".)')


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
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
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
        _smoke_emit(smoke)
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - defensive verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal kitchen storyworld: a secret cooking mistake, inner thoughts, and reconciliation."
    )
    ap.add_argument("--dish", choices=sorted(DISHES))
    ap.add_argument("--mistake", choices=sorted(MISTAKES))
    ap.add_argument("--repair", choices=sorted(REPAIRS))
    ap.add_argument("--home", choices=sorted(HOMES))
    ap.add_argument("--relation", choices=["friends", "siblings"])
    ap.add_argument("--severity", type=int, choices=[1, 2], help="how hard the mistake is to fix")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_pair(rng: random.Random) -> tuple[tuple[str, str, str], tuple[str, str, str]]:
    first = rng.choice(ANIMALS)
    second = rng.choice([a for a in ANIMALS if a[0] != first[0]])
    return first, second


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.dish and args.mistake and args.repair:
        if not compatible(args.dish, args.mistake, args.repair):
            raise StoryError(explain_rejection(args.dish, args.mistake, args.repair))

    combos = [
        combo for combo in valid_combos()
        if (args.dish is None or combo[0] == args.dish)
        and (args.mistake is None or combo[1] == args.mistake)
        and (args.repair is None or combo[2] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    dish_id, mistake_id, repair_id = rng.choice(combos)
    home_id = args.home or rng.choice(sorted(HOMES))
    relation = args.relation or rng.choice(["friends", "siblings"])
    severity = args.severity if args.severity is not None else rng.choice([1, 2])
    first, second = _pick_pair(rng)
    return StoryParams(
        dish=dish_id,
        mistake=mistake_id,
        repair=repair_id,
        home=home_id,
        cook_name=first[0],
        cook_species=first[1],
        cook_gender=first[2],
        friend_name=second[0],
        friend_species=second[1],
        friend_gender=second[2],
        relation=relation,
        severity=severity,
    )


def generate(params: StoryParams) -> StorySample:
    if params.dish not in DISHES:
        raise StoryError(f"(Unknown dish: {params.dish})")
    if params.mistake not in MISTAKES:
        raise StoryError(f"(Unknown mistake: {params.mistake})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")
    if params.home not in HOMES:
        raise StoryError(f"(Unknown home: {params.home})")
    if not compatible(params.dish, params.mistake, params.repair):
        raise StoryError(explain_rejection(params.dish, params.mistake, params.repair))

    world = tell(
        dish_cfg=DISHES[params.dish],
        mistake=MISTAKES[params.mistake],
        repair=REPAIRS[params.repair],
        home=HOMES[params.home],
        cook_name=params.cook_name,
        cook_species=params.cook_species,
        cook_gender=params.cook_gender,
        friend_name_value=params.friend_name,
        friend_species=params.friend_species,
        friend_gender=params.friend_gender,
        relation=params.relation,
        severity=params.severity,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (dish, mistake, repair) combos:\n")
        for dish_id, mistake_id, repair_id in combos:
            print(f"  {dish_id:8} {mistake_id:16} {repair_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.cook_name} and {p.friend_name}: {p.dish}, {p.mistake}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
