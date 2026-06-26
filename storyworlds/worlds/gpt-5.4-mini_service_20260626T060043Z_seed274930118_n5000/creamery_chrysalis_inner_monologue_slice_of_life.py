#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/creamery_chrysalis_inner_monologue_slice_of_life.py
================================================================================================

A small standalone storyworld for a slice-of-life creamery scene with a chrysalis
by the window and a child whose inner monologue helps carry the moment forward.

Seed premise:
---
A child visits a creamery, notices a chrysalis near the sunny window, and wants
to enjoy a treat without making a fuss. The child keeps thinking to themself
about the little changes happening in the chrysalis, and the quiet thoughtfulness
of the room turns into a gentle, satisfying ending.

World model:
---
- Physical meters track hunger, sweetness, warmth, quiet, drip, and chrysalis progress.
- Emotional memes track curiosity, worry, patience, tenderness, and wonder.
- The child’s inner monologue is part of the narration and is state-driven:
  curiosity and patience shape what they notice and how they act.
- The chrysalis changes only when the room stays warm and calm enough.

Contract notes:
---
- Standard storyworld interface: StoryParams, registries, build_parser,
  resolve_params, generate, emit, main.
- Shared result containers are imported eagerly from storyworlds/results.py.
- ASP helper import is lazy and used only in ASP helpers.
- --verify checks Python/ASP parity and exercises generated stories.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    place: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "woman"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "man"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Creamery:
    name: str = "the creamery"
    window: str = "sunny window"
    table: str = "small table"
    affords: set[str] = field(default_factory=lambda: {"watch", "eat", "sip"})


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    kind: str
    messy: bool
    cold: bool
    spoonable: bool
    sweetness: str
    drip_risk: float
    comfort: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    treat: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


NAMES_GIRL = ["Mia", "Lily", "Nora", "Ada", "June", "Ivy", "Zoe", "Maya"]
NAMES_BOY = ["Theo", "Leo", "Ben", "Max", "Eli", "Finn", "Noah", "Owen"]
TRAITS = ["curious", "gentle", "patient", "quiet", "bright", "thoughtful"]


CREAMERY = Creamery()

TREATS = {
    "cone": Treat(
        id="cone",
        label="waffle cone",
        phrase="a waffle cone with a scoop of vanilla",
        kind="cone",
        messy=True,
        cold=True,
        spoonable=False,
        sweetness="sweet",
        drip_risk=1.0,
        comfort="The cone was crunchy and fun to hold.",
        tags={"icecream", "cone", "sweet"},
    ),
    "cup": Treat(
        id="cup",
        label="paper cup",
        phrase="a paper cup with a scoop of strawberry ice cream",
        kind="cup",
        messy=False,
        cold=True,
        spoonable=True,
        sweetness="sweet",
        drip_risk=0.2,
        comfort="The cup kept the drips tucked in safely.",
        tags={"icecream", "cup", "sweet"},
    ),
    "sundae": Treat(
        id="sundae",
        label="small sundae",
        phrase="a small sundae with one cherry on top",
        kind="sundae",
        messy=True,
        cold=True,
        spoonable=True,
        sweetness="extra sweet",
        drip_risk=0.6,
        comfort="The spoon made each bite slow and neat.",
        tags={"icecream", "sundae", "sweet"},
    ),
    "milkshake": Treat(
        id="milkshake",
        label="milkshake",
        phrase="a milkshake with a paper straw",
        kind="milkshake",
        messy=False,
        cold=True,
        spoonable=False,
        sweetness="sweet and creamy",
        drip_risk=0.1,
        comfort="The straw made the sipping steady and quiet.",
        tags={"milkshake", "sweet"},
    ),
}

CURATED = [
    StoryParams(treat="cup", name="Mia", gender="girl", parent="mother", trait="gentle"),
    StoryParams(treat="sundae", name="Theo", gender="boy", parent="father", trait="curious"),
    StoryParams(treat="milkshake", name="June", gender="girl", parent="mother", trait="quiet"),
    StoryParams(treat="cone", name="Leo", gender="boy", parent="father", trait="thoughtful"),
]


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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
        import copy as _copy
        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _set_meter(e: Entity, key: str, delta: float) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + delta


def _set_meme(e: Entity, key: str, delta: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + delta


def _drip_rule(world: World) -> list[str]:
    out = []
    child = world.get("child")
    treat = world.get("treat")
    if child.meters.get("eaten", 0.0) >= THRESHOLD:
        return out
    if treat.meters.get("drip", 0.0) >= THRESHOLD and treat.meters.get("held", 0.0) >= THRESHOLD:
        sig = "drip"
        if sig in world.fired:
            return out
        world.fired.add(sig)
        _set_meter(world.get("table"), "sticky", 1.0)
        out.append("A little drip reached the table and made the paper napkin stick.")
    return out


def _calm_chrysalis_rule(world: World) -> list[str]:
    out = []
    chrys = world.get("chrysalis")
    if chrys.meters.get("warmth", 0.0) >= THRESHOLD and chrys.meters.get("quiet", 0.0) >= THRESHOLD:
        if chrys.meters.get("progress", 0.0) < 2.0:
            sig = f"progress-{int(chrys.meters.get('progress', 0.0))}"
            if sig in world.fired:
                return out
            world.fired.add(sig)
            chrys.meters["progress"] = chrys.meters.get("progress", 0.0) + 1.0
            if chrys.meters["progress"] >= 2.0:
                out.append("Inside the chrysalis, something ready and bright was almost finished.")
            else:
                out.append("The chrysalis gave the tiniest shiver in the warm, quiet window.")
    return out


CAUSAL_RULES = [_drip_rule, _calm_chrysalis_rule]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    for line in produced:
        world.say(line)
    return produced


def inner_monologue(child: Entity, thought: str) -> str:
    return f"*{thought}*"


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent))
    treat = world.add(Entity(id="treat", kind="thing", type=TREATS[params.treat].kind, label=TREATS[params.treat].label))
    chrys = world.add(Entity(id="chrysalis", kind="thing", type="chrysalis", label="chrysalis", place=CREAMERY.window))
    table = world.add(Entity(id="table", kind="thing", type="table", label="table"))
    child.meters.update(hunger=1.0, calm=0.0)
    child.memes.update(curiosity=1.0, worry=0.0, patience=1.0, wonder=0.0, tenderness=0.0)
    parent.memes.update(care=1.0, patience=1.0)
    treat.meters.update(held=1.0, drip=0.0, eaten=0.0)
    chrys.meters.update(progress=0.0, warmth=1.0, quiet=0.0)

    treat_def = TREATS[params.treat]

    world.say(f"{params.name} stepped into {CREAMERY.name} and looked right past the menu.")
    world.say(f"Near the {CREAMERY.window}, a small {chrys.label} hung still like a secret.")
    world.say(
        f"{params.name} thought, {inner_monologue(child, 'Maybe I can finish my treat and still keep an eye on that tiny cocoon.')}"
    )
    world.say(f"{params.name} asked for {treat_def.phrase}. {treat_def.comfort}")

    world.para()
    world.say(f"{params.name} carried the treat to the {CREAMERY.table}, where the window light felt soft and warm.")
    _set_meter(chrys, "quiet", 1.0)
    _set_meter(child, "calm", 1.0)
    _set_meme(child, "patience", 0.5)
    _set_meme(child, "wonder", 0.5)
    world.say(
        f"{params.name} thought, {inner_monologue(child, 'If I take small bites, the room will stay calm, and maybe the chrysalis will feel safe enough to change.')}"
    )
    if treat_def.messy and treat_def.drip_risk >= 0.5:
        _set_meter(treat, "drip", 1.0)
    if treat_def.spoonable:
        _set_meter(treat, "held", 0.0)
        _set_meter(treat, "eaten", 1.0)
        _set_meter(child, "hunger", -1.0)
        world.say(f"{params.name} used a spoon and ate slowly, so nothing rushed or spilled.")
    else:
        _set_meter(treat, "drip", 0.5)
        _set_meter(child, "hunger", -0.7)
        world.say(f"{params.name} took careful bites, and only a few sweet crumbs wandered onto the plate.")
    _set_meter(chrys, "warmth", 1.0)
    propagate(world)

    world.para()
    if chrys.meters.get("progress", 0.0) >= 1.0:
        world.say(
            f"{params.name} glanced up and thought, {inner_monologue(child, 'It moved a little. I think it noticed the quiet too.')}"
        )
    if chrys.meters.get("progress", 0.0) >= 2.0:
        world.say(
            f"By the time the cup was nearly empty, the chrysalis had become a butterfly, and the new wings were still drying by the glass."
        )
        _set_meme(child, "joy", 1.0)
        _set_meme(child, "tenderness", 1.0)
    else:
        world.say(
            f"By the time {params.name} finished the last bite, the chrysalis still looked close, round, and patient."
        )
        _set_meme(child, "tenderness", 0.5)

    world.say(
        f"{params.name} smiled, because a small treat, a quiet room, and one waiting chrysalis made the whole afternoon feel kind."
    )

    world.facts.update(
        child=child,
        parent=parent,
        treat=treat,
        chrysalis=chrys,
        table=table,
        params=params,
        treat_def=treat_def,
        creamery=CREAMERY,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    treat: Treat = f["treat_def"]
    return [
        f'Write a slice-of-life story for a young child at a creamery, with a chrysalis near the window and the word "{treat.id}".',
        f"Tell a gentle story where {params.name} thinks to themself about a chrysalis while eating {treat.phrase}.",
        "Write a short, child-friendly story about a quiet afternoon in a creamery, with inner monologue and a small change at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = f["params"]
    treat: Treat = f["treat_def"]
    child: Entity = f["child"]
    chrys: Entity = f["chrysalis"]
    answers = []
    answers.append(QAItem(
        question=f"What was {params.name} doing at the creamery?",
        answer=f"{params.name} was enjoying {treat.phrase} while sitting near the sunny window and watching the chrysalis."
    ))
    answers.append(QAItem(
        question=f"What did {params.name} think about while eating?",
        answer=f"{params.name} thought about the tiny chrysalis, the quiet room, and how small careful bites could keep the afternoon calm."
    ))
    if chrys.meters.get("progress", 0.0) >= 2.0:
        answers.append(QAItem(
            question="What changed by the end of the story?",
            answer="The chrysalis finished changing into a butterfly, and the child got to see the new wings by the window."
        ))
    else:
        answers.append(QAItem(
            question="What was special about the chrysalis at the end?",
            answer="It was still waiting, but it looked calm and close to changing."
        ))
    answers.append(QAItem(
        question=f"How did {params.name} feel in the creamery?",
        answer=f"{params.name} felt curious, patient, and happy, like the room itself was taking a quiet breath."
    ))
    return answers


WORLD_QA = [
    QAItem(question="What is a creamery?", answer="A creamery is a place where people buy and eat cold, creamy treats like ice cream."),
    QAItem(question="What is a chrysalis?", answer="A chrysalis is a protective case where a butterfly changes before it comes out."),
    QAItem(question="Why does a calm room matter for a chrysalis?", answer="A calm room keeps the little chrysalis undisturbed while the insect changes safely inside."),
    QAItem(question="What is a sundae?", answer="A sundae is a sweet ice cream treat often served with toppings."),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    treat: Treat = f["treat_def"]
    out = list(WORLD_QA)
    if treat.id == "cone":
        out.append(QAItem(question="What makes a waffle cone fun?", answer="A waffle cone is crunchy and easy to hold, so it feels playful to eat."))
    elif treat.id == "cup":
        out.append(QAItem(question="Why use a paper cup for ice cream?", answer="A paper cup helps catch drips and makes a treat easier to eat neatly."))
    elif treat.id == "milkshake":
        out.append(QAItem(question="Why do people use a straw for a milkshake?", answer="A straw makes it easy to sip a milkshake slowly without making a mess."))
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
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.place:
            bits.append(f"place={e.place}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def validate_treat(treat_id: str) -> None:
    if treat_id not in TREATS:
        raise StoryError(f"Unknown treat: {treat_id}")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.treat:
        validate_treat(args.treat)
    treat_id = args.treat or rng.choice(sorted(TREATS))
    trait = args.trait or rng.choice(TRAITS)
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = NAMES_GIRL if gender == "girl" else NAMES_BOY
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(treat=treat_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("place", "creamery"))
    lines.append(asp.fact("affords", "creamery", "watch"))
    lines.append(asp.fact("affords", "creamery", "eat"))
    lines.append(asp.fact("affords", "creamery", "sip"))
    lines.append(asp.fact("object", "chrysalis"))
    lines.append(asp.fact("object", "treat"))
    for tid, tr in TREATS.items():
        lines.append(asp.fact("treat", tid))
        lines.append(asp.fact("sweetness", tid, tr.sweetness))
        if tr.messy:
            lines.append(asp.fact("messy", tid))
        if tr.spoonable:
            lines.append(asp.fact("spoonable", tid))
        if tr.cold:
            lines.append(asp.fact("cold", tid))
        if tr.drip_risk >= 0.5:
            lines.append(asp.fact("drippy", tid))
        for tag in sorted(tr.tags):
            lines.append(asp.fact("tagged", tid, tag))
    lines.append(asp.fact("thing", "chrysalis"))
    lines.append(asp.fact("changeable", "chrysalis"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_treat(T) :- treat(T), cold(T).
quiet_treat(T) :- valid_treat(T), (spoonable(T); not messy(T)).
compatible(T) :- valid_treat(T), (spoonable(T); drippy(T)).
story_choice(T) :- compatible(T), tagged(T, sweet).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_treats() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_treat/1."))
    return sorted(set(asp.atoms(model, "valid_treat")))


def asp_story_choices() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_choice/1."))
    return sorted(set(asp.atoms(model, "story_choice")))


def asp_verify() -> int:
    py = sorted((tid,) for tid, t in TREATS.items() if t.cold)
    cl = asp_valid_treats()
    if set(py) != set(cl):
        print("MISMATCH between clingo and Python valid treats:")
        print("  python:", py)
        print("  clingo:", cl)
        return 1
    print(f"OK: clingo gate matches Python ({len(py)} valid treats).")
    sample = generate(StoryParams(treat="cup", name="Mia", gender="girl", parent="mother", trait="gentle"))
    if not sample.story or "chrysalis" not in sample.story:
        print("MISMATCH: generated story missing expected content.")
        return 1
    print("OK: generated story exercise passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life creamery storyworld with a chrysalis and inner monologue."
    )
    ap.add_argument("--treat", choices=sorted(TREATS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show story_choice/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(f"{len(asp_valid_treats())} valid treats; story choices: {len(asp_story_choices())}")
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
            header = f"### {p.name}: {p.treat}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
