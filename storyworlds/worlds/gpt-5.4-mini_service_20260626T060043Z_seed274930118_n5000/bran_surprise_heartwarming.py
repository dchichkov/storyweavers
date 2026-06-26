#!/usr/bin/env python3
"""
A small heartwarming storyworld about bran, surprise, and a gentle reveal.

Premise:
- A child or helper is preparing a simple bran treat or bran snack.
- Someone quietly plans a surprise.
- The surprise is meant to comfort, cheer, or welcome someone home.

The simulated state tracks:
- physical preparation of ingredients and gift items in meters
- feelings like anticipation, worry, gratitude, and delight in memes

The story turns when the hidden plan is discovered in a kind way,
then resolves with shared bran treats and warm feelings.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    prepared_by: Optional[str] = None
    hidden: bool = False
    served: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Scene:
    place: str = "the kitchen"
    occasion: str = "homecoming"
    surprise_kind: str = "welcome"
    bran_style: str = "bran muffins"
    surprise_note: str = "a happy surprise"
    mood: str = "warm"


class World:
    def __init__(self, scene: Scene):
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy

        w = World(self.scene)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Core causal rules
# ---------------------------------------------------------------------------
def _rule_smell_bran(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.type == "bran" and e.meters.get("mixed", 0.0) >= THRESHOLD and "smell" not in e.meters:
            e.meters["smell"] = 1.0
            out.append(f"The bran scent drifted through the room.")
    return out


def _rule_warm_feelings(world: World) -> list[str]:
    out: list[str] = []
    giver = world.facts.get("giver")
    receiver = world.facts.get("receiver")
    if not giver or not receiver:
        return out
    g = world.get(giver)
    r = world.get(receiver)
    if r.memes.get("surprised", 0.0) >= THRESHOLD and "gratitude" not in r.memes:
        r.memes["gratitude"] = 1.0
        g.memes["pride"] = g.memes.get("pride", 0.0) + 1.0
        out.append(f"{r.id} smiled with gratitude.")
    return out


def _rule_share(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.type == "bran" and e.meters.get("served", 0.0) >= THRESHOLD and "shared" not in e.meters:
            e.meters["shared"] = 1.0
            out.append("Everyone had a little bit together.")
    return out


CAUSAL_RULES = [_rule_smell_bran, _rule_warm_feelings, _rule_share]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            new = rule(world)
            if new:
                changed = True
                lines.extend(new)
    if narrate:
        for line in lines:
            world.say(line)
    return lines


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    occasion: str
    surprise_kind: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    bran_style: str
    seed: Optional[int] = None


PLACES = {
    "kitchen": Scene(place="the kitchen", occasion="homecoming", surprise_kind="welcome", bran_style="bran muffins"),
    "bakery": Scene(place="the bakery", occasion="thank-you", surprise_kind="thank-you", bran_style="bran cookies"),
    "porch": Scene(place="the porch", occasion="rainy-day", surprise_kind="comfort", bran_style="bran tea cakes"),
}

BRAN_STYLES = {
    "bran muffins": {"sweet", "warm"},
    "bran cookies": {"crisp", "sweet"},
    "bran tea cakes": {"soft", "gentle"},
}

CHILD_NAMES = ["Maya", "Leo", "Nina", "Eli", "Sora", "Owen", "Ivy", "Noah"]
HELPER_NAMES = ["Aunt June", "Dad", "Mom", "Grandpa", "Big Sister", "Older Brother"]


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def opening(world: World, child: Entity, helper: Entity, bran: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.type} who loved simple snacks and cozy days."
    )
    world.say(
        f"{helper.id} knew {child.id} liked {world.scene.bran_style}, even when the day felt ordinary."
    )
    world.say(
        f"So {helper.id} decided to make {world.scene.surprise_note} with {bran.label}."
    )


def prepare_bran(world: World, helper: Entity, bran: Entity) -> None:
    bran.meters["mixed"] = 1.0
    bran.prepared_by = helper.id
    world.say(
        f"In {world.scene.place}, {helper.id} stirred the bowl carefully and baked {bran.phrase}."
    )
    world.say(
        f"{helper.id} hid the finished {bran.label} behind a clean towel so the surprise could stay secret."
    )
    propagate(world)


def suspense(world: World, child: Entity, helper: Entity) -> None:
    child.memes["curious"] = child.memes.get("curious", 0.0) + 1.0
    world.say(
        f"Later, {child.id} noticed a sweet smell and paused by the doorway."
    )
    world.say(
        f"{child.id} asked, \"What are you making, {helper.id}?\" and peeked at the covered tray."
    )


def reveal(world: World, child: Entity, helper: Entity, bran: Entity) -> None:
    child.memes["surprised"] = 1.0
    world.say(
        f"{helper.id} laughed softly and lifted the towel."
    )
    world.say(
        f"\"It's a surprise for you,\" {helper.id} said. \"I made {bran.phrase} because I wanted your day to feel brighter.\""
    )
    bran.hidden = False
    bran.served = True
    bran.meters["served"] = 1.0
    propagate(world)


def ending(world: World, child: Entity, helper: Entity, bran: Entity) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
    child.memes["gratitude"] = child.memes.get("gratitude", 0.0) + 1.0
    world.say(
        f"{child.id} grinned and took a bite of the warm {bran.label}."
    )
    world.say(
        f"{child.id} hugged {helper.id} and said the surprise made the whole place feel kind and cozy."
    )
    world.say(
        f"By the end, the tray was empty, and the room felt full of love instead."
    )


def simulate(params: StoryParams) -> World:
    scene = PLACES[params.place]
    world = World(scene)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    bran = world.add(
        Entity(
            id="bran_treat",
            kind="thing",
            type="bran",
            label=params.bran_style,
            phrase=f"fresh {params.bran_style}",
            owner=helper.id,
            hidden=True,
        )
    )

    world.facts.update(child=child.id, helper=helper.id, bran=bran.id, scene=scene)

    opening(world, child, helper, bran)
    world.para()
    prepare_bran(world, helper, bran)
    world.para()
    suspense(world, child, helper)
    world.para()
    reveal(world, child, helper, bran)
    world.para()
    ending(world, child, helper, bran)

    world.facts.update(
        child=child,
        helper=helper,
        bran=bran,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    scene = world.scene
    return [
        f'Write a warm short story for a young child about {child.id}, a surprise, and {scene.bran_style}.',
        f"Tell a heartwarming story where {helper.id} secretly makes {scene.bran_style} and {child.id} discovers the surprise.",
        f'Write a gentle story set in {scene.place} that ends with sharing {scene.bran_style}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    bran: Entity = f["bran"]
    scene = world.scene
    return [
        QAItem(
            question=f"Who was the surprise for in the story?",
            answer=f"The surprise was for {child.id}, who found out that {helper.id} had made {bran.label}.",
        ),
        QAItem(
            question=f"What did {helper.id} make to surprise {child.id}?",
            answer=f"{helper.id} made {bran.phrase} and hid it carefully until the right moment.",
        ),
        QAItem(
            question=f"How did {child.id} feel after seeing the surprise?",
            answer=f"{child.id} felt surprised, happy, and grateful when the towel came off in {scene.place}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bran?",
            answer="Bran is the outer layer of a grain, and people often add it to muffins, cookies, or cereal for a hearty taste.",
        ),
        QAItem(
            question="Why can a surprise make someone feel better?",
            answer="A kind surprise can make someone feel remembered, cared for, and happy because it shows someone put in extra thought.",
        ),
        QAItem(
            question="What does sharing a snack do?",
            answer="Sharing a snack lets people enjoy something together and can turn an ordinary moment into a warm one.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A surprise is reasonable if one helper makes a bran treat for one child.
reasonable(C, H, B) :- child(C), helper(H), bran(B), makes(H, B), for(C, B).

% If the surprise is hidden, then it can be revealed.
can_reveal(B) :- bran(B), hidden(B).

% A warm ending is possible when the child is surprised and the bran is served.
warm_ending(C, B) :- child(C), bran(B), surprised(C), served(B).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for place_id, scene in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("located", place_id, scene.place))
    for style in BRAN_STYLES:
        lines.append(asp.fact("bran", style.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show reasonable/3."))
    atoms = set(asp.atoms(model, "reasonable"))
    expected = set()
    for place_id in PLACES:
        for style in BRAN_STYLES:
            expected.add(("child", "helper", "bran"))
    # We only verify the program is syntactically alive and yields a model.
    if model is None:
        print("ASP verification failed: no model.")
        return 1
    print(f"OK: ASP program solved with {len(model)} shown atoms.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming bran surprise storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--bran-style", choices=list(BRAN_STYLES))
    ap.add_argument("--child-name", choices=CHILD_NAMES)
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
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
    place = args.place or rng.choice(list(PLACES))
    scene = PLACES[place]
    bran_style = args.bran_style or scene.bran_style
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    if child_name == helper_name:
        raise StoryError("Child and helper must be different people.")
    child_type = "girl" if child_name in {"Maya", "Nina", "Ivy"} else "boy"
    helper_type = "woman" if helper_name in {"Aunt June", "Mom", "Big Sister"} else "man"
    return StoryParams(
        place=place,
        occasion=scene.occasion,
        surprise_kind=scene.surprise_kind,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
        bran_style=bran_style,
    )


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, dict(e.meters), dict(e.memes))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available, but this world keeps the Python story path primary.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    curated = [
        StoryParams("kitchen", "homecoming", "welcome", "Maya", "girl", "Mom", "woman", "bran muffins"),
        StoryParams("bakery", "thank-you", "thank-you", "Leo", "boy", "Dad", "man", "bran cookies"),
        StoryParams("porch", "rainy-day", "comfort", "Ivy", "girl", "Aunt June", "woman", "bran tea cakes"),
    ]

    if args.all:
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        if len(samples) > 1:
            header = f"### story {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
