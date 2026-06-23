#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/battalion_bid_repetition_reconciliation_inner_monologue_ghost.py
======================================================================================================================

A standalone story world for a small ghost-story domain.

Premise:
A shy little ghost hears a brave "bid" from a battalion of toy drummers
in the old hall. The ghost repeats one small chant in its head, grows
less afraid, and finally reconciles with the noisy visitors.

The story uses:
- battalion
- bid
- repetition
- reconciliation
- inner monologue
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"ghost", "spirit"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Hall:
    name: str
    place_detail: str
    echo_level: str
    moonlight: str
    affords: set[str] = field(default_factory=set)


@dataclass
class VisitorGroup:
    id: str
    label: str
    phrase: str
    sound: str
    group_word: str
    repeats: str
    bid_text: str
    settles: str
    tags: set[str] = field(default_factory=set)


@dataclass
class GhostMood:
    label: str
    inner_line: str
    fear_turn: str
    calm_turn: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    hall: Hall
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        clone = World(self.hall)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    hall: str
    visitors: str
    mood: str
    ghost_name: str
    seed: Optional[int] = None


HALLS = {
    "old_hall": Hall(
        name="the old hall",
        place_detail="The old hall had tall windows, dusty chairs, and moonlight on the floor.",
        echo_level="soft echoes",
        moonlight="silver moonlight",
        affords={"drum", "march", "listen"},
    ),
    "library": Hall(
        name="the quiet library",
        place_detail="The quiet library smelled like paper and rain, and the shelves made long shadows.",
        echo_level="thin echoes",
        moonlight="blue moonlight",
        affords={"whisper", "listen", "march"},
    ),
    "station": Hall(
        name="the empty station",
        place_detail="The empty station had a long bench, a clock that never seemed to hurry, and pale light on the tiles.",
        echo_level="hollow echoes",
        moonlight="cold moonlight",
        affords={"drum", "march", "listen"},
    ),
}

VISITORS = {
    "toy_battalion": VisitorGroup(
        id="toy_battalion",
        label="a battalion of toy drummers",
        phrase="a battalion of tiny drummers in blue caps",
        sound="tum-tum-tum",
        group_word="battalion",
        repeats="drum",
        bid_text="made a brave bid to wake the hall",
        settles="lowered their drums and bowed politely",
        tags={"battalion", "drum", "noise"},
    ),
    "school_band": VisitorGroup(
        id="school_band",
        label="a school band",
        phrase="a little school band with bright scarves",
        sound="ta-ta-ta",
        group_word="band",
        repeats="play",
        bid_text="made a bold bid to fill the hall with music",
        settles="softened their notes and smiled",
        tags={"music", "noise", "bid"},
    ),
    "night_walkers": VisitorGroup(
        id="night_walkers",
        label="a line of night walkers",
        phrase="three quiet walkers with lanterns",
        sound="tap-tap",
        group_word="line",
        repeats="step",
        bid_text="made a quiet bid to cross the hall together",
        settles="stood still and listened",
        tags={"quiet", "bid", "lantern"},
    ),
}

MOODS = {
    "startled": GhostMood(
        label="startled",
        inner_line="The ghost kept saying, in its own head, stay small, stay small, stay small.",
        fear_turn="The repeating thought made the fear less sharp.",
        calm_turn="When the noise slowed, the ghost felt brave enough to look up.",
        ending_image="At the end, the ghost floated by the window with moonlight on its cheeks.",
        tags={"repetition", "inner_monologue", "reconciliation"},
    ),
    "lonely": GhostMood(
        label="lonely",
        inner_line="The ghost whispered to itself, maybe they will not mind me, maybe they will not mind me.",
        fear_turn="The repeated whisper made the room feel less empty.",
        calm_turn="When the visitors answered kindly, the ghost stopped trembling.",
        ending_image="At the end, the ghost and the visitors shared the old bench like friends.",
        tags={"repetition", "inner_monologue", "reconciliation"},
    ),
    "curious": GhostMood(
        label="curious",
        inner_line="The ghost thought, again and again, what are they asking the dark for?",
        fear_turn="The same question turned fright into wonder.",
        calm_turn="When the answer came, the ghost drifted closer without shaking.",
        ending_image="At the end, the ghost glowed softly beside the lantern light.",
        tags={"repetition", "inner_monologue", "reconciliation"},
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for hall_id, hall in HALLS.items():
        for visitor_id, visitor in VISITORS.items():
            if "bid" in visitor.tags or visitor.id == "toy_battalion":
                for mood_id in MOODS:
                    combos.append((hall_id, visitor_id, mood_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with repetition and reconciliation.")
    ap.add_argument("--hall", choices=HALLS)
    ap.add_argument("--visitors", choices=VISITORS)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--name", dest="ghost_name")
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
    combos = [c for c in valid_combos()
              if (args.hall is None or c[0] == args.hall)
              and (args.visitors is None or c[1] == args.visitors)
              and (args.mood is None or c[2] == args.mood)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    hall, visitors, mood = rng.choice(sorted(combos))
    ghost_name = args.ghost_name or rng.choice(["Pip", "Milo", "Ivy", "Luna", "Nell"])
    return StoryParams(hall=hall, visitors=visitors, mood=mood, ghost_name=ghost_name)


def _setup_world(params: StoryParams) -> World:
    world = World(HALLS[params.hall])
    ghost = world.add(Entity(
        id=params.ghost_name,
        kind="character",
        type="ghost",
        label="little ghost",
        role="listener",
        traits=["shy", "curious"],
        meters={"drift": 0.0},
        memes={"fear": 0.0, "calm": 0.0, "reconciliation": 0.0},
        attrs={"hall": params.hall},
    ))
    group = world.add(Entity(
        id="visitors",
        kind="character",
        type="group",
        label=VISITORS[params.visitors].label,
        role="visitors",
        traits=["noisy"],
        meters={"sound": 0.0},
        memes={"noise": 0.0, "warmth": 0.0},
        attrs={"group": params.visitors},
        plural=True,
    ))
    world.facts.update(ghost=ghost, group=group, mood=MOODS[params.mood], visitor_cfg=VISITORS[params.visitors])
    return world


def _narrate(world: World, params: StoryParams) -> World:
    ghost = world.get(params.ghost_name)
    group = world.get("visitors")
    mood = MOODS[params.mood]
    visitor_cfg = VISITORS[params.visitors]
    ghost.memes["fear"] += 1
    world.say(f"{ghost.id} drifted through {world.hall.name}. {world.hall.place_detail}")
    world.say(f"{ghost.id} listened to the {visitor_cfg.group_word} enter with {visitor_cfg.sound} and saw {visitor_cfg.phrase}.")
    world.para()
    world.say(mood.inner_line)
    ghost.memes["fear"] += 1
    ghost.memes["repetition"] = ghost.memes.get("repetition", 0.0) + 1
    world.say(mood.fear_turn)
    world.say(f"In its head, {ghost.id} kept the same little phrase: {mood.inner_line.split(',', 1)[0].lower().rstrip('.')}.")
    world.para()
    group.memes["noise"] += 1
    group.meters["sound"] += 1
    world.say(f"The {visitor_cfg.group_word} made a bid to settle the room, and {visitor_cfg.bid_text}.")
    world.say(f"{ghost.id} almost fled, but the same thought came again: {mood.inner_line.split(',', 1)[0].lower().rstrip('.')}.")
    ghost.memes["calm"] += 1
    world.say(mood.calm_turn)
    ghost.memes["reconciliation"] += 1
    group.memes["warmth"] += 1
    world.say(f"Then the {visitor_cfg.group_word} {visitor_cfg.settles}, and the ghost floated closer instead of hiding.")
    world.para()
    ghost.meters["drift"] += 1
    world.say(f"{ghost.id} and the visitors shared the hush of {world.hall.moonlight}.")
    world.say(mood.ending_image)
    return world


def generate(params: StoryParams) -> StorySample:
    world = _setup_world(params)
    world = _narrate(world, params)
    prompts = [
        f'Write a ghost story that includes the words "{VISITORS[params.visitors].group_word}" and "bid", and lets a shy ghost calm down by repeating one thought.',
        f"Tell a child-friendly ghost tale set in {HALLS[params.hall].name} where {params.ghost_name} listens to {VISITORS[params.visitors].label} and finds reconciliation.",
        f'Write a short story with repetition, inner monologue, and reconciliation, using the word "{VISITORS[params.visitors].group_word}".',
    ]
    ghost = world.get(params.ghost_name)
    visitor_cfg = VISITORS[params.visitors]
    mood = MOODS[params.mood]
    story_qa = [
        QAItem(
            question=f"Why did {params.ghost_name} stop feeling so scared in the story?",
            answer=f"{params.ghost_name} kept repeating the same calm thought in its head, so the fear got smaller. The repeated thought helped {params.ghost_name} stay in the hall and meet the visitors instead of hiding.",
        ),
        QAItem(
            question=f"What did the {visitor_cfg.group_word} do that was called a bid?",
            answer=f"They made a bid to settle the room and be heard without frightening the ghost. That bid was the start of the story's turn from noise toward reconciliation.",
        ),
        QAItem(
            question=f"How did the story end for {params.ghost_name} and the visitors?",
            answer=f"They reconciled and shared the quiet space together. By the end, the ghost was calmer and the visitors had softened their noise.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is repetition in a story?",
            answer="Repetition means saying or doing the same thing again. In this kind of story, it can sound like a repeated thought or line that helps a character change.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after fear, confusion, or a disagreement. It is when characters stop feeling apart and can be together calmly.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is a character's private thinking in words. The reader hears the thought even though the character does not say it out loud.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(hall="old_hall", visitors="toy_battalion", mood="startled", ghost_name="Pip"),
    StoryParams(hall="library", visitors="night_walkers", mood="lonely", ghost_name="Ivy"),
    StoryParams(hall="station", visitors="school_band", mood="curious", ghost_name="Luna"),
]


ASP_RULES = r"""
valid(H,V,M) :- hall(H), visitors(V), mood(M), usable(V).
usable(toy_battalion).
usable(school_band).
usable(night_walkers).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for hid in HALLS:
        lines.append(asp.fact("hall", hid))
    for vid in VISITORS:
        lines.append(asp.fact("visitors", vid))
        lines.append(asp.fact("usable", vid))
    for mid in MOODS:
        lines.append(asp.fact("mood", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos disagree.")
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=True, qa=True)
    except Exception as err:
        print(f"MISMATCH: smoke test failed: {err}")
        return 1
    print(f"OK: ASP matches Python and smoke test passed ({len(valid_combos())} combos).")
    return 0


def generate_all(args: argparse.Namespace, base_seed: int) -> list[StorySample]:
    samples = []
    seen = set()
    i = 0
    while len(samples) < args.n and i < max(args.n * 50, 50):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        sample = generate(params)
        if sample.story not in seen:
            seen.add(sample.story)
            samples.append(sample)
        i += 1
    return samples


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{h} {v} {m}" for h, v, m in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = [generate(p) for p in CURATED] if args.all else generate_all(args, base_seed)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
