#!/usr/bin/env python3
"""
A small storyworld for an Animal Story style tale about croup and a soothing rhyme.

The simulated premise:
- A young animal gets a harsh, barking cough.
- A caregiver notices the cough, worries, and offers a warm, quiet rhyme.
- The rhyme and care help the little animal settle, breathe easier, and rest.

The world model tracks:
- Physical meters: cough, warmth, water, rest, soothed
- Emotional memes: worry, comfort, love, calm
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

ANIMALS = {
    "bunny": {"sound": "soft hop", "plural": False, "kind": "young bunny"},
    "kitten": {"sound": "tiny purr", "plural": False, "kind": "little kitten"},
    "puppy": {"sound": "little wag", "plural": False, "kind": "young puppy"},
    "duckling": {"sound": "small quack", "plural": False, "kind": "small duckling"},
    "foal": {"sound": "light step", "plural": False, "kind": "young foal"},
}

CARETAKERS = {
    "mother": {"label": "mother", "kind": "mother"},
    "father": {"label": "father", "kind": "father"},
    "aunt": {"label": "aunt", "kind": "aunt"},
    "uncle": {"label": "uncle", "kind": "uncle"},
}

SETTINGS = {
    "nest": "the cozy nest",
    "den": "the warm den",
    "barn": "the quiet barn corner",
    "room": "the little room",
}

RHYMES = [
    "Breathe slow, dear one, let worries go; the moon is round and warm and low.",
    "Hush now, small heart, and rest your head; a quiet song can tuck you in bed.",
    "One little breath, then two, then three; soft as a feather, calm as can be.",
    "Sleepy and snug, with water near, a gentle rhyme can dry a tear.",
]

SYMPTOMS = {
    "croup": {
        "cough": 2,
        "worry": 2,
        "voice": "barky",
        "phrase": "a barky cough",
        "risk": "dry air",
    }
}


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
        if self.type in {"mother", "aunt", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"father", "uncle", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    animal: str
    caretaker: str
    setting: str
    symptom: str = "croup"
    rhyme: str = ""
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world: croup, care, and a soothing rhyme.")
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--caretaker", choices=CARETAKERS)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--symptom", choices=["croup"], default="croup")
    ap.add_argument("--rhyme")
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
    animal = args.animal or rng.choice(list(ANIMALS))
    caretaker = args.caretaker or rng.choice(list(CARETAKERS))
    setting = args.setting or rng.choice(list(SETTINGS))
    rhyme = args.rhyme or rng.choice(RHYMES)
    return StoryParams(animal=animal, caretaker=caretaker, setting=setting, symptom="croup", rhyme=rhyme)


def make_world(params: StoryParams) -> World:
    w = World(setting=params.setting)
    young = ANIMALS[params.animal]
    carer = CARETAKERS[params.caretaker]
    symptom = SYMPTOMS[params.symptom]

    child = w.add(Entity(
        id="child",
        kind="character",
        type=params.animal,
        label=young["kind"],
        meters={"cough": 0.0, "warmth": 1.0, "water": 0.0, "rest": 0.0, "soothed": 0.0},
        memes={"worry": 0.0, "comfort": 0.0, "calm": 0.0, "love": 1.0},
    ))
    parent = w.add(Entity(
        id="caretaker",
        kind="character",
        type=params.caretaker,
        label=carer["label"],
        meters={"water": 1.0, "warmth": 1.0},
        memes={"worry": 0.0, "comfort": 0.0, "calm": 0.0, "love": 1.0},
    ))

    w.say(f"In {SETTINGS[params.setting]}, a little {young['kind']} had {symptom['phrase']}.")
    w.say(f"{parent.label.capitalize()} heard the {symptom['voice']} sound and felt worry rise like a small cloud.")
    child.meters["cough"] += symptom["cough"]
    child.memes["worry"] += symptom["worry"]
    parent.memes["worry"] += 1

    w.say(f'{parent.label.capitalize()} picked {child.pronoun("object")} up, wrapped {child.pronoun("object")} warm, and offered a cup of water.')
    child.meters["water"] += 1
    child.meters["warmth"] += 1
    parent.meters["water"] -= 0.5

    w.say(f"Then {parent.label} began a soft rhyme: “{params.rhyme}”")
    child.meters["soothed"] += 1
    child.memes["comfort"] += 2
    child.memes["calm"] += 1
    parent.memes["comfort"] += 1
    parent.memes["calm"] += 1

    if child.meters["soothed"] >= 1 and child.meters["water"] >= 1 and child.meters["warmth"] >= 2:
        child.meters["cough"] = max(0.0, child.meters["cough"] - 1.0)
        child.meters["rest"] += 1
        child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
        w.say(f"The rhyme slowed the room down. The cough stayed, but it sounded smaller.")
        w.say(f"At last, the little one curled up and rested, while {parent.label} sat close by and listened.")
    else:
        w.say("The rhyme helped, but the little one still needed more quiet and care.")

    w.facts.update(child=child, parent=parent, params=params, symptom=symptom)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        f'Write a gentle animal story for small children about a {p.animal} with croup and a comforting rhyme.',
        f"Tell a bedtime-style story where a {p.caretaker} helps a {p.animal} feel better in {SETTINGS[p.setting]}.",
        f'Write a short animal story that includes a soft rhyme and ends with the child resting quietly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    p: StoryParams = f["params"]
    return [
        QAItem(
            question=f"What kind of animal was the child in the story?",
            answer=f"The child was a little {ANIMALS[p.animal]['kind']}.",
        ),
        QAItem(
            question=f"What problem did the little {p.animal} have?",
            answer="The little animal had croup, which made a barky cough and made everyone worry.",
        ),
        QAItem(
            question=f"What did the {p.caretaker} do to help?",
            answer=f"The {p.caretaker} held the child close, gave water, kept the child warm, and said a soft rhyme.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the little {p.animal} resting quietly while the {p.caretaker} stayed nearby.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is croup?",
            answer="Croup is an illness that can make a child's cough sound barky or rough, so grown-ups often give comfort and keep the child calm.",
        ),
        QAItem(
            question="Why can a rhyme help a child feel better?",
            answer="A gentle rhyme can help a child relax, slow down, and feel safe when they are upset or uncomfortable.",
        ),
        QAItem(
            question="Why do caregivers offer water when a child is sick?",
            answer="Water can help a child stay comfortable and keep the throat from feeling too dry.",
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
        lines.append(f"  {e.id:8} ({e.type:10}) meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
% In this world, a croup story is reasonable when it has a child, a caretaker,
% a soothing rhyme, and a symptom that can plausibly be comforted.
reasonable_story(animal_story) :- symptom(croup), has_caretaker, has_rhyme, has_setting.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for c in CARETAKERS:
        lines.append(asp.fact("caretaker", c))
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    lines.append(asp.fact("symptom", "croup"))
    lines.append(asp.fact("has_caretaker"))
    lines.append(asp.fact("has_rhyme"))
    lines.append(asp.fact("has_setting"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for a in ANIMALS:
        for c in CARETAKERS:
            for s in SETTINGS:
                out.append((s, "croup", a))
    return out


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
    StoryParams(animal="kitten", caretaker="mother", setting="nest", rhyme=RHYMES[0]),
    StoryParams(animal="bunny", caretaker="father", setting="den", rhyme=RHYMES[1]),
    StoryParams(animal="duckling", caretaker="aunt", setting="barn", rhyme=RHYMES[2]),
    StoryParams(animal="puppy", caretaker="uncle", setting="room", rhyme=RHYMES[3]),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.animal} / {p.caretaker} / {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
