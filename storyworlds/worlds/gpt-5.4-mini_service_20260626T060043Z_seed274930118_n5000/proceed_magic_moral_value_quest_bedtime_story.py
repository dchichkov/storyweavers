#!/usr/bin/env python3
"""
A bedtime-story world about a child, a small magical quest, and a moral choice.

The seed tale behind this world:
---
At bedtime, Nia finds a tiny silver key under her pillow. A sleepy little moon
mouse asks for help opening a door in the garden wall, but the key can only work
if Nia does the kind thing first: share her warm blanket with a shivering kitten.
Nia wants to hurry to the magic door, but she pauses, helps the kitten, and then
proceeds to the garden. The door opens, the mouse smiles, and the night feels
gentle and bright.

This file turns that premise into a small, constraint-checked story world:
a child can proceed on a quest only after a moral value is satisfied, with
magic as the bridge between choice and reward.
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
    worn_by: Optional[str] = None
    location: str = ""
    plural: bool = False
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
    place: str
    indoors: bool = True
    quiet: bool = True


@dataclass
class Quest:
    id: str
    goal: str
    proceed_word: str
    magic_action: str
    reward: str
    danger: str
    value: str
    value_label: str
    keyword: str = "proceed"


@dataclass
class Charm:
    id: str
    label: str
    protects: set[str] = field(default_factory=set)
    helps: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    quest: str
    value: str
    charm: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


SETTINGS = {
    "bedroom": Setting(place="the bedroom", indoors=True),
    "garden": Setting(place="the garden", indoors=False),
    "hall": Setting(place="the hallway", indoors=True),
}

QUESTS = {
    "moon-door": Quest(
        id="moon-door",
        goal="open the little moon door",
        proceed_word="proceed",
        magic_action="follow the moon path",
        reward="a silver blessing",
        danger="the door stays sleepy",
        value="kindness",
        value_label="kind",
        keyword="proceed",
    ),
    "star-lantern": Quest(
        id="star-lantern",
        goal="light the star lantern",
        proceed_word="proceed",
        magic_action="sing the lantern awake",
        reward="a warm glow",
        danger="the lantern stays dark",
        value="patience",
        value_label="patient",
        keyword="proceed",
    ),
    "rabbit-bridge": Quest(
        id="rabbit-bridge",
        goal="cross the little rabbit bridge",
        proceed_word="proceed",
        magic_action="step gently on the moon stones",
        reward="a soft path home",
        danger="the bridge will wobble",
        value="care",
        value_label="careful",
        keyword="proceed",
    ),
}

CHARMS = {
    "blanket": Charm(
        id="blanket",
        label="a warm blanket",
        protects={"cold"},
        helps={"kindness"},
    ),
    "lantern": Charm(
        id="lantern",
        label="a tiny lantern",
        protects={"dark"},
        helps={"patience"},
    ),
    "gloves": Charm(
        id="gloves",
        label="soft mittens",
        protects={"wind"},
        helps={"care"},
    ),
}

GIRL_NAMES = ["Nia", "Mina", "Lina", "Rosa", "Ivy", "Mira", "Luna", "Ada"]
BOY_NAMES = ["Noah", "Eli", "Ben", "Theo", "Finn", "Leo", "Owen", "Kai"]
TRAITS = ["gentle", "curious", "sleepy", "brave", "kind", "soft-spoken"]


ASP_RULES = r"""
quest_ready(P, Q) :- place(P), quest(Q), value_for(Q, V), charm_help(C, V), has_charm(P, C).
quest_safe(P, Q) :- quest_ready(P, Q), magic_works(Q).
valid_story(P, Q, V, C) :- quest_ready(P, Q), value_for(Q, V), charm_help(C, V).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("value_for", qid, q.value))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        for v in sorted(c.helps):
            lines.append(asp.fact("charm_help", cid, v))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in SETTINGS:
        for qid, q in QUESTS.items():
            for cid, c in CHARMS.items():
                if q.value in c.helps:
                    combos.append((place, qid, q.value, cid))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: magic, moral value, quest, and proceed.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--value", choices=sorted({q.value for q in QUESTS.values()}))
    ap.add_argument("--charm", choices=CHARMS)
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
              and (args.value is None or c[2] == args.value)
              and (args.charm is None or c[3] == args.charm)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, value, charm = rng.choice(sorted(combos))
    q = QUESTS[quest]
    if value != q.value:
        raise StoryError("Invalid value for this quest.")
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, value=value, charm=charm, name=name, gender=gender, parent=parent, trait=trait)


def make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    quest = QUESTS[params.quest]
    charm = CHARMS[params.charm]
    charm_ent = world.add(Entity(id=charm.id, type="thing", label=charm.label, owner=hero.id))
    charm_ent.worn_by = hero.id

    world.say(f"{hero.id} was a {params.trait} little {params.gender} who loved bedtime stories and quiet rooms.")
    world.say(f"Before sleep, {hero.id} found {charm.label} and heard of a tiny quest to {quest.goal}.")
    world.say(f"The quest asked {hero.id} to be {quest.value_label}: {quest.magic_action} could only work after a good choice.")

    world.para()
    hero.memes["desire"] = 1.0
    world.say(f"{hero.id} wanted to {quest.proceed_word} at once, but {hero.pronoun('possessive')} {params.parent} smiled and waited.")
    world.say(f"Then {hero.id} noticed a small need nearby: a shivering kitten curled under the window.")

    if quest.value == "kindness":
        world.say(f"{hero.id} wrapped the kitten in {charm.label} and sat with it until it purred.")
    elif quest.value == "patience":
        world.say(f"{hero.id} sat still with {charm.label} and listened to the slow night sounds until the kitten relaxed.")
    else:
        world.say(f"{hero.id} moved softly, using {charm.label} to help without waking the sleepy house.")

    hero.memes[quest.value] = 1.0
    world.say(f"At last, {hero.id} could {quest.proceed_word} to {world.setting.place}.")

    world.para()
    world.say(f"There, the {quest.goal} waited like a secret in the dark.")
    world.say(f"{hero.id} used magic to {quest.magic_action}, and the door opened with a gentle shine.")
    world.say(f"The night answered with {quest.reward}, and {hero.id} felt warm inside for doing the right thing first.")

    world.facts.update(
        hero=hero,
        parent=parent,
        quest=quest,
        charm=charm,
        setting=world.setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    return [
        f'Write a bedtime story for a young child about magic, moral value, and a quest, and include the word "proceed".',
        f"Tell a gentle story where {hero.id} must be {quest.value_label} before {hero.pronoun('subject')} can proceed on a magical quest.",
        f"Write a short sleepy-time tale in which a child helps someone small, then proceeds to a magic door.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    parent = f["parent"]
    charm = f["charm"]
    return [
        QAItem(
            question=f"What did {hero.id} need to do before {hero.pronoun('subject')} could proceed on the quest?",
            answer=f"{hero.id} needed to be {quest.value_label} first, because the magic only worked after a kind choice.",
        ),
        QAItem(
            question=f"What magical thing did {hero.id} use to help with the quest?",
            answer=f"{hero.id} used {charm.label} and the little bedtime magic in the room.",
        ),
        QAItem(
            question=f"Who waited while {hero.id} paused before proceeding?",
            answer=f"{hero.pronoun('possessive').capitalize()} {parent.label} waited softly and let {hero.id} choose the right thing first.",
        ),
        QAItem(
            question=f"What happened after {hero.id} chose the good, {quest.value} path?",
            answer=f"The quest opened up, the door shone, and {hero.id} received {quest.reward}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    quest = f["quest"]
    charm = f["charm"]
    items = [
        QAItem(
            question="What is a quest?",
            answer="A quest is a goal or journey someone takes to find something, solve a problem, or help someone.",
        ),
        QAItem(
            question="What does it mean to be kind?",
            answer="Being kind means helping, sharing, and caring about other people or small creatures.",
        ),
        QAItem(
            question="What is magic in a bedtime story?",
            answer="Magic is something wonderful or impossible-looking that helps the story feel special and surprising.",
        ),
    ]
    if quest.value == "patience":
        items.append(QAItem(question="What does it mean to be patient?", answer="Being patient means waiting calmly without rushing.")))
    if charm.id == "blanket":
        items.append(QAItem(question="What is a blanket for?", answer="A blanket keeps someone warm and cozy.")))
    return items


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
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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


CURATED = [
    StoryParams(place="bedroom", quest="moon-door", value="kindness", charm="blanket", name="Nia", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="hall", quest="star-lantern", value="patience", charm="lantern", name="Theo", gender="boy", parent="father", trait="sleepy"),
    StoryParams(place="garden", quest="rabbit-bridge", value="care", charm="gloves", name="Mira", gender="girl", parent="mother", trait="curious"),
]


def resolve_gender_for_quest(quest: Quest, gender: str) -> None:
    return None


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:\n")
        for item in combos:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.name}: {p.quest} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
