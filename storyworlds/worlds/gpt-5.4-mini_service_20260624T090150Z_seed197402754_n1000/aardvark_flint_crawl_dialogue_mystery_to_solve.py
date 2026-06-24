#!/usr/bin/env python3
"""
A tiny animal-story world: an aardvark finds a flint, begins to crawl through
a puzzling trail, and uses dialogue with a friend to solve a small mystery.
The world is state-driven: the clue, the worry, the search, and the reveal are
all modeled as changes in physical meters and emotional memes.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"aardvark", "fox", "mouse", "rabbit", "badger", "hedgehog"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the warm burrow"
    affordances: set[str] = field(default_factory=lambda: {"crawl", "talk", "search"})


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: set[str]


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    points_to: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "burrow": Setting(place="the warm burrow", affordances={"crawl", "talk", "search"}),
    "meadow": Setting(place="the meadow path", affordances={"crawl", "talk", "search"}),
    "riverbank": Setting(place="the riverbank trail", affordances={"crawl", "talk", "search"}),
}

TOOLS = {
    "flint": Tool(
        id="flint",
        label="flint",
        phrase="a small flint with a sharp edge",
        helps_with={"scratch", "spark", "mark"},
    ),
    "leaf": Tool(
        id="leaf",
        label="leaf",
        phrase="a big leaf",
        helps_with={"carry", "cover"},
    ),
}

CLUES = {
    "marks": Clue(
        id="marks",
        label="mud marks",
        phrase="tiny mud marks",
        points_to="burrow",
    ),
    "crumbs": Clue(
        id="crumbs",
        label="crumbs",
        phrase="crumbs of seed",
        points_to="meadow",
    ),
    "shine": Clue(
        id="shine",
        label="shine",
        phrase="a little shine on the path",
        points_to="riverbank",
    ),
}

CHARACTER_NAMES = {
    "aardvark": ["Ari", "Milo", "Pip", "Nori"],
    "fox": ["Faye", "Tess", "Luna", "Ivy"],
    "rabbit": ["Rosie", "Bun", "Daisy", "Penny"],
    "hedgehog": ["Hugo", "Nell", "Poppy", "June"],
}


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hero_type: str
    friend_type: str
    tool: str
    clue: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness / ASP twin
# ---------------------------------------------------------------------------

def reasonableness_gate(params: StoryParams) -> None:
    if params.hero_type != "aardvark":
        raise StoryError("This world is built for an aardvark hero.")
    if params.tool != "flint":
        raise StoryError("The seed premise expects a flint as the important object.")
    if params.clue not in CLUES:
        raise StoryError("Unknown clue.")
    if params.place not in SETTINGS:
        raise StoryError("Unknown setting.")


ASP_RULES = r"""
hero(aardvark).
tool(flint).
action(crawl).
setting(burrow; meadow; riverbank).

solves(H, C) :- hero(H), clue(C), asks(H, C), follows(C, P), reaches(H, P).
reaches(H, burrow) :- sees(H, mud_marks).
reaches(H, meadow) :- sees(H, crumbs).
reaches(H, riverbank) :- sees(H, shine).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy
    lines = [
        asp.fact("hero", "aardvark"),
        asp.fact("tool", "flint"),
        asp.fact("action", "crawl"),
    ]
    for key in SETTINGS:
        lines.append(asp.fact("setting", key))
    for key in CLUES:
        lines.append(asp.fact("clue", key))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def _gentle_name(options: list[str], rng: random.Random) -> str:
    return rng.choice(options)


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_type))
    flint = world.add(Entity(id="flint", type="flint", label="flint", phrase=TOOLS["flint"].phrase, owner=hero.id))
    clue = world.add(Entity(id=params.clue, type="clue", label=CLUES[params.clue].label, phrase=CLUES[params.clue].phrase))
    world.facts.update(hero=hero, friend=friend, flint=flint, clue=clue, params=params)

    # setup
    world.say(f"{hero.id} was an aardvark who liked quiet mornings in {world.setting.place}.")
    world.say(f"{hero.id} found {flint.phrase} and tucked it close, because it looked useful.")
    world.say(f"Nearby, {friend.id} listened carefully, ready for a story or a puzzle.")

    # tension
    world.para()
    hero.memes["curiosity"] = hero.meme("curiosity") + 1
    world.say(f"Then {hero.id} noticed {clue.phrase}.")
    world.say(f"{hero.id} wanted to crawl after the clue, but the trail was twisty and dark.")
    hero.meters["crawl"] = hero.meter("crawl") + 1
    if params.clue == "marks":
        world.say(f"The muddy little prints seemed to come from inside a burrow.")
    elif params.clue == "crumbs":
        world.say(f"The crumbs pointed toward a soft patch of grass near the meadow.")
    else:
        world.say(f"The bright shine winked from a bend in the riverbank trail.")

    # dialogue
    world.para()
    world.say(f'"What do you think it means?" asked {hero.id}.')
    world.say(f'"Let us look slowly," said {friend.id}. "No rushing. We can solve it together."')
    world.say(f"{hero.id} nodded and began to crawl, one careful step at a time.")
    hero.meters["crawl"] += 1
    friend.memes["helpfulness"] = friend.meme("helpfulness") + 1

    # resolution
    world.para()
    if params.clue == "marks":
        world.say(f"The crawling led them to the burrow, where a sleepy mouse had lost a seed pouch.")
        world.say(f"{hero.id} used the flint to scrape a tiny mark in the dirt, and the mouse recognized the sign.")
        world.say(f'"That is my pouch!" squeaked the mouse, and the mystery was solved.')
        hero.memes["joy"] = hero.meme("joy") + 1
    elif params.clue == "crumbs":
        world.say(f"The crawling led them to the meadow, where a bird had spilled breakfast crumbs.")
        world.say(f"{hero.id} tapped the flint against a stone and saw a little spark of idea: the crumbs were a trail.")
        world.say(f'"I dropped them while flying home," said the bird, and everyone smiled.')
        hero.memes["joy"] = hero.meme("joy") + 1
    else:
        world.say(f"The crawling led them to the riverbank, where a shiny shell had caught the sun.")
        world.say(f"{hero.id} held up the flint beside it, and the flash showed the shell was stuck in a net.")
        world.say(f'"I can free it!" said the otter, and the mystery was solved at last.')
        hero.memes["joy"] = hero.meme("joy") + 1

    world.say(f"{hero.id} and {friend.id} went home with the flint, happy and a little muddy from the crawl.")
    world.facts["solved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a gentle animal story for small children about an aardvark, a flint, and a crawl through a mystery.',
        f'Write a short story where {p.hero_name} the aardvark finds a flint, crawls after a clue, and talks with a friend.',
        f'Tell an animal story that includes dialogue and ends with a mystery solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    clue = world.facts["clue"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {p.hero_name}, an aardvark who solves a small mystery with {friend.id}.",
        ),
        QAItem(
            question=f"What important object did {p.hero_name} find?",
            answer=f"{p.hero_name} found a flint and kept it close while following the clue.",
        ),
        QAItem(
            question=f"How did {p.hero_name} move through the trail?",
            answer=f"{p.hero_name} crawled carefully through the trail to follow the clue.",
        ),
        QAItem(
            question=f"How did the mystery get solved?",
            answer=f"The mystery was solved when {p.hero_name} and {friend.id} talked about the clue and followed it to the right place.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flint?",
            answer="A flint is a hard stone that can make sparks when it strikes another stone.",
        ),
        QAItem(
            question="What does it mean to crawl?",
            answer="To crawl means to move slowly on your hands and knees or low to the ground.",
        ),
        QAItem(
            question="Why do animals ask questions in a mystery?",
            answer="Animals ask questions in a mystery so they can notice clues and figure out what happened.",
        ),
    ]


# ---------------------------------------------------------------------------
# Parsing and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: aardvark, flint, crawl, dialogue, mystery.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["fox", "rabbit", "hedgehog"])
    ap.add_argument("--clue", choices=CLUES.keys())
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS.keys()))
    clue = args.clue or rng.choice(list(CLUES.keys()))
    friend_type = args.friend_type or rng.choice(["fox", "rabbit", "hedgehog"])
    hero_name = args.hero_name or rng.choice(CHARACTER_NAMES["aardvark"])
    friend_name = args.friend_name or rng.choice(CHARACTER_NAMES[friend_type])
    params = StoryParams(
        place=place,
        hero_type="aardvark",
        friend_type=friend_type,
        tool="flint",
        clue=clue,
        hero_name=hero_name,
        friend_name=friend_name,
        seed=args.seed,
    )
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"{e.id} ({e.type}): " + ", ".join(bits))
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


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp  # lazy
    model = asp.one_model(asp_program("#show solves/2."))
    return sorted(set(asp.atoms(model, "solves")))


def python_valid() -> list[tuple]:
    return [("aardvark", clue_id) for clue_id in CLUES.keys()]


def asp_verify() -> int:
    a = set(asp_valid())
    p = set(python_valid())
    if a != p:
        print("MISMATCH between ASP and Python gates.")
        if a - p:
            print("only in ASP:", sorted(a - p))
        if p - a:
            print("only in Python:", sorted(p - a))
        return 1
    print(f"OK: ASP and Python gates match ({len(a)} possibilities).")
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="burrow", hero_type="aardvark", friend_type="fox", tool="flint", clue="marks", hero_name="Ari", friend_name="Faye"),
    StoryParams(place="meadow", hero_type="aardvark", friend_type="rabbit", tool="flint", clue="crumbs", hero_name="Milo", friend_name="Rosie"),
    StoryParams(place="riverbank", hero_type="aardvark", friend_type="hedgehog", tool="flint", clue="shine", hero_name="Pip", friend_name="Nell"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solves/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp  # lazy
        model = asp.one_model(asp_program("#show solves/2."))
        print("\n".join(f"{a[0]} -> {a[1]}" for a in sorted(set(asp.atoms(model, "solves")))))
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base + i
            i += 1
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.place}, clue={p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
