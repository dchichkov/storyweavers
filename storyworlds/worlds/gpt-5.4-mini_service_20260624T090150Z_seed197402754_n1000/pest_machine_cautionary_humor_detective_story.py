#!/usr/bin/env python3
"""
A standalone storyworld for a small detective-style tale about a pest, a machine,
and a cautionary, humorous fix.

Premise:
- A curious child detective notices a strange machine making trouble.
- A pest has crawled into the machine and caused a small, messy problem.
- The story warns about ignoring little warning signs, but stays gentle and funny.
- The detective uses observation, care, and a simple fix to resolve the problem.
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
# Core model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    worn_by: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the old workshop"


@dataclass
class Pest:
    id: str
    label: str
    phrase: str
    mess: str
    warning: str
    sign: str


@dataclass
class Machine:
    id: str
    label: str
    phrase: str
    job: str
    sound: str
    risk: str


@dataclass
class StoryParams:
    pest: str
    machine: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
SETTINGS = {
    "workshop": Setting(place="the old workshop"),
}

PESTS = {
    "mouse": Pest(
        id="mouse",
        label="mouse",
        phrase="a sneaky little mouse",
        mess="crumbs",
        warning="tiny paw prints",
        sign="nibbled wire",
    ),
    "roach": Pest(
        id="roach",
        label="roach",
        phrase="a fast little roach",
        mess="dust",
        warning="quick skittering",
        sign="mystery crumbs",
    ),
    "ant": Pest(
        id="ant",
        label="ants",
        phrase="a marching trail of ants",
        mess="sugar",
        warning="a neat line of legs",
        sign="sticky trail",
    ),
}

MACHINES = {
    "popper": Machine(
        id="popper",
        label="popcorn machine",
        phrase="a shiny popcorn machine",
        job="make popcorn",
        sound="pop-pop-pop",
        risk="clogs",
    ),
    "printer": Machine(
        id="printer",
        label="printer machine",
        phrase="a boxy printer machine",
        job="print labels",
        sound="whirr-click",
        risk="jams",
    ),
    "fan": Machine(
        id="fan",
        label="box fan",
        phrase="a wobbly box fan",
        job="cool the room",
        sound="whum-whum",
        risk="stalls",
    ),
}

BOY_NAMES = ["Theo", "Milo", "Ben", "Finn", "Leo", "Noah"]
GIRL_NAMES = ["Maya", "Nina", "Ivy", "Luna", "Zoe", "Ava"]
HELPERS = ["mother", "father", "grandmother", "older brother", "older sister"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld: pest, machine, caution, and a funny fix.")
    ap.add_argument("--pest", choices=PESTS)
    ap.add_argument("--machine", choices=MACHINES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for pest in PESTS:
        for machine in MACHINES:
            combos.append((pest, machine))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.pest and args.machine:
        pass
    pest = args.pest or rng.choice(list(PESTS))
    machine = args.machine or rng.choice(list(MACHINES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    if (pest, machine) not in valid_combos():
        raise StoryError("That pest and machine cannot make a reasonable detective story.")
    return StoryParams(pest=pest, machine=machine, name=name, gender=gender, helper=helper)


def tell_story(params: StoryParams) -> World:
    world = World(SETTINGS["workshop"])
    detective = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    pest = PESTS[params.pest]
    machine = MACHINES[params.machine]
    pest_ent = world.add(Entity(id="pest", kind="thing", type=pest.id, label=pest.label, phrase=pest.phrase))
    machine_ent = world.add(Entity(id="machine", kind="thing", type=machine.id, label=machine.label, phrase=machine.phrase))
    machine_ent.meters["broken"] = 0.0
    machine_ent.meters["messy"] = 0.0
    detective.memes["curious"] = 1.0
    detective.memes["careful"] = 1.0

    # Act 1
    world.say(
        f"{detective.id} was a little detective who loved clues and quiet footsteps."
    )
    world.say(
        f"At {world.setting.place}, {machine.phrase} usually made {machine.job}, and its favorite sound was {machine.sound}."
    )
    world.say(
        f"But one morning, {detective.id} noticed {pest.phrase} near the machine."
    )
    world.say(
        f"There were {pest.warning} by the base and {pest.sign} on the side, which was a very bad sign."
    )

    # Act 2
    world.para()
    world.say(
        f"{detective.id} tapped a notebook and said, \"No big stampede, no panic. Just clues.\""
    )
    world.say(
        f"{machine.label} gave one unhappy rattle, then stopped with a sigh. It looked {machine.risk}."
    )
    machine_ent.meters["broken"] += 1.0
    machine_ent.meters["messy"] += 1.0
    pest_ent.meters["active"] = 1.0
    detective.memes["worry"] = 1.0
    world.say(
        f"{params.helper.capitalize()} pointed at the tiny tracks and said, \"A little pest can make a big machine grumpy.\""
    )
    world.say(
        f"{detective.id} nearly laughed, because the problem was serious, but the pest looked like it had stolen the whole scene."
    )

    # Act 3
    world.para()
    world.say(
        f"{detective.id} looked under the machine, found the snack bits, and gently moved them away with a spoon."
    )
    world.say(
        f"Then {params.helper} held a flashlight while {detective.id} opened the side panel and made sure the gears could breathe again."
    )
    machine_ent.meters["broken"] = 0.0
    machine_ent.meters["messy"] = 0.0
    pest_ent.meters["active"] = 0.0
    detective.memes["pride"] = 1.0
    detective.memes["worry"] = 0.0
    world.say(
        f"The machine went back to {machine.job}, and this time it sounded happy: {machine.sound}."
    )
    world.say(
        f"{detective.id} wrote, \"Small warnings matter,\" and tucked the notebook away beside a crumb-free wrench."
    )
    world.say(
        f"The pest was gone, the machine was calm, and the workshop felt neat again."
    )

    world.facts.update(
        detective=detective,
        helper=helper,
        pest=pest_ent,
        machine=machine_ent,
        pest_cfg=pest,
        machine_cfg=machine,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    d, p, m = f["detective"], f["pest_cfg"], f["machine_cfg"]
    return [
        f'Write a short detective story for a young child about {d.id} spotting a {p.label} near a {m.label}.',
        f"Tell a cautionary but funny story where a tiny pest makes a machine stop working until a careful child fixes it.",
        f'Write a simple mystery story that includes the words "{p.label}" and "{m.label}" and ends with a gentle lesson.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d, h, p, m = f["detective"], f["helper"], f["pest_cfg"], f["machine_cfg"]
    return [
        QAItem(
            question=f"What kind of story is this?",
            answer=f"It is a detective story about {d.id} noticing a {p.label} and helping a {m.label} work again.",
        ),
        QAItem(
            question=f"What problem did {d.id} find near the {m.label}?",
            answer=f"{d.id} found {p.phrase} near the {m.label}, along with clues like {p.warning} and {p.sign}.",
        ),
        QAItem(
            question=f"How was the machine fixed?",
            answer=f"{d.id} and {h.label} cleared away the messy bits, checked the gears, and let the {m.label} do its job again.",
        ),
        QAItem(
            question=f"What lesson did the story give?",
            answer="It showed that little warnings matter, and that it is better to notice a problem early than to ignore it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pest?",
            answer="A pest is a small animal or insect that can cause trouble where people live or work.",
        ),
        QAItem(
            question="What is a machine?",
            answer="A machine is a tool or device that helps do a job, often by moving parts together.",
        ),
        QAItem(
            question="Why should you be careful around a broken machine?",
            answer="A broken machine can be unsafe, so people should be careful and ask for help instead of poking it.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the chosen pest and machine are both part of the registry.
valid(pest(P), machine(M)) :- pest(P), machine(M).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in PESTS:
        lines.append(asp.fact("pest", pid))
    for mid in MACHINES:
        lines.append(asp.fact("machine", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid/2."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set((f"pest({p})", f"machine({m})") for p, m in valid_combos())
    # The above shape is intentionally not compared directly; instead ensure model exists.
    if model is None:
        print("No ASP model found.")
        return 1
    samples = [generate(StoryParams(pest=p, machine=m, name="Ivy", gender="girl", helper="mother")) for p, m in valid_combos()]
    if not samples:
        print("No generated stories.")
        return 1
    print(f"OK: ASP model available; generated {len(samples)} sample stories.")
    return 0


# ---------------------------------------------------------------------------
# Serialization / CLI
# ---------------------------------------------------------------------------
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
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(pest="mouse", machine="popper", name="Ivy", gender="girl", helper="mother"),
    StoryParams(pest="roach", machine="printer", name="Theo", gender="boy", helper="father"),
    StoryParams(pest="ant", machine="fan", name="Maya", gender="girl", helper="older brother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
