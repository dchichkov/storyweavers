#!/usr/bin/env python3
"""
A small fable-like storyworld about debt, trivia, and risk.

Seed premise:
A clever animal borrows something valuable, loses a trivia contest, and must
face the risk of not paying back what is owed. A wiser helper offers a fair,
kind way to settle the debt, and the story ends happily with trust restored.
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SITUATIONS = {
    "market": {
        "place": "the market square",
        "detail": "The stalls were bright with apples, bread, and ribbons.",
        "affords": {"trivia"},
    },
    "orchard": {
        "place": "the orchard",
        "detail": "The trees stood in neat rows, and the grass smelled sweet.",
        "affords": {"trivia", "risk"},
    },
    "riverbank": {
        "place": "the riverbank",
        "detail": "The river hummed softly, and reeds bent in the breeze.",
        "affords": {"trivia", "risk"},
    },
    "village_green": {
        "place": "the village green",
        "detail": "The green was wide and tidy, with a stone well in the middle.",
        "affords": {"trivia"},
    },
}

CHARACTERS = {
    "fox": {"type": "fox", "name_pool": ["Fenn", "Mira", "Tavi"], "trait_pool": ["clever", "quick", "proud"]},
    "hare": {"type": "hare", "name_pool": ["Pip", "Luma", "Suri"], "trait_pool": ["lively", "kind", "curious"]},
    "crow": {"type": "crow", "name_pool": ["Kest", "Nora", "Brim"], "trait_pool": ["sharp-eyed", "thoughtful", "chatty"]},
    "mole": {"type": "mole", "name_pool": ["Marn", "Tilda", "Gus"], "trait_pool": ["patient", "careful", "gentle"]},
}

OBJECTS = {
    "basket": {"label": "a berry basket", "kind": "basket", "risk": "scratched", "region": "hands"},
    "book": {"label": "a little ledger book", "kind": "book", "risk": "creased", "region": "hands"},
    "lamp": {"label": "a brass lamp", "kind": "lamp", "risk": "dented", "region": "hands"},
    "shawl": {"label": "a wool shawl", "kind": "shawl", "risk": "muddy", "region": "back"},
}

TRIVIA_TOPICS = {
    "apples": ("What grows in the orchard?", "Apples grow on trees in an orchard."),
    "lanterns": ("What helps people see in the dark?", "A lantern helps people see in the dark by giving off light."),
    "rivers": ("Where does a river flow?", "A river flows downhill across the land until it reaches a larger body of water."),
    "debts": ("What is a debt?", "A debt is something you owe to someone else and should pay back or return."),
    "risks": ("What is a risk?", "A risk is a chance that something might go wrong or cause harm."),
}

TOPIC_ORDER = ["debts", "risks", "apples", "lanterns", "rivers"]


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["risk", "debt", "trust", "hope", "joy", "pride", "effort"]:
            self.meters.setdefault(key, 0.0)
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    risk_kind: str
    region: str


@dataclass
class Debt:
    amount: int
    due_in_days: int
    thing: str


@dataclass
class StoryParams:
    setting: str
    protagonist_kind: str
    helper_kind: str
    prize: str
    trivia_topic: str
    seed: Optional[int] = None


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


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def _r_interest(world: World) -> list[str]:
    out: list[str] = []
    learner = world.facts["protagonist"]
    if learner.memes["hope"] < 1:
        return out
    if ("interest", learner.id) in world.fired:
        return out
    world.fired.add(("interest", learner.id))
    out.append(f"{learner.id} lifted {learner.pronoun('possessive')} head and listened closely.")
    return out


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts["protagonist"]
    item = world.facts["item"]
    if hero.meters["risk"] < 1:
        return out
    if ("risk", hero.id) in world.fired:
        return out
    world.fired.add(("risk", hero.id))
    item.memes["worry"] = item.memes.get("worry", 0.0) + 1
    out.append(f"The little thing at stake looked unsafe now.")
    return out


def _r_repay(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts["protagonist"]
    debt = world.facts["debt"]
    helper = world.facts["helper"]
    if hero.meters["effort"] < 1 or helper.memes["trust"] < 1:
        return out
    if ("repay", hero.id) in world.fired:
        return out
    world.fired.add(("repay", hero.id))
    hero.meters["debt"] = max(0.0, hero.meters["debt"] - debt.amount)
    helper.memes["joy"] += 1
    hero.memes["joy"] += 1
    out.append(f"By working steadily, {hero.id} paid back the debt.")
    return out


CAUSAL_RULES = [
    _r_interest,
    _r_risk,
    _r_repay,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def choose_name(kind: str, rng: random.Random) -> str:
    return rng.choice(CHARACTERS[kind]["name_pool"])


def choose_trait(kind: str, rng: random.Random) -> str:
    return rng.choice(CHARACTERS[kind]["trait_pool"])


def intro(world: World, hero: Entity, helper: Entity, item: Entity, debt: Debt) -> None:
    world.say(
        f"Once in {world.setting.place}, {hero.id} was a {hero.traits[0]} {hero.type} who loved trivia."
    )
    world.say(
        f"{hero.id} had borrowed {item.label} from {helper.id}, and that meant a debt of {debt.amount} careful favors."
    )


def trivia_scene(world: World, hero: Entity, helper: Entity, topic: str) -> None:
    q, a = TRIVIA_TOPICS[topic]
    hero.memes["hope"] += 1
    world.say(
        f"At the gathering, someone asked, \"{q}\" {hero.id} answered, \"{a}\""
    )
    world.say(
        f"The crowd listened, and {hero.id} felt proud for a moment."
    )


def risk_scene(world: World, hero: Entity, helper: Entity, item: Entity, debt: Debt) -> None:
    hero.meters["risk"] += 1
    hero.meters["debt"] += debt.amount
    hero.memes["pride"] += 1
    world.say(
        f"But the wind caught the corner of {item.label}, and there was real risk it might be harmed."
    )
    world.say(
        f"{helper.id} frowned a little, because a broken borrowed thing would make the debt heavier."
    )


def wise_turn(world: World, hero: Entity, helper: Entity, item: Entity, debt: Debt) -> None:
    helper.memes["trust"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"{helper.id} said, \"Pay me back with honest work and one good story for the village.\""
    )
    world.say(
        f"{hero.id} nodded. That was a fairer path than hiding from the risk."
    )


def resolution(world: World, hero: Entity, helper: Entity, item: Entity, debt: Debt) -> None:
    hero.meters["effort"] += 1
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} cleaned stalls, carried water, and mended a fence until the debt was paid."
    )
    world.say(
        f"In the end, {item.label} was safe, {helper.id} smiled, and the village enjoyed a happy evening of trivia."
    )


def tell_story(params: StoryParams, rng: random.Random) -> World:
    setting = Setting(**SITUATIONS[params.setting])
    world = World(setting)

    hero_name = choose_name(params.protagonist_kind, rng)
    helper_name = choose_name(params.helper_kind, rng)
    hero_trait = choose_trait(params.protagonist_kind, rng)
    helper_trait = choose_trait(params.helper_kind, rng)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=params.protagonist_kind,
        traits=[hero_trait, "fable-minded"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=params.helper_kind,
        traits=[helper_trait, "wise"],
    ))
    item_info = OBJECTS[params.prize]
    item = world.add(Entity(
        id="borrowed_item",
        kind="thing",
        type=item_info["kind"],
        label=item_info["label"],
        owner=helper.id,
        caretaker=helper.id,
        region=item_info["region"],
    ))
    debt = Debt(amount=1, due_in_days=3, thing=item.label)

    world.facts = {
        "protagonist": hero,
        "helper": helper,
        "item": item,
        "debt": debt,
        "topic": params.trivia_topic,
        "setting": setting,
    }

    intro(world, hero, helper, item, debt)
    world.para()
    trivia_scene(world, hero, helper, params.trivia_topic)
    risk_scene(world, hero, helper, item, debt)
    world.para()
    wise_turn(world, hero, helper, item, debt)
    resolution(world, hero, helper, item, debt)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["protagonist"]
    helper = f["helper"]
    item = f["item"]
    topic = f["topic"]
    return [
        f'Write a short fable about {hero.id}, a debt, and a trivia contest that includes the word "{topic}".',
        f"Tell a child-friendly story where {hero.id} borrows {item.label} from {helper.id}, faces a risk, and makes things right.",
        f"Write a happy ending fable about a clever animal who answers trivia and repays what is owed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["protagonist"]
    helper = f["helper"]
    item = f["item"]
    debt = f["debt"]
    topic = f["topic"]
    return [
        QAItem(
            question=f"Who borrowed {item.label}?",
            answer=f"{hero.id} borrowed {item.label} from {helper.id}, so {hero.id} had a debt to repay.",
        ),
        QAItem(
            question=f"What kind of game helped the story begin?",
            answer=f"A trivia question helped the story begin, and it used the topic of {topic}.",
        ),
        QAItem(
            question=f"Why did the helper worry?",
            answer=f"{helper.id} worried because there was a risk that {item.label} could be harmed, which would make the debt harder to settle.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.id} worked hard, paid back the debt, and the story ended happily with trust and smiles restored.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in TOPIC_ORDER:
        q, a = TRIVIA_TOPICS[key]
        out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in world.entities.values():
        lines.append(
            f"{ent.id}: type={ent.type} meters={{{', '.join(f'{k}={v}' for k, v in ent.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}={v}' for k, v in ent.memes.items() if v)}}}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(market).
setting(orchard).
setting(riverbank).
setting(village_green).

affords(market,trivia).
affords(orchard,trivia).
affords(orchard,risk).
affords(riverbank,trivia).
affords(riverbank,risk).
affords(village_green,trivia).

topic(debts).
topic(risks).
topic(apples).
topic(lanterns).
topic(rivers).

borrower(fox).
borrower(hare).
borrower(crow).
borrower(mole).

helper(fox).
helper(hare).
helper(crow).
helper(mole).

valid_story(S, P, T) :- setting(S), affords(S,trivia), topic(T), borrower(P).
happy_ending(S, P, T) :- valid_story(S, P, T).
#show valid_story/3.
#show happy_ending/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SITUATIONS:
        lines.append(asp.fact("setting", s))
        for a in sorted(SITUATIONS[s]["affords"]):
            lines.append(asp.fact("affords", s, a))
    for t in TRIVIA_TOPICS:
        lines.append(asp.fact("topic", t))
    for k in CHARACTERS:
        lines.append(asp.fact("borrower", k))
        lines.append(asp.fact("helper", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3.\n"))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    asp_set = set(asp_valid_stories())
    py_set = set(valid_combos())
    if asp_set != py_set:
        print("MISMATCH between ASP and Python")
        print("only in ASP:", sorted(asp_set - py_set))
        print("only in Python:", sorted(py_set - asp_set))
        return 1
    print(f"OK: ASP matches Python on {len(py_set)} valid stories.")
    return 0


# ---------------------------------------------------------------------------
# Validation / generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting, data in SITUATIONS.items():
        if "trivia" not in data["affords"]:
            continue
        for kind in CHARACTERS:
            for topic in TRIVIA_TOPICS:
                combos.append((setting, kind, topic))
    return combos


CURATED = [
    StoryParams(setting="orchard", protagonist_kind="fox", helper_kind="hare", prize="basket", trivia_topic="debts"),
    StoryParams(setting="market", protagonist_kind="crow", helper_kind="mole", prize="book", trivia_topic="lanterns"),
    StoryParams(setting="riverbank", protagonist_kind="hare", helper_kind="fox", prize="lamp", trivia_topic="risks"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about debt, trivia, and risk.")
    ap.add_argument("--setting", choices=SITUATIONS.keys())
    ap.add_argument("--protagonist-kind", choices=CHARACTERS.keys())
    ap.add_argument("--helper-kind", choices=CHARACTERS.keys())
    ap.add_argument("--prize", choices=OBJECTS.keys())
    ap.add_argument("--trivia-topic", choices=TRIVIA_TOPICS.keys())
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.protagonist_kind:
        combos = [c for c in combos if c[1] == args.protagonist_kind]
    if args.trivia_topic:
        combos = [c for c in combos if c[2] == args.trivia_topic]
    if not combos:
        raise StoryError("No valid story fits those options.")
    setting, protagonist_kind, trivia_topic = rng.choice(combos)
    helper_kind = args.helper_kind or rng.choice(list(CHARACTERS.keys()))
    prize = args.prize or rng.choice(list(OBJECTS.keys()))
    return StoryParams(
        setting=setting,
        protagonist_kind=protagonist_kind,
        helper_kind=helper_kind,
        prize=prize,
        trivia_topic=trivia_topic,
    )


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    world = tell_story(params, rng)
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
        print(asp_program("#show valid_story/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3.\n"))
        atoms = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(atoms)} valid story shapes:")
        for atom in atoms:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
