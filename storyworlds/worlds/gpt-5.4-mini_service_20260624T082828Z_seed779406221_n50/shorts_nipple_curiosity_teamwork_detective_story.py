#!/usr/bin/env python3
"""
A tiny detective-story world for a curious kid, a small clue, and a teamwork fix.

Premise:
- A child detective in shorts notices a missing baby-bottle nipple.
- Curiosity drives the search through a small setting full of clues.
- Teamwork turns the puzzle into a happy find.

This world keeps the story grounded in simulated state:
- physical meters: found/missing, dusty/clean, tucked/free, hidden/revealed
- emotional memes: curiosity, worry, teamwork, relief
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str
    clue_spots: list[str]


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    helper: str
    clue: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
    "backyard": Setting(
        place="the backyard",
        detail="The yard had a sandbox, a fence, and a row of bushy plants.",
        clue_spots=["sandbox", "fence", "bushes"],
    ),
    "playroom": Setting(
        place="the playroom",
        detail="The room had a toy chest, a rug, and a low table.",
        clue_spots=["toy chest", "rug", "table"],
    ),
    "porch": Setting(
        place="the porch",
        detail="The porch had a shoe rack, a step, and a doormat.",
        clue_spots=["shoe rack", "step", "doormat"],
    ),
}

CLUES = {
    "shorts": {
        "phrase": "a pair of bright blue shorts",
        "label": "shorts",
        "type": "shorts",
        "hide_spot": "clothing basket",
        "story_word": "shorts",
    },
    "nipple": {
        "phrase": "a soft rubber nipple from a baby bottle",
        "label": "nipple",
        "type": "nipple",
        "hide_spot": "toy basket",
        "story_word": "nipple",
    },
}

NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Sam", "Zoe", "Eli"]
HELPERS = ["friend", "sister", "brother", "neighbor"]
GENDERS = ["girl", "boy"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A clue is relevant when it can be hidden somewhere in the chosen setting.
relevant(C, P) :- clue(C), place(P), hides_in(C, Spot), spot(P, Spot).

% A story is valid when curiosity can start, teamwork can help, and the clue is relevant.
valid_story(P, C, G) :- relevant(C, P), curious(G), teamwork(G).

% The detective story is only reasonable if the clue is actually findable.
findable(C, P) :- relevant(C, P), spots(P, _).
#show valid_story/3.
#show findable/2.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for key in SETTINGS:
        lines.append(asp.fact("place", key))
        for spot in SETTINGS[key].clue_spots:
            lines.append(asp.fact("spot", key, spot))
    for key, clue in CLUES.items():
        lines.append(asp.fact("clue", key))
        lines.append(asp.fact("hides_in", key, clue["hide_spot"]))
    for g in GENDERS:
        lines.append(asp.fact("curious", g))
        lines.append(asp.fact("teamwork", g))
    return "\n".join(lines)

def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"

def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: ASP and Python agree on {len(py)} valid stories.")
        return 0
    print("MISMATCH")
    print("python only:", sorted(py - ac))
    print("asp only:", sorted(ac - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for clue in CLUES:
            out.append((place, clue, "girl"))
            out.append((place, clue, "boy"))
    return out


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    detective = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"clean": 1.0},
        memes={"curiosity": 1.0, "worry": 0.0, "teamwork": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type="friend",
        label=f"the {params.helper}",
        meters={"ready": 1.0},
        memes={"teamwork": 1.0},
    ))
    clue = CLUES[params.clue]
    lost_item = world.add(Entity(
        id="Clue",
        kind="thing",
        type=clue["type"],
        label=clue["label"],
        phrase=clue["phrase"],
        owner=detective.id,
        hidden=True,
        meters={"missing": 1.0, "dusty": 0.0, "found": 0.0},
    ))
    detective.meters["wearing_shorts"] = 1.0
    world.facts = {
        "detective": detective,
        "helper": helper,
        "clue": lost_item,
        "setting": setting,
        "params": params,
    }
    return world


def tell_story(world: World) -> None:
    f = world.facts
    d: Entity = f["detective"]
    h: Entity = f["helper"]
    clue: Entity = f["clue"]
    setting: Setting = f["setting"]

    world.say(
        f"{d.id} was a little detective in shorts who loved solving tiny mysteries."
    )
    world.say(
        f"One afternoon, {d.id} and {h.label} came to {setting.place}. {setting.detail}"
    )
    world.say(
        f"Then {d.id} noticed a problem: {clue.phrase} was missing."
    )

    d.memes["curiosity"] += 1.0
    d.memes["worry"] += 1.0
    clue.meters["missing"] = 1.0

    world.para()
    world.say(
        f"{d.id} looked under the {setting.clue_spots[0]}, behind the {setting.clue_spots[1]}, "
        f"and near the {setting.clue_spots[2]}. {d.pronoun().capitalize()} followed every small clue."
    )
    world.say(
        f"{h.label} helped by lifting boxes and checking corners. "
        f"That teamwork made the search feel less scary."
    )
    d.memes["teamwork"] += 1.0
    h.memes["teamwork"] += 1.0

    world.para()
    clue.hidden = False
    clue.meters["found"] = 1.0
    clue.meters["missing"] = 0.0
    clue.meters["dusty"] = 1.0

    world.say(
        f"At last, {d.id} spotted the {clue.label} tucked in a small hiding place."
    )
    world.say(
        f"{h.label} handed it over, and {d.id} gave a happy grin. "
        f"The little detective brushed it clean and felt relief wash over {d.pronoun('object')}."
    )
    d.memes["worry"] = 0.0
    d.memes["relief"] += 1.0
    clue.meters["dusty"] = 0.0

    world.para()
    world.say(
        f"By the end, {d.id} still wore {d.pronoun('possessive')} shorts, "
        f"the lost {clue.label} was safe again, and {d.id} and {h.label} walked home smiling."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        f'Write a short detective story for a child in which {p.name} wears shorts and searches for a lost {p.clue}.',
        f"Tell a gentle mystery about {p.name} the detective, {p.helper} teamwork, and a missing {p.clue}.",
        f'Create a child-friendly detective story that uses the words "{p.clue}" and "shorts".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d: Entity = f["detective"]
    h: Entity = f["helper"]
    clue: Entity = f["clue"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"What did {d.id} wear while solving the mystery?",
            answer=f"{d.id} wore shorts while acting like a little detective."
        ),
        QAItem(
            question=f"What was missing at {setting.place}?",
            answer=f"The missing thing was {clue.phrase}."
        ),
        QAItem(
            question=f"Who helped {d.id} look for the missing {clue.label}?",
            answer=f"{h.label} helped by checking places and using teamwork."
        ),
        QAItem(
            question=f"How did {d.id} feel after the {clue.label} was found?",
            answer=f"{d.id} felt relieved and happy after the lost {clue.label} was found."
        ),
    ]


WORLD_QA = [
    QAItem(
        question="What is curiosity?",
        answer="Curiosity is the feeling that makes someone want to know more and look for answers.",
    ),
    QAItem(
        question="What is teamwork?",
        answer="Teamwork means people help each other and work together to do a job.",
    ),
    QAItem(
        question="What does a detective do?",
        answer="A detective looks for clues and uses them to solve a mystery.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_QA)


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
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--clue", choices=sorted(CLUES))
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
    combos = valid_combos()
    combos = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.clue is None or c[1] == args.clue)
        and (args.gender is None or c[2] == args.gender)
    ]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, clue, gender = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        clue=clue,
        gender=args.gender or gender,
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


def valid_combos_with_gender() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for clue in CLUES:
                for gender in GENDERS:
                    params = StoryParams(
                        place=place,
                        clue=clue,
                        gender=gender,
                        name=NAMES[(len(samples)) % len(NAMES)],
                        helper=HELPERS[(len(samples)) % len(HELPERS)],
                        seed=base_seed + len(samples),
                    )
                    samples.append(generate(params))
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
