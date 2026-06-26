#!/usr/bin/env python3
"""
storyworlds/worlds/sphere_neighborhood_park_twist_rhyme_tall_tale.py
=====================================================================

A standalone storyworld for a Tall Tale set in a neighborhood park where a
huge sphere, Twist, and Rhyme make a small problem turn into a bright, helpful
ending.

Premise:
- Twist and Rhyme bring a mighty sphere to the neighborhood park.
- The sphere is so large and lively that it can roll into flower beds, benches,
  and snack blankets if nobody minds it carefully.

Turn:
- Twist wants to spin it fast.
- Rhyme worries the sphere will bowl over the little park things.
- A park keeper warns them, and the children see the trouble coming.

Resolution:
- They find a safer way to play with the sphere using a rope, a grassy lane,
  and a gentle hill.
- The sphere still feels grand, but now it travels where they choose.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the neighborhood park"
    affords: set[str] = field(default_factory=set)


@dataclass
class Sphere:
    label: str
    phrase: str
    size: str
    roll: str
    risk: str
    weight: str
    can_be_tied: bool = True


@dataclass
class Helper:
    id: str
    label: str
    prep: str
    tail: str
    protects: str


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

    def copy(self) -> "World":
        clone = World(self.setting)
        from copy import deepcopy
        clone.entities = deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _entity_mood(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _set_mood(ent: Entity, key: str, value: float) -> None:
    ent.memes[key] = value


def _add_mood(ent: Entity, key: str, value: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + value


def _add_meter(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + value


def sphere_is_risky(sphere: Sphere) -> bool:
    return sphere.size in {"huge", "towering"} and sphere.risk in {"roll", "bump", "tumble"}


def helper_for_sphere(sphere: Sphere) -> Optional[Helper]:
    for helper in HELPERS:
        if helper.protects == sphere.risk:
            return helper
    return None


def _narrate_start(world: World, twist: Entity, rhyme: Entity, sphere: Sphere, keeper: Entity) -> None:
    world.say(
        f"In the neighborhood park, Twist and Rhyme came trotting in with a {sphere.size} sphere "
        f"that looked as round as a moon and twice as proud."
    )
    world.say(
        f"The children liked it because it could {sphere.roll}, but it was so big it could {sphere.risk} "
        f"right into a picnic blanket or a flower bed."
    )
    world.say(
        f"{keeper.label} watched the grassy lanes and the swing set, because a runaway sphere can stir up "
        f"more trouble than a gusty wind at a county fair."
    )


def _warn(world: World, keeper: Entity, twist: Entity, rhyme: Entity, sphere: Sphere) -> None:
    _add_mood(keeper, "worry", 1.0)
    _add_mood(twist, "curiosity", 1.0)
    _add_mood(rhyme, "worry", 1.0)
    world.say(
        f'"If you send that great sphere skittering," {keeper.label} said, '
        f'"it will {sphere.risk} over the little park things and make a fine mess of the day."'
    )


def _twist_pushes(world: World, twist: Entity, sphere: Sphere) -> None:
    _add_meter(twist, "effort", 1.0)
    _add_mood(twist, "pride", 1.0)
    world.say(
        f"Twist gave the sphere a bold shove, and the sphere rolled away like a giant peach at a summer feast."
    )


def _rhyme_reacts(world: World, rhyme: Entity, sphere: Sphere) -> None:
    _add_mood(rhyme, "alarm", 1.0)
    world.say(
        f"Rhyme clapped a hand to {rhyme.pronoun('possessive')} mouth, because the sphere was heading straight for "
        f"the daisies."
    )


def _sphere_misbehaves(world: World, sphere: Sphere) -> None:
    world.say(
        f"The sphere bumped a bench leg, wobbled past the sandbox, and gathered speed on the slope by the path."
    )


def _helper_offer(world: World, keeper: Entity, twist: Entity, rhyme: Entity, sphere: Sphere, helper: Helper) -> Entity:
    _add_mood(keeper, "hope", 1.0)
    world.say(
        f"{keeper.label} pointed to a long rope and said, "
        f'"How about we {helper.prep} and guide it the careful way?"'
    )
    rope = world.add(Entity(
        id=helper.id,
        kind="thing",
        type="rope",
        label=helper.label,
        protective=True,
    ))
    return rope


def _accept(world: World, twist: Entity, rhyme: Entity, keeper: Entity, sphere: Sphere, helper: Helper) -> None:
    _add_mood(twist, "joy", 2.0)
    _add_mood(rhyme, "joy", 2.0)
    _set_mood(twist, "stubborn", 0.0)
    _set_mood(rhyme, "worry", 0.0)
    world.say(
        f"Twist and Rhyme nodded, and together they {helper.tail}."
    )
    world.say(
        f"Then the sphere stopped being a wild charger and became a merry, guided giant, rolling where they wanted."
    )
    world.say(
        f"By dusk, the whole neighborhood park looked brighter, and the great sphere had made a calm road of play."
    )


def tell(setting: Setting, sphere: Sphere, hero_name1: str = "Twist", hero_name2: str = "Rhyme") -> World:
    world = World(setting)
    twist = world.add(Entity(id=hero_name1, kind="character", type="child", label="Twist"))
    rhyme = world.add(Entity(id=hero_name2, kind="character", type="child", label="Rhyme"))
    keeper = world.add(Entity(id="keeper", kind="character", type="keeper", label="the park keeper"))
    ball = world.add(Entity(id="sphere", type="sphere", label=sphere.label, phrase=sphere.phrase))
    world.facts.update(twist=twist, rhyme=rhyme, keeper=keeper, sphere=ball, sphere_cfg=sphere)

    _narrate_start(world, twist, rhyme, sphere, keeper)
    world.para()
    _warn(world, keeper, twist, rhyme, sphere)
    _twist_pushes(world, twist, sphere)
    _rhyme_reacts(world, rhyme, sphere)
    _sphere_misbehaves(world, sphere)

    world.para()
    helper = helper_for_sphere(sphere)
    if helper is None:
        raise StoryError("No safe helper exists for this sphere story.")
    rope = _helper_offer(world, keeper, twist, rhyme, sphere, helper)
    if rope is None:
        raise StoryError("The helper could not be placed into the story.")
    _accept(world, twist, rhyme, keeper, sphere, helper)

    world.facts["helper"] = helper
    world.facts["rope"] = rope
    return world


SETTINGS = {
    "park": Setting(place="the neighborhood park", affords={"sphere"}),
}

SPHERES = {
    "moonball": Sphere(
        label="moonball",
        phrase="a shining sphere as big as a wagon wheel",
        size="huge",
        roll="rolls",
        risk="bump",
        weight="heavy",
    ),
    "sunball": Sphere(
        label="sunball",
        phrase="a bright yellow sphere bigger than a laundry basket",
        size="towering",
        roll="rolls",
        risk="tumble",
        weight="heavy",
    ),
    "pearlball": Sphere(
        label="pearlball",
        phrase="a smooth white sphere with a glossy shine",
        size="huge",
        roll="rolls",
        risk="roll",
        weight="heavy",
    ),
}

HELPERS = [
    Helper(
        id="rope",
        label="a long rope",
        prep="tie the rope around the sphere",
        tail="tied the rope around the sphere and walked it across the grass",
        protects="roll",
    ),
    Helper(
        id="guideflag",
        label="a bright flag",
        prep="set up a marked lane",
        tail="marked a lane and steered the sphere along it",
        protects="bump",
    ),
    Helper(
        id="sandbags",
        label="a row of sandbags",
        prep="set up a low stop line",
        tail="set the stop line and kept the sphere from tumbling downhill",
        protects="tumble",
    ),
]

TALL_TALE_WORDS = [
    "bigger than a barn cat's grin",
    "round as the harvest moon",
    "louder than a thunderclap in a tin bucket",
    "as lively as three kites in a storm",
]


@dataclass
class StoryParams:
    setting: str
    sphere: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: Twist, Rhyme, and a neighborhood park sphere."
    )
    ap.add_argument("--setting", choices=SETTINGS, default="park")
    ap.add_argument("--sphere", choices=SPHERES)
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SETTINGS:
        for sp in SPHERES:
            combos.append((s, sp))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.sphere:
        combos = [c for c in combos if c[1] == args.sphere]
    if not combos:
        raise StoryError("No valid sphere story matches the requested options.")
    setting, sphere = rng.choice(combos)
    return StoryParams(setting=setting, sphere=sphere)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    sphere = f["sphere_cfg"]
    return [
        'Write a short tall-tale story for a child about a sphere in a neighborhood park.',
        f"Tell a story where Twist and Rhyme meet {sphere.phrase} and learn to guide it safely.",
        f"Write a playful neighborhood park story that includes the word 'sphere' and ends with the sphere under control.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    sphere: Sphere = f["sphere_cfg"]
    return [
        QAItem(
            question="Who found the huge sphere in the neighborhood park?",
            answer="Twist and Rhyme found it together in the neighborhood park.",
        ),
        QAItem(
            question="Why did the park keeper worry about the sphere?",
            answer=(
                f"The park keeper worried because the sphere could {sphere.risk} into the little park things "
                f"and make a mess."
            ),
        ),
        QAItem(
            question="How did the children keep the sphere from causing trouble?",
            answer="They used the helper and guided the sphere carefully across the grass.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sphere?",
            answer="A sphere is a perfectly round shape, like a ball, that has no corners.",
        ),
        QAItem(
            question="What is a neighborhood park?",
            answer="A neighborhood park is a shared outdoor place with grass, paths, and things for people to enjoy nearby.",
        ),
        QAItem(
            question="What does a rope do?",
            answer="A rope can help people hold, tie, or guide things so they do not move away.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    sphere = SPHERES[params.sphere]
    world = tell(SETTINGS[params.setting], sphere)
    story = world.render()
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


ASP_RULES = r"""
setting(park).
sphere(moonball).
sphere(sunball).
sphere(pearlball).

helper(rope).
helper(guideflag).
helper(sandbags).

risk(moonball,bump).
risk(sunball,tumble).
risk(pearlball,roll).

compat(rope,roll).
compat(guideflag,bump).
compat(sandbags,tumble).

valid(Setting,Sphere) :- setting(Setting), sphere(Sphere), risk(Sphere,R), helper(H), compat(H,R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for sp in SPHERES:
        lines.append(asp.fact("sphere", sp))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
    for sp, cfg in SPHERES.items():
        lines.append(asp.fact("risk", sp, cfg.risk))
    for h in HELPERS:
        lines.append(asp.fact("compat", h.id, h.protects))
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
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for s, sp in valid_combos():
            params = StoryParams(setting=s, sphere=sp, seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
