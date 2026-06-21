#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/straighten_comma_twist_bravery_pirate_tale.py
=============================================================================

A small standalone storyworld for a pirate-tale-style story about a twisty map,
a brave choice, and the words "straighten" and "comma".

The world is intentionally tiny:
- two child pirates and one adult helper
- a twisted route that needs straightening
- a comma-shaped mark on a map that must be read correctly
- a bravery turn where a child speaks up and fixes the route

The story variants are driven by simulated world state, not by swapping nouns in
a frozen paragraph.
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
class Theme:
    id: str
    scene: str
    rig: str
    crew_title: str
    goal: str
    twist_noun: str
    map_mark: str
    send_off: str


@dataclass
class Problem:
    id: str
    label: str
    clue: str
    place: str
    messy: bool = True
    twisty: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    power: int
    sense: int
    text: str
    fail: str
    qa_text: str
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
    tag: str
    apply: Callable[[World], list[str]]


def _r_twist(world: World) -> list[str]:
    out: list[str] = []
    if "path" not in world.entities:
        return out
    path = world.get("path")
    if path.meters["twisted"] < THRESHOLD:
        return out
    sig = ("twist",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.entities.values():
        if kid.role in {"captain", "mate"}:
            kid.memes["confusion"] += 1
    out.append("__twist__")
    return out


def _r_brave(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.entities.values():
        if kid.role != "captain" or kid.memes["bravery"] < THRESHOLD:
            continue
        sig = ("brave", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("path").meters["straightened"] += 1
        out.append("__brave__")
    return out


CAUSAL_RULES = [Rule("twist", "physical", _r_twist), Rule("brave", "social", _r_brave)]


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


def read_mark(problem: Problem) -> str:
    return "comma" if problem.id == "comma" else problem.label


def hazard(problem: Problem) -> bool:
    return problem.twisty


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def route_confusion(problem: Problem, delay: int) -> int:
    return 1 + delay if problem.twisty else delay


def can_straighten(fix: Fix, problem: Problem, delay: int) -> bool:
    return fix.power >= route_confusion(problem, delay)


def predict(world: World, problem_id: str) -> dict:
    sim = world.copy()
    _do_twist(sim, sim.get(problem_id), narrate=False)
    return {"twisted": sim.get("path").meters["twisted"] >= THRESHOLD,
            "confusion": sim.get("crew").memes["confusion"] if "crew" in sim.entities else 0}


def _do_twist(world: World, problem_ent: Entity, narrate: bool = True) -> None:
    problem_ent.meters["twisted"] += 1
    propagate(world, narrate=narrate)


def opener(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a breezy day, {a.id} and {b.id} turned the deck into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"{theme.crew_title} {a.id} and lookout {b.id}!" {a.id} shouted. '
        f'"Let\'s find {theme.goal}!"'
    )


def show_problem(world: World, b: Entity, theme: Theme, problem: Problem) -> None:
    world.say(
        f"But the way ahead bent into a {theme.twist_noun} -- {problem.clue} -- "
        f"and the map mark looked like a little {theme.map_mark}."
    )
    world.say(f'{b.id} squinted at it. "We should {problem.label}," {b.pronoun()} said.')


def tempt(world: World, a: Entity, problem: Problem) -> None:
    a.memes["boldness"] += 1
    world.say(f'{a.id} grinned. "I know! We can just follow the mark and not worry."')
    world.say("For one blink, that sounded easy.")


def warn(world: World, b: Entity, a: Entity, problem: Problem, parent: Entity) -> None:
    pred = predict(world, "problem")
    b.memes["care"] += 1
    world.facts["predicted_confusion"] = pred["confusion"]
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, {parent.label_word} '
        f'said to watch the {problem.map_mark}. If we read it wrong, we get lost."'
    )


def brave_turn(world: World, a: Entity, b: Entity, theme: Theme, problem: Problem) -> None:
    a.memes["bravery"] += 1
    world.say(
        f'{a.id} took a breath, straightened the map with both hands, and said, '
        f'"Wait -- that mark is a {theme.map_mark}, not a bend in the road."'
    )
    world.say(
        f'With that brave little pause, {a.id} helped {b.id} see the path more clearly.'
    )


def resolve_story(world: World, a: Entity, b: Entity, parent: Entity, fix: Fix,
                  theme: Theme, problem: Problem) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came over and smiled. In a flash "
        f"{parent.pronoun()} {fix.text}."
    )
    world.say(
        f"The map lay flat again, the route was straightened, and the crew could "
        f"see the trail clearly at last."
    )
    world.say(
        f"Then {a.id} and {b.id} sailed on to {theme.send_off} -- brave, sure, and "
        f"laughing at the tiny comma mark that had fooled them."
    )


def fail_resolve(world: World, parent: Entity, fix: Fix, theme: Theme, problem: Problem) -> None:
    world.say(
        f"{parent.label_word.capitalize()} tried to help, but {fix.fail}."
    )
    world.say(
        f"The trail stayed twisted, so the little crew had to stop and call for help "
        f"before they could reach {theme.goal}."
    )
    world.say(
        f"Even then, they remembered the comma mark and promised to straighten the map "
        f"before the next trip."
    )


@dataclass
class StoryParams:
    theme: str
    problem: str
    fix: str
    captain: str
    captain_gender: str
    mate: str
    mate_gender: str
    parent: str
    delay: int = 0
    captain_age: int = 6
    mate_age: int = 5
    relation: str = "crew"
    seed: Optional[int] = None


THEMES = {
    "pirate_tale": Theme(
        id="pirate_tale",
        scene="a pretend pirate cove",
        rig="The barrel was their ship, a mop became a mast, and a paper flag flapped in the wind.",
        crew_title="Captain",
        goal="the hidden cove",
        twist_noun="twisty rope bridge",
        map_mark="comma",
        send_off="sail toward the hidden cove",
    ),
    "harbor": Theme(
        id="harbor",
        scene="a busy harbor game",
        rig="The crates became docks, a spoon was the lookout glass, and a chalk line traced the quay.",
        crew_title="Captain",
        goal="the far dock",
        twist_noun="crooked pier path",
        map_mark="comma",
        send_off="head out past the boats",
    ),
}

PROBLEMS = {
    "comma": Problem(
        id="comma",
        label="the comma",
        clue="the tiny mark that curled like a hook",
        place="the map",
        messy=False,
        twisty=True,
        tags={"comma", "map", "twist"},
    ),
    "twist": Problem(
        id="twist",
        label="the twist",
        clue="the path that looped around and around",
        place="the trail",
        messy=False,
        twisty=True,
        tags={"twist", "path"},
    ),
}

FIXES = {
    "straighten": Fix(
        id="straighten",
        label="straighten the map",
        phrase="straighten",
        power=3,
        sense=3,
        text="straightened the map and traced the route with a careful finger",
        fail="the map was still curled, and the route slipped away in a tangle",
        qa_text="straightened the map and traced the route with a careful finger",
        tags={"straighten", "map"},
    ),
    "line_up": Fix(
        id="line_up",
        label="line up the map",
        phrase="line up",
        power=2,
        sense=2,
        text="lined up the map against the table and smoothed the bend out",
        fail="the table was too wobbly, and the bend stayed put",
        qa_text="lined up the map against the table and smoothed the bend out",
        tags={"straighten", "map"},
    ),
    "ask_adult": Fix(
        id="ask_adult",
        label="ask for help",
        phrase="ask for help",
        power=4,
        sense=4,
        text="held the map up to the lantern light and helped read it aloud",
        fail="the light was too dim, so the mark stayed confusing",
        qa_text="held the map up to the lantern light and helped read it aloud",
        tags={"help", "light"},
    ),
}

SENSE_MIN = 2

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_fixes():
        return combos
    for t in THEMES:
        for p in PROBLEMS:
            for f in FIXES:
                if hazard(PROBLEMS[p]):
                    combos.append((t, p, f))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small pirate tale storyworld about twist, comma, and bravery.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
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
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError("That fix is too weak for this storyworld.")
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, problem, fix = rng.choice(sorted(combos))
    captain = rng.choice(GIRL_NAMES + BOY_NAMES)
    mate_pool = [n for n in GIRL_NAMES + BOY_NAMES if n != captain]
    mate = rng.choice(mate_pool)
    cg = rng.choice(["girl", "boy"])
    mg = rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        theme=theme,
        problem=problem,
        fix=fix,
        captain=captain,
        captain_gender=cg,
        mate=mate,
        mate_gender=mg,
        parent=parent,
        delay=rng.randint(0, 1),
    )


def tell(theme: Theme, problem: Problem, fix: Fix, captain: str, captain_gender: str,
         mate: str, mate_gender: str, parent_type: str, delay: int = 0) -> World:
    world = World()
    a = world.add(Entity(id=captain, kind="character", type=captain_gender, role="captain"))
    b = world.add(Entity(id=mate, kind="character", type=mate_gender, role="mate"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    crew = world.add(Entity(id="crew", kind="character", type="crew", role="crew"))
    path = world.add(Entity(id="path", type="thing", label="the path"))
    problem_ent = world.add(Entity(id="problem", type="thing", label=problem.label))
    a.memes["bravery"] = 1.0
    b.memes["care"] = 1.0

    opener(world, a, b, theme)
    show_problem(world, b, theme, problem)
    world.para()
    tempt(world, a, problem)
    warn(world, b, a, problem, parent)
    brave_turn(world, a, b, theme, problem)
    _do_twist(world, problem_ent)
    world.para()
    if can_straighten(fix, problem, delay):
        resolve_story(world, a, b, parent, fix, theme, problem)
    else:
        fail_resolve(world, parent, fix, theme, problem)

    world.facts.update(
        captain=a, mate=b, parent=parent, crew=crew, path=path, problem=problem_ent,
        theme=theme, problem_cfg=problem, fix=fix, delay=delay, outcome="resolved" if can_straighten(fix, problem, delay) else "failed",
    )
    return world


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES or params.problem not in PROBLEMS or params.fix not in FIXES:
        raise StoryError("Invalid parameters for this storyworld.")
    world = tell(THEMES[params.theme], PROBLEMS[params.problem], FIXES[params.fix],
                 params.captain, params.captain_gender, params.mate, params.mate_gender,
                 params.parent, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b = f["captain"], f["mate"]
    th, prob, fx = f["theme"], f["problem_cfg"], f["fix"]
    return [
        f'Write a pirate-tale story for a 3-to-5-year-old that includes the words "straighten" and "comma".',
        f"Tell a brave pirate story where {a.id} notices a comma-shaped mark and {b.id} helps keep the crew from getting lost.",
        f"Write a short story where a twisty route is fixed by someone brave enough to straighten the map.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, parent = f["captain"], f["mate"], f["parent"]
    theme, prob, fx = f["theme"], f["problem_cfg"], f["fix"]
    qa = [
        ("Who is the story about?",
         f"It is about {a.id} and {b.id}, two little pirates, and {parent.label_word}."),
        ("What was wrong with the path?",
         f"The path was twisty, and the map had a comma-shaped mark that could be read the wrong way."),
        ("What did {0} do that was brave?".format(a.id),
         f"{a.id} took a breath, straightened the map, and spoke up before the crew got lost."),
    ]
    if f["outcome"] == "resolved":
        qa.append((
            "How was the problem fixed?",
            f"{f['parent'].label_word.capitalize()} helped {fx.qa_text}. That made the route clear again, so the crew could keep sailing."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the map straightened and the crew sailing on happily toward {theme.send_off}."
        ))
    else:
        qa.append((
            "What happened when they tried to fix it?",
            f"The help was not enough, so the route stayed twisted and they had to stop for more help."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["problem_cfg"].tags) | set(world.facts["fix"].tags)
    out: list[tuple[str, str]] = []
    if "comma" in tags:
        out.append(("What is a comma?", "A comma is a small mark in writing that can show a pause or separate parts of a sentence."))
    if "straighten" in tags:
        out.append(("What does straighten mean?", "To straighten something means to make it less bent, twisted, or crooked."))
    if "twist" in tags:
        out.append(("What does twisty mean?", "Twisty means bent around or turned in a winding way."))
    if "help" in tags:
        out.append(("Why should you ask for help when you're stuck?", "A grown-up can notice things you missed and help you solve the problem safely."))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_invalid_fix(fix: Fix) -> str:
    return f"(Refusing fix '{fix.id}': it is too weak for this little storyworld.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for p, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", p))
        if prob.twisty:
            lines.append(asp.fact("twisty", p))
    for f, fx in FIXES.items():
        lines.append(asp.fact("fix", f))
        lines.append(asp.fact("sense", f, fx.sense))
        lines.append(asp.fact("power", f, fx.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(T,P,F) :- theme(T), problem(P), fix(F), twisty(P), sense(F,S), sense_min(M), S >= M.
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: smoke test story generation works.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def resolve_params_and_seed(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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
        for t, p, f in combos:
            print(f"  {t:12} {p:8} {f}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(theme="pirate_tale", problem="comma", fix="straighten",
                        captain="Lily", captain_gender="girl", mate="Tom", mate_gender="boy",
                        parent="mother", delay=0),
            StoryParams(theme="harbor", problem="twist", fix="ask_adult",
                        captain="Max", captain_gender="boy", mate="Mia", mate_gender="girl",
                        parent="father", delay=1),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
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
        if header:
            print(header)
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_invalid_fix(FIXES[args.fix]))
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, problem, fix = rng.choice(sorted(combos))
    captain_gender = args.captain_gender if hasattr(args, "captain_gender") else None
    captain = rng.choice(GIRL_NAMES + BOY_NAMES)
    mate = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != captain])
    return StoryParams(
        theme=theme,
        problem=problem,
        fix=fix,
        captain=args.captain if hasattr(args, "captain") and args.captain else captain,
        captain_gender="girl" if captain in GIRL_NAMES else "boy",
        mate=args.mate if hasattr(args, "mate") and args.mate else mate,
        mate_gender="girl" if mate in GIRL_NAMES else "boy",
        parent=args.parent or rng.choice(["mother", "father"]),
        delay=rng.randint(0, 1),
    )


if __name__ == "__main__":
    main()
