#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/guest_kindness_bad_ending_bravery_myth.py
====================================================================

A standalone storyworld about a brave child, a mysterious guest, and the old
mythic law of hospitality. In this little domain, dusk brings a stranger to a
household door while some natural danger stands between the guest and the fire.
A kind child dares the danger with the right help. If the help is strong enough
and the delay is short, the guest reaches the hearth and leaves a blessing. If
the danger wins, the ending turns sorrowful and the village bears the mark of
its lateness.

Run it
------
    python storyworlds/worlds/gpt-5.4/guest_kindness_bad_ending_bravery_myth.py
    python storyworlds/worlds/gpt-5.4/guest_kindness_bad_ending_bravery_myth.py --obstacle ice_bridge --aid rope
    python storyworlds/worlds/gpt-5.4/guest_kindness_bad_ending_bravery_myth.py --aid flowers
    python storyworlds/worlds/gpt-5.4/guest_kindness_bad_ending_bravery_myth.py --all
    python storyworlds/worlds/gpt-5.4/guest_kindness_bad_ending_bravery_myth.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so the package dir is
# three levels up.
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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.type)


@dataclass
class Realm:
    id: str
    place: str
    house: str
    threshold_name: str
    custom: str
    good_image: str
    bad_image: str


@dataclass
class GuestFigure:
    id: str
    arrival: str
    call: str
    reveal: str
    blessing: str
    loss_sign: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    scene: str
    warning: str
    need_tag: str
    severity: int
    peril: str
    success_line: str
    fail_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    need_tag: str
    sense: int
    power: int
    carry: str
    success: str
    fail: str
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


def _r_exposure(world: World) -> list[str]:
    out: list[str] = []
    guest = world.entities.get("guest")
    hero = world.entities.get("hero")
    village = world.entities.get("village")
    if guest is None or hero is None or village is None:
        return out
    if guest.meters["exposed"] >= THRESHOLD:
        sig = ("exposure", guest.id)
        if sig not in world.fired:
            world.fired.add(sig)
            guest.meters["peril"] += 1
            hero.memes["kindness"] += 1
            hero.memes["fear"] += 1
            village.meters["unease"] += 1
    return out


def _r_shelter(world: World) -> list[str]:
    out: list[str] = []
    guest = world.entities.get("guest")
    village = world.entities.get("village")
    if guest is None or village is None:
        return out
    if guest.meters["sheltered"] >= THRESHOLD:
        sig = ("shelter", guest.id)
        if sig not in world.fired:
            world.fired.add(sig)
            guest.meters["peril"] = 0.0
            guest.meters["cold"] = 0.0
            village.meters["grace"] += 1
    return out


def _r_loss(world: World) -> list[str]:
    out: list[str] = []
    guest = world.entities.get("guest")
    hero = world.entities.get("hero")
    village = world.entities.get("village")
    if guest is None or hero is None or village is None:
        return out
    if guest.meters["lost"] >= THRESHOLD:
        sig = ("loss", guest.id)
        if sig not in world.fired:
            world.fired.add(sig)
            village.meters["grief"] += 1
            hero.memes["sorrow"] += 1
    return out


CAUSAL_RULES = [
    Rule(name="exposure", tag="physical", apply=_r_exposure),
    Rule(name="shelter", tag="social", apply=_r_shelter),
    Rule(name="loss", tag="social", apply=_r_loss),
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


def aid_matches(aid: Aid, obstacle: Obstacle) -> bool:
    return aid.need_tag == obstacle.need_tag


def sensible_aids() -> list[Aid]:
    return [aid for aid in AIDS.values() if aid.sense >= SENSE_MIN]


def danger_strength(obstacle: Obstacle, delay: int) -> int:
    return obstacle.severity + delay


def guest_survives(aid: Aid, obstacle: Obstacle, delay: int) -> bool:
    return aid.power >= danger_strength(obstacle, delay)


def predict_outcome(obstacle: Obstacle, aid: Aid, delay: int) -> dict:
    return {
        "match": aid_matches(aid, obstacle),
        "danger": danger_strength(obstacle, delay),
        "survives": aid_matches(aid, obstacle) and guest_survives(aid, obstacle, delay),
    }


def introduce(world: World, hero: Entity, elder: Entity, realm: Realm) -> None:
    world.say(
        f"In the old days, in {realm.place}, there stood {realm.house} beside "
        f"{realm.threshold_name}. {realm.custom}"
    )
    world.say(
        f"A child named {hero.id} lived there with {hero.pronoun('possessive')} "
        f"{elder.label_word}. {hero.id} was small, but people already said "
        f"{hero.pronoun('possessive')} heart was bigger than fear."
    )


def evening(world: World, realm: Realm) -> None:
    world.say(
        f"One blue evening, wind moved around {realm.threshold_name}, and the last "
        f"light thinned over {realm.place}."
    )


def guest_arrives(world: World, guest: Entity, guest_cfg: GuestFigure, obstacle: Obstacle) -> None:
    guest.meters["exposed"] += 1
    guest.meters["cold"] += 1
    propagate(world, narrate=False)
    world.say(
        f"From beyond {obstacle.scene} came {guest_cfg.arrival}. "
        f'"{guest_cfg.call}"'
    )
    world.say(
        f"It was a guest, and the sound of that lonely voice made the doorway feel "
        f"larger and darker all at once."
    )


def elder_warns(world: World, elder: Entity, hero: Entity, obstacle: Obstacle, aid: Aid) -> None:
    pred = predict_outcome(obstacle, aid, world.facts["delay"])
    world.facts["predicted_danger"] = pred["danger"]
    hero.memes["kindness"] += 1
    elder.memes["fear"] += 1
    world.say(
        f'{elder.label_word.capitalize()} caught {hero.id} by the sleeve. '
        f'"Do not run blindly," {elder.pronoun()} said. "{obstacle.warning}"'
    )
    world.say(
        f"{hero.id} looked into the dark and thought of the guest standing alone "
        f"outside the firelight."
    )


def choose_kindness(world: World, hero: Entity, aid: Aid) -> None:
    hero.memes["bravery"] += 1
    hero.memes["kindness"] += 1
    world.say(
        f'"A guest should not be left alone," {hero.id} said. '
        f'Then {hero.pronoun()} took {aid.phrase}.'
    )
    world.say(aid.carry.format(name=hero.id, subject=hero.pronoun(), possessive=hero.pronoun("possessive")))


def cross(world: World, hero: Entity, obstacle: Obstacle) -> None:
    world.say(obstacle.success_line.format(name=hero.id, subject=hero.pronoun(), possessive=hero.pronoun("possessive")))


def welcome(world: World, hero: Entity, elder: Entity, guest: Entity, realm: Realm,
            guest_cfg: GuestFigure, aid: Aid) -> None:
    guest.meters["exposed"] = 0.0
    guest.meters["sheltered"] += 1
    propagate(world, narrate=False)
    hero.memes["relief"] += 1
    hero.memes["love"] += 1
    world.say(
        aid.success.format(name=hero.id, subject=hero.pronoun(), possessive=hero.pronoun("possessive"))
    )
    world.say(
        f"Soon the guest sat beside the hearth while {elder.label_word} set out "
        f"bread, honey, and a warm cup. Kindness made the whole house feel taller."
    )
    world.say(
        f"Before dawn, the guest was gone, but on the stone threshold lay {guest_cfg.reveal}. "
        f"People said {guest_cfg.blessing}."
    )
    world.say(realm.good_image)


def lose_guest(world: World, hero: Entity, elder: Entity, guest: Entity, realm: Realm,
               guest_cfg: GuestFigure, obstacle: Obstacle, aid: Aid) -> None:
    guest.meters["lost"] += 1
    propagate(world, narrate=False)
    hero.memes["sorrow"] += 1
    world.say(
        aid.fail.format(name=hero.id, subject=hero.pronoun(), possessive=hero.pronoun("possessive"))
    )
    world.say(
        obstacle.fail_line.format(name=hero.id, subject=hero.pronoun(), possessive=hero.pronoun("possessive"))
    )
    world.say(
        f"{hero.id} was brave enough to go, but bravery could not turn back time. "
        f"When {hero.pronoun()} reached the place, the guest was gone, leaving only "
        f"{guest_cfg.loss_sign}."
    )
    world.say(
        f"{elder.label_word.capitalize()} drew {hero.id} close, and neither of them "
        f"spoke for a long while. They had meant kindness, but they had come too late."
    )
    world.say(realm.bad_image)


def tell(realm: Realm, guest_cfg: GuestFigure, obstacle: Obstacle, aid: Aid,
         hero_name: str = "Mira", hero_gender: str = "girl",
         elder_type: str = "grandmother", delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_gender, role="hero",
        traits=["kind", "brave"],
    ))
    elder = world.add(Entity(
        id="Elder", kind="character", type=elder_type, role="elder", label="the elder",
    ))
    guest = world.add(Entity(
        id="guest", kind="character", type="traveler", role="guest", label="the guest",
        tags=set(guest_cfg.tags),
    ))
    world.add(Entity(id="village", type="village", label="the village"))
    world.facts["delay"] = delay

    introduce(world, hero, elder, realm)
    evening(world, realm)

    world.para()
    guest_arrives(world, guest, guest_cfg, obstacle)
    elder_warns(world, elder, hero, obstacle, aid)
    choose_kindness(world, hero, aid)

    world.para()
    cross(world, hero, obstacle)
    survived = guest_survives(aid, obstacle, delay)
    if survived:
        welcome(world, hero, elder, guest, realm, guest_cfg, aid)
        outcome = "welcomed"
    else:
        lose_guest(world, hero, elder, guest, realm, guest_cfg, obstacle, aid)
        outcome = "lost"

    world.facts.update(
        realm=realm,
        guest_cfg=guest_cfg,
        obstacle=obstacle,
        aid=aid,
        hero=hero,
        elder=elder,
        guest=guest,
        outcome=outcome,
        danger=danger_strength(obstacle, delay),
        delay=delay,
        survived=survived,
    )
    return world


REALMS = {
    "olive_hill": Realm(
        id="olive_hill",
        place="a hill of olive trees",
        house="a white house with a painted door",
        threshold_name="the lion gate",
        custom="The old people taught that any guest might be a hidden power, so a lamp was always kept near the door.",
        good_image="After that, the olives on the hill shone thick and silver, and no traveler went hungry at that door.",
        bad_image="After that night, the olives rattled dry in the wind, and even at noon the lion gate looked lonely.",
    ),
    "river_shrine": Realm(
        id="river_shrine",
        place="a river village below a moon shrine",
        house="a stone house with blue jars on the wall",
        threshold_name="the reed gate",
        custom="In that place, people said the river listened whenever a household welcomed a guest with clean hands and warm food.",
        good_image="After that, the river ran clear and full, and children found bright fish flashing between the reeds.",
        bad_image="After that night, the river went dim and thin, and reeds whispered like people telling a sad story.",
    ),
    "pine_cliff": Realm(
        id="pine_cliff",
        place="a cliff village above the sea",
        house="a tall house roofed in red tile",
        threshold_name="the gull gate",
        custom="The fishers believed the sea sent guests in plain cloaks to measure the kindness of a home.",
        good_image="After that, the sea sent easy winds, and the red tiles glowed warm at sunset.",
        bad_image="After that night, the sea beat hard against the cliff, and salt gathered on the red tiles like tears.",
    ),
}

GUESTS = {
    "pilgrim": GuestFigure(
        id="pilgrim",
        arrival="an old pilgrim with dust on the hem of a gray robe",
        call="Please, is there a fire for a weary guest?",
        reveal="a small coin stamped with a sunrise",
        blessing="the Dawn-Walker had tested that house and found it gentle",
        loss_sign="a single dusty footprint facing the road",
        tags={"guest", "kindness"},
    ),
    "singer": GuestFigure(
        id="singer",
        arrival="a wandering singer with a shell harp wrapped under one arm",
        call="Will any door remember a guest tonight?",
        reveal="a silver string that sang when the morning wind touched it",
        blessing="the Lady of Songs had left music in that house",
        loss_sign="one snapped harp string on a stone",
        tags={"guest", "music", "kindness"},
    ),
    "star_stranger": GuestFigure(
        id="star_stranger",
        arrival="a bent stranger whose cloak held a few pale sparks like sleepy stars",
        call="Child of this house, may a guest step into your light?",
        reveal="three bright seeds that never stopped glowing",
        blessing="a hidden star had bent low to bless the brave child",
        loss_sign="a little ash that glittered and blew away",
        tags={"guest", "star", "kindness"},
    ),
}

OBSTACLES = {
    "night_path": Obstacle(
        id="night_path",
        label="night path",
        scene="the black thorn path",
        warning="The thorn path is blind at night. One wrong step and the rocks bite.",
        need_tag="light",
        severity=2,
        peril="darkness",
        success_line="{name} stepped onto the thorn path. {possessive_cap} knees trembled, but a steady light pushed the dark back from each stone.",
        fail_line="The dark drank the little safety there was, and the path twisted longer than it had looked from the door.",
        tags={"darkness", "path"},
    ),
    "ice_bridge": Obstacle(
        id="ice_bridge",
        label="ice bridge",
        scene="the ice bridge over the mill stream",
        warning="The bridge is glazed with ice. Feet slide there faster than thoughts.",
        need_tag="rope",
        severity=3,
        peril="ice",
        success_line="{name} went out over the ice bridge while the stream hissed below. {possessive_cap} breath smoked in the air, but a sure line gave each step a promise.",
        fail_line="The bridge shone cruelly, and the stream below spoke in the cold voice of winter.",
        tags={"ice", "bridge"},
    ),
    "snow_wind": Obstacle(
        id="snow_wind",
        label="snow wind",
        scene="the snowy yard between the house and the shrine road",
        warning="The snow-wind steals heat from fingers and ears before a child can count to ten.",
        need_tag="warmth",
        severity=2,
        peril="cold",
        success_line="{name} leaned into the snow-wind. It tugged and whistled, but courage kept moving one small step after another.",
        fail_line="The snow-wind pressed hard against face and hands, and warmth leaked away into the white air.",
        tags={"snow", "cold"},
    ),
}

AIDS = {
    "lantern": Aid(
        id="lantern",
        label="lantern",
        phrase="a bronze lantern",
        need_tag="light",
        sense=3,
        power=3,
        carry="{name} lifted the bronze lantern high, and the flame inside made a round gold promise on the wall.",
        success="{name} found the guest and held the lantern so the safe stones showed themselves. Side by side, they came back to the house through the obedient dark.",
        fail="{name} held the lantern bravely, but the night had already grown too deep and wide for one small circle of light.",
        tags={"lantern", "light"},
    ),
    "rope": Aid(
        id="rope",
        label="rope",
        phrase="a coil of hemp rope",
        need_tag="rope",
        sense=3,
        power=3,
        carry="{name} took a coil of hemp rope over one shoulder and wrapped the end around a wrist that would not stop shaking.",
        success="{name} reached the guest, tied the rope around them both, and led the careful way back across the bridge.",
        fail="{name} cast the rope and tried to make a path of it, but ice and delay had made the crossing crueler than courage alone could mend.",
        tags={"rope", "bridge"},
    ),
    "cloak": Aid(
        id="cloak",
        label="cloak",
        phrase="a thick wool cloak",
        need_tag="warmth",
        sense=3,
        power=2,
        carry="{name} snatched up a thick wool cloak and ran with it pressed to {possessive} chest like an extra heartbeat.",
        success="{name} wrapped the guest in the warm cloak and put a small steady shoulder beneath one cold arm. Together they reached the red glow of the hearth.",
        fail="{name} wrapped the cloak around the guest as soon as {subject} could, but too much warmth had already been stolen by the wind.",
        tags={"cloak", "warmth"},
    ),
    "flowers": Aid(
        id="flowers",
        label="flowers",
        phrase="a bunch of summer flowers",
        need_tag="none",
        sense=1,
        power=0,
        carry="{name} picked up flowers that smelled sweet but did not fight danger.",
        success="{name} somehow solved everything with flowers.",
        fail="{name} offered flowers, but they could not light dark, grip ice, or warm cold hands.",
        tags={"flowers"},
    ),
}

GIRL_NAMES = ["Mira", "Dara", "Lina", "Nia", "Tala", "Rhea", "Iris", "Phae"]
BOY_NAMES = ["Aren", "Theo", "Nikos", "Leo", "Ivo", "Milo", "Damon", "Orin"]


@dataclass
class StoryParams:
    realm: str
    guest: str
    obstacle: str
    aid: str
    hero_name: str
    hero_gender: str
    elder: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        realm="olive_hill",
        guest="pilgrim",
        obstacle="night_path",
        aid="lantern",
        hero_name="Mira",
        hero_gender="girl",
        elder="grandmother",
        delay=0,
    ),
    StoryParams(
        realm="river_shrine",
        guest="singer",
        obstacle="ice_bridge",
        aid="rope",
        hero_name="Aren",
        hero_gender="boy",
        elder="grandfather",
        delay=0,
    ),
    StoryParams(
        realm="pine_cliff",
        guest="star_stranger",
        obstacle="snow_wind",
        aid="cloak",
        hero_name="Lina",
        hero_gender="girl",
        elder="grandmother",
        delay=2,
    ),
    StoryParams(
        realm="olive_hill",
        guest="singer",
        obstacle="ice_bridge",
        aid="rope",
        hero_name="Theo",
        hero_gender="boy",
        elder="grandfather",
        delay=1,
    ),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for realm_id in REALMS:
        for guest_id in GUESTS:
            for obstacle_id, obstacle in OBSTACLES.items():
                for aid_id, aid in AIDS.items():
                    if aid_matches(aid, obstacle) and aid.sense >= SENSE_MIN:
                        combos.append((realm_id, guest_id, obstacle_id, aid_id))
    return combos


def explain_rejection(obstacle: Obstacle, aid: Aid) -> str:
    if aid.sense < SENSE_MIN:
        return (
            f"(No story: {aid.label} is too weak or silly for this danger "
            f"(sense={aid.sense} < {SENSE_MIN}). A mythic rescue should use help "
            f"that could honestly matter.)"
        )
    return (
        f"(No story: {aid.label} does not fit {obstacle.label}. This danger needs "
        f"{obstacle.need_tag}, so the brave act would not make sense with that aid.)"
    )


def outcome_of(params: StoryParams) -> str:
    aid = AIDS.get(params.aid)
    obstacle = OBSTACLES.get(params.obstacle)
    if aid is None or obstacle is None:
        raise StoryError("(No story: unknown aid or obstacle.)")
    return "welcomed" if guest_survives(aid, obstacle, params.delay) else "lost"


KNOWLEDGE = {
    "guest": [
        (
            "What is a guest?",
            "A guest is someone who comes to your home or table and is welcomed there. In many old stories, being kind to a guest matters a great deal."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means noticing that someone needs help and choosing to help if you can. Sometimes kindness is a warm meal, and sometimes it is a brave action."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery does not mean feeling no fear. It means doing the right thing even when your knees are shaking."
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern makes light so people can see in the dark. In old stories, a lantern often stands for hope and guidance."
        )
    ],
    "rope": [
        (
            "Why can a rope help on a slippery bridge?",
            "A rope gives people something firm to hold or tie to. That makes it easier to cross carefully without sliding away."
        )
    ],
    "cloak": [
        (
            "Why can a cloak help in cold wind?",
            "A thick cloak holds warmth around a person's body. That helps stop the cold wind from stealing heat so quickly."
        )
    ],
    "darkness": [
        (
            "Why is darkness hard to cross in a story?",
            "Darkness hides rocks, holes, and the right path. That is why stories often give a brave traveler a light."
        )
    ],
    "ice": [
        (
            "Why is ice dangerous under your feet?",
            "Ice is smooth and slippery, so feet can slide before you are ready. A fall on ice can happen very fast."
        )
    ],
    "snow": [
        (
            "Why can snow-wind be dangerous?",
            "Snow-wind is dangerous because it makes people colder very quickly. Hands and faces can go numb, and a person can grow weak."
        )
    ],
}
KNOWLEDGE_ORDER = ["guest", "kindness", "bravery", "lantern", "rope", "cloak", "darkness", "ice", "snow"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    guest_cfg = f["guest_cfg"]
    obstacle = f["obstacle"]
    aid = f["aid"]
    outcome = f["outcome"]
    if outcome == "lost":
        return [
            f'Write a child-facing myth about a brave child and a guest at the door. Include the word "guest" and give it a sorrowful ending.',
            f"Tell a mythic story where {hero.id} tries to help a mysterious guest across {obstacle.label} with {aid.label}, but arrives too late and learns that bravery cannot mend every loss.",
            f"Write a gentle but sad myth where {guest_cfg.arrival} asks for shelter, and a kind child goes out to help."
        ]
    return [
        f'Write a child-facing myth about kindness to a guest, and include the word "guest".',
        f"Tell a mythic story where {hero.id} bravely carries {aid.label} through {obstacle.label} to help a mysterious traveler reach the fire.",
        f"Write a short myth in which welcoming a guest brings a blessing to a household."
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    guest_cfg = f["guest_cfg"]
    obstacle = f["obstacle"]
    aid = f["aid"]
    realm = f["realm"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a brave child, {hero.pronoun('possessive')} {elder.label_word}, and a mysterious guest who came to the door at dusk."
        ),
        (
            "Why did the child go outside?",
            f"{hero.id} heard a guest calling from beyond {obstacle.scene} and did not want to leave that stranger alone in danger. The choice to go came from kindness, even though the path was frightening."
        ),
        (
            f"What did {hero.id} carry?",
            f"{hero.id} carried {aid.phrase}. That was the right kind of help for {obstacle.label}, because it could honestly protect the guest from that danger."
        ),
    ]
    if outcome == "welcomed":
        qa.append(
            (
                "How did kindness change the ending?",
                f"Kindness brought the guest safely to the hearth, and the house was blessed. In this myth, welcoming the stranger changed the whole place, because {realm.good_image[0].lower() + realm.good_image[1:]}"
            )
        )
        qa.append(
            (
                "What showed that the guest was special?",
                f"When morning came, the guest had vanished and left {guest_cfg.reveal}. That sign made people think the traveler had been more than an ordinary wanderer."
            )
        )
    else:
        qa.append(
            (
                "Why is the ending sad even though the child was brave?",
                f"The ending is sad because {hero.id} truly tried to help, but the danger had already grown too strong. The story says that courage matters, yet some losses still happen when help comes too late."
            )
        )
        qa.append(
            (
                "What proved that something had gone wrong in the village?",
                f"The guest was gone and only {guest_cfg.loss_sign} remained. After that, {realm.bad_image[0].lower() + realm.bad_image[1:]}"
            )
        )
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"guest", "kindness", "bravery"} | set(f["aid"].tags) | set(f["obstacle"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% Reasonableness gate: a valid story uses aid that fits the danger and is sensible.
fits(A, O) :- aid(A), obstacle(O), helps(A, T), needs(O, T).
sensible(A) :- aid(A), sense(A, S), sense_min(M), S >= M.
valid(R, G, O, A) :- realm(R), guest(G), obstacle(O), aid(A), fits(A, O), sensible(A).

% Outcome model: welcome if the aid's power beats the danger (severity + delay).
danger(V) :- chosen_obstacle(O), severity(O, S), delay(D), V = S + D.
welcomed :- chosen_aid(A), chosen_obstacle(O), fits(A, O), power(A, P), danger(V), P >= V.
lost :- chosen_aid(A), chosen_obstacle(O), fits(A, O), power(A, P), danger(V), P < V.

outcome(welcomed) :- welcomed.
outcome(lost) :- lost.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for realm_id in REALMS:
        lines.append(asp.fact("realm", realm_id))
    for guest_id in GUESTS:
        lines.append(asp.fact("guest", guest_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("needs", obstacle_id, obstacle.need_tag))
        lines.append(asp.fact("severity", obstacle_id, obstacle.severity))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("helps", aid_id, aid.need_tag))
        lines.append(asp.fact("sense", aid_id, aid.sense))
        lines.append(asp.fact("power", aid_id, aid.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(aid for (aid,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_aid", params.aid),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a brave child, a mysterious guest, and the old law of hospitality."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--guest", choices=GUESTS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather", "mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the guest remains in danger before help arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.aid and args.obstacle:
        aid = AIDS[args.aid]
        obstacle = OBSTACLES[args.obstacle]
        if not (aid_matches(aid, obstacle) and aid.sense >= SENSE_MIN):
            raise StoryError(explain_rejection(obstacle, aid))
    if args.aid and AIDS[args.aid].sense < SENSE_MIN:
        obstacle = OBSTACLES[args.obstacle] if args.obstacle else next(iter(OBSTACLES.values()))
        raise StoryError(explain_rejection(obstacle, AIDS[args.aid]))

    combos = [
        combo for combo in valid_combos()
        if (args.realm is None or combo[0] == args.realm)
        and (args.guest is None or combo[1] == args.guest)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.aid is None or combo[3] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    realm_id, guest_id, obstacle_id, aid_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        realm=realm_id,
        guest=guest_id,
        obstacle=obstacle_id,
        aid=aid_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder=elder,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    realm = REALMS.get(params.realm)
    guest_cfg = GUESTS.get(params.guest)
    obstacle = OBSTACLES.get(params.obstacle)
    aid = AIDS.get(params.aid)
    if realm is None or guest_cfg is None or obstacle is None or aid is None:
        raise StoryError("(No story: one or more params are unknown.)")
    if not aid_matches(aid, obstacle) or aid.sense < SENSE_MIN:
        raise StoryError(explain_rejection(obstacle, aid))

    world = tell(
        realm=realm,
        guest_cfg=guest_cfg,
        obstacle=obstacle,
        aid=aid,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_type=params.elder,
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

    c_sens = set(asp_sensible())
    p_sens = {aid.id for aid in sensible_aids()}
    if c_sens == p_sens:
        print(f"OK: sensible aids match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible aids: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible aids: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (realm, guest, obstacle, aid) combos:\n")
        for realm, guest, obstacle, aid in combos:
            print(f"  {realm:12} {guest:13} {obstacle:11} {aid}")
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
            header = (
                f"### {p.hero_name}: {p.guest} at {p.realm} "
                f"({p.obstacle}, {p.aid}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
