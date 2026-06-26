#!/usr/bin/env python3
"""
A small animal-story world about dislike, misunderstanding, and a bad ending.

The seed story premise:
- An animal dislikes something common in its home.
- Another animal misunderstands that dislike.
- They try the wrong fix, which makes the problem worse.
- The ending is "bad" in the sense that the misunderstanding is not repaired.
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
# World model
# ---------------------------------------------------------------------------

@dataclass
class Animal:
    name: str
    species: str
    place: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"


@dataclass
class ObjectThing:
    name: str
    kind: str
    place: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    weather: str
    sound: str


@dataclass
class StoryParams:
    setting: str
    hero_species: str
    friend_species: str
    hero_name: str
    friend_name: str
    disliked_thing: str
    misunderstood_message: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, key: str, ent: object) -> object:
        self.entities[key] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "barn": Setting(place="the barn", weather="windy", sound="the rafters creaked softly"),
    "pond": Setting(place="the pond", weather="misty", sound="the water whispered at the reeds"),
    "meadow": Setting(place="the meadow", weather="bright", sound="the grass rustled in little waves"),
}

HERO_SPECIES = ["rabbit", "duck", "cat", "fox", "bear", "mouse"]
FRIEND_SPECIES = ["rabbit", "duck", "cat", "fox", "bear", "mouse"]

HERO_NAMES = {
    "rabbit": ["Pip", "Tilly", "Nori"],
    "duck": ["Dot", "Mimi", "Quin"],
    "cat": ["Miso", "Luna", "Puck"],
    "fox": ["Fenn", "Rory", "Sage"],
    "bear": ["Bruno", "Mabel", "Tuck"],
    "mouse": ["Mina", "Bibi", "Nip"],
}

DISLIKED_THINGS = {
    "mud": ("mud", "mud"),
    "loud rain": ("rain", "loud rain"),
    "straw": ("straw", "scratchy straw"),
    "splashes": ("water", "splashing water"),
    "crowded nook": ("crowd", "a crowded nook"),
}

MISUNDERSTANDINGS = {
    "hiding": "that the friend was hiding the disliked thing on purpose",
    "sharing": "that the friend was trying to share a surprise gift",
    "hurry": "that the friend wanted to hurry because something was wrong",
    "cleaning": "that the friend was cleaning up to help",
}

TRAITS = ["small", "shy", "brave", "quick", "gentle", "curious"]


# ---------------------------------------------------------------------------
# Core story logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.disliked_thing not in DISLIKED_THINGS:
        raise StoryError("Unknown disliked thing.")
    if params.misunderstood_message not in MISUNDERSTANDINGS:
        raise StoryError("Unknown misunderstanding type.")

    setting = SETTINGS[params.setting]
    world = World(setting)

    hero = Animal(name=params.hero_name, species=params.hero_species, place=setting.place)
    friend = Animal(name=params.friend_name, species=params.friend_species, place=setting.place)
    disliked_kind, disliked_phrase = DISLIKED_THINGS[params.disliked_thing]
    disliked = ObjectThing(name=disliked_phrase, kind=disliked_kind, place=setting.place, owner=friend.name)

    world.add("hero", hero)
    world.add("friend", friend)
    world.add("thing", disliked)

    # State meters / memes
    hero.memes["dislike"] = 1.0
    hero.memes["unease"] = 0.0
    friend.memes["care"] = 1.0
    friend.memes["confusion"] = 0.0
    friend.memes["hurt"] = 0.0
    disliked.meters["presence"] = 1.0

    world.facts.update(
        hero=hero,
        friend=friend,
        thing=disliked,
        disliked_phrase=disliked_phrase,
        misunderstood=MISUNDERSTANDINGS[params.misunderstood_message],
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    hero: Animal = world.entities["hero"]  # type: ignore[assignment]
    friend: Animal = world.entities["friend"]  # type: ignore[assignment]
    thing: ObjectThing = world.entities["thing"]  # type: ignore[assignment]
    setting = world.setting

    intro = (
        f"In {setting.place}, little {hero.species} {hero.name} was a {random.choice(TRAITS)} animal "
        f"who did not like {thing.name}."
    )
    world.say(intro)
    world.say(
        f"{hero.name} frowned and said the {thing.kind} made {hero.possessive()} nose wrinkle."
    )
    world.say(
        f"{friend.name} saw that frown and thought {params.misunderstood_message.replace('_', ' ')}."
    )

    world.para()

    # Misunderstanding escalates.
    hero.memes["unease"] += 1.0
    friend.memes["confusion"] += 1.0
    world.say(
        f"So {friend.name} tried to help, but the help was the wrong kind of help."
    )

    if params.misunderstood_message == "hiding":
        world.say(
            f"{friend.name} tucked {thing.name} behind a hay bale and said, "
            f'"Now you will not have to look at it!"'
        )
    elif params.misunderstood_message == "sharing":
        world.say(
            f"{friend.name} brought even more {thing.name} and smiled, hoping it would feel like a gift."
        )
    elif params.misunderstood_message == "hurry":
        world.say(
            f"{friend.name} rushed around the place, making a noisy mess that startled {hero.name}."
        )
    else:
        world.say(
            f"{friend.name} scrubbed and stacked things too fast, bumping into bowls and baskets."
        )

    # Bad ending: the misunderstanding does not get repaired.
    world.para()
    friend.memes["hurt"] += 1.0
    world.say(
        f"{hero.name} thought {friend.name} was being unkind, and {friend.name} thought {hero.name} was being mean."
    )
    world.say(
        f"They turned away from each other while {setting.sound} drifted through {setting.place}."
    )
    world.say(
        f"By bedtime, the little animals still did not understand each other, and the day felt heavy and sad."
    )

    world.facts["bad_ending"] = True
    world.facts["resolved"] = False


# ---------------------------------------------------------------------------
# Narrative output helpers
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero: Animal = world.facts["hero"]  # type: ignore[assignment]
    friend: Animal = world.facts["friend"]  # type: ignore[assignment]
    thing: ObjectThing = world.facts["thing"]  # type: ignore[assignment]
    return [
        f"Write a short animal story where {hero.name} the {hero.species} does not like {thing.name}.",
        f"Tell a gentle story about {friend.name} the {friend.species} misunderstanding {hero.name}'s dislike.",
        f"Write a child-friendly animal tale that ends with a bad ending because the animals never fix the misunderstanding.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Animal = world.facts["hero"]  # type: ignore[assignment]
    friend: Animal = world.facts["friend"]  # type: ignore[assignment]
    thing: ObjectThing = world.facts["thing"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who did not like {thing.name} in the story?",
            answer=f"{hero.name} the {hero.species} did not like {thing.name}.",
        ),
        QAItem(
            question=f"What did {friend.name} misunderstand?",
            answer=f"{friend.name} misunderstood {world.facts['misunderstood']}.",
        ),
        QAItem(
            question="Did the animals fix the problem at the end?",
            answer="No. The misunderstanding stayed unfixed, so the story ended badly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    hero: Animal = world.facts["hero"]  # type: ignore[assignment]
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing about what another animal meant.",
        ),
        QAItem(
            question="What does dislike mean?",
            answer=f"To dislike something means not to like it. In this story, {hero.name} did not like one particular thing.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for key, ent in world.entities.items():
        if isinstance(ent, Animal):
            lines.append(f"{key}: Animal(name={ent.name}, species={ent.species}, place={ent.place}, "
                         f"meters={ent.meters}, memes={ent.memes})")
        elif isinstance(ent, ObjectThing):
            lines.append(f"{key}: ObjectThing(name={ent.name}, kind={ent.kind}, place={ent.place}, "
                         f"owner={ent.owner}, meters={ent.meters}, memes={ent.memes})")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A simple parity twin for the reasonableness gate:
% A story is valid when the hero dislikes a thing, and the friend misunderstands it,
% which leads to a conflict and no resolution.
valid_story(S, H, F, T, M) :- setting(S), hero(H), friend(F), thing(T), misunderstanding(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sp in HERO_SPECIES:
        lines.append(asp.fact("hero", sp))
    for sp in FRIEND_SPECIES:
        lines.append(asp.fact("friend", sp))
    for name in DISLIKED_THINGS:
        lines.append(asp.fact("thing", name))
    for m in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_stories())
    py_cmp = set((s, h, f, t, m) for (s, h, f, t, m) in py)
    if py_cmp == asp_set:
        print(f"OK: ASP matches Python ({len(py_cmp)} story combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if asp_set - py_cmp:
        print("  only in ASP:", sorted(asp_set - py_cmp))
    if py_cmp - asp_set:
        print("  only in Python:", sorted(py_cmp - asp_set))
    return 1


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for hero in HERO_SPECIES:
            for friend in FRIEND_SPECIES:
                if hero == friend:
                    continue
                for thing in DISLIKED_THINGS:
                    for mis in MISUNDERSTANDINGS:
                        combos.append((setting, hero, friend, thing, mis))
    return combos


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal-story world about dislike and misunderstanding.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--hero-species", choices=sorted(HERO_SPECIES))
    ap.add_argument("--friend-species", choices=sorted(FRIEND_SPECIES))
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--disliked-thing", choices=sorted(DISLIKED_THINGS))
    ap.add_argument("--misunderstood-message", choices=sorted(MISUNDERSTANDINGS))
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    hero_species = args.hero_species or rng.choice(HERO_SPECIES)
    friend_species = args.friend_species or rng.choice([s for s in FRIEND_SPECIES if s != hero_species])
    disliked_thing = args.disliked_thing or rng.choice(sorted(DISLIKED_THINGS))
    misunderstood_message = args.misunderstood_message or rng.choice(sorted(MISUNDERSTANDINGS))
    hero_name = args.hero_name or rng.choice(HERO_NAMES[hero_species])
    friend_name = args.friend_name or rng.choice(HERO_NAMES[friend_species])
    return StoryParams(
        setting=setting,
        hero_species=hero_species,
        friend_species=friend_species,
        hero_name=hero_name,
        friend_name=friend_name,
        disliked_thing=disliked_thing,
        misunderstood_message=misunderstood_message,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
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
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} valid story combos")
        for c in combos[:200]:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for setting, hero, friend, thing, mis in valid_combos():
            params = StoryParams(
                setting=setting,
                hero_species=hero,
                friend_species=friend,
                hero_name=HERO_NAMES[hero][0],
                friend_name=HERO_NAMES[friend][0],
                disliked_thing=thing,
                misunderstood_message=mis,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
        header = ""
        if len(samples) > 1:
            p = sample.params
            header = f"### variant {idx + 1}: {p.hero_name} and {p.friend_name} at {p.setting}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
