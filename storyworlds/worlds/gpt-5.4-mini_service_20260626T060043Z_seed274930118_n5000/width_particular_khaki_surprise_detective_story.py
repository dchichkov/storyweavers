#!/usr/bin/env python3
"""
A standalone storyworld for a tiny detective mystery with a surprise reveal.

Seed-inspired premise:
- A detective notices a clue about width.
- The clue is particular and tied to a khaki-colored item.
- The case turns on a surprise: what seemed ordinary is actually the key.
- The story should feel like a small, classical detective tale with a child-facing
  tone and a clear state-driven turn.

The world models:
- Physical meters: width, tidy, hidden, found, etc.
- Emotional memes: curiosity, worry, surprise, relief, pride.

The detective follows the clues, tests a particular match, and discovers that a
khaki object hides the answer. The ending image proves the change.
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


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden_in: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    color: str = ""
    size: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "detective"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    kind: str = "city"


@dataclass
class Clue:
    label: str
    kind: str
    width: int
    color: str
    particular: str
    surprise: str


@dataclass
class StoryParams:
    place: str
    clue_kind: str
    suspect_kind: str
    detective_name: str
    assistant_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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
        out = ["--- world model state ---"]
        for e in self.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            if e.color:
                bits.append(f"color={e.color}")
            if e.size:
                bits.append(f"size={e.size}")
            if e.hidden_in:
                bits.append(f"hidden_in={e.hidden_in}")
            if e.carried_by:
                bits.append(f"carried_by={e.carried_by}")
            out.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
        return "\n".join(out)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "museum": Setting(place="the museum"),
    "library": Setting(place="the library"),
    "market": Setting(place="the market"),
    "station": Setting(place="the train station"),
}

CLUES = {
    "shoe": Clue(
        label="shoeprint",
        kind="shoeprint",
        width=4,
        color="khaki",
        particular="the left edge had a tiny nick",
        surprise="the print matched a shoe tucked inside a coat",
    ),
    "paper": Clue(
        label="paper scrap",
        kind="paper",
        width=3,
        color="khaki",
        particular="one corner was folded just so",
        surprise="the scrap came from a note hidden in a lunchbox",
    ),
    "ribbon": Clue(
        label="ribbon",
        kind="ribbon",
        width=2,
        color="khaki",
        particular="the knot was tied in a very exact way",
        surprise="the ribbon belonged to a bouquet hidden in a basket",
    ),
}

SUSPECTS = {
    "coat": {"label": "coat", "kind": "coat", "color": "khaki", "size": "wide"},
    "bag": {"label": "bag", "kind": "bag", "color": "khaki", "size": "small"},
    "box": {"label": "box", "kind": "box", "color": "khaki", "size": "narrow"},
}

NAMES = ["Ivy", "Milo", "Nora", "Tess", "Arlo", "Lena", "Pip", "June"]
ASSISTANTS = ["Jot", "Bean", "Moss", "Rae"]
TRAITS = ["quiet", "curious", "careful", "brave"]


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------

def clue_matches_suspect(clue: Clue, suspect_kind: str) -> bool:
    return clue.kind in {"shoeprint", "paper", "ribbon"} and suspect_kind in {"coat", "bag", "box"}


def judge_reasonable(clue: Clue, suspect_kind: str) -> bool:
    if clue.color != "khaki":
        return False
    if suspect_kind == "coat" and clue.width < 3:
        return False
    if suspect_kind == "bag" and clue.width > 3:
        return False
    return clue_matches_suspect(clue, suspect_kind)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def introduce(world: World, detective: Entity, assistant: Entity) -> None:
    world.say(
        f"{detective.id} was a {detective.memes.get('trait', 'curious')} detective "
        f"who never missed a small clue. {assistant.id} kept a pencil ready and a pocket notebook full of empty lines."
    )


def open_case(world: World, detective: Entity, clue: Clue, setting: Setting) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f"One bright morning, {detective.id} walked into {setting.place} and noticed something near the floor: "
        f"a {clue.color} {clue.label} with a width of about {clue.width} fingers."
    )
    world.say(
        f"It was not just any mark. {clue.particular.capitalize()}, and that made {detective.id} pause."
    )


def inspect_clue(world: World, detective: Entity, clue: Clue) -> None:
    detective.meters["focus"] = detective.meters.get("focus", 0) + 1
    world.say(
        f"{detective.id} crouched down and measured the clue again. "
        f"The width was {clue.width}, and the shape looked very particular."
    )


def find_suspect(world: World, clue: Clue, suspect: Entity) -> None:
    suspect.meters["hidden"] = 1
    world.say(
        f"Nearby stood a {suspect.color} {suspect.label}. At first it looked ordinary, but its shape felt suspiciously neat."
    )


def surprise_turn(world: World, detective: Entity, clue: Clue, suspect: Entity) -> None:
    detective.memes["surprise"] += 1
    detective.memes["certainty"] += 1
    suspect.meters["hidden"] = 0
    suspect.meters["found"] = 1
    world.say(
        f"Then came the surprise. {clue.surprise.capitalize()}, and the width matched perfectly."
    )
    world.say(
        f"{detective.id} smiled. The clue was not random at all; it had been waiting for a particular {suspect.label} all along."
    )


def reveal(world: World, detective: Entity, assistant: Entity, clue: Clue, suspect: Entity) -> None:
    detective.memes["relief"] += 1
    detective.memes["pride"] += 1
    assistant.memes["delight"] += 1
    world.say(
        f"{assistant.id} wrote it down while {detective.id} lifted the {suspect.label} aside. "
        f"Underneath was the missing item, safe and clean."
    )
    world.say(
        f"At the end of the case, the {clue.color} clue was no longer a mystery. "
        f"{detective.id} put the piece back where it belonged, and the room felt calm again."
    )


def tell(setting: Setting, clue: Clue, suspect: Entity, detective_name: str, assistant_name: str) -> World:
    world = World(setting)
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type="detective",
        label="detective",
        phrase=f"a {detective_name.lower()} detective",
        memes={"curiosity": 0.0, "surprise": 0.0, "relief": 0.0, "pride": 0.0, "certainty": 0.0},
        meters={"focus": 0.0},
    ))
    detective.memes["trait"] = "careful"
    assistant = world.add(Entity(
        id=assistant_name,
        kind="character",
        type="assistant",
        label="assistant",
        phrase=f"a helper named {assistant_name}",
        memes={"delight": 0.0},
    ))
    suspect_ent = world.add(Entity(
        id="suspect",
        kind="thing",
        type=suspect["kind"],
        label=suspect["label"],
        color=suspect["color"],
        size=suspect["size"],
    ))
    missing = world.add(Entity(
        id="missing",
        kind="thing",
        type="parcel",
        label="missing parcel",
        phrase="a missing parcel",
        hidden_in="suspect",
    ))

    world.facts.update(
        detective=detective,
        assistant=assistant,
        suspect=suspect_ent,
        missing=missing,
        clue=clue,
        setting=setting,
    )

    introduce(world, detective, assistant)
    world.para()
    open_case(world, detective, clue, setting)
    inspect_clue(world, detective, clue)
    find_suspect(world, clue, suspect_ent)
    world.para()
    if judge_reasonable(clue, suspect_ent.type):
        surprise_turn(world, detective, clue, suspect_ent)
        reveal(world, detective, assistant, clue, suspect_ent)
    else:
        raise StoryError("This clue and suspect do not make a reasonable detective story.")
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    clue: Clue = world.facts["clue"]
    setting: Setting = world.facts["setting"]
    return [
        f"Write a short detective story for a young child about a {clue.color} clue with a very particular width in {setting.place}.",
        f"Tell a gentle mystery where a detective notices a khaki {clue.label} and finds a surprise hiding behind it.",
        f"Create a story with a careful detective, a notebook, and a clue whose width matters to solving the case.",
    ]


def story_qa(world: World) -> list[QAItem]:
    detective: Entity = world.facts["detective"]
    assistant: Entity = world.facts["assistant"]
    clue: Clue = world.facts["clue"]
    suspect: Entity = world.facts["suspect"]
    setting: Setting = world.facts["setting"]

    return [
        QAItem(
            question=f"Who solved the mystery in {setting.place}?",
            answer=f"{detective.id} solved it with help from {assistant.id}.",
        ),
        QAItem(
            question=f"What color was the clue the detective noticed?",
            answer=f"It was khaki.",
        ),
        QAItem(
            question=f"What made the clue special?",
            answer=f"It had a very particular width of about {clue.width} fingers, and that helped {detective.id} match it to the right {suspect.label}.",
        ),
        QAItem(
            question=f"What was the surprise in the case?",
            answer=f"The surprise was that the {suspect.label} was hiding the missing parcel underneath it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    clue: Clue = world.facts["clue"]
    return [
        QAItem(
            question="What is a detective for?",
            answer="A detective looks for clues, asks careful questions, and tries to find out what happened.",
        ),
        QAItem(
            question="Why do people measure things?",
            answer="People measure things so they can compare sizes and figure out which thing matches best.",
        ),
        QAItem(
            question=f"What does khaki usually look like?",
            answer="Khaki is a light brown or sandy color.",
        ),
        QAItem(
            question=f"Why can a particular clue matter in a mystery?",
            answer=f"A particular clue matters because tiny details, like the width of a {clue.label}, can point to one exact answer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
clue(C) :- clue_kind(C).
suspect(S) :- suspect_kind(S).

reasonable(C,S) :- clue_kind(C), suspect_kind(S), khaki(C),
                   width(C,W), width_ok(S,W).
match(C,S) :- reasonable(C,S), particular(C,_).

width_ok(coat,W) :- W >= 3.
width_ok(bag,W) :- W =< 3.
width_ok(box,W) :- W >= 2, W =< 4.

surprise(C,S) :- match(C,S), hidden_under(S,_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue_kind", cid))
        lines.append(asp.fact("width", cid, clue.width))
        lines.append(asp.fact("color", cid, clue.color))
        lines.append(asp.fact("particular", cid, clue.particular))
        lines.append(asp.fact("khaki", cid))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect_kind", sid))
        lines.append(asp.fact("width", sid, 3 if sid == "coat" else 2 if sid == "bag" else 4))
        lines.append(asp.fact("hidden_under", sid, "parcel"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable_pairs() -> set[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    return set(asp.atoms(model, "reasonable"))


def asp_verify() -> int:
    py = {
        (c.kind, s)
        for c in CLUES.values()
        for s in SUSPECTS
        if judge_reasonable(c, s)
    }
    asp_pairs = asp_reasonable_pairs()
    if py == asp_pairs:
        print(f"OK: clingo gate matches python reasonableness ({len(py)} pairs).")
        return 0
    print("MISMATCH between clingo and python:")
    print(" python only:", sorted(py - asp_pairs))
    print(" clingo only:", sorted(asp_pairs - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective-story world with a khaki clue and a surprise reveal.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--clue", choices=CLUES.keys())
    ap.add_argument("--suspect", choices=SUSPECTS.keys())
    ap.add_argument("--name")
    ap.add_argument("--assistant")
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    clue_kind = args.clue or rng.choice(list(CLUES.keys()))
    suspect_kind = args.suspect or rng.choice(list(SUSPECTS.keys()))
    clue = CLUES[clue_kind]
    if not judge_reasonable(clue, suspect_kind):
        raise StoryError("The chosen clue and suspect do not make a reasonable mystery.")
    return StoryParams(
        place=place,
        clue_kind=clue_kind,
        suspect_kind=suspect_kind,
        detective_name=args.name or rng.choice(NAMES),
        assistant_name=args.assistant or rng.choice(ASSISTANTS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        CLUES[params.clue_kind],
        SUSPECTS[params.suspect_kind],
        params.detective_name,
        params.assistant_name,
    )
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


CURATED = [
    StoryParams(place="museum", clue_kind="shoe", suspect_kind="coat", detective_name="Ivy", assistant_name="Jot"),
    StoryParams(place="library", clue_kind="paper", suspect_kind="box", detective_name="Nora", assistant_name="Bean"),
    StoryParams(place="market", clue_kind="ribbon", suspect_kind="bag", detective_name="Tess", assistant_name="Moss"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        pairs = sorted(asp_reasonable_pairs())
        print(f"{len(pairs)} reasonable clue/suspect pairs:")
        for pair in pairs:
            print(" ", pair)
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
            except StoryError as e:
                print(e)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
