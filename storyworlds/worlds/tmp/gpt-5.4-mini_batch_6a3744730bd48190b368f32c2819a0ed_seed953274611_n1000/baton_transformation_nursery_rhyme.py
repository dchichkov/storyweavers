#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/baton_transformation_nursery_rhyme.py
======================================================================

A tiny nursery-rhyme storyworld about a baton that changes what the children are
doing. The world is small on purpose: one child finds a baton, the baton is used
as a pretend conductor's stick, and a transformation changes the toy game into a
real performance. The story stays child-facing, rhythmic, and concrete.

The domain supports close variations where the baton transforms a plain playtime
into a marching song, or where the child learns to treat the baton gently so the
moment can be shared. The world model drives the prose: the baton, the child,
the room, and the music all carry changing physical meters and emotional memes.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/baton_transformation_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4-mini/baton_transformation_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4-mini/baton_transformation_nursery_rhyme.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/baton_transformation_nursery_rhyme.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/baton_transformation_nursery_rhyme.py --verify
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"stillness": 0.0, "shine": 0.0, "music": 0.0, "tidy": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "curiosity": 0.0, "pride": 0.0, "wonder": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Room:
    id: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"quiet": 1.0, "music": 0.0, "spark": 0.0}
        if not self.memes:
            self.memes = {"wait": 0.0, "delight": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Baton:
    id: str
    label: str
    material: str
    can_transform: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"held": 0.0, "glow": 0.0, "turns": 0.0}
        if not self.memes:
            self.memes = {"importance": 0.0, "magic": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Transformation:
    id: str
    from_state: str
    to_state: str
    verb: str
    shine_gain: float
    music_gain: float
    joy_gain: float
    line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    child: str
    child_gender: str
    room: str
    baton: str
    transformation: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: str) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _r_turn(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    baton = world.get("baton")
    room = world.get("room")
    if baton.meters["held"] >= THRESHOLD and room.meters["spark"] >= THRESHOLD:
        sig = ("turn", baton.id)
        if sig not in world.fired:
            world.fired.add(sig)
            baton.meters["turns"] += 1
            baton.meters["glow"] += 1
            room.meters["music"] += 1
            child.memes["joy"] += 1
            child.memes["wonder"] += 1
            out.append("__turn__")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    child = world.get("child")
    if room.meters["music"] >= THRESHOLD:
        sig = ("settle", room.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["tidy"] += 1
            out.append("The tune settled into a neat little beat.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_r_turn, _r_settle):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_transformation(world: World, trans: Transformation) -> dict:
    sim = world.copy()
    baton = sim.get("baton")
    room = sim.get("room")
    baton.meters["held"] += 1
    room.meters["spark"] += 1
    propagate(sim, narrate=False)
    return {
        "turned": baton.meters["turns"] >= THRESHOLD,
        "music": room.meters["music"],
        "joy": sim.get("child").memes["joy"],
    }


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room_id, room in ROOMS.items():
        for baton_id, baton in BATONS.items():
            for trans_id, trans in TRANSFORMATIONS.items():
                if baton.can_transform and trans.from_state in {"quiet", "waiting"}:
                    combos.append((room_id, baton_id, trans_id))
    return combos


def explain_rejection(room: str, baton: str, trans: str) -> str:
    return f"(No story: the combination {room}/{baton}/{trans} does not support a gentle transformation.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme baton transformation storyworld.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--baton", choices=BATONS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
              and (args.baton is None or c[1] == args.baton)
              and (args.transformation is None or c[2] == args.transformation)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    room, baton, transformation = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    return StoryParams(child=child, child_gender=child_gender, room=room, baton=baton, transformation=transformation)


def tell(params: StoryParams) -> World:
    world = World(ROOMS[params.room].label)
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child, role="player"))
    baton = world.add(Entity(id="baton", kind="thing", type="baton", label=BATONS[params.baton].label, role="tool"))
    room = world.add(Room(id="room", label=ROOMS[params.room].label))
    trans = TRANSFORMATIONS[params.transformation]

    child.memes["curiosity"] += 1
    world.say(
        f"{child.label_word} was in {room.label}, and {child.label_word} found a {baton.label} by the bed."
    )
    world.say(
        f"{child.label_word} tapped the {baton.label}, and {trans.line}"
    )
    world.para()
    baton.meters["held"] += 1
    room.meters["spark"] += 1
    child.memes["joy"] += 1
    child.memes["wonder"] += 1
    propagate(world, narrate=True)
    world.say(
        f"{trans.ending_line} The {baton.label} stayed bright in {child.label_word}'s hand, and the room felt like a song."
    )

    world.facts.update(child=child, baton=baton, room=room, transformation=trans)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a nursery rhyme story with the word baton and a small transformation in {f['room'].label}.",
        f"Tell a gentle story where {f['child'].label_word} finds a baton and it changes an ordinary moment into music.",
        "Write a rhyming story for a child where a baton helps turn quiet play into a lively little song.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    baton = f["baton"]
    room = f["room"]
    trans = f["transformation"]
    return [
        ("Who is the story about?", f"It is about {child.label_word}, who found a {baton.label} in {room.label}."),
        (f"What did the {baton.label} do?", f"It helped transform the quiet room into a little music-filled scene. That change made the play feel brighter and more alive."),
        ("How did the child feel at the end?", f"{child.label_word} felt joyful and full of wonder. The baton and the music turned the room into a happy ending image."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a baton?", "A baton is a short stick that can be used to lead music or marching. In a pretend story, it can seem almost magical."),
        ("What is a transformation?", "A transformation is a change from one form or feeling into another. In stories, it can turn something quiet into something lively."),
        ("What is music?", "Music is sound arranged in rhythm and tune. It can make a room feel bright, lively, and full of movement."),
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ROOMS = {
    "nursery": Room(id="nursery", label="the nursery"),
    "playroom": Room(id="playroom", label="the playroom"),
    "hall": Room(id="hall", label="the little hall"),
}

BATONS = {
    "wood": Baton(id="wood", label="wooden baton", material="wood"),
    "glitter": Baton(id="glitter", label="glitter baton", material="cardboard"),
}

TRANSFORMATIONS = {
    "music": Transformation(
        id="music",
        from_state="quiet",
        to_state="music",
        verb="turns the silence into a song",
        shine_gain=1.0,
        music_gain=2.0,
        joy_gain=1.0,
        line="the baton twirled, and the silence turned into a song.",
        ending_line="The song had a neat little beat, and even the lamp seemed to nod.",
        tags={"music", "turn"},
    ),
    "march": Transformation(
        id="march",
        from_state="waiting",
        to_state="march",
        verb="makes the steps begin to march",
        shine_gain=1.0,
        music_gain=1.0,
        joy_gain=1.0,
        line="the baton flicked up, and the feet began to march in time.",
        ending_line="The steps went pat-a-pat, and the floor felt like a parade.",
        tags={"march", "turn"},
    ),
    "rainbow": Transformation(
        id="rainbow",
        from_state="quiet",
        to_state="rainbow",
        verb="fills the room with a rainbow rhyme",
        shine_gain=2.0,
        music_gain=1.0,
        joy_gain=1.5,
        line="the baton flashed, and a rainbow rhyme seemed to bloom in the air.",
        ending_line="The little room looked brighter than before, as if it wore a ribbon.",
        tags={"rainbow", "turn"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Tess", "Maya", "Ruby"]
BOY_NAMES = ["Finn", "Theo", "Ben", "Leo", "Ari", "Max"]


CURATED = [
    StoryParams(child="Lily", child_gender="girl", room="nursery", baton="wood", transformation="music"),
    StoryParams(child="Theo", child_gender="boy", room="playroom", baton="glitter", transformation="march"),
    StoryParams(child="Mina", child_gender="girl", room="hall", baton="wood", transformation="rainbow"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
    for bid in BATONS:
        lines.append(asp.fact("baton", bid))
    for tid in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(R,B,T) :- room(R), baton(B), transformation(T).
turned(B) :- baton(B), transformation(T), valid(_,B,T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    try:
        python_set = set(valid_combos())
        clingo_set = set(asp_valid_combos())
        if python_set == clingo_set:
            print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
        else:
            rc = 1
            print("MISMATCH in valid_combos:")
            print(" python-only:", sorted(python_set - clingo_set))
            print(" clingo-only:", sorted(clingo_set - python_set))
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"VERIFY FAILED: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS or params.baton not in BATONS or params.transformation not in TRANSFORMATIONS:
        raise StoryError("Invalid params.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def resolve_choice(args, key, values, rng):
    return getattr(args, key) or rng.choice(list(values))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("(No valid combination exists.)")
    room = args.room or rng.choice(sorted(ROOMS))
    baton = args.baton or rng.choice(sorted(BATONS))
    transformation = args.transformation or rng.choice(sorted(TRANSFORMATIONS))
    if (room, baton, transformation) not in combos:
        raise StoryError("(No valid combination matches the given options.)")
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(child=child, child_gender=gender, room=room, baton=baton, transformation=transformation)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (room, baton, transformation) combos:\n")
        for room, baton, trans in combos:
            print(f"  {room:9} {baton:8} {trans}")
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
            header = f"### {p.child}: {p.baton} -> {p.transformation} in {p.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
