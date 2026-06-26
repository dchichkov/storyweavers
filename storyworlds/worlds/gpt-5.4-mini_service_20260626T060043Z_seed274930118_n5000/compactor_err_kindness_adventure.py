#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/compactor_err_kindness_adventure.py
===============================================================================================================

A small storyworld about a child-sized adventure around a compactor, a tiny
err, and a kind fix.

Premise:
- A child helper is carrying a box of recyclables to the yard.
- A sorting mistake causes the compactor to jam.

Tension:
- The box is in the wrong pile.
- The compactor makes a worrying err sound and stops.
- The child worries the whole yard will fall behind.

Turn:
- The child notices the mistake, kindly asks for help, and sorts the load by hand.
- Friends and a caretaker work together to clear the jam.

Resolution:
- The compactor starts again.
- The yard feels calm, and the child leaves with a warm feeling from being kind.

The script follows the Storyweavers contract:
- stdlib only
- imports shared results eagerly
- imports shared ASP lazily
- defines StoryParams, registries, parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "mom"}
        male = {"boy", "father", "man", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Fix:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out = []
        buf = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)

    def copy(self) -> "World":
        import copy

        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.zone = set(self.zone)
        w.fired = set(self.fired)
        return w


def _gather_world() -> str:
    return "A small recycling yard sat beside a bright road, with bins, belts, and a big machine at the center."


def _act_delight(activity: Activity) -> str:
    return {
        "recycle": "the clink of bottles and the whirr of belts made the yard feel busy and brave",
        "deliver": "the cart wheels rolled like a soft drumbeat across the paving",
        "sort": "the neat stacks made the place feel tidy and safe",
    }.get(activity.id, "the work felt like an adventure")


def _hero_intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.memes.get("traits", []) if t != "little"), "kind")
    world.say(f"{hero.id} was a little {trait} {hero.type} who liked helping where things were busy.")


def _love_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund}, because {_act_delight(activity)}."
    )


def _introduce_compactor(world: World, compactor: Entity) -> None:
    world.say(
        f"At the middle of the yard stood {compactor.label}, a big compactor with a heavy mouth that pressed trash flat."
    )


def _start_mission(world: World, hero: Entity, caregiver: Entity, activity: Activity, prize: Entity) -> None:
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {caregiver.type} went to {world.place.name} with a load to {activity.verb}."
    )
    world.say(f"{hero.id} carried {hero.pronoun('possessive')} {prize.label} carefully and watched the yard hum.")


def _predict_jam(world: World, hero: Entity, activity: Activity, prize: Entity) -> bool:
    sim = world.copy()
    _do_activity(sim, sim.get(hero.id), activity, narrate=False)
    return bool(sim.facts.get("jammed", False))


def _do_activity(world: World, hero: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    hero.meters[activity.mess] = hero.meters.get(activity.mess, 0) + 1
    if narrate:
        world.say(f"{hero.id} tried to {activity.verb}, and the yard suddenly felt less steady.")


def _warn(world: World, caregiver: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    if not _predict_jam(world, hero, activity, prize):
        return False
    world.say(
        f'"Careful," {caregiver.pronoun("possessive")} {caregiver.type} said. "If we push that load now, the compactor may go err and jam."'
    )
    world.facts["warned"] = True
    return True


def _mistake(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["embarrassed"] = hero.memes.get("embarrassed", 0) + 1
    world.say(
        f"But {hero.id} saw that one bin had been sorted the wrong way, and {hero.pronoun()} felt a tiny err of worry in {hero.pronoun('possessive')} chest."
    )
    world.say(f"{hero.pronoun().capitalize()} reached for the wrong lever by mistake.")


def _jam(world: World, compactor: Entity) -> None:
    if ("jam", compactor.id) in world.fired:
        return
    world.fired.add(("jam", compactor.id))
    compactor.meters["jammed"] = compactor.meters.get("jammed", 0) + 1
    world.facts["jammed"] = True
    world.say(f"The compactor gave a loud err and stopped with its mouth half shut.")


def _kind_fix(world: World, hero: Entity, caregiver: Entity, prize: Entity, fix: Optional[Fix]) -> None:
    if fix is None:
        raise StoryError("No reasonable fix exists for this story.")
    world.say(
        f"{hero.id} did not scold anyone. Instead, {hero.pronoun()} spoke kindly and said, "
        f'"Let’s slow down and sort it together."'
    )
    world.say(
        f"{caregiver.pronoun().capitalize()} nodded, and soon they used {fix.label} to clear the stuck load by hand."
    )
    world.say(
        f"When the compactor was ready again, it hummed smoothly, and {hero.id} felt proud that kindness had helped the whole yard."
    )
    world.facts["fixed"] = True


def tell(place: Place, activity: Activity, prize_cfg: Prize, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender))
    hero.memes["traits"] = [trait, "little", "kind"]
    caregiver = world.add(Entity(id="Caregiver", kind="character", type=parent_type, label="the caregiver"))
    prize = world.add(Entity(id="box", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=caregiver.id, region=prize_cfg.region, plural=prize_cfg.plural))
    compactor = world.add(Entity(id="Compactor", type="compactor", label="the compactor", protective=True))

    world.say(_gather_world())
    _hero_intro(world, hero)
    _love_activity(world, hero, activity)
    _introduce_compactor(world, compactor)
    world.para()
    _start_mission(world, hero, caregiver, activity, prize)
    _warn(world, caregiver, hero, activity, prize)
    _mistake(world, hero, activity)
    _jam(world, compactor)
    world.para()
    fix = FIXES["clean_sort"]
    _kind_fix(world, hero, caregiver, prize, fix)

    world.facts.update(hero=hero, caregiver=caregiver, prize=prize, activity=activity, place=place, compactor=compactor, fix=fix)
    return world


PLACES = {
    "yard": Place(name="the recycling yard", indoors=False, affords={"sort", "deliver", "recycle"}),
    "dock": Place(name="the river dock", indoors=False, affords={"deliver", "sort"}),
    "shed": Place(name="the storage shed", indoors=True, affords={"sort"}),
}

ACTIVITIES = {
    "sort": Activity(
        id="sort",
        verb="sort the load",
        gerund="sorting the load",
        rush="rush to the wrong bin",
        mess="scattered",
        soil="mixed up",
        zone={"hands"},
        keyword="sort",
        tags={"kindness", "recycle"},
    ),
    "deliver": Activity(
        id="deliver",
        verb="deliver the crate",
        gerund="delivering crates",
        rush="hurry to the conveyor",
        mess="scattered",
        soil="out of order",
        zone={"hands", "feet"},
        keyword="deliver",
        tags={"adventure", "kindness"},
    ),
    "recycle": Activity(
        id="recycle",
        verb="feed the bottles into the line",
        gerund="helping the bottles along",
        rush="push the last bin too fast",
        mess="scattered",
        soil="out of place",
        zone={"hands"},
        keyword="recycle",
        tags={"recycle", "adventure"},
    ),
}

PRIZES = {
    "crate": Prize(label="crate", phrase="a small crate of clean glass", type="crate", region="hands"),
    "box": Prize(label="box", phrase="a cardboard box of sorted cans", type="box", region="hands", plural=False),
    "bag": Prize(label="bag", phrase="a bag of mixed bottles", type="bag", region="hands", plural=False),
}

FIXES = {
    "clean_sort": Fix(
        id="clean_sort",
        label="a sorting chart",
        covers={"hands"},
        guards={"scattered"},
        prep="use a sorting chart first",
        tail="went back to the bins with a cleaner plan",
    ),
    "slow_steps": Fix(
        id="slow_steps",
        label="steady hands and labels",
        covers={"hands", "feet"},
        guards={"scattered"},
        prep="move slowly and read the labels again",
        tail="walked back carefully and kept the stacks straight",
    ),
}

GIRL_NAMES = ["Mina", "Lia", "Noa", "Ivy", "Tess", "Zoe", "Mira", "Aya"]
BOY_NAMES = ["Finn", "Leo", "Nico", "Eli", "Theo", "Owen", "Milo", "Jude"]
TRAITS = ["brave", "curious", "gentle", "helpful", "spirited"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pname, place in PLACES.items():
        for aid in place.affords:
            act = ACTIVITIES[aid]
            for prize_id, prize in PRIZES.items():
                if act.keyword == "sort" or act.keyword == "deliver" or act.keyword == "recycle":
                    combos.append((pname, aid, prize_id))
    return combos


KNOWLEDGE = {
    "compactor": [("What is a compactor?", "A compactor is a machine that presses trash or recycling into a smaller, tighter pile.")],
    "err": [("What does err mean here?", "Here, err means a small mistake or a warning sound that tells you something is wrong.")],
    "kindness": [("What is kindness?", "Kindness means being gentle, helpful, and caring about other people and what they need.")],
    "recycle": [("What does recycling mean?", "Recycling means sorting used things so they can be made into new things instead of being thrown away.")],
    "adventure": [("What makes a story feel like an adventure?", "An adventure story usually has a goal, a problem to solve, and a brave choice that helps everyone.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    place = f["place"].name
    return [
        f'Write a gentle adventure story for a young child about {hero.id} at {place} involving a compactor and a tiny err.',
        f"Tell a story where {hero.id} wants to {act.verb}, makes a small mistake, and answers it with kindness.",
        "Write a short, child-friendly adventure where helping by hand fixes a jammed machine.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    caregiver = f["caregiver"]
    prize = f["prize"]
    act = f["activity"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do at {f['place'].name}?",
            answer=f"{hero.id} wanted to {act.verb}. {hero.pronoun().capitalize()} was helping in the busy yard.",
        ),
        QAItem(
            question=f"Why did the compactor make an err sound?",
            answer="It made an err sound because the load was sorted the wrong way and the machine jammed.",
        ),
        QAItem(
            question=f"What did {hero.id} carry carefully during the adventure?",
            answer=f"{hero.id} carried {hero.pronoun('possessive')} {prize.label} carefully so it would not get mixed up.",
        ),
        QAItem(
            question=f"How did the story end after the mistake?",
            answer=f"{hero.id} stayed kind, sorted the problem by hand, and helped the compactor work again.",
        ),
    ]
    if f.get("fixed"):
        qa.append(QAItem(
            question=f"What did the caregiver do after {hero.id} pointed out the problem?",
            answer=f"{caregiver.pronoun().capitalize()} helped clear the jam, and together they used a sorting chart to make the next step safer.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("compactor")
    tags.add("err")
    tags.add("kindness")
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v and k != "traits"}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  facts={world.facts.keys()}")
    return "\n".join(lines)


ASP_RULES = r"""
place(yard). place(dock). place(shed).
activity(sort). activity(deliver). activity(recycle).
prize(crate). prize(box). prize(bag).

affords(yard,sort). affords(yard,deliver). affords(yard,recycle).
affords(dock,deliver). affords(dock,sort).
affords(shed,sort).

kind_of_gentle_action(sort).
kind_of_gentle_action(deliver).
kind_of_gentle_action(recycle).

valid(Place,Act,Prize) :- affords(Place,Act), prize(Prize), activity(Act), place(Place).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    for p, pl in PLACES.items():
        for a in pl.affords:
            lines.append(asp.fact("affords", p, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    return 1


def explain_rejection() -> str:
    return "(No story: the requested options do not make a reasonable adventure about the compactor.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny adventure about a compactor, an err, and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError(explain_rejection())
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible story combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="yard", activity="sort", prize="box", name="Mina", gender="girl", parent="mother", trait="helpful"),
            StoryParams(place="dock", activity="deliver", prize="crate", name="Finn", gender="boy", parent="father", trait="brave"),
            StoryParams(place="yard", activity="recycle", prize="bag", name="Tess", gender="girl", parent="mother", trait="gentle"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
