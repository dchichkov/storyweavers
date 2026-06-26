#!/usr/bin/env python3
"""
storyworlds/worlds/sentry_sharing_rhyme_whodunit.py
====================================================

A small whodunit-style story world about a sentry, a shared rhyme, and a clue
that changes hands.

Premise:
- A night watch at a tiny museum or gate goes wrong when a secret token goes missing.
- The sentry notices that two people keep sharing the same rhyme to talk in code.
- The rhyme is harmless on its own, but it becomes a clue because only one person
  knows where the token was last seen.

Story logic:
- A sentry keeps a place safe and tracks visitors.
- Sharing can transfer an object, a clue, or trust from one character to another.
- A rhyme can be used as a code phrase, memory aid, or misleading alibi.
- The mystery resolves when the shared rhyme is traced to the true culprit.

This script is intentionally self-contained and uses only stdlib plus the shared
results containers. ASP helpers are imported lazily inside ASP helpers.
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
    holds: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
    kind: str = "place"
    shadows: bool = False
    quiet: bool = True
    clues: list[str] = field(default_factory=list)


@dataclass
class ObjectToken:
    id: str
    label: str
    phrase: str
    owner: Optional[str] = None
    hidden: bool = False
    shared: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Rhyme:
    id: str
    line: str
    meaning: str
    clue_about: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if isinstance(e, Entity) and e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    sentry: str
    suspect: str
    helper: str
    token: str
    rhyme: str
    seed: Optional[int] = None


PLACES = {
    "gatehouse": Place(id="gatehouse", label="the gatehouse", shadows=True, quiet=True),
    "museum": Place(id="museum", label="the small museum", shadows=True, quiet=True),
    "dock": Place(id="dock", label="the moonlit dock", shadows=False, quiet=True),
}

TOKENS = {
    "key": ObjectToken(id="key", label="brass key", phrase="a brass key with a cold tooth"),
    "pin": ObjectToken(id="pin", label="silver pin", phrase="a silver pin with a round head"),
    "map": ObjectToken(id="map", label="folded map", phrase="a folded map with a red mark"),
}

RHYMES = {
    "bell": Rhyme(id="bell", line="When the bell sings low, the shadows go.", meaning="the watch is changing", clue_about="the sentry"),
    "stone": Rhyme(id="stone", line="By the old blue stone, the lost thing goes home.", meaning="the hidden token was moved near the stone", clue_about="the culprit"),
    "moth": Rhyme(id="moth", line="If the moth flies by, keep one eye dry.", meaning="a witness saw someone leave in the rain", clue_about="the helper"),
}

NAMES = ["Ada", "Milo", "June", "Nico", "Tess", "Owen", "Mina", "Iris", "Theo", "Luna"]
TRAITS = ["careful", "curious", "quiet", "brave", "shy", "sharp"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world with a sentry, sharing, and rhyme clues.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sentry")
    ap.add_argument("--suspect")
    ap.add_argument("--helper")
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--rhyme", choices=RHYMES)
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
    place = args.place or rng.choice(list(PLACES))
    sentry = args.sentry or rng.choice(NAMES)
    suspect = args.suspect or rng.choice([n for n in NAMES if n != sentry])
    helper = args.helper or rng.choice([n for n in NAMES if n not in {sentry, suspect}])
    token = args.token or rng.choice(list(TOKENS))
    rhyme = args.rhyme or rng.choice(list(RHYMES))
    if sentry == suspect or sentry == helper or helper == suspect:
        raise StoryError("The sentry, suspect, and helper must be different people.")
    return StoryParams(place=place, sentry=sentry, suspect=suspect, helper=helper, token=token, rhyme=rhyme)


def _move_token(world: World, token: ObjectToken, new_owner: Optional[str]) -> None:
    old = token.owner
    token.owner = new_owner
    token.shared = True
    if old == new_owner:
        return


def _investigate(world: World, sentry: Entity, suspect: Entity, helper: Entity, token: ObjectToken, rhyme: Rhyme) -> None:
    if token.hidden:
        world.say(f"{sentry.id} noticed the {token.label} was gone, and the room felt too quiet.")
    world.say(
        f"{sentry.id} remembered a strange rhyme: “{rhyme.line}” "
        f"It sounded like a game, but games can hide clues."
    )
    world.say(
        f"{suspect.id} had been whispering the same rhyme, and {helper.id} had heard it too."
    )


def _share_clue(world: World, helper: Entity, sentry: Entity, rhyme: Rhyme) -> None:
    helper.memes["trust"] = helper.memes.get("trust", 0) + 1
    sentry.memes["trust"] = sentry.memes.get("trust", 0) + 1
    world.say(
        f"{helper.id} finally shared what {helper.pronoun()} knew: the rhyme meant {rhyme.meaning}."
    )


def _reveal(world: World, sentry: Entity, suspect: Entity, helper: Entity, token: ObjectToken, rhyme: Rhyme) -> None:
    world.say(
        f"{sentry.id} followed the clue to the old blue stone, where {suspect.id} had tucked the {token.label} away."
    )
    world.say(
        f"{suspect.id} had borrowed it first, then kept it hidden, hoping the rhyme would blur the trail."
    )
    token.hidden = False
    _move_token(world, token, sentry.id)
    world.say(
        f"In the end, {sentry.id} took the {token.label} back, and {helper.id} stood beside {sentry.id} as the truth came clear."
    )


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    sentry = world.add(Entity(id=params.sentry, kind="character", type="sentry", label="sentry", traits=["watchful"]))
    suspect = world.add(Entity(id=params.suspect, kind="character", type="child", label="suspect", traits=["nervous"]))
    helper = world.add(Entity(id=params.helper, kind="character", type="child", label="helper", traits=["kind"]))
    token = world.add(copy.deepcopy(TOKENS[params.token]))
    rhyme = RHYMES[params.rhyme]

    token.owner = suspect.id
    token.hidden = True
    sentry.memes["duty"] = 1
    suspect.memes["shifty"] = 1
    helper.memes["watchful"] = 1

    world.say(
        f"At {place.label}, {sentry.id} kept watch while the wind tapped softly at the doors."
    )
    world.say(
        f"Near midnight, a small {token.label} went missing, and the whole place felt like a puzzle."
    )
    world.para()
    _investigate(world, sentry, suspect, helper, token, rhyme)
    world.para()
    _share_clue(world, helper, sentry, rhyme)
    _reveal(world, sentry, suspect, helper, token, rhyme)

    world.facts.update(
        sentry=sentry,
        suspect=suspect,
        helper=helper,
        token=token,
        rhyme=rhyme,
        place=place,
        resolved=not token.hidden,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a child where a sentry at {f["place"].label} follows a rhyme clue.',
        f"Tell a mystery story in which {f['sentry'].id} notices that {f['token'].label} is missing and {f['helper'].id} shares the meaning of a rhyme.",
        f'Write a gentle detective story using the word "sentry" and ending with the lost object being found.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    sentry = f["sentry"]
    suspect = f["suspect"]
    helper = f["helper"]
    token = f["token"]
    rhyme = f["rhyme"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was watching over {place.label} when the {token.label} went missing?",
            answer=f"{sentry.id} was the sentry keeping watch at {place.label}.",
        ),
        QAItem(
            question=f"What was the missing object in the mystery?",
            answer=f"The missing object was {token.phrase}.",
        ),
        QAItem(
            question=f"Why did the rhyme matter in the story?",
            answer=f"The rhyme mattered because it pointed toward the hidden clue and helped {sentry.id} understand where the {token.label} was kept.",
        ),
        QAItem(
            question=f"Who shared the useful clue with the sentry?",
            answer=f"{helper.id} shared what {helper.pronoun()} knew, which helped solve the mystery.",
        ),
        QAItem(
            question=f"Who had hidden the {token.label}?",
            answer=f"{suspect.id} had hidden it, hoping the shared rhyme would keep the truth buried.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a sentry do?",
            answer="A sentry watches a place carefully to help keep it safe.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a line or song where words sound alike at the end.",
        ),
        QAItem(
            question="Why do people share clues in a mystery?",
            answer="People share clues so they can solve a puzzle together and find out what really happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        if isinstance(e, Entity):
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
        elif isinstance(e, ObjectToken):
            lines.append(f"  {e.id:10} (token) owner={e.owner} hidden={e.hidden} shared={e.shared}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="museum", sentry="Ada", suspect="Milo", helper="June", token="key", rhyme="stone"),
    StoryParams(place="gatehouse", sentry="Nico", suspect="Tess", helper="Owen", token="pin", rhyme="bell"),
    StoryParams(place="dock", sentry="Mina", suspect="Theo", helper="Luna", token="map", rhyme="moth"),
]


ASP_RULES = r"""
#show valid/4.

valid(P,S,U,H) :- place(P), sentry(S), suspect(U), helper(H), different(S,U,H),
                  token(T), rhyme(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for nid in NAMES:
        lines.append(asp.fact("sentry", nid))
        lines.append(asp.fact("suspect", nid))
        lines.append(asp.fact("helper", nid))
    for tid in TOKENS:
        lines.append(asp.fact("token", tid))
    for rid in RHYMES:
        lines.append(asp.fact("rhyme", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for p in PLACES:
        for s in NAMES:
            for u in NAMES:
                for h in NAMES:
                    if len({s, u, h}) == 3:
                        combos.append((p, s, u, h))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl)[:10])
    if cl - py:
        print("  only in clingo:", sorted(cl - py)[:10])
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations.")
        for combo in combos[:50]:
            print(combo)
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
            header = f"### {p.sentry} at {p.place} with {p.token} and {p.rhyme}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
