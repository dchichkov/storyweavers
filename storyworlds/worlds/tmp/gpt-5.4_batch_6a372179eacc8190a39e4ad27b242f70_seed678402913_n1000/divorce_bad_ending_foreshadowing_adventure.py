#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/divorce_bad_ending_foreshadowing_adventure.py
=========================================================================

A standalone story world about two children who turn grief into an adventure.
They overhear that their parents are getting a divorce, decide to chase a
storybook fix, ignore foreshadowed danger, and learn the hard way that an
adventure cannot solve a grown-up problem.

The world prefers a tight, plausible domain over broad coverage:

- Two children hear the word "divorce" and feel frightened and hopeful.
- They believe a local landmark might help if they reach it before dark.
- The route, weather, pack, and light determine whether the trip becomes merely
  miserable or dangerous enough to need a rescue.
- Every ending is bad in the seed's sense: the quest does not stop the divorce.
  Some endings are worse than others.

Run it
------
    python storyworlds/worlds/gpt-5.4/divorce_bad_ending_foreshadowing_adventure.py
    python storyworlds/worlds/gpt-5.4/divorce_bad_ending_foreshadowing_adventure.py --destination ridge --weather storm
    python storyworlds/worlds/gpt-5.4/divorce_bad_ending_foreshadowing_adventure.py --pack picnic_basket
    python storyworlds/worlds/gpt-5.4/divorce_bad_ending_foreshadowing_adventure.py --all
    python storyworlds/worlds/gpt-5.4/divorce_bad_ending_foreshadowing_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4/divorce_bad_ending_foreshadowing_adventure.py --verify
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
PREP_MIN = 2


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
        female = {"girl", "mother", "mom", "woman", "aunt", "sister"}
        male = {"boy", "father", "dad", "man", "uncle", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Destination:
    id: str
    label: str
    phrase: str
    approach: str
    omen: str
    hideout: str
    promise: str
    terrain: str
    distance: int
    night_risk: int
    danger_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Weather:
    id: str
    sky: str
    warning: str
    severity: int
    wet: int
    cold: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Pack:
    id: str
    label: str
    phrase: str
    safety: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Light:
    id: str
    label: str
    phrase: str
    power: int
    glow: str
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
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "follower"}]

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
        new.paragraphs = [[]]
        new.fired = set(self.fired)
        new.facts = copy.deepcopy(self.facts)
        return new


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def danger_score(destination: Destination, weather: Weather, delay: int) -> int:
    return destination.distance + destination.night_risk + weather.severity + delay


def prep_score(pack: Pack, light: Light) -> int:
    return pack.safety + light.power


def is_prepared(destination: Destination, pack: Pack) -> bool:
    return destination.terrain in pack.tags


def outcome_of_params(params: "StoryParams") -> str:
    destination = DESTINATIONS[params.destination]
    weather = WEATHER[params.weather]
    pack = PACKS[params.pack]
    light = LIGHTS[params.light]
    if danger_score(destination, weather, params.delay) > prep_score(pack, light):
        return "rescued"
    return "soggy_return"


def _r_wet_and_cold(world: World) -> list[str]:
    out: list[str] = []
    weather = world.facts["weather"]
    pack = world.facts["pack"]
    if weather.wet <= 0 or "rain_shell" in pack.tags:
        return out
    for kid in world.kids():
        sig = ("wet", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.meters["wet"] += 1
        kid.meters["cold"] += weather.cold
        out.append("__wet__")
    return out


def _r_darkness(world: World) -> list[str]:
    out: list[str] = []
    destination = world.facts["destination"]
    light = world.facts["light"]
    delay = world.facts["delay"]
    if destination.night_risk + delay < 2:
        return out
    if light.power >= 2:
        return out
    for kid in world.kids():
        sig = ("dark", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.meters["lost"] += 1
        kid.memes["fear"] += 1
        out.append("__dark__")
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.kids():
        if kid.meters["wet"] + kid.meters["cold"] + kid.meters["lost"] < THRESHOLD:
            continue
        sig = ("fear", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["fear"] += 1
        out.append("__fear__")
    return out


CAUSAL_RULES = [
    Rule(name="wet_and_cold", tag="physical", apply=_r_wet_and_cold),
    Rule(name="darkness", tag="physical", apply=_r_darkness),
    Rule(name="fear", tag="emotional", apply=_r_fear),
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


def explain_rejection(destination: Destination, pack: Pack) -> str:
    return (
        f"(No story: {destination.phrase} is a {destination.terrain} trip, but "
        f"{pack.phrase} is not sensible gear for that ground. Pick a pack that can handle "
        f"{destination.terrain} paths.)"
    )


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    press_on(sim, narrate=False)
    kids = sim.kids()
    return {
        "wet": any(k.meters["wet"] >= THRESHOLD for k in kids),
        "lost": any(k.meters["lost"] >= THRESHOLD for k in kids),
        "fear": sum(k.memes["fear"] for k in kids),
    }


def setup_home(world: World, leader: Entity, follower: Entity, parent: Entity) -> None:
    world.say(
        f"{leader.id} and {follower.id} had spent all week pretending the back yard was a wild country "
        f"full of trails, maps, and hidden places."
    )
    world.say(
        f"They called themselves the Lantern Club, and on that afternoon {leader.id} had drawn a brave red line "
        f"across an old paper map."
    )
    world.say(
        f"Then voices drifted from the kitchen. They heard {parent.label_word} say the word divorce, "
        f"and the whole house felt different."
    )


def hurt_and_hope(world: World, leader: Entity, follower: Entity, destination: Destination) -> None:
    leader.memes["hope"] += 1
    leader.memes["resolve"] += 1
    follower.memes["fear"] += 1
    world.say(
        f"{follower.id} went still. \"Does divorce mean our family breaks in two?\" "
        f"{follower.pronoun()} whispered."
    )
    world.say(
        f"{leader.id} pointed at the map. \"In adventure books, there is always one place left to try,\" "
        f"{leader.pronoun()} said. \"If we reach {destination.phrase}, maybe {destination.promise}.\""
    )


def foreshadow(world: World, destination: Destination, weather: Weather, parent: Entity, light: Light) -> None:
    world.say(
        f"Outside, {weather.sky}. {weather.warning}"
    )
    world.say(
        f"The way to {destination.label} began with {destination.approach}, and even before they stepped off, "
        f"{destination.omen}"
    )
    world.say(
        f"{parent.label_word.capitalize()} called from the porch, \"Stay close and be back before dark.\" "
        f"But the warning only made the map feel more secret."
    )
    world.say(
        f"{light.phrase.capitalize()} waited in the clubhouse box, {light.glow}."
    )


def choose_and_leave(world: World, leader: Entity, follower: Entity, pack: Pack) -> None:
    for kid in (leader, follower):
        kid.memes["resolve"] += 1
    world.say(
        f"{leader.id} grabbed {pack.phrase}, tucked the map under {leader.pronoun('possessive')} arm, "
        f"and led the way through the gate."
    )
    world.say(
        f"{follower.id} hurried after {leader.pronoun('object')}, because staying behind felt even scarier "
        f"than the trail."
    )


def warning_beat(world: World, follower: Entity) -> None:
    pred = predict_trouble(world)
    world.facts["predicted"] = pred
    if pred["lost"]:
        world.say(
            f'{follower.id} looked at the dim path and said, "If the light goes bad, we could lose the trail."'
        )
    elif pred["wet"]:
        world.say(
            f'{follower.id} looked up at the sky and said, "If the rain starts, we will be soaked before we get home."'
        )
    else:
        world.say(
            f'{follower.id} still felt a pinch in {follower.pronoun("possessive")} chest, but the path only looked hard, not impossible.'
        )


def press_on(world: World, narrate: bool = True) -> None:
    destination = world.facts["destination"]
    weather = world.facts["weather"]
    leader = world.facts["leader"]
    follower = world.facts["follower"]

    if narrate:
        world.say(
            f"They hurried on toward {destination.phrase}. The map line looked simple on paper, but the real ground kept tilting "
            f"and tugging at their shoes."
        )
        world.say(destination.danger_line)
        if weather.wet:
            world.say("The first drops came before they were halfway there.")
    for kid in (leader, follower):
        kid.meters["distance"] += destination.distance
    propagate(world, narrate=narrate)


def reach_or_fail(world: World, destination: Destination, weather: Weather) -> None:
    outcome = world.facts["outcome"]
    leader = world.facts["leader"]
    follower = world.facts["follower"]
    if outcome == "soggy_return":
        leader.memes["hope"] = 0.0
        follower.memes["hope"] = 0.0
        leader.memes["sadness"] += 1
        follower.memes["sadness"] += 1
        world.say(
            f"They did reach {destination.label}, but it was only {destination.hideout}, quiet and ordinary."
        )
        world.say(
            f"No lantern sign appeared. No magic answer rose from the stones. The wind only pushed the wet leaves around their ankles."
        )
        world.say(
            f"By the time they slogged back home, the adventure had turned heavy. They were muddy, tired, and full of the hard truth "
            f"that a trail could not mend a divorce."
        )
    else:
        leader.memes["fear"] += 1
        follower.memes["fear"] += 1
        leader.memes["sadness"] += 1
        follower.memes["sadness"] += 1
        world.say(
            f"They never reached {destination.label}. {weather.warning.split('.')[0].rstrip(',')} turned real around them, and soon "
            f"the map was soft, the trail was gone, and every tree looked like the next one."
        )
        world.say(
            f"{follower.id} began to cry, and even {leader.id} could not pretend the quest was brave anymore."
        )


def rescue_or_arrive_home(world: World, parent: Entity) -> None:
    outcome = world.facts["outcome"]
    leader = world.facts["leader"]
    follower = world.facts["follower"]
    if outcome == "rescued":
        for kid in (leader, follower):
            kid.memes["relief"] += 1
        world.say(
            f"At last they heard {parent.label_word}'s voice and the beam of a grown-up flashlight swept across the brush."
        )
        world.say(
            f"{parent.label_word.capitalize()} wrapped them in a coat and marched them home through the dark. Nobody scolded at first, "
            f"because the shaking in their hands said enough."
        )
    else:
        world.say(
            f"{parent.label_word.capitalize()} found them dripping at the back step and pulled them inside with a blanket already open."
        )


def final_truth(world: World, parent: Entity) -> None:
    leader = world.facts["leader"]
    follower = world.facts["follower"]
    world.say(
        f"Later, with dry socks and soup growing cold in their bowls, {parent.label_word} told them softly that the divorce was still real."
    )
    world.say(
        f'"I love you in one home or two," {parent.pronoun()} said, "but no child has to go on a quest to fix it."'
    )
    world.say(
        f"{leader.id} looked at the ruined map. {follower.id} tucked it into a drawer instead of onto the adventure wall."
    )
    world.say(
        "The club lantern stayed unlit that night, and the house felt smaller than it had that morning."
    )


def tell(
    destination: Destination,
    weather: Weather,
    pack: Pack,
    light: Light,
    leader_name: str = "Nora",
    leader_gender: str = "girl",
    follower_name: str = "Ben",
    follower_gender: str = "boy",
    parent_type: str = "mother",
    delay: int = 0,
) -> World:
    world = World()
    leader = world.add(Entity(id=leader_name, kind="character", type=leader_gender, role="leader"))
    follower = world.add(Entity(id=follower_name, kind="character", type=follower_gender, role="follower"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="pack", type="pack", label=pack.label, phrase=pack.phrase, tags=set(pack.tags)))
    world.add(Entity(id="light", type="light", label=light.label, phrase=light.phrase))
    world.add(Entity(id="destination", type="place", label=destination.label, phrase=destination.phrase))
    world.facts.update(
        destination=destination,
        weather=weather,
        pack=pack,
        light=light,
        leader=leader,
        follower=follower,
        parent=parent,
        delay=delay,
        outcome="",
    )

    setup_home(world, leader, follower, parent)
    hurt_and_hope(world, leader, follower, destination)

    world.para()
    foreshadow(world, destination, weather, parent, light)
    choose_and_leave(world, leader, follower, pack)
    warning_beat(world, follower)

    world.para()
    press_on(world, narrate=True)
    world.facts["outcome"] = "rescued" if danger_score(destination, weather, delay) > prep_score(pack, light) else "soggy_return"
    reach_or_fail(world, destination, weather)

    world.para()
    rescue_or_arrive_home(world, parent)
    final_truth(world, parent)

    world.facts["wet"] = any(k.meters["wet"] >= THRESHOLD for k in world.kids())
    world.facts["lost"] = any(k.meters["lost"] >= THRESHOLD for k in world.kids())
    world.facts["danger"] = danger_score(destination, weather, delay)
    world.facts["prep"] = prep_score(pack, light)
    return world


DESTINATIONS = {
    "ridge": Destination(
        id="ridge",
        label="Whisper Ridge",
        phrase="Whisper Ridge",
        approach="a long field path and a sagging fence gate",
        omen="the gate gave a tired squeal, as if it wanted them to turn back",
        hideout="a windy strip of stones above the blackberry bushes",
        promise="the hill will give us one answer",
        terrain="hillside",
        distance=2,
        night_risk=1,
        danger_line="The red line on the map kept crossing patches of slippery grass.",
        tags={"hill", "outdoors"},
    ),
    "bridge": Destination(
        id="bridge",
        label="Moss Bridge",
        phrase="Moss Bridge",
        approach="the creek path under willow branches",
        omen="the boards of the old bridge clicked against one another in the wind",
        hideout="an old footbridge green with moss above brown water",
        promise="the bridge will carry our wish across",
        terrain="creek",
        distance=2,
        night_risk=1,
        danger_line="The creek sounded louder than it had from the yard, and the bank kept crumbling under their shoes.",
        tags={"water", "outdoors"},
    ),
    "pines": Destination(
        id="pines",
        label="The Lantern Pines",
        phrase="the Lantern Pines",
        approach="the narrow deer trail behind the sheds",
        omen="the trees stood so close together that the path looked swallowed even before sunset",
        hideout="a ring of dark pines with a stump in the middle",
        promise="the pines will show us the right sign",
        terrain="woods",
        distance=3,
        night_risk=2,
        danger_line="The farther they went, the more the branches rubbed together with a dry, whispering sound.",
        tags={"woods", "outdoors"},
    ),
}

WEATHER = {
    "windy": Weather(
        id="windy",
        sky="the clouds dragged low and the wind kept tugging at the map",
        warning="The gusts bent the tall grass one way and then another.",
        severity=1,
        wet=0,
        cold=0,
        tags={"wind"},
    ),
    "drizzle": Weather(
        id="drizzle",
        sky="a gray drizzle had already begun to dot the stepping stones",
        warning="The air smelled like rain that meant to stay.",
        severity=1,
        wet=1,
        cold=1,
        tags={"rain"},
    ),
    "storm": Weather(
        id="storm",
        sky="dark clouds were bunching over the roofs and the light looked too early for evening",
        warning="Far off, thunder rolled once, then waited.",
        severity=2,
        wet=1,
        cold=1,
        tags={"storm", "rain"},
    ),
}

PACKS = {
    "trail_bag": Pack(
        id="trail_bag",
        label="trail bag",
        phrase="the trail bag with string, biscuits, and a folded rain shell",
        safety=2,
        tags={"woods", "creek", "hillside", "rain_shell"},
    ),
    "rope_satchel": Pack(
        id="rope_satchel",
        label="rope satchel",
        phrase="the rope satchel with chalk, a snack, and a coil of line",
        safety=1,
        tags={"creek", "hillside"},
    ),
    "picnic_basket": Pack(
        id="picnic_basket",
        label="picnic basket",
        phrase="the picnic basket with crackers and jam tucked inside",
        safety=0,
        tags={"hillside"},
    ),
}

LIGHTS = {
    "club_lantern": Light(
        id="club_lantern",
        label="club lantern",
        phrase="the club lantern",
        power=2,
        glow="with a steady yellow window",
        tags={"lantern"},
    ),
    "pocket_torch": Light(
        id="pocket_torch",
        label="pocket torch",
        phrase="the pocket torch",
        power=1,
        glow="with a thin white eye",
        tags={"flashlight"},
    ),
    "glow_stick": Light(
        id="glow_stick",
        label="glow stick",
        phrase="the glow stick",
        power=0,
        glow="with a weak green stripe",
        tags={"glow"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Ella", "Zoe", "Ruby", "Clara"]
BOY_NAMES = ["Ben", "Sam", "Leo", "Max", "Noah", "Finn", "Eli", "Theo"]


@dataclass
class StoryParams:
    destination: str
    weather: str
    pack: str
    light: str
    leader: str
    leader_gender: str
    follower: str
    follower_gender: str
    parent: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        destination="ridge",
        weather="drizzle",
        pack="picnic_basket",
        light="glow_stick",
        leader="Nora",
        leader_gender="girl",
        follower="Ben",
        follower_gender="boy",
        parent="mother",
        delay=1,
    ),
    StoryParams(
        destination="bridge",
        weather="storm",
        pack="rope_satchel",
        light="pocket_torch",
        leader="Sam",
        leader_gender="boy",
        follower="Lily",
        follower_gender="girl",
        parent="father",
        delay=1,
    ),
    StoryParams(
        destination="pines",
        weather="storm",
        pack="trail_bag",
        light="pocket_torch",
        leader="Ava",
        leader_gender="girl",
        follower="Leo",
        follower_gender="boy",
        parent="mother",
        delay=1,
    ),
    StoryParams(
        destination="bridge",
        weather="windy",
        pack="trail_bag",
        light="club_lantern",
        leader="Max",
        leader_gender="boy",
        follower="Ruby",
        follower_gender="girl",
        parent="father",
        delay=0,
    ),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for dest_id, destination in DESTINATIONS.items():
        for weather_id in WEATHER:
            for pack_id, pack in PACKS.items():
                if not is_prepared(destination, pack):
                    continue
                for light_id in LIGHTS:
                    combos.append((dest_id, weather_id, pack_id, light_id))
    return combos


KNOWLEDGE = {
    "divorce": [(
        "What is a divorce?",
        "A divorce is when two married grown-ups decide not to stay married anymore. A child did not cause it, and it is not a child's job to fix it."
    )],
    "storm": [(
        "Why is a storm a warning sign on a trip?",
        "Storms can make paths slippery, dark, and hard to follow. That means small problems can turn big very quickly."
    )],
    "map": [(
        "Can a map fix a family problem?",
        "No. A map can help people find a place, but it cannot solve a grown-up problem like a divorce. Children need care and honest talk, not a dangerous quest."
    )],
    "lantern": [(
        "Why does a lantern help on an evening walk?",
        "A lantern gives steady light so you can see the ground and the path. Good light makes it easier not to get lost."
    )],
    "rain": [(
        "Why is getting wet outside risky when it is cold?",
        "Wet clothes pull warmth away from your body. That can make you cold, shaky, and tired."
    )],
    "creek": [(
        "Why should children stay careful near a creek?",
        "Creek banks can be slippery and soft. A child can lose footing there much faster than expected."
    )],
    "woods": [(
        "Why can woods feel confusing after dark?",
        "Trees and shadows can make one part of the trail look like another. Without enough light, it is easy to lose the path."
    )],
}
KNOWLEDGE_ORDER = ["divorce", "storm", "map", "lantern", "rain", "creek", "woods"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    follower = f["follower"]
    destination = f["destination"]
    outcome = f["outcome"]
    base = (
        f'Write an adventure story for ages 5 to 7 that includes the word "divorce", '
        f"uses strong foreshadowing, and ends badly."
    )
    if outcome == "rescued":
        return [
            base,
            f"Tell a sad adventure where {leader.id} and {follower.id} sneak out to reach {destination.label} because they hope a quest can stop their parents' divorce, but the warnings come true and they need a rescue.",
            f"Write a foreshadowed quest story in which children mistake a grown-up problem for an adventure problem, and the ending shows they were cold, frightened, and wrong.",
        ]
    return [
        base,
        f"Tell an adventure where {leader.id} and {follower.id} reach {destination.label} hoping to fix a divorce, but discover there is no magic answer and come home sad.",
        "Write a story with warning signs, a brave-sounding plan, and a final scene where the children understand that some hurts cannot be solved by a quest.",
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    return "a brother and a sister"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    follower = f["follower"]
    parent = f["parent"]
    destination = f["destination"]
    weather = f["weather"]
    pack = f["pack"]
    light = f["light"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(leader, follower)}, {leader.id} and {follower.id}. They turn their fear into an adventure after hearing about a divorce at home."
        ),
        (
            "Why did the children start the quest?",
            f"They heard the grown-ups say the word divorce and felt scared. So they imagined that reaching {destination.label} might give them a way to fix the family."
        ),
        (
            "What signs warned them that the trip was a bad idea?",
            f"The sky already looked wrong, and the trail itself gave warnings before they even began. {weather.warning} {destination.omen[0].upper()}{destination.omen[1:]}"
        ),
        (
            f"What did they carry with them?",
            f"They took {pack.phrase} and {light.phrase}. Those things mattered because the trip became harder and darker than they expected."
        ),
    ]
    if outcome == "rescued":
        qa.append((
            "Why did the quest end badly?",
            f"It ended badly because the danger of the trail and weather was bigger than what they had packed for. They became cold, frightened, and lost enough that {parent.label_word} had to come find them."
        ))
        qa.append((
            "Did the adventure stop the divorce?",
            "No. The quest only made the children more scared and tired. At home, the grown-up still had to explain that the divorce was real and not something children could fix."
        ))
    else:
        qa.append((
            f"What happened when they reached {destination.label}?",
            f"They found only {destination.hideout}, not a magic answer. That is when the adventure feeling broke and they understood the place could not heal a divorce."
        ))
        qa.append((
            "Why is the ending still bad even though nobody had to rescue them?",
            "It is still bad because the children came home wet and disappointed, and the family problem remained. The trip took away their hopeful fantasy without solving anything."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"divorce", "map"}
    if "storm" in f["weather"].tags:
        tags.add("storm")
    if "rain" in f["weather"].tags:
        tags.add("rain")
    if "lantern" in f["light"].tags:
        tags.add("lantern")
    if f["destination"].terrain == "creek":
        tags.add("creek")
    if f["destination"].terrain == "woods":
        tags.add("woods")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  outcome: {world.facts.get('outcome')}")
    return "\n".join(lines)


ASP_RULES = r"""
prepared(D, P) :- destination(D), pack(P), needs(D, T), has(P, T).
valid(D, W, P, L) :- destination(D), weather(W), pack(P), light(L), prepared(D, P).

danger_value(V) :- chosen_destination(D), dist(D, A), night(D, B),
                   chosen_weather(W), severity(W, C), delay(Dly), V = A + B + C + Dly.
prep_value(V)   :- chosen_pack(P), safety(P, A), chosen_light(L), power(L, B), V = A + B.

outcome(rescued)      :- danger_value(D), prep_value(P), D > P.
outcome(soggy_return) :- danger_value(D), prep_value(P), D <= P.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for dest_id, destination in DESTINATIONS.items():
        lines.append(asp.fact("destination", dest_id))
        lines.append(asp.fact("needs", dest_id, destination.terrain))
        lines.append(asp.fact("dist", dest_id, destination.distance))
        lines.append(asp.fact("night", dest_id, destination.night_risk))
    for weather_id, weather in WEATHER.items():
        lines.append(asp.fact("weather", weather_id))
        lines.append(asp.fact("severity", weather_id, weather.severity))
    for pack_id, pack in PACKS.items():
        lines.append(asp.fact("pack", pack_id))
        lines.append(asp.fact("safety", pack_id, pack.safety))
        for tag in sorted(pack.tags):
            if tag in {"woods", "creek", "hillside"}:
                lines.append(asp.fact("has", pack_id, tag))
    for light_id, light in LIGHTS.items():
        lines.append(asp.fact("light", light_id))
        lines.append(asp.fact("power", light_id, light.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_destination", params.destination),
        asp.fact("chosen_weather", params.weather),
        asp.fact("chosen_pack", params.pack),
        asp.fact("chosen_light", params.light),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
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

    cases = list(CURATED)
    for s in range(50):
        rng = random.Random(s)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    mismatches = 0
    for params in cases:
        py = outcome_of_params(params)
        asp_out = asp_outcome(params)
        if py != asp_out:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: children turn fear about a divorce into a dangerous quest. "
        "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--destination", choices=DESTINATIONS)
    ap.add_argument("--weather", choices=WEATHER)
    ap.add_argument("--pack", choices=PACKS)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how late they leave")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.destination and args.pack:
        destination = DESTINATIONS[args.destination]
        pack = PACKS[args.pack]
        if not is_prepared(destination, pack):
            raise StoryError(explain_rejection(destination, pack))

    combos = [
        combo for combo in valid_combos()
        if (args.destination is None or combo[0] == args.destination)
        and (args.weather is None or combo[1] == args.weather)
        and (args.pack is None or combo[2] == args.pack)
        and (args.light is None or combo[3] == args.light)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    destination, weather, pack, light = rng.choice(sorted(combos))
    leader_gender = rng.choice(["girl", "boy"])
    follower_gender = "boy" if leader_gender == "girl" else "girl" if rng.random() < 0.6 else leader_gender
    leader = _pick_name(rng, leader_gender)
    follower = _pick_name(rng, follower_gender, avoid=leader)
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        destination=destination,
        weather=weather,
        pack=pack,
        light=light,
        leader=leader,
        leader_gender=leader_gender,
        follower=follower,
        follower_gender=follower_gender,
        parent=parent,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        destination = DESTINATIONS[params.destination]
        weather = WEATHER[params.weather]
        pack = PACKS[params.pack]
        light = LIGHTS[params.light]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from None

    if not is_prepared(destination, pack):
        raise StoryError(explain_rejection(destination, pack))

    world = tell(
        destination=destination,
        weather=weather,
        pack=pack,
        light=light,
        leader_name=params.leader,
        leader_gender=params.leader_gender,
        follower_name=params.follower,
        follower_gender=params.follower_gender,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (destination, weather, pack, light) combos:\n")
        for destination, weather, pack, light in combos:
            demo = StoryParams(
                destination=destination,
                weather=weather,
                pack=pack,
                light=light,
                leader="Nora",
                leader_gender="girl",
                follower="Ben",
                follower_gender="boy",
                parent="mother",
                delay=1,
            )
            print(f"  {destination:7} {weather:7} {pack:13} {light:12} -> {asp_outcome(demo)}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.leader} & {p.follower}: {p.destination} in {p.weather} ({outcome_of_params(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
