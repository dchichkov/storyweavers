#!/usr/bin/env python3
"""
A small adventure story world about curiosity, media, problem solving, moral
choice, and a little rhyme.

Seed tale idea:
- A curious child finds a broken piece of media that carries a message.
- The message is hard to hear, so the child must solve a practical problem.
- The child must also choose a moral path: share the truth instead of hiding it.
- The ending includes a rhyming beat and a clear change in the world state.

The world is intentionally tiny: one child, one helper, one media object, one
obstacle, one repair path, one moral turn.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class MediaItem:
    id: str
    label: str
    phrase: str
    type: str
    problem: str
    fix: str
    moral: str
    rhyme: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    media: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


PLACES = {
    "attic": Place(id="attic", label="the attic", indoor=True, affords={"search"}),
    "dock": Place(id="dock", label="the dock", indoor=False, affords={"search"}),
    "camp": Place(id="camp", label="the camp trail", indoor=False, affords={"search"}),
}

MEDIA = {
    "radio": MediaItem(
        id="radio",
        label="radio",
        phrase="an old radio with a bent antenna",
        type="radio",
        problem="static",
        fix="straighten the antenna",
        moral="share the message",
        rhyme="bright",
        tags={"media", "sound", "curiosity"},
    ),
    "comic": MediaItem(
        id="comic",
        label="comic",
        phrase="a rain-speckled comic book",
        type="comic",
        problem="torn pages",
        fix="carefully tape the pages",
        moral="tell the truth",
        rhyme="tight",
        tags={"media", "reading", "curiosity"},
    ),
    "camera": MediaItem(
        id="camera",
        label="camera",
        phrase="a small camera with a scratched lens",
        type="camera",
        problem="blurry picture",
        fix="wipe the lens clean",
        moral="share the photo",
        rhyme="light",
        tags={"media", "images", "curiosity"},
    ),
}

HELPER_LINES = {
    "mother": "His mother smiled and stayed nearby like a steady guide.",
    "father": "His father nodded and helped like a calm trail guide.",
}

TRAITS = ["curious", "brave", "careful", "lively", "thoughtful"]
GIRL_NAMES = ["Mia", "Luna", "Nora", "Zoe", "Ivy", "Ava"]
BOY_NAMES = ["Finn", "Leo", "Eli", "Theo", "Max", "Owen"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world: curiosity, media, problem solving, and rhyme.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--media", choices=MEDIA)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(p, m) for p in PLACES for m in MEDIA if "search" in PLACES[p].affords and "media" in MEDIA[m].tags]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place and args.media and (args.place, args.media) not in combos:
        raise StoryError("That place and media choice do not make a reasonable adventure.")
    combos = [c for c in combos if (not args.place or c[0] == args.place) and (not args.media or c[1] == args.media)]
    if not combos:
        raise StoryError("No valid story matches those options.")
    place, media = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, media=media, name=name, gender=gender, helper=helper, trait=trait)


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    media = MEDIA[params.media]
    world = World(place)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", params.trait]))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label=params.helper))
    item = world.add(Entity(id=media.id, kind="thing", type=media.type, label=media.label, phrase=media.phrase))
    world.facts.update(child=child, helper=helper, media=item, media_cfg=media, place=place)
    return world


def predict_success(world: World, media: MediaItem) -> bool:
    sim = world.copy()
    sim.facts["fixed"] = False
    return True


def _setup(world: World) -> None:
    c = world.facts["child"]
    m = world.facts["media_cfg"]
    world.say(f"{c.id} was a little {c.traits[-1]} child who loved to ask why the world worked.")
    world.say(f"{c.pronoun().capitalize()} loved old {m.label}s, because each one hid a story waiting to be found.")
    world.say(f"One day, {c.id} found {m.phrase} in {world.place.label}, and curiosity sparked like a tiny torch.")


def _problem(world: World) -> None:
    c = world.facts["child"]
    m = world.facts["media_cfg"]
    c.memes["curiosity"] = c.memes.get("curiosity", 0.0) + 1
    c.memes["desire"] = c.memes.get("desire", 0.0) + 1
    world.para()
    world.say(f"{c.id} turned the {m.label}, but the sound came out in rough static.")
    world.say(f"The message was there, yet it was stuck behind {m.problem}, so {c.id} had to solve the puzzle by hand.")


def _moral_turn(world: World) -> None:
    c = world.facts["child"]
    h = world.facts["helper"]
    m = world.facts["media_cfg"]
    world.say(f"{h.id} asked what {c.id} had found, and {c.id} nearly hid the secret for a moment.")
    c.memes["temptation"] = c.memes.get("temptation", 0.0) + 1
    world.say(f"Then {c.id} chose the honest path and said the truth, because sharing the find felt kinder than keeping it alone.")
    c.memes["moral"] = c.memes.get("moral", 0.0) + 1


def _solve(world: World) -> None:
    c = world.facts["child"]
    h = world.facts["helper"]
    m = world.facts["media_cfg"]
    world.para()
    world.say(f"{h.id} helped {c.id} {m.fix}.")
    world.say(f"Click by click, the static thinned, and the message became clear at last.")
    world.say(f"It was a call for help from a lost hiker, and the clue pointed down the trail beyond {world.place.label}.")
    world.say(f"{c.id} and {h.id} followed the clue together, brave and bright.")
    world.say(f'They whispered, "Find the sign, then we will shine."')


def _ending(world: World) -> None:
    c = world.facts["child"]
    h = world.facts["helper"]
    m = world.facts["media_cfg"]
    c.memes["joy"] = c.memes.get("joy", 0.0) + 1
    world.para()
    world.say(f"At the end, they found the lost hiker and got the message to the right people.")
    world.say(f"{c.id} held the repaired {m.label} close, proud that curiosity had helped, honesty had guided, and the tiny rhyme had lit the way.")
    world.say(f'The day felt small and grand at once: "Seek the clue, do what is true."')


def tell(world: World) -> None:
    _setup(world)
    _problem(world)
    _moral_turn(world)
    _solve(world)
    _ending(world)


def generation_prompts(world: World) -> list[str]:
    c = world.facts["child"]
    m = world.facts["media_cfg"]
    return [
        f"Write a short adventure story for a young child about {c.id} and a {m.label} that begins with curiosity and ends with a rhyme.",
        f"Tell a story where a child finds {m.phrase}, solves the problem with help, and chooses honesty.",
        f"Write a gentle adventure with media, problem solving, and a moral value, using the word '{m.label}'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    m = world.facts["media_cfg"]
    h = world.facts["helper"]
    return [
        QAItem(
            question=f"What did {c.id} find in {world.place.label}?",
            answer=f"{c.id} found {m.phrase}.",
        ),
        QAItem(
            question=f"What problem made the {m.label} hard to use?",
            answer=f"The {m.label} had {m.problem}, so the message was hard to hear or see until it was fixed.",
        ),
        QAItem(
            question=f"How did {c.id} solve the problem?",
            answer=f"{c.id} worked with {h.id} and {m.fix}. That made the message clear.",
        ),
        QAItem(
            question=f"What moral choice did {c.id} make?",
            answer=f"{c.id} chose to tell the truth and share the find instead of keeping it secret.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is media?", answer="Media is a way to share stories, pictures, sounds, or messages with other people."),
        QAItem(question="Why is curiosity useful?", answer="Curiosity helps you ask questions, notice clues, and learn new things."),
        QAItem(question="What does it mean to solve a problem?", answer="To solve a problem means to find a good way to fix something that is not working well."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
place(attic;dock;camp).
media(radio;comic;camera).
affords(attic,search).
affords(dock,search).
affords(camp,search).
tag(radio,media).
tag(radio,sound).
tag(radio,curiosity).
tag(comic,media).
tag(comic,reading).
tag(comic,curiosity).
tag(camera,media).
tag(camera,images).
tag(camera,curiosity).
valid(P,M) :- place(P), media(M), affords(P,search), tag(M,media).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, m in MEDIA.items():
        lines.append(asp.fact("media", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("tag", mid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="attic", media="radio", name="Mia", gender="girl", helper="mother", trait="curious"),
    StoryParams(place="dock", media="camera", name="Finn", gender="boy", helper="father", trait="brave"),
    StoryParams(place="camp", media="comic", name="Luna", gender="girl", helper="mother", trait="thoughtful"),
]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, media) combinations:")
        for p, m in combos:
            print(f"  {p:6} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
            header = f"### {p.name}: {p.media} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
