#!/usr/bin/env python3
"""
A standalone storyworld for this seed:

    Words: icy statue
    Features: Flashback
    Style: Adventure

The world models a child on a small expedition who finds an icy statue blocking
the way. A physical trigger wakes a flashback stored in the statue, the flashback
reveals the right rescue method, and the method must actually address the ice
problem before the story is allowed to render.
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
CLUE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    need: str = ""
    solves: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "sister"}
        male = {"boy", "father", "uncle", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Route:
    id: str
    place: str
    goal: str
    weather: str
    affords: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Statue:
    id: str
    phrase: str
    figure: str
    block: str
    need: str
    memory: str
    freed: str
    danger: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Trigger:
    id: str
    label: str
    phrase: str
    action: str
    reveals: set[str]
    clue_power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    line: str
    solves: set[str]
    strength: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, route: Route) -> None:
        self.route = route
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
        clone = World(self.route)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_cold_fear(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    statue = world.entities.get("statue")
    if not hero or not statue or statue.meters["ice"] < THRESHOLD:
        return out
    sig = ("cold_fear", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["fear"] += 1
    return out


def _r_memory_clue(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    statue = world.entities.get("statue")
    trigger = world.entities.get("trigger")
    if not hero or not statue or not trigger:
        return out
    if trigger.meters["used"] < THRESHOLD or statue.memes["memory"] >= THRESHOLD:
        return out
    if statue.need not in trigger.solves:
        return out
    sig = ("memory", statue.id, trigger.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    statue.memes["memory"] += 1
    hero.memes["clue"] += trigger.meters["clue_power"]
    out.append("__flashback__")
    return out


def _r_free_statue(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    statue = world.entities.get("statue")
    method = world.entities.get("method")
    if not hero or not statue or not method:
        return out
    if method.meters["used"] < THRESHOLD or statue.need not in method.solves:
        return out
    sig = ("free", statue.id, method.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    statue.meters["ice"] = 0.0
    statue.meters["blocked"] = 0.0
    statue.memes["gratitude"] += 1
    hero.memes["courage"] += 1
    out.append("__free__")
    return out


CAUSAL_RULES = [
    Rule("cold_fear", "emotional", _r_cold_fear),
    Rule("memory_clue", "memory", _r_memory_clue),
    Rule("free_statue", "physical", _r_free_statue),
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


def can_reveal(trigger: Trigger, statue: Statue) -> bool:
    return statue.need in trigger.reveals and trigger.clue_power >= CLUE_MIN


def compatible_method(method: Method, statue: Statue) -> bool:
    return statue.need in method.solves and method.strength >= statue.danger


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for route_id, route in ROUTES.items():
        for statue_id in sorted(route.affords):
            statue = STATUES[statue_id]
            for trigger_id, trigger in TRIGGERS.items():
                if not can_reveal(trigger, statue):
                    continue
                for method_id, method in METHODS.items():
                    if compatible_method(method, statue):
                        combos.append((route_id, statue_id, trigger_id, method_id))
    return combos


def predict_flashback(world: World, trigger: Trigger) -> dict:
    sim = world.copy()
    trig = sim.get("trigger")
    trig.meters["used"] += 1
    trig.meters["clue_power"] = trigger.clue_power
    trig.solves = set(trigger.reveals)
    propagate(sim, narrate=False)
    return {
        "revealed": sim.get("statue").memes["memory"] >= THRESHOLD,
        "clue": sim.get("hero").memes["clue"],
    }


def introduce(world: World, hero: Entity, guide: Entity) -> None:
    trait = hero.traits[0] if hero.traits else "curious"
    world.say(
        f"Once there was a {trait} {hero.type} named {hero.id} who loved maps, "
        f"boots, and brave little adventures."
    )
    world.say(
        f"One {world.route.weather} morning, {hero.id} and {hero.pronoun('possessive')} "
        f"{guide.label_word} followed a trail through {world.route.place} to reach "
        f"{world.route.goal}."
    )


def find_statue(world: World, hero: Entity, statue_cfg: Statue) -> None:
    statue = world.add(Entity("statue", type="statue", label=statue_cfg.figure, need=statue_cfg.need))
    statue.meters["ice"] = 1
    statue.meters["blocked"] = 1
    propagate(world, narrate=False)
    world.say(
        f"Halfway there, they found {statue_cfg.phrase}. It stood across the path, "
        f"blue with frost, and {statue_cfg.block}."
    )


def caution(world: World, guide: Entity, hero: Entity) -> None:
    hero.memes["desire"] += 1
    guide.memes["care"] += 1
    world.say(
        f'"We cannot shove it or climb over it," said {hero.pronoun("possessive")} '
        f"{guide.label_word}. \"Ice remembers pressure, and pressure can crack.\""
    )


def touch_trigger(world: World, hero: Entity, trigger_cfg: Trigger, statue_cfg: Statue) -> bool:
    trigger = world.add(Entity("trigger", type="tool", label=trigger_cfg.label,
                               solves=set(trigger_cfg.reveals)))
    trigger.meters["used"] += 1
    trigger.meters["clue_power"] = trigger_cfg.clue_power
    pred = predict_flashback(world, trigger_cfg)
    world.facts["predicted_flashback"] = pred
    world.say(f"{hero.id} {trigger_cfg.action}.")
    propagate(world, narrate=False)
    if not pred["revealed"]:
        return False
    hero.memes["wonder"] += 1
    world.say(
        f"Suddenly the ice glowed, and a flashback opened inside it. "
        f"{hero.id} saw the statue long ago, before the storm, when {statue_cfg.memory}"
    )
    return True


def choose_method(world: World, hero: Entity, guide: Entity, method_cfg: Method) -> None:
    method = world.add(Entity("method", type="tool", label=method_cfg.label,
                              solves=set(method_cfg.solves)))
    if hero.memes["clue"] >= CLUE_MIN:
        hero.memes["courage"] += 1
    world.say(
        f'"The memory is a clue," whispered {hero.id}. '
        f'"We should use {method_cfg.label}, not muscle."'
    )
    method.meters["used"] += 1
    propagate(world, narrate=False)
    world.say(f"Together they {method_cfg.line}.")
    guide.memes["pride"] += 1


def finish(world: World, hero: Entity, guide: Entity, statue_cfg: Statue) -> None:
    statue = world.get("statue")
    if statue.meters["blocked"] <= 0:
        hero.memes["joy"] += 1
        world.say(
            f"The ice loosened with a soft crackle. {statue_cfg.freed} "
            f"The path opened, and {hero.pronoun('possessive')} "
            f"{guide.label_word} squeezed {hero.id}'s shoulder."
        )
        world.say(
            f"{hero.id} carried the lesson down the trail: old places are easier "
            f"to save when you listen before you act."
        )
    else:
        hero.memes["patience"] += 1
        world.say(
            f"The statue stayed frozen, so {hero.id} marked the path and came home "
            f"to ask for better help."
        )


def tell(route: Route, statue_cfg: Statue, trigger_cfg: Trigger, method_cfg: Method,
         name: str, gender: str, guide_type: str, trait: str) -> World:
    world = World(route)
    hero = world.add(Entity("hero", kind="character", type=gender, label=name,
                            traits=[trait], role="hero"))
    hero.id = name
    world.entities["hero"] = hero
    guide = world.add(Entity("Guide", kind="character", type=guide_type,
                             label="the guide", role="guide"))
    introduce(world, hero, guide)
    world.para()
    find_statue(world, hero, statue_cfg)
    caution(world, guide, hero)
    world.para()
    touch_trigger(world, hero, trigger_cfg, statue_cfg)
    choose_method(world, hero, guide, method_cfg)
    finish(world, hero, guide, statue_cfg)
    world.facts.update(hero=hero, guide=guide, route=route, statue_cfg=statue_cfg,
                       trigger=trigger_cfg, method=method_cfg,
                       freed=world.get("statue").meters["blocked"] <= 0,
                       clue=hero.memes["clue"])
    return world


ROUTES = {
    "ridge": Route("ridge", "the silver ridge", "the hidden lookout", "windy",
                   {"sentinel", "bear"}, {"ice", "mountain"}),
    "cave": Route("cave", "the echoing ice cave", "the blue lantern room", "snowy",
                  {"sentinel", "fox"}, {"ice", "cave"}),
    "bridge": Route("bridge", "the frost bridge", "the far pine camp", "misty",
                    {"bear", "gatekeeper"}, {"ice", "bridge"}),
}

STATUES = {
    "sentinel": Statue(
        "sentinel", "an icy statue of a mountain sentinel", "sentinel",
        "held a frozen spear across the trail", "warmth",
        "a lost hiker had warmed the sentinel's hands and been shown the safe turn.",
        "The sentinel lowered its spear and pointed toward the safe pass.",
        2, {"statue", "warmth"}),
    "bear": Statue(
        "bear", "an icy statue of a great bear", "bear",
        "blocked the bridge with one glittering paw", "sound",
        "a child had sung the bear awake and the bear had guarded the bridge.",
        "The bear bowed its shining head and stepped aside.",
        2, {"statue", "sound"}),
    "fox": Statue(
        "fox", "an icy statue of a snow fox", "fox",
        "curled around a crack in the floor", "light",
        "moonlight had once shown the fox where the thin ice lay.",
        "The fox's tail shone, marking every safe stone.",
        1, {"statue", "light"}),
    "gatekeeper": Statue(
        "gatekeeper", "an icy statue of an old gatekeeper", "gatekeeper",
        "kept both hands locked over the latch", "warmth",
        "a traveler had thawed the latch slowly and promised never to force it.",
        "The gatekeeper opened the latch with a frosty smile.",
        3, {"statue", "warmth"}),
}

TRIGGERS = {
    "mitten": Trigger("mitten", "a red wool mitten", "a red wool mitten",
                      "pressed a red wool mitten to the statue's hand",
                      {"warmth"}, 2, {"mitten", "warmth"}),
    "bell": Trigger("bell", "a tiny trail bell", "a tiny trail bell",
                    "rang a tiny trail bell beside the frozen ear",
                    {"sound"}, 2, {"bell", "sound"}),
    "lamp": Trigger("lamp", "a pocket lantern", "a pocket lantern",
                    "opened a pocket lantern so its beam crossed the ice",
                    {"light"}, 2, {"lantern", "light"}),
    "map": Trigger("map", "an old map", "an old map",
                   "laid an old map against the statue's chest",
                   {"memory"}, 1, {"map"}),
}

METHODS = {
    "warm_scarf": Method("warm_scarf", "a warm scarf",
                         "wrapped the scarf around the frozen joint and waited",
                         {"warmth"}, 2, {"warmth", "scarf"}),
    "sun_mirror": Method("sun_mirror", "a mirror of sunlight",
                         "tilted a small mirror until sunlight ran along the ice",
                         {"light"}, 2, {"light", "mirror"}),
    "song": Method("song", "a steady song",
                   "sang the tune from the flashback until the ice hummed back",
                   {"sound"}, 2, {"sound", "song"}),
    "camp_stove": Method("camp_stove", "a careful camp stove",
                         "set a tiny safe flame far back and let warm air drift over the frozen place",
                         {"warmth"}, 3, {"warmth"}),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Eli"]
TRAITS = ["curious", "brave", "careful", "quick", "patient", "bright"]


@dataclass
class StoryParams:
    route: str
    statue: str
    trigger: str
    method: str
    name: str
    gender: str
    guide: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "ice": [("What is ice?", "Ice is frozen water. It can be slippery, hard, and very cold.")],
    "statue": [("What is a statue?", "A statue is a shaped figure made from stone, metal, ice, or another material.")],
    "warmth": [("Why can warmth loosen ice?", "Warmth gives frozen water energy, so some of the ice can melt and let stuck parts move.")],
    "sound": [("How can sound help in a story?", "Sound can carry a signal. In a story, a bell or song can wake attention without pushing or breaking things.")],
    "light": [("Why is light useful in an ice cave?", "Light helps people see cracks and paths, and shiny ice can reflect it into hidden places.")],
    "mountain": [("Why should hikers be careful on a mountain?", "Mountains can have cold wind, loose stones, and thin ice, so hikers need to move slowly and watch the trail.")],
    "bridge": [("Why can an icy bridge be risky?", "An icy bridge can be slippery, and cracks can be hard to see.")],
}
KNOWLEDGE_ORDER = ["ice", "statue", "warmth", "sound", "light", "mountain", "bridge"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, route, statue, trigger = f["hero"], f["route"], f["statue_cfg"], f["trigger"]
    return [
        'Write an adventure story for young children that includes the words "icy statue" and uses a flashback as a clue.',
        f"Tell a story where {hero.id} finds {statue.phrase} in {route.place}, wakes an old memory with {trigger.phrase}, and solves the problem gently.",
        f"Write a short adventure about listening to the past before trying to force a path open.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, guide = f["hero"], f["guide"]
    route, statue, trigger, method = f["route"], f["statue_cfg"], f["trigger"], f["method"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id}, a {hero.type}, and {hero.pronoun('possessive')} {guide.label_word} on an adventure."),
        ("What blocked the path?",
         f"{statue.phrase.capitalize()} blocked the path in {route.place}. It was frozen in place and could not be forced aside safely."),
        ("What did the flashback show?",
         f"The flashback showed that {statue.memory} That memory gave {hero.id} a clue about using {method.label}."),
        ("How did they solve the problem?",
         f"They used {method.label} because it matched what the icy statue needed. The statue moved aside, so the path opened without breaking it."),
        ("What lesson did the adventure teach?",
         f"{hero.id} learned to listen before acting. The old memory helped {hero.pronoun('object')} choose a careful solution instead of forcing the ice."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["route"].tags) | set(f["statue_cfg"].tags) | set(f["trigger"].tags) | set(f["method"].tags)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.need:
            bits.append(f"need={e.need}")
        if e.solves:
            bits.append(f"solves={sorted(e.solves)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("ridge", "sentinel", "mitten", "warm_scarf", "Lily", "girl", "father", "curious"),
    StoryParams("cave", "fox", "lamp", "sun_mirror", "Max", "boy", "mother", "careful"),
    StoryParams("bridge", "bear", "bell", "song", "Zoe", "girl", "father", "brave"),
    StoryParams("bridge", "gatekeeper", "mitten", "camp_stove", "Sam", "boy", "mother", "patient"),
]


def explain_rejection(statue: Statue, trigger: Optional[Trigger], method: Optional[Method]) -> str:
    if trigger is not None and not can_reveal(trigger, statue):
        return (f"(No story: {trigger.label} cannot wake the {statue.need} memory "
                f"inside the {statue.figure}, so the flashback would not provide a grounded clue.)")
    if method is not None and not compatible_method(method, statue):
        return (f"(No story: {method.label} does not solve the statue's {statue.need} problem "
                f"strongly enough, so the rescue would be forced rather than reasonable.)")
    return "(No story: the route, trigger, and method do not form a compatible adventure.)"


ASP_RULES = r"""
can_reveal(T, S) :- trigger(T), statue(S), reveals(T, Need), statue_need(S, Need),
                    clue_power(T, P), clue_min(M), P >= M.
can_solve(Md, S) :- method(Md), statue(S), solves(Md, Need), statue_need(S, Need),
                    strength(Md, P), danger(S, D), P >= D.
valid(R, S, T, Md) :- route(R), affords(R, S), can_reveal(T, S), can_solve(Md, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = [asp.fact("clue_min", CLUE_MIN)]
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        for sid in sorted(route.affords):
            lines.append(asp.fact("affords", rid, sid))
    for sid, statue in STATUES.items():
        lines.append(asp.fact("statue", sid))
        lines.append(asp.fact("statue_need", sid, statue.need))
        lines.append(asp.fact("danger", sid, statue.danger))
    for tid, trigger in TRIGGERS.items():
        lines.append(asp.fact("trigger", tid))
        lines.append(asp.fact("clue_power", tid, trigger.clue_power))
        for need in sorted(trigger.reveals):
            lines.append(asp.fact("reveals", tid, need))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("strength", mid, method.strength))
        for need in sorted(method.solves):
            lines.append(asp.fact("solves", mid, need))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
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
    ap = argparse.ArgumentParser(description="Story world: icy statue flashback adventure.")
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--statue", choices=STATUES)
    ap.add_argument("--trigger", choices=TRIGGERS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=["mother", "father"])
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    statue = STATUES[args.statue] if args.statue else None
    trigger = TRIGGERS[args.trigger] if args.trigger else None
    method = METHODS[args.method] if args.method else None
    if statue and trigger and not can_reveal(trigger, statue):
        raise StoryError(explain_rejection(statue, trigger, None))
    if statue and method and not compatible_method(method, statue):
        raise StoryError(explain_rejection(statue, None, method))
    combos = [c for c in valid_combos()
              if (args.route is None or c[0] == args.route)
              and (args.statue is None or c[1] == args.statue)
              and (args.trigger is None or c[2] == args.trigger)
              and (args.method is None or c[3] == args.method)]
    if not combos:
        raise StoryError("(No valid icy-statue story matches the given options.)")
    route, statue_id, trigger_id, method_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = args.guide or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(route, statue_id, trigger_id, method_id, name, gender, guide, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(ROUTES[params.route], STATUES[params.statue], TRIGGERS[params.trigger],
                 METHODS[params.method], params.name, params.gender,
                 params.guide, params.trait)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (route, statue, trigger, method) combos:\n")
        for row in combos:
            print("  " + " ".join(f"{part:12}" for part in row))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.name}: {p.statue} via {p.trigger}/{p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
