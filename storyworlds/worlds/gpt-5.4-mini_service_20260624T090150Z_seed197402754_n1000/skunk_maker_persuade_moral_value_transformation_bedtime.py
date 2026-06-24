#!/usr/bin/env python3
"""
A bedtime-story world about a little skunk, a maker, a gentle persuasion, and a
moral-value transformation.

Premise:
A small skunk wants to keep a strong smell for a special craft, but a kind maker
worries that the plan might bother the skunk's friends. The maker persuades the
skunk to try a cleaner, kinder way.

Tension:
The skunk believes the strong smell is the only way to make the craft feel
special. The maker sees that the same goal can be reached without hurting
anyone's noses or feelings.

Turn:
The maker offers a softer method that still preserves the skunk's pride and
purpose. The skunk listens, thinks, and changes the plan.

Resolution:
The skunk completes the bedtime craft in a new way, feeling proud and gentle.
The world ends with a small visible change in behavior and a calmer moral
feeling.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"skunk", "child", "maker"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little workshop"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    moral_tension: str
    moral_turn: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str = "hands"
    plural: bool = False


@dataclass
class Aid:
    id: str
    label: str
    prep: str
    tail: str
    reduces: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "workshop": Setting(place="the little workshop", indoor=True, affords={"craft"}),
    "bedroom": Setting(place="the bedroom", indoor=True, affords={"craft"}),
}

PLANS = {
    "scented_card": Plan(
        id="scented_card",
        verb="make a special card",
        gerund="making a special card",
        rush="dash to the scent jar",
        risk="the strong smell would cling to the card and bother friends",
        moral_tension="strong smells should only be used with care",
        moral_turn="a gentle craft can still feel special",
        keyword="skunk",
        tags={"skunk", "craft", "smell"},
    ),
    "mask": Plan(
        id="mask",
        verb="decorate a bedtime mask",
        gerund="decorating a bedtime mask",
        rush="reach for the shiny paint",
        risk="the wet paint would smear and make the room messy",
        moral_tension="good things are kinder when they stay neat and calm",
        moral_turn="kind choices can keep the room peaceful",
        keyword="maker",
        tags={"maker", "craft", "paint"},
    ),
}

PRIZES = {
    "card": Prize(label="card", phrase="a bright little card", type="card"),
    "mask": Prize(label="mask", phrase="a soft bedtime mask", type="mask"),
}

AIDS = {
    "fresh_air": Aid(
        id="fresh_air",
        label="the open window",
        prep="open the window first",
        tail="worked by the open window",
        reduces={"smell"},
    ),
    "flower_stickers": Aid(
        id="flower_stickers",
        label="tiny flower stickers",
        prep="use tiny flower stickers instead of the stinky bottle",
        tail="used the tiny flower stickers",
        reduces={"mess"},
    ),
    "quiet_lamp": Aid(
        id="quiet_lamp",
        label="a warm lamp",
        prep="turn on a warm lamp and slow everything down",
        tail="rested under the warm lamp",
        reduces={"fear", "rush"},
    ),
}

SKUNK_NAMES = ["Pip", "Milo", "Luna", "Nico", "Bibi"]
MAKER_NAMES = ["Mara", "Tessa", "Owen", "Jun", "Iris"]
TRAITS = ["curious", "gentle", "stubborn", "shy", "hopeful"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def plan_risky(plan: Plan, prize: Prize) -> bool:
    return True  # all registered plans create a meaningful bedtime tension


def select_aid(plan: Plan, prize: Prize) -> Optional[Aid]:
    if plan.id == "scented_card":
        return AIDS["fresh_air"]
    if plan.id == "mask":
        return AIDS["quiet_lamp"]
    return None


def explain_rejection(plan: Plan, prize: Prize) -> str:
    return (
        f"(No story: the plan '{plan.id}' does not have a gentle fix for a {prize.label} "
        f"in this bedtime world.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A plan is risky when it creates a meaningful bedtime conflict.
risky(P) :- plan(P).

% A fix is compatible when it reduces the right kind of tension.
fix(P, A) :- risky(P), aid(A).

valid_story(S, P, R) :- setting(S), plan(P), prize(R), fix(P, A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PLANS:
        lines.append(asp.fact("plan", pid))
    for rid in PRIZES:
        lines.append(asp.fact("prize", rid))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set((s, p, r) for s in SETTINGS for p in PLANS for r in PRIZES)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python story space ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python story space:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def predict_mess(world: World, hero: Entity, plan: Plan) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["smell"] += 1
    return {
        "smell": sim.get(hero.id).meters["smell"],
        "trouble": plan.risk,
    }


def setup_story(world: World, hero: Entity, maker: Entity, prize: Entity, plan: Plan) -> None:
    world.say(
        f"{hero.id} was a little skunk with a careful heart, and {maker.id} was a kind maker "
        f"who worked by the soft lamp."
    )
    world.say(
        f"{hero.id} wanted to {plan.verb}, because {plan.moral_tension}."
    )
    world.say(
        f"The maker smiled at the bright idea, but worried that {plan.risk}."
    )


def persuade(world: World, maker: Entity, hero: Entity, plan: Plan, prize: Entity) -> Optional[Aid]:
    aid = select_aid(plan, prize)
    if aid is None:
        return None
    world.say(
        f'"What if we {aid.prep}?" {maker.id} asked, gently persuading {hero.id} to try a kinder way.'
    )
    return aid


def accept(world: World, hero: Entity, maker: Entity, plan: Plan, prize: Prize, aid: Aid) -> None:
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    hero.memes["stubborn"] = 0.0
    world.say(
        f"{hero.id} sniffed, thought it over, and nodded. {hero.pronoun('subject').capitalize()} "
        f"liked that the new plan still felt special."
    )
    world.say(
        f"Together they {aid.tail}. Soon {hero.id} was {plan.gerund}, and the {prize.label} stayed clean and gentle."
    )
    world.say(
        f"At bedtime, {hero.id} felt proud, because {plan.moral_turn}."
    )


def tell(setting: Setting, plan: Plan, prize: Prize, hero_name: str, maker_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="skunk"))
    maker = world.add(Entity(id=maker_name, kind="character", type="maker"))
    prize_ent = world.add(Entity(id=prize.type, type=prize.type, label=prize.label, phrase=prize.phrase))

    hero.meters["smell"] = 0.0
    hero.memes["stubborn"] = 1.0
    hero.memes["hopeful"] = 1.0

    setup_story(world, hero, maker, prize_ent, plan)
    world.para()
    pred = predict_mess(world, hero, plan)
    world.say(
        f"By the time the maker looked closely, {hero.id} already had a big idea in mind."
    )
    world.say(
        f"{hero.id} wanted to hurry, but the maker kept the room calm and asked for a better way."
    )
    aid = persuade(world, maker, hero, plan, prize_ent)
    world.para()
    if aid:
        accept(world, hero, maker, plan, prize, aid)
    world.facts.update(
        hero=hero,
        maker=maker,
        prize=prize_ent,
        plan=plan,
        aid=aid,
        predicted=pred,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, maker, plan, prize = f["hero"], f["maker"], f["plan"], f["prize"]
    return [
        f"Write a bedtime story about a little {hero.type} and a kind {maker.type} who persuade each other to choose a gentler craft.",
        f"Tell a calm story where {hero.id} wants to {plan.verb} but {maker.id} helps with a safer idea.",
        f"Write a short moral story using the words skunk, maker, and persuade, ending with a peaceful bedtime feeling.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, maker, plan, prize, aid = f["hero"], f["maker"], f["plan"], f["prize"], f["aid"]
    qa = [
        QAItem(
            question=f"Who wanted to {plan.verb} in the story?",
            answer=f"{hero.id} the skunk wanted to {plan.verb} because {plan.moral_tension}.",
        ),
        QAItem(
            question=f"Why did {maker.id} worry about the idea?",
            answer=f"{maker.id} worried because {plan.risk}.",
        ),
        QAItem(
            question=f"What gentle thing did the maker suggest?",
            answer=f"The maker suggested {aid.prep}, which was a kinder way to finish the craft.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{hero.id} changed from stubborn to calm and kind, and the {prize.label} stayed neat.",
        ),
    ]
    if aid:
        qa.append(
            QAItem(
                question=f"How did {maker.id} persuade {hero.id}?",
                answer=(
                    f"{maker.id} persuaded {hero.id} by offering a soft, safer plan that still kept the craft special."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a skunk?",
            answer="A skunk is a small animal that can make a strong smell when it feels unsafe or startled.",
        ),
        QAItem(
            question="What does a maker do?",
            answer="A maker creates things with their hands, like crafts, toys, or decorations.",
        ),
        QAItem(
            question="What does it mean to persuade someone?",
            answer="To persuade someone means to help them choose by giving a gentle reason or a better idea.",
        ),
        QAItem(
            question="What is transformation in a story?",
            answer="Transformation is when something changes into a new form, choice, or feeling.",
        ),
        QAItem(
            question="What is moral value?",
            answer="Moral value is the good idea that helps a character choose kindness, care, and fairness.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    plan: str
    prize: str
    hero_name: str
    maker_name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="workshop", plan="scented_card", prize="card", hero_name="Pip", maker_name="Mara"),
    StoryParams(place="bedroom", plan="mask", prize="mask", hero_name="Luna", maker_name="Jun"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about a skunk, a maker, and a gentle persuasion.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero-name")
    ap.add_argument("--maker-name")
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
    if args.plan and args.prize:
        plan = PLANS[args.plan]
        prize = PRIZES[args.prize]
        if not plan_risky(plan, prize):
            raise StoryError(explain_rejection(plan, prize))

    place = args.place or rng.choice(list(SETTINGS))
    plan = args.plan or rng.choice(list(PLANS))
    prize = args.prize or rng.choice(list(PRIZES))
    hero_name = args.hero_name or rng.choice(SKUNK_NAMES)
    maker_name = args.maker_name or rng.choice(MAKER_NAMES)
    return StoryParams(place=place, plan=plan, prize=prize, hero_name=hero_name, maker_name=maker_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PLANS[params.plan], PRIZES[params.prize], params.hero_name, params.maker_name)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story combos:")
        for combo in combos:
            print(" ", combo)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
