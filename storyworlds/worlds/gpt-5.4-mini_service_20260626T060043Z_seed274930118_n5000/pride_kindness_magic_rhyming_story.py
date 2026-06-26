#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pride_kindness_magic_rhyming_story.py
===============================================================================================================

A small storyworld about pride, kindness, and a little bit of magic.
The simulated premise is simple: a child makes a proud, rhyming boast,
then a friend uses kind magic to turn the moment into a sweet shared song.

The world is intentionally tiny but state-driven:
- a child has pride, wonder, and a voice;
- a friend has kindness and a magic charm;
- a shared stage or garden can echo a rhyme;
- the child's pride can rise too high, causing the song to go sour;
- kindness and magic can soften pride into joy and togetherness.

This world is built to read like a short rhyming story, not a frozen template.
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


RHYMES = {
    "glow": "show",
    "moon": "tune",
    "star": "far",
    "breeze": "please",
    "light": "bright",
    "song": "long",
    "spark": "park",
}

PLACES = {
    "garden": {"echo": True, "magic": True},
    "stage": {"echo": True, "magic": True},
    "yard": {"echo": False, "magic": True},
    "porch": {"echo": False, "magic": True},
}

CHAR_NAMES = ["Mia", "Luna", "Nora", "Theo", "Finn", "Ruby", "Zara", "Owen"]
FRIEND_NAMES = ["Pip", "Bea", "Tess", "Kai", "June", "Noa", "Milo", "Ada"]
TRAITS = ["bright", "small", "bold", "cheery", "swift", "gentle"]

ASP_RULES = r"""
% A child starts out proud if their pride is high enough.
proud(C) :- pride(C, P), P >= 2.

% A kind magic act can lower pride and raise joy.
softened(C) :- kindness(K), magic(M), pride(C, P), P >= 2, helps(K, C), charms(M, C).

% A story is reasonable when pride can be softened by kindness and magic.
valid_story(Name, Place, Mood) :- child(Name), location(Place), mood(Mood),
                                  at(Name, Place), can_soften(Name), rhymes(Mood).

can_soften(C) :- proud(C), kind_friend(F), helps(F, C), magic_charm(M), charms(M, C).

rhymes(gentle).
rhymes(bright).
rhymes(kind).
"""


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    friend_of: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"presence": 0.0}
        if not self.memes:
            self.memes = {"pride": 0.0, "kindness": 0.0, "joy": 0.0, "worry": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    echo: bool = False
    magic: bool = True


@dataclass
class Charm:
    id: str
    label: str
    rhyme_word: str
    sparkle: str
    softens: bool = True


@dataclass
class StoryParams:
    place: str
    name: str
    friend: str
    trait: str
    rhyme: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


PLACES_REG = {
    k: Place(id=k, label=f"the {k}", echo=v["echo"], magic=v["magic"])
    for k, v in PLACES.items()
}

CHARACTERS = {n: {"type": "girl" if i % 2 == 0 else "boy"} for i, n in enumerate(CHAR_NAMES)}
FRIENDS = {n: {"type": "girl" if i % 2 == 1 else "boy"} for i, n in enumerate(FRIEND_NAMES)}

CHARM = Charm(id="sparkle-charm", label="a tiny sparkle charm", rhyme_word="light", sparkle="soft")


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES_REG.items():
        lines.append(asp.fact("location", pid))
        if p.echo:
            lines.append(asp.fact("echo_place", pid))
        if p.magic:
            lines.append(asp.fact("magic_place", pid))
    for n in CHARACTERS:
        lines.append(asp.fact("child", n))
    for n in FRIENDS:
        lines.append(asp.fact("kind_friend", n))
    lines.append(asp.fact("kindness", "kindness"))
    lines.append(asp.fact("magic_charm", "sparkle_charm"))
    lines.append(asp.fact("helps", "friend", "child"))
    lines.append(asp.fact("charms", "sparkle_charm", "child"))
    lines.append(asp.fact("rhymes", "gentle"))
    lines.append(asp.fact("rhymes", "bright"))
    lines.append(asp.fact("rhymes", "kind"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_story_combos())
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    cl = set(asp.atoms(model, "valid_story"))
    if py == cl:
        print(f"OK: clingo gate matches valid stories ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def valid_story_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES_REG:
        for name in CHARACTERS:
            for rhyme in RHYMES:
                combos.append((place, name, rhyme))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rhyming story world about pride, kindness, and magic.")
    ap.add_argument("--place", choices=PLACES_REG)
    ap.add_argument("--name", choices=CHARACTERS)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--rhyme", choices=sorted(RHYMES))
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
    place = args.place or rng.choice(list(PLACES_REG))
    name = args.name or rng.choice(CHAR_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    rhyme = args.rhyme or rng.choice(list(RHYMES))
    if place not in PLACES_REG:
        raise StoryError("Unknown place.")
    return StoryParams(place=place, name=name, friend=friend, trait=trait, rhyme=rhyme)


def choose_rhyme_word(word: str) -> str:
    return RHYMES[word]


def tell(params: StoryParams) -> World:
    place = PLACES_REG[params.place]
    world = World(place)
    child = world.add(Entity(id=params.name, kind="character", type=CHARACTERS[params.name]["type"], label=params.name))
    friend = world.add(Entity(id=params.friend, kind="character", type=FRIENDS[params.friend]["type"], label=params.friend))
    charm = world.add(Entity(id=CHARM.id, type="charm", label=CHARM.label, phrase=CHARM.label))

    child.memes["pride"] = 2.0
    child.memes["joy"] = 1.0
    friend.memes["kindness"] = 2.0

    rh_word = choose_rhyme_word(params.rhyme)
    world.facts.update(child=child, friend=friend, charm=charm, rhyme=params.rhyme, place=place, rhyme_word=rh_word)

    world.say(f"{child.id} was bright and bold, with a rhyme on the tongue,")
    world.say(f"{{ 'girl': 'she', 'boy': 'he' }[child.type]} liked to sing in a lilting, playful strum.")
    world.say(f"{child.id} said, “I can shine! I can twirl! I can glow!”")
    world.say(f"{child.id} said, “I am best at the sweet little show.”")

    world.para()
    world.say(f"At {place.label}, the air felt warm, and the day felt light,")
    world.say(f"but {child.id}'s proud little words made the rhythm feel tight.")
    child.memes["pride"] += 1.0
    child.memes["worry"] += 1.0
    friend.memes["kindness"] += 1.0

    world.say(f"{friend.id} came near with a smile, and a charm that could gleam,")
    world.say(f"“Let’s make room for each voice,” {friend.pronoun().capitalize()} said, “and share the same dream.”")
    if place.echo:
        world.say("The garden or stage gave each soft note a ring,")
    else:
        world.say("Even without echoes, the calm air could sing.")

    world.para()
    child.memes["pride"] = max(0.0, child.memes["pride"] - 2.0)
    child.memes["joy"] += 2.0
    world.say(f"The charm sent out sparkles like stars in a thread,")
    world.say(f"and pride grew much smaller in {child.id}'s busy head.")
    world.say(f"{child.id} blinked, then laughed, and the voice turned kind,")
    world.say(f"“You may sing the next line, and I’ll follow in time.”")
    world.say(f"So they sang in a pair, with a bounce and a beam,")
    world.say(f"and the rhyme found its place in one happy team.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    place = f["place"].label
    rhyme = f["rhyme"]
    return [
        f'Write a short rhyming story for a young child about pride, kindness, and magic at {place}.',
        f"Tell a gentle rhyme where {child.id} feels too proud, but {friend.id} uses kindness and a tiny charm to help.",
        f'Create a small story that includes the word "{rhyme}" and ends with friends singing together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    place = f["place"].label
    rhyme = f["rhyme"]
    return [
        QAItem(
            question=f"Who was the story about at {place}?",
            answer=f"It was about {child.id}, who started out proud, and {friend.id}, who helped with kindness and magic.",
        ),
        QAItem(
            question=f"What happened when {child.id} got too proud about the rhyme {rhyme}?",
            answer=f"{child.id}'s proud words made the song feel tight, but then {friend.id} stepped in with a kind smile and a little charm.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the two friends singing together, and {child.id} choosing joy and kindness instead of pride.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is being gentle, helpful, and caring toward someone else.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a special story idea that can make surprising things happen, like sparkles, spells, or a helpful charm.",
        ),
        QAItem(
            question="What is pride?",
            answer="Pride is a big feeling of being sure of yourself. It can feel good, but too much pride can make it hard to listen or share.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:12} ({e.kind}/{e.type}) meters={e.meters} memes={e.memes}")
    lines.append(f"  place: {world.place.label}")
    return "\n".join(lines)


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


def asp_facts_program() -> str:
    return asp_facts() + "\n"


def asp_valid_combo_list() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} compatible story tuples:")
        for t in vals:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for place in PLACES_REG:
            for name in CHARACTERS:
                params = StoryParams(place=place, name=name, friend=random.choice(FRIEND_NAMES), trait=random.choice(TRAITS), rhyme=random.choice(list(RHYMES)))
                samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
