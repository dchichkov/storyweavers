#!/usr/bin/env python3
"""
storyworlds/worlds/precocious_profile_bravery_nursery_rhyme.py
===============================================================

A tiny nursery-rhyme storyworld about a precocious child, a bravery profile,
and a small test of courage.

Premise:
- A child has a keepsake "profile" card that lists brave things they can do.
- The child wants to do a small task that feels scary but is not truly unsafe.
- Bravery rises when the child uses a helper, a charm, or a remembered rhyme.

The world is intentionally small and constraint-checked:
- Not every scary task is reasonable.
- The task must fit the child's profile.
- The ending proves a state change: the task is done, and the bravery profile
  gains a checkmark.

Style:
- Child-facing, concrete, lightly musical, nursery-rhyme cadence.

Seed words:
- precocious
- profile
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    touched_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "queen"}
        male = {"boy", "father", "dad", "man", "brother", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool
    supports: set[str]


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    scare: str
    reward: str
    risk: str
    sign: str
    supports: set[str]
    helper: str
    rhyme: str
    tag: str


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    protects: set[str]
    boosts: set[str]
    clue: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def place_line(place: Place, task: Task) -> str:
    if place.indoors:
        return f"In the {place.name}, the floor was smooth and the small room hummed like a spoon."
    return f"By the {place.name}, the breeze blew soft, and the lane looked bright for a brave small stroll."


def courage_line(task: Task) -> str:
    return {
        "bell": "A little bell can jingle, but it cannot bite.",
        "bridge": "A bridge can sway and sing, yet still be safe for careful feet.",
        "dark": "A dim hall can feel like a cave, though a lamp makes it mild and light.",
        "crowd": "A crowd can murmur and flutter, but kind faces are still kind faces.",
    }.get(task.id, "The thing felt big at first, then smaller once looked at closely.")


def _r_charm(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts.get("child")
    charm = world.facts.get("charm")
    if not child or not charm:
        return out
    if child.memes.get("worry", 0) >= THRESHOLD and child.meters.get("carrying_charm", 0) >= THRESHOLD:
        sig = ("charm_boost", child.id, charm.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["bravery"] = child.memes.get("bravery", 0) + 1
            out.append(f"The {charm.label} gave {child.id} a brave little spark.")
    return out


def _r_reward(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts.get("child")
    task = world.facts.get("task")
    if not child or not task:
        return out
    if child.meters.get("did_task", 0) < THRESHOLD:
        return out
    sig = ("reward", child.id, task.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["pride"] = child.memes.get("pride", 0) + 1
    child.meters["profile_marks"] = child.meters.get("profile_marks", 0) + 1
    out.append(f"A new checkmark went on the bravery profile.")
    return out


CAUSAL_RULES = [_r_charm, _r_reward]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_result(world: World, child: Entity, task: Task, charm: Optional[Charm]) -> dict:
    sim = world.copy()
    sim_child = sim.get(child.id)
    sim_child.memes["worry"] = sim_child.memes.get("worry", 0) + 1
    if charm:
        sim_child.meters["carrying_charm"] = 1
    if task.id in task.supports and task.id in sim.place.supports:
        sim_child.meters["did_task"] = 1
    propagate(sim, narrate=False)
    return {
        "brave_enough": sim_child.memes.get("bravery", 0) >= THRESHOLD,
        "done": sim_child.meters.get("did_task", 0) >= THRESHOLD,
        "profile_marks": sim_child.meters.get("profile_marks", 0),
    }


def introduce(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} was a precocious little {child.type}, quick to ask big questions and tiny enough to fit in a lap."
    )


def show_profile(world: World, child: Entity, task: Task) -> None:
    world.say(
        f"{child.id} kept a bravery profile with neat little lines, and one line said, "
        f'"{task.sign}."'
    )


def want(world: World, child: Entity, task: Task) -> None:
    child.memes["want"] = child.memes.get("want", 0) + 1
    world.say(
        f"{child.id} wanted to {task.verb}, for the rhyme in {task.rhyme} had caught in {child.pronoun('possessive')} ear."
    )


def worry(world: World, child: Entity, task: Task) -> None:
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.say(
        f"But {task.scare}, and {child.id} stood still with big round eyes."
    )
    world.say(courage_line(task))


def offer_charm(world: World, child: Entity, charm: Charm) -> None:
    child.meters["carrying_charm"] = 1
    charm_ent = world.add(Entity(id=charm.id, label=charm.label, phrase=charm.phrase, owner=child.id))
    charm_ent.carried_by = child.id
    world.say(
        f"{child.id} tucked the {charm.label} into a pocket, because {charm.clue}."
    )


def do_task(world: World, child: Entity, task: Task) -> None:
    child.meters["did_task"] = 1
    child.memes["bravery"] = child.memes.get("bravery", 0) + 1
    world.say(
        f"Then {child.id} took one breath, then two, and went to {task.gerund}."
    )
    world.say(
        f"{child.id} did it, and the {task.reward} felt warm and sweet."
    )
    propagate(world, narrate=True)


def resolve(world: World, child: Entity, task: Task) -> None:
    child.memes["worry"] = 0
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    world.say(
        f"{child.id} smiled a small, proud smile, and the bravery profile gained a fresh checkmark."
    )
    world.say(
        f"By the end, the little fright was gone, and the rhyme turned bright."
    )


def tell(place: Place, task: Task, charm: Charm, child_name: str, child_type: str, parent_type: str) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    world.facts.update(child=child, parent=parent, task=task, charm=charm, place=place)

    introduce(world, child)
    show_profile(world, child, task)
    world.say(place_line(place, task))
    want(world, child, task)
    worry(world, child, task)
    offer_charm(world, child, charm)
    if not predict_result(world, child, task, charm)["done"]:
        raise StoryError("This charm does not reasonably help the child complete the task.")
    do_task(world, child, task)
    resolve(world, child, task)
    return world


PLACES = {
    "nursery": Place(name="nursery", indoors=True, supports={"bell", "dark"}),
    "hall": Place(name="hall", indoors=True, supports={"dark", "crowd"}),
    "garden_gate": Place(name="garden gate", indoors=False, supports={"bridge", "crowd"}),
    "little_bridge": Place(name="little bridge", indoors=False, supports={"bridge"}),
    "square": Place(name="village square", indoors=False, supports={"crowd"}),
}

TASKS = {
    "bell": Task(
        id="bell",
        verb="ring the brass bell",
        gerund="ringing the brass bell",
        scare="the bell was taller than the stool and glinted like a moon",
        reward="sound",
        risk="a trembling hand might miss the pull",
        sign="Ring the bell once",
        supports={"bell"},
        helper="a stool and a steady breath",
        rhyme="ding-dong, ring-a-long",
        tag="bell",
    ),
    "bridge": Task(
        id="bridge",
        verb="cross the little bridge",
        gerund="crossing the little bridge",
        scare="the boards hummed in the wind",
        reward="other side",
        risk="a wobble might make the feet pause",
        sign="Cross the bridge slow",
        supports={"bridge"},
        helper="a hand and a hum",
        rhyme="tip-tap, gentle step",
        tag="bridge",
    ),
    "dark": Task(
        id="dark",
        verb="carry a lamp through the hall",
        gerund="carrying the lamp through the hall",
        scare="the hall was dim as a mitten",
        reward="glow",
        risk="shadows can make a child freeze",
        sign="Carry light kindly",
        supports={"dark"},
        helper="a lamp and a song",
        rhyme="shine-line, tiny pine",
        tag="dark",
    ),
    "crowd": Task(
        id="crowd",
        verb="say the little rhyme to the crowd",
        gerund="saying the little rhyme to the crowd",
        scare="the village square buzzed and swayed with many eyes",
        reward="clap",
        risk="a soft voice may hide inside the chest",
        sign="Speak the rhyme clearly",
        supports={"crowd"},
        helper="a friend at the elbow",
        rhyme="clear and near, one voice here",
        tag="crowd",
    ),
}

CHARMS = {
    "feather": Charm(
        id="feather",
        label="feather",
        phrase="a white feather charm",
        protects={"worry"},
        boosts={"bravery"},
        clue="it tickled like a secret saying, 'You can.'",
    ),
    "ribbon": Charm(
        id="ribbon",
        label="ribbon",
        phrase="a bright ribbon",
        protects={"worry"},
        boosts={"bravery"},
        clue="it was tied with a promise to try.",
    ),
    "pocketstone": Charm(
        id="pocketstone",
        label="pocket stone",
        phrase="a smooth pocket stone",
        protects={"worry"},
        boosts={"bravery"},
        clue="it felt calm and cool like a pond at dawn.",
    ),
}

NAMES = ["Nina", "Pip", "Milo", "Tess", "Luna", "Perry", "Cleo", "Ivo"]
TYPES = ["girl", "boy"]
PARENT_TYPES = ["mother", "father"]
TRAITS = ["precocious", "bright", "quick", "curious"]


@dataclass
class StoryParams:
    place: str
    task: str
    charm: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for task_id, task in TASKS.items():
            if task_id not in place.supports:
                continue
            for charm_id in CHARMS:
                combos.append((place_id, task_id, charm_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about a precocious child and a bravery profile.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--gender", choices=TYPES)
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.charm is None or c[2] == args.charm)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, charm = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(TYPES)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    trait = args.trait if hasattr(args, "trait") and args.trait else rng.choice(TRAITS)
    return StoryParams(place=place, task=task, charm=charm, name=name, gender=gender, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, task = f["child"], f["task"]
    return [
        f'Write a short nursery-rhyme story about a {child.pronoun("object")} and a bravery profile that mentions "{task.sign}".',
        f"Tell a gentle story where {child.id}, a precocious little {child.type}, learns to do {task.verb}.",
        f'Write a child-friendly rhyme about "{task.rhyme}" and a small brave choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, task, charm = f["child"], f["task"], f["charm"]
    return [
        QAItem(
            question=f"What kind of child is {child.id} in the story?",
            answer=f"{child.id} is a precocious little {child.type} who likes brave little tasks.",
        ),
        QAItem(
            question=f"What was written on the bravery profile?",
            answer=f"It said, \"{task.sign}.\"",
        ),
        QAItem(
            question=f"What helped {child.id} feel brave enough to {task.verb}?",
            answer=f"The {charm.label} helped, because it gave {child.id} a brave little spark.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"{child.id} did the task, and a new checkmark went on the bravery profile.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a profile?",
            answer="A profile is a picture or list that shows what someone is like, or what they can do.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means trying something even when it feels a little scary.",
        ),
        QAItem(
            question="Why can a small helper charm matter?",
            answer="A small helper can remind a child to breathe, focus, and keep going.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="nursery", task="bell", charm="feather", name="Nina", gender="girl", parent="mother", trait="precocious"),
    StoryParams(place="little_bridge", task="bridge", charm="pocketstone", name="Pip", gender="boy", parent="father", trait="curious"),
    StoryParams(place="hall", task="dark", charm="ribbon", name="Tess", gender="girl", parent="mother", trait="bright"),
    StoryParams(place="square", task="crowd", charm="feather", name="Milo", gender="boy", parent="father", trait="quick"),
]


ASP_RULES = r"""
task_valid(Place, Task) :- supports(Place, Task).
task_valid(Place, Task) :- place_supports(Place, Task).
"""
# The inline ASP twin is intentionally minimal but real: it mirrors the Python
# gating that a place must support a task for the story to be valid.
ASP_RULES = r"""
valid(Place, Task, Charm) :- place_supports(Place, Task), charm(Charm).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        for t in sorted(place.supports):
            lines.append(asp.fact("place_supports", pid, t))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        for s in sorted(task.supports):
            lines.append(asp.fact("supports", tid, s))
    for cid in CHARMS:
        lines.append(asp.fact("charm", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - py_set))
    print("  only in python:", sorted(py_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        TASKS[params.task],
        CHARMS[params.charm],
        params.name,
        params.gender,
        params.parent,
    )
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
        print(f"{len(valid_combos())} valid combos:\n")
        for place, task, charm in asp_valid_combos():
            print(f"  {place:12} {task:8} {charm}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
