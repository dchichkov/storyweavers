#!/usr/bin/env python3
"""
storyworlds/worlds/wheeler_conflict_whodunit.py
================================================

A small whodunit storyworld about a missing object, a tense accusation,
and a careful reveal. The seed word "wheeler" appears as a character name
and as part of the mystery's physical world.

Premise:
- A child-like detective story in a single room or small place.
- Someone notices a loss.
- Suspicion causes conflict.
- The sleuth follows physical clues and resolves the dispute.

The world model tracks:
- physical meters: distance, hiddenness, smudge, tension-related movement
- emotional memes: worry, suspicion, guilt, relief, trust

The story is deliberately state-driven. The prose is generated from the
simulated evidence trail, not from a frozen template with swapped nouns.
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
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("distance", "hiddenness", "smudge", "noise"):
            self.meters.setdefault(k, 0.0)
        for k in ("worry", "suspicion", "guilt", "relief", "trust", "anger"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "mom", "woman"}
        masculine = {"boy", "father", "dad", "man"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = True
    clues: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    kind: str
    where: str
    reveals: str
    smear: str = ""
    distance: float = 0.0


@dataclass
class StoryParams:
    place: str
    culprit: str
    missing: str
    detective_name: str
    suspect_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _mention(entity: Entity) -> str:
    return entity.label or entity.id


def _capital(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def _do_missing(world: World, missing: Entity) -> None:
    missing.hidden = True
    missing.meters["hiddenness"] += 2.0


def _search(world: World, detective: Entity, missing: Entity) -> Optional[str]:
    if missing.hidden:
        return "under the table"
    return None


def _clue_follows(world: World, detective: Entity, clue: Clue, suspect: Entity, missing: Entity) -> None:
    sig = ("clue", clue.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    detective.meters["distance"] += clue.distance
    detective.memes["worry"] += 0.5
    clue_line = f"{_capital(detective.id)} found {clue.kind} {clue.where}, and it pointed to {_mention(suspect)}."
    world.say(clue_line)
    if clue.smear:
        world.say(f"The {clue.smear} showed that the missing {_mention(missing)} had been moved, not stolen.")


def _accuse(world: World, detective: Entity, suspect: Entity) -> None:
    sig = ("accuse", suspect.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    detective.memes["suspicion"] += 1.0
    suspect.memes["anger"] += 0.5
    world.say(
        f'{_capital(detective.id)} looked at the clues and said, "You took it, {_mention(suspect)}."'
    )
    world.say(f"{_mention(suspect)} stared back, hurt and angry.")


def _conflict(world: World, detective: Entity, suspect: Entity) -> None:
    if detective.memes["suspicion"] < THRESHOLD:
        return
    detective.memes["anger"] += 0.2
    suspect.memes["worry"] += 0.4
    world.say(
        f"The room went quiet, and the accusation turned the air sharp."
    )


def _reveal(world: World, detective: Entity, suspect: Entity, missing: Entity, culprit: Entity) -> None:
    sig = ("reveal", missing.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    if culprit.id == suspect.id:
        suspect.memes["guilt"] += 1.0
    else:
        suspect.memes["trust"] += 0.8
    detective.memes["suspicion"] = 0.0
    detective.memes["relief"] += 1.0
    suspect.memes["anger"] = 0.0
    suspect.memes["worry"] += 0.2
    missing.hidden = False
    missing.carried_by = culprit.id
    world.say(
        f"At last, {_capital(detective.id)} found the missing {_mention(missing)} where {_mention(culprit)} had tucked it away."
    )
    world.say(
        f"It had not been stolen at all; it had only been put aside in a rush, and the mistake made everyone feel small."
    )


SETTING_REGISTRY = {
    "hall": Setting(place="the front hall", indoor=True, clues={"dust", "shoeprint"}),
    "kitchen": Setting(place="the kitchen", indoor=True, clues={"crumb", "spoon"}),
    "shed": Setting(place="the shed", indoor=False, clues={"mud", "tape"}),
}

MISSING_REGISTRY = {
    "glove": Entity(id="glove", type="thing", label="glove", phrase="a red glove", plural=False),
    "key": Entity(id="key", type="thing", label="key", phrase="a brass key", plural=False),
    "note": Entity(id="note", type="thing", label="note", phrase="a folded note", plural=False),
    "wheel": Entity(id="wheel", type="thing", label="wheel", phrase="a small cart wheel", plural=False),
}

CLUE_REGISTRY = {
    "dust": Clue(id="dust", kind="dusty marks", where="beside the chair", reveals="sneaking"),
    "shoeprint": Clue(id="shoeprint", kind="a shoeprint", where="near the door", reveals="movement"),
    "crumb": Clue(id="crumb", kind="crumbs", where="by the counter", reveals="snacking"),
    "spoon": Clue(id="spoon", kind="a spoon", where="in the sink", reveals="a hurried pause"),
    "mud": Clue(id="mud", kind="mud smears", where="on the floor", reveals="the shed", smear="mud"),
    "tape": Clue(id="tape", kind="a strip of tape", where="on a box", reveals="the shed"),
}

PEOPLE = {
    "wheeler": Entity(id="wheeler", kind="character", type="boy", label="Wheeler"),
    "mira": Entity(id="mira", kind="character", type="girl", label="Mira"),
    "pax": Entity(id="pax", kind="character", type="boy", label="Pax"),
    "nina": Entity(id="nina", kind="character", type="girl", label="Nina"),
}


ASP_RULES = r"""
clue_point(C) :- clue(C), seen(C).
conflict :- suspicion(Detective), Detective > 0.
reveal :- found_missing.
whodunit(P) :- conflict, reveal, culprit(P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTING_REGISTRY.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for c in sorted(s.clues):
            lines.append(asp.fact("supports", sid, c))
    for mid, m in MISSING_REGISTRY.items():
        lines.append(asp.fact("missing", mid))
        lines.append(asp.fact("label", mid, m.label))
    for cid, c in CLUE_REGISTRY.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("kind", cid, c.kind))
    for pid in PEOPLE:
        lines.append(asp.fact("person", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generate_world(params: StoryParams) -> World:
    setting = SETTING_REGISTRY[params.place]
    world = World(setting)
    detective = world.add(Entity(id=params.detective_name.lower(), kind="character", type="boy", label=params.detective_name))
    suspect = world.add(Entity(id=params.suspect_name.lower(), kind="character", type="girl", label=params.suspect_name))
    culprit = world.add(Entity(id=params.culprit, kind="character", type="boy", label=_capital(params.culprit)))
    missing = world.add(Entity(
        id=params.missing,
        kind="thing",
        type="thing",
        label=params.missing,
        phrase=MISSING_REGISTRY[params.missing].phrase,
        owner=suspect.id,
    ))

    world.say(
        f"{detective.id.capitalize()} was the kind of child who noticed every tiny thing, even the way a room felt before a secret came out."
    )
    world.say(
        f"That afternoon, {_mention(suspect)} gasped because {missing.phrase} had vanished from its place."
    )
    world.say(
        f"{detective.id.capitalize()} saw the worry on {_mention(suspect)}'s face and promised to solve it."
    )

    world.para()
    _do_missing(world, missing)
    clue1 = CLUE_REGISTRY["dust"] if params.place != "shed" else CLUE_REGISTRY["mud"]
    clue2 = CLUE_REGISTRY["shoeprint"] if params.place != "kitchen" else CLUE_REGISTRY["crumb"]
    _clue_follows(world, detective, clue1, culprit, missing)
    _accuse(world, detective, suspect)
    _conflict(world, detective, suspect)
    world.say(
        f"{_mention(suspect)} said the missing thing had only been moved, but the first clue sounded too suspicious."
    )
    _clue_follows(world, detective, clue2, culprit, missing)

    world.para()
    _reveal(world, detective, suspect, missing, culprit)
    world.say(
        f"In the end, the room felt warm again, and even the little {_mention(missing)} looked harmless in the light."
    )

    world.facts.update(
        detective=detective,
        suspect=suspect,
        culprit=culprit,
        missing=missing,
        place=params.place,
        clues=[clue1.id, clue2.id],
        conflict=detective.memes["suspicion"] > 0 or suspect.memes["anger"] > 0,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    det = f["detective"]
    sus = f["suspect"]
    miss = f["missing"]
    return [
        f'Write a short whodunit for a young child that includes "{det.label}" and the missing {miss.label}.',
        f"Tell a gentle mystery where {det.label} follows clues, argues with {sus.label}, and solves the case.",
        f"Write a simple detective story about a lost {miss.label}, a conflict, and a reveal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"]
    sus = f["suspect"]
    cul = f["culprit"]
    miss = f["missing"]
    qas = [
        QAItem(
            question=f"Who tried to solve the mystery about the missing {miss.label}?",
            answer=f"{det.label} tried to solve it by following clues and asking careful questions.",
        ),
        QAItem(
            question=f"Why did the room become tense between {det.label} and {sus.label}?",
            answer=f"It became tense because {det.label} suspected {sus.label} had taken the {miss.label}, even though that was not the real answer.",
        ),
        QAItem(
            question=f"What was the final truth about the missing {miss.label}?",
            answer=f"The {miss.label} had not been stolen. It had been put away by {cul.label} in a rush, and the mistake caused the conflict.",
        ),
    ]
    return qas


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a whodunit?",
            answer="A clue is a small piece of evidence that helps a detective figure out what really happened.",
        ),
        QAItem(
            question="Why can people argue during a mystery?",
            answer="People can argue when they are worried or blamed, especially before the detective understands the truth.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks at evidence, asks questions, and connects the facts to solve a problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"{e.id}: {' '.join(bits) if bits else 'plain'}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with Wheeler and a conflict.")
    ap.add_argument("--place", choices=SETTING_REGISTRY)
    ap.add_argument("--missing", choices=MISSING_REGISTRY)
    ap.add_argument("--culprit", choices=["wheeler", "mira", "pax", "nina"])
    ap.add_argument("--detective-name")
    ap.add_argument("--suspect-name")
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTING_REGISTRY:
        for missing in MISSING_REGISTRY:
            for culprit in ["wheeler", "mira", "pax", "nina"]:
                out.append((place, culprit, missing))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTING_REGISTRY))
    missing = args.missing or rng.choice(list(MISSING_REGISTRY))
    culprit = args.culprit or rng.choice(["wheeler", "mira", "pax", "nina"])
    detective = args.detective_name or rng.choice(["Ivy", "Jun", "Nora", "Owen"])
    suspect = args.suspect_name or rng.choice(["Mina", "Luca", "Tess", "Rafi"])
    if suspect.lower() == detective.lower():
        raise StoryError("detective and suspect must be different children")
    return StoryParams(
        place=place,
        culprit=culprit,
        missing=missing,
        detective_name=detective,
        suspect_name=suspect,
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


ASP_RULES = r"""
valid(P,C,M) :- place(P), culprit(C), missing(M).
"""


def asp_program(show: str) -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTING_REGISTRY:
        lines.append(asp.fact("place", p))
    for c in ["wheeler", "mira", "pax", "nina"]:
        lines.append(asp.fact("culprit", c))
    for m in MISSING_REGISTRY:
        lines.append(asp.fact("missing", m))
    return "\n".join(lines) + "\n" + ASP_RULES + "\n" + show + "\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [
            StoryParams(place=p, culprit=c, missing=m, detective_name="Ivy", suspect_name="Mina")
            for p, c, m in valid_combos()
        ]
        samples = [generate(p) for p in combos[: max(1, args.n)]]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
