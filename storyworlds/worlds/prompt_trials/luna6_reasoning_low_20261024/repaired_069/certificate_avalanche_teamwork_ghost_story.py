#!/usr/bin/env python3
"""A gentle ghost storyworld about teamwork, a certificate, and a snowy avalanche."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child: str = "Luna"
    friend: str = "Theo"
    ghost: str = "Misty"
    incident: int = 0
    opening: int = 0
    exchange: int = 0
    ending: int = 0


CHILDREN = ["Luna", "Milo", "Nell", "Robin"]
FRIENDS = ["Theo", "Ada", "Finn", "June"]
GHOSTS = ["Misty", "Wisp", "Clover", "Pip"]
OPENINGS = [
    "At the little snow lodge, {child} and {friend} were preparing for the winter safety fair.",
    "The mountain village woke beneath a blanket of snow, and {child} hurried to the lodge with {friend}.",
    "A silver moon shone over the snowy trail as {child} and {friend} carried supplies to the fair.",
    "The wind had quieted, but fresh snow still glittered around the village lodge.",
]
EXCHANGES = [
    ("“We should not cross that slope,” said {child}. “The snow is sliding,” replied {friend}. “Then we’ll warn everyone and work from the safe path.”"),
    ("“I can’t reach the bell rope,” said {friend}. “I can hold the lantern while you pull,” said {child}. Misty added, “I’ll guide the message through the snow.”"),
    ("“The certificate is still in the cabin!” cried {child}. “We can get it without climbing the slope,” said {friend}. “I know a quiet way around,” whispered Misty."),
    ("“I thought a ghost would frighten us,” said {friend}. “I’m frightened too,” Misty answered. “Let’s stay together and take one safe step at a time.”"),
]
INCIDENTS = [
    {
        "title": "the avalanche warning",
        "problem": "A small avalanche slid across the upper trail and buried the village warning bell's rope.",
        "clue": "Misty noticed that a line of blue marker flags still showed a safe route around the slope.",
        "plan": "The friends stayed behind the sturdy snow fence. Misty floated along the flagged route while the children tugged a spare bell rope from the safe side.",
        "result": "The warning bell rang, and the villagers gathered safely in the warm lodge.",
        "certificate": "Afterward, the safety teacher gave the three helpers a certificate for their careful teamwork.",
        "image": "Their certificate rested beside the bell, while snowflakes drifted harmlessly beyond the fence.",
        "object": "warning bell",
    },
    {
        "title": "the certificate in the cabin",
        "problem": "A gentle avalanche covered the cabin path just as the winter fair's teamwork certificate was needed.",
        "clue": "Misty spotted a sheltered path marked by red poles that led to the cabin from the other side.",
        "plan": "The children waited with the ranger while Misty carried a lantern along the marked path and showed them where the certificate lay inside.",
        "result": "The ranger retrieved the certificate without anyone stepping onto the unstable slope.",
        "certificate": "At the fair, the children received the certificate together for choosing a safe plan.",
        "image": "The bright certificate hung in the lodge window, far from the snow-covered path.",
        "object": "teamwork certificate",
    },
    {
        "title": "the stranded snowcat",
        "problem": "A little snowcat was stuck near the edge of a fresh avalanche, and its driver could not see the safe way back.",
        "clue": "Misty saw the driver's lantern blink behind a row of tall spruce trees, away from the slide.",
        "plan": "The children called the ranger and held up bright scarves as signals while Misty guided the driver toward the marked shelter.",
        "result": "The driver reached the shelter safely, and the ranger closed the trail until the snow settled.",
        "certificate": "The driver later presented the friends with a certificate honoring their teamwork and clear signals.",
        "image": "Three scarves fluttered beneath the certificate as the snowcat rested safely in the village.",
        "object": "bright scarves",
    },
    {
        "title": "the lost mountain mittens",
        "problem": "A small avalanche swept a basket of warm mittens off the fair path and left them near a closed trail.",
        "clue": "Misty heard the basket's little bell ringing from behind the safety barrier.",
        "plan": "The children asked the ranger to use a long reaching pole while Misty watched from the lodge window and pointed out the basket.",
        "result": "The mittens were brought back without anyone entering the closed area.",
        "certificate": "The fair leader awarded the team a certificate for helping others while respecting the safety barrier.",
        "image": "Warm mittens filled the fair basket beneath the certificate, ready for every visitor.",
        "object": "basket of mittens",
    },
]


ASP_RULES = r"""
safe_team :- danger(avalanche), plan(teamwork), helper(ghost).
certificate_awarded :- safe_team, completes(rescue).
#show safe_team/0.
#show certificate_awarded/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("danger", "avalanche"),
            asp.fact("plan", "teamwork"),
            asp.fact("helper", "ghost"),
            asp.fact("completes", "rescue"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A snowy ghost story about an avalanche, teamwork, and a certificate."
    )
    parser.add_argument("--child", choices=CHILDREN)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--ghost", choices=GHOSTS)
    parser.add_argument("--incident", type=int, choices=range(len(INCIDENTS)))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.n < 1:
        raise StoryError("The number of stories must be at least one.")
    return StoryParams(
        seed=args.seed,
        child=args.child or rng.choice(CHILDREN),
        friend=args.friend or rng.choice(FRIENDS),
        ghost=args.ghost or rng.choice(GHOSTS),
        incident=args.incident if args.incident is not None else rng.randrange(len(INCIDENTS)),
        opening=rng.randrange(len(OPENINGS)),
        exchange=rng.randrange(len(EXCHANGES)),
        ending=rng.randrange(len(INCIDENTS)),
    )


def generate(params: StoryParams) -> StorySample:
    if params.child not in CHILDREN:
        raise StoryError(f"Unknown child name: {params.child!r}.")
    if params.friend not in FRIENDS:
        raise StoryError(f"Unknown friend name: {params.friend!r}.")
    if params.ghost not in GHOSTS:
        raise StoryError(f"Unknown ghost name: {params.ghost!r}.")
    if not 0 <= params.incident < len(INCIDENTS):
        raise StoryError("The incident number is outside the available story choices.")
    if not 0 <= params.opening < len(OPENINGS) or not 0 <= params.exchange < len(EXCHANGES):
        raise StoryError("The selected story variation is not available.")

    incident = INCIDENTS[params.incident]
    world = World()
    child = world.add(
        Entity(params.child, "character", "child", params.child, memes={"courage": 0.5})
    )
    friend = world.add(
        Entity(params.friend, "character", "child", params.friend, memes={"care": 0.7})
    )
    ghost = world.add(
        Entity(params.ghost, "character", "ghost", params.ghost, meters={"visibility": 0.4}, memes={"kindness": 0.9})
    )
    world.facts.update(
        child=child,
        friend=friend,
        ghost=ghost,
        incident=incident,
        teamwork=True,
        avalanche=True,
        safe=True,
        certificate=True,
    )

    names = {"child": child.id, "friend": friend.id, "ghost": ghost.id}
    world.say(OPENINGS[params.opening].format(**names))
    world.say(f"{ghost.id} appeared in a pale shimmer beside the lodge. The gentle ghost had come to help.")
    world.say(incident["problem"])
    dialogue = EXCHANGES[params.exchange].format(**names)
    world.say(dialogue)
    world.say(incident["clue"])
    world.say(incident["plan"])
    world.say(incident["result"])
    world.say(incident["certificate"])
    child.memes["confidence"] = 1.0
    friend.memes["trust"] = 1.0
    ghost.meters["visibility"] = 0.7
    world.say(incident["image"])

    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a gentle ghost story about {child.id}, {friend.id}, and {ghost.id} helping together during {incident['title']}.",
            "Tell a child-friendly snowy adventure where teamwork leads to a safe choice and a certificate.",
            f"End with a clear image of the {incident['object']} and show what changed.",
        ],
        story_qa=[
            QAItem(
                question=f"What problem did the team face in {incident['title']}?",
                answer=incident["problem"],
            ),
            QAItem(
                question=f"What clue did {ghost.id} notice?",
                answer=incident["clue"],
            ),
            QAItem(
                question="How did the friends work together safely?",
                answer=incident["plan"],
            ),
            QAItem(
                question="Why did the team receive a certificate?",
                answer=incident["certificate"],
            ),
        ],
        world_qa=[
            QAItem(
                question="What is an avalanche?",
                answer="An avalanche is a large amount of snow that suddenly slides down a mountainside.",
            ),
            QAItem(
                question="Why is teamwork useful in an emergency?",
                answer="Teamwork lets people share information and responsibilities, so they can make safer choices together.",
            ),
            QAItem(
                question="What is a certificate?",
                answer="A certificate is a written document that recognizes an achievement or records that someone completed something.",
            ),
        ],
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label} ({entity.type}): meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  facts: {sorted(world.facts)}")
    return "\n".join(lines)


def asp_valid() -> set[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "safe_team")), set(asp.atoms(model, "certificate_awarded"))


def asp_verify() -> int:
    try:
        python_gate = {((), ((),))}
        clingo_gate = asp_valid()
        if clingo_gate != python_gate:
            print("MISMATCH between clingo and Python reasonableness gate.")
            print("  clingo:", clingo_gate)
            print("  python:", python_gate)
            return 1
        for incident_index in range(len(INCIDENTS)):
            sample = generate(
                StoryParams(
                    child=CHILDREN[incident_index % len(CHILDREN)],
                    friend=FRIENDS[incident_index % len(FRIENDS)],
                    ghost=GHOSTS[incident_index % len(GHOSTS)],
                    incident=incident_index,
                )
            )
            if not all(word in sample.story for word in ("avalanche", "certificate")):
                raise StoryError("A generated verification story omitted a required story element.")
            if not any(mark in sample.story for mark in ("“", "”")):
                raise StoryError("A generated verification story omitted spoken dialogue.")
        print("OK: ASP parity and generated-story checks passed.")
        return 0
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.show_asp:
        print(asp_program("#show safe_team/0.\n#show certificate_awarded/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        safe, certificate = asp_valid()
        print("ASP teamwork result:")
        print("  safe team:", sorted(safe))
        print("  certificate awarded:", sorted(certificate))
        return
    if args.n < 1 and not args.all:
        parser.error("-n must be at least one")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for index in range(len(INCIDENTS)):
            samples.append(
                generate(
                    StoryParams(
                        seed=base_seed,
                        child=CHILDREN[index % len(CHILDREN)],
                        friend=FRIENDS[index % len(FRIENDS)],
                        ghost=GHOSTS[index % len(GHOSTS)],
                        incident=index,
                        opening=index % len(OPENINGS),
                        exchange=index % len(EXCHANGES),
                    )
                )
            )
    else:
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            samples.append(generate(resolve_params(args, rng)))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### {sample.params.child}: {INCIDENTS[sample.params.incident]['title']}" if args.all else (
            f"### variant {index + 1}" if len(samples) > 1 else ""
        )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
