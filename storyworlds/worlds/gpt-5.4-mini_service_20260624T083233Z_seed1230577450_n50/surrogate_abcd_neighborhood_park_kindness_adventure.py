#!/usr/bin/env python3
"""
A small storyworld set in a neighborhood park, with an adventure flavored by
kindness, a surrogate helper, and the seed words "surrogate" and "abcd".
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"dust": 0.0, "lost": 0.0, "found": 0.0}
        if not self.memes:
            self.memes = {"kindness": 0.0, "worry": 0.0, "relief": 0.0, "bravery": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the neighborhood park"
    affords: set[str] = field(default_factory=lambda: {"search", "share", "help"})


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    obstacle: str
    rescue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    label: str
    phrase: str
    type: str = "thing"
    plural: bool = False
    region: str = "hands"
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    quest: str
    relic: str
    name: str
    gender: str
    surrogate_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


SETTINGS = {
    "neighborhood_park": Setting(place="the neighborhood park"),
}

QUESTS = {
    "abcd": Quest(
        id="abcd",
        verb="follow the little trail of letters",
        gerund="following the little trail of letters",
        rush="dash after the letters",
        obstacle="the letters kept slipping behind the maple trees",
        rescue="trace the path together until the letters were found",
        tags={"abcd", "letters", "adventure"},
    ),
    "surrogate": Quest(
        id="surrogate",
        verb="help the shy new kid find the right bench",
        gerund="helping the shy new kid",
        rush="hurry across the path to help",
        obstacle="the new kid was too nervous to ask anyone",
        rescue="walk beside the new kid and speak kindly",
        tags={"surrogate", "kindness", "help"},
    ),
}

RELICS = {
    "ribbon_map": Relic(
        label="a ribbon map",
        phrase="a bright ribbon map",
        tags={"map", "adventure"},
    ),
    "lost_note": Relic(
        label="a lost note",
        phrase="a small lost note with the letters abcd on it",
        tags={"abcd", "letters"},
    ),
    "blue_ball": Relic(
        label="a blue ball",
        phrase="a blue ball left near the slide",
        tags={"kindness", "help"},
    ),
}

NAMES_BOY = ["Milo", "Evan", "Noah", "Theo", "Finn"]
NAMES_GIRL = ["Maya", "Ivy", "Nora", "Luna", "Zoe"]


ASP_RULES = r"""
quest(Quest) :- quest_tag(Quest,_).
relic(Relic) :- relic_tag(Relic,_).
compatible(Quest, Relic) :- quest_tag(Quest, T), relic_tag(Relic, T).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "neighborhood_park")]
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest_tag", qid, qid))
        for t in sorted(q.tags):
            lines.append(asp.fact("quest_tag", qid, t))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic_tag", rid, rid))
        for t in sorted(r.tags):
            lines.append(asp.fact("relic_tag", rid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatible() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_compatible())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print(" python-only:", sorted(py - cl))
    print(" clingo-only:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for qid in QUESTS:
        for rid in RELICS:
            if QUESTS[qid].tags & RELICS[rid].tags:
                combos.append((qid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A neighborhood-park kindness adventure storyworld.")
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--surrogate-name")
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
    if args.quest and args.relic and (args.quest, args.relic) not in combos:
        raise StoryError("That quest and relic do not fit together in this park adventure.")
    picks = [c for c in combos if (not args.quest or c[0] == args.quest) and (not args.relic or c[1] == args.relic)]
    if not picks:
        raise StoryError("No valid combination matches the given options.")
    quest, relic = rng.choice(sorted(picks))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    surrogate_name = args.surrogate_name or rng.choice(["Aunt Jo", "Mr. Ray", "Ms. Kim", "Nina"])
    return StoryParams(quest=quest, relic=relic, name=name, gender=gender, surrogate_name=surrogate_name)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS["neighborhood_park"])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    surrogate = world.add(Entity(id="surrogate", kind="character", type="adult", label=params.surrogate_name))
    quest = QUESTS[params.quest]
    relic = RELICS[params.relic]

    world.say(f"{hero.id} was a brave little {hero.type} who loved an adventure in {world.setting.place}.")
    world.say(f"One morning, {hero.id} noticed {relic.phrase} near the path, and {hero.pronoun('possessive')} heart jumped.")
    world.say(f"At the same time, {params.surrogate_name} was there as a surrogate helper, ready to guide {hero.pronoun('object')} with kindness.")

    hero.memes["bravery"] += 1
    hero.memes["worry"] += 1
    world.facts.update(hero=hero, surrogate=surrogate, quest=quest, relic=relic, params=params)

    world.say(f"{hero.id} wanted to {quest.verb}, but {quest.obstacle}.")
    world.say(f"{params.surrogate_name} smiled and said that kindness could lead the way.")

    if params.quest == "abcd":
        world.say(f"So {hero.id} and {params.surrogate_name} set off to follow the letters abcd, step by step, past the swings and the bench.")
        world.say(f"They found the lost note, and {hero.id} carried it carefully back to the little bulletin board.")
        hero.memes["relief"] += 1
        hero.memes["kindness"] += 1
        world.say(f"That made {hero.id} feel proud, because a small kindness can be a big adventure.")
    else:
        world.say(f"They walked together until {quest.rescue}.")
        hero.memes["kindness"] += 1
        hero.memes["relief"] += 1
        world.say(f"In the end, {hero.id} shared the last step of the journey with a gentle smile.")

    world.say(f"By sunset, {hero.id} was still in {world.setting.place}, but now {hero.pronoun('subject')} knew how much kindness could help a whole day.")
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    q = world.facts["quest"]
    r = world.facts["relic"]
    return [
        f'Write a short adventure story for a child in a neighborhood park, using the word "{q.id}".',
        f"Tell a gentle story where {p.name} and {p.surrogate_name} solve a small park problem with kindness.",
        f'Write a simple story that includes the word "{r.label}" and ends with a helpful choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    q = world.facts["quest"]
    r = world.facts["relic"]
    return [
        QAItem(
            question=f"Who went on the adventure in the neighborhood park?",
            answer=f"{p.name} went on the adventure with {p.surrogate_name}, who acted as a surrogate helper.",
        ),
        QAItem(
            question=f"What did {p.name} want to do first?",
            answer=f"{p.name} wanted to {q.verb}.",
        ),
        QAItem(
            question=f"What was special about the lost item in the story?",
            answer=f"It was {r.phrase}, and the letters abcd were part of the clue that guided the adventure.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {p.name} choosing kindness, helping solve the problem, and feeling proud at the neighborhood park.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(question="What is kindness?", answer="Kindness is when someone helps, shares, or speaks gently to make things better."),
        QAItem(question="What is a surrogate?", answer="A surrogate is someone who stands in to help, guide, or support when a little extra help is needed."),
        QAItem(question="What does adventure mean?", answer="Adventure means going on a lively journey where something interesting or challenging happens."),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== story qa ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


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
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_compatible()
        print(f"{len(combos)} compatible quest/relic combos:\n")
        for q, r in combos:
            print(f"  {q:10} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(quest="abcd", relic="lost_note", name="Maya", gender="girl", surrogate_name="Aunt Jo"),
            StoryParams(quest="surrogate", relic="blue_ball", name="Noah", gender="boy", surrogate_name="Mr. Ray"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
