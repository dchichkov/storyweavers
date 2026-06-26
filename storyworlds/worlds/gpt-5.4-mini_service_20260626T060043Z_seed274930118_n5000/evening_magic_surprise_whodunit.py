#!/usr/bin/env python3
"""
storyworlds/worlds/evening_magic_surprise_whodunit.py
======================================================

A small storyworld about an evening whodunit with a touch of magic and a
surprise reveal.

Premise:
- At an evening gathering, something important goes missing.
- The characters inspect clues, notice odd magic, and reason about who could
  have moved what.
- A surprise truth turns the case from suspicion into a gentle reveal.

This world keeps the narrative small and state-driven:
- physical meters track facts like carried, hidden, glowing, locked, muddy
- emotional memes track worry, curiosity, relief, suspicion, trust

The ending should always prove what changed: the missing thing is found, the
odd magic is explained, and the evening ends with calm instead of confusion.
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
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    locked: bool = False
    glowing: bool = False
    suspicious: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    name: str
    evening_detail: str
    affords_magic: bool = True


@dataclass
class Clue:
    id: str
    label: str
    reveal: str
    points_to: str


@dataclass
class Trick:
    id: str
    label: str
    effect: str
    disguise: str
    method: str


@dataclass
class StoryParams:
    room: str
    missing: str
    culprit: str
    finder: str
    witness: str
    trick: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
ROOMS = {
    "parlor": Room("the parlor", "The lamplight made the curtains look golden."),
    "garden": Room("the garden", "The bushes held the last warm color of day."),
    "hall": Room("the hall", "The long hallway was quiet except for a tiny creak."),
}

MISSING = {
    "silver_key": Entity(
        id="silver_key",
        type="thing",
        label="silver key",
        phrase="a tiny silver key",
    ),
    "music_box": Entity(
        id="music_box",
        type="thing",
        label="music box",
        phrase="a little music box with a star on top",
    ),
    "lantern": Entity(
        id="lantern",
        type="thing",
        label="lantern",
        phrase="a round lantern with a glass face",
    ),
}

CHARACTERS = {
    "Mira": {"type": "girl", "traits": ["careful", "curious"]},
    "Ned": {"type": "boy", "traits": ["quiet", "watchful"]},
    "Iris": {"type": "girl", "traits": ["smart", "gentle"]},
    "Bram": {"type": "boy", "traits": ["patient", "kind"]},
}

TRICKS = {
    "glimmer_dust": Trick(
        id="glimmer_dust",
        label="glimmer dust",
        effect="left a sparkle trail",
        disguise="a smear of gold dust",
        method="broke open a little paper star",
    ),
    "mirror_bell": Trick(
        id="mirror_bell",
        label="mirror bell",
        effect="made the key ring from nowhere",
        disguise="a soft bell note",
        method="tapped the lamp twice",
    ),
    "moon_thread": Trick(
        id="moon_thread",
        label="moon thread",
        effect="tied the hidden thing to a ribbon of light",
        disguise="a pale silver string",
        method="whispered to the shadows",
    ),
}

CLUES = {
    "sparkle": Clue(
        id="sparkle",
        label="sparkles on the floor",
        reveal="They showed that something magical had been used nearby.",
        points_to="trick",
    ),
    "dust": Clue(
        id="dust",
        label="gold dust on a sleeve",
        reveal="The dust matched the trick that left a trail.",
        points_to="culprit",
    ),
    "ring": Clue(
        id="ring",
        label="a tiny ringing sound",
        reveal="It meant the missing thing had not been lost forever.",
        points_to="hidden_place",
    ),
}

# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------
class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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

        clone = World(self.room)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def _apply_magic(world: World, culprit: Entity, missing: Entity, trick: Trick) -> None:
    """A tiny whodunit twist: the culprit uses a trick to hide the missing item."""
    sig = f"magic:{missing.id}:{trick.id}"
    if sig in world.fired:
        return
    world.fired.add(sig)
    culprit.meters["magic_used"] = culprit.meters.get("magic_used", 0.0) + 1
    culprit.memes["nervous"] = culprit.memes.get("nervous", 0.0) + 1
    missing.glowing = True
    missing.hidden_in = "shadow_box"
    missing.suspicious = True


def _detect_clues(world: World, finder: Entity, witness: Entity, missing: Entity, trick: Trick) -> list[str]:
    out: list[str] = []
    finder.memes["curiosity"] = finder.memes.get("curiosity", 0.0) + 1
    witness.memes["worry"] = witness.memes.get("worry", 0.0) + 1

    if missing.hidden_in:
        out.append(f"{finder.id} noticed a faint glow near the skirting board.")
        out.append("The glow left sparkles on the floor, like someone had sprinkled tiny stars.")
        out.append(f"{witness.id} pointed out a little clue: {CLUES['sparkle'].label}.")
    if trick.id == "glimmer_dust":
        out.append(f"A gold speck clung to {world.get(culprit_id(world)).id}'s sleeve.")
        out.append(f"The dust matched the {trick.label} trick.")
    elif trick.id == "mirror_bell":
        out.append("A tiny ringing sound came from behind a curtain.")
        out.append("That meant the missing thing was still close by.")
    else:
        out.append("A pale thread of light led toward a shut toy box.")
        out.append("The line of light looked like a clue only magic could make.")

    return out


def culprit_id(world: World) -> str:
    return str(world.facts["culprit_id"])


def hide_place_for_trick(trick_id: str) -> str:
    return {
        "glimmer_dust": "a shadowy toy box",
        "mirror_bell": "behind the lamp table",
        "moon_thread": "under the ribbon basket",
    }[trick_id]


def begin_story(world: World, finder: Entity, witness: Entity, missing: Entity) -> None:
    world.say(
        f"By evening, {finder.id} was in {world.room.name}, and the room had gone very quiet."
    )
    world.say(
        f"{finder.id} had been looking for {missing.label}, but it was nowhere on the shelf."
    )
    world.say(
        f"{witness.id} saw the empty spot too, and that made the whole room feel like a puzzle."
    )


def suspect_and_search(world: World, finder: Entity, witness: Entity, culprit: Entity,
                       missing: Entity, trick: Trick) -> None:
    world.para()
    world.say(
        f"{finder.id} and {witness.id} searched under chairs, beside cushions, and behind the curtain."
    )
    world.say(
        f"{finder.id} felt curious, but also a little suspicious, because the air still seemed to sparkle."
    )
    world.say(
        f"{witness.id} said, \"Someone here knows where it went.\""
    )
    _apply_magic(world, culprit, missing, trick)
    for line in _detect_clues(world, finder, witness, missing, trick):
        world.say(line)


def reveal_and_resolve(world: World, finder: Entity, witness: Entity, culprit: Entity,
                       missing: Entity, trick: Trick) -> None:
    world.para()
    hidden_place = hide_place_for_trick(trick.id)
    missing.hidden_in = hidden_place
    missing.carried_by = culprit.id
    missing.glowing = False
    culprit.memes["nervous"] = max(0.0, culprit.memes.get("nervous", 0.0) - 1)
    culprit.memes["relief"] = culprit.memes.get("relief", 0.0) + 1

    world.say(
        f"At last, {finder.id} opened the little box and found {missing.phrase} tucked inside."
    )
    world.say(
        f"{culprit.id} admitted the surprise: {trick.label} had made it vanish for a game, not a theft."
    )
    world.say(
        f"{witness.id} laughed, because the mystery had looked serious, but the answer was playful."
    )
    world.say(
        f"By the end of the evening, everyone could see {missing.label} again, and the room felt bright and calm."
    )


def tell_story(params: StoryParams) -> World:
    room = ROOMS[params.room]
    world = World(room)

    finder = world.add(Entity(id=params.finder, kind="character", type=CHARACTERS[params.finder]["type"]))
    witness = world.add(Entity(id=params.witness, kind="character", type=CHARACTERS[params.witness]["type"]))
    culprit = world.add(Entity(id=params.culprit, kind="character", type=CHARACTERS[params.culprit]["type"]))
    missing_base = MISSING[params.missing]
    missing = world.add(Entity(
        id=missing_base.id,
        kind="thing",
        type=missing_base.type,
        label=missing_base.label,
        phrase=missing_base.phrase,
        owner=culprit.id,
    ))
    trick = TRICKS[params.trick]

    world.facts.update(
        room=params.room,
        missing=params.missing,
        culprit_id=params.culprit,
        finder_id=params.finder,
        witness_id=params.witness,
        trick_id=params.trick,
        hidden_place=hide_place_for_trick(params.trick),
    )

    begin_story(world, finder, witness, missing)
    suspect_and_search(world, finder, witness, culprit, missing, trick)
    reveal_and_resolve(world, finder, witness, culprit, missing, trick)

    world.facts["resolved"] = True
    world.facts["missing_found"] = True
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A missing thing is hidden if magic has been used on it.
hidden(M) :- missing(M), magic_used(M).

% A clue can point to the trick, the culprit, or the hidden place.
answer(trick) :- hidden(_), clue(sparkle).
answer(culprit) :- clue(dust), magic_used(_).
answer(hidden_place) :- clue(ring), hidden(_).

% A valid whodunit must have an evening room, a missing item, a culprit,
% a finder, a witness, and a magical surprise that resolves the mystery.
valid_story(R, M, C, F, W, T) :-
    room(R), evening(R),
    missing(M), culprit(C), finder(F), witness(W), trick(T),
    clue(sparkle), clue(dust), clue(ring).

#show valid_story/6.
#show answer/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        lines.append(asp.fact("evening", rid))
        if room.affords_magic:
            lines.append(asp.fact("magic_room", rid))
    for mid in MISSING:
        lines.append(asp.fact("missing", mid))
    for cid in CHARACTERS:
        lines.append(asp.fact("character", cid))
    for tid in TRICKS:
        lines.append(asp.fact("trick", tid))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/6.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/6."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    try:
        from storyworlds import asp as aspmod  # type: ignore
    except Exception:
        import asp as aspmod  # noqa: F401
    stories = asp_valid_stories()
    py = valid_combos()
    py_set = set(py)
    asp_set = set(stories)
    if asp_set == py_set:
        print(f"OK: ASP gate matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    if asp_set - py_set:
        print("  only in ASP:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in Python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Parameter helpers
# ---------------------------------------------------------------------------
@dataclass
class StoryChoice:
    room: str
    missing: str
    culprit: str
    finder: str
    witness: str
    trick: str


def valid_combos() -> list[tuple[str, str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str, str]] = []
    for room in ROOMS:
        for missing in MISSING:
            for culprit in CHARACTERS:
                for finder in CHARACTERS:
                    if finder == culprit:
                        continue
                    for witness in CHARACTERS:
                        if witness in {culprit, finder}:
                            continue
                        for trick in TRICKS:
                            combos.append((room, missing, culprit, finder, witness, trick))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Evening magic surprise whodunit.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--missing", choices=MISSING)
    ap.add_argument("--culprit", choices=CHARACTERS)
    ap.add_argument("--finder", choices=CHARACTERS)
    ap.add_argument("--witness", choices=CHARACTERS)
    ap.add_argument("--trick", choices=TRICKS)
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
    combos = valid_combos()
    filtered = []
    for c in combos:
        room, missing, culprit, finder, witness, trick = c
        if args.room and room != args.room:
            continue
        if args.missing and missing != args.missing:
            continue
        if args.culprit and culprit != args.culprit:
            continue
        if args.finder and finder != args.finder:
            continue
        if args.witness and witness != args.witness:
            continue
        if args.trick and trick != args.trick:
            continue
        filtered.append(c)
    if not filtered:
        raise StoryError("No valid whodunit matches the given options.")
    room, missing, culprit, finder, witness, trick = rng.choice(filtered)
    return StoryParams(room=room, missing=missing, culprit=culprit, finder=finder, witness=witness, trick=trick)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short evening whodunit for a child, with magic and a surprise, set in {ROOMS[f["room"]].name}.',
        f"Tell a gentle mystery where {f['finder_id']} looks for {MISSING[f['missing']].label} and learns why it vanished.",
        f"Write a story that starts with an empty spot, includes a magical clue, and ends with a surprise explanation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    missing = MISSING[f["missing"]]
    room = ROOMS[f["room"]]
    culprit = f["culprit_id"]
    finder = f["finder_id"]
    witness = f["witness_id"]
    trick = TRICKS[f["trick_id"]]
    return [
        QAItem(
            question=f"What was missing in {room.name}?",
            answer=f"{missing.phrase} was missing, and that made the evening feel like a puzzle.",
        ),
        QAItem(
            question=f"Who looked for {missing.label}?",
            answer=f"{finder} looked for {missing.label} while {witness} watched for clues.",
        ),
        QAItem(
            question=f"What magical surprise explained the mystery?",
            answer=f"The surprise was {trick.label}. It did not mean harm; it only made {missing.label} seem to disappear.",
        ),
        QAItem(
            question=f"Who had caused the mystery?",
            answer=f"{culprit} had used the trick, but only for a playful surprise, not to steal anything.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small bit of information that helps solve a mystery.",
        ),
        QAItem(
            question="What does evening mean?",
            answer="Evening is the part of the day after afternoon, when the light grows softer.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic in a story is something special that can do surprising things.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.locked:
            bits.append("locked=True")
        if e.glowing:
            bits.append("glowing=True")
        if e.suspicious:
            bits.append("suspicious=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for i, combo in enumerate(valid_combos()):
            if i >= args.n:
                break
            params = StoryParams(*combo)
            params.seed = base_seed + i
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
