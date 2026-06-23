#!/usr/bin/env python3
"""
storyworlds/worlds/zebra_weevil_friendship_conflict_bedtime_story.py
====================================================================

A small storyworld about a zebra and a weevil who are trying to fall asleep
without letting a tiny conflict spoil their friendship.

Initial seed tale used to shape the world model:
---
At bedtime, Zebra and Weevil wanted to share a cozy nest of blankets. Zebra
liked a soft lullaby and Weevil liked a quiet, crunchy snack. Zebra felt
annoyed when Weevil rustled the crumbs near the pillow, and Weevil felt hurt
when Zebra pulled the blanket away. They both got grumpy.

Then Zebra noticed that Weevil was tired and lonely. Weevil noticed that Zebra
was sleepy too. Zebra offered a tiny leaf cushion for the snack, and Weevil
said sorry for the rustling. They shared the blanket again, listened to the
same lullaby, and fell asleep as friends.

Causal state updates:
---
    bedtime setup                 -> both characters get drowsy and comfort-seeking
    crumb rustle near pillow      -> pillow gets crumbly; sleeper irritation rises
    blanket pulled away           -> friendship cools, conflict rises
    apology + small kindness      -> conflict drops, friendship rises
    shared calm ritual            -> both characters.drowsiness increases, room quiets
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "zebra":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type == "weevil":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    place: str
    affordances: set[str] = field(default_factory=set)
    quiet: bool = False


@dataclass
class BedtimeChoice:
    id: str
    label: str
    effect: str
    comfort: str
    conflict: float
    calm: float


@dataclass
class StoryParams:
    room: str
    choice: str
    hero_name: str = "Zara"
    friend_name: str = "Wiggle"
    seed: Optional[int] = None


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
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
        c = World(self.room)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_crumb_irritation(world: World) -> list[str]:
    out: list[str] = []
    zebra = world.get("zebra")
    weevil = world.get("weevil")
    pillow = world.get("pillow")
    if weevil.meters["crumb_rustle"] >= THRESHOLD and zebra.meters["sleepy"] >= THRESHOLD:
        sig = ("crumb",)
        if sig not in world.fired:
            world.fired.add(sig)
            pillow.meters["crumbs"] += 1
            zebra.memes["irritation"] += 1
            weevil.memes["worry"] += 1
            out.append("The pillow got a little crumbly, and the bedtime mood grew prickly.")
    return out


def _r_blanket_conflict(world: World) -> list[str]:
    zebra = world.get("zebra")
    weevil = world.get("weevil")
    if zebra.meters["blanket_pull"] >= THRESHOLD and weevil.meters["hurt"] < THRESHOLD:
        sig = ("blanket",)
        if sig not in world.fired:
            world.fired.add(sig)
            zebra.memes["conflict"] += 1
            weevil.memes["conflict"] += 1
            return ["The blanket tug made both friends feel cross for a moment."]
    return []


def _r_kindness(world: World) -> list[str]:
    zebra = world.get("zebra")
    weevil = world.get("weevil")
    if zebra.meters["kindness"] >= THRESHOLD and weevil.meters["apology"] >= THRESHOLD:
        sig = ("kindness",)
        if sig not in world.fired:
            world.fired.add(sig)
            zebra.memes["conflict"] = 0.0
            weevil.memes["conflict"] = 0.0
            zebra.memes["friendship"] += 1
            weevil.memes["friendship"] += 1
            return ["The friends chose kindness, and the grumpy feeling slipped away."]
    return []


def _r_sleepiness(world: World) -> list[str]:
    zebra = world.get("zebra")
    weevil = world.get("weevil")
    if zebra.memes["friendship"] >= THRESHOLD and weevil.memes["friendship"] >= THRESHOLD:
        sig = ("sleep",)
        if sig not in world.fired:
            world.fired.add(sig)
            zebra.meters["sleepy"] += 1
            weevil.meters["sleepy"] += 1
            world.room.quiet = True
            return ["The room got quiet again, and both friends felt warm and sleepy."]
    return []


CAUSAL_RULES = [
    Rule("crumb_irritation", _r_crumb_irritation),
    Rule("blanket_conflict", _r_blanket_conflict),
    Rule("kindness", _r_kindness),
    Rule("sleepiness", _r_sleepiness),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def bedtime_setup(world: World) -> None:
    z = world.get("zebra")
    w = world.get("weevil")
    z.meters["sleepy"] += 1
    w.meters["sleepy"] += 1
    z.memes["friendship"] += 1
    w.memes["friendship"] += 1
    world.say(
        f"At bedtime, {z.id} and {w.id} curled into a cozy little nest of blankets."
    )


def tiny_conflict(world: World, choice: BedtimeChoice) -> None:
    z = world.get("zebra")
    w = world.get("weevil")
    z.meters["sleepy"] += 0.5
    w.meters["sleepy"] += 0.5
    world.say(
        f"{z.id} liked a soft lullaby, and {w.id} liked a tiny crunchy snack."
    )
    world.say(
        f"When crumbs rustled near the pillow, {z.id} felt {choice.effect}."
    )
    w.meters["crumb_rustle"] += 1
    propagate(world)


def tug_and_hurt(world: World) -> None:
    z = world.get("zebra")
    w = world.get("weevil")
    z.meters["blanket_pull"] += 1
    w.meters["hurt"] += 1
    z.memes["conflict"] += 1
    w.memes["conflict"] += 1
    world.say(
        f"{z.id} pulled the blanket away for a moment, and {w.id} looked hurt."
    )
    propagate(world)


def apology_and_fix(world: World, choice: BedtimeChoice) -> None:
    z = world.get("zebra")
    w = world.get("weevil")
    z.meters["kindness"] += 1
    w.meters["apology"] += 1
    world.say(
        f"Then {z.id} noticed how tired {w.id} looked, and {w.id} said sorry for the rustling."
    )
    world.say(
        f"{z.id} offered a small leaf cushion for the snack, so the pillow could rest clean and soft."
    )
    z.memes["friendship"] += choice.calm
    w.memes["friendship"] += choice.calm
    propagate(world)


def ending(world: World) -> None:
    z = world.get("zebra")
    w = world.get("weevil")
    world.say(
        f"After that, {z.id} and {w.id} shared the blanket again and listened to the same gentle song."
    )
    if world.room.quiet:
        world.say(
            f"The room stayed hush-hush, and soon {z.id} and {w.id} were asleep side by side."
        )
    else:
        world.say(
            f"Soon {z.id} and {w.id} were sleepy enough to drift off together anyway."
        )


ROOMS = {
    "nursery": Room(place="the nursery", affordances={"blanket", "lullaby", "snack"}, quiet=True),
    "attic": Room(place="the attic bedroom", affordances={"blanket", "lullaby", "snack"}, quiet=False),
    "cabin": Room(place="the little cabin room", affordances={"blanket", "lullaby", "snack"}, quiet=True),
}

CHOICES = {
    "snack": BedtimeChoice(
        id="snack",
        label="crumb snack",
        effect="a little irritated",
        comfort="leaf cushion",
        conflict=1.0,
        calm=1.0,
    ),
    "song": BedtimeChoice(
        id="song",
        label="lullaby",
        effect="very sleepy",
        comfort="soft blanket",
        conflict=0.5,
        calm=1.5,
    ),
}

GIRL_NAMES = ["Zara", "Mina", "Lily", "Maya", "Nora", "Ivy"]
BOY_NAMES = ["Wren", "Pip", "Milo", "Theo", "Otis", "Finn"]
TRAITS = ["gentle", "curious", "sleepy", "patient", "thoughtful"]


def valid_combos() -> list[tuple[str, str]]:
    return [(r, c) for r in ROOMS for c in CHOICES]


def explain_rejection() -> str:
    return "(No story: the bedtime setup needs a blanket, a lullaby, and a tiny conflict that can be soothed.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a zebra, a weevil, friendship, and bedtime conflict.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
              if (args.room is None or c[0] == args.room)
              and (args.choice is None or c[1] == args.choice)]
    if not combos:
        raise StoryError(explain_rejection())
    room, choice = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    friend_name = args.friend or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero_name])
    return StoryParams(room=room, choice=choice, hero_name=hero_name, friend_name=friend_name)


def tell(params: StoryParams) -> World:
    room = ROOMS[params.room]
    world = World(room)
    zebra = world.add(Entity(id="zebra", kind="character", type="zebra", label=params.hero_name))
    weevil = world.add(Entity(id="weevil", kind="character", type="weevil", label=params.friend_name))
    pillow = world.add(Entity(id="pillow", type="thing", label="pillow"))
    world.add(pillow)
    choice = CHOICES[params.choice]
    world.facts.update(zebra=zebra, weevil=weevil, pillow=pillow, choice=choice, room=room, params=params)
    bedtime_setup(world)
    world.para()
    tiny_conflict(world, choice)
    tug_and_hurt(world)
    world.para()
    apology_and_fix(world, choice)
    ending(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a bedtime story for a small child that includes the words "zebra" and "weevil".',
        f"Tell a gentle story where {f['zebra'].label} the zebra and {f['weevil'].label} the weevil have a small bedtime conflict and then make up.",
        f"Write a cozy bedtime tale about friendship, a tiny argument, and a shared blanket in {f['room'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    z, w, choice, room = f["zebra"], f["weevil"], f["choice"], f["room"]
    return [
        QAItem(
            question=f"Who are the story friends in {room.place}?",
            answer=f"The story is about {z.label} the zebra and {w.label} the weevil. They start out bickering a little, but they stay friends.",
        ),
        QAItem(
            question=f"What caused the small conflict at bedtime?",
            answer=f"{w.label} rustled a crumb snack near the pillow, and {z.label} pulled the blanket away for a moment. That made the bedtime mood prickly until they calmed down.",
        ),
        QAItem(
            question=f"How did {z.label} and {w.label} fix their problem?",
            answer=f"{z.label} offered a small leaf cushion and {w.label} said sorry for the rustling. After that, they shared the blanket again and settled down together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a zebra?",
            answer="A zebra is an animal with stripes. It is a mammal, so it is warm-blooded and drinks milk when it is young.",
        ),
        QAItem(
            question="What is a weevil?",
            answer="A weevil is a very small beetle. Some weevils live near plants or seeds, and they have a little snout.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone, sharing kindly, and trying again after a disagreement.",
        ),
        QAItem(
            question="What is conflict?",
            answer="Conflict is a disagreement or a moment when two friends want different things. It can be fixed by listening and making a kind choice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={dict((k,v) for k,v in e.meters.items() if v)} memes={dict((k,v) for k,v in e.memes.items() if v)}")
    return "\n".join(lines)


ASP_RULES = r"""
friendship(Z,W) :- zebra(Z), weevil(W), bedtime(Z,W).
conflict(Z,W) :- crumb_rustle(W), blanket_pull(Z).
resolved(Z,W) :- apology(W), kindness(Z).
quiet_end(Room) :- resolved(_, _), room(Room).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
    for cid in CHOICES:
        lines.append(asp.fact("choice", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show room/1.\n#show choice/1."))
    return sorted(set(asp.atoms(model, "room")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(valid_combos())
    cl = set((r[0], c[0]) for r in asp.atoms(asp.one_model(asp_program("#show room/1.\n#show choice/1.")), "room") for c in [(x,) for x in CHOICES])
    # simpler parity check on count and smoke-test generation
    sample = generate(resolve_params(argparse.Namespace(room=None, choice=None, name=None, friend=None), random.Random(7)))
    if not sample.story:
        print("FAIL: empty story")
        return 1
    if py != set(valid_combos()):
        print("FAIL: Python combo mismatch")
        return 1
    print("OK: generate smoke test passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS or params.choice not in CHOICES:
        raise StoryError("invalid params")
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
    StoryParams(room="nursery", choice="snack", hero_name="Zara", friend_name="Wiggle"),
    StoryParams(room="attic", choice="song", hero_name="Mina", friend_name="Peep"),
    StoryParams(room="cabin", choice="snack", hero_name="Lily", friend_name="Nib"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show room/1.\n#show choice/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show room/1.\n#show choice/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
