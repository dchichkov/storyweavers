#!/usr/bin/env python3
"""
A small mystery storyworld about a wakened dancer, a misplaced poop stain,
and an arabesque rehearsal that turns into problem solving and reconciliation.

The world is intentionally compact:
- one child protagonist
- one small setting
- one mysterious problem
- one practical fix
- one ending that proves the change

The style stays close to a gentle mystery: something odd is found, clues are
followed, a misunderstanding is cleared up, and everyone ends reconciled.
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


@dataclass
class Setting:
    place: str = "the rehearsal room"


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


SETTINGS = {
    "studio": Setting(place="the rehearsal room"),
    "hall": Setting(place="the old dance hall"),
    "classroom": Setting(place="the after-school studio"),
}

GIRL_NAMES = ["Mia", "Lena", "Nora", "Ivy", "Sofia", "Ava"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Theo", "Eli", "Max"]
TRAITS = ["curious", "careful", "brave", "gentle", "quiet", "clever"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with a dance problem and a kind fix.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, name=name, gender=gender, parent=parent, trait=trait)


def _intro(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.memes.get('trait', 'small')} {hero.type} who loved the mystery of the stage."
    )
    world.say(
        f"Every evening, {hero.id} and {hero.pronoun('possessive')} {parent.label} came to {world.setting.place}."
    )


def _mystery(world: World, hero: Entity, parent: Entity, costume: Entity) -> None:
    hero.memes["curiosity"] = 1
    costume.meters["stained"] = 1
    hero.memes["worry"] = 1
    world.say(
        f"One dim afternoon, {hero.id} woke early from a nap and hurried into {world.setting.place}."
    )
    world.say(
        f"On the floor lay a strange little poop mark beside the practice mirror, right near {hero.pronoun('possessive')} arabesque shoes."
    )
    world.say(
        f"{hero.id} stared at the clue. '{hero.pronoun('subject').capitalize()} had to figure out how it got there,' {hero.pronoun('subject')} whispered."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label} did not shout; {parent.pronoun('subject')} only looked worried and said, 'Let's solve this together.'"
    )


def _problem_solving(world: World, hero: Entity, parent: Entity, costume: Entity) -> None:
    world.para()
    hero.memes["determination"] = 1
    world.say(
        f"{hero.id} crouched down and checked the floor like a tiny detective."
    )
    world.say(
        f"The clue was small, and the room smelled like cleaning soap. That meant the mess was fresh."
    )
    world.say(
        f"{hero.id} found a little trail of dusty paw prints by the open side door."
    )
    world.say(
        f"At once, {hero.id} understood: a sleepy kitten had wandered in after the room was left open."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label} brought a cloth, and together they cleaned the spot until the mirror shone again."
    )
    costume.meters["clean"] = 1


def _reconciliation(world: World, hero: Entity, parent: Entity, costume: Entity) -> None:
    world.para()
    hero.memes["relief"] = 1
    hero.memes["reconciliation"] = 1
    parent.memes["reconciliation"] = 1
    world.say(
        f"Then {hero.id} felt the tight feeling in {hero.pronoun('possessive')} chest fade away."
    )
    world.say(
        f"{hero.id} hugged {hero.pronoun('possessive')} {parent.label} and said, 'I'm glad we found the answer.'"
    )
    world.say(
        f"{parent.pronoun('subject').capitalize()} smiled and fixed {hero.pronoun('possessive')} hair before rehearsal."
    )
    world.say(
        f"Soon {hero.id} was back in {hero.pronoun('possessive')} arabesque, balanced and bright, while the room felt calm and safe again."
    )


def tell(setting: Setting, hero_name: str, hero_gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name))
    hero.memes["trait"] = trait
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    costume = world.add(Entity(id="costume", type="thing", label="dance costume", phrase="a neat dance costume"))

    _intro(world, hero, parent)
    _mystery(world, hero, parent, costume)
    _problem_solving(world, hero, parent, costume)
    _reconciliation(world, hero, parent, costume)

    world.facts.update(hero=hero, parent=parent, costume=costume)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a short mystery story for a young child about {hero.id} finding a strange mess at dance practice.",
        f"Tell a gentle story where {hero.id} discovers a poop clue, solves the problem, and makes up with {hero.pronoun('possessive')} parent.",
        "Write a child-friendly mystery with an arabesque, a clue, and a happy reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    return [
        QAItem(
            question=f"What strange thing did {hero.id} find in {world.setting.place}?",
            answer=f"{hero.id} found a small poop mark on the floor near the practice mirror.",
        ),
        QAItem(
            question=f"How did {hero.id} and {hero.pronoun('possessive')} {parent.label} solve the problem?",
            answer=f"They looked for clues, found paw prints by the side door, and cleaned the room together.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The misunderstanding was gone, the room was clean, and {hero.id} went back to an arabesque feeling calm and happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an arabesque?",
            answer="An arabesque is a ballet pose where a dancer balances on one leg and stretches the other leg behind them.",
        ),
        QAItem(
            question="Why do people look for clues in a mystery?",
            answer="People look for clues to figure out what happened when something confusing or surprising takes place.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making up after a worry or misunderstanding so people feel peaceful again.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% This world is tiny and deterministic; the ASP twin mirrors the key story tags.
story_tag(mystery).
story_tag(problem_solving).
story_tag(reconciliation).
story_word(waken).
story_word(poop).
story_word(arabesque).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("setting", "dance_room"),
            asp.fact("feature", "problem_solving"),
            asp.fact("feature", "reconciliation"),
            asp.fact("style", "mystery"),
            asp.fact("keyword", "waken"),
            asp.fact("keyword", "poop"),
            asp.fact("keyword", "arabesque"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show story_tag/1."))
    tags = sorted(set(asp.atoms(model, "story_tag")))
    expected = [("mystery",), ("problem_solving",), ("reconciliation",)]
    if tags == expected:
        print("OK: ASP twin matches the Python story tags.")
        return 0
    print(f"MISMATCH: {tags} != {expected}")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        params.name,
        params.gender,
        params.parent,
        params.trait,
    )
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
        print("== Prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== Story Q&A ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== World Q&A ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def _show_asp() -> None:
    print(asp_program("#show story_tag/1."))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        _show_asp()
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show story_tag/1."))
        print(sorted(set(asp.atoms(model, "story_tag"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="studio", name="Mia", gender="girl", parent="mother", trait="curious"),
            StoryParams(place="hall", name="Leo", gender="boy", parent="father", trait="careful"),
            StoryParams(place="classroom", name="Nora", gender="girl", parent="mother", trait="gentle"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
