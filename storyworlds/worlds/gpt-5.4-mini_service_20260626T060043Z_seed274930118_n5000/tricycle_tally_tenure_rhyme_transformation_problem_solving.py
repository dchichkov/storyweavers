#!/usr/bin/env python3
"""
A tiny pirate-tale storyworld about a tricycle, a tally, and a new tenure.

Premise:
A young deckhand loves riding a tricycle on the dock while keeping a tally of
ship chores. The ship's quartermaster has just begun a new tenure and wants the
dock neat. Trouble comes when the tally goes missing and the tricycle wheel
snags a loose rope.

Turn:
The deckhand must solve the problem without tossing the tally overboard. A
rhyming clue points to where the rope got caught.

Resolution:
The deckhand transforms the tricycle into a safer cart by fitting a sturdier
wheel guard, finds the tally, and helps the quartermaster finish the day with
a clean deck and a better count.

This file is a standalone Storyweavers world script.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"tension": 0.0, "mess": 0.0, "care": 0.0, "order": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "worry": 0.0, "pride": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain", "quartermaster"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "deckhand"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "dock": "the dock by the harbor",
    "ship": "the ship's main deck",
    "cove": "the quiet cove",
}

ACTIONS = {
    "ride": {
        "verb": "ride the tricycle",
        "gerund": "riding the tricycle",
        "rush": "pedal hard across the planks",
        "mess": "scraped",
        "soil": "scratched and wobbly",
        "keyword": "tricycle",
    },
    "count": {
        "verb": "keep a tally",
        "gerund": "counting crates",
        "rush": "scoop up the tally board",
        "mess": "scattered",
        "soil": "lost in the rush",
        "keyword": "tally",
    },
}

TRANSFORMS = {
    "guard": {
        "label": "a wheel guard",
        "prep": "fit a wheel guard on the tricycle",
        "result": "safer for the dock",
    },
    "cart": {
        "label": "a little cart",
        "prep": "turn the tricycle into a little cart",
        "result": "steady and useful",
    },
}

BEATS = {
    "rhyme": [
        ("If the wheel goes squeak in the sea-salt breeze, "
         "then look where the rope hides under the knees.",
         "The rhyme hinted that the snag was under the low rope coil by the dock edge."),
        ("When planks go thunk and the tally goes thin, "
         "peek by the barrels where the shadows begin.",
         "The rhyme pointed the deckhand toward the barrel shadows, where the tally board had slipped."),
    ]
}


@dataclass
class StoryParams:
    setting: str
    action: str
    transform: str
    name: str
    tenure_holder: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(setting: str, action: str, transform: str) -> bool:
    return setting in SETTINGS and action in ACTIONS and transform in TRANSFORMS


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, a, t) for s in SETTINGS for a in ACTIONS for t in TRANSFORMS]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(dock). setting(ship). setting(cove).
action(ride). action(count).
transform(guard). transform(cart).

valid(S,A,T) :- setting(S), action(A), transform(T).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    for t in TRANSFORMS:
        lines.append(asp.fact("transform", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def _r_tally(world: World) -> list[str]:
    out = []
    deckhand = world.get("Deckhand")
    tally = world.get("Tally")
    if deckhand.memes["worry"] < THRESHOLD:
        return out
    sig = ("tally_missing",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tally.meters["mess"] += 1
    world.say("The tally board slipped under the barrels, and the count was gone.")
    return out


def _r_transform(world: World) -> list[str]:
    out = []
    trike = world.get("Tricycle")
    if trike.meters["mess"] < THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    trike.meters["order"] += 1
    trike.memes["hope"] += 1
    world.say("With a quick fix, the tricycle changed from wobbly trouble to steady helper.")
    return out


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in (_r_tally, _r_transform):
            before = len(world.fired)
            rule(world)
            if len(world.fired) != before:
                changed = True


def rhyme_clue(action: str) -> tuple[str, str]:
    if action == "ride":
        return BEATS["rhyme"][0]
    return BEATS["rhyme"][1]


def tell(setting: str, action: str, transform: str, name: str, tenure_holder: str) -> World:
    world = World(SETTINGS[setting])

    deckhand = world.add(Entity(
        id="Deckhand",
        kind="character",
        type="boy",
        label=name,
    ))
    quartermaster = world.add(Entity(
        id="Quartermaster",
        kind="character",
        type="quartermaster",
        label=tenure_holder,
    ))
    trike = world.add(Entity(
        id="Tricycle",
        type="tricycle",
        label="the tricycle",
        phrase="a bright red tricycle with brass bells",
        owner=deckhand.id,
    ))
    tally = world.add(Entity(
        id="Tally",
        type="tally",
        label="the tally board",
        phrase="a small tally board with chalk marks",
        owner=quartermaster.id,
        caretaker=quartermaster.id,
    ))

    # Act I
    world.say(f"{name} was a nimble deckhand who loved the dock and the salt wind.")
    world.say(f"{name} kept {tally.label} near {quartermaster.pronoun('possessive')} chair and loved {ACTIONS[action]['gerund']}.")
    world.say(f"Under {quartermaster.label}'s new tenure, every crate and rope had to stay neat.")

    # Act II
    world.para()
    world.say(f"One bright tide day, {name} tried to {ACTIONS[action]['verb']} near the stacked barrels.")
    world.get("Deckhand").memes["worry"] += 1
    world.get("Tricycle").meters["mess"] += 1
    world.say("Then the front wheel snagged a loose rope, and the tally board skittered out of sight.")
    clue, explain = rhyme_clue(action)
    world.say(f"{name} muttered a little rhyme: \"{clue}\"")
    world.say(explain)

    # Act III
    world.para()
    if transform == "guard":
        world.say(f"{name} solved the trouble by deciding to {TRANSFORMS[transform]['prep']}.")
    else:
        world.say(f"{name} solved the trouble by deciding to {TRANSFORMS[transform]['prep']}.")
    world.get("Tricycle").meters["order"] += 1
    world.get("Deckhand").memes["hope"] += 1
    world.say(f"The new setup made the tricycle {TRANSFORMS[transform]['result']}.")
    world.say("Then the deckhand found the tally behind the barrels and handed it back to the quartermaster.")
    world.get("Quartermaster").memes["pride"] += 1
    world.get("Quartermaster").memes["relief"] += 1
    world.say(f"With the count restored, {quartermaster.label} smiled, and the deck shone shipshape again.")

    world.facts.update(
        deckhand=deckhand,
        quartermaster=quartermaster,
        tricycle=trike,
        tally=tally,
        setting=setting,
        action=action,
        transform=transform,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short pirate tale for a child about a tricycle, a tally, and a problem that needs solving.',
        f"Tell a gentle pirate story where {f['deckhand'].label} rides a tricycle, loses a tally, and fixes the trouble.",
        f"Write a story with a rhyme clue and a transformation that helps {f['quartermaster'].label} during a new tenure.",
    ]


def story_qa(world: World) -> list[QAItem]:
    d = world.facts["deckhand"]
    q = world.facts["quartermaster"]
    action = world.facts["action"]
    transform = world.facts["transform"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {d.label}, a deckhand who loved {ACTIONS[action]['gerund']} near the harbor.",
        ),
        QAItem(
            question=f"What problem did {d.label} have on the dock?",
            answer="The tricycle's wheel snagged a loose rope, and the tally board slipped away under the barrels.",
        ),
        QAItem(
            question=f"How did {d.label} solve the problem?",
            answer=f"{d.label} used a clever {transform} idea, which made the tricycle steadier and helped find the tally.",
        ),
        QAItem(
            question=f"Why did {q.label} care about the count?",
            answer=f"{q.label} was serving a new tenure and wanted the dock neat, counted, and ready for work.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tricycle?",
            answer="A tricycle is a small three-wheeled ride, and its extra wheel can make it steadier than a bicycle.",
        ),
        QAItem(
            question="What is a tally?",
            answer="A tally is a way to keep count, often by marking numbers or checking items one by one.",
        ),
        QAItem(
            question="What does tenure mean?",
            answer="Tenure means a period of time when someone holds a job or role, like a captain or quartermaster serving for a while.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== prompts ==")
    lines.extend(f"- {p}" for p in sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {e.label!r} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    action: str
    transform: str
    name: str
    tenure_holder: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld: tricycle, tally, tenure.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--action", choices=sorted(ACTIONS))
    ap.add_argument("--transform", choices=sorted(TRANSFORMS))
    ap.add_argument("--name")
    ap.add_argument("--tenure-holder")
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


NAMES = ["Finn", "Mira", "Jory", "Nell", "Pip", "Ari"]
TENURE_HOLDERS = ["Captain Vale", "Quartermaster Rook", "Old Maris"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting and args.action and args.transform:
        if not valid_combo(args.setting, args.action, args.transform):
            raise StoryError("Invalid setting/action/transform combination.")
    choices = [c for c in combos
               if (args.setting is None or c[0] == args.setting)
               and (args.action is None or c[1] == args.action)
               and (args.transform is None or c[2] == args.transform)]
    if not choices:
        raise StoryError("No valid combination matches the given options.")
    setting, action, transform = rng.choice(choices)
    return StoryParams(
        setting=setting,
        action=action,
        transform=transform,
        name=args.name or rng.choice(NAMES),
        tenure_holder=args.tenure_holder or rng.choice(TENURE_HOLDERS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params.setting, params.action, params.transform, params.name, params.tenure_holder)
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


# ---------------------------------------------------------------------------
# ASP wrappers
# ---------------------------------------------------------------------------

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="dock", action="ride", transform="guard", name="Finn", tenure_holder="Quartermaster Rook"),
    StoryParams(setting="ship", action="count", transform="cart", name="Mira", tenure_holder="Captain Vale"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
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
