#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gefilte_jambalaya_patrol_mystery_to_solve_flashback.py
====================================================================================================

A small superhero-style story world with a mystery to solve, a flashback, and a
little magic.

Premise:
- A patrol team protects a city block at dusk.
- A strange clue appears: a sweet-fishy smell mixed with spicy steam.
- The heroes remember a flashback that explains the clue.
- Magic helps them solve the mystery and end the patrol with a win.

This world is intentionally compact and constraint-checked. It varies by the
hero, the place, the mystery object, and the final magical solution, but it only
generates cases where the clue and the fix make sense together.

Seed words used in the domain:
- gefilte
- jambalaya
- patrol

Narrative instruments:
- Mystery to Solve
- Flashback
- Magic

Style:
- Superhero Story, child-facing, concrete, and state-driven.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    magical: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    name: str
    night: bool = True
    supports: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    flashback: str
    culprit: str
    solved_by: str
    mess: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicTool:
    id: str
    label: str
    phrase: str
    effect: str
    helps: set[str] = field(default_factory=set)
    flair: str = ""


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_mystery_hint(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes.get("curious", 0.0) < THRESHOLD:
            continue
        mystery: Mystery = world.facts["mystery"]
        sig = ("hint", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["focus"] = hero.memes.get("focus", 0.0) + 1
        out.append(f"{hero.id} noticed the clue and leaned closer to the trail.")
    return out


def _r_magic_help(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes.get("focus", 0.0) < THRESHOLD:
            continue
        tool: MagicTool = world.facts.get("magic")
        if not tool:
            continue
        sig = ("magic", hero.id, tool.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
        out.append(f"The magic made the clue glow like a tiny star.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("mystery_hint", _r_mystery_hint),
    Rule("magic_help", _r_magic_help),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setup_line(place: Place) -> str:
    return {
        "dock": "The dock was quiet except for the slap of water against the posts.",
        "alley": "The alley glowed under one sleepy streetlamp.",
        "rooftop": "The rooftop felt wide and windy above the sleeping city.",
    }.get(place.id, f"{place.name.capitalize()} was calm and ready for a patrol.")


def hero_intro(hero: Entity) -> str:
    trait = next((t for t in hero.traits if t != "young"), "brave")
    return f"{hero.id} was a young {trait} hero who loved helping the city at night."


def patrol_line(hero: Entity, sidekick: Entity, place: Place) -> str:
    return f"Every evening, {hero.id} and {sidekick.id} went on patrol at {place.name} to keep their block safe."


def mystery_setup(world: World, hero: Entity, sidekick: Entity, mystery: Mystery) -> None:
    world.say(hero_intro(hero))
    world.say(patrol_line(hero, sidekick, world.place))
    world.say(f"Then a strange clue drifted by: {mystery.clue}.")


def flashback(world: World, hero: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} blinked, and a flashback popped into mind. Earlier, {mystery.flashback}"
    )


def suspect_scene(world: World, hero: Entity, mystery: Mystery) -> None:
    world.say(
        f"That made the mystery harder for a moment, because the clue pointed at {mystery.culprit},"
        f" and {hero.id} had to think carefully before jumping to the wrong answer."
    )


def magic_scene(world: World, hero: Entity, tool: MagicTool) -> None:
    hero.memes["curious"] = hero.memes.get("curious", 0.0) + 1
    world.say(
        f"At last, {hero.id} lifted {tool.phrase}. {tool.flair} {tool.effect}"
    )
    propagate(world, narrate=True)


def solve_scene(world: World, hero: Entity, mystery: Mystery, tool: MagicTool, sidekick: Entity) -> None:
    hero.memes["sureness"] = hero.memes.get("sureness", 0.0) + 1
    world.say(
        f"The glow showed the real answer: {mystery.reveal}."
    )
    world.say(
        f"{hero.id} and {sidekick.id} solved the mystery by using {tool.label}, and the patrol ended with everyone smiling."
    )


def tell(place: Place, mystery: Mystery, tool: MagicTool, hero_name: str = "Nova",
         hero_type: str = "girl", sidekick_name: str = "Pip") -> World:
    world = World(place)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["young", "brave", "curious"],
        meters={"meters": 0.0},
        memes={"curious": 1.0},
    ))
    sidekick = world.add(Entity(
        id=sidekick_name,
        kind="character",
        type="boy",
        traits=["small", "clever"],
        meters={"meters": 0.0},
        memes={"curious": 1.0},
    ))
    world.facts["mystery"] = mystery
    world.facts["magic"] = tool
    world.facts["hero"] = hero
    world.facts["sidekick"] = sidekick

    mystery_setup(world, hero, sidekick, mystery)
    world.para()
    world.say(setup_line(place))
    flashback(world, hero, mystery)
    suspect_scene(world, hero, mystery)
    world.para()
    magic_scene(world, hero, tool)
    solve_scene(world, hero, mystery, tool, sidekick)

    world.facts["solved"] = True
    return world


PLACES = {
    "dock": Place(id="dock", name="the dock", supports={"patrol", "mystery", "night"}),
    "alley": Place(id="alley", name="the alley", supports={"patrol", "mystery", "night"}),
    "rooftop": Place(id="rooftop", name="the rooftop", supports={"patrol", "mystery", "night"}),
}

MYSTERIES = {
    "lunch_swap": Mystery(
        id="lunch_swap",
        clue="a swirl of gefilte and jambalaya drifting from the same open window",
        flashback="they had passed a little cafe where one cook stirred gefilte while another stirred jambalaya",
        culprit="the wind and a tipped lunch cart",
        solved_by="magic lantern",
        mess="mixed-up lunch smells",
        reveal="the lunch cart had rolled, and the two pots had swapped places by accident",
        tags={"gefilte", "jambalaya", "mystery"},
    ),
    "spice_trail": Mystery(
        id="spice_trail",
        clue="a spicy trail that smelled like jambalaya beside a sweet, fishy note of gefilte",
        flashback="they remembered a market stall with two cooking pots sitting side by side",
        culprit="a crate that had bumped into the stall",
        solved_by="magic ribbon",
        mess="spilled steam and clues",
        reveal="the crate bumped the stall, and the steam mixed together into one odd trail",
        tags={"gefilte", "jambalaya", "patrol"},
    ),
}

MAGIC = {
    "lantern": MagicTool(
        id="lantern",
        label="a magic lantern",
        phrase="the magic lantern",
        effect="Its light pointed straight to the tipped cart.",
        helps={"mystery", "gefilte", "jambalaya"},
        flair="A soft gold glow filled the alley.",
    ),
    "ribbon": MagicTool(
        id="ribbon",
        label="a magic ribbon",
        phrase="the magic ribbon",
        effect="Its sparkly trail traced the true path through the air.",
        helps={"mystery", "patrol"},
        flair="Silver sparks danced at its edges.",
    ),
}

HERO_NAMES = ["Nova", "Mira", "Sage", "Ivy", "Juno", "Ada", "Zara", "Nia"]
SIDEKICK_NAMES = ["Pip", "Bo", "Len", "Tico", "Max", "Roo"]
TRAITS = ["brave", "quick", "kind", "steady", "sharp"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    magic: str
    hero: str
    sidekick: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        if "patrol" not in place.supports or "mystery" not in place.supports:
            continue
        for m_id, m in MYSTERIES.items():
            for tool_id, tool in MAGIC.items():
                if {"mystery"} & tool.helps and m_id in MYSTERIES:
                    combos.append((place_id, m_id, tool_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero patrol story with a mystery, a flashback, and magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.mystery is None or c[1] == args.mystery)
        and (args.magic is None or c[2] == args.magic)
    ]
    if not combos:
        raise StoryError("(No valid story matches the given options.)")
    place, mystery, magic = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICK_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, magic=magic, hero=hero, sidekick=sidekick, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m: Mystery = f["mystery"]
    tool: MagicTool = f["magic"]
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    return [
        f'Write a short superhero story for a young child that includes the words "gefilte", "jambalaya", and "patrol".',
        f"Tell a mystery story where {hero.id} and {sidekick.id} go on patrol, notice a clue, remember a flashback, and use magic to solve it.",
        f"Write a gentle nighttime hero story in which {m.clue.lower()} leads to a surprising answer.",
        f"Make the ending show how {tool.label} helps the team solve the mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    mystery: Mystery = f["mystery"]
    tool: MagicTool = f["magic"]
    place = world.place.name
    return [
        QAItem(
            question=f"What kind of team was {hero.id} and {sidekick.id} on at {place}?",
            answer=f"They were on patrol, watching over {place} together.",
        ),
        QAItem(
            question=f"What strange clue started the mystery at {place}?",
            answer=f"The clue was {mystery.clue}. That made the heroes stop and think.",
        ),
        QAItem(
            question=f"What memory came back to {hero.id} during the story?",
            answer=f"The flashback was this: {mystery.flashback}. It helped explain the clue.",
        ),
        QAItem(
            question=f"How did the heroes solve the mystery?",
            answer=f"They used {tool.label} to reveal the real answer: {mystery.reveal}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    out = []
    out.append(QAItem(
        question="What is patrol?",
        answer="A patrol is a time when heroes walk or drive around to keep a place safe and watch for trouble.",
    ))
    if "gefilte" in mystery.tags:
        out.append(QAItem(
            question="What is gefilte?",
            answer="Gefilte is a kind of food made from fish, often shaped into patties or balls and served as a dish.",
        ))
    if "jambalaya" in mystery.tags:
        out.append(QAItem(
            question="What is jambalaya?",
            answer="Jambalaya is a warm rice dish with spices and other foods mixed together in one pot.",
        ))
    out.append(QAItem(
        question="What is a flashback in a story?",
        answer="A flashback is when a story briefly shows something that happened earlier, so the reader can understand the present moment better.",
    ))
    out.append(QAItem(
        question="What does magic do in a superhero story?",
        answer="Magic can help a hero see clues, open hidden paths, or solve a problem in a surprising way.",
    ))
    return out


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  place={world.place.id}")
    lines.append(f"  fired={sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A place is acceptable when it supports both patrol and mystery stories.
okay_place(P) :- place(P), supports(P, patrol), supports(P, mystery).

% A mystery is acceptable when its clue mentions both seed words.
seed_mystery(M) :- mystery(M), has_tag(M, gefilte), has_tag(M, jambalaya).

% Magic must help the mystery.
useful_magic(T) :- magic(T), helps(T, mystery).

valid_story(P, M, T) :- okay_place(P), seed_mystery(M), useful_magic(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for s in sorted(p.supports):
            lines.append(asp.fact("supports", pid, s))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("has_tag", mid, t))
    for tid, t in MAGIC.items():
        lines.append(asp.fact("magic", tid))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        MYSTERIES[params.mystery],
        MAGIC[params.magic],
        hero_name=params.hero,
        sidekick_name=params.sidekick,
    )
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for place, mystery, magic in combos:
            print(f"  {place:8} {mystery:14} {magic}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="dock", mystery="lunch_swap", magic="lantern", hero="Nova", sidekick="Pip", trait="brave"),
            StoryParams(place="alley", mystery="spice_trail", magic="ribbon", hero="Mira", sidekick="Bo", trait="quick"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.hero}: {p.mystery} at {p.place} (magic: {p.magic})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
