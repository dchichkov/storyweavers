#!/usr/bin/env python3
"""
A small animal story world about a curious animal helping a friend, causing a
misunderstanding, and then making up again with a kind fix.

Seed words: animal, hel
Features: Reconciliation, Curiosity
Style: Animal Story
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


@dataclass
class Animal:
    id: str
    kind: str
    name: str
    role: str
    pronoun_subject: str
    pronoun_object: str
    pronoun_possessive: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def touch(self, key: str, amt: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amt

    def feel(self, key: str, amt: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amt


@dataclass
class Place:
    name: str
    setting_line: str
    curiosity_draw: str


@dataclass
class ObjectThing:
    name: str
    label: str
    owner: str
    found_in: str


@dataclass
class World:
    place: Place
    hero: Animal
    friend: Animal
    object_thing: ObjectThing
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    hero_kind: str
    friend_kind: str
    name: str
    friend_name: str
    object_name: str
    seed: Optional[int] = None


PLACES = {
    "meadow": Place(
        name="the meadow",
        setting_line="The meadow was soft and sunny, with grass that swayed like a green wave.",
        curiosity_draw="A tiny trail of moving leaves made every step look interesting.",
    ),
    "pond": Place(
        name="the pond",
        setting_line="The pond shimmered with quiet water and round lily pads.",
        curiosity_draw="Little bubbles rose from the edge as if the water had a secret.",
    ),
    "garden": Place(
        name="the garden",
        setting_line="The garden was full of flowers, stones, and happy buzzing bees.",
        curiosity_draw="A shiny shell near the fence seemed to be asking to be noticed.",
    ),
}

ANIMALS = {
    "rabbit": ("rabbit", "they", "them", "their"),
    "fox": ("fox", "they", "them", "their"),
    "bird": ("bird", "they", "them", "their"),
    "squirrel": ("squirrel", "they", "them", "their"),
    "deer": ("deer", "they", "them", "their"),
}

OBJECTS = {
    "leaf": ("leaf", "little leaf", "friend", "meadow"),
    "berry": ("berry", "bright berry", "friend", "garden"),
    "shell": ("shell", "small shell", "friend", "pond"),
}

GREETINGS = [
    "curious",
    "gentle",
    "bright-eyed",
    "quick-footed",
    "soft-spoken",
]


def make_animal(name: str, kind: str, role: str) -> Animal:
    _, subj, obj, poss = ANIMALS[kind]
    return Animal(
        id=name,
        kind=kind,
        name=name,
        role=role,
        pronoun_subject=subj,
        pronoun_object=obj,
        pronoun_possessive=poss,
    )


def story_world_from_params(params: StoryParams) -> World:
    place = PLACES[params.place]
    hero = make_animal(params.name, params.hero_kind, "hero")
    friend = make_animal(params.friend_name, params.friend_kind, "friend")
    obj_name, obj_label, owner, found_in = OBJECTS[params.object_name]
    thing = ObjectThing(name=obj_name, label=obj_label, owner=friend.name, found_in=found_in)
    return World(place=place, hero=hero, friend=friend, object_thing=thing)


def tell_story(world: World) -> None:
    h = world.hero
    f = world.friend
    o = world.object_thing
    p = world.place

    h.feel("curiosity", 2)
    h.feel("care", 1)
    f.feel("sadness", 1)

    world.say(f"{h.name} was a {random.choice(GREETINGS)} {h.kind} who loved to look closely at everything.")
    world.say(f"One day, {h.name} and {f.name} went to {p.name}. {p.setting_line}")
    world.say(f"{p.curiosity_draw} {h.name} wanted to check it out at once, because {h.pronoun_subject} was full of curiosity.")
    world.say(f"Near a stone, {h.name} found a {o.label} that belonged to {f.name}.")
    world.say(f"{h.name} picked it up to help, but {f.name} thought {h.pronoun_subject} was taking it away.")
    h.feel("worry", 1)
    f.feel("hurt", 2)
    world.say(f"{f.name} lowered {f.pronoun_possessive} ears and stepped back. \"That is mine,\" {f.name} said softly.")
    world.para()
    world.say(f"{h.name} froze. {h.pronoun_subject.capitalize()} did not want to cause trouble.")
    world.say(f"Then {h.name} held the {o.label} out and explained, \"I was only being curious. I wanted to help.\"")
    h.feel("regret", 1)
    f.feel("listening", 1)
    world.say(f"{f.name} listened, saw the kind look in {h.name}'s eyes, and understood.")
    world.say(f"\"I am sorry,\" said {f.name}. \"I thought you were being mean.\"")
    world.para()
    h.feel("relief", 2)
    f.feel("relief", 2)
    h.feel("joy", 2)
    f.feel("joy", 2)
    world.say(f"{h.name} smiled and placed the {o.label} back with care.")
    world.say(f"To make up, {h.name} helped {f.name} carry it home, and the two friends walked side by side.")
    world.say(f"By the time they reached home, they were laughing again, and the little mistake felt much smaller.")
    world.say(f"The {o.label} was safe, the worry was gone, and {h.name} and {f.name} were friends again.")


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.hero_kind not in ANIMALS or params.friend_kind not in ANIMALS:
        raise StoryError("Unknown animal kind.")
    if params.object_name not in OBJECTS:
        raise StoryError("Unknown object.")
    if params.hero_kind == params.friend_kind and params.name == params.friend_name:
        raise StoryError("The hero and friend must be different animals.")

    world = story_world_from_params(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a short animal story for a young child about curiosity, a mistake, and reconciliation at {world.place.name}.',
        f"Tell a gentle story where {world.hero.name} wants to help {world.friend.name}, but a misunderstanding happens and they make up again.",
        f'Write a simple story that uses the word "curious" and ends with two animal friends being kind to each other.',
    ]


def story_qa(world: World) -> list[QAItem]:
    h = world.hero
    f = world.friend
    o = world.object_thing
    p = world.place
    return [
        QAItem(
            question=f"Why did {h.name} pick up the {o.label}?",
            answer=f"{h.name} picked up the {o.label} because {h.pronoun_subject} was curious and wanted to help.",
        ),
        QAItem(
            question=f"Why did {f.name} feel upset at first?",
            answer=f"{f.name} felt upset because {f.pronoun_subject} thought {h.name} was taking the {o.label} away.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"{h.name} explained the mistake, {f.name} understood, and the two friends made up again at {p.name}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to be curious?",
            answer="Being curious means you want to look, ask, and learn about something new.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means people or friends stop arguing, understand each other, and become friendly again.",
        ),
        QAItem(
            question="Why should you return something that belongs to a friend?",
            answer="You should return it because it belongs to your friend and giving it back helps keep trust and friendship strong.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in [world.hero, world.friend]:
        lines.append(
            f"{ent.name}: meters={dict(sorted(ent.meters.items()))} memes={dict(sorted(ent.memes.items()))}"
        )
    lines.append(f"object: {world.object_thing.label} owner={world.object_thing.owner} found_in={world.object_thing.found_in}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with curiosity and reconciliation.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero-kind", choices=sorted(ANIMALS))
    ap.add_argument("--friend-kind", choices=sorted(ANIMALS))
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--object-name", choices=sorted(OBJECTS))
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
    place = args.place or rng.choice(sorted(PLACES))
    hero_kind = args.hero_kind or rng.choice(sorted(ANIMALS))
    friend_kind = args.friend_kind or rng.choice([k for k in sorted(ANIMALS) if k != hero_kind])
    object_name = args.object_name or rng.choice(sorted([k for k, v in OBJECTS.items() if v[2] == "friend"]))
    if args.name:
        name = args.name
    else:
        name = rng.choice(["Hel", "Milo", "Pip", "Nia", "Tiki", "Luna", "Bram"])
    if args.friend_name:
        friend_name = args.friend_name
    else:
        friend_name = rng.choice([n for n in ["Ollie", "Mina", "Taro", "Suri", "Penny", "Kio"] if n != name])
    if name == friend_name:
        raise StoryError("The hero and friend must have different names.")
    return StoryParams(
        place=place,
        hero_kind=hero_kind,
        friend_kind=friend_kind,
        name=name,
        friend_name=friend_name,
        object_name=object_name,
    )


CURATED = [
    StoryParams(place="meadow", hero_kind="rabbit", friend_kind="bird", name="Hel", friend_name="Mina", object_name="leaf"),
    StoryParams(place="pond", hero_kind="fox", friend_kind="squirrel", name="Hel", friend_name="Ollie", object_name="shell"),
    StoryParams(place="garden", hero_kind="deer", friend_kind="rabbit", name="Hel", friend_name="Suri", object_name="berry"),
]


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pname, place in PLACES.items():
        lines.append(asp.fact("place", pname))
        if "pond" in pname:
            lines.append(asp.fact("wet_place", pname))
    for aname in ANIMALS:
        lines.append(asp.fact("animal", aname))
    for oname, (_, _, owner, found_in) in OBJECTS.items():
        lines.append(asp.fact("thing", oname))
        lines.append(asp.fact("belongs_to_role", oname, owner))
        lines.append(asp.fact("found_in", oname, found_in))
    return "\n".join(lines)


ASP_RULES = r"""
curious(X) :- animal(X).
reconcile(X,Y) :- animal(X), animal(Y), X != Y.
story_ok(P,H,F,O) :- place(P), animal(H), animal(F), H != F, thing(O).
#show curious/1.
#show reconcile/2.
#show story_ok/4.
"""


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    atoms = set((sym.name, tuple(arg.name if arg.type != arg.type.Number else arg.number for arg in sym.arguments)) for sym in model)
    expected = {("curious", (k,)) for k in ANIMALS}
    expected |= {("reconcile", (a, b)) for a in ANIMALS for b in ANIMALS if a != b}
    expected |= {("story_ok", (p, h, f, o)) for p in PLACES for h in ANIMALS for f in ANIMALS if h != f for o in OBJECTS}
    if atoms == expected:
        print(f"OK: ASP parity matches Python world gates ({len(expected)} atoms).")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    return 1


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
            header = f"### {p.name}: {p.hero_kind} with {p.friend_kind} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
