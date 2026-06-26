#!/usr/bin/env python3
"""
storyworlds/worlds/percussion_lentil_fox_inner_monologue_myth.py
===============================================================

A small mythic story world about a fox, a lentil offering, and sacred
percussion. The central tension comes from a choice between hunger, music,
and respect. The prose includes inner monologue, so the fox's thoughts can
carry the turning point.

World premise:
- A fox is sent to bring a bowl of lentils to a hill shrine.
- The shrine also keeps a drum used for calling the dawn.
- If the fox plays too loudly or too greedily, the lentils may spill or the
  ritual may be spoiled.
- A wise compromise lets the fox use a smaller instrument and keep the offering
  intact.

The simulated state tracks:
- physical meters: hunger, dust, spill, sound, warmth
- emotional memes: awe, worry, pride, restraint, relief

The ASP twin mirrors the reasonableness gate:
- a valid story requires a place, an instrument, and an offering that are
  genuinely in tension
- a valid fix must protect the at-risk offering while still fitting the mythic
  scene
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"hunger": 0.0, "dust": 0.0, "spill": 0.0, "sound": 0.0, "warmth": 0.0}
        if not self.memes:
            self.memes = {"awe": 0.0, "worry": 0.0, "pride": 0.0, "restraint": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "fox":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Shrine:
    place: str = "the hill shrine"
    affords: set[str] = field(default_factory=lambda: {"percussion", "small_percussion"})
    holy: bool = True


@dataclass
class Instrument:
    id: str
    label: str
    size: str  # "big" or "small"
    sound: str
    at_risk: bool = False
    protects_offering: bool = False


@dataclass
class Offering:
    label: str
    phrase: str
    vessel: str
    region: str = "hands"


class World:
    def __init__(self, shrine: Shrine) -> None:
        self.shrine = shrine
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        c = World(self.shrine)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class StoryParams:
    place: str
    instrument: str
    offering: str
    name: str
    seed: Optional[int] = None


SETTINGS = {
    "hill": Shrine(place="the hill shrine", affords={"percussion", "small_percussion"}),
    "grove": Shrine(place="the drum grove", affords={"percussion", "small_percussion"}),
}

INSTRUMENTS = {
    "drum": Instrument(id="drum", label="great drum", size="big", sound="booming", at_risk=True),
    "frame_drum": Instrument(id="frame_drum", label="frame drum", size="small", sound="bright", protects_offering=False),
    "rattle": Instrument(id="rattle", label="seed rattle", size="small", sound="soft", protects_offering=True),
}

OFFERINGS = {
    "lentils": Offering(label="lentils", phrase="a bowl of lentils", vessel="wooden bowl"),
    "spiced_lentils": Offering(label="lentils", phrase="a warm bowl of spiced lentils", vessel="clay bowl"),
}

NAMES = ["Ash", "Koa", "Mira", "Suri", "Tavi", "Niko"]


def valid_combo(place: str, instrument: str, offering: str) -> bool:
    inst = INSTRUMENTS[instrument]
    off = OFFERINGS[offering]
    if place not in SETTINGS:
        return False
    # Big drum is only reasonable when lentils are at risk of being disturbed.
    if inst.size == "big" and off.label == "lentils":
        return True
    # Small instrument is a valid gentler path.
    if inst.size == "small" and off.label == "lentils":
        return True
    return False


def select_compromise(inst: Instrument, offering: Offering) -> Optional[Instrument]:
    if inst.size == "small":
        return inst
    return INSTRUMENTS["rattle"]


def predict_spill(world: World, actor: Entity, inst: Instrument, offering: Offering) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["sound"] += 1.0 if inst.size == "big" else 0.3
    if inst.size == "big":
        sim.get("offering").meters["spill"] += 1.0
    return {"spilled": sim.get("offering").meters["spill"] >= THRESHOLD}


def tell(shrine: Shrine, instrument: Instrument, offering: Offering, name: str) -> World:
    world = World(shrine)
    fox = world.add(Entity(id=name, kind="character", type="fox"))
    drum = world.add(Entity(id=instrument.id, type="instrument", label=instrument.label))
    bowl = world.add(Entity(id="offering", type="offering", label=offering.label, phrase=offering.phrase, caretaker=name))
    world.facts.update(fox=fox, drum=drum, bowl=bowl, instrument=instrument, offering=offering, shrine=shrine)

    fox.meters["hunger"] += 1.0
    fox.memes["awe"] += 1.0
    world.say(f"In old tales, {fox.id} came to {shrine.place} with {offering.phrase}.")
    world.say(f"{fox.pronoun().capitalize()} had been asked to carry it carefully, for the shrine was listening.")

    world.para()
    world.say(f"{fox.id} looked at the {instrument.label} and felt the hum of the day in {fox.pronoun('possessive')} chest.")
    world.say(f'"If I beat it too hard," {fox.id} thought, "the bowl may tremble, and the lentils may scatter."')
    world.say(f'Yet another thought came: "If I do not play, the dawn may stay asleep."')

    world.para()
    world.say(f"{fox.id} lifted the {instrument.label} and tested its voice.")
    fox.meters["sound"] += 1.0 if instrument.size == "big" else 0.3
    if instrument.size == "big":
        fox.memes["worry"] += 1.0
    else:
        fox.memes["restraint"] += 1.0

    if predict_spill(world, fox, instrument, offering)["spilled"]:
        fox.memes["worry"] += 1.0
        world.say(f"The first great beat shivered through the air, and {fox.id} knew the bowl could not survive that storm.")
        world.say(f'"Not this way," {fox.id} thought. "A shrine is not impressed by recklessness."')
        alt = select_compromise(instrument, offering)
        if alt is None:
            raise StoryError("No reasonable compromise exists for this instrument and offering.")
        if alt.id != instrument.id:
            world.say(f"So {fox.id} set down the {instrument.label} and picked up the {alt.label} instead.")
        fox.memes["restraint"] += 1.0
        fox.meters["sound"] += 0.3
        bowl.meters["spill"] = 0.0
        world.para()
        world.say(f"{fox.id} played the {alt.label} in a gentle pattern, like rain tapping leaves.")
        world.say(f"The lentils stayed still, and the shrine answered with a warm hush.")
        fox.memes["relief"] += 1.0
        fox.memes["pride"] += 1.0
        world.say(f"{fox.id} thought, 'A small sound can still be holy.'")
        world.say(f"Then {fox.id} left the shrine with {offering.phrase} intact and {fox.pronoun('possessive')} heart full.")
    else:
        fox.memes["pride"] += 1.0
        fox.memes["relief"] += 1.0
        world.say(f"The {instrument.label} spoke, but softly enough that the bowl did not stir.")
        world.say(f"{fox.id} thought, 'I can serve both the drum and the lentils.'")
        world.say(f"At dawn, {shrine.place} shimmered, and {fox.id} carried the offering home unspilled.")

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    fox = f["fox"]
    inst = f["instrument"]
    off = f["offering"]
    return [
        f'Write a myth-like story about {fox.id}, a fox, who must carry {off.phrase} and decide whether to use the {inst.label}.',
        f"Tell a short story with inner monologue where a fox thinks about a {inst.label}, a bowl of lentils, and a sacred shrine.",
        f'Write a gentle myth for children about percussion, lentils, and a fox learning restraint.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    fox = f["fox"]
    inst = f["instrument"]
    off = f["offering"]
    shrine = f["shrine"]
    return [
        QAItem(
            question=f"Who carried {off.phrase} to {shrine.place}?",
            answer=f"A fox named {fox.id} carried {off.phrase} to {shrine.place}.",
        ),
        QAItem(
            question=f"What did {fox.id} worry would happen if {fox.pronoun('subject')} hit the {inst.label} too hard?",
            answer=f"{fox.id} thought the bowl might tremble and the lentils might scatter.",
        ),
        QAItem(
            question=f"What choice helped {fox.id} finish the journey with the offering safe?",
            answer=(
                f"{fox.id} chose a gentler kind of percussion, so the offering stayed safe "
                f"and the shrine could still hear music."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are lentils?",
            answer="Lentils are small edible seeds that people cook in soups and bowls.",
        ),
        QAItem(
            question="What is percussion?",
            answer="Percussion is music made by striking, shaking, or tapping instruments like drums and rattles.",
        ),
        QAItem(
            question="Why can a fox be a clever character in a story?",
            answer="A fox is often used in stories as a clever animal because it seems quick to notice things and solve problems.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        out.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(out)


ASP_RULES = r"""
place(hill). place(grove).
instrument(drum). instrument(frame_drum). instrument(rattle).
offering(lentils). offering(spiced_lentils).

percussion(drum). percussion(frame_drum). percussion(rattle).
big(drum). small(frame_drum). small(rattle).

at_risk(drum, lentils).
at_risk(drum, spiced_lentils).
gentle_fix(frame_drum, lentils).
gentle_fix(rattle, lentils).
gentle_fix(rattle, spiced_lentils).

valid(Place, Instrument, Offering) :- place(Place), instrument(Instrument), offering(Offering),
    percussion(Instrument), at_risk(Instrument, Offering).

valid_story(Place, Instrument, Offering) :- valid(Place, Instrument, Offering).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for iid, inst in INSTRUMENTS.items():
        lines.append(asp.fact("instrument", iid))
        if inst.size == "big":
            lines.append(asp.fact("big", iid))
        else:
            lines.append(asp.fact("small", iid))
        lines.append(asp.fact("percussion", iid))
    for oid in OFFERINGS:
        lines.append(asp.fact("offering", oid))
    for iid, inst in INSTRUMENTS.items():
        for oid in OFFERINGS:
            if inst.size == "big":
                lines.append(asp.fact("at_risk", iid, oid))
            if inst.size == "small":
                lines.append(asp.fact("gentle_fix", iid, oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in SETTINGS:
        for i in INSTRUMENTS:
            for o in OFFERINGS:
                if valid_combo(p, i, o):
                    out.append((p, i, o))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic fox, lentils, and percussion with inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.instrument is None or c[1] == args.instrument)
              and (args.offering is None or c[2] == args.offering)]
    if not combos:
        raise StoryError("No valid story matches those choices.")
    place, instrument, offering = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, instrument=instrument, offering=offering, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], INSTRUMENTS[params.instrument], OFFERINGS[params.offering], params.name)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in [StoryParams(place=p, instrument=i, offering=o, name="Ash") for (p, i, o) in valid_combos()]:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
