#!/usr/bin/env python3
"""
storyworlds/worlds/fuzzy_field_rusty_cabin_whispering_cloud_campground.py
=========================================================================

A standalone storyworld for the generated seed:

    Words: fuzzy field, rusty cabin, whispering cloud
    Setting: campground
    Features: Surprise, Humor
    Style: Heartwarming

Internal source tale:
    Two children help ready bedtime cocoa at a campground. Beside the fuzzy
    field stands a rusty cabin where the mugs are kept, and above it drifts a
    whispering cloud. Wind from the cloud turns a loose bit of cabin gear into
    a spooky-sounding whisper, so the younger campers start to hesitate. A
    silly fuzzy-field mishap makes the children laugh instead of panic, they
    trace the whisper to its real physical cause, fix it with camp gear, and a
    small surprise tumbles free just in time for the cocoa bell.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Campground:
    id: str
    name: str
    field_detail: str
    cabin_detail: str
    helper_title: str
    snack: str
    ending_sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Whisper:
    id: str
    mark: str
    need: str
    object_label: str
    clue: str
    whisper_line: str
    surprise_item: str
    surprise_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    mark: str
    need: str
    event: str
    discovery: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    need: str
    gear: str
    action: str
    qa: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, campground: Campground) -> None:
        self.campground = campground
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}
        self.history: list[tuple[str, str]] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        if ent.role:
            self.entities[ent.role] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def note(self, tag: str, detail: str) -> None:
        self.history.append((tag, detail))

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.campground)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.history = list(self.history)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_cloud_makes_whisper(world: World) -> list[str]:
    cloud = world.get("cloud")
    rig = world.get("whisper_rig")
    cocoa = world.get("cocoa_circle")
    hero = world.get("hero")
    friend = world.get("friend")
    if cloud.meters["wind"] < THRESHOLD or rig.meters["loose"] < THRESHOLD:
        return []
    sig = ("whisper", rig.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    rig.meters["whispering"] += 1
    cocoa.meters["delay"] += 1
    hero.memes["worry"] += 1
    friend.memes["worry"] += 1
    world.note("whisper", "Wind from the whispering cloud turned a loose cabin object into a spooky whisper.")
    return ["__whisper__"]


def _r_fuzzy_field_giggles(world: World) -> list[str]:
    field = world.get("field")
    hero = world.get("hero")
    friend = world.get("friend")
    if field.meters["fluff_swirl"] < THRESHOLD or friend.memes["nose_tickled"] < THRESHOLD:
        return []
    sig = ("giggles", friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["giggles"] += 1
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1)
    hero.memes["calm"] += 1
    friend.memes["calm"] += 1
    world.note("humor", "A puff from the fuzzy field turned fear into laughter.")
    return [
        f"A puff from the fuzzy field stuck to {friend.id}'s lip like a tiny mustache. "
        f"{friend.id} sneezed, then both children laughed so hard that the whisper stopped feeling big."
    ]


def _r_fix_steadies_camp(world: World) -> list[str]:
    rig = world.get("whisper_rig")
    cocoa = world.get("cocoa_circle")
    hero = world.get("hero")
    friend = world.get("friend")
    if rig.meters["secured"] < THRESHOLD:
        return []
    sig = ("steady", rig.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    rig.meters["loose"] = 0.0
    rig.meters["whispering"] = 0.0
    cocoa.meters["delay"] = 0.0
    cocoa.meters["ready"] += 1
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.note("repair", "The whispering object was secured and the cocoa circle was ready again.")
    return [
        "The next breeze only brushed the rusty cabin with a soft shhh, and the sound no longer felt scary."
    ]


def _r_shared_laughter_warms_camp(world: World) -> list[str]:
    cocoa = world.get("cocoa_circle")
    friend = world.get("friend")
    hero = world.get("hero")
    if cocoa.meters["ready"] < THRESHOLD or friend.memes["giggles"] < THRESHOLD:
        return []
    sig = ("warm", cocoa.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cocoa.meters["warm"] += 1
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.note("warmth", "The children finished the problem with laughter still between them.")
    return []


CAUSAL_RULES = [
    Rule("cloud_makes_whisper", "physical", _r_cloud_makes_whisper),
    Rule("fuzzy_field_giggles", "emotional", _r_fuzzy_field_giggles),
    Rule("fix_steadies_camp", "physical", _r_fix_steadies_camp),
    Rule("shared_laughter_warms_camp", "social", _r_shared_laughter_warms_camp),
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


def whisper_matches(whisper: Whisper, cause: Cause) -> bool:
    return whisper.mark == cause.mark


def fix_fits(cause: Cause, fix: Fix) -> bool:
    return cause.need == fix.need


def compatible(campground: Campground, whisper: Whisper, cause: Cause, fix: Fix) -> bool:
    return campground.id in CAMPGROUNDS and whisper_matches(whisper, cause) and fix_fits(cause, fix)


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for campground_id, campground in CAMPGROUNDS.items():
        for whisper_id, whisper in WHISPERS.items():
            for cause_id, cause in CAUSES.items():
                for fix_id, fix in FIXES.items():
                    if compatible(campground, whisper, cause, fix):
                        out.append((campground_id, whisper_id, cause_id, fix_id))
    return sorted(out)


def predict_delay(world: World) -> dict[str, float]:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "delay": sim.get("cocoa_circle").meters["delay"],
        "whispering": sim.get("whisper_rig").meters["whispering"],
    }


def introduce(world: World, hero: Entity, friend: Entity, host: Entity) -> None:
    camp = world.campground
    cloud = world.get("cloud")
    field = world.get("field")
    cabin = world.get("cabin")
    hero.memes["care"] += 1
    friend.memes["care"] += 1
    cloud.memes["playful"] += 1
    field.meters["soft"] += 1
    cabin.meters["rust"] += 1
    world.note("premise", f"{hero.id} and {friend.id} were helping with cocoa hour at {camp.name}.")
    world.say(
        f"At {camp.name}, {hero.id} and {friend.id} liked to help at bedtime cocoa."
    )
    world.say(
        f"Next to their tents stretched a fuzzy field, and {camp.field_detail}."
    )
    world.say(
        f"Beside it stood a rusty cabin, and {camp.cabin_detail}."
    )
    world.say(
        f"Above both floated a whispering cloud. It dragged a silver edge over the campground as if it had a secret it wanted to tell."
    )
    world.say(
        f"{host.id}, the {camp.helper_title}, asked the two friends to get the cocoa corner ready before the littlest campers came with their mugs."
    )


def set_task(world: World, whisper: Whisper) -> None:
    cocoa = world.get("cocoa_circle")
    rig = world.get("whisper_rig")
    item = world.get("surprise_item")
    cocoa.meters["planned"] += 1
    rig.meters["loose"] += 1
    item.meters["hidden"] += 1
    world.say(
        f"They hurried to hang {whisper.object_label} by the cabin steps so the cocoa corner would feel cheerful instead of sleepy."
    )
    world.note("goal", "The children wanted the cocoa corner ready before the younger campers arrived.")


def begin_whisper(world: World, hero: Entity, friend: Entity, whisper: Whisper, cause: Cause) -> None:
    world.get("cloud").meters["wind"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the whispering cloud sent a cool puff over the roof. {cause.event}"
    )
    world.say(
        f'{whisper.object_label.capitalize()} rustled, and the rusty cabin seemed to say, "{whisper.whisper_line}"'
    )
    world.say(
        f"{hero.id} squeezed the handle of the cocoa basket. A few younger campers stopped on the path and stared at the cabin."
    )
    world.note("problem", cause.risk)


def host_warns(world: World, host: Entity) -> None:
    pred = predict_delay(world)
    if pred["delay"] >= THRESHOLD:
        world.facts["predicted_delay"] = pred["delay"]
        world.say(
            f'"If that whisper keeps going," {host.id} said gently, "the little campers may think the cabin is cross with them. Let us find the real reason before cocoa gets cold."'
        )


def funny_break(world: World, hero: Entity, friend: Entity) -> None:
    world.get("field").meters["fluff_swirl"] += 1
    friend.memes["nose_tickled"] += 1
    propagate(world)
    world.say(
        f'Even {hero.id} had to grin. "{friend.id}, you look like a tiny grandpa with a cloud mustache," {hero.pronoun()} said.'
    )


def investigate(world: World, hero: Entity, friend: Entity, cause: Cause) -> None:
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    hero.memes["teamwork"] += 1
    friend.memes["teamwork"] += 1
    world.say(
        f"Still smiling, the two friends walked from the fuzzy field to the cabin wall and listened with their ears close to the metal."
    )
    world.say(
        f"There they found the truth: {cause.discovery}."
    )
    world.note("discovery", cause.discovery)


def repair(world: World, hero: Entity, friend: Entity, fix: Fix) -> None:
    rig = world.get("whisper_rig")
    hero.memes["responsibility"] += 1
    friend.memes["helping"] += 1
    rig.meters["secured"] += 1
    world.say(
        f"{friend.id} fetched {fix.gear}, and {hero.id} held the rattling piece still. {fix.action}"
    )
    propagate(world)
    world.note("fix", fix.qa)


def reveal_surprise(world: World, whisper: Whisper) -> None:
    item = world.get("surprise_item")
    if item.meters["hidden"] < THRESHOLD:
        return
    item.meters["hidden"] = 0.0
    item.meters["found"] += 1
    world.note("surprise", whisper.surprise_image)
    world.say(whisper.surprise_image)


def closing(world: World, hero: Entity, friend: Entity, host: Entity, fix: Fix) -> None:
    cocoa = world.get("cocoa_circle")
    camp = world.campground
    item = world.get("surprise_item")
    if cocoa.meters["warm"] >= THRESHOLD:
        world.say(
            f"Soon the younger campers came in a clump of sleepy slippers. This time the rusty cabin only hummed softly, so everyone stepped closer instead of backing away."
        )
        if item.meters["found"] >= THRESHOLD:
            world.say(
                f"{host.id} laughed when {item.label} appeared. {fix.ending_image}"
            )
        world.say(
            f"{hero.id} rang the cocoa call, {friend.id} passed out mugs, and the whispering cloud drifted over the fuzzy field like a blanket instead of a warning."
        )
        world.say(
            f"The campground sounded full of {camp.ending_sound}, and both children felt proud that they had turned a spooky joke into a warm one."
        )
        world.note("ending", "The cocoa circle became calm, funny, and welcoming again.")


def tell(
    campground: Campground,
    whisper: Whisper,
    cause: Cause,
    fix: Fix,
    hero_name: str = "June",
    hero_gender: str = "girl",
    friend_name: str = "Otis",
    friend_gender: str = "boy",
    host_name: str = "Ranger Bea",
    host_gender: str = "woman",
    trait: str = "careful",
) -> World:
    world = World(campground)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            traits=[trait],
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            label=friend_name,
            role="friend",
            traits=["playful"],
        )
    )
    host = world.add(
        Entity(
            id=host_name,
            kind="character",
            type=host_gender,
            label=host_name,
            role="host",
        )
    )
    world.add(Entity("field", type="field", label="fuzzy field"))
    world.add(Entity("cabin", type="cabin", label="rusty cabin"))
    world.add(Entity("cloud", type="cloud", label="whispering cloud"))
    world.add(Entity("whisper_rig", type="camp_gear", label=whisper.object_label))
    world.add(Entity("cocoa_circle", type="gathering", label=f"{campground.snack} circle"))
    world.add(Entity("surprise_item", type="camp_item", label=whisper.surprise_item))

    introduce(world, hero, friend, host)
    set_task(world, whisper)

    world.para()
    begin_whisper(world, hero, friend, whisper, cause)
    host_warns(world, host)
    funny_break(world, hero, friend)

    world.para()
    investigate(world, hero, friend, cause)
    repair(world, hero, friend, fix)
    reveal_surprise(world, whisper)
    closing(world, hero, friend, host, fix)

    world.facts.update(
        hero=hero,
        friend=friend,
        host=host,
        campground=campground,
        whisper=whisper,
        cause=cause,
        fix=fix,
        surprise_item=world.get("surprise_item"),
        cocoa_circle=world.get("cocoa_circle"),
        whisper_rig=world.get("whisper_rig"),
        resolved=world.get("cocoa_circle").meters["ready"] >= THRESHOLD,
        warm=world.get("cocoa_circle").meters["warm"] >= THRESHOLD,
        surprise=world.get("surprise_item").meters["found"] >= THRESHOLD,
        humor=friend.memes["giggles"] >= THRESHOLD,
    )
    return world


CAMPGROUNDS = {
    "fern_hollow": Campground(
        "fern_hollow",
        "Fern Hollow Campground",
        "the grass wore so many soft seed puffs that the children called it the fuzzy field even when no one else did",
        "the cabin boards smelled like rain and old nails, but the front step was always swept for evening cocoa",
        "camp host",
        "cocoa",
        "giggles and tin mugs clicking together",
        {"campground", "field", "cabin"},
    ),
    "pine_springs": Campground(
        "pine_springs",
        "Pine Springs Campground",
        "the fuzzy field glowed pale gold at dusk, as if the grass had put on soft slippers",
        "one rusty hinge sang whenever the door opened, though the shelves inside were neat as little rows of treasure",
        "night ranger",
        "apple cider",
        "small laughs under the pines",
        {"campground", "field", "cabin"},
    ),
    "creek_lantern": Campground(
        "creek_lantern",
        "Creek Lantern Campground",
        "the fuzzy field leaned toward the creek and tossed fluff into the air whenever the evening breeze ran through",
        "the rusty cabin had a roof the color of old pennies and a crate of bright enamel mugs by the steps",
        "camp leader",
        "warm milk with cinnamon",
        "the soft scrape of benches and happy whispers",
        {"campground", "field", "cabin"},
    ),
}

WHISPERS = {
    "cup_chain": Whisper(
        "cup_chain",
        "cup_chain",
        "knot",
        "a chain of tin cups",
        "a damp knot under the eaves and a line of cups tapping one another",
        "Soup for the cloud!",
        "the missing cocoa bell",
        "Then a bright surprise came free: the missing cocoa bell slid from behind the cups and dinged once against the cabin step.",
        {"humor", "surprise", "metal", "wind"},
    ),
    "ladle_sign": Whisper(
        "ladle_sign",
        "ladle_sign",
        "brace",
        "the old soup-ladle sign",
        "a wobbling ladle sign kissing the wall each time the wind leaned on it",
        "Tickle my cocoa!",
        "the camp joke card",
        "Then the best surprise fluttered down: the camp joke card had been hiding behind the sign, with a marshmallow face drawn right in the middle.",
        {"humor", "surprise", "metal", "wind"},
    ),
    "spoon_spinner": Whisper(
        "spoon_spinner",
        "spoon_spinner",
        "peg",
        "the spoon spinner",
        "one loose spoon arm chattering against the gutter while the spinner twirled",
        "Hats for porridge!",
        "the runaway napkin ring",
        "Then a little surprise popped loose: the runaway napkin ring rolled from the gutter and circled the host's boot like a shiny bug.",
        {"humor", "surprise", "metal", "wind"},
    ),
}

CAUSES = {
    "dew_slip": Cause(
        "dew_slip",
        "cup_chain",
        "knot",
        "Each breath of wind made the cups knock together in a whispery clatter.",
        "the cup chain's knot had soaked up dew and slipped halfway open under the roof edge",
        "if the whisper kept going, the smallest campers might decide the cocoa corner was spooky and stay back",
        {"wind", "metal", "camp"},
    ),
    "bent_hook": Cause(
        "bent_hook",
        "ladle_sign",
        "brace",
        "The wind kept nudging the sign until metal tapped the wall like teeth saying a joke.",
        "the ladle sign was hanging from one bent hook, so every gust knocked it against the cabin boards",
        "if the sign kept talking, the younger campers might laugh first and then feel nervous when they could not see the trick",
        {"wind", "metal", "camp"},
    ),
    "jumped_socket": Cause(
        "jumped_socket",
        "spoon_spinner",
        "peg",
        "The spinner turned too hard, and one spoon arm bounced against the gutter with silly little squeaks.",
        "one spoon arm had hopped out of its socket and was tapping the gutter each time the cloud pushed by",
        "if the tapping grew louder, the cocoa line would stall while everyone stared at the roof instead of gathering safely",
        {"wind", "metal", "camp"},
    ),
}

FIXES = {
    "dry_twine_bow": Fix(
        "dry_twine_bow",
        "knot",
        "dry twine from the craft box",
        "They tied a firm new bow, lifted the cups higher, and tucked the loose line where the wind could not nibble it.",
        "They used dry twine to retie the wet knot and stop the cups from knocking together.",
        "The bell sounded brighter after that, as if it liked being found in a brave little rescue.",
        {"gear", "repair"},
    ),
    "peg_loop_knot": Fix(
        "peg_loop_knot",
        "knot",
        "a tent peg and a loop of red cord",
        "They wrapped the cord around the peg, made a tidy loop, and pulled the cup chain snug beside the step rail.",
        "They anchored the loose cup line with cord and a tent peg so the wind could not swing it open again.",
        "The bell sounded brighter after that, and even the littlest camper grinned when it rang.",
        {"gear", "repair"},
    ),
    "dishcloth_brace": Fix(
        "dishcloth_brace",
        "brace",
        "a striped dishcloth and two clothespins",
        "They folded the dishcloth behind the sign like a soft pillow and pinned everything still until the metal stopped kissing the wall.",
        "They padded the sign with cloth and held it steady with clothespins so it could not bang against the boards.",
        "The joke card made the whole cocoa line laugh before the first sip was even poured.",
        {"gear", "repair"},
    ),
    "mug_shelf_brace": Fix(
        "mug_shelf_brace",
        "brace",
        "a wooden spoon and a mug-shelf clip",
        "They slipped the spoon behind the hook as a brace and fastened the top with a clip from the mug shelf.",
        "They braced the bent hook so the sign sat still instead of tapping the cabin.",
        "The joke card made the whole cocoa line laugh, and the cabin looked pleased to keep the punch line quiet.",
        {"gear", "repair"},
    ),
    "peg_reset": Fix(
        "peg_reset",
        "peg",
        "a spare tent peg and a loop of cord",
        "They nudged the spoon arm back into place and wedged it gently with the peg so it could spin without clattering.",
        "They reset the loose spoon arm and wedged it in place with a peg so it could move without hitting the gutter.",
        "The shiny ring rolling free made everyone cheer as if a tiny race had just been won.",
        {"gear", "repair"},
    ),
    "soap_lid_socket": Fix(
        "soap_lid_socket",
        "peg",
        "a soap-tin lid and a pocket screwdriver",
        "They tightened the socket with the screwdriver and slid the soap-tin lid underneath as a smooth little shield.",
        "They tightened the spoon socket and added a thin shield so the arm would not slap the gutter again.",
        "The shiny ring rolling free made the younger campers chase it in tiny careful steps until the host caught it.",
        {"gear", "repair"},
    ),
}

GIRL_NAMES = ["June", "Mina", "Tess", "Lila", "Nora"]
BOY_NAMES = ["Otis", "Leo", "Sam", "Finn", "Theo"]
TRAITS = ["careful", "gentle", "bright-eyed", "helpful", "thoughtful"]


@dataclass
class StoryParams:
    campground: str
    whisper: str
    cause: str
    fix: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    host: str
    host_gender: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "campground": [
        (
            "What is a campground?",
            "A campground is a place where people sleep outdoors in tents or cabins. It often has shared paths, camp helpers, and places to eat together.",
        )
    ],
    "field": [
        (
            "Why can a field look fuzzy?",
            "Some fields grow grasses or seed puffs that look soft from far away. When the wind moves through them, the fluff can drift into the air.",
        )
    ],
    "cabin": [
        (
            "What does rusty mean?",
            "Rusty means metal has grown rough and reddish after being wet for a long time. Rust can make old objects squeak, stick, or sound different in the wind.",
        )
    ],
    "wind": [
        (
            "Why can wind make metal whisper or rattle?",
            "Wind can shake loose metal until it taps or rubs against something nearby. That can sound like a hum, a whistle, or even a tiny pretend voice.",
        )
    ],
    "humor": [
        (
            "Why does laughing sometimes help during a problem?",
            "A gentle laugh can make people feel less scared and more steady. Then they can look at the real problem with clearer eyes.",
        )
    ],
    "repair": [
        (
            "Why should children fix a loose object before people gather around it?",
            "Loose objects can scare people or cause accidents if they keep moving in the wind. Fixing them first makes the place safer and calmer for everyone.",
        )
    ],
}
KNOWLEDGE_ORDER = ["campground", "field", "cabin", "wind", "humor", "repair"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    whisper = f["whisper"]
    campground = f["campground"]
    return [
        'Write a heartwarming campground story for young children that includes "fuzzy field," "rusty cabin," and "whispering cloud."',
        f"Tell a gentle story with humor and surprise where {hero.id} hears {whisper.object_label} by the rusty cabin and solves the mystery before bedtime cocoa at {campground.name}.",
        "Write a child-friendly story where a silly sound seems spooky at first, but laughter and careful fixing turn the ending warm.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    host = f["host"]
    campground = f["campground"]
    whisper = f["whisper"]
    cause = f["cause"]
    fix = f["fix"]
    item = f["surprise_item"]
    return [
        (
            "Where did the story happen?",
            f"The story happened at {campground.name}, beside the fuzzy field and the rusty cabin. The children were getting the cocoa corner ready there before bedtime.",
        ),
        (
            "What made the rusty cabin seem to whisper?",
            f"The whispering cloud pushed wind across {whisper.object_label}. That breeze set off the real problem: {cause.discovery}.",
        ),
        (
            "What funny thing happened in the fuzzy field?",
            f"A puff from the fuzzy field stuck to {friend.id}'s lip like a mustache. The sneeze and the silly look made {hero.id} and {friend.id} laugh, which helped them stop feeling so scared.",
        ),
        (
            "How did the children solve the problem?",
            f"{friend.id} brought {fix.gear}, and {hero.id} held the noisy piece still. {fix.qa}",
        ),
        (
            "What was the surprise at the end?",
            f"The surprise was that {item.label} came loose after the repair. That little discovery turned the whole cocoa gathering from worried to cheerful.",
        ),
        (
            "Why did the younger campers feel safe again?",
            f"They felt safe again because the whispering sound was fixed before cocoa time. After that, the cabin only made a soft harmless shhh, and the older children welcomed everyone in.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = (
        set(world.facts["campground"].tags)
        | set(world.facts["whisper"].tags)
        | set(world.facts["cause"].tags)
        | set(world.facts["fix"].tags)
    )
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    lines += [f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)]
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story world ==")
    for item in sample.story_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:13} ({ent.type:10}) {' '.join(bits)}")
    if world.history:
        lines.append("  history:")
        for tag, detail in world.history:
            lines.append(f"    - {tag}: {detail}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("fern_hollow", "cup_chain", "dew_slip", "dry_twine_bow", "June", "girl", "Otis", "boy", "Ranger Bea", "woman", "careful"),
    StoryParams("pine_springs", "ladle_sign", "bent_hook", "dishcloth_brace", "Mina", "girl", "Finn", "boy", "Ranger Sol", "man", "gentle"),
    StoryParams("creek_lantern", "spoon_spinner", "jumped_socket", "peg_reset", "Theo", "boy", "Lila", "girl", "Ranger Bea", "woman", "helpful"),
    StoryParams("fern_hollow", "cup_chain", "dew_slip", "peg_loop_knot", "Nora", "girl", "Sam", "boy", "Ranger Sol", "man", "thoughtful"),
    StoryParams("pine_springs", "ladle_sign", "bent_hook", "mug_shelf_brace", "Leo", "boy", "Tess", "girl", "Ranger Bea", "woman", "bright-eyed"),
    StoryParams("creek_lantern", "spoon_spinner", "jumped_socket", "soap_lid_socket", "Otis", "boy", "June", "girl", "Ranger Sol", "man", "careful"),
]


def explain_rejection(whisper: Whisper, cause: Cause, fix: Fix) -> str:
    if not whisper_matches(whisper, cause):
        return (
            f"(No story: {whisper.object_label} does not match the cause "
            f'"{cause.discovery}".)'
        )
    if not fix_fits(cause, fix):
        return (
            f"(No story: {fix.gear} does not solve the need created by "
            f'"{cause.discovery}".)'
        )
    return "(No story: the requested combination is not reasonable for this campground tale.)"


ASP_RULES = r"""
matching(Whisper,Cause) :- whisper(Whisper), cause(Cause), whisper_mark(Whisper,M), cause_mark(Cause,M).
effective(Cause,Fix) :- cause(Cause), fix(Fix), cause_need(Cause,N), fix_need(Fix,N).
valid(Camp,Whisper,Cause,Fix) :- campground(Camp), matching(Whisper,Cause), effective(Cause,Fix).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for campground_id in CAMPGROUNDS:
        lines.append(asp.fact("campground", campground_id))
    for whisper_id, whisper in WHISPERS.items():
        lines.append(asp.fact("whisper", whisper_id))
        lines.append(asp.fact("whisper_mark", whisper_id, whisper.mark))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("cause_mark", cause_id, cause.mark))
        lines.append(asp.fact("cause_need", cause_id, cause.need))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("fix_need", fix_id, fix.need))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def _exercise_samples() -> None:
    for idx, params in enumerate(CURATED):
        seeded = StoryParams(**vars(params))
        seeded.seed = 1000 + idx
        sample = generate(seeded)
        lower = sample.story.lower()
        for needle in ("fuzzy field", "rusty cabin", "whispering cloud"):
            if needle not in lower:
                raise StoryError(f"Verification sample missing required phrase: {needle}")
        if not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("Verification sample is missing prompts or one QA set.")
        if not sample.world.facts["resolved"] or not sample.world.facts["warm"]:
            raise StoryError("Verification sample failed to reach a warm resolved ending.")
        if not sample.world.facts["surprise"] or not sample.world.facts["humor"]:
            raise StoryError("Verification sample failed to realize both surprise and humor.")


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set != python_set:
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        return 1
    try:
        _exercise_samples()
    except StoryError as err:
        print(f"VERIFY FAILED: {err}")
        return 1
    print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    print("OK: curated samples keep the required landmarks, humor, surprise, and warm ending.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: fuzzy field, rusty cabin, whispering cloud, campground cocoa, surprise and humor."
    )
    ap.add_argument("--campground", choices=CAMPGROUNDS)
    ap.add_argument("--whisper", choices=WHISPERS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--host")
    ap.add_argument("--host-gender", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.whisper and args.cause and args.fix:
        whisper = WHISPERS[args.whisper]
        cause = CAUSES[args.cause]
        fix = FIXES[args.fix]
        if not compatible(next(iter(CAMPGROUNDS.values())), whisper, cause, fix):
            raise StoryError(explain_rejection(whisper, cause, fix))
    if args.whisper and args.cause and not whisper_matches(WHISPERS[args.whisper], CAUSES[args.cause]):
        raise StoryError(explain_rejection(WHISPERS[args.whisper], CAUSES[args.cause], next(iter(FIXES.values()))))
    if args.cause and args.fix and not fix_fits(CAUSES[args.cause], FIXES[args.fix]):
        whisper = WHISPERS[args.whisper] if args.whisper else next(
            w for w in WHISPERS.values() if w.mark == CAUSES[args.cause].mark
        )
        raise StoryError(explain_rejection(whisper, CAUSES[args.cause], FIXES[args.fix]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.campground is None or combo[0] == args.campground)
        and (args.whisper is None or combo[1] == args.whisper)
        and (args.cause is None or combo[2] == args.cause)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid fuzzy-field campground story matches the given options.)")

    campground, whisper, cause, fix = rng.choice(combos)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    friend = args.friend or _pick_name(rng, friend_gender, avoid=hero)
    host_gender = args.host_gender or rng.choice(["woman", "man"])
    host = args.host or ("Ranger Bea" if host_gender == "woman" else "Ranger Sol")
    return StoryParams(
        campground,
        whisper,
        cause,
        fix,
        hero,
        hero_gender,
        friend,
        friend_gender,
        host,
        host_gender,
        rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        CAMPGROUNDS[params.campground],
        WHISPERS[params.whisper],
        CAUSES[params.cause],
        FIXES[params.fix],
        params.hero,
        params.hero_gender,
        params.friend,
        params.friend_gender,
        params.host,
        params.host_gender,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (campground, whisper, cause, fix) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:15}" for part in combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero}: {p.whisper} at {p.campground} ({p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
