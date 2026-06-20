#!/usr/bin/env python3
"""
storyworlds/worlds/cozy_garden_misty_flower_forest_trail_sharing_5.py
=====================================================================

Seed prompt
-----------
Write a story that includes the following words and narrative instruments.
Words: cozy garden, misty flower
Setting: forest trail
Features: Sharing, Happy Ending
Style: Whodunit

Source tale written from the seed
---------------------------------
At the edge of a forest trail, a cozy garden keeps one misty flower in a blue
teacup beside a little brass borrowing bell. On lantern-walk morning, the cup
is empty. A careful child sleuth treats the missing bloom like a tiny whodunit
and follows the first clue instead of blaming anyone.

The clue leads down the trail to a friend who borrowed the flower without
asking. The friend did not take it to keep. The flower was carried to help a
worried child on the path feel warm, guided, or soothed. The mystery turns when
the sleuth sees that the missing flower has been sharing its comfort.

The children return the flower together, make a fair borrowing rule, and end
the day with the garden kinder than it began. The ending image proves the
change: the misty flower is back in its cup, and the brass bell now hangs over
a sign that says anyone may borrow kindly after asking.
"""

from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from results import QAItem, StoryError, StorySample


SOURCE_TALE = (
    "At the edge of a forest trail, a cozy garden keeps one misty flower in a blue "
    "teacup beside a brass borrowing bell. On lantern-walk morning the cup is empty, "
    "so a calm child sleuth follows a clue instead of accusing anyone. The clue leads "
    "to a friend who borrowed the flower to help another child on the trail, and the "
    "mystery ends with a happy sharing rule, the flower safely returned, and the "
    "garden made kinder than before."
)


@dataclass(frozen=True)
class SleuthProfile:
    id: str
    name: str
    noticing_style: str
    tool: str


@dataclass(frozen=True)
class BorrowerProfile:
    id: str
    name: str
    trail_spot: str
    clue_text: str
    clue_item: str
    aid_item: str
    action_text: str
    purpose_text: str


@dataclass(frozen=True)
class RecipientProfile:
    id: str
    name: str
    trail_spot: str
    problem_text: str
    need_label: str
    required_item: str
    relief_text: str
    changed_meter: str


@dataclass(frozen=True)
class StoryParams:
    sleuth: str
    borrower: str
    recipient: str


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
    world_delta: dict[str, int] = field(default_factory=dict)


@dataclass
class GardenWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    meters: dict[str, int] = field(
        default_factory=lambda: {
            "mystery": 0,
            "evidence": 0,
            "care": 0,
            "trust": 0,
            "sharing": 0,
        }
    )
    facts: dict[str, str | int | bool] = field(default_factory=dict)

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
        **world_delta: int,
    ) -> None:
        self.history.append(
            Event(
                id=event_id,
                text=text,
                actor=actor,
                target=target,
                location=location,
                world_delta=dict(world_delta),
            )
        )
        for key, value in world_delta.items():
            self.meters[key] = self.meters.get(key, 0) + value


SLEUTHS: dict[str, SleuthProfile] = {
    "wren": SleuthProfile(
        id="wren",
        name="Wren",
        noticing_style="noticed when one small thing in a room sat one inch away from where it belonged",
        tool="a pine-green notebook with a ribbon bookmark",
    ),
    "jory": SleuthProfile(
        id="jory",
        name="Jory",
        noticing_style="liked to stand quietly until even a shy clue seemed ready to speak",
        tool="a round tin magnifier",
    ),
    "tali": SleuthProfile(
        id="tali",
        name="Tali",
        noticing_style="counted steps, petals, and pebbles so carefully that missing things stood out at once",
        tool="a satchel of colored chalk",
    ),
}


BORROWERS: dict[str, BorrowerProfile] = {
    "orla": BorrowerProfile(
        id="orla",
        name="Orla",
        trail_spot="fern bend",
        clue_text="a mint-scented ribbon looped on the borrowing bell",
        clue_item="mint ribbon",
        aid_item="tea_flask",
        action_text="rested the teacup beside a steaming tea flask so the petals could share a soft, warm smell",
        purpose_text="Orla had borrowed the flower to warm a chilly child at fern bend",
    ),
    "moss": BorrowerProfile(
        id="moss",
        name="Moss",
        trail_spot="pebble fork",
        clue_text="a pinch of yellow chalk dust on the garden gate latch",
        clue_item="yellow chalk dust",
        aid_item="trail_chalk",
        action_text="set the teacup on a stump beside a chalk arrow so the pale bloom could make the right path easy to see",
        purpose_text="Moss had borrowed the flower to guide a lost child at pebble fork",
    ),
    "fen": BorrowerProfile(
        id="fen",
        name="Fen",
        trail_spot="cedar bridge",
        clue_text="a folded clean bandage tucked under the flower shelf",
        clue_item="clean bandage",
        aid_item="bandage_tin",
        action_text="placed the teacup beside a bandage tin so the flower's gentle smell could calm a stinging knee",
        purpose_text="Fen had borrowed the flower to soothe an injured child at cedar bridge",
    ),
}


RECIPIENTS: dict[str, RecipientProfile] = {
    "briar": RecipientProfile(
        id="briar",
        name="Briar",
        trail_spot="fern bend",
        problem_text="sat on a mossy bench and shivered into both sleeves",
        need_label="warmth",
        required_item="tea_flask",
        relief_text="By then Briar had stopped shivering and was warming both hands around a sweet cup of tea.",
        changed_meter="comfort",
    ),
    "niko": RecipientProfile(
        id="niko",
        name="Niko",
        trail_spot="pebble fork",
        problem_text="stood at the split in the trail with damp eyes and no idea which path led home",
        need_label="direction",
        required_item="trail_chalk",
        relief_text="By then Niko was walking with a steady breath, following the bright arrow that pointed home.",
        changed_meter="confidence",
    ),
    "tess": RecipientProfile(
        id="tess",
        name="Tess",
        trail_spot="cedar bridge",
        problem_text="sat by the bridge rail with a scraped knee and a brave little frown",
        need_label="comfort",
        required_item="bandage_tin",
        relief_text="By then Tess had a neat bandage, a dry face, and enough courage to smile at the rushing creek.",
        changed_meter="steadiness",
    ),
}


def is_reasonable(params: StoryParams) -> tuple[bool, str]:
    if params.sleuth not in SLEUTHS:
        return False, f"unknown sleuth: {params.sleuth}"
    if params.borrower not in BORROWERS:
        return False, f"unknown borrower: {params.borrower}"
    if params.recipient not in RECIPIENTS:
        return False, f"unknown recipient: {params.recipient}"
    borrower = BORROWERS[params.borrower]
    recipient = RECIPIENTS[params.recipient]
    if borrower.trail_spot != recipient.trail_spot:
        return (
            False,
            f"{borrower.name} heads to {borrower.trail_spot}, not {recipient.trail_spot}, so the clue would point to the wrong place.",
        )
    if borrower.aid_item != recipient.required_item:
        return (
            False,
            f"{borrower.name} carries {borrower.aid_item}, but {recipient.name} needs {recipient.required_item} for this trail problem.",
        )
    return True, ""


def all_params() -> list[StoryParams]:
    rows: list[StoryParams] = []
    for sleuth in SLEUTHS:
        for borrower in BORROWERS:
            for recipient in RECIPIENTS:
                params = StoryParams(sleuth=sleuth, borrower=borrower, recipient=recipient)
                if is_reasonable(params)[0]:
                    rows.append(params)
    return rows


def matching_params(args: argparse.Namespace) -> list[StoryParams]:
    rows: list[StoryParams] = []
    for params in all_params():
        if args.sleuth and params.sleuth != args.sleuth:
            continue
        if args.borrower and params.borrower != args.borrower:
            continue
        if args.recipient and params.recipient != args.recipient:
            continue
        rows.append(params)
    return rows


def make_world(params: StoryParams) -> GardenWorld:
    sleuth = SLEUTHS[params.sleuth]
    borrower = BORROWERS[params.borrower]
    recipient = RECIPIENTS[params.recipient]
    world = GardenWorld(params=params)
    world.add_entity(
        Entity(
            id="sleuth",
            name=sleuth.name,
            kind="child sleuth",
            location="cozy garden",
            meters={"steps_taken": 0, "clues_found": 0},
            memes={"Curiosity": 3, "Calm": 2, "Worry": 0},
        )
    )
    world.add_entity(
        Entity(
            id="borrower",
            name=borrower.name,
            kind="helper child",
            location=borrower.trail_spot,
            meters={"asked_first": 0, "flower_carried": 1},
            memes={"Generosity": 3, "Guilt": 1},
        )
    )
    world.add_entity(
        Entity(
            id="recipient",
            name=recipient.name,
            kind="trail child",
            location=recipient.trail_spot,
            meters={recipient.changed_meter: 0},
            memes={"Worry": 2, "Relief": 0},
        )
    )
    world.add_entity(
        Entity(
            id="flower",
            name="the misty flower",
            kind="flower",
            location=borrower.trail_spot,
            meters={"mist": 3, "borrowed": 1, "returned": 0},
            memes={"Comfort": 3, "Beauty": 2},
        )
    )
    world.add_entity(
        Entity(
            id="garden",
            name="the cozy garden",
            kind="garden",
            location="forest trail edge",
            meters={"borrow_bell": 1, "share_sign": 0},
            memes={"Welcome": 3},
        )
    )
    world.facts["source_tale"] = SOURCE_TALE
    world.facts["setting"] = "forest trail"
    world.facts["borrow_rule"] = "Borrow kindly, ring the bell, and bring the flower back before dusk."
    world.facts["opening_image"] = (
        "At the edge of the forest trail, a cozy garden held one misty flower in a blue teacup beside a brass bell."
    )
    world.facts["mystery_question"] = (
        f"Who had borrowed the misty flower from the cozy garden, and why had they taken it down the trail?"
    )
    world.facts["clue_text"] = borrower.clue_text
    world.facts["trail_spot"] = recipient.trail_spot
    world.facts["purpose_text"] = borrower.purpose_text
    return world


def discover_empty_cup(world: GardenWorld) -> None:
    sleuth = SLEUTHS[world.params.sleuth]
    flower = world.entities["flower"]
    flower.meters["borrowed"] = 1
    world.entities["sleuth"].memes["Worry"] += 2
    world.record(
        "empty_cup",
        (
            f"On lantern-walk morning, {sleuth.name} reached for the blue teacup and found only damp soil and one silver petal mist on the rim. "
            f"Because {sleuth.name} {sleuth.noticing_style}, the empty cup felt like a real little whodunit."
        ),
        actor="sleuth",
        target="flower",
        location="cozy garden",
        mystery=3,
        trust=-1,
    )


def inspect_the_bell(world: GardenWorld) -> None:
    sleuth = SLEUTHS[world.params.sleuth]
    borrower = BORROWERS[world.params.borrower]
    sleuth_ent = world.entities["sleuth"]
    sleuth_ent.meters["clues_found"] += 1
    sleuth_ent.memes["Curiosity"] += 1
    world.record(
        "clue",
        (
            f"{sleuth.name} knelt beside the borrowing bell and spotted {borrower.clue_text}. "
            f"The clue matched something {borrower.name} often carried, so {sleuth.name} chose to follow the evidence before guessing."
        ),
        actor="sleuth",
        target="borrower",
        location="cozy garden",
        evidence=2,
    )


def follow_the_trail(world: GardenWorld) -> None:
    sleuth = SLEUTHS[world.params.sleuth]
    recipient = RECIPIENTS[world.params.recipient]
    sleuth_ent = world.entities["sleuth"]
    sleuth_ent.location = recipient.trail_spot
    sleuth_ent.meters["steps_taken"] += 12
    world.record(
        "trail_search",
        (
            f"With {sleuth.tool} tucked under one arm, {sleuth.name} followed the forest trail to {recipient.trail_spot}. "
            f"There {recipient.name} {recipient.problem_text}."
        ),
        actor="sleuth",
        target="recipient",
        location=recipient.trail_spot,
        evidence=1,
    )


def reveal_the_kind_borrowing(world: GardenWorld) -> None:
    sleuth = SLEUTHS[world.params.sleuth]
    borrower = BORROWERS[world.params.borrower]
    recipient = RECIPIENTS[world.params.recipient]
    borrower_ent = world.entities["borrower"]
    recipient_ent = world.entities["recipient"]
    flower = world.entities["flower"]
    borrower_ent.memes["Guilt"] += 1
    recipient_ent.memes["Relief"] += 3
    recipient_ent.memes["Worry"] = 0
    recipient_ent.meters[recipient.changed_meter] += 3
    flower.memes["Comfort"] += 1
    world.record(
        "reveal",
        (
            f"Behind a ferny stump, {sleuth.name} found {borrower.name}, who had {borrower.action_text}. "
            f"{borrower.name} admitted the borrowing at once and explained the truth: {borrower.purpose_text}, because {recipient.name} {recipient.problem_text}."
        ),
        actor="borrower",
        target="recipient",
        location=recipient.trail_spot,
        mystery=-3,
        care=3,
        trust=2,
        sharing=2,
    )


def return_the_flower(world: GardenWorld) -> None:
    sleuth = SLEUTHS[world.params.sleuth]
    borrower = BORROWERS[world.params.borrower]
    flower = world.entities["flower"]
    garden = world.entities["garden"]
    borrower_ent = world.entities["borrower"]
    sleuth_ent = world.entities["sleuth"]
    flower.location = "cozy garden"
    flower.meters["returned"] = 1
    flower.meters["borrowed"] = 0
    borrower_ent.meters["asked_first"] = 1
    sleuth_ent.memes["Worry"] = 0
    garden.meters["share_sign"] = 1
    world.record(
        "return",
        (
            f"{sleuth.name} did not scold. Instead, {sleuth.name} and {borrower.name} carried the misty flower back together, rang the brass bell once, and agreed that kindness still had to ask first."
        ),
        actor="sleuth",
        target="flower",
        location="cozy garden",
        care=1,
        trust=2,
        sharing=2,
    )
    world.facts["ending_state"] = "shared_happy"


def render_story(world: GardenWorld) -> str:
    recipient = RECIPIENTS[world.params.recipient]
    final_image = (
        "By dusk, the misty flower was glowing again in its blue teacup at the cozy garden gate, "
        "and the brass bell hung over a painted sign that read, "
        f"\"{world.facts['borrow_rule']}\" {recipient.relief_text}"
    )
    world.facts["final_image"] = final_image
    return "\n\n".join(
        [
            (
                f"{world.facts['opening_image']} "
                f"{world.history[0].text} {world.facts['mystery_question']}"
            ),
            " ".join(
                [
                    world.history[1].text,
                    world.history[2].text,
                    "The deeper Wren-style hunch in the moment was simple: a clue was kinder than a guess."
                    if world.params.sleuth == "wren"
                    else "The little mystery stayed gentle because the sleuth followed the clue instead of making a sharp accusation.",
                ]
            ),
            " ".join(
                [
                    world.history[3].text,
                    world.history[4].text,
                    final_image,
                ]
            ),
        ]
    )


def make_prompts(world: GardenWorld) -> list[str]:
    borrower = BORROWERS[world.params.borrower]
    recipient = RECIPIENTS[world.params.recipient]
    sleuth = SLEUTHS[world.params.sleuth]
    return [
        "Write a child-friendly whodunit set on a forest trail.",
        "Include the exact phrases cozy garden and misty flower, and let the mystery stay gentle.",
        f"Make {sleuth.name} solve the case by following {borrower.clue_item} until {borrower.name} is found helping {recipient.name} with {recipient.need_label}.",
    ]


def make_story_qa(world: GardenWorld) -> list[QAItem]:
    sleuth = SLEUTHS[world.params.sleuth]
    borrower = BORROWERS[world.params.borrower]
    recipient = RECIPIENTS[world.params.recipient]
    return [
        QAItem(
            question="What mystery began the story?",
            answer=(
                "The mystery began when the blue teacup in the cozy garden was empty and the misty flower was gone. "
                f"{sleuth.name} could tell the flower had been lifted gently, so the question became who had borrowed it and why."
            ),
        ),
        QAItem(
            question=f"How did {sleuth.name} solve the whodunit?",
            answer=(
                f"{sleuth.name} solved it by noticing {world.facts['clue_text']} and following that clue down the forest trail to {world.facts['trail_spot']}. "
                f"The answer came from evidence, not blame, because the clue matched something {borrower.name} carried."
            ),
        ),
        QAItem(
            question=f"Why had {borrower.name} taken the flower?",
            answer=(
                f"{borrower.name} had borrowed the flower to help {recipient.name} with {recipient.need_label}. "
                "The flower's soft beauty and the borrowed gear together made the trail feel safer and kinder."
            ),
        ),
        QAItem(
            question="Why is the ending happy?",
            answer=(
                "The ending is happy because the children learn the flower was shared for kindness, not hidden for selfishness. "
                "They bring it back together, make a fair borrowing rule, and leave the garden more welcoming than before."
            ),
        ),
    ]


def make_world_qa(world: GardenWorld) -> list[QAItem]:
    borrower = BORROWERS[world.params.borrower]
    recipient = RECIPIENTS[world.params.recipient]
    return [
        QAItem(
            question="What kind of place is this world set in?",
            answer=(
                "This world is set beside a forest trail where a cozy garden meets small traveling problems. "
                "That lets one special flower matter both as a beautiful object and as something children can share to help each other."
            ),
        ),
        QAItem(
            question="Why is following a clue better than making a quick accusation?",
            answer=(
                "Following a clue gives the truth a chance to appear. "
                "In this world, the mystery stays gentle because the sleuth looks for evidence and learns the borrowing was meant to help."
            ),
        ),
        QAItem(
            question=f"How did borrowing the flower help with {recipient.need_label}?",
            answer=(
                f"It helped because {borrower.aid_item.replace('_', ' ')} and the misty flower worked together at {recipient.trail_spot}. "
                f"The borrowed flower changed the mood around {recipient.name}, so the trail problem felt less frightening and more manageable."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    ok, reason = is_reasonable(params)
    if not ok:
        raise StoryError(reason)
    world = make_world(params)
    discover_empty_cup(world)
    inspect_the_bell(world)
    follow_the_trail(world)
    reveal_the_kind_borrowing(world)
    return_the_flower(world)
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
    for sleuth in sorted(SLEUTHS):
        lines.append(asp.fact("sleuth", sleuth))
    for borrower_id, borrower in sorted(BORROWERS.items()):
        lines.append(asp.fact("borrower", borrower_id))
        lines.append(asp.fact("borrower_spot", borrower_id, borrower.trail_spot.replace(" ", "_")))
        lines.append(asp.fact("borrower_item", borrower_id, borrower.aid_item))
    for recipient_id, recipient in sorted(RECIPIENTS.items()):
        lines.append(asp.fact("recipient", recipient_id))
        lines.append(asp.fact("recipient_spot", recipient_id, recipient.trail_spot.replace(" ", "_")))
        lines.append(asp.fact("recipient_item", recipient_id, recipient.required_item))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(B,R) :- borrower_spot(B,S), recipient_spot(R,S), borrower_item(B,I), recipient_item(R,I).
invalid(S,B,R) :- sleuth(S), borrower(B), recipient(R), not compatible(B,R).
valid(S,B,R) :- sleuth(S), borrower(B), recipient(R), not invalid(S,B,R).
#show valid/3.
"""


def show_asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}"


def asp_valid_rows() -> list[tuple[str, str, str]]:
    import asp

    models = asp.solve(show_asp_program())
    model = models[0] if models else []
    return sorted(tuple(str(part) for part in atom) for atom in asp.atoms(model, "valid"))


def verify_asp_parity() -> str:
    asp_valid = set(asp_valid_rows())
    py_valid = {(p.sleuth, p.borrower, p.recipient) for p in all_params()}
    if asp_valid != py_valid:
        missing = sorted(py_valid - asp_valid)
        extra = sorted(asp_valid - py_valid)
        raise StoryError(f"ASP mismatch; missing={missing[:5]} extra={extra[:5]}")
    return f"OK: Python and ASP agree on {len(py_valid)} valid sharing mysteries."


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
        if sample.world is None or sample.world.facts.get("ending_state") != "shared_happy":
            raise StoryError(f"story for {params} did not reach the happy sharing ending")
        if len(sample.story_qa) < 3 or len(sample.world_qa) < 3 or len(sample.prompts) < 3:
            raise StoryError(f"story for {params} did not populate all required output sets")
        if len(sample.world.history) != 5:
            raise StoryError(f"story for {params} did not record the full world trace")
        if "{" in sample.story or "}" in sample.story:
            raise StoryError(f"story for {params} leaked template braces")
        if "  " in sample.story:
            raise StoryError(f"story for {params} contains doubled spaces")
        if "borrow kindly" not in story_lower:
            raise StoryError(f"story for {params} is missing the ending rule image")
    return f"OK: Exercised {len(all_params())} generated stories with grounded QA and happy endings."


def verify() -> str:
    return "\n".join([verify_asp_parity(), verify_story_samples()])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sleuth", choices=sorted(SLEUTHS))
    parser.add_argument("--borrower", choices=sorted(BORROWERS))
    parser.add_argument("--recipient", choices=sorted(RECIPIENTS))
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


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None) -> StoryParams:
    rng = rng or random.Random(args.seed)
    if args.borrower and args.recipient:
        requested = StoryParams(
            sleuth=args.sleuth or next(iter(SLEUTHS)),
            borrower=args.borrower,
            recipient=args.recipient,
        )
        ok, reason = is_reasonable(requested)
        if not ok:
            raise StoryError(reason)
    matches = matching_params(args)
    if not matches:
        requested = StoryParams(
            sleuth=args.sleuth or "any",
            borrower=args.borrower or "any",
            recipient=args.recipient or "any",
        )
        raise StoryError(f"no valid story matches {requested}")
    return rng.choice(matches)


def iter_samples(args: argparse.Namespace) -> Iterable[StorySample]:
    if args.all:
        for params in matching_params(args):
            yield generate(params)
        return
    rng = random.Random(args.seed)
    for _ in range(max(1, args.n)):
        yield generate(resolve_params(args, rng))


def dump_trace(sample: StorySample) -> str:
    if sample.world is None:
        return ""
    world = sample.world
    lines = ["Trace:"]
    for event in world.history:
        where = f" @ {event.location}" if event.location else ""
        lines.append(f"- {event.id}{where}: {event.text} {event.world_delta}")
    lines.append("Entities:")
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"- {entity.id} ({entity.kind}) at {entity.location}: meters={meters} memes={memes}"
        )
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace:
        print()
        print(dump_trace(sample))
    if qa:
        print("\nPrompts:")
        for item in sample.prompts:
            print(f"- {item}")
        print("\nStory QA:")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\nWorld QA:")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(show_asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            rows = asp_valid_rows()
            print(f"{len(rows)} valid sharing mysteries:\n")
            for row in rows:
                print("  " + " ".join(f"{part:10}" for part in row))
            return 0
        for index, sample in enumerate(iter_samples(args)):
            if args.json:
                print(sample.to_json())
                continue
            header = ""
            if args.all or args.n > 1:
                header = f"== sample {index + 1} =="
            if index:
                print("\n---\n")
            emit(sample, trace=args.trace, qa=args.qa, header=header)
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
