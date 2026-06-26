#!/usr/bin/env python3
"""
storyworlds/worlds/notion_wacko_sincere_mystery_to_solve_mystery.py
===================================================================

A small Mystery-to-Solve story world about a sincere child, a wacko clue, and
a careful notion that helps uncover the answer.

Seed idea:
- A child has a sincere notion that something has gone missing.
- The clue trail looks a little wacko at first.
- The child keeps going, follows evidence, and solves the mystery.
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
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = True
    search_spots: tuple[str, ...] = ("table", "chair", "shelf", "box", "corner")


@dataclass
class Mystery:
    missing: str
    missing_phrase: str
    missing_type: str
    missing_place: str
    culprit: str
    culprit_phrase: str
    culprit_type: str
    clue_kind: str
    clue_place: str
    clue_noise: str
    solve_method: str
    reveal_line: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

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
    "house": Setting(place="the house", indoors=True),
    "library": Setting(place="the library", indoors=True),
    "garden_shed": Setting(place="the garden shed", indoors=True),
}

MYSTERIES = {
    "missing_cookie": Mystery(
        missing="cookie",
        missing_phrase="a star-shaped cookie",
        missing_type="cookie",
        missing_place="the tin",
        culprit="mouse",
        culprit_phrase="a tiny mouse",
        culprit_type="mouse",
        clue_kind="crumbs",
        clue_place="the rug",
        clue_noise="a wacko squeak from under the chair",
        solve_method="follow the crumb trail",
        reveal_line="The mouse had carried the cookie to a little nest of napkins and shared it with a younger mouse.",
    ),
    "lost_key": Mystery(
        missing="key",
        missing_phrase="a brass key",
        missing_type="key",
        missing_place="the hook by the door",
        culprit="dog",
        culprit_phrase="a wacko puppy",
        culprit_type="dog",
        clue_kind="pawprints",
        clue_place="the muddy step",
        clue_noise="a wiggly jingle from the toy basket",
        solve_method="check the toy basket",
        reveal_line="The puppy had nosed the key into the toy basket and fallen asleep beside it.",
    ),
    "vanished_crayon": Mystery(
        missing="crayon",
        missing_phrase="a blue crayon",
        missing_type="crayon",
        missing_place="the cup",
        culprit="bird",
        culprit_phrase="a cheerful bird",
        culprit_type="bird",
        clue_kind="feathers",
        clue_place="the windowsill",
        clue_noise="a funny flutter near the curtain",
        solve_method="look at the windowsill",
        reveal_line="The bird had dropped the crayon beside its nest of shiny buttons.",
    ),
}

GIRL_NAMES = ["Mina", "Lia", "Nora", "Zoe", "Ivy", "Maya"]
BOY_NAMES = ["Theo", "Ben", "Leo", "Milo", "Finn", "Eli"]
TRAITS = ["sincere", "curious", "careful", "brave", "gentle"]


@dataclass
class StoryState:
    hero: Entity
    parent: Entity
    missing: Entity
    culprit: Entity
    clue: Entity
    mystery: Mystery
    found: bool = False
    solved: bool = False


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny mystery story world about a sincere notion and a wacko clue."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, mid) for place in SETTINGS for mid in MYSTERIES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.mystery is None or c[1] == args.mystery)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery = rng.choice(sorted(combos))
    m = MYSTERIES[mystery]
    if args.gender is None:
        gender = rng.choice(["girl", "boy"])
    else:
        gender = args.gender
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, parent=parent, trait=trait)


def _make_world(params: StoryParams) -> StoryState:
    setting = SETTINGS[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name, kind="character", type=params.gender, label=params.name,
        meters={"hope": 0.0}, memes={"sincere": 1.0, "notion": 1.0, "worry": 0.0}
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"
    ))
    missing = world.add(Entity(
        id="Missing", type=mystery.missing_type, label=mystery.missing,
        phrase=mystery.missing_phrase, owner=hero.id, hidden=True
    ))
    culprit = world.add(Entity(
        id="Culprit", type=mystery.culprit_type, label=mystery.culprit,
        phrase=mystery.culprit_phrase
    ))
    clue = world.add(Entity(
        id="Clue", type="clue", label=mystery.clue_kind, phrase=mystery.clue_kind
    ))
    state = StoryState(hero=hero, parent=parent, missing=missing, culprit=culprit, clue=clue, mystery=mystery)
    world.facts["state"] = state
    return state


def _world_from_state(state: StoryState) -> World:
    place = "the house"
    setting = SETTINGS["house"]
    world = World(setting)
    for ent in [state.hero, state.parent, state.missing, state.culprit, state.clue]:
        world.entities[ent.id] = ent
    return world


def tell(params: StoryParams) -> World:
    state = _make_world(params)
    world = _world_from_state(state)
    m = state.mystery
    hero = state.hero
    parent = state.parent

    world.say(
        f"{hero.id} was a little {params.trait} {params.gender} with a sincere notion: "
        f"{hero.pronoun('subject').capitalize()} wanted to solve a mystery."
    )
    world.say(
        f"Something important had gone missing: {m.missing_phrase}. "
        f"{hero.id} looked around {world.setting.place} and decided to start with a careful notion, not a wild guess."
    )

    world.para()
    world.say(
        f"At first, the clues seemed wacko. There was {m.clue_noise}, and the first sign was {m.clue_kind} near {m.clue_place}."
    )
    hero.memes["worry"] += 1.0
    hero.meters["search"] = 1.0
    world.say(
        f"{hero.id} stayed sincere anyway. {hero.pronoun('subject').capitalize()} said, "
        f"\"I can solve this if I follow the clues one by one.\""
    )

    world.para()
    world.say(
        f"{hero.id} checked under the table, behind a chair, and beside the box. "
        f"Then {hero.pronoun('subject')} remembered {m.solve_method}."
    )
    clue_found = True
    hero.meters["careful_search"] = 1.0 if clue_found else 0.0
    if clue_found:
        world.say(
            f"The trail made sense after all, because {m.clue_kind} led straight to the hidden spot."
        )
        state.found = True
        state.solved = True
        missing.hidden = False
        world.say(m.reveal_line)
        world.say(
            f"{hero.id}'s {params.parent} smiled, and the room felt calm again. "
            f"The sincere notion had been right."
        )

    world.facts.update(state=state, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    s: StoryState = world.facts["state"]
    m = s.mystery
    return [
        f'Write a short mystery for a child named {p.name} that includes the words "notion", "wacko", and "sincere".',
        f"Tell a gentle solve-the-mystery story where {p.name} has a sincere notion and follows a wacko clue to find {m.missing_phrase}.",
        f'Write a child-friendly mystery set in {SETTINGS[p.place].place} that ends with the mystery solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    s: StoryState = world.facts["state"]
    m = s.mystery
    hero = s.hero
    parent = s.parent
    return [
        QAItem(
            question=f"What did {p.name} want to do in the story?",
            answer=f"{p.name} wanted to solve a mystery and find {m.missing_phrase}.",
        ),
        QAItem(
            question=f"Why did the clues seem wacko at first?",
            answer=f"They seemed wacko because the first sign was {m.clue_noise}, which did not look like an answer right away.",
        ),
        QAItem(
            question=f"What careful notion helped {p.name} solve the mystery?",
            answer=f"{p.name} kept a sincere notion to follow the clues one by one instead of guessing too fast.",
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=f"The mystery ended when {p.name} followed {m.solve_method} and found {m.reveal_line.lower()}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps you find out what really happened.",
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer="To solve a mystery means to figure out the answer by paying attention and putting the clues together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="house", mystery="missing_cookie", name="Mina", gender="girl", parent="mother", trait="sincere"),
    StoryParams(place="library", mystery="lost_key", name="Theo", gender="boy", parent="father", trait="curious"),
    StoryParams(place="garden_shed", mystery="vanished_crayon", name="Ivy", gender="girl", parent="mother", trait="careful"),
]


ASP_RULES = r"""
valid_story(P, M) :- place(P), mystery(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
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


def explain_rejection() -> str:
    return "(No story: this mystery world is fully paired; try a different explicit setting or mystery.)"


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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.mystery is None or c[1] == args.mystery)
    ]
    if not combos:
        raise StoryError(explain_rejection())
    place, mystery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, parent=parent, trait=trait)


def valid_story_params() -> list[StoryParams]:
    out = []
    for place, mystery in valid_combos():
        for gender in ["girl", "boy"]:
            name = GIRL_NAMES[0] if gender == "girl" else BOY_NAMES[0]
            out.append(StoryParams(place=place, mystery=mystery, name=name, gender=gender, parent="mother", trait="sincere"))
    return out


def build_and_generate(args: argparse.Namespace, rng: random.Random) -> StorySample:
    params = resolve_params(args, rng)
    params.seed = args.seed
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, mystery) combos:\n")
        for place, mystery in combos:
            print(f"  {place:12} {mystery}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
