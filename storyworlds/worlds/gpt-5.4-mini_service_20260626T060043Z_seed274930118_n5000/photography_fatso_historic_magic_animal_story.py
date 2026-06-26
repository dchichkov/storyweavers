#!/usr/bin/env python3
"""
storyworlds/worlds/photography_fatso_historic_magic_animal_story.py
====================================================================

A small animal-story world about a magic camera, a historic place, and a
photograph that matters.

Seed impression:
---
A tiny animal photographer arrives at a historic place with a magic camera.
A friendly animal nicknamed Fatso wants to be in the picture, but the old
place is delicate and the flash can wake up old magic. The friends must choose
a careful way to take the photograph so the moment can be remembered without
hurting the historic room.

This world keeps the story simple and causal:
- an animal photographer wants a photo
- the historic setting is delicate
- magic makes the first attempt risky
- a gentle compromise lets everyone enjoy the picture
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat", "kitten", "fox", "mouse", "rabbit", "bird"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    historic: bool = False
    fragile: bool = False
    allows_magic: bool = True
    photo_spot: str = "the center of the room"


@dataclass
class Camera:
    label: str
    magic: bool = False
    flash: bool = True
    filter: str = "ordinary"


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def hero_desc(name: str, kind: str) -> str:
    return f"{name}, the little {kind}"


PLACES = {
    "museum_room": Place(name="the historic museum room", historic=True, fragile=True, allows_magic=True, photo_spot="the velvet rope"),
    "old_bridge": Place(name="the historic stone bridge", historic=True, fragile=False, allows_magic=True, photo_spot="the middle arch"),
    "town_square": Place(name="the historic town square", historic=True, fragile=False, allows_magic=True, photo_spot="the old fountain"),
}

ANIMALS = {
    "mouse": {"label": "mouse", "kind": "mouse", "name": "Mina"},
    "fox": {"label": "fox", "kind": "fox", "name": "Fenn"},
    "rabbit": {"label": "rabbit", "kind": "rabbit", "name": "Ruby"},
    "cat": {"label": "cat", "kind": "cat", "name": "Cleo"},
    "pig": {"label": "pig", "kind": "pig", "name": "Fatso"},
}

CAMERA = Camera(label="a small camera", magic=True, flash=True, filter="moonlit")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: photography, Fatso, and a historic magic place.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=ANIMALS)
    ap.add_argument("--friend", choices=ANIMALS)
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


def _reasonableness_gate(place: Place, hero: dict, friend: dict) -> None:
    if hero["kind"] == friend["kind"]:
        raise StoryError("The story needs two different animal roles so the photo moment can feel like a real visit.")
    if not place.historic:
        raise StoryError("This world is built around a historic place.")
    if not place.allows_magic:
        raise StoryError("This historic place must allow a little magic for the story to work.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_key = args.place or rng.choice(list(PLACES))
    hero_key = args.hero or rng.choice(list(ANIMALS))
    friend_key = args.friend or rng.choice([k for k in ANIMALS if k != hero_key])
    _reasonableness_gate(PLACES[place_key], ANIMALS[hero_key], ANIMALS[friend_key])
    return StoryParams(place=place_key, hero=hero_key, friend=friend_key)


def predict_flash_trouble(world: World) -> bool:
    return world.place.historic and world.place.fragile and CAMERA.magic and CAMERA.flash


def tell_story(place: Place, hero_def: dict, friend_def: dict) -> World:
    w = World(place)
    hero = w.add(Entity(id="hero", kind="character", type=hero_def["kind"], label=hero_def["label"]))
    friend = w.add(Entity(id="friend", kind="character", type=friend_def["kind"], label=friend_def["label"]))
    camera = w.add(Entity(id="camera", type="camera", label=CAMERA.label, phrase=CAMERA.label, protective=False))
    camera.meters["magic"] = 1.0 if CAMERA.magic else 0.0

    hero.memes["curious"] = 1.0
    friend.memes["proud"] = 1.0

    w.say(f"At {place.name}, {hero_desc('Mina' if hero.type == 'mouse' else hero.label or hero.type, hero.label or hero.type)} carried {CAMERA.label}.")
    w.say(f"{friend.label.capitalize()}, a friendly {friend.label}, had come along because {friend.pronoun('subject')} wanted to be in a photograph too.")
    w.say(f"The old room was {place.photo_spot}, and the air felt careful and quiet.")
    w.para()

    if predict_flash_trouble(w):
        hero.memes["worry"] = 1.0
        friend.memes["worry"] = 1.0
        w.say(f"{hero.label.capitalize()} wanted the picture, but the magic flash could wake up the historic dust and shake the old room.")
        w.say(f'"Maybe not the bright flash," said {hero.label.capitalize()}, holding the camera close.')
        w.say(f"{friend.label.capitalize()} nodded and pointed to the moonlit filter. " + '"That one looks gentler."')
        w.para()
        camera.meters["flash"] = 0.0
        camera.meters["magic"] = 1.0
        camera.meters["filter_used"] = 1.0
        hero.memes["relief"] = 1.0
        friend.memes["joy"] = 1.0
        w.say(f"So they turned the camera to its moonlit setting and stood still by {place.photo_spot}.")
        w.say(f"The picture came out soft and shiny, with {friend.label.capitalize()} smiling and the historic room staying safe.")
        w.say(f"Afterward, the old place looked peaceful, and the new photograph was tucked safely into {hero.label.capitalize()}'s bag.")
    else:
        w.say(f"The camera clicked once, and the photo came out clear and calm.")
        w.say(f"{hero.label.capitalize()} and {friend.label.capitalize()} both smiled, and the historic place stayed neat and quiet.")
    w.facts.update(hero=hero, friend=friend, place=place, camera=camera, resolved=True)
    return w


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    place: Place = world.facts["place"]
    return [
        "Write a short animal story about photography, a historic place, and a little bit of magic.",
        f"Tell a gentle story where {hero.label.capitalize()} and {friend.label.capitalize()} visit {place.name} to take a special picture.",
        "Write a child-friendly story in which a magic camera is used carefully in a historic place.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    place: Place = world.facts["place"]
    camera: Entity = world.facts["camera"]
    return [
        QAItem(
            question=f"Who went to {place.name} to take the picture?",
            answer=f"{hero.label.capitalize()} went with {friend.label.capitalize()} to {place.name} to take a photograph.",
        ),
        QAItem(
            question="Why did they avoid the bright flash?",
            answer="They avoided the bright flash because the place was historic and the magic flash could disturb the delicate old room.",
        ),
        QAItem(
            question="What did they use instead of the bright flash?",
            answer=f"They used the moonlit filter on {camera.label} so the picture could be gentle.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is photography?",
            answer="Photography is the art of taking pictures with a camera so you can keep a memory of a person, place, or event.",
        ),
        QAItem(
            question="What does historic mean?",
            answer="Historic means something is old and important because it comes from the past.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic in a story is something special that can do surprising things, like glow, change, or help in a gentle way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {e.label} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place_historic(P) :- place(P), historic(P).
photo_risky(P) :- place_historic(P), fragile(P), magic_camera(cam), flash(cam).
safe_choice(P) :- place_historic(P), magic_camera(cam), moonlit_filter(cam).
resolved(P) :- photo_risky(P), safe_choice(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pk, p in PLACES.items():
        lines.append(asp.fact("place", pk))
        if p.historic:
            lines.append(asp.fact("historic", pk))
        if p.fragile:
            lines.append(asp.fact("fragile", pk))
    lines.append(asp.fact("magic_camera", "cam"))
    lines.append(asp.fact("flash", "cam"))
    lines.append(asp.fact("moonlit_filter", "cam"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    got = set(asp.atoms(model, "resolved"))
    want = {("the_historic_museum_room",), ("the_historic_stone_bridge",), ("the_historic_town_square",)}
    if got == want:
        print(f"OK: ASP gate matches the expected historic-photo resolution set ({len(got)} places).")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(got))
    print("PY :", sorted(want))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell_story(PLACES[params.place], ANIMALS[params.hero], ANIMALS[params.friend])
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
    StoryParams(place="museum_room", hero="mouse", friend="pig"),
    StoryParams(place="old_bridge", hero="fox", friend="rabbit"),
    StoryParams(place="town_square", hero="cat", friend="pig"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/1."))
        print(sorted(set(asp.atoms(model, "resolved"))))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(rng.randrange(2**31)))
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
