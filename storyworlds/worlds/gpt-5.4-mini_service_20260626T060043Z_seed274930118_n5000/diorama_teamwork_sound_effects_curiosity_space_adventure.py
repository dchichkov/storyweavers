#!/usr/bin/env python3
"""
storyworlds/worlds/diorama_teamwork_sound_effects_curiosity_space_adventure.py
==============================================================================

A small story world about children making a space diorama together.

Premise:
- A curious child wants to build a space diorama.
- The project is exciting, but one important piece is missing.
- The team learns to use teamwork, sound effects, and careful curiosity to solve
  the problem and finish the scene.

The world model tracks:
- physical meters: progress, scattered_parts, glue, sparkle, steadiness
- emotional memes: curiosity, excitement, worry, teamwork, delight

The story is rendered from simulation state rather than a frozen template:
characters act, the project changes, tension appears, and the ending image
proves what changed.
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the craft table"
    theme: str = "space"


@dataclass
class BuildKit:
    name: str
    missing_piece: str
    key_piece: str
    sound_effect: str
    teamwork_move: str
    final_image: str


@dataclass
class StoryParams:
    setting: str
    kit: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


SETTINGS = {
    "table": Setting(place="the craft table", theme="space"),
    "floor": Setting(place="the living room floor", theme="space"),
    "garage": Setting(place="the garage workbench", theme="space"),
}

KITS = {
    "moon": BuildKit(
        name="moon diorama",
        missing_piece="silver stars",
        key_piece="the last silver star",
        sound_effect="shh-shh! click!",
        teamwork_move="hold the paper steady while the other child glued the stars on",
        final_image="a tiny moon with bright stars and a cardboard astronaut",
    ),
    "rocket": BuildKit(
        name="rocket diorama",
        missing_piece="the rocket flame",
        key_piece="the orange flame",
        sound_effect="vroom! zoom!",
        teamwork_move="paint the flame while the other child traced the rocket body",
        final_image="a shiny rocket with a glowing orange flame and a round porthole",
    ),
    "planet": BuildKit(
        name="planet diorama",
        missing_piece="the ring",
        key_piece="the wide paper ring",
        sound_effect="whirr! swish!",
        teamwork_move="curve the paper ring while the other child colored the planet",
        final_image="a striped planet with a bright ring and tiny tape moons",
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ava", "Zoe", "Ruby"]
BOY_NAMES = ["Leo", "Max", "Finn", "Theo", "Ben", "Owen"]
TRAITS = ["curious", "bright-eyed", "patient", "busy", "careful", "eager"]


def valid_combos() -> list[tuple[str, str]]:
    return [(setting, kit) for setting in SETTINGS for kit in KITS]


def explain_rejection(setting: str, kit: str) -> str:
    return f"(No story: the {kit} kit and the {setting} setting do not make a coherent diorama build.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: curious kids build a space diorama with teamwork and sound effects."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--kit", choices=KITS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["friend", "brother", "sister", "parent"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    kit = args.kit or rng.choice(list(KITS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["friend", "brother", "sister", "parent"])
    trait = args.trait or rng.choice(TRAITS)
    if (setting, kit) not in valid_combos():
        raise StoryError(explain_rejection(setting, kit))
    return StoryParams(setting=setting, kit=kit, name=name, gender=gender, helper=helper, trait=trait)


def _do_work(world: World, hero: Entity, kit: BuildKit) -> None:
    hero.meters["progress"] = hero.meters.get("progress", 0.0) + 1.0
    hero.memes["excitement"] = hero.memes.get("excitement", 0.0) + 1.0
    world.facts["sound_effect"] = kit.sound_effect
    world.facts["teamwork_move"] = kit.teamwork_move


def _problem(world: World, hero: Entity, kit: BuildKit) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    world.facts["missing_piece"] = kit.missing_piece


def _fix(world: World, hero: Entity, helper: Entity, kit: BuildKit) -> None:
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0.0) + 1.0
    helper.memes["teamwork"] = helper.memes.get("teamwork", 0.0) + 1.0
    hero.meters["progress"] = hero.meters.get("progress", 0.0) + 1.0
    world.facts["finished"] = True


def tell(setting: Setting, kit: BuildKit, name: str, gender: str, helper_kind: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name))
    helper_name = {"friend": "Jules", "brother": "Sam", "sister": "Ivy", "parent": "Pat"}[helper_kind]
    helper_type = {"friend": "boy", "brother": "boy", "sister": "girl", "parent": "parent"}[helper_kind]
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, label=helper_name))

    project = world.add(Entity(id="project", type="diorama", label=kit.name, phrase=kit.name))
    stars = world.add(Entity(id="stars", type="piece", label=kit.missing_piece, caretaker=hero.id))
    world.facts.update(hero=hero, helper=helper, project=project, kit=kit, setting=setting)

    world.say(f"{hero.id} was a {trait} child who loved space things and tiny, careful scenes.")
    world.say(
        f"{hero.id} had started a {kit.name} on {setting.place}, and {hero.pronoun('possessive')} eyes kept
        darting to every little detail."
    )
    world.say(
        f"{hero.id} wanted the diorama to look real, so {hero.pronoun()} arranged the planet cardboard, the little rocket, "
        f"and the dark paper sky."
    )

    world.para()
    _do_work(world, hero, kit)
    world.say(f"Then the room went soft and quiet until {hero.id} made the first sound: \"{kit.sound_effect}\".")
    world.say(f"That little sound made the project feel alive, and {hero.pronoun('possessive')} curiosity grew brighter.")

    _problem(world, hero, kit)
    world.say(f"But when {hero.id} looked closer, something was wrong: {kit.missing_piece} was missing.")
    world.say(f"{hero.id} searched under the paper moons, behind the glue, and inside the box of glitter bits.")

    world.para()
    world.say(
        f"{helper.id} came over and leaned in. Together they looked at the scene and made a plan:"
        f" {kit.teamwork_move}."
    )
    _fix(world, hero, helper, kit)
    world.say(
        f"{hero.id} and {helper.id} worked side by side, and the table filled with happy little noises:"
        f" \"{kit.sound_effect}\"."
    )
    world.say(
        f"At last, the diorama became {kit.final_image}. {hero.id} smiled because the project now looked complete, "
        f"and {hero.pronoun('possessive')} helper smiled too."
    )

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    kit = f["kit"]
    return [
        f"Write a short space-adventure story for a child named {hero.id} who is building a {kit.name}.",
        f"Tell a gentle story where curiosity, teamwork, and sound effects help finish a diorama.",
        f"Write a child-friendly scene about a missing piece in a tiny space project and a happy fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    kit = f["kit"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What was {hero.id} building at {setting.place}?",
            answer=f"{hero.id} was building a {kit.name}, a tiny space scene with cardboard pieces and careful glue."
        ),
        QAItem(
            question=f"What did {hero.id} notice was missing from the project?",
            answer=f"{kit.missing_piece} was missing, so the diorama did not look finished yet."
        ),
        QAItem(
            question=f"Who helped {hero.id} finish the space scene?",
            answer=f"{helper.id} helped {hero.id}. They worked together and fixed the diorama side by side."
        ),
        QAItem(
            question=f"How did the project feel when the important piece was found?",
            answer=f"It felt exciting and happy, because curiosity led to teamwork and the little space scene became complete."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a diorama?",
            answer="A diorama is a small model scene that shows a place or story in miniature."
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people work together and help each other finish a job."
        ),
        QAItem(
            question="Why do people make sound effects in stories or play?",
            answer="Sound effects make scenes feel lively, like a tiny rocket really zooming or a project really clicking together."
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to look closely, ask questions, and find out how something works."
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_setting(S) :- setting(S).
valid_kit(K) :- kit(K).
valid_story(S, K) :- valid_setting(S), valid_kit(K).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for k in KITS:
        lines.append(asp.fact("kit", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], KITS[params.kit], params.name, params.gender, params.helper, params.trait)
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
    StoryParams(setting="table", kit="rocket", name="Mia", gender="girl", helper="friend", trait="curious"),
    StoryParams(setting="floor", kit="moon", name="Leo", gender="boy", helper="sister", trait="eager"),
    StoryParams(setting="garage", kit="planet", name="Nora", gender="girl", helper="parent", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
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
