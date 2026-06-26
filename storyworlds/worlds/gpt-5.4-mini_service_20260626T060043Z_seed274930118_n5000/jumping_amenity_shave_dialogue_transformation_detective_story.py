#!/usr/bin/env python3
"""
A tiny detective-story world about a missing amenity, a jump, and a shave
transformation.

Premise:
- A young detective is called to a small inn when a guest's special amenity
  disappears.
- A clue trail leads over a little gate the detective must jump.
- The suspect changes appearance with a shave, but the detective notices the
  voice and the footprint of the plan.

Story shape:
- Setup: introduce detective, guest, amenity, and the odd complaint.
- Middle: dialogue, clue-hunting, a jump over a barrier, and a transformation.
- Ending: the truth is revealed and the amenity returns.

The world model tracks:
- Physical meters: movement, closeness, disguise, missingness, recovered.
- Emotional memes: worry, confidence, surprise, relief.
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
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "detective"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the little inn"
    barrier: str = "the low gate"


@dataclass
class Amenity:
    id: str
    label: str
    phrase: str
    place_hint: str
    missing_reason: str
    recovered_by: str


@dataclass
class StoryParams:
    amenity: str
    detective_name: str
    guest_name: str
    suspect_name: str
    seed: Optional[int] = None


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


def _narrate(world: World, speaker: Entity, text: str) -> None:
    world.say(f'"{text}" {speaker.id} said.')


def _do_jump(world: World, actor: Entity) -> None:
    actor.meters["jumping"] = actor.meters.get("jumping", 0.0) + 1.0
    actor.meters["closer"] = actor.meters.get("closer", 0.0) + 1.0
    world.say(f"{actor.id} took a careful jump over {world.setting.barrier}.")


def _do_shave(world: World, actor: Entity) -> None:
    actor.meters["shaved"] = actor.meters.get("shaved", 0.0) + 1.0
    actor.meters["disguise"] = actor.meters.get("disguise", 0.0) + 1.0
    actor.memes["nervous"] = actor.memes.get("nervous", 0.0) + 1.0
    world.say(f"{actor.id} gave himself a quick shave and tried to look different.")


def _reveal(world: World, detective: Entity, suspect: Entity, amenity: Entity) -> None:
    if ("reveal", suspect.id) in world.fired:
        return
    world.fired.add(("reveal", suspect.id))
    detective.memes["confidence"] = detective.memes.get("confidence", 0.0) + 1.0
    suspect.memes["surprised"] = suspect.memes.get("surprised", 0.0) + 1.0
    amenity.meters["recovered"] = 1.0
    world.say(
        f"{detective.id} smiled. {detective.pronoun().capitalize()} had heard the voice "
        f"and noticed the tidy chin. The disguise was only a shave."
    )
    world.say(
        f"{suspect.id} hung his head and returned {amenity.label} at once."
    )


def tell(amenity_cfg: Amenity, detective_name: str, guest_name: str, suspect_name: str) -> World:
    world = World(Setting())
    detective = world.add(Entity(
        id=detective_name, kind="character", type="detective",
        meters={"jumping": 0.0, "closer": 0.0}, memes={"confidence": 0.0},
    ))
    guest = world.add(Entity(
        id=guest_name, kind="character", type="girl",
        meters={"worry": 1.0}, memes={"worry": 1.0},
    ))
    suspect = world.add(Entity(
        id=suspect_name, kind="character", type="man",
        meters={"disguise": 0.0, "shaved": 0.0}, memes={"nervous": 0.0},
    ))
    amenity = world.add(Entity(
        id=amenity_cfg.id, type="thing", label=amenity_cfg.label,
        phrase=amenity_cfg.phrase, owner=guest.id, meters={"missing": 1.0},
        tags={amenity_cfg.id, "amenity"},
    ))

    world.say(
        f"It was a calm evening at {world.setting.place}, when {guest.id} came to {detective.id} in a whisper."
    )
    _narrate(world, guest, f"My {amenity.label} is gone, and I need it for the night.")
    world.say(
        f"{detective.id} looked at the little lobby, where {world.setting.barrier} stood like a line in a puzzle."
    )
    world.say(
        f"'{amenity_cfg.missing_reason}?' {detective.id} asked. '{amenity_cfg.recovered_by} might matter here.'"
    )

    world.para()
    _narrate(world, suspect, "I only came in for a minute.")
    _narrate(world, detective, "A minute can still hide a clue.")
    _do_jump(world, detective)
    world.say(
        f"On the other side of {world.setting.barrier}, {detective.id} found a wet footprint and a small razor."
    )
    _do_shave(world, suspect)
    world.say(
        f"{guest.id} stared. 'That sounded like you,' she said."
    )
    world.say(
        f"'{detective.id} answered, 'A shave can change a face, but not a habit.'"
    )
    _reveal(world, detective, suspect, amenity)

    world.para()
    world.say(
        f"By the end of the night, {amenity.label} was back where it belonged, and {guest.id} could smile again."
    )
    world.say(
        f"{detective.id} stepped away from {world.setting.barrier}, feeling proud of the jump, the clue, and the truth."
    )

    world.facts.update(
        detective=detective,
        guest=guest,
        suspect=suspect,
        amenity=amenity,
        amenity_cfg=amenity_cfg,
    )
    return world


SETTINGS = {
    "inn": Setting(place="the little inn", barrier="the low gate"),
}

AMENITIES = {
    "soap": Amenity(
        id="soap",
        label="soap",
        phrase="a smooth bar of soap",
        place_hint="washroom",
        missing_reason="Why would soap vanish from the washroom",
        recovered_by="It was hidden near the sink",
    ),
    "comb": Amenity(
        id="comb",
        label="comb",
        phrase="a bright blue comb",
        place_hint="desk",
        missing_reason="Who would take a comb from the front desk",
        recovered_by="It was tucked behind the sign",
    ),
    "towel": Amenity(
        id="towel",
        label="towel",
        phrase="a soft white towel",
        place_hint="laundry basket",
        missing_reason="How did a towel leave the laundry basket",
        recovered_by="It was folded behind the curtain",
    ),
}

DETECTIVE_NAMES = ["Nina", "Milo", "Tess", "Arlo", "June"]
GUEST_NAMES = ["Mina", "Lina", "Owen", "Pia", "Evan"]
SUSPECT_NAMES = ["Bram", "Noel", "Rudy", "Cleo", "Finn"]


def valid_combos() -> list[tuple[str, str]]:
    return [("inn", aid) for aid in AMENITIES]


@dataclass
class ASPConfig:
    pass


ASP_RULES = r"""
amenity(soap).
amenity(comb).
amenity(towel).

valid(place, amenity) :- place(inn), amenity(amenity).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "inn")]
    for aid in AMENITIES:
        lines.append(asp.fact("amenity", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with a jump, an amenity, and a shave.")
    ap.add_argument("--amenity", choices=AMENITIES)
    ap.add_argument("--detective-name", choices=DETECTIVE_NAMES)
    ap.add_argument("--guest-name", choices=GUEST_NAMES)
    ap.add_argument("--suspect-name", choices=SUSPECT_NAMES)
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
    amenity = args.amenity or rng.choice(list(AMENITIES))
    detective_name = args.detective_name or rng.choice(DETECTIVE_NAMES)
    guest_name = args.guest_name or rng.choice(GUEST_NAMES)
    suspect_name = args.suspect_name or rng.choice(SUSPECT_NAMES)
    if len({detective_name, guest_name, suspect_name}) < 3:
        raise StoryError("Choose different names for the detective, guest, and suspect.")
    return StoryParams(
        amenity=amenity,
        detective_name=detective_name,
        guest_name=guest_name,
        suspect_name=suspect_name,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a child about a missing {f["amenity_cfg"].label} and a clue that requires a jump.',
        f"Tell a dialogue-heavy mystery where {f['detective'].id} notices a shave transformation and solves the case.",
        f"Create a gentle detective tale set at {world.setting.place} with an amenity, a jump, and a hidden truth.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"]
    guest = f["guest"]
    suspect = f["suspect"]
    amenity = f["amenity_cfg"]
    return [
        QAItem(
            question=f"What was missing from {world.setting.place}?",
            answer=f"{guest.id}'s {amenity.label} was missing.",
        ),
        QAItem(
            question=f"What did {det.id} do to find the clue?",
            answer=f"{det.id} took a careful jump over {world.setting.barrier} and found a footprint and a razor.",
        ),
        QAItem(
            question=f"How did {suspect.id} try to look different?",
            answer=f"{suspect.id} gave himself a quick shave and tried to hide his face, but the detective still recognized the truth.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"The missing {amenity.label} was returned, and {guest.id} felt happy again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective for?",
            answer="A detective looks for clues, asks careful questions, and helps solve a mystery.",
        ),
        QAItem(
            question="What does shaving do?",
            answer="Shaving cuts hair off the face, which can change how someone looks.",
        ),
        QAItem(
            question="Why can jumping help in a mystery?",
            answer="Jumping can help someone get over a barrier or reach a clue that is in a hard place.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(f"- {p}" for p in sample.prompts)
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(AMENITIES[params.amenity], params.detective_name, params.guest_name, params.suspect_name)
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


def valid_story_params() -> list[StoryParams]:
    out = []
    for _, amenity in valid_combos():
        out.append(StoryParams(
            amenity=amenity,
            detective_name=DETECTIVE_NAMES[0],
            guest_name=GUEST_NAMES[0],
            suspect_name=SUSPECT_NAMES[0],
        ))
    return out


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid/2.")
    model = asp.one_model(program)
    clingo_set = set(asp.atoms(model, "valid"))
    py_set = set(valid_combos())
    if clingo_set != py_set:
        print("MISMATCH between ASP and Python.")
        print("ASP only:", sorted(clingo_set - py_set))
        print("Python only:", sorted(py_set - clingo_set))
        return 1
    print(f"OK: ASP matches Python ({len(py_set)} combos).")
    return 0


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for place, amenity in combos:
            print(f"  {place} {amenity}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, amenity in enumerate(AMENITIES):
            params = StoryParams(
                amenity=amenity,
                detective_name=DETECTIVE_NAMES[i % len(DETECTIVE_NAMES)],
                guest_name=GUEST_NAMES[i % len(GUEST_NAMES)],
                suspect_name=SUSPECT_NAMES[i % len(SUSPECT_NAMES)],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
