#!/usr/bin/env python3
"""
storyworlds/worlds/whispering_duck_whodunit.py
==============================================

Seed prompt
-----------
Write a story that includes the following words and narrative instruments.
Words: brave, jolly, whispering duck
Features: Suspense, Magic
Style: Whodunit

Source tale written from the seed
---------------------------------
Nora was a brave, jolly child who helped set up the pond fair. The mayor's tiny
silver crown was supposed to sit on the prize pillow, but just before the parade
it vanished. Everyone stared at everyone else, and the fair grew quiet.

On the raffle table sat a painted duck with a yellow bow. Nora had once heard it
whisper when a secret was nearby, so she leaned close. "Wet dots by the reed
basket," breathed the whispering duck. Nora did not accuse anyone. She imagined
who could have crossed the wet stones, carried the crown, and hidden it where the
duck had named.

The clue led Nora to the basket, where the crown gleamed under blue ribbons. The
juggler confessed that he had borrowed it to fix a loose clasp and then panicked
when the parade began. Nora gave the crown back, the parade started, and the duck
gave one last tiny quack that sounded almost proud.

This script rebuilds that shape as a small state-driven storyworld. The magic
duck can whisper only about evidence that is physically compatible with the
suspect's route, the prize size, and the hiding place. Bad accusations are
refused by both the Python gate and the inline ASP twin.
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


def display(ent: Entity) -> str:
    return ent.label or ent.id


@dataclass
class Scene:
    id: str
    place: str
    event: str
    opening: str
    paths: set[str]
    duck_perch: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    size: int
    shine: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    role: str
    route: set[str]
    carries: set[int]
    motive: str
    apology: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    where: str
    path: str
    capacity: int
    trace: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    trace: str
    whisper: str
    sensory: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
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
        clone = World(self.scene)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_missing_suspense(world: World) -> list[str]:
    prize = world.entities.get("prize")
    hero = world.entities.get("hero")
    if not prize or not hero or prize.meters["missing"] < THRESHOLD:
        return []
    sig = ("suspense", prize.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["suspense"] += 1
    hero.memes["courage"] += 1
    return []


def _r_duck_whisper(world: World) -> list[str]:
    duck = world.entities.get("duck")
    hero = world.entities.get("hero")
    if not duck or not hero or duck.meters["near_secret"] < THRESHOLD:
        return []
    sig = ("whisper", duck.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    duck.meters["whispered"] += 1
    hero.memes["curiosity"] += 1
    return []


def _r_evidence_embeds(world: World) -> list[str]:
    hiding = world.entities.get("hiding")
    clue = world.entities.get("clue")
    suspect = world.entities.get("suspect")
    if not hiding or not clue or not suspect:
        return []
    if hiding.meters["searched"] < THRESHOLD:
        return []
    if hiding.attrs.get("trace") != clue.attrs.get("trace"):
        return []
    if hiding.attrs.get("path") not in suspect.attrs.get("route", set()):
        return []
    sig = ("evidence", hiding.id, suspect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hiding.meters["evidence"] += 1
    suspect.memes["truth_pressure"] += 1
    return []


def _r_truth(world: World) -> list[str]:
    hiding = world.entities.get("hiding")
    prize = world.entities.get("prize")
    suspect = world.entities.get("suspect")
    if not hiding or not prize or not suspect:
        return []
    if hiding.meters["evidence"] < THRESHOLD:
        return []
    sig = ("truth", prize.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    prize.meters["missing"] = 0.0
    prize.meters["found"] += 1
    suspect.memes["sorry"] += 1
    return []


RULES = [
    Rule("missing_suspense", _r_missing_suspense),
    Rule("duck_whisper", _r_duck_whisper),
    Rule("evidence", _r_evidence_embeds),
    Rule("truth", _r_truth),
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


def clue_is_sound(scene: Scene, prize: Prize, suspect: Suspect,
                  hiding: HidingPlace, clue: Clue) -> bool:
    return (
        hiding.path in scene.paths
        and hiding.path in suspect.route
        and prize.size <= hiding.capacity
        and prize.size in suspect.carries
        and hiding.trace == clue.trace
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for scene_id, scene in SCENES.items():
        for prize_id, prize in PRIZES.items():
            for suspect_id, suspect in SUSPECTS.items():
                for hiding_id, hiding in HIDING_PLACES.items():
                    for clue_id, clue in CLUES.items():
                        if clue_is_sound(scene, prize, suspect, hiding, clue):
                            combos.append((scene_id, prize_id, suspect_id, hiding_id, clue_id))
    return sorted(combos)


def predict_clue(world: World) -> dict:
    sim = world.copy()
    sim.get("duck").meters["near_secret"] += 1
    sim.get("hiding").meters["searched"] += 1
    propagate(sim)
    return {
        "whispered": sim.get("duck").meters["whispered"] >= THRESHOLD,
        "evidence": sim.get("hiding").meters["evidence"] >= THRESHOLD,
        "found": sim.get("prize").meters["found"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{display(hero)} was a brave, jolly {hero.type} who liked mysteries best "
        f"when {display(friend)} helped keep track of the clues."
    )
    world.say(world.scene.opening)


def start_mystery(world: World, prize: Entity) -> None:
    prize.meters["missing"] += 1
    propagate(world)
    world.say(
        f"Just before {world.scene.event}, {prize.attrs['phrase']} vanished "
        f"from its pillow. The happy noise around {world.scene.place} thinned "
        f"into a puzzled hush."
    )


def meet_duck(world: World) -> None:
    duck = world.get("duck")
    world.say(
        f"On {world.scene.duck_perch} sat {duck.attrs['phrase']}. Everyone "
        f"thought it was only a decoration, but {display(world.get('hero'))} knew "
        f"the duck whispered when a hidden thing was close."
    )


def listen_and_predict(world: World, clue: Clue) -> None:
    hero = world.get("hero")
    duck = world.get("duck")
    duck.meters["near_secret"] += 1
    propagate(world)
    pred = predict_clue(world)
    world.facts["prediction"] = pred
    world.say(
        f'{display(hero)} leaned close. "{clue.whisper}," breathed the whispering duck. '
        f"{clue.sensory}"
    )
    if pred["evidence"]:
        hero.memes["patience"] += 1
        world.say(
            f"{display(hero)} did not point a finger yet. First {hero.pronoun()} "
            f"imagined the path: who could leave that sign, carry the prize, "
            f"and reach the place the duck had named?"
        )


def search(world: World, hiding_cfg: HidingPlace) -> None:
    hero = world.get("hero")
    hiding = world.get("hiding")
    hiding.meters["searched"] += 1
    propagate(world)
    world.say(
        f"{display(hero)} and {display(world.get('friend'))} followed the clue to "
        f"{hiding_cfg.where}. There, {hiding_cfg.reveal}"
    )


def reveal(world: World, suspect_cfg: Suspect) -> None:
    hero = world.get("hero")
    suspect = world.get("suspect")
    prize = world.get("prize")
    if prize.meters["found"] >= THRESHOLD and suspect.memes["sorry"] >= THRESHOLD:
        hero.memes["relief"] += 1
        world.say(
            f"{suspect_cfg.label.capitalize()} stepped forward, cheeks hot. "
            f"{suspect_cfg.apology} {suspect_cfg.motive}"
        )
        world.say(
            f"{display(hero)} returned the {prize.label}, and the jolly music started "
            f"again. The duck gave one tiny quack that sounded almost proud."
        )


def tell(scene: Scene, prize_cfg: Prize, suspect_cfg: Suspect,
         hiding_cfg: HidingPlace, clue_cfg: Clue, name: str, gender: str,
         friend_name: str, friend_gender: str, guardian: str,
         trait: str) -> World:
    world = World(scene)
    hero = world.add(Entity("hero", "character", gender, name, "detective", [trait]))
    friend = world.add(Entity("friend", "character", friend_gender, friend_name, "helper"))
    world.add(Entity("guardian", "character", guardian, "the grown-up", "guardian"))
    world.add(Entity("duck", "thing", "magic", "duck", attrs={
        "phrase": "a painted whispering duck with a yellow bow",
    }))
    world.add(Entity("prize", "thing", "prize", prize_cfg.label, attrs={
        "phrase": prize_cfg.phrase,
        "size": prize_cfg.size,
    }))
    world.add(Entity("suspect", "character", "person", suspect_cfg.label,
                     "suspect", attrs={"route": set(suspect_cfg.route)}))
    world.add(Entity("hiding", "thing", "hiding", hiding_cfg.label, attrs={
        "path": hiding_cfg.path,
        "trace": hiding_cfg.trace,
        "capacity": hiding_cfg.capacity,
    }))
    world.add(Entity("clue", "thing", "clue", clue_cfg.id,
                     attrs={"trace": clue_cfg.trace}))

    introduce(world, hero, friend)
    start_mystery(world, world.get("prize"))
    world.para()
    meet_duck(world)
    listen_and_predict(world, clue_cfg)
    world.para()
    search(world, hiding_cfg)
    reveal(world, suspect_cfg)

    world.facts.update(
        hero=hero, friend=friend, scene=scene, prize=prize_cfg,
        suspect=suspect_cfg, hiding=hiding_cfg, clue=clue_cfg,
        guardian=world.get("guardian"), solved=world.get("prize").meters["found"] >= THRESHOLD,
    )
    return world


SCENES = {
    "pond_fair": Scene(
        "pond_fair", "the pond fair", "the lily-pad parade",
        "One morning, the pond fair was full of paper flags, ribbon hoops, and "
        "neighbors practicing songs for the lily-pad parade.",
        {"wet_stones", "ribbon_table", "reed_path"}, "the raffle table",
        tags={"fair", "magic"}),
    "garden_show": Scene(
        "garden_show", "the garden show", "the flower-crown march",
        "At the garden show, every bench had a pot of marigolds, and every path "
        "smelled like rain-washed leaves.",
        {"mud_gate", "ribbon_table", "hedge_path"}, "a mossy bench",
        tags={"garden", "magic"}),
    "school_stage": Scene(
        "school_stage", "the school stage", "the jolly play",
        "The school stage buzzed with costumes, chalk stars, and children "
        "waiting for the jolly play to begin.",
        {"chalk_steps", "curtain_path", "prop_table"}, "the prop table",
        tags={"stage", "magic"}),
}

PRIZES = {
    "silver_crown": Prize("silver_crown", "crown", "the tiny silver crown", 1,
                          "gleamed like a drop of moonlight", tags={"crown"}),
    "golden_key": Prize("golden_key", "key", "the golden story key", 1,
                        "winked warmly in the light", tags={"key"}),
    "ribbon_cup": Prize("ribbon_cup", "cup", "the blue ribbon cup", 2,
                        "shone with blue painted stars", tags={"cup"}),
}

SUSPECTS = {
    "juggler": Suspect(
        "juggler", "the juggler", "performer",
        {"wet_stones", "chalk_steps", "ribbon_table"}, {1, 2},
        "He had borrowed it to fix a loose clasp before the parade, then panicked "
        "when everyone began looking.",
        '"I meant to bring it back," he said.',
        tags={"juggling"}),
    "baker": Suspect(
        "baker", "the baker", "helper",
        {"ribbon_table", "mud_gate", "prop_table"}, {1},
        "She had tucked it away so frosting would not drip on it, then forgot "
        "which box she had used.",
        '"I was trying to keep it clean," she said.',
        tags={"baking"}),
    "magician": Suspect(
        "magician", "the magician", "performer",
        {"hedge_path", "curtain_path", "reed_path"}, {1, 2},
        "He had hidden it as part of a trick and then lost his nerve when the "
        "real worry began.",
        '"The trick stopped being funny," he said.',
        tags={"magic"}),
}

HIDING_PLACES = {
    "reed_basket": HidingPlace(
        "reed_basket", "reed basket", "the reed basket beside the pond",
        "wet_stones", 2, "wet_dots",
        "under the blue ribbons, the missing prize gleamed.",
        tags={"reeds", "wet"}),
    "flour_box": HidingPlace(
        "flour_box", "flour box", "the flour box behind the cake stand",
        "ribbon_table", 1, "flour_dust",
        "inside a folded towel, the missing prize waited safely.",
        tags={"flour"}),
    "curtain_trunk": HidingPlace(
        "curtain_trunk", "curtain trunk", "the old costume trunk near the curtain",
        "curtain_path", 2, "gold_thread",
        "beneath a velvet cape, the missing prize caught the light.",
        tags={"stage"}),
    "hedge_pot": HidingPlace(
        "hedge_pot", "hedge pot", "the big clay pot by the hedge",
        "hedge_path", 1, "leaf_scratch",
        "behind the soft moss, the missing prize peeked out.",
        tags={"garden"}),
}

CLUES = {
    "wet": Clue("wet", "wet_dots", "Wet dots by the reed basket",
                "A cool drop slid down the duck's painted bill.", tags={"wet"}),
    "flour": Clue("flour", "flour_dust", "White dust where no snow falls",
                  "The duck's voice was soft as a sift of flour.", tags={"flour"}),
    "thread": Clue("thread", "gold_thread", "Gold thread under the dark cloth",
                   "The duck's bow trembled as if a tiny wind touched it.", tags={"thread"}),
    "leaf": Clue("leaf", "leaf_scratch", "A green scratch beside the clay pot",
                 "The duck whispered so softly that only a brave listener would hear.",
                 tags={"leaf"}),
}

GIRL_NAMES = ["Nora", "Mia", "Lily", "Zoe", "Ava", "Rose"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Theo", "Finn"]
TRAITS = ["brave", "curious", "jolly", "patient", "clever"]


@dataclass
class StoryParams:
    scene: str
    prize: str
    suspect: str
    hiding: str
    clue: str
    name: str
    gender: str
    friend: str
    friend_gender: str
    guardian: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "magic": [("What makes a magic clue different from a guess?",
               "A magic clue in a story still needs proof. The hero should check "
               "what the clue points to before blaming anyone.")],
    "crown": [("What is a crown?",
               "A crown is a special headpiece that can show someone is leading "
               "a parade, a game, or a pretend kingdom.")],
    "wet": [("Why do wet footprints help in a mystery?",
             "Wet footprints can show where someone walked. They dry up later, "
             "so a careful detective looks before they disappear.")],
    "flour": [("Why does flour leave a clue?",
               "Flour is a pale powder. It sticks to hands, boxes, and shoes, so "
               "it can leave a dusty mark behind.")],
    "thread": [("How can thread become a clue?",
                "A loose thread can catch on cloth or wood. If it matches a "
                "costume, it can show where that costume went.")],
    "leaf": [("What can a scratch on a leaf show?",
              "A fresh scratch can show that someone brushed past a plant or hid "
              "something nearby.")],
}
KNOWLEDGE_ORDER = ["magic", "crown", "wet", "flour", "thread", "leaf"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a magical whodunit for a young child using the words "brave", '
        f'"jolly", and "whispering duck".',
        f"Tell a suspenseful story where {display(f['hero'])} solves the mystery of "
        f"{f['prize'].phrase} at {f['scene'].place} by checking a magical clue.",
        f"Write a gentle mystery where a talking toy gives a clue, but the child "
        f"waits for evidence before accusing {f['suspect'].label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend = f["hero"], f["friend"]
    prize, suspect, hiding, clue = f["prize"], f["suspect"], f["hiding"], f["clue"]
    qa = [
        ("Who solved the mystery?",
         f"{display(hero)} solved it with help from {display(friend)} and the whispering duck."),
        ("What went missing?",
         f"{prize.phrase.capitalize()} went missing just before {f['scene'].event}. "
         f"That made the cheerful place feel suddenly quiet and suspicious."),
        ("What clue did the duck give?",
         f"The duck whispered, \"{clue.whisper}.\" {display(hero)} treated that as a "
         f"lead to test, not as a reason to accuse someone right away."),
        ("Where was the missing prize found?",
         f"It was found at {hiding.where}. The hiding place matched the clue's "
         f"{hiding.trace.replace('_', ' ')} and was large enough to hold it."),
        ("Who had taken it, and why?",
         f"{suspect.label.capitalize()} had taken it. {suspect.motive}"),
    ]
    if f.get("solved"):
        qa.append((
            "How did the story end?",
            f"{display(hero)} returned the {prize.label}, the celebration began again, "
            f"and the duck's last little sound felt proud. The ending proves the "
            f"mystery changed from suspicion back into trust."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["scene"].tags) | set(f["prize"].tags) | set(f["clue"].tags)
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
    StoryParams("pond_fair", "silver_crown", "juggler", "reed_basket", "wet",
                "Nora", "girl", "Ben", "boy", "mother", "brave"),
    StoryParams("garden_show", "golden_key", "baker", "flour_box", "flour",
                "Leo", "boy", "Mia", "girl", "father", "jolly"),
    StoryParams("school_stage", "ribbon_cup", "magician", "curtain_trunk", "thread",
                "Ava", "girl", "Theo", "boy", "mother", "clever"),
    StoryParams("garden_show", "silver_crown", "magician", "hedge_pot", "leaf",
                "Sam", "boy", "Rose", "girl", "father", "patient"),
]


def explain_rejection(scene: Scene, prize: Prize, suspect: Suspect,
                      hiding: HidingPlace, clue: Clue) -> str:
    if hiding.path not in scene.paths:
        return f"(No story: {hiding.label} is not reachable from {scene.place}.)"
    if hiding.path not in suspect.route:
        return (f"(No story: {suspect.label} never uses the path to "
                f"{hiding.label}, so the clue would accuse the wrong person.)")
    if prize.size > hiding.capacity:
        return (f"(No story: {prize.phrase} is too large for {hiding.label}; "
                f"the hiding place cannot physically hold it.)")
    if prize.size not in suspect.carries:
        return (f"(No story: {suspect.label} cannot plausibly carry "
                f"{prize.phrase} in this little mystery.)")
    if hiding.trace != clue.trace:
        return (f"(No story: the duck's clue is about {clue.trace.replace('_', ' ')}, "
                f"but {hiding.label} leaves {hiding.trace.replace('_', ' ')}.)")
    return "(No story: the clue, suspect, and hiding place do not line up.)"


ASP_RULES = r"""
reachable(S,H) :- scene_path(S,P), hiding_path(H,P).
suspect_can_reach(X,H) :- suspect_path(X,P), hiding_path(H,P).
fits(Prize,H) :- prize_size(Prize,PS), hiding_capacity(H,HC), PS <= HC.
can_carry(X,Prize) :- suspect_carries(X,Size), prize_size(Prize,Size).
trace_matches(H,C) :- hiding_trace(H,T), clue_trace(C,T).
valid(S,Prize,X,H,C) :- scene(S), prize(Prize), suspect(X), hiding(H), clue(C),
                        reachable(S,H), suspect_can_reach(X,H),
                        fits(Prize,H), can_carry(X,Prize), trace_matches(H,C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, scene in SCENES.items():
        lines.append(asp.fact("scene", sid))
        for path in sorted(scene.paths):
            lines.append(asp.fact("scene_path", sid, path))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_size", pid, prize.size))
    for sid, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        for path in sorted(suspect.route):
            lines.append(asp.fact("suspect_path", sid, path))
        for size in sorted(suspect.carries):
            lines.append(asp.fact("suspect_carries", sid, size))
    for hid, hiding in HIDING_PLACES.items():
        lines.append(asp.fact("hiding", hid))
        lines.append(asp.fact("hiding_path", hid, hiding.path))
        lines.append(asp.fact("hiding_capacity", hid, hiding.capacity))
        lines.append(asp.fact("hiding_trace", hid, hiding.trace))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_trace", cid, clue.trace))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    lp = set(asp_valid_combos())
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
        description="Story world: a brave child, a jolly fair, and a whispering duck whodunit.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--hiding", choices=HIDING_PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    choices = [x for x in pool if x != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if all(getattr(args, k) for k in ("scene", "prize", "suspect", "hiding", "clue")):
        scene, prize = SCENES[args.scene], PRIZES[args.prize]
        suspect, hiding, clue = SUSPECTS[args.suspect], HIDING_PLACES[args.hiding], CLUES[args.clue]
        if not clue_is_sound(scene, prize, suspect, hiding, clue):
            raise StoryError(explain_rejection(scene, prize, suspect, hiding, clue))

    combos = [
        c for c in valid_combos()
        if (args.scene is None or c[0] == args.scene)
        and (args.prize is None or c[1] == args.prize)
        and (args.suspect is None or c[2] == args.suspect)
        and (args.hiding is None or c[3] == args.hiding)
        and (args.clue is None or c[4] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid mystery matches the given options.)")
    scene, prize, suspect, hiding, clue = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _pick_name(rng, gender)
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    friend = args.friend or _pick_name(rng, friend_gender, avoid=name)
    guardian = args.guardian or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(scene, prize, suspect, hiding, clue, name, gender,
                       friend, friend_gender, guardian, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SCENES[params.scene], PRIZES[params.prize], SUSPECTS[params.suspect],
        HIDING_PLACES[params.hiding], CLUES[params.clue], params.name,
        params.gender, params.friend, params.friend_gender, params.guardian,
        params.trait,
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
        print(f"{len(combos)} compatible mysteries:\n")
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
            header = f"### {p.name}: {p.prize} at {p.scene} ({p.clue})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
