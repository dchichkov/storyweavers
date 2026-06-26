#!/usr/bin/env python3
"""
storyworlds/worlds/arc_teamwork_animal_story.py
===============================================

A small animal-teamwork story world about a few friends who need to work
together to cross an arc-shaped bridge and solve a simple problem.

Seed tale premise:
- An animal friend wants to reach something across a little stream.
- The old branch bridge bends into an arc and makes the path feel risky.
- The friends use teamwork to steady the bridge and carry the prize safely.

The world supports a single classical TinyStories-style arc:
beginning -> problem -> teamwork turn -> resolution image.
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
    species: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.species in {"fox", "rabbit", "bear", "mouse", "hedgehog", "badger"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little stream"
    features: set[str] = field(default_factory=lambda: {"stream", "arc", "bridge"})


@dataclass
class Task:
    id: str
    goal: str
    verb: str
    danger: str
    resolve: str
    tag: str


@dataclass
class Prize:
    label: str
    phrase: str
    carried_state: str
    reward: str


@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    hero: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _r_arc_lean(world: World) -> list[str]:
    out = []
    bridge = world.entities.get("bridge")
    if not bridge:
        return out
    if bridge.meters.get("lean", 0.0) < THRESHOLD:
        return out
    sig = ("arc", "lean")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bridge.meters["wobble"] = bridge.meters.get("wobble", 0.0) + 1
    out.append("The bridge bent a little more in the middle.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out = []
    bridge = world.entities.get("bridge")
    if not bridge:
        return out
    helpers = [e for e in world.entities.values() if e.kind == "character" and e.memes.get("helping", 0.0) >= THRESHOLD]
    if len(helpers) < 2:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bridge.meters["steady"] = 1.0
    out.append("With everyone holding on, the bridge stayed steady.")
    return out


CAUSAL_RULES = [_r_arc_lean, _r_teamwork]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(task: Task, prize: Prize) -> bool:
    return task.id in {"cross", "carry", "rescue"} and prize.label in {"basket", "seed bag", "lantern"}


SETTING = Setting()
TASKS = {
    "cross": Task(
        id="cross",
        goal="cross the arc-shaped bridge",
        verb="cross the bridge",
        danger="might slip into the stream",
        resolve="hold the bridge steady together",
        tag="arc",
    ),
    "carry": Task(
        id="carry",
        goal="carry the basket across",
        verb="carry the basket",
        danger="might drop the berries",
        resolve="share the load and walk carefully",
        tag="teamwork",
    ),
    "rescue": Task(
        id="rescue",
        goal="rescue the lost chick on the far bank",
        verb="reach the far bank",
        danger="might not make it over the bend",
        resolve="make a safe path together",
        tag="animal",
    ),
}
PRIZES = {
    "basket": Prize("basket", "a berry basket", "held", "the berries stayed safe"),
    "seed bag": Prize("seed bag", "a tiny seed bag", "held", "the seeds stayed dry"),
    "lantern": Prize("lantern", "a little lantern", "carried", "the lantern did not tip"),
}
ANIMALS = {
    "Pip": ("mouse", "small"),
    "Nia": ("rabbit", "bright"),
    "Tuck": ("badger", "steady"),
    "Moss": ("fox", "quick"),
    "Bram": ("hedgehog", "kind"),
    "Dot": ("squirrel", "nimble"),
}
NAMES = list(ANIMALS)


def build_story_world(params: StoryParams) -> World:
    if params.task not in TASKS or params.prize not in PRIZES:
        raise StoryError("Unknown task or prize.")
    task = TASKS[params.task]
    prize = PRIZES[params.prize]
    if not reasonableness_gate(task, prize):
        raise StoryError("This prize and task do not make a believable teamwork story.")

    hero_species, hero_trait = ANIMALS[params.hero]
    helper_species, helper_trait = ANIMALS[params.helper]
    world = World(SETTING)

    hero = world.add(Entity(id=params.hero, kind="character", species=hero_species, label=params.hero))
    helper = world.add(Entity(id=params.helper, kind="character", species=helper_species, label=params.helper))
    bridge = world.add(Entity(id="bridge", species="branch bridge", label="arc-shaped bridge", phrase="an old branch bridge", meters={"lean": 0.0, "steady": 0.0}))
    item = world.add(Entity(id="prize", species=prize.label, label=prize.label, phrase=prize.phrase, owner=hero.id, carried_by=hero.id))
    world.facts.update(hero=hero, helper=helper, bridge=bridge, prize=item, task=task, prize_def=prize)

    world.say(f"{hero.id} was a {hero_trait} {hero.species} who loved to help friends.")
    world.say(f"{helper.id} was a {helper_trait} {helper.species}, and {helper.id} was good at teamwork.")
    world.say(f"One morning, {hero.id} found {prize.phrase} on the far side of {SETTING.place}.")
    world.para()
    world.say(f"The only way across was {bridge.phrase}, a bridge that curved like an arc over the water.")
    world.say(f"{hero.id} wanted to {task.verb}, but the bridge looked a little shaky and {task.danger}.")
    world.say(f'"We can do it together," said {helper.id}.')
    world.para()
    hero.memes["worry"] = 1.0
    helper.memes["helping"] = 1.0
    bridge.meters["lean"] = 1.0
    propagate(world, narrate=True)
    world.say(f"{hero.id} took one step, and {helper.id} took the other side of the load.")
    hero.memes["courage"] = 1.0
    helper.memes["helping"] = 2.0
    item.carried_by = hero.id
    item.meters["safe"] = 1.0
    propagate(world, narrate=True)
    world.para()
    world.say(f"In the end, {hero.id} and {helper.id} crossed the arc-shaped bridge, and {prize.reward}.")
    world.say(f"{hero.id} smiled at the little stream below, because teamwork had made the hard path easy.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task: Task = f["task"]
    prize: Prize = f["prize_def"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    return [
        f'Write a short animal story about teamwork and an "{task.tag}" arc.',
        f"Tell a gentle story where {hero.id} and {helper.id} work together to {task.goal} for {prize.phrase}.",
        f"Write a child-friendly story with a bridge shaped like an arc and a happy teamwork ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    task: Task = f["task"]
    prize: Prize = f["prize_def"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, with help from {helper.id}. They were small animal friends who worked together.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at the stream?",
            answer=f"{hero.id} wanted to {task.verb} and reach {prize.phrase} on the far side.",
        ),
        QAItem(
            question=f"Why was the bridge a little tricky?",
            answer=f"The bridge curved like an arc, so it looked shaky and {task.danger}.",
        ),
        QAItem(
            question=f"How did the friends solve the problem?",
            answer=f"They used teamwork. {helper.id} helped steady the bridge, and {hero.id} crossed carefully with the prize.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"At the end, the bridge was steady, the prize was safe, and the friends crossed together with happy smiles.",
        ),
    ]
    return qa


WORLD_KNOWLEDGE = {
    "arc": [
        QAItem(
            question="What is an arc?",
            answer="An arc is a curved shape, like a rainbow or a bent bridge.",
        )
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people or animals help each other to get something done together.",
        )
    ],
    "bridge": [
        QAItem(
            question="What does a bridge do?",
            answer="A bridge helps you cross over water, a road, or another gap.",
        )
    ],
    "animal": [
        QAItem(
            question="Why do animals sometimes work together?",
            answer="Animals may work together to find food, stay safe, or help a friend.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"arc", "teamwork", "bridge", "animal"}
    out: list[QAItem] = []
    for tag in tags:
        out.extend(WORLD_KNOWLEDGE.get(tag, []))
    return out


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
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({sig[0] for sig in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="the little stream", task="cross", prize="basket", hero="Pip", helper="Nia"),
    StoryParams(place="the little stream", task="carry", prize="seed bag", hero="Bram", helper="Dot"),
    StoryParams(place="the little stream", task="rescue", prize="lantern", hero="Moss", helper="Tuck"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal teamwork story world with an arc-shaped bridge.")
    ap.add_argument("--place", choices=["the little stream"], default="the little stream")
    ap.add_argument("--task", choices=list(TASKS))
    ap.add_argument("--prize", choices=list(PRIZES))
    ap.add_argument("--hero", choices=NAMES)
    ap.add_argument("--helper", choices=NAMES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    task = args.task or rng.choice(list(TASKS))
    prize = args.prize or rng.choice(list(PRIZES))
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != hero])
    if hero == helper:
        helper = rng.choice([n for n in NAMES if n != hero])
    params = StoryParams(place=args.place, task=task, prize=prize, hero=hero, helper=helper)
    if not reasonableness_gate(TASKS[task], PRIZES[prize]):
        raise StoryError("This combination is not a believable teamwork story.")
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_story_world(params)
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


ASP_RULES = r"""
prize_at_risk(T, P) :- task(T), prize(P), needs_teamwork(T, P).
has_teamwork(T) :- needs_teamwork(T, _).
valid_story(T, P) :- task(T), prize(P), has_teamwork(T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for t in TASKS.values():
        lines.append(asp.fact("task", t.id))
        lines.append(asp.fact("needs_teamwork", t.id, "basket"))
        lines.append(asp.fact("needs_teamwork", t.id, "seed_bag"))
        lines.append(asp.fact("needs_teamwork", t.id, "lantern"))
    for p in PRIZES:
        lines.append(asp.fact("prize", p.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(t.id, p.label.replace(" ", "_")) for t in TASKS.values() for p in PRIZES.values() if reasonableness_gate(t, p)}
    asp_set = set(asp_valid_stories())
    if python_set == asp_set:
        print(f"OK: clingo gate matches python gate ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if asp_set - python_set:
        print("  only in ASP:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible task/prize combos:")
        for t, p in stories:
            print(f"  {t} {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.helper}: {p.task} / {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
