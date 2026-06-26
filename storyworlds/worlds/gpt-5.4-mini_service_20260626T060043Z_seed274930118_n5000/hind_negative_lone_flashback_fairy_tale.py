#!/usr/bin/env python3
"""
A standalone story world for a fairy-tale style hind tale with a flashback:
a lone hind remembers a safer glade, faces a negative omen, and chooses a
gentler path home.
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

STORY_THEME = "hind_negative_lone_flashback_fairy_tale"


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
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"hind", "doe", "deer"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    feature: str
    omen: str


@dataclass
class Wish:
    id: str
    label: str
    risk: str
    danger: str
    refuge: str


class World:
    def __init__(self, place: Place) -> None:
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

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


PLACES = {
    "moonwood": Place("Moonwood", "silver fern", "a thorn-black shadow"),
    "brookhollow": Place("Brookhollow", "a singing brook", "a cold hush"),
    "rosegate": Place("Rosegate", "a rose arch", "a fallen petal"),
}

WISHES = {
    "berries": Wish("berries", "sweet berries", "the berry thicket", "brambles and nettles", "the lantern path"),
    "spring": Wish("spring", "spring water", "the spring pool", "slippery stones", "the mossy bridge"),
    "home": Wish("home", "homeward way", "the old hill path", "dark roots and twisted branches", "the bright glen"),
}

NAMES = ["Elara", "Mira", "Nella", "Rowan", "Faye", "Lina"]
TRAITS = ["lone", "gentle", "brave", "quiet", "small"]


def flashback_memory(place: Place) -> str:
    return {
        "Moonwood": "she remembered a time when the moon shone kindly through the trees",
        "Brookhollow": "she remembered drinking from the brook beside her mother",
        "Rosegate": "she remembered running under blossoms with her little herd",
    }[place.name]


def reasonableness_gate(place: Place, wish: Wish) -> bool:
    return place.name != "Rosegate" or wish.id != "berries"


def select_wish(rng: random.Random, place: Place, maybe: Optional[str]) -> Wish:
    if maybe:
        return WISHES[maybe]
    choices = [w for w in WISHES.values() if reasonableness_gate(place, w)]
    return rng.choice(choices)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("feature", pid, p.feature))
        lines.append(asp.fact("omen", pid, p.omen))
    for wid, w in WISHES.items():
        lines.append(asp.fact("wish", wid))
        lines.append(asp.fact("risk", wid, w.risk))
        lines.append(asp.fact("danger", wid, w.danger))
        lines.append(asp.fact("refuge", wid, w.refuge))
    return "\n".join(lines)


ASP_RULES = r"""
unsafe(P,W) :- omen(P,_), wish(W), risk(W,R), danger(W,R).
safe_choice(P,W) :- wish(W), refuge(W,Ref), feature(P,Ref).
valid(P,W) :- place(P), wish(W), not unsafe(P,W), safe_choice(P,W).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid() -> list[tuple]:
    out = []
    for pid, p in PLACES.items():
        for wid, w in WISHES.items():
            if reasonableness_gate(p, w):
                out.append((pid, wid))
    return out


@dataclass
class StoryParams:
    place: str
    wish: str
    name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="moonwood", wish="berries", name="Elara"),
    StoryParams(place="brookhollow", wish="spring", name="Mira"),
    StoryParams(place="rosegate", wish="home", name="Nella"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world: a lone hind, a negative omen, and a flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--wish", choices=WISHES)
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
    place = args.place or rng.choice(list(PLACES))
    wish = select_wish(rng, PLACES[place], args.wish).id
    if not reasonableness_gate(PLACES[place], WISHES[wish]):
        raise StoryError("That wish does not fit this fairy-tale place.")
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, wish=wish, name=name)


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    hind = world.add(Entity(id=params.name, kind="character", type="hind", label=params.name))
    wish = WISHES[params.wish]
    lantern = world.add(Entity(id="lantern", type="lantern", label="a little lantern", owner=hind.id))
    world.facts.update(hind=hind, wish=wish, lantern=lantern, place=world.place)

    world.say(
        f"Once in {world.place.name}, there lived a {TRAITS[0]} hind named {hind.id}, "
        f"and she was very {TRAITS[0]} indeed, because she lived alone."
    )
    world.say(
        f"She loved the {world.place.feature}, but on that evening a {world.place.omen} lay over the trees."
    )
    world.para()
    world.say(
        f"{hind.id} wanted {wish.label}, yet the way was hidden by {wish.danger}."
    )
    world.say(
        f"The air felt negative and cold, and the lone hind slowed her steps."
    )
    world.say(
        f"Then she had a flashback: {flashback_memory(world.place)}."
    )
    world.para()
    world.say(
        f"She lifted her little lantern and chose the {wish.refuge} instead of the dark path."
    )
    world.say(
        f"So {hind.id} found a safe way forward, and the shadow behind her lost its power."
    )
    world.say(
        f"By the time she reached the glen, the hind was no longer lonely, because the night itself had grown kind."
    )

    prompts = [
        f"Write a short fairy tale about a lone hind named {params.name} in {world.place.name}.",
        f"Tell a story with a negative omen, a flashback, and a gentle ending for a hind who wants {wish.label}.",
        f"Write a child-friendly fairy tale where {params.name} remembers something from before and chooses a safer path.",
    ]

    story_qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about a lone hind named {hind.id} in {world.place.name}.",
        ),
        QAItem(
            question=f"What did {hind.id} want?",
            answer=f"{hind.id} wanted {wish.label}.",
        ),
        QAItem(
            question=f"What happened when the path felt negative and unsafe?",
            answer=f"{hind.id} had a flashback, remembered a kinder time, and chose the {wish.refuge} instead.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a hind?",
            answer="A hind is a female deer.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened earlier.",
        ),
        QAItem(
            question="Why can a dark omen make a character feel worried?",
            answer="A dark omen can suggest danger or trouble ahead, so a character may slow down and choose carefully.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
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
        for i, p in enumerate(sample.prompts, 1):
            print(f"P{i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type}, location={e.location}, meters={e.meters}, memes={e.memes}")
    lines.append(f"place={world.place.name}")
    lines.append(f"facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


def verify() -> int:
    a = set(asp_valid())
    b = set(python_valid())
    if a == b:
        print(f"OK: ASP and Python agree on {len(a)} valid choices.")
        return 0
    print("Mismatch between ASP and Python.")
    if a - b:
        print("Only in ASP:", sorted(a - b))
    if b - a:
        print("Only in Python:", sorted(b - a))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} valid place/wish pairs")
        for p, w in vals:
            print(p, w)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
