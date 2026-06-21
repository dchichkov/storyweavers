#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/yorkie_refraction_quest_moral_value_inner_monologue.py
=================================================================================

A standalone storyworld about a child and a yorkie who go on a little treasure
quest after a rainbow patch appears on the floor. The bright patch comes from
refraction: sunlight passing through a clear object and bending into colors.

The core tension is simple and concrete:
- a child wants the "rainbow treasure" badly,
- the rainbow comes from a clear object set up high,
- the child considers an unsafe shortcut to reach it,
- an inner monologue models the moral turn,
- a grown-up can help in the safe way.

The world rejects weak combinations. A quest is only reasonable when:
- the chosen object can really make a rainbow by refraction, and
- the chosen way of reaching it is unstable enough to create a real safety
  problem.

Like the better storyworlds in this repo, the prose comes from simulated state:
desire, wobble, fear, relief, trust, and the changed ending image.

Run it
------
python storyworlds/worlds/gpt-5.4/yorkie_refraction_quest_moral_value_inner_monologue.py
python storyworlds/worlds/gpt-5.4/yorkie_refraction_quest_moral_value_inner_monologue.py --light prism --perch books
python storyworlds/worlds/gpt-5.4/yorkie_refraction_quest_moral_value_inner_monologue.py --light mirror
python storyworlds/worlds/gpt-5.4/yorkie_refraction_quest_moral_value_inner_monologue.py --all
python storyworlds/worlds/gpt-5.4/yorkie_refraction_quest_moral_value_inner_monologue.py --qa --json
python storyworlds/worlds/gpt-5.4/yorkie_refraction_quest_moral_value_inner_monologue.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
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
class QuestTheme:
    id: str
    room: str
    game_open: str
    titles: str
    treasure_name: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LightMaker:
    id: str
    label: str
    phrase: str
    perch_place: str
    explanation: str
    color_line: str
    refracts: bool = True
    fragility: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Perch:
    id: str
    label: str
    phrase: str
    wobble_word: str
    danger: int
    unstable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class AdultHelp:
    id: str
    sense: int
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


def _r_wobble_fear(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    perch = world.entities.get("perch")
    yorkie = world.entities.get("yorkie")
    if not child or not perch:
        return out
    if child.meters["climbing"] < THRESHOLD or perch.meters["wobble"] < THRESHOLD:
        return out
    sig = ("wobble_fear", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    child.memes["conscience"] += 1
    if yorkie is not None:
        yorkie.memes["alarm"] += 1
    out.append("__wobble__")
    return out


def _r_break_scare(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    maker = world.entities.get("maker")
    if not child or not maker:
        return out
    if maker.meters["fallen"] < THRESHOLD:
        return out
    sig = ("break_scare", maker.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["sadness"] += 1
    child.memes["lesson"] += 1
    if maker.meters["broken"] >= THRESHOLD:
        out.append("__broken__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble_fear", tag="safety", apply=_r_wobble_fear),
    Rule(name="break_scare", tag="consequence", apply=_r_break_scare),
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


def rainbow_possible(light: LightMaker) -> bool:
    return light.refracts


def unsafe_attempt(perch: Perch) -> bool:
    return perch.unstable and perch.danger >= 2


def sensible_helps() -> list[AdultHelp]:
    return [h for h in HELPS.values() if h.sense >= SENSE_MIN]


def best_help() -> AdultHelp:
    return max(HELPS.values(), key=lambda h: h.sense)


def risk_score(light: LightMaker, perch: Perch) -> int:
    return light.fragility + perch.danger


def would_listen(inner_voice: str, patience: int, yorkie_alert: int) -> bool:
    bonus = 1 if inner_voice == "strong" else 0
    return patience + yorkie_alert + bonus >= 6


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    perch = sim.get("perch")
    maker = sim.get("maker")
    child.meters["climbing"] += 1
    perch.meters["wobble"] += 1
    if perch.attrs.get("danger", 0) + maker.attrs.get("fragility", 0) >= 4:
        maker.meters["fallen"] += 1
        maker.meters["broken"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": perch.meters["wobble"] >= THRESHOLD,
        "broken": maker.meters["broken"] >= THRESHOLD,
        "fear": child.memes["fear"],
    }


def play_setup(world: World, child: Entity, yorkie: Entity, theme: QuestTheme) -> None:
    child.memes["joy"] += 1
    yorkie.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {child.id} and a tiny yorkie named {yorkie.id} "
        f"turned {theme.room} into {theme.game_open}."
    )
    world.say(
        f"{theme.titles} -- that was what {child.id} called them when a quest felt big."
    )


def find_rainbow(world: World, child: Entity, yorkie: Entity,
                 maker_cfg: LightMaker, theme: QuestTheme) -> None:
    world.say(
        f"Then a patch of color slid across the floor like a dropped jewel. "
        f"It came from {maker_cfg.phrase} on {maker_cfg.perch_place}."
    )
    world.say(
        f"{yorkie.id} bounced after the colors, paws tapping fast, while {child.id} "
        f"gasped. \"It's {theme.treasure_name}!\" {child.pronoun()} whispered."
    )
    world.say(
        f"The colors were not magic at all, though they felt magical. "
        f"{maker_cfg.explanation}"
    )


def need_reach(world: World, child: Entity, maker_cfg: LightMaker, perch_cfg: Perch) -> None:
    child.memes["desire"] += 1
    world.say(
        f"But the rainbow came from high up, and {child.id} could not reach "
        f"{maker_cfg.phrase} from the floor."
    )
    world.say(
        f"{child.pronoun().capitalize()} looked at {perch_cfg.phrase} nearby and "
        f"thought of a quick way up."
    )


def inner_monologue(world: World, child: Entity, maker_cfg: LightMaker, perch_cfg: Perch) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_broken"] = pred["broken"]
    world.facts["predicted_wobble"] = pred["wobble"]
    child.memes["thinking"] += 1
    extra = ""
    if pred["broken"]:
        extra = (
            f" If {child.pronoun()} climbed and it tipped, {maker_cfg.label} might fall "
            f"and break with a sharp crash."
        )
    world.say(
        f'Inside, {child.id} had a small, honest thought: '
        f'"I want the rainbow now, but {perch_cfg.phrase} looks {perch_cfg.wobble_word}. '
        f'Maybe the brave thing is not the fastest thing."{extra}'
    )


def bark_warning(world: World, yorkie: Entity, perch_cfg: Perch) -> None:
    yorkie.memes["alarm"] += 1
    world.say(
        f"{yorkie.id} set both front paws on {perch_cfg.label} and gave one quick bark, "
        f"as if even the little dog did not trust it."
    )


def climb_attempt(world: World, child: Entity, yorkie: Entity,
                  maker: Entity, perch: Entity, perch_cfg: Perch) -> None:
    child.meters["climbing"] += 1
    perch.meters["wobble"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Wanting the treasure too much, {child.id} put one foot on {perch_cfg.label}. "
        f"The {perch_cfg.label} gave a small {perch_cfg.wobble_word} shake."
    )
    if child.memes["fear"] >= THRESHOLD:
        world.say(
            f"{yorkie.id} spun in a tight worried circle, and {child.id}'s heart "
            f"bumped hard once."
        )


def near_accident(world: World, child: Entity, maker: Entity, maker_cfg: LightMaker) -> None:
    maker.meters["fallen"] += 1
    maker.meters["broken"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Before {child.id} could steady up, {maker_cfg.phrase.capitalize()} slid to the edge "
        f"and fell. It hit the rug with a bright, sad clink."
    )
    world.say(
        f"The rainbow vanished at once, and the room felt suddenly plain."
    )


def step_down(world: World, child: Entity) -> None:
    child.meters["climbing"] = 0.0
    child.memes["choice"] += 1
    world.say(
        f"{child.id} climbed back down right away, cheeks hot but feet safe on the floor."
    )


def call_adult(world: World, child: Entity, adult: Entity) -> None:
    child.memes["trust"] += 1
    world.say(
        f"Then {child.pronoun()} called, \"{adult.label_word.capitalize()}, can you help us with the rainbow treasure?\""
    )


def adult_rescue(world: World, adult: Entity, child: Entity, yorkie: Entity,
                 maker: Entity, maker_cfg: LightMaker, help_cfg: AdultHelp) -> None:
    child.memes["relief"] += 1
    child.memes["love"] += 1
    child.memes["lesson"] += 1
    yorkie.memes["relief"] += 1
    maker.meters["shared_safely"] += 1
    world.say(
        f"{adult.label_word.capitalize()} came in smiling and {help_cfg.text.format(maker=maker_cfg.label)}."
    )
    world.say(
        f"Soon the colors danced low enough for small hands and one very eager yorkie nose."
    )


def explain_refraction(world: World, adult: Entity, maker_cfg: LightMaker) -> None:
    world.say(
        f'"Those colors come from refraction," {adult.label_word} said. '
        f'"Light bends when it passes through {maker_cfg.label}, and that bend lets the colors spread out where you can see them."'
    )


def gentle_lesson(world: World, adult: Entity, child: Entity) -> None:
    world.say(
        f"{adult.label_word.capitalize()} knelt beside {child.id}. "
        f'"I am glad you stopped and asked for help," {adult.pronoun()} said softly. '
        f'"A real helper cares more about safety than speed."'
    )


def ending_image(world: World, child: Entity, yorkie: Entity, theme: QuestTheme) -> None:
    child.memes["joy"] += 1
    yorkie.memes["joy"] += 1
    world.say(
        f"{child.id} held the little rainbow on {child.pronoun('possessive')} sleeve while "
        f"{yorkie.id} pounced on the colors that kept slipping away."
    )
    world.say(theme.ending_line)


THEMES = {
    "sun_quest": QuestTheme(
        id="sun_quest",
        room="the sitting room",
        game_open="a captain's map room",
        titles="Captain and First Mate",
        treasure_name="the Sun Captain's rainbow coin",
        ending_line="So the quest ended with bright colors on the floor, a safe heart in the chest, and a lesson that shone longer than the rainbow.",
        tags={"quest", "pirate"},
    ),
    "window_cove": QuestTheme(
        id="window_cove",
        room="the front room",
        game_open="a tiny pirate cove",
        titles="Scout Captain and Barking Mate",
        treasure_name="the window cove's hidden gem",
        ending_line="And there in the warm window light, the brave explorers learned that the safest path can still lead to treasure.",
        tags={"quest", "pirate"},
    ),
}

LIGHTS = {
    "prism": LightMaker(
        id="prism",
        label="a glass prism",
        phrase="a glass prism",
        perch_place="the sunny windowsill",
        explanation="It was refraction: sunlight bending as it passed through the clear glass and opening into stripes of red, gold, green, and blue.",
        color_line="stripes of color",
        refracts=True,
        fragility=2,
        tags={"prism", "refraction", "glass"},
    ),
    "water_glass": LightMaker(
        id="water_glass",
        label="a water glass",
        phrase="a water glass",
        perch_place="the mantel by the window",
        explanation="It was refraction: sunlight passing through the clear water and curved glass, bending enough to spill soft colors over the floorboards.",
        color_line="soft colors",
        refracts=True,
        fragility=2,
        tags={"water", "refraction", "glass"},
    ),
    "crystal_bowl": LightMaker(
        id="crystal_bowl",
        label="a crystal bowl",
        phrase="a crystal bowl",
        perch_place="the high side table",
        explanation="It was refraction: the sun bent through the clear crystal and scattered bright colors like tiny flags across the room.",
        color_line="bright colors",
        refracts=True,
        fragility=3,
        tags={"crystal", "refraction", "glass"},
    ),
    "mirror": LightMaker(
        id="mirror",
        label="a small mirror",
        phrase="a small mirror",
        perch_place="the shelf above the sofa",
        explanation="A mirror can bounce light back, but by itself it does not make this kind of rainbow spread.",
        color_line="plain reflected light",
        refracts=False,
        fragility=1,
        tags={"mirror"},
    ),
}

PERCHES = {
    "rolling_stool": Perch(
        id="rolling_stool",
        label="rolling stool",
        phrase="the rolling stool",
        wobble_word="wobbly",
        danger=3,
        unstable=True,
        tags={"stool", "unsafe"},
    ),
    "toy_chest": Perch(
        id="toy_chest",
        label="toy chest",
        phrase="the toy chest",
        wobble_word="slippery",
        danger=2,
        unstable=True,
        tags={"chest", "unsafe"},
    ),
    "books": Perch(
        id="books",
        label="stack of books",
        phrase="the stack of books",
        wobble_word="tippy",
        danger=3,
        unstable=True,
        tags={"books", "unsafe"},
    ),
    "step_stool": Perch(
        id="step_stool",
        label="step stool",
        phrase="the step stool",
        wobble_word="steady",
        danger=1,
        unstable=False,
        tags={"stool", "safe"},
    ),
}

HELPS = {
    "lift_down": AdultHelp(
        id="lift_down",
        sense=3,
        text="lifted the {maker} down to the carpet and stayed close while the light moved through it",
        qa_text="lifted the object down and let the child see the colors safely",
        tags={"ask_help", "safe"},
    ),
    "table_setup": AdultHelp(
        id="table_setup",
        sense=3,
        text="set the {maker} on the low table in a stripe of sun, where everyone could watch the colors together",
        qa_text="moved the object to a low table in the sunshine",
        tags={"ask_help", "safe", "table"},
    ),
    "hold_child": AdultHelp(
        id="hold_child",
        sense=2,
        text="held {maker} carefully and showed how the colors slid when it turned in the light",
        qa_text="held the object and showed the colors from a safe height",
        tags={"ask_help", "safe"},
    ),
    "ignore": AdultHelp(
        id="ignore",
        sense=1,
        text="told the child to stop fussing and walked away from the room",
        qa_text="did not help at all",
        tags={"poor_help"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]
YORKIE_NAMES = ["Pip", "Button", "Momo", "Peaches", "Nibbles", "Teddy"]
TRAITS = ["careful", "curious", "thoughtful", "brave", "eager"]
INNER_VOICES = ["gentle", "strong"]

KNOWLEDGE = {
    "refraction": [(
        "What is refraction?",
        "Refraction is when light bends as it moves through something clear, like glass or water. When the bend is just right, the colors in the light can spread out so you can see them."
    )],
    "prism": [(
        "What does a prism do?",
        "A prism bends light. That bending can split white light into many colors."
    )],
    "glass": [(
        "Why can glass objects be dangerous if they fall?",
        "Glass can break into sharp pieces. That is why children should ask a grown-up for help instead of reaching high glass things alone."
    )],
    "ask_help": [(
        "Why is asking a grown-up for help a brave choice?",
        "It is brave because you stop, think, and choose safety instead of doing the quickest thing. Asking for help can keep people and objects safe."
    )],
    "unsafe": [(
        "Why is it unsafe to stand on wobbly things?",
        "Wobbly things can tip or slide. That can make you fall or knock other things down."
    )],
    "table": [(
        "Why is a low table safer than climbing?",
        "A low table lets you see and touch something without reaching up high. When your feet stay on the floor, you are much steadier."
    )],
}
KNOWLEDGE_ORDER = ["refraction", "prism", "glass", "ask_help", "unsafe", "table"]


@dataclass
class StoryParams:
    theme: str
    light: str
    perch: str
    help_method: str
    child_name: str
    child_gender: str
    yorkie_name: str
    adult_type: str
    child_trait: str
    inner_voice: str
    patience: int = 3
    yorkie_alert: int = 2
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        theme="sun_quest",
        light="prism",
        perch="rolling_stool",
        help_method="table_setup",
        child_name="Lily",
        child_gender="girl",
        yorkie_name="Pip",
        adult_type="mother",
        child_trait="curious",
        inner_voice="strong",
        patience=4,
        yorkie_alert=2,
    ),
    StoryParams(
        theme="window_cove",
        light="water_glass",
        perch="toy_chest",
        help_method="lift_down",
        child_name="Ben",
        child_gender="boy",
        yorkie_name="Button",
        adult_type="father",
        child_trait="thoughtful",
        inner_voice="gentle",
        patience=4,
        yorkie_alert=3,
    ),
    StoryParams(
        theme="sun_quest",
        light="crystal_bowl",
        perch="books",
        help_method="hold_child",
        child_name="Maya",
        child_gender="girl",
        yorkie_name="Teddy",
        adult_type="grandmother",
        child_trait="eager",
        inner_voice="strong",
        patience=3,
        yorkie_alert=3,
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for light_id, light in LIGHTS.items():
            for perch_id, perch in PERCHES.items():
                if rainbow_possible(light) and unsafe_attempt(perch):
                    combos.append((theme_id, light_id, perch_id))
    return combos


def explain_rejection(light: LightMaker, perch: Perch) -> str:
    if not rainbow_possible(light):
        return (
            f"(No story: {light.phrase} can reflect light, but it does not make the rainbow "
            f"effect needed here. Pick a prism, water glass, or crystal bowl so refraction can happen.)"
        )
    if not unsafe_attempt(perch):
        return (
            f"(No story: {perch.phrase} is not wobbly enough to create the safety problem this quest needs. "
            f"Pick a rolling stool, toy chest, or stack of books.)"
        )
    return "(No story: this combination does not form a good quest problem.)"


def explain_help(help_id: str) -> str:
    help_cfg = HELPS[help_id]
    better = ", ".join(sorted(h.id for h in sensible_helps()))
    return (
        f"(Refusing help_method '{help_id}': it scores too low on common sense "
        f"(sense={help_cfg.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_listen(params.inner_voice, params.patience, params.yorkie_alert):
        return "safe_ask"
    return "near_break"


def tell(theme: QuestTheme, maker_cfg: LightMaker, perch_cfg: Perch, help_cfg: AdultHelp,
         child_name: str = "Lily", child_gender: str = "girl", yorkie_name: str = "Pip",
         adult_type: str = "mother", child_trait: str = "curious", inner_voice: str = "strong",
         patience: int = 3, yorkie_alert: int = 2) -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[child_trait],
        attrs={"patience": patience, "inner_voice": inner_voice},
    ))
    yorkie = world.add(Entity(
        id="yorkie",
        kind="character",
        type="dog",
        label=yorkie_name,
        role="yorkie",
        attrs={"alert": yorkie_alert, "breed": "yorkie"},
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=adult_type,
        label="the grown-up",
        role="adult",
    ))
    maker = world.add(Entity(
        id="maker",
        type="object",
        label=maker_cfg.label,
        phrase=maker_cfg.phrase,
        attrs={"fragility": maker_cfg.fragility},
    ))
    perch = world.add(Entity(
        id="perch",
        type="object",
        label=perch_cfg.label,
        phrase=perch_cfg.phrase,
        attrs={"danger": perch_cfg.danger},
    ))

    play_setup(world, child, yorkie, theme)
    find_rainbow(world, child, yorkie, maker_cfg, theme)
    need_reach(world, child, maker_cfg, perch_cfg)

    world.para()
    inner_monologue(world, child, maker_cfg, perch_cfg)
    bark_warning(world, yorkie, perch_cfg)

    listened = would_listen(inner_voice, patience, yorkie_alert)
    world.facts["listened"] = listened

    if listened:
        step_down(world, child)
        call_adult(world, child, adult)
        world.para()
        adult_rescue(world, adult, child, yorkie, maker, maker_cfg, help_cfg)
        explain_refraction(world, adult, maker_cfg)
        gentle_lesson(world, adult, child)
        world.para()
        ending_image(world, child, yorkie, theme)
        outcome = "safe_ask"
    else:
        climb_attempt(world, child, yorkie, maker, perch, perch_cfg)
        world.para()
        near_accident(world, child, maker, maker_cfg)
        step_down(world, child)
        call_adult(world, child, adult)
        world.say(
            f"{adult.label_word.capitalize()} hurried in, checked that nobody was hurt, and gave {child.label} a long hug before picking up the pieces."
        )
        world.say(
            f'"Next time," {adult.pronoun()} said gently, "we ask first. Treasure is never worth a tumble."'
        )
        world.para()
        world.say(
            f"Later, {adult.label_word} brought out a safer rainbow toy for the window, and {child.label} let {yorkie.label} chase the new colors across the rug."
        )
        world.say(
            "The quest still ended with light, but now the lesson was clearer than before: wanting something fast is not the same as choosing well."
        )
        outcome = "near_break"

    world.facts.update(
        child=child,
        yorkie=yorkie,
        adult=adult,
        theme=theme,
        maker_cfg=maker_cfg,
        maker=maker,
        perch_cfg=perch_cfg,
        perch=perch,
        help_cfg=help_cfg,
        outcome=outcome,
        refraction=maker_cfg.refracts,
        broke=maker.meters["broken"] >= THRESHOLD,
        moral="ask_for_help",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    yorkie = f["yorkie"]
    maker_cfg = f["maker_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a child-facing quest story in a pirate-tale style that includes the words '
        f'"yorkie" and "refraction". The hero is {child.label} and the little dog is {yorkie.label}.'
    )
    if outcome == "safe_ask":
        return [
            base,
            f"Tell a story where a child and a yorkie chase a rainbow made by {maker_cfg.label}, and an inner monologue helps the child choose safety over speed.",
            "Write a gentle moral tale where the treasure quest turns on one honest thought inside the hero's head, and the happy ending comes from asking a grown-up for help.",
        ]
    return [
        base,
        f"Tell a cautionary but gentle story where a child and a yorkie reach for a rainbow made by {maker_cfg.label}, ignore the safer choice for one moment, and learn the lesson after a near accident.",
        "Write a quest story with inner monologue, a clear moral value, and a final safe resolution after something almost goes wrong.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    yorkie = f["yorkie"]
    adult = f["adult"]
    maker_cfg = f["maker_cfg"]
    perch_cfg = f["perch_cfg"]
    help_cfg = f["help_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, a child on a little treasure quest, and {yorkie.label}, a tiny yorkie who follows every bright thing. A grown-up helps them when the quest turns risky."
        ),
        (
            "What was the treasure in the story?",
            f"The treasure was a patch of rainbow light on the floor. It came from refraction, with sunlight bending through {maker_cfg.phrase} and spreading into colors."
        ),
        (
            f"Why did {child.label} think about climbing?",
            f"The rainbow came from high up, so {child.label} could not reach the object from the floor. {child.pronoun('subject').capitalize()} wanted the treasure quickly and noticed {perch_cfg.phrase} nearby."
        ),
        (
            "What was the inner monologue about?",
            f"{child.label} told {child.pronoun('object')}self that wanting something right away was not the same as making a brave choice. The thought was about safety, patience, and whether the quick path might make the object fall."
        ),
    ]
    if f["outcome"] == "safe_ask":
        qa.extend([
            (
                f"How did {child.label} solve the problem?",
                f"{child.label} climbed down from the idea instead of climbing up on {perch_cfg.phrase}, then called for {adult.label_word}'s help. {adult.label_word.capitalize()} {help_cfg.qa_text}, so the quest could go on safely."
            ),
            (
                "What moral value did the story teach?",
                "It taught that asking for help can be the bravest choice. The story shows that real courage means caring more about safety than about being first."
            ),
            (
                f"How did the story end?",
                f"It ended with {child.label} and the yorkie enjoying the rainbow together on the floor. The ending image proves what changed, because the treasure stayed bright and everyone stayed safe."
            ),
        ])
    else:
        qa.extend([
            (
                "What almost went wrong?",
                f"{maker_cfg.phrase.capitalize()} fell when the risky reach went badly, and the rainbow disappeared. The danger came from using {perch_cfg.phrase}, which was too unsteady for reaching a fragile object."
            ),
            (
                "Was anyone hurt?",
                f"No one was hurt, and that is why the grown-up's first response was relief. But the scare was enough to teach the lesson before something worse happened."
            ),
            (
                "What moral value did the story teach?",
                "It taught that wanting something badly does not make an unsafe shortcut wise. The child learns that stopping early and asking for help would have protected both people and the treasure."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"refraction", "ask_help"}
    maker_cfg = world.facts["maker_cfg"]
    perch_cfg = world.facts["perch_cfg"]
    help_cfg = world.facts["help_cfg"]
    tags |= maker_cfg.tags
    if "unsafe" in perch_cfg.tags:
        tags.add("unsafe")
    if "table" in help_cfg.tags:
        tags.add("table")
    if "glass" in maker_cfg.tags:
        tags.add("glass")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
hazard(L, P) :- refracts(L), unstable(P), danger(P, D), D >= 2.
valid(T, L, P) :- theme(T), light(L), perch(P), hazard(L, P).
sensible_help(H) :- help(H), sense(H, S), sense_min(M), S >= M.

% --- outcome inference -----------------------------------------------------
listen_score(P + A + B) :- patience(P), yorkie_alert(A), inner_bonus(B).
inner_bonus(1) :- inner_voice(strong).
inner_bonus(0) :- not inner_voice(strong).
safe_ask :- listen_score(S), S >= 6.
outcome(safe_ask) :- safe_ask.
outcome(near_break) :- not safe_ask.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for light_id, light in LIGHTS.items():
        lines.append(asp.fact("light", light_id))
        if light.refracts:
            lines.append(asp.fact("refracts", light_id))
        lines.append(asp.fact("fragility", light_id, light.fragility))
    for perch_id, perch in PERCHES.items():
        lines.append(asp.fact("perch", perch_id))
        if perch.unstable:
            lines.append(asp.fact("unstable", perch_id))
        lines.append(asp.fact("danger", perch_id, perch.danger))
    for help_id, help_cfg in HELPS.items():
        lines.append(asp.fact("help", help_id))
        lines.append(asp.fact("sense", help_id, help_cfg.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_helps() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_help/1."))
    return sorted(h for (h,) in asp.atoms(model, "sensible_help"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("patience", params.patience),
        asp.fact("yorkie_alert", params.yorkie_alert),
        asp.fact("inner_voice", params.inner_voice),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_helps = set(asp_sensible_helps())
    python_helps = {h.id for h in sensible_helps()}
    if clingo_helps == python_helps:
        print(f"OK: sensible helps match ({sorted(clingo_helps)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible helps: clingo={sorted(clingo_helps)} python={sorted(python_helps)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            continue
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story in smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a yorkie, a rainbow quest, refraction, and the brave choice to ask for help."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--help-method", choices=HELPS, dest="help_method")
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--yorkie-name")
    ap.add_argument("--adult-type", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--child-trait", choices=TRAITS)
    ap.add_argument("--inner-voice", choices=INNER_VOICES, dest="inner_voice")
    ap.add_argument("--patience", type=int, choices=[2, 3, 4, 5])
    ap.add_argument("--yorkie-alert", type=int, choices=[1, 2, 3], dest="yorkie_alert")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.light and not LIGHTS[args.light].refracts:
        perch = PERCHES[args.perch] if args.perch else next(iter(PERCHES.values()))
        raise StoryError(explain_rejection(LIGHTS[args.light], perch))
    if args.perch and not unsafe_attempt(PERCHES[args.perch]):
        light = LIGHTS[args.light] if args.light else next(iter(l for l in LIGHTS.values() if l.refracts))
        raise StoryError(explain_rejection(light, PERCHES[args.perch]))
    if args.help_method and HELPS[args.help_method].sense < SENSE_MIN:
        raise StoryError(explain_help(args.help_method))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.light is None or combo[1] == args.light)
        and (args.perch is None or combo[2] == args.perch)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, light_id, perch_id = rng.choice(sorted(combos))
    help_method = args.help_method or rng.choice(sorted(h.id for h in sensible_helps()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    yorkie_name = args.yorkie_name or rng.choice(YORKIE_NAMES)
    adult_type = args.adult_type or rng.choice(["mother", "father", "grandmother"])
    child_trait = args.child_trait or rng.choice(TRAITS)
    inner_voice = args.inner_voice or rng.choice(INNER_VOICES)
    patience = args.patience if args.patience is not None else rng.choice([2, 3, 4, 5])
    yorkie_alert = args.yorkie_alert if args.yorkie_alert is not None else rng.choice([1, 2, 3])

    return StoryParams(
        theme=theme_id,
        light=light_id,
        perch=perch_id,
        help_method=help_method,
        child_name=child_name,
        child_gender=child_gender,
        yorkie_name=yorkie_name,
        adult_type=adult_type,
        child_trait=child_trait,
        inner_voice=inner_voice,
        patience=patience,
        yorkie_alert=yorkie_alert,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"Unknown theme: {params.theme}")
    if params.light not in LIGHTS:
        raise StoryError(f"Unknown light: {params.light}")
    if params.perch not in PERCHES:
        raise StoryError(f"Unknown perch: {params.perch}")
    if params.help_method not in HELPS:
        raise StoryError(f"Unknown help method: {params.help_method}")
    if params.help_method not in {h.id for h in sensible_helps()}:
        raise StoryError(explain_help(params.help_method))
    if not rainbow_possible(LIGHTS[params.light]) or not unsafe_attempt(PERCHES[params.perch]):
        raise StoryError(explain_rejection(LIGHTS[params.light], PERCHES[params.perch]))

    world = tell(
        theme=THEMES[params.theme],
        maker_cfg=LIGHTS[params.light],
        perch_cfg=PERCHES[params.perch],
        help_cfg=HELPS[params.help_method],
        child_name=params.child_name,
        child_gender=params.child_gender,
        yorkie_name=params.yorkie_name,
        adult_type=params.adult_type,
        child_trait=params.child_trait,
        inner_voice=params.inner_voice,
        patience=params.patience,
        yorkie_alert=params.yorkie_alert,
    )
    return StorySample(
        params=params,
        story=world.render().replace("child", params.child_name),
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
        print(asp_program("", "#show valid/3.\n#show sensible_help/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible helps: {', '.join(asp_sensible_helps())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, light, perch) combos:\n")
        for theme_id, light_id, perch_id in combos:
            print(f"  {theme_id:12} {light_id:12} {perch_id}")
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
            header = f"### {p.child_name} & {p.yorkie_name}: {p.light} with {p.perch} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
