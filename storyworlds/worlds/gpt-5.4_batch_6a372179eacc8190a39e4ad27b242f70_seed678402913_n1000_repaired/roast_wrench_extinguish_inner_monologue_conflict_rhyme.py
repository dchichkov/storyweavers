#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/roast_wrench_extinguish_inner_monologue_conflict_rhyme.py
====================================================================================

A standalone storyworld about a child helping with an evening roast, a loose part
that must be fixed with a wrench, a brief conflict between hurry and caution,
and a small fire risk that may need to be extinguished. The prose stays warm and
child-facing, uses simple inner monologue, and carries a few gentle rhymes.

Run it
------
    python storyworlds/worlds/gpt-5.4/roast_wrench_extinguish_inner_monologue_conflict_rhyme.py
    python storyworlds/worlds/gpt-5.4/roast_wrench_extinguish_inner_monologue_conflict_rhyme.py --target stone_path
    python storyworlds/worlds/gpt-5.4/roast_wrench_extinguish_inner_monologue_conflict_rhyme.py --response fan
    python storyworlds/worlds/gpt-5.4/roast_wrench_extinguish_inner_monologue_conflict_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/roast_wrench_extinguish_inner_monologue_conflict_rhyme.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/roast_wrench_extinguish_inner_monologue_conflict_rhyme.py --qa --json
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
PATIENT_TRAITS = {"patient", "careful", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    flammable: bool = False
    fixable_with_wrench: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    image: str
    breeze: str
    rhyme: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Roast:
    id: str
    label: str
    phrase: str
    aroma: str
    turn_text: str
    ready_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    warning: str
    fix_text: str
    risky_action: str
    spill_text: str
    fixable_with_wrench: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    phrase: str
    near_text: str
    flare_text: str
    spread: int = 1
    flammable: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return self.phrase

    @property
    def The(self) -> str:
        return self.phrase[0].upper() + self.phrase[1:]


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_smolder_to_danger(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["smolder"] < THRESHOLD:
            continue
        sig = ("danger", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "yard" in world.entities:
            world.get("yard").meters["danger"] += 1
        hero = world.entities.get("hero")
        helper = world.entities.get("helper")
        if hero is not None:
            hero.memes["fear"] += 1
        if helper is not None:
            helper.memes["alarm"] += 1
        out.append("__flare__")
    return out


CAUSAL_RULES = [
    Rule(name="smolder_to_danger", tag="physical", apply=_r_smolder_to_danger),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def hazard_at_risk(problem: Problem, target: Target) -> bool:
    return problem.fixable_with_wrench and target.flammable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity_of(target: Target, delay: int) -> int:
    return target.spread + delay


def is_contained(response: Response, target: Target, delay: int) -> bool:
    return response.power >= severity_of(target, delay)


def would_wait(trait: str, trust: int) -> bool:
    base = 5 if trait in PATIENT_TRAITS else 3
    return base + trust >= 11


def _spill_ember(world: World, target_ent: Entity, narrate: bool = True) -> None:
    target_ent.meters["smolder"] += 1
    target_ent.meters["singed"] += 1
    propagate(world, narrate=narrate)


def predict_flare(world: World, target_id: str) -> dict:
    sim = world.copy()
    _spill_ember(sim, sim.get(target_id), narrate=False)
    return {
        "smolder": sim.get(target_id).meters["smolder"] >= THRESHOLD,
        "danger": sim.get("yard").meters["danger"],
    }


def opening(world: World, hero: Entity, helper: Entity, setting: Setting, roast: Roast) -> None:
    hero.memes["joy"] += 1
    helper.memes["care"] += 1
    world.say(
        f"At {setting.place}, {setting.image}. {helper.label_word.capitalize()} had set out {roast.phrase} for a family roast, and {roast.aroma} drifted through the air."
    )
    world.say(
        f"{hero.id} stayed close beside {helper.label_word}, listening to the crackle and smiling at the warm glow."
    )
    world.say(
        f'{hero.id} thought, "If supper can roast, I can help the most." The little rhyme danced in {hero.pronoun("possessive")} head and made {hero.pronoun("object")} grin.'
    )


def discover_problem(world: World, helper: Entity, problem: Problem) -> None:
    world.say(
        f"Then {helper.label_word} noticed {problem.label}. \"Oh,\" {helper.pronoun()} said, \"{problem.warning}\""
    )
    world.say(
        f"{helper.label_word.capitalize()} reached for the old wrench from the toolbox. \"One careful twist, and this will be fixed.\""
    )


def warn(world: World, hero: Entity, helper: Entity, target: Target) -> None:
    pred = predict_flare(world, "target")
    hero.memes["hurry"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'"Please wait one minute," {helper.label_word} said. "{target.near_text} is too close. If the roaster wobbles, a hot ember could land there."'
    )
    world.say(
        f'{hero.id} looked at the coals and thought, "Wait feels late, but maybe wait is wise. Fast can surprise."'
    )


def defy(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"But the smell was sweet, and the wish to help tugged harder than the warning. Before the wrench could tighten the loose part, {hero.id} {problem.risky_action}."
    )


def wait_branch(world: World, hero: Entity, helper: Entity, roast: Roast, problem: Problem) -> None:
    hero.memes["relief"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"{hero.id} took one small step back and folded {hero.pronoun('possessive')} hands. \"Slow and right tonight,\" {hero.pronoun()} whispered."
    )
    world.say(
        f"{helper.label_word.capitalize()} used the wrench and {problem.fix_text}. The roaster stood steady again."
    )
    world.say(
        f"Soon they turned the food together, and {roast.turn_text}. When the roast was ready, {roast.ready_text}"
    )


def flare(world: World, hero: Entity, helper: Entity, target_ent: Entity, target: Target, problem: Problem) -> None:
    _spill_ember(world, target_ent, narrate=True)
    world.say(
        f"The loose part jerked. {problem.spill_text}, and one bright ember hopped onto {target.the}. {target.flare_text}"
    )
    world.say(
        f'"Oh no!" {hero.id} cried. Inside, {hero.pronoun()} thought, "I wanted to help, not make trouble."'
    )


def extinguish_success(world: World, helper: Entity, response: Response, target: Target) -> None:
    world.get("target").meters["smolder"] = 0.0
    world.get("yard").meters["danger"] = 0.0
    helper.memes["care"] += 1
    body = response.text.replace("{target}", target.label)
    world.say(
        f"{helper.label_word.capitalize()} moved fast and calm and {body}."
    )
    world.say(
        f'"There," {helper.pronoun()} said softly. "We extinguish little dangers before they grow big."'
    )


def extinguish_fail(world: World, helper: Entity, response: Response, target: Target) -> None:
    world.get("yard").meters["danger"] += 1
    world.get("target").meters["smolder"] += 1
    body = response.fail.replace("{target}", target.label)
    world.say(
        f"{helper.label_word.capitalize()} tried to {body}."
    )
    world.say(
        f"But the flare jumped higher and licked at the edge of the roasting space before it was finally beaten back."
    )


def repair_and_lesson(world: World, hero: Entity, helper: Entity, roast: Roast, problem: Problem) -> None:
    hero.memes["lesson"] += 1
    hero.memes["fear"] = 0.0
    hero.memes["love"] += 1
    helper.memes["love"] += 1
    world.say(
        f"After the scare, {helper.label_word} crouched beside {hero.id}. \"You wanted to help,\" {helper.pronoun()} said, \"and helping means listening when heat is near.\""
    )
    world.say(
        f'{hero.id} nodded. "{roast.label.capitalize()} can wait. Safety first is worth its weight."'
    )
    world.say(
        f"Then {helper.label_word} used the wrench and {problem.fix_text}. This time they worked side by side, slowly and safely, until {roast.ready_text}"
    )


def hard_lesson(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    hero.memes["lesson"] += 1
    hero.memes["love"] += 1
    helper.memes["love"] += 1
    world.say(
        f"When the danger was over, {helper.label_word} hugged {hero.id} close. The roast was ruined, but they were safe, and that mattered more than supper."
    )
    world.say(
        f"{hero.id} leaned in and whispered that {hero.pronoun()} would remember the wrench, the warning, and the need to extinguish danger right away."
    )
    world.say(
        f"Together they tidied the blackened roasting stand, quiet and grateful for each other."
    )


def happy_ending(world: World, hero: Entity, helper: Entity, setting: Setting, roast: Roast) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"At last they shared the warm {roast.label} together. {setting.breeze}"
    )
    world.say(
        f'{hero.id} made up one more rhyme: "Steady hand, glowing pan; safe together, that\'s the plan." {helper.label_word.capitalize()} laughed, and the night felt gentle again.'
    )


def tell(
    setting: Setting,
    roast: Roast,
    problem: Problem,
    target: Target,
    response: Response,
    *,
    hero_name: str = "Mia",
    hero_gender: str = "girl",
    helper_type: str = "grandfather",
    trait: str = "patient",
    trust: int = 6,
    delay: int = 0,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=[trait],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
    ))
    world.add(Entity(id="yard", type="place", label=setting.place))
    world.add(Entity(
        id="roaster",
        type="roaster",
        label="roaster",
        fixable_with_wrench=problem.fixable_with_wrench,
    ))
    target_ent = world.add(Entity(
        id="target",
        type="target",
        label=target.label,
        flammable=target.flammable,
    ))

    opening(world, hero, helper, setting, roast)
    world.para()
    discover_problem(world, helper, problem)
    warn(world, hero, helper, target)

    waited = would_wait(trait, trust)
    if waited:
        world.para()
        wait_branch(world, hero, helper, roast, problem)
        outcome = "waited"
        contained = True
        severity = 0
        ignited = False
    else:
        defy(world, hero, problem)
        world.para()
        flare(world, hero, helper, target_ent, target, problem)
        severity = severity_of(target, delay)
        contained = is_contained(response, target, delay)
        world.para()
        if contained:
            extinguish_success(world, helper, response, target)
            repair_and_lesson(world, hero, helper, roast, problem)
            world.para()
            happy_ending(world, hero, helper, setting, roast)
            outcome = "contained"
        else:
            extinguish_fail(world, helper, response, target)
            hard_lesson(world, hero, helper, problem)
            outcome = "burned"
        ignited = True

    world.facts.update(
        hero=hero,
        helper=helper,
        setting=setting,
        roast=roast,
        problem=problem,
        target_cfg=target,
        target=target_ent,
        response=response,
        trust=trust,
        delay=delay,
        outcome=outcome,
        contained=contained,
        severity=severity,
        ignited=ignited,
        waited=waited,
    )
    return world


SETTINGS = {
    "backyard": Setting(
        id="backyard",
        place="the backyard",
        image="string lights shone over the fence and a striped blanket lay on the grass",
        breeze="A soft backyard breeze carried the last sweet smoke away.",
        rhyme="night bright",
        tags={"yard"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the little orchard",
        image="apple trees stood dark and kind around the fire ring",
        breeze="The orchard leaves rustled like a quiet clap.",
        rhyme="glow slow",
        tags={"orchard"},
    ),
    "courtyard": Setting(
        id="courtyard",
        place="the brick courtyard",
        image="flower pots lined the wall and the bricks held the day's last warmth",
        breeze="The courtyard stayed cozy even after the flames settled down.",
        rhyme="warm calm",
        tags={"yard"},
    ),
}

ROASTS = {
    "corn": Roast(
        id="corn",
        label="corn",
        phrase="fresh ears of corn in a wire basket",
        aroma="the smell of butter and sweet corn",
        turn_text="the kernels grew golden and spotted brown",
        ready_text="the corn came off the fire soft, sweet, and shining with butter.",
        tags={"corn", "roast"},
    ),
    "chestnuts": Roast(
        id="chestnuts",
        label="chestnuts",
        phrase="a little pan of chestnuts with split shells",
        aroma="a toasty nutty smell",
        turn_text="the shells clicked and opened with tiny pops",
        ready_text="the chestnuts were hot in their shells and perfect for peeling.",
        tags={"chestnuts", "roast"},
    ),
    "apples": Roast(
        id="apples",
        label="apples",
        phrase="halved apples wrapped for roasting",
        aroma="the smell of warm fruit and cinnamon",
        turn_text="the apple edges browned and bubbled",
        ready_text="the apples came out soft enough to eat with a spoon.",
        tags={"apples", "roast"},
    ),
}

PROBLEMS = {
    "wheel": Problem(
        id="wheel",
        label="one little wheel on the roasting cart wobbling",
        warning="the cart wheel is loose",
        fix_text="tightened the wheel bolt until it no longer shivered",
        risky_action="reached out and gave the cart a turn anyway",
        spill_text="The cart tipped sideways",
        fixable_with_wrench=True,
        tags={"wrench", "wheel"},
    ),
    "handle": Problem(
        id="handle",
        label="the turning handle hanging loose on its metal pin",
        warning="the turning handle needs tightening",
        fix_text="snugged the handle bolt tight so it turned smooth and true",
        risky_action="grabbed the handle and tried to turn it alone",
        spill_text="The handle slipped in a sharp clack",
        fixable_with_wrench=True,
        tags={"wrench", "handle"},
    ),
    "lid": Problem(
        id="lid",
        label="the roaster lid rattling on one side",
        warning="the lid hinge is loose",
        fix_text="set the hinge straight and tightened it until the lid sat firm",
        risky_action="lifted the lid for a peek before the fix was done",
        spill_text="The lid knocked the basket hard",
        fixable_with_wrench=True,
        tags={"wrench", "lid"},
    ),
}

TARGETS = {
    "leaves": Target(
        id="leaves",
        label="dry leaves",
        phrase="the dry leaves by the stones",
        near_text="Those dry leaves by the stones",
        flare_text="A thin orange edge began to curl through them.",
        spread=2,
        flammable=True,
        tags={"leaves", "fire"},
    ),
    "napkin": Target(
        id="napkin",
        label="paper napkin",
        phrase="the paper napkin on the bench",
        near_text="That paper napkin on the bench",
        flare_text="Its corner darkened, then glowed with a sharp little flame.",
        spread=2,
        flammable=True,
        tags={"paper", "fire"},
    ),
    "towel": Target(
        id="towel",
        label="dish towel",
        phrase="the dish towel hanging from the chair",
        near_text="That dish towel on the chair",
        flare_text="A smoky line crawled along the cloth.",
        spread=3,
        flammable=True,
        tags={"cloth", "fire"},
    ),
    "stone_path": Target(
        id="stone_path",
        label="stone path",
        phrase="the stone path",
        near_text="The stone path",
        flare_text="Nothing happened at all.",
        spread=0,
        flammable=False,
        tags={"stone"},
    ),
}

RESPONSES = {
    "water_pail": Response(
        id="water_pail",
        sense=3,
        power=3,
        text="snatched up the water pail and poured it over the {target} until the glow went dark",
        fail="pour water on the {target}, but the flare had already raced wider than the splash",
        qa_text="poured water over the {target} until the fire went out",
        tags={"water", "extinguish"},
    ),
    "damp_cloth": Response(
        id="damp_cloth",
        sense=3,
        power=2,
        text="grabbed a damp cloth and pressed it over the {target}, smothering the ember",
        fail="press a damp cloth over the {target}, but the heat had spread past one small cover",
        qa_text="smothered the ember with a damp cloth",
        tags={"cloth", "extinguish"},
    ),
    "sand": Response(
        id="sand",
        sense=2,
        power=2,
        text="scooped sand from the bucket and buried the glowing spot on the {target}",
        fail="throw sand on the {target}, but the ember had already skipped beyond the first patch",
        qa_text="covered the glowing spot with sand to extinguish it",
        tags={"sand", "extinguish"},
    ),
    "fan": Response(
        id="fan",
        sense=1,
        power=0,
        text="waved a tray at the {target}",
        fail="fan the {target}, which only fed the ember more air",
        qa_text="waved at the fire",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Ella", "Zoe"]
BOY_NAMES = ["Leo", "Ben", "Sam", "Noah", "Finn", "Max"]
TRAITS = ["patient", "careful", "thoughtful", "eager", "hasty", "bouncy"]


@dataclass
class StoryParams:
    setting: str
    roast: str
    problem: str
    target: str
    response: str
    hero_name: str
    hero_gender: str
    helper_type: str
    trait: str
    trust: int = 6
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="backyard",
        roast="corn",
        problem="wheel",
        target="leaves",
        response="water_pail",
        hero_name="Mia",
        hero_gender="girl",
        helper_type="grandfather",
        trait="patient",
        trust=7,
        delay=0,
    ),
    StoryParams(
        setting="orchard",
        roast="chestnuts",
        problem="handle",
        target="napkin",
        response="damp_cloth",
        hero_name="Leo",
        hero_gender="boy",
        helper_type="grandmother",
        trait="eager",
        trust=5,
        delay=0,
    ),
    StoryParams(
        setting="courtyard",
        roast="apples",
        problem="lid",
        target="towel",
        response="sand",
        hero_name="Nora",
        hero_gender="girl",
        helper_type="father",
        trait="hasty",
        trust=4,
        delay=1,
    ),
    StoryParams(
        setting="backyard",
        roast="corn",
        problem="handle",
        target="towel",
        response="water_pail",
        hero_name="Ben",
        hero_gender="boy",
        helper_type="mother",
        trait="careful",
        trust=6,
        delay=0,
    ),
]


KNOWLEDGE = {
    "roast": [
        ("What does roast mean in cooking?",
         "To roast food means to cook it with steady heat until it becomes soft, brown, or toasty. Roasted food often smells warm and sweet.")
    ],
    "wrench": [
        ("What is a wrench?",
         "A wrench is a tool used to tighten or loosen nuts and bolts. It helps fix metal parts that are too loose to stay safe on their own.")
    ],
    "extinguish": [
        ("What does extinguish mean?",
         "To extinguish a fire means to put it out so it stops glowing and burning. Grown-ups do this quickly so a small danger does not become a big one.")
    ],
    "fire": [
        ("Why are little embers dangerous?",
         "An ember may look tiny, but it is still very hot. If it lands on paper, cloth, or dry leaves, it can start a fire.")
    ],
    "water": [
        ("Why does water put out many small fires?",
         "Water cools the hot spot down. Without enough heat, the fire cannot keep burning.")
    ],
    "sand": [
        ("How can sand help put out a small fire?",
         "Sand covers the glowing part and blocks some of the air the fire needs. That helps extinguish the flame.")
    ],
    "cloth": [
        ("How can a damp cloth stop a tiny flare?",
         "A damp cloth can cover a very small ember and smother it. A grown-up must do it quickly and carefully.")
    ],
}
KNOWLEDGE_ORDER = ["roast", "wrench", "extinguish", "fire", "water", "sand", "cloth"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for roast_id in ROASTS:
            for problem_id, problem in PROBLEMS.items():
                for target_id, target in TARGETS.items():
                    if hazard_at_risk(problem, target):
                        combos.append((setting_id, roast_id, problem_id, target_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    if would_wait(params.trait, params.trust):
        return "waited"
    return "contained" if is_contained(RESPONSES[params.response], TARGETS[params.target], params.delay) else "burned"


def explain_rejection(problem: Problem, target: Target) -> str:
    if not target.flammable:
        return (
            f"(No story: {target.phrase} will not catch from a stray ember, so there is no honest need to extinguish anything. "
            f"Pick a flammable nearby target such as leaves, a towel, or a paper napkin.)"
        )
    if not problem.fixable_with_wrench:
        return (
            f"(No story: {problem.label} is not a wrench-fixable problem here, so the core repair beat would not make sense.)"
        )
    return "(No story: this combination does not create a plausible ember danger.)"


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it is below the common-sense threshold "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    roast = f["roast"]
    problem = f["problem"]
    target = f["target_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a heartwarming story for a 3-to-5-year-old that includes the words "roast," "wrench," and "extinguish." '
        f"Use inner monologue, a small conflict, and at least one gentle rhyme."
    )
    if outcome == "waited":
        return [
            base,
            f"Tell a cozy story where {hero.id} wants to help with a {roast.label} roast, but waits while a grown-up uses a wrench to fix {problem.label}. End with warmth and relief.",
            f"Write a story in which a child argues with waiting, thinks quietly inside, then chooses patience and helps safely at the end.",
        ]
    if outcome == "contained":
        return [
            base,
            f"Tell a story where {hero.id} acts too soon during a {roast.label} roast, a tiny ember lands on {target.the}, and a calm grown-up extinguishes it before it spreads.",
            f"Write a gentle cautionary tale with rhyme and inner thoughts, where a loose roasting part must be fixed with a wrench after a brief scare.",
        ]
    return [
        base,
        f"Tell a sadder cautionary story where {hero.id} acts before the wrench repair is done, and a small flare grows large enough to ruin the roast even though everyone stays safe.",
        f"Write a story about hurry versus care, with a warm family bond but a spoiled supper after the fire is hard to extinguish.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    roast = f["roast"]
    problem = f["problem"]
    target = f["target_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    pw = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {pw}, who are together at an evening roast. They care about each other, even when they disagree for a moment."
        ),
        (
            f"What was wrong with the roaster?",
            f"{problem.label.capitalize()} was the problem. That is why {pw} reached for a wrench instead of letting the roast continue right away."
        ),
        (
            f"What was the conflict in the story?",
            f"The conflict was that {hero.id} wanted to help at once, but {pw} wanted to fix the loose part first. The heat made rushing feel tempting, while the warning called for patience."
        ),
        (
            f"What did {hero.id} think inside {hero.pronoun('possessive')} head?",
            f"{hero.id} had an inner monologue about wanting to help and not wanting to wait. Those thoughts showed the tug between hurry and safety before the big choice."
        ),
    ]
    if outcome == "waited":
        qa.append((
            f"Why did nothing catch fire?",
            f"Nothing caught fire because {hero.id} waited while {pw} used the wrench and fixed the problem first. Once the roaster was steady, no ember spilled onto anything nearby."
        ))
        qa.append((
            "How did the story end?",
            f"It ended warmly with the {roast.label} roasting safely and the family sharing food together. The ending image proves that patience changed the night."
        ))
    elif outcome == "contained":
        body = response.qa_text.replace("{target}", target.label)
        qa.append((
            f"What happened when {hero.id} acted too soon?",
            f"A hot ember landed on {target.the}, and it started to smolder. The danger came from using the loose roaster before the wrench repair was done."
        ))
        qa.append((
            f"How did {pw} fix the danger?",
            f"{pw.capitalize()} {body}. That quick response extinguished the little flare before it could spread farther."
        ))
        qa.append((
            f"What did {hero.id} learn?",
            f"{hero.id} learned that helping near heat means listening first. The lesson came from seeing how one hurried choice almost spoiled the whole roast."
        ))
    else:
        qa.append((
            f"Could {pw} save the roast?",
            f"No. {pw.capitalize()} tried to extinguish the flare, but it spread too far and the food was ruined. Everyone stayed safe, yet the supper was lost because the fire had too much time to grow."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with a hug, a spoiled roast, and a quiet promise to be more careful next time. The family lost supper, but they did not lose each other."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"roast", "wrench", "extinguish", "fire"}
    response = f["response"]
    if "water" in response.tags:
        tags.add("water")
    if "sand" in response.tags:
        tags.add("sand")
    if response.id == "damp_cloth":
        tags.add("cloth")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.flammable:
            bits.append("flammable=True")
        if ent.fixable_with_wrench:
            bits.append("fixable_with_wrench=True")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(P, T) :- problem(P), target(T), wrench_fixable(P), flammable(T).
valid(S, R, P, T) :- setting(S), roast(R), hazard(P, T).

sensible(X) :- response(X), sense(X, V), sense_min(M), V >= M.

patient_now(T) :- trait(T), patient_trait(T).
patient_value(5) :- trait(T), patient_now(T).
patient_value(3) :- trait(T), not patient_now(T).
waited :- patient_value(P), trust(TR), P + TR >= 11.

severity(Sp + D) :- chosen_target(T), spread(T, Sp), delay(D).
contained :- chosen_response(R), power(R, P), severity(S), P >= S.

outcome(waited) :- waited.
outcome(contained) :- not waited, contained.
outcome(burned) :- not waited, not contained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid in ROASTS:
        lines.append(asp.fact("roast", rid))
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if problem.fixable_with_wrench:
            lines.append(asp.fact("wrench_fixable", pid))
    for tid, target in TARGETS.items():
        lines.append(asp.fact("target", tid))
        lines.append(asp.fact("spread", tid, target.spread))
        if target.flammable:
            lines.append(asp.fact("flammable", tid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    for trait in sorted(PATIENT_TRAITS):
        lines.append(asp.fact("patient_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_target", params.target),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("trait", params.trait),
        asp.fact("trust", params.trust),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a cozy roast, a wrench repair, a brief conflict, and a fire-safety lesson."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--roast", choices=ROASTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--trust", type=int, choices=list(range(0, 11)))
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed")
    ap.add_argument("--all", action="store_true", help="render curated set")
    ap.add_argument("--trace", action="store_true", help="dump world model")
    ap.add_argument("--qa", action="store_true", help="include Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target is not None:
        target = TARGETS[args.target]
        problem = PROBLEMS[args.problem] if args.problem is not None else next(iter(PROBLEMS.values()))
        if not target.flammable:
            raise StoryError(explain_rejection(problem, target))
    if args.problem is not None and args.target is not None:
        if not hazard_at_risk(PROBLEMS[args.problem], TARGETS[args.target]):
            raise StoryError(explain_rejection(PROBLEMS[args.problem], TARGETS[args.target]))
    if args.response is not None and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.roast is None or combo[1] == args.roast)
        and (args.problem is None or combo[2] == args.problem)
        and (args.target is None or combo[3] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, roast_id, problem_id, target_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _pick_name(rng, gender)
    helper_type = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    trust = args.trust if args.trust is not None else rng.randint(3, 8)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting_id,
        roast=roast_id,
        problem=problem_id,
        target=target_id,
        response=response_id,
        hero_name=name,
        hero_gender=gender,
        helper_type=helper_type,
        trait=trait,
        trust=trust,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        roast = ROASTS[params.roast]
        problem = PROBLEMS[params.problem]
        target = TARGETS[params.target]
        response = RESPONSES[params.response]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter: {exc.args[0]})") from exc

    if not hazard_at_risk(problem, target):
        raise StoryError(explain_rejection(problem, target))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        setting=setting,
        roast=roast,
        problem=problem,
        target=target,
        response=response,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_type=params.helper_type,
        trait=params.trait,
        trust=params.trust,
        delay=params.delay,
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


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_responses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving random seed {seed}.")
            break
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")
        for bad in mismatches[:5]:
            print("  ", bad)

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("empty story")
        sink = io.StringIO()
        with redirect_stdout(sink):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (setting, roast, problem, target) combos:\n")
        for setting_id, roast_id, problem_id, target_id in combos:
            print(f"  {setting_id:10} {roast_id:10} {problem_id:8} {target_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero_name}: {p.roast} roast, {p.problem}, {p.target} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
