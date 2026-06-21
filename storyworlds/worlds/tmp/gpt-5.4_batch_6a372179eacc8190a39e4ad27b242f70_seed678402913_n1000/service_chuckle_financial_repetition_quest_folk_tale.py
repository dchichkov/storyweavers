#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/service_chuckle_financial_repetition_quest_folk_tale.py
===================================================================================

A standalone story world for a small folk-tale quest: a child carries silver
coins on a financial errand to pay for a village service, meets three needy
strangers on the road, and learns that an open hand can make a hard road short.

The tale is built as a simulation rather than a frozen template. The child has a
money pouch, a supply satchel, and a path with repeated encounters. Kind acts
change the state of helpers, and grateful helpers can later change the ending of
the quest.

Run it
------
    python storyworlds/worlds/gpt-5.4/service_chuckle_financial_repetition_quest_folk_tale.py
    python storyworlds/worlds/gpt-5.4/service_chuckle_financial_repetition_quest_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/service_chuckle_financial_repetition_quest_folk_tale.py --trace
    python storyworlds/worlds/gpt-5.4/service_chuckle_financial_repetition_quest_folk_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/service_chuckle_financial_repetition_quest_folk_tale.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandmother", "grandfather": "grandfather"}.get(self.type, self.type)


@dataclass
class ServiceTask:
    id: str
    label: str
    worker: str
    place: str
    price: int
    difficulty: int
    ending_image: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Pack:
    id: str
    label: str
    phrase: str
    capacity: int
    items: set[str] = field(default_factory=set)
    image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    place: str
    need: int
    problem: str
    solved: str
    late: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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

    def helpers(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role == "helper"]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_gratitude(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    for helper in world.helpers():
        if helper.meters["relief"] < THRESHOLD:
            continue
        sig = ("gratitude", helper.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        helper.memes["gratitude"] += 1
        hero.memes["kindness"] += 1
        out.append("__gratitude__")
    return out


def _r_burden(world: World) -> list[str]:
    hero = world.get("hero")
    pouch = world.get("pouch")
    if pouch.meters["lost"] < THRESHOLD:
        return []
    sig = ("worry", "hero")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    return ["__worry__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="gratitude", tag="social", apply=_r_gratitude),
    Rule(name="burden", tag="social", apply=_r_burden),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for bit in produced:
            if bit == "__gratitude__":
                continue
            if bit == "__worry__":
                continue
    return produced


SERVICES = {
    "well_rope": ServiceTask(
        id="well_rope",
        label="the rope-mender's service",
        worker="rope-mender",
        place="the well house",
        price=2,
        difficulty=1,
        ending_image="the bucket rose from the well with a clean splash",
        lesson="kindness can shorten a road",
        tags={"service", "water", "money"},
    ),
    "millstone": ServiceTask(
        id="millstone",
        label="the miller's grinding service",
        worker="miller",
        place="the old mill",
        price=3,
        difficulty=2,
        ending_image="the mill wheel turned slowly, and warm flour dust shone in the light",
        lesson="an open hand brings help back to you",
        tags={"service", "mill", "money"},
    ),
    "bell_polish": ServiceTask(
        id="bell_polish",
        label="the bell-keeper's polishing service",
        worker="bell-keeper",
        place="the hill chapel",
        price=4,
        difficulty=3,
        ending_image="the little bell rang clear enough to send birds up from the roof",
        lesson="a generous heart makes heavy work light",
        tags={"service", "bell", "money"},
    ),
}

PACKS = {
    "small_purse": Pack(
        id="small_purse",
        label="small purse",
        phrase="a small leather purse tied to a bread-colored satchel",
        capacity=2,
        items={"crumbs"},
        image="The purse was small, but it bumped bravely at the child's side.",
        tags={"financial", "money", "crumbs"},
    ),
    "market_bag": Pack(
        id="market_bag",
        label="market bag",
        phrase="a market bag with a coin purse tucked inside",
        capacity=3,
        items={"crumbs", "carrot"},
        image="The market bag smelled faintly of bread and sweet carrots.",
        tags={"financial", "money", "crumbs", "carrot"},
    ),
    "traveler_satchel": Pack(
        id="traveler_satchel",
        label="traveler's satchel",
        phrase="a traveler's satchel with a stout coin purse sewn inside",
        capacity=4,
        items={"crumbs", "carrot", "shawl"},
        image="The satchel sat snug against the child's shoulder, ready for a long walk.",
        tags={"financial", "money", "crumbs", "carrot", "shawl"},
    ),
}

OBSTACLES = {
    "bridge_wind": Obstacle(
        id="bridge_wind",
        label="the windy bridge",
        place="the willow bridge",
        need=1,
        problem="A gust danced across the planks and snatched at the coin pouch.",
        solved="The road steadied, and the child crossed the bridge with the silver safe.",
        late="The wind tugged the pouch loose, and one silver piece skittered away before the child could catch it.",
        tags={"bridge", "wind"},
    ),
    "muddy_ford": Obstacle(
        id="muddy_ford",
        label="the muddy ford",
        place="the brown ford",
        need=2,
        problem="The shallow water had turned to sucking mud, and every step tried to hold the child fast.",
        solved="Step by step, the child came out of the mud with clean silver and a lifted chin.",
        late="The child fought free at last, but the delay left the coins muddy and the sun already slipping down.",
        tags={"mud", "ford"},
    ),
    "thorn_hill": Obstacle(
        id="thorn_hill",
        label="the thorn hill",
        place="the steep thorn hill",
        need=3,
        problem="A bramble-choked path twisted up the hill, and the pouch snagged whenever the child tried to climb.",
        solved="The way opened, and the child reached the top while the silver still shone in the purse.",
        late="By the time the child untangled the pouch and climbed through alone, the chapel door was nearly shut for the day.",
        tags={"hill", "thorns"},
    ),
}

HELPER_ORDER = ["sparrow", "donkey", "old_woman"]
HELPER_NEEDS = {"sparrow": "crumbs", "donkey": "carrot", "old_woman": "shawl"}
HELPER_LABELS = {
    "sparrow": "a hungry sparrow",
    "donkey": "a tired gray donkey",
    "old_woman": "an old woman with chilly hands",
}
HELPER_TYPES = {"sparrow": "bird", "donkey": "animal", "old_woman": "woman"}
HELPER_PLACES = {
    "sparrow": "under a willow branch",
    "donkey": "beside a crooked fence",
    "old_woman": "near the hill gate",
}
HELPER_REQUESTS = {
    "sparrow": '"Little traveler, have you one crumb to spare?"',
    "donkey": '"Little traveler, have you one carrot end for my empty stomach?"',
    "old_woman": '"Little traveler, have you a spare shawl-cloth for these cold hands?"',
}
HELPER_THANKS = {
    "sparrow": "The sparrow gave a bright chirp and hopped in a grateful circle.",
    "donkey": "The donkey dipped its head and let out a soft, friendly snort.",
    "old_woman": 'The old woman wrapped the cloth around her hands and gave a warm chuckle. "A kind road remembers kind feet," she said.',
}
HELPER_REFUSALS = {
    "sparrow": "The sparrow fluttered away hungry, and the branch felt lonely after it.",
    "donkey": "The donkey lowered its ears and went back to nosing the dry ground.",
    "old_woman": "The old woman only nodded and folded her cold hands together.",
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Nora", "Elsa", "Pia", "Marta", "Anya"]
BOY_NAMES = ["Ivo", "Tomas", "Milo", "Pavel", "Niko", "Bram", "Luka", "Stefan"]
TRAITS = ["patient", "curious", "steady", "bright", "hopeful", "careful"]
GUARDIANS = ["grandmother", "grandfather"]


@dataclass
class StoryParams:
    service: str
    pack: str
    obstacle: str
    virtue: str
    name: str
    gender: str
    guardian: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        service="well_rope",
        pack="small_purse",
        obstacle="bridge_wind",
        virtue="open_hand",
        name="Lina",
        gender="girl",
        guardian="grandmother",
        trait="steady",
    ),
    StoryParams(
        service="millstone",
        pack="market_bag",
        obstacle="muddy_ford",
        virtue="open_hand",
        name="Milo",
        gender="boy",
        guardian="grandfather",
        trait="patient",
    ),
    StoryParams(
        service="bell_polish",
        pack="traveler_satchel",
        obstacle="thorn_hill",
        virtue="open_hand",
        name="Anya",
        gender="girl",
        guardian="grandmother",
        trait="hopeful",
    ),
    StoryParams(
        service="millstone",
        pack="market_bag",
        obstacle="thorn_hill",
        virtue="tight_fist",
        name="Pavel",
        gender="boy",
        guardian="grandfather",
        trait="careful",
    ),
    StoryParams(
        service="bell_polish",
        pack="traveler_satchel",
        obstacle="muddy_ford",
        virtue="tight_fist",
        name="Tessa",
        gender="girl",
        guardian="grandmother",
        trait="bright",
    ),
]


def valid_combo(service_id: str, pack_id: str) -> bool:
    service = SERVICES[service_id]
    pack = PACKS[pack_id]
    return pack.capacity >= service.price


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, service in SERVICES.items():
        for pid, pack in PACKS.items():
            if pack.capacity < service.price:
                continue
            for oid, obstacle in OBSTACLES.items():
                if obstacle.need <= service.difficulty + 1:
                    combos.append((sid, pid, oid))
    return combos


def helper_count(pack: Pack, virtue: str) -> int:
    if virtue != "open_hand":
        return 0
    return len(pack.items & {"crumbs", "carrot", "shawl"})


def outcome_of(params: StoryParams) -> str:
    pack = PACKS[params.pack]
    obstacle = OBSTACLES[params.obstacle]
    return "delivered" if helper_count(pack, params.virtue) >= obstacle.need else "late"


def explain_rejection(service_id: str, pack_id: str, obstacle_id: Optional[str] = None) -> str:
    service = SERVICES[service_id]
    pack = PACKS[pack_id]
    if pack.capacity < service.price:
        return (
            f"(No story: {pack.label} can only carry payment for {pack.capacity} silver piece"
            f"{'' if pack.capacity == 1 else 's'}, but {service.label} costs {service.price}. "
            f"The financial errand must start with enough money.)"
        )
    if obstacle_id is not None:
        obstacle = OBSTACLES[obstacle_id]
        if obstacle.need > service.difficulty + 1:
            return (
                f"(No story: {obstacle.label} is too harsh for the quest to {service.place}. "
                f"This little folk tale keeps the road difficult, but not wildly out of scale.)"
            )
    return "(No story: the requested choices do not make a reasonable quest.)"


def share(world: World, helper_id: str, item: str, narrate: bool = True) -> None:
    hero = world.get("hero")
    helper = world.get(helper_id)
    hero.attrs["shared_items"].append(item)
    helper.meters["relief"] += 1
    propagate(world, narrate=False)
    if not narrate:
        return
    if helper_id == "sparrow":
        world.say(
            f'{hero.id} opened the satchel and tipped out a few crumbs onto a flat stone. '
            f"{HELPER_THANKS[helper_id]}"
        )
    elif helper_id == "donkey":
        world.say(
            f"{hero.id} broke off the carrot end and held it out with both hands. "
            f"{HELPER_THANKS[helper_id]}"
        )
    else:
        world.say(
            f"{hero.id} took the spare shawl-cloth from the satchel and tucked it around the old woman's hands. "
            f"{HELPER_THANKS[helper_id]}"
        )


def refuse(world: World, helper_id: str, narrate: bool = True) -> None:
    hero = world.get("hero")
    hero.memes["stinginess"] += 1
    if narrate:
        world.say(
            f'{hero.id} held the satchel close and said, "I must keep all I have for my errand." '
            f"{HELPER_REFUSALS[helper_id]}"
        )


def predict_outcome(service: ServiceTask, pack: Pack, obstacle: Obstacle, virtue: str) -> dict:
    help_tokens = helper_count(pack, virtue)
    return {
        "enough_money": pack.capacity >= service.price,
        "help_tokens": help_tokens,
        "success": help_tokens >= obstacle.need,
    }


def introduce(world: World, service: ServiceTask, pack: Pack) -> None:
    hero = world.get("hero")
    guardian = world.get("guardian")
    pouch = world.get("pouch")
    hero.memes["duty"] += 1
    world.say(
        f"In a little village tucked between willows and hills lived {hero.id}, a {hero.traits[0]} little {hero.type}."
    )
    world.say(
        f"One morning, {hero.pronoun('possessive')} {guardian.label_word} placed {pack.phrase} into "
        f"{hero.pronoun('possessive')} hands. Inside the purse lay {service.price} bright silver pieces for "
        f"{service.label} at {service.place}."
    )
    world.say(
        f'"This is a financial errand," said {guardian.label_word}. "Walk straight, pay fairly, and come home before the stars wake."'
    )
    world.say(pack.image)
    pouch.meters["silver"] = float(service.price)


def set_out(world: World, service: ServiceTask) -> None:
    hero = world.get("hero")
    world.say(
        f"So {hero.id} set out on the road to {service.place}, where the {service.worker} was waiting to begin the village service."
    )


def repeated_encounters(world: World, virtue: str, pack: Pack) -> None:
    hero = world.get("hero")
    first = True
    for helper_id in HELPER_ORDER:
        helper = world.get(helper_id)
        item = HELPER_NEEDS[helper_id]
        if first:
            world.say(
                f"First, {HELPER_PLACES[helper_id]}, {HELPER_LABELS[helper_id]} called, {HELPER_REQUESTS[helper_id]}"
            )
            first = False
        else:
            world.say(
                f"Then, {HELPER_PLACES[helper_id]}, {HELPER_LABELS[helper_id]} called, {HELPER_REQUESTS[helper_id]}"
            )
        if virtue == "open_hand" and item in pack.items:
            share(world, helper_id, item, narrate=True)
        else:
            refuse(world, helper_id, narrate=True)
        if helper_id != HELPER_ORDER[-1]:
            world.say(f"And {hero.id} walked on with the coin purse tapping against {hero.pronoun('possessive')} side.")


def face_obstacle(world: World, obstacle: Obstacle) -> None:
    world.say(
        f"At last the child came to {obstacle.place}. {obstacle.problem}"
    )


def helpers_return(world: World) -> int:
    hero = world.get("hero")
    helped = 0
    if world.get("sparrow").memes["gratitude"] >= THRESHOLD:
        helped += 1
        world.say(
            f"Back came the sparrow, quick as a needle of light. It swooped low and showed {hero.id} the safest plank and where the loose string of the purse had caught."
        )
    if world.get("donkey").memes["gratitude"] >= THRESHOLD:
        helped += 1
        world.say(
            f"Back came the gray donkey, patient and strong. It knelt so {hero.id} could steady a foot and rise where the road was worst."
        )
    if world.get("old_woman").memes["gratitude"] >= THRESHOLD:
        helped += 1
        world.say(
            f"Back came the old woman with her shawl-cloth tied warm around her hands. With another soft chuckle, she bound the purse tight and pointed out the clear path through trouble."
        )
    return helped


def deliver(world: World, service: ServiceTask, obstacle: Obstacle) -> None:
    hero = world.get("hero")
    guardian = world.get("guardian")
    pouch = world.get("pouch")
    worker = world.get("worker")
    world.say(obstacle.solved)
    world.para()
    pouch.meters["paid"] = float(service.price)
    world.say(
        f"Before the sun slipped away, {hero.id} reached {service.place} and laid the silver into the {worker.label}'s broad palm."
    )
    world.say(
        f'The {worker.label} bowed and said, "You have paid for the village service honestly." Soon {service.ending_image}.'
    )
    world.say(
        f"When {hero.id} came home, {guardian.label_word} smiled to hear the tale. From then on, people in the village said that {service.lesson}."
    )


def arrive_late(world: World, service: ServiceTask, obstacle: Obstacle) -> None:
    hero = world.get("hero")
    guardian = world.get("guardian")
    pouch = world.get("pouch")
    worker = world.get("worker")
    pouch.meters["lost"] += 1
    propagate(world, narrate=False)
    world.say(obstacle.late)
    world.para()
    remaining = service.price - 1
    pouch.meters["paid"] = float(remaining)
    world.say(
        f"When {hero.id} finally reached {service.place}, only {remaining} silver piece"
        f"{'' if remaining == 1 else 's'} remained in the purse."
    )
    world.say(
        f'The {worker.label} looked kindly at the tired child and said, "The service can still be done, but one lost coin must be earned."'
    )
    world.say(
        f"So {hero.id} swept, carried, and helped until the last bit was worked off. By the time {hero.pronoun()} walked home in the evening light, {hero.pronoun()} knew that a tight fist can make a short road long."
    )
    world.say(
        f"{guardian.label_word.capitalize()} listened at the door and nodded. After that day, {hero.id} remembered to carry silver with care and kindness with it."
    )


def tell(service: ServiceTask, pack: Pack, obstacle: Obstacle, virtue: str, name: str,
         gender: str, guardian_type: str, trait: str) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=gender, label=name, traits=[trait], role="hero"))
    guardian = world.add(Entity(id="guardian", kind="character", type=guardian_type, label=guardian_type, role="guardian"))
    pouch = world.add(Entity(id="pouch", type="pouch", label="coin purse", role="pouch"))
    worker = world.add(Entity(id="worker", kind="character", type="adult", label=service.worker, role="worker"))
    world.add(Entity(id="sparrow", kind="character", type="bird", label="sparrow", role="helper"))
    world.add(Entity(id="donkey", kind="character", type="animal", label="donkey", role="helper"))
    world.add(Entity(id="old_woman", kind="character", type="woman", label="old woman", role="helper"))

    hero.id = name
    world.entities[name] = world.entities.pop("hero")
    guardian.id = guardian_type.capitalize()
    world.entities[guardian.id] = world.entities.pop("guardian")
    worker.id = service.worker.capitalize()
    world.entities[worker.id] = world.entities.pop("worker")

    world.facts["hero_id"] = name
    world.facts["guardian_id"] = guardian.id
    world.facts["worker_id"] = worker.id

    introduce(world, service, pack)
    set_out(world, service)

    world.para()
    repeated_encounters(world, virtue, pack)

    world.para()
    face_obstacle(world, obstacle)
    returned = helpers_return(world)
    world.facts["returned_helpers"] = returned

    if returned >= obstacle.need:
        deliver(world, service, obstacle)
        outcome = "delivered"
    else:
        arrive_late(world, service, obstacle)
        outcome = "late"

    hero_ent = world.get(name)
    guardian_ent = world.get(guardian.id)
    worker_ent = world.get(worker.id)
    world.facts.update(
        hero=hero_ent,
        guardian=guardian_ent,
        worker=worker_ent,
        service=service,
        pack=pack,
        obstacle=obstacle,
        virtue=virtue,
        outcome=outcome,
        kindness=int(hero_ent.memes["kindness"]),
        shared_items=list(hero_ent.attrs.get("shared_items", [])),
        help_tokens=returned,
        enough_money=pack.capacity >= service.price,
        financial_word_used=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    service = f["service"]
    obstacle = f["obstacle"]
    virtue = f["virtue"]
    prompt1 = (
        'Write a short folk tale for a 3-to-5-year-old that includes the words '
        '"service", "chuckle", and "financial", and uses a quest with repetition.'
    )
    prompt2 = (
        f"Tell a folk-tale quest about a little {hero.type} named {hero.id} who carries silver to pay for "
        f"{service.label}, meets three strangers on the road, and faces {obstacle.label}."
    )
    if virtue == "open_hand":
        prompt3 = (
            "Write a gentle repetition story where each kind deed returns as help at the end, proving that generosity can guide a traveler."
        )
    else:
        prompt3 = (
            "Write a gentle cautionary folk tale where a child guards the money too tightly, learns from a hard road, and comes home wiser."
        )
    return [prompt1, prompt2, prompt3]


KNOWLEDGE = {
    "financial": [
        (
            "What does financial mean?",
            "Financial means having to do with money or paying for things. A financial errand is a job where money matters."
        )
    ],
    "service": [
        (
            "What is a service?",
            "A service is work someone does to help other people, like fixing, carrying, or mending something. You pay for the helpful work, not for a toy."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey with a job to do before you can come home. In stories, a quest often has tests along the way."
        )
    ],
    "folk_tale": [
        (
            "What is a folk tale?",
            "A folk tale is an old-style story passed from one person to another. It often uses repeating parts and a simple lesson at the end."
        )
    ],
    "money": [
        (
            "Why do people put coins in a purse?",
            "A purse keeps coins together so they do not fall out on the road. It helps you carry money safely."
        )
    ],
    "kindness": [
        (
            "Why can kindness help someone later?",
            "When you help others, they remember it and may help you when you are in trouble. Kindness can travel in a circle."
        )
    ],
    "mill": [
        (
            "What does a miller do?",
            "A miller uses a mill to grind grain into flour. Flour can then be used to bake bread."
        )
    ],
    "bell": [
        (
            "Why do bells ring in stories and villages?",
            "Bells can call people together or tell them the time. A clear bell is useful because everyone can hear it."
        )
    ],
    "water": [
        (
            "Why does a village need a strong well rope?",
            "A strong well rope helps people lift water safely from the well. If the rope breaks, getting water is much harder."
        )
    ],
}
KNOWLEDGE_ORDER = ["financial", "service", "quest", "folk_tale", "money", "kindness", "mill", "bell", "water"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    guardian = f["guardian"]
    service = f["service"]
    obstacle = f["obstacle"]
    shared = f["shared_items"]
    virtue = f["virtue"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little {hero.type} on a quest to pay for {service.label}. {guardian.label_word.capitalize()} sends {hero.pronoun('object')} out with silver and a clear duty."
        ),
        (
            "What was the child's job?",
            f"{hero.id}'s job was to carry silver to {service.place} and pay fairly for the village service. It was a financial errand because the coins had to arrive safely."
        ),
        (
            "What repeating thing happened on the road?",
            f"Three times, someone in need called to {hero.id} on the road: a sparrow, a donkey, and an old woman. That repeating pattern turns the walk into a folk-tale quest with tests."
        ),
    ]
    if virtue == "open_hand":
        if shared:
            items = ", ".join(shared)
            qa.append(
                (
                    f"How did {hero.id} treat the strangers?",
                    f"{hero.id} shared {items} along the way instead of clutching everything close. Each small gift changed a needy traveler into a grateful helper."
                )
            )
        qa.append(
            (
                "Why did help come back at the obstacle?",
                f"Help came back because the strangers remembered the child's kindness. Their return gave {hero.id} enough help to pass {obstacle.label} and keep the silver safe."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"{hero.id} reached {service.place} in time and paid for the service honestly. The ending image shows that kindness traveled with the child all the way to the goal."
            )
        )
    else:
        qa.append(
            (
                f"Why was {hero.id} late?",
                f"{hero.id} kept the satchel shut and went on alone, so no grateful helpers returned when the hard place came. Because the child faced {obstacle.label} without help, the money was delayed and one coin was lost."
            )
        )
        qa.append(
            (
                "What lesson did the child learn?",
                "The child learned that guarding money without kindness can make the road harder. By the end, the errand is finished only after extra work, so the lesson comes from cause and consequence."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"{hero.id} still reached the worker, but only after trouble and extra chores. The final picture is a wiser child coming home in the evening, carrying both the lesson and the empty purse."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    service = f["service"]
    tags = {"financial", "service", "quest", "folk_tale", "money", "kindness"}
    if "mill" in service.tags:
        tags.add("mill")
    if "bell" in service.tags:
        tags.add("bell")
    if "water" in service.tags:
        tags.add("water")
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


ASP_RULES = r"""
enough_money(S, P) :- service(S), pack(P), price(S, Cost), capacity(P, Cap), Cap >= Cost.
mild_path(S, O)    :- service(S), obstacle(O), difficulty(S, D), need(O, N), N <= D + 1.
valid(S, P, O)     :- enough_money(S, P), mild_path(S, O).

shares(V, I) :- virtue(V), open_hand(V), pack_has(I).
help_tokens(C) :- C = #count { I : shares(_, I) }.
outcome(delivered) :- chosen_obstacle(O), need(O, N), help_tokens(C), C >= N.
outcome(late)      :- chosen_obstacle(O), need(O, N), help_tokens(C), C < N.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, service in SERVICES.items():
        lines.append(asp.fact("service", sid))
        lines.append(asp.fact("price", sid, service.price))
        lines.append(asp.fact("difficulty", sid, service.difficulty))
    for pid, pack in PACKS.items():
        lines.append(asp.fact("pack", pid))
        lines.append(asp.fact("capacity", pid, pack.capacity))
        for item in sorted(pack.items):
            lines.append(asp.fact("contains", pid, item))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("need", oid, obstacle.need))
    for virtue in ["open_hand", "tight_fist"]:
        lines.append(asp.fact("virtue", virtue))
    lines.append(asp.fact("open_hand", "open_hand"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario: list[str] = [asp.fact("chosen_obstacle", params.obstacle)]
    for item in sorted(PACKS[params.pack].items):
        scenario.append(asp.fact("pack_has", item))
    scenario.append(asp.fact("chosen_virtue", params.virtue))
    if params.virtue == "open_hand":
        scenario.append(asp.fact("open_hand", "open_hand"))
        scenario.append(asp.fact("virtue", "open_hand"))
    else:
        scenario.append(asp.fact("virtue", "tight_fist"))
    model = asp.one_model(
        asp_program(
            "\n".join(scenario),
            "#show outcome/1.",
        )
    )
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a folk-tale financial quest to pay for a village service."
    )
    ap.add_argument("--service", choices=SERVICES)
    ap.add_argument("--pack", choices=PACKS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--virtue", choices=["open_hand", "tight_fist"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.service and args.pack and not valid_combo(args.service, args.pack):
        raise StoryError(explain_rejection(args.service, args.pack, args.obstacle))
    if args.service and args.obstacle:
        if OBSTACLES[args.obstacle].need > SERVICES[args.service].difficulty + 1:
            pack_id = args.pack or next(iter(PACKS))
            raise StoryError(explain_rejection(args.service, pack_id, args.obstacle))

    combos = [
        c for c in valid_combos()
        if (args.service is None or c[0] == args.service)
        and (args.pack is None or c[1] == args.pack)
        and (args.obstacle is None or c[2] == args.obstacle)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    service_id, pack_id, obstacle_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    guardian = args.guardian or rng.choice(GUARDIANS)
    trait = rng.choice(TRAITS)
    virtue = args.virtue or rng.choice(["open_hand", "tight_fist"])
    return StoryParams(
        service=service_id,
        pack=pack_id,
        obstacle=obstacle_id,
        virtue=virtue,
        name=name,
        gender=gender,
        guardian=guardian,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.service not in SERVICES:
        raise StoryError(f"(Unknown service: {params.service})")
    if params.pack not in PACKS:
        raise StoryError(f"(Unknown pack: {params.pack})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.virtue not in {"open_hand", "tight_fist"}:
        raise StoryError(f"(Unknown virtue: {params.virtue})")
    if not valid_combo(params.service, params.pack):
        raise StoryError(explain_rejection(params.service, params.pack, params.obstacle))
    if OBSTACLES[params.obstacle].need > SERVICES[params.service].difficulty + 1:
        raise StoryError(explain_rejection(params.service, params.pack, params.obstacle))

    world = tell(
        service=SERVICES[params.service],
        pack=PACKS[params.pack],
        obstacle=OBSTACLES[params.obstacle],
        virtue=params.virtue,
        name=params.name,
        gender=params.gender,
        guardian_type=params.guardian,
        trait=params.trait,
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
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print("Unexpected StoryError during resolve_params smoke test.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (service, pack, obstacle) combos:\n")
        for service_id, pack_id, obstacle_id in combos:
            print(f"  {service_id:12} {pack_id:18} {obstacle_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.name}: {p.service}, {p.pack}, {p.obstacle}, {p.virtue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
