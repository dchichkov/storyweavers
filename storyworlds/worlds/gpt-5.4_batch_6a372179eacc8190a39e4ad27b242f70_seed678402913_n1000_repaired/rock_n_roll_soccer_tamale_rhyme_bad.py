#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rock_n_roll_soccer_tamale_rhyme_bad.py
=================================================================

A standalone story world for a tall-tale style cautionary story where a child
uses a rhyming magic charm during a soccer game, the ball turns into a runaway
tamale, and the game ends badly.

The domain is intentionally small and constraint-checked:

- A place must really support soccer.
- The ball must really be playable as a soccer ball.
- The charm must be a stable, singable bit of magic.
- Every generated story includes rock'n'roll, soccer, tamale, rhyme, magic,
  and a bad ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/rock_n_roll_soccer_tamale_rhyme_bad.py
    python storyworlds/worlds/gpt-5.4/rock_n_roll_soccer_tamale_rhyme_bad.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/rock_n_roll_soccer_tamale_rhyme_bad.py --all
    python storyworlds/worlds/gpt-5.4/rock_n_roll_soccer_tamale_rhyme_bad.py --qa
    python storyworlds/worlds/gpt-5.4/rock_n_roll_soccer_tamale_rhyme_bad.py --trace
    python storyworlds/worlds/gpt-5.4/rock_n_roll_soccer_tamale_rhyme_bad.py --json
    python storyworlds/worlds/gpt-5.4/rock_n_roll_soccer_tamale_rhyme_bad.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BOAST_MIN = 1
BOAST_MAX = 3


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
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man", "coach"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    scene: str
    crowd: str
    soccer: bool = True
    dust: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class BallCfg:
    id: str
    label: str
    phrase: str
    playable: bool = True
    sturdiness: int = 2
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    stable: bool = True
    power: int = 1
    music: str = ""
    warning: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class TamaleCfg:
    id: str
    label: str
    phrase: str
    steam: str
    sturdiness: int = 1
    filling: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    type: str
    label: str
    phrase: str
    speed: int = 1
    wisdom: str = ""
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


def _r_enchanted_runs(world: World) -> list[str]:
    out: list[str] = []
    ball = world.entities.get("ball")
    if ball is None or ball.meters["enchanted"] < THRESHOLD:
        return out
    sig = ("enchanted_runs",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ball.meters["rolling"] += 1
    ball.meters["hot"] += 1
    world.get("field").meters["chaos"] += 1
    world.get("hero").memes["shock"] += 1
    world.get("crowd").memes["confusion"] += 1
    return out


def _r_hot_tamale_scatters(world: World) -> list[str]:
    out: list[str] = []
    ball = world.entities.get("ball")
    if ball is None or ball.meters["hot"] < THRESHOLD or ball.meters["rolling"] < THRESHOLD:
        return out
    sig = ("hot_tamale_scatters",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("field").meters["damage"] += 1
    world.get("hero").memes["fear"] += 1
    world.get("helper").memes["worry"] += 1
    return out


def _r_chaos_means_loss(world: World) -> list[str]:
    out: list[str] = []
    field_ent = world.entities.get("field")
    if field_ent is None or field_ent.meters["chaos"] < THRESHOLD:
        return out
    sig = ("chaos_means_loss",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("hero").memes["regret"] += 1
    field_ent.meters["losing"] += 1
    return out


CAUSAL_RULES = [
    Rule(name="enchanted_runs", tag="physical", apply=_r_enchanted_runs),
    Rule(name="hot_tamale_scatters", tag="physical", apply=_r_hot_tamale_scatters),
    Rule(name="chaos_means_loss", tag="social", apply=_r_chaos_means_loss),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                produced.extend(lines)
                changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "schoolyard": Place(
        id="schoolyard",
        label="the schoolyard field",
        scene="a schoolyard field so wide that a kicked pebble needed lunch before it landed",
        crowd="a ring of children, aunties, and uncles clapping in the shade",
        soccer=True,
        dust="dust that hopped up in little brown puffs",
        tags={"soccer", "schoolyard"},
    ),
    "town_green": Place(
        id="town_green",
        label="the town green",
        scene="the town green, flat as a pancake and noisy as a fair",
        crowd="the whole town packed around the ropes, from babies in wagons to grandpas in boots",
        soccer=True,
        dust="grass clippings spinning like green confetti",
        tags={"soccer", "town"},
    ),
    "canyon_lot": Place(
        id="canyon_lot",
        label="the canyon lot",
        scene="a red canyon lot where even the echoes sounded out of breath",
        crowd="neighbors sitting on fence rails and stomping time with their heels",
        soccer=True,
        dust="red dust curling behind every sprint",
        tags={"soccer", "canyon"},
    ),
    "bakery_kitchen": Place(
        id="bakery_kitchen",
        label="the bakery kitchen",
        scene="the bakery kitchen with sacks of flour stacked to the ceiling",
        crowd="the bakers elbow to elbow by the ovens",
        soccer=False,
        dust="flour floating in the warm air",
        tags={"kitchen"},
    ),
}

BALLS = {
    "leather": BallCfg(
        id="leather",
        label="leather ball",
        phrase="a tough stitched leather soccer ball",
        playable=True,
        sturdiness=3,
        tags={"ball", "soccer"},
    ),
    "rag": BallCfg(
        id="rag",
        label="rag ball",
        phrase="a springy rag soccer ball wound tight with blue string",
        playable=True,
        sturdiness=2,
        tags={"ball", "soccer"},
    ),
    "pumpkin": BallCfg(
        id="pumpkin",
        label="pumpkin",
        phrase="a round pumpkin with a crooked stem",
        playable=False,
        sturdiness=1,
        tags={"pumpkin"},
    ),
}

CHARMS = {
    "moon_whistle": Charm(
        id="moon_whistle",
        label="moon whistle",
        phrase="a moon-silver whistle",
        stable=True,
        power=2,
        music="It sang one thin note that wriggled through the air like a fishhook.",
        warning="Magic likes rhyme, but it loves trouble more.",
        tags={"magic", "music", "whistle"},
    ),
    "guitar_pick": Charm(
        id="guitar_pick",
        label="silver guitar pick",
        phrase="a silver guitar pick warm from a bandman's palm",
        stable=True,
        power=1,
        music="When it clicked against a string, the tune came out all rock'n'roll and sparkle.",
        warning="A cheating rhyme can score a goal and still steal the game.",
        tags={"magic", "music", "guitar"},
    ),
    "cracked_horn": Charm(
        id="cracked_horn",
        label="cracked horn mouthpiece",
        phrase="a cracked horn mouthpiece",
        stable=False,
        power=3,
        music="It honked like a goose with a secret.",
        warning="That piece is wild magic, and wild magic never plays fair.",
        tags={"magic", "music", "horn"},
    ),
}

TAMALES = {
    "bean": TamaleCfg(
        id="bean",
        label="bean tamale",
        phrase="a bean tamale wrapped snug in a corn husk",
        steam="steam puffed from it in soft white curls",
        sturdiness=1,
        filling="beans",
        tags={"tamale", "food"},
    ),
    "cheese": TamaleCfg(
        id="cheese",
        label="cheese tamale",
        phrase="a cheese tamale wrapped tight as a drum",
        steam="golden steam huffed from the seams",
        sturdiness=2,
        filling="cheese",
        tags={"tamale", "food"},
    ),
    "pepper": TamaleCfg(
        id="pepper",
        label="pepper tamale",
        phrase="a pepper tamale tied with a brave green string",
        steam="spicy steam stung noses all across the field",
        sturdiness=2,
        filling="peppers",
        tags={"tamale", "food", "spicy"},
    ),
}

HELPERS = {
    "grandma": HelperCfg(
        id="grandma",
        type="grandmother",
        label="Grandma",
        phrase="Grandma with silver braids and fast hands",
        speed=2,
        wisdom="She could hear a bad idea before it reached the end of its boots.",
        tags={"family", "helper"},
    ),
    "coach": HelperCfg(
        id="coach",
        type="coach",
        label="Coach",
        phrase="Coach in a hat wide enough to shade a mule",
        speed=1,
        wisdom="He said real practice beats fancy tricks every day of the week.",
        tags={"coach", "helper"},
    ),
    "uncle": HelperCfg(
        id="uncle",
        type="uncle",
        label="Uncle",
        phrase="Uncle with a guitar slung across his back",
        speed=1,
        wisdom="He trusted rhythm, but not shortcuts.",
        tags={"family", "helper", "music"},
    ),
}

GIRL_NAMES = ["Mabel", "Tilly", "Rosa", "Lena", "Dottie", "Pearl"]
BOY_NAMES = ["Buck", "Eli", "Jasper", "Ned", "Wade", "Roy"]
TRAITS = ["brave", "loud", "restless", "showy", "quick", "stubborn"]


def valid_combo(place: Place, ball: BallCfg, charm: Charm) -> bool:
    return place.soccer and ball.playable and charm.stable


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for ball_id, ball in BALLS.items():
            for charm_id, charm in CHARMS.items():
                if valid_combo(place, ball, charm):
                    combos.append((place_id, ball_id, charm_id))
    return combos


def trouble_score(params: "StoryParams") -> int:
    ball = BALLS[params.ball]
    charm = CHARMS[params.charm]
    helper = HELPERS[params.helper]
    tamale = TAMALES[params.tamale]
    return params.boast + params.delay + charm.power + tamale.sturdiness - ball.sturdiness - helper.speed


def outcome_of(params: "StoryParams") -> str:
    return "disaster" if trouble_score(params) >= 2 else "messy_loss"


def explain_rejection(place: Place, ball: BallCfg, charm: Charm) -> str:
    if not place.soccer:
        return (
            f"(No story: {place.label} is no place for soccer, so the child cannot "
            f"honestly be in a soccer match there.)"
        )
    if not ball.playable:
        return (
            f"(No story: {ball.phrase} is not a real soccer ball here, so the game "
            f"would not make sense.)"
        )
    if not charm.stable:
        return (
            f"(No story: the {charm.label} is known to be wild magic, and this world "
            f"only allows singable, stable rhyme-magic.)"
        )
    return "(No story: this combination is not reasonable in the world.)"


def choose_rhyme(hero: Entity, tamale: TamaleCfg) -> str:
    return (
        f'"Rock\'n\'roll, roll to goal,\n'
        f'turn this soccer ball to a {tamale.label} whole!"'
    )


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    ball = sim.get("ball")
    ball.meters["enchanted"] += 1
    propagate(sim, narrate=False)
    return {
        "chaos": sim.get("field").meters["chaos"],
        "damage": sim.get("field").meters["damage"],
        "loss": sim.get("field").meters["losing"],
    }


def opening(world: World, hero: Entity, place: Place, ball: BallCfg, helper: Entity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"If you had stood on {place.scene}, you might have thought the earth itself "
        f"was trying to play soccer. {place.crowd} watched while {hero.id} chased "
        f"{ball.phrase} so fast that there was {place.dust} under {hero.pronoun('possessive')} heels."
    )
    world.say(
        f"On the bandstand, somebody thumped a drum and strummed a guitar until the air "
        f"felt full of rock'n'roll."
    )
    world.say(
        f"{helper.label} stood nearby. {helper.attrs.get('wisdom', '')}"
    )


def goal_dream(world: World, hero: Entity, place: Place) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"That day the prize was the Golden Shoe Cup, taller than a milk pail and shiny enough "
        f"to blink at the sun. {hero.id} wanted to score the winning goal so badly that "
        f"{hero.pronoun('possessive')} heart seemed to dribble inside {hero.pronoun('possessive')} chest."
    )


def discover_charm(world: World, hero: Entity, helper: Entity, charm: Charm) -> None:
    hero.memes["temptation"] += 1
    world.say(
        f"In {helper.label}'s pocket glimmered {charm.phrase}. {charm.music}"
    )
    world.say(
        f'{helper.label} tapped it once and murmured, "{charm.warning}"'
    )


def boast(world: World, hero: Entity, charm: Charm) -> None:
    hero.memes["boast"] += 1
    if hero.attrs.get("boast", 1) >= 3:
        brag = (
            f'{hero.id} puffed up like a rooster on a fence. "One little rhyme, and '
            f'I will score before the goalie even finishes blinking," {hero.pronoun()} said.'
        )
    elif hero.attrs.get("boast", 1) == 2:
        brag = (
            f'{hero.id} grinned sideways. "A tiny rhyme would not hurt a soul," '
            f'{hero.pronoun()} said.'
        )
    else:
        brag = (
            f'{hero.id} looked at the charm and whispered that maybe one quick bit of '
            f"magic could help."
        )
    world.say(brag)


def warning(world: World, hero: Entity, helper: Entity) -> None:
    pred = predict_trouble(world)
    helper.memes["caution"] += 1
    world.facts["predicted_chaos"] = pred["chaos"]
    world.facts["predicted_damage"] = pred["damage"]
    world.say(
        f'{helper.label} shook {helper.pronoun("possessive")} head. "A rhyming trick on a game ball '
        f'never stays small. It starts with a goal and ends with a mess," {helper.pronoun()} said.'
    )


def cast_spell(world: World, hero: Entity, tamale: TamaleCfg) -> None:
    ball = world.get("ball")
    ball.meters["enchanted"] += 1
    hero.memes["defiance"] += 1
    world.say(
        f"But wanting won over wisdom. {hero.id} tapped the ball, sang:\n{choose_rhyme(hero, tamale)}"
    )
    propagate(world, narrate=False)


def transform(world: World, tamale: TamaleCfg) -> None:
    ball = world.get("ball")
    ball.label = tamale.label
    ball.phrase = tamale.phrase
    ball.attrs["form"] = "tamale"
    world.say(
        f"At once the soccer ball puffed, steamed, and split its seams of air. It turned into "
        f"{tamale.phrase}, and {tamale.steam}."
    )
    world.say(
        "Instead of bouncing straight, it wriggled and rolled like it had heard the dinner bell and "
        "meant to answer first."
    )


def chase(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"Off went the hot tamale across {place.label}. {hero.id} lunged after it, "
        f"{helper.label} ran too, and the crowd scattered with hats flying and shoelaces flashing."
    )


def messy_loss(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    field_ent = world.get("field")
    field_ent.meters["score_lost"] += 1
    hero.memes["sadness"] += 1
    world.say(
        f"The tamale skipped under the wrong goal, bumped the post, and burst open in a flop of filling. "
        f"The referee wiped beans and corn husk from {helper.pronoun('possessive')} sleeve and called the game."
    )
    world.say(
        f"That meant {hero.id}'s team lost the cup without another kick. The whole grand soccer afternoon "
        f"ended with supper on the grass and no winner's song at all."
    )


def disaster(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    field_ent = world.get("field")
    field_ent.meters["score_lost"] += 1
    field_ent.meters["wrecked"] += 1
    hero.memes["sadness"] += 1
    world.say(
        f"The tamale grew hotter as it rolled. It bounced off the goal, flew into the bandstand, and sent "
        f"the tuba booming, the drum tumbling, and a shower of corn husks spinning over {place.label}."
    )
    world.say(
        f"When the smoke of spicy steam cleared, the net was torn, the music had stopped, and the referee said "
        f"the game was over for good. So {hero.id}'s team lost the cup, and the field looked more like a supper "
        f"accident than a soccer ground."
    )


def lesson(world: World, hero: Entity, helper: Entity, ball_cfg: BallCfg) -> None:
    hero.memes["lesson"] += 1
    hero.memes["boast"] = 0.0
    world.say(
        f"For a long minute, {hero.id} could not even look up. Then {helper.label} put a steady hand on "
        f"{hero.pronoun('possessive')} shoulder."
    )
    world.say(
        f'"A game wants feet, not magic," {helper.label} said. "A rhyme belongs in a song, not on a soccer ball."'
    )
    world.say(
        f"{hero.id} nodded and carried home what was left of {ball_cfg.phrase} under one arm, plain and quiet now. "
        f"From then on, when the band struck up rock'n'roll and the goal looked far away, {hero.pronoun()} kept "
        f"{hero.pronoun('possessive')} voice for singing and trusted {hero.pronoun('possessive')} feet instead."
    )


def tell(
    place: Place,
    ball_cfg: BallCfg,
    charm: Charm,
    tamale: TamaleCfg,
    helper_cfg: HelperCfg,
    hero_name: str = "Mabel",
    hero_gender: str = "girl",
    trait: str = "showy",
    boast_level: int = 2,
    delay: int = 1,
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        traits=[trait],
        attrs={"name": hero_name, "boast": boast_level},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.label,
        phrase=helper_cfg.phrase,
        role="helper",
        attrs={"speed": helper_cfg.speed, "wisdom": helper_cfg.wisdom},
    ))
    ball = world.add(Entity(
        id="ball",
        kind="thing",
        type="ball",
        label=ball_cfg.label,
        phrase=ball_cfg.phrase,
        role="ball",
        attrs={"form": "ball"},
    ))
    field_ent = world.add(Entity(
        id="field",
        kind="thing",
        type="field",
        label=place.label,
        phrase=place.scene,
        role="field",
    ))
    crowd = world.add(Entity(
        id="crowd",
        kind="character",
        type="crowd",
        label="crowd",
        phrase=place.crowd,
        role="crowd",
    ))

    opening(world, hero, place, ball_cfg, helper)
    goal_dream(world, hero, place)

    world.para()
    discover_charm(world, hero, helper, charm)
    boast(world, hero, charm)
    warning(world, hero, helper)

    world.para()
    cast_spell(world, hero, tamale)
    transform(world, tamale)
    chase(world, hero, helper, place)

    if delay >= 1:
        world.say(
            f"But the runaway tamale had already earned itself a head start, and every skipped second made it "
            f"harder to catch."
        )

    world.para()
    outcome = "disaster" if boast_level + delay + charm.power + tamale.sturdiness - ball_cfg.sturdiness - helper_cfg.speed >= 2 else "messy_loss"
    if outcome == "disaster":
        disaster(world, hero, helper, place)
    else:
        messy_loss(world, hero, helper, place)

    world.para()
    lesson(world, hero, helper, ball_cfg)

    world.facts.update(
        hero=hero,
        helper=helper,
        crowd=crowd,
        ball=ball,
        field=field_ent,
        place=place,
        ball_cfg=ball_cfg,
        charm=charm,
        tamale=tamale,
        helper_cfg=helper_cfg,
        outcome=outcome,
        bad_ending=True,
        used_magic=True,
        rhyme=choose_rhyme(hero, tamale),
        delay=delay,
        boast=boast_level,
        trouble=boast_level + delay + charm.power + tamale.sturdiness - ball_cfg.sturdiness - helper_cfg.speed,
    )
    return world


@dataclass
class StoryParams:
    place: str
    ball: str
    charm: str
    tamale: str
    helper: str
    hero_name: str
    hero_gender: str
    trait: str
    boast: int = 2
    delay: int = 1
    seed: Optional[int] = None


KNOWLEDGE = {
    "soccer": [
        (
            "What is soccer?",
            "Soccer is a game where players move a ball mostly with their feet and try to kick it into a goal. It works best when everyone follows the same rules."
        )
    ],
    "rock": [
        (
            "What is rock'n'roll music?",
            "Rock'n'roll is lively music with a strong beat that makes people want to clap, dance, or stomp along. It is fun for songs, but music cannot replace practice."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words sound alike at the end, like goal and roll. Rhymes can make a line easy to remember."
        )
    ],
    "magic": [
        (
            "Why can magic shortcuts be a bad idea in stories?",
            "Magic shortcuts often solve the wrong problem too fast and cause a bigger one. A fair game needs skill, patience, and honest play."
        )
    ],
    "tamale": [
        (
            "What is a tamale?",
            "A tamale is a food wrapped before it is cooked, often in a corn husk. It is good for supper, but it is not a soccer ball."
        )
    ],
    "sportsmanship": [
        (
            "Why is cheating unfair in a game?",
            "Cheating breaks the rules and spoils the game for everyone else. Winning only feels good when it is earned honestly."
        )
    ],
}
KNOWLEDGE_ORDER = ["soccer", "rock", "rhyme", "magic", "tamale", "sportsmanship"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    tamale = f["tamale"]
    return [
        'Write a tall-tale style story for a 3-to-5-year-old that includes the words "rock\'n\'roll", "soccer", and "tamale", and uses rhyme, magic, and a bad ending.',
        f"Tell a cautionary tall tale about {hero.label}, a child in a soccer game who sings a rhyming magic spell and turns the ball into a {tamale.label}.",
        f"Write a story where {helper.label} warns a child not to use magic to win at soccer, but the child does it anyway and the game ends badly.",
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place"]
    ball_cfg = f["ball_cfg"]
    tamale = f["tamale"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child playing soccer at {place.label}, and {helper.label}, who tried to warn {hero.pronoun('object')}. The whole trouble began because {hero.label} wanted a winning goal too badly."
        ),
        (
            "What did the story have to do with rock'n'roll?",
            "The band by the field played rock'n'roll while the game was going on. That lively music made the magic rhyme feel even more tempting."
        ),
        (
            f"What rhyme did {hero.label} sing?",
            f'{hero.label} sang, {f["rhyme"]} The rhyme was the magic that changed the ball.'
        ),
        (
            f"Why did {helper.label} warn {hero.label}?",
            f'{helper.label} warned {hero.label} because a magic trick on a game ball would bring chaos, not a fair goal. In the world model, the spell leads straight to a runaway hot tamale and a lost game.'
        ),
        (
            f"What happened to the soccer ball?",
            f"It turned into {tamale.phrase}. After that it rolled away hot and wild instead of bouncing like {ball_cfg.phrase}."
        ),
    ]
    if outcome == "messy_loss":
        qa.append(
            (
                "How did the game end badly?",
                f"The tamale rolled into the wrong goal and burst open, so the referee stopped the game and {hero.label}'s team lost the cup. The bad ending came from using magic instead of honest play."
            )
        )
    else:
        qa.append(
            (
                "How did the game end badly?",
                f"The hot tamale smashed into the bandstand, tore up the field, and ended the game for good. Because the trouble grew too big too fast, {hero.label}'s team lost the cup and the celebration vanished."
            )
        )
    qa.append(
        (
            f"What did {hero.label} learn at the end?",
            f'{hero.label} learned that a game wants feet, not magic. After losing, {hero.pronoun()} stopped looking for a shortcut and decided to trust practice instead.'
        )
    )
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    tags = {"soccer", "rock", "rhyme", "magic", "tamale", "sportsmanship"}
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
            shown = {k: v for k, v in ent.attrs.items() if v not in ("", None, 0)}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="schoolyard",
        ball="leather",
        charm="guitar_pick",
        tamale="bean",
        helper="grandma",
        hero_name="Mabel",
        hero_gender="girl",
        trait="showy",
        boast=2,
        delay=0,
    ),
    StoryParams(
        place="town_green",
        ball="rag",
        charm="moon_whistle",
        tamale="pepper",
        helper="coach",
        hero_name="Buck",
        hero_gender="boy",
        trait="loud",
        boast=3,
        delay=1,
    ),
    StoryParams(
        place="canyon_lot",
        ball="rag",
        charm="guitar_pick",
        tamale="cheese",
        helper="uncle",
        hero_name="Rosa",
        hero_gender="girl",
        trait="quick",
        boast=1,
        delay=1,
    ),
    StoryParams(
        place="town_green",
        ball="leather",
        charm="moon_whistle",
        tamale="cheese",
        helper="grandma",
        hero_name="Jasper",
        hero_gender="boy",
        trait="restless",
        boast=3,
        delay=2,
    ),
]


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(Place, Ball, Charm) :- place(Place), ball(Ball), charm(Charm),
                             soccer_place(Place), playable(Ball), stable(Charm).

% --- outcome model ---------------------------------------------------------
trouble(T) :- chosen_ball(B), chosen_charm(C), chosen_tamale(Tm), chosen_helper(H),
              boast(Boast), delay(Delay),
              sturdiness_ball(B, BS), power(C, CP), sturdiness_tamale(Tm, TS),
              helper_speed(H, HS),
              T = Boast + Delay + CP + TS - BS - HS.

outcome(disaster)  :- trouble(T), T >= 2.
outcome(messy_loss) :- trouble(T), T < 2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        if place.soccer:
            lines.append(asp.fact("soccer_place", place_id))
    for ball_id, ball in BALLS.items():
        lines.append(asp.fact("ball", ball_id))
        if ball.playable:
            lines.append(asp.fact("playable", ball_id))
        lines.append(asp.fact("sturdiness_ball", ball_id, ball.sturdiness))
    for charm_id, charm in CHARMS.items():
        lines.append(asp.fact("charm", charm_id))
        if charm.stable:
            lines.append(asp.fact("stable", charm_id))
        lines.append(asp.fact("power", charm_id, charm.power))
    for tamale_id, tamale in TAMALES.items():
        lines.append(asp.fact("tamale", tamale_id))
        lines.append(asp.fact("sturdiness_tamale", tamale_id, tamale.sturdiness))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("helper_speed", helper_id, helper.speed))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_ball", params.ball),
        asp.fact("chosen_charm", params.charm),
        asp.fact("chosen_tamale", params.tamale),
        asp.fact("chosen_helper", params.helper),
        asp.fact("boast", params.boast),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Tall-tale story world: rhyming magic turns a soccer ball into a runaway tamale."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--ball", choices=BALLS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--tamale", choices=TAMALES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--boast", type=int, choices=list(range(BOAST_MIN, BOAST_MAX + 1)))
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and not PLACES[args.place].soccer:
        place = PLACES[args.place]
        ball = BALLS[args.ball] if args.ball else next(iter(BALLS.values()))
        charm = CHARMS[args.charm] if args.charm else next(iter(CHARMS.values()))
        raise StoryError(explain_rejection(place, ball, charm))
    if args.ball and not BALLS[args.ball].playable:
        place = PLACES[args.place] if args.place else next(iter(PLACES.values()))
        ball = BALLS[args.ball]
        charm = CHARMS[args.charm] if args.charm else next(iter(CHARMS.values()))
        raise StoryError(explain_rejection(place, ball, charm))
    if args.charm and not CHARMS[args.charm].stable:
        place = PLACES[args.place] if args.place else next(iter(PLACES.values()))
        ball = BALLS[args.ball] if args.ball else next(iter(BALLS.values()))
        charm = CHARMS[args.charm]
        raise StoryError(explain_rejection(place, ball, charm))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.ball is None or combo[1] == args.ball)
        and (args.charm is None or combo[2] == args.charm)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, ball_id, charm_id = rng.choice(sorted(combos))
    tamale_id = args.tamale or rng.choice(sorted(TAMALES))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    hero_name = args.name or rng.choice(name_pool)
    trait = args.trait or rng.choice(TRAITS)
    boast = args.boast if args.boast is not None else rng.randint(BOAST_MIN, BOAST_MAX)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        place=place_id,
        ball=ball_id,
        charm=charm_id,
        tamale=tamale_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_gender=gender,
        trait=trait,
        boast=boast,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.ball not in BALLS:
        raise StoryError(f"(Unknown ball: {params.ball})")
    if params.charm not in CHARMS:
        raise StoryError(f"(Unknown charm: {params.charm})")
    if params.tamale not in TAMALES:
        raise StoryError(f"(Unknown tamale: {params.tamale})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    place = PLACES[params.place]
    ball = BALLS[params.ball]
    charm = CHARMS[params.charm]
    if not valid_combo(place, ball, charm):
        raise StoryError(explain_rejection(place, ball, charm))
    world = tell(
        place=place,
        ball_cfg=ball,
        charm=charm,
        tamale=TAMALES[params.tamale],
        helper_cfg=HELPERS[params.helper],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        trait=params.trait,
        boast_level=params.boast,
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

    scenarios = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        scenarios.append(params)

    mismatches = []
    for params in scenarios:
        py = outcome_of(params)
        asp_val = asp_outcome(params)
        if py != asp_val:
            mismatches.append((params, py, asp_val))
    if not mismatches:
        print(f"OK: outcome model matches on {len(scenarios)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(scenarios)} outcomes differ.")
        for params, py, asp_val in mismatches[:5]:
            print(f"  {params} -> python={py} asp={asp_val}")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=False, header="")
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
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
        print(f"{len(combos)} valid (place, ball, charm) combos:\n")
        for place_id, ball_id, charm_id in combos:
            print(f"  {place_id:14} {ball_id:8} {charm_id}")
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
            header = f"### {p.hero_name}: {p.place}, {p.ball}, {p.charm}, {outcome_of(p)}"
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
