#!/usr/bin/env python3
"""
A tiny fable-like story world about a previous quarrel and its reconciliation.

The premise is simple: one animal remembers a previous slight, the tension grows
into a refusal to help, and the turn comes when both sides choose to mend what
was broken together. The world model tracks whether the old hurt still weighs on
them, whether the shared task is possible, and how reconciliation changes the
ending image.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "animal"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def name(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    feature: str
    affords: set[str] = field(default_factory=set)


@dataclass
class FableTask:
    id: str
    verb: str
    gerund: str
    risk: str
    fix: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Token:
    label: str
    phrase: str
    region: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    a = world.entities["A"]
    b = world.entities["B"]
    if a.memes.get("stubborn", 0) >= THRESHOLD and b.memes.get("stubborn", 0) >= THRESHOLD:
        if ("soften",) not in world.fired:
            world.fired.add(("soften",))
            a.memes["hurt"] = max(0.0, a.memes.get("hurt", 0) - 1)
            b.memes["hurt"] = max(0.0, b.memes.get("hurt", 0) - 1)
            out.append("The old hurt began to feel smaller.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    a = world.entities["A"]
    b = world.entities["B"]
    if a.memes.get("apology", 0) >= THRESHOLD and b.memes.get("apology", 0) >= THRESHOLD:
        sig = ("reconcile",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        a.memes["peace"] = 1
        b.memes["peace"] = 1
        a.memes["hurt"] = 0
        b.memes["hurt"] = 0
        out.append("A small peace returned between them.")
    return out


CAUSAL_RULES = [_r_soften, _r_reconcile]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    place: str
    task: str
    token: str
    name_a: str
    name_b: str
    seed: Optional[int] = None


SETTINGS = {
    "lane": Setting(place="the lane", feature="stone arch", affords={"carry"}),
    "meadow": Setting(place="the meadow", feature="little brook", affords={"carry"}),
    "orchard": Setting(place="the orchard", feature="old fence", affords={"carry"}),
}

TASKS = {
    "carry": FableTask(
        id="carry",
        verb="carry the basket together",
        gerund="carrying the basket",
        risk="the basket might fall",
        fix="lift it carefully together",
        keyword="basket",
        tags={"shared", "work", "peace"},
    )
}

TOKENS = {
    "basket": Token(label="basket", phrase="a woven basket of apples", region="hands"),
    "lamp": Token(label="lamp", phrase="a small lamp with a brass handle", region="hands"),
    "book": Token(label="book", phrase="a thin book of tales", region="hands"),
}

NAMES_A = ["Toby", "Mira", "Pip", "June", "Bram"]
NAMES_B = ["Nell", "Otis", "Luna", "Reed", "Bess"]
TRAITS = ["kind", "proud", "thoughtful", "stubborn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            for token_id in TOKENS:
                combos.append((place, task_id, token_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable world about a previous quarrel and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.token is None or c[2] == args.token)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, token = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        task=task,
        token=token,
        name_a=args.name_a or rng.choice(NAMES_A),
        name_b=args.name_b or rng.choice(NAMES_B),
    )


def tell(setting: Setting, task: FableTask, token: Token, name_a: str, name_b: str) -> World:
    w = World(setting)
    a = w.add(Entity(id="A", label=name_a, traits=["little", "stubborn"], memes={"hurt": 1, "stubborn": 1}))
    b = w.add(Entity(id="B", label=name_b, traits=["little", "thoughtful"], memes={"hurt": 1, "stubborn": 1}))
    w.add(Entity(id="token", kind="thing", type=token.label, label=token.label, phrase=token.phrase))

    w.say(f"Once, in {setting.place}, {a.name} and {b.name} shared {token.phrase}.")
    w.say(f"That story had a previous quarrel in it, and both still remembered it.")
    w.para()
    w.say(f"One day they tried to {task.verb}, but {a.name} and {b.name} each thought the other should go first.")
    a.memes["refusal"] = 1
    b.memes["refusal"] = 1
    w.say(f"Because of that, the work stopped, and the basket sat still beside the {setting.feature}.")
    w.para()
    w.say(f"Then {a.name} saw that {task.risk}, and {b.name} saw the same thing.")
    a.memes["apology"] = 1
    b.memes["apology"] = 1
    w.say(f"{a.name} said sorry for the earlier sharp words.")
    w.say(f"{b.name} said sorry too, because pride had made the old hurt grow.")
    propagate(w, narrate=True)
    w.para()
    w.say(f"Together they chose to {task.fix}, and they lifted the basket with careful hands.")
    w.say(f"By the end, the previous grudge was gone, and {a.name} and {b.name} walked on as friends beneath the {setting.feature}.")
    w.facts.update(a=a, b=b, setting=setting, task=task, token=token, reconciled=True)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, task, token, setting = f["a"], f["b"], f["task"], f["token"], f["setting"]
    return [
        f'Write a short fable about a previous quarrel and a kind reconciliation using the word "{token.label}".',
        f"Tell a gentle story where {a.name} and {b.name} must {task.verb} in {setting.place} but first make peace.",
        f"Write a child-friendly fable in which two friends remember a previous mistake and then choose to work together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, task, token, setting = f["a"], f["b"], f["task"], f["token"], f["setting"]
    return [
        QAItem(
            question=f"Who was in the story in {setting.place}?",
            answer=f"The story was about {a.name} and {b.name}, two little friends who had a previous quarrel but later reconciled.",
        ),
        QAItem(
            question=f"What did {a.name} and {b.name} want to do together?",
            answer=f"They wanted to {task.verb}, but first they had to stop being stubborn and make peace.",
        ),
        QAItem(
            question=f"What happened after they said sorry?",
            answer=f"They chose to {task.fix} and carried {token.phrase} together, so the old hurt faded away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who have argued or hurt each other make peace again and become friendly.",
        ),
        QAItem(
            question="What does it mean to apologize?",
            answer="To apologize means to say sorry for hurting someone or doing something unkind.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {e.name} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="lane", task="carry", token="basket", name_a="Toby", name_b="Nell"),
    StoryParams(place="meadow", task="carry", token="lamp", name_a="Mira", name_b="Otis"),
    StoryParams(place="orchard", task="carry", token="book", name_a="Pip", name_b="Bess"),
]


ASP_RULES = r"""
valid(Place, Task, Token) :- affords(Place, Task), token(Token), task(Task).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", place, a))
    for task in TASKS:
        lines.append(asp.fact("task", task))
    for token in TOKENS:
        lines.append(asp.fact("token", token))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TASKS[params.task], TOKENS[params.token], params.name_a, params.name_b)
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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, task, token) combos:\n")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name_a} and {p.name_b}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
