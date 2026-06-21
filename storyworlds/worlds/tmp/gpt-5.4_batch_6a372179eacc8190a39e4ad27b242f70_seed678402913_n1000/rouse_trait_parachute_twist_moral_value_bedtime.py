#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rouse_trait_parachute_twist_moral_value_bedtime.py
==============================================================================

A standalone story world for a soft bedtime tale with a little twist:
a child hears a spooky night sound, tries not to rouse a sleeping baby,
and discovers that the sound is only a favorite toy caught high in the room
with its tiny parachute fluttering in the moonlight.

The domain is intentionally small and constraint-checked. The child may be
patient, gentle, thoughtful, or brave; the toy may be caught on different high
places; and the rescue method must be both safe and quiet enough for bedtime.
Unsafe or clumsy plans are rejected with legible errors. The resulting stories
aim for a complete bedtime arc: a calm beginning, a small nighttime worry, a
twist that changes what the child thinks is happening, and an ending image that
proves the room feels safe again.

Run it
------
    python storyworlds/worlds/gpt-5.4/rouse_trait_parachute_twist_moral_value_bedtime.py
    python storyworlds/worlds/gpt-5.4/rouse_trait_parachute_twist_moral_value_bedtime.py --perch curtain_rod --method blanket_catch
    python storyworlds/worlds/gpt-5.4/rouse_trait_parachute_twist_moral_value_bedtime.py --method climb_chair
    python storyworlds/worlds/gpt-5.4/rouse_trait_parachute_twist_moral_value_bedtime.py --all
    python storyworlds/worlds/gpt-5.4/rouse_trait_parachute_twist_moral_value_bedtime.py --qa
    python storyworlds/worlds/gpt-5.4/rouse_trait_parachute_twist_moral_value_bedtime.py --verify
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
SMART_TRAITS = {"patient", "thoughtful"}


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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Perch:
    id: str
    label: str
    the: str
    near: str
    height: int
    swing_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    sense: int
    quiet: int
    max_height: int
    needs_loop: bool
    works_on: set[str]
    body: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SleepWatcher:
    id: str
    label: str
    phrase: str
    room: str
    noise_limit: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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


def _r_flutter(world: World) -> list[str]:
    toy = world.entities.get("toy")
    room = world.entities.get("room")
    hero = world.entities.get("hero")
    if not toy or not room or not hero:
        return []
    if toy.meters["stuck_high"] < THRESHOLD or room.meters["breeze"] < THRESHOLD:
        return []
    sig = ("flutter", toy.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    toy.meters["tapping"] += 1
    hero.memes["worry"] += 1
    return ["__flutter__"]


def _r_reveal(world: World) -> list[str]:
    hero = world.entities.get("hero")
    toy = world.entities.get("toy")
    if not hero or not toy:
        return []
    if hero.meters["identified_source"] < THRESHOLD or toy.meters["tapping"] < THRESHOLD:
        return []
    sig = ("reveal", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] = 0.0
    hero.memes["relief"] += 1
    return ["__reveal__"]


def _r_rescue(world: World) -> list[str]:
    toy = world.entities.get("toy")
    hero = world.entities.get("hero")
    if not toy or not hero:
        return []
    if toy.meters["rescued"] < THRESHOLD:
        return []
    sig = ("rescue", toy.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    toy.meters["stuck_high"] = 0.0
    toy.meters["tapping"] = 0.0
    hero.memes["calm"] += 1
    hero.memes["sleepy"] += 1
    return ["__rescued__"]


CAUSAL_RULES = [
    Rule(name="flutter", tag="physical", apply=_r_flutter),
    Rule(name="reveal", tag="social", apply=_r_reveal),
    Rule(name="rescue", tag="physical", apply=_r_rescue),
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


TOYS = {
    "bunny": Toy(
        id="bunny",
        label="bunny",
        phrase="a soft little bunny with a stitched pink nose",
        tags={"toy", "comfort"},
    ),
    "fox": Toy(
        id="fox",
        label="fox",
        phrase="a small sleepy fox with bright felt ears",
        tags={"toy", "comfort"},
    ),
    "duck": Toy(
        id="duck",
        label="duck",
        phrase="a round yellow duck with a cheerful beak",
        tags={"toy", "comfort"},
    ),
}

PERCHES = {
    "curtain_rod": Perch(
        id="curtain_rod",
        label="curtain rod",
        the="the curtain rod",
        near="beside the moonlit window",
        height=2,
        swing_text="The little parachute kept brushing the glass with a tap-tap sound.",
        tags={"window", "high_place"},
    ),
    "bookshelf_top": Perch(
        id="bookshelf_top",
        label="top of the bookshelf",
        the="the top of the bookshelf",
        near="above the stack of bedtime books",
        height=2,
        swing_text="The parachute strings trembled whenever the night breeze slipped through.",
        tags={"bookshelf", "high_place"},
    ),
    "canopy_hook": Perch(
        id="canopy_hook",
        label="canopy hook",
        the="the canopy hook",
        near="over the bed where the soft cloth canopy hung",
        height=1,
        swing_text="The tiny parachute rustled against the canopy like whispering paper.",
        tags={"bed", "high_place"},
    ),
}

METHODS = {
    "ribbon_pole": Method(
        id="ribbon_pole",
        label="a ribbon-tipped pole",
        sense=3,
        quiet=1,
        max_height=2,
        needs_loop=True,
        works_on={"curtain_rod", "bookshelf_top", "canopy_hook"},
        body="softly hooked the parachute cord with a ribbon-tipped pole and guided the toy down into waiting hands",
        qa_text="used a ribbon-tipped pole to hook the parachute cord and guide the toy down",
        tags={"quiet", "safe_help"},
    ),
    "blanket_catch": Method(
        id="blanket_catch",
        label="a blanket catch",
        sense=2,
        quiet=1,
        max_height=2,
        needs_loop=False,
        works_on={"curtain_rod", "canopy_hook"},
        body="held out a blanket while the grown-up gave the toy the gentlest nudge, and it floated down like a tiny moon cloud",
        qa_text="held out a blanket while the grown-up nudged the toy so it floated down safely",
        tags={"quiet", "safe_help", "blanket"},
    ),
    "climb_chair": Method(
        id="climb_chair",
        label="climbing a chair alone",
        sense=1,
        quiet=2,
        max_height=2,
        needs_loop=False,
        works_on={"curtain_rod", "bookshelf_top", "canopy_hook"},
        body="climbed onto a chair alone to reach for the toy",
        qa_text="climbed onto a chair alone",
        tags={"unsafe"},
    ),
}

SLEEPERS = {
    "baby_sister": SleepWatcher(
        id="baby_sister",
        label="baby sister",
        phrase="her baby sister",
        room="the next room",
        noise_limit=1,
        tags={"baby", "sleep"},
    ),
    "baby_brother": SleepWatcher(
        id="baby_brother",
        label="baby brother",
        phrase="his baby brother",
        room="the next room",
        noise_limit=1,
        tags={"baby", "sleep"},
    ),
    "grandpa": SleepWatcher(
        id="grandpa",
        label="grandpa",
        phrase="grandpa in the little room down the hall",
        room="the little room down the hall",
        noise_limit=1,
        tags={"sleep"},
    ),
}

HERO_TRAITS = ["patient", "gentle", "thoughtful", "brave"]
GIRL_NAMES = ["Lila", "Mina", "Nora", "Tess", "Ivy", "Ella", "Ruby", "Poppy"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Finn", "Leo", "Jude", "Evan", "Noah"]


def method_works(method: Method, perch: Perch, toy: Toy, sleeper: SleepWatcher) -> bool:
    if method.sense < SENSE_MIN:
        return False
    if method.quiet > sleeper.noise_limit:
        return False
    if perch.id not in method.works_on:
        return False
    if perch.height > method.max_height:
        return False
    if method.needs_loop and "toy" not in toy.tags:
        return False
    return True


def sensible_methods() -> list[Method]:
    return [method for method in METHODS.values() if method.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for toy_id, toy in TOYS.items():
        for perch_id, perch in PERCHES.items():
            for sleeper_id, sleeper in SLEEPERS.items():
                for method_id, method in METHODS.items():
                    if method_works(method, perch, toy, sleeper):
                        combos.append((toy_id, perch_id, sleeper_id, method_id))
    return combos


@dataclass
class StoryParams:
    toy: str
    perch: str
    sleeper: str
    method: str
    trait: str
    helper: str
    name: str
    gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        toy="bunny",
        perch="curtain_rod",
        sleeper="baby_sister",
        method="ribbon_pole",
        trait="patient",
        helper="mother",
        name="Lila",
        gender="girl",
    ),
    StoryParams(
        toy="fox",
        perch="bookshelf_top",
        sleeper="grandpa",
        method="ribbon_pole",
        trait="thoughtful",
        helper="father",
        name="Milo",
        gender="boy",
    ),
    StoryParams(
        toy="duck",
        perch="canopy_hook",
        sleeper="baby_brother",
        method="blanket_catch",
        trait="gentle",
        helper="mother",
        name="Nora",
        gender="girl",
    ),
    StoryParams(
        toy="bunny",
        perch="canopy_hook",
        sleeper="baby_brother",
        method="blanket_catch",
        trait="brave",
        helper="grandmother",
        name="Theo",
        gender="boy",
    ),
]


def explain_method_rejection(method: Method) -> str:
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method.id}': it is below the common-sense floor "
        f"(sense={method.sense} < {SENSE_MIN}). A sleepy bedtime rescue should use "
        f"a safer plan. Try: {better}.)"
    )


def explain_combo_rejection(perch: Perch, sleeper: SleepWatcher, method: Method) -> str:
    if method.quiet > sleeper.noise_limit:
        return (
            f"(No story: {method.label} is too noisy for bedtime and would rouse "
            f"{sleeper.phrase} in {sleeper.room}. Pick a quieter rescue.)"
        )
    if perch.id not in method.works_on:
        return (
            f"(No story: {method.label} does not fit a rescue from {perch.the}. "
            f"Choose a method that can really reach that spot.)"
        )
    if perch.height > method.max_height:
        return (
            f"(No story: {perch.the} is too high for {method.label}. The rescue "
            f"must safely reach the toy.)"
        )
    return "(No story: this bedtime rescue does not work.)"


def smart_trait(trait: str) -> bool:
    return trait in SMART_TRAITS


def outcome_of(params: StoryParams) -> str:
    return "self_reveal" if smart_trait(params.trait) else "helper_reveal"


def hero_pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "girl":
        return ("she", "her", "her")
    return ("he", "him", "his")


def bedtime_setup(world: World, hero: Entity, toy_ent: Entity, toy_cfg: Toy) -> None:
    world.say(
        f"At bedtime, {hero.id} was already in soft pajamas, with {toy_cfg.phrase} "
        f"usually tucked near the pillow."
    )
    world.say(
        f"That evening, though, the little {toy_cfg.label} was missing, because "
        f"after supper they had played flying games with its toy parachute."
    )


def discover_sound(world: World, hero: Entity, perch: Perch, sleeper: SleepWatcher) -> None:
    room = world.get("room")
    toy = world.get("toy")
    room.meters["breeze"] += 1
    toy.meters["stuck_high"] += 1
    propagate(world, narrate=False)
    world.say(
        f"As the room grew dim, a soft tap-tap came from {perch.near}. "
        f"{perch.swing_text}"
    )
    world.say(
        f"{hero.id} sat up. {hero.pronoun().capitalize()} did not want to rouse "
        f"{sleeper.phrase} in {sleeper.room}, but the sound made the shadows feel bigger."
    )


def trait_response(world: World, hero: Entity, trait: str) -> None:
    hero.attrs["trait"] = trait
    hero.memes["care"] += 1
    if trait == "patient":
        world.say(
            f"{hero.id}'s best trait was patience. Instead of shouting, "
            f"{hero.pronoun()} listened for the sound again and let the room settle."
        )
    elif trait == "thoughtful":
        world.say(
            f"{hero.id}'s best trait was being thoughtful. {hero.pronoun().capitalize()} "
            f"looked at the window, the books, and the bed, trying to fit the little sound into a true idea."
        )
    elif trait == "gentle":
        world.say(
            f"{hero.id}'s kindest trait was gentleness. {hero.pronoun().capitalize()} "
            f"slipped out from the blanket without thumping the floorboards."
        )
    else:
        world.say(
            f"{hero.id}'s brave trait did not mean pretending not to be scared. "
            f"It meant staying honest about the fear while keeping {hero.pronoun('possessive')} voice small."
        )


def reveal_by_hero(world: World, hero: Entity, toy_cfg: Toy, perch: Perch) -> None:
    hero.meters["identified_source"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the moon moved, and a pale stripe of light reached {perch.the}. "
        f"There was the missing {toy_cfg.label}, dangling by its little parachute."
    )
    world.say(
        f"The spooky tap-tap was not a night creature at all. It was only the parachute brushing and fluttering in the breeze."
    )


def rouse_helper(world: World, hero: Entity, helper: Entity, sleeper: SleepWatcher, trait: str) -> None:
    hero.memes["trust"] += 1
    if trait in SMART_TRAITS:
        world.say(
            f"Even after figuring it out, {hero.id} knew the rescue should not be done alone. "
            f"{hero.pronoun().capitalize()} tiptoed to {helper.label_word} and gave {helper.pronoun('object')} the gentlest rouse."
        )
    else:
        world.say(
            f"At last {hero.id} decided that asking for help was the bravest quiet thing to do. "
            f"{hero.pronoun().capitalize()} padded to {helper.label_word} and gave {helper.pronoun('object')} a tiny rouse."
        )
    world.say(
        f'"Please come softly," {hero.id} whispered. "I do not want to wake {sleeper.phrase}."'
    )


def reveal_by_helper(world: World, hero: Entity, helper: Entity, toy_cfg: Toy, perch: Perch) -> None:
    hero.meters["identified_source"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.label_word.capitalize()} looked up, smiled, and pointed to {perch.the}. "
        f'"There is your {toy_cfg.label}," {helper.pronoun()} whispered. "Only the little parachute is making the sound."'
    )


def rescue_toy(world: World, hero: Entity, helper: Entity, method: Method) -> None:
    toy = world.get("toy")
    toy.meters["rescued"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they {method.body}."
    )
    world.say(
        f"When the toy landed safely, {hero.id} let out the long breath "
        f"{hero.pronoun()} had been holding."
    )


def moral_close(world: World, hero: Entity, helper: Entity, toy_cfg: Toy) -> None:
    hero.memes["loved"] += 1
    world.say(
        f'{helper.label_word.capitalize()} tucked the little {toy_cfg.label} beside the pillow and whispered, '
        f'"A good heart has more than one trait. Tonight you were careful, kind, and wise enough to ask for help."'
    )
    world.say(
        f"{hero.id} folded the tiny parachute flat as a petal and smiled into the blanket."
    )
    world.say(
        f"Soon the room felt small and safe again, and {hero.id} fell asleep with the rescued {toy_cfg.label} warm under {hero.pronoun('possessive')} hand."
    )


def tell(
    toy_cfg: Toy,
    perch: Perch,
    sleeper: SleepWatcher,
    method: Method,
    trait: str,
    helper_type: str,
    hero_name: str,
    hero_gender: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            label=hero_name,
            traits=[trait],
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label="the grown-up",
        )
    )
    room = world.add(
        Entity(
            id="room",
            type="bedroom",
            label="the bedroom",
            role="room",
        )
    )
    toy_ent = world.add(
        Entity(
            id="toy",
            type="toy",
            label=toy_cfg.label,
            phrase=toy_cfg.phrase,
            role="comfort_toy",
            tags=set(toy_cfg.tags),
            attrs={"has_loop": True, "parachute": True},
        )
    )

    bedtime_setup(world, hero, toy_ent, toy_cfg)
    world.para()
    discover_sound(world, hero, perch, sleeper)
    trait_response(world, hero, trait)

    world.para()
    if smart_trait(trait):
        reveal_by_hero(world, hero, toy_cfg, perch)
    rouse_helper(world, hero, helper, sleeper, trait)
    if not smart_trait(trait):
        reveal_by_helper(world, hero, helper, toy_cfg, perch)
    rescue_toy(world, hero, helper, method)

    world.para()
    moral_close(world, hero, helper, toy_cfg)

    world.facts.update(
        hero=hero,
        helper=helper,
        toy_cfg=toy_cfg,
        toy=toy_ent,
        perch=perch,
        sleeper=sleeper,
        method=method,
        trait=trait,
        outcome=outcome_of(
            StoryParams(
                toy=toy_cfg.id,
                perch=perch.id,
                sleeper=sleeper.id,
                method=method.id,
                trait=trait,
                helper=helper_type,
                name=hero_name,
                gender=hero_gender,
            )
        ),
        sound_was_toy=True,
        roused_helper=True,
        moral="Asking for help can be a brave and gentle choice.",
    )
    return world


KNOWLEDGE = {
    "parachute": [
        (
            "What is a parachute?",
            "A parachute is a light cloth canopy that opens wide and helps something fall slowly through the air.",
        )
    ],
    "rouse": [
        (
            "What does rouse mean?",
            "To rouse someone means to wake them up or gently stir them from sleep.",
        )
    ],
    "bedtime": [
        (
            "Why do small sounds seem bigger at bedtime?",
            "At bedtime the room is quieter, so tiny noises stand out more. When you feel sleepy, your imagination can make those sounds seem larger too.",
        )
    ],
    "help": [
        (
            "Why is asking a grown-up for help brave?",
            "It is brave because you tell the truth about what you need instead of making a risky choice alone. Good help keeps everyone safer.",
        )
    ],
    "breeze": [
        (
            "Why would a toy parachute make a tapping sound?",
            "A light parachute can flutter in a breeze and brush against a wall or window. That soft brushing can sound like tapping in a quiet room.",
        )
    ],
    "kindness": [
        (
            "What is a good trait to show at bedtime when someone else is sleeping?",
            "A good trait is gentleness. Gentle people move softly and think about other people's rest and comfort.",
        )
    ],
}
KNOWLEDGE_ORDER = ["parachute", "rouse", "bedtime", "breeze", "help", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    toy_cfg = f["toy_cfg"]
    sleeper = f["sleeper"]
    perch = f["perch"]
    trait = f["trait"]
    return [
        'Write a bedtime story for a 3-to-5-year-old that includes the words "rouse", "trait", and "parachute".',
        f"Tell a soft nighttime story where {hero.id} hears a spooky sound, tries not to rouse {sleeper.phrase}, and learns that the sound comes from a toy with a parachute stuck on {perch.the}.",
        f"Write a gentle twist story in which a child's best trait is {trait}, the fear turns out to be harmless, and the ending teaches that asking for help can be wise.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    toy_cfg = f["toy_cfg"]
    perch = f["perch"]
    sleeper = f["sleeper"]
    method = f["method"]
    trait = f["trait"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child getting ready for sleep, and a quiet grown-up helper. The story also centers on a favorite {toy_cfg.label} with a little parachute.",
        ),
        (
            "What problem began the story?",
            f"A soft tap-tap sound came from {perch.near}, and {hero.id} did not know what was making it. The sound felt spooky because the room was dark and {hero.pronoun()} was trying not to rouse {sleeper.phrase}.",
        ),
        (
            f"What trait helped {hero.id} at bedtime?",
            f"{hero.id}'s helpful trait was {trait}. That trait shaped the next step, because {hero.pronoun()} stayed quiet and careful instead of making the room noisier or riskier.",
        ),
    ]
    if outcome == "self_reveal":
        qa.append(
            (
                "What was the twist in the story?",
                f"The sound was not something scary at all. It was the missing {toy_cfg.label}, with its little parachute fluttering against {perch.the} in the breeze.",
            )
        )
    else:
        qa.append(
            (
                f"Why did {hero.id} rouse {helper.label_word}?",
                f"{hero.id} was still unsure what the sound meant and knew a bedtime rescue should not be done alone. Rousing {helper.label_word} softly was safer than climbing or grabbing in the dark.",
            )
        )
        qa.append(
            (
                "What was the twist in the story?",
                f"When the grown-up looked up, the mystery turned out to be harmless. The tapping came from the toy's parachute, not from anything frightening in the room.",
            )
        )
    qa.append(
        (
            f"How did they get the toy down?",
            f"They {method.qa_text}. That method worked because it reached {perch.the} safely and stayed quiet enough for bedtime.",
        )
    )
    qa.append(
        (
            "What is the moral value in the ending?",
            "The ending teaches that bravery is not the same as doing everything alone. Asking for help quietly and kindly can be the wisest choice.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"parachute", "rouse", "bedtime", "help", "kindness", "breeze"}
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% method works when it is sensible, quiet enough, reaches the perch,
% and is listed as suitable for that perch.
sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
quiet_ok(Slp, M) :- sleeper(Slp), method(M), noise_limit(Slp, N), quiet(M, Q), Q <= N.
height_ok(P, M) :- perch(P), method(M), height(P, H), max_height(M, MH), H =< MH.
works(P, M) :- usable_on(M, P).
valid(T, P, S, M) :- toy(T), perch(P), sleeper(S), method(M),
                     sensible(M), quiet_ok(S, M), height_ok(P, M), works(P, M).

smart(patient).
smart(thoughtful).
outcome(self_reveal) :- trait(T), smart(T).
outcome(helper_reveal) :- trait(T), not smart(T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for toy_id in TOYS:
        lines.append(asp.fact("toy", toy_id))
    for perch_id, perch in PERCHES.items():
        lines.append(asp.fact("perch", perch_id))
        lines.append(asp.fact("height", perch_id, perch.height))
    for sleeper_id, sleeper in SLEEPERS.items():
        lines.append(asp.fact("sleeper", sleeper_id))
        lines.append(asp.fact("noise_limit", sleeper_id, sleeper.noise_limit))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("quiet", method_id, method.quiet))
        lines.append(asp.fact("max_height", method_id, method.max_height))
        for perch_id in sorted(method.works_on):
            lines.append(asp.fact("usable_on", method_id, perch_id))
    for trait in HERO_TRAITS:
        lines.append(asp.fact("trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(trait: str) -> str:
    import asp

    model = asp.one_model(asp_program(asp.fact("trait", trait), "#show outcome/1."))
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

    bad = 0
    for trait in HERO_TRAITS:
        if asp_outcome(trait) != ("self_reveal" if smart_trait(trait) else "helper_reveal"):
            bad += 1
    if bad == 0:
        print("OK: outcome model matches trait logic.")
    else:
        rc = 1
        print(f"MISMATCH: {bad} trait outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - explicit verify guard
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: a child hears a night sound, tries not to rouse a sleeper, and rescues a toy parachute quietly."
    )
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--sleeper", choices=SLEEPERS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--trait", choices=HERO_TRAITS)
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(METHODS[args.method]))

    if args.perch and args.sleeper and args.method:
        perch = PERCHES[args.perch]
        sleeper = SLEEPERS[args.sleeper]
        method = METHODS[args.method]
        toy = TOYS[args.toy] if args.toy else next(iter(TOYS.values()))
        if not method_works(method, perch, toy, sleeper):
            raise StoryError(explain_combo_rejection(perch, sleeper, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.toy is None or combo[0] == args.toy)
        and (args.perch is None or combo[1] == args.perch)
        and (args.sleeper is None or combo[2] == args.sleeper)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    toy_id, perch_id, sleeper_id, method_id = rng.choice(sorted(combos))
    trait = args.trait or rng.choice(HERO_TRAITS)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])
    return StoryParams(
        toy=toy_id,
        perch=perch_id,
        sleeper=sleeper_id,
        method=method_id,
        trait=trait,
        helper=helper,
        name=name,
        gender=gender,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        toy_cfg = TOYS[params.toy]
        perch = PERCHES[params.perch]
        sleeper = SLEEPERS[params.sleeper]
        method = METHODS[params.method]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from err

    if params.trait not in HERO_TRAITS:
        raise StoryError(f"(Invalid trait: {params.trait})")
    if params.helper not in {"mother", "father", "grandmother", "grandfather"}:
        raise StoryError(f"(Invalid helper: {params.helper})")
    if method.sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(method))
    if not method_works(method, perch, toy_cfg, sleeper):
        raise StoryError(explain_combo_rejection(perch, sleeper, method))

    world = tell(
        toy_cfg=toy_cfg,
        perch=perch,
        sleeper=sleeper,
        method=method,
        trait=params.trait,
        helper_type=params.helper,
        hero_name=params.name,
        hero_gender=params.gender,
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
        print(f"{len(combos)} compatible (toy, perch, sleeper, method) combos:\n")
        for toy_id, perch_id, sleeper_id, method_id in combos:
            print(f"  {toy_id:6} {perch_id:14} {sleeper_id:12} {method_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.name}: {p.toy} on {p.perch} ({p.trait}, {p.method})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
