#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/terry_abominate_request_inner_monologue_slice_of.py
==============================================================================

A small slice-of-life storyworld about Terry learning to make a clear, polite
request when breakfast arrives with a topping he cannot stand.

The core world model is simple and state-driven:

    served disliked topping -> Terry's appetite drops, frustration rises
    frustration + silence   -> Terry fidgets and thinks instead of eating
    polite request          -> helper warmth rises, Terry courage rises
    grumpy request          -> helper pauses and coaches kinder words
    swap approved           -> disliked topping removed, new topping served,
                               appetite returns, relief/joy rise

The world only tells *reasonable* stories: the requested topping must actually
fit the meal and be stocked in the chosen setting. A child cannot sensibly ask
for berries on toast in this tiny domain if that café never has berries.

Run it
------
    python storyworlds/worlds/gpt-5.4/terry_abominate_request_inner_monologue_slice_of.py
    python storyworlds/worlds/gpt-5.4/terry_abominate_request_inner_monologue_slice_of.py --setting home_kitchen --meal oatmeal --disliked raisins --requested honey
    python storyworlds/worlds/gpt-5.4/terry_abominate_request_inner_monologue_slice_of.py --setting corner_cafe --meal toast --requested berries
    python storyworlds/worlds/gpt-5.4/terry_abominate_request_inner_monologue_slice_of.py --all
    python storyworlds/worlds/gpt-5.4/terry_abominate_request_inner_monologue_slice_of.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
        female = {"girl", "mother", "woman", "lunch_lady", "teacher", "grandmother"}
        male = {"boy", "father", "man", "grandfather", "cook"}
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
            "lunch_lady": "cafeteria helper",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    helper_type: str
    helper_label: str
    intro: str
    serve_phrase: str
    stock: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Meal:
    id: str
    label: str
    phrase: str
    vessel: str
    verb: str
    allowed_toppings: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Topping:
    id: str
    label: str
    phrase: str
    texture: str
    mood: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class RequestStyle:
    id: str
    opener: str
    polite: bool
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


def _r_stall(world: World) -> list[str]:
    terry = world.get("terry")
    breakfast = world.get("breakfast")
    if terry.memes["frustration"] < THRESHOLD:
        return []
    if terry.memes["requested"] >= THRESHOLD:
        return []
    if breakfast.meters["untouched"] < THRESHOLD:
        return []
    sig = ("stall",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    terry.memes["hesitation"] += 1
    return ["__stall__"]


def _r_relief(world: World) -> list[str]:
    terry = world.get("terry")
    breakfast = world.get("breakfast")
    disliked = world.facts.get("disliked")
    if disliked is not None and breakfast.attrs.get("topping") == disliked.id:
        return []
    if terry.memes["requested"] < THRESHOLD:
        return []
    sig = ("relief", breakfast.attrs.get("topping"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    terry.memes["relief"] += 1
    terry.memes["joy"] += 1
    terry.meters["hunger"] = 0.0
    breakfast.meters["untouched"] = 0.0
    breakfast.meters["eaten"] += 1
    return ["__relief__"]


CAUSAL_RULES = [
    Rule(name="stall", tag="emotion", apply=_r_stall),
    Rule(name="relief", tag="emotion", apply=_r_relief),
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


SETTINGS = {
    "home_kitchen": Setting(
        id="home_kitchen",
        place="the kitchen",
        helper_type="mother",
        helper_label="the parent",
        intro="Morning light lay across the table and made the spoon shine.",
        serve_phrase="set breakfast in front of Terry",
        stock={"honey", "cinnamon_apples", "berries"},
        tags={"home", "breakfast"},
    ),
    "school_cafeteria": Setting(
        id="school_cafeteria",
        place="the school cafeteria",
        helper_type="lunch_lady",
        helper_label="the helper",
        intro="Trays clicked softly, and the room smelled warm and milky.",
        serve_phrase="slid Terry's tray across the counter",
        stock={"berries", "granola", "honey"},
        tags={"school", "cafeteria"},
    ),
    "corner_cafe": Setting(
        id="corner_cafe",
        place="the corner café",
        helper_type="grandmother",
        helper_label="the grandparent",
        intro="People talked in low voices while a bell jingled near the door.",
        serve_phrase="brought a plate over to Terry",
        stock={"butter", "strawberry_jam", "honey"},
        tags={"cafe", "breakfast"},
    ),
}

MEALS = {
    "oatmeal": Meal(
        id="oatmeal",
        label="oatmeal",
        phrase="a warm bowl of oatmeal",
        vessel="bowl",
        verb="steam",
        allowed_toppings={"raisins", "honey", "cinnamon_apples", "berries"},
        tags={"oatmeal", "warm_food"},
    ),
    "yogurt": Meal(
        id="yogurt",
        label="yogurt",
        phrase="a cool cup of yogurt",
        vessel="cup",
        verb="sit",
        allowed_toppings={"banana_slices", "berries", "granola", "honey"},
        tags={"yogurt", "cool_food"},
    ),
    "toast": Meal(
        id="toast",
        label="toast",
        phrase="two triangles of toast",
        vessel="plate",
        verb="wait",
        allowed_toppings={"orange_marmalade", "butter", "strawberry_jam", "honey"},
        tags={"toast", "crunchy_food"},
    ),
}

TOPPINGS = {
    "raisins": Topping(
        id="raisins",
        label="raisins",
        phrase="a little pile of raisins",
        texture="chewy",
        mood="too chewy for breakfast",
        plural=True,
        tags={"raisins", "fruit"},
    ),
    "banana_slices": Topping(
        id="banana_slices",
        label="banana slices",
        phrase="soft banana slices",
        texture="soft",
        mood="too mushy for Terry's taste",
        plural=True,
        tags={"banana", "fruit"},
    ),
    "orange_marmalade": Topping(
        id="orange_marmalade",
        label="orange marmalade",
        phrase="a shiny spoonful of orange marmalade",
        texture="sticky",
        mood="too bitter and sticky",
        plural=False,
        tags={"marmalade", "spread"},
    ),
    "honey": Topping(
        id="honey",
        label="honey",
        phrase="a ribbon of honey",
        texture="smooth",
        mood="golden and easy to like",
        plural=False,
        tags={"honey", "sweet"},
    ),
    "cinnamon_apples": Topping(
        id="cinnamon_apples",
        label="cinnamon apples",
        phrase="soft cinnamon apples",
        texture="soft",
        mood="sweet and warm",
        plural=True,
        tags={"apples", "sweet"},
    ),
    "berries": Topping(
        id="berries",
        label="berries",
        phrase="bright berries",
        texture="juicy",
        mood="bright and fresh",
        plural=True,
        tags={"berries", "fruit"},
    ),
    "granola": Topping(
        id="granola",
        label="granola",
        phrase="a spoonful of crunchy granola",
        texture="crunchy",
        mood="crisp and cheerful",
        plural=False,
        tags={"granola", "crunchy"},
    ),
    "butter": Topping(
        id="butter",
        label="butter",
        phrase="melting butter",
        texture="smooth",
        mood="plain and cozy",
        plural=False,
        tags={"butter", "spread"},
    ),
    "strawberry_jam": Topping(
        id="strawberry_jam",
        label="strawberry jam",
        phrase="strawberry jam",
        texture="sticky",
        mood="sweet and sunny",
        plural=False,
        tags={"jam", "spread"},
    ),
}

REQUEST_STYLES = {
    "polite": RequestStyle(
        id="polite",
        opener="Could I please have",
        polite=True,
        tags={"polite", "request"},
    ),
    "grumbly": RequestStyle(
        id="grumbly",
        opener="I don't want this. I want",
        polite=False,
        tags={"grumbly", "request"},
    ),
}


def requested_fits(meal_id: str, topping_id: str) -> bool:
    return topping_id in MEALS[meal_id].allowed_toppings


def setting_has(setting_id: str, topping_id: str) -> bool:
    return topping_id in SETTINGS[setting_id].stock


def served_on(meal_id: str, disliked_id: str) -> bool:
    return disliked_id in MEALS[meal_id].allowed_toppings


def valid_combo(setting_id: str, meal_id: str, disliked_id: str, requested_id: str) -> bool:
    if disliked_id == requested_id:
        return False
    return (
        served_on(meal_id, disliked_id)
        and requested_fits(meal_id, requested_id)
        and setting_has(setting_id, requested_id)
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for meal_id in MEALS:
            for disliked_id in MEALS[meal_id].allowed_toppings:
                if disliked_id not in TOPPINGS:
                    continue
                for requested_id in sorted(SETTINGS[setting_id].stock):
                    if requested_id not in TOPPINGS:
                        continue
                    if valid_combo(setting_id, meal_id, disliked_id, requested_id):
                        combos.append((setting_id, meal_id, disliked_id, requested_id))
    return sorted(set(combos))


@dataclass
class StoryParams:
    setting: str
    meal: str
    disliked: str
    requested: str
    request_style: str
    helper_name: str
    terry_age: int = 6
    seed: Optional[int] = None


def explain_rejection(setting_id: str, meal_id: str, disliked_id: str, requested_id: str) -> str:
    if disliked_id == requested_id:
        return "(No story: Terry cannot make a swap request for the exact same topping.)"
    if not served_on(meal_id, disliked_id):
        return (
            f"(No story: {TOPPINGS[disliked_id].label} does not belong on "
            f"{MEALS[meal_id].label} in this world, so Terry has no honest breakfast problem.)"
        )
    if not requested_fits(meal_id, requested_id):
        return (
            f"(No story: asking for {TOPPINGS[requested_id].label} on "
            f"{MEALS[meal_id].label} would sound odd here. The requested topping must fit the meal.)"
        )
    if not setting_has(setting_id, requested_id):
        return (
            f"(No story: {SETTINGS[setting_id].place} does not stock "
            f"{TOPPINGS[requested_id].label}, so the helper cannot reasonably grant that request.)"
        )
    return "(No story: this combination is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    style = REQUEST_STYLES[params.request_style]
    return "direct_swap" if style.polite else "coached_swap"


def breakfast_phrase(meal: Meal, topping: Topping) -> str:
    if meal.id == "toast":
        return f"{meal.phrase} with {topping.phrase} on top"
    return f"{meal.phrase} with {topping.phrase}"


def helper_relation(setting: Setting) -> str:
    if setting.helper_type == "mother":
        return "mom"
    if setting.helper_type == "grandmother":
        return "grandma"
    return "cafeteria helper"


def introduce(world: World, terry: Entity, helper: Entity, setting: Setting) -> None:
    world.say(
        f"Terry sat at a table in {setting.place}. {setting.intro}"
    )
    world.say(
        f"{helper.id}, Terry's {helper_relation(setting)}, {setting.serve_phrase}."
    )


def serve_breakfast(world: World, breakfast: Entity, meal: Meal, disliked: Topping) -> None:
    breakfast.attrs["meal"] = meal.id
    breakfast.attrs["topping"] = disliked.id
    breakfast.meters["untouched"] += 1
    terry = world.get("terry")
    terry.meters["hunger"] += 1
    terry.memes["frustration"] += 1
    terry.memes["dislike"] += 1
    world.say(
        f"It was {breakfast_phrase(meal, disliked)}."
    )
    world.say(
        f'Terry looked down and thought, "I abominate {disliked.label}. '
        f'Why is it always {disliked.mood}?"'
    )
    propagate(world, narrate=False)


def hesitate(world: World, terry: Entity, requested: Topping) -> None:
    if terry.memes["hesitation"] >= THRESHOLD:
        world.say(
            f'Terry held the spoon without lifting it. "If I stay quiet," Terry thought, '
            f'"breakfast will just sit there, and I will still wish for {requested.label}."'
        )
        terry.memes["worry"] += 1


def choose_words(world: World, terry: Entity) -> None:
    world.say(
        f'Terry took a breath. "Say it kindly," Terry told himself. '
        f'"A request sounds better when it is clear."'
    )
    terry.memes["courage"] += 1


def ask(world: World, terry: Entity, helper: Entity, requested: Topping, style: RequestStyle) -> None:
    terry.memes["requested"] += 1
    if style.polite:
        world.say(
            f'Terry looked up at {helper.id} and said, '
            f'"{style.opener} {requested.label} instead?"'
        )
        helper.memes["warmth"] += 1
        terry.memes["courage"] += 1
    else:
        terry.memes["grumpiness"] += 1
        helper.memes["patience"] += 1
        world.say(
            f'Terry blurted, "{style.opener} {requested.label}."'
        )
        world.say(
            f'{helper.id} did not sound angry. "{helper.get("name", helper.id) if False else ""}'
        )


def coach_retry(world: World, terry: Entity, helper: Entity, requested: Topping) -> None:
    world.say(
        f'{helper.id} smiled a little and said, "Try that again with kind words, Terry. '
        f'I want to help, but I need a calm request."'
    )
    terry.memes["embarrassment"] += 1
    world.say(
        f'Terry felt his cheeks get warm. "Right," Terry thought. '
        f'"I can ask without snapping."'
    )
    terry.memes["courage"] += 1
    terry.memes["grumpiness"] = 0.0
    helper.memes["warmth"] += 1
    world.say(
        f'Terry tried again. "Could I please have {requested.label} instead?"'
    )


def swap(world: World, helper: Entity, breakfast: Entity, requested: Topping) -> None:
    breakfast.attrs["old_topping"] = breakfast.attrs.get("topping")
    breakfast.attrs["topping"] = requested.id
    helper.meters["helped"] += 1
    terry = world.get("terry")
    terry.memes["gratitude"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{helper.id} nodded and fixed the {world.facts["meal"].label}. '
        f'Soon there was {requested.phrase} where the old topping had been.'
    )


def finish_breakfast(world: World, terry: Entity, helper: Entity, requested: Topping) -> None:
    world.say(
        f'Terry took a bite and smiled. "{requested.label.capitalize()} is much better," Terry thought.'
    )
    world.say(
        f'"Thank you," Terry said. {helper.id} gave a small nod, and breakfast finally felt easy.'
    )


def tell(
    setting: Setting,
    meal: Meal,
    disliked: Topping,
    requested: Topping,
    request_style: RequestStyle,
    helper_name: str,
    terry_age: int,
) -> World:
    world = World()
    terry = world.add(
        Entity(
            id="Terry",
            kind="character",
            type="boy",
            label="Terry",
            phrase="a small boy named Terry",
            role="child",
            attrs={"age": terry_age},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=setting.helper_type,
            label=setting.helper_label,
            phrase=helper_name,
            role="helper",
        )
    )
    breakfast = world.add(
        Entity(
            id="breakfast",
            kind="thing",
            type=meal.id,
            label=meal.label,
            phrase=meal.phrase,
            role="meal",
        )
    )

    introduce(world, terry, helper, setting)
    serve_breakfast(world, breakfast, meal, disliked)

    world.para()
    hesitate(world, terry, requested)
    choose_words(world, terry)
    if request_style.polite:
        ask(world, terry, helper, requested, request_style)
    else:
        world.say(
            f'Terry almost said something cross. "I do not want to sound rude," Terry thought, '
            f'but the words came out too sharp anyway.'
        )
        world.say(
            f'Terry blurted, "{request_style.opener} {requested.label}."'
        )
        coach_retry(world, terry, helper, requested)
        terry.memes["requested"] += 1

    world.para()
    swap(world, helper, breakfast, requested)
    finish_breakfast(world, terry, helper, requested)

    world.facts.update(
        terry=terry,
        helper=helper,
        breakfast=breakfast,
        setting=setting,
        meal=meal,
        disliked=disliked,
        requested=requested,
        request_style=request_style,
        outcome="direct_swap" if request_style.polite else "coached_swap",
    )
    return world


KNOWLEDGE = {
    "request": [
        (
            "What is a polite request?",
            "A polite request is when you ask for something kindly, using calm words like please. It helps the other person understand what you need and makes it easier for them to help."
        )
    ],
    "breakfast": [
        (
            "Why do people eat breakfast?",
            "Breakfast gives your body energy after sleeping all night. It helps you start the day ready to learn, play, and think."
        )
    ],
    "oatmeal": [
        (
            "What is oatmeal?",
            "Oatmeal is a warm breakfast made from oats cooked until soft. People often add fruit or honey to change the taste."
        )
    ],
    "yogurt": [
        (
            "What is yogurt?",
            "Yogurt is a cool, creamy food often eaten at breakfast or snack time. Some people like to add fruit or granola to it."
        )
    ],
    "toast": [
        (
            "What is toast?",
            "Toast is bread warmed until it turns a little crisp. People often spread butter or jam on it."
        )
    ],
    "raisins": [
        (
            "What are raisins?",
            "Raisins are dried grapes. They are sweet and chewy, so some people enjoy them and some people do not."
        )
    ],
    "banana": [
        (
            "Why might someone not like banana slices?",
            "Different people notice different textures in food. Someone might think banana slices feel too mushy, even if another person likes them."
        )
    ],
    "marmalade": [
        (
            "What is marmalade?",
            "Marmalade is a fruit spread, often made with oranges. It can taste sweet and a little bitter at the same time."
        )
    ],
    "please": [
        (
            "Why does saying please matter?",
            "Saying please shows respect and gentleness. Kind words do not guarantee yes, but they help conversations stay calm."
        )
    ],
}
KNOWLEDGE_ORDER = ["request", "please", "breakfast", "oatmeal", "yogurt", "toast", "raisins", "banana", "marmalade"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    terry = f["terry"]
    setting = f["setting"]
    meal = f["meal"]
    disliked = f["disliked"]
    requested = f["requested"]
    outcome = f["outcome"]
    prompts = [
        (
            f'Write a short slice-of-life story for a 3-to-5-year-old about a child named '
            f'{terry.id} at breakfast. Include the words "Terry", "abominate", and "request", '
            f'and include inner monologue.'
        ),
        (
            f"Tell a gentle story where Terry is served {meal.label} with {disliked.label}, "
            f"thinks about how much he dislikes it, and then makes a request for {requested.label}."
        ),
    ]
    if outcome == "coached_swap":
        prompts.append(
            f"Write a morning story set in {setting.place} where Terry starts with sharp words, "
            f"gets coached to try again, and ends by asking politely."
        )
    else:
        prompts.append(
            f"Write a calm breakfast story set in {setting.place} where Terry finds the courage "
            f"to ask for a simple swap in kind words."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    terry = f["terry"]
    helper = f["helper"]
    setting = f["setting"]
    meal = f["meal"]
    disliked = f["disliked"]
    requested = f["requested"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Terry at breakfast with {helper.id}. The story follows the small problem Terry has with his food and the brave little request he makes."
        ),
        (
            "What was wrong with Terry's breakfast?",
            f"Terry was served {meal.label} with {disliked.label}, and he did not want that topping at all. In his thoughts he even says he abominates it, which shows how strongly he dislikes it."
        ),
        (
            "Why did Terry stay quiet at first?",
            f"He felt unsure about speaking up, so he held still and thought instead of eating. Terry knew what he wanted, but he had to gather courage before making his request."
        ),
    ]
    if outcome == "direct_swap":
        qa.append(
            (
                "How did Terry ask for help?",
                f"He asked politely for {requested.label} instead. Because his words were calm and clear, {helper.id} could understand exactly what Terry needed."
            )
        )
    else:
        qa.append(
            (
                "Did Terry ask politely the first time?",
                f"No. Terry first spoke too sharply, and {helper.id} asked him to try again with kind words. That pause helped Terry fix his tone and make a better request."
            )
        )
    qa.append(
        (
            "How did the problem get solved?",
            f"{helper.id} changed the topping and gave Terry {requested.label} instead. Once the breakfast matched what Terry could enjoy, he ate and the whole moment felt easier."
        )
    )
    qa.append(
        (
            "What changed at the end of the story?",
            f"At first Terry felt frustrated and stuck, but at the end he felt relieved and grateful. The change happened because he used words to ask for help instead of sitting with the problem."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"request", "please", "breakfast"}
    meal = f["meal"]
    disliked = f["disliked"]
    if meal.id == "oatmeal":
        tags.add("oatmeal")
    elif meal.id == "yogurt":
        tags.add("yogurt")
    elif meal.id == "toast":
        tags.add("toast")
    if disliked.id == "raisins":
        tags.add("raisins")
    elif disliked.id == "banana_slices":
        tags.add("banana")
    elif disliked.id == "orange_marmalade":
        tags.add("marmalade")
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="home_kitchen",
        meal="oatmeal",
        disliked="raisins",
        requested="honey",
        request_style="polite",
        helper_name="Mom",
        terry_age=6,
    ),
    StoryParams(
        setting="school_cafeteria",
        meal="yogurt",
        disliked="banana_slices",
        requested="berries",
        request_style="grumbly",
        helper_name="Ms. June",
        terry_age=7,
    ),
    StoryParams(
        setting="corner_cafe",
        meal="toast",
        disliked="orange_marmalade",
        requested="butter",
        request_style="polite",
        helper_name="Grandma May",
        terry_age=5,
    ),
    StoryParams(
        setting="home_kitchen",
        meal="oatmeal",
        disliked="raisins",
        requested="cinnamon_apples",
        request_style="grumbly",
        helper_name="Mom",
        terry_age=6,
    ),
]


ASP_RULES = r"""
served_on(M, T) :- allowed(M, T).
fits(M, T) :- allowed(M, T).
has_stock(S, T) :- stock(S, T).

valid(S, M, D, R) :- setting(S), meal(M), topping(D), topping(R),
                     served_on(M, D), fits(M, R), has_stock(S, R), D != R.

direct_swap :- chosen_style(polite).
coached_swap :- chosen_style(grumbly).

outcome(direct_swap) :- direct_swap.
outcome(coached_swap) :- coached_swap.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for topping_id in sorted(setting.stock):
            lines.append(asp.fact("stock", setting_id, topping_id))
    for meal_id, meal in MEALS.items():
        lines.append(asp.fact("meal", meal_id))
        for topping_id in sorted(meal.allowed_toppings):
            lines.append(asp.fact("allowed", meal_id, topping_id))
    for topping_id in TOPPINGS:
        lines.append(asp.fact("topping", topping_id))
    for style_id in REQUEST_STYLES:
        lines.append(asp.fact("style", style_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_style", params.request_style)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_generate() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: story text was empty.")
    with contextlib.redirect_stdout(io.StringIO()):
        emit(sample, trace=True, qa=True)


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
    for seed in range(40):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        _smoke_generate()
        print("OK: smoke generate/emit passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: Terry makes a breakfast request."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--meal", choices=MEALS)
    ap.add_argument("--disliked", choices=TOPPINGS)
    ap.add_argument("--requested", choices=TOPPINGS)
    ap.add_argument("--request-style", dest="request_style", choices=REQUEST_STYLES)
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible setting/meal/topping swaps from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


HELPER_NAMES = {
    "mother": ["Mom", "Mama"],
    "grandmother": ["Grandma May", "Grandma Ruth"],
    "lunch_lady": ["Ms. June", "Ms. Pru"],
}


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting_id = args.setting
    meal_id = args.meal
    disliked_id = args.disliked
    requested_id = args.requested

    if setting_id and meal_id and disliked_id and requested_id:
        if not valid_combo(setting_id, meal_id, disliked_id, requested_id):
            raise StoryError(explain_rejection(setting_id, meal_id, disliked_id, requested_id))

    combos = [
        combo for combo in valid_combos()
        if (setting_id is None or combo[0] == setting_id)
        and (meal_id is None or combo[1] == meal_id)
        and (disliked_id is None or combo[2] == disliked_id)
        and (requested_id is None or combo[3] == requested_id)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, meal_id, disliked_id, requested_id = rng.choice(sorted(combos))
    request_style = args.request_style or rng.choice(sorted(REQUEST_STYLES))
    helper_type = SETTINGS[setting_id].helper_type
    helper_name = args.helper_name or rng.choice(HELPER_NAMES[helper_type])
    terry_age = rng.choice([5, 6, 7])
    return StoryParams(
        setting=setting_id,
        meal=meal_id,
        disliked=disliked_id,
        requested=requested_id,
        request_style=request_style,
        helper_name=helper_name,
        terry_age=terry_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.meal not in MEALS:
        raise StoryError(f"Unknown meal: {params.meal}")
    if params.disliked not in TOPPINGS:
        raise StoryError(f"Unknown disliked topping: {params.disliked}")
    if params.requested not in TOPPINGS:
        raise StoryError(f"Unknown requested topping: {params.requested}")
    if params.request_style not in REQUEST_STYLES:
        raise StoryError(f"Unknown request style: {params.request_style}")
    if not valid_combo(params.setting, params.meal, params.disliked, params.requested):
        raise StoryError(explain_rejection(params.setting, params.meal, params.disliked, params.requested))

    world = tell(
        setting=SETTINGS[params.setting],
        meal=MEALS[params.meal],
        disliked=TOPPINGS[params.disliked],
        requested=TOPPINGS[params.requested],
        request_style=REQUEST_STYLES[params.request_style],
        helper_name=params.helper_name,
        terry_age=params.terry_age,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, meal, disliked, requested) combos:\n")
        for setting_id, meal_id, disliked_id, requested_id in combos:
            print(f"  {setting_id:16} {meal_id:8} {disliked_id:18} {requested_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### Terry at {p.setting}: {p.meal} with {p.disliked} -> {p.requested} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
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
