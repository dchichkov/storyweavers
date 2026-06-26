#!/usr/bin/env python3
"""
storyworlds/worlds/humbug_moral_splash_pad_friendship_humor_mystery.py
======================================================================

A standalone story world about a mystery at the splash pad.

Seed inspiration:
- A child story with a little mystery.
- A grumbly "humbug" character or mood.
- A moral that becomes clear through friendship and humor.
- A splash pad setting with water, guessing, and a small turn.

This world generates short, child-facing mystery stories where friends notice a
strange splash-pad problem, laugh together, solve it, and end with a clear
moral image.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the splash pad"
    affords: set[str] = field(default_factory=set)


@dataclass
class MysteryItem:
    id: str
    label: str
    phrase: str
    clue: str
    truth: str
    kind: str = "thing"


@dataclass
class StoryParams:
    name1: str
    name2: str
    age1: str
    age2: str
    gender1: str
    gender2: str
    parent: str
    mystery: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather: str = "sunny"

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_humor(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes.get("humor", 0) >= THRESHOLD and not ent.meters.get("laughed", 0):
            sig = ("laugh", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.meters["laughed"] = 1
            out.append(f"{ent.id} giggled at the silly clue.")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    a = world.facts.get("friend1")
    b = world.facts.get("friend2")
    if not a or not b:
        return out
    e1 = world.get(a.id)
    e2 = world.get(b.id)
    if e1.memes.get("helped", 0) >= THRESHOLD and e2.memes.get("helped", 0) >= THRESHOLD:
        sig = ("friendship", e1.id, e2.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        e1.memes["friendship"] = e1.memes.get("friendship", 0) + 1
        e2.memes["friendship"] = e2.memes.get("friendship", 0) + 1
        out.append("Their friendship felt warmer than the sun on the water.")
    return out


def _r_moral(world: World) -> list[str]:
    if world.facts.get("solved") and not world.facts.get("moral_spoken"):
        world.facts["moral_spoken"] = True
        return ["__moral__"]
    return []


CAUSAL_RULES = [
    Rule("humor", _r_humor),
    Rule("friendship", _r_friendship),
    Rule("moral", _r_moral),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                for line in got:
                    if line != "__moral__":
                        produced.append(line)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mystery stories at the splash pad with friendship, humor, and a moral."
    )
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--age1", choices=["little", "young"])
    ap.add_argument("--age2", choices=["little", "young"])
    ap.add_argument("--gender1", choices=["girl", "boy"])
    ap.add_argument("--gender2", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    if mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    return StoryParams(
        name1=args.name1 or rng.choice(NAMES[args.gender1 or rng.choice(["girl", "boy"])]),
        name2=args.name2 or rng.choice(NAMES[args.gender2 or rng.choice(["girl", "boy"])]),
        age1=args.age1 or rng.choice(["little", "young"]),
        age2=args.age2 or rng.choice(["little", "young"]),
        gender1=args.gender1 or rng.choice(["girl", "boy"]),
        gender2=args.gender2 or rng.choice(["girl", "boy"]),
        parent=args.parent or rng.choice(["mother", "father"]),
        mystery=mystery,
    )


def make_story_world(params: StoryParams) -> World:
    world = World(SPLASH_PAD)
    hero = world.add(Entity(id="hero", kind="character", type=params.gender1, traits=[params.age1, "curious"]))
    friend = world.add(Entity(id="friend", kind="character", type=params.gender2, traits=[params.age2, "funny"]))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent))
    mystery = MYSTERIES[params.mystery]
    clue = world.add(Entity(id="clue", type="thing", label=mystery.label, phrase=mystery.phrase))
    world.facts.update(hero=hero, friend1=hero, friend2=friend, parent=parent, mystery=mystery, clue=clue)
    return world


def tell(world: World, params: StoryParams) -> World:
    hero = world.get("hero")
    friend = world.get("friend")
    parent = world.get("parent")
    mystery = world.facts["mystery"]

    hero.memes["curiosity"] = 1
    friend.memes["humor"] = 1

    world.say(
        f"At {world.setting.place}, {params.name1} and {params.name2} were chasing the spray and laughing in the sun."
    )
    world.say(
        f"Then they found {mystery.phrase}. It looked odd, because it did not match the rest of the neat water jets."
    )
    world.para()

    world.say(
        f"{params.name1} leaned in and said, \"Huh, that is a funny little humbug.\""
    )
    world.say(
        f"{params.name2} sniffed the air, listened, and pointed at {mystery.clue}. \"Maybe it is a clue,\" {friend.pronoun()} said."
    )
    parent.memes["worry"] = 1
    world.say(
        f"{params.parent.capitalize()} smiled, but also wondered why the splash pad had gone quiet near the corner."
    )
    world.para()

    hero.memes["humor"] = 1
    friend.memes["helped"] = 1
    hero.memes["helped"] = 1
    world.say(
        f"To test the mystery, the two friends followed the dripping trail together."
    )
    if mystery.id == "lost_sandal":
        world.say(
            f"They found a tiny sandal stuck behind a nozzle, and that was why the water had been splashing sideways."
        )
    elif mystery.id == "stuck_button":
        world.say(
            f"They found a stuck button on the fountain box, and a gentle push made the spray pop back on."
        )
    elif mystery.id == "drift_leaf":
        world.say(
            f"They found a leaf curled over a drain, and lifting it away let the water sing again."
        )
    else:
        world.say(
            f"They found a squeaky toy hiding under a bench, and once it was moved, the water rhythm made sense."
        )
    propagate(world, narrate=True)
    world.para()

    world.facts["solved"] = True
    propagate(world, narrate=True)
    world.say(
        f"{params.name1} and {params.name2} laughed because the big humbug was only a small mix-up."
    )
    world.say(
        f"{params.parent.capitalize()} said, \"The best way to solve a puzzle is to stay kind, stay curious, and help each other.\""
    )
    world.say(
        f"So the splash pad sparkled again, and the two friends ran through the water side by side, smiling at the mystery they had solved together."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    m = world.facts["mystery"]
    h = world.facts["hero"]
    f = world.facts["friend2"]
    return [
        f"Write a short mystery story for young children set at the splash pad, with {m.label} as the clue and a kind ending.",
        f"Tell a story where {h.id} and {f.id} solve a small humbug at the splash pad using friendship and humor.",
        f"Create a gentle splash-pad mystery with a clear moral about helping friends and staying curious.",
    ]


def story_qa(world: World) -> list[QAItem]:
    m = world.facts["mystery"]
    hero = world.facts["hero"]
    friend = world.facts["friend2"]
    parent = world.facts["parent"]
    return [
        QAItem(
            question=f"Where did {hero.id} and {friend.id} find the strange clue?",
            answer=f"They found it at {world.setting.place}, where the water play turned into a small mystery.",
        ),
        QAItem(
            question=f"What made the story feel a little like a humbug at first?",
            answer=f"The humbug feeling came from the odd clue: {m.phrase}. It looked out of place and made everyone pause.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} solve the mystery?",
            answer=f"They stayed together, followed the dripping trail, and used their curiosity and teamwork to find the cause.",
        ),
        QAItem(
            question=f"What moral did {parent.id} share at the end?",
            answer="The moral was that kind friends solve puzzles better when they stay curious, help each other, and laugh without being mean.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a splash pad?",
            answer="A splash pad is a play place with water sprays and fountains where children can run, splash, and stay cool.",
        ),
        QAItem(
            question="What does humor do in a story?",
            answer="Humor adds silly or funny moments that make the story feel playful and light.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and enjoy being together.",
        ),
        QAItem(
            question="What is a moral in a story?",
            answer="A moral is the lesson the story wants to teach, like being kind, honest, or helpful.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.kind}/{e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


SPLASH_PAD = Setting(place="the splash pad", affords={"splash", "spray"})

MYSTERIES = {
    "lost_sandal": MysteryItem(
        id="lost_sandal",
        label="a tiny sandal",
        phrase="a tiny sandal lying near the drain",
        clue="little wet footprints",
        truth="a sandal was blocking the spray",
    ),
    "stuck_button": MysteryItem(
        id="stuck_button",
        label="a sticky button",
        phrase="a sticky button on the fountain box",
        clue="a soft clicking sound",
        truth="the button was stuck halfway down",
    ),
    "drift_leaf": MysteryItem(
        id="drift_leaf",
        label="a leaf",
        phrase="a leaf floating in the wrong corner",
        clue="a green leaf trail",
        truth="a leaf was covering the drain",
    ),
    "toy_whistle": MysteryItem(
        id="toy_whistle",
        label="a toy whistle",
        phrase="a toy whistle tucked under a bench",
        clue="a tiny whistle squeak",
        truth="a toy whistle was making the noise",
    ),
}

NAMES = {
    "girl": ["Mia", "Nora", "Lina", "Ava", "Zoe"],
    "boy": ["Ben", "Theo", "Max", "Leo", "Owen"],
}

CURATED = [
    StoryParams(name1="Mia", name2="Ben", age1="little", age2="young", gender1="girl", gender2="boy", parent="mother", mystery="lost_sandal"),
    StoryParams(name1="Nora", name2="Theo", age1="young", age2="little", gender1="girl", gender2="boy", parent="father", mystery="drift_leaf"),
    StoryParams(name1="Ava", name2="Max", age1="little", age2="little", gender1="girl", gender2="boy", parent="mother", mystery="stuck_button"),
    StoryParams(name1="Lina", name2="Owen", age1="young", age2="young", gender1="girl", gender2="boy", parent="father", mystery="toy_whistle"),
]


ASP_RULES = r"""
% A mystery is valid when the splash pad setting includes a clue, friendship,
% and humor are present, and the ending moral can be spoken after solving.
valid_story(P,M) :- place(P), mystery(M), has_friendship, has_humor, solvable(M).

solvable(M) :- clue(M,C), relevant_clue(M,C).
has_friendship :- friendship.
has_humor :- humor.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    lines.append(asp.fact("place", "splash_pad"))
    lines.append(asp.fact("friendship"))
    lines.append(asp.fact("humor"))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("relevant_clue", mid, m.clue))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(SPLASH_PAD.place, mid) for mid in MYSTERIES}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP gate matches Python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


def resolve_combo(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    world = make_story_world(params)
    world = tell(world, params)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid mystery stories:")
        for place, mid in stories:
            print(f"  {place}  {mid}")
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
                params = resolve_combo(args, random.Random(seed))
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
            header = f"### {p.name1} and {p.name2} at the splash pad"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
