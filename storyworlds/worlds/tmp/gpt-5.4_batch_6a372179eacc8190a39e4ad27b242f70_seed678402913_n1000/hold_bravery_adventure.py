#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hold_bravery_adventure.py
====================================================

A standalone storyworld about a small adventure where a child meets one scary
obstacle, learns the brave safe way to go on, and reaches a bright goal by
holding the right thing.

The world model is intentionally small and concrete:

- a child explorer wants to reach a goal
- one obstacle makes the path feel risky
- one support object is offered as the sensible way through
- holding the support lowers danger and lets bravery become action

The reasonableness gate refuses mismatched supports. A lantern helps in a dark
tunnel, but not on a rope bridge. A handrail helps on a narrow bridge, but not
in a cave. The model prefers a few strong, plausible variants over broad weak
coverage.

Run it
------
    python storyworlds/worlds/gpt-5.4/hold_bravery_adventure.py
    python storyworlds/worlds/gpt-5.4/hold_bravery_adventure.py --place canyon --obstacle bridge
    python storyworlds/worlds/gpt-5.4/hold_bravery_adventure.py --obstacle bridge --support lantern
    python storyworlds/worlds/gpt-5.4/hold_bravery_adventure.py --all
    python storyworlds/worlds/gpt-5.4/hold_bravery_adventure.py --qa
    python storyworlds/worlds/gpt-5.4/hold_bravery_adventure.py --verify
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
BRAVERY_START = 2.0
BRAVERY_NEED = 4.0


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
        female = {"girl", "mother", "woman", "aunt", "sister"}
        male = {"boy", "father", "man", "uncle", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "uncle": "uncle", "aunt": "aunt"}.get(
            self.type, self.label or self.type
        )


@dataclass
class Place:
    id: str
    label: str
    opening: str
    path: str
    air: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    risk: str
    support_kind: str
    support_verb: str
    success: str
    danger_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    label: str
    phrase: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Support:
    id: str
    label: str
    phrase: str
    kind: str
    use_line: str
    calm_effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    obstacle: str
    goal: str
    support: str
    name: str
    gender: str
    guide_type: str
    trait: str
    seed: Optional[int] = None


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


def _r_hesitate(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["danger"] < THRESHOLD:
        return []
    if ("hesitate",) in world.fired:
        return []
    world.fired.add(("hesitate",))
    child.memes["fear"] += 1
    return []


def _r_hold_helps(world: World) -> list[str]:
    child = world.get("child")
    support = world.get("support")
    obstacle = world.get("obstacle")
    if child.meters["holding"] < THRESHOLD:
        return []
    if support.attrs.get("kind") != obstacle.attrs.get("support_kind"):
        return []
    if ("hold_helps",) in world.fired:
        return []
    world.fired.add(("hold_helps",))
    child.meters["danger"] = max(0.0, child.meters["danger"] - 1.0)
    child.memes["bravery"] += 2.0
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1.0)
    return []


def _r_cross_ready(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["danger"] > 0.0:
        return []
    if child.memes["bravery"] < BRAVERY_NEED:
        return []
    if ("cross_ready",) in world.fired:
        return []
    world.fired.add(("cross_ready",))
    child.meters["progress"] += 1
    child.memes["confidence"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="hesitate", tag="emotion", apply=_r_hesitate),
    Rule(name="hold_helps", tag="physical", apply=_r_hold_helps),
    Rule(name="cross_ready", tag="physical", apply=_r_cross_ready),
]


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
            world.say(line)
    return produced


PLACES = {
    "canyon": Place(
        id="canyon",
        label="the canyon trail",
        opening="a red canyon with echoes under the cliffs",
        path="a path that curled above a clear rushing stream",
        air="The wind carried the smell of warm stone.",
        tags={"canyon", "adventure"},
    ),
    "forest": Place(
        id="forest",
        label="the forest path",
        opening="a green forest with mossy roots and tall ferns",
        path="a path that slipped between old trees",
        air="The leaves whispered softly overhead.",
        tags={"forest", "adventure"},
    ),
    "hill": Place(
        id="hill",
        label="the hill trail",
        opening="a bright hill with long grass and little yellow flowers",
        path="a path that climbed toward the top",
        air="The sky felt wide and blue above them.",
        tags={"hill", "adventure"},
    ),
}

OBSTACLES = {
    "bridge": Obstacle(
        id="bridge",
        label="rope bridge",
        phrase="a rope bridge stretched over the stream",
        risk="The boards wobbled, and the water hurried below.",
        support_kind="rail",
        support_verb="hold the side rope",
        success="step by careful step across the bridge",
        danger_text="The bridge looked too shaky to hurry across.",
        tags={"bridge", "height"},
    ),
    "tunnel": Obstacle(
        id="tunnel",
        label="dark tunnel",
        phrase="a dark tunnel opened in the rock",
        risk="Inside, the light faded after only a few steps.",
        support_kind="light",
        support_verb="hold the lantern high",
        success="walk slowly through the tunnel",
        danger_text="The tunnel was too dark to enter blind.",
        tags={"tunnel", "dark"},
    ),
    "ledge": Obstacle(
        id="ledge",
        label="steep ledge",
        phrase="a steep ledge climbed along the hill",
        risk="Loose pebbles clicked down the slope.",
        support_kind="rope",
        support_verb="hold the guide rope",
        success="climb the ledge one steady step at a time",
        danger_text="The ledge was too steep to scramble up without help.",
        tags={"ledge", "climb"},
    ),
}

GOALS = {
    "flag": Goal(
        id="flag",
        label="a bright red flag",
        phrase="a bright red flag on a stone post",
        ending="At the top, the red flag snapped in the wind like a tiny victory.",
        tags={"flag", "treasure"},
    ),
    "pool": Goal(
        id="pool",
        label="a hidden blue pool",
        phrase="a hidden blue pool that shone between rocks",
        ending="Beyond the path, the blue pool glittered as if it had been waiting for them.",
        tags={"pool", "water"},
    ),
    "nest": Goal(
        id="nest",
        label="an eagle nest",
        phrase="an eagle nest tucked high in the safe cliff grass",
        ending="From there they could see the nest, quiet and grand against the sky.",
        tags={"nest", "bird"},
    ),
}

SUPPORTS = {
    "handrail": Support(
        id="handrail",
        label="side rope",
        phrase="the side rope of the bridge",
        kind="rail",
        use_line="Hold the side rope with both hands and feel each board before the next step.",
        calm_effect="The rope gave a steady answer to each careful tug.",
        tags={"rail", "bridge"},
    ),
    "lantern": Support(
        id="lantern",
        label="lantern",
        phrase="a little brass lantern",
        kind="light",
        use_line="Hold the lantern high so the tunnel can show you where the floor is safe.",
        calm_effect="The lantern pushed the shadows back into the corners.",
        tags={"light", "lantern"},
    ),
    "guide_rope": Support(
        id="guide_rope",
        label="guide rope",
        phrase="a thick guide rope tied beside the ledge",
        kind="rope",
        use_line="Hold the guide rope and lean your feet into the hill, one step at a time.",
        calm_effect="The rope stayed firm while the pebbles slid away below.",
        tags={"rope", "climb"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nora", "Ava", "Zoe", "Ivy", "Ella", "Tara"]
BOY_NAMES = ["Kai", "Leo", "Finn", "Owen", "Milo", "Eli", "Noah", "Jude"]
TRAITS = ["eager", "curious", "quick", "thoughtful", "bright", "spirited"]

GUIDES = ["mother", "father", "aunt", "uncle"]

KNOWLEDGE = {
    "bridge": [
        (
            "Why is it smart to hold a rail on a bridge?",
            "Holding a rail helps your body stay balanced when the bridge moves. A steady hand can keep a careful step from turning into a slip."
        )
    ],
    "lantern": [
        (
            "What does a lantern help you do?",
            "A lantern gives light so you can see where to put your feet in a dark place. Seeing clearly helps you move safely."
        )
    ],
    "rope": [
        (
            "Why can a rope make climbing safer?",
            "A rope gives your hands something firm to hold while your feet search for the next safe step. It helps you stay steady on a steep path."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery is doing the right safe thing even when you still feel a little scared. It does not mean rushing without thinking."
        )
    ],
    "careful": [
        (
            "Does being brave mean going fast?",
            "No. Brave people often slow down, pay attention, and use help when they need it. Careful bravery is stronger than rushing."
        )
    ],
    "adventure": [
        (
            "What makes something feel like an adventure?",
            "An adventure feels new and exciting, with a path, a goal, and a challenge to solve. It stays good when people use safe choices along the way."
        )
    ],
}
KNOWLEDGE_ORDER = ["adventure", "bravery", "careful", "bridge", "lantern", "rope"]


def compatible(obstacle: Obstacle, support: Support) -> bool:
    return obstacle.support_kind == support.kind


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for obstacle_id, obstacle in OBSTACLES.items():
            for goal_id in GOALS:
                for support_id, support in SUPPORTS.items():
                    if compatible(obstacle, support):
                        combos.append((place_id, obstacle_id, goal_id, support_id))
    return combos


def predict_success(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["holding"] += 1
    propagate(sim, narrate=False)
    return {
        "progress": sim.get("child").meters["progress"],
        "bravery": sim.get("child").memes["bravery"],
        "danger": sim.get("child").meters["danger"],
    }


def introduce(world: World, child: Entity, guide: Entity, place: Place) -> None:
    world.say(
        f"One bright morning, {child.id} and {child.pronoun('possessive')} {guide.label_word} set out for {place.opening}. "
        f"They followed {place.path}. {place.air}"
    )
    world.say(
        f"{child.id} felt as if the day was opening like a map, and every turn promised a new adventure."
    )


def set_goal(world: World, child: Entity, goal: Goal) -> None:
    child.memes["desire"] += 1
    world.say(
        f"Far ahead, {child.pronoun()} spotted {goal.phrase}. At once, {child.id} wanted to be the one who reached it."
    )


def face_obstacle(world: World, child: Entity, obstacle: Obstacle) -> None:
    child.meters["danger"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But between {child.id} and the goal, {obstacle.phrase}. {obstacle.risk}"
    )
    if child.memes["fear"] >= THRESHOLD:
        world.say(
            f"{child.id} stopped short. {obstacle.danger_text}"
        )


def encourage(world: World, guide: Entity, child: Entity, support: Support, obstacle: Obstacle) -> None:
    guide.memes["care"] += 1
    child.memes["hope"] += 1
    pred = predict_success(world)
    world.facts["predicted_danger_after_hold"] = pred["danger"]
    world.facts["predicted_bravery_after_hold"] = pred["bravery"]
    world.say(
        f'{guide.label_word.capitalize()} knelt beside {child.id}. "{support.use_line} You do not have to pretend you are not scared," {guide.pronoun()} said. '
        f'"Bravery means {obstacle.success} the safe way."'
    )


def hold_support(world: World, child: Entity, support: Support) -> None:
    child.meters["holding"] += 1
    world.facts["held_support"] = support.label
    propagate(world, narrate=False)
    world.say(
        f"{child.id} took a long breath and reached out to hold {support.phrase}. {support.calm_effect}"
    )


def cross(world: World, child: Entity, obstacle: Obstacle) -> None:
    if child.meters["progress"] < THRESHOLD:
        raise StoryError("The child never became ready to cross the obstacle.")
    world.say(
        f"Then {child.pronoun()} began to {obstacle.success}. Each small step made the next one feel possible."
    )


def reach_goal(world: World, child: Entity, guide: Entity, goal: Goal) -> None:
    child.memes["joy"] += 1
    child.memes["bravery"] += 1
    child.memes["confidence"] += 1
    world.say(
        f"A moment later, {child.id} reached the far side and laughed with surprise. {goal.ending}"
    )
    world.say(
        f'"I was scared at first," {child.id} said, "but when I could hold on, I could keep going." '
        f'{guide.label_word.capitalize()} smiled and gave {child.pronoun("object")} a proud squeeze on the shoulder.'
    )


def tell(
    place: Place,
    obstacle: Obstacle,
    goal: Goal,
    support: Support,
    *,
    name: str = "Kai",
    gender: str = "boy",
    guide_type: str = "uncle",
    trait: str = "curious",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            label=name,
            role="child",
            attrs={"trait": trait},
            tags={"child", "adventure"},
        )
    )
    guide = world.add(
        Entity(
            id="Guide",
            kind="character",
            type=guide_type,
            label="the guide",
            role="guide",
            tags={"guide"},
        )
    )
    world.add(
        Entity(
            id="obstacle",
            kind="thing",
            type="obstacle",
            label=obstacle.label,
            phrase=obstacle.phrase,
            role="obstacle",
            attrs={"support_kind": obstacle.support_kind},
            tags=set(obstacle.tags),
        )
    )
    world.add(
        Entity(
            id="support",
            kind="thing",
            type="support",
            label=support.label,
            phrase=support.phrase,
            role="support",
            attrs={"kind": support.kind},
            tags=set(support.tags),
        )
    )
    world.add(
        Entity(
            id="goal",
            kind="thing",
            type="goal",
            label=goal.label,
            phrase=goal.phrase,
            role="goal",
            tags=set(goal.tags),
        )
    )

    child.memes["bravery"] = BRAVERY_START
    child.memes["wonder"] = 1.0

    introduce(world, child, guide, place)
    set_goal(world, child, goal)

    world.para()
    face_obstacle(world, child, obstacle)
    encourage(world, guide, child, support, obstacle)

    world.para()
    hold_support(world, child, support)
    cross(world, child, obstacle)
    reach_goal(world, child, guide, goal)

    world.facts.update(
        child=child,
        guide=guide,
        place=place,
        obstacle_cfg=obstacle,
        support_cfg=support,
        goal_cfg=goal,
        success=child.meters["progress"] >= THRESHOLD,
        bravery_final=child.memes["bravery"],
        fear_final=child.memes["fear"],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    obstacle = f["obstacle_cfg"]
    goal = f["goal_cfg"]
    support = f["support_cfg"]
    place = f["place"]
    return [
        f'Write a short adventure story for a 3-to-5-year-old that includes the word "hold" and shows bravery in a safe way.',
        f"Tell a gentle adventure where a child named {child.id} wants to reach {goal.phrase}, but must face {obstacle.phrase} by learning to hold {support.phrase}.",
        f"Write a child-facing story set on {place.label} where fear turns into bravery because the hero slows down, listens, and holds the right support.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    guide = f["guide"]
    obstacle = f["obstacle_cfg"]
    support = f["support_cfg"]
    goal = f["goal_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child on a small adventure, and {child.pronoun('possessive')} {guide.label_word} who helps along the way."
        ),
        (
            f"What did {child.id} want to reach?",
            f"{child.id} wanted to reach {goal.phrase}. The bright goal is what pulled the adventure forward."
        ),
        (
            f"Why did {child.id} stop at first?",
            f"{child.id} stopped because {obstacle.phrase}, and it looked risky. The path did not feel safe until there was something trustworthy to hold."
        ),
        (
            f"What did {guide.label_word} tell {child.id} to do?",
            f'{guide.label_word.capitalize()} told {child.id} to {obstacle.support_verb}. {guide.pronoun().capitalize()} explained that bravery meant going the safe careful way, not pretending the scary part was easy.'
        ),
        (
            f"How did holding {support.label} help?",
            f"Holding {support.phrase} made the path feel steady enough to keep moving. Because {child.id} could hold on, fear dropped and bravery turned into careful action."
        ),
        (
            "How did the story end?",
            f"{child.id} crossed safely and reached {goal.label}. The ending shows the change clearly: the same child who had stopped in fear was now smiling on the far side."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"adventure", "bravery", "careful"}
    support = f["support_cfg"]
    obstacle = f["obstacle_cfg"]
    if support.kind == "rail" or obstacle.id == "bridge":
        tags.add("bridge")
    if support.kind == "light":
        tags.add("lantern")
    if support.kind == "rope":
        tags.add("rope")
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
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="canyon",
        obstacle="bridge",
        goal="flag",
        support="handrail",
        name="Kai",
        gender="boy",
        guide_type="uncle",
        trait="curious",
    ),
    StoryParams(
        place="forest",
        obstacle="tunnel",
        goal="pool",
        support="lantern",
        name="Mira",
        gender="girl",
        guide_type="aunt",
        trait="thoughtful",
    ),
    StoryParams(
        place="hill",
        obstacle="ledge",
        goal="nest",
        support="guide_rope",
        name="Leo",
        gender="boy",
        guide_type="father",
        trait="spirited",
    ),
]


def explain_rejection(obstacle: Obstacle, support: Support) -> str:
    return (
        f"(No story: {support.phrase} does not sensibly solve {obstacle.phrase}. "
        f"This obstacle needs something to {obstacle.support_verb}, so choose a support of kind "
        f"'{obstacle.support_kind}'.)"
    )


ASP_RULES = r"""
compatible(O, S) :- obstacle(O), support(S), needs_kind(O, K), support_kind(S, K).
valid(P, O, G, S) :- place(P), obstacle(O), goal(G), support(S), compatible(O, S).

danger_after_hold(0) :- chosen_obstacle(O), chosen_support(S), compatible(O, S).
danger_after_hold(1) :- chosen_obstacle(O), chosen_support(S), not compatible(O, S).

bravery_after_hold(4) :- chosen_obstacle(O), chosen_support(S), compatible(O, S), bravery_start(2).
bravery_after_hold(2) :- chosen_obstacle(O), chosen_support(S), not compatible(O, S), bravery_start(2).

success :- danger_after_hold(0), bravery_after_hold(B), bravery_need(N), B >= N.
outcome(success) :- success.
outcome(stuck) :- not success.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("needs_kind", obstacle_id, obstacle.support_kind))
    for goal_id in GOALS:
        lines.append(asp.fact("goal", goal_id))
    for support_id, support in SUPPORTS.items():
        lines.append(asp.fact("support", support_id))
        lines.append(asp.fact("support_kind", support_id, support.kind))
    lines.append(asp.fact("bravery_start", int(BRAVERY_START)))
    lines.append(asp.fact("bravery_need", int(BRAVERY_NEED)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_support", params.support),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    obstacle = OBSTACLES[params.obstacle]
    support = SUPPORTS[params.support]
    return "success" if compatible(obstacle, support) else "stuck"


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

    cases: list[StoryParams] = list(CURATED)
    for obstacle_id in OBSTACLES:
        for support_id in SUPPORTS:
            cases.append(
                StoryParams(
                    place="canyon",
                    obstacle=obstacle_id,
                    goal="flag",
                    support=support_id,
                    name="Kai",
                    gender="boy",
                    guide_type="uncle",
                    trait="curious",
                )
            )

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} scenario outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a brave little adventure where holding the right thing makes the path safe."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.support:
        obstacle = OBSTACLES[args.obstacle]
        support = SUPPORTS[args.support]
        if not compatible(obstacle, support):
            raise StoryError(explain_rejection(obstacle, support))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.goal is None or combo[2] == args.goal)
        and (args.support is None or combo[3] == args.support)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, obstacle_id, goal_id, support_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    guide_type = args.guide or rng.choice(GUIDES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        obstacle=obstacle_id,
        goal=goal_id,
        support=support_id,
        name=name,
        gender=gender,
        guide_type=guide_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        obstacle = OBSTACLES[params.obstacle]
        goal = GOALS[params.goal]
        support = SUPPORTS[params.support]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter choice: {err.args[0]})") from err

    if not compatible(obstacle, support):
        raise StoryError(explain_rejection(obstacle, support))

    world = tell(
        place=place,
        obstacle=obstacle,
        goal=goal,
        support=support,
        name=params.name,
        gender=params.gender,
        guide_type=params.guide_type,
        trait=params.trait,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, obstacle, goal, support) combos:\n")
        for place_id, obstacle_id, goal_id, support_id in combos:
            print(f"  {place_id:8} {obstacle_id:8} {goal_id:6} {support_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.obstacle} at {p.place} with {p.support}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
