#!/usr/bin/env python3
"""
storyworlds/worlds/hamper_twist_heartwarming.py
===============================================

A small heartwarming story world about a hamper, a little twist, and the kind
of family moment that turns a chore into care.

Premise
-------
A child loves a favorite softie, but the softie has fallen into a hamper with
laundry that is muddy and damp. The child wants it right away. A parent worries
it will get worse, and the story turns on a gentle compromise: take it out,
clean it carefully, and discover that the hamper is also holding a surprise
gesture of love.

The world is intentionally small and constraint-checked:
- a hamper can be full, tipped, tidy, or shared
- laundry can be clean or dirty
- a softie can be safe or in danger
- the parent can foresee the mess and offer a better way

The "twist" is that the hamper is not just a chore basket; it becomes the place
where a small surprise is found and care is shown.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    place: str
    twist: str
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str
    indoors: bool = True


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    plural: bool = False


@dataclass
class Twist:
    id: str
    cue: str
    reveal: str
    gift: str
    gentle_fix: str


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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "laundry_room": Setting(place="the laundry room", indoors=True),
    "bedroom": Setting(place="the bedroom", indoors=True),
    "hall": Setting(place="the hall closet", indoors=True),
}

TWISTS = {
    "surprise_note": Twist(
        id="surprise_note",
        cue="a soft rustle under the towels",
        reveal="a little note that said, 'Thanks for helping'",
        gift="a surprise note",
        gentle_fix="read the note together and fold the clothes carefully",
    ),
    "toy_return": Twist(
        id="toy_return",
        cue="something round and fluffy tucked under a shirt",
        reveal="the missing bunny the child had been looking for all morning",
        gift="a found toy",
        gentle_fix="wash it gently and dry it by the window",
    ),
    "helping_hand": Twist(
        id="helping_hand",
        cue="a ribbon peeking out from the corner of the hamper",
        reveal="a small tag that said the child's laundry helper badge was ready",
        gift="a helper badge",
        gentle_fix="pin it to the child's shirt after the clothes were sorted",
    ),
}

PRIZE = Prize(
    label="softie",
    phrase="a favorite soft blue bunny",
    type="bunny",
    plural=False,
)

GIRL_NAMES = ["Mia", "Nora", "Lena", "Ivy", "Ava", "Zoe"]
BOY_NAMES = ["Ben", "Leo", "Owen", "Finn", "Max", "Theo"]
TRAITS = ["careful", "curious", "gentle", "busy", "helpful", "spirited"]


def hamper_is_risky(world: World, child: Entity, softie: Entity) -> bool:
    return child.memes.get("wants_softie", 0) >= THRESHOLD and softie.meters.get("dirty", 0) >= THRESHOLD


def select_gentle_fix(twist: Twist) -> bool:
    return True


def predict_mess(world: World, child: Entity, softie: Entity) -> dict:
    sim = world.copy()
    sim.get(child.id).memes["grab"] = 1
    sim.get(softie.id).meters["dirty"] += 1
    return {"soiled": bool(sim.get(softie.id).meters["dirty"] >= THRESHOLD)}


def _narrate_begin(world: World, child: Entity, parent: Entity, softie: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.type} who liked keeping things neat, "
        f"especially {child.pronoun('possessive')} {softie.label}."
    )
    world.say(
        f"One afternoon, {child.id} found {child.pronoun('possessive')} {softie.label} "
        f"near {child.pronoun('possessive')} {world.setting.place} hamper."
    )


def _narrate_worry(world: World, child: Entity, parent: Entity, softie: Entity, twist: Twist) -> None:
    child.memes["wants_softie"] = 1
    softie.meters["dirty"] = 1
    world.say(
        f"{child.id} wanted to pull {softie.it()} out right away, but "
        f"{parent.pronoun('possessive')} {parent.type} looked worried."
    )
    if predict_mess(world, child, softie)["soiled"]:
        world.say(
            f"\"If you tug too fast, {softie.it()} could get even messier,\" "
            f"{parent.pronoun('subject')} said. \"Let's do it the gentle way.\""
        )


def _narrate_twist(world: World, child: Entity, parent: Entity, twist: Twist) -> None:
    world.say(
        f"They lifted the towels and heard {twist.cue}."
    )
    world.say(
        f"Inside the hamper, they found {twist.reveal}."
    )
    world.say(
        f"{child.id} smiled, because the hamper was not just a pile of laundry after all."
    )


def _narrate_fix(world: World, child: Entity, parent: Entity, softie: Entity, twist: Twist) -> None:
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    child.memes["love"] = child.memes.get("love", 0) + 1
    child.meters["helping"] = child.meters.get("helping", 0) + 1
    softie.meters["dirty"] = 0
    world.say(
        f"{parent.id} smiled and said they could {twist.gentle_fix}. "
        f"{child.id} helped at once."
    )
    world.say(
        f"Soon {softie.it()} was clean, the hamper was neatly sorted, and "
        f"{child.id} felt proud for helping instead of hurrying."
    )


def tell(setting: Setting, twist: Twist, name: str, gender: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    softie = world.add(Entity(
        id="Softie",
        type=PRIZE.type,
        label=PRIZE.label,
        phrase=PRIZE.phrase,
        owner=child.id,
        caretaker=parent.id,
    ))

    world.say(
        f"{child.id} lived with {child.pronoun('possessive')} {parent.label} in {setting.place}."
    )
    world.say(
        f"{child.id} loved {child.pronoun('possessive')} {softie.label}, especially when the day felt busy."
    )
    world.para()
    _narrate_begin(world, child, parent, softie)
    _narrate_worry(world, child, parent, softie, twist)
    world.para()
    _narrate_twist(world, child, parent, twist)
    _narrate_fix(world, child, parent, softie, twist)

    world.facts.update(
        child=child,
        parent=parent,
        softie=softie,
        twist=twist,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    twist = f["twist"]
    return [
        f'Write a short heartwarming story for a young child that includes the word "hamper".',
        f"Tell a gentle story where {child.id} finds something surprising in a hamper and learns to help kindly.",
        f'Write a simple story with a twist ending where a hamper leads to a warm family moment.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    twist = f["twist"]
    softie = f["softie"]
    return [
        QAItem(
            question=f"Who found the softie near the hamper?",
            answer=f"{child.id} found {softie.phrase} near the hamper.",
        ),
        QAItem(
            question=f"Why did {parent.id} want {child.id} to be gentle?",
            answer=f"{parent.id} did not want {softie.it()} to get more messy, so {parent.pronoun('subject')} asked for a gentle way.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that inside the hamper they found {twist.reveal}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {softie.it()} clean, the hamper sorted, and {child.id} feeling proud for helping.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hamper for?",
            answer="A hamper is a basket or bin where people put laundry before they wash it.",
        ),
        QAItem(
            question="Why should dirty laundry be sorted?",
            answer="Sorting laundry helps keep different clothes together and makes washing easier.",
        ),
        QAItem(
            question="Why is it kind to help with chores?",
            answer="Helping with chores shows care for the people in the family and makes the home nicer for everyone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:9}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
risky_child(C,S) :- wants_softie(C), dirty(S).
has_twist(T) :- twist(T).
good_end(C,S) :- risky_child(C,S), has_twist(T), gentle_fix(T).
story_ok(C,S,T) :- good_end(C,S), twist(T).
#show story_ok/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("wants_softie", "child"))
    lines.append(asp.fact("dirty", "softie"))
    lines.append(asp.fact("twist", "surprise"))
    lines.append(asp.fact("gentle_fix", "surprise"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/3."))
    ok = bool(asp.atoms(model, "story_ok"))
    if ok:
        print("OK: ASP gate accepts the story shape.")
        return 0
    print("MISMATCH: ASP gate rejected the story shape.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming hamper story world with a gentle twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "grandmother", "grandfather"])
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
    place = args.place or rng.choice(list(SETTINGS))
    twist = args.twist or rng.choice(list(TWISTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(name=name, gender=gender, parent=parent, place=place, twist=twist)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TWISTS[params.twist], params.name, params.gender, params.parent)
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
    StoryParams(name="Mia", gender="girl", parent="mother", place="laundry_room", twist="surprise_note"),
    StoryParams(name="Leo", gender="boy", parent="father", place="bedroom", twist="toy_return"),
    StoryParams(name="Nora", gender="girl", parent="grandmother", place="hall", twist="helping_hand"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_ok/3."))
        print(asp.atoms(model, "story_ok"))
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
            header = f"### {p.name}: {p.twist} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
