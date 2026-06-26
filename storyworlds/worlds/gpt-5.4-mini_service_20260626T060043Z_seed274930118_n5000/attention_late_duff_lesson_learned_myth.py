#!/usr/bin/env python3
"""
storyworlds/worlds/attention_late_duff_lesson_learned_myth.py
==============================================================

A small mythic storyworld about attention, lateness, and duff.

Premise:
- A young hero must complete a sacred errand before the sky goes dark.
- If the hero is late or careless, the forest duff hides roots and stones,
  and the offering may be spoiled.
- An elder gives a warning. The hero learns to slow down, pay attention,
  and finish the task with care.

The domain is intentionally tiny and classical:
- typed entities with physical meters and emotional memes
- a forward-simulated world model
- a reasonableness gate that rejects weak combinations
- a matching inline ASP twin for parity checks
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from collections import defaultdict
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
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister", "priestess"}
        male = {"boy", "man", "father", "brother", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass(frozen=True)
class Setting:
    place: str
    dusk: bool
    affords: set[str]


@dataclass(frozen=True)
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    delay: str
    risk: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str]


@dataclass(frozen=True)
class Prize:
    id: str
    label: str
    phrase: str
    location: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass(frozen=True)
class Aid:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    offer: str
    ending: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.events: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.events = set(self.events)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _quietly_progress(world: World, actor: Entity, task: Task) -> None:
    actor.meters["purpose"] += 1
    actor.memes["resolve"] += 1
    actor.meters["late"] += 1 if world.setting.dusk else 0
    actor.meters["attention"] += 1
    world.trace.append(f"{actor.id} focuses on {task.id}")


def _duff_hides_trouble(world: World, actor: Entity, task: Task, prize: Entity) -> list[str]:
    out: list[str] = []
    if actor.meters["attention"] < THRESHOLD:
        return out
    if actor.meters["late"] < THRESHOLD:
        return out
    if prize.meters["dirty"] >= THRESHOLD:
        return out
    if task.id not in world.setting.affords:
        return out
    if prize.location not in task.zone:
        return out
    sig = ("duff", actor.id, task.id)
    if sig in world.events:
        return out
    world.events.add(sig)
    prize.meters["dirty"] += 1
    prize.meters["scuffed"] += 1
    out.append(f"The duff hid a root, and {prize.label} was scuffed.")
    return out


def _lesson_learned(world: World, hero: Entity) -> list[str]:
    out: list[str] = []
    if hero.meters["attention"] < THRESHOLD or hero.memes["lesson"] >= THRESHOLD:
        return out
    if hero.meters["late"] < THRESHOLD:
        return out
    sig = ("lesson", hero.id)
    if sig in world.events:
        return out
    world.events.add(sig)
    hero.memes["lesson"] += 1
    hero.memes["resolve"] += 1
    out.append(f"{hero.id} learned that attention was the quickest path through the dark.")
    return out


CAUSAL_RULES = [_duff_hides_trouble, _lesson_learned]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            for ent in world.characters():
                task = world.facts.get("task")
                prize = world.facts.get("prize")
                if not task or not prize:
                    continue
                sents = rule(world, ent, task, prize)
                if sents:
                    changed = True
                    produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(task: Task, prize: Prize) -> bool:
    return prize.location in task.zone


def select_aid(task: Task, prize: Prize) -> Optional[Aid]:
    for aid in AIDs:
        if task.mess in aid.guards and prize.location in aid.covers:
            return aid
    return None


def predict(world: World, hero: Entity, task: Task, prize_id: str) -> dict:
    sim = world.copy()
    sim_hero = sim.get(hero.id)
    sim_hero.meters["attention"] += 1
    sim_hero.meters["late"] += 1
    sim_hero.memes["resolve"] += 1
    sim.facts["task"] = task
    sim.facts["prize"] = sim.get(prize_id)
    propagate(sim, narrate=False)
    prize = sim.get(prize_id)
    return {
        "dirty": prize.meters["dirty"] >= THRESHOLD,
        "lesson": sim_hero.memes["lesson"] >= THRESHOLD,
    }


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved old songs and clear paths.")


def longing(world: World, hero: Entity, task: Task) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} loved {task.gerund}, because it felt like following a bright star."
    )


def omen(world: World) -> None:
    if world.setting.dusk:
        world.say("The sun dropped low, and the grove grew long and blue.")
    else:
        world.say("The grove was bright, but the old stones still asked for care.")


def warning(world: World, elder: Entity, hero: Entity, task: Task, prize: Prize) -> bool:
    pred = predict(world, hero, task, prize.id)
    if not pred["dirty"]:
        return False
    world.facts["predicted_dirty"] = True
    world.say(
        f'"Pay attention," {elder.pronoun("subject")} said. "If you rush now, '
        f"{prize.label} will get {task.risk} in the duff.""
    )
    return True


def late_step(world: World, hero: Entity, task: Task) -> None:
    hero.meters["late"] += 1
    world.say(f"But {hero.id} was late, and the path was already dim.")
    world.say(f"{hero.pronoun().capitalize()} tried to {task.rush},")
    hero.memes["defiance"] += 1


def touch_duff(world: World, hero: Entity, task: Task) -> None:
    hero.meters["attention"] += 1
    world.say(
        f"Then {hero.id} stopped, looked down, and paid attention to the brown duff underfoot."
    )
    world.say("There, the roots showed their crooked backs like old teeth.")


def accept_aid(world: World, elder: Entity, hero: Entity, task: Task, prize: Entity, aid: Aid) -> None:
    hero.memes["joy"] += 1
    hero.memes["defiance"] = 0.0
    world.say(
        f'{elder.pronoun("possessive").capitalize()} {elder.type} pointed to '
        f"{aid.label} and smiled. \"Use this first, and the path will be safe.\""
    )
    world.say(
        f"{hero.id} listened, used the {aid.label}, and finished {task.gerund} with care."
    )
    if prize.meters["dirty"] < THRESHOLD:
        world.say(f"{prize.label} stayed clean, and the grove kept its quiet glow.")
    else:
        world.say(f"{prize.label} was washed clean afterward, and the lesson stayed bright.")


def tell(setting: Setting, task: Task, prize_cfg: Prize, hero_name: str, hero_type: str, elder_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label="the elder"))
    prize = world.add(Entity(
        id=prize_cfg.id,
        type=prize_cfg.id,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=elder.id,
        location=prize_cfg.location,
        plural=prize_cfg.plural,
    ))
    world.facts["task"] = task
    world.facts["prize"] = prize

    intro(world, hero)
    longing(world, hero, task)
    world.say(f"{hero.id} carried {hero.pronoun('possessive')} {prize.label} toward the old shrine.")

    world.para()
    omen(world)
    warning(world, elder, hero, task, prize)
    late_step(world, hero, task)
    propagate(world, narrate=True)

    world.para()
    touch_duff(world, hero, task)
    aid = select_aid(task, prize)
    if aid:
        world.say(f"{elder.id} offered {aid.label}, a small kindness against the dark.")
        accept_aid(world, elder, hero, task, prize, aid)
        hero.memes["lesson"] += 1
    else:
        world.say("No fitting help was needed, for the path had already taught its own lesson.")

    world.facts.update(hero=hero, elder=elder, prize=prize, task=task, aid=aid)
    return world


SETTINGS = {
    "grove": Setting(place="the moonlit grove", dusk=True, affords={"torch", "offering"}),
    "shrine": Setting(place="the stone shrine", dusk=True, affords={"torch", "offering"}),
    "riverbank": Setting(place="the riverbank path", dusk=True, affords={"torch", "offering"}),
}

TASKS = {
    "torch": Task(
        id="torch",
        verb="carry the torch to the shrine",
        gerund="carrying the torch",
        rush="run to the shrine with the torch held high",
        delay="linger by the bright stones",
        risk="smudged",
        mess="dark",
        zone={"hands", "torso"},
        keyword="attention",
        tags={"attention", "late"},
    ),
    "offering": Task(
        id="offering",
        verb="bring the offering bowl",
        gerund="bringing the offering bowl",
        rush="hurry to the shrine with the bowl held out",
        delay="look back at the stars",
        risk="dirty",
        mess="mud",
        zone={"hands", "feet"},
        keyword="duff",
        tags={"duff", "attention"},
    ),
}

PRIZES = {
    "torch": Prize(id="torch", label="torch", phrase="a small bright torch", location="hands"),
    "bowl": Prize(id="bowl", label="bowl", phrase="a smooth offering bowl", location="hands"),
    "cloak": Prize(id="cloak", label="cloak", phrase="a ceremonial cloak", location="torso"),
}

AIDS = [
    Aid(id="sandals", label="worn sandals", covers={"feet"}, guards={"mud"}, offer="put on worn sandals", ending="walked more carefully", plural=True),
    Aid(id="lantern", label="a lantern", covers={"hands", "torso"}, guards={"dark"}, offer="lift a lantern", ending="followed the light", plural=False),
    Aid(id="staff", label="an old staff", covers={"hands"}, guards={"dark", "mud"}, offer="take the old staff", ending="leaned on the staff", plural=False),
]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            task = TASKS[task_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(task, prize) and select_aid(task, prize):
                    combos.append((place, task_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    name: str
    hero_type: str
    elder_type: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, task, prize = f["hero"], f["task"], f["prize"]
    return [
        f'Write a mythic short story for a child that includes the word "attention" and a late lesson learned.',
        f"Tell a gentle myth where {hero.id} tries to {task.verb} but learns to slow down before the duff hides trouble.",
        f'Write a story about a child, a sacred path, and the word "duff", ending with a clear lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, task, prize = f["hero"], f["elder"], f["task"], f["prize"]
    qa = [
        QAItem(
            question=f"What did {hero.id} try to do in the story?",
            answer=f"{hero.id} tried to {task.verb}.",
        ),
        QAItem(
            question=f"Why did the elder warn {hero.id} to pay attention?",
            answer=f"The elder warned {hero.id} because rushing could leave {prize.label} {task.risk} in the duff.",
        ),
        QAItem(
            question=f"What did {hero.id} learn by the end?",
            answer=f"{hero.id} learned that attention helps more than rushing, especially when the path is late and dark.",
        ),
    ]
    if f.get("aid"):
        aid = f["aid"]
        qa.append(
            QAItem(
                question=f"How did {aid.label} help {hero.id}?",
                answer=f"{aid.label} helped by giving {hero.id} a safer way to finish the task without harming {prize.label}.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is duff?",
            answer="Duff is the soft layer of dead leaves and little plant bits on a forest floor.",
        ),
        QAItem(
            question="What does attention mean?",
            answer="Attention means looking and listening carefully so you notice what is happening around you.",
        ),
        QAItem(
            question="Why can being late cause trouble?",
            answer="Being late can cause trouble because there may be less time to move carefully and make a wise choice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  events: {sorted(world.events)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="grove", task="torch", prize="cloak", name="Nera", hero_type="girl", elder_type="priestess"),
    StoryParams(place="shrine", task="offering", prize="bowl", name="Timo", hero_type="boy", elder_type="priest"),
    StoryParams(place="riverbank", task="torch", prize="torch", name="Lio", hero_type="boy", elder_type="priest"),
]


KNOWLEDGE_ORDER = ["attention", "late", "duff"]


def explain_rejection(task: Task, prize: Prize) -> str:
    if not prize_at_risk(task, prize):
        return f"(No story: {prize.label} is not at risk on the chosen path, so there is no honest warning or lesson.)"
    if not select_aid(task, prize):
        return f"(No story: the domain has no fitting aid for {prize.label} in this task, so the compromise would be weak.)"
    return "(No story: the requested combination is not reasonable.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: this prize is not typical for a {gender} here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(T, P) :- task(T), prize(P), zone(T, R), at(P, R).
has_aid(T, P) :- task(T), prize(P), prize_at_risk(T, P), task_mess(T, M), guards(G, M), covers(G, R), at(P, R).
valid(Place, T, P) :- setting(Place), affords(Place, T), prize_at_risk(T, P), has_aid(T, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.dusk:
            lines.append(asp.fact("dusk", sid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", sid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("task_mess", tid, t.mess))
        for r in sorted(t.zone):
            lines.append(asp.fact("zone", tid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("at", pid, p.location))
        if p.plural:
            lines.append(asp.fact("plural", pid))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid.id))
        for c in sorted(aid.covers):
            lines.append(asp.fact("covers", aid.id, c))
        for g in sorted(aid.guards):
            lines.append(asp.fact("guards", aid.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic lesson-learned storyworld about attention, late, and duff.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=["priest", "priestess"])
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
        if not (prize_at_risk(task, prize) and select_aid(task, prize)):
            raise StoryError(explain_rejection(task, prize))
    if args.gender and args.hero_type and args.gender != args.hero_type:
        raise StoryError("(No story: the requested gender and hero type do not match.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_type = args.hero_type or gender
    name = args.name or rng.choice(["Nera", "Timo", "Lio", "Mara", "Soren"])
    elder_type = args.elder_type or rng.choice(["priest", "priestess"])
    return StoryParams(place=place, task=task, prize=prize, name=name, hero_type=hero_type, elder_type=elder_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TASKS[params.task], PRIZES[params.prize], params.name, params.hero_type, params.elder_type)
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
        print(f"{len(triples)} compatible (place, task, prize) combos:\n")
        for place, task, prize in triples:
            print(f"  {place:10} {task:10} {prize:10}")
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
            header = f"### {p.name}: {p.task} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
