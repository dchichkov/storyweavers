#!/usr/bin/env python3
"""
Toy Store Whodunit: a child-friendly mystery in a toy store with a hidden cafe
corner, a lurking clue, and a shoe-shaped surprise.

A small, state-driven storyworld where a curious kid investigates a puzzling
mix-up at a toy store. The world is built for a gentle whodunit tone: clues,
suspects, a surprise reveal, and a satisfying ending image.
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "lady"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the toy store"
    cafe_corner: bool = True


@dataclass
class Clue:
    id: str
    label: str
    source: str
    place: str
    reveals: str
    surprise: bool = False


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    motive: str
    alibi: str
    suspicious: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _safe_sight(world: World, actor: Entity, item: Entity) -> bool:
    return not item.hidden or actor.memes.get("noticed", 0) >= THRESHOLD


def _r_note_clue(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    for clue in world.facts["clues"]:
        sig = ("clue", clue.id)
        if sig in world.fired:
            continue
        if clue.source == "cafe" and world.setting.cafe_corner:
            world.fired.add(sig)
            detective.memes["noticed"] = detective.memes.get("noticed", 0) + 1
            out.append(f"Near the cafe corner, {clue.label} looked oddly out of place.")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    if detective.memes.get("noticed", 0) < THRESHOLD:
        return out
    for clue in world.facts["clues"]:
        if clue.surprise and ("surprise", clue.id) not in world.fired:
            world.fired.add(("surprise", clue.id))
            detective.memes["surprise"] = detective.memes.get("surprise", 0) + 1
            out.append(f"The clue suddenly pointed to something surprising.")
    return out


CAUSAL_RULES = [_r_note_clue, _r_surprise]


def propagate(world: World) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    for s in out:
        world.say(s)
    return out


@dataclass
class StoryParams:
    seed: Optional[int] = None
    detective_name: str = "Mina"
    suspect_a: str = "the shopkeeper"
    suspect_b: str = "the little brother"
    place: str = "toy store"


SETTINGS = {
    "toy store": Setting(place="the toy store", cafe_corner=True),
}

CLUES = {
    "shoe": Clue(
        id="shoe",
        label="a tiny shoe print",
        source="cafe",
        place="by the cafe counter",
        reveals="someone had hurried away carrying a shoe-shaped toy",
        surprise=True,
    ),
    "receipt": Clue(
        id="receipt",
        label="a bent receipt",
        source="shelf",
        place="under the puzzle boxes",
        reveals="the missing item had been bought with a toy cup and a ribbon",
    ),
    "ribbon": Clue(
        id="ribbon",
        label="a red ribbon",
        source="floor",
        place="near the stuffed animals",
        reveals="the surprise gift was wrapped like a birthday present",
        surprise=True,
    ),
}

SUSPECTS = {
    "shopkeeper": Suspect(
        id="shopkeeper",
        label="the shopkeeper",
        type="woman",
        motive="she was keeping the surprise hidden",
        alibi="she had been making pretend cocoa at the cafe corner",
    ),
    "brother": Suspect(
        id="brother",
        label="the little brother",
        type="boy",
        motive="he loved sneaking peeks at presents",
        alibi="he had been hiding behind the blocks tower",
    ),
    "friend": Suspect(
        id="friend",
        label="the best friend",
        type="girl",
        motive="she wanted to help with a surprise",
        alibi="she had been counting plush cats by the window",
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Pia", "Sara", "Nora"]
BOY_NAMES = ["Noah", "Eli", "Finn", "Theo", "Ben"]


def build_mystery(world: World) -> None:
    detective = world.add(Entity(id="detective", kind="character", type="girl", label=world.facts["detective_name"]))
    detective.memes["curious"] = 1
    detective.memes["worry"] = 1

    for sid, suspect in world.facts["suspects"].items():
        world.add(Entity(id=sid, kind="character", type=suspect.type, label=suspect.label))

    for clue in world.facts["clues"]:
        world.add(Entity(id=clue.id, type="thing", label=clue.label, hidden=True))

    world.say(
        f"{detective.label} came into the toy store and noticed something odd: a shoe was missing."
    )
    world.say(
        f"Near the cafe corner, cups clinked softly, and {detective.label} felt sure the answer was hiding somewhere."
    )

    world.para()
    world.say(
        f"She looked at {world.facts['suspects']['shopkeeper'].label}, {world.facts['suspects']['brother'].label}, "
        f"and {world.facts['suspects']['friend'].label}."
    )
    world.say(
        f"Each one had a reason to seem suspicious, but each one also had an alibi."
    )

    world.para()
    for clue in world.facts["clues"]:
        world.say(f"{detective.label} found {clue.label} {clue.place}.")
        world.get(clue.id).hidden = False
        propagate(world)

    world.para()
    culprit = world.facts["culprit"]
    if culprit == "shopkeeper":
        world.say(
            f"Then the surprise finally made sense: the shopkeeper had tucked the shoe-shaped toy beside the cafe counter."
        )
        world.say(
            f"It was not a theft at all. It was a birthday surprise waiting to be wrapped."
        )
    else:
        world.say(
            f"Then the surprise finally made sense: the missing shoe was not lost, but hidden for a secret gift."
        )
        world.say(
            f"The clues had pointed to a surprise party all along."
        )

    world.para()
    world.say(
        f"{detective.label} smiled and put the shoe back in its box. The toy store felt peaceful again, "
        f"and the cafe corner smelled like pretend cocoa instead of mystery."
    )


def explain_reason(world: World) -> None:
    # No extra state changes; just centralizes the final reveal.
    pass


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a gentle whodunit story set in a toy store with a cafe corner, a shoe clue, and a surprise ending.',
        f"Tell a child-sized mystery where {world.facts['detective_name']} follows clues, questions suspects, and learns the shoe was hidden for a surprise.",
        'Write a short detective story in a toy store that includes a lurking clue near a cafe and ends with a happy reveal.',
    ]


def story_qa(world: World) -> list[QAItem]:
    detective = world.facts["detective_name"]
    culprit = world.facts["culprit"]
    clues = world.facts["clues"]
    suspect_names = ", ".join(s.label for s in world.facts["suspects"].values())
    return [
        QAItem(
            question=f"Who solved the mystery in the toy store?",
            answer=f"{detective} solved it by following the clues around the toy store.",
        ),
        QAItem(
            question="What was missing at first?",
            answer="A shoe-shaped toy was missing, which made the toy store feel like a mystery.",
        ),
        QAItem(
            question="Where did the first clue lurk?",
            answer="The first clue lurked near the cafe corner by the toy store counter.",
        ),
        QAItem(
            question="Who did the detective think might be involved?",
            answer=f"The detective watched {suspect_names} because each one seemed a little suspicious.",
        ),
        QAItem(
            question="What was the surprise at the end?",
            answer=f"The surprise was that the shoe had been hidden on purpose, because the shopkeeper was preparing a surprise.",
        ),
        QAItem(
            question="Who was really behind the surprise?",
            answer=f"It was {world.facts['suspects'][culprit].label}, who had a reason to keep the shoe hidden for a surprise reveal.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a toy store?",
            answer="A toy store is a place where children can find toys, games, and playful things to buy or look at.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small hint that helps someone figure out what happened.",
        ),
        QAItem(
            question="What does it mean to lurk?",
            answer="To lurk means to stay hidden or quiet and wait in a place where you might not be noticed.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that someone did not know about ahead of time.",
        ),
        QAItem(
            question="What is a cafe?",
            answer="A cafe is a cozy place where people can sit and have drinks or snacks.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.hidden:
            bits.append("hidden=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    world.facts["detective_name"] = params.detective_name
    world.facts["suspects"] = {
        "shopkeeper": SUSPECTS["shopkeeper"],
        "brother": SUSPECTS["brother"],
        "friend": SUSPECTS["friend"],
    }
    world.facts["clues"] = [CLUES["shoe"], CLUES["receipt"], CLUES["ribbon"]]
    world.facts["culprit"] = "shopkeeper"

    build_mystery(world)
    return world


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("place", "toy_store"))
    lines.append(asp.fact("feature", "cafe_corner"))
    lines.append(asp.fact("item", "shoe"))
    lines.append(asp.fact("theme", "surprise"))
    lines.append(asp.fact("style", "whodunit"))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("reveals", cid, clue.reveals))
        if clue.surprise:
            lines.append(asp.fact("surprise_clue", cid))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("motive", sid, s.motive))
    return "\n".join(lines)


ASP_RULES = r"""
shown(C) :- clue(C), surprise_clue(C).
mystery(C) :- clue(C), reveals(C, R), R != "".
whodunit(S) :- suspect(S), motive(S, _).
#show shown/1.
#show whodunit/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show shown/1.\n#show whodunit/1."))
    shown = sorted(set(asp.atoms(model, "shown")))
    whodunit = sorted(set(asp.atoms(model, "whodunit")))
    return shown + whodunit


def asp_verify() -> int:
    py = {("shown", "shoe"), ("shown", "ribbon"), ("whodunit", "shopkeeper"), ("whodunit", "brother"), ("whodunit", "friend")}
    cl = set()
    for pred, arg in asp_valid():
        cl.add((pred, arg))
    if cl == py:
        print(f"OK: clingo gate matches python gate ({len(cl)} atoms).")
        return 0
    print("MISMATCH between clingo and python gate:")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Toy store whodunit with a cafe corner, a shoe clue, and a surprise ending.")
    ap.add_argument("--name", dest="detective_name")
    ap.add_argument("--place", choices=SETTINGS.keys())
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
    place = args.place or "toy store"
    if place not in SETTINGS:
        raise StoryError("This mystery only works in the toy store.")
    return StoryParams(
        seed=args.seed,
        detective_name=args.detective_name or rng.choice(GIRL_NAMES + BOY_NAMES),
        place=place,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(detective_name="Mina", place="toy store"),
    StoryParams(detective_name="Theo", place="toy store"),
    StoryParams(detective_name="Nora", place="toy store"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show shown/1.\n#show whodunit/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show shown/1.\n#show whodunit/1."))
        print("ASP atoms:", sorted(asp.atoms(model, "shown")) + sorted(asp.atoms(model, "whodunit")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {sample.params.detective_name} at the toy store"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
