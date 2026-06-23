#!/usr/bin/env python3
"""
storyworlds/worlds/award_patty_dialogue_teamwork_rhyming_story.py
=================================================================

A tiny storyworld about teamwork in the kitchen: two children make a patty,
work together, and hope to win an award at the school fair. The prose is kept
child-facing and lightly rhyming, with dialogue and a state-driven turn.

The simulated domain is intentionally small:
- a shared cooking task
- a patty that can be prepared well or poorly
- an award at the end of the day
- teamwork beats rushing, and the ending image proves what changed

The script follows the storyworld contract:
- standalone stdlib script
- imports storyworlds/results.py eagerly
- lazy ASP helper import
- StoryParams, build_parser, resolve_params, generate, emit, main
- support for --seed, -n, --all, --trace, --qa, --json, --asp, --verify, --show-asp
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

# Robust import path setup: walk upward until we find storyworlds/results.py.
HERE = os.path.abspath(os.path.dirname(__file__))
CUR = HERE
RESULTS_DIR = None
while True:
    candidate = os.path.join(CUR, "results.py")
    if os.path.exists(candidate):
        RESULTS_DIR = CUR
        break
    parent = os.path.dirname(CUR)
    if parent == CUR:
        break
    CUR = parent

if RESULTS_DIR is None:
    # Fallback for repo layout under storyworlds/worlds/*
    RESULTS_DIR = os.path.dirname(os.path.dirname(HERE))

if RESULTS_DIR not in sys.path:
    sys.path.insert(0, RESULTS_DIR)

from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    location: str = ""
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mood: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    action: str
    teamwork_line: str
    risk: str
    reward: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Award:
    id: str
    label: str
    phrase: str
    reason: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
        import copy
        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


@dataclass
class StoryParams:
    setting: str
    task: str
    award: str
    hero: str
    helper: str
    hero_gender: str = "girl"
    helper_gender: str = "boy"
    parent: str = "mother"
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen", mood="warm", afford={"mix"}),
    "fair": Setting(place="the school fair", mood="bright", afford={"carry"}),
    "garden": Setting(place="the garden", mood="green", afford={"mix"}),
}

TASKS = {
    "mix": Task(
        id="mix",
        action="mix the batter for a patty",
        teamwork_line="one stirred while the other held the bowl",
        risk="the batter could spill and make a mess",
        reward="a neat patty for the contest",
        tags={"patty", "teamwork", "kitchen"},
    ),
    "shape": Task(
        id="shape",
        action="shape the patty carefully",
        teamwork_line="one shaped the patty while the other flaked the crumbs",
        risk="it could crack apart if rushed",
        reward="a round patty that looked just right",
        tags={"patty", "teamwork", "fair"},
    ),
    "cook": Task(
        id="cook",
        action="cook the patty on the pan",
        teamwork_line="one watched the pan while the other fanned the steam",
        risk="it could burn if nobody watched",
        reward="a golden patty with a happy smell",
        tags={"patty", "teamwork", "kitchen"},
    ),
}

AWARDS = {
    "blue_ribbon": Award(
        id="blue_ribbon",
        label="a blue ribbon award",
        phrase="a blue ribbon",
        reason="for careful teamwork and a tidy patty",
        tags={"award"},
    ),
    "gold_sticker": Award(
        id="gold_sticker",
        label="a gold sticker award",
        phrase="a gold sticker",
        reason="for a smart plan and a shining patty",
        tags={"award"},
    ),
    "star_medal": Award(
        id="star_medal",
        label="a star medal award",
        phrase="a star medal",
        reason="for kind teamwork and a patty made with care",
        tags={"award"},
    ),
}

GIRL_NAMES = ["Luna", "Mia", "Zoe", "Nina", "Ava", "Ella", "Ruby", "Ivy"]
BOY_NAMES = ["Noah", "Leo", "Ben", "Max", "Finn", "Theo", "Sam", "Owen"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, t, a) for s in SETTINGS for t in TASKS for a in AWARDS]


def explain_rejection(setting: str, task: str) -> str:
    if task not in TASKS:
        return "(No story: that task is not in this world.)"
    return f"(No story: {TASKS[task].action} does not fit {SETTINGS[setting].place} well enough.)"


def rhyme_end(word: str) -> str:
    return {
        "mix": "stick",
        "shape": "grape",
        "cook": "book",
        "award": "yard",
        "patty": "chatty",
    }.get(word, word)


def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type="mother" if params.parent == "mother" else "father", label="the parent"))
    task = TASKS[params.task]
    award = AWARDS[params.award]
    pan = world.add(Entity(id="pan", type="thing", label="the pan", tags={"pan"}))
    bowl = world.add(Entity(id="bowl", type="thing", label="the bowl", tags={"bowl"}))
    patty = world.add(Entity(id="patty", type="thing", label="the patty", tags={"patty"}, plural=False))
    ribbon = world.add(Entity(id="award", type="thing", label=award.label, tags={"award"}))
    world.facts.update(hero=hero, helper=helper, parent=parent, task=task, award=award, pan=pan, bowl=bowl, patty=patty, ribbon=ribbon)
    return world


def tell(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    parent: Entity = f["parent"]
    task: Task = f["task"]
    award: Award = f["award"]
    patty: Entity = f["patty"]

    hero.memes["joy"] += 1
    helper.memes["joy"] += 1

    world.say(f"At {world.setting.place}, {hero.id} and {helper.id} began with a grin, and the day felt warm and bright.")
    world.say(f"'{task.action}!' said {hero.id}. '{task.teamwork_line}, and that is how we win!'")
    world.say(f"'{task.risk},' said {helper.id}, 'so let's slow down and make it right, my friend.'")
    world.say("They worked with care, and the room was sweet with hope and light.")

    world.para()
    if task.id == "mix":
        patty.meters["mixed"] += 1
        patty.meters["mess"] += 0
        helper.memes["trust"] += 1
        world.say(f"{hero.id} stirred the bowl while {helper.id} held it tight.")
        world.say("The batter stayed in the bowl, and not a drop took flight.")
    elif task.id == "shape":
        patty.meters["shaped"] += 1
        hero.memes["pride"] += 1
        helper.memes["care"] += 1
        world.say(f"{helper.id} shaped the patty round while {hero.id} brushed the edge so neat.")
        world.say("It looked like a little moon, so tidy, trim, and sweet.")
    else:
        patty.meters["cooked"] += 1
        patty.meters["golden"] += 1
        helper.memes["focus"] += 1
        world.say(f"{hero.id} watched the pan, and {helper.id} fanned the steam away.")
        world.say("The patty turned a golden brown and did not burn that day.")

    world.para()
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    hero.meters["work"] += 1
    helper.meters["work"] += 1
    world.say("At the school fair, the judge came by and gave a smile so wide.")
    world.say(f"'{award.phrase} for your teamwork,' the judge said with pride.")
    world.say(f"{hero.id} and {helper.id} bowed low, then shared a happy cheer.")
    world.say("'We did it together!' they laughed, because teamwork brought the prize near.")
    world.say(f"So side by side they held the {patty.label}, and the award shone like a star in the yard.")
    world.say("They went home with bright cheeks and the lesson that sharing work can be hard, but sweetly rewarding, and not too hard.")
    world.facts["won"] = True
    world.facts["ending_rhyme"] = rhyme_end(task.id)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    task: Task = f["task"]
    award: Award = f["award"]
    return [
        f'Write a rhyming story for a young child about {hero.id} and {helper.id} working together to {task.action}, and include the words "award" and "patty".',
        f"Tell a gentle dialogue story where {hero.id} and {helper.id} share the job, make a patty, and hope for {award.phrase}.",
        'Write a teamwork story with a simple rhyme, a patty, and an award at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    task: Task = f["task"]
    award: Award = f["award"]
    qa = [
        QAItem(
            question="Who worked together in the story?",
            answer=f"{hero.id} and {helper.id} worked together as a team. They shared the job and kept the patty moving from start to finish.",
        ),
        QAItem(
            question="What did they make with teamwork?",
            answer="They made a patty. They were careful, and that teamwork helped the patty turn out well.",
        ),
        QAItem(
            question="What did the judge give them at the school fair?",
            answer=f"The judge gave them {award.phrase}. They earned it because they worked together and kept the patty neat.",
        ),
    ]
    if task.id == "mix":
        qa.append(QAItem(
            question="Why did one child hold the bowl while the other stirred?",
            answer="Because mixing can spill if nobody helps. Holding the bowl kept the batter safe, and that made the patty easier to finish.",
        ))
    elif task.id == "shape":
        qa.append(QAItem(
            question="How did they keep the patty from cracking?",
            answer="They went slowly and shared the work. One shaped it while the other watched the edges, so the patty stayed round.",
        ))
    else:
        qa.append(QAItem(
            question="How did they keep the patty from burning?",
            answer="They watched the pan together. One fanned the steam away while the other looked after the heat, so the patty stayed golden.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and do a job together. It can make hard jobs feel easier and kinder.",
        ),
        QAItem(
            question="What is an award?",
            answer="An award is a prize or special sign that shows someone did a good job. People often earn awards for care, skill, or kindness.",
        ),
        QAItem(
            question="What is a patty?",
            answer="A patty is a small round piece of food that can be cooked in a pan. It can be made from many ingredients and shaped by hand.",
        ),
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
task_ok(S,T,A) :- setting(S), task(T), award(A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TASKS:
        lines.append(asp.fact("task", t))
    for a in AWARDS:
        lines.append(asp.fact("award", a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show task_ok/3."))
    return sorted(set(asp.atoms(model, "task_ok")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    rc = 0
    if py != asp_set:
        rc = 1
        print("MISMATCH in valid_combos:")
        print("python only:", sorted(py - asp_set))
        print("asp only:", sorted(asp_set - py))
    else:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, task=None, award=None, hero=None, helper=None, hero_gender=None, helper_gender=None, parent=None, seed=None), random.Random(777)))
        _ = sample.story
        print("OK: smoke-test generation completed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming teamwork storyworld about a patty and an award.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--award", choices=AWARDS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", "--n", type=int, default=1)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    task = args.task or rng.choice(list(TASKS))
    if setting not in SETTINGS or task not in TASKS:
        raise StoryError("Invalid setting or task.")
    award = args.award or rng.choice(list(AWARDS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_pool = [n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != hero]
    helper = args.helper or rng.choice(helper_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting,
        task=task,
        award=award,
        hero=hero,
        helper=helper,
        hero_gender=hero_gender,
        helper_gender=helper_gender,
        parent=parent,
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.task not in TASKS or params.award not in AWARDS:
        raise StoryError("Invalid story parameters.")
    world = setup_world(params)
    tell(world)
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
        print(asp_program("#show task_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="kitchen", task="mix", award="blue_ribbon", hero="Mia", helper="Ben", hero_gender="girl", helper_gender="boy", parent="mother"),
            StoryParams(setting="fair", task="shape", award="gold_sticker", hero="Luna", helper="Noah", hero_gender="girl", helper_gender="boy", parent="father"),
            StoryParams(setting="garden", task="cook", award="star_medal", hero="Zoe", helper="Finn", hero_gender="girl", helper_gender="boy", parent="mother"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        payload = [s.to_dict() for s in samples]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
