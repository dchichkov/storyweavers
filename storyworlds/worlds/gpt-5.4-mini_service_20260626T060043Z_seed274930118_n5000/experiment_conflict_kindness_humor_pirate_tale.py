#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/experiment_conflict_kindness_humor_pirate_tale.py
=============================================================================================================

A standalone story world for a small pirate-tale domain with an experiment,
a conflict, a kind turn, and a humorous resolution.

The seed image:
---
A young pirate wants to try an experiment on a windy day at sea.
A proud captain worries the experiment will spoil the map, the lookout,
or the treasure. The crew argues, then a kind helper offers a safer way.
The experiment becomes funny instead of disastrous, and the ship ends in
laughter with a better plan than before.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0
BEATS = ("conflict", "kindness", "humor")

PLACES = {
    "deck": "the deck",
    "cabin": "the cabin",
    "harbor": "the harbor",
    "island": "the island shore",
    "lagoon": "the blue lagoon",
}

ACTIONS = {
    "experiment": {
        "verb": "try an experiment",
        "gerund": "trying an experiment",
        "rush": "rush to pour the bottles together",
        "result": "a bubbly splash",
        "risk": "mess up the chart",
        "topic": "experiment",
        "tag": "experiment",
    },
    "hide_and_seek": {
        "verb": "play hide-and-seek with the lantern",
        "gerund": "playing hide-and-seek with the lantern",
        "rush": "dash behind the crates",
        "result": "a silly echo",
        "risk": "spook the lookout",
        "topic": "hide",
        "tag": "humor",
    },
    "singing": {
        "verb": "sing a sea shanty",
        "gerund": "singing sea shanties",
        "rush": "start singing too loud",
        "result": "a laughing fit",
        "risk": "wake the sleepy gulls",
        "topic": "song",
        "tag": "kindness",
    },
}

PRIZES = {
    "map": {
        "label": "map",
        "phrase": "a rolled-up treasure map",
        "region": "table",
        "type": "map",
        "genders": {"girl", "boy"},
    },
    "hat": {
        "label": "hat",
        "phrase": "a shiny captain's hat",
        "region": "head",
        "type": "hat",
        "genders": {"girl", "boy"},
    },
    "boots": {
        "label": "boots",
        "phrase": "a pair of sea boots",
        "region": "feet",
        "type": "boots",
        "genders": {"girl", "boy"},
        "plural": True,
    },
}

FIXES = [
    {
        "id": "tablecloth",
        "label": "an oilcloth",
        "prep": "spread an oilcloth over the table first",
        "tail": "spread an oilcloth over the table and tried again",
        "guards": {"splash", "foam", "bubbles"},
        "covers": {"table"},
        "beats": {"experiment"},
        "kindness": True,
    },
    {
        "id": "earplugs",
        "label": "soft earplugs",
        "prep": "put in soft earplugs and sing more gently",
        "tail": "put in soft earplugs and sang more gently",
        "guards": {"noise"},
        "covers": {"ears"},
        "beats": {"humor", "kindness"},
        "kindness": True,
    },
    {
        "id": "patch",
        "label": "a dry patch of deck",
        "prep": "move to a dry patch of deck and work there",
        "tail": "moved to a dry patch of deck and worked there",
        "guards": {"splash"},
        "covers": {"table"},
        "beats": {"experiment"},
        "kindness": False,
    },
]

NAMES = {
    "girl": ["Mara", "Pippa", "Lina", "Tessa", "Rae"],
    "boy": ["Jory", "Finn", "Ned", "Bram", "Toby"],
}

TRAITS = ["bold", "cheerful", "curious", "mischievous", "kind"]


# ---------------------------------------------------------------------------
# Shared containers
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    gender: str
    captain: str
    trait: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "first mate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


class World:
    def __init__(self, place: str):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.lines = []
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Causal model
# ---------------------------------------------------------------------------

def _do_action(world: World, actor: Entity, action: dict, narrate: bool = True) -> None:
    actor.memes[action["tag"]] = actor.memes.get(action["tag"], 0.0) + 1.0
    if action["tag"] == "experiment":
        actor.meters["spill"] = actor.meters.get("spill", 0.0) + 1.0
    elif action["tag"] == "kindness":
        actor.memes["warmth"] = actor.memes.get("warmth", 0.0) + 1.0
    elif action["tag"] == "humor":
        actor.memes["humor"] = actor.memes.get("humor", 0.0) + 1.0
    if narrate:
        world.say(f"{actor.id} kept going with {action['gerund']}.")


def predict(world: World, hero: Entity, action: dict, prize: Entity) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(hero.id), action, narrate=False)
    ruined = False
    if action["tag"] == "experiment" and prize.region == "table":
        ruined = True
    return {"ruined": ruined}


def is_reasonable(action: dict, prize: dict) -> bool:
    if action["tag"] == "experiment":
        return prize["region"] == "table"
    if action["tag"] == "humor":
        return True
    if action["tag"] == "kindness":
        return True
    return False


def choose_fix(action: dict, prize: dict):
    for fix in FIXES:
        if action["topic"] in fix["beats"] and prize["region"] in fix["covers"]:
            return fix
    return None


# ---------------------------------------------------------------------------
# Story beats
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity, captain: Entity, prize: Entity, action: dict) -> None:
    world.say(
        f"{hero.id} was a {hero.meters.get('age_word', 'little')} {hero.type} with a {hero.memes.get('trait_word', 'spark')} for adventure."
    )
    world.say(
        f"{hero.id} loved {action['gerund']} aboard the ship, especially when the sea wind made everything feel lively."
    )
    world.say(
        f"{captain.label} guarded {prize.phrase} as if it were the most important thing on the deck."
    )


def arrive(world: World, hero: Entity, captain: Entity, action: dict, place: str) -> None:
    world.say(
        f"One day at {place}, {hero.id} wanted to {action['verb']}."
    )
    world.say(
        f"{captain.label} frowned and said the plan might {action['risk']}."
    )


def conflict(world: World, hero: Entity, captain: Entity, action: dict, prize: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    captain.memes["conflict"] = captain.memes.get("conflict", 0.0) + 1.0
    world.say(
        f"{hero.id} pouted, because {hero.pronoun('possessive')} clever idea was getting tossed overboard."
    )
    world.say(
        f"{hero.id} tried to {action['rush']}, but {captain.label} stepped in front of {prize.it()}."
    )


def kindness_turn(world: World, helper: Entity, hero: Entity, captain: Entity, action: dict, prize: Entity, fix: dict) -> None:
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1.0
    world.say(
        f"Then {helper.id} gave a kind grin and said, \"No need to scrap the whole idea.\""
    )
    world.say(
        f"\"We can {fix['prep']}, and then the experiment can be safe.\""
    )


def humor_turn(world: World, hero: Entity, helper: Entity, action: dict, fix: dict) -> None:
    hero.memes["humor"] = hero.memes.get("humor", 0.0) + 1.0
    world.say(
        f"{hero.id} tried it again, and the first splash looked so silly that even the grumpiest gull seemed to giggle."
    )
    world.say(
        f"With the new plan, {hero.id} and {helper.id} ended up {fix['tail']}, and the deck stayed tidy enough for a proper laugh."
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A prize is at risk when the action splashes or disturbs the region it sits on.
at_risk(A, P) :- action(A), prize(P), action_risks(A, R), prize_region(P, R).

% A fix is compatible if it addresses the same topic and covers the risky region.
fix_works(F, A, P) :- fix(F), action(A), prize(P),
                      fix_topic(F, T), action_topic(A, T),
                      fix_covers(F, R), prize_region(P, R).

valid_story(Place, A, P) :- place(Place), action(A), prize(P),
                            allowed(Place, A), at_risk(A, P), fix_works(_, A, P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("place_label", pid, place))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("action_topic", aid, a["topic"]))
        lines.append(asp.fact("action_risks", aid, "table"))
        lines.append(asp.fact("allowed", "deck", aid))
        lines.append(asp.fact("allowed", "cabin", aid))
        lines.append(asp.fact("allowed", "harbor", aid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p["region"]))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx["id"]))
        for t in fx["beats"]:
            lines.append(asp.fact("fix_topic", fx["id"], t))
        for c in fx["covers"]:
            lines.append(asp.fact("fix_covers", fx["id"], c))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES:
        for action in ACTIONS:
            for prize in PRIZES:
                if is_reasonable(ACTIONS[action], PRIZES[prize]):
                    out.append((place, action, prize))
    return out

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation and Q&A
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    captain = world.add(Entity(id="Captain", kind="character", type=params.captain, label="the captain"))
    prize_cfg = PRIZES[params.prize]
    prize = world.add(Entity(
        id="Prize",
        type=prize_cfg["type"],
        label=prize_cfg["label"],
        phrase=prize_cfg["phrase"],
        plural=prize_cfg.get("plural", False),
        owner=hero.id,
        caretaker=captain.id,
        region=prize_cfg["region"],
    ))
    helper = world.add(Entity(id="Mate", kind="character", type="first mate", label="the first mate"))

    action = ACTIONS[params.action]

    hero.memes["trait_word"] = 1.0
    hero.meters["age_word"] = 1.0

    introduce(world, hero, captain, prize, action)
    world.say("")
    arrive(world, hero, captain, action, world.place)
    conflict(world, hero, captain, action, prize)

    fix = choose_fix(action, prize_cfg)
    if not fix:
        raise StoryError("No reasonable pirate fix fits this conflict.")
    kindness_turn(world, helper, hero, captain, action, prize, fix)
    humor_turn(world, hero, helper, action, fix)

    world.facts.update(
        hero=hero,
        captain=captain,
        prize=prize,
        helper=helper,
        action=action,
        fix=fix,
        place=params.place,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    a = world.facts["action"]
    return [
        f'Write a short pirate tale for a child that includes the word "experiment" and a gentle argument.',
        f"Tell a sea story where {p.name} wants to {a['verb']} but the captain worries about a treasure item.",
        f"Write a funny pirate story where kindness helps solve a conflict and the ending feels cheerful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, captain, prize, action, fix = f["hero"], f["captain"], f["prize"], f["action"], f["fix"]
    qa = [
        QAItem(
            question=f"Who wanted to {action['verb']}?",
            answer=f"{hero.id} wanted to {action['verb']} on the ship.",
        ),
        QAItem(
            question=f"Why did {captain.label} worry about the {prize.label}?",
            answer=f"{captain.label} worried because the plan might {action['risk']}.",
        ),
        QAItem(
            question="What did the first mate suggest?",
            answer=f"The first mate suggested they {fix['prep']}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with a safe plan, a silly splash of humor, and everyone laughing together on the deck.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a captain on a pirate ship?",
            answer="A captain is the leader of the ship, the one who helps guide the crew and make big choices.",
        ),
        QAItem(
            question="What is an experiment?",
            answer="An experiment is a try at something new, so people can see what happens.",
        ),
        QAItem(
            question="Why can spills be a problem on a ship?",
            answer="Spills can make things slippery or messy, and that can make work harder and less safe.",
        ),
        QAItem(
            question="Why do kind helpers matter?",
            answer="Kind helpers can calm everyone down and suggest a safer plan that still lets the fun happen.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.region:
            bits.append(f"region={e.region}")
        if e.plural:
            bits.append("plural=True")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="deck", action="experiment", prize="map", name="Mara", gender="girl", captain="captain", trait="curious"),
    StoryParams(place="harbor", action="hide_and_seek", prize="hat", name="Jory", gender="boy", captain="captain", trait="mischievous"),
    StoryParams(place="cabin", action="singing", prize="boots", name="Tessa", gender="girl", captain="captain", trait="kind"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small pirate tale storyworld with experiment, conflict, kindness, and humor.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=["captain"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if args.place is None or c[0] == args.place
              if args.action is None or c[1] == args.action
              if args.prize is None or c[2] == args.prize]
    # above comprehension is invalid python; replace below
