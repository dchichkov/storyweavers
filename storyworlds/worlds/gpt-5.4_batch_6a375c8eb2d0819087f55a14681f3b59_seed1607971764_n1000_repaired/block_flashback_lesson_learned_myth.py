#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/block_flashback_lesson_learned_myth.py
=================================================================

A standalone storyworld for a tiny mythic domain: a child blocks living water
for a playful reason, the land begins to suffer, an elder's flashback to an old
myth explains the danger, and the child learns to let water travel.

This world is intentionally narrow and state-driven. The prose follows simulated
changes in flowing water, thirsty plants, frightened creatures, guilt, memory,
and repair.

Run it
------
    python storyworlds/worlds/gpt-5.4/block_flashback_lesson_learned_myth.py
    python storyworlds/worlds/gpt-5.4/block_flashback_lesson_learned_myth.py --waterway spring --blocker stone_block
    python storyworlds/worlds/gpt-5.4/block_flashback_lesson_learned_myth.py --waterway river
    python storyworlds/worlds/gpt-5.4/block_flashback_lesson_learned_myth.py --remedy poke_stick
    python storyworlds/worlds/gpt-5.4/block_flashback_lesson_learned_myth.py --all
    python storyworlds/worlds/gpt-5.4/block_flashback_lesson_learned_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/block_flashback_lesson_learned_myth.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother", "priestess"}
        male = {"boy", "man", "grandfather", "shepherd"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Waterway:
    id: str
    label: str
    phrase: str
    downstream: str
    spirit: str
    scene: str
    sensitivity: int
    min_block: int
    flashback_cause: str
    lesson: str
    tags: set[str] = field(default_factory=set)
    blockable: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Blocker:
    id: str
    label: str
    phrase: str
    material: str
    heaviness: int
    move_verb: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Desire:
    id: str
    wish: str
    image: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class ElderCfg:
    id: str
    label: str
    type: str
    entrance: str
    memory_intro: str
    blessing: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Remedy:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_blocked_flow(world: World) -> list[str]:
    water = world.get("water")
    grove = world.get("grove")
    if water.meters["blocked"] < THRESHOLD:
        return []
    sig = ("blocked_flow",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    water.meters["flow"] = 0.0
    grove.meters["thirst"] += 1
    world.get("creatures").memes["alarm"] += 1
    world.get("child").memes["wonder"] += 1
    return []


def _r_thirst_droop(world: World) -> list[str]:
    grove = world.get("grove")
    if grove.meters["thirst"] < THRESHOLD:
        return []
    sig = ("droop",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    grove.meters["droop"] += 1
    world.get("child").memes["unease"] += 1
    return []


def _r_restore(world: World) -> list[str]:
    water = world.get("water")
    if water.meters["opened"] < THRESHOLD:
        return []
    sig = ("restore",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    water.meters["flow"] = 1.0
    water.meters["blocked"] = 0.0
    grove = world.get("grove")
    grove.meters["thirst"] = 0.0
    grove.meters["droop"] = 0.0
    world.get("creatures").memes["alarm"] = 0.0
    world.get("child").memes["relief"] += 1
    world.get("child").memes["wisdom"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="blocked_flow", tag="physical", apply=_r_blocked_flow),
    Rule(name="thirst_droop", tag="physical", apply=_r_thirst_droop),
    Rule(name="restore", tag="physical", apply=_r_restore),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def can_block(waterway: Waterway, blocker: Blocker) -> bool:
    return waterway.blockable and blocker.heaviness >= waterway.min_block


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def severity_of(waterway: Waterway, delay: int) -> int:
    return waterway.sensitivity + delay


def restored_by(remedy: Remedy, waterway: Waterway, delay: int) -> bool:
    return remedy.power >= severity_of(waterway, delay)


def predict_harm(world: World) -> dict:
    sim = world.copy()
    sim.get("water").meters["blocked"] += 1
    propagate(sim, narrate=False)
    grove = sim.get("grove")
    return {
        "thirst": grove.meters["thirst"],
        "droop": grove.meters["droop"],
        "alarm": sim.get("creatures").memes["alarm"],
    }


def introduce(world: World, child: Entity, waterway: Waterway, desire: Desire) -> None:
    child.memes["joy"] += 1
    world.say(
        f"In the old days, when hills still listened, {child.id} went to {waterway.phrase}. "
        f"{waterway.scene}"
    )
    world.say(
        f"{child.pronoun().capitalize()} loved that place and wanted to {desire.wish}. "
        f"To a child, {desire.image} looked like a game the morning itself had offered."
    )


def block_water(world: World, child: Entity, blocker: Blocker, waterway: Waterway) -> None:
    water = world.get("water")
    water.meters["blocked"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So {child.id} {blocker.move_verb} {blocker.phrase} across the mouth of the "
        f"{waterway.label} to make the water linger. The little stream curled against "
        f"the {blocker.label} and slowed to a shining hush."
    )


def signs_of_harm(world: World, child: Entity, waterway: Waterway) -> None:
    grove = world.get("grove")
    creatures = world.get("creatures")
    world.say(
        f"But before the sun had climbed very high, the path below grew strangely quiet. "
        f"The water that should have run toward {waterway.downstream} had thinned."
    )
    if creatures.memes["alarm"] >= THRESHOLD:
        world.say(
            "Dragonflies skimmed in nervous circles, and the frogs fell still as if they were listening for a song that had stopped."
        )
    if grove.meters["droop"] >= THRESHOLD:
        world.say(
            f"In {waterway.downstream}, leaves began to bend at the edges. {child.id} felt a cold pinch of worry, because the thirsty place seemed to be looking back at {child.pronoun('object')}."
        )


def flashback(world: World, child: Entity, elder: Entity, waterway: Waterway) -> None:
    pred = predict_harm(world)
    world.facts["predicted_thirst"] = pred["thirst"]
    world.facts["predicted_droop"] = pred["droop"]
    world.facts["predicted_alarm"] = pred["alarm"]
    child.memes["memory"] += 1
    world.say(
        f"Then {elder.id} came along {elder.attrs['entrance']}. Seeing the still water, "
        f"{elder.pronoun()} stopped and whispered, {elder.attrs['memory_intro']}"
    )
    world.say(
        f"In a flashback that seemed older than dust, {child.id} remembered the tale: "
        f"long ago, {waterway.flashback_cause}. The people had begged the stream to stay, "
        f"but the stream had answered by leaving them with cracked bowls, silent reeds, and a lesson they learned too late."
    )
    world.say(
        f'"Living water is not a toy to keep," {elder.id} said. "{waterway.lesson}"'
    )
    child.memes["guilt"] += 1


def choose_repair(world: World, child: Entity, remedy: Remedy, waterway: Waterway, delay: int) -> None:
    if delay == 0:
        world.say(
            f"{child.id} did not argue. At once {child.pronoun()} knelt by the {waterway.label}, ready to mend the wrong."
        )
    elif delay == 1:
        world.say(
            f"For one uneasy moment {child.id} stared at the trapped water, wishing the game and the warning could both be true. Then {child.pronoun()} bowed {child.pronoun('possessive')} head and chose to mend the wrong."
        )
    else:
        world.say(
            f"{child.id} waited too long, hoping the trouble would somehow untie itself. By the time {child.pronoun()} moved, the quiet below had turned heavy and sad."
        )
    world.facts["repair_started"] = True
    world.facts["repair_method"] = remedy.id


def repair_success(world: World, child: Entity, elder: Entity, remedy: Remedy, waterway: Waterway) -> None:
    world.get("water").meters["opened"] += 1
    propagate(world, narrate=False)
    body = remedy.text.replace("{blocker}", world.facts["blocker"].label).replace("{waterway}", waterway.label)
    world.say(
        f"Together they {body}. At once the {waterway.label} laughed free again and went singing toward {waterway.downstream}."
    )
    world.say(
        f"The leaves lifted. The frogs began their small drums again. Even the light on the stones looked less worried."
    )
    world.say(
        f"{elder.id} touched {child.id}'s hair and gave {elder.pronoun('possessive')} blessing: {elder.attrs['blessing']}. "
        f"{child.id} watched the water hurry on and understood that its journey was part of its gift."
    )


def repair_fail(world: World, child: Entity, elder: Entity, remedy: Remedy, waterway: Waterway) -> None:
    body = remedy.fail.replace("{blocker}", world.facts["blocker"].label).replace("{waterway}", waterway.label)
    world.get("child").memes["sorrow"] += 1
    world.say(
        f"They {body}, but only a thin silver thread slipped past. It was not enough to wake {waterway.downstream} before evening."
    )
    world.say(
        f"That night the child sat beside {waterway.phrase} with {elder.id} and listened to the hard quiet below. "
        f"Before dawn they returned with stronger hands and opened the way at last, yet some petals had already fallen."
    )
    world.say(
        f"From then on, whenever {child.id} saw water running, {child.pronoun()} remembered that a small selfish block can cast a long shadow."
    )


def ending_lesson(world: World, child: Entity, waterway: Waterway, outcome: str) -> None:
    if outcome == "restored":
        world.say(
            f"After that day, {child.id} still played by {waterway.phrase}, but never by stopping it. "
            f"{child.pronoun().capitalize()} floated leaves on the current and let them go, smiling as they followed their own bright path."
        )
    else:
        world.say(
            f"After that day, {child.id} never tried to keep a stream for play again. "
            f"{child.pronoun().capitalize()} learned that what moves for many hearts should not be held for one pair of hands."
        )


def tell(
    waterway: Waterway,
    blocker: Blocker,
    desire: Desire,
    elder_cfg: ElderCfg,
    remedy: Remedy,
    *,
    child_name: str = "Iria",
    child_gender: str = "girl",
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", label=child_name))
    elder = world.add(
        Entity(
            id=elder_cfg.label.capitalize(),
            kind="character",
            type=elder_cfg.type,
            role="elder",
            label=elder_cfg.label,
            attrs={
                "entrance": elder_cfg.entrance,
                "memory_intro": elder_cfg.memory_intro,
                "blessing": elder_cfg.blessing,
            },
        )
    )
    water = world.add(Entity(id="water", type="waterway", label=waterway.label))
    grove = world.add(Entity(id="grove", type="grove", label=waterway.downstream))
    creatures = world.add(Entity(id="creatures", type="creatures", label="the small creatures"))

    water.meters["flow"] = 1.0
    water.meters["blocked"] = 0.0
    water.meters["opened"] = 0.0
    grove.meters["thirst"] = 0.0
    grove.meters["droop"] = 0.0
    creatures.memes["alarm"] = 0.0
    child.memes["joy"] = 0.0
    child.memes["wonder"] = 0.0
    child.memes["unease"] = 0.0
    child.memes["memory"] = 0.0
    child.memes["guilt"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["wisdom"] = 0.0
    child.memes["sorrow"] = 0.0

    world.facts.update(
        child=child,
        elder=elder,
        waterway=waterway,
        blocker=blocker,
        desire=desire,
        remedy=remedy,
        delay=delay,
    )

    introduce(world, child, waterway, desire)
    world.para()
    block_water(world, child, blocker, waterway)
    signs_of_harm(world, child, waterway)
    world.para()
    flashback(world, child, elder, waterway)
    choose_repair(world, child, remedy, waterway, delay)

    outcome = "restored" if restored_by(remedy, waterway, delay) else "withered"
    world.para()
    if outcome == "restored":
        repair_success(world, child, elder, remedy, waterway)
    else:
        repair_fail(world, child, elder, remedy, waterway)
    world.para()
    ending_lesson(world, child, waterway, outcome)

    world.facts.update(
        outcome=outcome,
        harmed=world.get("grove").meters["droop"] >= THRESHOLD or outcome == "withered",
        remembered=child.memes["memory"] >= THRESHOLD,
        learned=True,
        severity=severity_of(waterway, delay),
    )
    return world


WATERWAYS = {
    "spring": Waterway(
        id="spring",
        label="spring",
        phrase="the lion-faced spring under the hill",
        downstream="the fig terraces",
        spirit="the Spring Mother",
        scene="Bronze moss shone around it, and the water came clear as a spoken promise.",
        sensitivity=1,
        min_block=1,
        flashback_cause="a proud prince had sealed a spring with carved stone so he could admire his own reflection all day",
        lesson="Water stays holy by moving from one thirst to the next",
        tags={"spring", "water", "figs"},
    ),
    "brook": Waterway(
        id="brook",
        label="brook",
        phrase="the narrow brook of reed-song",
        downstream="the barley field",
        spirit="the Reed Singer",
        scene="Its banks smelled of mint, and bright fish flickered in the shadows.",
        sensitivity=2,
        min_block=2,
        flashback_cause="a greedy miller had wedged a heavy block into the brook to fatten only his own wheel",
        lesson="When one hand hoards the stream, many mouths inherit dust",
        tags={"brook", "water", "barley"},
    ),
    "rill": Waterway(
        id="rill",
        label="rill",
        phrase="the silver rill that climbed down the temple steps",
        downstream="the laurel court",
        spirit="the Laurel Nymph",
        scene="It sang over white stone, and every step of the temple gleamed where it passed.",
        sensitivity=2,
        min_block=2,
        flashback_cause="an old keeper had shut the sacred rill for a feast, and the temple laurels shed their leaves before dawn",
        lesson="A gift offered to the gods must not be trapped for pride or play",
        tags={"rill", "water", "laurel"},
    ),
    "river": Waterway(
        id="river",
        label="river",
        phrase="the wide river below the cypress ridge",
        downstream="the fishing cove",
        spirit="the River Father",
        scene="It rolled broad and strong, carrying whole clouds upon its back.",
        sensitivity=3,
        min_block=4,
        flashback_cause="a king had tried to imprison a river with walls of treasure, and the river answered by breaking the walls and washing his glory away",
        lesson="No single pair of arms may command what was made to flow beyond them",
        tags={"river", "water", "fish"},
    ),
}

BLOCKERS = {
    "stone_block": Blocker(
        id="stone_block",
        label="block",
        phrase="a square stone block",
        material="stone",
        heaviness=3,
        move_verb="rolled",
        tags={"block", "stone"},
    ),
    "clay_block": Blocker(
        id="clay_block",
        label="clay block",
        phrase="a sun-baked clay block",
        material="clay",
        heaviness=2,
        move_verb="dragged",
        tags={"block", "clay"},
    ),
    "cedar_block": Blocker(
        id="cedar_block",
        label="cedar block",
        phrase="a carved cedar block",
        material="wood",
        heaviness=1,
        move_verb="pushed",
        tags={"block", "wood"},
    ),
}

DESIRES = {
    "mirror_pool": Desire(
        id="mirror_pool",
        wish="make a still mirror pool and watch the clouds sit inside it",
        image="a round patch of trapped sky",
        tags={"play", "water"},
    ),
    "leaf_boats": Desire(
        id="leaf_boats",
        wish="keep the water shallow enough for leaf boats to circle in one place",
        image="tiny green boats spinning like dancers",
        tags={"play", "boats"},
    ),
    "pebbles": Desire(
        id="pebbles",
        wish="hold back the stream and gather the bright pebbles from its bed",
        image="hidden stones winking like little moons",
        tags={"play", "pebbles"},
    ),
}

ELDERS = {
    "grandmother": ElderCfg(
        id="grandmother",
        label="grandmother",
        type="grandmother",
        entrance="with a basket of herbs on her arm",
        memory_intro='"Ah," and her voice sounded as old as well water, "I have heard this quiet before."',
        blessing='"May your hands remember how to open what others need."',
        tags={"elder", "grandmother"},
    ),
    "shepherd": ElderCfg(
        id="shepherd",
        label="shepherd",
        type="shepherd",
        entrance="down from the hillside with the bells of sheep around him",
        memory_intro='"Child," and his voice was low as a reed flute, "there is an old sorrow in this silence."',
        blessing='"May you grow into someone who shares every good road and every good stream."',
        tags={"elder", "shepherd"},
    ),
    "priestess": ElderCfg(
        id="priestess",
        label="priestess",
        type="priestess",
        entrance="from the temple shade with laurel leaves in her hands",
        memory_intro='"Listen," she murmured, "the stones themselves are remembering."',
        blessing='"May wisdom reach you as quickly as water reaches roots."',
        tags={"elder", "priestess"},
    ),
}

REMEDIES = {
    "lift_block": Remedy(
        id="lift_block",
        sense=3,
        power=2,
        text="lifted the {blocker} away from the {waterway}",
        fail="tried to lift the {blocker} from the {waterway}",
        qa_text="lifted the block away so the water could run again",
        tags={"repair", "lifting"},
    ),
    "lever_branch": Remedy(
        id="lever_branch",
        sense=2,
        power=3,
        text="used a fallen branch as a lever and pried the {blocker} free from the {waterway}",
        fail="worked a fallen branch under the {blocker} at the {waterway}",
        qa_text="used a branch as a lever to pry the block free",
        tags={"repair", "lever"},
    ),
    "poke_stick": Remedy(
        id="poke_stick",
        sense=1,
        power=1,
        text="poked until the {blocker} shifted aside",
        fail="poked at the {blocker} with a thin stick near the {waterway}",
        qa_text="poked at the block with a thin stick",
        tags={"repair"},
    ),
}

GIRL_NAMES = ["Iria", "Nysa", "Dora", "Seli", "Mara", "Thaleia"]
BOY_NAMES = ["Timon", "Lykos", "Panos", "Damon", "Iason", "Nereus"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    if not sensible_remedies():
        return combos
    for wid, waterway in WATERWAYS.items():
        for bid, blocker in BLOCKERS.items():
            if can_block(waterway, blocker):
                combos.append((wid, bid))
    return combos


@dataclass
class StoryParams:
    waterway: str
    blocker: str
    desire: str
    elder: str
    remedy: str
    child_name: str
    child_gender: str
    delay: int = 0
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "spring": [
        (
            "What is a spring?",
            "A spring is water that rises from the ground and begins a stream. People and plants may depend on it far below where it first appears.",
        )
    ],
    "brook": [
        (
            "What is a brook?",
            "A brook is a small stream that keeps moving along a narrow path. Even a small brook can help fields, animals, and people.",
        )
    ],
    "rill": [
        (
            "What is a rill?",
            "A rill is a very small stream, often a thin ribbon of running water. Small streams still matter because roots and creatures may rely on them.",
        )
    ],
    "river": [
        (
            "Why is a river hard to stop?",
            "A river carries a great deal of moving water, so it pushes with strong force. Small tools or one person alone usually cannot control it safely.",
        )
    ],
    "block": [
        (
            "What does it mean to block water?",
            "To block water is to put something in its path so it cannot flow normally. When water is stopped, places farther along may not get what they need.",
        )
    ],
    "figs": [
        (
            "Why do fig trees need water?",
            "Fig trees need water in their roots to keep their leaves and fruit healthy. If the soil dries too much, the leaves droop and the fruit can suffer.",
        )
    ],
    "barley": [
        (
            "Why does barley need water?",
            "Barley is a grain plant, and grain plants need steady water to grow tall and make seeds. A thirsty field turns weak very quickly in the sun.",
        )
    ],
    "laurel": [
        (
            "Why do leaves droop when a plant is thirsty?",
            "Leaves droop when a plant does not have enough water to keep them firm. The plant is trying to save what little water it still has.",
        )
    ],
    "fish": [
        (
            "Why do fish need flowing water?",
            "Flowing water brings fresh air and food through the stream. When the water stops or becomes too shallow, fish can struggle.",
        )
    ],
    "lifting": [
        (
            "Why is removing the blockage a good fix?",
            "Removing the blockage lets the water travel the way it was already meant to travel. That helps the thirsty places downstream right away.",
        )
    ],
    "lever": [
        (
            "What does a lever do?",
            "A lever helps move something heavy by using a long stick or bar. It lets a person use smart force instead of only muscle.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "spring",
    "brook",
    "rill",
    "river",
    "block",
    "figs",
    "barley",
    "laurel",
    "fish",
    "lifting",
    "lever",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    waterway = f["waterway"]
    blocker = f["blocker"]
    desire = f["desire"]
    outcome = f["outcome"]
    if outcome == "restored":
        return [
            f'Write a short myth for a 3-to-5-year-old that includes the word "{blocker.label}" and a flashback.',
            f"Tell a mythic story where {child.id} blocks a {waterway.label} for play, remembers an old warning, and learns to let water travel on.",
            f"Write a gentle myth with a lesson learned: a child tries to {desire.wish}, harms a place downstream, then repairs the wrong and ends wiser.",
        ]
    return [
        f'Write a short myth for a 3-to-5-year-old that includes the word "{blocker.label}" and a flashback.',
        f"Tell a mythic cautionary story where {child.id} blocks a {waterway.label}, learns the old lesson too slowly, and sees why stopping shared water is selfish.",
        f"Write a myth-style story with a lesson learned: a child traps living water for play, hears an elder's old tale, and never makes that mistake again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    waterway = f["waterway"]
    blocker = f["blocker"]
    desire = f["desire"]
    remedy = f["remedy"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child who played by {waterway.phrase}, and {elder.id}, the elder who helped {child.pronoun('object')} understand what was wrong.",
        ),
        (
            f"Why did {child.id} put the {blocker.label} in the {waterway.label}?",
            f"{child.id} wanted to {desire.wish}. At first the still water looked beautiful, so the game seemed harmless.",
        ),
        (
            f"What changed after the {waterway.label} was blocked?",
            f"The water stopped reaching {waterway.downstream}, and the place below began to thirst. The quiet frogs and drooping leaves showed that the blocked stream was hurting more than one child could see.",
        ),
        (
            "What was the flashback about?",
            f"The flashback was about an old tale in which someone long ago stopped sacred water for pride or greed and brought trouble to others. It taught that water should keep moving from one thirsty place to the next.",
        ),
    ]
    if outcome == "restored":
        qa.append(
            (
                f"How did {child.id} fix the problem?",
                f"{child.id} and {elder.id} {remedy.qa_text}. That let the water run back toward {waterway.downstream}, so the thirsty place could recover.",
            )
        )
        qa.append(
            (
                f"What lesson did {child.id} learn?",
                f"{child.id} learned that shared water should not be kept for one person's game. {child.pronoun().capitalize()} understood this because the land below suffered as soon as the stream was stopped.",
            )
        )
    else:
        qa.append(
            (
                f"Did the first repair work in time?",
                f"No. They tried to mend the problem, but the water returned too slowly to help {waterway.downstream} before evening. That made the lesson feel heavier, because some harm had already reached the leaves and flowers.",
            )
        )
        qa.append(
            (
                f"What lesson did {child.id} learn?",
                f"{child.id} learned that even a small selfish block can hurt many living things. The old story became real when the quiet below the stream turned into true loss.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["waterway"].tags) | set(f["blocker"].tags)
    if f["outcome"] == "restored":
        tags |= set(f["remedy"].tags)
    if f["waterway"].id == "river":
        tags.add("fish")
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
        parts = []
        if e.role:
            parts.append(f"role={e.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.attrs:
            parts.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        waterway="spring",
        blocker="cedar_block",
        desire="mirror_pool",
        elder="grandmother",
        remedy="lift_block",
        child_name="Iria",
        child_gender="girl",
        delay=0,
    ),
    StoryParams(
        waterway="brook",
        blocker="stone_block",
        desire="leaf_boats",
        elder="shepherd",
        remedy="lever_branch",
        child_name="Timon",
        child_gender="boy",
        delay=0,
    ),
    StoryParams(
        waterway="rill",
        blocker="clay_block",
        desire="pebbles",
        elder="priestess",
        remedy="lift_block",
        child_name="Mara",
        child_gender="girl",
        delay=1,
    ),
    StoryParams(
        waterway="river",
        blocker="stone_block",
        desire="mirror_pool",
        elder="shepherd",
        remedy="lever_branch",
        child_name="Damon",
        child_gender="boy",
        delay=1,
    ),
    StoryParams(
        waterway="brook",
        blocker="clay_block",
        desire="pebbles",
        elder="grandmother",
        remedy="lift_block",
        child_name="Nysa",
        child_gender="girl",
        delay=2,
    ),
]


def explain_rejection(waterway: Waterway, blocker: Blocker) -> str:
    if not waterway.blockable:
        return f"(No story: the {waterway.label} is not a waterway this world allows a child to block.)"
    return (
        f"(No story: {blocker.phrase} is too light to truly stop the {waterway.label}. "
        f"This world only tells stories where the block can actually change the water's flow.)"
    )


def explain_remedy(remedy_id: str) -> str:
    remedy = REMEDIES[remedy_id]
    better = ", ".join(sorted(r.id for r in sensible_remedies()))
    return (
        f"(Refusing remedy '{remedy_id}': it is too weak or foolish for this world "
        f"(sense={remedy.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "restored" if restored_by(REMEDIES[params.remedy], WATERWAYS[params.waterway], params.delay) else "withered"


ASP_RULES = r"""
valid(W, B) :- waterway(W), blocker(B), blockable(W), heaviness(B, H), min_block(W, M), H >= M.

sensible(R) :- remedy(R), sense(R, S), sense_min(M), S >= M.

severity(V) :- chosen_waterway(W), sensitivity(W, S), delay(D), V = S + D.
restored :- chosen_remedy(R), power(R, P), severity(V), P >= V.
outcome(restored) :- restored.
outcome(withered) :- not restored.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for wid, waterway in WATERWAYS.items():
        lines.append(asp.fact("waterway", wid))
        if waterway.blockable:
            lines.append(asp.fact("blockable", wid))
        lines.append(asp.fact("sensitivity", wid, waterway.sensitivity))
        lines.append(asp.fact("min_block", wid, waterway.min_block))
    for bid, blocker in BLOCKERS.items():
        lines.append(asp.fact("blocker", bid))
        lines.append(asp.fact("heaviness", bid, blocker.heaviness))
    for rid, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("sense", rid, remedy.sense))
        lines.append(asp.fact("power", rid, remedy.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_remedies() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_waterway", params.waterway),
            asp.fact("chosen_remedy", params.remedy),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {r.id for r in sensible_remedies()}
    asp_sensible = set(asp_sensible_remedies())
    if py_sensible == asp_sensible:
        print(f"OK: sensible remedies match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible remedies: clingo={sorted(asp_sensible)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    for s in range(120):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a mythic child blocks a stream, hears an old warning, and learns a lesson."
    )
    ap.add_argument("--waterway", choices=WATERWAYS)
    ap.add_argument("--blocker", choices=BLOCKERS)
    ap.add_argument("--desire", choices=DESIRES)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (waterway, blocker) pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.remedy and REMEDIES[args.remedy].sense < SENSE_MIN:
        raise StoryError(explain_remedy(args.remedy))
    if args.waterway and args.blocker:
        if not can_block(WATERWAYS[args.waterway], BLOCKERS[args.blocker]):
            raise StoryError(explain_rejection(WATERWAYS[args.waterway], BLOCKERS[args.blocker]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.waterway is None or combo[0] == args.waterway)
        and (args.blocker is None or combo[1] == args.blocker)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    waterway, blocker = rng.choice(sorted(combos))
    desire = args.desire or rng.choice(sorted(DESIRES.keys()))
    elder = args.elder or rng.choice(sorted(ELDERS.keys()))
    remedy = args.remedy or rng.choice(sorted(r.id for r in sensible_remedies()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        waterway=waterway,
        blocker=blocker,
        desire=desire,
        elder=elder,
        remedy=remedy,
        child_name=child_name,
        child_gender=child_gender,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.waterway not in WATERWAYS:
        raise StoryError(f"(Unknown waterway: {params.waterway})")
    if params.blocker not in BLOCKERS:
        raise StoryError(f"(Unknown blocker: {params.blocker})")
    if params.desire not in DESIRES:
        raise StoryError(f"(Unknown desire: {params.desire})")
    if params.elder not in ELDERS:
        raise StoryError(f"(Unknown elder: {params.elder})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")
    if params.remedy in REMEDIES and REMEDIES[params.remedy].sense < SENSE_MIN:
        raise StoryError(explain_remedy(params.remedy))
    if not can_block(WATERWAYS[params.waterway], BLOCKERS[params.blocker]):
        raise StoryError(explain_rejection(WATERWAYS[params.waterway], BLOCKERS[params.blocker]))

    world = tell(
        WATERWAYS[params.waterway],
        BLOCKERS[params.blocker],
        DESIRES[params.desire],
        ELDERS[params.elder],
        REMEDIES[params.remedy],
        child_name=params.child_name,
        child_gender=params.child_gender,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible remedies: {', '.join(asp_sensible_remedies())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (waterway, blocker) combos:\n")
        for waterway, blocker in combos:
            print(f"  {waterway:8} {blocker}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.blocker} at {p.waterway} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
