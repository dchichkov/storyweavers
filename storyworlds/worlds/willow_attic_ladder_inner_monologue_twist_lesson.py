#!/usr/bin/env python3
"""
storyworlds/worlds/willow_attic_ladder_inner_monologue_twist_lesson.py
========================================================================

A standalone storyworld for a child-facing pirate tale set on an attic ladder.
The world is small and concrete: a young pirate helper climbs an attic ladder
in a harbor loft, studies a willow clue, argues privately with a tempting bad
idea, and discovers a twist that turns "treasure" into something useful.

The simulation keeps the physical problem and the emotional lesson on the same
carriers. A willow clue must match the twist by a shared physical key; the
ladder must actually be risky enough to justify help; and the child's inner
monologue only becomes wise after it is checked against what the ladder and clue
are really doing.
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
        female = {"girl", "mother", "woman", "captainess"}
        male = {"boy", "father", "man", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def reflexive(self) -> str:
        if self.type in {"girl", "mother", "woman", "captainess"}:
            return "herself"
        if self.type in {"boy", "father", "man", "captain"}:
            return "himself"
        return "themself"


@dataclass
class Attic:
    id: str
    name: str
    ladder: str
    rafters: str
    sea_sound: str
    helper_role: str
    final_image: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class WillowClue:
    id: str
    object: str
    mark: str
    rhyme: str
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
    clue: str
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
    def __init__(self, attic: Attic) -> None:
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


def _r_study_clue(world: World) -> list[str]:
    hero = world.get("hero")
    clue = world.get("clue")
    sig = ("study", clue.id)
    if clue.meters["studied"] >= THRESHOLD and sig not in world.fired:
        world.fired.add(sig)
        hero.memes["insight"] += 1
    return []


def _r_notice_danger(world: World) -> list[str]:
    hero = world.get("hero")
    ladder = world.get("ladder")
    shortcut = world.get("shortcut")
    sig = ("danger", ladder.id)
    if ladder.meters["wobble"] >= THRESHOLD and shortcut.meters["noticed"] >= THRESHOLD:
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["caution"] += 1
            hero.memes["temptation"] += shortcut.meters["lure"]
    return []


def _r_call_for_help(world: World) -> list[str]:
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
    Rule("study", "physical", _r_study_clue),
    Rule("danger", "physical_inner", _r_notice_danger),
    Rule("help", "inner_social", _r_call_for_help),
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


def clue_fits_attic(attic: Attic, clue: WillowClue) -> bool:
    return clue.key in attic.supports


def clue_solves_twist(clue: WillowClue, twist: Twist) -> bool:
    return clue.key == twist.key


def shortcut_is_bad_idea(shortcut: Shortcut) -> bool:
    return shortcut.required in {"rush", "yank", "hide"} and shortcut.lure >= 2


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for attic_id, attic in ATTICS.items():
        for clue_id, clue in CLUES.items():
            if not clue_fits_attic(attic, clue):
                continue
            for shortcut_id, shortcut in SHORTCUTS.items():
                if not shortcut_is_bad_idea(shortcut):
                    continue
                for twist_id, twist in TWISTS.items():
                    if clue_solves_twist(clue, twist):
                        combos.append((attic_id, clue_id, shortcut_id, twist_id))
    return sorted(combos)


def outcome_of(params: StoryParams) -> str:
    return TWISTS[params.twist].outcome


def ensure_period(text: str) -> str:
    if text.endswith((".", "!", "?")):
        return text
    return text + "."


def explain_rejection(attic: Attic, clue: WillowClue,
                      shortcut: Shortcut, twist: Twist) -> str:
    if not clue_fits_attic(attic, clue):
        return (f"(No story: {attic.name} does not physically support the "
                f"{clue.object} clue. The attic ladder needs the right kind of "
                f"light, wind, or rung for that clue to work.)")
    if not clue_solves_twist(clue, twist):
        return (f"(No story: the {clue.object} clue points by {clue.key}, but "
                f"this twist needs {twist.key}. The willow clue must truly open "
                f"the twist.)")
    if not shortcut_is_bad_idea(shortcut):
        return (f"(No story: {shortcut.label} is not a tempting bad idea, so the "
                f"inner monologue has no real moral turn.)")
    return "(No story: this combination falls outside the attic-ladder pirate world.)"


def predict_bad_grab(world: World, shortcut: Shortcut) -> dict:
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


def introduce(world: World, hero: Entity, helper: Entity, attic: Attic) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["friendship"] += 1
    world.say(
        f"Once upon a time, {hero.id} was the youngest helper on Captain "
        f"{world.get('captain').id}'s little pirate crew."
    )
    world.say(
        f"One windy afternoon, {hero.pronoun()} climbed the {attic.ladder} into "
        f"{attic.name}, where {attic.rafters}."
    )
    world.say(
        f"Below the hatch, {attic.sea_sound}, and {helper.id} waited with a hand "
        f"near the ladder in case the climb turned tricky."
    )


def rumor_and_clue(world: World, hero: Entity, clue: WillowClue, twist: Twist) -> None:
    cache = world.get("cache")
    clue_ent = world.get("clue")
    clue_ent.meters["found"] += 1
    world.say(
        f"The crew had been whispering about {twist.apparent}, hidden somewhere "
        f"above the old sails."
    )
    world.say(
        f"Near the top rung, {hero.id} found {clue.object}. It carried {clue.mark}."
    )
    world.say(f'The willow clue seemed to sing, "{clue.rhyme}"')
    cache.meters["rumored"] += 1


def study_clue(world: World, hero: Entity, clue: WillowClue) -> None:
    clue_ent = world.get("clue")
    clue_ent.meters["studied"] += 1
    world.say(
        f"{hero.id} did not snatch at the first shiny thought. {hero.pronoun('subject').capitalize()} "
        f"held still on the rung and studied the clue: {clue.study}."
    )
    world.say(
        f'"If the willow is telling the truth," {hero.pronoun()} thought, "then it is '
        f'pointing with {clue.hint}, not with a loud boast."'
    )
    propagate(world)


def tempt_shortcut(world: World, hero: Entity, shortcut: Shortcut) -> None:
    ladder = world.get("ladder")
    shortcut_ent = world.get("shortcut")
    shortcut_ent.meters["noticed"] += 1
    shortcut_ent.meters["lure"] = float(shortcut.lure)
    world.facts["bad_grab_prediction"] = predict_bad_grab(world, shortcut)
    world.say(f"Then the bad idea arrived: {shortcut.temptation}.")
    world.say(
        f'{shortcut.thought} {hero.id} thought. The attic ladder gave a small '
        f"creak under one foot."
    )
    ladder.meters["wobble"] += 1
    propagate(world)


def choose_wisely(world: World, hero: Entity, helper: Entity, shortcut: Shortcut) -> None:
    hero.memes["choose_help"] += 1
    world.say(
        f'"No," {hero.pronoun()} told {hero.reflexive()} in a whisper. "A real '
        f'pirate does not win by {shortcut.label}."'
    )
    world.say(
        f"{shortcut.refuse} \"{helper.id}, steady the ladder,\" {hero.id} called."
    )
    propagate(world)
    world.say(
        f"{helper.id} planted both feet, gripped the ladder rails, and answered, "
        f"\"Aye. Slow hands, clear eyes.\""
    )


def reveal_twist(world: World, hero: Entity, twist: Twist) -> None:
    cache = world.get("cache")
    if cache.meters["revealed"] < THRESHOLD:
        propagate(world)
    world.say(
        f"With the ladder firm and the willow clue clear, {hero.id} reached the "
        f"small box behind the sail roll. {twist.reveal}"
    )
    world.say(
        f"That was the twist: {twist.truth}. {hero.id} blinked, and then "
        f"{hero.pronoun('possessive')} grin turned soft instead of greedy."
    )


def ending(world: World, hero: Entity, helper: Entity, twist: Twist) -> None:
    world.say(
        f"{ensure_period(twist.payoff)} Captain {world.get('captain').id} nodded from below, as "
        f"proud as if a whole chest of gold had been found."
    )
    world.say(
        f"{hero.id} learned something better than a treasure rhyme: {twist.lesson}"
    )
    world.say(
        f"By sunset, {world.attic.final_image}, and the willow clue tapped the beam "
        f"like a tiny green flag over the safe attic ladder."
    )


def tell(attic: Attic, clue: WillowClue, shortcut: Shortcut, twist: Twist,
         hero_name: str = "Mara", hero_gender: str = "girl",
         helper_name: str = "Pip", helper_gender: str = "boy",
         captain: str = "Brine", trait: str = "careful") -> World:
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
        role="captain", traits=["old", "salty"],
    )).id = captain
    world.add(Entity(
        "ladder", type="attic ladder", label=attic.ladder,
        attrs={"supports": sorted(attic.supports)},
    ))
    world.add(Entity(
        "clue", type="willow clue", label=clue.object,
        attrs={"key": clue.key},
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
    rumor_and_clue(world, hero, clue, twist)

    world.para()
    study_clue(world, hero, clue)
    tempt_shortcut(world, hero, shortcut)
    choose_wisely(world, hero, helper, shortcut)

    world.para()
    reveal_twist(world, hero, twist)
    ending(world, hero, helper, twist)

    world.facts.update(
        hero=hero,
        helper=helper,
        attic=attic,
        clue=clue,
        shortcut=shortcut,
        twist=twist,
        ladder=world.get("ladder"),
        cache=world.get("cache"),
        captain=captain,
        outcome=twist.outcome,
    )
    return world


ATTICS = {
    "boathouse": Attic(
        "boathouse",
        "the boathouse attic",
        "attic ladder with salt-white rungs",
        "nets slept in the rafters and old oars crossed like quiet swords",
        "the harbor clinked against the pilings",
        "deckmate",
        "the mended ladder stood straight beside the hatch",
        supports={"rung", "wind", "thread"},
        tags={"attic", "ladder", "pirate", "harbor"},
    ),
    "chart_loft": Attic(
        "chart_loft",
        "the chart loft above the dock office",
        "narrow attic ladder with tar-dark rails",
        "rolled charts and tiny lantern hooks made striped shadows",
        "gulls cried over the wharf boards",
        "cabin friend",
        "the hatch stayed open to the peach-colored sky",
        supports={"rung", "thread", "shadow"},
        tags={"attic", "ladder", "pirate", "charts"},
    ),
    "captain_nook": Attic(
        "captain_nook",
        "the captain's attic nook",
        "creaking attic ladder under a round window",
        "old sea coats swayed and a brass spyglass blinked from a beam",
        "the tide slapped the stones below the house",
        "young mate",
        "the round window glowed on the ladder steps",
        supports={"wind", "shadow", "thread"},
        tags={"attic", "ladder", "pirate", "tide"},
    ),
}

CLUES = {
    "willow_braid": WillowClue(
        "willow_braid",
        "a thin willow braid tied around one rung",
        "three tiny knots and a chalk dot",
        "Rung that hums and rung that sighs, trust the step that answers wise.",
        "the chalk dot matched the only rung that sounded hollow when the wind nudged it",
        "rung",
        "the hollow knock in the rung",
        tags={"willow", "ladder", "rung"},
    ),
    "willow_whistle": WillowClue(
        "willow_whistle",
        "a willow whistle hanging by a nail",
        "a blue thread through its eye",
        "When rafters breathe and ladder sings, hear the truth on windy wings.",
        "the whistle only answered when the draft slipped behind one sail bundle",
        "wind",
        "the little wind in the rafters",
        tags={"willow", "wind", "attic"},
    ),
    "willow_hoop": WillowClue(
        "willow_hoop",
        "a small willow hoop wrapped with red thread",
        "a thread tail bright as a berry",
        "Thread to beam and beam to light, follow where the red turns bright.",
        "the red thread lit up only where a shaft of light crossed the beam beside the ladder",
        "thread",
        "the place where thread met light",
        tags={"willow", "thread", "light"},
    ),
    "willow_shadow": WillowClue(
        "willow_shadow",
        "a willow leaf pinned beside the round window",
        "a cutout star in its middle",
        "Leaf and lantern, dark and bright, shadow marks the truthful sight.",
        "the cutout star only touched the right beam when the window light leaned west",
        "shadow",
        "the shadow star",
        tags={"willow", "shadow", "window"},
    ),
}

SHORTCUTS = {
    "leap_beam": Shortcut(
        "leap_beam",
        "leaping from the third rung to the beam",
        "the little box looked close enough for one brave jump",
        '"If I spring now, I can grab it before anyone tells me to wait,"',
        "So both hands stayed on the ladder, not on the boast in the thought.",
        "rush",
        4,
        tags={"risk", "hurry", "pirate"},
    ),
    "yank_rope": Shortcut(
        "yank_rope",
        "yanking the old pulley rope to knock the box loose",
        "a frayed rope dangled beside the ladder like a quick answer",
        '"If I yank that rope, the treasure will drop right into my arms,"',
        "The rope stayed still, and the old pulley's splinters stayed quiet.",
        "yank",
        3,
        tags={"risk", "rope", "pirate"},
    ),
    "hide_clue": Shortcut(
        "hide_clue",
        "hiding the clue and climbing alone",
        "for one blink, keeping the secret felt shiny and grand",
        '"If I keep this willow clue to myself, the find will belong only to me,"',
        "The clue stayed where both children could see it, and the ladder was no place for lonely pride.",
        "hide",
        3,
        tags={"secret", "pride", "pirate"},
    ),
    "wait_nice": Shortcut(
        "wait_nice",
        "waiting calmly on the rung",
        "the steady choice was already there",
        '"If I wait, no one gets hurt,"',
        "They waited together.",
        "wait",
        1,
        tags={"patience"},
    ),
}

TWISTS = {
    "repair_tin": Twist(
        "repair_tin",
        "Captain Brine's hidden silver",
        "the box held rung pegs, wax, and a note about fixing the attic ladder before any child climbed it again",
        "rung",
        "Inside was not silver at all, but a repair tin wrapped in oilcloth. The captain had hidden the tools beside the bad rung so the ladder would be mended before anyone chased treasure.",
        "Together the children passed the tin down, and by supper the dangerous rung had been replaced",
        "Useful treasure is better than shiny trouble. A wise pirate makes the climb safer for the next person.",
        "repair",
        "the whole crew",
        tags={"lesson", "repair", "ladder"},
    ),
    "call_whistle": Twist(
        "call_whistle",
        "a pearl whistle from a sea king",
        "the box held a willow call whistle meant for summoning help whenever the attic ladder swayed",
        "wind",
        "When the draft slipped through the rafters, the box gave a low note instead of a sparkle. Inside lay a smooth call whistle and a tag that read, FOR HIGH PLACES, NEVER FOR SHOWING OFF.",
        "The whistle was hung beside the hatch where any child could reach it before a climb",
        "Asking for help is not a weak ending to an adventure. It is how a brave pirate keeps the whole crew safe.",
        "help",
        "the attic crew",
        tags={"lesson", "help", "wind"},
    ),
    "sail_thread": Twist(
        "sail_thread",
        "a roll of ruby ribbon from a stolen chest",
        "the box held red sail thread and patches for mending the toy boats the younger children sailed in the cove",
        "thread",
        "The red line on the beam led to a flat sailor's box. Inside were thread cards, neat little sail patches, and a note asking the older children to share them, not hoard them.",
        "Before dusk, the children spread the patches on the dock table and fixed every torn toy sail they could find",
        "The best kind of treasure is something useful that can be shared. Pirate pride should leave more good behind than it takes.",
        "share",
        "the younger dock children",
        tags={"lesson", "share", "thread"},
    ),
    "star_chart": Twist(
        "star_chart",
        "a map to moonlit doubloons",
        "the box held a star chart showing when the attic window made a safe shadow mark on the ladder and when it did not",
        "shadow",
        "The shadow star touched a flat beam and uncovered a chart folded inside a biscuit tin. It was not a gold map. It was a careful chart showing the safe hour for climbing when the window light made the shaky step easy to see.",
        "The chart was pinned beside the hatch so no one would climb at the blind hour again",
        "A lesson can be a treasure when it helps everyone move more safely. Good pirates pass useful knowledge along.",
        "knowledge",
        "the harbor house",
        tags={"lesson", "knowledge", "shadow"},
    ),
}

GIRL_NAMES = ["Mara", "Nia", "Lily", "Poppy", "Zoe", "Mina", "Tess", "Rina"]
BOY_NAMES = ["Pip", "Finn", "Theo", "Sam", "Leo", "Noah", "Jory", "Ben"]
TRAITS = ["careful", "bright", "steady", "curious", "brave", "kind"]
CAPTAINS = ["Brine", "Reed", "Sable", "Marrow"]

CURATED = [
    StoryParams("boathouse", "willow_braid", "leap_beam", "repair_tin",
                "Mara", "girl", "Pip", "boy", "Brine", "careful"),
    StoryParams("captain_nook", "willow_whistle", "hide_clue", "call_whistle",
                "Finn", "boy", "Nia", "girl", "Reed", "bright"),
    StoryParams("chart_loft", "willow_hoop", "yank_rope", "sail_thread",
                "Lily", "girl", "Theo", "boy", "Sable", "kind"),
    StoryParams("captain_nook", "willow_shadow", "leap_beam", "star_chart",
                "Sam", "boy", "Mina", "girl", "Marrow", "curious"),
]


KNOWLEDGE = {
    "willow": [(
        "What is willow?",
        "Willow is a kind of tree with bendy branches and narrow leaves. People can weave the branches into small useful things."
    )],
    "attic": [(
        "What is an attic?",
        "An attic is a small space under a roof where people keep stored things. It often has beams, dust, and narrow steps or a ladder."
    )],
    "ladder": [(
        "Why should a child be careful on an attic ladder?",
        "A ladder can wobble or have a weak rung. Slow climbing and help from another person make it safer."
    )],
    "pirate": [(
        "What makes this a pirate tale?",
        "It has a captain, a crew, a hidden cache, and sea-colored language. The adventure happens in a harbor world, even though the lesson is gentle."
    )],
    "wind": [(
        "How can wind help solve a clue?",
        "Wind can move a whistle, a thread, or a hanging leaf. If a clue depends on movement, a careful child can watch what the draft touches."
    )],
    "thread": [(
        "Why is thread useful?",
        "Thread can mend cloth and keep things working longer. In a story, useful materials can matter more than shiny treasure."
    )],
    "shadow": [(
        "How can a shadow be useful?",
        "A shadow can mark a place or a time when light falls in just the right way. Watching shadows carefully can turn light into a clue."
    )],
    "lesson": [(
        "What is a lesson learned in a story?",
        "A lesson learned is the idea a character understands after something happens. It usually changes what the character values next time."
    )],
}
KNOWLEDGE_ORDER = ["willow", "attic", "ladder", "pirate", "wind", "thread",
                   "shadow", "lesson"]


def place_name(attic: Attic) -> str:
    if attic.name.startswith("the "):
        return attic.name[4:]
    return attic.name


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, attic, clue, shortcut, twist = (
        f["hero"], f["attic"], f["clue"], f["shortcut"], f["twist"]
    )
    return [
        f'Write a TinyStories-style pirate tale set on an attic ladder that includes the word "willow", an inner monologue, a twist, and a lesson learned.',
        f"Tell a child-facing story about {hero.id} in {attic.name}, where {clue.object} becomes a clue, {shortcut.label} looks tempting, and the treasure rumor turns into something useful.",
        f"Write a harbor pirate story with a complete beginning, a middle turn on the attic ladder, and an ending that proves what changed after the willow clue is understood.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, attic, clue, shortcut, twist = (
        f["hero"], f["helper"], f["attic"], f["clue"], f["shortcut"], f["twist"]
    )
    qa = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, the youngest helper on a little pirate crew. {hero.pronoun('subject').capitalize()} climbs into {attic.name} on the attic ladder."
        ),
        (
            f"What willow clue did {hero.id} find?",
            f"{hero.id} found {clue.object}. It mattered because its {clue.key} clue showed how to read the attic safely instead of guessing."
        ),
        (
            f"What bad idea tempted {hero.id}?",
            f"{hero.id} was tempted by {shortcut.label}. The idea looked fast, but it would have put pride and hurry ahead of safety."
        ),
        (
            f"What did {hero.id} say in {hero.pronoun('possessive')} inner monologue?",
            f"{hero.id} first heard the tempting thought in {hero.pronoun('possessive')} own head, then answered it. {hero.pronoun('subject').capitalize()} told {hero.reflexive()} that a real pirate should not win by a dangerous shortcut."
        ),
        (
            "What was the twist?",
            f"The twist was that {twist.apparent} was not the true treasure at all. Instead, {twist.truth}."
        ),
        (
            "What lesson did the child learn?",
            f"{hero.id} learned this lesson: {twist.lesson} That lesson came from checking the willow clue, calling for help, and using the find to protect or help other people."
        ),
        (
            "How did the story end?",
            f"It ended with the attic ladder safer and the find used for a good purpose. The ending image proves the adventure changed the place, not just {hero.id}'s mood."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["attic"].tags) | set(f["clue"].tags) | set(f["shortcut"].tags)
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
solves(Clue, Twist) :- clue_key(Clue, Key), twist_key(Twist, Key).

bad_shortcut(S) :- requires(S, rush).
bad_shortcut(S) :- requires(S, yank).
bad_shortcut(S) :- requires(S, hide).
tempting(S) :- shortcut_lure(S, L), L >= 2.

valid(Attic, Clue, Shortcut, Twist) :-
    attic(Attic), supports(Attic, Key), clue_key(Clue, Key),
    solves(Clue, Twist), bad_shortcut(Shortcut), tempting(Shortcut).

outcome(O) :- chosen_twist(T), twist_outcome(T, O).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for attic_id, attic in ATTICS.items():
        lines.append(asp.fact("attic", attic_id))
        for support in sorted(attic.supports):
            lines.append(asp.fact("supports", attic_id, support))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_key", clue_id, clue.key))
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

    extra = "\n".join([
        asp.fact("chosen_twist", params.twist),
    ])
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
        if "willow" not in sample.story.lower():
            rc = 1
            print(f"MISMATCH: missing required seed word in story for {params}.")
        if "attic ladder" not in sample.story.lower():
            rc = 1
            print(f"MISMATCH: missing setting phrase in story for {params}.")
    if rc == 0:
        print(f"OK: generated curated stories keep the seed word and attic ladder setting ({len(CURATED)} cases).")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a pirate attic ladder, a willow clue, "
                    "a private debate, and a useful twist."
    )
    ap.add_argument("--attic", choices=ATTICS)
    ap.add_argument("--clue", choices=CLUES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    attic_id = args.attic or rng.choice(sorted(ATTICS))
    attic = ATTICS[attic_id]

    valid_clues = [cid for cid, clue in CLUES.items() if clue_fits_attic(attic, clue)]
    if args.clue is not None and args.clue not in valid_clues:
        raise StoryError(explain_rejection(
            attic, CLUES[args.clue], SHORTCUTS.get(args.shortcut or "wait_nice", SHORTCUTS["wait_nice"]),
            TWISTS.get(args.twist or "repair_tin", TWISTS["repair_tin"])
        ))
    clue_id = args.clue or rng.choice(sorted(valid_clues))
    clue = CLUES[clue_id]

    valid_twists = [tid for tid, twist in TWISTS.items() if clue_solves_twist(clue, twist)]
    if args.twist is not None and args.twist not in valid_twists:
        shortcut_key = args.shortcut or "wait_nice"
        raise StoryError(explain_rejection(attic, clue, SHORTCUTS[shortcut_key], TWISTS[args.twist]))
    twist_id = args.twist or rng.choice(sorted(valid_twists))

    valid_shortcuts = [sid for sid, shortcut in SHORTCUTS.items() if shortcut_is_bad_idea(shortcut)]
    shortcut_id = args.shortcut or rng.choice(sorted(valid_shortcuts))

    if (attic_id, clue_id, shortcut_id, twist_id) not in set(valid_combos()):
        raise StoryError(explain_rejection(
            attic, clue, SHORTCUTS[shortcut_id], TWISTS[twist_id]
        ))

    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.name or _pick_name(rng, gender)
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    helper = args.helper or _pick_name(rng, helper_gender, avoid=hero)
    captain = args.captain or rng.choice(CAPTAINS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        attic_id, clue_id, shortcut_id, twist_id, hero, gender,
        helper, helper_gender, captain, trait
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        ATTICS[params.attic], CLUES[params.clue], SHORTCUTS[params.shortcut],
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
        print(f"{len(combos)} compatible (attic, clue, shortcut, twist) combos:\n")
        for attic, clue, shortcut, twist in combos:
            print(f"  {attic:12} {clue:14} {shortcut:11} {twist}")
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
            print(json.dumps([sample.to_dict() for sample in samples],
                             indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero}: {p.attic} / {p.clue} / {p.shortcut} / "
                f"{p.twist} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
