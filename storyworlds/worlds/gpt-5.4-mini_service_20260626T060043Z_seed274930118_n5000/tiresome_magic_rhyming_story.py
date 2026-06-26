#!/usr/bin/env python3
"""
A tiny storyworld for a Rhyming Story-style tale about tiresome magic.

Premise:
A child finds a magic rhyme that can make chores feel easier. The magic is
useful, but it gets tiresome when the words keep slipping, the room keeps
changing, and the child must choose a better, gentler spell.

The world is intentionally small:
- one child
- one parent
- one boring task
- one magical helper/tool
- one happy resolution

The story stays state-driven: the task has an emotional burden, the spell adds
magic pressure, and the ending proves what changed.
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


# ---------------------------------------------------------------------------
# Entities and world state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoors: bool
    afford: str


@dataclass
class Task:
    id: str
    label: str
    verb: str
    gerund: str
    mess: str
    burden: str
    place: str
    rhyme_word: str
    risk: str


@dataclass
class MagicTool:
    id: str
    label: str
    phrase: str
    effect: str
    limitation: str
    fix: str
    rhyme_word: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "kitchen": Place("kitchen", "the kitchen", True, "tidy"),
    "laundry_room": Place("laundry_room", "the laundry room", True, "wash"),
    "garden_shed": Place("garden_shed", "the garden shed", False, "sweep"),
}

TASKS = {
    "sweeping": Task(
        id="sweeping",
        label="sweeping the floor",
        verb="sweep the floor",
        gerund="sweeping the floor",
        mess="dust",
        burden="tiresome dust",
        place="kitchen",
        rhyme_word="sweep",
        risk="dusty",
    ),
    "sorting": Task(
        id="sorting",
        label="sorting the socks",
        verb="sort the socks",
        gerund="sorting the socks",
        mess="tangle",
        burden="tiresome tangles",
        place="laundry_room",
        rhyme_word="sort",
        risk="tangled",
    ),
    "watering": Task(
        id="watering",
        label="watering the plants",
        verb="water the plants",
        gerund="watering the plants",
        mess="spill",
        burden="tiresome spills",
        place="garden_shed",
        rhyme_word="pour",
        risk="splashy",
    ),
}

MAGIC = {
    "broom_spell": MagicTool(
        id="broom_spell",
        label="a magic broom",
        phrase="a magic broom that hummed a tune",
        effect="the dust spun into neat little swirls",
        limitation="it only worked while the words stayed in step",
        fix="a gentler rhyme",
        rhyme_word="glow",
    ),
    "sock_spell": MagicTool(
        id="sock_spell",
        label="a silver bell",
        phrase="a silver bell with a tinkly sound",
        effect="the socks lined up like sleepy ducks",
        limitation="it stopped if the rhyme got too fast",
        fix="a slower chorus",
        rhyme_word="jingle",
    ),
    "rain_spell": MagicTool(
        id="rain_spell",
        label="a warm wand",
        phrase="a warm wand that made a soft spark",
        effect="the plants drank their water and stood up straight",
        limitation="it splashed too much if waved wildly",
        fix="a careful whisper",
        rhyme_word="spark",
    ),
}

NAMES = ["Mina", "Theo", "Luna", "Finn", "Nora", "Pip", "Ari", "Bea"]
TRAITS = ["brave", "curious", "cheerful", "sleepy", "playful", "patient"]


@dataclass
class StoryParams:
    place: str
    task: str
    magic: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def task_needs_magic(task: Task) -> bool:
    return task.id in TASKS


def compatible_magic(task: Task, magic: MagicTool) -> bool:
    return {
        ("sweeping", "broom_spell"),
        ("sorting", "sock_spell"),
        ("watering", "rain_spell"),
    }.__contains__((task.id, magic.id))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for task_id, task in TASKS.items():
            if task.place != place_id:
                continue
            for magic_id, magic in MAGIC.items():
                if compatible_magic(task, magic):
                    combos.append((place_id, task_id, magic_id))
    return combos


def explain_rejection(task: Task, magic: MagicTool) -> str:
    return (
        f"(No story: {magic.label} does not fit {task.gerund}. "
        f"The magic must actually help with that chore, or the tale would not be fair.)"
    )


# ---------------------------------------------------------------------------
# Simulated beats
# ---------------------------------------------------------------------------
def setup(world: World, child: Entity, parent: Entity, task: Task, magic: MagicTool) -> None:
    child.memes["interest"] = child.memes.get("interest", 0) + 1
    world.say(
        f"{child.id} was a {child.pronoun('subject')} who liked little surprises, "
        f"but {task.burden} felt long and tiresome."
    )
    world.say(
        f"Then {child.id} found {magic.phrase}, and {child.pronoun('possessive')} {parent.type} smiled, "
        f"\"Try a rhyme and see what it can do.\""
    )


def attempt_magic(world: World, child: Entity, task: Task, magic: MagicTool) -> None:
    child.memes["hope"] = child.memes.get("hope", 0) + 1
    child.meters["magic"] = child.meters.get("magic", 0) + 1
    world.say(
        f"{child.id} sang, \"{task.rhyme_word}, {task.rhyme_word}, bright and slow, "
        f"make the {task.label} easy to go.\""
    )
    world.say(
        f"For a blink, {magic.effect}, and the room felt light with a tiny glow."
    )
    world.facts["magic_used"] = True
    world.facts["spell_limit"] = magic.limitation


def complication(world: World, child: Entity, parent: Entity, task: Task, magic: MagicTool) -> None:
    child.memes["frustration"] = child.memes.get("frustration", 0) + 1
    child.meters[task.mess] = child.meters.get(task.mess, 0) + 1
    world.say(
        f"But the rhyme grew fast and the spell went wrong; the magic felt noisy, not neat or strong."
    )
    world.say(
        f"The {task.label} turned {task.risk}, and {child.id} sighed, \"This is getting tiresome for me.\""
    )
    world.facts["problem"] = task.risk


def turn_to_better_way(world: World, child: Entity, parent: Entity, task: Task, magic: MagicTool) -> None:
    child.memes["calm"] = child.memes.get("calm", 0) + 1
    child.memes["frustration"] = 0
    world.say(
        f"{parent.id} said, \"Use a {magic.fix}, and keep it small; then the magic will help instead of making a stall.\""
    )
    world.say(
        f"{child.id} breathed in once, then sang again, soft as a feather and square as a pen."
    )
    world.say(
        f"This time the words moved slow and clear, and the {task.label} was easy to keep near."
    )


def resolution(world: World, child: Entity, parent: Entity, task: Task) -> None:
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    child.meters["done"] = child.meters.get("done", 0) + 1
    world.say(
        f"At last the chore was done, and {child.id} grinned wide; the tiresome job had turned into pride."
    )
    world.say(
        f"The floor was clean, the socks were set, or the plants stood tall without getting wet."
    )
    world.say(
        f"{parent.id} laughed, {child.id} did too, and the little magic rhyme felt just right through and through."
    )


def tell(place: Place, task: Task, magic: MagicTool, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type=gender, memes={"calm": 0.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    world.facts["child"] = child
    world.facts["parent"] = parent
    world.facts["task"] = task
    world.facts["magic"] = magic
    world.facts["place"] = place
    world.facts["trait"] = trait

    setup(world, child, parent, task, magic)
    world.para()
    attempt_magic(world, child, task, magic)
    complication(world, child, parent, task, magic)
    world.para()
    turn_to_better_way(world, child, parent, task, magic)
    resolution(world, child, parent, task)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task: Task = f["task"]
    magic: MagicTool = f["magic"]
    child: Entity = f["child"]
    return [
        f'Write a short rhyming story for a child named {child.id} about {task.label} and {magic.label}.',
        f"Tell a gentle story where {child.id} tries magic to make {task.gerund} less tiresome.",
        f'Write a small story with the word "tiresome" and a magic rhyme that goes wrong before it goes right.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    task: Task = f["task"]
    magic: MagicTool = f["magic"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"What tiresome chore did {child.id} try to do with {magic.label}?",
            answer=f"{child.id} tried {task.gerund} with {magic.label} in {place.label}.",
        ),
        QAItem(
            question=f"Why did the first magic rhyme make {child.id} unhappy?",
            answer=f"The first rhyme made the magic too noisy, and the {task.label} turned {task.risk} instead of easy.",
        ),
        QAItem(
            question=f"What helped {child.id} finish the chore in the end?",
            answer=f"A gentler rhyme and {parent.id}'s calm advice helped {child.id} finish the job.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does tiresome mean?",
            answer="Tiresome means something feels long, boring, or hard to keep doing.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a special impossible-seeming power that can make unusual things happen in a story.",
        ),
        QAItem(
            question="Why can a rhyme help in a story?",
            answer="A rhyme can help a character remember words, and it can make a story sound playful and musical.",
        ),
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid_combo(P,T,M) :- place(P), task(T), magic(M), matches(P,T,M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        lines.append(asp.fact("place_label", pid, p.label))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("task_place", tid, t.place))
        lines.append(asp.fact("matches", t.place, tid, next(k for k, v in MAGIC.items() if compatible_magic(t, v))))
    for mid, m in MAGIC.items():
        lines.append(asp.fact("magic", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming storyworld with tiresome magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.task and args.magic:
        task = TASKS[args.task]
        magic = MAGIC[args.magic]
        if not compatible_magic(task, magic):
            raise StoryError(explain_rejection(task, magic))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.magic is None or c[2] == args.magic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task_id, magic_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, task=task_id, magic=magic_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        TASKS[params.task],
        MAGIC[params.magic],
        params.name,
        params.gender,
        params.parent,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="kitchen", task="sweeping", magic="broom_spell", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="laundry_room", task="sorting", magic="sock_spell", name="Theo", gender="boy", parent="father", trait="patient"),
    StoryParams(place="garden_shed", task="watering", magic="rain_spell", name="Luna", gender="girl", parent="mother", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print(" ", row)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i+1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
