#!/usr/bin/env python3
"""
storyworlds/worlds/afford_conflict_teamwork_mystery.py
=====================================================

A standalone story world for a small mystery domain with affordances,
conflict, and teamwork.

Seed tale:
---
Nia and her brother Ben were helping at the old attic library. The school had
asked them to find a missing silver key before the evening reading time. They
noticed that the lantern could afford a bright search, but only if they worked
together: one child held the lamp steady while the other checked the dusty
shelves. When Ben wanted to rush and grab the first shiny thing he saw, Nia
pointed out that the clues did not match. They split up the work, followed the
tracks of dust and a tiny blue ribbon, and found the key tucked inside a hollow
book. The librarian smiled, and the two children learned that teamwork solved
the mystery better than arguing.

World shape:
- Physical meters: distance, dust, brightness, effort.
- Emotional memes: worry, conflict, trust, joy, teamwork.
- The narrative is driven by the simulated state and a short causal chain:
  clues -> conflict -> teamwork -> discovery.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    afford: set[str] = field(default_factory=set)
    hidden_spot: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    leads_to: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    afford: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class StoryParams:
    place: str
    mystery: str
    tool: str
    hero: str
    helper: str
    hero_kind: str
    helper_kind: str
    seed: Optional[int] = None


PLACES = {
    "attic": Place(
        id="attic",
        label="the old attic library",
        afford={"search", "listen", "climb"},
        hidden_spot="inside a hollow book",
        tags={"library", "attic", "mystery"},
    ),
    "shed": Place(
        id="shed",
        label="the garden shed",
        afford={"search", "listen", "open"},
        hidden_spot="behind a stack of boxes",
        tags={"shed", "mystery"},
    ),
    "hall": Place(
        id="hall",
        label="the quiet school hall",
        afford={"search", "listen", "walk"},
        hidden_spot="under the long bench",
        tags={"school", "hall", "mystery"},
    ),
}

MYSTERIES = {
    "key": Clue(
        id="key",
        label="silver key",
        phrase="a missing silver key",
        leads_to="unlock the reading chest",
        tags={"key", "silver", "missing"},
    ),
    "ribbon": Clue(
        id="ribbon",
        label="blue ribbon",
        phrase="a tiny blue ribbon",
        leads_to="find the secret drawer",
        tags={"ribbon", "blue", "missing"},
    ),
    "glove": Clue(
        id="glove",
        label="glove",
        phrase="a single red glove",
        leads_to="open the dusty case",
        tags={"glove", "red", "missing"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a bright lantern",
        afford={"search", "see"},
        tags={"lantern", "light", "afford"},
    ),
    "magnifier": Tool(
        id="magnifier",
        label="magnifier",
        phrase="a little magnifier",
        afford={"inspect", "search"},
        tags={"magnifier", "afford"},
    ),
    "clipboard": Tool(
        id="clipboard",
        label="clipboard",
        phrase="a small clipboard",
        afford={"note", "search"},
        tags={"clipboard", "afford"},
    ),
}

GIRL_NAMES = ["Nia", "Maya", "Lena", "Ivy", "Mila", "Zoe"]
BOY_NAMES = ["Ben", "Owen", "Noah", "Jude", "Leo", "Sam"]
TRAITS = ["careful", "curious", "patient", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES:
        for mystery in MYSTERIES:
            for tool in TOOLS:
                if tool == "lantern" or mystery in {"key", "ribbon", "glove"}:
                    out.append((place, mystery, tool))
    return out


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.afford):
            lines.append(asp.fact("afford", pid, a))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for a in sorted(t.afford):
            lines.append(asp.fact("afford", tid, a))
    return "\n".join(lines)


ASP_RULES = r"""
eligible(P,M,T) :- place(P), mystery(M), tool(T), afford(P,search), afford(T,search).
show_eligible(P,M,T) :- eligible(P,M,T).
#show show_eligible/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "show_eligible")))


def clue_at_risk(place: Place, mystery: Clue, tool: Tool) -> bool:
    return "search" in place.afford and "search" in tool.afford


def tell(place: Place, mystery: Clue, tool: Tool, hero: str, helper: str, hero_kind: str, helper_kind: str) -> World:
    world = World(place)
    a = world.add(Entity(id=hero, kind="character", type=hero_kind, role="hero"))
    b = world.add(Entity(id=helper, kind="character", type=helper_kind, role="helper"))
    key = world.add(Entity(id="mystery", kind="thing", type="thing", label=mystery.label, tags=set(mystery.tags)))
    prop = world.add(Entity(id="tool", kind="thing", type="thing", label=tool.label, tags=set(tool.tags)))
    room = world.add(Entity(id="place", kind="thing", type="place", label=place.label, tags=set(place.tags)))

    a.memes["worry"] = 1.0
    b.memes["trust"] = 1.0
    a.meters["effort"] = 0.0
    b.meters["effort"] = 0.0
    key.meters["dust"] = 1.0
    prop.meters["brightness"] = 1.0 if tool.id == "lantern" else 0.5

    world.say(f"{a.id} and {b.id} arrived at {room.label_word}.")
    world.say(f"They had {tool.phrase}, which could afford a careful search.")
    world.say(f"Somewhere in the room, {mystery.phrase} was waiting.")
    world.para()

    if not clue_at_risk(place, mystery, tool):
        raise StoryError("This tool cannot afford a search here.")

    a.memes["conflict"] += 1
    world.say(f"{a.id} wanted to rush, but {b.id} pointed at the dusty clues.")
    world.say(f'"Let\'s look closely," {b.id} said. "The clue does not fit the first shiny thing."')

    world.para()
    a.meters["effort"] += 1
    b.meters["effort"] += 1
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1
    a.memes["conflict"] = 0
    b.memes["conflict"] = 0
    world.say(f"They split the work: one held the {tool.label}, and the other checked the shelves.")
    world.say(f"That teamwork afforded a better look at the dusty corners.")

    world.para()
    key.meters["found"] = 1
    a.meters["brightness"] += prop.meters["brightness"]
    world.say(f"At last, they found the {mystery.label} {place.hidden_spot}.")
    world.say(f"It was tucked where the light could reach only because they stayed calm together.")
    world.say(f"The mystery ended with a grin, and the room felt clear and peaceful again.")

    world.facts.update(
        hero=a,
        helper=b,
        mystery=mystery,
        tool=tool,
        place=place,
        found_where=place.hidden_spot,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story where {f["hero"].id} and {f["helper"].id} use a {f["tool"].label} to search {f["place"].label}.',
        f'Tell a story about a missing {f["mystery"].label} where teamwork solves the clue and conflict turns into a careful search.',
        f'Write a short mystery with the word "afford" in it, and end with the hidden item being found.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b = f["hero"], f["helper"]
    myst = f["mystery"]
    tool = f["tool"]
    place = f["place"]
    return [
        QAItem(
            question=f"What were {a.id} and {b.id} trying to find at {place.label}?",
            answer=f"They were trying to find {myst.phrase}. The clue was hidden {f['found_where']}.",
        ),
        QAItem(
            question=f"Why did {a.id} stop arguing and work with {b.id}?",
            answer=f"{b.id} noticed that the first shiny thing did not fit the clues. Working together afforded a better search, so the conflict faded.",
        ),
        QAItem(
            question=f"How did the {tool.label} help the mystery?",
            answer=f"The {tool.label} afforded a bright search, so they could see the dusty shelves and find the hidden clue.",
        ),
        QAItem(
            question=f"Where was the {myst.label} found?",
            answer=f"It was found {f['found_where']}, after the children searched carefully together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does afford mean?",
            answer="Afford can mean that something makes an action possible or easier. A bright lantern can afford a better search in the dark.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together and each person helps. It can solve a problem better than arguing.",
        ),
        QAItem(
            question="Why can a mystery need careful clues?",
            answer="A mystery is solved by noticing small clues. If the clues do not match, guessing too fast can lead to the wrong answer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if e.memes:
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"{e.id}: {e.label_word} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="attic", mystery="key", tool="lantern", hero="Nia", helper="Ben", hero_kind="girl", helper_kind="boy"),
    StoryParams(place="shed", mystery="ribbon", tool="magnifier", hero="Maya", helper="Jude", hero_kind="girl", helper_kind="boy"),
    StoryParams(place="hall", mystery="glove", tool="clipboard", hero="Leo", helper="Ivy", hero_kind="boy", helper_kind="girl"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world with affordances, conflict, and teamwork.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--hero-kind", choices=["girl", "boy"])
    ap.add_argument("--helper-kind", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, mystery, tool = rng.choice(sorted(combos))
    hero_kind = args.hero_kind or rng.choice(["girl", "boy"])
    helper_kind = args.helper_kind or ("boy" if hero_kind == "girl" else "girl")
    hero_pool = GIRL_NAMES if hero_kind == "girl" else BOY_NAMES
    helper_pool = GIRL_NAMES if helper_kind == "girl" else BOY_NAMES
    hero = args.hero or rng.choice(hero_pool)
    helper_choices = [n for n in helper_pool if n != hero] or helper_pool
    helper = args.helper or rng.choice(helper_choices)
    return StoryParams(
        place=place,
        mystery=mystery,
        tool=tool,
        hero=hero,
        helper=helper,
        hero_kind=hero_kind,
        helper_kind=helper_kind,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.mystery not in MYSTERIES or params.tool not in TOOLS:
        raise StoryError("Invalid story parameters.")
    world = tell(PLACES[params.place], MYSTERIES[params.mystery], TOOLS[params.tool], params.hero, params.helper, params.hero_kind, params.helper_kind)
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


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py != asp_set:
        print("ASP mismatch")
        print("only py", sorted(py - asp_set))
        print("only asp", sorted(asp_set - py))
        return 1
    print(f"OK: {len(py)} valid combos")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show show_eligible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
