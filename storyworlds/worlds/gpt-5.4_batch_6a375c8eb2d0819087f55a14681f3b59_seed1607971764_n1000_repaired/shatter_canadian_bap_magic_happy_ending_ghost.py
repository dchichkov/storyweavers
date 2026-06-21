#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/shatter_canadian_bap_magic_happy_ending_ghost.py
=============================================================================

A standalone storyworld about a child who meets a gentle ghost in an old house.
A stormy night, a worried spirit, and a fragile keepsake create the tension.
The child listens to the ghost's clues, uses the right bit of magic, and helps
the ghost rest with a happy ending.

Seed words woven into the domain:
- shatter
- canadian
- bap

The world model tracks physical state (cracks, wind, glow, safety) and emotional
state (fear, trust, relief, belonging). A reasonableness gate only allows magic
that actually fits the threatened object and the kind of trouble. The ASP twin
mirrors that gate and the outcome model.

Run it
------
    python storyworlds/worlds/gpt-5.4/shatter_canadian_bap_magic_happy_ending_ghost.py
    python storyworlds/worlds/gpt-5.4/shatter_canadian_bap_magic_happy_ending_ghost.py --place attic --keepsake snow_globe
    python storyworlds/worlds/gpt-5.4/shatter_canadian_bap_magic_happy_ending_ghost.py --keepsake quilt_patch
    python storyworlds/worlds/gpt-5.4/shatter_canadian_bap_magic_happy_ending_ghost.py --all
    python storyworlds/worlds/gpt-5.4/shatter_canadian_bap_magic_happy_ending_ghost.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/shatter_canadian_bap_magic_happy_ending_ghost.py --verify
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
    material: str = ""
    fragile: bool = False
    # physical + emotional state
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "ghost_girl"}
        male = {"boy", "father", "man", "ghost_boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Place:
    id: str
    label: str
    moonlight: str
    hiding_spot: str
    echo: str
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
class Keepsake:
    id: str
    label: str
    phrase: str
    material: str
    danger: str
    threat_line: str
    memory: str
    sound: str
    plural: bool = False
    fragile: bool = True
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
class MagicAid:
    id: str
    label: str
    phrase: str
    verb: str
    use_line: str
    fixes_materials: set[str] = field(default_factory=set)
    sense: int = 2
    power: int = 2
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
class Spirit:
    id: str
    label: str
    type: str
    whisper: str
    wish: str
    relation_line: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_rattle(world: World) -> list[str]:
    out: list[str] = []
    keepsake = world.get("keepsake")
    room = world.get("room")
    child = world.get("child")
    spirit = world.get("spirit")
    if room.meters["wind"] < THRESHOLD or keepsake.meters["at_risk"] < THRESHOLD:
        return out
    sig = ("rattle", keepsake.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    keepsake.meters["rattling"] += 1
    keepsake.meters["danger"] += 1
    child.memes["fear"] += 1
    spirit.memes["worry"] += 1
    out.append("__rattle__")
    return out


def _r_shatter(world: World) -> list[str]:
    out: list[str] = []
    keepsake = world.get("keepsake")
    room = world.get("room")
    if keepsake.meters["rattling"] < THRESHOLD:
        return out
    if room.meters["wind"] < 2.0:
        return out
    if keepsake.meters["protected"] >= THRESHOLD:
        return out
    sig = ("shatter", keepsake.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    keepsake.meters["shattered"] += 1
    keepsake.meters["danger"] += 1
    room.meters["sadness"] += 1
    out.append("__shatter__")
    return out


def _r_comfort(world: World) -> list[str]:
    out: list[str] = []
    spirit = world.get("spirit")
    child = world.get("child")
    keepsake = world.get("keepsake")
    if keepsake.meters["mended"] < THRESHOLD:
        return out
    sig = ("comfort", spirit.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    spirit.memes["peace"] += 1
    child.memes["bravery"] += 1
    child.memes["relief"] += 1
    out.append("__comfort__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="rattle", tag="physical", apply=_r_rattle),
    Rule(name="shatter", tag="physical", apply=_r_shatter),
    Rule(name="comfort", tag="social", apply=_r_comfort),
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
        for s in produced:
            world.say(s)
    return produced


def magic_fits(aid: MagicAid, keepsake: Keepsake) -> bool:
    return keepsake.material in aid.fixes_materials


def sensible_aids() -> list[MagicAid]:
    return [aid for aid in MAGIC.values() if aid.sense >= SENSE_MIN]


def storm_severity(place: Place, draft: int) -> int:
    base = 1 if place.id in {"attic", "greenhouse"} else 0
    return base + draft


def can_save(aid: MagicAid, place: Place, draft: int) -> bool:
    return aid.power >= storm_severity(place, draft)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_aids():
        return combos
    for place_id in PLACES:
        for keepsake_id, keepsake in KEEPSAKES.items():
            for aid_id, aid in MAGIC.items():
                if magic_fits(aid, keepsake) and aid.sense >= SENSE_MIN:
                    combos.append((place_id, keepsake_id, aid_id))
    return combos


def predict_break(world: World) -> dict:
    sim = world.copy()
    sim.get("room").meters["wind"] += 1
    propagate(sim, narrate=False)
    return {
        "rattling": sim.get("keepsake").meters["rattling"] >= THRESHOLD,
        "shattered": sim.get("keepsake").meters["shattered"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, parent: Entity, place: Place) -> None:
    world.say(
        f"On a windy night, {child.id} stayed with {child.pronoun('possessive')} "
        f"{parent.label_word} in an old house. {place.moonlight}"
    )
    world.say(
        f"The house was not mean, only full of hush and {place.echo}."
    )


def hear_bap(world: World, child: Entity, keepsake: Keepsake, place: Place) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Just as the lamp was turned low, a soft sound came from {place.hiding_spot}: "
        f'"bap... bap... bap."'
    )
    world.say(
        f"It was the sound of {keepsake.sound}, as if something small was asking not to be forgotten."
    )


def reveal_spirit(world: World, child: Entity, spirit: Entity, spirit_cfg: Spirit) -> None:
    child.memes["fear"] += 1
    spirit.memes["lonely"] += 1
    world.say(
        f"{child.id} peeked closer and saw a pale little {spirit_cfg.label} rise out of the dimness, "
        f"silver at the edges like moonlit fog."
    )
    world.say(
        f'"{spirit_cfg.whisper}" {spirit.pronoun()} whispered. {spirit_cfg.relation_line}'
    )


def show_keepsake(world: World, spirit: Entity, keepsake_ent: Entity, keepsake_cfg: Keepsake) -> None:
    keepsake_ent.meters["at_risk"] += 1
    world.say(
        f"In {spirit.pronoun('possessive')} hands floated {keepsake_cfg.phrase}. "
        f"{keepsake_cfg.threat_line}"
    )


def warn_of_storm(world: World, child: Entity, place: Place) -> None:
    pred = predict_break(world)
    world.facts["predicted_rattle"] = pred["rattling"]
    world.facts["predicted_shatter"] = pred["shattered"]
    if pred["shattered"]:
        world.say(
            f"{child.id} looked up at the shaking boards and knew the next hard gust could make it shatter."
        )
    else:
        world.say(
            f"{child.id} could tell the storm was making the room tremble, and the keepsake would not stay safe by itself."
        )


def fetch_magic(world: World, child: Entity, aid: MagicAid) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"{child.id} remembered {aid.phrase} in a drawer nearby and took it out with careful hands."
    )
    world.say(aid.use_line)


def cast_magic(world: World, child: Entity, spirit: Entity, aid: MagicAid, keepsake_ent: Entity) -> None:
    keepsake_ent.meters["protected"] += 1
    keepsake_ent.meters["mended"] += 1
    keepsake_ent.meters["glow"] += 1
    keepsake_ent.meters["danger"] = 0.0
    world.get("room").meters["wind"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"When {child.id} {aid.verb}, soft light gathered around the keepsake like warm breath on a winter window."
    )
    world.say(
        f"The trembling stopped. Even the dark corners seemed to lean closer and listen."
    )
    spirit.memes["trust"] += 1


def farewell(world: World, child: Entity, spirit: Entity, keepsake_cfg: Keepsake, spirit_cfg: Spirit) -> None:
    spirit.memes["relief"] += 1
    child.memes["wonder"] += 1
    world.say(
        f'The little {spirit_cfg.label} smiled. "{keepsake_cfg.memory} Now it will stay," {spirit.pronoun()} said.'
    )
    world.say(
        f"{spirit.pronoun().capitalize()} grew brighter and less lonely, as if the house had been waiting a very long time for someone to listen."
    )


def happy_ending(world: World, child: Entity, parent: Entity, keepsake_cfg: Keepsake) -> None:
    child.memes["belonging"] += 1
    world.say(
        f"In the morning, {child.id} told {child.pronoun('possessive')} {parent.label_word} about the night. "
        f"{parent.label_word.capitalize()} found {keepsake_cfg.phrase} exactly where the moonlight had faded, safe and whole."
    )
    world.say(
        f"They placed it on a sturdy shelf, and the old house felt gentle after that. "
        f"Now when the wind passed by, it made no frightened bap at all, only a sleepy sigh."
    )
    world.say(
        f"{child.id} always remembered that some ghost stories end not with fear, but with kindness."
    )


def failed_magic(world: World, child: Entity, spirit: Entity, keepsake_cfg: Keepsake) -> None:
    room = world.get("room")
    room.meters["wind"] = 2.0
    propagate(world, narrate=False)
    child.memes["fear"] += 1
    spirit.memes["grief"] += 1
    world.say(
        f"But the storm was too strong. The keepsake slipped, flashed once, and seemed ready to shatter in the dark."
    )
    if world.get("keepsake").meters["shattered"] >= THRESHOLD:
        world.say(
            f"The room gave a sad little gasp as the {keepsake_cfg.label} broke apart."
        )


def gentle_repair_after_break(world: World, child: Entity, spirit: Entity, keepsake_cfg: Keepsake) -> None:
    keepsake_ent = world.get("keepsake")
    keepsake_ent.meters["shattered"] = 0.0
    keepsake_ent.meters["mended"] += 1
    keepsake_ent.meters["glow"] += 1
    keepsake_ent.meters["protected"] += 1
    world.get("room").meters["wind"] = 0.0
    spirit.memes["peace"] += 1
    child.memes["relief"] += 1
    world.say(
        f"{child.id} did not run. Instead, {child.pronoun()} gathered the shining pieces and whispered the ghost's name until the cracks drew together like threads being sewn."
    )
    world.say(
        f"Soon the {keepsake_cfg.label} was whole again, brighter than before, and the house felt warm clear through."
    )


def tell(
    place: Place,
    keepsake_cfg: Keepsake,
    aid: MagicAid,
    spirit_cfg: Spirit,
    *,
    child_name: str = "Nora",
    child_type: str = "girl",
    parent_type: str = "mother",
    draft: int = 1,
) -> World:
    world = World(place)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        role="child",
        traits=["careful", "kind"],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    spirit = world.add(Entity(
        id="spirit",
        kind="character",
        type=spirit_cfg.type,
        role="spirit",
        label=spirit_cfg.label,
        attrs={"wish": spirit_cfg.wish},
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label=place.label,
        attrs={"draft": draft},
    ))
    room.meters["wind"] = float(storm_severity(place, draft))
    keepsake_ent = world.add(Entity(
        id="keepsake",
        type="keepsake",
        label=keepsake_cfg.label,
        material=keepsake_cfg.material,
        fragile=keepsake_cfg.fragile,
    ))

    world.facts.update(
        place=place,
        keepsake_cfg=keepsake_cfg,
        aid=aid,
        spirit_cfg=spirit_cfg,
        draft=draft,
        child_name=child_name,
    )

    introduce(world, child, parent, place)
    hear_bap(world, child, keepsake_cfg, place)

    world.para()
    reveal_spirit(world, child, spirit, spirit_cfg)
    show_keepsake(world, spirit, keepsake_ent, keepsake_cfg)
    warn_of_storm(world, child, place)

    world.para()
    fetch_magic(world, child, aid)
    saved = can_save(aid, place, draft)

    if saved:
        cast_magic(world, child, spirit, aid, keepsake_ent)
        farewell(world, child, spirit, keepsake_cfg, spirit_cfg)
        world.para()
        happy_ending(world, child, parent, keepsake_cfg)
        outcome = "saved"
    else:
        failed_magic(world, child, spirit, keepsake_cfg)
        world.para()
        gentle_repair_after_break(world, child, spirit, keepsake_cfg)
        farewell(world, child, spirit, keepsake_cfg, spirit_cfg)
        world.para()
        happy_ending(world, child, parent, keepsake_cfg)
        outcome = "mended_after_break"

    world.facts.update(
        child=child,
        parent=parent,
        spirit=spirit,
        room=room,
        keepsake=keepsake_ent,
        outcome=outcome,
        shattered=keepsake_ent.meters["shattered"] >= THRESHOLD,
        mended=keepsake_ent.meters["mended"] >= THRESHOLD,
        protected=keepsake_ent.meters["protected"] >= THRESHOLD,
        saved=(outcome == "saved"),
    )
    return world


PLACES = {
    "attic": Place(
        id="attic",
        label="the attic",
        moonlight="Moonlight lay across the attic floor in thin silver boards.",
        hiding_spot="an old cedar trunk",
        echo="small creaks from the rafters",
        tags={"attic", "ghost"},
    ),
    "hallway": Place(
        id="hallway",
        label="the upstairs hallway",
        moonlight="A strip of moonlight reached along the hallway runner like a pale ribbon.",
        hiding_spot="the little table under the stairs",
        echo="soft tapping from the picture frames",
        tags={"hallway", "ghost"},
    ),
    "greenhouse": Place(
        id="greenhouse",
        label="the glass greenhouse",
        moonlight="Moonlight gleamed on the greenhouse panes until the whole place looked underwater.",
        hiding_spot="a wicker chair by the fern shelf",
        echo="tiny leaf-rustles against the glass",
        tags={"greenhouse", "ghost"},
    ),
}

KEEPSAKES = {
    "snow_globe": Keepsake(
        id="snow_globe",
        label="snow globe",
        phrase="a canadian snow globe with a tiny red cabin inside",
        material="glass",
        danger="The thin globe clicked against the trunk lid every time the house shook.",
        threat_line="One more hard bump and the glass might shatter.",
        memory="My grandmother brought this from a canadian winter fair",
        sound="glass tapping against wood",
        tags={"glass", "canadian", "snow"},
    ),
    "star_locket": Keepsake(
        id="star_locket",
        label="star locket",
        phrase="a silver star locket on a worn blue ribbon",
        material="metal",
        danger="The clasp had sprung loose, and it kept knocking the wall.",
        threat_line="If it flew open in the storm, the picture inside could be lost.",
        memory="It holds the last little portrait my family tucked inside",
        sound="metal kissing plaster",
        tags={"metal", "memory"},
    ),
    "quilt_patch": Keepsake(
        id="quilt_patch",
        label="quilt patch",
        phrase="a quilt patch stitched with tiny maple leaves",
        material="cloth",
        danger="The old cloth fluttered so wildly that the seam was beginning to pull.",
        threat_line="Another tug and the little patch could tear away for good.",
        memory="It came from the blanket I used when I was alive",
        sound="cloth patting wood",
        tags={"cloth", "maple"},
    ),
}

MAGIC = {
    "moon_glue": MagicAid(
        id="moon_glue",
        label="moon glue",
        phrase="a jar of moon glue",
        verb="drew a shining line of moon glue around each crack",
        use_line="The glue shone like milk in starlight and smelled faintly of mint.",
        fixes_materials={"glass", "metal"},
        sense=3,
        power=2,
        tags={"repair", "magic"},
    ),
    "hush_song": MagicAid(
        id="hush_song",
        label="hush song",
        phrase="the old hush song written inside a music book",
        verb="sang the hush song in a low brave voice",
        use_line="The notes floated up softly, and even the wind seemed to hold still to hear them.",
        fixes_materials={"cloth", "paper"},
        sense=3,
        power=2,
        tags={"song", "magic"},
    ),
    "star_thread": MagicAid(
        id="star_thread",
        label="star thread",
        phrase="a spool of star thread",
        verb="looped the star thread through the air with careful fingers",
        use_line="Each strand glimmered like frost and moved as if it already knew what belonged together.",
        fixes_materials={"cloth", "metal"},
        sense=2,
        power=1,
        tags={"thread", "magic"},
    ),
    "candle_wish": MagicAid(
        id="candle_wish",
        label="candle wish",
        phrase="a candle wish whispered over a sleepy flame",
        verb="made a candle wish and blew warm gold across the object",
        use_line="It looked pretty, but wishes alone were weak against rough weather.",
        fixes_materials={"glass"},
        sense=1,
        power=1,
        tags={"wish", "magic"},
    ),
}

SPIRITS = {
    "lost_girl": Spirit(
        id="lost_girl",
        label="ghost girl",
        type="ghost_girl",
        whisper="Please help me keep one good thing from the storm",
        wish="keep the family keepsake safe",
        relation_line="She did not lunge or moan. She only looked worried, like a child who had been left holding something precious for far too long.",
        tags={"ghost", "kind"},
    ),
    "lost_boy": Spirit(
        id="lost_boy",
        label="ghost boy",
        type="ghost_boy",
        whisper="I do not want my memory to blow away",
        wish="keep the memory safe",
        relation_line="He seemed more lonely than scary, and the air around him smelled faintly of rain and old cedar.",
        tags={"ghost", "kind"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lily", "Ava", "Zoe", "Ella", "Anna", "Ruby"]
BOY_NAMES = ["Eli", "Tom", "Ben", "Max", "Finn", "Theo", "Noah", "Leo"]


@dataclass
class StoryParams:
    place: str
    keepsake: str
    magic: str
    spirit: str
    child_name: str
    child_type: str
    parent: str
    draft: int = 1
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
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a tale about a spirit or a haunting. In gentle ghost stories, the ghost is often sad or lonely instead of mean.",
        )
    ],
    "glass": [
        (
            "Why can glass shatter?",
            "Glass is hard, but it can also be brittle. A strong bump or a sudden force can make it crack or shatter into pieces.",
        )
    ],
    "snow": [
        (
            "What is a snow globe?",
            "A snow globe is a glass ball with a tiny scene inside. When you shake it, white flakes drift down like snow.",
        )
    ],
    "canadian": [
        (
            "What does canadian mean?",
            "Canadian means something comes from Canada or belongs to Canada. A canadian snow globe would be a snow globe from that country.",
        )
    ],
    "metal": [
        (
            "Why do lockets matter to people?",
            "A locket is often special because it can hold a tiny picture or keepsake inside. People keep them close because they carry memories.",
        )
    ],
    "cloth": [
        (
            "Why can old cloth tear?",
            "Old cloth can become weak after a long time. If it pulls too hard, the threads can come apart and tear.",
        )
    ],
    "magic": [
        (
            "What is magic in a story?",
            "Magic in a story is a special power that can change things in ways real life usually cannot. It often helps show love, courage, or hope.",
        )
    ],
    "repair": [
        (
            "Why is fixing something kind?",
            "Fixing something kind means you care about what matters to someone else. It can turn fear into relief because the precious thing is safe again.",
        )
    ],
    "song": [
        (
            "Why can a song feel comforting?",
            "A soft song can help people feel calm and less alone. In stories, a song can also carry memory and love.",
        )
    ],
    "thread": [
        (
            "What does thread do?",
            "Thread is used to join pieces of cloth together. It can help mend a tear so the fabric stays whole.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "glass", "snow", "canadian", "metal", "cloth", "magic", "repair", "song", "thread"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    keepsake = f["keepsake_cfg"]
    aid = f["aid"]
    spirit_cfg = f["spirit_cfg"]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the words "shatter", "canadian", and "bap".',
        f"Tell a magic story where {child.id} hears a quiet bap in {place.label} and meets a {spirit_cfg.label} trying to save {keepsake.phrase}.",
        f"Write a child-facing ghost story with a happy ending where the right kind of magic helps protect a fragile keepsake instead of letting it shatter, using {aid.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    spirit = f["spirit"]
    keepsake_cfg = f["keepsake_cfg"]
    aid = f["aid"]
    place = f["place"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child in an old house, and a gentle {spirit.label} who was trying to protect {keepsake_cfg.phrase}. They meet because a strange bap sound leads {child.id} to the ghost.",
        ),
        (
            "What was making the bap sound?",
            f"The bap sound came from the threatened keepsake moving and tapping in {place.hiding_spot}. The storm made it knock softly as if it were asking for help.",
        ),
        (
            f"Why was the {spirit.label} worried?",
            f"The ghost was worried that the {keepsake_cfg.label} would be ruined. It mattered because {keepsake_cfg.memory.lower()}.",
        ),
        (
            f"Why did {child.id} think it might shatter or break?",
            f"{child.id} saw that the storm was shaking the room and the keepsake was already at risk. That made {child.pronoun('object')} realize one more hard gust could do real damage.",
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                f"How did {child.id} help the ghost?",
                f"{child.id} used {aid.label} because it fit the kind of keepsake that was in danger. The magic calmed the shaking, protected the object, and let the ghost finally feel peaceful.",
            )
        )
    else:
        qa.append(
            (
                f"What happened before the ending became happy?",
                f"For a moment, the storm was too strong and the keepsake seemed ready to break. But {child.id} stayed brave, gathered the shining pieces, and helped mend it instead of running away.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended happily because the keepsake was safe and the ghost was no longer lonely. In the morning, {parent.label_word} found it whole, and the house felt gentle instead of troubled.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"ghost", "magic"}
    keepsake_cfg = world.facts["keepsake_cfg"]
    aid = world.facts["aid"]
    tags |= set(keepsake_cfg.tags)
    tags |= set(aid.tags)
    if "canadian" in keepsake_cfg.tags:
        tags.add("canadian")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.material:
            bits.append(f"material={ent.material}")
        if ent.fragile:
            bits.append("fragile=True")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(keepsake: Keepsake, aid: MagicAid) -> str:
    if aid.sense < SENSE_MIN:
        return (
            f"(No story: {aid.label} is known in this world, but it is too flimsy to trust. "
            f"Pick a sturdier magic aid for a child-facing happy ending.)"
        )
    return (
        f"(No story: {aid.label} does not truly fit a {keepsake.label}. "
        f"The magic must match the material in danger, or the rescue would feel false.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.place not in PLACES or params.keepsake not in KEEPSAKES or params.magic not in MAGIC:
        return "?"
    return "saved" if can_save(MAGIC[params.magic], PLACES[params.place], params.draft) else "mended_after_break"


ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
fit(M,K) :- magic(M), keepsake(K), fixes(M,Mat), made_of(K,Mat).
sensible(M) :- magic(M), sense(M,S), sense_min(Min), S >= Min.
valid(P,K,M) :- place(P), keepsake(K), magic(M), fit(M,K), sensible(M).

% --- outcome model ---------------------------------------------------------
storm(P,D,Base + D) :- chosen_place(P), draft(D), draft_base(P,Base).
saved :- chosen_magic(M), power(M,Pwr), chosen_place(P), draft(D), storm(P,D,Need), Pwr >= Need.
outcome(saved) :- saved.
outcome(mended_after_break) :- not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pid, place in PLACES.items():
        base = 1 if place.id in {"attic", "greenhouse"} else 0
        lines.append(asp.fact("draft_base", pid, base))
    for kid, keepsake in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", kid))
        lines.append(asp.fact("made_of", kid, keepsake.material))
    for mid, aid in MAGIC.items():
        lines.append(asp.fact("magic", mid))
        for mat in sorted(aid.fixes_materials):
            lines.append(asp.fact("fixes", mid, mat))
        lines.append(asp.fact("sense", mid, aid.sense))
        lines.append(asp.fact("power", mid, aid.power))
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
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_magic", params.magic),
            asp.fact("draft", params.draft),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


CURATED = [
    StoryParams(
        place="attic",
        keepsake="snow_globe",
        magic="moon_glue",
        spirit="lost_girl",
        child_name="Nora",
        child_type="girl",
        parent="mother",
        draft=1,
    ),
    StoryParams(
        place="hallway",
        keepsake="star_locket",
        magic="moon_glue",
        spirit="lost_boy",
        child_name="Eli",
        child_type="boy",
        parent="father",
        draft=1,
    ),
    StoryParams(
        place="greenhouse",
        keepsake="quilt_patch",
        magic="hush_song",
        spirit="lost_girl",
        child_name="Ruby",
        child_type="girl",
        parent="mother",
        draft=2,
    ),
    StoryParams(
        place="attic",
        keepsake="quilt_patch",
        magic="star_thread",
        spirit="lost_boy",
        child_name="Finn",
        child_type="boy",
        parent="father",
        draft=1,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a gentle ghost, the right magic, and a happy ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--spirit", choices=SPIRITS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--draft", type=int, choices=[0, 1, 2], help="how hard the storm pushes through the room")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.keepsake and args.magic:
        keepsake = KEEPSAKES[args.keepsake]
        aid = MAGIC[args.magic]
        if not magic_fits(aid, keepsake) or aid.sense < SENSE_MIN:
            raise StoryError(explain_rejection(keepsake, aid))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.keepsake is None or combo[1] == args.keepsake)
        and (args.magic is None or combo[2] == args.magic)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, keepsake_id, magic_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    spirit = args.spirit or rng.choice(sorted(SPIRITS))
    parent = args.parent or rng.choice(["mother", "father"])
    draft = args.draft if args.draft is not None else rng.randint(0, 2)

    return StoryParams(
        place=place,
        keepsake=keepsake_id,
        magic=magic_id,
        spirit=spirit,
        child_name=child_name,
        child_type=gender,
        parent=parent,
        draft=draft,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.keepsake not in KEEPSAKES:
        raise StoryError(f"(Unknown keepsake: {params.keepsake})")
    if params.magic not in MAGIC:
        raise StoryError(f"(Unknown magic aid: {params.magic})")
    if params.spirit not in SPIRITS:
        raise StoryError(f"(Unknown spirit: {params.spirit})")
    keepsake_cfg = KEEPSAKES[params.keepsake]
    aid = MAGIC[params.magic]
    if not magic_fits(aid, keepsake_cfg) or aid.sense < SENSE_MIN:
        raise StoryError(explain_rejection(keepsake_cfg, aid))

    world = tell(
        PLACES[params.place],
        keepsake_cfg,
        aid,
        SPIRITS[params.spirit],
        child_name=params.child_name,
        child_type=params.child_type,
        parent_type=params.parent,
        draft=params.draft,
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


def asp_verify() -> int:
    rc = 0

    python_gate = set(valid_combos())
    clingo_gate = set(asp_valid_combos())
    if python_gate == clingo_gate:
        print(f"OK: gate matches valid_combos() ({len(python_gate)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_gate - python_gate:
            print("  only in clingo:", sorted(clingo_gate - python_gate))
        if python_gate - clingo_gate:
            print("  only in python:", sorted(python_gate - clingo_gate))

    python_sense = {aid.id for aid in sensible_aids()}
    clingo_sense = set(asp_sensible())
    if python_sense == clingo_sense:
        print(f"OK: sensible magic aids match ({sorted(python_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible magic aids: clingo={sorted(clingo_sense)} python={sorted(python_sense)}")

    cases = list(CURATED)
    for s in range(60):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        p.seed = s
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sensible = asp_sensible()
        combos = asp_valid_combos()
        print(f"sensible magic aids: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (place, keepsake, magic) combos:\n")
        for place, keepsake, magic in combos:
            print(f"  {place:10} {keepsake:12} {magic}")
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
            header = f"### {p.child_name}: {p.keepsake} in {p.place} with {p.magic} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
