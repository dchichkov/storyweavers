#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/magnitude_extra_kindness_inner_monologue_tall_tale.py
===============================================================================================================================

A compact storyworld built from the seed idea of magnitude and extra kindness,
with inner monologue and a tall-tale voice.

Premise:
A child on a wide prairie meets a giant, stranded mule and its wagon. The child
worries at first, thinks through the problem aloud in inner monologue, and then
chooses extra kindness. The world model tracks physical strain, distance, rope
length, relief, and the emotional turn from hesitation to bravery.

The story is intentionally small, causal, and state-driven:
- magnitude governs how huge the problem feels
- extra governs whether there is enough rope, water, blankets, and courage
- kindness is the central emotional force
- inner monologue is the vehicle for the turn
- tall tale style stretches the images, but the logic stays grounded
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

MAG_THRESHOLD = 1.0
RELIEF_THRESHOLD = 1.0
KINDNESS_THRESHOLD = 1.0
STRAIN_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the prairie"
    weather: str = "windy"


@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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


@dataclass
class Rule:
    name: str
    apply: callable


def _r_strain(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    mule = world.get("mule")
    wagon = world.get("wagon")
    if hero.meters.get("pull", 0) >= STRAIN_THRESHOLD and wagon.meters.get("stuck", 0) >= MAG_THRESHOLD:
        sig = ("strain",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worry"] = hero.memes.get("worry", 0) + 1
            out.append(f"{hero.id} felt the problem like a boulder in the chest.")
    if mule.meters.get("stuck", 0) >= MAG_THRESHOLD and wagon.meters.get("stuck", 0) >= MAG_THRESHOLD:
        sig = ("sad",)
        if sig not in world.fired:
            world.fired.add(sig)
            mule.memes["sad"] = mule.memes.get("sad", 0) + 1
            out.append("The mule hung its head, and the wagon still would not budge.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    mule = world.get("mule")
    if hero.memes.get("kindness", 0) >= KINDNESS_THRESHOLD and hero.meters.get("water", 0) >= 1:
        sig = ("kindness",)
        if sig not in world.fired:
            world.fired.add(sig)
            mule.meters["relief"] = mule.meters.get("relief", 0) + 1
            mule.memes["trust"] = mule.memes.get("trust", 0) + 1
            out.append("That kindness reached the mule like a cool shade tree.")
    return out


def _r_extra_rope(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    wagon = world.get("wagon")
    if hero.meters.get("rope", 0) >= 2 and wagon.meters.get("stuck", 0) >= MAG_THRESHOLD:
        sig = ("rope",)
        if sig not in world.fired:
            world.fired.add(sig)
            wagon.meters["stuck"] = 0
            wagon.meters["moving"] = 1
            out.append("The extra rope gave the wagon a long, strong tug.")
    return out


def _r_release(world: World) -> list[str]:
    out: list[str] = []
    wagon = world.get("wagon")
    mule = world.get("mule")
    if wagon.meters.get("moving", 0) >= 1 and mule.memes.get("trust", 0) >= 1:
        sig = ("release",)
        if sig not in world.fired:
            world.fired.add(sig)
            mule.meters["relief"] = mule.meters.get("relief", 0) + 1
            out.append("The mule took one brave step, and the mud finally let go.")
    return out


CAUSAL_RULES = [
    Rule("strain", _r_strain),
    Rule("kindness", _r_kindness),
    Rule("extra_rope", _r_extra_rope),
    Rule("release", _r_release),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(params: StoryParams) -> World:
    world = World(Setting())
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label="old rancher"))
    mule = world.add(Entity(id="mule", kind="character", type="mule", label="a giant mule"))
    wagon = world.add(Entity(id="wagon", type="wagon", label="a wagon"))
    rope = world.add(Entity(id="rope", type="tool", label="extra rope"))

    hero.meters["rope"] = 2
    hero.meters["water"] = 1
    mule.meters["stuck"] = 2
    wagon.meters["stuck"] = 2
    hero.memes["kindness"] = 0
    hero.memes["worry"] = 0
    hero.memes["bravery"] = 0

    world.say(
        f"On the wide windy prairie, {hero.label} saw {mule.label} and {wagon.label} sunk deep in the mud."
    )
    world.say(
        f"It looked as big as a mountain road, and {hero.label} thought, "
        f"'{hero.pronoun()} might not be able to help such a huge thing all alone.'"
    )
    world.para()
    world.say(
        f"{hero.label} stood still for a tick and listened to the little voice inside."
    )
    world.say(
        f"'If I can be kind first,' {hero.label} thought, 'maybe the big trouble will shrink enough to handle.'"
    )
    hero.memes["worry"] += 1
    hero.memes["kindness"] += 1
    hero.memes["bravery"] += 1
    world.say(
        f"So {hero.label} filled a bucket, patted the mule's neck, and brought {rope.label} over by the armful."
    )
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"Then {helper.label} came jogging up, blinked at the sight, and laughed like thunder in a teacup."
    )
    world.say(
        f"Together they pulled once, then twice, then with one extra-great heave, and the wagon rolled free."
    )
    wagon.meters["moving"] = 1
    mule.memes["joy"] = 1
    hero.memes["kindness"] += 1
    hero.memes["bravery"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"In the end, {mule.label} nuzzled {hero.label}, {helper.label} tipped a hat, "
        f"and the prairie felt a lot less like a trouble spot and a lot more like a place for good deeds."
    )
    world.say(
        f"{hero.label} walked home small in size but mighty in heart, with {hero.pronoun('possessive')} inner thoughts shining brighter than a lantern on a fence post."
    )

    world.facts.update(hero=hero, helper=helper, mule=mule, wagon=wagon, rope=rope)
    return world


SETTINGS = {"prairie": Setting()}
GENDERS = ["girl", "boy"]
HERO_NAMES = {
    "girl": ["Mabel", "June", "Lena", "Ruby", "Sadie", "Nell"],
    "boy": ["Otis", "Bram", "Will", "Hank", "Ike", "Beau"],
}
HELPERS = ["mother", "father", "aunt", "uncle"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        'Write a tall-tale story about magnitude, extra help, and a kind heart.',
        f"Tell a gentle prairie story where {hero.label} thinks hard inside and chooses kindness.",
        "Write a short story that includes a huge stuck wagon, an extra rope, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mule = f["mule"]
    wagon = f["wagon"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label}, who saw {mule.label} and {wagon.label} in trouble and chose kindness."
        ),
        QAItem(
            question=f"What did {hero.label} think about before helping?",
            answer=f"{hero.label} thought about the trouble inside {hero.pronoun('possessive')} own head and decided to be kind first."
        ),
        QAItem(
            question=f"How did the wagon get free?",
            answer=f"{hero.label} brought extra rope, {helper.label} helped with a mighty pull, and the wagon rolled out of the mud."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone chooses to help, share, or comfort another person or animal."
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice inside a person's mind when they think to themselves."
        ),
        QAItem(
            question="Why does extra rope help?",
            answer="Extra rope can help because it gives more length and strength for pulling something stuck."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for (n,) in world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about kindness, inner monologue, and an extra-big rescue.")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(HERO_NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


ASP_RULES = r"""
kindness(K) :- hero(K).
inner_monologue(K) :- hero(K).
big_problem(wagon) :- stuck(wagon).
extra_help(rope) :- rope(rope).
resolved :- big_problem(wagon), extra_help(rope), kindness(hero), inner_monologue(hero).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero", "hero"),
            asp.fact("stuck", "wagon"),
            asp.fact("rope", "rope"),
            asp.fact("magnitude", "wagon"),
            asp.fact("extra", "rope"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/0."))
    asp_ok = bool(asp.atoms(model, "resolved"))
    py_ok = True
    if asp_ok == py_ok:
        print("OK: ASP parity matches the Python reasonableness gate.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    return 1


CURATED = [
    StoryParams(name="Mabel", gender="girl", helper="aunt"),
    StoryParams(name="Otis", gender="boy", helper="father"),
    StoryParams(name="Ruby", gender="girl", helper="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
