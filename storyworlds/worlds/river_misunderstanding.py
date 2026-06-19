#!/usr/bin/env python3
"""
storyworlds/worlds/river_misunderstanding.py
============================================

A standalone story world from the seed:

    Words: star, gentle, river
    Features: Teamwork, Misunderstanding, Mystery to Solve
    Style: Whodunit

The world models a child seeing a shimmer near a river and thinking a star has
fallen. A friend predicts the danger of trying alone, then the pair choose a safe
team method that matches the shimmer's location and risk. The mystery is solved
from state: once the shimmer is safely checked, the "fallen star" becomes a
reflection, pebble, lantern-glow, or firefly cluster.

Run it
------
    python storyworlds/worlds/river_misunderstanding.py
    python storyworlds/worlds/river_misunderstanding.py --all --trace --qa
    python storyworlds/worlds/river_misunderstanding.py --shimmer star_reflection --approach wade
    python storyworlds/worlds/river_misunderstanding.py --shimmer star_reflection --approach lean  # rejected
    python storyworlds/worlds/river_misunderstanding.py --verify
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
RISKS = {"deep_water", "slippery_bank", "snagged_reeds", "startled_insects"}
LOCATIONS = {"middle", "bank", "reeds"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    location: str = ""
    risk: str = ""
    real: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    phrase: str
    affords: set[str]


@dataclass
class Shimmer:
    id: str
    label: str
    phrase: str
    location: str
    risk: str
    real: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Approach:
    id: str
    action: str
    reach: set[str]
    risks: set[str]
    warning: str


@dataclass
class Plan:
    id: str
    label: str
    solves: set[str]
    action: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    apply: Callable[["World"], list[str]]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.active_approach: Optional[Approach] = None
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
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.active_approach = self.active_approach
        return clone


def _r_solo_attempt_creates_risk(world: World) -> list[str]:
    approach = world.active_approach
    if approach is None:
        return []
    hero = world.get("Hero")
    friend = world.get("Friend")
    shimmer = world.get("Shimmer")
    if hero.meters["trying_alone"] < THRESHOLD:
        return []
    if shimmer.location not in approach.reach or shimmer.risk not in approach.risks:
        return []
    sig = ("risk", approach.id, shimmer.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters[shimmer.risk] += 1
    friend.memes["worried"] += 1
    return [approach.warning.format(hero=hero.label, shimmer=shimmer.label)]


def _r_teamwork_identifies_shimmer(world: World) -> list[str]:
    hero = world.get("Hero")
    friend = world.get("Friend")
    shimmer = world.get("Shimmer")
    if hero.memes["teamwork"] < THRESHOLD or friend.memes["teamwork"] < THRESHOLD:
        return []
    sig = ("identify", shimmer.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    shimmer.meters["identified"] += 1
    hero.memes["misunderstanding"] = 0.0
    friend.memes["relief"] += 1
    return [f"The mystery opened gently: the shimmer was {shimmer.real}."]


CAUSAL_RULES = [
    Rule("solo_attempt_creates_risk", _r_solo_attempt_creates_risk),
    Rule("teamwork_identifies_shimmer", _r_teamwork_identifies_shimmer),
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
        for sent in produced:
            world.say(sent)
    return produced


def approach_fits(shimmer: Shimmer, approach: Approach) -> bool:
    return shimmer.location in approach.reach and shimmer.risk in approach.risks


def select_plan(shimmer: Shimmer) -> Optional[Plan]:
    for plan in PLANS:
        if shimmer.risk in plan.solves:
            return plan
    return None


def risk_phrase(risk: str) -> str:
    return {
        "deep_water": "deep water",
        "slippery_bank": "slipping on the bank",
        "snagged_reeds": "getting snagged in the reeds",
        "startled_insects": "scaring the insects",
    }.get(risk, risk.replace("_", " "))


def valid_story(setting: Setting, shimmer: Shimmer, approach: Approach) -> bool:
    return (
        shimmer.id in setting.affords
        and approach_fits(shimmer, approach)
        and select_plan(shimmer) is not None
    )


def try_alone(world: World, hero: Entity, approach: Approach, narrate: bool = True) -> None:
    hero.meters["trying_alone"] += 1
    world.active_approach = approach
    propagate(world, narrate=narrate)


def predict_risk(world: World, hero: Entity, approach: Approach) -> dict:
    sim = world.copy()
    try_alone(sim, sim.get(hero.id), approach, narrate=False)
    shimmer = sim.get("Shimmer")
    return {
        "risky": sim.get(hero.id).meters[shimmer.risk] >= THRESHOLD,
        "risk": shimmer.risk,
    }


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"Once upon a time, {hero.label} and {friend.label} walked beside "
        f"{world.setting.phrase}, looking for a gentle mystery to solve."
    )


def notice(world: World, hero: Entity, shimmer: Shimmer) -> None:
    hero.memes["misunderstanding"] += 1
    world.say(
        f"Near the river, {hero.label} saw {shimmer.phrase}. "
        f'"A star fell down!" {hero.pronoun()} whispered.'
    )


def warn(world: World, hero: Entity, friend: Entity, approach: Approach) -> bool:
    prediction = predict_risk(world, hero, approach)
    if not prediction["risky"]:
        return False
    world.facts["predicted_risk"] = prediction["risk"]
    world.say(
        f'"Wait," {friend.label} said. "If you {approach.action}, '
        f'{risk_phrase(prediction["risk"])} could make things worse."'
    )
    return True


def nearly_try(world: World, hero: Entity, approach: Approach) -> None:
    world.say(f"{hero.label} still wanted to {approach.action}.")
    try_alone(world, hero, approach, narrate=True)


def choose_teamwork(world: World, hero: Entity, friend: Entity, plan: Plan) -> None:
    hero.memes["teamwork"] += 1
    friend.memes["teamwork"] += 1
    world.say(f"{friend.label} had an idea. Together, they {plan.action}.")
    world.say(plan.result.format(hero=hero.label, friend=friend.label))
    propagate(world, narrate=True)


def moral(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.label} learned that a mystery is easier to solve when friends check it together."
    )


def tell(setting: Setting, shimmer_cfg: Shimmer, approach: Approach,
         hero_name: str, gender: str, friend_name: str) -> World:
    if not valid_story(setting, shimmer_cfg, approach):
        raise StoryError(explain_rejection(setting, shimmer_cfg, approach))
    world = World(setting)
    hero = world.add(Entity("Hero", kind="character", type=gender, label=hero_name))
    friend_gender = "girl" if gender == "boy" else "boy"
    friend = world.add(Entity("Friend", kind="character", type=friend_gender, label=friend_name))
    shimmer = world.add(Entity("Shimmer", type=shimmer_cfg.id, label=shimmer_cfg.label,
                               phrase=shimmer_cfg.phrase, location=shimmer_cfg.location,
                               risk=shimmer_cfg.risk, real=shimmer_cfg.real))
    plan = select_plan(shimmer_cfg)
    if plan is None:
        raise StoryError(explain_rejection(setting, shimmer_cfg, approach))

    introduce(world, hero, friend)
    world.para()
    notice(world, hero, shimmer_cfg)
    warn(world, hero, friend, approach)
    nearly_try(world, hero, approach)
    world.para()
    choose_teamwork(world, hero, friend, plan)
    moral(world, hero)
    world.facts.update(hero=hero, friend=friend, shimmer=shimmer,
                       shimmer_cfg=shimmer_cfg, approach=approach,
                       plan=plan, setting=setting)
    return world


SETTINGS = {
    "riverbank": Setting("the quiet riverbank", {"star_reflection", "silver_pebble", "lantern_glow"}),
    "bridge": Setting("the old footbridge", {"star_reflection", "lantern_glow"}),
    "meadow_stream": Setting("the meadow stream", {"silver_pebble", "fireflies"}),
    "reed_path": Setting("the reed-lined path", {"lantern_glow", "fireflies"}),
}

SHIMMERS = {
    "star_reflection": Shimmer(
        "star_reflection", "the star", "a bright star-shape trembling in the water",
        "middle", "deep_water", "the evening star reflected in the river",
        {"star", "river", "reflection"},
    ),
    "silver_pebble": Shimmer(
        "silver_pebble", "the silver spot", "a silver spot shining near the bank",
        "bank", "slippery_bank", "a smooth pebble under clear water",
        {"river", "pebble"},
    ),
    "lantern_glow": Shimmer(
        "lantern_glow", "the lantern glow", "a warm glow tangled in the reeds",
        "reeds", "snagged_reeds", "a neighbor's lantern shining through reeds",
        {"lantern", "river"},
    ),
    "fireflies": Shimmer(
        "fireflies", "the little stars", "tiny stars dancing above the reeds",
        "reeds", "startled_insects", "a cluster of fireflies rising together",
        {"star", "firefly"},
    ),
}

APPROACHES = {
    "wade": Approach(
        "wade", "wade into the river", {"middle"}, {"deep_water"},
        "{hero} stepped close to the current, and the deep water tugged at the bank.",
    ),
    "lean": Approach(
        "lean", "lean over the slick bank", {"bank"}, {"slippery_bank"},
        "{hero} leaned too far, and the slippery bank shifted underfoot.",
    ),
    "poke": Approach(
        "poke", "poke into the reeds", {"reeds"}, {"snagged_reeds"},
        "{hero} poked at the reeds, and the stems snagged around the stick.",
    ),
    "chase": Approach(
        "chase", "chase the dancing lights", {"reeds"}, {"startled_insects"},
        "{hero} rushed forward, and the tiny lights scattered in every direction.",
    ),
}

PLANS = [
    Plan("rope", "a rope line", {"deep_water"},
         "held a rope line from the bridge and watched from the bank",
         "{hero} stayed dry while {friend} pointed to the real star above them.",
         {"teamwork", "river"}),
    Plan("stick", "a steady walking stick", {"slippery_bank"},
         "used a steady walking stick and stepped slowly",
         "{hero} touched the silver spot safely while {friend} held the stick steady.",
         {"teamwork", "river"}),
    Plan("net", "a small net", {"snagged_reeds"},
         "used a small net to lift the reeds apart",
         "{friend} held the reeds open while {hero} saw the lantern shining beyond them.",
         {"teamwork", "lantern"}),
    Plan("quiet", "quiet watching", {"startled_insects"},
         "sat still and watched without chasing",
         "{hero} and {friend} watched the little lights rise like a gentle answer.",
         {"teamwork", "firefly"}),
]

GIRL_NAMES = ["Lina", "Maya", "Nora", "Zoe", "Ava", "Rose"]
BOY_NAMES = ["Ben", "Eli", "Theo", "Max", "Sam", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for shimmer_id in setting.affords:
            shimmer = SHIMMERS[shimmer_id]
            for approach_id, approach in APPROACHES.items():
                if valid_story(setting, shimmer, approach):
                    combos.append((place, shimmer_id, approach_id))
    return sorted(combos)


@dataclass
class StoryParams:
    place: str
    shimmer: str
    approach: str
    hero: str
    gender: str
    friend: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "star": [("Why do stars look like they sparkle?",
              "Stars can seem to sparkle because their light passes through moving air.")],
    "river": [("Why should children be careful near rivers?",
               "River edges can be slippery, and water can be deeper or faster than it looks.")],
    "reflection": [("What is a reflection?",
                    "A reflection is light bouncing off a surface, like a star shining on water.")],
    "lantern": [("What does a lantern do?",
                 "A lantern holds a light so people can see in dim places.")],
    "firefly": [("What is a firefly?",
                 "A firefly is an insect that can glow softly in the dark.")],
    "teamwork": [("Why does teamwork help solve mysteries?",
                  "Teamwork lets friends slow down, share ideas, and notice what one person missed.")],
}
KNOWLEDGE_ORDER = ["star", "river", "reflection", "lantern", "firefly", "teamwork"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, shimmer = f["hero"], f["shimmer_cfg"]
    return [
        'Write a gentle river mystery for young children using the words "star", "gentle", and "river".',
        f"Tell a teamwork story where {hero.label} misunderstands {shimmer.phrase} and solves the mystery with a friend.",
        "Write a whodunit-style story where the answer is a harmless reflection or natural light.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, shimmer, approach, plan = (
        f["hero"], f["friend"], f["shimmer_cfg"], f["approach"], f["plan"]
    )
    risk = risk_phrase(f.get("predicted_risk", shimmer.risk))
    return [
        ("Who is the story about?",
         f"It is about {hero.label} and {friend.label}, who found a mystery near {world.setting.phrase}."),
        (f"What did {hero.label} think they saw?",
         f"{hero.label} thought {shimmer.phrase} was a fallen star. The shimmer "
         "looked magical at first because it moved and shone near the river."),
        ("Why was trying alone risky?",
         f"Trying to {approach.action} was risky because it could lead to {risk}. "
         f"{friend.label} warned about that before they acted."),
        ("How did teamwork solve the mystery?",
         f"They chose {plan.label}. That let them check the shimmer safely and "
         f"discover it was {shimmer.real}, without making the river problem worse."),
        (f"What did {hero.label} learn?",
         f"{hero.label} learned that a mystery is easier to solve when friends "
         "check it together. Slowing down helped them find the harmless truth."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["shimmer_cfg"].tags) | set(f["plan"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.location:
            bits.append(f"location={ent.location}")
        if ent.risk:
            bits.append(f"risk={ent.risk}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:16}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("riverbank", "star_reflection", "wade", "Lina", "girl", "Ben"),
    StoryParams("riverbank", "silver_pebble", "lean", "Theo", "boy", "Maya"),
    StoryParams("bridge", "lantern_glow", "poke", "Nora", "girl", "Sam"),
    StoryParams("reed_path", "fireflies", "chase", "Finn", "boy", "Ava"),
]


def explain_rejection(setting: Setting, shimmer: Shimmer, approach: Approach) -> str:
    if shimmer.id not in setting.affords:
        return (f"(No story: {setting.phrase} does not contain {shimmer.phrase}, "
                "so the mystery cannot be staged there.)")
    if not approach_fits(shimmer, approach):
        return (f"(No story: trying to {approach.action} does not match a shimmer "
                f"in the {shimmer.location} with risk {shimmer.risk}.)")
    return f"(No story: no team plan protects against {shimmer.risk}.)"


ASP_RULES = r"""
fits(S, A) :- location(S, L), reaches(A, L), risk(S, R), approach_risk(A, R).
has_plan(S) :- risk(S, R), solves(_, R).
valid(P, S, A) :- affords(P, S), fits(S, A), has_plan(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for risk in sorted(RISKS):
        lines.append(asp.fact("risk_kind", risk))
    for loc in sorted(LOCATIONS):
        lines.append(asp.fact("location_kind", loc))
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for shimmer in sorted(setting.affords):
            lines.append(asp.fact("affords", place, shimmer))
    for sid, shimmer in SHIMMERS.items():
        lines.append(asp.fact("shimmer", sid))
        lines.append(asp.fact("location", sid, shimmer.location))
        lines.append(asp.fact("risk", sid, shimmer.risk))
    for aid, approach in APPROACHES.items():
        lines.append(asp.fact("approach", aid))
        for loc in sorted(approach.reach):
            lines.append(asp.fact("reaches", aid, loc))
        for risk in sorted(approach.risks):
            lines.append(asp.fact("approach_risk", aid, risk))
    for plan in PLANS:
        lines.append(asp.fact("plan", plan.id))
        for risk in sorted(plan.solves):
            lines.append(asp.fact("solves", plan.id, risk))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: star, gentle, river. "
                    "Unspecified choices are picked at random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--shimmer", choices=SHIMMERS)
    ap.add_argument("--approach", choices=APPROACHES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.shimmer and args.shimmer not in SETTINGS[args.place].affords:
        raise StoryError(explain_rejection(SETTINGS[args.place], SHIMMERS[args.shimmer],
                                           APPROACHES[args.approach or "wade"]))
    if args.shimmer and args.approach and not approach_fits(SHIMMERS[args.shimmer],
                                                            APPROACHES[args.approach]):
        setting = SETTINGS[args.place] if args.place else next(
            s for s in SETTINGS.values() if args.shimmer in s.affords
        )
        raise StoryError(explain_rejection(setting, SHIMMERS[args.shimmer],
                                           APPROACHES[args.approach]))
    if args.place and args.shimmer and args.approach:
        combo = (args.place, args.shimmer, args.approach)
        if combo not in valid_combos():
            raise StoryError(explain_rejection(SETTINGS[args.place], SHIMMERS[args.shimmer],
                                               APPROACHES[args.approach]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.shimmer is None or c[1] == args.shimmer)
              and (args.approach is None or c[2] == args.approach)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, shimmer, approach = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    names = GIRL_NAMES if gender == "girl" else BOY_NAMES
    friend_names = BOY_NAMES if gender == "girl" else GIRL_NAMES
    hero = args.hero or rng.choice(names)
    friend = args.friend or rng.choice([n for n in friend_names if n != hero])
    return StoryParams(place, shimmer, approach, hero, gender, friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], SHIMMERS[params.shimmer],
                 APPROACHES[params.approach], params.hero, params.gender,
                 params.friend)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(f"{len(combos)} compatible (place, shimmer, approach) combos:\n")
        for place, shimmer, approach in combos:
            print(f"  {place:14} {shimmer:16} {approach}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.shimmer} via {p.approach} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
