#!/usr/bin/env python3
"""
storyworlds/worlds/small_conflict_curiosity_rhyme_whodunit.py
=============================================================

A tiny whodunit-flavored storyworld for child-facing mystery stories.

Seed tale:
---
At the small house, a little brass bell kept vanishing from the shelf.
Nia, who loved rhymes, thought the clues sounded funny.
Every time the bell was missing, a line of verse turned up nearby.
Nia and her friend Bea searched the kitchen, the hall, and the garden gate.
They argued about who could be moving the bell, until they noticed the
rhymes always pointed to a place where someone wanted quiet.
In the end they found the bell under a cushion in the reading nook.
The cat had been hiding there to nap, and the bell kept getting moved.
Nia stopped the arguing, laughed, and made a rhyme for the cat instead.

World idea:
- A small mystery with a single missing object.
- Curiosity drives clues; conflict rises when suspects are blamed.
- Rhyme is a real signal in the world: clue cards, notes, and answers rhyme.
- The resolution is a causal reveal, not a frozen recap.

The storyworld uses typed entities with physical meters and emotional memes.
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
    tucked: bool = False
    noisy: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "cat"}
        male = {"boy", "father", "dad", "man", "dog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    rooms: list[str]
    quiet_spots: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing: str
    object_label: str
    object_phrase: str
    rhyme_word: str
    clue_rhyme: str
    clue_place: str
    reveal_place: str
    reason: str
    conflict_word: str
    curiosity_word: str


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    plausible_reason: str
    hush_reason: str
    rhyme_tag: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_rhyme_points(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("note_reveals") and "note" not in world.fired:
        world.fired.add(("note",))
        note = world.get("note")
        note.meters["found"] = 1
        out.append(f"The rhyme on the note pointed straight at a quiet place.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for e in world.children():
        if e.memes.get("blame", 0) >= THRESHOLD and e.memes.get("tension", 0) < THRESHOLD:
            e.memes["tension"] = 1
            out.append(f"The guessing made everyone feel cross.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_rhyme_points, _r_conflict):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_hiding(world: World, mystery: Mystery) -> str:
    sim = world.copy()
    box = sim.get("object")
    if sim.facts.get("rhyme_hint") and sim.facts.get("quiet_spot"):
        box.meters["found"] = 1
        return sim.facts["quiet_spot"]
    return mystery.reveal_place


SETTING = Setting(
    place="the small house",
    rooms=["kitchen", "hall", "garden gate", "reading nook"],
    quiet_spots={"reading nook"},
)

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        missing="bell",
        object_label="little brass bell",
        object_phrase="a little brass bell",
        rhyme_word="bell",
        clue_rhyme="When the bell was gone, the clue said, 'Think of the place that likes a hush.'",
        clue_place="the reading nook",
        reveal_place="the reading nook",
        reason="the cat liked quiet and warm cushions",
        conflict_word="blame",
        curiosity_word="curious",
    ),
    "spoon": Mystery(
        id="spoon",
        missing="spoon",
        object_label="silver spoon",
        object_phrase="a silver spoon",
        rhyme_word="moon",
        clue_rhyme="The line rhymed with 'moon' and pointed to the room where snacks were kept soon.",
        clue_place="the kitchen",
        reveal_place="the kitchen",
        reason="someone had left it beside the tea tin",
        conflict_word="guessing",
        curiosity_word="wondering",
    ),
}

SUSPECTS = {
    "cat": Suspect("cat", "the cat", "cat", "wanted a quiet nap", "could not explain itself", "mat"),
    "dog": Suspect("dog", "the dog", "dog", "wanted a noisy chew", "had muddy paws", "log"),
    "twin": Suspect("twin", "the twin", "girl", "was borrowing things", "hid behind a chair", "thin"),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for mid in MYSTERIES:
        for sid in SUSPECTS:
            combos.append((mid, sid, "small"))
    return combos


@dataclass
class StoryParams:
    mystery: str
    suspect: str
    size: str = "small"
    name: str = "Nia"
    friend: str = "Bea"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rhyming whodunit storyworld.")
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--size", choices=["small"], default="small")
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
    if args.mystery and args.suspect:
        if (args.mystery, args.suspect, "small") not in valid_combos():
            raise StoryError("No reasonable small whodunit matches those choices.")
    combos = [c for c in valid_combos()
              if (args.mystery is None or c[0] == args.mystery)
              and (args.suspect is None or c[1] == args.suspect)]
    if not combos:
        raise StoryError("No reasonable small whodunit matches those choices.")
    mystery, suspect, size = rng.choice(sorted(combos))
    return StoryParams(
        mystery=mystery,
        suspect=suspect,
        size=size,
        name=args.name or rng.choice(["Nia", "Lena", "Milo", "June"]),
        friend=args.friend or rng.choice(["Bea", "Ollie", "Pip", "Tess"]),
    )


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type="girl", label=params.name))
    friend = world.add(Entity(id=params.friend, kind="character", type="girl", label=params.friend))
    mystery = MYSTERIES[params.mystery]
    suspect = SUSPECTS[params.suspect]
    missing = world.add(Entity(id="object", type="thing", label=mystery.object_label, phrase=mystery.object_phrase))
    note = world.add(Entity(id="note", type="thing", label="rhyme note", phrase="a rhyme note"))
    culprit = world.add(Entity(id="culprit", type=suspect.type, label=suspect.label, phrase=suspect.label))
    world.facts.update(mystery=mystery, suspect=suspect, hero=hero, friend=friend, object=missing, note=note)

    hero.memes["curiosity"] = 1
    friend.memes["curiosity"] = 1
    world.say(f"At {SETTING.place}, {hero.id} noticed that {mystery.object_phrase} had vanished.")
    world.say(f"{friend.id} listened, and the missing thing made the whole room feel like a small mystery.")
    world.say(f"Then a note appeared: {mystery.clue_rhyme}")
    world.para()
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.facts["rhyme_hint"] = True
    world.facts["quiet_spot"] = mystery.clue_place
    world.say(f"{hero.id} wanted to solve it, but {friend.id} started blaming {suspect.label}.")
    culprit.memes["blame"] = 1
    hero.memes["tension"] = 0
    friend.memes["tension"] = 0
    propagate(world, narrate=True)
    world.para()
    world.say(f"{hero.id} kept looking, because {mystery.curiosity_word} was stronger than the arguing.")
    world.say(f"The clue fit a place that liked hush, so they searched {mystery.reveal_place}.")
    found_where = predict_hiding(world, mystery)
    missing.meters["found"] = 1
    world.say(f"Under a cushion in {found_where}, they found the {mystery.object_label}.")
    world.say(f"The {suspect.label} was innocent in the end: it had only wanted {mystery.reason}.")
    world.say(f"{hero.id} stopped the conflict and made a rhyme for the {suspect.label} instead.")
    world.facts["resolved"] = True
    world.facts["found_where"] = found_where
    return world


def generation_prompts(world: World) -> list[str]:
    m = world.facts["mystery"]
    s = world.facts["suspect"]
    h = world.facts["hero"]
    return [
        f"Write a small whodunit for a child where {h.id} solves a rhyme clue about a missing {m.object_label}.",
        f"Tell a short mystery where the clue rhymes, the guessing causes conflict, and the ending reveals why {s.label} was near the {m.object_label}.",
        f"Write a gentle detective story with curiosity, rhyme, and a small family-space mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    m = world.facts["mystery"]
    s = world.facts["suspect"]
    h = world.facts["hero"]
    f = world.facts["friend"]
    return [
        QAItem(
            question=f"What was missing in the story?",
            answer=f"The missing thing was {m.object_phrase}. It kept the small house feeling puzzled until the clue was followed.",
        ),
        QAItem(
            question=f"Who did {f.id} blame before the mystery was solved?",
            answer=f"{f.id} blamed {s.label}. That caused a little conflict, but the rhyme clue showed the blaming was wrong.",
        ),
        QAItem(
            question=f"Where did {h.id} finally find the missing object?",
            answer=f"{h.id} found it in {world.facts['found_where']}. That quiet place matched the clue and ended the search.",
        ),
        QAItem(
            question=f"Why was the {s.label} near the missing {m.object_label}?",
            answer=f"{s.label} was near it because {m.reason}. It was looking for a soft, quiet place instead of trying to hide anything badly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps you solve a mystery.",
        ),
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes you want to look, ask questions, and learn what is going on.",
        ),
        QAItem(
            question="Why do rhymes help in a mystery?",
            answer="Rhymes can make clues easier to remember, and sometimes the words point to the right place.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(sample.prompts)
    parts.append("")
    parts.append("== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(M,S) :- mystery(M), suspect(S).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(str(e))
        return 1
    model = asp.one_model(asp_program("#show valid/2."))
    atoms = sorted(set(asp.atoms(model, "valid")))
    py = sorted((m, s) for m in MYSTERIES for s in SUSPECTS)
    ok = atoms == py
    print("OK" if ok else "MISMATCH")
    return 0 if ok else 1


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


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for m in MYSTERIES:
            for s in SUSPECTS:
                samples.append(generate(StoryParams(mystery=m, suspect=s, name="Nia", friend="Bea")))
    else:
        i = 0
        while len(samples) < args.n and i < 50:
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
