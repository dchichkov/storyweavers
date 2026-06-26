#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/fake_mystery_to_solve_transformation_pirate_tale.py
===============================================================================================================

A tiny pirate-tale story world about a fake clue, a mystery to solve, and a
visible transformation at the end.

Premise:
- A young pirate finds a fake map on a small ship.
- The crew must solve who made the fake clue and why.
- The answer leads to a transformation: a shy lookout becomes bold after the
  mystery is cleared.

This script is a self-contained classical simulation. The story text is driven
from state changes rather than a frozen template: the pirate's suspicion rises,
the clue is tested, the lie is exposed, and the ending image proves what changed.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captainess"}
        male = {"boy", "father", "dad", "man", "captain"}
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
    sea_mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    fake_reason: str
    tell: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    subject: str
    before: str
    after: str
    trigger: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
    "harbor": Setting(place="the harbor", sea_mood="bright", affords={"search"}),
    "moon_cove": Setting(place="Moon Cove", sea_mood="silver", affords={"search"}),
    "reef": Setting(place="the reef", sea_mood="windy", affords={"search"}),
}

MYSTERIES = {
    "fake_map": Mystery(
        id="fake_map",
        clue="a fake map",
        fake_reason="it was drawn with copied stars and a wrong X",
        tell="the ink was still wet on the edges",
        reveal="a sneaky deckhand had drawn it to send the crew the wrong way",
        tags={"fake", "map", "mystery"},
    ),
    "fake_key": Mystery(
        id="fake_key",
        clue="a fake brass key",
        fake_reason="it was made from painted shell and not real brass",
        tell="it felt light as a feather",
        reveal="a gull had dropped shiny shell bits into the captain's chest",
        tags={"fake", "key", "mystery"},
    ),
    "fake_message": Mystery(
        id="fake_message",
        clue="a fake bottle message",
        fake_reason="the message was copied from an old rhyme",
        tell="the paper smelled of fresh glue",
        reveal="someone on the dock wanted the crew to miss the tide",
        tags={"fake", "message", "mystery"},
    ),
}

TRANSFORMS = {
    "parrot_bold": Transformation(
        id="parrot_bold",
        subject="parrot",
        before="shy",
        after="bold",
        trigger="the truth was finally spoken aloud",
        tags={"transformation", "parrot", "brave"},
    ),
    "boy_captain": Transformation(
        id="boy_captain",
        subject="boy",
        before="small and unsure",
        after="steady and brave",
        trigger="the crew trusted him to lead",
        tags={"transformation", "boy", "brave"},
    ),
    "net_clean": Transformation(
        id="net_clean",
        subject="sail net",
        before="tangled and gray",
        after="bright and neat",
        trigger="the crew washed away the grime after the mystery was solved",
        tags={"transformation", "clean"},
    ),
}

NAMES = ["Finn", "Mira", "Jory", "Nina", "Toby", "Pia", "Nell", "Oren"]
CREW_NAMES = ["Captain Brine", "First Mate Salt", "Old Peg", "Deckhand Dot"]
TRAITS = ["curious", "spirited", "cautious", "cheerful", "stubborn"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    transform: str
    name: str
    crew: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        if "search" not in setting.affords:
            continue
        for mid, mystery in MYSTERIES.items():
            if "fake" not in mystery.tags:
                continue
            for tid, tr in TRANSFORMS.items():
                if "transformation" in tr.tags:
                    combos.append((place, mid, tid))
    return combos


def explain_rejection(mystery: Mystery, transform: Transformation) -> str:
    return (
        f"(No story: this pirate tale needs a fake clue that can be solved and a "
        f"visible transformation at the end. The chosen mystery '{mystery.clue}' "
        f"and transformation '{transform.id}' do not make a clear pair.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Pirate tale story world: a fake clue, a mystery, and a transformation."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--name")
    ap.add_argument("--crew", choices=CREW_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.mystery is None or c[1] == args.mystery)
        and (args.transform is None or c[2] == args.transform)
    ]
    if not combos:
        raise StoryError("(No valid pirate tale matches the given options.)")
    place, mystery, transform = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    crew = args.crew or rng.choice(CREW_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, transform=transform, name=name, crew=crew, trait=trait)


def _format_title_case(s: str) -> str:
    return s[0].upper() + s[1:] if s else s


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    mystery = MYSTERIES[params.mystery]
    transform = TRANSFORMS[params.transform]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type="boy", membranes := {}))  # type: ignore
    hero.type = "boy" if params.name in {"Finn", "Jory", "Toby", "Oren"} else "girl"
    hero.kind = "character"
    hero.meters = {"courage": 0.0, "suspicion": 0.0, "joy": 0.0}
    hero.memes = {"curiosity": 0.0, "hope": 0.0, "pride": 0.0}

    captain = world.add(Entity(id=params.crew, kind="character", type="captain", label=params.crew))
    parrot = world.add(Entity(id="parrot", kind="character", type="bird", label="parrot"))
    parrot.memes = {"shy": 1.0, "bold": 0.0}

    clue = world.add(Entity(id="clue", type="thing", label=mystery.clue, phrase=mystery.clue))
    clue.meters = {"fake": 1.0, "ink": 1.0}

    tool = world.add(Entity(id="lantern", type="thing", label="a lantern", phrase="a tiny lantern"))
    tool.meters = {"light": 1.0}

    # Act 1
    world.say(
        f"{params.name} was a {params.trait} little pirate aboard the ship, and {params.name} liked "
        f"listening to waves slap the hull."
    )
    world.say(
        f"One bright morning, {params.name} found {mystery.clue} tucked under a rope coil near {setting.place}."
    )
    world.say(
        f"It looked important, but something felt off, because {mystery.tell}."
    )

    # Act 2
    world.para()
    hero.meters["suspicion"] += 1.0
    hero.memes["curiosity"] += 1.0
    world.say(
        f"{params.name} took the clue to {params.crew}, and both of them leaned over it like two gulls over bread."
    )
    world.say(
        f"{params.name} noticed the map was wrong, so {params.name} decided it was a mystery to solve."
    )
    world.say(
        f"The crew followed the marks past wet boards and a creaking mast until the fake clue was tested."
    )
    world.say(
        f"Then the trick was clear: {mystery.reveal}."
    )

    # Act 3
    world.para()
    hero.meters["courage"] += 1.0
    hero.memes["hope"] += 1.0
    parrot.memes["shy"] = 0.0
    parrot.memes["bold"] = 1.0
    world.say(
        f"When the lie was gone, the parrot at the mast lifted its head, and {transform.trigger}."
    )
    world.say(
        f"The shy parrot became bold enough to squawk the true path to the crew, and {params.name} smiled."
    )
    world.say(
        f"By sunset, {params.name} was standing straighter, the deck was calm, and the ship sailed on with a real answer instead of a fake one."
    )

    world.facts = {
        "hero": hero,
        "captain": captain,
        "parrot": parrot,
        "clue": clue,
        "setting": setting,
        "mystery": mystery,
        "transform": transform,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short pirate tale for a child that includes {f['mystery'].clue} and ends with a transformation.",
        f"Tell a story where {f['hero'].id} solves a fake-clue mystery aboard a ship and the shy parrot turns bold.",
        f"Write a gentle pirate adventure about a mystery to solve, a fake clue, and a brave ending on {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    transform = f["transform"]
    return [
        QAItem(
            question=f"What did {hero.id} find on the ship?",
            answer=f"{hero.id} found {mystery.clue} tucked under a rope coil.",
        ),
        QAItem(
            question=f"Why was the clue fake?",
            answer=f"It was fake because {mystery.fake_reason}.",
        ),
        QAItem(
            question=f"What happened after the mystery was solved?",
            answer=f"The shy parrot became bold, and {hero.id} stood straighter with a happy smile.",
        ),
        QAItem(
            question=f"What transformation happened at the end?",
            answer=f"{transform.subject} changed from {transform.before} to {transform.after}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fake clue?",
            answer="A fake clue looks useful, but it is made to trick someone and send them the wrong way.",
        ),
        QAItem(
            question="What does a pirate use to find a route?",
            answer="A pirate may use a map, the stars, a compass, or a lookout's call to help find the route.",
        ),
        QAItem(
            question="What is a transformation in a story?",
            answer="A transformation is when something changes into a new form, like a shy helper becoming brave.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is valid if it uses a fake clue.
valid_mystery(M) :- mystery(M), fake_clue(M).

% A transformation is valid if it changes one visible state into another.
valid_transform(T) :- transform(T), before(T,B), after(T,A), B != A.

% A story is valid when it contains both a mystery and a transformation.
valid_story(P, M, T) :- setting(P), valid_mystery(M), valid_transform(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("fake_clue", mid))
    for tid, t in TRANSFORMS.items():
        lines.append(asp.fact("transform", tid))
        lines.append(asp.fact("before", tid, t.before))
        lines.append(asp.fact("after", tid, t.after))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


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


CURATED = [
    StoryParams(place="harbor", mystery="fake_map", transform="parrot_bold", name="Mira", crew="Captain Brine", trait="curious"),
    StoryParams(place="moon_cove", mystery="fake_key", transform="boy_captain", name="Finn", crew="First Mate Salt", trait="spirited"),
    StoryParams(place="reef", mystery="fake_message", transform="net_clean", name="Nell", crew="Old Peg", trait="cautious"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(f"{len(asp_valid_combos())} compatible stories:")
        for row in sorted(set(asp.atoms(model, "valid_story"))):
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.mystery} / {p.transform} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
