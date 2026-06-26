#!/usr/bin/env python3
"""
storyworlds/worlds/sacrament_bad_ending_reconciliation_heartwarming.py
======================================================================

A small standalone storyworld about a child, a sacrament, a bad ending,
and a warm reconciliation.

The seed idea:
- A child is entrusted with a sacrament tray for a gentle family or chapel
  gathering.
- Something goes wrong: the bread tilts, the cup spills, and the moment feels
  ruined.
- Then comes reconciliation: someone apologizes, someone forgives, and the
  group makes the moment tender again.

This world keeps the prose concrete and state-driven:
- physical meters track spill, brokenness, and tidiness
- emotional memes track worry, shame, hurt, comfort, and closeness
- the ending image proves what changed
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "daughter"}
        male = {"boy", "father", "dad", "man", "son"}
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
    kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Sacrament:
    id: str
    name: str
    container: str
    contents: str
    phrase: str
    risk: str
    mess: str
    keyword: str = "sacrament"


@dataclass
class Comfort:
    id: str
    label: str
    method: str
    result: str


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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _join(parts: list[str]) -> str:
    return " ".join(p for p in parts if p)


def _capitalize_clause(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def spill_risk(world: World, child: Entity, sacrament: Sacrament) -> bool:
    return world.setting.kind in {"chapel", "hall", "kitchen"} and sacrament.name in {"cup", "tray", "plate"}


def steady_fix_available(world: World, sacrament: Sacrament) -> bool:
    return "cloth" in world.setting.affords or sacrament.container == "tray"


def settings() -> dict[str, Setting]:
    return {
        "chapel": Setting(place="the chapel", kind="chapel", affords={"cloth", "bench"}),
        "kitchen": Setting(place="the kitchen table", kind="kitchen", affords={"cloth", "bowl"}),
        "living_room": Setting(place="the living room", kind="home", affords={"cloth", "rug"}),
    }


SACRAMENTS = {
    "cup": Sacrament(
        id="cup",
        name="cup",
        container="cup",
        contents="grape juice",
        phrase="a small cup of grape juice for the sacrament",
        risk="spilled",
        mess="spill",
        keyword="sacrament",
    ),
    "plate": Sacrament(
        id="plate",
        name="plate",
        container="plate",
        contents="bread pieces",
        phrase="a little plate of bread for the sacrament",
        risk="crumbled",
        mess="crumbs",
        keyword="sacrament",
    ),
    "tray": Sacrament(
        id="tray",
        name="tray",
        container="tray",
        contents="bread and juice",
        phrase="a careful sacrament tray",
        risk="tipped",
        mess="spill",
        keyword="sacrament",
    ),
}

COMFORTS = [
    Comfort(
        id="apology",
        label="an apology",
        method="said sorry and helped clean up",
        result="the hurt softened",
    ),
    Comfort(
        id="blessing",
        label="a blessing",
        method="held hands and spoke kindly",
        result="the room felt gentle again",
    ),
    Comfort(
        id="sharing",
        label="a shared plate",
        method="split the bread into smaller pieces",
        result="everyone could take part again",
    ),
]

CHILD_NAMES = ["Maya", "Eli", "Nora", "Leo", "Ivy", "Sam", "Lina", "Noah"]
PARENT_NAMES = ["Mom", "Dad", "Aunt June", "Uncle Ben"]
TRAITS = ["careful", "gentle", "shy", "earnest", "small", "hopeful"]


@dataclass
class StoryParams:
    place: str
    sacrament: str
    child_name: str
    child_gender: str
    parent_name: str
    trait: str
    seed: Optional[int] = None


def build_world(params: StoryParams) -> World:
    setting = settings()[params.place]
    world = World(setting)
    child_type = params.child_gender
    child = world.add(Entity(id=params.child_name, kind="character", type=child_type))
    parent = world.add(Entity(id=params.parent_name, kind="character", type="parent"))
    sac = SACRAMENTS[params.sacrament]
    vessel = world.add(Entity(
        id="sacrament",
        type=sac.container,
        label=sac.name,
        phrase=sac.phrase,
        owner=child.id,
        caretaker=parent.id,
    ))
    cloth = world.add(Entity(id="cloth", type="cloth", label="clean cloth", owner=parent.id))
    world.facts.update(child=child, parent=parent, sacrament=vessel, sac=sac, cloth=cloth)
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    child: Entity = world.facts["child"]
    parent: Entity = world.facts["parent"]
    sac: Entity = world.facts["sacrament"]
    sac_def: Sacrament = world.facts["sac"]
    trait = params.trait

    child.memes["reverence"] = 1
    child.memes["hope"] = 1
    world.say(
        f"{child.id} was a {trait} little {child.type} who wanted to help with the sacrament."
    )
    world.say(
        f"{child.pronoun().capitalize()} watched carefully as {parent.id} set out {sac.phrase}."
    )
    world.say(
        f"{child.id} wanted to carry {sac.it()} {world.setting.place} so the moment would feel special."
    )

    world.para()
    child.memes["worry"] += 1
    world.say(
        f"At {world.setting.place}, {child.id} lifted {sac.it()} with both hands."
    )
    world.say(
        f"For one heartbeat, everything looked calm."
    )

    child.meters["steady"] = 0.0
    sac.meters["spill"] = 0.0
    if spill_risk(world, child, sac_def):
        child.memes["nervous"] += 1
        sac.meters["spill"] += 1
        sac.meters["broken"] += 0.5
        child.memes["guilt"] += 1
        parent.memes["surprise"] += 1
        parent.memes["hurt"] += 1
        world.say(
            f"Then {child.id}'s elbow bumped the edge, and {sac_def.contents} spilled."
        )
        world.say(
            f"The little mess made {child.id}'s face fall, because the good moment seemed ruined."
        )
    else:
        if not steady_fix_available(world, sac_def):
            raise StoryError("This sacrament setup is too easy; it needs a real risk and a real recovery.")
        world.say(
            f"Nothing spilled, and the sacrament stayed calm in {child.id}'s hands."
        )

    world.para()
    comfort = COMFORTS[0]
    if sac.meters.get("spill", 0) >= THRESHOLD:
        parent.memes["care"] = 1
        world.say(
            f"{parent.id} knelt beside {child.id} and did not scold."
        )
        world.say(
            f'"It is all right," {parent.id} said. "We can fix a mistake together."'
        )
        child.memes["shame"] += 1
        child.memes["comforted"] += 1
        child.memes["close"] += 1
        parent.memes["close"] += 1
        sac.meters["spill"] = 0.0
        sac.meters["tidy"] = 1.0
        world.say(
            f"{child.id} whispered sorry, and {parent.id} {comfort.method}."
        )
        world.say(
            f"They wiped the table until it shone, and the little room felt kind again."
        )
        world.say(
            f"Then they shared a gentle blessing, and the sacrament continued without hurry."
        )
        world.say(
            f"By the end, {child.id} was holding hands instead of holding fear."
        )
    else:
        child.memes["comforted"] += 1
        world.say(
            f"{parent.id} smiled and thanked {child.id} for being careful."
        )
        world.say(
            f"The sacrament stayed steady, and the family felt closer because of it."
        )

    world.facts.update(params=params, comfort=comfort, resolved=sac.meters.get("spill", 0) == 0.0)
    return world


def story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    sac: Entity = f["sacrament"]
    sac_def: Sacrament = f["sac"]
    return [
        f"Write a heartwarming short story for a young child about {child.id} helping with a sacrament.",
        f"Tell a gentle story where {child.id} carries {sac.phrase} and something goes wrong, then the family reconciles.",
        f"Write a small story about a {child.type} named {child.id}, {parent.id}, and a sacrament that ends in forgiveness and comfort.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    sac: Entity = f["sacrament"]
    sac_def: Sacrament = f["sac"]
    resolved = f["resolved"]
    place = world.setting.place
    qa = [
        QAItem(
            question=f"Who was helping with the sacrament at {place}?",
            answer=f"{child.id} was helping with the sacrament at {place}, with {parent.id} nearby.",
        ),
        QAItem(
            question=f"What did {child.id} try to carry carefully?",
            answer=f"{child.id} tried to carry {sac.phrase} carefully.",
        ),
        QAItem(
            question=f"What went wrong when {child.id} bumped the edge?",
            answer=f"{sac_def.contents} spilled, and that made the moment feel sad for a little while.",
        ),
    ]
    if resolved:
        qa.append(
            QAItem(
                question=f"How did {child.id} and {parent.id} fix the bad moment?",
                answer=f"They apologized, cleaned the table together, and shared a gentle blessing so the sacrament could continue.",
            )
        )
        qa.append(
            QAItem(
                question=f"How did {child.id} feel at the end?",
                answer=f"{child.id} felt comforted and close to {parent.id} again.",
            )
        )
    return qa


KNOWLEDGE = [
    QAItem(
        question="What is a sacrament?",
        answer="A sacrament is a holy or very special act people do to show faith, promise, and care together.",
    ),
    QAItem(
        question="Why do people speak softly during a sacred moment?",
        answer="People often speak softly so the moment feels calm, respectful, and peaceful for everyone there.",
    ),
    QAItem(
        question="Why does an apology help after a mistake?",
        answer="An apology helps because it shows someone noticed the hurt and wants to make things better.",
    ),
]


def world_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


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
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for sac in SACRAMENTS:
            if place in {"chapel", "kitchen"} and sac in {"cup", "tray"}:
                combos.append((place, sac))
    return combos


def explain_rejection(place: str, sac: str) -> str:
    return f"(No story: {sac} at {place} does not create a gentle enough risk for this world.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p, s in SETTINGS.items():
        lines.append(asp.fact("setting", p))
        lines.append(asp.fact("kind", p, s.kind))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", p, a))
    for s in SACRAMENTS.values():
        lines.append(asp.fact("sacrament", s.id))
        lines.append(asp.fact("container", s.id, s.container))
        lines.append(asp.fact("risk", s.id, s.risk))
        lines.append(asp.fact("mess", s.id, s.mess))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place,S) :- setting(Place), sacrament(S), affords(Place, cloth), container(S, cup).
valid(Place,S) :- setting(Place), sacrament(S), affords(Place, cloth), container(S, tray).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming sacrament story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--sacrament", choices=SACRAMENTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.place and args.sacrament:
        if (args.place, args.sacrament) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.sacrament))
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.sacrament:
        combos = [c for c in combos if c[1] == args.sacrament]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, sac = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, sacrament=sac, child_name=name, child_gender=gender, parent_name=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=story_text(world),
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


CURATED = [
    StoryParams(place="chapel", sacrament="cup", child_name="Maya", child_gender="girl", parent_name="Mom", trait="careful"),
    StoryParams(place="kitchen", sacrament="tray", child_name="Eli", child_gender="boy", parent_name="Dad", trait="earnest"),
    StoryParams(place="living_room", sacrament="plate", child_name="Nora", child_gender="girl", parent_name="Aunt June", trait="hopeful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, sac in combos:
            print(f"  {place:12} {sac}")
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
