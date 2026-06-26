#!/usr/bin/env python3
"""
A small whodunit-style storyworld about a minion who must solve a mystery,
with a gentle cautionary turn and a few rhyming lines.

The seed word is "minion", but the world is child-friendly: a tiny helper,
a missing item, clues, suspects, and a careful resolution.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    truthful: bool = True
    suspect: bool = False
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "minion"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    name: str
    indoors: bool = True
    clue_kind: str = "crumb"
    caution_kind: str = "sneak"
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    missing: str
    location: str
    culprit: str
    clue: str
    wrong_suspects: list[str] = field(default_factory=list)
    warning: str = ""


@dataclass
class StoryParams:
    place: str
    missing: str
    culprit: str
    hero_name: str
    sidekick_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.clues: list[str] = []
        self.solution: Optional[str] = None

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

PLACES = {
    "kitchen": Place(
        name="the kitchen",
        indoors=True,
        clue_kind="crumb",
        caution_kind="pantry",
        affords={"crumb", "cookie", "jar"},
    ),
    "hall": Place(
        name="the hall",
        indoors=True,
        clue_kind="track",
        caution_kind="quiet step",
        affords={"track", "shoe"},
    ),
    "playroom": Place(
        name="the playroom",
        indoors=True,
        clue_kind="toy",
        caution_kind="tidy",
        affords={"toy", "block"},
    ),
    "garden": Place(
        name="the garden",
        indoors=False,
        clue_kind="mud",
        caution_kind="gate",
        affords={"mud", "leaf"},
    ),
}

MISSING_ITEMS = {
    "cookie": {
        "label": "cookie",
        "phrase": "a sweet cookie with a star on top",
        "location": "the pantry shelf",
        "clue": "crumbs",
        "warning": "If you sneak cookies before supper, the jar gets empty and the floor gets sticky.",
    },
    "key": {
        "label": "key",
        "phrase": "the little brass key",
        "location": "under the rug",
        "clue": "a bright scratch",
        "warning": "Keys belong on hooks, not in pockets where they can vanish.",
    },
    "ribbon": {
        "label": "ribbon",
        "phrase": "a blue ribbon with tiny stars",
        "location": "behind the toy box",
        "clue": "blue thread",
        "warning": "Tiny things can get lost fast when they are left out of their basket.",
    },
}

CULPRITS = {
    "mouse": {
        "label": "mouse",
        "phrase": "a shy gray mouse",
        "tell": "little nibble marks",
    },
    "cat": {
        "label": "cat",
        "phrase": "a sleepy orange cat",
        "tell": "a clump of orange fluff",
    },
    "brother": {
        "label": "brother",
        "phrase": "the big brother",
        "tell": "one green sock",
    },
    "minion": {
        "label": "minion",
        "phrase": "a tiny minion helper",
        "tell": "a yellow glove print",
    },
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Tia", "Zoe"]
BOY_NAMES = ["Finn", "Leo", "Milo", "Toby", "Noah"]
SIDEKICK_NAMES = ["Pip", "Bean", "Dot", "Bix", "Mum"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def choose_culprit(missing: str) -> str:
    if missing == "key":
        return "brother"
    if missing == "ribbon":
        return "cat"
    return "mouse"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES:
        for missing in MISSING_ITEMS:
            culprit = choose_culprit(missing)
            if place == "garden" and missing == "cookie":
                continue
            out.append((place, missing, culprit))
    return out


def rhyme_line(a: str, b: str) -> str:
    return f"{a}, {b}—so the tale could gently sway."


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type="minion",
        label="the minion",
        truthful=True,
    ))
    friend = world.add(Entity(
        id=params.sidekick_name,
        kind="character",
        type="friend",
        label="the helper",
        truthful=True,
    ))
    culprit_cfg = CULPRITS[params.culprit]
    culprit = world.add(Entity(
        id="culprit",
        kind="character",
        type=params.culprit,
        label=culprit_cfg["label"],
        phrase=culprit_cfg["phrase"],
        truthful=False,
        suspect=True,
    ))
    item_cfg = MISSING_ITEMS[params.missing]
    missing = world.add(Entity(
        id="missing",
        kind="thing",
        type=params.missing,
        label=item_cfg["label"],
        phrase=item_cfg["phrase"],
        owner=hero.id,
        caretaker=friend.id,
        hidden=True,
    ))

    world.facts.update(hero=hero, friend=friend, culprit=culprit, missing=missing,
                       place=place, item_cfg=item_cfg, culprit_cfg=culprit_cfg)
    return world


def tell_story(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    culprit: Entity = f["culprit"]
    missing: Entity = f["missing"]
    item_cfg = f["item_cfg"]
    place: Place = f["place"]

    world.say(
        f"At {place.name}, a tiny minion named {hero.id} noticed something gone."
    )
    world.say(
        f"{hero.id} looked high, then low, then asked {friend.id} to help the show."
    )
    world.say(
        rhyme_line(
            f"'A thing is missing, that is a pity'",
            f"'Let us search the hall and the pantry'" if place.indoors else "'Let us search the grass and gate so sprightly'"
        )
    )

    world.para()
    world.say(
        f"They followed clues in careful steps: {item_cfg['clue']} near the floor, "
        f"a small trail by the wall, and a quiet sign that someone had passed by."
    )
    if world.place.caution_kind == "pantry":
        world.say(
            f"The clue warned them to be careful: sneaking into the pantry can make trouble "
            f"when treats are taken without asking."
        )
    elif world.place.caution_kind == "gate":
        world.say(
            f"The clue warned them to be careful: a shut gate should be opened only with help."
        )
    else:
        world.say(
            f"The clue warned them to be careful: rushing about can knock things over."
        )

    world.para()
    world.say(
        f"At last they found {culprit.phrase}. {culprit_cfg['tell'].capitalize()} gave the culprit away."
    )
    world.say(
        f"{hero.id} did not shout. The little minion asked why, and the answer was plain: "
        f"{culprit.id} had taken {missing.phrase} by mistake."
    )
    world.say(
        f"That was the caution in the case: when something is borrowed in secret, it can turn into a mystery."
    )

    world.para()
    world.say(
        f"{culprit.id} gave back the {missing.label}, and {hero.id} put it in its proper place."
    )
    world.say(
        f"{friend.id} smiled, the room felt tidy again, and the case was solved."
    )
    world.say(
        rhyme_line(
            f"'A puzzle was puzzled, but now it is through'",
            f"'A clue led the way, and the careful heart knew'"
        )
    )
    world.say(
        f"By the end, {hero.id} had learned to ask first, look closely, and solve with a calm nose for clues."
    )

    world.solution = culprit.id
    world.clues = [
        item_cfg["clue"],
        culprit_cfg["tell"],
        item_cfg["warning"],
    ]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming whodunit for children about a minion named {f["hero"].id} who solves a mystery.',
        f"Tell a cautionary mystery where {f['hero'].id} and {f['friend'].id} find out who took {f['missing'].phrase}.",
        f"Write a short story with clues, a careful warning, and a solved mystery at {world.place.name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    culprit: Entity = f["culprit"]
    missing: Entity = f["missing"]
    item_cfg = f["item_cfg"]
    place: Place = f["place"]

    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a tiny minion who solves a mystery at {place.name}.",
        ),
        QAItem(
            question=f"What went missing in the story?",
            answer=f"{missing.phrase} went missing, and that made the mystery start.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} search?",
            answer=f"{item_cfg['clue']} helped {hero.id} and {friend.id} follow the trail.",
        ),
        QAItem(
            question=f"Who took the missing thing?",
            answer=f"{culprit.id} took it by mistake, and then gave it back.",
        ),
        QAItem(
            question=f"What lesson did the story give?",
            answer=(
                "The story warned that taking things without asking can cause trouble, "
                "and it is better to ask first and tell the truth."
            ),
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=(
                f"{hero.id} solved it, {missing.label} was returned, and the room felt tidy again."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle where you do not yet know what happened, so you look for clues.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps solve a problem or mystery.",
        ),
        QAItem(
            question="Why should you ask before taking something?",
            answer="You should ask first so the owner knows what is happening and nobody gets worried.",
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a story about figuring out who did something by following clues.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mystery is valid when there is a missing thing, a place, and a culprit.
valid_story(Place, Missing, Culprit) :- place(Place), missing(Missing), culprit(Culprit).

% The chosen culprit must match the missing item's canonical culprit.
matches(Missing, Culprit) :- missing_culprit(Missing, Culprit).
valid_story(Place, Missing, Culprit) :- valid_story(Place, Missing, Culprit), matches(Missing, Culprit).

% A cautionary story should have a warning clue and a returned item.
cautionary(Missing) :- warning(Missing), clue(Missing).
solves(Place, Missing, Culprit) :- valid_story(Place, Missing, Culprit), cautionary(Missing).

#show valid_story/3.
#show solves/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pname, p in PLACES.items():
        lines.append(asp.fact("place", pname))
        if p.indoors:
            lines.append(asp.fact("indoors", pname))
    for mname, m in MISSING_ITEMS.items():
        lines.append(asp.fact("missing", mname))
        lines.append(asp.fact("clue", mname))
        lines.append(asp.fact("warning", mname))
        lines.append(asp.fact("missing_culprit", mname, choose_culprit(mname)))
    for cname in CULPRITS:
        lines.append(asp.fact("culprit", cname))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Validation and generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for missing in MISSING_ITEMS:
            culprit = choose_culprit(missing)
            combos.append((place, missing, culprit))
    return combos


def explain_rejection(place: str, missing: str, culprit: str) -> str:
    return (
        f"(No story: {place} with {missing} is not a valid whodunit setup for the "
        f"chosen culprit {culprit}.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny rhyming cautionary whodunit storyworld with a minion hero."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--missing", choices=sorted(MISSING_ITEMS))
    ap.add_argument("--culprit", choices=sorted(CULPRITS))
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.missing is None or c[1] == args.missing)
        and (args.culprit is None or c[2] == args.culprit)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, missing, culprit = rng.choice(sorted(filtered))
    hero_name = args.name or rng.choice(BOY_NAMES + GIRL_NAMES)
    sidekick_name = args.sidekick or rng.choice(SIDEKICK_NAMES)
    return StoryParams(place=place, missing=missing, culprit=culprit, hero_name=hero_name, sidekick_name=sidekick_name)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.truthful is False:
            bits.append("truthful=False")
        if e.suspect:
            bits.append("suspect=True")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  place={world.place.name}")
    lines.append(f"  clues={world.clues}")
    lines.append(f"  solution={world.solution}")
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
        print(f"{len(asp.atoms(model, 'valid_story'))} valid stories:\n")
        for triple in sorted(set(asp.atoms(model, "valid_story"))):
            print("  ", triple)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place, missing, culprit in valid_combos():
            params = StoryParams(
                place=place,
                missing=missing,
                culprit=culprit,
                hero_name=args.name or "Milo",
                sidekick_name=args.sidekick or "Pip",
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.missing} at {p.place} (culprit: {p.culprit})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
