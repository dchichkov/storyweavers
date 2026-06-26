#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/bingo_fawn_scout_bad_ending_misunderstanding_surprise.py
====================================================================================================

A small slice-of-life story world about a scout, a bingo night, a fawn-shaped
surprise, and a misunderstanding that ends badly.

Seed tale:
---
Fawn loved going to the community hall with the scout troop on Friday nights.
The hall had bright lights, paper cups of juice, and big bingo boards. Fawn was
careful and quiet, because the scout leader said good scouts listen first and
speak kindly.

One night, Fawn found a little fawn figurine on the windowsill. Fawn thought it
was a prize left out for the winner of bingo. The scout leader thought Fawn was
trying to sneak a prize before the game ended. Nobody asked enough questions.
The room got awkward, the game stopped feeling fun, and the surprise turned into
a bad ending: the figurine belonged to the hall volunteer's child, and it broke
when someone knocked it off the sill.

Story model:
---
- typed entities with physical meters and emotional memes
- the scout's desire for bingo and the surprise object drive the turn
- misunderstanding raises tension
- the ending proves what changed: a broken figurine, a quiet hall, and a child
  who feels embarrassed instead of proud
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
# World model
# ---------------------------------------------------------------------------

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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"damage": 0.0, "mess": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "conflict": 0.0, "embarrassment": 0.0}


@dataclass
class Location:
    name: str
    place_kind: str = "hall"
    affordances: set[str] = field(default_factory=set)


@dataclass
class World:
    location: Location
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str = "community hall"
    game: str = "bingo"
    surprise: str = "fawn figurine"
    hero_name: str = "Fawn"
    hero_type: str = "scout"
    leader_name: str = "Mara"
    seed: Optional[int] = None


LOCATIONS = {
    "community hall": Location("the community hall", affordances={"bingo"}),
    "school gym": Location("the school gym", affordances={"bingo"}),
}

GAMES = {
    "bingo": {
        "noun": "bingo",
        "verb": "play bingo",
        "board": "bingo board",
        "sound": "the soft clatter of markers",
    }
}

SURPRISES = {
    "fawn figurine": {
        "label": "fawn figurine",
        "phrase": "a little fawn figurine",
        "owner": "volunteer_child",
        "fragile": True,
    }
}

HERO_NAMES = ["Fawn", "Mina", "Toby", "Eli", "Nia", "June"]
LEADER_NAMES = ["Mara", "Silas", "June", "Ari"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

class BadEndingWorld(World):
    pass


def _hero_pronouns(hero: Entity) -> tuple[str, str, str]:
    return "they", "them", "their"


def build_world(params: StoryParams) -> World:
    if params.place not in LOCATIONS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.game not in GAMES:
        raise StoryError(f"Unknown game: {params.game}")
    if params.surprise not in SURPRISES:
        raise StoryError(f"Unknown surprise object: {params.surprise}")

    world = BadEndingWorld(LOCATIONS[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    leader = world.add(Entity(id=params.leader_name, kind="character", type="leader"))
    surprise = SURPRISES[params.surprise]
    prop = world.add(Entity(
        id="surprise_object",
        type="figurine",
        label=surprise["label"],
        phrase=surprise["phrase"],
        owner=surprise["owner"],
    ))
    world.facts.update(hero=hero, leader=leader, prop=prop, surprise=surprise, params=params)
    return world


def intro(world: World) -> None:
    hero: Entity = world.facts["hero"]
    leader: Entity = world.facts["leader"]
    game = GAMES[world.facts["params"].game]
    world.say(
        f"{hero.id} was a small scout who liked quiet Friday nights at {world.location.name}."
    )
    world.say(
        f"The room had paper cups of juice, warm lights, and the steady rhythm of {game['noun']}."
    )
    hero.memes["joy"] += 1
    leader.memes["calm"] = 1.0


def discovery(world: World) -> None:
    hero: Entity = world.facts["hero"]
    prop: Entity = world.facts["prop"]
    game = GAMES[world.facts["params"].game]
    hero.memes["curiosity"] = 1.0
    world.para()
    world.say(
        f"Near the window, {hero.id} spotted {prop.phrase} on the sill."
    )
    world.say(
        f"{hero.id} thought it might be a prize for the next {game['noun']} winner."
    )


def misunderstanding(world: World) -> None:
    hero: Entity = world.facts["hero"]
    leader: Entity = world.facts["leader"]
    prop: Entity = world.facts["prop"]
    hero.memes["worry"] += 1
    hero.memes["conflict"] += 1
    leader.memes["worry"] += 1
    world.say(
        f"When {hero.id} reached for it, {leader.id} thought {hero.id} was taking something that did not belong there."
    )
    world.say(
        f"{leader.id} frowned and asked {hero.id} to stop, and the room turned quiet."
    )
    world.facts["misunderstanding"] = True


def surprise_and_bad_ending(world: World) -> None:
    hero: Entity = world.facts["hero"]
    leader: Entity = world.facts["leader"]
    prop: Entity = world.facts["prop"]
    hero.memes["embarrassment"] += 1
    leader.memes["embarrassment"] += 1
    prop.meters["damage"] += 1
    world.para()
    world.say(
        f"Then the surprise came out: the figurine belonged to the volunteer's child, and nobody had meant for it to be part of the game."
    )
    world.say(
        f"It slipped off the sill, hit the floor, and broke."
    )
    world.say(
        f"{hero.id}'s face went hot, and {leader.id} had to explain the mistake to the whole hall."
    )
    world.facts["bad_ending"] = True


def close(world: World) -> None:
    hero: Entity = world.facts["hero"]
    prop: Entity = world.facts["prop"]
    world.para()
    world.say(
        f"The bingo game ended without a happy prize, and the hall stayed hushed while the broken pieces were gathered up."
    )
    world.say(
        f"{hero.id} walked home feeling small, with the image of the broken fawn figurine stuck in {hero.id}'s mind."
    )
    world.facts["ended_badly"] = True


def generate_story(params: StoryParams) -> World:
    world = build_world(params)
    intro(world)
    discovery(world)
    misunderstanding(world)
    surprise_and_bad_ending(world)
    close(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a short slice-of-life story about a scout named {p.hero_name} at {world.location.name} during bingo night.",
        f"Tell a gentle but sad story that includes bingo, a scout, and a fawn figurine that causes a misunderstanding.",
        f"Write a story where a small surprise at {world.location.name} leads to a bad ending for {p.hero_name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    hero: Entity = world.facts["hero"]
    leader: Entity = world.facts["leader"]
    prop: Entity = world.facts["prop"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a small scout who went to {world.location.name} for bingo.",
        ),
        QAItem(
            question=f"What did {hero.id} think the little fawn figurine was?",
            answer=f"{hero.id} thought {prop.phrase} was a prize for bingo.",
        ),
        QAItem(
            question=f"Why did {leader.id} get upset?",
            answer=f"{leader.id} got upset because {hero.id} reached for something that was not meant to be a prize, and it caused a misunderstanding.",
        ),
        QAItem(
            question=f"What was the bad ending of the story?",
            answer=f"The figurine slipped off the sill, broke on the floor, and the hall ended in embarrassment instead of a happy prize.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bingo?",
            answer="Bingo is a game where people listen for called numbers and mark them on a card or board.",
        ),
        QAItem(
            question="What is a scout?",
            answer="A scout is a child who learns skills, helps others, and tries to be prepared and kind.",
        ),
        QAItem(
            question="What is a fawn?",
            answer="A fawn is a young deer, often small and spotted.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:14} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- location(P).
game(G) :- game_kind(G).
surprise(S) :- surprise_kind(S).

compatible_story(P, G, S) :- location(P), game_kind(G), surprise_kind(S), game_affords(P, G), surprise_possible(S).

#show compatible_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for place, loc in LOCATIONS.items():
        lines.append(asp.fact("location", place.replace(" ", "_")))
        for g in sorted(loc.affordances):
            lines.append(asp.fact("game_affords", place.replace(" ", "_"), g))
    for g in GAMES:
        lines.append(asp.fact("game_kind", g))
    for s in SURPRISES:
        lines.append(asp.fact("surprise_kind", s.replace(" ", "_")))
        lines.append(asp.fact("surprise_possible", s.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible_story/3."))
    asp_set = set(asp.atoms(model, "compatible_story"))
    py_set = {
        (place.replace(" ", "_"), game, surprise.replace(" ", "_"))
        for place, loc in LOCATIONS.items()
        for game in GAMES
        for surprise in SURPRISES
        if game in loc.affordances
    }
    if asp_set == py_set:
        print(f"OK: clingo gate matches python ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in asp:", sorted(asp_set - py_set))
    print("  only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = generate_story(params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life story world about bingo, a scout, and a fawn-shaped misunderstanding."
    )
    ap.add_argument("--place", choices=sorted(LOCATIONS))
    ap.add_argument("--game", choices=sorted(GAMES))
    ap.add_argument("--surprise", choices=sorted(SURPRISES))
    ap.add_argument("--name")
    ap.add_argument("--leader")
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
    place = args.place or rng.choice(list(LOCATIONS))
    game = args.game or rng.choice(list(GAMES))
    surprise = args.surprise or rng.choice(list(SURPRISES))
    if game not in LOCATIONS[place].affordances:
        raise StoryError("This place does not reasonably support that game.")
    name = args.name or rng.choice(HERO_NAMES)
    leader = args.leader or rng.choice(LEADER_NAMES)
    return StoryParams(place=place, game=game, surprise=surprise, hero_name=name, leader_name=leader)


CURATED = [
    StoryParams(place="community hall", game="bingo", surprise="fawn figurine", hero_name="Fawn", leader_name="Mara"),
    StoryParams(place="school gym", game="bingo", surprise="fawn figurine", hero_name="Mina", leader_name="June"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show compatible_story/3."))
        triples = sorted(set(asp.atoms(model, "compatible_story")))
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.hero_name}: {p.game} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
