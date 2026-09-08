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

FRIENDS = ("Ava", "Ben", "Cleo", "Drew", "Mina", "Oren", "Pia", "Sami")
PLACES = {
    "clockwork workshop": {"setting": "the clockwork workshop", "has_mechanism": True, "has_mystery": True},
    "lantern library": {"setting": "the lantern library", "has_mechanism": True, "has_mystery": True},
    "rainy greenhouse": {"setting": "the rainy greenhouse", "has_mechanism": True, "has_mystery": True},
    "harbor shed": {"setting": "the harbor shed", "has_mechanism": True, "has_mystery": True},
}
MECHANISMS = (
    "little brass latch",
    "wind-up crate",
    "hidden drawer spring",
    "pocket gear puzzle",
    "turning key mechanism",
    "tiny bell mechanism",
    "sliding panel lock",
)
MYSTERY_OBJECTS = (
    "a scratched note",
    "a muddy footprint",
    "a missing key",
    "a half-open box",
    "a crumb trail",
    "a bent map corner",
)
CAUTION_TYPES = (
    "do not force it",
    "do not blame the nearest thing",
    "do not rush the guess",
    "do not touch the fragile part first",
    "do not turn the crank too hard",
)
TWISTS = (
    "the mechanism was not broken; it was protecting something small",
    "the clue pointed to a friend, but the friend was trying to help",
    "the strange noise came from an ordinary tool used in a new way",
    "the locked thing was not hiding treasure, but a safety fix",
    "the missing piece had been moved on purpose to keep it safe",
)
OPENERS = (
    "On a quiet afternoon, a tiny mystery made the room go still.",
    "The case began with one odd sound and one worried look.",
    "Just before the rain started, a strange clue appeared near the shelves.",
    "A small mechanism clicked when nobody expected it to move.",
)
DIALOGUES = (
    ("I think this is broken", "Maybe it is only stuck, so let's be careful"),
    ("That sounds suspicious", "Suspicious does not mean dangerous"),
    ("Should we pry it open", "Not until we know what it protects"),
    ("I do not want to make it worse", "Then we will test one gentle step at a time"),
    ("Could a friend have done this", "A friend might be the reason it is safe"),
)
ASP_RULES = r"""
setting(clockwork_workshop).
setting(lantern_library).
setting(rainy_greenhouse).
setting(harbor_shed).

has_mechanism(clockwork_workshop).
has_mechanism(lantern_library).
has_mechanism(rainy_greenhouse).
has_mechanism(harbor_shed).

story_kind(mystery).
story_kind(friendship).
story_kind(cautionary).
story_kind(twist).

safe_place(P) :- setting(P), has_mechanism(P).
#show safe_place/1.
#show story_kind/1.
"""


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: Optional[str] = None
    carried_by: Optional[str] = None


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    mechanism: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld about a mechanism, friendship, caution, and a twist.")
    ap.add_argument("--place", choices=sorted(PLACES))
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


def _story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    raw = "|".join((params.place, params.hero, params.friend, params.mechanism))
    return int.from_bytes(hashlib.blake2b(raw.encode("utf-8"), digest_size=8).digest(), "big")


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [asp.fact("setting", p.replace(" ", "_")) for p in PLACES]
        + [asp.fact("has_mechanism", p.replace(" ", "_")) for p in PLACES]
        + [asp.fact("story_kind", k) for k in ("mystery", "friendship", "cautionary", "twist")]
    )


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    if not PLACES[place]["has_mechanism"]:
        raise StoryError("This story needs a place with a mechanism.")
    hero = rng.choice(FRIENDS)
    friend = rng.choice([n for n in FRIENDS if n != hero])
    mechanism = rng.choice(MECHANISMS)
    return StoryParams(place=place, hero=hero, friend=friend, mechanism=mechanism)


def _pick(seed: int, items: tuple[str, ...], salt: int) -> str:
    return items[(seed + salt) % len(items)]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.hero == params.friend:
        raise StoryError("The hero and friend must be different characters.")
    if not params.mechanism:
        raise StoryError("A mechanism is required for this story.")

    seed = _story_seed(params)
    opener = _pick(seed, OPENERS, 0)
    dialogue = _pick(seed, DIALOGUES, 3)
    caution = _pick(seed, CAUTION_TYPES, 5)
    twist = _pick(seed, TWISTS, 7)
    object_clue = _pick(seed, MYSTERY_OBJECTS, 11)

    world = World(place=PLACES[params.place]["setting"])
    hero = Entity(id=params.hero, kind="character", label="curious friend", meters={"calm": 0.6, "alert": 0.8}, memes={"trust": 0.9})
    friend = Entity(id=params.friend, kind="character", label="steady friend", meters={"calm": 0.9, "alert": 0.7}, memes={"trust": 1.0})
    mechanism = Entity(id="mechanism", kind="object", label=params.mechanism, location=params.place, meters={"tension": 0.7}, memes={"mystery": 1.0})
    clue = Entity(id="clue", kind="object", label=object_clue, location=params.place, meters={"attention": 0.8}, memes={"importance": 0.7})
    world.entities = {e.id: e for e in (hero, friend, mechanism, clue)}

    world.say(opener)
    world.say(f"{params.hero} and {params.friend} were exploring {world.place} when they heard a soft click from the {params.mechanism}.")
    world.say(f"On the floor nearby lay {object_clue}, and that made the little mystery feel even stranger.")

    world.para()
    world.say(f"'{dialogue[0]},' said {params.hero}. '{dialogue[1]},' said {params.friend}.")
    world.say(f"They agreed on a rule: {caution}.")
    world.say(f"Instead of forcing the {params.mechanism}, they looked for what changed and what stayed still.")
    world.say(f"Their first guess was that {object_clue} meant someone had hidden something valuable.")

    world.para()
    world.say(f"Then they noticed a tiny groove beside the {params.mechanism}, and the click only came when the light touched it at an angle.")
    world.say(f"That was the twist: {twist}.")
    world.say(f"The clue was not a threat at all; it was a warning sign left by a careful friend.")
    world.say(f"{params.friend} smiled and said, 'Good thing we checked before prying.'")
    world.say(f"{params.hero} answered, 'Good thing we trusted each other enough to slow down.'")

    world.para()
    world.say(f"Together they tested the gentle latch, and the {params.mechanism} opened just enough to reveal a safe little space.")
    world.say("Inside was not trouble, but a neatly tucked spare part and a note that said the cover must stay closed until the rain passed.")
    world.say(f"So the friends closed it again, this time understanding the reason behind the mystery.")
    world.say(f"By the end, {params.hero} and {params.friend} had learned that caution can protect friendship as well as secrets.")
    world.say(f"They left the room calmer than before, with the solved clue shining in their minds like a lantern.")

    hero.meters["calm"] = 1.0
    friend.meters["calm"] = 1.1
    mechanism.meters["tension"] = 0.1
    clue.memes["importance"] = 1.0
    world.trace = [
        f"heard_click:{params.mechanism}",
        f"noticed_clue:{object_clue}",
        f"chose_caution:{caution}",
        f"twist:{twist}",
        "opened_safely:yes",
    ]

    prompts = [
        f"Write a child-friendly mystery about {params.hero} and {params.friend} in {world.place}.",
        f"Include the mechanism '{params.mechanism}', a cautious decision, and a friendship moment.",
        f"End with a twist that explains why the clue was not dangerous.",
    ]

    story_qa = [
        QAItem(
            question="What did the friends hear at the beginning?",
            answer=f"They heard a soft click from the {params.mechanism}, which made them suspect there was a mystery nearby.",
        ),
        QAItem(
            question="What clue did they find on the floor?",
            answer=f"They found {object_clue}, which seemed suspicious until they looked more carefully.",
        ),
        QAItem(
            question="What careful choice did they make?",
            answer=f"They chose to {caution} instead of forcing the mechanism open.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {twist}. The clue was part of a safety message, not a danger.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{params.hero} and {params.friend} opened the mechanism gently, found only a safe note and spare part, and closed it again with a better understanding.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of connected parts that moves or opens in a planned way.",
        ),
        QAItem(
            question="Why can caution help in a mystery?",
            answer="Caution helps because careful checking can prevent mistakes and keep people safe.",
        ),
        QAItem(
            question="What does friendship add to a story?",
            answer="Friendship adds trust, teamwork, and kind words that help characters solve problems together.",
        ),
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
            print(f"{e.id}: {' '.join(bits)}")
    if qa:
        print("\n== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show safe_place/1.\n#show story_kind/1.")
    model = asp.one_model(program)
    safe_places = set(asp.atoms(model, "safe_place"))
    kinds = set(asp.atoms(model, "story_kind"))
    py_safe = {(p.replace(" ", "_"),) for p in PLACES}
    py_kinds = {("mystery",), ("friendship",), ("cautionary",), ("twist",)}
    ok = safe_places == py_safe and kinds == py_kinds
    if not ok:
        print("MISMATCH:")
        print("safe_places only in asp:", sorted(safe_places - py_safe))
        print("safe_places only in py:", sorted(py_safe - safe_places))
        print("kinds only in asp:", sorted(kinds - py_kinds))
        print("kinds only in py:", sorted(py_kinds - kinds))
        return 1
    sample = generate(StoryParams(place="clockwork workshop", hero="Ava", friend="Ben", mechanism="little brass latch", seed=7))
    if "Good thing we checked before prying." not in sample.story:
        print("MISMATCH: generated story failed QA expectation.")
        return 1
    print("OK: ASP/Python parity and generated story checks passed.")
    return 0


CURATED = [
    StoryParams(place="clockwork workshop", hero="Ava", friend="Ben", mechanism="little brass latch", seed=1),
    StoryParams(place="lantern library", hero="Cleo", friend="Drew", mechanism="hidden drawer spring", seed=2),
    StoryParams(place="rainy greenhouse", hero="Mina", friend="Oren", mechanism="sliding panel lock", seed=3),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        print(asp.one_model(asp_program("#show safe_place/1.\n#show story_kind/1.")))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        attempts = 0
        while len(samples) < args.n and attempts < args.n * 20:
            attempts += 1
            params = resolve_params(args, random.Random((args.seed or 0) + attempts))
            params.seed = (args.seed or 0) + attempts
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
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
