#!/usr/bin/env python3
"""
A small mythic storyworld about teamwork, chard, and a skate-park lair.

A young skater discovers that a lair beneath the skate park is guarded by a
vegetable-loving stone guardian. The guardian's trouble is solved not by one
hero, but by a team that listens, shares jobs, and turns an obstacle into a
safe new ramp.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    skater: str
    friend: str
    coach: str
    guardian: str
    lair: str
    chard: str
    challenge: int = 0
    omen: int = 0
    teamwork: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SKATERS = ["Luna", "Milo", "Nia", "Tavi", "Rin", "Oren", "Pia", "Sol"]
FRIENDS = ["Bea", "Jax", "Kiko", "Mara", "Theo", "Wren"]
COACHES = ["Coach Imani", "Coach Vale", "Coach Rowan", "Coach June"]
GUARDIANS = ["the Moss Giant", "the Stone Owl", "the Ramp Keeper", "the Green Knight"]
LAIRS = ["the Moon-Ramp Lair", "the Root-Tunnel Lair", "the Echo Bowl Lair", "the Lantern Lair"]
CHARD = ["rainbow chard", "crimson chard", "silver chard", "golden chard"]

OMENS = [
    "At sunset, a green spark flickered beneath the oldest quarter pipe.",
    "Three pigeons circled the bowl and dropped a single bright chard leaf.",
    "The wheels of a resting skateboard pointed toward a crack shaped like a crescent moon.",
    "A soft rumble rose under the ramps, though the park was still and empty.",
    "A chalk arrow appeared beside the rail, pointing toward a hidden gate.",
    "The park lights blinked once, twice, and then shone on a vine-covered doorway.",
]

CHALLENGES = [
    {
        "lead": "Behind the bowl, the team found {lair}, where a stone door was pinned shut by a fallen metal sign.",
        "risk": "The sign was too heavy for one person, and its sharp corner blocked the narrow path.",
        "method": "Luna studied the wheels, Mara braced the sign, and {coach} showed them how to lift only when everyone was ready.",
        "result": "Together they rolled the sign onto a stack of soft pads and opened the doorway without scraping the stone.",
        "cause": "a fallen metal sign pinned the lair door shut",
        "deed": "the team shared jobs, counted together, and rolled the sign onto safe pads",
        "proof": "the lair door opened while every teammate stayed safe",
    },
    {
        "lead": "Inside {lair}, the guardian's glowing chard garden had spilled across the only skating path.",
        "risk": "If anyone rushed through, the tender leaves would tear and the path would become slippery.",
        "method": "Luna carried baskets, {friend} marked a gentle route with cones, and {coach} asked everyone to pass each plant hand to hand.",
        "result": "The team moved the chard into a sunny bed, leaving a smooth path through the lair.",
        "cause": "the guardian's chard garden covered the only safe path",
        "deed": "the team moved each plant carefully into a sunny bed",
        "proof": "the chard was safe and a clear path remained",
    },
    {
        "lead": "A deep bell rang in {lair}, and a stone gate began sliding toward the skate park bowl.",
        "risk": "The gate could block the bowl before the younger skaters noticed it moving.",
        "method": "Luna warned the park, {friend} placed bright cones, and {coach} directed the team to pull the gate's three ropes at once.",
        "result": "Their single strong pull stopped the gate beside the bowl instead of across it.",
        "cause": "a sliding stone gate threatened to block the skate bowl",
        "deed": "the team warned skaters, marked the danger, and pulled three ropes together",
        "proof": "the gate stopped safely beside the bowl",
    },
    {
        "lead": "The guardian led the team to {lair}, where a moonstone had rolled beneath a wobbling launch ramp.",
        "risk": "Touching the ramp alone might make it tip, but leaving the moonstone there made the guardian's light fade.",
        "method": "Luna watched the ramp, {friend} fetched wooden blocks, and {coach} counted as the team steadied and raised it.",
        "result": "The moonstone rolled free, and the ramp settled on the blocks like a bridge.",
        "cause": "a moonstone was trapped beneath a wobbling launch ramp",
        "deed": "the team braced the ramp before lifting it together",
        "proof": "the moonstone was freed and the ramp became steady",
    },
    {
        "lead": "At the heart of {lair}, vines had wrapped around the bell that welcomed every skater.",
        "risk": "Pulling the vines all at once might crack the old bell or snap the nearby rail.",
        "method": "Luna loosened small loops, {friend} held the rail still, and {coach} used a cool cloth to protect the bell.",
        "result": "The vines came away in soft coils, and the bell rang a warm note over the park.",
        "cause": "thick vines tangled the lair's welcome bell",
        "deed": "the team loosened the vines in small turns while protecting the bell",
        "proof": "the bell rang without damage",
    },
]

TEAMWORK_LINES = [
    "\"I can watch the wheels,\" said {skater}. \"I can guide the load,\" said {friend}. \"Then I will count,\" said {coach}. Their three jobs became one brave plan.",
    "\"Lift on three?\" asked {friend}. \"On three,\" said {skater}. The guardian added, \"A shared word is stronger than a lonely roar.\"",
    "{skater} said, \"No one has to do this alone.\" {friend} replied, \"Good, because I have the map!\" Even {coach} laughed before joining the plan.",
    "\"You notice the danger, I can carry the tools, and {coach} can keep us steady,\" said {friend}. {skater} nodded. The lair seemed to listen.",
    "The guardian asked, \"Who is the hero?\" {skater} answered, \"The team.\" That answer made the hidden stones glow.",
    "\"Pass, pause, and check,\" said {coach}. \"Pass, pause, and check,\" the children repeated until the work felt like a careful skate rhythm.",
]

ENDINGS = [
    "When the work was done, the guardian planted a row of bright chard beside the bowl. Each leaf shone like a tiny green flag for teamwork.",
    "The stone door became a new low ramp, smooth enough for beginners. {skater} took the first ride while the whole team cheered from the edge.",
    "At dusk, the lair's bell rang over the skate park. Its echo sounded like many voices saying one kind word together.",
    "The guardian gave the team a chard leaf shaped like a star. They tucked it beside the park map so every future skater could find the safe path.",
    "Under the moon, the team painted three arrows on the repaired ramp: notice, help, and share. Then they skated through the lair in a bright little parade.",
    "The next morning, nobody called the hidden place a scary hole. They called it the Teamwork Lair, where every careful hand helped the park grow.",
]

ASP_RULES = r"""
#show valid/4.
#show valid_story/6.

skater(S) :- skater_name(S).
friend(F) :- friend_name(F).
coach(C) :- coach_name(C).
guardian(G) :- guardian_name(G).
lair(L) :- lair_name(L).
chard(H) :- chard_name(H).

compatible_lair(L, H) :- lair_name(L), chard_name(H).

valid(S, F, C, L) :-
    skater_name(S),
    friend_name(F),
    coach_name(C),
    compatible_lair(L, H),
    chard_name(H).

valid_story(S, F, C, G, L, H) :-
    valid(S, F, C, L),
    guardian_name(G),
    chard_name(H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for value in SKATERS:
        lines.append(asp.fact("skater_name", value))
    for value in FRIENDS:
        lines.append(asp.fact("friend_name", value))
    for value in COACHES:
        lines.append(asp.fact("coach_name", value))
    for value in GUARDIANS:
        lines.append(asp.fact("guardian_name", value))
    for value in LAIRS:
        lines.append(asp.fact("lair_name", value))
    for value in CHARD:
        lines.append(asp.fact("chard_name", value))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [(lair, leaf) for lair in LAIRS for leaf in CHARD]


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    combos: set[tuple[str, str]] = set()
    for _, _, _, lair in asp.atoms(model, "valid"):
        for leaf in CHARD:
            if (lair, leaf) in valid_combos():
                combos.add((lair, leaf))
    return sorted(combos)


def asp_verify() -> int:
    python_pairs = set(valid_combos())
    asp_pairs = set(asp_valid_combos())
    if python_pairs == asp_pairs:
        print(f"OK: clingo gate matches valid_combos() ({len(python_pairs)} combos).")
        for params in build_curated():
            sample = generate(params)
            if not sample.story or "team" not in sample.story.lower():
                print("Generated-story verification failed.")
                return 1
        print("OK: generated stories passed the teamwork gate.")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_pairs - asp_pairs:
        print("  only in python:", sorted(python_pairs - asp_pairs))
    if asp_pairs - python_pairs:
        print("  only in clingo:", sorted(asp_pairs - python_pairs))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    chosen_lair = args.lair
    chosen_chard = args.chard
    if chosen_lair and chosen_lair not in LAIRS:
        raise StoryError("No story: that lair is not part of the skate park myth.")
    if chosen_chard and chosen_chard not in CHARD:
        raise StoryError("No story: that chard variety is not in the garden registry.")

    return StoryParams(
        skater=args.skater or rng.choice(SKATERS),
        friend=args.friend or rng.choice(FRIENDS),
        coach=args.coach or rng.choice(COACHES),
        guardian=args.guardian or rng.choice(GUARDIANS),
        lair=chosen_lair or rng.choice(LAIRS),
        chard=chosen_chard or rng.choice(CHARD),
        challenge=rng.randrange(len(CHALLENGES)),
        omen=rng.randrange(len(OMENS)),
        teamwork=rng.randrange(len(TEAMWORK_LINES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def apply_seeded_structure(params: StoryParams, seed: int) -> None:
    params.challenge = seed % len(CHALLENGES)
    params.omen = (seed // len(CHALLENGES)) % len(OMENS)
    params.teamwork = (seed // 3) % len(TEAMWORK_LINES)
    params.ending = (seed // 5) % len(ENDINGS)


def generate(params: StoryParams) -> StorySample:
    values = {
        "skater": params.skater,
        "friend": params.friend,
        "coach": params.coach,
        "guardian": params.guardian,
        "lair": params.lair,
        "chard": params.chard,
    }
    challenge = CHALLENGES[params.challenge % len(CHALLENGES)]

    world = World()
    skater = world.add(Entity(params.skater, "character", params.skater, memes={"courage": 0.2}))
    friend = world.add(Entity(params.friend, "character", params.friend, memes={"care": 0.3}))
    coach = world.add(Entity(params.coach, "character", params.coach, memes={"wisdom": 0.5}))
    guardian = world.add(Entity(params.guardian, "character", params.guardian, memes={"trust": 0.0}))
    lair = world.add(Entity("lair", "place", params.lair, meters={"door": 0.0}))
    garden = world.add(Entity("chard", "plant", params.chard, meters={"leaves": 1.0}, memes={"sacred": 1.0}))
    ramp = world.add(Entity("ramp", "thing", "the skate ramp", meters={"stability": 0.4}))

    world.say(
        f"{params.skater} loved the skate park, where wheels hummed over ramps and the evening sun painted the rails gold."
    )
    world.say(OMENS[params.omen % len(OMENS)])
    world.say(
        f"With {params.friend} and {params.coach}, {params.skater} followed the sign to {params.lair}. "
        f"At its gate stood {params.guardian}, holding a bundle of {params.chard} like a royal torch."
    )

    world.para()
    lair.meters["door"] = 1.0
    garden.meters["leaves"] = 0.8
    ramp.meters["stability"] = 0.3
    skater.memes["courage"] = 0.8
    world.say(challenge["lead"].format(**values))
    world.say(challenge["risk"].format(**values))
    world.say(f"{params.guardian} frowned. \"The lair will stay closed unless the danger is solved with care.\"")
    world.say(challenge["method"].format(**values))

    world.para()
    friend.memes["care"] = 1.0
    coach.memes["wisdom"] = 1.0
    guardian.memes["trust"] = 1.0
    ramp.meters["stability"] = 1.0
    lair.meters["door"] = 0.0
    world.say(TEAMWORK_LINES[params.teamwork % len(TEAMWORK_LINES)].format(**values))
    world.say(challenge["result"].format(**values))
    world.say(
        f"{params.guardian} bowed to the team. \"You did not defeat the obstacle,\" said the guardian. "
        f"\"You taught it how to help.\""
    )
    world.say(ENDINGS[params.ending % len(ENDINGS)].format(**values))

    world.facts.update(
        skater=params.skater,
        friend=params.friend,
        coach=params.coach,
        guardian=params.guardian,
        lair=params.lair,
        chard=params.chard,
        challenge=params.challenge % len(CHALLENGES),
        danger=challenge["cause"],
        teamwork_action=challenge["deed"],
        result=challenge["proof"],
        resolved=True,
    )

    prompts = [
        "Write a child-friendly myth about a skate park lair where teamwork solves a magical problem involving chard.",
        f"Tell a mythic skate-park adventure in which {params.skater}, {params.friend}, and {params.coach} help {params.guardian}.",
        f"Write a teamwork story with {params.lair}, {params.chard}, a clear danger, shared jobs, and a changed skate park.",
    ]

    story_qa = [
        QAItem(
            question="Where did the adventure happen?",
            answer=f"The adventure happened at a skate park and continued inside {params.lair}.",
        ),
        QAItem(
            question=f"What problem did {params.skater} and the team face?",
            answer=f"They faced a problem because {challenge['cause']}. The team had to protect the skate park and the lair.",
        ),
        QAItem(
            question="How did teamwork solve the problem?",
            answer=f"The team solved it when {challenge['deed']}. Their different jobs worked together.",
        ),
        QAItem(
            question="How could readers tell the problem was resolved?",
            answer=f"They could tell because {challenge['proof']}. The guardian trusted the team and the park became safer.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a lair?",
            answer="A lair is a hidden home or resting place, often belonging to a creature in a myth or adventure.",
        ),
        QAItem(
            question="What is chard?",
            answer="Chard is a leafy vegetable with colorful stems that can be cooked or eaten fresh.",
        ),
        QAItem(
            question="Why is teamwork useful?",
            answer="Teamwork is useful because people can share jobs, notice different details, and solve a difficult problem together.",
        ),
        QAItem(
            question="What makes a myth feel magical?",
            answer="A myth often includes a mysterious place, a guardian, or an unusual event that teaches a lasting lesson.",
        ),
        QAItem(
            question="How can a skate park be kept safe?",
            answer="A skate park can be kept safe by checking ramps, marking hazards, sharing space, and helping others follow careful routes.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
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
    for entity in world.entities.values():
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id:10} ({entity.kind:9}) {' '.join(details)}")
    if world.facts:
        lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(
            "Luna", "Bea", "Coach Imani", "the Moss Giant",
            "the Moon-Ramp Lair", "rainbow chard", 0, 0, 0, 0
        ),
        StoryParams(
            "Milo", "Jax", "Coach Vale", "the Stone Owl",
            "the Root-Tunnel Lair", "crimson chard", 1, 1, 1, 1
        ),
        StoryParams(
            "Nia", "Mara", "Coach Rowan", "the Ramp Keeper",
            "the Echo Bowl Lair", "silver chard", 2, 2, 2, 2
        ),
        StoryParams(
            "Tavi", "Kiko", "Coach June", "the Green Knight",
            "the Lantern Lair", "golden chard", 3, 3, 3, 3
        ),
    ]


CURATED = build_curated()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A mythic skate-park storyworld about lairs, chard, and teamwork."
    )
    parser.add_argument("--skater", choices=SKATERS)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--coach", choices=COACHES)
    parser.add_argument("--guardian", choices=GUARDIANS)
    parser.add_argument("--lair", choices=LAIRS)
    parser.add_argument("--chard", choices=CHARD)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


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
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/6."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_combos()
        print(f"{len(pairs)} compatible (lair, chard) combinations:\n")
        for lair, leaf in pairs:
            print(f"  {lair:24} -> {leaf}")
        return

    if args.n < 1:
        raise StoryError("The number of stories must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
            params.seed = seed
            apply_seeded_structure(params, seed)
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.skater}: {params.lair} at the skate park"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
