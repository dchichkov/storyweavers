#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/skinned_pivot_flashback_comedy.py
============================================================

A standalone storyworld about a child who wants to make a funny grand entrance
while carrying a wobbly snack. The danger is not abstract: some floor-and-shoe
combinations make a dramatic pivot a bad idea. A flashback to an earlier tumble
with a skinned knee pushes on the choice, and the ending proves what changed:
either the child chooses a safer flourish, or a grown-up saves the snack just in
time, or the dessert lands with a comic splat.

Run it
------
    python storyworlds/worlds/gpt-5.4/skinned_pivot_flashback_comedy.py
    python storyworlds/worlds/gpt-5.4/skinned_pivot_flashback_comedy.py --route polished_hall --footwear socks --treat cupcake_tower
    python storyworlds/worlds/gpt-5.4/skinned_pivot_flashback_comedy.py --route rug_runner
    python storyworlds/worlds/gpt-5.4/skinned_pivot_flashback_comedy.py --all
    python storyworlds/worlds/gpt-5.4/skinned_pivot_flashback_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/skinned_pivot_flashback_comedy.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
FLASHBACK_BONUS = 2
SHOWOFF_BASE = 4

CAUTIOUS_TRAITS = {"careful", "thoughtful", "steady", "gentle"}


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
        female = {"girl", "mother", "mom", "woman", "aunt", "grandma"}
        male = {"boy", "father", "dad", "man", "uncle", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandpa": "grandpa",
            "grandma": "grandma",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Route:
    id: str
    label: str
    scene: str
    slick: int
    detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Footwear:
    id: str
    label: str
    phrase: str
    slip: int
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    wobble: int
    mess: str
    landing: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeGear:
    id: str
    label: str
    phrase: str
    grip: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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
    hero = world.entities.get("hero")
    treat = world.entities.get("treat")
    room = world.entities.get("room")
    if hero is None or treat is None or room is None:
        return []
    if hero.meters["pivoting"] < THRESHOLD:
        return []
    sig = ("wobble",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    risk = room.meters["risk"]
    if risk >= THRESHOLD:
        treat.meters["wobble"] += risk
        hero.memes["alarm"] += 1
        return ["__wobble__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(i for i in items if not i.startswith("__"))
    if narrate:
        for item in produced:
            world.say(item)
    return produced


def hazard(route: Route, footwear: Footwear, treat: Treat) -> bool:
    return route.slick > 0 and footwear.slip > 0 and treat.wobble > 0


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity(route: Route, footwear: Footwear, treat: Treat, delay: int) -> int:
    return route.slick + footwear.slip + treat.wobble + delay


def initial_caution(trait: str, helper_type: str) -> int:
    score = 2 if trait in CAUTIOUS_TRAITS else 1
    if helper_type in {"grandpa", "grandma"}:
        score += 1
    return score


def would_heed(trait: str, helper_type: str, showoff: int) -> bool:
    caution = initial_caution(trait, helper_type) + FLASHBACK_BONUS
    return caution > showoff


def is_saved(response: Response, route: Route, footwear: Footwear, treat: Treat, delay: int) -> bool:
    return response.power >= severity(route, footwear, treat, delay)


def predict_mishap(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").meters["pivoting"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": sim.get("treat").meters["wobble"],
        "alarm": sim.get("hero").memes["alarm"],
    }


def setup_scene(world: World, hero: Entity, helper: Entity, route: Route, treat: Treat, footwear: Footwear) -> None:
    hero.memes["joy"] += 1
    hero.memes["showoff"] += 1
    world.say(
        f"One busy afternoon, {hero.id} decided that carrying {treat.phrase} across "
        f"{route.scene} should look like a comedy show, not a plain old walk."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} had on {footwear.phrase}, and {route.detail} "
        f'At the far end, {helper.label_word} was waiting by the card table with a napkin folded like a tiny flag.'
    )
    world.say(
        f'"Watch this grand pivot!" {hero.id} announced, lifting {treat.phrase} as if it were treasure.'
    )


def flashback(world: World, hero: Entity) -> None:
    hero.memes["memory"] += 1
    hero.memes["caution"] += FLASHBACK_BONUS
    world.say(
        f"Then a little flashback flickered through {hero.id}'s mind. Last week, one wild hallway spin had ended with a skinned knee, "
        f"a crooked bandage, and a banana sticker that would not stay on straight."
    )
    world.say(
        f"For a second, {hero.pronoun('subject')} could almost hear the old oof again, and the new pivot idea stopped feeling quite so magnificent."
    )


def warning(world: World, hero: Entity, helper: Entity, route: Route, footwear: Footwear, treat: Treat) -> None:
    pred = predict_mishap(world)
    world.facts["predicted_wobble"] = pred["wobble"]
    helper.memes["care"] += 1
    world.say(
        f'{helper.label_word.capitalize()} squinted at {route.label}, then at the {footwear.label}, then at {treat.label}. '
        f'"Funny is wonderful," {helper.pronoun("subject")} said, "but that floor is slick, those {footwear.label if footwear.plural else footwear.label} can slide, '
        f'and {treat.label} likes to wobble before it listens."'
    )


def back_down(world: World, hero: Entity, helper: Entity, gear: SafeGear, treat: Treat) -> None:
    hero.memes["relief"] += 1
    hero.memes["wisdom"] += 1
    world.say(
        f"{hero.id} looked down at the plate, looked down at {hero.pronoun('possessive')} feet, and made a face. "
        f'"Maybe my joke can survive without a giant pivot," {hero.pronoun("subject")} admitted.'
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} swapped into {gear.phrase}, took two tiny steps, made one careful little pivot beside the table, "
        f"and set down {treat.label} without losing a crumb."
    )
    world.say(
        f'{helper.label_word.capitalize()} clapped anyway. "Still funny," {helper.pronoun("subject")} said. "And now the joke does not need a mop."'
    )


def attempt(world: World, hero: Entity) -> None:
    hero.meters["pivoting"] += 1
    propagate(world, narrate=False)


def wobble_beat(world: World, hero: Entity, treat: Treat) -> None:
    hero.memes["alarm"] += 1
    world.say(
        f"But the moment {hero.pronoun('subject')} tried the big pivot, {treat.label} gave a shaky shimmy. "
        f"The whole thing wobbled like it had suddenly remembered it was made for eating, not for dancing."
    )


def rescue(world: World, hero: Entity, helper: Entity, response: Response, treat: Entity) -> None:
    treat.meters["caught"] += 1
    treat.meters["wobble"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["lesson"] += 1
    body = response.text
    world.say(
        f"{helper.label_word.capitalize()} moved fast and {body}."
    )
    world.say(
        f"{hero.id}'s mouth made a tiny O. Then {hero.pronoun('subject')} laughed first, because the plate had survived and because {helper.label_word} looked very proud of that save."
    )


def rescue_fail(world: World, hero: Entity, helper: Entity, response: Response, treat: Entity, treat_cfg: Treat) -> None:
    treat.meters["spilled"] += 1
    hero.memes["embarrassment"] += 1
    hero.memes["lesson"] += 1
    room = world.get("room")
    room.meters["mess"] += 1
    body = response.fail
    world.say(
        f"{helper.label_word.capitalize()} reached out and {body}."
    )
    world.say(
        f"Instead, {treat_cfg.landing} The room went quiet for one amazed blink, and then even {hero.id} gave a helpless little laugh at the disaster."
    )


def lesson(world: World, hero: Entity, helper: Entity, gear: SafeGear, treat: Treat) -> None:
    hero.memes["love"] += 1
    world.say(
        f'{helper.label_word.capitalize()} knelt beside {hero.id} and tapped the floor with one finger. '
        f'"Big jokes need small choices under them," {helper.pronoun("subject")} said. "Good shoes, steady hands, then a tiny pivot if you still want sparkle."'
    )
    world.say(
        f"{hero.id} nodded and switched into {gear.phrase}. On the second trip, {hero.pronoun('subject')} walked with careful feet, made one neat little pivot near the table, and everyone cheered."
    )
    world.say(
        f"This time the laugh came at the right part: {treat.label} stayed safe, and {hero.id} took the bow instead."
    )


ROUTES = {
    "polished_hall": Route(
        id="polished_hall",
        label="the polished hall",
        scene="the polished hall",
        slick=2,
        detail="The floor gleamed so brightly that it looked as if it had already practiced slipping.",
        tags={"slippery", "hall"},
    ),
    "kitchen_tiles": Route(
        id="kitchen_tiles",
        label="the kitchen tiles",
        scene="the kitchen tiles",
        slick=1,
        detail="The tiles were clean and a little shiny, the sort that liked to surprise socks.",
        tags={"slippery", "kitchen"},
    ),
    "rug_runner": Route(
        id="rug_runner",
        label="the rug runner",
        scene="the rug runner",
        slick=0,
        detail="The rug gripped the floor so firmly that even a silly dance would have trouble causing trouble.",
        tags={"rug"},
    ),
}

FOOTWEAR = {
    "socks": Footwear(
        id="socks",
        label="socks",
        phrase="striped socks",
        slip=2,
        plural=True,
        tags={"socks"},
    ),
    "flippers": Footwear(
        id="flippers",
        label="flippers",
        phrase="oversized joke flippers from the dress-up box",
        slip=2,
        plural=True,
        tags={"flippers", "costume"},
    ),
    "fuzzy_slippers": Footwear(
        id="fuzzy_slippers",
        label="slippers",
        phrase="fuzzy slippers with sleepy bear faces",
        slip=1,
        plural=True,
        tags={"slippers"},
    ),
    "sneakers": Footwear(
        id="sneakers",
        label="sneakers",
        phrase="good grippy sneakers",
        slip=0,
        plural=True,
        tags={"sneakers"},
    ),
}

TREATS = {
    "jelly_plate": Treat(
        id="jelly_plate",
        label="a plate of jelly toast",
        phrase="a plate of jelly toast cut into stars",
        wobble=1,
        mess="jelly",
        landing="three sticky stars skated onto the floor in different directions.",
        tags={"toast", "jelly"},
    ),
    "lemonade_tray": Treat(
        id="lemonade_tray",
        label="the lemonade tray",
        phrase="a tray of lemonade cups with lemon slices floating on top",
        wobble=2,
        mess="lemonade",
        landing="the lemonade sloshed out in bright little rivers, and one lemon slice stuck to the leg of a chair as if it wanted a better view.",
        tags={"lemonade"},
    ),
    "cupcake_tower": Treat(
        id="cupcake_tower",
        label="the cupcake tower",
        phrase="a little tower of cupcakes with wiggly frosting",
        wobble=2,
        mess="frosting",
        landing="the cupcake tower gave up with dignity, and frosting landed on the floor in soft cheerful blobs.",
        tags={"cupcake", "frosting"},
    ),
}

SAFE_GEARS = {
    "grippy_slippers": SafeGear(
        id="grippy_slippers",
        label="grippy slippers",
        phrase="grippy slippers with rubber stars underneath",
        grip=2,
        tags={"safe_shoes", "slippers"},
    ),
    "sneakers": SafeGear(
        id="sneakers",
        label="sneakers",
        phrase="good grippy sneakers",
        grip=2,
        tags={"safe_shoes", "sneakers"},
    ),
}

RESPONSES = {
    "tray_catch": Response(
        id="tray_catch",
        sense=3,
        power=6,
        text="slid a baking tray under the wobbling snack and caught the whole mess before it could dive",
        fail="slid a baking tray under it, but the wobble was already too wild to tame",
        qa_text="caught it by sliding a baking tray underneath",
        tags={"save", "tray"},
    ),
    "elbow_steady": Response(
        id="elbow_steady",
        sense=3,
        power=5,
        text="steadied the plate with one hand and guided {hero} straight with the other elbow",
        fail="tried to steady the plate with one hand, but the swing was too big",
        qa_text="steadied it with a quick hand and guided the child straight",
        tags={"save", "steady"},
    ),
    "table_slide": Response(
        id="table_slide",
        sense=2,
        power=4,
        text="pulled the little table closer so the snack could land safely before the wobble grew teeth",
        fail="yanked the table closer, but the treat had already tipped past the point of saving",
        qa_text="pulled the table closer so it could land safely",
        tags={"save", "table"},
    ),
    "blow_on_it": Response(
        id="blow_on_it",
        sense=1,
        power=1,
        text="blew at the wobble as if wind might suddenly become glue",
        fail="blew at it, which helped absolutely nothing at all",
        qa_text="tried blowing on it",
        tags={"bad_idea"},
    ),
}

HELPERS = ["mother", "father", "grandpa", "grandma", "aunt", "uncle"]
GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Maya", "Nora"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Theo"]
TRAITS = ["careful", "showy", "curious", "thoughtful", "bouncy", "steady"]


@dataclass
class StoryParams:
    route: str
    footwear: str
    treat: str
    safe_gear: str
    response: str
    hero: str
    hero_gender: str
    helper: str
    trait: str
    showoff: int = SHOWOFF_BASE
    delay: int = 0
    seed: Optional[int] = None


def compatible_safe_gears(route: Route) -> list[str]:
    return [gid for gid, gear in SAFE_GEARS.items() if gear.grip >= route.slick]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for route_id, route in ROUTES.items():
        if not compatible_safe_gears(route):
            continue
        for footwear_id, footwear in FOOTWEAR.items():
            for treat_id, treat in TREATS.items():
                if hazard(route, footwear, treat):
                    combos.append((route_id, footwear_id, treat_id))
    return combos


def tell(
    route: Route,
    footwear: Footwear,
    treat_cfg: Treat,
    safe_gear: SafeGear,
    response: Response,
    hero_name: str,
    hero_gender: str,
    helper_type: str,
    trait: str,
    showoff: int,
    delay: int,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero", traits=[trait]))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label="the helper", role="helper"))
    room = world.add(Entity(id="room", type="room", label=route.label))
    treat = world.add(Entity(id="treat", type="treat", label=treat_cfg.label, phrase=treat_cfg.phrase))
    shoes = world.add(Entity(id="shoes", type="footwear", label=footwear.label, phrase=footwear.phrase))
    room.meters["risk"] = float(severity(route, footwear, treat_cfg, delay))
    hero.attrs["name"] = hero_name

    setup_scene(world, hero, helper, route, treat_cfg, footwear)
    world.para()
    flashback(world, hero)
    warning(world, hero, helper, route, footwear, treat_cfg)

    heeded = would_heed(trait, helper_type, showoff)
    world.facts["heeded"] = heeded

    if heeded:
        world.para()
        back_down(world, hero, helper, safe_gear, treat_cfg)
        outcome = "averted"
    else:
        world.say(
            f'"It will be fine," {hero_name} said, though the plate was already making a suspicious little wobble all by itself.'
        )
        world.para()
        attempt(world, hero)
        wobble_beat(world, hero, treat_cfg)

        if is_saved(response, route, footwear, treat_cfg, delay):
            rescue(world, hero, helper, response, treat)
            world.para()
            lesson(world, hero, helper, safe_gear, treat_cfg)
            outcome = "saved"
        else:
            rescue_fail(world, hero, helper, response, treat, treat_cfg)
            world.para()
            lesson(world, hero, helper, safe_gear, treat_cfg)
            outcome = "splat"

    world.facts.update(
        hero=hero,
        helper=helper,
        route=route,
        footwear=footwear,
        treat_cfg=treat_cfg,
        treat=treat,
        shoes=shoes,
        safe_gear=safe_gear,
        response=response,
        outcome=outcome,
        severity=severity(route, footwear, treat_cfg, delay),
        delay=delay,
        flashback=True,
        hero_name=hero_name,
    )
    return world


KNOWLEDGE = {
    "slippery": [
        (
            "Why can a shiny floor be slippery?",
            "A shiny floor can be slippery because smooth surfaces give your feet less grip. When your feet cannot grip well, they can slide instead of stopping where you want.",
        )
    ],
    "socks": [
        (
            "Why can socks slide on the floor?",
            "Socks are soft and smooth, so they do not grip the floor the way shoes do. On a slick floor, that can make your feet skid.",
        )
    ],
    "flippers": [
        (
            "Why are costume flippers bad shoes for carrying things?",
            "Big costume flippers are silly and fun, but they are clumsy for walking. They make it harder to balance and turn carefully.",
        )
    ],
    "safe_shoes": [
        (
            "What do grippy shoes do?",
            "Grippy shoes help your feet hold onto the floor instead of sliding. That makes careful walking and turning much safer.",
        )
    ],
    "cupcake": [
        (
            "Why can cupcakes tip over easily?",
            "Cupcakes are soft and top-heavy when they have frosting on them. If the plate tilts, they can slide or fall quickly.",
        )
    ],
    "lemonade": [
        (
            "Why does lemonade spill when a tray wobbles?",
            "Liquid moves when the tray moves, so a wobble can send it sloshing over the edge. The faster the wobble, the easier it spills.",
        )
    ],
    "jelly": [
        (
            "Why is jelly messy when it falls?",
            "Jelly is sticky and slippery at the same time. When it falls, it spreads and sticks to lots of things.",
        )
    ],
    "save": [
        (
            "What should you do if something you carry starts to tip?",
            "Stop moving fast and get help right away if a grown-up is nearby. A quick steady hand is much better than trying a bigger trick.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a short look back at something that happened earlier. It helps explain why a character feels or chooses something now.",
        )
    ],
}
KNOWLEDGE_ORDER = ["flashback", "slippery", "socks", "flippers", "safe_shoes", "cupcake", "lemonade", "jelly", "save"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    route = f["route"]
    treat = f["treat_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            'Write a funny story for a 3-to-5-year-old that includes the words "skinned" and "pivot" and uses a flashback.',
            f"Tell a comedy story where {f['hero_name']} wants to make a grand pivot while carrying {treat.phrase}, but a flashback to a skinned knee helps {hero.pronoun('object')} choose a safer joke.",
            f"Write a light family story set on {route.label} where a child almost turns snack delivery into a stunt, then changes the plan and still gets a laugh.",
        ]
    if outcome == "saved":
        return [
            'Write a funny story for a 3-to-5-year-old that includes the words "skinned" and "pivot" and uses a flashback.',
            f"Tell a comedy story where {f['hero_name']} ignores a flashback warning, tries a big pivot with {treat.phrase}, and a grown-up saves the snack just in time.",
            "Write a child-friendly near-disaster story where a silly stunt almost ruins dessert, but the ending shows a safer way to be funny.",
        ]
    return [
        'Write a funny story for a 3-to-5-year-old that includes the words "skinned" and "pivot" and uses a flashback.',
        f"Tell a comedy story where {f['hero_name']} tries a big pivot with {treat.phrase}, the snack lands with a splat, and the family still ends with warmth and a lesson.",
        "Write a light cautionary story where a flashback almost changes a child's choice, but the real lesson arrives after a messy tumble of food instead.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    route = f["route"]
    footwear = f["footwear"]
    treat = f["treat_cfg"]
    safe_gear = f["safe_gear"]
    response = f["response"]
    outcome = f["outcome"]
    helper_word = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {f['hero_name']}, a child who wanted to be funny while carrying {treat.label}, and {helper_word}, who was watching nearby.",
        ),
        (
            "Why did the child want to do a pivot?",
            f"{f['hero_name']} wanted the snack delivery to feel like a comedy performance instead of an ordinary walk. The pivot was meant to be the big funny flourish.",
        ),
        (
            "What happened in the flashback?",
            f"In the flashback, {f['hero_name']} remembered an earlier spin that ended with a skinned knee and a crooked bandage. That memory made the new stunt feel less clever.",
        ),
        (
            f"Why was the trick risky on {route.label}?",
            f"It was risky because {route.label} was slick, {footwear.label} could slide, and {treat.label} was easy to wobble. Those three facts together made a big pivot a bad bet.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"How did {f['hero_name']} solve the problem?",
                f"{f['hero_name']} listened to the warning and changed into {safe_gear.phrase}. Then {hero.pronoun('subject')} made only a tiny careful pivot and set the snack down safely.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with a laugh and no mess. The child still got to be funny, but in a safer way.",
            )
        )
    elif outcome == "saved":
        qa.append(
            (
                f"How did {helper_word} save the snack?",
                f"{helper_word.capitalize()} {response.qa_text.replace('{hero}', f['hero_name'])}. That quick move stopped the wobble before it turned into a spill.",
            )
        )
        qa.append(
            (
                f"What did {f['hero_name']} learn after that?",
                f"{f['hero_name']} learned that good jokes still need steady feet and careful hands. After the save, {hero.pronoun('subject')} switched to {safe_gear.phrase} and tried again more safely.",
            )
        )
    else:
        qa.append(
            (
                "What happened when the rescue failed?",
                f"The treat spilled and made a real mess on the floor. The failed save showed that once a wobble gets too big, funny can turn into cleanup very fast.",
            )
        )
        qa.append(
            (
                f"What did {f['hero_name']} do after the splat?",
                f"After laughing a little at the disaster, {f['hero_name']} listened to {helper_word} and changed into {safe_gear.phrase}. The second trip was careful, and that one worked.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"flashback"}
    route = world.facts["route"]
    footwear = world.facts["footwear"]
    treat = world.facts["treat_cfg"]
    safe_gear = world.facts["safe_gear"]
    response = world.facts["response"]
    tags |= set(route.tags)
    tags |= set(footwear.tags)
    tags |= set(treat.tags)
    tags |= set(safe_gear.tags)
    tags |= set(response.tags)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.traits:
            parts.append(f"traits={ent.traits}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        route="polished_hall",
        footwear="socks",
        treat="jelly_plate",
        safe_gear="grippy_slippers",
        response="table_slide",
        hero="Mia",
        hero_gender="girl",
        helper="grandpa",
        trait="careful",
        showoff=4,
        delay=0,
    ),
    StoryParams(
        route="kitchen_tiles",
        footwear="fuzzy_slippers",
        treat="lemonade_tray",
        safe_gear="sneakers",
        response="elbow_steady",
        hero="Tom",
        hero_gender="boy",
        helper="mother",
        trait="showy",
        showoff=5,
        delay=0,
    ),
    StoryParams(
        route="polished_hall",
        footwear="flippers",
        treat="cupcake_tower",
        safe_gear="sneakers",
        response="table_slide",
        hero="Leo",
        hero_gender="boy",
        helper="aunt",
        trait="bouncy",
        showoff=6,
        delay=1,
    ),
]


def explain_rejection(route: Route, footwear: Footwear, treat: Treat) -> str:
    if route.slick <= 0:
        return (
            f"(No story: {route.label} is not slick enough to make the pivot risky. "
            f"This world only tells versions where the floor, the footwear, and the treat together create a real wobble problem.)"
        )
    if footwear.slip <= 0:
        return (
            f"(No story: {footwear.label} already give good grip, so the pivot would not be a sensible danger here. "
            f"Pick slipperier footwear like socks or costume flippers.)"
        )
    if treat.wobble <= 0:
        return "(No story: this treat would not wobble enough to drive the story.)"
    return "(No story: this combination has no meaningful pivot hazard.)"


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    good = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {good}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_heed(params.trait, params.helper, params.showoff):
        return "averted"
    saved = is_saved(
        RESPONSES[params.response],
        ROUTES[params.route],
        FOOTWEAR[params.footwear],
        TREATS[params.treat],
        params.delay,
    )
    return "saved" if saved else "splat"


ASP_RULES = r"""
hazard(Route, Shoe, Treat) :- route(Route), footwear(Shoe), treat(Treat),
                              slick(Route, Rs), slip(Shoe, Ss), wobble(Treat, Tw),
                              Rs > 0, Ss > 0, Tw > 0.

compatible_gear(Route, Gear) :- route(Route), safe_gear(Gear),
                                slick(Route, Rs), grip(Gear, G), G >= Rs.

valid(Route, Shoe, Treat) :- hazard(Route, Shoe, Treat), compatible_gear(Route, _).

helper_bonus(1) :- helper_type(grandpa).
helper_bonus(1) :- helper_type(grandma).
helper_bonus(0) :- helper_type(H), H != grandpa, H != grandma.

trait_bonus(2) :- chosen_trait(T), cautious_trait(T).
trait_bonus(1) :- chosen_trait(T), not cautious_trait(T).

caution(TB + HB + FB) :- trait_bonus(TB), helper_bonus(HB), flashback_bonus(FB).
heeded :- caution(C), showoff(S), C > S.

severity(Rs + Ss + Tw + D) :- chosen_route(R), slick(R, Rs),
                              chosen_footwear(S), slip(S, Ss),
                              chosen_treat(T), wobble(T, Tw),
                              delay(D).

saved :- chosen_response(R), power(R, P), severity(V), P >= V.

outcome(averted) :- heeded.
outcome(saved)   :- not heeded, saved.
outcome(splat)   :- not heeded, not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        lines.append(asp.fact("slick", route_id, route.slick))
    for footwear_id, footwear in FOOTWEAR.items():
        lines.append(asp.fact("footwear", footwear_id))
        lines.append(asp.fact("slip", footwear_id, footwear.slip))
    for treat_id, treat in TREATS.items():
        lines.append(asp.fact("treat", treat_id))
        lines.append(asp.fact("wobble", treat_id, treat.wobble))
    for gear_id, gear in SAFE_GEARS.items():
        lines.append(asp.fact("safe_gear", gear_id))
        lines.append(asp.fact("grip", gear_id, gear.grip))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("cautious_trait", trait))
    lines.append(asp.fact("flashback_bonus", FLASHBACK_BONUS))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    extra = f"sense_min({SENSE_MIN}).\nsensible(R) :- response(R), sense(R, S), sense_min(M), S >= M."
    model = asp.one_model(asp_program(extra, "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_route", params.route),
            asp.fact("chosen_footwear", params.footwear),
            asp.fact("chosen_treat", params.treat),
            asp.fact("chosen_response", params.response),
            asp.fact("helper_type", params.helper),
            asp.fact("chosen_trait", params.trait),
            asp.fact("showoff", params.showoff),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    python_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if python_valid == clingo_valid:
        print(f"OK: gate matches valid_combos() ({len(python_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    python_sensible = {r.id for r in sensible_responses()}
    clingo_sensible = set(asp_sensible())
    if python_sensible == clingo_sensible:
        print(f"OK: sensible responses match ({sorted(python_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

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
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a silly pivot, a flashback, and a snack that may or may not survive."
    )
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--footwear", choices=FOOTWEAR)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--showoff", type=int, choices=[3, 4, 5, 6, 7])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how late the helper reacts")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python and ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route and args.footwear and args.treat:
        route = ROUTES[args.route]
        footwear = FOOTWEAR[args.footwear]
        treat = TREATS[args.treat]
        if not hazard(route, footwear, treat):
            raise StoryError(explain_rejection(route, footwear, treat))
        if not compatible_safe_gears(route):
            raise StoryError("(No story: there is no reasonable safer shoe for that route.)")

    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.route is None or combo[0] == args.route)
        and (args.footwear is None or combo[1] == args.footwear)
        and (args.treat is None or combo[2] == args.treat)
    ]
    if not combos:
        if args.route and args.route in ROUTES and args.footwear and args.footwear in FOOTWEAR and args.treat and args.treat in TREATS:
            raise StoryError(explain_rejection(ROUTES[args.route], FOOTWEAR[args.footwear], TREATS[args.treat]))
        raise StoryError("(No valid combination matches the given options.)")

    route_id, footwear_id, treat_id = rng.choice(sorted(combos))
    route = ROUTES[route_id]
    safe_gear = rng.choice(sorted(compatible_safe_gears(route)))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    showoff = args.showoff if args.showoff is not None else rng.choice([4, 5, 6])
    delay = args.delay if args.delay is not None else rng.choice([0, 1])

    return StoryParams(
        route=route_id,
        footwear=footwear_id,
        treat=treat_id,
        safe_gear=safe_gear,
        response=response,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        trait=trait,
        showoff=showoff,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        route = ROUTES[params.route]
        footwear = FOOTWEAR[params.footwear]
        treat = TREATS[params.treat]
        safe_gear = SAFE_GEARS[params.safe_gear]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from None

    if not hazard(route, footwear, treat):
        raise StoryError(explain_rejection(route, footwear, treat))
    if params.response not in RESPONSES:
        raise StoryError("(Invalid response.)")
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if safe_gear.id not in compatible_safe_gears(route):
        raise StoryError("(Invalid safe gear for this route.)")
    if params.helper not in HELPERS:
        raise StoryError("(Invalid helper choice.)")

    world = tell(
        route=route,
        footwear=footwear,
        treat_cfg=treat,
        safe_gear=safe_gear,
        response=response,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        helper_type=params.helper,
        trait=params.trait,
        showoff=params.showoff,
        delay=params.delay,
    )

    response_qa = [QAItem(question=q, answer=a) for q, a in story_qa(world)]
    world_qa_items = [QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=response_qa,
        world_qa=world_qa_items,
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
        print(f"{len(combos)} compatible (route, footwear, treat) combos:\n")
        for route, footwear, treat in combos:
            print(f"  {route:14} {footwear:14} {treat}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for params in CURATED:
            samples.append(generate(params))
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
            header = f"### {p.hero}: {p.treat} on {p.route} in {p.footwear} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
