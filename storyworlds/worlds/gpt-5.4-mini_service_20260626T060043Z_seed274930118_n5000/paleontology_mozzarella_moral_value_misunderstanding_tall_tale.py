#!/usr/bin/env python3
"""
Standalone storyworld: a tall tale of paleontology, mozzarella, a misunderstanding,
and a moral value learned the hard way.

A small source-tale seed:
- A young fossil hunter wants to help at a dig.
- A shiny white "bone" turns out to be mozzarella.
- The misunderstanding causes a scramble and a moral lesson about telling the truth,
  checking carefully, and respecting other people's work.

The world stays tiny, classical, and state-driven: a child-sized cast, a few
physical objects, and emotional changes that drive the prose.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the dusty museum yard"
    afford: str = "dig"


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    type: str
    material: str
    risk: str
    value: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "yard": Setting(place="the dusty museum yard", afford="dig"),
    "badlands": Setting(place="the windy badlands", afford="dig"),
    "hill": Setting(place="the sun-baked hill", afford="dig"),
}

CHARACTER_TRAITS = ["brave", "curious", "lively", "stubborn", "cheerful", "bold"]
BOY_NAMES = ["Finn", "Milo", "Theo", "Jack", "Leo", "Eli"]
GIRL_NAMES = ["Luna", "Mia", "Ada", "Nora", "Zoe", "Ivy"]

ARTIFACTS = {
    "fossil": Artifact(
        id="fossil",
        label="fossil",
        phrase="a rare fossil",
        type="fossil",
        material="stone",
        risk="broken",
        value="respect for careful work",
    ),
    "skull": Artifact(
        id="skull",
        label="skull",
        phrase="an old skull-shaped fossil",
        type="fossil",
        material="stone",
        risk="scratched",
        value="truth",
    ),
    "shell": Artifact(
        id="shell",
        label="shell",
        phrase="a delicate shell fossil",
        type="fossil",
        material="stone",
        risk="dusted",
        value="patience",
    ),
}

TREATS = {
    "mozzarella": {
        "label": "mozzarella",
        "phrase": "a soft white ball of mozzarella",
        "risk": "squashed",
        "value": "honesty",
    }
}

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    artifact: str
    treat: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
class TaleWorld(World):
    pass


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _set_meter(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = value


def _add_meter(ent: Entity, key: str, value: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + value


def _add_meme(ent: Entity, key: str, value: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + value


def build_scene(params: StoryParams) -> TaleWorld:
    setting = SETTINGS[params.place]
    art = ARTIFACTS[params.artifact]
    treat = TREATS[params.treat]

    world = TaleWorld(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"dust": 0.0},
        memes={"wonder": 1.0, "misunderstanding": 0.0, "guilt": 0.0, "joy": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        meters={"dust": 0.0},
        memes={"patience": 1.0, "alarm": 0.0, "warmth": 0.0},
    ))
    mentor = world.add(Entity(
        id="Mentor",
        kind="character",
        type="man",
        label="old Professor Brindle",
        meters={"dust": 0.0},
        memes={"care": 1.0, "pride": 0.0, "moral_value": 0.0},
    ))
    artifact = world.add(Entity(
        id="artifact",
        kind="thing",
        type=art.type,
        label=art.label,
        phrase=art.phrase,
        owner="Mentor",
        caretaker="Mentor",
        meters={"cleanliness": 1.0, "value": 1.0},
        memes={"importance": 1.0},
    ))
    mozzarella = world.add(Entity(
        id="mozzarella",
        kind="thing",
        type="food",
        label=treat["label"],
        phrase=treat["phrase"],
        owner=params.name,
        caretaker=params.name,
        meters={"softness": 1.0, "messiness": 0.0},
        memes={"temptation": 1.0},
    ))
    world.facts.update(hero=hero, parent=parent, mentor=mentor, artifact=artifact, mozzarella=mozzarella, art=art, treat=treat)
    return world


def tell(world: TaleWorld) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    mentor: Entity = f["mentor"]
    artifact: Entity = f["artifact"]
    mozzarella: Entity = f["mozzarella"]
    art: Artifact = f["art"]
    treat = f["treat"]

    _add_meme(hero, "wonder", 1.0)
    world.say(
        f"{hero.id} was a {random.choice(['little', 'young'])} {random.choice(CHARACTER_TRAITS)} {hero.type} "
        f"who loved the tall tales of paleontology."
    )
    world.say(
        f"At the {world.setting.place}, {mentor.label} guarded {artifact.phrase} and told "
        f"stories so big they seemed to shake the clouds."
    )
    world.say(
        f"{hero.id} also carried {treat['phrase']} in a cloth wrap, and the smell of mozzarella "
        f"made the whole day feel like lunch and adventure together."
    )

    world.para()
    world.say(
        f"One bright day, {hero.id} saw a pale white lump in the dirt and gasped, "
        f'"A bone! A bone from a giant!"'
    )
    _add_meme(hero, "misunderstanding", 1.0)
    _add_meme(parent, "alarm", 1.0)
    _add_meter(hero, "dust", 1.0)
    _add_meter(artifact, "cleanliness", -0.5)

    world.say(
        f"{hero.id} scooped it up without looking close, because {hero.pronoun('subject')} thought "
        f"the shiny bit might belong in a museum case."
    )
    world.say(
        f"But it was only {mozzarella.phrase}, left near the dig by mistake, and the soft cheese "
        f"smudged onto {hero.pronoun('possessive')} hands."
    )
    _add_meter(mozzarella, "messiness", 1.0)
    _add_meme(mentor, "alarm", 1.0)

    world.para()
    world.say(
        f'"Hold on now," said {mentor.label}, lifting a finger like a flagpole. '
        f'"A good fossil hunter checks first. The truth is better than a guess."'
    )
    _add_meme(mentor, "moral_value", 1.0)
    _add_meme(hero, "guilt", 1.0)
    _add_meme(parent, "warmth", 0.5)

    world.say(
        f"{hero.id} looked down, blushed red as a sunset barn, and admitted, "
        f'"It was mozzarella, not a bone."'
    )
    world.say(
        f"{parent.label} laughed softly, because the mistake was silly, not mean, and {hero.id} had "
        f"told the truth before the story could grow any taller."
    )
    _set_meter(artifact, "cleanliness", 1.0)
    _add_meme(hero, "joy", 1.0)
    _add_meme(mentor, "pride", 1.0)
    _set_meter(hero, "dust", 0.0)

    world.para()
    world.say(
        f"After that, {hero.id} brushed the dirt from {hero.pronoun('possessive')} sleeves, set the "
        f"mozzarella back in a lunch basket, and helped {mentor.label} label the real fossil."
    )
    world.say(
        f"The little dig went on under the wide sky, and the moral stood taller than a windmill: "
        f"look carefully, tell the truth, and respect the work before you grab it."
    )

    world.facts["resolved"] = True
    world.facts["moral"] = "look carefully, tell the truth, and respect the work before you grab it"


def build_story(params: StoryParams) -> TaleWorld:
    world = build_scene(params)
    tell(world)
    return world


# ---------------------------------------------------------------------------
# QA and prompts
# ---------------------------------------------------------------------------
def generation_prompts(world: TaleWorld) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    art: Artifact = f["art"]
    return [
        f'Write a tall tale for a young child about paleontology and {f["treat"]["label"]}.',
        f"Tell a story where {hero.id} mistakes {f['treat']['phrase']} for {art.phrase} and learns a moral lesson.",
        f"Write a gentle, funny tale about a misunderstanding at a dig site that ends with truth and care.",
    ]


def story_qa(world: TaleWorld) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    mentor: Entity = f["mentor"]
    artifact: Entity = f["artifact"]
    mozzarella: Entity = f["mozzarella"]
    art: Artifact = f["art"]
    return [
        QAItem(
            question=f"What did {hero.id} think the mozzarella was at the dig?",
            answer=f"{hero.id} thought it was {artifact.phrase}, but it was really {mozzarella.phrase}.",
        ),
        QAItem(
            question=f"Why did the {mentor.label} stop the child and speak firmly?",
            answer=(
                f"The {mentor.label} stopped the child because a good paleontology worker must check carefully. "
                f"The mistake was a misunderstanding, and the truth mattered more than a guess."
            ),
        ),
        QAItem(
            question=f"What moral lesson did the story teach at the end?",
            answer=(
                f"The story taught that children should look carefully, tell the truth, and respect other people's work "
                f"before they grab something that might not be theirs."
            ),
        ),
        QAItem(
            question=f"How did {parent.label} react when the mistake was explained?",
            answer=f"{parent.label.capitalize()} laughed softly, because the mistake was silly and {hero.id} was honest about it.",
        ),
    ]


def world_knowledge_qa(world: TaleWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is paleontology?",
            answer="Paleontology is the study of fossils and old life from long ago.",
        ),
        QAItem(
            question="What is a fossil?",
            answer="A fossil is a trace or remains of something that lived long ago, often preserved in rock.",
        ),
        QAItem(
            question="What is mozzarella?",
            answer="Mozzarella is a soft cheese that can be white, stretchy, and very mild.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks one thing is true, but the real answer is different.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is an important rule about how to treat people well, like honesty and kindness.",
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


def dump_trace(world: TaleWorld) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind}/{e.type} " + " ".join(bits))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/4.

place(yard).
place(badlands).
place(hill).

artifact(fossil).
artifact(skull).
artifact(shell).

treat(mozzarella).

moral(honesty).
moral(care).
moral(respect).

valid_story(P, A, T, moral_value) :- place(P), artifact(A), treat(T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for a in ARTIFACTS:
        lines.append(asp.fact("artifact", a))
    for t in TREATS:
        lines.append(asp.fact("treat", t))
    lines.append(asp.fact("moral", "honesty"))
    lines.append(asp.fact("moral", "care"))
    lines.append(asp.fact("moral", "respect"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_stories())
    python_set = {(p, a, t, "moral_value") for p in SETTINGS for a in ARTIFACTS for t in TREATS}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    if clingo_set - python_set:
        print("Only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("Only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: paleontology and mozzarella.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--artifact", choices=ARTIFACTS.keys())
    ap.add_argument("--treat", choices=TREATS.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=CHARACTER_TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    artifact = args.artifact or rng.choice(list(ARTIFACTS.keys()))
    treat = args.treat or "mozzarella"
    if treat not in TREATS:
        raise StoryError("Unknown treat.")
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(CHARACTER_TRAITS)
    return StoryParams(place=place, artifact=artifact, treat=treat, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
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


def curated_samples() -> list[StoryParams]:
    return [
        StoryParams(place="yard", artifact="fossil", treat="mozzarella", name="Finn", gender="boy", parent="father", trait="curious"),
        StoryParams(place="badlands", artifact="shell", treat="mozzarella", name="Mia", gender="girl", parent="mother", trait="brave"),
        StoryParams(place="hill", artifact="skull", treat="mozzarella", name="Theo", gender="boy", parent="father", trait="bold"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in curated_samples()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} / {p.artifact} / {p.treat}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
