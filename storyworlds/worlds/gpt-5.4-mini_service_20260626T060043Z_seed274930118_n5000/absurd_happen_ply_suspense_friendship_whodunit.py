#!/usr/bin/env python3
"""
Standalone storyworld: an absurd little whodunit with friendship, suspense,
and a clean resolution.

Seed premise:
A child detective notices something strange in a small house. A favorite
object has gone missing, the clues look a little absurd, and a friend helps
them follow the trail. The mystery turns on a simple, believable reveal.

The domain is intentionally small:
- one setting
- a few typed entities
- a single missing object
- clue-driven suspicion
- a friendship beat that helps solve the case

The world model uses meters for physical state and memes for emotional state.
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


# ---------------------------------------------------------------------------
# Core data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
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
    place: str = "the little house"
    rooms: list[str] = field(default_factory=lambda: ["kitchen", "hallway", "garden shed"])


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    culprit: str
    object: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "house": Setting(place="the little house", rooms=["kitchen", "hallway", "laundry nook"]),
    "cottage": Setting(place="the cottage", rooms=["porch", "kitchen", "attic stairs"]),
    "school": Setting(place="the school art room", rooms=["table", "sink corner", "supply shelf"]),
}

OBJECTS = {
    "clock": {"label": "toy clock", "phrase": "a tiny brass toy clock", "owner_word": "toy"},
    "cup": {"label": "blue cup", "phrase": "a blue cup with a star on it", "owner_word": "cup"},
    "ring": {"label": "silver ring", "phrase": "a shiny silver ring", "owner_word": "ring"},
}

CULPRITS = {
    "cat": {"type": "cat", "label": "the cat", "absurd_clue": "a paw print on the windowsill"},
    "dog": {"type": "dog", "label": "the dog", "absurd_clue": "a muddy nose print on a towel"},
    "mouse": {"type": "mouse", "label": "the mouse", "absurd_clue": "tiny nibble marks on a crumb trail"},
}

NAMES_GIRL = ["Mina", "Lila", "Nora", "Tia", "June", "Ava"]
NAMES_BOY = ["Owen", "Finn", "Theo", "Milo", "Leo", "Ezra"]
FRIEND_NAMES = ["Pip", "Bea", "Kit", "Rae", "Max", "Jules"]


# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        # clue suspicion
        for ent in list(world.entities.values()):
            if ent.kind != "character":
                continue
            if ent.memes.get("suspicion", 0) >= 1 and ("suspicion", ent.id) not in world.fired:
                world.fired.add(("suspicion", ent.id))
                out.append(f"{ent.id} looked more suspicious now.")
                changed = True

        # friendship helps calm fear
        for ent in list(world.entities.values()):
            if ent.kind != "character":
                continue
            if ent.memes.get("friendship", 0) >= 1 and ent.memes.get("fear", 0) > 0:
                sig = ("calm", ent.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                ent.memes["fear"] = max(0.0, ent.memes.get("fear", 0.0) - 1)
                ent.memes["trust"] = ent.memes.get("trust", 0.0) + 1
                out.append(f"{ent.id} felt braver with a friend beside {ent.pronoun('object')}.")
                changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def setup_suspense(world: World, hero: Entity, friend: Entity, missing: Entity) -> None:
    hero.memes["curiosity"] = 1
    hero.memes["suspicion"] = 1
    hero.memes["fear"] = 1
    world.say(
        f"{hero.id} noticed something odd in {world.setting.place}: "
        f"{missing.phrase} was gone."
    )
    world.say(
        f"The room felt quiet in an absurd way, like it was holding its breath."
    )
    world.say(
        f"{hero.id} and {friend.id} whispered together and began to ply the clues."
    )
    propagate(world, narrate=True)


def find_clue(world: World, culprit: Entity, clue_text: str) -> None:
    world.say(f"Then they found {clue_text}.")
    culprit.memes["nervous"] = culprit.memes.get("nervous", 0.0) + 1


def friendship_beat(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
    world.say(
        f"{friend.id} stayed close and helped {hero.id} think instead of panic."
    )
    world.say(
        f"That small kindness made the mystery feel less scary."
    )
    propagate(world, narrate=True)


def reveal(world: World, hero: Entity, friend: Entity, culprit: Entity, missing: Entity) -> None:
    culprit.memes["caught"] = 1
    missing.hidden_in = None
    missing.carried_by = hero.id
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["relief"] = 1
    world.say(
        f'At last, {hero.id} pointed to {culprit.label} and said, '
        f'"{culprit.label.capitalize()} had taken the {missing.label}!"'
    )
    world.say(
        f'But the answer was less grim than it looked: {culprit.label} had only '
        f'stolen the {missing.label} to hide it under {hero.pronoun("possessive")} '
        f'own blanket, where it had been waiting all along.'
    )
    world.say(
        f"{hero.id} laughed, {friend.id} laughed, and even the silly little culprit "
        f"looked relieved."
    )
    world.say(
        f"In the end, the missing {missing.label} was found, the absurd clues made sense, "
        f"and the friendship stayed brighter than the mystery."
    )


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def tell(setting: Setting, hero_name: str, friend_name: str, culprit_id: str, object_id: str) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type="girl" if hero_name in NAMES_GIRL else "boy",
        label=hero_name,
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type="girl" if friend_name in NAMES_GIRL else "boy",
        label=friend_name,
    ))
    culprit_cfg = CULPRITS[culprit_id]
    culprit = world.add(Entity(
        id=culprit_cfg["type"],
        kind="character",
        type=culprit_cfg["type"],
        label=culprit_cfg["label"],
    ))
    obj_cfg = OBJECTS[object_id]
    missing = world.add(Entity(
        id=object_id,
        kind="thing",
        type=object_id,
        label=obj_cfg["label"],
        phrase=obj_cfg["phrase"],
        owner=hero.id,
        hidden_in=culprit.id,
    ))

    world.say(
        f"{hero.id} was a small detective with a sharp eye and a very kind heart."
    )
    world.say(
        f"{friend.id} was {hero.id}'s best friend, and together they liked to solve little puzzles."
    )
    world.say(
        f"One morning, an absurd thing happened: {missing.phrase} had vanished."
    )
    world.para()
    setup_suspense(world, hero, friend, missing)
    find_clue(world, culprit, culprit_cfg["absurd_clue"])
    friendship_beat(world, hero, friend)
    world.say(
        f"They followed the clue to the {culprit.label_word if hasattr(culprit, 'label_word') else culprit.label} "
        f"and found the missing spot hiding behind a blanket."
    )
    world.para()
    reveal(world, hero, friend, culprit, missing)

    world.facts.update(
        hero=hero,
        friend=friend,
        culprit=culprit,
        missing=missing,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    missing = f["missing"]
    culprit = f["culprit"]
    return [
        f'Write a short whodunit for a child named {hero.id} and a friend named {friend.id}.',
        f"Tell a suspenseful but gentle mystery where {missing.phrase} goes missing and a clue feels absurd.",
        f"Write a friendship story that helps solve a mystery about {culprit.label} and the missing {missing.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    culprit = f["culprit"]
    missing = f["missing"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What was missing at {setting.place}?",
            answer=f"{hero.id}'s {missing.label} was missing from {setting.place}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} stay calm while they looked for the missing {missing.label}?",
            answer=f"{friend.id} stayed close and helped {hero.id} keep looking without feeling so scared.",
        ),
        QAItem(
            question=f"Who turned out to be behind the mystery?",
            answer=f"It was {culprit.label}, who had hidden the {missing.label} under a blanket.",
        ),
        QAItem(
            question=f"Why did the clues feel a little absurd?",
            answer=(
                f"The clues were funny-looking and strange, like {culprit.memes.get('absurd_clue', 'odd signs')} "
                f"leading them to the answer."
            ),
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a clue in a mystery?",
        answer="A clue is a small piece of information that helps you figure out what happened.",
    ),
    QAItem(
        question="Why do friends help each other?",
        answer="Friends help each other because kindness makes hard things feel easier and safer.",
    ),
    QAItem(
        question="What does suspense mean in a story?",
        answer="Suspense is the feeling of wondering what will happen next.",
    ),
    QAItem(
        question="What is a whodunit?",
        answer="A whodunit is a mystery story where readers try to figure out who did it.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts:
% setting(S). room(S,R). character(C). thing(T). missing(T). culprit(CU).
% hidden_in(T,CU). friend(F,H). hero(H). clue_kind(CK). clue(CK).
% suspicion(C) and friendship(C) are optional semantic tags.

mystery(H, T) :- hero(H), missing(T).
has_friendship(H, F) :- hero(H), friend(F, H).
absurd_case(H, T) :- mystery(H, T), has_friendship(H, _).
solved(H, T) :- mystery(H, T), culprit(CU), hidden_in(T, CU).

#show mystery/2.
#show has_friendship/2.
#show absurd_case/2.
#show solved/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for room in setting.rooms:
            lines.append(asp.fact("room", sid, room))
    for oid in OBJECTS:
        lines.append(asp.fact("thing", oid))
    for cid in CULPRITS:
        lines.append(asp.fact("culprit_kind", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery/2.\n#show has_friendship/2.\n#show absurd_case/2.\n#show solved/2."))
    shown = set((s.name, tuple(str(a) for a in s.arguments)) for s in model)
    if shown:
        print("OK: ASP program grounds and produces a model.")
        return 0
    print("MISMATCH: ASP program produced no model.")
    return 1


# ---------------------------------------------------------------------------
# Parameter handling
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small absurd whodunit storyworld.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--culprit", choices=CULPRITS.keys())
    ap.add_argument("--object", choices=OBJECTS.keys())
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS.keys()))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(NAMES_GIRL if hero_gender == "girl" else NAMES_BOY)
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    if friend_name == hero_name:
        friend_name = rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    culprit = args.culprit or rng.choice(list(CULPRITS.keys()))
    object_id = args.object or rng.choice(list(OBJECTS.keys()))
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        culprit=culprit,
        object=object_id,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        params.hero_name,
        params.friend_name,
        params.culprit,
        params.object,
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
        print(asp_program("#show mystery/2.\n#show has_friendship/2.\n#show absurd_case/2.\n#show solved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery/2.\n#show has_friendship/2.\n#show absurd_case/2.\n#show solved/2."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            for culprit in CULPRITS:
                for obj in OBJECTS:
                    p = StoryParams(
                        place=place,
                        hero_name="Mina",
                        hero_gender="girl",
                        friend_name="Pip",
                        friend_gender="boy",
                        culprit=culprit,
                        object=obj,
                    )
                    samples.append(generate(p))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
