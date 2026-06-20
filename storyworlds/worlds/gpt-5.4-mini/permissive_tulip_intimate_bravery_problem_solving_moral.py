#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/permissive_tulip_intimate_bravery_problem_solving_moral.py
==========================================================================================

A standalone story world for a small folk-tale domain: a child, a curious tulip,
an intimate little secret, a brave choice, a practical fix, and a moral value
learned at the end.

The world is intentionally tiny and classical:
- a child wants something gentle and secret,
- a problem blocks the way,
- bravery and problem solving change the state,
- a moral value is learned and narrated through the ending image.

The required seed words appear in the story naturally:
- permissive
- tulip
- intimate

The style aims at a warm folk tale voice.
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVERY_THRESHOLD = 1.0
PROBLEM_THRESHOLD = 1.0
MORAL_THRESHOLD = 1.0


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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "queen": "queen", "king": "king"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    mood: str
    hidden: str
    has_stream: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Problem:
    id: str
    noun: str
    cause: str
    effect: str
    risk: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Solution:
    id: str
    method: str
    text: str
    result: str
    power: int

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Moral:
    id: str
    value: str
    lesson: str
    closing: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_problem(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    problem = world.get("problem")
    if child.memes["curiosity"] >= THRESHOLD and problem.meters["blocked"] >= THRESHOLD:
        sig = ("problem", problem.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] += 1
            out.append("__problem__")
    return out


def _r_solution(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    problem = world.get("problem")
    solution = world.get("solution")
    if child.memes["bravery"] >= BRAVERY_THRESHOLD and problem.meters["blocked"] >= THRESHOLD:
        sig = ("solution", solution.id)
        if sig not in world.fired:
            world.fired.add(sig)
            problem.meters["blocked"] = 0.0
            problem.meters["solved"] += 1
            child.memes["relief"] += 1
            out.append("__solution__")
    return out


def _r_moral(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    moral = world.get("moral")
    if moral.meters["heard"] >= THRESHOLD and child.memes["understanding"] < THRESHOLD:
        sig = ("moral", moral.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["understanding"] += 1
            child.memes["kindness"] += 1
            out.append("__moral__")
    return out


CAUSAL_RULES = [
    Rule("problem", _r_problem),
    Rule("solution", _r_solution),
    Rule("moral", _r_moral),
]


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


def _do_action(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    problem = world.get("problem")
    solution = world.get("solution")
    child.memes["bravery"] += 1
    child.memes["curiosity"] += 1
    problem.meters["blocked"] += 1
    child.meters["steps"] += 1
    if narrate:
        world.say(f"The child stepped forward, and the little trouble by the tulip patch grew clear.")
    propagate(world, narrate=narrate)
    if problem.meters["blocked"] >= THRESHOLD and narrate:
        world.say(f"The way still seemed shut, like a gate that would not open.")
    if solution.power >= 1:
        problem.meters["blocked"] = 0.0
        problem.meters["solved"] += 1
        child.memes["relief"] += 1


def predict_world(world: World) -> dict:
    sim = world.copy()
    _do_action(sim, narrate=False)
    return {
        "blocked": sim.get("problem").meters["blocked"],
        "solved": sim.get("problem").meters["solved"],
        "understanding": sim.get("child").memes["understanding"],
    }


def tell(setting: Setting, problem: Problem, solution: Solution, moral: Moral,
         child_name: str, child_gender: str, guardian_name: str, guardian_gender: str,
         seed_word: str = "tulip", intimate_word: str = "intimate",
         permissive_word: str = "permissive") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="hero"))
    guardian = world.add(Entity(id=guardian_name, kind="character", type=guardian_gender, role="guardian"))
    prob = world.add(Entity(id="problem", kind="thing", type="thing", label=problem.noun, role="problem"))
    solv = world.add(Entity(id="solution", kind="thing", type="thing", label=solution.method, role="solution"))
    mr = world.add(Entity(id="moral", kind="thing", type="thing", label=moral.value, role="moral"))

    child.memes["curiosity"] = 1.0
    child.memes["bravery"] = 0.0
    guardian.memes["permissive"] = 1.0
    prob.meters["blocked"] = 1.0
    mr.meters["heard"] = 0.0

    world.say(
        f"Once in a small folk tale village, {child.id} lived beside a {setting.mood} lane where a {setting.hidden} hid among the roots."
    )
    world.say(
        f"By the gate grew a {seed_word}, and beside it the child kept an {intimate_word} little wish tucked close to the heart."
    )
    world.say(
        f"{guardian.id}, {permissive_word} and kind, let {child.id} listen to the wind and wonder for a while."
    )

    world.para()
    pred = predict_world(world)
    world.facts["prediction"] = pred
    world.say(
        f"One day, {child.id} saw that the path to the {setting.hidden} was blocked by the trouble of {problem.cause}."
    )
    world.say(
        f"{child.id} wished to solve it, but first {child.pronoun()} felt the prick of fear, because {problem.risk}."
    )
    world.say(
        f"Still, {child.id} gathered {child.pronoun('possessive')} courage and looked hard at the path."
    )

    _do_action(world, narrate=True)

    world.para()
    if world.get("problem").meters["solved"] >= THRESHOLD:
        world.say(
            f"Then {solution.text}, and the way opened at once."
        )
        world.say(
            f"{guardian.id} smiled to see that the child had used brave thinking as well as brave feet."
        )
        mr.meters["heard"] = 1.0
        world.say(
            f"{moral.lesson} {moral.closing}"
        )
        propagate(world, narrate=True)
        world.say(
            f"In the end, the {seed_word} swayed in the breeze, and the child walked on with a gentler heart and a clearer mind."
        )
    else:
        world.say(
            f"Yet the trouble would not move, and the child had to wait for wiser help."
        )

    world.facts.update(
        child=child,
        guardian=guardian,
        problem=prob,
        solution=solv,
        moral=mr,
        setting=setting,
        outcome="solved" if world.get("problem").meters["solved"] >= THRESHOLD else "blocked",
        seed_word=seed_word,
        intimate_word=intimate_word,
        permissive_word=permissive_word,
    )
    return world


SETTINGS = {
    "garden_path": Setting("garden_path", "garden path", "gentle", "stone arch", has_stream=False),
    "orchard_lane": Setting("orchard_lane", "orchard lane", "quiet", "low gate", has_stream=False),
    "brook_side": Setting("brook_side", "brook side", "soft", "reed fence", has_stream=True),
}

PROBLEMS = {
    "fallen_branch": Problem("fallen_branch", "fallen branch", "a storm had dropped a heavy branch", "the branch had blocked the path", "the child could not reach the tulip patch"),
    "mud_pile": Problem("mud_pile", "mud pile", "rain had made a muddy heap", "the mud pile had sealed the way", "small shoes would slip and sink"),
    "bee_riddle": Problem("bee_riddle", "bee riddle", "the child did not know which flowers were safe to touch", "the child was stuck, thinking too long", "the tulips might be disturbed"),
}

SOLUTIONS = {
    "pushing": Solution("pushing", "push the branch aside", "the child pushed the branch aside with both hands", "the branch rolled off the path", 1),
    "bridging": Solution("bridging", "lay reeds across the mud", "the child laid reeds across the mud and stepped carefully", "the muddy place became a little bridge", 1),
    "asking": Solution("asking", "ask the gardener kindly", "the child asked the gardener kindly for help", "the gardener showed the safe way around", 1),
}

MORALS = {
    "kind_courage": Moral("kind_courage", "kind courage", "Bravery is brightest when it stays kind and calm.", "The best brave deed is the one that helps without hurting."),
    "clear_eyes": Moral("clear_eyes", "clear eyes", "A problem is smaller when it is looked at closely.", "Thinking clearly can make a hard thing simple."),
    "gentle_hand": Moral("gentle_hand", "gentle hand", "A gentle hand can solve what a hasty hand would harm.", "So the child learned to be brave, thoughtful, and gentle too."),
}

GIRL_NAMES = ["May", "Rose", "Anna", "Lina", "Mira", "Elsie"]
BOY_NAMES = ["Jon", "Alf", "Pip", "Ned", "Otto", "Finn"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    problem: str
    solution: str
    moral: str
    child_name: str
    child_gender: str
    guardian_name: str
    guardian_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about bravery, problem solving, and moral value.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--moral", choices=MORALS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--guardian-name")
    ap.add_argument("--guardian-gender", choices=["woman", "man", "girl", "boy"])
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid in PROBLEMS:
            for sol in SOLUTIONS:
                for mid in MORALS:
                    combos.append((sid, pid, sol, mid))
    return combos


def explain_rejection() -> str:
    return "(No story: that combination does not give a clear problem and a fitting solution.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.solution is None or c[2] == args.solution)
              and (args.moral is None or c[3] == args.moral)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, problem, solution, moral = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    guardian_gender = args.guardian_gender or rng.choice(["woman", "man"])
    guardian_name = args.guardian_name or rng.choice(GIRL_NAMES + BOY_NAMES)
    return StoryParams(setting, problem, solution, moral, child_name, child_gender, guardian_name, guardian_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale story for a young child that includes the words "permissive", "tulip", and "intimate".',
        f"Tell a gentle tale where {f['child'].id} meets a small problem near the tulip patch and solves it with brave thinking.",
        f"Write a story about {f['child'].id} and {f['guardian'].id} that ends with the moral of {f['moral'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    guardian = f["guardian"]
    problem = f["problem"]
    solution = f["solution"]
    moral = f["moral"]
    setting = f["setting"]
    pred = f.get("prediction", {})
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id}, a small {child.type}, and {guardian.id}, who was permissive and kind. They live in a folk-tale village near the {setting.place}.",
        ),
        QAItem(
            question="What problem did the child face?",
            answer=f"The child faced {problem.noun}. It blocked the way to the tulip patch, so the child had to think carefully before going on.",
        ),
        QAItem(
            question="How did the child solve the problem?",
            answer=f"{solution.text.capitalize()}. That worked because the child was brave enough to try and thoughtful enough to choose a useful fix.",
        ),
        QAItem(
            question="What did the child learn at the end?",
            answer=f"{moral.lesson} {moral.closing} The child ended wiser, with a calmer heart and a better way forward.",
        ),
        QAItem(
            question="Why was the path hard at first?",
            answer=f"It was hard because {problem.effect}. The prediction showed that the block would remain until someone used a good solution.",
        ),
        QAItem(
            question="What did the prediction say before the action?",
            answer=f"It showed the trouble was still blocked at first, which meant the child needed bravery and problem solving instead of rushing. That is why the answer came from steady thought, not from haste.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"tulip", "bravery", "problem_solving", "moral_value"}
    out = []
    knowledge = {
        "tulip": ("What is a tulip?", "A tulip is a flower with a smooth stem and a bright cup-shaped bloom."),
        "bravery": ("What is bravery?", "Bravery means doing what is right or needed even when you feel a little afraid."),
        "problem_solving": ("What is problem solving?", "Problem solving means looking at a difficulty and finding a useful way through it."),
        "moral_value": ("What is a moral value?", "A moral value is a good idea about how to live, like kindness, honesty, or courage."),
    }
    for key in ["tulip", "bravery", "problem_solving", "moral_value"]:
        q, a = knowledge[key]
        out.append(QAItem(q, a))
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,L,M) :- setting(S), problem(P), solution(L), moral(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for lid in SOLUTIONS:
        lines.append(asp.fact("solution", lid))
    for mid in MORALS:
        lines.append(asp.fact("moral", mid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams("garden_path", "fallen_branch", "pushing", "kind_courage", "May", "girl", "Mira", "woman"),
    StoryParams("orchard_lane", "mud_pile", "bridging", "clear_eyes", "Finn", "boy", "Anna", "woman"),
    StoryParams("brook_side", "bee_riddle", "asking", "gentle_hand", "Rose", "girl", "Jon", "man"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        PROBLEMS[params.problem],
        SOLUTIONS[params.solution],
        MORALS[params.moral],
        params.child_name,
        params.child_gender,
        params.guardian_name,
        params.guardian_gender,
    )
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


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH: ASP and Python valid-combos differ.")
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"MISMATCH: ordinary generation failed: {exc}")
        return 1
    print(f"OK: ASP parity and story generation passed ({len(py)} combos).")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:")
        for row in combos:
            print("  " + " ".join(row))
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
            header = f"### {p.child_name}: {p.setting} / {p.problem} / {p.moral}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
