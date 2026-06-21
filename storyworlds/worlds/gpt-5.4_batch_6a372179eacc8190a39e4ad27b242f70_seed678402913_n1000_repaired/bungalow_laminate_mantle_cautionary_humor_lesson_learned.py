#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bungalow_laminate_mantle_cautionary_humor_lesson_learned.py
=======================================================================================

A small standalone storyworld for a cautionary, gently humorous, lesson-learned
fable about rough play in a bungalow with a slippery laminate floor and a
mantle full of wobble-worthy treasures.

The world model rebuilds a tiny tale shape:

- a child invents a silly indoor game on slick laminate,
- a wiser sibling predicts trouble near the mantle,
- the warning is either heeded or ignored,
- a grown-up answers sensibly,
- the ending proves the lesson by showing a safer way to play.

Run it
------
python storyworlds/worlds/gpt-5.4/bungalow_laminate_mantle_cautionary_humor_lesson_learned.py
python storyworlds/worlds/gpt-5.4/bungalow_laminate_mantle_cautionary_humor_lesson_learned.py --game sock_skate --mantle-item blue_vase
python storyworlds/worlds/gpt-5.4/bungalow_laminate_mantle_cautionary_humor_lesson_learned.py --alternative basket_track
python storyworlds/worlds/gpt-5.4/bungalow_laminate_mantle_cautionary_humor_lesson_learned.py --all
python storyworlds/worlds/gpt-5.4/bungalow_laminate_mantle_cautionary_humor_lesson_learned.py --verify
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
BRAVERY_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "sensible", "steady", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Game:
    id: str
    label: str
    opening: str
    motion: str
    object_phrase: str
    risk_text: str
    laugh_line: str
    severity: int
    alt_kinds: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class MantleItem:
    id: str
    label: str
    phrase: str
    article: str
    fragile: bool = True
    severity: int = 1
    shards_word: str = "pieces"
    tags: set[str] = field(default_factory=set)


@dataclass
class Alternative:
    id: str
    label: str
    phrase: str
    kind: str
    setup: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    success: str
    failure: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_slide_becomes_danger(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    mantle_item = world.get("mantle_item")
    for kid in world.kids():
        if kid.meters["sliding"] < THRESHOLD:
            continue
        sig = ("danger", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        speed = int(world.facts["game"].severity)
        kid.meters["speed"] += speed
        room.meters["danger"] += 1
        mantle_item.meters["wobble"] += 1
        for other in world.kids():
            other.memes["fear"] += 1
        out.append("__wobble__")
    return out


CAUSAL_RULES = [
    Rule(name="slide_becomes_danger", tag="physical", apply=_r_slide_becomes_danger),
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


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def hazard_at_risk(game: Game, mantle_item: MantleItem) -> bool:
    return mantle_item.fragile and game.severity >= 1


def alternative_fits(game: Game, alternative: Alternative) -> bool:
    return alternative.kind in game.alt_kinds


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older_sibling = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (3.0 if older_sibling else 0.0)
    return older_sibling and authority > BRAVERY_INIT


def accident_severity(game: Game, mantle_item: MantleItem, delay: int) -> int:
    return game.severity + mantle_item.severity + delay


def is_contained(response: Response, game: Game, mantle_item: MantleItem, delay: int) -> bool:
    return response.power >= accident_severity(game, mantle_item, delay)


def _do_risky_game(world: World, narrate: bool = True) -> None:
    instigator = world.get("instigator")
    instigator.meters["sliding"] += 1
    propagate(world, narrate=narrate)


def predict_wobble(world: World) -> dict:
    sim = world.copy()
    _do_risky_game(sim, narrate=False)
    return {
        "wobble": sim.get("mantle_item").meters["wobble"],
        "danger": sim.get("room").meters["danger"],
    }


def introduce(world: World, a: Entity, b: Entity, parent: Entity, game: Game, mantle_item: MantleItem) -> None:
    world.say(
        f"In a tidy little bungalow with a bright laminate floor, {a.id} and {b.id} found a rainy afternoon too large to waste."
    )
    world.say(
        f"Above the fireplace, the mantle held {mantle_item.article} {mantle_item.label}, as proud and still as a cat pretending not to nap."
    )
    world.say(
        f'{a.id} looked at the long shiny floor and whispered, "{game.opening}"'
    )
    world.say(
        f"{b.id} laughed, because even before the game began, the room already looked ready for mischief."
    )
    world.facts["setting_line"] = f"a bungalow with a bright laminate floor and a mantle holding {mantle_item.article} {mantle_item.label}"


def tempt(world: World, a: Entity, game: Game) -> None:
    a.memes["joy"] += 1
    a.memes["bravado"] += 1
    world.say(
        f"Soon {a.id} was {game.motion}. {game.laugh_line}"
    )
    world.say(f"For one delighted moment, the plan felt cleverer than a fox in a waistcoat.")


def warn(world: World, b: Entity, a: Entity, parent: Entity, game: Game, mantle_item: MantleItem) -> None:
    pred = predict_wobble(world)
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'{b.id} caught {a.pronoun("object")} by the sleeve. "{a.id}, the laminate is too slick for that," {b.pronoun()} said. '
        f'"If you zoom toward the mantle, {mantle_item.article} {mantle_item.label} may wobble, and {parent.label_word} will not call that a game."'
    )


def back_down(world: World, a: Entity, b: Entity, alternative: Alternative) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["bravery"] = 0.0
    world.say(
        f'{a.id} made one last funny skating face, then stopped with both feet flat. "You are right," {a.pronoun()} admitted. "A grand crash would be exciting for only one second."'
    )
    world.say(
        f"Instead, the children chose {alternative.phrase}. The house seemed to let out the small breath it had been holding."
    )


def defy(world: World, a: Entity, b: Entity, game: Game) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"I am as light as a feather and twice as fast," {a.id} declared. Then {a.pronoun()} tried {game.risk_text}.'
    )
    world.say(
        f"{b.id} hopped after {a.pronoun('object')}, but warnings are slow shoes when pride is wearing skates."
    )


def accident(world: World, a: Entity, b: Entity, mantle_item: MantleItem) -> None:
    _do_risky_game(world, narrate=False)
    mantle_ent = world.get("mantle_item")
    room = world.get("room")
    room.meters["danger"] += 1
    mantle_ent.meters["wobble"] += 1
    mantle_ent.meters["risk"] += 1
    world.say(
        f"{a.id} slid farther than meant to, windmilled both arms, and bumped the little hearth stool beneath the mantle."
    )
    world.say(
        f"{mantle_item.article.capitalize()} {mantle_item.label} gave one dreadful wobble. Even the bungalow seemed to gasp."
    )


def alarm(world: World, b: Entity, parent: Entity, mantle_item: MantleItem) -> None:
    world.say(f'"The {mantle_item.label}!" {b.id} cried. "{parent.label_word.capitalize()}!"')


def rescue_success(world: World, parent: Entity, response: Response, mantle_item: MantleItem) -> None:
    world.get("room").meters["danger"] = 0.0
    world.get("mantle_item").meters["wobble"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} hurried in and {response.success.format(item=mantle_item.label)}."
    )
    world.say(
        f"The room went quiet except for one small thump from {a_or_an('heart')} beating fast inside two chests."
    )


def rescue_fail(world: World, parent: Entity, response: Response, mantle_item: MantleItem) -> None:
    item = world.get("mantle_item")
    item.meters["broken"] += 1
    world.get("room").meters["danger"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} rushed in and {response.failure.format(item=mantle_item.label)}."
    )
    world.say(
        f"There came a clink, a crack, and then a silence so complete that even the rain outside seemed embarrassed."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, game: Game, mantle_item: MantleItem, broken: bool) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
        kid.memes["fear"] = 0.0
    if broken:
        world.say(
            f'{parent.label_word.capitalize()} knelt beside them. "{game.label.capitalize()} may feel funny," {parent.pronoun()} said, "but laughter is too expensive when it is paid for with broken things."'
        )
        world.say(
            f"{a.id} looked at the little {mantle_item.shards_word} and wished speed had an undo button."
        )
    else:
        world.say(
            f'{parent.label_word.capitalize()} set a gentle hand on the hearth. "{game.label.capitalize()} may look funny," {parent.pronoun()} said, "but smooth floors send mistakes farther than feet expect."'
        )
        world.say(
            f"{a.id} nodded at once. A near-miss can teach with the same clear voice as a crash, if one is humble enough to hear it."
        )


def safer_end(world: World, a: Entity, b: Entity, parent: Entity, alternative: Alternative, broken: bool) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    if broken:
        world.say(
            f"After the sweeping and the sighing were done, {parent.label_word} helped them choose {alternative.phrase} instead."
        )
    else:
        world.say(
            f"Then {parent.label_word} showed them {alternative.setup}."
        )
    world.say(
        f"Soon {a.id} and {b.id} were playing again, but now {alternative.ending}"
    )
    world.say(
        "And so the children learned that a shiny floor can be a fine place for careful feet, while foolish speed belongs only in stories that want a moral."
    )


def a_or_an(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def tell(
    game: Game,
    mantle_item: MantleItem,
    alternative: Alternative,
    response: Response,
    *,
    instigator: str = "Ned",
    instigator_gender: str = "boy",
    cautioner: str = "June",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    relation: str = "siblings",
    instigator_age: int = 6,
    cautioner_age: int = 8,
    delay: int = 0,
) -> World:
    world = World()
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        phrase=instigator,
        role="instigator",
        age=instigator_age,
        traits=["bold"],
        attrs={"name": instigator, "relation": relation},
    ))
    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner,
        phrase=cautioner,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"name": cautioner, "relation": relation},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        phrase="the parent",
        role="parent",
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label="bungalow sitting room",
        phrase="the bungalow sitting room",
        tags={"bungalow", "laminate", "mantle"},
    ))
    item = world.add(Entity(
        id="mantle_item",
        type="mantle_item",
        label=mantle_item.label,
        phrase=mantle_item.phrase,
        tags=set(mantle_item.tags),
    ))
    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)
    world.facts.update(
        game=game,
        mantle_cfg=mantle_item,
        alternative=alternative,
        response=response,
        instigator=a,
        cautioner=b,
        parent=parent,
        room=room,
    )

    introduce(world, a, b, parent, game, mantle_item)
    world.para()
    tempt(world, a, game)
    warn(world, b, a, parent, game, mantle_item)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, alternative)
        world.para()
        safer_end(world, a, b, parent, alternative, broken=False)
        outcome = "averted"
        broken = False
        severity = 0
    else:
        defy(world, a, b, game)
        world.para()
        accident(world, a, b, mantle_item)
        alarm(world, b, parent, mantle_item)
        severity = accident_severity(game, mantle_item, delay)
        contained = is_contained(response, game, mantle_item, delay)
        world.para()
        if contained:
            rescue_success(world, parent, response, mantle_item)
            lesson(world, parent, a, b, game, mantle_item, broken=False)
            world.para()
            safer_end(world, a, b, parent, alternative, broken=False)
            outcome = "contained"
            broken = False
        else:
            rescue_fail(world, parent, response, mantle_item)
            lesson(world, parent, a, b, game, mantle_item, broken=True)
            world.para()
            safer_end(world, a, b, parent, alternative, broken=True)
            outcome = "broken"
            broken = True

    world.facts.update(
        outcome=outcome,
        broken=broken,
        severity=severity,
        relation=relation,
        promised=a.memes["lesson"] >= THRESHOLD,
    )
    return world


GAMES = {
    "sock_skate": Game(
        id="sock_skate",
        label="sock-skating",
        opening="What if the hallway were a river and my socks were skates?",
        motion="sock-skating across the laminate in striped socks",
        object_phrase="his striped socks",
        risk_text="to skim the whole shiny strip from rug to hearth",
        laugh_line="He whooshed with cheeks puffed out like a proud little kettle",
        severity=2,
        alt_kinds={"grip", "soft_lane"},
        tags={"laminate", "socks", "sliding"},
    ),
    "orange_chase": Game(
        id="orange_chase",
        label="orange-chasing",
        opening="This orange could be a runaway moon!",
        motion="chasing a runaway orange that zipped over the laminate like a tiny golden wheel",
        object_phrase="a runaway orange",
        risk_text="to catch the orange before it escaped under the mantle",
        laugh_line="At one point he nearly bowed to a fruit",
        severity=2,
        alt_kinds={"contain", "soft_lane"},
        tags={"orange", "laminate", "rolling"},
    ),
    "tray_sled": Game(
        id="tray_sled",
        label="tray-sledding",
        opening="A tea tray would make a splendid sled on this shiny floor.",
        motion="sitting on a tea tray and pushing off with heroic little grunts",
        object_phrase="a tea tray",
        risk_text="to launch one more tray-sled run toward the hearth",
        laugh_line="The tray hummed under him like a beetle trying to sing opera",
        severity=3,
        alt_kinds={"soft_lane"},
        tags={"tray", "laminate", "sliding"},
    ),
}

MANTLE_ITEMS = {
    "blue_vase": MantleItem(
        id="blue_vase",
        label="blue vase",
        phrase="a blue vase painted with tiny white leaves",
        article="a",
        fragile=True,
        severity=2,
        shards_word="blue pieces",
        tags={"vase", "mantle", "fragile"},
    ),
    "snow_globe": MantleItem(
        id="snow_globe",
        label="snow globe",
        phrase="a snow globe with a silver church inside",
        article="a",
        fragile=True,
        severity=2,
        shards_word="sparkly bits",
        tags={"snow_globe", "mantle", "fragile"},
    ),
    "china_lamb": MantleItem(
        id="china_lamb",
        label="china lamb",
        phrase="a china lamb with a pink ribbon at its neck",
        article="a",
        fragile=True,
        severity=1,
        shards_word="white chips",
        tags={"china", "mantle", "fragile"},
    ),
    "felt_owl": MantleItem(
        id="felt_owl",
        label="felt owl",
        phrase="a felt owl with button eyes",
        article="a",
        fragile=False,
        severity=0,
        shards_word="soft lint",
        tags={"owl", "mantle"},
    ),
}

ALTERNATIVES = {
    "grip_slippers": Alternative(
        id="grip_slippers",
        label="grip slippers",
        phrase="a pair of grip slippers with rubbery dots",
        kind="grip",
        setup="a pair of grip slippers with rubbery dots on the soles",
        ending="their steps were still playful, but the floor no longer sent them sailing",
        tags={"slippers", "safety"},
    ),
    "rug_road": Alternative(
        id="rug_road",
        label="rug road",
        phrase="a long rug road from sofa to window",
        kind="soft_lane",
        setup="a long rug road from sofa to window, with cushions for borders",
        ending="they marched and pretended and made their jokes on the rug road, where speed had softer manners",
        tags={"rug", "safety"},
    ),
    "basket_track": Alternative(
        id="basket_track",
        label="basket track",
        phrase="a basket track with books for low walls",
        kind="contain",
        setup="a basket track with books for low walls so rolling things stayed where games belonged",
        ending="the orange rolled in cheerful circles inside its basket track instead of fleeing toward the hearth",
        tags={"basket", "safety"},
    ),
}

RESPONSES = {
    "catch_it": Response(
        id="catch_it",
        sense=3,
        power=5,
        success="caught the {item} with both hands before it could leap",
        failure="reached for the {item}, but fingertips and hurry were a blink too late",
        qa_text="caught the mantle item before it fell",
        tags={"catch", "adult_help"},
    ),
    "cushion_drop": Response(
        id="cushion_drop",
        sense=2,
        power=3,
        success="snatched up a sofa cushion and softened the bump so the {item} only rocked and settled",
        failure="threw a cushion under the fall, but the {item} struck the edge and cracked anyway",
        qa_text="used a cushion to soften the fall and save the mantle item",
        tags={"cushion", "adult_help"},
    ),
    "gasp_only": Response(
        id="gasp_only",
        sense=1,
        power=0,
        success="only gasped, which helped no one at all",
        failure="could do no more than gasp, and gasps do not catch falling things",
        qa_text="only gasped",
        tags={"poor_response"},
    ),
}

GIRL_NAMES = ["June", "Mira", "Tess", "Elsie", "Ruby", "Nora", "Lila", "Wren"]
BOY_NAMES = ["Ned", "Ollie", "Theo", "Ben", "Milo", "Finn", "Sam", "Eli"]
TRAITS = ["careful", "sensible", "steady", "thoughtful", "curious", "cheerful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for game_id, game in GAMES.items():
        for item_id, item in MANTLE_ITEMS.items():
            if not hazard_at_risk(game, item):
                continue
            for alt_id, alt in ALTERNATIVES.items():
                if alternative_fits(game, alt):
                    combos.append((game_id, item_id, alt_id))
    return combos


@dataclass
class StoryParams:
    game: str
    mantle_item: str
    alternative: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 6
    cautioner_age: int = 8
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "laminate": [
        (
            "Why can laminate floors feel slippery?",
            "Laminate floors can feel slippery because they are smooth and hard. Socks or fast little feet can slide farther on them than children expect."
        )
    ],
    "mantle": [
        (
            "What is a mantle?",
            "A mantle is the shelf above a fireplace. People often put pictures or decorations on it, so it is not a good place to bump and jostle near."
        )
    ],
    "vase": [
        (
            "Why should you be careful near a vase?",
            "A vase can tip and break if it gets bumped. Broken pieces can be sharp, so grown-ups handle the cleanup."
        )
    ],
    "snow_globe": [
        (
            "What happens if a snow globe falls?",
            "A snow globe can crack or shatter if it falls. Then the glass and the water inside make a mess."
        )
    ],
    "china": [
        (
            "Why is china easy to break?",
            "China is hard but brittle, so a bump or fall can chip or break it. That is why breakable decorations belong away from wild games."
        )
    ],
    "slippers": [
        (
            "What do grip slippers do?",
            "Grip slippers have rubbery dots or strips on the bottom. They help feet hold the floor instead of sliding away."
        )
    ],
    "rug": [
        (
            "Why is a rug safer for indoor play than a slick floor?",
            "A rug gives feet more grip and makes falls softer. It slows silly games down before they turn into accidents."
        )
    ],
    "basket": [
        (
            "Why use walls or a basket for rolling games?",
            "Low walls or a basket keep rolling things in one place. That keeps them from racing under furniture or into breakable things."
        )
    ],
    "adult_help": [
        (
            "What should you do if something breakable starts to fall?",
            "Step back and call a grown-up right away. Reaching wildly can make the accident bigger."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "laminate",
    "mantle",
    "vase",
    "snow_globe",
    "china",
    "slippers",
    "rug",
    "basket",
    "adult_help",
]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two children"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    game = f["game"]
    item = f["mantle_cfg"]
    alt = f["alternative"]
    a = f["instigator"]
    b = f["cautioner"]
    if f["outcome"] == "averted":
        return [
            f'Write a short fable for a young child set in a bungalow with a laminate floor and a mantle. Include the words "bungalow", "laminate", and "mantle".',
            f"Tell a cautionary but gentle story where {a.label} wants to try {game.label}, but {b.label} warns about {item.article} {item.label} on the mantle and stops the trouble before it starts.",
            f"Write a humorous lesson-learned story where the children abandon a silly indoor game and choose {alt.phrase} instead.",
        ]
    if f["outcome"] == "contained":
        return [
            f'Write a fable-like cautionary story using the words "bungalow", "laminate", and "mantle".',
            f"Tell a story where {a.label} ignores a warning, a breakable thing on the mantle wobbles, and a grown-up barely saves the day.",
            f"Write a humorous lesson-learned story that ends with the children choosing {alt.phrase} for safer indoor play.",
        ]
    return [
        f'Write a cautionary fable using the words "bungalow", "laminate", and "mantle".',
        f"Tell a story where a silly game on a slick floor sends danger toward the mantle, something breaks, and the children learn a clear lesson.",
        f"Write a story with a little humor, a sharp warning, and a calm ending that shows wiser play afterward.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    game = f["game"]
    item = f["mantle_cfg"]
    alt = f["alternative"]
    rel = f["relation"]
    pair = pair_noun(a, b, rel)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.label} and {b.label}, in their bungalow. Their parent appears when the game on the laminate floor becomes risky."
        ),
        (
            "Why did the game seem funny at first?",
            f"It seemed funny because {a.label} was {game.motion}, which made the scene look silly instead of dangerous. The humor is what made the bad idea tempting."
        ),
        (
            f"Why did {b.label} warn {a.label}?",
            f"{b.label} warned {a.label} because the laminate floor was slick and the game pointed straight toward the mantle. {b.label} could imagine {item.article} {item.label} wobbling if the play got too fast."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What changed the story before anything broke?",
                f"{a.label} listened and stopped. That choice kept the mantle safe and turned the lesson into a near-miss instead of a crash."
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                f"How did {parent.label_word} solve the problem?",
                f"{parent.label_word.capitalize()} {f['response'].qa_text}. The quick help stopped a wobble from becoming real damage."
            )
        )
        qa.append(
            (
                "What lesson did the children learn?",
                f"They learned that funny speed on a smooth floor can travel farther than a child means it to. After the scare, they chose {alt.phrase} so the game could stay playful without reaching the mantle."
            )
        )
    else:
        qa.append(
            (
                f"What happened to the {item.label}?",
                f"The {item.label} broke after the dangerous slide near the mantle. The broken pieces made the lesson plain, because the children could see what one proud moment had cost."
            )
        )
        qa.append(
            (
                "How did the story end after the mistake?",
                f"It ended calmly, not wildly. After cleanup, the children switched to {alt.phrase}, which proved they had learned to keep indoor fun away from breakable things."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"laminate", "mantle", "adult_help"} | set(f["mantle_cfg"].tags) | set(f["alternative"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if e.age:
            bits.append(f"age={e.age}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:12} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        game="sock_skate",
        mantle_item="blue_vase",
        alternative="grip_slippers",
        response="catch_it",
        instigator="Ned",
        instigator_gender="boy",
        cautioner="June",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        relation="siblings",
        instigator_age=5,
        cautioner_age=8,
        delay=0,
    ),
    StoryParams(
        game="orange_chase",
        mantle_item="snow_globe",
        alternative="basket_track",
        response="catch_it",
        instigator="Milo",
        instigator_gender="boy",
        cautioner="Tess",
        cautioner_gender="girl",
        parent="father",
        trait="sensible",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
        delay=0,
    ),
    StoryParams(
        game="tray_sled",
        mantle_item="china_lamb",
        alternative="rug_road",
        response="cushion_drop",
        instigator="Ruby",
        instigator_gender="girl",
        cautioner="Nora",
        cautioner_gender="girl",
        parent="mother",
        trait="thoughtful",
        relation="siblings",
        instigator_age=7,
        cautioner_age=5,
        delay=1,
    ),
]


def explain_rejection(game: Game, mantle_item: MantleItem, alternative: Optional[Alternative] = None) -> str:
    if not mantle_item.fragile:
        return (
            f"(No story: the mantle item is {mantle_item.label}, which is not breakable enough to support a cautionary turn. "
            f"Pick a fragile mantle object such as a vase, snow globe, or china lamb.)"
        )
    if alternative is not None and not alternative_fits(game, alternative):
        return (
            f"(No story: {alternative.label} does not honestly solve the risk created by {game.label}. "
            f"The safer alternative must match the kind of trouble the game creates.)"
        )
    return "(No story: this combination does not create a clear cautionary problem.)"


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    contained = is_contained(
        RESPONSES[params.response],
        GAMES[params.game],
        MANTLE_ITEMS[params.mantle_item],
        params.delay,
    )
    return "contained" if contained else "broken"


ASP_RULES = r"""
hazard(G, I) :- game(G), mantle_item(I), fragile(I).
fits(G, A) :- game(G), alternative(A), allows(G, K), alt_kind(A, K).
valid(G, I, A) :- hazard(G, I), fits(G, A).

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older_sibling :- relation(siblings), cautioner_age(CA), instigator_age(IA), CA > IA.
bonus(3) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_sibling, authority(A), bravery_init(BR), A > BR.

severity(V) :- chosen_game(G), chosen_item(I), delay(D), game_severity(G, GS), item_severity(I, IS), V = GS + IS + D.
contained :- chosen_response(R), power(R, P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(broken) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for game_id, game in GAMES.items():
        lines.append(asp.fact("game", game_id))
        lines.append(asp.fact("game_severity", game_id, game.severity))
        for kind in sorted(game.alt_kinds):
            lines.append(asp.fact("allows", game_id, kind))
    for item_id, item in MANTLE_ITEMS.items():
        lines.append(asp.fact("mantle_item", item_id))
        if item.fragile:
            lines.append(asp.fact("fragile", item_id))
        lines.append(asp.fact("item_severity", item_id, item.severity))
    for alt_id, alt in ALTERNATIVES.items():
        lines.append(asp.fact("alternative", alt_id))
        lines.append(asp.fact("alt_kind", alt_id, alt.kind))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_game", params.game),
            asp.fact("chosen_item", params.mantle_item),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
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

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small cautionary fable about slippery indoor play in a bungalow."
    )
    ap.add_argument("--game", choices=GAMES)
    ap.add_argument("--mantle-item", choices=MANTLE_ITEMS)
    ap.add_argument("--alternative", choices=ALTERNATIVES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="head start before help fully acts")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combinations via clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.game and args.mantle_item:
        game = GAMES[args.game]
        item = MANTLE_ITEMS[args.mantle_item]
        if not hazard_at_risk(game, item):
            raise StoryError(explain_rejection(game, item))
    if args.game and args.alternative:
        game = GAMES[args.game]
        alt = ALTERNATIVES[args.alternative]
        if not alternative_fits(game, alt):
            item = MANTLE_ITEMS[args.mantle_item] if args.mantle_item else next(
                item for item in MANTLE_ITEMS.values() if item.fragile
            )
            raise StoryError(explain_rejection(game, item, alt))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.game is None or combo[0] == args.game)
        and (args.mantle_item is None or combo[1] == args.mantle_item)
        and (args.alternative is None or combo[2] == args.alternative)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    game_id, item_id, alt_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7, 8], 2)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        game=game_id,
        mantle_item=item_id,
        alternative=alt_id,
        response=response_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        parent=parent,
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.game not in GAMES:
        raise StoryError(f"Unknown game: {params.game}")
    if params.mantle_item not in MANTLE_ITEMS:
        raise StoryError(f"Unknown mantle item: {params.mantle_item}")
    if params.alternative not in ALTERNATIVES:
        raise StoryError(f"Unknown alternative: {params.alternative}")
    if params.response not in RESPONSES:
        raise StoryError(f"Unknown response: {params.response}")

    game = GAMES[params.game]
    item = MANTLE_ITEMS[params.mantle_item]
    alt = ALTERNATIVES[params.alternative]
    response = RESPONSES[params.response]

    if not hazard_at_risk(game, item):
        raise StoryError(explain_rejection(game, item))
    if not alternative_fits(game, alt):
        raise StoryError(explain_rejection(game, item, alt))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        game=game,
        mantle_item=item,
        alternative=alt,
        response=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        delay=params.delay,
    )

    return StorySample(
        params=params,
        story=world.render().replace("instigator", params.instigator).replace("cautioner", params.cautioner),
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (game, mantle_item, alternative) combos:\n")
        for game_id, item_id, alt_id in combos:
            print(f"  {game_id:12} {item_id:11} {alt_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.instigator} and {p.cautioner}: {p.game} near {p.mantle_item} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
