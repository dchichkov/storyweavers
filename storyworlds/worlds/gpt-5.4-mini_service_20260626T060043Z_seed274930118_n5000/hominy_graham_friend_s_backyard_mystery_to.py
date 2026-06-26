#!/usr/bin/env python3
"""
A small fairy-tale storyworld about Hominy and Graham solving a backyard mystery
with careful problem solving.

The seed tale behind this world:
- Hominy visits friend Graham in a backyard that feels a little magical.
- Something mysterious goes missing: a shiny little spoon, a ribbon, or a toy.
- The children look for clues, ask gentle questions, and test ideas.
- They solve the mystery by noticing a hidden place and helping each other.

The world model tracks:
- physical state: where objects are, whether they are hidden, and what clues
  have been found
- emotional state: curiosity, worry, relief, pride, and friendship

This script follows the Storyweavers contract and includes an ASP twin.
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


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    label: str = ""
    type: str = ""
    plural: bool = False
    owner: Optional[str] = None
    location: str = ""
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    mood: str
    features: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    clue_word: str
    hiding_places: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str = "friend_backyard"
    mystery: str = "missing_spoon"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------

class World:
    def __init__(self, place: Place, mystery: Mystery) -> None:
        self.place = place
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
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
        import copy
        w = World(self.place, self.mystery)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "friend_backyard": Place(
        id="friend_backyard",
        label="a friend's backyard",
        mood="gentle and a little magical",
        features={"hedge", "flowerbed", "bench", "shed", "tree", "path"},
    ),
}

MYSTERIES = {
    "missing_spoon": Mystery(
        id="missing_spoon",
        label="a tiny silver spoon",
        clue_word="shine",
        hiding_places={"flowerbed", "bench", "shed"},
    ),
    "missing_ribbon": Mystery(
        id="missing_ribbon",
        label="a blue ribbon",
        clue_word="flutter",
        hiding_places={"hedge", "tree", "bench"},
    ),
    "missing_cookie": Mystery(
        id="missing_cookie",
        label="a honey cookie",
        clue_word="crumb",
        hiding_places={"path", "flowerbed", "shed"},
    ),
}

CHARACTER_NAMES = ["Hominy", "Graham"]
TRAITS = ["curious", "brave", "gentle", "thoughtful", "cheerful"]

# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def mystery_is_reasonable(place: Place, mystery: Mystery) -> bool:
    return place.id == "friend_backyard" and bool(mystery.hiding_places)


def explain_rejection(place: Place, mystery: Mystery) -> str:
    return (
        f"(No story: this mystery does not fit {place.label}. "
        f"Try the backyard mystery with a hidden object that could plausibly be found there.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mystery is solvable when it has at least one hiding place in the backyard.
solvable(M) :- mystery(M), hide(M, _).

% A clue can be found if it points to a place and that place exists.
findable(M, P) :- clue(M, P), place(P).

% A valid fairy-tale backyard mystery is one that is solvable and findable.
valid_story(P, M) :- place(P), mystery(M), solvable(M), findable(M, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for feat in sorted(p.features):
            lines.append(asp.fact("feature", pid, feat))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.clue_word))
        for hp in sorted(m.hiding_places):
            lines.append(asp.fact("hide", mid, hp))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = sorted((p.id, m.id) for p in PLACES.values() for m in MYSTERIES.values() if mystery_is_reasonable(p, m))
    asp_set = asp_valid_stories()
    asp_pairs = sorted((a, b) for (a, b) in asp_set)
    if py == asp_pairs:
        print(f"OK: clingo gate matches Python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("  python:", py)
    print("  clingo:", asp_pairs)
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def intro_line(hero: Entity, friend: Entity, place: Place) -> str:
    return (
        f"Hominy and Graham were friends, and one soft afternoon they met in {place.label}, "
        f"where the air felt {place.mood}."
    )


def mystery_setup_line(hero: Entity, friend: Entity, mystery: Entity) -> str:
    return (
        f"Then Graham noticed that {mystery.label} was gone, and that made both friends very curious."
    )


def clue_line(mystery: Entity, clue_place: str) -> str:
    clue_map = {
        "shine": "a glint of light",
        "flutter": "a little fluttering shape",
        "crumb": "a tiny trail of crumbs",
    }
    return f"Near the {clue_place}, they spotted {clue_map.get(mystery.type, 'a clue')}."


def resolution_line(hero: Entity, friend: Entity, mystery: Entity, place: Place) -> str:
    return (
        f"At last, Hominy and Graham looked under the {mystery.location} and found {mystery.label} tucked safely away. "
        f"They laughed, because the mystery had been solved by patient looking, careful thinking, and friendship."
    )


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(place, mystery)

    hominy = world.add(Entity(
        id="Hominy",
        kind="character",
        label="Hominy",
        type="child",
        meters={},
        memes={"curiosity": 2.0, "kindness": 2.0},
    ))
    graham = world.add(Entity(
        id="Graham",
        kind="character",
        label="Graham",
        type="child",
        meters={},
        memes={"curiosity": 2.0, "care": 2.0},
    ))
    object_ent = world.add(Entity(
        id=mystery.id,
        kind="thing",
        label=mystery.label,
        type="mystery_object",
        location="hidden",
        hidden=True,
        owner="Graham",
    ))
    # Pick a hiding place deterministically from the seeded params
    object_ent.location = sorted(mystery.hiding_places)[0]

    world.facts.update(
        hero=hominy,
        friend=graham,
        mystery=object_ent,
        place=place,
        mystery_cfg=mystery,
        solved=False,
        clue_found=False,
        final_place=object_ent.location,
    )
    return world


def tell_story(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    mystery: Entity = world.facts["mystery"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    mystery_cfg: Mystery = world.facts["mystery_cfg"]  # type: ignore[assignment]

    world.say(intro_line(hero, friend, place))
    world.say(mystery_setup_line(hero, friend, mystery))

    world.para()
    world.say(
        f"Hominy did not rush. Instead, {hero.id} asked, “Where did it last shine?”"
    )
    world.say(
        f"Graham thought hard and said the best clue might be near the {mystery.location}."
    )
    world.facts["clue_found"] = True
    world.facts["clue_place"] = mystery.location

    world.para()
    world.say(
        f"So the two friends began a little treasure hunt. They checked the {mystery.location}, "
        f"peeked by the bench, and looked behind the hedge."
    )
    world.say(
        f"Hominy noticed that the light from the spoon could hide in a dim place, so {hero.id} kept looking where shadows were soft."
    )

    world.para()
    mystery.hidden = False
    world.facts["solved"] = True
    world.say(resolution_line(hero, friend, mystery, place))
    world.say(
        f"From then on, Graham kept {mystery.label} on the table, and Hominy remembered that careful problem solving can turn a mystery into a happy ending."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    place: Place = world.facts["place"]  # type: ignore[assignment]
    mystery_cfg: Mystery = world.facts["mystery_cfg"]  # type: ignore[assignment]
    return [
        f"Write a fairy tale for a young child set in {place.label} where Hominy and Graham solve a small mystery.",
        f"Tell a gentle backyard story about {mystery_cfg.label} disappearing and two friends using problem solving to find it.",
        f"Write a short fairy tale in which Hominy notices clues, Graham remembers where something was seen last, and the mystery is solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    mystery: Entity = world.facts["mystery"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    mystery_cfg: Mystery = world.facts["mystery_cfg"]  # type: ignore[assignment]

    qas = [
        QAItem(
            question="Who were the two friends in the story?",
            answer=f"The friends were {hero.id} and {friend.id}.",
        ),
        QAItem(
            question="Where did the mystery happen?",
            answer=f"It happened in {place.label}.",
        ),
        QAItem(
            question=f"What was missing?",
            answer=f"Missing was {mystery.label}.",
        ),
        QAItem(
            question="How did they solve the mystery?",
            answer=(
                "They solved it by looking carefully, following a clue, and checking the hiding places one by one."
            ),
        ),
    ]
    if world.facts.get("clue_found"):
        qas.append(
            QAItem(
                question=f"What clue helped Hominy and Graham look in the right place?",
                answer=(
                    f"They listened for the clue about {mystery_cfg.clue_word}, and that helped them search near the {world.facts.get('clue_place')}."
                ),
            )
        )
    if world.facts.get("solved"):
        qas.append(
            QAItem(
                question="What changed by the end of the story?",
                answer=(
                    f"By the end, {mystery.label} was found, the worry was gone, and the two friends felt proud."
                ),
            )
        )
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    mystery_cfg: Mystery = world.facts["mystery_cfg"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not known right away, so people look for clues and try to figure it out.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking about a problem, trying ideas, and using clues until you find a good answer.",
        ),
        QAItem(
            question="Why are backyards good places to search?",
            answer="Backyards have many little hiding places like benches, flowerbeds, hedges, and sheds, so they can be good places for a search.",
        ),
        QAItem(
            question=f"What is special about {mystery_cfg.label}?",
            answer=(
                f"{mystery_cfg.label.capitalize()} is the kind of thing that can hide in a small place and be found again by careful looking."
            ),
        ),
        QAItem(
            question="What do friends do when they work together?",
            answer="Friends help each other, share ideas, and make a hard job easier.",
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.hidden:
            bits.append("hidden=True")
        if e.location:
            bits.append(f"location={e.location}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        lines.append(f"{e.id}: {e.kind} {e.label} {' '.join(bits)}")
    lines.append(f"facts: solved={world.facts.get('solved')} clue_found={world.facts.get('clue_found')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale backyard mystery storyworld.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--mystery", choices=MYSTERIES.keys())
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
    place = args.place or "friend_backyard"
    mystery = args.mystery or rng.choice(list(MYSTERIES.keys()))
    if not mystery_is_reasonable(PLACES[place], MYSTERIES[mystery]):
        raise StoryError(explain_rejection(PLACES[place], MYSTERIES[mystery]))
    return StoryParams(place=place, mystery=mystery)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="friend_backyard", mystery="missing_spoon"),
    StoryParams(place="friend_backyard", mystery="missing_ribbon"),
    StoryParams(place="friend_backyard", mystery="missing_cookie"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid story combos:")
        for place, mystery in combos:
            print(f"  {place:16} {mystery}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
