#!/usr/bin/env python3
"""
A small whodunit storyworld about a missing thingamajigger, a few clues, and a
careful solve.

The child-facing premise:
- Something called the thingamajigger has gone missing.
- The hero asks questions, checks clues, and rules out suspects.
- The ending reveals who moved it and why, with the object recovered.

The world is intentionally tiny and classical: one room, one mystery, one turn,
one resolution.
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
# World data
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Setting:
    place: str
    indoor: bool = True
    detail: str = ""


@dataclass(frozen=True)
class Suspect:
    id: str
    label: str
    role: str
    trait: str


@dataclass(frozen=True)
class Clue:
    id: str
    label: str
    where: str
    points_to: str
    what_it_shows: str


@dataclass(frozen=True)
class Thing:
    id: str
    label: str
    owner: str
    hiding_spot: str
    size: str = "small"


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "it" if self.kind != "character" else "they"

    def possessive(self) -> str:
        return "its" if self.kind != "character" else "their"


@dataclass
class StoryParams:
    setting: str
    hero: str
    sidekick: str
    culprit: str
    seed: Optional[int] = None


SETTINGS = {
    "workshop": Setting(
        place="the little workshop",
        indoor=True,
        detail="Dusty shelves lined one wall, and a single lamp made a bright circle on the table.",
    ),
    "library": Setting(
        place="the back room of the library",
        indoor=True,
        detail="Tall books leaned close together, and the carpet muffled every step.",
    ),
    "kitchen": Setting(
        place="the kitchen",
        indoor=True,
        detail="A warm clock ticked near the sink, and the counter was cleared for supper.",
    ),
}

HEROES = {
    "nora": "Nora",
    "leo": "Leo",
    "mila": "Mila",
    "toby": "Toby",
}

SIDEKICKS = {
    "pip": "Pip",
    "ivy": "Ivy",
    "otto": "Otto",
    "zara": "Zara",
}

SUSPECTS = {
    "cat": Suspect("cat", "the cat", "pet", "quiet"),
    "brother": Suspect("brother", "the older brother", "family", "shy"),
    "neighbor": Suspect("neighbor", "the neighbor", "visitor", "hushed"),
}

THING = Thing(
    id="thingamajigger",
    label="thingamajigger",
    owner="hero",
    hiding_spot="under the blue stool",
)

CLUES = {
    "scratch": Clue(
        id="scratch",
        label="tiny scratch marks",
        where="near the stool",
        points_to="cat",
        what_it_shows="something with little paws moved it across the floor",
    ),
    "crumbs": Clue(
        id="crumbs",
        label="crumb crumbs",
        where="by the table leg",
        points_to="brother",
        what_it_shows="someone had been snacking while looking for it",
    ),
    "note": Clue(
        id="note",
        label="a folded note",
        where="on the lamp base",
        points_to="neighbor",
        what_it_shows="someone had left a careful message instead of taking it",
    ),
}

ASP_RULES = r"""
% A mystery is solvable when clues point to exactly one culprit.
possible_culprit(S) :- suspect(S).
supported(S) :- clue_points_to(_, S).
solved(S) :- possible_culprit(S), supported(S), not other_supported(S).
other_supported(S) :- supported(T), suspect(T), T != S.

% The thingamajigger is recovered when the culprit is identified and the hero
% checks the hiding spot.
recovered(T) :- thing(T), found_spot(T), solved(_).
"""


# ---------------------------------------------------------------------------
# Registry facts
# ---------------------------------------------------------------------------
def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoor:
            lines.append(asp.fact("indoor", sid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_points_to", cid, clue.points_to))
    lines.append(asp.fact("thing", THING.id))
    lines.append(asp.fact("found_spot", THING.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(setting: str, culprit: str) -> bool:
    return setting in SETTINGS and culprit in SUSPECTS


def valid_combos() -> list[tuple[str, str]]:
    return [(s, c) for s in SETTINGS for c in SUSPECTS]


def explain_rejection(setting: str, culprit: str) -> str:
    if setting not in SETTINGS:
        return "(No story: the setting is unknown.)"
    if culprit not in SUSPECTS:
        return "(No story: the suspect is unknown.)"
    return "(No story: this mystery would not have a clear enough clue trail.)"


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    resolved: bool = False
    culprit: Optional[str] = None

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        self.trace.append(text)

    def render(self) -> str:
        return "\n\n".join(self.trace)


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting=setting)
    hero = world.add(Entity(id=params.hero, kind="character", label=params.hero, type="child"))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", label=params.sidekick, type="child"))
    culprit = SUSPECTS[params.culprit]
    suspect_ent = world.add(Entity(id=culprit.id, kind="character", label=culprit.label, type=culprit.role))
    thing = world.add(Entity(id=THING.id, kind="thing", label=THING.label, type="object", owner=hero.id))

    hero.memes["curiosity"] = 1
    sidekick.memes["worry"] = 1
    thing.meters["missing"] = 1
    suspect_ent.meters["suspicion"] = 0

    world.say(
        f"In {setting.place}, {hero.id} noticed that the thingamajigger was gone."
    )
    world.say(setting.detail)
    world.say(
        f"{sidekick.id} whispered, 'It was here a minute ago.'"
    )

    # Suspense build: searching the room.
    clues_seen: list[str] = []
    for clue in CLUES.values():
        if clue.points_to == culprit.id:
            clues_seen.append(clue.label)
            world.say(
                f"Then {hero.id} found {clue.label} {clue.where}, and the little clue felt important."
            )
            suspect_ent.meters["suspicion"] += 1
            world.facts["best_clue"] = clue.id
            break
        else:
            world.say(
                f"{hero.id} checked {clue.where}, but that clue only added more questions."
            )

    world.say(
        f"{hero.id} looked at {suspect_ent.label} and asked gentle questions instead of guessing."
    )

    # Whodunit reveal.
    if clues_seen:
        world.resolved = True
        world.culprit = culprit.id
        thing.owner = hero.id
        thing.meters["found"] = 1
        world.say(
            f"At last, {hero.id} understood it: {suspect_ent.label} had moved the thingamajigger "
            f"to {THING.hiding_spot} while tidying the room."
        )
        world.say(
            f"{suspect_ent.label} admitted it with a small nod, because {suspect_ent.label} had only wanted "
            f"to make space for a game."
        )
        world.say(
            f"{hero.id} smiled, fetched the thingamajigger, and set it back in the open where everyone could see it."
        )
        world.say(
            f"With the mystery solved, {sidekick.id} laughed, and the room felt calm again."
        )
    else:
        world.say(
            f"The clues never lined up, so {hero.id} kept looking until the lamp came on and the thingamajigger was found."
        )

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        culprit=suspect_ent,
        thing=thing,
        setting=params.setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    culprit = f["culprit"]
    setting = f["setting"]
    return [
        f'Write a short whodunit story for a child about a missing thingamajigger in {SETTINGS[setting].place}.',
        f"Tell a suspenseful but gentle story where {hero.id} investigates a missing thingamajigger and solves the mystery.",
        f"Write a story with clues, a careful question, and a calm reveal about why {culprit.label} moved the thingamajigger.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    culprit = f["culprit"]
    clue = CLUES.get(f.get("best_clue", "scratch"))
    return [
        QAItem(
            question="What was missing at the start of the story?",
            answer="The thingamajigger was missing, so the children had to look for it.",
        ),
        QAItem(
            question=f"Who noticed that the thingamajigger was gone?",
            answer=f"{hero.id} noticed first, and {sidekick.id} helped look carefully.",
        ),
        QAItem(
            question=f"What clue helped point toward {culprit.label}?",
            answer=f"{clue.label} helped because it showed {clue.what_it_shows}.",
        ),
        QAItem(
            question=f"Why had {culprit.label} moved the thingamajigger?",
            answer=f"{culprit.label} had moved it while tidying the room and making space for a game.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a little piece of information that helps you figure something out.",
        ),
        QAItem(
            question="Why do detectives ask questions?",
            answer="Detectives ask questions so they can learn what happened and solve the mystery carefully.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to find a way to make it better or to understand it clearly.",
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


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_solve_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_solve_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in asp:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld about a missing thingamajigger.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--culprit", choices=SUSPECTS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    culprit = args.culprit or rng.choice(list(SUSPECTS))
    if not valid_combo(setting, culprit):
        raise StoryError(explain_rejection(setting, culprit))
    hero = args.hero or rng.choice(list(HEROES))
    sidekick = args.sidekick or rng.choice([k for k in SIDEKICKS if k != hero])
    return StoryParams(
        setting=setting,
        hero=HEROES[hero],
        sidekick=SIDEKICKS[sidekick],
        culprit=culprit,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print()
        print("--- world trace ---")
        for line in sample.world.trace:
            print(line)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_combo/2."))
        print(f"{len(set(asp.atoms(model, 'valid_combo')))} valid combos")
        for t in sorted(set(asp.atoms(model, "valid_combo"))):
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTINGS:
            for culprit in SUSPECTS:
                params = StoryParams(setting=setting, hero="Nora", sidekick="Pip", culprit=culprit)
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            p = sample.params
            header = f"### {p.hero} in {p.setting} / culprit={p.culprit}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
