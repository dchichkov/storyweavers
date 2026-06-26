#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gasket_maneuver_transformation_reconciliation_slice_of_life.py
===============================================================================================================================

A small slice-of-life storyworld about a household fix: a child notices a
leak, a careful maneuver replaces a worn gasket, and the day transforms from
messy worry into calm reassurance.

The world is designed around grounded, child-facing repairs and small social
shifts. It keeps the story local: a kitchen counter, a toolkit, a bottle or jar,
and the feeling of learning a careful move from someone trusted.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    slot: str = ""
    plural: bool = False
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
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    covers: set[str]
    fits: set[str]
    maneuver: str
    after: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.task_zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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
        c.task_zone = set(self.task_zone)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_leak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for task in TASKS.values():
            if actor.meters.get(task.id, 0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.slot not in world.task_zone:
                    continue
                sig = ("leak", actor.id, item.id, task.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["wet"] = item.meters.get("wet", 0) + 1
                item.memes["worry"] = item.memes.get("worry", 0) + 1
                out.append(f"A little drip reached {item.label}.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters.get("wet", 0) < THRESHOLD:
            continue
        sig = ("transform", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters["fixed"] = item.meters.get("fixed", 0) + 1
        out.append(f"{item.label.capitalize()} shifted from leaky to snug.")
    return out


CAUSAL_RULES = [Rule("leak", _r_leak), Rule("transform", _r_transform)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def task_at_risk(task: Task, prize: PrizeLike) -> bool:
    return prize.slot in task.zone


@dataclass
class PrizeLike:
    label: str
    phrase: str
    slot: str
    plural: bool = False


def select_fix(task: Task, prize: PrizeLike) -> Optional[Fix]:
    for fix in FIXES:
        if task.id in fix.fits and prize.slot in fix.covers:
            return fix
    return None


def predict(world: World, actor: Entity, task: Task, prize_id: str) -> dict:
    sim = world.copy()
    _do_task(sim, sim.get(actor.id), task, narrate=False)
    prize = sim.get(prize_id)
    return {
        "wet": prize.meters.get("wet", 0) >= THRESHOLD,
        "fixed": prize.meters.get("fixed", 0) >= THRESHOLD,
    }


def _do_task(world: World, actor: Entity, task: Task, narrate: bool = True) -> None:
    if task.id not in world.setting.affords:
        raise StoryError("This setting can't host that task.")
    world.task_zone = set(task.zone)
    actor.meters[task.id] = actor.meters.get(task.id, 0) + 1
    actor.memes["eagerness"] = actor.memes.get("eagerness", 0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    world.say(f"{hero.id} was a little {trait} {hero.type} who liked noticing small fixes.")


def setup(world: World, hero: Entity, helper: Entity, prize: Entity, task: Task) -> None:
    world.say(
        f"At {world.setting.place}, {hero.id} spotted that {hero.pronoun('possessive')} {prize.label} was not quite right."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to {task.verb}, and {helper.id} was nearby with a tiny toolkit."
    )


def worry(world: World, helper: Entity, hero: Entity, task: Task, prize: Entity) -> bool:
    pred = predict(world, hero, task, prize.id)
    if not pred["wet"]:
        return False
    world.facts["predicted_wet"] = True
    world.say(
        f"\"If you {task.verb}, {hero.pronoun('possessive')} {prize.label} could get wet,\" {helper.id} said. \"Let's slow down.\""
    )
    return True


def frustrated(world: World, hero: Entity, task: Task) -> None:
    hero.memes["frustration"] = hero.memes.get("frustration", 0) + 1
    world.say(
        f"{hero.id} frowned, because {hero.pronoun('possessive')} wish to {task.verb} was still buzzing."
    )
    world.say(f"{hero.pronoun().capitalize()} tried to {task.rush}, but the problem stayed in the way.")


def maneuver_fix(world: World, helper: Entity, hero: Entity, task: Task, prize: Entity) -> Optional[Fix]:
    fix = select_fix(task, prize)
    if fix is None:
        return None
    world.say(
        f"{helper.id} showed {hero.id} a careful maneuver: {fix.maneuver}."
    )
    predicted = predict(world, hero, task, prize.id)
    if predicted["wet"]:
        return None
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    world.add(Entity(
        id=fix.id,
        type="thing",
        label=fix.label,
        phrase=fix.phrase,
        owner=hero.id,
        caretaker=helper.id,
        worn_by=hero.id,
        slot=prize.slot,
        plural=fix.plural,
    ))
    world.say(
        f"They used {fix.label} and {fix.after}, so the little repair finally had a shape."
    )
    return fix


def reconcile(world: World, hero: Entity, helper: Entity, task: Task, prize: Entity, fix: Fix) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["frustration"] = 0.0
    world.say(
        f"{hero.id}'s face softened, and {hero.pronoun()} leaned against {helper.id} for a moment."
    )
    world.say(
        f"Together they finished the maneuver, and {prize.label} felt transformed from risky to ready."
    )
    world.say(
        f"{hero.id} smiled because the day had become calm again."
    )


def tell(setting: Setting, task: Task, prize_cfg: PrizeLike,
         hero_name: str = "Mina", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, helper_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["careful"])))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="mom"))
    prize = world.add(Entity(id="prize", type="thing", label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=helper.id, slot=prize_cfg.slot, plural=prize_cfg.plural))
    introduce(world, hero)
    setup(world, hero, helper, prize, task)
    world.para()
    worry(world, helper, hero, task, prize)
    frustrated(world, hero, task)
    fix = maneuver_fix(world, helper, hero, task, prize)
    world.para()
    if fix:
        reconcile(world, hero, helper, task, prize, fix)
    world.facts.update(hero=hero, helper=helper, prize=prize, task=task, setting=setting, fix=fix, resolved=fix is not None)
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen counter", indoors=True, affords={"seal"}),
    "laundry": Setting(place="the laundry room table", indoors=True, affords={"seal"}),
    "porch": Setting(place="the porch bench", indoors=False, affords={"seal"}),
}

TASKS = {
    "seal": Task(
        id="seal",
        verb="re-seat the lid",
        gerund="re-seating the lid",
        rush="reach for the bottle too fast",
        risk="the gasket could slip and leak",
        zone={"counter"},
        keyword="gasket",
        tags={"gasket", "transform"},
    ),
}

FIXES = [
    Fix(
        id="new_gasket",
        label="a fresh gasket",
        phrase="a tiny fresh gasket from the parts box",
        covers={"counter"},
        fits={"seal"},
        maneuver="lifting the lid, rolling the old gasket out, and pressing the new one in place with two fingertips",
        after="the lid clicked shut with a soft, neat sound",
    ),
    Fix(
        id="silicone_ring",
        label="a silicone ring",
        phrase="a flexible silicone ring",
        covers={"counter"},
        fits={"seal"},
        maneuver="sliding the ring into the groove and turning the lid a quarter-turn",
        after="the seal settled down without wobbling",
    ),
]

PRIZES = {
    "bottle": PrizeLike(label="bottle", phrase="a blue water bottle", slot="counter"),
    "jar": PrizeLike(label="jar", phrase="a strawberry jar", slot="counter"),
}

GIRL_NAMES = ["Mina", "Lia", "Nora", "Ruby", "Tess", "Ivy"]
BOY_NAMES = ["Owen", "Eli", "Noah", "Ben", "Finn", "Theo"]
TRAITS = ["curious", "careful", "cheerful", "quiet", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            task = TASKS[task_id]
            for prize_id, prize in PRIZES.items():
                if task_at_risk(task, prize) and select_fix(task, prize):
                    combos.append((place, task_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, task, prize = f["hero"], f["helper"], f["task"], f["prize"]
    return [
        f'Write a slice-of-life story for a young child that includes a gasket and the word "maneuver".',
        f"Tell a gentle story where {hero.id} wants to {task.verb} but {helper.id} worries about {prize.label}, then they fix it together.",
        f"Write a simple home-repair story about a {task.keyword} and a careful, happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, task, prize = f["hero"], f["helper"], f["task"], f["prize"]
    fix = f.get("fix")
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {next((t for t in hero.traits if t != 'little'), hero.type)} {hero.type}, and {helper.id}, who helped with the repair.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {task.verb} because {hero.pronoun('possessive')} {prize.label} needed a careful fix.",
        ),
        QAItem(
            question=f"Why did {helper.id} pause the repair?",
            answer=f"{helper.id} paused because the worn gasket could make {prize.label} leak if they rushed the job.",
        ),
    ]
    if fix is not None:
        qa.append(QAItem(
            question="What maneuver helped the repair work?",
            answer=f"The helpful maneuver was {fix.maneuver}. That made the seal tight again.",
        ))
        qa.append(QAItem(
            question=f"How did the story end for {prize.label}?",
            answer=f"It ended with {prize.label} feeling transformed and ready again, after {fix.after}.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gasket?",
            answer="A gasket is a small ring or seal that helps two parts fit tightly so liquid does not leak out.",
        ),
        QAItem(
            question="What is a maneuver?",
            answer="A maneuver is a careful move or action, especially one that needs a little skill.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means a change from one state to another, like something broken becoming fixed or different.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after a disagreement, so people can feel close and calm.",
        ),
    ]


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.slot:
            bits.append(f"slot={e.slot}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", task="seal", prize="bottle", name="Mina", gender="girl", helper="mother", trait="careful"),
    StoryParams(place="laundry", task="seal", prize="jar", name="Owen", gender="boy", helper="father", trait="curious"),
    StoryParams(place="porch", task="seal", prize="bottle", name="Lia", gender="girl", helper="mother", trait="cheerful"),
]


def explain_rejection(task: Task, prize: PrizeLike) -> str:
    return f"(No story: this task and prize do not make a believable gasket problem.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.task and args.prize:
        task, prize = TASKS[args.task], PRIZES[args.prize]
        if not (task_at_risk(task, prize) and select_fix(task, prize)):
            raise StoryError(explain_rejection(task, prize))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task_id, prize_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, task=task_id, prize=prize_id, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TASKS[params.task], PRIZES[params.prize], params.name, params.gender, [params.trait], params.helper)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: gasket, maneuver, transformation, reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--name")
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


ASP_RULES = r"""
task_at_risk(T, P) :- task(T), prize(P), zone(T, Z), slot(P, Z).
valid_fix(T, P, F) :- task_at_risk(T, P), fix(F), fits(F, T), covers(F, Z), slot(P, Z).
valid_story(Place, T, P) :- affords(Place, T), task_at_risk(T, P), valid_fix(T, P, _).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for t in sorted(setting.affords):
            lines.append(asp.fact("affords", place, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("zone", tid, "counter"))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("slot", pid, p.slot))
    for fid, f in FIXES:
        pass
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for t in sorted(fx.fits):
            lines.append(asp.fact("fits", fx.id, t))
        for c in sorted(fx.covers):
            lines.append(asp.fact("covers", fx.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import storyworlds.asp as asp
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
