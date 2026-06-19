#!/usr/bin/env python3
"""
storyworlds/worlds/muddy_dialogue_mystery.py
============================================

A standalone story world for:

    Words: muddy
    Features: Dialogue
    Style: Mystery

The domain is a gentle muddy mystery. Something useful goes missing, muddy
marks are found, and the children solve the case by matching evidence to a
plausible culprit. The world refuses unfair mysteries: a culprit must be able to
make the track shape, have a reason to touch the missing thing, and plausibly
come from the muddy place.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: Optional[str] = None
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen"}
        male = {"boy", "father", "dog", "goat", "duck"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    muddy_from: str
    clue_spot: str
    affords: set[str] = field(default_factory=set)


@dataclass
class MissingThing:
    id: str
    label: str
    phrase: str
    use: str
    likely_motives: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    track: str
    shape: str
    hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    tracks: set[str]
    motives: set[str]
    from_places: set[str]
    hiding_place: str
    apology: str
    tags: set[str] = field(default_factory=set)


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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_mud_marks(world: World) -> list[str]:
    culprit = world.entities.get("culprit")
    room = world.get("room")
    if not culprit or culprit.meters["muddy"] < THRESHOLD:
        return []
    sig = ("mud_marks", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["muddy"] += 1
    return ["__mud_marks__"]


def _r_missing_worry(world: World) -> list[str]:
    thing = world.get("missing")
    hero = world.get("hero")
    if thing.meters["missing"] < THRESHOLD:
        sig = ("worry", thing.id)
        world.fired.discard(sig)
        return []
    sig = ("worry", thing.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["curiosity"] += 1
    hero.memes["worry"] += 1
    return ["__worry__"]


def _r_evidence_points(world: World) -> list[str]:
    clue = world.get("clue")
    culprit = world.entities.get("culprit")
    if not culprit or clue.meters["seen"] < THRESHOLD:
        return []
    sig = ("evidence", clue.id, culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    clue.meters["points"] += 1
    world.get("hero").memes["confidence"] += 1
    return ["__evidence__"]


def _r_case_solved(world: World) -> list[str]:
    thing = world.get("missing")
    clue = world.get("clue")
    if thing.meters["returned"] < THRESHOLD or clue.meters["points"] < THRESHOLD:
        return []
    sig = ("solved", thing.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("hero").memes["relief"] += 1
    world.get("helper").memes["relief"] += 1
    return ["__solved__"]


CAUSAL_RULES = [
    Rule("mud_marks", "physical", _r_mud_marks),
    Rule("missing_worry", "social", _r_missing_worry),
    Rule("evidence_points", "mystery", _r_evidence_points),
    Rule("case_solved", "mystery", _r_case_solved),
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


def clue_matches(clue: Clue, suspect: Suspect) -> bool:
    return clue.track in suspect.tracks


def motive_matches(thing: MissingThing, suspect: Suspect) -> bool:
    return bool(thing.likely_motives & suspect.motives)


def place_matches(place: Place, suspect: Suspect) -> bool:
    return place.id in suspect.from_places


def plausible_solution(place: Place, thing: MissingThing, clue: Clue,
                       suspect: Suspect) -> bool:
    return clue_matches(clue, suspect) and motive_matches(thing, suspect) and place_matches(place, suspect)


def culprit_for(place: Place, thing: MissingThing, clue: Clue) -> Optional[Suspect]:
    for suspect in SUSPECTS.values():
        if plausible_solution(place, thing, clue, suspect):
            return suspect
    return None


def predict_solution(world: World, thing: MissingThing, clue: Clue,
                     suspect: Suspect) -> dict:
    sim = world.copy()
    culprit = sim.add(Entity("culprit", kind="character", type=suspect.type,
                             label=suspect.label, role="culprit"))
    culprit.meters["muddy"] += 1
    sim.get("missing").meters["missing"] += 1
    sim.get("clue").meters["seen"] += 1
    propagate(sim, narrate=False)
    return {
        "muddy_room": sim.get("room").meters["muddy"],
        "worry": sim.get("hero").memes["worry"],
        "points": sim.get("clue").meters["points"],
        "fair": plausible_solution(sim.place, thing, clue, suspect),
    }


def introduce(world: World, hero: Entity, helper: Entity, thing: MissingThing) -> None:
    world.say(
        f"One muddy morning, {hero.id} and {helper.id} were {world.place.label}. "
        f"Rain had left {world.place.muddy_from}."
    )
    world.say(
        f"{hero.id} was ready to use {thing.phrase}, because {thing.use}. "
        f'"It was right here," {hero.pronoun()} said.'
    )


def vanish(world: World, thing: MissingThing) -> None:
    missing = world.get("missing")
    missing.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {thing.label} was gone. \"A mystery,\" whispered "
        f"{world.get('helper').id}. \"A muddy mystery.\""
    )


def notice_clue(world: World, hero: Entity, helper: Entity, clue: Clue) -> None:
    world.para()
    clue_ent = world.get("clue")
    clue_ent.meters["seen"] += 1
    world.say(
        f"Near {world.place.clue_spot}, {helper.id} pointed to {clue.label}. "
        f'"Look," {helper.pronoun()} said. "{clue.hint}."'
    )
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} crouched down. \"The mud is not just mess,\" "
        f"{hero.pronoun()} said. \"It is a clue.\""
    )


def question(world: World, hero: Entity, helper: Entity, suspect: Suspect,
             thing: MissingThing, clue: Clue) -> None:
    pred = predict_solution(world, thing, clue, suspect)
    world.facts["predicted_fair"] = pred["fair"]
    world.facts["predicted_points"] = pred["points"]
    world.say(
        f'"Who makes {clue.shape} tracks and might want {thing.label}?" asked '
        f"{helper.id}."
    )
    world.say(
        f'"{suspect.label[0].upper() + suspect.label[1:]}," said {hero.id}. "But we should ask, '
        f'not accuse."'
    )


def find_culprit(world: World, hero: Entity, helper: Entity, suspect: Suspect,
                 thing: MissingThing) -> None:
    world.para()
    culprit = world.add(Entity("culprit", kind="character", type=suspect.type,
                               label=suspect.label, role="culprit"))
    culprit.meters["muddy"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They followed the marks to {suspect.hiding_place}. There sat "
        f"{suspect.label}, muddy and quiet, with {thing.label} nearby."
    )
    world.say(
        f'"Did you take it?" asked {hero.id}. "{suspect.apology}," said '
        f"{suspect.label}. \"I only meant to borrow it.\""
    )


def return_thing(world: World, hero: Entity, helper: Entity, thing: MissingThing,
                 suspect: Suspect) -> None:
    missing = world.get("missing")
    missing.meters["missing"] = 0.0
    missing.meters["returned"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.id} wiped the mud from {thing.label}, and {suspect.label} "
        f"helped put it back."
    )
    world.say(
        f'"Next time, ask first," said {hero.id}. The case was solved, and the '
        f"muddy marks were cleaned away."
    )


def tell(place: Place, thing: MissingThing, clue: Clue, suspect: Suspect,
         hero_name: str = "Mia", hero_type: str = "girl",
         helper_name: str = "Ben", helper_type: str = "boy",
         trait: str = "curious") -> World:
    world = World(place)
    hero = world.add(Entity("hero", kind="character", type=hero_type,
                            label=hero_name, traits=[trait], role="detective"))
    hero.id = hero_name
    world.entities["hero"] = hero
    helper = world.add(Entity("helper", kind="character", type=helper_type,
                              label=helper_name, traits=["careful"], role="helper"))
    helper.id = helper_name
    world.entities["helper"] = helper
    world.add(Entity("room", type="room", label=place.label))
    world.add(Entity("missing", type="object", label=thing.label, owner=hero.id))
    world.add(Entity("clue", type="clue", label=clue.label))

    introduce(world, hero, helper, thing)
    vanish(world, thing)
    notice_clue(world, hero, helper, clue)
    question(world, hero, helper, suspect, thing, clue)
    find_culprit(world, hero, helper, suspect, thing)
    return_thing(world, hero, helper, thing, suspect)

    world.facts.update(
        hero=hero, helper=helper, place=place, thing=thing, clue=clue,
        suspect=suspect, solved=world.get("missing").meters["returned"] >= THRESHOLD,
        muddy_room=world.get("room").meters["muddy"],
    )
    return world


PLACES = {
    "porch": Place(
        "porch", "on the back porch", "a puddle of garden mud", "the umbrella stand",
        affords={"paw", "webbed", "hoof"}),
    "greenhouse": Place(
        "greenhouse", "in the little greenhouse", "wet soil under the tomato pots",
        "the seed shelf", affords={"paw", "hoof", "boot"}),
    "barn": Place(
        "barn", "in the red barn", "sticky mud beside the hay door",
        "the feed bin", affords={"hoof", "webbed", "paw"}),
    "kitchen": Place(
        "kitchen", "in the warm kitchen", "mud from the doorstep mat",
        "the low cupboard", affords={"paw", "boot"}),
}

THINGS = {
    "spoon": MissingThing(
        "spoon", "the little spoon", "the little wooden spoon",
        "a small job needed scooping", {"taste", "carry"}, tags={"spoon", "mystery"}),
    "seed_packet": MissingThing(
        "seed_packet", "the seed packet", "a packet of sunflower seeds",
        "the seeds had to be planted before noon", {"eat", "carry"}, tags={"seed", "mystery"}),
    "ribbon": MissingThing(
        "ribbon", "the blue ribbon", "the blue prize ribbon",
        "it was needed for the fair table", {"wear", "play"}, tags={"ribbon", "mystery"}),
    "brush": MissingThing(
        "brush", "the soft brush", "the soft cleaning brush",
        "mud had to be brushed from the boots", {"scratch", "carry"}, tags={"brush", "mystery"}),
}

CLUES = {
    "paw": Clue(
        "paw", "muddy paw prints", "paw", "small paw-shaped",
        "These prints have toe dots", tags={"muddy", "tracks"}),
    "webbed": Clue(
        "webbed", "wide muddy webbed prints", "webbed", "wide webbed",
        "These prints look like little fans", tags={"muddy", "tracks"}),
    "hoof": Clue(
        "hoof", "two muddy hoof marks", "hoof", "split hoof",
        "These marks are hard and split in the middle", tags={"muddy", "tracks"}),
    "boot": Clue(
        "boot", "muddy boot squares", "boot", "square boot",
        "These marks have a crisscross sole", tags={"muddy", "tracks"}),
}

SUSPECTS = {
    "puppy": Suspect(
        "puppy", "the puppy", "dog", {"paw"}, {"taste", "play", "carry"},
        {"porch", "kitchen", "greenhouse"}, "behind the flour sack",
        "Sorry, I smelled something nice", tags={"dog", "paw"}),
    "duck": Suspect(
        "duck", "the duck", "duck", {"webbed"}, {"eat", "carry"},
        {"porch", "barn"}, "under the water barrel",
        "Quack, I thought it was a snack", tags={"duck", "webbed"}),
    "goat": Suspect(
        "goat", "the goat", "goat", {"hoof"}, {"eat", "scratch", "carry"},
        {"barn", "greenhouse", "porch"}, "beside the hay bale",
        "Maa, I was curious and nosy", tags={"goat", "hoof"}),
    "brother": Suspect(
        "brother", "little brother Toby", "boy", {"boot"}, {"play", "wear", "carry"},
        {"kitchen", "greenhouse"}, "under the table",
        "I wanted to help and forgot to ask", tags={"boot", "asking"}),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Finn", "Noah", "Theo"]
TRAITS = ["curious", "patient", "careful", "brave", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for tid, thing in THINGS.items():
            for cid, clue in CLUES.items():
                if cid not in place.affords:
                    continue
                for sid, suspect in SUSPECTS.items():
                    if plausible_solution(place, thing, clue, suspect):
                        combos.append((pid, tid, cid, sid))
    return combos


@dataclass
class StoryParams:
    place: str
    thing: str
    clue: str
    suspect: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "muddy": [("What does muddy mean?",
               "Muddy means covered with wet dirt. Mud can stick to feet, paws, and shoes.")],
    "tracks": [("How can tracks help solve a mystery?",
                "Tracks show where someone walked and sometimes what kind of foot made the mark.")],
    "mystery": [("What is a mystery?",
                 "A mystery is a puzzle about what happened. Detectives look for clues to solve it.")],
    "asking": [("Why should you ask before borrowing?",
                "Asking first shows respect and keeps other people from worrying when something disappears.")],
    "dog": [("Why do dogs leave paw prints?",
             "Dogs have paws with toes and pads, so muddy paws can stamp little prints on the floor.")],
    "duck": [("Why are duck footprints webbed?",
              "Ducks have webbed feet that help them swim, and those feet can leave fan-shaped prints in mud.")],
    "goat": [("What are hoof marks?",
              "Hoof marks are prints made by animals with hard hooves, like goats or horses.")],
    "seed": [("Why do animals like seeds?",
              "Some animals eat seeds because seeds can be tasty and full of energy.")],
    "spoon": [("What is a spoon used for?",
               "A spoon can scoop, stir, and taste food, so it is useful in a kitchen.")],
    "brush": [("What does a brush do?",
               "A brush has bristles that sweep dirt or mud away from a surface.")],
    "ribbon": [("What is a ribbon?",
                "A ribbon is a strip of cloth used for tying, decorating, or giving as a prize.")],
}
KNOWLEDGE_ORDER = ["muddy", "tracks", "mystery", "asking", "dog", "duck", "goat", "seed", "spoon", "brush", "ribbon"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, thing, clue = f["hero"], f["helper"], f["thing"], f["clue"]
    return [
        f'Write a mystery story for young children using the word "muddy", with lots of dialogue between {hero.id} and {helper.id}.',
        f"Tell a gentle mystery where {thing.label} goes missing, {clue.label} become the clue, and the children solve the case by asking kindly.",
        f'Write a dialogue-heavy story about muddy tracks, a missing object, and the lesson "ask before borrowing."',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper = f["hero"], f["helper"]
    thing, clue, suspect, place = f["thing"], f["clue"], f["suspect"], f["place"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id} and {helper.id}, who solved a muddy mystery {place.label}."),
        ("What went missing?",
         f"{thing.label.capitalize()} went missing. It mattered because {thing.use}."),
        ("What clue did they find?",
         f"They found {clue.label} near {place.clue_spot}. The shape of the marks helped them know who could have made them."),
        ("Who took the missing thing?",
         f"{suspect.label[0].upper() + suspect.label[1:]} had taken {thing.label}. The muddy tracks matched {suspect.label}, and {suspect.label} had a reason to touch it."),
        ("How did the children solve the mystery?",
         f"They followed the evidence and asked a question instead of accusing. Then {suspect.label} explained, returned the item, and helped clean up."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"muddy", "tracks"} | set(f["thing"].tags) | set(f["clue"].tags) | set(f["suspect"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={dict(e.attrs)}")
        lines.append(f"  {e.id:14} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("porch", "spoon", "paw", "puppy", "Mia", "girl", "Ben", "boy", "curious"),
    StoryParams("barn", "seed_packet", "webbed", "duck", "Nora", "girl", "Sam", "boy", "patient"),
    StoryParams("greenhouse", "brush", "hoof", "goat", "Leo", "boy", "Ava", "girl", "careful"),
    StoryParams("kitchen", "ribbon", "boot", "brother", "Zoe", "girl", "Finn", "boy", "thoughtful"),
    StoryParams("porch", "seed_packet", "hoof", "goat", "Theo", "boy", "Rose", "girl", "brave"),
]


def explain_rejection(place: Place, thing: MissingThing, clue: Clue,
                      suspect: Optional[Suspect] = None) -> str:
    if clue.id not in place.affords:
        return (f"(No story: {place.label} can have mud, but {clue.label} do not "
                "fit this setting's plausible track catalog.)")
    if suspect is None:
        return (f"(No story: no suspect can fairly connect {clue.label} to "
                f"{thing.label} in {place.label}.)")
    if not clue_matches(clue, suspect):
        return (f"(No story: {suspect.label} cannot make {clue.track} tracks, "
                f"so {clue.label} would be unfair evidence.)")
    if not motive_matches(thing, suspect):
        return (f"(No story: {suspect.label} has no clear reason to take "
                f"{thing.label}; the mystery would not be fair.)")
    if not place_matches(place, suspect):
        return (f"(No story: {suspect.label} does not plausibly come from "
                f"{place.label}, so the muddy trail is rejected.)")
    return "(No story: this mystery has no fair solution.)"


ASP_RULES = r"""
clue_matches(C,S) :- clue_track(C,T), suspect_track(S,T).
motive_matches(Thing,S) :- thing_motive(Thing,M), suspect_motive(S,M).
place_matches(P,S) :- suspect_place(S,P).
plausible(P,Thing,C,S) :- affords(P,C), clue_matches(C,S), motive_matches(Thing,S), place_matches(P,S).
valid(P,Thing,C,S) :- place(P), thing(Thing), clue(C), suspect(S), plausible(P,Thing,C,S).
culprit(P,Thing,C,S) :- valid(P,Thing,C,S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for clue_id in sorted(place.affords):
            lines.append(asp.fact("affords", pid, clue_id))
    for tid, thing in THINGS.items():
        lines.append(asp.fact("thing", tid))
        for motive in sorted(thing.likely_motives):
            lines.append(asp.fact("thing_motive", tid, motive))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_track", cid, clue.track))
    for sid, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        for track in sorted(suspect.tracks):
            lines.append(asp.fact("suspect_track", sid, track))
        for motive in sorted(suspect.motives):
            lines.append(asp.fact("suspect_motive", sid, motive))
        for place_id in sorted(suspect.from_places):
            lines.append(asp.fact("suspect_place", sid, place_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_culprits(place: str, thing: str, clue: str) -> list[str]:
    import asp
    extra = "\n".join([
        asp.fact("chosen_place", place),
        asp.fact("chosen_thing", thing),
        asp.fact("chosen_clue", clue),
        "chosen_culprit(S) :- chosen_place(P), chosen_thing(T), chosen_clue(C), culprit(P,T,C,S).",
    ])
    model = asp.one_model(f"{asp_facts()}\n{ASP_RULES}\n{extra}\n#show chosen_culprit/1.\n")
    return sorted(s for (s,) in asp.atoms(model, "chosen_culprit"))


def asp_verify() -> int:
    rc = 0
    c_set, p_set = set(asp_valid_combos()), set(valid_combos())
    if c_set == p_set:
        print(f"OK: clingo gate matches valid_combos() ({len(c_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if c_set - p_set:
            print("  only in clingo:", sorted(c_set - p_set))
        if p_set - c_set:
            print("  only in python:", sorted(p_set - c_set))
    for pid, place in PLACES.items():
        for tid, thing in THINGS.items():
            for cid, clue in CLUES.items():
                py = sorted(sid for sid, s in SUSPECTS.items() if plausible_solution(place, thing, clue, s))
                asp_ids = asp_culprits(pid, tid, cid)
                if py != asp_ids:
                    rc = 1
                    print(f"MISMATCH culprit set for {(pid, tid, cid)}: python={py} asp={asp_ids}")
                    return rc
    if rc == 0:
        print("OK: culprit query matches Python plausible_solution() for all scenarios.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a muddy dialogue mystery. Unspecified choices are random.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible mysteries derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP gate matches Python")
    ap.add_argument("--show-asp", action="store_true", help="print facts + inline ASP rules")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.clue and args.clue not in PLACES[args.place].affords:
        thing = THINGS[args.thing] if args.thing else next(iter(THINGS.values()))
        raise StoryError(explain_rejection(PLACES[args.place], thing, CLUES[args.clue]))
    if args.place and args.thing and args.clue and args.suspect:
        pl, th, cl, su = PLACES[args.place], THINGS[args.thing], CLUES[args.clue], SUSPECTS[args.suspect]
        if not plausible_solution(pl, th, cl, su):
            raise StoryError(explain_rejection(pl, th, cl, su))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.thing is None or c[1] == args.thing)
              and (args.clue is None or c[2] == args.clue)
              and (args.suspect is None or c[3] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, thing, clue, suspect = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or _pick_name(rng, hero_gender)
    helper = args.helper or _pick_name(rng, helper_gender, avoid=hero)
    trait = rng.choice(TRAITS)
    return StoryParams(place, thing, clue, suspect, hero, hero_gender, helper, helper_gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place], THINGS[params.thing], CLUES[params.clue],
        SUSPECTS[params.suspect], params.hero, params.hero_gender,
        params.helper, params.helper_gender, params.trait,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, thing, clue, suspect) combos:\n")
        for place, thing, clue, suspect in combos:
            print(f"  {place:10} {thing:12} {clue:7} {suspect}")
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
            header = f"### {p.hero} and {p.helper}: {p.thing} ({p.clue} -> {p.suspect})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
