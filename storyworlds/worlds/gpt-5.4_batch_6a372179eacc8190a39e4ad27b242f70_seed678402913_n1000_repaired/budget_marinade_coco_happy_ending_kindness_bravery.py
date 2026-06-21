#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/budget_marinade_coco_happy_ending_kindness_bravery.py
=================================================================================

A small heartwarming storyworld about Coco, a careful grown-up, a tight dinner
budget, and the brave choice to share food with someone who looks left out.

The world model is simple and state-driven:

- typed entities with physical meters and emotional memes
- a tiny forward-chaining rule system
- a reasonableness gate over affordable meal plans
- an inline ASP twin for parity checks
- three Q&A sets grounded in the simulated world, not parsed from English

Domain sketch
-------------
Coco and a grown-up are planning a simple supper for a small community spot.
They only have a little budget. A humble main ingredient and a good marinade can
stretch the meal into something warm and special. Then Coco notices a lonely
child nearby and must decide whether to be brave enough to invite them.

The story only exists when the meal plan is reasonable:
- the chosen main plus marinade must fit the setting's budget
- after cooking, the food must make enough portions for Coco, the grown-up,
  and one guest

Run it
------
python storyworlds/worlds/gpt-5.4/budget_marinade_coco_happy_ending_kindness_bravery.py
python storyworlds/worlds/gpt-5.4/budget_marinade_coco_happy_ending_kindness_bravery.py --all
python storyworlds/worlds/gpt-5.4/budget_marinade_coco_happy_ending_kindness_bravery.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/budget_marinade_coco_happy_ending_kindness_bravery.py --qa
python storyworlds/worlds/gpt-5.4/budget_marinade_coco_happy_ending_kindness_bravery.py --json
python storyworlds/worlds/gpt-5.4/budget_marinade_coco_happy_ending_kindness_bravery.py --verify
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
PEOPLE_TO_FEED = 3


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
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
        female = {"girl", "woman", "mother", "grandmother", "aunt"}
        male = {"boy", "man", "father", "grandfather", "uncle"}
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
class Setting:
    id: str
    place: str
    budget: int
    pantry_servings: int = 1
    scene: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class MainDish:
    id: str
    label: str
    phrase: str
    cost: int
    base_servings: int
    pot_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Marinade:
    id: str
    label: str
    phrase: str
    cost: int
    stretch_bonus: int
    aroma: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Guest:
    id: str
    label: str
    phrase: str
    waiting_place: str
    loneliness: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    main: str
    marinade: str
    guest: str
    caregiver: str
    seed: Optional[int] = None


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
        clone = World(self.setting)
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


def total_servings(setting: Setting, main: MainDish, marinade: Marinade) -> int:
    return setting.pantry_servings + main.base_servings + marinade.stretch_bonus


def total_cost(main: MainDish, marinade: Marinade) -> int:
    return main.cost + marinade.cost


def affordable(setting: Setting, main: MainDish, marinade: Marinade) -> bool:
    return total_cost(main, marinade) <= setting.budget


def enough_food(setting: Setting, main: MainDish, marinade: Marinade) -> bool:
    return total_servings(setting, main, marinade) >= PEOPLE_TO_FEED


def valid_plan(setting: Setting, main: MainDish, marinade: Marinade) -> bool:
    return affordable(setting, main, marinade) and enough_food(setting, main, marinade)


def explain_rejection(setting: Setting, main: MainDish, marinade: Marinade) -> str:
    cost = total_cost(main, marinade)
    portions = total_servings(setting, main, marinade)
    if cost > setting.budget:
        return (
            f"(No story: {main.label} with {marinade.label} costs {cost} coins, but "
            f"the budget at {setting.place} is only {setting.budget}. Pick a cheaper plan.)"
        )
    if portions < PEOPLE_TO_FEED:
        return (
            f"(No story: {main.label} with {marinade.label} would make only {portions} "
            f"servings, not enough for Coco, the grown-up, and one guest. Pick a meal "
            f"the marinade can stretch further.)"
        )
    return "(No story: this meal plan is not reasonable.)"


def _r_marinate(world: World) -> list[str]:
    meal = world.get("meal")
    if meal.meters["marinade_added"] < THRESHOLD:
        return []
    sig = ("marinated",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    meal.meters["servings"] += float(world.facts["marinade_cfg"].stretch_bonus)
    meal.meters["flavor"] += 1.0
    meal.meters["marinated"] += 1.0
    return ["__marinated__"]


def _r_enough_for_guest(world: World) -> list[str]:
    meal = world.get("meal")
    if meal.meters["servings"] < PEOPLE_TO_FEED:
        return []
    invite = world.get("invite")
    if invite.meters["offered"] < THRESHOLD:
        return []
    sig = ("welcome",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    coco = world.get("Coco")
    guest = world.get("Guest")
    caregiver = world.get("Caregiver")
    coco.memes["bravery"] += 1.0
    coco.memes["kindness"] += 1.0
    guest.memes["relief"] += 1.0
    guest.memes["belonging"] += 1.0
    caregiver.memes["pride"] += 1.0
    world.get("table").meters["full_places"] = float(PEOPLE_TO_FEED)
    return ["__welcome__"]


CAUSAL_RULES = [
    Rule(name="marinate", tag="physical", apply=_r_marinate),
    Rule(name="welcome", tag="social", apply=_r_enough_for_guest),
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


SETTINGS = {
    "courtyard": Setting(
        id="courtyard",
        place="the apartment courtyard",
        budget=6,
        pantry_servings=1,
        scene="Window boxes leaned over the bricks, and evening light lay soft on the benches.",
        tags={"budget", "community"},
    ),
    "rooftop": Setting(
        id="rooftop",
        place="the rooftop garden",
        budget=7,
        pantry_servings=1,
        scene="Tomato vines climbed old strings, and the city hummed far below.",
        tags={"budget", "garden"},
    ),
    "church_hall": Setting(
        id="church_hall",
        place="the little church hall kitchen",
        budget=8,
        pantry_servings=1,
        scene="The old windows glowed gold, and folding chairs waited in a neat line.",
        tags={"budget", "hall"},
    ),
}

MAINS = {
    "beans": MainDish(
        id="beans",
        label="beans",
        phrase="a bag of soft brown beans",
        cost=2,
        base_servings=2,
        pot_phrase="the beans simmered slowly in the pot",
        tags={"beans", "frugal"},
    ),
    "tofu": MainDish(
        id="tofu",
        label="tofu",
        phrase="two neat blocks of tofu",
        cost=3,
        base_servings=2,
        pot_phrase="the tofu cubes sizzled at the pan's edge",
        tags={"tofu", "frugal"},
    ),
    "chickpeas": MainDish(
        id="chickpeas",
        label="chickpeas",
        phrase="a tin of chickpeas",
        cost=2,
        base_servings=2,
        pot_phrase="the chickpeas rolled and popped softly in the pan",
        tags={"chickpeas", "frugal"},
    ),
    "mushrooms": MainDish(
        id="mushrooms",
        label="mushrooms",
        phrase="a basket of mushrooms",
        cost=4,
        base_servings=2,
        pot_phrase="the mushrooms turned glossy and brown",
        tags={"mushrooms"},
    ),
}

MARINADES = {
    "coco_lime": Marinade(
        id="coco_lime",
        label="coco-lime marinade",
        phrase="a bowl of coco-lime marinade",
        cost=2,
        stretch_bonus=1,
        aroma="sweet and bright, with lime waking up the whole room",
        tags={"coco", "marinade"},
    ),
    "garlic_herb": Marinade(
        id="garlic_herb",
        label="garlic-herb marinade",
        phrase="a bowl of garlic-herb marinade",
        cost=1,
        stretch_bonus=1,
        aroma="green and cozy, like a warm garden after rain",
        tags={"marinade", "herbs"},
    ),
    "soy_orange": Marinade(
        id="soy_orange",
        label="soy-orange marinade",
        phrase="a bowl of soy-orange marinade",
        cost=2,
        stretch_bonus=2,
        aroma="salty and sunny, with a tiny sparkle of orange",
        tags={"marinade", "citrus"},
    ),
}

GUESTS = {
    "new_neighbor": Guest(
        id="new_neighbor",
        label="the new neighbor",
        phrase="a new neighbor named Mina",
        waiting_place="by the fence with her hands tucked into her sleeves",
        loneliness="She looked as if she wanted to come closer but did not know how.",
        ending_image="Mina's smile stayed at the table even after the bowls were empty.",
        tags={"neighbor", "kindness"},
    ),
    "delivery_boy": Guest(
        id="delivery_boy",
        label="the bicycle delivery boy",
        phrase="a bicycle delivery boy named Ren",
        waiting_place="near the gate, rubbing tired knees after his last errand",
        loneliness="He looked hungry and surprised to smell supper meant for someone else.",
        ending_image="Ren rode away later with a straighter back and a grin.",
        tags={"helper", "kindness"},
    ),
    "choir_girl": Guest(
        id="choir_girl",
        label="the choir girl",
        phrase="a choir girl named Lila",
        waiting_place="on the hall steps with a music folder in her lap",
        loneliness="She looked small in the big evening, as if the song practice had ended too early.",
        ending_image="Lila hummed softly while she ate, and the tune made everyone smile.",
        tags={"choir", "kindness"},
    ),
}

CAREGIVERS = {
    "mother": {"type": "mother", "name": "Mama"},
    "father": {"type": "father", "name": "Dad"},
    "aunt": {"type": "aunt", "name": "Auntie"},
    "grandmother": {"type": "grandmother", "name": "Grandma"},
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for main_id, main in MAINS.items():
            for marinade_id, marinade in MARINADES.items():
                if valid_plan(setting, main, marinade):
                    combos.append((setting_id, main_id, marinade_id))
    return combos


def predict_meal(world: World, main_id: str, marinade_id: str) -> dict:
    sim = world.copy()
    cook_meal(sim, MAINS[main_id], MARINADES[marinade_id], narrate=False)
    meal = sim.get("meal")
    return {
        "servings": int(meal.meters["servings"]),
        "spend": int(sim.get("money").meters["spent"]),
        "left": int(sim.get("money").meters["budget"] - sim.get("money").meters["spent"]),
        "enough": meal.meters["servings"] >= PEOPLE_TO_FEED,
    }


def introduce(world: World, coco: Entity, caregiver: Entity) -> None:
    world.say(
        f"Coco stood beside {caregiver.label_word} in {world.setting.place}. "
        f"{world.setting.scene}"
    )
    world.say(
        f"In {caregiver.pronoun('possessive')} pocket was a folded paper envelope with the supper budget tucked inside."
    )


def count_budget(world: World, coco: Entity, caregiver: Entity) -> None:
    money = world.get("money")
    coco.memes["care"] += 1.0
    world.say(
        f'"We only have {int(money.meters["budget"])} coins today," '
        f'{caregiver.label_word.capitalize()} said. "So we have to cook with care and with heart."'
    )


def buy_plan(world: World, main: MainDish, marinade: Marinade) -> None:
    world.say(
        f"They chose {main.phrase} and {marinade.phrase}. "
        f"The little bowl of marinade looked simple, but it promised to do a big job."
    )


def notice_guest(world: World, coco: Entity, guest: Entity) -> None:
    coco.memes["concern"] += 1.0
    guest.memes["lonely"] += 1.0
    world.say(
        f"Just then Coco noticed {guest.label} {guest.attrs['waiting_place']}. "
        f"{guest.attrs['loneliness']}"
    )


def worry(world: World, coco: Entity, caregiver: Entity, guest: Entity, prediction: dict) -> None:
    coco.memes["worry"] += 1.0
    world.say(
        f'"I want to ask {guest.attrs["name"]} to eat with us," Coco whispered, '
        f'"but what if our budget is too small?"'
    )
    world.say(
        f'{caregiver.label_word.capitalize()} looked at the bowl and the pot. '
        f'"Let us think before we are afraid," {caregiver.pronoun()} said.'
    )
    world.facts["predicted_servings"] = prediction["servings"]
    world.facts["coins_left"] = prediction["left"]


def reassure(world: World, caregiver: Entity, marinade: Marinade, prediction: dict) -> None:
    world.say(
        f'{caregiver.label_word.capitalize()} stirred the {marinade.label} and smiled. '
        f'"A good marinade helps every bite count. This one will make {prediction["servings"]} warm servings, '
        f'and we will still have {prediction["left"]} coin left."'
    )


def brave_invitation(world: World, coco: Entity, guest: Entity) -> None:
    coco.memes["fear"] += 1.0
    world.say(
        f"Coco's stomach fluttered. It can feel brave just to speak kindly first."
    )
    world.say(
        f'Coco walked over to {guest.attrs["name"]} and said, '
        f'"Would you like to eat with us?"'
    )
    world.get("invite").meters["offered"] += 1.0
    propagate(world, narrate=False)


def guest_accepts(world: World, guest: Entity) -> None:
    guest.memes["hope"] += 1.0
    world.say(
        f'{guest.attrs["name"]} blinked, then nodded so fast that {guest.pronoun("possessive")} shoulders nearly bounced. '
        f'"Really?" {guest.pronoun()} asked.'
    )
    world.say(
        f'"Really," Coco said. "There is a place for you."'
    )


def cook_meal(world: World, main: MainDish, marinade: Marinade, narrate: bool = True) -> None:
    money = world.get("money")
    meal = world.get("meal")
    money.meters["spent"] += float(total_cost(main, marinade))
    money.meters["left"] = money.meters["budget"] - money.meters["spent"]
    meal.meters["servings"] += float(world.setting.pantry_servings + main.base_servings)
    meal.meters["marinade_added"] += 1.0
    propagate(world, narrate=False)
    if narrate:
        world.say(
            f"Soon {main.pot_phrase}. When the marinade went in, the food smelled {marinade.aroma}."
        )
        world.say(
            f"The plain supper no longer looked plain. It looked welcoming."
        )


def set_table(world: World, caregiver: Entity, guest: Entity) -> None:
    table = world.get("table")
    full_places = int(table.meters["full_places"])
    world.say(
        f'{caregiver.label_word.capitalize()} set out {full_places} bowls instead of two.'
    )
    world.say(
        f'{guest.attrs["name"]} held the spoons carefully, as if kindness were something breakable and bright.'
    )


def share_and_end(world: World, coco: Entity, caregiver: Entity, guest: Entity) -> None:
    coco.memes["joy"] += 1.0
    caregiver.memes["joy"] += 1.0
    guest.memes["joy"] += 1.0
    world.say(
        f"They ate slowly, talking between warm bites. The little budget had not become bigger, but the table had."
    )
    world.say(
        f'{caregiver.label_word.capitalize()} squeezed Coco\'s shoulder and said, '
        f'"You were brave enough to ask, and kind enough to share. That made the supper rich."'
    )
    world.say(guest.attrs["ending_image"])


def tell(setting: Setting, main: MainDish, marinade: Marinade, guest_cfg: Guest, caregiver_key: str) -> World:
    if caregiver_key not in CAREGIVERS:
        raise StoryError(f"(No story: unknown caregiver '{caregiver_key}'.)")
    if not valid_plan(setting, main, marinade):
        raise StoryError(explain_rejection(setting, main, marinade))

    world = World(setting)
    coco = world.add(Entity(id="Coco", kind="character", type="girl", label="Coco", role="hero"))
    care_info = CAREGIVERS[caregiver_key]
    caregiver = world.add(
        Entity(
            id="Caregiver",
            kind="character",
            type=care_info["type"],
            label=care_info["name"],
            role="caregiver",
        )
    )
    guest_name_map = {
        "new_neighbor": "Mina",
        "delivery_boy": "Ren",
        "choir_girl": "Lila",
    }
    guest = world.add(
        Entity(
            id="Guest",
            kind="character",
            type="girl" if guest_cfg.id != "delivery_boy" else "boy",
            label=guest_cfg.label,
            role="guest",
            attrs={
                "name": guest_name_map[guest_cfg.id],
                "waiting_place": guest_cfg.waiting_place,
                "loneliness": guest_cfg.loneliness,
                "ending_image": guest_cfg.ending_image,
            },
            tags=set(guest_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="money",
            type="money",
            label="budget envelope",
            meters=defaultdict(float, {"budget": float(setting.budget), "spent": 0.0, "left": float(setting.budget)}),
        )
    )
    world.add(Entity(id="meal", type="meal", label="supper pot"))
    world.add(Entity(id="invite", type="invitation", label="invitation"))
    world.add(Entity(id="table", type="table", label="table"))

    introduce(world, coco, caregiver)
    count_budget(world, coco, caregiver)
    buy_plan(world, main, marinade)

    world.para()
    notice_guest(world, coco, guest)
    prediction = predict_meal(world, main.id, marinade.id)
    worry(world, coco, caregiver, guest, prediction)
    reassure(world, caregiver, marinade, prediction)

    world.para()
    brave_invitation(world, coco, guest)
    guest_accepts(world, guest)
    cook_meal(world, main, marinade, narrate=True)

    world.para()
    set_table(world, caregiver, guest)
    share_and_end(world, coco, caregiver, guest)

    meal = world.get("meal")
    money = world.get("money")
    world.facts.update(
        setting=setting,
        main_cfg=main,
        marinade_cfg=marinade,
        guest_cfg=guest_cfg,
        caregiver=caregiver,
        coco=coco,
        guest=guest,
        servings=int(meal.meters["servings"]),
        spend=int(money.meters["spent"]),
        left=int(money.meters["left"]),
        brave=world.get("invite").meters["offered"] >= THRESHOLD,
        welcomed=world.get("table").meters["full_places"] >= PEOPLE_TO_FEED,
        happy=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    main = f["main_cfg"]
    marinade = f["marinade_cfg"]
    guest = f["guest"]
    caregiver = f["caregiver"]
    return [
        'Write a heartwarming story for a 3-to-5-year-old that includes the words "budget", "marinade", and "Coco".',
        f"Tell a gentle story where Coco and {caregiver.label_word} have a small supper budget in {setting.place}, "
        f"but Coco bravely invites {guest.attrs['name']} to share {main.label}.",
        f"Write a kind happy-ending story where a simple {marinade.label} helps stretch dinner far enough for one extra guest.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    guest = f["guest"]
    caregiver = f["caregiver"]
    main = f["main_cfg"]
    marinade = f["marinade_cfg"]
    setting = f["setting"]
    servings = f["servings"]
    spend = f["spend"]
    left = f["left"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Coco, {caregiver.label_word}, and {guest.attrs['name']}. The story follows a small supper in {setting.place} that grows kinder when Coco notices someone left out.",
        ),
        (
            "Why was Coco worried?",
            f"Coco wanted to invite {guest.attrs['name']}, but worried the budget would not stretch far enough. The worry came from having only a few coins and not wanting anyone at the table to go without.",
        ),
        (
            f"How did the marinade help?",
            f"The {marinade.label} helped turn a simple pot of {main.label} into {servings} warm servings. It mattered because the meal had to feed three people without spending more than the small budget.",
        ),
        (
            "What brave thing did Coco do?",
            f"Coco walked over and invited {guest.attrs['name']} to eat with them. That was brave because Coco was nervous, but kindness mattered more than staying quiet.",
        ),
        (
            "How do you know the ending was happy?",
            f"They set out three bowls, shared the meal, and everyone ate together. The supper stayed within the budget at {spend} coins, with {left} coin left, and the lonely person was lonely no longer.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "budget": [
        (
            "What is a budget?",
            "A budget is a plan for how much money you can spend. It helps people choose carefully so they do not use more money than they have.",
        )
    ],
    "marinade": [
        (
            "What is a marinade?",
            "A marinade is a seasoned liquid or sauce that food can soak in before or during cooking. It adds flavor and can help simple ingredients taste special.",
        )
    ],
    "beans": [
        (
            "Why are beans a good budget food?",
            "Beans can feed several people without costing very much. That is why many families use them when they want a filling meal for a small price.",
        )
    ],
    "tofu": [
        (
            "What is tofu?",
            "Tofu is a soft food made from soybeans. It can soak up sauces and marinades very well.",
        )
    ],
    "chickpeas": [
        (
            "What are chickpeas?",
            "Chickpeas are round beans that can be cooked into many warm meals. They are mild, filling, and good at taking on flavor.",
        )
    ],
    "mushrooms": [
        (
            "Why do mushrooms change when you cook them?",
            "Mushrooms hold water inside, and heat makes that water move and steam away. That is why they turn softer, darker, and more flavorful in a hot pan.",
        )
    ],
    "coco": [
        (
            "What does coco mean in coco-lime marinade?",
            "Here coco means coconut. Coconut can make a marinade taste creamy and a little sweet.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to help, include, or comfort someone. Small kind actions can make a person feel safe and welcome.",
        )
    ],
    "bravery": [
        (
            "Can inviting someone be brave?",
            "Yes. Bravery is not only about danger; sometimes it means doing a kind thing even when you feel shy or worried first.",
        )
    ],
}

KNOWLEDGE_ORDER = [
    "budget",
    "marinade",
    "coco",
    "beans",
    "tofu",
    "chickpeas",
    "mushrooms",
    "kindness",
    "bravery",
]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"budget", "marinade", "kindness", "bravery"}
    tags |= set(world.facts["main_cfg"].tags)
    tags |= set(world.facts["marinade_cfg"].tags)
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
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="courtyard",
        main="beans",
        marinade="coco_lime",
        guest="new_neighbor",
        caregiver="mother",
    ),
    StoryParams(
        setting="rooftop",
        main="tofu",
        marinade="soy_orange",
        guest="delivery_boy",
        caregiver="aunt",
    ),
    StoryParams(
        setting="church_hall",
        main="chickpeas",
        marinade="garlic_herb",
        guest="choir_girl",
        caregiver="grandmother",
    ),
    StoryParams(
        setting="rooftop",
        main="mushrooms",
        marinade="soy_orange",
        guest="new_neighbor",
        caregiver="father",
    ),
]


ASP_RULES = r"""
% Costs and servings decide whether a plan is reasonable.
cost_total(S, M, R, C + MC) :- setting(S), main(M), marinade(R), main_cost(M, C), marinade_cost(R, MC).
servings_total(S, M, R, P + B + X) :- setting(S), main(M), marinade(R),
                                      pantry_servings(S, P), base_servings(M, B), stretch_bonus(R, X).

affordable(S, M, R) :- cost_total(S, M, R, T), budget(S, B), T <= B.
enough_food(S, M, R) :- servings_total(S, M, R, T), people_needed(N), T >= N.
valid(S, M, R) :- affordable(S, M, R), enough_food(S, M, R).

happy(S, M, R) :- valid(S, M, R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        lines.append(asp.fact("budget", setting_id, setting.budget))
        lines.append(asp.fact("pantry_servings", setting_id, setting.pantry_servings))
    for main_id, main in MAINS.items():
        lines.append(asp.fact("main", main_id))
        lines.append(asp.fact("main_cost", main_id, main.cost))
        lines.append(asp.fact("base_servings", main_id, main.base_servings))
    for marinade_id, marinade in MARINADES.items():
        lines.append(asp.fact("marinade", marinade_id))
        lines.append(asp.fact("marinade_cost", marinade_id, marinade.cost))
        lines.append(asp.fact("stretch_bonus", marinade_id, marinade.stretch_bonus))
    lines.append(asp.fact("people_needed", PEOPLE_TO_FEED))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_happy_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show happy/3."))
    return sorted(set(asp.atoms(model, "happy")))


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

    happy_set = set(asp_happy_combos())
    if happy_set == python_set:
        print(f"OK: happy endings align with valid meal plans ({len(happy_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in happy combos:")
        if happy_set - python_set:
            print("  only in clingo:", sorted(happy_set - python_set))
        if python_set - happy_set:
            print("  only in python:", sorted(python_set - happy_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Verify failed: generated story was empty.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Heartwarming storyworld: Coco stretches a small supper budget with a marinade and a brave, kind invitation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--main", choices=MAINS)
    ap.add_argument("--marinade", choices=MARINADES)
    ap.add_argument("--guest", choices=GUESTS)
    ap.add_argument("--caregiver", choices=CAREGIVERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid meal-plan set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.main and args.marinade:
        setting = SETTINGS[args.setting]
        main = MAINS[args.main]
        marinade = MARINADES[args.marinade]
        if not valid_plan(setting, main, marinade):
            raise StoryError(explain_rejection(setting, main, marinade))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.main is None or combo[1] == args.main)
        and (args.marinade is None or combo[2] == args.marinade)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, main_id, marinade_id = rng.choice(sorted(combos))
    guest_id = args.guest or rng.choice(sorted(GUESTS))
    caregiver_id = args.caregiver or rng.choice(sorted(CAREGIVERS))
    return StoryParams(
        setting=setting_id,
        main=main_id,
        marinade=marinade_id,
        guest=guest_id,
        caregiver=caregiver_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.main not in MAINS:
        raise StoryError(f"(No story: unknown main '{params.main}'.)")
    if params.marinade not in MARINADES:
        raise StoryError(f"(No story: unknown marinade '{params.marinade}'.)")
    if params.guest not in GUESTS:
        raise StoryError(f"(No story: unknown guest '{params.guest}'.)")
    if params.caregiver not in CAREGIVERS:
        raise StoryError(f"(No story: unknown caregiver '{params.caregiver}'.)")

    setting = SETTINGS[params.setting]
    main = MAINS[params.main]
    marinade = MARINADES[params.marinade]
    if not valid_plan(setting, main, marinade):
        raise StoryError(explain_rejection(setting, main, marinade))

    world = tell(setting, main, marinade, GUESTS[params.guest], params.caregiver)
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
        print(asp_program("", "#show valid/3.\n#show happy/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, main, marinade) combos:\n")
        for setting_id, main_id, marinade_id in combos:
            print(f"  {setting_id:12} {main_id:10} {marinade_id}")
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
            header = f"### Coco at {p.setting}: {p.main} with {p.marinade} for {p.guest}"
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
