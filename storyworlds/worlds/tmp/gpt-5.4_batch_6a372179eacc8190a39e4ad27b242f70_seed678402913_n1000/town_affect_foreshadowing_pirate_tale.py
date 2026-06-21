#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/town_affect_foreshadowing_pirate_tale.py
===================================================================

A standalone story world about two children in a little harbor town who play
pirates, notice signs of weather changing, and are tempted to untie a small
boat to hurry toward the festival pier. The world uses foreshadowing as live
state: warning signs raise storm risk before the main mistake happens, and the
children's choices decide whether the danger is avoided, neatly rescued, or
turns into a frightening near-disaster.

The seed asks for the words "town" and "affect" and a Pirate Tale style, so the
stories keep a child-facing pretend-pirate frame while grounding the turn in a
small coastal town and in weather that can affect the harbor very quickly.

Run it
------
    python storyworlds/worlds/gpt-5.4/town_affect_foreshadowing_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/town_affect_foreshadowing_pirate_tale.py --craft skiff
    python storyworlds/worlds/gpt-5.4/town_affect_foreshadowing_pirate_tale.py --craft ferry
    python storyworlds/worlds/gpt-5.4/town_affect_foreshadowing_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/town_affect_foreshadowing_pirate_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/town_affect_foreshadowing_pirate_tale.py --qa --json
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "watchful"}


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
    small_craft: bool = False
    sheltered: bool = False
    gives_ride: bool = False
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


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    leader: str
    mate: str
    goal: str
    launch_spot: str
    crew_word: str
    crew_plural: str
    send_off: str


@dataclass
class Sign:
    id: str
    omen: str
    line: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Craft:
    id: str
    label: str
    phrase: str
    tied_where: str
    wobble: str
    owner: str
    exposure: int
    small_craft: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeWay:
    id: str
    phrase: str
    arrival: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in ("instigator", "cautioner")]

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


def _r_rough_water(world: World) -> list[str]:
    out: list[str] = []
    weather = world.entities.get("weather")
    harbor = world.entities.get("harbor")
    boat = world.entities.get("craft")
    if weather is None or harbor is None or boat is None:
        return out
    if weather.meters["storm_risk"] < THRESHOLD:
        return out
    sig = ("rough_water",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    harbor.meters["chop"] += 1
    if boat.small_craft:
        boat.meters["danger"] += 1
    out.append("__foreshadow__")
    return out


def _r_drift(world: World) -> list[str]:
    out: list[str] = []
    weather = world.entities.get("weather")
    boat = world.entities.get("craft")
    if weather is None or boat is None:
        return out
    if boat.meters["untied"] < THRESHOLD or weather.meters["storm_risk"] < THRESHOLD:
        return out
    sig = ("drift",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    boat.meters["drifting"] += 1
    boat.meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__drift__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="rough_water", tag="physical", apply=_r_rough_water),
    Rule(name="drift", tag="physical", apply=_r_drift),
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
        for sentence in produced:
            world.say(sentence)
    return produced


def storm_hazard(sign: Sign, craft: Craft) -> bool:
    return sign.severity > 0 and craft.small_craft and craft.exposure > 0


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def weather_severity(sign: Sign, delay: int) -> int:
    return sign.severity + delay


def is_contained(response: Response, sign: Sign, craft: Craft, delay: int) -> bool:
    return response.power >= weather_severity(sign, delay) + max(0, craft.exposure - 1)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_drift(world: World) -> dict:
    sim = world.copy()
    do_untie(sim, narrate=False)
    craft = sim.get("craft")
    harbor = sim.get("harbor")
    return {
        "drifting": craft.meters["drifting"] >= THRESHOLD,
        "danger": craft.meters["danger"],
        "chop": harbor.meters["chop"],
    }


def introduce_town(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"In a small harbor town, {a.id} and {b.id} turned the quay into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"{theme.leader} {a.id} and {theme.mate} {b.id}!" {a.id} shouted. '
        f'"Let\'s hurry to {theme.goal}!"'
    )


def foreshadow(world: World, b: Entity, sign: Sign) -> None:
    weather = world.get("weather")
    weather.meters["storm_risk"] += float(sign.severity)
    b.memes["caution"] += 1
    world.say(sign.omen)
    world.say(sign.line)
    propagate(world, narrate=False)


def tempt(world: World, a: Entity, craft: Craft, theme: Theme) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'At {theme.launch_spot}, {a.id} spotted {craft.phrase} {craft.tied_where}. '
        f'"There! We can take that and reach the music before the next drumbeat."'
    )
    world.say("For one bright second, the shortcut felt like real pirate luck.")


def warn(world: World, b: Entity, a: Entity, craft: Craft, parent: Entity) -> None:
    pred = predict_drift(world)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_chop"] = pred["chop"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.pronoun().capitalize()} knew the harbor had already started to look rough."
    world.say(
        f'{b.id} caught {a.id}\'s sleeve. "No, {a.id}. We are not allowed to untie boats. '
        f'The wind can affect the water fast, and {craft.label} is too small for us."{extra}'
    )
    world.say(
        f'{parent.label_word.capitalize()} had said little boats must stay tied unless a grown-up was with them.'
    )


def defy(world: World, a: Entity, b: Entity, craft: Craft) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        rel = "big brother" if a.type == "boy" else "big sister"
        world.say(
            f'"We will only borrow it for one minute," {a.id} said, and because '
            f'{a.id} was {b.pronoun("possessive")} {rel}, {b.id} could not stop '
            f'{a.pronoun("object")} in time.'
        )
    else:
        world.say(f'"We will only borrow it for one minute," {a.id} said, reaching for the rope.')
    world.say(f"{a.id}'s fingers worked at the knot on the {craft.label}.")


def back_down(world: World, a: Entity, b: Entity, craft: Craft, parent: Entity) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    rel = "brother" if b.type == "boy" else "sister"
    world.say(
        f'{a.id} looked at the dark water, then at {b.id}, {a.pronoun("possessive")} older {rel}, '
        f'and let go of the rope. "All right," {a.pronoun()} muttered. "That does look too rough."'
    )
    world.say(
        f"They left {craft.phrase} tied where it belonged and went to find {parent.label_word} instead."
    )


def do_untie(world: World, narrate: bool = True) -> None:
    craft = world.get("craft")
    craft.meters["untied"] += 1
    propagate(world, narrate=False)
    if narrate:
        world.say(
            f"The rope slipped free. At once the little boat rocked hard, and the harbor water shoved it away from the post."
        )


def launch_accident(world: World, a: Entity, b: Entity, craft: Craft) -> None:
    do_untie(world, narrate=False)
    world.say(
        f"{craft.wobble} The children had barely climbed in when the bow swung out and the boat began to drift."
    )
    world.say(f'"{a.id}!" {b.id} cried. "It is moving!"')


def call_for_help(world: World, parent: Entity) -> None:
    world.say(f'"{parent.label_word.upper()}!"')
    world.say("Their shout skipped across the wet boards and down the whole pier.")


def rescue(world: World, parent: Entity, response: Response, craft: Craft) -> None:
    craft.meters["drifting"] = 0.0
    craft.meters["danger"] = 0.0
    world.get("harbor").meters["chop"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came running and {response.text.replace('{craft}', craft.label)}."
    )
    world.say(
        "The boat bumped safely back against the pier, and the children's knees shook with relief."
    )


def rescue_fail(world: World, parent: Entity, response: Response, craft: Craft) -> None:
    craft.meters["drifting"] += 1
    craft.meters["danger"] += 1
    world.get("harbor").meters["chop"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    world.say(
        f"{parent.label_word.capitalize()} {response.fail.replace('{craft}', craft.label)}."
    )
    world.say(
        "The little boat spun farther out into the harbor before a harbor launch finally thundered over."
    )


def hard_lesson(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
    world.say(
        f"When the launch brought them back, {parent.label_word} hugged them so tightly that neither child tried to speak at first."
    )
    world.say(
        f'"You are safe, and that is what matters," {parent.pronoun()} whispered. '
        f'"But the weather signs were warning us. In this town, a squall can affect the harbor faster than children can think."'
    )
    world.say("After that, they never touched a tied boat without a grown-up again.")


def lesson(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["fear"] = 0.0
    world.say("For a breath, nobody said anything at all.")
    world.say(
        f"Then {parent.label_word} knelt on the pier and gathered both children close. "
        f'"I am glad you called for me," {parent.pronoun()} said softly. '
        f'"Those weather signs were not there for decoration. The wind can affect the harbor very quickly, and little boats are never toys."'
    )
    world.say(f'"We know," whispered {b.id}, and {a.id} nodded too.')


def safe_arrival(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme, safe_way: SafeWay) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"A little later, {parent.label_word} smiled and led them to {safe_way.phrase}. {safe_way.arrival}"
    )
    world.say(
        f'This time, {a.id} raised an arm like a captain and {b.id} laughed beside {a.pronoun("object")}.'
    )
    world.say(
        f"The {theme.crew_plural} reached {theme.goal} the safe way at last, and the harbor town glowed around them like treasure."
    )


def tell(
    theme: Theme,
    sign: Sign,
    craft_cfg: Craft,
    safe_way: SafeWay,
    response: Response,
    *,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    trait: str = "watchful",
    parent_type: str = "mother",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 7,
    pet: str = "",
) -> World:
    world = World()
    a = world.add(
        Entity(
            id=instigator,
            kind="character",
            type=instigator_gender,
            role="instigator",
            traits=["bold"],
            age=instigator_age,
            attrs={"relation": relation},
        )
    )
    b = world.add(
        Entity(
            id=cautioner,
            kind="character",
            type=cautioner_gender,
            role="cautioner",
            traits=[trait],
            age=cautioner_age,
            attrs={"relation": relation},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    weather = world.add(Entity(id="weather", type="weather", label="the weather"))
    harbor = world.add(Entity(id="harbor", type="harbor", label="the harbor"))
    craft = world.add(
        Entity(
            id="craft",
            type="craft",
            label=craft_cfg.label,
            phrase=craft_cfg.phrase,
            small_craft=craft_cfg.small_craft,
            attrs={"owner": craft_cfg.owner},
            tags=set(craft_cfg.tags),
        )
    )

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)
    b.memes["trust"] = float(trust)

    introduce_town(world, a, b, theme)
    foreshadow(world, b, sign)

    world.para()
    tempt(world, a, craft_cfg, theme)
    warn(world, b, a, craft_cfg, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, craft_cfg, parent)
        world.para()
        safe_arrival(world, parent, a, b, theme, safe_way)
        severity = 0
        contained = True
    else:
        defy(world, a, b, craft_cfg)
        world.para()
        launch_accident(world, a, b, craft_cfg)
        call_for_help(world, parent)
        severity = weather_severity(sign, delay) + max(0, craft_cfg.exposure - 1)
        craft.meters["severity"] = float(severity)
        contained = is_contained(response, sign, craft_cfg, delay)
        world.para()
        if contained:
            rescue(world, parent, response, craft_cfg)
            lesson(world, parent, a, b)
            world.para()
            safe_arrival(world, parent, a, b, theme, safe_way)
        else:
            rescue_fail(world, parent, response, craft_cfg)
            hard_lesson(world, parent, a, b)

    outcome = "averted" if averted else ("contained" if contained else "adrift")
    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        theme=theme,
        sign=sign,
        craft_cfg=craft_cfg,
        craft=craft,
        safe_way=safe_way,
        response=response,
        relation=relation,
        ignited=False,
        outcome=outcome,
        rescued=contained,
        severity=severity,
        delay=delay,
        pet=pet,
    )
    return world


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a noisy kingdom of docks and rigging",
        rig="A coil of rope became a sea serpent, a striped crate became a treasure chest, and a chalk line on the boards became their map to the festival pier.",
        leader="Captain",
        mate="First Mate",
        goal="the pirate parade at the far pier",
        launch_spot="the old mooring post",
        crew_word="pirate",
        crew_plural="pirates",
        send_off="marched to the far pier",
    ),
    "raiders": Theme(
        id="raiders",
        scene="a windy coast full of secret coves",
        rig="A fish basket became a chest of silver, a broom became a mast, and the boardwalk rails became the walls of a stolen ship.",
        leader="Captain",
        mate="Lookout",
        goal="the drum circle by the lighthouse pier",
        launch_spot="the worn mooring post",
        crew_word="raider",
        crew_plural="raiders",
        send_off="hurried down the quay",
    ),
    "sailors": Theme(
        id="sailors",
        scene="a bright sea road with gulls overhead",
        rig="A folded blanket became a sail, a bucket became a drum, and the painted line on the dock became the edge of their brave ship.",
        leader="Skipper",
        mate="Mate",
        goal="the brass band in the market square by the pier",
        launch_spot="the harbor post",
        crew_word="sailor",
        crew_plural="sailors",
        send_off="strode to the parade",
    ),
}

SIGNS = {
    "clouds": Sign(
        id="clouds",
        omen="Above the town, the blue sky was slipping behind a line of dark clouds.",
        line='Even the gulls had gone quiet, as if they expected a squall to hurry in soon.',
        severity=2,
        tags={"weather", "foreshadowing", "clouds"},
    ),
    "bell": Sign(
        id="bell",
        omen="From the harbor tower came a low warning bell that rolled over the water.",
        line='The sound made the dock boards feel less like a game and more like a place that needed care.',
        severity=1,
        tags={"weather", "foreshadowing", "bell"},
    ),
    "wind": Sign(
        id="wind",
        omen="A sudden gust chased paper flags straight out over the water.",
        line='The banners snapped so sharply that even the town band stopped tuning for a moment.',
        severity=2,
        tags={"weather", "foreshadowing", "wind"},
    ),
}

CRAFTS = {
    "dinghy": Craft(
        id="dinghy",
        label="dinghy",
        phrase="a little red dinghy",
        tied_where="beside the fish market steps",
        wobble="The dinghy tipped from side to side at once.",
        owner="the baker",
        exposure=1,
        small_craft=True,
        tags={"boat", "dinghy", "harbor"},
    ),
    "skiff": Craft(
        id="skiff",
        label="skiff",
        phrase="a narrow blue skiff",
        tied_where="under the lantern post",
        wobble="The skiff slapped the water and lurched under their shoes.",
        owner="the net-mender",
        exposure=2,
        small_craft=True,
        tags={"boat", "skiff", "harbor"},
    ),
    "rowboat": Craft(
        id="rowboat",
        label="rowboat",
        phrase="a flat-bottomed rowboat",
        tied_where="by the old bait shed",
        wobble="The rowboat bumped and spun as soon as the rope came loose.",
        owner="the florist",
        exposure=1,
        small_craft=True,
        tags={"boat", "rowboat", "harbor"},
    ),
    "ferry": Craft(
        id="ferry",
        label="ferry",
        phrase="the town ferry",
        tied_where="at the ticket dock",
        wobble="The ferry barely moved at all.",
        owner="the harbor captain",
        exposure=0,
        small_craft=False,
        tags={"ferry", "harbor"},
    ),
}

SAFE_WAYS = {
    "ferry_tickets": SafeWay(
        id="ferry_tickets",
        phrase="the ferry with its grown-up captain",
        arrival="With a ticket in each small hand, they crossed the harbor properly while the bell clanged and the gulls wheeled overhead.",
        tags={"ferry", "safe_travel"},
    ),
    "footbridge": SafeWay(
        id="footbridge",
        phrase="the painted footbridge over the inlet",
        arrival="They walked above the water instead of on it, and from the middle they could see all the little boats dancing safely below.",
        tags={"bridge", "safe_travel"},
    ),
    "harbor_cart": SafeWay(
        id="harbor_cart",
        phrase="the harbor cart that rattled around the quay",
        arrival="They rode beside stacked nets and bright buoys until the far pier opened in front of them.",
        tags={"cart", "safe_travel"},
    ),
}

RESPONSES = {
    "throw_line": Response(
        id="throw_line",
        sense=3,
        power=3,
        text="snatched up the rescue line from the post and cast it neatly across the bow of the {craft}",
        fail="threw the rescue line toward the {craft}, but the little boat had already spun beyond easy reach",
        qa_text="threw a rescue line and pulled the boat back to the pier",
        tags={"rope", "rescue"},
    ),
    "boat_hook": Response(
        id="boat_hook",
        sense=3,
        power=2,
        text="grabbed the long boat hook and caught the side of the {craft} before it could drift far",
        fail="lunged with the boat hook, but the {craft} slipped farther out between the pilings",
        qa_text="used a boat hook to snag the boat and guide it back",
        tags={"hook", "rescue"},
    ),
    "jump_in": Response(
        id="jump_in",
        sense=1,
        power=1,
        text="splashed straight into the harbor and shoved the {craft} back by hand",
        fail="jumped into the water after the {craft}, but the chop and cold only slowed everything down",
        qa_text="jumped into the harbor and pushed the boat back",
        tags={"water", "rescue"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "watchful", "curious", "cautious", "thoughtful", "sensible"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme_id in THEMES:
        for sign_id, sign in SIGNS.items():
            for craft_id, craft in CRAFTS.items():
                if storm_hazard(sign, craft):
                    combos.append((theme_id, sign_id, craft_id))
    return combos


@dataclass
class StoryParams:
    theme: str
    sign: str
    craft: str
    safe_way: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    trust: int = 7
    pet: str = ""
    seed: Optional[int] = None


KNOWLEDGE = {
    "weather": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is when a story shows little clues early, like dark clouds or a warning bell, so you can feel that something important may happen soon."
        ),
        (
            "Why can dark clouds and sudden wind matter at a harbor?",
            "They can be signs that rough weather is coming. Rough weather can affect small boats very quickly."
        ),
    ],
    "boat": [
        (
            "Why should children not untie a small boat by themselves?",
            "A small boat can drift away or tip if nobody skilled is guiding it. Water can become dangerous very fast."
        ),
    ],
    "dinghy": [
        (
            "What is a dinghy?",
            "A dinghy is a very small boat. It is useful with a grown-up, but it is not for children to untie and use alone."
        ),
    ],
    "skiff": [
        (
            "What is a skiff?",
            "A skiff is a light little boat that can move quickly on the water. Because it is small, wind and chop can push it around."
        ),
    ],
    "rowboat": [
        (
            "What is a rowboat?",
            "A rowboat is a small boat moved with oars. It still needs a grown-up or a careful boater to handle it safely."
        ),
    ],
    "rope": [
        (
            "What does a rescue line do?",
            "A rescue line is a rope used to reach or pull something back safely. It lets a grown-up help without jumping into danger first."
        ),
    ],
    "hook": [
        (
            "What is a boat hook?",
            "A boat hook is a long pole with a hook on the end. Grown-ups can use it to pull a boat close to the pier."
        ),
    ],
    "ferry": [
        (
            "What is a ferry?",
            "A ferry is a bigger boat that carries people across the water on purpose. It has a grown-up captain and follows safe rules."
        ),
    ],
    "bridge": [
        (
            "Why is a bridge safer than a loose little boat?",
            "A bridge stays still while you walk across it. A loose little boat can rock, drift, or turn when the water changes."
        ),
    ],
    "cart": [
        (
            "What is a harbor cart?",
            "A harbor cart is a wheeled cart used to move things around the docks. Riding in a cart with a grown-up keeps you off the risky water."
        ),
    ],
}
KNOWLEDGE_ORDER = ["weather", "boat", "dinghy", "skiff", "rowboat", "rope", "hook", "ferry", "bridge", "cart"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    sign = f["sign"]
    craft = f["craft_cfg"]
    theme = f["theme"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a gentle pirate-style story for a 3-to-5-year-old set in a harbor town. Use foreshadowing with {sign.id} and include the word "affect".',
            f"Tell a story where {a.id} wants to untie {craft.phrase}, but {b.id} notices the weather clues first and stops the mistake before the danger begins.",
            f"Write a story about children playing {theme.crew_plural} who learn that weather can affect the harbor quickly, so they choose a safe way across town instead.",
        ]
    if outcome == "adrift":
        return [
            f'Write a cautionary pirate-style story set in a harbor town that uses foreshadowing before a child unties {craft.phrase}. Include the word "affect".',
            f"Tell a story where {a.id} ignores the warning signs, the little boat drifts out, and the lesson comes from a frightening rescue.",
            f"Write a story with an uneasy ending where weather clues matter, because the children treat a real harbor like a pretend pirate game.",
        ]
    return [
        f'Write a short pirate-style story for a 3-to-5-year-old set in a harbor town. Use foreshadowing and include the word "affect".',
        f"Tell a story where {a.id} and {b.id} are playing {theme.crew_plural}, a small boat starts to drift, and a calm grown-up rescues them.",
        f"Write a simple story where weather signs matter before the problem happens, and the ending shows the children reaching the festival safely another way.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    theme = f["theme"]
    sign = f["sign"]
    craft = f["craft_cfg"]
    safe_way = f["safe_way"]
    response = f["response"]
    pair = pair_noun(a, b, f["relation"])
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, who were pretending to be {theme.crew_plural} in their harbor town. It also includes {pw}, who helped when the game brushed against real danger."
        ),
        (
            "What was the foreshadowing at the beginning?",
            f"The story first showed {sign.omen.lower()} {sign.line} Those clues warned that the weather was changing before the children touched the boat."
        ),
        (
            f"Why did {b.id} tell {a.id} not to untie the boat?",
            f"{b.id} had noticed the weather signs and knew the wind could affect the harbor quickly. {b.pronoun().capitalize()} also knew {craft.label} was too small for children to borrow alone."
        ),
    ]
    if f["outcome"] == "averted":
        qa.extend(
            [
                (
                    f"What did {a.id} do after the warning?",
                    f"{a.id} let go of the rope and backed down, so the boat stayed tied where it belonged. The danger never started because the warning worked in time."
                ),
                (
                    "How did the story end?",
                    f"It ended safely, with the children using {safe_way.phrase} instead. They still reached {theme.goal}, but now the ending proved they had learned the safer way."
                ),
            ]
        )
    elif f["outcome"] == "contained":
        qa.extend(
            [
                (
                    "What happened when the rope came loose?",
                    f"The little boat rocked, swung away from the post, and began to drift. That happened because the rough water and the untied rope worked together at once."
                ),
                (
                    f"How did {pw} help?",
                    f"{pw.capitalize()} {response.qa_text.replace('{craft}', craft.label)}. The quick help stopped the drifting before the little boat went farther into the harbor."
                ),
                (
                    "What did the children learn?",
                    f"They learned that weather clues matter and that a real harbor is not the same as a pretend pirate game. They also learned that wind can affect the water faster than they expected."
                ),
            ]
        )
    else:
        qa.extend(
            [
                (
                    "Was it an easy rescue?",
                    f"No. The first try did not work, and the little boat spun farther out before the harbor launch brought them back. That is what made the lesson feel so serious."
                ),
                (
                    "How did the story end?",
                    f"It ended with the children safe again, but shaken and quiet after the frightening ride. The ending proves they changed, because they never touched a tied boat without a grown-up after that."
                ),
            ]
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["sign"].tags) | set(f["craft_cfg"].tags) | set(f["safe_way"].tags)
    if f["outcome"] != "averted":
        tags |= set(f["response"].tags)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.small_craft:
            bits.append("small_craft=True")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="pirates",
        sign="clouds",
        craft="dinghy",
        safe_way="ferry_tickets",
        response="throw_line",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=8,
        pet="the puppy",
    ),
    StoryParams(
        theme="raiders",
        sign="bell",
        craft="skiff",
        safe_way="footbridge",
        response="boat_hook",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Mia",
        cautioner_gender="girl",
        parent="father",
        trait="thoughtful",
        delay=0,
        instigator_age=5,
        cautioner_age=5,
        relation="friends",
        trust=4,
        pet="",
    ),
    StoryParams(
        theme="pirates",
        sign="wind",
        craft="rowboat",
        safe_way="harbor_cart",
        response="boat_hook",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Tom",
        cautioner_gender="boy",
        parent="father",
        trait="watchful",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=3,
        pet="their little dog",
    ),
    StoryParams(
        theme="sailors",
        sign="clouds",
        craft="skiff",
        safe_way="footbridge",
        response="boat_hook",
        instigator="Eli",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        parent="mother",
        trait="cautious",
        delay=2,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        trust=2,
        pet="the cat",
    ),
]


def explain_rejection(sign: Sign, craft: Craft) -> str:
    if not craft.small_craft:
        return (
            f"(No story: {craft.phrase} is not the kind of loose little boat this world is about. "
            f"The danger needs a small craft that children might foolishly untie, not {craft.label}.)"
        )
    if craft.exposure <= 0:
        return (
            f"(No story: {craft.label} is too sheltered for the storm setup to matter here. "
            f"Pick a small boat that rough water can push around.)"
        )
    if sign.severity <= 0:
        return "(No story: without warning signs, the foreshadowing beat disappears.)"
    return "(No story: this combination does not make a plausible drifting-boat problem.)"


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], SIGNS[params.sign], CRAFTS[params.craft], params.delay) else "adrift"


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = " / ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try a safer rescue such as {better}.)"
    )


ASP_RULES = r"""
hazard(S, C) :- sign(S), craft(C), sign_severity(S, V), V > 0, small_craft(C), exposure(C, E), E > 0.
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(T, S, C) :- theme(T), hazard(S, C).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

storm_value(V + D + X) :- chosen_sign(S), sign_severity(S, V), delay(D), chosen_craft(C), exposure(C, E), X = E - 1, E > 0.
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), storm_value(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(adrift) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for sign_id, sign in SIGNS.items():
        lines.append(asp.fact("sign", sign_id))
        lines.append(asp.fact("sign_severity", sign_id, sign.severity))
    for craft_id, craft in CRAFTS.items():
        lines.append(asp.fact("craft", craft_id))
        lines.append(asp.fact("exposure", craft_id, craft.exposure))
        if craft.small_craft:
            lines.append(asp.fact("small_craft", craft_id))
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

    scenario = "\n".join(
        [
            asp.fact("chosen_sign", params.sign),
            asp.fact("chosen_craft", params.craft),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_responses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(seed)))
        except StoryError:
            continue
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated smoke-test story was empty.")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a harbor-town pirate game, weather foreshadowing, and a drifting boat."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--craft", choices=CRAFTS)
    ap.add_argument("--safe-way", choices=SAFE_WAYS, dest="safe_way")
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="head start before help reaches the drifting boat")
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


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [name for name in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if name != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.craft:
        craft = CRAFTS[args.craft]
        sign = SIGNS[args.sign] if args.sign else next(iter(SIGNS.values()))
        if not storm_hazard(sign, craft):
            raise StoryError(explain_rejection(sign, craft))
    if args.sign and args.craft:
        sign = SIGNS[args.sign]
        craft = CRAFTS[args.craft]
        if not storm_hazard(sign, craft):
            raise StoryError(explain_rejection(sign, craft))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.sign is None or combo[1] == args.sign)
        and (args.craft is None or combo[2] == args.craft)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, sign, craft = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    safe_way = args.safe_way or rng.choice(sorted(SAFE_WAYS))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    pet = rng.choice(["the cat", "the puppy", "their little dog", "", ""])
    return StoryParams(
        theme=theme,
        sign=sign,
        craft=craft,
        safe_way=safe_way,
        response=response,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        sign = SIGNS[params.sign]
        craft = CRAFTS[params.craft]
        safe_way = SAFE_WAYS[params.safe_way]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err.args[0]})") from err

    if not storm_hazard(sign, craft):
        raise StoryError(explain_rejection(sign, craft))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        theme=theme,
        sign=sign,
        craft_cfg=craft,
        safe_way=safe_way,
        response=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        parent_type=params.parent,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        trust=params.trust,
        pet=params.pet,
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
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, sign, craft) combos:\n")
        for theme, sign, craft in combos:
            print(f"  {theme:9} {sign:8} {craft}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.sign} with {p.craft} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
