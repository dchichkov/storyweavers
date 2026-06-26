#!/usr/bin/env python3
"""
storyworlds/worlds/naughty_pile.py
===================================

A standalone *story world* sketch for "The Naughty Pile" tall tale and its
constraint-checked variations.  Modeled on the puddle-jumping world, but
keyed on a different shape: a heap of things, an inner monologue that gets
louder as the pile grows, comic sound effects that land with each new drop,
and a turn toward sharing that resolves the tension.

Initial story (used to build the world model):
---
Way out past the last fence, on a stretch of road where the dust never quite
settled, there lived a tall-tale sort of dog named Bruno.  Bruno was the kind
of dog who could not walk past a stick without picking it up, and he could
not walk past a sock without picking it up, and he could not walk past a shoe
without picking it up -- so by the time he got home his mouth was full and
his back legs were wiggling with all the things he had found.

His boy, Theo, watched from the porch and shook his head.  "Bruno," he said,
"that is a NAUGHTY pile."  But Bruno only thumped his tail, because in his
own head the pile was not naughty at all.  In his own head the pile was a
castle, and the sock was the flag, and the shoe was the gate, and if he just
had one MORE thing the castle would be finished.

THUD went the boot.  CLINK went the can.  CRINKLE went the paper bag.  Each
new thing made the pile wobble, and each new thing made Bruno's little voice
yell "Yes!  Almost!  One more!"  The pile grew taller than the cat, then
taller than the bucket, then taller than the boy himself, and still Bruno
thought: one more.

Then the door opened and out came little Mia, Theo's sister, with two arms
open wide.  She did not scold.  She did not sigh.  She said: "Bruno, that's
a big pile, and big piles are for two."  And so, ever so carefully, she took
half.

Bruno's little voice went quiet.  He blinked.  He looked at his castle, and
at Mia, and at the second half of the castle.  And then he sat, and he let
her have the shoe that was the gate, and he took the sock that was the flag,
and together they played castle until suppertime.

Causal state updates:
---
    take a thing      -> actor.<thing> += 1
                         pile.<thing> += 1
                         actor.urge += 1            (the inner voice gets louder)
                         pile.height += 1           (visual growth)
    thing on pile     -> thing.dirty += 1           (dust + drool)
    pile.tall + new   -> pile.wobble += 1           (instability rises)
    share_event       -> pile.shared += 1
                         actor.urge -> 0            (inner voice goes quiet)
                         actor.calm += 1

Style instruments:
---
    inner monologue   -> a stylized inner sentence, repeated louder as urge
                         climbs, capped when the voice is overwhelmed.
    sound effects     -> one onomatopoeia per item, chosen from a per-kind table.
    sharing           -> the resolution beat; only fires when pile has enough
                         items to split and a partner is present.

This script is a self-contained, classical simulation: small domain, shared
``StoryParams``/``StorySample`` from ``storyworlds/results``, inline ASP twin
for the reasonableness gate, prose driven entirely by world state.
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

# Categories of found thing; each drives its own sound effect and its own
# sharing rule.  Keep this small on purpose -- this is a TinyStories-ish world.
THING_KINDS = {"stick", "sock", "shoe", "boot", "can", "paper_bag", "ball"}

# Items the dog finds along the road.  Realistic for a porch/home setting.
PRIZE_LABELS = {
    "stick":     "stick",
    "sock":      "sock",
    "shoe":      "shoe",
    "boot":      "boot",
    "can":       "tin can",
    "paper_bag": "paper bag",
    "ball":      "old tennis ball",
}

# Onomatopoeia per thing -- the sound effects instrument.  Each item gets a
# landing sound when it is dropped onto the pile.
SOUNDS = {
    "stick":     ["THUD", "TAP", "BONK"],
    "sock":      ["PLOP", "PFFT", "FLOOF"],
    "shoe":      ["CLUNK", "CLOP", "THUMP"],
    "boot":      ["THUD", "BANG", "CLOMP"],
    "can":       ["CLINK", "CLANK", "TINK"],
    "paper_bag": ["CRINKLE", "RUSTLE", "SHHHHRIP"],
    "ball":      ["BOUNCE", "BOP", "BOING"],
}


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # dog, girl, boy, sock, shoe ...
    label: str = ""                # short reference, e.g. "stick", "tin can"
    phrase: str = ""               # full noun phrase, e.g. "a long old stick"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    partner: Optional[str] = None  # who shares the pile at the end
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # mental

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "sister": "sister",
                "brother": "brother"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Pile: a separate aggregate that tracks the heap itself (height, wobble).
# ---------------------------------------------------------------------------
@dataclass
class Pile:
    id: str
    owner: str                     # whose pile it is (the collector)
    things: list[str] = field(default_factory=list)   # ids of things, in drop order
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the porch"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    """The collecting walk: a sequence of found things + how they're dropped."""
    id: str
    verb: str                # "gather up the things"
    gerund: str              # "gathering up things"
    items: list[str]         # ordered list of thing kinds the dog finds
    noise: str               # ambient line, e.g. "the road stretched quiet"
    keyword: str = ""        # topic word for prompts
    tags: set[str] = field(default_factory=set)


@dataclass
class Partner:
    """Who joins the collector at the end to share the pile."""
    id_kind: str             # "sister" | "brother" | "mother" | "father" | "friend"
    phrase: str              # "his little sister"
    shared_phrase: str       # "big piles are for two"
    wants_to_take: str       # which item kind they want from the pile


# ---------------------------------------------------------------------------
# World: entity store + pile + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.piles: dict[str, Pile] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.weather: str = ""
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.piles = copy.deepcopy(self.piles)
        clone.fired = set(self.fired)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_dirty(world: World) -> list[str]:
    """A thing on a pile accumulates dirt (dust + drool + a bit of road)."""
    out: list[str] = []
    for pile in world.piles.values():
        for tid in pile.things:
            thing = world.entities.get(tid)
            if not thing or not thing.owner:
                continue
            sig = ("dirty", tid)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            thing.meters["dirty"] += 1
    return out


def _r_wobble(world: World) -> list[str]:
    """Pile height >= 3 and a new item just landed -> wobble rises."""
    for pile in world.piles.values():
        if pile.meters["height"] < 3:
            continue
        sig = ("wobble", pile.id, int(pile.meters["height"]))
        if sig in world.fired:
            continue
        world.fired.add(sig)
        pile.meters["wobble"] += 1
        return ["__wobble__"]
    return []


def _r_urge(world: World) -> list[str]:
    """A new item on the pile makes the collector's inner voice louder."""
    for pile in world.piles.values():
        if not pile.things:
            continue
        sig = ("urge", pile.id, len(pile.things))
        if sig in world.fired:
            continue
        world.fired.add(sig)
        owner = world.get(pile.owner)
        owner.memes["urge"] += 1
        return ["__urge__"]
    return []


def _r_calm(world: World) -> list[str]:
    """Once the pile is shared, the inner voice goes quiet."""
    for pile in world.piles.values():
        if pile.memes["shared"] < THRESHOLD:
            continue
        owner = world.get(pile.owner)
        if owner.memes["calm"] >= THRESHOLD:
            continue
        sig = ("calm", pile.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        owner.memes["calm"] += 1
        owner.memes["urge"] = 0.0
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="dirty",    tag="physical", apply=_r_dirty),
    Rule(name="wobble",   tag="physical", apply=_r_wobble),
    Rule(name="urge",     tag="mental",   apply=_r_urge),
    Rule(name="calm",     tag="mental",   apply=_r_calm),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    """Apply all rules until nothing new fires."""
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__wobble__"
                                and s != "__urge__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers.
# ---------------------------------------------------------------------------
def pile_split_ok(pile: Pile) -> bool:
    """The pile is shareable when it has at least 2 things and a wobble."""
    return len(pile.things) >= 2 and pile.meters["wobble"] >= THRESHOLD


def select_partner(activity: Activity, gender: str) -> Optional[Partner]:
    """A partner whose 'wants_to_take' kind actually appears in the pile."""
    kinds = set(activity.items)
    for partner in PARTNERS:
        if partner.wants_to_take in kinds:
            return partner
    return None


def predict_height(world: World, owner_id: str, items: list[str]) -> int:
    """Forward-sim: how tall would the pile be after dropping these items?"""
    sim = world.copy()
    _drop_items(sim, sim.get(owner_id), items, narrate=False)
    return int(sim.piles[owner_id].meters["height"])


# ---------------------------------------------------------------------------
# Sound effects + inner monologue: the two style instruments.
# ---------------------------------------------------------------------------
def sound_for(kind: str, rng: random.Random) -> str:
    return rng.choice(SOUNDS[kind])


def inner_line(actor: Entity, kind: str, urge: float) -> str:
    """The collector's inner voice, scaled by accumulated urge."""
    if urge <= 0.5:
        return f"Inside his head a little voice said: \"Yes, a {kind} -- perfect.\""
    if urge <= 1.5:
        return f"The little voice in his head got a bit louder: \"Almost!  The {kind} is just right.\""
    if urge <= 2.5:
        return f"The little voice in his head YELLED: \"YES!  The {kind}!  ONE MORE and the pile is FINISHED!\""
    return f"The little voice in his head would not stop: \"{kind.upper()}!  {kind.upper()}!  ONE MORE!\""


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def setting_detail(setting: Setting) -> str:
    return {
        "the porch":   "the porch boards creaked, and the road went quiet and wide.",
        "the yard":    "the yard was long, and the grass tickled little paws.",
        "the lane":    "the lane was dusty, and the gate hung a little open.",
        "the driveway":"the driveway was full of gravel, and the cat watched from the wall.",
    }.get(setting.place, f"{setting.place.capitalize()} stretched out wide.")


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "naughty"), "")
    desc = f"a tall-tale {trait} {hero.type}".strip()
    world.say(
        f"Way out past the last fence, on a stretch of road where the dust never "
        f"quite settled, there lived {desc} named {hero.id}."
    )


def habit(world: World, hero: Entity) -> None:
    """The collector's habit: anything on the ground becomes a treasure."""
    world.say(
        f"{hero.id} was the kind of {hero.type} who could not walk past a stick "
        f"without picking it up, and could not walk past a sock without picking "
        f"it up, and could not walk past a shoe without picking it up."
    )


def family_setup(world: World, hero: Entity, partner_entity: Entity) -> None:
    world.say(
        f"So by the time {hero.id} wandered home, his mouth was full and his back "
        f"legs were wiggling with all the things he had found."
    )
    world.say(
        f"{partner_entity.id}, who lived at the {world.setting.place} and was "
        f"smaller than {hero.id} by a whole head, watched from the step and "
        f"crossed {partner_entity.pronoun('possessive')} arms."
    )


def scold(world: World, partner_entity: Entity, hero: Entity) -> None:
    partner_entity.memes["annoy"] += 1
    world.say(
        f'"{hero.id}," {partner_entity.id} said, shaking '
        f"{partner_entity.pronoun('possessive')} head, "
        f'"that is a NAUGHTY pile."'
    )


def first_drop(world: World, hero: Entity, kind: str, rng: random.Random) -> None:
    """Drop the first item and fire the very first inner line."""
    pile = _drop_one(world, hero, kind)
    label = PRIZE_LABELS[kind]
    sound = sound_for(kind, rng)
    world.say(
        f"{hero.pronoun('subject').capitalize()} set the {label} down with a "
        f"small {sound}."
    )
    world.say(inner_line(hero, label, hero.memes["urge"]))


def middle_drop(world: World, hero: Entity, kind: str, rng: random.Random) -> None:
    """Drop a middle item, with sound + growing inner line."""
    _drop_one(world, hero, kind)
    label = PRIZE_LABELS[kind]
    sound = sound_for(kind, rng)
    # Sound effects land in tall-tale CAPS as the pile grows.
    if hero.memes["urge"] >= 2.0:
        world.say(f"{sound} went the {label}.")
    else:
        world.say(f"{sound} went the {label}.")
    world.say(inner_line(hero, label, hero.memes["urge"]))


def final_drop(world: World, hero: Entity, kind: str, rng: random.Random) -> None:
    """The last item: this is the one the inner voice was waiting for."""
    _drop_one(world, hero, kind)
    label = PRIZE_LABELS[kind]
    sound = sound_for(kind, rng)
    world.say(f"And then -- {sound.upper()}! -- the {label}.")
    world.say(inner_line(hero, label, hero.memes["urge"]))


def height_report(world: World, hero: Entity, pile: Pile) -> None:
    """Tall-tale escalation: pile grows taller than successive benchmarks."""
    h = int(pile.meters["height"])
    if h >= 4:
        world.say(
            f"The pile grew taller than the cat, then taller than the bucket, "
            f"then taller than {hero.id} himself."
        )
    elif h >= 3:
        world.say(f"The pile grew taller than the bucket.")
    elif h >= 2:
        world.say(f"The pile grew taller than a shoe.")


def _drop_one(world: World, actor: Entity, kind: str) -> Pile:
    """Drop one thing of a given kind onto the actor's pile.  Idempotent per kind."""
    label = PRIZE_LABELS[kind]
    thing_id = f"{actor.id}_{kind}_{len(world.piles[actor.id].things)}"
    thing = world.add(Entity(
        id=thing_id, kind="thing", type=kind, label=label,
        phrase=f"a {label}", owner=actor.id,
    ))
    pile = world.piles[actor.id]
    pile.things.append(thing_id)
    pile.meters["height"] += 1
    actor.meters[kind] += 1
    propagate(world, narrate=False)
    height_report(world, actor, pile)
    return pile


def _drop_items(world: World, actor: Entity, kinds: list[str], narrate: bool = True) -> None:
    """Drop a sequence of items (used by the screenplay and by predict_height)."""
    for kind in kinds:
        _drop_one(world, actor, kind)
        if not narrate:
            continue


def partner_enters(world: World, partner_entity: Entity, partner_def: Partner) -> None:
    world.say(
        f"Then the door opened and out came {partner_def.phrase}, "
        f"with two arms open wide."
    )


def partner_offers(world: World, partner_entity: Entity, partner_def: Partner) -> None:
    world.say(
        f"{partner_entity.pronoun('subject').capitalize()} did not scold.  "
        f"{partner_entity.pronoun('subject').capitalize()} did not sigh.  "
        f'{partner_entity.pronoun('subject').capitalize()} said: '
        f'"That is a big pile, and {partner_def.shared_phrase}."'
    )


def share(world: World, hero: Entity, partner_entity: Entity,
          partner_def: Partner, pile: Pile) -> None:
    """The sharing beat.  Splits the pile and quiets the inner voice."""
    if not pile_split_ok(pile):
        return
    wanted = partner_def.wants_to_take
    partner_kind = wanted
    partner_item_id = None
    for tid in pile.things:
        if world.entities[tid].type == partner_kind:
            partner_item_id = tid
            break
    pile.memes["shared"] += 1
    partner_entity.memes["calm"] += 1
    propagate(world, narrate=False)              # fires the calm rule

    kept_label = ""
    if partner_item_id:
        world.entities[partner_item_id].owner = partner_entity.id
        kept_label = world.entities[partner_item_id].label
    half_phrase = (f"she took the {kept_label}"
                   if kept_label else "she took half the heap")
    world.say(
        f"And so, ever so carefully, {half_phrase}."
    )
    world.say(
        f"{hero.id}'s little voice went quiet.  {hero.pronoun('subject').capitalize()} "
        f"blinked.  {hero.pronoun('subject').capitalize()} looked at {hero.pronoun('possessive')} "
        f"castle, and at {partner_entity.id}, and at the second half of the castle."
    )
    if partner_item_id:
        world.say(
            f"And then {hero.id} sat, and let {partner_entity.id} have "
            f"the {kept_label} that was the gate, and {hero.pronoun('subject')} took "
            f"the {pile_label_excluding(pile, partner_item_id, world)} "
            f"that was the flag, and together they played castle until suppertime."
        )
    else:
        world.say(
            f"And then {hero.id} sat, and let {partner_entity.id} have half, "
            f"and together they played castle until suppertime."
        )


def pile_label_excluding(pile: Pile, exclude_id: str, world: World) -> str:
    for tid in pile.things:
        if tid != exclude_id:
            return world.entities[tid].label
    return "old sock"


# ---------------------------------------------------------------------------
# Screenplay.
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, partner_def: Partner,
         hero_name: str = "Bruno", hero_type: str = "dog",
         partner_name: str = "Mia", partner_type: str = "sister",
         rng: Optional[random.Random] = None) -> World:
    rng = rng or random.Random()
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["naughty", "tall-tale"],
    ))
    partner_entity = world.add(Entity(
        id=partner_name, kind="character", type=partner_type,
        traits=["small", "even-tempered"],
    ))
    hero.partner = partner_entity.id
    pile = Pile(id=hero_name, owner=hero_name)
    world.piles[hero_name] = pile

    # Act 1 -- setup: who, what they love, the family on the porch.
    introduce(world, hero)
    habit(world, hero)
    family_setup(world, hero, partner_entity)
    world.say(setting_detail(setting))

    # Act 2 -- the collecting walk, with sound effects + inner monologue.
    world.para()
    scold(world, partner_entity, hero)
    items = activity.items
    if not items:
        return world                                  # empty activity handled below
    first_drop(world, hero, items[0], rng)
    for kind in items[1:-1]:
        middle_drop(world, hero, kind, rng)
    if len(items) > 1:
        final_drop(world, hero, items[-1], rng)

    # Act 3 -- the partner enters, offers sharing, splits the pile.
    world.para()
    partner_enters(world, partner_entity, partner_def)
    partner_offers(world, partner_entity, partner_def)
    share(world, hero, partner_entity, partner_def, pile)

    world.facts.update(
        hero=hero, partner_entity=partner_entity, partner_def=partner_def,
        activity=activity, setting=setting, pile=pile,
        n_items=len(pile.things), final_urge=hero.memes["urge"],
        resolved=hero.memes["calm"] >= THRESHOLD,
        kinds_dropped=list(items),
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "porch":    Setting(place="the porch",    indoor=False, affords={"walk_a", "walk_b"}),
    "yard":     Setting(place="the yard",     indoor=False, affords={"walk_a", "walk_c"}),
    "lane":     Setting(place="the lane",     indoor=False, affords={"walk_b", "walk_c"}),
    "driveway": Setting(place="the driveway", indoor=False, affords={"walk_a", "walk_b"}),
}

ACTIVITIES = {
    "walk_a": Activity(
        id="walk_a",
        verb="bring the things home",
        gerund="bringing the things home",
        items=["stick", "sock", "can", "paper_bag", "ball"],
        noise="the road stretched quiet",
        keyword="naughty",
        tags={"naughty", "pile"},
    ),
    "walk_b": Activity(
        id="walk_b",
        verb="haul the heap up the path",
        gerund="hauling the heap",
        items=["sock", "shoe", "boot", "stick", "paper_bag"],
        noise="the gravel crunched underfoot",
        keyword="pile",
        tags={"naughty", "pile"},
    ),
    "walk_c": Activity(
        id="walk_c",
        verb="tote the loot to the door",
        gerund="toting the loot",
        items=["ball", "can", "stick", "boot", "sock"],
        noise="the gate hung a little open",
        keyword="naughty",
        tags={"naughty", "pile"},
    ),
}

PARTNERS = [
    Partner(
        id_kind="sister",
        phrase="his little sister",
        shared_phrase="big piles are for two",
        wants_to_take="shoe",
    ),
    Partner(
        id_kind="brother",
        phrase="his little brother",
        shared_phrase="big piles are for sharing",
        wants_to_take="boot",
    ),
    Partner(
        id_kind="mother",
        phrase="his mom",
        shared_phrase="big piles are for the family",
        wants_to_take="sock",
    ),
    Partner(
        id_kind="father",
        phrase="his dad",
        shared_phrase="big piles are for two",
        wants_to_take="can",
    ),
    Partner(
        id_kind="friend",
        phrase="his small friend from next door",
        shared_phrase="big piles are for friends",
        wants_to_take="ball",
    ),
}

DOG_NAMES = ["Bruno", "Buster", "Rex", "Hugo", "Otis", "Pip", "Ranger", "Barkley"]
BOY_NAMES = ["Theo", "Ben", "Sam", "Finn", "Eli", "Max", "Jack", "Noah"]
GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
TRAITS = ["tall-tale", "stubborn", "lively", "cheerful", "spirited"]


def valid_combos() -> list[tuple[str, str]]:
    """(setting_id, activity_id) pairs that pass the reasonableness gate.

    Every (setting, activity) pair in the registries is reasonable: each
    setting affords a set that includes both walks, and every walk yields a
    pile that the partner rule can split.  Returned as a curated list."""
    return [
        (sid, aid)
        for sid, s in SETTINGS.items()
        for aid in s.affords
    ]


# ---------------------------------------------------------------------------
# Per-world parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    setting: str
    activity: str
    partner: str
    hero_name: str
    hero_type: str
    partner_name: str
    partner_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three separate sets.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "pile": [
        ("What is a pile?",
         "A pile is a heap of things stacked or gathered in one spot, "
         "usually taller than it is wide."),
    ],
    "naughty": [
        ("What does naughty mean?",
         "Naughty means being a little bit badly behaved, like doing "
         "something you have been told not to do."),
    ],
    "share": [
        ("What does sharing mean?",
         "Sharing means letting someone else use or play with something "
         "of yours, so you both get to enjoy it."),
    ],
    "stick": [
        ("What is a stick good for?",
         "A stick is good for fetching, pointing at things, drawing lines "
         "in the dirt, or pretending it is a sword."),
    ],
    "sock": [
        ("Where does a lost sock go?",
         "A lost sock can slip behind the dryer, slide under the bed, "
         "or land in the garden if it bounces out of the laundry basket."),
    ],
    "shoe": [
        ("Why do shoes come in pairs?",
         "Shoes come in pairs because your feet come in pairs -- one for "
         "the left foot and one for the right foot."),
    ],
    "can": [
        ("Why do tin cans make a clinking sound?",
         "Tin cans make a clinking sound because the metal is hard and "
         "thin, so it rings a little when it bumps into things."),
    ],
    "ball": [
        ("Why do balls bounce?",
         "Balls bounce because the rubber or air inside pushes them back "
         "into shape after they hit the ground."),
    ],
}
KNOWLEDGE_ORDER = ["pile", "naughty", "share", "stick", "sock", "shoe",
                   "can", "ball"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    hero, partner_entity, act = f["hero"], f["partner_entity"], f["activity"]
    kw = act.keyword or "naughty"
    items_phrase = ", ".join(PRIZE_LABELS[k] for k in act.items)
    return [
        f'Write a short tall-tale story for a 3-to-5-year-old on the theme '
        f'"a heap, an inner voice, a partner" that includes the word "{kw}".',
        f"Tell a tall-tale story where {hero.id} the {hero.type} gathers "
        f"{items_phrase} into a naughty pile, and {partner_entity.id} shows "
        f"up at the end to share it.",
        f'Write a simple story that uses the noun "{kw}", uses onomatopoeia '
        f"for the sounds things make when they land, and ends with sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    hero, partner_entity, act, pile = f["hero"], f["partner_entity"], f["activity"], f["pile"]
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    place = world.setting.place
    items_phrase = ", ".join(PRIZE_LABELS[k] for k in act.items)
    trait = next((t for t in hero.traits if t != "naughty"), hero.type)
    n_items = f["n_items"]
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} the {hero.type} builds "
                f"a pile of {items_phrase} at {place}?"
            ),
            answer=(
                f"It is about {trait} {hero.id} the {hero.type}, who is a "
                f"tall-tale sort of collector, and {pos} smaller friend "
                f"{partner_entity.id} who lives at {place}."
            ),
        ),
        QAItem(
            question=(
                f"What did {trait} {hero.id} keep doing on the way home before "
                f"the pile at {place} got too tall?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} could not walk past a stick, "
                f"sock, shoe, boot, can, paper bag, or ball without picking it "
                f"up. {sub.capitalize()} gathered {items_phrase} into a heap "
                f"on {pos} way home."
            ),
        ),
        QAItem(
            question=(
                f"How many things ended up in {hero.id}'s pile at {place} before "
                f"{partner_entity.id} offered to share?"
            ),
            answer=(
                f"There were {n_items} things in the pile: {items_phrase}. "
                f"The pile grew taller than the bucket, then taller than "
                f"{hero.id} himself, while {hero.id}'s little voice kept "
                f"asking for one more."
            ),
        ),
    ]
    if f.get("resolved"):
        pd = f["partner_def"]
        kept = ""
        for tid in pile.things:
            if world.entities[tid].type == pd.wants_to_take:
                kept = world.entities[tid].label
                break
        qa.append(QAItem(
            question=(
                f"How did {partner_entity.id} share {hero.id}'s naughty pile of "
                f"{items_phrase} at {place}?"
            ),
            answer=(
                f"{partner_entity.id} did not scold. {partner_entity.id} said "
                f'"{pd.shared_phrase.capitalize()}," and so {partner_entity.id} '
                f"carefully took {('the ' + kept) if kept else 'half the heap'}. "
                f"{hero.id}'s little voice went quiet, and they played castle "
                f"together until suppertime."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"What happened to {hero.id}'s inner voice after {partner_entity.id} "
                f"shared the {', '.join(PRIZE_LABELS[k] for k in act.items[:-1])} "
                f"pile at {place}?"
            ),
            answer=(
                f"The little voice went quiet. {hero.id} blinked, looked at "
                f"{pos} castle and at {partner_entity.id}, and sat down to play "
                f"together. The urge that said 'one more' was gone."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    tags = set(f["activity"].tags)
    tags.update(f["activity"].items)
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
# CLI / trace.
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    for pid, pile in world.piles.items():
        meters = {k: v for k, v in pile.meters.items() if v}
        memes = {k: v for k, v in pile.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"pile_meters={dict(meters)}")
        if memes:
            bits.append(f"pile_memes={dict(memes)}")
        bits.append(f"things={pile.things}")
        lines.append(f"  PILE {pid:8} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="porch",
        activity="walk_a",
        partner="sister",
        hero_name="Bruno",
        hero_type="dog",
        partner_name="Mia",
        partner_type="sister",
    ),
    StoryParams(
        setting="yard",
        activity="walk_b",
        partner="brother",
        hero_name="Buster",
        hero_type="dog",
        partner_name="Theo",
        partner_type="brother",
    ),
    StoryParams(
        setting="lane",
        activity="walk_c",
        partner="mother",
        hero_name="Rex",
        hero_type="dog",
        partner_name="Lily",
        partner_type="mother",
    ),
    StoryParams(
        setting="driveway",
        activity="walk_a",
        partner="father",
        hero_name="Hugo",
        hero_type="dog",
        partner_name="Ben",
        partner_type="father",
    ),
]


def explain_rejection(activity: Activity) -> str:
    if not activity.items:
        return (f"(No story: activity {activity.id!r} has no items to drop, "
                f"so the pile can never grow.)")
    if len(activity.items) < 2:
        return (f"(No story: activity {activity.id!r} yields only one item, "
                f"so the pile can never be shared.)")
    return ""


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- inline twin of the reasonableness gate.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Every (setting, activity) pair is reasonable iff the setting affords it
% AND the activity has at least two items (the pile must be splittable).
reasonable(Setting, Activity) :-
    affords(Setting, Activity),
    item(Activity, _, _).

splittable(Activity) :- n_items(Activity, N), N >= 2.
valid(Setting, Activity) :- reasonable(Setting, Activity), splittable(Activity).

% Partner is compatible iff the activity contains an item of the partner's kind.
compatible_partner(Setting, Activity, Partner) :-
    valid(Setting, Activity),
    partner(Partner, _Wants),
    wants(Partner, Kind),
    item(Activity, Kind, _).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for i, kind in enumerate(a.items):
            lines.append(asp.fact("item", aid, kind, i))
        lines.append(asp.fact("n_items", aid, len(a.items)))
    for p in PARTNERS:
        lines.append(asp.fact("partner", p.id_kind))
        lines.append(asp.fact("wants", p.id_kind, p.wants_to_take))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    """Clingo's version of valid_combos(): (setting, activity) pairs."""
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_compatible_partners() -> list[tuple]:
    """(setting, activity, partner_kind) triples that pass the ASP gate."""
    import asp
    model = asp.one_model(asp_program("#show compatible_partner/3."))
    return sorted(set(asp.atoms(model, "compatible_partner")))


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
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a naughty pile, an inner voice, "
                    "sound effects, and sharing.  Unspecified choices are "
                    "picked at random (seeded).")
    ap.add_argument("--setting",  choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--partner",  choices=[p.id_kind for p in PARTNERS])
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["dog"])
    ap.add_argument("--partner-name")
    ap.add_argument("--partner-type",
                    choices=["sister", "brother", "mother", "father", "friend"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true",
                    help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    """Fill in unspecified choices at random; reject invalid combos explicitly."""
    if args.activity:
        msg = explain_rejection(ACTIVITIES[args.activity])
        if msg:
            raise StoryError(msg)

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.activity is None or c[1] == args.activity)]
    if not combos:
        raise StoryError("(No valid (setting, activity) matches the given options.)")

    setting_id, activity_id = rng.choice(sorted(combos))
    partner_id = args.partner or rng.choice([p.id_kind for p in PARTNERS])
    partner_def = next(p for p in PARTNERS if p.id_kind == partner_id)
    if partner_def.wants_to_take not in ACTIVITIES[activity_id].items:
        # Pick a partner whose wanted kind is in the activity's items.
        for p in PARTNERS:
            if p.wants_to_take in ACTIVITIES[activity_id].items:
                partner_id = p.id_kind
                partner_def = p
                break

    hero_name = args.hero_name or rng.choice(DOG_NAMES)
    hero_type = args.hero_type or "dog"
    partner_name = args.partner_name or rng.choice(
        GIRL_NAMES if partner_def.id_kind in {"sister", "mother"} else BOY_NAMES)
    partner_type = args.partner_type or partner_def.id_kind

    return StoryParams(
        setting=setting_id,
        activity=activity_id,
        partner=partner_id,
        hero_name=hero_name,
        hero_type=hero_type,
        partner_name=partner_name,
        partner_type=partner_type,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + Q&A."""
    partner_def = next(p for p in PARTNERS if p.id_kind == params.partner)
    world = tell(SETTINGS[params.setting], ACTIVITIES[params.activity],
                 partner_def, params.hero_name, params.hero_type,
                 params.partner_name, params.partner_type,
                 rng=random.Random(params.seed if params.seed is not None else 0))
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
        print(asp_program("#show compatible_partner/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, combos = asp_compatible_partners(), asp_valid_combos()
        print(f"{len(combos)} compatible (setting, activity) combos, "
              f"{len(triples)} with partner:\n")
        for setting, activity in combos:
            partners = sorted(p for (s, a, p) in triples
                              if (s, a) == (setting, activity))
            print(f"  {setting:9} {activity:8}  [{', '.join(partners)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = []
        for i, p in enumerate(CURATED):
            p = StoryParams(**{**p.__dict__, "seed": base_seed + i})
            samples.append(generate(p))
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
            header = f"### {p.hero_name}: {p.activity} at {p.setting} (partner: {p.partner})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
