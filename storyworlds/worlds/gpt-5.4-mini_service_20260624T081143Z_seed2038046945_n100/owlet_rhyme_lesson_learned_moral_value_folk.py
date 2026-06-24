#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/owlet_rhyme_lesson_learned_moral_value_folk.py
==============================================================================================================

A small folk-tale storyworld about an owlet who learns a useful lesson, with
gentle rhyme, a clear moral value, and a state-driven turn.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str = "meadow"
    lesson: str = "listen"
    moral: str = "kindness"
    seed: Optional[int] = None


SETTINGS: dict[str, dict[str, str]] = {
    "meadow": {
        "place": "the moonlit meadow",
        "sound": "soft grass and crickets",
        "helper": "a wise field mouse",
        "hazard": "the dark hollow near the roots",
        "gift": "a silver feather",
    },
    "oak": {
        "place": "the old oak tree",
        "sound": "wind in the branches",
        "helper": "a patient squirrel",
        "hazard": "the high windy limb",
        "gift": "a warm nest twig",
    },
    "brook": {
        "place": "the lantern-lit brook",
        "sound": "water singing over stones",
        "helper": "a gentle heron",
        "hazard": "the slippery bank",
        "gift": "a smooth reed",
    },
}

LESSONS = {
    "listen": {
        "title": "listen before you leap",
        "action": "listened",
        "warning": "first ask, then act",
    },
    "share": {
        "title": "share what you have",
        "action": "shared",
        "warning": "kind hands make small gifts feel large",
    },
    "wait": {
        "title": "wait for the safer way",
        "action": "waited",
        "warning": "slow wings find steadier paths",
    },
}

MORALS = {
    "kindness": "kindness makes a small home feel bright",
    "patience": "patience keeps trouble from tumbling near",
    "courage": "courage is strongest when it is careful",
}


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owns: list[str] = field(default_factory=list)
    located: str = ""

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.story_lines: list[str] = []
        self.trace_lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.story_lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.story_lines)


def build_world(params: StoryParams) -> World:
    cfg = SETTINGS[params.setting]
    lesson = LESSONS[params.lesson]
    moral = MORALS[params.moral]

    w = World(params)
    owlet = w.add(Entity(id="owlet", kind="character", label="young owlet"))
    mother = w.add(Entity(id="mother", kind="character", label="mother owl"))
    helper = w.add(Entity(id="helper", kind="character", label=cfg["helper"]))
    gift = w.add(Entity(id="gift", kind="thing", label=cfg["gift"], located=cfg["place"]))

    owlet.meters["hunger"] = 1
    owlet.memes["curiosity"] = 1
    owlet.memes["wanting"] = 1
    mother.memes["care"] = 1
    helper.memes["wise"] = 1

    w.facts.update(
        place=cfg["place"],
        sound=cfg["sound"],
        helper=cfg["helper"],
        hazard=cfg["hazard"],
        gift=cfg["gift"],
        lesson=lesson["title"],
        lesson_action=lesson["action"],
        lesson_warning=lesson["warning"],
        moral=moral,
    )

    # Act 1: set the folk-tale scene.
    w.say(
        f"Deep in {cfg['place']}, under a pale round moon, a young owlet lived with a mother owl."
    )
    w.say(
        f"The night was full of {cfg['sound']}, and the little owlet loved to peer into every shadow."
    )
    w.say(
        f"It longed to fly at once, for it had heard that every brave bird must learn to {lesson['action']}."
    )

    # Act 2: tension.
    w.say(
        f"But one night the owlet spotted {cfg['hazard']} and fluttered too near it, hoping to reach {cfg['gift']} first."
    )
    owlet.memes["reckless"] = 1
    mother.memes["worry"] = 1

    w.say(
        f"'Little wings, little wings, do not rush the sting,' said the mother owl. 'First {lesson['warning']}.'"
    )
    helper.memes["helpful"] = 1
    w.say(
        f"Then {cfg['helper']} came along and showed the owlet a safer path around the roots and stones."
    )

    # Act 3: turn and resolution.
    owlet.memes["humble"] = 1
    owlet.memes["safe_choice"] = 1
    w.say(
        f"The owlet {lesson['action']} at last, and it chose the safer path instead of the sharp little shortcut."
    )
    owlet.owns.append(cfg["gift"])
    w.say(
        f"There, waiting in the moonshine, was {cfg['gift']}; the owlet carried it home with care."
    )
    w.say(
        f"By dawn, the nest felt warm, and the owlet knew the {params.moral} it had learned: {moral}."
    )

    w.facts.update(
        owl="owlet",
        lesson=lesson["title"],
        resolved=True,
        risky=True,
    )
    return w


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a folk tale about an owlet at {f['place']} that learns to {f['lesson_action']}.",
        f"Tell a short story with rhyme, a gentle warning, and the moral value of {f['moral']}.",
        f"Create a child-friendly owlet tale that ends with the lesson '{f['lesson']}'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="Who is the story about?",
            answer="The story is about a young owlet who lives with a mother owl and learns a careful lesson.",
        ),
        QAItem(
            question=f"What was the owlet trying to reach near {f['hazard']}?",
            answer=f"It was trying to reach {f['gift']}.",
        ),
        QAItem(
            question="What did the mother owl tell the owlet?",
            answer=f"The mother owl told the owlet to {f['lesson_warning']}.",
        ),
        QAItem(
            question="What safer help did the owlet receive?",
            answer=f"{f['helper']} showed the owlet a safer path around the danger.",
        ),
        QAItem(
            question="What did the owlet learn in the end?",
            answer=f"The owlet learned to {f['lesson_action']} and choose the safer path.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an owlet?",
            answer="An owlet is a young owl.",
        ),
        QAItem(
            question="When do owls often wake up?",
            answer="Owls often wake up at night and use the dark to help them hunt and fly.",
        ),
        QAItem(
            question="What does a moral mean in a folk tale?",
            answer="A moral is the lesson the story wants you to remember after the tale ends.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(meadow).
setting(oak).
setting(brook).

lesson(listen).
lesson(share).
lesson(wait).

moral(kindness).
moral(patience).
moral(courage).

compatible(S, L, M) :- setting(S), lesson(L), moral(M).
#show compatible/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for l in LESSONS:
        lines.append(asp.fact("lesson", l))
    for m in MORALS:
        lines.append(asp.fact("moral", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/3."))
    asp_set = set(asp.atoms(model, "compatible"))
    py_set = {(s, l, m) for s in SETTINGS for l in LESSONS for m in MORALS}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python ({len(py_set)} combinations).")
        return 0
    print("MISMATCH between ASP and Python.")
    if asp_set - py_set:
        print("  only in ASP:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in Python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="An owlet folk tale with rhyme, lesson, and moral.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--lesson", choices=sorted(LESSONS))
    ap.add_argument("--moral", choices=sorted(MORALS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    lesson = args.lesson or rng.choice(list(LESSONS))
    moral = args.moral or rng.choice(list(MORALS))
    return StoryParams(setting=setting, lesson=lesson, moral=moral)


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.located:
            bits.append(f"located={e.located}")
        if e.owns:
            bits.append(f"owns={e.owns}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"{e.id}: " + ", ".join(bits))
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
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show compatible/3."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(combos)} compatible combinations:")
        for item in combos:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for s in SETTINGS:
            for l in LESSONS:
                for m in MORALS:
                    samples.append(generate(StoryParams(setting=s, lesson=l, moral=m, seed=base_seed)))
    else:
        seen = set()
        for i in range(max(1, args.n * 20)):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + i))
            if (params.setting, params.lesson, params.moral) in seen:
                continue
            seen.add((params.setting, params.lesson, params.moral))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
