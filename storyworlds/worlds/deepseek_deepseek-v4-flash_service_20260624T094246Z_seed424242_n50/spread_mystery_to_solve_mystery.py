#!/usr/bin/env python3
"""
storyworlds/worlds/spread_mystery_to_solve_mystery.py
=====================================================

A standalone story world for a child-friendly mystery where clues are spread
across a small neighbourhood. The child must gather clues, interpret them, and
find the hidden object. The narrative follows a clear arc: mystery announced,
search spread across locations, a turning point (misleading clue or dead end),
and a resolution when the object is found.

Initial story (seed):
---
Once upon a time, a little girl named Maya lost her favourite storybook. She
searched everywhere. The first clue was a page left on the bench.
"Maya, look at this page," said her dad. "It must be from your book."
Maya ran to the garden – another clue, a bookmark stuck in the hedge.
"I'm getting closer!" she whispered.
But then she found a wet page near the pond – that was sad. Her dad smiled.
"Let's look together. The last clue is probably near where you read yesterday."
Behind the big oak tree, the book lay safe and dry, waiting for her.
Maya hugged it and said, "I love solving mysteries with you."
---

State-driven model:
- Each clue is a typed entity with a `found` flag and a `location` region.
- The child moves from one location to another; visiting a location yields
  any unfound clue there.
- A dead end occurs when the child visits a location with no clue and the
  remaining clues are far away – the child's frustration rises.
- Finding a clue increases hope and reduces the mystery's "unsolved" meter.
- When all clues are found, the hidden object is revealed at the final
  location.
- The parent can suggest a hint if frustration gets too high.

The "spread" is expressed by distributing clues across up to four locations;
the child must physically visit each location in any order.
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

THRESHOLD = 0.5

# ---------------------------------------------------------------------------
# Entity
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    location: str = ""
    found: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "boy", "child"}:
            personal = {"subject": self.id, "object": self.id, "possessive": self.id + "'s"}
            return personal[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "it"

# ---------------------------------------------------------------------------
# Setting & Registry types
# ---------------------------------------------------------------------------
@dataclass
class Location:
    id: str
    name: str
    children_ok: bool = True

@dataclass
class MysteryProfile:
    id: str
    object_label: str
    object_phrase: str
    clues: list[str]          # short descriptions of clues
    final_location: str       # where the object ends up
    tags: set[str] = field(default_factory=set)

LOCATIONS = [
    Location("bench", "the garden bench"),
    Location("hedge", "the hedge by the fence"),
    Location("pond", "the little pond"),
    Location("oak", "the big oak tree"),
    Location("doorstep", "the front doorstep"),
    Location("sandbox", "the sandbox"),
    Location("garage", "the garage corner"),
]

MYSTERIES = {
    "storybook": MysteryProfile(
        id="storybook",
        object_label="storybook",
        object_phrase="her favourite storybook with dancing rabbits on the cover",
        clues=["a colourful page on the bench",
               "a bookmark tangled in the hedge",
               "a wet page near the pond"],
        final_location="oak",
        tags={"book", "reading"},
    ),
    "blanket": MysteryProfile(
        id="blanket",
        object_label="blanket",
        object_phrase="his soft blue blanket with a star patch",
        clues=["a tiny feather on the doorstep",
               "a piece of blue fuzz on the sandbox edge",
               "a tear of fabric near the garage"],
        final_location="sandbox",
        tags={"blanket", "soft"},
    ),
    "favorite_toy": MysteryProfile(
        id="favorite_toy",
        object_label="toy car",
        object_phrase="his red toy car with shiny wheels",
        clues=["a wheel near the hedge",
               "a streak of red paint on the bench",
               "a tiny keychain under the oak"],
        final_location="garage",
        tags={"car", "toy"},
    ),
}

# Map location ids to a list of clue indices for each mystery.
# This is deterministic given the mystery; we spread clues across selected locations.
def spread_clues(mystery: MysteryProfile, rng: random.Random) -> dict[str, int]:
    """Assign each clue index to a location; final location gets no clue."""
    pool = [loc.id for loc in LOCATIONS if loc.id != mystery.final_location and rng.random() < 0.8]
    rng.shuffle(pool)
    needed = len(mystery.clues)
    if len(pool) < needed:
        pool = [loc.id for loc in LOCATIONS if loc.id != mystery.final_location]
    rng.shuffle(pool)
    assignment = {}
    for i, clue_idx in enumerate(range(needed)):
        assignment[pool[i % len(pool)]] = clue_idx
    return assignment

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
class World:
    def __init__(self, mystery: MysteryProfile, rng: random.Random) -> None:
        self.mystery = mystery
        self.paragraphs: list[list[str]] = [[]]
        self.clue_assign = spread_clues(mystery, rng)
        # entities
        self.child = None
        self.parent = None
        self.hidden_object = None
        self.clue_entities: dict[str, Entity] = {}  # location -> clue entity
        self.visited: set[str] = set()
        self.hints_given = 0
        self.final_revealed = False

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.mystery, random.Random(0))
        clone.paragraphs = [[]]
        clone.clue_assign = dict(self.clue_assign)
        clone.child = copy.deepcopy(self.child)
        clone.parent = copy.deepcopy(self.parent)
        clone.hidden_object = self.hidden_object
        clone.clue_entities = {k: copy.deepcopy(v) for k, v in self.clue_entities.items()}
        clone.visited = set(self.visited)
        clone.hints_given = self.hints_given
        clone.final_revealed = self.final_revealed
        return clone

# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_frustration_on_dead_end(world: World) -> list[str]:
    if world.child and world.child.memes["visit_attempt"] > 0 and world.child.memes["found_clue"] < 1:
        world.child.memes["frustration"] += 0.3
        if world.child.memes["frustration"] >= THRESHOLD and world.child.memes["frustration"] < 1.5:
            return ["(frustration rising)"]
    return []

def _r_hint_on_frustration(world: World) -> list[str]:
    if world.child and world.parent and world.child.memes["frustration"] >= 1.0 and world.hints_given == 0:
        world.hints_given += 1
        return ["(hint offered)"]
    return []

CAUSAL_RULES = [
    Rule("frustration", "social", _r_frustration_on_dead_end),
    Rule("hint", "social", _r_hint_on_frustration),
]

def propagate(world: World, narrate: bool = True) -> list[str]:
    out = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("("))
    if narrate:
        for s in out:
            world.say(s)
    return out

# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, parent: Entity) -> None:
    world.say(f"{child.id} was a {child.type} who loved mysteries. "
              f"Every little thing felt like a clue waiting to be found.")
    world.child = child
    world.parent = parent

def introduce_mystery(world: World, mystery: MysteryProfile, hide_obj: Entity) -> None:
    world.say(f"One morning, {world.child.id} noticed that {mystery.object_phrase} "
              f"was not in its usual spot. It was gone!")
    world.say(f'"{mystery.object_label.title()} is missing!" {world.child.id} said with wide eyes.')
    world.hidden_object = hide_obj

def discover_first_clue(world: World, location_id: str, clue_desc: str) -> None:
    world.say(f"{world.child.id} looked around. On {LOCATIONS[0].name} there was a clue: {clue_desc}.")
    world.say(f'"That must be from {world.hidden_object.label}!" {world.child.id} exclaimed.')
    world.child.memes["hope"] += 0.5
    world.clue_entities[location_id] = Entity(
        id=f"clue_{location_id}", kind="thing", type="clue",
        label=clue_desc, found=True, location=location_id
    )
    world.visited.add(location_id)

def visit_location(world: World, location_id: str) -> Optional[str]:
    """Return a clue description if one is found here, else None."""
    if location_id in world.visited:
        return None  # already been here
    world.visited.add(location_id)
    world.child.memes["visit_attempt"] += 1
    # check if this location has a clue
    for loc, clue_idx in world.clue_assign.items():
        if loc == location_id:
            clue_text = world.mystery.clues[clue_idx]
            world.clue_entities[loc] = Entity(
                id=f"clue_{loc}", kind="thing", type="clue",
                label=clue_text, found=True, location=loc
            )
            world.child.memes["found_clue"] += 1
            world.child.memes["hope"] += 0.3
            return clue_text
    return None

def dead_end(world: World) -> None:
    world.say(f"{world.child.id} searched and searched, but nothing was there. "
              f"Tears started to form. Where could it be?")
    world.child.memes["frustration"] += 0.5

def parent_hint(world: World) -> None:
    loc_ids = [l for l in world.clue_assign if l not in world.visited]
    if not loc_ids:
        return
    hint_loc = random.choice(loc_ids)
    world.say(f'{world.parent.id} put a gentle hand on {world.child.id}\'s shoulder. '
              f'"Maybe we haven\'t looked near {LOCATIONS[0].name} yet?"')
    # reduce frustration
    world.child.memes["frustration"] = max(0, world.child.memes["frustration"] - 0.5)

def find_object(world: World, location_id: str) -> None:
    loc_name = next((l.name for l in LOCATIONS if l.id == location_id), location_id)
    world.say(f"Finally, behind {loc_name}, there it was: {world.hidden_object.phrase} "
              f"waiting safely!")
    world.child.memes["joy"] += 1
    world.final_revealed = True

def celebrate(world: World) -> None:
    world.say(f"{world.child.id} hugged the {world.hidden_object.label} tightly. "
              f'"I love solving mysteries with you," {world.child.id} whispered to {world.parent.id}.')

# ---------------------------------------------------------------------------
# Tell function (full story)
# ---------------------------------------------------------------------------
def tell(mystery_id: str, child_name: str, child_gender: str,
         parent_label: str, seed: int) -> World:
    mystery = MYSTERIES[mystery_id]
    rng = random.Random(seed)
    world = World(mystery, rng)

    child = Entity(id=child_name, kind="character",
                   type=child_gender, traits=["curious", "brave"])
    parent = Entity(id=parent_label if parent_label == "Dad" else "Mom",
                    kind="character", type="parent",
                    label=parent_label)

    hide_obj = Entity(id="hidden_object", kind="thing",
                      type=mystery.object_label,
                      label=mystery.object_label,
                      phrase=mystery.object_phrase)

    introduce(world, child, parent)
    world.para()
    introduce_mystery(world, mystery, hide_obj)

    # Act 2: search – visit locations in a loop
    location_order = list(world.clue_assign.keys())
    location_order.append(mystery.final_location)
    rng.shuffle(location_order)  # spread the search order
    found_count = 0
    world.para()

    for loc in location_order:
        if world.final_revealed:
            break
        if loc == mystery.final_location and found_count < len(mystery.clues):
            continue  # don't go to final until all clues found
        clue = visit_location(world, loc)
        if clue is not None:
            found_count += 1
            world.say(f"Another clue! {clue.capitalize()}.")
            world.child.memes["hope"] += 0.2
        else:
            if not world.final_revealed and found_count < len(mystery.clues):
                dead_end(world)
        propagate(world)
        if world.hints_given > 0 and world.child.memes["frustration"] >= 1.0:
            parent_hint(world)

    # final location
    if not world.final_revealed:
        find_object(world, mystery.final_location)
        celebrate(world)

    world.facts = {
        "child": child,
        "parent": parent,
        "mystery": mystery,
        "hide_obj": hide_obj,
        "clue_count": len(mystery.clues),
        "final_location": mystery.final_location,
        "child_hope": child.memes.get("hope", 0),
        "child_frustration": child.memes.get("frustration", 0),
    }
    return world

# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
CHILD_NAMES = ["Maya", "Leo", "Emma", "Ethan", "Lily", "Sam"]
PARENT_LABELS = ["Dad", "Mom", "Papa", "Mama"]

# Valid mystery + child gender pairings (simple: any gender can play any mystery)
VALID_STORIES = [(mid, g) for mid in MYSTERIES for g in ("girl", "boy")]

def valid_combos() -> list[tuple[str, str]]:
    return VALID_STORIES

# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    mystery: str
    child_name: str
    child_gender: str
    parent_label: str
    seed: Optional[int] = None

# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "book": [("Why is it important to keep books dry?",
              "Books are made of paper, and water makes the paper soggy and tears "
              "easily. Keeping them dry helps them last longer.")],
    "blanket": [("Why might a favourite blanket get lost?",
                 "A blanket can get left behind when you move quickly or if the "
                 "wind carries it. That is why we check the places we visited.")],
    "toy": [("How can we remember where we left a toy?",
             "Putting a toy back in its special box after playing helps us find "
             "it again. Clues like a wheel or a paint mark can also help.")],
}
KNOWLEDGE_ORDER = ["book", "blanket", "toy"]

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = f["child"]
    m = f["mystery"]
    return [
        f'Write a short mystery story for a child about {c.id} searching for a lost '
        f'{m.object_label} with the help of clues spread around the neighbourhood.',
        f'Create a gentle mystery where {c.id} finds {m.object_label} after following '
        f'clues left in different places. Include a moment of doubt and a happy ending.',
        f'A child\'s {m.object_label} is missing. Clues are spread across the yard. '
        f'Tell the story of the search and the final discovery.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    mystery = f["mystery"]
    obj = f["hide_obj"]
    clue_num = f["clue_count"]
    final_loc_name = next((l.name for l in LOCATIONS if l.id == mystery.final_location),
                          mystery.final_location)
    qa = [
        QAItem(
            question=f"What was missing at the beginning of the story?",
            answer=f"{child.id} could not find {obj.phrase}. It was {child.pronoun('possessive')} "
                   f"favourite {obj.label} and it had disappeared.",
        ),
        QAItem(
            question=f"How many clues did {child.id} find?",
            answer=f"{child.id} found {clue_num} clues that were spread around. Each clue "
                   f"brought {child.pronoun('object')} closer to the lost {obj.label}.",
        ),
        QAItem(
            question=f"Where did {child.id} finally find the {obj.label}?",
            answer=f"After following the clues, {child.id} discovered the {obj.label} "
                   f"behind {final_loc_name}. It was safe and waiting.",
        ),
    ]
    # Add a question about feelings if frustration occurred
    if f["child_frustration"] >= 0.5:
        qa.append(QAItem(
            question=f"Did {child.id} ever feel sad or frustrated during the search?",
            answer=f"Yes, when {child.pronoun('subject')} visited a place with no clue, "
                   f"{child.pronoun('subject')} felt frustrated. But {parent.id} helped "
                   f"and {child.pronoun('subject')} kept going.",
        ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = world.mystery.tags
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(q=q, a=a) for q, a in KNOWLEDGE[tag])
    return out

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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    if world.child:
        lines.append(f"  child: {world.child.id} | hope={world.child.memes.get('hope',0):.1f} "
                     f"frustration={world.child.memes.get('frustration',0):.1f}")
    lines.append(f"  clues found: {[k for k,v in world.clue_entities.items() if v.found]}")
    lines.append(f"  visited: {sorted(world.visited)}")
    lines.append(f"  hints given: {world.hints_given}")
    return "\n".join(lines)

CURATED = [
    StoryParams(mystery="storybook", child_name="Maya", child_gender="girl", parent_label="Dad"),
    StoryParams(mystery="blanket", child_name="Leo", child_gender="boy", parent_label="Mom"),
    StoryParams(mystery="favorite_toy", child_name="Emma", child_gender="girl", parent_label="Dad"),
]

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Each mystery has exactly three clues; final location must differ from clue locations.
% We verify that at least one location remains for the final find.
clue_location(Clue_idx, Loc) :- clue_idx(Loc, C), mystery(M), final_loc(M, F), Loc != F.
% A valid story has all clues assigned to distinct locations (spread).
valid_story(M, G) :- mystery(M), child_gender(G), not failure(M).
failure(M) :- mystery(M), clue_count(M, C), {clue_location(_,M,Loc)} < C.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for mid, mp in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_count", mid, len(mp.clues)))
        lines.append(asp.fact("final_loc", mid, mp.final_location))
    for g in ("girl", "boy"):
        lines.append(asp.fact("child_gender", g))
    # Location distribution facts: for each mystery, every clue assigned to some location.
    # We'll use a deterministic assignment for ASP verification: assign in order.
    for mid, mp in MYSTERIES.items():
        locs = [loc.id for loc in LOCATIONS if loc.id != mp.final_location]
        for i, loc in enumerate(locs[:len(mp.clues)]):
            lines.append(asp.fact("clue_idx", loc, i))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH:")
    print(" clingo only:", sorted(clingo_set - python_set))
    print(" python only:", sorted(python_set - clingo_set))
    return 1

# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child solves a mystery by following spread clues.")
    ap.add_argument("--mystery", choices=list(MYSTERIES.keys()))
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--child-name", type=str)
    ap.add_argument("--parent-label", choices=PARENT_LABELS)
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
    combos = valid_combos()
    if args.mystery and args.child_gender and (args.mystery, args.child_gender) not in combos:
        raise StoryError(f"Invalid combination for {args.mystery} and {args.child_gender}.")
    if args.mystery and args.child_gender:
        chosen = (args.mystery, args.child_gender)
    else:
        chosen = rng.choice(combos)
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    parent_label = args.parent_label or rng.choice(PARENT_LABELS)
    return StoryParams(
        mystery=chosen[0],
        child_name=child_name,
        child_gender=chosen[1],
        parent_label=parent_label,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(params.mystery, params.child_name, params.child_gender,
                 params.parent_label, seed=params.seed or 0)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid mystery–gender pairs:")
        for m, g in stories:
            print(f"  {m:12} {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            p.seed = base_seed
            samples.append(generate(p))
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
            header = f"### {p.child_name}: lost {MYSTERIES[p.mystery].object_label}"
        elif len(samples) > 1:
            header = f"### variant {i+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
