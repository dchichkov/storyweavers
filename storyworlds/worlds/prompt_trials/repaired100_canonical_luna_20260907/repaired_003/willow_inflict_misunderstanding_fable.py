#!/usr/bin/env python3
"""
A small fable about Willow, a rushed message, and the gentle repair of a
misunderstanding.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    setting: str
    seed: Optional[int] = None
    child_name: str = "Luna"
    helper_name: str = "Milo"
    creature: str = "willow"
    feature: str = "Misunderstanding"
    style: str = "Fable"


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def inc_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def inc_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class World:
    setting: str
    child: Entity
    friend: Entity
    tree: Entity
    basket: Entity
    note: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for entity in (
            self.child,
            self.friend,
            self.tree,
            self.basket,
            self.note,
        ):
            meters = {k: v for k, v in entity.meters.items() if v}
            memes = {k: v for k, v in entity.memes.items() if v}
            details = []
            if meters:
                details.append(f"meters={meters}")
            if memes:
                details.append(f"memes={memes}")
            lines.append(
                f"  {entity.id:10} ({entity.kind:9}) {' '.join(details)}"
            )
        lines.append(f"  setting: {self.setting}")
        return "\n".join(lines)


SETTINGS = {
    "garden": "the village garden",
    "meadow": "the sunny meadow",
    "pond": "the pond beneath the hill",
    "orchard": "the old orchard",
}

NAMES = ["Luna", "Pia", "Tomas", "Niko", "Suri"]
FRIENDS = ["Milo", "Ada", "Tavi", "Rose", "Finn"]

EVENTS = [
    {
        "opening": (
            "{child} carried a basket of red apples beneath a graceful willow "
            "beside {setting}."
        ),
        "clue": (
            "A folded note lay under the basket handle, marked with {friend}'s name."
        ),
        "message": "Please leave the apples by the gate. I must hurry home.",
        "misread": (
            "{child} read the hurried words and thought {friend} was cross "
            "about the apples."
        ),
        "action": (
            "{child} tucked the basket beneath the willow and walked away quietly."
        ),
        "reveal": (
            "{friend} soon arrived, breathless, carrying a tiny bluebird with a "
            "hurt wing. The note had meant that {friend} needed to hurry to help "
            "the bird, not that {friend} disliked the apples."
        ),
        "repair": (
            "{child} listened again, apologized for guessing, and helped make a "
            "soft nest from grass and fallen willow leaves."
        ),
    },
    {
        "opening": (
            "{child} painted a bright sign beneath a cool willow at {setting}."
        ),
        "clue": (
            "A note from {friend} rested beside the paint pot."
        ),
        "message": "Do not show the sign yet. I have a surprise.",
        "misread": (
            "{child} feared that {friend} wanted the painting hidden because it "
            "looked silly."
        ),
        "action": (
            "{child} turned the sign toward the willow trunk and sat with a sad face."
        ),
        "reveal": (
            "{friend} came back wearing a paper crown. The surprise was a small "
            "parade for {child}'s beautiful sign."
        ),
        "repair": (
            "{child} asked what the words meant, and {friend} explained before "
            "they marched beneath the willow together."
        ),
    },
    {
        "opening": (
            "At {setting}, {child} found a little bell hanging from a willow branch."
        ),
        "clue": (
            "A note beside it said that {friend} would return after sunset."
        ),
        "message": "Keep the bell safe until I return.",
        "misread": (
            "{child} wondered if {friend} did not trust anyone else with the bell."
        ),
        "action": (
            "{child} held the bell tightly and waited alone beneath the willow."
        ),
        "reveal": (
            "{friend} returned with a loose wheel from a toy cart. The bell was "
            "meant to help them find one another while repairing the cart."
        ),
        "repair": (
            "{child} admitted the mistake, and the two friends tied the bell to "
            "the cart before rolling it home."
        ),
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A fable about Willow, Luna, and repairing a misunderstanding."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def _validate_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Choose a setting such as the garden, meadow, pond, or orchard.")
    if not params.child_name or not params.helper_name:
        raise StoryError("Both friends need names so their conversation is clear.")
    if params.creature != "willow":
        raise StoryError("This fable's living landmark must be a willow.")
    if params.feature != "Misunderstanding":
        raise StoryError("This fable must center on a Misunderstanding.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        seed=args.seed,
        child_name=args.name or rng.choice(NAMES),
        helper_name=args.friend or rng.choice(FRIENDS),
    )
    _validate_params(params)
    return params


def make_world(params: StoryParams) -> World:
    return World(
        setting=SETTINGS[params.setting],
        child=Entity(
            id="child",
            kind="character",
            label=params.child_name,
            type="child",
        ),
        friend=Entity(
            id="friend",
            kind="character",
            label=params.helper_name,
            type="friend",
        ),
        tree=Entity(
            id="willow",
            kind="place",
            label="willow",
            type="tree",
            meters={"shade": 1.0, "shelter": 1.0},
        ),
        basket=Entity(
            id="basket",
            kind="thing",
            label="basket",
            type="container",
        ),
        note=Entity(
            id="note",
            kind="thing",
            label="folded note",
            type="message",
        ),
    )


def _build_story(world: World, params: StoryParams) -> None:
    rng = random.Random((params.seed or 0) + 31337)
    event = rng.choice(EVENTS)
    child = world.child
    friend = world.friend

    child.memes["trust"] = 1.0
    child.memes["certainty"] = 0.0
    friend.memes["care"] = 1.0
    world.note.meters["clarity"] = 0.0
    world.note.meters["unread"] = 1.0

    opening = event["opening"].format(
        child=child.label,
        friend=friend.label,
        setting=world.setting,
    )
    clue = event["clue"].format(
        child=child.label,
        friend=friend.label,
        setting=world.setting,
    )
    misread = event["misread"].format(child=child.label, friend=friend.label)
    action = event["action"].format(child=child.label, friend=friend.label)
    reveal = event["reveal"].format(child=child.label, friend=friend.label)
    repair = event["repair"].format(child=child.label, friend=friend.label)

    world.say(opening)
    world.say(
        f"The willow's long green branches made a quiet roof, and {child.label} "
        "felt proud to be helping a friend."
    )
    world.say(clue)
    world.say(f'The note said, "{event["message"]}"')
    world.say(misread)

    child.memes["certainty"] = 1.0
    child.memes["trust"] = 0.25
    world.note.meters["unread"] = 0.0
    world.note.meters["misunderstood"] = 1.0
    child.inc_meter("distance", 1.0)

    world.para()
    world.say(action)
    world.say(
        f"Just then, {friend.label} called, “Wait, {child.label}! Please tell me "
        "what you thought I meant.”"
    )
    world.say(
        f"{child.label} answered, “I thought you were upset with me.” "
        f"{friend.label} shook their head. “No. I was rushing to explain something "
        "important. I should have written more clearly.”"
    )
    friend.inc_meter("explanation", 1.0)
    child.inc_meter("listening", 1.0)

    world.para()
    world.say(reveal)
    world.note.meters["clarity"] = 1.0
    world.note.meters["misunderstood"] = 0.0
    child.memes["certainty"] = 0.0
    child.memes["trust"] = 1.0

    world.say(
        f"{child.label} saw that the sharp feeling had come from a guess, not from "
        f"{friend.label}'s heart. The {params.feature.lower()} began to loosen."
    )
    world.say(repair)
    child.inc_meme("wisdom", 1.0)
    friend.inc_meme("honesty", 1.0)

    world.para()
    world.say(
        f"From then on, {child.label} and {friend.label} asked gentle questions "
        "before believing a worried thought."
    )
    world.say(
        "The willow swayed above them, and its leaves whispered the old fable's "
        "lesson: a hurried guess may inflict sadness, but honest words can mend it."
    )

    world.facts.update(
        event=event,
        misunderstood=True,
        repaired=True,
        message=event["message"],
        reveal=reveal,
        repair=repair,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        (
            f"Write a child-friendly fable set near {world.setting}, where "
            f"{world.child.label} misunderstands {world.friend.label} beneath a willow."
        ),
        (
            "Tell a gentle story in which a rushed note causes a misunderstanding, "
            "spoken questions reveal the truth, and friendship is repaired."
        ),
        (
            "Write a fable whose ending shows that unclear words can inflict sadness "
            "but honest conversation can restore trust."
        ),
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.child.label
    friend = world.friend.label
    return [
        QAItem(
            question=f"What did {child} misunderstand?",
            answer=(
                f"{child} thought {friend}'s hurried note showed anger or distrust, "
                "but it actually explained a kind and urgent plan."
            ),
        ),
        QAItem(
            question=f"How did {friend} repair the misunderstanding?",
            answer=(
                f"{friend} asked {child} what the note had seemed to mean, explained "
                "the missing context, and admitted the note should have been clearer."
            ),
        ),
        QAItem(
            question="What changed beneath the willow?",
            answer=(
                "The worried guess was replaced by a clear explanation, so the "
                "friends returned to trust and worked together again."
            ),
        ),
        QAItem(
            question="What caused the sadness?",
            answer=(
                "A rushed message left out important context, and the missing "
                "context allowed a fearful guess to grow."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer=(
                "A misunderstanding happens when someone gives a meaning to words "
                "that the speaker did not intend."
            ),
        ),
        QAItem(
            question="How can people repair a misunderstanding?",
            answer=(
                "They can ask calm questions, listen carefully, explain their "
                "intentions, and apologize for any unclear words."
            ),
        ),
        QAItem(
            question="What does a willow provide in this fable?",
            answer=(
                "The willow provides shade, shelter, and a peaceful place where "
                "the friends can speak honestly."
            ),
        ),
        QAItem(
            question="What is the fable's lesson?",
            answer=(
                "Do not let a quick guess inflict lasting sadness; ask for the "
                "truth and use kind, clear words."
            ),
        ),
    ]


ASP_RULES = r"""
misunderstanding :- rushed_message, missing_context.
repair_possible :- misunderstanding, asks_question, explains_intent.
trust_restored :- repair_possible, listens, apology.
good_fable :- willow_place, trust_restored.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    facts = [
        asp.fact("willow_place"),
        asp.fact("rushed_message"),
        asp.fact("missing_context"),
        asp.fact("asks_question"),
        asp.fact("explains_intent"),
        asp.fact("listens"),
        asp.fact("apology"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show good_fable/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _python_reasonable(params: StoryParams) -> bool:
    return (
        params.creature == "willow"
        and params.feature == "Misunderstanding"
        and params.style == "Fable"
        and params.setting in SETTINGS
    )


def asp_verify() -> int:
    params = StoryParams(setting="garden")
    if not _python_reasonable(params):
        print("MISMATCH: Python reasonableness gate failed.")
        return 1
    try:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        if not any(str(atom) == "good_fable" for atom in model):
            print("MISMATCH: ASP did not derive good_fable.")
            return 1
    except ImportError:
        print("OK: Python reasonableness gate passed; clingo is unavailable.")
        return 0
    except Exception as exc:
        print(f"MISMATCH: ASP verification failed: {exc}")
        return 1

    sample = generate(params)
    required = ["willow", "misunderstanding", "inflict"]
    text = sample.story.lower()
    if not all(word in text for word in required):
        print("MISMATCH: generated story missed a required narrative instrument.")
        return 1
    print("OK: Python and ASP parity passed; generated story exercised.")
    return 0


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = make_world(params)
    _build_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print("== Generation prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print()
        print("== Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== World questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(setting="garden", child_name="Luna", helper_name="Milo"),
    StoryParams(setting="meadow", child_name="Pia", helper_name="Ada"),
    StoryParams(setting="pond", child_name="Tomas", helper_name="Tavi"),
    StoryParams(setting="orchard", child_name="Suri", helper_name="Finn"),
]


def build_all_samples() -> list[StorySample]:
    return [generate(params) for params in CURATED]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import storyworlds.asp as asp

            models = asp.solve(asp_program(), models=1)
            print("ASP model:", ", ".join(str(atom) for atom in models[0]))
        except ImportError:
            print("ASP support requires clingo.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = build_all_samples()
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
