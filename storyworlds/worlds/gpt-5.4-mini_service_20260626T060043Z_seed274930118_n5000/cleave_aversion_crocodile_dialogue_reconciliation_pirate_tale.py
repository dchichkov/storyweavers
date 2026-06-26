#!/usr/bin/env python3
"""
A standalone story world for a pirate tale with a crocodile, a split
cleaving problem, an aversion to danger, dialogue, and reconciliation.

The seed idea:
- A small pirate crew sails with a clever captain.
- A frightened deckhand has an aversion to the crocodile.
- A mishap cleaves a vital plank or crate rope.
- The crew must talk through the fear, repair the trouble, and reconcile.
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

PIRATE_NAMES = ["Mara", "Jory", "Nell", "Rook", "Tess", "Finn", "Bram", "Ada"]
CREW_ROLES = ["captain", "deckhand", "boatswain", "cook", "lookout"]
SHIP_PARTS = ["plank", "mast rope", "crate lid", "oar handle", "sail seam"]
TOOLS = ["hatchet", "knife", "cleaver", "saw", "chisel"]
PLACES = ["the dock", "the tide cave", "the moonlit cove", "the sandy shore", "the small harbor"]

ASP_RULES = r"""
% A tale is valid when the setting can host the crocodile encounter,
% the cleave makes something need repair, and the fear can be reconciled.
valid_story(S, P, T) :- setting(S), pirate(P), tool(T), place_ok(S), tool_ok(T).

% The crocodile is a danger worth fearing when it is near the crew.
danger(crocodile).

% Dialogue can soften aversion and lead to reconciliation.
reconciles(P) :- speaks(P), hears(P), danger(crocodile).

#show valid_story/3.
#show danger/1.
#show reconciles/1.
"""

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "deckhand", "boatswain", "cook", "lookout", "pirate"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the moonlit cove"
    has_crocodile: bool = True
    has_dialogue: bool = True
    has_reconciliation: bool = True


@dataclass
class StoryParams:
    place: str
    pirate_name: str
    pirate_role: str
    crocodile_name: str
    ship_part: str
    tool: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("setting", p))
        lines.append(asp.fact("place_ok", p))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
        lines.append(asp.fact("tool_ok", t))
    for n in PIRATE_NAMES:
        lines.append(asp.fact("pirate", n))
    lines.append(asp.fact("danger", "crocodile"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    if asp_valid_stories():
        print("OK: ASP rules produce valid story patterns.")
        return 0
    print("MISMATCH: ASP rules produced no stories.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale with crocodile, cleave, dialogue, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name", choices=PIRATE_NAMES)
    ap.add_argument("--role", choices=CREW_ROLES)
    ap.add_argument("--crocodile", default="Crookjaw")
    ap.add_argument("--part", choices=SHIP_PARTS)
    ap.add_argument("--tool", choices=TOOLS)
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
    place = args.place or rng.choice(PLACES)
    pirate_name = args.name or rng.choice(PIRATE_NAMES)
    pirate_role = args.role or rng.choice(CREW_ROLES)
    crocodile_name = args.crocodile or "Crookjaw"
    ship_part = args.part or rng.choice(SHIP_PARTS)
    tool = args.tool or rng.choice(TOOLS)
    return StoryParams(place=place, pirate_name=pirate_name, pirate_role=pirate_role,
                       crocodile_name=crocodile_name, ship_part=ship_part, tool=tool)


def generate(params: StoryParams) -> StorySample:
    world = World(Setting(place=params.place))
    captain = world.add(Entity(id="captain", kind="character", label="the captain", type="captain"))
    pirate = world.add(Entity(id=params.pirate_name, kind="character", label=params.pirate_name, type=params.pirate_role,
                              meters={"courage": 1.0}, memes={"aversion": 1.0}))
    croc = world.add(Entity(id="crocodile", kind="character", label=params.crocodile_name, type="crocodile",
                            meters={"splashes": 1.0}, memes={"mischief": 1.0}))
    broken = world.add(Entity(id="broken", kind="thing", label=params.ship_part, type=params.ship_part,
                              meters={"cleaved": 1.0}))
    tool = world.add(Entity(id=params.tool, kind="thing", label=params.tool, type="tool"))

    world.say(f"{params.pirate_name} served as the {params.pirate_role} aboard a small pirate boat by {params.place}.")
    world.say(f"{params.pirate_name} had a strong aversion to {params.crocodile_name}, the crocodile with sharp eyes and muddy teeth.")
    world.say(f"One rough swell sent the tool flying, and it cleaved the {params.ship_part} clean in two.")
    world.para()
    world.say(f'"Keep back from the edge," said the captain, "for the crocodile may be near."')
    world.say(f'"I know," said {params.pirate_name}, "but I do not like that great snout one bit."')
    world.say(f'"Aye," said the captain, "but fear can speak, and so can we."')
    world.say(f'The crew talked by lantern light, and the captain showed how to mend the {params.ship_part} with the {params.tool}.')
    world.para()
    world.say(f"{params.pirate_name} breathed slow, listened, and helped steady the boards.")
    world.say(f"The crocodile only bobbed in the water, blinking as the crew worked together.")
    world.say(f"By dusk, the {params.ship_part} was whole again, and {params.pirate_name} gave {params.crocodile_name} a careful nod instead of a frightened step back.")
    world.say(f"The captain smiled, because the little crew had chosen reconciliation over a hard quarrel, and the ship sailed on with the moon above.")

    world.facts.update(
        captain=captain, pirate=pirate, crocodile=croc, broken=broken, tool=tool,
        params=params, reconciled=True, aversion=True, cleaved=True
    )

    prompts = [
        f"Write a short pirate tale for a young child that includes a crocodile, a cleaved ship part, dialogue, and reconciliation.",
        f"Tell a gentle story where {params.pirate_name} fears {params.crocodile_name}, but the crew solves a problem together.",
        f"Make a simple pirate story in which a {params.pirate_role} helps mend a {params.ship_part} after a mishap.",
    ]

    story_qa = [
        QAItem(
            question=f"Why was {params.pirate_name} worried near {params.place}?",
            answer=f"{params.pirate_name} had an aversion to {params.crocodile_name}, the crocodile, so being near the water made {pirate.pronoun('object')} nervous.",
        ),
        QAItem(
            question=f"What got cleaved in the story?",
            answer=f"The {params.ship_part} got cleaved in two when the tool flew loose during the rough swell.",
        ),
        QAItem(
            question="How did the crew fix the trouble?",
            answer=f"They used the {params.tool} to mend the {params.ship_part}, and they talked kindly so everyone could work together.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"{params.pirate_name} was calmer, the {params.ship_part} was repaired, and the crew reached reconciliation instead of staying afraid or angry.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a crocodile?",
            answer="A crocodile is a large reptile that lives near water and has a long mouth full of sharp teeth.",
        ),
        QAItem(
            question="What does aversion mean?",
            answer="Aversion means a strong dislike or fear of something, like not wanting to go near a scary animal.",
        ),
        QAItem(
            question="What does cleave mean in this story?",
            answer="Here, cleave means to split something into two pieces.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people calm down, talk things through, and make peace after trouble.",
        ),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts,
                       story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for ent in sample.world.entities.values():
            print(f"{ent.id}: kind={ent.kind} type={ent.type} meters={ent.meters} memes={ent.memes}")
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(f"- {p}")
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story patterns:")
        for row in stories:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        all_params = [
            StoryParams(place=p, pirate_name=n, pirate_role=r, crocodile_name="Crookjaw", ship_part=s, tool=t)
            for p in PLACES[:3]
            for n in PIRATE_NAMES[:3]
            for r in CREW_ROLES[:2]
            for s in SHIP_PARTS[:2]
            for t in TOOLS[:2]
        ]
        samples = [generate(p) for p in all_params[: min(len(all_params), max(1, args.n))]]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
