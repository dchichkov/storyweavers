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
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402

TITLE = "Superhero Story"
FEATURES = ("Twist", "Reconciliation")
WORDS = ("bacon", "remove")

HERO_NAMES = ("Captain Crisp", "Lady Lantern", "Rocket Rook", "Silver Sprout", "Night Kite", "Blue Comet")
SIDEKICK_NAMES = ("Pip", "Mara", "Toby", "Lena", "Iris", "Juno")
VILLAIN_NAMES = ("Dr. Twist", "The Tangle", "Captain Grin", "Mist Maker", "Rattle Rat", "Lord Loop")
LOCATIONS = (
    "Maple Square",
    "Sunset Pier",
    "Pine Station",
    "Bright Market",
    "Clover Park",
    "Clocktower Street",
)
PLACES = {
    "Maple Square": {"inside": False, "has_bacon": True, "has_remove": True, "has_twist": True, "has_reconciliation": True},
    "Sunset Pier": {"inside": False, "has_bacon": True, "has_remove": True, "has_twist": True, "has_reconciliation": True},
    "Pine Station": {"inside": True, "has_bacon": True, "has_remove": True, "has_twist": True, "has_reconciliation": True},
    "Bright Market": {"inside": False, "has_bacon": True, "has_remove": True, "has_twist": True, "has_reconciliation": True},
    "Clover Park": {"inside": False, "has_bacon": True, "has_remove": True, "has_twist": True, "has_reconciliation": True},
    "Clocktower Street": {"inside": False, "has_bacon": True, "has_remove": True, "has_twist": True, "has_reconciliation": True},
}

ASP_RULES = r"""
world(superhero_story).
feature(bacon).
feature(remove).
feature(twist).
feature(reconciliation).

place(maple_square).
place(sunset_pier).
place(pine_station).
place(bright_market).
place(clover_park).
place(clocktower_street).

compatible(P) :- place(P), has_bacon(P), has_remove(P), has_twist(P), has_reconciliation(P).

has_bacon(maple_square).
has_remove(maple_square).
has_twist(maple_square).
has_reconciliation(maple_square).

has_bacon(sunset_pier).
has_remove(sunset_pier).
has_twist(sunset_pier).
has_reconciliation(sunset_pier).

has_bacon(pine_station).
has_remove(pine_station).
has_twist(pine_station).
has_reconciliation(pine_station).

has_bacon(bright_market).
has_remove(bright_market).
has_twist(bright_market).
has_reconciliation(bright_market).

has_bacon(clover_park).
has_remove(clover_park).
has_twist(clover_park).
has_reconciliation(clover_park).

has_bacon(clocktower_street).
has_remove(clocktower_street).
has_twist(clocktower_street).
has_reconciliation(clocktower_street).

#show compatible/1.
#show feature/1.
#show world/1.
"""

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    carried_by: Optional[str] = None
    location: Optional[str] = None


@dataclass
class StoryParams:
    place: str
    hero: str
    sidekick: str
    villain: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
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
    ap = argparse.ArgumentParser(description="A small superhero storyworld with bacon, remove, twist, and reconciliation.")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    if not PLACES[place]["has_bacon"] or not PLACES[place]["has_remove"]:
        raise StoryError("This story needs both bacon and remove in the same place.")
    hero = rng.choice(HERO_NAMES)
    sidekick = rng.choice([name for name in SIDEKICK_NAMES if name != hero])
    villain = rng.choice(VILLAIN_NAMES)
    return StoryParams(place=place, hero=hero, sidekick=sidekick, villain=villain, seed=args.seed)


def _story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    key = "|".join((params.place, params.hero, params.sidekick, params.villain))
    return int.from_bytes(hashlib.blake2b(key.encode("utf-8"), digest_size=8).digest(), "big")


def asp_facts() -> str:
    from storyworlds import asp

    lines = [asp.fact("world", "superhero_story")]
    for feat in FEATURES:
        lines.append(asp.fact("feature", feat.lower()))
    for p, meta in PLACES.items():
        atom = p.lower().replace(" ", "_")
        lines.append(asp.fact("place", atom))
        if meta["has_bacon"]:
            lines.append(asp.fact("has_bacon", atom))
        if meta["has_remove"]:
            lines.append(asp.fact("has_remove", atom))
        if meta["has_twist"]:
            lines.append(asp.fact("has_twist", atom))
        if meta["has_reconciliation"]:
            lines.append(asp.fact("has_reconciliation", atom))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    from storyworlds import asp

    python_set = {p.lower().replace(" ", "_") for p, meta in PLACES.items() if meta["has_bacon"] and meta["has_remove"] and meta["has_twist"] and meta["has_reconciliation"]}
    model = asp.one_model(asp_program("#show compatible/1."))
    clingo_set = {args[0] for args in asp.atoms(model, "compatible")}
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python reasoning ({len(clingo_set)} facts).")
        sample = generate(StoryParams(place=sorted(PLACES)[0], hero=HERO_NAMES[0], sidekick=SIDEKICK_NAMES[0], villain=VILLAIN_NAMES[0], seed=7))
        assert "bacon" in sample.story.lower()
        assert "remove" in sample.story.lower()
        assert any('"' in sample.story for _ in [0]) or "'" in sample.story
        return 0
    print("MISMATCH:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    seed = _story_seed(params)
    rng = random.Random(seed)
    place_meta = PLACES[params.place]
    twist_type = rng.choice(
        (
            "the bait was a bacon-shaped decoy",
            "the alarm had been triggered by a sticky ribbon labeled remove",
            "the villain had hidden the real clue inside a lunch bag",
            "the strange message was meant for a helper named Remove, not an order to take things away",
            "the missing item was never stolen; it had been moved for safety",
        )
    )
    reconciliation_type = rng.choice(
        (
            "they apologized, listened again, and worked together",
            "they shared the truth, fixed the mistake, and became allies",
            "they let the misunderstanding go and chose a kinder plan",
            "they told the crowd what really happened and made peace",
        )
    )
    action_line = rng.choice(
        (
            "Captain Crisp and the sidekick opened the latch and removed the bacon from the smoke trap before it could burn",
            "Lady Lantern used a bright beam to remove the jammed panel while the others shielded the sizzling bacon",
            "Rocket Rook flipped the switch, then carefully removed the bacon strips from the villain's spinning gadget",
            "Silver Sprout tugged the red cord to remove the net and rescue the bacon breakfast from the rooftop",
        )
    )
    ending_image = rng.choice(
        (
            "At sunset, the bacon cooled on a clean plate, and the whole square felt lighter after the reconciliation.",
            "When the dust settled, the bacon was safe, and even the twisty villain nodded at the new peace.",
            "By evening, the bacon smell drifted over the street, and the heroes stood together, friends again.",
            "The last orange light shone on the rescued bacon as the team smiled through their reconciliation.",
        )
    )

    world = World(place=params.place)
    hero = Entity(id=params.hero, kind="character", label="hero", type="hero", meters={"bravery": 1.0, "speed": 0.8}, memes={"hope": 1.0})
    sidekick = Entity(id=params.sidekick, kind="character", label="sidekick", type="sidekick", meters={"bravery": 0.6, "speed": 0.7}, memes={"curious": 0.9})
    villain = Entity(id=params.villain, kind="character", label="villain", type="villain", meters={"trickiness": 0.9}, memes={"pride": 0.8})
    bacon = Entity(id="bacon", kind="object", label="bacon", type="food", location=params.place)
    sign = Entity(id="sign", kind="object", label="remove sign", type="sign", location=params.place)
    world.entities = {e.id: e for e in (hero, sidekick, villain, bacon, sign)}

    world.say(f"At {params.place}, {params.hero} and {params.sidekick} wore their capes bright under the afternoon sky.")
    world.say(f"They were a small superhero team, and they always tried to keep the city safe.")
    world.say(f"Then {params.villain} caused a twisty problem near the snack cart, where a tray of bacon sat waiting.")
    world.say(f"'{params.sidekick},' said {params.hero}, 'something is wrong here.'")
    world.say(f"'{params.hero},' replied {params.sidekick}, 'I can see the smoke, but I need the real clue.'")

    world.para()
    world.say(f"The trouble looked simple at first, but it was not. The first twist was that {twist_type}.")
    world.say(f"{params.sidekick} pointed at a sign that said remove, and for a moment they thought it meant the bacon should be thrown away.")
    world.say(f"'{params.sidekick}, wait,' said {params.hero}. 'That word may be a label, not an order.'")
    world.say(f"'{params.hero},' said {params.sidekick}, 'then let's check before we rush.'")
    world.say(f"They listened, looked, and noticed the villain laughing beside the cart.")

    world.para()
    world.say(f"The second twist was clearer: {params.villain} had planned to distract everyone while the real danger ticked under the tray.")
    world.say(f"That is when {action_line}.")
    world.say(f"{params.sidekick} exclaimed, 'Now I understand! The sign was telling us which panel to remove.'")
    world.say(f"{params.hero} answered, 'Yes, and the bacon was the thing we had to save.'")
    world.say(f"The team solved the puzzle by following the clue instead of the first guess, and that turned fear into {reconciliation_type}.")

    world.para()
    world.say(f"{params.villain} paused, looked at the heroes, and finally admitted, 'I wanted attention, not a fight.'")
    world.say(f"{params.hero} replied, 'Then let's do this the right way.'")
    world.say(f"{params.sidekick} said, 'We can fix the mess together, and no one has to stay angry.'")
    world.say(f"So the heroes and the villain shared the cleanup, which was the reconciliation that changed the whole scene.")
    world.say(f"With the danger gone, the city could enjoy breakfast again.")
    world.say(ending_image)

    hero.meters["bravery"] = 1.2
    sidekick.meters["bravery"] = 0.9
    villain.memes["pride"] = 0.2
    bacon.meters["sizzle"] = 0.0
    world.trace = [
        f"place:{params.place}",
        f"twist:{twist_type}",
        f"action:{action_line}",
        f"reconciliation:{reconciliation_type}",
    ]

    prompts = [
        f"Write a {TITLE} story in {params.place} that includes bacon, remove, a twist, and reconciliation.",
        f"Show how {params.hero} and {params.sidekick} misread the word remove and then fix the mistake.",
        f"Tell a child-friendly superhero tale where a villain makes trouble, the heroes talk, and the ending proves the change.",
    ]

    story_qa = [
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {twist_type}. That changed how the heroes understood the scene.",
        ),
        QAItem(
            question="Why did the heroes talk before acting?",
            answer="They talked first because the clue could mean more than one thing, and they did not want to make the wrong choice too fast.",
        ),
        QAItem(
            question="How did they use the word remove?",
            answer="At first they thought remove meant throw away, but then they learned it was a label for the panel they needed to open.",
        ),
        QAItem(
            question="What happened to the bacon?",
            answer="The heroes saved the bacon from danger and kept it from being ruined.",
        ),
        QAItem(
            question="What was the reconciliation?",
            answer=f"The reconciliation was that {reconciliation_type}, so the heroes and the villain ended the story in peace.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a superhero story?",
            answer="A superhero story is a tale about brave characters who use their powers, teamwork, and good choices to solve problems.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace after a disagreement or misunderstanding.",
        ),
        QAItem(
            question="What does twist mean in a story?",
            answer="A twist is a surprising turn that changes what the characters or readers thought was happening.",
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
            bits = [f"kind={e.kind}", f"type={e.type}"]
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
            print(f"{e.id}: " + ", ".join(bits))
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
    StoryParams(place="Maple Square", hero="Captain Crisp", sidekick="Pip", villain="Dr. Twist", seed=11),
    StoryParams(place="Sunset Pier", hero="Lady Lantern", sidekick="Mara", villain="The Tangle", seed=22),
    StoryParams(place="Bright Market", hero="Rocket Rook", sidekick="Lena", villain="Captain Grin", seed=33),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        from storyworlds import asp

        model = asp.one_model(asp_program("#show compatible/1.\n"))
        print(asp.atoms(model, "compatible"))
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
