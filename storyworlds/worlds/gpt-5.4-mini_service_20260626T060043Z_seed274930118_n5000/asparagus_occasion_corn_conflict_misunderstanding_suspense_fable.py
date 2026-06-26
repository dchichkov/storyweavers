#!/usr/bin/env python3
"""
storyworlds/worlds/asparagus_occasion_corn_conflict_misunderstanding_suspense_fable.py
======================================================================================

A small fable-like story world about an occasion, asparagus, and corn, with
conflict, misunderstanding, and a suspenseful turn.

Seed-tale premise:
---
On the day of the harvest occasion, a rabbit brought asparagus to the hilltop
table and a crow guarded the corn. Each thought the other was being greedy.
The rabbit mistook the crow's watchful silence for refusal, and the crow mistook
the rabbit's hurried whisper for a plan to take everything. The friends split
apart, then the wind revealed that the corn was meant for the feast, and the
asparagus was meant as a gift for the smallest guests. They shared the food and
learned to ask before judging.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "hare"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"crow", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the hilltop table"
    occasion: str = "harvest occasion"


@dataclass
class Goods:
    id: str
    label: str
    phrase: str
    kind: str
    quantity: str
    gift_for: str
    purpose: str


@dataclass
class StoryParams:
    occasion: str
    place: str
    hero: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        other = World(self.setting)
        import copy as _copy

        other.entities = _copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "hilltop": Setting(place="the hilltop table", occasion="harvest occasion"),
    "orchard": Setting(place="the orchard bench", occasion="apple occasion"),
    "barn": Setting(place="the barn door", occasion="barn dance occasion"),
}

HEROES = {
    "rabbit": {"type": "rabbit", "label": "rabbit"},
    "crow": {"type": "crow", "label": "crow"},
    "fox": {"type": "fox", "label": "fox"},
    "mouse": {"type": "mouse", "label": "mouse"},
}

GOODS = {
    "asparagus": Goods(
        id="asparagus",
        label="asparagus",
        phrase="a bundle of asparagus",
        kind="green",
        quantity="bundle",
        gift_for="small guests",
        purpose="share",
    ),
    "corn": Goods(
        id="corn",
        label="corn",
        phrase="a basket of corn",
        kind="golden",
        quantity="basket",
        gift_for="the feast",
        purpose="serve",
    ),
}

# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id="hero", kind="character", type=params.hero, label=params.hero))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=params.helper))
    asparagus = world.add(Entity(
        id="asparagus", kind="thing", type="asparagus", label="asparagus",
        phrase="a bundle of asparagus", owner=hero.id, caretaker=helper.id
    ))
    corn = world.add(Entity(
        id="corn", kind="thing", type="corn", label="corn",
        phrase="a basket of corn", owner=helper.id, caretaker=hero.id
    ))
    world.facts.update(hero=hero, helper=helper, asparagus=asparagus, corn=corn)
    return world


def _intro(world: World) -> None:
    p = world.facts["hero"]
    q = world.facts["helper"]
    world.say(
        f"At {world.setting.place}, on the {world.setting.occasion}, a {p.type} and a {q.type} met beneath a bright sky."
    )
    world.say(
        f"The {p.type} carried {world.facts['asparagus'].phrase}, and the {q.type} guarded {world.facts['corn'].phrase}."
    )
    world.say("Both wanted the table to be ready, but each was already worried about the other.")
    world.facts["suspense"] = True


def _misunderstanding(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    asparagus = world.facts["asparagus"]
    corn = world.facts["corn"]
    world.para()
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    helper.memes["worry"] = helper.memes.get("worry", 0) + 1
    world.say(
        f"The {hero.type} saw the {helper.type} standing still by the corn and thought, "
        f'"That one is keeping all the food."'
    )
    world.say(
        f"The {helper.type} saw the {hero.type} hurrying with the asparagus and thought, "
        f'"That one is trying to take the feast away."'
    )
    world.say(
        f"So the two friends turned their backs, and the air felt tight around the {asparagus.label} and the {corn.label}."
    )
    world.facts["misunderstanding"] = True
    world.facts["conflict"] = True


def _suspense(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    world.para()
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    helper.memes["hope"] = helper.memes.get("hope", 0) + 1
    world.say("Then a gust of wind lifted a leaf high above the table.")
    world.say(
        f"Under it was a note from the elder: the corn was meant for the feast, and the asparagus was meant for the smallest guests."
    )
    world.say(
        f"The note fluttered between the {hero.type} and the {helper.type} just long enough to make them stop and listen."
    )
    world.facts["suspense"] = True
    world.facts["note_found"] = True


def _resolution(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    asparagus = world.facts["asparagus"]
    corn = world.facts["corn"]
    world.para()
    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    helper.memes["joy"] = helper.memes.get("joy", 0) + 2
    hero.memes["conflict"] = 0
    helper.memes["conflict"] = 0
    world.say(
        f"The {hero.type} and the {helper.type} laughed at their mistake."
    )
    world.say(
        f"They set the {corn.label} in the middle of the table, passed the {asparagus.label} to the small guests, and shared every bite."
    )
    world.say(
        f"By the end of the {world.setting.occasion}, the table was full, the friends were calm, and nobody had to guess what the other meant."
    )
    world.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    world = build_world(params)
    _intro(world)
    _misunderstanding(world)
    _suspense(world)
    _resolution(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["hero"].type
    q = world.facts["helper"].type
    return [
        f"Write a short fable about an {world.setting.occasion} with asparagus and corn, where a {p} and a {q} misunderstand each other before sharing.",
        "Tell a child-friendly story with suspense, conflict, and a gentle lesson about asking before judging.",
        f"Write a small fable set at {world.setting.place} in which {world.facts['asparagus'].label} and {world.facts['corn'].label} matter to the ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    aspa = world.facts["asparagus"]
    corn = world.facts["corn"]
    return [
        QAItem(
            question=f"Who carried the asparagus at the start of the story?",
            answer=f"The {hero.type} carried {aspa.phrase} to the {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did the {hero.type} and the {helper.type} have a conflict?",
            answer=f"They had a conflict because each one misunderstood the other and thought the other was being greedy with the food.",
        ),
        QAItem(
            question=f"What created the suspense before the ending?",
            answer="The suspense came from the wind lifting a note that explained what the food was really for.",
        ),
        QAItem(
            question=f"What changed after the misunderstanding was cleared up?",
            answer=f"After the note, they shared the {corn.label} and the {aspa.label} instead of guarding them from each other.",
        ),
        QAItem(
            question=f"What lesson does the fable teach?",
            answer="It teaches that asking a question is better than assuming someone means harm.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is asparagus?",
            answer="Asparagus is a green vegetable with tender stalks that people can cook and eat.",
        ),
        QAItem(
            question="What is corn?",
            answer="Corn is a golden vegetable with kernels on a cob, and people often serve it at meals and feasts.",
        ),
        QAItem(
            question="What is an occasion?",
            answer="An occasion is a special event or reason for people to gather, celebrate, or share something together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/3.

conflict(A,B) :- hero(A), helper(B), misunderstanding(A,B).
misunderstanding(A,B) :- sees_greedy(A,B); sees_greedy(B,A).
suspense(P) :- note_floats(P).
resolved(P) :- suspense(P), shared_food(P).

valid_story(Place, Hero, Helper) :- setting(Place), character(Hero), character(Helper), Hero != Helper,
                                     has_asparagus(Hero), has_corn(Helper).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
        lines.append(asp.fact("occasion", sid, s.occasion))
    for hid, info in HEROES.items():
        lines.append(asp.fact("character", hid))
        lines.append(asp.fact("hero", hid))
        if info["type"] == "crow":
            lines.append(asp.fact("helper", hid))
    lines.append(asp.fact("has_asparagus", "rabbit"))
    lines.append(asp.fact("has_corn", "crow"))
    lines.append(asp.fact("sees_greedy", "rabbit", "crow"))
    lines.append(asp.fact("sees_greedy", "crow", "rabbit"))
    lines.append(asp.fact("note_floats", "harvest"))
    lines.append(asp.fact("shared_food", "harvest"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(p, "rabbit", "crow") for p in SETTINGS}
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: ASP matches Python ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python:", sorted(python_set - clingo_set))
    print("asp:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable world: asparagus, corn, occasion, conflict, misunderstanding, suspense.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--occasion", choices=["harvest occasion", "apple occasion", "barn dance occasion"])
    ap.add_argument("--hero", choices=sorted(HEROES))
    ap.add_argument("--helper", choices=sorted(HEROES))
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
    places = [args.place] if args.place else list(SETTINGS)
    if args.occasion:
        places = [k for k, s in SETTINGS.items() if s.occasion == args.occasion]
    if not places:
        raise StoryError("No story matches the requested occasion/place.")
    place = rng.choice(sorted(places))
    hero = args.hero or "rabbit"
    helper = args.helper or "crow"
    if hero == helper:
        raise StoryError("Hero and helper must be different characters.")
    return StoryParams(occasion=SETTINGS[place].occasion, place=place, hero=hero, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"facts={sorted(world.facts.keys())}")
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


CURATED = [
    StoryParams(occasion="harvest occasion", place="hilltop", hero="rabbit", helper="crow"),
    StoryParams(occasion="apple occasion", place="orchard", hero="fox", helper="mouse"),
    StoryParams(occasion="barn dance occasion", place="barn", hero="crow", helper="rabbit"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for place, hero, helper in stories:
            print(f"  {place} {hero} {helper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.occasion} @ {p.place}: {p.hero} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
