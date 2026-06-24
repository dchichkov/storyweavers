#!/usr/bin/env python3
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "wolf", "he", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"hare", "she", "girl", "mouse"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    name: str
    kind: str
    job: str
    service: str
    budget: int
    fee: int
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HEROES = [
    ("Fox", "fox"),
    ("Hare", "hare"),
    ("Mouse", "mouse"),
]
JOBS = [
    ("garden service", "service"),
    ("market service", "service"),
    ("library service", "service"),
]
SERVICES = {
    "garden": "garden service",
    "market": "market service",
    "library": "library service",
}
FEES = [3, 4, 5, 6]
BUDGETS = [1, 2, 3, 4, 5, 6, 7, 8]


ASP_RULES = r"""
need_enroll(P) :- budget(P), fee(P, F), F =< B.
can_enroll(P) :- need_enroll(P), service(S), useful(S).
fair_choice(P) :- can_enroll(P), pays(P, F).
#show need_enroll/1.
#show can_enroll/1.
#show fair_choice/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name, kind in HEROES:
        lines.append(asp.fact("hero", kind))
    for k, svc in SERVICES.items():
        lines.append(asp.fact("service", svc.replace(" ", "_")))
        lines.append(asp.fact("useful", svc.replace(" ", "_")))
    for b in BUDGETS:
        lines.append(asp.fact("budget", b))
    for f in FEES:
        lines.append(asp.fact("fee", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like story world about service, budgetary worries, and enroll.")
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=[k for _, k in HEROES])
    ap.add_argument("--job", choices=list(SERVICES))
    ap.add_argument("--service", choices=list(SERVICES))
    ap.add_argument("--budget", type=int)
    ap.add_argument("--fee", type=int)
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
    name, kind = rng.choice(HEROES)
    job = args.job or rng.choice(list(SERVICES))
    service = args.service or SERVICES[job]
    budget = args.budget if args.budget is not None else rng.choice(BUDGETS)
    fee = args.fee if args.fee is not None else rng.choice(FEES)
    if args.kind:
        kind = args.kind
    if args.name:
        name = args.name
    if args.budget is not None and args.fee is not None and args.budget < args.fee:
        raise StoryError("The budget is too small for the fee; the animal cannot honestly enroll.")
    if args.job and args.service and SERVICES[args.job] != SERVICES[args.service]:
        raise StoryError("The chosen job and service do not match.")
    return StoryParams(name=name, kind=kind, job=job, service=service, budget=budget, fee=fee)


def generate(params: StoryParams) -> StorySample:
    w = World()
    hero = w.add(Entity(id=params.name, kind="character", type=params.kind, label=params.name))
    clerk = w.add(Entity(id="Clerk", kind="character", type="mouse", label="the clerk"))
    cash = w.add(Entity(id="Coins", type="thing", label="coins"))
    service = w.add(Entity(id="Service", type="thing", label=params.service, phrase=params.service))
    hero.meters["budget"] = params.budget
    service.meters["fee"] = params.fee

    w.say(f"Once there was a little {params.kind} named {params.name}.")
    w.say(f"{params.name} loved useful work, and {params.name} loved service, service, service.")
    w.say(f"One bright day, {params.name} heard about the {params.service} and wanted to enroll.")
    w.para()
    w.say(f'"To enroll, you need {params.fee} coins," said {clerk.label}.')
    w.say(f'"I have only {params.budget} coins," said {params.name}.')
    w.say(f'"Then you cannot enroll yet," said the clerk. "Budgetary worries are real worries."')
    w.say(f"{params.name} nodded. {params.name} counted the coins again: one, two, three, and more if work was done.")
    w.para()
    if params.budget >= params.fee:
        hero.meters["budget"] -= params.fee
        hero.memes["hope"] = 1
        w.say(f'"I can earn the rest by helping," said {params.name}. "I can serve, serve, serve."')
        w.say(f"{params.name} carried water, swept leaves, and carried seeds. The service was steady, and the coins grew steady too.")
        hero.meters["budget"] = params.budget
        w.say(f'At last, {params.name} had enough. "Now I may enroll," said {params.name}.')
        w.say(f'"Yes," said the clerk. "Now you may enroll."')
        w.say(f"So {params.name} enrolled in the {params.service}, and the little {params.kind} worked with a happy heart.")
        w.say("And from that day on, the animal remembered: a fair fee can be met by fair work.")
    else:
        w.say(f'"I will work first," said {params.name}. "I will serve, serve, serve until I can pay."')
        w.say(f"{params.name} helped with bags, swept paths, and fetched water. The coins clinked little by little.")
        w.say(f"By evening, {params.name} still could not enroll, but the path to enroll had begun.")
        w.say("The little animal learned that patience can grow a budget as surely as rain grows a field.")
    w.para()
    w.say("Moral: Service is sweetest when patience and honest work help pay the way.")

    w.facts.update(hero=hero, clerk=clerk, service=service, params=params)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_qa(w),
        world=w,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a short fable about a {p.kind} who wants to enroll in a {p.service}.",
        f"Tell a gentle story where budgetary worries keep {p.name} from enrolling right away.",
        f"Write a child-friendly dialogue story using the words service, budgetary, and enroll.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question=f"Who wanted to enroll in the {p.service}?",
            answer=f"{p.name}, the little {p.kind}, wanted to enroll in the {p.service}.",
        ),
        QAItem(
            question="Why did the clerk say the animal could not enroll yet?",
            answer=f"The clerk said that because {p.name} had only {p.budget} coins, but the fee was {p.fee} coins.",
        ),
        QAItem(
            question="What did the animal do to solve the budgetary problem?",
            answer=f"{p.name} chose to work and serve, serve, serve until enough coins were ready.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is service?",
            answer="Service is helpful work done for other people or for a community.",
        ),
        QAItem(
            question="What does budgetary mean?",
            answer="Budgetary means it has to do with money, spending, or a budget.",
        ),
        QAItem(
            question="What does enroll mean?",
            answer="Enroll means to join a class, club, or group officially.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], ""]
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def valid_pairs() -> list[tuple[int, int]]:
    return [(b, f) for b in BUDGETS for f in FEES if b >= f]


def asp_verify() -> int:
    import asp
    prog = asp_program("#show need_enroll/1.\n#show can_enroll/1.\n")
    model = asp.one_model(prog)
    need = set(asp.atoms(model, "need_enroll"))
    can = set(asp.atoms(model, "can_enroll"))
    py = set((b,) for b, f in valid_pairs())
    if need == py and can == py:
        print(f"OK: ASP parity matches Python ({len(py)} feasible budget/fee pairs).")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


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
    StoryParams(name="Fenn", kind="fox", job="garden", service="garden", budget=2, fee=4),
    StoryParams(name="Mira", kind="hare", job="market", service="market", budget=5, fee=4),
    StoryParams(name="Pip", kind="mouse", job="library", service="library", budget=3, fee=3),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show need_enroll/1.\n#show can_enroll/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show need_enroll/1.\n#show can_enroll/1.\n"))
        print("need_enroll:", sorted(set(asp.atoms(model, "need_enroll"))))
        print("can_enroll:", sorted(set(asp.atoms(model, "can_enroll"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
