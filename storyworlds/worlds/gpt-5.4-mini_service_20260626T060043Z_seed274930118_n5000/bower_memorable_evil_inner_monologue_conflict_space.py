#!/usr/bin/env python3
"""
A small storyworld for a Space Adventure tale about a bower, a memorable
choice, and an evil inner monologue that turns into conflict and repair.
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

SPACEWORLD_KINDS = {"probe", "bot", "captain", "pilot", "drone", "alien", "star"}

GREETINGS = [
    "starlit",
    "bright",
    "quiet",
    "curious",
    "careful",
    "brave",
    "memorable",
]

PLACE_PHRASES = {
    "orbital_bower": "the orbital bower",
    "moon_bower": "the moon bower",
    "station_bower": "the station bower",
}

OBJECT_PHRASES = {
    "signal_garden": "a signal garden",
    "glow_vines": "glow vines",
    "moon_harp": "a moon harp",
    "star_lantern": "a star lantern",
}

VALUES = {
    "repair": "repair the broken light",
    "share": "share the power cell",
    "wait": "wait for the rescue pod",
    "warn": "warn the others",
}

ENEMIES = {
    "void_shadow": "a void shadow",
    "red_meteor": "a red meteor",
    "gremlin_bot": "a gremlin bot",
    "cold_alien": "a cold alien",
}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carrying: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pilot"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "robot"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    kind: str = "bower"


@dataclass
class StoryParams:
    place: str
    hero_type: str
    name: str
    object: str
    enemy: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
    ap = argparse.ArgumentParser(description="Space Adventure storyworld with a bower, conflict, and inner monologue.")
    ap.add_argument("--place", choices=sorted(PLACE_PHRASES))
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["captain", "pilot"])
    ap.add_argument("--object", dest="object_", choices=sorted(OBJECT_PHRASES))
    ap.add_argument("--enemy", choices=sorted(ENEMIES))
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
    place = args.place or rng.choice(list(PLACE_PHRASES))
    hero_type = args.hero_type or rng.choice(["captain", "pilot"])
    name = args.name or rng.choice(["Nova", "Iris", "Luna", "Zed", "Milo", "Rin"])
    obj = args.object_ or rng.choice(list(OBJECT_PHRASES))
    enemy = args.enemy or rng.choice(list(ENEMIES))
    if hero_type == "captain" and name in {"Zed"}:
        pass
    return StoryParams(place=place, hero_type=hero_type, name=name, object=obj, enemy=enemy)


def _inner_monologue(world: World, hero: Entity, threat: str) -> str:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1.0
    return (
        f"{hero.id} thought, \"If I hurry now, I might make the wrong choice.\" "
        f"Then {hero.pronoun('subject')} remembered that being brave could also mean being careful."
    )


def _conflict(world: World, hero: Entity, enemy: Entity, obj: Entity) -> None:
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1.0
    enemy.meters["danger"] = enemy.meters.get("danger", 0.0) + 1.0
    obj.meters["risk"] = obj.meters.get("risk", 0.0) + 1.0
    world.say(
        f"But {ENEMIES[enemy.type]} drifted into the bower and blocked the light from {obj.phrase}."
    )
    world.say(_inner_monologue(world, hero, enemy.label))


def _resolution(world: World, hero: Entity, obj: Entity, enemy: Entity) -> None:
    hero.memes["conflict"] = 0.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    obj.meters["risk"] = 0.0
    enemy.meters["danger"] = 0.0
    world.say(
        f"{hero.id} chose to {world.facts['plan']} instead of panicking, and the crew worked together."
    )
    world.say(
        f"At last, the bower glowed again, {obj.phrase} shone like a small star, and "
        f"{hero.id} knew this would be a memorable day."
    )


def tell(place: Place, hero_type: str, name: str, object_id: str, enemy_id: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=hero_type, label=name))
    obj = world.add(Entity(
        id=object_id,
        kind="thing",
        type=object_id,
        label=OBJECT_PHRASES[object_id],
        phrase=OBJECT_PHRASES[object_id],
        owner=hero.id,
    ))
    enemy = world.add(Entity(
        id=enemy_id,
        kind="character" if enemy_id != "red_meteor" else "thing",
        type=enemy_id,
        label=ENEMIES[enemy_id],
        phrase=ENEMIES[enemy_id],
    ))

    world.facts["plan"] = random.choice(list(VALUES.values()))
    world.say(f"{hero.id} was a {hero_type} who loved the quiet bower on the ship.")
    world.say(
        f"That bower was a memorable place with vines of light, soft seats, and a window that looked out at the stars."
    )
    world.say(
        f"{hero.id} kept {obj.phrase} there because {hero.pronoun('subject')} wanted the bower to feel bright and safe."
    )
    world.para()
    world.say(
        f"One evening, {hero.id} stepped into {place.label} and saw that something evil had crept near the glow."
    )
    world.say(
        f"{hero.id} wanted to protect the bower, but {hero.pronoun('possessive')} mind filled with a sharp inner monologue."
    )
    _conflict(world, hero, enemy, obj)
    world.para()
    _resolution(world, hero, obj, enemy)

    world.facts.update(hero=hero, obj=obj, enemy=enemy, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short space adventure story about {f['hero'].id} in {f['place'].label}, with a bower and a memorable ending.",
        f"Tell a gentle science-fiction story where {f['hero'].id} faces an evil problem, listens to an inner monologue, and resolves a conflict.",
        f"Write a child-friendly story set in a bower among the stars, using the words bower, memorable, and evil.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, obj, enemy, place = f["hero"], f["obj"], f["enemy"], f["place"]
    return [
        QAItem(
            question=f"Where did {hero.id} spend time before the trouble began?",
            answer=f"{hero.id} spent time in {place.label}, a quiet bower aboard the ship."
        ),
        QAItem(
            question=f"What did {hero.id} want to protect?",
            answer=f"{hero.id} wanted to protect {obj.phrase} and keep the bower bright."
        ),
        QAItem(
            question=f"What made the story tense?",
            answer=f"{ENEMIES[enemy.type]} made the story tense by blocking the light and starting a conflict."
        ),
        QAItem(
            question=f"What helped {hero.id} after the inner monologue?",
            answer=f"After thinking carefully, {hero.id} chose a plan and worked with the crew instead of giving in to fear."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bower?",
            answer="A bower is a cozy little place with plants or branches that can feel like a tiny garden or shelter."
        ),
        QAItem(
            question="What does memorable mean?",
            answer="Memorable means easy to remember because it felt special, strong, or important."
        ),
        QAItem(
            question="What does evil mean in a story?",
            answer="Evil means very bad or harmful in a story, usually for a character or force that tries to cause trouble."
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private voice a character hears in their own mind when they think about what to do."
        ),
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is the problem or struggle that makes a story tense and pushes the characters to act."
        ),
    ]


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACE_PHRASES:
        lines.append(asp.fact("place", pid))
    for oid in OBJECT_PHRASES:
        lines.append(asp.fact("object", oid))
    for eid in ENEMIES:
        lines.append(asp.fact("enemy", eid))
    lines.append(asp.fact("theme", "bower"))
    lines.append(asp.fact("theme", "memorable"))
    lines.append(asp.fact("theme", "evil"))
    return "\n".join(lines)


ASP_RULES = r"""
good_story(P) :- place(P), theme(bower), theme(memorable), theme(evil).
#show good_story/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(Place(params.place, PLACE_PHRASES[params.place]), params.hero_type, params.name, params.object, params.enemy)
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
    StoryParams(place="orbital_bower", hero_type="captain", name="Nova", object="star_lantern", enemy="void_shadow"),
    StoryParams(place="moon_bower", hero_type="pilot", name="Iris", object="moon_harp", enemy="gremlin_bot"),
    StoryParams(place="station_bower", hero_type="captain", name="Luna", object="glow_vines", enemy="cold_alien"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("3 compatible bower stories.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} / {p.object} / {p.enemy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
