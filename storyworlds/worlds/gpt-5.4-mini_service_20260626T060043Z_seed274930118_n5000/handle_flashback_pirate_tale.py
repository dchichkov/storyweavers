#!/usr/bin/env python3
"""
storyworlds/worlds/handle_flashback_pirate_tale.py
===================================================

A standalone story world for a small Pirate Tale with a flashback beat.

Premise:
- A young pirate wants to tug at a handle: a chest lid, a ship latch, or a
  crate ring.
- The grown-up pirate remembers an earlier mishap in a flashback.
- The flashback changes the plan: they slow down, use the right tool, and the
  handle opens safely.
- The ending shows what changed: the treasure is reached, the ship stays tidy,
  and the hero feels proud instead of careless.

The world is intentionally small and constraint-checked:
- The handle must actually matter to the scene.
- The flashback must explain why the pirate hesitates or changes method.
- The chosen helper/tool must fit the handle type.
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
# World entities
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
    held_by: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Scene:
    place: str
    affordance: str
    handle_kind: str
    handle_label: str
    handle_phrase: str
    handle_risk: str
    handle_turn: str
    tool_needed: str
    tool_label: str
    tool_phrase: str
    flashback: str
    outcome: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    fits: set[str]
    helps_with: set[str]
    action: str
    ending: str
    plural: bool = False


@dataclass
class StoryParams:
    scene: str
    tool: str
    hero_name: str
    hero_type: str
    parent_name: str
    parent_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
SCENES = {
    "captain_cabin": Scene(
        place="the captain's cabin",
        affordance="open the chest",
        handle_kind="chest",
        handle_label="brass handle",
        handle_phrase="a brass handle on an old sea chest",
        handle_risk="might jam the lid or make a loud clank",
        handle_turn="the chest could be opened without breaking the latch",
        tool_needed="cloth",
        tool_label="soft cloth",
        tool_phrase="a soft cloth to steady the pull",
        flashback="the last time the pirate yanked a handle too fast, the lid banged shut and spilled coins everywhere",
        outcome="the lid opened cleanly and the gold stayed neat",
        tags={"handle", "flashback", "pirate", "chest"},
    ),
    "deck_hatch": Scene(
        place="the ship's deck",
        affordance="lift the hatch",
        handle_kind="hatch",
        handle_label="iron ring",
        handle_phrase="an iron ring on a heavy hatch",
        handle_risk="might pinch fingers or slam the hatch",
        handle_turn="the hatch could be lifted safely",
        tool_needed="rope",
        tool_label="short rope",
        tool_phrase="a short rope to make a safer pull",
        flashback="the pirate remembered a windy day when a hard tug made a hatch slap shut and scare the gulls",
        outcome="the hatch lifted smoothly and the sea air rushed up",
        tags={"handle", "flashback", "pirate", "hatch"},
    ),
    "cargo_crate": Scene(
        place="the cargo hold",
        affordance="open the crate",
        handle_kind="crate",
        handle_label="wooden handle",
        handle_phrase="a wooden handle on a crate of supplies",
        handle_risk="might crack the crate and spill the apples",
        handle_turn="the crate could be opened without smashing it",
        tool_needed="knife",
        tool_label="small knife",
        tool_phrase="a small knife to ease the latch",
        flashback="the pirate remembered once snapping a crate handle and having to pick up fruit all afternoon",
        outcome="the crate opened neatly and the apples stayed stacked",
        tags={"handle", "flashback", "pirate", "crate"},
    ),
}

TOOLS = {
    "cloth": Tool(
        id="cloth",
        label="soft cloth",
        phrase="a soft cloth",
        fits={"chest"},
        helps_with={"steady"},
        action="wrap the handle",
        ending="wrapped the brass handle with the cloth and pulled gently",
    ),
    "rope": Tool(
        id="rope",
        label="short rope",
        phrase="a short rope",
        fits={"hatch"},
        helps_with={"pull"},
        action="loop the ring",
        ending="looped the ring with the rope and lifted together",
        plural=False,
    ),
    "knife": Tool(
        id="knife",
        label="small knife",
        phrase="a small knife",
        fits={"crate"},
        helps_with={"ease"},
        action="slip under the latch",
        ending="slipped the knife under the latch and eased it open",
    ),
}

NAMES = ["Pip", "Nell", "Finn", "Mara", "Jory", "Sailor", "Tess", "Bo", "Ruby", "Wren"]
TRAITS = ["brave", "curious", "bouncy", "quick", "spirited", "stubborn"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
scene_valid(S) :- scene(S).
compatible(S,T) :- scene_valid(S), tool(T), fits(T,K), handle_kind(S,K).
good_story(S,T) :- compatible(S,T), tags(S,flashback), tags(S,handle).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SCENES.items():
        lines.append(asp.fact("scene", sid))
        lines.append(asp.fact("handle_kind", sid, s.handle_kind))
        lines.append(asp.fact("tags", sid, "handle"))
        lines.append(asp.fact("tags", sid, "flashback"))
        for tag in sorted(s.tags):
            if tag not in {"handle", "flashback"}:
                lines.append(asp.fact("tags", sid, tag))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for k in sorted(t.fits):
            lines.append(asp.fact("fits", tid, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatible_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set((scene_id, tool_id) for scene_id, s in SCENES.items() for tool_id, t in TOOLS.items() if t.fits == {s.handle_kind} or s.handle_kind in t.fits)
    asp_set = set(asp_compatible_pairs())
    if asp_set == py:
        print(f"OK: clingo gate matches python ({len(py)} compatible pairs).")
        return 0
    print("MISMATCH between clingo and python:")
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(scene: Scene, tool: Tool) -> bool:
    return scene.handle_kind in tool.fits and scene.handle_kind in scene.tags and "flashback" in scene.tags


def explain_invalid(scene: Scene, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not fit the {scene.handle_kind}. "
        f"The handle must actually matter, and the flashback must lead to a tool that works.)"
    )


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    scene = SCENES[params.scene]
    tool = TOOLS[params.tool]
    world = World(scene)

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    parent = world.add(Entity(id=params.parent_name, kind="character", type=params.parent_type))
    handle = world.add(Entity(
        id="handle",
        type="handle",
        label=scene.handle_label,
        phrase=scene.handle_phrase,
        owner="scene",
    ))
    tool_ent = world.add(Entity(
        id=tool.id,
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        owner=hero.id,
        held_by=hero.id,
    ))

    world.say(f"{hero.id} was a {params.trait} little pirate who loved every hidden thing on the ship.")
    world.say(f"One day, {hero.id} spotted {handle.phrase} in {scene.place}.")

    world.para()
    world.say(f"{hero.id} wanted to {scene.affordance}, but {handle.label} looked tricky.")
    world.say(f"It could {scene.handle_risk}.")
    world.say(f"Then {parent.id} paused with a faraway look, and a flashback came back.")

    world.para()
    world.say(f"In the flashback, {scene.flashback}.")
    world.say(f"So this time, {parent.id} said to slow down and use {tool.phrase}.")

    world.para()
    world.say(f"{hero.id} listened, because {params.trait} pirates can learn from old mistakes.")
    world.say(f"Together they {tool.action} and {scene.handle_turn}.")
    world.say(f"Their careful choice made it easy to {scene.affordance}.")

    world.para()
    world.say(f"At the end, {scene.outcome}, and {hero.id} grinned like a tiny captain.")
    world.say(f"{parent.id} smiled too, glad the flashback helped them do it the smart way.")

    world.facts.update(
        hero=hero,
        parent=parent,
        handle=handle,
        tool=tool,
        scene=scene,
        resolved=True,
        flashback=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short Pirate Tale for a young child that includes the word "handle" and a remembering-back moment.',
        f"Tell a gentle pirate story where {f['hero'].id} wants to {f['scene'].affordance} but remembers an old mistake.",
        f"Write a small adventure about {f['hero'].id}, {f['parent'].id}, a {f['scene'].handle_kind}, and a flashback that leads to a safer choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    scene = f["scene"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do when they saw the {scene.handle_kind} handle?",
            answer=f"{hero.id} wanted to {scene.affordance}. The handle looked tricky, so they paused instead of rushing.",
        ),
        QAItem(
            question=f"Why did {parent.id} remember the flashback?",
            answer=f"{parent.id} remembered that an earlier hard tug had caused trouble. The flashback showed why it was smarter to slow down and use {tool.phrase}.",
        ),
        QAItem(
            question=f"What helped {hero.id} open the {scene.handle_kind} safely?",
            answer=f"{tool.phrase} helped {hero.id} do it carefully. They used it to make the pull gentle, and that kept the handle from causing a mess.",
        ),
        QAItem(
            question=f"How did the story end after the flashback?",
            answer=f"The careful plan worked: {scene.outcome}, and {hero.id} finished proud instead of careless.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a handle?",
            answer="A handle is a part you can hold, pull, or turn to open something or move it.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a scene that shows something that happened earlier, so the character can remember it now.",
        ),
        QAItem(
            question="Why do pirates use tools carefully on a ship?",
            answer="Pirates use tools carefully because ships can be shaky, and a rough pull can break things or make a big clatter.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sid, scene in SCENES.items():
        for tid, tool in TOOLS.items():
            if valid_combo(scene, tool):
                out.append((sid, tid))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.tool:
        if not valid_combo(SCENES[args.scene], TOOLS[args.tool]):
            raise StoryError(explain_invalid(SCENES[args.scene], TOOLS[args.tool]))
    combos = [c for c in valid_combos() if (args.scene is None or c[0] == args.scene) and (args.tool is None or c[1] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene_id, tool_id = rng.choice(sorted(combos))
    hero_type = rng.choice(["boy", "girl"])
    parent_type = rng.choice(["father", "mother", "captain"])
    hero_name = args.hero_name or rng.choice(NAMES)
    parent_name = args.parent_name or rng.choice(["Cap", "Aunt", "Dad", "Ma"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        scene=scene_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_type=hero_type,
        parent_name=parent_name,
        parent_type=parent_type,
        trait=trait,
    )


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(scene="captain_cabin", tool="cloth", hero_name="Pip", hero_type="boy", parent_name="Cap", parent_type="captain", trait="curious"),
    StoryParams(scene="deck_hatch", tool="rope", hero_name="Mara", hero_type="girl", parent_name="Dad", parent_type="father", trait="brave"),
    StoryParams(scene="cargo_crate", tool="knife", hero_name="Finn", hero_type="boy", parent_name="Ma", parent_type="mother", trait="spirited"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A Pirate Tale story world with a handle and a flashback.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-type", choices=["mother", "father", "captain"])
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_program_text() -> str:
    return asp_program("#show compatible/2.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_text())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible scene/tool pairs:\n")
        for scene, tool in combos:
            print(f"  {scene:14} {tool}")
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
            header = f"### {p.hero_name}: {p.scene} via {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
