#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hang_foreshadowing_dialogue_magic_adventure.py
=========================================================================

A standalone story world for a tiny magical adventure: two children carry a lost
sky-chime back to its hidden home, meet one obstacle on the way, and solve it
with the right kind of magic. The world is built around three seed requirements:

- the word "hang"
- foreshadowing
- dialogue
- an adventure tone

The foreshadowing is state-driven, not decorative: an elder gives the children a
silver guide ribbon and says that when it begins to hang straight, the hidden
gate is near. Early in the journey the ribbon flutters wildly; after the
obstacle is truly solved and the destination is close, the ribbon's state
changes and the promise pays off in the ending image.

This world uses one compact reasonableness rule:
a story is only valid when the chosen place can plausibly contain the chosen
obstacle, and the chosen magic is the kind of magic that can honestly solve it.
Invalid explicit combinations are rejected with StoryError instead of being
forced into weak prose.

Run it
------
    python storyworlds/worlds/gpt-5.4/hang_foreshadowing_dialogue_magic_adventure.py
    python storyworlds/worlds/gpt-5.4/hang_foreshadowing_dialogue_magic_adventure.py --place whispering_woods --obstacle thorns --magic lullaby_flute
    python storyworlds/worlds/gpt-5.4/hang_foreshadowing_dialogue_magic_adventure.py --place moon_cave --obstacle dark --magic bridge_ribbon
    python storyworlds/worlds/gpt-5.4/hang_foreshadowing_dialogue_magic_adventure.py --all
    python storyworlds/worlds/gpt-5.4/hang_foreshadowing_dialogue_magic_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/hang_foreshadowing_dialogue_magic_adventure.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "witch"}
        male = {"boy", "father", "grandfather", "man", "wizard"}
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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
class Place:
    id: str
    label: str
    trail: str
    destination: str
    air: str
    affords: set[str] = field(default_factory=set)
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
class Obstacle:
    id: str
    label: str
    intro: str
    danger: str
    solve_tag: str
    aftermath: str
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
class MagicTool:
    id: str
    label: str
    phrase: str
    solve_tag: str
    spell_line: str
    effect: str
    qa_text: str
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
class Treasure:
    id: str
    label: str
    phrase: str
    home: str
    song: str
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


PLACES = {
    "whispering_woods": Place(
        id="whispering_woods",
        label="the Whispering Woods",
        trail="a ferny trail under old branches",
        destination="the ivy gate in an ancient oak",
        air="Leaves whispered to one another overhead.",
        affords={"thorns", "gap"},
        tags={"forest", "adventure"},
    ),
    "moon_cave": Place(
        id="moon_cave",
        label="the Moon Cave",
        trail="a winding stone path under the hill",
        destination="the silver door deep inside the cave",
        air="Cool drips tapped from the ceiling like tiny bells.",
        affords={"dark"},
        tags={"cave", "adventure"},
    ),
    "cloud_cliff": Place(
        id="cloud_cliff",
        label="the Cloud Cliff",
        trail="a narrow path high above the valley",
        destination="the wind shrine at the cliff's far side",
        air="The sky felt close enough to touch.",
        affords={"gap", "dark"},
        tags={"cliff", "adventure"},
    ),
}

OBSTACLES = {
    "thorns": Obstacle(
        id="thorns",
        label="sleeping thorn-vines",
        intro="A wall of thorn-vines had grown across the path, woven tight as a basket.",
        danger="The thorns twitched whenever anyone stepped close, as if they were ready to grab a sleeve.",
        solve_tag="soothe",
        aftermath="The thorn-vines loosened and curled back like cats settling into a nap.",
        tags={"thorns", "plants"},
    ),
    "dark": Obstacle(
        id="dark",
        label="a patch of swallowing dark",
        intro="Ahead of them lay a patch of dark so thick it looked almost poured onto the ground.",
        danger="The children could not see where the path bent, and the stones near the edge looked slippery.",
        solve_tag="light",
        aftermath="The dark peeled away from the path, and the safe stones shone clear.",
        tags={"dark", "light"},
    ),
    "gap": Obstacle(
        id="gap",
        label="a broken path over a drop",
        intro="Part of the path had fallen away, leaving a windy gap above the rocks below.",
        danger="It was too wide for a jump, and the wind kept tugging at their sleeves.",
        solve_tag="bridge",
        aftermath="A bright way stretched across the empty space, steady enough for small careful feet.",
        tags={"gap", "bridge"},
    ),
}

MAGIC = {
    "lullaby_flute": MagicTool(
        id="lullaby_flute",
        label="lullaby flute",
        phrase="a little willow flute",
        solve_tag="soothe",
        spell_line='"Hush now, thorns. Dream of rain and roots."',
        effect="the note floated soft and warm through the air",
        qa_text="played the lullaby flute to soothe the thorn-vines until they curled aside",
        tags={"music", "magic", "flute"},
    ),
    "glow_orb": MagicTool(
        id="glow_orb",
        label="glow orb",
        phrase="a pearl-bright glow orb",
        solve_tag="light",
        spell_line='"Shine small, shine steady, show the true stones."',
        effect="the orb lifted from the child's palm and poured silver light over the path",
        qa_text="used the glow orb to light the hidden path so they could walk safely",
        tags={"light", "magic", "orb"},
    ),
    "bridge_ribbon": MagicTool(
        id="bridge_ribbon",
        label="bridge ribbon",
        phrase="a ribbon woven from moon-silk",
        solve_tag="bridge",
        spell_line='"Ribbon, remember how a path should hold."',
        effect="the ribbon leapt into the air and wove itself into a shining bridge",
        qa_text="sent the bridge ribbon across the gap, and it wove a safe shining bridge",
        tags={"bridge", "magic", "ribbon"},
    ),
}

TREASURES = {
    "sky_chime": Treasure(
        id="sky_chime",
        label="sky-chime",
        phrase="a lost sky-chime shaped like a silver star",
        home="its little hook above the hidden door",
        song="a clear silver note",
        tags={"bell", "magic"},
    ),
    "sun_key": Treasure(
        id="sun_key",
        label="sun-key",
        phrase="a lost sun-key warm as toast",
        home="the lock at the hidden door",
        song="a bright golden hum",
        tags={"key", "magic"},
    ),
    "feather_token": Treasure(
        id="feather_token",
        label="feather token",
        phrase="a lost feather token glowing pale blue",
        home="the wind shrine's carved nest",
        song="a soft airy trill",
        tags={"token", "magic"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tara", "Nora", "Zia", "Asha", "Pia", "Wren"]
BOY_NAMES = ["Oren", "Milo", "Tobin", "Finn", "Eli", "Rowan", "Jory", "Kai"]
TRAITS = ["brave", "curious", "careful", "hopeful", "steady", "bright"]


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "foreshadow_line": "",
            "ribbon_line": "",
            "obstacle_seen": False,
            "obstacle_cleared": False,
            "near_goal": False,
            "returned": False,
        }

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
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


def _r_blocked(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    hero = world.get("hero")
    friend = world.get("friend")
    if obstacle.meters["blocking"] < THRESHOLD:
        return []
    sig = ("blocked", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    friend.memes["caution"] += 1
    world.facts["obstacle_seen"] = True
    return ["__blocked__"]


def _r_near_goal(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    ribbon = world.get("ribbon")
    destination = world.get("destination")
    if obstacle.meters["cleared"] < THRESHOLD or destination.meters["open"] >= THRESHOLD:
        return []
    sig = ("near_goal", destination.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    destination.meters["open"] += 1
    ribbon.meters["hanging"] += 1
    ribbon.meters["fluttering"] = 0.0
    world.facts["near_goal"] = True
    return ["__near_goal__"]


def _r_returned(world: World) -> list[str]:
    treasure = world.get("treasure")
    hero = world.get("hero")
    friend = world.get("friend")
    elder = world.get("elder")
    destination = world.get("destination")
    if treasure.meters["returned"] < THRESHOLD or destination.meters["open"] < THRESHOLD:
        return []
    sig = ("returned", treasure.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    friend.memes["joy"] += 1
    friend.memes["wonder"] += 1
    elder.memes["pride"] += 1
    world.facts["returned"] = True
    return ["__returned__"]


CAUSAL_RULES = [
    Rule(name="blocked", tag="tension", apply=_r_blocked),
    Rule(name="near_goal", tag="turn", apply=_r_near_goal),
    Rule(name="returned", tag="resolution", apply=_r_returned),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def magic_fits(obstacle: Obstacle, magic: MagicTool) -> bool:
    return obstacle.solve_tag == magic.solve_tag


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for obstacle_id in sorted(place.affords):
            obstacle = OBSTACLES[obstacle_id]
            for magic_id, magic in MAGIC.items():
                if magic_fits(obstacle, magic):
                    combos.append((place_id, obstacle_id, magic_id))
    return sorted(combos)


def explain_rejection(place: Optional[Place], obstacle: Optional[Obstacle], magic: Optional[MagicTool]) -> str:
    if place and obstacle and obstacle.id not in place.affords:
        allowed = ", ".join(sorted(place.affords))
        return (
            f"(No story: {place.label} does not fit the obstacle '{obstacle.id}'. "
            f"That place supports: {allowed}.)"
        )
    if obstacle and magic and not magic_fits(obstacle, magic):
        return (
            f"(No story: {magic.label} cannot honestly solve {obstacle.label}. "
            f"Choose magic that can {obstacle.solve_tag} the problem.)"
        )
    return "(No story: this combination is not part of the world's reasonable set.)"


def predict_success(world: World, magic: MagicTool) -> dict:
    sim = world.copy()
    obstacle = sim.get("obstacle")
    obstacle.meters["cleared"] += 1 if magic_fits(OBSTACLES[sim.facts["obstacle_cfg"].id], magic) else 0
    propagate(sim, narrate=False)
    return {
        "cleared": obstacle.meters["cleared"] >= THRESHOLD,
        "near_goal": bool(sim.facts["near_goal"]),
        "ribbon_hanging": sim.get("ribbon").meters["hanging"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, friend: Entity, elder: Entity, treasure: Treasure) -> None:
    hero.memes["wonder"] += 1
    friend.memes["wonder"] += 1
    world.say(
        f"{hero.id} and {friend.id} stood at the edge of {world.place.label} while "
        f"{elder.label_word.capitalize()} placed {treasure.phrase} in {hero.id}'s hands."
    )
    world.say(
        f'"This belongs at {world.place.destination}," {elder.label_word} said. '
        f'"If it sleeps away from home for one more night, its song will fade."'
    )


def foreshadow(world: World, elder: Entity, hero: Entity, friend: Entity) -> None:
    ribbon = world.get("ribbon")
    ribbon.meters["fluttering"] = 1.0
    line = (
        'Then the old guide ribbon gave a nervous little shake in the breeze. '
        f'"Watch this closely," {elder.label_word} whispered. '
        '"When the silver ribbon begins to hang straight instead of fluttering, '
        'you will know the hidden place is near."'
    )
    world.facts["foreshadow_line"] = line
    world.say(line)
    world.say(
        f'"So if it still dances, we keep going?" {friend.id} asked. '
        f'"Exactly," said {elder.label_word}.'
    )


def begin_journey(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["bravery"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"With the ribbon tied to {hero.id}'s satchel and the treasure wrapped safely in a scarf, "
        f"the two children set off along {world.place.trail}. {world.place.air}"
    )
    world.say(
        f'"Adventure feet," {hero.id} said.'
        f' "{friend.id}, stay close."'
    )


def meet_obstacle(world: World, hero: Entity, friend: Entity, obstacle: Obstacle) -> None:
    world.get("obstacle").meters["blocking"] += 1
    propagate(world, narrate=False)
    world.say(obstacle.intro)
    world.say(obstacle.danger)
    world.say(
        f'"Oh," {friend.id} breathed. "That is not a little problem."'
    )
    if hero.memes["fear"] >= THRESHOLD:
        world.say(
            f'{hero.id} swallowed hard, but kept one hand on the treasure bundle.'
        )


def discuss_plan(world: World, hero: Entity, friend: Entity, magic: MagicTool) -> None:
    pred = predict_success(world, magic)
    world.facts["predicted_clear"] = pred["cleared"]
    world.facts["predicted_ribbon_hanging"] = pred["ribbon_hanging"]
    friend.memes["caution"] += 1
    world.say(
        f'"Wait," said {friend.id}. "We do have {magic.phrase}. '
        f'If the magic really works, the ribbon should stop fluttering after we pass."'
    )
    world.say(
        f'"Then let\'s try the true way, not the rushed way," {hero.id} said.'
    )


def use_magic(world: World, hero: Entity, magic: MagicTool, obstacle: Obstacle) -> None:
    obstacle_ent = world.get("obstacle")
    hero.memes["focus"] += 1
    world.say(
        f"{hero.id} took out {magic.phrase} and spoke the spell: {magic.spell_line}"
    )
    world.say(f"At once, {magic.effect}.")
    obstacle_ent.meters["cleared"] += 1
    obstacle_ent.meters["blocking"] = 0.0
    propagate(world, narrate=False)
    world.say(obstacle.aftermath)


def cross_and_notice(world: World, hero: Entity, friend: Entity) -> None:
    ribbon = world.get("ribbon")
    hero.memes["hope"] += 1
    friend.memes["wonder"] += 1
    world.say(
        f"They went on carefully, step by step, until the path opened ahead of them."
    )
    if ribbon.meters["hanging"] >= THRESHOLD:
        line = (
            f"Then {friend.id} pointed. "
            f'"Look! The ribbon does not flutter now. It has begun to hang straight."'
        )
        world.facts["ribbon_line"] = line
        world.say(line)
        world.say(
            f'{hero.id} smiled. "Grandma was right. We are close."'
        )


def return_treasure(world: World, hero: Entity, friend: Entity, treasure: Treasure) -> None:
    treasure_ent = world.get("treasure")
    destination = world.get("destination")
    destination.meters["reached"] += 1
    treasure_ent.meters["returned"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At last they reached {world.place.destination}. "
        f"{hero.id} lifted the {treasure.label} to {treasure.home}."
    )
    world.say(
        f"As soon as it touched home, it sang {treasure.song}, and a soft light spilled over both children."
    )
    world.say(
        f'"We brought it back," {friend.id} said, almost laughing from relief.'
    )


def ending(world: World, elder: Entity, hero: Entity, friend: Entity, treasure: Treasure) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"When they came out again, {elder.label_word} was waiting by the first bend in the trail, "
        f"as if {elder.pronoun()} had trusted the whole path all along."
    )
    world.say(
        f'"You listened to the warning, you watched the ribbon, and you brought the {treasure.label} home," '
        f'{elder.label_word} said.'
    )
    world.say(
        f"The ribbon still hung straight from {hero.id}'s satchel, quiet and silver in the evening air, "
        f"and the adventure no longer felt like a question. It felt like a promise they had kept."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    place: Place,
    obstacle_cfg: Obstacle,
    magic_cfg: MagicTool,
    treasure_cfg: Treasure,
    hero_name: str = "Lina",
    hero_gender: str = "girl",
    friend_name: str = "Oren",
    friend_gender: str = "boy",
    elder_type: str = "grandmother",
    hero_trait: str = "brave",
    friend_trait: str = "careful",
) -> World:
    world = World(place)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=[hero_trait],
        attrs={},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        traits=[friend_trait],
        attrs={},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        role="elder",
        label="the elder",
        attrs={},
    ))
    ribbon = world.add(Entity(
        id="ribbon",
        kind="thing",
        type="ribbon",
        label="guide ribbon",
        owner=hero.id,
        attrs={},
    ))
    obstacle = world.add(Entity(
        id="obstacle",
        kind="thing",
        type="obstacle",
        label=obstacle_cfg.label,
        attrs={},
    ))
    destination = world.add(Entity(
        id="destination",
        kind="thing",
        type="destination",
        label=place.destination,
        attrs={},
    ))
    treasure = world.add(Entity(
        id="treasure",
        kind="thing",
        type=treasure_cfg.id,
        label=treasure_cfg.label,
        owner=hero.id,
        attrs={},
    ))

    world.facts.update(
        hero=hero,
        friend=friend,
        elder=elder,
        ribbon=ribbon,
        obstacle_cfg=obstacle_cfg,
        magic_cfg=magic_cfg,
        treasure_cfg=treasure_cfg,
        destination_cfg=place.destination,
        place_cfg=place,
        predicted_clear=False,
        predicted_ribbon_hanging=False,
    )

    introduce(world, hero, friend, elder, treasure_cfg)
    foreshadow(world, elder, hero, friend)
    world.para()
    begin_journey(world, hero, friend)
    meet_obstacle(world, hero, friend, obstacle_cfg)
    discuss_plan(world, hero, friend, magic_cfg)
    world.para()
    use_magic(world, hero, magic_cfg, obstacle_cfg)
    cross_and_notice(world, hero, friend)
    world.para()
    return_treasure(world, hero, friend, treasure_cfg)
    ending(world, elder, hero, friend, treasure_cfg)

    world.facts.update(
        success=world.facts["returned"],
        near_goal=world.facts["near_goal"],
        obstacle_label=obstacle_cfg.label,
        magic_label=magic_cfg.label,
        treasure_label=treasure_cfg.label,
    )
    return world


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    obstacle: str
    magic: str
    treasure: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    elder: str
    hero_trait: str
    friend_trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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
    "thorns": [
        (
            "Why can thorn-vines be hard to pass?",
            "Thorn-vines have sharp points and tangle together, so they can catch on clothes and block a path."
        )
    ],
    "dark": [
        (
            "Why is it hard to walk in the dark?",
            "It is hard to walk in the dark because you cannot easily see the path, edges, or slippery stones. That makes careful walking much harder."
        )
    ],
    "gap": [
        (
            "Why is a gap in a path dangerous?",
            "A gap means part of the safe ground is missing. If you cannot cross it safely, you could fall."
        )
    ],
    "flute": [
        (
            "What is a flute?",
            "A flute is a musical instrument you blow into to make notes. In stories, music is often used as gentle magic."
        )
    ],
    "orb": [
        (
            "What is an orb?",
            "An orb is a round object like a little glowing ball. In magic stories, an orb often shines or carries power."
        )
    ],
    "ribbon": [
        (
            "What does it mean when something hangs straight?",
            "When something hangs straight, it is not fluttering or swinging much. In a story, that kind of change can be a clue."
        )
    ],
    "foreshadow": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is when a story gives you a clue early about something important that will happen later. It helps the ending feel prepared instead of sudden."
        )
    ],
    "magic": [
        (
            "What is magic in an adventure story?",
            "Magic in an adventure story is a special power that changes the world in an unusual way, like making light or building a bridge. The best magic still has rules inside the story."
        )
    ],
}
KNOWLEDGE_ORDER = ["foreshadow", "magic", "thorns", "dark", "gap", "flute", "orb", "ribbon"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place_cfg"]
    obstacle = f["obstacle_cfg"]
    magic = f["magic_cfg"]
    treasure = f["treasure_cfg"]
    hero = f["hero"]
    friend = f["friend"]
    return [
        (
            f'Write a short adventure story for a 3-to-5-year-old that includes the word '
            f'"hang", uses dialogue, and has a magical clue that pays off later.'
        ),
        (
            f"Tell a magical adventure where {hero.id} and {friend.id} must carry a lost "
            f"{treasure.label} through {place.label}, face {obstacle.label}, and use "
            f"{magic.label} to continue."
        ),
        (
            f"Write a simple foreshadowing story where an elder says a ribbon will hang straight "
            f"when the children are near the hidden place, and later that clue comes true."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    elder = f["elder"]
    place = f["place_cfg"]
    obstacle = f["obstacle_cfg"]
    magic = f["magic_cfg"]
    treasure = f["treasure_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id}, two children on a magical adventure, and {elder.label_word} who sends them on their way."
        ),
        (
            f"What were {hero.id} and {friend.id} trying to do?",
            f"They were trying to bring the lost {treasure.label} back to {treasure.home} at {place.destination}. They hurried because the elder said its song would fade if it stayed away too long."
        ),
        (
            "What was the clue at the beginning of the story?",
            f"{elder.label_word.capitalize()} said the silver ribbon would hang straight when the hidden place was near. That clue mattered later because the children watched for it while they traveled."
        ),
        (
            f"What problem blocked their way?",
            f"They found {obstacle.label} in the path. It was dangerous because {obstacle.danger.lower()}"
        ),
        (
            f"How did they get past the problem?",
            f"{hero.id} used {magic.phrase} and {magic.qa_text}. After the obstacle was truly cleared, the path opened and they could keep going."
        ),
        (
            "How did the foreshadowing come true?",
            f"After the magic worked and they were close to the destination, the ribbon stopped fluttering and began to hang straight. That proved the elder's warning had been true all along."
        ),
        (
            "How did the story end?",
            f"They returned the {treasure.label} to its proper home, heard it sing again, and came back proud and relieved. The last image of the ribbon hanging straight shows that the journey really changed from uncertainty to safety."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"foreshadow", "magic", "ribbon"}
    obstacle = world.facts["obstacle_cfg"]
    magic = world.facts["magic_cfg"]
    if obstacle.id == "thorns":
        tags.add("thorns")
        tags.add("flute")
    elif obstacle.id == "dark":
        tags.add("dark")
        tags.add("orb")
    elif obstacle.id == "gap":
        tags.add("gap")
        tags.add("ribbon")
    if magic.id == "lullaby_flute":
        tags.add("flute")
    if magic.id == "glow_orb":
        tags.add("orb")
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:11} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  facts: near_goal={world.facts.get('near_goal')} returned={world.facts.get('returned')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="whispering_woods",
        obstacle="thorns",
        magic="lullaby_flute",
        treasure="sky_chime",
        hero="Lina",
        hero_gender="girl",
        friend="Oren",
        friend_gender="boy",
        elder="grandmother",
        hero_trait="brave",
        friend_trait="careful",
    ),
    StoryParams(
        place="moon_cave",
        obstacle="dark",
        magic="glow_orb",
        treasure="sun_key",
        hero="Milo",
        hero_gender="boy",
        friend="Nora",
        friend_gender="girl",
        elder="grandfather",
        hero_trait="steady",
        friend_trait="bright",
    ),
    StoryParams(
        place="cloud_cliff",
        obstacle="gap",
        magic="bridge_ribbon",
        treasure="feather_token",
        hero="Tara",
        hero_gender="girl",
        friend="Finn",
        friend_gender="boy",
        elder="grandmother",
        hero_trait="hopeful",
        friend_trait="careful",
    ),
    StoryParams(
        place="cloud_cliff",
        obstacle="dark",
        magic="glow_orb",
        treasure="sky_chime",
        hero="Kai",
        hero_gender="boy",
        friend="Mira",
        friend_gender="girl",
        elder="grandfather",
        hero_trait="curious",
        friend_trait="steady",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
fits_magic(O, M) :- obstacle(O), magic(M), solves_as(O, T), solves_as_magic(M, T).
valid(P, O, M)   :- place(P), obstacle(O), magic(M), affords(P, O), fits_magic(O, M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for obstacle in sorted(place.affords):
            lines.append(asp.fact("affords", pid, obstacle))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("solves_as", oid, obstacle.solve_tag))
    for mid, magic in MAGIC.items():
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("solves_as_magic", mid, magic.solve_tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        parser = build_parser()
        for s in range(10):
            params = resolve_params(parser.parse_args([]), random.Random(s))
            params.seed = s
            smoke_cases.append(params)
    except StoryError as err:
        rc = 1
        print(f"SMOKE SETUP FAILED: {err}")

    try:
        for params in smoke_cases[:8]:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("Generated empty story.")
            if "hang" not in sample.story.lower():
                raise StoryError("Generated story did not include required word 'hang'.")
            emit(sample, trace=False, qa=False)
            print("---")
        print(f"OK: smoke-tested {min(len(smoke_cases), 8)} generated stories.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Magical adventure storyworld with foreshadowing, dialogue, and a guide ribbon that will hang straight near the goal."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include QA sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (place, obstacle, magic) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    candidates = [n for n in pool if n != avoid]
    return rng.choice(candidates)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = PLACES.get(args.place) if args.place else None
    obstacle = OBSTACLES.get(args.obstacle) if args.obstacle else None
    magic = MAGIC.get(args.magic) if args.magic else None

    if place and obstacle and obstacle.id not in place.affords:
        raise StoryError(explain_rejection(place, obstacle, magic))
    if obstacle and magic and not magic_fits(obstacle, magic):
        raise StoryError(explain_rejection(place, obstacle, magic))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.magic is None or combo[2] == args.magic)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, obstacle_id, magic_id = rng.choice(combos)
    treasure_id = args.treasure or rng.choice(sorted(TREASURES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero or _pick_name(rng, hero_gender)
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    friend_name = args.friend or _pick_name(rng, friend_gender, avoid=hero_name)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    hero_trait = rng.choice(TRAITS)
    friend_trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        obstacle=obstacle_id,
        magic=magic_id,
        treasure=treasure_id,
        hero=hero_name,
        hero_gender=hero_gender,
        friend=friend_name,
        friend_gender=friend_gender,
        elder=elder,
        hero_trait=hero_trait,
        friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.magic not in MAGIC:
        raise StoryError(f"(Unknown magic: {params.magic})")
    if params.treasure not in TREASURES:
        raise StoryError(f"(Unknown treasure: {params.treasure})")

    place = PLACES[params.place]
    obstacle = OBSTACLES[params.obstacle]
    magic = MAGIC[params.magic]
    if params.obstacle not in place.affords or not magic_fits(obstacle, magic):
        raise StoryError(explain_rejection(place, obstacle, magic))

    world = tell(
        place=place,
        obstacle_cfg=obstacle,
        magic_cfg=magic,
        treasure_cfg=TREASURES[params.treasure],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        elder_type=params.elder,
        hero_trait=params.hero_trait,
        friend_trait=params.friend_trait,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, obstacle, magic) combos:\n")
        for place, obstacle, magic in combos:
            print(f"  {place:16} {obstacle:8} {magic}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero} and {p.friend}: {p.place} / {p.obstacle} / {p.magic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
