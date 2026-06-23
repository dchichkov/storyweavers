#!/usr/bin/env python3
"""
storyworlds/worlds/dummy_cautionary_repetition_superhero_story.py
===============================================================

A small superhero story world about a brave kid hero, a practice dummy, and a
cautionary lesson about repeating a stunt too many times.

The seed tale behind this world:
---
A young superhero wants to show off a flying punch. At first, the practice dummy
holds steady. The hero tries the same move again and again, but each repeat makes
the dummy wobble closer to a window, then a lamp, then a stack of blocks. A
careful sidekick warns that repeated hits can push a harmless practice into a
real mess. The hero stops, changes the setup, and uses a safer training plan.
---

The world model tracks physical meters and emotional memes, then renders a story
from the changing state. Repetition is the core tension: the same move is tried
more than once, but the result changes because the dummy, room, and caution all
shift over time.
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
from typing import Optional

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
    owner: str = ""
    region: str = ""
    tags: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character" and self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    danger_spots: list[str]
    afford: str


@dataclass
class Move:
    id: str
    name: str
    repeat_line: str
    risk: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class DummyConfig:
    id: str
    label: str
    phrase: str
    type: str = "thing"
    tags: set[str] = field(default_factory=set)


@dataclass
class SafetyPlan:
    id: str
    label: str
    phrase: str
    action: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    move: str
    dummy: str
    plan: str
    hero_name: str
    hero_type: str
    sidekick_name: str
    sidekick_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "rooftop": Setting(place="the rooftop training pad", danger_spots=["edge", "dish"], afford="fly"),
    "alley": Setting(place="the alley gym", danger_spots=["trash can", "window"], afford="punch"),
    "lab": Setting(place="the bright lab room", danger_spots=["glass shelf", "lamp"], afford="kick"),
}

MOVES = {
    "punch": Move("punch", "flying punch", "Do it again!", "wobble", "rocked", {"repeat", "combat"}),
    "kick": Move("kick", "spinning kick", "Try it once more!", "slide", "shook", {"repeat", "combat"}),
    "fly": Move("fly", "sky loop", "One more loop!", "drift", "tilted", {"repeat", "flight"}),
}

DUMMIES = {
    "bag": DummyConfig("bag", "practice dummy", "a hanging practice dummy"),
    "bot": DummyConfig("bot", "training bot", "a round training bot"),
}

SAFETY = {
    "reset": SafetyPlan("reset", "reset the setup", "move the dummy back to the center", "reset the setup"),
    "slow": SafetyPlan("slow", "slow down the drills", "take a breath between tries", "slow down the drills"),
    "mark": SafetyPlan("mark", "mark a safe circle", "draw a safe circle on the floor", "mark a safe circle"),
}

HERO_NAMES = ["Nova", "Mina", "Rex", "Ivy", "Luca", "Zuri"]
SIDEKICK_NAMES = ["Pip", "Tess", "Jules", "Bea", "Milo", "Kai"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting, s in SETTINGS.items():
        for move, m in MOVES.items():
            for dummy, d in DUMMIES.items():
                if setting == "rooftop" and move == "punch":
                    combos.append((setting, move, dummy))
                elif setting == "alley" and move == "kick":
                    combos.append((setting, move, dummy))
                elif setting == "lab" and move == "fly":
                    combos.append((setting, move, dummy))
    return combos


def explain_rejection(setting: str, move: str, dummy: str) -> str:
    return f"(No story: {move} does not fit {setting} with {dummy}; choose one of the valid training setups.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero cautionary repetition story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--dummy", choices=DUMMIES)
    ap.add_argument("--plan", choices=SAFETY)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--sidekick-name")
    ap.add_argument("--sidekick-type", choices=["girl", "boy"])
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
              and (args.move is None or c[1] == args.move)
              and (args.dummy is None or c[2] == args.dummy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, move, dummy = rng.choice(sorted(combos))
    plan = args.plan or rng.choice(sorted(SAFETY))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    sidekick_type = args.sidekick_type or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    sidekick_name = args.sidekick_name or rng.choice([n for n in SIDEKICK_NAMES if n != hero_name])
    return StoryParams(setting=setting, move=move, dummy=dummy, plan=plan,
                       hero_name=hero_name, hero_type=hero_type,
                       sidekick_name=sidekick_name, sidekick_type=sidekick_type)


def _build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS or params.move not in MOVES or params.dummy not in DUMMIES or params.plan not in SAFETY:
        raise StoryError("Invalid story parameters.")
    if (params.setting, params.move, params.dummy) not in valid_combos():
        raise StoryError(explain_rejection(params.setting, params.move, params.dummy))
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    sidekick = world.add(Entity(id="sidekick", kind="character", type=params.sidekick_type, label=params.sidekick_name))
    dummy_cfg = DUMMIES[params.dummy]
    dummy = world.add(Entity(id="dummy", type=dummy_cfg.type, label=dummy_cfg.label, phrase=dummy_cfg.phrase, tags=set(dummy_cfg.tags)))
    plan = world.add(Entity(id="plan", type="plan", label=SAFETY[params.plan].label, phrase=SAFETY[params.plan].phrase))
    world.facts.update(hero=hero, sidekick=sidekick, dummy=dummy, plan=plan, move=MOVES[params.move], setting=SETTINGS[params.setting])
    return world


def _apply_move(world: World, hero: Entity, sidekick: Entity, dummy: Entity, move: Move, plan: SafetyPlan) -> None:
    hero.memes["bold"] += 1
    hero.memes["joy"] += 1
    dummy.meters["wobble"] += 1
    world.say(f"{hero.label} and {sidekick.label} trained at {world.setting.place}.")
    world.say(f"{hero.label} practiced a {move.name}, and the {dummy.label} held steady at first.")
    if move.id == "punch":
        dummy.meters["wobble"] += 1
        dummy.meters["shift"] += 1
        world.say(f"Then {hero.label} did it again. {move.repeat_line}")
        world.say(f"The {dummy.label} {move.effect} toward the {world.setting.danger_spots[0]}.")
    else:
        dummy.meters["tilt"] += 1
        world.say(f"Then {hero.label} repeated it. {move.repeat_line}")
        world.say(f"The {dummy.label} {move.effect} closer to the {world.setting.danger_spots[0]}.")
    sidekick.memes["caution"] += 1
    if dummy.meters["wobble"] >= 2:
        sidekick.memes["fear"] += 1
        world.say(f"{sidekick.label} pointed at the {world.setting.danger_spots[0]} and warned, 'Too many repeats can turn a practice move into a real mess.'")
    world.say(f"Together they chose to {plan.action}.")


def tell(params: StoryParams) -> World:
    world = _build_world(params)
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    dummy = world.get("dummy")
    move = world.facts["move"]
    plan = SAFETY[params.plan]
    world.say(f"{hero.label} was a young superhero who loved training on {world.setting.place}.")
    world.say(f"{sidekick.label} stayed close because even heroes need a careful friend.")
    world.para()
    _apply_move(world, hero, sidekick, dummy, move, plan)
    world.para()
    hero.memes["pride"] += 1
    hero.memes["care"] += 1
    dummy.meters["centered"] += 1
    world.say(f"{hero.label} stopped repeating the stunt and moved the {dummy.label} back to the center.")
    world.say(f"After that, the training felt safer: one move, one pause, then another try only when the room was ready.")
    world.say(f"At the end, the {dummy.label} stood straight, the window stayed clear, and the hero learned that careful repetition is better than wild bravado.")
    world.facts.update(outcome="safe", repeated=True, warned=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    move = f["move"]
    return [
        f"Write a superhero story for a young child about {hero.label} repeating a {move.name} too many times and learning to slow down.",
        f"Tell a cautionary story where {sidekick.label} warns that repeating the same stunt can push a practice dummy too close to trouble.",
        f"Write a short superhero tale that includes the word 'dummy' and ends with a safer training plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    dummy = world.facts["dummy"]
    move = world.facts["move"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Why did {sidekick.label} warn {hero.label} during training?",
            answer=f"{sidekick.label} warned {hero.label} because repeating the {move.name} pushed the dummy closer to trouble. The practice was still safe at first, but doing the same move again made the room less safe."
        ),
        QAItem(
            question=f"What happened to the dummy when {hero.label} did the move again?",
            answer=f"The dummy wobbled and shifted closer to the danger spots in {place}. That change showed why the sidekick wanted the hero to slow down."
        ),
        QAItem(
            question=f"How did the story end for {hero.label} and the dummy?",
            answer=f"They moved the dummy back to the center and changed the plan. The ending is calm because the hero stopped repeating the stunt and chose a safer way to train."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a practice dummy?", "A practice dummy is a training stand-in used to learn moves safely. It lets heroes practice without hurting a real person."),
        QAItem("Why can repeating a stunt be risky?", "Repeating a stunt can change the setup little by little. If the space shifts toward something fragile, the same move can become dangerous."),
        QAItem("What should a careful hero do before trying again?", "A careful hero should pause, check the space, and make sure the area is safe. Then the hero can try again without causing a mess."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:7} ({e.type:7}) meters={dict(meters)} memes={dict(memes)}")
    lines.append(f"  facts: {sorted(world.facts)}")
    return "\n".join(lines)


def valid_stories() -> list[StoryParams]:
    return [
        StoryParams(setting="rooftop", move="punch", dummy="bag", plan="reset", hero_name="Nova", hero_type="girl", sidekick_name="Pip", sidekick_type="boy"),
        StoryParams(setting="alley", move="kick", dummy="bot", plan="slow", hero_name="Rex", hero_type="boy", sidekick_name="Tess", sidekick_type="girl"),
        StoryParams(setting="lab", move="fly", dummy="bag", plan="mark", hero_name="Ivy", hero_type="girl", sidekick_name="Kai", sidekick_type="boy"),
    ]


CURATED = valid_stories()


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MOVES:
        lines.append(asp.fact("move", m))
    for d in DUMMIES:
        lines.append(asp.fact("dummy", d))
    for p in SAFETY:
        lines.append(asp.fact("plan", p))
    lines.append(asp.fact("fits", "rooftop", "punch"))
    lines.append(asp.fact("fits", "alley", "kick"))
    lines.append(asp.fact("fits", "lab", "fly"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M, D) :- fits(S, M), setting(S), move(M), dummy(D).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP valid combos differ from Python.")
        ok = False
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, move=None, dummy=None, plan=None, hero_name=None, hero_type=None, sidekick_name=None, sidekick_type=None), random.Random(0)))
        if not sample.story.strip():
            print("MISMATCH: empty story.")
            ok = False
    except Exception as e:
        print(f"MISMATCH: generation crashed: {e}")
        ok = False
    parser = build_parser()
    for seed in (1, 7, 777):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            sample = generate(params)
            if not sample.story.strip():
                raise RuntimeError("empty story")
        except Exception as e:
            print(f"MISMATCH: seed {seed} failed: {e}")
            ok = False
    try:
        samples = []
        for s in range(3):
            params = resolve_params(parser.parse_args(["-n", "3", "--seed", "777"]), random.Random(777 + s))
            samples.append(generate(params))
        if len({x.story for x in samples}) < 1:
            ok = False
    except Exception as e:
        print(f"MISMATCH: qa smoke test failed: {e}")
        ok = False
    try:
        out = generate(resolve_params(parser.parse_args([]), random.Random(42)))
        _ = out.to_json()
    except Exception as e:
        print(f"MISMATCH: json smoke test failed: {e}")
        ok = False
    try:
        for p in CURATED:
            emit(generate(p), qa=True)
    except Exception as e:
        print(f"MISMATCH: emit smoke test failed: {e}")
        ok = False
    print("OK" if ok else "FAILED")
    return 0 if ok else 1


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.move} in {p.setting}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
