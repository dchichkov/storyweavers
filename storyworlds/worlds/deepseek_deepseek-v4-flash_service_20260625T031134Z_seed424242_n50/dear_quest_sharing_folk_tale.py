#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/dear_quest_sharing_folk_tale.py
====================================================================================================================

A standalone story world for a small folk-tale domain about a child discovering
that a kind quest and generous sharing bring more joy than holding onto
everything alone.

Seed tale:
---
Once upon a time, in a small village at the edge of a green wood, there lived a
dear little girl named Elara. She had a basket of ripe berries she had picked
herself. The berries were plump and sweet, and she loved them very much.

One morning, a young boy named Theo came to the village. He was hungry and had
no food. He asked Elara if she would share her berries. But Elara clutched her
basket and said, "No, these are mine."

Theo's face fell, and he sat down by the old oak tree, looking sad. Elara
walked away, but her basket felt heavy, and the berries did not taste as sweet.

That afternoon, Elara saw a squirrel hiding an acorn and then another squirrel
coming to share the spot. She thought, "Why do I feel sad when I have so many
berries?" She ran back to the oak tree and gave half her berries to Theo. His
eyes lit up, and they ate together. The berries tasted sweet again.

From that day on, whenever Elara picked berries, she set aside some for anyone
who passed by.

Causal state updates:
---
    give_share(actor, recipient) -> actor.generosity += 1
                                   actor.joy += 1
                                   recipient.joy += 1
                                   recipient.hunger -= 1
                                   actor.possessiveness -= 0.5
    refuse_share(actor, recipient) -> actor.generosity -= 1
                                      actor.possessiveness += 1
                                      actor.joy -= 0.5
                                      recipient.hunger += 1
                                      recipient.sadness += 1
    complete_quest(actor)         -> actor.joy += 2
                                     actor.courage += 1
                                     actor.generosity += 1
    observe_sharing(actor)        -> actor.kindness_insight += 1
    berry_pick(actor)             -> actor.berries += 1
                                     actor.joy += 0.5
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MESS_KINDS = {"hunger", "sadness"}
REGIONS = {"feet", "legs", "torso", "heart"}


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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "maiden"}
        male = {"boy", "father", "man", "lad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the village"
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    reward: str
    kindness_lesson: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    label: str
    phrase: str
    type: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


SETTINGS = {
    "village": Setting(place="the village", affords={"berry_quest"}),
    "forest": Setting(place="the green wood", affords={"berry_quest"}),
    "meadow": Setting(place="the sunlit meadow", affords={"berry_quest"}),
}

QUESTS = {
    "berry_quest": Quest(
        id="berry_quest",
        verb="pick berries to share",
        gerund="picking berries to share",
        rush="reach for the berry bush",
        reward="a basket of ripe berries",
        kindness_lesson="sharing makes the heart light",
        keyword="berries",
        tags={"berry", "sharing"},
    ),
}

GIFTS = {
    "berries": Gift(
        label="berries",
        phrase="a basket of bright red berries",
        type="berries",
        plural=True,
    ),
    "bread": Gift(
        label="bread",
        phrase="a warm loaf of bread",
        type="bread",
    ),
}

GIRL_NAMES = ["Elara", "Maya", "Lina", "Sera", "Fia", "Nora", "Tessa", "Briar"]
BOY_NAMES = ["Theo", "Rohan", "Kai", "Finn", "Leo", "Jasper", "Eli", "Nikhil"]
TRAITS = ["kind-hearted", "curious", "stubborn", "brave", "generous", "thoughtful"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for quest_id in setting.affords:
            combos.append((place, quest_id))
    return combos


@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "berry": [
        ("What is a berry?",
         "A berry is a small, round fruit that grows on bushes. Berries can be "
         "red, blue, or black, and they taste sweet or tart."),
    ],
    "sharing": [
        ("Why is sharing kind?",
         "Sharing is kind because it gives something good to someone else. When "
         "you share, you help others feel happy and less alone."),
    ],
    "quest": [
        ("What is a quest?",
         "A quest is a special journey or task someone takes to find something "
         "or help someone. It often has a kind purpose."),
    ],
}
KNOWLEDGE_ORDER = ["berry", "sharing", "quest"]


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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def give_share_effect(world: World, actor: Entity, recipient: Entity) -> None:
    actor.memes["generosity"] += 1
    actor.memes["joy"] += 1
    recipient.memes["joy"] += 1
    recipient.meters["hunger"] = max(0, recipient.meters["hunger"] - 1)
    actor.memes["possessiveness"] = max(0, actor.memes["possessiveness"] - 0.5)
    sig = ("shared", actor.id, recipient.id)
    if sig not in world.fired:
        world.fired.add(sig)


def refuse_share_effect(world: World, actor: Entity, recipient: Entity) -> None:
    actor.memes["generosity"] = max(0, actor.memes["generosity"] - 0.5)
    actor.memes["possessiveness"] += 1
    actor.memes["joy"] = max(0, actor.memes["joy"] - 0.5)
    recipient.meters["hunger"] += 1
    recipient.memes["sadness"] += 1
    sig = ("refused", actor.id, recipient.id)
    if sig not in world.fired:
        world.fired.add(sig)


def observe_sharing_effect(world: World, actor: Entity) -> None:
    actor.memes["kindness_insight"] += 1
    sig = ("observed", actor.id)
    if sig not in world.fired:
        world.fired.add(sig)


def tell(setting: Setting, quest: Quest, hero_name: str = "Elara",
         hero_type: str = "girl", hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["dear"] + (hero_traits or ["kind-hearted"]),
    ))
    traveler = world.add(Entity(
        id="Traveler", kind="character", type="boy",
        label="the traveler",
        traits=["hungry"],
    ))
    world.facts["hero"] = hero
    world.facts["traveler"] = traveler
    world.facts["quest"] = quest

    world.say(f"Once upon a time, in {setting.place}, there lived a dear little {hero_type} named {hero_name}.")
    world.say(f"{hero_name} had a basket of ripe berries {hero.pronoun('possessive')} own hands had picked.")
    world.say(f"The berries were plump and sweet, and {hero.pronoun()} loved them very much.")

    world.para()
    world.say(f"One morning, a young lad named {traveler.id} came to {setting.place}.")
    world.say(f"He was hungry and had no food. He asked {hero_name} if {hero.pronoun()} would share.")
    world.say(f"But {hero_name} clutched {hero.pronoun('possessive')} basket and said, 'No, these are mine.'")
    refuse_share_effect(world, hero, traveler)
    world.say(f"{traveler.id}'s face fell, and he sat down by the old oak tree, looking sad.")
    world.say(f"{hero_name} walked away, but {hero.pronoun('possessive')} basket felt heavy, and the berries did not taste as sweet.")

    world.para()
    world.say(f"That afternoon, {hero_name} saw a squirrel hiding an acorn and then another squirrel coming to share the spot.")
    observe_sharing_effect(world, hero)
    world.say(f"{hero.pronoun().capitalize()} thought, 'Why do I feel sad when I have so many berries?'")
    world.say(f"{hero.pronoun().capitalize()} ran back to the oak tree and gave half {hero.pronoun('possessive')} berries to {traveler.id}.")
    give_share_effect(world, hero, traveler)
    world.say(f"{traveler.id}'s eyes lit up, and they ate together. The berries tasted sweet again.")

    world.para()
    world.say(f"From that day on, whenever {hero_name} picked berries, {hero.pronoun()} set aside some for anyone who passed by.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, quest = f["hero"], f["quest"]
    return [
        f'Write a short folk tale for a child about a dear {hero.type} named {hero.id} who learns about sharing.',
        f"Tell a gentle story where a {hero.type} goes on a {quest.keyword} quest and discovers that sharing brings joy.",
        f'Write a simple story about a {hero.type} who gives part of {hero.pronoun("possessive")} {quest.reward} to someone in need.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    traveler = f["traveler"]
    sub, obj, pos = hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")
    qa = [
        QAItem(
            question=f"What did dear {hero.id} have in {pos} basket at the beginning of the folk tale?",
            answer=f"{hero.id} had a basket of ripe berries that {sub} had picked {pos}self. The berries were "
                   f"plump and sweet, and {sub} loved them very much.",
        ),
        QAItem(
            question=f"Who came to {world.setting.place} hungry and asked {hero.id} for food?",
            answer=f"A young lad named {traveler.id} came to {world.setting.place}. He was hungry and had no food, "
                   f"so he asked {hero.id} if {sub} would share {pos} berries.",
        ),
        QAItem(
            question=f"How did dear {hero.id} feel after refusing to share {pos} berries?",
            answer=f"{hero.id} felt sad because {pos} basket felt heavy, and the berries did not taste as sweet. "
                   f"{sub} saw {traveler.id} sitting sadly by the old oak tree, and {pos} heart felt heavy.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"What made dear {hero.id} change {pos} mind and share {pos} berries?",
            answer=f"{hero.id} saw two squirrels sharing a spot to hide an acorn. That gave {obj} a kindness insight. "
                   f"{sub} ran back to {traveler.id} and gave half {pos} berries to {obj}. Then they ate together, "
                   f"and the berries tasted sweet again.",
        ))
        qa.append(QAItem(
            question=f"What did dear {hero.id} do from that day onward in the folk tale?",
            answer=f"From that day on, whenever {hero.id} picked berries, {sub} set aside some for anyone who passed by. "
                   f"The quest of sharing became {pos} new and joyful habit.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["quest"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="village", quest="berry_quest", name="Elara", gender="girl", trait="kind-hearted"),
    StoryParams(place="forest", quest="berry_quest", name="Theo", gender="boy", trait="brave"),
    StoryParams(place="meadow", quest="berry_quest", name="Lina", gender="girl", trait="generous"),
]


ASP_RULES = r"""
quest_at(Place, Q) :- setting(Place), affords(Place, Q).
hero_gender(H, G) :- hero(H), gender(H, G).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", pid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    clingo_set = set(asp.atoms(asp.one_model(asp_program("#show quest_at/2.")), "quest_at"))
    python_set = set()
    for place in SETTINGS:
        for quest_id in SETTINGS[place].affords:
            python_set.add((place, quest_id))
    if clingo_set == python_set:
        print(f"OK: clingo gate matches ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk tale about a dear child, a quest, and sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.quest and args.quest not in [q for qs in SETTINGS.values() for q in qs.affords]:
        raise StoryError(f"(No setting supports the quest '{args.quest}'.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUESTS[params.quest], params.name, params.gender, [params.trait])
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
        print(asp_program("#show quest_at/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp.atoms(asp.one_model(asp_program("#show quest_at/2.")), "quest_at")
        print(f"{len(combos)} compatible (place, quest) pairs:")
        for place, quest in sorted(combos):
            print(f"  {place:10} {quest}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
