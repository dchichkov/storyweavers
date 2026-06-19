#!/usr/bin/env python3
"""
storyworlds/worlds/crown_lamp_teamwork_tall_tale.py
===================================================

A standalone story world for a TinyStories-style prompt:

    Words: crown, twinkling lamp
    Features: Misunderstanding, Teamwork
    Style: Tall Tale

The tale exaggerates a small optical mix-up into a huge rumor: a shiny crown
under a twinkling lamp throws a strange light or shadow, the children make a
wild guess, and teamwork reveals the ordinary cause. The model refuses variants
where the misunderstanding has no physical reason or where the team's plan would
not actually test the effect.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    reflective: bool = False
    twinkling: bool = False
    effect: str = ""
    clears: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Fair:
    id: str
    place: str
    stage: str
    supports: set[str]
    opening: str


@dataclass
class Crown:
    id: str
    phrase: str
    material: str
    reflective: bool
    owner: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Lamp:
    id: str
    phrase: str
    twinkle: bool
    effect: str
    flicker_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Surface:
    id: str
    label: str
    location: str
    effect: str
    wild_claim: str
    ordinary_cause: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    label: str
    clears: set[str]
    job_a: str
    job_b: str
    proof_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, fair: Fair) -> None:
        self.fair = fair
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

    def copy(self) -> "World":
        clone = World(self.fair)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def role(world: World, name: str) -> Optional[Entity]:
    return next((e for e in world.entities.values() if e.role == name), None)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_cast_wonder(world: World) -> list[str]:
    crown = world.entities.get("crown")
    lamp = world.entities.get("lamp")
    surface = world.entities.get("surface")
    if not crown or not lamp or not surface:
        return []
    if not crown.reflective or not lamp.twinkling or lamp.effect != surface.effect:
        return []
    if lamp.meters["lit"] < THRESHOLD:
        return []
    sig = ("wonder", crown.id, lamp.id, surface.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    surface.meters["strange_sign"] += 1
    crown.meters["sparkle"] += 1
    return ["wonder"]


def _r_misunderstand(world: World) -> list[str]:
    surface = world.entities.get("surface")
    hero = role(world, "spotter")
    partner = role(world, "tester")
    if not surface or not hero or not partner:
        return []
    if surface.meters["strange_sign"] < THRESHOLD:
        return []
    sig = ("misunderstanding", surface.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["excitement"] += 1
    partner.memes["confusion"] += 1
    surface.memes["rumor"] += 1
    return ["misunderstanding"]


def _r_team_test(world: World) -> list[str]:
    plan = world.entities.get("plan")
    surface = world.entities.get("surface")
    hero = role(world, "spotter")
    partner = role(world, "tester")
    if not plan or not surface or not hero or not partner:
        return []
    if hero.memes["teamwork"] < THRESHOLD or partner.memes["teamwork"] < THRESHOLD:
        return []
    if surface.effect not in plan.clears:
        return []
    sig = ("clarity", plan.id, surface.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    surface.meters["explained"] += 1
    surface.memes["rumor"] = 0.0
    hero.memes["wisdom"] += 1
    partner.memes["wisdom"] += 1
    return ["clarity"]


CAUSAL_RULES = [
    Rule("cast_wonder", "physical", _r_cast_wonder),
    Rule("misunderstand", "social", _r_misunderstand),
    Rule("team_test", "social", _r_team_test),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) > before:
                changed = True


def illusion_possible(crown: Crown, lamp: Lamp, surface: Surface) -> bool:
    return crown.reflective and lamp.twinkle and lamp.effect == surface.effect


def plan_clears(plan: Plan, surface: Surface) -> bool:
    return surface.effect in plan.clears


def fair_hosts(fair: Fair, surface: Surface) -> bool:
    return surface.location in fair.supports


def valid_combo(fair: Fair, crown: Crown, lamp: Lamp, surface: Surface, plan: Plan) -> bool:
    return fair_hosts(fair, surface) and illusion_possible(crown, lamp, surface) and plan_clears(plan, surface)


def predict_truth(world: World) -> dict:
    sim = world.copy()
    sim.get("lamp").meters["lit"] += 1
    propagate(sim)
    spotter = role(sim, "spotter")
    tester = role(sim, "tester")
    if spotter is not None:
        spotter.memes["teamwork"] += 1
    if tester is not None:
        tester.memes["teamwork"] += 1
    propagate(sim)
    return {
        "misunderstood": sim.get("surface").memes["rumor"] >= THRESHOLD,
        "explained": sim.get("surface").meters["explained"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, partner: Entity, crown: Crown, lamp: Lamp) -> None:
    world.say(
        f"At {world.fair.place}, {world.fair.opening}. {hero.id} and {partner.id} "
        f"were in charge of guarding {crown.phrase}."
    )
    world.say(
        f"Above {world.fair.stage} hung {lamp.phrase}, which twinkled like "
        f"a jar full of tiny stars."
    )


def light_lamp(world: World, lamp: Entity, lamp_cfg: Lamp) -> None:
    lamp.meters["lit"] += 1
    propagate(world)
    world.say(lamp_cfg.flicker_line)


def tall_claim(world: World, hero: Entity, partner: Entity, surface: Surface) -> None:
    propagate(world)
    if surface and world.get("surface").memes["rumor"] >= THRESHOLD:
        world.say(
            f'{hero.id} gasped so loudly the spoons rattled. "{surface.wild_claim}!" '
            f"{hero.pronoun()} cried."
        )
        world.say(
            f"{partner.id} looked once, looked twice, and felt a question grow "
            f"as tall as the lodge chimney."
        )


def crowd_reacts(world: World, hero: Entity, partner: Entity) -> None:
    world.say(
        f"By the time {hero.id} whispered it to one person and {partner.id} tried "
        f"to slow the whisper down, the tale had grown bigger than a hay wagon."
    )


def team_plan(world: World, hero: Entity, partner: Entity, plan: Plan) -> None:
    hero.memes["teamwork"] += 1
    partner.memes["teamwork"] += 1
    pred = predict_truth(world)
    world.facts["predicted_truth"] = pred
    world.say(
        f'Then {partner.id} said, "Tall tales need tiny tests." '
        f"{hero.id} would {plan.job_a}, and {partner.id} would {plan.job_b}."
    )


def prove(world: World, plan: Plan, surface: Surface) -> None:
    propagate(world)
    if world.get("surface").meters["explained"] < THRESHOLD:
        return
    world.say(plan.proof_line)
    world.say(
        f"The enormous mystery shrank down to the truth: {surface.ordinary_cause}."
    )


def finish(world: World, hero: Entity, partner: Entity, crown: Crown) -> None:
    hero.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"Everyone laughed kindly, and the {crown.material} crown stayed right "
        f"where it belonged."
    )
    world.say(
        f"{hero.id} and {partner.id} bowed like royal detectives. From then on, "
        f"they checked together before believing a story as big as the sky."
    )


def tell(
    fair: Fair,
    crown: Crown,
    lamp: Lamp,
    surface: Surface,
    plan: Plan,
    hero_name: str,
    hero_gender: str,
    partner_name: str,
    partner_gender: str,
    trait: str,
) -> World:
    world = World(fair)
    hero = world.add(Entity(hero_name, "character", hero_gender, role="spotter", traits=[trait]))
    partner = world.add(Entity(partner_name, "character", partner_gender, role="tester"))
    crown_ent = world.add(Entity("crown", "thing", "crown", label="crown", reflective=crown.reflective))
    lamp_ent = world.add(Entity("lamp", "thing", "lamp", label="twinkling lamp", twinkling=lamp.twinkle, effect=lamp.effect))
    surface_ent = world.add(Entity("surface", "thing", surface.id, label=surface.label, effect=surface.effect))
    plan_ent = world.add(Entity("plan", "thing", plan.id, label=plan.label, clears=set(plan.clears)))
    world.facts.update(
        hero=hero, partner=partner, crown=crown, crown_ent=crown_ent,
        lamp=lamp, lamp_ent=lamp_ent, surface=surface, surface_ent=surface_ent,
        plan=plan, plan_ent=plan_ent, fair=fair,
    )

    introduce(world, hero, partner, crown, lamp)
    light_lamp(world, lamp_ent, lamp)

    world.para()
    tall_claim(world, hero, partner, surface)
    crowd_reacts(world, hero, partner)

    world.para()
    team_plan(world, hero, partner, plan)
    prove(world, plan, surface)
    finish(world, hero, partner, crown)
    world.facts["resolved"] = surface_ent.meters["explained"] >= THRESHOLD
    return world


FAIRS = {
    "harvest": Fair("harvest", "the Harvest Hall", "the prize table",
                    {"curtain", "window", "mirror"}, "the pies were stacked like hills"),
    "lodge": Fair("lodge", "the Snowcap Lodge party", "the fireplace shelf",
                  {"curtain", "wall", "window"}, "the cocoa pot puffed warm steam"),
    "school": Fair("school", "the school playroom fair", "the puppet stage",
                   {"curtain", "mirror", "wall"}, "paper flags fluttered from string"),
}

CROWNS = {
    "tin": Crown("tin", "a shiny tin crown", "tin", True, "the pretend king", {"crown", "metal"}),
    "gold": Crown("gold", "a golden cardboard crown", "gold-painted", True, "the play queen", {"crown", "shiny"}),
    "velvet": Crown("velvet", "a velvet crown with dull felt stars", "velvet", False, "the puppet prince", {"crown"}),
}

LAMPS = {
    "twinkling_lamp": Lamp("twinkling_lamp", "a twinkling lamp", True, "sparkle",
                           "The twinkling lamp blinked once, twice, and sent bright dots dancing.",
                           {"twinkling_lamp", "light"}),
    "swinging_lamp": Lamp("swinging_lamp", "a swinging twinkling lamp", True, "shadow",
                          "The swinging twinkling lamp made the crown's shadow stretch and bow.",
                          {"twinkling_lamp", "shadow"}),
    "plain_lamp": Lamp("plain_lamp", "a plain reading lamp", False, "sparkle",
                       "The plain lamp glowed politely without a single wink.",
                       {"lamp"}),
}

SURFACES = {
    "curtain": Surface("curtain", "curtain", "curtain", "shadow",
                       "The crown has grown taller than the mountain",
                       "the swinging lamp had stretched the crown's shadow on the curtain",
                       {"curtain", "shadow"}),
    "mirror": Surface("mirror", "mirror", "mirror", "sparkle",
                      "There are a hundred crowns hiding in the mirror",
                      "the shiny crown had bounced lamp-sparkles into the mirror",
                      {"mirror", "reflection"}),
    "window": Surface("window", "window", "window", "sparkle",
                      "The stars are stealing the crown",
                      "the lamp dots had reflected in the dark window",
                      {"window", "reflection"}),
    "wall": Surface("wall", "wall", "wall", "shadow",
                    "A giant king is peeking through the wall",
                    "the crown's shadow had landed on the plain wall",
                    {"shadow"}),
}

PLANS = {
    "move_lamp": Plan("move_lamp", "move the lamp", {"sparkle", "shadow"},
                      "hold the crown still", "move the lamp one inch at a time",
                      "When the lamp moved, the wild shape moved too.",
                      {"teamwork", "lamp"}),
    "cover_crown": Plan("cover_crown", "cover the crown", {"sparkle", "shadow"},
                        "cover the crown with a napkin", "watch the wall and window",
                        "When the crown was covered, the wild shape disappeared.",
                        {"teamwork", "crown"}),
    "wipe_mirror": Plan("wipe_mirror", "wipe the mirror", {"sparkle"},
                        "keep the lamp steady", "wipe the mirror with a clean cloth",
                        "The extra crowns vanished from the mirror as the cloth passed over it.",
                        {"teamwork", "reflection"}),
    "measure_shadow": Plan("measure_shadow", "measure the shadow", {"shadow"},
                           "stand beside the crown", "mark the shadow with chalk",
                           "The chalk marks proved the shadow grew only when the lamp swung.",
                           {"teamwork", "shadow"}),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Ella", "Rose"]
BOY_NAMES = ["Leo", "Tom", "Ben", "Max", "Finn", "Sam"]
TRAITS = ["curious", "bold", "careful", "cheerful", "imaginative"]


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for fair_id, fair in FAIRS.items():
        for crown_id, crown in CROWNS.items():
            for lamp_id, lamp in LAMPS.items():
                for surface_id, surface in SURFACES.items():
                    for plan_id, plan in PLANS.items():
                        if valid_combo(fair, crown, lamp, surface, plan):
                            combos.append((fair_id, crown_id, lamp_id, surface_id, plan_id))
    return sorted(combos)


@dataclass
class StoryParams:
    fair: str
    crown: str
    lamp: str
    surface: str
    plan: str
    hero: str
    hero_gender: str
    partner: str
    partner_gender: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "crown": [("What is a crown?",
               "A crown is a special headpiece that can show someone is pretending to be royal.")],
    "twinkling_lamp": [("Why does a twinkling lamp make things look different?",
                        "A twinkling lamp changes its light, so shiny things can flash or cast moving shadows.")],
    "reflection": [("What is a reflection?",
                    "A reflection is light bouncing off something shiny, like a mirror or dark window.")],
    "shadow": [("What is a shadow?",
                "A shadow is a dark shape made when something blocks light.")],
    "teamwork": [("Why did teamwork help?",
                  "Teamwork helped because one child could move or hold something while the other watched what changed.")],
    "lamp": [("How can moving a lamp test a mystery?",
              "If a strange shape moves when the lamp moves, the lamp is probably making the shape.")],
}
KNOWLEDGE_ORDER = ["crown", "twinkling_lamp", "reflection", "shadow", "teamwork", "lamp"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, partner = f["hero"], f["partner"]
    surface, crown = f["surface"], f["crown"]
    return [
        f'Write a tall tale for young children that includes "crown" and "twinkling lamp" and turns a misunderstanding into teamwork.',
        f"Tell a funny story where {hero.id} and {partner.id} see {surface.wild_claim.lower()}, then test the clue together.",
        f"Write a story about {crown.phrase}, a twinkling lamp, and two children who discover the ordinary cause of a giant rumor.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, partner = f["hero"], f["partner"]
    crown, lamp, surface, plan = f["crown"], f["lamp"], f["surface"], f["plan"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {partner.id}, who guarded {crown.phrase} at {world.fair.place}."),
        ("What caused the misunderstanding?",
         f"{lamp.phrase.capitalize()} shone on {crown.phrase}, and the light made a strange {surface.effect} on the {surface.label}."),
        ("What wild idea did the children hear?",
         f"The tall tale was that {surface.wild_claim.lower()}. It sounded enormous, but it came from a small trick of light."),
        ("How did teamwork solve it?",
         f"{hero.id} and {partner.id} used the plan to {plan.label}. One child did a job while the other watched what changed."),
    ]
    if f.get("resolved"):
        qa.append(("What was the truth?",
                   f"The truth was that {surface.ordinary_cause}. The crown was safe the whole time."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"crown", "teamwork"} | set(f["crown"].tags) | set(f["lamp"].tags) | set(f["surface"].tags) | set(f["plan"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    lines += [f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)]
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
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
        flags = []
        if e.reflective:
            flags.append("reflective")
        if e.twinkling:
            flags.append("twinkling")
        if flags:
            bits.append(f"flags={flags}")
        if e.clears:
            bits.append(f"clears={sorted(e.clears)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:9} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("lodge", "tin", "swinging_lamp", "curtain", "measure_shadow", "Mia", "girl", "Leo", "boy", "curious"),
    StoryParams("harvest", "gold", "twinkling_lamp", "mirror", "wipe_mirror", "Tom", "boy", "Lily", "girl", "careful"),
    StoryParams("school", "tin", "twinkling_lamp", "window", "move_lamp", "Zoe", "girl", "Finn", "boy", "bold"),
    StoryParams("school", "gold", "swinging_lamp", "wall", "cover_crown", "Sam", "boy", "Ava", "girl", "imaginative"),
]


def explain_rejection(fair: Fair, crown: Crown, lamp: Lamp, surface: Surface, plan: Plan) -> str:
    if not fair_hosts(fair, surface):
        return f"(No story: {fair.place} has no {surface.location} for this misunderstanding to appear on.)"
    if not crown.reflective:
        return f"(No story: {crown.phrase} is not shiny enough to throw a tall-tale sign.)"
    if not lamp.twinkle:
        return f"(No story: {lamp.phrase} does not twinkle, so it cannot create the misunderstanding.)"
    if lamp.effect != surface.effect:
        return f"(No story: {lamp.phrase} makes {lamp.effect}, but the {surface.label} needs {surface.effect}.)"
    return f"(No story: the plan '{plan.label}' does not test a {surface.effect}; teamwork must actually clear the cause.)"


ASP_RULES = r"""
host(F,S)       :- supports(F,Loc), surface_loc(S,Loc).
illusion(C,L,S) :- reflective(C), twinkling(L), lamp_effect(L,E), surface_effect(S,E).
clears_plan(P,S) :- clears(P,E), surface_effect(S,E).
valid(F,C,L,S,P) :- fair(F), crown(C), lamp(L), surface(S), plan(P), host(F,S), illusion(C,L,S), clears_plan(P,S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for fid, fair in FAIRS.items():
        lines.append(asp.fact("fair", fid))
        for loc in sorted(fair.supports):
            lines.append(asp.fact("supports", fid, loc))
    for cid, crown in CROWNS.items():
        lines.append(asp.fact("crown", cid))
        if crown.reflective:
            lines.append(asp.fact("reflective", cid))
    for lid, lamp in LAMPS.items():
        lines += [asp.fact("lamp", lid), asp.fact("lamp_effect", lid, lamp.effect)]
        if lamp.twinkle:
            lines.append(asp.fact("twinkling", lid))
    for sid, surface in SURFACES.items():
        lines += [
            asp.fact("surface", sid),
            asp.fact("surface_loc", sid, surface.location),
            asp.fact("surface_effect", sid, surface.effect),
        ]
    for pid, plan in PLANS.items():
        lines.append(asp.fact("plan", pid))
        for e in sorted(plan.clears):
            lines.append(asp.fact("clears", pid, e))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: crown, twinkling lamp, teamwork tall tale.")
    ap.add_argument("--fair", choices=FAIRS)
    ap.add_argument("--crown", choices=CROWNS)
    ap.add_argument("--lamp", choices=LAMPS)
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--partner")
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice([n for n in pool if n != avoid])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fair and args.crown and args.lamp and args.surface and args.plan:
        if not valid_combo(FAIRS[args.fair], CROWNS[args.crown], LAMPS[args.lamp], SURFACES[args.surface], PLANS[args.plan]):
            raise StoryError(explain_rejection(FAIRS[args.fair], CROWNS[args.crown], LAMPS[args.lamp], SURFACES[args.surface], PLANS[args.plan]))
    combos = [
        c for c in valid_combos()
        if (args.fair is None or c[0] == args.fair)
        and (args.crown is None or c[1] == args.crown)
        and (args.lamp is None or c[2] == args.lamp)
        and (args.surface is None or c[3] == args.surface)
        and (args.plan is None or c[4] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid crown-and-lamp tall tale matches the given options.)")
    fair, crown, lamp, surface, plan = rng.choice(combos)
    hg = args.hero_gender or rng.choice(["girl", "boy"])
    pg = args.partner_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hg)
    partner = args.partner or _pick_name(rng, pg, avoid=hero)
    return StoryParams(fair, crown, lamp, surface, plan, hero, hg, partner, pg, rng.choice(TRAITS))


def generate(params: StoryParams) -> StorySample:
    world = tell(
        FAIRS[params.fair], CROWNS[params.crown], LAMPS[params.lamp],
        SURFACES[params.surface], PLANS[params.plan],
        params.hero, params.hero_gender, params.partner, params.partner_gender, params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (fair, crown, lamp, surface, plan) combos:\n")
        for row in combos:
            print("  " + " ".join(f"{x:15}" for x in row))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
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
        p = sample.params
        header = ""
        if args.all:
            header = f"### {p.hero} & {p.partner}: {p.crown}, {p.lamp}, {p.surface}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
