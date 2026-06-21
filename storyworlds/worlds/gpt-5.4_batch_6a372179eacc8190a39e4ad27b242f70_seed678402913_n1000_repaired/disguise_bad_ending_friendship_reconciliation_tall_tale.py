#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/disguise_bad_ending_friendship_reconciliation_tall_tale.py
=====================================================================================

A standalone storyworld for a small tall-tale domain about two friends, a giant
disguise, a hurt feeling, and a chance to make up.

This world models a braggy frontier-fair sort of story:
- two children are good friends
- one child puts on an enormous disguise to surprise the other
- the disguise causes a wobble, a scare, or a muddy mishap
- the ending depends on whether the trickster tells the truth and repairs the harm

Some endings are bright and reconciled. Some are bad endings: the blue ribbon is
lost in the mud, or the friendship stays sore. Even then, the story still grows
from the same simulated state instead of swapping nouns into one frozen paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4/disguise_bad_ending_friendship_reconciliation_tall_tale.py
    python storyworlds/worlds/gpt-5.4/disguise_bad_ending_friendship_reconciliation_tall_tale.py --disguise hay_giant --support stilts
    python storyworlds/worlds/gpt-5.4/disguise_bad_ending_friendship_reconciliation_tall_tale.py --support boots
    python storyworlds/worlds/gpt-5.4/disguise_bad_ending_friendship_reconciliation_tall_tale.py --repair brag_more
    python storyworlds/worlds/gpt-5.4/disguise_bad_ending_friendship_reconciliation_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/disguise_bad_ending_friendship_reconciliation_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/disguise_bad_ending_friendship_reconciliation_tall_tale.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so the package dir is three
# levels up from here.
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
class Setting:
    id: str
    place: str
    stage: str
    horizon: str
    ground: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Disguise:
    id: str
    label: str
    costume: str
    boast: str
    reveal: str
    height: int
    wobble: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Support:
    id: str
    label: str
    phrase: str
    capacity: int
    steady: int
    ride_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Weather:
    id: str
    sky: str
    breeze: int
    mud: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    sense: int
    trust_gain: int
    practical_gain: int
    text: str
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


def _r_wobble_spreads(world: World) -> list[str]:
    out: list[str] = []
    giant = world.entities.get("giant")
    if giant is None:
        return out
    if giant.meters["wobble"] < THRESHOLD:
        return out
    sig = ("wobble_spreads", giant.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friend = world.get("friend")
    room = world.get("grounds")
    friend.memes["alarm"] += 1
    room.meters["commotion"] += 1
    return out


def _r_mud_splat(world: World) -> list[str]:
    out: list[str] = []
    grounds = world.get("grounds")
    if grounds.meters["muddy"] < THRESHOLD:
        return out
    giant = world.entities.get("giant")
    if giant is None or giant.meters["wobble"] < THRESHOLD:
        return out
    sig = ("mud_splat", giant.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    giant.meters["splattered"] += 1
    world.get("hero").memes["embarrassment"] += 1
    world.get("friend").memes["pity"] += 1
    return out


CAUSAL_RULES = [
    Rule(name="wobble_spreads", tag="social", apply=_r_wobble_spreads),
    Rule(name="mud_splat", tag="physical", apply=_r_mud_splat),
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


def support_safe(disguise: Disguise, support: Support) -> bool:
    return support.capacity >= disguise.height


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def trouble_score(disguise: Disguise, support: Support, weather: Weather) -> int:
    return max(0, disguise.wobble + weather.breeze + weather.mud - support.steady)


def friendship_hurt(disguise: Disguise) -> int:
    return disguise.height + 1


def repair_reconciles(disguise: Disguise, repair: Repair) -> bool:
    return repair.trust_gain >= friendship_hurt(disguise)


def repair_saves_show(disguise: Disguise, support: Support, weather: Weather, repair: Repair) -> bool:
    return repair.practical_gain >= trouble_score(disguise, support, weather)


def outcome_of(params: "StoryParams") -> str:
    disguise = DISGUISES[params.disguise]
    support = SUPPORTS[params.support]
    weather = WEATHERS[params.weather]
    repair = REPAIRS[params.repair]
    reconciled = repair_reconciles(disguise, repair)
    saved = repair_saves_show(disguise, support, weather, repair)
    if reconciled and saved:
        return "cheer"
    if reconciled and not saved:
        return "muddy_loss"
    return "rift"


def predict_mishap(world: World, disguise: Disguise, support: Support, weather: Weather) -> dict:
    sim = world.copy()
    giant = sim.get("giant")
    grounds = sim.get("grounds")
    giant.meters["wobble"] += float(max(0, disguise.wobble + weather.breeze - support.steady))
    if weather.mud:
        grounds.meters["muddy"] += float(weather.mud)
    propagate(sim, narrate=False)
    return {
        "wobble": giant.meters["wobble"],
        "muddy": grounds.meters["muddy"],
        "alarm": sim.get("friend").memes["alarm"],
    }


def introduce(world: World, hero: Entity, friend: Entity, setting: Setting, weather: Weather) -> None:
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"In {setting.place}, where {setting.horizon}, {hero.id} and {friend.id} were the sort of friends "
        f"who could laugh loud enough to rattle a row of pie tins."
    )
    world.say(
        f"That morning, {weather.sky}, and the whole town was headed toward {setting.stage} for the Tall-Tale Parade."
    )


def plan_show(world: World, hero: Entity, friend: Entity, disguise: Disguise, support: Support) -> None:
    world.say(
        f"The two of them had sworn to bring the tallest story in the county, so {hero.id} climbed onto "
        f"{support.phrase} and tucked into {disguise.costume}."
    )
    world.say(
        f'"Wait till you see my disguise," {hero.id} whispered. "I will look {disguise.boast}."'
    )
    friend.memes["trust"] += 1


def secret_choice(world: World, hero: Entity, friend: Entity, disguise: Disguise, support: Support, weather: Weather) -> None:
    pred = predict_mishap(world, disguise, support, weather)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_alarm"] = pred["alarm"]
    hero.memes["mischief"] += 1
    world.say(
        f"But instead of telling {friend.id} the full plan, {hero.id} slipped behind a flour wagon and finished the disguise in secret."
    )
    if pred["wobble"] >= THRESHOLD:
        world.say(
            f"The great outfit already swayed a little in the breeze, tall as trouble and almost as hard to steer."
        )
    else:
        world.say(
            f"The great outfit rose smooth and steady, taller than three fence posts wearing one hat."
        )


def reveal(world: World, hero: Entity, friend: Entity, disguise: Disguise, support: Support, weather: Weather) -> None:
    giant = world.get("giant")
    grounds = world.get("grounds")
    wobble = max(0, disguise.wobble + weather.breeze - support.steady)
    giant.meters["wobble"] += float(wobble)
    if weather.mud:
        grounds.meters["muddy"] += float(weather.mud)
    hero.memes["showoff"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then out strode the giant figure from behind the wagon, {disguise.costume}, riding on {support.label}. "
        f"{disguise.reveal}"
    )
    if world.get("friend").memes["alarm"] >= THRESHOLD:
        world.say(
            f'{friend.id} jumped so high that a crow on the fence looked down to see where {friend.pronoun()} had gone.'
        )
    else:
        world.say(
            f"{friend.id}'s mouth opened into a round, surprised O, and then into a grin."
        )


def hurt_friend(world: World, hero: Entity, friend: Entity) -> None:
    friend.memes["hurt"] += 1
    hero.memes["guilt"] += 1
    world.say(
        f'"You scared me first and told me second," said {friend.id}. "That did not feel like a friendly joke."'
    )


def mishap(world: World, hero: Entity, friend: Entity, setting: Setting, disguise: Disguise, support: Support, weather: Weather) -> None:
    giant = world.get("giant")
    grounds = world.get("grounds")
    severity = trouble_score(disguise, support, weather)
    giant.meters["trouble"] += float(severity)
    if severity <= 0:
        world.say(
            f"The huge costume swayed once, then settled, and the crowd gasped happily as the pretend giant marched past the lemonade stand."
        )
        return
    giant.meters["wobble"] += float(severity)
    if weather.mud:
        grounds.meters["muddy"] += float(weather.mud)
    propagate(world, narrate=False)
    if grounds.meters["muddy"] >= THRESHOLD:
        world.say(
            f"Then the ground turned slick as gravy on a plate. One long step slid, one giant sleeve pinwheeled, and the whole disguise sat down in the mud with a sound like a sleepy buffalo."
        )
    else:
        world.say(
            f"Then a gust pushed against the tall outfit. It lurched sideways, bobbled over a pickle barrel, and scattered the parade line into squeaks and skids."
        )
    world.say(
        f"The blue ribbon the children hoped to win fluttered away from the judges' table, and the crowd's cheer broke into a worried murmur."
    )


def repair_scene(world: World, hero: Entity, friend: Entity, repair: Repair) -> None:
    hero.memes["repairing"] += 1
    world.say(repair.text.replace("{friend}", friend.id).replace("{hero}", hero.id))


def ending_cheer(world: World, hero: Entity, friend: Entity, setting: Setting, repair: Repair) -> None:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"{friend.id} looked at {hero.id} for one long breath, then nodded. They took hold of the sagging giant together and marched it across {setting.stage} as partners again."
    )
    world.say(
        f"The judges laughed, the town clapped, and the two friends won a bright blue ribbon anyway, because the biggest tale that day was how a shaky disguise turned into an honest one."
    )
    world.say(
        f"That evening they hung the ribbon where the sunset could see it, and their friendship felt taller than the giant had."
    )


def ending_muddy_loss(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"{friend.id} sighed, then reached for the muddy sleeve. Together they peeled off the disguise, righted the hat, and laughed a little at how grandly it had fallen."
    )
    world.say(
        f"They did not win the blue ribbon. It lay somewhere under {setting.ground}, and the parade moved on without them."
    )
    world.say(
        f"But the two friends walked home side by side, mud drying on their boots and peace back between them, which was a better thing to carry than any prize."
    )


def ending_rift(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    friend.memes["distance"] += 1
    hero.memes["lonely"] += 1
    world.say(
        f"{friend.id} did not answer right away. {friend.pronoun().capitalize()} stepped back from the muddy giant and folded {friend.pronoun('possessive')} arms."
    )
    world.say(
        f'The parade rolled on without them, and the blue ribbon went to somebody else while the big disguise sagged beside {setting.stage} like a sorry barn with its roof caved in.'
    )
    world.say(
        f"By sundown, {hero.id} was walking home alone, knowing a friendship can be easier to frighten than to mend."
    )


def tell(
    setting: Setting,
    disguise: Disguise,
    support: Support,
    weather: Weather,
    repair: Repair,
    hero_name: str = "Mabel",
    hero_gender: str = "girl",
    friend_name: str = "June",
    friend_gender: str = "girl",
    judge_type: str = "mother",
    hero_trait: str = "bold",
    friend_trait: str = "steady",
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=[hero_trait],
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        traits=[friend_trait],
    ))
    judge = world.add(Entity(
        id="Judge",
        kind="character",
        type=judge_type,
        role="judge",
        label="the judge",
    ))
    grounds = world.add(Entity(
        id="grounds",
        type="grounds",
        label="the fairgrounds",
    ))
    giant = world.add(Entity(
        id="giant",
        type="disguise",
        label=disguise.label,
        phrase=disguise.costume,
        tags=set(disguise.tags),
    ))

    introduce(world, hero, friend, setting, weather)
    plan_show(world, hero, friend, disguise, support)

    world.para()
    secret_choice(world, hero, friend, disguise, support, weather)
    reveal(world, hero, friend, disguise, support, weather)
    hurt_friend(world, hero, friend)

    world.para()
    mishap(world, hero, friend, setting, disguise, support, weather)
    repair_scene(world, hero, friend, repair)

    outcome = outcome_of(StoryParams(
        setting=setting.id,
        disguise=disguise.id,
        support=support.id,
        weather=weather.id,
        repair=repair.id,
        hero=hero_name,
        hero_gender=hero_gender,
        friend=friend_name,
        friend_gender=friend_gender,
        judge=judge_type,
        hero_trait=hero_trait,
        friend_trait=friend_trait,
    ))

    world.para()
    if outcome == "cheer":
        ending_cheer(world, hero, friend, setting, repair)
    elif outcome == "muddy_loss":
        ending_muddy_loss(world, hero, friend, setting)
    else:
        ending_rift(world, hero, friend, setting)

    world.facts.update(
        hero=hero,
        friend=friend,
        judge=judge,
        grounds=grounds,
        giant=giant,
        setting=setting,
        disguise=disguise,
        support=support,
        weather=weather,
        repair=repair,
        outcome=outcome,
        reconciled=outcome in {"cheer", "muddy_loss"},
        kept_prize=outcome == "cheer",
        trouble=trouble_score(disguise, support, weather),
        friendship_hurt=friendship_hurt(disguise),
    )
    return world


SETTINGS = {
    "prairie_fair": Setting(
        id="prairie_fair",
        place="a prairie fair so wide it looked stitched to the edge of the sky",
        stage="the parade lane by the grandstand",
        horizon="the wheat shone like a million little brass buttons",
        ground="the fairground mud",
        tags={"fair", "parade"},
    ),
    "river_landing": Setting(
        id="river_landing",
        place="a river landing where the dock boards bragged louder than the boatmen",
        stage="the boardwalk parade path",
        horizon="the river bent like a silver ribbon around the town",
        ground="the damp riverbank clay",
        tags={"river", "parade"},
    ),
    "sunflower_day": Setting(
        id="sunflower_day",
        place="a sunflower field with a picnic lane down the middle",
        stage="the sunflower path",
        horizon="yellow heads nodded clear out to the fence line",
        ground="the dark garden loam",
        tags={"field", "parade"},
    ),
}

DISGUISES = {
    "hay_giant": Disguise(
        id="hay_giant",
        label="hay giant",
        costume="inside a hill of hay with a turnip grin and sleeves as long as rain gutters",
        boast="as tall as a windmill wearing Sunday boots",
        reveal="The crowd saw a hay giant where a child had been a moment before.",
        height=3,
        wobble=2,
        tags={"disguise", "hay"},
    ),
    "cloud_cowboy": Disguise(
        id="cloud_cowboy",
        label="cloud cowboy",
        costume="in a puffed-up white disguise with a rope belt and a hat broad enough to shade a calf",
        boast="like a cowboy who had lassoed a cloud and climbed inside it",
        reveal="It seemed a cloud had grown legs and come swaggering into town.",
        height=2,
        wobble=1,
        tags={"disguise", "cloud"},
    ),
    "scarecrow_king": Disguise(
        id="scarecrow_king",
        label="scarecrow king",
        costume="wrapped in patchwork sacks with corn-silk whiskers and a crown made of pie tins",
        boast="taller than the meeting-house weather vane",
        reveal="For one blink, half the town believed the fields had sent in their own king.",
        height=3,
        wobble=3,
        tags={"disguise", "scarecrow"},
    ),
}

SUPPORTS = {
    "wagon": Support(
        id="wagon",
        label="the wagon bed",
        phrase="the wagon bed with hidden boards under the straw",
        capacity=3,
        steady=3,
        ride_text="rolling high on the wagon bed",
        tags={"wagon"},
    ),
    "stilts": Support(
        id="stilts",
        label="a pair of hickory stilts",
        phrase="a pair of hickory stilts",
        capacity=3,
        steady=2,
        ride_text="teetering on hickory stilts",
        tags={"stilts"},
    ),
    "boots": Support(
        id="boots",
        label="stacked boot boxes",
        phrase="stacked boot boxes under a tarp",
        capacity=1,
        steady=1,
        ride_text="perched on stacked boot boxes",
        tags={"boots"},
    ),
}

WEATHERS = {
    "clear": Weather(
        id="clear",
        sky="the sky was clear and blue enough to wash in",
        breeze=0,
        mud=0,
        tags={"clear"},
    ),
    "breezy": Weather(
        id="breezy",
        sky="a playful wind kept tugging at ribbons and hat brims",
        breeze=1,
        mud=0,
        tags={"wind"},
    ),
    "drizzly": Weather(
        id="drizzly",
        sky="a silver drizzle had polished every board and made the earth soft",
        breeze=1,
        mud=1,
        tags={"rain", "mud"},
    ),
}

REPAIRS = {
    "apologize_and_patch": Repair(
        id="apologize_and_patch",
        sense=3,
        trust_gain=4,
        practical_gain=3,
        text='"I am sorry, {friend}," said {hero}. "The surprise mattered less than you did." Then {hero} climbed down, told the truth to the judge, and worked with {friend} to patch the torn disguise before the next drumbeat.',
        qa_text="apologized, told the truth, and patched the disguise together",
        tags={"apology", "truth"},
    ),
    "share_credit": Repair(
        id="share_credit",
        sense=2,
        trust_gain=4,
        practical_gain=1,
        text='"I was showy and silly," {hero} said. "If there is any cheering left, we share it." {hero} pulled off the giant hat, offered it to {friend}, and asked to finish the parade side by side.',
        qa_text="admitted the mistake and asked to share the show",
        tags={"apology", "sharing"},
    ),
    "brag_more": Repair(
        id="brag_more",
        sense=1,
        trust_gain=0,
        practical_gain=0,
        text='{hero} tried to laugh it off and boomed in a giant voice that the town should cheer louder instead of fussing. That only made the hurt feeling heavier.',
        qa_text="kept bragging instead of making things right",
        tags={"boast"},
    ),
    "hide_inside": Repair(
        id="hide_inside",
        sense=0,
        trust_gain=0,
        practical_gain=0,
        text='{hero} ducked deeper into the disguise and hoped the trouble might pass by without a word. It did not.',
        qa_text="hid in the disguise and said nothing helpful",
        tags={"avoid"},
    ),
}

GIRL_NAMES = ["Mabel", "Nell", "June", "Ada", "Josie", "Clara", "Daisy", "Ruby"]
BOY_NAMES = ["Hank", "Eli", "Jesse", "Cal", "Otis", "Beau", "Silas", "Roy"]
TRAITS = ["bold", "merry", "steady", "clever", "stubborn", "warmhearted"]


@dataclass
class StoryParams:
    setting: str
    disguise: str
    support: str
    weather: str
    repair: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    judge: str
    hero_trait: str
    friend_trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    if not sensible_repairs():
        return combos
    for setting_id in SETTINGS:
        for disguise_id, disguise in DISGUISES.items():
            for support_id, support in SUPPORTS.items():
                if not support_safe(disguise, support):
                    continue
                for weather_id in WEATHERS:
                    combos.append((setting_id, disguise_id, support_id, weather_id))
    return combos


KNOWLEDGE = {
    "disguise": [(
        "What is a disguise?",
        "A disguise is something you wear to look like someone or something else. It can be for play, but people should still be kind and honest about it."
    )],
    "apology": [(
        "What does an apology do?",
        "An apology tells the truth about a mistake and shows you want to make things right. A real apology is kinder when it comes with helping."
    )],
    "friendship": [(
        "What helps a friendship after someone gets hurt feelings?",
        "Listening, telling the truth, and trying to repair the harm all help. Friends do better when they care more about each other than about winning."
    )],
    "stilts": [(
        "What are stilts?",
        "Stilts are long poles you stand on to make yourself taller. They can be wobbly, so they must be used carefully."
    )],
    "wagon": [(
        "Why is a wagon steadier than stilts?",
        "A wagon keeps your weight on a broad floor instead of two narrow poles. That makes it easier to balance something tall."
    )],
    "mud": [(
        "Why is mud slippery?",
        "Mud is wet soil, and the water lets shoes slide on top of it. That is why people can slip when the ground gets muddy."
    )],
    "truth": [(
        "Why is telling the truth important after a trick?",
        "Telling the truth helps people understand what really happened. It is the first step toward trust coming back."
    )],
}
KNOWLEDGE_ORDER = ["disguise", "apology", "friendship", "stilts", "wagon", "mud", "truth"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    disguise = f["disguise"]
    outcome = f["outcome"]
    base = (
        f'Write a tall-tale style story for a 3-to-5-year-old that includes the word "disguise", '
        f'features friendship, and begins with two children planning a parade trick.'
    )
    if outcome == "cheer":
        return [
            base,
            f"Tell a frontier-fair story where {hero.id} wears a {disguise.label} disguise, scares {friend.id} by accident, then tells the truth and makes up with {friend.pronoun('object')}.",
            "Write a playful tall tale where a giant parade costume causes trouble, but honesty and teamwork save both the show and the friendship.",
        ]
    if outcome == "muddy_loss":
        return [
            base,
            f"Tell a tall tale where {hero.id}'s disguise falls into trouble, the prize is lost, but {hero.id} and {friend.id} still reconcile.",
            "Write a story with a bad ending for the contest but a good ending for the friendship: the children lose the ribbon and win each other back.",
        ]
    return [
        base,
        f"Tell a tall tale where {hero.id} uses a disguise to show off, hurts {friend.id}'s feelings, and the parade ends badly because {hero.pronoun()} does not repair the harm.",
        "Write a sad, child-facing story where a trick becomes too big, the blue ribbon is lost, and a friendship stays sore at the end.",
    ]


def pair_noun(hero: Entity, friend: Entity) -> str:
    if hero.type == "girl" and friend.type == "girl":
        return "two friends"
    if hero.type == "boy" and friend.type == "boy":
        return "two friends"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    disguise = f["disguise"]
    support = f["support"]
    weather = f["weather"]
    repair = f["repair"]
    setting = f["setting"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(hero, friend)}, {hero.id} and {friend.id}, at {setting.place}. They were trying to bring the biggest tale to the parade."
        ),
        (
            f"What was {hero.id}'s plan?",
            f"{hero.id} wanted to surprise everyone by wearing a {disguise.label} disguise. {hero.pronoun('subject').capitalize()} climbed onto {support.label} so the costume would look wonderfully tall."
        ),
        (
            f"Why were {friend.id}'s feelings hurt?",
            f"{friend.id} was hurt because {hero.id} scared {friend.pronoun('object')} first and explained later. The trick put showing off ahead of friendship."
        ),
    ]
    if f["trouble"] > 0:
        qa.append((
            "What went wrong with the disguise?",
            f"The disguise got into trouble because it was tall and hard to steady, and {weather.sky.lower()}. That made the parade turn wobbly and spoiled their chance at the prize."
        ))
    else:
        qa.append((
            "Did the disguise cause a mishap?",
            "Not much. It swayed, but it did not truly crash the show, so the children still had a chance to fix the hurt feeling before the parade passed them by."
        ))
    if outcome == "cheer":
        qa.append((
            f"How did {hero.id} and {friend.id} reconcile?",
            f"{hero.id} {repair.qa_text}. That helped {friend.id} trust {hero.pronoun('object')} again, and the two of them finished the parade as partners."
        ))
        qa.append((
            "How did the story end?",
            "It ended happily. The friends made up and even won the blue ribbon after turning the shaky trick into an honest act."
        ))
    elif outcome == "muddy_loss":
        qa.append((
            f"Did {hero.id} and {friend.id} make up?",
            f"Yes. {hero.id} {repair.qa_text}, so the friendship healed even though the parade prize was gone."
        ))
        qa.append((
            "Why is this still a bad ending in one way?",
            "It is a bad ending for the contest because the children lost the blue ribbon and their big parade moment. But it is a better ending for their hearts because they walked home together."
        ))
    else:
        qa.append((
            f"Why did the friendship not heal by the end?",
            f"The friendship stayed sore because {hero.id} did not make a true repair. Without honest help, the hurt feeling stayed bigger than the joke."
        ))
        qa.append((
            "How did the story end?",
            "It ended sadly. The parade moved on, the ribbon went elsewhere, and the two friends were no longer walking side by side."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"disguise", "friendship"}
    tags |= set(f["disguise"].tags)
    tags |= set(f["support"].tags)
    tags |= set(f["repair"].tags)
    tags |= set(f["weather"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="prairie_fair",
        disguise="hay_giant",
        support="wagon",
        weather="clear",
        repair="apologize_and_patch",
        hero="Mabel",
        hero_gender="girl",
        friend="June",
        friend_gender="girl",
        judge="mother",
        hero_trait="bold",
        friend_trait="steady",
    ),
    StoryParams(
        setting="river_landing",
        disguise="cloud_cowboy",
        support="stilts",
        weather="drizzly",
        repair="share_credit",
        hero="Eli",
        hero_gender="boy",
        friend="Roy",
        friend_gender="boy",
        judge="father",
        hero_trait="merry",
        friend_trait="warmhearted",
    ),
    StoryParams(
        setting="sunflower_day",
        disguise="scarecrow_king",
        support="wagon",
        weather="drizzly",
        repair="apologize_and_patch",
        hero="Ada",
        hero_gender="girl",
        friend="Clara",
        friend_gender="girl",
        judge="mother",
        hero_trait="clever",
        friend_trait="steady",
    ),
    StoryParams(
        setting="prairie_fair",
        disguise="hay_giant",
        support="stilts",
        weather="breezy",
        repair="brag_more",
        hero="Hank",
        hero_gender="boy",
        friend="Josie",
        friend_gender="girl",
        judge="father",
        hero_trait="bold",
        friend_trait="warmhearted",
    ),
]


def explain_rejection(disguise: Disguise, support: Support) -> str:
    return (
        f"(No story: {support.label} cannot safely carry a {disguise.label}. "
        f"The disguise wants height {disguise.height}, but the support can only manage {support.capacity}. "
        f"Pick a steadier base like the wagon or stilts.)"
    )


def explain_repair(repair_id: str) -> str:
    repair = REPAIRS[repair_id]
    better = " / ".join(sorted(r.id for r in sensible_repairs()))
    return (
        f"(Refusing repair '{repair_id}': it scores too low on common sense "
        f"(sense={repair.sense} < {SENSE_MIN}). A storyworld should prefer honest repair. "
        f"Try: {better}.)"
    )


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
safe_support(D, S) :- disguise(D), support(S), height(D, H), capacity(S, C), C >= H.
sensible_repair(R) :- repair(R), sense(R, V), sense_min(M), V >= M.
valid(Se, D, S, W) :- setting(Se), disguise(D), support(S), weather(W), safe_support(D, S).

% --- outcome model ---------------------------------------------------------
friendship_hurt(D, H + 1) :- height(D, H).
reconciled :- chosen_disguise(D), chosen_repair(R),
              friendship_hurt(D, Need), trust_gain(R, Gain), Gain >= Need.

trouble(T) :- chosen_disguise(D), chosen_support(S), chosen_weather(W),
              wobble(D, Dw), breeze(W, Bw), mud(W, Mw), steady(S, Ss),
              X = Dw + Bw + Mw - Ss, X > 0, T = X.
trouble(0) :- chosen_disguise(D), chosen_support(S), chosen_weather(W),
              wobble(D, Dw), breeze(W, Bw), mud(W, Mw), steady(S, Ss),
              X = Dw + Bw + Mw - Ss, X <= 0.

saved_show :- chosen_repair(R), trouble(T), practical_gain(R, P), P >= T.

outcome(cheer) :- reconciled, saved_show.
outcome(muddy_loss) :- reconciled, not saved_show.
outcome(rift) :- not reconciled.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did, disguise in DISGUISES.items():
        lines.append(asp.fact("disguise", did))
        lines.append(asp.fact("height", did, disguise.height))
        lines.append(asp.fact("wobble", did, disguise.wobble))
    for sid, support in SUPPORTS.items():
        lines.append(asp.fact("support", sid))
        lines.append(asp.fact("capacity", sid, support.capacity))
        lines.append(asp.fact("steady", sid, support.steady))
    for wid, weather in WEATHERS.items():
        lines.append(asp.fact("weather", wid))
        lines.append(asp.fact("breeze", wid, weather.breeze))
        lines.append(asp.fact("mud", wid, weather.mud))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("sense", rid, repair.sense))
        lines.append(asp.fact("trust_gain", rid, repair.trust_gain))
        lines.append(asp.fact("practical_gain", rid, repair.practical_gain))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_repairs() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_repair/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible_repair"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_disguise", params.disguise),
        asp.fact("chosen_support", params.support),
        asp.fact("chosen_weather", params.weather),
        asp.fact("chosen_repair", params.repair),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "disguise" not in sample.story.lower():
        raise StoryError("(Verify failed: smoke test story was empty or missed the seed word.)")
    with contextlib.redirect_stdout(io.StringIO()):
        emit(sample, trace=True, qa=True, header="smoke")


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

    clingo_repairs = set(asp_sensible_repairs())
    python_repairs = {r.id for r in sensible_repairs()}
    if clingo_repairs == python_repairs:
        print(f"OK: sensible repairs match ({sorted(clingo_repairs)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: clingo={sorted(clingo_repairs)} python={sorted(python_repairs)}")

    cases = list(CURATED)
    for seed in range(60):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            continue
    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        _smoke_test()
        print("OK: smoke test generation/emit passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: a giant disguise, a hurt friend, and a chance to reconcile."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--disguise", choices=DISGUISES)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--judge", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.disguise and args.support:
        disguise = DISGUISES[args.disguise]
        support = SUPPORTS[args.support]
        if not support_safe(disguise, support):
            raise StoryError(explain_rejection(disguise, support))
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair(args.repair))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.disguise is None or combo[1] == args.disguise)
        and (args.support is None or combo[2] == args.support)
        and (args.weather is None or combo[3] == args.weather)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, disguise_id, support_id, weather_id = rng.choice(sorted(combos))
    repair_id = args.repair or rng.choice(sorted(r.id for r in sensible_repairs()))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    friend = args.friend or _pick_name(rng, friend_gender, avoid=hero)
    judge = args.judge or rng.choice(["mother", "father"])
    hero_trait = rng.choice(TRAITS)
    friend_trait = rng.choice([t for t in TRAITS if t != hero_trait] or TRAITS)
    return StoryParams(
        setting=setting_id,
        disguise=disguise_id,
        support=support_id,
        weather=weather_id,
        repair=repair_id,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        judge=judge,
        hero_trait=hero_trait,
        friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        disguise = DISGUISES[params.disguise]
        support = SUPPORTS[params.support]
        weather = WEATHERS[params.weather]
        repair = REPAIRS[params.repair]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter value: {err})") from err

    if not support_safe(disguise, support):
        raise StoryError(explain_rejection(disguise, support))
    if repair.sense < SENSE_MIN:
        raise StoryError(explain_repair(params.repair))

    world = tell(
        setting=setting,
        disguise=disguise,
        support=support,
        weather=weather,
        repair=repair,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        judge_type=params.judge,
        hero_trait=params.hero_trait,
        friend_trait=params.friend_trait,
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
        print(asp_program("", "#show valid/4.\n#show sensible_repair/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible repairs: {', '.join(asp_sensible_repairs())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, disguise, support, weather) combos:\n")
        for setting_id, disguise_id, support_id, weather_id in combos:
            print(f"  {setting_id:14} {disguise_id:15} {support_id:8} {weather_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
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
            header = (
                f"### {p.hero} & {p.friend}: {p.disguise} on {p.support} "
                f"({p.setting}, {p.weather}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
