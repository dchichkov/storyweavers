#!/usr/bin/env python3
"""A slice-of-life storyworld about transforming a small dam.

Seed:
    Words: dam
    Features: Transformation, Lesson Learned
    Style: Slice of Life

The child wants to build a tiny dam. A mentor predicts the downstream
consequence on a copied world, then the child transforms the dam into a
controlled opening so the water can still move safely.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass(frozen=True)
class Place:
    id: str
    label: str
    water: str
    affords: set[str]
    opening: str
    tags: set[str]


@dataclass(frozen=True)
class DamPlan:
    id: str
    label: str
    build_phrase: str
    gerund: str
    risk: str
    zones: set[str]
    warning: str
    belief: str
    tags: set[str]


@dataclass(frozen=True)
class Downstream:
    id: str
    label: str
    full_label: str
    zone: str
    vulnerable: set[str]
    trouble: str
    safe_result: str
    tags: set[str]


@dataclass(frozen=True)
class Transformation:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    advice: str
    action: str
    result: str
    tags: set[str]


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    gender: Optional[str] = None
    meters: defaultdict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: defaultdict[str, float] = field(default_factory=lambda: defaultdict(float))
    zone: Optional[str] = None
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    used_on: Optional[str] = None
    protective: bool = False

    def pronoun(self, case: str) -> str:
        table = {
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
            "child": {"subject": "they", "object": "them", "possessive": "their"},
        }
        return table.get(self.gender or "child", table["child"])[case]


class World:
    def __init__(self, params: "StoryParams"):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.fired_names: list[str] = []
        self.facts: dict[str, object] = {}
        self.active_dam: Optional[str] = None
        self.active_target: Optional[str] = None

    def copy(self) -> "World":
        return copy.deepcopy(self)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, sentence: str) -> None:
        sentence = sentence.strip()
        if sentence:
            self.paragraphs[-1].append(sentence)

    def break_para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def protections_for(self, target: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.protective and e.used_on == target.id]

    def protected(self, target: Entity, risk: str) -> bool:
        return any(target.zone in t.covers and risk in t.guards for t in self.protections_for(target))

    def trace(self) -> str:
        lines = [
            f"place: {self.params.place}",
            f"fired rules: {', '.join(self.fired_names) if self.fired_names else 'none'}",
        ]
        for ent in self.entities.values():
            bits = [f"  {ent.id} | {ent.kind} | {ent.label}"]
            if ent.zone:
                bits.append(f"zone={ent.zone}")
            if ent.guards:
                bits.append(f"guards={sorted(ent.guards)}")
            if ent.covers:
                bits.append(f"covers={sorted(ent.covers)}")
            if ent.used_on:
                bits.append(f"used_on={ent.used_on}")
            lines.append(" | ".join(bits))
            if ent.meters:
                lines.append(f"    meters={dict(ent.meters)}")
            if ent.memes:
                lines.append(f"    memes={dict(ent.memes)}")
        return "\n".join(lines)


@dataclass(frozen=True)
class Rule:
    name: str
    apply: Callable[[World, bool], bool]


def _mark(world: World, name: str, *parts: object) -> bool:
    sig = (name, *parts)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    world.fired_names.append(name)
    return True


def _r_downstream_threat(world: World, narrate: bool) -> bool:
    if not world.active_dam or not world.active_target:
        return False
    dam = DAMS[world.active_dam]
    water = world.get("water")
    target = world.get(world.active_target)
    if water.meters[dam.risk] < THRESHOLD:
        return False
    if target.zone not in dam.zones or dam.risk not in target.guards:
        return False
    if world.protected(target, dam.risk):
        return False
    if not _mark(world, "downstream_threat", dam.id, target.id, dam.risk):
        return False
    target.meters["threatened"] += 1
    target.meters[dam.risk] += 1
    if narrate:
        world.say(f"The water pressed against the dam and began to threaten the {target.label}.")
    return True


def _r_mentor_worry(world: World, narrate: bool) -> bool:
    mentor_id = world.facts.get("mentor")
    target_id = world.active_target
    if not isinstance(mentor_id, str) or not isinstance(target_id, str):
        return False
    mentor = world.get(mentor_id)
    target = world.get(target_id)
    if target.meters["threatened"] < THRESHOLD:
        return False
    if not _mark(world, "mentor_worry", mentor.id, target.id):
        return False
    mentor.memes["worry"] += 1
    if narrate:
        world.say(f"{mentor.label} could see that the {target.label} needed a safer flow.")
    return True


def _r_small_conflict(world: World, narrate: bool) -> bool:
    hero_id = world.facts.get("hero")
    mentor_id = world.facts.get("mentor")
    if not isinstance(hero_id, str) or not isinstance(mentor_id, str):
        return False
    hero = world.get(hero_id)
    mentor = world.get(mentor_id)
    if hero.memes["pride"] < THRESHOLD or hero.meters["paused"] < THRESHOLD:
        return False
    if not _mark(world, "small_conflict", hero.id, mentor.id):
        return False
    hero.memes["frustration"] += 1
    mentor.memes["patience"] += 1
    if narrate:
        world.say(f"{hero.label} paused with muddy hands, still wishing the dam could stay big.")
    return True


CAUSAL_RULES = [
    Rule("downstream_threat", _r_downstream_threat),
    Rule("mentor_worry", _r_mentor_worry),
    Rule("small_conflict", _r_small_conflict),
]


def propagate(world: World, *, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world, narrate):
                changed = True


PLACES = {
    "backyard_runnel": Place(
        "backyard_runnel",
        "the backyard runnel",
        "a thin stream beside the tomato pots",
        {"mud_wall", "stone_stack"},
        "The water made a quiet line around every pebble.",
        {"garden", "water", "dam"},
    ),
    "park_gutter": Place(
        "park_gutter",
        "the park gutter",
        "a rain trickle beside the walking path",
        {"stone_stack", "leaf_pile"},
        "Every leaf that touched the trickle turned and floated away.",
        {"park", "water", "flow"},
    ),
    "school_garden": Place(
        "school_garden",
        "the school garden",
        "a little hose stream near the class planter",
        {"mud_wall", "leaf_pile"},
        "The teacher had said the water was for everyone growing there.",
        {"school", "garden", "lesson"},
    ),
}


DAMS = {
    "mud_wall": DamPlan(
        "mud_wall",
        "mud dam",
        "pack a mud dam across the stream",
        "packing a mud dam across the stream",
        "flood",
        {"garden", "path"},
        "push water over the low side",
        "a taller mud dam would make the best tiny pond",
        {"mud", "dam", "flood"},
    ),
    "stone_stack": DamPlan(
        "stone_stack",
        "stone dam",
        "stack flat stones into a dam",
        "stacking flat stones into a dam",
        "overflow",
        {"path", "bank"},
        "make the backed-up water spill sideways",
        "a stone dam would hold the water perfectly still",
        {"stone", "dam", "overflow"},
    ),
    "leaf_pile": DamPlan(
        "leaf_pile",
        "leaf dam",
        "sweep leaves into a soft dam",
        "sweeping leaves into a soft dam",
        "spread",
        {"path", "sand"},
        "spread brown water where it does not belong",
        "a leaf dam would be easy to build and easy to fix",
        {"leaf", "dam", "spread"},
    ),
}


DOWNSTREAM = {
    "bean_seedlings": Downstream(
        "bean_seedlings",
        "bean seedlings",
        "two bean seedlings",
        "garden",
        {"flood"},
        "wash soil away from the bean seedlings",
        "The bean seedlings stayed tucked in their soil.",
        {"garden", "seedlings", "water"},
    ),
    "chalk_path": Downstream(
        "chalk_path",
        "chalk path",
        "blue chalk path",
        "path",
        {"flood", "overflow", "spread"},
        "smear the chalk path into gray streaks",
        "The chalk path kept its blue line.",
        {"path", "chalk", "water"},
    ),
    "paper_boat_cove": Downstream(
        "paper_boat_cove",
        "paper boat cove",
        "paper boat cove",
        "bank",
        {"overflow"},
        "tip the paper boats onto the grass",
        "The paper boats bobbed in place instead of tipping over.",
        {"boat", "bank", "flow"},
    ),
    "sandbox_corner": Downstream(
        "sandbox_corner",
        "sandbox corner",
        "smooth sandbox corner",
        "sand",
        {"spread"},
        "turn the sandbox corner into sticky mud",
        "The sandbox corner stayed smooth enough for digging.",
        {"sand", "mud", "play"},
    ),
}


TRANSFORMS = {
    "spillway": Transformation(
        "spillway",
        "spillway",
        {"garden", "path"},
        {"flood"},
        "Press one thumb-width spillway into the dam",
        "pressed one thumb-width spillway into the dam",
        "Water slipped through the spillway in a silver thread.",
        {"dam", "water", "safety"},
    ),
    "pebble_gap": Transformation(
        "pebble_gap",
        "pebble gap",
        {"path", "bank"},
        {"overflow"},
        "Leave a pebble gap so the dam can breathe",
        "left a pebble gap so the dam could breathe",
        "Water moved through the pebble gap instead of climbing sideways.",
        {"stone", "water", "flow"},
    ),
    "leaf_scoop": Transformation(
        "leaf_scoop",
        "leaf scoop",
        {"path", "sand"},
        {"spread"},
        "Scoop a small channel through the leaves",
        "scooped a small channel through the leaves",
        "Water followed the channel and left the dry places alone.",
        {"leaf", "channel", "lesson"},
    ),
}

TRANSFORM_METHODS = {
    "spillway": "pressing one thumb-width spillway into the dam",
    "pebble_gap": "leaving a pebble gap so the dam could breathe",
    "leaf_scoop": "scooping a small channel through the leaves",
}


NAMES = {
    "girl": ["Maya", "Nora", "Ivy", "Lena"],
    "boy": ["Sam", "Owen", "Theo", "Ben"],
    "child": ["Riley", "Ari", "Quinn", "Rowan"],
}
MENTORS = ["mother", "father", "neighbor", "teacher"]
TRAITS = ["careful", "curious", "busy", "proud"]
GENDERS = ["girl", "boy", "child"]


def title(name: str) -> str:
    return name[:1].upper() + name[1:]


def at_risk(dam: DamPlan, target: Downstream) -> bool:
    return target.zone in dam.zones and bool(dam.risk in target.vulnerable)


def select_transformation(dam: DamPlan, target: Downstream) -> Optional[Transformation]:
    for transform in TRANSFORMS.values():
        if target.zone in transform.covers and dam.risk in transform.guards:
            return transform
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES.values():
        for dam in DAMS.values():
            if dam.id not in place.affords:
                continue
            for target in DOWNSTREAM.values():
                if not at_risk(dam, target):
                    continue
                if select_transformation(dam, target) is None:
                    continue
                for gender in GENDERS:
                    combos.append((place.id, dam.id, target.id, gender))
    return sorted(combos)


def explain_rejection(place_id: str, dam_id: str, target_id: str, gender: str) -> str:
    if place_id not in PLACES:
        return f"Unknown place {place_id!r}."
    if dam_id not in DAMS:
        return f"Unknown dam plan {dam_id!r}."
    if target_id not in DOWNSTREAM:
        return f"Unknown downstream target {target_id!r}."
    if gender not in GENDERS:
        return f"Unknown gender {gender!r}."
    place = PLACES[place_id]
    dam = DAMS[dam_id]
    target = DOWNSTREAM[target_id]
    if dam.id not in place.affords:
        return f"{place.label} does not plausibly afford a {dam.label}."
    if not at_risk(dam, target):
        return f"A {dam.label} would not honestly threaten the {target.label}."
    if select_transformation(dam, target) is None:
        return f"No transformation protects the {target.label} from {dam.risk}."
    return "The requested dam story is not in the valid set."


def introduce(world: World, place: Place, hero: Entity, mentor: Entity, target_cfg: Downstream) -> Entity:
    water = world.add(Entity("water", "water", place.water))
    target = world.add(
        Entity(
            target_cfg.id,
            "downstream",
            target_cfg.label,
            zone=target_cfg.zone,
            guards=set(target_cfg.vulnerable),
        )
    )
    world.say(
        f"One afternoon, {hero.label}, a {world.params.trait} child, played near {place.water}."
    )
    world.say(f"{mentor.label} was nearby, and the {target_cfg.full_label} waited downstream.")
    world.say(place.opening)
    world.facts["hero"] = hero.id
    world.facts["mentor"] = mentor.id
    world.facts["target"] = target.id
    water.memes["movement"] += 1
    return target


def plan_dam(world: World, hero: Entity, dam: DamPlan) -> None:
    world.break_para()
    world.say(f"{hero.label} believed that {dam.belief}.")
    world.say(f"{title(hero.pronoun('subject'))} wanted to {dam.build_phrase} and call it a real dam.")
    hero.memes["pride"] += 1
    hero.memes["curiosity"] += 1


def build_trial_dam(world: World, dam: DamPlan, target: Entity) -> None:
    world.active_dam = dam.id
    world.active_target = target.id
    world.add(Entity("trial_dam", "dam", dam.label))
    water = world.get("water")
    water.meters[dam.risk] += 1
    propagate(world, narrate=False)


def predict_flow(world: World, dam: DamPlan, target: Entity) -> dict[str, object]:
    sim = world.copy()
    build_trial_dam(sim, dam, sim.get(target.id))
    sim_target = sim.get(target.id)
    return {
        "risk": dam.risk,
        "threatened": sim_target.meters["threatened"] >= THRESHOLD,
        "trouble": DOWNSTREAM[target.id].trouble,
        "fired": list(sim.fired_names),
    }


def warn(world: World, hero: Entity, mentor: Entity, dam: DamPlan, target: Entity) -> None:
    prediction = predict_flow(world, dam, target)
    world.facts["prediction"] = prediction
    world.say(
        f'"Pause a second," said {mentor.label}. "If you finish {dam.gerund}, '
        f'the water may {prediction["trouble"]}. A dam still has to share the stream."'
    )
    mentor.memes["care"] += 1
    mentor.memes["caution"] += 1


def small_conflict(world: World, hero: Entity) -> None:
    world.say(f"{hero.label} looked at the little stream, then at the unfinished dam.")
    world.say(f'"But I wanted to change the water," {hero.pronoun("subject")} said.')
    hero.meters["paused"] += 1
    propagate(world, narrate=True)


def transform_dam(world: World, hero: Entity, mentor: Entity, dam: DamPlan, target: Entity) -> Transformation:
    target_cfg = DOWNSTREAM[target.id]
    transform = select_transformation(dam, target_cfg)
    if transform is None:
        raise StoryError("No safe transformation fits this dam story.")
    world.break_para()
    world.add(
        Entity(
            transform.id,
            "transformation",
            transform.label,
            covers=set(transform.covers),
            guards=set(transform.guards),
            used_on=target.id,
            protective=True,
        )
    )
    world.say(f"{mentor.label} knelt down and pointed to the moving water.")
    world.say(f'"{transform.advice}," {mentor.label} said.')
    world.say(f"So {hero.label} {transform.action}.")
    world.say(transform.result)
    hero.memes["flexibility"] += 1
    hero.memes["lesson"] += 1
    mentor.memes["relief"] += 1
    world.facts["transform"] = transform.id
    return transform


def finish(world: World, hero: Entity, mentor: Entity, target: Entity) -> None:
    target_cfg = DOWNSTREAM[target.id]
    world.say(target_cfg.safe_result)
    if hero.memes["lesson"] >= THRESHOLD:
        world.say(
            f"{hero.label} learned that changing a dam can be better than making it bigger."
        )
    world.say(
        f"The stream kept moving, {mentor.label} smiled, and the afternoon felt ordinary again."
    )
    hero.memes["satisfaction"] += 1
    mentor.memes["trust"] += 1


def tell(world: World) -> str:
    params = world.params
    place = PLACES[params.place]
    dam = DAMS[params.dam]
    target_cfg = DOWNSTREAM[params.downstream]
    hero = world.add(Entity("hero", "character", params.name, gender=params.gender))
    mentor = world.add(Entity("mentor", "character", title(params.mentor)))
    target = introduce(world, place, hero, mentor, target_cfg)
    plan_dam(world, hero, dam)
    warn(world, hero, mentor, dam, target)
    small_conflict(world, hero)
    transform_dam(world, hero, mentor, dam, target)
    finish(world, hero, mentor, target)
    return world.render()


@dataclass(frozen=True)
class StoryParams:
    place: str
    dam: str
    downstream: str
    name: str
    gender: str
    mentor: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("backyard_runnel", "mud_wall", "bean_seedlings", "Maya", "girl", "mother", "curious", 151),
    StoryParams("park_gutter", "stone_stack", "paper_boat_cove", "Owen", "boy", "father", "proud", 152),
    StoryParams("school_garden", "leaf_pile", "sandbox_corner", "Riley", "child", "teacher", "careful", 153),
    StoryParams("backyard_runnel", "stone_stack", "chalk_path", "Ivy", "girl", "neighbor", "busy", 154),
]


def generation_prompts(params: StoryParams) -> list[str]:
    dam = DAMS[params.dam]
    target = DOWNSTREAM[params.downstream]
    return [
        'Write a slice-of-life story that includes the word "dam".',
        f"Write a story where {params.name} transforms a {dam.label} to protect the {target.label}.",
        "Write a lesson-learned story about water needing a safe path.",
    ]


def story_qa(params: StoryParams, world: World) -> list[QAItem]:
    dam = DAMS[params.dam]
    target = DOWNSTREAM[params.downstream]
    transform = TRANSFORMS[str(world.facts["transform"])]
    method = TRANSFORM_METHODS[transform.id]
    mentor = title(params.mentor)
    prediction = world.facts["prediction"]
    trouble = str(prediction["trouble"])
    return [
        QAItem(
            f"Why did {mentor} ask {params.name} to pause?",
            f"{mentor} asked {params.name} to pause because {dam.gerund} could {trouble}. "
            f"The warning came from a predicted consequence, not from damage that already happened.",
        ),
        QAItem(
            f"How did {params.name} transform the dam?",
            f"{params.name} used the {transform.label} by {method}. "
            f"That changed the dam from a hard blockage into something the water could pass through safely.",
        ),
        QAItem(
            "What lesson did the story teach?",
            f"The lesson was that a dam should guide water, not trap it completely. "
            f"{params.name} learned that a smaller change could protect the {target.label}.",
        ),
    ]


KNOWLEDGE = {
    "dam": QAItem(
        "What is a dam?",
        "A dam is something that holds back or guides water. Even a tiny pretend dam changes where water goes.",
    ),
    "water": QAItem(
        "Why does water need a path?",
        "Water keeps moving toward lower places. If its path is blocked, it may spread sideways or overflow.",
    ),
    "flood": QAItem(
        "What does flooding mean?",
        "Flooding means water covers a place that is usually dry. Small floods can still move soil or make a path messy.",
    ),
    "overflow": QAItem(
        "What is overflow?",
        "Overflow happens when water rises past an edge. A small opening can lower the water before that happens.",
    ),
    "spread": QAItem(
        "Why can wet leaves spread water?",
        "Leaves can block drains and redirect trickles. Clearing a channel gives water an easier route.",
    ),
    "garden": QAItem(
        "Why can too much water hurt seedlings?",
        "Seedlings need water, but too much can wash soil away. Their roots stay safer when water moves gently.",
    ),
}


def world_qa(params: StoryParams) -> list[QAItem]:
    dam = DAMS[params.dam]
    target = DOWNSTREAM[params.downstream]
    tags = set().union(dam.tags, target.tags, {dam.risk, "dam", "water"})
    out = [item for key, item in KNOWLEDGE.items() if key in tags]
    return out[:4]


def generate(params: StoryParams) -> StorySample:
    combo = (params.place, params.dam, params.downstream, params.gender)
    if combo not in set(valid_combos()):
        raise StoryError(explain_rejection(params.place, params.dam, params.downstream, params.gender))
    world = World(params)
    story = tell(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(params),
        story_qa=story_qa(params, world),
        world_qa=world_qa(params),
        world=world,
    )


ASP_RULES = r"""
at_risk(D,T) :- dam_zone(D,Z), target_zone(T,Z), risk(D,R), vulnerable(T,R).
effective(D,T,X) :- at_risk(D,T), target_zone(T,Z), risk(D,R), covers(X,Z), guards(X,R).
valid(P,D,T,G) :- place(P), affords(P,D), target(T), gender(G), effective(D,T,_).
#show valid/4.
"""


def asp_facts() -> str:
    import asp

    facts: list[str] = []
    for place in PLACES.values():
        facts.append(asp.fact("place", place.id))
        for dam_id in place.affords:
            facts.append(asp.fact("affords", place.id, dam_id))
    for dam in DAMS.values():
        facts.append(asp.fact("dam", dam.id))
        facts.append(asp.fact("risk", dam.id, dam.risk))
        for zone in dam.zones:
            facts.append(asp.fact("dam_zone", dam.id, zone))
    for target in DOWNSTREAM.values():
        facts.append(asp.fact("target", target.id))
        facts.append(asp.fact("target_zone", target.id, target.zone))
        for risk in target.vulnerable:
            facts.append(asp.fact("vulnerable", target.id, risk))
    for transform in TRANSFORMS.values():
        facts.append(asp.fact("transform", transform.id))
        for zone in transform.covers:
            facts.append(asp.fact("covers", transform.id, zone))
        for risk in transform.guards:
            facts.append(asp.fact("guards", transform.id, risk))
    for gender in GENDERS:
        facts.append(asp.fact("gender", gender))
    return "\n".join(facts) + "\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp

    models = asp.solve(asp_facts() + ASP_RULES)
    combos: set[tuple[str, str, str, str]] = set()
    for model in models:
        for atom in asp.atoms(model, "valid"):
            combos.add(tuple(str(x) for x in atom))  # type: ignore[arg-type]
    return sorted(combos)


def asp_verify() -> int:
    py = set(valid_combos())
    lp = set(asp_valid_combos())
    if py != lp:
        print("Python/ASP mismatch")
        print("Only Python:", sorted(py - lp))
        print("Only ASP:", sorted(lp - py))
        return 1
    print(f"OK: Python and ASP agree on {len(py)} valid dam-transformation stories.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--dam", choices=sorted(DAMS))
    parser.add_argument("--downstream", choices=sorted(DOWNSTREAM))
    parser.add_argument("--gender", choices=GENDERS)
    parser.add_argument("--name")
    parser.add_argument("--mentor", choices=MENTORS)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--seed", type=int)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    return parser


def resolve_params(args, rng: random.Random) -> StoryParams:
    valid = valid_combos()
    choices = [
        combo
        for combo in valid
        if (args.place is None or combo[0] == args.place)
        and (args.dam is None or combo[1] == args.dam)
        and (args.downstream is None or combo[2] == args.downstream)
        and (args.gender is None or combo[3] == args.gender)
    ]
    if not choices:
        place = args.place or sorted(PLACES)[0]
        dam = args.dam or sorted(DAMS)[0]
        downstream = args.downstream or sorted(DOWNSTREAM)[0]
        gender = args.gender or GENDERS[0]
        raise StoryError(explain_rejection(place, dam, downstream, gender))
    place, dam, downstream, gender = rng.choice(choices)
    name = args.name or rng.choice(NAMES[gender])
    mentor = args.mentor or rng.choice(MENTORS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, dam, downstream, name, gender, mentor, trait, args.seed)


def format_qa(title_text: str, items: list[QAItem]) -> list[str]:
    lines = [title_text]
    for item in items:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return lines


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        print()
        print("PROMPTS")
        for prompt in sample.prompts:
            print(f"- {prompt}")
        print()
        print("\n".join(format_qa("STORY QA", sample.story_qa)))
        print()
        print("\n".join(format_qa("WORLD KNOWLEDGE QA", sample.world_qa)))
    if trace and sample.world is not None:
        print()
        print("TRACE")
        print(sample.world.trace())


def samples_from_args(args) -> list[StorySample]:
    if args.all:
        return [generate(params) for params in CURATED]
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    attempts = 0
    target = max(1, args.n)
    while len(samples) < target and attempts < target * 20:
        seed = base_seed + i
        i += 1
        attempts += 1
        local_args = copy.copy(args)
        local_args.seed = seed
        params = resolve_params(local_args, random.Random(seed))
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.show_asp:
        print(asp_facts() + ASP_RULES)
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print(" ".join(combo))
        return 0
    try:
        samples = samples_from_args(args)
    except StoryError as exc:
        parser.error(str(exc))
        return 2
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return 0
    for idx, sample in enumerate(samples, 1):
        header = ""
        if len(samples) > 1:
            header = f"=== dam_transformation_lesson #{idx} seed={sample.params.seed} ==="
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
