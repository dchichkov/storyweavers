#!/usr/bin/env python3
"""
A small nursery-rhyme world about continuing bravely through a quarrel.

Luna and Pip must carry a silver bell across a moonlit bridge. A missing
ribbon creates suspense, a sharp disagreement creates conflict, and an honest
conversation restores their teamwork.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    phrase: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    held_by: Optional[str] = None
    owner: Optional[str] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


@dataclass
class StoryParams:
    luna_name: str
    friend_name: str
    bell: str = "silver bell"
    setting: str = "the moonlit bridge"
    seed: Optional[int] = None


NAMES = ["Luna", "Pip", "Milo", "Nell", "Clover", "Toby"]
BELLS = {
    "silver bell": "a little silver bell",
    "brass bell": "a bright brass bell",
    "blue bell": "a tiny blue bell",
}
SETTINGS = ["the moonlit bridge", "the quiet lane", "the hilltop gate"]


@dataclass(frozen=True)
class Arc:
    opening: str
    suspense: str
    conflict: str
    friend_line: str
    reconciliation: str
    ending: str


ARCS = (
    Arc(
        "Luna and Pip set out at night with {bell_phrase} tucked in a woolly sack.",
        "Halfway across, the red ribbon tied to the bell slipped loose and vanished in the dark.",
        '"You walked too fast!" cried Luna. "You should have watched the sack!"',
        '"I was watching the shadows," said Pip. "Let us stop blaming and search together."',
        "Luna took a breath. Pip lifted the lantern, and Luna felt beneath the bridge rail until her paw found the ribbon.",
        "They tied the ribbon twice and crossed on, ding-ding, with their friendship bright beneath the moon.",
    ),
    Arc(
        "In {setting}, Luna and Pip promised to carry {bell_phrase} to the sleepy village.",
        "A cold wind blew the bell from its hook, and its soft sound rolled toward the fog.",
        '"We must turn back!" Luna cried. "No, we must continue!" Pip answered, though his knees trembled.',
        '"We can continue carefully," said Pip. "You listen for the ring while I follow the path."',
        "Luna heard one faint ding behind a stone. Pip reached it first, and Luna thanked him for staying calm.",
        "Together they brought the bell home, where every window glowed like a friendly star.",
    ),
    Arc(
        "Before the moon climbed high, Luna and Pip began a rhyme with {bell_phrase}.",
        "The bridge boards creaked, and the bell stopped ringing. No one could see why.",
        '"You hid the bell from me!" Luna said. Pip looked hurt and held the sack open wide.',
        '"I did not hide it," said Pip. "Let us tell the truth before the dark tells a scarier tale."',
        "They checked the sack together and found the bell caught in a fold. Luna apologized, and Pip smiled.",
        "The bell rang once more, and the two friends continued in step: tap, tap, ding.",
    ),
)


def build_world(params: StoryParams) -> World:
    if params.luna_name == params.friend_name:
        raise StoryError("Luna and friend must have different names.")
    if params.bell not in BELLS:
        raise StoryError(f"Unknown bell: {params.bell}")
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")

    world = World()
    luna = world.add(Entity(
        id=params.luna_name, kind="character", type="child",
        label="Luna", meters={"courage": 1.0, "calm": 0.6},
        memes={"worry": 0.2, "friendship": 1.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name, kind="character", type="friend",
        label="friend", meters={"courage": 0.8, "calm": 0.8},
        memes={"worry": 0.2, "friendship": 1.0},
    ))
    bell = world.add(Entity(
        id="bell", kind="thing", type="bell", label=params.bell,
        phrase=BELLS[params.bell], owner=luna.id, held_by=luna.id,
        meters={"safety": 1.0},
    ))

    arc = ARCS[(params.seed or 0) % len(ARCS)]
    values = {
        "bell_phrase": bell.phrase,
        "setting": params.setting,
    }

    world.say(arc.opening.format(**values))
    world.say(f"The moon hummed, “Continue, continue,” while {luna.id} and {friend.id} walked carefully.")
    world.para()
    world.say(arc.suspense)
    luna.memes["worry"] += 0.8
    friend.memes["worry"] += 0.5
    world.say(arc.conflict)
    world.say(arc.friend_line)
    world.para()
    world.say("For a moment the path seemed longer than a song, and neither friend knew what to do.")
    world.say(arc.reconciliation)
    luna.meters["calm"] += 0.5
    friend.meters["calm"] += 0.4
    luna.memes["friendship"] += 0.7
    friend.memes["friendship"] += 0.7
    bell.held_by = None
    world.say("They remembered that a quarrel may be loud, but listening can make a quiet door.")
    world.say(arc.ending)

    world.facts.update(
        luna=luna,
        friend=friend,
        bell=bell,
        setting=params.setting,
        arc=arc,
        suspense=arc.suspense,
        conflict=arc.conflict,
        friend_line=arc.friend_line,
        reconciliation=arc.reconciliation,
        ending=arc.ending,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    luna: Entity = f["luna"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    bell: Entity = f["bell"]  # type: ignore[assignment]
    return [
        f"Write a Nursery Rhyme about {luna.id} and {friend.id} who continue through suspense and make peace.",
        f"Tell a child-friendly story in {f['setting']} involving {bell.phrase}, conflict, and reconciliation.",
        f"Use the word continue in a rhyming tale where two friends solve a frightening problem together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    luna: Entity = f["luna"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    bell: Entity = f["bell"]  # type: ignore[assignment]
    return [
        QAItem(
            question="Who carried the bell?",
            answer=f"{luna.id} and {friend.id} carried {bell.phrase} together.",
        ),
        QAItem(
            question="What suspenseful problem happened?",
            answer=str(f["suspense"]),
        ),
        QAItem(
            question="What caused the conflict?",
            answer=str(f["conflict"]),
        ),
        QAItem(
            question=f"How did {luna.id} and {friend.id} reconcile?",
            answer=str(f["reconciliation"]),
        ),
        QAItem(
            question="What shows that they continued bravely?",
            answer=str(f["ending"]),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does continue mean?",
            answer="Continue means to keep going instead of stopping.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen next when something is uncertain.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is making peace after a disagreement by listening, apologizing, and finding a way forward.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Nursery-rhyme world of suspense, conflict, and reconciliation.")
    parser.add_argument("--luna-name")
    parser.add_argument("--friend-name")
    parser.add_argument("--bell", choices=list(BELLS))
    parser.add_argument("--setting", choices=SETTINGS)
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
    luna = args.luna_name or "Luna"
    choices = [name for name in NAMES if name != luna]
    return StoryParams(
        luna_name=luna,
        friend_name=args.friend_name or rng.choice(choices),
        bell=args.bell or rng.choice(list(BELLS)),
        setting=args.setting or rng.choice(SETTINGS),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: type={entity.type}, meters={entity.meters}, "
            f"memes={entity.memes}, held_by={entity.held_by}, owner={entity.owner}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    sections = [
        ("== prompts ==", sample.prompts),
        ("== story qa ==", sample.story_qa),
        ("== world qa ==", sample.world_qa),
    ]
    lines: list[str] = []
    for title, items in sections:
        lines.append(title)
        for item in items:
            if isinstance(item, QAItem):
                lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
            else:
                lines.append(str(item))
        lines.append("")
    return "\n".join(lines).rstrip()


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
character(X) :- luna(X).
character(X) :- friend(X).
mission(L,F,B) :- luna(L), friend(F), bell(B), L != F.
continues(L,F) :- mission(L,F,_).
reconciles(L,F) :- continues(L,F).
#show reconciles/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name in NAMES:
        lines.append(asp.fact("luna", name))
        lines.append(asp.fact("friend", name))
    for bell in BELLS:
        lines.append(asp.fact("bell", bell.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str = "#show reconciles/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        models = asp.solve(asp_program(), models=1)
        if not models:
            print("ASP verification failed.")
            return 1
        for seed in range(6):
            sample = generate(StoryParams("Luna", "Pip", seed=seed))
            if "continue" not in sample.story.lower():
                print("Python verification failed: missing continue.")
                return 1
        print("OK: ASP twin and generated stories verified.")
        return 0
    except Exception as exc:
        print(f"ASP verification failed: {exc}")
        return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import asp
            print(json.dumps([str(atom) for atom in asp.one_model(asp_program())], indent=2))
        except Exception as exc:
            raise StoryError(f"ASP mode requires a working clingo installation: {exc}") from exc
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, bell in enumerate(BELLS):
            params = StoryParams(
                luna_name="Luna",
                friend_name=NAMES[(index + 1) % len(NAMES)],
                bell=bell,
                setting=SETTINGS[index % len(SETTINGS)],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        for index in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [sample.to_dict() for sample in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
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
