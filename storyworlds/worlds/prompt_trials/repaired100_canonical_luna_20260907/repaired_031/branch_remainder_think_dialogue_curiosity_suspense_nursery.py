#!/usr/bin/env python3
"""
Standalone story world: a nursery-rhyme branch, a remainder, and a thoughtful rescue.

A small child follows a branch-marked path in a moonlit garden. A remainder of
a rhyme is missing, and a curious friend must think aloud with the child before
the suspenseful dark can be solved.
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
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    child_name: str
    friend_name: str
    child_gender: str
    place: str = "moonlit_nursery_garden"
    branch: str = "willow_branch"
    remainder: str = "missing_rhyme"
    think: str = "listen_and_follow"
    scenario: str = "lantern_rhyme"
    opening_variant: int = 0
    dialogue_variant: int = 0
    ending_variant: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Setting:
    id: str
    label: str
    affords: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
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


SETTINGS = {
    "moonlit_nursery_garden": Setting(
        "moonlit_nursery_garden",
        "the moonlit nursery garden",
        {"branches", "riddles", "lanterns", "quiet_thinking"},
    ),
}

BRANCHES = {
    "willow_branch": {
        "label": "a silver willow branch",
        "clue": "three soft leaves pointing toward the pond",
        "sound": "swish",
    },
    "apple_branch": {
        "label": "a crooked apple branch",
        "clue": "a red apple shining beside the path",
        "sound": "tap",
    },
    "birch_branch": {
        "label": "a pale birch branch",
        "clue": "white bark striped like a little road",
        "sound": "rustle",
    },
}

REMAINDERS = {
    "missing_rhyme": {
        "label": "the remainder of a nursery rhyme",
        "line": "and home again by moonbeam light",
        "answer": "the last line was hidden under the lantern",
    },
    "lost_lullaby": {
        "label": "the remainder of a quiet lullaby",
        "line": "then sleepy stars tucked dreams in tight",
        "answer": "the last words were caught in a bird's nest",
    },
    "unfinished_riddle": {
        "label": "the remainder of a garden riddle",
        "line": "the answer waits where shadows meet",
        "answer": "the final clue was folded beneath a stone",
    },
}

THINKING_METHODS = {
    "listen_and_follow": {
        "label": "listen and follow",
        "action": "listened for the branch's small swish and followed the sound",
        "lesson": "careful listening can make a faint clue clear",
    },
    "count_the_clues": {
        "label": "count the clues",
        "action": "counted the leaves, steps, and stars before choosing a path",
        "lesson": "patient counting can keep a curious traveler from guessing",
    },
    "ask_and_notice": {
        "label": "ask and notice",
        "action": "asked a question, then noticed what the moonlight touched",
        "lesson": "a good question helps hidden details come into view",
    },
}

SCENARIOS = {
    "lantern_rhyme": {
        "trouble": "the nursery lantern went dark before the final rhyme could be read",
        "turn": "the missing remainder had been tucked beneath the branch that made the quietest sound",
        "result": "the lantern glowed again and the rhyme reached its gentle end",
    },
    "owl_path": {
        "trouble": "a tiny owl called from the wrong side of the hedge while the rhyme's remainder vanished",
        "turn": "the owl's call echoed only where the branch pointed toward the hidden verse",
        "result": "the owl flew home, and the last line fluttered safely into view",
    },
    "silver_key": {
        "trouble": "a silver key slipped into the dark grass just as the rhyme broke off",
        "turn": "the branch shadow made a thin arrow toward the key and the forgotten words",
        "result": "the key chimed in the lock, and the unfinished rhyme opened like a door",
    },
}

OPENINGS = [
    "In the nursery garden, where the moon made puddles shine, {child} heard a tiny rhyme.",
    "The stars peeped low above the garden wall when {child} and {friend} stepped out on tiptoe.",
    "Beside the nursery window, {child} found a branch-marked path that curled beneath the moon.",
    "A sleepy bell went ding-ding-ding, and {child} wondered what the garden wished to sing.",
]

DIALOGUES = [
    '{child} whispered, "Which way should we go?" {friend} answered, "Let us think, then follow what we know."',
    '"I am curious," said {child}. "So am I," said {friend}. "We will ask the dark a question, and watch for its reply."',
    '{friend} said, "Do not hurry when clues are small." {child} replied, "I will notice each one, tall or tiny, round or all."',
]

ENDINGS = [
    "They sang the whole rhyme softly, and the moon tucked the garden in silver.",
    "Then home they went, step by step, while the little branch waved good night.",
    "The nursery window shone warm and bright, and every curious heart felt light.",
    "The final word rang clear as a bell, and the sleepy garden knew all was well.",
]

GIRL_NAMES = ["Luna", "Mina", "Ivy", "Nora", "Pia"]
BOY_NAMES = ["Milo", "Theo", "Owen", "Finn", "Eli"]
FRIENDS = ["Pip", "Robin", "Tess", "Moss", "Bram"]


def valid_combo(place: str, branch: str, remainder: str, think: str) -> bool:
    return (
        place in SETTINGS
        and branch in BRANCHES
        and remainder in REMAINDERS
        and think in THINKING_METHODS
    )


def explain_rejection(place: str, branch: str, remainder: str, think: str) -> str:
    return (
        f"Invalid story choice: place={place!r}, branch={branch!r}, "
        f"remainder={remainder!r}, and think={think!r} do not form a complete "
        "nursery-garden mystery."
    )


def _pronoun(gender: str, case: str = "subject") -> str:
    table = {
        "girl": {"subject": "she", "object": "her", "possessive": "her"},
        "boy": {"subject": "he", "object": "him", "possessive": "his"},
    }
    return table.get(gender, table["girl"])[case]


def tell(params: StoryParams) -> World:
    if not valid_combo(params.place, params.branch, params.remainder, params.think):
        raise StoryError(
            explain_rejection(params.place, params.branch, params.remainder, params.think)
        )

    setting = SETTINGS[params.place]
    branch = BRANCHES[params.branch]
    remainder = REMAINDERS[params.remainder]
    thinking = THINKING_METHODS[params.think]
    scenario = SCENARIOS[params.scenario]

    world = World(setting)
    child = world.add(Entity(params.child_name, "character", params.child_name))
    friend = world.add(Entity(params.friend_name, "helper", params.friend_name))
    twig = world.add(Entity(params.branch, "branch", branch["label"]))
    verse = world.add(Entity(params.remainder, "riddle", remainder["label"]))
    lantern = world.add(Entity("lantern", "prop", "the nursery lantern"))

    child.memes["curiosity"] = 1.0
    friend.memes["patience"] = 1.0
    lantern.meters["brightness"] = 0.4
    twig.meters["clue_strength"] = 0.7
    verse.meters["completeness"] = 0.5

    world.say(
        OPENINGS[params.opening_variant % len(OPENINGS)].format(
            child=params.child_name, friend=params.friend_name
        )
    )
    world.say(
        f"{params.child_name} carried the nursery lantern, while {params.friend_name} "
        f"carried a pocket notebook for curious clues. A rhyme began: "
        f"“Follow the {branch['label']} where moonlit shadows bend...”"
    )
    world.say(
        f"But the verse stopped at the very middle. The {remainder['label']} was gone, "
        f"and {scenario['trouble']}."
    )

    world.para()
    world.say(
        DIALOGUES[params.dialogue_variant % len(DIALOGUES)].format(
            child=params.child_name, friend=params.friend_name
        )
    )
    world.say(
        f"They saw {branch['clue']}. The garden grew still, and suspense curled "
        f"around the hedge like a cat that would not purr."
    )
    world.say(
        f"“What if the branch is a sign?” {params.child_name} asked. "
        f"“Then we should think before we leap,” said {params.friend_name}."
    )
    world.fired.add(("curiosity", params.branch))
    world.facts["noticed_clue"] = branch["clue"]

    world.para()
    world.say(
        f"Together they {thinking['action']}. Under the branch they found a faint "
        f"silver mark and heard the sound “{branch['sound']}.”"
    )
    world.say(
        f"{scenario['turn']}. The {remainder['label']} lay beneath a curled leaf, "
        f"holding the words, “{remainder['line']}.”"
    )
    world.fired.add(("think", params.think))
    child.memes["understanding"] = 1.0
    friend.memes["helpfulness"] = 1.0
    verse.meters["completeness"] = 1.0
    lantern.meters["brightness"] = 1.0

    world.say(
        f"{params.child_name} read the line aloud. {params.friend_name} joined in, "
        f"and {scenario['result']}."
    )
    world.say(ENDINGS[params.ending_variant % len(ENDINGS)])
    world.fired.add(("resolve", params.remainder))

    world.facts.update(
        child=child,
        friend=friend,
        branch=twig,
        remainder=verse,
        lantern=lantern,
        branch_cfg=branch,
        remainder_cfg=remainder,
        thinking=thinking,
        scenario=scenario,
        resolved=True,
        clue=branch["clue"],
        final_line=remainder["line"],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a complete nursery rhyme story about a branch, a missing remainder, and a child who must think carefully.",
        f"Show how {f['child'].id} and {f['friend'].id} use dialogue and curiosity to follow {f['branch_cfg']['label']} without rushing.",
        f"Build suspense around the missing rhyme, then resolve it when the characters notice {f['clue']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"].id
    friend = f["friend"].id
    return [
        QAItem(
            f"What was missing from the nursery rhyme?",
            f"The remainder of the rhyme was missing. It was found beneath {f['branch_cfg']['label']}, where it held the words “{f['final_line']}.”",
        ),
        QAItem(
            f"Why did {child} and {friend} follow the branch?",
            f"They followed {f['branch_cfg']['label']} because they noticed {f['clue']}, which was a useful clue in the moonlit garden.",
        ),
        QAItem(
            f"How did {child} and {friend} solve the mystery?",
            f"They talked together, thought before choosing, and {f['thinking']['action']}. That led them to the hidden remainder.",
        ),
        QAItem(
            "What changed by the end?",
            f"The rhyme became complete, the lantern glowed brightly, and the suspense ended because the missing words were found.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a branch?", "A branch is a woody part that grows from the trunk of a tree."),
        QAItem("What is a remainder?", "A remainder is the part that is left over after something is used, divided, or completed."),
        QAItem("What does it mean to think?", "To think means to use your mind to notice, understand, remember, or decide."),
        QAItem("What is curiosity?", "Curiosity is the wish to learn more about something unfamiliar or interesting."),
        QAItem("What is suspense?", "Suspense is the wondering feeling that grows while we wait to discover what will happen."),
        QAItem("Why is dialogue useful in a story?", "Dialogue lets characters share clues, feelings, and decisions with one another."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
branch(B) :- branch_choice(B).
remainder(R) :- remainder_choice(R).
think(T) :- think_choice(T).
complete_story(P,B,R,T) :-
    place(P), branch(B), remainder(R), think(T),
    curious, dialogue, suspense, resolved.
"""


def asp_facts() -> str:
    import asp

    lines = [asp.fact("place", key) for key in SETTINGS]
    lines += [asp.fact("branch_choice", key) for key in BRANCHES]
    lines += [asp.fact("remainder_choice", key) for key in REMAINDERS]
    lines += [asp.fact("think_choice", key) for key in THINKING_METHODS]
    lines += [
        asp.fact("curious"),
        asp.fact("dialogue"),
        asp.fact("suspense"),
        asp.fact("resolved"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show complete_story/4."))
    return sorted(set(asp.atoms(model, "complete_story")))


def asp_verify() -> int:
    py = sorted(
        (place, branch, remainder, think)
        for place in SETTINGS
        for branch in BRANCHES
        for remainder in REMAINDERS
        for think in THINKING_METHODS
    )
    cl = asp_valid_combos()
    if py == cl:
        for params in curated_params():
            generate(params)
        print(f"OK: clingo gate matches Python gate ({len(py)} combos); stories exercised.")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("python:", py)
    print("clingo:", cl)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nursery-rhyme story world about a branch, a remainder, and thinking."
    )
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--branch", choices=BRANCHES)
    parser.add_argument("--remainder", choices=REMAINDERS)
    parser.add_argument("--think", choices=THINKING_METHODS)
    parser.add_argument("--scenario", choices=SCENARIOS)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_name = args.friend or rng.choice([n for n in FRIENDS if n != child_name])
    branch = args.branch or rng.choice(list(BRANCHES))
    remainder = args.remainder or rng.choice(list(REMAINDERS))
    think = args.think or rng.choice(list(THINKING_METHODS))
    scenario = args.scenario or rng.choice(list(SCENARIOS))
    if not valid_combo("moonlit_nursery_garden", branch, remainder, think):
        raise StoryError(explain_rejection("moonlit_nursery_garden", branch, remainder, think))
    return StoryParams(
        child_name=child_name,
        friend_name=friend_name,
        child_gender=gender,
        branch=branch,
        remainder=remainder,
        think=think,
        scenario=scenario,
        opening_variant=rng.randrange(len(OPENINGS)),
        dialogue_variant=rng.randrange(len(DIALOGUES)),
        ending_variant=rng.randrange(len(ENDINGS)),
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:18} ({entity.kind:10}) meters={meters} memes={memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def curated_params() -> list[StoryParams]:
    return [
        StoryParams(
            child_name="Luna",
            friend_name="Pip",
            child_gender="girl",
            branch="willow_branch",
            remainder="missing_rhyme",
            think="listen_and_follow",
            scenario="lantern_rhyme",
        ),
        StoryParams(
            child_name="Milo",
            friend_name="Robin",
            child_gender="boy",
            branch="apple_branch",
            remainder="lost_lullaby",
            think="count_the_clues",
            scenario="owl_path",
        ),
        StoryParams(
            child_name="Ivy",
            friend_name="Moss",
            child_gender="girl",
            branch="birch_branch",
            remainder="unfinished_riddle",
            think="ask_and_notice",
            scenario="silver_key",
        ),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show complete_story/4."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in curated_params()]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
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
            header = (
                f"### {sample.params.child_name}: "
                f"{sample.params.branch}, {sample.params.remainder}"
            )
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
