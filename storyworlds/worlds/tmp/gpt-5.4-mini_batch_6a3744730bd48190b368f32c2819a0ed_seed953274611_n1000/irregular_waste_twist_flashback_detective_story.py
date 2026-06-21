#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/irregular_waste_twist_flashback_detective_story.py
==================================================================================

A standalone story world in a small detective domain.

Premise
-------
A child detective notices an irregular waste trail in a neighborhood, follows a
flashback to an earlier mishap, and discovers a harmless-looking twist: the
"waste" is not a crime at all, but scrap from a repair job that someone tried
to hide from view. The detective uses clues, memory, and a calm helper to solve
the misunderstanding and point everyone toward a better cleanup.

The story is built from simulated state:
- typed entities with physical meters and emotional memes
- a clue trail that can be irregular or neat
- a flashback that can raise certainty about the past
- a twist that changes the meaning of the waste
- a resolution that proves what changed

The words "irregular" and "waste" are included in the rendered story.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/irregular_waste_twist_flashback_detective_story.py
    python storyworlds/worlds/gpt-5.4-mini/irregular_waste_twist_flashback_detective_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/irregular_waste_twist_flashback_detective_story.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/irregular_waste_twist_flashback_detective_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
EVIDENCE_MIN = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    surfaces: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)


@dataclass
class ClueKind:
    id: str
    label: str
    phrase: str
    irregular: bool = False
    waste: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class FlashbackKind:
    id: str
    label: str
    cue: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TwistKind:
    id: str
    label: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperKind:
    id: str
    label: str
    job: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    clue: str
    flashback: str
    twist: str
    helper: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


PLACES = {
    "alley": Place(id="alley", label="the alley", indoors=False, surfaces=["brick", "pavement"], tags={"street"}),
    "bakery": Place(id="bakery", label="the bakery back room", indoors=True, surfaces=["tile", "wood"], tags={"shop"}),
    "dock": Place(id="dock", label="the dock", indoors=False, surfaces=["plank", "stone"], tags={"harbor"}),
}

CLUES = {
    "scrap": ClueKind(id="scrap", label="scrap paper", phrase="little scraps of paper", irregular=True, waste=False, tags={"paper"}),
    "trash": ClueKind(id="trash", label="waste", phrase="a trail of waste", irregular=True, waste=True, tags={"waste"}),
    "receipt": ClueKind(id="receipt", label="receipt bits", phrase="tiny receipt bits", irregular=False, waste=True, tags={"paper", "waste"}),
}

FLASHBACKS = {
    "repair": FlashbackKind(id="repair", label="flashback", cue="remembered a rainy afternoon", reveal="someone had torn open a box to fix a broken lock", tags={"memory"}),
    "delivery": FlashbackKind(id="delivery", label="flashback", cue="remembered the morning delivery", reveal="a bag had spilled when it snagged on the door", tags={"memory"}),
}

TWISTS = {
    "innocent": TwistKind(id="innocent", label="twist", reveal="the waste was not from a thief at all, but from a repair job", tags={"twist"}),
    "false_alarm": TwistKind(id="false_alarm", label="twist", reveal="the scattered bits only looked suspicious because the wind had spread them apart", tags={"twist"}),
}

HELPERS = {
    "janitor": HelperKind(id="janitor", label="the janitor", job="swept and sorted the mess", tags={"cleanup"}),
    "neighbor": HelperKind(id="neighbor", label="the neighbor", job="explained what had happened", tags={"witness"}),
}

GIRL_NAMES = ["Maya", "Iris", "Nina", "Lina", "Pia", "Zoe"]
BOY_NAMES = ["Evan", "Noah", "Owen", "Theo", "Milo", "Ari"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for c in CLUES:
            for t in TWISTS:
                if c == "trash" or CLUES[c].waste:
                    out.append((p, c, t))
    return out


def reasonableness_gate(place: Place, clue: ClueKind, flashback: FlashbackKind, twist: TwistKind) -> bool:
    return clue.waste or clue.irregular


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if c.irregular:
            lines.append(asp.fact("irregular", cid))
        if c.waste:
            lines.append(asp.fact("waste", cid))
    for fid in FLASHBACKS:
        lines.append(asp.fact("flashback", fid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, C, T) :- place(P), clue(C), twist(T), waste(C).
valid(P, C, T) :- place(P), clue(C), twist(T), irregular(C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world: irregular waste, flashback, twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--flashback", choices=FLASHBACKS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.clue is None or c[1] == args.clue)
        and (args.twist is None or c[2] == args.twist)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, twist = rng.choice(sorted(filtered))
    flashback = args.flashback or rng.choice(sorted(FLASHBACKS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    return StoryParams(
        place=place,
        clue=clue,
        flashback=flashback,
        twist=twist,
        helper=helper,
        detective_name=args.name or pick_name(rng, gender),
        detective_gender=gender,
        helper_name=args.helper_name or pick_name(rng, helper_gender),
        helper_gender=helper_gender,
    )


def flashback_open(world: World, detective: Entity, place: Place, clue: ClueKind) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f"{detective.id} was a little detective who noticed things other people missed. "
        f"That afternoon, {detective.pronoun()} spotted an {clue.label} trail in {place.label}."
    )
    world.say(
        f"The trail looked irregular, as if someone had dropped it while hurrying away."
    )


def follow_clues(world: World, detective: Entity, clue: ClueKind) -> None:
    detective.meters["evidence"] += 1
    world.say(
        f"{detective.id} crouched low and studied the clues. {clue.phrase} made a thin line across the floor."
    )


def _r_infer(world: World) -> list[str]:
    out = []
    det = world.get("detective")
    if det.meters["evidence"] >= EVIDENCE_MIN and world.get("memory").meters["shown"] >= THRESHOLD:
        sig = ("infer",)
        if sig not in world.fired:
            world.fired.add(sig)
            det.memes["certainty"] += 1
            out.append("__inference__")
    return out


def propagate(world: World) -> None:
    _r_infer(world)


def flashback_scene(world: World, fb: FlashbackKind, helper: Entity) -> None:
    helper.memes["calm"] += 1
    world.get("memory").meters["shown"] += 1
    world.say(
        f"Then came a flashback: {fb.cue}. In the memory, {fb.reveal}."
    )


def twist_scene(world: World, twist: TwistKind, helper: Entity, clue: ClueKind) -> None:
    world.say(
        f"The case turned on a twist. {twist.reveal}, and that made the odd trail make sense."
    )
    if clue.waste:
        world.say(
            f"What looked like useless waste was really safe leftover paper and packing."
        )


def cleanup_end(world: World, helper: Entity) -> None:
    helper.meters["cleanup"] += 1
    world.say(
        f"{helper.id} arrived and {HELPERS[world.facts['helper']].job}. "
        f"Together they gathered the stray bits into one neat pile."
    )
    world.say(
        f"By the end, the floor was tidy again, and the irregular trail had become a solved clue instead of a mystery."
    )


def tell(params: StoryParams) -> World:
    world = World()
    place = world.add(Entity(id="place", type="place", label=PLACES[params.place].label, attrs={"place_id": params.place}))
    detective = world.add(Entity(id=params.detective_name, kind="character", type=params.detective_gender, role="detective"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper"))
    memory = world.add(Entity(id="memory", kind="thing", type="memory", label="memory"))
    clue = CLUES[params.clue]
    flashback = FLASHBACKS[params.flashback]
    twist = TWISTS[params.twist]
    helper_kind = HELPERS[params.helper]
    detective.memes["curiosity"] = 1.0
    flashback_open(world, detective, PLACES[params.place], clue)
    world.para()
    follow_clues(world, detective, clue)
    flashback_scene(world, flashback, helper)
    world.para()
    twist_scene(world, twist, helper, clue)
    propagate(world)
    world.para()
    cleanup_end(world, helper)
    detective.memes["relief"] += 1
    detective.memes["pride"] += 1
    world.facts.update(
        place=PLACES[params.place],
        clue=clue,
        flashback=flashback,
        twist=twist,
        helper=helper_kind,
        detective=detective,
        memory=memory,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a detective story for a young child that includes the word '{f['clue'].label}' and the word 'irregular'.",
        f"Tell a mystery story where {f['detective'].id} follows a strange clue in {f['place'].label}, remembers a flashback, and learns a twist.",
        f"Write a short detective story where what looked like waste turns out to mean something else.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"]
    helper = f["helper"]
    clue = f["clue"]
    flashback = f["flashback"]
    twist = f["twist"]
    qa = [
        QAItem(
            question="What kind of story is this?",
            answer="It is a detective story about following clues, remembering the past, and solving a small mystery."
        ),
        QAItem(
            question=f"What did {det.id} notice?",
            answer=f"{det.id} noticed an irregular trail of {clue.label_word} in the case's setting. That was the first clue that something important had been left behind."
        ),
        QAItem(
            question="What did the flashback show?",
            answer=f"The flashback showed a moment when {flashback.reveal}. It helped the detective understand that the trail came from an earlier accident, not a crime."
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {twist.reveal}. That changed the meaning of the waste and made the mystery harmless."
        ),
        QAItem(
            question=f"How did {helper.id} help?",
            answer=f"{helper.id} helped by staying calm and explaining what had happened. That let the detective gather the clues and finish the cleanup."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a piece of information that helps solve a mystery."
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a scene that goes back to an earlier time so the story can show what happened before."
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise turn that changes how you understand the problem."
        ),
        QAItem(
            question="Why can waste be a clue in a mystery?",
            answer="Waste can be a clue because what was thrown away or left behind may show who was there and what they were doing."
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="alley", clue="trash", flashback="repair", twist="innocent", helper="neighbor", detective_name="Maya", detective_gender="girl", helper_name="Owen", helper_gender="boy"),
    StoryParams(place="bakery", clue="scrap", flashback="delivery", twist="false_alarm", helper="janitor", detective_name="Evan", detective_gender="boy", helper_name="Lina", helper_gender="girl"),
]


def explain_rejection() -> str:
    return "(No story: this combination does not build a believable mystery.)"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: ASP and Python disagree.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        print("OK: normal story generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.clue not in CLUES or params.flashback not in FLASHBACKS or params.twist not in TWISTS or params.helper not in HELPERS:
        raise StoryError("(Invalid parameters.)")
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            i += 1
            p = resolve_params(args, random.Random((args.seed or 0) + i))
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
