#!/usr/bin/env python3
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
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


@dataclass
class StoryParams:
    fox_name: str
    beetle_name: str
    setting: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Tavi", "Nia", "Pip", "Suri", "Bram", "Cora"]
SETTINGS = ["the warm meadow", "the old orchard", "the hill beside the brook"]
ARCS = [
    {
        "key": "lantern_husk",
        "premise": "{fox} lived beside {setting}, where a small beetle named {beetle} carried a dry husk like a lantern.",
        "problem": "One evening, {fox} saw a spark inside the husk and tried to inflame it with a breath. The flame leaped too high and smoked the meadow path.",
        "conflict": '"Put it out at once!" cried {beetle}. "A bright flame will help us!" answered {fox}. Their fear and pride made the conflict hotter.',
        "turn": "Then {beetle} noticed that the husk was only a shell, while a damp green leaf lay nearby. The leaf could cool the spark without crushing the tiny light.",
        "action": '"You found the safe way," said {fox}. Together they covered the husk with the leaf and moved it away from the dry grass.',
        "resolution": "The flame became a gentle glow. {fox} admitted that wanting to help had caused the danger, and {beetle} forgave the hasty choice.",
        "ending": "They carried the glowing husk to a stone beside the path, where it lit the way home for every small traveler.",
        "problem_fact": "a spark inside a dry husk began to inflame the meadow grass",
        "clue_fact": "a damp green leaf could cool the spark while saving its gentle light",
        "action_fact": "they covered the husk with the leaf and moved it from the grass",
        "outcome_fact": "the husk became a safe lantern and the conflict ended",
    },
    {
        "key": "thorn_hollow",
        "premise": "{fox} guarded a hollow tree in {setting}, while {beetle} gathered a brown husk to make a warm shelter.",
        "problem": "A coal hidden beneath the husk began to inflame the dry leaves. Smoke curled through the hollow, and the animals could not agree on what to do.",
        "conflict": '"Carry the coal outside!" said {fox}. "Save the shelter first!" argued {beetle}. Their quarrel delayed them while the smoke grew thick.',
        "turn": "A cool breeze slipped through a thorn hole. {beetle} realized that opening the hole would guide the smoke out, and {fox} saw that the coal could be moved with a flat stone.",
        "action": '"You open the hole; I will lift the coal," said {fox}. They worked together, using the stone and the breeze instead of their paws.',
        "resolution": "The smoke streamed away, the coal cooled, and the hollow stayed safe. The two friends smiled because neither idea had needed to win alone.",
        "ending": "That night, the husk rested by the hollow door, dry and useful, while moonlight shone through the new little window.",
        "problem_fact": "a coal began to inflame dry leaves inside the hollow",
        "clue_fact": "a thorn hole could guide smoke out and a flat stone could move the coal",
        "action_fact": "they opened the hole and lifted the coal with a stone",
        "outcome_fact": "the hollow stayed safe and the friends solved their conflict",
    },
    {
        "key": "seed_cake",
        "premise": "{fox} and {beetle} shared a seed cake beneath an oak in {setting}. Beside them lay a silver-brown husk left by the wind.",
        "problem": "The husk caught a tiny ember and began to inflame. {fox} wanted to stomp it, but {beetle} feared the ember would scatter into the seed cake.",
        "conflict": '"Stomp quickly!" said {fox}. "Wait and shield the cake!" said {beetle}. Their disagreement left both animals frozen.',
        "turn": "A drop of water fell from an oak leaf onto the husk. It showed them that a small cup made from the leaf could hold water safely.",
        "action": "{beetle} folded the leaf into a cup while {fox} carried water from the brook. They poured together, slowly, onto the husk.",
        "resolution": "The ember went dark without scattering, and the seed cake stayed dry. {fox} and {beetle} laughed at how a quiet plan had beaten a loud argument.",
        "ending": "They shared the cake beside the harmless husk, which now looked like a little silver boat on the grass.",
        "problem_fact": "an ember began to inflame a husk beside their seed cake",
        "clue_fact": "an oak leaf could become a small cup for carrying water",
        "action_fact": "they carried water in the leaf cup and cooled the husk together",
        "outcome_fact": "the ember went dark and their seed cake stayed safe",
    },
]


def _rng_for(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    raw = "|".join((params.fox_name, params.beetle_name, params.setting))
    return random.Random(int.from_bytes(hashlib.sha256(raw.encode()).digest()[:8], "big"))


def tell(params: StoryParams) -> World:
    if params.fox_name == params.beetle_name:
        raise StoryError("fox_name and beetle_name must be different characters")
    if params.setting not in SETTINGS:
        raise StoryError(f"unknown setting: {params.setting}")
    rng = _rng_for(params)
    index = (params.seed if params.seed is not None else rng.randrange(len(ARCS))) % len(ARCS)
    arc = ARCS[index]

    world = World(params.setting)
    fox = world.add(Entity(params.fox_name, kind="character", type="fox", label="fox"))
    beetle = world.add(Entity(params.beetle_name, kind="character", type="beetle", label="beetle"))
    husk = world.add(Entity("husk", type="husk", label="dry husk", phrase="a dry husk"))
    fox.meters.update(energy=3.0, care=1.0)
    beetle.meters.update(energy=3.0, care=1.0)
    husk.meters.update(dryness=1.0, warmth=0.0)
    fox.memes["impatience"] = 1.0
    beetle.memes["worry"] = 1.0

    beats = ["premise", "problem", "conflict", "turn", "action", "resolution", "ending"]
    rendered = {}
    for i, beat in enumerate(beats):
        if i:
            world.para()
        text = arc[beat].format(fox=params.fox_name, beetle=params.beetle_name, setting=params.setting)
        rendered[beat] = text
        world.say(text)

    husk.meters.update(dryness=0.0, warmth=0.5)
    fox.memes["impatience"] = 0.0
    beetle.memes["worry"] = 0.0
    world.facts = {
        "fox": fox,
        "beetle": beetle,
        "husk": husk,
        "arc": arc,
        "rendered": rendered,
        "problem": arc["problem_fact"],
        "clue": arc["clue_fact"],
        "action": arc["action_fact"],
        "outcome": arc["outcome_fact"],
    }
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a child-friendly fable about a husk that begins to inflame and two animals who solve a conflict.",
        f"Tell a fable in {world.setting} where {f['fox'].id} and {f['beetle'].id} disagree, listen to each other, and create a happy ending.",
        "Write a short fable in which a small danger becomes safe through patience and teamwork.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    fox = f["fox"].id
    beetle = f["beetle"].id
    return [
        QAItem(
            question="Who were the two main characters?",
            answer=f"The story followed {fox}, a fox, and {beetle}, a beetle, who worked together.",
        ),
        QAItem(question="What danger began the conflict?", answer=f["rendered"]["problem"]),
        QAItem(question="What clue changed their plan?", answer=f["rendered"]["turn"]),
        QAItem(
            question="How did the characters solve the problem?",
            answer=f"{f['rendered']['action']} {f['rendered']['resolution']}",
        ),
        QAItem(question="What showed that the ending was happy?", answer=f["rendered"]["ending"]),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a husk?",
            answer="A husk is a dry outer covering around a seed, grain, or other small plant part.",
        ),
        QAItem(
            question="What does inflame mean?",
            answer="To inflame means to make something burn, glow, or become more heated and excited.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story, often with animals as characters, that teaches an idea through what happens.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:8} ({entity.type:8}) meters={meters} memes={memes}"
        )
    lines.append(f"  setting={world.setting}")
    lines.append("  conflict_resolved=True")
    lines.append("  happy_ending=True")
    return "\n".join(lines)


ASP_RULES = r"""
has_feature(conflict).
has_feature(happy_ending).
has_seed_word(inflame).
has_seed_word(husk).
valid_story :-
    has_feature(conflict),
    has_feature(happy_ending),
    has_seed_word(inflame),
    has_seed_word(husk).
#show valid_story/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("has_feature", "conflict"),
            asp.fact("has_feature", "happy_ending"),
            asp.fact("has_seed_word", "inflame"),
            asp.fact("has_seed_word", "husk"),
            asp.fact("style", "fable"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/0."))
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    if any(symbol.name == "valid_story" for symbol in model):
        sample = generate(StoryParams("Luna", "Milo", SETTINGS[0], seed=7))
        if all(word in sample.story.lower() for word in ("inflame", "husk")):
            print("OK: ASP and Python agree on the fable domain.")
            return 0
    print("MISMATCH: ASP and Python do not agree.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fable world with an inflamed husk and a happy ending.")
    parser.add_argument("--fox-name")
    parser.add_argument("--beetle-name")
    parser.add_argument("--setting", choices=SETTINGS)
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
    fox = args.fox_name or rng.choice(NAMES)
    choices = [name for name in NAMES if name != fox]
    beetle = args.beetle_name or rng.choice(choices)
    setting = args.setting or rng.choice(SETTINGS)
    return StoryParams(fox, beetle, setting)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("1 compatible fable pattern: inflame + husk + conflict + happy ending")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams("Luna", "Milo", SETTINGS[0], seed=0),
            StoryParams("Tavi", "Nia", SETTINGS[1], seed=1),
            StoryParams("Pip", "Suri", SETTINGS[2], seed=2),
        ]
        samples = [generate(params) for params in params_list]
    else:
        seen: set[str] = set()
        for i in range(max(args.n, 0) * 50 + 50):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
