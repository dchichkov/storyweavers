#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/sprinkle_liberate_inner_monologue_adventure.py
================================================================================

A standalone story world for a small Adventure-style tale:
a brave child explorer uses a careful sprinkle to reveal the way and
liberates a trapped friend, while the story includes inner monologue.

The premise is intentionally tiny and constraint-checked:
- the hero travels through a location with a blocked passage
- a light sprinkling action reveals what is hidden or loosens what is stuck
- the hero then frees a captive companion
- the ending proves the change in the world state

The prose stays child-facing and causal, with the hero's inner monologue
rendered as brief thought sentences.
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
# Core world constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

PLACES = {
    "ancient_gate": {
        "label": "the ancient gate",
        "detail": "The stone gate stood under curling vines, with a tiny crack near the lock.",
        "affords": {"sprinkle", "liberate"},
        "kind": "ruins",
    },
    "moon_cavern": {
        "label": "the moonlit cave",
        "detail": "The cave glittered softly, and a shallow pool reflected the ceiling like glass.",
        "affords": {"sprinkle", "liberate"},
        "kind": "cave",
    },
    "forest_hollow": {
        "label": "the forest hollow",
        "detail": "Tall roots made a hiding place under the trees, and old leaves whispered on the ground.",
        "affords": {"sprinkle", "liberate"},
        "kind": "forest",
    },
}

TOOLS = {
    "sprinkle": {
        "label": "a little tin cup of water",
        "verb": "sprinkle",
        "result": "the dust lifted and the hidden latch showed itself",
        "mess": "wet",
        "tags": {"water", "spark"},
    },
    "glitter": {
        "label": "a pouch of glittering sand",
        "verb": "sprinkle",
        "result": "the grainy dust slid into the crack and loosened the jammed latch",
        "mess": "sandy",
        "tags": {"sand", "spark"},
    },
}

CAPTIVES = {
    "bird": {
        "label": "a little bird",
        "type": "bird",
        "trapped_in": "vine net",
        "free_verb": "liberate",
        "freed_image": "the bird flapped onto a low branch and sang",
        "tags": {"bird", "flight"},
    },
    "fox": {
        "label": "a small fox",
        "type": "fox",
        "trapped_in": "fallen snare",
        "free_verb": "liberate",
        "freed_image": "the fox darted into the brush with a bright tail wave",
        "tags": {"fox", "forest"},
    },
    "sprite": {
        "label": "a tiny river sprite",
        "type": "sprite",
        "trapped_in": "glass jar",
        "free_verb": "liberate",
        "freed_image": "the sprite danced out in a shining splash",
        "tags": {"water", "glow"},
    },
}

HERO_NAMES = ["Mina", "Leo", "Nori", "Tess", "Ari", "Pia", "Jude", "Iris"]
TRAITS = ["curious", "brave", "careful", "quick-thinking", "steady", "bold"]


# ---------------------------------------------------------------------------
# Entity model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    trapped: bool = False
    openable: bool = False
    freed: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    key: str
    label: str
    detail: str
    affords: set[str] = field(default_factory=set)
    kind: str = "place"


@dataclass
class StoryParams:
    place: str
    tool: str
    captive: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------

class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
# Simulation
# ---------------------------------------------------------------------------

def _inner_monologue(world: World, hero: Entity, thought: str) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1
    world.say(f'“{thought}” {hero.id} thought.')


def _apply_sprinkle(world: World, hero: Entity, tool: Entity, captive: Entity) -> None:
    if ("sprinkle", tool.id) in world.fired:
        return
    world.fired.add(("sprinkle", tool.id))
    tool.meters["used"] = tool.meters.get("used", 0.0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(
        f"{hero.id} lifted {hero.pronoun('possessive')} {tool.label} and "
        f"sprinkled the water over the cracked stone."
    )
    world.say(
        f"{TOOLS[world.facts['tool_key']]['result'].capitalize()}."
    )
    captive.memes["attention"] = captive.memes.get("attention", 0.0) + 1


def _apply_liberate(world: World, hero: Entity, captive: Entity) -> None:
    if ("liberate", captive.id) in world.fired:
        return
    world.fired.add(("liberate", captive.id))
    captive.trapped = False
    captive.freed = True
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["courage"] = hero.memes.get("courage", 0.0) + 1
    world.say(
        f"{hero.id} reached in carefully and {CAPTIVES[world.facts['captive_key']]['free_verb']}d "
        f"{captive.label}."
    )
    world.say(CAPTIVES[world.facts["captive_key"]]["freed_image"].capitalize() + ".")


def tell(place_key: str, tool_key: str, captive_key: str, hero_name: str, hero_gender: str, trait: str) -> World:
    place_cfg = PLACES[place_key]
    world = World(Place(key=place_key, **place_cfg))
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name))
    tool_cfg = TOOLS[tool_key]
    tool = world.add(Entity(id="tool", kind="thing", type="tool", label=tool_cfg["label"]))
    captive_cfg = CAPTIVES[captive_key]
    captive = world.add(Entity(id="captive", kind="character", type=captive_cfg["type"], label=captive_cfg["label"], trapped=True))

    world.facts.update(
        hero=hero,
        tool=tool,
        captive=captive,
        place_key=place_key,
        tool_key=tool_key,
        captive_key=captive_key,
        trait=trait,
    )

    # Act 1: setup.
    world.say(
        f"{hero.id} was a {trait} little explorer who loved hidden places and old secrets."
    )
    world.say(
        f"One day, {hero.id} came to {world.place.label}. {world.place.detail}"
    )
    world.say(
        f"Near the gate, {hero.id} found {captive.label} trapped in {captive_cfg['trapped_in']}."
    )
    _inner_monologue(world, hero, "I can help if I stay calm and look closely.")

    # Act 2: the key action.
    world.para()
    if "sprinkle" not in world.place.affords:
        raise StoryError("This place does not support the sprinkle action.")
    _apply_sprinkle(world, hero, tool, captive)
    _inner_monologue(world, hero, "There! The small trick worked. Now I can free them.")

    # Act 3: resolve and ending image.
    world.para()
    if "liberate" not in world.place.affords:
        raise StoryError("This place does not support the liberate action.")
    _apply_liberate(world, hero, captive)
    world.say(
        f"{hero.id} smiled as the path opened again, and the gate no longer felt stuck and lonely."
    )
    world.say(
        f"At the end, {hero.id} walked on with lighter steps, and the freed friend was safe at last."
    )
    return world


# ---------------------------------------------------------------------------
# Registries and ASP twin
# ---------------------------------------------------------------------------

PLACE_REGISTRY = PLACES
TOOL_REGISTRY = TOOLS
CAPTIVE_REGISTRY = CAPTIVES

ASP_RULES = r"""
% A story is valid when the place allows the needed actions.
valid_story(P, T, C) :- place(P), tool(T), captive(C),
                        affords(P, sprinkle), affords(P, liberate),
                        tool_needs_sprinkle(T), captive_needs_liberate(C).

% Sprinkle is a reasonableness step that reveals or loosens the obstacle.
helpful_sprinkle(T, C) :- tool_needs_sprinkle(T), captive_needs_liberate(C).

% Liberation is only appropriate after the sprinkle step exists in the same world.
can_liberate(C) :- captive_needs_liberate(C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pkey, place in PLACE_REGISTRY.items():
        lines.append(asp.fact("place", pkey))
        for a in sorted(place["affords"]):
            lines.append(asp.fact("affords", pkey, a))
    for tkey, tool in TOOL_REGISTRY.items():
        lines.append(asp.fact("tool", tkey))
        lines.append(asp.fact("tool_needs_sprinkle", tkey))
    for ckey, captive in CAPTIVE_REGISTRY.items():
        lines.append(asp.fact("captive", ckey))
        lines.append(asp.fact("captive_needs_liberate", ckey))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    cl = set(asp.atoms(model, "valid_story"))
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Constraints / content selection
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pkey, p in PLACES.items():
        for tkey in TOOLS:
            for ckey in CAPTIVES:
                combos.append((pkey, tkey, ckey))
    return combos


def explain_rejection(place: str, tool: str, captive: str) -> str:
    return (
        f"(No story: {PLACE_REGISTRY[place]['label']} does not support a mismatch "
        f"for {tool} and {captive}; this world expects a sprinkle that reveals a way "
        f"and a liberation that follows from it.)"
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short Adventure story for a child where {f["hero"].id} uses a sprinkle action and then liberates a trapped friend.',
        f"Tell a gentle exploration tale at {world.place.label} with an inner monologue, a careful sprinkle, and a happy rescue.",
        f'Write a child-facing adventure where the words "sprinkle" and "liberate" both matter to the ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    captive = world.facts["captive"]
    trait = world.facts["trait"]
    place = world.place.label
    return [
        QAItem(
            question=f"Who went to {place} in the story?",
            answer=f"{hero.id} went to {place} as a {trait} little explorer.",
        ),
        QAItem(
            question=f"What did {hero.id} think before acting?",
            answer="The hero thought about staying calm, looking closely, and helping step by step.",
        ),
        QAItem(
            question=f"What did the sprinkle action do?",
            answer=f"It revealed the hidden latch and made it possible to help {captive.label}.",
        ),
        QAItem(
            question=f"What happened after {hero.id} liberated the trapped friend?",
            answer=f"The trapped friend was free, safe, and able to move again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to sprinkle something?",
            answer="To sprinkle means to scatter a little bit of liquid or small pieces over a surface.",
        ),
        QAItem(
            question="What does liberate mean?",
            answer="To liberate means to set someone or something free.",
        ),
        QAItem(
            question="Why do explorers think before they act?",
            answer="Explorers think first so they can stay safe, notice clues, and choose a good plan.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
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
        if e.trapped:
            bits.append("trapped=True")
        if e.freed:
            bits.append("freed=True")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world with sprinkle, liberate, and inner monologue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--captive", choices=CAPTIVES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = [c for c in combos if (args.place is None or c[0] == args.place)
              and (args.tool is None or c[1] == args.tool)
              and (args.captive is None or c[2] == args.captive)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, tool, captive = rng.choice(sorted(combos))
    name = args.name or rng.choice(HERO_NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, tool=tool, captive=captive, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.tool, params.captive, params.name, params.gender, params.trait)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} compatible stories:")
        for row in vals:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in [StoryParams(place=p, tool=t, captive=c, name="Mina", gender="girl", trait="curious")
                  for p, t, c in valid_combos()]:
            samples.append(generate(p))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
