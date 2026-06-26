#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/antique_problem_solving_sharing_heartwarming.py
=========================================================================================================================

A standalone *story world* sketch for "The Antique Tea Set" tale and close,
constraint-checked variations of it.

Initial story (used to build a world model):
---
Once upon a time, there was a gentle boy named Theo. He loved visiting his
grandmother, because in her parlour there was a small wooden shelf full of
treasures from long ago. His favourite treasure was a tiny antique tea set:
a round pot and four little cups painted with pink roses.

One rainy afternoon, Theo and his grandmother sat down together. She poured
him real tea in a grown-up cup, and he got to set out his tiny antique tea
set on the lace cloth. "These cups have been on my shelf for sixty years,"
his grandmother said softly. "They are very dear to me."

Just then, Theo's little cousin Anna arrived. She was only four, and she
wanted to play tea party right away. But Anna's hands were still clumsy
from her nap, and when she reached for a tiny cup, it slipped from her
fingers and chipped its little painted handle.

Theo felt his eyes sting. He knew the cup was old and could not be
replaced. He looked at Anna's worried face, and he looked at the chipped
rose on his grandmother's cup. He took a slow breath.

"The handle is chipped," he said, "but the cup is still beautiful." Then
he poured pretend tea with his grandmother, and let Anna choose which cup
she wanted, and he told her about the pink roses. They shared the tea set
together, one chipped cup and three whole ones, and his grandmother smiled
because the old treasures had made a new memory.

Causal state updates:
---
    set out antique       -> set.care += 1, set.sentiment += 1
    chip on fragile item  -> item.chips += 1 ; item.whole -> 0
                            item.care ++        (the heirloom is more fragile now)
                            owner.sadness += 1
    child offered the chipped cup
        without resentment -> owner.letting_go += 1, owner.sharing += 1
    included the cousin   -> cousin.belonging += 1 ; both kids.warmth += 1

Scripted social/emotional beats:
---
    conflict raised       -> owner.hurt += 1
    reasoned second look  -> owner.patience += 1
    share accepted        -> both kids.warmth += 1 ; set.loved += 1
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
# (so ``results`` resolves regardless of the current working directory).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# What kinds of damage can a clumsy child do to a fragile heirloom?
DAMAGE_KINDS = {"chipped", "cracked", "stained"}

# Body / handling regions -- only some are realistic for a small child.
HANDLING = {"handle", "rim", "body"}


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # boy, girl, grandmother, teapot, cup ...
    label: str = ""                # short reference, e.g. "teapot", "tiny cup"
    phrase: str = ""               # full noun phrase, e.g. "a tiny antique tea set"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None    # who it belongs to
    caretaker: Optional[str] = None  # who looks after it (grandmother often)
    fragile: bool = False
    whole: bool = True
    era: str = ""                  # "antique", "old", "new"
    part: str = ""                 # handle | rim | body  (which part got hurt)
    damage: str = ""               # chipped | cracked | stained
    plural: bool = False
    # Two numeric dimensions, treated uniformly (cf. story.py memeplex model):
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandma", "grandfather": "grandpa",
                "mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the parlour"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)   # which activities fit


@dataclass
class Activity:
    """The gentle play the children settle on once the conflict is named."""
    id: str
    verb: str            # after "wanted to ..."            : "play tea party"
    gerund: str          # after "loved ... and ..."       : "pouring pretend tea"
    start: str           # after "began to ..."            : "set out the tea set"
    mess: str            # mess kind key, one of DAMAGE_KINDS (often "")
    risk: str            # how a clumsy child could hurt it : "slip from small fingers"
    zone: set[str]       # which part is at risk            : {"handle"}
    weather: str         # "rainy" | "sunny" | ""
    keyword: str = ""    # topic word for generation prompts : "tea set"
    tags: set[str] = field(default_factory=set)


@dataclass
class Heirloom:
    """The fragile old thing the child loves; the cousin can break it."""
    label: str
    phrase: str
    type: str             # teapot, cup, saucer, music_box ...
    part: str             # handle | rim | body
    plural: bool = False
    eras: set[str] = field(default_factory=lambda: {"antique"})  # acceptable ages
    genders: set[str] = field(default_factory=lambda: {"boy", "girl"})


@dataclass
class Repair:
    """The kind of gentle fix the elder can offer (or that the child accepts
    with grace).  Used by the resolution step.
    """
    id: str
    label: str           # "use a little glue", "wrap a tiny cloth around the handle"
    covers: set[str]     # which damage kinds it makes right
    guards: set[str]     # which parts it protects going forward
    offer: str           # body of the offer: "smear a touch of safe glue"
    tail: str            # closing clause: "smiled and set the cup on the shelf"
    plural: bool = False


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()       # idempotency for the rule engine
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()          # which part is at risk this scene
        self.weather: str = ""
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

    def heirlooms(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.fragile]

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
        clone.zone = set(self.zone)
        clone.weather = self.weather
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


def _r_damage(world: World) -> list[str]:
    """A clumsy handling on a fragile heirloom produces chips/cracks and care."""
    out: list[str] = []
    for actor in world.characters():
        for kind in DAMAGE_KINDS:
            if actor.meters[kind] < THRESHOLD:
                continue
            for item in world.heirlooms():
                if not item.whole:
                    continue
                if item.part not in world.zone:
                    continue
                sig = ("damage", item.id, kind)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.damage = kind
                item.whole = False
                item.meters[kind] += 1
                item.meters["care"] += 1
                # owner feels the loss
                if item.owner and item.owner in world.entities:
                    owner = world.get(item.owner)
                    owner.memes["sadness"] += 1
                out.append(
                    f"One tiny {item.label} came away with a {kind} {item.part}."
                )
    return out


def _r_hurt(world: World) -> list[str]:
    """An owner who has noticed damage and feels sadness registers a hurt beat
    (only when conflict is also on the table -- we narrate it in the screenplay)."""
    for actor in world.characters():
        if actor.memes["sadness"] < THRESHOLD or actor.memes["conflict"] < THRESHOLD:
            continue
        sig = ("hurt", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["hurt"] += 1
        return ["__hurt__"]              # marker; narrated by the screenplay beat
    return []


def _r_warmth(world: World) -> list[str]:
    """A child who has accepted a share or a repair raises warmth in both kids."""
    out: list[str] = []
    for actor in world.characters():
        if actor.type not in {"boy", "girl"}:
            continue
        if actor.memes["sharing"] < THRESHOLD or actor.memes["letting_go"] < THRESHOLD:
            continue
        sig = ("warmth", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["warmth"] += 1
        # the other child picks it up too
        for other in world.characters():
            if other.id != actor.id and other.type in {"boy", "girl"}:
                other.memes["warmth"] += 1
        out.append("__warmth__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="damage", tag="physical", apply=_r_damage),
    Rule(name="hurt", tag="social", apply=_r_hurt),
    Rule(name="warmth", tag="social", apply=_r_warmth),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers -- what is a *reasonable* concern and a *reasonable* fix.
# ---------------------------------------------------------------------------
def heirloom_at_risk(activity: Activity, heirloom: Heirloom) -> bool:
    """Would this activity actually expose this heirloom's fragile part?"""
    return heirloom.part in activity.zone


def select_repair(activity: Activity, heirloom: Heirloom) -> Optional[Repair]:
    """The compatible fix: a repair that handles the activity's risk kind AND
    covers the at-risk part.  Returns None when no reasonable repair exists
    (which is exactly the case we refuse to generate)."""
    for r in REPAIRS:
        if activity.mess in r.guards and heirloom.part in r.covers:
            return r
    # Even with no ``mess`` (gentle play), a graceful "keep using it" counts as
    # a valid resolution when the heirloom is antique and the part is handle.
    if not activity.mess:
        for r in REPAIRS:
            if heirloom.part in r.covers:
                return r
    return None


# ---------------------------------------------------------------------------
# Prediction: the elder runs the world model forward on a copy to foresee the
# damage before deciding what to say.
# ---------------------------------------------------------------------------
def predict_break(world: World, actor: Entity, activity: Activity,
                  heirloom_id: str) -> dict:
    """Simulate the clumsy handling silently and report whether the heirloom
    was hurt, and how much care the heirloom needs now."""
    sim = world.copy()
    _do_clumsy(sim, sim.get(actor.id), activity, narrate=False)
    item = sim.entities.get(heirloom_id)
    return {
        "broken": bool(item and not item.whole),
        "care": sum(i.meters["care"] for i in sim.heirlooms()),
    }


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def activity_delight(activity: Activity) -> str:
    return {
        "tea_party": "the little painted roses seemed to nod as the cups clinked",
        "music_box": "the tiny melody made the parlour feel like a meadow",
        "doll_show": "the porcelain dolls tilted their heads as if listening",
        "story_time": "the old pictures in the book made the room feel warm",
    }.get(activity.id, "the moment felt gentle and full")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return (f"Inside {setting.place}, the curtains were drawn, and the "
                f"lace cloth waited for little hands.")
    return f"{setting.place.capitalize()} was quiet, and a bench sat waiting."


def _do_clumsy(world: World, actor: Entity, activity: Activity,
               narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return                                  # this place can't host the activity
    world.zone = set(activity.zone)
    if activity.mess:
        actor.meters[activity.mess] += 1
    actor.memes["clumsy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who noticed old things.")


def loves_heirloom(world: World, hero: Entity, heirloom: Entity) -> None:
    hero.memes["love"] += 1
    world.say(
        f"{hero.id} loved the {heirloom.label} on the shelf; the soft "
        f"colours made {hero.pronoun('object')} feel calm."
    )


def set_out(world: World, owner: Entity, heirloom: Entity) -> None:
    heirloom.meters["use"] += 1
    heirloom.meters["care"] += 1
    heirloom.owner = owner.id
    world.say(
        f"One afternoon, {owner.id} set the {heirloom.label} on the lace cloth, "
        f"and the parlour smelled faintly of tea."
    )


def elder_sets_value(world: World, elder: Entity, heirloom: Entity) -> None:
    heirloom.meters["care"] += 1
    heirloom.caretaker = elder.id
    era = heirloom.era or "antique"
    world.say(
        f'"{this_or_these(heirloom).capitalize()} {been_or_was(heirloom)} on '
        f'my shelf for a very long time," {elder.id} said softly. '
        f'"They are very dear to me."'
    )


def cousin_arrives(world: World, owner: Entity, cousin: Entity,
                   activity: Activity) -> None:
    cousin.memes["excitement"] += 1
    world.say(
        f"Just then, {cousin.id}, who was little and still clumsy from "
        f"{'her' if cousin.type == 'girl' else 'his'} nap, ran in wanting to "
        f"{activity.verb} right away."
    )


def clumsy_reach(world: World, cousin: Entity, heirloom: Entity,
                 activity: Activity) -> bool:
    """The cousin reaches for an heirloom; the world model predicts the break."""
    pred = predict_break(world, cousin, activity, heirloom.id)
    world.facts["predicted_break"] = pred["broken"]
    world.facts["predicted_care"] = pred["care"]
    if not pred["broken"]:
        return False
    world.say(
        f"When {cousin.id} reached for one tiny {heirloom.label}, it "
        f"{activity.risk} and came away with a small {activity.mess or 'chip'} "
        f"on its {heirloom.part}."
    )
    return True


def owner_feels(world: World, owner: Entity, heirloom: Entity) -> None:
    owner.memes["sadness"] += 1
    owner.memes["conflict"] += 1
    world.say(
        f"{owner.id} felt {owner.pronoun('possessive')} eyes sting; the {heirloom.label} "
        f"was old and could not be replaced."
    )


def pause_and_look(world: World, owner: Entity, heirloom: Entity) -> None:
    owner.memes["patience"] += 1
    world.say(
        f"{owner.id} took a slow breath and looked at the {heirloom.label} "
        f"again, and at {heirloom.owner and world.get(heirloom.owner).id or 'the cousin'}'s worried face."
    )


def name_what_changed(world: World, owner: Entity, heirloom: Entity,
                      activity: Activity) -> None:
    owner.memes["reason"] += 1
    noun = heirloom.label
    world.say(
        f'"{The_capitalized_named(owner)} said. "The {noun} is still beautiful, '
        f'even with the {heirloom.damage or "little mark"} on its {heirloom.part}."'
    )


def offer_share(world: World, owner: Entity, cousin: Entity,
                heirloom: Entity) -> None:
    owner.memes["letting_go"] += 1
    owner.memes["sharing"] += 1
    world.say(
        f"Then {owner.id} poured pretend tea with the {heirloom.label} and let "
        f"{cousin.id} choose which cup {cousin.pronoun()} wanted."
    )


def cousin_belongs(world: World, owner: Entity, cousin: Entity,
                   heirloom: Entity) -> None:
    cousin.memes["belonging"] += 1
    cousin.memes["sharing"] += 1
    world.say(
        f"{cousin.id} sat close and held the {heirloom.label} gently, and "
        f"{cousin.pronoun()} began to feel that this little tea party was "
        f"also {cousin.pronoun('possessive')}."
    )


def elder_sees_made(world: World, elder: Entity, owner: Entity,
                    heirloom: Entity) -> None:
    heirloom.meters["use"] += 1
    elder.memes["love"] += 1
    world.say(
        f"{elder.id} smiled because the old {heirloom.label} had made a new "
        f"memory, and {elder.pronoun()} set the {heirloom.label} back on the "
        f"shelf as if it were a little treasure once again."
    )


def repair_offer(world: World, owner: Entity, heirloom: Entity,
                 activity: Activity) -> Optional[Repair]:
    """Offer a repair -- but only a repair that covers the at-risk part,
    and only if the world model then predicts no further damage."""
    repair = select_repair(activity, heirloom)
    if repair is None:
        return None
    world.add(Entity(
        id=repair.id, type="repair", label=repair.label,
        covers=set(repair.covers), plural=repair.plural,
    ))
    world.say(
        f'"{The_capitalized_named(owner)} looked at the {heirloom.label} and said, '
        f'"How about we {repair.offer} so the {heirloom.label} can keep "
        f'being used?"'
    )
    return repair


def repair_apply(world: World, repair: Repair, heirloom: Entity) -> None:
    heirloom.whole = True
    heirloom.damage = ""
    world.say(
        f"They {repair.tail}, and the {heirloom.label} was whole again, "
        f"ready for more little guests."
    )


# ---------------------------------------------------------------------------
# Small utility helpers (kept here so the verb code reads like prose).
# ---------------------------------------------------------------------------
def this_or_these(e: Entity) -> str:
    return "These" if e.plural else "This"


def been_or_was(e: Entity) -> str:
    return "have been" if e.plural else "has been"


def The_capitalized_named(e: Entity) -> str:
    if e.id in {"Theo", "Lily", "Ben", "Mia", "Anna", "Rose"}:
        return f'"{e.id}"'
    return f'"{e.id}"'


# ---------------------------------------------------------------------------
# The screenplay: coarse three-act shape, driven entirely by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, heirloom_cfg: Heirloom,
         hero_name: str = "Theo", hero_type: str = "boy",
         hero_traits: Optional[list[str]] = None,
         elder_type: str = "grandmother",
         cousin_name: str = "Anna",
         cousin_type: str = "girl") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["gentle", "thoughtful"]),
    ))
    elder = world.add(Entity(
        id="Grand", kind="character", type=elder_type, label="the grandparent",
    ))
    cousin = world.add(Entity(
        id=cousin_name, kind="character", type=cousin_type,
        traits=["little", "clumsy", "eager"],
    ))
    heirloom = world.add(Entity(
        id="heirloom", type=heirloom_cfg.type, label=heirloom_cfg.label,
        phrase=heirloom_cfg.phrase, owner=hero.id, caretaker=elder.id,
        fragile=True, era=heirloom_cfg.era or "antique",
        part=heirloom_cfg.part, plural=heirloom_cfg.plural,
    ))

    # Act 1 -- setup: who, the heirloom, the elder's quiet claim on it.
    introduce(world, hero)
    loves_heirloom(world, hero, heirloom)
    elder_sets_value(world, elder, heirloom)

    # Act 2 -- the clumsy moment and the small injury.
    world.para()
    set_out(world, elder, heirloom)
    cousin_arrives(world, hero, cousin, activity)
    clumsy_reach(world, cousin, heirloom, activity)
    propagate(world, narrate=False)             # fires damage -> sadness
    owner_feels(world, hero, heirloom)

    # Act 3 -- resolution: the hero names what changed and shares the set.
    world.para()
    pause_and_look(world, hero, heirloom)
    name_what_changed(world, hero, heirloom, activity)
    offer_share(world, hero, cousin, heirloom)
    cousin_belongs(world, hero, cousin, heirloom)
    propagate(world, narrate=False)             # fires warmth in both kids
    # A small final repair beat, when one applies (chipped handle -> glue).
    repair = repair_offer(world, hero, heirloom, activity)
    if repair:
        repair_apply(world, repair, heirloom)
    elder_sees_made(world, elder, hero, heirloom)

    # Record facts for the Q&A generators (grounded in the simulated world).
    world.facts.update(
        hero=hero, elder=elder, cousin=cousin, heirloom=heirloom,
        heirloom_cfg=heirloom_cfg, activity=activity, setting=setting,
        repair=repair,
        conflict=hero.memes["conflict"] >= THRESHOLD,
        resolved=(repair is not None) or True,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "parlour": Setting(place="the parlour", indoor=True,
                       affords={"tea_party", "doll_show"}),
    "kitchen": Setting(place="the kitchen", indoor=True,
                       affords={"tea_party", "story_time"}),
    "sunroom": Setting(place="the sunroom", indoor=True,
                       affords={"tea_party", "doll_show", "story_time"}),
    "porch": Setting(place="the porch", indoor=False,
                     affords={"music_box", "story_time"}),
}

ACTIVITIES = {
    # gentle tea-party -- the cousin's clumsy fingers can chip a handle.
    "tea_party": Activity(
        id="tea_party",
        verb="play tea party",
        gerund="pouring pretend tea",
        start="set out the tea set",
        mess="chipped",
        risk="slipped from her small fingers",
        zone={"handle", "rim"},
        weather="rainy",
        keyword="tea set",
        tags={"tea", "antique", "fragile"},
    ),
    # music box -- the cousin can crack the body if she lifts it too hard.
    "music_box": Activity(
        id="music_box",
        verb="wind the music box",
        gerund="listening to the music box",
        start="wind up the music box",
        mess="cracked",
        risk="bumped the corner against the table",
        zone={"body"},
        weather="sunny",
        keyword="music box",
        tags={"music", "antique", "fragile"},
    ),
    # doll show -- the porcelain dolls' painted faces can be stained.
    "doll_show": Activity(
        id="doll_show",
        verb="show the dolls",
        gerund="showing the dolls",
        start="bring out the dolls",
        mess="stained",
        risk="left a sticky thumbprint on the face",
        zone={"body"},
        weather="",
        keyword="porcelain dolls",
        tags={"doll", "antique", "fragile"},
    ),
    # story time -- old picture book pages can tear at the rim/spine.
    "story_time": Activity(
        id="story_time",
        verb="read the old book",
        gerund="turning the old pages",
        start="open the old book",
        mess="chipped",
        risk="caught the page on the corner",
        zone={"rim"},
        weather="",
        keyword="story book",
        tags={"book", "antique", "fragile"},
    ),
}

# Order matters: more specific repair first, "use gently" fallback last.
REPAIRS = [
    Repair(
        id="glue",
        label="a touch of safe glue",
        covers={"handle"},
        guards={"chipped"},
        offer="smear a tiny bit of safe glue on the chipped handle",
        tail="smiled and set the cup on the shelf",
    ),
    Repair(
        id="cloth",
        label="a tiny cloth wrap",
        covers={"handle", "rim"},
        guards={"chipped"},
        offer="wrap a soft cloth around the handle",
        tail="wrapped the soft cloth around the handle",
    ),
    Repair(
        id="polish",
        label="a careful polish",
        covers={"body"},
        guards={"stained"},
        offer="polish the stain with a soft cloth",
        tail="polished the stain away",
    ),
    Repair(
        id="shelf",
        label="back to the shelf",
        covers={"handle", "rim", "body"},
        guards={"chipped", "cracked", "stained"},
        offer="set it gently on the shelf until it is mended",
        tail="set the old thing back on the shelf",
    ),
]

# Each heirloom names the *one* fragile part that is realistically at risk.
HEIRLOOMS = {
    "teapot": Heirloom(
        label="antique tea set",
        phrase="a tiny antique tea set with pink roses",
        type="teapot",
        part="handle",
    ),
    "teacup": Heirloom(
        label="antique teacup",
        phrase="a tiny antique teacup painted with a pink rose",
        type="teacup",
        part="handle",
    ),
    "musicbox": Heirloom(
        label="antique music box",
        phrase="a small antique music box with a brass key",
        type="music_box",
        part="body",
    ),
    "dolls": Heirloom(
        label="porcelain dolls",
        phrase="two little porcelain dolls in silk dresses",
        type="doll",
        part="body",
        plural=True,
    ),
    "book": Heirloom(
        label="picture book",
        phrase="an old picture book with gold-edged pages",
        type="book",
        part="rim",
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Theo", "Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli"]
COUSIN_NAMES = ["Anna", "Eli", "Maya", "Noah", "Rose", "Finn"]
TRAITS = ["gentle", "thoughtful", "careful", "kind", "patient", "quiet"]


def valid_combos() -> list[tuple[str, str]]:
    """(place, activity, heirloom) triples that pass the reasonableness gate."""
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for hid, heirloom in HEIRLOOMS.items():
                if heirloom_at_risk(act, heirloom) and select_repair(act, heirloom):
                    combos.append((place, act_id, hid))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific; the generic StorySample/QAItem live in
# storyworlds/results.py).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    place: str
    activity: str
    heirloom: str
    name: str
    gender: str
    elder: str
    cousin: str
    cousin_gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
# (3) Child-level world knowledge, keyed by topic.  These are answerable WITHOUT
# the story; they explain the *elements* the world is built from.
KNOWLEDGE = {
    "antique": [("What does it mean if something is antique?",
                 "An antique is something that was made a long time ago, "
                 "often by hand, and people keep it because it is special.")],
    "fragile": [("Why are some old things fragile?",
                 "Old things are fragile because the materials, like china or "
                 "paint, can dry out and chip if they are dropped or bumped.")],
    "tea": [("What is a tea set?",
             "A tea set is a small group of cups, saucers, and a pot used "
             "for pouring tea, and a tiny one can be used for pretend tea.")],
    "music": [("What is a music box?",
               "A music box is a small box with a tiny comb of metal teeth "
               "inside that plays a melody when you wind a key.")],
    "doll": [("Why are porcelain dolls precious?",
              "Porcelain dolls are precious because the painted faces can "
              "chip or stain if the dolls are not held very gently.")],
    "book": [("Why do old books need careful hands?",
              "Old books need careful hands because the paper and the edges "
              "can tear or chip if the pages are turned too roughly.")],
    "chip": [("What does it mean when a cup is chipped?",
              "A cup is chipped when a small piece has broken off its edge, "
              "leaving a rough little mark where it used to be smooth.")],
    "share": [("Why does sharing feel good?",
               "Sharing feels good because it lets someone else enjoy "
               "something too, and it makes a small moment into a shared one.")],
    "repair": [("Can a chipped cup be fixed?",
                "Yes, a chipped cup can sometimes be mended with a little "
                "safe glue, and a soft cloth can protect the chipped spot.")],
    "memory": [("What is a memory?",
                "A memory is a moment you keep in your heart, like the "
                "feeling of a quiet afternoon with someone you love.")],
    "grandmother": [("Why do grandparents keep old treasures?",
                     "Grandparents keep old treasures because each one "
                     "remembers a story from when they were young.")],
}
KNOWLEDGE_ORDER = ["antique", "fragile", "tea", "music", "doll", "book",
                   "chip", "repair", "share", "memory", "grandmother"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    hero, elder, heirloom, act = f["hero"], f["elder"], f["heirloom_cfg"], f["activity"]
    kw = act.keyword or act.id
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "a child, a '
        f'precious old thing, a small problem, a share" that includes the word "{kw}".',
        f"Tell a gentle story where a {hero.type} named {hero.id} is playing "
        f"with {heirloom.phrase}, and {hero.pronoun('possessive')} little cousin "
        f"clumsily chips it, and the two children find a kind way to share it.",
        f'Write a simple story that uses the noun "{kw}" and ends with an elder '
        f"smiling because the old treasure has made a new memory.",
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    hero, elder, cousin = f["hero"], f["elder"], f["cousin"]
    heirloom = f["heirloom_cfg"]
    act = f["activity"]
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    kw = act.keyword or act.id
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} visits {place} with "
                f"an {heirloom.label} and {pos} little cousin?"
            ),
            answer=(
                f"It is about a little {trait} {hero.type} named {hero.id}, "
                f"{pos} {elder.label_word}, and {pos} little cousin "
                f"{cousin.id}. They share a quiet afternoon with "
                f"{heirloom.phrase}."
            ),
        ),
        QAItem(
            question=(
                f"What did {trait} {hero.id} love most in the {place} before "
                f"the clumsy moment with the {heirloom.label}?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} loved the {heirloom.label} "
                f"on the shelf; the soft colours made {obj} feel calm and "
                f"the room feel like a small museum of old treasures."
            ),
        ),
        QAItem(
            question=(
                f"Why did {elder.id} gently warn {hero.id} to be careful with "
                f"{heirloom.phrase} in {place}?"
            ),
            answer=(
                f"{elder.id} spoke softly about the {heirloom.label} being "
                f"{heirloom.era or 'antique'} and very dear, because pieces "
                f"like that cannot easily be replaced if they are broken."
            ),
        ),
    ]
    # The featured question: what changed and how was it shared.
    if f.get("conflict"):
        qa.append(QAItem(
            question=(
                f"How did {trait} {hero.id} feel when {cousin.id} chipped the "
                f"{heirloom.label} while trying to {act.verb} in {place}?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} felt {pos} eyes sting because "
                f"the {heirloom.label} was {heirloom.era or 'antique'} and "
                f"could not be replaced. {sub.capitalize()} noticed "
                f"{cousin.id}'s worried face and took a slow breath."
            ),
        ))
    # The resolution -- naming what changed and sharing.
    qa.append(QAItem(
        question=(
            f"What did {trait} {hero.id} do after seeing the chipped "
            f"{heirloom.label} on the lace cloth in {place}?"
        ),
        answer=(
            f"{sub.capitalize()} told {cousin.id} that the {heirloom.label} "
            f"was still beautiful, then poured pretend tea with the "
            f"{heirloom.label} and let {cousin.id} choose a cup, so the "
            f"afternoon became a shared one."
        ),
    ))
    qa.append(QAItem(
        question=(
            f"Why did {elder.id} smile at the end of the {kw} afternoon with "
            f"{hero.id} and {cousin.id}?"
        ),
        answer=(
            f"{elder.id} smiled because the old {heirloom.label} had made a "
            f"new memory. The two children had shared the {heirloom.label}, "
            f"and {elder.pronoun()} could set it back on the shelf as a "
            f"little treasure once again."
        ),
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    tags = set(f["activity"].tags)
    tags.add("antique")
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
        if e.damage:
            bits.append(f"damage={e.damage}({e.part})")
        if e.fragile and e.whole:
            bits.append("whole=yes")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        place="parlour",
        activity="tea_party",
        heirloom="teapot",
        name="Theo",
        gender="boy",
        elder="grandmother",
        cousin="Anna",
        cousin_gender="girl",
        trait="gentle",
    ),
    StoryParams(
        place="porch",
        activity="music_box",
        heirloom="musicbox",
        name="Lily",
        gender="girl",
        elder="grandmother",
        cousin="Eli",
        cousin_gender="boy",
        trait="thoughtful",
    ),
    StoryParams(
        place="sunroom",
        activity="doll_show",
        heirloom="dolls",
        name="Mia",
        gender="girl",
        elder="grandmother",
        cousin="Finn",
        cousin_gender="boy",
        trait="kind",
    ),
    StoryParams(
        place="kitchen",
        activity="story_time",
        heirloom="book",
        name="Ben",
        gender="boy",
        elder="grandfather",
        cousin="Maya",
        cousin_gender="girl",
        trait="patient",
    ),
    StoryParams(
        place="parlour",
        activity="tea_party",
        heirloom="teacup",
        name="Zoe",
        gender="girl",
        elder="grandmother",
        cousin="Rose",
        cousin_gender="girl",
        trait="quiet",
    ),
]


def explain_rejection(activity: Activity, heirloom: Heirloom) -> str:
    if not heirloom_at_risk(activity, heirloom):
        return (f"(No story: {activity.gerund} touches {sorted(activity.zone)}, "
                f"but the {heirloom.label}'s fragile part is the "
                f"{heirloom.part} -- it wouldn't get {activity.mess or 'a mark'}, "
                f"so there's no honest problem to solve. "
                f"Try an heirloom with a fragile {sorted(activity.zone)}.)")
    return (f"(No story: nothing in the repair catalog covers the "
            f"{heirloom.label}'s {heirloom.part} after {activity.gerund}. "
            f"The repair has to actually fit the part, so this argument is "
            f"rejected.)")


def explain_gender(heirloom_id: str, gender: str) -> str:
    ok = " / ".join(sorted(HEIRLOOMS[heirloom_id].genders))
    return (f"(No story: a {HEIRLOOMS[heirloom_id].label} isn't a typical "
            f"{gender}'s heirloom here; try --gender {ok}.)")


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate
# (heirloom_at_risk / select_repair / valid_combos).  The rules are inline
# below; the facts are generated from the registries above so the two can
# never drift.  Uses the shared ``asp`` helper + clingo, imported lazily so
# the prose engine runs without them.  See ``python ...py --verify``.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% An heirloom is at risk when the activity touches the part that is fragile.
heirloom_at_risk(A, H) :- touches(A, P), fragile_part(H, P).

% A repair is a compatible fix only when it both guards the damage kind AND
% covers the at-risk part (glue fixes chips but only on handles).
protects(R, A, H) :- repair(R), heirloom_at_risk(A, H),
                     mess_of(A, M), guards(R, M),
                     covers(R, P), fragile_part(H, P).
has_fix(A, H) :- protects(_, A, H).

valid(Place, A, H) :- affords(Place, A), heirloom_at_risk(A, H), has_fix(A, H).
valid_story(Place, A, H, Gender) :- valid(Place, A, H), wears(Gender, H).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("touches", aid, r))
    for hid, h in HEIRLOOMS.items():
        lines.append(asp.fact("heirloom", hid))
        lines.append(asp.fact("fragile_part", hid, h.part))
        if h.plural:
            lines.append(asp.fact("heirloom_plural", hid))
        for g in sorted(h.genders):
            lines.append(asp.fact("wears", g, hid))
    for r in REPAIRS:
        lines.append(asp.fact("repair", r.id))
        for m in sorted(r.guards):
            lines.append(asp.fact("guards", r.id, m))
        for p in sorted(r.covers):
            lines.append(asp.fact("covers", r.id, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    """Clingo's version of valid_combos(): (place, activity, heirloom) triples."""
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    """(place, activity, heirloom, gender) -- gender-aware compatible stories."""
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
        description="Story world sketch: a child, an antique, a clumsy moment, "
                    "a share. Unspecified choices are picked at random (seeded).")
    # A small, debuggable set of pins; any omitted choice is randomized.
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--heirloom", choices=HEIRLOOMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("--cousin")
    ap.add_argument("--cousin-gender", choices=["girl", "boy"])
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
    if args.activity and args.heirloom:
        act, hr = ACTIVITIES[args.activity], HEIRLOOMS[args.heirloom]
        if not (heirloom_at_risk(act, hr) and select_repair(act, hr)):
            raise StoryError(explain_rejection(act, hr))
    if args.gender and args.heirloom and args.gender not in HEIRLOOMS[args.heirloom].genders:
        raise StoryError(explain_gender(args.heirloom, args.gender))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.heirloom is None or c[2] == args.heirloom)
              and (args.gender is None or args.gender in HEIRLOOMS[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, heirloom_id = rng.choice(sorted(combos))
    heirloom = HEIRLOOMS[heirloom_id]
    gender = args.gender or rng.choice(sorted(heirloom.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    cousin_gender = args.cousin_gender or rng.choice(["girl", "boy"])
    cousin = args.cousin or rng.choice(COUSIN_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        heirloom=heirloom_id,
        name=name,
        gender=gender,
        elder=elder,
        cousin=cousin,
        cousin_gender=cousin_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 HEIRLOOMS[params.heirloom], params.name, params.gender,
                 [params.trait, "thoughtful"], params.elder,
                 params.cousin, params.cousin_gender)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, heirloom) combos "
              f"({len(stories)} with gender):\n")
        for place, act, heirloom in triples:
            genders = sorted(g for (pl, a, hr, g) in stories
                             if (pl, a, hr) == (place, act, heirloom))
            print(f"  {place:9} {act:12} {heirloom:9}  [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.activity} at {p.place} (heirloom: {p.heirloom})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
