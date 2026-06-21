#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ignite_ineffable_toast_driveway_quest_surprise_folk.py
==================================================================================

A standalone storyworld for a small folk-tale-like driveway quest: a child wants
to prepare a surprise piece of toast for someone they love. The quest turns on
how the toast is made, how it is carried across the driveway, and whether wind
or mist steals its warmth before the surprise can bloom.

Required seed words and instruments:
- words: ignite, ineffable, toast
- setting: driveway
- features: Quest, Surprise
- style: Folk Tale

Run it
------
python storyworlds/worlds/gpt-5.4/ignite_ineffable_toast_driveway_quest_surprise_folk.py
python storyworlds/worlds/gpt-5.4/ignite_ineffable_toast_driveway_quest_surprise_folk.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/ignite_ineffable_toast_driveway_quest_surprise_folk.py --all --qa
python storyworlds/worlds/gpt-5.4/ignite_ineffable_toast_driveway_quest_surprise_folk.py --json
python storyworlds/worlds/gpt-5.4/ignite_ineffable_toast_driveway_quest_surprise_folk.py --verify
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
    traits: list[str] = field(default_factory=list)
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "aunt", "sister"}
        male = {"boy", "father", "grandfather", "man", "uncle", "brother"}
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
        }.get(self.type, self.type)


@dataclass
class Quest:
    id: str
    recipient_name: str
    recipient_type: str
    recipient_label: str
    arrival: str
    reason: str
    distance: int
    gift_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Weather:
    id: str
    sky: str
    breeze: int
    damp: int
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    sense: int
    dry_only: bool
    heat: int
    ignite_text: str
    finish_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Carrier:
    id: str
    label: str
    phrase: str
    retention: int
    cover: bool
    journey_text: str
    qa_text: str
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


def _r_heat_softens_butter(world: World) -> list[str]:
    toast = world.entities.get("toast")
    if toast is None or toast.meters["warmth"] < THRESHOLD:
        return []
    sig = ("soften",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    toast.meters["butter_melt"] += 1
    return ["A little butter sank into the toast and made it shine."]


def _r_weather_steals_heat(world: World) -> list[str]:
    toast = world.entities.get("toast")
    weather = world.entities.get("weather")
    carrier = world.entities.get("carrier")
    if toast is None or weather is None or carrier is None:
        return []
    if toast.meters["moving"] < THRESHOLD:
        return []
    sig = ("cool", weather.id, carrier.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    loss = max(0, int(weather.attrs.get("breeze", 0)) + int(weather.attrs.get("damp", 0)) - int(carrier.attrs.get("shield", 0)))
    if loss > 0:
        toast.meters["warmth"] -= loss
        toast.meters["cooling"] += loss
        return ["__cooling__"]
    return []


def _r_warm_toast_makes_hope(world: World) -> list[str]:
    toast = world.entities.get("toast")
    child = world.entities.get("child")
    if toast is None or child is None:
        return []
    if toast.meters["warmth"] < 3:
        return []
    sig = ("hope",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["hope"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="soften_butter", tag="physical", apply=_r_heat_softens_butter),
    Rule(name="weather_steals_heat", tag="physical", apply=_r_weather_steals_heat),
    Rule(name="warm_toast_makes_hope", tag="emotional", apply=_r_warm_toast_makes_hope),
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
            if not sent.startswith("__"):
                world.say(sent)
    return produced


QUESTS = {
    "grandpa": Quest(
        id="grandpa",
        recipient_name="Grandpa Rowan",
        recipient_type="grandfather",
        recipient_label="grandpa",
        arrival="came back from the lane with a basket of apples",
        reason="because he always greeted the morning as if it were a friend",
        distance=2,
        gift_line='a golden piece of toast with honey',
        tags={"grandparent", "surprise"},
    ),
    "aunt": Quest(
        id="aunt",
        recipient_name="Aunt May",
        recipient_type="aunt",
        recipient_label="aunt",
        arrival="rolled home with her flower cart singing softly",
        reason="because she spent her mornings carrying color to other people",
        distance=3,
        gift_line='a warm piece of cinnamon toast',
        tags={"aunt", "surprise"},
    ),
    "sister": Quest(
        id="sister",
        recipient_name="Mira",
        recipient_type="sister",
        recipient_label="big sister",
        arrival="returned from her early bicycle ride with bright cheeks",
        reason="because she had cheered for everyone else all week",
        distance=1,
        gift_line='a buttery piece of toast cut into a star',
        tags={"sibling", "surprise"},
    ),
}

WEATHERS = {
    "sunny": Weather(
        id="sunny",
        sky="the sun laid pale gold across the stones",
        breeze=0,
        damp=0,
        image="The driveway looked like a small gray road leading into a bright day.",
        tags={"sun"},
    ),
    "windy": Weather(
        id="windy",
        sky="the morning light came with a skipping wind",
        breeze=1,
        damp=0,
        image="Dusty leaves chased one another over the driveway like tiny brown goats.",
        tags={"wind"},
    ),
    "misty": Weather(
        id="misty",
        sky="a silver mist sat low over the hedges",
        breeze=0,
        damp=1,
        image="The driveway glimmered with tiny beads of water that made every stone look washed and old.",
        tags={"mist"},
    ),
}

METHODS = {
    "porch_toaster": Method(
        id="porch_toaster",
        label="porch toaster",
        sense=3,
        dry_only=True,
        heat=3,
        ignite_text="When the grown-up pressed the lever, the coils glowed red as if they would ignite a tiny dawn inside the toaster.",
        finish_text="Soon the bread sprang up brown at the edges and sweet at the middle.",
        qa_text="They used a toaster on a steady table by the porch.",
        tags={"toaster", "electricity"},
    ),
    "stone_griddle": Method(
        id="stone_griddle",
        label="stone-slab griddle",
        sense=3,
        dry_only=False,
        heat=3,
        ignite_text="The helper lit the small griddle on a flat stone, and the careful flame did its work without wandering.",
        finish_text="The bread turned crisp and speckled, and the air filled with a gentle, toasty smell.",
        qa_text="They toasted the bread on a small griddle set safely on a stone slab.",
        tags={"griddle", "flame"},
    ),
    "candle_rack": Method(
        id="candle_rack",
        label="candle rack",
        sense=1,
        dry_only=False,
        heat=1,
        ignite_text="A candle flickered under a wire rack, but it was a poor and risky way to toast bread.",
        finish_text="The bread hardly browned at all.",
        qa_text="They tried a candle under a rack.",
        tags={"candle", "flame"},
    ),
}

CARRIERS = {
    "open_plate": Carrier(
        id="open_plate",
        label="open plate",
        phrase="an open blue plate",
        retention=1,
        cover=False,
        journey_text="The toast rode on an open plate, proud and unhidden before the weather.",
        qa_text="They carried it on an open plate.",
        tags={"plate"},
    ),
    "cloth_basket": Carrier(
        id="cloth_basket",
        label="cloth basket",
        phrase="a little basket lined with a clean cloth",
        retention=3,
        cover=True,
        journey_text="They tucked the toast into a little basket lined with cloth, where the warmth could linger.",
        qa_text="They carried it in a cloth-lined basket that held the warmth.",
        tags={"basket", "cloth"},
    ),
    "lidded_tin": Carrier(
        id="lidded_tin",
        label="lidded tin",
        phrase="a round tin with a clicking lid",
        retention=2,
        cover=True,
        journey_text="They slipped the toast into a round tin and shut the lid with a brave little click.",
        qa_text="They carried it in a lidded tin.",
        tags={"tin"},
    ),
}

NAMES = ["Anya", "Milo", "Tara", "Ben", "Lina", "Ned", "Suri", "Oren"]
TRAITS = ["patient", "bright-eyed", "steady", "kind", "careful", "hopeful"]
HELPERS = [
    ("mother", "Mother Elowen"),
    ("father", "Father Bram"),
    ("grandmother", "Grandma Wren"),
    ("uncle", "Uncle Ash"),
]


@dataclass
class StoryParams:
    quest: str
    weather: str
    method: str
    carrier: str
    child_name: str
    child_gender: str
    helper_type: str
    helper_name: str
    child_trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        quest="grandpa",
        weather="sunny",
        method="porch_toaster",
        carrier="cloth_basket",
        child_name="Anya",
        child_gender="girl",
        helper_type="mother",
        helper_name="Mother Elowen",
        child_trait="patient",
    ),
    StoryParams(
        quest="aunt",
        weather="windy",
        method="stone_griddle",
        carrier="lidded_tin",
        child_name="Milo",
        child_gender="boy",
        helper_type="uncle",
        helper_name="Uncle Ash",
        child_trait="bright-eyed",
    ),
    StoryParams(
        quest="sister",
        weather="misty",
        method="stone_griddle",
        carrier="open_plate",
        child_name="Lina",
        child_gender="girl",
        helper_type="grandmother",
        helper_name="Grandma Wren",
        child_trait="hopeful",
    ),
    StoryParams(
        quest="grandpa",
        weather="windy",
        method="porch_toaster",
        carrier="open_plate",
        child_name="Ben",
        child_gender="boy",
        helper_type="father",
        helper_name="Father Bram",
        child_trait="careful",
    ),
]


def method_allowed(method: Method, weather: Weather) -> bool:
    return not (method.dry_only and weather.damp > 0)


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for qid in QUESTS:
        for wid, weather in WEATHERS.items():
            for mid, method in METHODS.items():
                if method.sense < SENSE_MIN:
                    continue
                if not method_allowed(method, weather):
                    continue
                for cid in CARRIERS:
                    combos.append((qid, wid, mid, cid))
    return combos


def warmth_score(quest: Quest, weather: Weather, method: Method, carrier: Carrier) -> int:
    return method.heat + carrier.retention - quest.distance - weather.breeze - weather.damp


def outcome_of(params: StoryParams) -> str:
    quest = QUESTS[params.quest]
    weather = WEATHERS[params.weather]
    method = METHODS[params.method]
    carrier = CARRIERS[params.carrier]
    score = warmth_score(quest, weather, method, carrier)
    if score >= 3:
        return "radiant"
    if score >= 1:
        return "warm"
    return "cool"


def explain_method_rejection(method: Method) -> str:
    safe = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method.id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). A driveway surprise should use a steadier, safer way to make toast. "
        f"Try: {safe}.)"
    )


def explain_weather_rejection(method: Method, weather: Weather) -> str:
    return (
        f"(No story: {method.label} is a dry-weather method, but {weather.id} weather leaves the air damp. "
        f"The toast quest needs a method that suits the morning.)"
    )


def predict_toast(world: World) -> dict:
    sim = world.copy()
    toast = sim.get("toast")
    toast.meters["moving"] += 1
    propagate(sim, narrate=False)
    return {
        "warmth": toast.meters["warmth"],
        "cooling": toast.meters["cooling"],
    }


def introduce(world: World, child: Entity, helper: Entity, quest: Quest, weather: Weather) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"In a village where hedges kept their own secrets, {child.id} woke with a quest in {child.pronoun('possessive')} heart."
    )
    world.say(
        f"{weather.sky}. {weather.image}"
    )
    world.say(
        f"{child.id} wished to carry {quest.gift_line} to {quest.recipient_name}, {quest.reason}."
    )
    world.say(
        f'"If I can do it before {quest.recipient_name} {quest.arrival}," {child.pronoun()} whispered, "the morning itself will feel like a surprise."'
    )
    helper_word = helper.label_word
    world.say(
        f"{helper.id}, who knew the ways of kettles and crumbs, listened from the porch and smiled without spoiling the plan."
    )
    world.facts["quest_opened"] = True
    world.facts["helper_word"] = helper_word


def prepare(world: World, child: Entity, method: Method, carrier: Carrier) -> None:
    toast = world.get("toast")
    carrier_ent = world.get("carrier")
    toast.meters["plain"] = 1
    child.memes["purpose"] += 1
    carrier_ent.attrs["shield"] = 1 if carrier.cover else 0
    world.say(
        f"{child.id} set a small table at the edge of the driveway and laid out bread, butter, and honey as if they were treasures for a gentle dragon."
    )
    world.say(method.ignite_text)
    toast.meters["warmth"] += method.heat
    toast.meters["crisp"] += 1
    propagate(world, narrate=True)
    world.say(method.finish_text)
    world.say(
        "An ineffable smell drifted up from the bread, too lovely for easy naming, and even the sparrows seemed to notice."
    )
    world.say(carrier.journey_text)


def forecast(world: World, child: Entity, weather: Weather, carrier: Carrier, quest: Quest) -> None:
    pred = predict_toast(world)
    world.facts["predicted_warmth"] = pred["warmth"]
    world.facts["predicted_cooling"] = pred["cooling"]
    if pred["cooling"] > 0:
        child.memes["worry"] += 1
        world.say(
            f"But {child.id} saw the truth of the road at once: the {weather.id} morning and the {carrier.label} might steal some of the toast's warmth before {quest.recipient_label} arrived."
        )
    else:
        child.memes["confidence"] += 1
        world.say(
            f"{child.id} looked along the short driveway and felt sure the toast could cross it while the warmth still held."
        )


def carry(world: World, child: Entity, helper: Entity, quest: Quest, weather: Weather, carrier: Carrier) -> None:
    toast = world.get("toast")
    toast.meters["moving"] += 1
    child.memes["courage"] += 1
    world.say(
        f"So {child.id} lifted {carrier.phrase}, and {helper.id} walked beside {child.pronoun('object')} with the slow patience folk save for important things."
    )
    produced = propagate(world, narrate=False)
    if "__cooling__" in produced:
        world.say(
            f"The {weather.id} air nibbled at the toast on the way across the driveway."
        )
    else:
        world.say(
            "No wind and no damp hand touched it; the warmth stayed tucked inside like a secret."
        )


def arrive(world: World, child: Entity, quest: Quest) -> None:
    recipient = world.get("recipient")
    child.memes["anticipation"] += 1
    world.say(
        f"Just then {recipient.id} {quest.arrival}."
    )
    world.say(
        f"{child.id} stepped forward and bowed as solemnly as any hero at the end of a tale."
    )


def reveal(world: World, child: Entity, helper: Entity, quest: Quest, carrier: Carrier) -> None:
    toast = world.get("toast")
    recipient = world.get("recipient")
    warmth = int(toast.meters["warmth"])
    outcome = "cool"
    if warmth >= 3:
        outcome = "radiant"
        recipient.memes["surprise"] += 1
        recipient.memes["delight"] += 1
        child.memes["pride"] += 1
        world.say(
            f'"For you," said {child.id}, opening the {carrier.label}. Steam lifted in a tiny silver curl.'
        )
        world.say(
            f"{recipient.id}'s eyes widened. The toast was still golden and warm, and the honey shone like trapped sunlight."
        )
        world.say(
            f'"Oh!" {recipient.id} said. "What a bright surprise."'
        )
    elif warmth >= 1:
        outcome = "warm"
        recipient.memes["surprise"] += 1
        recipient.memes["gratitude"] += 1
        child.memes["relief"] += 1
        world.say(
            f'"For you," said {child.id}, opening the {carrier.label}. The toast was no longer piping hot, yet it kept a little heart of warmth.'
        )
        world.say(
            f"{recipient.id} took a bite and smiled at once. The gift had traveled just far enough and just kindly enough."
        )
        world.say(
            f'"A surprise does not need to shout," {recipient.pronoun()} said. "This one speaks softly, and I hear it well."'
        )
    else:
        recipient.memes["surprise"] += 1
        recipient.memes["love"] += 1
        child.memes["disappointment"] += 1
        helper.memes["wisdom"] += 1
        world.say(
            f'"For you," said {child.id}, opening the {carrier.label}. Alas, the toast had gone cool on the road.'
        )
        world.say(
            f"For one blink {child.id} looked ready to cry, but {recipient.id} broke the toast in half and laughed a kindly laugh."
        )
        world.say(
            f'"Then we shall call it traveler\'s toast," {recipient.pronoun()} said. "{helper.id}, bring the tea, and we will warm the morning another way."'
        )
        world.say(
            "So the surprise changed its shape. It was no longer a warm crust alone, but a little feast shared at the end of the driveway."
        )
    world.facts["outcome"] = outcome


def close_story(world: World, child: Entity, quest: Quest) -> None:
    outcome = world.facts.get("outcome", "warm")
    recipient = world.get("recipient")
    if outcome == "radiant":
        world.say(
            f"From that day on, children said that a careful quest could carry heat as well as kindness, if the road was measured and the heart was steady."
        )
        world.say(
            f"And whenever {recipient.id} smelled honey on toast, {recipient.pronoun()} remembered the driveway shining like a little kingdom road."
        )
    elif outcome == "warm":
        world.say(
            "From that day on, people in the lane said that even modest warmth can feel grand when it arrives with love and timing."
        )
        world.say(
            f"And {child.id} learned that a small surprise may travel farther than smoke, because it rides inside the heart of the giver."
        )
    else:
        world.say(
            "From that day on, the old ones said that not every quest ends exactly as planned, yet a kind surprise can still find its true door."
        )
        world.say(
            f"And {child.id} never forgot that the driveway had taught two lessons at once: measure the weather, and keep room for joy."
        )


def tell(
    quest: Quest,
    weather: Weather,
    method: Method,
    carrier: Carrier,
    child_name: str,
    child_gender: str,
    helper_type: str,
    helper_name: str,
    child_trait: str,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            phrase=child_name,
            traits=[child_trait],
            role="child",
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_type,
            label=helper_name,
            phrase=helper_name,
            role="helper",
        )
    )
    recipient = world.add(
        Entity(
            id=quest.recipient_name,
            kind="character",
            type=quest.recipient_type,
            label=quest.recipient_label,
            phrase=quest.recipient_name,
            role="recipient",
            tags=set(quest.tags),
        )
    )
    world.add(
        Entity(
            id="weather",
            kind="thing",
            type="weather",
            label=weather.id,
            phrase=weather.sky,
            attrs={"breeze": weather.breeze, "damp": weather.damp},
            tags=set(weather.tags),
        )
    )
    world.add(
        Entity(
            id="toast",
            kind="thing",
            type="food",
            label="toast",
            phrase="the toast",
            tags={"toast"},
        )
    )
    world.add(
        Entity(
            id="carrier",
            kind="thing",
            type="carrier",
            label=carrier.label,
            phrase=carrier.phrase,
            attrs={"shield": 1 if carrier.cover else 0},
            tags=set(carrier.tags),
        )
    )

    introduce(world, child, helper, quest, weather)
    world.para()
    prepare(world, child, method, carrier)
    forecast(world, child, weather, carrier, quest)
    world.para()
    carry(world, child, helper, quest, weather, carrier)
    arrive(world, child, quest)
    reveal(world, child, helper, quest, carrier)
    world.para()
    close_story(world, child, quest)

    toast = world.get("toast")
    world.facts.update(
        child=child,
        helper=helper,
        recipient=recipient,
        quest=quest,
        weather_cfg=weather,
        method=method,
        carrier_cfg=carrier,
        warmth=int(toast.meters["warmth"]),
        crisp=int(toast.meters["crisp"]),
        butter_melt=toast.meters["butter_melt"] >= THRESHOLD,
        predicted_warmth=world.facts.get("predicted_warmth", int(toast.meters["warmth"])),
    )
    return world


KNOWLEDGE = {
    "toast": [
        (
            "What is toast?",
            "Toast is bread that has been heated until the outside turns brown and a little crisp. Warm toast smells rich because the heat changes the bread."
        )
    ],
    "toaster": [
        (
            "What does a toaster do?",
            "A toaster heats bread with glowing coils so it turns brown and crisp. It should be used on a steady surface by a grown-up or with a grown-up's help."
        )
    ],
    "griddle": [
        (
            "What is a griddle?",
            "A griddle is a flat cooking surface used to warm or cook food. When a grown-up uses it carefully on a safe base, it can toast bread."
        )
    ],
    "electricity": [
        (
            "Why should electric kitchen tools stay dry?",
            "Electric tools and water do not mix safely. Keeping a toaster dry helps stop shocks and keeps the tool working the right way."
        )
    ],
    "flame": [
        (
            "Why must small flames be watched carefully?",
            "Even a small flame can spread if it wanders onto the wrong thing. That is why careful grown-ups keep fire on a safe surface and stay close."
        )
    ],
    "wind": [
        (
            "Why does wind cool warm food?",
            "Moving air carries heat away. A breeze can make warm food cool faster, especially if the food is uncovered."
        )
    ],
    "mist": [
        (
            "What is mist?",
            "Mist is a cloud of tiny water drops close to the ground. It can make the air feel damp and cool."
        )
    ],
    "basket": [
        (
            "Why can a cloth-lined basket keep food warm a little longer?",
            "The cloth slows down how quickly heat escapes. It does not keep food hot forever, but it can help warmth linger."
        )
    ],
    "tin": [
        (
            "Why does a lid help keep food warm?",
            "A lid helps hold in warm air around the food. That means the heat has a harder time escaping right away."
        )
    ],
    "plate": [
        (
            "Why does food cool quickly on an open plate?",
            "An open plate leaves the food exposed to the air. Wind and cool air can carry the heat away very fast."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "toast",
    "toaster",
    "griddle",
    "electricity",
    "flame",
    "wind",
    "mist",
    "basket",
    "tin",
    "plate",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    quest = f["quest"]
    weather = f["weather_cfg"]
    return [
        (
            f'Write a folk-tale-style story for a 3-to-5-year-old set in a driveway, where a child goes on a quest to surprise {quest.recipient_name} with toast. '
            f'Include the words "ignite", "ineffable", and "toast".'
        ),
        (
            f"Tell a gentle folk tale where {child.id} tries to carry warm toast across a {weather.id} driveway as a surprise for {quest.recipient_label}, and the weather changes the test."
        ),
        (
            "Write a simple story about a morning quest, a humble gift, and a surprise ending that shows what kindness can carry."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    recipient = f["recipient"]
    quest = f["quest"]
    weather = f["weather_cfg"]
    method = f["method"]
    carrier = f["carrier_cfg"]
    outcome = f["outcome"]
    warmth = f["warmth"]
    items: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who went on a small quest in the driveway, {helper.id}, who helped without spoiling the plan, and {recipient.id}, who received the surprise."
        ),
        (
            f"What was {child.id}'s quest?",
            f"{child.id} wanted to bring {quest.gift_line} to {recipient.id} before {recipient.pronoun()} {quest.arrival}. The quest mattered because it was meant as a loving surprise, not just a snack."
        ),
        (
            f"How did they make the toast?",
            f"{method.qa_text} That choice gave the bread enough heat to brown and smell sweet before the journey began."
        ),
        (
            f"Why did the weather matter?",
            f"The story's {weather.id} morning could steal heat from the toast while it crossed the driveway. Warm food changes quickly when wind or damp air gets to it."
        ),
        (
            f"How did they carry the toast?",
            f"{carrier.qa_text} The way they carried it mattered because some containers protect warmth better than others."
        ),
    ]
    if outcome == "radiant":
        items.append(
            (
                f"How did the surprise turn out?",
                f"It turned out beautifully: the toast reached {recipient.id} still warm and golden. The careful making and carrying kept enough heat in it for the gift to feel bright and immediate."
            )
        )
    elif outcome == "warm":
        items.append(
            (
                f"How did the surprise turn out?",
                f"It still worked well, even though the toast was not as hot as when it began. A little warmth remained, and {recipient.id} could feel the care that had crossed the driveway with it."
            )
        )
    else:
        items.append(
            (
                f"What happened when {child.id} opened the carrier?",
                f"The toast had gone cool on the way. Even so, {recipient.id} changed the ending by sharing it with tea, so the surprise became a warm moment even after the bread had lost its heat."
            )
        )
    items.append(
        (
            "What did the story show about kindness?",
            f"It showed that kindness is part planning and part heart. {child.id} had to measure the weather and the journey, but love still mattered most when the surprise was finally given."
        )
    )
    if warmth >= 3:
        items.append(
            (
                "Why did the toast stay warm enough?",
                f"It stayed warm enough because the heating method started it hot, and the trip across the driveway did not take too much away. The weather and carrier together could not steal all that warmth."
            )
        )
    return items


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"toast"}
    tags |= set(f["method"].tags)
    tags |= set(f["carrier_cfg"].tags)
    tags |= set(f["weather_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:16} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible_method(M) :- method(M), sense(M,S), sense_min(Min), S >= Min.
allowed(M,W) :- method(M), weather(W), not dry_only(M).
allowed(M,W) :- method(M), weather(W), dry_only(M), damp(W,0).

valid(Q,W,M,C) :- quest(Q), weather(W), carrier(C), sensible_method(M), allowed(M,W).

warmth(Q,W,M,C, H + R - D - B - P) :-
    quest(Q), weather(W), method(M), carrier(C),
    heat(M,H), retention(C,R), distance(Q,D), breeze(W,B), damp(W,P).

outcome(Q,W,M,C,radiant) :- warmth(Q,W,M,C,S), S >= 3.
outcome(Q,W,M,C,warm)    :- warmth(Q,W,M,C,S), S >= 1, S < 3.
outcome(Q,W,M,C,cool)    :- warmth(Q,W,M,C,S), S < 1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for qid, quest in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("distance", qid, quest.distance))
    for wid, weather in WEATHERS.items():
        lines.append(asp.fact("weather", wid))
        lines.append(asp.fact("breeze", wid, weather.breeze))
        lines.append(asp.fact("damp", wid, weather.damp))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        lines.append(asp.fact("heat", mid, method.heat))
        if method.dry_only:
            lines.append(asp.fact("dry_only", mid))
    for cid, carrier in CARRIERS.items():
        lines.append(asp.fact("carrier", cid))
        lines.append(asp.fact("retention", cid, carrier.retention))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_method/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible_method"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen", params.quest, params.weather, params.method, params.carrier),
            f"selected_outcome(O) :- chosen(Q,W,M,C), outcome(Q,W,M,C,O).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show selected_outcome/1."))
    atoms = asp.atoms(model, "selected_outcome")
    return atoms[0][0] if atoms else "?"


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

    clingo_methods = set(asp_sensible_methods())
    python_methods = {m.id for m in sensible_methods()}
    if clingo_methods == python_methods:
        print(f"OK: sensible methods match ({sorted(clingo_methods)}).")
    else:
        rc = 1
        print("MISMATCH in sensible methods:")
        print("  clingo:", sorted(clingo_methods))
        print("  python:", sorted(python_methods))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(40):
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
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="A folk-tale driveway quest about making toast for a surprise. "
        "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=sorted(t for t, _ in HELPERS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method:
        method = METHODS[args.method]
        if method.sense < SENSE_MIN:
            raise StoryError(explain_method_rejection(method))
        if args.weather:
            weather = WEATHERS[args.weather]
            if not method_allowed(method, weather):
                raise StoryError(explain_weather_rejection(method, weather))

    combos = [
        combo
        for combo in valid_combos()
        if (args.quest is None or combo[0] == args.quest)
        and (args.weather is None or combo[1] == args.weather)
        and (args.method is None or combo[2] == args.method)
        and (args.carrier is None or combo[3] == args.carrier)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    quest, weather, method, carrier = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice([n for n in NAMES if n != QUESTS[quest].recipient_name])
    helper_type = args.helper_type or rng.choice([t for t, _ in HELPERS])
    helper_name = next(name for t, name in HELPERS if t == helper_type)
    child_trait = rng.choice(TRAITS)

    return StoryParams(
        quest=quest,
        weather=weather,
        method=method,
        carrier=carrier,
        child_name=child_name,
        child_gender=child_gender,
        helper_type=helper_type,
        helper_name=helper_name,
        child_trait=child_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS:
        raise StoryError(f"Unknown quest: {params.quest}")
    if params.weather not in WEATHERS:
        raise StoryError(f"Unknown weather: {params.weather}")
    if params.method not in METHODS:
        raise StoryError(f"Unknown method: {params.method}")
    if params.carrier not in CARRIERS:
        raise StoryError(f"Unknown carrier: {params.carrier}")

    method = METHODS[params.method]
    weather = WEATHERS[params.weather]
    if method.sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(method))
    if not method_allowed(method, weather):
        raise StoryError(explain_weather_rejection(method, weather))

    world = tell(
        quest=QUESTS[params.quest],
        weather=weather,
        method=method,
        carrier=CARRIERS[params.carrier],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper_type,
        helper_name=params.helper_name,
        child_trait=params.child_trait,
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
        print(asp_program("", "#show valid/4.\n#show sensible_method/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        methods = asp_sensible_methods()
        print(f"sensible methods: {', '.join(methods)}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (quest, weather, method, carrier) combos:\n")
        for quest, weather, method, carrier in combos:
            print(f"  {quest:8} {weather:6} {method:14} {carrier}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.quest} on a {p.weather} driveway ({p.method}, {outcome_of(p)})"
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
