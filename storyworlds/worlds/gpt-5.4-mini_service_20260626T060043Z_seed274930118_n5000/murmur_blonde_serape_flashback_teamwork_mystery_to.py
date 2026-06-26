#!/usr/bin/env python3
"""
A small folk-tale storyworld about a mystery in a village, with a flashback,
teamwork, and a gentle resolution.

The seed words are woven in naturally:
- murmur
- blonde
- serape

The story domain:
A blonde child in a village notices a missing serape near a market stall.
A murmur spreads, the child remembers a flashback about who last carried it,
and then a few helpers work together to solve the mystery.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    detail: str
    folks: list[str] = field(default_factory=list)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.place)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "traits": list(v.traits), "owner": v.owner,
            "caretaker": v.caretaker, "carried_by": v.carried_by,
            "meters": dict(v.meters), "memes": dict(v.memes),
        }) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        return clone


def meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def mind(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def set_meter(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = value


def set_mind(ent: Entity, key: str, value: float) -> None:
    ent.memes[key] = value


def add_mind(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def add_meter(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper_name: str
    elder_name: str
    seed: Optional[int] = None


PLACES = {
    "village_square": Place(
        name="the village square",
        detail="The old fountain sat in the middle of the square, and the market stalls stood in a bright ring around it.",
        folks=["stalls", "fountain", "lanterns"],
    ),
    "river_market": Place(
        name="the river market",
        detail="The river market had woven baskets, wooden benches, and a little bridge where everyone stopped to talk.",
        folks=["baskets", "benches", "bridge"],
    ),
    "hillside_lane": Place(
        name="the hillside lane",
        detail="The hillside lane climbed past stone steps, porch doors, and garden walls covered in ivy.",
        folks=["stone steps", "porch doors", "ivy"],
    ),
}

HEROES = ["Lina", "Elsa", "Mara", "Nina", "Tessa"]
HELPERS = ["Pip", "Otto", "Bram", "Ivo", "Rami"]
ELDERS = ["Grandma", "Aunt Rose", "Old Ben", "Uncle Soren", "Nana"]
TRAITS = ["blonde", "bright-eyed", "quick-footed", "gentle", "curious"]

ASP_RULES = r"""
place(village_square).
place(river_market).
place(hillside_lane).

has_item(hero, serape).
needs_story(hero).
murmur_spreads :- missing(serape), crowded(placeX).
flashback_helpful :- murmur_spreads, remembered_clue.
teamwork_solves :- helper_joined, elder_joined, clue_shared.
mystery_solved :- teamwork_solves, serape_found.

#show mystery_solved/0.
#show teamwork_solves/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("missing", "serape"),
        asp.fact("crowded", "placeX"),
        asp.fact("remembered_clue"),
        asp.fact("helper_joined"),
        asp.fact("elder_joined"),
        asp.fact("clue_shared"),
        asp.fact("serape_found"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery_solved/0.\n#show teamwork_solves/0."))
    atoms = {(sym.name, len(sym.arguments)) for sym in model}
    ok = ("mystery_solved", 0) in atoms and ("teamwork_solves", 0) in atoms
    if ok:
        print("OK: ASP twin recognizes the mystery as solvable by teamwork.")
        return 0
    print("MISMATCH: ASP twin did not derive the expected story shape.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld: a murmur, a flashback, and teamwork solve a mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--elder")
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
    hero_name = args.name or rng.choice(HEROES)
    helper_name = args.helper or rng.choice([n for n in HELPERS if n != hero_name])
    elder_name = args.elder or rng.choice([n for n in ELDERS if n != hero_name and n != helper_name])
    return StoryParams(place=place, hero_name=hero_name, helper_name=helper_name, elder_name=elder_name)


def narrate_flashback(world: World, hero: Entity, serape: Entity, elder: Entity) -> None:
    hero.memes["memory"] = 1.0
    world.say(
        f"{hero.label} paused, and a flashback rose like mist: yesterday, {elder.label} had wrapped the blue serape around a bundle of bread."
    )
    world.say(
        f"{hero.label} remembered the cloth because {elder.label} had said, “This serape belongs to the market stall until the moon climbs high.”"
    )


def generate_mystery_solution(world: World, hero: Entity, helper: Entity, elder: Entity, serape: Entity) -> None:
    add_mind(hero, "worry", 1.0)
    add_mind(helper, "help", 1.0)
    add_mind(elder, "wisdom", 1.0)

    world.say(
        f"Then a murmur ran through the square, and soon everyone was whispering about the missing serape."
    )
    world.say(
        f"{hero.label} did not like the worry, so {hero.pronoun().capitalize()} called {helper.label} and {elder.label} to listen together."
    )
    world.say(
        f"{helper.label} looked near the fountain while {elder.label} checked the benches, and {hero.label} searched the stall ropes."
    )
    world.say(
        f"At last, the three of them found the serape caught on a lantern hook, fluttering softly in the wind like a sleeping flag."
    )
    world.say(
        f"{helper.label} laughed, {elder.label} smiled, and {hero.label} tied the serape back where it belonged, so the market could rest again."
    )
    set_mind(hero, "worry", 0.0)
    set_meter(serape, "found", 1.0)
    set_meter(serape, "safe", 1.0)


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type="girl",
        label=f"{params.hero_name} the blonde child",
        traits=["blonde", "kind", "curious"],
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="boy",
        label=params.helper_name,
        traits=["helpful", "quick"],
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type="woman",
        label=params.elder_name,
        traits=["wise", "gentle"],
    ))
    serape = world.add(Entity(
        id="serape",
        kind="thing",
        type="cloth",
        label="serape",
        phrase="a woven blue serape",
        owner="market",
        caretaker=elder.id,
    ))

    world.say(f"Long ago, in {place.name}, {hero.label} lived among the stall-keepers and song-sellers.")
    world.say(
        f"{hero.label} loved the {place.name} because it was lively, and {hero.pronoun('possessive')} favorite thing was the bright serape that hung near the bread stall."
    )
    world.say(place.detail)

    world.para()
    world.say(
        f"One morning, the serape was gone, and the people began to murmur."
    )
    narrate_flashback(world, hero, serape, elder)

    world.para()
    generate_mystery_solution(world, hero, helper, elder, serape)

    world.facts.update(
        place=place,
        hero=hero,
        helper=helper,
        elder=elder,
        serape=serape,
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a folk-tale style story with a murmur, a flashback, and teamwork that solves a small mystery.",
        f"Tell a gentle village story about {f['hero'].label} the blonde child, a missing serape, and helpers who work together.",
        "Write a short story for children where a clue from memory helps a community find a lost cloth and restore peace.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    elder: Entity = f["elder"]
    serape: Entity = f["serape"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label}, who was a blonde child in {place.name}.",
        ),
        QAItem(
            question=f"What mystery did the people notice in {place.name}?",
            answer=f"Their serape was missing, and that made the people murmur and wonder where it had gone.",
        ),
        QAItem(
            question=f"What helped {hero.label} remember the clue?",
            answer=f"A flashback came to mind, and {elder.label}'s words helped {hero.label} remember seeing the serape before.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"{hero.label}, {helper.label}, and {elder.label} worked together, found the serape on a lantern hook, and put it back where it belonged.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"The serape was safe again, the murmur quieted down, and the village square felt calm and tidy.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    place: Place = world.facts["place"]
    return [
        QAItem(
            question="What is a serape?",
            answer="A serape is a long piece of cloth or a shawl that people can wear around their shoulders.",
        ),
        QAItem(
            question="What is a murmur?",
            answer="A murmur is a soft, low whispering sound made by many people speaking quietly together.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and share the work so they can solve a problem together.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a moment when the story briefly remembers something that happened earlier.",
        ),
        QAItem(
            question=f"What kind of place was {place.name}?",
            answer=f"It was a busy village place with stalls, paths, and neighbors who knew one another well.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story QA ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        parts = []
        if e.label:
            parts.append(f"label={e.label}")
        if e.traits:
            parts.append(f"traits={e.traits}")
        if e.owner:
            parts.append(f"owner={e.owner}")
        if e.caretaker:
            parts.append(f"caretaker={e.caretaker}")
        if e.carried_by:
            parts.append(f"carried_by={e.carried_by}")
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {', '.join(parts)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_facts_text() -> str:
    return asp_facts()


def asp_validity_check() -> bool:
    import asp
    model = asp.one_model(asp_program("#show mystery_solved/0.\n#show teamwork_solves/0."))
    names = {sym.name for sym in model}
    return "mystery_solved" in names and "teamwork_solves" in names


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery_solved/0.\n#show teamwork_solves/0."))
        return
    if args.verify:
        sys.exit(0 if asp_verify() == 0 else 1)
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery_solved/0.\n#show teamwork_solves/0."))
        print("ASP model:", " ".join(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    seen: set[str] = set()

    if args.all:
        curated = [
            StoryParams("village_square", "Lina", "Pip", "Grandma"),
            StoryParams("river_market", "Mara", "Bram", "Aunt Rose"),
            StoryParams("hillside_lane", "Elsa", "Ivo", "Old Ben"),
        ]
        samples = [generate(p) for p in curated]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

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
