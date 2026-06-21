#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/consult_twist_space_adventure.py
===========================================================

A standalone story world for a small space-adventure tale built around one
important choice: when something strange appears outside the ship, should the
children rush first or consult the ship's computer and a grown-up first?

This world models a short story with a clear beginning, middle turn, and ending:
two children on a family shuttle spot a mysterious object drifting in space.
One child wants to act right away. The wiser move is to consult the ship's
computer, which reveals a twist: the scary or treasure-like thing is really a
lost helpful object that needs rescue. A grown-up then uses the right tool to
bring it safely aboard -- or, if the drift is too strong for the chosen method,
the children must watch it float away and learn to ask before acting.

Run it
------
    python storyworlds/worlds/gpt-5.4/consult_twist_space_adventure.py
    python storyworlds/worlds/gpt-5.4/consult_twist_space_adventure.py --sector ring_lane --mystery mail_drone
    python storyworlds/worlds/gpt-5.4/consult_twist_space_adventure.py --response cargo_net
    python storyworlds/worlds/gpt-5.4/consult_twist_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/consult_twist_space_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/consult_twist_space_adventure.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/consult_twist_space_adventure.py --json
    python storyworlds/worlds/gpt-5.4/consult_twist_space_adventure.py --verify
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Sector:
    id: str
    name: str
    window_view: str
    glow_line: str
    risk: int
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
class Mystery:
    id: str
    first_shape: str
    first_guess: str
    true_name: str
    true_phrase: str
    purpose: str
    material: str
    chirp: str
    ending_image: str
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
class Response:
    id: str
    sense: int
    power: int
    materials: set[str]
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
    def __init__(self, sector: Sector) -> None:
        self.sector = sector
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
        clone = World(self.sector)
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


def _r_drift(world: World) -> list[str]:
    out: list[str] = []
    thing = world.entities.get("mystery")
    space = world.entities.get("space")
    if thing is None or space is None:
        return out
    if thing.meters["drifting"] < THRESHOLD:
        return out
    sig = ("drift", thing.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    space.meters["risk"] += float(world.sector.risk)
    for kid in world.kids():
        kid.memes["wonder"] += 1
        kid.memes["worry"] += 1
    out.append("__drift__")
    return out


def _r_rescued(world: World) -> list[str]:
    out: list[str] = []
    thing = world.entities.get("mystery")
    space = world.entities.get("space")
    if thing is None or space is None:
        return out
    if thing.meters["secured"] < THRESHOLD:
        return out
    sig = ("secured", thing.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    thing.meters["drifting"] = 0.0
    space.meters["risk"] = 0.0
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
    out.append("__secured__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="drift", tag="physical", apply=_r_drift),
    Rule(name="secured", tag="physical", apply=_r_rescued),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def compatible(response: Response, mystery: Mystery) -> bool:
    return mystery.material in response.materials


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sector_id in SECTORS:
        for mystery_id, mystery in MYSTERIES.items():
            for response_id, response in RESPONSES.items():
                if response.sense >= SENSE_MIN and compatible(response, mystery):
                    combos.append((sector_id, mystery_id, response_id))
    return combos


def drift_severity(sector: Sector, delay: int) -> int:
    return sector.risk + delay


def is_rescued(sector: Sector, response: Response, delay: int) -> bool:
    return response.power >= drift_severity(sector, delay)


def predict_loss(world: World, delay: int) -> dict:
    sim = world.copy()
    thing = sim.get("mystery")
    space = sim.get("space")
    thing.meters["drifting"] = 1.0
    propagate(sim, narrate=False)
    return {
        "risk": int(space.meters["risk"]) + delay,
        "drifting": thing.meters["drifting"] >= THRESHOLD,
    }


def introduce(world: World, a: Entity, b: Entity, sector: Sector) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"{a.id} and {b.id} were riding with their {world.get('Parent').label_word} in a small shuttle, "
        f"on the way past {sector.name}. {sector.window_view}"
    )
    world.say(
        f"They pretended the ship was the bravest explorer in the sky, and even the cup holder felt like a control panel."
    )


def spot(world: World, a: Entity, b: Entity, mystery: Mystery, sector: Sector) -> None:
    thing = world.get("mystery")
    thing.meters["drifting"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Then {sector.glow_line} Outside the round window floated {mystery.first_shape}, turning slowly in the dark."
    )
    world.say(
        f'"Look!" {a.id} whispered. "{mystery.first_guess}!"'
    )
    world.say(
        f"{b.id} pressed closer to the glass. The strange thing gave {mystery.chirp}."
    )


def tempt(world: World, a: Entity) -> None:
    a.memes["impulse"] += 1
    world.say(
        f'"We should grab it right now," said {a.id}. "{a.pronoun("subject").capitalize()} could pop the outer hatch and zoom out on the helper scooter before it drifts away."'
    )


def consult_warning(world: World, b: Entity, a: Entity, parent: Entity, sector: Sector, delay: int) -> None:
    pred = predict_loss(world, delay)
    world.facts["predicted_risk"] = pred["risk"]
    b.memes["care"] += 1
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "No. We have to consult the ship computer first, and {parent.label_word} too," {b.pronoun()} said.'
    )
    world.say(
        f'"Things outside can tumble into trouble fast near {sector.name}. If we guess wrong, we could make it worse."'
    )


def consult_scan(world: World, parent: Entity, mystery: Mystery) -> None:
    thing = world.get("mystery")
    thing.memes["identified"] = 1.0
    world.facts["consulted"] = True
    world.say(
        f"{parent.label_word.capitalize()} tapped the scanner, and the ship gave a soft blue hum."
    )
    world.say(
        f"The screen drew neat bright lines around the shape. Then came the twist: it was not {mystery.first_guess.lower()} at all."
    )
    world.say(
        f"It was {mystery.true_phrase}, {mystery.purpose}."
    )


def choose_response(world: World, parent: Entity, response: Response, mystery: Mystery) -> None:
    world.say(
        f'"Good thing we stopped to consult," {parent.label_word} said. "For something made of {mystery.material}, we need the right tool."'
    )
    if response.id == "magnet_arm":
        world.say(
            f"{parent.label_word.capitalize()} swung the ship's magnet arm toward the drifting object."
        )
    elif response.id == "tow_beam":
        world.say(
            f"{parent.label_word.capitalize()} lined up the gentle tow beam and painted the drifting object with a band of silver light."
        )
    elif response.id == "foam_claw":
        world.say(
            f"{parent.label_word.capitalize()} eased out the foam-padded claw, slow and careful."
        )
    else:
        world.say(
            f"{parent.label_word.capitalize()} reached for a tool."
        )


def rescue(world: World, parent: Entity, response: Response, mystery: Mystery) -> None:
    thing = world.get("mystery")
    thing.meters["secured"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} {response.text}."
    )
    world.say(
        f"A moment later, the air lock clunked, the inner door slid open, and {mystery.true_phrase} bobbed safely inside."
    )


def fail_rescue(world: World, parent: Entity, response: Response, mystery: Mystery, sector: Sector) -> None:
    thing = world.get("mystery")
    space = world.get("space")
    thing.meters["lost"] = 1.0
    space.meters["risk"] += 1.0
    world.say(
        f"{parent.label_word.capitalize()} {response.fail}."
    )
    world.say(
        f"But the drift was too strong near {sector.name}. The little object spun away into the bright pebbly dark before anyone could try again."
    )


def happy_ending(world: World, a: Entity, b: Entity, parent: Entity, mystery: Mystery) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f'{a.id} blinked. "So the scary thing was helping all along?"'
    )
    world.say(
        f'"That is why we consult before we leap," {parent.label_word} said with a smile. "Space is full of surprises, and some surprises need kindness more than guesses."'
    )
    world.say(
        f"Soon {mystery.ending_image} The shuttle felt warmer, and the stars outside no longer looked lonely."
    )


def sad_ending(world: World, a: Entity, b: Entity, parent: Entity, mystery: Mystery) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["sadness"] += 1
    world.say(
        f"{a.id} and {b.id} stood very still by the window and watched until even the last blink was gone."
    )
    world.say(
        f'"We did the right first thing by stopping to consult," {parent.label_word} said gently. "Next time we will be ready even faster."'
    )
    world.say(
        f"The children gave the dark a small salute and promised that in space, brave hearts would always ask and think before they rushed."
    )


def tell(
    sector: Sector,
    mystery: Mystery,
    response: Response,
    *,
    instigator: str = "Tara",
    instigator_gender: str = "girl",
    cautioner: str = "Milo",
    cautioner_gender: str = "boy",
    parent_type: str = "mother",
    delay: int = 0,
) -> World:
    world = World(sector=sector)
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        traits=["bold"],
        attrs={},
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        traits=["careful"],
        attrs={},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
        attrs={},
    ))
    world.add(Entity(id="space", type="space", label="space", attrs={}))
    world.add(Entity(id="mystery", type="object", label=mystery.true_name, attrs={"material": mystery.material}))

    world.facts["consulted"] = False
    world.facts["predicted_risk"] = 0
    world.facts["delay"] = delay

    introduce(world, a, b, sector)
    spot(world, a, b, mystery, sector)

    world.para()
    tempt(world, a)
    consult_warning(world, b, a, parent, sector, delay)
    consult_scan(world, parent, mystery)

    world.para()
    choose_response(world, parent, response, mystery)
    success = is_rescued(sector, response, delay)
    if success:
        rescue(world, parent, response, mystery)
        world.para()
        happy_ending(world, a, b, parent, mystery)
        outcome = "rescued"
    else:
        fail_rescue(world, parent, response, mystery, sector)
        world.para()
        sad_ending(world, a, b, parent, mystery)
        outcome = "lost"

    thing = world.get("mystery")
    world.facts.update(
        sector=sector,
        mystery_cfg=mystery,
        response=response,
        parent=parent,
        instigator=a,
        cautioner=b,
        outcome=outcome,
        success=success,
        secured=thing.meters["secured"] >= THRESHOLD,
        consulted=True,
        severity=drift_severity(sector, delay),
    )
    return world


SECTORS = {
    "moon_orbit": Sector(
        id="moon_orbit",
        name="the silver side of the moon",
        window_view="Far below, craters shone like giant thumbprints in flour.",
        glow_line="a bead of green light winked between two sleepy antennas.",
        risk=1,
        tags={"moon", "space"},
    ),
    "ring_lane": Sector(
        id="ring_lane",
        name="the bright ring lane",
        window_view="A ribbon of ice crumbs arced past the ship like glitter tossed across velvet.",
        glow_line="something flickered between the ring stones, then vanished, then flickered again.",
        risk=2,
        tags={"rings", "space"},
    ),
    "comet_turn": Sector(
        id="comet_turn",
        name="the blue comet turn",
        window_view="Behind the shuttle, the comet's tail spread out like a glowing scarf.",
        glow_line="a sharp little sparkle tumbled in the comet dust and bumped against the dark.",
        risk=3,
        tags={"comet", "space"},
    ),
}

MYSTERIES = {
    "beacon": Mystery(
        id="beacon",
        first_shape="a spiky green star with one eye-bright blink",
        first_guess="a baby space monster",
        true_name="beacon",
        true_phrase="a tiny lost beacon sphere",
        purpose="sent out to mark the safe path home for other ships",
        material="metal",
        chirp="a worried pip-pip-pip",
        ending_image="the little beacon blinked cheerfully from a shelf by the window, painting dots of green on their sleeves.",
        tags={"beacon", "consult"},
    ),
    "seed_pod": Mystery(
        id="seed_pod",
        first_shape="a golden shell with curly fins folded tight",
        first_guess="a treasure egg",
        true_name="seed pod",
        true_phrase="a drifting garden seed pod",
        purpose="packed with sleepy seeds for the greenhouse deck",
        material="fabric",
        chirp="a soft peep from its guidance tag",
        ending_image="later, the seed pod rested in a warm tray, waiting to grow moon-tomatoes under the lamp.",
        tags={"garden", "consult"},
    ),
    "mail_drone": Mystery(
        id="mail_drone",
        first_shape="a blinking silver claw with one red spark at its middle",
        first_guess="a pirate trap",
        true_name="mail drone",
        true_phrase="a little mail drone with its arms folded in",
        purpose="carrying a note bundle and a packet of star stickers",
        material="metal",
        chirp="a thin help-meep through the hull",
        ending_image="soon the mail drone was humming by the door, and the packet of star stickers shone on the table between them.",
        tags={"mail", "consult"},
    ),
    "crystal_map": Mystery(
        id="crystal_map",
        first_shape="a blue shard that flashed like a cold tooth",
        first_guess="a broken comet fang",
        true_name="crystal map",
        true_phrase="a crystal map prism",
        purpose="holding a tiny picture of the safest tunnels through the comet dust",
        material="crystal",
        chirp="a bright tink-tink from the cracked locator ring",
        ending_image="before bed, the crystal map threw small blue roads across the ceiling like friendly constellations.",
        tags={"crystal", "consult"},
    ),
}

RESPONSES = {
    "magnet_arm": Response(
        id="magnet_arm",
        sense=3,
        power=3,
        materials={"metal"},
        text="locked onto it with the magnet arm and reeled it in, inch by careful inch",
        fail="reached with the magnet arm, but the pull slipped and could not beat the rushing drift",
        qa_text="used the magnet arm to pull it safely back to the shuttle",
        tags={"magnet", "rescue"},
    ),
    "tow_beam": Response(
        id="tow_beam",
        sense=3,
        power=2,
        materials={"metal", "fabric", "crystal"},
        text="wrapped it in the tow beam and guided it gently into the air lock",
        fail="caught it in the tow beam for a second, but the stream outside dragged it free",
        qa_text="used the tow beam to guide it into the air lock",
        tags={"tow_beam", "rescue"},
    ),
    "foam_claw": Response(
        id="foam_claw",
        sense=2,
        power=2,
        materials={"fabric", "crystal"},
        text="closed the foam-padded claw around it as softly as picking up a soap bubble",
        fail="tried to cradle it with the foam-padded claw, but it spun out past the tip",
        qa_text="used the foam-padded claw to cradle it safely",
        tags={"claw", "rescue"},
    ),
    "cargo_net": Response(
        id="cargo_net",
        sense=1,
        power=1,
        materials={"fabric"},
        text="flung the cargo net and somehow snagged it",
        fail="threw a cargo net after it, but the net opened too wide and drifted uselessly away",
        qa_text="threw a cargo net at it",
        tags={"net", "rescue"},
    ),
}

GIRL_NAMES = ["Tara", "Lina", "Nova", "Ivy", "Mira", "Skye", "Zuri", "Aya"]
BOY_NAMES = ["Milo", "Theo", "Owen", "Nico", "Finn", "Arlo", "Jace", "Kai"]


@dataclass
class StoryParams:
    sector: str
    mystery: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
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
    "consult": [
        (
            "What does it mean to consult before you do something big?",
            "To consult means to stop and ask for good information or advice before you act. It helps you make a safer, smarter plan."
        )
    ],
    "moon": [
        (
            "What is orbit?",
            "Orbit is the path something follows as it goes around a moon or planet. Spaceships can travel in orbit instead of landing right away."
        )
    ],
    "rings": [
        (
            "What are planetary rings made of?",
            "Planetary rings are made of many tiny pieces of ice and rock moving together around a planet. From far away they can look like one shining band."
        )
    ],
    "comet": [
        (
            "What is a comet?",
            "A comet is a chunk of ice, dust, and rock that travels through space. When sunlight warms it, it can grow a long glowing tail."
        )
    ],
    "beacon": [
        (
            "What does a beacon do?",
            "A beacon sends out a signal to help others find a place or a safe path. In space, a beacon can guide ships when things are dark or confusing."
        )
    ],
    "garden": [
        (
            "Why would a spaceship carry seeds?",
            "A spaceship might carry seeds so people can grow food or plants on board. Plants can make long trips feel brighter and more alive."
        )
    ],
    "mail": [
        (
            "What is a drone?",
            "A drone is a small machine that can move by itself or by remote control. Some drones carry tools or messages from one place to another."
        )
    ],
    "crystal": [
        (
            "Why are some things made of crystal handled gently?",
            "Crystal can chip or crack more easily than metal, so people handle it carefully. Gentle tools help keep it safe."
        )
    ],
    "magnet": [
        (
            "What does a magnet do?",
            "A magnet can pull some kinds of metal toward it. That makes magnets useful for picking up certain metal things without using hands."
        )
    ],
    "tow_beam": [
        (
            "What does a tow beam do in a pretend space story?",
            "A tow beam is a gentle pulling light that helps guide something drifting back where it belongs. In a space adventure, it is a safe rescue tool."
        )
    ],
    "claw": [
        (
            "Why would a padded claw help with a rescue?",
            "A padded claw can hold something soft or breakable without squeezing too hard. The padding keeps the object from getting hurt."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "consult",
    "moon",
    "rings",
    "comet",
    "beacon",
    "garden",
    "mail",
    "crystal",
    "magnet",
    "tow_beam",
    "claw",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    mystery = f["mystery_cfg"]
    sector = f["sector"]
    outcome = f["outcome"]
    base = (
        f'Write a short Space Adventure story for a 3-to-5-year-old where two children spot something strange near {sector.name} and stop to consult the ship computer before acting.'
    )
    if outcome == "rescued":
        return [
            base,
            f"Tell a gentle space story where {a.id} wants to rush out after a mystery object, but {b.id} insists they consult first, and the twist is that the strange thing is really {mystery.true_phrase}.",
            f'Write a simple story with the word "consult" where a scary-looking object turns out to need help, and the family rescues it safely.',
        ]
    return [
        base,
        f"Tell a thoughtful space story where consulting first reveals the truth about the mystery object, but the drift outside is still too strong and the children must say goodbye.",
        f'Write a Space Adventure story with the word "consult" and a twist: the object is not dangerous at all, but the family cannot save it in time and learns to be ready earlier next time.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    mystery = f["mystery_cfg"]
    response = f["response"]
    sector = f["sector"]
    risk = f.get("predicted_risk", 0)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id}, two children riding in a shuttle with their {parent.label_word}. They are on a small space trip when they notice something strange outside."
        ),
        (
            "What did the children see outside the shuttle?",
            f"They saw {mystery.first_shape} drifting outside the window. At first it looked like {mystery.first_guess.lower()}, so it felt exciting and a little scary."
        ),
        (
            f"Why did {b.id} want to consult before anyone rushed outside?",
            f"{b.id} knew the thing was drifting near {sector.name}, where trouble can grow quickly. Consulting first gave the family real information instead of a wild guess, and the scanner showed the danger level was about {risk}."
        ),
        (
            "What was the twist?",
            f"The twist was that the strange thing was not {mystery.first_guess.lower()} at all. It was {mystery.true_phrase}, and it needed help instead of fighting."
        ),
    ]
    if f["outcome"] == "rescued":
        qa.append(
            (
                f"How did the family rescue the object?",
                f"They used the right tool and {response.qa_text}. That worked because they had stopped to consult and learned what the object was made of before trying to grab it."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended warmly and safely, with {mystery.true_phrase} inside the shuttle. The ending image shows what changed: the mysterious thing was no longer lonely outside, and the children were calmer and wiser inside."
            )
        )
    else:
        qa.append(
            (
                "Could they save it?",
                f"No. Even after they made a smart plan, the drift outside was too strong and the object floated away. The family still learned something important because consulting first kept them from making a reckless mistake."
            )
        )
        qa.append(
            (
                "What did the children learn at the end?",
                f"They learned that brave space travelers do not just rush -- they consult, think, and then act. That lesson mattered even more after they watched how fast the object drifted away."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["sector"].tags) | set(f["mystery_cfg"].tags)
    tags.add("consult")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        sector="moon_orbit",
        mystery="beacon",
        response="magnet_arm",
        instigator="Tara",
        instigator_gender="girl",
        cautioner="Milo",
        cautioner_gender="boy",
        parent="mother",
        delay=0,
    ),
    StoryParams(
        sector="ring_lane",
        mystery="seed_pod",
        response="tow_beam",
        instigator="Nova",
        instigator_gender="girl",
        cautioner="Theo",
        cautioner_gender="boy",
        parent="father",
        delay=0,
    ),
    StoryParams(
        sector="ring_lane",
        mystery="crystal_map",
        response="foam_claw",
        instigator="Kai",
        instigator_gender="boy",
        cautioner="Mira",
        cautioner_gender="girl",
        parent="mother",
        delay=1,
    ),
    StoryParams(
        sector="comet_turn",
        mystery="mail_drone",
        response="tow_beam",
        instigator="Finn",
        instigator_gender="boy",
        cautioner="Skye",
        cautioner_gender="girl",
        parent="father",
        delay=2,
    ),
    StoryParams(
        sector="comet_turn",
        mystery="beacon",
        response="magnet_arm",
        instigator="Aya",
        instigator_gender="girl",
        cautioner="Nico",
        cautioner_gender="boy",
        parent="mother",
        delay=1,
    ),
]


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try a safer rescue method such as {better}.)"
    )


def explain_incompatible(mystery: Mystery, response: Response) -> str:
    mats = ", ".join(sorted(response.materials))
    return (
        f"(No story: {response.id} can handle {mats}, but {mystery.true_name} is made of {mystery.material}. "
        f"The rescue tool must fit the object.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.sector not in SECTORS:
        return "?"
    if params.response not in RESPONSES:
        return "?"
    return "rescued" if is_rescued(SECTORS[params.sector], RESPONSES[params.response], params.delay) else "lost"


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
compatible(M,R) :- mystery(M), material(M,Mat), handles(R,Mat).
valid(Sec,M,R) :- sector(Sec), mystery(M), response(R), sensible(R), compatible(M,R).

severity(V) :- chosen_sector(Sec), risk(Sec,R), delay(D), V = R + D.
rescued :- chosen_response(R), power(R,P), severity(V), P >= V.
outcome(rescued) :- rescued.
outcome(lost) :- not rescued.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sector_id, sector in SECTORS.items():
        lines.append(asp.fact("sector", sector_id))
        lines.append(asp.fact("risk", sector_id, sector.risk))
    for mystery_id, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mystery_id))
        lines.append(asp.fact("material", mystery_id, mystery.material))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
        for material in sorted(response.materials):
            lines.append(asp.fact("handles", response_id, material))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3.\n#show sensible/1."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_sector", params.sector),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
    ])
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

    py_sensible = {r.id for r in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        emit(smoke, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generation/emit succeeded.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: children on a shuttle, a mysterious drifting object, a consult-first twist."
    )
    ap.add_argument("--sector", choices=SECTORS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra drift time before the rescue tool can lock on")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (sector, mystery, response) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    names = GIRL_NAMES if gender == "girl" else BOY_NAMES
    pool = [n for n in names if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.mystery and args.response:
        mystery = MYSTERIES[args.mystery]
        response = RESPONSES[args.response]
        if not compatible(response, mystery):
            raise StoryError(explain_incompatible(mystery, response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.sector is None or combo[0] == args.sector)
        and (args.mystery is None or combo[1] == args.mystery)
        and (args.response is None or combo[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    sector_id, mystery_id, response_id = rng.choice(sorted(combos))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1, 1, 2])

    return StoryParams(
        sector=sector_id,
        mystery=mystery_id,
        response=response_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        parent=parent,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.sector not in SECTORS:
        raise StoryError(f"(Unknown sector: {params.sector})")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"(Unknown mystery: {params.mystery})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")

    sector = SECTORS[params.sector]
    mystery = MYSTERIES[params.mystery]
    response = RESPONSES[params.response]

    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not compatible(response, mystery):
        raise StoryError(explain_incompatible(mystery, response))

    world = tell(
        sector=sector,
        mystery=mystery,
        response=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (sector, mystery, response) combos:\n")
        for sector_id, mystery_id, response_id in combos:
            print(f"  {sector_id:11} {mystery_id:12} {response_id}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.mystery} at {p.sector} ({p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
