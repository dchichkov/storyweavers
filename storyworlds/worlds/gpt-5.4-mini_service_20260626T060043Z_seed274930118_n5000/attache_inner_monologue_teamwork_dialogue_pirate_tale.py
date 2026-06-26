#!/usr/bin/env python3
"""
storyworlds/worlds/attache_inner_monologue_teamwork_dialogue_pirate_tale.py
============================================================================

A tiny pirate-tale story world about a crew, an attache case, and a safe way
to work together.

Seed premise:
---
A young pirate finds a shiny attache in the captain's cabin. Inside is a map
to a moonlit cove and a letter stamped with a wax seal. The crew wants the
treasure, but the attache is too important to snatch roughly. The first mate
thinks hard, speaks up, and the pirates work together: one watches the door,
one steadies the lantern, and one opens the clasp carefully. Inside, they find
the map they needed and a note that leads them to the cove. The crew sails on
happy, with the attache safe.

This script models the story as a small state machine:
- the attache can be carried, guarded, opened, and shared;
- characters have meters like suspicion, calm, trust, and readiness;
- dialogue and inner monologue move the emotional state;
- teamwork changes the physical and emotional state and resolves tension.

The prose is generated from the simulated world state rather than from a frozen
template with swapped names.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Entity model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    opened: bool = False
    locked: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["weight", "safety", "access", "shine", "noise"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "calm", "trust", "worry", "joy", "pride", "hope"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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
        clone = World(self.setting)
        clone.entities = dataclasses.deepcopy(self.entities)  # type: ignore[attr-defined]
        clone.lines = list(self.lines)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    name: str
    role: str
    setting: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "ship": {
        "place": "the creaking pirate ship",
        "sound": "the boards groaned softly under bare feet",
        "light": "a lantern flickered like a tiny star",
        "theme": "on deck",
    },
    "harbor": {
        "place": "the windy harbor",
        "sound": "ropes tapped against the mast",
        "light": "the water shone in silver strips",
        "theme": "by the dock",
    },
    "cabin": {
        "place": "the captain's cabin",
        "sound": "the ship swayed in a sleepy rhythm",
        "light": "the lamp made warm gold circles on the table",
        "theme": "inside the cabin",
    },
}

NAMES = {
    "boy": ["Finn", "Nate", "Pip", "Toby"],
    "girl": ["Mara", "Luna", "Bess", "Ivy"],
}

ROLES = {
    "first mate": "first mate",
    "deckhand": "deckhand",
    "captain": "captain",
    "cabin boy": "cabin boy",
}

# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(params.setting)
    config = SETTINGS[params.setting]

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="boy" if params.role != "captain" else "man",
        label=params.name,
        pronouns="",
        meters={"weight": 0.0, "access": 0.0, "safety": 0.0, "noise": 0.0},
        memes={"curiosity": 1.0, "calm": 0.0, "trust": 0.0, "worry": 0.0, "joy": 0.0, "pride": 0.0, "hope": 0.0},
    ))
    mate = world.add(Entity(
        id="mate",
        kind="character",
        type="girl",
        label="first mate",
        meters={"weight": 0.0, "access": 0.0, "safety": 0.0, "noise": 0.0},
        memes={"curiosity": 1.0, "calm": 1.0, "trust": 1.0, "worry": 0.0, "joy": 0.0, "pride": 0.0, "hope": 1.0},
    ))
    captain = world.add(Entity(
        id="captain",
        kind="character",
        type="captain",
        label="captain",
        meters={"weight": 0.0, "access": 0.0, "safety": 0.0, "noise": 0.0},
        memes={"curiosity": 0.5, "calm": 1.0, "trust": 0.5, "worry": 0.0, "joy": 0.0, "pride": 1.0, "hope": 1.0},
    ))
    attache = world.add(Entity(
        id="attache",
        kind="thing",
        type="attache",
        label="attache case",
        phrase="a shiny black attache case with a brass clasp",
        owner="captain",
        carried_by="captain",
        locked=True,
        meters={"weight": 2.0, "access": 0.0, "safety": 1.0, "shine": 1.0, "noise": 0.0},
        memes={},
    ))
    lamp = world.add(Entity(
        id="lamp",
        kind="thing",
        type="lamp",
        label="lantern",
        phrase="a small lantern",
        owner="mate",
        meters={"weight": 0.0, "access": 0.0, "safety": 1.0, "shine": 1.0, "noise": 0.0},
    ))

    world.facts.update(hero=hero, mate=mate, captain=captain, attache=attache, lamp=lamp, config=config)
    return world


def narrate_opening(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    captain: Entity = f["captain"]
    attache: Entity = f["attache"]
    config = f["config"]
    role = hero.label
    world.say(
        f"{role} was a young pirate who loved bright secrets and salty winds."
    )
    world.say(
        f"One evening {hero.label} spotted {attache.phrase} in {captain.label}'s cabin."
    )
    world.say(
        f"{config['sound'].capitalize()}, and {config['light']}."
    )
    hero.memes["curiosity"] += 1.0
    attache.meters["access"] = 0.0


def narrate_inner_monologue(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    attache: Entity = f["attache"]
    hero.memes["curiosity"] += 1.0
    hero.memes["worry"] += 0.5
    world.say(
        f"{hero.label} thought, "
        f"\"If I yank that clasp, I might tear the papers inside. I should be careful.\""
    )
    if attache.locked:
        world.say(
            f"{hero.label} looked at the clasp and felt {hero.pronoun('possessive')} hands go still."
        )


def narrate_dialogue_and_tension(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    mate: Entity = f["mate"]
    captain: Entity = f["captain"]
    attache: Entity = f["attache"]

    hero.memes["worry"] += 1.0
    captain.memes["worry"] += 1.0
    world.say(
        f"\"Easy now,\" said {mate.label}. \"That {attache.label} may hold a map.\""
    )
    world.say(
        f"\"A map?\" whispered {hero.label}, and {hero.pronoun().capitalize()} leaned closer."
    )
    world.say(
        f"\"Yes,\" said {captain.label}. \"But the papers are thin, and the clasp is stiff.\""
    )
    world.say(
        f"{hero.label} wanted to open it at once, yet {hero.pronoun('possessive')} chest felt tight with caution."
    )


def teamwork_open_attache(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    mate: Entity = f["mate"]
    captain: Entity = f["captain"]
    attache: Entity = f["attache"]
    lamp: Entity = f["lamp"]

    mate.memes["calm"] += 1.0
    hero.memes["trust"] += 1.0
    captain.memes["trust"] += 1.0

    world.say(
        f"The three pirates worked together: {mate.label} held up {lamp.label}, "
        f"{captain.label} steadied the case, and {hero.label} pressed the clasp with two careful thumbs."
    )
    attache.locked = False
    attache.opened = True
    attache.meters["access"] = 1.0
    attache.meters["safety"] = 1.0
    hero.memes["joy"] += 1.0
    hero.memes["pride"] += 1.0
    mate.memes["joy"] += 1.0
    captain.memes["joy"] += 1.0

    world.say(
        f"The clasp clicked open, and inside was a folded map, a wax-sealed note, and a tidy pencil."
    )
    world.say(
        f"{hero.label} smiled because the papers were safe, and everyone could see the secret together."
    )


def narrate_resolution(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    mate: Entity = f["mate"]
    captain: Entity = f["captain"]
    attache: Entity = f["attache"]
    world.say(
        f"The map pointed to a moonlit cove, so the crew tucked the {attache.label} under {captain.pronoun('possessive')} arm and sailed on."
    )
    world.say(
        f"{hero.label} grinned at {mate.label}, and {mate.label} grinned back."
    )
    world.say(
        f"By the time the ship reached the water's glow, the attache was safe, the secret was shared, and the whole crew felt braver than before."
    )


def generate_story(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate_opening(world)
    world.para()
    narrate_inner_monologue(world)
    narrate_dialogue_and_tension(world)
    world.para()
    teamwork_open_attache(world)
    narrate_resolution(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    return [
        f"Write a short pirate tale about {hero.label} and a mysterious attache case.",
        "Tell a gentle story where a pirate thinks first, speaks kindly, and works with friends.",
        "Write a child-friendly pirate story that includes inner monologue, teamwork, and dialogue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mate: Entity = f["mate"]
    captain: Entity = f["captain"]
    attache: Entity = f["attache"]
    return [
        QAItem(
            question=f"What did {hero.label} find in {captain.label}'s cabin?",
            answer=f"{hero.label} found {attache.phrase} in {captain.label}'s cabin.",
        ),
        QAItem(
            question=f"Why did {hero.label} not just yank open the case?",
            answer=f"{hero.label} was worried the papers inside might tear, so {hero.pronoun('subject')} chose to be careful.",
        ),
        QAItem(
            question="How did the pirates open the attache safely?",
            answer=f"{mate.label} held the lantern, {captain.label} steadied the case, and {hero.label} opened the clasp gently with both hands.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The case was opened safely, the secret map was shared, and the crew felt happier and braver.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an attache case?",
            answer="An attache case is a small, hard-sided case with a clasp, often used to carry papers or important things.",
        ),
        QAItem(
            question="Why is it good to work together?",
            answer="Working together helps people do careful jobs more safely and makes hard tasks easier.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the quiet thinking a character does inside their own head before they act.",
        ),
        QAItem(
            question="What is dialogue in a story?",
            answer="Dialogue is when characters speak to one another using their own words.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
character(hero). character(mate). character(captain).
thing(attache). thing(lamp).

role(first_mate,mate).
role(captain,captain).
role(deckhand,hero).

holds(captain,attache).
important(attache).
stiff_clasp(attache).
thin_papers(attache).

wants_open(hero,attache).
careful_opening(hero,attache) :- wants_open(hero,attache), important(attache).

teamwork(hero,mate,captain,attache) :-
    careful_opening(hero,attache).

safe(attache) :- teamwork(hero,mate,captain,attache).
shared_secret(attache) :- safe(attache).
happy_ending :- shared_secret(attache).

#show safe/1.
#show shared_secret/1.
#show happy_ending/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("character", "hero"),
        asp.fact("character", "mate"),
        asp.fact("character", "captain"),
        asp.fact("thing", "attache"),
        asp.fact("thing", "lamp"),
        asp.fact("holds", "captain", "attache"),
        asp.fact("important", "attache"),
        asp.fact("stiff_clasp", "attache"),
        asp.fact("thin_papers", "attache"),
        asp.fact("wants_open", "hero", "attache"),
    ]
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = {str(a) for a in model}
    required = {"safe(attache)", "shared_secret(attache)", "happy_ending"}
    if required.issubset(atoms):
        print("OK: ASP twin reaches the safe/shared/happy outcome.")
        return 0
    print("MISMATCH: ASP twin did not reach the expected outcome.")
    print("atoms:", sorted(atoms))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with an attache case.")
    ap.add_argument("--name", choices={n for v in NAMES.values() for n in v})
    ap.add_argument("--role", choices=sorted(ROLES))
    ap.add_argument("--setting", choices=sorted(SETTINGS))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    role = args.role or rng.choice(list(ROLES))
    if args.name:
        name = args.name
    else:
        name = rng.choice(NAMES["girl"] if role == "captain" else NAMES["boy"])
    return StoryParams(name=name, role=role, setting=setting)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- trace ---")
        for eid, ent in sample.world.entities.items():
            meters = {k: v for k, v in ent.meters.items() if v}
            memes = {k: v for k, v in ent.memes.items() if v}
            print(f"{eid}: type={ent.type} meters={meters} memes={memes} opened={ent.opened} locked={ent.locked}")
    if qa:
        print("\n--- prompts ---")
        for p in sample.prompts:
            print(f"- {p}")
        print("\n--- story qa ---")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n--- world qa ---")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def generate(params: StoryParams) -> StorySample:
    return generate_story(params)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTINGS:
            for role in ROLES:
                params = StoryParams(name=NAMES["girl"][0] if role == "captain" else NAMES["boy"][0], role=role, setting=setting, seed=base_seed)
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
