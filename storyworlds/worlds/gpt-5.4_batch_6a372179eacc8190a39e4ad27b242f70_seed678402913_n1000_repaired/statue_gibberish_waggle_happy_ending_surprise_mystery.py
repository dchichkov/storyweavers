#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/statue_gibberish_waggle_happy_ending_surprise_mystery.py
===================================================================================

A standalone story world for a superhero-style mystery: a child hero notices a
statue that seems to waggle and speak gibberish, follows state-grounded clues,
solves the mystery, and gets a happy surprise at the end.

The world is intentionally small and constraint-checked. A mystery is only
generated when:

- the chosen statue can physically hide the chosen culprit, and
- the chosen solution actually fits that culprit.

The prose is driven by simulated state: hidden causes make the statue move and
sound strange; clue-finding updates knowledge; the right rescue/fix changes the
world; and the ending image proves the danger and confusion are gone.

Run it
------
    python storyworlds/worlds/gpt-5.4/statue_gibberish_waggle_happy_ending_surprise_mystery.py
    python storyworlds/worlds/gpt-5.4/statue_gibberish_waggle_happy_ending_surprise_mystery.py --all
    python storyworlds/worlds/gpt-5.4/statue_gibberish_waggle_happy_ending_surprise_mystery.py --statue comet_captain --culprit parrot --solution open_hatch
    python storyworlds/worlds/gpt-5.4/statue_gibberish_waggle_happy_ending_surprise_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/statue_gibberish_waggle_happy_ending_surprise_mystery.py --verify
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
        female = {"girl", "mother", "woman", "mayor_woman"}
        male = {"boy", "father", "man", "mayor_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def title_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Statue:
    id: str
    label: str
    place: str
    phrase: str
    moving_part: str
    hollow: str
    supports: set[str] = field(default_factory=set)
    clue_spot: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    kind: str
    noise: str
    gibberish: str
    clue: str
    clue_noun: str
    needs: str
    solved_text: str
    after_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    works_for: set[str] = field(default_factory=set)
    action: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    statue: str
    culprit: str
    solution: str
    hero_name: str
    hero_gender: str
    sidekick_name: str
    sidekick_gender: str
    mayor_gender: str
    trait: str
    power_style: str
    seed: Optional[int] = None


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
        new = World()
        new.entities = copy.deepcopy(self.entities)
        new.fired = set(self.fired)
        new.paragraphs = [[]]
        new.facts = copy.deepcopy(self.facts)
        return new


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_hidden_cause(world: World) -> list[str]:
    statue = world.get("statue")
    culprit = world.get("culprit")
    if culprit.attrs.get("hidden_in") != "statue" or culprit.meters["active"] < THRESHOLD:
        return []
    sig = ("hidden_cause", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    statue.meters["waggle"] += 1
    statue.meters["noise"] += 1
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    hero.memes["curiosity"] += 1
    sidekick.memes["wonder"] += 1
    if culprit.type == "animal":
        culprit.memes["distress"] += 1
    return []


def _r_clue_found(world: World) -> list[str]:
    hero = world.get("hero")
    culprit = world.get("culprit")
    if hero.meters["inspected"] < THRESHOLD or culprit.meters["active"] < THRESHOLD:
        return []
    sig = ("clue", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["clue_found"] += 1
    hero.attrs["clue_text"] = culprit.attrs.get("clue_text", "")
    return []


def _r_resolved(world: World) -> list[str]:
    statue = world.get("statue")
    culprit = world.get("culprit")
    if culprit.meters["helped"] < THRESHOLD:
        return []
    sig = ("resolved", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    culprit.meters["active"] = 0.0
    culprit.memes["distress"] = 0.0
    statue.meters["waggle"] = 0.0
    statue.meters["noise"] = 0.0
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="hidden_cause", tag="physical", apply=_r_hidden_cause),
    Rule(name="clue_found", tag="knowledge", apply=_r_clue_found),
    Rule(name="resolved", tag="physical", apply=_r_resolved),
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


STATUES = {
    "comet_captain": Statue(
        id="comet_captain",
        label="Captain Comet statue",
        place="the sun-bright plaza",
        phrase="a tall silver statue of Captain Comet pointing at the sky",
        moving_part="the star badge on its chest",
        hollow="a service hatch in the pedestal",
        supports={"parrot", "radio", "mini_robot"},
        clue_spot="the little vent behind the pedestal",
        tags={"statue", "plaza"},
    ),
    "thunder_pup": Statue(
        id="thunder_pup",
        label="Thunder Pup statue",
        place="the park gate",
        phrase="a giant bronze statue of Thunder Pup with one brave paw raised",
        moving_part="the metal cape by its shoulders",
        hollow="a round door under the raised paw",
        supports={"parrot", "radio"},
        clue_spot="the seam under the raised paw",
        tags={"statue", "park"},
    ),
    "sky_shield": Statue(
        id="sky_shield",
        label="Sky Shield statue",
        place="the museum steps",
        phrase="a blue stone statue of Sky Shield holding a huge round shield",
        moving_part="the edge of the shield",
        hollow="a narrow panel in the back",
        supports={"radio", "mini_robot"},
        clue_spot="a slit behind the shield strap",
        tags={"statue", "museum"},
    ),
}

CULPRITS = {
    "parrot": Culprit(
        id="parrot",
        label="a lost green parrot",
        kind="animal",
        noise="a scratchy voice",
        gibberish='"Zoom-zam! Cracker-boom! Zip!"',
        clue="a bright green feather",
        clue_noun="feather",
        needs="space",
        solved_text="lifted the hatch just enough for a fluttering green parrot to hop out",
        after_text="The parrot blinked, ruffled its feathers, and said a much clearer hello.",
        tags={"parrot", "animal", "gibberish"},
    ),
    "radio": Culprit(
        id="radio",
        label="a buzzing walkie-talkie",
        kind="device",
        noise="a crackly speaker",
        gibberish='"Bzzz-krrt! Hero unit wobble-wobble!"',
        clue="a blinking red light",
        clue_noun="light",
        needs="slot",
        solved_text="reached inside and switched off a lost walkie-talkie that had been rattling around",
        after_text="At once the crackle stopped, and the plaza sounded normal again.",
        tags={"radio", "device", "gibberish"},
    ),
    "mini_robot": Culprit(
        id="mini_robot",
        label="a tiny helper robot",
        kind="device",
        noise="a tinny little voice",
        gibberish='"Beep-zorp! Waggle mode! Hero-noodle!"',
        clue="tiny wheel marks and a weak blue blink",
        clue_noun="wheel marks",
        needs="panel",
        solved_text="opened the back panel and found a tiny helper robot whose battery had gone funny",
        after_text="When the hero pressed its reset button, the robot gave a neat salute instead of gibberish.",
        tags={"robot", "device", "gibberish"},
    ),
}

SOLUTIONS = {
    "open_hatch": Solution(
        id="open_hatch",
        label="open the hatch",
        works_for={"parrot", "radio"},
        action="used careful hands to open the hatch in the pedestal",
        qa_text="opened the statue's hatch and checked inside",
        tags={"hatch", "careful"},
    ),
    "follow_beep": Solution(
        id="follow_beep",
        label="follow the beeping panel",
        works_for={"radio", "mini_robot"},
        action="followed the strange beeping to the back panel and clicked it open",
        qa_text="followed the beeping to the panel and opened it",
        tags={"panel", "beep"},
    ),
    "calm_call": Solution(
        id="calm_call",
        label="make a calm hero call",
        works_for={"parrot"},
        action="cupped kind hands and made the soft hero call used at the bird rescue tent",
        qa_text="used a calm bird call to coax the hidden parrot out",
        tags={"animal", "kindness"},
    ),
    "reset_robot": Solution(
        id="reset_robot",
        label="reset the tiny robot",
        works_for={"mini_robot"},
        action="slid open the panel and pressed the little reset star on the machine inside",
        qa_text="opened the panel and reset the tiny robot",
        tags={"robot", "fix"},
    ),
}

POWER_STYLES = {
    "echo_ears": "super-hearing",
    "spark_eyes": "sparkly clue-eyes",
    "brave_brain": "a brave puzzle-brain",
}

GIRL_NAMES = ["Maya", "Lila", "Zoe", "Ava", "Nora", "Ruby", "Ella", "Ivy"]
BOY_NAMES = ["Max", "Leo", "Finn", "Eli", "Theo", "Sam", "Noah", "Jack"]
TRAITS = ["bold", "kind", "quick-thinking", "steady", "curious", "helpful"]


def culprit_fits(statue: Statue, culprit: Culprit) -> bool:
    return culprit.id in statue.supports


def solution_fits(culprit: Culprit, solution: Solution) -> bool:
    return culprit.id in solution.works_for


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for statue_id, statue in STATUES.items():
        for culprit_id, culprit in CULPRITS.items():
            if not culprit_fits(statue, culprit):
                continue
            for solution_id, solution in SOLUTIONS.items():
                if solution_fits(culprit, solution):
                    combos.append((statue_id, culprit_id, solution_id))
    return combos


def predict_mystery(statue: Statue, culprit: Culprit) -> dict:
    world = World()
    world.add(Entity(id="hero", kind="character", type="girl", label="hero"))
    world.add(Entity(id="sidekick", kind="character", type="boy", label="sidekick"))
    world.add(Entity(id="statue", kind="thing", type="statue", label=statue.label))
    world.add(Entity(
        id="culprit",
        kind="thing",
        type="animal" if culprit.kind == "animal" else "device",
        label=culprit.label,
        attrs={"hidden_in": "statue", "clue_text": culprit.clue},
    ))
    world.get("culprit").meters["active"] = 1
    propagate(world, narrate=False)
    return {
        "waggle": world.get("statue").meters["waggle"] >= THRESHOLD,
        "noise": world.get("statue").meters["noise"] >= THRESHOLD,
        "distress": world.get("culprit").memes["distress"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, sidekick: Entity, statue: Statue) -> None:
    world.say(
        f"{hero.id} zipped into {statue.place} wearing a red towel-cape and practicing {hero.attrs['power_style']}. "
        f"Beside {hero.pronoun('object')} trotted {sidekick.id}, the best sidewalk sidekick in town."
    )
    world.say(
        f"In the middle of the open space stood {statue.phrase}. Children usually waved at it on the way by."
    )


def mystery_appears(world: World, hero: Entity, sidekick: Entity, statue_cfg: Statue, culprit_cfg: Culprit) -> None:
    statue = world.get("statue")
    culprit = world.get("culprit")
    culprit.meters["active"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then something very odd happened. {statue_cfg.moving_part.capitalize()} gave a tiny waggle, "
        f"and from inside came {culprit_cfg.noise} saying {culprit_cfg.gibberish}"
    )
    world.say(
        f'{sidekick.id} grabbed {hero.pronoun("possessive")} cape. "A talking statue?" {sidekick.pronoun()} whispered.'
    )
    if culprit.memes["distress"] >= THRESHOLD:
        world.say(
            f"{hero.id} tipped {hero.pronoun('possessive')} head. The noise sounded silly, but it also sounded a little worried."
        )


def inspect(world: World, hero: Entity, statue_cfg: Statue) -> None:
    hero.meters["inspected"] += 1
    propagate(world, narrate=False)
    clue = hero.attrs.get("clue_text", "")
    world.say(
        f"{hero.id} used {hero.attrs['power_style']} and knelt near {statue_cfg.clue_spot}. "
        f"There {hero.pronoun()} found {clue}."
    )
    hero.memes["confidence"] += 1


def reason_out(world: World, hero: Entity, sidekick: Entity, culprit_cfg: Culprit) -> None:
    clue = hero.attrs.get("clue_text", culprit_cfg.clue)
    if culprit_cfg.id == "parrot":
        thought = "Something feathery must be stuck inside."
    elif culprit_cfg.id == "radio":
        thought = "That was not magic at all. It sounded like mixed-up radio talk."
    else:
        thought = "Those little marks belonged to wheels, not paws."
    world.say(
        f'"This is a mystery, not a monster," {hero.id} said. "{clue.capitalize()} is the clue. {thought}"'
    )
    sidekick.memes["trust"] += 1


def solve(world: World, hero: Entity, solution_cfg: Solution, culprit_cfg: Culprit) -> None:
    culprit = world.get("culprit")
    world.say(
        f"So {hero.id} {solution_cfg.action}, and {hero.pronoun()} {culprit_cfg.solved_text}."
    )
    culprit.meters["helped"] += 1
    propagate(world, narrate=False)
    world.say(culprit_cfg.after_text)


def celebrate(world: World, hero: Entity, sidekick: Entity, mayor: Entity, statue_cfg: Statue, culprit_cfg: Culprit) -> None:
    world.say(
        f"Soon {statue_cfg.moving_part} was still, the silly gibberish was gone, and the whole place felt brave and bright again."
    )
    if culprit_cfg.id == "parrot":
        world.say(
            f"The parrot hopped onto the statue, bobbed once, and this time said, \"Thank you, hero!\""
        )
    elif culprit_cfg.id == "radio":
        world.say(
            "A laughing mail carrier came running up and said the lost walkie-talkie belonged to the parade team."
        )
    else:
        world.say(
            "The tiny robot rolled a neat circle around the hero's shoes and projected one perfect gold star in the air."
        )
    world.para()
    mayor_word = "mayor"
    world.say(
        f"Just then the {mayor_word} stepped out from behind the snack cart with a velvet box. "
        f'"For solving today\'s mystery with a superhero heart," {mayor.pronoun()} said, "this city has a surprise for you."'
    )
    world.say(
        f"Inside was a shining Junior Mystery Hero badge shaped like a tiny star. "
        f"{hero.id} pinned it on, and {sidekick.id} danced in a proud little circle."
    )
    world.say(
        f"After that, whenever children passed {statue_cfg.label}, they smiled, because they knew even a spooky waggle could hide a problem that kindness and courage could solve."
    )


def tell(
    statue_cfg: Statue,
    culprit_cfg: Culprit,
    solution_cfg: Solution,
    hero_name: str,
    hero_gender: str,
    sidekick_name: str,
    sidekick_gender: str,
    mayor_gender: str,
    trait: str,
    power_style: str,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[trait],
        attrs={"power_style": POWER_STYLES[power_style]},
    ))
    sidekick = world.add(Entity(
        id=sidekick_name,
        kind="character",
        type=sidekick_gender,
        label=sidekick_name,
        role="sidekick",
        traits=["loyal"],
    ))
    mayor_type = "mayor_woman" if mayor_gender == "girl" else "mayor_man"
    mayor = world.add(Entity(
        id="Mayor",
        kind="character",
        type=mayor_type,
        label="the mayor",
        role="mayor",
    ))
    statue = world.add(Entity(
        id="statue",
        kind="thing",
        type="statue",
        label=statue_cfg.label,
        phrase=statue_cfg.phrase,
        attrs={"moving_part": statue_cfg.moving_part, "place": statue_cfg.place},
        tags=set(statue_cfg.tags),
    ))
    culprit = world.add(Entity(
        id="culprit",
        kind="thing",
        type="animal" if culprit_cfg.kind == "animal" else "device",
        label=culprit_cfg.label,
        attrs={"hidden_in": "statue", "clue_text": culprit_cfg.clue},
        tags=set(culprit_cfg.tags),
    ))

    introduce(world, hero, sidekick, statue_cfg)
    world.para()
    mystery_appears(world, hero, sidekick, statue_cfg, culprit_cfg)
    inspect(world, hero, statue_cfg)
    reason_out(world, hero, sidekick, culprit_cfg)
    world.para()
    solve(world, hero, solution_cfg, culprit_cfg)
    celebrate(world, hero, sidekick, mayor, statue_cfg, culprit_cfg)

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        mayor=mayor,
        statue_cfg=statue_cfg,
        culprit_cfg=culprit_cfg,
        solution_cfg=solution_cfg,
        clue=hero.attrs.get("clue_text", culprit_cfg.clue),
        solved=world.get("culprit").meters["helped"] >= THRESHOLD,
        calm=world.get("statue").meters["waggle"] < THRESHOLD,
        surprise_badge=True,
    )
    return world


def explain_rejection(statue: Statue, culprit: Culprit, solution: Optional[Solution] = None) -> str:
    if not culprit_fits(statue, culprit):
        return (
            f"(No story: {statue.label} cannot reasonably hide {culprit.label}. "
            f"The mystery needs a statue whose hollow part can contain that culprit.)"
        )
    if solution is not None and not solution_fits(culprit, solution):
        return (
            f"(No story: the solution '{solution.label}' would not actually solve a mystery caused by {culprit.label}. "
            f"Pick a method that fits the real cause.)"
        )
    return "(No story: those options do not make a reasonable mystery.)"


def outcome_of(params: StoryParams) -> str:
    statue_cfg = STATUES[params.statue]
    culprit_cfg = CULPRITS[params.culprit]
    solution_cfg = SOLUTIONS[params.solution]
    if culprit_fits(statue_cfg, culprit_cfg) and solution_fits(culprit_cfg, solution_cfg):
        return "solved"
    return "invalid"


KNOWLEDGE = {
    "statue": [
        (
            "What is a statue?",
            "A statue is a figure made from stone or metal. It stands very still unless something outside or inside is making it move."
        )
    ],
    "parrot": [
        (
            "Why can a parrot sound like silly talk?",
            "Parrots can copy bits of words and sounds they hear. If they mix those sounds together, it can come out like funny gibberish."
        )
    ],
    "radio": [
        (
            "Why can a radio or walkie-talkie sound crackly?",
            "A radio can sound crackly when signals bump into each other or the battery is weak. Then the words can come out jumbled and hard to understand."
        )
    ],
    "robot": [
        (
            "Why might a tiny robot talk in gibberish?",
            "If a robot has a weak battery or a mixed-up program, its words can come out wrong. Fixing or resetting it can help it talk clearly again."
        )
    ],
    "mystery": [
        (
            "How do you solve a mystery?",
            "You look for clues, think carefully, and test the idea that makes the most sense. Good mystery solving uses a calm brain instead of a scared guess."
        )
    ],
    "badge": [
        (
            "What does a badge show?",
            "A badge is a small sign that honors a job or a brave deed. It shows that someone did something helpful and important."
        )
    ],
}
KNOWLEDGE_ORDER = ["statue", "parrot", "radio", "robot", "mystery", "badge"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    statue_cfg = f["statue_cfg"]
    culprit_cfg = f["culprit_cfg"]
    return [
        f'Write a superhero story for a 3-to-5-year-old that includes the words "statue," "gibberish," and "waggle," and ends happily.',
        f"Tell a mystery-to-solve story where {hero.id} notices {statue_cfg.label} move in a strange way, follows clues, and discovers {culprit_cfg.label}.",
        f"Write a bright, child-facing story about a young hero who hears gibberish from a statue, stays calm, solves the mystery, and gets a surprise reward.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    culprit_cfg = f["culprit_cfg"]
    statue_cfg = f["statue_cfg"]
    solution_cfg = f["solution_cfg"]
    clue = f["clue"]
    return [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child pretending to be a superhero, and {sidekick.id}, the sidekick who stayed close during the mystery."
        ),
        (
            "What made the mystery begin?",
            f"The mystery began when {statue_cfg.moving_part} gave a tiny waggle and a strange voice inside the statue spoke gibberish. That told {hero.id} something real was causing the spooky sound."
        ),
        (
            f"What clue helped {hero.id} solve the mystery?",
            f"The clue was {clue}. It mattered because it pointed toward {culprit_cfg.label} instead of magic, so {hero.id} could choose the right plan."
        ),
        (
            f"How did {hero.id} solve the mystery?",
            f"{hero.id} {solution_cfg.qa_text}. That worked because the real cause was {culprit_cfg.label}, and the plan matched the problem."
        ),
        (
            "How did the story end?",
            f"It ended happily because the statue stopped moving, the gibberish stopped, and everyone understood the mystery at last. Then the mayor surprised {hero.id} with a Junior Mystery Hero badge."
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    culprit_cfg = f["culprit_cfg"]
    tags = {"statue", "mystery", "badge"}
    if culprit_cfg.id == "parrot":
        tags.add("parrot")
    elif culprit_cfg.id == "radio":
        tags.add("radio")
    else:
        tags.add("robot")
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
        statue="comet_captain",
        culprit="parrot",
        solution="open_hatch",
        hero_name="Maya",
        hero_gender="girl",
        sidekick_name="Leo",
        sidekick_gender="boy",
        mayor_gender="girl",
        trait="kind",
        power_style="echo_ears",
    ),
    StoryParams(
        statue="sky_shield",
        culprit="mini_robot",
        solution="reset_robot",
        hero_name="Finn",
        hero_gender="boy",
        sidekick_name="Ruby",
        sidekick_gender="girl",
        mayor_gender="boy",
        trait="quick-thinking",
        power_style="brave_brain",
    ),
    StoryParams(
        statue="thunder_pup",
        culprit="radio",
        solution="open_hatch",
        hero_name="Ava",
        hero_gender="girl",
        sidekick_name="Max",
        sidekick_gender="boy",
        mayor_gender="girl",
        trait="steady",
        power_style="spark_eyes",
    ),
    StoryParams(
        statue="comet_captain",
        culprit="radio",
        solution="follow_beep",
        hero_name="Theo",
        hero_gender="boy",
        sidekick_name="Ivy",
        sidekick_gender="girl",
        mayor_gender="boy",
        trait="bold",
        power_style="echo_ears",
    ),
]


ASP_RULES = r"""
supports_culprit(S, C) :- statue(S), culprit(C), supports(S, C).
usable_solution(C, Sol) :- culprit(C), solution(Sol), works_for(Sol, C).
valid(S, C, Sol) :- supports_culprit(S, C), usable_solution(C, Sol).

outcome(solved) :- chosen_statue(S), chosen_culprit(C), chosen_solution(Sol),
                   valid(S, C, Sol).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for statue_id, statue in STATUES.items():
        lines.append(asp.fact("statue", statue_id))
        for culprit_id in sorted(statue.supports):
            lines.append(asp.fact("supports", statue_id, culprit_id))
    for culprit_id in CULPRITS:
        lines.append(asp.fact("culprit", culprit_id))
    for solution_id, solution in SOLUTIONS.items():
        lines.append(asp.fact("solution", solution_id))
        for culprit_id in sorted(solution.works_for):
            lines.append(asp.fact("works_for", solution_id, culprit_id))
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
        asp.fact("chosen_statue", params.statue),
        asp.fact("chosen_culprit", params.culprit),
        asp.fact("chosen_solution", params.solution),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "invalid"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(25):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during random param resolution for seed {seed}.")
            break
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome differences.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "statue" not in sample.story.lower():
            raise StoryError("smoke test story did not render expected content")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generation/emission succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a young superhero solves a statue mystery with a happy surprise ending."
    )
    ap.add_argument("--statue", choices=STATUES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick-gender", choices=["girl", "boy"])
    ap.add_argument("--mayor-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--sidekick-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.statue and args.culprit:
        statue = STATUES[args.statue]
        culprit = CULPRITS[args.culprit]
        if not culprit_fits(statue, culprit):
            raise StoryError(explain_rejection(statue, culprit))
    if args.culprit and args.solution:
        culprit = CULPRITS[args.culprit]
        solution = SOLUTIONS[args.solution]
        if not solution_fits(culprit, solution):
            any_statue = STATUES[args.statue] if args.statue else next(iter(STATUES.values()))
            raise StoryError(explain_rejection(any_statue, culprit, solution))

    combos = [
        combo for combo in valid_combos()
        if (args.statue is None or combo[0] == args.statue)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.solution is None or combo[2] == args.solution)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    statue_id, culprit_id, solution_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    sidekick_gender = args.sidekick_gender or rng.choice(["girl", "boy"])
    mayor_gender = args.mayor_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    sidekick_name = args.sidekick_name or _pick_name(rng, sidekick_gender, avoid=hero_name)
    trait = rng.choice(TRAITS)
    power_style = rng.choice(sorted(POWER_STYLES))
    return StoryParams(
        statue=statue_id,
        culprit=culprit_id,
        solution=solution_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        sidekick_name=sidekick_name,
        sidekick_gender=sidekick_gender,
        mayor_gender=mayor_gender,
        trait=trait,
        power_style=power_style,
    )


def generate(params: StoryParams) -> StorySample:
    if params.statue not in STATUES:
        raise StoryError(f"(Unknown statue: {params.statue})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.solution not in SOLUTIONS:
        raise StoryError(f"(Unknown solution: {params.solution})")
    if params.power_style not in POWER_STYLES:
        raise StoryError(f"(Unknown power style: {params.power_style})")

    statue_cfg = STATUES[params.statue]
    culprit_cfg = CULPRITS[params.culprit]
    solution_cfg = SOLUTIONS[params.solution]
    if not culprit_fits(statue_cfg, culprit_cfg):
        raise StoryError(explain_rejection(statue_cfg, culprit_cfg))
    if not solution_fits(culprit_cfg, solution_cfg):
        raise StoryError(explain_rejection(statue_cfg, culprit_cfg, solution_cfg))

    world = tell(
        statue_cfg=statue_cfg,
        culprit_cfg=culprit_cfg,
        solution_cfg=solution_cfg,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        sidekick_name=params.sidekick_name,
        sidekick_gender=params.sidekick_gender,
        mayor_gender=params.mayor_gender,
        trait=params.trait,
        power_style=params.power_style,
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
        print(f"{len(combos)} compatible (statue, culprit, solution) combos:\n")
        for statue_id, culprit_id, solution_id in combos:
            print(f"  {statue_id:14} {culprit_id:10} {solution_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.culprit} in {p.statue} ({p.solution})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
