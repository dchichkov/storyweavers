#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100/mar_wiggle_flashback_humor_bedtime_story.py
===============================================================================================================

A tiny bedtime story world about a child, a little mar, and too much wiggle.

Seed tale premise:
- At bedtime, a child is too wiggly to settle.
- A parent remembers, with a small flashback, how this same wiggle once caused trouble.
- With a funny, gentle routine, they turn the wiggle into sleepy comfort.

The world is intentionally small:
- one bedroom setting
- one child with a blanket, pillow, and stuffed animal
- one source of mess/tension: wiggle
- one resolving action: a bedtime routine that channels the wiggle into calm

The story voice stays close to a bedtime story: soft, concrete, reassuring, and lightly humorous.
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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wiggle": 0.0, "mar": 0.0, "sleep": 0.0, "mess": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "tired": 0.0, "humor": 0.0, "memory": 0.0, "calm": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    name: str
    quiet: bool = True
    moonlight: bool = True
    affords: set[str] = field(default_factory=lambda: {"bedtime", "story", "lullaby"})


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    action: str
    helps: set[str] = field(default_factory=lambda: {"wiggle"})


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

    def characters(self) -> list[Entity]:
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
        clone = World(self.room)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def child_name_pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "girl":
        return ("she", "her", "her")
    return ("he", "him", "his")


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    room: str
    comfort: str
    seed: Optional[int] = None


ROOMS = {
    "bedroom": Room(name="the bedroom", quiet=True, moonlight=True, affords={"bedtime", "story", "lullaby"}),
    "nursery": Room(name="the nursery", quiet=True, moonlight=True, affords={"bedtime", "story", "lullaby"}),
}

COMFORTS = {
    "blanket": Comfort(
        id="blanket",
        label="blanket",
        phrase="a soft blanket with blue stars",
        action="pull the blanket up and tuck it close",
        helps={"wiggle"},
    ),
    "stuffie": Comfort(
        id="stuffie",
        label="stuffed bunny",
        phrase="a stuffed bunny with floppy ears",
        action="hug the bunny and listen to its silly ears flop",
        helps={"wiggle"},
    ),
    "pillow": Comfort(
        id="pillow",
        label="pillow",
        phrase="a round pillow that felt like a cloud",
        action="rest one cheek on the pillow and breathe slowly",
        helps={"wiggle"},
    ),
}

NAMES = ["Mia", "Noah", "Lily", "Theo", "Ava", "Finn"]
TRAITS = ["sleepy", "curious", "cheerful", "squirmy"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small bedtime story world with mar, wiggle, flashback, and humor.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--comfort", choices=COMFORTS)
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
    room = args.room or rng.choice(list(ROOMS))
    comfort = args.comfort or rng.choice(list(COMFORTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(name=name, gender=gender, parent=parent, room=room, comfort=comfort)


def _do_wiggle(world: World, child: Entity, intensity: float = 1.0, narrate: bool = True) -> None:
    child.meters["wiggle"] += intensity
    child.memes["joy"] += 0.5
    if narrate:
        world.say(f"{child.id} wiggled so much that even the moonlight seemed to bounce a little.")


def _flashback(world: World, child: Entity) -> None:
    if "flashback" in world.fired:
        return
    world.fired.add(("flashback", child.id))
    child.memes["memory"] += 1
    world.say(
        f"{child.pronoun('possessive').capitalize()} {world.facts['parent_label']} remembered a funny bedtime from before, "
        f"when {child.id} had wiggled so hard that the pillow slid like a sneaky little boat."
    )
    world.say("That was the night the family had laughed so quietly that the giggles sounded like feathers.")


def _calm(world: World, child: Entity, comfort: Comfort) -> None:
    child.meters["wiggle"] = max(0.0, child.meters["wiggle"] - 1.0)
    child.meters["sleep"] += 1.0
    child.memes["calm"] += 1.0
    child.memes["humor"] += 1.0
    world.say(
        f"{child.id} tried {comfort.action}, and the silly wiggle turned smaller and smaller."
    )
    world.say(
        f"Before long, {child.pronoun('subject')} was breathing slow, with a tiny smile that said the blanket had won the race."
    )


def tell(room: Room, comfort: Comfort, name: str = "Mia", gender: str = "girl", parent_type: str = "mother") -> World:
    world = World(room)
    child = world.add(Entity(id=name, kind="character", type=gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"{parent_type}"))
    blanket = world.add(Entity(id="blanket", label=comfort.label, phrase=comfort.phrase, owner=child.id, caretaker=parent.id))
    child.worn_by = None

    parent_label = "mom" if parent_type == "mother" else "dad"
    world.facts.update(child=child, parent=parent, blanket=blanket, comfort=comfort, parent_label=parent_label)

    world.say(f"{name} was a little {TRAITS[0]} child in {room.name}, where the moon made a pale square on the floor.")
    world.say(f"At bedtime, {name} liked {comfort.phrase}, because it felt like the room was giving a sleepy hug.")

    world.para()
    world.say(f"But tonight, {name} could not stop wiggle-wiggling under the covers.")
    _do_wiggle(world, child, intensity=1.0)
    world.say(f"{parent_label} peeked in and said, “Easy now. Your toes are trying to dance without the music.”")
    _flashback(world, child)

    world.para()
    world.say(f"{name} giggled, because the idea of wiggling toes with no music was funny enough to make a pillow giggle too.")
    _calm(world, child, comfort)
    world.say(
        f"Then {parent_label} tucked the blanket in at the corners, and the room grew quiet enough to hear the night smiling."
    )
    world.say(f"{name} fell asleep with {comfort.label} tucked close, and the little mar of the day felt far away now.")
    return world


def valid_combos() -> list[tuple[str, str]]:
    return [(r, c) for r in ROOMS for c in COMFORTS]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_wiggle_to_memory(world: World) -> list[str]:
    child = next(iter(world.characters()), None)
    if not child or child.meters["wiggle"] < THRESHOLD:
        return []
    sig = ("memory", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    _flashback(world, child)
    return ["flashback"]


def _r_memory_to_calm(world: World) -> list[str]:
    child = next(iter(world.characters()), None)
    if not child or child.memes["memory"] < THRESHOLD:
        return []
    sig = ("calm", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["sleep"] += 1.0
    child.memes["calm"] += 1.0
    return ["calm"]


RULES = [Rule("memory", _r_wiggle_to_memory), Rule("calm", _r_memory_to_calm)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for s in produced:
            if s == "flashback":
                continue


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a young child about "{f["comfort"].label}", a little mar, and too much wiggle.',
        f"Tell a soft, humorous bedtime story in which {f['child'].id} cannot settle until {f['parent_label']} remembers an earlier wiggle moment.",
        f'Write a gentle story that includes a flashback, a funny bedtime line, and the word "wiggle".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent_label = f["parent_label"]
    comfort: Comfort = f["comfort"]
    qa = [
        QAItem(
            question=f"Who was wiggling at bedtime in the story?",
            answer=f"{child.id} was wiggling at bedtime in {world.room.name}.",
        ),
        QAItem(
            question=f"What did {parent_label} remember from before?",
            answer=f"{parent_label.capitalize()} remembered an earlier bedtime when {child.id} had wiggled so hard that the pillow slid like a little boat.",
        ),
        QAItem(
            question=f"How did {child.id} finally get calm?",
            answer=f"{child.id} calmed down by using {comfort.phrase} and following the bedtime routine with a slow, cozy tuck.",
        ),
        QAItem(
            question=f"What funny detail made the story humorous?",
            answer="The story joked that the toes were trying to dance without music, which was silly enough to make the pillow seem to giggle too.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story briefly remembers something that happened earlier, before the present moment.",
        ),
        QAItem(
            question="Why do bedtime routines help children settle?",
            answer="Bedtime routines help because the same calm steps, like tucking in and breathing slowly, tell the body it is safe to rest.",
        ),
        QAItem(
            question="What does wiggle mean?",
            answer="Wiggle means to move with small, quick little motions, like a squirmy knee or a wriggly toe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Mia", gender="girl", parent="mother", room="bedroom", comfort="blanket"),
    StoryParams(name="Noah", gender="boy", parent="father", room="nursery", comfort="stuffie"),
    StoryParams(name="Lily", gender="girl", parent="mother", room="bedroom", comfort="pillow"),
]


ASP_RULES = r"""
% A small bedtime story is valid when a room supports bedtime and a comfort object can settle wiggle.
supports(R, C) :- room(R), comfort(C), affords(R, bedtime), helps(C, wiggle).
valid_story(R, C) :- supports(R, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        for a in sorted(room.affords):
            lines.append(asp.fact("affords", rid, a))
    for cid, comfort in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        for h in sorted(comfort.helps):
            lines.append(asp.fact("helps", cid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(ROOMS[params.room], COMFORTS[params.comfort], params.name, params.gender, params.parent)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} valid bedtime combinations:")
        for room, comfort in combos:
            print(f"  {room:8} {comfort}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
            header = f"### {p.name}: {p.room} / {p.comfort}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
