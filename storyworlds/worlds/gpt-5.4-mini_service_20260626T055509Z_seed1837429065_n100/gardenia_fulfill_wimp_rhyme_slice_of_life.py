#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a child who wants to fulfill a promise,
carry a gardenia, and rise above being called a wimp.

Seed premise:
- A child promised to bring a gardenia to someone important.
- On the way, a small worry and a teasing voice make the child feel like a wimp.
- A gentle helper and a simple rhyme help the child keep going.
- The flower is delivered, and the day ends warmer than it began.

This world is intentionally tiny and constraint-checked: it models a few typed
entities with meters and memes, and it generates one complete story with a
beginning, a turn, and a resolution image.
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
# Constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

NAMES = ["Mina", "Owen", "Iris", "Noah", "Tessa", "Ben", "Lena", "Theo"]
HELPER_NAMES = ["Aunt Jo", "Mr. Reed", "Ms. Park", "Grandma", "Dad", "Mom"]
PLACES = ["the front steps", "the corner shop", "the little path", "the garden gate"]
RECIPIENTS = ["Grandma", "Mrs. Vale", "the neighbor", "the teacher", "a friend"]
MOODS = ["calm", "bright", "quiet", "nervous", "hopeful"]

# ---------------------------------------------------------------------------
# Entities
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

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"tired": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "shame": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool = True


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    risk: str
    keyword: str
    rhyme: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "home": Setting(place="the little house", affords={"walk"}),
    "street": Setting(place="the sunny street", affords={"walk"}),
    "garden": Setting(place="the garden gate", affords={"walk", "breathe"}),
}

TASKS = {
    "deliver": Task(
        id="deliver",
        verb="deliver the gardenia",
        gerund="delivering the gardenia",
        risk="crush the petals",
        keyword="gardenia",
        rhyme="gardenia",
        tags={"gardenia", "flower", "promise"},
    ),
    "walk": Task(
        id="walk",
        verb="walk to the gate",
        gerund="walking along",
        risk="stub a toe",
        keyword="step",
        rhyme="step",
        tags={"walk", "street"},
    ),
}

ITEMS = {
    "gardenia": Item(
        id="gardenia",
        label="gardenia",
        phrase="a white gardenia wrapped in paper",
        region="hands",
        fragile=True,
    )
}

# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    task: str
    name: str
    helper: str
    recipient: str
    mood: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the setting affords the task and the gardenia exists.
valid_story(S, T) :- setting(S), task(T), affords(S, T), item(gardenia).

% The worry-turn is valid when the task involves the gardenia and the story can
% plausibly include a tease and a helper.
turn_valid(T) :- task(T), task_tags(T, gardenia), task_tags(T, promise).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("task_tags", tid, tag))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - clingo:
        print("  only in python:", sorted(py - clingo))
    if clingo - py:
        print("  only in clingo:", sorted(clingo - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for tid, t in TASKS.items():
            if sid in ("home", "street", "garden") and t.id == "deliver":
                combos.append((sid, tid))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.task not in TASKS:
        raise StoryError("Unknown task.")
    if params.task == "deliver" and "gardenia" not in TASKS[params.task].tags:
        raise StoryError("The story needs the gardenia task.")
    if params.mood not in MOODS:
        raise StoryError("Unknown mood.")


def predict_turn(world: World, child: Entity, task: Task) -> dict[str, bool]:
    sim = world.copy()
    child2 = sim.get(child.id)
    child2.memes["worry"] += 1
    child2.memes["shame"] += 1
    soars = task.id == "deliver"
    returns = soars and sim.facts.get("helper_present", False)
    return {"worry": True, "resolve": bool(returns)}


def rhyme_line(word: str) -> str:
    return {
        "gardenia": "The gardenia glowed, and the worry would wane.",
        "step": "One small step, then another step.",
        "promise": "Keep the promise, steady and kind.",
    }.get(word, "A gentle rhyme helped the night feel light.")


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Mina", "Iris", "Tessa", "Lena"} else "boy"))
    helper = world.add(Entity(id=params.helper, kind="character", type="woman" if params.helper in {"Aunt Jo", "Ms. Park", "Grandma", "Mom"} else "man"))
    recipient = world.add(Entity(id=params.recipient, kind="character", type="woman"))

    flower = world.add(Entity(
        id="gardenia",
        kind="thing",
        type="flower",
        label="gardenia",
        phrase="a white gardenia wrapped in paper",
        owner=child.id,
        caretaker=recipient.id,
    ))

    world.facts.update(child=child, helper=helper, recipient=recipient, flower=flower, task=TASKS[params.task], helper_present=True)
    return world


def tell(world: World, params: StoryParams) -> World:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    recipient: Entity = world.facts["recipient"]  # type: ignore[assignment]
    flower: Entity = world.facts["flower"]  # type: ignore[assignment]
    task: Task = world.facts["task"]  # type: ignore[assignment]

    child.memes["joy"] += 1
    child.memes["pride"] += 0.5

    world.say(
        f"{child.id} woke up with a small promise in mind: {task.verb}. "
        f"{flower.phrase} waited by the door, smelling soft and sweet."
    )
    world.say(
        f"It was one of those quiet days when the world felt close and simple. "
        f"{child.id} wanted to fulfill the promise before lunch, and {params.mood} "
        f"felt like the right mood for trying."
    )

    world.para()
    world.say(
        f"At {world.setting.place}, {child.id} started down the path with {flower.it()}. "
        f"Then a teasing voice from nearby laughed, 'Don't be such a wimp.'"
    )
    child.memes["worry"] += 1
    child.memes["shame"] += 1

    world.say(
        f"{child.id}'s cheeks grew hot. For a moment, {child.pronoun()} almost stopped. "
        f"But {helper.id} came along beside {child.id} and said, "
        f'"A soft heart is not a weak one."'
    )
    world.say(
        f"{helper.id} tapped the paper around the flower and added a little rhyme: "
        f'"Keep the promise, steady and kind; small brave steps are easy to find."'
    )
    child.memes["worry"] = max(0.0, child.memes["worry"] - 0.5)
    child.memes["shame"] = max(0.0, child.memes["shame"] - 0.5)
    child.memes["pride"] += 1

    world.para()
    world.say(
        f"So {child.id} took one careful step, then another. "
        f"The gardenia stayed bright, and the path did not feel so long anymore."
    )
    world.say(
        f"When {child.id} reached {recipient.id}, {child.id} held out {flower.it()} and "
        f"said, 'I came back to fulfill my promise.'"
    )
    world.say(
        f"{recipient.id} smiled at the flower like it was a little piece of morning. "
        f"{helper.id} smiled too, and {child.id} stood a little straighter than before."
    )

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    task: Task = f["task"]  # type: ignore[assignment]
    return [
        f'Write a slice-of-life story for a young child about "{task.keyword}" and a promise.',
        f"Tell a gentle story where {child.id} tries to {task.verb} and hears the word 'wimp', but keeps going.",
        f'Write a warm, rhyming story that includes a gardenia, a small worry, and a kind helper.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    recipient: Entity = f["recipient"]  # type: ignore[assignment]
    task: Task = f["task"]  # type: ignore[assignment]
    flower: Entity = f["flower"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"What did {child.id} want to do with the gardenia?",
            answer=f"{child.id} wanted to {task.verb} and keep the promise.",
        ),
        QAItem(
            question=f"Who helped {child.id} when the word 'wimp' made {child.id} feel bad?",
            answer=f"{helper.id} walked beside {child.id} and gave kind words and a small rhyme.",
        ),
        QAItem(
            question=f"What did {child.id} bring to {recipient.id} at the end?",
            answer=f"{child.id} brought {flower.phrase} to {recipient.id}.",
        ),
        QAItem(
            question=f"How did {child.id} feel after fulfilling the promise?",
            answer=f"{child.id} felt prouder and steadier, because the hard part was done and the flower arrived safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gardenia?",
            answer="A gardenia is a flower with white petals and a sweet smell.",
        ),
        QAItem(
            question="What does it mean to fulfill a promise?",
            answer="To fulfill a promise means to do the thing you said you would do.",
        ),
        QAItem(
            question="What does the word wimp mean?",
            answer="Wimp is a hurtful word people use when they mean someone is scared or seems not brave, but being careful does not mean being weak.",
        ),
        QAItem(
            question="Why can a rhyme help someone feel better?",
            answer="A rhyme can feel steady and friendly, and it can make a hard moment seem smaller and easier to face.",
        ),
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="home", task="deliver", name="Mina", helper="Aunt Jo", recipient="Grandma", mood="hopeful"),
    StoryParams(setting="street", task="deliver", name="Owen", helper="Dad", recipient="Mrs. Vale", mood="nervous"),
    StoryParams(setting="garden", task="deliver", name="Iris", helper="Mom", recipient="the neighbor", mood="calm"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life gardenia storyworld with rhyme.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--recipient", choices=RECIPIENTS)
    ap.add_argument("--mood", choices=MOODS)
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
    if args.setting and args.task and (args.setting, args.task) not in valid_combos():
        raise StoryError("This setting cannot support that task.")
    setting = args.setting or rng.choice(list(SETTINGS))
    task = args.task or "deliver"
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    recipient = args.recipient or rng.choice(RECIPIENTS)
    mood = args.mood or rng.choice(MOODS)
    return StoryParams(setting=setting, task=task, name=name, helper=helper, recipient=recipient, mood=mood)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    world = tell(world, params)
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


def asp_program_for_show() -> str:
    return asp_program("#show valid_story/2.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_for_show())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(asp.atoms(model, "valid_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.setting}, {p.task}, {p.mood}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
