#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T021641Z_seed1855084837_n10/award_patty_dialogue_teamwork_rhyming_story.py
==========================================================================================================================

A small standalone storyworld for a rhyming, dialogue-driven teamwork tale
about making a patty for an award.

Premise:
- A child and helper want to win a small award at a kitchen-table fair.
- They need to make a patty that is round, cooked, and neat.
- Teamwork matters: one stirs, one shapes, one watches the timer.
- Dialogue carries the beats, and the story ends with a rhyming celebration.

The world simulates physical meters and emotional memes:
- Physical: batter, heat, shape, mess, doneness, award_ready
- Emotional: hope, worry, pride, teamwork, joy

The prose is state-driven. A failed patty can be too messy or too raw; a
successful one becomes golden and ready for the award table.

Supported CLI:
- default run
- -n
- --all
- --seed
- --trace
- --qa
- --json
- --asp
- --verify
- --show-asp
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
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    light: str
    supports_dialogue: bool = True
    supports_teamwork: bool = True


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    mess_desc: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    award_phrase: str
    needed: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.turn: str = "start"

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.turn = self.turn
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["mixing"] < THRESHOLD:
            continue
        sig = ("mess", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["mess"] += 1
        actor.meters["batter"] += 1
        out.append(f"{actor.label_word.capitalize()} got a dab of batter on {actor} fingertips.")
    return out


def _r_award_ready(world: World) -> list[str]:
    out: list[str] = []
    for prize in [e for e in world.entities.values() if e.type == "patty"]:
        if prize.meters["shape"] >= THRESHOLD and prize.meters["doneness"] >= THRESHOLD and prize.meters["mess"] < 2:
            sig = ("award_ready", prize.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            prize.meters["award_ready"] = 1
            out.append("The patty looked ready for the award table.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("shared_job") and world.facts.get("shared_job_done") and not world.facts.get("teamwork_narrated"):
        world.facts["teamwork_narrated"] = True
        for kid in world.characters():
            kid.memes["teamwork"] += 1
            kid.memes["pride"] += 1
        out.append("The helpers smiled because they had worked as one.")
    return out


CAUSAL_RULES = [
    Rule("mess", "physical", _r_mess),
    Rule("award_ready", "physical", _r_award_ready),
    Rule("teamwork", "social", _r_teamwork),
]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for tid, task in TASKS.items():
            for pid, prize in PRIZES.items():
                if prize.id in {"award_patty"} and task.id in {"flip", "shape"} and setting.supports_dialogue and setting.supports_teamwork:
                    combos.append((sid, tid, pid))
    return combos


def choose_tool(task: Task, prize: Prize) -> Tool:
    for tool in TOOLS.values():
        if task.id in tool.helps and prize.id == "award_patty":
            return tool
    raise StoryError("No sensible tool exists for this story.")


@dataclass
class StoryParams:
    setting: str
    task: str
    prize: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    tool: str = "spatula"
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting("kitchen", "the little kitchen", "sunlight on the tile"),
    "barn": Setting("barn", "the cozy barn", "warm light by the door"),
    "fair": Setting("fair", "the school fair", "bright paper lanterns"),
}

TASKS = {
    "shape": Task("shape", "shape the patty", "shaping the patty", "scoot to the pan", "sticky", "sticky and soft", {"shape"}),
    "flip": Task("flip", "flip the patty", "flipping the patty", "flip too soon", "raw", "raw and runny", {"heat"}),
}

PRIZES = {
    "award_patty": Prize("award_patty", "award patty", "the award patty", "the blue-ribbon award", {"shape", "heat"}, {"award", "patty"}),
}

TOOLS = {
    "spatula": Tool("spatula", "spatula", "a little spatula", {"shape", "heat"}, {"tool"}),
    "timer": Tool("timer", "timer", "a tiny timer", {"heat"}, {"tool"}),
    "bowl": Tool("bowl", "bowl", "a big bowl", {"shape"}, {"tool"}),
}

GIRL_NAMES = ["Mia", "Lina", "Tess", "Nora", "Ruby"]
BOY_NAMES = ["Ben", "Owen", "Eli", "Theo", "Finn"]


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming teamwork storyworld about an award patty.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--tool", choices=TOOLS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.task is None or c[1] == args.task)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, prize = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" and rng.random() < 0.5 else "girl")
    hero = args.hero or _pick_name(rng, hero_gender)
    helper = args.helper or _pick_name(rng, helper_gender)
    if helper == hero:
        helper = _pick_name(rng, "boy" if helper_gender == "boy" else "girl")
    tool = args.tool or rng.choice(sorted(TOOLS))
    return StoryParams(setting=setting, task=task, prize=prize, hero=hero, hero_gender=hero_gender,
                       helper=helper, helper_gender=helper_gender, tool=tool)


def _intro(world: World, hero: Entity, helper: Entity, task: Task, prize: Prize) -> None:
    world.say(f"{hero.id} said, \"Let's make it nice and neat.\"")
    world.say(f"{helper.id} said, \"Teamwork makes the dream sweet.\"")
    world.say(f"They wanted to {task.verb} for the {prize.award_phrase}, with a happy beat.")


def _work(world: World, hero: Entity, helper: Entity, task: Task, tool: Tool, prize: Prize) -> None:
    hero.meters["mixing"] += 1
    helper.meters["mixing"] += 1
    hero.memes["hope"] += 1
    helper.memes["hope"] += 1
    world.facts["shared_job"] = True
    world.facts["shared_job_done"] = True
    world.say(f"{hero.id} said, \"Pass me {tool.phrase}, and I'll start to stir.\"")
    world.say(f"{helper.id} said, \"I will watch the pan, so nothing will blur.\"")
    if task.id == "shape":
        prize.meters["shape"] += 1
        prize.meters["mess"] += 0.5
        world.say(f"They shaped the {prize.label} with care, so round and clear.")
    else:
        prize.meters["shape"] += 0.5
        prize.meters["doneness"] += 1
        world.say(f"They flipped the {prize.label} together, with rhythm and cheer.")
    propagate(world)


def _finish(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    if prize.meters["award_ready"] >= THRESHOLD:
        hero.memes["joy"] += 1
        helper.memes["joy"] += 1
        world.say(f"The judge came by and gave the prize a gleam.")
        world.say(f"\"That patty wins the award!\" they said, and the room felt like a dream.")
        world.say(f"{hero.id} and {helper.id} grinned wide, proud of their teamwork scene.")
        world.say(f"The award patty shone like sunshine, tidy and golden and keen.")
    else:
        hero.memes["worry"] += 1
        helper.memes["worry"] += 1
        world.say(f"The patty was still too messy or raw, so they tried once more.")
        world.say(f"With one more turn and one more grin, they worked beside the stove.")
        prize.meters["shape"] += 1
        prize.meters["doneness"] += 1
        prize.meters["mess"] = 1
        propagate(world)
        if prize.meters["award_ready"] >= THRESHOLD:
            world.say(f"At last it was ready, a tidy patty to adore.")
            world.say(f"The judge smiled, and the award was theirs for sure.")


def tell(setting: Setting, task: Task, prize_cfg: Prize, hero_name: str, hero_gender: str,
         helper_name: str, helper_gender: str, tool: Tool) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, label=helper_name))
    prize = world.add(Entity(id=prize_cfg.id, type="patty", label=prize_cfg.label))
    world.facts["setting"] = setting
    world.facts["task"] = task
    world.facts["prize"] = prize_cfg
    world.facts["tool"] = tool
    _intro(world, hero, helper, task, prize)
    world.para()
    _work(world, hero, helper, task, tool, prize)
    world.para()
    _finish(world, hero, helper, prize)
    world.facts.update(hero=hero, helper=helper, prize_ent=prize)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a child about {f["hero"].id} and {f["helper"].id} working together to make an award patty.',
        f'Tell a teamwork story with dialogue where {f["hero"].id} says a line, {f["helper"].id} answers, and the award patty turns out right.',
        f'Write a gentle rhyming story that includes the words "award" and "patty" and ends with a happy prize.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    prize_ent: Entity = f["prize_ent"]
    task: Task = f["task"]
    prize: Prize = f["prize"]
    qa = [
        QAItem(
            question=f"What were {hero.id} and {helper.id} trying to make?",
            answer=f"They were trying to make {prize.phrase} for {prize.award_phrase}. They worked together so the patty could be neat and ready.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} work as a team?",
            answer=f"{hero.id} helped with the making, and {helper.id} helped watch and guide the job. They used dialogue to share the work instead of doing it alone.",
        ),
        QAItem(
            question=f"Why did the patty need both shape and heat?",
            answer=f"It needed shape to look like a proper patty, and it needed heat to finish cooking. When both were in place, it could win the award.",
        ),
    ]
    if prize_ent.meters["award_ready"] >= THRESHOLD:
        qa.append(QAItem(
            question=f"What happened at the end with the award patty?",
            answer=f"The patty was ready and the judge gave it the award. The final image was a tidy, golden patty that showed the team had done it right.",
        ))
    else:
        qa.append(QAItem(
            question=f"What happened when the patty was not ready yet?",
            answer=f"They noticed it was still messy or raw and worked again together. That extra teamwork helped turn it into something ready for the award table.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and share the work so the job can be done well.",
        ),
        QAItem(
            question="What is an award?",
            answer="An award is something given to show that a person or thing did a very good job.",
        ),
        QAItem(
            question="What is a patty?",
            answer="A patty is a small flat cake or patty-shaped food that is usually shaped by hand and cooked.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
chosen_setting(S) :- setting(S).
chosen_task(T) :- task(T).
chosen_prize(P) :- prize(P).
valid(S,T,P) :- setting(S), task(T), prize(P), supports_dialogue(S), supports_teamwork(S), task_works(T), prize_needs(P,T).
award_ready(P) :- shape(P), heat(P), neat(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.supports_dialogue:
            lines.append(asp.fact("supports_dialogue", sid))
        if s.supports_teamwork:
            lines.append(asp.fact("supports_teamwork", sid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("task_works", tid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_needs", pid, "shape"))
        lines.append(asp.fact("prize_needs", pid, "heat"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos disagree.")
        rc = 1
    try:
        p = StoryParams(
            setting="kitchen",
            task="shape",
            prize="award_patty",
            hero="Mia",
            hero_gender="girl",
            helper="Ben",
            helper_gender="boy",
            tool="spatula",
            seed=1,
        )
        sample = generate(p)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="verify-smoke")
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generate/emit smoke test passed.")
    return rc


def build_valid_combo_filter(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    return [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.task is None or c[1] == args.task)
        and (args.prize is None or c[2] == args.prize)
    ]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = build_valid_combo_filter(args)
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, prize = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or ("Mia" if hero_gender == "girl" else "Ben")
    helper = args.helper or ("Owen" if helper_gender == "boy" else "Lina")
    tool = args.tool or "spatula"
    return StoryParams(
        setting=setting,
        task=task,
        prize=prize,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        tool=tool,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.task not in TASKS or params.prize not in PRIZES or params.tool not in TOOLS:
        raise StoryError("Invalid story parameters.")
    world = tell(
        SETTINGS[params.setting],
        TASKS[params.task],
        PRIZES[params.prize],
        params.hero,
        params.hero_gender,
        params.helper,
        params.helper_gender,
        TOOLS[params.tool],
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(setting="kitchen", task="shape", prize="award_patty", hero="Mia", hero_gender="girl", helper="Ben", helper_gender="boy", tool="spatula"),
    StoryParams(setting="barn", task="shape", prize="award_patty", hero="Theo", hero_gender="boy", helper="Lina", helper_gender="girl", tool="bowl"),
    StoryParams(setting="fair", task="flip", prize="award_patty", hero="Ruby", hero_gender="girl", helper="Finn", helper_gender="boy", tool="timer"),
]


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
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
