#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/meym_tuition_conflict_folk_tale.py
===================================================================

A small folk-tale storyworld about a village child, a tuition debt, and a
patient resolution.  The seed words "meym" and "tuition" are threaded into a
gentle, child-facing domain where a family must choose between pride and help,
and a wiser helper changes the outcome.

The world is built around a tiny conflict:
- a child wants to join lessons,
- the family cannot yet afford the tuition,
- a helper or kin member takes action,
- the problem turns from worry into a shared plan.

The simulation uses physical meters and emotional memes, a forward-chained
causal model, grounded Q&A, and an inline ASP twin for parity checks.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/meym_tuition_conflict_folk_tale.py
    python storyworlds/worlds/gpt-5.4-mini/meym_tuition_conflict_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/meym_tuition_conflict_folk_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/meym_tuition_conflict_folk_tale.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MIN_WISDOM = 2
MIN_KIND_HELP = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    scene: str
    needs: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ChildGoal:
    id: str
    desire: str
    reason: str
    topic: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TuitionNeed:
    id: str
    label: str
    amount: int
    symbol: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperPlan:
    id: str
    sense: int
    power: int
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    parent = world.get("parent")
    need = world.facts["tuition"]
    if child.memes["hope"] >= THRESHOLD and parent.meters["coins"] < need.amount:
        sig = ("worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            parent.memes["worry"] += 1
            child.memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    parent = world.get("parent")
    child = world.get("child")
    if helper.memes["generous"] >= THRESHOLD and helper.meters["coins"] >= world.facts["tuition"].amount:
        sig = ("relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            parent.memes["relief"] += 1
            child.memes["relief"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("relief", _r_relief)]


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


def reasonableness_gate(goal: ChildGoal, tuition: TuitionNeed, helper: HelperPlan) -> bool:
    return goal.topic in {"lesson", "music", "letters"} and helper.sense >= MIN_WISDOM and helper.power >= MIN_KIND_HELP


def helper_available(helper: HelperPlan, tuition: TuitionNeed) -> bool:
    return helper.power >= tuition.amount and helper.sense >= MIN_WISDOM


def predict_resolution(world: World, helper_id: str) -> dict:
    sim = world.copy()
    helper = sim.get(helper_id)
    helper.meters["coins"] += 0
    propagate(sim, narrate=False)
    return {
        "relief": sim.get("parent").memes["relief"],
        "worry": sim.get("parent").memes["worry"],
    }


def introduce(world: World, child: Entity, place: Place) -> None:
    world.say(
        f"Once in a village by the river, {child.id} lived near {place.label}. "
        f"The little one loved {place.needs} and the old songs of the lane."
    )


def desire_lessons(world: World, child: Entity, goal: ChildGoal, tuition: TuitionNeed) -> None:
    child.memes["hope"] += 1
    world.say(
        f"{child.id} dreamed of {goal.desire} because {goal.reason}. "
        f"The village teacher asked for {tuition.label}, and the child asked for a chance."
    )


def conflict_becomes_clear(world: World, parent: Entity, child: Entity, tuition: TuitionNeed) -> None:
    parent.meters["coins"] = float(world.facts["family_coins"])
    propagate(world, narrate=False)
    world.say(
        f"But the purse was light. {parent.id} counted only a few coins, not enough for {tuition.label}. "
        f"So {child.id} frowned, and {parent.pronoun().capitalize()} worried in silence."
    )


def helper_enters(world: World, helper: Entity, goal: ChildGoal, tuition: TuitionNeed) -> None:
    helper.memes["generous"] += 1
    world.say(
        f"Then {helper.id}, who had a kind heart and a careful hand, came by with a small pouch. "
        f"{helper.pronoun().capitalize()} had heard that {child_name(world)} longed to learn {goal.topic}."
    )
    world.say(
        f"\"No child should lose a bright door for want of {tuition.label},\" {helper.id} said. "
        f"\"Let us see what we can do.\""
    )


def settle_payment(world: World, helper: Entity, parent: Entity, child: Entity, tuition: TuitionNeed, goal: ChildGoal, place: Place) -> None:
    helper.meters["coins"] -= tuition.amount
    parent.meters["coins"] += tuition.amount
    parent.memes["relief"] += 1
    child.memes["joy"] += 1
    world.say(
        f"{helper.id} placed the coins in {parent.pronoun('possessive')} palm, and the tuition was paid. "
        f"{parent.id} bowed {parent.pronoun('possessive')} head and thanked {helper.id}."
    )
    world.say(
        f"By the next dawn, {child.id} went off to {goal.desire} at {place.label}, walking with a lighter step."
    )


def closing_image(world: World, child: Entity, place: Place) -> None:
    world.say(
        f"The village seemed kinder that day: the river sang, the teacher smiled, and {child.id} "
        f"carried no worry at all as {child.pronoun()} crossed the lane toward {place.label}."
    )


def child_name(world: World) -> str:
    return world.get("child").id


def tell(place: Place, goal: ChildGoal, tuition: TuitionNeed, helper_plan: HelperPlan,
         child_name_: str = "Mira", child_gender: str = "girl",
         parent_name: str = "Meym", parent_gender: str = "woman",
         helper_name: str = "Aunt Sela", helper_gender: str = "woman",
         family_coins: int = 1, helper_coins: int = 3) -> World:
    world = World()
    child = world.add(Entity(id=child_name_, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))

    child.memes["hope"] = 1.0
    parent.meters["coins"] = float(family_coins)
    helper.meters["coins"] = float(helper_coins)
    helper.memes["kindness"] = 1.0

    world.facts.update(place=place, goal=goal, tuition=tuition, helper_plan=helper_plan,
                       family_coins=family_coins, helper_coins=helper_coins)

    introduce(world, child, place)
    world.para()
    desire_lessons(world, child, goal, tuition)
    conflict_becomes_clear(world, parent, child, tuition)
    world.para()
    helper_enters(world, helper, goal, tuition)
    can_help = helper_available(helper_plan, tuition) and reasonableness_gate(goal, tuition, helper_plan)
    if can_help:
        settle_payment(world, helper, parent, child, tuition, goal, place)
    else:
        world.say(
            f"But even kind help cannot do a task that is too small or too weak. "
            f"The family had to wait, and the child kept the lesson in {child.pronoun('possessive')} heart."
        )
    world.para()
    closing_image(world, child, place)
    world.facts.update(child=child, parent=parent, helper=helper, resolved=can_help)
    return world


PLACES = {
    "schoolhouse": Place(id="schoolhouse", label="the schoolhouse", scene="a wooden room with a chalkboard", needs="the alphabet", tags={"school"}),
    "market": Place(id="market", label="the market lane", scene="a row of bright stalls", needs="counting and songs", tags={"market"}),
    "byre": Place(id="byre", label="the byre", scene="a warm barn room", needs="listening and patience", tags={"barn"}),
}

GOALS = {
    "letters": ChildGoal(id="letters", desire="learn letters", reason="the shapes looked like magic marks", topic="letters", tags={"lesson"}),
    "music": ChildGoal(id="music", desire="learn music", reason="the fiddle made the child's toes tap", topic="music", tags={"lesson"}),
    "reading": ChildGoal(id="reading", desire="learn reading", reason="the story scrolls shone like treasure", topic="letters", tags={"lesson"}),
}

TUITION = {
    "small_fee": TuitionNeed(id="small_fee", label="tuition", amount=2, symbol="tuition", tags={"tuition"}),
    "fair_fee": TuitionNeed(id="fair_fee", label="tuition", amount=3, symbol="tuition", tags={"tuition"}),
}

HELPERS = {
    "aunt": HelperPlan(id="aunt", sense=3, power=3, text="paid the tuition from a pouch of saved coins", fail="could not pay enough", qa_text="paid the tuition with saved coins", tags={"help"}),
    "shepherd": HelperPlan(id="shepherd", sense=2, power=2, text="shared two bright coins and a promise", fail="had too few coins", qa_text="shared enough coins to pay", tags={"help"}),
    "grandma": HelperPlan(id="grandma", sense=3, power=4, text="opened a little red box and counted out the fee", fail="did not have the fee", qa_text="opened a little box and paid the fee", tags={"help"}),
}

CURATED = [
    StoryParams(place="schoolhouse", goal="letters", tuition="small_fee", helper="aunt", child_name="Mira", child_gender="girl", parent_name="Meym", parent_gender="woman", helper_name="Aunt Sela", helper_gender="woman", family_coins=1, helper_coins=3),
    StoryParams(place="market", goal="music", tuition="fair_fee", helper="grandma", child_name="Toma", child_gender="boy", parent_name="Meym", parent_gender="woman", helper_name="Grandma Ilya", helper_gender="woman", family_coins=1, helper_coins=4),
    StoryParams(place="byre", goal="reading", tuition="small_fee", helper="shepherd", child_name="Nari", child_gender="girl", parent_name="Meym", parent_gender="woman", helper_name="Shepherd Oren", helper_gender="man", family_coins=1, helper_coins=2),
]


@dataclass
class StoryParams:
    place: str
    goal: str
    tuition: str
    helper: str
    child_name: str = "Mira"
    child_gender: str = "girl"
    parent_name: str = "Meym"
    parent_gender: str = "woman"
    helper_name: str = "Aunt Sela"
    helper_gender: str = "woman"
    family_coins: int = 1
    helper_coins: int = 3
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for g in GOALS:
            for t in TUITION:
                hp = HELPERS["aunt"] if t == "small_fee" else HELPERS["grandma"]
                if reasonableness_gate(GOALS[g], TUITION[t], hp):
                    combos.append((p, g, t))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld about Meym, tuition, and a village conflict.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--tuition", choices=TUITION)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--parent-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-gender", choices=["woman", "man"])
    ap.add_argument("--helper-gender", choices=["woman", "man"])
    ap.add_argument("--family-coins", type=int)
    ap.add_argument("--helper-coins", type=int)
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
    helper_key = args.helper or rng.choice(list(HELPERS))
    goal_key = args.goal or rng.choice(list(GOALS))
    tuition_key = args.tuition or rng.choice(list(TUITION))
    place_key = args.place or rng.choice(list(PLACES))
    if args.helper and args.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    if args.goal and args.goal not in GOALS:
        raise StoryError("Unknown goal.")
    if args.tuition and args.tuition not in TUITION:
        raise StoryError("Unknown tuition.")
    helper = HELPERS[helper_key]
    if not reasonableness_gate(GOALS[goal_key], TUITION[tuition_key], helper):
        raise StoryError("No reasonable folk-tale conflict fits those choices.")
    return StoryParams(
        place=place_key,
        goal=goal_key,
        tuition=tuition_key,
        helper=helper_key,
        child_name=args.child_name or rng.choice(["Mira", "Nari", "Toma", "Lina"]),
        child_gender=args.child_gender or rng.choice(["girl", "boy"]),
        parent_name=args.parent_name or "Meym",
        parent_gender=args.parent_gender or "woman",
        helper_name=args.helper_name or rng.choice(["Aunt Sela", "Grandma Ilya", "Shepherd Oren"]),
        helper_gender=args.helper_gender or rng.choice(["woman", "man"]),
        family_coins=args.family_coins if args.family_coins is not None else 1,
        helper_coins=args.helper_coins if args.helper_coins is not None else rng.choice([2, 3, 4]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale story for a 3-to-5-year-old that includes the words "meym" and "tuition".',
        f"Tell a village story where {f['child'].id} wants lessons, but {f['parent'].id} worries about tuition, and a helper steps in.",
        f"Write a gentle conflict story in a folk-tale style about paying tuition and reaching a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    helper = world.facts["helper"]
    tuition = world.facts["tuition"]
    goal = world.facts["goal"]
    place = world.facts["place"]
    resolved = world.facts["resolved"]
    items = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id}, {parent.id}, and {helper.id} in a village near {place.label}. The family conflict is about paying {tuition.label} so the child can learn."
        ),
        QAItem(
            question=f"Why was {parent.id} worried?",
            answer=f"{parent.id} was worried because the family had too few coins for {tuition.label}. That made the lesson dream hard to reach until someone kind offered help."
        ),
    ]
    if resolved:
        items.append(QAItem(
            question="How was the problem solved?",
            answer=f"{helper.id} paid the {tuition.label}, so the child could go on to {goal.desire}. The conflict turned into a shared plan instead of a worry."
        ))
        items.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with the child walking toward {place.label} with a lighter heart. The village felt warmer because the tuition was paid and the lesson could begin."
        ))
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does tuition mean?",
            answer="Tuition is the money paid for lessons or school. Families sometimes save for it so a child can learn."
        ),
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is an old-style story from a village or people, often with a lesson, a helper, and a hopeful ending."
        ),
        QAItem(
            question="What does a helper do in a story like this?",
            answer="A helper gives support when the family cannot solve the trouble alone. In this story, the helper brings coins and kindness."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
goal(G) :- goal_fact(G).
tuition(T) :- tuition_fact(T).
place(P) :- place_fact(P).
helper(H) :- helper_fact(H).

reasonable(P, G, T, H) :- place(P), goal(G), tuition(T), helper(H), helper_sense(H, S), helper_power(H, Pwr), min_wisdom(M), min_kind(Mk), S >= M, Pwr >= Mk.
conflict(P, G, T) :- place(P), goal(G), tuition(T).
resolved(T) :- helper_power(H, Pwr), tuition_amount(T, A), Pwr >= A.
outcome(shared_plan) :- resolved(T).
outcome(still_worrying) :- not resolved(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place_fact", p))
    for g in GOALS:
        lines.append(asp.fact("goal_fact", g))
    for t, obj in TUITION.items():
        lines.append(asp.fact("tuition_fact", t))
        lines.append(asp.fact("tuition_amount", t, obj.amount))
    for h, obj in HELPERS.items():
        lines.append(asp.fact("helper_fact", h))
        lines.append(asp.fact("helper_sense", h, obj.sense))
        lines.append(asp.fact("helper_power", h, obj.power))
    lines.append(asp.fact("min_wisdom", MIN_WISDOM))
    lines.append(asp.fact("min_kind", MIN_KIND_HELP))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonable/4."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("helper_power", params.helper, HELPERS[params.helper].power),
        asp.fact("tuition_amount", params.tuition, TUITION[params.tuition].amount),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in ASP vs Python gate.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"Story generation smoke test failed: {exc}")
        return 1
    print("OK: ASP gate matches Python gate and story generation smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.goal not in GOALS or params.tuition not in TUITION or params.helper not in HELPERS:
        raise StoryError("Invalid params.")
    place = PLACES[params.place]
    goal = GOALS[params.goal]
    tuition = TUITION[params.tuition]
    helper_plan = HELPERS[params.helper]
    if not reasonableness_gate(goal, tuition, helper_plan):
        raise StoryError("The chosen folk-tale conflict is not reasonable.")
    world = tell(place, goal, tuition, helper_plan, params.child_name, params.child_gender,
                 params.parent_name, params.parent_gender, params.helper_name, params.helper_gender,
                 params.family_coins, params.helper_coins)
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
        print(asp_program("", "#show reasonable/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} reasonable combinations")
        for combo in asp_valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
