#!/usr/bin/env python3
"""
storyworlds/worlds/lodge_teamwork_detective.py
==============================================

A standalone story world for a TinyStories-style prompt:

    Words: lodge
    Features: Teamwork
    Style: Detective Story

The world models a small lodge mystery where a child detective cannot solve the
case alone. Evidence has to be physically present, a teammate has to choose a
tool that can actually read that evidence, and the solved case must point to the
right harmless culprit. The constraint gate refuses mysteries whose clue cannot
reasonably identify the missing object's trail.
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
    owner: Optional[str] = None
    location: str = ""
    hidden_at: str = ""
    clue_kind: str = ""
    can_detect: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "aunt", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "uncle", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def adult_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )


@dataclass
class Lodge:
    id: str
    name: str
    weather: str
    rooms: set[str]
    detail: str


@dataclass
class Case:
    id: str
    missing: str
    phrase: str
    owner_label: str
    owner_type: str
    vanish_room: str
    found_at: str
    culprit: str
    culprit_kind: str
    motive: str
    allowed_clues: set[str]
    lesson: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    kind: str
    label: str
    mark: str
    trail: str
    source: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    verb: str
    detects: set[str]
    teammate_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, lodge: Lodge) -> None:
        self.lodge = lodge
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
        clone = World(self.lodge)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def role(world: World, name: str) -> Optional[Entity]:
    return next((e for e in world.entities.values() if e.role == name), None)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_missing_worry(world: World) -> list[str]:
    obj = world.entities.get("missing")
    owner = world.entities.get("owner")
    hero = role(world, "detective")
    if not obj or not owner or not hero or obj.meters["missing"] < THRESHOLD:
        return []
    sig = ("worry", obj.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["worry"] += 1
    hero.memes["curiosity"] += 1
    return []


def _r_lone_stall(world: World) -> list[str]:
    hero = role(world, "detective")
    if not hero or hero.memes["curiosity"] < THRESHOLD or hero.memes["teamwork"] >= THRESHOLD:
        return []
    sig = ("stall", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["stuck"] += 1
    return []


def _r_evidence(world: World) -> list[str]:
    clue = world.entities.get("clue")
    tool = world.entities.get("tool")
    if not clue or not tool:
        return []
    if clue.meters["present"] < THRESHOLD or tool.meters["used"] < THRESHOLD:
        return []
    if clue.clue_kind not in tool.can_detect:
        return []
    sig = ("evidence", clue.id, tool.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    clue.meters["read"] += 1
    for ent in (role(world, "detective"), role(world, "teammate")):
        if ent is not None:
            ent.memes["confidence"] += 1
    return []


def _r_team_solve(world: World) -> list[str]:
    hero = role(world, "detective")
    partner = role(world, "teammate")
    clue = world.entities.get("clue")
    obj = world.entities.get("missing")
    if not hero or not partner or not clue or not obj:
        return []
    if hero.memes["teamwork"] < THRESHOLD or partner.memes["teamwork"] < THRESHOLD:
        return []
    if clue.meters["read"] < THRESHOLD:
        return []
    sig = ("solve", obj.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obj.meters["found"] += 1
    obj.meters["missing"] = 0
    hero.memes["joy"] += 1
    partner.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule("missing_worry", "social", _r_missing_worry),
    Rule("lone_stall", "social", _r_lone_stall),
    Rule("evidence", "physical", _r_evidence),
    Rule("team_solve", "social", _r_team_solve),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True
            else:
                before = len(world.fired)
                rule.apply(world)
                changed = changed or len(world.fired) > before


def clue_fits_case(case: Case, clue: Clue) -> bool:
    return clue.kind in case.allowed_clues


def tool_reads_clue(tool: Tool, clue: Clue) -> bool:
    return clue.kind in tool.detects


def lodge_hosts_case(lodge: Lodge, case: Case) -> bool:
    return case.vanish_room in lodge.rooms and case.found_at in lodge.rooms


def valid_combo(lodge: Lodge, case: Case, clue: Clue, tool: Tool) -> bool:
    return lodge_hosts_case(lodge, case) and clue_fits_case(case, clue) and tool_reads_clue(tool, clue)


def predict_solution(world: World, clue: Clue, tool: Tool) -> dict:
    sim = world.copy()
    detective = role(sim, "detective")
    teammate = role(sim, "teammate")
    if detective is not None:
        detective.memes["teamwork"] += 1
    if teammate is not None:
        teammate.memes["teamwork"] += 1
    sim.get("tool").meters["used"] += 1
    sim.get("clue").meters["present"] += 1
    propagate(sim)
    return {
        "read": sim.get("clue").meters["read"] >= THRESHOLD,
        "found": sim.get("missing").meters["found"] >= THRESHOLD,
        "tool": tool.label,
        "clue": clue.label,
    }


def introduce(world: World, hero: Entity, partner: Entity, case: Case) -> None:
    world.say(
        f"At {world.lodge.name}, where {world.lodge.detail}, {hero.id} kept a tiny "
        f"notebook for lodge mysteries."
    )
    world.say(
        f"{partner.id} was {hero.pronoun('possessive')} best teammate, because "
        f"{partner.pronoun()} noticed the small things {hero.id} missed."
    )
    world.say(f"That {world.lodge.weather} morning, {case.owner_label}'s {case.missing} vanished.")


def report_case(world: World, owner: Entity, missing: Entity, case: Case) -> None:
    missing.meters["missing"] += 1
    propagate(world)
    world.say(
        f'"Detectives, please help," said {case.owner_label}. '
        f'"I left {case.phrase} in the {case.vanish_room}, and now '
        f'{"they are" if case.plural else "it is"} gone."'
    )


def solo_search(world: World, hero: Entity) -> None:
    propagate(world)
    if hero.memes["stuck"] >= THRESHOLD:
        world.say(
            f"{hero.id} searched under chairs, behind boots, and beside the firewood, "
            f"but working alone only made the mystery feel bigger."
        )


def team_plan(world: World, hero: Entity, partner: Entity, tool: Tool) -> None:
    hero.memes["teamwork"] += 1
    partner.memes["teamwork"] += 1
    world.say(
        f'Then {partner.id} tapped the notebook. "Teamwork," {partner.pronoun()} said. '
        f'"You ask questions, and I will {tool.verb}."'
    )


def find_clue(world: World, partner: Entity, clue: Entity, clue_cfg: Clue) -> None:
    clue.meters["present"] += 1
    world.say(
        f"Near the {world.facts['case'].vanish_room}, {partner.id} found "
        f"{clue_cfg.mark}. {clue_cfg.trail}"
    )


def use_tool(world: World, tool_ent: Entity, tool: Tool) -> None:
    tool_ent.meters["used"] += 1
    propagate(world)
    world.say(tool.teammate_line)


def solve(world: World, hero: Entity, partner: Entity, case: Case, clue: Clue) -> None:
    propagate(world)
    found = world.get("missing").meters["found"] >= THRESHOLD
    if not found:
        return
    if case.culprit_kind in {"dog", "kitten"}:
        found = f"There they found {case.phrase} beside {case.culprit}, who had {case.motive}."
    else:
        found = f"There they found {case.phrase}, right where {case.culprit} had {case.motive}."
    world.say(f"The clue pointed to the {case.found_at}. {found}")
    world.say(
        f"{case.owner_label} laughed with relief, and {hero.id} wrote the answer "
        f"in the notebook: {case.lesson}."
    )
    world.say(
        f"{hero.id} and {partner.id} high-fived, because the lodge mystery had "
        f"needed two detectives, not one."
    )


def tell(
    lodge: Lodge,
    case: Case,
    clue: Clue,
    tool: Tool,
    hero_name: str,
    hero_gender: str,
    partner_name: str,
    partner_gender: str,
    trait: str,
) -> World:
    world = World(lodge)
    hero = world.add(Entity(hero_name, "character", hero_gender, role="detective", traits=[trait]))
    partner = world.add(Entity(partner_name, "character", partner_gender, role="teammate"))
    owner = world.add(Entity("owner", "character", case.owner_type, label=case.owner_label))
    missing = world.add(Entity("missing", "thing", case.missing, label=case.missing, owner="owner"))
    clue_ent = world.add(Entity("clue", "thing", clue.kind, label=clue.label, clue_kind=clue.kind))
    tool_ent = world.add(Entity("tool", "thing", tool.id, label=tool.label, can_detect=set(tool.detects)))

    world.facts.update(
        hero=hero, partner=partner, owner=owner, missing=missing,
        case=case, clue=clue, tool=tool, lodge=lodge,
    )

    introduce(world, hero, partner, case)
    report_case(world, owner, missing, case)

    world.para()
    solo_search(world, hero)
    team_plan(world, hero, partner, tool)
    pred = predict_solution(world, clue, tool)
    world.facts["predicted_solution"] = pred
    world.say(
        f"{hero.id} guessed that if {partner.id} used {tool.label} on {clue.label}, "
        f"the trail would lead them to the missing {case.missing}."
    )

    world.para()
    find_clue(world, partner, clue_ent, clue)
    use_tool(world, tool_ent, tool)
    solve(world, hero, partner, case, clue)
    world.facts["solved"] = missing.meters["found"] >= THRESHOLD
    return world


LODGES = {
    "pine": Lodge("pine", "Pinecone Lodge", "snowy", {"lobby", "mudroom", "porch", "kitchen"},
                  "pine branches scratched softly at the windows"),
    "lake": Lodge("lake", "Blue Lake Lodge", "misty", {"lobby", "boatroom", "porch", "kitchen"},
                  "the lake made silver fog around the porch"),
    "hill": Lodge("hill", "Hilltop Lodge", "windy", {"lobby", "mudroom", "gear room", "kitchen"},
                  "the old roof hummed whenever the wind blew"),
}

CASES = {
    "key": Case("key", "key", "the brass room key", "Aunt Nora", "aunt", "lobby", "porch",
                "the lodge dog", "dog", "carried it to guard the porch",
                {"pawprints", "pine_needles"}, "good detectives follow evidence together",
                False,
                {"key", "dog", "lodge"}),
    "mittens": Case("mittens", "mittens", "the red wool mittens", "Uncle Ben", "uncle",
                    "mudroom", "kitchen", "the cook's kitten", "kitten",
                    "dragged them to a warm basket", {"yarn", "pawprints"},
                    "a soft clue can solve a cold case", True,
                    {"mittens", "tracks", "lodge"}),
    "map": Case("map", "map", "the folded trail map", "Ranger May", "woman",
                "boatroom", "porch", "a gust of wind", "wind",
                "pushed it under the porch bench", {"water_spots", "pine_needles"},
                "even the wind leaves clues", False, {"map", "weather", "lodge"}),
    "medal": Case("medal", "medal", "the shiny ski medal", "Coach Lee", "man",
                  "gear room", "mudroom", "a loose backpack pocket", "pocket",
                  "spilled it near the boot rack", {"scratches", "bootprints"},
                  "small marks tell big truths", False, {"medal", "teamwork", "lodge"}),
}

CLUES = {
    "pawprints": Clue("pawprints", "pawprints", "small pawprints",
                      "a row of tiny pawprints in the dust",
                      "The prints curved away like commas in a secret sentence.",
                      "animal feet", {"tracks"}),
    "pine_needles": Clue("pine_needles", "pine_needles", "fresh pine needles",
                         "three green pine needles caught on the rug",
                         "They smelled like the porch rail after snow.",
                         "outside branch", {"pine", "nature"}),
    "yarn": Clue("yarn", "yarn", "a red yarn thread",
                 "one red yarn thread snagged on a basket",
                 "It matched the missing wool exactly.", "wool", {"fiber"}),
    "water_spots": Clue("water_spots", "water_spots", "round water spots",
                        "three round water spots leading toward the door",
                        "Each spot was smaller than the one before it.",
                        "wet paper", {"water"}),
    "scratches": Clue("scratches", "scratches", "thin silver scratches",
                      "thin silver scratches on the boot bench",
                      "They shone whenever the lamp swung overhead.",
                      "metal", {"metal"}),
    "bootprints": Clue("bootprints", "bootprints", "muddy bootprints",
                       "muddy bootprints crossing the floor",
                       "The left print had a star-shaped nick in it.",
                       "boots", {"tracks", "mud"}),
}

TOOLS = {
    "magnifier": Tool("magnifier", "a magnifying glass", "check every mark with the magnifying glass",
                      {"pawprints", "scratches", "pine_needles"},
                      "The magnifying glass made the clue sharp and certain.",
                      {"magnifier", "detective"}),
    "thread_card": Tool("thread_card", "a thread card", "compare every fiber on the thread card",
                        {"yarn", "pine_needles"}, "The thread card showed which tiny piece matched.",
                        {"fiber", "detective"}),
    "chalk": Tool("chalk", "detective chalk", "circle the trail with detective chalk",
                  {"bootprints", "pawprints", "water_spots"},
                  "The chalk circles turned scattered marks into one clear trail.",
                  {"tracks", "detective"}),
    "lamp": Tool("lamp", "a little lodge lamp", "hold the little lamp low to the floor",
                 {"scratches", "water_spots"}, "The low lamp made the faint marks glimmer.",
                 {"lamp", "detective"}),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Rose"]
BOY_NAMES = ["Leo", "Tom", "Ben", "Max", "Finn", "Sam"]
TRAITS = ["curious", "careful", "patient", "bold", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for lodge_id, lodge in LODGES.items():
        for case_id, case in CASES.items():
            for clue_id, clue in CLUES.items():
                for tool_id, tool in TOOLS.items():
                    if valid_combo(lodge, case, clue, tool):
                        combos.append((lodge_id, case_id, clue_id, tool_id))
    return sorted(combos)


@dataclass
class StoryParams:
    lodge: str
    case: str
    clue: str
    tool: str
    hero: str
    hero_gender: str
    partner: str
    partner_gender: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "lodge": [("What is a lodge?",
               "A lodge is a cozy place where people stay, often near woods, hills, or a lake.")],
    "detective": [("What does a detective do?",
                   "A detective looks carefully at clues and asks questions to solve a mystery.")],
    "tracks": [("Why are tracks useful clues?",
                "Tracks show where someone or something walked. They can point detectives in the right direction.")],
    "fiber": [("How can a thread be a clue?",
               "A thread can match cloth or wool from an object, so it helps show where that object went.")],
    "magnifier": [("What is a magnifying glass for?",
                   "A magnifying glass makes small things look bigger, which helps people see tiny details.")],
    "lamp": [("How can a lamp help in a mystery?",
              "A lamp adds light, and light can reveal faint marks, scratches, or water spots.")],
    "teamwork": [("Why does teamwork help solve problems?",
                  "Teamwork lets people share jobs and ideas. One person may notice what another person misses.")],
}
KNOWLEDGE_ORDER = ["lodge", "detective", "teamwork", "tracks", "fiber", "magnifier", "lamp"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case, clue = f["case"], f["clue"]
    hero, partner = f["hero"], f["partner"]
    missing_phrase = f"some missing {case.missing}" if case.plural else f"a missing {case.missing}"
    return [
        f'Write a detective story for young children that includes the word "lodge" '
        f"and solves a mystery through teamwork.",
        f"Tell a story where {hero.id} and {partner.id} work together at a lodge "
        f"to find {case.phrase} by following {clue.label}.",
        f"Write a gentle mystery about {missing_phrase}, a real clue, and "
        f"two child detectives who solve the case as a team.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, partner, case, clue, tool = f["hero"], f["partner"], f["case"], f["clue"], f["tool"]
    qa = [
        ("Who were the detectives in the story?",
         f"The detectives were {hero.id} and {partner.id}. They solved the lodge mystery together."),
        ("What went missing?",
         f"{case.owner_label}'s {case.missing} went missing from the {case.vanish_room}."),
        ("What clue did they find?",
         f"They found {clue.label}. It mattered because it connected the missing {case.missing} to the {case.found_at}."),
        ("How did teamwork help?",
         f"{hero.id} asked questions while {partner.id} used {tool.label}. Their shared work turned the clue into evidence."),
    ]
    if f.get("solved"):
        where = f"on the {case.found_at}" if case.found_at == "porch" else f"in the {case.found_at}"
        if case.culprit_kind in {"dog", "kitten"}:
            found_answer = f"They found {case.phrase} {where} beside {case.culprit}. {case.culprit.capitalize()} had {case.motive}."
        else:
            found_answer = f"They found {case.phrase} {where}, where {case.culprit} had {case.motive}."
        qa.append(("Where was the missing thing found?",
                   found_answer))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"lodge", "detective", "teamwork"} | set(f["case"].tags) | set(f["clue"].tags) | set(f["tool"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    lines += [f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)]
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    return "\n".join(lines)


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
        if e.can_detect:
            bits.append(f"detects={sorted(e.can_detect)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("pine", "key", "pawprints", "magnifier", "Mia", "girl", "Leo", "boy", "curious"),
    StoryParams("pine", "mittens", "yarn", "thread_card", "Tom", "boy", "Lily", "girl", "careful"),
    StoryParams("lake", "map", "water_spots", "lamp", "Nora", "girl", "Finn", "boy", "patient"),
    StoryParams("hill", "medal", "bootprints", "chalk", "Sam", "boy", "Zoe", "girl", "thoughtful"),
]


def explain_rejection(lodge: Lodge, case: Case, clue: Clue, tool: Tool) -> str:
    if not lodge_hosts_case(lodge, case):
        return f"(No story: {lodge.name} does not contain both the {case.vanish_room} and the {case.found_at} for this case.)"
    if not clue_fits_case(case, clue):
        return f"(No story: {clue.label} does not honestly point to the missing {case.missing}; choose a clue tied to {sorted(case.allowed_clues)}.)"
    return f"(No story: {tool.label} cannot read {clue.label}; the teammate's tool must detect {clue.kind}.)"


ASP_RULES = r"""
hosts_case(L,C) :- room(L,V), room(L,F), vanish_room(C,V), found_at(C,F).
fits(C,Cl)      :- allowed_clue(C,K), clue_kind(Cl,K).
reads(T,Cl)     :- detects(T,K), clue_kind(Cl,K).
valid(L,C,Cl,T) :- lodge(L), case(C), clue(Cl), tool(T), hosts_case(L,C), fits(C,Cl), reads(T,Cl).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for lid, lodge in LODGES.items():
        lines.append(asp.fact("lodge", lid))
        for room in sorted(lodge.rooms):
            lines.append(asp.fact("room", lid, room))
    for cid, case in CASES.items():
        lines += [
            asp.fact("case", cid),
            asp.fact("vanish_room", cid, case.vanish_room),
            asp.fact("found_at", cid, case.found_at),
        ]
        for k in sorted(case.allowed_clues):
            lines.append(asp.fact("allowed_clue", cid, k))
    for clue_id, clue in CLUES.items():
        lines += [asp.fact("clue", clue_id), asp.fact("clue_kind", clue_id, clue.kind)]
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for k in sorted(tool.detects):
            lines.append(asp.fact("detects", tool_id, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: lodge teamwork detective mystery.")
    ap.add_argument("--lodge", choices=LODGES)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--partner")
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
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
    return rng.choice([n for n in pool if n != avoid])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.lodge and args.case and args.clue and args.tool:
        if not valid_combo(LODGES[args.lodge], CASES[args.case], CLUES[args.clue], TOOLS[args.tool]):
            raise StoryError(explain_rejection(LODGES[args.lodge], CASES[args.case], CLUES[args.clue], TOOLS[args.tool]))
    combos = [
        c for c in valid_combos()
        if (args.lodge is None or c[0] == args.lodge)
        and (args.case is None or c[1] == args.case)
        and (args.clue is None or c[2] == args.clue)
        and (args.tool is None or c[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid lodge mystery matches the given options.)")
    lodge, case, clue, tool = rng.choice(combos)
    hg = args.hero_gender or rng.choice(["girl", "boy"])
    pg = args.partner_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hg)
    partner = args.partner or _pick_name(rng, pg, avoid=hero)
    return StoryParams(lodge, case, clue, tool, hero, hg, partner, pg, rng.choice(TRAITS))


def generate(params: StoryParams) -> StorySample:
    world = tell(
        LODGES[params.lodge], CASES[params.case], CLUES[params.clue], TOOLS[params.tool],
        params.hero, params.hero_gender, params.partner, params.partner_gender, params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (lodge, case, clue, tool) combos:\n")
        for row in combos:
            print("  " + " ".join(f"{x:12}" for x in row))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        p = sample.params
        header = ""
        if args.all:
            header = f"### {p.hero} & {p.partner}: {p.case} at {p.lodge}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
