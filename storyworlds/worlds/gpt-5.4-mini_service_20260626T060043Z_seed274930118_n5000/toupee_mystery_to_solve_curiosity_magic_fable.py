#!/usr/bin/env python3
"""
Storyworld: toupee mystery with curiosity and a small magic-fable arc.

A child-facing fable domain:
- A curious animal notices a strange toupee.
- A little mystery must be solved.
- Magic helps reveal the truth, but only after careful looking and asking.
- The ending should feel like a fable: a gentle lesson about curiosity and honesty.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    secret: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "rabbit", "mouse", "cat", "bird"}:
            # Use "it" for fable animals to keep the tone simple and universal.
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    magic_kind: str = "glow"


@dataclass
class Mystery:
    id: str
    clue: str
    hidden_by: str
    revealed_by: str
    solved_by: str
    lesson: str


@dataclass
class MagicTool:
    id: str
    label: str
    effect: str
    glow_word: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "orchard": Place(id="orchard", label="the orchard", indoors=False, magic_kind="golden"),
    "brook": Place(id="brook", label="the brook", indoors=False, magic_kind="sparkling"),
    "grove": Place(id="grove", label="the grove", indoors=False, magic_kind="silver"),
    "cottage": Place(id="cottage", label="the cottage", indoors=True, magic_kind="warm"),
}

CHAR_TYPES = {
    "fox": {"name": "fox"},
    "rabbit": {"name": "rabbit"},
    "mouse": {"name": "mouse"},
    "cat": {"name": "cat"},
    "bird": {"name": "bird"},
}

MYSTERIES = {
    "toupee_lost": Mystery(
        id="toupee_lost",
        clue="a small brown toupee with a bright ribbon",
        hidden_by="a thorny branch",
        revealed_by="a spell of kind light",
        solved_by="a careful question",
        lesson="Looking closely can be kinder than guessing quickly.",
    ),
    "toupee_wind": Mystery(
        id="toupee_wind",
        clue="a fluffy toupee that smelled like apples",
        hidden_by="the wind in the grass",
        revealed_by="a mirror of moonlight",
        solved_by="a patient search",
        lesson="Curiosity works best when it is gentle and patient.",
    ),
    "toupee_misplaced": Mystery(
        id="toupee_misplaced",
        clue="a tiny toupee tied with blue thread",
        hidden_by="a basket of leaves",
        revealed_by="a tiny glowing moth",
        solved_by="a truthful memory",
        lesson="Truth shines brighter when someone is brave enough to tell it.",
    ),
}

MAGIC = {
    "glow": MagicTool(id="glow", label="a glow stone", effect="shined on hidden things", glow_word="glow"),
    "mirror": MagicTool(id="mirror", label="a mirror charm", effect="showed what was nearby", glow_word="shine"),
    "moth": MagicTool(id="moth", label="a moon moth lantern", effect="led the eye to a secret", glow_word="twinkle"),
}

GENTLE_NAMES = ["Ari", "Bea", "Cleo", "Drew", "Eli", "Fern", "Gus", "Hope"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_type: str
    name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def place_line(place: Place) -> str:
    return {
        "orchard": "The orchard was soft with grass, and the apple trees whispered in the breeze.",
        "brook": "The brook sang over the stones, and little ripples blinked in the sun.",
        "grove": "The grove stood quiet and green, with shadows like folded blankets.",
        "cottage": "The cottage was warm and tidy, with a window that caught the afternoon light.",
    }[place.id]


def mystery_answer(m: Mystery) -> str:
    return f"It was {m.clue}."


def select_magic(place: Place, mystery: Mystery) -> MagicTool:
    if place.magic_kind == "golden":
        return MAGIC["glow"]
    if place.magic_kind == "sparkling":
        return MAGIC["mirror"]
    return MAGIC["moth"]


def build_story_seed_hint() -> str:
    return "toupee"


def hero_pronoun(name: str) -> str:
    return "it"


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def solve_with_magic(world: World, hero: Entity, mystery: Mystery, tool: MagicTool) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    world.say(
        f"{hero.id} felt curious when it spotted {mystery.clue} near {world.place.label}."
    )
    world.say(
        f"It asked, “What could this strange little thing be?” and picked up {tool.label}."
    )
    if mystery.id == "toupee_lost":
        world.say(
            f"The {tool.effect}, and soon the answer came clear: the toupee had been hidden by {mystery.hidden_by}."
        )
    elif mystery.id == "toupee_wind":
        world.say(
            f"The {tool.effect}, and a soft clue appeared in the grass. The toupee had drifted under {mystery.hidden_by}."
        )
    else:
        world.say(
            f"The {tool.effect}, and the secret came out at once. The toupee had been tucked away by mistake behind {mystery.hidden_by}."
        )
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1.0
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    world.say(
        f"{hero.id} used {mystery.solved_by}, and the mystery was solved without any fuss."
    )


def tell_story(params: StoryParams) -> World:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    tool = select_magic(place, mystery)

    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type=params.hero_type))
    world.facts.update(hero=hero, place=place, mystery=mystery, tool=tool)

    world.say(
        f"Once in {place.label}, there lived a curious {params.hero_type} named {params.name}."
    )
    world.say(
        f"{params.name} loved to notice small things, especially when a mystery was hiding in plain sight."
    )

    world.para()
    world.say(place_line(place))
    world.say(f"One day, {params.name} found {mystery.clue}.")
    world.say(f"It looked important, but nobody could say why.")

    world.para()
    solve_with_magic(world, hero, mystery, tool)

    world.para()
    world.say(
        f"In the end, {params.name} returned the toupee to its owner and learned that gentle curiosity can bring a happy answer."
    )
    world.say(f"The lesson was simple: {mystery.lesson}")

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short fable for a child about a curious {f['hero'].type} who finds a toupee mystery in {f['place'].label}.",
        f"Tell a gentle story where magic helps solve a tiny mystery about {f['mystery'].clue}.",
        f"Write a simple fable about curiosity, a missing toupee, and a kind ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    place: Place = f["place"]
    mystery: Mystery = f["mystery"]
    tool: MagicTool = f["tool"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a curious {hero.type} in {place.label}.",
        ),
        QAItem(
            question=f"What strange thing did {hero.id} find?",
            answer=f"{hero.id} found {mystery.clue}, and it turned out to be a toupee mystery to solve.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"{tool.label} helped by using its magic to reveal what was hidden, and {mystery.solved_by} finished the search.",
        ),
        QAItem(
            question=f"What did {hero.id} learn?",
            answer=mystery.lesson,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    place: Place = f["place"]
    mystery: Mystery = f["mystery"]
    tool: MagicTool = f["tool"]
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to know more, to look carefully, and to ask questions about something unknown.",
        ),
        QAItem(
            question="What does magic do in stories?",
            answer="Magic can reveal hidden things, help characters understand a problem, or make an ordinary moment feel special.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not understood right away, so someone has to look for clues and solve it.",
        ),
        QAItem(
            question="What kind of place is this story set in?",
            answer=f"The story happens in {place.label}, a place that can hold quiet clues and a little wonder.",
        ),
        QAItem(
            question="Why is a toupee a clue in this story?",
            answer=f"The toupee is the mysterious object that starts the search, so it gives the characters something to notice and solve.",
        ),
        QAItem(
            question="What kind of magical thing helped here?",
            answer=f"{tool.label} helped by {tool.effect}, which made the hidden clue easier to find.",
        ),
        QAItem(
            question="What is the lesson of this fable?",
            answer=mystery.lesson,
        ),
    ]


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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id:10} ({ent.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/4.
place(orchard). place(brook). place(grove). place(cottage).
hero_type(fox). hero_type(rabbit). hero_type(mouse). hero_type(cat). hero_type(bird).
mystery(toupee_lost). mystery(toupee_wind). mystery(toupee_misplaced).
tool(glow). tool(mirror). tool(moth).

valid_story(P, M, T, H) :- place(P), mystery(M), tool(T), hero_type(H).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for hid in CHAR_TYPES:
        lines.append(asp.fact("hero_type", hid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for tid in MAGIC:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, m, t, h) for p in PLACES for m in MYSTERIES for t in MAGIC for h in CHAR_TYPES}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python registry space ({len(cl)} stories).")
        return 0
    print("MISMATCH between clingo and Python registry space:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about a toupee mystery and gentle magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero-type", choices=CHAR_TYPES)
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(PLACES))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    hero_type = args.hero_type or rng.choice(list(CHAR_TYPES))
    name = args.name or rng.choice(GENTLE_NAMES)
    return StoryParams(place=place, mystery=mystery, hero_type=hero_type, name=name)


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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for p, m, t, h in stories[:50]:
            print(f"  {p:8} {m:18} {t:8} {h}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in PLACES:
            for m in MYSTERIES:
                for h in CHAR_TYPES:
                    params = StoryParams(place=p, mystery=m, hero_type=h, name=GENTLE_NAMES[(hash((p, m, h)) % len(GENTLE_NAMES))])
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 25):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mystery} at {p.place} ({p.hero_type})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
