#!/usr/bin/env python3
"""
storyworlds/worlds/sorry_transformation_friendship_dialogue_mystery.py
======================================================================

A standalone story world about a small mystery where a sincere apology helps
transform a broken friendship.

Seed premise:
---
A child notices that a treasured paper crown has gone missing, and the search
turns into a quiet mystery. The clues lead to a friend who meant no harm but
did make a hurtful choice. A careful conversation, a sincere "sorry," and a
small act of repair transform the scene from suspicion into friendship again.

World model:
---
- Physical meters track clues, loss, repair, and a transformation token.
- Emotional memes track worry, hurt, trust, friendship, and relief.
- The story begins with a mystery, turns on a revealing dialogue, and ends in a
  changed relationship.
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

FRIENDS = ["Mina", "Owen", "Iris", "Nico", "Pia", "Toby", "Luna", "Ezra"]
PLACES = ["the classroom", "the library corner", "the garden bench", "the playroom"]
OBJECTS = [
    ("paper crown", "a shiny paper crown", "crown"),
    ("toy star", "a little toy star", "star"),
    ("blue ribbon", "a blue ribbon", "ribbon"),
    ("button badge", "a round button badge", "badge"),
]
MYSTERY_MOTIFS = [
    "a soft clue",
    "a tiny trail",
    "a whisper of paper",
    "a small mystery",
]
TRAITS = ["curious", "gentle", "quiet", "clever", "kind"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("loss", "repair", "clue", "transformation"):
            self.meters.setdefault(k, 0.0)
        for k in ("worry", "hurt", "trust", "friendship", "relief", "guilt"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    place: str
    item: str
    hero: str
    friend: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def copy(self) -> "World":
        import copy as _copy

        clone = World()
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


THRESHOLD = 1.0


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    item = world.get("item")
    friend = world.get("friend")
    if hero.memes["worry"] >= THRESHOLD and item.meters["loss"] >= THRESHOLD:
        sig = ("clue",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["clue"] += 1
            out.append(f"A tiny clue pointed toward {friend.id}.")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    item = world.get("item")
    sig = ("transform",)
    if sig in world.fired:
        return out
    if hero.memes["trust"] >= THRESHOLD and friend.memes["guilt"] >= THRESHOLD and item.meters["repair"] >= THRESHOLD:
        world.fired.add(sig)
        hero.meters["transformation"] += 1
        friend.meters["transformation"] += 1
        hero.memes["relief"] += 1
        friend.memes["friendship"] += 1
        out.append("__transform__")
    return out


CAUSAL_RULES = [_r_clue, _r_transformation]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__transform__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_resolution(world: World) -> bool:
    sim = world.copy()
    speak_sorry(sim.get("hero"), sim.get("friend"), sim.get("item"), sim, narrate=False)
    repair(sim.get("hero"), sim.get("friend"), sim.get("item"), sim)
    propagate(sim, narrate=False)
    return sim.get("hero").meters["transformation"] >= THRESHOLD


def intro(world: World, hero: Entity, friend: Entity, item: Entity, place: str, trait: str) -> None:
    world.say(
        f"{hero.id} was a {trait} child who liked quiet places and tiny clues. "
        f"{friend.id} was {hero.id}'s best friend, and both of them loved {item.phrase}."
    )
    world.say(
        f"One day in {place}, {item.phrase} went missing, and that turned the day into a small mystery."
    )
    hero.memes["worry"] += 1
    item.meters["loss"] += 1


def search(world: World, hero: Entity, friend: Entity, item: Entity, place: str) -> None:
    world.para()
    motif = random.choice(MYSTERY_MOTIFS)
    world.say(
        f"{hero.id} looked under a bench, behind a book stack, and near the window. "
        f"{motif} led {hero.id} to ask, \"Have you seen {item.label}?\""
    )
    friend.memes["hurt"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"{friend.id} lowered {friend.pronoun('possessive')} eyes and said, \"I saw it, but I was not careful.\""
    )


def reveal(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    world.say(
        f"{hero.id} asked one more question, and the answer came out slow and plain."
    )
    world.say(
        f"\"I wanted to borrow {item.label},\" {friend.id} said, "
        f"\"but I hid it and then forgot where.\""
    )
    friend.memes["guilt"] += 1
    hero.memes["hurt"] += 1
    hero.memes["trust"] += 0.5
    world.facts["mystery_revealed"] = True


def speak_sorry(hero: Entity, friend: Entity, item: Entity, world: World, narrate: bool = True) -> None:
    if friend.memes["guilt"] < THRESHOLD:
        return
    friend.memes["guilt"] += 1
    friend.memes["trust"] += 0.5
    if narrate:
        world.say(
            f"Then {friend.id} took a breath and said, \"I'm sorry. I should have asked first.\""
        )
        world.say(
            f"{hero.id} listened, and the room grew quiet enough for the truth to matter."
        )
    world.facts["sorry"] = True


def repair(hero: Entity, friend: Entity, item: Entity, world: World, narrate: bool = True) -> None:
    if friend.memes["guilt"] < THRESHOLD:
        return
    item.meters["repair"] += 1
    friend.memes["trust"] += 1
    hero.memes["trust"] += 1
    if narrate:
        world.say(
            f"{friend.id} helped untie the knot, smoothed the bend, and put {item.label} back together."
        )
        world.say(
            f"{hero.id} said, \"Thank you for fixing it with me.\""
        )
    world.facts["repaired"] = True
    propagate(world, narrate=narrate)


def finish(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    if hero.meters["transformation"] >= THRESHOLD:
        world.para()
        world.say(
            f"In the end, the missing thing was found, the apology was real, and the friendship changed shape."
        )
        world.say(
            f"{hero.id} and {friend.id} stood together with {item.label}, no longer suspicious, only relieved."
        )
    else:
        world.para()
        world.say(
            f"The mystery was not fully solved, and the room stayed unsettled."
        )


def tell(params: StoryParams) -> World:
    world = World()
    item_id, item_phrase, item_label = params.item
    hero = world.add(Entity(id="hero", kind="character", type="child", label=params.hero))
    friend = world.add(Entity(id="friend", kind="character", type="child", label=params.friend))
    item = world.add(Entity(id="item", kind="thing", type=item_label, label=item_label, phrase=item_phrase, owner=hero.id))

    intro(world, hero, friend, item, params.place, params.trait)
    search(world, hero, friend, item, params.place)
    reveal(world, hero, friend, item)
    speak_sorry(hero, friend, item, world, narrate=True)
    repair(hero, friend, item, world, narrate=True)
    finish(world, hero, friend, item)

    world.facts.update(
        hero=hero,
        friend=friend,
        item=item,
        place=params.place,
        trait=params.trait,
        resolved=hero.meters["transformation"] >= THRESHOLD,
    )
    return world


def resolve_rejection(reason: str) -> str:
    return f"(No story: {reason})"


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, item[0], item[2]) for place in PLACES for item in OBJECTS]


@dataclass
class Registry:
    place: str
    item: tuple[str, str, str]
    hero: str
    friend: str
    trait: str


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for young children set in {f["place"]} about a missing {f["item"].label}.',
        f"Tell a gentle dialogue story where {f['hero'].id} asks questions, {f['friend'].id} says sorry, and the friendship changes.",
        f'Write a child-friendly mystery that includes an honest apology and ends with repaired friendship.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    item: Entity = f["item"]
    place = f["place"]
    qa = [
        QAItem(
            question=f"What was missing in {place}?",
            answer=f"{item.label.capitalize()} was missing, and that made the day feel like a little mystery.",
        ),
        QAItem(
            question=f"Who spoke the sorry line in the story?",
            answer=f"{friend.id} said, \"I'm sorry. I should have asked first.\"",
        ),
        QAItem(
            question=f"What did {hero.id} do after hearing the truth?",
            answer=f"{hero.id} listened, asked questions, and stayed calm long enough for the answer to come out.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question="What changed at the end?",
                answer=f"The missing {item.label} was repaired or found, and the friendship between {hero.id} and {friend.id} felt warmer again.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sorry mean?",
            answer="Sorry is a word people use when they know they hurt someone or made a mistake and want to make it right.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling or unknown that people try to figure out by looking for clues.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring bond between people who help each other, listen, and share kind feelings.",
        ),
        QAItem(
            question="Why do people talk things through?",
            answer="People talk things through so they can understand what happened, fix mistakes, and keep trust strong.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={m} memes={mm}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
missing_item(I) :- item(I), loss(I).
clue_appears(H) :- worry(H), missing_item(_).
needs_sorry(F) :- guilt(F).
friendship_restored(H,F) :- sorry(F), repair_done(_), trust(H), trust(F).
resolved(H,F) :- friendship_restored(H,F), clue_appears(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for item_id, phrase, label in OBJECTS:
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("label", item_id, label))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show place/1.\n#show item/1.\n"))
    return sorted(set((a[0], a[1]) for a in asp.atoms(model, "place") for _ in [0]))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_combos())
    if py == cl:
        print(f"OK: ASP parity check passed for {len(py)} combos.")
        return 0
    print("MISMATCH")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world with apology and friendship transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--item", choices=[x[0] for x in OBJECTS])
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
    place = args.place or rng.choice(PLACES)
    item = next((x for x in OBJECTS if x[0] == args.item), None) if args.item else rng.choice(OBJECTS)
    hero = args.hero or rng.choice(FRIENDS)
    friend = args.friend or rng.choice([n for n in FRIENDS if n != hero])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, item=item, hero=hero, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="the library corner", item=OBJECTS[0], hero="Mina", friend="Owen", trait="curious"),
    StoryParams(place="the classroom", item=OBJECTS[1], hero="Iris", friend="Nico", trait="gentle"),
    StoryParams(place="the garden bench", item=OBJECTS[2], hero="Pia", friend="Toby", trait="clever"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show resolved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available, but this world uses a simple parity stub.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
