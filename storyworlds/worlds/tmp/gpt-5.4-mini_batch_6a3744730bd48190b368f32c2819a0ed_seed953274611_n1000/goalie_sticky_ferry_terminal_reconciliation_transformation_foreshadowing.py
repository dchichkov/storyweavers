#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/goalie_sticky_ferry_terminal_reconciliation_transformation_foreshadowing.py
===========================================================================================================

A bedtime-story storyworld set in a ferry terminal: a small child, a sticky
mistake, a gentle reconciliation, a hopeful transformation, and a foreshadowed
future at the waterline.

The story world is intentionally small and classical:
- a child is playing a pretend game at a ferry terminal,
- sticky hands or a sticky thing causes a social snag,
- a grown-up or friend helps repair the moment,
- something transforms from messy to useful,
- and a small foreshadowed image hints at the next calm outing.

The required seed words are included naturally in the domain:
- goalie
- sticky

Narrative instruments:
- reconciliation
- transformation
- foreshadowing

Style:
- bedtime story
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
QUALITY_MIN = 2

GENTLE_TRAITS = {"gentle", "patient", "kind", "careful", "calm"}


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
    sticky: bool = False
    clean: bool = True
    transformable: bool = False

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
class Setting:
    id: str
    place: str
    mood: str
    detail: str
    foreshadow: str


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    role: str
    transform_to: str
    transform_phrase: str
    sticky_result: str
    tag: str = ""


@dataclass
class Problem:
    id: str
    label: str
    source: str
    mess: str
    can_reconcile: bool = True
    quality: int = 3
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    action: str
    result: str
    quality: int
    tags: set[str] = field(default_factory=set)


@dataclass
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_sticky(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if not e.sticky or e.meters["mess"] < THRESHOLD:
            continue
        sig = ("sticky", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("terminal").meters["mess"] += 1
        world.get("caretaker").memes["worry"] += 1
        out.append("__sticky__")
    return out


def _r_reconcile(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["apology"] < THRESHOLD or helper.memes["forgiveness"] < THRESHOLD:
        return []
    sig = ("reconcile",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["warmth"] += 1
    helper.memes["warmth"] += 1
    return ["__reconcile__"]


CAUSAL_RULES = [Rule("sticky", _r_sticky), Rule("reconcile", _r_reconcile)]


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


def valid_problem(problem: Problem) -> bool:
    return problem.quality >= QUALITY_MIN and problem.can_reconcile


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for problem_id, problem in PROBLEMS.items():
            for toy_id, toy in TOYS.items():
                if problem.id == "lost_glove" and toy.role == "ball":
                    combos.append((setting, problem_id, toy_id))
                elif problem.id == "sticky_mess" and toy.role in {"goalie_glove", "lantern"}:
                    combos.append((setting, problem_id, toy_id))
    return combos


def reasonableness(problem: Problem, toy: Toy) -> bool:
    return problem.quality >= QUALITY_MIN and valid_problem(problem) and toy.transform_to


def predict(world: World, problem: Problem, toy: Toy) -> dict:
    sim = world.copy()
    apply_problem(sim, sim.get("child"), problem, toy, narrate=False)
    return {
        "mess": sim.get("toy").meters["mess"],
        "worry": sim.get("caretaker").memes["worry"],
    }


def apply_problem(world: World, child: Entity, problem: Problem, toy: Toy, narrate: bool = True) -> None:
    child.meters["mess"] += 1
    if problem.id == "sticky_mess":
        child.sticky = True
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"At the ferry terminal, {child.id} and {helper.id} listened to the water breathe against the dock. "
        f"{setting.detail}"
    )
    world.say(
        f"The little station looked sleepy and kind, with warm lights, soft benches, and a view of the gray sea."
    )


def play(world: World, child: Entity, toy: Toy) -> None:
    world.say(
        f"{child.id} played goalie with {toy.phrase}, making brave little saves against an imaginary wave."
    )
    world.say(
        f"{toy.label.capitalize()} felt fun in {child.pronoun('possessive')} hands, and the whole waiting room felt like a quiet game."
    )


def trouble(world: World, child: Entity, helper: Entity, problem: Problem, toy: Toy) -> None:
    child.memes["concern"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"Then came the {problem.label}. {problem.source} left {problem.mess} on {toy.label}, and the sticky patch would not let go."
    )
    world.say(
        f"{helper.id} frowned a little, but {helper.id} did not scold. In bedtime-story voices, {helper.id} only asked for a pause."
    )


def apologize(world: World, child: Entity, helper: Entity) -> None:
    child.memes["apology"] += 1
    helper.memes["forgiveness"] += 1
    world.say(
        f"{child.id} blinked, then said sorry in a small, brave voice. {helper.id} hugged {child.pronoun('object')} and forgave {child.pronoun('object')} at once."
    )


def transform(world: World, toy: Toy, child: Entity) -> None:
    toy_ent = world.get("toy")
    toy_ent.clean = True
    toy_ent.meters["mess"] = 0.0
    toy_ent.transformable = True
    world.say(
        f"Together they washed and wiped until the sticky spots came off. What had been a messy glove became {toy.transform_phrase}."
    )
    world.say(
        f"By the end, {toy.label} was not ruined at all; it had transformed into something neat and ready for the next game."
    )
    child.memes["warmth"] += 1


def foreshadow(world: World, setting: Setting, toy: Toy) -> None:
    world.say(
        f"As the ferry's horn sounded far off, {setting.foreshadow}."
    )
    world.say(
        f"{child_name_from_world(world)} looked out at the dark water and smiled, already imagining the next morning's calm crossing."
    )


def child_name_from_world(world: World) -> str:
    return world.get("child").id


def tell(setting: Setting, problem: Problem, toy: Toy,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Gran", helper_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    caret = world.add(Entity(id="caretaker", kind="character", type=helper_gender, role="caretaker"))
    terminal = world.add(Entity(id="terminal", type="place", label="the ferry terminal"))
    toy_ent = world.add(Entity(id="toy", type="toy", label=toy.label, sticky=True, clean=False))
    world.facts["setting"] = setting
    world.facts["problem"] = problem
    world.facts["toy_cfg"] = toy
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["caretaker"] = caret

    setup(world, child, helper, setting)
    world.para()
    play(world, child, toy)
    trouble(world, child, helper, problem, toy)
    world.para()
    apologize(world, child, helper)
    transform(world, toy, child)
    world.para()
    foreshadow(world, setting, toy)
    world.facts["outcome"] = "reconciled_transformed"
    return world


SETTINGS = {
    "ferry_terminal": Setting(
        id="ferry_terminal",
        place="the ferry terminal",
        mood="sleepy and kind",
        detail="A ferry terminal is a place where people wait for boats that carry them over the water.",
        foreshadow="the next ferry would arrive with silver windows and a bright blue flag",
    ),
    "harbor_terminal": Setting(
        id="harbor_terminal",
        place="the harbor terminal",
        mood="soft and quiet",
        detail="The harbor terminal hummed gently while gulls stitched the sky above the boats.",
        foreshadow="a tiny ferry would soon bob into view with a cheerful whistle",
    ),
}

PROBLEMS = {
    "sticky_mess": Problem(
        id="sticky_mess",
        label="sticky mess",
        source="a dropped honey bun",
        mess="a sticky smear",
        quality=3,
        tags={"sticky"},
    ),
    "lost_glove": Problem(
        id="lost_glove",
        label="lost glove",
        source="a windy bench",
        mess="a small fuss",
        quality=2,
        tags={"goalie"},
    ),
}

TOYS = {
    "goalie_glove": Toy(
        id="goalie_glove",
        label="goalie glove",
        phrase="a tiny goalie glove",
        role="goalie_glove",
        transform_to="clean game prop",
        transform_phrase="a clean goalie glove, soft as a cloud",
        sticky_result="sticky and clumsy",
        tag="goalie",
    ),
    "ferry_ticket": Toy(
        id="ferry_ticket",
        label="ferry ticket",
        phrase="a folded ferry ticket",
        role="lantern",
        transform_to="keepsake",
        transform_phrase="a little keepsake bookmark",
        sticky_result="soggy and bent",
        tag="ticket",
    ),
    "lantern": Toy(
        id="lantern",
        label="lantern",
        phrase="a small lantern",
        role="lantern",
        transform_to="night-light",
        transform_phrase="a warm night-light for the window",
        sticky_result="smudged but shining",
        tag="light",
    ),
}

CURATED = [
    StoryParams(
        setting="ferry_terminal",
        problem="sticky_mess",
        toy="goalie_glove",
        child_name="Mina",
        child_gender="girl",
        helper_name="Gran",
        helper_gender="woman",
        seed=None,
    ),
    StoryParams(
        setting="harbor_terminal",
        problem="lost_glove",
        toy="ferry_ticket",
        child_name="Noah",
        child_gender="boy",
        helper_name="Dad",
        helper_gender="man",
        seed=None,
    ),
    StoryParams(
        setting="ferry_terminal",
        problem="sticky_mess",
        toy="lantern",
        child_name="Ivy",
        child_gender="girl",
        helper_name="Mom",
        helper_gender="woman",
        seed=None,
    ),
]


@dataclass
class StoryParams:
    setting: str
    problem: str
    toy: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    problem = f["problem"]
    toy = f["toy_cfg"]
    return [
        f"Write a bedtime story set at {setting.place} that includes the words goalie and sticky.",
        f"Tell a gentle story where a child uses {toy.label} like a goalie toy, gets into a sticky problem, then makes up with a helper.",
        f"Write a soft reconciliation story in a ferry terminal where a sticky mistake turns into a transformation and ends with a hopeful hint about the next ferry.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    setting = f["setting"]
    problem = f["problem"]
    toy = f["toy_cfg"]
    qa = [
        ("Where does the story happen?",
         f"It happens at {setting.place}. The terminal is a quiet place where people wait for ferries on the water."),
        ("What game was the child playing?",
         f"{child.id} was playing goalie with {toy.phrase}. The game made the waiting feel gentle and fun."),
        ("What problem happened?",
         f"A sticky mess happened when {problem.source} left {problem.mess} on the {toy.label}. That is why the child and helper had to pause and fix it."),
        ("How did they feel at the end?",
         f"They felt warm and peaceful after they made up. The apology and hug turned the moment from a worry into a bedtime-sweet ending."),
    ]
    if f.get("outcome") == "reconciled_transformed":
        qa.append((
            "How was the toy transformed?",
            f"They washed and wiped it until it became {toy.transform_phrase}. The toy changed from messy to neat, so it was ready for the next game."
        ))
        qa.append((
            "What foreshadowing is in the story?",
            f"The story hints that the next ferry will arrive soon, with silver windows and a bright blue flag. That little hint makes the ending feel calm and expectant."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a ferry terminal?",
         "A ferry terminal is a place where people wait for ferries. It usually has docks, signs, and a view of the water."),
        ("What does goalie mean?",
         "A goalie is a player who tries to stop the ball from getting through. In a pretend game, a child can act like a goalie with a toy or a glove."),
        ("What does sticky mean?",
         "Sticky means something clings and does not come off easily. Honey, syrup, and glue can all feel sticky."),
        ("What is reconciliation?",
         "Reconciliation is when people make up after a problem. They feel kinder again and can be together peacefully."),
        ("What is transformation?",
         "Transformation means something changes into a new form or feels different in an important way. A messy thing can become clean and useful again."),
        ("What is foreshadowing?",
         "Foreshadowing is a small hint about what might happen later. It helps the ending feel connected to the rest of the story."),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.sticky:
            bits.append("sticky=True")
        if not e.clean:
            bits.append("clean=False")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def choose_problem(rng: random.Random, args: argparse.Namespace) -> tuple[str, str, str]:
    combos = valid_combos()
    if args.setting or args.problem or args.toy:
        combos = [c for c in combos if (args.setting is None or c[0] == args.setting)
                  and (args.problem is None or c[1] == args.problem)
                  and (args.toy is None or c[2] == args.toy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    return rng.choice(sorted(combos))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime ferry-terminal storyworld with a goalie and a sticky turn.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--child-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting, problem, toy = choose_problem(rng, args)
    child_name = args.child_name or rng.choice(["Mina", "Ivy", "Lia", "Nora", "Theo", "Noah"])
    helper_name = args.helper_name or rng.choice(["Gran", "Mom", "Dad", "Aunt June", "Uncle Ben"])
    child_gender = "girl" if child_name in {"Mina", "Ivy", "Lia", "Nora"} else "boy"
    helper_gender = "woman" if helper_name in {"Gran", "Mom", "Aunt June"} else "man"
    return StoryParams(
        setting=setting,
        problem=problem,
        toy=toy,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.toy not in TOYS:
        raise StoryError("(Invalid StoryParams keys.)")
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    toy = TOYS[params.toy]
    if not reasonableness(problem, toy):
        raise StoryError("(This problem/toy combination is not reasonable enough for a story.)")
    world = tell(setting, problem, toy, params.child_name, params.child_gender, params.helper_name, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


ASP_RULES = r"""
valid(S,P,T) :- setting(S), problem(P), toy(T), compatible(P,T).
compatible(sticky_mess, goalie_glove) :- toy(goalie_glove).
compatible(sticky_mess, lantern) :- toy(lantern).
compatible(lost_glove, ferry_ticket) :- toy(ferry_ticket).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid in TOYS:
        lines.append(asp.fact("toy", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, toy=None, child_name=None, helper_name=None), random.Random(777)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"FAILED smoke test: {exc}")
        return 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (setting, problem, toy) combos:")
        for setting, problem, toy in asp_valid_combos():
            print(f"  {setting:15} {problem:12} {toy}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} at {p.setting} ({p.problem}, {p.toy})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
