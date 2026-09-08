#!/usr/bin/env python3
"""
A small folk-tale storyworld about Dodo, a shy bird, and the friendship that
grows when two neighbors solve a problem together.
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

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "child":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    id: str
    place: str
    affords: set[str]


@dataclass(frozen=True)
class Tale:
    title: str
    problem: str
    warning: str
    first_action: str
    consequence: str
    clue: str
    repair: str
    lesson: str
    ending: str
    saying: str


SETTINGS = {
    "grove": Setting(
        id="grove",
        place="the greenwood grove",
        affords={"gather", "share"},
    )
}

ACTIVITIES = {
    "gather": {"label": "gathering berries", "tag": "food"},
    "share": {"label": "sharing food", "tag": "kindness"},
}

TALES = [
    Tale(
        title="The Dodo and the Empty Basket",
        problem="Dodo found a basket of golden berries beside the old kapok tree.",
        warning="the basket was not his, and its owner might be searching for it",
        first_action="carried the basket toward his nest without asking",
        consequence="The basket caught on a thorn branch, and the berries rolled into the ferns.",
        clue="a blue thread on the handle matched the blue shawl of a small girl nearby",
        repair="gathered every berry he could find and carried the basket back",
        lesson="friendship begins when we return what is not ours and help repair our mistakes",
        ending="The girl and Dodo sat beneath the kapok tree and shared the berries from one clean basket",
        saying="A returned basket makes a friendship grow",
    ),
    Tale(
        title="The Dodo and the Rainy Path",
        problem="Dodo knew a dry path through the grove, but a young girl named Luma did not.",
        warning="the stepping stones were slippery after the rain",
        first_action="hurried ahead without telling Luma where to place her feet",
        consequence="Luma slipped into a puddle, and the little bundle she carried became wet",
        clue="the safest stones were marked by tiny white shells along the bank",
        repair="showed Luma each shell and helped her carry the bundle beneath a broad leaf",
        lesson="a friend does not merely go first; a friend makes the way safer for both",
        ending="Dodo and Luma crossed the shining path together, leaving two rows of footprints",
        saying="A careful guide makes two feet brave",
    ),
    Tale(
        title="The Dodo and the Last Mango",
        problem="Only one ripe mango hung low on a branch after a long dry season.",
        warning="the mango belonged to the whole grove, not to the strongest beak",
        first_action="pulled the fruit down and hid it under a leaf",
        consequence="A curious monkey found the hiding place and carried the mango away",
        clue="mango leaves led from Dodo's hiding place to the monkey's hollow",
        repair="admitted what he had done and invited Luma to help find a fair share of fruit",
        lesson="keeping everything for oneself can lose even the little one has",
        ending="The grove's neighbors divided the next basket of fruit, and Dodo was given the first piece",
        saying="A shared bite is sweeter than a hidden feast",
    ),
]


@dataclass
class StoryParams:
    setting: str
    activity: str
    name: str
    friend: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def valid_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.activity not in ACTIVITIES:
        raise StoryError(f"Unknown activity: {params.activity}")
    if not params.name.strip() or not params.friend.strip():
        raise StoryError("Both Dodo and the friend need names.")
    if params.name.strip().lower() == params.friend.strip().lower():
        raise StoryError("Dodo and the friend must be different characters.")


def build_story(params: StoryParams) -> World:
    valid_params(params)
    world = World(SETTINGS[params.setting])
    seed = params.seed if params.seed is not None else 0
    tale = TALES[seed % len(TALES)]

    dodo = world.add(Entity("dodo", "bird", params.name))
    friend = world.add(Entity("friend", "child", params.friend))
    dodo.meters["curiosity"] = 1.0
    dodo.memes["loneliness"] = 1.0

    world.facts.update(tale=tale, dodo=dodo, friend=friend)
    world.say(
        f"In {world.setting.place}, where the ferns whispered to the moon, "
        f"{dodo.label} the dodo lived alone. {tale.problem}"
    )
    world.say(
        f"{dodo.label} wanted to be noticed, but {tale.warning}. "
        f"Still, he {tale.first_action}."
    )

    world.para()
    world.say(
        f"\"Wait, {dodo.label},\" called {friend.label}. "
        f"\"May I help you understand what happened?\""
    )
    world.say(
        f"\"I thought I could manage by myself,\" said {dodo.label}. "
        f"\"Then please show me what you saw,\" replied {friend.label}."
    )
    world.say(f"{tale.consequence} {dodo.label} lowered his head.")
    world.say(
        f"Together they looked closely. They noticed that {tale.clue}. "
        f"The small clue showed {dodo.label} what had truly gone wrong."
    )

    world.para()
    world.say(
        f"{dodo.label} said, \"I am sorry. I will make this right.\" "
        f"He {tale.repair}, while {friend.label} helped without scolding."
    )
    dodo.memes["loneliness"] = 0.0
    dodo.memes["friendship"] = 1.0
    dodo.meters["trust"] = 1.0
    friend.memes["friendship"] = 1.0
    world.fired.add("mistake_repaired")
    world.say(
        f"Afterward, {dodo.label} understood that {tale.lesson}. "
        f"{tale.ending}."
    )
    world.say(f"The old trees seemed to nod. \"{tale.saying},\" they rustled.")

    world.facts.update(
        warning=tale.warning,
        consequence=tale.consequence,
        clue=tale.clue,
        repair=tale.repair,
        lesson=tale.lesson,
        ending=tale.ending,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    tale: Tale = world.facts["tale"]
    dodo: Entity = world.facts["dodo"]
    friend: Entity = world.facts["friend"]
    return [
        f'Write a child-friendly folk tale titled "{tale.title}" about {dodo.label} the dodo and {friend.label}.',
        f"Show how {dodo.label} makes a mistake, listens to {friend.label}, and repairs it through friendship.",
        f"End with this changed image: {tale.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    tale: Tale = world.facts["tale"]
    dodo: Entity = world.facts["dodo"]
    friend: Entity = world.facts["friend"]
    return [
        QAItem(
            question=f"What mistake did {dodo.label} make?",
            answer=f"{dodo.label} {tale.first_action}. That choice caused the trouble described in the tale.",
        ),
        QAItem(
            question=f"What did {friend.label} say before helping?",
            answer=f"{friend.label} asked {dodo.label} to wait and explain what had happened so they could understand it together.",
        ),
        QAItem(
            question="What clue helped explain the problem?",
            answer=f"They noticed that {tale.clue}. The clue connected the trouble to the earlier choice.",
        ),
        QAItem(
            question=f"How did {dodo.label} repair the mistake?",
            answer=f"{dodo.label} {tale.repair}. {friend.label} helped without scolding.",
        ),
        QAItem(
            question="What did the two friends learn?",
            answer=f"They learned that {tale.lesson}. Their honest teamwork changed loneliness into friendship.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a dodo?",
        answer="A dodo was a large, flightless bird that once lived on the island of Mauritius.",
    ),
    QAItem(
        question="Why can friendship help solve a problem?",
        answer="Friendship can help solve a problem because trusted friends listen, share ideas, and work together carefully.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:8} ({entity.kind:5}) meters={meters} memes={memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    return [(setting, activity) for setting in SETTINGS for activity in ACTIVITIES
            if activity in SETTINGS[setting].affords]


ASP_RULES = r"""
valid(S,A) :- setting(S), activity(A), affords(S,A).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for activity in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, activity))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    try:
        clingo_rows = set(asp_valid_combos())
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    if py != clingo_rows:
        print("MISMATCH:")
        print("python only:", sorted(py - clingo_rows))
        print("clingo only:", sorted(clingo_rows - py))
        return 1
    for params in (
        StoryParams("grove", "gather", "Dodo", "Luma", 0),
        StoryParams("grove", "share", "Dodo", "Luma", 1),
        StoryParams("grove", "gather", "Dodo", "Luma", 2),
    ):
        sample = generate(params)
        if not sample.story or len(sample.story_qa) < 3:
            print("Generated-story verification failed.")
            return 1
    print(f"OK: ASP and Python agree on {len(py)} combinations; stories pass.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A folk tale about a dodo, friendship, and repairing a mistake."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--activity", choices=ACTIVITIES)
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or "grove"
    activity = args.activity or rng.choice(sorted(ACTIVITIES))
    name = args.name or "Dodo"
    friend = args.friend or rng.choice(["Luma", "Tavi", "Nia"])
    params = StoryParams(setting, activity, name, friend)
    valid_params(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        try:
            rows = asp_valid_combos()
        except Exception as exc:
            raise SystemExit(f"ASP mode unavailable: {exc}")
        print(f"{len(rows)} compatible combinations:")
        for row in rows:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("grove", "gather", "Dodo", "Luma", 0),
            StoryParams("grove", "share", "Dodo", "Tavi", 1),
            StoryParams("grove", "gather", "Dodo", "Nia", 2),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < max(args.n, 1) and attempts < max(args.n * 20, 20):
            seed = base_seed + attempts
            attempts += 1
            try:
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
            except StoryError:
                continue
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
