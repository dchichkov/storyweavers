#!/usr/bin/env python3
"""
A small myth-style storyworld with rhyme, repetition, and a happy ending.

Premise:
A tiny village wants a bit of pizzazz for the midsummer feast. A clever child
and a proud helper try to bring wonder to the people, but the first plan is too
showy and causes a wobble. They learn to trade flash for warmth, and the feast
ends in song.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    goal: str
    flair: str
    seed: Optional[int] = None


@dataclass
class Goal:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


PLACES = {
    "hill": "the moonlit hill",
    "river": "the silver river",
    "grove": "the old grove",
    "village": "the little village",
}

GOALS = {
    "torch": Goal(
        id="torch",
        verb="raise the torch",
        gerund="raising the torch",
        rush="dash to the torchstone",
        mess="spark",
        soil="scorched",
        zone={"hands"},
        keyword="torch",
        tags={"light", "fire"},
    ),
    "banner": Goal(
        id="banner",
        verb="unfurl the banner",
        gerund="unfurling the banner",
        rush="run with the banner pole",
        mess="wind",
        soil="tattered",
        zone={"arms"},
        keyword="banner",
        tags={"cloth", "wind"},
    ),
    "harp": Goal(
        id="harp",
        verb="play the harp",
        gerund="playing the harp",
        rush="hurry to the harp seat",
        mess="tune",
        soil="out of tune",
        zone={"hands"},
        keyword="harp",
        tags={"music", "string"},
    ),
}

CHARMS = [
    Charm(
        id="gloves",
        label="silver gloves",
        phrase="silver gloves",
        covers={"hands"},
        guards={"spark", "tune"},
        prep="put on silver gloves first",
        tail="walked back with the silver gloves on",
    ),
    Charm(
        id="cloak",
        label="a sky-blue cloak",
        phrase="a sky-blue cloak",
        covers={"arms"},
        guards={"wind", "spark"},
        prep="wrap a sky-blue cloak around the shoulders",
        tail="returned with the sky-blue cloak fluttering",
    ),
    Charm(
        id="softwrap",
        label="a soft wrap",
        phrase="a soft wrap",
        covers={"hands", "arms"},
        guards={"spark", "wind", "tune"},
        prep="choose a soft wrap for both hands and arms",
        tail="came back with the soft wrap tied neat",
    ),
]

HERO_NAMES = ["Mira", "Taro", "Nia", "Eren", "Sana", "Oren"]
HELPER_NAMES = ["Aunt Lysa", "Old Bram", "Mother Reed", "Father Ash"]

TRAITS = ["bold", "bright", "gentle", "restless", "cheery"]

# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------


def rhyme_line(a: str, b: str) -> str:
    return f"{a}, then {b}."


def predict_mess(world: World, hero: Entity, goal: Goal) -> dict:
    sim = world.copy()
    _do_goal(sim, hero.id, goal, narrate=False)
    return {
        "soiled": any(e.meters.get(goal.mess, 0) >= THRESHOLD for e in sim.entities.values()),
        "tension": sum(e.memes.get("worry", 0) for e in sim.entities.values()),
    }


def choose_charm(goal: Goal) -> Optional[Charm]:
    for charm in CHARMS:
        if goal.mess in charm.guards and goal.zone.issubset(charm.covers):
            return charm
    return None


def _do_goal(world: World, hero_id: str, goal: Goal, narrate: bool = True) -> None:
    hero = world.get(hero_id)
    hero.meters[goal.mess] = hero.meters.get(goal.mess, 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    if narrate:
        world.say(rhyme_line(f"{hero.id} reached for {goal.verb}", f"the day began to sing"))


def tell(params: StoryParams) -> World:
    world = World(params.place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, traits=[params.flair, "curious"]))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, traits=["wise", "patient"]))
    goal = GOALS[params.goal]

    world.facts.update(hero=hero, helper=helper, goal=goal, place=params.place)

    # Act I: mythic setup
    world.say(
        f"In {params.place}, under a wide old sky, {hero.id} was known for {params.flair} steps "
        f"and a heart that wanted a little pizzazz."
    )
    world.say(
        f"Each year the people called for a feast, and each feast called for a wonder; "
        f"{hero.id} longed to {goal.verb} before the stars grew bright."
    )
    world.say(
        f"{helper.id} smiled and said, {hero.id} would do well, for every brave deed begins with a wish."
    )

    # Act II: trouble and warning
    world.para()
    world.say(
        f"At the edge of {params.place}, {hero.id} went to {goal.verb}, and the first try was too eager."
    )
    pred = predict_mess(world, hero, goal)
    if pred["soiled"]:
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        helper.memes["worry"] = helper.memes.get("worry", 0) + 1
        world.say(
            f"{helper.id} said, 'Easy, easy. If you rush the {goal.keyword}, it will come to harm.'"
        )
        world.say(
            f"{hero.id} did not stop at once; {hero.id} tried to {goal.rush}, and the air grew sharp."
        )
        world.say(
            f"The sign was plain: the old way would leave the {goal.keyword} {goal.soil}."
        )

    # Act III: the wise fix
    world.para()
    charm = choose_charm(goal)
    if charm is None:
        raise StoryError("No reasonable charm can protect the hero for this goal.")
    world.say(
        f"Then {helper.id} brought {charm.label} and whispered, 'Small hands, safe hands, steady hands.'"
    )
    world.say(
        f"{hero.id} listened, and listened again, and chose to {charm.prep}."
    )
    world.say(
        f"At last {hero.id} could {goal.verb}, and the charm kept the harm away."
    )
    world.say(
        f"So the feast shone on: the {goal.keyword} rose, the people cheered, and the night kept its promise."
    )
    world.say(
        f"{hero.id} smiled, {helper.id} laughed, and the village had its pizzazz at last."
    )

    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1
    world.facts["resolved"] = True
    world.facts["charm"] = charm
    return world


# ---------------------------------------------------------------------------
# Registries and ASP twin
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for goal_id, goal in GOALS.items():
            if choose_charm(goal) is not None:
                combos.append((place, goal_id, goal.keyword))
    return combos


ASP_RULES = r"""
goal_risky(G) :- goal(G), zone(G,Z), charm(C), covers(C,Z).
has_fix(G) :- goal_risky(G), charm(C), zone(G,Z), covers(C,Z), guards(C,M), mess(G,M).
valid(P,G) :- place(P), goal(G), has_fix(G).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for gid, goal in GOALS.items():
        lines.append(asp.fact("goal", gid))
        lines.append(asp.fact("mess", gid, goal.mess))
        lines.append(asp.fact("zone", gid, ",".join(sorted(goal.zone))))
    for charm in CHARMS:
        lines.append(asp.fact("charm", charm.id))
        for z in sorted(charm.covers):
            lines.append(asp.fact("covers", charm.id, z))
        for g in sorted(charm.guards):
            lines.append(asp.fact("guards", charm.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    clingo_set = set(asp.atoms(model, "valid"))
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH:")
    print(" only in clingo:", sorted(clingo_set - py_set))
    print(" only in python:", sorted(py_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, goal = f["hero"], f["helper"], f["goal"]
    return [
        f'Write a short myth for a child named {hero.id} who wants to {goal.verb} with a little pizzazz.',
        f"Tell a rhyme-filled happy-ending story where {helper.id} helps {hero.id} solve a problem with {goal.keyword}.",
        f"Write a gentle myth about {hero.id}, {helper.id}, and a small {goal.keyword} ceremony.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, goal = f["hero"], f["helper"], f["goal"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in the story?",
            answer=f"{hero.id} wanted to {goal.verb}, and wanted to do it with a bit of pizzazz.",
        ),
        QAItem(
            question=f"Who helped {hero.id} when the first plan looked risky?",
            answer=f"{helper.id} helped {hero.id} and brought a safer charm for the job.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"At the end, {hero.id} succeeded, the people celebrated, and the story ended happily.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is pizzazz?",
            answer="Pizzazz means a lively, showy kind of sparkle or charm that makes something feel exciting.",
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is an old story that often tells about brave people, special places, and big ideas in a memorable way.",
        ),
        QAItem(
            question="Why do people use a charm in a story like this?",
            answer="People use a charm to help keep something safe or to make a task easier in a magical or special way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld with rhyme, repetition, and a happy ending.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--goal", choices=sorted(GOALS))
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.goal:
        combos = [c for c in combos if c[1] == args.goal]
    if not combos:
        raise StoryError("No valid combination matches the given options.")

    place, goal_id, _ = rng.choice(sorted(combos))
    hero_type = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    helper_type = "woman" if "Aunt" in helper_name or "Mother" in helper_name else "man"
    flair = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        goal=goal_id,
        flair=flair,
    )


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid/2."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible stories:")
        for v in vals:
            print(" ", v)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="village", hero_name="Mira", hero_type="girl", helper_name="Aunt Lysa", helper_type="woman", goal="torch", flair="bright"),
            StoryParams(place="grove", hero_name="Taro", hero_type="boy", helper_name="Old Bram", helper_type="man", goal="banner", flair="bold"),
            StoryParams(place="hill", hero_name="Nia", hero_type="girl", helper_name="Mother Reed", helper_type="woman", goal="harp", flair="gentle"),
        ]
        samples = [generate(p) for p in curated]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.goal} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
