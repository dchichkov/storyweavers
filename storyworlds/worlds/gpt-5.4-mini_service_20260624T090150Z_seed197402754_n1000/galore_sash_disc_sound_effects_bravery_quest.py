#!/usr/bin/env python3
"""
A small storyworld for a mystery-leaning quest about sound effects, bravery, and
a found disc with a sash.

The domain is intentionally tiny and simulation-driven:
- a child protagonist hears clues as sound effects
- a missing disc must be recovered
- a sash is a meaningful object that can help reveal identity
- bravery changes the child's emotional state and lets the quest resolve
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("value", 0.0)
        self.meters.setdefault("missing", 0.0)
        self.memes.setdefault("fear", 0.0)
        self.memes.setdefault("bravery", 0.0)
        self.memes.setdefault("curiosity", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    mood: str
    clues: list[str] = field(default_factory=list)
    soundscape: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    helper_name: str
    clue_sound: str
    disc_owner: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
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

    def trace(self) -> str:
        parts = ["--- world model state ---"]
        for e in self.entities.values():
            meters = {k: round(v, 2) for k, v in e.meters.items() if v}
            memes = {k: round(v, 2) for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            if e.worn_by:
                bits.append(f"worn_by={e.worn_by}")
            parts.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
        return "\n".join(parts)


PLACES = {
    "attic": Place(
        name="the attic",
        mood="dusty",
        clues=["a squeaky floorboard", "a whispery draft", "a tiny chime"],
        soundscape=["creak", "tap-tap", "hush"],
    ),
    "hall": Place(
        name="the old hall",
        mood="quiet",
        clues=["a soft echo", "a muffled thump", "a long hallway hum"],
        soundscape=["thump", "thrum", "whoosh"],
    ),
    "garden_shed": Place(
        name="the garden shed",
        mood="shadowy",
        clues=["a rattling latch", "a metal ring", "a hidden shelf"],
        soundscape=["clink", "rattle", "ding"],
    ),
}

GIRL_NAMES = ["Maya", "Nora", "Lina", "Zoe", "Ivy", "Ella"]
BOY_NAMES = ["Theo", "Noah", "Milo", "Eli", "Finn", "Ben"]

SOUNDS = {
    "creak": "creak",
    "tap": "tap-tap",
    "echo": "echo",
    "clink": "clink",
    "rattle": "rattle",
    "ding": "ding",
    "hush": "hush",
    "whoosh": "whoosh",
}


def sound_effect_galore(chosen: str) -> str:
    return {
        "creak": "creak creak",
        "tap": "tap-tap tap-tap",
        "echo": "echo... echo...",
        "clink": "clink clink",
        "rattle": "rattle-rattle",
        "ding": "ding!",
        "hush": "hush hush",
        "whoosh": "whoosh",
    }.get(chosen, chosen)


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("unknown place")
    place = PLACES[params.place]
    world = World(place)

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        label=params.child_name,
        meters={"value": 0.0},
        memes={"fear": 0.0, "bravery": 0.0, "curiosity": 1.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="mother" if params.child_gender == "girl" else "father",
        label=params.helper_name,
        meters={"value": 0.0},
        memes={"fear": 0.0, "bravery": 0.5, "curiosity": 0.5},
    ))
    disc = world.add(Entity(
        id="disc",
        kind="thing",
        type="disc",
        label="disc",
        phrase="a shiny disc",
        owner=params.disc_owner,
        meters={"value": 1.0, "missing": 1.0},
    ))
    sash = world.add(Entity(
        id="sash",
        kind="thing",
        type="sash",
        label="sash",
        phrase="a bright sash",
        owner=params.disc_owner,
        meters={"value": 1.0},
    ))

    world.facts.update(
        child=child,
        helper=helper,
        disc=disc,
        sash=sash,
        place=place,
        clue_sound=params.clue_sound,
        owner=params.disc_owner,
    )
    return world


def begin_story(world: World) -> None:
    c = world.facts["child"]
    helper = world.facts["helper"]
    place = world.facts["place"]
    sound = world.facts["clue_sound"]
    world.say(
        f"{c.id} went into {place.name} because a mystery had to be solved."
    )
    world.say(
        f"Somewhere in the dim corners, {sound_effect_galore(sound)} kept drifting through the air, "
        f"and {c.id} listened very hard."
    )
    world.para()
    world.say(
        f"{helper.label} said the missing disc mattered because it belonged with a bright sash, "
        f"and the two of them had to find the pair before night fell."
    )


def find_clues(world: World) -> None:
    c = world.facts["child"]
    place = world.facts["place"]
    disc = world.facts["disc"]
    world.para()
    world.say(
        f"{c.id} followed the clues one by one: {', '.join(place.clues[:-1])}, and {place.clues[-1]}."
    )
    world.say(
        f"Each clue made the sound in the room feel louder, like {sound_effect_galore(world.facts['clue_sound'])} leading the way."
    )
    c.memes["curiosity"] += 1.0
    c.meters["value"] += 1.0
    disc.meters["missing"] = 1.0


def fear_turn(world: World) -> None:
    c = world.facts["child"]
    helper = world.facts["helper"]
    sash = world.facts["sash"]
    world.para()
    c.memes["fear"] += 1.0
    world.say(
        f"Then {c.id} found the sash hanging on a hook, but the disc was still nowhere in sight."
    )
    world.say(
        f"{c.id} felt a little scared in the hush, and {helper.label} knelt down to say that brave hearts can keep looking."
    )
    world.say(
        f"The sash was a clue, not the answer, and that made the mystery feel bigger."
    )
    sash.meters["value"] += 0.5


def bravery_resolution(world: World) -> None:
    c = world.facts["child"]
    helper = world.facts["helper"]
    disc = world.facts["disc"]
    sash = world.facts["sash"]
    world.para()
    c.memes["bravery"] += 1.5
    c.memes["fear"] = 0.0
    disc.meters["missing"] = 0.0
    disc.worn_by = c.id
    sash.worn_by = c.id
    world.say(
        f"{c.id} took a deep breath, stepped toward the dark shelf, and listened for one last clue."
    )
    world.say(
        f"With a final {sound_effect_galore(world.facts['clue_sound'])}, {c.id} lifted the hidden box and found the disc inside."
    )
    world.say(
        f"At the end, {c.id} wore the sash and held the disc up like a treasure while {helper.label} smiled, because the mystery was solved."
    )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    begin_story(world)
    find_clues(world)
    fear_turn(world)
    bravery_resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    c = world.facts["child"]
    place = world.facts["place"]
    return [
        f"Write a child-friendly mystery story with lots of sound effects galore in {place.name}.",
        f"Tell a brave quest story where {c.id} follows clues to find a missing disc and a special sash.",
        "Write a short story that uses sound clues, a little fear, and a brave ending where the mystery is solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    helper = world.facts["helper"]
    disc = world.facts["disc"]
    sash = world.facts["sash"]
    place = world.facts["place"]
    return [
        QAItem(
            question=f"Who was trying to solve the mystery in {place.name}?",
            answer=f"{c.id} was trying to solve the mystery, and {helper.label} was helping.",
        ),
        QAItem(
            question="What did the child hear again and again while searching?",
            answer=f"{c.id} kept hearing {sound_effect_galore(world.facts['clue_sound'])}, which helped guide the search.",
        ),
        QAItem(
            question="What two things were found by the end?",
            answer=f"The missing disc was found, and the sash was being worn during the happy ending.",
        ),
        QAItem(
            question="How did the child change during the quest?",
            answer=f"{c.id} started out curious and a little scared, but became brave enough to check the hidden spot and finish the quest.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a disc?",
            answer="A disc is a round, flat object, like a shiny circle that can be carried or kept safe.",
        ),
        QAItem(
            question="What is a sash?",
            answer="A sash is a band of cloth worn across the body or around the waist, often to show a special role or decoration.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are special words that copy sounds, like creak, tap, or ding, so a story can feel more alive.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when it feels scary, because the goal is important.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey with a goal, where someone looks for something important or tries to solve a problem.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery-like quest storyworld.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--clue-sound", choices=sorted(SOUNDS))
    ap.add_argument("--owner", default="grandparent")
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
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_name = args.helper or rng.choice(["Mina", "Perry", "Jules", "Robin"])
    clue_sound = args.clue_sound or rng.choice(list(SOUNDS))
    return StoryParams(
        place=place,
        child_name=child_name,
        child_gender=gender,
        helper_name=helper_name,
        clue_sound=clue_sound,
        disc_owner=args.owner,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
place(attic). place(hall). place(garden_shed).
sound(creak). sound(tap). sound(echo). sound(clink). sound(rattle). sound(ding). sound(hush). sound(whoosh).
feature(sound_effects). feature(bravery). feature(quest).
style(mystery).

valid(P, S, F) :- place(P), sound(S), feature(F), style(mystery).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for s in SOUNDS:
        lines.append(asp.fact("sound", s))
    for f in ["sound_effects", "bravery", "quest"]:
        lines.append(asp.fact("feature", f))
    lines.append(asp.fact("style", "mystery"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    prog = asp_program("#show valid/3.")
    model = asp.one_model(prog)
    atoms = sorted(set(asp.atoms(model, "valid")))
    python_set = sorted((p, s, "sound_effects") for p in PLACES for s in SOUNDS)
    if len(atoms) == len(python_set):
        print(f"OK: ASP twin produced {len(atoms)} valid triples.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", atoms[:10])
    print("PY :", python_set[:10])
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        for row in vals:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        all_params = [
            StoryParams(place=p, child_name=n, child_gender=g, helper_name="Mina", clue_sound=s, disc_owner="grandparent")
            for p in PLACES
            for g in ["girl", "boy"]
            for n in (GIRL_NAMES if g == "girl" else BOY_NAMES)[:1]
            for s in ["creak", "clink", "ding"]
        ]
        samples = [generate(p) for p in all_params]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
