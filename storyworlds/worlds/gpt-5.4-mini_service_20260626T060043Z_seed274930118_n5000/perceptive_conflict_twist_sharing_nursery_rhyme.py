#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/perceptive_conflict_twist_sharing_nursery_rhyme.py
=============================================================================================================================

A tiny nursery-rhyme story world about a perceptive child, a sharing conflict,
and a twist that turns tugging into togetherness.

The world premise:
- A child has one beloved toy or treat.
- A friend wants to join in.
- The child first resists, then notices something important.
- The twist is that sharing makes the play better, not worse.

The stories are built from state changes, not from a frozen paragraph.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"shine": 0.0}
        if not self.memes:
            self.memes = {"want": 0.0, "conflict": 0.0, "perceptive": 0.0, "joy": 0.0, "care": 0.0}

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
    place: str = "the nursery"
    mood: str = "soft"
    affords: set[str] = field(default_factory=lambda: {"share", "play"})


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    shine: str
    shared_by_holding: bool = True


@dataclass
class StoryParams:
    place: str
    prize: str
    name: str
    gender: str
    companion: str
    companion_gender: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_shine(world: World) -> list[str]:
    out: list[str] = []
    prize = world.facts["prize_entity"]
    if prize.meters["shine"] >= THRESHOLD and ("shine", prize.id) not in world.fired:
        world.fired.add(("shine", prize.id))
        out.append(f"The {prize.label} gleamed bright as a little star.")
    return out


def _r_share_joy(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts["child"]
    friend = world.facts["friend"]
    prize = world.facts["prize_entity"]
    if friend.id in prize.shared_with and ("sharejoy", prize.id, friend.id) not in world.fired:
        world.fired.add(("sharejoy", prize.id, friend.id))
        child.memes["joy"] += 1
        friend.memes["joy"] += 1
        child.memes["conflict"] = 0.0
        out.append(f"Then both of them laughed, and the little room felt warm and light.")
    return out


CAUSAL_RULES = [
    ("shine", _r_shine),
    ("sharejoy", _r_share_joy),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def child_pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "girl":
        return "she", "her", "her"
    return "he", "him", "his"


def prize_at_risk() -> bool:
    return True


def valid_story_combo(place: str, prize_id: str, gender: str, companion_gender: str) -> bool:
    if place not in SETTINGS:
        return False
    if prize_id not in PRIZES:
        return False
    if gender not in {"girl", "boy"} or companion_gender not in {"girl", "boy"}:
        return False
    return prize_at_risk()


def build_nursery_line(name: str, trait: str, setting: Setting, prize: Prize) -> str:
    return f"Little {trait} {name} sat in {setting.place} with {prize.phrase} in {name}'s lap."


def introduce(world: World, child: Entity, prize: Entity) -> None:
    world.say(f"Little {child.type} {child.id} was {child.memes.get('trait_word', 'perceptive')} and bright.")
    world.say(f"{child.id} loved {prize.phrase} most of all.")


def want_and_worry(world: World, child: Entity, friend: Entity, prize: Entity) -> None:
    child.memes["want"] += 1
    friend.memes["want"] += 1
    world.say(f"{child.id} would not let go, and {friend.id} stood near with hopeful eyes.")
    world.say(f'"May I have a turn?" asked {friend.id}. "{child.id}, please share the {prize.label}."')


def conflict(world: World, child: Entity, friend: Entity, prize: Entity) -> None:
    child.memes["conflict"] += 1
    friend.memes["conflict"] += 1
    world.say(f"{child.id} held the {prize.label} close and said, 'No, no, mine, mine, mine.'")
    world.say(f"{friend.id} frowned, and the small room fell still.")


def twist(world: World, child: Entity, friend: Entity, prize: Entity) -> None:
    child.memes["perceptive"] += 1
    world.say(f"Then {child.id} looked again and saw {friend.id}'s droop and quiet chin.")
    world.say(f"{child.id} was perceptive and softly said, 'You may hold it with me.'")
    prize.shared_with.add(friend.id)


def resolve(world: World, child: Entity, friend: Entity, prize: Entity) -> None:
    child.memes["care"] += 1
    friend.memes["care"] += 1
    prize.meters["shine"] += 1
    propagate(world, narrate=True)
    world.say(f"{child.id} passed the {prize.label} over, and {friend.id} took it with a grin.")
    world.say(f"Side by side they played, and the sharing made the game twice as grand.")


def tell(setting: Setting, prize_cfg: Prize, child_name: str, child_gender: str,
         friend_name: str, friend_gender: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, memes={"want": 0.0, "conflict": 0.0, "perceptive": 0.0, "joy": 0.0, "care": 0.0, "trait_word": trait}))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=child.id))
    world.facts.update(child=child, friend=friend, prize_entity=prize, prize_cfg=prize_cfg, setting=setting)

    world.say(build_nursery_line(child.id, trait, setting, prize_cfg))
    world.say(f"In {setting.place}, the air was soft, and the day was slow and sweet.")
    world.para()
    introduce(world, child, prize)
    want_and_worry(world, child, friend, prize)
    conflict(world, child, friend, prize)
    world.para()
    twist(world, child, friend, prize)
    resolve(world, child, friend, prize)
    return world


SETTINGS = {
    "nursery": Setting(place="the nursery", mood="soft", affords={"share", "play"}),
    "playroom": Setting(place="the playroom", mood="warm", affords={"share", "play"}),
    "garden": Setting(place="the garden nook", mood="green", affords={"share", "play"}),
}

PRIZES = {
    "ball": Prize(label="ball", phrase="a bright little ball", type="toy", shine="gleam"),
    "book": Prize(label="book", phrase="a picture book with shiny pages", type="book", shine="gleam"),
    "bell": Prize(label="bell", phrase="a tiny silver bell", type="toy", shine="ring"),
    "blanket": Prize(label="blanket", phrase="a soft patchwork blanket", type="blanket", shine="glow"),
}

GIRL_NAMES = ["Mia", "Lily", "Rose", "Nora", "Ava", "Eve"]
BOY_NAMES = ["Ben", "Leo", "Max", "Theo", "Finn", "Sam"]
TRAITS = ["perceptive", "gentle", "bright-eyed", "curious", "kind"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, prize) for place in SETTINGS for prize in PRIZES]


@dataclass
class StoryParams:
    place: str
    prize: str
    name: str
    gender: str
    companion: str
    companion_gender: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    prize = f["prize_cfg"]
    return [
        f'Write a short nursery-rhyme story about a perceptive child named {child.id} who learns to share {prize.phrase}.',
        f"Tell a gentle conflict-and-twist story where {friend.id} asks for a turn and {child.id} discovers sharing is the happy answer.",
        f'Write a rhyming story for little children set in {world.setting.place} with "{prize.label}" and a kind share at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    prize = f["prize_entity"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {child.id}, a {child.type} who was {child.memes.get('trait_word', 'perceptive')} and learned to share {prize.phrase}.",
        ),
        QAItem(
            question=f"What did {friend.id} want at first?",
            answer=f"{friend.id} wanted a turn with the {prize.label}, because {friend.id} wanted to play too.",
        ),
        QAItem(
            question=f"What was the conflict in the story?",
            answer=f"The conflict was that {child.id} wanted to keep the {prize.label} close, but {friend.id} wished to share in the game.",
        ),
        QAItem(
            question=f"What was the twist?",
            answer=f"The twist was that {child.id} noticed how quiet {friend.id} looked and chose sharing instead of keeping the {prize.label} alone.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.id} and {friend.id} playing together, and the {prize.label} feeling even better because it was shared.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let someone else use something, enjoy something, or have a turn too.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is when people want different things and feel upset until they find a kinder way.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise change that makes the story go in a new direction.",
        ),
        QAItem(
            question="What does perceptive mean?",
            answer="Perceptive means noticing small clues and understanding what they show.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="nursery", prize="ball", name="Mia", gender="girl", companion="Ben", companion_gender="boy", trait="perceptive"),
    StoryParams(place="playroom", prize="book", name="Leo", gender="boy", companion="Rose", companion_gender="girl", trait="kind"),
    StoryParams(place="garden", prize="bell", name="Nora", gender="girl", companion="Sam", companion_gender="boy", trait="curious"),
]


def explain_rejection(place: str, prize: str) -> str:
    return f"(No story: {place!r} and {prize!r} do not form a reasonable sharing scene.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if prize.shared_by_holding:
            lines.append(asp.fact("can_share", pid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Prize) :- place(Place), prize(Prize), affords(Place, share), can_share(Prize).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about perceptive sharing and a conflict twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion")
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
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
    place = args.place or rng.choice(list(SETTINGS))
    prize = args.prize or rng.choice(list(PRIZES))
    gender = args.gender or rng.choice(["girl", "boy"])
    companion_gender = args.companion_gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion_pool = GIRL_NAMES if companion_gender == "girl" else BOY_NAMES
    companion = args.companion or rng.choice([n for n in companion_pool if n != name] or companion_pool)
    trait = args.trait or rng.choice(TRAITS)
    if not valid_combos():
        raise StoryError("(No valid stories exist.)")
    return StoryParams(place=place, prize=prize, name=name, gender=gender, companion=companion, companion_gender=companion_gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        PRIZES[params.prize],
        params.name,
        params.gender,
        params.companion,
        params.companion_gender,
        params.trait,
    )
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
        print(f"{len(asp_valid_combos())} compatible (place, prize) combos:\n")
        for place, prize in asp_valid_combos():
            print(f"  {place:10} {prize:8}")
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
            header = f"### {p.name}: {p.prize} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
