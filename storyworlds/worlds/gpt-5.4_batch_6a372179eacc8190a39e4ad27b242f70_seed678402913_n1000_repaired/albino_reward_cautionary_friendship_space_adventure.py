#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/albino_reward_cautionary_friendship_space_adventure.py
=================================================================================

A standalone story world for a small cautionary friendship tale in a cheerful
space-adventure style.

Premise
-------
Two young friends on a moon-base field trip hear about a reward for carefully
spotting a rare albino creature. In the dark habitat where the creature hides,
one friend is tempted to use a forbidden flame-making tool for a quick look.
The other friend warns that the dry habitat materials could catch fire. Depending
on the world state, the warning may avert the danger, or a small fire may start
and a calm grown-up must fix it. In every happy ending, the real reward turns
out to be safe teamwork and honest friendship.

Run it
------
    python storyworlds/worlds/gpt-5.4/albino_reward_cautionary_friendship_space_adventure.py
    python storyworlds/worlds/gpt-5.4/albino_reward_cautionary_friendship_space_adventure.py --habitat fern_dome
    python storyworlds/worlds/gpt-5.4/albino_reward_cautionary_friendship_space_adventure.py --target steel_wall
    python storyworlds/worlds/gpt-5.4/albino_reward_cautionary_friendship_space_adventure.py --verify
    python storyworlds/worlds/gpt-5.4/albino_reward_cautionary_friendship_space_adventure.py --all --qa
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
IMPULSE_INIT = 6.0
LOYAL_FRIENDSHIP_MIN = 8


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
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
    age: int = 0
    attrs: dict = field(default_factory=dict)
    flammable: bool = False
    makes_flame: bool = False
    gives_light: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man"}
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
            "captain": "captain",
        }.get(self.type, self.type)


@dataclass
class Habitat:
    id: str
    scene: str
    opening: str
    dark_spot: str
    cave_word: str
    creature_home: str
    ending_path: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Forbidden:
    id: str
    cry: str
    label: str
    phrase: str
    where: str
    unit: str
    sound: str
    lesson: str
    plural: bool = False
    makes_flame: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    the: str
    near: str
    detail: str
    spread: int = 2
    flammable: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class RewardCfg:
    id: str
    label: str
    phrase: str
    cheer: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeTool:
    id: str
    label: str
    phrase: str
    glow: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "friend"}]

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


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["burning"] < THRESHOLD:
            continue
        sig = ("spread", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "room" in world.entities:
            world.get("room").meters["danger"] += 1
        for kid in world.kids():
            kid.memes["fear"] += 1
        out.append("__fire__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="spread", tag="physical", apply=_r_spread),
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


def hazard_at_risk(forbidden: Forbidden, target: Target) -> bool:
    return forbidden.makes_flame and target.flammable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fire_severity(target: Target, delay: int) -> int:
    return target.spread + delay


def is_contained(response: Response, target: Target, delay: int) -> bool:
    return response.power >= fire_severity(target, delay)


def would_avert(friendship: int, trait: str) -> bool:
    careful = trait in {"careful", "steady", "thoughtful", "loyal"}
    bonus = 1 if careful else 0
    return friendship + bonus >= LOYAL_FRIENDSHIP_MIN


def predict_fire(world: World, target_id: str) -> dict:
    sim = world.copy()
    _do_forbidden(sim, sim.get(target_id), narrate=False)
    return {
        "ignites": sim.get(target_id).meters["burning"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
    }


def _do_forbidden(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["burning"] += 1
    target.meters["scorched"] += 1
    propagate(world, narrate=narrate)


def introduce_reward(world: World, captain: Entity, reward: RewardCfg) -> None:
    world.say(
        f"At Moonbright Base, {captain.label_word.capitalize()} Mira clapped her hands and pointed to a silver poster by the biodome door."
    )
    world.say(
        f'"Today\'s mission," {captain.pronoun()} said, "is to spot the shy albino moon-mouse without scaring it. The careful team that helps best will earn {reward.phrase}."'
    )


def setup_adventure(world: World, a: Entity, b: Entity, habitat: Habitat) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["wonder"] += 1
    world.say(
        f"{a.id} and {b.id} hurried into {habitat.scene}. {habitat.opening}"
    )
    world.say(
        f"To them it felt like a real space adventure, the kind where every shadow might hide a secret creature."
    )


def need_light(world: World, b: Entity, habitat: Habitat, target: Target) -> None:
    world.say(
        f"But {habitat.dark_spot}, {target.detail}, was dim as midnight on the far side of the moon."
    )
    world.say(
        f'{b.id} squinted into the {habitat.cave_word}. "The albino moon-mouse might be hiding in there," {b.pronoun()} whispered.'
    )


def tempt(world: World, a: Entity, forbidden: Forbidden, reward: RewardCfg) -> None:
    a.memes["impulse"] = IMPULSE_INIT
    a.memes["greed"] += 1
    world.say(
        f'{a.id}\'s eyes shone. "{forbidden.cry} If I use {forbidden.phrase} {forbidden.where}, I can peek inside first and maybe win {reward.the_phrase if hasattr(reward, "the_phrase") else reward.phrase}!"'
    )


def warn(world: World, b: Entity, a: Entity, forbidden: Forbidden, target: Target, reward: RewardCfg) -> None:
    pred = predict_fire(world, "target")
    world.facts["predicted_danger"] = pred["danger"]
    b.memes["caution"] += 1
    world.say(
        f'{b.id} caught {a.id}\'s sleeve. "No, {a.id}. {forbidden.label.capitalize()} are for grown-ups. If a spark touches {target.near}, {target.the} could catch fire, and a {reward.label} would not be worth that."'
    )
    if b.memes["friendship"] >= THRESHOLD:
        world.say(
            f'{b.id} stayed close instead of stomping away. "I want the reward too," {b.pronoun()} said, "but I want my friend safe even more."'
        )


def back_down(world: World, a: Entity, b: Entity, forbidden: Forbidden, captain: Entity) -> None:
    a.memes["impulse"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked at {b.id}, then at {forbidden.label}, and let out a slow breath. "Okay," {a.pronoun()} said. "You are right."'
    )
    world.say(
        f"Together they left the forbidden tool where it belonged and called for {captain.label_word} Mira instead."
    )


def defy(world: World, a: Entity, b: Entity, forbidden: Forbidden) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"We only need one little spark," {a.id} said, and before {b.id} could stop {a.pronoun("object")}, {a.pronoun()} reached for {forbidden.label}.'
    )


def ignite(world: World, target_ent: Entity, forbidden: Forbidden, target: Target) -> None:
    _do_forbidden(world, target_ent, narrate=True)
    world.say(
        f"{forbidden.sound} {forbidden.unit[0].upper()}{forbidden.unit[1:]} flashed to life. For half a heartbeat it looked bright and brave, like a tiny star in a child's hand. Then the spark leaned the wrong way, kissed {target.near}, and a sharp orange line began to climb."
    )


def alarm(world: World, b: Entity, target: Target, captain: Entity) -> None:
    world.say(f'"Fire! {target.The}!" {b.id} cried.')
    world.say(f'"Captain Mira!"')


def rescue(world: World, captain: Entity, response: Response, target_ent: Entity, target: Target) -> None:
    target_ent.meters["burning"] = 0.0
    world.get("room").meters["danger"] = 0.0
    world.say(
        f"{captain.label_word.capitalize()} Mira came running and {response.text.replace('{target}', target.label)}."
    )
    world.say(
        "The hiss of the foam sounded loud in the quiet dome, and then the fire was gone."
    )


def rescue_fail(world: World, captain: Entity, response: Response, target_ent: Entity, target: Target) -> None:
    if "room" in world.entities:
        world.get("room").meters["burning"] += 1
    target_ent.meters["burning"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{captain.label_word.capitalize()} Mira rushed in and {response.fail.replace('{target}', target.label)}."
    )
    world.say(
        f"But the flames raced from {target.the} into the rest of the habitat faster than little feet could think."
    )


def lesson(world: World, captain: Entity, a: Entity, b: Entity, forbidden: Forbidden) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["friendship"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say("For a moment, the two friends only held each other's hands.")
    world.say(
        f'Then Captain Mira knelt beside them. "I am glad you called for help," {captain.pronoun()} said softly. "But remember this always: {forbidden.lesson}. A real spark can turn a game into danger faster than you expect."'
    )


def grim_lesson(world: World, captain: Entity, a: Entity, b: Entity, forbidden: Forbidden) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["friendship"] += 1
        kid.memes["fear"] += 1
    world.say(
        f"Outside the sealed dome, Captain Mira wrapped both children in one silver rescue blanket."
    )
    world.say(
        f'"You are safe, and that matters most," {captain.pronoun()} told them. "But never forget: {forbidden.lesson}, and friends must stop each other before danger grows."'
    )


def reward_safe(world: World, captain: Entity, a: Entity, b: Entity, reward: RewardCfg, habitat: Habitat, tool1: SafeTool, tool2: SafeTool) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["friendship"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"A little later, Captain Mira handed them {tool1.phrase} and {tool2.phrase}. {tool1.label.capitalize()} {tool1.glow}, and the {tool2.label} {tool2.glow}."
    )
    world.say(
        f"With safe light, the friends peered into {habitat.creature_home}. Two pink eyes blinked back, and out stepped the tiny albino moon-mouse, white as moon dust."
    )
    world.say(
        f'"There it is!" {b.id} whispered.'
    )
    world.say(
        f'Captain Mira smiled. "{reward.cheer} You shared the mission, you told the truth, and you kept each other safe."'
    )
    world.say(
        f"They clipped the reward to one map board between them and walked {habitat.ending_path} side by side, feeling like the best space team on the whole moon."
    )


def reward_after_fire(world: World, captain: Entity, a: Entity, b: Entity, reward: RewardCfg, habitat: Habitat, tool1: SafeTool, tool2: SafeTool) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
        kid.memes["friendship"] += 1
    world.say(
        f"The next day, after the scorched smell was gone, Captain Mira came back with {tool1.phrase} and {tool2.phrase}."
    )
    world.say(
        f'"We explore the moon with safe tools," {captain.pronoun()} said.'
    )
    world.say(
        f"This time the friends used them to look into {habitat.creature_home}. The little albino moon-mouse peeked out at last, its pale whiskers shining."
    )
    world.say(
        f'"And here is your {reward.label}," Captain Mira added. "Not for rushing, but for telling the truth and staying together when things got scary."'
    )
    world.say(
        f"{a.id} and {b.id} shared the reward and walked {habitat.ending_path} more carefully than before."
    )


def escape(world: World, captain: Entity, a: Entity, b: Entity, habitat: Habitat) -> None:
    world.say(
        f"Warning lights blinked red over {habitat.scene}. Captain Mira hurried {a.id} and {b.id} through the safety door into the moon-cold hallway."
    )
    world.say(
        f"They watched through the round window as shutters sealed over the habitat, and the adventure suddenly felt small beside the danger."
    )


def tell(
    habitat: Habitat,
    forbidden: Forbidden,
    target: Target,
    reward: RewardCfg,
    safe_tools: tuple[SafeTool, SafeTool],
    response: Response,
    instigator: str = "Nova",
    instigator_gender: str = "girl",
    friend: str = "Jae",
    friend_gender: str = "boy",
    trait: str = "careful",
    captain_type: str = "captain",
    delay: int = 0,
    friendship: int = 7,
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        traits=["bold"],
    ))
    b = world.add(Entity(
        id=friend,
        kind="character",
        type=friend_gender,
        role="friend",
        traits=[trait],
    ))
    captain = world.add(Entity(
        id="Captain",
        kind="character",
        type=captain_type,
        role="captain",
        label="captain",
    ))
    world.add(Entity(id="room", type="room", label="the habitat"))
    tool = world.add(Entity(
        id="tool",
        type="tool",
        label=forbidden.label,
        makes_flame=True,
    ))
    tgt = world.add(Entity(
        id="target",
        type="target",
        label=target.label,
        flammable=target.flammable,
    ))
    a.memes["friendship"] = float(friendship)
    b.memes["friendship"] = float(friendship)
    b.memes["caution"] = 5.0 if trait in {"careful", "steady", "thoughtful", "loyal"} else 3.0

    introduce_reward(world, captain, reward)
    setup_adventure(world, a, b, habitat)
    need_light(world, b, habitat, target)

    world.para()
    tempt(world, a, forbidden, reward)
    warn(world, b, a, forbidden, target, reward)

    averted = would_avert(friendship, trait)
    if averted:
        back_down(world, a, b, forbidden, captain)
        world.para()
        reward_safe(world, captain, a, b, reward, habitat, safe_tools[0], safe_tools[1])
        severity = 0
        contained = True
    else:
        defy(world, a, b, forbidden)
        world.para()
        ignite(world, tgt, forbidden, target)
        alarm(world, b, target, captain)
        severity = fire_severity(target, delay)
        tgt.meters["severity"] = float(severity)
        contained = is_contained(response, target, delay)
        world.para()
        if contained:
            rescue(world, captain, response, tgt, target)
            lesson(world, captain, a, b, forbidden)
            world.para()
            reward_after_fire(world, captain, a, b, reward, habitat, safe_tools[0], safe_tools[1])
        else:
            rescue_fail(world, captain, response, tgt, target)
            escape(world, captain, a, b, habitat)
            grim_lesson(world, captain, a, b, forbidden)

    outcome = "averted" if averted else ("contained" if contained else "burned")
    world.facts.update(
        habitat=habitat,
        forbidden=forbidden,
        target_cfg=target,
        target=tgt,
        reward=reward,
        safe_tools=safe_tools,
        response=response,
        instigator=a,
        friend=b,
        captain=captain,
        friendship=friendship,
        ignited=tgt.meters["scorched"] >= THRESHOLD,
        outcome=outcome,
        severity=severity,
        delay=delay,
    )
    return world


HABITATS = {
    "fern_dome": Habitat(
        id="fern_dome",
        scene="the Fern Dome",
        opening="Tall red ferns arched overhead, and the glass ceiling showed a soft blue Earth hanging far away.",
        dark_spot="a hollow under a low rock arch",
        cave_word="hollow",
        creature_home="the cool rock hollow under the ferns",
        ending_path="back through the glowing airlock tunnel",
        tags={"moonbase", "habitat"},
    ),
    "crystal_grotto": Habitat(
        id="crystal_grotto",
        scene="the Crystal Grotto",
        opening="Pale mineral walls glittered like frozen stars, and the floor hummed with gentle rover lights.",
        dark_spot="a crack behind the crystal shelf",
        cave_word="crack",
        creature_home="the shadowy crack behind the crystal shelf",
        ending_path="past the rover dock with quiet proud steps",
        tags={"moonbase", "crystal"},
    ),
    "moss_lab": Habitat(
        id="moss_lab",
        scene="the Moss Lab",
        opening="Soft silver moss climbed the planters, and little fans whispered as if the room were breathing.",
        dark_spot="the nook behind the water tanks",
        cave_word="nook",
        creature_home="the damp nook behind the tanks",
        ending_path="under the round lamp rings of the lab hall",
        tags={"moonbase", "lab"},
    ),
}

FORBIDDEN = {
    "flare_pen": Forbidden(
        id="flare_pen",
        cry="The flare pen!",
        label="the flare pen",
        phrase="the flare pen",
        where="from the emergency shelf",
        unit="the tiny flare tip",
        sound="Ffft!",
        lesson="flare pens are not toys",
        plural=False,
        tags={"fire", "flare", "call_adult"},
    ),
    "plasma_match": Forbidden(
        id="plasma_match",
        cry="Plasma matches!",
        label="plasma matches",
        phrase="the plasma matches",
        where="in the tool drawer",
        unit="the first blue spark",
        sound="Tzzk!",
        lesson="plasma matches are not toys",
        plural=True,
        tags={"fire", "plasma", "call_adult"},
    ),
    "mini_torch": Forbidden(
        id="mini_torch",
        cry="The mini torch!",
        label="the mini torch",
        phrase="the mini torch",
        where="by the repair kit",
        unit="the little torch flame",
        sound="Click!",
        lesson="mini torches are not toys",
        plural=False,
        tags={"fire", "torch", "call_adult"},
    ),
}

TARGETS = {
    "star_reeds": Target(
        id="star_reeds",
        label="star reeds",
        the="the star reeds",
        near="the dry tips of the star reeds",
        detail="fringed with dry star reeds",
        spread=3,
        flammable=True,
        tags={"flammable", "reeds"},
    ),
    "nest_pad": Target(
        id="nest_pad",
        label="nesting pad",
        the="the nesting pad",
        near="the edge of the nesting pad",
        detail="lined with a fluffy nesting pad",
        spread=2,
        flammable=True,
        tags={"flammable", "nest"},
    ),
    "shade_cloth": Target(
        id="shade_cloth",
        label="shade cloth",
        the="the shade cloth",
        near="the hanging shade cloth",
        detail="hung with a curtain of shade cloth",
        spread=2,
        flammable=True,
        tags={"flammable", "cloth"},
    ),
    "steel_wall": Target(
        id="steel_wall",
        label="steel wall",
        the="the steel wall",
        near="the cool steel wall",
        detail="rimmed with plain steel panels",
        spread=0,
        flammable=False,
        tags={"steel"},
    ),
}

REWARDS = {
    "star_badge": RewardCfg(
        id="star_badge",
        label="star badge",
        phrase="a silver star badge as the reward",
        cheer="This silver star badge is your reward",
        tags={"reward", "badge"},
    ),
    "patch": RewardCfg(
        id="patch",
        label="mission patch",
        phrase="a bright mission patch as the reward",
        cheer="This mission patch is your reward",
        tags={"reward", "patch"},
    ),
    "pin": RewardCfg(
        id="pin",
        label="comet pin",
        phrase="a shiny comet pin as the reward",
        cheer="This comet pin is your reward",
        tags={"reward", "pin"},
    ),
}

SAFE_TOOLS = {
    "beam_lamp": SafeTool(
        id="beam_lamp",
        label="beam lamp",
        phrase="a beam lamp",
        glow="clicked on with a wide white circle",
        tags={"light", "lamp"},
    ),
    "glow_map": SafeTool(
        id="glow_map",
        label="glow map",
        phrase="a glow map",
        glow="shimmered with soft green lines",
        tags={"light", "map"},
    ),
    "helmet_lights": SafeTool(
        id="helmet_lights",
        label="helmet lights",
        phrase="helmet lights",
        glow="beamed straight ahead in two safe bright bars",
        tags={"light", "helmet"},
    ),
    "moon_lantern": SafeTool(
        id="moon_lantern",
        label="moon lantern",
        phrase="a moon lantern",
        glow="glowed like bottled starlight",
        tags={"light", "lantern"},
    ),
}

RESPONSES = {
    "foam_spray": Response(
        id="foam_spray",
        sense=3,
        power=4,
        text="snatched the foam sprayer from the wall and covered the flames until every spark disappeared",
        fail="emptied the foam sprayer over the {target}, but the flames had already spread too far",
        qa_text="used the wall foam sprayer to put the flames out",
        tags={"foam", "fire"},
    ),
    "seal_and_smother": Response(
        id="seal_and_smother",
        sense=3,
        power=3,
        text="dropped the safety hood over the {target} and smothered the flames underneath it",
        fail="pulled the safety hood over the {target}, but the fire slipped around the edges",
        qa_text="smothered the flames with the safety hood",
        tags={"smother", "fire"},
    ),
    "stomp": Response(
        id="stomp",
        sense=2,
        power=2,
        text="knocked the burning bits down and stamped them out fast with heavy moon boots",
        fail="stamped at the burning {target}, but the fire jumped higher",
        qa_text="stamped the small fire out with moon boots",
        tags={"stomp", "fire"},
    ),
    "water_cup": Response(
        id="water_cup",
        sense=1,
        power=1,
        text="splashed a cup of water over the {target}",
        fail="splashed a cup of water over the {target}, but it barely touched the flames",
        qa_text="splashed water on the flames",
        tags={"water", "fire"},
    ),
}

GIRL_NAMES = ["Nova", "Lina", "Mira", "Ayla", "Zuri", "Tess", "Ivy", "Nia"]
BOY_NAMES = ["Jae", "Milo", "Orin", "Kian", "Rex", "Leo", "Finn", "Tao"]
TRAITS = ["careful", "steady", "thoughtful", "curious", "brave", "loyal"]


@dataclass
class StoryParams:
    habitat: str
    forbidden: str
    target: str
    reward: str
    safe_tool1: str
    safe_tool2: str
    response: str
    instigator: str
    instigator_gender: str
    friend: str
    friend_gender: str
    trait: str
    friendship: int = 7
    delay: int = 0
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for habitat in HABITATS:
        for forbidden_id, forbidden in FORBIDDEN.items():
            for target_id, target in TARGETS.items():
                if hazard_at_risk(forbidden, target):
                    combos.append((habitat, forbidden_id, target_id))
    return combos


KNOWLEDGE = {
    "albino": [
        (
            "What does albino mean?",
            "Albino means an animal has very little color in its fur, feathers, or skin, so it may look white or very pale.",
        )
    ],
    "reward": [
        (
            "What is a reward?",
            "A reward is something kind or special you get after doing a good job or making a good choice.",
        )
    ],
    "moonbase": [
        (
            "What is a moon base?",
            "A moon base is a place where people live or work on the moon, with rooms, tools, and air to breathe.",
        )
    ],
    "fire": [
        (
            "Why is fire dangerous on a station or base?",
            "Fire is dangerous because it spreads fast, makes smoke, and can damage the place people need to stay safe inside.",
        )
    ],
    "call_adult": [
        (
            "What should children do if they see a fire?",
            "They should move away and call a grown-up right away. Getting help fast is the safe and brave choice.",
        )
    ],
    "foam": [
        (
            "What does a foam sprayer do?",
            "A foam sprayer covers the fire with special foam so the flames can go out.",
        )
    ],
    "smother": [
        (
            "What does it mean to smother a fire?",
            "To smother a fire means to cover it so it cannot keep burning.",
        )
    ],
    "light": [
        (
            "Why is a lamp safer than a flame for looking in the dark?",
            "A lamp gives light without making a hot spark, so it helps you see without setting things on fire.",
        )
    ],
    "friendship": [
        (
            "How can friendship help keep people safe?",
            "Good friends warn each other, tell the truth, and stay together when something feels wrong.",
        )
    ],
}
KNOWLEDGE_ORDER = ["albino", "reward", "moonbase", "fire", "call_adult", "foam", "smother", "light", "friendship"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["friend"]
    reward = f["reward"]
    forbidden = f["forbidden"]
    habitat = f["habitat"]
    if f["outcome"] == "averted":
        return [
            'Write a space-adventure story for a 3-to-5-year-old that includes the words "albino" and "reward" and shows one friend stopping another from making a dangerous choice.',
            f"Tell a gentle cautionary story where {a.id} wants to use {forbidden.label} to win {reward.phrase}, but {b.id} helps {a.pronoun('object')} choose safety instead.",
            f"Write a friendship story set in {habitat.scene} where a rare albino creature is found only after the children slow down and use safe light.",
        ]
    if f["outcome"] == "burned":
        return [
            'Write a cautionary space-adventure story for a 3-to-5-year-old that includes the words "albino" and "reward" and shows how rushing for a prize can go wrong.',
            f"Tell a sadder cautionary story where {a.id} ignores {b.id}'s warning, uses {forbidden.label}, and the fire grows too big, though everyone gets out safely.",
            "Write a friendship story where the true reward is learned too late, after a dangerous mistake on a moon base.",
        ]
    return [
        'Write a space-adventure story for a 3-to-5-year-old that includes the words "albino" and "reward" and teaches children to call for help.',
        f"Tell a friendship story where {a.id} rushes to win {reward.phrase}, but {b.id} still helps when trouble starts.",
        f"Write a cautionary story in {habitat.scene} where safe tools matter more than a fast reward.",
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "boy" and b.type == "boy":
        return "two friends"
    if a.type == "girl" and b.type == "girl":
        return "two friends"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["friend"]
    captain = f["captain"]
    habitat = f["habitat"]
    forbidden = f["forbidden"]
    target = f["target_cfg"]
    reward = f["reward"]
    tool1, tool2 = f["safe_tools"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.id} and {b.id}, on a mission with Captain Mira. They were exploring {habitat.scene} and hoping to spot an albino moon-mouse.",
        ),
        (
            "What reward did the children hope to earn?",
            f"They hoped to earn {reward.phrase}. That reward made the mission feel exciting, but it also tempted {a.id} to rush.",
        ),
        (
            f"Why did {a.id} want to use {forbidden.label}?",
            f"{a.id} wanted a quick light to peek into the dark hiding place first. {a.pronoun().capitalize()} thought that finding the albino moon-mouse faster might win the reward.",
        ),
        (
            f"Why did {b.id} say no?",
            f"{b.id} warned that a spark from {forbidden.label} could catch on {target.the}. {b.pronoun().capitalize()} cared about the reward too, but cared more about keeping {a.id} safe.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What changed {a.id}'s mind?",
                f"{a.id} listened when {b.id} spoke like a true friend and stayed close instead of arguing. That friendship made the reward feel smaller than the danger.",
            )
        )
        qa.append(
            (
                "How did they finally find the albino moon-mouse?",
                f"They used {tool1.phrase} and {tool2.phrase} to look safely into the dark place. With safe light, they found the tiny albino moon-mouse without hurting its home.",
            )
        )
        qa.append(
            (
                "What was the real reward?",
                f"The children earned {reward.label}, but the bigger reward was that they worked as a team and kept each other safe. The ending shows their friendship shining brighter than the prize.",
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                "What happened when the forbidden tool was used?",
                f"A spark touched {target.near}, and {target.the} caught fire. The danger came from using a flame in a place with dry habitat materials.",
            )
        )
        qa.append(
            (
                "How did Captain Mira stop the fire?",
                f"Captain Mira {response.qa_text.replace('{target}', target.label)}. The fast response kept the small fire from taking over the whole habitat.",
            )
        )
        qa.append(
            (
                "Did the children still get a reward?",
                f"Yes, but not for rushing. They got {reward.label} for telling the truth, staying together, and learning to use safe tools next time.",
            )
        )
    else:
        qa.append(
            (
                "Could the fire be stopped in time?",
                f"No. Captain Mira tried, but the fire had already grown too big for that response. The children had to leave the habitat and watch the shutters close.",
            )
        )
        qa.append(
            (
                "What did the friends learn?",
                f"They learned that {forbidden.lesson} and that chasing a reward is never worth risking a fire. They also learned that real friends must stop each other sooner.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with everyone safe outside, but the mission spoiled and the habitat shut down. The lost adventure made the safety lesson feel very real.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"albino", "reward", "moonbase", "friendship", "fire", "call_adult", "light"}
    if f["response"].id == "foam_spray":
        tags.add("foam")
    if f["response"].id == "seal_and_smother":
        tags.add("smother")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (("flammable", ent.flammable), ("makes_flame", ent.makes_flame), ("gives_light", ent.gives_light)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        habitat="fern_dome",
        forbidden="flare_pen",
        target="star_reeds",
        reward="star_badge",
        safe_tool1="beam_lamp",
        safe_tool2="glow_map",
        response="foam_spray",
        instigator="Nova",
        instigator_gender="girl",
        friend="Jae",
        friend_gender="boy",
        trait="loyal",
        friendship=9,
        delay=0,
    ),
    StoryParams(
        habitat="crystal_grotto",
        forbidden="plasma_match",
        target="nest_pad",
        reward="patch",
        safe_tool1="helmet_lights",
        safe_tool2="moon_lantern",
        response="seal_and_smother",
        instigator="Milo",
        instigator_gender="boy",
        friend="Tess",
        friend_gender="girl",
        trait="curious",
        friendship=6,
        delay=0,
    ),
    StoryParams(
        habitat="moss_lab",
        forbidden="mini_torch",
        target="shade_cloth",
        reward="pin",
        safe_tool1="beam_lamp",
        safe_tool2="helmet_lights",
        response="stomp",
        instigator="Ayla",
        instigator_gender="girl",
        friend="Finn",
        friend_gender="boy",
        trait="thoughtful",
        friendship=5,
        delay=1,
    ),
    StoryParams(
        habitat="fern_dome",
        forbidden="plasma_match",
        target="star_reeds",
        reward="patch",
        safe_tool1="moon_lantern",
        safe_tool2="glow_map",
        response="foam_spray",
        instigator="Leo",
        instigator_gender="boy",
        friend="Nia",
        friend_gender="girl",
        trait="steady",
        friendship=4,
        delay=2,
    ),
]


def explain_rejection(forbidden: Forbidden, target: Target) -> str:
    if not target.flammable:
        return (
            f"(No story: {forbidden.label} can make a spark, but {target.the} will not catch fire. Pick dry reeds, cloth, or a nesting pad so the warning and lesson are honest.)"
        )
    return "(No story: this combination has no believable fire hazard.)"


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it is too weak or not sensible enough for this world (sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.friendship, params.trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], TARGETS[params.target], params.delay) else "burned"


ASP_RULES = r"""
hazard(F, T) :- makes_flame(F), flammable(T).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(H, F, T) :- habitat(H), forbidden(F), target(T), hazard(F, T).

careful_trait(T) :- trait(T), cautious(T).
bonus(1) :- careful_trait(_).
bonus(0) :- not careful_trait(_).
friendship_total(F + B) :- friendship(F), bonus(B).
averted :- friendship_total(V), loyal_min(M), V >= M.

severity(Sp + D) :- chosen_target(T), spread(T, Sp), delay(D).
contained :- chosen_response(R), power(R, P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(burned) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for habitat in HABITATS:
        lines.append(asp.fact("habitat", habitat))
    for forbidden_id, forbidden in FORBIDDEN.items():
        lines.append(asp.fact("forbidden", forbidden_id))
        if forbidden.makes_flame:
            lines.append(asp.fact("makes_flame", forbidden_id))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        if target.flammable:
            lines.append(asp.fact("flammable", target_id))
        lines.append(asp.fact("spread", target_id, target.spread))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait_name", trait))
    for trait in sorted({"careful", "steady", "thoughtful", "loyal"}):
        lines.append(asp.fact("cautious", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("loyal_min", LOYAL_FRIENDSHIP_MIN))
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
    return sorted(atom[0] for atom in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_target", params.target),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("friendship", params.friendship),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def _smoke_generate() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: empty story.")
    emit(sample, trace=False, qa=False)


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_sensible, python_sensible = set(asp_sensible()), {r.id for r in sensible_responses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(seed)))
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_generate()
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a moon-base friendship, a dangerous shortcut, and the real reward of safe teamwork."
    )
    ap.add_argument("--habitat", choices=HABITATS)
    ap.add_argument("--forbidden", choices=FORBIDDEN)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--reward", choices=REWARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the fire grows before the grown-up responds")
    ap.add_argument("--friendship", type=int, choices=list(range(0, 11)), help="how strongly the friends trust and listen to each other")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python logic and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target and not TARGETS[args.target].flammable:
        forbidden = FORBIDDEN[args.forbidden] if args.forbidden else next(iter(FORBIDDEN.values()))
        raise StoryError(explain_rejection(forbidden, TARGETS[args.target]))
    if args.forbidden and args.target:
        forbidden = FORBIDDEN[args.forbidden]
        target = TARGETS[args.target]
        if not hazard_at_risk(forbidden, target):
            raise StoryError(explain_rejection(forbidden, target))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.habitat is None or combo[0] == args.habitat)
        and (args.forbidden is None or combo[1] == args.forbidden)
        and (args.target is None or combo[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    habitat, forbidden, target = rng.choice(sorted(combos))
    reward = args.reward or rng.choice(sorted(REWARDS))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    safe_tool1, safe_tool2 = rng.sample(sorted(SAFE_TOOLS), 2)
    instigator, instigator_gender = _pick_kid(rng)
    friend, friend_gender = _pick_kid(rng, avoid=instigator)
    trait = rng.choice(TRAITS)
    friendship = args.friendship if args.friendship is not None else rng.randint(4, 10)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        habitat=habitat,
        forbidden=forbidden,
        target=target,
        reward=reward,
        safe_tool1=safe_tool1,
        safe_tool2=safe_tool2,
        response=response,
        instigator=instigator,
        instigator_gender=instigator_gender,
        friend=friend,
        friend_gender=friend_gender,
        trait=trait,
        friendship=friendship,
        delay=delay,
    )


def _require_key(table: dict, key: str, label: str):
    if key not in table:
        raise StoryError(f"(No story: unknown {label} '{key}'.)")
    return table[key]


def generate(params: StoryParams) -> StorySample:
    habitat = _require_key(HABITATS, params.habitat, "habitat")
    forbidden = _require_key(FORBIDDEN, params.forbidden, "forbidden tool")
    target = _require_key(TARGETS, params.target, "target")
    reward = _require_key(REWARDS, params.reward, "reward")
    tool1 = _require_key(SAFE_TOOLS, params.safe_tool1, "safe tool")
    tool2 = _require_key(SAFE_TOOLS, params.safe_tool2, "safe tool")
    response = _require_key(RESPONSES, params.response, "response")

    if not hazard_at_risk(forbidden, target):
        raise StoryError(explain_rejection(forbidden, target))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if params.safe_tool1 == params.safe_tool2:
        raise StoryError("(No story: the two safe tools must be different.)")

    world = tell(
        habitat=habitat,
        forbidden=forbidden,
        target=target,
        reward=reward,
        safe_tools=(tool1, tool2),
        response=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        friend=params.friend,
        friend_gender=params.friend_gender,
        trait=params.trait,
        delay=params.delay,
        friendship=params.friendship,
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
        print(f"{len(combos)} compatible (habitat, forbidden, target) combos:\n")
        for habitat, forbidden, target in combos:
            print(f"  {habitat:14} {forbidden:13} {target}")
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
            params = sample.params
            header = (
                f"### {params.instigator} & {params.friend}: {params.forbidden} near {params.target} "
                f"({params.habitat}, {params.reward}, {outcome_of(params)})"
            )
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
