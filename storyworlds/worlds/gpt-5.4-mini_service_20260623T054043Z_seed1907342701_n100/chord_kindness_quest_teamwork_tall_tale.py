#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/chord_kindness_quest_teamwork_tall_tale.py
===============================================================================================================

A standalone storyworld for a tall-tale quest about a broken chord, kindness,
and teamwork. A small crew travels by river, repairs a bridge-harp, and uses a
shared chord to guide a homecoming song.
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
    phrase: str = ""
    role: str = ""
    plural: bool = False
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    id: str
    place: str
    water: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    noun: str
    source: str
    risk: str
    wound: str
    zone: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    action: str
    fix: str
    cover: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_break(world: World) -> list[str]:
    out: list[str] = []
    tether = world.facts["problem_ent"]
    for ent in world.entities.values():
        if ent.meters["strain"] < THRESHOLD:
            continue
        sig = ("break", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["broken"] += 1
        tether.meters["hush"] += 1
        out.append("__broken__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes["kindness"] < THRESHOLD or ent.memes["teamwork"] < THRESHOLD:
            continue
        sig = ("kindness", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["hope"] += 1
        out.append("__hope__")
    return out


CAUSAL_RULES = [Rule("break", _r_break), Rule("kindness", _r_kindness)]


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
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for problem in PROBLEMS:
            for prize in PRIZES:
                if PROBLEMS[problem].zone & PRIZES[prize].tags:
                    combos.append((setting, problem, prize))
    return combos


@dataclass
class StoryParams:
    setting: str
    problem: str
    prize: str
    hero: str
    helper: str
    helper_type: str
    hero_type: str
    seed: Optional[int] = None


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.problem not in PROBLEMS or params.prize not in PRIZES:
        raise StoryError("Unknown problem or prize.")
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    prize = PRIZES[params.prize]
    if problem.zone.isdisjoint(prize.tags):
        raise StoryError("This problem does not touch that prize.")

    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper))
    bridge = world.add(Entity(id="bridge", type="thing", label="the bridge"))
    chord = world.add(Entity(id="chord", type="thing", label="the chord"))
    prize_ent = world.add(Entity(id="prize", type="thing", label=prize.label, phrase=prize.phrase, plural=prize.plural))
    problem_ent = world.add(Entity(id="problem", type="thing", label=problem.noun))
    world.facts.update(hero=hero, helper=helper, bridge=bridge, chord=chord, prize=prize_ent,
                       problem=problem, prize_cfg=prize, problem_ent=problem_ent,
                       setting=setting, repaired=False, route_open=False)
    hero.memes["kindness"] = 1
    helper.memes["teamwork"] = 1
    problem_ent.meters["strain"] = 1
    problem_ent.meters["broken"] = 0
    prize_ent.meters["dust"] = 0
    bridge.meters["sway"] = 0
    chord.meters["song"] = 0
    world.say(f"{hero.label} and {helper.label} came to {setting.place}, where {problem.source} had left {problem.risk}.")
    world.say(f"On the trail sat {prize.phrase}, waiting like treasure.")
    world.para()
    hero.memes["kindness"] += 1
    helper.memes["teamwork"] += 1
    world.say(f"{hero.label} shared a snack with {helper.label}, and {helper.label} shared a plan in return.")
    world.say(f"They tied the {problem.noun} with the {chord.label}, then lifted together, slow and steady.")
    if problem.id == "wind":
        world.say("The wind sang through the trees like a fiddle with long legs.")
    if problem.id == "river":
        bridge.meters["sway"] += 1
        world.say("Below them, the river rolled by as blue as a moving ribbon.")
    world.para()
    propagate(world, narrate=False)
    problem_ent.meters["strain"] += 1
    if problem.id == "river":
        bridge.meters["sway"] += 1
    if hero.memes["kindness"] >= THRESHOLD and helper.memes["teamwork"] >= THRESHOLD:
        problem_ent.meters["broken"] = 0
        world.facts["repaired"] = True
        world.facts["route_open"] = True
        chord.meters["song"] += 1
        prize_ent.meters["dust"] = 0
        world.say(f"With one mighty pull, the {problem.noun} held, and the {chord.label} hummed a bright note.")
        world.say(f"{hero.label} and {helper.label} laughed, because {prize.phrase} was safe and the way ahead was open.")
        world.say(f"At sunset they crossed on singing feet, and the chord still quivered like a happy bee.")
    else:
        world.facts["repaired"] = False
        world.say(f"Their first try was shaky, but they learned to pull as one.")
        world.say(f"By the second try, the {problem.noun} held, and the {chord.label} gave a proud twang.")
        world.say(f"They reached {prize.phrase} at last, just as the sky turned gold.")
        world.facts["route_open"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale adventure about kindness, teamwork, and a "{f["problem"].noun}" that includes the word "chord".',
        f"Tell a child-sized quest story where {f['hero'].label} and {f['helper'].label} solve a problem at {f['setting'].place} together.",
        f"Write a short story about two helpers who use a chord to finish a quest and protect {f['prize_cfg'].phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize = f["hero"], f["helper"], f["prize_cfg"]
    problem = f["problem"]
    qa = [
        QAItem(
            question=f"Who went on the quest at {f['setting'].place}?",
            answer=f"{hero.label} and {helper.label} went there together. They worked as a team, and that is why the quest could move forward.",
        ),
        QAItem(
            question=f"Why did they need the chord?",
            answer=f"They needed the chord to help hold the {problem.noun} steady. It gave them a safe way to share the pulling work instead of doing it alone.",
        ),
        QAItem(
            question=f"What did kindness change in the story?",
            answer=f"Kindness helped them stay patient and gentle with each other. Because they kept helping one another, the hard job turned into a success.",
        ),
    ]
    if f.get("repaired"):
        qa.append(QAItem(
            question=f"What happened to {prize.phrase} at the end?",
            answer=f"{prize.phrase} stayed safe and easy to carry home. The happy ending proves the quest worked because the problem was fixed before anything was lost.",
        ))
    else:
        qa.append(QAItem(
            question=f"How did the quest end for {hero.label} and {helper.label}?",
            answer=f"They kept trying together until the problem gave way. The ending image shows them crossing safely, with the chord still buzzing from the work they shared.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people do a job together and help each other. Each helper shares the work so the whole group can finish more easily.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and thoughtful toward someone else. Kind choices make hard moments feel easier.",
        ),
        QAItem(
            question="What is a chord?",
            answer="A chord can be a strong rope or string used to pull, tie, or hold things together. In a story like this, it can help a crew share one hard job.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a trip where someone goes to solve a problem or find something important. Quests usually have a task, a challenge, and a finished goal.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS = {
    "river": Setting(id="river", place="the river bend", water=True, affords={"bridge", "song"}),
    "hill": Setting(id="hill", place="the windy hill", affords={"bridge", "song"}),
    "harbor": Setting(id="harbor", place="the harbor road", water=True, affords={"bridge", "song"}),
}

PROBLEMS = {
    "bridge_rope": Problem(id="bridge_rope", noun="bridge rope", source="the old bridge keeper", risk="it had frayed nearly to lace", wound="snapped", zone={"bridge"}, tags={"rope", "bridge", "chord"}),
    "ferry_line": Problem(id="ferry_line", noun="ferry line", source="the ferryman", risk="it sagged in the wind", wound="slipped", zone={"bridge"}, tags={"line", "bridge", "chord"}),
    "kite_string": Problem(id="kite_string", noun="kite string", source="a sky-wee gale", risk="it tangled in the branches", wound="tied up", zone={"song"}, tags={"string", "knot", "chord"}),
}

PRIZES = {
    "lantern": Prize(id="lantern", label="lantern", phrase="a brass lantern", region="bridge", tags={"bridge", "light"}),
    "parcel": Prize(id="parcel", label="parcel", phrase="a wrapped parcel", region="bridge", tags={"bridge", "gift"}),
    "banner": Prize(id="banner", label="banner", phrase="a bright banner", region="song", tags={"song", "cloth"}),
}

NAMES = ["Mina", "Otto", "June", "Hank", "Willa", "Gus", "Poppy", "Jeb"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale quest about kindness, teamwork, and a chord.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--hero-type", choices=["girl", "boy"], default=None)
    ap.add_argument("--helper-type", choices=["girl", "boy"], default=None)
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
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, prize = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != hero])
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or ("boy" if hero_type == "girl" else "girl")
    return StoryParams(setting=setting, problem=problem, prize=prize, hero=hero, helper=helper, helper_type=helper_type, hero_type=hero_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid(S,P,R) :- setting(S), problem(P), prize(R), touches(P,R).
touches(bridge_rope, lantern).
touches(bridge_rope, parcel).
touches(ferry_line, lantern).
touches(ferry_line, parcel).
touches(kite_string, banner).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for rid in PRIZES:
        lines.append(asp.fact("prize", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    ok = True
    if python_set != clingo_set:
        ok = False
        print("MISMATCH between Python and ASP combo sets.")
        print("Python only:", sorted(python_set - clingo_set))
        print("ASP only:", sorted(clingo_set - python_set))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, prize=None, hero=None, helper=None, hero_type=None, helper_type=None), random.Random(777)))
        if not sample.story.strip():
            ok = False
            print("Smoke test failed: empty story.")
    except Exception as exc:
        ok = False
        print(f"Smoke test failed: {exc}")
    if ok:
        print(f"OK: verify passed ({len(python_set)} combos).")
        return 0
    return 1


CURATED = [
    StoryParams(setting="river", problem="bridge_rope", prize="lantern", hero="Mina", helper="Gus", helper_type="boy", hero_type="girl"),
    StoryParams(setting="hill", problem="kite_string", prize="banner", hero="Willa", helper="Otto", helper_type="boy", hero_type="girl"),
    StoryParams(setting="harbor", problem="ferry_line", prize="parcel", hero="Hank", helper="June", helper_type="girl", hero_type="boy"),
]


def asp_show() -> str:
    return asp_program("#show valid/3.")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_show())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} combos:")
        for row in combos:
            print(" ", row)
        return
    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
            s = generate(params)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, s in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
