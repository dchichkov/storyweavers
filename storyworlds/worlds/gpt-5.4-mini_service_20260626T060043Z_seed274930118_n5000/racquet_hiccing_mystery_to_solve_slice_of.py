#!/usr/bin/env python3
"""
Standalone storyworld: racquet hiccing mystery to solve slice of life.

A small, child-facing slice-of-life mystery:
- a child loves a racquet
- the racquet goes missing
- a hiccing sound becomes the clue trail
- the child and a helper solve the mystery by following ordinary, concrete signs
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


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    hidden: bool = False
    returned: bool = False
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
    detail: str


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.hints: list[str] = []
        self.found: bool = False

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.hints = list(self.hints)
        c.found = self.found
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "courtyard": Setting(place="the courtyard", detail="The courtyard had a bench, a flowerpot, and a low wall."),
    "playground": Setting(place="the playground", detail="The playground had a sandbox, a water fountain, and a bright red slide."),
    "backyard": Setting(place="the backyard", detail="The backyard had a hose, a folding chair, and a little garden table."),
    "community_court": Setting(place="the community court", detail="The court had painted lines, a fence, and a ball basket."),
}

HELPERS = {
    "mother": "mother",
    "father": "father",
    "grandma": "grandma",
}

NAMES = {
    "girl": ["Mina", "Lila", "Nora", "Zoe", "Iris"],
    "boy": ["Ben", "Theo", "Milo", "Kai", "Eli"],
}

# Object of desire.
RACQUETS = {
    "tennis": {
        "label": "racquet",
        "phrase": "a light blue racquet with a bright grip",
        "use": "play tennis",
        "fun": "hit the yellow ball back and forth",
    }
}

# Ordinary hiding places, used for the mystery.
HIDE_SPOTS = [
    "behind the bench",
    "under the flowerpot",
    "next to the water fountain",
    "by the fence",
    "under the folding chair",
    "near the garden table",
]

# The hiccing clue chain.
HICCING = [
    "hic",
    "hic-hic",
    "hic",
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the child has a racquet, it is misplaced, and there is
% at least one plausible hiccing clue trail that leads to a hiding spot in the
% chosen setting.
valid_story(Place) :- setting(Place), has_racquet, misplaced, clue_trail, solvable(Place).

% A clue trail is available when a character makes hic sounds and those sounds
% point to one of the possible hiding spots.
clue_trail :- hiccing, hint(bench).
clue_trail :- hiccing, hint(flowerpot).
clue_trail :- hiccing, hint(fountain).
clue_trail :- hiccing, hint(fence).
clue_trail :- hiccing, hint(chair).
clue_trail :- hiccing, hint(table).

% The mystery is solvable if the racquet can be found in one of the hiding spots.
solvable(Place) :- hiding_spot(Place, bench).
solvable(Place) :- hiding_spot(Place, flowerpot).
solvable(Place) :- hiding_spot(Place, fountain).
solvable(Place) :- hiding_spot(Place, fence).
solvable(Place) :- hiding_spot(Place, chair).
solvable(Place) :- hiding_spot(Place, table).

#show valid_story/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for spot in ["bench", "flowerpot", "fountain", "fence", "chair", "table"]:
        lines.append(asp.fact("hint", spot))
        lines.append(asp.fact("hiding_spot", "any", spot))
    lines.append(asp.fact("has_racquet"))
    lines.append(asp.fact("misplaced"))
    lines.append(asp.fact("hiccing"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program())
    except Exception as exc:
        print(f"ASP error: {exc}")
        return 1
    if model:
        print("OK: ASP program grounds and finds a model.")
        return 0
    print("ASP program produced no model.")
    return 1


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------

def valid_places() -> list[str]:
    return list(SETTINGS.keys())


def choose_hidden_spot(rng: random.Random) -> str:
    return rng.choice(HIDE_SPOTS)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life racquet mystery storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    place = args.place or rng.choice(valid_places())
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(place=place, name=name, gender=gender, helper=helper)


def _do_hiccing(world: World, child: Entity) -> None:
    child.memes["embarrassed"] = child.memes.get("embarrassed", 0) + 1
    world.hints.append("hiccing")
    world.say(f"Every few steps, {child.pronoun('subject')} gave a tiny hiccing sound.")


def _hide_racquet(world: World, racquet: Entity, spot: str) -> None:
    racquet.hidden = True
    racquet.location = spot


def _find_racquet(world: World, racquet: Entity, child: Entity) -> None:
    racquet.hidden = False
    racquet.returned = True
    child.memes["relief"] = child.memes.get("relief", 0) + 1
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    world.found = True


def tell_story(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    setting = SETTINGS[params.place]
    world = World(setting)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type=params.helper,
        label=params.helper,
    ))
    racquet = world.add(Entity(
        id="racquet",
        kind="thing",
        type="racquet",
        label="racquet",
        phrase=RACQUETS["tennis"]["phrase"],
        owner=child.id,
        location="with the child",
    ))

    hide_spot = choose_hidden_spot(rng)
    _hide_racquet(world, racquet, hide_spot)

    world.say(f"{child.label} loved {RACQUETS['tennis']['use']} at {setting.place}.")
    world.say(f"{child.pronoun('possessive').capitalize()} favorite thing was {racquet.phrase}.")
    world.para()

    world.say(setting.detail)
    world.say(f"One afternoon, {child.label} reached for the racquet, but it was gone.")
    _do_hiccing(world, child)
    world.say(f"{helper.label.capitalize()} looked up from nearby and asked where {child.pronoun('possessive')} racquet had gone.")
    world.para()

    world.say(f"{child.label} and {helper.label} checked the usual places one by one.")
    if hide_spot == "behind the bench":
        world.say("They looked behind the bench and saw a tiny racquet-shaped corner.")
    elif hide_spot == "under the flowerpot":
        world.say("They crouched by the flowerpot, and a little handle peeked out.")
    elif hide_spot == "next to the water fountain":
        world.say("They followed the hiccing sound to the water fountain, where something blue flashed at the base.")
    elif hide_spot == "by the fence":
        world.say("They walked by the fence and noticed the racquet leaning in the shade.")
    elif hide_spot == "under the folding chair":
        world.say("They lifted the folding chair and found the racquet tucked underneath.")
    else:
        world.say("They came to the garden table and spotted the racquet resting in its shadow.")

    _find_racquet(world, racquet, child)
    world.say(f"{child.label} smiled, grabbed the racquet, and gave a little relieved laugh that still had one last hic in it.")
    world.say(f"After that, {child.label} went back to the game, and the afternoon felt ordinary again.")
    world.facts.update(
        child=child,
        helper=helper,
        racquet=racquet,
        spot=hide_spot,
        place=params.place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    return [
        f"Write a gentle slice-of-life mystery about {child.label} looking for a missing racquet at {world.setting.place}.",
        f"Tell a simple story where {child.label} keeps hiccing while {helper.label} helps find a lost racquet.",
        f"Write a child-friendly mystery set at {world.setting.place} that ends with a racquet being found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    racquet: Entity = f["racquet"]
    spot = f["spot"]
    return [
        QAItem(
            question=f"What was {child.label} looking for?",
            answer=f"{child.label} was looking for the racquet, because {racquet.label} was the thing {child.pronoun('subject')} wanted for the game.",
        ),
        QAItem(
            question=f"Why was the racquet a mystery?",
            answer=f"It was a mystery because the racquet was not where {child.pronoun('subject')} expected it to be, so {child.label} had to search for it.",
        ),
        QAItem(
            question=f"Who helped {child.label} solve the mystery?",
            answer=f"{helper.label} helped by looking with {child.label} and checking the usual places.",
        ),
        QAItem(
            question=f"Where was the racquet found?",
            answer=f"It was found {spot}, where it had been hiding during the search.",
        ),
        QAItem(
            question=f"How did {child.label} feel at the end?",
            answer=f"{child.label} felt relieved and happy after finding the racquet and going back to play.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a racquet?",
            answer="A racquet is a framed sports tool with strings that people use to hit a ball or shuttle back and forth.",
        ),
        QAItem(
            question="What does hiccing mean?",
            answer="Hiccing means making small hiccup sounds again and again for a little while.",
        ),
        QAItem(
            question="Why do people look in usual places when something goes missing?",
            answer="People look in usual places first because important things are often set down nearby by mistake.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.hidden:
            bits.append("hidden=True")
        if e.returned:
            bits.append("returned=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"found={world.found}")
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


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="courtyard", name="Mina", gender="girl", helper="mother"),
    StoryParams(place="playground", name="Theo", gender="boy", helper="father"),
    StoryParams(place="backyard", name="Lila", gender="girl", helper="grandma"),
]


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_places())} settings can host the racquet mystery.")
        for p in valid_places():
            print(f"  {p}")
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
            if sample.story in seen:
                i += 1
                continue
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
            header = f"### {p.name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
