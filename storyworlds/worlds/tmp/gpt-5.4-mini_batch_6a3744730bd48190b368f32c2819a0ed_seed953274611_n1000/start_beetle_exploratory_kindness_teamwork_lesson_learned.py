#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/start_beetle_exploratory_kindness_teamwork_lesson_learned.py
==============================================================================================

A small space-adventure storyworld about a first launch, a curious beetle-like
companion, and a kind teamwork lesson learned. The core premise is simple:
two explorers begin a mission together, meet a stranded beetle scout in a
tiny shipyard or moon garden, and choose kindness and teamwork over leaving it
behind. The ending proves what changed by showing the explorers and beetle
working together on a safer, brighter start.

Seed words: start, beetle, exploratory
Features: Kindness, Teamwork, Lesson Learned
Style: Space Adventure
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
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    scene: str
    start_image: str
    dark_spot: str
    mission: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Beetle:
    id: str
    label: str
    phrase: str
    exploratory: str
    need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    text: str
    risk: str
    fix_need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    beetle: str
    problem: str
    fix: str
    hero: str
    helper: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_scatter(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["lost"] < THRESHOLD:
            continue
        sig = ("scatter", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ch in world.entities.values():
            if ch.kind == "character":
                ch.memes["worry"] += 1
        out.append("__scatter__")
    return out


CAUSAL_RULES = [Rule("scatter", _r_scatter)]


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


def plausible_fix(problem: Problem, fix: Fix) -> bool:
    return problem.fix_need in fix.tags and fix.sense >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for bid, b in BEETLES.items():
            for pid, p in PROBLEMS.items():
                for fid, f in FIXES.items():
                    if p.fix_need in f.tags and f.sense >= 2:
                        combos.append((sid, bid, pid, fid))
    return combos


def _do_problem(world: World, beetle_ent: Entity, problem: Problem, narrate: bool = True) -> None:
    beetle_ent.meters["lost"] += 1
    beetle_ent.meters["tired"] += 1
    propagate(world, narrate=narrate)


def predict(world: World, beetle_ent: Entity, problem: Problem) -> dict:
    sim = world.copy()
    _do_problem(sim, sim.get(beetle_ent.id), problem, narrate=False)
    return {"lost": sim.get(beetle_ent.id).meters["lost"] >= THRESHOLD, "worry": sim.get("hero").memes["worry"]}


def start(world: World, setting: Setting, hero: Entity, helper: Entity) -> None:
    hero.memes["curious"] += 1
    helper.memes["hope"] += 1
    world.say(
        f"At the start of the mission, {hero.id} and {helper.id} rolled their small exploratory pod out beneath the stars. "
        f"{setting.start_image}"
    )
    world.say(
        f'"Today is the start," {hero.id} said. "{setting.mission}!"'
    )


def discover(world: World, beetle_ent: Entity, setting: Setting, problem: Problem) -> None:
    world.say(
        f"Beyond the glowing hatch, they found {beetle_ent.phrase} near {setting.dark_spot}. "
        f"It looked {beetle_ent.exploratory} but also a little lost."
    )
    world.say(
        f"{beetle_ent.id} listened with tiny clicking feet, as if it needed a friend before it could go on."
    )


def warn(world: World, helper: Entity, hero: Entity, beetle_ent: Entity, problem: Problem) -> None:
    pred = predict(world, hero, problem)
    helper.memes["kindness"] += 1
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'{helper.id} touched {hero.pronoun("possessive")} sleeve and said, '
        f'"We cannot leave the {beetle_ent.label} here. It needs {problem.risk}, and it may get more lost."'
    )


def choose_kindness(world: World, hero: Entity, helper: Entity, beetle_ent: Entity) -> None:
    hero.memes["kindness"] += 1
    helper.memes["teamwork"] += 1
    world.say(
        f"{hero.id} nodded. \"Then we help it,\" {hero.id} said, and {helper.id} smiled."
    )


def teamwork(world: World, hero: Entity, helper: Entity, beetle_ent: Entity, setting: Setting) -> None:
    hero.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    beetle_ent.memes["trust"] += 1
    world.say(
        f"The two explorers worked as a team: one held the lantern, one fixed the map, and the {beetle_ent.label} followed the bright line home."
    )


def lesson(world: World, parent: Entity, hero: Entity, helper: Entity, beetle_ent: Entity) -> None:
    hero.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    beetle_ent.memes["safe"] += 1
    world.say(
        f"{parent.label_word.capitalize()} met them at the dock and hugged them both. "
        f'"Kindness makes a team stronger," {parent.id} said. "You learned that the start of a good trip is helping first."'
    )
    world.say(
        f"{hero.id} looked at the {beetle_ent.label} and grinned. The little scout was no longer alone."
    )


def rescue(world: World, fix: Fix, beetle_ent: Entity, problem: Problem) -> None:
    beetle_ent.meters["lost"] = 0
    beetle_ent.memes["relief"] += 1
    world.say(
        f"{fix.text.replace('{problem}', problem.id)}"
    )
    world.say(
        f"The {beetle_ent.label} buzzed happily, and the dark spot on the map turned into a safe path."
    )


def fail_rescue(world: World, fix: Fix, beetle_ent: Entity, problem: Problem) -> None:
    beetle_ent.meters["lost"] += 1
    world.say(
        f"{fix.fail.replace('{problem}', problem.id)}"
    )
    world.say(
        f"The explorers still tried to help, but the trail grew dim and they had to call for backup."
    )


SETTINGS = {
    "hangar": Setting(
        id="hangar",
        scene="a silver hangar that echoed like a sleeping moon",
        start_image="A tiny launch bay glowed blue, and a telescope watched from the wall.",
        dark_spot="the shadow under the cargo ramp",
        mission="Let's begin the exploratory route",
        tags={"space", "start"},
    ),
    "moon_garden": Setting(
        id="moon_garden",
        scene="a moon garden with glass flowers and dusty paths",
        start_image="Starlight fell on neat rows of glowing plants.",
        dark_spot="a little crater behind the glass lilies",
        mission="Let's start our exploratory walk",
        tags={"space", "start"},
    ),
    "asteroid_post": Setting(
        id="asteroid_post",
        scene="a tiny asteroid post with round windows",
        start_image="A red beacon blinked beside the airlock, ready for a launch.",
        dark_spot="the narrow crack behind the antenna",
        mission="Let's start the exploratory scan",
        tags={"space", "start"},
    ),
}

BEETLES = {
    "beetle_scout": Beetle(
        id="beetle_scout",
        label="beetle",
        phrase="a beetle scout with shiny copper wings",
        exploratory="exploratory and brave",
        need="a lantern and a kind hand",
        tags={"beetle", "exploratory"},
    ),
    "beetle_cartographer": Beetle(
        id="beetle_cartographer",
        label="beetle",
        phrase="a beetle cartographer carrying a tiny map shell",
        exploratory="exploratory, careful, and curious",
        need="a map and teamwork",
        tags={"beetle", "exploratory"},
    ),
}

PROBLEMS = {
    "stuck": Problem(
        id="stuck",
        text="stuck behind a shadowy hatch",
        risk="a clear path",
        fix_need="help",
        tags={"help", "kindness"},
    ),
    "lost": Problem(
        id="lost",
        text="lost near the dark edge of the route",
        risk="a guiding line",
        fix_need="map",
        tags={"map", "teamwork"},
    ),
}

FIXES = {
    "lantern_share": Fix(
        id="lantern_share",
        sense=3,
        power=3,
        text="They shared the lantern light, and the {problem} was easy to find again",
        fail="They tried to shine a little light on the {problem}, but the dark stayed too thick",
        qa_text="shared the lantern light and found the way together",
        tags={"help", "kindness"},
    ),
    "map_pair": Fix(
        id="map_pair",
        sense=3,
        power=3,
        text="They matched the map to the stars, and the {problem} became a safe route",
        fail="They lined up the map, but the {problem} still hid in the dark",
        qa_text="matched the map to the stars and found a safe route",
        tags={"map", "teamwork"},
    ),
    "rope_team": Fix(
        id="rope_team",
        sense=2,
        power=2,
        text="They tied a careful rope line, and the {problem} could not pull the beetle away",
        fail="They tugged on a rope line, but the {problem} was too far out",
        qa_text="tied a careful rope line and worked together",
        tags={"help", "teamwork"},
    ),
}


GIRL_NAMES = ["Luna", "Mira", "Ivy", "Nova", "Zara"]
BOY_NAMES = ["Orion", "Finn", "Jace", "Theo", "Kai"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld about kindness and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--beetle", choices=BEETLES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--parent", choices=["captain", "pilot"])
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
    if args.setting and args.beetle and args.problem and args.fix:
        if (args.setting, args.beetle, args.problem, args.fix) not in combos:
            raise StoryError("That combination does not make a reasonable space story.")
    cand = [c for c in combos
            if (args.setting is None or c[0] == args.setting)
            and (args.beetle is None or c[1] == args.beetle)
            and (args.problem is None or c[2] == args.problem)
            and (args.fix is None or c[3] == args.fix)]
    if not cand:
        raise StoryError("(No valid combination matches the given options.)")
    setting, beetle, problem, fix = rng.choice(sorted(cand))
    hero = args.hero or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero])
    parent = args.parent or rng.choice(["captain", "pilot"])
    return StoryParams(setting=setting, beetle=beetle, problem=problem, fix=fix, hero=hero, helper=helper, parent=parent)


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.beetle not in BEETLES:
        raise StoryError("Unknown beetle.")
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if params.fix not in FIXES:
        raise StoryError("Unknown fix.")
    setting = SETTINGS[params.setting]
    beetle_cfg = BEETLES[params.beetle]
    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    if not plausible_fix(problem, fix):
        raise StoryError("That fix does not fit the problem.")
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type="girl" if params.hero in GIRL_NAMES else "boy", role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type="girl" if params.helper in GIRL_NAMES else "boy", role="helper"))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label="the ship captain"))
    beetle_ent = world.add(Entity(id="beetle", kind="character", type="beetle", label="beetle", role="companion"))
    beetle_ent.memes["exploratory"] = 1
    start(world, setting, hero, helper)
    world.para()
    discover(world, beetle_ent, setting, problem)
    warn(world, helper, hero, beetle_ent, problem)
    choose_kindness(world, hero, helper, beetle_ent)
    _do_problem(world, beetle_ent, problem, narrate=False)
    if fix.power >= 3:
        rescue(world, fix, beetle_ent, problem)
    else:
        fail_rescue(world, fix, beetle_ent, problem)
    teamwork(world, hero, helper, beetle_ent, setting)
    lesson(world, parent, hero, helper, beetle_ent)
    world.facts.update(hero=hero, helper=helper, parent=parent, beetle=beetle_ent,
                       beetle_cfg=beetle_cfg, setting=setting, problem=problem, fix=fix)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space-adventure story that starts with the word "start" and includes a beetle scout.',
        f"Tell a gentle exploratory mission where {f['hero'].id} and {f['helper'].id} choose kindness when they find a beetle in trouble.",
        f'Write a child-friendly story about teamwork and a lesson learned in a moon base, using the word "exploratory".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, beetle = f["hero"], f["helper"], f["beetle"]
    fix = f["fix"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id}, {helper.id}, and a beetle scout who needed help. They began their space trip at the start of the mission and learned to work together."
        ),
        QAItem(
            question=f"What did {hero.id} and {helper.id} do when they found the beetle?",
            answer=f"They chose kindness and helped the beetle instead of leaving it alone. That teamwork made the scary part turn into a safe path."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the explorers and the beetle working side by side. The lesson learned was that kindness makes teamwork stronger."
        ),
        QAItem(
            question="What changed after the fix?",
            answer=f"The {beetle.label} was no longer lost, and the route became clear. The explorers used {fix.qa_text}, so the mission could continue safely."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a beetle?",
            answer="A beetle is a small insect with a hard shell and six legs. Some beetles can crawl, explore, and sparkle in the light."
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing to help instead of ignore someone. It is a gentle way to make another creature feel safe."
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people share the job and help one another. Each helper does a part, and together they can do more than one could alone."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={dict(m)}")
        if mm:
            bits.append(f"memes={dict(mm)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="hangar", beetle="beetle_scout", problem="stuck", fix="lantern_share", hero="Luna", helper="Kai", parent="captain"),
    StoryParams(setting="moon_garden", beetle="beetle_cartographer", problem="lost", fix="map_pair", hero="Orion", helper="Mira", parent="pilot"),
    StoryParams(setting="asteroid_post", beetle="beetle_scout", problem="lost", fix="rope_team", hero="Nova", helper="Finn", parent="captain"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid, b in BEETLES.items():
        lines.append(asp.fact("beetle", bid))
        for t in sorted(b.tags):
            lines.append(asp.fact("beetle_tag", bid, t))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("fix_need", pid, p.fix_need))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("power", fid, f.power))
        for t in sorted(f.tags):
            lines.append(asp.fact("fix_tag", fid, t))
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(S,B,P,F) :- setting(S), beetle(B), problem(P), fix(F), fix_need(P,N), fix_tag(F,N), sense(F, Sx), Sx >= 2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/4."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, beetle=None, problem=None, fix=None, hero=None, helper=None, parent=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: story generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show reasonable/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
