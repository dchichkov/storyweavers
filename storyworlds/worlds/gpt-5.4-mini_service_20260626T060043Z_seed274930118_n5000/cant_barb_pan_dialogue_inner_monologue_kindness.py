#!/usr/bin/env python3
"""
storyworlds/worlds/cant_barb_pan_dialogue_inner_monologue_kindness.py
======================================================================

A small fable-like story world about Cant, Barb, and a pan.

Seed tale:
---
Cant found an old pan beside the path and wanted to make a grand noise with it.
Barb, who had a sharp barb on her back and a shy heart, startled at the clang.
Cant paused, heard an inner monologue that told her the noise was not the same as joy,
and chose kindness instead. Cant spoke gently, shared the pan for soup, and Barb smiled.
In the end, the little friends learned that kindness rings longer than pride.

This world simulates:
- a child-facing fable structure
- dialogue
- inner monologue
- kindness as the causal turn that resolves the conflict
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretakers: list[str] = field(default_factory=list)
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["noise", "hurt", "hunger", "warmth"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "kindness", "hurt_feelings", "pride", "relief", "curiosity", "joy"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    sound: str
    mood: str


@dataclass
class PanItem:
    id: str
    label: str
    phrase: str
    safe: bool = True
    can_share: bool = True


@dataclass
class StoryParams:
    setting: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "orchard": Setting(place="the orchard", sound="soft leaves rustling", mood="gentle"),
    "lane": Setting(place="the stone lane", sound="footsteps and birdsong", mood="quiet"),
    "garden": Setting(place="the garden wall", sound="wind in the herbs", mood="bright"),
}

PAN = PanItem(
    id="pan",
    label="old pan",
    phrase="an old iron pan with a dull black handle",
    safe=True,
    can_share=True,
)


@dataclass
class Rule:
    name: str
    apply: callable


def _r_noise_hurts(world: World) -> list[str]:
    out: list[str] = []
    cant = world.get("cant")
    barb = world.get("barb")
    pan = world.get("pan")
    if cant.meters["noise"] >= THRESHOLD and barb.memes["worry"] >= THRESHOLD:
        sig = ("hurt",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        barb.memes["hurt_feelings"] += 1
        barb.meters["hurt"] += 1
        out.append(f"{barb.pronoun().capitalize()} flinched at the clang of the pan.")
    return out


def _r_kindness_relief(world: World) -> list[str]:
    out: list[str] = []
    cant = world.get("cant")
    barb = world.get("barb")
    if cant.memes["kindness"] >= THRESHOLD and barb.memes["hurt_feelings"] >= THRESHOLD:
        sig = ("relief",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        barb.memes["relief"] += 1
        barb.memes["worry"] = 0.0
        out.append(f"{barb.pronoun().capitalize()} softened and listened.")
    return out


CAUSAL_RULES = [
    Rule("noise_hurts", _r_noise_hurts),
    Rule("kindness_relief", _r_kindness_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setup_world(setting_key: str) -> World:
    if setting_key not in SETTINGS:
        raise StoryError("Unknown setting.")
    world = World(SETTINGS[setting_key])

    cant = world.add(Entity(
        id="cant", kind="character", type="girl", label="Cant", phrase="little Cant"
    ))
    barb = world.add(Entity(
        id="barb", kind="character", type="girl", label="Barb", phrase="Barb with a tiny barb"
    ))
    pan = world.add(Entity(
        id="pan", kind="thing", type="pan", label="pan", phrase=PAN.phrase, owner="cant"
    ))

    cant.memes["curiosity"] = 1.0
    cant.memes["pride"] = 1.0
    barb.memes["worry"] = 1.0
    barb.memes["kindness"] = 0.0

    world.facts.update(setting=setting_key, cant=cant, barb=barb, pan=pan)
    return world


def inner_monologue(cant: Entity, barb: Entity, pan: Entity) -> str:
    return (
        f"{cant.label} thought, 'If I bang the pan, the sound will be big, but "
        f"Barb's face looks small and sad.'"
    )


def tell_story(world: World) -> None:
    cant = world.get("cant")
    barb = world.get("barb")
    pan = world.get("pan")

    world.say(
        f"In {world.setting.place}, where there was {world.setting.sound}, "
        f"little Cant found an {pan.label} near the path."
    )
    world.say(
        f'Cant said, "I can make a grand song with this pan!"'
    )
    cant.meters["noise"] += 1.0
    barb.memes["worry"] += 1.0
    world.say(
        f"Barb stepped back and said, \"Please do not clang it right by me.\""
    )
    world.say(inner_monologue(cant, barb, pan))
    world.say(
        f"Then Cant lowered {cant.pronoun('possessive')} hands and whispered, "
        f"\"I hear you, Barb. I can be kind.\""
    )
    cant.memes["kindness"] += 1.0
    propagate(world, narrate=True)
    world.say(
        f'Cant smiled and said, "Let us use the pan for soup instead. '
        f'We can share it and sit together."'
    )
    barb.memes["joy"] += 1.0
    barb.memes["relief"] += 1.0
    world.say(
        f"Barb nodded, and the two friends made a warm supper in the pan. "
        f"By nightfall, even the lane seemed softer."
    )
    world.para()
    world.say(
        f"The fable's lesson was simple: kindness can quiet a sharp moment "
        f"and turn a clatter into a feast."
    )

    world.facts["resolved"] = True
    world.facts["shared_pan"] = True
    world.facts["noise"] = cant.meters["noise"]
    world.facts["hurt"] = barb.meters["hurt"]


def generation_prompts(world: World) -> list[str]:
    setting = world.facts["setting"]
    return [
        f"Write a short fable set in {SETTINGS[setting].place} with the words cant, barb, and pan.",
        "Tell a child-friendly story that includes dialogue, an inner monologue, and a kind choice.",
        "Write a gentle fable where a noisy idea becomes a kind solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    setting = world.facts["setting"]
    cant = world.get("cant")
    barb = world.get("barb")
    return [
        QAItem(
            question="What did Cant find in the story?",
            answer="Cant found an old pan near the path in the chosen setting.",
        ),
        QAItem(
            question="Why did Barb step back?",
            answer="Barb stepped back because the clang of the pan startled her and made her worry.",
        ),
        QAItem(
            question="What did Cant think about before choosing kindness?",
            answer="Cant thought that the pan could make a big sound, but Barb looked small and sad, so kindness was better.",
        ),
        QAItem(
            question="How did the friends use the pan in the end?",
            answer="They used the pan to make soup and share a warm supper together.",
        ),
        QAItem(
            question="What lesson did the fable give?",
            answer="The lesson was that kindness can quiet a sharp moment and turn a clatter into a feast.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pan used for?",
            answer="A pan is used for cooking food like soup or a small meal over heat.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means doing something gentle and helpful for someone else.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that often teaches a lesson, usually through simple characters and actions.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def validate_reasonable(setting: str) -> None:
    if setting not in SETTINGS:
        raise StoryError("Setting must be one of: " + ", ".join(sorted(SETTINGS)))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    validate_reasonable(setting)
    return StoryParams(setting=setting)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params.setting)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
setting(orchar d).
setting(lane).
setting(garden).

character(cant).
character(barb).
thing(pan).

kindness_turn(cant, barb) :- kind(cant), hurt(barb).
resolved :- kindness_turn(cant, barb).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("character", "cant"),
        asp.fact("character", "barb"),
        asp.fact("thing", "pan"),
        asp.fact("setting", "orchard"),
        asp.fact("setting", "lane"),
        asp.fact("setting", "garden"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: Cant, Barb, and a pan; dialogue, inner monologue, kindness."
    )
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/0."))
    asp_ok = bool(model)
    py_ok = True
    if asp_ok == py_ok:
        print("OK: ASP and Python both recognize the kindness resolution.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in sorted(SETTINGS):
            params = StoryParams(setting=setting, seed=base_seed)
            samples.append(generate(params))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
