#!/usr/bin/env python3
"""
A standalone storyworld script for a tiny whodunit: a cordoned scene, a visible
magic clue, and a child-safe mystery that gets solved by careful looking.
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    visible: bool = False
    cordoned: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "detective"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    name: str
    cordoned: bool = True
    visible_magic: bool = True
    clues: list[str] = field(default_factory=list)


@dataclass
class World:
    room: Room
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
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
        import copy
        clone = World(Room(self.room.name, self.room.cordoned, self.room.visible_magic, list(self.room.clues)))
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Parameters / registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    room: str
    culprit: str
    magician: str
    detective: str
    seed: Optional[int] = None


ROOMS = {
    "hall": Room(name="the hall", cordoned=True, visible_magic=True),
    "museum": Room(name="the museum room", cordoned=True, visible_magic=True),
    "garden": Room(name="the garden path", cordoned=True, visible_magic=True),
}

CULPRITS = {
    "cat": ("cat", "a sneaky cat", "pawprints"),
    "bird": ("bird", "a bright bird", "feathers"),
    "rabbit": ("rabbit", "a white rabbit", "crumbs"),
}

MAGICIANS = [
    ("Mina", "girl"),
    ("Theo", "boy"),
    ("Poppy", "girl"),
    ("Ben", "boy"),
]

DETECTIVES = [
    ("Dot", "girl"),
    ("Max", "boy"),
    ("Ivy", "girl"),
    ("Noah", "boy"),
]

TRAITS = ["curious", "careful", "brave", "patient"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A room is a mystery scene when it is cordoned and has visible magic clues.
scene(R) :- room(R), cordoned(R), visible_magic(R).

% A culprit is plausible when it leaves a clue that can be noticed.
plausible(C) :- culprit(C), clue(C, _).

% The mystery is solved when a detective sees a clue, names the culprit, and
% the scene has at least one visible magical sign.
solved(R, C) :- scene(R), culprit(C), clue(C, _), visible(C), detective(D), solved_by(D, C).

#show scene/1.
#show plausible/1.
#show solved/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        if room.cordoned:
            lines.append(asp.fact("cordoned", rid))
        if room.visible_magic:
            lines.append(asp.fact("visible_magic", rid))
    for cid, (_, _, clue) in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        lines.append(asp.fact("clue", cid, clue))
        lines.append(asp.fact("visible", cid))
    for name, _ in MAGICIANS:
        lines.append(asp.fact("magician", name))
    for name, _ in DETECTIVES:
        lines.append(asp.fact("detective", name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_solve_atoms(show: str) -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show))
    return model


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show scene/1. #show plausible/1. #show solved/2."))
    scenes = set(asp.atoms(model, "scene"))
    plausible = set(asp.atoms(model, "plausible"))
    solved = set(asp.atoms(model, "solved"))
    py = set(valid_signatures())
    asp_set = {(r,) for (r,) in scenes}
    if not asp_set:
        print("MISMATCH: no scenes found")
        return 1
    if not plausible:
        print("MISMATCH: no plausible culprits found")
        return 1
    if not solved:
        print("MISMATCH: no solved facts found")
        return 1
    print("OK: ASP facts are present and parse correctly.")
    return 0


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_signatures() -> list[tuple[str, str, str]]:
    out = []
    for room_id, room in ROOMS.items():
        if not room.cordoned or not room.visible_magic:
            continue
        for cid, (_, _, clue) in CULPRITS.items():
            out.append((room_id, cid, clue))
    return out


def explain_invalid(room_id: str) -> str:
    room = ROOMS[room_id]
    if not room.cordoned:
        return "(No story: the scene needs a cordon so the mystery feels like a real whodunit.)"
    if not room.visible_magic:
        return "(No story: the magic clue must be visible, or there is nothing fair to notice and solve.)"
    return "(No story: this setup is not usable.)"


# ---------------------------------------------------------------------------
# Narrative
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    room = ROOMS[params.room]
    world = World(room=Room(room.name, room.cordoned, room.visible_magic, list(room.clues)))

    detective_name, detective_type = params.detective, "girl" if params.detective in {"Dot", "Ivy"} else "boy"
    magician_name, magician_type = params.magician, "girl" if params.magician in {"Mina", "Poppy"} else "boy"
    culprit_type, culprit_label, clue = CULPRITS[params.culprit]

    detective = world.add(Entity(
        id=detective_name, kind="character", type=detective_type,
        label=detective_name, role="detective",
        meters={"steps": 0.0, "focus": 0.0}, memes={"curiosity": 1.0, "calm": 1.0}
    ))
    magician = world.add(Entity(
        id=magician_name, kind="character", type=magician_type,
        label=magician_name, role="magician",
        meters={"sparkles": 0.0}, memes={"nervousness": 0.0}
    ))
    culprit = world.add(Entity(
        id=params.culprit, kind="character", type=culprit_type,
        label=culprit_label, role="culprit",
        visible=True, meters={"clue": 1.0}, memes={"mischief": 1.0}
    ))
    clue_obj = world.add(Entity(
        id="clue", kind="thing", type="thing",
        label=clue, phrase=f"a {clue} that was easy to see", visible=True,
        meters={"shine": 1.0}
    ))

    world.facts.update(
        room_id=params.room,
        detective=detective,
        magician=magician,
        culprit=culprit,
        clue_obj=clue_obj,
        clue_word=clue,
        room=world.room,
    )

    # Act 1
    world.say(
        f"In {world.room.name}, a yellow cordon stood around the center of the floor, "
        f"and the magic clue was visible to everyone."
    )
    world.say(
        f"{detective.id} was a careful little detective who loved a good mystery."
    )
    world.say(
        f"{magician.id} had set a tiny trick in the room, but now {magician.pronoun('possessive')} eyes were wide."
    )

    # Act 2
    world.para()
    world.say(
        f"{detective.id} stepped slowly around the cordon, looking at the shiny clue."
    )
    detective.meters["steps"] += 3
    detective.meters["focus"] += 1
    detective.memes["curiosity"] += 1

    world.say(
        f"The clue was so visible that {detective.id} could point at it without guessing."
    )
    world.say(
        f"{detective.id} asked, “Who made this little magic mess?”"
    )
    world.say(
        f"{magician.id} pointed toward {culprit.label}. That was the part that made the mystery turn."
    )
    magician.meters["sparkles"] += 1
    magician.memes["nervousness"] += 1

    # Act 3
    world.para()
    world.say(
        f"{detective.id} matched the {clue} to {culprit.label}, and the answer felt neat and true."
    )
    culprit.memes["mischief"] = 0.0
    detective.memes["calm"] += 1
    detective.meters["focus"] += 1

    world.say(
        f"The cordon stayed in place until the room was safe to open again."
    )
    world.say(
        f"At the end, the visible magic clue had done its job, and the whodunit was solved."
    )

    world.facts["solved"] = True
    world.facts["culprit_id"] = params.culprit
    return world


# ---------------------------------------------------------------------------
# Storyworld interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny cordoned whodunit with visible magic clues.")
    ap.add_argument("--room", choices=sorted(ROOMS))
    ap.add_argument("--culprit", choices=sorted(CULPRITS))
    ap.add_argument("--magician", choices=[n for n, _ in MAGICIANS])
    ap.add_argument("--detective", choices=[n for n, _ in DETECTIVES])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    if room not in ROOMS:
        raise StoryError("Unknown room.")
    if not ROOMS[room].cordoned or not ROOMS[room].visible_magic:
        raise StoryError(explain_invalid(room))
    culprit = args.culprit or rng.choice(list(CULPRITS))
    magician = args.magician or rng.choice([n for n, _ in MAGICIANS])
    detective = args.detective or rng.choice([n for n, _ in DETECTIVES])
    return StoryParams(room=room, culprit=culprit, magician=magician, detective=detective)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a young child set in {f["room"].name} with a visible magic clue.',
        f"Tell a mystery story where {f['detective'].id} solves who caused the clue in {f['room'].name}.",
        "Write a gentle story with a cordon, a visible clue, and a solved mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    culprit = f["culprit"]
    room = f["room"]
    clue = f["clue_word"]
    return [
        QAItem(
            question=f"Where did the mystery happen?",
            answer=f"It happened in {room.name}, where a cordon kept the scene neat and easy to inspect."
        ),
        QAItem(
            question=f"What clue did {detective.id} see?",
            answer=f"{detective.id} saw a {clue} that was visible right inside the cordoned scene."
        ),
        QAItem(
            question=f"Who solved the whodunit?",
            answer=f"{detective.id} solved it by matching the clue to {culprit.label}."
        ),
        QAItem(
            question=f"Why was the clue useful?",
            answer=f"It was useful because it was visible, so {detective.id} could notice it and figure out who caused the trouble."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cordon?",
            answer="A cordon is a line or barrier that keeps people back from a place so it can stay safe or undisturbed."
        ),
        QAItem(
            question="What does visible mean?",
            answer="Visible means something can be seen with your eyes."
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where the main question is who did it."
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks carefully at clues and asks questions to solve a mystery."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.visible:
            bits.append("visible=True")
        if e.cordoned:
            bits.append("cordoned=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) " + " ".join(bits))
    lines.append(f"  room: {world.room.name} visible_magic={world.room.visible_magic} cordoned={world.room.cordoned}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(room="hall", culprit="cat", magician="Mina", detective="Dot"),
    StoryParams(room="museum", culprit="bird", magician="Theo", detective="Ivy"),
    StoryParams(room="garden", culprit="rabbit", magician="Poppy", detective="Max"),
]


def asp_verify_program() -> int:
    import asp
    model = asp.one_model(asp_program("#show scene/1. #show plausible/1. #show solved/2."))
    scenes = asp.atoms(model, "scene")
    plausible = asp.atoms(model, "plausible")
    solved = asp.atoms(model, "solved")
    if not scenes or not plausible or not solved:
        print("MISMATCH: ASP reasoning did not produce the expected atoms.")
        return 1
    print("OK: ASP reasoning produced scene/plausible/solved atoms.")
    return 0


def build_valid_combo_list() -> list[tuple[str, str, str]]:
    return valid_signatures()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show scene/1. #show plausible/1. #show solved/2."))
        return
    if args.verify:
        sys.exit(asp_verify_program())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show scene/1. #show plausible/1. #show solved/2."))
        print("scene:", sorted(set(asp.atoms(model, "scene"))))
        print("plausible:", sorted(set(asp.atoms(model, "plausible"))))
        print("solved:", sorted(set(asp.atoms(model, "solved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.detective} in {p.room} / culprit={p.culprit}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
