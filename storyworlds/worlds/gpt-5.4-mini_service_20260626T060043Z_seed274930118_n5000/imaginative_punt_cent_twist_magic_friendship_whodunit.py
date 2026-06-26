#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/imaginative_punt_cent_twist_magic_friendship_whodunit.py
==============================================================================================================================

A small whodunit storyworld: a child, a missing cent, a twist, a little magic,
and a friendship that helps solve the mystery.

The story premise is intentionally tiny and state-driven:
- a coin goes missing from a jar
- several characters have access and motives
- clues are gathered by looking at physical traces and emotional reactions
- the ending reveals who took the cent and why, plus how friendship repairs the hurt

Seed words used in the world and story text:
- imaginative
- punt
- cent

Style:
- child-facing whodunit
- concrete clues
- one twist
- a gentle magical element
- a friendship resolution
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
    carried_by: Optional[str] = None
    holds: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"present": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "joy": 0.0, "guilt": 0.0, "curiosity": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    label: str
    indoor: bool = True
    clue_spots: tuple[str, ...] = ("table", "floor", "shelf")


@dataclass
class SuspectProfile:
    id: str
    type: str
    label: str
    motive: str
    alibi: str
    tell: str
    can_take: bool


@dataclass
class StoryParams:
    place: str
    hero_name: str
    friend_name: str
    suspect: str
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
        import copy as _copy

        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_touch_clue(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters.get("dusty", 0.0) >= THRESHOLD and ("dusty", ent.id) not in world.fired:
            world.fired.add(("dusty", ent.id))
            out.append(f"A dusty trace showed up on {ent.label}.")
    return out


def _r_guilt_spill(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes.get("guilt", 0.0) >= THRESHOLD and ("guilt", ent.id) not in world.fired:
            world.fired.add(("guilt", ent.id))
            out.append(f"{ent.label} looked like someone carrying a secret.")
    return out


CAUSAL_RULES = [Rule("touch_clue", _r_touch_clue), Rule("guilt_spill", _r_guilt_spill)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "hall": Place(label="the hall", indoor=True, clue_spots=("table", "bench", "door")),
    "library": Place(label="the library", indoor=True, clue_spots=("desk", "shelf", "rug")),
    "cafe": Place(label="the cafe", indoor=True, clue_spots=("counter", "jar", "floor")),
}

SUSPECTS = {
    "cat": SuspectProfile(
        id="cat", type="cat", label="the cat",
        motive="wanted the shiny coin to roll",
        alibi="was napping in a sunbeam",
        tell="had a tiny paw print on the rug",
        can_take=False,
    ),
    "magician": SuspectProfile(
        id="magician", type="person", label="the magician",
        motive="needed a coin for a trick",
        alibi="was practicing a hat trick",
        tell="wore a sleeve with silver thread",
        can_take=True,
    ),
    "brother": SuspectProfile(
        id="brother", type="boy", label="the brother",
        motive="wanted to buy a sweet bun",
        alibi="said he was outside kicking a ball",
        tell="had crumbs on his shirt",
        can_take=True,
    ),
    "neighbor": SuspectProfile(
        id="neighbor", type="girl", label="the neighbor",
        motive="wanted to make a wish at the fountain",
        alibi="was helping set the table",
        tell="had wet shoelaces",
        can_take=True,
    ),
}

NAMES = ["Maya", "Nina", "Iris", "Owen", "Theo", "Lena", "June", "Ari"]
FRIEND_NAMES = ["Pip", "Milo", "Zara", "Noa", "Bea", "Finn"]
TRAITS = ["imaginative", "curious", "careful", "brave", "patient"]


@dataclass
class Knowledge:
    item: str
    description: str


KNOWLEDGE = {
    "cent": Knowledge("cent", "A cent is a very small coin, worth one penny."),
    "magic": Knowledge("magic", "Magic in stories often looks like a surprising trick that seems impossible at first."),
    "friendship": Knowledge("friendship", "Friendship means helping, listening, and caring about someone even when things feel hard."),
    "whodunit": Knowledge("whodunit", "A whodunit is a mystery story where the reader wonders who did the thing."),
    "punt": Knowledge("punt", "To punt a ball means to kick it forward with your foot."),
    "twist": Knowledge("twist", "A twist is a surprise change in a story that makes things feel different at the end."),
}


@dataclass
class Mystery:
    thief: str
    reason: str
    hiding_place: str
    twist: str


MYSTERIES = {
    "magician": Mystery(
        thief="magician",
        reason="needed the cent for a trick that only worked with an exact coin",
        hiding_place="the inside pocket of a sleeve",
        twist="the magician had not stolen the cent to keep it; the coin was part of a practice trick and had slipped away",
    ),
    "brother": Mystery(
        thief="brother",
        reason="wanted to buy a bun from the little stand",
        hiding_place="under the rug",
        twist="the brother had taken the cent, but only to pay back a debt he thought he owed",
    ),
    "neighbor": Mystery(
        thief="neighbor",
        reason="wanted to drop it into the fountain for a wish",
        hiding_place="inside a teacup",
        twist="the neighbor took the cent, but then forgot it was in her pocket because she was helping everyone else",
    ),
}


CURATED = [
    StoryParams(place="cafe", hero_name="Maya", friend_name="Pip", suspect="magician"),
    StoryParams(place="library", hero_name="Lena", friend_name="Bea", suspect="brother"),
    StoryParams(place="hall", hero_name="Owen", friend_name="Zara", suspect="neighbor"),
]

ASP_RULES = r"""
% A whodunit is valid when the story has a place, a missing cent, one suspect,
% a clue, a magical element, and a friendship resolution.
missing_cent(P) :- place(P), cent(C), absent(C), at(C, P).
suspect(S) :- has_motive(S), can_access(S, P), place(P).
can_access(S, P) :- suspect_place(S, P).
clue(S) :- tell(S, _).
magic_event(P) :- magical_place(P).
friendship_fix(H, F) :- friend(H, F), resolves_with_talk(H, F).

valid_story(P, S) :- missing_cent(P), suspect(S), clue(S), magic_event(P), friendship_fix(hero, friend).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoor:
            lines.append(asp.fact("indoor", pid))
        for spot in place.clue_spots:
            lines.append(asp.fact("spot", pid, spot))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("has_motive", sid))
        lines.append(asp.fact("tell", sid, s.tell))
        if s.can_take:
            lines.append(asp.fact("can_access", sid, "any"))
    lines.append(asp.fact("cent", "coin"))
    lines.append(asp.fact("absent", "coin"))
    lines.append(asp.fact("magical_place", "cafe"))
    lines.append(asp.fact("friend", "hero", "friend"))
    lines.append(asp.fact("resolves_with_talk", "hero", "friend"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES:
        for suspect, profile in SUSPECTS.items():
            if place == "library" and suspect == "magician":
                combos.append((place, suspect))
            elif place == "cafe" and suspect in {"magician", "neighbor"}:
                combos.append((place, suspect))
            elif place == "hall" and suspect in {"brother", "neighbor"}:
                combos.append((place, suspect))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld with magic and friendship.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--trait", choices=TRAITS)
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


def explain_rejection(place: str, suspect: str) -> str:
    return f"(No story: the clue pattern does not fit a {suspect} mystery at {place}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.suspect:
        combos = [c for c in combos if c[1] == args.suspect]
    if not combos:
        raise StoryError("(No valid mystery matches the given options.)")
    place, suspect = rng.choice(sorted(combos))
    hero = args.hero_name or rng.choice(NAMES)
    friend = args.friend_name or rng.choice(FRIEND_NAMES)
    return StoryParams(place=place, hero_name=hero, friend_name=friend, suspect=suspect, seed=None)


def _do_magic(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["curiosity"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"At the back of the room, a small magic trick made the cent seem to vanish again, "
        f"and that gave {hero.id} a new idea."
    )


def tell(place: Place, hero_name: str, friend_name: str, suspect: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", label=hero_name))
    friend = world.add(Entity(id=friend_name, kind="character", type="boy", label=friend_name))
    suspect_profile = SUSPECTS[suspect]
    s = world.add(Entity(id=suspect_profile.id, kind="character", type=suspect_profile.type, label=suspect_profile.label))
    coin = world.add(Entity(id="coin", type="coin", label="the cent", phrase="a tiny cent"))
    coin.carried_by = suspect_profile.id
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["suspect"] = s
    world.facts["coin"] = coin
    world.facts["place"] = place
    world.facts["trait"] = trait
    world.facts["mystery"] = MYSTERIES[suspect]

    world.say(
        f"{hero_name} was an {trait} little detective who loved a good whodunit."
    )
    world.say(
        f"{friend_name} was {hero_name}'s best friend, and together they liked to imagine clues "
        f"as if the room itself were telling a secret."
    )
    world.say(
        f"That afternoon, a shiny cent disappeared from the jar at {place.label}."
    )
    world.para()
    world.say(
        f"{hero_name} looked first at the floor, then at the table, then at the shelf."
    )
    world.say(
        f"{friend_name} pointed to the {suspect_profile.tell}."
    )
    world.say(
        f"The suspect, {suspect_profile.label}, had {suspect_profile.alibi}."
    )
    _do_magic(world, hero, friend)
    world.para()
    world.say(
        f"{hero_name} asked careful questions and noticed that {suspect_profile.label} kept glancing "
        f"toward a small hiding place."
    )
    world.say(
        f"Finally, the clue led them to {MYSTERIES[suspect].hiding_place}."
    )
    if suspect == "magician":
        world.say("That was the twist: the cent was part of a magic practice, not a mean theft.")
    elif suspect == "brother":
        world.say("That was the twist: the cent had been taken for a snack, but not to be cruel.")
    else:
        world.say("That was the twist: the cent had been tucked away during a busy moment, not stolen forever.")
    world.para()
    world.say(
        f"{hero_name} and {friend_name} returned the cent, and the truth made the room feel lighter."
    )
    world.say(
        f"{hero_name} kept the mystery book closed at the end and smiled at {friend_name}, because friendship had solved the case."
    )
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    place = f["place"]
    suspect = f["suspect"]
    return [
        f'Write a child-friendly whodunit set at {place.label} where a cent goes missing and {hero.id} investigates with {friend.id}.',
        f"Tell a mystery story with a twist, a little magic, and friendship where {suspect.label} is suspected of taking a cent.",
        f'Write an imaginative whodunit that uses the words "imaginative", "punt", and "cent".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    suspect = f["suspect"]
    mystery = f["mystery"]
    place = f["place"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"Who helped {hero.id} look for the missing cent at {place.label}?",
            answer=f"{friend.id} helped {hero.id}. They worked together like true friends."
        ),
        QAItem(
            question=f"What clue made {hero.id} suspect {suspect.label}?",
            answer=f"The clue was that {suspect.label} had {suspect.meters.get('dusty', 0.0) and 'a dusty trace' or suspect_profile_clue(suspect.id)}."
        ),
        QAItem(
            question=f"What was the twist in the mystery?",
            answer=f"The twist was that {mystery.twist}."
        ),
        QAItem(
            question=f"Why did the cent matter in the story?",
            answer=f"The cent mattered because someone needed it for a small reason, and its disappearance started the whodunit."
        ),
        QAItem(
            question=f"How did {trait} {hero.id} solve the case?",
            answer=f"{hero.id} solved the case by asking questions, following clues, and listening to {friend.id}."
        ),
        QAItem(
            question=f"What helped the ending feel happy?",
            answer=f"Friendship helped the ending feel happy, because {hero.id} and {friend.id} told the truth and put things right."
        ),
    ]


def suspect_profile_clue(sid: str) -> str:
    return SUSPECTS[sid].tell


def world_knowledge_qa(world: World) -> list[QAItem]:
    keys = ["cent", "magic", "friendship", "whodunit", "punt", "twist"]
    return [QAItem(question=f"What is {k}?", answer=v.description) for k, v in KNOWLEDGE.items() if k in keys]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], params.hero_name, params.friend_name, params.suspect, "imaginative")
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


def build_asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(build_asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        program = build_asp_program("#show valid_story/2.")
        model = asp.one_model(program)
        print(f"{len(asp.atoms(model, 'valid_story'))} compatible stories:")
        for pair in asp.atoms(model, "valid_story"):
            print(" ", pair)
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.hero_name} at {p.place} with {p.suspect}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
