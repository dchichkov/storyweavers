#!/usr/bin/env python3
"""
A small slice-of-life story world about teamwork, a puffer jacket, and a child
practicing a recitation.

Seed tale:
---
On a cool afternoon, Maya had to recite a short poem at the neighborhood center.
She was excited, but when she put on her new puffer jacket, the sleeves felt a
little too puffy for her paper cards. Her older brother Theo noticed her worrying
and helped by holding the cards, counting the lines, and practicing with her.

Together they moved to the front porch, took turns reading each line, and clapped
on the pauses. When it was time to go, Maya recited the poem without stumbling.
She smiled in her puffer jacket, and Theo smiled too, because helping each other
had made the whole thing easier.

This script turns that premise into a tiny simulated domain: a child wants to
recite, a puffer jacket gets in the way of handling notes, and teamwork resolves
the snag.
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
    held_by: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("mess", "care", "tidy", "practice"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "nerves", "confidence", "teamwork", "frustration"):
            self.memes.setdefault(k, 0.0)

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
    place: str = "the porch"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    struggle: str
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


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

    def characters(self) -> list[Entity]:
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def _r_practice(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["practice"] < THRESHOLD:
            continue
        sig = ("practice", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["confidence"] += 1
        out.append(f"{actor.id} felt a little steadier after another round of practice.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    notes = world.entities.get("notes")
    if not child or not helper or not notes:
        return out
    if child.memes["teamwork"] < THRESHOLD or helper.memes["teamwork"] < THRESHOLD:
        return out
    if notes.held_by == helper.id and notes.meters["care"] >= THRESHOLD:
        sig = ("teamwork",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["frustration"] = 0.0
        child.memes["joy"] += 1
        helper.memes["joy"] += 1
        out.append("The practice felt easier when they worked together.")
    return out


CAUSAL_RULES: list[tuple[str, Callable[[World], list[str]]]] = [
    ("practice", _r_practice),
    ("teamwork", _r_teamwork),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def risk_from_puffer(task: Task, prize: Prize) -> bool:
    return prize.region in {"hands", "torso"} and task.id == "recite"


def select_gear(task: Task, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if task.id in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_snag(world: World, actor: Entity, task: Task, prize_id: str) -> dict:
    sim = world.copy()
    _do_task(sim, sim.get(actor.id), task, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "messy": bool(prize.meters["care"] < THRESHOLD and sim.get("notes").held_by is None),
        "confidence": sim.get(actor.id).memes["confidence"],
    }


def _do_task(world: World, actor: Entity, task: Task, narrate: bool = True) -> None:
    if task.id not in world.setting.affords:
        return
    actor.meters["practice"] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, child: Entity) -> None:
    trait = next((t for t in child.traits if t != "little"), "quiet")
    world.say(f"{child.id} was a little {trait} {child.type} who loved a calm afternoon routine.")


def desire(world: World, child: Entity, task: Task) -> None:
    child.memes["nerves"] += 1
    world.say(f"{child.id} wanted to {task.verb}, but the words still felt wobbly.")


def puffer_detail(world: World, child: Entity, prize: Entity) -> None:
    child.worn_by = child.id
    world.say(f"{child.id} wore {child.pronoun('possessive')} {prize.label} and held the pages close.")


def warning(world: World, helper: Entity, child: Entity, task: Task, prize: Entity) -> bool:
    pred = predict_snag(world, child, task, prize.id)
    if not pred["messy"]:
        return False
    world.facts["predicted_confidence"] = pred["confidence"]
    world.say(
        f'"If you try to {task.verb} with those notes by yourself, they might slide around," '
        f"{helper.id} said. \"Let's do it together.\""
    )
    return True


def worry(world: World, child: Entity, task: Task) -> None:
    child.memes["frustration"] += 1
    world.say(f"{child.id} frowned and tried to sort the lines again.")
    world.say(f"{child.pronoun().capitalize()} even tried to {task.struggle}.")


def teamwork_offer(world: World, helper: Entity, child: Entity, task: Task, prize: Entity) -> Optional[Gear]:
    gear = select_gear(task, prize)
    if gear is None:
        return None
    g = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=child.id,
        caretaker=helper.id,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
    ))
    g.worn_by = helper.id
    child.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    world.say(
        f"{helper.id} smiled and offered a simple plan: {gear.prep}. "
        f"That way {child.id} could keep {prize.it()} safe while practicing."
    )
    return gear


def accept(world: World, child: Entity, helper: Entity, task: Task, prize: Entity, gear: Gear) -> None:
    child.memes["frustration"] = 0.0
    child.memes["confidence"] += 1
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{child.id}'s face brightened, and {child.pronoun()} nodded. "
        f"Together they {gear.tail}. "
        f"By the end, {child.id} was {task.gerund}, {prize.label} stayed neat, "
        f"and the whole porch felt peaceful."
    )


def tell(setting: Setting, task: Task, prize_cfg: Prize, hero_name: str, hero_type: str,
         hero_traits: Optional[list[str]] = None, helper_name: str = "Theo", helper_type: str = "boy") -> World:
    world = World(setting)
    child = world.add(Entity(
        id="child", kind="character", type=hero_type, label=hero_name,
        traits=["little"] + (hero_traits or ["careful", "gentle"])
    ))
    helper = world.add(Entity(
        id="helper", kind="character", type=helper_type, label=helper_name,
        traits=["steady", "kind"]
    ))
    prize = world.add(Entity(
        id="notes", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=child.id, caretaker=helper.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))

    introduce(world, child)
    world.say(f"{child.id} had to {task.verb} for the neighborhood gathering.")
    puffer_detail(world, child, prize)

    world.para()
    desire(world, child, task)
    warning(world, helper, child, task, prize)
    worry(world, child, task)

    world.para()
    gear = teamwork_offer(world, helper, child, task, prize)
    if gear:
        accept(world, child, helper, task, prize, gear)

    world.facts.update(child=child, helper=helper, prize=prize, task=task, setting=setting, gear=gear)
    return world


SETTINGS = {
    "porch": Setting(place="the porch", indoor=False, affords={"recite"}),
    "kitchen": Setting(place="the kitchen table", indoor=True, affords={"recite"}),
    "living_room": Setting(place="the living room", indoor=True, affords={"recite"}),
}

TASKS = {
    "recite": Task(
        id="recite",
        verb="recite a short poem",
        gerund="reciting the poem",
        struggle="say the lines without peeking",
        keyword="recite",
        tags={"recite", "teamwork", "home"},
    ),
}

PRIZES = {
    "puffer": Prize(
        label="puffer jacket",
        phrase="a soft blue puffer jacket",
        type="jacket",
        region="hands",
        genders={"girl", "boy"},
    ),
    "cards": Prize(
        label="index cards",
        phrase="a small stack of index cards",
        type="cards",
        region="hands",
        plural=True,
        genders={"girl", "boy"},
    ),
}

GEAR = [
    Gear(
        id="clip",
        label="a little binder clip",
        covers={"hands"},
        guards={"recite"},
        prep="clip the cards together first",
        tail="used the binder clip to keep the cards neat",
    ),
    Gear(
        id="stand",
        label="a tiny card stand",
        covers={"hands"},
        guards={"recite"},
        prep="set the cards on a tiny stand",
        tail="moved the cards onto the tiny stand",
    ),
]

GIRL_NAMES = ["Maya", "Ivy", "Luna", "Nina", "Sara"]
BOY_NAMES = ["Theo", "Owen", "Eli", "Noah", "Finn"]
TRAITS = ["shy", "thoughtful", "bright", "careful", "restless"]


@dataclass
class StoryParams:
    setting: str
    task: str
    prize: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s, setting in SETTINGS.items():
        for t in setting.affords:
            task = TASKS[t]
            for p, prize in PRIZES.items():
                if risk_from_puffer(task, prize) and select_gear(task, prize):
                    out.append((s, t, p))
    return out


KNOWLEDGE = {
    "puffer": [("What is a puffer jacket?", "A puffer jacket is a warm coat with soft, squishy padding inside.")],
    "recite": [("What does it mean to recite?", "To recite means to say words aloud from memory, like a poem or a pledge.")],
    "teamwork": [("What is teamwork?", "Teamwork means people help each other and do a job together.")],
}

KNOWLEDGE_ORDER = ["puffer", "recite", "teamwork"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle slice-of-life story that includes the words "{f["prize"].label}" and "recite".',
        f"Tell a small story about {f['child'].label} and {f['helper'].label} working together so {f['child'].label} can {f['task'].verb}.",
        f"Write a calm story where a child in a {f['prize'].label} gets help from a family member and finishes a recitation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, prize, task = f["child"], f["helper"], f["prize"], f["task"]
    qa = [
        QAItem(
            question=f"Who wanted to {task.verb} in the story?",
            answer=f"{child.label} wanted to {task.verb}, and {helper.label} helped make it easier.",
        ),
        QAItem(
            question=f"What was {child.label} wearing while getting ready?",
            answer=f"{child.label} was wearing {prize.phrase}. It was a puffer jacket, so it made the notes a little awkward to hold.",
        ),
        QAItem(
            question=f"How did {helper.label} help {child.label}?",
            answer=f"{helper.label} helped by making a simple teamwork plan and holding the cards steady.",
        ),
    ]
    if f.get("gear") is not None:
        gear = f["gear"]
        qa.append(
            QAItem(
                question=f"What did they use to keep the notes neat?",
                answer=f"They used {gear.label} so the cards stayed neat while {child.label} practiced.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["task"].tags)
    if world.facts.get("gear"):
        tags.add("teamwork")
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(task: Task, prize: Prize) -> str:
    return "(No story: this combination does not create a real snag that teamwork can solve.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} here is not configured for {gender}; try --gender {ok}.)"


ASP_RULES = r"""
risk(task(recite), prize(P)) :- prize_region(P,hands).
has_fix(task(recite), prize(P)) :- gear(G), gear_guards(G,recite), gear_covers(G,hands), prize(P).
valid(Setting,Task,Prize) :- setting_affords(Setting,Task), risk(task(Task), prize(Prize)), has_fix(task(Task), prize(Prize)).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for t in sorted(s.affords):
            lines.append(asp.fact("setting_affords", sid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("gear_covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("gear_guards", g.id, m))
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
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about teamwork, a puffer jacket, and reciting.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if args.task and args.prize:
        task, prize = TASKS[args.task], PRIZES[args.prize]
        if not (risk_from_puffer(task, prize) and select_gear(task, prize)):
            raise StoryError(explain_rejection(task, prize))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.task is None or c[1] == args.task)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(BOY_NAMES if gender == "girl" else GIRL_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, task=task, prize=prize, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TASKS[params.task], PRIZES[params.prize],
                 params.name, params.gender, [params.trait], params.helper)
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

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(setting="porch", task="recite", prize="puffer", name="Maya", gender="girl", helper="Theo", trait="thoughtful"),
            StoryParams(setting="living_room", task="recite", prize="cards", name="Noah", gender="boy", helper="Ivy", trait="careful"),
        ]
        samples = [generate(p) for p in curated]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.task} with {p.prize} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
