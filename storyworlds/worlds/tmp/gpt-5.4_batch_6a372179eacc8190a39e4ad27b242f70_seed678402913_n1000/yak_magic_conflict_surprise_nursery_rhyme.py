#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/yak_magic_conflict_surprise_nursery_rhyme.py
=======================================================================

A tiny storyworld about a gentle yak in a nursery-rhyme landscape. Each story
has a bit of magic, a small conflict, and a surprise ending.

The seed shape rebuilt here is:

    yak + magic + conflict + surprise + nursery-rhyme style

This world models one little problem clearly instead of covering many weak
ones. A yak prepares to perform a rhyme-song in a pretty place. A troublemaker
causes a concrete snag. The yak uses a magic charm in a reasonable way, and the
conflict ends either in sharing or in a repaired apology. The ending image
shows the surprise that the magic leaves behind.

Run it
------
    python storyworlds/worlds/gpt-5.4/yak_magic_conflict_surprise_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/yak_magic_conflict_surprise_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/yak_magic_conflict_surprise_nursery_rhyme.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/yak_magic_conflict_surprise_nursery_rhyme.py --qa
    python storyworlds/worlds/gpt-5.4/yak_magic_conflict_surprise_nursery_rhyme.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/yak_magic_conflict_surprise_nursery_rhyme.py --verify
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

# Make storyworlds/results.py importable when this file is run directly from the
# repo root. This script lives in storyworlds/worlds/gpt-5.4/, so the package
# dir is three levels up.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Shared entity representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"                 # "character" | "thing"
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
        female = {"girl", "mother", "woman", "hen"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


# ---------------------------------------------------------------------------
# Domain configuration.
# ---------------------------------------------------------------------------
@dataclass
class Place:
    id: str
    label: str
    phrase: str
    floor: str
    sky: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    magic: str
    power: str                 # "glow" | "calm" | "untangle"
    song_line: str
    surprise: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    label: str
    phrase: str
    action: str
    problem: str               # "dark" | "noise" | "tangle"
    need: str                  # matching charm power needed
    feeling: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    image: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Per-world params.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    charm: str
    trouble: str
    treat: str
    yak_name: str
    mood: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World state + narration.
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


# ---------------------------------------------------------------------------
# Causal rules.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    yak = world.get("yak")
    trickster = world.get("troublemaker")
    if trickster.meters["blocked_song"] >= THRESHOLD and ("conflict",) not in world.fired:
        world.fired.add(("conflict",))
        yak.memes["worry"] += 1
        trickster.memes["grumpiness"] += 1
        out.append("__conflict__")
    return out


def _r_magic_help(world: World) -> list[str]:
    out: list[str] = []
    yak = world.get("yak")
    charm = world.get("charm")
    trickster = world.get("troublemaker")
    if yak.meters["sang"] >= THRESHOLD and charm.meters["glowing"] >= THRESHOLD:
        sig = ("magic_help", world.facts.get("needed_power"))
        if sig not in world.fired:
            world.fired.add(sig)
            need = world.facts.get("needed_power")
            if charm.attrs.get("power") == need:
                trickster.meters["blocked_song"] = 0.0
                trickster.memes["grumpiness"] = 0.0
                trickster.memes["softened"] += 1
                yak.memes["hope"] += 1
                yak.memes["kindness"] += 1
                out.append("__resolved__")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    yak = world.get("yak")
    treat = world.get("treat")
    if yak.memes["hope"] >= THRESHOLD and ("surprise",) not in world.fired:
        world.fired.add(("surprise",))
        treat.meters["appeared"] += 1
        yak.memes["delight"] += 1
        out.append("__surprise__")
    return out


CAUSAL_RULES = [
    Rule(name="conflict", tag="social", apply=_r_conflict),
    Rule(name="magic_help", tag="magic", apply=_r_magic_help),
    Rule(name="surprise", tag="magic", apply=_r_surprise),
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
                produced.extend(sents)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness gate and outcome model.
# ---------------------------------------------------------------------------
def compatible(charm: Charm, trouble: Trouble) -> bool:
    return charm.power == trouble.need


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for charm_id, charm in CHARMS.items():
            for trouble_id, trouble in TROUBLES.items():
                if not compatible(charm, trouble):
                    continue
                for treat_id in TREATS:
                    combos.append((place_id, charm_id, trouble_id, treat_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    charm = CHARMS[params.charm]
    trouble = TROUBLES[params.trouble]
    return "mended" if compatible(charm, trouble) else "stuck"


def explain_rejection(charm: Charm, trouble: Trouble) -> str:
    return (
        f"(No story: {charm.label} works by {charm.power}, but {trouble.label} "
        f"needs magic that can {trouble.need}. Pick a matching charm so the "
        f"yak can solve the conflict honestly.)"
    )


# ---------------------------------------------------------------------------
# Prediction.
# ---------------------------------------------------------------------------
def predict_fix(world: World) -> dict:
    sim = world.copy()
    yak = sim.get("yak")
    charm = sim.get("charm")
    yak.meters["sang"] += 1
    charm.meters["glowing"] += 1
    propagate(sim, narrate=False)
    trickster = sim.get("troublemaker")
    treat = sim.get("treat")
    return {
        "resolved": trickster.meters["blocked_song"] < THRESHOLD,
        "surprise": treat.meters["appeared"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Screenplay verbs.
# ---------------------------------------------------------------------------
def opening(world: World, place: Place, yak: Entity, mood: str) -> None:
    yak.memes["content"] += 1
    world.say(
        f"In {place.phrase}, where {place.floor} and {place.sky}, "
        f"lived {yak.id} the yak, so {mood} and so slack."
    )
    world.say(
        f"{yak.id} liked to sway and hum a small evening rhyme, "
        f"soft as a cradle and sweet as a chime."
    )


def show_charm(world: World, yak: Entity, charm: Charm) -> None:
    world.say(
        f"Round {yak.pronoun('possessive')} neck hung {charm.phrase}, "
        f"and everyone said it held {charm.magic}."
    )
    world.say(charm.song_line)


def bring_trouble(world: World, trouble: Trouble) -> None:
    trickster = world.get("troublemaker")
    trickster.meters["blocked_song"] += 1
    world.facts["needed_power"] = trouble.need
    propagate(world, narrate=False)
    world.say(
        f"But in popped {trouble.phrase}, and {trouble.action}. "
        f"The neat little rhyme could not come out right."
    )


def lament(world: World, yak: Entity, trouble: Trouble) -> None:
    world.say(
        f'"Oh dear," sighed {yak.id}, "{trouble.feeling} has stepped in my track. '
        f'My song has gone crooked. How shall I get it back?"'
    )


def use_magic(world: World, yak: Entity, charm: Entity, charm_cfg: Charm) -> None:
    yak.meters["sang"] += 1
    charm.meters["glowing"] += 1
    world.say(
        f"So {yak.id} stamped once, not in anger but time, "
        f"and sang to the charm in a bobbling rhyme."
    )
    world.say(charm_cfg.song_line)
    markers = propagate(world, narrate=False)
    if "__resolved__" not in markers:
        raise StoryError("Magic failed to solve the conflict; this parameter set is unreasonable.")


def mend(world: World, yak: Entity, troublemaker: Entity, trouble: Trouble) -> None:
    world.say(
        f"At once the air softened around {troublemaker.label_word}, "
        f"and the snag in the song came loose in a twirl."
    )
    if trouble.id == "magpie":
        world.say(
            f'The magpie blinked twice and said, "I liked the bright gleam. '
            f'I should have asked first instead of spoiling your dream."'
        )
    elif trouble.id == "wind_sprite":
        world.say(
            f'The wind sprite grew gentle and whispered, "I only meant play. '
            f'I did not mean to puff your best verses away."'
        )
    else:
        world.say(
            f'The puddle troll rubbed {troublemaker.pronoun("possessive")} eyes and said, '
            f'"I wanted a turn. I should not have splashed through your line."'
        )
    troublemaker.memes["apology"] += 1
    yak.memes["forgiveness"] += 1
    world.say(
        f"{yak.id} did not scold. {yak.pronoun().capitalize()} scooted aside and made room, "
        f"for kind words can mend what cross feet consume."
    )


def surprise(world: World, charm_cfg: Charm, treat: Treat) -> None:
    markers = propagate(world, narrate=False)
    if "__surprise__" not in markers:
        raise StoryError("The story reached no surprise ending.")
    world.say(
        f"Then came the surprise that no one could lack: {charm_cfg.surprise}."
    )
    world.say(
        f"There on the ground appeared {treat.phrase}, {treat.image}."
    )


def closing(world: World, place: Place, yak: Entity, treat: Treat) -> None:
    world.say(
        f"So {yak.id} sang clearly in {place.label}, and even the troublemaker stayed. "
        f"They shared {treat.label} together and ended the day."
    )
    world.say(
        f"And if you pass by where {place.floor}, you may hear that same yak say: "
        f'"Soft song, kind heart, bright end to the day."'
    )


# ---------------------------------------------------------------------------
# Story assembly.
# ---------------------------------------------------------------------------
def tell(place: Place, charm_cfg: Charm, trouble: Trouble, treat: Treat,
         yak_name: str, mood: str) -> World:
    world = World()
    yak = world.add(Entity(
        id=yak_name,
        kind="character",
        type="yak",
        label="yak",
        role="hero",
        traits=[mood, "gentle"],
        tags={"yak"},
    ))
    charm = world.add(Entity(
        id="charm",
        kind="thing",
        type="charm",
        label=charm_cfg.label,
        phrase=charm_cfg.phrase,
        attrs={"power": charm_cfg.power},
        tags=set(charm_cfg.tags),
    ))
    troublemaker_type = {
        "magpie": "bird",
        "wind_sprite": "sprite",
        "puddle_troll": "troll",
    }[trouble.id]
    troublemaker = world.add(Entity(
        id="troublemaker",
        kind="character",
        type=troublemaker_type,
        label=trouble.label,
        role="troublemaker",
        tags=set(trouble.tags),
    ))
    treat_ent = world.add(Entity(
        id="treat",
        kind="thing",
        type="treat",
        label=treat.label,
        phrase=treat.phrase,
        tags=set(treat.tags),
    ))

    opening(world, place, yak, mood)
    show_charm(world, yak, charm_cfg)

    world.para()
    bring_trouble(world, trouble)
    lament(world, yak, trouble)

    pred = predict_fix(world)
    world.facts["predicted_resolved"] = pred["resolved"]
    world.facts["predicted_surprise"] = pred["surprise"]
    if not pred["resolved"]:
        raise StoryError(explain_rejection(charm_cfg, trouble))

    world.para()
    use_magic(world, yak, charm, charm_cfg)
    mend(world, yak, troublemaker, trouble)
    surprise(world, charm_cfg, treat)
    closing(world, place, yak, treat)

    world.facts.update(
        place=place,
        charm_cfg=charm_cfg,
        trouble_cfg=trouble,
        treat_cfg=treat,
        yak=yak,
        troublemaker=troublemaker,
        charm=charm,
        treat=treat_ent,
        outcome="mended",
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
PLACES = {
    "clover_hill": Place(
        id="clover_hill",
        label="the clover hill",
        phrase="a clover hill by a silver fence",
        floor="the clover nodded in round green rings",
        sky="the sky wore a blue shawl fit for kings",
        tags={"meadow"},
    ),
    "moon_pond": Place(
        id="moon_pond",
        label="the moon pond",
        phrase="a moon pond tucked by whispering reeds",
        floor="the reeds bent low in feathery rows",
        sky="the sky held a pearl where the first star glows",
        tags={"pond"},
    ),
    "thistle_lane": Place(
        id="thistle_lane",
        label="thistle lane",
        phrase="thistle lane by the old stone gate",
        floor="the thistles rocked on purple toes",
        sky="the sky stretched pink where sunset rose",
        tags={"lane"},
    ),
}

CHARMS = {
    "moonbell": Charm(
        id="moonbell",
        label="moon bell",
        phrase="a moon bell of milk-white tin",
        magic="glow-magic that could light dark corners",
        power="glow",
        song_line='"Ding little moonbell, silver and slow, show the shy places where soft singers go."',
        surprise="tiny moon-moths fluttered up and stitched pale light along the grass",
        tags={"magic", "bell", "light"},
    ),
    "hush_drum": Charm(
        id="hush_drum",
        label="hush drum",
        phrase="a hush drum no bigger than a teacup lid",
        magic="calm-magic that could settle noisy hearts",
        power="calm",
        song_line='"Hum little hush drum, round as the noon, smooth all the bumping and quiet the tune."',
        surprise="sleepy stars drifted down and bobbed like lantern seeds over the path",
        tags={"magic", "music", "calm"},
    ),
    "knot_ribbon": Charm(
        id="knot_ribbon",
        label="knot ribbon",
        phrase="a knot ribbon braided with gold thread",
        magic="untangling magic for twists and snags",
        power="untangle",
        song_line='"Twine little ribbon, loop and unlace, loosen each muddle and tidy its place."',
        surprise="bright loops of ribbon danced by themselves and tied the daisies in bows",
        tags={"magic", "ribbon", "untangle"},
    ),
}

TROUBLES = {
    "magpie": Trouble(
        id="magpie",
        label="magpie",
        phrase="a magpie with a quick black eye",
        action="snatched the gleaming beat-stick and hid it under a fern",
        problem="missing_item",
        need="untangle",
        feeling="a muddle of grabbing wings",
        tags={"bird", "sharing"},
    ),
    "wind_sprite": Trouble(
        id="wind_sprite",
        label="wind sprite",
        phrase="a wind sprite in a fluttering cap",
        action="blew the little lantern cloud away and left the path too dim",
        problem="dark",
        need="glow",
        feeling="a gusty patch of dark",
        tags={"wind", "light"},
    ),
    "puddle_troll": Trouble(
        id="puddle_troll",
        label="puddle troll",
        phrase="a puddle troll with drippy boots",
        action="thumped a spoon on a pan and made such a racket that no line could stay straight",
        problem="noise",
        need="calm",
        feeling="a clattery heap of noise",
        tags={"noise", "manners"},
    ),
}

TREATS = {
    "honey_buns": Treat(
        id="honey_buns",
        label="honey buns",
        phrase="a plate of honey buns",
        image="warm and shining, with steam in curly threads",
        tags={"food"},
    ),
    "plum_tarts": Treat(
        id="plum_tarts",
        label="plum tarts",
        phrase="three plum tarts",
        image="round as buttons and purple at the seams",
        tags={"food"},
    ),
    "clover_cakes": Treat(
        id="clover_cakes",
        label="clover cakes",
        phrase="a basket of clover cakes",
        image="small and green-flecked, smelling sweet as toast",
        tags={"food"},
    ),
}

YAK_NAMES = ["Yori", "Moss", "Tumble", "Nori", "Puff"]
MOODS = ["merry", "dreamy", "gentle", "drowsy", "jolly"]


# ---------------------------------------------------------------------------
# QA generation.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "yak": [
        (
            "What is a yak?",
            "A yak is a shaggy animal with long hair and strong legs. Yaks live in cold places and can carry heavy things.",
        )
    ],
    "magic": [
        (
            "What does magic mean in a story?",
            "Magic in a story is something wonderful that can happen in a way real life usually cannot. It often helps show feelings or solve a problem in a surprising way.",
        )
    ],
    "sharing": [
        (
            "Why is it better to ask before taking something shiny?",
            "You should ask first because the thing may belong to someone else. Asking is kind, and it helps everyone feel safe and respected.",
        )
    ],
    "light": [
        (
            "Why does a little light help in the dark?",
            "A little light helps your eyes see where things are. It can also make a place feel calmer and less scary.",
        )
    ],
    "noise": [
        (
            "Why can loud noise make singing hard?",
            "Loud noise can cover up the words and beat of a song. When things grow quiet, it is easier to hear and sing together.",
        )
    ],
    "manners": [
        (
            "What can you do after you spoil someone's game or song?",
            "You can stop, say sorry, and try to help fix the problem. A real apology means you want to make things better.",
        )
    ],
    "food": [
        (
            "Why do treats feel special at the end of a story?",
            "A shared treat can show that everyone feels safe and friendly again. It is a cozy way to prove the problem is over.",
        )
    ],
    "ribbon": [
        (
            "What is a ribbon?",
            "A ribbon is a long strip of cloth used for tying or decorating things. It bends easily and can make loops and bows.",
        )
    ],
    "bell": [
        (
            "What does a bell do?",
            "A bell makes a clear ringing sound when it is moved or tapped. In stories, bells often call attention or seem magical.",
        )
    ],
    "calm": [
        (
            "What does calm mean?",
            "Calm means quiet, settled, and not wild or upset. A calm voice or beat can help everyone think more clearly.",
        )
    ],
}
KNOWLEDGE_ORDER = ["yak", "magic", "sharing", "light", "noise", "manners", "food", "ribbon", "bell", "calm"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    yak = f["yak"]
    trouble = f["trouble_cfg"]
    charm = f["charm_cfg"]
    place = f["place"]
    return [
        f'Write a short nursery-rhyme style story for a small child about a yak with magic. Include the word "{yak.label_word}".',
        f"Tell a gentle story set in {place.label} where a {trouble.label} causes trouble, but a magical {charm.label} helps mend it.",
        "Write a rhyming story with a conflict, a kind solution, and a surprise ending that shows what changed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    yak = f["yak"]
    trouble = f["trouble_cfg"]
    charm = f["charm_cfg"]
    place = f["place"]
    treat = f["treat_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {yak.id} the yak. {yak.id} wanted to sing a soft rhyme in {place.label}.",
        ),
        (
            "What magical thing did the yak have?",
            f"{yak.id} had {charm.phrase}. It was magical because it could {charm.power} when the yak sang to it.",
        ),
        (
            "What was the problem in the story?",
            f"The problem was that {trouble.label} {trouble.action}. That blocked the yak's song and made the moment feel wrong.",
        ),
        (
            "How did the yak solve the conflict?",
            f"{yak.id} used the magic in the {charm.label} by singing a careful rhyme to it. The charm matched the trouble, so it softened the problem instead of making the fight bigger.",
        ),
        (
            "How did the troublemaker change?",
            f"The troublemaker stopped causing trouble and apologized. The yak answered with kindness, which helped turn the conflict into sharing instead of more fuss.",
        ),
        (
            "What was the surprise at the end?",
            f"After the conflict was mended, {charm.surprise}. Then {treat.phrase} appeared, which showed the magic had turned the ending cozy and bright.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"yak", "magic"} | set(f["trouble_cfg"].tags) | set(f["treat_cfg"].tags) | set(f["charm_cfg"].tags)
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


# ---------------------------------------------------------------------------
# Trace.
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set.
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="clover_hill",
        charm="moonbell",
        trouble="wind_sprite",
        treat="clover_cakes",
        yak_name="Yori",
        mood="merry",
    ),
    StoryParams(
        place="moon_pond",
        charm="hush_drum",
        trouble="puddle_troll",
        treat="plum_tarts",
        yak_name="Moss",
        mood="dreamy",
    ),
    StoryParams(
        place="thistle_lane",
        charm="knot_ribbon",
        trouble="magpie",
        treat="honey_buns",
        yak_name="Tumble",
        mood="jolly",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
compatible(C, T) :- charm(C), trouble(T), power(C, P), need(T, P).
valid(P, C, T, Tr) :- place(P), compatible(C, T), treat(Tr).

outcome(mended) :- compatible_chosen.
compatible_chosen :- chosen_charm(C), chosen_trouble(T), compatible(C, T).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid, charm in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        lines.append(asp.fact("power", cid, charm.power))
    for tid, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("need", tid, trouble.need))
    for rid in TREATS:
        lines.append(asp.fact("treat", rid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_charm", params.charm),
        asp.fact("chosen_trouble", params.trouble),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    cases = list(CURATED)
    for seed in range(25):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = []
    for params in cases:
        py = outcome_of(params)
        asp_o = asp_outcome(params)
        if py != asp_o:
            bad.append((params, py, asp_o))
    if not bad:
        print(f"OK: ASP outcome matches Python outcome on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)} outcome disagreements.")
        for params, py, asp_o in bad[:5]:
            print(" ", params, py, asp_o)

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test produced empty story.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny nursery-rhyme storyworld about a magical yak, a small conflict, and a surprise."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--charm", choices=sorted(CHARMS))
    ap.add_argument("--trouble", choices=sorted(TROUBLES))
    ap.add_argument("--treat", choices=sorted(TREATS))
    ap.add_argument("--yak-name")
    ap.add_argument("--mood", choices=sorted(MOODS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.charm and args.trouble:
        if not compatible(CHARMS[args.charm], TROUBLES[args.trouble]):
            raise StoryError(explain_rejection(CHARMS[args.charm], TROUBLES[args.trouble]))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.charm is None or combo[1] == args.charm)
        and (args.trouble is None or combo[2] == args.trouble)
        and (args.treat is None or combo[3] == args.treat)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, charm_id, trouble_id, treat_id = rng.choice(sorted(combos))
    yak_name = args.yak_name or rng.choice(YAK_NAMES)
    mood = args.mood or rng.choice(MOODS)
    return StoryParams(
        place=place_id,
        charm=charm_id,
        trouble=trouble_id,
        treat=treat_id,
        yak_name=yak_name,
        mood=mood,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.charm not in CHARMS:
        raise StoryError(f"Unknown charm: {params.charm}")
    if params.trouble not in TROUBLES:
        raise StoryError(f"Unknown trouble: {params.trouble}")
    if params.treat not in TREATS:
        raise StoryError(f"Unknown treat: {params.treat}")

    place = PLACES[params.place]
    charm = CHARMS[params.charm]
    trouble = TROUBLES[params.trouble]
    treat = TREATS[params.treat]

    if not compatible(charm, trouble):
        raise StoryError(explain_rejection(charm, trouble))

    world = tell(place, charm, trouble, treat, params.yak_name, params.mood)
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, charm, trouble, treat) combos:\n")
        for place, charm, trouble, treat in combos:
            print(f"  {place:12} {charm:12} {trouble:12} {treat}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.yak_name}: {p.charm} vs {p.trouble} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
