#!/usr/bin/env python3
"""
A small mystery storyworld about remembering that a haven belongs to everyone.
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
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    friend_name: str
    caretaker_name: str
    seed: Optional[int] = None
    case_id: int = 0
    opening_id: int = 0
    clue_id: int = 0
    dialogue_id: int = 0
    ending_id: int = 0


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


NAMES = ["Luna", "Milo", "Nia", "Theo", "Ada", "Pip"]
FRIENDS = ["Iris", "Owen", "Mara", "Ben", "Suki", "Jude"]
CARETAKERS = ["Ms. Vale", "Aunt Rose", "Mr. Finn", "Grandma Jo"]

CASES = [
    {
        "place": "the patio",
        "mystery": "the brass haven key had vanished from its hook",
        "clue": "a crescent of chalk dust beside the rain barrel",
        "danger": "the wind was pushing dark clouds toward the open yard",
        "twist": "the key had not been stolen at all; it was tucked inside the old bench so the frightened garden cat could shelter without being disturbed",
        "action": "followed the chalk dust to the bench and found the key beneath a loose slat",
        "resolution": "they opened the little haven before the rain began and left the door wide enough for the cat",
        "image": "The patio lantern glowed beside the open haven while rain whispered on the roof.",
        "lesson": "bravery is not rushing into danger; it is looking carefully and protecting a smaller, quieter life",
    },
    {
        "place": "the patio",
        "mystery": "the welcome bell for the neighborhood haven rang once and then disappeared",
        "clue": "three tiny muddy prints leading toward a stack of flowerpots",
        "danger": "a new child might arrive and think the haven was closed",
        "twist": "a shy child had hidden the bell after hearing a loud crash, hoping to make the haven feel calm",
        "action": "knelt by the flowerpots, spoke softly, and invited the child to return the bell when ready",
        "resolution": "they rehung the bell with a gentle ribbon and made a quiet signal for anyone who disliked loud sounds",
        "image": "The ribbon moved in the evening breeze, making the haven easy to find but never noisy.",
        "lesson": "a moral choice can make room for someone whose courage looks quiet",
    },
    {
        "place": "the patio",
        "mystery": "the painted sign that said EVERYONE MAY REST had been turned facedown",
        "clue": "fresh blue paint on the edge of a wheelbarrow",
        "danger": "people might believe the haven belonged only to the strongest children",
        "twist": "the sign had been turned around by the caretaker during a storm, but nobody remembered to turn it back",
        "action": "carried the sign to the wall and asked before changing the storm-bent nails",
        "resolution": "they repaired the sign together and added a second line: REST, ASK, AND HELP",
        "image": "The sign shone above the patio, its words clear beneath a row of warm lights.",
        "lesson": "remembering a shared promise is a form of bravery when silence could let unfairness grow",
    },
]

OPENINGS = [
    "Luna liked mysteries that left muddy clues instead of scary shadows.",
    "The patio was quiet after breakfast, but Luna knew quiet places often kept important secrets.",
    "At the edge of the garden stood a small haven where anyone could pause, breathe, and feel safe.",
    "Luna arrived with a notebook, a red pencil, and one promise: she would not guess before she looked.",
]

DIALOGUES = [
    '"I am afraid of finding a hard answer," Luna admitted. "Then we will face the answer gently," said {friend}."',
    '"Should we wait for an adult?" asked {friend}. Luna nodded. "Yes, and we can still notice what the clues are telling us."',
    '"A haven is not truly safe if we leave someone out," Luna said. "{friend} replied, "Then our search must protect people as well as solve the mystery."',
    '"What if I am wrong?" asked Luna. "{friend} smiled. "Being careful matters more than pretending to know everything."',
]

ENDING_LEADS = [
    "By sunset,",
    "When the first drops began to fall,",
    "At the end of the careful search,",
    "That evening,",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A patio mystery about memory, bravery, and a shared haven.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--caretaker", choices=CARETAKERS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    friend_choices = [item for item in FRIENDS if item != name]
    friend = args.friend or rng.choice(friend_choices)
    if friend == name:
        raise StoryError("The investigator and friend must have different names.")
    return StoryParams(
        name=name,
        friend_name=friend,
        caretaker_name=args.caretaker or rng.choice(CARETAKERS),
        case_id=rng.randrange(len(CASES)),
        opening_id=rng.randrange(len(OPENINGS)),
        clue_id=rng.randrange(3),
        dialogue_id=rng.randrange(len(DIALOGUES)),
        ending_id=rng.randrange(len(ENDING_LEADS)),
    )


def validate_params(params: StoryParams) -> None:
    if not params.name.strip() or not params.friend_name.strip():
        raise StoryError("Names must not be empty.")
    if params.name == params.friend_name:
        raise StoryError("The investigator and friend must have different names.")
    if not 0 <= params.case_id < len(CASES):
        raise StoryError("case_id is outside the available mystery cases.")


def tell(params: StoryParams) -> World:
    validate_params(params)
    case = CASES[params.case_id]
    world = World()

    luna = world.add(Entity("investigator", "character", params.name))
    friend = world.add(Entity("friend", "character", params.friend_name))
    caretaker = world.add(Entity("caretaker", "character", params.caretaker_name))
    patio = world.add(Entity("patio", "place", "patio"))
    haven = world.add(Entity("haven", "place", "haven"))
    clue = world.add(Entity("clue", "thing", case["clue"]))

    world.facts.update(
        investigator=luna,
        friend=friend,
        caretaker=caretaker,
        patio=patio,
        haven=haven,
        clue=clue,
        case=case,
        resolved=False,
    )

    luna.memes["curiosity"] = 1.0
    friend.memes["care"] = 1.0
    patio.meters["distance"] = 4.0
    haven.memes["welcome"] = 1.0

    world.say(OPENINGS[params.opening_id % len(OPENINGS)])
    world.say(
        f"{params.name} met {params.friend_name} on the patio beside a small haven where "
        f"neighbors could rest. The morning's mystery was simple to state but hard to solve: "
        f"{case['mystery']}."
    )
    world.say(
        f"{params.caretaker_name} had asked them to remember that the haven belonged to everyone, "
        f"especially anyone who needed a quiet place."
    )

    world.para()
    world.say(f"The sky darkened, and {case['danger']}.")
    world.say(
        f"Near the haven, {case['clue']}. {params.name} wanted to run toward the first explanation, "
        f"but {params.friend_name} pointed to the notebook and asked them to compare every mark."
    )
    luna.meters["search"] = 1.0
    friend.meters["careful_observation"] = 1.0
    world.say(
        DIALOGUES[params.dialogue_id % len(DIALOGUES)].format(friend=params.friend_name)
    )

    world.para()
    world.say(
        f"They searched without breaking anything. {params.name} {case['action']}. "
        f"The discovery brought a twist: {case['twist']}."
    )
    luna.memes["bravery"] = 1.0
    friend.memes["trust"] = 1.0
    haven.memes["protected"] = 1.0
    world.say(
        f"Instead of blaming anyone, they called {params.caretaker_name} and explained what they had seen. "
        f"Together, they {case['resolution']}."
    )
    world.say(f"The mystery was solved because {case['lesson']}.")

    world.para()
    world.facts["resolved"] = True
    world.facts["twist"] = case["twist"]
    world.facts["action"] = case["action"]
    world.facts["resolution"] = case["resolution"]
    world.say(
        f"{ENDING_LEADS[params.ending_id % len(ENDING_LEADS)]} "
        f"the patio became calm again. {case['image']}"
    )
    world.say(
        f"{params.name} wrote the final clue in the notebook: remember who the haven is for, "
        f"and let that memory guide the brave choice."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    return [
        f"Write a child-facing mystery on a patio where {case['mystery']}.",
        f"Include a haven, a brave but careful search, and the clue {case['clue']}.",
        "Reveal a gentle twist showing that remembering a moral value changes the ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    case = facts["case"]
    investigator = facts["investigator"].label
    friend = facts["friend"].label
    return [
        QAItem(
            question="Where did the mystery happen?",
            answer=f"It happened on the patio, around a small haven where people could rest safely.",
        ),
        QAItem(
            question="What problem did the children investigate?",
            answer=f"They investigated why {case['mystery']}.",
        ),
        QAItem(
            question="What clue helped them?",
            answer=f"They noticed {case['clue']}, then compared it with the other details instead of guessing.",
        ),
        QAItem(
            question="How did the conversation change what they did?",
            answer=f"{investigator} and {friend} decided to observe carefully, avoid blame, and ask {facts['caretaker'].label} for help.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {case['twist']}.",
        ),
        QAItem(
            question="What moral value did the ending show?",
            answer=f"It showed that {case['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a patio?",
            answer="A patio is a paved or outdoor area beside a home or building where people can sit or gather.",
        ),
        QAItem(
            question="What does it mean to remember something?",
            answer="To remember means to keep information or an experience in your mind and bring it back when needed.",
        ),
        QAItem(
            question="What is a haven?",
            answer="A haven is a safe, peaceful place where someone can rest or receive protection.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is choosing a careful or kind action even when you feel worried or afraid.",
        ),
        QAItem(
            question="What is a twist in a mystery?",
            answer="A twist is a surprising change in what the reader thought was happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"{entity.id}: {entity.label} {' '.join(details)}".rstrip())
    lines.append(f"resolved: {world.facts.get('resolved', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(patio).
seed_word(remember).
seed_word(haven).
feature(moral_value).
feature(bravery).
feature(twist).
valid_story(patio, remember, haven) :-
    setting(patio),
    seed_word(remember),
    seed_word(haven),
    feature(moral_value),
    feature(bravery),
    feature(twist).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "patio"),
            asp.fact("seed_word", "remember"),
            asp.fact("seed_word", "haven"),
            asp.fact("feature", "moral_value"),
            asp.fact("feature", "bravery"),
            asp.fact("feature", "twist"),
        ]
    )


def asp_program(show: str = "#show valid_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    observed = set(asp.atoms(model, "valid_story"))
    expected = {("patio", "remember", "haven")}
    if observed != expected:
        print("MISMATCH")
        print("ASP:", sorted(observed))
        print("PY :", sorted(expected))
        return 1

    checks = [
        StoryParams(name="Luna", friend_name="Iris", caretaker_name="Ms. Vale"),
        StoryParams(name="Theo", friend_name="Mara", caretaker_name="Aunt Rose", case_id=1),
        StoryParams(name="Ada", friend_name="Jude", caretaker_name="Mr. Finn", case_id=2),
    ]
    for params in checks:
        sample = generate(params)
        if not sample.story or not sample.world.facts["resolved"]:
            print("MISMATCH: generated story did not resolve")
            return 1
        if "patio" not in sample.story or "haven" not in sample.story:
            print("MISMATCH: required setting words missing")
            return 1

    print("OK: ASP parity and generated-story checks passed.")
    return 0


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


CURATED = [
    StoryParams(name="Luna", friend_name="Iris", caretaker_name="Ms. Vale", case_id=0),
    StoryParams(name="Milo", friend_name="Mara", caretaker_name="Aunt Rose", case_id=1),
    StoryParams(name="Ada", friend_name="Jude", caretaker_name="Mr. Finn", case_id=2),
]


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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        print(asp_program())
        print("models:", len(asp.solve(asp_program(), models=0)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
