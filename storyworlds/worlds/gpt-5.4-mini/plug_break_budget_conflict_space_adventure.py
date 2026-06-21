#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/plug_break_budget_conflict_space_adventure.py
=============================================================================

A standalone story world for a tiny space-adventure tale: a ship crew plans a
small voyage, a power plug breaks, the budget becomes a problem, conflict rises,
and a careful fix saves the trip. The world is built from state, not from a
frozen paragraph: typed entities carry physical meters and emotional memes, the
simulation drives the prose, and the ending image shows what changed.

Seed words: plug, break, budget
Style: Space Adventure
Feature: Conflict
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

CREW_ROLES = {"pilot", "engineer", "captain", "friend"}


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
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot", "engineer"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Theme:
    id: str
    scene: str
    ship: str
    goal: str
    bay: str
    ending: str

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
    phrase: str
    place: str
    breaks: bool = True

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
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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

    def crew(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]


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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    if "captain" not in world.entities or "engineer" not in world.entities:
        return out
    cap, eng = world.get("captain"), world.get("engineer")
    if cap.memes["anger"] >= THRESHOLD and eng.memes["worry"] >= THRESHOLD:
        sig = ("conflict",)
        if sig not in world.fired:
            world.fired.add(sig)
            cap.memes["conflict"] += 1
            eng.memes["conflict"] += 1
            out.append("__conflict__")
    return out


CAUSAL_RULES = [Rule("conflict", "social", _r_conflict)]


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


def risk(problem: Problem) -> bool:
    return problem.breaks


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def fixable(problem: Problem) -> bool:
    return any(risk(problem) for _ in [problem])


def severity(delay: int) -> int:
    return 1 + delay


def outcome_of(params: "StoryParams") -> str:
    if params.conflict_type == "resolved":
        return "resolved"
    return "handled" if FIXES[params.fix].power >= severity(params.delay) else "drifted"


def _do_break(world: World, item: Entity, problem: Problem, narrate: bool = True) -> None:
    item.meters["broken"] += 1
    item.meters["sparks"] += 1
    world.get("ship").meters["risk"] += 1
    if narrate:
        world.say(f"A sharp snap came from the {problem.label}, and the ship's lights flickered.")
    propagate(world, narrate=narrate)


def predict_problem(world: World, problem: Problem) -> dict:
    sim = world.copy()
    _do_break(sim, sim.get("plug"), problem, narrate=False)
    return {
        "broken": sim.get("plug").meters["broken"] >= THRESHOLD,
        "risk": sim.get("ship").meters["risk"],
    }


def setup(world: World, theme: Theme, hero: Entity, partner: Entity) -> None:
    hero.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"On a bright day in deep space, {hero.id} and {partner.id} floated through "
        f"{theme.scene}. {theme.ship}"
    )
    world.say(f'They were on the way to {theme.goal} aboard the {theme.id} explorer.')


def need_power(world: World, partner: Entity, theme: Theme, problem: Problem) -> None:
    world.say(
        f"But the engine bay near {theme.bay} was dark, and the crew needed a live plug "
        f"to keep the controls steady."
    )
    world.say(f'{partner.id} frowned. "We need power for this mission," {partner.pronoun()} said.')


def tempt(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["boldness"] += 1
    world.say(
        f'{hero.id} pointed at {problem.phrase}. "I can fix it fast," '
        f'{hero.pronoun()} said. "We do not have to miss the mission."'
    )


def warn(world: World, partner: Entity, hero: Entity, problem: Problem) -> None:
    pred = predict_problem(world, problem)
    partner.memes["worry"] += 1
    world.facts["predicted_risk"] = pred["risk"]
    world.say(
        f'{partner.id} bit {partner.pronoun("possessive")} lip. "{problem.label.capitalize()} '
        f'can break the power line, and then the ship could lose its light."'
    )


def argue(world: World, hero: Entity, partner: Entity) -> None:
    hero.memes["anger"] += 1
    partner.memes["worry"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} shook {hero.pronoun("possessive")} head, and the two of them had a '
        f"small but real conflict over what to do next."
    )


def repair(world: World, captain: Entity, fix: Fix, problem: Problem) -> None:
    world.get("plug").meters["broken"] = 0.0
    world.get("ship").meters["risk"] = 0.0
    captain.memes["relief"] += 1
    world.say(
        f"{captain.id} hurried in with a careful plan and {fix.text.replace('{problem}', problem.label)}."
    )
    world.say(
        f"The lights steadied again, and the ship hummed soft and calm."
    )


def repair_fail(world: World, captain: Entity, fix: Fix, problem: Problem) -> None:
    world.get("ship").meters["risk"] += 1
    world.get("plug").meters["broken"] += 1
    world.say(
        f"{captain.id} tried to help, but {fix.fail.replace('{problem}', problem.label)}."
    )
    world.say("The mission slowed, and the crew had to wait for a better way.")


def lesson(world: World, captain: Entity, hero: Entity, partner: Entity) -> None:
    for kid in (hero, partner):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"Then {captain.id} explained that a broken plug and a tight budget still need a safe fix."
    )
    world.say(
        f'"Next time," {captain.id} said, "we ask for help before we spend more than we should."'
    )


def ending(world: World, theme: Theme, hero: Entity, partner: Entity, fix: Fix) -> None:
    hero.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"By the time the {theme.ending} came into view, the crew had a steady plug, a calm budget, "
        f"and a ship that could go on."
    )
    world.say(
        f"{hero.id} and {partner.id} looked out at the stars, glad the mission had found its way."
    )


def tell(theme: Theme, problem: Problem, fix: Fix, captain_name: str = "Ava",
         partner_name: str = "Milo", delay: int = 0, conflict_type: str = "resolved") -> World:
    world = World()
    captain = world.add(Entity("captain", "character", "captain", captain_name))
    partner = world.add(Entity("engineer", "character", "engineer", partner_name))
    plug = world.add(Entity("plug", "thing", "plug", "power plug"))
    ship = world.add(Entity("ship", "thing", "ship", "little starship"))
    world.facts.update(theme=theme, problem=problem, fix=fix, delay=delay, conflict_type=conflict_type)

    setup(world, theme, captain, partner)
    world.para()
    need_power(world, partner, theme, problem)
    tempt(world, captain, problem)
    warn(world, partner, captain, problem)
    if conflict_type == "resolved":
        argue(world, captain, partner)
        world.para()
        repair(world, captain, fix, problem)
        lesson(world, captain, captain, partner)
        world.para()
        ending(world, theme, captain, partner, fix)
        outcome = "resolved"
    else:
        argue(world, captain, partner)
        world.para()
        repair_fail(world, captain, fix, problem)
        world.say("The crew shared the budget carefully and chose to turn back for a safer repair.")
        outcome = "handled"
    world.facts.update(outcome=outcome, plug=plug, ship=ship, captain=captain, partner=partner)
    return world


THEMES = {
    "orbit": Theme("orbit", "the glittering curve of an orbiting station", "Their starship slid past glowing panels and silver windows.", "reach the moon relay", "the side hatch", "moon relay"),
    "comet": Theme("comet", "a bright comet trail over a blue planet", "Their tiny ship zipped beside crystal ice and pale stars.", "map the comet tail", "the fuel nook", "comet tail"),
    "asteroid": Theme("asteroid", "a field of spinning pebbles and tiny sparks", "Their explorer ship hummed between rocks and dust.", "deliver supplies to the mine", "the battery bay", "asteroid mine"),
}

PROBLEMS = {
    "plug": Problem("plug", "plug", "the loose plug", "the wall socket", True),
    "cord": Problem("cord", "cord", "the sparking cord", "the control panel", True),
    "budget": Problem("budget", "budget", "the tight budget", "the supply locker", False),
}

FIXES = {
    "patch": Fix("patch", 3, 3, "patched the plug with a spare connector from the repair kit", "patched the plug with tape, but the connection still failed", "patched the plug with a spare connector"),
    "swap": Fix("swap", 2, 2, "swapped in a backup plug from the kit", "swapped in the backup plug, but the spark was already too strong", "swapped in a backup plug"),
    "call_base": Fix("call_base", 3, 4, "called the base station and borrowed a proper part", "called the base station, but the answer came too late", "called the base station for a proper part"),
    "tighten": Fix("tighten", 2, 1, "tightened the plug by hand", "tightened the plug, but it slipped again", "tightened the plug by hand"),
    "spend_less": Fix("spend_less", 1, 1, "promised to spend less and keep the broken part in a box", "counted every coin, but that did not fix the plug", "counted every coin"),
}

NAMES = ["Ava", "Milo", "Nia", "Zed", "Luna", "Kai", "Oli", "Rin", "Mira", "Tess"]


@dataclass
@dataclass
class StoryParams:
    theme: str
    problem: str
    fix: str
    captain: str
    partner: str
    delay: int = 0
    conflict_type: str = "resolved"
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for t in THEMES:
        for p in PROBLEMS:
            if p != "plug" and p != "cord":
                continue
            for f in FIXES:
                if FIXES[f].sense >= SENSE_MIN:
                    combos.append((t, p, f))
    return combos


def explain_rejection(problem: Problem) -> str:
    return f"(No story: the word '{problem.label}' is not a real technical problem here.)"


def explain_fix(fid: str) -> str:
    fx = FIXES[fid]
    return f"(Refusing fix '{fid}': it is too weak for a space repair.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world with a plug, a break, and a budget conflict.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--partner")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
    ap.add_argument("--conflict-type", choices=["resolved", "handled"], default="resolved")
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
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, problem, fix = rng.choice(sorted(combos))
    captain = args.name or rng.choice(NAMES)
    partner = args.partner or rng.choice([n for n in NAMES if n != captain])
    return StoryParams(theme, problem, fix, captain, partner, args.delay, args.conflict_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space adventure story for a young child that includes the words "plug", "break", and "budget".',
        f"Tell a story where {f['captain'].id} and {f['partner'].id} face a broken plug and a tight budget, then solve their conflict with a careful repair.",
        f"Write a gentle spaceship story with conflict, a small repair, and an ending that shows the mission can continue.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain, partner, problem, fix = f["captain"], f["partner"], f["problem"], f["fix"]
    return [
        ("Who is the story about?", f"It is about {captain.id} and {partner.id}, who are trying to keep their little ship ready for the trip."),
        ("What went wrong?", f"The {problem.label} broke, and that made the power line shaky. That is why the crew had a conflict about what to do next."),
        ("How did they fix it?", f"They used {fix.qa_text} so the ship could stay powered without wasting the budget."),
        ("How did the story end?", f"It ended with the ship steady again and the crew able to keep flying. The final scene shows the mission going on under calm stars."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a plug?", "A plug is the part that fits into a socket to carry power to a device or ship."),
        ("Why is a broken plug a problem?", "A broken plug can stop power from flowing, and then lights or machines may not work right."),
        ("What does budget mean?", "A budget is the plan for how much money you can spend, so you do not use too much."),
        ("What is a conflict?", "A conflict is when people want different things and must work through the disagreement."),
        ("Why do space crews keep backup parts?", "Backup parts help fix problems quickly when a trip is far from home."),
    ]


def asp_facts() -> str:
    import asp
    lines = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
        if PROBLEMS[pid].breaks:
            lines.append(asp.fact("breaks", pid))
    for fid, fx in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fx.sense))
        lines.append(asp.fact("power", fid, fx.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
valid(T, P, F) :- theme(T), problem(P), breaks(P), sensible(F).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos.")
    if set(asp_sensible()) != {k for k, v in FIXES.items() if v.sense >= SENSE_MIN}:
        rc = 1
        print("MISMATCH in sensible fixes.")
    try:
        sample = generate(resolve_params(argparse.Namespace(theme=None, problem=None, fix=None, name=None, partner=None, delay=0, conflict_type="resolved"), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], PROBLEMS[params.problem], FIXES[params.fix], params.captain, params.partner, params.delay, params.conflict_type)
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
        print("trace:", sample.world.facts)
    if qa:
        print()
        for item in sample.prompts:
            print(item)


CURATED = [
    StoryParams("orbit", "plug", "patch", "Ava", "Milo", 0, "resolved"),
    StoryParams("comet", "plug", "swap", "Nia", "Kai", 1, "resolved"),
    StoryParams("asteroid", "cord", "call_base", "Luna", "Zed", 0, "resolved"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
