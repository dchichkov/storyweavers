#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/kill_shock_dim_transformation_foreshadowing_rhyming_story.py
=================================================================================================

A standalone story world for a tiny rhyming tale about a risky magic light,
a foreshadowed dimming, and a gentle transformation that turns a scare into
a glow.

Seed tale inspiration:
---
A little lantern-sprite loved bright shows and silver light. Before the moon
rose, a stormy pop in the sky made the lantern tremble and dim. The sprite
feared the dark, but a friend found the "kill switch" charm on the stagebox,
pressed it at the right time, and the bright blast transformed into a soft
song-light instead of a fright.

This world models:
- physical meters: brightness, dimness, charge, heat, glow, smoke
- emotional memes: joy, worry, shock, hope, relief
- a foreshadowing cue that warns the hero before the dimming
- a transformation turn that safely changes the light's form
- a rhyming prose style with a complete beginning, middle, and end
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"sprite", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    stage_name: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Device:
    id: str
    label: str
    phrase: str
    trigger: str
    transforms_to: str
    creates: str
    danger: str
    foreshadow: str


@dataclass
class StoryParams:
    place: str
    device: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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


SETTINGS = {
    "moon_stage": Setting(place="the moon stage", stage_name="moon stage", affords={"show"}),
    "lantern_room": Setting(place="the lantern room", stage_name="lantern room", affords={"show"}),
    "cloud_dock": Setting(place="the cloud dock", stage_name="cloud dock", affords={"show"}),
}

DEVICES = {
    "shock_dim": Device(
        id="shock_dim",
        label="shock-dim wand",
        phrase="a shock-dim wand with a silver tip",
        trigger="tap the silver tip",
        transforms_to="softglow",
        creates="soft glow",
        danger="dim and trembling",
        foreshadow="the air gave a hush and the lamp began to dim",
    ),
    "kill_switch": Device(
        id="kill_switch",
        label="kill-switch charm",
        phrase="a kill-switch charm tied on a blue cord",
        trigger="press the blue knot",
        transforms_to="softglow",
        creates="safe hush",
        danger="too bright and wild",
        foreshadow="the cord twitched like it knew a storm was coming",
    ),
}

GENTLE_NAMES = ["Pip", "Mina", "Toby", "Nia", "Lumi", "Faye", "Rin", "Bea"]
TRAITS = ["brave", "small", "bright-eyed", "spry", "cheery"]


def story_rhyme(a: str, b: str) -> str:
    return f"{a} {b}"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world: foreshadow a dimming, then transform it safely."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    device = args.device or rng.choice(list(DEVICES))
    hero_name = args.name or rng.choice(GENTLE_NAMES)
    helper_name = args.helper or rng.choice([n for n in GENTLE_NAMES if n != hero_name])
    return StoryParams(place=place, device=device, hero_name=hero_name, helper_name=helper_name)


def _entity_state(label: str, kind: str, type_: str) -> Entity:
    return Entity(id=label, kind=kind, type=type_, label=label, phrase=label)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    device = DEVICES[params.device]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type="sprite",
        label=params.hero_name,
        phrase=f"little {params.hero_name}",
        meters={"brightness": 2.0, "glow": 1.0},
        memes={"joy": 1.0, "worry": 0.0, "hope": 0.0, "relief": 0.0, "shock": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="sprite",
        label=params.helper_name,
        phrase=f"tiny {params.helper_name}",
        meters={"brightness": 1.0},
        memes={"joy": 0.5, "worry": 0.0, "hope": 0.0, "relief": 0.0},
    ))
    wand = world.add(Entity(
        id=device.id,
        kind="thing",
        type="device",
        label=device.label,
        phrase=device.phrase,
        owner=hero.id,
        meters={"charge": 2.0, "brightness": 2.0},
        memes={"mystery": 1.0},
    ))
    stage = world.add(Entity(
        id="stage",
        kind="thing",
        type="stage",
        label=setting.stage_name,
        phrase=setting.place,
        meters={"brightness": 1.5, "shadow": 0.0},
    ))

    world.say(
        f"On the {setting.stage_name} so wide, {hero.id} shone with a spark inside."
    )
    world.say(
        f"{hero.id} loved the show and the silver glow, and {helper.id} clapped, all in a row."
    )
    world.say(
        f"But a small hush came first, a foreshadowed burst: {device.foreshadow}."
    )
    world.para()

    # Middle: tension grows.
    hero.memes["worry"] += 1.0
    hero.memes["shock"] += 1.0
    hero.meters["brightness"] -= 1.0
    stage.meters["shadow"] = 1.0
    wand.meters["charge"] -= 1.0
    world.say(
        f"The light went thin; the room felt dim, and {hero.id}'s smile grew small and grim."
    )
    world.say(
        f"{helper.id} saw the wobble, the twirl and the trouble, and hurried near with a steady bubble."
    )

    # Turn: the helper uses the device; transformation happens.
    world.para()
    helper.memes["hope"] += 1.0
    world.say(
        f'"Try the {device.label}," said {helper.id} in a hum, "and tap {device.trigger}; let safety come."'
    )

    # Reasonable transformation gate.
    if device.id == "shock_dim":
        hero.meters["brightness"] = max(0.0, hero.meters["brightness"] - 0.5)
        hero.meters["glow"] += 2.0
        hero.meters["softglow"] = 1.0
        hero.meters["shockdim"] = 1.0
        hero.memes["shock"] = max(0.0, hero.memes["shock"] - 0.5)
        hero.memes["hope"] += 1.0
        stage.meters["shadow"] = 0.2
        world.say(
            f"When the tip was tapped, the bright flash wrapped up and slipped into a soft new cap."
        )
    else:
        hero.meters["brightness"] = 1.0
        hero.meters["glow"] = 2.0
        hero.meters["safe"] = 1.0
        hero.memes["worry"] = max(0.0, hero.memes["worry"] - 0.5)
        world.say(
            f"When the blue knot was pressed, the wild light rested and wore a safe new vest."
        )

    # Resolution: the transformed light is kinder and dimmer, but still bright enough.
    world.para()
    hero.memes["relief"] += 2.0
    helper.memes["relief"] += 2.0
    helper.meters["brightness"] += 0.5
    world.say(
        f"Now the room sang low, in a tender glow, and the dark felt friendly instead of slow."
    )
    world.say(
        f"{hero.id} smiled at the change, so soft and tame; {helper.id} smiled too, and the stage kept its flame."
    )

    world.facts = {
        "hero": hero,
        "helper": helper,
        "wand": wand,
        "stage": stage,
        "device": device,
        "setting": setting,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    device = f["device"]
    return [
        f'Write a short rhyming story for a little child about {hero.id}, a foreshadowed dimming, and a safe transformation.',
        f"Tell a gentle rhyming tale where {helper.id} helps {hero.id} use the {device.label} when the room begins to dim.",
        f'Write a tiny story that includes the words "kill" and "shock-dim" without sounding scary, and ends with a calm glow.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    device = f["device"]
    setting = f["setting"]

    return [
        QAItem(
            question=f"Who is the story about on the {setting.stage_name}?",
            answer=f"The story is about {hero.id}, with {helper.id} beside {hero.id} on the {setting.stage_name}.",
        ),
        QAItem(
            question=f"What warning came before the room grew dim?",
            answer=f"The warning was that {device.foreshadow}. That hint came before the light turned faint.",
        ),
        QAItem(
            question=f"What did {helper.id} suggest using to change the light safely?",
            answer=f"{helper.id} suggested using the {device.label}. That was the careful way to transform the bright light.",
        ),
        QAItem(
            question=f"How did the light change at the end?",
            answer="It changed into a soft glow. The new glow was calmer, dimmer, and friendly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to transform something?",
            answer="To transform something means to change it into a different form or kind.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small clue that hints something important may happen later.",
        ),
        QAItem(
            question="What does dim mean?",
            answer="Dim means not very bright. A dim light gives off only a little glow.",
        ),
        QAItem(
            question="Why can a soft glow feel nicer than a harsh flash?",
            answer="A soft glow is gentler on your eyes, so it feels calmer and easier to enjoy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if abs(v) > 0}
        memes = {k: round(v, 2) for k, v in e.memes.items() if abs(v) > 0}
        out.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="moon_stage", device="shock_dim", hero_name="Pip", helper_name="Mina"),
    StoryParams(place="lantern_room", device="kill_switch", hero_name="Lumi", helper_name="Bea"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for did, d in DEVICES.items():
        lines.append(asp.fact("device", did))
        lines.append(asp.fact("transforms_to", did, d.transforms_to))
        lines.append(asp.fact("creates", did, d.creates))
        lines.append(asp.fact("danger", did, d.danger))
    return "\n".join(lines)


ASP_RULES = r"""
valid_device(D) :- device(D).
valid_story(P, D) :- place(P), device(D), affords(P, show), valid_device(D).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_pairs = sorted(set(asp.atoms(model, "valid_story")))
    python_pairs = sorted((p, d) for p in SETTINGS for d in DEVICES)
    if set(clingo_pairs) == set(python_pairs):
        print(f"OK: ASP parity matches ({len(clingo_pairs)} combinations).")
        return 0
    print("Mismatch between ASP and Python.")
    return 1


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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.asp:
        try:
            import asp
        except Exception as e:
            raise StoryError(str(e))
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
