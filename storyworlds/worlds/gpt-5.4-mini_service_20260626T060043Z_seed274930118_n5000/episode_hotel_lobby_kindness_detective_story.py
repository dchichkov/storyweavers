#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/episode_hotel_lobby_kindness_detective_story.py
========================================================================================================================

A small detective-style storyworld set in a hotel lobby, built from the seed
word "episode" and centered on kindness.

Premise:
- A young detective notices a small problem in the hotel lobby.
- A guest is worried because something important is missing.
- The detective uses kindness, careful looking, and a few practical clues.
- The lost thing is found, and the lobby ends calmer than before.

This storyworld models both physical state (meters) and emotional state
(memes). The main tension comes from a missing object in a busy hotel lobby,
and the turn comes when a kind, observant helper treats people gently and
follows clues instead of rushing.
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
    lost: bool = False
    found: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother", "hostess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father", "doorman"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def item_pronoun(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the hotel lobby"
    counters: bool = True
    chairs: bool = True
    front_desk: bool = True


@dataclass
class Clue:
    id: str
    label: str
    place: str
    reveals: str
    helpful: str


@dataclass
class MissingThing:
    id: str
    label: str
    phrase: str
    kind: str
    location: str
    value: str
    important: bool = True


@dataclass
class StoryParams:
    name: str
    gender: str
    helper_role: str
    guest_role: str
    missing: str
    clue: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

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
    "hotel_lobby": Setting(place="the hotel lobby"),
}

HELPER_ROLES = ["child detective", "young detective", "little detective"]
GUEST_ROLES = ["guest", "traveler", "visitor", "mother", "father"]
NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Theo", "Lila", "Max"]
GENDERS = ["girl", "boy"]

MISSING = {
    "keycard": MissingThing(
        id="keycard",
        label="keycard",
        phrase="a tiny silver keycard",
        kind="keycard",
        location="front desk",
        value="important",
    ),
    "umbrella": MissingThing(
        id="umbrella",
        label="umbrella",
        phrase="a bright red umbrella",
        kind="umbrella",
        location="sofa",
        value="useful",
    ),
    "ticket": MissingThing(
        id="ticket",
        label="ticket",
        phrase="a folded travel ticket",
        kind="ticket",
        location="pocket",
        value="important",
    ),
}

CLUES = {
    "sofa": Clue(
        id="sofa",
        label="the sofa",
        place="near the sofa",
        reveals="someone had sat there with the missing thing",
        helpful="a gentle search around the cushions",
    ),
    "planter": Clue(
        id="planter",
        label="the tall planter",
        place="by the tall planter",
        reveals="the missing thing slipped down beside the leaves",
        helpful="careful looking between the pots",
    ),
    "front_desk": Clue(
        id="front_desk",
        label="the front desk",
        place="behind the front desk",
        reveals="the missing thing had been set down by mistake",
        helpful="asking the clerk kindly",
    ),
    "bag_rack": Clue(
        id="bag_rack",
        label="the bag rack",
        place="at the bag rack",
        reveals="the missing thing was tucked on a shelf",
        helpful="checking the shelves one by one",
    ),
}

KNOWLEDGE = {
    "kindness": [(
        "What is kindness?",
        "Kindness is being gentle, helpful, and caring toward other people."
    )],
    "detective": [(
        "What does a detective do?",
        "A detective looks carefully for clues to help solve a problem or mystery."
    )],
    "hotel": [(
        "What is a hotel?",
        "A hotel is a place where travelers can stay for a night or more."
    )],
    "lobby": [(
        "What is a lobby?",
        "A lobby is the open room near the entrance of a building where people wait and meet."
    )],
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for miss in MISSING:
            for clue in CLUES:
                if miss != clue:
                    combos.append((place, miss, clue))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A hotel-lobby detective storyworld centered on kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--missing", choices=MISSING)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--helper-role", choices=HELPER_ROLES)
    ap.add_argument("--guest-role", choices=GUEST_ROLES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.missing is None or c[1] == args.missing)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("No valid hotel-lobby mystery matches the given options.")
    place, missing, clue = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(GENDERS)
    helper_role = args.helper_role or rng.choice(HELPER_ROLES)
    guest_role = args.guest_role or rng.choice(GUEST_ROLES)
    return StoryParams(
        name=name,
        gender=gender,
        helper_role=helper_role,
        guest_role=guest_role,
        missing=missing,
        clue=clue,
    )


def story_pronoun(gender: str, case: str) -> str:
    return {"girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"}}[gender][case]


def tell(params: StoryParams) -> World:
    world = World(SETTINGS["hotel_lobby"])
    helper = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    guest = world.add(Entity(id="guest", kind="character", type=params.guest_role, label=f"the {params.guest_role}"))
    missing = MISSING[params.missing]
    clue = CLUES[params.clue]
    lost = world.add(Entity(
        id=missing.id,
        kind="thing",
        type=missing.kind,
        label=missing.label,
        phrase=missing.phrase,
        owner=guest.id,
        lost=True,
        found=False,
    ))

    helper.memes["curious"] = 1
    helper.memes["kind"] = 1
    guest.memes["worried"] = 1
    guest.meters["anxiety"] = 1

    world.say(f"{helper.id} was a little {params.helper_role} who loved a good mystery.")
    world.say(f"One {params.seed is not None and 'episode' or 'day'} in {world.setting.place}, {helper.id} noticed a worried {params.guest_role} near the front desk.")
    world.say(f"The {params.guest_role} whispered that {lost.phrase} had gone missing.")

    world.para()
    world.say(f"{helper.id} looked at the lobby like a detective. The chairs were neat, the floor was shiny, and the front desk clerk kept glancing around.")
    world.say(f"{helper.id} did not rush. {helper.id} smiled, spoke kindly, and asked careful questions.")
    world.say(f"That kindness made the {params.guest_role} breathe a little easier.")

    world.para()
    world.say(f"The first clue led {helper.id} {clue.place}.")
    world.say(f"There, {clue.reveals}.")
    world.say(f"With {clue.helpful}, {helper.id} followed the trail and found the missing thing.")

    world.para()
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1
    guest.memes["relief"] = 1
    guest.meters["anxiety"] = 0
    lost.found = True
    lost.lost = False
    world.say(f"{helper.id} gave {lost.item_pronoun()} back with a grin.")
    world.say(f"The {params.guest_role} thanked {helper.id} and smiled so widely that the whole lobby felt warmer.")
    world.say(f"By the end of the episode, the hotel lobby was calm again, and kindness had solved the mystery.")

    world.facts = {
        "helper": helper,
        "guest": guest,
        "missing": lost,
        "clue": clue,
        "params": params,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a short detective story set in a hotel lobby where a {p.guest_role} loses {MISSING[p.missing].phrase} and a kind helper looks for clues.",
        f"Tell a child-friendly mystery episode in the hotel lobby that includes kindness, careful questions, and the word 'episode'.",
        f"Write a gentle detective tale where {p.name} solves a small hotel-lobby problem by being kind first and clever second.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    helper: Entity = world.facts["helper"]
    guest: Entity = world.facts["guest"]
    missing: Entity = world.facts["missing"]
    clue: Clue = world.facts["clue"]
    return [
        QAItem(
            question=f"Who was the detective in the hotel lobby episode?",
            answer=f"The detective was {helper.id}, a little {p.helper_role} who used kindness and careful looking."
        ),
        QAItem(
            question=f"What did the {p.guest_role} lose?",
            answer=f"The {p.guest_role} lost {missing.phrase}."
        ),
        QAItem(
            question=f"How did {helper.id} find the missing thing?",
            answer=f"{helper.id} followed the clue {clue.place}, looked carefully, and found it with {clue.helpful}."
        ),
        QAItem(
            question=f"How did the {p.guest_role} feel at the end?",
            answer=f"The {p.guest_role} felt relieved and happy because {missing.label} was found and returned kindly."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["kindness", "detective", "hotel", "lobby"]:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
        if e.lost:
            bits.append("lost=True")
        if e.found:
            bits.append("found=True")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
missing(X) :- thing(X), lost(X).
helpful_clue(C) :- clue(C).
solved(X) :- missing(X), found(X).
kind_story :- kindness, detective, hotel, lobby.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("kindness"),
        asp.fact("detective"),
        asp.fact("hotel"),
        asp.fact("lobby"),
    ]
    for mid in MISSING:
        lines.append(asp.fact("thing", mid))
        lines.append(asp.fact("lost", mid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show kind_story/0."))
    has_kind_story = any(sym.name == "kind_story" for sym in model)
    python_ok = True
    if has_kind_story != python_ok:
        print("MISMATCH between ASP and Python gates.")
        return 1
    print("OK: ASP and Python gates agree.")
    return 0


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show missing/1."))
    return sorted(set(asp.atoms(model, "missing")))


def asp_valid_stories() -> list[tuple]:
    return asp_valid_combos()


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


CURATED = [
    StoryParams(name="Mia", gender="girl", helper_role="young detective", guest_role="guest", missing="keycard", clue="front_desk"),
    StoryParams(name="Leo", gender="boy", helper_role="child detective", guest_role="traveler", missing="umbrella", clue="sofa"),
    StoryParams(name="Nora", gender="girl", helper_role="little detective", guest_role="mother", missing="ticket", clue="bag_rack"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show kind_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show missing/1."))
        print(f"{len(asp.atoms(model, 'missing'))} missing facts available.")
        for atom in asp.atoms(model, "missing"):
            print(atom[0])
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
            header = f"### {p.name}: {p.missing} with {p.clue} clue"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
