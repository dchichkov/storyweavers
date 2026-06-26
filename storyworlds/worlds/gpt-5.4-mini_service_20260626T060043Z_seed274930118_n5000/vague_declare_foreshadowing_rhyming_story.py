#!/usr/bin/env python3
"""
storyworlds/worlds/vague_declare_foreshadowing_rhyming_story.py
===============================================================

A tiny rhyming story world with foreshadowing, built from the seed words
"vague" and "declare".

Seed tale idea:
---
On a dim evening, a child named Mira found a vague note in the garden.
It said a little star-shaped kite might be near the old pond, but the note
did not declare exactly where. The wind kept teasing the grass, and Mira
felt unsure.

Her grandmother noticed the cloudy sky and the bending reeds. She declared
that the wind was planning trouble, so Mira should take a lantern and a spool
of string. Together they followed the faint clues, and the lantern glow made
the path clear. In the end, Mira found the kite caught in a berry bush and
laughed at how the vague note had foreshadowed the windy search.

World model:
---
A small, state-driven rhyming tale about a child, a vague clue, a foreshadowed
problem, and a clear finishing image proving what changed.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"lost": 0.0, "windy": 0.0, "found": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "joy": 0.0, "foreshadow": 0.0, "certainty": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the garden"


@dataclass
class Quest:
    id: str
    object_label: str
    object_phrase: str
    search_zone: str
    clue: str
    ending_image: str
    rhymes: tuple[str, str, str]


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, line: str) -> None:
        if line:
            self.lines.append(line)

    def render(self) -> str:
        return "\n".join(self.lines)


SETTINGS = {
    "garden": Setting("the garden"),
    "pond": Setting("the old pond"),
    "lane": Setting("the windy lane"),
}

QUESTS = {
    "kite": Quest(
        id="kite",
        object_label="kite",
        object_phrase="a star-shaped kite",
        search_zone="bush",
        clue="vague",
        ending_image="the kite snagged in a berry bush",
        rhymes=("glow", "show", "slow"),
    ),
    "shell": Quest(
        id="shell",
        object_label="shell",
        object_phrase="a shiny shell",
        search_zone="reeds",
        clue="vague",
        ending_image="the shell tucked in the reeds",
        rhymes=("gleam", "dream", "stream"),
    ),
    "bell": Quest(
        id="bell",
        object_label="bell",
        object_phrase="a little silver bell",
        search_zone="hedge",
        clue="vague",
        ending_image="the bell resting in the hedge",
        rhymes=("ring", "thing", "spring"),
    ),
}

GEAR = {
    "lantern": Gear("lantern", "a lantern", {"dark"}, "take a lantern for the walk", "The lantern made the path bright and light."),
    "string": Gear("string", "a spool of string", {"windy"}, "bring a spool of string too", "The string kept the treasure from flying away."),
}

GIRL_NAMES = ["Mira", "Luna", "Nina", "Eve", "Mina"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Jude", "Noah"]
TRAITS = ["curious", "gentle", "brave", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


ASP_RULES = r"""
quest_risk(Q) :- clue(Q, vague), search_zone(Q, Z), windy(Z).
need_gear(Q, lantern) :- quest_risk(Q).
need_gear(Q, string) :- quest_risk(Q).
valid_story(P, Q, G) :- setting(P), quest(Q), need_gear(Q, G).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("clue", qid, q.clue))
        lines.append(asp.fact("search_zone", qid, q.search_zone))
    for gid in GEAR:
        lines.append(asp.fact("gear", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in SETTINGS:
        for q in QUESTS:
            combos.append((p, q, "lantern"))
            combos.append((p, q, "string"))
    return sorted(set(combos))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world with vague clues and foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)]
    if not combos:
        raise StoryError("No valid story matches the requested options.")
    place, quest, _ = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, name=name, gender=gender, elder=elder, trait=trait)


def predict(world: World, hero: Entity, quest: Quest) -> dict:
    risky = hero.memes["worry"] + hero.memes["foreshadow"] >= THRESHOLD
    return {"risky": risky, "ending": quest.ending_image}


def tell(setting: Setting, quest: Quest, name: str, gender: str, elder: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, memes={"worry": 0.0, "joy": 0.0, "foreshadow": 0.0, "certainty": 0.0}))
    elder_ent = world.add(Entity(id="elder", kind="character", type=elder))
    clue = world.add(Entity(id="clue", label="note", phrase=f"a {quest.clue} note", owner=elder_ent.id))
    prize = world.add(Entity(id=quest.id, label=quest.object_label, phrase=quest.object_phrase, owner=hero.id))
    lantern = world.add(Entity(id="lantern", label="lantern", phrase="a lantern", owner=hero.id, protective=True, covers={"dark"}))
    string = world.add(Entity(id="string", label="string", phrase="a spool of string", owner=hero.id))

    world.say(f"In {setting.place}, little {trait} {name} went strolling by the light.")
    world.say(f"{hero.pronoun().capitalize()} found {clue.phrase}, but it was vague, not bright.")
    world.say(f"It did not declare just where to seek; it only hinted at sight.")

    hero.memes["foreshadow"] += 1
    hero.memes["worry"] += 1
    world.say(f"The reeds bent low, and the wind blew slow; that was a clue in disguise.")
    world.say(f"{hero.pronoun().capitalize()} felt a small tug in the heart, as if clouds were writing the skies.")

    world.say("")
    world.say(f"{elder_ent.pronoun().capitalize()} saw the dark and the swaying bark, and chose a careful way.")
    world.say(f'{elder_ent.pronoun().capitalize()} would declare, "Take {lantern.label} and {string.label}; the night is not the day."')
    world.say(f"So {name} agreed and held the gear; the path grew less unclear.")

    hero.meters["windy"] += 1
    hero.memes["certainty"] += 1
    world.say(f"With lantern glow and string in tow, {name} walked on with cheer.")
    if predict(world, hero, quest)["risky"]:
        world.say(f"The foreshadowing felt true at last; the search was now sincere.")

    world.say(f"At the end, there was {quest.ending_image}, and {name} gave a joyful grin.")
    world.say(f"{hero.pronoun().capitalize()} declared, 'The vague old note was right all along; the treasure was tucked right in!'")
    world.say(f"The night grew mild, the child looked smiled, and home came near and sweet.")
    world.say(f"With lantern lit and heart made glad, {name} danced on dancing feet.")

    world.facts.update(
        hero=hero,
        elder=elder_ent,
        clue=clue,
        prize=prize,
        lantern=lantern,
        string=string,
        quest=quest,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, elder, quest = f["hero"], f["elder"], f["quest"]
    return [
        f'Write a rhyming story for a young child that includes the word "vague" and the word "declare".',
        f"Tell a gentle foreshadowing story where {hero.id} finds a vague clue and {elder.pronoun().capitalize()} helps",
        f"Write a short rhyming tale in {world.setting.place} about searching for {quest.object_phrase} by lantern light.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, quest = f["hero"], f["elder"], f["quest"]
    return [
        QAItem(
            question=f"What did {hero.id} find in {world.setting.place} at the start?",
            answer=f"{hero.id} found a vague note that hinted at {quest.object_phrase}.",
        ),
        QAItem(
            question=f"Why did {elder.pronoun().capitalize()} tell {hero.id} to take the lantern?",
            answer=f"{elder.pronoun().capitalize()} could tell the night was getting dark and the wind was making the search tricky, so the lantern would help make the path clear.",
        ),
        QAItem(
            question=f"What was found in the end?",
            answer=f"In the end, {quest.ending_image} was found, and the child went home happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does vague mean?",
            answer="Vague means not clear enough to say exactly what something is or where it is.",
        ),
        QAItem(
            question="What does declare mean?",
            answer="Declare means to say something clearly and strongly, so other people can hear your decision or message.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives small hints early on about something important that will happen later.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        if e.covers:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set((p, q, "lantern") for p, q, _ in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    print("clingo only:", sorted(clingo_set - python_set))
    print("python only:", sorted(python_set - clingo_set))
    return 1


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


CURATED = [
    StoryParams(place="garden", quest="kite", name="Mira", gender="girl", elder="grandmother", trait="curious"),
    StoryParams(place="pond", quest="shell", name="Theo", gender="boy", elder="grandfather", trait="thoughtful"),
    StoryParams(place="lane", quest="bell", name="Luna", gender="girl", elder="grandmother", trait="brave"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUESTS[params.quest], params.name, params.gender, params.elder, params.trait)
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
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for p, q, g in stories:
            print(f"  {p:8} {q:8} {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
            header = f"### {p.name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
