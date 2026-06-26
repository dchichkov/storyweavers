#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/collide_suspense_bravery_magic_tall_tale.py
==============================================================================================================

A standalone *story world* sketch built from the seed word "collide" and the
mood ingredients Suspense, Bravery, and Magic, told in a Tall Tale register.

Initial story (the source tale this world model is built from):
---
Way out past the cabbage patch and the leaning silo of the Tucker farm,
there lived a boy named Otis Buckholt who could hear the wind coming three
hours before it arrived.  Folks said Otis was seven, maybe eight, but nobody
could be sure, because every time you asked him his age he'd tell you he
was as old as the thunder he had outrun.

Now the trouble in those parts was the Tin Bell.  The Tin Bell hung on a
rope between two old fence posts at the crossroads, and it was so heavy and
so loud that when the wind blew hard it would swing and COLLIDE against the
posts with a clang that could crack a wagon spoke and pop a barn door
shutter.  Whenever the Bell collided, the cattle bolted, the chickens went
silent, and the wind itself seemed to lean sideways to listen.

One evening, just as Mama Buckholt was wringing out the dish rag, the
candles along the porch all turned blue at the same time, and the air
smelled of wet iron.  "Otis," she said, in the careful voice she saved for
storms, "the Bell is going to swing tonight, and swing hard."  Otis
nodded, because he had already felt the wind turning under the floorboards
like a dog getting up from a nap.

Out across the dark field, something silver was racing toward the
crossroads, low and quick, leaving a thin scar of sparks in the tall grass.
It was a cyclone in a bottle, a thing that did not belong in any bottle,
and it had escaped from a travelling magician named Mr. Quill, who was
chasing it down the road with his hat in his hand and his words all
tangled.  The little storm streaked straight for the Tin Bell, and if it
hit, the Bell would collide with both posts at once and the whole farm
would shake itself apart.

Otis did not wait to be told twice.  He grabbed the magic ribbon his
grandmother had sewn into the lining of his coat (a strip of cloth that
could hold a wish the way a jar holds a firefly), and he ran.  His boots
hit the grass in time with his heart, thump-thump, thump-thump, and the
grass leaned back to let him by, because even grass knew that Otis was the
bravest boy in that county and maybe the next one over.

He reached the crossroads just as the little cyclone reached the Bell.  He
threw the ribbon up like a lasso, and the ribbon looped around the Bell's
tongue and around the cyclone both, so when the wind tried to make them
COLLIDE they instead swung together like dancers learning a new step.
The Bell rang, but soft and silver, and the cattle lay down, and the
chickens opened one eye and went back to sleep.

Mr. Quill came puffing up the road, hatless now and laughing, and he said
Otis had done a braver thing than he had ever seen a grown magician do.  He
taught Otis three little words of magic that night by the kitchen fire,
and from then on, whenever the Tin Bell swung, it swung in time with the
boy who had caught the storm.

This script models that tale.  It is a *classical* simulation: it spins up a
world with a few typed characters, a swinging bell, a rogue mini-cyclone,
and a magic ribbon; it forward-chains the physical and emotional effects
of those entities colliding (and not colliding); and it lets the simulated
state drive the prose.
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

# Make the shared result containers importable when this script is run directly
# (``python storyworlds/worlds/.../collide_..._tall_tale.py``): add the package
# dir (storyworlds/) to the path so ``results`` resolves regardless of cwd.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# Collision outcomes -- which kinds of clash we recognise in this world.
CLASH_KINDS = {"clang", "spark", "boom", "ring"}

# Object categories used by the gear/coverage constraint.
OBJECT_KINDS = {"bell", "bottle", "ribbon", "post", "cyclone"}


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation, so the
# same forward-chainer can reason about people and about a Tin Bell.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # boy, girl, mother, father, bell, cyclone ...
    label: str = ""                # short reference, e.g. "Tin Bell", "ribbon"
    phrase: str = ""               # full noun phrase
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    magical: bool = False          # can it hold a wish or do magic work?
    wish_slots: int = 0            # for ribbon-like objects: how many wishes fit
    guards: set[str] = field(default_factory=set)   # clash kinds it neutralises
    anchor: bool = False           # a fixed object the bell hangs on (a post)
    moving: bool = False           # cyclone-like: it is the moving thing
    belt: set[str] = field(default_factory=set)    # objects it ties together
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "magician_woman"}
        male = {"boy", "father", "dad", "man", "magician_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad",
                "magician_man": "the magician",
                "magician_woman": "the magician"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the crossroads"
    weather: str = "windy"         # "windy" | "stormy" | "still"
    bell_kind: str = "tin"         # "tin" | "bronze" | "silver"
    affords: set[str] = field(default_factory=set)


@dataclass
class Storm:
    """The little cyclone-in-a-bottle that escapes and races toward the Bell."""
    id: str
    kind: str = "cyclone"          # "cyclone" | "whirlwind" | "dust devil"
    noun: str                      # "a cyclone in a bottle"
    rush: str                      # "raced straight for the Bell"
    speed: float = 1.0             # how violently it meets the Bell
    spark: bool = True             # does it leave sparks in the grass
    belong_to: str = "bottle"      # what it should be inside of, normally


@dataclass
class Hero:
    """The brave child who can hear the wind coming hours before it arrives."""
    id: str
    type: str                      # "boy" | "girl"
    noun: str                      # "a boy named Otis"
    trait: str                     # "bravest boy in the county"
    sense: str                     # "could hear the wind coming three hours early"
    verb_listen: str               # "had already felt the wind turning"
    coat: str                      # "his coat" -- where the magic ribbon lives


@dataclass
class Ribbon:
    """The grandmother's magic ribbon: holds a wish the way a jar holds a firefly."""
    id: str
    label: str                     # "magic ribbon"
    phrase: str                    # "a strip of cloth from his grandmother"
    prep: str                      # "throw the ribbon up like a lasso"
    tail: str                      # "the ribbon looped around the Bell and the storm"
    wishes: int = 1                # how many wishes it can hold


@dataclass
class Mage:
    """The travelling magician who lost the bottle and praised the boy's bravery."""
    id: str
    type: str                      # "magician_man" | "magician_woman"
    label: str                     # "Mr. Quill"
    phrase: str                    # "a travelling magician with his hat in his hand"
    teach: str                     # "taught Otis three little words of magic"


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()       # idempotency for the rule engine
        self.paragraphs: list[list[str]] = [[]]
        self.belt: set[tuple[str, str]] = set()    # (a, b) pairs bound by the ribbon
        # Facts recorded during the screenplay, read back by the Q&A generators.
        self.facts: dict = {}

    # -- entity helpers -----------------------------------------------------
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def carried_by(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]

    # -- narration helpers --------------------------------------------------
    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        """Throwaway clone used for forward-simulation (prediction)."""
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.belt = set(self.belt)
        clone.paragraphs = [[]]            # predictions are silent
        return clone


# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_bell_clang(world: World) -> list[str]:
    """Bell wind >= 1 -> the Bell swings and collides with the post (clang)."""
    out: list[str] = []
    bell = world.entities.get("bell")
    post = world.entities.get("post")
    if bell is None or post is None:
        return out
    if bell.meters["wind"] < THRESHOLD:
        return out
    sig = ("clang", bell.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bell.meters["clang"] += 1
    bell.meters["swing"] += 1
    out.append(
        f"the {world.setting.bell_kind} Bell {bell.label_word_swing()} "
        "and collided with the post with a clang that could pop a barn shutter."
    )
    return out


def _r_bell_boom(world: World) -> list[str]:
    """Two clangs (Bell hitting both posts) without a ribbon -> farm shakes (boom)."""
    bell = world.entities.get("bell")
    post = world.entities.get("post")
    if bell is None or post is None:
        return []
    if bell.meters["clang"] < 2:
        return []
    if any(e.magical and "boom" in e.guards and e.belt
           for e in world.entities.values()):
        return []                          # the ribbon (or similar) prevents the boom
    sig = ("boom", bell.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bell.meters["boom"] += 1
    return ["__boom__"]                    # marker; narrated by the screenplay beat


def _r_cyclone_spark(world: World) -> list[str]:
    """A moving cyclone in the open -> spark in the grass."""
    out: list[str] = []
    for ent in world.entities.values():
        if not ent.moving or ent.meters["arrive"] < THRESHOLD:
            continue
        sig = ("spark", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["spark"] += 1
        out.append(
            f"the little {ent.type} streaked past leaving a thin scar of "
            f"sparks in the tall grass."
        )
    return out


def _r_ribbon_belt(world: World) -> list[str]:
    """A magical ribbon looped around (bell, cyclone) -> binds them on the belt."""
    out: list[str] = []
    ribbon = world.entities.get("ribbon")
    bell = world.entities.get("bell")
    storm = None
    for e in world.entities.values():
        if e.moving:
            storm = e
            break
    if ribbon is None or bell is None or storm is None:
        return out
    if not (ribbon.carried_by and ribbon.magical and ribbon.wish_slots >= 1):
        return out
    if storm.meters["arrive"] < THRESHOLD:
        return out
    sig = ("belt", ribbon.id, bell.id, storm.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ribbon.belt.update({bell.id, storm.id})
    world.belt.add((bell.id, storm.id))
    bell.meters["bound"] += 1
    storm.meters["bound"] += 1
    return [
        f"the ribbon looped around the Bell and the {storm.type} both, "
        f"so when the wind tried to make them collide they instead swung "
        f"together like dancers learning a new step."
    ]


def _r_bell_ring_soft(world: World) -> list[str]:
    """A bound Bell rings soft instead of clanging -- the cattle can rest."""
    bell = world.entities.get("bell")
    if bell is None:
        return []
    if bell.meters["bound"] < THRESHOLD:
        return []
    if bell.meters["soft_ring"] >= THRESHOLD:
        return []
    sig = ("ring", bell.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bell.meters["soft_ring"] += 1
    return [
        "the Bell rang, but soft and silver, and the cattle lay back down."
    ]


def _r_bravery(world: World) -> list[str]:
    """A hero who ran out into the dark while scared-but-brave -> bravery meter."""
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["ran_out"] < THRESHOLD or actor.memes["scared"] < THRESHOLD:
            continue
        sig = ("bravery", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["bravery"] += 1
    return out


def _r_praise(world: World) -> list[str]:
    """Magician sees a brave child's bravery meter -> praise, and a teach beat."""
    out: list[str] = []
    mage = None
    hero = None
    for e in world.characters():
        if e.type.startswith("magician"):
            mage = e
        elif e.type in {"boy", "girl"}:
            hero = e
    if mage is None or hero is None:
        return out
    if hero.memes["bravery"] < THRESHOLD:
        return out
    sig = ("praise", mage.id, hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["praised"] += 1
    hero.memes["taught_magic"] += 1
    out.append("__praise__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="bell_clang", tag="physical", apply=_r_bell_clang),
    Rule(name="bell_boom", tag="physical", apply=_r_bell_boom),
    Rule(name="cyclone_spark", tag="physical", apply=_r_cyclone_spark),
    Rule(name="ribbon_belt", tag="magic", apply=_r_ribbon_belt),
    Rule(name="bell_ring_soft", tag="magic", apply=_r_bell_ring_soft),
    Rule(name="bravery", tag="social", apply=_r_bravery),
    Rule(name="praise", tag="social", apply=_r_praise),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    """Apply all rules until nothing new fires (forward chaining to fixpoint)."""
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__boom__" and s != "__praise__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers -- what is a *reasonable* conflict and a *reasonable* fix.
# ---------------------------------------------------------------------------
def storm_targets_bell(storm: Storm) -> bool:
    """Would this storm be racing toward the Tin Bell if it got free?"""
    return storm.id in {"cyclone", "whirlwind", "dust devil"}


def select_ribbon(hero: Hero, ribbon: Ribbon) -> Optional[Ribbon]:
    """A reasonable fix: a magical ribbon with at least one wish slot left."""
    return ribbon if ribbon.magical and ribbon.wishes >= 1 else None


def predict_shakeout(world: World, storm: Storm) -> dict:
    """Simulate the storm arriving silently; report whether the Bell booms."""
    sim = world.copy()
    sim.entities["storm" if False else _storm_id(storm)].meters["arrive"] += 1
    propagate(sim, narrate=False)
    bell = sim.entities.get("bell")
    return {
        "boom": bool(bell and bell.meters["boom"] >= THRESHOLD),
        "bound": bool(bell and bell.meters["bound"] >= THRESHOLD),
        "soft_ring": bool(bell and bell.meters["soft_ring"] >= THRESHOLD),
    }


def _storm_id(storm: Storm) -> str:
    return f"storm_{storm.id}"


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def opening_word(setting: Setting) -> str:
    return {"windy": "Way out past the cabbage patch and the leaning silo, ",
            "stormy": "On the night the sky turned the colour of a bruise, ",
            "still": "Out where the road dust had been quiet for a week, "}[setting.weather]


def introduce_hero(world: World, hero: Entity, hero_cfg: Hero) -> None:
    world.say(
        f"{opening_word(world.setting)}there lived a {hero.type} named "
        f"{hero.id} who {hero_cfg.sense}."
    )
    world.say(
        f"Folks said {hero.id} was seven, maybe eight, but nobody could be "
        f"sure, because every time you asked {hero.pronoun('object')} {hero.pronoun('possessive')} "
        f"age {hero.pronoun()} would say {hero.pronoun()} was as old as the "
        f"thunder {hero.pronoun()} had outrun."
    )


def introduce_bell(world: World, bell: Entity) -> None:
    world.say(
        f"Now the trouble in those parts was the {world.setting.bell_kind} Bell. "
        f"It hung on a rope between two old fence posts at the crossroads, and "
        f"it was so heavy and so loud that when the wind blew hard it would "
        f"swing and collide with the posts with a clang that could crack a "
        f"wagon spoke and pop a barn door shutter."
    )
    world.say(
        "Whenever the Bell collided, the cattle bolted, the chickens went "
        "silent, and the wind itself seemed to lean sideways to listen."
    )


def portents(world: World, hero: Entity, parent: Entity) -> None:
    parent.memes["careful"] += 1
    world.say(
        "One evening, just as the dish rag was being wrung out, the candles "
        "along the porch all turned blue at the same time, and the air "
        "smelled of wet iron."
    )
    world.say(
        f'"{hero.id}," {parent.id} said, in the careful voice {parent.pronoun()} '
        f'saved for storms, "the Bell is going to swing tonight, and swing hard."'
    )


def hero_sense(world: World, hero: Entity, hero_cfg: Hero) -> None:
    hero.memes["scared"] += 1
    hero.memes["ready"] += 1
    world.say(
        f"{hero.id} nodded, because {hero.pronoun()} had already felt the wind "
        f"turning under the floorboards like a dog getting up from a nap."
    )


def storm_arrives(world: World, storm: Entity, hero: Entity) -> None:
    storm.meters["arrive"] += 1
    world.say(
        f"Out across the dark field, something silver was racing toward the "
        f"crossroads, low and quick. It was {storm.label_word_noun()}, a thing "
        f"that did not belong where it was, and it had escaped from a "
        f"travelling magician whose hat was already in {hero.pronoun('possessive')} "
        f"hand and whose words were all tangled."
    )
    world.say(
        f"The little storm {storm.rush_verb()} for the {world.setting.bell_kind} "
        f"Bell, and if it hit, the Bell would collide with both posts at "
        f"once and the whole farm would shake itself apart."
    )


def hero_runs(world: World, hero: Entity, ribbon: Entity, ribbon_cfg: Ribbon,
              hero_cfg: Hero) -> None:
    hero.memes["ran_out"] += 1
    hero.memes["brave_now"] += 1
    ribbon.carried_by = hero.id
    world.say(
        f"{hero.id} did not wait to be told twice. {hero.pronoun('subject').capitalize()} "
        f"grabbed the {ribbon.label} {hero.pronoun()} kept in the lining of "
        f"{hero.pronoun('possessive')} coat -- {ribbon_cfg.phrase}, a strip of "
        f"cloth that could hold a wish the way a jar holds a firefly -- and "
        f"{hero.pronoun()} ran."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} boots hit the grass in time "
        f"with {hero.pronoun('possessive')} heart, thump-thump, thump-thump, "
        f"and the grass leaned back to let {hero.pronoun('object')} by, "
        f"because even grass knew that {hero.id} was the {hero_cfg.trait}."
    )


def ribbon_catch(world: World, hero: Entity, ribbon: Entity, ribbon_cfg: Ribbon) -> bool:
    """Throw the ribbon; if the storm and bell are bound, the boom is averted."""
    ribbon.wish_slots -= 1
    world.say(
        f"{hero.pronoun('subject').capitalize()} reached the crossroads just as "
        f"the storm reached the Bell. {hero.pronoun('subject').capitalize()} "
        f"{ribbon_cfg.prep}, and {ribbon_cfg.tail}, so when the wind tried to "
        f"make them collide they instead swung together like dancers learning "
        f"a new step."
    )
    bell = world.entities.get("bell")
    if bell is not None:
        bell.meters["bound"] += 1
    propagate(world, narrate=False)             # fires the bound/soft_ring path
    return True


def aftermath(world: World, hero: Entity, parent: Entity, mage: Entity) -> None:
    world.say(
        "The Bell rang, but soft and silver, and the cattle lay down, and "
        "the chickens opened one eye and went back to sleep."
    )


def mage_arrives(world: World, hero: Entity, mage: Entity, mage_cfg: Mage) -> None:
    mage.memes["arrived"] += 1
    world.say(
        f"The travelling magician came puffing up the road, hatless now and "
        f"laughing, and said {hero.id} had done a braver thing than "
        f"{mage.pronoun('subject')} had ever seen a grown magician do."
    )


def teach_magic(world: World, hero: Entity, mage: Entity, mage_cfg: Mage) -> None:
    hero.memes["taught_magic"] += 1
    hero.memes["praised"] += 1
    hero.memes["joy"] += 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{mage.pronoun('subject').capitalize()} {mage_cfg.teach} that night "
        f"by the kitchen fire, and from then on, whenever the "
        f"{world.setting.bell_kind} Bell swung, it swung in time with the "
        f"child who had caught the storm."
    )


# Patch on Entity so the prose verb helpers can stay readable.
def _bell_swing_word(self: Entity) -> str:
    return "sang a long note and swung"
def _storm_noun(self: Entity) -> str:
    return self.label
def _storm_rush_verb(self: Entity) -> str:
    return self.rush

Entity.label_word_swing = _bell_swing_word          # type: ignore[attr-defined]
Entity.label_word_noun = _storm_noun                # type: ignore[attr-defined]
Entity.rush_verb = _storm_rush_verb                 # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# The screenplay: coarse three-act shape, driven entirely by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, storm: Storm, hero_cfg: Hero, ribbon: Ribbon,
         mage_cfg: Mage, parent_type: str = "mother") -> World:
    world = World(setting)

    # Cast.
    hero = world.add(Entity(
        id=hero_cfg.id, kind="character", type=hero_cfg.type, label=hero_cfg.id,
        traits=["little", hero_cfg.trait],
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type,
        label="the parent", traits=["careful"],
    ))
    mage = world.add(Entity(
        id=mage_cfg.id, kind="character", type=mage_cfg.type,
        label=mage_cfg.id, traits=["breathless", "kind"],
    ))
    bell = world.add(Entity(
        id="bell", type="bell", label=f"{setting.bell_kind} Bell",
        phrase=f"the {setting.bell_kind} Bell at the crossroads",
        anchor=False,
    ))
    post = world.add(Entity(
        id="post", type="post", label="post",
        phrase="an old fence post", anchor=True,
    ))
    ribbon_e = world.add(Entity(
        id="ribbon", type="ribbon", label=ribbon.label,
        phrase=ribbon.phrase, magical=True, wish_slots=ribbon.wishes,
        guards={"boom", "clang"}, owner=hero.id,
    ))
    storm_e = world.add(Entity(
        id=f"storm_{storm.id}", type=storm.kind, label=storm.noun,
        phrase=storm.noun, moving=True, rush=storm.rush,
    ))

    # Act 1 -- setup: the hero, the Bell, the portents.
    introduce_hero(world, hero, hero_cfg)
    introduce_bell(world, bell)

    # Act 2 -- conflict: portents, the storm, the hero's run.
    world.para()
    portents(world, hero, parent)
    hero_sense(world, hero, hero_cfg)
    storm_arrives(world, storm_e, hero)
    hero_runs(world, hero, ribbon_e, ribbon, hero_cfg)

    # Act 3 -- resolution: the ribbon catches the storm and Bell together.
    world.para()
    ribbon_catch(world, hero, ribbon_e, ribbon)
    aftermath(world, hero, parent, mage)
    mage_arrives(world, hero, mage, mage_cfg)
    teach_magic(world, hero, mage, mage_cfg)

    # Record facts for the Q&A generators (grounded in the simulated world).
    world.facts.update(
        hero=hero, parent=parent, mage=mage, mage_cfg=mage_cfg,
        bell=bell, post=post, ribbon=ribbon_e, ribbon_cfg=ribbon,
        storm=storm_e, storm_cfg=storm, setting=setting, hero_cfg=hero_cfg,
        caught=ribbon_e.wish_slots <= 0 and bell.meters["bound"] >= THRESHOLD,
        boom=bell.meters["boom"] >= THRESHOLD,
        soft_ring=bell.meters["soft_ring"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "crossroads": Setting(place="the crossroads", weather="windy", bell_kind="tin",
                          affords={"cyclone", "whirlwind", "dust_devil"}),
    "farm": Setting(place="the farm gate", weather="stormy", bell_kind="bronze",
                    affords={"cyclone", "whirlwind"}),
    "prairie": Setting(place="the open prairie", weather="windy", bell_kind="silver",
                       affords={"cyclone", "whirlwind", "dust_devil"}),
    "covered_bridge": Setting(place="the covered bridge", weather="still",
                              bell_kind="tin", affords={"dust_devil"}),
}

STORMS = {
    "cyclone": Storm(
        id="cyclone",
        noun="a cyclone in a bottle",
        rush="streaked straight",
        speed=2.0,
        spark=True,
    ),
    "whirlwind": Storm(
        id="whirlwind",
        noun="a whirlwind the size of a supper plate",
        rush="skidded sideways toward",
        speed=1.5,
        spark=True,
    ),
    "dust_devil": Storm(
        id="dust_devil",
        noun="a dust devil with a mind of its own",
        rush="hopped and skittered toward",
        speed=1.0,
        spark=False,
    ),
}

RIBBONS = {
    "grandmother": Ribbon(
        id="grandmother",
        label="magic ribbon",
        phrase="a strip of cloth his grandmother had sewn into the coat lining",
        prep="threw the ribbon up like a lasso",
        tail="the ribbon looped around the Bell and the little storm both",
        wishes=1,
    ),
    "aunt": Ribbon(
        id="aunt",
        label="grandmother's ribbon",
        phrase="a length of red silk his aunt had pressed into his palm",
        prep="flung the ribbon in a long loop",
        tail="the silk caught the Bell's tongue and the storm's edge together",
        wishes=1,
    ),
    "neighbour": Ribbon(
        id="neighbour",
        label="neighbour's wish-cloth",
        phrase="a square of cloth his neighbour had cut from a flour sack",
        prep="spun the cloth open above his head",
        tail="the cloth caught both the Bell and the swirl and held them tight",
        wishes=1,
    ),
}

HERO_TRAITS = [
    ("bravest boy in the county", "could hear the wind coming three hours before it arrived",
     "had already felt the wind turning under the floorboards"),
    ("quickest girl on the road", "could feel a storm in the soles of her feet",
     "had already felt the wind turning under the floorboards"),
    ("stubbornest boy in two valleys", "could smell rain in the air an hour early",
     "had already felt the wind turning under the floorboards"),
]

MAGES = [
    Mage(id="Mr. Quill", type="magician_man", label="Mr. Quill",
         phrase="a travelling magician with his hat in his hand",
         teach="taught Otis three little words of magic"),
    Mage(id="Ms. Penny", type="magician_woman", label="Ms. Penny",
         phrase="a travelling magician in a coat that whistled at the cuffs",
         teach="taught Mae three little words of magic"),
    Mage(id="Old Coot", type="magician_man", label="Old Coot",
         phrase="an old conjurer who kept his tricks in a soup tin",
         teach="taught the boy three little words of magic"),
]

BOY_NAMES = ["Otis", "Hank", "Wes", "Tuck", "Jed", "Silas", "Cobb"]
GIRL_NAMES = ["Mae", "Della", "Wren", "Ivy", "Josie", "Cora", "Hallie"]
PARENT_TYPES = ["mother", "father"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    """(setting, storm, ribbon, mage) tuples that pass the reasonableness gate."""
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for storm_id in setting.affords:
            for ribbon_id in RIBBONS:
                for mage_id, mage in MAGES.items():
                    combos.append((setting_id, storm_id, ribbon_id, mage_id))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific; the generic StorySample/QAItem live in
# storyworlds/results.py).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    setting: str
    storm: str
    ribbon: str
    mage: str
    hero_name: str
    hero_gender: str
    parent: str
    trait: str
    sense: str
    verb_listen: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
# (3) Child-level world knowledge, keyed by topic.  These are answerable WITHOUT
# the story; they explain the *elements* the world is built from.
KNOWLEDGE = {
    "collide": [
        ("What does it mean to collide?",
         "To collide is to crash into something else while moving fast. "
         "Two things that collide bump into each other hard."),
        ("What happens when two heavy things collide?",
         "When two heavy things collide they can clang, spark, or shake the "
         "ground under them."),
    ],
    "suspense": [
        ("What is suspense?",
         "Suspense is the feeling you get when you do not yet know how a "
         "story will turn out, and your heart beats a little faster while "
         "you wait to find out."),
        ("Why does a candle flame turn blue before a storm?",
         "A candle flame can turn blue before a storm because the air is "
         "filling with tiny charged bits that change how the flame burns."),
    ],
    "bravery": [
        ("What is bravery?",
         "Bravery is doing the right thing even when you are scared. A "
         "brave person keeps going when their knees want to stop."),
        ("Why is it brave to run out into a dark field?",
         "It is brave to run out into a dark field because you cannot see "
         "what is out there, and your heart is pounding, and you keep going "
         "anyway."),
    ],
    "magic": [
        ("What is a magic ribbon?",
         "A magic ribbon is a strip of cloth that can hold a wish the way "
         "a jar holds a firefly. It is not really magic, but in a story it "
         "lets a small person catch a very big trouble."),
        ("What does a travelling magician do?",
         "A travelling magician goes from town to town performing tricks "
         "and sometimes chasing things that have escaped from those tricks."),
    ],
    "tall_tale": [
        ("What is a tall tale?",
         "A tall tale is a story that tells small, true things in very "
         "large ways. The wind is bigger, the bell is louder, and the hero "
         "is braver than any real person could be."),
        ("How can you tell a story is a tall tale?",
         "You can tell a story is a tall tale because the people in it are "
         "the best at everything, the weather does what it wants, and "
         "every problem ends with a bang or a laugh."),
    ],
    "tin_bell": [
        ("Why does a big bell ring so loud?",
         "A big bell rings so loud because it is heavy and made of metal, "
         "and when it swings it pushes a lot of air, and that air pushes "
         "our ears."),
        ("Why would a bell collide with a fence post?",
         "A bell on a rope can swing so far that the metal part hits a "
         "fence post on the way past, and the bell and the post collide."),
    ],
    "cyclone": [
        ("What is a cyclone in a bottle?",
         "A cyclone in a bottle is a tiny storm that a magician has folded "
         "into a jar for showing off. If the cork comes loose, the storm "
         "slips out and behaves like a real, but very small, whirlwind."),
        ("What does a cyclone do when it meets something big?",
         "When a cyclone meets something big, it tries to push that thing "
         "with its spinning wind. The big thing can shake, ring, or topple."),
    ],
}
KNOWLEDGE_ORDER = ["tall_tale", "collide", "suspense", "bravery", "magic",
                   "tin_bell", "cyclone"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    hero, mage, storm, ribbon, bell = (f["hero"], f["mage"], f["storm_cfg"],
                                       f["ribbon_cfg"], f["bell"])
    return [
        f'Write a short tall-tale story for a 5-to-8-year-old on the theme '
        f'"a brave child catches a storm" that uses the word "collide" twice.',
        f"Tell a suspenseful story where a {hero.type} named {hero.id} hears a "
        f"storm coming, runs out to a crossroads {bell.label}, and uses a "
        f"{ribbon.label} to keep the Bell and the {storm.kind} from "
        f"colliding with each other and the fence post.",
        f'Write a simple story that uses the words "collide", "brave", and '
        f'"magic ribbon", and ends with a child swinging in time with a Bell.',
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    hero, parent, mage, bell, ribbon, storm = (f["hero"], f["parent"], f["mage"],
                                               f["bell"], f["ribbon_cfg"],
                                               f["storm_cfg"])
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    psub = parent.pronoun("subject")
    setting = world.setting

    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who lives out past the cabbage patch and the leaning silo, "
                f"and what can {hero.id} hear three hours before it arrives?"
            ),
            answer=(
                f"{hero.id} lives out past the cabbage patch and the leaning "
                f"silo, and {sub} can hear the wind coming three hours before "
                f"it arrives."
            ),
        ),
        QAItem(
            question=(
                f"What is the trouble in those parts, and what does the "
                f"{setting.bell_kind} Bell do when the wind blows hard at "
                f"{setting.place}?"
            ),
            answer=(
                f"The trouble is the {setting.bell_kind} Bell. When the wind "
                f"blows hard it swings and collides with the posts at "
                f"{setting.place}, and the clang can crack a wagon spoke and "
                f"pop a barn shutter."
            ),
        ),
        QAItem(
            question=(
                f"What portents told {parent.id} that the Bell was going to "
                f"swing hard the night {hero.id} ran out to {setting.place}?"
            ),
            answer=(
                f"The candles along the porch all turned blue at the same "
                f"time, and the air smelled of wet iron. {psub.capitalize()} "
                f"spoke in the careful voice saved for storms."
            ),
        ),
        QAItem(
            question=(
                f"What was the silver thing racing toward the Bell at "
                f"{setting.place}, and where did it come from?"
            ),
            answer=(
                f"It was {storm.noun}, a thing that did not belong where it "
                f"was. It had escaped from a travelling magician -- "
                f"{mage.label} -- whose hat was in {pos} hand and whose "
                f"words were all tangled."
            ),
        ),
        QAItem(
            question=(
                f"What did brave {hero.id} grab from {pos} coat lining before "
                f"{sub} ran out to stop the Bell and the {storm.kind} from "
                f"colliding at {setting.place}?"
            ),
            answer=(
                f"{sub.capitalize()} grabbed the {ribbon.label}: {ribbon.phrase}, "
                f"a strip of cloth that could hold a wish the way a jar holds "
                f"a firefly."
            ),
        ),
    ]
    if f.get("caught"):
        qa.append(QAItem(
            question=(
                f"How did the {ribbon.label} keep the {setting.bell_kind} Bell "
                f"and the {storm.kind} from colliding and shaking the farm apart?"
            ),
            answer=(
                f"{hero.id} {ribbon.prep}, and {ribbon.tail}, so when the wind "
                f"tried to make them collide they instead swung together "
                f"like dancers learning a new step. The Bell rang soft and "
                f"silver instead of clanging."
            ),
        ))
    qa.append(QAItem(
        question=(
            f"What did the travelling magician {mage.label} do after seeing "
            f"brave {hero.id} catch the storm at {setting.place}?"
        ),
        answer=(
            f"{mage.label} said {hero.id} had done a braver thing than "
            f"{mage.pronoun('subject')} had ever seen a grown magician do, and "
            f"{mage.pronoun('subject')} {mage.teach} that night by the "
            f"kitchen fire."
        ),
    ))
    qa.append(QAItem(
        question=(
            f"From that night on, what did the {setting.bell_kind} Bell do "
            f"whenever it swung at {setting.place}?"
        ),
        answer=(
            f"Whenever the {setting.bell_kind} Bell swung, it swung in time "
            f"with the child who had caught the storm."
        ),
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    tags = {"collide", "suspense", "bravery", "magic", "tall_tale",
            "tin_bell", "cyclone"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
# CLI / trace
# ---------------------------------------------------------------------------
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
        if e.magical:
            bits.append(f"magical wishes={e.wish_slots}")
        if e.belt:
            bits.append(f"belt={sorted(e.belt)}")
        lines.append(f"  {e.id:14} ({e.type:13}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        setting="crossroads", storm="cyclone", ribbon="grandmother",
        mage="Mr. Quill", hero_name="Otis", hero_gender="boy",
        parent="mother", trait="bravest boy in the county",
        sense="could hear the wind coming three hours before it arrived",
        verb_listen="had already felt the wind turning under the floorboards",
    ),
    StoryParams(
        setting="farm", storm="whirlwind", ribbon="aunt",
        mage="Ms. Penny", hero_name="Mae", hero_gender="girl",
        parent="father", trait="quickest girl on the road",
        sense="could feel a storm in the soles of her feet",
        verb_listen="had already felt the wind turning under the floorboards",
    ),
    StoryParams(
        setting="prairie", storm="dust_devil", ribbon="neighbour",
        mage="Old Coot", hero_name="Hank", hero_gender="boy",
        parent="mother", trait="stubbornest boy in two valleys",
        sense="could smell rain in the air an hour early",
        verb_listen="had already felt the wind turning under the floorboards",
    ),
]


def explain_rejection(storm: Storm, setting: Setting) -> str:
    if storm.id not in setting.affords:
        return (f"(No story: a {storm.kind} cannot escape toward the Bell at "
                f"{setting.place} in this world; try a storm the setting can host.)")
    return "(No story: no ribbon in the registry can hold a wish for this conflict.)"


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate.
# The rules are inline below; the facts are generated from the registries
# above so the two can never drift.  Uses the shared ``asp`` helper + clingo,
# imported lazily so the prose engine runs without clingo installed.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A storm can collide with the bell only when the setting hosts that kind.
storm_targets_bell(S) :- storm(S, _), affords(Setting, S).

% A ribbon is a magical fix only when it has at least one wish left.
magical_fix(R) :- ribbon(R), wishes(R, N), N >= 1.

% A fix catches the storm when (a) the storm targets the bell and (b) the
% ribbon is a magical fix the hero can carry.
catchable(Setting, Storm, Ribbon) :- storm_targets_bell(Storm),
                                     setting(Setting),
                                     affords(Setting, Storm),
                                     magical_fix(Ribbon).

valid(Setting, Storm, Ribbon, Mage) :- catchable(Setting, Storm, Ribbon),
                                       mage(Mage).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("bell_kind", sid, s.bell_kind))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for storm_id, st in STORMS.items():
        lines.append(asp.fact("storm", storm_id, st.kind))
    for rid, r in RIBBONS.items():
        lines.append(asp.fact("ribbon", rid))
        lines.append(asp.fact("wishes", rid, r.wishes))
    for mage_id, m in MAGES.items():
        lines.append(asp.fact("mage", mage_id))
        lines.append(asp.fact("mage_type", mage_id, m.type))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    """Clingo's version of valid_combos(): (setting, storm, ribbon, mage)."""
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    """Check the inline ASP gate agrees with the Python valid_combos()."""
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard storyworld interface (see storyworlds/AGENTS.md):
#   build_parser() -> ArgumentParser
#   resolve_params(args, rng) -> StoryParams        (random where unspecified)
#   generate(params) -> StorySample                  (the core; world -> story+QA)
#   emit(sample, ...) -> None                        (human-readable output)
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a brave child catches a storm. "
                    "Unspecified choices are picked at random (seeded).")
    # A small, debuggable set of pins; any omitted choice is randomized.
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--storm", choices=STORMS)
    ap.add_argument("--ribbon", choices=RIBBONS)
    ap.add_argument("--mage", choices=list(MAGES.keys()))
    ap.add_argument("--hero-gender", choices=["boy", "girl"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("--hero-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    # Clingo (ASP) modes -- the inline declarative reasoner (needs clingo).
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    """Fill in any unspecified choices at random, keeping the combo reasonable.

    Raises StoryError if the *explicit* options describe an invalid story."""
    if args.setting and args.storm:
        s, st = SETTINGS[args.setting], STORMS[args.storm]
        if storm_id_in_setting(st.id, s) is False or not storm_targets_bell(st):
            raise StoryError(explain_rejection(st, s))

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.storm is None or c[1] == args.storm)
              and (args.ribbon is None or c[2] == args.ribbon)
              and (args.mage is None or c[3] == args.mage)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, storm_id, ribbon_id, mage_id = rng.choice(sorted(combos))
    gender = args.hero_gender or rng.choice(["boy", "girl"])
    name = args.hero_name or rng.choice(BOY_NAMES if gender == "boy" else GIRL_NAMES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    trait, sense, verb_listen = rng.choice(HERO_TRAITS)
    if gender == "girl":
        trait = trait.replace("boy", "girl").replace("his", "her").replace("Otis", name)
    return StoryParams(
        setting=setting_id,
        storm=storm_id,
        ribbon=ribbon_id,
        mage=mage_id,
        hero_name=name,
        hero_gender=gender,
        parent=parent,
        trait=trait,
        sense=sense,
        verb_listen=verb_listen,
    )


def storm_id_in_setting(storm_id: str, setting: Setting) -> bool:
    return storm_id in setting.affords


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    hero_cfg = Hero(
        id=params.hero_name, type=params.hero_gender,
        noun=f"a {params.hero_gender} named {params.hero_name}",
        trait=params.trait, sense=params.sense, verb_listen=params.verb_listen,
        coat="his coat" if params.hero_gender == "boy" else "her coat",
    )
    world = tell(SETTINGS[params.setting], STORMS[params.storm],
                 hero_cfg, RIBBONS[params.ribbon], MAGES[params.mage],
                 params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, storm, ribbon, mage) combos:\n")
        for setting, storm, ribbon, mage in combos:
            print(f"  {setting:14} {storm:11} {ribbon:11}  [{mage}]")
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
            header = (f"### {p.hero_name}: a {p.storm} at {p.setting} "
                      f"(ribbon: {p.ribbon}, mage: {p.mage})")
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
