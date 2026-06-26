#!/usr/bin/env python3
"""
storyworlds/worlds/wag_quest_friendship_bedtime_story.py
========================================================

A small bedtime-style story world about a gentle quest, a wagging tail, and
friendship that helps everybody feel safe at night.

The seed idea:
- At bedtime, a child and a dog notice that a little friend has lost a moon-shaped
  night charm.
- They go on a tiny quest through the quiet house to find it.
- The dog's wagging tail helps lead the way.
- When the charm is found, the friend can sleep, and the group ends the night
  warm and calm together.

This script follows the storyworld contract:
- self-contained stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- --verify, --asp, --show-asp, --json, --qa, --trace, --all, --seed, -n support
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
    room: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = True
    rooms: tuple[str, ...] = ("hall", "stairs", "bedroom")
    affords: set[str] = field(default_factory=set)


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    room: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    kind: str
    tail_wag: float
    clues: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_log: list[str] = []

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
    place: str
    quest: str
    friend: str
    helper: str
    child: str
    seed: Optional[int] = None


SETTINGS = {
    "house": Setting(place="the house", indoors=True, rooms=("hall", "stairs", "bedroom", "rug"), affords={"search"}),
    "cottage": Setting(place="the little cottage", indoors=True, rooms=("kitchen", "hall", "nursery"), affords={"search"}),
}

QUESTS = {
    "moon-charm": QuestItem(
        id="moon-charm",
        label="moon charm",
        phrase="a tiny moon-shaped charm for bedtime",
        room="under the rug",
        keyword="moon",
        tags={"moon", "night", "sleep"},
    ),
    "pillow-star": QuestItem(
        id="pillow-star",
        label="pillow star",
        phrase="a soft star tucked into a pillow",
        room="near the bed",
        keyword="star",
        tags={"star", "sleep", "night"},
    ),
    "dream-bell": QuestItem(
        id="dream-bell",
        label="dream bell",
        phrase="a little bell that makes sleepy songs",
        room="by the stairs",
        keyword="bell",
        tags={"bell", "night", "sleep"},
    ),
}

HELPERS = {
    "dog": Helper(id="dog", label="a small dog", kind="dog", tail_wag=1.0, clues={"sniff", "wag"}),
    "cat": Helper(id="cat", label="a sleepy cat", kind="cat", tail_wag=0.0, clues={"purr"}),
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Pippa", "Mabel", "Etta"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Eli", "Noah", "Bram"]
FRIENDS = ["a shy rabbit", "a little teddy bear", "a tiny mouse", "a moon-faced doll"]
TRAITS = ["gentle", "curious", "kind", "patient", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for q in QUESTS:
            for helper in HELPERS:
                combos.append((place, q, helper))
    return combos


def prize_at_risk(quest: QuestItem) -> bool:
    return quest.keyword in {"moon", "star", "bell"}


def select_helper(quest: QuestItem, helper: Helper) -> bool:
    return helper.kind == "dog" or "wag" in helper.clues


def explain_rejection(quest: QuestItem, helper: Helper) -> str:
    return (
        f"(No story: this quest needs a helper who can offer a wagging, reassuring clue. "
        f"{helper.label} is not a good fit for a bedtime search for {quest.label}.)"
    )


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_wag_clue(world: World) -> list[str]:
    out = []
    child = world.get("child")
    helper = world.get("helper")
    if helper.memes.get("wag", 0) >= THRESHOLD and child.memes.get("worry", 0) >= THRESHOLD:
        sig = ("wag_clue",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["hope"] = child.memes.get("hope", 0) + 1
            out.append("The wagging tail made the room feel less scary.")
    return out


def _r_found(world: World) -> list[str]:
    child = world.get("child")
    item = world.get("quest_item")
    if child.meters.get("search", 0) >= THRESHOLD and item.meters.get("found", 0) >= THRESHOLD:
        sig = ("found",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["joy"] = child.memes.get("joy", 0) + 1
            return ["__found__"]
    return []


RULES = [Rule("wag_clue", _r_wag_clue), Rule("found", _r_found)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__found__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, quest: QuestItem, helper_def: Helper, child_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type="child", label=child_name))
    friend = world.add(Entity(id="friend", kind="character", type="friend", label="their friend"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_def.kind, label=helper_def.label))
    item = world.add(Entity(id="quest_item", kind="thing", type=quest.label, label=quest.label, phrase=quest.phrase, room=quest.room))
    child.memes["worry"] = 1.0
    friend.memes["sleepy"] = 1.0
    helper.memes["wag"] = 1.0 if helper_def.kind == "dog" else 0.0

    world.say(f"At bedtime, {child_name} noticed that {friend.label} could not find {quest.phrase}.")
    world.say(f"So {child_name}, {friend.label}, and {helper.label} began a tiny quest through {setting.place}.")
    world.para()

    world.say(f"They looked in the hall, then the stairs, and then the bedroom.")
    world.say(f"{helper.label.capitalize()} kept {('wagging its tail' if helper_def.kind == 'dog' else 'walking softly')} as if it knew a secret.")
    child.meters["search"] = 1.0
    propagate(world, narrate=True)
    world.para()

    item.meters["found"] = 1.0
    world.say(f"At last, {child_name} found the {quest.label} {quest.room}.")
    propagate(world, narrate=True)

    world.say(f"{friend.label} smiled and held the little charm close.")
    world.say(f"Then the three friends climbed into bed, and the room felt warm and quiet.")
    world.say(f"The wagging, the searching, and the friendship had turned the night into a gentle ending.")

    world.facts.update(
        child=child,
        friend=friend,
        helper=helper,
        quest_item=item,
        setting=setting,
        quest=quest,
        helper_def=helper_def,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    quest = f["quest"]
    return [
        f"Write a bedtime story about {child.label}, a wagging dog, and a small quest to find a lost {quest.label}.",
        f"Tell a gentle story where friendship helps {child.label} search the house and bring bedtime peace back.",
        f"Write a calm children's story that includes a wagging tail, a tiny quest, and a happy sleep at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    helper = f["helper"]
    quest = f["quest"]
    setting = f["setting"]

    return [
        QAItem(
            question=f"What did {child.label} and the others search for at bedtime?",
            answer=f"They searched for the {quest.label}, a little bedtime treasure that their friend had lost.",
        ),
        QAItem(
            question=f"Who helped lead the quest through {setting.place}?",
            answer=f"{helper.label.capitalize()} helped lead the quest, and its wagging tail made the search feel hopeful.",
        ),
        QAItem(
            question=f"Why did the friends feel better when the {quest.label} was found?",
            answer=f"{friend.label} could hold the {quest.label} close again, so bedtime felt safe, calm, and ready for sleep.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "wag": (
        "What does it mean when a dog wags its tail?",
        "When a dog wags its tail, it often means the dog feels happy, excited, or friendly.",
    ),
    "moon": (
        "What is the moon?",
        "The moon is the bright round shape we see in the night sky.",
    ),
    "sleep": (
        "Why do children go to bed at night?",
        "Children go to bed at night so their bodies and minds can rest and get ready for a new day.",
    ),
    "friendship": (
        "What is friendship?",
        "Friendship is when people care for each other, help each other, and enjoy being together.",
    ),
    "quest": (
        "What is a quest?",
        "A quest is a search or adventure to find something important or do a helpful job.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["quest"].tags)
    tags.add("wag")
    tags.add("friendship")
    tags.add("quest")
    out = []
    for tag in ["wag", "moon", "sleep", "friendship", "quest"]:
        if tag in tags and tag in WORLD_KNOWLEDGE:
            q, a = WORLD_KNOWLEDGE[tag]
            out.append(QAItem(question=q, answer=a))
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
        if e.room:
            bits.append(f"room={e.room}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="house", quest="moon-charm", friend="rabbit", helper="dog", child="Mia"),
    StoryParams(place="cottage", quest="pillow-star", friend="teddy", helper="dog", child="Owen"),
    StoryParams(place="house", quest="dream-bell", friend="mouse", helper="cat", child="Nora"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: a gentle quest, friendship, and a wagging tail.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child")
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
    if args.quest and args.helper:
        q = QUESTS[args.quest]
        h = HELPERS[args.helper]
        if not select_helper(q, h):
            raise StoryError(explain_rejection(q, h))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid bedtime story combination matches the given options.)")
    place, quest, helper = rng.choice(sorted(combos))
    child = args.child or rng.choice(GIRL_NAMES + BOY_NAMES)
    return StoryParams(place=place, quest=quest, friend=rng.choice(FRIENDS), helper=helper, child=child)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUESTS[params.quest], HELPERS[params.helper], params.child)
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


ASP_RULES = r"""
quest_valid(P,Q,H) :- setting(P), quest(Q), helper(H).
wag_helper(H) :- helper(H), waggy(H).
friendship_story(P,Q,H) :- quest_valid(P,Q,H), wag_helper(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
        if prize_at_risk(QUESTS[qid]):
            lines.append(asp.fact("at_risk", qid))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        if h.kind == "dog" or "wag" in h.clues:
            lines.append(asp.fact("waggy", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show quest_valid/3."))
    return sorted(set(asp.atoms(model, "quest_valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show quest_valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible bedtime quest combos")
        for t in asp_valid_combos():
            print("  ", t)
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
            header = f"### {p.child}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
