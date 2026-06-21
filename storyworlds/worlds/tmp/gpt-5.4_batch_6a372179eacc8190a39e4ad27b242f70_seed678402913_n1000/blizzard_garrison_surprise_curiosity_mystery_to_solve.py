#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/blizzard_garrison_surprise_curiosity_mystery_to_solve.py
===================================================================================

A standalone story world about a silly little mystery inside a snowy garrison.

Premise
-------
A child waits inside an old hilltop garrison while a blizzard piles snow against
the doors. The cook promises a surprise snack for the whole watch. Before the
surprise is served, one treat goes missing. A curious child and a comic helper
follow a trail of crumbs, prints, or feathers through the drafty rooms and
discover that the "thief" is only a cold, frightened animal hiding from the
storm. The real surprise turns out to be a fresh tray of treats, and the whole
garrison ends the night laughing.

The world enforces one core reasonableness rule:
- a culprit only fits a story when it plausibly likes the treat,
- can plausibly reach the chosen stash room,
- leaves the kind of clue the helper knows how to read.

Run it
------
    python storyworlds/worlds/gpt-5.4/blizzard_garrison_surprise_curiosity_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4/blizzard_garrison_surprise_curiosity_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4/blizzard_garrison_surprise_curiosity_mystery_to_solve.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/blizzard_garrison_surprise_curiosity_mystery_to_solve.py --qa
    python storyworlds/worlds/gpt-5.4/blizzard_garrison_surprise_curiosity_mystery_to_solve.py --trace
    python storyworlds/worlds/gpt-5.4/blizzard_garrison_surprise_curiosity_mystery_to_solve.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root. This file lives under storyworlds/worlds/gpt-5.4/, so we
# need the storyworlds/ package directory on sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "animal" | "thing" | "place"
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
        female = {"girl", "woman", "mother", "cook_woman"}
        male = {"boy", "man", "father", "guard_man"}
        if self.kind == "animal":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    plural: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class CulpritCfg:
    id: str
    label: str
    phrase: str
    print_word: str
    clue_kind: str
    likes: set[str] = field(default_factory=set)
    reachable: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Stash:
    id: str
    label: str
    phrase: str
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    label: str
    phrase: str
    helper_type: str
    skill: set[str] = field(default_factory=set)
    line: str = ""
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


def _r_fear_from_blizzard(world: World) -> list[str]:
    culprit = world.get("culprit")
    storm = world.get("storm")
    if storm.meters["blowing"] < THRESHOLD:
        return []
    sig = ("fear", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    culprit.memes["fear"] += 1
    return []


def _r_nibble(world: World) -> list[str]:
    culprit = world.get("culprit")
    treat = world.get("treat")
    clue = world.get("clue")
    if culprit.meters["hungry"] < THRESHOLD:
        return []
    if treat.meters["aroma"] < THRESHOLD:
        return []
    sig = ("nibble", culprit.id, treat.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    culprit.meters["nibbled"] += 1
    treat.meters["missing"] += 1
    clue.meters["fresh"] += 1
    return []


def _r_comfort(world: World) -> list[str]:
    culprit = world.get("culprit")
    helper = world.get("helper")
    if culprit.memes["fear"] < THRESHOLD or helper.meters["offered_warmth"] < THRESHOLD:
        return []
    sig = ("comfort", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    culprit.memes["fear"] = 0.0
    culprit.memes["relief"] += 1
    helper.memes["kindness"] += 1
    world.get("child").memes["relief"] += 1
    return []


def _r_solved(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    culprit = world.get("culprit")
    if culprit.memes["relief"] < THRESHOLD:
        return []
    sig = ("solved", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["pride"] += 1
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.get("cook").memes["joy"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="fear_from_blizzard", tag="emotion", apply=_r_fear_from_blizzard),
    Rule(name="nibble", tag="physical", apply=_r_nibble),
    Rule(name="comfort", tag="emotion", apply=_r_comfort),
    Rule(name="solved", tag="emotion", apply=_r_solved),
]


def propagate(world: World, narrate: bool = False) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule.apply(world)
            if produced:
                changed = True
                out.extend(produced)
            elif len(world.fired) > 0:
                pass
            # We also need to keep running when rules mutate state silently.
        current = len(world.fired)
        if current and not changed:
            # Detect whether a silent rule fired by comparing signatures count.
            # We cannot inspect per-rule mutation directly, so the rule loop above
            # is followed by one more pass only when any new signature appeared.
            pass
        before = getattr(propagate, "_last_fired_count", None)
        propagate._last_fired_count = len(world.fired)  # type: ignore[attr-defined]
        if before is None:
            before = 0
        if len(world.fired) > before:
            changed = True
    if narrate:
        for line in out:
            world.say(line)
    return out


TREATS = {
    "jam_buns": Treat(
        id="jam_buns",
        label="jam buns",
        phrase="a tray of round jam buns with shiny red middles",
        tags={"bread", "jam", "snack"},
    ),
    "cheese_pies": Treat(
        id="cheese_pies",
        label="cheese pies",
        phrase="a plate of tiny cheese pies that smelled buttery and warm",
        tags={"cheese", "pastry", "snack"},
    ),
    "carrot_biscuits": Treat(
        id="carrot_biscuits",
        label="carrot biscuits",
        phrase="a basket of carrot biscuits shaped like crooked moons",
        tags={"carrot", "biscuit", "snack"},
    ),
}

CULPRITS = {
    "goat": CulpritCfg(
        id="goat",
        label="goat",
        phrase="the shaggy supply goat",
        print_word="little hoofprints",
        clue_kind="hoofprints",
        likes={"jam_buns", "carrot_biscuits"},
        reachable={"hayloft", "laundry", "drum_room"},
        tags={"goat", "animal"},
    ),
    "dog": CulpritCfg(
        id="dog",
        label="dog",
        phrase="the garrison's sleepy sled dog",
        print_word="muddy pawprints",
        clue_kind="pawprints",
        likes={"jam_buns", "cheese_pies"},
        reachable={"laundry", "watch_stairs", "drum_room"},
        tags={"dog", "animal"},
    ),
    "goose": CulpritCfg(
        id="goose",
        label="goose",
        phrase="the captain's bossy goose",
        print_word="white feathers",
        clue_kind="feathers",
        likes={"cheese_pies", "carrot_biscuits"},
        reachable={"hayloft", "watch_stairs"},
        tags={"goose", "animal"},
    ),
}

STASHES = {
    "hayloft": Stash(
        id="hayloft",
        label="hayloft",
        phrase="the hayloft above the cart shed",
        image="golden hay poking from the rafters",
        tags={"hayloft"},
    ),
    "laundry": Stash(
        id="laundry",
        label="laundry room",
        phrase="the warm laundry room near the big copper boiler",
        image="sheets hanging like ghostly sails",
        tags={"laundry"},
    ),
    "watch_stairs": Stash(
        id="watch_stairs",
        label="watch stairs",
        phrase="the narrow stairs under the watch tower",
        image="helmets stacked like sleepy metal mushrooms",
        tags={"stairs"},
    ),
    "drum_room": Stash(
        id="drum_room",
        label="drum room",
        phrase="the old drum room behind the west hall",
        image="one huge parade drum leaning against the wall",
        tags={"drum"},
    ),
}

HELPERS = {
    "guard": HelperCfg(
        id="guard",
        label="guard",
        phrase="a round-cheeked guard named Brin",
        helper_type="guard_man",
        skill={"hoofprints", "pawprints"},
        line="Brin squinted at the floor as if the stones might whisper back.",
        tags={"guard"},
    ),
    "cook": HelperCfg(
        id="cook",
        label="cook",
        phrase="a flour-dusted cook named Tessa",
        helper_type="cook_woman",
        skill={"feathers", "pawprints"},
        line="Tessa narrowed her eyes and sniffed the air like a detective in an apron.",
        tags={"cook"},
    ),
    "drummer": HelperCfg(
        id="drummer",
        label="drummer",
        phrase="a cheerful drummer named Nib",
        helper_type="man",
        skill={"hoofprints", "feathers"},
        line="Nib tapped one thoughtful finger on his drumstick and looked delighted by the puzzle.",
        tags={"music"},
    ),
}

GIRL_NAMES = ["Mira", "Nell", "Poppy", "Tansy", "Lila", "Ruth"]
BOY_NAMES = ["Oren", "Kit", "Pax", "Milo", "Rowan", "Toby"]
TRAITS = ["curious", "nosy", "bright", "eager", "merry", "quick-eyed"]


def culprit_likes_treat(culprit: CulpritCfg, treat: Treat) -> bool:
    return treat.id in culprit.likes


def culprit_reaches_stash(culprit: CulpritCfg, stash: Stash) -> bool:
    return stash.id in culprit.reachable


def helper_reads_clue(helper: HelperCfg, culprit: CulpritCfg) -> bool:
    return culprit.clue_kind in helper.skill


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for treat_id, treat in TREATS.items():
        for culprit_id, culprit in CULPRITS.items():
            for stash_id, stash in STASHES.items():
                for helper_id, helper in HELPERS.items():
                    if (
                        culprit_likes_treat(culprit, treat)
                        and culprit_reaches_stash(culprit, stash)
                        and helper_reads_clue(helper, culprit)
                    ):
                        combos.append((treat_id, culprit_id, stash_id, helper_id))
    return sorted(combos)


@dataclass
class StoryParams:
    treat: str
    culprit: str
    stash: str
    helper: str
    child_name: str
    child_gender: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        treat="jam_buns",
        culprit="goat",
        stash="hayloft",
        helper="guard",
        child_name="Mira",
        child_gender="girl",
        trait="curious",
        seed=101,
    ),
    StoryParams(
        treat="cheese_pies",
        culprit="dog",
        stash="laundry",
        helper="cook",
        child_name="Oren",
        child_gender="boy",
        trait="quick-eyed",
        seed=102,
    ),
    StoryParams(
        treat="carrot_biscuits",
        culprit="goose",
        stash="watch_stairs",
        helper="drummer",
        child_name="Poppy",
        child_gender="girl",
        trait="merry",
        seed=103,
    ),
    StoryParams(
        treat="jam_buns",
        culprit="dog",
        stash="drum_room",
        helper="guard",
        child_name="Toby",
        child_gender="boy",
        trait="bright",
        seed=104,
    ),
    StoryParams(
        treat="carrot_biscuits",
        culprit="goat",
        stash="laundry",
        helper="drummer",
        child_name="Nell",
        child_gender="girl",
        trait="eager",
        seed=105,
    ),
]


def explain_rejection(treat: Treat, culprit: CulpritCfg, stash: Stash, helper: HelperCfg) -> str:
    reasons: list[str] = []
    if not culprit_likes_treat(culprit, treat):
        reasons.append(f"{culprit.label} would not plausibly sneak off with {treat.label}")
    if not culprit_reaches_stash(culprit, stash):
        reasons.append(f"{culprit.label} would not plausibly hide in the {stash.label}")
    if not helper_reads_clue(helper, culprit):
        reasons.append(
            f"{helper.label} is not the right helper to read {culprit.clue_kind}"
        )
    if not reasons:
        return "(No story: this combination is outside the world's reasonable set.)"
    return "(No story: " + "; ".join(reasons) + ".)"


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def introduce(world: World, child: Entity, helper: Entity) -> None:
    world.say(
        f"A blizzard pressed its white face against the windows of the old garrison, "
        f"and the wind kept trying all the doors as if it had forgotten the password."
    )
    world.say(
        f"Inside, {child.id}, a {child.traits[0]} little {child.type}, waited by the stove "
        f"with {helper.id}. The whole stone place felt creaky and serious, which only made "
        f"{child.id} want something funny to happen."
    )


def announce_surprise(world: World, child: Entity, cook: Entity, treat: Treat) -> None:
    child.memes["anticipation"] += 1
    world.say(
        f'From the kitchen came the rich smell of {treat.label}. "{child.id}, no peeking," '
        f"{cook.id} called. \"I baked {treat.phrase} for a surprise after the lamps are lit.\""
    )
    world.say(
        f"That one word -- surprise -- bounced around {child.id}'s mind like a rubber ball."
    )


def prepare_mystery(world: World) -> None:
    storm = world.get("storm")
    treat = world.get("treat")
    culprit = world.get("culprit")
    storm.meters["blowing"] = 1.0
    treat.meters["aroma"] = 1.0
    culprit.meters["hungry"] = 1.0
    propagate(world, narrate=False)


def discover_missing(world: World, child: Entity, helper: Entity, treat: Treat) -> None:
    child.memes["surprise"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"When the cook lifted the cloth for a quick check, everyone blinked. One of the "
        f"{treat.label} was missing."
    )
    world.say(
        f'"A blizzard outside, a vanished snack inside," {helper.id} said. '
        f'"That sounds like a mystery with cold feet."'
    )


def inspect_clue(world: World, child: Entity, helper: Entity, culprit: CulpritCfg) -> None:
    clue = world.get("clue")
    clue.meters["noticed"] = 1.0
    child.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"{child.id} crouched beside the kitchen door and found {culprit.print_word} leading away "
        f"from the table."
    )
    world.say(HELPERS[world.facts["helper_cfg"].id].line)
    world.say(
        f'"Then let us follow the evidence," {child.id} whispered, feeling braver now that the '
        f"mystery had something small and silly to hold on to."
    )


def follow_trail(world: World, child: Entity, helper: Entity, stash: Stash, culprit: CulpritCfg) -> None:
    child.meters["steps_taken"] += 1
    world.say(
        f"The trail wound through the hall, past helmets, cloaks, and a snoring chair by the fire, "
        f"until it reached {stash.phrase}."
    )
    world.say(
        f"There they saw {stash.image}, and in the middle of it all came a suspicious little rustle."
    )
    if culprit.id == "goose":
        world.say(
            f'"If that rustle salutes me, I am resigning at once," {helper.id} muttered.'
        )
    elif culprit.id == "goat":
        world.say(
            f'"If that is the captain, he has become remarkably woolly," {helper.id} said.'
        )
    else:
        world.say(
            f'"Either the thief has four paws, or one guard has become very unusual," {helper.id} said.'
        )


def reveal_culprit(world: World, child: Entity, helper: Entity, culprit_ent: Entity, culprit: CulpritCfg, treat: Treat) -> None:
    world.facts["solved"] = True
    world.say(
        f"Behind a crate sat {culprit.phrase}, clutching half of a {treat.label[:-1] if treat.label.endswith('s') else treat.label} "
        f"and looking more embarrassed than dangerous."
    )
    world.say(
        f"{child.id} stared, then laughed. It was not a villain at all -- only a hungry animal with very poor ideas."
    )
    world.say(
        f"The poor {culprit.label} was shivering. The blizzard had frightened it, and the warm smell from the kitchen had seemed like help."
    )
    culprit_ent.memes["caught"] += 1


def comfort_culprit(world: World, helper: Entity, culprit_ent: Entity) -> None:
    helper.meters["offered_warmth"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"{helper.id} wrapped the little thief in an old blanket and rubbed {culprit_ent.pronoun('possessive')} ears."
    )
    world.say(
        f'"Mystery solved," {helper.id} said. "Motive: hunger. Accomplice: weather. Weapon: nose."'
    )


def final_surprise(world: World, child: Entity, cook: Entity, helper: Entity, treat: Treat, culprit: CulpritCfg) -> None:
    child.memes["surprise"] += 1
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    cook.memes["joy"] += 1
    world.say(
        f"When they carried the culprit back to the kitchen, {cook.id} burst out laughing."
    )
    world.say(
        f'"Good thing that rascal only stole one," {cook.id} said, opening the oven. '
        f'Inside waited a second, bigger tray of {treat.label}, hot and shining. '
        f'"That was the real surprise for the night watch."'
    )
    world.say(
        f"Even the old garrison seemed warmer then. Snow still beat at the shutters, but inside "
        f"there were fresh {treat.label}, steam on the windows, and one very sleepy {culprit.label} "
        f"curled by the stove while everyone laughed."
    )


def tell(
    treat_cfg: Treat,
    culprit_cfg: CulpritCfg,
    stash_cfg: Stash,
    helper_cfg: HelperCfg,
    *,
    child_name: str,
    child_gender: str,
    trait: str,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[trait],
    ))
    helper = world.add(Entity(
        id=helper_cfg.phrase.split()[-1],
        kind="character",
        type=helper_cfg.helper_type,
        label=helper_cfg.label,
        phrase=helper_cfg.phrase,
        role="helper",
        tags=set(helper_cfg.tags),
    ))
    cook = world.add(Entity(
        id="Cook",
        kind="character",
        type="cook_woman",
        label="cook",
        phrase="the cook",
        role="cook",
    ))
    storm = world.add(Entity(
        id="storm",
        kind="thing",
        type="blizzard",
        label="blizzard",
        phrase="the blizzard",
        role="storm",
    ))
    treat = world.add(Entity(
        id="treat",
        kind="thing",
        type="treat",
        label=treat_cfg.label,
        phrase=treat_cfg.phrase,
        role="treat",
        tags=set(treat_cfg.tags),
    ))
    culprit = world.add(Entity(
        id="culprit",
        kind="animal",
        type=culprit_cfg.label,
        label=culprit_cfg.label,
        phrase=culprit_cfg.phrase,
        role="culprit",
        tags=set(culprit_cfg.tags),
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=culprit_cfg.print_word,
        phrase=culprit_cfg.print_word,
        role="clue",
    ))
    place = world.add(Entity(
        id="stash",
        kind="place",
        type=stash_cfg.id,
        label=stash_cfg.label,
        phrase=stash_cfg.phrase,
        role="stash",
        tags=set(stash_cfg.tags),
    ))

    world.facts.update(
        child=child,
        helper=helper,
        cook=cook,
        treat_cfg=treat_cfg,
        culprit_cfg=culprit_cfg,
        stash_cfg=stash_cfg,
        helper_cfg=helper_cfg,
        culprit_ent=culprit,
        storm=storm,
        solved=False,
    )

    introduce(world, child, helper)
    announce_surprise(world, child, cook, treat_cfg)

    world.para()
    prepare_mystery(world)
    discover_missing(world, child, helper, treat_cfg)
    inspect_clue(world, child, helper, culprit_cfg)

    world.para()
    follow_trail(world, child, helper, stash_cfg, culprit_cfg)
    reveal_culprit(world, child, helper, culprit, culprit_cfg, treat_cfg)
    comfort_culprit(world, helper, culprit)

    world.para()
    final_surprise(world, child, cook, helper, treat_cfg, culprit_cfg)
    return world


KNOWLEDGE = {
    "blizzard": [
        (
            "What is a blizzard?",
            "A blizzard is a very strong snowstorm with hard wind and blowing snow. It can make it hard to see and very cold outside.",
        )
    ],
    "garrison": [
        (
            "What is a garrison?",
            "A garrison is a place where soldiers or guards live and work. It often has kitchens, stores, sleeping rooms, and watch posts.",
        )
    ],
    "hoofprints": [
        (
            "What are hoofprints?",
            "Hoofprints are marks left on the ground by animals with hard hooves, like goats or horses. They can show where the animal walked.",
        )
    ],
    "pawprints": [
        (
            "What are pawprints?",
            "Pawprints are little marks left by an animal's feet. Dogs and cats can leave pawprints in snow, mud, or dust.",
        )
    ],
    "feathers": [
        (
            "Why can feathers be a clue?",
            "Feathers can fall off a bird or goose as it moves. If you find them in the wrong place, they can help you guess where the bird went.",
        )
    ],
    "goat": [
        (
            "What does a goat like to eat?",
            "A goat likes plants and tasty nibbles, though it should not steal people's snacks. Goats are curious animals and will investigate interesting smells.",
        )
    ],
    "dog": [
        (
            "Why might a dog follow a smell?",
            "Dogs have very strong noses, so a warm food smell can pull them across a room fast. They often find food long before people do.",
        )
    ],
    "goose": [
        (
            "Why can a goose make people laugh?",
            "A goose can honk, flap, and march around in a very bossy way. That makes it funny, especially when it acts as if it owns the place.",
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something you do not understand yet and want to figure out. You solve it by noticing clues and asking careful questions.",
        )
    ],
    "surprise": [
        (
            "What is a surprise?",
            "A surprise is something you did not expect. It can feel exciting because you only find out about it at the special moment.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "blizzard",
    "garrison",
    "mystery",
    "surprise",
    "hoofprints",
    "pawprints",
    "feathers",
    "goat",
    "dog",
    "goose",
]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    treat = world.facts["treat_cfg"]
    culprit = world.facts["culprit_cfg"]
    helper = world.facts["helper_cfg"]
    return [
        (
            f'Write a funny story for a 3-to-5-year-old set in a snowy garrison during a blizzard. '
            f'Use surprise, curiosity, and a mystery to solve.'
        ),
        (
            f"Tell a comedy about {child.id}, a curious child, who notices that one of the "
            f"{treat.label} is missing and follows clues with a {helper.label}."
        ),
        (
            f'Write a gentle mystery where the missing snack thief turns out to be a {culprit.label}, '
            f'and the ending reveals a warm surprise for everyone.'
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    cook = world.facts["cook"]
    treat = world.facts["treat_cfg"]
    culprit = world.facts["culprit_cfg"]
    stash = world.facts["stash_cfg"]
    solved = world.facts.get("solved", False)

    qa: list[tuple[str, str]] = [
        (
            "Where does the story happen?",
            "It happens inside an old garrison during a blizzard. The storm keeps everyone indoors and makes the warm kitchen feel extra cozy.",
        ),
        (
            "What made the child curious?",
            f"{cook.id} promised a surprise, and then one of the {treat.label} went missing. That missing snack turned waiting into a funny little mystery.",
        ),
        (
            "What clue did they find?",
            f"They found {culprit.print_word} leading away from the kitchen. The clue gave them a real trail to follow instead of only guessing.",
        ),
        (
            f"Who helped {child.id} solve the mystery?",
            f"{helper.id} helped. {helper.pronoun('subject').capitalize()} stayed playful and calm, which made the searching feel brave instead of scary.",
        ),
    ]
    if solved:
        qa.extend(
            [
                (
                    "Who took the missing treat, and why?",
                    f"It was {culprit.phrase}. The poor animal was hungry and frightened by the blizzard, so the warm smell from the kitchen pulled it inside.",
                ),
                (
                    f"Where did they find the culprit?",
                    f"They found the culprit in {stash.phrase}. It had hidden there because the place felt sheltered from the wind.",
                ),
                (
                    "What was the surprise at the end?",
                    f"The cook still had a second, bigger tray of {treat.label} waiting in the oven. So the mystery ended with laughter, warm food, and a real surprise after all.",
                ),
            ]
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"blizzard", "garrison", "mystery", "surprise", world.facts["culprit_cfg"].id}
    tags.add(world.facts["culprit_cfg"].clue_kind)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
likes(C, T) :- culprit(C), treat(T), likes_fact(C, T).
reaches(C, S) :- culprit(C), stash(S), reaches_fact(C, S).
reads(H, K) :- helper(H), clue_kind(K), reads_fact(H, K).

valid(T, C, S, H) :- treat(T), culprit(C), stash(S), helper(H),
                     likes(C, T), reaches(C, S), culprit_clue(C, K), reads(H, K).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for treat_id in TREATS:
        lines.append(asp.fact("treat", treat_id))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("culprit_clue", culprit_id, culprit.clue_kind))
        for treat_id in sorted(culprit.likes):
            lines.append(asp.fact("likes_fact", culprit_id, treat_id))
        for stash_id in sorted(culprit.reachable):
            lines.append(asp.fact("reaches_fact", culprit_id, stash_id))
    clue_kinds = sorted({c.clue_kind for c in CULPRITS.values()})
    for clue_kind in clue_kinds:
        lines.append(asp.fact("clue_kind", clue_kind))
    for stash_id in STASHES:
        lines.append(asp.fact("stash", stash_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for skill in sorted(helper.skill):
            lines.append(asp.fact("reads_fact", helper_id, skill))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(77))
        sample = generate(params)
        if not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("generated sample is missing QA/prompts")
        print("OK: default resolve_params() + generate() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a funny little mystery in a blizzard-bound garrison."
    )
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--stash", choices=STASHES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.treat and args.culprit and args.stash and args.helper:
        treat = TREATS[args.treat]
        culprit = CULPRITS[args.culprit]
        stash = STASHES[args.stash]
        helper = HELPERS[args.helper]
        if not (
            culprit_likes_treat(culprit, treat)
            and culprit_reaches_stash(culprit, stash)
            and helper_reads_clue(helper, culprit)
        ):
            raise StoryError(explain_rejection(treat, culprit, stash, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.treat is None or combo[0] == args.treat)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.stash is None or combo[2] == args.stash)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    treat_id, culprit_id, stash_id, helper_id = rng.choice(combos)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    trait = rng.choice(TRAITS)
    return StoryParams(
        treat=treat_id,
        culprit=culprit_id,
        stash=stash_id,
        helper=helper_id,
        child_name=child_name,
        child_gender=child_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.treat not in TREATS:
        raise StoryError(f"(Unknown treat: {params.treat})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.stash not in STASHES:
        raise StoryError(f"(Unknown stash: {params.stash})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    treat = TREATS[params.treat]
    culprit = CULPRITS[params.culprit]
    stash = STASHES[params.stash]
    helper = HELPERS[params.helper]
    if not (
        culprit_likes_treat(culprit, treat)
        and culprit_reaches_stash(culprit, stash)
        and helper_reads_clue(helper, culprit)
    ):
        raise StoryError(explain_rejection(treat, culprit, stash, helper))

    world = tell(
        treat_cfg=treat,
        culprit_cfg=culprit,
        stash_cfg=stash,
        helper_cfg=helper,
        child_name=params.child_name,
        child_gender=params.child_gender,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (treat, culprit, stash, helper) combos:\n")
        for treat_id, culprit_id, stash_id, helper_id in combos:
            print(f"  {treat_id:16} {culprit_id:8} {stash_id:12} {helper_id}")
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
            header = (
                f"### {p.child_name}: {p.culprit} took {p.treat} "
                f"to {p.stash} with {p.helper}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
