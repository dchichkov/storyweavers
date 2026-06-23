#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T042304Z_seed1855084837_n10/scrub_reconciliation_surprise_moral_value_slice_of.py
===============================================================================================================================

A small slice-of-life storyworld about a child doing a scrubby chore, a surprise,
and a gentle reconciliation with a moral-value ending.
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional


def _bootstrap_sys_path() -> None:
    here = os.path.abspath(__file__)
    cur = os.path.dirname(here)
    while True:
        # Prefer the project root that contains the storyworlds package.
        if os.path.isdir(os.path.join(cur, "storyworlds")) and cur not in sys.path:
            sys.path.insert(0, cur)
            return
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    pkg = os.path.dirname(os.path.dirname(here))
    if pkg not in sys.path:
        sys.path.insert(0, pkg)


_bootstrap_sys_path()
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: str = ""
    caretaker: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"dirty": 0.0, "clean": 0.0, "mess": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"joy": 0.0, "hurt": 0.0, "pride": 0.0, "regret": 0.0, "care": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Chore:
    id: str
    verb: str
    noun: str
    mess: str
    cleanup: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    reveal: str
    gift: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


PLACES = {
    "kitchen": Place(id="kitchen", label="the kitchen", detail="sunlight on the table", affords={"dishes", "counter"}),
    "laundry": Place(id="laundry", label="the laundry room", detail="a humming washer and a basket of socks", affords={"basket", "floor"}),
    "porch": Place(id="porch", label="the porch", detail="a little row of shoes by the door", affords={"chair", "floor"}),
}

CHORES = {
    "dishes": Chore(id="dishes", verb="scrub the dishes", noun="dishes", mess="splash", cleanup="rinsed clean", clue="soap bubbles", tags={"scrub", "clean", "water"}),
    "counter": Chore(id="counter", verb="scrub the counter", noun="counter", mess="crumbs", cleanup="wiped clean", clue="sticky jam", tags={"scrub", "clean", "kitchen"}),
    "basket": Chore(id="basket", verb="scrub the laundry basket", noun="basket", mess="lint", cleanup="brushed clean", clue="a forgotten note", tags={"scrub", "home", "note"}),
    "floor": Chore(id="floor", verb="scrub the floor", noun="floor", mess="mud", cleanup="mopped clean", clue="a tiny sticker", tags={"scrub", "floor", "mud"}),
    "chair": Chore(id="chair", verb="scrub the chair", noun="chair", mess="dust", cleanup="polished clean", clue="a ribbon under the seat", tags={"scrub", "chair", "dust"}),
}

SURPRISES = {
    "note": Surprise(id="note", reveal="a small thank-you note was tucked under the cloth", gift="a folded note", tags={"note", "surprise"}),
    "snack": Surprise(id="snack", reveal="a plate of warm cookies was waiting on the counter", gift="cookies", tags={"snack", "surprise"}),
    "photo": Surprise(id="photo", reveal="a family photo had been propped up to dry", gift="a photo", tags={"photo", "surprise"}),
}

GIRL_NAMES = ["Mina", "Ivy", "Lena", "Nora", "Sage", "Ella"]
BOY_NAMES = ["Noah", "Theo", "Eli", "Owen", "Finn", "Milo"]
TRAITS = ["patient", "kind", "curious", "gentle", "careful"]


@dataclass
class StoryParams:
    place: str
    chore: str
    surprise: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for chore in PLACES[place].affords:
            for surprise in SURPRISES:
                combos.append((place, chore, surprise))
    return combos


ASP_RULES = r"""
valid(P,C,S) :- place(P), chore(C), surprise(S), affords(P,C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for c in sorted(p.affords):
            lines.append(asp.fact("affords", pid, c))
    for cid in CHORES:
        lines.append(asp.fact("chore", cid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def _setup_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, role="child", tags={"child"}, attrs={"trait": params.trait}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, role="parent", label="the parent", tags={"adult"}))
    chore_obj = world.add(
        Entity(
            id="chore",
            type="chore",
            label=CHORES[params.chore].noun,
            phrase=CHORES[params.chore].verb,
            tags=set(CHORES[params.chore].tags),
            attrs={"cleanup": CHORES[params.chore].cleanup, "clue": CHORES[params.chore].clue},
        )
    )
    surprise = world.add(Entity(id="surprise", type="surprise", label=SURPRISES[params.surprise].gift, phrase=SURPRISES[params.surprise].reveal, tags=set(SURPRISES[params.surprise].tags)))
    world.facts.update(child=child, parent=parent, chore=chore_obj, surprise=surprise, place=place)
    return world


def _tell(world: World) -> None:
    child = world.facts["child"]
    parent = world.facts["parent"]
    chore = world.facts["chore"]
    surprise = world.facts["surprise"]
    place = world.place
    cleanup = chore.attrs.get("cleanup", "clean")
    child.memes["joy"] += 1
    world.say(f"On a quiet afternoon, {child.id} and {parent.label_word} were in {place.label}. The room felt calm, with {place.detail}.")
    world.say(f"{child.id} wanted to {chore.phrase}, because {chore.label} looked a little messy and the job felt useful.")
    world.para()
    child.meters["mess"] += 1
    world.say(f"{child.id} got to work. Soap, water, and steady hands turned the {chore.label} from dirty to {cleanup}.")
    child.memes["pride"] += 1
    parent.memes["care"] += 1
    if surprise.id == "note":
        world.say(f"Then, while the cloth moved aside, {surprise.phrase}. It was a small surprise, but it made {child.id} smile.")
    elif surprise.id == "snack":
        world.say(f"Then, while the work was almost done, {surprise.phrase}. It was a happy surprise waiting to be shared.")
    else:
        world.say(f"Then, while the surface dried, {surprise.phrase}. The sight brought the whole room a softer feeling.")
    world.para()
    child.memes["hurt"] += 1
    world.say(f"{parent.label_word.capitalize()} pointed out a small mistake in a kind voice, and {child.id}'s face fell for a moment.")
    world.say(f"{child.id} felt embarrassed, but the surprise helped: it was really meant as a thank-you, not a correction.")
    child.memes["regret"] += 1
    world.say(f"{child.id} said sorry for snapping back, and {parent.label_word} said sorry too for sounding too sharp.")
    child.memes["joy"] += 1
    parent.memes["care"] += 1
    world.para()
    world.say(f"After that, {child.id} finished the job with a calmer heart. The {chore.label} stayed {cleanup}, the surprise stayed on the table, and the kitchen felt peaceful again.")
    world.say(f"That evening, {child.id} learned a simple moral: a little care can turn an awkward moment into a better one.")


def _prompts(world: World) -> list[str]:
    c = world.facts["child"]
    ch = world.facts["chore"]
    p = world.place
    return [
        f"Write a slice-of-life story about {c.id} in {p.label} who needs to {ch.phrase}, includes the word scrub, and ends with a small surprise.",
        f"Tell a gentle story where a child helps with {ch.label}, then a surprise appears and the child learns a kind moral value.",
        f"Write a short everyday story about family chores, reconciliation after a small hurt feeling, and a surprise with a warm ending.",
    ]


def _story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    p = world.facts["parent"]
    ch = world.facts["chore"]
    return [
        QAItem(question=f"What was {c.id} trying to do in {world.place.label}?", answer=f"{c.id} was trying to {ch.phrase}. It was an ordinary chore, and the story showed them making the space neater bit by bit."),
        QAItem(question=f"Why did the surprise matter after the chore?", answer=f"The surprise mattered because it softened the mood after the small hurt feelings. It helped {c.id} and {p.label_word} come back together and talk more gently."),
        QAItem(question=f"What did {c.id} learn by the end?", answer="They learned that a kind apology can fix an awkward moment. The moral was that care and honesty can turn a hard minute into a better one."),
    ]


def _world_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(question="What does scrub mean?", answer="Scrub means to clean something by rubbing it with effort, usually with water, soap, or a cloth."),
        QAItem(question="Why do people do chores at home?", answer="People do chores to keep their homes clean, safe, and comfortable. Shared work also helps families take care of one another."),
        QAItem(question="What is reconciliation?", answer="Reconciliation is when people who had hurt feelings make up and feel close again. They may apologize, forgive, and start fresh."),
        QAItem(question="What is a surprise?", answer="A surprise is something unexpected that suddenly appears or happens. It can make an ordinary day feel special."),
        QAItem(question="What is a moral value?", answer="A moral value is a good lesson about how to treat people well, like being kind, honest, or patient."),
    ]
    return out


def _format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def _trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)} attrs={e.attrs}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.chore not in CHORES or params.surprise not in SURPRISES:
        raise StoryError("invalid parameter combination")
    world = _setup_world(params)
    _tell(world)
    return StorySample(params=params, story=world.render(), prompts=_prompts(world), story_qa=_story_qa(world), world_qa=_world_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(_trace(sample.world))
    if qa:
        print()
        print(_format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about scrub, reconciliation, surprise, and moral value.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--chore", choices=sorted(CHORES))
    ap.add_argument("--surprise", choices=sorted(SURPRISES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"], default="mother")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.chore is None or c[1] == args.chore)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, chore, surprise = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, chore=chore, surprise=surprise, name=name, gender=gender, parent=parent, trait=trait)


CURATED = [
    StoryParams(place="kitchen", chore="dishes", surprise="note", name="Mina", gender="girl", parent="mother", trait="kind"),
    StoryParams(place="laundry", chore="basket", surprise="snack", name="Noah", gender="boy", parent="father", trait="patient"),
    StoryParams(place="porch", chore="floor", surprise="photo", name="Ivy", gender="girl", parent="mother", trait="gentle"),
]


def asp_verify() -> int:
    import asp
    p = set(asp_valid_combos())
    py = set(valid_combos())
    ok = p == py
    print("OK: ASP matches Python valid_combos()." if ok else "MISMATCH: ASP and Python differ.")
    sample = generate(CURATED[0])
    if not sample.story.strip():
        print("MISMATCH: generate() returned empty story.")
        ok = False
    buf = io.StringIO()
    old = sys.stdout
    try:
        sys.stdout = buf
        emit(sample, trace=True, qa=True)
    finally:
        sys.stdout = old
    return 0 if ok else 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for row in combos:
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
