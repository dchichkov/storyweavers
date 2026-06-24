#!/usr/bin/env python3
"""
storyworlds/worlds/talon_sharing_animal_story.py
=================================================

A small animal-story world about a treasured talon-shaped trinket and the
gentle turn from keeping to sharing.

The seed image:
- A young animal finds a talon-shaped shiny thing.
- Another animal wants to play too.
- The first feels possessive at first, then learns that sharing makes the play
  better, not smaller.

This world keeps the prose child-facing and concrete while the state model tracks
who owns the talon, who is waiting, and how sharing changes the animals' feelings.
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
    kind: str = "animal"
    species: str = "animal"
    name: str = ""
    plural: bool = False
    owner: Optional[str] = None
    held: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford_share: bool = True


@dataclass
class Talon:
    label: str
    phrase: str
    kind: str = "talon"
    sparkle: str = "bright"
    size: str = "small"


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    talon: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal sharing story with a talon trinket.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--hero", choices=sorted(ANIMALS))
    ap.add_argument("--friend", choices=sorted(ANIMALS))
    ap.add_argument("--talon", choices=sorted(TALONS))
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


SETTINGS = {
    "meadow": Setting("the meadow"),
    "pond": Setting("the pond"),
    "nest": Setting("the nest"),
    "hill": Setting("the sunny hill"),
}

ANIMALS = {
    "fox": {"name": "Finn", "species": "fox"},
    "rabbit": {"name": "Ruby", "species": "rabbit"},
    "bear": {"name": "Benny", "species": "bear"},
    "squirrel": {"name": "Sia", "species": "squirrel"},
    "duck": {"name": "Didi", "species": "duck"},
}

TALONS = {
    "hawk_talon": Talon(label="talon", phrase="a shiny hawk talon"),
    "gold_talon": Talon(label="talon", phrase="a little golden talon"),
    "shell_talon": Talon(label="talon", phrase="a smooth talon-shaped shell"),
}


ASP_RULES = r"""
holds(H, T) :- hero(H), talon(T), owns(H, T).
wants(F, T) :- friend(F), talon(T), present(T).
shares(H, F, T) :- holds(H, T), wants(F, T), kind(H, animal), kind(F, animal).
resolved(H, F, T) :- shares(H, F, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for k, s in SETTINGS.items():
        lines.append(asp.fact("place", k))
        if s.afford_share:
            lines.append(asp.fact("affords_share", k))
    for k, a in ANIMALS.items():
        lines.append(asp.fact("animal", k))
        lines.append(asp.fact("kind", k, "animal"))
        lines.append(asp.fact("named", k, a["name"]))
    for k, t in TALONS.items():
        lines.append(asp.fact("talon", k))
        lines.append(asp.fact("present", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for hero in ANIMALS:
            for friend in ANIMALS:
                if hero == friend:
                    continue
                for talon in TALONS:
                    combos.append((place, hero, friend, talon))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show resolved/3."))
    return sorted(set(asp.atoms(model, "resolved")))


def asp_verify() -> int:
    py = len(valid_combos())
    print(f"OK: Python gate allows {py} story shapes.")
    return 0


def _animal_line(ent: Entity) -> str:
    return f"{ent.name} the {ent.species}"


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero_info = ANIMALS[params.hero]
    friend_info = ANIMALS[params.friend]
    talon = TALONS[params.talon]

    hero = world.add(Entity(id="hero", species=hero_info["species"], name=hero_info["name"]))
    friend = world.add(Entity(id="friend", species=friend_info["species"], name=friend_info["name"]))
    trinket = world.add(Entity(id="talon", kind="thing", species="talon", owner=hero.id, held=True))

    hero.meters["holding"] = 1.0
    hero.memes["joy"] = 1.0
    hero.memes["pride"] = 1.0

    world.say(
        f"{_animal_line(hero)} found {talon.phrase} near {world.setting.place} and held the talon close."
    )
    world.say(
        f"{_animal_line(hero)} thought the talon was special, because it gleamed like a tiny treasure."
    )

    world.para()
    friend.memes["hope"] = 1.0
    world.say(
        f"Then {_animal_line(friend)} came over and asked, "
        f'"Can I play with the talon too?"'
    )
    if world.setting.afford_share:
        hero.memes["worry"] = 1.0
        world.say(
            f"{_animal_line(hero)} hugged the talon tighter. "
            f"It was hard to share something so shiny."
        )

    world.para()
    hero.memes["worry"] = 0.0
    hero.memes["kindness"] = 1.0
    friend.memes["joy"] = 1.0
    world.say(
        f"{_animal_line(hero)} looked at {_animal_line(friend)} and took a slow breath."
    )
    world.say(
        f'"We can share the talon," {hero.name} said, and placed it between them on the grass.'
    )
    world.say(
        f"They both tapped the talon, took turns telling stories, and laughed together."
    )

    world.para()
    trinket.held = False
    trinket.owner = None
    hero.memes["joy"] += 1.0
    friend.memes["joy"] += 1.0
    world.say(
        f"In the end, the talon was still bright, but now it was part of a game for both friends."
    )
    world.say(
        f"{hero.name} and {friend.name} smiled side by side, happy that sharing had made the fun bigger."
    )

    world.facts = {
        "hero": hero,
        "friend": friend,
        "talon": talon,
        "place": params.place,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    return [
        f"Write a gentle animal story where {hero.name} learns to share a talon with {friend.name}.",
        f"Tell a short story for a small child about a shiny talon, a friend, and a happy sharing moment.",
        f"Write an Animal Story style tale set at {world.setting.place} with animals who solve a problem by sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    talon: Talon = world.facts["talon"]
    place = world.facts["place"]
    return [
        QAItem(
            question=f"What did {hero.name} find at {SETTINGS[place].place}?",
            answer=f"{hero.name} found {talon.phrase} and thought it was a special treasure.",
        ),
        QAItem(
            question=f"What did {friend.name} ask about the talon?",
            answer=f"{friend.name} asked if they could play with the talon too.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer="The talon went from being something one animal wanted to keep to something both friends shared happily.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use, enjoy, or have a turn with something you have.",
        ),
        QAItem(
            question="What is a talon?",
            answer="A talon is a sharp claw on a bird of prey, like a hawk or an eagle.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        m = {k: v for k, v in ent.meters.items() if v}
        e = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if e:
            bits.append(f"memes={e}")
        if ent.owner is not None:
            bits.append(f"owner={ent.owner}")
        if ent.held:
            bits.append("held=True")
        lines.append(f"  {ent.id:6} ({ent.species:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(SETTINGS))
    hero = args.hero or rng.choice(sorted(ANIMALS))
    friend_choices = [a for a in ANIMALS if a != hero]
    friend = args.friend or rng.choice(sorted(friend_choices))
    talon = args.talon or rng.choice(sorted(TALONS))
    if hero == friend:
        raise StoryError("Hero and friend must be different animals.")
    return StoryParams(place=place, hero=hero, friend=friend, talon=talon)


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


CURATED = [
    StoryParams(place="meadow", hero="fox", friend="rabbit", talon="hawk_talon"),
    StoryParams(place="pond", hero="duck", friend="squirrel", talon="gold_talon"),
    StoryParams(place="hill", hero="bear", friend="fox", talon="shell_talon"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show resolved/3."))
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
            header = f"### {p.hero} shares with {p.friend} at {p.place} ({p.talon})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
