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

STORYWORLDS_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path[:0] = [STORYWORLDS_DIR, os.path.dirname(STORYWORLDS_DIR)]
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
need_enroll(B, F) :- budget(B), fee(F), F <= B.
can_enroll(B, F) :- need_enroll(B, F), service(S), useful(S).
#show need_enroll/2.
#show can_enroll/2.
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
    service = SERVICES[args.service] if args.service else SERVICES[job]
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
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}:{params.kind}:{params.job}:{params.budget}:{params.fee}")
    rng = random.Random(seed ^ 0xB0D6E7)

    w = World()
    hero = w.add(Entity(id=params.name, kind="character", type=params.kind, label=params.name))
    clerk = w.add(Entity(id="Clerk", kind="character", type="mouse", label="the clerk"))
    cash = w.add(Entity(id="Coins", type="thing", label="coins"))
    service = w.add(Entity(id="Service", type="thing", label=params.service, phrase=params.service))
    hero.meters["budget"] = params.budget
    service.meters["fee"] = params.fee

    service_details = {
        "garden service": {
            "place": "the community garden",
            "goal": "help plant a crooked row of bean seedlings",
            "badge": "a green leaf badge",
            "tasks": [
                "filled tiny watering cans",
                "sorted smooth seeds from wrinkled ones",
                "tied drooping bean stems to stakes",
                "carried peelings to the compost bin",
                "painted signs for the herb beds",
            ],
            "finals": [
                "A new bean leaf curled around its stake beside the green badge.",
                "Under the sunset, the watered seedlings stood straight in one shining row.",
                "A ladybug rested on the leaf badge while the last watering can dripped dry.",
            ],
        },
        "market service": {
            "place": "the covered market",
            "goal": "help neighbors carry their baskets before the lunch bell",
            "badge": "a blue basket badge",
            "tasks": [
                "stacked empty berry boxes",
                "returned rolling apples to their crate",
                "carried a light basket for an old badger",
                "swept oat husks from the stall",
                "wrote neat price cards for the baker",
            ],
            "finals": [
                "The lunch bell rang as the blue badge gleamed above one last tidy basket.",
                "A red apple sat safely in its crate beneath the hero's new basket badge.",
                "The closing shutters clicked, and every neighbor's basket was safely home.",
            ],
        },
        "library service": {
            "place": "the little library",
            "goal": "prepare the reading room before the toddlers arrived",
            "badge": "a silver book badge",
            "tasks": [
                "matched lost books to their shelf labels",
                "mended a torn paper moon with tape",
                "set round cushions beside the story rug",
                "carried returned books from the cart",
                "sharpened colored pencils for the picture table",
            ],
            "finals": [
                "The silver badge caught the lamplight as the first storybook opened.",
                "On the quiet rug, a toddler pointed to the newly mended paper moon.",
                "The final book slid home, and the reading-room lamp made a warm golden circle.",
            ],
        },
    }
    detail = service_details[params.service]
    opener = rng.choice([
        f"On the morning after a windy night, {params.name} hurried to {detail['place']}.",
        f"Once, a little {params.kind} named {params.name} followed a hand-painted sign to {detail['place']}.",
        f"Before breakfast one Saturday, {params.name} heard the busy bell at {detail['place']}.",
        f"A neighbor's call for helpers brought {params.name}, a little {params.kind}, to {detail['place']}.",
        f"Rain had finally stopped when {params.name} found an open service day at {detail['place']}.",
    ])
    reasons = [
        "The work looked useful, and the small badge would show that its wearer had promised to return.",
        "The helpers were busy, and joining them meant taking a real turn at caring for the place.",
        "The job mattered to the whole neighborhood, not just to one animal.",
        "A younger animal was waiting for help, so the work suddenly felt important.",
    ]
    w.say(opener)
    w.say(f"{params.name} wanted to enroll in the {params.service} and {detail['goal']}.")
    w.say(rng.choice(reasons))
    w.para()

    w.say(f'"Enrollment costs {params.fee} coins for tools and supplies," said {clerk.label}.')
    w.say(f'{params.name} spread {params.budget} coins on the counter. "This is every coin in my budget."')
    w.say(rng.choice([
        '"Then we need a budgetary plan," said the clerk. "That just means a careful plan for the coins."',
        '"Let us solve the budgetary part," said the clerk. "We will count what comes in and what goes out."',
        '"A budgetary worry is a money-plan worry," the clerk explained. "Counting clearly is the first step."',
        'The clerk drew two boxes on a slate: COINS SAVED and COINS NEEDED. "That is our budgetary picture," she said.',
    ]))

    actions = rng.sample(detail["tasks"], 3)
    if params.budget >= params.fee:
        remaining = params.budget - params.fee
        conflicts = [
            (f"A gust scattered the enrollment forms across {detail['place']} before the fee could be paid.",
             f'"Forms first, coins second!" called {params.name}.',
             f"Together, {params.name} and the clerk gathered every page and weighed the stack down with a smooth stone."),
            (f"Just then, a younger helper whispered that there were not enough supplies for today's work.",
             f'"Can my enrollment fee buy the missing supplies?" asked {params.name}.',
             f'The clerk checked the list. "Exactly," she said. "Now every coin has a purpose."'),
            (f"The coin box had three slots, but none was labeled, so nobody knew where an enrollment fee belonged.",
             f'"Tools, repairs, and new helpers," {params.name} repeated. "Let us label them."',
             f"They made three clear labels and placed the fee in the tools slot."),
            (f"A wheel squeaked on the supply cart, and the waiting helpers could not move it.",
             f'"Let us fix what the fee is meant to support," said {params.name}.',
             f"The clerk found a washer, and {params.name} held the wheel steady until it rolled quietly."),
        ]
        conflict, refrain, turn = rng.choice(conflicts)
        w.say(conflict)
        w.say(refrain)
        w.say(turn)
        w.para()
        w.say(f"The clerk counted {params.fee} coins into the enrollment box, leaving {remaining} with {params.name}.")
        hero.meters["budget"] -= params.fee
        hero.memes["hope"] = 1
        w.say(f'"To enroll means to join officially," said the clerk, pinning {detail["badge"]} on {params.name}.')
        w.say(f"For the first service shift, {params.name} {actions[0]}, {actions[1]}, and {actions[2]}.")
        outcomes = [
            f'"Count, choose, then use," {params.name} said at each new job.',
            f'"A coin plan should help the work," {params.name} repeated, "help the work, help the work."',
            f'"Every coin had a job, and now I do too," {params.name} told the younger helpers.',
        ]
        w.say(rng.choice(outcomes))
        outcome = f"{params.name} paid the {params.fee}-coin fee, enrolled, and completed a first service shift."
        lesson = "A good budget gives each coin a clear purpose, and service gives willing paws a useful purpose."
    else:
        shortfall = params.fee - params.budget
        plans = [
            (f'The slate showed a gap of {shortfall} coin{"s" if shortfall != 1 else ""}. "I will earn it without pretending I have it," said {params.name}.',
             f"The clerk offered service credit for a set of finished tasks. {params.name} {actions[0]}, {actions[1]}, and {actions[2]}.",
             f'"Count the work, count the credit," they repeated until the two sides of the slate matched.'),
            (f'A savings jar stood beside the slate. "I can come back after doing small paid chores," said {params.name}.',
             f"Over several mornings, {params.name} {actions[0]}, then {actions[1]}, and finally {actions[2]}. Each earned coin went straight into the jar.",
             f'"Save a little, mark it down; save a little, mark it down," {params.name} repeated.'),
            (f'The clerk pointed to a sign offering reduced fees to helpers who completed an open job. "That is fair to everyone," said {params.name}.',
             f"To earn the reduction, {params.name} {actions[0]}, {actions[1]}, and {actions[2]} while the clerk checked each job.",
             f'"Done with care, counted fair," the two of them said after every check mark.'),
            (f'"Could I pay part now and the rest after my first supervised shift?" asked {params.name}. The clerk showed the written installment rule.',
             f"After paying the first part, {params.name} {actions[0]}, {actions[1]}, and {actions[2]}. The earned coins covered the final part exactly.",
             f'"Part by part, keep the chart," {params.name} repeated while marking each payment.'),
        ]
        conflict, turn, refrain = rng.choice(plans)
        w.say(conflict)
        w.say(turn)
        w.say(refrain)
        w.para()
        w.say(f"At last, the clerk counted all {params.fee} coins and crossed out the gap on the slate.")
        hero.meters["budget"] = 0
        hero.memes["patience"] = 1
        w.say(f'"You planned honestly and finished the work," she said. "Now you may enroll."')
        w.say(f"She pinned {detail['badge']} on {params.name}, who joined the {params.service} and began to {detail['goal']}.")
        outcome = f"{params.name} followed a fair plan to cover the {shortfall}-coin gap, enrolled, and joined the work."
        lesson = "When money is short, an honest plan and patient work can make the next step possible."

    w.para()
    final_image = rng.choice(detail["finals"])
    w.say(final_image)
    w.say(f"Moral: {lesson}")

    w.facts.update(
        hero=hero,
        clerk=clerk,
        service=service,
        params=params,
        goal=detail["goal"],
        actions=actions,
        outcome=outcome,
        final_image=final_image,
    )
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
    money_prompt = (
        f"Tell a gentle story where {p.name} makes a budgetary plan before enrolling."
        if p.budget >= p.fee
        else f"Tell a gentle story where a budgetary shortfall keeps {p.name} from enrolling right away."
    )
    return [
        f"Write a short fable about a {p.kind} who wants to enroll in a {p.service}.",
        money_prompt,
        f"Write a child-friendly dialogue story using the words service, budgetary, and enroll.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    actions = world.facts["actions"]
    return [
        QAItem(
            question=f"Who wanted to enroll in the {p.service}?",
            answer=f"{p.name}, the little {p.kind}, wanted to enroll in the {p.service}.",
        ),
        QAItem(
            question=f"What did {p.name} hope to do after enrolling?",
            answer=f"{p.name} hoped to {world.facts['goal']} after enrolling.",
        ),
        QAItem(
            question="What service work did the animal do?",
            answer=f"{p.name} {actions[0]}, {actions[1]}, and {actions[2]}.",
        ),
        QAItem(
            question="How was the enrollment problem resolved?",
            answer=world.facts["outcome"],
        ),
        QAItem(
            question="What picture closes the fable?",
            answer=world.facts["final_image"],
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
    prog = asp_program("#show need_enroll/2.\n#show can_enroll/2.\n")
    model = asp.one_model(prog)
    need = set(asp.atoms(model, "need_enroll"))
    can = set(asp.atoms(model, "can_enroll"))
    py = set(valid_pairs())
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
    StoryParams(name="Fenn", kind="fox", job="garden", service="garden service", budget=2, fee=4),
    StoryParams(name="Mira", kind="hare", job="market", service="market service", budget=5, fee=4),
    StoryParams(name="Pip", kind="mouse", job="library", service="library service", budget=3, fee=3),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show need_enroll/2.\n#show can_enroll/2.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show need_enroll/2.\n#show can_enroll/2.\n"))
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
