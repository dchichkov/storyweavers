#!/usr/bin/env python3
"""
A tiny storyworld for a mysterious teamwork tale in a rhyming-story style.

A seed tale imagined from the prompt:
- A small group finds a mysterious problem.
- They cannot solve it alone.
- They work together, each using a different helpful skill.
- The mystery is resolved, and the ending image shows what changed.

The world model tracks physical meters and emotional memes for a few typed
entities, and the prose is generated from that state rather than from a frozen
template.
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
# Core world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    helper_for: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    vibe: str
    hides: set[str] = field(default_factory=set)  # what kinds of clue/problems it can hold


@dataclass
class Mystery:
    id: str
    clue: str
    trouble: str
    reveal: str
    needed: set[str]  # helpers needed to solve it
    setting_kind: str = "outdoor"


@dataclass
class Tool:
    id: str
    label: str
    use: str
    helps: set[str]


class World:
    def __init__(self, place: Place, mystery: Mystery):
        self.place = place
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        w = World(self.place, self.mystery)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "garden": Place(name="the garden", vibe="green and bright", hides={"lost", "hidden"}),
    "attic": Place(name="the attic", vibe="dusty and quiet", hides={"lost", "hidden"}),
    "forest": Place(name="the forest", vibe="deep and whispery", hides={"lost", "hidden", "glow"}),
}

MYSTERIES = {
    "glow": Mystery(
        id="glow",
        clue="a tiny glow behind the leaves",
        trouble="a shy lantern was stuck under a fallen branch",
        reveal="the lantern was a firefly lamp that needed a gentle lift",
        needed={"lift", "look"},
        setting_kind="outdoor",
    ),
    "lost_key": Mystery(
        id="lost_key",
        clue="a little silver shine near the rug",
        trouble="a key had slipped behind a box and no one could reach it",
        reveal="the key was hiding beside a rolled-up map",
        needed={"reach", "look"},
        setting_kind="indoor",
    ),
    "hollow_song": Mystery(
        id="hollow_song",
        clue="a hollow hum under the roots",
        trouble="a song-box had fallen into a root hole and gone quiet",
        reveal="the song-box was safe once the roots were moved apart",
        needed={"move", "listen"},
        setting_kind="outdoor",
    ),
}

TOOLS = {
    "lantern": Tool(id="lantern", label="lantern", use="shine a beam", helps={"look"}),
    "stick": Tool(id="stick", label="long stick", use="hook things close", helps={"reach"}),
    "gloves": Tool(id="gloves", label="soft gloves", use="move things safely", helps={"move"}),
    "ear": Tool(id="ear", label="quiet ear", use="hear tiny sounds", helps={"listen"}),
    "stepstool": Tool(id="stepstool", label="small stepstool", use="stand a little taller", helps={"reach"}),
    "helper_rope": Tool(id="rope", label="helper rope", use="pull together", helps={"lift"}),
}

NAMES = ["Mia", "Leo", "Nora", "Finn", "Ava", "Theo", "Zoe", "Eli"]
ROLES = ["girl", "boy"]
HUMAN_TRAITS = ["brave", "kind", "curious", "patient", "gentle", "clever"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mystery is solvable when all needed helper-abilities are present.
solvable(M) :- mystery(M), need(M, N), not missing(M, N).

missing(M, N) :- need(M, N), not has_help(N).

% Teamwork succeeds when the mystery is solvable and there are at least two
% characters participating.
teamwork_success(M) :- solvable(M), pair_needed.

valid_story(P, M, G) :- place(P), mystery(M), gender(G),
                        place_kind(P, K), mystery_kind(M, K),
                        character_gender(G, M),
                        solvable(M), teamwork_possible(M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("place_kind", pid, "outdoor" if p.name != "the attic" else "indoor"))
        for h in sorted(p.hides):
            lines.append(asp.fact("hides", pid, h))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("mystery_kind", mid, m.setting_kind))
        for n in sorted(m.needed):
            lines.append(asp.fact("need", mid, n))
    for tid, t in TOOLS.items():
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", tid, h))
    for g in ROLES:
        lines.append(asp.fact("gender", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def mystery_matches_place(place: Place, mystery: Mystery) -> bool:
    if mystery.setting_kind == "indoor":
        return place.name == "the attic"
    return place.name != "the attic"


def teamwork_possible(mystery: Mystery) -> bool:
    return bool(mystery.needed)


def has_required_tools(mystery: Mystery, tools: list[Tool]) -> bool:
    needed = set(mystery.needed)
    have = set()
    for t in tools:
        have |= t.helps
    return needed <= have


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for mid, mystery in MYSTERIES.items():
            if mystery_matches_place(place, mystery) and teamwork_possible(mystery):
                combos.append((pid, mid))
    return combos


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def choose_tools(mystery: Mystery) -> list[Tool]:
    selected: list[Tool] = []
    needed = set(mystery.needed)
    for tool in TOOLS.values():
        if tool.helps & needed:
            selected.append(tool)
            needed -= tool.helps
        if not needed:
            break
    return selected


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    if not mystery_matches_place(place, mystery):
        raise StoryError("That mystery does not fit that setting.")
    if not teamwork_possible(mystery):
        raise StoryError("That mystery has no teamwork path.")
    world = World(place, mystery)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={}))
    friend_name = "Pal"
    friend_type = "boy" if params.gender == "girl" else "girl"
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, meters={}, memes={}))
    helper = world.add(Entity(id="Helper", kind="character", type="adult", meters={}, memes={}))

    tools = choose_tools(mystery)
    for t in tools:
        world.add(Entity(id=t.id, type="tool", label=t.label, owner=params.name, helper_for=mystery.id))

    world.facts.update(hero=hero, friend=friend, helper=helper, tools=tools, mystery=mystery, place=place)
    return world


def intro_line(hero: Entity, trait: str, place: Place) -> str:
    return f"{hero.id} was a {trait} little {hero.type} who wandered where the breezes play, in {place.name} so bright and gray."


def mystery_line(mystery: Mystery, place: Place) -> str:
    return f"But then came a clue, so mysterious and new: {mystery.clue} in {place.name} with a hush-hush view."


def teamwork_line(hero: Entity, friend: Entity, tools: list[Tool], mystery: Mystery) -> str:
    if tools:
        tool_text = " and ".join(t.label for t in tools)
        return f"{hero.id} took the {tool_text}; {friend.id} came too. Together they knew just what to do."
    return f"{hero.id} and {friend.id} stood side by side, and shared one brave idea to guide."


def solve_mystery(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    helper = world.facts["helper"]
    mystery = world.facts["mystery"]
    tools = world.facts["tools"]

    hero.memes["curious"] = 1
    friend.memes["helpful"] = 1
    helper.memes["kind"] = 1

    world.say(intro_line(hero, world.facts["params_trait"], world.facts["place"]))
    world.say(mystery_line(mystery, world.facts["place"]))
    world.para()
    world.say(f"{hero.id} frowned and said, \"This puzzle feels deep.\"")
    world.say(f"{friend.id} replied, \"Let's work together and take a careful peek.\"")
    if tools:
        world.say(teamwork_line(hero, friend, tools, mystery))
    else:
        world.say(f"{helper.id} came along and said, \"We'll solve it as one.\"")
    world.para()
    world.say(f"{hero.id} used patience, {friend.id} used care, and {helper.id} helped them compare.")
    if "look" in mystery.needed:
        world.say("A lantern shone low, and the shadows could go.")
    if "reach" in mystery.needed:
        world.say("A stick and a stepstool made the hard spot feel cool.")
    if "move" in mystery.needed:
        world.say("Soft gloves moved the roots with a gentle little poot.")
    if "listen" in mystery.needed:
        world.say("A quiet ear heard the softest hum clear.")
    world.say(f"At last they found the answer: {mystery.reveal}.")
    hero.memes["joy"] = 1
    friend.memes["joy"] = 1
    helper.memes["joy"] = 1
    world.para()
    world.say(f"{hero.id} smiled, {friend.id} grinned, and the room or woods felt light as a spin.")
    world.say(f"The mystery was ended, and the teamwork was splendid.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    world.facts["params_trait"] = params.trait
    solve_mystery(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m: Mystery = f["mystery"]
    p: Place = f["place"]
    return [
        f'Write a short rhyming story for a young child about a mysterious problem in {p.name} and a teamwork solution.',
        f'Create a gentle mystery story where friends use teamwork to solve {m.clue}.',
        f'Write a simple story that ends with everyone feeling proud because they solved a mystery together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    mystery: Mystery = f["mystery"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who led the teamwork in {place.name}?",
            answer=f"{hero.id} led the teamwork, and {friend.id} helped beside {hero.pronoun('object')}.",
        ),
        QAItem(
            question=f"What made the story feel mysterious?",
            answer=f"The mysterious clue was {mystery.clue}, and it led everyone to look more closely.",
        ),
        QAItem(
            question=f"How did the friends solve the problem?",
            answer=f"They used teamwork, careful looking, and the right helpers to uncover that {mystery.reveal}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help one another and combine their different strengths to reach a goal together.",
        ),
        QAItem(
            question="What does mysterious mean?",
            answer="Mysterious means something is puzzling or hard to understand right away.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI and output
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mysterious teamwork rhyming-story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=ROLES)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=HUMAN_TRAITS)
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(ROLES)
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(HUMAN_TRAITS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, trait=trait)


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
        if e.kind == "character":
            bits.append("character")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set((p, m) for (p, m, *_rest) in asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, mystery in valid_combos():
            params = StoryParams(
                place=place,
                mystery=mystery,
                name=NAMES[0],
                gender=ROLES[0],
                trait=HUMAN_TRAITS[0],
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
