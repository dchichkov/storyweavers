#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/glorify_salon_happy_ending_teamwork_bedtime_story.py
====================================================================================

A small standalone storyworld for a bedtime-style tale about a family salon,
teamwork, and a happy ending. The world centers on a child helping in a salon
after closing time, a tiny mistake with a display, and a calm team fix that ends
with a glowing, cozy final image.

The seed words are intentionally woven into the world:
- "glorify" appears in the story as a child's song / praise for kind work
- "salon" is the main setting

The story aims for a bedtime-story tone: soft, concrete, gentle, and complete.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
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
class SalonSetting:
    id: str
    place: str
    closing: str
    glow: str
    room_word: str


@dataclass
class Task:
    id: str
    label: str
    verb: str
    tool: str
    result: str
    mess: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    action: str
    outcome: str
    power: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: SalonSetting) -> None:
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    setting: str
    task: str
    fix: str
    child: str
    child_gender: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "salon": SalonSetting(
        id="salon",
        place="the salon",
        closing="the chairs were lined up like sleepy turtles",
        glow="the mirror lamps glowed like little moons",
        room_word="room",
    ),
    "home_salon": SalonSetting(
        id="home_salon",
        place="the little home salon",
        closing="the combs were put away and the floor was swept smooth",
        glow="the lamp made the room look warm and soft",
        room_word="room",
    ),
    "corner_salon": SalonSetting(
        id="corner_salon",
        place="the corner salon",
        closing="the cape hooks were quiet and still",
        glow="the window light turned gold on the mirrors",
        room_word="shop",
    ),
}

TASKS = {
    "glitter_sign": Task(
        id="glitter_sign",
        label="a glitter sign",
        verb="hang up the sign",
        tool="glitter glue",
        result="sparkle",
        mess="sticky",
        risk="the glitter could smear on the fresh towels",
        tags={"glitter", "sign", "sticky"},
    ),
    "flower_box": Task(
        id="flower_box",
        label="the flower box",
        verb="fill the flower box",
        tool="water cups",
        result="spill",
        mess="wet",
        risk="the water could splash the clean floor",
        tags={"flower", "water", "wet"},
    ),
    "style_board": Task(
        id="style_board",
        label="the style board",
        verb="pin up the style board",
        tool="thumb tacks",
        result="tilt",
        mess="messy",
        risk="the board could tip into the comb basket",
        tags={"board", "pins", "messy"},
    ),
}

FIXES = {
    "towels": Fix(
        id="towels",
        label="fresh towels",
        action="wrap the wet spot and dry it together",
        outcome="the spill was gone",
        power=2,
        tags={"wet", "sticky"},
    ),
    "cloth": Fix(
        id="cloth",
        label="a soft cloth",
        action="wipe the sticky corner and smooth the sign flat",
        outcome="the glitter stayed neat",
        power=2,
        tags={"sticky", "messy"},
    ),
    "clips": Fix(
        id="clips",
        label="little clips",
        action="steady the board and hold it straight",
        outcome="the board stood proud again",
        power=1,
        tags={"messy"},
    ),
}

CHILDREN = {
    "Mina": "girl",
    "Theo": "boy",
    "Lia": "girl",
    "Noah": "boy",
    "Suri": "girl",
    "Owen": "boy",
}

PARENTS = ["mother", "father"]

KNOWLEDGE = {
    "salon": [(
        "What is a salon?",
        "A salon is a place where people wash, comb, cut, and style hair. It is a tidy place where careful hands help people feel neat and nice."
    )],
    "glitter": [(
        "Why can glitter glue be messy?",
        "Glitter glue is sticky, and tiny sparkly bits can spread onto other things. That is why grown-ups like to keep it in one neat spot."
    )],
    "water": [(
        "Why should water be used carefully near clean floors?",
        "Water can make a smooth floor slippery or leave a wet mark. People wipe it up so no one slips."
    )],
    "teamwork": [(
        "What is teamwork?",
        "Teamwork is when people help each other with different jobs and finish one job together. It feels easier and kinder than doing everything alone."
    )],
    "mirror": [(
        "Why do salons have mirrors?",
        "Mirrors help people see how their hair looks from the front and back. They also make the room feel bright."
    )],
    "towels": [(
        "What are towels for?",
        "Towels soak up water. People use them to dry hands, hair, and little spills."
    )],
}


class Rule:
    def __init__(self, name: str, apply) -> None:
        self.name = name
        self.apply = apply


def _r_mess(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["mess"] < THRESHOLD:
            continue
        sig = ("mess", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("salon").meters["untidy"] += 1
        out.append("__mess__")
    return out


def _r_worry(world: World) -> list[str]:
    out = []
    if world.get("child").meters["mess"] >= THRESHOLD and ("worry",) not in world.fired:
        world.fired.add(("worry",))
        world.get("parent").memes["worry"] += 1
        out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("mess", _r_mess), Rule("worry", _r_worry)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)


def _do_task(world: World, child: Entity, task: Task, narrate: bool = True) -> None:
    child.meters["mess"] += 1
    child.memes["pride"] += 1
    world.get("salon").meters["busy"] += 1
    propagate(world, narrate=narrate)


def predict_task(world: World, task: Task) -> dict:
    sim = world.copy()
    _do_task(sim, sim.get("child"), task, narrate=False)
    return {
        "mess": sim.get("salon").meters["untidy"],
        "worry": sim.get("parent").memes["worry"],
    }


def intro(world: World, child: Entity, parent: Entity, setting: SalonSetting) -> None:
    world.say(
        f"After the last haircut of the day, {setting.place} grew quiet. "
        f"{setting.closing} {setting.glow}."
    )
    world.say(
        f"{child.id} stayed close to {parent.id} and watched the combs and ribbons "
        f"rest in their boxes."
    )


def desire(world: World, child: Entity, task: Task) -> None:
    child.memes["eager"] += 1
    world.say(
        f'{child.id} pointed at {task.label}. "Can I help {task.verb}?" '
        f'{child.pronoun().capitalize()} asked.'
    )
    world.say(
        f"The little job looked bright and fun, and it could make the {task.label} "
        f"shine like part of a bedtime song."
    )


def warn(world: World, parent: Entity, task: Task) -> None:
    pred = predict_task(world, task)
    if pred["mess"] < THRESHOLD:
        return
    world.facts["predicted_mess"] = task.mess
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'"Careful," {parent.id} said softly. "If we rush, the {task.label} could '
        f'get {task.mess}, and the salon would need more tidying."'
    )


def teamwork_offer(world: World, parent: Entity, child: Entity, fix: Fix, task: Task) -> None:
    parent.memes["hope"] += 1
    child.memes["hope"] += 1
    world.say(
        f'{parent.id} smiled and lifted {fix.label}. "{fix.action.capitalize()}."'
    )
    world.say(
        f'"We can do it together," {child.id} said, and that made the room feel '
        f"smaller and warmer."
    )


def resolve(world: World, child: Entity, parent: Entity, fix: Fix, task: Task) -> None:
    child.memes["joy"] += 1
    parent.memes["joy"] += 1
    world.get("salon").meters["untidy"] = 0.0
    world.say(
        f"Together they used {fix.label} to {fix.action}. {fix.outcome}, and the "
        f"little salon felt calm again."
    )


def ending(world: World, child: Entity, parent: Entity, setting: SalonSetting) -> None:
    child.memes["love"] += 1
    parent.memes["love"] += 1
    world.say(
        f"Then {child.id} hummed a tiny tune to glorify the gentle hands that "
        f"kept the {setting.place} neat."
    )
    world.say(
        f"{parent.id} tucked the brushes away, and the two of them looked at the "
        f"mirror together, smiling at the happy ending they had made as a team."
    )
    world.say(
        f"By bedtime, {setting.place} was tidy, the air was soft, and the last "
        f"light in the mirror looked like a star saying goodnight."
    )


def tell(setting: SalonSetting, task: Task, fix: Fix, child_name: str, child_gender: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))

    intro(world, child, parent, setting)
    world.para()
    desire(world, child, task)
    warn(world, parent, task)
    teamwork_offer(world, parent, child, fix, task)
    _do_task(world, child, task, narrate=False)
    world.para()
    resolve(world, child, parent, fix, task)
    ending(world, child, parent, setting)

    world.facts.update(
        child=child,
        parent=parent,
        task=task,
        fix=fix,
        setting=setting,
        outcome="happy",
    )
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (sid, tid, fid)
        for sid in SETTINGS
        for tid in TASKS
        for fid in FIXES
        if task_fix_compatible(TASKS[tid], FIXES[fid])
    ]


def task_fix_compatible(task: Task, fix: Fix) -> bool:
    return any(tag in fix.tags for tag in task.tags)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime-style story for a young child that takes place in {f["setting"].place} and includes the word "salon".',
        f"Tell a gentle story about teamwork in a salon where {f['child'].id} helps with {f['task'].label} and a grown-up finds a calm fix.",
        f'Write a happy ending story where the child and parent work together, and the child says or sings "glorify" in a soft, loving way.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, task, fix = f["child"], f["parent"], f["task"], f["fix"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {parent.id}, who worked together in {f['setting'].place}. "
         f"Their teamwork turns the small problem into a calm bedtime ending."),
        ("What did the child want to do?",
         f"{child.id} wanted to {task.verb}. That job looked fun, but it also had a little risk of making a mess."),
        ("How did they fix the problem?",
         f"They used {fix.label} and worked together to {fix.action}. That teamwork helped the salon stay neat and peaceful."),
        ("How did the story end?",
         f"It ended happily. The salon was tidy again, and {child.id} and {parent.id} were smiling at the mirror like they had finished a cozy bedtime chore."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = []
    tags = set(world.facts["task"].tags) | set(world.facts["fix"].tags) | {"salon", "teamwork"}
    for key, pairs in KNOWLEDGE.items():
        if key in tags:
            for q, a in pairs:
                out.append(QAItem(q, a))
    return out


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
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
compatible(S, T, F) :- setting(S), task(T), fix(F), task_fix_compatible(T, F).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        for tag in sorted(task.tags):
            lines.append(asp.fact("task_tag", tid, tag))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for tag in sorted(fix.tags):
            lines.append(asp.fact("fix_tag", fid, tag))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP compatible combos differ from Python valid_combos().")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        print(f"MISMATCH: normal generation failed: {e}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return rc


CURATED = [
    StoryParams("salon", "glitter_sign", "cloth", "Mina", "girl", "mother"),
    StoryParams("home_salon", "flower_box", "towels", "Theo", "boy", "father"),
    StoryParams("corner_salon", "style_board", "clips", "Lia", "girl", "mother"),
]


def explain_rejection(task: Task, fix: Fix) -> str:
    return (
        f"(No story: {fix.label} does not really solve {task.label}. "
        f"Pick a fix that matches the mess better.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime-style salon storyworld with teamwork and a happy ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.task and args.fix and not task_fix_compatible(TASKS[args.task], FIXES[args.fix]):
        raise StoryError(explain_rejection(TASKS[args.task], FIXES[args.fix]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.task is None or c[1] == args.task)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, fix = rng.choice(sorted(combos))
    child_name = args.child or rng.choice(sorted(CHILDREN))
    child_gender = args.child_gender or CHILDREN[child_name]
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(setting, task, fix, child_name, child_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TASKS[params.task], FIXES[params.fix],
                 params.child, params.child_gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
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
        print(asp_program(show="#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for s, t, f in combos:
            print(f"{s} {t} {f}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
