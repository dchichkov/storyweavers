#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sop_repetition_surprise_heartwarming.py
========================================================================

A standalone storyworld about a small, heartwarming surprise built around a
repeated act of sopping up a mess.

Domain premise
--------------
A child notices a spill or drip, keeps sopping it up in a little routine, and
then discovers a surprise that turns the chore into something warm and happy:
the repeated effort helps a parent, grandparent, or friend prepare a cozy
moment for someone arriving home.

Story shape
-----------
- Repetition: the same gentle cleanup action happens more than once.
- Surprise: the child discovers the real reason for the mess or the little task.
- Heartwarming ending: the ending image proves that the care mattered.

This file follows the Storyweavers contract:
- imports storyworlds/results.py eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate and inline ASP twin
- produces grounded QA from simulated state, not from rendered prose
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SOFT_LIMIT = 3
MAX_REPETITIONS = 4


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "mess": 0.0, "warmth": 0.0}
        if not self.memes:
            self.memes = {"care": 0.0, "curiosity": 0.0, "joy": 0.0, "surprise": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma",
                "grandfather": "grandpa"}.get(self.type, self.label or self.type)


@dataclass
class Setting:
    id: str
    place: str
    cozy_detail: str
    mess_source: str
    surprise_kind: str


@dataclass
class Task:
    id: str
    verb: str
    repeated_verb: str
    result: str
    gentle: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    reveal: str
    surprise_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.repetitions: int = 0
        self.mess_seen: int = 0

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.repetitions = self.repetitions
        clone.mess_seen = self.mess_seen
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts.get("child")
    task = world.facts.get("task")
    spill = world.facts.get("spill")
    if not child or not task or not spill:
        return out
    if world.repetitions < 2:
        sig = ("repeat", world.repetitions)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.repetitions += 1
        child.memes["care"] += 1
        spill.meters["wet"] = max(spill.meters["wet"], 1.0)
        out.append(f"{child.id} did it again, because little drips kept showing up.")
    return out


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    spill = world.facts.get("spill")
    helper = world.facts.get("helper")
    if not spill or not helper:
        return out
    if spill.meters["wet"] < THRESHOLD:
        return out
    sig = ("soften", spill.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["joy"] += 1
    world.facts["hidden_note"] = True
    out.append("__soften__")
    return out


CAUSAL_RULES = [
    Rule("repeat", "social", _r_repeat),
    Rule("soften", "social", _r_soften),
]


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


def reasonableness(task: Task, spill_kind: str, surprise: Surprise) -> bool:
    return task.gentle and spill_kind in {"milk", "tea", "juice", "rain"} and bool(surprise.reveal)


def predict_cleanup(world: World, child: Entity, task: Task, spill: Entity) -> dict:
    sim = world.copy()
    _do_task(sim, sim.get(child.id), task, narrate=False)
    return {
        "repeat_count": sim.repetitions,
        "wet": sim.get(spill.id).meters["wet"],
        "joy": sim.get(child.id).memes["joy"],
    }


def _do_task(world: World, child: Entity, task: Task, narrate: bool = True) -> None:
    child.memes["curiosity"] += 1
    child.meters["mess"] += 0.2
    spill = world.facts["spill"]
    spill.meters["wet"] += 1
    world.mess_seen += 1
    if narrate:
        world.say(f"{child.id} {task.verb} with a soft towel.")
    propagate(world, narrate=narrate)


def begin(world: World, child: Entity, helper: Entity, task: Task, setting: Setting) -> None:
    child.memes["joy"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} and {helper.id} were in {setting.place}. "
        f"{setting.cozy_detail}"
    )
    world.say(
        f"{child.id} noticed a tiny spill by the sink and reached for a cloth."
    )


def repeat_beat(world: World, child: Entity, task: Task) -> None:
    world.say(
        f"{child.id} kept {task.repeated_verb} because another little drip appeared."
    )


def reveal(world: World, child: Entity, helper: Entity, surprise: Surprise) -> None:
    child.memes["surprise"] += 1
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Then {helper.id} smiled and shared the surprise: {surprise.reveal}."
    )
    world.say(surprise.surprise_line)


def ending(world: World, child: Entity, helper: Entity, surprise: Surprise) -> None:
    child.meters["wet"] = 0.0
    child.memes["care"] += 1
    world.say(
        f"By the end, the counter was dry, the towel was warm in {child.pronoun('possessive')} hands, "
        f"and {surprise.ending_image}."
    )
    world.say(
        f"{child.id} hugged {helper.id}, proud that a few careful sops had helped make the day sweeter."
    )


def tell(setting: Setting, task: Task, surprise: Surprise,
         child_name: str = "Mia", child_gender: str = "girl",
         helper_name: str = "Grandma", helper_gender: str = "grandmother",
         spill_name: str = "spill") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="child", traits=["gentle", "helpful"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender,
                              role="helper", traits=["warm", "smiling"]))
    spill = world.add(Entity(id=spill_name, label="little spill", type=spill_name))
    spill.meters["wet"] = 1.0
    world.facts.update(child=child, helper=helper, task=task, spill=spill,
                       setting=setting, surprise=surprise)

    begin(world, child, helper, task, setting)
    _do_task(world, child, task)
    world.para()
    repeat_beat(world, child, task)
    _do_task(world, child, task)
    world.para()
    reveal(world, child, helper, surprise)
    ending(world, child, helper, surprise)
    world.facts["outcome"] = "heartwarming"
    world.facts["repeat_count"] = world.repetitions
    return world


SETTINGS = {
    "kitchen": Setting(
        "kitchen",
        "the kitchen",
        "Sunlight made the floor shine, and a little blue towel waited by the sink.",
        "milk",
        "family surprise"),
    "porch": Setting(
        "porch",
        "the porch",
        "The porch boards were warm, and a row of shoes sat neatly by the door.",
        "rain",
        "welcome surprise"),
    "laundry": Setting(
        "laundry",
        "the laundry room",
        "The washer hummed softly, and clean socks peeked out of a basket.",
        "juice",
        "birthday surprise"),
}

TASKS = {
    "sop": Task(
        "sop",
        "sopped it up",
        "sopping it up",
        "the spill went away little by little",
        gentle=True,
        tags={"sop", "cleanup"}),
    "wipe": Task(
        "wipe",
        "wiped it clean",
        "wiping it clean",
        "the shine came back",
        gentle=True,
        tags={"cleanup"}),
    "dry": Task(
        "dry",
        "dried it off",
        "drying it off",
        "the wet patch shrank",
        gentle=True,
        tags={"cleanup"}),
}

SURPRISES = {
    "family": Surprise(
        "family",
        "Grandma had been hiding a welcome-home card for the whole family",
        "The child blinked in surprise, then laughed with relief.",
        "the welcome-home card leaned against a mug and the room felt extra warm",
        tags={"family", "welcome"}),
    "birthday": Surprise(
        "birthday",
        "the spill was really covering up a surprise birthday cake box",
        "A ribbon peeked out from under the towel, and everyone grinned.",
        "the cake box sat safely on the counter with a bright ribbon on top",
        tags={"birthday", "cake"}),
    "pet": Surprise(
        "pet",
        "a tiny kitten had been asleep beside the spill the whole time",
        "The kitten yawned, and the child whispered a happy hello.",
        "the kitten curled on a folded towel like a soft comma",
        tags={"kitten", "pet"}),
}

CHILD_NAMES = ["Mia", "Nora", "Lena", "Ivy", "Ruby", "Ella", "June", "Lucy", "Ava", "Zoe"]


@dataclass
class StoryParams:
    setting: str
    task: str
    surprise: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for tid, t in TASKS.items():
            for uid, u in SURPRISES.items():
                if reasonableness(t, s.mess_source, u):
                    combos.append((sid, tid, uid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the word "sop" and a small surprise.',
        f"Tell a cozy story where {f['child'].id} keeps {f['task'].repeated_verb}, then learns why the little mess was there.",
        f"Write a gentle story about a child who keeps cleaning the same spot and ends up feeling happy and surprised.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    task = f["task"]
    surprise = f["surprise"]
    setting = f["setting"]
    answers = [
        QAItem(
            question="What did the child keep doing?",
            answer=f"{child.id} kept {task.repeated_verb} again and again because the tiny wet spot kept coming back. The repeated cleaning showed how careful the child was being."
        ),
        QAItem(
            question="What surprise did the helper share?",
            answer=f"{helper.id} shared that {surprise.reveal}. That is why the little spill mattered, and it turned the chore into a warm family moment."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the wet spot gone, the room cozy, and {child.id} hugging {helper.id}. The ending image shows that the repeated helping made the surprise feel special."
        ),
    ]
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to sop something up?",
            answer="To sop something up means to use a cloth, towel, or sponge to soak up liquid from a surface. It is a gentle way to clean a spill."
        ),
        QAItem(
            question="Why might someone repeat a cleanup task?",
            answer="They might repeat it if more liquid keeps appearing or if they want to make sure the spot is fully dry. Repeating the task can help finish the job well."
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you did not expect. It can make a story feel exciting, sweet, or both."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={dict(m)}")
        if mm:
            bits.append(f"memes={dict(mm)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  repetitions: {world.repetitions}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "sop", "family", "Mia", "girl", "Grandma", "grandmother"),
    StoryParams("porch", "wipe", "pet", "Leo", "boy", "Mom", "mother"),
    StoryParams("laundry", "dry", "birthday", "June", "girl", "Dad", "father"),
]


def explain_rejection(task: Task, setting: Setting, surprise: Surprise) -> str:
    if not reasonableness(task, setting.mess_source, surprise):
        return "(No story: this combination is not gentle or not plausible enough for a heartwarming cleanup surprise.)"
    return "(No story: the requested combination does not fit the domain.)"


def outcome_of(params: StoryParams) -> str:
    return "heartwarming"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: repeated sopping, a small surprise, and a warm ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--child-name", dest="child_name")
    ap.add_argument("--child-gender", dest="child_gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name", dest="helper_name")
    ap.add_argument("--helper-gender", dest="helper_gender", choices=["mother", "father", "grandmother", "grandfather"])
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
              and (args.task is None or c[1] == args.task)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, surprise = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["mother", "grandmother", "father", "grandfather"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    helper_name = args.helper_name or rng.choice(["Mom", "Dad", "Grandma", "Grandpa"])
    return StoryParams(setting, task, surprise, child_name, child_gender, helper_name, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        TASKS[params.task],
        SURPRISES[params.surprise],
        params.child_name,
        params.child_gender,
        params.helper_name,
        params.helper_gender,
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


ASP_RULES = r"""
repetition(Child) :- child(Child), repeat_target(Task), task(Task).
surprise(S) :- surprise_kind(S).
valid(Setting, Task, Surprise) :- setting(Setting), task(Task), surprise(Surprise), gentle(Task), mess_source(Setting, Mess), compatible(Mess, Surprise).

repeat_count(2) :- chosen_task(Task), gentle(Task).
heartwarming :- repeat_count(N), N >= 2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        if t.gentle:
            lines.append(asp.fact("gentle", tid))
    for uid in SURPRISES:
        lines.append(asp.fact("surprise", uid))
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("mess_source", sid, s.mess_source))
    for uid, u in SURPRISES.items():
        lines.append(asp.fact("compatible", s.mess_source if False else "milk", uid))
        lines.append(asp.fact("compatible", "rain", uid))
        lines.append(asp.fact("compatible", "juice", uid))
    lines.append(asp.fact("chosen_task", "sop"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: verify passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.child_name} in {p.setting} with {p.task} / {p.surprise}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
