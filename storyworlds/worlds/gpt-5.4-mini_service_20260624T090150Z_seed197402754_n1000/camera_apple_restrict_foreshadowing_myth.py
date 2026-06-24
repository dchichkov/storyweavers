#!/usr/bin/env python3
"""
A small mythic storyworld about a camera, an apple, and a restriction.

Premise:
A young keeper longs to use a camera to capture a sacred apple in an old grove.
An elder has set a restriction: the apple may not be photographed until the
right sign appears. The story builds a foreshadowing omen, the keeper tests the
rule, and the ending proves what changed.

The world model tracks:
- physical state: the camera, the apple, the grove, and the sign
- emotional state: longing, worry, patience, trust, and awe

The narrative instrument is foreshadowing: the opening quietly plants an omen
that later justifies the restriction and its lifting.
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

FORESHADOW_THRESHOLD = 1.0
CAMERA_THRESHOLD = 1.0
APPLE_THRESHOLD = 1.0
SIGN_THRESHOLD = 1.0


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
        if self.type in {"girl", "woman", "mother", "queen", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "prince", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the grove"
    weather: str = "still"
    tone: str = "mythic"


@dataclass
class Camera:
    label: str
    phrase: str
    can_shoot: bool = True


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    sacred: bool = False


@dataclass
class Restriction:
    label: str
    reason: str
    lifted_by: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    elder_name: str
    seed: Optional[int] = None


SETTINGS = {
    "grove": Setting(place="the grove", weather="still", tone="mythic"),
    "temple": Setting(place="the temple steps", weather="still", tone="mythic"),
    "orchard": Setting(place="the old orchard", weather="golden", tone="mythic"),
}

HERO_TYPES = {
    "girl": {"she", "her"},
    "boy": {"he", "him"},
}

HERO_NAMES = {
    "girl": ["Iris", "Mira", "Lena", "Nora", "Elin"],
    "boy": ["Arin", "Tomas", "Bren", "Cai", "Oren"],
}

ELDER_NAMES = ["the elder", "the watcher", "the priest", "the keeper", "the old sage"]


CAMERAS = {
    "lantern_camera": Camera(
        label="camera",
        phrase="a small bronze camera with a glass eye",
        can_shoot=True,
    )
}

APPLES = {
    "golden_apple": Prize(
        label="apple",
        phrase="a bright golden apple",
        type="apple",
        sacred=True,
    )
}

RESTRICTIONS = {
    "wait_for_omen": Restriction(
        label="restriction",
        reason="the apple must not be photographed before the omen",
        lifted_by="the moon-spark on the leaves",
    )
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for hero_type in HERO_TYPES:
            for _ in [0]:
                combos.append((place, hero_type, "elder"))
    return combos


def _omen_text() -> str:
    return "a silver moth circled the apple like a tiny prophecy"


def _can_fulfill(world: World, hero: Entity, camera: Entity, apple: Entity) -> bool:
    return camera.meters.get("ready", 0.0) >= CAMERA_THRESHOLD and apple.meters.get("glow", 0.0) >= APPLE_THRESHOLD


def tell(setting: Setting, hero_name: str, hero_type: str, elder_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    elder = world.add(Entity(id=elder_name, kind="character", type="elder", label=elder_name))
    camera = world.add(Entity(id="camera", type="camera", label="camera", phrase=CAMERAS["lantern_camera"].phrase, owner=hero.id))
    apple = world.add(Entity(id="apple", type="apple", label="apple", phrase=APPLES["golden_apple"].phrase))
    restriction = world.add(Entity(id="restriction", type="rule", label="restriction", phrase=RESTRICTIONS["wait_for_omen"].reason))

    world.facts.update(hero=hero, elder=elder, camera=camera, apple=apple, restriction=restriction)

    world.say(f"Long ago, in {setting.place}, there lived {hero_name}, a young {hero_type} who loved the camera.")
    world.say(f"{hero_name} held {camera.pronoun('possessive')} {camera.label} as if it were a little star caught in a hand.")
    world.say(f"Beyond the roots stood the apple, {apple.phrase}, resting in the hush of the grove.")
    world.say(f"Yet the elder had set a restriction: {restriction.phrase}.")
    world.say(f"The elder said, \"Wait until {RESTRICTIONS['wait_for_omen'].lifted_by}; then the camera may look.\"")
    world.say(f"And before anyone moved, { _omen_text() }.")

    world.para()
    hero.memes["longing"] = 1.0
    hero.memes["worry"] = 0.5
    camera.meters["ready"] = 0.0
    apple.meters["glow"] = 0.5
    world.say(f"{hero_name} wanted to take the picture at once, but the words stayed in {hero.pronoun('possessive')} chest.")
    world.say(f"{hero_name} lifted the camera, then lowered it again, remembering the elder's warning.")

    world.para()
    hero.memes["patience"] = 1.0
    apple.meters["glow"] += 0.5
    camera.meters["ready"] = 1.0
    world.say(f"Then the sky changed its breathing, and the leaves flashed with {RESTRICTIONS['wait_for_omen'].lifted_by}.")
    world.say(f"The omen arrived at last, and the restriction was no longer a closed door.")
    world.say(f"The elder nodded, and {hero_name} could finally lift the camera without breaking the old law.")

    world.para()
    if _can_fulfill(world, hero, camera, apple):
        camera.meters["shot"] = 1.0
        hero.memes["awe"] = 1.0
        world.say(f"{hero_name} took one careful picture, and the camera kept the apple's light in its bright little heart.")
        world.say(f"The apple still shone in the grove, but now its image lived too, safe inside the camera.")
        world.say(f"{hero_name} smiled, because patience had not taken the wonder away; it had made the wonder last.")
    else:
        raise StoryError("the mythic scene did not reach the omen that would lift the restriction")

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a small myth about {hero.id}, a camera, and a forbidden apple, with a foreshadowing omen.",
        f"Tell a child-friendly legendary story where the restriction on the apple is lifted by a sign in the grove.",
        f"Write a brief myth in which a young {hero.type} waits before using the camera, then finally takes the picture.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    elder: Entity = f["elder"]
    camera: Entity = f["camera"]
    apple: Entity = f["apple"]
    restriction: Entity = f["restriction"]

    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, who wanted to use the camera near the apple but had to respect the restriction.",
        ),
        QAItem(
            question=f"What did the elder say about the apple?",
            answer=f"The elder said the apple should not be photographed until the omen appeared, because the restriction had to be obeyed first.",
        ),
        QAItem(
            question=f"What changed after the omen came?",
            answer=f"After the omen came, the restriction was lifted, the camera could be used, and {hero.id} took the picture of the apple.",
        ),
        QAItem(
            question=f"Why did {hero.id} wait instead of taking the picture at once?",
            answer=f"{hero.id} waited because {restriction.phrase}, and the elder warned that the camera should not look yet.",
        ),
        QAItem(
            question=f"What did the camera keep at the end?",
            answer=f"The camera kept an image of the apple, so the wonder stayed with {hero.id} even after the moment passed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a camera for?",
            answer="A camera is used to take pictures so a moment can be remembered later.",
        ),
        QAItem(
            question="What is an apple?",
            answer="An apple is a round fruit that grows on trees and is often sweet and crisp.",
        ),
        QAItem(
            question="What does it mean to restrict something?",
            answer="To restrict something means to set a rule that says it can only happen in a certain way or at a certain time.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small clue or sign at the beginning that hints at what will matter later.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
camera(C) :- camera_id(C).
apple(A) :- apple_id(A).

restriction_active(R) :- restriction_id(R).
omen_seen :- omen(_).

can_shoot(C, A) :- camera(C), apple(A), omen_seen, not blocked(C, A).
blocked(C, A) :- camera(C), apple(A), restriction_active(_), not omen_seen.

valid_story(Place, Hero, Camera, Apple) :- setting(Place), hero(Hero), camera(Camera), apple(Apple), omen_seen.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for name in HERO_NAMES:
        lines.append(asp.fact("hero_name", name))
    for cam in CAMERAS:
        lines.append(asp.fact("camera_id", cam))
    for app in APPLES:
        lines.append(asp.fact("apple_id", app))
    for rid in RESTRICTIONS:
        lines.append(asp.fact("restriction_id", rid))
    lines.append(asp.fact("omen", "silver_moth"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set((place, hero, cam, apple) for place, hero, cam, apple in valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  clingo:", sorted(asp_set))
    print("  python:", sorted(py_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld: camera, apple, restriction, and foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gender", choices=list(HERO_TYPES))
    ap.add_argument("--name")
    ap.add_argument("--elder")
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
    hero_type = args.gender or rng.choice(list(HERO_TYPES))
    hero_name = args.name or rng.choice(HERO_NAMES[hero_type])
    elder_name = args.elder or rng.choice(ELDER_NAMES)
    if place not in SETTINGS:
        raise StoryError("unknown place")
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, elder_name=elder_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.hero_name, params.hero_type, params.elder_name)
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


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


CURATED = [
    StoryParams(place="grove", hero_name="Iris", hero_type="girl", elder_name="the watcher"),
    StoryParams(place="orchard", hero_name="Arin", hero_type="boy", elder_name="the old sage"),
    StoryParams(place="temple", hero_name="Mira", hero_type="girl", elder_name="the keeper"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
