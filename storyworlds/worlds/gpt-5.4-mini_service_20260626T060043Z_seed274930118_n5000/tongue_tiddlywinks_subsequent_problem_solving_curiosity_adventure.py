#!/usr/bin/env python3
"""
tongue_tiddlywinks_subsequent_problem_solving_curiosity_adventure.py
====================================================================

A small standalone storyworld about a curious child, a stubborn tiddlywinks
mishap, and a subsequent problem-solving adventure.

Premise:
A child finds a tiny tiddlywinks set and wants to play at once. During the game,
a wink lands in a crack, a pet lizard sticks out its tongue in alarm, and the
child must solve the problem before the game can continue.

Story shape:
- Beginning: curiosity, setting, and the found game
- Middle: the tiddlywinks problem, search, and careful fixing
- Ending: the game resumes, and the child learns something useful

This world is intentionally small and constraint-checked. It generates one
complete story per sample, plus grounded Q&A.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = False


@dataclass
class Game:
    label: str
    phrase: str
    play_verb: str
    discovery_verb: str
    problem: str
    fix_tool: str
    clue: str
    place_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    game: str
    hero_name: str
    hero_type: str
    parent_type: str
    companion: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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


SETTINGS = {
    "attic": Setting(place="the attic", indoor=True),
    "shed": Setting(place="the garden shed", indoor=True),
    "porch": Setting(place="the porch", indoor=False),
    "workshop": Setting(place="the workshop", indoor=True),
    "courtyard": Setting(place="the courtyard", indoor=False),
}

GAMES = {
    "tiddlywinks": Game(
        label="tiddlywinks set",
        phrase="a bright little tiddlywinks set with a red cup and a blue cup",
        play_verb="flick the winks",
        discovery_verb="found the set",
        problem="one wink skittered under a crate",
        fix_tool="a spoon",
        clue="the next wink bounced toward the light",
        place_hint="under the table",
        tags={"tiddlywinks", "game", "tiny"},
    )
}

HERO_NAMES = ["Nia", "Milo", "Iris", "Jasper", "Lena", "Finn", "Oona", "Tobin"]
COMPANIONS = ["cat", "sparrow", "lizard", "mouse", "puppy"]
TRAITS = ["curious", "careful", "brave", "quick", "bright"]


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def _intro(world: World, hero: Entity, parent: Entity, game: Game, companion: Entity) -> None:
    world.say(
        f"{hero.id} was a curious little {hero.type} who loved finding small treasures."
    )
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.type} went to {world.setting.place}."
    )
    world.say(
        f"Near an old box, they {game.discovery_verb}, and {hero.id} grinned at the {game.label}."
    )
    world.say(
        f"A quiet {companion.type} watched nearby and kept sticking out {companion.pronoun('possessive')} tongue at the shiny pieces."
    )


def _play(world: World, hero: Entity, game: Game) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"{hero.id} wanted to {game.play_verb} right away, because the little game looked like an adventure."
    )
    world.say(
        f"The first few turns were fun, but then {game.problem}."
    )
    world.say(
        f"That was a problem, because the game could not keep going with one wink missing."
    )


def _problem_solving(world: World, hero: Entity, parent: Entity, game: Game, companion: Entity) -> None:
    hero.memes["puzzled"] = hero.memes.get("puzzled", 0) + 1
    world.para()
    world.say(
        f"{hero.id} knelt down and looked very carefully."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.type} pointed to {game.clue}, and together they searched {game.place_hint} and behind the crate."
    )
    world.say(
        f"Then {companion.id} darted forward, wiggled {companion.pronoun('possessive')} nose, and showed them a tiny gap in the floorboards."
    )
    world.say(
        f"{hero.id} had an idea: use {game.fix_tool} to guide the wink back out without knocking the cups over."
    )
    hero.memes["confidence"] = hero.memes.get("confidence", 0) + 1
    world.say(
        f"Carefully, {hero.id} slid the {game.fix_tool} into the gap, and the wink rolled free at last."
    )


def _resolution(world: World, hero: Entity, parent: Entity, game: Game, companion: Entity) -> None:
    world.para()
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"{hero.id} laughed, and the {game.label} felt new again."
    )
    world.say(
        f"The {companion.type} settled down and closed {companion.pronoun('possessive')} tongue, as if the adventure was done."
    )
    world.say(
        f"After that, {hero.id} played {game.play_verb} with a steadier hand, and every wink stayed in sight."
    )
    world.say(
        f"It was a small fix, but it made the subsequent game even better, because now {hero.id} knew how to solve a tricky problem."
    )


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.game not in GAMES:
        raise StoryError(f"Unknown game: {params.game}")

    world = World(SETTINGS[params.setting])
    game = GAMES[params.game]

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type))
    companion = world.add(Entity(id=params.companion, kind="character", type=params.companion))

    world.facts.update(hero=hero, parent=parent, companion=companion, game=game)

    _intro(world, hero, parent, game, companion)
    _play(world, hero, game)
    _problem_solving(world, hero, parent, game, companion)
    _resolution(world, hero, parent, game, companion)
    return world


# ---------------------------------------------------------------------------
# Registries / parameter resolution
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    return [(s, g) for s in SETTINGS for g in GAMES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A curious adventure with tiddlywinks and a subsequent fix."
    )
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--game", choices=sorted(GAMES))
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--companion", choices=COMPANIONS)
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    game = args.game or rng.choice(sorted(GAMES))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    companion = args.companion or rng.choice(COMPANIONS)
    return StoryParams(
        setting=setting,
        game=game,
        hero_name=name,
        hero_type=hero_type,
        parent_type=parent,
        companion=companion,
    )


# ---------------------------------------------------------------------------
# Output / QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    game: Game = f["game"]  # type: ignore[assignment]
    return [
        f'Write a child-friendly adventure story about {hero.id} and a {game.label}.',
        f"Tell a story where a curious {hero.type} solves a tiddlywinks problem and learns something useful.",
        f'Write a short story that uses the words "tongue", "tiddlywinks", and "subsequent".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    companion: Entity = f["companion"]  # type: ignore[assignment]
    game: Game = f["game"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {hero.id} find at {world.setting.place}?",
            answer=f"{hero.id} found a {game.label}, and that made {hero.id} very curious.",
        ),
        QAItem(
            question=f"What problem happened during the game?",
            answer=f"One wink skittered under a crate, so the game could not continue until it was found.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=f"{hero.id} and {parent.type} searched carefully, and then used {game.fix_tool} to guide the wink back out.",
        ),
        QAItem(
            question=f"What did the {companion.type} do with {companion.pronoun('possessive')} tongue?",
            answer=f"The {companion.type} stuck out {companion.pronoun('possessive')} tongue at the shiny pieces, as if it was part of the adventure.",
        ),
        QAItem(
            question=f"What happened after the wink was fixed?",
            answer=f"The subsequent game became smoother, and {hero.id} played again with a steadier hand.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tiddlywinks?",
            answer="Tiddlywinks is a small game where you flick tiny pieces into a cup or target.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn more.",
        ),
        QAItem(
            question="What does subsequent mean?",
            answer="Subsequent means something that comes after something else.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.type:
            bits.append(f"type={e.type}")
        lines.append(f"{e.id}: " + ", ".join(bits))
    return "\n".join(lines)


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(attic; shed; porch; workshop; courtyard).
game(tiddlywinks).

valid_story(S, G) :- setting(S), game(G).

#show valid_story/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid in GAMES:
        lines.append(asp.fact("game", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((s, g) for s, g in valid_combos())
    asp_set = set(asp_valid())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python-only:", sorted(py - asp_set))
    print("asp-only:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting, game in valid_combos():
            params = StoryParams(
                setting=setting,
                game=game,
                hero_name=HERO_NAMES[0],
                hero_type="girl",
                parent_type="mother",
                companion="lizard",
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 25):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
