#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bath_dim_kindness_adventure.py
=========================================================

A standalone story world for a tiny "bath-dim kindness adventure" domain.

Premise
-------
Two children are having a bath-time adventure in a dim bathroom. A favorite
bath toy drifts into a shadowy or awkward spot, and the more timid child pauses.
The other child notices the fear and responds with kindness in a way that
actually fits the problem: sharing light, offering a steady hand, or nudging
the toy closer with a bath tool. The story ends with the adventure continuing
because the children learned that kind help can make a dark place feel brave.

This world keeps the domain small and classical:

- typed entities carry physical meters and emotional memes
- simulated state drives the prose
- invalid kindness/problem pairings are rejected explicitly
- a Python reasonableness gate has an inline ASP twin
- QA is generated from world state, not by parsing the story text

Run it
------
    python storyworlds/worlds/gpt-5.4/bath_dim_kindness_adventure.py
    python storyworlds/worlds/gpt-5.4/bath_dim_kindness_adventure.py --challenge drain_shadow --aid lantern_cup
    python storyworlds/worlds/gpt-5.4/bath_dim_kindness_adventure.py --aid shell_scoop
    python storyworlds/worlds/gpt-5.4/bath_dim_kindness_adventure.py --all
    python storyworlds/worlds/gpt-5.4/bath_dim_kindness_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4/bath_dim_kindness_adventure.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly
# from the repo root. This file lives in storyworlds/worlds/gpt-5.4/, so the
# package directory (storyworlds/) is three levels up.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------


@dataclass
class Theme:
    id: str
    scene: str
    opener: str
    titles: tuple[str, str]
    water_name: str
    goal: str
    ending: str


@dataclass
class Challenge:
    id: str
    label: str
    text: str
    fear_text: str
    needs: set[str]
    severity: int
    location: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    mode: str
    power: int
    action: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    sparkle: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_dim_fear(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    seeker = world.get("seeker")
    challenge = world.facts["challenge"]
    if room.meters["dim"] < THRESHOLD:
        return out
    if seeker.memes["timid"] < THRESHOLD:
        return out
    if seeker.memes["helped"] >= THRESHOLD:
        return out
    sig = ("dim_fear", challenge.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seeker.memes["fear"] += float(challenge.severity)
    out.append("__fear__")
    return out


def _r_kindness_relief(world: World) -> list[str]:
    out: list[str] = []
    seeker = world.get("seeker")
    helper = world.get("helper")
    aid_mode = world.facts.get("aid_mode")
    challenge = world.facts["challenge"]
    if aid_mode is None:
        return out
    if aid_mode not in challenge.needs:
        return out
    sig = ("relief", aid_mode, challenge.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seeker.memes["fear"] = max(0.0, seeker.memes["fear"] - challenge.severity)
    seeker.memes["courage"] += 2.0
    seeker.memes["trust"] += 1.0
    helper.memes["kindness"] += 1.0
    seeker.memes["helped"] += 1.0
    out.append("__relief__")
    return out


def _r_reach_treasure(world: World) -> list[str]:
    out: list[str] = []
    seeker = world.get("seeker")
    treasure = world.get("treasure")
    if seeker.memes["courage"] < THRESHOLD:
        return out
    if treasure.meters["retrieved"] >= THRESHOLD:
        return out
    sig = ("reach", treasure.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    treasure.meters["retrieved"] += 1.0
    treasure.meters["close"] += 1.0
    seeker.memes["joy"] += 1.0
    helper = world.get("helper")
    helper.memes["joy"] += 1.0
    out.append("__retrieved__")
    return out


CAUSAL_RULES = [
    Rule("dim_fear", "emotional", _r_dim_fear),
    Rule("kindness_relief", "social", _r_kindness_relief),
    Rule("reach_treasure", "physical", _r_reach_treasure),
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


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------


def aid_fits(aid: Aid, challenge: Challenge) -> bool:
    return aid.mode in challenge.needs and aid.power >= challenge.severity


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for challenge_id, challenge in CHALLENGES.items():
            for aid_id, aid in AIDS.items():
                if aid_fits(aid, challenge):
                    combos.append((theme_id, challenge_id, aid_id))
    return combos


def explain_rejection(challenge: Challenge, aid: Aid) -> str:
    need = " or ".join(sorted(challenge.needs))
    if aid.mode not in challenge.needs:
        return (
            f"(No story: {aid.label} helps by {aid.mode}, but {challenge.label} "
            f"really needs {need}. The kindness has to match the problem.)"
        )
    return (
        f"(No story: {aid.label} is too small for {challenge.label}. It has power "
        f"{aid.power}, but this problem needs at least {challenge.severity}.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------


def predict_fear(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    seeker = sim.get("seeker")
    return {
        "fear": seeker.memes["fear"],
        "hesitates": seeker.memes["fear"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Verbs / screenplay helpers
# ---------------------------------------------------------------------------


def bath_setup(world: World, seeker: Entity, helper: Entity, parent: Entity,
               theme: Theme, treasure: Treasure) -> None:
    room = world.get("room")
    room.meters["dim"] = 1.0
    for kid in (seeker, helper):
        kid.memes["joy"] += 1.0
    title_a, title_b = theme.titles
    world.say(
        f"At bath time, {parent.label_word.capitalize()} turned off the bright ceiling light "
        f"and left only the little wall lamp glowing. The bathroom was bath-dim, soft and "
        f"shadowy, and to {seeker.id} and {helper.id} it felt like {theme.scene}."
    )
    world.say(theme.opener.format(seeker=seeker.id, helper=helper.id, title_a=title_a, title_b=title_b))
    world.say(
        f"On the warm water, {treasure.phrase} bobbed and {treasure.sparkle}. "
        f"It was their treasure for the night's adventure."
    )


def drift_problem(world: World, seeker: Entity, theme: Theme, treasure: Treasure,
                  challenge: Challenge) -> None:
    treasure_ent = world.get("treasure")
    treasure_ent.meters["adrift"] += 1.0
    world.say(
        f"Then a tiny wave from {seeker.id}'s knee sent the {treasure.label} drifting toward "
        f"{challenge.location}. Soon it was at {challenge.text}."
    )
    world.say(
        f"If they lost it there, the whole game would lose {theme.goal}."
    )


def worry(world: World, seeker: Entity, challenge: Challenge) -> None:
    pred = predict_fear(world)
    world.facts["predicted_fear"] = pred["fear"]
    propagate(world, narrate=False)
    if seeker.memes["fear"] >= THRESHOLD:
        world.say(
            f"{seeker.id} leaned forward, then stopped. {challenge.fear_text} "
            f"{seeker.pronoun().capitalize()} pulled back until the water lapped softly at "
            f"{seeker.pronoun('possessive')} tummy."
        )


def notice_kindness(world: World, helper: Entity, seeker: Entity) -> None:
    helper.memes["care"] += 1.0
    world.say(
        f"{helper.id} saw the pause right away. Instead of laughing or grabbing the toy first, "
        f"{helper.pronoun()} looked carefully at {seeker.id}'s face."
    )
    world.say(
        f'"It looks too dark from here," {helper.id} said. "We can do it together."'
    )


def give_aid(world: World, helper: Entity, seeker: Entity, aid: Aid, challenge: Challenge) -> None:
    world.facts["aid_mode"] = aid.mode
    world.say(
        f"Then {helper.id} {aid.action}. It was a small, kind thing, but it changed the whole tub."
    )
    propagate(world, narrate=False)
    if seeker.memes["helped"] >= THRESHOLD:
        if aid.mode == "light":
            world.say(
                f"The shadows thinned, and {challenge.location} no longer looked like a monster place."
            )
        elif aid.mode == "steady":
            world.say(
                f"With {helper.id}'s steadiness there, the wobble went out of the moment."
            )
        elif aid.mode == "reach":
            world.say(
                f"The treasure slipped closer instead of farther away, and the hard part suddenly looked possible."
            )
        world.say(
            f"{seeker.id} took a slow breath. Fear shrank, and brave room opened up inside "
            f"{seeker.pronoun('object')}."
        )


def retrieve(world: World, seeker: Entity, helper: Entity, treasure: Treasure, challenge: Challenge) -> None:
    propagate(world, narrate=False)
    if world.get("treasure").meters["retrieved"] >= THRESHOLD:
        world.say(
            f"{seeker.id} reached through the warm water and brought back the {treasure.label}. "
            f"Not even {challenge.label} could keep it now."
        )
        world.say(
            f'{helper.id} grinned. "{theme_finish_line(world)}"'
        )


def theme_finish_line(world: World) -> str:
    theme = world.facts["theme"]
    return {
        "river_cave": "The expedition is still on!",
        "moon_lagoon": "The moon crew is safe again!",
        "pirate_harbor": "The harbor treasure is ours!"
    }.get(theme.id, "The adventure can go on!")


def gratitude(world: World, seeker: Entity, helper: Entity) -> None:
    seeker.memes["gratitude"] += 1.0
    helper.memes["love"] += 1.0
    world.say(
        f'"Thank you for helping me," {seeker.id} said.'
    )
    world.say(
        f'"That is what adventure partners do," {helper.id} answered, and {seeker.id} smiled so hard that '
        f"little drops shone on {seeker.pronoun('possessive')} cheeks."
    )


def calm_end(world: World, parent: Entity, seeker: Entity, helper: Entity,
             theme: Theme, treasure: Treasure, aid: Aid) -> None:
    for kid in (seeker, helper):
        kid.memes["safety"] += 1.0
        kid.memes["joy"] += 1.0
    world.say(
        f"{parent.label_word.capitalize()} handed them the towel ship at the side of the tub and watched "
        f"the game go on."
    )
    world.say(
        f"Now the bathroom still looked bath-dim, but it no longer felt lonely or scary. "
        f"With {aid.phrase} and a kind heart between them, {seeker.id} and {helper.id} "
        f"{theme.ending}."
    )


def tell(theme: Theme, challenge: Challenge, aid: Aid, treasure: Treasure,
         seeker_name: str = "Lina", seeker_gender: str = "girl",
         helper_name: str = "Owen", helper_gender: str = "boy",
         parent_type: str = "mother", seeker_trait: str = "careful",
         helper_trait: str = "gentle") -> World:
    if not aid_fits(aid, challenge):
        raise StoryError(explain_rejection(challenge, aid))

    world = World()
    seeker = world.add(Entity(
        id=seeker_name,
        kind="character",
        type=seeker_gender,
        role="seeker",
        traits=[seeker_trait, "small"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=[helper_trait, "kind"],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    room = world.add(Entity(id="room", type="bathroom", label="the bathroom"))
    treasure_ent = world.add(Entity(id="treasure", type="toy", label=treasure.label))
    aid_ent = world.add(Entity(id="aid", type="aid", label=aid.label))
    seeker.memes["timid"] = 1.0
    helper.memes["ready"] = 1.0
    room.meters["warm"] = 1.0
    treasure_ent.meters["floating"] = 1.0
    aid_ent.meters["available"] = 1.0

    world.facts.update(
        theme=theme,
        challenge=challenge,
        aid=aid,
        treasure=treasure,
        seeker=seeker,
        helper=helper,
        parent=parent,
    )

    bath_setup(world, seeker, helper, parent, theme, treasure)
    world.para()
    drift_problem(world, seeker, theme, treasure, challenge)
    worry(world, seeker, challenge)
    world.para()
    notice_kindness(world, helper, seeker)
    give_aid(world, helper, seeker, aid, challenge)
    retrieve(world, seeker, helper, treasure, challenge)
    gratitude(world, seeker, helper)
    world.para()
    calm_end(world, parent, seeker, helper, theme, treasure, aid)

    world.facts.update(
        resolved=world.get("treasure").meters["retrieved"] >= THRESHOLD,
        fear_before=world.facts.get("predicted_fear", 0.0),
        kindness_used=helper.memes["kindness"] >= THRESHOLD,
        gratitude=seeker.memes["gratitude"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------


THEMES = {
    "river_cave": Theme(
        "river_cave",
        "a cave river under shining stone walls",
        '{title_a} {seeker} and {title_b} {helper} were steering a bubble raft through the hidden river.',
        ("Captain", "Scout"),
        "river",
        "its sparkle",
        "paddled on through their cave river, brave and close together",
    ),
    "moon_lagoon": Theme(
        "moon_lagoon",
        "a moon lagoon under sleepy silver light",
        '{title_a} {seeker} and {title_b} {helper} were guarding a secret lagoon where foam hills drifted like clouds.',
        ("Pilot", "Keeper"),
        "lagoon",
        "its silver secret",
        "sailed gentle circles through the moon lagoon, still talking kindly to each other",
    ),
    "pirate_harbor": Theme(
        "pirate_harbor",
        "a pirate harbor tucked inside dark rocks",
        '{title_a} {seeker} and {title_b} {helper} were watching over a tiny harbor where the bubbles were brave white waves.',
        ("Matey", "Captain"),
        "harbor",
        "its treasure",
        "sent their little harbor fleet back into the warm water with happy splashes",
    ),
}

CHALLENGES = {
    "drain_shadow": Challenge(
        "drain_shadow",
        "the drain shadow",
        "the dark swirl near the drain",
        "The dark circle by the drain looked deep and whirly in the dim light.",
        {"light"},
        2,
        "the dark swirl near the drain",
        tags={"drain", "dim", "shadow"},
    ),
    "slippery_rim": Challenge(
        "slippery_rim",
        "the slippery rim",
        "the shiny edge of the tub where the soap made everything slick",
        "The rim looked glossy and wobbly, like one wrong reach might make the moment feel too big.",
        {"steady"},
        2,
        "the shiny edge of the tub",
        tags={"slip", "tub"},
    ),
    "foam_cove": Challenge(
        "foam_cove",
        "the foam cove",
        "a pocket of bubbles packed thick against the far side",
        "The heap of bubbles hid the toy so well that the far side of the tub felt farther away than it really was.",
        {"reach"},
        1,
        "the far bubble cove",
        tags={"bubbles", "foam"},
    ),
    "curtain_corner": Challenge(
        "curtain_corner",
        "the curtain corner",
        "the dim corner under the hanging towel where the light barely reached",
        "That corner looked very shadowy, and in bath-dim light it seemed bigger than a plain bathroom corner.",
        {"light"},
        3,
        "the corner under the hanging towel",
        tags={"dim", "shadow", "towel"},
    ),
}

AIDS = {
    "lantern_cup": Aid(
        "lantern_cup",
        "the star cup lantern",
        "the star cup lantern",
        "light",
        2,
        "lifted the little star cup, filled with glow from the wall lamp, and held it over the water like a lantern",
        tags={"light", "cup"},
    ),
    "nightlight_boat": Aid(
        "nightlight_boat",
        "the moon night-light",
        "the moon night-light nearby",
        "light",
        3,
        "slid the small moon night-light closer on the bath mat until a pale gold shine fell across the tub",
        tags={"light", "nightlight"},
    ),
    "steady_hand": Aid(
        "steady_hand",
        "a steady hand",
        "a steady hand",
        "steady",
        2,
        "offered a warm hand for balance and kept it right there at the safe side of the tub",
        tags={"hand", "balance"},
    ),
    "shell_scoop": Aid(
        "shell_scoop",
        "the shell scoop",
        "the shell scoop",
        "reach",
        1,
        "used the little shell scoop to nudge the drifting toy through the bubbles until it came within easy reach",
        tags={"reach", "scoop"},
    ),
}

TREASURES = {
    "duck": Treasure("duck", "duck", "their yellow duck", "winked with one bright bead eye", tags={"duck"}),
    "boat": Treasure("boat", "boat", "their blue bath boat", "rocked on the water like a tiny ship", tags={"boat"}),
    "whale": Treasure("whale", "whale", "their smooth blue whale", "gleamed with a wet, round back", tags={"whale"}),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ivy", "Ella", "Zoe", "Ruby", "Mina"]
BOY_NAMES = ["Owen", "Leo", "Finn", "Max", "Theo", "Eli", "Ben", "Sam"]
SEEKER_TRAITS = ["careful", "small", "thoughtful", "quiet"]
HELPER_TRAITS = ["gentle", "kind", "steady", "cheerful"]

CURATED = [
    # light helps a dim fear near the drain
    None,  # filled below after StoryParams is defined
]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------


@dataclass
class StoryParams:
    theme: str
    challenge: str
    aid: str
    treasure: str
    seeker: str
    seeker_gender: str
    helper: str
    helper_gender: str
    parent: str
    seeker_trait: str
    helper_trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("river_cave", "drain_shadow", "lantern_cup", "boat",
                "Lina", "girl", "Owen", "boy", "mother", "careful", "gentle"),
    StoryParams("moon_lagoon", "slippery_rim", "steady_hand", "duck",
                "Nora", "girl", "Finn", "boy", "father", "quiet", "steady"),
    StoryParams("pirate_harbor", "foam_cove", "shell_scoop", "whale",
                "Leo", "boy", "Maya", "girl", "mother", "thoughtful", "kind"),
    StoryParams("moon_lagoon", "curtain_corner", "nightlight_boat", "duck",
                "Ruby", "girl", "Theo", "boy", "father", "small", "cheerful"),
]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------


KNOWLEDGE = {
    "dim": [(
        "What does dim mean?",
        "Dim means there is only a little light, not bright light. Things can look softer, shadowier, and harder to see."
    )],
    "shadow": [(
        "Why can shadows feel scary?",
        "Shadows can make ordinary things look strange when you cannot see them well. When more light comes in, the shape often looks normal again."
    )],
    "drain": [(
        "What is a bathtub drain?",
        "A bathtub drain is the little opening where water goes out. It can look swirly, but it is just part of the tub."
    )],
    "slip": [(
        "Why can a bathtub edge be slippery?",
        "Water and soap can make a bathtub edge slick. That is why it is safer to move slowly and keep a steady hand nearby."
    )],
    "bubbles": [(
        "Why can bubbles hide a toy?",
        "Lots of bubbles can cover a toy so you cannot see it well. The toy is still there, but the foam makes it harder to spot."
    )],
    "light": [(
        "How can more light help when something feels scary?",
        "More light helps you see what is really there. When you can see clearly, a shadow or dark corner often feels much less frightening."
    )],
    "hand": [(
        "Why does holding a steady hand help?",
        "A steady hand can help your body feel balanced and safe. It also reminds you that someone is right there with you."
    )],
    "reach": [(
        "Why is it kind to move something closer for a friend?",
        "It is kind because you notice what is hard for your friend and make it easier. Small help can turn a worried moment into a calm one."
    )],
    "nightlight": [(
        "What is a night-light?",
        "A night-light is a small lamp that gives a gentle glow in the dark. It helps a room feel calm without using bright light."
    )],
    "kindness": [(
        "What is kindness?",
        "Kindness is choosing to help, comfort, or care for someone. It can be a small action that changes how another person feels."
    )],
}
KNOWLEDGE_ORDER = ["dim", "shadow", "drain", "slip", "bubbles", "light", "hand", "reach", "nightlight", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = f["seeker"]
    helper = f["helper"]
    challenge = f["challenge"]
    aid = f["aid"]
    treasure = f["treasure"]
    theme = f["theme"]
    return [
        'Write a short adventure story for a 3-to-5-year-old that includes the word "bath-dim" and shows kindness changing a scary moment.',
        f"Tell a bath-time adventure where {seeker.id} pauses because of {challenge.label}, and {helper.id} helps with {aid.label} so they can rescue {treasure.phrase}.",
        f"Write a gentle adventure in {theme.scene} where one child notices another child is afraid, chooses kindness first, and the story ends with the game continuing safely.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker = f["seeker"]
    helper = f["helper"]
    parent = f["parent"]
    challenge = f["challenge"]
    aid = f["aid"]
    treasure = f["treasure"]
    theme = f["theme"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {seeker.id} and {helper.id} at bath time, with {seeker.id}'s {parent.label_word} nearby. They turn the tub into {theme.scene} and make a small adventure out of the bath."
        ),
        (
            "What went wrong in the bath?",
            f"The {treasure.label} drifted to {challenge.text}, and {seeker.id} did not want to reach for it right away. In the bath-dim room, that place felt bigger and scarier than it really was."
        ),
        (
            f"Why did {seeker.id} stop instead of grabbing the {treasure.label}?",
            f"{seeker.id} felt afraid because of {challenge.label} in the dim bathroom. The low light made the problem look harder, so {seeker.pronoun()} pulled back and hesitated."
        ),
        (
            f"How did {helper.id} show kindness?",
            f"{helper.id} noticed the fear and chose to help instead of teasing or rushing ahead. Then {helper.pronoun()} used {aid.label}, which matched the real problem and helped {seeker.id} feel brave again."
        ),
    ]
    if f.get("resolved"):
        qa.append((
            f"How did they get the {treasure.label} back?",
            f"They got it back after {helper.id} used {aid.label} and the scary part no longer felt so big. Because the help fit the problem, {seeker.id} could reach through the water and bring the toy back safely."
        ))
        qa.append((
            "How did the story end?",
            f"It ended warmly: the bathroom was still bath-dim, but it no longer felt frightening. The children kept playing because kindness had changed the adventure from a worried pause into a brave ending."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"kindness"}
    challenge = world.facts["challenge"]
    aid = world.facts["aid"]
    tags |= set(challenge.tags)
    tags |= set(aid.tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------


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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------


ASP_RULES = r"""
% Basic gate: an aid fits a challenge when its mode is allowed and its power is
% at least the challenge severity.
fits(A, C) :- aid(A), challenge(C), mode(A, M), needs(C, M), power(A, P), severity(C, S), P >= S.
valid(T, C, A) :- theme(T), challenge(C), aid(A), fits(A, C).

% Outcome is simple in this world: valid kindness resolves the problem.
outcome(resolved) :- chosen_challenge(C), chosen_aid(A), fits(A, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for cid, challenge in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("severity", cid, challenge.severity))
        for need in sorted(challenge.needs):
            lines.append(asp.fact("needs", cid, need))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("mode", aid_id, aid.mode))
        lines.append(asp.fact("power", aid_id, aid.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_challenge", params.challenge),
        asp.fact("chosen_aid", params.aid),
    ])
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

    for params in CURATED:
        py = "resolved" if aid_fits(AIDS[params.aid], CHALLENGES[params.challenge]) else "?"
        asp_res = asp_outcome(params)
        if py != asp_res:
            rc = 1
            print(f"MISMATCH outcome for {params.challenge}/{params.aid}: asp={asp_res} python={py}")

    # Smoke-test ordinary generation and emitting.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
    except Exception as err:  # pragma: no cover - verify-only behavior
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    else:
        print("OK: smoke-tested generate() and emit().")
    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a bath-dim adventure where kindness solves a small fear."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.challenge and args.aid:
        challenge = CHALLENGES[args.challenge]
        aid = AIDS[args.aid]
        if not aid_fits(aid, challenge):
            raise StoryError(explain_rejection(challenge, aid))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.challenge is None or combo[1] == args.challenge)
        and (args.aid is None or combo[2] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, challenge_id, aid_id = rng.choice(sorted(combos))
    treasure_id = args.treasure or rng.choice(sorted(TREASURES))
    seeker_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    seeker = _pick_name(rng, seeker_gender)
    helper = _pick_name(rng, helper_gender, avoid=seeker)
    parent = args.parent or rng.choice(["mother", "father"])
    seeker_trait = rng.choice(SEEKER_TRAITS)
    helper_trait = rng.choice(HELPER_TRAITS)
    return StoryParams(
        theme=theme_id,
        challenge=challenge_id,
        aid=aid_id,
        treasure=treasure_id,
        seeker=seeker,
        seeker_gender=seeker_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=parent,
        seeker_trait=seeker_trait,
        helper_trait=helper_trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        THEMES[params.theme],
        CHALLENGES[params.challenge],
        AIDS[params.aid],
        TREASURES[params.treasure],
        params.seeker,
        params.seeker_gender,
        params.helper,
        params.helper_gender,
        params.parent,
        params.seeker_trait,
        params.helper_trait,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, challenge, aid) combos:\n")
        for theme, challenge, aid in combos:
            print(f"  {theme:13} {challenge:15} {aid}")
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
            header = f"### {p.seeker} & {p.helper}: {p.challenge} with {p.aid} ({p.theme})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
