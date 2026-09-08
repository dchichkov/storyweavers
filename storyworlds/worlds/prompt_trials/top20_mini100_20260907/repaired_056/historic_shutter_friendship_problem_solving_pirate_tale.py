#!/usr/bin/env python3
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402

try:
    import clingo  # noqa: F401
except Exception:
    clingo = None

PLACES = {
    "harbor museum": {
        "setting": "the harbor museum",
        "dock": "museum dock",
        "shutter_kind": "storm shutter",
        "historic_item": "a historic compass",
        "problem": "a stuck shutter",
        "solution": "oiled the hinge and cleared the salt grit",
        "risk": "the rain was blowing straight through the open frame",
    },
    "old lighthouse": {
        "setting": "the old lighthouse",
        "dock": "lighthouse stairs",
        "shutter_kind": "wooden shutter",
        "historic_item": "a historic lantern",
        "problem": "a jammed shutter",
        "solution": "pushed the latch free with a flat key and tied it open",
        "risk": "the beam room was getting dark fast",
    },
    "tide archive": {
        "setting": "the tide archive",
        "dock": "archive pier",
        "shutter_kind": "iron shutter",
        "historic_item": "a historic map case",
        "problem": "a locked shutter",
        "solution": "found the spare chain and reset the latch",
        "risk": "the papers would be soaked by the sea spray",
    },
    "castle quay": {
        "setting": "the castle quay",
        "dock": "castle quay wall",
        "shutter_kind": "harbor shutter",
        "historic_item": "a historic brass spyglass",
        "problem": "a crooked shutter",
        "solution": "straightened the rail and wedged the panel safely",
        "risk": "the wind kept slamming the panel like a sail",
    },
}

CREW = ["Ava", "Bram", "Nia", "Finn", "Mara", "Joss", "Toby", "Lena"]
PIRATE_TITLES = ["captain", "mate", "lookout", "bosun", "sailor"]
MOODS = ["bold", "gentle", "quick-thinking", "steady"]

OPENERS = (
    "The tide had just turned when trouble found the crew.",
    "On a bright gray morning, the harbor kept one secret too tightly.",
    "A pirate crew can spot a storm, but this puzzle was smaller than a storm and trickier too.",
    "The day began with gulls shouting and wood creaking in the wind.",
    "At the edge of the water, a historic place waited for careful hands.",
)

TURNERS = (
    "They paused, listened, and chose the safest fix first.",
    "They stopped blaming the nearest thing and searched for the cause.",
    "They tested one clue at a time, like sailors reading a map by touch.",
    "They checked what moved, what stayed still, and what the wind was doing.",
    "They asked each other questions until the meaning became plain.",
)

DIALOGUES = (
    ("We cannot force it", "Then we will solve it together"),
    ("That shutter will not budge", "Aye, but it still has a hinge and a latch"),
    ("I think I know the answer", "Tell me, mate, and we will test it"),
    ("The first idea is too hasty", "Then let us find the better one"),
    ("Should we call for help", "Not yet. Let us try the careful way first"),
)

ASP_RULES = r"""
feature(friendship).
feature(problem_solving).

setting("harbor_museum").
setting("old_lighthouse").
setting("tide_archive").
setting("castle_quay").

supports_friendship(P) :- setting(P).
supports_problem_solving(P) :- setting(P).

#show supports_friendship/1.
#show supports_problem_solving/1.
"""

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: Optional[str] = None
    carried_by: Optional[str] = None


@dataclass
class StoryParams:
    place: str
    hero: str
    mate: str
    mood: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    trace: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate tale about friendship, a historic shutter, and solving a problem.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    hero = rng.choice(CREW)
    mate = rng.choice([c for c in CREW if c != hero])
    mood = rng.choice(MOODS)
    return StoryParams(place=place, hero=hero, mate=mate, mood=mood)


def _story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join([params.place, params.hero, params.mate, params.mood])
    return int.from_bytes(hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest(), "big")


def asp_facts() -> str:
    from storyworlds import asp
    return "\n".join(asp.fact("setting", p.replace(" ", "_")) for p in PLACES)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    from storyworlds import asp
    program = asp_program("#show supports_friendship/1.\n#show supports_problem_solving/1.")
    model = asp.one_model(program)
    clingo_set = set(asp.atoms(model, "supports_friendship")) | set(asp.atoms(model, "supports_problem_solving"))
    python_set = {(p.replace(" ", "_"),) for p in PLACES}
    if len(clingo_set) == len(python_set) * 2:
        print(f"OK: ASP/Python parity looks good for {len(PLACES)} settings.")
        return 0
    print("MISMATCH:")
    print("clingo:", sorted(clingo_set))
    print("python:", sorted(python_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    meta = PLACES[params.place]
    seed = _story_seed(params)
    rng = random.Random(seed)
    opener = OPENERS[seed % len(OPENERS)]
    turner = TURNERS[(seed // len(OPENERS)) % len(TURNERS)]
    dialogue = DIALOGUES[(seed // (len(OPENERS) * len(TURNERS))) % len(DIALOGUES)]
    world = World(setting=meta["setting"])

    hero = Entity(id=params.hero, kind="character", label="pirate captain", meters={"bravery": 1.2}, memes={"friendship": 1.0, "problem_solving": 0.8}, location=meta["setting"])
    mate = Entity(id=params.mate, kind="character", label="pirate mate", meters={"bravery": 0.9}, memes={"friendship": 1.1, "problem_solving": 1.1}, location=meta["setting"])
    shutter = Entity(id="shutter", kind="object", label=meta["shutter_kind"], meters={"stuck": 1.0}, memes={"trouble": 1.0}, location=meta["setting"])
    historic_item = Entity(id="historic_item", kind="object", label=meta["historic_item"], meters={"safe": 1.0}, memes={"value": 1.0}, carried_by=params.hero)
    world.entities = {e.id: e for e in [hero, mate, shutter, historic_item]}

    opening_detail = f"In {meta['setting']}, {meta['risk']}."
    world.say(opener)
    world.say(f"{params.hero}, a {params.mood} {PIRATE_TITLES[seed % len(PIRATE_TITLES)]}, and {params.mate} hurried to {meta['dock']} where a {meta['problem']} blocked the way.")
    world.say(f"Their job was to protect {meta['historic_item']}, because the old treasure room needed its window sealed before the rain came in.")
    world.say(opening_detail)

    world.para()
    world.say(f"The {meta['shutter_kind']} would not close, and the wind kept prying it open like a sneaky hand.")
    world.say(f"'{dialogue[0]},' said {params.hero}. '{dialogue[1]},' answered {params.mate}.")
    world.say("They were friends, so neither laughed at the other’s first guess.")
    world.say(f"At first, {params.mate} blamed the frame, but {params.hero} pointed out that the latch was full of salt grit.")

    world.para()
    world.say(turner)
    world.say("Together they checked the hinge, the latch, and the rail, one at a time.")
    world.say(f"{params.hero} held the shutter steady while {params.mate} swept away the grit with a cloth and a small brush.")
    world.say(f"Then {params.hero} said, 'Look there.' {params.mate} replied, 'Aye, the latch is the real problem!'")
    world.say("That shared clue turned the trouble from a mystery into a task they could solve.")

    world.para()
    world.say(f"They {meta['solution']}, and the shutter swung shut with a soft thump.")
    world.say(f"Because they worked together, the rain stayed outside and {meta['historic_item']} stayed dry and safe.")
    world.say("Their friendship made the answer easier to find, and their careful problem solving made the fix last.")
    world.say("At sunset, the crew stood under the quiet window, proud of the sturdy shutter and the good work they had done.")
    world.say("The old place looked brighter for it, like a ship mended just in time for a calm voyage home.")

    hero.meters["bravery"] += 0.2
    mate.meters["bravery"] += 0.2
    hero.memes["friendship"] += 0.5
    mate.memes["friendship"] += 0.5
    shutter.meters["stuck"] = 0.0
    shutter.memes["trouble"] = 0.0
    world.trace = [
        "problem:stuck_shutter",
        "clue:salt_grit_in_latch",
        "action:cleaned_and_steadied",
        "result:window_sealed",
    ]

    prompts = [
        f"Write a child-friendly pirate tale set at {meta['setting']} with friendship and problem solving.",
        f"Show how {params.hero} and {params.mate} fix {meta['problem']} without harming {meta['historic_item']}.",
        f"Include a short spoken exchange, a careful clue hunt, and an ending that proves the shutter is fixed.",
    ]

    story_qa = [
        QAItem(
            question="What problem did the pirates face?",
            answer=f"They faced {meta['problem']} at {meta['setting']}, and it kept the window from closing safely.",
        ),
        QAItem(
            question="What clue helped them solve it?",
            answer="They noticed salt grit jammed in the latch, which showed the shutter was not broken beyond repair.",
        ),
        QAItem(
            question="How did friendship matter in the story?",
            answer=f"{params.hero} and {params.mate} listened to each other, shared ideas, and fixed the shutter as a team.",
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"They {meta['solution']}, and the rain stayed outside while {meta['historic_item']} remained dry.",
        ),
    ]

    world_qa = [
        QAItem(question="What is a shutter?", answer="A shutter is a panel that can cover a window or opening to block wind, rain, or light."),
        QAItem(question="What does historic mean?", answer="Historic means important from the past, like something old that people want to protect."),
        QAItem(question="What is problem solving?", answer="Problem solving means finding a careful way to fix something that is not working right."),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for e in sample.world.entities.values():
            bits = []
            if e.label:
                bits.append(f"label={e.label}")
            if e.location:
                bits.append(f"location={e.location}")
            if e.carried_by:
                bits.append(f"carried_by={e.carried_by}")
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            print(f"  {e.id}: {e.kind} {' '.join(bits)}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(place="harbor museum", hero="Ava", mate="Bram", mood="steady"),
    StoryParams(place="old lighthouse", hero="Nia", mate="Finn", mood="quick-thinking"),
    StoryParams(place="tide archive", hero="Mara", mate="Joss", mood="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show supports_friendship/1.\n#show supports_problem_solving/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        from storyworlds import asp
        model = asp.one_model(asp_program("#show supports_friendship/1.\n#show supports_problem_solving/1."))
        print(asp.atoms(model, "supports_friendship"))
        print(asp.atoms(model, "supports_problem_solving"))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < args.n * 20:
            i += 1
            params = resolve_params(args, random.Random((args.seed or 0) + i))
            params.seed = (args.seed or 0) + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
