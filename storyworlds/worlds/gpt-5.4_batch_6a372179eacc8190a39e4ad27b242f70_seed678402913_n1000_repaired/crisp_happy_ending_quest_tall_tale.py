#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/crisp_happy_ending_quest_tall_tale.py
================================================================

A standalone storyworld for a tall-tale flavored quest with a happy ending.
A child sets out to fetch something wonderfully crisp from an enormous far-off
patch, crosses one outsized obstacle, and comes home changed by the trip.

The world model is small on purpose:
- one hero wants to help the town feast
- one obstacle blocks the road
- one piece of gear may solve it directly
- otherwise a helpful animal turns the story at the middle beat
- the prize is fetched and shared in a bright ending image

Run it
------
    python storyworlds/worlds/gpt-5.4/crisp_happy_ending_quest_tall_tale.py
    python storyworlds/worlds/gpt-5.4/crisp_happy_ending_quest_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/crisp_happy_ending_quest_tall_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/crisp_happy_ending_quest_tall_tale.py --qa
    python storyworlds/worlds/gpt-5.4/crisp_happy_ending_quest_tall_tale.py --verify
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    start: str = ""
    path: str = ""
    source: str = ""
    ending: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str = ""
    phrase: str = ""
    harvest: str = ""
    crunch: str = ""
    feast_use: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str = ""
    phrase: str = ""
    challenge: str = ""
    road_text: str = ""
    risk_text: str = ""
    need: str = ""
    severity: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str = ""
    phrase: str = ""
    need: str = ""
    power: int = 1
    use_text: str = ""
    direct_text: str = ""
    partial_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    label: str = ""
    phrase: str = ""
    specialty: str = ""
    power: int = 0
    intro_text: str = ""
    help_text: str = ""
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


def _r_helper_ready(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    helper = world.get("helper")
    if obstacle.meters["stuck"] < THRESHOLD:
        return []
    if helper.attrs.get("specialty") != obstacle.attrs.get("need"):
        return []
    sig = ("helper_ready", helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["alert"] += 1
    return []


def _r_crossed(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    hero = world.get("hero")
    if obstacle.meters["help_applied"] + obstacle.meters["gear_applied"] < obstacle.attrs.get("severity", 0):
        return []
    sig = ("crossed", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obstacle.meters["crossed"] = 1.0
    obstacle.meters["stuck"] = 0.0
    hero.memes["hope"] += 1
    hero.memes["grit"] += 1
    return []


def _r_prize_reached(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    prize = world.get("prize")
    if obstacle.meters["crossed"] < THRESHOLD:
        return []
    sig = ("prize_reached", prize.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    prize.meters["reachable"] = 1.0
    return []


CAUSAL_RULES = [
    Rule(name="helper_ready", tag="social", apply=_r_helper_ready),
    Rule(name="crossed", tag="physical", apply=_r_crossed),
    Rule(name="prize_reached", tag="physical", apply=_r_prize_reached),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                produced.extend(out)
                changed = True
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
        before = len(world.fired)
        for rule in CAUSAL_RULES:
            rule.apply(world)
        if len(world.fired) != before:
            changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "prairie": Place(
        id="prairie",
        start="the Pancake Prairie",
        path="a road so long it needed two sunrises painted on the mileposts",
        source="the Sky-High Orchard",
        ending="the supper tables beside the windmill",
        tags={"prairie", "orchard"},
    ),
    "ridge": Place(
        id="ridge",
        start="the Buttermilk Ridge",
        path="a trail that curled around hills taller than courthouse chimneys",
        source="the Moonlit Garden",
        ending="the porch of the town hall",
        tags={"ridge", "garden"},
    ),
    "hollow": Place(
        id="hollow",
        start="the Clover Hollow",
        path="a lane that ran between bean poles as tall as church steeples",
        source="the Far Pumpkin Patch",
        ending="the long picnic blanket by the creek",
        tags={"hollow", "patch"},
    ),
}

PRIZES = {
    "apple": Prize(
        id="apple",
        label="apple",
        phrase="a giant apple",
        harvest="picked the biggest apple in the whole patch",
        crunch="It looked so crisp that even the sunlight seemed to snap on its skin.",
        feast_use="slice it for the feast",
        tags={"apple", "fruit", "crisp"},
    ),
    "pear": Prize(
        id="pear",
        label="pear",
        phrase="a big green pear",
        harvest="twisted down a pear as round as a kettle",
        crunch="Its peel shone so crisp and cool that it seemed to ring when a breeze touched it.",
        feast_use="share pear wedges at the feast",
        tags={"pear", "fruit", "crisp"},
    ),
    "carrot": Prize(
        id="carrot",
        label="carrot",
        phrase="a tall orange carrot",
        harvest="pulled up a carrot that came out of the ground like a bright wooden oar",
        crunch="It was so crisp the little root hairs stood straight as brush bristles.",
        feast_use="chop it into the stew pot",
        tags={"carrot", "vegetable", "crisp"},
    ),
}

OBSTACLES = {
    "wind": Obstacle(
        id="wind",
        label="windy gap",
        phrase="a windy gap",
        challenge="gusts were blowing hard enough to wrinkle the road",
        road_text="right in the middle yawned a windy gap where the air itself seemed to shove sideways",
        risk_text="One bad step would send hat, lunch, and courage all tumbling together.",
        need="steady",
        severity=3,
        tags={"wind", "gap"},
    ),
    "mud": Obstacle(
        id="mud",
        label="mud bog",
        phrase="a mud bog",
        challenge="the ground was gulping at boots like a hungry pudding bowl",
        road_text="across the road sprawled a mud bog that tried to keep every footprint it met",
        risk_text="If the hero rushed in, the mud would pin both feet and swallow the day.",
        need="high",
        severity=2,
        tags={"mud", "bog"},
    ),
    "stream": Obstacle(
        id="stream",
        label="racing stream",
        phrase="a racing stream",
        challenge="the water hurried along as if it were late for the ocean",
        road_text="the path stopped at a racing stream bright with fast white splashes",
        risk_text="The current would tug a small traveler sideways before breakfast could even cool.",
        need="float",
        severity=3,
        tags={"stream", "water"},
    ),
}

GEAR = {
    "boots": Gear(
        id="boots",
        label="tall boots",
        phrase="a pair of tall boots",
        need="high",
        power=2,
        use_text="pulled on the tall boots and tested the ground with slow, brave steps",
        direct_text="The boots lifted each foot clear, and the bog never got a chance to bite.",
        partial_text="The boots helped, but the place still looked meaner than a thundercloud's grin.",
        tags={"boots", "mud"},
    ),
    "rope": Gear(
        id="rope",
        label="coiled rope",
        phrase="a coiled rope",
        need="steady",
        power=2,
        use_text="swung the rope toward a stout post and held tight with both hands",
        direct_text="The rope stayed straight as a ruler, and the crossing turned into three good hops.",
        partial_text="The rope caught, but the wind puffed it and the hero sideways too.",
        tags={"rope", "wind"},
    ),
    "raft": Gear(
        id="raft",
        label="little raft",
        phrase="a little raft",
        need="float",
        power=2,
        use_text="pushed the little raft into the water and climbed in as careful as setting down an egg",
        direct_text="The raft bobbed once, then scooted across as neat as a button on a sleeve.",
        partial_text="The raft stayed afloat, but the stream spun it in a shiny half-circle.",
        tags={"raft", "stream"},
    ),
    "ladder": Gear(
        id="ladder",
        label="long ladder",
        phrase="a long ladder",
        need="high",
        power=1,
        use_text="laid the ladder across the worst stretch and crept forward one rung at a time",
        direct_text="The ladder bridged the softest part, and the hero tiptoed over without a splash.",
        partial_text="The ladder reached partway, yet the far side still looked a boot-length too far.",
        tags={"ladder", "mud"},
    ),
    "kite_string": Gear(
        id="kite_string",
        label="kite string",
        phrase="a spool of kite string",
        need="steady",
        power=1,
        use_text="ran out the kite string and tied it where the gusts could not boss it around",
        direct_text="The line hummed steady, and the hero crossed with one hand on it and one hand on hope.",
        partial_text="The string sang in the wind, though the gap kept tossing it left and right.",
        tags={"kite", "wind"},
    ),
    "barrel": Gear(
        id="barrel",
        label="round barrel",
        phrase="a round barrel",
        need="float",
        power=1,
        use_text="rolled the barrel to the bank and used it like a bobbing boat",
        direct_text="The barrel floated true enough, and the stream gave way with a splashy grumble.",
        partial_text="The barrel floated, but it spun so fast it made the cattails dizzy.",
        tags={"barrel", "stream"},
    ),
}

HELPERS = {
    "mule": HelperCfg(
        id="mule",
        label="mule",
        phrase="a patient gray mule",
        specialty="steady",
        power=2,
        intro_text="A patient gray mule lifted its ears as if it had been listening to the whole road.",
        help_text="The mule planted its hooves like fence posts and leaned into the wind until the crossing went still enough to walk.",
        tags={"mule", "farm"},
    ),
    "stork": HelperCfg(
        id="stork",
        label="stork",
        phrase="a long-legged stork",
        specialty="high",
        power=2,
        intro_text="A long-legged stork came stepping over the reeds as if it owned every puddle in three counties.",
        help_text="The stork showed the hero the highest hummocks, and each careful step landed on dry, honest ground.",
        tags={"stork", "bird"},
    ),
    "beaver": HelperCfg(
        id="beaver",
        label="beaver",
        phrase="a broad-tailed beaver",
        specialty="float",
        power=2,
        intro_text="A broad-tailed beaver popped up with a twig in its teeth and a bright worker's look in its eyes.",
        help_text="The beaver nudged the raft straight and slapped the water until the current minded its manners.",
        tags={"beaver", "water"},
    ),
}

GIRL_NAMES = ["June", "Molly", "Ada", "Ruth", "Elsie", "Clara", "Willa", "Nell"]
BOY_NAMES = ["Jed", "Cal", "Eli", "Bo", "Silas", "Toby", "Nate", "Hank"]
TRAITS = ["brave", "cheerful", "steady", "quick", "kind", "plucky"]


def compatible(place_id: str, prize_id: str, obstacle_id: str, gear_id: str, helper_id: str) -> bool:
    if place_id not in PLACES or prize_id not in PRIZES or obstacle_id not in OBSTACLES:
        return False
    if gear_id not in GEAR or helper_id not in HELPERS:
        return False
    obstacle = OBSTACLES[obstacle_id]
    gear = GEAR[gear_id]
    helper = HELPERS[helper_id]
    if gear.need != obstacle.need:
        return False
    if helper.specialty != obstacle.need:
        return False
    return gear.power + helper.power >= obstacle.severity


def outcome_of(params: "StoryParams") -> str:
    obstacle = OBSTACLES[params.obstacle]
    gear = GEAR[params.gear]
    return "direct" if gear.power >= obstacle.severity else "assisted"


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id in sorted(PLACES):
        for prize_id in sorted(PRIZES):
            for obstacle_id in sorted(OBSTACLES):
                for gear_id in sorted(GEAR):
                    for helper_id in sorted(HELPERS):
                        if compatible(place_id, prize_id, obstacle_id, gear_id, helper_id):
                            combos.append((place_id, prize_id, obstacle_id, gear_id, helper_id))
    return combos


@dataclass
class StoryParams:
    place: str
    prize: str
    obstacle: str
    gear: str
    helper: str
    hero_name: str
    hero_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def predict_crossing(obstacle: Obstacle, gear: Gear, helper: HelperCfg) -> dict[str, object]:
    direct = gear.power >= obstacle.severity
    return {
        "direct": direct,
        "assisted": not direct and gear.power + helper.power >= obstacle.severity,
        "need": obstacle.need,
    }


def introduce(world: World, place: Place, hero: Entity, parent: Entity, prize: Prize) -> None:
    hero.memes["duty"] += 1
    world.say(
        f"In {place.start}, where cabbages were said to cast square shadows at noon, lived {hero.id}, "
        f"a {hero.traits[0]} little {hero.type} with legs made for errands and a heart made for quests."
    )
    world.say(
        f"That morning {hero.id}'s {parent.label_word} looked at the feast tables and sighed. "
        f'The town still needed {prize.phrase} from {place.source}, something fine enough to {prize.feast_use}.'
    )
    world.say(
        f'"I can fetch it," said {hero.id}, standing so straight that even the porch boards seemed to salute.'
    )


def set_out(world: World, place: Place, hero: Entity, prize: Prize) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"So off {hero.pronoun()} went along {place.path}, heading for {place.source} where the best {prize.label}s grew bigger than wash tubs."
    )


def meet_obstacle(world: World, obstacle: Obstacle, hero: Entity) -> None:
    obstacle_ent = world.get("obstacle")
    obstacle_ent.meters["blocked"] = 1.0
    hero.memes["doubt"] += 1
    world.say(
        f"By and by, {hero.id} reached {obstacle.phrase}. {obstacle.road_text}. {obstacle.challenge} {obstacle.risk_text}"
    )


def try_gear(world: World, obstacle: Obstacle, gear: Gear, hero: Entity) -> None:
    obstacle_ent = world.get("obstacle")
    obstacle_ent.meters["gear_applied"] += float(gear.power)
    hero.memes["grit"] += 1
    world.say(
        f"{hero.id} was not the sort to turn around while breakfast still needed saving, so {hero.pronoun()} {gear.use_text}."
    )
    propagate(world, narrate=False)
    if obstacle_ent.meters["crossed"] >= THRESHOLD:
        world.say(gear.direct_text)
    else:
        obstacle_ent.meters["stuck"] = 1.0
        world.say(gear.partial_text)


def helper_turn(world: World, helper: HelperCfg, hero: Entity) -> None:
    obstacle_ent = world.get("obstacle")
    helper_ent = world.get("helper")
    world.say(helper.intro_text)
    helper_ent.memes["care"] += 1
    obstacle_ent.meters["help_applied"] += float(helper.power)
    propagate(world, narrate=False)
    world.say(helper.help_text)
    hero.memes["trust"] += 1
    hero.memes["relief"] += 1


def harvest(world: World, place: Place, prize: Prize, hero: Entity) -> None:
    prize_ent = world.get("prize")
    if prize_ent.meters["reachable"] < THRESHOLD:
        raise StoryError("The prize was not reachable; the quest did not make sense.")
    prize_ent.meters["carried"] = 1.0
    hero.memes["joy"] += 1
    world.say(
        f"On the far side waited {place.source}, and there {hero.id} {prize.harvest}. {prize.crunch}"
    )


def homecome(world: World, place: Place, prize: Prize, hero: Entity, parent: Entity, helper: HelperCfg) -> None:
    hero.memes["belonging"] += 1
    world.say(
        f"{hero.id} came home by sundown to {place.ending}, carrying the {prize.label} in both arms while the whole town made room and grinned."
    )
    world.say(
        f"{parent.label_word.capitalize()} cut the first piece, and the crunch was so crisp it sounded like a tiny parade of boots on frosty grass."
    )
    world.say(
        f"They shared the feast with everybody, and {hero.id} saved the very next bite for {helper.phrase}. "
        f"After that, whenever a job looked too big, folks in town said it was only just the right size for {hero.id}."
    )


def tell(
    place: Place,
    prize: Prize,
    obstacle: Obstacle,
    gear: Gear,
    helper: HelperCfg,
    hero_name: str,
    hero_gender: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, phrase=hero_name, role="hero", traits=[trait]))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    obstacle_ent = world.add(Entity(
        id="obstacle",
        kind="thing",
        type="obstacle",
        label=obstacle.label,
        phrase=obstacle.phrase,
        role="obstacle",
        attrs={"need": obstacle.need, "severity": obstacle.severity},
        tags=set(obstacle.tags),
    ))
    helper_ent = world.add(Entity(
        id="helper",
        kind="character",
        type="animal",
        label=helper.label,
        phrase=helper.phrase,
        role="helper",
        attrs={"specialty": helper.specialty},
        tags=set(helper.tags),
    ))
    prize_ent = world.add(Entity(
        id="prize",
        kind="thing",
        type="prize",
        label=prize.label,
        phrase=prize.phrase,
        role="prize",
        tags=set(prize.tags),
    ))
    gear_ent = world.add(Entity(
        id="gear",
        kind="thing",
        type="gear",
        label=gear.label,
        phrase=gear.phrase,
        role="gear",
        attrs={"need": gear.need, "power": gear.power},
        tags=set(gear.tags),
    ))

    introduce(world, place, hero, parent, prize)
    set_out(world, place, hero, prize)

    world.para()
    meet_obstacle(world, obstacle, hero)
    try_gear(world, obstacle, gear, hero)

    if world.get("obstacle").meters["crossed"] < THRESHOLD:
        world.para()
        helper_turn(world, helper, hero)
        if world.get("obstacle").meters["crossed"] < THRESHOLD:
            raise StoryError("The helper turn failed to solve the obstacle.")
    else:
        hero.memes["confidence"] += 1

    world.para()
    harvest(world, place, prize, hero)
    homecome(world, place, prize, hero, parent, helper)

    world.facts.update(
        place=place,
        prize_cfg=prize,
        obstacle_cfg=obstacle,
        gear_cfg=gear,
        helper_cfg=helper,
        hero=hero,
        parent=parent,
        direct=(gear.power >= obstacle.severity),
        outcome="direct" if gear.power >= obstacle.severity else "assisted",
        crossing_done=(world.get("obstacle").meters["crossed"] >= THRESHOLD),
        prize_got=(world.get("prize").meters["carried"] >= THRESHOLD),
    )
    return world


KNOWLEDGE = {
    "apple": [(
        "What does crisp mean when food is crisp?",
        "When food is crisp, it feels fresh and firm and makes a little crunch when you bite it. That crunchy sound is one way you can tell it is fresh."
    )],
    "pear": [(
        "How can you tell a pear is fresh?",
        "A fresh pear usually feels firm instead of mushy and smells sweet. If it is crisp when you bite it, that is another good sign."
    )],
    "carrot": [(
        "Why do carrots crunch?",
        "Carrots crunch because they are full of water and have firm cells packed tightly together. When you bite them, those tiny firm parts break with a snapping sound."
    )],
    "wind": [(
        "Why can strong wind make walking hard?",
        "Strong wind pushes against your body and can throw off your balance. That is why people hold on tight or take slower steps on windy days."
    )],
    "mud": [(
        "Why does mud grab your boots?",
        "Mud is wet dirt, and it can be soft and sticky. When your boots sink in, the mud holds on and makes each step harder."
    )],
    "stream": [(
        "Why is a fast stream hard to cross?",
        "A fast stream keeps moving against your feet or boat the whole time. That moving water can push you off balance if you are not careful."
    )],
    "rope": [(
        "What can a rope help with on a trip?",
        "A rope can give you something steady to hold. It can also help you pull, tie, or balance when the ground is tricky."
    )],
    "boots": [(
        "Why are tall boots useful in mud?",
        "Tall boots keep mud off your feet and ankles and help you step into wet places more safely. They work best when you move slowly and plant each foot firmly."
    )],
    "raft": [(
        "What does a raft do?",
        "A raft floats on water and carries people or things across. It spreads weight over the water so you do not have to wade through the current."
    )],
    "helper": [(
        "Why is a helper good on a quest?",
        "A helper can bring a skill you do not have by yourself. Working together often solves a problem faster and more safely than struggling alone."
    )],
}
KNOWLEDGE_ORDER = ["apple", "pear", "carrot", "wind", "mud", "stream", "rope", "boots", "raft", "helper"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    prize = f["prize_cfg"]
    obstacle = f["obstacle_cfg"]
    if f["outcome"] == "direct":
        return [
            f'Write a tall-tale quest for preschoolers that includes the word "crisp" and ends happily.',
            f"Tell a big, cheerful story where a little {hero.type} crosses {obstacle.phrase} on the way to fetch {prize.phrase} from {place.source}.",
            f"Write a quest story with a huge obstacle, a brave child, and a crunchy feast ending.",
        ]
    return [
        f'Write a tall-tale quest for preschoolers that includes the word "crisp" and ends happily.',
        f"Tell a big, cheerful story where a little {hero.type} starts to cross {obstacle.phrase}, needs help from an animal friend, and still brings home {prize.phrase}.",
        f"Write a quest story with a middle rescue turn, a helpful animal, and a happy feast at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    place = f["place"]
    prize = f["prize_cfg"]
    obstacle = f["obstacle_cfg"]
    gear = f["gear_cfg"]
    helper = f["helper_cfg"]
    name = hero.label
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, a little {hero.type} who set out on a quest to bring back {prize.phrase} for the town feast. {parent.label_word.capitalize()} and the whole town were waiting for that trip to succeed."
        ),
        (
            f"Why did {name} leave home?",
            f"{name} wanted to help the town feast by fetching {prize.phrase} from {place.source}. The trip mattered because everyone was hoping to share it at supper."
        ),
        (
            f"What problem stood in {name}'s way?",
            f"{obstacle.phrase.capitalize()} blocked the road. It was dangerous because {obstacle.challenge.lower()} and {obstacle.risk_text.lower()}"
        ),
        (
            f"What did {name} use to face the obstacle?",
            f"{name} used {gear.phrase}. That made sense because it gave the right kind of help for {obstacle.label} instead of just hoping the trouble would go away."
        ),
    ]
    if f["outcome"] == "direct":
        qa.append((
            f"Did {name} solve the problem alone?",
            f"Yes. {name}'s gear was strong enough to handle the obstacle directly, so the crossing worked without needing rescue. That shows how good planning can make a hard road manageable."
        ))
    else:
        qa.append((
            f"How did the middle of the story turn from trouble to success?",
            f"At first the gear helped but did not fully beat the obstacle, so {name} was stuck. Then {helper.phrase} arrived and used its special skill, which turned the crossing from scary to possible."
        ))
    qa.append((
        f"What was the prize like when {name} found it?",
        f"The {prize.label} was wonderfully crisp and fresh. The story proves that by describing a sharp, crunchy sound when it was finally cut at the feast."
    ))
    qa.append((
        "How did the story end?",
        f"It ended happily with the town sharing the food together and {name} being proud of finishing the quest. The last image shows the prize on the table and even the helper getting a bite."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set()
    tags |= set(f["prize_cfg"].tags)
    tags |= set(f["obstacle_cfg"].tags)
    tags |= set(f["gear_cfg"].tags)
    tags.add("helper")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits: list[str] = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="prairie",
        prize="apple",
        obstacle="mud",
        gear="boots",
        helper="stork",
        hero_name="June",
        hero_gender="girl",
        parent="mother",
        trait="plucky",
    ),
    StoryParams(
        place="ridge",
        prize="pear",
        obstacle="wind",
        gear="rope",
        helper="mule",
        hero_name="Cal",
        hero_gender="boy",
        parent="father",
        trait="steady",
    ),
    StoryParams(
        place="hollow",
        prize="carrot",
        obstacle="stream",
        gear="raft",
        helper="beaver",
        hero_name="Ada",
        hero_gender="girl",
        parent="mother",
        trait="cheerful",
    ),
    StoryParams(
        place="prairie",
        prize="apple",
        obstacle="wind",
        gear="kite_string",
        helper="mule",
        hero_name="Eli",
        hero_gender="boy",
        parent="father",
        trait="brave",
    ),
    StoryParams(
        place="ridge",
        prize="pear",
        obstacle="stream",
        gear="barrel",
        helper="beaver",
        hero_name="Clara",
        hero_gender="girl",
        parent="mother",
        trait="kind",
    ),
]


def explain_rejection(place_id: str, prize_id: str, obstacle_id: str, gear_id: str, helper_id: str) -> str:
    parts: list[str] = []
    if obstacle_id in OBSTACLES and gear_id in GEAR:
        obstacle = OBSTACLES[obstacle_id]
        gear = GEAR[gear_id]
        if gear.need != obstacle.need:
            parts.append(f"{gear.label} does not match {obstacle.phrase}")
    if obstacle_id in OBSTACLES and helper_id in HELPERS:
        obstacle = OBSTACLES[obstacle_id]
        helper = HELPERS[helper_id]
        if helper.specialty != obstacle.need:
            parts.append(f"{helper.label} is the wrong kind of helper for {obstacle.phrase}")
    if obstacle_id in OBSTACLES and gear_id in GEAR and helper_id in HELPERS:
        obstacle = OBSTACLES[obstacle_id]
        gear = GEAR[gear_id]
        helper = HELPERS[helper_id]
        if gear.need == obstacle.need and helper.specialty == obstacle.need and gear.power + helper.power < obstacle.severity:
            parts.append("even together, the gear and helper are too weak for that obstacle")
    if not parts:
        parts.append("those options do not make a reasonable quest")
    return "(No story: " + "; ".join(parts) + ".)"


ASP_RULES = r"""
matches_need(G, O) :- gear(G), obstacle(O), gear_need(G, N), obstacle_need(O, N).
matches_helper(H, O) :- helper(H), obstacle(O), helper_skill(H, N), obstacle_need(O, N).
strong_enough(G, H, O) :- gear_power(G, GP), helper_power(H, HP), obstacle_severity(O, S), GP + HP >= S.
compatible(P, R, O, G, H) :- place(P), prize(R), obstacle(O), gear(G), helper(H),
                             matches_need(G, O), matches_helper(H, O), strong_enough(G, H, O).

direct(G, O) :- gear_power(G, GP), obstacle_severity(O, S), GP >= S.
assisted(G, H, O) :- compatible(_, _, O, G, H), not direct(G, O).

outcome(direct) :- chosen_obstacle(O), chosen_gear(G), direct(G, O).
outcome(assisted) :- chosen_place(_), chosen_prize(_), chosen_obstacle(O), chosen_gear(G), chosen_helper(H),
                     compatible(_, _, O, G, H), not direct(G, O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in sorted(PLACES):
        lines.append(asp.fact("place", pid))
    for rid in sorted(PRIZES):
        lines.append(asp.fact("prize", rid))
    for oid, obstacle in sorted(OBSTACLES.items()):
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("obstacle_need", oid, obstacle.need))
        lines.append(asp.fact("obstacle_severity", oid, obstacle.severity))
    for gid, gear in sorted(GEAR.items()):
        lines.append(asp.fact("gear", gid))
        lines.append(asp.fact("gear_need", gid, gear.need))
        lines.append(asp.fact("gear_power", gid, gear.power))
    for hid, helper in sorted(HELPERS.items()):
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_skill", hid, helper.specialty))
        lines.append(asp.fact("helper_power", hid, helper.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show compatible/5."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_prize", params.prize),
        asp.fact("chosen_obstacle", params.obstacle),
        asp.fact("chosen_gear", params.gear),
        asp.fact("chosen_helper", params.helper),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale quest storyworld: a child crosses a huge obstacle to fetch something crisp for a happy feast."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--obstacle", choices=sorted(OBSTACLES))
    ap.add_argument("--gear", choices=sorted(GEAR))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    chosen_place = args.place
    chosen_prize = args.prize
    chosen_obstacle = args.obstacle
    chosen_gear = args.gear
    chosen_helper = args.helper

    if all(x is not None for x in [chosen_place, chosen_prize, chosen_obstacle, chosen_gear, chosen_helper]):
        if not compatible(chosen_place, chosen_prize, chosen_obstacle, chosen_gear, chosen_helper):
            raise StoryError(explain_rejection(chosen_place, chosen_prize, chosen_obstacle, chosen_gear, chosen_helper))

    combos = [
        combo for combo in valid_combos()
        if (chosen_place is None or combo[0] == chosen_place)
        and (chosen_prize is None or combo[1] == chosen_prize)
        and (chosen_obstacle is None or combo[2] == chosen_obstacle)
        and (chosen_gear is None or combo[3] == chosen_gear)
        and (chosen_helper is None or combo[4] == chosen_helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, prize_id, obstacle_id, gear_id, helper_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    if args.hero_name:
        hero_name = args.hero_name
    else:
        hero_name = rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        prize=prize_id,
        obstacle=obstacle_id,
        gear=gear_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if not compatible(params.place, params.prize, params.obstacle, params.gear, params.helper):
        raise StoryError(explain_rejection(params.place, params.prize, params.obstacle, params.gear, params.helper))
    try:
        place = PLACES[params.place]
        prize = PRIZES[params.prize]
        obstacle = OBSTACLES[params.obstacle]
        gear = GEAR[params.gear]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"Unknown parameter value: {err}") from err
    world = tell(
        place=place,
        prize=prize,
        obstacle=obstacle,
        gear=gear,
        helper=helper,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        parent_type=params.parent,
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
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP gate matches Python valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if asp_set - py:
            print("  only in ASP:", sorted(asp_set - py))
        if py - asp_set:
            print("  only in Python:", sorted(py - asp_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

    mismatch = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: ASP outcome matches Python outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0] if cases else CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show compatible/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, prize, obstacle, gear, helper) combos:\n")
        for combo in combos:
            print("  " + "  ".join(combo))
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
            header = f"### {p.hero_name}: {p.prize} quest at {p.place} ({p.obstacle}, {p.gear}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
