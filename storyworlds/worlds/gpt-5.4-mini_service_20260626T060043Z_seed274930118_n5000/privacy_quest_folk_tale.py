#!/usr/bin/env python3
"""
privacy_quest_folk_tale.py
===========================

A small folk-tale storyworld about a child on a privacy quest: a gentle hero
wants a little private place, faces a nosy problem, and finds a kind, clever
way to keep a secret safe without hurting anyone's feelings.

The world is simulation-driven. Physical state uses meters; emotional state uses
memes. The prose is built from the state changes, not from a frozen template.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    guarded: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen"}
        male = {"boy", "father", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    private_kind: str
    noise: str
    shieldable: bool = True


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    guards: set[str]
    fits: set[str]


@dataclass
class StoryParams:
    place: str
    privacy_need: str
    tool: str
    hero_name: str
    hero_type: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.noise: float = 0.0
        self.prying: float = 0.0

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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.noise = self.noise
        clone.prying = self.prying
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "cottage_garden": Place(
        id="cottage_garden",
        label="the cottage garden",
        private_kind="a quiet nook",
        noise="the hedge rustled softly",
    ),
    "mill_pond": Place(
        id="mill_pond",
        label="the mill pond",
        private_kind="a secret bank",
        noise="the water lapped under the reeds",
    ),
    "forest_glade": Place(
        id="forest_glade",
        label="the forest glade",
        private_kind="a hidden clearing",
        noise="the leaves whispered overhead",
    ),
}

TOOLS = {
    "hedge": Tool(
        id="hedge",
        label="a hedge",
        phrase="a thick hedge of green leaves",
        guards={"prying", "seeing", "noise"},
        fits={"cottage_garden", "forest_glade"},
    ),
    "curtain": Tool(
        id="curtain",
        label="a curtain",
        phrase="a soft curtain for the little window",
        guards={"seeing"},
        fits={"cottage_garden"},
    ),
    "screen": Tool(
        id="screen",
        label="a reed screen",
        phrase="a tall reed screen tied with twine",
        guards={"seeing", "noise"},
        fits={"mill_pond", "forest_glade"},
    ),
    "lantern_cloth": Tool(
        id="lantern_cloth",
        label="a lantern cloth",
        phrase="a cloth to cover the lantern",
        guards={"seeing"},
        fits={"cottage_garden", "forest_glade", "mill_pond"},
    ),
}

NEEDS = {
    "privacy": {
        "want": "keep a little privacy",
        "risk": "the whole lane could peek in",
        "soil": "too open and thin",
        "want_sentence": "wanted a private place to think and dream",
    },
    "secret_note": {
        "want": "write a secret note",
        "risk": "a nosy eye might read it",
        "soil": "unfolded for all to see",
        "want_sentence": "wanted a quiet corner to write a secret note",
    },
    "changing_space": {
        "want": "change clothes in peace",
        "risk": "a stray glance might shame the child",
        "soil": "not private enough",
        "want_sentence": "wanted a place to change clothes in peace",
    },
}

HERO_NAMES = ["Mila", "Tobin", "Anya", "Oren", "Leah", "Finn", "Nora", "Pip"]
TRAITS = ["gentle", "curious", "patient", "brave", "thoughtful", "quiet"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def need_at_risk(place: Place, need_key: str) -> bool:
    return True


def select_tool(place: Place, need_key: str) -> Optional[Tool]:
    for tool in TOOLS.values():
        if place.id in tool.fits:
            if need_key == "privacy" and "seeing" in tool.guards:
                return tool
            if need_key == "secret_note" and "seeing" in tool.guards:
                return tool
            if need_key == "changing_space" and "seeing" in tool.guards:
                return tool
    return None


def predict_problem(world: World, tool: Optional[Tool]) -> dict:
    sim = world.copy()
    sim.noise += 1
    sim.prying += 1
    protected = tool is not None and "seeing" in tool.guards
    return {"exposed": not protected, "prying": sim.prying, "noise": sim.noise}


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"Once, in {world.place.label}, there lived {hero.phrase}, "
        f"who was known as a {hero.type} with a {hero.memes.get('trait', 0):.0f}-hearted smile."
    )


def set_scene(world: World) -> None:
    world.say(f"{world.place.noise}, and {world.place.private_kind} waited beneath the trees.")


def desire(world: World, hero: Entity, need_key: str) -> None:
    need = NEEDS[need_key]
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    world.say(f"{hero.pronoun().capitalize()} {need['want_sentence']}.")
    world.say(f"But {need['risk']}.")


def worry(world: World, helper: Entity, hero: Entity, need_key: str) -> None:
    helper.memes["care"] = helper.memes.get("care", 0) + 1
    world.prying += 1
    world.say(
        f"Then {helper.pronoun().capitalize()} came by and said, "
        f'"I hear a place like that needs care, or else it grows {NEEDS[need_key]["soil"]}."'
    )


def choose_fix(world: World, hero: Entity, helper: Entity, need_key: str) -> Optional[Tool]:
    tool = select_tool(world.place, need_key)
    if tool is None:
        return None
    world.say(
        f"{helper.pronoun().capitalize()} brought {tool.phrase} and showed how it could keep prying eyes away."
    )
    return tool


def accept(world: World, hero: Entity, helper: Entity, tool: Tool) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    helper.memes["pride"] = helper.memes.get("pride", 0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} nodded, and together they set up {tool.label}."
    )
    world.say(
        f"After that, {world.place.label} held its secret safely, and {hero.id} could breathe easy inside the little hidden place."
    )


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    world.facts["need_key"] = params.privacy_need
    world.facts["tool_key"] = params.tool
    world.facts["place"] = place
    world.facts["params"] = params

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        phrase=f"{'a' if params.hero_name[0].lower() not in 'aeiou' else 'an'} {params.trait} {params.hero_type} named {params.hero_name}",
        memes={"trait": 1.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=params.helper_type,
        label=f"the {params.helper_type}",
        phrase=f"the {params.helper_type}",
    ))

    tool = TOOLS[params.tool]

    introduce(world, hero)
    set_scene(world)
    world.para()
    desire(world, hero, params.privacy_need)
    worry(world, helper, hero, params.privacy_need)
    world.para()
    chosen = choose_fix(world, hero, helper, params.privacy_need)
    if chosen is not None:
        accept(world, hero, helper, chosen)

    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["tool"] = chosen
    world.facts["resolved"] = chosen is not None
    return world


# ---------------------------------------------------------------------------
# QA and narration helpers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    need = NEEDS[p.privacy_need]["want"]
    return [
        f"Write a short folk tale about a child who wants to {need} in {world.place.label}.",
        f"Tell a gentle story where {p.hero_name} needs privacy and a wise helper offers a simple fix.",
        f"Write a child-friendly quest story about keeping a secret safe without being rude.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    tool = world.facts["tool"]
    need = NEEDS[p.privacy_need]
    qa = [
        QAItem(
            question=f"What did {p.hero_name} want in {world.place.label}?",
            answer=f"{p.hero_name} wanted to {need['want']} in {world.place.label}.",
        ),
        QAItem(
            question=f"Who worried that the place was too open?",
            answer=f"{helper.label.capitalize()} worried that {need['risk']}.",
        ),
        QAItem(
            question=f"What did {p.hero_name} and {helper.label} use to make the place private?",
            answer=f"They used {tool.label} to keep the secret space safe." if tool else "They did not find a good fix.",
        ),
    ]
    if world.facts["resolved"]:
        qa.append(
            QAItem(
                question=f"How did the story end for {p.hero_name}?",
                answer=f"{p.hero_name} felt relieved, and the little private place stayed safe.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is privacy?",
            answer="Privacy means having a little space that others do not look into or disturb.",
        ),
        QAItem(
            question="What is a hedge for?",
            answer="A hedge can mark a boundary, make a garden feel private, and give birds a place to rest.",
        ),
        QAItem(
            question="Why do people sometimes use curtains or screens?",
            answer="People use curtains or screens to block a view and make a room or corner feel quieter and more private.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        out.append(f"{i}. {q}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  place={world.place.id}")
    lines.append(f"  prying={world.prying} noise={world.noise}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A privacy need is at risk in any place.
at_risk(P, N) :- place(P), need(N).

% A tool is a valid fix when it guards seeing and fits the place.
valid_fix(P, N, T) :- at_risk(P, N), tool(T), fits(T, P), guards(T, seeing).

valid_story(P, N, T) :- valid_fix(P, N, T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for t in [tool for tool in TOOLS.values() if pid in tool.fits]:
            lines.append(asp.fact("fits", t.id, pid))
    for nid in NEEDS:
        lines.append(asp.fact("need", nid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for g in sorted(t.guards):
            lines.append(asp.fact("guards", tid, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_fixes() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_fix/3."))
    return sorted(set(asp.atoms(model, "valid_fix")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_fixes())
    if python_set == asp_set:
        print(f"OK: ASP matches Python ({len(asp_set)} valid fixes).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  only in ASP:", sorted(asp_set - python_set))
    print("  only in Python:", sorted(python_set - asp_set))
    return 1


def valid_combos() -> list[tuple]:
    combos = []
    for place_id, place in PLACES.items():
        for need_id in NEEDS:
            for tool_id, tool in TOOLS.items():
                if place_id in tool.fits and "seeing" in tool.guards:
                    combos.append((place_id, need_id, tool_id))
    return combos


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    privacy_need: str
    tool: str
    hero_name: str
    hero_type: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale privacy quest storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--privacy-need", choices=NEEDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather", "neighbor"])
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
    combos = valid_combos()
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.privacy_need is None or c[1] == args.privacy_need)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, need, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_type = "girl" if gender == "girl" else "boy"
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_type = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather", "neighbor"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, privacy_need=need, tool=tool, hero_name=hero_name,
                       hero_type=hero_type, helper_type=helper_type, trait=trait)


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


CURATED = [
    StoryParams("cottage_garden", "privacy", "hedge", "Mila", "girl", "grandmother", "gentle"),
    StoryParams("forest_glade", "secret_note", "screen", "Tobin", "boy", "father", "curious"),
    StoryParams("mill_pond", "changing_space", "screen", "Anya", "girl", "mother", "thoughtful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        fixes = asp_valid_fixes()
        print(f"{len(fixes)} valid fixes:\n")
        for p, n, t in fixes:
            print(f"  {p:14} {n:15} {t}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
