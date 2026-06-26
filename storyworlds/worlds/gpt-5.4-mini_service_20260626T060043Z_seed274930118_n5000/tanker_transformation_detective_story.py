#!/usr/bin/env python3
"""
storyworlds/worlds/tanker_transformation_detective_story.py
===========================================================

A small detective-style storyworld about a tanker, a clue trail, and a
transformation.

Seed premise:
A young detective notices that a tanker at the harbor is not looking like
it used to. The clues point to rust, soot, and an old coat of paint. The
detective follows the evidence, finds the right tools, and helps the tanker
transform into a bright, proud ship again.

The story is driven by world state:
- physical meters: rust, soot, shine, paint, clean, hull_repaired
- emotional memes: worry, curiosity, pride, relief, trust

The "mystery" is not a frozen paragraph: clues are discovered from the
simulated harbor, the tanker changes as the case advances, and the ending
image proves the transformation.
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
# Domain registries
# ---------------------------------------------------------------------------

SETTING_REGISTRY = {
    "harbor": {
        "label": "the harbor",
        "noise": "The harbor was full of gulls, ropes, and gentle waves.",
        "affords": {"inspection", "transformation"},
    },
    "shipyard": {
        "label": "the shipyard",
        "noise": "The shipyard smelled like salt, paint, and wet wood.",
        "affords": {"inspection", "transformation"},
    },
    "riverdock": {
        "label": "the river dock",
        "noise": "The river dock sat quiet, with water tapping softly against the posts.",
        "affords": {"inspection", "transformation"},
    },
}

DETECTIVE_REGISTRY = {
    "milo": {
        "name": "Milo",
        "role": "detective",
        "gender": "boy",
        "traits": ["careful", "curious"],
    },
    "ella": {
        "name": "Ella",
        "role": "detective",
        "gender": "girl",
        "traits": ["sharp", "patient"],
    },
    "nina": {
        "name": "Nina",
        "role": "detective",
        "gender": "girl",
        "traits": ["brave", "observant"],
    },
}

TANKER_REGISTRY = {
    "oil_tanker": {
        "label": "tanker",
        "kind": "oil tanker",
        "phrase": "a big gray tanker with a long hull",
        "cargo": "oil",
        "old_look": "dull and rusty",
        "new_look": "bright and smooth",
        "problem": "rust stains and soot",
        "fix": "fresh paint and a careful polish",
    },
    "water_tanker": {
        "label": "tanker",
        "kind": "water tanker",
        "phrase": "a sturdy tanker with round windows",
        "cargo": "fresh water",
        "old_look": "faded and dusty",
        "new_look": "clean and shiny",
        "problem": "dust and worn paint",
        "fix": "soap, water, and a new coat of paint",
    },
    "fuel_tanker": {
        "label": "tanker",
        "kind": "fuel tanker",
        "phrase": "a long tanker with red stripes",
        "cargo": "fuel",
        "old_look": "smudged and tired",
        "new_look": "gleaming and proud",
        "problem": "smudges and peeling paint",
        "fix": "washing, patching, and bright paint",
    },
}

TOOLS_REGISTRY = {
    "brush": {
        "label": "paint brush",
        "verb": "brush",
        "purpose": "spread the paint evenly",
    },
    "cloth": {
        "label": "polishing cloth",
        "verb": "polish",
        "purpose": "wipe away the grime",
    },
    "hose": {
        "label": "water hose",
        "verb": "wash",
        "purpose": "clear away dust and soot",
    },
    "patch": {
        "label": "patch kit",
        "verb": "patch",
        "purpose": "cover small worn spots",
    },
}

# ---------------------------------------------------------------------------
# Shared world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        gender = self.type
        if gender == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    setting: str
    detective: Entity
    tanker: Entity
    tool: Entity
    clues: list[str] = field(default_factory=list)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    detective: str
    tanker: str
    transformation: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def setting_label(setting: str) -> str:
    return SETTING_REGISTRY[setting]["label"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting, s in SETTING_REGISTRY.items():
        if "transformation" not in s["affords"]:
            continue
        for detective in DETECTIVE_REGISTRY:
            for tanker in TANKER_REGISTRY:
                combos.append((setting, detective, tanker))
    return combos


def choose_tool(tanker_id: str) -> str:
    if tanker_id == "oil_tanker":
        return "cloth"
    if tanker_id == "water_tanker":
        return "hose"
    return "brush"


def build_world(params: StoryParams) -> World:
    dcfg = DETECTIVE_REGISTRY[params.detective]
    tcfg = TANKER_REGISTRY[params.tanker]
    tool_id = choose_tool(params.tanker)
    tool_cfg = TOOLS_REGISTRY[tool_id]

    detective = Entity(
        id=dcfg["name"],
        kind="character",
        label="detective",
        type=dcfg["gender"],
        traits=list(dcfg["traits"]),
        meters={"curiosity": 1.0},
        memes={"curiosity": 1.0, "care": 1.0},
    )
    tanker = Entity(
        id="tanker",
        kind="thing",
        label="tanker",
        phrase=tcfg["phrase"],
        type=tcfg["kind"],
        meters={
            "rust": 2.0,
            "soot": 1.0,
            "shine": 0.5,
            "paint": 0.2,
            "hull_repaired": 0.0,
        },
        memes={"worry": 1.0, "trust": 0.0, "pride": 0.0, "relief": 0.0},
    )
    tool = Entity(
        id=tool_id,
        kind="thing",
        label=tool_cfg["label"],
        type="tool",
        phrase=tool_cfg["purpose"],
        meters={},
        memes={},
    )
    return World(setting=params.setting, detective=detective, tanker=tanker, tool=tool)


def inspect_clues(world: World) -> None:
    tanker = world.tanker
    clues: list[str] = []
    if tanker.meters["rust"] >= 1.5:
        clues.append("rust along the lower side")
    if tanker.meters["soot"] >= 0.5:
        clues.append("dark soot near the funnel")
    if tanker.meters["paint"] < 0.5:
        clues.append("peeling paint on the deck rail")
    world.clues = clues
    world.facts["clues"] = list(clues)


def clean_and_transform(world: World) -> None:
    tanker = world.tanker
    tool = world.tool

    if tool.id == "cloth":
        tanker.meters["soot"] = max(0.0, tanker.meters["soot"] - 1.0)
        tanker.meters["rust"] = max(0.0, tanker.meters["rust"] - 0.5)
        tanker.meters["shine"] += 0.8
    elif tool.id == "hose":
        tanker.meters["soot"] = max(0.0, tanker.meters["soot"] - 0.8)
        tanker.meters["shine"] += 0.6
    else:
        tanker.meters["rust"] = max(0.0, tanker.meters["rust"] - 0.7)
        tanker.meters["paint"] += 0.9

    tanker.meters["paint"] += 1.0
    tanker.meters["hull_repaired"] = 1.0
    tanker.meters["shine"] = max(tanker.meters["shine"], 1.5)
    tanker.memes["worry"] = 0.0
    tanker.memes["trust"] = 1.0
    tanker.memes["pride"] = 1.0
    tanker.memes["relief"] = 1.0


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTING_REGISTRY:
        raise StoryError("Unknown setting.")
    if params.detective not in DETECTIVE_REGISTRY:
        raise StoryError("Unknown detective.")
    if params.tanker not in TANKER_REGISTRY:
        raise StoryError("Unknown tanker.")
    if params.transformation != "transformation":
        raise StoryError("This world only supports the transformation premise.")
    if "transformation" not in SETTING_REGISTRY[params.setting]["affords"]:
        raise StoryError("That setting cannot host the transformation story.")


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.

setting(harbor).
setting(shipyard).
setting(riverdock).

affords(harbor,transformation).
affords(shipyard,transformation).
affords(riverdock,transformation).

detective(milo).
detective(ella).
detective(nina).

tanker(oil_tanker).
tanker(water_tanker).
tanker(fuel_tanker).

valid(S,D,T) :- setting(S), affords(S,transformation), detective(D), tanker(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTING_REGISTRY:
        lines.append(asp.fact("setting", s))
        for a in sorted(SETTING_REGISTRY[s]["affords"]):
            lines.append(asp.fact("affords", s, a))
    for d in DETECTIVE_REGISTRY:
        lines.append(asp.fact("detective", d))
    for t in TANKER_REGISTRY:
        lines.append(asp.fact("tanker", t))
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
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Narrative
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    world = build_world(params)
    detective = world.detective
    tanker = world.tanker
    tool = world.tool
    cfg = TANKER_REGISTRY[params.tanker]

    world.say(
        f"{detective.id} was a {detective.traits[0]} detective who liked quiet clues and tidy answers."
    )
    world.say(
        f"One morning at {setting_label(params.setting)}, {detective.id} spotted the {tanker.label}."
        f" {tanker.phrase.capitalize()} looked {cfg['old_look']}."
    )
    world.say(
        f"{detective.id} knelt to look closer. The case had signs: {cfg['problem']}."
    )

    world.para()
    inspect_clues(world)
    clue_text = ", ".join(world.clues)
    world.say(
        f"{detective.id} followed the clues and found {clue_text}."
    )
    world.say(
        f"That pointed to the right tool: a {tool.label} made to {tool.phrase}."
    )

    world.para()
    world.say(
        f"{detective.id} worked carefully with the {tool.label}."
    )
    if tool.id == "cloth":
        world.say("The cloth wiped away soot, and the tanker's side began to gleam.")
    elif tool.id == "hose":
        world.say("The hose washed off the dust, and the tanker stopped looking tired.")
    else:
        world.say("The brush spread fresh paint across the worn places like a new coat of morning.")
    clean_and_transform(world)
    world.say(
        f"At last, the {tanker.label} had changed from {cfg['old_look']} to {cfg['new_look']}."
    )
    world.say(
        f"{tanker.label.capitalize()} {tanker.phrase} now looked ready for the water again."
    )

    world.facts.update(
        setting=params.setting,
        detective=detective,
        tanker=tanker,
        tool=tool,
        transformation=params.transformation,
        tanker_cfg=cfg,
        clues=list(world.clues),
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    d = f["detective"]
    cfg = f["tanker_cfg"]
    return [
        "Write a gentle detective story about a tanker that changes from worn-out to bright again.",
        f"Tell a child-friendly mystery where {d.id} follows clues about {cfg['problem']} on a tanker.",
        f"Write a short story in detective style where a tanker gets {cfg['fix']} and ends looking {cfg['new_look']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    d = world.detective
    t = world.tanker
    cfg = world.facts["tanker_cfg"]
    place = setting_label(world.facts["setting"])
    clue_text = ", ".join(world.clues)
    return [
        QAItem(
            question=f"Who solved the mystery at {place}?",
            answer=f"{d.id} solved it by following the clues and helping the tanker change.",
        ),
        QAItem(
            question=f"What clues did {d.id} notice on the tanker?",
            answer=f"{d.id} noticed {clue_text}, which pointed to the tanker needing care.",
        ),
        QAItem(
            question=f"What changed about the tanker by the end?",
            answer=f"The tanker changed from {cfg['old_look']} to {cfg['new_look']}.",
        ),
        QAItem(
            question=f"Why did the tanker need help in the first place?",
            answer=f"It needed help because it had {cfg['problem']} and looked worn out.",
        ),
        QAItem(
            question=f"What did the detective use to fix the tanker?",
            answer=f"{d.id} used a {world.tool.label} so the tanker could get {cfg['fix']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tanker?",
            answer="A tanker is a ship that carries liquids like oil or water in large tanks.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, thinks carefully, and tries to solve a mystery.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a new form or looks different from before.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    for e in [world.detective, world.tanker, world.tool]:
        lines.append(
            f"{e.id}: meters={{{', '.join(f'{k}: {v:.1f}' for k, v in e.meters.items())}}} "
            f"memes={{{', '.join(f'{k}: {v:.1f}' for k, v in e.memes.items())}}}"
        )
    lines.append(f"clues={world.clues}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="harbor", detective="milo", tanker="oil_tanker", transformation="transformation"),
    StoryParams(setting="shipyard", detective="ella", tanker="water_tanker", transformation="transformation"),
    StoryParams(setting="riverdock", detective="nina", tanker="fuel_tanker", transformation="transformation"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld: a tanker transformation mystery.")
    ap.add_argument("--setting", choices=sorted(SETTING_REGISTRY))
    ap.add_argument("--detective", choices=sorted(DETECTIVE_REGISTRY))
    ap.add_argument("--tanker", choices=sorted(TANKER_REGISTRY))
    ap.add_argument("--transformation", default="transformation", choices=["transformation"])
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
    setting = args.setting or rng.choice(sorted(SETTING_REGISTRY))
    detective = args.detective or rng.choice(sorted(DETECTIVE_REGISTRY))
    tanker = args.tanker or rng.choice(sorted(TANKER_REGISTRY))
    transformation = args.transformation or "transformation"

    params = StoryParams(
        setting=setting,
        detective=detective,
        tanker=tanker,
        transformation=transformation,
    )
    reasonableness_gate(params)
    return params


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid story combos:")
        for s, d, t in combos:
            print(f"  {s}  {d}  {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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

    for idx, sample in enumerate(samples):
        if args.all:
            p = sample.params
            header = f"### {p.setting} / {p.detective} / {p.tanker}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
