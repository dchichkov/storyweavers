#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/inter_hew_repetition_teamwork_mystery_to_solve.py
================================================================================================

A slice-of-life storyworld about a small mystery solved by repetition and teamwork.

Seed impression:
- Two child-sized helpers keep checking the same cozy places.
- They get stuck on a tiny missing thing.
- They try again together, notice a pattern, and solve it.

This world includes the seed words "inter" and "hew" in a child-friendly way,
and keeps the prose grounded in ordinary home routines.
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the apartment"
    spots: list[str] = field(default_factory=lambda: ["the sofa", "the shoe rack", "the kitchen table", "the hallway shelf"])


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    clue: str
    where_found: str
    hidden_in: str
    searched_spots: list[str] = field(default_factory=list)


@dataclass
class TeamMember:
    id: str
    type: str
    label: str
    trait: str


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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _mem(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _inc_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = _meter(ent, key) + amount


def _inc_mem(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = _mem(ent, key) + amount


def _search(world: World, seeker: Entity, mystery: Mystery, spot: str, narrate: bool = True) -> bool:
    sig = ("search", seeker.id, mystery.id, spot)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    _inc_mem(seeker, "effort")
    _inc_mem(seeker, "worry", 0.2)
    if narrate:
        world.say(f"{seeker.id} looked at {spot} again, just to be sure.")
    if spot == mystery.hidden_in:
        _inc_mem(seeker, "clue", 1.0)
        mystery.searched_spots.append(spot)
        if narrate:
            world.say(f"That time, {seeker.id} spotted a tiny clue: {mystery.clue}.")
        return True
    mystery.searched_spots.append(spot)
    return False


def _teamwork(world: World, a: Entity, b: Entity, narrate: bool = True) -> None:
    sig = ("teamwork", a.id, b.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    _inc_mem(a, "trust", 1.0)
    _inc_mem(b, "trust", 1.0)
    _inc_mem(a, "calm", 0.5)
    _inc_mem(b, "calm", 0.5)
    if narrate:
        world.say(f"{a.id} and {b.id} teamed up and split the list of places between them.")


def _solve(world: World, a: Entity, b: Entity, mystery: Mystery, narrate: bool = True) -> None:
    sig = ("solve", mystery.id)
    if sig in world.fired:
        return
    if _mem(a, "clue") < THRESHOLD or _mem(b, "clue") < THRESHOLD:
        return
    world.fired.add(sig)
    mystery.where_found = mystery.hidden_in
    if narrate:
        world.say(
            f"Then {a.id} and {b.id} put their clues together and found the missing {mystery.label} "
            f"in {mystery.where_found}."
        )
        world.say(f"It had been tucked there all along, waiting for someone patient enough to notice.")


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        team = world.facts["team"]
        mystery = world.facts["mystery"]
        if ("teamwork", team[0].id, team[1].id) not in world.fired:
            _teamwork(world, world.get(team[0].id), world.get(team[1].id), narrate=narrate)
            changed = True
        if ("solve", mystery.id) not in world.fired:
            before = len(world.fired)
            _solve(world, world.get(team[0].id), world.get(team[1].id), mystery, narrate=narrate)
            if len(world.fired) > before:
                changed = True


def tell(setting: Setting, mystery: Mystery, team: list[TeamMember]) -> World:
    world = World(setting)
    one = world.add(Entity(
        id=team[0].id, kind="character", type=team[0].type, label=team[0].label,
        traits=[team[0].trait, "careful"], meters={"effort": 0.0}, memes={"trust": 0.0, "calm": 0.0, "clue": 0.0}
    ))
    two = world.add(Entity(
        id=team[1].id, kind="character", type=team[1].type, label=team[1].label,
        traits=[team[1].trait, "patient"], meters={"effort": 0.0}, memes={"trust": 0.0, "calm": 0.0, "clue": 0.0}
    ))
    item = world.add(Entity(
        id=mystery.id, type="thing", label=mystery.label, phrase=mystery.phrase,
        owner="family", caretaker="family", location=mystery.hidden_in
    ))
    world.facts["team"] = [one, two]
    world.facts["mystery"] = mystery
    world.facts["item"] = item

    # Setup
    world.say(f"{one.id} and {two.id} were having a quiet afternoon at {setting.place}.")
    world.say(f"They were looking for {item.phrase}, because it was needed for the next little task.")
    world.say(f"But the {item.label} was nowhere obvious, so the house felt like a tiny mystery.")

    # Repetition with teamwork
    world.para()
    world.say(f"{one.id} checked the usual places one by one: the sofa, the shoe rack, the kitchen table, and the hallway shelf.")
    world.say(f"Then {two.id} checked the same places again, because sometimes a second look finds what the first look misses.")
    propagate(world, narrate=True)

    # Another round of repetition, now with a better pattern.
    world.para()
    world.say(f"{one.id} said, 'Let's do it together this time.'")
    world.say(f"So they repeated the search, but slower: one child looked high, the other looked low.")
    _search(world, one, mystery, mystery.hidden_in, narrate=True)
    _search(world, two, mystery, mystery.hidden_in, narrate=True)
    propagate(world, narrate=True)

    # Resolution
    world.para()
    world.say(f"In the end, the missing {item.label} was back in the right hands, and the room felt ordinary again.")
    world.say(f"{one.id} smiled at {two.id}, glad that patience and teamwork had solved the little mystery.")
    world.facts["solved"] = True
    world.facts["setting"] = setting
    return world


SETTINGS = {
    "apartment": Setting(place="the apartment"),
    "kitchen": Setting(place="the kitchen"),
    "hallway": Setting(place="the hallway"),
    "porch": Setting(place="the porch"),
}

MYSTERIES = {
    "spoon": Mystery(
        id="spoon",
        label="spoon",
        phrase="the shiny spoon for afternoon snacks",
        clue="a little reflection from the silver handle",
        where_found="the hallway shelf",
        hidden_in="the hallway shelf",
        searched_spots=["the sofa", "the shoe rack", "the kitchen table", "the hallway shelf"],
    ),
    "key": Mystery(
        id="key",
        label="key",
        phrase="the small spare key",
        clue="a soft jingle from the basket",
        where_found="the shoe rack",
        hidden_in="the shoe rack",
        searched_spots=["the sofa", "the shoe rack", "the kitchen table"],
    ),
    "sticker": Mystery(
        id="sticker",
        label="sticker sheet",
        phrase="the bright sticker sheet for a notebook",
        clue="a tiny corner of colorful paper",
        where_found="the kitchen table",
        hidden_in="the kitchen table",
        searched_spots=["the sofa", "the kitchen table", "the hallway shelf"],
    ),
}

TEAM_PRESETS = [
    [TeamMember("Inter", "boy", "Inter", "thoughtful"), TeamMember("Hew", "boy", "Hew", "steady")],
    [TeamMember("Mina", "girl", "Mina", "careful"), TeamMember("Hew", "boy", "Hew", "steady")],
    [TeamMember("Inter", "boy", "Inter", "thoughtful"), TeamMember("Nia", "girl", "Nia", "patient")],
]


@dataclass
class StoryParams:
    place: str
    mystery: str
    seed: Optional[int] = None
    team_index: int = 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life mystery world about repetition and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--team-index", type=int, choices=range(len(TEAM_PRESETS)))
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
    place = args.place or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    team_index = args.team_index if args.team_index is not None else rng.randrange(len(TEAM_PRESETS))
    return StoryParams(place=place, mystery=mystery, team_index=team_index)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    mystery = copy.deepcopy(MYSTERIES[params.mystery])
    team = copy.deepcopy(TEAM_PRESETS[params.team_index])
    world = tell(setting, mystery, team)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    team = world.facts["team"]
    mystery = world.facts["mystery"]
    return [
        "Write a gentle slice-of-life story about two children who keep checking the same places until they solve a tiny mystery.",
        f"Tell a simple story where {team[0].id} and {team[1].id} use teamwork and repetition to find the missing {mystery.label}.",
        f"Write a child-friendly mystery story set at {world.setting.place} that ends with the lost {mystery.label} being found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    team = world.facts["team"]
    mystery = world.facts["mystery"]
    a, b = team[0], team[1]
    return [
        QAItem(
            question=f"Who worked together to solve the mystery?",
            answer=f"{a.id} and {b.id} worked together. They kept checking the same places until they found the missing {mystery.label}.",
        ),
        QAItem(
            question=f"What was the little mystery in the story?",
            answer=f"The mystery was where {mystery.phrase} had gone. It turned out to be in {mystery.hidden_in}.",
        ),
        QAItem(
            question=f"What helped the children solve the problem?",
            answer=f"Repetition and teamwork helped them. They looked again, shared clues, and noticed the pattern together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do different jobs together so the work is easier.",
        ),
        QAItem(
            question="Why do people check again when something is missing?",
            answer="People check again because a second look can reveal something they missed the first time.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not understood right away and needs clues to solve.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"{e.id}: {', '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
spot(X) :- spot_name(X).
teamwork :- character(A), character(B), A < B.
clue(A) :- search(A, _, hidden).
solve :- clue(A), clue(B), A != B.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES.values():
        lines.append(asp.fact("mystery", m.id))
        lines.append(asp.fact("hidden", m.hidden_in))
    for team in TEAM_PRESETS:
        for member in team:
            lines.append(asp.fact("character", member.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show teamwork/0. #show solve/0."))
    atoms = {sym.name for sym in model}
    if "teamwork" in atoms and "solve" in atoms:
        print("OK: ASP twin can derive teamwork and solve.")
        return 0
    print("MISMATCH: ASP twin did not derive expected atoms.")
    return 1


def asp_summary() -> None:
    print("ASP mode is available for verification, but this storyworld is primarily prose-driven.")


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
    StoryParams(place="apartment", mystery="spoon", team_index=0),
    StoryParams(place="kitchen", mystery="key", team_index=1),
    StoryParams(place="hallway", mystery="sticker", team_index=2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show teamwork/0. #show solve/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp_summary()
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.place} / {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
