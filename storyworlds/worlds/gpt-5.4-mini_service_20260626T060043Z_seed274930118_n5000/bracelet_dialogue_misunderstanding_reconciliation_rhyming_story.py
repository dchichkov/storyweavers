#!/usr/bin/env python3
"""
storyworlds/worlds/bracelet_dialogue_misunderstanding_reconciliation_rhyming_story.py
=====================================================================================

A small story world for a rhyming, dialogue-driven tale about a bracelet,
a misunderstanding, and a warm reconciliation.

Premise:
- A child treasures a bracelet.
- Another character misunderstands what the bracelet is for.
- A brief argument follows.
- A kind explanation fixes the mix-up.
- The ending proves the relationship is repaired.

This world models a few physical meters and emotional memes:
- bracelet: kept safe, worn, or misplaced
- sparkle / break risk / worry: physical and emotional tension
- confusion / hurt / apology / trust / joy: emotional beats

The generated prose is intentionally child-facing and lightly rhyming.
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
# Registry content
# ---------------------------------------------------------------------------
NAMES = {
    "girl": ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella"],
    "boy": ["Leo", "Max", "Ben", "Finn", "Theo", "Jack"],
}
ADULTS = ["mom", "dad", "aunt", "uncle", "grandma", "grandpa"]
SETTINGS = {
    "bedroom": "the bedroom",
    "garden": "the garden",
    "kitchen": "the kitchen",
    "porch": "the porch",
    "playroom": "the playroom",
}
BRACELETS = {
    "bead": "a bright bead bracelet",
    "shell": "a little shell bracelet",
    "friendship": "a woven friendship bracelet",
    "gold": "a shiny gold bracelet",
    "rainbow": "a rainbow string bracelet",
}
ACTIVITIES = {
    "painting": "painting with color and cheer",
    "baking": "mixing and whisking with great delight",
    "playing": "playing and spinning in afternoon light",
    "reading": "reading a book in a cozy nook",
    "gardening": "watering sprouts with muddy boots",
}


# ---------------------------------------------------------------------------
# Shared world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom", "aunt", "grandma"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad", "uncle", "grandpa"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    setting: str
    bracelet: str
    child_name: str
    child_gender: str
    adult_role: str
    activity: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------
def _rhyming_line(a: str, b: str) -> str:
    return f"{a} {b}"


def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])

    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.child_gender,
        label=params.child_name,
        owner=params.child_name,
        meters={"care": 1.0},
        memes={"joy": 1.0, "trust": 1.0},
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=params.adult_role,
        label=params.adult_role,
        meters={"care": 1.0},
        memes={"care": 1.0, "worry": 0.0},
    ))
    bracelet = world.add(Entity(
        id="bracelet",
        kind="thing",
        type="bracelet",
        label="bracelet",
        phrase=BRACELETS[params.bracelet],
        owner=child.id,
        caretaker=adult.id,
        worn_by=child.id,
        meters={"safe": 1.0, "sparkle": 1.0},
        memes={"precious": 1.0},
    ))

    world.facts.update(
        child=child,
        adult=adult,
        bracelet=bracelet,
        params=params,
    )
    return world


def tell_story(world: World) -> None:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    adult: Entity = world.facts["adult"]  # type: ignore[assignment]
    bracelet: Entity = world.facts["bracelet"]  # type: ignore[assignment]
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]

    act = ACTIVITIES[params.activity]
    setting = world.place

    # Act 1: setup
    world.say(
        f"In {setting}, {child.label} wore {bracelet.phrase} with a happy little glow; "
        f"it jingled like tinsel wherever they’d go."
    )
    world.say(
        f"{child.label} loved {act}; the day felt bright and light, "
        f"and the bracelet sparkled soft and white."
    )

    # Act 2: misunderstanding
    world.para()
    bracelet.memes["wanted"] = 1.0
    adult.memes["worry"] += 1.0
    child.memes["confusion"] = 0.5

    if params.activity in {"painting", "gardening", "baking"}:
        adult.say = None

    world.say(
        f"Then {adult.label} said, “That bracelet should stay off during play; "
        f"it may get lost or scratched away.”"
    )
    world.say(
        f"{child.label} frowned and said, “But it’s mine, and it makes me gleam; "
        f"I only want to wear my dream!”"
    )

    child.memes["hurt"] = child.memes.get("hurt", 0.0) + 1.0
    adult.memes["worry"] += 1.0
    bracelet.meters["safe"] = 0.5

    world.say(
        f"The words sounded sharp; the moment felt tight, "
        f"like a cloud over sunshine in the middle of light."
    )

    # Act 3: reconciliation
    world.para()
    adult.memes["apology"] = 1.0
    child.memes["trust"] += 0.5

    world.say(
        f"{adult.label} took a breath and spoke with care: "
        f'“I wasn’t trying to be mean, I swear.”'
    )
    world.say(
        f'“I worried it might slip or snag on the way; '
        f'let’s keep it safe and still enjoy the day.”'
    )
    world.say(
        f"{child.label} looked up and gave a small grin bright; "
        f'“Oh! You meant safe, not no-bracelet tonight.”'
    )

    adult.memes["worry"] = max(0.0, adult.memes["worry"] - 1.0)
    child.memes["hurt"] = 0.0
    child.memes["confusion"] = 0.0
    child.memes["joy"] += 1.0
    child.memes["trust"] += 1.0
    bracelet.meters["safe"] = 1.0

    world.say(
        f"So {child.label} wore the bracelet with pride, "
        f"and {adult.label} stayed near their side."
    )
    world.say(
        f"They shared a smile, all soft and true; "
        f"the mix-up was mended, and love shone through."
    )

    world.facts["resolved"] = True
    world.facts["setting_name"] = setting
    world.facts["activity_text"] = act


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    return [
        f'Write a short rhyming story about a child named {params.child_name}, '
        f"a bracelet, and a misunderstanding that ends in reconciliation.",
        f"Tell a gentle story set in {SETTINGS[params.setting]} where "
        f"{params.child_name} wants to keep a bracelet on during {ACTIVITIES[params.activity]}.",
        "Write a child-friendly dialogue story where a worried adult and a child "
        "first disagree, then make up kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    adult: Entity = world.facts["adult"]  # type: ignore[assignment]
    bracelet: Entity = world.facts["bracelet"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"Who wore the bracelet in the story?",
            answer=f"{child.label} wore the bracelet at first, because it was theirs and they loved it.",
        ),
        QAItem(
            question=f"Why did {adult.label} worry about the bracelet?",
            answer=(
                f"{adult.label} worried the bracelet might get scratched, snagged, or lost during "
                f"{ACTIVITIES[params.activity]}, so they asked to keep it safe."
            ),
        ),
        QAItem(
            question="What fixed the misunderstanding?",
            answer=(
                f"A calm apology and a clear explanation fixed it. {adult.label} explained they wanted "
                f"to protect the bracelet, not take it away, and then they agreed to keep it safe."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended with {child.label} smiling again, the bracelet safe and shiny, and both of them "
                f"feeling close and happy."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bracelet?",
            answer=(
                "A bracelet is a small piece of jewelry or decoration that you wear around your wrist."
            ),
        ),
        QAItem(
            question="Why do people sometimes take off jewelry for play?",
            answer=(
                "People sometimes take off jewelry for play so it does not get scratched, broken, or lost."
            ),
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer=(
                "A misunderstanding happens when someone thinks the other person means one thing, but they meant something else."
            ),
        ),
        QAItem(
            question="What is reconciliation?",
            answer=(
                "Reconciliation is when people make up after a disagreement and feel friendly again."
            ),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:10}) meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/4.

valid(S, B, A, G) :- setting(S), bracelet(B), activity(A), gender(G).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for key in SETTINGS:
        lines.append(asp.fact("setting", key))
    for key in BRACELETS:
        lines.append(asp.fact("bracelet", key))
    for key in ACTIVITIES:
        lines.append(asp.fact("activity", key))
    for key in NAMES:
        lines.append(asp.fact("gender", key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    got = set(asp.atoms(model, "valid"))
    want = {
        (s, b, a, g)
        for s in SETTINGS
        for b in BRACELETS
        for a in ACTIVITIES
        for g in NAMES
    }
    if got == want:
        print(f"OK: clingo gate matches Python registry space ({len(got)} combos).")
        return 0
    print("MISMATCH between clingo and Python registry space:")
    if got - want:
        print("  only in clingo:", sorted(got - want))
    if want - got:
        print("  only in python:", sorted(want - got))
    return 1


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming bracelet story with dialogue, misunderstanding, and reconciliation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--bracelet", choices=BRACELETS)
    ap.add_argument("--name", choices=sorted({n for vals in NAMES.values() for n in vals}))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=ADULTS)
    ap.add_argument("--activity", choices=ACTIVITIES)
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
    bracelet = args.bracelet or rng.choice(list(BRACELETS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    adult = args.adult or rng.choice(ADULTS)
    activity = args.activity or rng.choice(list(ACTIVITIES))

    if args.name and not args.gender:
        if args.name in NAMES["girl"]:
            gender = "girl"
        elif args.name in NAMES["boy"]:
            gender = "boy"
    if args.gender and args.name:
        if args.gender == "girl" and args.name not in NAMES["girl"]:
            raise StoryError("That name does not fit the requested gender in this world.")
        if args.gender == "boy" and args.name not in NAMES["boy"]:
            raise StoryError("That name does not fit the requested gender in this world.")

    return StoryParams(
        setting=setting,
        bracelet=bracelet,
        child_name=name,
        child_gender=gender,
        adult_role=adult,
        activity=activity,
    )


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell_story(world)
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
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/4."))
        atoms = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(atoms)} compatible registry combos:")
        for atom in atoms[:100]:
            print(" ", atom)
        if len(atoms) > 100:
            print(f"... {len(atoms) - 100} more")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("bedroom", "friendship", "Mia", "girl", "mom", "reading"),
            StoryParams("garden", "bead", "Leo", "boy", "dad", "gardening"),
            StoryParams("kitchen", "gold", "Ava", "girl", "aunt", "baking"),
            StoryParams("porch", "shell", "Ben", "boy", "grandma", "playing"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
