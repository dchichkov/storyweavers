#!/usr/bin/env python3
"""
storyworlds/worlds/compression_pappo_sharing_inner_monologue_animal_story.py
============================================================================

A small animal-story world about sharing, a little compression mishap, and the
quiet thoughts that help the characters choose kindly.

The seed tale:
---
A small fox named Pippa found a bouncy pappo toy in the grass. She loved to
squeeze it until it got tiny and springy again. Her friend Momo the mouse also
wanted to play with it. Pippa first wanted to keep it all to herself, and she
thought about how nice the toy felt in her paws. But when she watched Momo wait
patiently, she felt a tug in her chest. She decided to share the pappo, and
together they took turns squeezing it and tossing it gently. The toy stayed
tiny and bouncy, and both friends laughed until the sun slid down.

World model:
---
- One small animal hero owns a pappo toy.
- The pappo can be compressed into a smaller, springier form.
- Another animal wants a turn.
- A private inner monologue can shift the hero from possessive to generous.
- Sharing resolves the tension and ends with a concrete, happy image.

This script follows the Storyweavers contract:
- self-contained stdlib storyworld
- eager results import for QAItem / StoryError / StorySample
- lazy asp import only inside ASP helpers
- includes StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- includes inline ASP_RULES and a Python reasonableness gate
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"fox", "rabbit", "cat", "dog", "mouse"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the meadow"
    affords: set[str] = field(default_factory=set)


@dataclass
class Animal:
    species: str
    name: str
    trait: str
    friend: str


@dataclass
class Toy:
    label: str
    phrase: str
    softness: str
    compressed_phrase: str
    can_compress: bool = True


@dataclass
class StoryParams:
    setting: str
    hero: str
    friend: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "meadow": Setting(place="the meadow", affords={"play"}),
    "garden": Setting(place="the garden", affords={"play"}),
    "riverbank": Setting(place="the riverbank", affords={"play"}),
    "yard": Setting(place="the yard", affords={"play"}),
}

HEROES = {
    "pippa": Animal(species="fox", name="Pippa", trait="clever", friend="Momo"),
    "miri": Animal(species="rabbit", name="Miri", trait="gentle", friend="Toto"),
    "nino": Animal(species="cat", name="Nino", trait="bright", friend="Lulu"),
    "suki": Animal(species="dog", name="Suki", trait="cheerful", friend="Bea"),
}

FRIENDS = ["Momo", "Toto", "Lulu", "Bea", "Nori", "Pip"]

TRAITS = ["clever", "gentle", "curious", "cheerful", "brave", "patient"]

PAPPO = Toy(
    label="pappo",
    phrase="a round pappo toy",
    softness="soft",
    compressed_phrase="tiny and springy",
    can_compress=True,
)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for hero in HEROES:
            for friend in FRIENDS:
                if friend != HEROES[hero].friend:
                    continue
                combos.append((setting, hero, friend))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if params.hero not in HEROES:
        raise StoryError("Unknown hero choice.")
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting choice.")
    hero = HEROES[params.hero]
    if params.friend != hero.friend:
        raise StoryError(f"(No story: {hero.name} is paired with {hero.friend}, not {params.friend}.)")


def setting_line(world: World) -> str:
    return {
        "the meadow": "The meadow was wide and green, with little flowers bending in the wind.",
        "the garden": "The garden was quiet, with warm dirt and bright leaves all around.",
        "the riverbank": "The riverbank glittered softly, and the water made a gentle hush.",
        "the yard": "The yard had a sunny patch of grass where small paws could hop and play.",
    }[world.setting.place]


def compress_toy(world: World, hero: Entity, toy: Entity) -> None:
    toy.meters["compressed"] = 1.0
    hero.meters["joy"] = hero.meters.get("joy", 0) + 1.0
    world.say(
        f"{hero.id} squeezed the {toy.label}, and {toy.label} turned {PAPPO.compressed_phrase} in {hero.pronoun('possessive')} paws."
    )


def share_turn(world: World, hero: Entity, friend: Entity, toy: Entity) -> None:
    hero.memes["generous"] = hero.memes.get("generous", 0) + 1.0
    friend.memes["happy"] = friend.memes.get("happy", 0) + 1.0
    toy.meters["shared"] = toy.meters.get("shared", 0) + 1.0
    world.say(
        f"{hero.id} held the {toy.label} out to {friend.id}, and they took turns pressing it soft and slow."
    )


def inner_monologue(world: World, hero: Entity, friend: Entity, toy: Entity) -> bool:
    hero.memes["possessive"] = hero.memes.get("possessive", 0) + 1.0
    world.say(
        f"Inside, {hero.id} thought, \"I like how the {toy.label} feels when I hold it.\""
    )
    if friend.memes.get("waiting", 0) >= THRESHOLD:
        world.say(
            f"Then another thought came: \"{friend.id} is waiting kindly. I can share.\""
        )
        return True
    return False


def wait_patiently(world: World, friend: Entity) -> None:
    friend.memes["waiting"] = friend.memes.get("waiting", 0) + 1.0
    world.say(f"{friend.id} waited with a small smile and looked at the {PAPPO.label} kindly.")


def ending_image(world: World, hero: Entity, friend: Entity, toy: Entity) -> None:
    world.say(
        f"In the end, the {toy.label} stayed tiny and bouncy, and {hero.id} and {friend.id} laughed together in the {world.setting.place.split()[-1]}."
    )


def tell(setting_key: str, hero_key: str, friend_name: str) -> World:
    setting = SETTINGS[setting_key]
    hero_cfg = HEROES[hero_key]
    world = World(setting)
    hero = world.add(Entity(id=hero_cfg.name, kind="character", type=hero_cfg.species, label=hero_cfg.name))
    friend = world.add(Entity(id=friend_name, kind="character", type="mouse", label=friend_name))
    toy = world.add(Entity(
        id="pappo",
        kind="thing",
        type="toy",
        label="pappo",
        phrase=PAPPO.phrase,
        owner=hero.id,
        caretaker=hero.id,
    ))
    world.facts.update(hero=hero, friend=friend, toy=toy, setting=setting, hero_cfg=hero_cfg)

    world.say(f"{hero.id} was a {hero_cfg.trait} little {hero_cfg.species} who found {PAPPO.phrase} in {setting.place}.")
    world.say(f"{hero.id} loved to compress the {toy.label} until it felt {PAPPO.compressed_phrase}.")
    world.say(f"{friend.id} was {hero_cfg.friend} and wanted a turn too.")

    world.para()
    world.say(setting_line(world))
    wait_patiently(world, friend)
    if inner_monologue(world, hero, friend, toy):
        share_turn(world, hero, friend, toy)
    compress_toy(world, hero, toy)
    share_turn(world, hero, friend, toy)

    world.para()
    ending_image(world, hero, friend, toy)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    return [
        f"Write a short animal story about {hero.id} and {friend.id} sharing a pappo toy after a small thought inside.",
        f"Tell a child-friendly story where compression makes a toy smaller, and a kind inner monologue helps an animal share.",
        f"Write an animal story with the word 'compression' and the toy name 'pappo' that ends with two friends playing together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    toy: Entity = f["toy"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who found the pappo toy in {setting.place}?",
            answer=f"{hero.id} found the pappo toy in {setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} think about before sharing the pappo?",
            answer=f"{hero.id} thought about how nice the pappo felt to hold, and then noticed that {friend.id} was waiting kindly.",
        ),
        QAItem(
            question=f"What changed when {hero.id} shared the pappo with {friend.id}?",
            answer=f"The pappo stayed tiny and springy, and both friends got to take turns with it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does compression mean?",
            answer="Compression means pressing something so it takes up less space or becomes smaller and tighter.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use or enjoy something too, often by taking turns.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet talking a character does in their own mind, like private thoughts.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
friend(F) :- friend_name(F).
toy(t).
share_story(S,H,F) :- setting(S), hero(H), friend(F), paired(H,F).
good_story(S,H,F) :- share_story(S,H,F), toy(t), can_compress(t).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, h in HEROES.items():
        lines.append(asp.fact("hero_name", h.name))
        lines.append(asp.fact("paired", h.name, h.friend))
        lines.append(asp.fact("species", h.name, h.species))
    lines.append(asp.fact("toy", "t"))
    lines.append(asp.fact("can_compress", "t"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show share_story/3."))
    asp_set = set(asp.atoms(model, "share_story"))
    py_set = set()
    for s, h, f in valid_combos():
        py_set.add((s, h, f))
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("Only in ASP:", sorted(asp_set - py_set))
    print("Only in Python:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about sharing, compression, and an inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
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
    hero_key = args.hero or rng.choice(sorted(HEROES))
    hero = HEROES[hero_key]
    if args.friend and args.friend != hero.friend:
        raise StoryError(f"(No story: {hero.name} is paired with {hero.friend}, not {args.friend}.)")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    friend = args.friend or hero.friend
    params = StoryParams(setting=setting, hero=hero_key, friend=friend, trait=hero.trait)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(params.setting, params.hero, params.friend)
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
        print(asp_program("#show share_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show share_story/3."))
        triples = sorted(set(asp.atoms(model, "share_story")))
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting, hero, friend in valid_combos()[:5]:
            params = StoryParams(setting=setting, hero=hero, friend=friend, trait=HEROES[hero].trait, seed=base_seed)
            samples.append(generate(params))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
