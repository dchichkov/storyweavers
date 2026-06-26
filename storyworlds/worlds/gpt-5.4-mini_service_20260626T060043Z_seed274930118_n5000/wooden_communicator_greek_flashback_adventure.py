#!/usr/bin/env python3
"""
A small Adventure-style story world with flashback structure.

Premise:
A child explorer finds a wooden communicator and hears an old Greek clue
that pulls them into a flashback about a hidden path, a lost gate, and a safe
way to return with treasure.

The world is constraint-driven: the communicator must be wooden, the clue must
be Greek-themed, and the story must include a clear flashback that helps solve
the present problem.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the hill path"
    feature: str = "stone steps"
    weather: str = "warm"
    affords: set[str] = field(default_factory=set)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    material: str
    clue: str
    flashback: str
    risk: str
    resolves: str


@dataclass
class StoryParams:
    setting: str
    artifact: str
    hero_name: str
    hero_type: str
    companion_type: str
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
    "ruins": Setting(place="the old ruins", feature="broken columns", weather="bright", affords={"explore"}),
    "cave": Setting(place="the cave mouth", feature="echoing walls", weather="cool", affords={"explore"}),
    "harbor": Setting(place="the harbor path", feature="wooden docks", weather="windy", affords={"explore"}),
}

ARTIFACTS = {
    "communicator": Artifact(
        id="communicator",
        label="communicator",
        phrase="a wooden communicator",
        material="wooden",
        clue="a Greek message carved into the side",
        flashback="an old Greek map and a sailor's warning",
        risk="the trail could be lost in the dark",
        resolves="the right turn leads home",
    ),
}

GIRL_NAMES = ["Mina", "Iris", "Nora", "Lina", "Tess", "Ada"]
BOY_NAMES = ["Theo", "Milo", "Aris", "Leo", "Pax", "Niko"]


def _story_intro(hero: Entity, companion: Entity, setting: Setting, artifact: Artifact) -> str:
    return (
        f"{hero.id} was a curious little explorer who loved adventure. "
        f"{hero.pronoun().capitalize()} traveled with {companion.id} to {setting.place}, "
        f"where {setting.feature} watched over the path. "
        f"On the ground they found {artifact.phrase}, and {hero.id} held it carefully."
    )


def _story_turn(hero: Entity, companion: Entity, setting: Setting, artifact: Artifact) -> str:
    return (
        f"The communicator clicked, and {artifact.clue} glowed in the afternoon light. "
        f"{hero.id} did not understand it at first, so {hero.pronoun()} listened closely. "
        f"Then the sound pulled {hero.id} into a flashback: {artifact.flashback}. "
        f"In the flashback, the old path and the Greek clue had saved a lost traveler."
    )


def _story_resolution(hero: Entity, companion: Entity, setting: Setting, artifact: Artifact) -> str:
    return (
        f"{hero.id} came back to the present with a grin and followed the hint. "
        f"{hero.pronoun().capitalize()} turned at the second stone, and {companion.id} stayed close. "
        f"The wooden communicator had helped them choose safely, so they crossed {setting.place} "
        f"without getting lost. By sunset, {artifact.resolves}, and the little explorers went home "
        f"with the wooden communicator tucked safely in {hero.pronoun('possessive')} bag."
    )


def build_story(world: World) -> str:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    setting = world.setting
    artifact = world.facts["artifact"]
    return "\n\n".join(
        [
            _story_intro(hero, companion, setting, artifact),
            _story_turn(hero, companion, setting, artifact),
            _story_resolution(hero, companion, setting, artifact),
        ]
    )


def generation_prompts(world: World) -> list[str]:
    artifact = world.facts["artifact"]
    setting = world.setting
    hero = world.facts["hero"]
    return [
        f"Write an adventure story for a child who finds {artifact.phrase} at {setting.place}.",
        f"Tell a story where {hero.id} hears a Greek clue and uses a flashback to solve a problem.",
        f"Create a short adventure that includes a wooden communicator and ends with a safe return home.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    artifact = world.facts["artifact"]
    setting = world.setting
    return [
        QAItem(
            question=f"What did {hero.id} find at {setting.place}?",
            answer=f"{hero.id} found {artifact.phrase} at {setting.place}.",
        ),
        QAItem(
            question=f"What kind of message did the communicator show?",
            answer=f"It showed {artifact.clue}, which was a Greek clue.",
        ),
        QAItem(
            question=f"Why did the story include a flashback?",
            answer=(
                f"The flashback showed {artifact.flashback}, and that helped {hero.id} "
                f"understand how to use the clue in the present."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} and {companion.id} get home safely?",
            answer=(
                f"They followed the clue from the wooden communicator, turned at the right place, "
                f"and crossed {setting.place} without getting lost."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a communicator?",
            answer="A communicator is something that carries a message or lets people send a message to one another.",
        ),
        QAItem(
            question="What does wooden mean?",
            answer="Wooden means made from wood, like a tree-based material.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a scene that goes back to an earlier time so the reader can learn something important.",
        ),
        QAItem(
            question="What is Greek?",
            answer="Greek can mean something from Greece, including the Greek language, stories, and old symbols.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} label={e.label}")
    return "\n".join(lines)


def explain_reasonableness(setting: Setting, artifact: Artifact) -> None:
    if "explore" not in setting.affords:
        raise StoryError("This setting does not support the adventure premise.")
    if artifact.material != "wooden":
        raise StoryError("The seed requires a wooden communicator.")
    if "Greek" not in artifact.clue and "Greek" not in artifact.flashback:
        raise StoryError("The seed requires a Greek clue or Greek flashback.")


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sname, setting in SETTINGS.items():
        for aname, art in ARTIFACTS.items():
            try:
                explain_reasonableness(setting, art)
            except StoryError:
                continue
            out.append((sname, aname))
    return out


ASP_RULES = r"""
setting_ok(S) :- setting(S), affords(S, explore).
artifact_ok(A) :- artifact(A), wooden(A), greek(A).
valid(S,A) :- setting_ok(S), artifact_ok(A).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sname, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sname))
        for aff in sorted(setting.affords):
            lines.append(asp.fact("affords", sname, aff))
    for aname, art in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aname))
        lines.append(asp.fact("wooden", aname))
        lines.append(asp.fact("greek", aname))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world with flashback and a wooden communicator.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"], dest="hero_type")
    ap.add_argument("--companion-type", choices=["girl", "boy"], dest="companion_type")
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
    artifact = args.artifact or rng.choice(list(ARTIFACTS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    companion_type = args.companion_type or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if hero_type == "girl" else BOY_NAMES
    hero_name = args.name or rng.choice(name_pool)
    explain_reasonableness(SETTINGS[setting], ARTIFACTS[artifact])
    return StoryParams(
        setting=setting,
        artifact=artifact,
        hero_name=hero_name,
        hero_type=hero_type,
        companion_type=companion_type,
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    artifact = ARTIFACTS[params.artifact]
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    companion_name = "Nia" if params.companion_type == "girl" else "Oren"
    if companion_name == hero.id:
        companion_name = "Oren" if companion_name != "Oren" else "Nia"
    companion = world.add(Entity(id=companion_name, kind="character", type=params.companion_type))
    world.facts["hero"] = hero
    world.facts["companion"] = companion
    world.facts["artifact"] = artifact
    story = build_story(world)
    return StorySample(
        params=params,
        story=story,
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

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for s in SETTINGS:
            for a in ARTIFACTS:
                try:
                    params = StoryParams(setting=s, artifact=a, hero_name="Mina", hero_type="girl", companion_type="boy")
                    samples.append(generate(params))
                except StoryError:
                    pass
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            i += 1
            seed = base_seed + i
            try:
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
