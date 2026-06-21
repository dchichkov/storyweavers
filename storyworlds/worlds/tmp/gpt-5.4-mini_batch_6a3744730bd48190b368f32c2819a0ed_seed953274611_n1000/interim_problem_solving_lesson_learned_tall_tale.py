#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/interim_problem_solving_lesson_learned_tall_tale.py
==================================================================================

A standalone story world for a tall-tale style story about a problem, an
interim fix, a bigger lesson, and a cheerful ending image.

Premise
-------
A small village has a cracked bridge, a runaway problem, and one sturdy helper
who tries an interim solution before the proper fix can be finished. The story
is tall-tale flavored: the wind talks big, the river argues back, and the helper
is daring enough to tackle the trouble without turning the whole tale into a
frozen moral.

World idea
----------
- Physical meters model the broken bridge, the problem's spread, and the state of
  the interim fix.
- Emotional memes model worry, confidence, relief, pride, and lesson learned.
- The story can end in two reasonable ways:
  1. The interim fix holds long enough for the real repair.
  2. The interim fix fails, but the helper still solves the problem with a backup
     method and learns a lesson.

The story must mention the word "interim" and include a problem-solving beat and a
lesson-learned beat. The prose is driven by world state, not by a template swap.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    feature: str
    problem_name: str
    problem_phrase: str
    image: str
    wind_phrase: str
    water_phrase: str
    lesson_phrase: str
    rescue_phrase: str
    backup_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    near: str
    spread: int
    dangerous: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class InterimFix:
    id: str
    label: str
    phrase: str
    method: str
    holds: int
    can_fail: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class BackupFix:
    id: str
    label: str
    phrase: str
    method: str
    power: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    problem = world.get("problem")
    if problem.meters["active"] < THRESHOLD:
        return out
    sig = ("spread", problem.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["worry"] += 1
    world.get("town").meters["trouble"] += 1
    out.append("__spread__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.get("town").meters["trouble"] < THRESHOLD:
        return out
    sig = ("relief", "town")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("helper").memes["determination"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("spread", _r_spread), Rule("relief", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
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
    return produced


def problem_is_bad(problem: Problem) -> bool:
    return problem.dangerous


def interim_can_hold(problem: Problem, fix: InterimFix, delay: int) -> bool:
    return fix.holds >= problem.spread + delay


def backup_can_work(problem: Problem, backup: BackupFix, delay: int) -> bool:
    return backup.power >= problem.spread + delay


def predict_hold(world: World, problem_id: str, fix_id: str) -> dict:
    sim = world.copy()
    problem = sim.get(problem_id)
    fix = INTERIM_FIXES[fix_id]
    problem.meters["active"] = 1.0
    if interim_can_hold(PROBLEMS[problem.id], fix, int(sim.facts.get("delay", 0))):
        sim.get("bridge").meters["steady"] += 1
    else:
        sim.get("bridge").meters["steady"] += 0
    return {"holds": interim_can_hold(PROBLEMS[problem.id], fix, int(sim.facts.get("delay", 0)))}


def setup(world: World, helper: Entity, setting: Setting, problem: Problem) -> None:
    helper.memes["hope"] += 1
    world.say(
        f"At {setting.place}, where the {setting.image}, {helper.id} set out to fix a problem so big it seemed to have its own weather."
    )
    world.say(
        f"A tall crack ran through the {problem.label}, and the {setting.wind_phrase} kept bragging around it."
    )


def want_fix(world: World, helper: Entity, problem: Problem, setting: Setting) -> None:
    world.say(
        f"{helper.id} squinted at the trouble and said, \"That crack needs a plan, and it needs one before supper.\""
    )
    world.say(
        f"The river below kept muttering, and the whole village looked at the {problem.label} like it might wander off."
    )


def make_interim(world: World, helper: Entity, fix: InterimFix, setting: Setting) -> None:
    helper.memes["confidence"] += 1
    world.get("bridge").meters["patched"] += 1
    world.say(
        f"Then {helper.id} cooked up an {fix.label} -- {fix.phrase} -- because a proper repair would take longer than a rabbit can wink."
    )
    world.say(
        f"{helper.id} {fix.method}, and for a little while the trouble sat still."
    )


def hold_or_fail(world: World, helper: Entity, fix: InterimFix, problem: Problem, delay: int) -> bool:
    world.facts["delay"] = delay
    if interim_can_hold(problem, fix, delay):
        world.get("bridge").meters["steady"] += 1
        helper.memes["relief"] += 1
        world.say(
            f"The {fix.label} held. The crack stopped grumbling, and the village got a breath long enough to finish the real repair."
        )
        return True
    world.get("bridge").meters["steady"] += 0
    helper.memes["worry"] += 1
    world.say(
        f"The {fix.label} almost held, but the problem was too wild and the delay was too long. The crack kept widening like a jaw."
    )
    return False


def solve_backup(world: World, helper: Entity, backup: BackupFix, problem: Problem, delay: int) -> None:
    if backup_can_work(problem, backup, delay):
        world.get("bridge").meters["fixed"] += 1
        helper.memes["relief"] += 1
        helper.memes["pride"] += 1
        world.say(
            f"So {helper.id} did not panic. Instead, {helper.pronoun()} {backup.method}, and that sturdy trick finished what the interim patch could not."
        )
        world.say(
            f"The {problem.label} settled down at last, and the whole town could cross with both feet and both smiles."
        )
    else:
        world.get("bridge").meters["fixed"] += 0
        helper.memes["worry"] += 1
        world.say(
            f"Even the backup plan was too small, so {helper.id} had to send for the biggest help in the county."
        )


def lesson(world: World, helper: Entity, fix_halted: bool, setting: Setting) -> None:
    helper.memes["lesson"] += 1
    if fix_halted:
        world.say(
            f"By then {helper.id} had learned the grand lesson of the day: an interim fix is good for a minute, but a real repair is better for a lifetime."
        )
    else:
        world.say(
            f"{helper.id} learned a grand lesson anyway: when one fix is not enough, the next one must be wiser, not louder."
        )
    world.say(
        f"And that evening, {setting.place} looked peaceful again, with the {setting.image} shining like it had never been worried at all."
    )


def tell(setting: Setting, problem: Problem, interim_fix: InterimFix, backup: BackupFix,
         helper_name: str = "Mabel", helper_gender: str = "girl", delay: int = 0) -> World:
    world = World()
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    town = world.add(Entity(id="town", type="place", label="the town"))
    bridge = world.add(Entity(id="bridge", type="thing", label=problem.label))
    problem_ent = world.add(Entity(id="problem", type="thing", label=problem.label))
    world.facts["problem"] = problem
    world.facts["setting"] = setting
    world.facts["interim_fix"] = interim_fix
    world.facts["backup_fix"] = backup
    world.facts["helper"] = helper
    world.facts["delay"] = delay
    setup(world, helper, setting, problem)
    world.para()
    want_fix(world, helper, problem, setting)
    make_interim(world, helper, interim_fix, setting)
    world.para()
    held = hold_or_fail(world, helper, interim_fix, problem, delay)
    if held:
        solve_backup(world, helper, backup, problem, delay)
    else:
        solve_backup(world, helper, backup, problem, delay)
    world.para()
    lesson(world, helper, held, setting)
    world.facts["outcome"] = "held" if held else "backup"
    return world


SETTINGS = {
    "river_town": Setting(
        id="river_town",
        place="Riverbend Town",
        feature="interim",
        problem_name="bridge crack",
        problem_phrase="the bridge crack",
        image="the old bridge",
        wind_phrase="the wind",
        water_phrase="the river water",
        lesson_phrase="an interim fix is only a visitor, not a forever home",
        rescue_phrase="put a stop to the crack",
        backup_phrase="the backup plan",
        tags={"interim", "bridge", "river"},
    ),
    "canyon": Setting(
        id="canyon",
        place="Canyon Cross",
        feature="interim",
        problem_name="rope break",
        problem_phrase="the rope bridge",
        image="the rope bridge",
        wind_phrase="the canyon wind",
        water_phrase="the creek below",
        lesson_phrase="a patch can help, but a sturdy fix lasts longer",
        rescue_phrase="hold the span steady",
        backup_phrase="the stronger rope",
        tags={"interim", "bridge", "canyon"},
    ),
}

PROBLEMS = {
    "bridge_crack": Problem(id="bridge_crack", label="bridge", near="the river", spread=2, tags={"bridge"}),
    "rope_break": Problem(id="rope_break", label="rope bridge", near="the canyon", spread=3, tags={"bridge"}),
}

INTERIM_FIXES = {
    "wood_wedges": InterimFix(id="wood_wedges", label="interim patch", phrase="a row of wooden wedges", method="hammered the wedges into the crack", holds=2, can_fail=True, tags={"interim"}),
    "rope_bind": InterimFix(id="rope_bind", label="interim binding", phrase="a quick rope binding", method="wrapped the rope around the break", holds=3, can_fail=True, tags={"interim"}),
}

BACKUP_FIXES = {
    "planks": BackupFix(id="planks", label="plank brace", phrase="a brace of planks", method="bolted on two stout planks", power=4, tags={"backup"}),
    "stones": BackupFix(id="stones", label="stone support", phrase="a stone support", method="stacked river stones under the weak spot", power=5, tags={"backup"}),
}

TRAITS = ["bold", "steady", "clever", "patient", "spry", "stubborn"]

GIRL_NAMES = ["Mabel", "Ruby", "Ivy", "Nell", "Hazel", "Ada"]
BOY_NAMES = ["Benny", "Otis", "Theo", "Cal", "Jasper", "Ollie"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    interim_fix: str
    backup_fix: str
    helper_name: str
    helper_gender: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid in PROBLEMS:
            for iid in INTERIM_FIXES:
                for bid in BACKUP_FIXES:
                    combos.append((sid, pid, iid, bid))
    return combos


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the chosen pieces do not make a plausible problem-solving tall tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about an interim fix and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--interim-fix", dest="interim_fix", choices=INTERIM_FIXES)
    ap.add_argument("--backup-fix", dest="backup_fix", choices=BACKUP_FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.setting is None:
        setting = rng.choice(sorted(SETTINGS))
    else:
        setting = args.setting
    if args.problem is None:
        problem = rng.choice(sorted(PROBLEMS))
    else:
        problem = args.problem
    if args.interim_fix is None:
        interim_fix = rng.choice(sorted(INTERIM_FIXES))
    else:
        interim_fix = args.interim_fix
    if args.backup_fix is None:
        backup_fix = rng.choice(sorted(BACKUP_FIXES))
    else:
        backup_fix = args.backup_fix
    if (setting, problem, interim_fix, backup_fix) not in combos:
        raise StoryError("The chosen setting/problem/fixes do not form a workable tall tale.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting,
        problem=problem,
        interim_fix=interim_fix,
        backup_fix=backup_fix,
        helper_name=name,
        helper_gender=gender,
        trait=trait,
        delay=delay,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    problem = f["problem"]
    return [
        f'Write a tall-tale story for a child that includes the word "interim" and shows a quick fix for {problem.label}.',
        f"Tell a lively story where {f['helper'].id} uses an interim fix at {setting.place} and learns a bigger lesson about solving problems.",
        f"Write a story with a problem-solving middle and a lesson-learned ending, using the image of {setting.image} and the word interim.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    helper = f["helper"]
    setting = f["setting"]
    problem = f["problem"]
    interim_fix = f["interim_fix"]
    backup = f["backup_fix"]
    items = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {helper.id}, who tries to solve a big problem at {setting.place}. The helper keeps going even when the trouble feels taller than the road."
        ),
        QAItem(
            question="What problem needed solving?",
            answer=f"The {problem.label} had become a dangerous problem and needed attention right away. If nobody helped, the trouble could keep spreading near {problem.near}."
        ),
        QAItem(
            question="What was the interim fix?",
            answer=f"The interim fix was {interim_fix.phrase}. It gave the problem a temporary hold so there was time to make a better repair."
        ),
    ]
    if f.get("outcome") == "held":
        items.append(
            QAItem(
                question="How did the helper solve the problem in the end?",
                answer=f"{helper.id} used the interim patch first, and it held long enough for the next repair to happen. That solved the problem without letting the trouble win the day."
            )
        )
    else:
        items.append(
            QAItem(
                question="How did the helper solve the problem in the end?",
                answer=f"The interim fix was not strong enough, so {helper.id} switched to the backup plan and finished the job with {backup.phrase}. That second move solved what the first move could only start."
            )
        )
    items.append(
        QAItem(
            question="What lesson did the helper learn?",
            answer=f"{helper.id} learned that an interim fix is useful only for a while, and the real solution must be chosen with care. The lesson was bigger than the crack, and it stayed with the helper after the dust settled."
        )
    )
    return items


WORLD_KNOWLEDGE = {
    "interim": [
        QAItem(
            question="What does interim mean?",
            answer="Interim means temporary or in-between. It describes something that helps for now while a better fix is being prepared."
        )
    ],
    "bridge": [
        QAItem(
            question="What is a bridge for?",
            answer="A bridge helps people cross water, a gap, or another hard-to-cross place. It connects one side to another."
        )
    ],
    "lesson": [
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is something you understand better after an experience. It helps you do wiser things next time."
        )
    ],
    "problem": [
        QAItem(
            question="What should you do when you find a problem?",
            answer="First, stay calm and look carefully. Then choose a safe plan and ask for help if the problem is bigger than one person can handle."
        )
    ],
}

WORLD_KNOWLEDGE_ORDER = ["interim", "bridge", "lesson", "problem"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in WORLD_KNOWLEDGE_ORDER:
        out.extend(WORLD_KNOWLEDGE.get(key, []))
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
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="river_town",
        problem="bridge_crack",
        interim_fix="wood_wedges",
        backup_fix="planks",
        helper_name="Mabel",
        helper_gender="girl",
        trait="bold",
        delay=0,
    ),
    StoryParams(
        setting="canyon",
        problem="rope_break",
        interim_fix="rope_bind",
        backup_fix="stones",
        helper_name="Benny",
        helper_gender="boy",
        trait="clever",
        delay=1,
    ),
]


def generate_story(params: StoryParams) -> World:
    setting = SETTINGS.get(params.setting)
    problem = PROBLEMS.get(params.problem)
    interim_fix = INTERIM_FIXES.get(params.interim_fix)
    backup = BACKUP_FIXES.get(params.backup_fix)
    if not (setting and problem and interim_fix and backup):
        raise StoryError("Invalid story parameters.")
    return tell(
        setting=setting,
        problem=problem,
        interim_fix=interim_fix,
        backup=backup,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        delay=params.delay,
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_story(params)
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for iid in INTERIM_FIXES:
        lines.append(asp.fact("interim_fix", iid))
    for bid in BACKUP_FIXES:
        lines.append(asp.fact("backup_fix", bid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,I,B) :- setting(S), problem(P), interim_fix(I), backup_fix(B).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combos disagree.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"MISMATCH: smoke test failed: {exc}")
        rc = 1
    else:
        print("OK: ASP parity and story smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld with interim fixes and lessons learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--interim-fix", dest="interim_fix", choices=INTERIM_FIXES)
    ap.add_argument("--backup-fix", dest="backup_fix", choices=BACKUP_FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
