#!/usr/bin/env python3
"""
storyworlds/worlds/juniper_tuba_toil_inner_monologue_friendship_curiosity.py
===========================================================================

A compact, self-contained storyworld in a fable-like style.

Seed essence:
- juniper
- tuba
- toil

Narrative instruments:
- Inner Monologue
- Friendship
- Curiosity

Premise:
A small friend wants to help with a hard job, but a shiny tuba and a patch of
juniper bushes make the job tempting to rush. The story turns when curiosity
reveals a better method, and friendship helps finish the toil kindly.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

# Make shared result containers importable when run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    place: str = "the garden path"
    task: str = "carry water"
    helper: str = "Mina"
    friend: str = "Pip"
    object: str = "a tuba"
    plant: str = "juniper"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def inc(self, bucket: str, amount: float = 1.0) -> None:
        store = self.meters if bucket in {"dust", "spill", "done"} else self.memes
        store[bucket] = store.get(bucket, 0.0) + amount


@dataclass
class World:
    params: StoryParams
    helper: Entity
    friend: Entity
    task_done: bool = False
    tool_clean: bool = True
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    trace: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTING_REGISTRY = {
    "garden": "the garden path",
    "yard": "the yard",
    "lane": "the narrow lane",
}

TASK_REGISTRY = {
    "carry_water": {
        "verb": "carry water",
        "hard": "toil",
        "method": "walk carefully",
        "risk": "spill the bucket",
        "turn": "notice the steady way the weight settled",
        "ending": "the water arrived with hardly a drop lost",
    },
    "move_stones": {
        "verb": "move stones",
        "hard": "toil",
        "method": "roll them one by one",
        "risk": "drop the heavy stones",
        "turn": "see that small steps were faster than a hurried boast",
        "ending": "the stones made a neat little line",
    },
    "gather_kindling": {
        "verb": "gather kindling",
        "hard": "toil",
        "method": "choose dry twigs from the edges",
        "risk": "snap the green branches",
        "turn": "remember that the best sticks were the ones already waiting",
        "ending": "a tidy pile rose beside the path",
    },
}

QA_KNOWLEDGE = {
    "juniper": (
        "What is juniper?",
        "Juniper is a shrub or small tree with sharp little leaves and berries.",
    ),
    "tuba": (
        "What is a tuba?",
        "A tuba is a large brass instrument that makes deep, rich notes.",
    ),
    "toil": (
        "What does toil mean?",
        "Toil means hard work that takes patience and effort.",
    ),
    "curiosity": (
        "What is curiosity?",
        "Curiosity is the desire to look, ask, and learn something new.",
    ),
    "friendship": (
        "What is friendship?",
        "Friendship is caring for someone and helping each other kindly.",
    ),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like storyworld about toil, curiosity, and friendship.")
    ap.add_argument("--place", choices=SETTING_REGISTRY)
    ap.add_argument("--task", choices=TASK_REGISTRY)
    ap.add_argument("--name", default=None)
    ap.add_argument("--friend", default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTING_REGISTRY))
    task = args.task or rng.choice(list(TASK_REGISTRY))
    name = args.name or rng.choice(["Mina", "Lio", "Nia", "Tomo", "Sera", "Eli"])
    friend = args.friend or rng.choice(["Pip", "June", "Arlo", "Bea", "Oren", "Luz"])
    if name == friend:
        raise StoryError("The helper and the friend must be different characters.")
    return StoryParams(place=SETTING_REGISTRY[place], task=task, helper=name, friend=friend, object="a tuba", plant="juniper")


def generate(params: StoryParams) -> StorySample:
    world = World(
        params=params,
        helper=Entity(name=params.helper, kind="child", label=params.helper),
        friend=Entity(name=params.friend, kind="child", label=params.friend),
    )
    task = TASK_REGISTRY[params.task]

    world.say(
        f"On {params.place}, {params.helper} had a piece of {task['hard']} to do, "
        f"and {params.friend} came along with a bright old tuba."
    )
    world.say(
        f"{params.helper} looked at the deep brass shine and thought, "
        f"“If I stop to play, will the {task['verb']} ever get done?”"
    )
    world.para()
    world.say(
        f"Then curiosity tugged at {params.friend}, who peered near the {params.plant} bush "
        f"and asked if the job had a kinder way."
    )
    world.say(
        f"{params.helper} answered in an inner monologue of the heart, "
        f"“I can finish this if I move slowly and keep my hands steady.”"
    )
    world.say(
        f"So the two friends chose to {task['method']}, instead of trying to {task['risk']}."
    )
    world.para()
    world.say(
        f"They worked side by side until the little bit of {task['hard']} was done, "
        f"and the tuba rested safely beside the {params.plant}."
    )
    world.say(
        f"In the end, {task['ending']}, and friendship made the work feel light."
    )

    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=[
            "Write a short fable about a child, a curious friend, and a piece of hard work.",
            "Tell a gentle story where a tuba, a juniper bush, and friendship help a task get done.",
            "Write a child-facing story that includes inner monologue, curiosity, and a warm ending.",
        ],
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )
    return sample


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    task = TASK_REGISTRY[p.task]
    return [
        QAItem(
            question=f"What hard thing did {p.helper} need to do on {p.place}?",
            answer=f"{p.helper} needed to {task['verb']} on {p.place}.",
        ),
        QAItem(
            question=f"What did {p.friend} notice near the {p.plant} bush?",
            answer=f"{p.friend} noticed that the job might have a kinder way, and curiosity helped ask a useful question.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{task['ending'].capitalize()}, and the friends finished the work together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["juniper", "tuba", "toil", "curiosity", "friendship"]:
        q, a = QA_KNOWLEDGE[key]
        out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
story(Place,Task) :- place(Place), task(Task).
valid_story(Place,Task) :- story(Place,Task), curiosity(Task), friendship(Task).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for place in SETTING_REGISTRY:
        lines.append(asp.fact("place", place))
    for task in TASK_REGISTRY:
        lines.append(asp.fact("task", task))
    lines.append(asp.fact("curiosity", "carry_water"))
    lines.append(asp.fact("curiosity", "move_stones"))
    lines.append(asp.fact("curiosity", "gather_kindling"))
    lines.append(asp.fact("friendship", "carry_water"))
    lines.append(asp.fact("friendship", "move_stones"))
    lines.append(asp.fact("friendship", "gather_kindling"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def verify() -> int:
    python_count = len(TASK_REGISTRY) * len(SETTING_REGISTRY)
    try:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        asp_count = len(asp.atoms(model, "valid_story"))
    except Exception as err:  # pragma: no cover
        print(f"ASP unavailable: {err}")
        return 1
    if asp_count > 0 and python_count > 0:
        print(f"OK: ASP and Python both describe a nonempty story space ({python_count} ideas).")
        return 0
    print("MISMATCH: one side found no valid stories.")
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- trace ---")
        for line in sample.world.trace:
            print(line)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        raise SystemExit(verify())
    if args.asp:
        try:
            import storyworlds.asp as asp
            model = asp.one_model(asp_program("#show valid_story/2."))
            atoms = sorted(set(asp.atoms(model, "valid_story")))
        except Exception as err:
            raise SystemExit(str(err))
        for atom in atoms:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place in SETTING_REGISTRY:
            for task in TASK_REGISTRY:
                params = StoryParams(place=SETTING_REGISTRY[place], task=task, helper="Mina", friend="Pip", object="a tuba", plant="juniper", seed=base_seed)
                samples.append(generate(params))
    else:
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
