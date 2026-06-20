#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/streak_plate_curiosity_sound_effects_nursery_rhyme.py
======================================================================================

A standalone storyworld for a tiny nursery-rhyme-like domain about a curious
child, a shiny plate, a little streak, and playful sound effects.

The world simulates a small causal chain:
- a curious child notices a streak on a plate,
- a sound effect helps them investigate,
- an adult notices whether the streak is harmless or needs a careful wash,
- the ending proves what changed in the plate, the child, and the room.

This script follows the Storyweavers contract:
- stdlib only
- eager import of storyworlds/results.py for QAItem, StoryError, StorySample
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import copy
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.meters is None:
            self.meters = {}
        if self.memes is None:
            self.memes = {}

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def add_m(self, key: str, value: float) -> None:
        self.meters[key] = self.m(key) + value

    def add_e(self, key: str, value: float) -> None:
        self.memes[key] = self.e(key) + value

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Scene:
    name: str
    setting: str
    rhyme_line: str
    curiosity_line: str
    sound_effect: str
    sound_source: str
    streak_source: str
    plate_image: str
    ending_image: str
    can_wash: bool
    clean_result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class StoryParams:
    scene: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_gender: str
    seed: Optional[int] = None


SCENES = {
    "kitchen": Scene(
        name="kitchen",
        setting="a little kitchen with warm tiles",
        rhyme_line="The day was bright, the table neat, with crumbs in crumbs and tiny feet.",
        curiosity_line="A curious child peeped and poked, as if the plate might sing or joke.",
        sound_effect="clink-clink!",
        sound_source="the spoon against the bowl",
        streak_source="a berry streak from jam",
        plate_image="a white plate with a red streak",
        ending_image="a clean plate shining by the sink",
        can_wash=True,
        clean_result="washed the plate clean",
        tags={"curiosity", "sound_effects", "plate", "streak"},
    ),
    "porch": Scene(
        name="porch",
        setting="a sunny porch with a small blue chair",
        rhyme_line="On the porch there sat a plate, so shiny, round, and neat and great.",
        curiosity_line="A curious child leaned close to see the streak and where it made its peak.",
        sound_effect="tap-tap!",
        sound_source="a little rain drop on the railing",
        streak_source="dust from a windy day",
        plate_image="a blue plate with a pale streak",
        ending_image="a plate wiped dry in the afternoon sun",
        can_wash=False,
        clean_result="wiped the plate dry",
        tags={"curiosity", "sound_effects", "plate", "streak"},
    ),
    "garden": Scene(
        name="garden",
        setting="a garden path beside a green gate",
        rhyme_line="The flowers swayed, the birds did sing, and silver light danced over everything.",
        curiosity_line="A curious child bent low to learn what made the streak appear.",
        sound_effect="shh-shh!",
        sound_source="the leaves brushing together",
        streak_source="mud from a muddy shoe",
        plate_image="a garden plate with a brown streak",
        ending_image="a tidy plate on the windowsill",
        can_wash=True,
        clean_result="rinsed the plate until it gleamed",
        tags={"curiosity", "sound_effects", "plate", "streak"},
    ),
}

CHILD_NAMES = ["Mia", "Lily", "Noah", "Theo", "Ava", "Ruby", "Finn", "Lena"]
ADULT_NAMES = ["Mom", "Dad", "Nana", "Papa"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld with streaks, plates, curiosity, and sound effects.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--adult-name")
    ap.add_argument("--adult-gender", choices=["mother", "father"])
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


def valid_combos() -> list[tuple[str, str]]:
    return [(sid, "clean") for sid in SCENES] + [(sid, "wipe") for sid in SCENES if SCENES[sid].can_wash]


def asp_facts() -> str:
    import asp
    lines = []
    for sid, sc in SCENES.items():
        lines.append(asp.fact("scene", sid))
        if sc.can_wash:
            lines.append(asp.fact("can_wash", sid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Scene, Mode) :- scene(Scene), mode(Mode), Mode = clean.
valid(Scene, wipe) :- scene(Scene), can_wash(Scene).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\nmode(clean).\nmode(wipe).\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def _child_pronoun(gender: str) -> str:
    return "she" if gender == "girl" else "he"


def _child_object(gender: str) -> str:
    return "her" if gender == "girl" else "him"


def _adult_word(gender: str) -> str:
    return "mom" if gender == "mother" else "dad"


def tell(scene: Scene, child: Entity, adult: Entity) -> World:
    w = World()
    plate = w.add(Entity("plate", type="thing", label="plate"))
    streak = w.add(Entity("streak", type="thing", label="streak"))
    sound = w.add(Entity("sound", type="thing", label="sound"))
    child.add_e("curious", 1)
    child.add_e("joy", 1)
    w.say(f"{scene.rhyme_line} {scene.curiosity_line}")
    w.say(f"{child.id} pointed and said, \"{scene.sound_effect} What makes that sound?\"")
    w.para()
    w.say(
        f"Near {scene.setting}, {child.id} found {scene.plate_image}. "
        f"The {scene.sound_source} went {scene.sound_effect}"
    )
    w.say(f"{child.id} was curious enough to look closer, but careful enough to ask {adult.id}.")
    w.para()

    if scene.can_wash:
        child.add_e("satisfaction", 1)
        plate.add_m("streak", 1)
        streak.add_m("visible", 1)
        w.say(
            f"{adult.id} smiled and said the streak was only {scene.streak_source}. "
            f"{adult.id} helped {child.id} {scene.clean_result}."
        )
        plate.add_m("clean", 1)
        plate.meters["streak"] = 0.0
        w.say(
            f"Together they wiped and rinsed until the plate became {scene.ending_image}. "
            f"{child.id} laughed, and the little room felt bright and neat again."
        )
        outcome = "clean"
    else:
        child.add_e("surprise", 1)
        plate.add_m("streak", 1)
        streak.add_m("visible", 1)
        w.say(
            f"{adult.id} nodded and said the streak was only {scene.streak_source}. "
            f"They wiped the plate dry at once."
        )
        plate.add_m("dry", 1)
        w.say(
            f"That was all it needed. Soon there was {scene.ending_image}, and {child.id} "
            f"smiled because the mystery had turned gentle and small."
        )
        outcome = "dry"

    w.facts.update(scene=scene, child=child, adult=adult, plate=plate, streak=streak, sound=sound, outcome=outcome)
    return w


def generation_prompts(world: World) -> list[str]:
    sc = world.facts["scene"]
    child = world.facts["child"]
    return [
        f'Write a nursery-rhyme-style story for a child named {child.id} that includes the words "streak" and "plate".',
        f"Tell a gentle story with sound effects where {child.id} gets curious about a streak on a plate and asks a grown-up what it is.",
        f'Write a short child-friendly rhyme where curiosity leads to a small mystery, a sound effect, and a tidy ending with a plate.',
    ]


def story_qa(world: World) -> list[QAItem]:
    sc = world.facts["scene"]
    child = world.facts["child"]
    adult = world.facts["adult"]
    outcome = world.facts["outcome"]
    answers = [
        QAItem(
            question=f"What did {child.id} notice on the plate?",
            answer=f"{child.id} noticed a streak on the plate. That made {child.pronoun()} curious, so {child.pronoun()} asked {adult.id} to explain it."
        ),
        QAItem(
            question=f"How did the sound effects help the story?",
            answer=f"The story used {sc.sound_effect} to make the little scene feel lively. The sound helped show that {child.id} was paying close attention to small things."
        ),
    ]
    if outcome == "clean":
        answers.append(
            QAItem(
                question="How did the story end?",
                answer="It ended with a clean plate shining by the sink. The streak was washed away, and the curious child felt happy and calm."
            )
        )
    else:
        answers.append(
            QAItem(
                question="How did the story end?",
                answer="It ended with the plate wiped dry in the sunshine. The streak was not a problem after all, so the child could smile and move on."
            )
        )
    return answers


def world_qa(world: World) -> list[QAItem]:
    sc = world.facts["scene"]
    return [
        QAItem(
            question="What is a streak?",
            answer="A streak is a narrow line or mark on something smooth. On a plate, it can be a little smear that makes the plate look less neat."
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are playful words that let you hear the action in your head. They make the story feel lively, like clink-clink or tap-tap."
        ),
        QAItem(
            question="Why do people wash plates?",
            answer="People wash plates to remove food, streaks, and dirt. A clean plate is safer and nicer to use again."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}\nA: {q.answer}")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}\nA: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: meters={e.meters} memes={e.memes} label={e.label}")
    out.append(f"facts: {sorted(world.facts.keys())}")
    return "\n".join(out)


CURATED = [
    StoryParams("kitchen", "Mia", "girl", "Mom", "mother"),
    StoryParams("porch", "Noah", "boy", "Dad", "father"),
    StoryParams("garden", "Lily", "girl", "Nana", "mother"),
]


def explain_rejection(scene: Scene) -> str:
    return f"(No story: the requested scene '{scene.name}' does not fit the tiny rhyme world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.scene not in SCENES:
        raise StoryError(explain_rejection(Scene(args.scene, "", "", "", "", "", "", "", "", False, "")))
    scene = args.scene or rng.choice(list(SCENES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    adult_gender = args.adult_gender or rng.choice(["mother", "father"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    adult_name = args.adult_name or rng.choice(ADULT_NAMES)
    return StoryParams(scene, child_name, child_gender, adult_name, adult_gender)


def generate(params: StoryParams) -> StorySample:
    scene = SCENES[params.scene]
    child = Entity(params.child_name, kind="character", type=params.child_gender, role="curious-child")
    adult = Entity(params.adult_name, kind="character", type=params.adult_gender, role="helper")
    world = tell(scene, child, adult)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print("python-only:", sorted(py - cl))
        print("asp-only:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"FAILED: generate() smoke test crashed: {e}")
        return 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for item in asp_valid_combos():
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 30, 30)):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
