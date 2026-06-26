#!/usr/bin/env python3
"""
storyworlds/worlds/humongous_zoo_sound_effects_quest_space_adventure.py
======================================================================

A small zoo storyworld with a space-adventure feel, built around a quest and
sound effects. The world model tracks a child, a guide, a humongous zoo friend,
and a quest item that must be delivered or found by following noisy clues.

The stories are intentionally compact and state-driven:
- setup: the child arrives at the zoo and hears a space-like quest
- tension: a clue goes missing or the path feels tricky
- turn: sound effects reveal the trail
- resolution: the quest finishes with a bright ending image

The world is small on purpose so that every variant stays plausible and
grounded in a clear causal chain.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the zoo"
    zones: list[str] = field(default_factory=lambda: ["gate", "paths", "reptile house", "bird tower", "space dome"])


@dataclass
class Quest:
    id: str
    mission: str
    clue: str
    sound: str
    turn_sound: str
    finish: str
    risk: str
    target_zone: str
    keyword: str = "quest"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    zone: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
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


GIRL_NAMES = ["Mia", "Luna", "Zoe", "Ava", "Nora", "Ivy", "Lily"]
BOY_NAMES = ["Max", "Leo", "Theo", "Finn", "Ben", "Sam", "Jude"]
TRAITS = ["curious", "brave", "cheerful", "spirited", "careful"]


SETTINGS = {"zoo": Setting()}
PRIZES = {
    "star_map": Prize(label="star map", phrase="a silver star map", type="map", zone="space dome"),
    "comet_ticket": Prize(label="comet ticket", phrase="a shiny comet ticket", type="ticket", zone="bird tower"),
    "moon_key": Prize(label="moon key", phrase="a little moon key", type="key", zone="reptile house"),
}
QUESTS = {
    "find_map": Quest(
        id="find_map",
        mission="find the missing star map",
        clue="The map was last seen near the humming gate.",
        sound="whirr-whirr",
        turn_sound="click-click",
        finish="the star map glinted under a bench",
        risk="the child might wander the wrong way",
        target_zone="space dome",
        keyword="quest",
        tags={"space", "map", "sound"},
    ),
    "deliver_ticket": Quest(
        id="deliver_ticket",
        mission="deliver the comet ticket to the bird tower keeper",
        clue="The ticket needed to get to the loud bird tower before lunch.",
        sound="tap-tap",
        turn_sound="tweet-hoot",
        finish="the keeper held the ticket up with a smile",
        risk="the ticket could blow away",
        target_zone="bird tower",
        keyword="quest",
        tags={"birds", "ticket", "sound"},
    ),
    "return_key": Quest(
        id="return_key",
        mission="return the moon key to the reptile house desk",
        clue="The key had slipped behind a bright green sign.",
        sound="clink-clink",
        turn_sound="hiss-hum",
        finish="the desk held the moon key safely again",
        risk="the key could be lost in the grass",
        target_zone="reptile house",
        keyword="quest",
        tags={"reptiles", "key", "sound"},
    ),
}


ASP_RULES = r"""
compatible(S, Q, P) :- setting(S), quest(Q), prize(P), target(Q, Z), prize_zone(P, Z).
featured(S, Q, P) :- compatible(S, Q, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("target", qid, q.target_zone))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_zone", pid, p.zone))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for qid, q in QUESTS.items():
            for pid, p in PRIZES.items():
                if p.zone == q.target_zone:
                    out.append((sid, qid, pid))
    return out


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class StoryWorld:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Zoo space-adventure quest with sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid zoo quest matches the given options.)")
    place, quest, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def _story_sound(q: Quest) -> str:
    return f"{q.sound}."


def _turn_sound(q: Quest) -> str:
    return f"{q.turn_sound}."


def tell(params: StoryParams) -> StoryWorld:
    world = StoryWorld(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    prize = world.add(Entity(id="Prize", type=PRIZES[params.prize].type, label=PRIZES[params.prize].label,
                             phrase=PRIZES[params.prize].phrase))
    quest = QUESTS[params.quest]

    hero.memes["curiosity"] = 1
    hero.memes["hope"] = 1
    world.say(f"{hero.id} was a {params.trait} little {params.gender} who loved the zoo.")
    world.say(f"The zoo felt big and humongous, like a whole planet full of paws, feathers, and shiny doors.")
    world.say(f"That morning, {hero.id} and {hero.pronoun('possessive')} {parent.label} heard about a space-style {quest.keyword}: {quest.mission}.")
    world.say(f"{quest.clue} { _story_sound(quest) }")
    world.say(f"{hero.id} wanted to help right away, because {hero.pronoun('possessive')} heart liked any mission that sounded like an adventure.")

    world.para()
    world.say(f"They walked past the ticket gate and the monkey house. { _turn_sound(quest) }")
    world.say(f"Then a humongous animal made the clue clearer: a giant, friendly zoo friend pointed its nose toward the right path.")
    world.say(f"{hero.id} paused when the path split near the {quest.target_zone}, because {quest.risk}.")
    hero.memes["worry"] = 1

    world.para()
    hero.memes["bravery"] = 1
    world.say(f"{hero.id} listened again. {quest.sound}, {quest.sound} went the clue from the shiny floor.")
    world.say(f"{hero.id}'s {parent.label} smiled and said they could follow the sounds like star beacons.")
    world.say(f"At last, {quest.finish}.")
    world.say(f"{hero.id} felt proud and light, and the zoo sounded happy all around: chirp-chirp, stomp-stomp, and a little whoosh of spacey joy.")

    world.facts.update(hero=hero, parent=parent, prize=prize, quest=quest, params=params)
    return world


def generation_prompts(world: StoryWorld) -> list[str]:
    f = world.facts
    hero, quest = f["hero"], f["quest"]
    return [
        f'Write a short zoo adventure with a space feel and the word "humongous".',
        f"Tell a child-friendly quest story where {hero.id} follows sound effects to finish {quest.mission}.",
        f"Write a tiny space-adventure at the zoo with a clear quest, a noisy clue, and a happy ending.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, quest = f["hero"], f["parent"], f["prize"], f["quest"]
    return [
        QAItem(
            question=f"Who went on the quest at the zoo?",
            answer=f"{hero.id} went with {hero.pronoun('possessive')} {parent.label} to finish the zoo quest.",
        ),
        QAItem(
            question=f"What was the quest about?",
            answer=f"The quest was about {quest.mission}, and the clue sounded like {quest.sound}.",
        ),
        QAItem(
            question=f"What helped {hero.id} find the way?",
            answer=f"{hero.id} listened to the sound effects and followed the clues until the prize was found.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"At the end, {quest.finish}, and {hero.id} felt proud and happy.",
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a zoo?",
            answer="A zoo is a place where people can see animals and learn about them safely.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or search that someone tries to finish by following clues.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a special sound, like click-click or whoosh, that helps make a story feel lively.",
        ),
    ]


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


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this zoo quest needs a prize whose zone matches the quest target.)"


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def asp_program_text(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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


CURATED = [
    StoryParams(place="zoo", quest="find_map", prize="star_map", name="Luna", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="zoo", quest="deliver_ticket", prize="comet_ticket", name="Max", gender="boy", parent="father", trait="brave"),
    StoryParams(place="zoo", quest="return_key", prize="moon_key", name="Mia", gender="girl", parent="mother", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_text("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible story combos:\n")
        for c in combos:
            print("  ", c)
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
            header = f"### {p.name}: {p.quest} at the zoo"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
