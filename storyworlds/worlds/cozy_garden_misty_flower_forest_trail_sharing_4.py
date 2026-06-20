#!/usr/bin/env python3
"""A gentle whodunit about a borrowed flower, a forest trail, and a better way to share."""

from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from results import QAItem, StoryError, StorySample


SOURCE_TALE = """
At the start of a forest trail sits a cozy garden with one misty flower in a painted tin.
One morning the flower disappears, and a careful child treats the empty tin like a whodunit.
Garden clues lead down the trail to a friend who quietly borrowed the bloom to help someone
in trouble. The mystery ends with the flower returned, the kindness understood, and a new
sharing box that makes the whole trail feel more welcome.
""".strip()


@dataclass(frozen=True)
class SleuthProfile:
    id: str
    name: str
    noticing_style: str
    casebook: str


@dataclass(frozen=True)
class BorrowerProfile:
    id: str
    name: str
    clue_text: str
    clue_object: str
    gear: str
    action_text: str
    reason_text: str
    expected_case: str


@dataclass(frozen=True)
class TrailCaseProfile:
    id: str
    recipient_name: str
    trail_spot: str
    trouble_text: str
    relief_text: str
    need_label: str
    comfort_item: str


@dataclass
class StoryParams:
    sleuth: str
    borrower: str
    trail_case: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    name: str
    kind: str
    location: str
    meters: dict[str, int] = field(default_factory=dict)
    memes: dict[str, int] = field(default_factory=dict)


@dataclass
class Event:
    id: str
    text: str
    actor: str
    target: str | None = None
    location: str | None = None
    delta: dict[str, int] = field(default_factory=dict)


@dataclass
class FlowerCaseWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    meters: dict[str, int] = field(
        default_factory=lambda: {
            "mystery": 0,
            "evidence": 0,
            "sharing": 0,
            "trust": 0,
            "comfort": 0,
            "fairness": 0,
        }
    )
    facts: dict[str, object] = field(default_factory=dict)

    def add_entity(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def record(
        self,
        event_id: str,
        text: str,
        actor: str,
        target: str | None = None,
        location: str | None = None,
        **delta: int,
    ) -> None:
        self.history.append(
            Event(
                id=event_id,
                text=text,
                actor=actor,
                target=target,
                location=location,
                delta=dict(delta),
            )
        )
        for key, value in delta.items():
            self.meters[key] = self.meters.get(key, 0) + value


SLEUTHS: dict[str, SleuthProfile] = {
    "mara": SleuthProfile(
        "mara",
        "Mara",
        "noticed when even one pebble had been nudged out of line",
        "a bark-paper casebook",
    ),
    "kit": SleuthProfile(
        "kit",
        "Kit",
        "liked to crouch so quietly that clues seemed ready to whisper back",
        "a button compass tucked in one pocket",
    ),
    "oona": SleuthProfile(
        "oona",
        "Oona",
        "could tell which way a ribbon had fluttered by the twist it left behind",
        "a tiny pencil tied with blue string",
    ),
    "pax": SleuthProfile(
        "pax",
        "Pax",
        "counted petals the way other children counted coins",
        "a seed tin full of question marks",
    ),
}


BORROWERS: dict[str, BorrowerProfile] = {
    "nora": BorrowerProfile(
        "nora",
        "Nora",
        "a ring of lavender steam and one striped mitten thread on the bench",
        "striped mitten thread",
        "a striped tea flask",
        "set the flower beside the flask so its cool scent could make the rest stop feel gentle",
        "Nora wanted to share something beautiful before the shivers made the morning feel bigger than it was",
        "chill",
    ),
    "benji": BorrowerProfile(
        "benji",
        "Benji",
        "a dusting of green chalk and a flap of map paper caught under the watering can",
        "green chalk dust",
        "a foldout trail map tied with green string",
        "propped the flower on a forked sign where the pale petals could point like a lantern",
        "Benji wanted the bloom to guide a worried walker before the mist made every turn look the same",
        "lost",
    ),
    "lila": BorrowerProfile(
        "lila",
        "Lila",
        "a dab of berry salve and a neat bandage wrapper by the gate latch",
        "bandage wrapper",
        "a berry-red bandage tin",
        "rested the flower beside the bandage tin so its soft smell could steady a scraped-up friend",
        "Lila hoped the flower would keep pain from turning into panic",
        "scrape",
    ),
    "remy": BorrowerProfile(
        "remy",
        "Remy",
        "a tiny brass bell cord and a drip of candle wax near the trellis post",
        "brass bell cord",
        "a hand lantern with a little brass bell",
        "hung the flower near the lantern handle so its misty petals could make a shadowy bend feel friendly",
        "Remy wanted the trail to look kinder to a child frightened by the fog",
        "fog",
    ),
}


TRAIL_CASES: dict[str, TrailCaseProfile] = {
    "chill": TrailCaseProfile(
        "chill",
        "Pru",
        "fern turn",
        "sat with chattering teeth beside a stone bench after the mist soaked her sleeves",
        "By dusk, Pru was sipping warm tea and laughing at the steam instead of hiding in it.",
        "warming a chilled friend",
        "the tea flask",
    ),
    "lost": TrailCaseProfile(
        "lost",
        "Niko",
        "pebble fork",
        "stood at the split path with wet lashes and no idea which way led back to the picnic clearing",
        "By dusk, Niko could point out the right path on his own and walked it with a steadier smile.",
        "guiding a lost walker",
        "the trail map",
    ),
    "scrape": TrailCaseProfile(
        "scrape",
        "Tessa",
        "stepping-log bridge",
        "held one scraped knee and tried very hard not to cry beside the stepping-log bridge",
        "By dusk, Tessa was testing the bridge again with a neat bandage and a much braver grin.",
        "calming an injured friend",
        "the bandage tin",
    ),
    "fog": TrailCaseProfile(
        "fog",
        "Asa",
        "Owl Hollow",
        "froze at the foggy bend called Owl Hollow because every stump looked like a giant in the mist",
        "By dusk, Asa was trotting past Owl Hollow with the lantern swinging and no fear left in his shoulders.",
        "comforting a frightened walker",
        "the hand lantern",
    ),
}


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.sleuth not in SLEUTHS:
        return False, f"unknown sleuth: {params.sleuth}"
    if params.borrower not in BORROWERS:
        return False, f"unknown borrower: {params.borrower}"
    if params.trail_case not in TRAIL_CASES:
        return False, f"unknown trail case: {params.trail_case}"
    borrower = BORROWERS[params.borrower]
    if borrower.expected_case != params.trail_case:
        expected = TRAIL_CASES[borrower.expected_case]
        actual = TRAIL_CASES[params.trail_case]
        return (
            False,
            f"{borrower.name} only borrows the flower for {expected.need_label}, not for {actual.need_label}.",
        )
    return True, ""


def explain_rejection(sleuth: str, borrower: str, trail_case: str) -> str:
    params = StoryParams(sleuth=sleuth, borrower=borrower, trail_case=trail_case)
    ok, reason = valid_params(params)
    if ok:
        return "The requested options are reasonable."
    return reason


def all_params() -> list[StoryParams]:
    rows: list[StoryParams] = []
    for sleuth in SLEUTHS:
        for borrower in BORROWERS:
            for trail_case in TRAIL_CASES:
                params = StoryParams(sleuth=sleuth, borrower=borrower, trail_case=trail_case)
                if valid_params(params)[0]:
                    rows.append(params)
    return rows


def make_world(params: StoryParams) -> FlowerCaseWorld:
    sleuth = SLEUTHS[params.sleuth]
    borrower = BORROWERS[params.borrower]
    trail_case = TRAIL_CASES[params.trail_case]
    world = FlowerCaseWorld(params=params)
    world.add_entity(
        Entity(
            id="sleuth",
            name=sleuth.name,
            kind="child sleuth",
            location="cozy garden",
            meters={"steps": 0, "suspects_named": 0},
            memes={"Curiosity": 3, "Worry": 0, "Warmth": 1},
        )
    )
    world.add_entity(
        Entity(
            id="borrower",
            name=borrower.name,
            kind="helpful child",
            location=trail_case.trail_spot,
            meters={"left_card": 0, "borrowed_quietly": 1},
            memes={"Generosity": 3, "Guilt": 1},
        )
    )
    world.add_entity(
        Entity(
            id="recipient",
            name=trail_case.recipient_name,
            kind="trail child",
            location=trail_case.trail_spot,
            meters={"steady": 0},
            memes={"Worry": 2, "Relief": 0},
        )
    )
    world.add_entity(
        Entity(
            id="flower",
            name="the misty flower",
            kind="flower",
            location="cozy garden",
            meters={"petals": 11, "borrowed": 0, "dew": 3},
            memes={"Comfort": 3, "Wonder": 2},
        )
    )
    world.add_entity(
        Entity(
            id="garden",
            name="the cozy garden",
            kind="place",
            location="forest trail edge",
            meters={"pots": 4, "borrow_rules": 0},
            memes={"Coziness": 3, "Welcome": 2},
        )
    )
    world.add_entity(
        Entity(
            id="share_box",
            name="the borrowing box",
            kind="box",
            location="cozy garden gate",
            meters={"cards": 0, "pencils": 1},
            memes={"Fairness": 0},
        )
    )
    world.facts["source_tale"] = SOURCE_TALE
    world.facts["setting"] = "forest trail"
    world.facts["opening_image"] = (
        f"At the place where the forest trail widened into a cozy garden, {sleuth.name} liked to sit with "
        f"{sleuth.casebook}. The prettiest thing there was a misty flower in a painted tin, pale as dawn fog "
        "and loved by every child who passed."
    )
    world.facts["sleuth_style"] = sleuth.noticing_style
    world.facts["mystery_question"] = (
        f"Who had carried off the misty flower, and why had they taken it away from the cozy garden?"
    )
    world.facts["clue_text"] = borrower.clue_text
    world.facts["clue_object"] = borrower.clue_object
    world.facts["need_label"] = trail_case.need_label
    return world


def open_case(world: FlowerCaseWorld) -> None:
    sleuth = SLEUTHS[world.params.sleuth]
    flower = world.entities["flower"]
    flower.location = "missing"
    flower.meters["borrowed"] = 1
    world.entities["sleuth"].memes["Worry"] += 2
    world.record(
        "open_case",
        (
            f"That morning, {sleuth.name} reached the painted tin and found only damp soil and one cool petal. "
            f"Because {sleuth.name} {sleuth.noticing_style}, the empty place did not feel like plain bad luck. "
            f"It felt like the opening of a very small whodunit."
        ),
        actor="sleuth",
        target="flower",
        location="cozy garden",
        mystery=3,
        trust=-1,
    )


def read_garden_clue(world: FlowerCaseWorld) -> None:
    sleuth = SLEUTHS[world.params.sleuth]
    borrower = BORROWERS[world.params.borrower]
    world.entities["sleuth"].meters["suspects_named"] += 1
    world.entities["sleuth"].memes["Curiosity"] += 1
    world.record(
        "garden_clue",
        (
            f"{sleuth.name} checked the bench, the latch, and the watering shelf until the clue appeared: "
            f"{borrower.clue_text}. That clue belonged with {borrower.name}, who always carried {borrower.gear}, "
            "so the case finally had a fair direction."
        ),
        actor="sleuth",
        target="borrower",
        location="cozy garden",
        evidence=2,
        fairness=1,
    )


def follow_trail(world: FlowerCaseWorld) -> None:
    sleuth = SLEUTHS[world.params.sleuth]
    trail_case = TRAIL_CASES[world.params.trail_case]
    world.entities["sleuth"].location = trail_case.trail_spot
    world.entities["sleuth"].meters["steps"] += 1
    world.entities["flower"].location = trail_case.trail_spot
    world.record(
        "follow_trail",
        (
            f"Following the clue, {sleuth.name} hurried down the forest trail to {trail_case.trail_spot}. "
            f"There was {trail_case.recipient_name}, who {trail_case.trouble_text}, and nearby the misty flower "
            "glimmered exactly where comfort was needed."
        ),
        actor="sleuth",
        target="recipient",
        location=trail_case.trail_spot,
        evidence=1,
        comfort=1,
    )


def reveal_borrowing(world: FlowerCaseWorld) -> None:
    borrower = BORROWERS[world.params.borrower]
    trail_case = TRAIL_CASES[world.params.trail_case]
    borrower_entity = world.entities["borrower"]
    recipient_entity = world.entities["recipient"]
    recipient_entity.meters["steady"] = 3
    recipient_entity.memes["Worry"] = 0
    recipient_entity.memes["Relief"] = 3
    borrower_entity.memes["Guilt"] = 0
    borrower_entity.memes["Generosity"] += 1
    world.entities["flower"].memes["Comfort"] += 1
    world.record(
        "reveal_borrowing",
        (
            f"{borrower.name} stepped out at once and told the truth. {borrower.name} had borrowed the flower and "
            f"{borrower.action_text}. {borrower.reason_text}, because {trail_case.recipient_name} {trail_case.trouble_text}."
        ),
        actor="borrower",
        target="recipient",
        location=trail_case.trail_spot,
        mystery=-3,
        sharing=3,
        comfort=2,
        trust=2,
    )


def build_sharing_fix(world: FlowerCaseWorld) -> None:
    sleuth = SLEUTHS[world.params.sleuth]
    borrower = BORROWERS[world.params.borrower]
    world.entities["flower"].location = "cozy garden gate"
    world.entities["garden"].meters["borrow_rules"] = 1
    world.entities["share_box"].meters["cards"] = 1
    world.entities["share_box"].memes["Fairness"] = 3
    world.entities["borrower"].meters["left_card"] = 1
    world.entities["sleuth"].memes["Worry"] = 0
    world.entities["sleuth"].memes["Warmth"] += 2
    world.record(
        "sharing_fix",
        (
            f"Then the case changed shape. It was not theft, only sharing done too quietly, so {sleuth.name} "
            "did not scold. Instead, the children carried the flower back together and set a small borrowing box "
            f"by the gate. {borrower.name} wrote the first card, promising to ask or leave a note before borrowing again."
        ),
        actor="sleuth",
        target="share_box",
        location="cozy garden gate",
        sharing=2,
        fairness=2,
        trust=1,
    )
    world.facts["ending"] = "happy_shared_return"


def render_story(world: FlowerCaseWorld) -> str:
    trail_case = TRAIL_CASES[world.params.trail_case]
    final_image = (
        "At sunset, the misty flower was back at the cozy garden gate in its painted tin, and beside it stood "
        'a card box that read, "Borrow to help. Leave a note. Return by sunset." '
        f"{trail_case.relief_text}"
    )
    world.facts["final_image"] = final_image
    return "\n".join(
        [
            str(world.facts["opening_image"]),
            f"{world.history[0].text} {world.facts['mystery_question']}",
            world.history[1].text,
            world.history[2].text,
            world.history[3].text,
            world.history[4].text,
            final_image,
        ]
    )


def make_prompts(world: FlowerCaseWorld) -> list[str]:
    borrower = BORROWERS[world.params.borrower]
    trail_case = TRAIL_CASES[world.params.trail_case]
    return [
        "Write a child-friendly whodunit set on a forest trail.",
        "Include the exact phrases cozy garden and misty flower.",
        f"Let the mystery end happily when {borrower.name} borrows the flower for {trail_case.need_label} and the children create a fair sharing rule.",
    ]


def make_story_qa(world: FlowerCaseWorld) -> list[QAItem]:
    sleuth = SLEUTHS[world.params.sleuth]
    borrower = BORROWERS[world.params.borrower]
    trail_case = TRAIL_CASES[world.params.trail_case]
    return [
        QAItem(
            question="What started the whodunit?",
            answer=(
                "The whodunit began when the painted tin in the cozy garden held only damp soil and the misty flower was gone. "
                f"That empty space felt important to {sleuth.name}, so the morning turned into a case instead of an ordinary mistake."
            ),
        ),
        QAItem(
            question=f"Which clue pointed {sleuth.name} toward the answer?",
            answer=(
                f"The key clue was {world.facts['clue_text']}. It pointed toward {borrower.name} because the clue matched "
                f"{borrower.name}'s usual gear and gave the mystery a fair trail to follow."
            ),
        ),
        QAItem(
            question=f"Why did {borrower.name} borrow the flower?",
            answer=(
                f"{borrower.name} borrowed the flower to help {trail_case.recipient_name}, who {trail_case.trouble_text}. "
                f"The flower was meant to share comfort beside {trail_case.comfort_item}, not to be hidden away forever."
            ),
        ),
        QAItem(
            question="What proved the ending was happy?",
            answer=(
                "The ending was happy because the children understood the kindness behind the borrowing and solved the problem together. "
                "They returned the flower, added a borrowing box, and turned the mystery into a clearer way to share."
            ),
        ),
    ]


def make_world_qa(world: FlowerCaseWorld) -> list[QAItem]:
    borrower = BORROWERS[world.params.borrower]
    trail_case = TRAIL_CASES[world.params.trail_case]
    return [
        QAItem(
            question="Why is a note card important in this story?",
            answer=(
                "A note card makes borrowing visible, so help does not look like stealing. "
                "That matters on the forest trail because the flower may travel for a kind reason, but the garden still needs a fair record."
            ),
        ),
        QAItem(
            question="What makes this mystery feel gentle instead of scary?",
            answer=(
                "The clues are small, ordinary things like threads, chalk, or wax, so the case stays child-sized. "
                "The answer also comes from kindness and sharing, which keeps the whodunit curious instead of harsh."
            ),
        ),
        QAItem(
            question="How does the misty flower help in this story?",
            answer=(
                f"In this version, the misty flower helps with {trail_case.need_label}. "
                f"{borrower.name} uses its beauty and calm presence to soften trouble on the trail before the children bring it home again."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = make_world(params)
    open_case(world)
    read_garden_clue(world)
    follow_trail(world)
    reveal_borrowing(world)
    build_sharing_fix(world)
    story = render_story(world)
    return StorySample(
        params=params,
        story=story,
        prompts=make_prompts(world),
        story_qa=make_story_qa(world),
        world_qa=make_world_qa(world),
        world=world,
    )


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("setting", "forest_trail"),
        asp.fact("seed_word", "cozy_garden"),
        asp.fact("seed_word", "misty_flower"),
        asp.fact("feature", "sharing"),
        asp.fact("feature", "happy_ending"),
        asp.fact("style", "whodunit"),
    ]
    for sleuth in SLEUTHS:
        lines.append(asp.fact("sleuth", sleuth))
    for borrower, profile in BORROWERS.items():
        lines.append(asp.fact("borrower", borrower))
        lines.append(asp.fact("expects", borrower, profile.expected_case))
    for trail_case in TRAIL_CASES:
        lines.append(asp.fact("trail_case", trail_case))
    return "\n".join(lines) + "\n"


ASP_RULES = r"""
compatible(B,C) :- expects(B,C).
invalid(S,B,C) :- sleuth(S), borrower(B), trail_case(C), not compatible(B,C).
valid(S,B,C) :- sleuth(S), borrower(B), trail_case(C), not invalid(S,B,C).
#show valid/3.
"""


def solve_asp_valid() -> list[tuple[str, str, str]]:
    import asp

    model = asp.one_model(asp_facts() + ASP_RULES)
    return sorted(asp.atoms(model, "valid"))


def verify_asp_parity() -> str:
    py_valid = {(p.sleuth, p.borrower, p.trail_case) for p in all_params()}
    asp_valid = set(solve_asp_valid())
    if py_valid != asp_valid:
        missing = sorted(py_valid - asp_valid)
        extra = sorted(asp_valid - py_valid)
        raise StoryError(f"ASP mismatch; missing={missing[:5]} extra={extra[:5]}")
    return f"OK: Python and ASP agree on {len(py_valid)} valid cozy-garden whodunits."


def _has_two_sentences(text: str) -> bool:
    return text.count(".") >= 2


def verify_story_samples() -> str:
    for params in all_params():
        sample = generate(params)
        story_lower = sample.story.lower()
        if "cozy garden" not in story_lower:
            raise StoryError(f"story for {params} is missing 'cozy garden'")
        if "misty flower" not in story_lower:
            raise StoryError(f"story for {params} is missing 'misty flower'")
        if "forest trail" not in story_lower:
            raise StoryError(f"story for {params} is missing 'forest trail'")
        if sample.world is None or sample.world.facts.get("ending") != "happy_shared_return":
            raise StoryError(f"story for {params} did not reach the happy sharing ending")
        if sample.world is None or sample.world.entities["flower"].location != "cozy garden gate":
            raise StoryError(f"story for {params} did not return the flower to the garden gate")
        if sample.world is None or sample.world.entities["share_box"].meters["cards"] != 1:
            raise StoryError(f"story for {params} did not create the sharing box")
        if not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError(f"story for {params} did not populate all output sets")
        if any(not _has_two_sentences(item.answer) for item in sample.story_qa):
            raise StoryError(f"story QA for {params} regressed to short answers")
        if any(not _has_two_sentences(item.answer) for item in sample.world_qa):
            raise StoryError(f"world QA for {params} regressed to short answers")
        if "{" in sample.story or "}" in sample.story:
            raise StoryError(f"story for {params} leaked template braces")
        if "  " in sample.story:
            raise StoryError(f"story for {params} contains doubled spaces")
    return f"OK: Exercised {len(all_params())} generated stories with grounded QA and happy endings."


def verify() -> str:
    return "\n".join([verify_asp_parity(), verify_story_samples()])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sleuth", choices=sorted(SLEUTHS))
    parser.add_argument("--borrower", choices=sorted(BORROWERS))
    parser.add_argument("--case", dest="trail_case", choices=sorted(TRAIL_CASES))
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = all_params()
    if args.sleuth:
        combos = [p for p in combos if p.sleuth == args.sleuth]
    if args.borrower:
        combos = [p for p in combos if p.borrower == args.borrower]
    if args.trail_case:
        combos = [p for p in combos if p.trail_case == args.trail_case]
    if not combos:
        sleuth = args.sleuth or next(iter(SLEUTHS))
        borrower = args.borrower or next(iter(BORROWERS))
        trail_case = args.trail_case or next(iter(TRAIL_CASES))
        raise StoryError(explain_rejection(sleuth, borrower, trail_case))
    choice = rng.choice(combos)
    return StoryParams(
        sleuth=choice.sleuth,
        borrower=choice.borrower,
        trail_case=choice.trail_case,
        seed=args.seed,
    )


def dump_trace(world: FlowerCaseWorld) -> None:
    print("\nTRACE")
    print(f"world meters: {world.meters}")
    for event in world.history:
        print(f"- {event.id}: actor={event.actor} target={event.target} location={event.location}")
        print(f"  {event.text}")
    for entity in world.entities.values():
        print(f"* {entity.id} | {entity.kind} | {entity.name} | location={entity.location}")
        print(f"  meters={entity.meters}")
        print(f"  memes={entity.memes}")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        print("\nPROMPTS")
        for prompt in sample.prompts:
            print(f"- {prompt}")
        print("\nSTORY QA")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\nWORLD KNOWLEDGE QA")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
    if trace and sample.world is not None:
        dump_trace(sample.world)


def _filtered_all_params(args: argparse.Namespace) -> list[StoryParams]:
    combos = all_params()
    if args.sleuth:
        combos = [p for p in combos if p.sleuth == args.sleuth]
    if args.borrower:
        combos = [p for p in combos if p.borrower == args.borrower]
    if args.trail_case:
        combos = [p for p in combos if p.trail_case == args.trail_case]
    return combos


def _samples_from_args(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        combos = _filtered_all_params(args)
        if not combos:
            sleuth = args.sleuth or next(iter(SLEUTHS))
            borrower = args.borrower or next(iter(BORROWERS))
            trail_case = args.trail_case or next(iter(TRAIL_CASES))
            raise StoryError(explain_rejection(sleuth, borrower, trail_case))
        return [generate(StoryParams(p.sleuth, p.borrower, p.trail_case, args.seed)) for p in combos]
    base_seed = args.seed if args.seed is not None else random.randrange(1, 10_000_000)
    samples: list[StorySample] = []
    seen: set[str] = set()
    attempts = 0
    while len(samples) < args.n and attempts < max(20, args.n * 20):
        seed = base_seed + attempts
        rng = random.Random(seed)
        local_args = copy.copy(args)
        local_args.seed = seed
        params = resolve_params(local_args, rng)
        params.seed = seed
        sample = generate(params)
        if sample.story not in seen:
            samples.append(sample)
            seen.add(sample.story)
        attempts += 1
    if len(samples) < args.n:
        raise StoryError(f"Only generated {len(samples)} distinct stories after {attempts} attempts.")
    return samples


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.show_asp:
        print(asp_facts() + ASP_RULES)
        return 0
    if args.verify:
        try:
            print(verify())
        except StoryError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        return 0
    if args.asp:
        for combo in solve_asp_valid():
            print(combo)
        return 0
    try:
        samples = _samples_from_args(args)
    except StoryError as exc:
        parser.error(str(exc))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0
    for index, sample in enumerate(samples, 1):
        header = ""
        if len(samples) > 1:
            header = (
                "=== cozy_garden_misty_flower_forest_trail_sharing_4 "
                f"#{index} seed={sample.params.seed} ==="
            )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
