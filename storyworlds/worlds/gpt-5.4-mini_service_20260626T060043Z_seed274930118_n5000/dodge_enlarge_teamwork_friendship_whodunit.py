#!/usr/bin/env python3
"""
storyworlds/worlds/dodge_enlarge_teamwork_friendship_whodunit.py
=================================================================

A small whodunit storyworld about two friends who solve a missing-object mystery
by teaming up, dodging one small hazard, and enlarging a clue so the truth can
be seen clearly.

The seed premise:
- Something important has vanished from a snug little place.
- Two friends investigate.
- They use teamwork and friendship to follow clues.
- One clue is tiny, so they enlarge it.
- They must dodge a small obstacle on the way to the answer.
- The story ends with the missing thing found and the real culprit revealed.

This script follows the Storyweavers contract:
- standalone stdlib script
- shared result containers imported eagerly
- ASP helper imported lazily
- supports default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carries: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoor: bool = True
    clues: set[str] = field(default_factory=set)
    hazards: set[str] = field(default_factory=set)
    suspects: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing: str
    phrase: str
    clue: str
    tiny_clue: str
    culprit: str
    hiding_spot: str
    hazard: str
    dodge_verb: str = "dodge"
    enlarge_verb: str = "enlarge"


@dataclass
class Tool:
    id: str
    label: str
    action: str
    helps_with: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        clone = World(self.place)
        import copy
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.lines = []
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "library": Place(
        id="library",
        label="the little library",
        indoor=True,
        clues={"ink", "paper", "tiny-fold"},
        hazards={"shelf-cart"},
        suspects={"owl", "mouse", "tall_reader"},
    ),
    "kitchen": Place(
        id="kitchen",
        label="the sunny kitchen",
        indoor=True,
        clues={"crumb", "spoon", "tiny-print"},
        hazards={"rolling-stool"},
        suspects={"cook", "cat", "baby_brother"},
    ),
    "workshop": Place(
        id="workshop",
        label="the busy workshop",
        indoor=True,
        clues={"dust", "thread", "tiny-scratch"},
        hazards={"tool-tray"},
        suspects={"builder", "sparrow", "helper"},
    ),
}

MYSTERIES = {
    "library": Mystery(
        id="library_case",
        missing="storybook",
        phrase="the velvet storybook",
        clue="a smudge of blue ink",
        tiny_clue="a tiny folded corner",
        culprit="owl",
        hiding_spot="behind the atlas shelf",
        hazard="a rolling shelf cart",
        dodge_verb="dodge",
        enlarge_verb="enlarge",
    ),
    "kitchen": Mystery(
        id="kitchen_case",
        missing="jam_tart",
        phrase="the jam tart on the plate",
        clue="a crumb trail",
        tiny_clue="a tiny spoon mark",
        culprit="cat",
        hiding_spot="under the napkin basket",
        hazard="a rolling stool",
        dodge_verb="dodge",
        enlarge_verb="enlarge",
    ),
    "workshop": Mystery(
        id="workshop_case",
        missing="toy_gear",
        phrase="the bright toy gear",
        clue="a dust streak",
        tiny_clue="a tiny scratch",
        culprit="sparrow",
        hiding_spot="inside the paint tin",
        hazard="a tool tray",
        dodge_verb="dodge",
        enlarge_verb="enlarge",
    ),
}

TOOLS = {
    "magnifier": Tool(id="magnifier", label="a magnifying glass", action="held it over", helps_with="small clues"),
    "lamp": Tool(id="lamp", label="a little lamp", action="shined it on", helps_with="dark corners"),
}

HERO_NAMES = ["Mina", "Owen", "Luna", "Toby", "Ari", "Nia", "Pip", "Sage"]
FRIEND_NAMES = ["Milo", "Ivy", "Noah", "Zara", "Bea", "Kai", "Rose", "Eli"]
TRAITS = ["curious", "gentle", "brave", "quick", "quiet", "smart"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mystery: str
    hero: str
    friend: str
    hero_type: str
    friend_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    return [(place, mystery.id) for place, mystery in MYSTERIES.items() if place in PLACES]


def _check_params(place: str, mystery_id: str) -> None:
    if place not in PLACES:
        raise StoryError(f"(No story: unknown place {place!r}.)")
    if mystery_id not in MYSTERIES:
        raise StoryError(f"(No story: unknown mystery {mystery_id!r}.)")


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def set_up(world: World, hero: Entity, friend: Entity, mystery: Mystery) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    friend.memes["curiosity"] = friend.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.id} and {friend.id} were best friends, and they loved solving little mysteries together."
    )
    world.say(
        f"One day, something was wrong at {world.place.label}: {mystery.phrase} was missing."
    )


def investigate(world: World, hero: Entity, friend: Entity, mystery: Mystery) -> None:
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0) + 1
    friend.memes["teamwork"] = friend.memes.get("teamwork", 0) + 1
    world.say(
        f"{hero.id} looked at the room while {friend.id} asked careful questions."
    )
    world.say(
        f"Together they found {mystery.clue}, but it was so small they could barely see it."
    )
    world.say(
        f"So {friend.id} did not guess too fast; instead, {hero.id} used a magnifying glass to {mystery.enlarge_verb} the clue."
    )


def dodge_hazard(world: World, hero: Entity, friend: Entity, mystery: Mystery) -> None:
    hero.meters["danger"] = hero.meters.get("danger", 0) + 1
    friend.meters["danger"] = friend.meters.get("danger", 0) + 1
    world.say(
        f"On the way, they had to {mystery.dodge_verb} a {mystery.hazard}, but they moved together and stayed safe."
    )


def solve(world: World, hero: Entity, friend: Entity, mystery: Mystery) -> None:
    world.say(
        f"The enlarged clue pointed straight to {mystery.culprit}, hiding {mystery.hiding_spot}."
    )
    world.say(
        f"{hero.id} and {friend.id} found the missing thing, and the mystery was over."
    )
    world.say(
        f"{mystery.culprit.capitalize()} had only been trying to hide it, not keep it forever, so the friends forgave {mystery.culprit}."
    )
    world.say(
        f"In the end, teamwork and friendship made the little whodunit easy to solve."
    )


def tell(place: Place, mystery: Mystery, hero_name: str, friend_name: str,
         hero_type: str = "girl", friend_type: str = "boy", trait: str = "curious") -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={}))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, meters={}, memes={}))
    world.facts.update(place=place, mystery=mystery, hero=hero, friend=friend, trait=trait)

    set_up(world, hero, friend, mystery)
    world.say("They checked the floor, the shelves, and every quiet corner.")
    investigate(world, hero, friend, mystery)
    dodge_hazard(world, hero, friend, mystery)
    solve(world, hero, friend, mystery)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    return [
        f'Write a child-friendly whodunit about {hero.id} and {friend.id} who use teamwork to solve a mystery in {world.place.label}.',
        f'Tell a short story where a tiny clue must be {mystery.enlarge_verb}d and the friends have to {mystery.dodge_verb} one hazard.',
        f'Write a gentle mystery story with friendship, a missing thing, and a happy ending where the culprit is found.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What was missing in {world.place.label}?",
            answer=f"{mystery.phrase} was missing, and that was the problem the friends had to solve.",
        ),
        QAItem(
            question=f"Who solved the mystery together?",
            answer=f"{hero.id} and {friend.id} solved it together by using teamwork and friendship.",
        ),
        QAItem(
            question=f"Why did they use a magnifying glass?",
            answer=f"They used a magnifying glass because {mystery.tiny_clue} was too small to see clearly without enlarging it.",
        ),
        QAItem(
            question=f"What hazard did they {mystery.dodge_verb}?",
            answer=f"They had to {mystery.dodge_verb} {mystery.hazard} while they were investigating.",
        ),
        QAItem(
            question=f"Who had hidden the missing thing?",
            answer=f"The clue led them to {mystery.culprit}, who was hiding it {mystery.hiding_spot}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a magnifying glass do?",
            answer="A magnifying glass makes small things look bigger, so tiny clues are easier to see.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together to reach the same goal.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind bond between people who care about each other and enjoy being together.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place_ok(P) :- place(P).
case_ok(P, M) :- place_ok(P), mystery(P, M), clue_small(M), hazard(P, H), culprit(M, C), hide_spot(M, S).
valid_story(P, M) :- case_ok(P, M).

#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for c in sorted(p.clues):
            lines.append(asp.fact("clue", pid, c))
        for h in sorted(p.hazards):
            lines.append(asp.fact("hazard", pid, h))
        for s in sorted(p.suspects):
            lines.append(asp.fact("suspect", pid, s))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_small", mid))
        lines.append(asp.fact("culprit", mid, m.culprit))
        lines.append(asp.fact("hide_spot", mid, m.hiding_spot))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Sampling / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld about teamwork and friendship.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"], default=None)
    ap.add_argument("--friend-type", choices=["girl", "boy"], default=None)
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
    place = args.place or rng.choice(sorted(PLACES))
    mystery_id = args.mystery or place
    _check_params(place, mystery_id)

    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or ("boy" if hero_type == "girl" else "girl")
    hero = args.name or rng.choice(HERO_NAMES)
    friend = args.friend_name or rng.choice([n for n in FRIEND_NAMES if n != hero])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        mystery=mystery_id,
        hero=hero,
        friend=friend,
        hero_type=hero_type,
        friend_type=friend_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    world = tell(place, mystery, params.hero, params.friend, params.hero_type, params.friend_type, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story Q&A ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World knowledge Q&A ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"  place={world.place.label}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="library", mystery="library", hero="Mina", friend="Milo", hero_type="girl", friend_type="boy", trait="curious"),
    StoryParams(place="kitchen", mystery="kitchen", hero="Owen", friend="Ivy", hero_type="boy", friend_type="girl", trait="smart"),
    StoryParams(place="workshop", mystery="workshop", hero="Luna", friend="Kai", hero_type="girl", friend_type="boy", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible mystery setups:\n")
        for place, mystery in combos:
            print(f"  {place:10} {mystery}")
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
            header = f"### {p.hero} and {p.friend} in {p.place} ({p.mystery})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
