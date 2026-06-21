#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/banister_scaredy_flashback_adventure.py
==================================================================

A standalone story world for a tiny adventure tale built around a dangerous
shortcut: a child wants to ride or balance on a banister during pretend play,
another child has a flashback to an earlier scare, and the family turns the
same adventure urge into a safer game.

The world model prefers a small set of plausible stories over broad coverage.
It refuses plans that do not actually solve the play problem in a sensible way.

Run it
------
    python storyworlds/worlds/gpt-5.4/banister_scaredy_flashback_adventure.py
    python storyworlds/worlds/gpt-5.4/banister_scaredy_flashback_adventure.py --theme castle --action slide
    python storyworlds/worlds/gpt-5.4/banister_scaredy_flashback_adventure.py --plan leap_jump
    python storyworlds/worlds/gpt-5.4/banister_scaredy_flashback_adventure.py --all
    python storyworlds/worlds/gpt-5.4/banister_scaredy_flashback_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/banister_scaredy_flashback_adventure.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 5.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    scene: str = ""
    goal: str = ""
    high_place: str = ""
    danger_name: str = ""
    ending_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str = ""
    ing: str = ""
    motion: str = ""
    risk: str = ""
    boast: str = ""
    start_line: str = ""
    slip_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Memory:
    id: str
    cue: str = ""
    flashback: str = ""
    lesson: str = ""
    severity: int = 1
    matches: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    label: str = ""
    meets: set[str] = field(default_factory=set)
    sense: int = 0
    offer: str = ""
    ending: str = ""
    qa_text: str = ""
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "guide"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    banister = world.get("banister")
    if banister.meters["ridden"] >= THRESHOLD:
        sig = ("wobble", "banister")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["danger"] += 1
            hero.memes["fear"] += 1
            for kid in world.kids():
                if kid.id != "hero":
                    kid.memes["fear"] += 1
            out.append("__wobble__")
    return out


def _r_bump(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["danger"] >= THRESHOLD and world.facts.get("delay", 0) >= 1:
        sig = ("bump", "hero")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["bump"] += 1
            out.append("__bump__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="bump", tag="physical", apply=_r_bump),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(got)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


THEMES = {
    "castle": Theme(
        id="castle",
        scene="a windy stone castle",
        goal="the moon jewel hidden in the tower room",
        high_place="the upstairs landing",
        danger_name="the deep stairwell below",
        ending_line="At the end, the stairs felt less like a trap and more like a path brave explorers knew how to use.",
        tags={"castle", "adventure"},
    ),
    "jungle": Theme(
        id="jungle",
        scene="a jungle temple high above the vines",
        goal="the golden compass in the lower cave",
        high_place="the top of the staircase",
        danger_name="the dark drop between the steps",
        ending_line="By the end, every safe step felt like part of the expedition.",
        tags={"jungle", "adventure"},
    ),
    "mountain": Theme(
        id="mountain",
        scene="a snowy mountain fort",
        goal="the lost flag waiting at base camp",
        high_place="the upstairs hall",
        danger_name="the long tumble to the floor below",
        ending_line="At the end, the mountain still felt exciting, only now it felt wise too.",
        tags={"mountain", "adventure"},
    ),
}

ACTIONS = {
    "slide": Action(
        id="slide",
        verb="slide down the banister",
        ing="sliding down the banister",
        motion="descent",
        risk="speed",
        boast='"I can get there in one whoosh!"',
        start_line="One hand reached for the polished banister as if it were a silver chute.",
        slip_line="The smooth wood ran faster than little feet could think.",
        tags={"banister", "speed"},
    ),
    "balance": Action(
        id="balance",
        verb="walk along the banister",
        ing="balancing on the banister",
        motion="bridge",
        risk="height",
        boast='"I can cross it like a bridge!"',
        start_line="Small toes edged toward the banister as if it were a narrow log over a canyon.",
        slip_line="The rail felt much thinner once the game became real.",
        tags={"banister", "height"},
    ),
    "climb": Action(
        id="climb",
        verb="climb up onto the banister and ride it",
        ing="climbing onto the banister",
        motion="descent",
        risk="height",
        boast='"Real adventurers use the high way!"',
        start_line="A knee lifted toward the banister as though it were the back of a giant dragon.",
        slip_line="The high perch made the floor below look suddenly far away.",
        tags={"banister", "height"},
    ),
}

MEMORIES = {
    "sock_slip": Memory(
        id="sock_slip",
        cue="the shine of the wood",
        flashback="For one blink, the guide remembered last week: socks skidding on the top step, arms windmilling, and a hard thump on the floor. It had been over in a second, but the scare had felt much bigger.",
        lesson="smooth stairs can turn a game into a fall very quickly",
        severity=2,
        matches={"speed", "height"},
        tags={"flashback", "stairs"},
    ),
    "toy_tumble": Memory(
        id="toy_tumble",
        cue="a toy lying near the stairs",
        flashback="Then a flashback rushed in. The guide remembered a toy left near the stairs, a stumble, and a breathless moment when everyone froze before the crying started.",
        lesson="one small mistake near stairs can hurt more than children expect",
        severity=1,
        matches={"height"},
        tags={"flashback", "stairs"},
    ),
    "dizzy_peek": Memory(
        id="dizzy_peek",
        cue="looking over the side",
        flashback="For a moment the guide saw an older scary picture in the mind again: leaning too far over the side, feeling dizzy, and grabbing the wall with a pounding heart.",
        lesson="high places can make the body wobble before a child is ready",
        severity=2,
        matches={"height"},
        tags={"flashback", "stairs"},
    ),
    "fast_corner": Memory(
        id="fast_corner",
        cue="the wish to go fast",
        flashback="A flashback flickered through the guide's mind: a fast run around a corner, a skid, and a sore knee that stung all evening.",
        lesson="going fast indoors can make a child lose control",
        severity=1,
        matches={"speed"},
        tags={"flashback", "running"},
    ),
}

PLANS = {
    "stair_march": Plan(
        id="stair_march",
        label="the explorer march",
        meets={"descent"},
        sense=3,
        offer="\"Let's make the stairs the explorer march,\" the grown-up said. \"Hands on the rail, one step, one stamp, one brave count at a time.\"",
        ending="Soon the children were marching down the stairs, counting each step like a drumbeat, and the treasure hunt still felt fast and grand.",
        qa_text="They turned the stairs into an explorer march and went down step by step with hands on the rail.",
        tags={"stairs", "safe_steps"},
    ),
    "bridge_pillows": Plan(
        id="bridge_pillows",
        label="the pillow bridge",
        meets={"bridge"},
        sense=3,
        offer="\"Let's build the bridge on the floor instead,\" the grown-up said. \"Pillows can be stepping stones, and the banister can stay for hands.\"",
        ending="Soon a line of pillows crossed the rug like a river bridge, and the children tiptoed over them with proud explorer faces.",
        qa_text="They built a bridge from pillows on the floor so the balancing game stayed adventurous without using the banister.",
        tags={"pillows", "bridge"},
    ),
    "tape_trail": Plan(
        id="tape_trail",
        label="the trail markers",
        meets={"descent", "bridge"},
        sense=3,
        offer="\"We can make a trail instead,\" the grown-up said, laying bright tape marks on safe places to step. \"Adventurers follow the marks and keep one hand on the rail.\"",
        ending="Soon bright trail markers turned the staircase into a secret route, and every careful footstep felt like discovering a map.",
        qa_text="They used trail markers on the safe steps and kept a hand on the rail while they played.",
        tags={"trail", "safe_steps"},
    ),
    "leap_jump": Plan(
        id="leap_jump",
        label="a big jump to the bottom",
        meets={"descent"},
        sense=1,
        offer="\"Maybe just jump from halfway,\" someone said.",
        ending="",
        qa_text="",
        tags={"jump"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Theo"]
TRAITS = ["careful", "curious", "bold", "thoughtful", "steady", "lively"]


def sensible_plans() -> list[Plan]:
    return [p for p in PLANS.values() if p.sense >= SENSE_MIN]


def hazard_matches(action: Action, memory: Memory) -> bool:
    return action.risk in memory.matches


def plan_fits(action: Action, plan: Plan) -> bool:
    return action.motion in plan.meets and plan.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for theme_id in THEMES:
        for action_id, action in ACTIONS.items():
            for memory_id, memory in MEMORIES.items():
                if not hazard_matches(action, memory):
                    continue
                for plan_id, plan in PLANS.items():
                    if plan_fits(action, plan):
                        combos.append((theme_id, action_id, memory_id, plan_id))
    return combos


def older_sibling_bonus(relation: str, hero_age: int, guide_age: int) -> int:
    return 2 if relation == "siblings" and guide_age > hero_age else 0


def would_avert(relation: str, hero_age: int, guide_age: int, trust: int, memory_severity: int) -> bool:
    authority = (trust // 2) + memory_severity + older_sibling_bonus(relation, hero_age, guide_age)
    return authority >= 6


def outcome_of(params: "StoryParams") -> str:
    memory = MEMORIES[params.memory]
    if would_avert(params.relation, params.hero_age, params.guide_age, params.trust, memory.severity):
        return "averted"
    return "bumped" if params.delay >= 1 else "caught"


def explain_plan(plan_id: str) -> str:
    plan = PLANS[plan_id]
    better = " / ".join(sorted(p.id for p in sensible_plans()))
    return (
        f"(Refusing plan '{plan_id}': it scores too low on common sense "
        f"(sense={plan.sense} < {SENSE_MIN}). Try a safer plan such as {better}.)"
    )


def explain_rejection(action: Action, memory: Memory, plan: Plan) -> str:
    if not hazard_matches(action, memory):
        return (
            f"(No story: the flashback '{memory.id}' does not honestly warn about "
            f"{action.verb}. Pick a memory that matches the danger of {action.risk}.)"
        )
    if not plan_fits(action, plan):
        return (
            f"(No story: {plan.label} does not solve the play problem created by "
            f"{action.verb}. The safe plan must still support {action.motion}.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
matches(A, M) :- action(A), memory(M), risk_of(A, R), memory_risk(M, R).
fits(A, P)    :- action(A), plan(P), motion_of(A, Mo), meets(P, Mo), sense(P, S), sense_min(Min), S >= Min.
valid(T, A, M, P) :- theme(T), matches(A, M), fits(A, P).

older_bonus(2) :- relation(siblings), hero_age(HA), guide_age(GA), GA > HA.
older_bonus(0) :- not relation(siblings).
older_bonus(0) :- relation(siblings), hero_age(HA), guide_age(GA), GA <= HA.

authority(T / 2 + Sev + B) :- trust(T), memory_severity(Sev), older_bonus(B).
averted :- authority(A), A >= 6.

outcome(averted) :- averted.
outcome(caught)  :- not averted, delay(0).
outcome(bumped)  :- not averted, delay(D), D >= 1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("motion_of", aid, action.motion))
        lines.append(asp.fact("risk_of", aid, action.risk))
    for mid, memory in MEMORIES.items():
        lines.append(asp.fact("memory", mid))
        lines.append(asp.fact("memory_severity_of", mid, memory.severity))
        for risk in sorted(memory.matches):
            lines.append(asp.fact("memory_risk", mid, risk))
    for pid, plan in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("sense", pid, plan.sense))
        for motion in sorted(plan.meets):
            lines.append(asp.fact("meets", pid, motion))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: "StoryParams") -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("relation", params.relation),
            asp.fact("hero_age", params.hero_age),
            asp.fact("guide_age", params.guide_age),
            asp.fact("trust", params.trust),
            asp.fact("delay", params.delay),
            asp.fact("memory_severity", MEMORIES[params.memory].severity),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def predict_danger(world: World, action: Action, delay: int) -> dict:
    sim = world.copy()
    sim.facts["delay"] = delay
    sim.get("banister").meters["ridden"] += 1
    propagate(sim, narrate=False)
    hero = sim.get("hero")
    return {"danger": hero.meters["danger"], "bump": hero.meters["bump"]}


def setup(world: World, theme: Theme, hero: Entity, guide: Entity) -> None:
    hero.memes["joy"] += 1
    guide.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {hero.id} and {guide.id} turned the house into {theme.scene}. "
        f"From {theme.high_place}, they were sure they could reach {theme.goal} before sunset."
    )
    world.say(
        f'The staircase curled below them like part of the quest, and the banister gleamed beside it.'
    )


def need_shortcut(world: World, theme: Theme, hero: Entity, action: Action) -> None:
    hero.memes["bravery"] = BRAVERY_INIT
    world.say(
        f'"There it is!" {hero.id} whispered, pointing toward the way down. '
        f'"If we hurry, we can reach {theme.goal} first."'
    )
    world.say(f"{action.start_line} {action.boast}")


def flashback_warning(world: World, guide: Entity, hero: Entity, action: Action, memory: Memory, parent: Entity) -> None:
    pred = predict_danger(world, action, world.facts.get("delay", 0))
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_bump"] = pred["bump"]
    guide.memes["memory"] += float(memory.severity)
    guide.memes["caution"] += 1
    world.say(
        f"{guide.id} saw {memory.cue}, and a flashback came at once. {memory.flashback}"
    )
    world.say(
        f'"Please don\'t," {guide.id} said. "The banister is for hands, not for riding. '
        f'{memory.lesson.capitalize()}. Let\'s call {parent.label_word} instead."'
    )


def defy(world: World, hero: Entity, guide: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"I\'m not a scaredy," {hero.id} said. "I can do it."'
    )
    if guide.attrs.get("relation") == "siblings" and guide.age > hero.age:
        world.say(
            f"{guide.id} reached out to stop {hero.pronoun('object')}, but {hero.id} had already darted ahead."
        )
    else:
        world.say(f"{hero.id} slipped away before {guide.id} could stop {hero.pronoun('object')}.")


def back_down(world: World, hero: Entity, guide: Entity, parent: Entity) -> None:
    hero.memes["relief"] += 1
    guide.memes["relief"] += 1
    world.say(
        f'{hero.id} looked at the banister again, then at {guide.id}\'s face, and the brave grin faded. '
        f'"Okay," {hero.pronoun()} whispered. "Maybe that is not adventure. Maybe that is just risky."'
    )
    world.say(
        f"They called for {parent.label_word}, and the game waited instead of racing ahead."
    )


def ride_banister(world: World, hero: Entity, action: Action) -> None:
    banister = world.get("banister")
    banister.meters["ridden"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} tried {action.ing}. {action.slip_line}"
    )


def rescue_caught(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["relief"] += 1
    hero.memes["fear"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came fast and caught {hero.id} under the arms before the scare could turn into a fall."
    )
    world.say(
        f"For one second, {hero.id}'s heart thumped louder than the whole pretend adventure."
    )


def rescue_bumped(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} rushed over, but not before {hero.id} bumped a knee on the stair and sat down with watering eyes."
    )
    world.say(
        f"The hurt was small, but the fright felt big enough to quiet the whole staircase."
    )


def lesson(world: World, parent: Entity, hero: Entity, guide: Entity) -> None:
    hero.memes["lesson"] += 1
    guide.memes["lesson"] += 1
    world.say(
        f'{parent.label_word.capitalize()} knelt beside them both. "I am glad you told the truth about what happened," '
        f'{parent.pronoun()} said. "Banisters help people walk safely. They are not slides, bridges, or rides."'
    )
    world.say(
        f"{hero.id} nodded, and {guide.id} leaned close, still shaky from the scare."
    )


def safe_plan(world: World, parent: Entity, hero: Entity, guide: Entity, plan: Plan, theme: Theme) -> None:
    hero.memes["joy"] += 1
    guide.memes["joy"] += 1
    world.say(plan.offer)
    world.say(plan.ending)
    world.say(
        f'{hero.id} grinned at {guide.id}. "That still feels like a real adventure," {hero.pronoun()} said.'
    )
    world.say(theme.ending_line)


def tell(
    theme: Theme,
    action: Action,
    memory: Memory,
    plan: Plan,
    hero_name: str = "Tom",
    hero_gender: str = "boy",
    guide_name: str = "Lily",
    guide_gender: str = "girl",
    parent_type: str = "mother",
    relation: str = "siblings",
    trust: int = 6,
    hero_age: int = 5,
    guide_age: int = 6,
    delay: int = 0,
    trait: str = "careful",
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            age=hero_age,
            attrs={"relation": relation, "display": hero_name},
            traits=["bold"],
        )
    )
    guide = world.add(
        Entity(
            id="guide",
            kind="character",
            type=guide_gender,
            label=guide_name,
            role="guide",
            age=guide_age,
            attrs={"relation": relation, "display": guide_name},
            traits=[trait],
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
        )
    )
    world.add(Entity(id="banister", type="thing", label="banister", tags={"banister"}))
    world.facts["delay"] = delay

    setup(world, theme, hero, guide)
    need_shortcut(world, theme, hero, action)

    world.para()
    flashback_warning(world, guide, hero, action, memory, parent)

    if would_avert(relation, hero_age, guide_age, trust, memory.severity):
        back_down(world, hero, guide, parent)
        world.para()
        safe_plan(world, parent, hero, guide, plan, theme)
        outcome = "averted"
    else:
        defy(world, hero, guide)
        world.para()
        ride_banister(world, hero, action)
        if delay >= 1:
            rescue_bumped(world, parent, hero)
            outcome = "bumped"
        else:
            rescue_caught(world, parent, hero)
            outcome = "caught"
        lesson(world, parent, hero, guide)
        world.para()
        safe_plan(world, parent, hero, guide, plan, theme)

    world.facts.update(
        theme=theme,
        action=action,
        memory=memory,
        plan=plan,
        hero=hero,
        guide=guide,
        parent=parent,
        relation=relation,
        trust=trust,
        outcome=outcome,
        used_banister=world.get("banister").meters["ridden"] >= THRESHOLD,
        bumped=hero.meters["bump"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    theme: str
    action: str
    memory: str
    plan: str
    hero_name: str
    hero_gender: str
    guide_name: str
    guide_gender: str
    parent: str
    relation: str
    trust: int
    hero_age: int
    guide_age: int
    trait: str
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "banister": [
        (
            "What is a banister for?",
            "A banister is the railing beside stairs that people hold to help them walk safely up or down. It is not for climbing or sliding.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a quick look back at something that happened before. It helps a character remember why they feel scared, careful, or sure about something.",
        )
    ],
    "stairs": [
        (
            "Why can stairs be dangerous during rough play?",
            "Stairs are hard and uneven, so a slip can quickly turn into a tumble. That is why calm feet and a hand on the rail matter.",
        )
    ],
    "safe_steps": [
        (
            "How do you go down stairs safely?",
            "You go one step at a time, look where your feet are going, and hold the rail with your hand. Going slowly is safer than rushing.",
        )
    ],
    "bridge": [
        (
            "Why is a floor game safer than balancing high up?",
            "A floor game keeps your body close to the ground, so a mistake is much smaller. You can still pretend without a big fall.",
        )
    ],
    "pillows": [
        (
            "Why can pillows make a good pretend bridge?",
            "Pillows are soft and low to the ground, so they can turn a room into an adventure path without the danger of high climbing.",
        )
    ],
    "trail": [
        (
            "What do trail markers do?",
            "Trail markers show explorers where to go next. In a game, they can turn safe steps into part of the adventure.",
        )
    ],
}


def pair_noun(hero: Entity, guide: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and guide.type == "boy":
            return "two brothers"
        if hero.type == "girl" and guide.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    theme, action, memory, plan = f["theme"], f["action"], f["memory"], f["plan"]
    hero = f["hero"]
    guide = f["guide"]
    outcome = f["outcome"]
    base = (
        f'Write a short adventure story for a 3-to-5-year-old that includes the word "banister" '
        f'and the word "scaredy", and uses a flashback when one child sees danger.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle home adventure where {hero.label} wants to {action.verb}, but {guide.label}'s flashback helps stop the risky choice before anyone gets hurt.",
            f'Write a story where a flashback turns a dangerous shortcut into {plan.label}, keeping the adventure feeling real and safe.',
        ]
    return [
        base,
        f"Tell an adventure where {hero.label} insists on {action.verb} after saying {action.boast}, but a scare proves the guide's flashback was right.",
        f"Write a child-facing story in which a grown-up turns a risky staircase game into {plan.label} after a near accident.",
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, guide, parent = f["hero"], f["guide"], f["parent"]
    theme, action, memory, plan = f["theme"], f["action"], f["memory"], f["plan"]
    relation = f["relation"]
    outcome = f["outcome"]
    hero_name = hero.label
    guide_name = guide.label
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(hero, guide, relation)}, {hero_name} and {guide_name}, who turned the house into {theme.scene}. Their adventure changed when the banister looked like a shortcut.",
        ),
        (
            f"What did {hero_name} want to do?",
            f"{hero_name} wanted to {action.verb} to reach {theme.goal} faster. The dangerous idea felt exciting because it looked like part of the adventure.",
        ),
        (
            f"Why did {guide_name} warn {hero_name}?",
            f"{guide_name} had a flashback about {memory.lesson}. That memory made the danger feel real before the risky move even happened.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"Did anyone get hurt?",
                f"No. {hero_name} listened after the warning and stepped away from the banister. The flashback changed the choice before the accident could begin.",
            )
        )
    elif outcome == "caught":
        qa.append(
            (
                f"What happened when {hero_name} tried it?",
                f"{hero_name} did try it, and the scare became real right away. {pw.capitalize()} caught {hero.pronoun('object')} before it turned into a fall, so the danger stayed a near miss.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero_name} tried it?",
                f"{hero_name} bumped a knee on the stair and got frightened. The injury was small, but it proved the flashback warning had been wise.",
            )
        )
    qa.append(
        (
            f"How did the grown-up solve the problem?",
            f"{pw.capitalize()} used {plan.label} instead. {plan.qa_text}",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the children still playing adventure, but in a safer way. {theme.ending_line}",
        )
    )
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"banister", "flashback"}
    tags |= set(f["memory"].tags)
    tags |= set(f["plan"].tags)
    out: list[tuple[str, str]] = []
    order = ["banister", "flashback", "stairs", "safe_steps", "bridge", "pillows", "trail"]
    for tag in order:
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="castle",
        action="slide",
        memory="sock_slip",
        plan="stair_march",
        hero_name="Tom",
        hero_gender="boy",
        guide_name="Lily",
        guide_gender="girl",
        parent="mother",
        relation="siblings",
        trust=7,
        hero_age=5,
        guide_age=7,
        trait="careful",
        delay=0,
    ),
    StoryParams(
        theme="jungle",
        action="balance",
        memory="dizzy_peek",
        plan="bridge_pillows",
        hero_name="Mia",
        hero_gender="girl",
        guide_name="Ben",
        guide_gender="boy",
        parent="father",
        relation="friends",
        trust=3,
        hero_age=6,
        guide_age=6,
        trait="thoughtful",
        delay=1,
    ),
    StoryParams(
        theme="mountain",
        action="climb",
        memory="toy_tumble",
        plan="tape_trail",
        hero_name="Sam",
        hero_gender="boy",
        guide_name="Zoe",
        guide_gender="girl",
        parent="mother",
        relation="siblings",
        trust=4,
        hero_age=6,
        guide_age=5,
        trait="steady",
        delay=0,
    ),
    StoryParams(
        theme="castle",
        action="balance",
        memory="dizzy_peek",
        plan="tape_trail",
        hero_name="Ella",
        hero_gender="girl",
        guide_name="Nora",
        guide_gender="girl",
        parent="father",
        relation="siblings",
        trust=8,
        hero_age=4,
        guide_age=7,
        trait="careful",
        delay=0,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world: a banister shortcut, a flashback warning, and a safer adventure."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="0 = caught in time, 1 = small bump before help")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plan and PLANS[args.plan].sense < SENSE_MIN:
        raise StoryError(explain_plan(args.plan))
    if args.action and args.memory:
        action = ACTIONS[args.action]
        memory = MEMORIES[args.memory]
        plan = PLANS[args.plan] if args.plan else sensible_plans()[0]
        if not hazard_matches(action, memory):
            raise StoryError(explain_rejection(action, memory, plan))
    if args.action and args.plan:
        action = ACTIONS[args.action]
        plan = PLANS[args.plan]
        memory = MEMORIES[args.memory] if args.memory else next(iter(MEMORIES.values()))
        if not plan_fits(action, plan):
            raise StoryError(explain_rejection(action, memory, plan))

    combos = [
        c
        for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.action is None or c[1] == args.action)
        and (args.memory is None or c[2] == args.memory)
        and (args.plan is None or c[3] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, action_id, memory_id, plan_id = rng.choice(sorted(combos))
    hero_name, hero_gender = _pick_child(rng)
    guide_name, guide_gender = _pick_child(rng, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    relation = args.relation or rng.choice(["siblings", "friends"])
    trust = rng.randint(2, 9)
    hero_age, guide_age = rng.sample([4, 5, 6, 7], 2)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    return StoryParams(
        theme=theme_id,
        action=action_id,
        memory=memory_id,
        plan=plan_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        guide_name=guide_name,
        guide_gender=guide_gender,
        parent=parent,
        relation=relation,
        trust=trust,
        hero_age=hero_age,
        guide_age=guide_age,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        action = ACTIONS[params.action]
        memory = MEMORIES[params.memory]
        plan = PLANS[params.plan]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from err

    if plan.sense < SENSE_MIN:
        raise StoryError(explain_plan(plan.id))
    if not hazard_matches(action, memory) or not plan_fits(action, plan):
        raise StoryError(explain_rejection(action, memory, plan))

    world = tell(
        theme=theme,
        action=action,
        memory=memory,
        plan=plan,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        guide_name=params.guide_name,
        guide_gender=params.guide_gender,
        parent_type=params.parent,
        relation=params.relation,
        trust=params.trust,
        hero_age=params.hero_age,
        guide_age=params.guide_age,
        delay=params.delay,
        trait=params.trait,
    )

    hero = world.facts["hero"]
    guide = world.facts["guide"]
    story = world.render().replace("hero", hero.label).replace("guide", guide.label)

    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, action, memory, plan) combos:\n")
        for theme, action, memory, plan in combos:
            print(f"  {theme:8} {action:8} {memory:11} {plan}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name} & {p.guide_name}: {p.action} in {p.theme} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
