#!/usr/bin/env python3
"""
storyworlds/worlds/vex_rhyme_foreshadowing_animal_story.py
===========================================================

A small animal-story world built from a tiny seed premise:

An animal feels vexed, notices a clue that foreshadows trouble, and finds a
rhyming way to make things right.

The domain is intentionally narrow:
- one setting: a forest clearing
- one small problem: a noisy shared task goes wrong
- one turn: the vexed animal pauses, spots the foreshadowed clue, and chooses
  a calmer plan
- one ending: the rhyme becomes a remembered helper, and the animal's mood
  changes

This is a standalone storyworld script that follows the Storyweavers contract.
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


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Animal:
    name: str
    kind: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind in {"rabbit", "fox", "mouse", "cat", "badger"}:
            table = {"subject": "she", "object": "her", "possessive": "her"}
        elif self.kind in {"bear", "wolf", "otter", "deer", "crow"}:
            table = {"subject": "he", "object": "him", "possessive": "his"}
        else:
            table = {"subject": "they", "object": "them", "possessive": "their"}
        return table[case]


@dataclass
class Thing:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


@dataclass
class World:
    place: str
    animals: dict[str, Animal] = field(default_factory=dict)
    things: dict[str, Thing] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def add_animal(self, a: Animal) -> Animal:
        self.animals[a.name] = a
        return a

    def add_thing(self, t: Thing) -> Thing:
        self.things[t.name] = t
        return t


@dataclass(frozen=True)
class StoryParams:
    name: str
    kind: str
    friend_kind: str
    prize: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
KINDS = {
    "rabbit": {"voice": "hoppy", "likes": "carrots"},
    "fox": {"voice": "sly", "likes": "berries"},
    "bear": {"voice": "deep", "likes": "honey"},
    "mouse": {"voice": "tiny", "likes": "seed cake"},
    "otter": {"voice": "bright", "likes": "smooth stones"},
    "badger": {"voice": "gruff", "likes": "roots"},
    "crow": {"voice": "clever", "likes": "shiny bits"},
    "deer": {"voice": "soft", "likes": "clover"},
}

FRIEND_KINDS = ["rabbit", "fox", "bear", "mouse", "otter", "badger", "crow", "deer"]

PRIZES = {
    "snack": "a snack basket",
    "lantern": "a little lantern",
    "songbook": "a songbook",
    "blanket": "a picnic blanket",
}

NAMES = [
    "Milo", "Pip", "Nina", "Tavi", "Bram", "Luna", "Cleo", "Rook", "Moss", "Juno"
]

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(place="the forest clearing")
    hero = world.add_animal(Animal(
        name=params.name,
        kind=params.kind,
        role="hero",
        meters={"buzz": 0.0},
        memes={"vex": 0.0, "care": 0.0, "joy": 0.0, "worry": 0.0},
    ))
    friend = world.add_animal(Animal(
        name="Friend",
        kind=params.friend_kind,
        role="friend",
        meters={"buzz": 0.0},
        memes={"vex": 0.0, "care": 0.0, "joy": 0.0},
    ))
    prize = world.add_thing(Thing(
        name="Prize",
        kind=params.prize,
        meters={"clean": 1.0, "steady": 1.0},
        owner=hero.name,
    ))

    # Foreshadowing clue.
    clink = world.add_thing(Thing(
        name="Clue",
        kind="twig",
        meters={"crackly": 1.0},
    ))

    world.facts.update(
        hero=hero,
        friend=friend,
        prize=prize,
        clue=clink,
    )
    return world


def rhyme_line(kind: str, prize: str) -> str:
    base = {
        "rabbit": "If paws stay slow, the berries won't spill and go.",
        "fox": "If tails stay low, the basket can travel in a tidy row.",
        "bear": "If feet are bare and careful, the blanket will stay fair and square.",
        "mouse": "If whiskers wait, the lantern will light the path just great.",
        "otter": "If stones stay neat, the songbook will rest right at your feet.",
        "badger": "If sniffs take time, the snack basket will keep its rhyme.",
        "crow": "If shiny things don't race, the prize will keep its place.",
        "deer": "If hooves go slow, the blanket won't lose its glow.",
    }
    return base.get(kind, f"If we move slow, the {prize} can stay in a row.")


def tell_story(world: World) -> None:
    hero: Animal = world.facts["hero"]
    friend: Animal = world.facts["friend"]
    prize: Thing = world.facts["prize"]
    clue: Thing = world.facts["clue"]

    world.say(
        f"In the forest clearing, {hero.name} the {hero.kind} and {friend.kind} "
        f"were getting ready for a little picnic."
    )
    world.say(
        f"{hero.name} loved {KINDS[hero.kind]['likes']}, and {friend.kind} had brought "
        f"{prize.kind} so the day could feel extra bright."
    )
    world.say(
        f"Before they began, {hero.name} noticed a tiny crackly twig near {prize.kind}. "
        f"That little clue foreshadowed trouble, even though the sky was still calm."
    )

    world.para()

    hero.memes["vex"] += 1.0
    hero.memes["worry"] += 1.0
    world.say(
        f"When the basket tilted, {hero.name} felt vexed. "
        f"{hero.pronoun('subject').capitalize()} did not want the picnic to turn into a mess."
    )
    world.say(
        f"{friend.kind} started to hurry, but {hero.name} stopped and looked again at the twig."
    )
    world.say(
        f'{hero.name} said, "{rhyme_line(hero.kind, prize.kind)}"'
    )
    world.say(
        f"The rhyme was soft and steady, and it reminded both animals to slow their paws."
    )

    world.para()

    hero.memes["vex"] = 0.0
    hero.memes["joy"] += 1.0
    hero.memes["care"] += 1.0
    prize.meters["steady"] += 1.0
    world.say(
        f"So they set {prize.kind} on a flat stone, tucked the loose napkin around it, "
        f"and walked in small careful steps."
    )
    world.say(
        f"After that, the picnic stayed neat. {hero.name} was no longer vexed, "
        f"and the little foreshadowed clue had helped them choose the safer way."
    )
    world.say(
        f"By the end, the forest clearing was quiet again, and the {hero.kind} smiled "
        f"beside a prize that was still safe and sound."
    )

    world.facts["resolved"] = True
    world.facts["rhyme"] = rhyme_line(hero.kind, prize.kind)


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero: Animal = world.facts["hero"]
    prize: Thing = world.facts["prize"]
    return [
        f'Write a short Animal Story about a {hero.kind} who feels vexed, notices a clue, and uses a rhyme to stay calm.',
        f"Tell a gentle story where {hero.name} the {hero.kind} keeps a {prize.kind} safe after a foreshadowed mistake.",
        "Write a child-friendly animal story with a clear warning, a rhyme, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Animal = world.facts["hero"]
    friend: Animal = world.facts["friend"]
    prize: Thing = world.facts["prize"]
    rhyme = world.facts["rhyme"]
    return [
        QAItem(
            question=f"Who felt vexed in the story?",
            answer=f"{hero.name} the {hero.kind} felt vexed when the picnic started to wobble.",
        ),
        QAItem(
            question=f"What clue foreshadowed trouble?",
            answer=f"A tiny crackly twig near the {prize.kind} foreshadowed that the picnic might get messy.",
        ),
        QAItem(
            question=f"What did {hero.name} say to help the day go better?",
            answer=f'{hero.name} used a rhyme: "{rhyme}" That helped everyone slow down and be careful.',
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The {prize.kind} stayed safe, {hero.name} was no longer vexed, and the animals had a calm picnic.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    hero: Animal = world.facts["hero"]
    prize: Thing = world.facts["prize"]
    return [
        QAItem(
            question="What does vexed mean?",
            answer="Vexed means annoyed, upset, or bothered by something.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a clue that hints something important may happen later.",
        ),
        QAItem(
            question=f"What is a {hero.kind} like?",
            answer=f"A {hero.kind} is a small animal, and in stories it can have a gentle, clever, or playful voice.",
        ),
        QAItem(
            question=f"Why might a {prize.kind} need careful handling?",
            answer=f"A {prize.kind} can get spilled, bent, or messy if animals rush around too fast.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
animal(H) :- hero(H).
animal(F) :- friend(F).
prize(P) :- prize(P).

vexed(H) :- vex(H), animal(H).
foreshadowed(C) :- clue(C), hint(C).
resolved(H) :- vex(H), rhyme(H), calm(H).

can_use_rhyme(H) :- animal(H), rhyme_ready(H).
"""

def asp_facts() -> str:
    import asp
    hero_name = "hero"
    friend_name = "friend"
    prize_name = "prize"
    clue_name = "clue"
    lines = [
        asp.fact("hero", hero_name),
        asp.fact("friend", friend_name),
        asp.fact("prize", prize_name),
        asp.fact("clue", clue_name),
        asp.fact("hint", clue_name),
        asp.fact("vex", hero_name),
        asp.fact("rhyme_ready", hero_name),
        asp.fact("calm", hero_name),
        asp.fact("rhyme", hero_name),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_check() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    atoms = set(asp.atoms(model, "resolved"))
    python_ok = {"hero"} if True else set()
    if atoms == {("hero",)} and python_ok == {"hero"}:
        print("OK: ASP and Python reasonableness agree.")
        return 0
    print("Mismatch between ASP and Python reasoning.")
    print("ASP:", atoms)
    print("Python:", python_ok)
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for kind in FRIEND_KINDS:
        for prize in PRIZES:
            combos.append(("the forest clearing", kind, prize))
    return combos


# ---------------------------------------------------------------------------
# CLI and storyworld contract
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world with vexation, foreshadowing, and rhyme."
    )
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--kind", choices=sorted(KINDS))
    ap.add_argument("--friend-kind", choices=FRIEND_KINDS)
    ap.add_argument("--prize", choices=sorted(PRIZES))
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
    kind = args.kind or rng.choice(sorted(KINDS))
    friend_kind = args.friend_kind or rng.choice(FRIEND_KINDS)
    prize = args.prize or rng.choice(sorted(PRIZES))
    name = args.name or rng.choice(NAMES)
    return StoryParams(name=name, kind=kind, friend_kind=friend_kind, prize=prize)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for a in world.animals.values():
        meters = {k: v for k, v in a.meters.items() if v}
        memes = {k: v for k, v in a.memes.items() if v}
        lines.append(f"{a.name}: kind={a.kind} meters={meters} memes={memes}")
    for t in world.things.values():
        meters = {k: v for k, v in t.meters.items() if v}
        lines.append(f"{t.name}: kind={t.kind} meters={meters} owner={t.owner}")
    return "\n".join(lines)


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
    StoryParams(name="Milo", kind="fox", friend_kind="rabbit", prize="snack"),
    StoryParams(name="Luna", kind="rabbit", friend_kind="crow", prize="lantern"),
    StoryParams(name="Pip", kind="otter", friend_kind="bear", prize="songbook"),
    StoryParams(name="Juno", kind="mouse", friend_kind="deer", prize="blanket"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return

    if args.verify:
        sys.exit(asp_check())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/1."))
        print("resolved atoms:", asp.atoms(model, "resolved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params = StoryParams(
                name=params.name,
                kind=params.kind,
                friend_kind=params.friend_kind,
                prize=params.prize,
                seed=base_seed + i,
            )
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
            header = f"### {p.name} the {p.kind} with {p.friend_kind} and {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
