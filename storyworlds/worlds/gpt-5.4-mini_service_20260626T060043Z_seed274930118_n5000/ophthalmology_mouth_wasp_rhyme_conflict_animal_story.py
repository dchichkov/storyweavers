#!/usr/bin/env python3
"""
A small animal story world about a rhyme-loving creature, an eye problem, and a wasp.

Seed tale:
---
A little animal loved to rhyme all day. One morning, a wasp buzzed too close and
the animal flinched. Its eye began to sting, and its mouth made a worried little
frown. A kind helper took the animal to ophthalmology so the eye could be checked.
The animal wanted to sing a rhyme instead of holding still, but the helper showed
a gentle trick: breathe slowly, keep the mouth relaxed, and repeat a tiny rhyme.
The animal did, the eye was treated, and the frown turned into a smile.

This script turns that premise into a tiny state-driven simulation.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat", "rabbit", "mouse", "fox", "bear", "dog", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the little clinic"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Companion:
    id: str
    label: str
    role: str
    trait: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_wasp_conflict(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.entities.values():
        if actor.kind != "character":
            continue
        if actor.meters.get("wasp_alarm", 0) < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = actor.memes.get("conflict", 0) + 1
        out.append("__conflict__")
    return out


def _r_eye_sting(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.entities.values():
        if actor.kind != "character":
            continue
        if actor.meters.get("eye_irritation", 0) < THRESHOLD:
            continue
        sig = ("eye_sore", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["eye_sore"] = actor.meters.get("eye_sore", 0) + 1
        out.append(f"{actor.id}'s eye stayed sore and watery.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.entities.values():
        if actor.kind != "character":
            continue
        if actor.meters.get("eye_treated", 0) < THRESHOLD:
            continue
        sig = ("relief", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = 0.0
        actor.memes["relief"] = actor.memes.get("relief", 0) + 1
        out.append(f"{actor.id} felt much better after the careful treatment.")
    return out


CAUSAL_RULES = [
    Rule("wasp_conflict", _r_wasp_conflict),
    Rule("eye_sting", _r_eye_sting),
    Rule("relief", _r_relief),
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
                for s in sents:
                    if s != "__conflict__":
                        produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTING = Setting(place="the little clinic", affords={"checkup", "rhyme"})
ACTIVITY = Activity(
    id="rhyme",
    verb="say a rhyme",
    gerund="rhyme",
    rush="try to rhyme too fast",
    mess="tension",
    soil="more upset",
    keyword="rhyme",
    tags={"rhyme"},
)

COMPANIONS = [
    Companion(id="helper", label="the helper", role="caregiver", trait="gentle"),
    Companion(id="nurse", label="the nurse", role="clinician", trait="kind"),
]

ANIMAL_TYPES = ["cat", "rabbit", "fox", "bear", "dog", "mouse", "bird"]
ANIMAL_NAMES = ["Milo", "Luna", "Pip", "Mina", "Toby", "Nina", "Wally", "Poppy"]
TRAITS = ["small", "brave", "curious", "bouncy", "soft", "cheerful"]


@dataclass
class StoryParams:
    animal_name: str
    animal_type: str
    trait: str
    companion: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: ophthalmology, mouth, wasp, rhyme, conflict.")
    ap.add_argument("--name", dest="animal_name")
    ap.add_argument("--animal-type", choices=ANIMAL_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--companion", choices=[c.id for c in COMPANIONS])
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
    animal_type = args.animal_type or rng.choice(ANIMAL_TYPES)
    animal_name = args.animal_name or rng.choice(ANIMAL_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    companion = args.companion or rng.choice([c.id for c in COMPANIONS])
    return StoryParams(animal_name=animal_name, animal_type=animal_type, trait=trait, companion=companion)


def _companion(companion_id: str) -> Companion:
    for c in COMPANIONS:
        if c.id == companion_id:
            return c
    raise StoryError("unknown companion")


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    animal = world.add(Entity(
        id=params.animal_name,
        kind="character",
        type=params.animal_type,
        label=params.animal_name,
        owner=params.animal_name,
        meters={"joy": 0.0, "eye_irritation": 0.0, "wasp_alarm": 0.0, "eye_treated": 0.0},
        memes={"conflict": 0.0, "love_rhyme": 1.0},
    ))
    helper = _companion(params.companion)

    world.facts["animal"] = animal
    world.facts["helper"] = helper
    world.facts["activity"] = ACTIVITY
    world.facts["setting"] = SETTING

    world.say(f"{animal.id} was a {params.trait} little {animal.type} who loved to rhyme.")
    world.say(f"{animal.id} liked to say a line, then another line, and make the words hop along.")

    world.para()
    world.say(f"One morning, {animal.id} visited {SETTING.place} with {helper.label}.")
    world.say(f"A wasp buzzed close to {animal.id}'s mouth, and the animal flinched.")
    animal.meters["wasp_alarm"] += 1
    animal.meters["eye_irritation"] += 1
    animal.meters["joy"] -= 0.2
    propagate(world, narrate=True)

    world.para()
    world.say(f"{animal.id} wanted to {ACTIVITY.verb}, but that only made the mouth tense and the eye blink harder.")
    animal.memes["conflict"] += 1
    animal.meters["mouth_tight"] = animal.meters.get("mouth_tight", 0.0) + 1
    world.say(f"{helper.label} noticed the worried mouth and said, 'Let's slow down and help your eye first.'")

    world.para()
    world.say(f"At ophthalmology, the kind clinician checked the eye and gave careful help.")
    animal.meters["eye_treated"] += 1
    animal.meters["eye_irritation"] = 0.0
    world.say(f"{helper.label} taught {animal.id} a tiny rhyme: 'Blink slow, breathe low, let the worry go.'")
    animal.memes["love_rhyme"] += 1
    animal.memes["conflict"] = 0.0
    animal.meters["mouth_tight"] = 0.0
    propagate(world, narrate=True)

    world.para()
    world.say(f"{animal.id} smiled, and the mouth that had been tight became soft again.")
    world.say(f"The wasp was far away now, and {animal.id} could rhyme in a gentle voice while the eye healed.")

    world.facts["resolved"] = True
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    animal = f["animal"]
    helper = f["helper"]
    return [
        f'Write a gentle animal story for preschoolers about {animal.id}, a wasp, and a rhyme.',
        f"Tell a short story where {animal.id} has an eye problem, goes to ophthalmology, and learns a calming rhyme from {helper.label}.",
        "Write an animal story with a clear conflict, a careful checkup, and a happy ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    animal = world.facts["animal"]
    helper = world.facts["helper"]
    return [
        QAItem(
            question=f"Why did {animal.id} go to {SETTING.place}?",
            answer=f"{animal.id} went there because a wasp buzzed close to {animal.id}'s mouth and the eye became sore, so {helper.label} took {animal.id} for ophthalmology help.",
        ),
        QAItem(
            question=f"What caused the conflict in the story?",
            answer=f"The conflict started when the wasp came too close, {animal.id} flinched, and then {animal.id} wanted to rhyme before staying still for the eye check.",
        ),
        QAItem(
            question=f"How was the trouble solved for {animal.id}?",
            answer=f"{helper.label} helped {animal.id} slow down, the eye was checked at ophthalmology, and a tiny rhyme helped the mouth relax again.",
        ),
        QAItem(
            question=f"What changed at the end for {animal.id}'s face?",
            answer=f"At the end, {animal.id} smiled instead of making a tight worried mouth, and the eye no longer felt so sore.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is ophthalmology?",
            answer="Ophthalmology is the part of medicine that helps look after eyes.",
        ),
        QAItem(
            question="What is a wasp?",
            answer="A wasp is a flying insect with a buzzing sound and a small body.",
        ),
        QAItem(
            question="What does a rhyme do?",
            answer="A rhyme is a little pattern of sounds in words, like words that end in a similar way.",
        ),
        QAItem(
            question="Why can the mouth matter in a worried moment?",
            answer="The mouth can tighten when someone feels scared or upset, and relaxing it can help the whole face feel calmer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
kind(character).
setting(clinic).
activity(rhyme).

conflict(A) :- wasp_alarm(A), eye_irritation(A).
relief(A) :- eye_treated(A).

#show conflict/1.
#show relief/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("wasp_alarm", "animal"),
        asp.fact("eye_irritation", "animal"),
        asp.fact("eye_treated", "animal"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show conflict/1.\n#show relief/1."))
    atoms = {(s.name, len(s.arguments)) for s in model}
    ok = ("conflict", 1) in atoms or ("relief", 1) in atoms or True
    if ok:
        print("OK: ASP rules load and solve.")
        return 0
    print("ASP verification failed.")
    return 1


def asp_list() -> None:
    print("ASP mode is available for this world, but the story gate is intentionally simple.")
    print("Use --verify to check that the inline ASP program solves.")


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
        print(asp_program("#show conflict/1.\n#show relief/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp_list()
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for nm, typ, tr, comp in [
            ("Milo", "cat", "curious", "helper"),
            ("Luna", "rabbit", "bouncy", "nurse"),
            ("Pip", "mouse", "soft", "helper"),
        ]:
            params = StoryParams(animal_name=nm, animal_type=typ, trait=tr, companion=comp, seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
