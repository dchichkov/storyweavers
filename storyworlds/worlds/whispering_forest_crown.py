#!/usr/bin/env python3
"""
storyworlds/worlds/whispering_forest_crown.py
=============================================

Seed prompt
-----------
Write a story that includes the following words and narrative instruments.
Words: crown, whispering forest, tiptoe
Features: Surprise, Flashback, Curiosity
Style: Whodunit

Source tale written from the seed
---------------------------------
Milo and Tessa carried a paper crown to the whispering forest for the birthday
queen game. They hung it on a low branch while they made a leaf throne. When
they came back, the crown was gone, and the forest seemed to hush.

Milo grew curious instead of cross. He remembered a flashback from last autumn:
the same hollow stump had echoed secrets only when someone tiptoed past it. So
he tiptoed beside the moss and listened. "Soft steps to the fern pocket," the
forest whispered.

The clue matched a trail of bent fern tips, and the crown was inside a bark
basket. Tessa admitted she had moved it there to keep it safe from the wind and
then forgotten because the game began. The surprise was not a thief at all. They
set the crown on the leaf throne, and the forest whispered like clapping.

This world models that story domain. Flashback memories only become useful when
the forest, clue, mover, and hiding place are compatible. The generated mystery
is refused when the clue could not physically or causally lead to the crown.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


def display(ent: Entity) -> str:
    return ent.label or ent.id


def sentence_display(ent: Entity) -> str:
    text = display(ent)
    return text[:1].upper() + text[1:]


@dataclass
class Forest:
    id: str
    label: str
    opening: str
    paths: set[str]
    memory_place: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Crown:
    id: str
    label: str
    phrase: str
    size: int
    danger: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mover:
    id: str
    name: str
    gender: str
    relation: str
    motive: str
    route: set[str]
    can_carry: set[int]
    tags: set[str] = field(default_factory=set)


@dataclass
class Cache:
    id: str
    label: str
    phrase: str
    path: str
    capacity: int
    mark: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MemoryClue:
    id: str
    mark: str
    whisper: str
    flashback: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, forest: Forest) -> None:
        self.forest = forest
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.forest)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_loss_wakes_curiosity(world: World) -> list[str]:
    crown = world.entities.get("crown")
    hero = world.entities.get("hero")
    if not crown or not hero or crown.meters["missing"] < THRESHOLD:
        return []
    sig = ("curiosity", crown.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["curiosity"] += 1
    hero.memes["worry"] += 1
    return []


def _r_flashback_unlocks_forest(world: World) -> list[str]:
    hero = world.entities.get("hero")
    forest = world.entities.get("forest")
    if not hero or not forest or hero.memes["flashback"] < THRESHOLD:
        return []
    sig = ("flashback", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    forest.meters["listening"] += 1
    hero.memes["patience"] += 1
    return []


def _r_tiptoe_hears_clue(world: World) -> list[str]:
    hero = world.entities.get("hero")
    forest = world.entities.get("forest")
    if not hero or not forest:
        return []
    if forest.meters["listening"] < THRESHOLD or hero.meters["tiptoe"] < THRESHOLD:
        return []
    sig = ("forest_whisper", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    forest.meters["whispered"] += 1
    hero.memes["hope"] += 1
    return []


def _r_mark_becomes_evidence(world: World) -> list[str]:
    cache = world.entities.get("cache")
    clue = world.entities.get("clue")
    mover = world.entities.get("mover")
    if not cache or not clue or not mover:
        return []
    if cache.meters["checked"] < THRESHOLD:
        return []
    if cache.attrs.get("mark") != clue.attrs.get("mark"):
        return []
    if cache.attrs.get("path") not in mover.attrs.get("route", set()):
        return []
    sig = ("evidence", cache.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cache.meters["evidence"] += 1
    mover.memes["ready_to_tell"] += 1
    return []


def _r_crown_found(world: World) -> list[str]:
    crown = world.entities.get("crown")
    cache = world.entities.get("cache")
    if not crown or not cache or cache.meters["evidence"] < THRESHOLD:
        return []
    sig = ("found", crown.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crown.meters["missing"] = 0.0
    crown.meters["found"] += 1
    return []


RULES = [
    Rule("loss_curiosity", _r_loss_wakes_curiosity),
    Rule("flashback", _r_flashback_unlocks_forest),
    Rule("tiptoe_clue", _r_tiptoe_hears_clue),
    Rule("evidence", _r_mark_becomes_evidence),
    Rule("found", _r_crown_found),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) != before:
                changed = True


def clue_is_sound(forest: Forest, crown: Crown, mover: Mover,
                  cache: Cache, clue: MemoryClue) -> bool:
    return (
        cache.path in forest.paths
        and cache.path in mover.route
        and crown.size <= cache.capacity
        and crown.size in mover.can_carry
        and cache.mark == clue.mark
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    out: list[tuple[str, str, str, str, str]] = []
    for fid, forest in FORESTS.items():
        for cid, crown in CROWNS.items():
            for mid, mover in MOVERS.items():
                for cache_id, cache in CACHES.items():
                    for clue_id, clue in CLUES.items():
                        if clue_is_sound(forest, crown, mover, cache, clue):
                            out.append((fid, cid, mid, cache_id, clue_id))
    return sorted(out)


def predict_search(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").memes["flashback"] += 1
    propagate(sim)
    sim.get("hero").meters["tiptoe"] += 1
    propagate(sim)
    sim.get("cache").meters["checked"] += 1
    propagate(sim)
    return {
        "heard": sim.get("forest").meters["whispered"] >= THRESHOLD,
        "evidence": sim.get("cache").meters["evidence"] >= THRESHOLD,
        "found": sim.get("crown").meters["found"] >= THRESHOLD,
    }


def begin(world: World, hero: Entity, mover: Entity, crown: Crown) -> None:
    world.say(
        f"{display(hero)} and {display(mover)} carried {crown.phrase} into "
        f"{world.forest.label} for a pretend royal game."
    )
    world.say(world.forest.opening)


def lose_crown(world: World, crown: Crown) -> None:
    ent = world.get("crown")
    ent.meters["missing"] += 1
    propagate(world)
    world.say(
        f"They hung the {crown.label} on a low branch while they made a leaf "
        f"throne. When they came back, the {crown.label} was gone, and the "
        f"whispering forest seemed to hold its breath."
    )


def remember(world: World, clue: MemoryClue) -> None:
    hero = world.get("hero")
    hero.memes["flashback"] += 1
    propagate(world)
    world.say(
        f"{display(hero)} felt curiosity rise higher than worry. {clue.flashback}"
    )


def tiptoe_and_listen(world: World, clue: MemoryClue) -> None:
    hero = world.get("hero")
    hero.meters["tiptoe"] += 1
    propagate(world)
    pred = predict_search(world)
    world.facts["prediction"] = pred
    world.say(
        f"So {display(hero)} began to tiptoe near {world.forest.memory_place}. "
        f'"{clue.whisper}," the forest whispered.'
    )
    if pred["evidence"]:
        world.say(
            f"{display(hero)} did not call it solved yet. A whisper was only useful "
            f"if the mark, the path, and the hiding place all agreed."
        )


def follow_mark(world: World, cache: Cache) -> None:
    hero = world.get("hero")
    world.get("cache").meters["checked"] += 1
    propagate(world)
    world.say(
        f"{display(hero)} followed the sign to {cache.phrase}. {cache.reveal}"
    )


def finish(world: World, mover: Mover, crown: Crown) -> None:
    hero = world.get("hero")
    crown_ent = world.get("crown")
    mover_ent = world.get("mover")
    if crown_ent.meters["found"] >= THRESHOLD:
        hero.memes["relief"] += 1
        mover_ent.memes["honesty"] += 1
        world.say(
            f"{sentence_display(mover_ent)} looked surprised, then told the truth. {mover.motive}"
        )
        world.say(
            f"The surprise was not a thief after all. They set the {crown.label} "
            f"on the leaf throne, and the whispering forest rustled like clapping."
        )


def tell(forest: Forest, crown: Crown, mover: Mover, cache: Cache,
         clue: MemoryClue, hero_name: str, hero_gender: str,
         guardian: str, trait: str) -> World:
    world = World(forest)
    hero = world.add(Entity("hero", "character", hero_gender, hero_name,
                            "detective", {"trait": trait}))
    mover_ent = world.add(Entity("mover", "character", mover.gender, mover.name,
                                 "mover", {"route": set(mover.route)}))
    world.add(Entity("guardian", "character", guardian, "the grown-up", "guardian"))
    world.add(Entity("forest", "place", "forest", forest.label))
    world.add(Entity("crown", "thing", "crown", crown.label, attrs={"size": crown.size}))
    world.add(Entity("cache", "thing", "cache", cache.label, attrs={
        "path": cache.path, "mark": cache.mark, "capacity": cache.capacity,
    }))
    world.add(Entity("clue", "thing", "clue", clue.id, attrs={"mark": clue.mark}))

    begin(world, hero, mover_ent, crown)
    lose_crown(world, crown)
    world.para()
    remember(world, clue)
    tiptoe_and_listen(world, clue)
    world.para()
    follow_mark(world, cache)
    finish(world, mover, crown)

    world.facts.update(
        hero=hero, mover=mover, mover_ent=mover_ent, forest=forest, crown=crown,
        cache=cache, clue=clue, guardian=world.get("guardian"),
        solved=world.get("crown").meters["found"] >= THRESHOLD,
    )
    return world


FORESTS = {
    "moss_glen": Forest(
        "moss_glen", "the whispering forest",
        "The moss glen was cool and green, and the leaves made tiny secret "
        "sounds whenever the wind changed.",
        {"fern_path", "stump_path", "brook_path"}, "the hollow stump",
        tags={"forest", "whisper"}),
    "pine_gate": Forest(
        "pine_gate", "the pine-gate woods",
        "Tall pines leaned together like doors, and every needle seemed to "
        "remember who had passed beneath.",
        {"needle_path", "stump_path", "fern_path"}, "the pine gate",
        tags={"forest", "whisper"}),
    "moon_fern": Forest(
        "moon_fern", "the moon-fern forest",
        "Pale ferns curled beside the path, shining just enough to make every "
        "small movement feel important.",
        {"fern_path", "root_path", "brook_path"}, "the fern arch",
        tags={"forest", "whisper"}),
}

CROWNS = {
    "paper_crown": Crown("paper_crown", "crown", "a paper crown", 1,
                         "a sharp wind could fold it", tags={"crown"}),
    "leaf_crown": Crown("leaf_crown", "crown", "a braided leaf crown", 1,
                        "the leaves could dry and crumble", tags={"crown", "leaf"}),
    "wooden_crown": Crown("wooden_crown", "crown", "a small wooden crown", 2,
                          "it was sturdy but too important to lose", tags={"crown"}),
}

MOVERS = {
    "tessa": Mover(
        "tessa", "Tessa", "girl", "friend",
        "She had moved it to keep it safe from the wind, then forgot when the "
        "game began.",
        {"fern_path", "stump_path"}, {1, 2}, tags={"friend"}),
    "milo": Mover(
        "milo", "Milo", "boy", "brother",
        "He had tucked it away for a surprise coronation, but the surprise "
        "became a worry when nobody could find it.",
        {"brook_path", "root_path", "stump_path"}, {1}, tags={"surprise"}),
    "keeper": Mover(
        "keeper", "the park keeper", "man", "helper",
        "He had rescued it from the muddy path and meant to bring it back after "
        "sweeping the leaves.",
        {"needle_path", "fern_path", "brook_path"}, {1, 2}, tags={"helper"}),
}

CACHES = {
    "fern_pocket": Cache(
        "fern_pocket", "fern pocket", "the pocket of curled ferns",
        "fern_path", 1, "bent_fern",
        "Behind the bent fern tips, the crown waited in a nest of soft leaves.",
        tags={"fern"}),
    "hollow_stump": Cache(
        "hollow_stump", "hollow stump", "the hollow stump",
        "stump_path", 2, "soft_echo",
        "Inside the stump, the crown rested where the wood smelled warm and dry.",
        tags={"stump"}),
    "root_basket": Cache(
        "root_basket", "root basket", "the woven basket under the roots",
        "root_path", 2, "root_scratch",
        "Under the crossed roots, the crown shone through strips of bark.",
        tags={"root"}),
    "brook_stone": Cache(
        "brook_stone", "brook stone", "the flat stone beside the brook",
        "brook_path", 1, "wet_moss",
        "Beside the wet moss, the crown sat safe from the rushing water.",
        tags={"brook"}),
}

CLUES = {
    "fern": MemoryClue(
        "fern", "bent_fern", "Soft steps to the fern pocket",
        "A flashback came back: last autumn, bent fern tips had shown where "
        "a lost mitten went.",
        tags={"fern", "flashback"}),
    "echo": MemoryClue(
        "echo", "soft_echo", "The hollow place repeats the secret",
        "A flashback came back: the hollow stump had echoed only after "
        "someone tiptoed past it.",
        tags={"stump", "flashback"}),
    "root": MemoryClue(
        "root", "root_scratch", "Follow the scratched root",
        "A flashback came back: a pale scratch on a root had pointed to a "
        "hidden acorn cup.",
        tags={"root", "flashback"}),
    "moss": MemoryClue(
        "moss", "wet_moss", "Where the moss is wet, look low",
        "A flashback came back: wet moss had kept the shape of small quiet "
        "steps.",
        tags={"brook", "flashback"}),
}

GIRL_NAMES = ["Nora", "Mia", "Tessa", "Lily", "Ava", "Rose"]
BOY_NAMES = ["Milo", "Leo", "Ben", "Sam", "Theo", "Finn"]
TRAITS = ["curious", "patient", "brave", "careful", "kind"]


@dataclass
class StoryParams:
    forest: str
    crown: str
    mover: str
    cache: str
    clue: str
    hero: str
    hero_gender: str
    guardian: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "forest": [("Why can a forest feel mysterious?",
                "A forest has many sounds, shadows, and paths. In a story, that "
                "can make every small clue feel important.")],
    "whisper": [("What does whispering mean?",
                 "Whispering means speaking very softly. People whisper when "
                 "they want only someone close by to hear.")],
    "crown": [("What is a crown used for in pretend play?",
               "A crown can show who is the queen, king, or leader in a game. "
               "It makes the pretend story feel special.")],
    "flashback": [("What is a flashback in a story?",
                   "A flashback is a memory of something that happened earlier. "
                   "It can help a character understand what is happening now.")],
    "fern": [("What is a fern?",
              "A fern is a leafy green plant. Its soft tips can bend when "
              "someone brushes past.")],
    "stump": [("What is a hollow stump?",
               "A hollow stump is the bottom part of an old tree with an open "
               "space inside. Small things can hide there.")],
    "brook": [("What is a brook?",
               "A brook is a little stream of water. The stones and moss near it "
               "can be wet and slippery.")],
}
KNOWLEDGE_ORDER = ["forest", "whisper", "crown", "flashback", "fern", "stump", "brook"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a curious whodunit for a young child using "crown", '
        f'"whispering forest", and "tiptoe".',
        f"Tell a surprise mystery where {display(f['hero'])} remembers a flashback and "
        f"uses it to find {f['crown'].phrase} in {f['forest'].label}.",
        f"Write a gentle story where a forest clue proves the crown was moved "
        f"for a reason, not stolen.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, crown, mover, cache, clue = f["hero"], f["crown"], f["mover"], f["cache"], f["clue"]
    qa = [
        ("Who is the story about?",
         f"It is about {display(hero)}, who becomes curious when {crown.phrase} "
         f"disappears in {f['forest'].label}."),
        ("What was missing?",
         f"{crown.phrase.capitalize()} was missing from the branch where the "
         f"children had left it for their pretend royal game."),
        ("How did the flashback help?",
         f"The flashback reminded {display(hero)} that the forest answered quiet, "
         f"careful searching. That memory is why {hero.pronoun()} chose to "
         f"tiptoe and listen instead of getting angry."),
        ("What did the forest whisper?",
         f"The forest whispered, \"{clue.whisper}.\" The clue mattered because "
         f"it matched the mark at {cache.phrase}."),
        ("Where was the crown found?",
         f"The crown was found at {cache.phrase}. The place could hold the crown "
         f"and carried the same sign the forest whispered about."),
        ("Who moved the crown?",
         f"{mover.name[:1].upper() + mover.name[1:]} moved it. {mover.motive}"),
    ]
    if f.get("solved"):
        qa.append((
            "What was the surprise?",
            f"The surprise was that there was no real thief. The crown had been "
            f"moved for a small reason, and the mystery ended with the game "
            f"restored."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["forest"].tags) | set(f["crown"].tags) | set(f["clue"].tags) | set(f["cache"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("moss_glen", "paper_crown", "tessa", "fern_pocket", "fern",
                "Milo", "boy", "mother", "curious"),
    StoryParams("pine_gate", "paper_crown", "keeper", "fern_pocket", "fern",
                "Nora", "girl", "father", "patient"),
    StoryParams("moon_fern", "paper_crown", "milo", "brook_stone", "moss",
                "Tessa", "girl", "mother", "brave"),
    StoryParams("moss_glen", "leaf_crown", "milo", "hollow_stump", "echo",
                "Rose", "girl", "father", "careful"),
]


def explain_rejection(forest: Forest, crown: Crown, mover: Mover,
                      cache: Cache, clue: MemoryClue) -> str:
    if cache.path not in forest.paths:
        return f"(No story: {cache.label} is not on a path in {forest.label}.)"
    if cache.path not in mover.route:
        return (f"(No story: {mover.name} did not pass {cache.label}, so the "
                f"whisper would point to the wrong mover.)")
    if crown.size > cache.capacity:
        return f"(No story: {crown.phrase} is too large for {cache.label}.)"
    if crown.size not in mover.can_carry:
        return f"(No story: {mover.name} cannot plausibly move {crown.phrase}.)"
    if cache.mark != clue.mark:
        return (f"(No story: the clue names {clue.mark.replace('_', ' ')}, but "
                f"{cache.label} has {cache.mark.replace('_', ' ')}.)")
    return "(No story: this forest mystery is not causally compatible.)"


ASP_RULES = r"""
reachable(F,Ca) :- forest_path(F,P), cache_path(Ca,P).
mover_reached(M,Ca) :- mover_path(M,P), cache_path(Ca,P).
fits(Crown,Ca) :- crown_size(Crown,S), cache_capacity(Ca,K), S <= K.
can_move(M,Crown) :- mover_carries(M,S), crown_size(Crown,S).
mark_matches(Ca,Clue) :- cache_mark(Ca,X), clue_mark(Clue,X).
valid(F,Crown,M,Ca,Clue) :- forest(F), crown(Crown), mover(M), cache(Ca), clue(Clue),
                            reachable(F,Ca), mover_reached(M,Ca), fits(Crown,Ca),
                            can_move(M,Crown), mark_matches(Ca,Clue).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for fid, forest in FORESTS.items():
        lines.append(asp.fact("forest", fid))
        for path in sorted(forest.paths):
            lines.append(asp.fact("forest_path", fid, path))
    for cid, crown in CROWNS.items():
        lines.append(asp.fact("crown", cid))
        lines.append(asp.fact("crown_size", cid, crown.size))
    for mid, mover in MOVERS.items():
        lines.append(asp.fact("mover", mid))
        for path in sorted(mover.route):
            lines.append(asp.fact("mover_path", mid, path))
        for size in sorted(mover.can_carry):
            lines.append(asp.fact("mover_carries", mid, size))
    for cid, cache in CACHES.items():
        lines.append(asp.fact("cache", cid))
        lines.append(asp.fact("cache_path", cid, cache.path))
        lines.append(asp.fact("cache_capacity", cid, cache.capacity))
        lines.append(asp.fact("cache_mark", cid, cache.mark))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_mark", cid, clue.mark))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py, lp = set(valid_combos()), set(asp_valid_combos())
    if py == lp:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between Python and ASP gates:")
    if py - lp:
        print("  only in Python:", sorted(py - lp))
    if lp - py:
        print("  only in clingo:", sorted(lp - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a crown mystery in a whispering forest.")
    ap.add_argument("--forest", choices=FORESTS)
    ap.add_argument("--crown", choices=CROWNS)
    ap.add_argument("--mover", choices=MOVERS)
    ap.add_argument("--cache", choices=CACHES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice([x for x in pool if x != avoid])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if all(getattr(args, k) for k in ("forest", "crown", "mover", "cache", "clue")):
        forest, crown = FORESTS[args.forest], CROWNS[args.crown]
        mover, cache, clue = MOVERS[args.mover], CACHES[args.cache], CLUES[args.clue]
        if not clue_is_sound(forest, crown, mover, cache, clue):
            raise StoryError(explain_rejection(forest, crown, mover, cache, clue))
    combos = [
        c for c in valid_combos()
        if (args.forest is None or c[0] == args.forest)
        and (args.crown is None or c[1] == args.crown)
        and (args.mover is None or c[2] == args.mover)
        and (args.cache is None or c[3] == args.cache)
        and (args.clue is None or c[4] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid forest mystery matches the given options.)")
    forest, crown, mover, cache, clue = rng.choice(combos)
    gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, gender, avoid=MOVERS[mover].name)
    guardian = args.guardian or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(forest, crown, mover, cache, clue, hero, gender, guardian, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        FORESTS[params.forest], CROWNS[params.crown], MOVERS[params.mover],
        CACHES[params.cache], CLUES[params.clue], params.hero,
        params.hero_gender, params.guardian, params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible forest mysteries:\n")
        for row in combos:
            print("  " + " ".join(f"{x:14}" for x in row))
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.crown} in {p.forest} ({p.clue})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
