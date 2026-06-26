#!/usr/bin/env python3
"""
storyworlds/worlds/poop_dim_mystery_to_solve_superhero_story.py
===============================================================

A small superhero mystery world: a young hero follows clues, tests a theory,
and solves the "poop-dim" problem by finding the real cause of the dim light.

The story premise is intentionally simple:
- A superhero notices something in the city is dim and strange.
- A mystery must be solved with clues, not random force.
- The ending shows what changed after the fix.

The world models both physical meters and emotional memes:
- meters track light, stink, soot, and trust
- memes track worry, courage, curiosity, relief, and pride
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
# Small world registries
# ---------------------------------------------------------------------------

PLACES = {
    "alley": {
        "label": "the alley",
        "kind": "street",
        "clues": {"shadow", "stink", "crumbs"},
        "good_for": {"investigate", "fly", "scan"},
    },
    "rooftop": {
        "label": "the rooftop",
        "kind": "high",
        "clues": {"wind", "shadow", "glow"},
        "good_for": {"investigate", "scan", "fly"},
    },
    "park": {
        "label": "the park",
        "kind": "open",
        "clues": {"mud", "stink", "glow"},
        "good_for": {"investigate", "run", "scan"},
    },
    "museum": {
        "label": "the museum",
        "kind": "quiet",
        "clues": {"dust", "shadow", "glow"},
        "good_for": {"investigate", "scan"},
    },
}

TOOLS = {
    "lantern": {
        "label": "a bright lantern",
        "helps": {"light"},
        "clues": {"glow"},
        "problem": "dimness",
    },
    "scanner": {
        "label": "a clue scanner",
        "helps": {"shadow", "stink", "crumbs", "mud", "dust"},
        "clues": {"shadow", "crumbs", "dust"},
        "problem": "mystery",
    },
    "gloves": {
        "label": "sticky gloves",
        "helps": {"mess"},
        "clues": {"stink", "mud"},
        "problem": "mess",
    },
}

VILLAINS = {
    "moth": {
        "label": "the Moth Shade",
        "mess": "shadow",
        "tell": "soft fluttering wings",
        "motive": "wanted the city lights low and sleepy",
    },
    "raccoon": {
        "label": "the Sneaky Raccoon",
        "mess": "stink",
        "tell": "tiny paw prints",
        "motive": "wanted shiny snacks from the trash cans",
    },
    "goop": {
        "label": "Goop Goblin",
        "mess": "mud",
        "tell": "squishy footprints",
        "motive": "wanted to smear everything with goo",
    },
    "dust": {
        "label": "Dust Drifter",
        "mess": "dust",
        "tell": "a gray little puff",
        "motive": "wanted to hide bright signs under dust",
    },
}

POWERS = {
    "scan": "scan for clues",
    "fly": "fly over rooftops",
    "shine": "shine a beam of light",
    "listen": "listen for tiny sounds",
    "leap": "leap across the street",
}

HERO_NAMES = ["Nova", "Zuri", "Atlas", "Mira", "Kai", "Tess", "Rory", "Ivy"]
SIDEKICK_NAMES = ["Pip", "Bop", "Mox", "Luna", "Jax", "Nia"]

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # hero | sidekick | villain | thing
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owns: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Scene:
    place: str
    mystery: str
    villain: str
    tool: str
    hero_power: str
    seed_word: str = "poop-dim"


@dataclass
class StoryParams:
    place: str
    mystery: str
    villain: str
    tool: str
    hero_name: str
    sidekick_name: str
    hero_power: str
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
# Helpers
# ---------------------------------------------------------------------------

def _inc(entity: Entity, bucket: str, amount: float = 1.0) -> None:
    entity.meters[bucket] = entity.meters.get(bucket, 0.0) + amount


def _mem(entity: Entity, bucket: str, amount: float = 1.0) -> None:
    entity.memes[bucket] = entity.memes.get(bucket, 0.0) + amount


def valid_combo(place: str, mystery: str, villain: str, tool: str) -> bool:
    if mystery != villain:
        return False
    if place not in PLACES:
        return False
    if tool not in TOOLS:
        return False
    if "investigate" not in PLACES[place]["good_for"]:
        return False
    if mystery not in TOOLS[tool]["clues"] and tool != "scanner":
        return False
    return True


def explain_rejection(place: str, mystery: str, villain: str, tool: str) -> str:
    return (
        f"(No story: this setup does not make a solvable mystery. "
        f"The place, clue, villain, and tool need to fit together.)"
    )


def choose_clue_word(villain: str) -> str:
    return VILLAINS[villain]["mess"]


def clue_chain(villain: str) -> list[str]:
    info = VILLAINS[villain]
    if villain == "raccoon":
        return ["tiny paw prints", "a trail of crumbs", "the smell from a trash lid"]
    if villain == "moth":
        return ["soft fluttering wings", "a shadow over the lamp", "the dim glow of a torn cape"]
    if villain == "goop":
        return ["squishy footprints", "a slimy puddle", "a green smear on the wall"]
    return ["a gray little puff", "dusty footprints", "a faded sign"]

# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def tell(scene: Scene, hero_name: str, sidekick_name: str, hero_power: str) -> World:
    w = World(scene)
    hero = w.add(Entity(id=hero_name, kind="hero", type="hero", label=hero_name))
    sidekick = w.add(Entity(id=sidekick_name, kind="sidekick", type="sidekick", label=sidekick_name))
    villain = w.add(Entity(id=scene.villain, kind="villain", type="villain", label=VILLAINS[scene.villain]["label"]))

    _mem(hero, "curiosity", 2)
    _mem(hero, "courage", 1)
    _mem(sidekick, "trust", 2)

    # Act 1: setup
    w.say(f"{hero_name} was a little superhero who loved to {POWERS[hero_power]}.")
    w.say(f"One evening, {hero_name} and {sidekick_name} noticed a strange poop-dim glow over {PLACES[scene.place]['label']}.")
    w.say(
        f"The light looked wrong, and the air felt weird, so {hero_name} knew this was a mystery to solve."
    )

    # Act 2: clues
    w.para()
    _inc(hero, "worry", 1)
    _inc(sidekick, "worry", 1)
    w.say(f"They hurried to {PLACES[scene.place]['label']} to look for clues.")
    for clue in clue_chain(scene.villain)[:2]:
        w.say(f"First they found {clue}.")
        _inc(hero, "curiosity", 1)
    w.say(f"{hero_name} used {TOOLS[scene.tool]['label']} to {POWERS[hero_power]}.")
    w.say(f"That helped them notice {clue_chain(scene.villain)[-1]}.")
    w.say(f"The clue pointed to {VILLAINS[scene.villain]['label']}.")
    _mem(hero, "confidence", 1)

    # Act 3: reveal and fix
    w.para()
    w.say(
        f"{hero_name} and {sidekick_name} followed the trail and found {VILLAINS[scene.villain]['label']} near the dark corner."
    )
    w.say(
        f"It was the one behind the poop-dim problem because it {VILLAINS[scene.villain]['motive']}."
    )
    _mem(villain, "caught", 1)
    _mem(hero, "pride", 1)
    _mem(hero, "relief", 2)
    _mem(sidekick, "relief", 2)
    _inc(hero, "light", 1)

    w.say(
        f"{hero_name} did not need to smash anything. Instead, {hero_name} used {hero_power} to show the truth, "
        f"and {sidekick_name} helped clean the mess."
    )
    w.say(
        f"At the end, the poop-dim shadow lifted, the place looked bright again, and {hero_name} stood smiling in the clear light."
    )

    w.facts.update(
        hero=hero,
        sidekick=sidekick,
        villain=villain,
        scene=scene,
        clue_chain=clue_chain(scene.villain),
        solved=True,
    )
    return w


# ---------------------------------------------------------------------------
# Registries and parameter resolution
# ---------------------------------------------------------------------------

def available_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place in PLACES:
        for villain in VILLAINS:
            for mystery in VILLAINS:
                for tool in TOOLS:
                    if valid_combo(place, mystery, villain, tool):
                        out.append((place, mystery, villain, tool))
    return out


@dataclass
class StoryParams:
    place: str
    mystery: str
    villain: str
    tool: str
    hero_name: str
    sidekick_name: str
    hero_power: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero mystery story world with a poop-dim clue.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--mystery", choices=sorted(VILLAINS))
    ap.add_argument("--villain", choices=sorted(VILLAINS))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--hero-name", dest="hero_name")
    ap.add_argument("--sidekick-name", dest="sidekick_name")
    ap.add_argument("--hero-power", choices=sorted(POWERS))
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
    combos = available_combos()
    if args.place and args.mystery and args.villain and args.tool:
        if not valid_combo(args.place, args.mystery, args.villain, args.tool):
            raise StoryError(explain_rejection(args.place, args.mystery, args.villain, args.tool))
        combos = [c for c in combos if c == (args.place, args.mystery, args.villain, args.tool)]
    else:
        if args.place:
            combos = [c for c in combos if c[0] == args.place]
        if args.mystery:
            combos = [c for c in combos if c[1] == args.mystery]
        if args.villain:
            combos = [c for c in combos if c[2] == args.villain]
        if args.tool:
            combos = [c for c in combos if c[3] == args.tool]
    if not combos:
        raise StoryError("(No valid superhero mystery matches the given options.)")
    place, mystery, villain, tool = rng.choice(sorted(combos))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    sidekick_name = args.sidekick_name or rng.choice(SIDEKICK_NAMES)
    hero_power = args.hero_power or rng.choice(list(POWERS))
    return StoryParams(place, mystery, villain, tool, hero_name, sidekick_name, hero_power)


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene: Scene = f["scene"]
    return [
        f'Write a short superhero story for a child that includes the word "poop-dim" and a mystery to solve.',
        f"Tell a simple hero story where {f['hero'].id} and {f['sidekick'].id} investigate {PLACES[scene.place]['label']} with a {TOOLS[scene.tool]['label']}.",
        f"Write a gentle mystery story where the villain is {VILLAINS[scene.villain]['label']} and the ending proves who caused the poop-dim problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    scene: Scene = f["scene"]
    villain: Entity = f["villain"]

    qa = [
        QAItem(
            question=f"Who solved the poop-dim mystery at {PLACES[scene.place]['label']}?",
            answer=f"{hero.id} solved it with help from {sidekick.id}. They used clues instead of guessing."
        ),
        QAItem(
            question=f"What tool did {hero.id} use to look for clues?",
            answer=f"{hero.id} used {TOOLS[scene.tool]['label']} to search for clues and follow the trail."
        ),
        QAItem(
            question=f"Who caused the poop-dim problem?",
            answer=f"It was {villain.label}. The clues showed that this was the real cause of the dim and strange light."
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"The mystery was solved, the bad dimness lifted, and {hero.id} ended the story smiling in bright light."
        ),
    ]
    return qa


WORLD_KNOWLEDGE = {
    "shadow": QAItem(
        question="What is a shadow?",
        answer="A shadow is a dark shape made when something blocks the light."
    ),
    "stink": QAItem(
        question="Why do some things smell bad?",
        answer="Some things smell bad because tiny bits from them mix into the air and our noses notice the smell."
    ),
    "crumbs": QAItem(
        question="What are crumbs?",
        answer="Crumbs are tiny broken pieces of food."
    ),
    "mud": QAItem(
        question="What is mud?",
        answer="Mud is wet dirt that can stick to shoes and paws."
    ),
    "dust": QAItem(
        question="What is dust?",
        answer="Dust is made of tiny bits that can gather on shelves and make things look gray."
    ),
    "glow": QAItem(
        question="What does glow mean?",
        answer="Glow means to shine softly with light."
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out: list[QAItem] = []
    for clue in f["clue_chain"]:
        if "shadow" in clue:
            out.append(WORLD_KNOWLEDGE["shadow"])
        if "smell" in clue or "stink" in clue:
            out.append(WORLD_KNOWLEDGE["stink"])
        if "crumb" in clue:
            out.append(WORLD_KNOWLEDGE["crumbs"])
        if "mud" in clue or "goo" in clue:
            out.append(WORLD_KNOWLEDGE["mud"])
        if "dust" in clue or "puff" in clue:
            out.append(WORLD_KNOWLEDGE["dust"])
    out.append(WORLD_KNOWLEDGE["glow"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
villain(V) :- bad(V).
tool(T) :- gadget(T).

solvable(P, M, V, T) :- place(P), mystery(M), villain(V), tool(T),
                        clue_for(V, M), can_investigate(P), helps(T, M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("setting", p))
        lines.append(asp.fact("can_investigate", p))
    for v, info in VILLAINS.items():
        lines.append(asp.fact("bad", v))
        lines.append(asp.fact("mystery", v))
        lines.append(asp.fact("clue_for", v, info["mess"]))
    for t, info in TOOLS.items():
        lines.append(asp.fact("gadget", t))
        for clue in sorted(info["clues"]):
            lines.append(asp.fact("helps", t, clue))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solvable/4."))
    return sorted(set(asp.atoms(model, "solvable")))


def asp_verify() -> int:
    py = set(available_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Output and trace
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"{ent.id}: kind={ent.kind} meters={meters} memes={memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    scene = Scene(
        place=params.place,
        mystery=params.mystery,
        villain=params.villain,
        tool=params.tool,
        hero_power=params.hero_power,
    )
    world = tell(scene, params.hero_name, params.sidekick_name, params.hero_power)
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
        print(asp_program("#show solvable/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(json.dumps(asp_valid_combos(), indent=2))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        # Curated, valid set.
        curated = [
            StoryParams("alley", "raccoon", "raccoon", "scanner", "Nova", "Pip", "scan"),
            StoryParams("rooftop", "moth", "moth", "lantern", "Zuri", "Bop", "shine"),
            StoryParams("park", "goop", "goop", "gloves", "Atlas", "Luna", "leap"),
            StoryParams("museum", "dust", "dust", "scanner", "Mira", "Jax", "listen"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
