#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/trust_confuse_dialogue_humor_fable.py
======================================================================

A small fable world about trust, confusion, dialogue, and a light joke that
turns into a wise ending.

Premise:
- A proud little animal wants to solve a problem.
- A chatty helper gives confusing advice, often funny but not always useful.
- A calmer friend tells the truth with a short dialogue.
- Trust is tested, confusion clears, and the group learns a fable-like lesson.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- eager import of storyworlds/results.py
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- --qa, --json, --asp, --verify, --show-asp, --all, --seed, --trace, -n
- Python reasonableness gate plus inline ASP twin
- world model uses physical meters and emotional memes
- QA is grounded in simulated world state rather than rendered English
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
TRUST_TO_ACT = 2
CONFUSE_LIMIT = 1
HUMOR_LIMIT = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"hen", "girl", "mother", "woman"}
        male = {"rooster", "boy", "father", "man"}
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
    name: str
    place: str
    mood: str


@dataclass
class Problem:
    id: str
    task: str
    object_name: str
    risk: str
    confusion_source: str
    joke_line: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    calm: int
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_confuse(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["confusion"] < THRESHOLD:
            continue
        sig = ("confuse", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["trust"] -= 0.25
        out.append("")
    return out


def _r_clear(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["clarity"] < THRESHOLD:
            continue
        sig = ("clear", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["confusion"] = max(0.0, e.meters["confusion"] - 1.0)
        e.memes["trust"] += 0.5
        out.append("")
    return out


CAUSAL_RULES = [Rule("confuse", "mental", _r_confuse), Rule("clear", "mental", _r_clear)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def suspicious_problem(problem: Problem) -> bool:
    return bool(problem.object_name and problem.risk)


def sensible_response(resp: Response) -> bool:
    return resp.sense >= 2


def can_repair(trust: float, confuse: float, response: Response) -> bool:
    return trust >= TRUST_TO_ACT and confuse <= CONFUSE_LIMIT and response.calm >= 2


def predict(world: World, problem: Problem, response: Response) -> dict:
    sim = world.copy()
    sim.get("hero").meters["confusion"] += 1
    sim.get("hero").memes["trust"] -= 0.5
    if can_repair(sim.get("hero").memes["trust"], sim.get("hero").meters["confusion"], response):
        sim.get("hero").meters["clarity"] += 1
    return {
        "confusion": sim.get("hero").meters["confusion"],
        "trust": sim.get("hero").memes["trust"],
    }


def introduce(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    world.say(
        f"On a bright morning at {setting.name}, {hero.id} and {friend.id} met by "
        f"the {setting.place}. {hero.id} wanted to solve a small problem, and "
        f"{friend.id} was ready with a grin."
    )


def problem_set(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["want"] += 1
    world.say(
        f"{hero.id} pointed at {problem.object_name}. \"I want to {problem.task},\" "
        f"{hero.id} said. \"But this thing keeps acting like a clever goose.\""
    )


def confuse(world: World, trickster: Entity, hero: Entity, problem: Problem) -> None:
    hero.meters["confusion"] += 1
    hero.memes["trust"] -= 0.5
    trickster.memes["humor"] += 1
    world.say(
        f"{trickster.id} blinked and gave a very silly answer. "
        f"\"Easy,\" {trickster.id} said, \"just ask the {problem.object_name} to "
        f"stand still and think about its manners.\""
    )
    world.say(problem.joke_line)


def warn(world: World, friend: Entity, hero: Entity, problem: Problem) -> None:
    pred = predict(world, problem, RESPONSES["honest"])
    friend.meters["clarity"] += 1
    world.facts["pred_confusion"] = pred["confusion"]
    world.say(
        f"{friend.id} shook {friend.pronoun('possessive')} head. "
        f"\"That joke is funny, but it will only confuse you more,\" {friend.id} "
        f"said. \"Let's do the honest thing.\""
    )


def honest_talk(world: World, friend: Entity, hero: Entity, problem: Problem, response: Response) -> None:
    hero.meters["clarity"] += 1
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"\"You're right,\" {hero.id} said. \"I trust you more when you speak plainly.\" "
        f"Then {friend.id} replied, \"Good. Let's {problem.task} by {response.text}.\""
    )


def solve(world: World, hero: Entity, problem: Problem, response: Response) -> None:
    hero.meters["confusion"] = 0.0
    hero.meters["clarity"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"Together they {response.text}, and at last the {problem.object_name} was no longer "
        f"such a puzzle."
    )
    world.say(
        f"{problem.lesson.capitalize()}, and {hero.id} laughed at the silly little mistake."
    )


SETTINGS = {
    "farm": Setting("farm", "the old farm", "barn door", "sunny"),
    "garden": Setting("garden", "the garden path", "stone path", "gentle"),
    "village": Setting("village", "the village square", "wishing well", "busy"),
}

PROBLEMS = {
    "gate": Problem(
        "gate",
        "open the gate",
        "gate latch",
        "it keeps looking upside down",
        "the crow says the latch is 'smiling'",
        "The crow laughed so hard that even the hens looked offended.",
        "A wise helper speaks clearly when another is confused.",
        tags={"gate", "crow", "humor"},
    ),
    "jar": Problem(
        "jar",
        "open the jar",
        "jam jar",
        "it is slippery and stuck",
        "the mouse says the lid is 'sleeping'",
        "The mouse bowed and said the lid needed a bedtime song.",
        "A friend who tells the truth helps more than a joke that hides the answer.",
        tags={"jar", "mouse", "humor"},
    ),
    "cart": Problem(
        "cart",
        "move the cart",
        "cart wheel",
        "one wheel is turned the wrong way",
        "the duck claimed the wheel was 'thinking sideways'",
        "The duck quacked, and the wheel did not feel wiser for it.",
        "Trust grows when advice is simple and kind.",
        tags={"cart", "duck", "humor"},
    ),
}

RESPONSES = {
    "honest": Response("honest", 3, 3, "lifted the latch the right way", "could not lift it", "lifted the latch the right way", tags={"truth"}),
    "steady": Response("steady", 2, 2, "turned the wheel until it faced forward", "turned too hard and made the wheel wobble", "turned the wheel until it faced forward", tags={"repair"}),
    "gentle": Response("gentle", 2, 2, "patted the jar lid with a cloth and twisted slowly", "twisted too fast and lost the grip", "patted the jar lid with a cloth and twisted slowly", tags={"repair"}),
}

HERO_NAMES = ["Milo", "Nina", "Pip", "Lia", "Toby", "Mara"]
FRIEND_NAMES = ["Crow", "Mouse", "Duck", "Goat", "Hen", "Fox"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    response: str
    hero: str
    friend: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PROBLEMS:
            if suspicious_problem(PROBLEMS[p]):
                combos.append((s, p))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about trust, confusion, and dialogue.")
    ap.add_argument("--setting", choices=SETTINGS)
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
    if args.response and not sensible_response(RESPONSES[args.response]):
        raise StoryError(f"(Refusing response '{args.response}': too weak and confusing.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    hero = rng.choice(HERO_NAMES)
    friend = rng.choice(FRIEND_NAMES)
    while friend == hero:
        friend = rng.choice(FRIEND_NAMES)
    return StoryParams(setting, problem, response, hero, friend)


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    response = RESPONSES[params.response]
    hero = world.add(Entity("hero", kind="character", type="goat", label=params.hero, role="hero"))
    friend = world.add(Entity("friend", kind="character", type="crow", label=params.friend, role="friend"))
    object_ent = world.add(Entity("object", kind="thing", type=problem.object_name, label=problem.object_name))
    world.facts["problem"] = problem
    world.facts["response"] = response

    introduce(world, hero, friend, setting)
    world.para()
    problem_set(world, hero, problem)
    confuse(world, friend, hero, problem)
    warn(world, friend, hero, problem)
    world.para()
    honest_talk(world, friend, hero, problem, response)
    solve(world, hero, problem, response)
    world.facts.update(hero=hero, friend=friend, object=object_ent, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    problem = f["problem"]
    return [
        f'Write a fable-like story for a small child that includes the words "trust" and "confuse".',
        f"Tell a short animal story where {f['hero'].id} is confused by a funny joke about the {problem.object_name}, but a friend speaks plainly and helps.",
        f'Write a humorous fable with dialogue that teaches why clear advice builds trust.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, problem = f["hero"], f["friend"], f["problem"]
    return [
        QAItem(
            question="Why did the hero feel confused?",
            answer=f"{hero.id} felt confused because {friend.id} answered with a funny joke instead of a clear plan. The joke made the {problem.object_name} sound silly, but it did not help solve the problem."
        ),
        QAItem(
            question="How did trust change in the story?",
            answer=f"Trust grew after {friend.id} spoke clearly and {hero.id} heard an honest answer. The honest talk made it easier for {hero.id} to listen and follow the good advice."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the problem fixed and a laugh shared between friends. The fable-like lesson is that clear words help more than confusing ones."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    problem = f["problem"]
    return [
        QAItem(
            question="What is trust?",
            answer="Trust is believing that someone will tell the truth, keep a promise, or give helpful advice. It grows when words and actions match."
        ),
        QAItem(
            question="What does confuse mean?",
            answer="To confuse someone means to make them unsure or mixed up. Confusing words can make a problem harder to solve."
        ),
        QAItem(
            question=f"Why can a joke be funny but not helpful for {problem.object_name}?",
            answer="A joke can make everyone laugh, but a real problem still needs a clear answer. Humor is nice, but honest help is what fixes things."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
suspicious(P) :- problem(P).
sensible(R) :- response(R), sense(R,S), S >= 2.
valid(S, P) :- setting(S), problem(P), suspicious(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid_combos().")
        rc = 1
    if set(asp_sensible()) != {r for r, v in RESPONSES.items() if v.sense >= 2}:
        print("MISMATCH in sensible responses.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP/Python parity and generation smoke test passed.")
    return rc


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("farm", "gate", "honest", "Milo", "Crow"),
    StoryParams("garden", "jar", "gentle", "Nina", "Mouse"),
    StoryParams("village", "cart", "steady", "Pip", "Duck"),
]


def explain_rejection(problem: Problem) -> str:
    return f"(No story: the problem '{problem.id}' is not a good enough puzzle for this fable.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        print()
        for s, p in asp_valid_combos():
            print(s, p)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
            header = f"### {p.hero} & {p.friend}: {p.setting}/{p.problem}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
