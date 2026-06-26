#!/usr/bin/env python3
"""
storyworlds/worlds/wick_cereal_bad_ending_foreshadowing_flashback_heartwarming.py
==================================================================================

A small story world about a candle wick, a bowl of cereal, and a warm family
morning that carries a gentle disappointment.

Seed premise:
- A child and caregiver want a cozy breakfast.
- A candle wick is important because the power is out.
- Cereal is the breakfast prize.
- Foreshadowing hints that the wick is too short and the milk is warming too
  slowly.
- A flashback explains why the caregiver knows how to keep calm.
- The ending is heartwarming, but not perfectly happy: the little plan does not
  go exactly right, though the family stays kind and together.

This world is intentionally small and constraint-checked. The script models a
few typed entities with physical meters and emotional memes, simulates a short
cause-and-effect chain, and then renders one complete story plus grounded Q&A.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    name: str
    power_out: bool = True
    cozy: bool = True
    quiet: bool = True


@dataclass
class StoryParams:
    name: str
    child_type: str
    caretaker_type: str
    room: str
    cereal: str
    wick_style: str
    seed: Optional[int] = None


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

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
        import copy as _copy
        w = World(self.room)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _narrate(world: World, msg: str) -> None:
    world.trace.append(msg)


def _r_wick_burn(world: World) -> list[str]:
    out = []
    candle = world.entities["candle"]
    if candle.meter("lit") < THRESHOLD:
        return out
    if candle.meter("wick_short") < THRESHOLD:
        return out
    sig = ("wick_burn",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    candle.meters["glow"] = candle.meter("glow") + 1.0
    candle.meters["wick_short"] += 0.5
    out.append("The candle burned, but the wick grew shorter.")
    return out


def _r_foreshadow(world: World) -> list[str]:
    out = []
    candle = world.entities["candle"]
    if candle.meter("wick_short") >= THRESHOLD and ("foreshadow",) not in world.fired:
        world.fired.add(("foreshadow",))
        out.append("The short wick made the flame look a little shaky.")
    return out


def _r_milk_warm(world: World) -> list[str]:
    out = []
    bowl = world.entities["cereal_bowl"]
    if bowl.meter("milk_cold") < THRESHOLD:
        return out
    if world.entities["candle"].meter("glow") < THRESHOLD:
        return out
    sig = ("milk_warm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bowl.meters["milk_cold"] -= 0.5
    bowl.meters["milk_warm"] += 0.5
    out.append("The little flame helped warm the room, but the milk stayed slow.")
    return out


def _r_bad_ending(world: World) -> list[str]:
    out = []
    candle = world.entities["candle"]
    bowl = world.entities["cereal_bowl"]
    child = world.entities["child"]
    if candle.meter("wick_short") < 1.5:
        return out
    if bowl.meter("milk_warm") >= THRESHOLD:
        return out
    sig = ("bad_end",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    candle.meters["lit"] = 0.0
    bowl.meters["milk_cold"] = 1.0
    child.memes["disappointment"] = child.meme("disappointment") + 1.0
    out.append("The flame winked out before breakfast was ready.")
    return out


RULES = [_r_wick_burn, _r_foreshadow, _r_milk_warm, _r_bad_ending]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    for s in produced:
        world.say(s)
    return produced


ROOMS = {
    "kitchen": Room(name="the kitchen", power_out=True, cozy=True, quiet=True),
    "cottage": Room(name="the little cottage kitchen", power_out=True, cozy=True, quiet=True),
    "camp": Room(name="the camp table", power_out=True, cozy=True, quiet=True),
}

CEREALS = {
    "puffed": ("a bowl of puffed cereal", "puffed cereal"),
    "flakes": ("a blue bowl of cereal flakes", "cereal flakes"),
    "stars": ("a tiny bowl of star cereal", "star cereal"),
}

WICKS = {
    "short": ("a short candle wick", "short"),
    "tiny": ("a tiny candle wick", "tiny"),
    "frayed": ("a frayed candle wick", "frayed"),
}


def build_world(params: StoryParams) -> World:
    room = ROOMS[params.room]
    world = World(room)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.child_type,
        label=params.name,
        meters={"hunger": 1.0},
        memes={"hope": 1.0, "warmth": 1.0},
    ))
    caretaker_type = params.caretaker_type
    caregiver = world.add(Entity(
        id="caregiver",
        kind="character",
        type=caretaker_type,
        label="Grandma" if caretaker_type == "grandmother" else "Dad",
        meters={"patience": 1.0},
        memes={"care": 1.0, "calm": 1.0},
    ))
    candle = world.add(Entity(
        id="candle",
        type="candle",
        label="candle",
        phrase=params.wick_style,
        owner=child.id,
        meters={"lit": 1.0, "wick_short": 1.0},
    ))
    bowl_phrase, cereal_name = CEREALS[params.cereal]
    bowl = world.add(Entity(
        id="cereal_bowl",
        type="bowl",
        label="bowl",
        phrase=bowl_phrase,
        owner=child.id,
        meters={"milk_cold": 1.0, "milk_warm": 0.0},
    ))
    wick_desc, wick_style = WICKS[params.wick_style]
    wick = world.add(Entity(
        id="wick",
        type="wick",
        label="wick",
        phrase=wick_desc,
        owner="candle",
        meters={"shortness": 1.0},
    ))
    world.facts.update(
        child=child,
        caregiver=caregiver,
        candle=candle,
        bowl=bowl,
        wick=wick,
        cereal_name=cereal_name,
        room=room,
        params=params,
    )
    return world


def flashback_line(child: Entity, caregiver: Entity, wick_style: str) -> str:
    if caregiver.type == "grandmother":
        return (
            f"That reminded {child.label} of a morning long ago, when {caregiver.label} "
            f"showed {child.pronoun('object')} how to watch a candle without rushing."
        )
    return (
        f"That reminded {child.label} of an earlier day, when {caregiver.label} "
        f"taught {child.pronoun('object')} to stay calm and keep trying."
    )


def tell_story(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    caregiver: Entity = f["caregiver"]
    candle: Entity = f["candle"]
    bowl: Entity = f["bowl"]

    world.say(
        f"In {world.room.name}, {child.label} woke to a quiet morning and a little bowl of cereal."
    )
    world.say(
        f"The only light came from a {candle.phrase if candle.phrase else 'candle'}."
    )
    world.say(
        f"{child.label} liked that warm glow, because it made breakfast feel special."
    )
    world.para()
    world.say(
        f"Still, the wick looked a bit too short."
    )
    world.say(
        f"{child.label} noticed it first, and that tiny worry sat beside the cereal like a shadow."
    )
    propagate(world)
    world.para()
    world.say(
        flashback_line(child, caregiver, f["params"].wick_style)
    )
    world.say(
        f"That memory helped {child.label} breathe slowly while {caregiver.label} checked the bowl."
    )
    world.say(
        f"They ate the {f['cereal_name']} together, even though the milk stayed colder than they hoped."
    )
    if candle.meter("lit") < THRESHOLD:
        world.say(
            f"In the end, the candle went out before the breakfast was finished."
        )
        world.say(
            f"{child.label} felt a little sad about the spoiled start, but {caregiver.label} smiled and put an arm around {child.pronoun('object')}."
        )
        world.say(
            f"They shared the last spoonfuls in the dim kitchen, and the quiet morning still felt full of love."
        )
    else:
        world.say(
            f"The candle stayed on for a while, and the room glowed softly while they ate."
        )
    world.facts["ended_bad"] = candle.meter("lit") < THRESHOLD
    world.facts["flashback"] = True
    world.facts["foreshadow"] = True


def story_intro(world: World) -> str:
    f = world.facts
    child: Entity = f["child"]
    caregiver: Entity = f["caregiver"]
    return (
        f"{child.label} and {caregiver.label} tried to make a cozy breakfast when the power was out."
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    caregiver: Entity = f["caregiver"]
    candle: Entity = f["candle"]
    bowl: Entity = f["bowl"]
    qas = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {child.label} and {caregiver.label}, who tried to have a gentle breakfast together.",
        ),
        QAItem(
            question=f"What was important about the candle?",
            answer=f"The candle gave light in the dark kitchen, and its wick was important because it helped the flame stay on.",
        ),
        QAItem(
            question=f"Why did {child.label} notice something worrying?",
            answer=f"{child.label} noticed that the wick was getting too short, so the flame looked shaky and the breakfast felt less certain.",
        ),
        QAItem(
            question=f"What food did they want to eat?",
            answer=f"They wanted to eat cereal from a bowl, even though the milk stayed colder than they hoped.",
        ),
        QAItem(
            question=f"What memory helped {child.label} stay calm?",
            answer=f"{child.label} remembered an earlier time when {caregiver.label} taught {child.pronoun('object')} to watch a candle carefully and breathe slowly.",
        ),
    ]
    if f.get("ended_bad"):
        qas.append(
            QAItem(
                question="What went wrong at the end?",
                answer="The candle went out before breakfast was finished, so the morning did not end the way they wanted, even though they stayed kind to each other.",
            )
        )
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a wick?",
            answer="A wick is the string part of a candle that soaks up wax and helps the candle flame burn.",
        ),
        QAItem(
            question="What is cereal?",
            answer="Cereal is a breakfast food made from grains, often eaten in a bowl with milk.",
        ),
        QAItem(
            question="What does a flashback do in a story?",
            answer="A flashback tells about something that happened earlier, so readers understand why a character feels or acts a certain way now.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a hint that something may happen later in the story, like noticing a problem before it gets bigger.",
        ),
        QAItem(
            question="What is a bad ending?",
            answer="A bad ending is when the main goal does not work out perfectly, even if the characters still handle it kindly.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    return [
        f'Write a heartwarming story about {child.label}, a candle wick, and a bowl of cereal during a power outage.',
        "Tell a gentle story with foreshadowing, a flashback, and a bad ending that still feels warm and caring.",
        "Write a small family story where breakfast goes a little wrong, but kindness matters more than perfection.",
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
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.extend(f"  {line}" for line in world.trace)
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("room", "kitchen"),
        asp.fact("room", "cottage"),
        asp.fact("room", "camp"),
        asp.fact("feature", "foreshadowing"),
        asp.fact("feature", "flashback"),
        asp.fact("feature", "bad_ending"),
        asp.fact("style", "heartwarming"),
    ]
    for cid, (label, _) in CEREALS.items():
        lines.append(asp.fact("cereal", cid))
        lines.append(asp.fact("breakfast_food", cid))
    for wid, (label, _) in WICKS.items():
        lines.append(asp.fact("wick", wid))
        lines.append(asp.fact("candlestick_part", wid))
    lines.append(asp.fact("character", "child"))
    lines.append(asp.fact("character", "caregiver"))
    lines.append(asp.fact("can_foreshadow", "wick"))
    lines.append(asp.fact("can_flashback", "memory"))
    lines.append(asp.fact("can_bad_ending", "candle_out"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(R, C, W) :- room(R), cereal(C), wick(W).
uses_foreshadowing :- feature(foreshadowing).
uses_flashback :- feature(flashback).
uses_bad_ending :- feature(bad_ending).
heartwarming :- style(heartwarming).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_triples() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(r, c, w) for r in ROOMS for c in CEREALS for w in WICKS}
    cl = set(asp_valid_triples())
    if py == cl:
        print(f"OK: clingo gate matches python registry ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


@dataclass
class StoryParams:
    room: str
    cereal: str
    wick_style: str
    name: str
    child_type: str
    caretaker_type: str
    seed: Optional[int] = None


NAMES = ["Mia", "Nora", "Ben", "Leo", "Ava", "Elsie", "Theo", "June"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld about wick and cereal.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--cereal", choices=CEREALS)
    ap.add_argument("--wick-style", choices=WICKS)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--caretaker-type", choices=["grandmother", "father"])
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
    room = args.room or rng.choice(list(ROOMS))
    cereal = args.cereal or rng.choice(list(CEREALS))
    wick_style = args.wick_style or rng.choice(list(WICKS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    caretaker_type = args.caretaker_type or rng.choice(["grandmother", "father"])
    name = args.name or rng.choice(NAMES)
    return StoryParams(
        room=room,
        cereal=cereal,
        wick_style=wick_style,
        name=name,
        child_type=child_type,
        caretaker_type=caretaker_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    story = story_intro(world) + "\n\n" + world.render()
    return StorySample(
        params=params,
        story=story,
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
    StoryParams(room="kitchen", cereal="flakes", wick_style="short", name="Mia", child_type="girl", caretaker_type="grandmother"),
    StoryParams(room="cottage", cereal="stars", wick_style="frayed", name="Ben", child_type="boy", caretaker_type="father"),
    StoryParams(room="camp", cereal="puffed", wick_style="tiny", name="Ava", child_type="girl", caretaker_type="grandmother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} compatible room/cereal/wick combinations:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
