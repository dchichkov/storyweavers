#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/linguini_kindness_teamwork_transformation_fairy_tale.py
==================================================================================

A standalone story world for a fairy-tale domain built around linguini, kindness,
teamwork, and transformation.

Premise
-------
A child in a magical kitchen wants to cook linguini for a fairy feast, but one
important obstacle makes the task too hard alone. On the way, the child finds a
small creature who needs a kind act. When the child helps first, the creature
joins in. Their teamwork solves the obstacle, and the plain dry linguini
transforms into a shining fairy-tale supper.

Reasonableness constraint
-------------------------
Not every kindness fits every helper, and not every helper can solve every
kitchen problem. This world only generates stories where:

* the chosen kindness actually meets the helper's need, and
* the helper's ability can honestly solve the chosen obstacle.

That keeps the warning/fix grounded in common sense inside the fairy-tale frame.

Run it
------
    python storyworlds/worlds/gpt-5.4/linguini_kindness_teamwork_transformation_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/linguini_kindness_teamwork_transformation_fairy_tale.py --helper firefly --obstacle dark_pantry --kindness leaf_towel
    python storyworlds/worlds/gpt-5.4/linguini_kindness_teamwork_transformation_fairy_tale.py --helper mole --obstacle high_shelf
    python storyworlds/worlds/gpt-5.4/linguini_kindness_teamwork_transformation_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/linguini_kindness_teamwork_transformation_fairy_tale.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    need: str = ""
    ability: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "fairy_girl", "woman"}
        male = {"boy", "father", "fairy_boy", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    kitchen: str
    opening: str
    feast: str
    ending: str


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    type: str
    need: str
    ability: str
    entrance: str
    solve_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Kindness:
    id: str
    label: str
    phrase: str
    need_tags: set[str]
    act_text: str
    answer_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    need_ability: str
    worry_text: str
    solve_result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Finish:
    id: str
    sauce: str
    color: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_gratitude(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    if helper.meters["comforted"] < THRESHOLD:
        return []
    sig = ("gratitude", helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["gratitude"] += 1
    helper.memes["trust"] += 1
    hero.memes["kindness"] += 1
    return []


def _r_teamwork(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    if helper.memes["gratitude"] < THRESHOLD:
        return []
    sig = ("teamwork", hero.id, helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    return []


def _r_cook(world: World) -> list[str]:
    pot = world.get("pot")
    pasta = world.get("linguini")
    if pot.meters["ready"] < THRESHOLD or pasta.meters["in_pot"] < THRESHOLD:
        return []
    sig = ("cook", pasta.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pasta.meters["cooked"] += 1
    pasta.meters["stiff"] = 0.0
    return []


def _r_transform(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    pasta = world.get("linguini")
    if pasta.meters["cooked"] < THRESHOLD:
        return []
    if hero.memes["kindness"] < THRESHOLD or hero.memes["teamwork"] < THRESHOLD:
        return []
    sig = ("transform", pasta.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pasta.meters["transformed"] += 1
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule("gratitude", _r_gratitude),
    Rule("teamwork", _r_teamwork),
    Rule("cook", _r_cook),
    Rule("transform", _r_transform),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) != before:
                changed = True


def kindness_fits(helper: Helper, kindness: Kindness) -> bool:
    return helper.need in kindness.need_tags


def helper_solves(helper: Helper, obstacle: Obstacle) -> bool:
    return helper.ability == obstacle.need_ability


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for helper_id, helper in HELPERS.items():
            for obstacle_id, obstacle in OBSTACLES.items():
                if not helper_solves(helper, obstacle):
                    continue
                for kindness_id, kindness in KINDNESS_ACTS.items():
                    if kindness_fits(helper, kindness):
                        combos.append((place_id, helper_id, obstacle_id, kindness_id))
    return combos


def predict_success(helper: Helper, obstacle: Obstacle, kindness: Kindness) -> dict:
    return {
        "comforts_helper": kindness_fits(helper, kindness),
        "solves_obstacle": helper_solves(helper, obstacle),
        "successful": kindness_fits(helper, kindness) and helper_solves(helper, obstacle),
    }


def introduce(world: World, hero: Entity, place: Place, finish: Finish) -> None:
    world.say(
        f"In {place.opening}, {hero.id} stood in {place.kitchen} with a willow-wood spoon "
        f"and a packet of linguini tied in silver string."
    )
    world.say(
        f"That night there would be {place.feast}, and {hero.pronoun()} longed to bring "
        f"a bowl of {finish.color} linguini in {finish.sauce}."
    )


def reveal_obstacle(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.memes["worry"] += 1
    world.say(obstacle.worry_text.replace("{hero}", hero.id))
    world.say(
        f"{hero.id} pressed {hero.pronoun('possessive')} lips together. One small cook could not mend "
        f"{obstacle.phrase} alone."
    )


def meet_helper(world: World, helper_ent: Entity, helper_cfg: Helper) -> None:
    world.say(helper_cfg.entrance.replace("{helper}", helper_ent.label))
    if helper_cfg.need == "hungry":
        world.say(f"The little {helper_cfg.label} looked so hungry that even its whiskers drooped.")
    elif helper_cfg.need == "wet":
        world.say(f"Tiny drops clung to the {helper_cfg.label}, and it shivered in the cool air.")
    elif helper_cfg.need == "lonely":
        world.say(f"The {helper_cfg.label} tried to look brave, but it was plainly lonely.")
    elif helper_cfg.need == "thirsty":
        world.say(f"The {helper_cfg.label}'s voice sounded dry, like pebbles in a summer stream.")


def do_kindness(world: World, hero: Entity, helper_ent: Entity,
                helper_cfg: Helper, kindness: Kindness) -> None:
    helper_ent.meters[helper_cfg.need] = 0.0
    helper_ent.meters["comforted"] += 1
    hero.memes["care"] += 1
    world.say(kindness.act_text.replace("{hero}", hero.id).replace("{helper}", helper_cfg.label))
    propagate(world)
    world.say(
        f"The {helper_cfg.label} blinked in surprise, and a warm thankful light came into its eyes."
    )


def offer_teamwork(world: World, helper_cfg: Helper, obstacle: Obstacle) -> None:
    world.say(
        f'"You were kind to me first," said the {helper_cfg.label}. "Now let us work together."'
    )
    world.say(helper_cfg.solve_text.replace("{obstacle}", obstacle.label))
    world.say(obstacle.solve_result)


def cook_and_transform(world: World, hero: Entity, helper_ent: Entity,
                       finish: Finish) -> None:
    pot = world.get("pot")
    pasta = world.get("linguini")
    pot.meters["ready"] += 1
    pasta.meters["in_pot"] += 1
    propagate(world)
    world.say(
        f"At last the dry linguini slipped into the singing pot, and {hero.id} and "
        f"the {helper_ent.label} stirred side by side."
    )
    if pasta.meters["cooked"] >= THRESHOLD:
        world.say(
            f"The stiff pale strands softened into long ribbons, and the kitchen filled with "
            f"the sweet smell of {finish.sauce}."
        )
    if pasta.meters["transformed"] >= THRESHOLD:
        world.say(
            f"Then the true fairy-tale wonder arrived: the linguini shone {finish.color}, "
            f"as if kindness itself had woven moonlight through every strand."
        )


def feast_ending(world: World, hero: Entity, helper_cfg: Helper, place: Place,
                 finish: Finish) -> None:
    hero.memes["belonging"] += 1
    world.say(
        f"When they carried the bowl to {place.feast}, everyone leaned close to see the glowing curls."
    )
    world.say(
        f"{hero.id} made sure the {helper_cfg.label} had the first warm twirl, and that made the meal taste "
        f"even better."
    )
    world.say(finish.ending_line.replace("{hero}", hero.id).replace("{ending}", place.ending))


def tell(place: Place, helper_cfg: Helper, obstacle: Obstacle, kindness: Kindness,
         finish: Finish, hero_name: str = "Lina", hero_type: str = "girl") -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    helper_ent = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.label,
        phrase=helper_cfg.phrase,
        role="helper",
        need=helper_cfg.need,
        ability=helper_cfg.ability,
    ))
    pot = world.add(Entity(id="pot", type="pot", label="copper pot"))
    pasta = world.add(Entity(id="linguini", type="food", label="linguini"))
    issue = world.add(Entity(id="obstacle", type="obstacle", label=obstacle.label))
    issue.meters["blocking"] += 1
    helper_ent.meters[helper_cfg.need] += 1
    pasta.meters["stiff"] += 1

    introduce(world, hero, place, finish)

    world.para()
    reveal_obstacle(world, hero, obstacle)
    meet_helper(world, helper_ent, helper_cfg)

    world.para()
    do_kindness(world, hero, helper_ent, helper_cfg, kindness)
    offer_teamwork(world, helper_cfg, obstacle)
    issue.meters["blocking"] = 0.0
    issue.meters["solved"] += 1
    helper_ent.memes["helped"] += 1

    world.para()
    cook_and_transform(world, hero, helper_ent, finish)
    feast_ending(world, hero, helper_cfg, place, finish)

    world.facts.update(
        hero=hero,
        hero_name=hero_name,
        helper=helper_ent,
        helper_cfg=helper_cfg,
        kindness=kindness,
        obstacle=obstacle,
        place=place,
        finish=finish,
        pot=pot,
        linguini=pasta,
        transformed=pasta.meters["transformed"] >= THRESHOLD,
        teamwork=hero.memes["teamwork"] >= THRESHOLD,
        kindness_done=hero.memes["kindness"] >= THRESHOLD,
    )
    return world


PLACES = {
    "moon_kitchen": Place(
        "moon_kitchen",
        "the Moon Queen's blue-tiled kitchen",
        "a little kingdom above the trees",
        "the moonrise feast in the crystal hall",
        "outside, the stars looked close enough to stir with a spoon",
    ),
    "toadstool_hearth": Place(
        "toadstool_hearth",
        "the round kitchen inside a red toadstool house",
        "a glade where mushrooms were taller than children",
        "the dew-supper under lantern leaves",
        "the toadstool windows glowed like tiny suns",
    ),
    "willow_oven": Place(
        "willow_oven",
        "the willow bakery beside the silver brook",
        "a green kingdom where willow branches bowed like curtains",
        "the twilight feast on the mossy bank",
        "the brook carried away little splashes of gold light",
    ),
}

HELPERS = {
    "mouse": Helper(
        "mouse",
        "mouse tailor",
        "a mouse tailor in a thimble cap",
        "mouse",
        "hungry",
        "climb",
        "From beneath a flour sack peeped a mouse tailor in a thimble cap, holding its tiny tummy.",
        'With nimble feet the mouse tailor scampered upward and fetched what was needed from the {obstacle}.',
        tags={"mouse", "helping"}),
    "firefly": Helper(
        "firefly",
        "firefly fairy",
        "a firefly fairy with damp wings",
        "firefly",
        "wet",
        "glow",
        "By the window hovered a firefly fairy whose wings were speckled with rain.",
        'The firefly fairy lifted high into the air and lit the whole room until the {obstacle} could hide no secrets.',
        tags={"firefly", "light"}),
    "mole": Helper(
        "mole",
        "mole baker",
        "a mole baker dusted with flour",
        "mole",
        "lonely",
        "lift",
        "Near the stove sat a mole baker beside a basket of rolls, sighing softly to itself.",
        'The mole baker planted sturdy paws on the floor and heaved until the {obstacle} was no trouble at all.',
        tags={"mole", "strength"}),
    "brook_sprite": Helper(
        "brook_sprite",
        "brook sprite",
        "a brook sprite wearing bead-bright drops",
        "sprite",
        "thirsty",
        "loosen",
        "On the sink rim perched a brook sprite, blinking as if it had wandered a long way from water.",
        'The brook sprite touched the pasta with cool water-magic, and the {obstacle} loosened at once.',
        tags={"sprite", "water"}),
}

KINDNESS_ACTS = {
    "honey_roll": Kindness(
        "honey_roll",
        "a honey roll",
        "a honey roll",
        {"hungry"},
        "{hero} broke a honey roll in half and offered the sweetest piece to the {helper}.",
        "The child shared food with the hungry helper before asking for anything back.",
        tags={"food", "sharing"}),
    "leaf_towel": Kindness(
        "leaf_towel",
        "a soft leaf towel",
        "a soft leaf towel",
        {"wet"},
        "{hero} wrapped the {helper} in a soft leaf towel and dabbed the raindrops from its wings.",
        "The child gently dried the helper's wet wings so it could feel warm and safe again.",
        tags={"drying", "care"}),
    "warm_invitation": Kindness(
        "warm_invitation",
        "a warm invitation",
        "a warm invitation to sit by the stove",
        {"lonely"},
        '{hero} patted the stool by the stove and said, "You need not sit alone. Stay with me, little {helper}."',
        "The child noticed the lonely helper and invited it to stay close and belong.",
        tags={"friendship", "welcome"}),
    "dew_cup": Kindness(
        "dew_cup",
        "a cup of dew",
        "a silver cup of dew",
        {"thirsty"},
        "{hero} filled a silver acorn cup with clear dew and held it carefully for the {helper}.",
        "The child gave the thirsty helper fresh dew to drink before the work began.",
        tags={"water", "care"}),
}

OBSTACLES = {
    "high_shelf": Obstacle(
        "high_shelf",
        "high shelf",
        "the high herb shelf",
        "climb",
        "{hero} reached for the star-basil on the high shelf, but the jar stood far above {hero}'s fingertips.",
        "Soon the star-basil was in the pot where it belonged.",
        tags={"shelf", "herbs"}),
    "dark_pantry": Obstacle(
        "dark_pantry",
        "dark pantry",
        "the dark pantry",
        "glow",
        "{hero} opened the pantry door, but it was so dark inside that the mushroom salt and moon cheese might have been hidden in midnight.",
        "In the clear glow, the right ingredients were easy to find.",
        tags={"dark", "pantry"}),
    "heavy_pot": Obstacle(
        "heavy_pot",
        "heavy pot",
        "the heavy copper pot",
        "lift",
        "{hero} tugged at the heavy copper pot, but it would not budge onto the stove.",
        "The copper pot rose at last and settled above the blue flame.",
        tags={"pot", "heavy"}),
    "knotted_linguini": Obstacle(
        "knotted_linguini",
        "knotted linguini",
        "the knotted linguini",
        "loosen",
        "{hero} untied the silver string, only to find the linguini bent into stubborn little knots.",
        "The tangled strands relaxed and fell straight as ribbons.",
        tags={"linguini", "tangled"}),
}

FINISHES = {
    "golden_butter": Finish(
        "golden_butter",
        "golden butter with star-basil",
        "golden",
        "{hero} smiled to see everyone sharing. {ending}, and the bowl of linguini gleamed like a treasure won by kindness.",
        tags={"butter"}),
    "rose_cream": Finish(
        "rose_cream",
        "rose cream and moon-pepper",
        "rosy",
        "{hero} bowed a little as the first happy bites were taken. {ending}, and even the steam curling from the linguini looked enchanted.",
        tags={"cream"}),
    "green_pesto": Finish(
        "green_pesto",
        "emerald pesto of garden leaves",
        "green-gold",
        "{hero} laughed when the hall filled with happy slurps. {ending}, and the shining linguini looked almost too lovely to eat.",
        tags={"pesto"}),
}

GIRL_NAMES = ["Lina", "Mira", "Elsa", "Nora", "Ivy", "Talia", "Poppy", "Wren"]
BOY_NAMES = ["Finn", "Oren", "Tobin", "Milo", "Rowan", "Elio", "Pip", "Jory"]


@dataclass
class StoryParams:
    place: str
    helper: str
    obstacle: str
    kindness: str
    finish: str
    hero_name: str
    hero_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "linguini": [("What is linguini?",
                  "Linguini is a kind of long, flat pasta. When it cooks, the dry stiff strands turn soft and bendy.")],
    "teamwork": [("What is teamwork?",
                  "Teamwork means two or more people help one another do a job. A hard task can become easier when everyone shares the work.")],
    "kindness": [("What is kindness?",
                  "Kindness means noticing what someone needs and helping in a gentle way. Kind acts often make other hearts feel safe and ready to help too.")],
    "transformation": [("What does transformation mean in a fairy tale?",
                        "Transformation means something changes into a new form. In fairy tales, that change often shows that love, courage, or kindness has done real magic.")],
    "firefly": [("Why is a firefly useful in the dark?",
                 "A firefly makes light, so it can help others see in a dark place. That is why a glowing helper can solve a dark problem.")],
    "mouse": [("Why could a small mouse reach a high shelf?",
               "A mouse is tiny, quick, and good at climbing. Sometimes being small is exactly what helps with a tall problem.")],
    "mole": [("Why could a mole help with a heavy pot?",
              "A sturdy mole can push and lift with strong paws. Strength is useful when something is too heavy for one child alone.")],
    "sprite": [("How could water-magic help knotted pasta?",
                "Water softens dry pasta and can help tight tangles loosen. In a fairy tale, a brook sprite can do that very quickly with magic.")],
}
KNOWLEDGE_ORDER = [
    "linguini", "kindness", "teamwork", "transformation",
    "firefly", "mouse", "mole", "sprite"
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper_cfg"]
    obstacle = f["obstacle"]
    return [
        'Write a short fairy tale for a 3-to-5-year-old that includes the word "linguini" and shows kindness turning into teamwork.',
        f"Tell a fairy-tale story where {hero.label} cannot solve {obstacle.phrase} alone, helps a {helper.label} first, and then cooks a magical supper together.",
        "Write a gentle magical story where a kind act comes before the help, and the final meal is transformed in a way that proves kindness mattered.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper_cfg"]
    kindness = f["kindness"]
    obstacle = f["obstacle"]
    place = f["place"]
    finish = f["finish"]
    out: list[tuple[str, str]] = [
        ("Who is the story about?",
         f"It is about {hero.label}, who wanted to cook linguini in {place.kitchen}, and a {helper.label} who became a helper and friend."),
        ("What problem did the child have at the start?",
         f"{hero.label} wanted to make supper, but {obstacle.phrase} was in the way. The problem was too hard to fix alone, so the cooking could not begin yet."),
        (f"How did {hero.label} show kindness to the {helper.label}?",
         f"{kindness.answer_text} That kind choice came before any teamwork, which is why it mattered so much."),
        ("How did teamwork help?",
         f"The {helper.label} used its special gift to solve {obstacle.phrase}, and then they cooked side by side. The hard part changed once they shared the work instead of struggling alone."),
    ]
    if f["transformed"]:
        out.append((
            "How did the linguini transform at the end?",
            f"The dry stiff linguini first softened in the pot, and then it began to shine {finish.color}. The change showed that kindness and teamwork had turned an ordinary supper into fairy-tale magic."
        ))
    out.append((
        "Why did the ending feel happy?",
        f"The feast was ready, the helper was included, and the bowl was shared. The final picture proves that everyone had more joy because {hero.label} chose kindness first."
    ))
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"linguini", "kindness", "teamwork", "transformation"}
    helper_id = f["helper_cfg"].id
    if helper_id == "firefly":
        tags.add("firefly")
    elif helper_id == "mouse":
        tags.add("mouse")
    elif helper_id == "mole":
        tags.add("mole")
    elif helper_id == "brook_sprite":
        tags.add("sprite")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.need:
            bits.append(f"need={e.need}")
        if e.ability:
            bits.append(f"ability={e.ability}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("moon_kitchen", "mouse", "high_shelf", "honey_roll", "golden_butter", "Lina", "girl"),
    StoryParams("toadstool_hearth", "firefly", "dark_pantry", "leaf_towel", "rose_cream", "Finn", "boy"),
    StoryParams("willow_oven", "mole", "heavy_pot", "warm_invitation", "green_pesto", "Mira", "girl"),
    StoryParams("moon_kitchen", "brook_sprite", "knotted_linguini", "dew_cup", "golden_butter", "Oren", "boy"),
]


def explain_rejection(helper: Helper, obstacle: Obstacle, kindness: Kindness) -> str:
    if not kindness_fits(helper, kindness):
        return (
            f"(No story: {kindness.phrase} does not match what the {helper.label} needs. "
            f"In this world, kindness must genuinely comfort the helper before help returns.)"
        )
    if not helper_solves(helper, obstacle):
        return (
            f"(No story: a {helper.label} cannot honestly solve {obstacle.phrase}. "
            f"Pick a helper whose gift matches the obstacle.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
kind_fit(H, K)   :- helper_need(H, N), kindness_meets(K, N).
can_solve(H, O)  :- helper_ability(H, A), obstacle_needs(O, A).
valid(P, H, O, K) :- place(P), helper(H), obstacle(O), kindness(K), kind_fit(H, K), can_solve(H, O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_need", hid, helper.need))
        lines.append(asp.fact("helper_ability", hid, helper.ability))
    for kid, kindness in KINDNESS_ACTS.items():
        lines.append(asp.fact("kindness", kid))
        for tag in sorted(kindness.need_tags):
            lines.append(asp.fact("kindness_meets", kid, tag))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("obstacle_needs", oid, obstacle.need_ability))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        sample = generate(smoke_cases[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generated and emitted a story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: linguini, kindness, teamwork, and transformation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--kindness", choices=KINDNESS_ACTS)
    ap.add_argument("--finish", choices=FINISHES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper and args.obstacle and args.kindness:
        helper = HELPERS[args.helper]
        obstacle = OBSTACLES[args.obstacle]
        kindness = KINDNESS_ACTS[args.kindness]
        if not (kindness_fits(helper, kindness) and helper_solves(helper, obstacle)):
            raise StoryError(explain_rejection(helper, obstacle, kindness))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.helper is None or c[1] == args.helper)
        and (args.obstacle is None or c[2] == args.obstacle)
        and (args.kindness is None or c[3] == args.kindness)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, helper_id, obstacle_id, kindness_id = rng.choice(sorted(combos))
    finish = args.finish or rng.choice(sorted(FINISHES))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    if args.hero_name:
        hero_name = args.hero_name
    else:
        hero_name = rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    return StoryParams(place, helper_id, obstacle_id, kindness_id, finish, hero_name, hero_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        HELPERS[params.helper],
        OBSTACLES[params.obstacle],
        KINDNESS_ACTS[params.kindness],
        FINISHES[params.finish],
        params.hero_name,
        params.hero_type,
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
        print(f"{len(combos)} compatible (place, helper, obstacle, kindness) combos:\n")
        for place, helper, obstacle, kindness in combos:
            print(f"  {place:16} {helper:12} {obstacle:16} {kindness}")
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
            header = f"### {p.hero_name}: {p.helper} + {p.obstacle} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
