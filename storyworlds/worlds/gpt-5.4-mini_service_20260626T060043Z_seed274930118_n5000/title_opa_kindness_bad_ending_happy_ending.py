#!/usr/bin/env python3
"""
storyworlds/worlds/title_opa_kindness_bad_ending_happy_ending.py
=================================================================

A small whodunit-style story world about kindness, a mistaken bad ending, and a
happy ending that comes from careful clues.

Seed tale:
---
In a quiet house, a child and Opa were getting ready for a small family reading.
Opa could not find the title card for his little book display. The child tried
to help kindly, but the first search went badly and everyone thought the child
had made a mess. Then a few clues pointed to the real culprit, and the family
found the title card in a happy ending.
---

The domain keeps the mystery small on purpose:
- one missing object,
- one suspicious muddy clue,
- one kind helper,
- one false ending,
- one final reveal.

The prose is written to feel a little like a whodunit, but child-friendly.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "opa", "grandpa"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    hiding_places: set[str]
    clues: list[str]
    risk: str


@dataclass
class HelpAction:
    id: str
    verb: str
    gentle_verb: str
    effect: str
    clue: str
    resolves: str
    compatible_with: set[str]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    scene: str = "setup"

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.scene = self.scene
        return clone


SETTINGS = {
    "house": Setting(place="the quiet house", mood="cozy", affords={"search", "explain"}),
    "library": Setting(place="the little library room", mood="still", affords={"search", "explain"}),
    "garden": Setting(place="the back garden", mood="fresh", affords={"search", "explain"}),
}

MYSTERIES = {
    "title_card": Mystery(
        id="title_card",
        label="title card",
        phrase="the little title card for Opa's book display",
        hiding_places={"shelf", "rug", "basket"},
        clues=["paper_dust", "muddy_footprint", "cat_hair"],
        risk="missing",
    ),
    "red_book": Mystery(
        id="red_book",
        label="red book",
        phrase="Opa's red book with a curled corner",
        hiding_places={"chair", "rug", "box"},
        clues=["paper_dust", "torn_thread", "cat_hair"],
        risk="missing",
    ),
    "reading_glasses": Mystery(
        id="reading_glasses",
        label="reading glasses",
        phrase="Opa's reading glasses in their soft case",
        hiding_places={"table", "cushion", "basket"},
        clues=["glint", "dust_smudge", "cat_hair"],
        risk="missing",
    ),
}

HELP = {
    "search_slowly": HelpAction(
        id="search_slowly",
        verb="rush around",
        gentle_verb="search slowly",
        effect="calm",
        clue="notice the little clue trail",
        resolves="found by following the clues",
        compatible_with={"title_card", "red_book", "reading_glasses"},
    ),
    "ask_opa": HelpAction(
        id="ask_opa",
        verb="guess loudly",
        gentle_verb="ask Opa quietly",
        effect="trust",
        clue="remember the last place it was seen",
        resolves="found by listening carefully",
        compatible_with={"title_card", "red_book", "reading_glasses"},
    ),
    "check_cat": HelpAction(
        id="check_cat",
        verb="blame the cat",
        gentle_verb="check under the cat's favorite chair",
        effect="clarity",
        clue="follow the cat hair and tiny prints",
        resolves="found where the cat had been sleeping",
        compatible_with={"title_card", "red_book", "reading_glasses"},
    ),
}

NAMES = ["Mia", "Theo", "Nora", "Leo", "Ava", "Ben", "Zoe", "Mila"]
TRAITS = ["kind", "careful", "curious", "gentle", "brave"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    help_action: str
    name: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for mystery in MYSTERIES:
            for action in HELP:
                if mystery in HELP[action].compatible_with and "search" in SETTINGS[setting].affords:
                    combos.append((setting, mystery, action))
    return combos


def reason_gate(setting: str, mystery: str, action: str) -> bool:
    return (setting, mystery, action) in valid_combos()


def explain_rejection(setting: str, mystery: str, action: str) -> str:
    return (
        f"(No story: {action} does not fit a {mystery} mystery in {setting}. "
        f"Pick a combo where the helper can really follow clues and help solve the case.)"
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    action = HELP[params.help_action]

    world = World(setting=setting)
    child = world.add(Entity(id=params.name, kind="character", type="child", label=params.name,
                             meters={"kindness": 0.0, "worry": 0.0, "relief": 0.0},
                             memes={"kindness": 0.0, "worry": 0.0, "relief": 0.0}))
    opa = world.add(Entity(id="opa", kind="character", type="opa", label="Opa",
                           meters={"worry": 0.0, "hope": 0.0, "relief": 0.0},
                           memes={"worry": 0.0, "hope": 0.0, "relief": 0.0}))
    mystery_ent = world.add(Entity(id=mystery.id, kind="thing", type="thing", label=mystery.label,
                                   phrase=mystery.phrase,
                                   meters={"missing": 1.0, "muddy": 0.0, "found": 0.0}))
    clue = world.add(Entity(id="clue", kind="thing", type="thing", label="clue",
                            phrase="a tiny clue", meters={"seen": 0.0}))

    world.facts.update(child=child, opa=opa, mystery=mystery_ent, action=action, clue=clue)
    return world


def narrate_setup(world: World, params: StoryParams) -> None:
    child = world.get(params.name)
    opa = world.get("opa")
    mystery = world.get(params.mystery)

    world.say(
        f"On a quiet evening in {world.setting.place}, {child.id} was a {params.trait} child who liked to help."
    )
    world.say(
        f"Opa smiled, but then he frowned at the empty spot on the table: "
        f"{mystery.phrase} was gone."
    )
    child.memes["kindness"] += 1
    child.meters["kindness"] += 1
    opa.meters["worry"] += 1
    opa.memes["worry"] += 1
    world.say(
        f"{child.id} said, \"Don't worry, Opa. I'll help find it.\" That kind promise made Opa's face soften a little."
    )


def predict_bump(world: World, params: StoryParams) -> bool:
    sim = world.copy()
    child = sim.get(params.name)
    mystery = sim.get(params.mystery)
    child.meters["worry"] += 0.5
    mystery.meters["found"] += 0.0
    return True


def narrate_bad_ending(world: World, params: StoryParams) -> None:
    child = world.get(params.name)
    opa = world.get("opa")
    mystery = world.get(params.mystery)
    action = HELP[params.help_action]

    world.para()
    world.say(
        f"{child.id} looked under the chair, behind the shelf, and even by the rug."
    )
    world.say(
        f"Then {child.id} reached for the basket and knocked it sideways by accident."
    )
    mystery.meters["muddy"] += 1.0
    child.meters["worry"] += 1.0
    opa.meters["worry"] += 1.0
    child.memes["worry"] += 1.0
    opa.memes["worry"] += 1.0
    world.say(
        f"Brown smudges showed on the floor, and for a moment it looked as if {child.id} had made the whole mystery worse."
    )
    world.say(
        f"Opa looked so sad that this felt like a bad ending, even though {child.id} had only tried to help."
    )
    world.facts["bad_ending"] = True
    world.facts["bad_reason"] = f"{child.id} knocked the basket and left smudges while searching."


def apply_clue(world: World, params: StoryParams) -> None:
    child = world.get(params.name)
    opa = world.get("opa")
    mystery = world.get(params.mystery)
    action = HELP[params.help_action]

    world.para()
    world.say(
        f"Then {child.id} noticed something small and bright: the clue was not the smudge, but the pattern around it."
    )
    world.say(
        f"There were tiny cat hairs on the rug, and the dusty trail pointed toward {mystery.phrase.split(' ')[0]} hidden under the old chair."
    )
    mystery.meters["found"] = 1.0
    mystery.meters["missing"] = 0.0
    world.say(
        f"{child.id} used {action.gentle_verb} instead of guessing, and that careful kindness changed the case."
    )
    opa.memes["hope"] += 1.0
    world.facts["reveal"] = "The cat had dragged the missing item to a hidden spot."
    world.facts["found_by"] = child.id


def narrate_happy_ending(world: World, params: StoryParams) -> None:
    child = world.get(params.name)
    opa = world.get("opa")
    mystery = world.get(params.mystery)

    world.say(
        f"Under the chair, {child.id} found {mystery.phrase} exactly where the clues had pointed."
    )
    world.say(
        f"Opa laughed with relief, thanked {child.id} for being kind, and set the little display straight again."
    )
    world.say(
        f"In the happy ending, {child.id} was still a helpful little detective, and Opa's table looked tidy once more."
    )
    child.meters["relief"] += 1.0
    child.memes["relief"] += 1.0
    opa.meters["relief"] += 1.0
    opa.memes["relief"] += 1.0
    world.facts["happy_ending"] = True


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    narrate_setup(world, params)
    narrate_bad_ending(world, params)
    apply_clue(world, params)
    narrate_happy_ending(world, params)
    return world


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    return [
        f'Write a short whodunit-style story for a child named {params.name} and Opa, using the word "title".',
        f"Tell a gentle mystery where kindness leads to a bad ending first, then a happy ending after clues solve the case.",
        f"Write a small detective story about a missing title card, a worried Opa, and a careful child who finds the truth.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    mystery: Entity = world.facts["mystery"]
    child: Entity = world.facts["child"]
    opa: Entity = world.facts["opa"]
    action: HelpAction = world.facts["action"]

    return [
        QAItem(
            question=f"Who tried to help Opa find the missing {mystery.label}?",
            answer=f"{child.id} tried to help Opa because {child.id} was kind and wanted to make the problem better.",
        ),
        QAItem(
            question="Why did the story have a bad ending for a moment?",
            answer=(
                f"It seemed like a bad ending when {child.id} knocked the basket and left smudges while searching, "
                f"so Opa thought the mystery might be worse."
            ),
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=(
                f"The clue was the trail of cat hairs and dusty marks, which showed that the missing item had been moved "
                f"to a hidden spot instead of being lost forever."
            ),
        ),
        QAItem(
            question="How did kindness help in the end?",
            answer=(
                f"Kindness helped because {child.id} kept searching carefully, stayed gentle with Opa, and "
                f"used {action.gentle_verb} to follow the clues. That led to the happy ending."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery story?",
            answer="A clue is a small piece of information that helps a detective figure out what really happened.",
        ),
        QAItem(
            question="Why do detectives look carefully at tiny details?",
            answer="Detectives look carefully because little details can point to the truth when something seems strange or missing.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring about how someone else feels.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id} ({e.type}) meters={meters} memes={memes}")
    lines.append(f"  scene={world.scene}")
    lines.append(f"  facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


ASP_RULES = r"""
mystery_combo(S, M, A) :- setting(S), mystery(M), help(A), can_search(S), helps(A, M).
bad_then_good(M) :- mystery(M), missing(M), found(M).
kindness_matters(A) :- help(A), gentle(A).
valid_story(S, M, A) :- mystery_combo(S, M, A), kindness_matters(A), bad_then_good(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if "search" in s.affords:
            lines.append(asp.fact("can_search", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid))
        lines.append(asp.fact("found", mid))
        for _clue in m.clues:
            lines.append(asp.fact("clue_for", mid, _clue))
    for aid, a in HELP.items():
        lines.append(asp.fact("help", aid))
        lines.append(asp.fact("gentle", aid))
        for mid in a.compatible_with:
            lines.append(asp.fact("helps", aid, mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


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
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit-style kindness story world with a bad ending and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--help-action", choices=HELP)
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.mystery is None or c[1] == args.mystery)
        and (args.help_action is None or c[2] == args.help_action)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, action = rng.choice(sorted(filtered))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, mystery=mystery, help_action=action, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    world.facts["params"] = params
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


CURATED = [
    StoryParams(setting="house", mystery="title_card", help_action="search_slowly", name="Mia", trait="kind"),
    StoryParams(setting="library", mystery="red_book", help_action="ask_opa", name="Leo", trait="curious"),
    StoryParams(setting="garden", mystery="reading_glasses", help_action="check_cat", name="Nora", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for s, m, a in combos:
            print(f"  {s:8} {m:14} {a}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
