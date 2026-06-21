#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lob_hold_generate_friendship_misunderstanding_nursery_rhyme.py
================================================================================================

A small standalone storyworld about two friends in a sing-song, nursery-rhyme
garden. One friend asks the other to hold something while a small object is
lobbed across a patch. A misunderstanding makes the toss go wrong, feelings
wobble, and then the friends talk plainly, mend the mix-up, and finish the game
together. The ending image proves the repair: the friends work side by side and
the garden begins to generate tiny green life.

The required seed words appear naturally in this domain:
- "lob"    : one friend makes a gentle little toss
- "hold"   : the other friend must hold the right catching thing
- "generate": warm rain and patient care generate sprouts

This world keeps the parameter space narrow on purpose. Not every item belongs
in every holder, and not every misunderstanding is reasonable for every holder.
Invalid explicit choices raise StoryError with an explanation.

Run it
------
    python storyworlds/worlds/gpt-5.4/lob_hold_generate_friendship_misunderstanding_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/lob_hold_generate_friendship_misunderstanding_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/lob_hold_generate_friendship_misunderstanding_nursery_rhyme.py --qa
    python storyworlds/worlds/gpt-5.4/lob_hold_generate_friendship_misunderstanding_nursery_rhyme.py --trace
    python storyworlds/worlds/gpt-5.4/lob_hold_generate_friendship_misunderstanding_nursery_rhyme.py --verify
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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Core entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"         # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    portable: bool = False
    open_top: bool = False
    soft: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen"}
        male = {"boy", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    ground: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LobThing:
    id: str
    label: str
    phrase: str
    plural_name: str
    spill_word: str
    landing: str
    can_plant: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Holder:
    id: str
    label: str
    phrase: str
    held_on: str
    open_top: bool = True
    soft: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    heard_as: str
    held_instead: str
    reason: str
    needs_open_holder: bool = True
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World and rules
# ---------------------------------------------------------------------------
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
        return [e for e in self.entities.values() if e.role in {"lobber", "holder"}]

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


def _r_spill_stings(world: World) -> list[str]:
    out: list[str] = []
    seeds = world.get("thing")
    if seeds.meters["spilled"] < THRESHOLD:
        return out
    sig = ("spill_stings",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["worry"] += 1
    world.get("friendship").meters["tangle"] += 1
    out.append("__spill__")
    return out


def _r_plain_words_mend(world: World) -> list[str]:
    out: list[str] = []
    if world.get("friendship").meters["tangle"] < THRESHOLD:
        return out
    if world.get("friendship").meters["plain_words"] < THRESHOLD:
        return out
    sig = ("plain_words_mend",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("friendship").meters["mended"] += 1
    world.get("friendship").meters["tangle"] = 0.0
    for kid in world.kids():
        kid.memes["worry"] = 0.0
        kid.memes["trust"] += 1
        kid.memes["relief"] += 1
    out.append("__mended__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="spill_stings", tag="social", apply=_r_spill_stings),
    Rule(name="plain_words_mend", tag="social", apply=_r_plain_words_mend),
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


# ---------------------------------------------------------------------------
# Constraints and prediction
# ---------------------------------------------------------------------------
def holder_fits(thing: LobThing, holder: Holder) -> bool:
    return holder.open_top and thing.can_plant


def misunderstanding_fits(holder: Holder, misunderstanding: Misunderstanding) -> bool:
    if misunderstanding.needs_open_holder and not holder.open_top:
        return False
    if misunderstanding.id == "hold_corners":
        return holder.soft
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for thing_id, thing in THINGS.items():
            for holder_id, holder in HOLDERS.items():
                if not holder_fits(thing, holder):
                    continue
                for mis_id, mis in MISUNDERSTANDINGS.items():
                    if misunderstanding_fits(holder, mis):
                        combos.append((place_id, thing_id, holder_id, mis_id))
    return combos


def predict_spill(holder: Holder, misunderstanding: Misunderstanding) -> bool:
    return misunderstanding_fits(holder, misunderstanding)


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def opening_verse(world: World, place: Place, a: Entity, b: Entity, thing: LobThing) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"In {place.label}, where the {place.ground} lay neat, "
        f"{a.id} and {b.id} came skipping on little feet."
    )
    world.say(
        f'{a.id} had {thing.phrase}, round and dry and small, '
        f'and both good friends meant to share them all.'
    )


def plan_game(world: World, a: Entity, b: Entity, holder: Holder, thing: LobThing) -> None:
    world.say(
        f'"Please hold {holder.phrase}," sang {a.id}, "steady as you stand. '
        f'I will lob the {thing.plural_name} over with a careful hand."'
    )
    b.memes["trust"] += 1
    world.say(
        f'{b.id} nodded brightly, ready to help. The little game felt easy, '
        f'and friendship hummed between them like a bell.'
    )


def muddle(world: World, a: Entity, b: Entity, holder: Holder, misunderstanding: Misunderstanding) -> None:
    b.memes["confusion"] += 1
    world.say(
        f"But {b.id} heard "{misunderstanding.heard_as}" instead, {misunderstanding.reason}. "
        f"So {b.pronoun()} reached to {misunderstanding.held_instead}, not to hold {holder.phrase} the way {a.id} meant.'
    )


def do_lob(world: World, a: Entity, b: Entity, thing_ent: Entity, holder_ent: Entity, thing: LobThing) -> None:
    a.meters["lobbed"] += 1
    world.say(
        f'Up went {a.id}\'s arm with a tiny, tidy lob. '
        f'The first little {thing.spill_word} arced through the air like a bobbing bead.'
    )
    thing_ent.meters["spilled"] += 1
    holder_ent.meters["missed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But there was no proper place for it to land. The {thing.plural_name} pattered down on the path and into the border bed."
    )


def hurt_feelings(world: World, a: Entity, b: Entity) -> None:
    a.memes["cross"] += 1
    b.memes["sad"] += 1
    world.say(
        f'"Oh!" cried {a.id}. "I asked you to hold it." {b.id} blinked and looked low. '
        f'For one small breath, each friend thought the other already knew.'
    )


def clear_talk(world: World, a: Entity, b: Entity, holder: Holder, misunderstanding: Misunderstanding) -> None:
    world.get("friendship").meters["plain_words"] += 1
    propagate(world, narrate=False)
    world.say(
        f'Then {a.id} took a softer tone. "I meant hold {holder.phrase}," {a.pronoun()} said. '
        f'"Not {misunderstanding.held_instead}."'
    )
    world.say(
        f'{b.id} pressed a hand to {b.pronoun("possessive")} chest. '
        f'"Oh! I heard "{misunderstanding.heard_as}," not "hold {holder.label}." '
        f'I was trying to help."'
    )


def mend_and_gather(world: World, a: Entity, b: Entity, thing_ent: Entity, thing: LobThing, holder: Holder) -> None:
    thing_ent.meters["gathered"] += 1
    world.say(
        f'So down they knelt, side by side, and gathered each stray {thing.spill_word}. '
        f'This time {b.id} did hold {holder.phrase} still and wide.'
    )
    world.say(
        f'The muddle shrank as quickly as it had grown. Plain words made room for friendship again.'
    )


def plant_and_end(world: World, a: Entity, b: Entity, place: Place, thing_ent: Entity, thing: LobThing) -> None:
    if thing.can_plant:
        thing_ent.meters["planted"] += 1
        thing_ent.meters["sprouting"] += 1
        world.say(
            f'They tucked the {thing.plural_name} into the soil in a neat brown row, '
            f'and patted the earth with fingers soft and slow.'
        )
        world.say(
            f'Soon warm rain and kindly sun would generate tiny green tips there, '
            f'and {a.id} with {b.id} would watch them rise in the gentle air.'
        )
    world.say(
        f'So in {place.label}, by the end of day, the friends walked home in step again, '
        f'with clearer words and cheerful hearts at play.'
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def tell(
    place: Place,
    thing: LobThing,
    holder: Holder,
    misunderstanding: Misunderstanding,
    lobber_name: str = "Mira",
    lobber_gender: str = "girl",
    holder_name: str = "Pip",
    holder_gender: str = "boy",
) -> World:
    world = World()
    a = world.add(Entity(
        id=lobber_name,
        kind="character",
        type=lobber_gender,
        role="lobber",
        label=lobber_name,
        portable=True,
    ))
    b = world.add(Entity(
        id=holder_name,
        kind="character",
        type=holder_gender,
        role="holder",
        label=holder_name,
        portable=True,
    ))
    thing_ent = world.add(Entity(
        id="thing",
        type="thing",
        label=thing.label,
        phrase=thing.phrase,
        tags=set(thing.tags),
        portable=True,
    ))
    holder_ent = world.add(Entity(
        id="holder",
        type="holder",
        label=holder.label,
        phrase=holder.phrase,
        tags=set(holder.tags),
        portable=True,
        open_top=holder.open_top,
        soft=holder.soft,
    ))
    world.add(Entity(
        id="friendship",
        type="bond",
        label="friendship",
    ))

    opening_verse(world, place, a, b, thing)
    plan_game(world, a, b, holder, thing)

    world.para()
    muddle(world, a, b, holder, misunderstanding)
    do_lob(world, a, b, thing_ent, holder_ent, thing)
    hurt_feelings(world, a, b)

    world.para()
    clear_talk(world, a, b, holder, misunderstanding)
    mend_and_gather(world, a, b, thing_ent, thing, holder)

    world.para()
    plant_and_end(world, a, b, place, thing_ent, thing)

    world.facts.update(
        place=place,
        thing=thing,
        holder=holder,
        misunderstanding=misunderstanding,
        lobber=a,
        holder_friend=b,
        thing_ent=thing_ent,
        holder_ent=holder_ent,
        spilled=thing_ent.meters["spilled"] >= THRESHOLD,
        mended=world.get("friendship").meters["mended"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
PLACES = {
    "garden": Place(
        id="garden",
        label="the garden",
        opening="where marigolds nodded in the sun",
        ground="garden rows",
        tags={"garden", "sprout"},
    ),
    "yard": Place(
        id="yard",
        label="the yard",
        opening="where the old fence cast a stripe of shade",
        ground="yard path",
        tags={"yard", "sprout"},
    ),
    "meadow_edge": Place(
        id="meadow_edge",
        label="the meadow edge",
        opening="where clover bobbed beside a low stone wall",
        ground="meadow fringe",
        tags={"meadow", "sprout"},
    ),
}

THINGS = {
    "pea_seeds": LobThing(
        id="pea_seeds",
        label="pea seeds",
        phrase="a paper twist of pea seeds",
        plural_name="pea seeds",
        spill_word="seed",
        landing="into the row",
        can_plant=True,
        tags={"seed", "sprout"},
    ),
    "bean_seeds": LobThing(
        id="bean_seeds",
        label="bean seeds",
        phrase="a little cloth pouch of bean seeds",
        plural_name="bean seeds",
        spill_word="bean",
        landing="into the row",
        can_plant=True,
        tags={"seed", "sprout"},
    ),
    "flower_bulbs": LobThing(
        id="flower_bulbs",
        label="flower bulbs",
        phrase="a small bundle of flower bulbs",
        plural_name="flower bulbs",
        spill_word="bulb",
        landing="into the bed",
        can_plant=True,
        tags={"bulb", "sprout", "flower"},
    ),
}

HOLDERS = {
    "basket": Holder(
        id="basket",
        label="basket",
        phrase="the willow basket",
        held_on="with both hands in front",
        open_top=True,
        soft=False,
        tags={"basket"},
    ),
    "apron": Holder(
        id="apron",
        label="apron",
        phrase="the blue apron like a little pouch",
        held_on="by its corners",
        open_top=True,
        soft=True,
        tags={"apron"},
    ),
    "bowl": Holder(
        id="bowl",
        label="bowl",
        phrase="the round red bowl",
        held_on="under the falling seeds",
        open_top=True,
        soft=False,
        tags={"bowl"},
    ),
}

MISUNDERSTANDINGS = {
    "hold_gate": Misunderstanding(
        id="hold_gate",
        heard_as="hold the gate",
        held_instead="hold the gate latch",
        reason="because the breeze made the little gate click and shake",
        needs_open_holder=True,
        tags={"mishear"},
    ),
    "hold_hat": Misunderstanding(
        id="hold_hat",
        heard_as="hold your hat",
        held_instead="grab hold of a hat against the wind",
        reason="because the wind came skipping by at the very same moment",
        needs_open_holder=True,
        tags={"mishear"},
    ),
    "hold_corners": Misunderstanding(
        id="hold_corners",
        heard_as="hold the corners",
        held_instead="pinch the apron corners but forget to make a pocket",
        reason="because soft cloth can flop unless someone says exactly how",
        needs_open_holder=True,
        tags={"mishear", "cloth"},
    ),
}


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    thing: str
    holder: str
    misunderstanding: str
    lobber_name: str
    lobber_gender: str
    holder_name: str
    holder_gender: str
    seed: Optional[int] = None


# Curated set used by --all and verify smoke tests.
CURATED = [
    StoryParams(
        place="garden",
        thing="pea_seeds",
        holder="basket",
        misunderstanding="hold_gate",
        lobber_name="Mira",
        lobber_gender="girl",
        holder_name="Pip",
        holder_gender="boy",
    ),
    StoryParams(
        place="yard",
        thing="bean_seeds",
        holder="bowl",
        misunderstanding="hold_hat",
        lobber_name="Nell",
        lobber_gender="girl",
        holder_name="Tob",
        holder_gender="boy",
    ),
    StoryParams(
        place="meadow_edge",
        thing="flower_bulbs",
        holder="apron",
        misunderstanding="hold_corners",
        lobber_name="Wren",
        lobber_gender="girl",
        holder_name="May",
        holder_gender="girl",
    ),
]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "seed": [(
        "What does a seed do in the ground?",
        "A seed can sleep in the soil until it gets water, warmth, and time. Then it can sprout and grow into a plant."
    )],
    "bulb": [(
        "What is a flower bulb?",
        "A flower bulb is a rounded plant part that stores food for a future flower. When it is planted, it can grow roots, leaves, and then a bloom."
    )],
    "sprout": [(
        "What does generate mean in a garden story?",
        "Here generate means to help bring something into being. Sun, rain, and care can generate tiny green sprouts from seeds or bulbs."
    )],
    "basket": [(
        "Why is a basket useful for carrying little things?",
        "A basket has open space and sides that help keep small things together. That makes it easier to catch or carry them."
    )],
    "bowl": [(
        "Why is a bowl good for catching seeds?",
        "A bowl is round and open at the top, so small things can drop into it instead of scattering away."
    )],
    "apron": [(
        "How can an apron hold things?",
        "If someone lifts an apron into a pocket shape, it can hold light things for a little while. If the cloth hangs flat, the things may tumble out."
    )],
    "mishear": [(
        "What is a misunderstanding?",
        "A misunderstanding happens when people do not mean the same thing or hear the same words. It can make a problem even when both people are trying to help."
    )],
    "friendship": [(
        "How can friends fix a misunderstanding?",
        "Friends can stop, speak plainly, and listen to each other. Clear words help each person understand what the other meant."
    )],
}
KNOWLEDGE_ORDER = ["seed", "bulb", "sprout", "basket", "bowl", "apron", "mishear", "friendship"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["lobber"]
    b = f["holder_friend"]
    thing = f["thing"]
    holder = f["holder"]
    return [
        f'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the words "lob", "hold", and "generate".',
        f"Tell a sing-song story where {a.id} asks {b.id} to hold {holder.phrase}, but a misunderstanding makes a gentle lob go wrong before the friends make up.",
        f"Write a short friendship story in a rhyming nursery style where spilled {thing.plural_name} lead to clearer words, teamwork, and a garden ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["lobber"]
    b = f["holder_friend"]
    thing = f["thing"]
    holder = f["holder"]
    misunderstanding = f["misunderstanding"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {a.id} and {b.id}, working together in {place.label}. They begin with a happy plan, then have to mend a small misunderstanding."
        ),
        (
            f"What did {a.id} want {b.id} to do?",
            f"{a.id} wanted {b.id} to hold {holder.phrase} so a gentle lob of {thing.plural_name} could land neatly inside. The plan was meant to help them share the planting work."
        ),
        (
            "What caused the problem?",
            f"The problem started because {b.id} misheard the words and thought {misunderstanding.heard_as}. Both friends were trying to help, but they were not imagining the same action."
        ),
    ]
    if f["spilled"]:
        qa.append((
            "What happened when the seeds or bulbs were lobbed?",
            f"They spilled onto the ground instead of landing in {holder.phrase}. That happened because the right thing was not being held in the right way."
        ))
    if f["mended"]:
        qa.append((
            "How did the friends fix the misunderstanding?",
            f"They stopped and explained exactly what each one had meant. Plain talk untangled the mix-up, and then they gathered the scattered {thing.plural_name} together."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the friends planting the {thing.plural_name} side by side and feeling close again. The last image shows warm sun and rain that would generate little sprouts, proving their teamwork turned the muddle into something growing."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"friendship", "mishear"} | set(f["thing"].tags) | set(f["holder"].tags)
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


# ---------------------------------------------------------------------------
# Trace and rejection explanations
# ---------------------------------------------------------------------------
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.open_top:
            bits.append("open_top=True")
        if ent.soft:
            bits.append("soft=True")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(thing: LobThing, holder: Holder, misunderstanding: Misunderstanding) -> str:
    if not holder_fits(thing, holder):
        return (
            f"(No story: {holder.phrase} is not a reasonable thing to catch {thing.plural_name} in. "
            f"Pick an open holder like a basket, bowl, or apron-pocket.)"
        )
    if not misunderstanding_fits(holder, misunderstanding):
        return (
            f"(No story: the misunderstanding '{misunderstanding.heard_as}' does not fit {holder.phrase}. "
            f"That mix-up only makes sense with a holder that can be held the described way.)"
        )
    return "(No story: this combination does not make a reasonable misunderstanding.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Reasonable catching setup.
fits(T, H) :- plantable(T), open_holder(H).
misfit_ok(H, M) :- misunderstanding(M), not requires_soft(M), open_holder(H).
misfit_ok(H, M) :- misunderstanding(M), requires_soft(M), soft_holder(H), open_holder(H).

valid(P, T, H, M) :- place(P), thing(T), holder(H), misunderstanding(M), fits(T, H), misfit_ok(H, M).

% Outcome is simple in this world: if the combo is valid, the misunderstanding causes
% a spill, and clear talk mends the friendship.
spill(P, T, H, M) :- valid(P, T, H, M).
mended(P, T, H, M) :- valid(P, T, H, M).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid, thing in THINGS.items():
        lines.append(asp.fact("thing", tid))
        if thing.can_plant:
            lines.append(asp.fact("plantable", tid))
    for hid, holder in HOLDERS.items():
        lines.append(asp.fact("holder", hid))
        if holder.open_top:
            lines.append(asp.fact("open_holder", hid))
        if holder.soft:
            lines.append(asp.fact("soft_holder", hid))
    for mid, mis in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("misunderstanding", mid))
        if mis.id == "hold_corners":
            lines.append(asp.fact("requires_soft", mid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    # Smoke test ordinary generation.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        print("OK: smoke-tested generate() on a curated sample.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    # A few seeded random scenarios.
    parser = build_parser()
    for seed in [0, 1, 7, 11]:
        try:
            params = resolve_params(parser.parse_args(["--seed", str(seed)]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
        except Exception as err:  # pragma: no cover - verify path only
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random generation smoke tests passed.")
    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme friendship storyworld: a gentle lob, a muddled 'hold', and clear words that generate new growth."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--holder", choices=HOLDERS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--lobber-name")
    ap.add_argument("--lobber-gender", choices=["girl", "boy"])
    ap.add_argument("--holder-name")
    ap.add_argument("--holder-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


GIRL_NAMES = ["Mira", "Nell", "May", "Dot", "Wren", "Ivy", "Tess", "Rose"]
BOY_NAMES = ["Pip", "Tob", "Ben", "Kit", "Ned", "Sam", "Lew", "Oli"]


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.thing and args.holder:
        thing = THINGS[args.thing]
        holder = HOLDERS[args.holder]
        mis = MISUNDERSTANDINGS[args.misunderstanding] if args.misunderstanding else next(iter(MISUNDERSTANDINGS.values()))
        if not holder_fits(thing, holder) or not misunderstanding_fits(holder, mis):
            raise StoryError(explain_rejection(thing, holder, mis))
    if args.holder and args.misunderstanding:
        holder = HOLDERS[args.holder]
        mis = MISUNDERSTANDINGS[args.misunderstanding]
        if not misunderstanding_fits(holder, mis):
            thing = THINGS[args.thing] if args.thing else next(iter(THINGS.values()))
            raise StoryError(explain_rejection(thing, holder, mis))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.thing is None or combo[1] == args.thing)
        and (args.holder is None or combo[2] == args.holder)
        and (args.misunderstanding is None or combo[3] == args.misunderstanding)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, thing, holder, misunderstanding = rng.choice(sorted(combos))
    lobber_gender = args.lobber_gender or rng.choice(["girl", "boy"])
    holder_gender = args.holder_gender or rng.choice(["girl", "boy"])
    lobber_name = args.lobber_name or _pick_name(rng, lobber_gender)
    holder_name = args.holder_name or _pick_name(rng, holder_gender, avoid=lobber_name)

    return StoryParams(
        place=place,
        thing=thing,
        holder=holder,
        misunderstanding=misunderstanding,
        lobber_name=lobber_name,
        lobber_gender=lobber_gender,
        holder_name=holder_name,
        holder_gender=holder_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.thing not in THINGS:
        raise StoryError(f"(Invalid thing: {params.thing})")
    if params.holder not in HOLDERS:
        raise StoryError(f"(Invalid holder: {params.holder})")
    if params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError(f"(Invalid misunderstanding: {params.misunderstanding})")

    thing = THINGS[params.thing]
    holder = HOLDERS[params.holder]
    misunderstanding = MISUNDERSTANDINGS[params.misunderstanding]
    if not holder_fits(thing, holder) or not misunderstanding_fits(holder, misunderstanding):
        raise StoryError(explain_rejection(thing, holder, misunderstanding))

    world = tell(
        place=PLACES[params.place],
        thing=thing,
        holder=holder,
        misunderstanding=misunderstanding,
        lobber_name=params.lobber_name,
        lobber_gender=params.lobber_gender,
        holder_name=params.holder_name,
        holder_gender=params.holder_gender,
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, thing, holder, misunderstanding) combos:\n")
        for place, thing, holder, misunderstanding in combos:
            print(f"  {place:12} {thing:14} {holder:8} {misunderstanding}")
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
                f"### {p.lobber_name} and {p.holder_name}: "
                f"{p.thing} with {p.holder} in {p.place} ({p.misunderstanding})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
