#!/usr/bin/env python3
from __future__ import annotations

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
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
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


@dataclass
class StoryParams:
    detective: str
    partner: str
    suspect: str
    room: str
    clue_id: int = 0
    opening_id: int = 0
    dialogue_id: int = 0
    action_id: int = 0
    ending_id: int = 0
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Ivy", "Theo", "Nora", "Sam"]
PARTNERS = ["Pip", "June", "Arlo", "Tess"]
SUSPECTS = ["the little robot", "the brass beetle", "the wind-up fox", "the blue cart"]
ROOMS = ["the school workshop", "the old museum room", "the neighborhood shed", "the rainy-day clubhouse"]

CASES = [
    {
        "object": "the missing brass key",
        "problem": "the key to the story cupboard had vanished",
        "crud": "a smear of green crud",
        "clue": "the crud marked a crooked trail from the sink to the stuck cupboard",
        "cause": "a leaking jar of craft paste had spilled when the blue cart bumped the sink",
        "capture": "they trapped the rolling cart gently between two empty crates",
        "answer": "the blue cart had pushed the key beneath the cupboard door",
        "ending": "the key clicked into the lock, and the cupboard opened to reveal the finished puppet show",
    },
    {
        "object": "the silver bell",
        "problem": "the bell used to call everyone together had disappeared",
        "crud": "a stripe of sticky red crud",
        "clue": "the stripe ended beside a wheel-shaped mark under the worktable",
        "cause": "a jar of red modeling clay had stuck to the brass beetle's wheel",
        "capture": "they made a soft cardboard corral and guided the beetle inside",
        "answer": "the beetle had carried the bell under the table while searching for a shiny place to rest",
        "ending": "the bell rang once, and every friend came running to the repaired table",
    },
    {
        "object": "the moon map",
        "problem": "the club's moon map was gone before their night-sky lesson",
        "crud": "a patch of gray chalk crud",
        "clue": "the chalk dust formed two short lines toward the locked supply chest",
        "cause": "the supply chest had tipped when the wind-up fox chased its own tail",
        "capture": "they worked together to stop the fox with a ribbon loop and a cushion",
        "answer": "the fox had nudged the map beneath the chest while circling the room",
        "ending": "the map returned to the wall, where its paper moon shone above the team",
    },
    {
        "object": "the captain's badge",
        "problem": "the badge for the teamwork captain was missing",
        "crud": "a blob of blue paint crud",
        "clue": "blue spots crossed the floor and disappeared behind an immobile tool chest",
        "cause": "the chest had been left blocking the path after painting time",
        "capture": "they lifted the loose badge with a ruler while keeping the chest safely still",
        "answer": "the badge had slid behind the chest when someone hurried past with wet paint",
        "ending": "the badge was pinned to the teamwork board, ready for a new captain",
    },
]

OPENINGS = [
    "{detective} noticed that {problem} in {room}.",
    "A mystery waited in {room}: {problem}, and {detective} was the first to see it.",
    "The workshop grew quiet when {detective} discovered that {problem}.",
    "Before the team could begin, {detective} found a strange problem: {problem}.",
]

DIALOGUES = [
    '"We should not blame anyone yet," {partner} said. "Let us follow the clues."',
    '"A good detective uses every set of eyes," {partner} said. "We can solve this together."',
    '"The mess is a clue, not an answer," {partner} reminded {detective}.',
    '"If something is immobile, we can study it safely," {partner} said. "Then we can test our guess."',
]

ACTIONS = [
    "{detective} held the lantern while {partner} measured the trail and checked each quiet corner",
    "the two friends compared the wheel marks, then searched beneath the immobile chest",
    "{detective} guarded the clue while {partner} gathered a cushion, ribbon, and empty crates",
    "the team divided the room into small squares and examined every patch of crud",
]

ENDINGS = [
    "At last, {ending}. The mystery had been solved by teamwork, not by a hurried guess.",
    "The case was closed: {ending}. {detective} and {partner} smiled at their careful work.",
    "Everyone cheered when {ending}. Even the odd crud now looked like a helpful clue.",
    "That was the answer to the whodunit. {ending}, and the team knew why each clue mattered.",
]


def valid_combo(params: StoryParams) -> bool:
    if not params.detective.strip() or not params.partner.strip():
        raise StoryError("detective and partner names must not be empty")
    if params.detective == params.partner:
        raise StoryError("detective and partner must be different people")
    if not params.room.strip():
        raise StoryError("room must not be empty")
    return True


def tell(params: StoryParams) -> World:
    valid_combo(params)
    case = CASES[params.clue_id % len(CASES)]
    world = World()
    detective = world.add(Entity(
        "detective", "child", params.detective,
        meters={"attention": 1.0, "mobility": 1.0},
        memes={"curiosity": 1.0, "worry": 0.3, "confidence": 0.5},
    ))
    partner = world.add(Entity(
        "partner", "child", params.partner,
        meters={"attention": 1.0, "mobility": 1.0},
        memes={"patience": 1.0, "trust": 1.0},
    ))
    suspect = world.add(Entity(
        "suspect", "object", params.suspect,
        meters={"mobility": 0.0},
        memes={"confusion": 0.5},
        props={"status": "immobile until examined"},
    ))
    missing = world.add(Entity(
        "missing", "object", case["object"],
        meters={"visibility": 0.0},
        memes={"importance": 1.0},
    ))
    world.facts.update(
        detective=detective,
        partner=partner,
        suspect=suspect,
        missing=missing,
        room=params.room,
        problem=case["problem"],
        crud=case["crud"],
        clue=case["clue"],
        cause=case["cause"],
        capture=case["capture"],
        answer=case["answer"],
        ending=case["ending"],
        resolved=False,
        teamwork=False,
    )

    world.say(OPENINGS[params.opening_id % len(OPENINGS)].format(
        detective=params.detective, problem=case["problem"], room=params.room,
    ))
    world.say(
        f"Near the empty place lay {case['crud']}, and {params.suspect} stood immobile beside it. "
        f"{params.detective} wondered whether {params.suspect} had taken {case['object']}."
    )
    detective.memes["worry"] += 0.5
    world.para()
    world.say(DIALOGUES[params.dialogue_id % len(DIALOGUES)].format(
        partner=params.partner, detective=params.detective,
    ))
    world.say(
        f'"Did you see {case["object"]}?" {params.detective} asked. '
        f'"I saw only the crud and the wheel marks," {params.partner} replied. '
        f'"Then we will look before we decide who did it."'
    )
    partner.memes["trust"] += 0.5
    world.para()
    world.say(f"The partners examined the room. They discovered that {case['clue']}.")
    world.say(f"Together, {ACTIONS[params.action_id % len(ACTIONS)]}.")
    world.say(
        f'"Ready?' {params.detective} asked. '
        f'"Together," {params.partner} answered. '
        f"Then {case['capture']}."
    )
    world.facts["teamwork"] = True
    detective.memes["confidence"] += 1.0
    partner.memes["trust"] += 1.0
    world.para()
    world.say(
        f"The capture revealed the truth: {case['answer']}. "
        f"{case['cause'].capitalize()}."
    )
    world.say(ENDINGS[params.ending_id % len(ENDINGS)].format(ending=case["ending"], detective=params.detective, partner=params.partner))
    world.say(
        f"{params.detective} learned that a whodunit is solved best when friends share clues, "
        f"move carefully, and use teamwork."
    )
    missing.meters["visibility"] = 1.0
    world.facts["resolved"] = True
    return world


ASP_RULES = r"""
clue_seen :- crud_present, wheel_mark_present.
team_ready :- clue_seen, partner_helped.
capture_safe :- team_ready, suspect_immobile.
case_solved :- capture_safe, answer_found.
#show clue_seen/0.
#show team_ready/0.
#show capture_safe/0.
#show case_solved/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("crud_present"),
        asp.fact("wheel_mark_present"),
        asp.fact("partner_helped"),
        asp.fact("suspect_immobile"),
        asp.fact("answer_found"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {str(atom).split("(", 1)[0] for atom in model}
    needed = {"clue_seen", "team_ready", "capture_safe", "case_solved"}
    if needed <= names:
        params = StoryParams("Luna", "Pip", "the blue cart", ROOMS[0])
        sample = generate(params)
        if sample.world and sample.world.facts["resolved"]:
            print("OK: Python and ASP both solve the teamwork capture case.")
            return 0
    print("MISMATCH: Python and ASP did not agree.")
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly whodunit in {f['room']} about {f['problem']}.",
        f"Use {f['crud']} and this clue: {f['clue']}.",
        "Show two friends using dialogue and teamwork to capture a moving suspect safely and discover the truth.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = f["detective"].label
    p = f["partner"].label
    suspect = f["suspect"].label
    return [
        QAItem(
            f"What mystery did {d} and {p} investigate?",
            f"They investigated why {f['missing'].label} was missing. The problem began when {f['problem']}.",
        ),
        QAItem(
            "What clue did the team find?",
            f"They found {f['crud']} and noticed that {f['clue']}.",
        ),
        QAItem(
            f"How did {d} and {p} capture the suspect?",
            f"They worked together carefully: {f['capture']}. They treated {suspect} as something to understand, not something to frighten.",
        ),
        QAItem(
            "Who caused the problem?",
            f"The answer was that {f['answer']}. The other important cause was that {f['cause']}.",
        ),
        QAItem(
            "What did the detectives learn?",
            f"They learned that teamwork solves a whodunit by sharing clues, checking evidence, and acting safely together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is crud?",
            "Crud is a messy bit of dirt or unwanted material that can leave a useful trail.",
        ),
        QAItem(
            "What does immobile mean?",
            "Immobile means unable to move or staying still.",
        ),
        QAItem(
            "What does capture mean in this story?",
            "Capture means safely stopping or enclosing something so it cannot roll away while people investigate.",
        ),
        QAItem(
            "Why is teamwork useful?",
            "Teamwork is useful because people can share attention, compare clues, and solve a problem more safely together.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A teamwork whodunit about crud, an immobile clue, and a gentle capture.")
    parser.add_argument("--detective", "--name", dest="detective")
    parser.add_argument("--partner")
    parser.add_argument("--suspect")
    parser.add_argument("--room")
    parser.add_argument("--seed", type=int, default=None)
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
    detective = getattr(args, "detective", None) or rng.choice(NAMES)
    partner = getattr(args, "partner", None) or rng.choice([x for x in PARTNERS if x != detective])
    suspect = getattr(args, "suspect", None) or rng.choice(SUSPECTS)
    room = getattr(args, "room", None) or rng.choice(ROOMS)
    params = StoryParams(
        detective=detective,
        partner=partner,
        suspect=suspect,
        room=room,
        clue_id=rng.randrange(len(CASES)),
        opening_id=rng.randrange(len(OPENINGS)),
        dialogue_id=rng.randrange(len(DIALOGUES)),
        action_id=rng.randrange(len(ACTIONS)),
        ending_id=rng.randrange(len(ENDINGS)),
        seed=getattr(args, "seed", None),
    )
    valid_combo(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label}: kind={entity.kind}; meters={entity.meters}; "
            f"memes={entity.memes}; props={entity.props}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program("#show case_solved/0."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("ASP model:")
        print(" ".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams("Luna", "Pip", "the blue cart", ROOMS[0], 0, 0, 0, 0, 0),
            StoryParams("Milo", "June", "the brass beetle", ROOMS[1], 1, 1, 1, 1, 1),
            StoryParams("Ivy", "Arlo", "the wind-up fox", ROOMS[2], 2, 2, 2, 2, 2),
            StoryParams("Theo", "Tess", "the little robot", ROOMS[3], 3, 3, 3, 3, 3),
        ]
        samples = [generate(params) for params in params_list]
    else:
        samples = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 20):
            rng = random.Random(base_seed + attempts)
            attempts += 1
            try:
                sample = generate(resolve_params(args, rng))
            except StoryError:
                continue
            if sample.story not in seen:
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
            header = f"### {sample.params.detective} and {sample.params.partner}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
