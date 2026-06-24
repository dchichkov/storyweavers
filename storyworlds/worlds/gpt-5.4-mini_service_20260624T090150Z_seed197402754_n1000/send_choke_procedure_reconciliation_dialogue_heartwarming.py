#!/usr/bin/env python3
"""
storyworlds/worlds/send_choke_procedure_reconciliation_dialogue_heartwarming.py
===============================================================================

A small heartwarming storyworld about a child who gets choked up, follows a
kind procedure, sends a note, and reaches reconciliation through dialogue.

Seed premise:
- A child and a sibling/friend have a small hurt feelings problem.
- The child tries to speak, but chokes on the apology.
- A gentle procedure helps them slow down, write, send, and talk.
- Reconciliation happens through dialogue, ending in warmth and repair.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool
    comforts: set[str] = field(default_factory=set)


@dataclass
class Procedure:
    id: str
    label: str
    steps: list[str]
    requires_dialogue: bool = True


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    kind: str
    recipient_role: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone = World(self.place)
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "kitchen": Place(name="the kitchen", indoors=True, comforts={"quiet", "table"}),
    "bedroom": Place(name="the bedroom", indoors=True, comforts={"lamp", "blanket"}),
    "porch": Place(name="the porch", indoors=False, comforts={"breeze"}),
    "garden": Place(name="the garden", indoors=False, comforts={"flowers", "bench"}),
}

PROCEDURES = {
    "breathe_write_send_talk": Procedure(
        id="breathe_write_send_talk",
        label="a gentle apology procedure",
        steps=["breathe", "write", "send", "talk"],
        requires_dialogue=True,
    ),
    "quiet_note_apology": Procedure(
        id="quiet_note_apology",
        label="a quiet note procedure",
        steps=["write", "send", "talk"],
        requires_dialogue=True,
    ),
}

GIFTS = {
    "note": Gift(
        id="note",
        label="note",
        phrase="a small folded note with a heart on it",
        kind="paper_note",
        recipient_role="sibling",
    ),
    "drawing": Gift(
        id="drawing",
        label="drawing",
        phrase="a bright crayon drawing of a sunshine cat",
        kind="drawing",
        recipient_role="friend",
    ),
}

NAMES_GIRL = ["Mia", "Nora", "Lila", "Ava", "Zoe", "Ruby", "Maya"]
NAMES_BOY = ["Noah", "Eli", "Theo", "Finn", "Leo", "Ben", "Owen"]
KINDS = {"girl", "boy", "sister", "brother"}
TRAITS = ["kind", "gentle", "shy", "careful", "warm", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    procedure: str
    gift: str
    hero_name: str
    hero_type: str
    other_name: str
    other_type: str
    trait: str
    seed: Optional[int] = None


class ScenarioError(StoryError):
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming reconciliation through dialogue and a simple procedure.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--procedure", choices=PROCEDURES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--other-name")
    ap.add_argument("--other-type", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(SETTINGS))
    procedure = args.procedure or rng.choice(list(PROCEDURES))
    gift = args.gift or rng.choice(list(GIFTS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    other_type = args.other_type or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(NAMES_GIRL if hero_type == "girl" else NAMES_BOY)
    other_name = args.other_name or rng.choice(NAMES_BOY if other_type == "boy" else NAMES_GIRL)
    if hero_name == other_name:
        other_name = other_name + "y"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, procedure=procedure, gift=gift, hero_name=hero_name,
                       hero_type=hero_type, other_name=other_name, other_type=other_type,
                       trait=trait)


def valid_combo(params: StoryParams) -> bool:
    return params.hero_name != params.other_name and params.procedure in PROCEDURES and params.gift in GIFTS


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for pid in PROCEDURES:
        lines.append(asp.fact("procedure", pid))
    for gid in GIFTS:
        lines.append(asp.fact("gift", gid))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P, PR, G) :- place(P), procedure(PR), gift(G).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params):
        raise ScenarioError("The chosen options do not make a gentle reconciliation story.")
    world = World(SETTINGS[params.place])

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    other = world.add(Entity(id=params.other_name, kind="character", type=params.other_type))
    proc = PROCEDURES[params.procedure]
    gift = GIFTS[params.gift]
    note = world.add(Entity(id="gift", type=gift.kind, label=gift.label, phrase=gift.phrase, owner=hero.id))

    # state
    hero.memes["hurt"] = 1
    hero.memes["want_reconcile"] = 1
    hero.memes["choked_up"] = 1
    other.memes["sad"] = 1

    # Act 1
    world.say(f"{hero.id} and {other.id} had a small hurt feeling at {world.place.name}.")
    world.say(f"{hero.id} wanted to make it right, because {hero.pronoun('subject')} was a {params.trait} child who cared a lot.")
    world.say(f"But when {hero.id} opened {hero.pronoun('possessive')} mouth, the apology got stuck, and {hero.pronoun('subject')} choked on the words.")

    world.para()
    # Act 2
    world.say(f"Then a grown-up showed {hero.id} {proc.label}.")
    if "breathe" in proc.steps:
        hero.memes["calm"] = 1
        world.say(f"First, {hero.id} took a slow breath.")
    if "write" in proc.steps:
        hero.meters["paper"] = 1
        world.say(f"Next, {hero.id} wrote down the sorry words on a little {gift.label}.")
    if "send" in proc.steps:
        note.worn_by = hero.id
        hero.meters["send"] = 1
        world.say(f"Then {hero.id} folded the message, and was ready to send it across the room.")
    if "talk" in proc.steps:
        hero.memes["courage"] = 1
        world.say(f"After that, {hero.id} walked over and used a soft dialogue voice: \"I am sorry.\"")

    world.para()
    # Act 3
    other.memes["softened"] = 1
    hero.memes["reconciliation"] = 1
    other.memes["reconciliation"] = 1
    world.say(f"{other.id} listened, nodded, and said, \"Thank you for telling me.\"")
    world.say(f"Then {other.id} answered with dialogue too: \"I forgive you.\"")
    world.say(f"{hero.id} smiled, and the two children sat together again while the little {gift.label} stayed between them like a warm bridge.")
    world.say(f"By the end, the air at {world.place.name} felt lighter, and their friendship did too.")

    world.facts.update(
        hero=hero,
        other=other,
        procedure=proc,
        gift=gift,
        place=params.place,
        resolved=True,
    )

    prompts = [
        f'Write a short heartwarming story about a child who gets choked up, follows a {proc.label}, sends a note, and makes up with a friend.',
        f"Tell a gentle reconciliation story where {params.hero_name} uses dialogue after a small mistake and a simple send procedure.",
        f'Create a child-friendly story about "{gift.label}", a worried feeling, and a kind ending with reconciliation.',
    ]
    story_qa = [
        QAItem(
            question=f"Why did {params.hero_name} need the procedure at {world.place.name}?",
            answer=(
                f"{params.hero_name} needed it because {hero.pronoun('subject')} was too choked up to say sorry right away. "
                f"The procedure helped {hero.pronoun('object')} breathe, write, send, and talk in a kind way."
            ),
        ),
        QAItem(
            question=f"What did {params.hero_name} send to make things better?",
            answer=f"{params.hero_name} sent {hero.pronoun('possessive')} {gift.label}, which held a gentle apology and helped start the reconciliation.",
        ),
        QAItem(
            question=f"How did {params.other_name} respond to the dialogue?",
            answer=f"{params.other_name} listened carefully, forgave {params.hero_name}, and spoke kindly back, which finished the reconciliation.",
        ),
    ]
    world_qa = [
        QAItem(question="What is a procedure?", answer="A procedure is a set of steps that helps someone do something in a calm and safe order."),
        QAItem(question="What does it mean to be choked up?", answer="Being choked up means feeling so full of emotion that it is hard to speak for a moment."),
        QAItem(question="What is reconciliation?", answer="Reconciliation is when people who had a hurt feeling make peace again."),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.label:
            parts.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "breathe_write_send_talk", "note", "Mia", "girl", "Ben", "boy", "gentle"),
    StoryParams("bedroom", "quiet_note_apology", "drawing", "Noah", "boy", "Ava", "girl", "thoughtful"),
    StoryParams("garden", "breathe_write_send_talk", "note", "Lila", "girl", "Finn", "boy", "careful"),
]


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    found = sorted(set(asp.atoms(model, "valid_story")))
    expected = [(p, pr, g) for p in SETTINGS for pr in PROCEDURES for g in GIFTS]
    if sorted(found) == sorted(expected):
        print(f"OK: ASP matches Python ({len(expected)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("ASP:", found)
    print("PY :", expected)
    return 1


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        for c in combos:
            print(c)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} and {p.other_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
