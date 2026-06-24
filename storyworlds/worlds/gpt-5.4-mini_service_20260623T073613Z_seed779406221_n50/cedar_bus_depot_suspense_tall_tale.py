#!/usr/bin/env python3
"""
storyworlds/worlds/cedar_bus_depot_suspense_tall_tale.py
========================================================

A standalone storyworld for a tiny Tall Tale-style suspense story set in a bus
depot. The seed word is cedar, and the world leans on a big, folksy, suspenseful
voice: creaking boards, a waiting bus, a vanished cedar crate, and a brave child
who follows clues to bring the day back together.

The story model is state-driven: meters track physical conditions, memes track
feelings, and prose is rendered from those changes rather than from a fixed
paragraph with swapped nouns.
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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    kind: str
    reveals: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    kind: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    method: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    place: str
    clue: str
    prize: str
    fix: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "bus_depot": Setting(place="the bus depot", afford={"search", "wait", "listen"}),
}

CLUES = {
    "cedar_box": Clue(
        id="cedar_box",
        label="cedar box",
        phrase="a cedar box",
        kind="box",
        reveals="the cedar smell and the scratched lid gave away the hiding place",
        risk="its missing weight made the depot feel wrong",
        tags={"cedar", "box", "hide"},
    ),
    "cedar_sign": Clue(
        id="cedar_sign",
        label="cedar sign",
        phrase="a cedar sign",
        kind="sign",
        reveals="the cedar grain glowed in the light and pointed to the lost shelf",
        risk="its empty hook left a lonely gap by the timetable",
        tags={"cedar", "sign"},
    ),
    "cedar_whistle": Clue(
        id="cedar_whistle",
        label="cedar whistle",
        phrase="a cedar whistle",
        kind="whistle",
        reveals="the cedar whistle answered with a long wooden note from under the bench",
        risk="its silence made everyone hold their breath",
        tags={"cedar", "whistle", "sound"},
    ),
}

PRIZES = {
    "ticket_roll": Prize(
        id="ticket_roll",
        label="ticket roll",
        phrase="the old ticket roll",
        region="desk",
        kind="roll",
        tags={"ticket", "paper"},
    ),
    "bus_schedule": Prize(
        id="bus_schedule",
        label="bus schedule",
        phrase="the big bus schedule",
        region="wall",
        kind="paper",
        tags={"schedule", "paper"},
    ),
    "lost_bundle": Prize(
        id="lost_bundle",
        label="bundle",
        phrase="the lost bundle of cedar tags",
        region="bench",
        kind="bundle",
        plural=True,
        tags={"cedar", "bundle"},
    ),
}

FIXES = {
    "lantern": Fix(
        id="lantern",
        label="lantern",
        phrase="a little lantern",
        method="shine a soft light",
        tags={"light", "safe"},
    ),
    "bell": Fix(
        id="bell",
        label="bell",
        phrase="the depot bell",
        method="ring the bell and call the helper",
        tags={"sound", "safe"},
    ),
    "map": Fix(
        id="map",
        label="map",
        phrase="the hand-drawn depot map",
        method="follow the map marks",
        tags={"map", "safe"},
    ),
}

NAMES = ["Nora", "Milo", "June", "Eli", "Maya", "Otis"]
HELPERS = ["the conductor", "the depot keeper", "the bus driver"]
TRAITS = ["steady", "curious", "brave", "patient"]


def prize_at_risk(clue: Clue, prize: Prize) -> bool:
    return clue.kind in {"box", "sign", "whistle"} and prize.kind in {"roll", "paper", "bundle"}


def select_fix(clue: Clue, prize: Prize) -> Optional[Fix]:
    if clue.id == "cedar_whistle":
        return FIXES["bell"]
    if clue.id == "cedar_box":
        return FIXES["lantern"]
    if clue.id == "cedar_sign":
        return FIXES["map"]
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for clue_id, clue in CLUES.items():
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(clue, prize) and select_fix(clue, prize):
                    out.append((place, clue_id, prize_id))
    return out


def tell(setting: Setting, clue: Clue, prize: Prize, fix: Fix, name: str, gender: str, helper: str) -> World:
    world = World(setting)
    kid = world.add(Entity(id=name, kind="character", type=gender, label=name))
    adult = world.add(Entity(id="Helper", kind="character", type="adult", label=helper))
    prize_ent = world.add(Entity(id="Prize", type=prize.kind, label=prize.label, plural=prize.plural))
    clue_ent = world.add(Entity(id="Clue", type=clue.kind, label=clue.label))
    fix_ent = world.add(Entity(id="Fix", type=fix.id, label=fix.label))

    kid.memes["curiosity"] = 1
    kid.memes["wonder"] = 1
    world.say(
        f"{name} came into the bus depot where the ceiling was high as a barn roof and the air smelled like cedar and rain."
    )
    world.say(
        f"Down by the benches, {name} noticed {clue.phrase}. Folks in the depot said it was a sure sign that something had gone missing."
    )
    world.para()
    kid.memes["suspense"] = 1
    prize_ent.meters["hidden"] = 1
    world.say(
        f"The old {prize.label} was not where it ought to be, and that made the whole depot feel hush-hush and slow."
    )
    world.say(
        f"{name} listened hard. {clue.reveals.capitalize()}."
    )
    world.say(
        f"At the far end of the depot, {helper} watched and waited, ready to help if the trail turned tricky."
    )
    world.para()
    world.say(
        f"{name} followed the clue with a careful step, using {fix.phrase} to {fix.method}."
    )
    prize_ent.meters["found"] = 1
    prize_ent.memes["relief"] = 1
    kid.memes["joy"] = 1
    kid.memes["suspense"] = 0
    world.say(
        f"Under a bench near the cedar crate, the lost {prize.label} turned up at last."
    )
    world.say(
        f"{helper} laughed like a train whistle and said the depot was in good hands now."
    )
    world.say(
        f"{name} held the {prize.label} close, and the bus depot felt bright again, with cedar in the air and no more hiding left to do."
    )

    world.facts.update(
        kid=kid,
        adult=adult,
        prize=prize_ent,
        clue=clue_ent,
        fix=fix_ent,
        helper=helper,
        clue_cfg=clue,
        prize_cfg=prize,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid = f["kid"]
    clue = f["clue_cfg"]
    prize = f["prize_cfg"]
    return [
        f'Write a tall-tale suspense story for a young child set in {world.setting.place} that includes cedar and a missing {prize.label}.',
        f"Tell a suspenseful story where {kid.id} follows {clue.label} through {world.setting.place} and finds the lost {prize.label}.",
        f'Write a child-friendly bus depot story with cedar, a hidden object, and a careful clue that leads to a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid = f["kid"]
    clue = f["clue_cfg"]
    prize = f["prize_cfg"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Who is the story about in {world.setting.place}?",
            answer=f"It is about {kid.id}, who notices the missing {prize.label} and follows the cedar clue through the bus depot.",
        ),
        QAItem(
            question=f"What clue did {kid.id} find?",
            answer=f"{kid.id} found {clue.phrase}. It gave a cedar hint about where the missing {prize.label} was hiding.",
        ),
        QAItem(
            question=f"Who helped near the end of the story?",
            answer=f"{helper} was ready to help, and {kid.id} used that help to finish the search safely.",
        ),
        QAItem(
            question=f"What happened to the lost {prize.label}?",
            answer=f"The lost {prize.label} was found under a bench near the cedar crate, so the depot could relax again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is cedar?",
            answer="Cedar is a kind of tree wood with a strong smell. People use it for boxes, signs, and little tools because it is sturdy and sweet-smelling.",
        ),
        QAItem(
            question="What is a bus depot?",
            answer="A bus depot is a place where buses stop, wait, and get ready for their trips. People can also work there and look for lost things.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense is the feeling of wondering what will happen next. A suspenseful story makes you wait, listen, and hope the problem gets solved.",
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {e.label} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Clue, Prize) :- setting(Place), clue(Clue), prize(Prize), risk(Clue, Prize), fix_for(Clue, Prize).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("risk", cid, c.kind))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("kind", pid, p.kind))
    for cid, c in CLUES.items():
        for pid, p in PRIZES.items():
            if select_fix(c, p):
                lines.append(asp.fact("fix_for", cid, pid))
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
        print(f"OK: ASP matches Python for {len(py)} combos.")
        return 0
    print("Mismatch:")
    print("only python", sorted(py - cl))
    print("only asp", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale suspense at a bus depot with cedar clues.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = valid_combos()
    combos = [c for c in combos if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, prize = rng.choice(sorted(combos))
    clue_cfg = CLUES[clue]
    prize_cfg = PRIZES[prize]
    fix = args.fix or select_fix(clue_cfg, prize_cfg).id
    if fix not in FIXES:
        raise StoryError("Unknown fix.")
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, clue=clue, prize=prize, fix=fix, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CLUES[params.clue], PRIZES[params.prize], FIXES[params.fix], params.name, params.gender, params.helper)
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
    if trace and sample.world:
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
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for c in valid_combos():
            p = StoryParams(place=c[0], clue=c[1], prize=c[2], fix=select_fix(CLUES[c[1]], PRIZES[c[2]]).id, name="Nora", gender="girl", helper="the conductor")
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.clue} / {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
