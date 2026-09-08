#!/usr/bin/env python3
"""
A gentle rhyming storyworld about a nightmare, a warning, and a bad ending.
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    lines: list[str] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, line: str) -> None:
        if line:
            self.lines.append(line)

    def render(self) -> str:
        return "\n\n".join(self.lines)


NIGHTMARES = (
    {
        "name": "the Crooked Crow",
        "warning": "a black feather trembled by the bed",
        "danger": "the crow stole the moon from the sky",
        "help": "a silver bell",
        "ending": "The bell lay cracked, and the moon stayed gone until dawn.",
    },
    {
        "name": "the Growling Gray Fog",
        "warning": "cold mist curled beneath the door",
        "danger": "the fog swallowed every friendly light",
        "help": "a bright candle",
        "ending": "The candle sputtered out, and the room filled up with gray.",
    },
    {
        "name": "the Giant Clock",
        "warning": "the bedside clock ticked backward",
        "danger": "the clock locked the child inside one endless hour",
        "help": "a wooden key",
        "ending": "The key bent in the lock, and the ticking would not cease.",
    },
    {
        "name": "the Hungry Shadow",
        "warning": "a long shadow reached past the rug",
        "danger": "the shadow gobbled every happy dream",
        "help": "a paper star",
        "ending": "The star tore in two, and no bright dream came back.",
    },
)

SETTINGS = (
    "a small room beneath a round moon",
    "a quiet cottage where the rain tapped light",
    "an attic bedroom under a blanket of night",
    "a warm house beside a dark and whispering lane",
)

CHILDREN = (
    ("Luna", "girl"),
    ("Milo", "boy"),
    ("Ari", "child"),
    ("Nia", "girl"),
)

COMPANIONS = (
    ("Pip", "a small blue dog"),
    ("Moss", "a patient green frog"),
    ("Tess", "a brave little sister"),
    ("Odo", "a sleepy orange cat"),
)

ENDINGS = (
    "The night grew still, but the broken warning stayed near.",
    "By morning the room was bright, though the dream had left a mark.",
    "The stars kept quiet, and the child wished the warning had been heard.",
)


@dataclass
class StoryParams:
    seed: int | None = None
    child_name: str = "Luna"
    companion_name: str = "Pip"
    companion_kind: str = "a small blue dog"
    setting: str = SETTINGS[0]
    nightmare_name: str = NIGHTMARES[0]["name"]
    warning: str = NIGHTMARES[0]["warning"]
    danger: str = NIGHTMARES[0]["danger"]
    help_object: str = NIGHTMARES[0]["help"]
    bad_ending: str = NIGHTMARES[0]["ending"]
    final_image: str = ENDINGS[0]


def build_world(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity("child", "character", params.child_name))
    companion = world.add(Entity("companion", "character", params.companion_name))
    child.meters.update({"courage": 1.0, "fear": 0.0})
    companion.meters.update({"courage": 1.0})
    child.memes.update({"warning_heard": 0.0, "nightmare": 0.0, "safe": 0.0})
    companion.memes.update({"warning_heard": 0.0})
    world.facts.update(
        child=params.child_name,
        companion=params.companion_name,
        companion_kind=params.companion_kind,
        setting=params.setting,
        nightmare=params.nightmare_name,
        warning=params.warning,
        danger=params.danger,
        help_object=params.help_object,
        bad_ending=params.bad_ending,
        final_image=params.final_image,
    )

    world.say(
        f"In {params.setting}, Luna dreamed of {params.nightmare_name}; "
        f"the nightmare came creeping with a terrible fright."
        .replace("Luna", params.child_name)
    )
    world.say(
        f'"Wake up!" cried {params.companion_name}, {params.companion_kind}; '
        f'"Something is wrong in the night."'
    )
    world.say(
        f"{params.warning.capitalize()}—a warning small but clear, "
        f"yet {params.child_name} did not listen, for fear was drawing near."
    )
    world.say(
        f'"We should ring the {params.help_object}," said {params.child_name}. '
        f'"No, run!" said {params.companion_name}; "the dark is far too strong!"'
    )
    child.memes["warning_heard"] = 1.0
    companion.memes["warning_heard"] = 1.0
    child.memes["nightmare"] = 1.0
    child.meters["fear"] = 2.0
    world.fired.add("foreshadowing")
    world.say(
        f"The {params.nightmare_name} rose, and the bedroom shook; "
        f"{params.danger.capitalize()}, as the warning had foretook."
    )
    world.fired.add("conflict")
    world.say(
        f"They tugged at the {params.help_object}, but the nightmare held it tight; "
        f"the courage in their hearts grew dim beneath the bite of night."
    )
    world.fired.add("bad_ending")
    world.say(params.bad_ending)
    child.meters["fear"] = 3.0
    world.say(params.final_image)
    return world


ASP_RULES = r"""
nightmare_present.
warning_seen.
conflict(nightmare) :- nightmare_present, warning_seen.
bad_ending(nightmare) :- conflict(nightmare).
#show conflict/1.
#show bad_ending/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("nightmare_present"),
            asp.fact("warning_seen"),
        ]
    )


def asp_program(show: str = "#show conflict/1.\n#show bad_ending/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    conflicts = set(asp.atoms(model, "conflict"))
    endings = set(asp.atoms(model, "bad_ending"))
    if conflicts == {("nightmare",)} and endings == {("nightmare",)}:
        print("OK: ASP and Python agree on the nightmare conflict and bad ending.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP conflict:", sorted(conflicts))
    print("ASP bad ending:", sorted(endings))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    seed = args.seed if args.seed is not None else 0
    rng = random.Random(seed)
    nightmare = NIGHTMARES[seed % len(NIGHTMARES)]
    child_name, _ = CHILDREN[(seed // 3) % len(CHILDREN)]
    companion_name, companion_kind = COMPANIONS[(seed // 5) % len(COMPANIONS)]
    return StoryParams(
        seed=seed,
        child_name=child_name,
        companion_name=companion_name,
        companion_kind=companion_kind,
        setting=rng.choice(SETTINGS),
        nightmare_name=nightmare["name"],
        warning=nightmare["warning"],
        danger=nightmare["danger"],
        help_object=nightmare["help"],
        bad_ending=nightmare["ending"],
        final_image=rng.choice(ENDINGS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a rhyming story about a child facing a nightmare.",
        f"Include foreshadowing through {f['warning']}.",
        f"Build a conflict with {f['nightmare']} and end with {f['bad_ending']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What nightmare troubled {f['child']}?",
            answer=f"{f['child']} was troubled by {f['nightmare']}, which entered the dream and brought fear.",
        ),
        QAItem(
            question="What warning foreshadowed the danger?",
            answer=f"The warning was that {f['warning']}. It appeared before the nightmare's danger became clear.",
        ),
        QAItem(
            question=f"Who spoke with {f['child']} during the conflict?",
            answer=f"{f['companion']} spoke with {f['child']} and urged caution when the nightmare appeared.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended badly: {f['bad_ending']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a nightmare?",
            answer="A nightmare is a frightening dream that can make a sleeper feel afraid or worried.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is an early clue that hints at something important that may happen later.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    chunks = ["== prompts =="]
    chunks.extend(sample.prompts)
    chunks.append("")
    chunks.append("== story qa ==")
    for item in sample.story_qa:
        chunks.append(f"Q: {item.question}")
        chunks.append(f"A: {item.answer}")
    chunks.append("")
    chunks.append("== world qa ==")
    for item in sample.world_qa:
        chunks.append(f"Q: {item.question}")
        chunks.append(f"A: {item.answer}")
    return "\n".join(chunks)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A rhyming nightmare conflict storyworld.")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(sorted(set(asp.atoms(model, "conflict"))))
        print(sorted(set(asp.atoms(model, "bad_ending"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = len(NIGHTMARES) if args.all else args.n
    samples = []
    for index in range(count):
        sample_seed = base_seed + index
        params = resolve_params(
            argparse.Namespace(seed=sample_seed),
            random.Random(sample_seed),
        )
        samples.append(generate(params))

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
