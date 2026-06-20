#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/magician_surprise_quest_flashback_slice_of_life.py
===================================================================================

A standalone story world for a small slice-of-life tale about a magician who
prepares a gentle surprise quest, remembers a helpful flashback, and ends the day
with a cozy, ordinary win.

The world model keeps a few typed entities with physical meters and emotional
memes. A child and a magician share a neighborhood day: an invitation arrives,
a small quest is set, a flashback teaches a better trick, and a surprise reveal
makes the ending feel warm and complete.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/magician_surprise_quest_flashback_slice_of_life.py
    python storyworlds/worlds/gpt-5.4-mini/magician_surprise_quest_flashback_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4-mini/magician_surprise_quest_flashback_slice_of_life.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/magician_surprise_quest_flashback_slice_of_life.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    detail: str


@dataclass
class Quest:
    id: str
    goal: str
    clue: str
    item: str
    finish: str


@dataclass
class Surprise:
    id: str
    reveal: str
    gift: str
    feeling: str


@dataclass
class Flashback:
    id: str
    cue: str
    memory: str
    lesson: str


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_nervous(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes["quest"] >= THRESHOLD and e.memes["helping"] < THRESHOLD:
            sig = ("nervous", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["wonder"] += 1
            out.append("")
    return out


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("flashback_used") and not world.facts.get("flashback_done"):
        sig = ("flashback",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["flashback_done"] = True
            out.append("")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    rules = [Rule("nervous", _r_nervous), Rule("flashback", _r_flashback)]
    while changed:
        changed = False
        for rule in rules:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for qid in QUESTS:
            for sur in SURPRISES:
                if qid == "lost_coin" and sur == "music_box":
                    combos.append((sid, qid, sur))
                if qid == "birthday_note" and sur in {"cookie_plate", "music_box"}:
                    combos.append((sid, qid, sur))
    return combos


@dataclass
class StoryParams:
    setting: str
    quest: str
    surprise: str
    magician_name: str
    child_name: str
    child_gender: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "The kettle hummed, and a sunbeam rested on the table."),
    "garden": Setting("garden", "the garden", "The little path had warm stones and a few sleepy flowers."),
    "porch": Setting("porch", "the porch", "A porch swing creaked softly beside a jar of lemonade."),
}

QUESTS = {
    "lost_coin": Quest("lost_coin", "find a lost coin", "the coin rolled under a chair", "a shiny coin", "Soon the coin was back in the jar."),
    "birthday_note": Quest("birthday_note", "deliver a birthday note", "the note needed a ribbon", "a blue ribbon", "Then the note looked ready for sharing."),
    "tiny_plant": Quest("tiny_plant", "carry a tiny plant to a sunny spot", "the plant wanted gentle hands", "a small plant pot", "After that, the plant had a brighter place to sit."),
}

SURPRISES = {
    "music_box": Surprise("music_box", "a tiny music box clicked open", "a little music box", "delighted"),
    "cookie_plate": Surprise("cookie_plate", "a plate of warm cookies appeared", "a plate of cookies", "cozy"),
    "star_card": Surprise("star_card", "a hand-painted star card was waiting", "a star card", "smiling"),
}

FLASHBACKS = {
    "rainy_day": Flashback("rainy_day", "the rain on the window", "the magician had once solved a rainy mess by using a tray and a towel", "small plans work best"),
    "grandpa_story": Flashback("grandpa_story", "the old family story", "the magician remembered how a grandpa once taught a quiet, careful trick", "kind tricks are the best tricks"),
    "school_show": Flashback("school_show", "a school show memory", "the magician remembered missing a cue until a kind friend whispered the next step", "helpers make quests easier"),
}

MAGICIANS = ["Milo", "Nina", "Owen", "Sage", "Iris"]
CHILDREN = ["Lena", "Ben", "Maya", "Theo", "Rosa", "Cal"]
TRAITS = ["careful", "curious", "gentle", "patient", "thoughtful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: magician, surprise, quest, flashback, slice of life.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--flashback", choices=FLASHBACKS)
    ap.add_argument("--magician")
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, surprise = rng.choice(sorted(combos))
    magician_name = args.magician or rng.choice(MAGICIANS)
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child or rng.choice(CHILDREN)
    trait = rng.choice(TRAITS)
    flashback = args.flashback or rng.choice(list(FLASHBACKS))
    return StoryParams(setting, quest, surprise, magician_name, child_name, child_gender, trait)


def tell(params: StoryParams) -> World:
    world = World()
    mag = world.add(Entity(id=params.magician_name, kind="character", type="person", role="magician", label="the magician", traits=["kind", "calm"]))
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child", label="the child", traits=["little", params.trait]))
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    surprise = SURPRISES[params.surprise]
    flashback = FLASHBACKS[params.flashback if params.flashback in FLASHBACKS else "grandpa_story"]

    mag.memes["care"] += 1
    child.memes["wonder"] += 1
    world.say(f"One quiet afternoon, {child.id} found {mag.id}, a magician, in {setting.place}. {setting.detail}")
    world.say(f'{mag.id} smiled and said there was a small quest: "{quest.goal}."')
    world.say(f'The clue was simple: {quest.clue}, and the two of them looked around together.')

    world.para()
    child.memes["quest"] += 1
    mag.memes["helping"] += 1
    world.say(f"{child.id} wanted to help, and {mag.id} liked that. {child.id} carried {quest.item} carefully.")
    world.say(f"While they worked, {flashback.cue} brought back a memory. {flashback.memory}. {flashback.lesson}.")

    world.para()
    world.facts["flashback_used"] = True
    propagate(world, narrate=False)
    world.say(f"Then came a surprise: {surprise.reveal}. {surprise.gift} made {child.id} look up with {surprise.feeling} eyes.")
    world.say(f'{mag.id} laughed softly and finished the little quest. {quest.finish}')
    world.say(f"At the end of the day, the magician and the child sat together, sharing the quiet surprise and the solved quest like an ordinary, happy moment.")
    world.facts.update(
        magician=mag,
        child=child,
        setting=setting,
        quest=quest,
        surprise=surprise,
        flashback=flashback,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a young child that includes the word "magician" and ends with a small surprise.',
        f"Tell a gentle story where {f['magician'].id}, a magician, helps {f['child'].id} on a tiny quest in {f['setting'].place}.",
        f"Write a cozy story with a flashback that helps solve a simple quest and includes a pleasant surprise.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    mag = f["magician"]
    child = f["child"]
    quest = f["quest"]
    surprise = f["surprise"]
    flashback = f["flashback"]
    return [
        ("Who is the story about?", f"It is about {child.id} and {mag.id}, a magician who spent a quiet day helping with a small quest."),
        ("What was the quest?", f"They were trying to {quest.goal}. The whole point of the walk was to finish that one small job together."),
        ("What flashback did the magician remember?", f"{mag.id} remembered {flashback.cue}. That memory helped because it taught {flashback.lesson}."),
        ("What was the surprise?", f"The surprise was that {surprise.reveal}. It turned the ending into a warm, happy moment after the quest was done."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does a magician do?", "A magician performs tricks and surprises, often using practice, timing, and careful hands to make something feel magical."),
        ("What is a flashback in a story?", "A flashback is a memory from an earlier time that the story shows again so the character can learn from it."),
        ("What is a quest?", "A quest is a small goal or errand a character tries to finish, like finding something or delivering a note."),
        ("Why can a surprise make a story feel special?", "A surprise can make a normal day feel extra bright because the characters get an unexpected happy moment."),
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    for fid in FLASHBACKS:
        lines.append(asp.fact("flashback", fid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, Q, U) :- setting(S), quest(Q), surprise(U).
"""

def asp_facts() -> str:
    return valid_asp_facts()

def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in the gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, quest=None, surprise=None, flashback=None, magician=None, child=None, gender=None), random.Random(7)))
        _ = sample.story
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    else:
        print("OK: generation smoke test passed.")
    return rc

def explain_rejection() -> str:
    return "(No story: that combination does not give a believable small quest with a real surprise.)"

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        curated = [
            StoryParams("kitchen", "lost_coin", "music_box", "Milo", "Lena", "girl", "curious"),
            StoryParams("garden", "birthday_note", "cookie_plate", "Nina", "Theo", "boy", "gentle"),
            StoryParams("porch", "tiny_plant", "star_card", "Owen", "Rosa", "girl", "thoughtful"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
