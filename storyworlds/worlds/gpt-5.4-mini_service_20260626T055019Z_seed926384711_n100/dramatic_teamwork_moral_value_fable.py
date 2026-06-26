#!/usr/bin/env python3
"""
storyworlds/worlds/dramatic_teamwork_moral_value_fable.py
==========================================================

A small fable-style story world about dramatic teamwork and moral value.

Premise:
A small animal tries to move something heavy through a risky place, discovers
that pride makes the task harder, and learns that asking for help turns a hard
moment into a shared success.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- eager import of shared results containers
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    helper: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"hare", "rabbit", "fox", "wolf", "bird", "crow"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    obstacle: str
    affordance: str


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    struggle: str
    risk: str
    weight: str
    moral: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    type: str
    burden: str
    pride_trigger: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Ally:
    id: str
    label: str
    offer: str
    action: str
    finish: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about dramatic teamwork and moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--cargo", choices=CARGOS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--ally", choices=ALLIES)
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


SETTINGS = {
    "meadow": Setting(place="the meadow", obstacle="a narrow creek", affordance="cross"),
    "hill": Setting(place="the hill", obstacle="a steep slope", affordance="pull"),
    "orchard": Setting(place="the orchard", obstacle="a muddy path", affordance="carry"),
}

TASKS = {
    "carry_grain": Task(
        id="carry_grain",
        verb="carry the grain home",
        gerund="carrying grain home",
        struggle="the sack slipped and wobbled",
        risk="the grain might spill",
        weight="heavy",
        moral="teamwork makes a hard job gentle",
        keyword="grain",
        tags={"grain", "heavy"},
    ),
    "pull_cart": Task(
        id="pull_cart",
        verb="pull the cart across the hill",
        gerund="pulling the cart uphill",
        struggle="the wheels sank in the mud",
        risk="the cart might get stuck",
        weight="heavy",
        moral="many paws can move one load",
        keyword="cart",
        tags={"cart", "mud"},
    ),
    "rescue_basket": Task(
        id="rescue_basket",
        verb="rescue the basket from the creek",
        gerund="rescuing a basket",
        struggle="the basket was drifting away",
        risk="the basket might float off",
        weight="light",
        moral="a friend can reach what one paw cannot",
        keyword="basket",
        tags={"basket", "water"},
    ),
}

CARGOS = {
    "grain": Cargo(id="grain", label="grain sack", phrase="a sack of golden grain", type="sack", burden="heavy", pride_trigger="carry it alone", tags={"grain"}),
    "apples": Cargo(id="apples", label="apple basket", phrase="a basket of red apples", type="basket", burden="heavy", pride_trigger="do it by oneself", tags={"basket"}),
    "bundle": Cargo(id="bundle", label="bundle", phrase="a tied bundle of reeds", type="bundle", burden="light", pride_trigger="go without help", tags={"water"}),
}

HEROES = {
    "hare": {"type": "hare", "label": "little hare", "traits": {"quick", "proud", "brave"}},
    "mouse": {"type": "mouse", "label": "small mouse", "traits": {"busy", "careful", "proud"}},
    "squirrel": {"type": "squirrel", "label": "young squirrel", "traits": {"nimble", "eager", "proud"}},
}

ALLIES = {
    "ant": Ally(id="ant", label="an ant", offer="I can help lift", action="braced at one side", finish="Soon the load moved as if it had grown wings.", tags={"teamwork"}),
    "bird": Ally(id="bird", label="a bird", offer="I can guide the way", action="flew ahead and called back", finish="Together, they reached the other side in a neat little line.", tags={"teamwork"}),
    "beaver": Ally(id="beaver", label="a beaver", offer="I can push", action="nudged from behind", finish="The job became steady, slow, and safe.", tags={"teamwork"}),
}

CURATED = [
    ("meadow", "rescue_basket", "bundle", "hare", "bird"),
    ("hill", "pull_cart", "grain", "mouse", "ant"),
    ("orchard", "carry_grain", "apples", "squirrel", "beaver"),
]


@dataclass
class StoryParams:
    place: str
    task: str
    cargo: str
    hero: str
    ally: str
    name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, s in SETTINGS.items():
        for task_id, task in TASKS.items():
            if place == "meadow" and task_id == "rescue_basket":
                combos.append((place, task_id, "bundle"))
            if place == "hill" and task_id == "pull_cart":
                combos.append((place, task_id, "grain"))
            if place == "orchard" and task_id == "carry_grain":
                combos.append((place, task_id, "apples"))
    return combos


def explain_invalid(place: str, task: str, cargo: str) -> str:
    return f"(No story: {task} with {cargo} does not fit the setting at {place}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.task and args.cargo:
        if (args.place, args.task, args.cargo) not in valid_combos():
            raise StoryError(explain_invalid(args.place, args.task, args.cargo))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.cargo is None or c[2] == args.cargo)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, cargo = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(list(HEROES))
    ally = args.ally or rng.choice(list(ALLIES))
    name = args.name or rng.choice(["Pip", "Tara", "Milo", "Nia", "Roo"])
    return StoryParams(place=place, task=task, cargo=cargo, hero=hero, ally=ally, name=name)


def _do_task(world: World, hero: Entity, task: Task, cargo: Entity) -> None:
    hero.meters["effort"] = hero.meters.get("effort", 0) + 1
    if task.id == "carry_grain":
        cargo.meters["spill"] = cargo.meters.get("spill", 0) + 1
    elif task.id == "pull_cart":
        cargo.meters["stuck"] = cargo.meters.get("stuck", 0) + 1
    elif task.id == "rescue_basket":
        cargo.meters["drift"] = cargo.meters.get("drift", 0) + 1


def predict_failure(world: World, hero: Entity, task: Task, cargo: Entity) -> bool:
    sim = world.copy()
    _do_task(sim, sim.get(hero.id), task, sim.get(cargo.id))
    return sim.get(cargo.id).meters.get("spill", 0) >= THRESHOLD or sim.get(cargo.id).meters.get("stuck", 0) >= THRESHOLD or sim.get(cargo.id).meters.get("drift", 0) >= THRESHOLD


def tell(setting: Setting, task: Task, cargo_cfg: Cargo, hero_key: str, ally_key: str, name: str) -> World:
    world = World(setting)
    hero_meta = HEROES[hero_key]
    hero = world.add(Entity(id=name, kind="character", type=hero_meta["type"], label=hero_meta["label"], traits=sorted(hero_meta["traits"])))
    ally_cfg = ALLIES[ally_key]
    ally = world.add(Entity(id="Ally", kind="character", type=ally_cfg.id, label=ally_cfg.label, traits=["helpful"]))
    cargo = world.add(Entity(id="cargo", type=cargo_cfg.type, label=cargo_cfg.label, phrase=cargo_cfg.phrase))
    world.facts.update(hero=hero, ally=ally, cargo=cargo, setting=setting, task=task, cargo_cfg=cargo_cfg)
    world.say(f"{hero.label.capitalize()} lived by {setting.place} and liked to solve problems fast.")
    world.say(f"{name} wanted to {task.verb}, because {cargo_cfg.phrase} was waiting to be moved.")
    world.para()
    world.say(f"But at {setting.place}, there was {setting.obstacle}, and {task.struggle}.")
    if predict_failure(world, hero, task, cargo):
        world.say(f"{name} frowned. {task.risk.capitalize()}, and that felt dramatic.")
    world.para()
    world.say(f"Then {ally_cfg.label} arrived and said, “{ally_cfg.offer}.”")
    world.say(f"{name} stopped trying to do it alone and let {ally_cfg.label} {ally_cfg.action}.")
    _do_task(world, hero, task, cargo)
    cargo.helper = ally.id
    hero.memes["pride"] = 0
    hero.memes["joy"] = 1
    world.say(f"With both of them working together, the hard job turned smooth.")
    world.say(f"{ally_cfg.finish} {name} smiled, and the cargo was safe at last.")
    world.para()
    world.say(f"The little moral was clear: {task.moral}.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    cargo = f["cargo_cfg"]
    return [
        f'Write a short fable for a child about {hero.label} who tries to {task.verb} and learns that help matters.',
        f'Tell a gentle dramatic story where a small animal faces {f["setting"].obstacle} while moving {cargo.phrase}.',
        f'Write a moral tale about teamwork, where a brave little character stops trying to {cargo.pride_trigger} and accepts help.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, ally, task, cargo = f["hero"], f["ally"], f["task"], f["cargo_cfg"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {f['setting'].place}?",
            answer=f"{hero.id} wanted to {task.verb}, but it was hard to do alone.",
        ),
        QAItem(
            question=f"Why did {hero.id} need help with the {cargo.label}?",
            answer=f"The {cargo.label} was too hard to move safely by one little animal, so teamwork was the better choice.",
        ),
        QAItem(
            question=f"Who helped {hero.id} in the middle of the story?",
            answer=f"{ally.label} helped by working beside {hero.id}, and that changed the whole task.",
        ),
        QAItem(
            question="What was the moral of the fable?",
            answer=f"The moral was that {task.moral}.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "teamwork": [("What is teamwork?", "Teamwork means people or animals work together to do a job that is hard for one alone.")],
    "moral": [("What is a moral in a fable?", "A moral is the lesson the story wants you to remember.")],
    "heavy": [("What makes something heavy?", "Something heavy is hard to lift or carry because it has a lot of weight.")],
    "water": [("Why can a creek be tricky to cross?", "Water can move fast, make the ground slippery, and carry things away.")],
    "grain": [("What is grain?", "Grain is small seeds like wheat or corn that animals and people can eat.")],
    "basket": [("What is a basket used for?", "A basket is a container with sides, often used to carry fruit or other things.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["task"].tags) | {"teamwork", "moral"}
    out: list[QAItem] = []
    for tag in ["teamwork", "moral", "heavy", "water", "grain", "basket"]:
        if tag in tags and tag in WORLD_KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[tag])
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
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Task, Cargo) :- place(Place), task(Task), cargo(Cargo), compatible(Place, Task, Cargo).
resolved(Task) :- valid(_, Task, _).
teamwork(Task) :- valid(_, Task, _).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for t in TASKS:
        lines.append(asp.fact("task", t))
    for c in CARGOS:
        lines.append(asp.fact("cargo", c))
    for place, task, cargo in valid_combos():
        lines.append(asp.fact("compatible", place, task, cargo))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TASKS[params.task], CARGOS[params.cargo], params.hero, params.ally, params.name)
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


def resolve_gendered_random(rng: random.Random, hero: str) -> str:
    return rng.choice(["Pip", "Milo", "Nia", "Tara", "Roo"])


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        for place, task, cargo in CURATED:
            p = StoryParams(place=place, task=task, cargo=cargo, hero="hare", ally="bird", name="Pip", seed=base_seed)
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
