#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ketchup_invention_assed_problem_solving_reconciliation_heartwarming.py
=======================================================================================================

A standalone story world about a small kitchen invention, a ketchup mishap,
and a warm reconciliation. The story is built from simulated state: a child
tries to invent a better lunch helper, something goes wrong, then the children
solve it together and make up.

This world includes the seed words ketchup, invention, and assed, and is tuned
for a heartwarming tone with problem solving and reconciliation.
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class KitchenSetting:
    id: str
    place: str
    warmth: str
    table: str


@dataclass
class Invention:
    id: str
    purpose: str
    parts: str
    action: str
    risk: str
    fixable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Mess:
    id: str
    label: str
    thing: str
    spread: int
    sticky: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: KitchenSetting) -> None:
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spill(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.meters["ketchup"] < THRESHOLD:
            continue
        sig = ("spill", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "floor" in world.entities:
            world.get("floor").meters["sticky"] += 1
        out.append("The kitchen got sticky.")
    return out


def _r_sad(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.meters["ketchup"] < THRESHOLD:
            continue
        sig = ("sad", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in world.characters():
            kid.memes["worry"] += 1
        out.append("The children looked worried.")
    return out


CAUSAL_RULES = [Rule("spill", "physical", _r_spill), Rule("sad", "social", _r_sad)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def characters(world: World) -> list[Entity]:
    return [e for e in world.entities.values() if e.kind == "character"]


World.characters = characters  # type: ignore[attr-defined]


def reasonable(invention: Invention, mess: Mess) -> bool:
    return invention.fixable and mess.sticky


def repair_fit(repair: Repair) -> bool:
    return repair.sense >= SENSE_MIN


def mess_severity(mess: Mess, delay: int) -> int:
    return mess.spread + delay


def contained(repair: Repair, mess: Mess, delay: int) -> bool:
    return repair.power >= mess_severity(mess, delay)


def build_scene(world: World, maker: Entity, sibling: Entity, invention: Invention) -> None:
    maker.memes["curiosity"] += 1
    sibling.memes["hope"] += 1
    world.say(
        f"On a bright afternoon in {world.setting.place}, {maker.id} had an idea for an invention. "
        f"{maker.id} wanted to use {invention.purpose} to make lunch kinder and more fun."
    )
    world.say(
        f"{sibling.id} sat at {world.setting.table}, ready to taste, while the air smelled warm and cozy."
    )


def invent(world: World, maker: Entity, invention: Invention) -> None:
    maker.memes["pride"] += 1
    world.say(
        f'{maker.id} gathered {invention.parts} and whispered, "This will be my ketchup invention."'
    )
    world.say(f"It was meant to {invention.action}, so every bite would feel a little brighter.")


def warn(world: World, sibling: Entity, maker: Entity, mess: Mess) -> None:
    sibling.memes["care"] += 1
    world.say(
        f'{sibling.id} bit {sibling.pronoun("possessive")} lip. "Be careful," {sibling.pronoun()} said, '
        f'"that {mess.label} can get everywhere."'
    )


def spill(world: World, maker: Entity, mess: Mess) -> None:
    maker.meters[mess.id] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the squeeze bottle tipped, and {mess.label} splashed across the table and the floor."
    )


def react(world: World, sibling: Entity, maker: Entity) -> None:
    sibling.memes["upset"] += 1
    maker.memes["guilt"] += 1
    world.say(f"{sibling.id} frowned, and for a moment both children went quiet.")


def apologize(world: World, maker: Entity, sibling: Entity, invention: Invention) -> None:
    maker.memes["sorry"] += 1
    world.say(
        f'{maker.id} looked at {sibling.id} and said, "I am sorry. I wanted my invention to help, not make a mess."'
    )
    world.say(
        f'{sibling.id} took a breath, nodded, and said, "I know. Let\'s fix it together."'
    )


def fix(world: World, maker: Entity, sibling: Entity, repair: Repair, mess: Mess) -> None:
    maker.memes["relief"] += 1
    sibling.memes["relief"] += 1
    world.say(
        f"Together they used {repair.text}."
    )
    world.say(
        f"The sticky {mess.label} was cleaned up, and the kitchen felt calm again."
    )


def end(world: World, maker: Entity, sibling: Entity) -> None:
    maker.memes["love"] += 1
    sibling.memes["love"] += 1
    world.say(
        f"After that, {maker.id} shared the last bite with {sibling.id}, and they both smiled at the neat little table."
    )
    world.say(
        "The invention still existed, but now it was a gentler plan, built with care and a friend beside it."
    )


def tell(setting: KitchenSetting, invention: Invention, mess: Mess, repair: Repair,
         maker_name: str = "Maya", maker_gender: str = "girl",
         sibling_name: str = "Ben", sibling_gender: str = "boy") -> World:
    world = World(setting)
    maker = world.add(Entity(id=maker_name, kind="character", type=maker_gender, role="maker"))
    sibling = world.add(Entity(id=sibling_name, kind="character", type=sibling_gender, role="sibling"))
    floor = world.add(Entity(id="floor", label="the floor"))
    world.facts.update(setting=setting, invention=invention, mess=mess, repair=repair,
                       maker=maker, sibling=sibling, floor=floor)

    build_scene(world, maker, sibling, invention)
    world.para()
    invent(world, maker, invention)
    warn(world, sibling, maker, mess)
    spill(world, maker, mess)
    react(world, sibling, maker)
    world.para()
    apologize(world, maker, sibling, invention)
    fix(world, maker, sibling, repair, mess)
    world.para()
    end(world, maker, sibling)

    world.facts.update(outcome="reconciled", sticky=floor.meters["sticky"] >= THRESHOLD)
    return world


SETTING = KitchenSetting("sunlit kitchen", "the sunlit kitchen", "warm", "small table")

INVENTIONS = {
    "ketchup_pump": Invention("ketchup_pump", "put a dab on the plate", "a spoon, a bottle, and a tiny cardboard ramp",
                              "squeeze ketchup in a careful ribbon", "it might spill if tipped",
                              tags={"ketchup", "invention"}),
    "dipper": Invention("dipper", "help a sandwich taste better", "a lid, a straw, and a little handle",
                        "carry ketchup from bottle to plate", "it could drip if moved too fast",
                        tags={"ketchup", "invention"}),
}

MESSES = {
    "ketchup": Mess("ketchup", "ketchup", "ketchup", 2, sticky=True, tags={"ketchup"}),
}

REPAIRS = {
    "towel": Repair("towel", 3, 3, "a stack of paper towels and a damp cloth",
                    "used paper towels, but the spill was too big to finish quickly",
                    "cleaned the spill with paper towels and a damp cloth",
                    tags={"cleanup"}),
    "napkins": Repair("napkins", 2, 2, "some napkins and a wet rag",
                      "used napkins, but they soaked through too fast",
                      "wiped up the ketchup with napkins and a wet rag",
                      tags={"cleanup"}),
}

CURATED = [
    ("ketchup_pump", "ketchup", "towel"),
    ("dipper", "ketchup", "napkins"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(i, m, r) for i in INVENTIONS for m in MESSAGES for r in REPAIRS if reasonable(INVENTIONS[i], MESSAGES[m]) and repair_fit(REPAIRS[r])]


@dataclass
class StoryParams:
    invention: str
    mess: str
    repair: str
    maker: str
    maker_gender: str
    sibling: str
    sibling_gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming ketchup invention story world.")
    ap.add_argument("--invention", choices=INVENTIONS)
    ap.add_argument("--mess", choices=MESSES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--name")
    ap.add_argument("--sibling")
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
              if (args.invention is None or c[0] == args.invention)
              and (args.mess is None or c[1] == args.mess)
              and (args.repair is None or c[2] == args.repair)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    invention, mess, repair = rng.choice(combos)
    return StoryParams(
        invention, mess, repair,
        args.name or rng.choice(["Maya", "Luna", "Nina", "Ivy"]),
        "girl",
        args.sibling or rng.choice(["Ben", "Eli", "Noah", "Finn"]),
        "boy",
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a heartwarming story about a {f['maker'].id}'s ketchup invention that goes wrong and then gets fixed kindly.",
        f"Tell a problem-solving story where {f['maker'].id} uses ketchup, makes a mess, and then makes up with {f['sibling'].id}.",
        "Write a gentle kitchen story that includes the word assed and ends with two children smiling together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    maker = f["maker"]
    sibling = f["sibling"]
    invention = f["invention"]
    mess = f["mess"]
    repair = f["repair"]
    return [
        QAItem(
            question=f"What was {maker.id} trying to make?",
            answer=f"{maker.id} was trying to make a ketchup invention that would help put a little ketchup on the plate more neatly. It was meant to make lunch easier and nicer."
        ),
        QAItem(
            question=f"Why did {sibling.id} get upset?",
            answer=f"{sibling.id} got upset because the ketchup tipped and made a sticky mess on the table and floor. {sibling.id} had warned that it could get everywhere, so the spill felt disappointing."
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They apologized and cleaned up together using {repair.text}. That turned the mistake into teamwork, and they felt better once the kitchen was clean again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is ketchup?", "Ketchup is a thick red sauce that people often put on food like fries or sandwiches."),
        QAItem("What is an invention?", "An invention is something new that a person makes to help solve a problem or do a job in a new way."),
        QAItem("Why should you clean up a spill?", "Cleaning up a spill keeps the floor safe and the kitchen nice for everyone."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this world needs a sticky ketchup mess and a repair that can really fix it.)"


def asp_facts() -> str:
    import asp
    lines = []
    for i in INVENTIONS:
        lines.append(asp.fact("invention", i))
    for m in MESSAGES:
        lines.append(asp.fact("mess", m))
    for r in REPAIRS:
        lines.append(asp.fact("repair", r))
        lines.append(asp.fact("sense", r, REPAIRS[r].sense))
        lines.append(asp.fact("power", r, REPAIRS[r].power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(I, M, R) :- invention(I), mess(M), repair(R), sticky(M), sense(R,S), sense_min(Min), S >= Min.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP matches Python valid_combos().")
    else:
        print("MISMATCH in valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(invention=None, mess=None, repair=None, name=None, sibling=None), random.Random(0)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"FAILED generate() smoke test: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTING, INVENTIONS[params.invention], MESSAGES[params.mess], REPAIRS[params.repair], params.maker, params.maker_gender, params.sibling, params.sibling_gender)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(i, m, r, "Maya", "girl", "Ben", "boy")) for i, m, r in CURATED]
    else:
        seen = set()
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
