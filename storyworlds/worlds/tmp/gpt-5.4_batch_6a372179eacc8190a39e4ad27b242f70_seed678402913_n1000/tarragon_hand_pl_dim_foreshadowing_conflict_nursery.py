#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tarragon_hand_pl_dim_foreshadowing_conflict_nursery.py
==================================================================================

A standalone story world for a tiny nursery-rhyme-like tale about a child sent
to fetch tarragon at dusk with a hand-pl-dim lantern. The world models a small
garden errand with foreshadowing and conflict: the lantern is already dimming,
the path holds one practical trouble, and a sensible helper resolves it so the
meal and the mood can end warmly.

Run it
------
    python storyworlds/worlds/gpt-5.4/tarragon_hand_pl_dim_foreshadowing_conflict_nursery.py
    python storyworlds/worlds/gpt-5.4/tarragon_hand_pl_dim_foreshadowing_conflict_nursery.py --obstacle goose --fix grain
    python storyworlds/worlds/gpt-5.4/tarragon_hand_pl_dim_foreshadowing_conflict_nursery.py --obstacle goose --fix boots
    python storyworlds/worlds/gpt-5.4/tarragon_hand_pl_dim_foreshadowing_conflict_nursery.py --all
    python storyworlds/worlds/gpt-5.4/tarragon_hand_pl_dim_foreshadowing_conflict_nursery.py --trace --seed 7
    python storyworlds/worlds/gpt-5.4/tarragon_hand_pl_dim_foreshadowing_conflict_nursery.py --qa --json
    python storyworlds/worlds/gpt-5.4/tarragon_hand_pl_dim_foreshadowing_conflict_nursery.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so go up to storyworlds/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mother",
            "father": "father",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.label or self.type)


@dataclass
class Setting:
    id: str
    place: str
    patch: str
    kitchen: str
    sky: str
    path: str


@dataclass
class Obstacle:
    id: str
    label: str
    sign: str
    risk: str
    rise_line: str
    calm_fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    handles: set[str] = field(default_factory=set)
    action: str = ""
    after: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
    apply: Callable[[World], list[str]]


def _r_dim_warning(world: World) -> list[str]:
    lantern = world.entities.get("lantern")
    path = world.entities.get("path")
    child = world.entities.get("child")
    if not lantern or not path or not child:
        return []
    if lantern.meters["dim"] < THRESHOLD:
        return []
    sig = ("dim_warning",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    path.meters["dark"] += 1
    child.memes["unease"] += 1
    return ["The little light was going low, and that meant the path would soon grow shadowy."]


def _r_obstacle_risk(world: World) -> list[str]:
    obstacle = world.entities.get("obstacle")
    child = world.entities.get("child")
    if not obstacle or not child:
        return []
    if obstacle.meters["blocking"] < THRESHOLD:
        return []
    sig = ("obstacle_risk", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["frustration"] += 1
    world.get("path").meters["risk"] += 1
    return ["The errand, which had seemed so tiny, suddenly felt taller than a child-sized song."]


RULES = [
    Rule(name="dim_warning", apply=_r_dim_warning),
    Rule(name="obstacle_risk", apply=_r_obstacle_risk),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    made: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            out = rule.apply(world)
            if out:
                changed = True
                made.extend(out)
    if narrate:
        for line in made:
            world.say(line)
    return made


SETTINGS = {
    "cottage": Setting(
        id="cottage",
        place="the cottage yard",
        patch="the tarragon patch by the stepping stones",
        kitchen="the warm cottage kitchen",
        sky="the sky was lilac with a thin silver moon",
        path="the stone path",
    ),
    "mill": Setting(
        id="mill",
        place="the mill yard",
        patch="the tarragon bed beside the little rain barrel",
        kitchen="the snug mill kitchen",
        sky="the sky was blue-gray with the first small star",
        path="the brick path",
    ),
    "farm": Setting(
        id="farm",
        place="the farm garden",
        patch="the tarragon row by the bean poles",
        kitchen="the bright farm kitchen",
        sky="the sky was peach-gold with sleepy swallows above",
        path="the garden path",
    ),
}

OBSTACLES = {
    "goose": Obstacle(
        id="goose",
        label="goose",
        sign="a white goose stood by the herbs, neck bent like a question mark",
        risk="a hiss and a peck",
        rise_line="the goose gave a sharp hiss and stamped one orange foot",
        calm_fix="a few grains scattered wide",
        tags={"goose", "garden_animals"},
    ),
    "gate": Obstacle(
        id="gate",
        label="gate",
        sign="the little gate sagged and would not swing free",
        risk="pinched fingers and a hard tug",
        rise_line="the latch stuck fast and rattled in the dimness",
        calm_fix="a lift on the latch before the pull",
        tags={"gate"},
    ),
    "mud": Obstacle(
        id="mud",
        label="mud",
        sign="the damp ground by the patch had turned to slick brown mud",
        risk="a slip and a plop",
        rise_line="the child's shoe slid and the basket tipped sideways",
        calm_fix="dry boots and slower steps",
        tags={"mud"},
    ),
}

FIXES = {
    "grain": Fix(
        id="grain",
        label="grain",
        handles={"goose"},
        action="shook a little scoop of grain onto the far grass",
        after="The goose waddled after the supper of seeds, busy with pecking instead of peevishness.",
        tags={"grain", "goose"},
    ),
    "lift_latch": Fix(
        id="lift_latch",
        label="lifted latch",
        handles={"gate"},
        action="showed how to lift the latch up before easing the gate forward",
        after="The gate gave one small click and opened with a polite wooden sigh.",
        tags={"gate"},
    ),
    "boots": Fix(
        id="boots",
        label="boots",
        handles={"mud"},
        action="brought the child's red boots and tied them snugly on",
        after="The boots held firm where soft shoes would have skidded and sulked.",
        tags={"boots", "mud"},
    ),
}

CHILDREN = [
    ("Mabel", "girl"),
    ("Ned", "boy"),
    ("Poppy", "girl"),
    ("Kit", "boy"),
    ("Daisy", "girl"),
    ("Ben", "boy"),
]

HELPERS = [
    ("mother", "mother"),
    ("grandma", "grandmother"),
    ("grandpa", "grandfather"),
]

TRAITS = ["brisk", "careful", "cheerful", "eager", "thoughtful"]


def valid_combo(obstacle_id: str, fix_id: str) -> bool:
    return obstacle_id in OBSTACLES and fix_id in FIXES and obstacle_id in FIXES[fix_id].handles


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for obstacle_id in OBSTACLES:
            for fix_id in FIXES:
                if valid_combo(obstacle_id, fix_id):
                    combos.append((setting_id, obstacle_id, fix_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    obstacle: str
    fix: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="cottage",
        obstacle="goose",
        fix="grain",
        child_name="Mabel",
        child_gender="girl",
        helper_name="grandma",
        helper_type="grandmother",
        trait="eager",
    ),
    StoryParams(
        setting="mill",
        obstacle="gate",
        fix="lift_latch",
        child_name="Ned",
        child_gender="boy",
        helper_name="mother",
        helper_type="mother",
        trait="brisk",
    ),
    StoryParams(
        setting="farm",
        obstacle="mud",
        fix="boots",
        child_name="Poppy",
        child_gender="girl",
        helper_name="grandpa",
        helper_type="grandfather",
        trait="careful",
    ),
]


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if not valid_combo(params.obstacle, params.fix):
        raise StoryError(explain_rejection(params.obstacle, params.fix))

    setting = SETTINGS[params.setting]
    obstacle_cfg = OBSTACLES[params.obstacle]
    fix_cfg = FIXES[params.fix]

    world = World(setting=setting)
    child = world.add(
        Entity(
            id="child",
            kind="character",
            type=params.child_gender,
            label=params.child_name,
            phrase=params.child_name,
            role="child",
            attrs={"trait": params.trait},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=params.helper_type,
            label=params.helper_name,
            phrase=params.helper_name,
            role="helper",
        )
    )
    lantern = world.add(
        Entity(
            id="lantern",
            kind="thing",
            type="lantern",
            label="hand-pl-dim lantern",
            phrase="the hand-pl-dim lantern",
            tags={"lantern", "light"},
        )
    )
    path = world.add(
        Entity(
            id="path",
            kind="thing",
            type="path",
            label=setting.path,
            phrase=setting.path,
            tags={"path"},
        )
    )
    patch = world.add(
        Entity(
            id="patch",
            kind="thing",
            type="herb_patch",
            label="tarragon patch",
            phrase=setting.patch,
            tags={"tarragon", "garden"},
        )
    )
    obstacle = world.add(
        Entity(
            id="obstacle",
            kind="thing",
            type=obstacle_cfg.id,
            label=obstacle_cfg.label,
            phrase=obstacle_cfg.label,
            tags=set(obstacle_cfg.tags),
        )
    )

    child.memes["eagerness"] += 1
    lantern.meters["dim"] += 1
    obstacle.meters["blocking"] += 1
    propagate(world, narrate=False)

    world.say(
        f"In {setting.place}, where supper spoons would soon begin, "
        f"{params.child_name} skipped out light of foot and chin."
    )
    world.say(
        f"{setting.sky}. From {setting.kitchen} came a call: "
        f'"Bring tarragon, dear heart, for broth, before the evening settles all."'
    )
    world.say(
        f"{params.child_name} took {lantern.phrase}, a hand-pl-dim little gleam, "
        f"and hummed along as if the errand were the easiest of dreams."
    )

    world.para()
    world.say(
        f"But foreshadow sat soft on the air: {obstacle_cfg.sign}. "
        f"The light in the lantern thinned to a butter-yellow rim."
    )
    propagate(world, narrate=True)
    world.say(
        f"Still {params.child_name} hurried toward {setting.patch}, for tarragon smelled sweet and green, "
        f"and the bowl indoors was waiting for the leaf no one had yet seen."
    )

    world.para()
    child.memes["hurry"] += 1
    world.say(
        f"Then trouble tapped its tiny drum. {obstacle_cfg.rise_line}. "
        f"{params.child_name} stopped with a catch of breath, thinking of {obstacle_cfg.risk} in the growing dim."
    )

    if params.obstacle == "goose":
        child.memes["fear"] += 1
    elif params.obstacle == "gate":
        child.memes["frustration"] += 1
    else:
        child.memes["wobble"] += 1

    world.say(
        f'"Oh dear," said {params.child_name}, "the tarragon is there, but the way is cross and grim."'
    )

    world.para()
    helper.memes["calm"] += 1
    child.memes["trust"] += 1
    world.say(
        f"Out came {helper.label_word} {params.helper_name}, hearing both the pause and the plea. "
        f'"No snatching, no dashing," {helper.pronoun()} said. "We will solve it sensibly."'
    )
    world.say(
        f"{params.helper_name} {fix_cfg.action}. {fix_cfg.after}"
    )
    obstacle.meters["blocking"] = 0.0
    path.meters["risk"] = 0.0
    child.memes["relief"] += 1

    world.say(
        f"Then hand in hand they reached the patch. {params.child_name} pinched a feathery sprig of tarragon, "
        f"and the air smelled peppery and bright, like supper finding its own song."
    )

    world.para()
    child.memes["joy"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"Back to {setting.kitchen} they went, with the hand-pl-dim lantern bobbing slow. "
        f"The broth took in the tarragon, and the whole room seemed to glow."
    )
    world.say(
        f"{params.child_name} learned that when the evening whispers warning in a thinner, smaller light, "
        f"one kind pause and one wise helper can set a little errand right."
    )
    world.say(
        "So stir the pot and mind the sign: when shadows gather, do not dash. "
        "A calm small plan can save the herbs, the shoes, the gate, and all the rest from rash."
    )

    world.facts.update(
        child=child,
        helper=helper,
        setting=setting,
        obstacle_cfg=obstacle_cfg,
        fix_cfg=fix_cfg,
        lantern=lantern,
        patch=patch,
        obstacle=obstacle,
        success=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    obstacle = f["obstacle_cfg"]
    return [
        'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the words "tarragon" and "hand-pl-dim".',
        f"Tell a small evening garden story where {child.label} goes out for tarragon, a {obstacle.label} causes conflict, and {helper.label_word} helps with a calm fix.",
        'Write a gentle foreshadowing story in sing-song language where a dim lantern warns that rushing is a bad idea, and the ending proves that patience solves the problem.',
    ]


def pair_role(helper: Entity) -> str:
    return {
        "mother": "mother",
        "grandmother": "grandma",
        "grandfather": "grandpa",
    }.get(helper.type, helper.label_word)


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    obstacle = f["obstacle_cfg"]
    fix = f["fix_cfg"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, who went out into {setting.place} to fetch tarragon, and {pair_role(helper)} {helper.label}, who came to help. The story follows their little dusk errand from trouble to comfort.",
        ),
        (
            "What was the child sent to get?",
            f"{child.label} was sent to fetch tarragon for the supper broth. The herb mattered because the warm kitchen was already waiting for that last green sprig.",
        ),
        (
            'What is the "hand-pl-dim" thing in the story?',
            'It is the small lantern the child carries outside. Calling it "hand-pl-dim" makes it sound tiny and nursery-like, and its weak glow foreshadows that the garden errand may grow harder in the dark.',
        ),
        (
            "How did the story foreshadow trouble?",
            f"The lantern was already dimming, and {obstacle.sign}. Those signs warned that the path to the tarragon would not stay easy for long.",
        ),
        (
            "What was the conflict?",
            f"The conflict was that {child.label} wanted to hurry to the tarragon, but {obstacle.label} blocked the safe way. The child had to stop because rushing in the dimness might lead to {obstacle.risk}.",
        ),
        (
            "How did the helper solve the problem?",
            f"{helper.label} {fix.action}. That worked because {fix.label} is the sensible answer to a {obstacle.label} problem, so the child could reach the herb safely instead of dashing in upset.",
        ),
        (
            "How did the story end?",
            f"They brought the tarragon back to the kitchen, and the broth and the room both seemed warmer. The ending image proves what changed: the child stopped rushing and learned to trust a calm plan when evening gives a warning sign.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "tarragon": [
        (
            "What is tarragon?",
            "Tarragon is a green herb with thin leaves that people use to flavor food. A little bit can make soup or sauce smell bright and tasty.",
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern gives light so you can see in dim places. If its light is weak, people should slow down and be extra careful.",
        )
    ],
    "goose": [
        (
            "Why should you be careful around a goose?",
            "A goose can hiss, flap, and peck if it feels bothered. It is kinder and safer to give it space than to rush at it.",
        )
    ],
    "gate": [
        (
            "Why can a stuck gate be a problem?",
            "A stuck gate can pinch fingers or make someone tug too hard. It is better to open it the right way than to yank at it in a hurry.",
        )
    ],
    "mud": [
        (
            "Why is mud slippery?",
            "Mud is wet soil, so shoes can slide on it more easily than on dry ground. Slow steps and good boots help people keep their balance.",
        )
    ],
    "boots": [
        (
            "What are boots good for in wet ground?",
            "Boots help keep feet steadier and drier on muddy ground. They give more protection than soft indoor shoes.",
        )
    ],
    "garden_animals": [
        (
            "Why do garden animals come near herbs and seeds?",
            "Garden animals often come where food smells good or seeds are nearby. They are simply looking for something to peck or nibble.",
        )
    ],
}

KNOWLEDGE_ORDER = ["tarragon", "lantern", "goose", "gate", "mud", "boots", "garden_animals"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"tarragon", "lantern"} | set(f["obstacle_cfg"].tags) | set(f["fix_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


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
    for ent in world.entities.values():
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for (name, *_) in world.fired))}")
    return "\n".join(lines)


def explain_rejection(obstacle_id: str, fix_id: str) -> str:
    if obstacle_id not in OBSTACLES:
        return f"(No story: unknown obstacle '{obstacle_id}'.)"
    if fix_id not in FIXES:
        return f"(No story: unknown fix '{fix_id}'.)"
    obstacle = OBSTACLES[obstacle_id]
    fix = FIXES[fix_id]
    return (
        f"(No story: {fix.label} does not sensibly solve the {obstacle.label} problem. "
        f"Pick a fix that matches the obstacle: goose->grain, gate->lift_latch, mud->boots.)"
    )


ASP_RULES = r"""
solves(O, F) :- fix_handles(F, O).
valid(S, O, F) :- setting(S), obstacle(O), fix(F), solves(O, F).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for obstacle_id in OBSTACLES:
        lines.append(asp.fact("obstacle", obstacle_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for handled in sorted(fix.handles):
            lines.append(asp.fact("fix_handles", fix_id, handled))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "tarragon" not in sample.story or "hand-pl-dim" not in sample.story:
            raise StoryError("(Smoke test failed: generated story is missing required seed words.)")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme storyworld: a child fetches tarragon at dusk with a hand-pl-dim lantern."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=[name for name, _ in HELPERS])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.fix and not valid_combo(args.obstacle, args.fix):
        raise StoryError(explain_rejection(args.obstacle, args.fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, obstacle_id, fix_id = rng.choice(sorted(combos))
    child_name, child_gender = rng.choice(CHILDREN)
    if args.child_gender is not None:
        child_gender = args.child_gender
        pools = [name for name, gender in CHILDREN if gender == child_gender]
        child_name = rng.choice(pools)
    if args.child_name is not None:
        child_name = args.child_name

    helper_name, helper_type = rng.choice(HELPERS)
    if args.helper is not None:
        helper_name = args.helper
        helper_type = dict(HELPERS)[args.helper]

    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        obstacle=obstacle_id,
        fix=fix_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_type=helper_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, obstacle, fix) combos:\n")
        for setting_id, obstacle_id, fix_id in combos:
            print(f"  {setting_id:8} {obstacle_id:8} {fix_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.obstacle} with {p.fix} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
