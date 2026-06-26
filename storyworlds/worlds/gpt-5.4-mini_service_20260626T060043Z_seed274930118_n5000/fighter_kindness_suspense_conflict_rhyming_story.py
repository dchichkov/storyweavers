#!/usr/bin/env python3
"""
Standalone storyworld: a fighter learns that kindness can win a tense moment.

Premise:
- A young fighter is preparing for a friendly match or practice display.
- Conflict arises when a boastful rival pokes fun and the fighter feels the urge to lash back.
- Suspense grows as a fragile, important object or moment is at risk.
- Kindness turns the scene: the fighter chooses a gentle move, helps the rival, and the conflict softens.

This world is intentionally small, state-driven, and rhyming in tone.
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

# -----------------------------------------------------------------------------
# Domain registries
# -----------------------------------------------------------------------------

RHYMES = {
    "bright": ["light", "night", "kite", "might", "tight"],
    "small": ["tall", "ball", "call", "wall", "stall"],
    "glow": ["show", "flow", "slow", "row", "snow"],
    "ring": ["sing", "spring", "wing", "thing", "king"],
    "care": ["share", "fair", "bare", "stare", "glare"],
    "soft": ["lift", "gentle", "safe", "warm", "kind"],
}

PLACES = {
    "dojo": {
        "name": "the dojo",
        "affords": {"practice", "spar", "help"},
    },
    "yard": {
        "name": "the yard",
        "affords": {"practice", "spar", "help"},
    },
    "stage": {
        "name": "the stage",
        "affords": {"practice", "show", "help"},
    },
}

TOOLS = {
    "gloves": {
        "label": "soft gloves",
        "kind": "gear",
        "safety": 2,
    },
    "pads": {
        "label": "padded gear",
        "kind": "gear",
        "safety": 3,
    },
    "banner": {
        "label": "a bright banner",
        "kind": "prop",
        "fragile": True,
    },
    "lantern": {
        "label": "a little lantern",
        "kind": "prop",
        "fragile": True,
    },
}

CHARACTER_NAMES = ["Milo", "Nia", "Rin", "Tess", "Juno", "Kai", "Lena", "Pip"]
RIVALS = ["Blaze", "Crush", "Rook", "Vex", "Crow", "Dart"]
TRAITS = ["brave", "steady", "quick", "gentle", "bold", "calm"]


# -----------------------------------------------------------------------------
# Dataclasses
# -----------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    tool: str
    prop: str
    hero_name: str
    rival_name: str
    hero_trait: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    fragile: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

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

        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def choose_rhyme(word: str, rng: random.Random) -> str:
    opts = RHYMES.get(word, [])
    return rng.choice(opts) if opts else "shine"


def meter_text(value: float) -> str:
    return "steady" if value <= 0 else "raised"


def actor_pronoun(name: str) -> str:
    return "they"


def possessive(name: str) -> str:
    return f"{name}'s"


def risk_of_damage(action: str, prop: str) -> bool:
    # Friendly spar can bump fragile props; practice/show can jostle them too.
    if TOOLS[prop].get("fragile", False) and action in {"spar", "practice", "show"}:
        return True
    return False


def conflict_score(hero: Entity) -> float:
    return hero.memes.get("conflict", 0.0)


def kindness_score(hero: Entity) -> float:
    return hero.memes.get("kindness", 0.0)


def reasonableness_gate(place: str, tool: str, prop: str) -> bool:
    # We want a fragile prop and a setting that can host some motion.
    return place in PLACES and tool in TOOLS and prop in TOOLS and TOOLS[prop].get("fragile", False)


# -----------------------------------------------------------------------------
# Narrative engine
# -----------------------------------------------------------------------------

def setup_world(params: StoryParams) -> World:
    world = World(PLACES[params.place]["name"])
    hero = world.add(Entity(id=params.hero_name, kind="character", label=params.hero_name))
    rival = world.add(Entity(id=params.rival_name, kind="character", label=params.rival_name))
    tool = world.add(Entity(id=params.tool, label=TOOLS[params.tool]["label"], worn_by=hero.id))
    prop = world.add(Entity(id=params.prop, label=TOOLS[params.prop]["label"], fragile=True, owner=hero.id))
    world.facts.update(hero=hero, rival=rival, tool=tool, prop=prop, params=params)
    return world


def intro(world: World) -> None:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    tool: Entity = world.facts["tool"]  # type: ignore[assignment]
    rhyme = choose_rhyme("bright", random.Random(len(p.hero_name) + len(p.place)))
    world.say(
        f"{hero.id} was a fighter {p.hero_trait} and bright, "
        f"who trained with care from morning to night."
    )
    world.say(
        f"With {tool.label}, {hero.id} would practice and grin, "
        f"for every small step felt like a win."
    )
    world.say(
        f"In {world.place}, the day had a soft little glow, "
        f"and each steady breath made the courage grow {rhyme}."
    )


def introduce_conflict(world: World) -> None:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    rival: Entity = world.facts["rival"]  # type: ignore[assignment]
    prop: Entity = world.facts["prop"]  # type: ignore[assignment]

    hero.memes["eagerness"] = 1
    world.say(
        f"Then {rival.id} came near with a snicker and strife, "
        f"and teased, \"You can't keep the rhythm alive.\""
    )
    hero.memes["conflict"] = 1
    world.say(
        f"{hero.id} felt heat in the chest and a sting in the face, "
        f"for harsh words can quickly speed up the race."
    )
    world.say(
        f"At the same time, {prop.label} sat close in the light, "
        f"and one clumsy bump could make it all rattle tight."
    )


def build_suspense(world: World) -> None:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    prop: Entity = world.facts["prop"]  # type: ignore[assignment]
    tool: Entity = world.facts["tool"]  # type: ignore[assignment]

    world.say(
        f"{hero.id} took one step, then paused for a glance, "
        f"wondering whether to answer with anger or dance."
    )
    hero.memes["suspense"] = 1
    if risk_of_damage("spar" if p.tool in {"gloves", "pads"} else "practice", p.prop):
        world.say(
            f"The little {prop.label} seemed ready to fall, "
            f"if the next quick move bounced hard off the wall."
        )
    else:
        world.say(
            f"Even with {tool.label}, the moment felt tight, "
            f"for the crowd and the teasing had dimmed the light."
        )


def resolve_with_kindness(world: World) -> None:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    rival: Entity = world.facts["rival"]  # type: ignore[assignment]
    prop: Entity = world.facts["prop"]  # type: ignore[assignment]

    hero.memes["kindness"] = 1
    hero.memes["conflict"] = 0
    hero.memes["suspense"] = 0
    world.say(
        f"Then {hero.id} chose kindness instead, with a nod and a smile, "
        f"and answered the teasing in a peaceful style."
    )
    world.say(
        f"\"Want a turn with me?\" {hero.id} said soft and fair, "
        f"\"We can both use the space and both show we care.\""
    )
    world.say(
        f"{rival.id} blinked, then frowned, then relaxed at the sound, "
        f"and the sharp little conflict lost grip on the ground."
    )
    world.say(
        f"{hero.id} fixed the {prop.label}, made sure it stood right, "
        f"and the whole room felt gentler by end of the night."
    )
    world.say(
        f"So the fighter won something more warm than a prize: "
        f"a friend at the side and a calm in the skies."
    )


def tell_story(params: StoryParams) -> World:
    if not reasonableness_gate(params.place, params.tool, params.prop):
        raise StoryError("The chosen place, tool, and prop do not make a reasonable fighter story.")

    world = setup_world(params)
    intro(world)
    world.para()
    introduce_conflict(world)
    world.para()
    build_suspense(world)
    world.para()
    resolve_with_kindness(world)
    return world


# -----------------------------------------------------------------------------
# QA generation
# -----------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    return [
        f"Write a short rhyming story about a fighter named {p.hero_name} who meets conflict with kindness.",
        f"Tell a child-friendly story in a small setting where {p.hero_name} stays brave during suspense and chooses a gentle ending.",
        f"Create a simple rhyming tale about teasing, calm words, and a fighter who protects {TOOLS[p.prop]['label']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    rival: Entity = world.facts["rival"]  # type: ignore[assignment]
    prop: Entity = world.facts["prop"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a fighter who stays brave and learns to use kindness when conflict appears.",
        ),
        QAItem(
            question=f"What caused the conflict in the story?",
            answer=f"{rival.id} teased {hero.id}, and that made the moment tense and full of conflict.",
        ),
        QAItem(
            question=f"What did {hero.id} do when the suspense felt strong?",
            answer=f"{hero.id} chose a gentle response, helped keep {prop.label} safe, and used kindness instead of anger.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended calmly, with the fighter and the rival at peace, and the fragile {prop.label} still safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness means doing something gentle, helpful, or caring for someone else.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of waiting to see what will happen next.",
        ),
        QAItem(
            question="What is conflict?",
            answer="Conflict is a disagreement or struggle between people, words, or choices.",
        ),
        QAItem(
            question="What is a fighter?",
            answer="A fighter is a person who practices strength, balance, and quick moves, often in training or sport.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        bits = []
        if ent.kind:
            bits.append(f"kind={ent.kind}")
        if ent.label:
            bits.append(f"label={ent.label}")
        if ent.worn_by:
            bits.append(f"worn_by={ent.worn_by}")
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        if ent.fragile:
            bits.append("fragile=True")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        lines.append(f"  {ent.id}: " + ", ".join(bits))
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# ASP twin
# -----------------------------------------------------------------------------

ASP_RULES = r"""
place_ok(P) :- place(P).
tool_ok(T) :- tool(T).
prop_ok(X) :- prop(X), fragile(X).

safe_story(P,T,X) :- place_ok(P), tool_ok(T), prop_ok(X).
% The world is valid when the fighter setting exists and the fragile prop can be protected.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
        if TOOLS[tid].get("fragile", False):
            lines.append(asp.fact("fragile", tid))
    for pid in PLACES:
        for a in sorted(PLACES[pid]["affords"]):
            lines.append(asp.fact("affords", pid, a))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable_combos() -> list[tuple[str, str, str]]:
    import asp
    program = asp_program("#show safe_story/3.")
    model = asp.one_model(program)
    return sorted(set(asp.atoms(model, "safe_story")))


def python_reasonable_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES:
        for tool in TOOLS:
            for prop in TOOLS:
                if reasonableness_gate(place, tool, prop):
                    out.append((place, tool, prop))
    return sorted(set(out))


def asp_verify() -> int:
    py = set(python_reasonable_combos())
    cl = set(asp_reasonable_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print("only in python:", sorted(py - cl))
    print("only in asp:", sorted(cl - py))
    return 1


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rhyming fighter storyworld about kindness, suspense, and conflict.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--prop", choices=sorted(k for k, v in TOOLS.items() if v.get("fragile", False)))
    ap.add_argument("--name")
    ap.add_argument("--rival")
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for tool in TOOLS:
            for prop in TOOLS:
                if reasonableness_gate(place, tool, prop):
                    combos.append((place, tool, prop))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("No reasonable story combinations exist.")

    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.tool is None or c[1] == args.tool)
        and (args.prop is None or c[2] == args.prop)
    ]
    if not filtered:
        raise StoryError("No valid combination matches the given options.")

    place, tool, prop = rng.choice(filtered)
    hero_name = args.name or rng.choice(CHARACTER_NAMES)
    rival = args.rival or rng.choice([r for r in RIVALS if r != hero_name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, tool=tool, prop=prop, hero_name=hero_name, rival_name=rival, hero_trait=trait)


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
        print(asp_program("#show safe_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_reasonable_combos()
        print(f"{len(combos)} safe combos:")
        for place, tool, prop in combos:
            print(f"  {place:8} {tool:8} {prop}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, tool, prop in sorted(valid_combos()):
            params = StoryParams(
                place=place,
                tool=tool,
                prop=prop,
                hero_name=args.name or "Milo",
                rival_name=args.rival or "Blaze",
                hero_trait=args.trait or "gentle",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            attempts += 1
            rng = random.Random(base_seed + attempts)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + attempts
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
            header = f"### {p.hero_name}: {p.place} / {p.tool} / {p.prop}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
