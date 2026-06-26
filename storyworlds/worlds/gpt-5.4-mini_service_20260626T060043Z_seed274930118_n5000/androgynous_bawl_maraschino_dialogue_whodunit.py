#!/usr/bin/env python3
"""
A small whodunit storyworld with dialogue, an androgynous suspect, a bawling
child, and a maraschino cherry clue.
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

METER_KEYS = ("curiosity", "fear", "relief", "stain", "noise")
MEME_KEYS = ("suspicion", "confidence", "alarm", "comfort", "bawl")


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
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Location:
    id: str
    label: str
    indoor: bool
    clues: set[str] = field(default_factory=set)
    witnesses: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    hidden_by: str = ""
    reveals: str = ""
    owner: Optional[str] = None
    found: bool = False


@dataclass
class StoryParams:
    location: str
    culprit: str
    clue: str
    hero_name: str
    hero_type: str
    detective_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.clues: dict[str, Clue] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_clue(self, clue: Clue) -> Clue:
        self.clues[clue.id] = clue
        return clue

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


LOCATIONS = {
    "parlor": Location(
        id="parlor",
        label="the parlor",
        indoor=True,
        clues={"couch", "lamp", "table"},
        witnesses={"host", "guest"},
    ),
    "library": Location(
        id="library",
        label="the library",
        indoor=True,
        clues={"bookstack", "desk", "rug"},
        witnesses={"librarian", "reader"},
    ),
    "garden_room": Location(
        id="garden_room",
        label="the glass garden room",
        indoor=True,
        clues={"fern", "bench", "tray"},
        witnesses={"host", "helper"},
    ),
}

CULPRITS = {
    "host": ("host", "the host"),
    "guest": ("guest", "the guest"),
    "helper": ("helper", "the helper"),
    "librarian": ("librarian", "the librarian"),
}

CLUES = {
    "maraschino": Clue(
        id="maraschino",
        label="a maraschino cherry",
        phrase="a bright maraschino cherry",
        hidden_by="cake",
        reveals="someone reached for the dessert first",
    ),
    "napkin": Clue(
        id="napkin",
        label="a crumpled napkin",
        phrase="a crumpled napkin with red sugar on it",
        hidden_by="tray",
        reveals="the red stain came from dessert, not ink",
    ),
    "shoeprint": Clue(
        id="shoeprint",
        label="a small shoeprint",
        phrase="a small wet shoeprint near the door",
        hidden_by="rug",
        reveals="the kitchen door was opened in a hurry",
    ),
}

GIRL_NAMES = ["Mina", "Rosa", "Ivy", "Nora", "Lena"]
BOY_NAMES = ["Theo", "Eli", "Finn", "Noah", "Ari"]
ANDRO_NAMES = ["Rowan", "Quinn", "Sage", "Remy", "Avery"]
DETECTIVES = ["mother", "father", "girl", "boy", "androgynous"]


@dataclass
class StoryState:
    tension: float = 0.0
    suspicion: float = 0.0
    clue_found: bool = False
    culprit_named: bool = False


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world with dialogue and a maraschino clue.")
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy", "androgynous"])
    ap.add_argument("--detective-type", choices=DETECTIVES)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(loc, cul, clue) for loc in LOCATIONS for cul in CULPRITS for clue in CLUES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.location is None or c[0] == args.location)
              and (args.culprit is None or c[1] == args.culprit)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("No valid mystery matches the given options.")
    location, culprit, clue = rng.choice(sorted(combos))
    hero_type = args.hero_type or "androgynous"
    detective_type = args.detective_type or rng.choice(DETECTIVES)
    if hero_type == "androgynous":
        name = args.name or rng.choice(ANDRO_NAMES)
    elif hero_type == "girl":
        name = args.name or rng.choice(GIRL_NAMES)
    else:
        name = args.name or rng.choice(BOY_NAMES)
    return StoryParams(
        location=location,
        culprit=culprit,
        clue=clue,
        hero_name=name,
        hero_type=hero_type,
        detective_type=detective_type,
    )


def story_name(hero_type: str) -> str:
    return {"girl": "girl", "boy": "boy", "androgynous": "androgynous child"}[hero_type]


def detective_title(kind: str) -> str:
    return {"mother": "Mom", "father": "Dad", "girl": "the girl detective", "boy": "the boy detective",
            "androgynous": "the androgynous detective"}[kind]


def introduce(world: World, hero: Entity, detective: Entity) -> None:
    world.say(f"{hero.id} was an {story_name(hero.type)} with sharp eyes and a loud, curious heart.")
    world.say(f"At {world.location.label}, {hero.id} met {detective.label}, who liked asking careful questions.")


def incident(world: World, hero: Entity, culprit: Entity, clue: Clue, state: StoryState) -> None:
    world.para()
    hero.memes["bawl"] += 1
    hero.meters["noise"] += 1
    state.tension += 1
    world.say(f'The room went still when {hero.id} suddenly began to bawl. "My dessert is gone!" {hero.id} cried.')
    world.say(f'{detective_title(detective_type_of(hero))} said, "Who was near the cake table?"')
    culprit.memes["suspicion"] += 1
    world.say(f'{culprit.label.capitalize()} replied, "I was only near the tray. I did not take anything."')
    world.say(f"But on the table there was a {clue.phrase}, which looked terribly out of place.")


def detective_type_of(hero: Entity) -> str:
    return "androgynous"


def question_round(world: World, hero: Entity, culprit: Entity, clue: Clue, detective: Entity, state: StoryState) -> None:
    world.para()
    hero.meters["curiosity"] += 1
    state.suspicion += 1
    world.say(f'"Did anyone see a red shine?" {detective.label} asked.')
    world.say(f'{hero.id} sniffled. "I saw a bright red bit by the plate."')
    world.say(f'{culprit.label} said, "Maraschino cherries are red. That does not mean I stole it."')
    world.say(f'{detective.label} tapped the table and answered, "It means someone touched the dessert."')


def reveal(world: World, hero: Entity, culprit: Entity, clue: Clue, detective: Entity, state: StoryState) -> None:
    world.para()
    clue.found = True
    state.clue_found = True
    world.say(f'{hero.id} pointed to the {clue.label}. "That was the clue!"')
    world.say(f'{detective.label} nodded. "The cherry was stuck to your sleeve, {culprit.label}."')
    world.say(f'{culprit.label} sighed. "All right. I took the top cherry because I thought no one would notice."')
    state.culprit_named = True
    culprit.memes["confidence"] -= 1
    culprit.memes["comfort"] += 1


def end(world: World, hero: Entity, culprit: Entity, clue: Clue, detective: Entity, state: StoryState) -> None:
    world.para()
    hero.memes["bawl"] = 0
    hero.meters["noise"] = 0
    hero.memes["relief"] = 1
    world.say(f'{detective.label} returned the dessert and said, "A mystery can be solved without shouting."')
    world.say(f"{hero.id} stopped bawling, wiped {hero.pronoun('possessive')} face, and smiled at the repaired plate.")
    world.say(f"By the end, the maraschino cherry was back on top, and the odd little room felt calm again.")


def tell(params: StoryParams) -> World:
    location = LOCATIONS[params.location]
    world = World(location)

    hero = world.add_entity(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={k: 0.0 for k in METER_KEYS},
        memes={k: 0.0 for k in MEME_KEYS},
    ))
    detective = world.add_entity(Entity(
        id="detective",
        kind="character",
        type=params.detective_type if params.detective_type != "androgynous" else "androgynous",
        label=detective_title(params.detective_type),
        meters={k: 0.0 for k in METER_KEYS},
        memes={k: 0.0 for k in MEME_KEYS},
    ))
    culprit = world.add_entity(Entity(
        id=params.culprit,
        kind="character",
        type=params.culprit,
        label=f"the {params.culprit}",
        meters={k: 0.0 for k in METER_KEYS},
        memes={k: 0.0 for k in MEME_KEYS},
    ))
    clue = world.add_clue(CLUES[params.clue])

    world.facts.update(hero=hero, detective=detective, culprit=culprit, clue=clue, location=location)

    introduce(world, hero, detective)
    incident(world, hero, culprit, clue, StoryState())
    question_round(world, hero, culprit, clue, detective, StoryState())
    reveal(world, hero, culprit, clue, detective, StoryState())
    end(world, hero, culprit, clue, detective, StoryState())
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a child where {f["hero"].id} bawls after a dessert goes missing at {f["location"].label}.',
        f'Write a dialogue-driven mystery where a {f["hero"].type} notices a maraschino cherry clue and a {f["detective"].label} asks careful questions.',
        f'Write a simple story ending with the missing treat being explained and everyone calming down.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    culprit = f["culprit"]
    clue = f["clue"]
    detective = f["detective"]
    loc = f["location"].label
    return [
        QAItem(
            question=f"Why did {hero.id} bawl at {loc}?",
            answer=f"{hero.id} bawled because a dessert went missing, and the loss made the room feel upsetting and strange.",
        ),
        QAItem(
            question=f"What clue helped {detective.label} solve the mystery?",
            answer=f"The clue was {clue.phrase}, and it pointed to someone touching the dessert before the shouting started.",
        ),
        QAItem(
            question=f"Who finally admitted what happened?",
            answer=f"{culprit.label} admitted taking the top cherry and said no one would notice, but the clue gave it away.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The dessert was put back in order, {hero.id} stopped bawling, and the room felt calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a maraschino cherry?",
            answer="A maraschino cherry is a bright red sweet cherry often used on desserts and drinks.",
        ),
        QAItem(
            question="What does bawling mean?",
            answer="Bawling means crying very loudly.",
        ),
        QAItem(
            question="What is a whodunit story?",
            answer="A whodunit is a mystery story where the reader learns who did the wrongdoing by following clues.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:13}) meters={meters} memes={memes}")
    for c in world.clues.values():
        lines.append(f"  clue {c.id}: found={c.found} phrase={c.phrase}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
culprit(C) :- culprit_name(C).
clue(K) :- clue_name(K).
bawled(H) :- hero(H), incident(H).
found(K) :- clue(K), clue_reveals(K).
solved :- found(K), culprit(C), hero(H).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero_name", "hero"),
        asp.fact("culprit_name", "culprit"),
        asp.fact("clue_name", "maraschino"),
        asp.fact("incident", "hero"),
        asp.fact("clue_reveals", "maraschino"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show found/1. #show solved/0."))
    found = set(asp.atoms(model, "found"))
    if ("maraschino",) in found:
        print("OK: ASP gate recognizes the maraschino clue.")
        return 0
    print("Mismatch: ASP did not derive the expected clue fact.")
    return 1


def explain_rejection() -> str:
    return "(No story: this whodunit needs a location, a culprit, and a clue that can be discovered.)"


CURATED = [
    StoryParams(location="parlor", culprit="host", clue="maraschino", hero_name="Quinn", hero_type="androgynous", detective_type="androgynous"),
    StoryParams(location="library", culprit="guest", clue="napkin", hero_name="Avery", hero_type="androgynous", detective_type="mother"),
    StoryParams(location="garden_room", culprit="helper", clue="shoeprint", hero_name="Rowan", hero_type="androgynous", detective_type="father"),
]


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show found/1. #show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show found/1. #show solved/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.hero_name}: {p.location} / {p.culprit} / {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
