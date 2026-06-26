#!/usr/bin/env python3
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Animal:
    id: str
    species: str
    name: str
    role: str
    home: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"tired": 0.0, "scared": 0.0, "found": 0.0, "helped": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"curious": 0.0, "worry": 0.0, "relief": 0.0, "joy": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def article_name(self) -> str:
        return f"{self.name} the {self.species}"


@dataclass
class Place:
    name: str
    outer: bool = False
    clues: list[str] = field(default_factory=list)
    hiding_spots: list[str] = field(default_factory=list)
    ambient: str = ""


@dataclass
class Mystery:
    id: str
    missing: str
    clue: str
    hidden_where: str
    solving_tool: str
    solve_verb: str
    reveal: str


class World:
    def __init__(self, place: Place, mystery: Mystery) -> None:
        self.place = place
        self.mystery = mystery
        self.animals: dict[str, Animal] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.found_clue = False
        self.revealed = False
        self.resolved = False

    def add(self, animal: Animal) -> Animal:
        self.animals[animal.id] = animal
        return animal

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "orchard_edge": Place(
        name="the outer edge of the orchard",
        outer=True,
        clues=["a shiny feather", "tiny paw prints", "a snapped berry stem"],
        hiding_spots=["under a low bush", "behind a basket", "in a hollow log"],
        ambient="The breeze stirred the tall grass beyond the fence.",
    ),
    "pond_bank": Place(
        name="the outer bank of the pond",
        outer=True,
        clues=["a silver ribbon", "muddy steps", "a curled reed"],
        hiding_spots=["under a lily leaf", "beside a stone", "in the reeds"],
        ambient="The water made soft rings near the shore.",
    ),
    "barn_yard": Place(
        name="the outer barn yard",
        outer=True,
        clues=["a yellow button", "a straw scrap", "a tiny hoof mark"],
        hiding_spots=["behind a bucket", "under the porch", "near the hay pile"],
        ambient="The yard smelled warm and sweet from the hay.",
    ),
    "woodland_path": Place(
        name="the outer woodland path",
        outer=True,
        clues=["a pine cone cap", "a leaf with a bite mark", "a bright pebble"],
        hiding_spots=["under roots", "behind a stump", "in moss"],
        ambient="Sunlight blinked through the branches along the path.",
    ),
}

MYSTERIES = {
    "missing_lunch": Mystery(
        id="missing_lunch",
        missing="a picnic lunch",
        clue="a trail of crumbs",
        hidden_where="under the striped blanket",
        solving_tool="a careful sniff",
        solve_verb="followed",
        reveal="the lunch had been tucked safely away by mistake",
    ),
    "missing_bell": Mystery(
        id="missing_bell",
        missing="a little bell",
        clue="a tiny ring in the dirt",
        hidden_where="inside the nest",
        solving_tool="a gentle look through the reeds",
        solve_verb="searched",
        reveal="the bell had rolled into a nest of soft leaves",
    ),
    "missing_hat": Mystery(
        id="missing_hat",
        missing="a red hat",
        clue="a red thread caught on bark",
        hidden_where="behind the berry basket",
        solving_tool="a careful paw under the basket",
        solve_verb="peeked",
        reveal="the hat had slipped behind the basket and waited there all morning",
    ),
    "missing_sock": Mystery(
        id="missing_sock",
        missing="a tiny sock",
        clue="one lonely sock-print in the mud",
        hidden_where="in the warm hay",
        solving_tool="a patient dig through the hay",
        solve_verb="dug",
        reveal="the sock had landed in the hay pile and stayed snug and dry",
    ),
}

ANIMALS = [
    ("rabbit", "Pip", "small", "brave"),
    ("fox", "Mina", "quick", "gentle"),
    ("bear", "Toby", "round", "patient"),
    ("mouse", "Nell", "tiny", "curious"),
    ("otter", "Ravi", "sleek", "bright"),
    ("deer", "Luna", "graceful", "kind"),
]

HELPERS = [
    ("squirrel", "Sally"),
    ("hedgehog", "Hugo"),
    ("duck", "Dara"),
    ("beaver", "Bram"),
]


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    hero_species: str
    helper_name: str
    helper_species: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mystery is solvable when the place has at least one clue and one hiding spot.
solvable(M) :- mystery(M), clue_for(M,_), hide_for(M,_).

% A happy ending is possible when a helper exists and the clue can be found.
happy(M) :- solvable(M), helper(_), clue_found(M), reveal(M,_).

#show solvable/1.
#show happy/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.outer:
            lines.append(asp.fact("outer", pid))
        for c in p.clues:
            lines.append(asp.fact("clue", pid, c))
        for h in p.hiding_spots:
            lines.append(asp.fact("hide", pid, h))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid, m.missing))
        lines.append(asp.fact("solve_tool", mid, m.solving_tool))
        lines.append(asp.fact("reveal", mid, m.reveal))
        lines.append(asp.fact("clue_for", mid, m.clue))
        lines.append(asp.fact("hide_for", mid, m.hidden_where))
    for sp, nm in HELPERS:
        lines.append(asp.fact("helper_kind", sp, nm))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_checks() -> tuple[set[str], set[str]]:
    import asp
    model = asp.one_model(asp_program("#show solvable/1.\n#show happy/1."))
    solvable = {args[0] for args in asp.atoms(model, "solvable")}
    happy = {args[0] for args in asp.atoms(model, "happy")}
    return solvable, happy


def python_reasonable(place: Place, mystery: Mystery) -> bool:
    return place.outer and bool(place.clues) and bool(place.hiding_spots) and bool(mystery.clue) and bool(mystery.hidden_where)


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def intro(world: World, hero: Animal, helper: Animal, mystery: Mystery) -> None:
    world.say(
        f"{hero.article_name()} lived near {world.place.name} and was known for a curious nose and a kind heart."
    )
    world.say(
        f"One morning, {hero.name} noticed that {mystery.missing} was gone, and that made {hero.pronoun('object')} frown."
    )
    world.say(
        f"{helper.article_name()} hurried over and said they would help solve the mystery together."
    )
    hero.memes["curious"] += 1
    helper.meters["helped"] += 1
    world.facts.update(hero=hero, helper=helper, mystery=mystery)


def search(world: World, hero: Animal, helper: Animal, mystery: Mystery) -> None:
    world.para()
    world.say(world.place.ambient)
    world.say(
        f"{hero.name} {mystery.solve_verb} the clues one by one, starting with {mystery.clue}."
    )
    world.say(
        f"{helper.name} used {mystery.solving_tool} and helped look in {world.place.hiding_spots[0]}."
    )
    hero.meters["found"] += 1
    hero.memes["worry"] += 1


def turn(world: World, hero: Animal, helper: Animal, mystery: Mystery) -> None:
    world.para()
    world.say(
        f"At first, the trail seemed to stop, and {hero.name} felt a small wobble of worry."
    )
    world.say(
        f"Then {helper.name} spotted a clue near {world.place.hiding_spots[1]} and called {hero.name} back."
    )
    world.say(
        f"Together they looked more carefully, because patient eyes can notice what hurried eyes miss."
    )
    hero.meters["tired"] += 1
    hero.memes["worry"] += 1


def resolve(world: World, hero: Animal, helper: Animal, mystery: Mystery) -> None:
    world.para()
    world.say(
        f"Finally, {hero.name} {mystery.solve_verb} into {mystery.hidden_where} and found {mystery.missing}."
    )
    world.say(
        f"It was right where it had been tucked away, and that solved the whole mystery."
    )
    world.say(
        f"{helper.name} laughed with relief, and {hero.name} bounced happily beside {helper.pronoun('object')}."
    )
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.revealed = True
    world.resolved = True


def tell(place: Place, mystery: Mystery, hero_name: str, hero_species: str, helper_name: str, helper_species: str) -> World:
    world = World(place, mystery)
    hero = world.add(Animal(id="hero", species=hero_species, name=hero_name, role="hero", home=place.name, traits=["curious", "kind"]))
    helper = world.add(Animal(id="helper", species=helper_species, name=helper_name, role="helper", home=place.name, traits=["helpful", "patient"]))

    intro(world, hero, helper, mystery)
    search(world, hero, helper, mystery)
    turn(world, hero, helper, mystery)
    resolve(world, hero, helper, mystery)

    world.facts.update(place=place, resolved=world.resolved)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero: Animal = world.facts["hero"]
    helper: Animal = world.facts["helper"]
    mystery: Mystery = world.facts["mystery"]
    return [
        f'Write a short animal story set at {world.place.name} where {hero.name} and {helper.name} solve a mystery and end happy.',
        f"Tell a gentle outer-story about {hero.name} the {hero.species} finding {mystery.missing} with help from {helper.name} the {helper.species}.",
        f'Write a child-friendly story with the word "outer" in it, where animals use clues to solve a mystery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Animal = world.facts["hero"]
    helper: Animal = world.facts["helper"]
    mystery: Mystery = world.facts["mystery"]
    place: Place = world.facts["place"]
    return [
        QAItem(
            question=f"Who was looking for {mystery.missing}?",
            answer=f"{hero.name} the {hero.species} was looking for {mystery.missing} at {place.name}.",
        ),
        QAItem(
            question=f"Who helped {hero.name} solve the mystery?",
            answer=f"{helper.name} the {helper.species} helped by looking carefully and following the clue.",
        ),
        QAItem(
            question=f"What clue did the animals notice first?",
            answer=f"They noticed {mystery.clue}, which led them closer to the answer.",
        ),
        QAItem(
            question=f"Where was {mystery.missing} found?",
            answer=f"It was found {mystery.hidden_where}, which matched the careful search they made.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The mystery was solved, the missing thing was found, and both animals felt happy at the end.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "outer": [
        QAItem(
            question="What does outer mean in a place like an outer path or outer yard?",
            answer="Outer means near the outside edge of a place, not deep inside it.",
        )
    ],
    "clue": [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps you figure out an answer.",
        )
    ],
    "mystery": [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not known at first, so you have to look for clues to solve it.",
        )
    ],
    "happy": [
        QAItem(
            question="What does a happy ending mean?",
            answer="A happy ending means the problem gets solved and the story finishes in a good way.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    if world.place.outer:
        out.extend(WORLD_KNOWLEDGE["outer"])
    out.extend(WORLD_KNOWLEDGE["clue"])
    out.extend(WORLD_KNOWLEDGE["mystery"])
    out.extend(WORLD_KNOWLEDGE["happy"])
    return out


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


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal mystery storyworld with an outer setting and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_key = args.place or rng.choice([k for k, v in PLACES.items() if v.outer])
    mystery_key = args.mystery or rng.choice(list(MYSTERIES))
    place = PLACES[place_key]
    mystery = MYSTERIES[mystery_key]
    if not python_reasonable(place, mystery):
        raise StoryError("The requested place and mystery do not form a reasonable outer mystery story.")
    hero_species, hero_name, _, _ = rng.choice(ANIMALS)
    helper_species, helper_name = rng.choice(HELPERS)
    return StoryParams(
        place=place_key,
        mystery=mystery_key,
        hero_name=hero_name,
        hero_species=hero_species,
        helper_name=helper_name,
        helper_species=helper_species,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        MYSTERIES[params.mystery],
        params.hero_name,
        params.hero_species,
        params.helper_name,
        params.helper_species,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"place={world.place.name}")
    lines.append(f"mystery={world.mystery.id}")
    for a in world.animals.values():
        meters = {k: v for k, v in a.meters.items() if v}
        memes = {k: v for k, v in a.memes.items() if v}
        lines.append(f"  {a.name} the {a.species}: meters={meters} memes={memes}")
    lines.append(f"resolved={world.resolved}")
    return "\n".join(lines)


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
    solvable, happy = asp_checks()
    py_solvable = {mid for mid, place in PLACES.items() if place.outer and place.clues and place.hiding_spots and mid in MYSTERIES}
    py_happy = set(py_solvable)
    if solvable == py_solvable and happy == py_happy:
        print(f"OK: ASP parity check passed ({len(solvable)} solvable, {len(happy)} happy).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("ASP solvable:", sorted(solvable))
    print("PY solvable:", sorted(py_solvable))
    print("ASP happy:", sorted(happy))
    print("PY happy:", sorted(py_happy))
    return 1


CURATED = [
    StoryParams(place="orchard_edge", mystery="missing_lunch", hero_name="Pip", hero_species="rabbit", helper_name="Sally", helper_species="squirrel"),
    StoryParams(place="pond_bank", mystery="missing_bell", hero_name="Mina", hero_species="fox", helper_name="Dara", helper_species="duck"),
    StoryParams(place="barn_yard", mystery="missing_hat", hero_name="Toby", hero_species="bear", helper_name="Bram", helper_species="beaver"),
    StoryParams(place="woodland_path", mystery="missing_sock", hero_name="Nell", hero_species="mouse", helper_name="Hugo", helper_species="hedgehog"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show solvable/1.\n#show happy/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solvable/1.\n#show happy/1."))
        print("solvable:", sorted(set(asp.atoms(model, "solvable"))))
        print("happy:", sorted(set(asp.atoms(model, "happy"))))
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.hero_name} the {p.hero_species}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
