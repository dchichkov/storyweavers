#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/invasion_curiosity_moral_value_happy_ending_superhero.py
========================================================================================

A standalone story world for a small superhero tale: a curious kid sees a strange
"invasion" of tiny glowing bots in the city, chooses to do the right thing, and
with a hero's help turns the problem into a happy ending.

The world is modeled as a compact simulation with typed entities, physical meters,
emotional memes, forward-chained rules, a reasonableness gate, and an inline ASP
twin for parity checks.

The story premise is intentionally small and child-facing:
- curiosity leads the protagonist toward the unknown,
- moral value keeps them from doing the selfish thing,
- a superhero helps solve the problem,
- the ending proves the city is safe and brighter than before.
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

HERO_NAMES = ["Nova", "Piper", "Milo", "Zuri", "Aria", "Jude", "Kai", "Lina"]
SIDEKICK_NAMES = ["Bean", "Tess", "Rae", "Otis", "Nia", "Bo", "Skye", "Finn"]
SUPERHERO_NAMES = ["Captain Comet", "Silver Shield", "Rocket Ray", "Starburst"]
VILLAIN_NAMES = ["the Glitch King", "Dr. Wobble", "the Grin Gremlin", "the Smoke Sprite"]
PLACES = ["the museum", "the library roof", "the city square", "the park fountain"]
PROBLEM_ITEMS = ["glowing drone", "tiny metal bug", "shiny robot crab", "buzzing orb"]
SAFE_TOOLS = ["signal beacon", "big flashlight", "loud whistle", "mirror sign"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    exposed: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Problem:
    id: str
    label: str
    swarm_word: str
    noise: str
    curious_hook: str
    harm: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    power: int
    tool: str
    action: str
    text: str
    fail: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["alarm"] < THRESHOLD:
            continue
        sig = ("alarm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("city").meters["danger"] += 1
        for cid, ent in world.entities.items():
            if ent.role in {"child", "sidekick"}:
                ent.memes["worry"] += 1
        out.append("__alarm__")
    return out


def _r_good_choice(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("kid")
    hero = world.entities.get("hero")
    if not kid or not hero:
        return out
    if kid.memes["curiosity"] < THRESHOLD or kid.memes["moral"] < THRESHOLD:
        return out
    sig = ("good", kid.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.memes["brave"] += 1
    hero.memes["trust"] += 1
    out.append("__good__")
    return out


CAUSAL_RULES = [Rule("alarm", "danger", _r_alarm), Rule("good_choice", "social", _r_good_choice)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness(problem: Problem, place: Place, response: Response) -> bool:
    return place.exposed and response.sense >= SENSE_MIN and "invasion" in problem.tags


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def choose_response_for_severity(response: Response, severity: int) -> bool:
    return response.power >= severity


def predict_invasion(world: World, problem_id: str) -> dict:
    sim = world.copy()
    _cause_problem(sim, sim.get(problem_id), narrate=False)
    return {"danger": sim.get("city").meters["danger"], "alarm": sim.get(problem_id).meters["alarm"] >= THRESHOLD}


def _cause_problem(world: World, problem_ent: Entity, narrate: bool = True) -> None:
    problem_ent.meters["alarm"] += 1
    problem_ent.meters["spread"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, kid: Entity, sidekick: Entity, place: Place, problem: Problem) -> None:
    world.say(
        f"On a bright afternoon, {kid.id} and {sidekick.id} raced to {place.label}. "
        f"They were pretending to be superhero helpers when a strange {problem.swarm_word} "
        f"buzzed into the air."
    )
    world.say(
        f'"Look!" {kid.id} said. "That {problem.noise} sounds like an invasion!" '
        f"{sidekick.id} leaned closer, curious but careful."
    )
    kid.memes["joy"] += 1
    sidekick.memes["curiosity"] += 1


def curiosity_beat(world: World, kid: Entity, sidekick: Entity, problem: Problem) -> None:
    kid.memes["curiosity"] += 1
    world.say(
        f"{kid.id} wanted to peek at the tiny {problem.label} and see where it came from. "
        f"{sidekick.id} thought it looked cool too, because curious eyes always notice shiny things."
    )


def moral_choice(world: World, kid: Entity, hero: Entity, place: Place, problem: Problem) -> None:
    kid.memes["moral"] += 1
    pred = predict_invasion(world, "problem")
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'But {kid.id} remembered that sneaking off with something found in {place.label} would be wrong. '
        f'"We should tell a hero," {kid.id} said. "It could be part of the invasion, and somebody might need help."'
    )
    if pred["danger"] >= THRESHOLD:
        world.say(f"{kid.id} stayed with the group instead of chasing the shiny thing alone.")


def villain_move(world: World, villain: Entity, problem: Entity, problem_cfg: Problem) -> None:
    villain.memes["scheming"] += 1
    world.say(
        f"Then {villain.id} tried to use the little {problem_cfg.swarm_word} to scare everyone away."
    )
    _cause_problem(world, problem)


def call_hero(world: World, kid: Entity, hero: Entity, place: Place) -> None:
    world.say(
        f'"{hero.id}!" {kid.id} called. "There is an invasion at {place.label}!" '
        f'{hero.id} heard the call and flashed a calm smile.'
    )


def rescue(world: World, hero: Entity, response: Response, problem_ent: Entity, problem: Problem) -> None:
    problem_ent.meters["alarm"] = 0.0
    world.get("city").meters["danger"] = 0.0
    hero.memes["hope"] += 1
    world.say(
        f"{hero.id} dashed in with a {response.tool} and {response.text.replace('{problem}', problem.label)}."
    )
    world.say(f"The buzzing quieted, and the invasion lost its scary spark.")


def rescue_fail(world: World, hero: Entity, response: Response, problem_ent: Entity, problem: Problem) -> None:
    world.get("city").meters["danger"] += 1
    problem_ent.meters["alarm"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} tried to help with a {response.tool}, but {response.fail.replace('{problem}', problem.label)}."
    )
    world.say("Still, the hero kept everyone moving together until the danger passed.")


def ending(world: World, kid: Entity, sidekick: Entity, hero: Entity, place: Place) -> None:
    kid.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"After the trouble was gone, {hero.id} gave the children a safe signal beacon and a lesson: "
        f"curious minds are good, but helping first is better."
    )
    world.say(
        f"{kid.id} and {sidekick.id} watched the sky turn gold over {place.label}, knowing the city was safe again."
    )


def tell(place: Place, problem: Problem, response: Response, kid_name: str, sidekick_name: str,
         hero_name: str, villain_name: str) -> World:
    world = World()
    kid = world.add(Entity(id=kid_name, kind="character", type="boy" if kid_name in {"Milo", "Jude", "Kai"} else "girl", role="child"))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="boy" if sidekick_name in {"Bo", "Finn", "Otis"} else "girl", role="sidekick"))
    hero = world.add(Entity(id=hero_name, kind="character", type="man", role="hero"))
    villain = world.add(Entity(id=villain_name, kind="character", type="man", role="villain"))
    city = world.add(Entity(id="city", type="city", label="the city"))
    prob_ent = world.add(Entity(id="problem", type="thing", label=problem.label, role="problem"))

    kid.memes["curiosity"] = 1.0
    kid.memes["moral"] = 0.0
    sidekick.memes["curiosity"] = 1.0
    hero.memes["trust"] = 0.0
    world.facts.update(place=place, problem=problem, response=response, kid=kid, sidekick=sidekick, hero=hero, villain=villain, problem_ent=prob_ent)

    opening(world, kid, sidekick, place, problem)
    world.para()
    curiosity_beat(world, kid, sidekick, problem)
    moral_choice(world, kid, hero, place, problem)
    world.para()
    villain_move(world, villain, prob_ent, problem)
    call_hero(world, kid, hero, place)
    world.para()
    severity = 1 + int(problem_ent.meters["spread"])
    if choose_response_for_severity(response, severity):
        rescue(world, hero, response, prob_ent, problem)
    else:
        rescue_fail(world, hero, response, prob_ent, problem)
    world.para()
    ending(world, kid, sidekick, hero, place)
    world.facts["outcome"] = "happy"
    return world


SETTINGS = {
    "museum": Place("museum", "the museum"),
    "library": Place("library", "the library roof"),
    "square": Place("square", "the city square"),
    "park": Place("park", "the park fountain"),
}

PROBLEMS = {
    "drone": Problem("drone", "tiny glowing drones", "drone swarm", "high beep", "glowing bits", "alarm", {"invasion"}),
    "robot_crab": Problem("robot_crab", "shiny robot crabs", "robot crab swarm", "clack-clack", "shiny shells", "alarm", {"invasion"}),
    "orb": Problem("orb", "buzzing orbs", "orb swarm", "whirr-whirr", "bright sparks", "alarm", {"invasion"}),
}

RESPONSES = {
    "beacon": Response("beacon", 3, 3, "signal beacon", "shine the beacon", "shined the beacon until the drones turned toward the light", "waved it around, but the swarm kept buzzing", {"signal"}),
    "flashlight": Response("flashlight", 2, 2, "big flashlight", "point the flashlight", "pointed the flashlight and guided everyone to the steps", "pointed the flashlight, but the swarm was too tangled to follow", {"light"}),
    "whistle": Response("whistle", 2, 2, "loud whistle", "blow the whistle", "blew the whistle and made a clear path for people to move", "blew the whistle, but the noise only made the swarm bounce more", {"sound"}),
    "mirror": Response("mirror", 3, 3, "mirror sign", "flash the mirror", "flashed the mirror and sent the swarm drifting toward the open sky", "flashed the mirror, but the clouds swallowed the light", {"signal"}),
}


@dataclass
class StoryParams:
    place: str
    problem: str
    response: str
    kid: str
    sidekick: str
    hero: str
    villain: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")

CURATED = [
    dataclass(type("P", (), {}))
]



def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in SETTINGS:
        for pr in PROBLEMS:
            for r in RESPONSES:
                if reasonableness(PROBLEMS[pr], SETTINGS[p], RESPONSES[r]):
                    combos.append((p, pr, r))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story about {f["kid"].id} noticing an invasion at {f["place"].label}. Include the word "invasion".',
        f"Tell a child-friendly superhero tale where curiosity leads {f['kid'].id} to investigate strange {f['problem'].label}, but {f['kid'].id} chooses to do the moral thing and call {f['hero'].id}.",
        f"Write a happy-ending story with a superhero, a curious child, and a safe response that stops an invasion.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid, sidekick, hero, place, prob, resp = f["kid"], f["sidekick"], f["hero"], f["place"], f["problem"], f["response"]
    return [
        ("Who noticed the invasion first?",
         f"{kid.id} noticed it first because {kid.id} was curious and wanted to know what the strange {prob.label} were doing at {place.label}."),
        ("Why did the child call the superhero instead of grabbing the shiny thing?",
         f"{kid.id} remembered that it would be wrong to take something that might belong to someone else or be part of the invasion. So {kid.id} chose the moral thing and asked {hero.id} for help."),
        ("How did the story end?",
         f"It ended happily: {hero.id} used a {resp.tool} to calm the problem, and the city was safe again. {kid.id} and {sidekick.id} could look at the bright sky without fear."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does curiosity mean?", "Curiosity means wanting to know more and asking questions about something new."),
        QAItem("What is a hero?", "A hero is someone who helps others and does the right thing, especially when there is trouble."),
        QAItem("What does a happy ending mean?", "A happy ending means the problem gets fixed and the characters finish safe and glad."),
    ]


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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(problem: Problem, place: Place, response: Response) -> str:
    return f"(No story: this combination does not make a believable invasion scene.)"


ASP_RULES = r"""
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(P, Pr, R) :- place(P), problem(Pr), response(R), exposed(P), invasion(Pr), sensible(R).
happy :- chosen_response(R), chosen_problem(Pr), power(R, P), severity(Pr, S), P >= S.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("exposed", pid))
    for pid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("invasion", pid))
        lines.append(asp.fact("severity", pid, 1))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    sample = generate(resolve_params(argparse.Namespace(place=None, problem=None, response=None), random.Random(3)))
    if not sample.story.strip():
        return 1
    print("OK: story generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero curiosity / moral-value / happy-ending story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--response", choices=RESPONSES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, response = rng.choice(sorted(combos))
    kid = rng.choice(HERO_NAMES)
    sidekick = rng.choice([n for n in SIDEKICK_NAMES if n != kid])
    hero = rng.choice(SUPERHERO_NAMES)
    villain = rng.choice(VILLAIN_NAMES)
    return StoryParams(place, problem, response, kid, sidekick, hero, villain)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PROBLEMS[params.problem], RESPONSES[params.response],
                 params.kid, params.sidekick, params.hero, params.villain)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{p} {pr} {r}" for p, pr, r in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(p, pr, r, HERO_NAMES[0], SIDEKICK_NAMES[0], SUPERHERO_NAMES[0], VILLAIN_NAMES[0]))
                   for p, pr, r in valid_combos()[:3]]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
