#!/usr/bin/env python3
"""
A small mystery-style storyworld about a front room, a shared weapon prop,
fairness, repetition, friendship, and curiosity.

Seed tale:
- A child at the front of a club or playroom finds a toy weapon in a costume box.
- Friends each want a turn.
- Repetition matters because the hero keeps checking the same clue.
- Curiosity drives the search for who owns the prop.
- Equity matters because everyone should get a fair chance.
- The ending reveals the prop belongs to the costume bin and is shared safely.

The world is deliberately compact and state-driven:
- physical meters: ownership, placement, hiding, distance, wear, order
- emotional memes: curiosity, worry, fairness, friendship, relief
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
# Core entities and world state
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the front room"
    doorway: str = "the front door"
    desk: str = "the front desk"


@dataclass
class StoryParams:
    place: str
    name: str
    friend: str
    prop: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "front_room": Setting(place="the front room", doorway="the front door", desk="the front desk"),
    "front_hall": Setting(place="the front hall", doorway="the front gate", desk="the front shelf"),
    "front_counter": Setting(place="the front counter", doorway="the front window", desk="the front counter"),
}

NAMES = [
    "Maya", "Nina", "Luca", "Owen", "Zoe", "Iris", "Noah", "Mila", "Eli", "Sage"
]

FRIENDS = [
    "Ari", "Bea", "Finn", "Jules", "Kai", "Pip", "Ren", "Tia", "Uma", "Vera"
]

PROPS = {
    "toy_sword": {
        "label": "toy sword",
        "phrase": "a shiny toy sword",
        "detail": "wooden and smooth",
        "key": "sword",
    },
    "foam_blaster": {
        "label": "foam blaster",
        "phrase": "a bright foam blaster",
        "detail": "light and soft",
        "key": "blaster",
    },
    "cardboard_spear": {
        "label": "cardboard spear",
        "phrase": "a tall cardboard spear",
        "detail": "made for pretend play",
        "key": "spear",
    },
}

FALLBACKS = [
    "The front room was quiet, and every small sound seemed to matter.",
    "The front hall held a neat shelf, a little bench, and one closed box.",
    "The front counter had papers, hooks, and a basket of costume props.",
]

# ---------------------------------------------------------------------------
# Reasonableness / story model
# ---------------------------------------------------------------------------

def valid_props() -> list[str]:
    # This world wants a mystery about a shared prop that can be handled safely.
    return list(PROPS)


def choose_prop(rng: random.Random, prop_id: Optional[str]) -> str:
    if prop_id:
        if prop_id not in PROPS:
            raise StoryError(f"(No story: unknown prop '{prop_id}'.)")
        return prop_id
    return rng.choice(valid_props())


def choose_setting(rng: random.Random, place: Optional[str]) -> str:
    if place:
        if place not in SETTINGS:
            raise StoryError(f"(No story: unknown setting '{place}'.)")
        return place
    return rng.choice(list(SETTINGS))


def reasonableness_gate(place: str, prop: str) -> None:
    # Keep the weapon purely pretend and the front setting suitable for a small mystery.
    if place not in SETTINGS:
        raise StoryError("(No story: the front setting must be one of the curated places.)")
    if prop not in PROPS:
        raise StoryError("(No story: the prop must be one of the curated costume props.)")


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity, friend: Entity, prop: Entity) -> None:
    world.say(
        f"{hero.id} was a curious little {hero.type} who liked to notice tiny clues. "
        f"{friend.id} was {hero.pronoun('possessive')} friend, and together they liked to solve small mysteries."
    )
    world.say(
        f"At {world.setting.place}, a box held {prop.phrase}, and the front of the room felt extra important that day."
    )


def notice(world: World, hero: Entity, prop: Entity) -> None:
    hero.memes["curiosity"] += 1
    prop.meters["seen"] = prop.meters.get("seen", 0.0) + 1
    world.say(
        f"{hero.id} noticed {prop.phrase} near {world.setting.desk}. "
        f"{hero.pronoun().capitalize()} looked at it twice, then looked again, because the same clue kept pulling at {hero.pronoun('object')}."
    )


def ask_again(world: World, hero: Entity, friend: Entity, prop: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f'"Whose is it?" {hero.id} asked. '
        f'{hero.id} asked again, softly, because repetition helped the question feel clearer.'
    )
    world.say(
        f"{friend.id} shrugged, but {friend.pronoun().capitalize()} stayed nearby. "
        f"They both wanted an answer that felt fair."
    )


def share_turns(world: World, hero: Entity, friend: Entity, prop: Entity) -> None:
    hero.memes["fairness"] += 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
    world.say(
        f"{hero.id} suggested they take turns. "
        f"First {hero.id} held {prop.it()}, then {friend.id} held {prop.it()}, then they switched back the other way."
    )
    world.say(
        f"That little pattern made the front room feel calmer, because everyone could see the same rule apply to both friends."
    )


def clue_hunt(world: World, hero: Entity, friend: Entity, prop: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"They checked the same places in order: the basket, the shelf, the hooks, and the box lid. "
        f"Each time they looked, the answer still seemed close but not quite ready."
    )
    world.say(
        f"{hero.id} found a tag tucked under {prop.label}. "
        f"The tag said the prop belonged to the costume box, not to one child alone."
    )


def resolve(world: World, hero: Entity, friend: Entity, prop: Entity) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
    prop.owner = "costume_box"
    world.say(
        f"{hero.id} smiled. The mystery was small, but the answer mattered: {prop.label} was for shared pretend play, not for keeping."
    )
    world.say(
        f"{hero.id} and {friend.id} put {prop.it()} back at the front of the box, so the next child could find it too."
    )
    world.say(
        f"In the quiet front room, the toy weapon stayed safe, and the friends walked away side by side, happy that things had been fair."
    )


# ---------------------------------------------------------------------------
# World assembly
# ---------------------------------------------------------------------------

def tell(place: str, prop_id: str, hero_name: str, friend_name: str) -> World:
    world = World(SETTINGS[place])
    prop_cfg = PROPS[prop_id]

    hero = world.add(Entity(id=hero_name, kind="character", type="child", label=hero_name))
    friend = world.add(Entity(id=friend_name, kind="character", type="child", label=friend_name))
    prop = world.add(
        Entity(
            id=prop_id,
            kind="thing",
            type="toy",
            label=prop_cfg["label"],
            phrase=prop_cfg["phrase"],
            owner="costume_box",
            held_by=None,
        )
    )

    world.facts.update(hero=hero, friend=friend, prop=prop, prop_cfg=prop_cfg, place=place)

    introduce(world, hero, friend, prop)
    world.para()
    notice(world, hero, prop)
    ask_again(world, hero, friend, prop)
    world.para()
    share_turns(world, hero, friend, prop)
    clue_hunt(world, hero, friend, prop)
    world.para()
    resolve(world, hero, friend, prop)

    return world


# ---------------------------------------------------------------------------
# Questions and prompts
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    prop_cfg = f["prop_cfg"]
    place = f["place"]
    return [
        f'Write a short mystery story for a young child set in {place} about a shared {prop_cfg["label"]}.',
        f"Tell a gentle story where {hero.id} and {friend.id} use curiosity and fairness to solve a small front-room mystery.",
        f"Write a story that repeats one clue, shows friendship, and ends with {prop_cfg['label']} being put back for everyone.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    prop_cfg = f["prop_cfg"]
    place = f["place"]
    prop: Entity = f["prop"]

    return [
        QAItem(
            question=f"Who was curious about the {prop_cfg['label']} in {place}?",
            answer=f"{hero.id} was curious about the {prop_cfg['label']}, and {friend.id} stayed close to help.",
        ),
        QAItem(
            question=f"What made the question feel special in the story?",
            answer=f"The question was repeated more than once, which helped {hero.id} keep following the clue.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} show friendship and fairness?",
            answer=f"They took turns with the {prop_cfg['label']} and made sure the same rule worked for both of them.",
        ),
        QAItem(
            question=f"What was the answer to the mystery?",
            answer=f"The {prop_cfg['label']} belonged to the costume box, so it was meant to be shared, not kept by just one child.",
        ),
        QAItem(
            question=f"What happened to the {prop.label} at the end?",
            answer=f"{hero.id} and {friend.id} put it back at the front of the box so everyone could use it safely later.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    prop_cfg = f["prop_cfg"]
    out = [
        QAItem(
            question="What does curiosity help people do?",
            answer="Curiosity helps people ask questions, look closely, and learn new things.",
        ),
        QAItem(
            question="What is fairness?",
            answer="Fairness means people get a kind and equal chance, so one person does not take everything.",
        ),
        QAItem(
            question="Why can repetition help when solving a mystery?",
            answer="Repetition can help because hearing or checking the same clue again makes it easier to notice details.",
        ),
        QAItem(
            question="What does friendship look like?",
            answer="Friendship looks like helping, sharing, listening, and staying close when someone needs a buddy.",
        ),
    ]
    if prop_cfg["key"] == "sword":
        out.append(
            QAItem(
                question="What is a toy sword for?",
                answer="A toy sword is for pretend play and costumes, not for hurting anyone.",
            )
        )
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id:10} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A front-room mystery is valid when the prop is shared, the setting is front-facing,
% and the story can support curiosity, repetition, friendship, and fairness.
shared_prop(P) :- prop(P), costume_prop(P).

front_setting(S) :- setting(S), front(S).

valid_story(S, P) :- front_setting(S), shared_prop(P).

% The story's theme words should be present in the declared world.
theme(curiosity).
theme(repetition).
theme(friendship).
theme(equity).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("front", sid))
    for pid, cfg in PROPS.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("costume_prop", pid))
        lines.append(asp.fact("weapon", pid))
        lines.append(asp.fact("theme_word", cfg["key"]))
    lines.append(asp.fact("theme_word", "equity"))
    lines.append(asp.fact("theme_word", "front"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(s, p) for s in SETTINGS for p in PROPS}
    clingo = set(asp_valid_stories())
    if py == clingo:
        print(f"OK: clingo and Python agree on {len(py)} front-room story pairs.")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - clingo:
        print("  only in python:", sorted(py - clingo))
    if clingo - py:
        print("  only in clingo:", sorted(clingo - py))
    return 1


# ---------------------------------------------------------------------------
# Story sample generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = choose_setting(rng, args.place)
    prop = choose_prop(rng, args.prop)
    reasonableness_gate(place, prop)
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in FRIENDS if n != name])
    if friend == name:
        friend = rng.choice([n for n in FRIENDS if n != name])
    return StoryParams(place=place, name=name, friend=friend, prop=prop)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.prop, params.name, params.friend)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld about a front room, fairness, and a shared toy weapon.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--prop", choices=list(PROPS))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend", choices=FRIENDS)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid front-room story pairs:")
        for s, p in stories:
            print(f"  {s} / {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for prop in PROPS:
                params = StoryParams(place=place, name=NAMES[0], friend=FRIENDS[0], prop=prop)
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
