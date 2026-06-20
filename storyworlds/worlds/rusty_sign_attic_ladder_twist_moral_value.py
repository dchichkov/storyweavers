#!/usr/bin/env python3
"""
storyworlds/worlds/rusty_sign_attic_ladder_twist_moral_value.py
================================================================

A standalone storyworld for a child-facing space adventure set on an attic
ladder above a repair bay. A young cadet follows a rumor of space treasure,
finds a rusty sign that works as a real physical clue, faces a tempting bad
shortcut, and discovers a twist where the true treasure is something useful
that protects or helps other people.
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
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def reflexive(self) -> str:
        if self.type == "girl":
            return "herself"
        if self.type == "boy":
            return "himself"
        return "themself"


@dataclass
class AtticBay:
    id: str
    name: str
    ladder: str
    rafters: str
    below_sound: str
    final_image: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class RustySign:
    id: str
    object: str
    mark: str
    message: str
    study: str
    key: str
    hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Shortcut:
    id: str
    label: str
    temptation: str
    thought: str
    refuse: str
    required: str
    lure: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Twist:
    id: str
    apparent: str
    truth: str
    key: str
    reveal: str
    payoff: str
    lesson: str
    outcome: str
    owner: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    attic: str
    sign: str
    shortcut: str
    twist: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    captain: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, attic: AtticBay) -> None:
        self.attic = attic
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.attic)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_read_sign(world: World) -> list[str]:
    hero = world.get("hero")
    sign = world.get("sign")
    sig = ("read_sign", sign.id)
    if sign.meters["studied"] >= THRESHOLD and sig not in world.fired:
        world.fired.add(sig)
        hero.memes["insight"] += 1
    return []


def _r_notice_risk(world: World) -> list[str]:
    hero = world.get("hero")
    ladder = world.get("ladder")
    shortcut = world.get("shortcut")
    sig = ("risk", ladder.id)
    if ladder.meters["wobble"] >= THRESHOLD and shortcut.meters["noticed"] >= THRESHOLD:
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["caution"] += 1
            hero.memes["temptation"] += shortcut.meters["lure"]
    return []


def _r_accept_help(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    ladder = world.get("ladder")
    sig = ("help", hero.id)
    if hero.memes["choose_help"] >= THRESHOLD and hero.memes["insight"] >= THRESHOLD:
        if sig not in world.fired:
            world.fired.add(sig)
            ladder.meters["steady"] += 1
            helper.memes["trust"] += 1
            hero.memes["wisdom"] += 1
            hero.memes["temptation"] = max(0.0, hero.memes["temptation"] - 1.0)
    return []


def _r_reveal_truth(world: World) -> list[str]:
    hero = world.get("hero")
    ladder = world.get("ladder")
    cache = world.get("cache")
    sig = ("truth", cache.id)
    if ladder.meters["steady"] >= THRESHOLD and hero.memes["insight"] >= THRESHOLD:
        if sig not in world.fired:
            world.fired.add(sig)
            cache.meters["revealed"] += 1
            hero.memes["lesson"] += 1
            hero.memes["wonder"] += 1
    return []


CAUSAL_RULES = [
    Rule("read_sign", "physical", _r_read_sign),
    Rule("risk", "turn", _r_notice_risk),
    Rule("help", "social", _r_accept_help),
    Rule("truth", "twist", _r_reveal_truth),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        before = len(world.fired)
        for rule in CAUSAL_RULES:
            for sentence in rule.apply(world):
                world.say(sentence)
        changed = len(world.fired) != before


def sign_fits_attic(attic: AtticBay, sign: RustySign) -> bool:
    return sign.key in attic.supports


def sign_solves_twist(sign: RustySign, twist: Twist) -> bool:
    return sign.key == twist.key


def shortcut_is_bad_idea(shortcut: Shortcut) -> bool:
    return shortcut.required in {"rush", "yank", "hide"} and shortcut.lure >= 2


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for attic_id, attic in ATTICS.items():
        for sign_id, sign in SIGNS.items():
            if not sign_fits_attic(attic, sign):
                continue
            for shortcut_id, shortcut in SHORTCUTS.items():
                if not shortcut_is_bad_idea(shortcut):
                    continue
                for twist_id, twist in TWISTS.items():
                    if sign_solves_twist(sign, twist):
                        combos.append((attic_id, sign_id, shortcut_id, twist_id))
    return sorted(combos)


def outcome_of(params: StoryParams) -> str:
    return TWISTS[params.twist].outcome


def ensure_period(text: str) -> str:
    if text.endswith((".", "!", "?")):
        return text
    return text + "."


def explain_rejection(attic: AtticBay, sign: RustySign,
                      shortcut: Shortcut, twist: Twist) -> str:
    if not sign_fits_attic(attic, sign):
        return (
            f"(No story: {attic.name} does not physically support {sign.object}. "
            f"The rusty sign needs the right beam, draft, light, or magnet to mean anything here.)"
        )
    if not sign_solves_twist(sign, twist):
        return (
            f"(No story: {sign.object} points by {sign.key}, but this twist needs {twist.key}. "
            f"The rusty sign must truly unlock the space-attic mystery.)"
        )
    if not shortcut_is_bad_idea(shortcut):
        return (
            f"(No story: {shortcut.label} is not a tempting bad idea, so the moral turn would be weak.)"
        )
    return "(No story: this combination falls outside the attic-ladder space-adventure world.)"


def predict_bad_shortcut(world: World, shortcut: Shortcut) -> dict:
    sim = world.copy()
    ladder = sim.get("ladder")
    hero = sim.get("hero")
    shortcut_ent = sim.get("shortcut")
    shortcut_ent.meters["noticed"] += 1
    shortcut_ent.meters["lure"] = float(shortcut.lure)
    propagate(sim)
    ladder.meters["sway_if_rushed"] += 1
    hero.memes["would_brag"] += 1
    return {
        "ladder_sways": ladder.meters["sway_if_rushed"] >= THRESHOLD,
        "would_brag": hero.memes["would_brag"] >= THRESHOLD,
        "required": shortcut.required,
    }


def introduce(world: World, hero: Entity, helper: Entity, attic: AtticBay) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["friendship"] += 1
    captain = world.get("captain")
    world.say(
        f"Once upon a time, {hero.id} was the youngest cadet on Captain {captain.id}'s little star crew."
    )
    world.say(
        f"One blue evening, {hero.pronoun()} climbed the {attic.ladder} into {attic.name}, "
        f"where {attic.rafters}."
    )
    world.say(
        f"Below the hatch, {attic.below_sound}, and {helper.id} waited with both hands near the ladder "
        f"in case the attic ladder shook."
    )


def rumor_and_sign(world: World, hero: Entity, sign: RustySign, twist: Twist) -> None:
    cache = world.get("cache")
    sign_ent = world.get("sign")
    sign_ent.meters["found"] += 1
    world.say(
        f"The ship children had been whispering about {twist.apparent}. Everyone said the prize was tucked above the repair bay."
    )
    world.say(
        f"Near the upper rung, {hero.id} found {sign.object}. It was a rusty sign with {sign.mark}."
    )
    world.say(f'The sign seemed to say, "{sign.message}"')
    cache.meters["rumored"] += 1


def study_sign(world: World, hero: Entity, sign: RustySign) -> None:
    sign_ent = world.get("sign")
    sign_ent.meters["studied"] += 1
    world.say(
        f"{hero.id} did not grab at the first shiny dream. {hero.pronoun('subject').capitalize()} held still on the rung and studied the rusty sign: {sign.study}."
    )
    world.say(
        f'"If the sign is honest," {hero.pronoun()} thought, "then it is pointing with {sign.hint}, not with a braggy guess."'
    )
    propagate(world)


def tempt_shortcut(world: World, hero: Entity, shortcut: Shortcut) -> None:
    ladder = world.get("ladder")
    shortcut_ent = world.get("shortcut")
    shortcut_ent.meters["noticed"] += 1
    shortcut_ent.meters["lure"] = float(shortcut.lure)
    world.facts["bad_shortcut_prediction"] = predict_bad_shortcut(world, shortcut)
    world.say(f"Then the bad idea slid into the story: {shortcut.temptation}.")
    world.say(
        f'{shortcut.thought} {hero.id} thought. The attic ladder gave a tiny space-creak under one boot.'
    )
    ladder.meters["wobble"] += 1
    propagate(world)


def choose_wisely(world: World, hero: Entity, helper: Entity, shortcut: Shortcut) -> None:
    hero.memes["choose_help"] += 1
    world.say(
        f'"No," {hero.pronoun()} whispered to {hero.reflexive()}. "A real space explorer does not win by {shortcut.label}."'
    )
    world.say(
        f'{shortcut.refuse} "{helper.id}, hold the ladder while I follow the clue," {hero.id} called.'
    )
    propagate(world)
    world.say(
        f"{helper.id} planted both feet, gripped the rails, and said, "
        f"\"Slow hands, bright eyes. We do this together.\""
    )


def reveal_twist(world: World, hero: Entity, twist: Twist) -> None:
    cache = world.get("cache")
    if cache.meters["revealed"] < THRESHOLD:
        propagate(world)
    world.say(
        f"With the ladder steady and the clue clear, {hero.id} reached behind the crate near the beam. {twist.reveal}"
    )
    world.say(
        f"That was the twist: {twist.truth}. {hero.id} blinked, and then {hero.pronoun('possessive')} grin turned gentle instead of grabby."
    )


def ending(world: World, hero: Entity, twist: Twist) -> None:
    captain = world.get("captain")
    world.say(
        f"{ensure_period(twist.payoff)} Captain {captain.id} looked up from the deck below, as proud as if a whole moon chest had been found."
    )
    world.say(
        f"{hero.id} learned something brighter than treasure talk: {twist.lesson}"
    )
    world.say(
        f"By starlight, {world.attic.final_image}, and the rusty sign rested above the safe attic ladder like a little metal star."
    )


def tell(attic: AtticBay, sign: RustySign, shortcut: Shortcut, twist: Twist,
         hero_name: str = "Nova", hero_gender: str = "girl",
         helper_name: str = "Jax", helper_gender: str = "boy",
         captain: str = "Sol", trait: str = "careful") -> World:
    world = World(attic)
    hero = world.add(Entity(
        "hero", kind="character", type=hero_gender, label=hero_name,
        role="hero", traits=[trait, "young"],
    ))
    hero.id = hero_name
    helper = world.add(Entity(
        "helper", kind="character", type=helper_gender, label=helper_name,
        role="helper", traits=["steady", "kind"],
    ))
    helper.id = helper_name
    world.add(Entity(
        "captain", kind="character", type="captain", label=captain,
        role="captain", traits=["wise", "calm"],
    )).id = captain
    world.add(Entity(
        "ladder", type="attic ladder", label=attic.ladder,
        attrs={"supports": sorted(attic.supports)},
    ))
    world.add(Entity(
        "sign", type="rusty sign", label=sign.object,
        attrs={"key": sign.key},
    ))
    world.add(Entity(
        "shortcut", type="temptation", label=shortcut.label,
        attrs={"required": shortcut.required},
    ))
    world.add(Entity(
        "cache", type="cache", label=twist.apparent, owner=twist.owner,
        attrs={"key": twist.key, "outcome": twist.outcome},
    ))

    introduce(world, hero, helper, attic)
    rumor_and_sign(world, hero, sign, twist)

    world.para()
    study_sign(world, hero, sign)
    tempt_shortcut(world, hero, shortcut)
    choose_wisely(world, hero, helper, shortcut)

    world.para()
    reveal_twist(world, hero, twist)
    ending(world, hero, twist)

    world.facts.update(
        hero=hero,
        helper=helper,
        attic=attic,
        sign=sign,
        shortcut=shortcut,
        twist=twist,
        ladder=world.get("ladder"),
        cache=world.get("cache"),
        captain=captain,
        outcome=twist.outcome,
    )
    return world


ATTICS = {
    "launch_loft": AtticBay(
        "launch_loft",
        "the launch loft above Dock Seven",
        "aluminum attic ladder with blue grip tape",
        "packed parachute cloth, toy rockets, and silver ducts crossed the rafters",
        "engines purred below like sleepy lions of light",
        "fresh hull patches gleamed beside the hatch",
        supports={"arrow", "light", "magnet"},
        tags={"attic", "ladder", "space", "repair"},
    ),
    "observatory_nook": AtticBay(
        "observatory_nook",
        "the observatory nook over the moon garage",
        "thin attic ladder under a round skylight",
        "coils of cable, a tiny telescope, and folded glider wings made striped shadows",
        "the launch field hummed and blinked below",
        "the skylight laid a bright path over the ladder rungs",
        supports={"shadow", "light", "arrow"},
        tags={"attic", "ladder", "space", "stars"},
    ),
    "comet_storage": AtticBay(
        "comet_storage",
        "the comet-storage attic above the tool room",
        "creaking attic ladder with copper rails",
        "old helmets swung from hooks and soft dust sparkled like tiny planets",
        "repair carts clicked over the metal floor below",
        "a new bell and neat bolts shone near the safe hatch",
        supports={"magnet", "shadow", "arrow"},
        tags={"attic", "ladder", "space", "tools"},
    ),
}


SIGNS = {
    "arrow_sign": RustySign(
        "arrow_sign",
        "a bent rusty sign nailed beside a beam",
        "a faded red arrow and two screw holes",
        "Follow the arrow that still tells the truth.",
        "the old arrow lined up only when one rung and one beam made a straight path toward a tucked box",
        "arrow",
        "the straight arrow line",
        tags={"sign", "arrow", "metal"},
    ),
    "star_hole_sign": RustySign(
        "star_hole_sign",
        "a rusty sign punched with tiny star holes",
        "five little light dots around a scratched circle",
        "When light wakes stars, look where they land.",
        "the starlike holes made bright dots only when the skylight hit the right corner above the ladder",
        "light",
        "the star-dots made by light",
        tags={"sign", "light", "stars"},
    ),
    "magnet_strip_sign": RustySign(
        "magnet_strip_sign",
        "a rusty sign with a silver strip bolted along one edge",
        "a magnet strip and a tiny painted moon",
        "Metal remembers where careful hands should look.",
        "the strip tugged softly toward a hidden metal case when the sign was held near the beam",
        "magnet",
        "the gentle magnetic pull",
        tags={"sign", "magnet", "metal"},
    ),
    "shadow_ring_sign": RustySign(
        "shadow_ring_sign",
        "a round rusty sign cut with a moon-ring in its middle",
        "a hollow ring and a dark blue edge",
        "Trust the shadow that arrives on time.",
        "the ring only framed the right mark when the skylight made a round shadow on the beam beside the attic ladder",
        "shadow",
        "the moon-ring shadow",
        tags={"sign", "shadow", "moon"},
    ),
}


SHORTCUTS = {
    "jump_rung": Shortcut(
        "jump_rung",
        "jumping from the third rung to the beam",
        "the hidden box looked close enough for one fast leap",
        '"If I spring now, I can grab it before anyone even blinks,"',
        "So both boots stayed on the ladder instead of on the boast.",
        "rush",
        4,
        tags={"risk", "hurry", "space"},
    ),
    "yank_cable": Shortcut(
        "yank_cable",
        "yanking a loose service cable to drag the box closer",
        "a dangling cable looked like a quick answer from a machine",
        '"If I yank that cable, the treasure will swing right to me,"',
        "The cable stayed quiet, and no one let the loft shake harder.",
        "yank",
        3,
        tags={"risk", "cable", "space"},
    ),
    "pocket_sign": Shortcut(
        "pocket_sign",
        "pocketing the clue and finishing the climb alone",
        "for one hot second, keeping the secret felt shiny and important",
        '"If I hide the clue, the great find will belong only to me,"',
        "The clue stayed where both children could read it, because lonely pride makes a weak captain.",
        "hide",
        3,
        tags={"secret", "pride", "space"},
    ),
    "steady_wait": Shortcut(
        "steady_wait",
        "waiting quietly on the rung",
        "the wise choice was already there",
        '"If I wait, I can understand the clue first,"',
        "They waited together.",
        "wait",
        1,
        tags={"patience"},
    ),
}


TWISTS = {
    "patch_case": Twist(
        "patch_case",
        "moon coins from an old captain's chest",
        "the box held silver patch squares and seal foam for fixing tiny leaks before the next launch",
        "arrow",
        "The arrow led to a flat tin behind the beam. Inside were seal patches, foam strips, and a note that said, FOR SMALL LEAKS BEFORE BIG TROUBLES.",
        "Together the children passed the patch case down, and before bedtime the crew sealed every hissing toy shuttle and loose vent flap",
        "Useful treasure can protect more people than shiny treasure. A brave cadet helps repair the world instead of bragging over it.",
        "repair",
        "the launch crew",
        tags={"lesson", "repair", "sharing"},
    ),
    "beacon_bell": Twist(
        "beacon_bell",
        "a comet crystal for the captain's collar",
        "the box held a hand beacon and a bell-switch meant for calling help any time the ladder swayed",
        "light",
        "The star dots landed on a small latch. Inside the box rested a hand beacon, a bell-switch, and a bright card that read, CALL EARLY, CLIMB SAFELY.",
        "The beacon was hung beside the hatch so no child had to pretend to be fine on a shaky climb again",
        "Asking for help does not shrink an adventure. It makes the adventure safe enough to share.",
        "help",
        "the loft crew",
        tags={"lesson", "help", "safety"},
    ),
    "bolt_case": Twist(
        "bolt_case",
        "a meteor medal hidden for the cleverest cadet",
        "the box held magnetic bolts for the attic ladder hatch and a tiny wrench for tightening the rails",
        "magnet",
        "The sign tugged toward a tucked case under the beam. Inside lay magnetic bolts, a child-sized wrench, and a card saying that high places stay brave only when they stay tight.",
        "By supper, the loose hatch and the singing rail had both been tightened",
        "Real courage cares whether the next climber is safe. The best prize is the one that keeps everyone steady.",
        "tighten",
        "everyone who climbs",
        tags={"lesson", "repair", "metal"},
    ),
    "shadow_chart": Twist(
        "shadow_chart",
        "a secret map to starsilver on the roof",
        "the box held a shadow chart showing the safe climbing hour and the unsafe blind hour for the loft",
        "shadow",
        "The moon-ring shadow framed a narrow box. Inside was no starsilver at all, only a careful shadow chart with bright marks for safe time and dark marks for the blind time.",
        "The chart was pinned beside the hatch so younger children could see when to climb and when to wait",
        "Knowledge becomes a treasure when it is shared clearly. Wise explorers leave signs that help the next person choose well.",
        "knowledge",
        "the younger dock children",
        tags={"lesson", "knowledge", "sharing"},
    ),
}


GIRL_NAMES = ["Nova", "Lina", "Mira", "Tess", "Poppy", "Rhea", "Zuri", "Ivy"]
BOY_NAMES = ["Jax", "Milo", "Orin", "Theo", "Nico", "Bram", "Eli", "Finn"]
TRAITS = ["careful", "bright", "curious", "steady", "brave", "kind"]
CAPTAINS = ["Sol", "Vega", "Comet", "Lyra"]

CURATED = [
    StoryParams("launch_loft", "arrow_sign", "jump_rung", "patch_case",
                "Nova", "girl", "Jax", "boy", "Sol", "careful"),
    StoryParams("observatory_nook", "star_hole_sign", "pocket_sign", "beacon_bell",
                "Milo", "boy", "Mira", "girl", "Vega", "bright"),
    StoryParams("comet_storage", "magnet_strip_sign", "yank_cable", "bolt_case",
                "Lina", "girl", "Theo", "boy", "Comet", "kind"),
    StoryParams("observatory_nook", "shadow_ring_sign", "jump_rung", "shadow_chart",
                "Finn", "boy", "Rhea", "girl", "Lyra", "curious"),
]


KNOWLEDGE = {
    "sign": [(
        "Why can an old sign still matter?",
        "An old sign can still carry useful information if someone studies it carefully. Rust may make it ugly, but it does not always erase the truth it points to."
    )],
    "attic": [(
        "What is an attic?",
        "An attic is a space high under a roof where things are stored. It often has beams, dust, and narrow ways to climb."
    )],
    "ladder": [(
        "Why should a child be careful on an attic ladder?",
        "A ladder can wobble, squeak, or have a weak part. Slow climbing and help from another person make high places safer."
    )],
    "space": [(
        "What makes this feel like a space adventure?",
        "The story has a star crew, a launch bay, repair gear, and sky-colored language. Even the lesson happens inside a world of ladders, hatches, and space tools."
    )],
    "light": [(
        "How can light help solve a clue?",
        "Light can shine through holes, draw a shape, or mark one special spot. Watching where light lands can turn a plain object into a clear clue."
    )],
    "magnet": [(
        "What does a magnet do?",
        "A magnet pulls certain metal things toward it. In a story, that pull can reveal where a hidden metal object is waiting."
    )],
    "shadow": [(
        "How can a shadow help someone?",
        "A shadow can mark a place or the right time to do something. A careful child can use a shadow like a quiet pointer."
    )],
    "lesson": [(
        "What is a moral value in a story?",
        "A moral value is a good idea the character learns to live by, such as sharing, honesty, or helping. It matters because the character acts differently after learning it."
    )],
}
KNOWLEDGE_ORDER = ["sign", "attic", "ladder", "space", "light", "magnet",
                   "shadow", "lesson"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, attic, sign, shortcut, twist = (
        f["hero"], f["attic"], f["sign"], f["shortcut"], f["twist"]
    )
    return [
        'Write a TinyStories-style space adventure set on an attic ladder that includes the words "rusty sign", a twist, and a moral value.',
        f"Tell a child-facing story about {hero.id} in {attic.name}, where {sign.object} becomes a clue, {shortcut.label} looks tempting, and the treasure rumor turns into something useful.",
        f"Write a complete attic-ladder space adventure with a clear beginning, a risky middle turn, and an ending image that proves the lesson changed the place.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, attic, sign, shortcut, twist = (
        f["hero"], f["helper"], f["attic"], f["sign"], f["shortcut"], f["twist"]
    )
    return [
        (
            "Who is the story about?",
            f"It is about {hero.id}, the youngest cadet on a little star crew. {hero.pronoun('subject').capitalize()} climbs into {attic.name} on the attic ladder."
        ),
        (
            f"What clue did {hero.id} find?",
            f"{hero.id} found {sign.object}. It mattered because {sign.hint} showed how to read the loft carefully instead of guessing."
        ),
        (
            f"What bad idea tempted {hero.id}?",
            f"{hero.id} was tempted by {shortcut.label}. It looked fast, but it would have put hurry or pride ahead of safety."
        ),
        (
            f"How did {helper.id} help during the climb?",
            f"{helper.id} held the ladder rails steady while {hero.id} followed the clue. That help mattered because the ladder had already warned them with a shaky creak."
        ),
        (
            "What was the twist?",
            f"The twist was that the rumored prize was not the true treasure at all. The children had whispered about {twist.apparent}, but instead, {twist.truth}."
        ),
        (
            "What moral value did the child learn?",
            f"{hero.id} learned this moral value: {twist.lesson} The lesson became real because the treasure was used to help other people instead of making one child feel important."
        ),
        (
            "How did the story end?",
            f"It ended with the attic ladder area safer or wiser than before. The final picture shows that the adventure changed the world, not only {hero.id}'s thoughts."
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["attic"].tags) | set(f["sign"].tags) | set(f["shortcut"].tags)
    tags |= set(f["twist"].tags)
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
    seen: set[int] = set()
    for ent in world.entities.values():
        if id(ent) in seen:
            continue
        seen.add(id(ent))
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
solves(Sign, Twist) :- sign_key(Sign, Key), twist_key(Twist, Key).

bad_shortcut(S) :- requires(S, rush).
bad_shortcut(S) :- requires(S, yank).
bad_shortcut(S) :- requires(S, hide).
tempting(S) :- shortcut_lure(S, L), L >= 2.

valid(Attic, Sign, Shortcut, Twist) :-
    attic(Attic), supports(Attic, Key), sign_key(Sign, Key),
    solves(Sign, Twist), bad_shortcut(Shortcut), tempting(Shortcut).

outcome(O) :- chosen_twist(T), twist_outcome(T, O).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for attic_id, attic in ATTICS.items():
        lines.append(asp.fact("attic", attic_id))
        for support in sorted(attic.supports):
            lines.append(asp.fact("supports", attic_id, support))
    for sign_id, sign in SIGNS.items():
        lines.append(asp.fact("sign", sign_id))
        lines.append(asp.fact("sign_key", sign_id, sign.key))
    for shortcut_id, shortcut in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", shortcut_id))
        lines.append(asp.fact("requires", shortcut_id, shortcut.required))
        lines.append(asp.fact("shortcut_lure", shortcut_id, shortcut.lure))
    for twist_id, twist in TWISTS.items():
        lines.append(asp.fact("twist", twist_id))
        lines.append(asp.fact("twist_key", twist_id, twist.key))
        lines.append(asp.fact("twist_outcome", twist_id, twist.outcome))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([asp.fact("chosen_twist", params.twist)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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
    empty = build_parser().parse_args([])
    for seed in range(200):
        try:
            cases.append(resolve_params(empty, random.Random(seed)))
        except StoryError:
            continue
    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")
        for params in bad[:5]:
            print(" ", params, asp_outcome(params), outcome_of(params))

    for params in CURATED:
        sample = generate(params)
        story_lower = sample.story.lower()
        if "rusty sign" not in story_lower:
            rc = 1
            print(f"MISMATCH: missing required seed words in story for {params}.")
        if "attic ladder" not in story_lower:
            rc = 1
            print(f"MISMATCH: missing setting phrase in story for {params}.")
    if rc == 0:
        print(f"OK: generated curated stories keep the seed words and attic ladder setting ({len(CURATED)} cases).")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a space attic ladder, a rusty sign clue, "
                    "a dangerous shortcut, and a useful twist."
    )
    ap.add_argument("--attic", choices=ATTICS)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=CAPTAINS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP twin against Python logic")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the ASP facts and rules")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random,
                   index: int = 0) -> StoryParams:
    _ = index
    attic_id = args.attic or rng.choice(sorted(ATTICS))
    attic = ATTICS[attic_id]

    valid_signs = [sid for sid, sign in SIGNS.items() if sign_fits_attic(attic, sign)]
    if args.sign is not None and args.sign not in valid_signs:
        raise StoryError(explain_rejection(
            attic,
            SIGNS[args.sign],
            SHORTCUTS.get(args.shortcut or "jump_rung", SHORTCUTS["jump_rung"]),
            TWISTS.get(args.twist or "patch_case", TWISTS["patch_case"]),
        ))
    sign_id = args.sign or rng.choice(sorted(valid_signs))
    sign = SIGNS[sign_id]

    valid_twists = [tid for tid, twist in TWISTS.items() if sign_solves_twist(sign, twist)]
    if args.twist is not None and args.twist not in valid_twists:
        shortcut_key = args.shortcut or "jump_rung"
        raise StoryError(explain_rejection(attic, sign, SHORTCUTS[shortcut_key], TWISTS[args.twist]))
    twist_id = args.twist or rng.choice(sorted(valid_twists))

    valid_shortcuts = [sid for sid, shortcut in SHORTCUTS.items() if shortcut_is_bad_idea(shortcut)]
    shortcut_id = args.shortcut or rng.choice(sorted(valid_shortcuts))

    if (attic_id, sign_id, shortcut_id, twist_id) not in set(valid_combos()):
        raise StoryError(explain_rejection(attic, sign, SHORTCUTS[shortcut_id], TWISTS[twist_id]))

    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.name or _pick_name(rng, gender)
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    helper = args.helper or _pick_name(rng, helper_gender, avoid=hero)
    captain = args.captain or rng.choice(CAPTAINS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        attic_id, sign_id, shortcut_id, twist_id, hero, gender,
        helper, helper_gender, captain, trait
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        ATTICS[params.attic], SIGNS[params.sign], SHORTCUTS[params.shortcut],
        TWISTS[params.twist], params.hero, params.hero_gender,
        params.helper, params.helper_gender, params.captain, params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (attic, sign, shortcut, twist) combos:\n")
        for attic, sign, shortcut, twist in combos:
            print(f"  {attic:16} {sign:18} {shortcut:12} {twist}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 80, 80):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed), i)
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
            print(json.dumps([sample.to_dict() for sample in samples],
                             indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero}: {p.attic} / {p.sign} / {p.shortcut} / "
                f"{p.twist} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
