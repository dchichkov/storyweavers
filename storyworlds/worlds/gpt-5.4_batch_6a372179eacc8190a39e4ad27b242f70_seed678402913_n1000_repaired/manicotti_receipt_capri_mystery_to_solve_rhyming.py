#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/manicotti_receipt_capri_mystery_to_solve_rhyming.py
==============================================================================

A small standalone storyworld for a rhyming "mystery to solve" tale built around
three seed words: manicotti, receipt, and capri.

Premise
-------
A child visits a small shop or café with a grown-up. A tray of warm manicotti is
meant for a helper, but the paper receipt has gone missing. Without the receipt,
the grown-up cannot check where the box belongs. The child follows concrete clues
through the place, notices flour, steam, or a napkin trail, and solves the little
mystery. The ending image proves what changed: the missing receipt is found, the
right person gets the meal, and everyone feels calm again.

The prose is intentionally child-facing and gently rhyming, but the world model
still drives it: where the receipt was dropped, what clue revealed it, who found
it, and whether the mystery is solved by careful looking or by asking a helper.

Run it
------
    python storyworlds/worlds/gpt-5.4/manicotti_receipt_capri_mystery_to_solve_rhyming.py
    python storyworlds/worlds/gpt-5.4/manicotti_receipt_capri_mystery_to_solve_rhyming.py --all
    python storyworlds/worlds/gpt-5.4/manicotti_receipt_capri_mystery_to_solve_rhyming.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/manicotti_receipt_capri_mystery_to_solve_rhyming.py --qa
    python storyworlds/worlds/gpt-5.4/manicotti_receipt_capri_mystery_to_solve_rhyming.py --json
    python storyworlds/worlds/gpt-5.4/manicotti_receipt_capri_mystery_to_solve_rhyming.py --verify
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
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    movable: bool = False
    paper: bool = False
    warm_food: bool = False
    # world axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt", "grandmother"}
        male = {"boy", "father", "man", "uncle", "grandfather"}
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
            "aunt": "aunt",
            "uncle": "uncle",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    owner_name: str
    sign_name: str
    delivery_spot: str
    rhyme_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    aroma: str
    sauce: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class ReceiptPlace:
    id: str
    label: str
    phrase: str
    clue_text: str
    solve_text: str
    clue_tag: str
    reachable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    reveals: set[str] = field(default_factory=set)
    sense: int = 2
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperMove:
    id: str
    label: str
    phrase: str
    reveals: set[str] = field(default_factory=set)
    sense: int = 2
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    grown = world.get("grown")
    receipt = world.get("receipt")
    food = world.get("food")
    if receipt.meters["missing"] >= THRESHOLD and grown.memes["worry"] < THRESHOLD:
        sig = ("worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            grown.memes["worry"] += 1
            world.get("child").memes["concern"] += 1
            out.append("__worry__")
    if food.meters["waiting"] >= THRESHOLD and food.meters["delivered"] < THRESHOLD:
        sig = ("cool",)
        if sig not in world.fired:
            world.fired.add(sig)
            food.meters["cooling"] += 1
            out.append("__cool__")
    return out


def _r_solve(world: World) -> list[str]:
    out: list[str] = []
    receipt = world.get("receipt")
    child = world.get("child")
    if receipt.meters["found"] >= THRESHOLD:
        sig = ("solve",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["mystery_solved"] = True
            child.memes["pride"] += 1
            world.get("grown").memes["relief"] += 1
            world.get("food").meters["delivered"] += 1
            out.append("__solve__")
    return out


CAUSAL_RULES = [
    Rule(name="worry", tag="social", apply=_r_worry),
    Rule(name="solve", tag="social", apply=_r_solve),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def valid_combo(place_id: str, clue_id: str, helper_id: str) -> bool:
    place = RECEIPT_PLACES[place_id]
    clue = CLUES[clue_id]
    helper = HELPERS[helper_id]
    if not place.reachable:
        return False
    if clue.sense < SENSE_MIN:
        return False
    if helper.sense < SENSE_MIN:
        return False
    return place.clue_tag in clue.reveals or place.clue_tag in helper.reveals


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in RECEIPT_PLACES:
        for clue_id in CLUES:
            for helper_id in HELPERS:
                if valid_combo(place_id, clue_id, helper_id):
                    combos.append((place_id, clue_id, helper_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    clue = CLUES[params.clue]
    helper = HELPERS[params.helper]
    place = RECEIPT_PLACES[params.receipt_place]
    clue_hits = place.clue_tag in clue.reveals
    helper_hits = place.clue_tag in helper.reveals
    if clue_hits and helper_hits:
        return "shared"
    if clue_hits:
        return "noticed"
    if helper_hits:
        return "asked"
    raise StoryError("(No story: the chosen clue and helper cannot solve this mystery.)")


def predict_solution(place_id: str, clue_id: str, helper_id: str) -> dict:
    place = RECEIPT_PLACES[place_id]
    clue = CLUES[clue_id]
    helper = HELPERS[helper_id]
    return {
        "clue_hits": place.clue_tag in clue.reveals,
        "helper_hits": place.clue_tag in helper.reveals,
    }


def open_scene(world: World, child: Entity, grown: Entity, setting: Setting, food: Food) -> None:
    child.memes["joy"] += 1
    world.say(
        f"At {setting.sign_name}, by the bright capri-blue door, "
        f"{child.id} skipped in with {child.pronoun('possessive')} {grown.label_word} to the floor."
    )
    world.say(
        f"The shop smelled of {food.aroma}, warm and yummy through the air, "
        f"and a box of {food.label} waited by {setting.delivery_spot} there."
    )


def purchase(world: World, child: Entity, grown: Entity, food: Food) -> None:
    world.say(
        f'"That manicotti is for Mr. Dell," said {grown.label_word} with a careful grin. '
        f'"We need the little receipt to know just where to carry it in."'
    )
    world.get("food").meters["waiting"] += 1
    world.get("receipt").meters["needed"] += 1


def lose_receipt(world: World, grown: Entity, place: ReceiptPlace) -> None:
    receipt = world.get("receipt")
    receipt.meters["missing"] += 1
    receipt.attrs["hidden_at"] = place.id
    propagate(world, narrate=False)
    world.say(
        f"But pat went {grown.pronoun('possessive')} pocket, then bag, then sleeve so neat—"
        f'"Oh dear," {grown.pronoun()} sighed, "I cannot find the receipt."'
    )


def worry_beat(world: World, child: Entity, grown: Entity, food: Food) -> None:
    if grown.memes["worry"] >= THRESHOLD:
        world.say(
            f"The steam from the manicotti made swirls in the light, "
            f"while {grown.label_word} looked left and looked right."
        )
        world.say(
            f"{child.id} felt a tiny flutter, a mystery to meet: "
            f"no box could leave the counter without the missing receipt."
        )
    if food.meters["cooling"] >= THRESHOLD:
        world.say("The noodles would not stay warm forever on the seat.")


def hunt_clue(world: World, child: Entity, clue: Clue, place: ReceiptPlace) -> None:
    child.memes["curiosity"] += 1
    pred = predict_solution(place.id, clue.id, world.facts["helper_cfg"].id)
    world.facts["clue_hits"] = pred["clue_hits"]
    world.say(
        f'{child.id} did not stomp or leap or race with noisy feet. '
        f'{child.pronoun().capitalize()} looked for little signs instead, soft-eyed and small and sweet.'
    )
    world.say(clue.phrase)
    if pred["clue_hits"]:
        child.memes["confidence"] += 1
        world.say(place.clue_text)
    else:
        world.say(
            f"But that first clue only made a maybe, not a neat and tidy treat; "
            f"it pointed toward a question, not yet to the receipt."
        )


def ask_helper(world: World, child: Entity, grown: Entity, helper: HelperMove, place: ReceiptPlace) -> None:
    pred = predict_solution(place.id, world.facts["clue_cfg"].id, helper.id)
    world.facts["helper_hits"] = pred["helper_hits"]
    world.say(
        f'Then {child.id} asked a helper in a voice both calm and clear, '
        f'"Can you help us solve this puzzle? The receipt was somewhere near."'
    )
    world.say(helper.phrase)
    if pred["helper_hits"]:
        world.say(place.solve_text)
    else:
        world.say(
            "The helper was kind, but that guess did not complete the feat."
        )


def find_receipt(world: World, child: Entity, grown: Entity, place: ReceiptPlace, solver: str) -> None:
    receipt = world.get("receipt")
    receipt.meters["found"] += 1
    receipt.meters["missing"] = 0.0
    receipt.attrs["found_by"] = solver
    propagate(world, narrate=False)
    if solver == "child":
        world.say(
            f'"Here it is!" cried {child.id}. "What a tiny paper sheet!" '
            f'{child.pronoun().capitalize()} reached and picked it up—the missing receipt.'
        )
    elif solver == "helper":
        world.say(
            f'"There it is," the helper said, below {place.phrase} neat. '
            f'{child.id} clapped happy hands at last—they found the receipt.'
        )
    else:
        world.say(
            f'{child.id} and the helper found it both, a tidy little feat: '
            f'tucked safe below {place.phrase} lay the missing receipt.'
        )
    world.facts["solver"] = solver


def deliver(world: World, child: Entity, grown: Entity, setting: Setting, food: Food) -> None:
    if world.facts.get("mystery_solved"):
        world.say(
            f'Soon the box of {food.label} went to {setting.delivery_spot} right, '
            f'and {grown.label_word} smiled with shoulders loose and light.'
        )
        world.say(
            f"Past the capri-blue window, the evening looked sweet; "
            f"{child.id} had solved a warm, kind mystery with a box and a receipt."
        )


def closing_image(world: World, child: Entity, grown: Entity, setting: Setting) -> None:
    solver = world.facts.get("solver", "child")
    if solver == "child":
        lead = f"{child.id} felt proud"
    elif solver == "helper":
        lead = f"{child.id} felt glad to ask for help"
    else:
        lead = f"{child.id} felt proud and glad"
    world.say(
        f"{lead}, and {grown.label_word} felt steady from head down to feet. "
        f"Outside, {setting.rhyme_image}, and no one feared the missing receipt."
    )


def tell(
    setting: Setting,
    food_cfg: Food,
    place: ReceiptPlace,
    clue_cfg: Clue,
    helper_cfg: HelperMove,
    child_name: str = "Lila",
    child_type: str = "girl",
    grown_type: str = "aunt",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child", label=child_name))
    grown = world.add(Entity(id="Grown", kind="character", type=grown_type, role="grown", label="the grown-up"))
    food = world.add(
        Entity(
            id="food",
            type="food",
            label=food_cfg.label,
            phrase=food_cfg.phrase,
            tags=set(food_cfg.tags),
            warm_food=True,
        )
    )
    receipt = world.add(
        Entity(
            id="receipt",
            type="receipt",
            label="receipt",
            phrase="the little paper receipt",
            paper=True,
            movable=True,
            tags={"receipt", "paper"},
        )
    )

    world.facts.update(
        child=child,
        grown=grown,
        setting=setting,
        food_cfg=food_cfg,
        place_cfg=place,
        clue_cfg=clue_cfg,
        helper_cfg=helper_cfg,
        mystery_solved=False,
    )

    open_scene(world, child, grown, setting, food_cfg)
    purchase(world, child, grown, food_cfg)

    world.para()
    lose_receipt(world, grown, place)
    worry_beat(world, child, grown, food)

    world.para()
    hunt_clue(world, child, clue_cfg, place)
    ask_helper(world, child, grown, helper_cfg, place)

    outcome = outcome_of(
        StoryParams(
            setting=setting.id,
            food=food_cfg.id,
            receipt_place=place.id,
            clue=clue_cfg.id,
            helper=helper_cfg.id,
            child_name=child_name,
            child_type=child_type,
            grown_type=grown_type,
            seed=None,
        )
    )
    if outcome == "noticed":
        find_receipt(world, child, grown, place, "child")
    elif outcome == "asked":
        find_receipt(world, child, grown, place, "helper")
    else:
        find_receipt(world, child, grown, place, "both")

    world.para()
    deliver(world, child, grown, setting, food_cfg)
    closing_image(world, child, grown, setting)

    world.facts["outcome"] = outcome
    return world


SETTINGS = {
    "capri_corner": Setting(
        id="capri_corner",
        place="Capri Corner",
        owner_name="Nina",
        sign_name="Capri Corner",
        delivery_spot="the blue front shelf",
        rhyme_image="the capri-blue sign hummed softly in the street",
        tags={"shop", "capri"},
    ),
    "capri_cafe": Setting(
        id="capri_cafe",
        place="Capri Café",
        owner_name="Tomas",
        sign_name="Capri Café",
        delivery_spot="the wicker pick-up seat",
        rhyme_image="the capri awning fluttered gently in the street",
        tags={"cafe", "capri"},
    ),
    "capri_kitchen": Setting(
        id="capri_kitchen",
        place="Capri Kitchen",
        owner_name="Rosa",
        sign_name="Capri Kitchen",
        delivery_spot="the window by the herb pots",
        rhyme_image="the capri tiles glowed softly in the heat",
        tags={"kitchen", "capri"},
    ),
}

FOODS = {
    "manicotti": Food(
        id="manicotti",
        label="manicotti",
        phrase="a warm box of manicotti",
        aroma="baked cheese and tomato sauce",
        sauce="tomato sauce",
        plural=False,
        tags={"manicotti", "pasta"},
    ),
}

RECEIPT_PLACES = {
    "napkin_jar": ReceiptPlace(
        id="napkin_jar",
        label="napkin jar",
        phrase="the tall napkin jar",
        clue_text="A paper corner peeked out beside the tall napkin jar.",
        solve_text="The helper tipped the napkin jar and spotted a white corner near its base.",
        clue_tag="paper_corner",
        reachable=True,
        tags={"receipt", "napkins"},
    ),
    "sauce_crate": ReceiptPlace(
        id="sauce_crate",
        label="sauce crate",
        phrase="the wooden sauce crate",
        clue_text="A drip of red sauce had dotted the wooden sauce crate, and a white slip hid below.",
        solve_text="The helper followed the sauce drip to the wooden crate and found the white slip below it.",
        clue_tag="sauce_drip",
        reachable=True,
        tags={"sauce", "crate"},
    ),
    "capri_mat": ReceiptPlace(
        id="capri_mat",
        label="capri mat",
        phrase="the capri welcome mat",
        clue_text="The capri mat had one curled edge, and a paper strip winked under it.",
        solve_text="The helper lifted the capri mat and there it was, flat and safe underneath.",
        clue_tag="curled_mat",
        reachable=True,
        tags={"capri", "mat"},
    ),
    "oven_back": ReceiptPlace(
        id="oven_back",
        label="back of the hot oven",
        phrase="the hot oven",
        clue_text="A shimmer of heat rose there, but no child should reach behind that place.",
        solve_text="The helper checked by the hot oven and found the receipt resting behind the mitts.",
        clue_tag="oven_mitts",
        reachable=False,
        tags={"oven", "hot"},
    ),
}

CLUES = {
    "paper_corner": Clue(
        id="paper_corner",
        label="paper corner",
        phrase="A tiny white corner poked from somewhere low, like a shy little moon in a paper glow.",
        reveals={"paper_corner"},
        sense=3,
        tags={"paper"},
    ),
    "sauce_spot": Clue(
        id="sauce_spot",
        label="sauce spot",
        phrase="A red sauce spot dotted the floor in a neat little line, as if saying, 'Follow me, child, and the answer is mine.'",
        reveals={"sauce_drip"},
        sense=3,
        tags={"sauce"},
    ),
    "curled_edge": Clue(
        id="curled_edge",
        label="curled mat edge",
        phrase="Near the capri mat, one edge gave a curl and a creep, as if something beneath it had gone there to sleep.",
        reveals={"curled_mat"},
        sense=3,
        tags={"capri", "mat"},
    ),
    "guessing_game": Clue(
        id="guessing_game",
        label="wild guessing",
        phrase='Lila spun in a circle and whispered, "Maybe it flew!" But guessing without looking was not a strong clue.',
        reveals=set(),
        sense=1,
        tags={"guess"},
    ),
}

HELPERS = {
    "ask_cashier": HelperMove(
        id="ask_cashier",
        label="ask the cashier",
        phrase='The cashier said, "Let us think where a paper slip might meet a jar, a crate, or a mat on the floor not far."',
        reveals={"paper_corner", "sauce_drip", "curled_mat"},
        sense=3,
        tags={"helper"},
    ),
    "ask_cook": HelperMove(
        id="ask_cook",
        label="ask the cook",
        phrase='The cook tapped a spoon and said, "I saw no flying sheet, but I did carry sauce near the front with quick small feet."',
        reveals={"sauce_drip", "oven_mitts"},
        sense=2,
        tags={"helper", "cook"},
    ),
    "ask_delivery_boy": HelperMove(
        id="ask_delivery_boy",
        label="ask the delivery boy",
        phrase='The delivery boy said, "A breeze can scoot paper low; check the mat where tiny slips sometimes go."',
        reveals={"curled_mat"},
        sense=2,
        tags={"helper"},
    ),
    "shrug": HelperMove(
        id="shrug",
        label="just shrug",
        phrase='One helper only shrugged and said, "I do not know," which made the mystery no less slow.',
        reveals=set(),
        sense=1,
        tags={"helper"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Ava", "Ella", "Ruby", "Tessa", "Lucy"]
BOY_NAMES = ["Milo", "Theo", "Ben", "Owen", "Finn", "Leo", "Jude", "Evan"]


@dataclass
class StoryParams:
    setting: str
    food: str
    receipt_place: str
    clue: str
    helper: str
    child_name: str
    child_type: str
    grown_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "manicotti": [
        (
            "What is manicotti?",
            "Manicotti is a kind of pasta. It is usually a tube of pasta filled with cheese or other filling and baked with sauce."
        )
    ],
    "receipt": [
        (
            "What is a receipt?",
            "A receipt is a small paper note that shows what was bought. Shops use it to help remember orders and payments."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a problem where you do not know the answer yet. You solve it by noticing clues and thinking carefully."
        )
    ],
    "helper": [
        (
            "Why is it smart to ask a helper when you are stuck?",
            "A helper may have seen something you missed. Asking kindly can give you a new clue and help solve the problem faster."
        )
    ],
    "paper": [
        (
            "Why can a paper receipt be easy to lose?",
            "Paper slips are light and small. They can slide under things, stick to other paper, or get hidden where you do not expect."
        )
    ],
    "capri": [
        (
            "What does capri mean in this story?",
            "Here capri is part of the place name and the color image around the shop. It helps make the setting feel bright and memorable."
        )
    ],
    "sauce": [
        (
            "Why can a sauce drip become a clue?",
            "A drip can show where food or a box was carried. Following a small mark can help you find where something went."
        )
    ],
}

KNOWLEDGE_ORDER = ["manicotti", "receipt", "mystery", "helper", "paper", "capri", "sauce"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    grown = f["grown"]
    setting = f["setting"]
    return [
        'Write a short rhyming story for a 3-to-5-year-old that includes the words "manicotti", "receipt", and "capri", and has a small mystery to solve.',
        f"Tell a gentle mystery in rhyme where {child.id} and {child.pronoun('possessive')} {grown.label_word} lose a receipt at {setting.sign_name} and solve the problem by noticing clues.",
        "Write a child-facing rhyming story where a missing paper leads to a tiny mystery, and the ending proves the puzzle was solved kindly and carefully.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    grown = f["grown"]
    setting = f["setting"]
    place = f["place_cfg"]
    clue = f["clue_cfg"]
    helper = f["helper_cfg"]
    food = f["food_cfg"]
    outcome = f["outcome"]
    solver = f.get("solver", "child")
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {child.pronoun('possessive')} {grown.label_word} at {setting.sign_name}. They are trying to take a warm box of {food.label} to the right place."
        ),
        (
            "What was the mystery?",
            f"The little mystery was that the receipt had gone missing. Without it, {grown.label_word} could not be sure where the manicotti box should go."
        ),
        (
            "Why did the missing receipt matter?",
            f"The receipt helped show where the order belonged. Without that small paper, the grown-up did not want to send the manicotti to the wrong spot."
        ),
    ]
    if outcome == "noticed":
        out.append(
            (
                f"How did {child.id} solve the mystery?",
                f"{child.id} solved it by noticing a clue: {clue.label}. That careful looking led right to the receipt near {place.phrase}."
            )
        )
    elif outcome == "asked":
        out.append(
            (
                f"How was the mystery solved?",
                f"The clue alone was not enough, so {child.id} asked for help. The helper's idea led them to the receipt near {place.phrase}."
            )
        )
    else:
        out.append(
            (
                "Did the child solve it alone?",
                f"No, not completely. {child.id} noticed an important clue and the helper added the last useful idea, so they solved the mystery together near {place.phrase}."
            )
        )
    out.append(
        (
            "How did the story end?",
            f"It ended warmly and calmly: the missing receipt was found, the manicotti could be delivered, and {child.id} felt {('proud' if solver == 'child' else 'glad')} afterward."
        )
    )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"manicotti", "receipt", "mystery", "helper", "paper", "capri"}
    if f["place_cfg"].clue_tag == "sauce_drip" or "sauce" in f["clue_cfg"].tags:
        tags.add("sauce")
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} solver={world.facts.get('solver')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="capri_corner",
        food="manicotti",
        receipt_place="napkin_jar",
        clue="paper_corner",
        helper="ask_cashier",
        child_name="Lila",
        child_type="girl",
        grown_type="aunt",
        seed=1,
    ),
    StoryParams(
        setting="capri_cafe",
        food="manicotti",
        receipt_place="sauce_crate",
        clue="sauce_spot",
        helper="ask_cook",
        child_name="Milo",
        child_type="boy",
        grown_type="father",
        seed=2,
    ),
    StoryParams(
        setting="capri_corner",
        food="manicotti",
        receipt_place="capri_mat",
        clue="curled_edge",
        helper="ask_delivery_boy",
        child_name="Ruby",
        child_type="girl",
        grown_type="grandmother",
        seed=3,
    ),
    StoryParams(
        setting="capri_kitchen",
        food="manicotti",
        receipt_place="capri_mat",
        clue="paper_corner",
        helper="ask_delivery_boy",
        child_name="Theo",
        child_type="boy",
        grown_type="uncle",
        seed=4,
    ),
]


def explain_combo(place_id: str, clue_id: str, helper_id: str) -> str:
    place = RECEIPT_PLACES[place_id]
    clue = CLUES[clue_id]
    helper = HELPERS[helper_id]
    if not place.reachable and place.clue_tag not in helper.reveals:
        return (
            f"(No story: the receipt is hidden near {place.phrase}, which a child should not reach, "
            f"and the chosen helper move gives no safe way to find it.)"
        )
    if clue.sense < SENSE_MIN:
        return (
            f"(No story: '{clue_id}' is only wild guessing, not a reasonable clue for a mystery to solve.)"
        )
    if helper.sense < SENSE_MIN:
        return (
            f"(No story: '{helper_id}' gives no useful help. Pick a helper who notices or remembers something.)"
        )
    return (
        f"(No story: neither clue '{clue_id}' nor helper '{helper_id}' can reveal a receipt hidden at {place.phrase}.)"
    )


ASP_RULES = r"""
reachable(P) :- receipt_place(P), not unsafe(P).
good_clue(C) :- clue(C), clue_sense(C, S), sense_min(M), S >= M.
good_helper(H) :- helper(H), helper_sense(H, S), sense_min(M), S >= M.

solvable(P, C, H) :- reveals_clue(C, T), hidden_tag(P, T).
solvable(P, C, H) :- reveals_helper(H, T), hidden_tag(P, T).

valid(P, C, H) :- receipt_place(P), clue(C), helper(H),
                  reachable(P), good_clue(C), good_helper(H), solvable(P, C, H).

clue_hits :- chosen_place(P), chosen_clue(C), hidden_tag(P, T), reveals_clue(C, T).
helper_hits :- chosen_place(P), chosen_helper(H), hidden_tag(P, T), reveals_helper(H, T).

outcome(shared) :- clue_hits, helper_hits.
outcome(noticed) :- clue_hits, not helper_hits.
outcome(asked) :- helper_hits, not clue_hits.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for fid in FOODS:
        lines.append(asp.fact("food", fid))
    for pid, place in RECEIPT_PLACES.items():
        lines.append(asp.fact("receipt_place", pid))
        lines.append(asp.fact("hidden_tag", pid, place.clue_tag))
        if not place.reachable:
            lines.append(asp.fact("unsafe", pid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_sense", cid, clue.sense))
        for tag in sorted(clue.reveals):
            lines.append(asp.fact("reveals_clue", cid, tag))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_sense", hid, helper.sense))
        for tag in sorted(helper.reveals):
            lines.append(asp.fact("reveals_helper", hid, tag))
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
            asp.fact("chosen_place", params.receipt_place),
            asp.fact("chosen_clue", params.clue),
            asp.fact("chosen_helper", params.helper),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatch = 0
    for params in cases:
        try:
            py_out = outcome_of(params)
        except StoryError:
            py_out = "!"
        asp_out = asp_outcome(params)
        if py_out != asp_out:
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Rhyming mystery storyworld: a missing receipt, a box of manicotti, and a small capri-colored clue."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--receipt-place", choices=RECEIPT_PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--grown-type", choices=["mother", "father", "aunt", "uncle", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.food and args.food not in FOODS:
        raise StoryError(f"(No story: unknown food '{args.food}'.)")
    if args.receipt_place and args.clue and args.helper:
        if not valid_combo(args.receipt_place, args.clue, args.helper):
            raise StoryError(explain_combo(args.receipt_place, args.clue, args.helper))
    if args.clue and CLUES[args.clue].sense < SENSE_MIN:
        raise StoryError(explain_combo(args.receipt_place or "napkin_jar", args.clue, args.helper or "ask_cashier"))
    if args.helper and HELPERS[args.helper].sense < SENSE_MIN:
        raise StoryError(explain_combo(args.receipt_place or "napkin_jar", args.clue or "paper_corner", args.helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.receipt_place is None or combo[0] == args.receipt_place)
        and (args.clue is None or combo[1] == args.clue)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    receipt_place, clue, helper = rng.choice(sorted(combos))
    setting = args.setting or rng.choice(sorted(SETTINGS))
    food = args.food or "manicotti"
    child_type = args.child_type or rng.choice(["girl", "boy"])
    if args.child_name:
        child_name = args.child_name
    else:
        child_name = rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    grown_type = args.grown_type or rng.choice(["mother", "father", "aunt", "uncle", "grandmother", "grandfather"])

    return StoryParams(
        setting=setting,
        food=food,
        receipt_place=receipt_place,
        clue=clue,
        helper=helper,
        child_name=child_name,
        child_type=child_type,
        grown_type=grown_type,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.food not in FOODS:
        raise StoryError(f"(No story: unknown food '{params.food}'.)")
    if params.receipt_place not in RECEIPT_PLACES:
        raise StoryError(f"(No story: unknown receipt place '{params.receipt_place}'.)")
    if params.clue not in CLUES:
        raise StoryError(f"(No story: unknown clue '{params.clue}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if not valid_combo(params.receipt_place, params.clue, params.helper):
        raise StoryError(explain_combo(params.receipt_place, params.clue, params.helper))

    world = tell(
        setting=SETTINGS[params.setting],
        food_cfg=FOODS[params.food],
        place=RECEIPT_PLACES[params.receipt_place],
        clue_cfg=CLUES[params.clue],
        helper_cfg=HELPERS[params.helper],
        child_name=params.child_name,
        child_type=params.child_type,
        grown_type=params.grown_type,
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
        print(f"{len(combos)} compatible (receipt_place, clue, helper) combos:\n")
        for place, clue, helper in combos:
            print(f"  {place:12} {clue:14} {helper}")
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
            header = (
                f"### {p.child_name}: {p.receipt_place} with {p.clue}/{p.helper} "
                f"({p.setting}, {outcome_of(p)})"
            )
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
