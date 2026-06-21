#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/calcium_problem_solving_pirate_tale.py
=================================================================

A standalone story world about two children playing pirates who hit a snag in
their treasure hunt, stop to think, and solve it by choosing a sensible ship
snack with calcium.

The tiny domain is intentionally narrow and child-facing:

- the children are pretending to be pirates indoors
- a treasure map gives a clue about a "calcium treasure"
- one child first grabs the wrong snack in a hurry
- the crew gets stuck, reads the clue carefully, and picks a calcium-rich food
- with the right plan, they finish the pirate task and find the treasure

The important change is not magic food. The world models a simple bit of problem
solving: the crew pauses, checks the clue, asks for help, and chooses a fitting
calcium snack before rushing on.

Run it
------
    python storyworlds/worlds/gpt-5.4/calcium_problem_solving_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/calcium_problem_solving_pirate_tale.py --quest mast --calcium-food cheese_cubes
    python storyworlds/worlds/gpt-5.4/calcium_problem_solving_pirate_tale.py --quest mast --calcium-food yogurt
    python storyworlds/worlds/gpt-5.4/calcium_problem_solving_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/calcium_problem_solving_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/calcium_problem_solving_pirate_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/calcium_problem_solving_pirate_tale.py --json
    python storyworlds/worlds/gpt-5.4/calcium_problem_solving_pirate_tale.py --verify
"""

from __future__ import annotations

import argparse
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Quest:
    id: str
    scene: str
    setup: str
    goal: str
    obstacle: str
    try_line: str
    solved_line: str
    ending_image: str
    needs_portable: bool = False
    allow_cup: bool = True
    allow_spoon: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class WrongSnack:
    id: str
    label: str
    phrase: str
    quick_claim: str
    mess: str
    in_cup: bool = False
    spoon_needed: bool = False
    has_calcium: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class CalciumFood:
    id: str
    label: str
    phrase: str
    serving: str
    portable: bool
    in_cup: bool
    spoon_needed: bool
    calcium: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_stall_from_wrong_choice(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    mate = world.get("mate")
    quest = world.get("quest")
    if quest.meters["attempt"] < THRESHOLD:
        return out
    if world.facts.get("chosen_food_has_calcium"):
        return out
    sig = ("stall", world.facts.get("wrong_snack_id", ""))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    quest.meters["stalled"] += 1
    hero.memes["frustration"] += 1
    mate.memes["concern"] += 1
    out.append("__stall__")
    return out


def _r_ready_from_calcium(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    mate = world.get("mate")
    if hero.meters["calcium"] < THRESHOLD:
        return out
    if not world.facts.get("food_fits_quest"):
        return out
    sig = ("ready", world.facts.get("calcium_food_id", ""))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["steady"] += 1
    hero.memes["confidence"] += 1
    mate.memes["relief"] += 1
    out.append("__ready__")
    return out


def _r_complete_quest(world: World) -> list[str]:
    out: list[str] = []
    quest = world.get("quest")
    treasure = world.get("treasure")
    if quest.meters["attempt"] < THRESHOLD:
        return out
    if world.get("hero").meters["steady"] < THRESHOLD:
        return out
    if not world.facts.get("clue_solved"):
        return out
    sig = ("complete", world.facts.get("quest_id", ""))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    quest.meters["done"] += 1
    treasure.meters["found"] += 1
    out.append("__complete__")
    return out


CAUSAL_RULES = [
    Rule(name="stall_from_wrong_choice", tag="problem", apply=_r_stall_from_wrong_choice),
    Rule(name="ready_from_calcium", tag="physical", apply=_r_ready_from_calcium),
    Rule(name="complete_quest", tag="resolution", apply=_r_complete_quest),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def food_fits_quest(quest: Quest, food: CalciumFood) -> bool:
    if not food.calcium:
        return False
    if quest.needs_portable and not food.portable:
        return False
    if not quest.allow_cup and food.in_cup:
        return False
    if not quest.allow_spoon and food.spoon_needed:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for quest_id, quest in QUESTS.items():
        for wrong_id, wrong in WRONG_SNACKS.items():
            if wrong.has_calcium:
                continue
            for food_id, food in CALCIUM_FOODS.items():
                if food_fits_quest(quest, food):
                    combos.append((quest_id, wrong_id, food_id))
    return combos


@dataclass
class StoryParams:
    quest: str
    wrong_snack: str
    calcium_food: str
    hero: str
    hero_gender: str
    mate: str
    mate_gender: str
    parent: str
    clue: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


QUESTS = {
    "mast": Quest(
        id="mast",
        scene="a stormy living-room sea",
        setup="The sofa was their ship, two couch cushions were the mast, a broom was the oar, and a blanket cave hid the treasure island.",
        goal="reach the top of the cushion mast and spot the silver shell",
        obstacle="the lookout climb needed a ship snack that could be finished before busy pirate hands started climbing",
        try_line="scrambled toward the cushion mast",
        solved_line="climbed the cushion mast with dry hands and a steady grin",
        ending_image="From the top, they saw the silver shell gleaming in the blanket cave like moonlight on water.",
        needs_portable=True,
        allow_cup=False,
        allow_spoon=False,
        tags={"pirates", "climb", "problem_solving"},
    ),
    "row": Quest(
        id="row",
        scene="a brave cardboard harbor",
        setup="The cardboard box was their boat, the rug was the sea, and a line of blue blocks marked the choppy reef.",
        goal="row past the blue-block reef to the treasure cove",
        obstacle="the crew could stop at the kitchen dock for a proper ship snack, but nothing sloshy or sticky could come aboard in the middle of rowing",
        try_line="pushed the cardboard boat off the rug shore",
        solved_line="rowed past the blue blocks in strong little strokes",
        ending_image="Their boat bumped the treasure cove, and the gold-paper coins shivered inside the shoebox chest.",
        needs_portable=False,
        allow_cup=True,
        allow_spoon=False,
        tags={"pirates", "rowing", "problem_solving"},
    ),
    "map": Quest(
        id="map",
        scene="a cozy captain's cabin",
        setup="The coffee table was the captain's desk, a rolled-up crayon map lay beside a toy compass, and a shoebox chest waited under the chair.",
        goal="solve the map riddle and open the chest",
        obstacle="the crew had time to sit and think, so any sensible calcium snack from the galley could work if they read the clue carefully",
        try_line="spread the crayon map across the table and tried to guess the answer",
        solved_line="traced the clue slowly and solved the riddle together",
        ending_image="The lid popped open, and bright paper jewels winked up at them from the chest.",
        needs_portable=False,
        allow_cup=True,
        allow_spoon=True,
        tags={"pirates", "map", "problem_solving"},
    ),
}

WRONG_SNACKS = {
    "gummy_rope": WrongSnack(
        id="gummy_rope",
        label="gummy rope",
        phrase="a long red gummy rope",
        quick_claim="This looks piratey enough!",
        mess="It was chewy and bright, but it was not the kind of ship snack the clue had asked for.",
        in_cup=False,
        spoon_needed=False,
        has_calcium=False,
        tags={"sweet", "snack"},
    ),
    "jam_bun": WrongSnack(
        id="jam_bun",
        label="jam bun",
        phrase="a sticky jam bun",
        quick_claim="This will make us fast!",
        mess="Jam shone on the bun, but sticky fingers were no help to a careful pirate crew.",
        in_cup=False,
        spoon_needed=False,
        has_calcium=False,
        tags={"sweet", "snack"},
    ),
    "fizz_pop": WrongSnack(
        id="fizz_pop",
        label="fizz pop",
        phrase="a bubbly cup of fizz pop",
        quick_claim="This sparkly drink must be captain food!",
        mess="The cup fizzed and tickled, but the map was asking for calcium, not bubbles.",
        in_cup=True,
        spoon_needed=False,
        has_calcium=False,
        tags={"drink", "sweet"},
    ),
}

CALCIUM_FOODS = {
    "cheese_cubes": CalciumFood(
        id="cheese_cubes",
        label="cheese cubes",
        phrase="a little bowl of cheese cubes",
        serving="nibbled the cheese cubes one by one",
        portable=True,
        in_cup=False,
        spoon_needed=False,
        calcium=True,
        tags={"calcium", "cheese"},
    ),
    "milk": CalciumFood(
        id="milk",
        label="milk",
        phrase="a cool cup of milk",
        serving="took slow sips of milk",
        portable=False,
        in_cup=True,
        spoon_needed=False,
        calcium=True,
        tags={"calcium", "milk"},
    ),
    "yogurt": CalciumFood(
        id="yogurt",
        label="yogurt",
        phrase="a small bowl of yogurt",
        serving="ate the yogurt with careful spoonfuls",
        portable=False,
        in_cup=False,
        spoon_needed=True,
        calcium=True,
        tags={"calcium", "yogurt"},
    ),
}

CLUES = {
    "map_rhyme": (
        "A chalky-white treasure helps pirate bones and teeth stay strong. "
        "Do not just grab the first sweet thing. Stop, think, and choose a snack with calcium."
    ),
    "parrot_card": (
        "Captain Parrot's note said: Strong crews solve clues before they rush. "
        "Pick a ship snack with calcium, then set sail."
    ),
    "shell_riddle": (
        "The shell on the map read: Not sticky, not just sweet, but a clever calcium treat for the crew."
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]


def explain_rejection(quest: Quest, food: CalciumFood) -> str:
    reasons: list[str] = []
    if not food.calcium:
        reasons.append(f"{food.label} does not give the crew any calcium")
    if quest.needs_portable and not food.portable:
        reasons.append(f"the {quest.id} quest needs a snack the pirates can finish before climbing or dashing off")
    if not quest.allow_cup and food.in_cup:
        reasons.append("cups do not fit this part of the game")
    if not quest.allow_spoon and food.spoon_needed:
        reasons.append("there is no calm place to sit with a spoon during this part of the adventure")
    joined = "; ".join(reasons) if reasons else "that snack does not fit this quest"
    return f"(No story: {joined}. Pick a calcium food that matches the quest.)"


def play_setup(world: World, hero: Entity, mate: Entity, quest: Quest) -> None:
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"On a soft afternoon, {hero.id} and {mate.id} turned the living room into {quest.scene}. "
        f"{quest.setup}"
    )
    world.say(
        f'"Captain {hero.id} and Scout {mate.id}!" {hero.id} cried. '
        f'"Today we will {quest.goal}!"'
    )


def find_clue(world: World, hero: Entity, mate: Entity, clue_text: str, quest: Quest) -> None:
    world.say(
        f"At the start of the game, they found a folded pirate clue tucked under the toy compass. "
        f"It promised that the crew could {quest.goal}, but only if they solved one food puzzle first."
    )
    world.say(f"{mate.id} read the clue aloud: {clue_text}")


def hurry_to_wrong_snack(world: World, hero: Entity, wrong: WrongSnack) -> None:
    hero.memes["impatience"] += 1
    world.say(
        f'{hero.id} hurried to the pretend galley and grabbed {wrong.phrase}. '
        f'"{wrong.quick_claim}" {hero.pronoun()} said.'
    )


def first_attempt(world: World, hero: Entity, mate: Entity, quest: Quest, wrong: WrongSnack) -> None:
    quest_ent = world.get("quest")
    quest_ent.meters["attempt"] += 1
    world.facts["wrong_snack_id"] = wrong.id
    world.facts["chosen_food_has_calcium"] = wrong.has_calcium
    world.say(
        f"But when they {quest.try_line}, the crew stopped almost at once. "
        f"{wrong.mess}"
    )
    propagate(world, narrate=False)
    if quest_ent.meters["stalled"] >= THRESHOLD:
        world.say(
            f'"Wait," said {mate.id}. "We still have not solved the clue." '
            f"The pirate game wobbled right there, and the treasure seemed farther away."
        )


def think_and_ask(world: World, mate: Entity, parent: Entity, clue_text: str) -> None:
    mate.memes["thoughtfulness"] += 1
    world.say(
        f"{mate.id} sat back on {mate.pronoun('possessive')} heels and read the clue again, slower this time. "
        f"{parent.label_word.capitalize()} heard the whispering and came over to listen."
    )
    world.say(
        f'"The important word is calcium," {parent.label_word} said. '
        f'"The clue is not asking for the brightest snack. It is asking for a sensible one."'
    )
    world.facts["clue_text"] = clue_text


def choose_calcium_food(world: World, hero: Entity, mate: Entity, quest: Quest, food: CalciumFood) -> None:
    if not food_fits_quest(quest, food):
        raise StoryError(explain_rejection(quest, food))
    world.facts["calcium_food_id"] = food.id
    world.facts["food_fits_quest"] = True
    world.facts["clue_solved"] = True
    hero.meters["calcium"] += 1
    mate.memes["confidence"] += 1
    world.say(
        f"Together they checked the galley choices and chose {food.phrase}. "
        f'"This one has calcium," said {mate.id}, and {hero.id} nodded at once.'
    )
    world.say(
        f"They {food.serving}. It was not magic. The clever part was that they had stopped, read carefully, and picked a ship snack that fit the clue."
    )
    propagate(world, narrate=False)


def second_attempt(world: World, hero: Entity, mate: Entity, quest: Quest) -> None:
    quest_ent = world.get("quest")
    quest_ent.meters["attempt"] += 1
    propagate(world, narrate=False)
    if quest_ent.meters["done"] >= THRESHOLD:
        hero.memes["pride"] += 1
        mate.memes["joy"] += 1
        world.say(
            f"Then they tried again. This time {hero.id} and {mate.id} {quest.solved_line}."
        )


def finish_story(world: World, parent: Entity, quest: Quest, food: CalciumFood) -> None:
    world.say(
        f"{quest.ending_image} {parent.label_word.capitalize()} clapped from the doorway and smiled."
    )
    world.say(
        f'"Now that was real pirate thinking," {parent.label_word} said. '
        f'"You found the problem, looked at the clue, and solved it together with {food.label}."'
    )
    world.say(
        "The crew tucked the map back into the shoebox chest, already chattering about their next voyage. "
        "From then on, when a pirate problem popped up, they remembered to stop, think, and choose the sensible answer first."
    )


def tell(
    quest: Quest,
    wrong: WrongSnack,
    food: CalciumFood,
    hero_name: str = "Tom",
    hero_gender: str = "boy",
    mate_name: str = "Lily",
    mate_gender: str = "girl",
    parent_type: str = "mother",
    clue_id: str = "map_rhyme",
) -> World:
    if clue_id not in CLUES:
        raise StoryError(f"(No story: unknown clue '{clue_id}'.)")
    if not food_fits_quest(quest, food):
        raise StoryError(explain_rejection(quest, food))
    if wrong.has_calcium:
        raise StoryError("(No story: the first snack should be the wrong answer, so it cannot already be a calcium snack.)")

    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, role="hero", label=hero_name))
    mate = world.add(Entity(id="mate", kind="character", type=mate_gender, role="mate", label=mate_name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, role="parent", label="the parent"))
    quest_ent = world.add(Entity(id="quest", kind="thing", type="quest", label=quest.id))
    treasure = world.add(Entity(id="treasure", kind="thing", type="treasure", label="treasure chest"))
    world.add(Entity(id="wrong_snack", kind="thing", type="snack", label=wrong.label, tags=set(wrong.tags)))
    world.add(Entity(id="calcium_food", kind="thing", type="food", label=food.label, tags=set(food.tags)))

    world.facts["quest_id"] = quest.id
    world.facts["quest_cfg"] = quest
    world.facts["wrong_snack_cfg"] = wrong
    world.facts["calcium_food_cfg"] = food
    world.facts["hero_name"] = hero_name
    world.facts["mate_name"] = mate_name
    world.facts["parent"] = parent
    world.facts["hero"] = hero
    world.facts["mate"] = mate
    world.facts["food_fits_quest"] = False
    world.facts["clue_solved"] = False
    world.facts["chosen_food_has_calcium"] = False
    world.facts["outcome"] = "stalled"

    play_setup(world, hero, mate, quest)
    find_clue(world, hero, mate, CLUES[clue_id], quest)

    world.para()
    hurry_to_wrong_snack(world, hero, wrong)
    first_attempt(world, hero, mate, quest, wrong)

    world.para()
    think_and_ask(world, mate, parent, CLUES[clue_id])
    choose_calcium_food(world, hero, mate, quest, food)
    second_attempt(world, hero, mate, quest)
    finish_story(world, parent, quest, food)

    world.facts["outcome"] = "solved" if treasure.meters["found"] >= THRESHOLD else "stalled"
    world.facts["treasure_found"] = treasure.meters["found"] >= THRESHOLD
    world.facts["clue_id"] = clue_id
    return world


def pair_noun(hero: Entity, mate: Entity) -> str:
    if hero.type == "boy" and mate.type == "boy":
        return "two boys"
    if hero.type == "girl" and mate.type == "girl":
        return "two girls"
    return "a boy and a girl"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    quest = f["quest_cfg"]
    food = f["calcium_food_cfg"]
    wrong = f["wrong_snack_cfg"]
    return [
        f'Write a short pirate tale for a 3-to-5-year-old where two children solve a snack clue using the word "calcium".',
        f"Tell a gentle story where {hero.label} and {mate.label} are playing pirates, grab {wrong.label} too quickly, and then slow down and choose {food.label} after rereading the clue.",
        f"Write a simple problem-solving story in a pirate style where the crew wants to {quest.goal}, gets stuck, and finishes the adventure by picking a sensible calcium snack.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    parent = f["parent"]
    quest = f["quest_cfg"]
    wrong = f["wrong_snack_cfg"]
    food = f["calcium_food_cfg"]
    crew = pair_noun(hero, mate)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {crew}, {hero.label} and {mate.label}, who were playing pirates together. Their {parent.label_word} helped them listen to the clue instead of hurrying.",
        ),
        (
            "What problem did the pirate crew have?",
            f"They wanted to {quest.goal}, but they rushed at the first snack instead of solving the food clue. Because they had not picked the calcium snack the clue asked for, the game stalled in the middle.",
        ),
        (
            f"Why was {wrong.label} the wrong choice?",
            f"{wrong.label.capitalize()} looked exciting, but it did not match the clue. The map was asking for a snack with calcium, so the crew needed to stop and think instead of grabbing the sweetest thing first.",
        ),
        (
            f"How did they solve the problem?",
            f"They read the clue again, listened for the important word calcium, and chose {food.label}. The solution worked because they used careful thinking and picked a snack that fit the quest, not because of magic.",
        ),
        (
            "How did the story end?",
            f"After that, they {quest.solved_line} and found the treasure. The ending shows that the crew had learned to stop, think, and choose a sensible answer before charging ahead.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "calcium": [
        (
            "What is calcium?",
            "Calcium is something your body uses to help build strong bones and teeth. You get it from foods, and it helps over time as part of growing.",
        )
    ],
    "milk": [
        (
            "Why do people say milk has calcium?",
            "Milk is one food that contains calcium. It can be part of helping bones and teeth grow strong.",
        )
    ],
    "yogurt": [
        (
            "Does yogurt have calcium?",
            "Yes, yogurt can have calcium because it is made from milk. It can be a good snack when you sit down to eat it.",
        )
    ],
    "cheese": [
        (
            "Does cheese have calcium?",
            "Yes, cheese can have calcium too. Little cheese cubes can make an easy snack because they are simple to pick up and eat.",
        )
    ],
    "problem_solving": [
        (
            "What does problem solving mean?",
            "Problem solving means noticing what is wrong, thinking about it, and trying a smart fix. Good problem solving often means slowing down instead of rushing.",
        )
    ],
    "pirates": [
        (
            "What is a treasure map?",
            "A treasure map is a pretend or real map that shows where treasure may be hidden. In stories, it often has clues the characters must solve.",
        )
    ],
    "climb": [
        (
            "Why might a climber want both hands free?",
            "Both hands free can help a climber hold on and move carefully. That is why a tidy little snack can make more sense than a cup or bowl during a climb.",
        )
    ],
    "rowing": [
        (
            "Why do rowers put drinks down before rowing?",
            "Rowing works better when your hands are ready for the oars. If a drink is still in your hands, it can slosh or distract you.",
        )
    ],
    "map": [
        (
            "Why is rereading a clue a smart idea?",
            "Rereading helps you notice words you missed the first time. Sometimes one important word is the key to the whole answer.",
        )
    ],
}
KNOWLEDGE_ORDER = ["calcium", "milk", "yogurt", "cheese", "problem_solving", "pirates", "climb", "rowing", "map"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"calcium", "problem_solving"}
    quest = world.facts["quest_cfg"]
    food = world.facts["calcium_food_cfg"]
    tags |= set(quest.tags)
    tags |= set(food.tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:12} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    facts = {k: v for k, v in world.facts.items() if k in {"quest_id", "clue_id", "food_fits_quest", "clue_solved", "outcome", "treasure_found"}}
    lines.append(f"  facts: {facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        quest="mast",
        wrong_snack="gummy_rope",
        calcium_food="cheese_cubes",
        hero="Tom",
        hero_gender="boy",
        mate="Lily",
        mate_gender="girl",
        parent="mother",
        clue="map_rhyme",
    ),
    StoryParams(
        quest="row",
        wrong_snack="jam_bun",
        calcium_food="milk",
        hero="Mia",
        hero_gender="girl",
        mate="Ben",
        mate_gender="boy",
        parent="father",
        clue="parrot_card",
    ),
    StoryParams(
        quest="map",
        wrong_snack="fizz_pop",
        calcium_food="yogurt",
        hero="Zoe",
        hero_gender="girl",
        mate="Finn",
        mate_gender="boy",
        parent="mother",
        clue="shell_riddle",
    ),
    StoryParams(
        quest="row",
        wrong_snack="gummy_rope",
        calcium_food="cheese_cubes",
        hero="Sam",
        hero_gender="boy",
        mate="Theo",
        mate_gender="boy",
        parent="father",
        clue="map_rhyme",
    ),
]


ASP_RULES = r"""
% Quest logistics.
fits(Q, F) :- quest(Q), food(F), gives_calcium(F),
              not need_portable(Q).
fits(Q, F) :- quest(Q), food(F), gives_calcium(F),
              need_portable(Q), portable(F).

:- fits(Q, F), no_cup(Q), in_cup(F).
:- fits(Q, F), no_spoon(Q), needs_spoon(F).

valid(Q, W, F) :- quest(Q), wrong_snack(W), food(F),
                  not wrong_has_calcium(W), fits(Q, F).

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for quest_id, quest in QUESTS.items():
        lines.append(asp.fact("quest", quest_id))
        if quest.needs_portable:
            lines.append(asp.fact("need_portable", quest_id))
        if not quest.allow_cup:
            lines.append(asp.fact("no_cup", quest_id))
        if not quest.allow_spoon:
            lines.append(asp.fact("no_spoon", quest_id))
    for wrong_id, wrong in WRONG_SNACKS.items():
        lines.append(asp.fact("wrong_snack", wrong_id))
        if wrong.has_calcium:
            lines.append(asp.fact("wrong_has_calcium", wrong_id))
    for food_id, food in CALCIUM_FOODS.items():
        lines.append(asp.fact("food", food_id))
        if food.calcium:
            lines.append(asp.fact("gives_calcium", food_id))
        if food.portable:
            lines.append(asp.fact("portable", food_id))
        if food.in_cup:
            lines.append(asp.fact("in_cup", food_id))
        if food.spoon_needed:
            lines.append(asp.fact("needs_spoon", food_id))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and Python gate:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated an empty story.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        auto_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        auto_sample = generate(auto_params)
        if not auto_sample.story.strip():
            raise StoryError("(Auto smoke failed: generated an empty story.)")
        print("OK: default resolved generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a pirate treasure hunt, a clue about calcium, and a small problem-solving turn."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--wrong-snack", dest="wrong_snack", choices=WRONG_SNACKS)
    ap.add_argument("--calcium-food", dest="calcium_food", choices=CALCIUM_FOODS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", dest="hero_gender", choices=["girl", "boy"])
    ap.add_argument("--mate")
    ap.add_argument("--mate-gender", dest="mate_gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest and args.calcium_food:
        quest = QUESTS[args.quest]
        food = CALCIUM_FOODS[args.calcium_food]
        if not food_fits_quest(quest, food):
            raise StoryError(explain_rejection(quest, food))
    combos = [
        combo for combo in valid_combos()
        if (args.quest is None or combo[0] == args.quest)
        and (args.wrong_snack is None or combo[1] == args.wrong_snack)
        and (args.calcium_food is None or combo[2] == args.calcium_food)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    quest_id, wrong_id, food_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero or pick_name(rng, hero_gender)
    mate_name = args.mate or pick_name(rng, mate_gender, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    clue = args.clue or rng.choice(sorted(CLUES))
    return StoryParams(
        quest=quest_id,
        wrong_snack=wrong_id,
        calcium_food=food_id,
        hero=hero_name,
        hero_gender=hero_gender,
        mate=mate_name,
        mate_gender=mate_gender,
        parent=parent,
        clue=clue,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS:
        raise StoryError(f"(No story: unknown quest '{params.quest}'.)")
    if params.wrong_snack not in WRONG_SNACKS:
        raise StoryError(f"(No story: unknown wrong snack '{params.wrong_snack}'.)")
    if params.calcium_food not in CALCIUM_FOODS:
        raise StoryError(f"(No story: unknown calcium food '{params.calcium_food}'.)")
    if params.clue not in CLUES:
        raise StoryError(f"(No story: unknown clue '{params.clue}'.)")

    world = tell(
        quest=QUESTS[params.quest],
        wrong=WRONG_SNACKS[params.wrong_snack],
        food=CALCIUM_FOODS[params.calcium_food],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        mate_name=params.mate,
        mate_gender=params.mate_gender,
        parent_type=params.parent,
        clue_id=params.clue,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (quest, wrong_snack, calcium_food) combos:\n")
        for quest_id, wrong_id, food_id in combos:
            print(f"  {quest_id:6} {wrong_id:10} {food_id}")
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
            header = f"### {p.hero} & {p.mate}: {p.quest} with {p.calcium_food}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
