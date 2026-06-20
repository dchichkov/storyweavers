#!/usr/bin/env python3
"""
storyworlds/worlds/cozy_garden_misty_flower_forest_trail_sharing_6.py
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
Beside a forest trail sits a cozy garden with one misty flower resting in a
blue teacup near a borrowing bell. One cool morning, the teacup is empty. A
child sleuth treats the missing bloom as a tiny whodunit and follows a clue
instead of accusing the first child who comes to mind.

The clue leads down the trail to a friend who did borrow the flower, but only
to share its comfort. The flower is helping another child who is cold, lost, or
hurt on the path. The mystery turns when the sleuth sees that the missing flower
was not hidden at all. It was being used kindly.

The children return the flower together, make a fair borrowing rule, and end
with a happier garden than before. The ending image proves the change: the
misty flower is back in its cup, and the bell now hangs above a sign that
invites sharing after asking.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from results import QAItem, StoryError, StorySample


SOURCE_TALE = (
    "A cozy garden beside a forest trail keeps one misty flower in a blue teacup "
    "near a brass borrowing bell. When the flower vanishes, a child sleuth follows "
    "one careful clue and discovers a gentle truth: a friend borrowed the bloom to "
    "share comfort with another child in need. The flower comes home, a fair rule is "
    "made, and the garden ends kinder than it began."
)


@dataclass(frozen=True)
class SleuthProfile:
    id: str
    name: str
    noticing_style: str
    tool: str
    hunch_line: str


@dataclass(frozen=True)
class BorrowerProfile:
    id: str
    name: str
    trail_spot: str
    clue_text: str
    clue_item: str
    aid_item: str
    share_action: str
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
    recovery_meter: str


@dataclass(frozen=True)
class StoryParams:
    sleuth: str
    borrower: str
    recipient: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    location: str
    meters: dict[str, int] = field(default_factory=dict)
    memes: dict[str, int] = field(default_factory=dict)


@dataclass
class Event:
    id: str
    text: str
    actor: str
    target: Optional[str] = None
    location: Optional[str] = None
    effects: dict[str, int] = field(default_factory=dict)


@dataclass
class GardenWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    meters: dict[str, int] = field(
        default_factory=lambda: {
            "mystery": 0,
            "evidence": 0,
            "trust": 0,
            "sharing": 0,
            "comfort": 0,
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
        target: Optional[str] = None,
        location: Optional[str] = None,
        **effects: int,
    ) -> None:
        self.history.append(
            Event(
                id=event_id,
                text=text,
                actor=actor,
                target=target,
                location=location,
                effects=dict(effects),
            )
        )
        for key, value in effects.items():
            self.meters[key] = self.meters.get(key, 0) + value


SLEUTHS: dict[str, SleuthProfile] = {
    "wren": SleuthProfile(
        id="wren",
        name="Wren",
        noticing_style="always noticed when one petal, spoon, or pebble sat out of place",
        tool="a tiny green notebook",
        hunch_line="Wren's best detective rule was that a clue could be kinder than a guess.",
    ),
    "jory": SleuthProfile(
        id="jory",
        name="Jory",
        noticing_style="could wait so quietly that even a shy clue seemed ready to speak",
        tool="a brass-rimmed magnifier",
        hunch_line="Jory liked mysteries best when patience solved them before blame had a chance to grow.",
    ),
    "tali": SleuthProfile(
        id="tali",
        name="Tali",
        noticing_style="counted steps, petals, and footprints so carefully that missing things stood out at once",
        tool="a satchel of colored chalk",
        hunch_line="Tali believed every fair whodunit needed clear tracks and a gentle heart.",
    ),
}


BORROWERS: dict[str, BorrowerProfile] = {
    "orla": BorrowerProfile(
        id="orla",
        name="Orla",
        trail_spot="fern bend",
        clue_text="a mint-green ribbon looped over the borrowing bell",
        clue_item="mint-green ribbon",
        aid_item="tea_flask",
        share_action="rested the teacup beside a steaming tea flask so the bloom could share its warm, sweet smell",
        purpose_text="Orla had borrowed the flower to warm a chilly friend at fern bend",
    ),
    "moss": BorrowerProfile(
        id="moss",
        name="Moss",
        trail_spot="pebble fork",
        clue_text="a dusting of yellow chalk on the garden gate latch",
        clue_item="yellow chalk dust",
        aid_item="trail_chalk",
        share_action="set the teacup on a stump beside a bright arrow of chalk so the pale bloom could calm the path choice",
        purpose_text="Moss had borrowed the flower to guide a lost friend at pebble fork",
    ),
    "fen": BorrowerProfile(
        id="fen",
        name="Fen",
        trail_spot="cedar bridge",
        clue_text="a folded clean bandage tucked under the flower shelf",
        clue_item="clean bandage",
        aid_item="bandage_tin",
        share_action="placed the teacup beside a bandage tin so the soft mist could settle an aching, scraped knee",
        purpose_text="Fen had borrowed the flower to comfort an injured friend at cedar bridge",
    ),
}


RECIPIENTS: dict[str, RecipientProfile] = {
    "briar": RecipientProfile(
        id="briar",
        name="Briar",
        trail_spot="fern bend",
        problem_text="sat on a mossy log shivering into both sleeves",
        need_label="warmth",
        required_item="tea_flask",
        relief_text="By then Briar was holding a warm cup with steady hands and smiling into the steam.",
        recovery_meter="warmth",
    ),
    "niko": RecipientProfile(
        id="niko",
        name="Niko",
        trail_spot="pebble fork",
        problem_text="stood at the split in the trail with wet eyes and no idea which path led back home",
        need_label="direction",
        required_item="trail_chalk",
        relief_text="By then Niko was walking with a calm breath behind a clear arrow that pointed home.",
        recovery_meter="confidence",
    ),
    "tess": RecipientProfile(
        id="tess",
        name="Tess",
        trail_spot="cedar bridge",
        problem_text="sat by the rail with a scraped knee and a brave little frown",
        need_label="comfort",
        required_item="bandage_tin",
        relief_text="By then Tess had a neat bandage, a dry face, and enough courage to grin at the creek below.",
        recovery_meter="steadiness",
    ),
}


def all_params() -> list[StoryParams]:
    rows: list[StoryParams] = []
    for sleuth_id in sorted(SLEUTHS):
        for borrower_id in sorted(BORROWERS):
            for recipient_id in sorted(RECIPIENTS):
                params = StoryParams(sleuth=sleuth_id, borrower=borrower_id, recipient=recipient_id)
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
            f"{borrower.name} heads toward {borrower.trail_spot}, not {recipient.trail_spot}, so the clue would point to the wrong child.",
        )
    if borrower.aid_item != recipient.required_item:
        return (
            False,
            f"{borrower.name} carries {borrower.aid_item}, but {recipient.name} needs {recipient.required_item} for that trail problem.",
        )
    return True, ""


def make_world(params: StoryParams) -> GardenWorld:
    sleuth = SLEUTHS[params.sleuth]
    borrower = BORROWERS[params.borrower]
    recipient = RECIPIENTS[params.recipient]
    world = GardenWorld(params=params)
    world.add_entity(
        Entity(
            id="sleuth",
            label=sleuth.name,
            kind="child sleuth",
            location="cozy garden",
            meters={"steps": 0, "clues": 0},
            memes={"curiosity": 3, "worry": 0, "fairness": 2},
        )
    )
    world.add_entity(
        Entity(
            id="borrower",
            label=borrower.name,
            kind="helper child",
            location=borrower.trail_spot,
            meters={"asked_first": 0, "carrying_flower": 1},
            memes={"generosity": 3, "guilt": 1},
        )
    )
    world.add_entity(
        Entity(
            id="recipient",
            label=recipient.name,
            kind="trail child",
            location=recipient.trail_spot,
            meters={recipient.recovery_meter: 0},
            memes={"worry": 2, "relief": 0},
        )
    )
    world.add_entity(
        Entity(
            id="flower",
            label="the misty flower",
            kind="flower",
            location=borrower.trail_spot,
            meters={"mist": 3, "borrowed": 1, "returned": 0, "petals": 6},
            memes={"comfort": 3, "beauty": 2},
        )
    )
    world.add_entity(
        Entity(
            id="garden",
            label="the cozy garden",
            kind="garden",
            location="forest trail edge",
            meters={"bell": 1, "share_sign": 0},
            memes={"welcome": 3},
        )
    )
    world.add_entity(
        Entity(
            id="teacup",
            label="the blue teacup",
            kind="teacup",
            location="cozy garden",
            meters={"occupied": 0, "soil_damp": 1},
            memes={},
        )
    )
    world.facts["source_tale"] = SOURCE_TALE
    world.facts["setting"] = "forest trail"
    world.facts["opening_image"] = (
        "At the edge of the forest trail, a cozy garden held one misty flower in a blue teacup beside a brass borrowing bell."
    )
    world.facts["mystery_question"] = (
        "Who had borrowed the misty flower, and why had they carried it away from the garden?"
    )
    world.facts["clue_text"] = borrower.clue_text
    world.facts["share_rule"] = "Please ring the bell, ask first, share kindly, and bring the flower home before dusk."
    world.facts["ending_state"] = "mystery_open"
    return world


def discover_missing_flower(world: GardenWorld) -> None:
    sleuth = SLEUTHS[world.params.sleuth]
    sleuth_ent = world.entities["sleuth"]
    sleuth_ent.memes["worry"] += 2
    world.record(
        "missing_flower",
        (
            f"On cool morning rounds, {sleuth.name} reached the blue teacup and found only damp soil and a silver curl of petal mist on the rim. "
            f"Because {sleuth.name} {sleuth.noticing_style}, the empty place felt less like a prank and more like a true little whodunit."
        ),
        actor="sleuth",
        target="flower",
        location="cozy garden",
        mystery=3,
        trust=-1,
    )


def inspect_borrowing_bell(world: GardenWorld) -> None:
    sleuth = SLEUTHS[world.params.sleuth]
    borrower = BORROWERS[world.params.borrower]
    sleuth_ent = world.entities["sleuth"]
    sleuth_ent.meters["clues"] += 1
    sleuth_ent.memes["curiosity"] += 1
    world.record(
        "bell_clue",
        (
            f"Beside the bell, {sleuth.name} spotted {borrower.clue_text}. "
            f"It looked exactly like something {borrower.name} would carry, yet {sleuth.name} kept the clue gentler than a rumor and chose to follow it first."
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
    sleuth_ent.meters["steps"] += 12
    world.record(
        "follow_trail",
        (
            f"With {sleuth.tool} tucked close, {sleuth.name} followed the forest trail to {recipient.trail_spot}. "
            f"There, {recipient.name} {recipient.problem_text}."
        ),
        actor="sleuth",
        target="recipient",
        location=recipient.trail_spot,
        evidence=1,
    )


def reveal_kind_sharing(world: GardenWorld) -> None:
    borrower = BORROWERS[world.params.borrower]
    recipient = RECIPIENTS[world.params.recipient]
    borrower_ent = world.entities["borrower"]
    recipient_ent = world.entities["recipient"]
    flower = world.entities["flower"]
    borrower_ent.memes["guilt"] += 1
    recipient_ent.memes["worry"] = 0
    recipient_ent.memes["relief"] += 3
    recipient_ent.meters[recipient.recovery_meter] += 3
    flower.memes["comfort"] += 1
    world.record(
        "kind_reveal",
        (
            f"Behind a ferny stump, {borrower.name} had {borrower.share_action}. "
            f"{borrower.name} confessed at once and explained the answer to the case: {borrower.purpose_text}, because {recipient.name} {recipient.problem_text}."
        ),
        actor="borrower",
        target="recipient",
        location=recipient.trail_spot,
        mystery=-3,
        comfort=3,
        trust=2,
        sharing=2,
    )


def return_flower_and_make_rule(world: GardenWorld) -> None:
    sleuth = SLEUTHS[world.params.sleuth]
    borrower = BORROWERS[world.params.borrower]
    sleuth_ent = world.entities["sleuth"]
    borrower_ent = world.entities["borrower"]
    flower = world.entities["flower"]
    garden = world.entities["garden"]
    teacup = world.entities["teacup"]
    sleuth_ent.location = "cozy garden"
    borrower_ent.location = "cozy garden"
    flower.location = "cozy garden"
    flower.meters["borrowed"] = 0
    flower.meters["returned"] = 1
    borrower_ent.meters["asked_first"] = 1
    sleuth_ent.memes["worry"] = 0
    garden.meters["share_sign"] = 1
    teacup.meters["occupied"] = 1
    world.facts["ending_state"] = "shared_happy"
    world.record(
        "return_and_rule",
        (
            f"{sleuth.name} did not scold. Instead, {sleuth.name} and {borrower.name} carried the misty flower back together, rang the brass bell once, and promised that kindness would still ask before borrowing."
        ),
        actor="sleuth",
        target="flower",
        location="cozy garden",
        trust=2,
        sharing=2,
        comfort=1,
    )


def render_story(world: GardenWorld) -> str:
    sleuth = SLEUTHS[world.params.sleuth]
    recipient = RECIPIENTS[world.params.recipient]
    final_image = (
        "By dusk, the misty flower was glowing again in its blue teacup at the cozy garden gate, "
        "and the brass bell hung above a painted sign that read, "
        f"\"{world.facts['share_rule']}\" {recipient.relief_text}"
    )
    world.facts["final_image"] = final_image
    return "\n\n".join(
        [
            (
                f"{world.facts['opening_image']} "
                f"{world.history[0].text} {world.facts['mystery_question']}"
            ),
            (
                f"{world.history[1].text} {world.history[2].text} "
                f"{sleuth.hunch_line}"
            ),
            (
                f"{world.history[3].text} {world.history[4].text} {final_image}"
            ),
        ]
    )


def make_prompts(world: GardenWorld) -> list[str]:
    sleuth = SLEUTHS[world.params.sleuth]
    borrower = BORROWERS[world.params.borrower]
    recipient = RECIPIENTS[world.params.recipient]
    return [
        "Write a child-friendly whodunit set on a forest trail.",
        "Include the exact phrases cozy garden and misty flower, and make the mystery turn toward sharing instead of blame.",
        f"Let {sleuth.name} follow {borrower.clue_item} until the case reveals {borrower.name} helping {recipient.name} with {recipient.need_label}.",
    ]


def make_story_qa(world: GardenWorld) -> list[QAItem]:
    sleuth = SLEUTHS[world.params.sleuth]
    borrower = BORROWERS[world.params.borrower]
    recipient = RECIPIENTS[world.params.recipient]
    return [
        QAItem(
            question="What mystery started the story?",
            answer=(
                "The mystery started when the blue teacup in the cozy garden was empty and the misty flower was gone. "
                f"{sleuth.name} saw enough careful signs to believe someone had borrowed it on purpose, so the real question became who took it and why."
            ),
        ),
        QAItem(
            question=f"How did {sleuth.name} solve the whodunit?",
            answer=(
                f"{sleuth.name} solved it by noticing {world.facts['clue_text']} and following that clue along the forest trail to {recipient.trail_spot}. "
                f"The answer came from evidence instead of suspicion because the clue matched something {borrower.name} carried."
            ),
        ),
        QAItem(
            question=f"Why had {borrower.name} borrowed the flower?",
            answer=(
                f"{borrower.name} borrowed the flower to help {recipient.name} with {recipient.need_label}. "
                "The flower was being shared as comfort, so what looked like a theft turned out to be a kind plan."
            ),
        ),
        QAItem(
            question="Why is the ending happy?",
            answer=(
                "The ending is happy because the children learn the flower was missing for a caring reason, not a selfish one. "
                "They return it together, make a fair borrowing rule, and leave the garden more welcoming than it was that morning."
            ),
        ),
    ]


def make_world_qa(world: GardenWorld) -> list[QAItem]:
    borrower = BORROWERS[world.params.borrower]
    recipient = RECIPIENTS[world.params.recipient]
    return [
        QAItem(
            question="Why does this world work well as a gentle whodunit?",
            answer=(
                "It works as a gentle whodunit because something important disappears, clues point to a real answer, and nobody needs to be treated as a villain. "
                "The suspense comes from not knowing the reason for the borrowing until the trail evidence leads to it."
            ),
        ),
        QAItem(
            question="Why is sharing tied to asking first in this world?",
            answer=(
                "Sharing matters here because the misty flower can help more than one child, but the garden still belongs to everyone who cares for it. "
                "Asking first protects trust, so kindness does not create a second problem while solving the first."
            ),
        ),
        QAItem(
            question=f"How did the flower help with {recipient.need_label}?",
            answer=(
                f"It helped because {borrower.aid_item.replace('_', ' ')} handled the practical need while the flower softened the fear around {recipient.name}. "
                "The world treats comfort as part of real help, so beauty and care can steady a child enough for the rest of the aid to work."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    ok, reason = is_reasonable(params)
    if not ok:
        raise StoryError(reason)
    world = make_world(params)
    discover_missing_flower(world)
    inspect_borrowing_bell(world)
    follow_the_trail(world)
    reveal_kind_sharing(world)
    return_flower_and_make_rule(world)
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
    for sleuth_id in sorted(SLEUTHS):
        lines.append(asp.fact("sleuth", sleuth_id))
    for borrower_id, borrower in sorted(BORROWERS.items()):
        lines.append(asp.fact("borrower", borrower_id))
        lines.append(asp.fact("borrower_spot", borrower_id, borrower.trail_spot.replace(" ", "_")))
        lines.append(asp.fact("borrower_item", borrower_id, borrower.aid_item))
    for recipient_id, recipient in sorted(RECIPIENTS.items()):
        lines.append(asp.fact("recipient", recipient_id))
        lines.append(asp.fact("recipient_spot", recipient_id, recipient.trail_spot.replace(" ", "_")))
        lines.append(asp.fact("recipient_item", recipient_id, recipient.required_item))
    return "\n".join(lines) + "\n"


ASP_RULES = r"""
compatible(B,R) :-
    borrower_spot(B,S),
    recipient_spot(R,S),
    borrower_item(B,I),
    recipient_item(R,I).

invalid(S,B,R) :- sleuth(S), borrower(B), recipient(R), not compatible(B,R).
valid(S,B,R) :- sleuth(S), borrower(B), recipient(R), not invalid(S,B,R).

#show valid/3.
"""


def show_asp_program() -> str:
    return f"{asp_facts()}{ASP_RULES}"


def asp_valid_rows() -> list[tuple[str, str, str]]:
    import asp

    model = asp.one_model(show_asp_program())
    return sorted(tuple(str(part) for part in atom) for atom in asp.atoms(model, "valid"))


def verify_asp_parity() -> str:
    asp_valid = set(asp_valid_rows())
    py_valid = {(p.sleuth, p.borrower, p.recipient) for p in all_params()}
    if asp_valid != py_valid:
        missing = sorted(py_valid - asp_valid)
        extra = sorted(asp_valid - py_valid)
        raise StoryError(f"ASP mismatch; missing={missing[:5]} extra={extra[:5]}")
    return f"OK: Python and ASP agree on {len(py_valid)} valid forest-trail sharing mysteries."


def verify_story_samples() -> str:
    params_list = all_params()
    for params in params_list:
        sample = generate(params)
        if sample.world is None:
            raise StoryError(f"story for {params} did not retain its world model")
        story_lower = sample.story.lower()
        if "cozy garden" not in story_lower:
            raise StoryError(f"story for {params} is missing 'cozy garden'")
        if "misty flower" not in story_lower:
            raise StoryError(f"story for {params} is missing 'misty flower'")
        if "forest trail" not in story_lower:
            raise StoryError(f"story for {params} is missing 'forest trail'")
        if "whodunit" not in story_lower:
            raise StoryError(f"story for {params} is missing whodunit framing")
        if sample.world.facts.get("ending_state") != "shared_happy":
            raise StoryError(f"story for {params} did not reach the happy ending state")
        if len(sample.world.history) != 5:
            raise StoryError(f"story for {params} did not record the full world trace")
        if sample.world.entities["flower"].location != "cozy garden":
            raise StoryError(f"story for {params} failed to return the flower")
        if sample.world.entities["garden"].meters.get("share_sign") != 1:
            raise StoryError(f"story for {params} failed to create the sharing rule sign")
        if sample.world.meters["sharing"] < 4 or sample.world.meters["trust"] < 3:
            raise StoryError(f"story for {params} did not resolve through enough sharing/trust state")
        if len(sample.prompts) < 3 or len(sample.story_qa) < 3 or len(sample.world_qa) < 3:
            raise StoryError(f"story for {params} did not populate all output sets")
        if "{" in sample.story or "}" in sample.story:
            raise StoryError(f"story for {params} leaked template braces")
        if "  " in sample.story:
            raise StoryError(f"story for {params} contains doubled spaces")
        if "ask first" not in story_lower:
            raise StoryError(f"story for {params} is missing the final borrowing rule image")
    return f"OK: Exercised {len(params_list)} generated stories with grounded QA and state-driven happy endings."


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
            sleuth=args.sleuth or next(iter(sorted(SLEUTHS))),
            borrower=args.borrower,
            recipient=args.recipient,
            seed=args.seed,
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
            seed=args.seed,
        )
        raise StoryError(f"no valid story matches {requested}")
    choice = rng.choice(matches)
    return StoryParams(
        sleuth=choice.sleuth,
        borrower=choice.borrower,
        recipient=choice.recipient,
        seed=args.seed,
    )


def iter_samples(args: argparse.Namespace) -> Iterable[StorySample]:
    if args.all:
        for params in matching_params(args):
            yield generate(StoryParams(params.sleuth, params.borrower, params.recipient, args.seed))
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
        lines.append(f"- {event.id}{where}: {event.text} {event.effects}")
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
        samples = list(iter_samples(args))
        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0
        for index, sample in enumerate(samples):
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
