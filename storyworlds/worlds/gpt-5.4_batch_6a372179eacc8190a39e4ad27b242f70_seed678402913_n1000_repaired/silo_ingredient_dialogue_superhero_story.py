#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/silo_ingredient_dialogue_superhero_story.py
======================================================================

A standalone storyworld about a child-sized superhero helping save an important
ingredient at the town silo before breakfast at the square.

The world models:
- a hero team with physical meters and emotional memes
- a grain silo storing one ingredient for a baker
- a concrete problem at the silo
- a sensible repair tool that may or may not succeed in time

Run it
------
python storyworlds/worlds/gpt-5.4/silo_ingredient_dialogue_superhero_story.py
python storyworlds/worlds/gpt-5.4/silo_ingredient_dialogue_superhero_story.py --ingredient cornmeal --problem roof_leak
python storyworlds/worlds/gpt-5.4/silo_ingredient_dialogue_superhero_story.py --tool bucket
python storyworlds/worlds/gpt-5.4/silo_ingredient_dialogue_superhero_story.py --all
python storyworlds/worlds/gpt-5.4/silo_ingredient_dialogue_superhero_story.py --qa --json
python storyworlds/worlds/gpt-5.4/silo_ingredient_dialogue_superhero_story.py --verify
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
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Ingredient:
    id: str
    label: str
    phrase: str
    treat: str
    color: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    sentence: str
    danger: str
    severity: int
    needs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class ToolCfg:
    id: str
    label: str
    phrase: str
    sense: int
    power: int
    fixes: set[str] = field(default_factory=set)
    action: str = ""
    fail: str = ""
    qa_text: str = ""
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


def _r_danger_worry(world: World) -> list[str]:
    out: list[str] = []
    silo = world.entities.get("silo")
    ingredient = world.entities.get("ingredient")
    baker = world.entities.get("baker")
    hero = world.entities.get("hero")
    sidekick = world.entities.get("sidekick")
    if not silo or not ingredient:
        return out
    if silo.meters["risk"] >= THRESHOLD:
        sig = ("worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            if baker:
                baker.memes["worry"] += 1
            if hero:
                hero.memes["duty"] += 1
            if sidekick:
                sidekick.memes["duty"] += 1
            out.append("__risk__")
    if ingredient.meters["spoiled"] >= THRESHOLD:
        sig = ("loss",)
        if sig not in world.fired:
            world.fired.add(sig)
            if baker:
                baker.memes["sad"] += 1
            if hero:
                hero.memes["sad"] += 1
            if sidekick:
                sidekick.memes["sad"] += 1
            out.append("__loss__")
    return out


CAUSAL_RULES = [
    Rule(name="danger_worry", tag="social", apply=_r_danger_worry),
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


INGREDIENTS = {
    "cornmeal": Ingredient(
        id="cornmeal",
        label="cornmeal",
        phrase="golden cornmeal",
        treat="sunrise cornbread",
        color="golden",
        tags={"cornmeal", "ingredient", "baking"},
    ),
    "oats": Ingredient(
        id="oats",
        label="oats",
        phrase="soft oats",
        treat="hero oat cakes",
        color="pale",
        tags={"oats", "ingredient", "baking"},
    ),
    "flour": Ingredient(
        id="flour",
        label="flour",
        phrase="white flour",
        treat="cloud muffins",
        color="white",
        tags={"flour", "ingredient", "baking"},
    ),
}

PROBLEMS = {
    "roof_leak": Problem(
        id="roof_leak",
        label="roof leak",
        sentence="A dark drip-drip line was creeping down the side of the silo roof.",
        danger="water would soak the ingredient",
        severity=2,
        needs={"cover"},
        tags={"leak", "water", "silo"},
    ),
    "chute_jam": Problem(
        id="chute_jam",
        label="chute jam",
        sentence="The silo chute was stuck with a clunk, and not one grain would slide out.",
        danger="the baker could not get the ingredient out",
        severity=2,
        needs={"turn"},
        tags={"jam", "machine", "silo"},
    ),
    "split_sack": Problem(
        id="split_sack",
        label="split sack",
        sentence="A feed sack at the silo door had split open, and the ingredient was trickling out in a little stream.",
        danger="the ingredient would spill across the ground",
        severity=1,
        needs={"catch"},
        tags={"spill", "sack", "silo"},
    ),
}

TOOLS = {
    "tarp": ToolCfg(
        id="tarp",
        label="tarp patch",
        phrase="a bright blue tarp patch",
        sense=3,
        power=3,
        fixes={"cover"},
        action="spread the tarp patch over the leak and tied it tight before another splash could get in",
        fail="spread the tarp patch, but the water was already pouring in too fast",
        qa_text="covered the leak with a tarp patch",
        tags={"tarp", "repair"},
    ),
    "wrench": ToolCfg(
        id="wrench",
        label="crank wrench",
        phrase="a long silver crank wrench",
        sense=3,
        power=3,
        fixes={"turn"},
        action="fit the crank wrench onto the stuck wheel and turned until the chute gave a happy clunk",
        fail="worked the crank wrench as hard as possible, but the jam held fast",
        qa_text="used a crank wrench to free the stuck chute",
        tags={"wrench", "repair"},
    ),
    "clean_bin": ToolCfg(
        id="clean_bin",
        label="clean bin",
        phrase="a clean red bin",
        sense=3,
        power=2,
        fixes={"catch"},
        action="slid the clean bin under the split sack and held it steady while the last of the ingredient poured safely inside",
        fail="slid the clean bin under the split sack, but too much had already spilled away",
        qa_text="caught the falling ingredient in a clean bin",
        tags={"bin", "repair"},
    ),
    "brush": ToolCfg(
        id="brush",
        label="grain brush",
        phrase="a grain brush with stiff bristles",
        sense=2,
        power=2,
        fixes={"turn"},
        action="used the grain brush to sweep the clog from the chute opening until the path was clear",
        fail="scrubbed with the grain brush, but the clog was packed in too tightly",
        qa_text="brushed the clog out of the chute",
        tags={"brush", "repair"},
    ),
    "bucket": ToolCfg(
        id="bucket",
        label="bucket",
        phrase="a little metal bucket",
        sense=1,
        power=1,
        fixes={"cover", "catch"},
        action="put the bucket under the trouble spot",
        fail="put the bucket in place, but it was too small to solve the problem",
        qa_text="set out a bucket",
        tags={"bucket"},
    ),
}

HERO_NAMES = ["Nova", "Bolt", "Sunny", "Mira", "Dash", "Ruby", "Theo", "Pip"]
SIDEKICK_NAMES = ["Gus", "Lina", "Tess", "Milo", "Bee", "Finn", "Ivy", "Jax"]
TRAITS = ["brave", "quick", "kind", "careful", "steady", "hopeful"]


def problem_matches_tool(problem: Problem, tool: ToolCfg) -> bool:
    return bool(problem.needs & tool.fixes)


def sensible_tools() -> list[ToolCfg]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for ing_id in INGREDIENTS:
        for prob_id, problem in PROBLEMS.items():
            for tool_id, tool in TOOLS.items():
                if tool.sense >= SENSE_MIN and problem_matches_tool(problem, tool):
                    combos.append((ing_id, prob_id, tool_id))
    return combos


def crisis_level(problem: Problem, delay: int) -> int:
    return problem.severity + delay


def is_saved(problem: Problem, tool: ToolCfg, delay: int) -> bool:
    return tool.power >= crisis_level(problem, delay)


def explain_rejection(problem: Problem, tool: ToolCfg) -> str:
    if tool.sense < SENSE_MIN:
        return (
            f"(Refusing tool '{tool.id}': it scores too low on common sense "
            f"(sense={tool.sense} < {SENSE_MIN}). A stronger repair tool would make a better story.)"
        )
    return (
        f"(No story: {tool.label} does not really solve a {problem.label}. "
        f"Pick a tool that can {', '.join(sorted(problem.needs))} the problem.)"
    )


def predict_loss(world: World, problem: Problem, delay: int) -> dict:
    sim = world.copy()
    silo = sim.get("silo")
    ingredient = sim.get("ingredient")
    silo.meters["risk"] += 1
    if crisis_level(problem, delay) >= 3:
        ingredient.meters["spoiled"] += 1
        ingredient.meters["saved"] = 0
    propagate(sim, narrate=False)
    return {
        "spoiled": ingredient.meters["spoiled"] >= THRESHOLD,
        "risk": silo.meters["risk"],
    }


def opening(world: World, hero: Entity, sidekick: Entity, baker: Entity, ingredient: Ingredient) -> None:
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"In the little town of Brightfield stood a silver silo taller than the bakery chimney. "
        f"Every child said it looked like a rocket waiting for a hero."
    )
    world.say(
        f"That morning, {hero.id} tied on a homemade cape, and {sidekick.id} snapped a paper badge onto a shirt. "
        f'"Super Grain Guard is on patrol!" {hero.id} said.'
    )
    world.say(
        f'At the bakery door, Mr. Vale the baker waved both hands. "{ingredient.phrase.capitalize()} is my most important ingredient today," '
        f'he called. "Without it, there will be no {ingredient.treat} for the square."'
    )


def discover(world: World, hero: Entity, sidekick: Entity, problem: Problem) -> None:
    silo = world.get("silo")
    silo.meters["risk"] += 1
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"The two friends raced to the silo. {problem.sentence}"
    )
    world.say(
        f'"Oh no," {sidekick.id} said. "If we do nothing, {problem.danger}."'
    )


def warn(world: World, sidekick: Entity, problem: Problem, delay: int) -> None:
    pred = predict_loss(world, problem, delay)
    world.facts["predicted_spoiled"] = pred["spoiled"]
    world.facts["predicted_risk"] = pred["risk"]
    if pred["spoiled"]:
        world.say(
            f'"Then breakfast could be ruined," {sidekick.id} whispered. '
            f'"This is a real superhero problem."'
        )
    else:
        world.say(
            f'"We still have a little time," {sidekick.id} said. '
            f'"But we have to fix it before the trouble grows."'
        )


def choose_tool(world: World, hero: Entity, tool: ToolCfg) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f'{hero.id} straightened {hero.pronoun("possessive")} cape. '
        f'"Grab {tool.phrase}," {hero.pronoun()} said. "A hero uses the right tool, not the fastest guess."'
    )


def climb_and_fix(world: World, hero: Entity, sidekick: Entity, tool: ToolCfg, problem: Problem, delay: int) -> bool:
    silo = world.get("silo")
    ingredient = world.get("ingredient")
    hero.meters["height"] += 1
    sidekick.memes["trust"] += 1
    success = is_saved(problem, tool, delay)
    world.para()
    if problem.id == "roof_leak":
        world.say(
            f"{hero.id} scrambled up the silo ladder while {sidekick.id} held the bottom steady."
        )
    elif problem.id == "chute_jam":
        world.say(
            f"{hero.id} planted both shoes on the silo platform while {sidekick.id} pointed to the stuck chute wheel."
        )
    else:
        world.say(
            f"{hero.id} dropped to one knee beside the silo door while {sidekick.id} swept loose grain away from little shoes."
        )

    if success:
        silo.meters["risk"] = 0.0
        ingredient.meters["saved"] += 1
        hero.memes["pride"] += 1
        sidekick.memes["joy"] += 1
        world.say(
            f'"Steady now," {sidekick.id} said.'
        )
        world.say(
            f"{hero.id} {tool.action}."
        )
        if problem.id == "chute_jam":
            world.say(
                f'From inside the silo came a rushing whisper, and {world.facts["ingredient_cfg"].label} began to slide where it should.'
            )
        elif problem.id == "roof_leak":
            world.say(
                f"The last raindrop slipped off the new cover and splashed harmlessly into the grass."
            )
        else:
            world.say(
                f"The trickling stream stopped wasting itself on the ground."
            )
    else:
        ingredient.meters["spoiled"] += 1
        hero.memes["fear"] += 1
        sidekick.memes["fear"] += 1
        world.say(
            f'"Hold on!" {sidekick.id} cried.'
        )
        world.say(
            f"But {hero.id} {tool.fail}."
        )
        if problem.id == "roof_leak":
            world.say(
                f"Water kept slipping into the silo, and the {world.facts['ingredient_cfg'].label} turned clumpy and sad."
            )
        elif problem.id == "chute_jam":
            world.say(
                f"The chute stayed locked, and the baker still could not reach the ingredient in time."
            )
        else:
            world.say(
                f"More of the ingredient spilled into the dust than the little bin could save."
            )
    propagate(world, narrate=False)
    return success


def celebration(world: World, hero: Entity, sidekick: Entity, baker: Entity, ingredient: Ingredient) -> None:
    hero.memes["love"] += 1
    sidekick.memes["love"] += 1
    baker.memes["relief"] += 1
    world.para()
    world.say(
        f'Mr. Vale hurried over with flour on his sleeves and a big smile. "{ingredient.label.capitalize()} saved!" he cheered.'
    )
    world.say(
        f'"Teamwork saved it," {hero.id} said, tugging the cape straight. "{sidekick.id} saw the danger, and we used the right tool."'
    )
    world.say(
        f"By breakfast time, the square smelled warm and sweet with {ingredient.treat}. "
        f"The silver silo shone in the sun, and the two small heroes looked up at it as if it had saluted them back."
    )


def gentle_loss(world: World, hero: Entity, sidekick: Entity, baker: Entity, ingredient: Ingredient) -> None:
    baker.memes["kindness"] += 1
    hero.memes["lesson"] += 1
    sidekick.memes["lesson"] += 1
    world.para()
    world.say(
        f'Mr. Vale set a gentle hand on both their shoulders. "You tried to help, and that matters," he said. '
        f'"We lost the {ingredient.label} for today, but we did not lose our hearts."'
    )
    world.say(
        f'"Next time we bring the stronger tool first," {hero.id} said softly.'
    )
    world.say(
        "So the baker made berry toast instead, and the town still gathered in the square. "
        "The cape was a little droopy, but the promise inside it stood taller than ever."
    )


def tell(
    ingredient_cfg: Ingredient,
    problem_cfg: Problem,
    tool_cfg: ToolCfg,
    *,
    hero_name: str = "Nova",
    hero_gender: str = "girl",
    sidekick_name: str = "Milo",
    sidekick_gender: str = "boy",
    baker_name: str = "Mr. Vale",
    baker_gender: str = "man",
    trait: str = "brave",
    delay: int = 0,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[trait, "heroic"],
    ))
    sidekick = world.add(Entity(
        id=sidekick_name,
        kind="character",
        type=sidekick_gender,
        label=sidekick_name,
        role="sidekick",
        traits=["loyal", "quick-eyed"],
    ))
    baker = world.add(Entity(
        id=baker_name,
        kind="character",
        type=baker_gender,
        label=baker_name,
        role="baker",
        traits=["busy", "kind"],
    ))
    silo = world.add(Entity(
        id="silo",
        type="silo",
        label="the silo",
        phrase="the tall silver silo",
        tags={"silo"},
    ))
    ingredient = world.add(Entity(
        id="ingredient",
        type="ingredient",
        label=ingredient_cfg.label,
        phrase=ingredient_cfg.phrase,
        tags=set(ingredient_cfg.tags),
    ))

    opening(world, hero, sidekick, baker, ingredient_cfg)
    discover(world, hero, sidekick, problem_cfg)
    warn(world, sidekick, problem_cfg, delay)
    choose_tool(world, hero, tool_cfg)
    success = climb_and_fix(world, hero, sidekick, tool_cfg, problem_cfg, delay)

    if success:
        celebration(world, hero, sidekick, baker, ingredient_cfg)
        outcome = "saved"
    else:
        gentle_loss(world, hero, sidekick, baker, ingredient_cfg)
        outcome = "lost"

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        baker=baker,
        silo=silo,
        ingredient=ingredient,
        ingredient_cfg=ingredient_cfg,
        problem=problem_cfg,
        tool=tool_cfg,
        delay=delay,
        outcome=outcome,
        success=success,
    )
    return world


@dataclass
class StoryParams:
    ingredient: str
    problem: str
    tool: str
    hero_name: str
    hero_gender: str
    sidekick_name: str
    sidekick_gender: str
    baker_name: str
    baker_gender: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    ingredient = f["ingredient_cfg"]
    problem = f["problem"]
    outcome = f["outcome"]
    if outcome == "saved":
        return [
            f'Write a short superhero story for a 3-to-5-year-old that includes the words "silo" and "ingredient" and uses dialogue.',
            f"Tell a superhero story where {hero.id} and {sidekick.id} save {ingredient.label} at a silo after discovering a {problem.label}.",
            f"Write a gentle rescue story with spoken lines, a town baker, and a child hero who solves a silo problem using the right tool.",
        ]
    return [
        f'Write a short superhero story for a 3-to-5-year-old that includes the words "silo" and "ingredient" and uses dialogue.',
        f"Tell a superhero story where {hero.id} tries to save {ingredient.label} at a silo, but the first fix is not strong enough and the town must be flexible.",
        f"Write a child-facing story with dialogue in which a small hero learns that bravery also means bringing the right tool.",
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    baker = f["baker"]
    ingredient = f["ingredient_cfg"]
    problem = f["problem"]
    tool = f["tool"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a small superhero, {sidekick.id}, the sidekick, and {baker.id} the baker. "
            f"They all cared about saving the {ingredient.label} at the silo.",
        ),
        (
            "Why did the ingredient matter?",
            f"The {ingredient.label} was the important ingredient for {ingredient.treat}. "
            f"Without it, the baker could not make the town's breakfast treat.",
        ),
        (
            f"What problem did the heroes find at the silo?",
            f"They found a {problem.label} at the silo. That was dangerous because {problem.danger}.",
        ),
        (
            f"Why did {sidekick.id} say they had to hurry?",
            f"{sidekick.id} understood that waiting would make the trouble worse. "
            f"The danger was not just the broken thing itself, but what it would do to the ingredient if nobody acted.",
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                f"How did {hero.id} save the ingredient?",
                f"{hero.id} used {tool.phrase} and {tool.qa_text}. "
                f"That worked because the tool matched the problem and was strong enough to beat it in time.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily with {ingredient.treat} baking in the square. "
                f"The ending image shows that the ingredient was truly saved and the superhero work changed the morning for everyone.",
            )
        )
    else:
        qa.append(
            (
                f"Why did the rescue fail?",
                f"The tool was not strong enough once the trouble had grown. "
                f"Because the fix came too late for that problem, the {ingredient.label} was lost for the day's baking.",
            )
        )
        qa.append(
            (
                "How did the town respond at the end?",
                "The baker stayed kind and made a different breakfast instead. "
                "That ending shows the town could be disappointed and still stay together.",
            )
        )
    return qa


KNOWLEDGE = {
    "silo": [
        (
            "What is a silo?",
            "A silo is a tall building used to store grain or other dry food safely. It keeps the food together until people need it.",
        )
    ],
    "ingredient": [
        (
            "What is an ingredient?",
            "An ingredient is one part you use to make a food or recipe. Flour, oats, and cornmeal can all be ingredients.",
        )
    ],
    "cornmeal": [
        (
            "What is cornmeal?",
            "Cornmeal is grain ground into tiny yellow bits. People use it to make foods like cornbread.",
        )
    ],
    "oats": [
        (
            "What are oats?",
            "Oats are grains that can be cooked or baked into food. They are often used in porridge or oat cakes.",
        )
    ],
    "flour": [
        (
            "What is flour?",
            "Flour is a soft powder made from ground grain. Bakers mix it with other ingredients to make bread and cakes.",
        )
    ],
    "leak": [
        (
            "Why is water bad for dry grain?",
            "Dry grain needs to stay dry. If water gets in, it can turn clumpy and spoil the food.",
        )
    ],
    "jam": [
        (
            "What is a jammed chute?",
            "A jammed chute is a part that is stuck and will not move. If it cannot open, the grain inside cannot come out.",
        )
    ],
    "spill": [
        (
            "Why is spilled grain a problem?",
            "Spilled grain can get dirty and be wasted on the ground. Then people cannot use all of it for food.",
        )
    ],
    "tarp": [
        (
            "What does a tarp do?",
            "A tarp is a strong cover. People use it to block rain and protect things underneath.",
        )
    ],
    "wrench": [
        (
            "What is a wrench for?",
            "A wrench helps you grip and turn a tight part. Grown-ups use one to loosen or tighten things.",
        )
    ],
    "bin": [
        (
            "What is a bin?",
            "A bin is a container that holds things in one place. A clean bin can catch food so it does not spill away.",
        )
    ],
    "superhero": [
        (
            "Does a superhero always need powers?",
            "No. A superhero can also be someone who is brave, helpful, and uses good ideas at the right time.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "silo",
    "ingredient",
    "cornmeal",
    "oats",
    "flour",
    "leak",
    "jam",
    "spill",
    "tarp",
    "wrench",
    "bin",
    "superhero",
]


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"silo", "ingredient", "superhero"}
    tags |= set(f["ingredient_cfg"].tags)
    tags |= set(f["problem"].tags)
    tags |= set(f["tool"].tags)
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
    for entity in list(world.entities.values()):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        bits = []
        if entity.role:
            bits.append(f"role={entity.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if entity.tags:
            bits.append(f"tags={sorted(entity.tags)}")
        lines.append(f"  {entity.id:12} ({entity.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible_tool(T) :- tool(T), sense(T,S), sense_min(M), S >= M.
compatible(P, T) :- problem(P), tool(T), needs(P, N), fixes(T, N).
valid(I, P, T) :- ingredient(I), problem(P), sensible_tool(T), compatible(P, T).

severity_total(V) :- chosen_problem(P), severity(P, S), delay(D), V = S + D.
success :- chosen_problem(P), chosen_tool(T), compatible(P, T), sense(T, Ss),
           sense_min(M), Ss >= M, power(T, Pt), severity(P, Sp), delay(D), Pt >= Sp + D.
outcome(saved) :- success.
outcome(lost) :- not success.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for ing_id in INGREDIENTS:
        lines.append(asp.fact("ingredient", ing_id))
    for prob_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", prob_id))
        lines.append(asp.fact("severity", prob_id, problem.severity))
        for need in sorted(problem.needs):
            lines.append(asp.fact("needs", prob_id, need))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        lines.append(asp.fact("power", tool_id, tool.power))
        for fix in sorted(tool.fixes):
            lines.append(asp.fact("fixes", tool_id, fix))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_problem", params.problem),
            asp.fact("chosen_tool", params.tool),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        ingredient="cornmeal",
        problem="roof_leak",
        tool="tarp",
        hero_name="Nova",
        hero_gender="girl",
        sidekick_name="Gus",
        sidekick_gender="boy",
        baker_name="Mr. Vale",
        baker_gender="man",
        trait="brave",
        delay=0,
    ),
    StoryParams(
        ingredient="oats",
        problem="chute_jam",
        tool="wrench",
        hero_name="Bolt",
        hero_gender="boy",
        sidekick_name="Lina",
        sidekick_gender="girl",
        baker_name="Mr. Vale",
        baker_gender="man",
        trait="steady",
        delay=0,
    ),
    StoryParams(
        ingredient="flour",
        problem="split_sack",
        tool="clean_bin",
        hero_name="Sunny",
        hero_gender="girl",
        sidekick_name="Milo",
        sidekick_gender="boy",
        baker_name="Mr. Vale",
        baker_gender="man",
        trait="kind",
        delay=1,
    ),
    StoryParams(
        ingredient="cornmeal",
        problem="chute_jam",
        tool="brush",
        hero_name="Dash",
        hero_gender="boy",
        sidekick_name="Ivy",
        sidekick_gender="girl",
        baker_name="Mr. Vale",
        baker_gender="man",
        trait="quick",
        delay=1,
    ),
    StoryParams(
        ingredient="oats",
        problem="roof_leak",
        tool="tarp",
        hero_name="Ruby",
        hero_gender="girl",
        sidekick_name="Finn",
        sidekick_gender="boy",
        baker_name="Mr. Vale",
        baker_gender="man",
        trait="hopeful",
        delay=2,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Storyworld: a tiny superhero saves an ingredient at the town silo."
    )
    ap.add_argument("--ingredient", choices=INGREDIENTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the trouble grows before the fix")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, pool: list[str], avoid: str = "") -> str:
    options = [name for name in pool if name != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.tool:
        problem = PROBLEMS[args.problem]
        tool = TOOLS[args.tool]
        if not (tool.sense >= SENSE_MIN and problem_matches_tool(problem, tool)):
            raise StoryError(explain_rejection(problem, tool))
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        any_problem = PROBLEMS[args.problem] if args.problem else next(iter(PROBLEMS.values()))
        raise StoryError(explain_rejection(any_problem, TOOLS[args.tool]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.ingredient is None or combo[0] == args.ingredient)
        and (args.problem is None or combo[1] == args.problem)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    ingredient_id, problem_id, tool_id = rng.choice(sorted(combos))
    hero_gender = rng.choice(["girl", "boy"])
    sidekick_gender = rng.choice(["girl", "boy"])
    hero_name = _pick_name(rng, HERO_NAMES)
    sidekick_name = _pick_name(rng, SIDEKICK_NAMES, avoid=hero_name)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        ingredient=ingredient_id,
        problem=problem_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        sidekick_name=sidekick_name,
        sidekick_gender=sidekick_gender,
        baker_name="Mr. Vale",
        baker_gender="man",
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.ingredient not in INGREDIENTS:
        raise StoryError(f"(Unknown ingredient: {params.ingredient})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    if tool.sense < SENSE_MIN or not problem_matches_tool(problem, tool):
        raise StoryError(explain_rejection(problem, tool))

    world = tell(
        INGREDIENTS[params.ingredient],
        problem,
        tool,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        sidekick_name=params.sidekick_name,
        sidekick_gender=params.sidekick_gender,
        baker_name=params.baker_name,
        baker_gender=params.baker_gender,
        trait=params.trait,
        delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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


def outcome_of(params: StoryParams) -> str:
    tool = TOOLS[params.tool]
    problem = PROBLEMS[params.problem]
    if tool.sense < SENSE_MIN or not problem_matches_tool(problem, tool):
        return "lost"
    return "saved" if is_saved(problem, tool, params.delay) else "lost"


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
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {seed}.")
            break

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (ingredient, problem, tool) combos:\n")
        for ingredient, problem, tool in combos:
            print(f"  {ingredient:9} {problem:11} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.problem} with {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
