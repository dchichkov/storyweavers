#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/principal_mutton_repetition_pirate_tale.py
==========================================================================

A standalone story world for a tiny pirate tale: a school pirate club, a stern
principal, and a pot of mutton that is supposed to feed the crew. The story is
built from world state, with a repetition beat that makes the captain keep
trying the same plan until the crew notices the problem and chooses a better
course.

Seed words and style:
- principal
- mutton
- repetition
- pirate tale
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
SENSE_MIN = 2


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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    crew_name: str
    ship_name: str
    holds: str
    deck_detail: str


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    smell: str
    dish: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    line: str
    repeat: str
    solve: str
    sense: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["repeat"] < 2 * THRESHOLD:
            continue
        sig = ("repeat", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["stuck"] += 1
        if "deck" in world.entities:
            world.get("deck").meters["confusion"] += 1
        out.append("__repeat__")
    return out


def _r_hunger(world: World) -> list[str]:
    out: list[str] = []
    stew = world.entities.get("mutton")
    if not stew or stew.meters["spoiled"] < THRESHOLD:
        return out
    for ent in world.characters():
        if ent.memes["hunger"] < THRESHOLD:
            continue
        sig = ("hunger", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["disappointment"] += 1
        out.append("__hunger__")
    return out


CAUSAL_RULES = [Rule("repetition", "social", _r_repetition), Rule("hunger", "physical", _r_hunger)]


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


def plan_unsafe(plan: Plan, food: Food) -> bool:
    return plan.id == "same_song" and food.id == "mutton"


def sensible_plans() -> list[Plan]:
    return [p for p in PLANS.values() if p.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid, plan in PLANS.items():
            for fid, food in FOODS.items():
                if plan_unsafe(plan, food):
                    combos.append((sid, pid, fid))
    return combos


def _do_bad_plan(world: World, plan: Plan, food: Food) -> None:
    captain = world.get("captain")
    captain.memes["repeat"] += 1
    food.meters["served"] += 1
    if food.id == "mutton":
        food.meters["spoiled"] += 1
    propagate(world, narrate=False)


def setup(world: World, captain: Entity, mate: Entity, setting: Setting, food: Food) -> None:
    captain.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"On the {setting.place}, the pirate crew gathered aboard the {setting.ship_name}. "
        f"{setting.deck_detail} and the {setting.holds} smelled of salt and boards."
    )
    world.say(
        f"{captain.id} was the captain, and {mate.id} kept the lookout. "
        f"That day, they had a pot of {food.label} waiting for the crew."
    )


def warn(world: World, principal: Entity, captain: Entity, food: Food, plan: Plan) -> None:
    principal.memes["worry"] += 1
    world.say(
        f'{principal.id} tapped the rail and said, "Captain, that plan again? '
        f"{plan.repeat} {plan.repeat} {plan.repeat}. The {food.label} will grow cold.""
    )


def repeat_attempt(world: World, captain: Entity, plan: Plan, food: Food) -> None:
    captain.memes["stubborn"] += 1
    world.say(
        f"{captain.id} took a breath and tried the same tune again: "
        f'"{plan.line}" {plan.line} {plan.line}.'
    )
    world.say(
        f"The crew hummed, then frowned, because {food.smell} from the {food.label} "
        f"kept fading into a stale smell."
    )


def choose_change(world: World, mate: Entity, plan: Plan, food: Food) -> None:
    mate.memes["courage"] += 1
    world.say(
        f"{mate.id} pointed at the pot and said, "
        f'"Let us stop the chant, save the {food.label}, and do {plan.solve} instead."'
    )


def serve_fix(world: World, principal: Entity, plan: Plan, food: Food) -> None:
    food.meters["served"] = 0
    food.meters["spoiled"] = 0
    principal.memes["pride"] += 1
    world.say(
        f"The principal smiled and helped with the new plan. Soon the crew was "
        f"serving the {food.label} the proper way, and the deck smelled rich and warm."
    )
    world.say(
        f"{plan.solve.capitalize()}, and the pirates ate with wide eyes while the wind "
        f"bounced softly against the sails."
    )


def tell(setting: Setting, food: Food, plan: Plan,
         captain_name: str = "Captain Finn", mate_name: str = "Mara",
         principal_name: str = "Principal Penny") -> World:
    world = World(setting)
    captain = world.add(Entity(id=captain_name, kind="character", type="boy", role="captain"))
    mate = world.add(Entity(id=mate_name, kind="character", type="girl", role="mate"))
    principal = world.add(Entity(id=principal_name, kind="character", type="woman", role="principal"))
    world.add(Entity(id="deck", type="deck", label="the deck"))
    world.add(Entity(id="mutton", type="food", label=food.label))
    setup(world, captain, mate, setting, food)
    world.para()
    warn(world, principal, captain, food, plan)
    repeat_attempt(world, captain, plan, food)
    choose_change(world, mate, plan, food)
    world.para()
    _do_bad_plan(world, plan, food)
    serve_fix(world, principal, plan, food)
    world.facts.update(
        captain=captain, mate=mate, principal=principal, setting=setting, food=food, plan=plan,
        repeat=True, fixed=True
    )
    return world


SETTINGS = {
    "harbor_school": Setting(
        "harbor_school", "the harbor school dock", "school pirates", "Merry Gull",
        "the galley held a bright kettle", "The deck was painted blue and white"
    ),
    "island_cove": Setting(
        "island_cove", "the island cove", "sand-skip pirates", "Pebble Star",
        "the galley held a round stove", "The deck was scattered with shells"
    ),
    "river_ship": Setting(
        "river_ship", "the river quay", "river pirates", "Ruffled Tide",
        "the galley held a copper pot", "The deck shone with lantern light"
    ),
}

FOODS = {
    "mutton": Food("mutton", "mutton", "a steaming bowl of mutton", "rich mutton smell", "mutton", {"food"}),
    "stew": Food("stew", "stew", "a warm bowl of stew", "savory stew smell", "stew", {"food"}),
}

PLANS = {
    "same_song": Plan("same_song", "Sing the same pirate song", "the same song, the same song, the same song", "slice the bread and serve in turns", 1, {"repeat", "song"}),
    "bell_call": Plan("bell_call", "Ring the bell for each pirate", "the bell, the bell, the bell", "pass the plates in a circle", 3, {"repeat", "bell"}),
    "count_steps": Plan("count_steps", "Count the steps to the galley", "one step, two step, three step", "open the hatch and carry the bowls together", 2, {"repeat", "count"}),
}

GIRL_NAMES = ["Mara", "Pia", "Luna", "Nell"]
BOY_NAMES = ["Finn", "Jory", "Ari", "Bram"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a young child that includes the word "{f["principal"].id}".',
        f"Tell a story where {f['captain'].id} keeps repeating the same pirate plan, but {f['mate'].id} notices the problem and {f['principal'].id} helps fix it.",
        f'Write a rhythmic story with repetition, mutton, and a principal who guides the pirates to a better way.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    cap, mate, principal, food, plan = f["captain"], f["mate"], f["principal"], f["food"], f["plan"]
    return [
        ("Who are the main people in the story?",
         f"It is about {cap.id}, {mate.id}, and {principal.id}. The captain keeps repeating a plan, the mate notices, and the principal helps steer things right."),
        ("What food did the pirates have?",
         f"They had {food.phrase}. It was important because the crew meant to share it, so wasting it would spoil the meal."),
        ("What did the captain keep repeating?",
         f"{cap.id} kept repeating {plan.repeat}. The repetition made the crew notice that the plan was not helping the mutton get served well."),
        ("How was the problem fixed?",
         f"{mate.id} suggested {plan.solve}, and the principal helped with that better plan. The repeated chant stopped, and the food was served the proper way."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a principal?",
         "A principal is the grown-up in charge of a school. A principal helps keep everyone safe and on track."),
        ("What is mutton?",
         "Mutton is meat from a sheep. People can cook it into a warm meal like a stew or roast."),
        ("What is repetition?",
         "Repetition means saying or doing the same thing again and again. In stories, repetition can make a pattern easy to notice."),
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
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("harbor_school", "mutton", "same_song", seed=1),
    StoryParams("island_cove", "mutton", "bell_call", seed=2),
    StoryParams("river_ship", "mutton", "count_steps", seed=3),
]


def explain_rejection(plan: Plan, food: Food) -> str:
    if not plan_unsafe(plan, food):
        return "(No story: the plan does not create a meaningful repetition problem for the mutton.)"
    return ""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for fid in FOODS:
        lines.append(asp.fact("food", fid))
    for pid, p in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("sense", pid, p.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
unsafe(P, F) :- plan(P), food(F), P = same_song, F = mutton.
sensible(P) :- plan(P), sense(P, S), sense_min(M), S >= M.
valid(S, P, F) :- setting(S), plan(P), food(F), unsafe(P, F).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        print(f"FAIL: generate() smoke test crashed: {exc}")
        rc = 1
    return rc


@dataclass
class StoryParams:
    setting: str
    food: str
    plan: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with repetition, principal, and mutton.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--plan", choices=PLANS)
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
    if args.plan and args.food and not plan_unsafe(PLANS[args.plan], FOODS[args.food]):
        raise StoryError(explain_rejection(PLANS[args.plan], FOODS[args.food]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.plan is None or c[1] == args.plan)
              and (args.food is None or c[2] == args.food)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, plan, food = rng.choice(sorted(combos))
    return StoryParams(setting, food, plan)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], FOODS[params.food], PLANS[params.plan])
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, p, f in combos:
            print(f"  {s:16} {p:10} {f}")
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
            header = f"### {p.setting} / {p.plan} / {p.food}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
