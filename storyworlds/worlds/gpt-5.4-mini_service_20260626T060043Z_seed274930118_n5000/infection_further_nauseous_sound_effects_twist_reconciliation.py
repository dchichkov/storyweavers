#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/infection_further_nauseous_sound_effects_twist_reconciliation.py
=================================================================================================

A small heartwarming story world about a child who worries about an infection,
feels nauseous, hears sound effects all around the room, and then reaches a
twist that leads to reconciliation.

The story is built from a compact world model:
- typed entities with meters and memes
- physically grounded infection risk and relief
- a gentle twist that changes what the scary sign means
- a warm reconciliation ending

This script supports the standard Storyweavers interface, plus an inline ASP
twin for parity checks.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Situation:
    id: str
    trigger: str
    sound: str
    risk: str
    twist: str
    relief: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    sound_fx: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.sound_fx = list(self.sound_fx)
        return clone


@dataclass
class StoryParams:
    place: str
    situation: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"soup", "bandage"}),
    "garden": Setting(place="the garden", indoor=False, affords={"soup", "bandage"}),
    "clinic": Setting(place="the clinic", indoor=True, affords={"bandage", "medicine"}),
}

SITUATIONS = {
    "soup": Situation(
        id="soup",
        trigger="warm soup",
        sound="slurp-swish",
        risk="nauseous",
        twist="the smell was from the soup, not from an infection",
        relief="a cool drink and a clean cloth",
        keyword="soup",
        tags={"sound-effects", "twist", "reconciliation", "nauseous"},
    ),
    "bandage": Situation(
        id="bandage",
        trigger="a small cut",
        sound="beep-beep",
        risk="infection",
        twist="the red mark was only from a sticker, not an infection",
        relief="soap, ointment, and a soft bandage",
        keyword="bandage",
        tags={"sound-effects", "twist", "reconciliation", "infection"},
    ),
}

NAMES = {
    "girl": ["Mina", "Lila", "Nora", "Ruby"],
    "boy": ["Owen", "Eli", "Theo", "Finn"],
    "mother": "mother",
    "father": "father",
}


class SoundWorld:
    def __init__(self) -> None:
        self.sounds: list[str] = []

    def add(self, fx: str) -> None:
        self.sounds.append(fx)


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    situation = SITUATIONS[params.situation]
    world = World(setting)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"comfort": 1.0, "nausea": 0.0, "worry": 0.0, "relief": 0.0},
        memes={"love": 1.0, "fear": 0.0, "trust": 1.0, "reconciliation": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        meters={"patience": 1.0, "care": 1.0},
        memes={"concern": 1.0, "love": 1.0},
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type=situation.id,
        label=situation.trigger,
        phrase=situation.trigger,
        owner=child.id,
        caretaker=parent.id,
    ))
    world.facts.update(child=child, parent=parent, item=item, situation=situation, setting=setting)
    return world


def narration_sfx(world: World, fx: str) -> str:
    world.sound_fx.append(fx)
    return f"*{fx}*"


def tell_story(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    situation: Situation = f["situation"]

    world.say(
        f"{child.id} was a little {child.type} who liked quiet days with {parent.label if parent.label else 'the parent'}."
    )
    world.say(
        f"One day, {child.id} noticed {situation.trigger} and heard {narration_sfx(world, situation.sound)} from the room."
    )
    world.say(
        f"That sound made {child.pronoun('object')} think about {situation.risk} and feel a little nauseous."
    )
    world.para()
    world.say(
        f"{child.id} tucked {child.pronoun('possessive')} hands close and said, "
        f'"I feel {situation.risk} in here."'
    )
    world.say(
        f"{parent.label.capitalize()} listened carefully and looked further, because a kind grown-up checks what is real before worrying too much."
    )
    world.say(
        f"Then came the twist: {situation.twist}."
    )
    world.para()
    world.say(
        f"{parent.label.capitalize()} smiled and washed the spot gently while {child.id} watched the water go {narration_sfx(world, 'drip-drip')} into the sink."
    )
    world.say(
        f"Together they used {situation.relief}, and {child.id}'s stomach stopped feeling so tight."
    )
    world.say(
        f"{child.id} leaned into {parent.label if parent.label else 'the parent'} for a hug, and the worry turned into reconciliation."
    )
    world.say(
        f"By the end, the room was calm again, {parent.label if parent.label else 'the parent'} was nearby, and {child.id} could breathe easy."
    )

    world.facts["resolved"] = True
    world.facts["twist_text"] = situation.twist
    world.facts["sound_fx"] = list(world.sound_fx)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    sit: Situation = f["situation"]
    return [
        f'Write a heartwarming story for a young child that includes the word "{sit.keyword}" and a gentle twist.',
        f"Tell a story where {child.id} hears a strange sound effect, worries about {sit.risk}, and then feels better.",
        f"Write a simple reconciliation story that begins with a scary feeling, looks further, and ends kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    sit: Situation = f["situation"]
    return [
        QAItem(
            question=f"What did {child.id} hear that made the moment feel scary?",
            answer=f"{child.id} heard {sit.sound}, which sounded strange and made the room feel worrisome.",
        ),
        QAItem(
            question=f"Why did {child.id} feel nauseous before the twist?",
            answer=f"{child.id} felt nauseous because the sound and the possible {sit.risk} made {child.pronoun('object')} worry.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {sit.twist}. That changed the scary guess into something calmer.",
        ),
        QAItem(
            question=f"How did {child.id} and {parent.label if parent.label else 'the parent'} end the story?",
            answer=f"They ended with reconciliation: {parent.label if parent.label else 'the parent'} helped gently, and {child.id} felt safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an infection?",
            answer="An infection happens when tiny germs get into a cut or another part of the body and cause trouble, so people clean it and get help if needed.",
        ),
        QAItem(
            question="Why can a smell make someone feel nauseous?",
            answer="A strong or unpleasant smell can upset the stomach and make someone feel like they might throw up.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that help readers imagine noises, like drip-drip, beep-beep, or swish.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop feeling upset and come back together kindly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"sounds={world.sound_fx}")
    return "\n".join(lines)


ASP_RULES = r"""
sound_fx(F) :- effect(F).
twist_present :- twist(_).
reconciles :- reconciliation(_).

valid_story(Place, Situation, Gender) :-
    setting(Place),
    affords(Place, Situation),
    situation(Situation),
    wears(Gender).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if setting.indoor:
            lines.append(asp.fact("indoor", pid))
        for s in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, s))
    for sid, sit in SITUATIONS.items():
        lines.append(asp.fact("situation", sid))
        lines.append(asp.fact("effect", sit.sound))
        lines.append(asp.fact("twist", sid))
        lines.append(asp.fact("reconciliation", sid))
        for tag in sorted(sit.tags):
            lines.append(asp.fact("tag", sid, tag))
    for gender in ("girl", "boy"):
        lines.append(asp.fact("wears", gender))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python-only:", sorted(py - asp_set))
    print("asp-only:", sorted(asp_set - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for sit in setting.affords:
            if sit in SITUATIONS:
                for gender in ("girl", "boy"):
                    combos.append((place, sit, gender))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming infection-and-twist story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--situation", choices=SITUATIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    setting = SETTINGS[place]
    situation = args.situation or rng.choice(sorted(setting.affords))
    if situation not in SITUATIONS:
        raise StoryError("Unknown situation.")
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(["Mina", "Lila", "Nora", "Ruby", "Owen", "Eli", "Theo", "Finn"])
    if situation not in setting.affords:
        raise StoryError("That situation does not fit this place.")
    return StoryParams(place=place, situation=situation, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


CURATED = [
    StoryParams(place="kitchen", situation="bandage", name="Mina", gender="girl", parent="mother"),
    StoryParams(place="clinic", situation="bandage", name="Owen", gender="boy", parent="father"),
    StoryParams(place="garden", situation="soup", name="Ruby", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        for row in vals:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

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
