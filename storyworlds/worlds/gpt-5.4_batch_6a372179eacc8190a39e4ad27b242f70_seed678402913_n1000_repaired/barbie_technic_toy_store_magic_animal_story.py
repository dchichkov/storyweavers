#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/barbie_technic_toy_store_magic_animal_story.py
=========================================================================

A standalone storyworld about two small animals in a toy store after closing.
A little animal is stranded in a high display, magic stirs the toys awake, and
the friends must choose a toy helper that can truly reach the perch safely.

The seed asked for:
- the words "barbie" and "technic"
- a toy store setting
- a magical feature
- an Animal Story style

This world always includes both the barbie aisle and the technic aisle in the
same toy store, but the central rescue depends on the world state: height,
surface, helper power, and whether the chosen plan is sensible.

Run it
------
    python storyworlds/worlds/gpt-5.4/barbie_technic_toy_store_magic_animal_story.py
    python storyworlds/worlds/gpt-5.4/barbie_technic_toy_store_magic_animal_story.py --perch top_shelf
    python storyworlds/worlds/gpt-5.4/barbie_technic_toy_store_magic_animal_story.py --helper barbie_car
    python storyworlds/worlds/gpt-5.4/barbie_technic_toy_store_magic_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/barbie_technic_toy_store_magic_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/barbie_technic_toy_store_magic_animal_story.py --verify
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


@dataclass
class AnimalKind:
    id: str
    label: str
    home: str
    sound: str
    trait: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Perch:
    id: str
    label: str
    phrase: str
    height: int
    shaky: bool
    night_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    series: str
    reach: int
    stable_on_shaky: bool
    comfort: int
    sense: int
    success_text: str
    fail_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Spark:
    id: str
    label: str
    phrase: str
    glow: str
    promise: str
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


def _r_stranded_fear(world: World) -> list[str]:
    rescued = world.get("stranded")
    if rescued.meters["stranded"] < THRESHOLD:
        return []
    sig = ("fear", rescued.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    rescued.memes["fear"] += 1
    world.get("hero").memes["care"] += 1
    world.get("friend").memes["care"] += 1
    return []


def _r_rescue_relief(world: World) -> list[str]:
    rescued = world.get("stranded")
    if rescued.meters["safe"] < THRESHOLD:
        return []
    sig = ("relief", rescued.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    rescued.memes["relief"] += 1
    world.get("hero").memes["joy"] += 1
    world.get("friend").memes["joy"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="stranded_fear", tag="emotional", apply=_r_stranded_fear),
    Rule(name="rescue_relief", tag="emotional", apply=_r_rescue_relief),
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
            world.say(sent)
    return produced


def can_reach(helper: Helper, perch: Perch) -> bool:
    return helper.reach >= perch.height


def stable_enough(helper: Helper, perch: Perch) -> bool:
    return (not perch.shaky) or helper.stable_on_shaky


def sensible_helper(helper: Helper) -> bool:
    return helper.sense >= SENSE_MIN


def rescue_works(helper: Helper, perch: Perch) -> bool:
    return can_reach(helper, perch) and stable_enough(helper, perch)


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for perch_id, perch in PERCHES.items():
        for helper_id, helper in HELPERS.items():
            if sensible_helper(helper) and rescue_works(helper, perch):
                combos.append((perch_id, helper_id))
    return combos


@dataclass
class StoryParams:
    perch: str
    helper: str
    hero_name: str
    hero_kind: str
    friend_name: str
    friend_kind: str
    stranded_name: str
    stranded_kind: str
    spark: str
    seed: Optional[int] = None


ANIMALS = {
    "mouse": AnimalKind(
        id="mouse",
        label="mouse",
        home="behind the puzzle shelf",
        sound="squeaked",
        trait="quick",
        tags={"mouse", "animal"},
    ),
    "bunny": AnimalKind(
        id="bunny",
        label="bunny",
        home="inside the plush basket",
        sound="whispered",
        trait="gentle",
        tags={"bunny", "animal"},
    ),
    "fox": AnimalKind(
        id="fox",
        label="fox",
        home="under the train table",
        sound="murmured",
        trait="bright",
        tags={"fox", "animal"},
    ),
    "squirrel": AnimalKind(
        id="squirrel",
        label="squirrel",
        home="near the craft beads",
        sound="chattered",
        trait="busy",
        tags={"squirrel", "animal"},
    ),
    "hedgehog": AnimalKind(
        id="hedgehog",
        label="hedgehog",
        home="beside the storybooks",
        sound="said softly",
        trait="careful",
        tags={"hedgehog", "animal"},
    ),
}

PERCHES = {
    "top_shelf": Perch(
        id="top_shelf",
        label="top shelf",
        phrase="the top shelf above the dolls",
        height=3,
        shaky=False,
        night_image="silver moonlight lay across the high boxes",
        tags={"shelf", "high"},
    ),
    "ribbon_tower": Perch(
        id="ribbon_tower",
        label="ribbon tower",
        phrase="a tall tower of ribbon boxes beside the barbie aisle",
        height=2,
        shaky=True,
        night_image="pink ribbons trembled whenever the air hummed",
        tags={"ribbon", "shaky"},
    ),
    "star_window": Perch(
        id="star_window",
        label="star window",
        phrase="the little star-shaped window in the castle display",
        height=2,
        shaky=False,
        night_image="the tiny window shone with blue magic dust",
        tags={"window", "castle"},
    ),
}

HELPERS = {
    "technic_crane": Helper(
        id="technic_crane",
        label="technic crane",
        phrase="a yellow technic crane with a careful hook",
        series="technic",
        reach=3,
        stable_on_shaky=True,
        comfort=1,
        sense=3,
        success_text="rolled the technic crane close, raised the careful hook, and made a snug little seat from soft string",
        fail_text="rolled the technic crane over, but even its tall arm could not hold steady there",
        qa_text="They used the technic crane to lift the stranded friend down safely",
        tags={"technic", "crane", "machine"},
    ),
    "technic_bridge": Helper(
        id="technic_bridge",
        label="technic bridge",
        phrase="a buildable technic bridge with clicking gray beams",
        series="technic",
        reach=2,
        stable_on_shaky=True,
        comfort=1,
        sense=3,
        success_text="snapped the technic bridge into place so the little one could walk down step by step",
        fail_text="built the technic bridge as fast as they could, but it still stopped too low",
        qa_text="They built a technic bridge that gave the stranded friend a safe way down",
        tags={"technic", "bridge", "machine"},
    ),
    "barbie_car": Helper(
        id="barbie_car",
        label="barbie car",
        phrase="a shiny barbie car with pearly wheels",
        series="barbie",
        reach=1,
        stable_on_shaky=False,
        comfort=3,
        sense=1,
        success_text="drove the barbie car close and somehow turned it into the perfect ride home",
        fail_text="drove the barbie car beneath the perch, but a car on the floor could not reach high enough",
        qa_text="They tried the barbie car, but it could not reach the high place",
        tags={"barbie", "car", "doll"},
    ),
    "barbie_balloon": Helper(
        id="barbie_balloon",
        label="barbie balloon",
        phrase="a barbie balloon basket tied with satin string",
        series="barbie",
        reach=2,
        stable_on_shaky=False,
        comfort=3,
        sense=2,
        success_text="guided the barbie balloon basket upward until it floated beside the perch",
        fail_text="sent the barbie balloon basket up, but it bobbed and swayed too much to be safe",
        qa_text="They used the barbie balloon basket to float beside the stranded friend",
        tags={"barbie", "balloon", "doll"},
    ),
}

SPARKS = {
    "moonbell": Spark(
        id="moonbell",
        label="moonbell",
        phrase="a moonbell spark tucked in a glass jar",
        glow="made the toy store glow like a sleepy star",
        promise="One kind plan tonight will wake one toy to help.",
        tags={"magic", "moon"},
    ),
    "stardust": Spark(
        id="stardust",
        label="stardust",
        phrase="a pinch of stardust hidden in a music box",
        glow="spilled a soft trail of silver over the aisles",
        promise="One brave wish tonight will make a good tool listen.",
        tags={"magic", "star"},
    ),
}

GIRL_NAMES = ["Pip", "Mimi", "Lulu", "Tess", "Nia", "Daisy"]
BOY_NAMES = ["Nico", "Ollie", "Benji", "Toby", "Finn", "Milo"]


def outcome_of(params: StoryParams) -> str:
    helper = HELPERS[params.helper]
    perch = PERCHES[params.perch]
    return "rescued" if rescue_works(helper, perch) else "stuck"


def explain_helper(helper: Helper) -> str:
    good = ", ".join(sorted(hid for hid, h in HELPERS.items() if sensible_helper(h)))
    return (
        f"(Refusing helper '{helper.id}': it scores too low on common sense "
        f"(sense={helper.sense} < {SENSE_MIN}). A floor car cannot honestly be the best rescue plan here. "
        f"Try one of: {good}.)"
    )


def explain_combo(perch: Perch, helper: Helper) -> str:
    if not sensible_helper(helper):
        return explain_helper(helper)
    if not can_reach(helper, perch):
        return (
            f"(No story: {helper.label} cannot reach {perch.phrase}. "
            f"Pick a taller helper or a lower perch.)"
        )
    if not stable_enough(helper, perch):
        return (
            f"(No story: {perch.phrase} is too shaky for {helper.label}. "
            f"The rescue must be steady, not merely pretty.)"
        )
    return "(No story: this rescue plan does not work.)"


def _pick_name(rng: random.Random, avoid: set[str]) -> str:
    pool = [name for name in GIRL_NAMES + BOY_NAMES if name not in avoid]
    return rng.choice(pool)


def _pick_animal(rng: random.Random, avoid: set[str]) -> str:
    pool = [aid for aid in ANIMALS if aid not in avoid]
    return rng.choice(sorted(pool))


def wake_magic(world: World, spark: Spark) -> None:
    world.say(
        f"After the toy store went dark and quiet, {spark.phrase} {spark.glow}. "
        f"A whisper of magic slipped between the barbie boxes and the technic sets."
    )
    world.say(f'On the glass jar, tiny silver letters seemed to say, "{spark.promise}"')


def introduce_animals(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} the {hero.type} lived {hero.attrs['home']}, and {friend.id} the {friend.type} lived {friend.attrs['home']}. "
        f"Every night they padded through the toy store together, careful not to wake the sleeping dolls too soon."
    )
    world.say(
        f"{hero.id} was {hero.attrs['trait']}, and {friend.id} was {friend.attrs['trait']}. "
        f"They liked the pink shine of the barbie aisle and the tidy click of the technic builders' corner."
    )


def discover_trouble(world: World, hero: Entity, friend: Entity, stranded: Entity, perch: Perch) -> None:
    stranded.meters["stranded"] += 1
    propagate(world, narrate=False)
    world.say(
        f"That night they heard a small cry above them. {stranded.id} the {stranded.type} was stuck on {perch.phrase}, "
        f"and {perch.night_image}."
    )
    world.say(
        f'"Please help me down," {stranded.id} {stranded.attrs["sound"]}. '
        f'{hero.id} looked up so hard {hero.pronoun("possessive")} whiskers trembled.'
    )


def plan_talk(world: World, hero: Entity, friend: Entity, helper: Helper, perch: Perch) -> None:
    world.say(
        f'{friend.id} stared from the barbie aisle to the technic shelves and back again. '
        f'"We need something kind, but also something that can truly reach," {friend.pronoun()} said.'
    )
    world.say(
        f"They chose {helper.phrase}. Even with magic in the air, the toy store still followed careful rules."
    )
    world.facts["predicted_reach"] = can_reach(helper, perch)
    world.facts["predicted_stable"] = stable_enough(helper, perch)


def do_rescue(world: World, hero: Entity, friend: Entity, stranded: Entity, helper: Helper, perch: Perch) -> None:
    stranded.meters["safe"] += 1
    stranded.meters["stranded"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"The moonlit magic answered their brave choice. The {helper.label} shimmered awake, and they {helper.success_text}."
    )
    if helper.series == "barbie":
        world.say(
            f"{stranded.id} stepped into the soft little basket, and the barbie ribbon bows fluttered like friendly birds."
        )
    else:
        world.say(
            f"The technic pieces clicked so neatly that even the highest part of the toy store felt steady and safe."
        )
    world.say(
        f"In another moment, {stranded.id} was back on the floor, pressed close between {hero.id} and {friend.id}, no longer afraid."
    )


def fail_rescue(world: World, hero: Entity, friend: Entity, stranded: Entity, helper: Helper, perch: Perch) -> None:
    world.say(
        f"The moonlit magic tried to help. They {helper.fail_text}."
    )
    if not can_reach(helper, perch):
        world.say(
            f"{stranded.id} was still too high above them, and the little one's ears drooped. "
            f"Pretty wheels and shiny paint were not the same as a real rescue."
        )
    else:
        world.say(
            f"The perch wobbled at once, so {hero.id} and {friend.id} backed away. "
            f"They would rather wait than make their friend more frightened."
        )


def comfort_and_change(world: World, hero: Entity, friend: Entity, stranded: Entity, helper: Helper) -> None:
    hero.memes["wisdom"] += 1
    friend.memes["wisdom"] += 1
    stranded.memes["trust"] += 1
    world.say(
        f'"Magic is sweetest when it listens to good sense," {friend.id} {friend.attrs["sound"]}. '
        f'{hero.id} nodded, because now the whole toy store felt wiser than before.'
    )
    if helper.series == "technic":
        world.say(
            f"Before dawn, they tucked a pink ribbon from the barbie aisle around the rescued little one like a tiny scarf. "
            f"The strong technic rescue and the gentle barbie kindness belonged in the same happy night."
        )
    else:
        world.say(
            f"Before dawn, they parked the little barbie basket beside the neat technic boxes and thanked both aisles for shining in their own way."
        )


def final_image(world: World, hero: Entity, friend: Entity, stranded: Entity, spark: Spark) -> None:
    world.say(
        f"When the first morning light touched the toy store window, {hero.id}, {friend.id}, and {stranded.id} were curled together beneath the shelves. "
        f"Above them, the last glimmer of {spark.label} faded like a yawn."
    )


def tell(
    perch: Perch,
    helper: Helper,
    hero_name: str,
    hero_kind: AnimalKind,
    friend_name: str,
    friend_kind: AnimalKind,
    stranded_name: str,
    stranded_kind: AnimalKind,
    spark: Spark,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_kind.label,
        role="hero",
        attrs={"home": hero_kind.home, "sound": hero_kind.sound, "trait": hero_kind.trait},
        tags=set(hero_kind.tags),
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_kind.label,
        role="friend",
        attrs={"home": friend_kind.home, "sound": friend_kind.sound, "trait": friend_kind.trait},
        tags=set(friend_kind.tags),
    ))
    stranded = world.add(Entity(
        id=stranded_name,
        kind="character",
        type=stranded_kind.label,
        role="stranded",
        attrs={"home": stranded_kind.home, "sound": stranded_kind.sound, "trait": stranded_kind.trait},
        tags=set(stranded_kind.tags),
    ))
    world.add(Entity(id="toy_store", type="place", label="toy store", role="place"))

    wake_magic(world, spark)
    introduce_animals(world, hero, friend)

    world.para()
    discover_trouble(world, hero, friend, stranded, perch)
    plan_talk(world, hero, friend, helper, perch)

    world.para()
    success = rescue_works(helper, perch)
    if success:
        do_rescue(world, hero, friend, stranded, helper, perch)
        world.para()
        comfort_and_change(world, hero, friend, stranded, helper)
    else:
        fail_rescue(world, hero, friend, stranded, helper, perch)
        world.para()
        world.say(
            f"So they sat below {perch.phrase} and sang soft nighttime songs until help would come with the morning keys. "
            f"{stranded.id} was still stuck, but not alone."
        )
        world.say(
            "Even in a magical toy store, kind hearts learned that wishing was not enough without the right plan."
        )
    final_image(world, hero, friend, stranded, spark)

    world.facts.update(
        hero=hero,
        friend=friend,
        stranded=stranded,
        perch=perch,
        helper=helper,
        spark=spark,
        outcome="rescued" if success else "stuck",
        rescued=success,
        predicted_reach=can_reach(helper, perch),
        predicted_stable=stable_enough(helper, perch),
    )
    return world


KNOWLEDGE = {
    "magic": [
        (
            "What is magic in a story?",
            "Magic in a story is something wonderful that cannot happen in ordinary life, like a toy waking up or a spark that listens. It helps make the problem feel bright and special."
        )
    ],
    "toy_store": [
        (
            "What is a toy store?",
            "A toy store is a shop where people buy toys, games, dolls, and building sets. It is full of shelves, boxes, and colorful displays."
        )
    ],
    "barbie": [
        (
            "What is barbie in this story world?",
            "Barbie is one part of the toy store with dolls, bright accessories, and pretty vehicles. It adds softness and sparkle to the story."
        )
    ],
    "technic": [
        (
            "What is technic in this story world?",
            "Technic is the building-set part of the toy store with beams, wheels, and sturdy machines. It is useful when the story needs a strong tool."
        )
    ],
    "crane": [
        (
            "What does a crane do?",
            "A crane lifts things up or lowers them down with a tall arm. That makes it helpful when someone is stuck in a high place."
        )
    ],
    "bridge": [
        (
            "What does a bridge do?",
            "A bridge makes a safe path from one place to another. It helps someone cross down instead of jumping."
        )
    ],
    "balloon": [
        (
            "Why can a balloon basket feel gentle?",
            "A balloon basket can feel gentle because it floats and carries someone softly. But gentle is only safe if it stays steady enough."
        )
    ],
    "animal": [
        (
            "Why do animal stories often feel cozy?",
            "Animal stories often feel cozy because small animals can show big feelings in a gentle way. Their homes and worries feel tiny, warm, and easy to imagine."
        )
    ],
}
KNOWLEDGE_ORDER = ["toy_store", "magic", "animal", "barbie", "technic", "crane", "bridge", "balloon"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    stranded = f["stranded"]
    perch = f["perch"]
    helper = f["helper"]
    outcome = f["outcome"]
    prompts = [
        'Write a short Animal Story for a 3-to-5-year-old set in a magical toy store that includes the words "barbie" and "technic".',
        f"Tell a gentle nighttime story where {hero.id} and {friend.id} find {stranded.id} stuck on {perch.phrase} and must choose a toy helper wisely.",
    ]
    if outcome == "rescued":
        prompts.append(
            f"Write a cozy story where magic wakes a {helper.label} to help with a rescue, and the ending shows the toy store feeling safer and kinder than before."
        )
    else:
        prompts.append(
            f"Write a gentle cautionary story where a lovely-looking plan is not enough, because {helper.label} cannot safely rescue a friend from {perch.phrase}."
        )
    return prompts


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    stranded = f["stranded"]
    perch = f["perch"]
    helper = f["helper"]
    spark = f["spark"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type}, {friend.id} the {friend.type}, and {stranded.id} the {stranded.type} in a magical toy store. They are small animals facing one careful nighttime problem together."
        ),
        (
            "Where does the story happen?",
            "It happens in a toy store after closing time. The barbie aisle and the technic shelves both matter because the friends look at both kinds of toys while making their plan."
        ),
        (
            "What made the toy store magical that night?",
            f"{spark.phrase.capitalize()} woke the toy store with a soft glow. The magic could help, but it still asked the friends to make one kind and sensible choice."
        ),
        (
            f"Why was {stranded.id} in trouble?",
            f"{stranded.id} was stuck on {perch.phrase}, which was too high to climb down alone. That is why {hero.id} and {friend.id} had to think about reach and safety, not just speed."
        ),
        (
            f"Why did they choose the {helper.label}?",
            f"They chose it because they hoped it could reach {perch.label} and help bring {stranded.id} down. In this story world, even magic works best when the helper truly fits the problem."
        ),
    ]
    if outcome == "rescued":
        qa.append(
            (
                f"How did the rescue work?",
                f"The rescue worked because the {helper.label} could safely reach {perch.phrase}. {helper.qa_text}, so the plan matched the height and steadiness of the place."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended warmly with the three animals safe together under the shelves as morning came. The ending proves something changed, because {stranded.id} was no longer stranded and the friends had learned that kind magic should follow good sense."
            )
        )
    else:
        reach = "could not reach high enough" if not f["predicted_reach"] else "was not steady enough"
        qa.append(
            (
                f"Why did the plan fail?",
                f"The plan failed because the {helper.label} {reach}. The story shows that a lovely toy is not always the right rescue tool, even in a magical toy store."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended gently but sadly, with {stranded.id} still stuck until morning help could come. The change is in what the friends learned: they became more careful about matching the plan to the problem."
            )
        )
    return qa


def world_knowledge_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"toy_store", "magic", "animal", "barbie", "technic"} | set(f["helper"].tags)
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        perch="top_shelf",
        helper="technic_crane",
        hero_name="Pip",
        hero_kind="mouse",
        friend_name="Lulu",
        friend_kind="bunny",
        stranded_name="Milo",
        stranded_kind="hedgehog",
        spark="moonbell",
    ),
    StoryParams(
        perch="star_window",
        helper="barbie_balloon",
        hero_name="Nico",
        hero_kind="fox",
        friend_name="Mimi",
        friend_kind="mouse",
        stranded_name="Tess",
        stranded_kind="bunny",
        spark="stardust",
    ),
    StoryParams(
        perch="ribbon_tower",
        helper="technic_bridge",
        hero_name="Daisy",
        hero_kind="squirrel",
        friend_name="Ollie",
        friend_kind="hedgehog",
        stranded_name="Finn",
        stranded_kind="mouse",
        spark="moonbell",
    ),
]


ASP_RULES = r"""
sensible(H) :- helper(H), sense(H, S), sense_min(M), S >= M.
works(H, P) :- helper(H), perch(P), reach(H, RH), height(P, PH), RH >= PH,
               not shaky(P).
works(H, P) :- helper(H), perch(P), reach(H, RH), height(P, PH), RH >= PH,
               shaky(P), stable(H).

valid(P, H) :- perch(P), helper(H), sensible(H), works(H, P).

outcome(rescued) :- chosen_perch(P), chosen_helper(H), works(H, P).
outcome(stuck)   :- chosen_perch(P), chosen_helper(H), not works(H, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for perch_id, perch in PERCHES.items():
        lines.append(asp.fact("perch", perch_id))
        lines.append(asp.fact("height", perch_id, perch.height))
        if perch.shaky:
            lines.append(asp.fact("shaky", perch_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("reach", helper_id, helper.reach))
        lines.append(asp.fact("sense", helper_id, helper.sense))
        if helper.stable_on_shaky:
            lines.append(asp.fact("stable", helper_id))
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
            asp.fact("chosen_perch", params.perch),
            asp.fact("chosen_helper", params.helper),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
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

    cases: list[StoryParams] = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"resolve_params unexpectedly failed for seed {seed}")
            break

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome disagreements.")

    try:
        smoke = generate(CURATED[0])
        emit(smoke, trace=False, qa=False, header="### smoke test")
        print("OK: smoke generation and emit succeeded.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Animal-story toy-store world with magic, barbie sparkle, and technic rescue logic."
    )
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--spark", choices=SPARKS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible rescue plans derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper is not None and args.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {args.helper})")
    if args.perch is not None and args.perch not in PERCHES:
        raise StoryError(f"(Unknown perch: {args.perch})")
    if args.spark is not None and args.spark not in SPARKS:
        raise StoryError(f"(Unknown spark: {args.spark})")

    if args.helper is not None and not sensible_helper(HELPERS[args.helper]):
        raise StoryError(explain_helper(HELPERS[args.helper]))
    if args.helper is not None and args.perch is not None:
        helper = HELPERS[args.helper]
        perch = PERCHES[args.perch]
        if not rescue_works(helper, perch):
            raise StoryError(explain_combo(perch, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.perch is None or combo[0] == args.perch)
        and (args.helper is None or combo[1] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    perch_id, helper_id = rng.choice(sorted(combos))
    spark_id = args.spark or rng.choice(sorted(SPARKS))
    hero_kind = _pick_animal(rng, set())
    friend_kind = _pick_animal(rng, {hero_kind})
    stranded_kind = _pick_animal(rng, {hero_kind, friend_kind})

    used_names: set[str] = set()
    hero_name = _pick_name(rng, used_names)
    used_names.add(hero_name)
    friend_name = _pick_name(rng, used_names)
    used_names.add(friend_name)
    stranded_name = _pick_name(rng, used_names)

    return StoryParams(
        perch=perch_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_kind=hero_kind,
        friend_name=friend_name,
        friend_kind=friend_kind,
        stranded_name=stranded_name,
        stranded_kind=stranded_kind,
        spark=spark_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.perch not in PERCHES:
        raise StoryError(f"(Unknown perch: {params.perch})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.spark not in SPARKS:
        raise StoryError(f"(Unknown spark: {params.spark})")
    if params.hero_kind not in ANIMALS or params.friend_kind not in ANIMALS or params.stranded_kind not in ANIMALS:
        raise StoryError("(Unknown animal kind in params.)")
    if params.helper not in HELPERS or not sensible_helper(HELPERS[params.helper]):
        raise StoryError(explain_helper(HELPERS[params.helper]))
    if not rescue_works(HELPERS[params.helper], PERCHES[params.perch]):
        raise StoryError(explain_combo(PERCHES[params.perch], HELPERS[params.helper]))

    world = tell(
        perch=PERCHES[params.perch],
        helper=HELPERS[params.helper],
        hero_name=params.hero_name,
        hero_kind=ANIMALS[params.hero_kind],
        friend_name=params.friend_name,
        friend_kind=ANIMALS[params.friend_kind],
        stranded_name=params.stranded_name,
        stranded_kind=ANIMALS[params.stranded_kind],
        spark=SPARKS[params.spark],
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa_pairs(world)],
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (perch, helper) rescue plans:\n")
        for perch_id, helper_id in combos:
            print(f"  {perch_id:13} {helper_id}")
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
            header = f"### {p.hero_name}, {p.friend_name}, and {p.stranded_name}: {p.helper} at {p.perch}"
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
