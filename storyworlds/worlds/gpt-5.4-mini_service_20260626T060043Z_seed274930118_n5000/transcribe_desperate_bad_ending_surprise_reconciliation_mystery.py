#!/usr/bin/env python3
"""
A standalone storyworld for a small mystery domain.

Premise:
A child tries to transcribe clues from a strange little mystery, grows
desperate when the trail looks hopeless, then gets a surprise that turns the
story toward reconciliation instead of a bad ending.
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
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    mood: str
    hides: set[str] = field(default_factory=set)
    reveals: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    source: str
    truth: str
    misread_as: str


@dataclass
class StoryParams:
    place: str
    clue: str
    protagonist: str
    role: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        clone = World(self.place)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "label": v.label, "type": v.type,
            "owner": v.owner, "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
PLACES = {
    "quiet_library": Place(
        id="quiet_library",
        label="the quiet library",
        mood="dusty",
        hides={"echo", "footsteps"},
        reveals={"ink", "paper", "stamp"},
    ),
    "attic_room": Place(
        id="attic_room",
        label="the attic room",
        mood="dim",
        hides={"shadow", "scrape"},
        reveals={"dust", "box", "key"},
    ),
    "garden_shed": Place(
        id="garden_shed",
        label="the garden shed",
        mood="still",
        hides={"rustle", "whisper"},
        reveals={"rope", "chalk", "jar"},
    ),
}

CLUES = {
    "ink_note": Clue(
        id="ink_note",
        label="ink-smudged note",
        source="a torn notebook page",
        truth="someone had been copying names carefully",
        misread_as="someone was hiding a secret message",
    ),
    "tiny_key": Clue(
        id="tiny_key",
        label="tiny brass key",
        source="under a loose board",
        truth="it opened a small box of borrowed things",
        misread_as="it was a key to a locked mystery room",
    ),
    "blue_thread": Clue(
        id="blue_thread",
        label="blue thread",
        source="caught on a nail",
        truth="it matched a patched coat and a missing sleeve",
        misread_as="it proved a stranger had sneaked in",
    ),
}

NAMES = ["Mina", "Owen", "Pip", "Lena", "Toby", "June", "Ari", "Nia"]
ROLES = {
    "girl": ["girl", "daughter", "student"],
    "boy": ["boy", "son", "student"],
}

ASP_RULES = r"""
place(quiet_library).
place(attic_room).
place(garden_shed).

clue(ink_note).
clue(tiny_key).
clue(blue_thread).

hides(quiet_library,echo). hides(quiet_library,footsteps).
hides(attic_room,shadow). hides(attic_room,scrape).
hides(garden_shed,rustle). hides(garden_shed,whisper).

reveals(quiet_library,ink). reveals(quiet_library,paper). reveals(quiet_library,stamp).
reveals(attic_room,dust). reveals(attic_room,box). reveals(attic_room,key).
reveals(garden_shed,rope). reveals(garden_shed chalk). reveals(garden_shed,jar).

misread(ink_note,secret_message).
misread(tiny_key,locked_room).
misread(blue_thread,stranger).

truth(ink_note,copying_names).
truth(tiny_key,borrowed_things).
truth(blue_thread,patched_coat).

surprise(C) :- clue(C), truth(C,_).
reconciliation(C) :- clue(C), surprise(C).
bad_ending(C) :- clue(C), misread(C,_), not reconciliation(C).

#show surprise/1.
#show reconciliation/1.
#show bad_ending/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
        for h in sorted(p.hides):
            lines.append(asp.fact("hides", p.id, h))
        for r in sorted(p.reveals):
            lines.append(asp.fact("reveals", p.id, r))
    for c in CLUES.values():
        lines.append(asp.fact("clue", c.id))
        lines.append(asp.fact("misread", c.id, c.misread_as))
        lines.append(asp.fact("truth", c.id, c.truth))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show surprise/1.\n#show reconciliation/1.\n#show bad_ending/1."))
    atoms = {f"{sym.name}{tuple(a.name if hasattr(a, 'name') else a for a in sym.arguments)}" for sym in model}
    expected = set()
    for cid in CLUES:
        expected.add(f"surprise({cid!r})")
        expected.add(f"reconciliation({cid!r})")
    if atoms:
        print("OK: ASP program solves.")
        return 0
    print("ASP verification failed.")
    return 1


# ---------------------------------------------------------------------------
# Narrative
# ---------------------------------------------------------------------------
def _transcribe(world: World, hero: Entity, clue: Clue) -> None:
    hero.memes["focus"] = hero.memes.get("focus", 0) + 1
    hero.meters["notes"] = hero.meters.get("notes", 0) + 1
    world.say(
        f"{hero.id} sat with a small notebook and began to transcribe the {clue.label} by hand."
        f" The pages filled with neat lines, because {hero.pronoun('subject')} wanted every mark to stay exact."
    )


def _desperate(world: World, hero: Entity, clue: Clue) -> None:
    hero.memes["desperate"] = hero.memes.get("desperate", 0) + 1
    hero.memes["fear"] = hero.memes.get("fear", 0) + 1
    world.say(
        f"By late afternoon, {hero.id} felt desperate. The clue still pointed in circles,"
        f" and every copied line seemed to lead to another locked door."
    )


def _surprise(world: World, hero: Entity, clue: Clue) -> str:
    hero.memes["surprised"] = hero.memes.get("surprised", 0) + 1
    if clue.id == "ink_note":
        return "the library helper quietly admitted the page came from a class list, not a secret code"
    if clue.id == "tiny_key":
        return "the key fit a little box of returned pencils and scarves, not a hidden chamber"
    return "the blue thread matched a mended coat hanging on a hook, not a stranger's coat"
    

def _reconcile(world: World, hero: Entity, clue: Clue, reveal: str) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["fear"] = 0
    world.say(
        f"Then came a surprise: {reveal}. {hero.id} looked again and saw the truth in a kinder way."
        f" What had seemed like a bad ending was only a misunderstanding, and the people in the room"
        f" could finally reconcile over the real story."
    )
    world.say(
        f"{hero.id} closed the notebook at last. The final line was simple: the mystery was solved,"
        f" and the room felt warmer than before."
    )


def generate_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    clue = CLUES[params.clue]
    world = World(place)

    hero = world.add(Entity(id=params.protagonist, kind="character", type=params.role, label=params.role))
    helper = world.add(Entity(id="helper", kind="character", type="adult", label="the helper"))
    world.facts.update(hero=hero, helper=helper, clue=clue, place=place, params=params)

    world.say(
        f"{hero.id} wandered through {place.label}, where the air felt {place.mood} and every small sound seemed important."
        f" {hero.pronoun('subject').capitalize()} had come to solve a little mystery."
    )
    world.para()
    _transcribe(world, hero, clue)
    world.say(
        f"At first, {hero.id} thought the {clue.label} meant {clue.misread_as}."
        f" That guess made the notebook page feel heavier."
    )
    world.para()
    _desperate(world, hero, clue)
    world.say(
        f"{hero.id} almost feared a bad ending, because the trail looked tangled and lonely."
    )
    world.para()
    reveal = _surprise(world, hero, clue)
    _reconcile(world, hero, clue, reveal)
    world.facts["surprise_reveal"] = reveal
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    clue: Clue = world.facts["clue"]
    place: Place = world.facts["place"]
    return [
        f'Write a child-friendly mystery story set in {place.label} that includes the word "transcribe".',
        f"Tell a short story where {p.protagonist} feels desperate about the {clue.label} and then learns the truth.",
        f"Write a mystery with a surprise, a mistaken bad ending, and a gentle reconciliation at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    clue: Clue = world.facts["clue"]
    place: Place = world.facts["place"]
    reveal = world.facts["surprise_reveal"]
    return [
        QAItem(
            question=f"Where did {p.protagonist} look for clues?",
            answer=f"{p.protagonist} looked for clues in {place.label}, where the story felt quiet and a little mysterious.",
        ),
        QAItem(
            question=f"What did {p.protagonist} try to do with the clue?",
            answer=f"{p.protagonist} tried to transcribe the {clue.label} carefully into a notebook.",
        ),
        QAItem(
            question=f"Why did the story feel desperate for a while?",
            answer=(
                f"It felt desperate because the clue seemed to point toward {clue.misread_as},"
                f" so the mystery looked as if it might end badly before the truth was found."
            ),
        ),
        QAItem(
            question="What was the surprise?",
            answer=f"The surprise was that {reveal}.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with reconciliation: the misunderstanding cleared up, the people calmed down, and the mystery was solved kindly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to transcribe something?",
            answer="To transcribe something means to copy spoken words or marks carefully into writing.",
        ),
        QAItem(
            question="What does desperate mean?",
            answer="Desperate means feeling very worried and willing to try hard because something feels urgent or hard to fix.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that happens when you did not know it was coming.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset and make peace again.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzling problem with clues that help someone figure out what is really true.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with transcription, desperation, surprise, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--role", choices=["girl", "boy"])
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
    place = args.place or rng.choice(list(PLACES))
    clue = args.clue or rng.choice(list(CLUES))
    role = args.role or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, clue=clue, protagonist=name, role=role)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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
        print(asp_program("#show surprise/1.\n#show reconciliation/1.\n#show bad_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [(p, c, n, r) for p in PLACES for c in CLUES for n in NAMES[:3] for r in ["girl", "boy"]]
        for i, (p, c, n, r) in enumerate(combos[: max(1, args.n)]):
            params = StoryParams(place=p, clue=c, protagonist=n, role=r, seed=base_seed + i)
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
