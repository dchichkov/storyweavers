#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tubby_boom_problem_solving_repetition_cautionary_fable.py
====================================================================================

A small fable-shaped story world about a tubby animal, a stuck gate, and the
difference between pounding at a problem and solving it with care.

Seed goals covered:
- includes the words "tubby" and "boom"
- uses Problem Solving, Repetition, and a Cautionary turn
- reads like a small animal fable with a closing moral

Run it
------
    python storyworlds/worlds/gpt-5.4/tubby_boom_problem_solving_repetition_cautionary_fable.py
    python storyworlds/worlds/gpt-5.4/tubby_boom_problem_solving_repetition_cautionary_fable.py --obstacle mud_jam --fix clear_mud
    python storyworlds/worlds/gpt-5.4/tubby_boom_problem_solving_repetition_cautionary_fable.py --obstacle vine_latch --fix oil_hinge
    python storyworlds/worlds/gpt-5.4/tubby_boom_problem_solving_repetition_cautionary_fable.py --all
    python storyworlds/worlds/gpt-5.4/tubby_boom_problem_solving_repetition_cautionary_fable.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/tubby_boom_problem_solving_repetition_cautionary_fable.py --qa --json
    python storyworlds/worlds/gpt-5.4/tubby_boom_problem_solving_repetition_cautionary_fable.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"hen", "goose", "sheep", "mother", "aunt"}
        male = {"boar", "fox", "mole", "uncle", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    gate_kind: str
    reward: str
    scene: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    cause_text: str
    clue_text: str
    fix_family: str
    safe_booms: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    family: str
    act_text: str
    result_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    apply: callable


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


def _r_crack(world: World) -> list[str]:
    gate = world.get("gate")
    sig = ("crack", int(gate.meters["strain"]))
    if gate.meters["strain"] < 2 or sig in world.fired:
        return []
    world.fired.add(sig)
    gate.meters["cracked"] = 1
    for eid in ("hero", "helper"):
        if eid in world.entities:
            world.get(eid).memes["worry"] += 1
    return ["__crack__"]


CAUSAL_RULES = [Rule(name="crack", apply=_r_crack)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


SETTINGS = {
    "meadow": Setting(
        id="meadow",
        place="a clover meadow",
        gate_kind="wooden gate",
        reward="sweet clover",
        scene="At the edge of a sunny farm lane stood a wooden gate with silver dew on its rails.",
        tags={"gate", "clover"},
    ),
    "orchard": Setting(
        id="orchard",
        place="an apple orchard",
        gate_kind="orchard gate",
        reward="fallen apples",
        scene="Beside a winding path stood an orchard gate, and beyond it the grass smelled of apples.",
        tags={"gate", "apples"},
    ),
    "pond": Setting(
        id="pond",
        place="a pond bank",
        gate_kind="reed gate",
        reward="cool water lilies",
        scene="Near a shining pond stood a reed gate that opened onto soft, green shade.",
        tags={"gate", "pond"},
    ),
}

OBSTACLES = {
    "mud_jam": Obstacle(
        id="mud_jam",
        label="mud in the lower hinge",
        cause_text="Rain had dried into a hard lump of mud in the lower hinge.",
        clue_text="A brown crust clung to the hinge near the ground.",
        fix_family="clear",
        safe_booms=1,
        tags={"mud", "hinge"},
    ),
    "vine_latch": Obstacle(
        id="vine_latch",
        label="a vine caught around the latch",
        cause_text="A thin green vine had curled around the latch and held it fast.",
        clue_text="A small vine looped around the latch like a knot.",
        fix_family="lift",
        safe_booms=2,
        tags={"vine", "latch"},
    ),
    "rusty_hinge": Obstacle(
        id="rusty_hinge",
        label="a rusty upper hinge",
        cause_text="The upper hinge was stiff with rust and would not swing.",
        clue_text="The top hinge was orange and squeaky with rust.",
        fix_family="oil",
        safe_booms=1,
        tags={"rust", "hinge"},
    ),
}

FIXES = {
    "clear_mud": Fix(
        id="clear_mud",
        label="clear the mud away with a twig",
        family="clear",
        act_text="brushed and poked the dried mud away with a neat little twig",
        result_text="When the hard clump fell out, the gate moved again with a soft creak.",
        qa_text="cleared the dried mud from the hinge with a twig",
        tags={"mud", "problem_solving"},
    ),
    "lift_vine": Fix(
        id="lift_vine",
        label="lift the vine off the latch",
        family="lift",
        act_text="lifted the vine from the latch and unwound it one green curl at a time",
        result_text="As soon as the latch was free, the gate clicked and swung open.",
        qa_text="lifted the vine off the latch",
        tags={"vine", "problem_solving"},
    ),
    "oil_hinge": Fix(
        id="oil_hinge",
        label="rub the hinge with a drop of cart oil",
        family="oil",
        act_text="rubbed one shiny drop of cart oil into the rusty hinge and worked it gently",
        result_text="The squeak faded, and the hinge loosened enough for the gate to swing.",
        qa_text="rubbed a drop of oil into the rusty hinge and moved it gently",
        tags={"rust", "problem_solving"},
    ),
}

HEROES = {
    "Pip": "pig",
    "Moss": "boar",
    "Nell": "hen",
    "Tula": "goose",
}

HELPERS = {
    "Fern": "sheep",
    "Rill": "mole",
    "Juniper": "fox",
}

TRAITS = ["eager", "cheerful", "stubborn", "hasty", "bright"]


def compatible_fix(obstacle_id: str, fix_id: str) -> bool:
    return OBSTACLES[obstacle_id].fix_family == FIXES[fix_id].family


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid in SETTINGS:
        for oid in OBSTACLES:
            for fid in FIXES:
                if compatible_fix(oid, fid):
                    combos.append((sid, oid, fid))
    return combos


@dataclass
class StoryParams:
    setting: str
    obstacle: str
    fix: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    hero_trait: str
    booms: int
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="meadow",
        obstacle="mud_jam",
        fix="clear_mud",
        hero_name="Pip",
        hero_type="pig",
        helper_name="Fern",
        helper_type="sheep",
        hero_trait="hasty",
        booms=2,
    ),
    StoryParams(
        setting="orchard",
        obstacle="vine_latch",
        fix="lift_vine",
        hero_name="Nell",
        hero_type="hen",
        helper_name="Rill",
        helper_type="mole",
        hero_trait="cheerful",
        booms=1,
    ),
    StoryParams(
        setting="pond",
        obstacle="rusty_hinge",
        fix="oil_hinge",
        hero_name="Tula",
        hero_type="goose",
        helper_name="Juniper",
        helper_type="fox",
        hero_trait="stubborn",
        booms=2,
    ),
]


def outcome_of(params: StoryParams) -> str:
    obstacle = OBSTACLES[params.obstacle]
    return "cracked" if params.booms > obstacle.safe_booms else "safe"


def explain_rejection(obstacle_id: str, fix_id: str) -> str:
    obstacle = OBSTACLES[obstacle_id]
    fix = FIXES[fix_id]
    return (
        f"(No story: {fix.label} does not match {obstacle.label}. "
        f"This world only allows fixes that solve the real cause of the stuck gate.)"
    )


def introduce(world: World, hero: Entity, setting: Setting) -> None:
    world.say(setting.scene)
    world.say(
        f"There lived a tubby little {hero.type} named {hero.id}, "
        f"so fond of {setting.reward} that {hero.pronoun()} could smell it from the lane."
    )


def see_problem(world: World, hero: Entity, setting: Setting, obstacle: Obstacle) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"One morning {hero.id} hurried toward {setting.gate_kind}, eager to reach "
        f"{setting.place}. But the gate would not open."
    )
    world.say(obstacle.cause_text)
    world.say(obstacle.clue_text)


def boom_push(world: World, hero: Entity, obstacle: Obstacle, count: int) -> None:
    gate = world.get("gate")
    hero.memes["defiance"] += 1
    gate.meters["strain"] += 1
    gate.meters["pushed"] += 1
    hero.meters["sore"] += 1
    word = {1: "once", 2: "again", 3: "yet again"}.get(count, "again")
    if count == 1:
        world.say(
            f'"I can open it with one good shove," said {hero.id}. {hero.pronoun().capitalize()} '
            f"set {hero.pronoun('possessive')} round shoulder to the wood and pushed. Boom!"
        )
    else:
        world.say(
            f"{word.capitalize()}, {hero.pronoun()} pushed with all {hero.pronoun('possessive')} weight. Boom!"
        )
    if count <= obstacle.safe_booms:
        world.say("The gate only shivered and stayed shut.")
    else:
        propagate(world, narrate=False)
        world.say(
            "This time the gate gave a sharp crack. A splinter jumped, and the lane suddenly felt less playful."
        )


def warn(world: World, helper: Entity, hero: Entity, obstacle: Obstacle) -> None:
    helper.memes["care"] += 1
    if world.get("gate").meters["cracked"] >= THRESHOLD:
        world.say(
            f'{helper.id}, a watchful {helper.type}, stepped close and said, '
            f'"Friend, a harder boom will not teach a stuck thing to move. It may only teach it to break."'
        )
    else:
        world.say(
            f'{helper.id}, a patient {helper.type}, tilted {helper.pronoun("possessive")} head and said, '
            f'"Before you boom at it again, look at why it is stuck."'
        )
    world.say(
        f"{helper.id} pointed to the trouble: {obstacle.clue_text[0].lower() + obstacle.clue_text[1:]}"
    )


def solve(world: World, helper: Entity, hero: Entity, fix: Fix) -> None:
    gate = world.get("gate")
    helper.memes["calm"] += 1
    hero.memes["attention"] += 1
    world.say(
        f"Then {helper.id} {fix.act_text}. {fix.result_text}"
    )
    gate.meters["open"] = 1
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1


def mend_if_needed(world: World, helper: Entity, hero: Entity) -> None:
    gate = world.get("gate")
    if gate.meters["cracked"] < THRESHOLD:
        return
    gate.meters["mended"] = 1
    world.say(
        f'Because of the crack, {hero.id} and {helper.id} fetched a strip of willow bark and tied the rail snugly. '
        f'"A problem first asks for eyes," said {helper.id}, "and only afterward for hands."'
    )


def ending(world: World, hero: Entity, helper: Entity, setting: Setting) -> None:
    gate = world.get("gate")
    hero.memes["lesson"] += 1
    if gate.meters["cracked"] >= THRESHOLD:
        world.say(
            f"At last they passed through the gate slowly, and {hero.id} did not lean on it again. "
            f"The tubby little {hero.type} still reached the {setting.reward}, but now with slower steps and wiser eyes."
        )
        world.say(
            "So the lane remembered this: when force begins with boom, trouble may answer with crack."
        )
    else:
        world.say(
            f"They went through together, and even the hinges seemed to sigh with ease. "
            f"{hero.id} tasted the {setting.reward} and smiled, for a careful mind had opened what a hard shove could not."
        )
        world.say(
            "So the lane remembered this: a small thought can open a gate better than a big boom."
        )


def tell(
    setting: Setting,
    obstacle: Obstacle,
    fix: Fix,
    hero_name: str,
    hero_type: str,
    helper_name: str,
    helper_type: str,
    hero_trait: str,
    booms: int,
) -> World:
    world = World(setting=setting)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        traits=["tubby", hero_trait],
        tags={"hero"},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label=helper_name,
        role="helper",
        traits=["patient"],
        tags={"helper"},
    ))
    gate = world.add(Entity(
        id="gate",
        kind="thing",
        type="gate",
        label=setting.gate_kind,
        phrase=f"the {setting.gate_kind}",
        role="obstacle",
        tags={"gate"} | setting.tags | obstacle.tags,
    ))

    world.facts["hero_name"] = hero_name
    world.facts["helper_name"] = helper_name

    introduce(world, hero, setting)
    see_problem(world, hero, setting, obstacle)

    world.para()
    for n in range(1, booms + 1):
        boom_push(world, hero, obstacle, n)

    world.para()
    warn(world, helper, hero, obstacle)
    solve(world, helper, hero, fix)
    mend_if_needed(world, helper, hero)

    world.para()
    ending(world, hero, helper, setting)

    world.facts.update(
        setting=setting,
        obstacle=obstacle,
        fix=fix,
        hero=hero,
        helper=helper,
        gate=gate,
        booms=booms,
        outcome="cracked" if gate.meters["cracked"] >= THRESHOLD else "safe",
        cracked=gate.meters["cracked"] >= THRESHOLD,
        mended=gate.meters["mended"] >= THRESHOLD,
        opened=gate.meters["open"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "gate": [
        (
            "Why should you look at a gate before pushing hard?",
            "A gate can be stuck for a reason, like mud, a vine, or rust. If you look first, you can solve the real problem instead of breaking the gate."
        )
    ],
    "mud": [
        (
            "Why can mud make a hinge stick?",
            "Mud can dry into a hard lump and block the moving parts. Then the hinge cannot swing smoothly."
        )
    ],
    "vine": [
        (
            "How can a vine stop a latch from moving?",
            "A vine can wrap around the latch like a little rope. Until it is lifted away, the latch cannot click free."
        )
    ],
    "rust": [
        (
            "What is rust?",
            "Rust is a rough orange coating that can grow on metal when it gets old and wet. It makes metal parts stiff and hard to move."
        )
    ],
    "problem_solving": [
        (
            "What is problem solving?",
            "Problem solving means noticing what is wrong and choosing a step that fits the real trouble. It often works better than pushing harder."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    obstacle = f["obstacle"]
    fix = f["fix"]
    hero = f["hero"]
    helper = f["helper"]
    return [
        'Write a short fable for a 3-to-5-year-old that includes the words "tubby" and "boom".',
        f"Tell a cautionary animal story where a tubby {hero.type} keeps trying to force open a gate, but a {helper.type} solves the real problem by noticing {obstacle.label}.",
        f"Write a repetitive problem-solving tale set by {setting.place} where the wrong move is more boom and the right move is to {fix.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    setting = f["setting"]
    obstacle = f["obstacle"]
    fix = f["fix"]
    booms = f["booms"]
    hero_name = f["hero_name"]
    helper_name = f["helper_name"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a tubby little {hero.type} named {hero_name} and a careful {helper.type} named {helper_name}. {hero_name} wanted to get through the gate, and {helper_name} helped solve the trouble."
        ),
        (
            "What problem did the hero have?",
            f"{hero_name} wanted to reach {setting.place}, but the gate was stuck because of {obstacle.label}. The problem was not the hero's strength; it was the real thing blocking the gate."
        ),
        (
            f"How many times did {hero_name} push with boom?",
            f"{hero_name} pushed {booms} time{'s' if booms != 1 else ''}, each time with a loud boom. The repetition matters because the hero kept trying the same forceful idea instead of examining the gate."
        ),
        (
            f"How did {helper_name} solve the problem?",
            f"{helper_name} {fix.qa_text}. That worked because it matched the real cause of the stuck gate."
        ),
    ]
    if f["cracked"]:
        qa.append(
            (
                "Why is the story cautionary?",
                f"The hard pushing made the gate crack before the real fix was tried. It warns that doing the same rough thing again and again can make a small problem bigger."
            )
        )
        qa.append(
            (
                "How did the ending show that the hero changed?",
                f"After the crack, {hero_name} went through the gate slowly and did not lean on it again. The ending proves the lesson because the hero moved more carefully, not more noisily."
            )
        )
    else:
        qa.append(
            (
                "What lesson did the hero learn?",
                f"{hero_name} learned to look at the trouble before pushing harder. The gate opened once the real cause was fixed, so thought worked better than force."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The gate opened safely, and the two animals went through together. The calm ending shows that careful problem solving kept the place whole."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"gate", "problem_solving"} | set(world.facts["obstacle"].tags) | set(world.facts["fix"].tags)
    out: list[tuple[str, str]] = []
    for key in ["gate", "mud", "vine", "rust", "problem_solving"]:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
compatible(O, F) :- obstacle(O), fix(F), needs(O, K), solves(F, K).
valid(S, O, F) :- setting(S), obstacle(O), fix(F), compatible(O, F).

outcome(cracked) :- chosen_obstacle(O), chosen_booms(B), safe_booms(O, S), B > S.
outcome(safe)    :- chosen_obstacle(O), chosen_booms(B), safe_booms(O, S), B <= S.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("needs", oid, obstacle.fix_family))
        lines.append(asp.fact("safe_booms", oid, obstacle.safe_booms))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("solves", fid, fix.family))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_booms", params.booms),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate/fix compatibility matches ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            rc = 1
            print("Unexpected StoryError during resolve_params() smoke generation.")
            break
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke-test generation and emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tubby animal learns that solving a problem beats booming at it."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--booms", type=int, choices=[1, 2, 3], help="how many loud boom pushes the hero tries")
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible setting/obstacle/fix combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def choose_hero(rng: random.Random, explicit_name: Optional[str] = None) -> tuple[str, str]:
    if explicit_name:
        if explicit_name in HEROES:
            return explicit_name, HEROES[explicit_name]
        return explicit_name, rng.choice(sorted(set(HEROES.values())))
    name = rng.choice(sorted(HEROES))
    return name, HEROES[name]


def choose_helper(rng: random.Random, avoid_name: str = "", explicit_name: Optional[str] = None) -> tuple[str, str]:
    pool = [n for n in sorted(HELPERS) if n != avoid_name]
    if explicit_name:
        if explicit_name in HELPERS and explicit_name != avoid_name:
            return explicit_name, HELPERS[explicit_name]
        return explicit_name, rng.choice(sorted(set(HELPERS.values())))
    name = rng.choice(pool)
    return name, HELPERS[name]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.fix and not compatible_fix(args.obstacle, args.fix):
        raise StoryError(explain_rejection(args.obstacle, args.fix))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, obstacle_id, fix_id = rng.choice(sorted(combos))
    booms = args.booms if args.booms is not None else rng.choice([1, 2, 3])
    hero_name, hero_type = choose_hero(rng, args.hero_name)
    helper_name, helper_type = choose_helper(rng, avoid_name=hero_name, explicit_name=args.helper_name)
    hero_trait = rng.choice(TRAITS)

    return StoryParams(
        setting=setting_id,
        obstacle=obstacle_id,
        fix=fix_id,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        hero_trait=hero_trait,
        booms=booms,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if not compatible_fix(params.obstacle, params.fix):
        raise StoryError(explain_rejection(params.obstacle, params.fix))

    world = tell(
        setting=SETTINGS[params.setting],
        obstacle=OBSTACLES[params.obstacle],
        fix=FIXES[params.fix],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        hero_trait=params.hero_trait,
        booms=params.booms,
    )

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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, obstacle, fix) combos:\n")
        for setting_id, obstacle_id, fix_id in combos:
            print(f"  {setting_id:8} {obstacle_id:11} {fix_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} at {p.setting}: {p.obstacle} -> {p.fix} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
