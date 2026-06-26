#!/usr/bin/env python3
"""
storyworlds/worlds/plankton_stand_repetition_friendship_misunderstanding_detective_story.py
===========================================================================================

A small detective-style story world about a plankton stand, a repeated clue,
a friendship, and a misunderstanding that gets solved.

The seed image:
- A child detective keeps visiting the same plankton stand.
- The same little sign, the same missing scoop, and the same footprints repeat.
- A friend looks suspicious, but the real cause is a simple misunderstanding.
- The ending should feel like a solved mystery and a repaired friendship.

The world is intentionally narrow:
- One place: a stand by the water.
- One clue pattern: repetition.
- One emotional turn: misunderstanding.
- One resolution: friendship after the truth is uncovered.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
    place: str
    afford: str
    repeated_details: list[str] = field(default_factory=list)


@dataclass
class Mystery:
    id: str
    clue_noun: str
    clue_verb: str
    clue_phrase: str
    cause_phrase: str
    misunderstanding_phrase: str
    resolution_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FriendTool:
    id: str
    label: str
    phrase: str
    helps: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "harbor": Setting(
        place="the harbor stand",
        afford="plankton",
        repeated_details=["same blue awning", "same salty breeze", "same chalk price sign"],
    ),
    "pier": Setting(
        place="the pier stand",
        afford="plankton",
        repeated_details=["same striped bucket", "same gull circling overhead", "same wooden counter"],
    ),
    "aquarium": Setting(
        place="the aquarium stand",
        afford="plankton",
        repeated_details=["same glass tank", "same wet floor", "same careful queue"],
    ),
}

MYSTERIES = {
    "missing_scoop": Mystery(
        id="missing_scoop",
        clue_noun="scoop",
        clue_verb="go missing",
        clue_phrase="the same little scoop of plankton kept disappearing",
        cause_phrase="a tide-cart worker had been using the scoop for deliveries",
        misunderstanding_phrase="the friend looked guilty because the scoop was found in their bucket",
        resolution_phrase="the bucket was for carrying the borrowed scoop back",
        tags={"plankton", "stand", "repetition", "misunderstanding", "friendship"},
    ),
    "repeated_note": Mystery(
        id="repeated_note",
        clue_noun="note",
        clue_verb="reappear",
        clue_phrase="the same note kept showing up under the cash box",
        cause_phrase="the notes were being left by the stand owner to remind everyone of the order list",
        misunderstanding_phrase="the friend thought the note was a secret message",
        resolution_phrase="the note was just a normal reminder",
        tags={"plankton", "stand", "repetition", "misunderstanding", "friendship"},
    ),
    "borrowed_bucket": Mystery(
        id="borrowed_bucket",
        clue_noun="bucket",
        clue_verb="vanish",
        clue_phrase="the same bucket vanished and came back again and again",
        cause_phrase="the bucket was being borrowed for cleaning the damp deck",
        misunderstanding_phrase="the friend looked sneaky because they were carrying the bucket away",
        resolution_phrase="they were only taking it to the wash tub and back",
        tags={"plankton", "stand", "repetition", "misunderstanding", "friendship"},
    ),
}

FRIEND_TOOLS = {
    "magnifier": FriendTool(
        id="magnifier",
        label="a little magnifying glass",
        phrase="a little magnifying glass",
        helps="helped spot tiny shell prints",
    ),
    "notebook": FriendTool(
        id="notebook",
        label="a tiny notebook",
        phrase="a tiny notebook",
        helps="helped keep the repeated clues in order",
    ),
    "lantern": FriendTool(
        id="lantern",
        label="a small lantern",
        phrase="a small lantern",
        helps="helped follow the same track after sunset",
    ),
}

NAMES = ["Mina", "Nico", "Lena", "Toby", "Iris", "Owen", "Mara", "Eli"]
FRIEND_NAMES = ["June", "Pip", "Sage", "Remy", "Nell", "Quinn"]
TRAITS = ["careful", "curious", "patient", "quiet", "sharp", "brave"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    friend: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for mystery in MYSTERIES:
            combos.append((place, mystery))
    return combos


def explain_rejection(place: str, mystery: str) -> str:
    return f"(No story: the mystery {mystery} does not fit the setting {place}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective story world: a plankton stand, repetition, a misunderstanding, and friendship."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    if args.place and args.mystery:
        if (args.place, args.mystery) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.mystery))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, friend=friend, trait=trait)


def setting_detail(setting: Setting) -> str:
    details = setting.repeated_details
    if len(details) == 3:
        return f"Every day, it had {details[0]}, {details[1]}, and {details[2]}."
    return f"It always looked the same in the morning light."


def introduce(world: World, hero: Entity, friend: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in hero.traits if t != 'little'), 'curious')} {hero.type} who loved detective work."
    )
    world.say(
        f"{hero.id} and {friend.id} were friends, and they liked solving the same mystery together."
    )
    world.say(
        f"At {world.setting.place}, {mystery.clue_phrase}, and that made {hero.id} pause."
    )
    world.say(setting_detail(world.setting))


def clue_repeat(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["focus"] += 1
    world.say(
        f"Each morning, {hero.id} noticed the clue again: {mystery.clue_phrase}."
    )
    world.say(
        f"The repetition felt odd, like the stand was trying to say something twice."
    )


def suspect_friend(world: World, hero: Entity, friend: Entity, mystery: Mystery, tool: FriendTool) -> None:
    friend.memes["uncertainty"] += 1
    hero.memes["doubt"] += 1
    world.say(
        f"{hero.id} held up {tool.phrase}, and it {tool.helps}."
    )
    world.say(
        f"Then {hero.id} saw {friend.id} near the counter and wondered if {friend.pronoun('subject')} was hiding something."
    )
    world.say(
        f"It looked like a clue, but it was really a misunderstanding."
    )


def accusation(world: World, hero: Entity, friend: Entity, mystery: Mystery) -> None:
    hero.memes["worry"] += 1
    friend.memes["hurt"] += 1
    world.say(
        f"{hero.id} asked {friend.id} about the {mystery.clue_noun}, and {friend.id} went very still."
    )
    world.say(
        f"For a moment, their friendship felt as fragile as a shell on wet sand."
    )


def reveal(world: World, hero: Entity, friend: Entity, mystery: Mystery) -> None:
    hero.memes["understanding"] += 1
    friend.memes["understanding"] += 1
    world.say(
        f"At last, {hero.id} checked the back path and found the truth: {mystery.cause_phrase}."
    )
    world.say(
        f"That explained why {mystery.misunderstanding_phrase}."
    )
    world.say(
        f"{hero.id} apologized, because the real mystery had never been {friend.id}."
    )


def resolve_friendship(world: World, hero: Entity, friend: Entity, mystery: Mystery) -> None:
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    hero.memes["worry"] = 0.0
    friend.memes["hurt"] = 0.0
    world.say(
        f"{friend.id} smiled and forgave {hero.id}."
    )
    world.say(
        f"Together they carried the {mystery.clue_noun} back, and the stand felt calm again."
    )
    world.say(
        f"By evening, the case was solved, the clue was clear, and the friends walked home side by side."
    )


def tell(setting: Setting, mystery: Mystery, hero_name: str = "Mina", hero_type: str = "girl",
         friend_name: str = "June", parent_type: str = "parent", trait: str = "curious") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait]))
    friend = world.add(Entity(id=friend_name, kind="character", type="child", traits=["little", "friendly"]))
    tool = world.add(Entity(id="tool", type="thing", label="tool"))
    world.facts.update(hero=hero, friend=friend, mystery=mystery, tool=tool)

    introduce(world, hero, friend, mystery)
    world.para()
    clue_repeat(world, hero, mystery)
    suspect_friend(world, hero, friend, mystery, FRIEND_TOOLS["notebook"])
    accusation(world, hero, friend, mystery)
    world.para()
    reveal(world, hero, friend, mystery)
    resolve_friendship(world, hero, friend, mystery)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a young child about {f["hero"].id}, a plankton stand, and a clue that repeats.',
        f"Tell a gentle mystery where {f['hero'].id} and {f['friend'].id} think there is a problem at {world.setting.place}, but the truth is a misunderstanding.",
        f'Write a simple story that includes the words "plankton" and "stand" and ends with friendship after the case is solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, mystery = f["hero"], f["friend"], f["mystery"]
    return [
        QAItem(
            question=f"Who solved the mystery at {world.setting.place}?",
            answer=f"{hero.id} solved it with {friend.id}. They looked carefully, noticed the repeated clue, and found the real reason behind it."
        ),
        QAItem(
            question=f"What kept happening again and again in the story?",
            answer=f"{mystery.clue_phrase.capitalize()}. That repetition made the mystery feel strange until the truth was found."
        ),
        QAItem(
            question=f"Why did the friends have a misunderstanding?",
            answer=f"They thought {friend.id} might be hiding the clue, but the clue had only been borrowed for a normal reason. The mistake caused worry until {hero.id} checked more carefully."
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {friend.id}?",
            answer=f"They apologized to each other, solved the case, and stayed friends. The stand was peaceful again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is plankton?",
            answer="Plankton are tiny living things that float in water. Many sea creatures eat them."
        ),
        QAItem(
            question="What is a stand?",
            answer="A stand is a small place where someone sells or gives out things, often from a counter or table."
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people think the wrong thing about each other or about a situation."
        ),
        QAItem(
            question="Why can friendship help in a mystery story?",
            answer="Friends can share clues, talk kindly, and help each other stay calm until the truth is found."
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is valid when it features the plankton stand setting and the
% repeated clue pattern that can lead to a misunderstanding and then friendship.
valid(Place, Mystery) :- setting(Place), case(Mystery), clue(Mystery), repeat(Mystery), friendship(Mystery), misunderstanding(Mystery).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("case", mid))
        lines.append(asp.fact("clue", mid))
        lines.append(asp.fact("repeat", mid))
        lines.append(asp.fact("friendship", mid))
        lines.append(asp.fact("misunderstanding", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("tag", mid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(place="harbor", mystery="missing_scoop", name="Mina", gender="girl", friend="June", trait="curious"),
    StoryParams(place="pier", mystery="repeated_note", name="Toby", gender="boy", friend="Pip", trait="careful"),
    StoryParams(place="aquarium", mystery="borrowed_bucket", name="Iris", gender="girl", friend="Quinn", trait="sharp"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MYSTERIES[params.mystery], params.name, params.gender, params.friend, "parent", params.trait)
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
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible (place, mystery) combos:\n")
        for place, mystery in combos:
            print(f"  {place:10} {mystery}")
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
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
