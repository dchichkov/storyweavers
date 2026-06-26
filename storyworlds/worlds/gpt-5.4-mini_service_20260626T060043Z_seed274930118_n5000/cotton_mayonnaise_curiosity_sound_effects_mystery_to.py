#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/cotton_mayonnaise_curiosity_sound_effects_mystery_to.py
================================================================================================

A small detective-style storyworld about curiosity, sound effects, and a mystery
to solve. The core seed words are cotton and mayonnaise.

Premise:
- A child detective notices a cotton item has been splashed with mayonnaise.
- Strange sound effects point toward a small kitchen mystery.
- Curiosity helps the child follow clues and solve it.

The world is kept intentionally small and classical:
- one setting,
- a few entities,
- physical state on meters,
- emotional state on memes,
- a clear turn from mystery to solution.

The story is generated from world state, not from a frozen paragraph template.
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
    kind: str = "thing"          # "character" | "thing"
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
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"


@dataclass
class Mystery:
    id: str
    clue_sound: str
    culprit_sound: str
    explanation: str
    mess: str = "sticky"


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen"),
    "pantry": Setting(place="the pantry"),
    "dining_room": Setting(place="the dining room"),
}

MYSTERIES = {
    "mayonnaise_spill": Mystery(
        id="mayonnaise_spill",
        clue_sound="plip",
        culprit_sound="clink",
        explanation="the mayonnaise jar had tipped over beside the cotton napkin",
        mess="sticky mayonnaise",
    ),
    "sandwich_splatter": Mystery(
        id="sandwich_splatter",
        clue_sound="squish",
        culprit_sound="rustle",
        explanation="someone had packed a sandwich too fast and mayonnaise smeared onto the cotton cloth",
        mess="sticky mayonnaise",
    ),
}

GIRL_NAMES = ["Nina", "Maya", "Ruby", "Lena", "Ivy", "Clara"]
BOY_NAMES = ["Theo", "Max", "Eli", "Finn", "Owen", "Leo"]
TRAITS = ["curious", "careful", "brave", "sharp-eyed", "quiet", "witty"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def _mem(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def _add_meter(entity: Entity, key: str, amount: float) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def _add_mem(entity: Entity, key: str, amount: float) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def _set_mem(entity: Entity, key: str, value: float) -> None:
    entity.memes[key] = value


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes.get('trait_word', 'curious')} detective who noticed every tiny clue."
    )


def set_scene(world: World, hero: Entity, parent: Entity, mystery: Mystery, napkin: Entity) -> None:
    world.say(
        f"One day in {world.setting.place}, {hero.id} found a cotton napkin with a blob of mayonnaise on it."
    )
    world.say(
        f"The white cotton looked wrong, and the sticky spot made {hero.id} squint and listen."
    )


def follow_sounds(world: World, hero: Entity, mystery: Mystery) -> None:
    _add_mem(hero, "curiosity", 1)
    _add_mem(hero, "focus", 1)
    world.say(
        f"Then came a tiny {mystery.clue_sound}-sound, followed by a soft {mystery.culprit_sound}-sound from deeper in the room."
    )
    world.say(
        f"{hero.pronoun().capitalize()} tipped {hero.pronoun('possessive')} head, because curious detectives do not ignore sound effects."
    )


def investigate(world: World, hero: Entity, parent: Entity, mystery: Mystery, napkin: Entity, jar: Entity) -> None:
    _add_mem(hero, "curiosity", 1)
    _add_mem(hero, "bravery", 1)
    _add_mem(parent, "worry", 1)
    world.say(
        f"{hero.id} looked at the cotton napkin, then at the mayonnaise jar, and began to solve the mystery."
    )
    world.say(
        f"{hero.pronoun().capitalize()} followed the sticky clue trail with careful steps."
    )
    if mystery.id == "mayonnaise_spill":
        jar.meters["tipped"] = 1
        napkin.meters["sticky"] = 1
        napkin.meters["dirty"] = 1
        _add_mem(parent, "relief_pending", 1)
        world.say(
            f"The clue trail ended beside the jar, and the answer was clear: {mystery.explanation}."
        )
    else:
        napkin.meters["dirty"] = 1
        world.say(
            f"The clue trail ended at a lunch plate, and the answer was clear: {mystery.explanation}."
        )


def resolve(world: World, hero: Entity, parent: Entity, napkin: Entity, mystery: Mystery) -> None:
    _add_mem(hero, "joy", 1)
    _add_mem(parent, "joy", 1)
    _set_mem(hero, "curiosity", 0)
    napkin.meters["sticky"] = 0
    napkin.meters["clean"] = 1
    world.say(
        f"{hero.id} smiled and told {parent.pronoun('object')} the answer."
    )
    world.say(
        f"Together they washed the cotton napkin until the mayonnaise was gone."
    )
    world.say(
        f"At the end, the room felt calm again, and the little detective had solved the mystery with ears, patience, and curiosity."
    )


def tell(setting: Setting, mystery: Mystery, hero_name: str, hero_type: str, hero_traits: list[str], parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        memes={"trait_word": hero_traits[0] if hero_traits else "curious"},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="parent",
    ))
    napkin = world.add(Entity(
        id="Napkin",
        type="napkin",
        label="cotton napkin",
        phrase="a cotton napkin",
        owner=parent.id,
        caretaker=parent.id,
    ))
    jar = world.add(Entity(
        id="Jar",
        type="jar",
        label="mayonnaise jar",
        phrase="a jar of mayonnaise",
        owner=parent.id,
    ))

    introduce(world, hero)
    world.para()
    set_scene(world, hero, parent, mystery, napkin)
    follow_sounds(world, hero, mystery)
    world.para()
    investigate(world, hero, parent, mystery, napkin, jar)
    resolve(world, hero, parent, napkin, mystery)

    world.facts.update(
        hero=hero,
        parent=parent,
        napkin=napkin,
        jar=jar,
        mystery=mystery,
        setting=setting,
    )
    return world


def valid_combos() -> list[tuple[str, str]]:
    return [("kitchen", "mayonnaise_spill"), ("pantry", "sandwich_splatter"), ("dining_room", "sandwich_splatter")]


@dataclass
class RegistryRow:
    setting: str
    mystery: str


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    return [
        f'Write a short detective story for a child about {hero.id}, cotton, and mayonnaise.',
        f"Tell a gentle mystery where {hero.id} hears a {mystery.clue_sound} and follows the sound to solve the problem.",
        "Write a small, cozy detective story with a sticky clue, a careful child, and a clear answer at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    napkin = f["napkin"]
    mystery = f["mystery"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What did {hero.id} find in {setting.place}?",
            answer=f"{hero.id} found a cotton napkin with mayonnaise on it.",
        ),
        QAItem(
            question=f"What made {hero.id} curious about the mystery?",
            answer=f"A tiny {mystery.clue_sound}-sound and a soft {mystery.culprit_sound}-sound made {hero.id} listen closely.",
        ),
        QAItem(
            question=f"What was the answer to the mystery?",
            answer=f"The answer was that {mystery.explanation}.",
        ),
        QAItem(
            question=f"How did the story end for the cotton napkin?",
            answer=f"The cotton napkin was washed clean, and the sticky mayonnaise was gone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is cotton?",
            answer="Cotton is a soft plant fiber that people use to make cloth and clothes.",
        ),
        QAItem(
            question="What is mayonnaise?",
            answer="Mayonnaise is a thick, creamy sauce often used in sandwiches and salads.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a problem or secret that needs clues and careful thinking to solve.",
        ),
        QAItem(
            question="Why do detectives pay attention to sound effects?",
            answer="Detectives listen for little sounds because sounds can be clues that help explain what happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_sound", mid, m.clue_sound))
        lines.append(asp.fact("culprit_sound", mid, m.culprit_sound))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S, M) :- setting(S), mystery(M).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective-story world about cotton, mayonnaise, and curiosity.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.setting and args.mystery:
        if (args.setting, args.mystery) not in valid_combos():
            raise StoryError("That setting and mystery do not make a strong detective story together.")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    mystery = args.mystery or rng.choice([m for s, m in valid_combos() if s == setting])
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], params.name, params.gender, [params.trait], params.parent)
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
    StoryParams(setting="kitchen", mystery="mayonnaise_spill", name="Nina", gender="girl", parent="mother", trait="curious"),
    StoryParams(setting="pantry", mystery="sandwich_splatter", name="Theo", gender="boy", parent="father", trait="witty"),
    StoryParams(setting="dining_room", mystery="sandwich_splatter", name="Ruby", gender="girl", parent="mother", trait="sharp-eyed"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
