#!/usr/bin/env python3
"""A tiny whodunit about a borrowed flower, a forest trail, and openhearted sharing."""

from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from results import QAItem, StoryError, StorySample


SOURCE_TALE = """
At the edge of a forest trail, a cozy garden keeps one misty flower in a clay cup.
On picnic morning the flower goes missing, and a careful child treats it like a
whodunit. The clues lead to a friend who borrowed the flower to help someone on
the trail. Instead of ending with blame, the mystery ends with a new sharing rule,
the flower safely returned, and the trail made kinder.
""".strip()


@dataclass(frozen=True)
class DetectiveProfile:
    id: str
    name: str
    noticing_style: str
    keepsake: str


@dataclass(frozen=True)
class SharerProfile:
    id: str
    name: str
    clue_text: str
    clue_object: str
    gear: str
    action_text: str
    purpose_text: str
    expected_recipient: str


@dataclass(frozen=True)
class RecipientProfile:
    id: str
    name: str
    trail_spot: str
    trouble_text: str
    relief_text: str
    need_label: str
    meter_key: str


@dataclass(frozen=True)
class StoryParams:
    detective: str
    sharer: str
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
    delta: dict[str, int] = field(default_factory=dict)


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


DETECTIVES: dict[str, DetectiveProfile] = {
    "hazel": DetectiveProfile(
        "hazel",
        "Hazel",
        "noticed the smallest changes before anyone else did",
        "a green satchel with a stubby pencil",
    ),
    "pip": DetectiveProfile(
        "pip",
        "Pip",
        "counted every stepping stone and never forgot the count",
        "a bright rain cape with deep pockets",
    ),
    "suri": DetectiveProfile(
        "suri",
        "Suri",
        "liked to listen to a place until it seemed ready to answer back",
        "an acorn-brown notebook",
    ),
}


SHARERS: dict[str, SharerProfile] = {
    "mina": SharerProfile(
        "mina",
        "Mina",
        "a blue thermos ring and a curl of mint steam on the garden shelf",
        "blue thermos ring",
        "a blue thermos",
        "set the clay cup beside a steaming thermos so the flower's gentle scent could warm the air",
        "Mina wanted the flower's softness to cheer a chilly friend",
        "cold",
    ),
    "theo": SharerProfile(
        "theo",
        "Theo",
        "a red ribbon fiber caught on the garden latch",
        "red ribbon fiber",
        "a folded trail map tied with red ribbon",
        "tied the clay cup beside the fork sign so the pale bloom glowed like an arrow",
        "Theo wanted the flower's glow to guide a lost walker",
        "lost",
    ),
    "lark": SharerProfile(
        "lark",
        "Lark",
        "three crushed berries and a clean bandage strip near the stepping stones",
        "bandage strip",
        "a berry tin filled with bandages",
        "placed the clay cup beside a bandage tin so the flower's soft smell could calm a shaking child",
        "Lark wanted the flower's calm to comfort an injured friend",
        "hurt",
    ),
}


RECIPIENTS: dict[str, RecipientProfile] = {
    "cold": RecipientProfile(
        "cold",
        "Pru",
        "fern bend",
        "was shivering on a mossy bench with both hands around an empty cup",
        "Soon Pru was smiling into a warm drink instead of shivering at the mist.",
        "warmth",
        "comfort",
    ),
    "lost": RecipientProfile(
        "lost",
        "Niko",
        "pebble fork",
        "stood with damp eyes at the split in the path and could not tell which way home was",
        "Soon Niko was following the marked path with a steadier breath and a sure face.",
        "direction",
        "confidence",
    ),
    "hurt": RecipientProfile(
        "hurt",
        "Tessa",
        "cedar bridge",
        "sat beside the bridge with a stinging knee and a tight little frown",
        "Soon Tessa let the bandage rest neatly and even laughed at the creek below.",
        "comfort",
        "steadiness",
    ),
}


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.detective not in DETECTIVES:
        return False, f"unknown detective: {params.detective}"
    if params.sharer not in SHARERS:
        return False, f"unknown sharer: {params.sharer}"
    if params.recipient not in RECIPIENTS:
        return False, f"unknown recipient: {params.recipient}"
    sharer = SHARERS[params.sharer]
    if sharer.expected_recipient != params.recipient:
        expected = RECIPIENTS[sharer.expected_recipient]
        actual = RECIPIENTS[params.recipient]
        return (
            False,
            f"{sharer.name} only borrows the flower for the {expected.need_label} problem, not for {actual.name}'s {actual.need_label} problem.",
        )
    return True, ""


def all_params() -> list[StoryParams]:
    rows: list[StoryParams] = []
    for detective in DETECTIVES:
        for sharer in SHARERS:
            for recipient in RECIPIENTS:
                params = StoryParams(detective, sharer, recipient)
                if valid_params(params)[0]:
                    rows.append(params)
    return rows


def matching_params(args: argparse.Namespace) -> list[StoryParams]:
    matches = []
    for params in all_params():
        if args.detective and params.detective != args.detective:
            continue
        if args.sharer and params.sharer != args.sharer:
            continue
        if args.recipient and params.recipient != args.recipient:
            continue
        matches.append(params)
    return matches


def make_world(params: StoryParams) -> GardenWorld:
    detective = DETECTIVES[params.detective]
    sharer = SHARERS[params.sharer]
    recipient = RECIPIENTS[params.recipient]
    world = GardenWorld(params=params)
    world.add_entity(
        Entity(
            id="detective",
            name=detective.name,
            kind="child detective",
            location="cozy garden",
            meters={"steps": 0},
            memes={"Curiosity": 3, "Calm": 2, "Worry": 0},
        )
    )
    world.add_entity(
        Entity(
            id="sharer",
            name=sharer.name,
            kind="kind child",
            location=recipient.trail_spot,
            meters={"asked_first": 0},
            memes={"Generosity": 3, "Guilt": 1},
        )
    )
    world.add_entity(
        Entity(
            id="recipient",
            name=recipient.name,
            kind="trail walker",
            location=recipient.trail_spot,
            meters={recipient.meter_key: 0},
            memes={"Worry": 2, "Relief": 0},
        )
    )
    world.add_entity(
        Entity(
            id="flower",
            name="the misty flower",
            kind="physical flower",
            location=recipient.trail_spot,
            meters={"glow": 3, "petals": 9, "borrowed": 1},
            memes={"Comfort": 3},
        )
    )
    world.add_entity(
        Entity(
            id="garden",
            name="the cozy garden",
            kind="place",
            location="forest trail edge",
            meters={"pots": 3, "signs": 0},
            memes={"Coziness": 3},
        )
    )
    world.facts["setting"] = "forest trail"
    world.facts["source_tale"] = SOURCE_TALE
    world.facts["garden_intro"] = (
        "Beside the forest trail sat a cozy garden, and in its best clay cup grew a misty flower "
        "that always looked as if dawn had folded itself into petals."
    )
    world.facts["mystery_question"] = (
        f"Who had borrowed the misty flower, and why had they carried it away from the cozy garden?"
    )
    world.facts["sharer_purpose"] = sharer.purpose_text
    world.facts["trail_spot"] = recipient.trail_spot
    return world


def observe_missing_flower(world: GardenWorld) -> None:
    detective = DETECTIVES[world.params.detective]
    world.entities["detective"].memes["Worry"] += 2
    world.record(
        "missing",
        (
            f"On picnic morning, {detective.name} reached the garden gate and found the clay cup empty. "
            "The dark soil was still damp, which meant the flower had been taken gently and not snatched in a hurry."
        ),
        actor="detective",
        target="flower",
        location="cozy garden",
        mystery=3,
        trust=-1,
    )


def inspect_clue(world: GardenWorld) -> None:
    detective = DETECTIVES[world.params.detective]
    sharer = SHARERS[world.params.sharer]
    world.entities["detective"].memes["Curiosity"] += 1
    world.record(
        "clue",
        (
            f"{detective.name} crouched beside the shelf and noticed {sharer.clue_text}. "
            f"It was a tiny clue, but it fit the things {sharer.name} carried, especially {sharer.gear}."
        ),
        actor="detective",
        target="sharer",
        location="cozy garden",
        evidence=2,
    )
    world.facts["clue_text"] = sharer.clue_text
    world.facts["clue_object"] = sharer.clue_object


def follow_trail(world: GardenWorld) -> None:
    detective = DETECTIVES[world.params.detective]
    recipient = RECIPIENTS[world.params.recipient]
    world.entities["detective"].location = recipient.trail_spot
    world.entities["detective"].meters["steps"] += 1
    world.record(
        "trail",
        (
            f"Following the clue, {detective.name} moved down the forest trail until the pines opened at {recipient.trail_spot}. "
            f"There was {recipient.name}, who {recipient.trouble_text}."
        ),
        actor="detective",
        target="recipient",
        location=recipient.trail_spot,
        evidence=1,
    )


def reveal_kindness(world: GardenWorld) -> None:
    detective = DETECTIVES[world.params.detective]
    sharer = SHARERS[world.params.sharer]
    recipient = RECIPIENTS[world.params.recipient]
    recipient_entity = world.entities["recipient"]
    sharer_entity = world.entities["sharer"]
    recipient_entity.meters[recipient.meter_key] += 3
    recipient_entity.memes["Worry"] = 0
    recipient_entity.memes["Relief"] = 3
    sharer_entity.meters["asked_first"] = 0
    world.entities["flower"].meters["glow"] += 1
    world.entities["flower"].location = recipient.trail_spot
    world.record(
        "reveal",
        (
            f"There {detective.name} found {sharer.name}, who had {sharer.action_text}. "
            f"{sharer.name} confessed at once and explained the reason plainly: {sharer.purpose_text}, because {recipient.name} {recipient.trouble_text}."
        ),
        actor="sharer",
        target="recipient",
        location=recipient.trail_spot,
        mystery=-3,
        care=3,
        trust=2,
        sharing=2,
    )
    world.facts["recipient_relief"] = recipient.relief_text
    world.facts["reveal_action"] = sharer.action_text


def make_sharing_rule(world: GardenWorld) -> None:
    detective = DETECTIVES[world.params.detective]
    sharer = SHARERS[world.params.sharer]
    world.entities["flower"].location = "cozy garden"
    world.entities["garden"].meters["signs"] = 1
    world.entities["sharer"].meters["asked_first"] = 1
    world.entities["detective"].memes["Worry"] = 0
    world.record(
        "ending",
        (
            f"{detective.name} solved the whodunit with a soft laugh instead of a scold. "
            f"{sharer.name} promised to ask before borrowing next time, and the children carried the flower back together so sharing would feel honest as well as kind."
        ),
        actor="detective",
        target="flower",
        location="cozy garden",
        care=1,
        trust=1,
        sharing=2,
    )
    world.facts["ending"] = "happy_shared"


def render_story(world: GardenWorld) -> str:
    detective = DETECTIVES[world.params.detective]
    recipient = RECIPIENTS[world.params.recipient]
    final_image = (
        f"By sunset, the misty flower was glowing again in its clay cup at the cozy garden gate, "
        f"and a hand-painted sign promised that anyone on the forest trail could borrow it kindly after asking. "
        f"{recipient.relief_text}"
    )
    world.facts["final_image"] = final_image
    return "\n".join(
        [
            str(world.facts["garden_intro"]),
            (
                f"{world.history[0].text} {detective.name} loved small mysteries, so this one made the whole morning feel like a gentle whodunit. "
                f"{world.facts['mystery_question']}"
            ),
            world.history[1].text,
            world.history[2].text,
            world.history[3].text,
            world.history[4].text,
            final_image,
        ]
    )


def make_prompts(world: GardenWorld) -> list[str]:
    sharer = SHARERS[world.params.sharer]
    recipient = RECIPIENTS[world.params.recipient]
    return [
        "Write a child-friendly whodunit set on a forest trail.",
        "Include the exact phrases cozy garden and misty flower.",
        f"Let the missing flower mystery resolve through sharing when {sharer.name} helps {recipient.name} with {recipient.need_label}.",
    ]


def make_story_qa(world: GardenWorld) -> list[QAItem]:
    detective = DETECTIVES[world.params.detective]
    sharer = SHARERS[world.params.sharer]
    recipient = RECIPIENTS[world.params.recipient]
    return [
        QAItem(
            question="What mystery began the story?",
            answer=(
                "The mystery began when the clay cup in the cozy garden was empty and the misty flower was gone. "
                f"{detective.name} wanted to know who had borrowed it before the picnic path filled with walkers."
            ),
        ),
        QAItem(
            question=f"How did {detective.name} solve the whodunit?",
            answer=(
                f"{detective.name} solved it by noticing {world.facts['clue_text']} and following that clue to {recipient.trail_spot}. "
                f"The clue matched {sharer.name}'s gear, so the answer came from evidence instead of guessing."
            ),
        ),
        QAItem(
            question="Why did the ending become happy instead of angry?",
            answer=(
                f"The ending became happy because {sharer.name} had borrowed the flower to help {recipient.name}, not to keep it selfishly. "
                "Once everyone understood that kindness, they returned the flower together and made a fair sharing rule."
            ),
        ),
    ]


def make_world_qa(world: GardenWorld) -> list[QAItem]:
    sharer = SHARERS[world.params.sharer]
    recipient = RECIPIENTS[world.params.recipient]
    return [
        QAItem(
            question="Where does this story take place?",
            answer=(
                "This story takes place in a cozy garden beside a forest trail. "
                "The mystery starts at the garden gate and then moves to a quiet spot under the pines."
            ),
        ),
        QAItem(
            question="What did the misty flower help with on the trail?",
            answer=(
                f"In this version of the world, the misty flower helped with {recipient.need_label}. "
                f"{sharer.name} borrowed it because the flower's glow and scent could make that trail problem gentler."
            ),
        ),
        QAItem(
            question="What changed after the mystery was solved?",
            answer=(
                "After the mystery was solved, the children stopped treating the flower like a secret treasure that had to stay hidden. "
                "They returned it to the garden and added a borrowing sign so sharing would be open, careful, and kind."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = make_world(params)
    observe_missing_flower(world)
    inspect_clue(world)
    follow_trail(world)
    reveal_kindness(world)
    make_sharing_rule(world)
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
    lines = [
        "setting(forest_trail).",
        "seed_word(cozy_garden).",
        "seed_word(misty_flower).",
        "feature(sharing).",
        "feature(happy_ending).",
        "style(whodunit).",
    ]
    for detective in DETECTIVES:
        lines.append(f"detective({detective}).")
    for sharer, profile in SHARERS.items():
        lines.append(f"sharer({sharer}).")
        lines.append(f"expects({sharer},{profile.expected_recipient}).")
    for recipient in RECIPIENTS:
        lines.append(f"recipient({recipient}).")
    return "\n".join(lines)


ASP_RULES = r"""
compatible(S,R) :- expects(S,R).
invalid(D,S,R) :- detective(D), sharer(S), recipient(R), not compatible(S,R).
valid(D,S,R) :- detective(D), sharer(S), recipient(R), not invalid(D,S,R).
#show valid/3.
"""


def show_asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}"


def solve_asp_models() -> object:
    import asp

    return asp.solve(show_asp_program())


def verify_asp_parity() -> str:
    import asp

    models = asp.solve(show_asp_program())
    model = models[0] if models and isinstance(models[0], list) else models
    asp_valid = {tuple(str(part) for part in atom) for atom in asp.atoms(model, "valid")}
    py_valid = {(p.detective, p.sharer, p.recipient) for p in all_params()}
    if asp_valid != py_valid:
        missing = sorted(py_valid - asp_valid)
        extra = sorted(asp_valid - py_valid)
        raise StoryError(f"ASP mismatch; missing={missing[:5]} extra={extra[:5]}")
    return f"OK: Python and ASP agree on {len(py_valid)} valid whodunit combinations."


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
        if sample.world is None or sample.world.facts.get("ending") != "happy_shared":
            raise StoryError(f"story for {params} did not reach the happy sharing ending")
        if not sample.story_qa or not sample.world_qa or not sample.prompts:
            raise StoryError(f"story for {params} did not populate all output sets")
        if "{" in sample.story or "}" in sample.story:
            raise StoryError(f"story for {params} leaked template braces")
        if "  " in sample.story:
            raise StoryError(f"story for {params} contains doubled spaces")
    return f"OK: Exercised {len(all_params())} generated stories with grounded QA and happy endings."


def verify() -> str:
    parity = verify_asp_parity()
    samples = verify_story_samples()
    return f"{parity}\n{samples}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--detective", choices=sorted(DETECTIVES))
    parser.add_argument("--sharer", choices=sorted(SHARERS))
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
    matches = matching_params(args)
    if not matches:
        requested = StoryParams(
            detective=args.detective or "any",
            sharer=args.sharer or "any",
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


def emit(sample: StorySample, args: argparse.Namespace, header: str | None = None) -> None:
    if header:
        print(header)
    if args.json:
        print(sample.to_json())
        return
    print(sample.story)
    if args.trace:
        print("\nTrace:")
        for event in sample.world.history:
            where = f" @ {event.location}" if event.location else ""
            print(f"- {event.id}{where}: {event.text} {event.delta}")
    if args.qa:
        print("\nPrompts:")
        for item in sample.prompts:
            print(f"- {item}")
        print("\nStory QA:")
        for qa in sample.story_qa:
            print(f"Q: {qa.question}")
            print(f"A: {qa.answer}")
        print("\nWorld QA:")
        for qa in sample.world_qa:
            print(f"Q: {qa.question}")
            print(f"A: {qa.answer}")


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
            print(solve_asp_models())
            return 0
        for index, sample in enumerate(iter_samples(args)):
            header = None
            if not args.json and (args.all or args.n > 1):
                header = f"== sample {index + 1} =="
            if index and not args.json:
                print("\n---\n")
            emit(sample, args, header=header)
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
