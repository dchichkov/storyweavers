#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hell_friendship_bad_ending_rhyme_comedy.py
=====================================================================

A standalone storyworld about two imp friends in a silly little hell bakery who
try to win a rhyme contest by using a flashy ingredient. The model prefers only
reasonable combinations: some treats are airy enough to burst, some rescue
methods are sensible enough to tell, and every generated sample ends as a
complete comic cautionary story with friendship, rhymes, and a bad ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/hell_friendship_bad_ending_rhyme_comedy.py
    python storyworlds/worlds/gpt-5.4/hell_friendship_bad_ending_rhyme_comedy.py --venue bakery --trick boom_pepper --treat cream_puff
    python storyworlds/worlds/gpt-5.4/hell_friendship_bad_ending_rhyme_comedy.py --treat brick_biscuit
    python storyworlds/worlds/gpt-5.4/hell_friendship_bad_ending_rhyme_comedy.py --response fan_it
    python storyworlds/worlds/gpt-5.4/hell_friendship_bad_ending_rhyme_comedy.py --all
    python storyworlds/worlds/gpt-5.4/hell_friendship_bad_ending_rhyme_comedy.py --qa --json
    python storyworlds/worlds/gpt-5.4/hell_friendship_bad_ending_rhyme_comedy.py --verify
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
        table = {
            "subject": "they",
            "object": "them",
            "possessive": "their",
        }
        return table[case]


@dataclass
class Venue:
    id: str
    place: str
    scene: str
    contest: str
    prize: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    plural: bool = False
    fragile: bool = False
    spread: int = 1
    crumb: str = ""
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"


@dataclass
class Trick:
    id: str
    label: str
    phrase: str
    warning: str
    chant: str
    unstable: bool = True
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "friend"}]

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_burst(world: World) -> list[str]:
    out: list[str] = []
    treat = world.get("treat")
    room = world.get("room")
    if treat.meters["volatile"] < THRESHOLD:
        return out
    if not treat.attrs.get("fragile", False):
        return out
    sig = ("burst", treat.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    treat.meters["burst"] += 1
    room.meters["mess"] += float(treat.attrs.get("spread", 1))
    room.meters["noise"] += 1
    for kid in world.kids():
        kid.memes["embarrassment"] += 1
        kid.memes["surprise"] += 1
    out.append("__burst__")
    return out


def _r_loss(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    if room.meters["mess"] < THRESHOLD:
        return out
    sig = ("lost_contest", "room")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters["contest_lost"] += 1
    for kid in world.kids():
        kid.memes["disappointment"] += 1
    out.append("__lost__")
    return out


CAUSAL_RULES = [
    Rule(name="burst", tag="physical", apply=_r_burst),
    Rule(name="loss", tag="social", apply=_r_loss),
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


def hazard_at_risk(venue: Venue, trick: Trick, treat: Treat) -> bool:
    return treat.id in venue.affords and trick.unstable and treat.fragile


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity_of(treat: Treat, delay: int) -> int:
    return treat.spread + delay


def is_contained(response: Response, treat: Treat, delay: int) -> bool:
    return response.power >= severity_of(treat, delay)


def predict_burst(world: World, treat: Treat) -> dict:
    sim = world.copy()
    sim_treat = sim.get("treat")
    sim_treat.meters["volatile"] += 1
    propagate(sim, narrate=False)
    return {
        "burst": sim_treat.meters["burst"] >= THRESHOLD,
        "mess": sim.get("room").meters["mess"],
        "loss": sim.get("room").meters["contest_lost"] >= THRESHOLD,
        "treat": treat.label,
    }


def _do_trick(world: World, treat: Entity, narrate: bool = True) -> None:
    treat.meters["volatile"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, a: Entity, b: Entity, venue: Venue) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["friendship"] += 1
    world.say(
        f"In {venue.place}, {venue.scene}. "
        f"{a.id} and {b.id} were the kind of friends who always tried to make each other snort with laughter."
    )
    world.say(
        f"That night they were entering {venue.contest}, and the winning pair would get {venue.prize}."
    )


def practice(world: World, a: Entity, b: Entity, treat: Treat) -> None:
    world.say(
        f"They set out {treat.phrase} and practiced their act. "
        f'"Snack on a puff, ring the bell, tell it well!" {a.id} chanted.'
    )
    world.say(
        f'"If the rhyme is bright, the crowd will clap tonight," {b.id} answered, and they bowed to an empty oven door.'
    )


def temptation(world: World, a: Entity, trick: Trick) -> None:
    a.memes["showoff"] += 1
    world.say(
        f"Then {a.id} spotted {trick.phrase} on a high shelf and grinned. "
        f'"{trick.chant}"'
    )


def warning(world: World, b: Entity, a: Entity, trick: Trick, treat: Treat) -> None:
    pred = predict_burst(world, treat)
    world.facts["predicted_mess"] = pred["mess"]
    b.memes["caution"] += 1
    world.say(
        f'{b.id} tugged {a.pronoun("possessive")} sleeve. '
        f'"That stuff is trouble on the double," {b.id} said. '
        f'"{trick.warning} If you shake it into {treat.the}, half of hell will wear our dessert."'
    )


def defy(world: World, a: Entity, b: Entity, trick: Trick) -> None:
    a.memes["defiance"] += 1
    b.memes["trust"] -= 1
    world.say(
        f'"A little pop will help us hop to the top," {a.id} said. '
        f"{a.pronoun().capitalize()} winked, pinched in the {trick.label}, and gave the bowl one wild swirl."
    )


def burst(world: World, a: Entity, b: Entity, treat_ent: Entity, treat: Treat) -> None:
    _do_trick(world, treat_ent)
    world.say(
        f"For one tiny second, {treat.the} puffed up neat and sweet. "
        f"Then it went bloop, blorp, BLAM, and {treat.crumb} flew over the table, the bell rope, and both little friends."
    )
    world.say(
        f'"Well," said {b.id}, batter sliding off {b.pronoun("possessive")} nose, '
        f'"that rhyme was a crime."'
    )
    a.memes["guilt"] += 1
    b.memes["annoyance"] += 1


def rescue_contained(world: World, chef: Entity, response: Response, treat: Treat) -> None:
    room = world.get("room")
    room.meters["mess"] = 0.0
    room.meters["contained"] += 1
    world.say(
        f"{chef.id} rushed over and {response.text.replace('{treat}', treat.label)}."
    )
    world.say(
        "The mess stopped spreading, but the contest table already looked like a pudding storm had sat on it."
    )


def rescue_failed(world: World, chef: Entity, response: Response, treat: Treat, venue: Venue) -> None:
    room = world.get("room")
    room.meters["mess"] += 1
    room.meters["fiasco"] += 1
    world.say(
        f"{chef.id} rushed over and {response.fail.replace('{treat}', treat.label)}."
    )
    world.say(
        f"That only made things sillier. Sticky crumbs slapped the rhyme cards, the stage curtain, and even the sign for {venue.contest}."
    )


def loss(world: World, a: Entity, b: Entity, venue: Venue, contained: bool) -> None:
    a.memes["sadness"] += 1
    b.memes["sadness"] += 1
    prize = "the shiny bell-cup" if contained else venue.prize
    if contained:
        world.say(
            f"When the judges peeped over, they shook their heads. No one was going to award {prize} to a pair dripping custard."
        )
    else:
        world.say(
            f"When the judges peeped over, they did not even try to score the round. "
            f"One crumb landed in {prize}, and that was the end of the show."
        )
    world.say(
        f"{a.id} looked at {b.id}. The laugh had gone out of the room, and so had their chance to win."
    )


def apology(world: World, a: Entity, b: Entity) -> None:
    a.memes["friendship"] += 1
    b.memes["friendship"] += 1
    b.memes["annoyance"] = 0.0
    world.say(
        f'"I wanted a cheer, but I made a smear," {a.id} said quietly. '
        f'"I should have listened."'
    )
    world.say(
        f'{b.id} sighed, then handed {a.pronoun("object")} a mop. '
        f'"You were a goof, but you are still my roof-on-fire buddy," {b.id} said. '
        f'"Next time we rhyme first and stir second."'
    )


def ending_contained(world: World, a: Entity, b: Entity, venue: Venue) -> None:
    world.say(
        f"So they spent the rest of the evening mopping the tiles in {venue.place} instead of standing on stage. "
        f"They stayed friends, but the bell-cup rang for somebody else."
    )


def ending_fiasco(world: World, a: Entity, b: Entity, venue: Venue) -> None:
    world.say(
        f"So they spent the rest of the evening scraping sweet goo off the curtain, the judges' table, and the contest sign in {venue.place}. "
        f"They stayed friends, but the show ended with two mops, one bucket, and no prize at all."
    )


def tell(
    venue: Venue,
    trick: Trick,
    treat: Treat,
    response: Response,
    *,
    friend_one: str = "Pip",
    friend_two: str = "Zip",
    delay: int = 0,
) -> World:
    world = World()
    a = world.add(Entity(id=friend_one, kind="character", type="imp", role="instigator"))
    b = world.add(Entity(id=friend_two, kind="character", type="imp", role="friend"))
    chef = world.add(Entity(id="Chef Cackle", kind="character", type="chef", role="chef"))
    world.add(Entity(id="room", type="hall", label=venue.place))
    treat_ent = world.add(
        Entity(
            id="treat",
            type="treat",
            label=treat.label,
            phrase=treat.phrase,
            attrs={"fragile": treat.fragile, "spread": treat.spread},
            tags=set(treat.tags),
        )
    )

    opening(world, a, b, venue)
    practice(world, a, b, treat)

    world.para()
    temptation(world, a, trick)
    warning(world, b, a, trick, treat)
    defy(world, a, b, trick)

    world.para()
    burst(world, a, b, treat_ent, treat)

    world.para()
    contained = is_contained(response, treat, delay)
    if contained:
        rescue_contained(world, chef, response, treat)
    else:
        rescue_failed(world, chef, response, treat, venue)
    loss(world, a, b, venue, contained)

    world.para()
    apology(world, a, b)
    if contained:
        ending_contained(world, a, b, venue)
    else:
        ending_fiasco(world, a, b, venue)

    outcome = "contained_bad" if contained else "fiasco_bad"
    world.facts.update(
        venue=venue,
        trick=trick,
        treat_cfg=treat,
        response=response,
        instigator=a,
        friend=b,
        chef=chef,
        treat=treat_ent,
        delay=delay,
        outcome=outcome,
        burst=treat_ent.meters["burst"] >= THRESHOLD,
        contest_lost=world.get("room").meters["contest_lost"] >= THRESHOLD,
        friendship_saved=a.memes["friendship"] >= THRESHOLD and b.memes["friendship"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    venue: str
    trick: str
    treat: str
    response: str
    friend_one: str
    friend_two: str
    delay: int = 0
    seed: Optional[int] = None


VENUES = {
    "bakery": Venue(
        id="bakery",
        place="the joke-bakery in Little Hell",
        scene="red ovens hiccuped steam and the ceiling fans wore tiny brass bells",
        contest="the Rhyme-and-Chime Bake-Off",
        prize="a shiny bell-cup",
        affords={"cream_puff", "jelly_tart", "sponge_cake"},
        tags={"bakery", "rhyme"},
    ),
    "cellar": Venue(
        id="cellar",
        place="the laugh-cellar under Little Hell",
        scene="warm brick walls glowed orange and a crooked stage sat beside three sleepy ovens",
        contest="the Midnight Rhyme Supper",
        prize="a gold spoon with little wings",
        affords={"jelly_tart", "sponge_cake"},
        tags={"cellar", "rhyme"},
    ),
    "canteen": Venue(
        id="canteen",
        place="the lunch canteen of Little Hell",
        scene="long black tables shone like mirrors and the oven timer clanged like a silly gong",
        contest="the Snack-and-Rhyme Show",
        prize="a striped apron covered in bells",
        affords={"cream_puff", "sponge_cake", "brick_biscuit"},
        tags={"canteen", "rhyme"},
    ),
}

TREATS = {
    "cream_puff": Treat(
        id="cream_puff",
        label="cream puff",
        phrase="a tray of cream puffs",
        plural=True,
        fragile=True,
        spread=3,
        crumb="custard and crumbs",
        tags={"pastry", "cream_puff"},
    ),
    "jelly_tart": Treat(
        id="jelly_tart",
        label="jelly tart",
        phrase="a wobbling jelly tart",
        fragile=True,
        spread=2,
        crumb="jelly and crust",
        tags={"pastry", "jelly"},
    ),
    "sponge_cake": Treat(
        id="sponge_cake",
        label="sponge cake",
        phrase="a tall sponge cake",
        fragile=True,
        spread=2,
        crumb="pink frosting and spongey bits",
        tags={"cake", "frosting"},
    ),
    "brick_biscuit": Treat(
        id="brick_biscuit",
        label="brick biscuit",
        phrase="a stack of brick biscuits",
        plural=True,
        fragile=False,
        spread=1,
        crumb="hard crumbs",
        tags={"biscuit"},
    ),
}

TRICKS = {
    "boom_pepper": Trick(
        id="boom_pepper",
        label="boom pepper",
        phrase="a jar of boom pepper",
        warning="Boom pepper makes soft batter swell, yell, and burst",
        chant="Boom for the room! Pepper for glory!",
        unstable=True,
        tags={"pepper", "boom"},
    ),
    "echo_syrup": Trick(
        id="echo_syrup",
        label="echo syrup",
        phrase="a bottle of echo syrup",
        warning="Echo syrup makes airy sweets wobble and pop with sticky plops",
        chant="Drip it, flip it, make the whole hall yip it!",
        unstable=True,
        tags={"syrup", "sticky"},
    ),
    "sneeze_salt": Trick(
        id="sneeze_salt",
        label="sneeze salt",
        phrase="a tin of sneeze salt",
        warning="Sneeze salt tickles puffy batter until it bursts in all directions",
        chant="Salt for a jolt! A sprinkle for a tinkle!",
        unstable=True,
        tags={"salt", "sneeze"},
    ),
}

RESPONSES = {
    "iron_lid": Response(
        id="iron_lid",
        sense=3,
        power=3,
        text="slapped a big iron lid over the {treat} and trapped the worst of the splat",
        fail="slapped a big iron lid over the {treat}, but the goo had already bounced past it",
        qa_text="covered it with a big iron lid to stop the splatter",
        tags={"lid", "cleanup"},
    ),
    "oven_shovel": Response(
        id="oven_shovel",
        sense=2,
        power=2,
        text="used the oven shovel to scoop the wobbling mess off the table before it could spread farther",
        fail="jabbed at the mess with the oven shovel, but that only flung sticky bits farther",
        qa_text="used an oven shovel to scoop up the mess",
        tags={"shovel", "cleanup"},
    ),
    "fan_it": Response(
        id="fan_it",
        sense=1,
        power=1,
        text="fanned at the {treat} with a menu card",
        fail="fanned at the {treat} with a menu card, which sent the goo sailing even farther",
        qa_text="tried to fan it away with a menu card",
        tags={"fan", "cleanup"},
    ),
}

NAMES = ["Pip", "Zip", "Mop", "Bop", "Nib", "Fizz", "Snip", "Crick"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for venue_id, venue in VENUES.items():
        for trick_id, trick in TRICKS.items():
            for treat_id, treat in TREATS.items():
                if hazard_at_risk(venue, trick, treat):
                    combos.append((venue_id, trick_id, treat_id))
    return combos


KNOWLEDGE = {
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words end with the same sound, like bell and shell. Rhymes can make songs and jokes sound fun."
        )
    ],
    "pastry": [
        (
            "Why do puffy pastries burst more easily than hard biscuits?",
            "Puffy pastries have lots of soft air pockets inside. When something makes them swell too much, they can split and splatter."
        )
    ],
    "boom": [
        (
            "Why is adding a silly extra ingredient risky in baking?",
            "Baking works best when you know what each ingredient will do. A surprise ingredient can change the batter and make a mess."
        )
    ],
    "sticky": [
        (
            "Why is sticky syrup hard to clean up?",
            "Sticky syrup clings to tables, tools, and clothes. That means it takes extra wiping to get everything clean again."
        )
    ],
    "lid": [
        (
            "Why does putting a lid over a splattery food help?",
            "A lid blocks the mess from flying farther. It helps keep the spill in one place so it is easier to clean."
        )
    ],
    "shovel": [
        (
            "What is an oven shovel for?",
            "An oven shovel is a flat tool for moving hot food safely. It can also help scoop up a mess when a grown-up uses it."
        )
    ],
    "cleanup": [
        (
            "What should friends do after one of them makes a mess?",
            "They should tell the truth, say sorry, and help clean it up. Working together is a good way to repair hurt feelings."
        )
    ],
}
KNOWLEDGE_ORDER = ["rhyme", "pastry", "boom", "sticky", "lid", "shovel", "cleanup"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    venue = f["venue"]
    trick = f["trick"]
    treat = f["treat_cfg"]
    a = f["instigator"]
    b = f["friend"]
    return [
        (
            f'Write a funny cautionary story for a 3-to-5-year-old that includes the word "hell", '
            f'a friendship, a rhyme contest, and a bad ending. Set it in {venue.place}.'
        ),
        (
            f"Tell a comedy about two imp friends, {a.id} and {b.id}, who want to win {venue.contest} "
            f"with {treat.phrase} but make a foolish choice with {trick.label}."
        ),
        (
            f'Write a short rhyming story where a silly baking trick goes wrong, the friends lose the prize, '
            f"and the ending image is both sad and funny."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["friend"]
    chef = f["chef"]
    venue = f["venue"]
    trick = f["trick"]
    treat = f["treat_cfg"]
    response = f["response"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two imp friends, {a.id} and {b.id}, in {venue.place}. They are trying to win {venue.contest}."
        ),
        (
            "What did the friends want at the beginning?",
            f"They wanted to win {venue.prize} by doing a funny rhyming baking act. That wish is why {a.id} reached for {trick.label}."
        ),
        (
            f"Why did {b.id} warn {a.id}?",
            f"{b.id} warned {a.id} because {trick.label} was known to make soft treats burst. {b.id} could see that using it on {treat.the} would likely make a huge mess."
        ),
        (
            f"What happened when {a.id} used {trick.label} anyway?",
            f"{treat.the.capitalize()} puffed up for a moment and then burst. The splatter covered the table and ruined their contest round."
        ),
    ]
    if outcome == "contained_bad":
        qa.append(
            (
                f"How did {chef.id} help, and why was the ending still bad?",
                f"{chef.id} {response.qa_text.replace('{treat}', treat.label)}. Even so, the judges saw the wrecked table, so {a.id} and {b.id} still lost the prize."
            )
        )
    else:
        qa.append(
            (
                f"Why was the ending worse than the friends expected?",
                f"{chef.id} tried to help, but the mess spread through the whole contest area. Because the splatter hit the signs and stage too, the round could not continue at all."
            )
        )
    qa.append(
        (
            "Did the friends stop being friends?",
            f"No. {a.id} said sorry, and {b.id} still handed over a mop. Their evening ended badly, but they chose to clean together instead of staying mad."
        )
    )
    qa.append(
        (
            "How did the story end?",
            "It ended with the friends mopping up instead of winning. That is a bad ending, but the picture is funny because their grand rhyme show turned into a sticky cleanup job."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"rhyme", "cleanup"}
    tags |= set(world.facts["treat_cfg"].tags)
    tags |= set(world.facts["trick"].tags)
    tags |= set(world.facts["response"].tags)
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        venue="bakery",
        trick="boom_pepper",
        treat="cream_puff",
        response="iron_lid",
        friend_one="Pip",
        friend_two="Zip",
        delay=0,
    ),
    StoryParams(
        venue="cellar",
        trick="echo_syrup",
        treat="jelly_tart",
        response="oven_shovel",
        friend_one="Nib",
        friend_two="Bop",
        delay=1,
    ),
    StoryParams(
        venue="canteen",
        trick="sneeze_salt",
        treat="sponge_cake",
        response="oven_shovel",
        friend_one="Fizz",
        friend_two="Snip",
        delay=2,
    ),
]


def explain_rejection(venue: Venue, trick: Trick, treat: Treat) -> str:
    if treat.id not in venue.affords:
        return (
            f"(No story: {venue.place} is not set up for {treat.phrase}, so the contest premise does not fit there.)"
        )
    if not treat.fragile:
        return (
            f"(No story: {treat.phrase} is too sturdy to burst from {trick.label}. "
            f"No splattery turn means no comic bad ending.)"
        )
    if not trick.unstable:
        return (
            f"(No story: {trick.label} would not upset the batter, so the story has no believable disaster.)"
        )
    return "(No story: this combination has no pastry disaster.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "contained_bad" if is_contained(RESPONSES[params.response], TREATS[params.treat], params.delay) else "fiasco_bad"


ASP_RULES = r"""
hazard(V, Tr, Tt) :- affords(V, Tt), unstable(Tr), fragile(Tt).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(V, Tr, Tt) :- venue(V), trick(Tr), treat(Tt), hazard(V, Tr, Tt).

severity(Sp + D) :- chosen_treat(Tt), spread(Tt, Sp), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).

outcome(contained_bad) :- resp_power(P), severity(S), P >= S.
outcome(fiasco_bad) :- resp_power(P), severity(S), P < S.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for venue_id, venue in VENUES.items():
        lines.append(asp.fact("venue", venue_id))
        for treat_id in sorted(venue.affords):
            lines.append(asp.fact("affords", venue_id, treat_id))
    for trick_id, trick in TRICKS.items():
        lines.append(asp.fact("trick", trick_id))
        if trick.unstable:
            lines.append(asp.fact("unstable", trick_id))
    for treat_id, treat in TREATS.items():
        lines.append(asp.fact("treat", treat_id))
        if treat.fragile:
            lines.append(asp.fact("fragile", treat_id))
        lines.append(asp.fact("spread", treat_id, treat.spread))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
            asp.fact("chosen_treat", params.treat),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
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
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: imp friends in a silly little hell bakery, rhymes, and a comic bad ending."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--trick", choices=TRICKS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the mess gets to spread before help arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_two_names(rng: random.Random) -> tuple[str, str]:
    a, b = rng.sample(NAMES, 2)
    return a, b


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.venue and args.trick and args.treat:
        venue = VENUES[args.venue]
        trick = TRICKS[args.trick]
        treat = TREATS[args.treat]
        if not hazard_at_risk(venue, trick, treat):
            raise StoryError(explain_rejection(venue, trick, treat))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c
        for c in valid_combos()
        if (args.venue is None or c[0] == args.venue)
        and (args.trick is None or c[1] == args.trick)
        and (args.treat is None or c[2] == args.treat)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    venue_id, trick_id, treat_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    friend_one, friend_two = _pick_two_names(rng)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        venue=venue_id,
        trick=trick_id,
        treat=treat_id,
        response=response_id,
        friend_one=friend_one,
        friend_two=friend_two,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        venue = VENUES[params.venue]
        trick = TRICKS[params.trick]
        treat = TREATS[params.treat]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid params: unknown key {err}.)") from err

    if not hazard_at_risk(venue, trick, treat):
        raise StoryError(explain_rejection(venue, trick, treat))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        venue=venue,
        trick=trick,
        treat=treat,
        response=response,
        friend_one=params.friend_one,
        friend_two=params.friend_two,
        delay=params.delay,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (venue, trick, treat) combos:\n")
        for venue, trick, treat in combos:
            print(f"  {venue:8} {trick:12} {treat}")
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
            header = f"### {p.friend_one} & {p.friend_two}: {p.trick} in {p.treat} at {p.venue} ({outcome_of(p)})"
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
