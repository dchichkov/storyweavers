#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/treatment_marinara_quest_sharing_dialogue_ghost_story.py
===============================================================================================================

A small, child-facing ghost-story world with a quest, sharing, and dialogue.

Seed premise:
- A little ghost needs a soothing treatment after chilly night wandering.
- The same night, the ghost wants to share marinara with a friend.
- A short quest through a quiet house turns the worry into a warm shared meal.

This world keeps the simulation small and state-driven:
- entities have meters (physical state) and memes (emotional state)
- a quest progresses through locations and clues
- dialogue reveals choices and changes feelings
- sharing can reduce loneliness and finish the story with a calm ending image
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

LOCATIONS = {
    "kitchen": {
        "label": "the kitchen",
        "bright": True,
        "clues": {"marinara", "spoon", "warmth"},
    },
    "hallway": {
        "label": "the hallway",
        "bright": False,
        "clues": {"echo", "footsteps", "door"},
    },
    "attic": {
        "label": "the attic",
        "bright": False,
        "clues": {"blanket", "jar", "dust"},
    },
    "garden": {
        "label": "the garden",
        "bright": False,
        "clues": {"moonlight", "basil", "stone"},
    },
}

TREASURES = {
    "marinara": {
        "label": "a jar of marinara",
        "type": "jar",
        "place": "kitchen",
        "warm": True,
        "shareable": True,
    },
    "blanket": {
        "label": "a soft blanket",
        "type": "blanket",
        "place": "attic",
        "warm": True,
        "shareable": False,
    },
    "medicine": {
        "label": "a tiny bottle of treatment",
        "type": "bottle",
        "place": "hallway",
        "warm": False,
        "shareable": False,
    },
}

QUESTS = {
    "marinara": {
        "goal": "find the marinara",
        "verbs": ("search for", "look for", "follow the clue to"),
        "nouns": ("marinara", "sauce", "the red jar"),
    }
}

GHOST_NAMES = ["Mina", "Boo", "Luna", "Pip", "Nora", "Ivy", "Milo", "Wren"]
FRIEND_NAMES = ["Penny", "Toby", "Sage", "Otis", "June", "Mabel", "Eli", "Rose"]
TRAITS = ["brave", "gentle", "curious", "shy", "bright", "kind"]


# ---------------------------------------------------------------------------
# Shared result model helpers
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    held_by: Optional[str] = None
    shareable: bool = False
    warm: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("cold", 0.0)
        self.meters.setdefault("full", 0.0)
        self.meters.setdefault("lost", 0.0)
        self.meters.setdefault("found", 0.0)
        self.meters.setdefault("distance", 0.0)
        self.memes.setdefault("hope", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("joy", 0.0)
        self.memes.setdefault("lonely", 0.0)
        self.memes.setdefault("trust", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type in {"people"} else "it"


@dataclass
class StoryParams:
    place: str = "kitchen"
    treasure: str = "marinara"
    ghost_name: str = "Mina"
    friend_name: str = "Penny"
    trait: str = "gentle"
    seed: Optional[int] = None


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.route: list[str] = []
        self.cursor: int = 0

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
        clone = World(copy.deepcopy(self.params))
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.route = list(self.route)
        clone.cursor = self.cursor
        return clone


# ---------------------------------------------------------------------------
# Physical/emotional rules
# ---------------------------------------------------------------------------
def _rule_cold(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("ghost")
    if hero.location in {"hallway", "garden", "attic"} and hero.meters["cold"] < 2.0:
        sig = ("cold", hero.location)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["cold"] += 1.0
            hero.memes["worry"] += 0.5
            out.append("The chill clung to the ghost like a whisper.")
    return out


def _rule_warmth(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("ghost")
    if hero.held_by == "sauce" or world.get("sauce").location == "table":
        if hero.meters["cold"] > 0:
            sig = ("warmth",)
            if sig not in world.fired:
                world.fired.add(sig)
                hero.meters["cold"] = max(0.0, hero.meters["cold"] - 1.0)
                hero.memes["joy"] += 0.5
                out.append("The warm smell made the ghost feel better.")
    return out


def _rule_sharing(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("ghost")
    friend = world.get("friend")
    sauce = world.get("sauce")
    if sauce.location == "table" and hero.location == friend.location:
        sig = ("share",)
        if sig not in world.fired and sauce.shareable:
            world.fired.add(sig)
            hero.memes["joy"] += 1.0
            friend.memes["joy"] += 1.0
            hero.memes["lonely"] = max(0.0, hero.memes["lonely"] - 1.0)
            friend.memes["trust"] += 1.0
            out.append("They shared the marinara and the room felt friendlier.")
    return out


RULES = [_rule_cold, _rule_warmth, _rule_sharing]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def valid_story(place: str, treasure: str) -> bool:
    return place in LOCATIONS and treasure in TREASURES and TREASURES[treasure]["place"] != "nowhere"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in LOCATIONS:
        raise StoryError("Unknown place.")
    if args.treasure and args.treasure not in TREASURES:
        raise StoryError("Unknown treasure.")
    place = args.place or rng.choice(list(LOCATIONS))
    treasure = args.treasure or rng.choice(list(TREASURES))
    if not valid_story(place, treasure):
        raise StoryError("No reasonable story for those choices.")
    return StoryParams(
        place=place,
        treasure=treasure,
        ghost_name=args.ghost_name or rng.choice(GHOST_NAMES),
        friend_name=args.friend_name or rng.choice(FRIEND_NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def setup_world(params: StoryParams) -> World:
    world = World(params)
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label=params.ghost_name,
        location="hallway",
        meters={"cold": 0.0, "full": 0.0, "lost": 0.0, "found": 0.0, "distance": 0.0},
        memes={"hope": 0.0, "worry": 0.0, "joy": 0.0, "lonely": 1.0, "trust": 0.0},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type="child",
        label=params.friend_name,
        location="kitchen",
        meters={"cold": 0.0, "full": 0.0, "lost": 0.0, "found": 0.0, "distance": 0.0},
        memes={"hope": 0.0, "worry": 0.0, "joy": 0.0, "lonely": 0.0, "trust": 0.0},
    ))
    sauce = world.add(Entity(
        id="sauce",
        kind="thing",
        type="jar",
        label="marinara",
        phrase="a jar of marinara",
        location="kitchen",
        held_by=None,
        shareable=True,
        warm=True,
        meters={"cold": 0.0, "full": 1.0, "lost": 0.0, "found": 1.0, "distance": 0.0},
    ))
    treatment = world.add(Entity(
        id="treatment",
        kind="thing",
        type="bottle",
        label="treatment",
        phrase="a tiny bottle of treatment",
        location="attic",
        held_by=None,
        shareable=False,
        warm=False,
    ))
    world.route = [params.place, "attic", "kitchen"]
    world.facts.update(
        ghost=ghost, friend=friend, sauce=sauce, treatment=treatment,
        place=params.place, treasure=params.treasure, params=params,
    )
    return world


def move_to(world: World, ent_id: str, location: str) -> None:
    ent = world.get(ent_id)
    ent.location = location
    ent.meters["distance"] += 1.0
    if location != "kitchen":
        ent.memes["worry"] += 0.25


def find_treatment(world: World) -> None:
    ghost = world.get("ghost")
    ghost.memes["hope"] += 0.5
    world.say(
        f"On a quiet night, {ghost.label} the {world.params.trait} ghost floated through {LOCATIONS[ghost.location]['label']} looking for help."
    )
    world.say(
        f"{ghost.label} had a chilly whisper in {ghost.label}'s voice and needed a little treatment."
    )
    world.say(
        f"Then {ghost.label} remembered the marinara waiting somewhere in the house, because even a ghost can get hungry after a long quest."
    )


def quest_dialogue(world: World) -> None:
    ghost = world.get("ghost")
    friend = world.get("friend")
    sauce = world.get("sauce")
    treatment = world.get("treatment")

    world.para()
    world.say(
        f"{ghost.label} asked, “Can you help me find the marinara?”"
    )
    world.say(
        f"{friend.label} listened and answered, “Yes. But first, we should look for the treatment in case the cold gets worse.”"
    )

    move_to(world, "ghost", world.route[0])
    if world.route[0] == "attic":
        world.say(f"They drifted into {LOCATIONS['attic']['label']}, where dust sparkled like tiny stars.")
    elif world.route[0] == "garden":
        world.say(f"They glided into {LOCATIONS['garden']['label']}, where moonlight lay on the stones.")
    else:
        world.say(f"They drifted back into {LOCATIONS['kitchen']['label']}, where the warm air smelled like supper.")

    propagate(world)

    if treatment.location == world.route[0]:
        ghost.memes["hope"] += 1.0
        ghost.meters["cold"] = max(0.0, ghost.meters["cold"] - 1.0)
        world.say(
            f"{friend.label} pointed and said, “Look! The treatment is right here.”"
        )
        world.say(
            f"{ghost.label} sighed with relief and felt a little warmer already."
        )
    else:
        world.say(
            f"They did not find the treatment there, so they kept going, one quiet room at a time."
        )

    world.para()
    move_to(world, "ghost", "kitchen")
    move_to(world, "friend", "kitchen")
    world.say(
        f"At last, they came to {LOCATIONS['kitchen']['label']}, and there sat the red jar of marinara like a bright little lantern."
    )
    if sauce.location == "kitchen":
        sauce.held_by = "ghost"
        world.say(
            f"{ghost.label} said, “I found it!” and lifted the marinara carefully."
        )
        world.say(
            f"{friend.label} grinned. “That was a good quest,” {friend.label} said. “Now let's share it.”"
        )
    propagate(world)

    world.para()
    sauce.location = "table"
    ghost.memes["joy"] += 0.5
    friend.memes["joy"] += 0.5
    world.say(
        f"They set the marinara on the table, and the whole kitchen smelled warm and tomato-sweet."
    )
    world.say(
        f"{ghost.label} and {friend.label} each took a small bowl. The ghost's cold faded, and the lonely feeling softened too."
    )
    world.say(
        f"{friend.label} whispered, “This is the best kind of treatment: soup, sharing, and a friend.”"
    )
    propagate(world)

    world.facts.update(
        ending_warm=ghost.meters["cold"] <= 0.0,
        shared=True,
        treatment_found=(treatment.location == world.route[0]),
    )


def story_text(world: World) -> str:
    return world.render()


def generate_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a gentle ghost story about {p.ghost_name} going on a quest for marinara and a little treatment.",
        f"Tell a short story where two friends share marinara after a spooky but friendly search.",
        f"Write a child-friendly dialogue story about a ghost, a kitchen, and a warm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    ghost = world.get("ghost")
    friend = world.get("friend")
    return [
        QAItem(
            question=f"What did {p.ghost_name} need at the start of the story?",
            answer=f"{p.ghost_name} needed a little treatment because the ghost felt chilly after wandering the house.",
        ),
        QAItem(
            question=f"What were {p.ghost_name} and {p.friend_name} looking for on their quest?",
            answer=f"They were looking for marinara, the red jar in the kitchen.",
        ),
        QAItem(
            question=f"How did the story end for {p.ghost_name} and {p.friend_name}?",
            answer=f"They shared the marinara in the kitchen, and {p.ghost_name} felt warmer and less lonely at the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is marinara?",
            answer="Marinara is a tomato sauce often served with pasta or other warm foods.",
        ),
        QAItem(
            question="What is a treatment?",
            answer="A treatment is something that helps make a problem better, like medicine or another kind of care.",
        ),
        QAItem(
            question="Why do friends share food?",
            answer="Friends share food to be kind, to help each other, and to enjoy the meal together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
        if ent.kind:
            bits.append(f"kind={ent.kind}")
        if ent.type:
            bits.append(f"type={ent.type}")
        if ent.location:
            bits.append(f"location={ent.location}")
        if ent.held_by:
            bits.append(f"held_by={ent.held_by}")
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id}: {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
location(L) :- place(L).
treasure(T) :- item(T).

quest_ready(G, T) :- character(G), item(T), shareable(T), warm(T).

reachable(G, L) :- character(G), location(L).
found(T) :- item(T), at(T, kitchen).

shared(G, F, T) :- character(G), character(F), item(T), shareable(T), at(T, kitchen).

good_story(G, F, T) :- quest_ready(G, T), character(F), at(T, kitchen).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for loc in LOCATIONS:
        lines.append(asp.fact("place", loc))
        if LOCATIONS[loc]["bright"]:
            lines.append(asp.fact("bright", loc))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("item", tid))
        lines.append(asp.fact("at", tid, t["place"]))
        if t["shareable"]:
            lines.append(asp.fact("shareable", tid))
        if t["warm"]:
            lines.append(asp.fact("warm", tid))
    lines.append(asp.fact("character", "ghost"))
    lines.append(asp.fact("character", "friend"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/3."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = {
        (params.ghost_name, params.friend_name, params.treasure)
        for params in [StoryParams(place=p, treasure=t, ghost_name="ghost", friend_name="friend")
                       for p in LOCATIONS for t in TREASURES if valid_story(p, t)]
    }
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    find_treatment(world)
    quest_dialogue(world)
    return StorySample(
        params=params,
        story=story_text(world),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost-story world with a quest, sharing, and dialogue.")
    ap.add_argument("--place", choices=sorted(LOCATIONS))
    ap.add_argument("--treasure", choices=sorted(TREASURES))
    ap.add_argument("--ghost-name", choices=GHOST_NAMES)
    ap.add_argument("--friend-name", choices=FRIEND_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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


CURATED = [
    StoryParams(place="kitchen", treasure="marinara", ghost_name="Mina", friend_name="Penny", trait="gentle"),
    StoryParams(place="attic", treasure="marinara", ghost_name="Luna", friend_name="Sage", trait="curious"),
    StoryParams(place="hallway", treasure="marinara", ghost_name="Pip", friend_name="Otis", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_story/3."))
        stories = sorted(set(asp.atoms(model, "good_story")))
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.ghost_name}: quest for marinara in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
