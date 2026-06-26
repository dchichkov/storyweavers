#!/usr/bin/env python3
"""
A small fable-style storyworld about a hasty gallop, a callous choice, and a
misunderstanding that Curiosity helps resolve.
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "hare", "rabbit", "wolf", "donkey", "horse", "pony"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    path: str
    afford_gallop: bool = True


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    object: str
    seed: Optional[int] = None


SETTINGS = {
    "meadow": Setting(place="the meadow", path="the hill path", afford_gallop=True),
    "lane": Setting(place="the village lane", path="the dusty lane", afford_gallop=True),
    "orchard": Setting(place="the orchard", path="the narrow path", afford_gallop=False),
}

HEROES = {
    "pony": {"type": "pony", "label": "pony", "name": "Poppy"},
    "fox": {"type": "fox", "label": "fox", "name": "Felix"},
    "hare": {"type": "hare", "label": "hare", "name": "Holly"},
}

FRIENDS = {
    "donkey": {"type": "donkey", "label": "donkey", "name": "Dora"},
    "rabbit": {"type": "rabbit", "label": "rabbit", "name": "Rory"},
    "horse": {"type": "horse", "label": "horse", "name": "Hugo"},
}

OBJECTS = {
    "basket": "a basket of apples",
    "lantern": "a little lantern",
    "letter": "a folded letter",
}

GENTLE_TRAITS = ["curious", "patient", "thoughtful", "bright-eyed", "quiet"]
HARD_TRAITS = ["callous", "proud", "hasty"]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


def act_gallop(world: World, hero: Entity) -> None:
    hero.meters["speed"] = hero.meters.get("speed", 0.0) + 1.0
    hero.memes["excitement"] = hero.memes.get("excitement", 0.0) + 1.0
    world.say(f"{hero.id} loved to gallop across the open ground, where the wind felt like a ribbon in the ears.")


def set_scene(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    world.say(
        f"In {world.setting.place}, {hero.id} and {friend.id} met beside {world.setting.path}, "
        f"with {item.label} waiting nearby."
    )


def misunderstanding(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    friend.memes["worry"] = friend.memes.get("worry", 0.0) + 1.0
    world.say(
        f"{friend.id} thought {hero.id} meant to dash away with {item.label}, and {hero.pronoun().capitalize()} "
        f"wondered why {friend.pronoun('subject')} sounded so sharp."
    )
    world.say(
        f"{hero.id} felt a little callous for not explaining sooner, even though the plan had only been to help."
    )


def reveal(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    world.say(
        f"Curiosity nudged {hero.id} to ask a gentle question, and the truth came out: {item.label} was a gift, "
        f"not a trick."
    )
    world.say(
        f"Then {hero.id} and {friend.id} laughed at the mistake, and {friend.id} lowered {friend.pronoun('possessive')} ears in shame."
    )


def resolve(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1.0
    friend.memes["relief"] = friend.memes.get("relief", 0.0) + 1.0
    world.say(
        f"To make it right, {hero.id} shared the work, and together they carried {item.label} home."
    )
    world.say(
        f"After that, {hero.id} still galloped, but now {friend.id} galloped beside {hero.pronoun('object')}, "
        f"and the path felt warmer for both of them."
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting=setting)
    hero_cfg = HEROES[params.hero]
    friend_cfg = FRIENDS[params.friend]
    item_label = OBJECTS[params.object]

    hero = world.add(Entity(id=hero_cfg["name"], kind="character", type=hero_cfg["type"], label=hero_cfg["label"]))
    friend = world.add(Entity(id=friend_cfg["name"], kind="character", type=friend_cfg["type"], label=friend_cfg["label"]))
    item = world.add(Entity(id="item", kind="thing", type=params.object, label=item_label))

    world.facts.update(hero=hero, friend=friend, item=item, setting=setting, params=params)

    set_scene(world, hero, friend, item)
    world.para()
    act_gallop(world, hero)
    misunderstanding(world, hero, friend, item)
    world.para()
    reveal(world, hero, friend, item)
    resolve(world, hero, friend, item)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item"]
    return [
        f'Write a short fable for children about {hero.id}, {friend.id}, and {item.label}, using the word "gallop".',
        f"Tell a gentle story where a curious animal and a friend solve a misunderstanding and end by sharing {item.label}.",
        f'Write a fable-style story with the words "callous" and "curiosity" that ends in kindness after a mistake.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item"]
    return [
        QAItem(
            question=f"Who wanted to gallop in the story?",
            answer=f"{hero.id} wanted to gallop, and {hero.pronoun('subject')} loved the feeling of moving fast across the path.",
        ),
        QAItem(
            question=f"Why did {friend.id} get upset?",
            answer=f"{friend.id} got upset because {friend.pronoun('subject')} thought {hero.id} might take {item.label} away without asking.",
        ),
        QAItem(
            question=f"What helped fix the misunderstanding?",
            answer="Curiosity helped fix it, because someone asked a gentle question and the real plan was explained.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} and {friend.id} sharing the work and galloping together in a friendlier way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to gallop?",
            answer="To gallop is to run very fast, like a horse or pony moving with strong, quick steps.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to know more. A curious animal asks questions and looks carefully at what is happening.",
        ),
        QAItem(
            question="What does callous mean?",
            answer="Callous means not thinking enough about another creature's feelings. In a fable, that choice usually causes trouble.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="meadow", hero="pony", friend="donkey", object="basket"),
    StoryParams(place="lane", hero="fox", friend="rabbit", object="lantern"),
    StoryParams(place="orchard", hero="hare", friend="horse", object="letter"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable world about gallop, callousness, curiosity, and misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--object", choices=OBJECTS)
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
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(list(HEROES))
    friend = args.friend or rng.choice(list(FRIENDS))
    if friend == hero:
        friend = rng.choice([k for k in FRIENDS if k != hero])
    obj = args.object or rng.choice(list(OBJECTS))
    return StoryParams(place=place, hero=hero, friend=friend, object=obj)


ASP_RULES = r"""
place(meadow). place(lane). place(orchard).
hero(pony). hero(fox). hero(hare).
friend(donkey). friend(rabbit). friend(horse).
object(basket). object(lantern). object(letter).
can_gallop(meadow). can_gallop(lane).

misunderstanding(P,H,F,O) :- place(P), hero(H), friend(F), object(O), H != F.
curiosity(H) :- hero(H).
callous(H) :- hero(H).
story(P,H,F,O) :- can_gallop(P), misunderstanding(P,H,F,O), curiosity(H).
#show story/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        if SETTINGS[p].afford_gallop:
            lines.append(asp.fact("can_gallop", p))
    for h in HEROES:
        lines.append(asp.fact("hero", h))
    for f in FRIENDS:
        lines.append(asp.fact("friend", f))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    models = asp.solve(asp_program("#show story/4."), models=0)
    found = set()
    for m in models:
        found.update(asp.atoms(m, "story"))
    py = set()
    for p in SETTINGS:
        if SETTINGS[p].afford_gallop:
            for h in HEROES:
                for f in FRIENDS:
                    if h != f:
                        for o in OBJECTS:
                            py.add((p, h, f, o))
    if found == py:
        print(f"OK: ASP parity matches Python ({len(found)} stories).")
        return 0
    print("MISMATCH")
    if found - py:
        print("only in ASP:", sorted(found - py))
    if py - found:
        print("only in Python:", sorted(py - found))
    return 1


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

    if args.show_asp:
        print(asp_program("#show story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp.solve(asp_program("#show story/4."), models=0)
        atoms = set()
        for m in models:
            atoms.update(asp.atoms(m, "story"))
        for a in sorted(atoms):
            print(a)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
