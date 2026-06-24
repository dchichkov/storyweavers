#!/usr/bin/env python3
"""
A small mystery storyworld about a pokey switch, a tense search, and a
reconciliation quest that ends with a gentle repair of feelings.

The seed tale behind this world:
---
A child found that the little switch by the hallway lamp kept getting turned off.
Each time it happened, the room went dark, and someone had to feel their way
along the wall. The child thought the switch looked pokey and strange, like it
was daring someone to touch it.

Soon the child began to suspect that a sibling was playing a secret trick.
The two children searched for clues: a scuff by the door, a tiny shadow on the
stairs, and a note with a crooked arrow. The mystery turned out to be smaller
than the fear. The sibling had not meant harm; they were trying to help fix the
lamp because it flickered.

After they talked, the children reconciled. They found a brighter bulb, flipped
the switch together, and turned the whole search into a little quest that ended
with trust instead of blame.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        gender = self.type
        if gender in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = True
    sounds: str = "a quiet room"


@dataclass
class Clue:
    label: str
    detail: str
    weight: str
    found_in: str


@dataclass
class Quest:
    name: str
    verb: str
    goal: str
    turns: list[str] = field(default_factory=list)


@dataclass
class Switch:
    label: str
    phrase: str
    trait: str
    tricky: bool = True
    flicker_fix: str = "a new bulb"
    turns_on: str = "the lamp"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


@dataclass
class StoryParams:
    name: str
    sibling_name: str
    gender: str
    sibling_gender: str
    parent_type: str
    place: str
    seed: Optional[int] = None


SETTINGS = {
    "hallway": Setting(place="the hallway", indoors=True, sounds="a quiet hallway"),
    "kitchen": Setting(place="the kitchen", indoors=True, sounds="a sleepy kitchen"),
    "attic": Setting(place="the attic", indoors=True, sounds="a dusty attic"),
    "porch": Setting(place="the porch", indoors=False, sounds="the night air"),
}

SWITCHES = {
    "lamp_switch": Switch(
        label="lamp switch",
        phrase="the little switch by the lamp",
        trait="pokey",
        flicker_fix="a brighter bulb",
        turns_on="the hallway lamp",
    ),
    "wall_switch": Switch(
        label="wall switch",
        phrase="the pokey wall switch",
        trait="pokey",
        flicker_fix="a fresh bulb",
        turns_on="the ceiling light",
    ),
}

QUESTS = {
    "search": Quest(name="search", verb="search for clues", goal="find out why the light kept going out"),
    "reconcile": Quest(name="reconcile", verb="talk it through", goal="turn blame into trust"),
}

CLUES = [
    Clue(label="scuff mark", detail="a tiny scuff by the baseboard", weight="light", found_in="hallway"),
    Clue(label="note", detail="a crooked note with an arrow", weight="light", found_in="kitchen"),
    Clue(label="bulb", detail="a flickery bulb in the lamp", weight="medium", found_in="hallway"),
]

GIRL_NAMES = ["Mia", "Lina", "Nora", "Tess", "Ruby", "Ivy"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Leo", "Owen", "Max"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery about a pokey switch and a reconciliation quest.")
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--sibling-name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--sibling-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--place", choices=SETTINGS)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    sibling_gender = args.sibling_gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    sibling_name = args.sibling_name or rng.choice([n for n in (GIRL_NAMES if sibling_gender == "girl" else BOY_NAMES) if n != name])
    parent = args.parent or rng.choice(["mother", "father"])
    place = args.place or rng.choice(list(SETTINGS))
    if name == sibling_name:
        raise StoryError("The hero and sibling must be different children.")
    return StoryParams(
        name=name,
        sibling_name=sibling_name,
        gender=gender,
        sibling_gender=sibling_gender,
        parent_type=parent,
        place=place,
    )


def narrative_setup(world: World, hero: Entity, sibling: Entity, parent: Entity, sw: Switch) -> None:
    world.say(f"{hero.id} lived in {world.setting.place}, where the air felt calm and still.")
    world.say(f"One evening, {hero.pronoun('possessive')} {sw.phrase} seemed extra {sw.trait}, like it might tell a secret.")
    world.say(f"{hero.id} liked the light, but the switch kept going off, and that made the room go dim.")
    world.say(f"{hero.id} began to wonder whether {sibling.id} was hiding something.")
    world.say(f"{parent.label} noticed the hush and said the children should be careful and curious at the same time.")


def add_clues(world: World, hero: Entity) -> None:
    world.para()
    world.say(f"{hero.id} started a small quest to {QUESTS['search'].verb}.")
    for clue in CLUES:
        world.say(f"{hero.id} found {clue.detail} in the {clue.found_in}.")
    world.say(f"Each clue felt tiny, but together they pointed toward the lamp and its tired bulb.")


def reveal_and_reconcile(world: World, hero: Entity, sibling: Entity, parent: Entity, sw: Switch) -> None:
    world.para()
    sibling.memes["fear"] = 1
    sibling.memes["guilt"] = 1
    hero.memes["worry"] = 1
    world.say(f"At last, {sibling.id} admitted the truth: {sibling.pronoun()} had been trying to help fix {sw.turns_on}.")
    world.say(f"They had not meant to play a trick; they just wanted the light to stop flickering.")
    world.say(f"{hero.id} felt the blame soften, because the mystery had a kind reason after all.")
    world.say(f"{parent.label} brought {sw.flicker_fix}, and the children worked together under the warm lamp glow.")
    world.say(f"{hero.id} and {sibling.id} talked, forgave each other, and made a little reconciliation quest out of the evening.")
    hero.memes["trust"] = 1
    sibling.memes["trust"] = 1
    hero.memes["peace"] = 1
    sibling.memes["peace"] = 1
    world.say(f"Then {hero.id} flipped the {sw.label} on, and {sw.turns_on} shone bright again.")


def generate_story(world: World, params: StoryParams) -> StorySample:
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    sibling = world.add(Entity(id=params.sibling_name, kind="character", type=params.sibling_gender))
    parent = world.add(Entity(id=params.parent_type, kind="character", type=params.parent_type, label=f"the {params.parent_type}"))
    sw = SWITCHES["lamp_switch"] if params.place in {"hallway", "kitchen"} else SWITCHES["wall_switch"]

    narrative_setup(world, hero, sibling, parent, sw)
    add_clues(world, hero)
    reveal_and_reconcile(world, hero, sibling, parent, sw)

    world.facts.update(hero=hero, sibling=sibling, parent=parent, switch=sw, quest=QUESTS["reconcile"], setting=world.setting)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return generate_story(World(SETTINGS[params.place]), params)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, sibling, sw = f["hero"], f["sibling"], f["switch"]
    return [
        f'Write a short mystery story for a young child that includes a pokey switch and a kind ending.',
        f"Tell a story where {hero.id} suspects {sibling.id} about {sw.phrase}, then learns the truth and reconciles.",
        f"Write a gentle quest story about clues, a switch, and children making up after a misunderstanding.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, sibling, sw, parent = f["hero"], f["sibling"], f["switch"], f["parent"]
    return [
        QAItem(
            question=f"What made {hero.id} think something secret was happening?",
            answer=f"{hero.id} kept seeing {sw.phrase} and the room going dim, so the switch felt like a clue and a worry at the same time.",
        ),
        QAItem(
            question=f"What was the quest in the story?",
            answer=f"The quest was to {QUESTS['search'].verb} and then {QUESTS['reconcile'].verb} so the children could understand each other again.",
        ),
        QAItem(
            question=f"Why did {sibling.id} keep touching the light?",
            answer=f"{sibling.id} was trying to help fix the lamp because it flickered, not to cause trouble.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {sibling.id}?",
            answer=f"They talked, forgave each other, and ended the night with trust, a brighter lamp, and a peaceful feeling.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a switch?",
            answer="A switch is a little control you flip or press to turn something on or off, like a lamp or light.",
        ),
        QAItem(
            question="What does pokey mean?",
            answer="Pokey can mean something sticks out a little and feels pointy or sharp to touch.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important, like solving a problem or finding an answer.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop fighting, make up, and feel friendly toward each other again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
switch(pokey_switch).
quest(search).
quest(reconcile).
topic(mystery).
supports(pokey_switch, mystery).
supports(search, mystery).
supports(reconcile, mystery).

story_ok(S) :- switch(S), quest(search), quest(reconcile), supports(S, mystery).
#show story_ok/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("switch", "pokey_switch"),
        asp.fact("quest", "search"),
        asp.fact("quest", "reconcile"),
        asp.fact("topic", "mystery"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/1."))
    ok = bool(asp.atoms(model, "story_ok"))
    if ok:
        print("OK: ASP twin recognizes the mystery storyworld.")
        return 0
    print("MISMATCH: ASP twin did not recognize the storyworld.")
    return 1


def asp_valid() -> bool:
    import asp
    model = asp.one_model(asp_program("#show story_ok/1."))
    return bool(asp.atoms(model, "story_ok"))


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
    StoryParams(name="Mia", sibling_name="Eli", gender="girl", sibling_gender="boy", parent_type="mother", place="hallway"),
    StoryParams(name="Leo", sibling_name="Nora", gender="boy", sibling_gender="girl", parent_type="father", place="kitchen"),
    StoryParams(name="Ivy", sibling_name="Max", gender="girl", sibling_gender="boy", parent_type="mother", place="attic"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show story_ok/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP twin ready." if asp_valid() else "ASP twin not ready.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
