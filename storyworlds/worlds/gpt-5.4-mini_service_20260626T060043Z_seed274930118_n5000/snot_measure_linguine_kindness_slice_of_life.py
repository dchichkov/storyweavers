#!/usr/bin/env python3
"""
storyworlds/worlds/snot_measure_linguine_kindness_slice_of_life.py
==================================================================

A small slice-of-life story world about a child helping make dinner, a tiny
mess of snot, a careful measure of linguine, and a kindness that turns the
evening around.

The premise is intentionally simple:
- Someone in the kitchen is making supper.
- A child wants to measure linguine and help.
- A sniffly nose creates a small problem.
- A kind, practical response keeps the story gentle and grounded.

The world simulates physical state with meters and emotional state with memes.
The narrative is driven by those state changes rather than by a frozen template.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the kitchen"
    time_of_day: str = "evening"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MeasureItem:
    id: str
    label: str
    phrase: str
    plural: bool = True
    risky: str = "splash"


@dataclass
class Comfort:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.zone = set(self.zone)
        return clone


def meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def bump_meter(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = meter(ent, key) + amt


def bump_meme(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = meme(ent, key) + amt


def has_mess(ent: Entity, key: str) -> bool:
    return meter(ent, key) >= THRESHOLD


def story_intro(hero: Entity, helper: Entity, pot: Entity) -> str:
    return (
        f"{hero.id} liked helping in the kitchen after school. "
        f"{hero.pronoun().capitalize()} liked the quiet clink of bowls, "
        f"the warm light on the counter, and the way {helper.pronoun('subject')} "
        f"showed {hero.pronoun('object')} how to cook."
    )


def story_measure(hero: Entity, activity: Activity) -> str:
    return (
        f"{hero.id} wanted to {activity.verb}, because {activity.gerund} made "
        f"supper feel real and grown-up."
    )


def story_kindness(helper: Entity, hero: Entity) -> str:
    return (
        f"{helper.id} smiled and said, \"We can do this together, one careful step at a time.\""
    )


def story_resolution(hero: Entity, helper: Entity, item: MeasureItem) -> str:
    return (
        f"In the end, {hero.id} measured the {item.label} neatly, wiped the counter, "
        f"and sat down to eat with {helper.pronoun('object')}."
    )


def apply_sneeze(world: World, child: Entity) -> list[str]:
    out: list[str] = []
    if meme(child, "sniffly") < THRESHOLD:
        return out
    sig = ("sneeze", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bump_meter(child, "snot", 1.0)
    out.append(f"{child.id} gave a tiny sneeze, and a little snot landed on the tissue.")
    return out


def apply_kindness(world: World, helper: Entity, child: Entity) -> list[str]:
    out: list[str] = []
    if meme(child, "embarrassed") < THRESHOLD:
        return out
    sig = ("kindness", helper.id, child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bump_meme(child, "comforted", 1.0)
    bump_meme(helper, "kindness", 1.0)
    out.append(f"{helper.id} handed over a fresh tissue and stayed cheerful about it.")
    return out


def apply_measure_help(world: World, helper: Entity, child: Entity, item: MeasureItem) -> list[str]:
    out: list[str] = []
    if meter(child, "helping") < THRESHOLD or meter(child, "snot") < THRESHOLD:
        return out
    sig = ("measure_help", helper.id, child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bump_meme(child, "proud", 1.0)
    out.append(
        f"{helper.id} showed {child.id} how to measure the linguine by eye, "
        f"then by hand, so the pot would not overflow."
    )
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for ent in world.entities.values():
            if ent.kind == "character":
                for s in apply_sneeze(world, ent):
                    produced.append(s)
                    changed = True
        helper = world.facts.get("helper")
        child = world.facts.get("child")
        item = world.facts.get("item")
        if helper and child and item:
            for s in apply_kindness(world, helper, child):
                produced.append(s)
                changed = True
            for s in apply_measure_help(world, helper, child, item):
                produced.append(s)
                changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_spill(world: World, child: Entity, activity: Activity) -> dict:
    sim = world.copy()
    bump_meter(sim.get(child.id), activity.mess, 1.0)
    propagate(sim, narrate=False)
    return {
        "messy": meter(sim.get(child.id), activity.mess) >= THRESHOLD,
        "comforted": meme(sim.get(child.id), "comforted") >= THRESHOLD,
    }


def tell(setting: Setting, activity: Activity, item: MeasureItem,
         hero_name: str, helper_name: str, hero_type: str = "boy",
         helper_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["small", "careful"],
        meters={"helping": 1.0},
        memes={"curious": 1.0},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        traits=["patient", "kind"],
        memes={"kindness": 1.0},
    ))
    pot = world.add(Entity(
        id="pot",
        type="thing",
        label="pot",
        phrase="a wide pot for dinner",
        caretaker=helper.id,
    ))
    measure = world.add(Entity(
        id=item.id,
        type="thing",
        label=item.label,
        phrase=item.phrase,
        owner=child.id,
    ))
    world.facts.update(child=child, helper=helper, pot=pot, item=measure, activity=activity)

    world.say(story_intro(child, helper, pot))
    world.say(story_measure(child, activity))
    world.say(f"The {setting.place.removeprefix('the ')} smelled like garlic and warm water.")
    world.para()

    pred = predict_spill(world, child, activity)
    if pred["messy"]:
        bump_meme(child, "sniffly", 1.0)
        bump_meme(child, "embarrassed", 1.0)
        world.say(
            f"Just then, {child.id} sniffled, and {child.pronoun()} paused with the measuring cup in hand."
        )
        world.say(f"{helper.id} noticed at once and did not make it a big deal.")
        propagate(world, narrate=True)
    else:
        world.say(f"{child.id} measured the linguine carefully, and nothing spilled.")

    world.para()
    world.zone = {"counter"}
    if meter(child, "snot") >= THRESHOLD:
        world.say(
            f"{child.id} wiped {child.pronoun('possessive')} nose, then kept helping."
        )
    world.say(story_kindness(helper, child))
    world.say(
        f"The pot stayed steady, the pasta stayed dry, and the kitchen kept its calm, homey feeling."
    )
    world.para()
    world.say(story_resolution(child, helper, measure))

    world.facts["resolved"] = True
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", time_of_day="evening", affords={"measure", "cook"}),
    "small_kitchen": Setting(place="the small kitchen", time_of_day="evening", affords={"measure", "cook"}),
    "apartment_kitchen": Setting(place="the apartment kitchen", time_of_day="evening", affords={"measure", "cook"}),
}

ACTIVITIES = {
    "measure_linguine": Activity(
        id="measure_linguine",
        verb="measure linguine",
        gerund="measuring linguine",
        rush="tip the whole box into the pot",
        mess="overflow",
        soil="spilled and tangled",
        keyword="linguine",
        tags={"linguine", "measure", "kindness"},
    ),
    "stir_sauce": Activity(
        id="stir_sauce",
        verb="stir the sauce",
        gerund="stirring the sauce",
        rush="grab the spoon too fast",
        mess="splash",
        soil="splashed",
        keyword="sauce",
        tags={"kindness"},
    ),
}

MEASURE_ITEMS = {
    "linguine": MeasureItem(
        id="linguine",
        label="linguine",
        phrase="a long nest of dry linguine",
        plural=True,
    ),
    "measuring_cup": MeasureItem(
        id="measuring_cup",
        label="measuring cup",
        phrase="a small measuring cup",
        plural=False,
    ),
}

COMFORTS = {
    "tissue": Comfort(
        id="tissue",
        label="a fresh tissue",
        prep="hand over a fresh tissue",
        tail="kept dinner going without fuss",
        helps={"snot", "comfort"},
    ),
    "tea": Comfort(
        id="tea",
        label="warm tea",
        prep="pour warm tea into a little mug",
        tail="made the kitchen feel gentle again",
        helps={"comfort"},
    ),
}

CHILD_NAMES = ["Milo", "Nora", "Eli", "Ivy", "June", "Owen", "Ada", "Theo"]
HELPER_NAMES = ["Mom", "Dad", "Aunt Lina", "Grandma", "Uncle Ben"]
CHILD_TYPES = ["boy", "girl"]
HELPER_TYPES = ["mother", "father", "woman", "man"]


@dataclass
class StoryParams:
    setting: str
    activity: str
    item: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for s in SETTINGS:
        for a in ACTIVITIES:
            for i in MEASURE_ITEMS:
                if a == "measure_linguine" and i == "linguine":
                    combos.append((s, a, i))
    return combos


def explain_rejection(activity: Activity, item: MeasureItem) -> str:
    return (
        f"(No story: the activity {activity.id} only makes sense with {item.label}, "
        f"because this world is about carefully measuring linguine before dinner.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A slice-of-life story world about linguine, a small snot problem, and kindness."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--item", choices=MEASURE_ITEMS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
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
    if args.activity == "measure_linguine" and args.item and args.item != "linguine":
        raise StoryError(explain_rejection(ACTIVITIES[args.activity], MEASURE_ITEMS[args.item]))
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.item:
        combos = [c for c in combos if c[2] == args.item]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, activity, item = rng.choice(combos)
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(
        setting=setting,
        activity=activity,
        item=item,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    act = f["activity"]
    item = f["item"]
    return [
        f'Write a gentle slice-of-life story for a young child that includes the word "{item.label}".',
        f"Tell a small kitchen story where {child.id} helps {helper.id} {act.verb} and a kind moment follows a sniffly nose.",
        f'Write a simple story about "kindness" in a kitchen, with careful measuring and a little nose wipe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    item = f["item"]
    act = f["activity"]
    return [
        QAItem(
            question=f"What did {child.id} want to do in the kitchen?",
            answer=f"{child.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"What made the story turn into a kindness moment?",
            answer=f"{child.id} got a little sniffly, and {helper.id} answered with patience instead of fuss.",
        ),
        QAItem(
            question=f"What was carefully measured?",
            answer=f"The {item.label} was carefully measured before dinner.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.id} helping neatly, the kitchen staying calm, and dinner moving forward kindly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is linguine?",
            answer="Linguine is a kind of long, flat pasta that people boil for dinner.",
        ),
        QAItem(
            question="Why do people measure pasta?",
            answer="People measure pasta so they do not cook too much or too little at once.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means noticing someone needs help and choosing to be gentle and caring.",
        ),
        QAItem(
            question="What can you do if your nose is runny?",
            answer="You can use a tissue to wipe your nose and keep things clean.",
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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("verb", aid, a.verb))
        lines.append(asp.fact("keyword", aid, a.keyword))
    for iid, item in MEASURE_ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("label", iid, item.label))
    lines.append(asp.fact("feature", "kindness"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S,A,I) :- setting(S), activity(A), item(I), A = measure_linguine, I = linguine.
kindness_theme :- feature(kindness).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        ACTIVITIES[params.activity],
        MEASURE_ITEMS[params.item],
        params.child_name,
        params.helper_name,
        params.child_type,
        params.helper_type,
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


CURATED = [
    StoryParams(
        setting="kitchen",
        activity="measure_linguine",
        item="linguine",
        child_name="Milo",
        child_type="boy",
        helper_name="Mom",
        helper_type="mother",
    ),
    StoryParams(
        setting="small_kitchen",
        activity="measure_linguine",
        item="linguine",
        child_name="Nora",
        child_type="girl",
        helper_name="Grandma",
        helper_type="woman",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
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
            header = f"### {p.child_name}: {p.activity} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
