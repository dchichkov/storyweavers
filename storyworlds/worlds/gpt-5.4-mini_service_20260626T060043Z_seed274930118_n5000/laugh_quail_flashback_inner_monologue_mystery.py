#!/usr/bin/env python3
"""
storyworlds/worlds/laugh_quail_flashback_inner_monologue_mystery.py
====================================================================

A small mystery storyworld built from the seed words "laugh" and "quail", with
flashback and inner monologue as narrative instruments.

Premise:
- A child notices something strange at a quiet place.
- A small missing object, a startled quail, and a clue lead to a gentle mystery.
- A flashback explains the clue, and an inner monologue shows the detective turn.
- The ending reveals what was really happening and changes the emotional state.
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

PLACES = {
    "garden": {"label": "the garden", "detail": "The garden was quiet, with beans climbing a fence and a small path of pebbles."},
    "orchard": {"label": "the orchard", "detail": "The orchard was still, with low branches and soft grass under the trees."},
    "pond": {"label": "the pond", "detail": "The pond sat like a dark mirror, with reeds, stones, and a few muddy tracks."},
    "barn": {"label": "the barnyard", "detail": "The barnyard was busy with straw, old crates, and a gate that never quite latched."},
}

MISSING_THINGS = {
    "button": {"label": "button", "phrase": "a bright brass button", "place": "pocket"},
    "key": {"label": "key", "phrase": "a small iron key", "place": "hook"},
    "hat": {"label": "hat", "phrase": "a floppy straw hat", "place": "bench"},
    "ribbon": {"label": "ribbon", "phrase": "a blue ribbon", "place": "branch"},
}

CLUES = {
    "feather": {"label": "feather", "phrase": "a downy feather", "meaning": "a quail had been close by"},
    "footprint": {"label": "footprint", "phrase": "tiny three-toed tracks", "meaning": "something small and quick had passed through"},
    "rustle": {"label": "rustle", "phrase": "a rustle in the grass", "meaning": "something was hiding in the weeds"},
}

NAMES = ["Mina", "Toby", "Leah", "Nico", "Pia", "Hugo", "Ada", "June"]
TRAITS = ["curious", "careful", "bright-eyed", "thoughtful", "quiet", "brave"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    revealed: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    place: str
    child: Entity
    adult: Entity
    missing: Entity
    clue: Entity
    quail: Entity
    heard_laugh: bool = False
    flashback_done: bool = False
    solved: bool = False
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def make_world(place_key: str, name: str, trait: str, missing_key: str, seed: Optional[int] = None) -> World:
    place = PLACES[place_key]
    child = Entity(id=name, kind="character", type="child", label=name, memes={"curiosity": 1.0, "worry": 0.0, "relief": 0.0})
    adult = Entity(id="grownup", kind="character", type="adult", label="the grown-up")
    missing_cfg = MISSING_THINGS[missing_key]
    missing = Entity(id="missing", type=missing_cfg["label"], label=missing_cfg["label"], phrase=missing_cfg["phrase"], owner=name, location=missing_cfg["place"])
    clue = Entity(id="clue", type="clue", label=random.choice(["feather", "tracks", "rustle"]), phrase="", revealed=False)
    quail = Entity(id="quail", kind="character", type="quail", label="a quail", phrase="a round brown quail", meters={"feet": 1.0}, memes={"startle": 1.0})
    world = World(place=place_key, child=child, adult=adult, missing=missing, clue=clue, quail=quail)
    world.facts.update(place=place_key, name=name, trait=trait, missing_key=missing_key, seed=seed)
    return world


def tell(world: World) -> World:
    c, a, m, clue, q = world.child, world.adult, world.missing, world.clue, world.quail
    place = PLACES[world.place]["label"]
    detail = PLACES[world.place]["detail"]

    world.say(f"{c.label} was a {world.facts['trait']} child who liked quiet places and tiny surprises.")
    world.say(f"One morning at {place}, {c.label} noticed that {m.phrase} was gone.")
    world.say(detail)
    world.say(f"{c.label} looked at the ground and listened closely, because mysteries often hid in small things.")
    world.para()

    world.say(f"Then {c.label} spotted {random.choice(['a feather', 'tiny tracks', 'a soft rustle'])}.")
    clue.revealed = True
    c.memes["worry"] += 1.0
    world.say(f"{c.label} thought, \"If I can understand this clue, I can solve the whole puzzle.\"")
    world.say(f"That was when the little sound of a laugh floated from the grass.")

    world.heard_laugh = True
    q.memes["startle"] += 0.0
    world.say(f"It was not a scary laugh. It was a surprised, secret laugh, like someone trying not to giggle.")
    world.para()

    # Flashback
    world.flashback_done = True
    world.say(f"{c.label} remembered something from yesterday.")
    world.say(f"Yesterday, {c.label} had left {m.phrase} on a bench near a nest.")
    world.say(f"A quail had fluttered out, brushed the bench, and the {m.label} must have slipped away then.")
    world.say(f"Back then, {c.label} had laughed too, because the quail had looked so puffed-up and puzzled.")
    world.para()

    # Inner monologue
    world.say(f"\"Think carefully,\" {c.label} told {c.label} inside {c.label}'s head.")
    world.say(f"\"The clue is not trouble. It's a trail.\"")
    world.say(f"{c.label} followed the tiny marks to a low nook under the reeds, where the missing thing was waiting.")
    world.say(f"It had only been tucked behind a stone, safe from the wind.")

    world.solved = True
    c.memes["worry"] = 0.0
    c.memes["relief"] = 1.0
    q.memes["startle"] = 0.0

    world.say(f"{c.label} laughed softly, not because anything was silly, but because the mystery finally made sense.")
    world.say(f"{c.label} picked up the {m.label} and held it tight.")
    world.say(f"The quail peeped from the grass, and the grown-up smiled at the tiny detective.")
    world.say(f"By the end, the clue had become a answer, and the quiet place felt friendly again.")

    world.facts.update(solved=True, heard_laugh=True, flashback_done=True)
    return world


def build_story(params: "StoryParams") -> StorySample:
    world = tell(make_world(params.place, params.name, params.trait, params.missing, params.seed))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


@dataclass
class StoryParams:
    place: str
    missing: str
    name: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a gentle mystery for a young child that includes a quail and a quiet laugh.",
        f"Tell a short story set in {PLACES[world.place]['label']} where {world.child.label} solves a tiny missing-item mystery.",
        "Use a flashback and an inner monologue to help the child connect a clue to the answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"What did {world.child.label} lose at {PLACES[world.place]['label']}?",
            answer=f"{world.child.label} lost {world.missing.phrase}, which started the mystery.",
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=f"The clue was {world.clue.phrase}, and it hinted that {world.facts['missing_key']} had been moved near the quail.",
        ),
        QAItem(
            question="Why did the story use a flashback?",
            answer="The flashback showed how the missing thing had been left near the nest the day before, which explained the clue.",
        ),
        QAItem(
            question=f"How did {world.child.label} feel at the end?",
            answer=f"{world.child.label} felt relieved and happy after finding {world.missing.phrase} again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quail?",
            answer="A quail is a small ground bird with a round body and quick feet.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a part of a story that goes back to an earlier time to explain something.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the silent thinking a character does inside their own head.",
        ),
        QAItem(
            question="Why can a clue matter in a mystery?",
            answer="A clue can point toward the truth and help a character solve what happened.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in [world.child, world.adult, world.missing, world.clue, world.quail]:
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.revealed:
            bits.append("revealed=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  solved={world.solved} heard_laugh={world.heard_laugh} flashback_done={world.flashback_done}")
    return "\n".join(lines)


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
    out.append("== (3) World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
place(garden). place(orchard). place(pond). place(barn).
missing(button). missing(key). missing(hat). missing(ribbon).
clue(feather). clue(footprint). clue(rustle).

can_happen(P, M) :- place(P), missing(M).
mystery(P, M) :- can_happen(P, M).
has_flashback(P) :- mystery(P, M), missing(M).
has_inner_monologue(P) :- mystery(P, M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for m in MISSING_THINGS:
        lines.append(asp.fact("missing", m))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery storyworld with quail, laugh, flashback, and inner monologue.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--missing", choices=sorted(MISSING_THINGS))
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=sorted(TRAITS))
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
    place = args.place or rng.choice(sorted(PLACES))
    missing = args.missing or rng.choice(sorted(MISSING_THINGS))
    trait = args.trait or rng.choice(TRAITS)
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, missing=missing, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import asp
    program = asp_program("#show mystery/2. #show has_flashback/1. #show has_inner_monologue/1.")
    model = asp.one_model(program)
    mystery_atoms = asp.atoms(model, "mystery")
    flash = asp.atoms(model, "has_flashback")
    mono = asp.atoms(model, "has_inner_monologue")
    ok = bool(mystery_atoms) and bool(flash) and bool(mono)
    if ok:
        print("OK: ASP rules produce the expected mystery features.")
        return 0
    print("MISMATCH: ASP rules did not produce the expected features.")
    return 1


CURATED = [
    StoryParams(place="garden", missing="button", name="Mina", trait="curious"),
    StoryParams(place="orchard", missing="key", name="Toby", trait="careful"),
    StoryParams(place="pond", missing="hat", name="Leah", trait="thoughtful"),
    StoryParams(place="barn", missing="ribbon", name="Nico", trait="quiet"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery/2. #show has_flashback/1. #show has_inner_monologue/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery/2. #show has_flashback/1. #show has_inner_monologue/1."))
        print("mystery:", sorted(set(asp.atoms(model, "mystery"))))
        print("flashback:", sorted(set(asp.atoms(model, "has_flashback"))))
        print("inner_monologue:", sorted(set(asp.atoms(model, "has_inner_monologue"))))
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
