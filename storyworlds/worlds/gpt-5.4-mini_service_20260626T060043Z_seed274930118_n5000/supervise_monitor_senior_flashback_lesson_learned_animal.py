#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/supervise_monitor_senior_flashback_lesson_learned_animal.py
==============================================================================================================

A small animal-story world about a senior helper who supervises and monitors
a younger animal, with a flashback that explains the lesson learned.

Premise:
- A young animal wants to do a job alone.
- A senior animal watches closely and supervises the task.
- The younger animal makes a small mistake.
- A flashback recalls the earlier warning and the lesson learned.
- The animals repair the problem and finish safely together.

The story is built from actual simulated state:
- physical meters: dirt, tiredness, water, balance, readiness
- emotional memes: pride, worry, trust, relief, patience, confidence

This world keeps the prose child-facing, concrete, and classical in shape:
setup -> tension -> flashback -> lesson learned -> resolution.
"""

from __future__ import annotations

import argparse
import copy
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
    species: str = "animal"
    label: str = ""
    phrase: str = ""
    role: str = ""
    senior: bool = False
    helper: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def verb_be(self) -> str:
        return "was" if self.id else "was"

    def title(self) -> str:
        if self.senior:
            return f"senior {self.species}"
        return self.species


@dataclass
class Place:
    name: str
    kind: str
    affordances: set[str] = field(default_factory=set)
    hazards: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    hazard: str
    fix: str
    place_kind: str
    requires: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    task: str
    hero: str
    hero_species: str
    senior: str
    senior_species: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    history: list[str] = field(default_factory=list)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        return World(
            place=self.place,
            entities=copy.deepcopy(self.entities),
            facts=copy.deepcopy(self.facts),
            paragraphs=[[]],
            fired=set(self.fired),
            history=list(self.history),
        )


@dataclass
class Rule:
    name: str
    apply: callable


def _r_mess(world: World) -> list[str]:
    out = []
    hero = world.get(world.facts["hero"].id)
    task = world.facts["task"]
    place = world.place
    if hero.meters.get(task.hazard, 0.0) < THRESHOLD:
        return out
    sig = ("mess", hero.id, task.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["dirt"] = hero.meters.get("dirt", 0.0) + 1
    hero.memes["embarrassed"] = hero.memes.get("embarrassed", 0.0) + 1
    out.append(f"{hero.id} got splashed and muddy near the {place.name}.")
    return out


def _r_worry(world: World) -> list[str]:
    out = []
    hero = world.get(world.facts["hero"].id)
    senior = world.get(world.facts["senior"].id)
    if hero.meters.get("dirt", 0.0) < THRESHOLD:
        return out
    sig = ("worry", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    senior.memes["worry"] = senior.memes.get("worry", 0.0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    out.append(f"{senior.id} watched closely and grew worried.")
    return out


def _r_repair(world: World) -> list[str]:
    out = []
    hero = world.get(world.facts["hero"].id)
    senior = world.get(world.facts["senior"].id)
    sig = ("repair", hero.id)
    if sig in world.fired:
        return out
    if hero.memes.get("lesson", 0.0) < THRESHOLD:
        return out
    world.fired.add(sig)
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    senior.memes["pride"] = senior.memes.get("pride", 0.0) + 1
    hero.meters["dirt"] = max(0.0, hero.meters.get("dirt", 0.0) - 1)
    out.append(f"Together they cleaned the mess and finished the job.")
    return out


CAUSAL_RULES = [Rule("mess", _r_mess), Rule("worry", _r_worry), Rule("repair", _r_repair)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def predict_mess(world: World) -> bool:
    sim = world.copy()
    propagate(sim, narrate=False)
    hero = sim.get(sim.facts["hero"].id)
    return hero.meters.get("dirt", 0.0) >= THRESHOLD


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    task = TASKS[params.task]
    world = World(place=place)

    hero = world.add(Entity(
        id=params.hero,
        kind="animal",
        species=params.hero_species,
        label=params.hero,
        role="young helper",
        meters={"dirt": 0.0, "readiness": 1.0, "balance": 1.0},
        memes={"pride": 1.0, "confidence": 1.0},
    ))
    senior = world.add(Entity(
        id=params.senior,
        kind="animal",
        species=params.senior_species,
        label=params.senior,
        role="senior helper",
        senior=True,
        helper=True,
        meters={"patience": 1.0, "readiness": 1.0},
        memes={"care": 1.0, "watchfulness": 1.0},
    ))

    world.facts["hero"] = hero
    world.facts["senior"] = senior
    world.facts["task"] = task

    world.say(
        f"{hero.id} was a little {hero.species} who wanted to {task.verb} by the {place.name}."
    )
    world.say(
        f"{senior.id} was a senior {senior.species} who knew how to supervise and monitor a job safely."
    )

    world.para()
    world.say(
        f"One bright morning, {hero.id} and {senior.id} went to the {place.name} to do the work together."
    )
    world.say(
        f"{hero.id} wanted to act brave, but {senior.id} said, \"Stay close, and I will monitor you while you try.\""
    )

    world.para()
    hero.meters[task.hazard] = hero.meters.get(task.hazard, 0.0) + 1.0
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1.0
    world.say(
        f"{hero.id} tried to {task.verb}, but the {task.hazard} made the task tricky."
    )
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"That brought back a flashback: earlier, {senior.id} had shown {hero.id} what could happen when a small animal rushed."
    )
    world.say(
        f"{hero.id} remembered the lesson learned: it was smarter to listen, slow down, and let a senior helper supervise."
    )
    hero.memes["lesson"] = 1.0
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1.0

    world.para()
    propagate(world, narrate=True)
    world.say(
        f"In the end, {hero.id} worked carefully beside {senior.id}, and the {place.name} looked tidy again."
    )
    world.say(
        f"{hero.id} smiled, because the lesson learned had made the whole day go better."
    )

    world.facts["flashback"] = True
    world.facts["lesson_learned"] = True
    return world


SETTINGS = {
    "riverbank": Place(name="riverbank", kind="outdoor", affordances={"carry", "gather"}, hazards={"splash"}),
    "barnyard": Place(name="barnyard", kind="outdoor", affordances={"carry", "stack"}, hazards={"mud"}),
    "orchard": Place(name="orchard", kind="outdoor", affordances={"pick", "carry"}, hazards={"branches"}),
    "pond": Place(name="pond", kind="outdoor", affordances={"watch", "carry"}, hazards={"splash"}),
}

TASKS = {
    "carry-buckets": Task(
        id="carry-buckets",
        verb="carry water buckets",
        gerund="carrying water buckets",
        hazard="splash",
        fix="dry off and try again slowly",
        place_kind="outdoor",
        requires={"supervise", "monitor"},
        tags={"water", "lesson"},
    ),
    "stack-hay": Task(
        id="stack-hay",
        verb="stack hay",
        gerund="stacking hay",
        hazard="mud",
        fix="check each step",
        place_kind="outdoor",
        requires={"supervise", "monitor"},
        tags={"farm", "lesson"},
    ),
    "pick-apples": Task(
        id="pick-apples",
        verb="pick apples",
        gerund="picking apples",
        hazard="branches",
        fix="reach carefully",
        place_kind="outdoor",
        requires={"supervise", "monitor"},
        tags={"tree", "lesson"},
    ),
    "watch-ducks": Task(
        id="watch ducks",
        gerund="watching ducks",
        hazard="splash",
        fix="stand back from the edge",
        place_kind="outdoor",
        requires={"supervise", "monitor"},
        tags={"water", "animal"},
    ),
}

ANIMALS = {
    "rabbit": ["Pip", "Milo", "Nina", "Toby", "Luna", "Poppy"],
    "fox": ["Fin", "Ruby", "Sage", "Bram", "Mara", "Juno"],
    "bear": ["Benny", "Clara", "Otis", "Hazel", "Bruno", "Iris"],
    "otter": ["Ollie", "Mina", "Rory", "Kiki", "Nell", "Arlo"],
    "duck": ["Daisy", "Quin", "Moss", "Tilly", "Rowan", "Wren"],
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id, place in SETTINGS.items():
        for task_id, task in TASKS.items():
            if place.kind != task.place_kind:
                continue
            for species, names in ANIMALS.items():
                for senior_species in ANIMALS:
                    combos.append((place_id, task_id, species, senior_species))
    return combos


def explain_invalid(task: Task, place: Place) -> str:
    return f"(No story: the {place.name} does not fit the task {task.id}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with supervise, monitor, senior, flashback, and lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--hero-species", choices=ANIMALS)
    ap.add_argument("--senior-species", choices=ANIMALS)
    ap.add_argument("--hero")
    ap.add_argument("--senior")
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
    if args.place and args.task:
        if TASKS[args.task].place_kind != SETTINGS[args.place].kind:
            raise StoryError(explain_invalid(TASKS[args.task], SETTINGS[args.place]))
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.task:
        combos = [c for c in combos if c[1] == args.task]
    if args.hero_species:
        combos = [c for c in combos if c[2] == args.hero_species]
    if args.senior_species:
        combos = [c for c in combos if c[3] == args.senior_species]
    if not combos:
        raise StoryError("(No valid animal-story combination matches the given options.)")
    place, task, hero_species, senior_species = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(ANIMALS[hero_species])
    senior = args.senior or rng.choice(ANIMALS[senior_species])
    return StoryParams(place=place, task=task, hero=hero, hero_species=hero_species, senior=senior, senior_species=senior_species)


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    senior = world.facts["senior"]
    task = world.facts["task"]
    return [
        f"Write a short animal story about {hero.id}, a young {hero.species}, and {senior.id}, a senior {senior.species}, who supervise a job together.",
        f"Tell a child-friendly story that includes supervise, monitor, a flashback, and a lesson learned while {hero.id} tries to {task.verb}.",
        f"Write an animal story where a senior helper keeps watch and a younger animal learns a safer way to work at the {world.place.name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    senior = world.facts["senior"]
    task = world.facts["task"]
    place = world.place.name
    return [
        QAItem(
            question=f"Who wanted to {task.verb} at the {place}?",
            answer=f"{hero.id}, the young {hero.species}, wanted to {task.verb} at the {place}.",
        ),
        QAItem(
            question=f"Who helped supervise and monitor the job?",
            answer=f"{senior.id}, the senior {senior.species}, helped supervise and monitor the job.",
        ),
        QAItem(
            question=f"What happened when {hero.id} tried to work too quickly?",
            answer=f"{hero.id} got into a little trouble with the {task.hazard}, so the job became messy.",
        ),
        QAItem(
            question="What did the flashback help the young animal remember?",
            answer="The flashback helped the young animal remember the lesson learned: slow down and listen to the senior helper.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The two animals cleaned up together, and {hero.id} finished the work safely beside {senior.id}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to supervise?",
            answer="To supervise means to watch over a job or activity to help make sure it is done safely and well.",
        ),
        QAItem(
            question="What does it mean to monitor?",
            answer="To monitor means to keep checking something closely so you can notice problems early.",
        ),
        QAItem(
            question="What does senior mean?",
            answer="Senior means older or more experienced, like a helper who already knows a lot.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that shows something from earlier in time so the reader understands the past.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is the important thing someone understands after making a mistake or having an experience.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)} role={e.role}")
    lines.append(f"place={world.place.name}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- selected_hero(H).
senior(S) :- selected_senior(S).
task(T) :- selected_task(T).
place(P) :- selected_place(P).

needs_supervision(T) :- task(T), task_requires(T, supervise).
needs_monitoring(T) :- task(T), task_requires(T, monitor).

lesson_learned(H) :- hero(H), flashback(H), supervised(H), monitored(H).
resolved(H) :- lesson_learned(H), cleaned(H).

valid_story(P,T,HS,SS) :- place(P), task(T), hero_species(HS), senior_species(SS),
                          place_fits_task(P,T), supervised_task(T), monitored_task(T).
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("selected_place", pid))
        lines.append(asp.fact("place_kind", pid, p.kind))
        for hz in sorted(p.hazards):
            lines.append(asp.fact("hazard", pid, hz))
    for tid, t in TASKS.items():
        lines.append(asp.fact("selected_task", tid))
        lines.append(asp.fact("task_requires", tid, "supervise"))
        lines.append(asp.fact("task_requires", tid, "monitor"))
        lines.append(asp.fact("task_hazard", tid, t.hazard))
        lines.append(asp.fact("task_place_kind", tid, t.place_kind))
    for sp in ANIMALS:
        lines.append(asp.fact("hero_species", sp))
        lines.append(asp.fact("senior_species", sp))
    for pid, p in SETTINGS.items():
        for tid, t in TASKS.items():
            if p.kind == t.place_kind:
                lines.append(asp.fact("place_fits_task", pid, tid))
    lines.append(asp.fact("supervised_task", "carry-buckets"))
    lines.append(asp.fact("supervised_task", "stack-hay"))
    lines.append(asp.fact("supervised_task", "pick-apples"))
    lines.append(asp.fact("supervised_task", "watch-ducks"))
    lines.append(asp.fact("monitored_task", "carry-buckets"))
    lines.append(asp.fact("monitored_task", "stack-hay"))
    lines.append(asp.fact("monitored_task", "pick-apples"))
    lines.append(asp.fact("monitored_task", "watch-ducks"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set()
    for p in SETTINGS:
        for t in TASKS:
            for hs in ANIMALS:
                for ss in ANIMALS:
                    if SETTINGS[p].kind == TASKS[t].place_kind:
                        python_set.add((p, t, hs, ss))
    if clingo_set == python_set:
        print(f"OK: ASP gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH:")
    print("only in asp:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


CURATED = [
    StoryParams(place="riverbank", task="carry-buckets", hero="Pip", hero_species="rabbit", senior="Hazel", senior_species="bear"),
    StoryParams(place="barnyard", task="stack-hay", hero="Milo", hero_species="fox", senior="Benny", senior_species="bear"),
    StoryParams(place="orchard", task="pick-apples", hero="Luna", hero_species="duck", senior="Mara", senior_species="fox"),
    StoryParams(place="pond", task="watch-ducks", hero="Toby", hero_species="rabbit", senior="Clara", senior_species="bear"),
]


def build_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        return [generate(p) for p in CURATED]
    samples = []
    seen = set()
    i = 0
    while len(samples) < args.n and i < max(100, args.n * 50):
        seed = base_seed + i
        i += 1
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible stories:")
        for t in triples[:200]:
            print(" ", t)
        return

    samples = build_samples(args)

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
            header = f"### {p.hero} and {p.senior} at {p.place} ({p.task})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
