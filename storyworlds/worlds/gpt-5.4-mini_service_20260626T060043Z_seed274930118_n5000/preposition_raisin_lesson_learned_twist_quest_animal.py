#!/usr/bin/env python3
"""
A standalone story world: an animal story built around a preposition lesson,
a raisin, a quest, a twist, and a learned lesson.

The seed premise:
- A small animal wants to reach a raisin.
- The path depends on prepositions: in, on, under, over, through, beside.
- A twist complicates the quest.
- The story ends with a lesson learned and a concrete change in state.
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
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"mouse", "rat", "hamster"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    label: str
    kind: str = "garden"
    affordances: set[str] = field(default_factory=set)


@dataclass
class Route:
    id: str
    preposition: str
    obstacle: str
    approach: str
    result: str
    twist: str
    lesson: str
    path_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str = "raisin"
    phrase: str = "a shiny raisin"
    location: str = "under the leaf"


@dataclass
class StoryParams:
    place: str
    route: str
    animal: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.trace: list[str] = []

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "garden": Place(label="the garden", kind="garden", affordances={"under", "over", "beside", "through"}),
    "barnyard": Place(label="the barnyard", kind="yard", affordances={"under", "over", "beside"}),
    "orchard": Place(label="the orchard", kind="orchard", affordances={"in", "under", "beside", "through"}),
    "park": Place(label="the park", kind="park", affordances={"on", "under", "beside", "through"}),
}

ANIMALS = {
    "mouse": {"type": "mouse", "name": "Milo", "traits": ["small", "curious"]},
    "rabbit": {"type": "rabbit", "name": "Ruby", "traits": ["quick", "brave"]},
    "squirrel": {"type": "squirrel", "name": "Sunny", "traits": ["busy", "thoughtful"]},
    "hedgehog": {"type": "hedgehog", "name": "Holly", "traits": ["careful", "gentle"]},
}

ROUTES = {
    "under_log": Route(
        id="under_log",
        preposition="under",
        obstacle="a fallen log",
        approach="crawl under the log",
        result="reached the raisin",
        twist="The log was lower than it looked, so the animal had to slow down and squeeze flat.",
        lesson="The best way under something is to go slow and keep your belly low.",
        path_word="under",
        tags={"under", "log"},
    ),
    "over_stump": Route(
        id="over_stump",
        preposition="over",
        obstacle="a round stump",
        approach="hop over the stump",
        result="got to the raisin",
        twist="A beetle crossed the stump at the same time, which made the hop turn into a careful tiptoe.",
        lesson="Sometimes over means taking one small step at a time.",
        path_word="over",
        tags={"over", "stump"},
    ),
    "through_grass": Route(
        id="through_grass",
        preposition="through",
        obstacle="tall grass",
        approach="push through the grass",
        result="found the raisin",
        twist="The grass tickled the whiskers so much that the animal had to stop and laugh.",
        lesson="Going through a place is easier when you know it is okay to pause and try again.",
        path_word="through",
        tags={"through", "grass"},
    ),
    "beside_pond": Route(
        id="beside_pond",
        preposition="beside",
        obstacle="a little pond",
        approach="walk beside the pond",
        result="spotted the raisin",
        twist="A duck splashed beside the path, so the animal learned to keep a little space.",
        lesson="Beside means next to, not into, and that keeps a traveler safe.",
        path_word="beside",
        tags={"beside", "pond"},
    ),
}

RAISIN = Prize(id="raisin")
LESSONS = {
    "under": "under means below something",
    "over": "over means above something",
    "through": "through means moving inside a space from one side to the other",
    "beside": "beside means next to something",
}


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def choose_name(animal_id: str) -> str:
    return ANIMALS[animal_id]["name"]


def choose_traits(animal_id: str) -> list[str]:
    return list(ANIMALS[animal_id]["traits"])


def setup_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.route not in ROUTES:
        raise StoryError("Unknown route.")
    if params.animal not in ANIMALS:
        raise StoryError("Unknown animal.")

    place = PLACES[params.place]
    route = ROUTES[params.route]
    animal = ANIMALS[params.animal]

    if route.preposition not in place.affordances:
        raise StoryError(
            f"This place does not support a story about going {route.preposition} something."
        )

    world = World(place)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=animal["type"],
        label=choose_name(params.animal),
    ))
    prize = world.add(Entity(
        id="raisin",
        type="raisin",
        label="raisin",
        location=f"{route.preposition} the {params.place}",
    ))
    world.facts = {
        "hero": hero,
        "prize": prize,
        "route": route,
        "place": place,
        "animal": animal,
    }
    return world


def intro(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    animal = world.facts["animal"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    world.say(
        f"{hero.label} was a {animal['traits'][0]} little {animal['type']} who loved exploring {place.label}."
    )
    world.say(
        f"One morning, {hero.label} found a tiny raisin and wanted to keep the whole quest simple: just get to the raisin and bring it home."
    )


def quest(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    route: Route = world.facts["route"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    world.para()
    world.say(
        f"{hero.label} looked at {route.obstacle} in {place.label} and decided to go {route.preposition} it."
    )
    world.say(
        f"The plan was to {route.approach}, because the raisin was waiting on the other side."
    )


def twist(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    route: Route = world.facts["route"]  # type: ignore[assignment]
    prize: Entity = world.facts["prize"]  # type: ignore[assignment]
    world.para()
    world.say(route.twist)
    world.say(
        f"For a moment, {hero.label} thought the raisin might be too hard to reach, but then {hero.pronoun()} noticed a safer way."
    )
    world.facts["twist"] = True
    world.facts["lesson_hint"] = LESSONS[route.preposition]


def resolve(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    route: Route = world.facts["route"]  # type: ignore[assignment]
    prize: Entity = world.facts["prize"]  # type: ignore[assignment]
    world.para()
    world.say(
        f"{hero.label} tried again, this time remembering what {route.preposition} meant."
    )
    world.say(
        f"{hero.label} followed the path {route.preposition} the obstacle, {route.result}, and picked up the raisin with a happy grin."
    )
    world.say(
        f"Then {hero.label} carried it home and said, '{route.lesson}'"
    )
    world.say(
        f"The little raisin stayed safe, and {hero.label} learned that a good preposition can show the right way."
    )
    world.facts["resolved"] = True
    world.facts["prize_home"] = True
    prize.location = "home in the hero's paw"


def tell_story(params: StoryParams) -> World:
    world = setup_world(params)
    intro(world)
    quest(world)
    twist(world)
    resolve(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    route: Route = world.facts["route"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    return [
        f"Write an animal story for a young child about {hero.label} and a raisin in {place.label}, using the preposition '{route.preposition}'.",
        f"Tell a gentle quest story where a little {hero.type} learns what it means to go {route.preposition} something.",
        f"Write a short story with a twist and a lesson learned about finding a raisin by going {route.preposition} an obstacle.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    route: Route = world.facts["route"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    prize: Entity = world.facts["prize"]  # type: ignore[assignment]
    qa = [
        QAItem(
            question=f"Who went on the quest in {place.label}?",
            answer=f"{hero.label}, a little {hero.type}, went on the quest in {place.label}.",
        ),
        QAItem(
            question=f"What was {hero.label} trying to find?",
            answer=f"{hero.label} was trying to find a raisin.",
        ),
        QAItem(
            question=f"What preposition did the story teach?",
            answer=f"The story taught '{route.preposition}', which means {LESSONS[route.preposition]}.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=route.twist,
        ),
        QAItem(
            question=f"What lesson did {hero.label} learn at the end?",
            answer=route.lesson,
        ),
        QAItem(
            question=f"Where did the raisin end up?",
            answer=f"The raisin ended up home in {hero.label}'s paw.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    route: Route = world.facts["route"]  # type: ignore[assignment]
    tag_qas = {
        "under": QAItem(question="What does under mean?", answer="Under means below something."),
        "over": QAItem(question="What does over mean?", answer="Over means above something."),
        "through": QAItem(question="What does through mean?", answer="Through means moving inside a space from one side to the other."),
        "beside": QAItem(question="What does beside mean?", answer="Beside means next to something."),
    }
    return [tag_qas[route.preposition], QAItem(question="What is a raisin?", answer="A raisin is a dried grape. It is small, wrinkly, and sweet.")]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(X) :- animal(X).
route(R) :- route_id(R).
place(P) :- place_id(P).

allowed(P,R) :- place_affords(P,Prep), route_preposition(R,Prep).
questable(P,R) :- allowed(P,R), route_twist(R,_), route_lesson(R,_).

#show allowed/2.
#show questable/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place_id", pid))
        for prep in sorted(PLACES[pid].affordances):
            lines.append(asp.fact("place_affords", pid, prep))
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route_id", rid))
        lines.append(asp.fact("route_preposition", rid, route.preposition))
        lines.append(asp.fact("route_twist", rid, route.twist))
        lines.append(asp.fact("route_lesson", rid, route.lesson))
    for aid, animal in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    allowed = set(asp.atoms(model, "allowed"))
    questable = set(asp.atoms(model, "questable"))
    py_allowed = {
        (p, r)
        for p, place in PLACES.items()
        for r, route in ROUTES.items()
        if route.preposition in place.affordances
    }
    py_questable = py_allowed
    if allowed == py_allowed and questable == py_questable:
        print(f"OK: ASP parity verified ({len(py_allowed)} allowed routes).")
        return 0
    print("MISMATCH between ASP and Python.")
    if allowed != py_allowed:
        print(" allowed only in ASP:", sorted(allowed - py_allowed))
        print(" allowed only in Python:", sorted(py_allowed - allowed))
    if questable != py_questable:
        print(" questable only in ASP:", sorted(questable - py_questable))
        print(" questable only in Python:", sorted(py_questable - questable))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about a raisin, a quest, and a preposition lesson.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--route", choices=sorted(ROUTES))
    ap.add_argument("--animal", choices=sorted(ANIMALS))
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
    combos = []
    for place, pobj in PLACES.items():
        if args.place and place != args.place:
            continue
        for route, robj in ROUTES.items():
            if args.route and route != args.route:
                continue
            if robj.preposition not in pobj.affordances:
                continue
            for animal in ANIMALS:
                if args.animal and animal != args.animal:
                    continue
                combos.append((place, route, animal))
    if not combos:
        raise StoryError("No valid story matches those options.")
    place, route, animal = rng.choice(sorted(combos))
    return StoryParams(place=place, route=route, animal=animal)


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} label={e.label} location={e.location}")
    lines.append(f"place={world.place.label}")
    lines.append(f"facts={sorted(world.facts.keys())}")
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


CURATED = [
    StoryParams(place="garden", route="under_log", animal="mouse"),
    StoryParams(place="orchard", route="through_grass", animal="squirrel"),
    StoryParams(place="park", route="over_stump", animal="rabbit"),
    StoryParams(place="barnyard", route="beside_pond", animal="hedgehog"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        allowed = sorted(set(asp.atoms(model, "allowed")))
        questable = sorted(set(asp.atoms(model, "questable")))
        print(f"{len(allowed)} allowed routes, {len(questable)} questable pairs")
        for a in allowed:
            print("allowed", a)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.animal} at {p.place} via {p.route}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
