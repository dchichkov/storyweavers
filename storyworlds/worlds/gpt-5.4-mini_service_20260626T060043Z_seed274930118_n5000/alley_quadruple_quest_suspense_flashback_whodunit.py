#!/usr/bin/env python3
"""
Standalone storyworld: an alley whodunit with a quadruple clue, a small quest,
suspense, and a flashback.

The world models a child-facing mystery in a narrow alley. A curious lead
detective follows a quest to solve a missing-object puzzle. Suspense grows as
four clues appear to point in different directions, then a flashback reveals the
truth and the mystery is resolved.
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
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Location:
    name: str
    mood: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    detail: str
    points_to: str


@dataclass
class StoryParams:
    place: str
    detective: str
    sidekick: str
    missing: str
    culprit: str
    seed: Optional[int] = None


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

LOCATIONS = {
    "alley": Location(name="the alley", mood="shadowy", affordances={"search", "hide", "listen"}),
    "courtyard": Location(name="the courtyard", mood="open", affordances={"search", "gather"}),
    "attic": Location(name="the attic", mood="dusty", affordances={"search", "flashback"}),
}

DETECTIVE_TYPES = {
    "girl": ("girl", "curious"),
    "boy": ("boy", "careful"),
}

SIDEKICKS = {
    "cat": Entity(id="cat", kind="character", type="thing", label="the cat"),
    "dog": Entity(id="dog", kind="character", type="thing", label="the dog"),
    "friend": Entity(id="friend", kind="character", type="girl", label="the friend"),
}

MISSING_THINGS = {
    "teacup": Entity(id="teacup", kind="thing", type="cup", label="teacup", phrase="a tiny blue teacup"),
    "key": Entity(id="key", kind="thing", type="key", label="key", phrase="a small brass key"),
    "badge": Entity(id="badge", kind="thing", type="badge", label="badge", phrase="a shiny club badge"),
}

CULPRITS = {
    "raccoon": "a hungry raccoon",
    "wind": "a gust of wind",
    "twin": "the detective's twin",
}

CLUE_REGISTRY = {
    "boots": Clue("boots", "muddy boots", "mudprints by the wall", "raccoon"),
    "ribbon": Clue("ribbon", "red ribbon", "a ribbon snagged on a nail", "twin"),
    "crumbs": Clue("crumbs", "cookie crumbs", "crumbs in a neat line", "wind"),
    "lamp": Clue("lamp", "broken lamp glow", "a flicker by the drain", "raccoon"),
}

QUADRUPLE_ORDER = ["boots", "ribbon", "crumbs", "lamp"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mystery is valid when there is an alley, a missing item, and at least four clues.
valid_story(L, M) :- location(L), missing(M), alley(L), clue(C1), clue(C2), clue(C3), clue(C4),
                     C1 != C2, C1 != C3, C1 != C4, C2 != C3, C2 != C4, C3 != C4,
                     clue_points(C1, _), clue_points(C2, _), clue_points(C3, _), clue_points(C4, _).
quadruple_clue(M) :- clue_count(M, 4).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for lid, loc in LOCATIONS.items():
        lines.append(asp.fact("location", lid))
        if lid == "alley":
            lines.append(asp.fact("alley", lid))
        for a in sorted(loc.affordances):
            lines.append(asp.fact("affords", lid, a))
    for mid in MISSING_THINGS:
        lines.append(asp.fact("missing", mid))
    for cid, clue in CLUE_REGISTRY.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_points", cid, clue.points_to))
    lines.append(asp.fact("clue_count", "case", 4))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2. #show quadruple_clue/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="An alley whodunit with a quest, suspense, and a flashback.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--detective", choices=DETECTIVE_TYPES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--missing", choices=MISSING_THINGS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--name")
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
    place = args.place or "alley"
    detective = args.detective or rng.choice(list(DETECTIVE_TYPES))
    sidekick = args.sidekick or rng.choice(list(SIDEKICKS))
    missing = args.missing or rng.choice(list(MISSING_THINGS))
    culprit = args.culprit or rng.choice(list(CULPRITS))
    if place != "alley" and not args.place:
        place = rng.choice(list(LOCATIONS))
    if missing == "badge" and culprit == "wind":
        raise StoryError("(No story: the wind cannot reasonably steal a club badge from a locked pocket.)")
    return StoryParams(place=place, detective=detective, sidekick=sidekick, missing=missing, culprit=culprit)


def generate(params: StoryParams) -> StorySample:
    world = World(LOCATIONS[params.place])
    det_type, trait = DETECTIVE_TYPES[params.detective]
    detective = world.add(Entity(id="detective", kind="character", type=det_type, label="the detective", memes={"curiosity": 1.0, "suspense": 0.0}))
    sidekick_proto = SIDEKICKS[params.sidekick]
    sidekick = world.add(Entity(id="sidekick", kind="character", type=sidekick_proto.type, label=sidekick_proto.label))
    missing_proto = MISSING_THINGS[params.missing]
    missing = world.add(Entity(id="missing", kind="thing", type=missing_proto.type, label=missing_proto.label, phrase=missing_proto.phrase, owner=detective.id, location=params.place))
    clue_ids = QUADRUPLE_ORDER[:4]

    # Act 1 setup
    world.say(f"In {world.location.name}, a {trait} detective started a quiet quest to find {missing.phrase}.")
    world.say(f"{detective.label.capitalize()} had a small sidekick, {sidekick.label}, and together they watched the alley for signs.")

    # Act 2 suspense
    world.para()
    world.say(f"First came a muddy clue, then a ribbon, then crumbs, then a flicker by the drain.")
    world.say(f"Each clue seemed to point somewhere different, and that made the case feel like a quadruple puzzle.")
    detective.memes["suspense"] = 1.0
    world.say(f"{detective.label.capitalize()} held still and listened, because the alley was so quiet it almost whispered back.")

    # Flashback turn
    world.para()
    world.say(f"Then {detective.label} remembered a flashback from earlier: {missing.phrase} had been carried near the back gate.")
    if params.culprit == "raccoon":
        world.say("A raccoon had sniffed around the gate, knocked the item loose, and dragged the shiny lid toward the drain.")
    elif params.culprit == "wind":
        world.say("A gust of wind had blown the item off a crate and into the darker corner of the alley.")
    else:
        world.say("The detective's twin had borrowed it for a game and forgotten to put it back.")
    world.say(f"The four clues made sense at once, and the scary hush turned into a simple answer.")

    # Resolution
    world.para()
    world.say(f"At last, {detective.label} found {missing.phrase} tucked safely behind a box.")
    world.say(f"{sidekick.label.capitalize()} sat beside the find, and the quest ended with a relieved smile instead of a mystery.")
    world.facts.update(
        detective=detective,
        sidekick=sidekick,
        missing=missing,
        culprit=params.culprit,
        clues=[CLUE_REGISTRY[c] for c in clue_ids],
        place=params.place,
        trait=trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short whodunit for a young child in an alley, with a quest, suspense, and a flashback.',
        f"Tell a simple mystery where {f['detective'].label} and {f['sidekick'].label} search {world.location.name} for {f['missing'].phrase}.",
        "Write a child-friendly detective story that uses a quadruple clue and ends with the truth revealed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    sidekick = f["sidekick"]
    missing = f["missing"]
    culprit = f["culprit"]
    place = f["place"]
    return [
        QAItem(
            question=f"What was {detective.label} trying to find in {place}?",
            answer=f"{detective.label.capitalize()} was trying to find {missing.phrase} during a careful quest in {place}.",
        ),
        QAItem(
            question=f"Why did the case feel suspenseful before the flashback?",
            answer="It felt suspenseful because four clues appeared and each one seemed to point in a different direction.",
        ),
        QAItem(
            question=f"What helped the detective solve the mystery?",
            answer="A flashback helped the detective remember what had happened earlier, and that made the clues make sense.",
        ),
        QAItem(
            question=f"Who stayed with the detective during the search?",
            answer=f"{sidekick.label.capitalize()} stayed with the detective and watched the alley during the search.",
        ),
        QAItem(
            question=f"Who caused the missing item to disappear?",
            answer=f"The culprit was {CULPRITS[culprit]}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an alley?",
            answer="An alley is a narrow path between buildings, often a little dark and quiet.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important or a job that needs brave effort to finish.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the uneasy feeling of waiting to learn what will happen next.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a remembered scene from earlier that helps explain the present.",
        ),
        QAItem(
            question="What does whodunit mean?",
            answer="A whodunit is a mystery story where the reader tries to figure out who caused the trouble.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def asp_verify() -> int:
    import asp
    if set(asp_valid()) == {("alley", "case")}:
        print("OK: ASP twin is present.")
        return 0
    print("ASP mismatch.")
    return 1


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
    StoryParams(place="alley", detective="girl", sidekick="cat", missing="key", culprit="raccoon"),
    StoryParams(place="alley", detective="boy", sidekick="dog", missing="teacup", culprit="wind"),
    StoryParams(place="courtyard", detective="girl", sidekick="friend", missing="badge", culprit="twin"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2. #show quadruple_clue/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.detective} in the {p.place} ({p.missing})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
