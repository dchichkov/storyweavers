#!/usr/bin/env python3
"""
Standalone story world: peeve -> surprise -> transformation, with a comedic tone.

This world tells short, child-facing stories about a character who has a small
peeve about something ordinary, gets a surprise, and then watches the thing
transform into something funnier and more useful.

The story is driven by a tiny world model with physical meters and emotional
memes. The same world also emits an inline ASP twin for parity checks.
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
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    transformed_from: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Scenario:
    id: str
    peeve: str
    peeve_kind: str
    surprise: str
    transformation: str
    object_id: str
    object_label: str
    object_phrase: str
    transformed_label: str
    transformed_phrase: str
    setting: str
    clue: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        parts: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    parts.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            parts.append(" ".join(buf))
        return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "playroom": Setting("the playroom", indoors=True, affords={"box", "hat"}),
    "kitchen": Setting("the kitchen", indoors=True, affords={"spoon", "chair"}),
    "garden": Setting("the garden", indoors=False, affords={"umbrella", "wheelbarrow"}),
}

SCENARIOS = {
    "box_stage": Scenario(
        id="box_stage",
        peeve="the box was just plain and boring",
        peeve_kind="boring",
        surprise="a helper hid a tiny curtain inside the box",
        transformation="the box popped open and turned into a puppet stage",
        object_id="box",
        object_label="box",
        object_phrase="a plain cardboard box",
        transformed_label="puppet stage",
        transformed_phrase="a silly puppet stage with little red curtains",
        setting="playroom",
        clue="curtains",
    ),
    "hat_crown": Scenario(
        id="hat_crown",
        peeve="the hat kept flopping over their eyes",
        peeve_kind="awkward",
        surprise="a ribbon was tucked under the brim",
        transformation="the hat sprang up into a bright parade crown",
        object_id="hat",
        object_label="hat",
        object_phrase="a floppy old hat",
        transformed_label="parade crown",
        transformed_phrase="a bright parade crown with shiny paper stars",
        setting="playroom",
        clue="ribbon",
    ),
    "spoon_microphone": Scenario(
        id="spoon_microphone",
        peeve="the spoon made a dull clink in the bowl",
        peeve_kind="noisy",
        surprise="someone set a tinny little speaker beside the spoon",
        transformation="the spoon twirled and became a stage microphone",
        object_id="spoon",
        object_label="spoon",
        object_phrase="a plain silver spoon",
        transformed_label="microphone",
        transformed_phrase="a shiny toy microphone with a star on top",
        setting="kitchen",
        clue="speaker",
    ),
    "chair_rocker": Scenario(
        id="chair_rocker",
        peeve="the chair gave a squeaky little complaint every time they sat down",
        peeve_kind="squeaky",
        surprise="a cheerful spring was hiding under the seat",
        transformation="the chair bounced itself into a happy rocking chair",
        object_id="chair",
        object_label="chair",
        object_phrase="a stiff wooden chair",
        transformed_label="rocking chair",
        transformed_phrase="a happy rocking chair that bobbed like a duck",
        setting="kitchen",
        clue="spring",
    ),
    "umbrella_parasol": Scenario(
        id="umbrella_parasol",
        peeve="the umbrella dripped right onto their nose",
        peeve_kind="drippy",
        surprise="a painted flower was folded inside the umbrella",
        transformation="the umbrella twirled into a sunny parasol",
        object_id="umbrella",
        object_label="umbrella",
        object_phrase="a tired black umbrella",
        transformed_label="parasol",
        transformed_phrase="a sunny parasol with painted flowers",
        setting="garden",
        clue="flower",
    ),
}

NAMES = {
    "girl": ["Mia", "Nora", "Zoe", "Lily", "Ava"],
    "boy": ["Leo", "Finn", "Max", "Theo", "Ben"],
}
TRAITS = ["curious", "cheerful", "silly", "bouncy", "lively"]

GENDERS = ["girl", "boy"]
PARENTS = ["mother", "father"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    scenario: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _indefinite(text: str) -> str:
    return "an " + text if text[:1].lower() in "aeiou" else "a " + text


def _capitalize_first(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def _article_label(label: str) -> str:
    if label.startswith(("a ", "an ", "the ")):
        return label
    return _indefinite(label)


def _choose(seq: list[str], rng: random.Random) -> str:
    return rng.choice(seq)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, sc in SCENARIOS.items():
        if sc.setting in SETTINGS and sc.object_id in SETTINGS[sc.setting].affords:
            combos.append((sc.setting, sid))
    return combos


def explain_rejection(setting: str, scenario: str) -> str:
    sc = SCENARIOS[scenario]
    return (
        f"(No story: {sc.object_phrase} does not fit naturally in {SETTINGS[setting].place}. "
        f"Try a scene where that object belongs there.)"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    scenario = SCENARIOS[params.scenario]
    world = World(setting)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"calm": 1.0, "amusement": 0.0},
        memes={"peeve": 0.0, "surprise": 0.0, "delight": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=params.parent,
        meters={"calm": 1.0},
        memes={"warmth": 0.0},
    ))
    obj = world.add(Entity(
        id="object",
        kind="thing",
        type=scenario.object_id,
        label=scenario.object_label,
        phrase=scenario.object_phrase,
        owner=hero.id,
        meters={"plainness": 1.0},
        memes={"boring": 1.0},
    ))
    transformed = world.add(Entity(
        id="transformed",
        kind="thing",
        type=scenario.transformed_label,
        label=scenario.transformed_label,
        phrase=scenario.transformed_phrase,
        owner=hero.id,
        transformed_from=obj.id,
        meters={"fun": 0.0},
        memes={"wow": 0.0},
    ))

    world.facts.update(
        hero=hero, parent=parent, object=obj, transformed=transformed,
        scenario=scenario, params=params
    )

    world.say(
        f"{params.name} was a little {params.trait} {params.gender} who loved to poke around "
        f"{setting.place} and notice odd little things."
    )
    world.say(
        f"One day, {params.name} spotted {_article_label(scenario.object_phrase)} in {setting.place}."
    )
    world.say(
        f"But {params.name} had a tiny peeve: {scenario.peeve}."
    )
    hero.memes["peeve"] += 1.0

    world.para()
    world.say(
        f"Then came the surprise. {scenario.surprise.capitalize()}."
    )
    hero.memes["surprise"] += 1.0
    obj.meters["plainness"] = 0.0
    transformed.meters["fun"] = 1.0
    transformed.memes["wow"] = 1.0

    world.say(
        f"With a pop and a wobble, {scenario.transformation}."
    )
    hero.memes["peeve"] = 0.0
    hero.memes["delight"] += 1.0
    parent.memes["warmth"] += 1.0

    world.para()
    world.say(
        f"{params.name} laughed so hard that {params.name.lower()} snorted a little and had to sit down."
    )
    world.say(
        f"Now the {scenario.object_label} was not boring at all; it was {_article_label(scenario.transformed_label)}."
    )
    world.say(
        f"{params.name} and {params.parent} shared a grin, and the room felt much sillier than before."
    )

    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    sc: Scenario = f["scenario"]  # type: ignore[assignment]
    p: StoryParams = f["params"]  # type: ignore[assignment]
    return [
        f'Write a short comedy story for a young child about {p.name}, a peeve, a surprise, and a transformation in {SETTINGS[p.setting].place}.',
        f"Tell a funny story where {p.name} gets peeved by {sc.object_phrase}, then something unexpected changes it into {sc.transformed_phrase}.",
        f'Write a gentle, silly story that includes the word "peeve" and ends with {p.name} laughing at a transformed object.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    sc: Scenario = f["scenario"]  # type: ignore[assignment]
    p: StoryParams = f["params"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What tiny peeve did {p.name} have in {SETTINGS[p.setting].place}?",
            answer=f"{p.name} had a tiny peeve because {sc.peeve}.",
        ),
        QAItem(
            question=f"What surprise showed up before the object changed?",
            answer=f"The surprise was that {sc.surprise}.",
        ),
        QAItem(
            question=f"What did {sc.object_label} turn into?",
            answer=f"It turned into {sc.transformed_phrase}.",
        ),
        QAItem(
            question=f"How did {p.name} feel at the end?",
            answer=f"{p.name} felt delighted and laughed at the silly new {sc.transformed_label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a peeve?",
            answer="A peeve is a small thing that annoys someone a little bit.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that you did not know was coming.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="A transformation is a change where something becomes something else.",
        ),
        QAItem(
            question="Why can comedy be funny?",
            answer="Comedy is funny because it turns ordinary things into silly situations that make people laugh.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid_story(S, C) :- setting(S), scenario(C), compatible(S, C).
compatible(S, C) :- setting_scene(S, Obj), scenario_obj(C, Obj).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("setting_scene", sid, a))
    for cid, c in SCENARIOS.items():
        lines.append(asp.fact("scenario", cid))
        lines.append(asp.fact("scenario_obj", cid, c.object_id))
        lines.append(asp.fact("scenario_setting", cid, c.setting))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


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
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: peeve, surprise, transformation, comedy.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--scenario", choices=SCENARIOS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENTS)
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
    if args.setting and args.scenario:
        if (args.setting, args.scenario) not in combos:
            raise StoryError(explain_rejection(args.setting, args.scenario))

    filtered = [
        (s, c) for (s, c) in combos
        if (args.setting is None or s == args.setting)
        and (args.scenario is None or c == args.scenario)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")

    setting, scenario = rng.choice(sorted(filtered))
    sc = SCENARIOS[scenario]
    gender = args.gender or rng.choice(GENDERS)
    parent = args.parent or rng.choice(PARENTS)
    name = args.name or rng.choice(NAMES[gender])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, scenario=scenario, name=name, gender=gender, parent=parent, trait=trait)


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
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        if e.transformed_from:
            bits.append(f"transformed_from={e.transformed_from}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
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
    StoryParams(setting="playroom", scenario="box_stage", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(setting="kitchen", scenario="chair_rocker", name="Ben", gender="boy", parent="father", trait="silly"),
    StoryParams(setting="garden", scenario="umbrella_parasol", name="Nora", gender="girl", parent="mother", trait="bouncy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible setting/scenario combos:\n")
        for setting, scenario in triples:
            sc = SCENARIOS[scenario]
            print(f"  {setting:10} {scenario:16} -> {sc.object_phrase}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            except StoryError as e:
                print(e)
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
            header = f"### {p.name}: {p.scenario} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
