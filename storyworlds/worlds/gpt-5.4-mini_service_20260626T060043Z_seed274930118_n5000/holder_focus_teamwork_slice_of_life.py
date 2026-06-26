#!/usr/bin/env python3
"""
A small slice-of-life storyworld about keeping a shared holder organized so a
pair of characters can stay focused and work together.

The seed words are built into the domain: "holder" and "focus".
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
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    shared: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the kitchen table"
    afford_focus: bool = True


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    distraction: str
    needs_holder: bool
    focus_gain: float
    mess: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Holder:
    id: str
    label: str
    phrase: str
    purpose: str
    shared: bool = True
    fits: set[str] = field(default_factory=set)


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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "table": Setting(place="the kitchen table", afford_focus=True),
    "desk": Setting(place="the little desk by the window", afford_focus=True),
    "bench": Setting(place="the quiet bench in the hallway", afford_focus=True),
    "library": Setting(place="the library corner", afford_focus=True),
}

TASKS = {
    "blocks": Task(
        id="blocks",
        verb="build a tall block tower",
        gerund="building a tall block tower",
        distraction="the blocks kept wobbling and begging for another try",
        needs_holder=True,
        focus_gain=1.0,
        mess="pieces",
        result="the tower stood straight and proud",
        tags={"teamwork", "play"},
    ),
    "snacks": Task(
        id="snacks",
        verb="sort the snack cups",
        gerund="sorting the snack cups",
        distraction="the cups rolled everywhere when they were nudged too fast",
        needs_holder=True,
        focus_gain=1.0,
        mess="spilled",
        result="the snacks stayed neat and easy to share",
        tags={"teamwork", "care"},
    ),
    "crayons": Task(
        id="crayons",
        verb="color a big picture",
        gerund="coloring a big picture",
        distraction="the crayons kept sliding off the page and onto the floor",
        needs_holder=True,
        focus_gain=1.0,
        mess="scattered",
        result="the picture came out bright and complete",
        tags={"teamwork", "art"},
    ),
    "buttons": Task(
        id="buttons",
        verb="sort the buttons by color",
        gerund="sorting the buttons by color",
        distraction="the tiny buttons were easy to lose if nobody watched them closely",
        needs_holder=True,
        focus_gain=1.0,
        mess="dropped",
        result="the buttons ended up lined up in neat little rows",
        tags={"teamwork", "care"},
    ),
}

HOLDERS = {
    "tray": Holder(
        id="tray",
        label="a shallow tray",
        phrase="a shallow tray with smooth sides",
        purpose="keeping little things from rolling away",
        shared=True,
        fits={"blocks", "snacks", "buttons"},
    ),
    "basket": Holder(
        id="basket",
        label="a woven basket",
        phrase="a woven basket with a soft cloth inside",
        purpose="holding things together in one place",
        shared=True,
        fits={"snacks", "buttons", "crayons"},
    ),
    "cup": Holder(
        id="cup",
        label="a pencil cup",
        phrase="a pencil cup with a bright rim",
        purpose="standing crayons up so they are easy to reach",
        shared=True,
        fits={"crayons"},
    ),
    "box": Holder(
        id="box",
        label="a little box",
        phrase="a little box with a snug lid",
        purpose="keeping tiny pieces together",
        shared=True,
        fits={"buttons", "blocks"},
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Ivy", "Nora", "Tia", "Maya", "Ella", "June"]
BOY_NAMES = ["Owen", "Theo", "Eli", "Noah", "Finn", "Leo", "Max", "Ben"]
TRAITS = ["careful", "gentle", "curious", "patient", "helpful", "bright"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    task: str
    holder: str
    name1: str
    gender1: str
    name2: str
    gender2: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def choose_holder(task: Task) -> Optional[Holder]:
    for holder in HOLDERS.values():
        if task.id in holder.fits:
            return holder
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for task in TASKS.values():
            holder = choose_holder(task)
            if holder:
                combos.append((setting, task.id, holder.id))
    return combos


def assert_valid(task: Task, holder: Holder) -> None:
    if task.id not in holder.fits:
        raise StoryError(
            f"(No story: {holder.label} is not a reasonable holder for {task.gerund}; "
            f"the teamwork fix would not actually help.)"
        )


def pronoun_type(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def make_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    task = TASKS[params.task]
    holder = HOLDERS[params.holder]

    world = World(setting)

    a = world.add(Entity(
        id=params.name1, kind="character", type=pronoun_type(params.gender1),
        meters={"focus": 0.0}, memes={"joy": 0.0, "teamwork": 0.0}
    ))
    b = world.add(Entity(
        id=params.name2, kind="character", type=pronoun_type(params.gender2),
        meters={"focus": 0.0}, memes={"joy": 0.0, "teamwork": 0.0}
    ))
    h = world.add(Entity(
        id=holder.id, kind="thing", type="holder", label=holder.label,
        phrase=holder.phrase, shared=True, owner=a.id, held_by=a.id
    ))

    world.facts.update(actor=a, helper=b, holder=h, task=task, setting=setting)
    return world


def narrate_story(world: World) -> str:
    a = world.facts["actor"]
    b = world.facts["helper"]
    h = world.facts["holder"]
    task: Task = world.facts["task"]
    setting: Setting = world.facts["setting"]

    world.say(
        f"{a.id} and {b.id} sat down at {setting.place} on a quiet little afternoon. "
        f"They had {h.phrase}, and it was the kind of holder that made a busy table feel calm."
    )
    world.say(
        f"{a.id} wanted to {task.verb}, and {b.id} wanted to help. "
        f"Together they knew they could keep their focus if everything stayed in one place."
    )

    world.para()
    a.memes["interest"] = a.memes.get("interest", 0.0) + 1
    b.memes["interest"] = b.memes.get("interest", 0.0) + 1
    a.meters["focus"] += 0.5
    b.meters["focus"] += 0.5
    world.say(
        f"At first, the task was a little tricky. {task.distraction.capitalize()}. "
        f"{b.id} moved the {h.label} closer and said, \"Let's use the holder so we can stay focused.\""
    )
    h.held_by = b.id
    b.memes["teamwork"] += 1
    a.memes["teamwork"] += 1
    a.meters["focus"] += task.focus_gain
    b.meters["focus"] += task.focus_gain

    world.para()
    world.say(
        f"That helped right away. {a.id} worked on {task.gerund}, while {b.id} kept the pieces tidy in the {h.label}. "
        f"They took turns and checked each other with small smiles, which made the whole job feel easier."
    )
    world.say(
        f"By the end, {task.result}, and nobody had to chase stray bits around the room. "
        f"{a.id} and {b.id} had used teamwork to keep their focus from drifting."
    )

    world.facts["finished"] = True
    world.facts["holder_used"] = True
    world.facts["result"] = task.result
    return world.render()


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task: Task = f["task"]
    return [
        f'Write a short slice-of-life story about two children sharing {f["holder"].label} to stay focused.',
        f"Tell a gentle teamwork story where {f['actor'].id} and {f['helper'].id} use a holder while they {task.verb}.",
        f'Write a story that includes the words "holder" and "focus" and ends with a calm, happy finish.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = f["actor"]
    b = f["helper"]
    task: Task = f["task"]
    holder: Entity = f["holder"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who worked together at {setting.place}?",
            answer=f"{a.id} and {b.id} worked together at {setting.place}. They shared {holder.label} so they could stay focused."
        ),
        QAItem(
            question=f"What did they use to keep the task tidy?",
            answer=f"They used {holder.phrase}. It helped keep the little parts in one place while they worked."
        ),
        QAItem(
            question=f"Why did the holder help with the task?",
            answer=f"The holder helped because {task.distraction.lower()}. With everything gathered together, it was easier for them to focus."
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {task.result}, and {a.id} and {b.id} felt good about their teamwork."
        ),
    ]


WORLD_KNOWLEDGE = {
    "holder": (
        "What is a holder?",
        "A holder is something that keeps things together so they do not roll away, fall over, or get lost."
    ),
    "focus": (
        "What does it mean to focus?",
        "To focus means to pay attention to one thing and keep your mind on it."
    ),
    "teamwork": (
        "What is teamwork?",
        "Teamwork is when people help each other and work together to finish something."
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE.values()]


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
        bits = []
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        if e.held_by:
            bits.append(f"held_by={e.held_by!r}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

valid(Setting, Task, Holder) :- setting(Setting), task(Task), holder(Holder),
    fits(Holder, Task), afford_focus(Setting).

valid_story(Setting, Task, Holder, Gender1) :-
    valid(Setting, Task, Holder), gender(Gender1).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.afford_focus:
            lines.append(asp.fact("afford_focus", sid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for hid, h in HOLDERS.items():
        lines.append(asp.fact("holder", hid))
        for fit in sorted(h.fits):
            lines.append(asp.fact("fits", hid, fit))
    lines.append(asp.fact("gender", "girl"))
    lines.append(asp.fact("gender", "boy"))
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
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Parameter resolution and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life teamwork storyworld with a holder and focus.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--holder", choices=HOLDERS)
    ap.add_argument("--name1")
    ap.add_argument("--gender1", choices=["girl", "boy"])
    ap.add_argument("--name2")
    ap.add_argument("--gender2", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.task:
        combos = [c for c in combos if c[1] == args.task]
    if args.holder:
        combos = [c for c in combos if c[2] == args.holder]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, holder = rng.choice(sorted(combos))
    g1 = args.gender1 or rng.choice(["girl", "boy"])
    g2 = args.gender2 or ("boy" if g1 == "girl" and rng.random() < 0.5 else "girl")
    name1 = args.name1 or make_name(g1, rng)
    name2 = args.name2 or make_name(g2, rng)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, task=task, holder=holder, name1=name1, gender1=g1,
                       name2=name2, gender2=g2, trait=trait)


def generate(params: StoryParams) -> StorySample:
    task = TASKS[params.task]
    holder = HOLDERS[params.holder]
    assert_valid(task, holder)
    world = build_world(params)
    story = narrate_story(world)
    return StorySample(
        params=params,
        story=story,
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
    StoryParams(setting="table", task="blocks", holder="tray", name1="Mina", gender1="girl", name2="Owen", gender2="boy", trait="careful"),
    StoryParams(setting="desk", task="crayons", holder="cup", name1="Theo", gender1="boy", name2="Lena", gender2="girl", trait="helpful"),
    StoryParams(setting="library", task="buttons", holder="box", name1="Ivy", gender1="girl", name2="Finn", gender2="boy", trait="patient"),
    StoryParams(setting="bench", task="snacks", holder="basket", name1="Noah", gender1="boy", name2="Maya", gender2="girl", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (setting, task, holder) combos:\n")
        for s, t, h in triples:
            print(f"  {s:10} {t:10} {h:10}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name1} and {p.name2}: {p.task} with {p.holder} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
