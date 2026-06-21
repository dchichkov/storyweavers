#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/apprehensive_orchard_dialogue_conflict_comedy.py
============================================================================

A standalone storyworld about an apprehensive child in an orchard. The stories
are small domestic comedies with lively dialogue and a real conflict: a bold
partner wants a quick, silly shortcut, while an apprehensive child worries about
what might go wrong. The world only permits combinations where the obstacle,
shortcut, and safe fix make common sense.

Run it
------
    python storyworlds/worlds/gpt-5.4/apprehensive_orchard_dialogue_conflict_comedy.py
    python storyworlds/worlds/gpt-5.4/apprehensive_orchard_dialogue_conflict_comedy.py --obstacle high_branch --shortcut climb_crate
    python storyworlds/worlds/gpt-5.4/apprehensive_orchard_dialogue_conflict_comedy.py --shortcut yell_at_goose
    python storyworlds/worlds/gpt-5.4/apprehensive_orchard_dialogue_conflict_comedy.py --all
    python storyworlds/worlds/gpt-5.4/apprehensive_orchard_dialogue_conflict_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/apprehensive_orchard_dialogue_conflict_comedy.py --trace
    python storyworlds/worlds/gpt-5.4/apprehensive_orchard_dialogue_conflict_comedy.py --verify
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
        female = {"girl", "mother", "grandmother", "woman", "aunt"}
        male = {"boy", "father", "grandfather", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Fruit:
    id: str
    label: str
    phrase: str
    pie_name: str
    height_need: int
    soft: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    risk: str
    needs_height: int = 0
    needs_calm: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Shortcut:
    id: str
    label: str
    phrase: str
    sense: int
    reach: int
    calms_goose: bool = False
    bumps_fruit: bool = False
    text: str = ""
    fail_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    sense: int
    reach: int
    calms_goose: bool = False
    gentle: bool = False
    text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def _r_wobble(world: World) -> list[str]:
    hero = world.get("hero")
    fruit = world.get("fruit")
    out: list[str] = []
    if hero.meters["wobbling"] >= THRESHOLD and ("wobble",) not in world.fired:
        world.fired.add(("wobble",))
        hero.memes["fear"] += 1
        world.get("basket").meters["danger"] += 1
        out.append("__wobble__")
        if fruit.meters["hanging"] >= THRESHOLD:
            fruit.meters["swaying"] += 1
    return out


def _r_honk(world: World) -> list[str]:
    goose = world.entities.get("goose")
    hero = world.get("hero")
    partner = world.get("partner")
    out: list[str] = []
    if goose and goose.meters["upset"] >= THRESHOLD and ("honk",) not in world.fired:
        world.fired.add(("honk",))
        hero.memes["fear"] += 1
        partner.memes["surprise"] += 1
        out.append("__honk__")
    return out


def _r_bonk(world: World) -> list[str]:
    fruit = world.get("fruit")
    out: list[str] = []
    if fruit.meters["bonked"] >= THRESHOLD and ("bonk",) not in world.fired:
        world.fired.add(("bonk",))
        world.get("hero").memes["alarm"] += 1
        world.get("partner").memes["alarm"] += 1
        out.append("__bonk__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="honk", tag="social", apply=_r_honk),
    Rule(name="bonk", tag="physical", apply=_r_bonk),
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
        for s in produced:
            world.say(s)
    return produced


FRUITS = {
    "apple": Fruit(
        id="apple",
        label="apple",
        phrase="a shiny red apple",
        pie_name="apple tart",
        height_need=2,
        soft=False,
        tags={"apple", "orchard"},
    ),
    "pear": Fruit(
        id="pear",
        label="pear",
        phrase="a fat yellow pear",
        pie_name="pear pie",
        height_need=2,
        soft=True,
        tags={"pear", "orchard"},
    ),
    "plum": Fruit(
        id="plum",
        label="plum",
        phrase="a deep purple plum",
        pie_name="plum jam tart",
        height_need=1,
        soft=True,
        tags={"plum", "orchard"},
    ),
}

OBSTACLES = {
    "high_branch": Obstacle(
        id="high_branch",
        label="high branch",
        phrase="on a branch much too high for small hands",
        risk="a long reach",
        needs_height=2,
        needs_calm=False,
        tags={"height", "orchard"},
    ),
    "bramble_ring": Obstacle(
        id="bramble_ring",
        label="bramble ring",
        phrase="inside a ring of scratchy brambles under the tree",
        risk="thorny scratches",
        needs_height=1,
        needs_calm=False,
        tags={"bramble", "orchard"},
    ),
    "goose_guard": Obstacle(
        id="goose_guard",
        label="goose guard",
        phrase="right beside a goose who believed everything belonged to him",
        risk="a flapping chase",
        needs_height=1,
        needs_calm=True,
        tags={"goose", "orchard"},
    ),
}

SHORTCUTS = {
    "climb_crate": Shortcut(
        id="climb_crate",
        label="wobbly crate",
        phrase="climb onto a wobbly crate",
        sense=2,
        reach=2,
        text="dragged over an upside-down crate and climbed onto it",
        fail_text="The crate gave a silly little wobble under the shoes",
        qa_text="tried climbing onto a wobbly crate",
        tags={"crate", "shortcut"},
    ),
    "shake_tree": Shortcut(
        id="shake_tree",
        label="shake the tree",
        phrase="shake the tree hard",
        sense=2,
        reach=1,
        bumps_fruit=True,
        text="grabbed the trunk and shook it with both hands",
        fail_text="Leaves fluttered, twigs rattled, and the fruit came down much faster than anyone liked",
        qa_text="tried shaking the tree",
        tags={"tree", "shortcut"},
    ),
    "yell_at_goose": Shortcut(
        id="yell_at_goose",
        label="yell at the goose",
        phrase='yell "Shoo!" at the goose',
        sense=1,
        reach=1,
        calms_goose=False,
        text='cupped both hands and shouted, "Shoo, you feathery grump!"',
        fail_text='The goose answered with an even louder HONK and marched forward as if he had won the argument',
        qa_text='tried yelling at the goose',
        tags={"goose", "shortcut"},
    ),
}

FIXES = {
    "picker": Fix(
        id="picker",
        label="fruit picker",
        phrase="a long fruit picker with a little basket at the end",
        sense=3,
        reach=2,
        gentle=True,
        text="used the long fruit picker, twisted the stem gently, and lowered the fruit into the basket without a bump",
        qa_text="used a long fruit picker to lift the fruit down gently",
        tags={"picker", "tool"},
    ),
    "blanket_path": Fix(
        id="blanket_path",
        label="blanket path",
        phrase="an old blanket laid over the brambles",
        sense=3,
        reach=1,
        gentle=True,
        text="spread an old blanket over the prickly stems, making a soft path to the fruit",
        qa_text="covered the brambles with an old blanket before reaching in",
        tags={"blanket", "bramble", "tool"},
    ),
    "grain_scoop": Fix(
        id="grain_scoop",
        label="grain scoop",
        phrase="a scoop of grain in a tin bowl",
        sense=3,
        reach=1,
        calms_goose=True,
        gentle=True,
        text="set down a little tin bowl of grain a few steps away, and the goose waddled after it with grand importance",
        qa_text="lured the goose aside with a bowl of grain",
        tags={"grain", "goose", "tool"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]
TRAITS = ["apprehensive", "careful", "thoughtful", "watchful"]
PARTNER_TRAITS = ["bold", "sparky", "impatient", "cheerful"]


def sensible_shortcuts() -> list[Shortcut]:
    return [s for s in SHORTCUTS.values() if s.sense >= SENSE_MIN]


def obstacle_supports_shortcut(obstacle: Obstacle, shortcut: Shortcut) -> bool:
    if obstacle.id == "high_branch":
        return shortcut.id in {"climb_crate", "shake_tree"}
    if obstacle.id == "bramble_ring":
        return shortcut.id in {"climb_crate", "shake_tree"}
    if obstacle.id == "goose_guard":
        return shortcut.id in {"yell_at_goose", "shake_tree"}
    return False


def select_fix(obstacle: Obstacle) -> Optional[Fix]:
    return {
        "high_branch": FIXES["picker"],
        "bramble_ring": FIXES["blanket_path"],
        "goose_guard": FIXES["grain_scoop"],
    }.get(obstacle.id)


def shortcut_reaches_fruit(fruit: Fruit, obstacle: Obstacle, shortcut: Shortcut) -> bool:
    need = max(fruit.height_need, obstacle.needs_height)
    return shortcut.reach >= need


def fix_solves(fruit: Fruit, obstacle: Obstacle, fix: Fix) -> bool:
    need = max(fruit.height_need, obstacle.needs_height)
    if fix.reach < need:
        return False
    if obstacle.needs_calm and not fix.calms_goose:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for fruit_id, fruit in FRUITS.items():
        for obstacle_id, obstacle in OBSTACLES.items():
            fix = select_fix(obstacle)
            if not fix or not fix_solves(fruit, obstacle, fix):
                continue
            for shortcut_id, shortcut in SHORTCUTS.items():
                if not obstacle_supports_shortcut(obstacle, shortcut):
                    continue
                if shortcut.id == "yell_at_goose" and obstacle.id != "goose_guard":
                    continue
                if obstacle.id == "goose_guard" and not shortcut_reaches_fruit(fruit, obstacle, shortcut):
                    continue
                if obstacle.id in {"high_branch", "bramble_ring"} and not shortcut_reaches_fruit(fruit, obstacle, shortcut):
                    continue
                if shortcut.sense >= SENSE_MIN or shortcut.id == "yell_at_goose":
                    combos.append((fruit_id, obstacle_id, shortcut_id))
    return sorted(combos)


@dataclass
class StoryParams:
    fruit: str
    obstacle: str
    shortcut: str
    hero_name: str
    hero_gender: str
    partner_name: str
    partner_gender: str
    grownup: str
    hero_trait: str
    partner_trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        fruit="apple",
        obstacle="high_branch",
        shortcut="climb_crate",
        hero_name="Lily",
        hero_gender="girl",
        partner_name="Tom",
        partner_gender="boy",
        grownup="grandmother",
        hero_trait="apprehensive",
        partner_trait="bold",
    ),
    StoryParams(
        fruit="pear",
        obstacle="bramble_ring",
        shortcut="shake_tree",
        hero_name="Max",
        hero_gender="boy",
        partner_name="Mia",
        partner_gender="girl",
        grownup="grandfather",
        hero_trait="watchful",
        partner_trait="cheerful",
    ),
    StoryParams(
        fruit="plum",
        obstacle="goose_guard",
        shortcut="yell_at_goose",
        hero_name="Zoe",
        hero_gender="girl",
        partner_name="Ben",
        partner_gender="boy",
        grownup="grandmother",
        hero_trait="apprehensive",
        partner_trait="impatient",
    ),
    StoryParams(
        fruit="apple",
        obstacle="goose_guard",
        shortcut="shake_tree",
        hero_name="Leo",
        hero_gender="boy",
        partner_name="Anna",
        partner_gender="girl",
        grownup="grandfather",
        hero_trait="careful",
        partner_trait="sparky",
    ),
]


def explain_shortcut_rejection(obstacle: Obstacle, shortcut: Shortcut) -> str:
    if not obstacle_supports_shortcut(obstacle, shortcut):
        return (
            f"(No story: {shortcut.label} does not fit the problem of {obstacle.label}. "
            f"The conflict should come from a tempting shortcut that actually matches the obstacle.)"
        )
    return (
        f"(No story: {shortcut.label} is known here, but it is too weak or too silly for this setup.)"
    )


def explain_combo_rejection(fruit: Fruit, obstacle: Obstacle, shortcut: Shortcut) -> str:
    if not obstacle_supports_shortcut(obstacle, shortcut):
        return explain_shortcut_rejection(obstacle, shortcut)
    if not shortcut_reaches_fruit(fruit, obstacle, shortcut):
        return (
            f"(No story: {shortcut.label} cannot reach {fruit.phrase} {obstacle.phrase}. "
            f"The shortcut would not even get to the fruit.)"
        )
    fix = select_fix(obstacle)
    if not fix or not fix_solves(fruit, obstacle, fix):
        return (
            f"(No story: this orchard problem has no sensible fix in the catalog, "
            f"so the story would have no honest resolution.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
supports_shortcut(high_branch, climb_crate).
supports_shortcut(high_branch, shake_tree).
supports_shortcut(bramble_ring, climb_crate).
supports_shortcut(bramble_ring, shake_tree).
supports_shortcut(goose_guard, yell_at_goose).
supports_shortcut(goose_guard, shake_tree).

fix_for(high_branch, picker).
fix_for(bramble_ring, blanket_path).
fix_for(goose_guard, grain_scoop).

need(F, O, N) :- fruit(F), obstacle(O), fruit_height(F, FH), obstacle_height(O, OH), FH >= OH, N = FH.
need(F, O, N) :- fruit(F), obstacle(O), fruit_height(F, FH), obstacle_height(O, OH), OH > FH, N = OH.

shortcut_reaches(F, O, S) :- shortcut(S), need(F, O, N), reach_s(S, R), R >= N.
fix_reaches(F, O, X) :- fix(X), need(F, O, N), reach_f(X, R), R >= N.

fix_solves(F, O, X) :- fix_for(O, X), fix_reaches(F, O, X), not needs_calm(O).
fix_solves(F, O, X) :- fix_for(O, X), fix_reaches(F, O, X), needs_calm(O), calms(X).

valid(F, O, S) :- fruit(F), obstacle(O), shortcut(S),
                  supports_shortcut(O, S),
                  shortcut_reaches(F, O, S),
                  fix_solves(F, O, _).

sensible_shortcut(S) :- shortcut(S), sense_s(S, N), sense_min(M), N >= M.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for fruit_id, fruit in FRUITS.items():
        lines.append(asp.fact("fruit", fruit_id))
        lines.append(asp.fact("fruit_height", fruit_id, fruit.height_need))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("obstacle_height", obstacle_id, obstacle.needs_height))
        if obstacle.needs_calm:
            lines.append(asp.fact("needs_calm", obstacle_id))
    for shortcut_id, shortcut in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", shortcut_id))
        lines.append(asp.fact("sense_s", shortcut_id, shortcut.sense))
        lines.append(asp.fact("reach_s", shortcut_id, shortcut.reach))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("reach_f", fix_id, fix.reach))
        if fix.calms_goose:
            lines.append(asp.fact("calms", fix_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_shortcuts() -> list[str]:
    import asp

    model = asp.one_model(asp_program("#show sensible_shortcut/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible_shortcut"))


def intro(world: World, hero: Entity, partner: Entity, grownup: Entity, fruit: Fruit, obstacle: Obstacle) -> None:
    hero.memes["apprehension"] += 1
    world.say(
        f"On a bright afternoon in the orchard, {hero.id} followed {partner.id} between the rows of trees while "
        f"{grownup.label_word} carried an empty pie basket."
    )
    world.say(
        f"They spotted {fruit.phrase} {obstacle.phrase}. It looked perfect for {fruit.pie_name}, which made "
        f"{partner.id} grin and made {hero.id} feel a little apprehensive."
    )


def begin_conflict(world: World, hero: Entity, partner: Entity, shortcut: Shortcut) -> None:
    partner.memes["confidence"] += 1
    hero.memes["caution"] += 1
    world.say(
        f'"There it is!" said {partner.id}. "Easy. We can just {shortcut.phrase}."'
    )
    world.say(
        f'{hero.id} wrinkled {hero.pronoun("possessive")} nose. "That does not sound easy. That sounds like the beginning of a silly mistake."'
    )


def predict_shortcut(world: World, fruit: Fruit, obstacle: Obstacle, shortcut: Shortcut) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    goose = sim.entities.get("goose")
    fruit_ent = sim.get("fruit")
    if shortcut.id == "climb_crate":
        hero.meters["wobbling"] += 1
    elif shortcut.id == "shake_tree":
        fruit_ent.meters["bonked"] += 1
        if obstacle.id == "goose_guard" and goose is not None:
            goose.meters["upset"] += 1
    elif shortcut.id == "yell_at_goose" and goose is not None:
        goose.meters["upset"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": hero.memes["fear"],
        "goose_upset": float(goose.meters["upset"]) if goose is not None else 0.0,
        "fruit_bonked": fruit_ent.meters["bonked"],
        "danger": sim.get("basket").meters["danger"],
    }


def warning_dialogue(world: World, hero: Entity, partner: Entity, fruit: Fruit, obstacle: Obstacle, shortcut: Shortcut) -> None:
    pred = predict_shortcut(world, fruit, obstacle, shortcut)
    world.facts["predicted_fear"] = pred["fear"]
    world.facts["predicted_danger"] = pred["danger"]
    if obstacle.id == "high_branch":
        world.say(
            f'"If you {shortcut.phrase}," said {hero.id}, "the crate will wobble, you will windmill your arms, and I will have to watch all of it."'
        )
    elif obstacle.id == "bramble_ring":
        world.say(
            f'"If you {shortcut.phrase}," said {hero.id}, "that fruit may drop right into the thorns. Then we will be chasing dessert through a prickly nest."'
        )
    else:
        world.say(
            f'"If you {shortcut.phrase}," said {hero.id}, "that goose will think we have declared war. I am not ready for war with a bird."'
        )
    if pred["fruit_bonked"] >= THRESHOLD:
        world.say(f'"Also," {hero.pronoun()} added, "the fruit might get bonked before it even reaches the basket."')


def attempt_shortcut(world: World, hero: Entity, partner: Entity, fruit: Fruit, obstacle: Obstacle, shortcut: Shortcut) -> None:
    world.say(f'"Only one quick try," said {partner.id}. Then {partner.pronoun()} {shortcut.text}.')
    hero.memes["alarm"] += 1
    fruit_ent = world.get("fruit")
    goose = world.entities.get("goose")
    if shortcut.id == "climb_crate":
        world.get("hero").meters["wobbling"] += 1
    elif shortcut.id == "shake_tree":
        fruit_ent.meters["bonked"] += 1
        if goose is not None and obstacle.id == "goose_guard":
            goose.meters["upset"] += 1
    elif shortcut.id == "yell_at_goose" and goose is not None:
        goose.meters["upset"] += 1
    propagate(world, narrate=False)

    if shortcut.id == "climb_crate":
        world.say(f"{shortcut.fail_text}. {partner.id}'s hat slid over one eyebrow, which did not improve the plan.")
    elif shortcut.id == "shake_tree":
        world.say(f"{shortcut.fail_text}. {hero.id} hopped backward with both hands over {hero.pronoun('possessive')} head.")
    elif shortcut.id == "yell_at_goose":
        world.say(f"{shortcut.fail_text}. {hero.id} squeaked and hid behind the pie basket.")

    if world.get("hero").memes["fear"] >= THRESHOLD:
        world.say(f'"I was right to be apprehensive," said {hero.id}. "My knees knew it before the rest of me did."')


def grownup_steps_in(world: World, grownup: Entity, hero: Entity, partner: Entity, obstacle: Obstacle) -> None:
    hero.memes["relief"] += 1
    partner.memes["sheepish"] += 1
    if obstacle.id == "goose_guard":
        world.say(
            f'{grownup.label_word.capitalize()} arrived with a calm face and one raised eyebrow. "Why," {grownup.pronoun()} asked, '
            f'"is the goose arguing and why are both of you behind my basket?"'
        )
    else:
        world.say(
            f'{grownup.label_word.capitalize()} turned at the rustle and looked over. "Why," {grownup.pronoun()} asked, '
            f'"does this look less like picking fruit and more like rehearsing a clown act?"'
        )


def apply_fix(world: World, grownup: Entity, hero: Entity, partner: Entity, fruit: Fruit, obstacle: Obstacle, fix: Fix) -> None:
    fruit_ent = world.get("fruit")
    goose = world.entities.get("goose")
    world.say(
        f'"We will do this the orchard way," said {grownup.label_word}. {grownup.pronoun().capitalize()} {fix.text}.'
    )
    if goose is not None and fix.calms_goose:
        goose.meters["upset"] = 0.0
    fruit_ent.meters["picked"] += 1
    fruit_ent.meters["hanging"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f'Soon the {fruit.label} rested safely in the basket. {partner.id} let out a laugh. "{hero.id}," {partner.pronoun()} said, '
        f'"your cautious face just saved the pie."'
    )


def comic_ending(world: World, grownup: Entity, hero: Entity, partner: Entity, obstacle: Obstacle) -> None:
    if obstacle.id == "goose_guard":
        world.say(
            f'The goose kept eating with such dignity that even {partner.id} bowed to him. {hero.id} finally laughed so hard '
            f'{hero.pronoun()} had to hold the basket with both hands.'
        )
    elif obstacle.id == "high_branch":
        world.say(
            f'{partner.id} put the wobbly crate back upside down and patted it. "You tried your best," {partner.pronoun()} told it. '
            f'Even {grownup.label_word} had to laugh.'
        )
    else:
        world.say(
            f'A thorn had caught one leaf in {partner.id}\'s hair like a tiny green feather. When {hero.id} pointed it out, '
            f'everyone laughed, including {partner.id}.'
        )
    world.say(
        f"They walked home through the orchard with the basket between them, and the whole row felt friendlier now that the fruit had been gathered the sensible way."
    )


def tell(
    fruit: Fruit,
    obstacle: Obstacle,
    shortcut: Shortcut,
    fix: Fix,
    hero_name: str,
    hero_gender: str,
    partner_name: str,
    partner_gender: str,
    grownup_type: str,
    hero_trait: str,
    partner_trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[hero_trait],
    ))
    partner = world.add(Entity(
        id="partner",
        kind="character",
        type=partner_gender,
        label=partner_name,
        role="partner",
        traits=[partner_trait],
    ))
    grownup = world.add(Entity(
        id="grownup",
        kind="character",
        type=grownup_type,
        label="the grown-up",
        role="grownup",
    ))
    world.add(Entity(
        id="fruit",
        kind="thing",
        type=fruit.id,
        label=fruit.label,
        phrase=fruit.phrase,
        tags=set(fruit.tags),
    ))
    world.get("fruit").meters["hanging"] = 1.0
    world.add(Entity(id="basket", kind="thing", type="basket", label="basket", phrase="a pie basket"))
    if obstacle.id == "goose_guard":
        world.add(Entity(
            id="goose",
            kind="character",
            type="goose",
            label="the goose",
            phrase="a very opinionated goose",
            tags={"goose"},
        ))

    intro(world, hero, partner, grownup, fruit, obstacle)
    world.para()
    begin_conflict(world, hero, partner, shortcut)
    warning_dialogue(world, hero, partner, fruit, obstacle, shortcut)
    world.say(f'"Oh, come on," said {partner.label}. "What is the worst that could happen?"')
    attempt_shortcut(world, hero, partner, fruit, obstacle, shortcut)
    world.para()
    grownup_steps_in(world, grownup, hero, partner, obstacle)
    apply_fix(world, grownup, hero, partner, fruit, obstacle, fix)
    world.say(f'"Next time," said {hero.label}, "please let my apprehensive ideas go first."')
    world.say(f'"Agreed," said {partner.label}. "They are annoyingly useful."')
    comic_ending(world, grownup, hero, partner, obstacle)

    world.facts.update(
        fruit=fruit,
        obstacle=obstacle,
        shortcut=shortcut,
        fix=fix,
        hero=hero,
        partner=partner,
        grownup=grownup,
        hero_name=hero_name,
        partner_name=partner_name,
        picked=world.get("fruit").meters["picked"] >= THRESHOLD,
        goose_present="goose" in world.entities,
    )
    return world


KNOWLEDGE = {
    "orchard": [(
        "What is an orchard?",
        "An orchard is a place where people grow fruit trees in rows. It is like a farm for fruit."
    )],
    "apple": [(
        "What grows in an orchard?",
        "Many orchards grow fruit such as apples, pears, or plums. The fruit grows on trees and is picked when it is ripe."
    )],
    "pear": [(
        "What is a pear?",
        "A pear is a sweet fruit that is often yellow or green. It is softer than an apple, so it can bruise more easily."
    )],
    "plum": [(
        "Why must you be gentle with a plum?",
        "A plum has soft skin and soft flesh, so a hard bump can squash it. Gentle hands keep it neat and tasty."
    )],
    "goose": [(
        "Why can a goose seem scary?",
        "A goose can flap, honk, and rush forward very loudly. That sudden noise and motion can make people jump back."
    )],
    "picker": [(
        "What is a fruit picker?",
        "A fruit picker is a long tool with a small basket or claw at the end. It helps people reach fruit high in a tree without climbing."
    )],
    "bramble": [(
        "What is a bramble?",
        "A bramble is a prickly plant with thorny stems. It can scratch your skin or catch on clothes."
    )],
    "grain": [(
        "Why would grain help with a goose?",
        "Food can pull an animal's attention away from something else. A calm, gentle distraction often works better than shouting."
    )],
    "shortcut": [(
        "What is a shortcut?",
        "A shortcut is a quick way people hope will save time. Sometimes a shortcut works, but sometimes it creates a new problem."
    )],
}
KNOWLEDGE_ORDER = ["orchard", "apple", "pear", "plum", "goose", "picker", "bramble", "grain", "shortcut"]


def generation_prompts(world: World) -> list[str]:
    fruit = world.facts["fruit"]
    obstacle = world.facts["obstacle"]
    hero = world.facts["hero"]
    partner = world.facts["partner"]
    return [
        f'Write a funny orchard story for a 3-to-5-year-old that includes the word "apprehensive" and lots of dialogue.',
        f"Tell a comedy where {hero.label}, an apprehensive child, clashes with {partner.label} over a silly shortcut for getting {fruit.phrase} {obstacle.phrase}.",
        f"Write a gentle conflict story set in an orchard where a child worries out loud, a shortcut goes wrong, and a grown-up solves the problem sensibly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    fruit = world.facts["fruit"]
    obstacle = world.facts["obstacle"]
    shortcut = world.facts["shortcut"]
    fix = world.facts["fix"]
    hero = world.facts["hero"]
    partner = world.facts["partner"]
    grownup = world.facts["grownup"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, an apprehensive child in an orchard, {partner.label}, who wanted a fast shortcut, and {grownup.label_word}, who helped at the end."
        ),
        (
            f"Why did {hero.label} feel apprehensive?",
            f"{hero.label} felt apprehensive because {partner.label} wanted to {shortcut.phrase} to get {fruit.phrase}. {hero.pronoun('subject').capitalize()} could already imagine the trouble that might come from {obstacle.risk}."
        ),
        (
            f"What was the conflict between {hero.label} and {partner.label}?",
            f"Their conflict was about how to get the fruit. {partner.label} wanted the quick, silly plan, but {hero.label} kept warning that it could turn into a mess."
        ),
        (
            f"What happened when {partner.label} tried the shortcut?",
            f"{partner.label} {shortcut.qa_text}, and the plan immediately felt wrong. That moment proved that {hero.label}'s worried warning had a real reason behind it."
        ),
        (
            f"How did {grownup.label_word} solve the problem?",
            f"{grownup.label_word.capitalize()} {fix.qa_text}. The fix matched the obstacle, so the fruit came down safely instead of causing more trouble."
        ),
        (
            "How did the story end?",
            f"It ended with the fruit safe in the basket and everyone laughing in the orchard. The ending shows that the children changed from arguing about a shortcut to trusting a sensible plan."
        ),
    ]
    if obstacle.id == "goose_guard":
        qa.append((
            "Why did the goose matter in the story?",
            f"The goose made the orchard problem feel noisy and funny, but also real. Yelling only upset him more, while the calm fix moved him aside without a chase."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    fruit = world.facts["fruit"]
    obstacle = world.facts["obstacle"]
    fix = world.facts["fix"]
    tags = {"orchard", "shortcut"}
    if fruit.id in KNOWLEDGE:
        tags.add(fruit.id)
    if obstacle.id == "goose_guard":
        tags.update({"goose", "grain"})
    if obstacle.id == "bramble_ring":
        tags.add("bramble")
    if fix.id == "picker":
        tags.add("picker")
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
    for ent in list(world.entities.values()):
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
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: an apprehensive child, orchard dialogue, and a funny conflict."
    )
    ap.add_argument("--fruit", choices=FRUITS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--grownup", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [x for x in pool if x != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.shortcut:
        obstacle = OBSTACLES[args.obstacle]
        shortcut = SHORTCUTS[args.shortcut]
        if not obstacle_supports_shortcut(obstacle, shortcut):
            raise StoryError(explain_shortcut_rejection(obstacle, shortcut))
    if args.fruit and args.obstacle and args.shortcut:
        fruit = FRUITS[args.fruit]
        obstacle = OBSTACLES[args.obstacle]
        shortcut = SHORTCUTS[args.shortcut]
        if (args.fruit, args.obstacle, args.shortcut) not in set(valid_combos()):
            raise StoryError(explain_combo_rejection(fruit, obstacle, shortcut))

    combos = [
        combo for combo in valid_combos()
        if (args.fruit is None or combo[0] == args.fruit)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.shortcut is None or combo[2] == args.shortcut)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    fruit_id, obstacle_id, shortcut_id = rng.choice(combos)
    hero_gender = rng.choice(["girl", "boy"])
    partner_gender = "boy" if hero_gender == "girl" else "girl"
    hero_name = _pick_name(rng, hero_gender)
    partner_name = _pick_name(rng, partner_gender, avoid=hero_name)
    grownup = args.grownup or rng.choice(["grandmother", "grandfather"])
    return StoryParams(
        fruit=fruit_id,
        obstacle=obstacle_id,
        shortcut=shortcut_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        grownup=grownup,
        hero_trait=rng.choice(TRAITS),
        partner_trait=rng.choice(PARTNER_TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.fruit not in FRUITS or params.obstacle not in OBSTACLES or params.shortcut not in SHORTCUTS:
        raise StoryError("(Invalid params: unknown fruit, obstacle, or shortcut.)")
    combo = (params.fruit, params.obstacle, params.shortcut)
    if combo not in set(valid_combos()):
        raise StoryError(explain_combo_rejection(FRUITS[params.fruit], OBSTACLES[params.obstacle], SHORTCUTS[params.shortcut]))
    fix = select_fix(OBSTACLES[params.obstacle])
    if fix is None:
        raise StoryError("(Invalid params: no fix exists for this obstacle.)")

    world = tell(
        fruit=FRUITS[params.fruit],
        obstacle=OBSTACLES[params.obstacle],
        shortcut=SHORTCUTS[params.shortcut],
        fix=fix,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        grownup_type=params.grownup,
        hero_trait=params.hero_trait,
        partner_trait=params.partner_trait,
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


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: ASP valid combos match Python ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))

    py_sense = sorted(s.id for s in sensible_shortcuts())
    asp_sense = sorted(asp_sensible_shortcuts())
    if py_sense == asp_sense:
        print(f"OK: sensible shortcuts match ({py_sense}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible shortcuts: asp={asp_sense} python={py_sense}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated story was empty")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    parser = build_parser()
    for seed in range(10):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
        except Exception as err:
            rc = 1
            print(f"RANDOM SMOKE TEST FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random generation smoke tests succeeded.")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3.\n#show sensible_shortcut/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (fruit, obstacle, shortcut) combos:\n")
        for fruit, obstacle, shortcut in combos:
            print(f"  {fruit:6} {obstacle:12} {shortcut}")
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
            header = f"### {p.hero_name} and {p.partner_name}: {p.fruit} / {p.obstacle} / {p.shortcut}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
