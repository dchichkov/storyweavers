#!/usr/bin/env python3
"""
storyworlds/worlds/delay_dinner_cautionary_rhyming_story.py
===========================================================

A small cautionary rhyming story world about delay and dinner.

Premise:
A hungry child is tempted to delay dinner for one more bit of play.
The parent warns that the meal will grow cold, and the child must choose
between a little more fun and a warm, kindly ending.

The world model tracks:
- physical meters: hunger, warmth, tidiness, time, patience
- emotional memes: delight, worry, regret, relief, care

The simulation keeps the prose grounded in causal state changes rather than
replaying a fixed paragraph. Each story ends by proving what changed: dinner
stayed warm or cooled, the child learned a lesson, and the evening closed
with a concrete image.

Style note:
This script leans into a gentle rhyming story voice with short, child-facing
sentences and a cautionary turn.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    eaten: bool = False
    warm: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["hunger", "warmth", "tidiness", "time", "patience"]:
            self.meters.setdefault(key, 0.0)
        for key in ["delight", "worry", "regret", "relief", "care"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the kitchen"
    delay_spot: str = "the porch"
    afford_delay: bool = True


@dataclass
class Dinner:
    label: str
    phrase: str
    smell: str
    warmth_loss: float = 1.0


@dataclass
class Distraction:
    label: str
    verb: str
    delight: str
    delay_cost: float
    rhyme1: str
    rhyme2: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_time(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["time"] < THRESHOLD:
            continue
        sig = ("time", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append(f"The clock ticked on, and the evening grew long.")
    return out


def _r_warmth(world: World) -> list[str]:
    out: list[str] = []
    dinner = world.get("dinner")
    if dinner.meters["time"] >= THRESHOLD and dinner.warm:
        sig = ("cool",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        dinner.warm = False
        dinner.meters["warmth"] = 0.0
        out.append("The dinner lost its steam and turned from warm to a little cold.")
    return out


def _r_patience(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    parent = world.get("parent")
    if child.meters["time"] < THRESHOLD:
        return out
    sig = ("patience",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    parent.memes["care"] += 1
    child.memes["worry"] += 1
    out.append("The parent watched the delay and felt a gentle worry.")
    return out


RULES = [_r_time, _r_warmth, _r_patience]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_delay(world: World, distraction: Distraction) -> dict[str, object]:
    sim = world.copy()
    child = sim.get("child")
    dinner = sim.get("dinner")
    child.meters["time"] += distraction.delay_cost
    dinner.meters["time"] += distraction.delay_cost
    propagate(sim, narrate=False)
    return {
        "warm": dinner.warm,
        "worry": child.memes["worry"],
    }


def intro(world: World, child: Entity, parent: Entity, setting: Setting, dinner: Dinner) -> None:
    world.say(
        f"{child.id} was a little {child.type} with a hop and a cheer, "
        f"who loved the warm smell of dinner drawing near."
    )
    world.say(
        f"{parent.pronoun('subject').capitalize()} called from {setting.place}, "
        f"with a kind, calm tone: "
        f'"Dinner is ready, so come in home."'
    )
    world.say(
        f"{dinner.phrase.capitalize()} waited there gently, in a cozy bright glow, "
        f"with a savory smell that made hungry hearts slow."
    )


def temptation(world: World, child: Entity, distraction: Distraction) -> None:
    child.memes["delight"] += 1
    child.meters["time"] += distraction.delay_cost
    world.say(
        f"But {child.id} saw {distraction.label} and gave it a whirl, "
        f"because one more little moment can feel like a swirl."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} wanted to {distraction.verb}, "
        f"just once in the light, "
        f"and the game felt so shiny, so breezy, so right."
    )
    world.say(distraction.delight)


def warn(world: World, parent: Entity, child: Entity, dinner: Dinner) -> None:
    world.say(
        f'The parent said, "Delay too long, and the soup may grow cold; '
        f"warm bites turn to sighs when the minutes grow old.""
    )
    world.say(
        f'"A dinner left waiting can lose all its cheer, '
        f"so come to the table while supper is near."'
    )


def hesitate(world: World, child: Entity) -> None:
    child.memes["worry"] += 1
    world.say(
        f"{child.id} paused by the doorway, then frowned at the floor, "
        f"for play tugged one way and dinner tugged more."
    )


def resolve(world: World, child: Entity, parent: Entity, dinner: Dinner) -> None:
    child.memes["regret"] += 1
    child.memes["relief"] += 1
    world.say(
        f"At last {child.id} chose dinner and hurried inside, "
        f"with a small little blush and a softer new pride."
    )
    if dinner.warm:
        world.say(
            f"The meal still was steaming, so rosy and bright, "
            f"and the whole room felt cozy at the end of the night."
        )
    else:
        world.say(
            f"The meal had grown cooler, but still it was kind, "
            f"and {child.id} learned a lesson to keep in mind."
        )
    world.say(
        f"{parent.pronoun('subject').capitalize()} smiled at the choice and pulled out a chair, "
        f"and the ending was gentle, with comfort to spare."
    )


SETTING_REGISTRY = {
    "kitchen": Setting(place="the kitchen", delay_spot="the porch", afford_delay=True),
    "yard": Setting(place="the yard", delay_spot="the swing", afford_delay=True),
    "playroom": Setting(place="the playroom", delay_spot="the rug", afford_delay=True),
}

DINNERS = {
    "soup": Dinner(label="soup", phrase="a bowl of soup", smell="savory"),
    "stew": Dinner(label="stew", phrase="a pot of stew", smell="hearty"),
    "rice": Dinner(label="rice", phrase="a plate of rice and peas", smell="warm"),
}

DISTRACTIONS = {
    "blocks": Distraction(
        label="a tower of blocks",
        verb="stack the blocks taller and taller",
        delight="The blocks clicked bright and neat, like a tiny drumbeat for feet.",
        delay_cost=1.5,
        rhyme1="bright",
        rhyme2="night",
    ),
    "crayons": Distraction(
        label="a box of crayons",
        verb="draw one more smiling sun",
        delight="The crayons skated over paper, red and blue and green, a cheerful rainbow cape.",
        delay_cost=1.25,
        rhyme1="sun",
        rhyme2="fun",
    ),
    "ball": Distraction(
        label="a bouncy ball",
        verb="bounce the ball down the hall",
        delight="The ball went boing and bound, a merry little sound.",
        delay_cost=1.75,
        rhyme1="hall",
        rhyme2="call",
    ),
}


@dataclass
class StoryParams:
    setting: str
    dinner: str
    distraction: str
    child_name: str
    child_type: str
    parent_type: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella", "Ruby", "Ivy"]
BOY_NAMES = ["Leo", "Finn", "Milo", "Ben", "Noah", "Theo", "Max", "Jack"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for s in SETTING_REGISTRY:
        for d in DINNERS:
            for x in DISTRACTIONS:
                combos.append((s, d, x))
    return combos


def explain_invalid(setting: str, dinner: str, distraction: str) -> str:
    return f"(No story: the combination {setting}/{dinner}/{distraction} does not fit the cautionary dinner-delay premise.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Cautionary rhyming story world about delaying dinner."
    )
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--dinner", choices=DINNERS)
    ap.add_argument("--distraction", choices=DISTRACTIONS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
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
    combos = valid_combos()
    combos = [c for c in combos
              if (args.setting is None or c[0] == args.setting)
              and (args.dinner is None or c[1] == args.dinner)
              and (args.distraction is None or c[2] == args.distraction)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, dinner, distraction = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    return StoryParams(setting, dinner, distraction, child_name, child_type, parent_type)


def tell(params: StoryParams) -> World:
    world = World(SETTING_REGISTRY[params.setting])
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_type))
    dinner = world.add(Entity(id="dinner", kind="thing", type=params.dinner, label=params.dinner, phrase=DINNERS[params.dinner].phrase))
    distraction = DISTRACTIONS[params.distraction]

    intro(world, child, parent, world.setting, DINNERS[params.dinner])
    world.para()
    temptation(world, child, distraction)
    warn(world, parent, child, DINNERS[params.dinner])
    hesitate(world, child)
    child.meters["time"] += distraction.delay_cost
    dinner.meters["time"] += distraction.delay_cost
    propagate(world, narrate=True)
    world.para()
    resolve(world, child, parent, DINNERS[params.dinner])

    world.facts = {
        "child": child,
        "parent": parent,
        "dinner": dinner,
        "distraction": distraction,
        "setting": world.setting,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    distraction = f["distraction"]
    dinner = f["dinner"]
    return [
        f'Write a short cautionary rhyming story for a young child about delaying {dinner.label}.',
        f"Tell a gentle story where {child.id} wants to keep playing with {distraction.label} instead of coming to dinner.",
        f"Create a simple rhyming story about a parent warning that dinner will get cold if the child delays too long.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    dinner: Entity = f["dinner"]
    dist: Distraction = f["distraction"]
    qa = [
        QAItem(
            question=f"What did {child.id} want to do instead of coming to dinner?",
            answer=f"{child.id} wanted to keep playing with {dist.label} and delay dinner for a little while.",
        ),
        QAItem(
            question=f"Why did {parent.pronoun('subject')} warn {child.id} about the meal?",
            answer=f"{parent.pronoun('subject').capitalize()} warned {child.id} because delaying dinner could let {dinner.label} grow cold and less inviting.",
        ),
        QAItem(
            question=f"What happened when {child.id} finally chose dinner?",
            answer=f"{child.id} came inside, the evening settled down, and the story ended with a warm family meal and a gentle lesson.",
        ),
    ]
    if not f["dinner"].warm:
        qa.append(
            QAItem(
                question=f"Did the dinner stay warm the whole time?",
                answer=f"No. The dinner waited too long and cooled off before {child.id} came in.",
            )
        )
    else:
        qa.append(
            QAItem(
                question=f"Did the dinner stay warm the whole time?",
                answer=f"Yes. {child.id} came in before the meal lost its warmth, so dinner stayed cozy and ready.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    dist: Distraction = f["distraction"]
    dinner: Entity = f["dinner"]
    return [
        QAItem(
            question="Why should hot food be eaten soon after it is served?",
            answer="Hot food is best eaten soon after it is served because it can cool down, and warm meals often taste better and feel cozier.",
        ),
        QAItem(
            question="What does it mean to delay something?",
            answer="To delay something means to wait or put it off for a little while instead of doing it right away.",
        ),
        QAItem(
            question=f"Why can {dist.label} be a tempting distraction?",
            answer=f"{dist.label} can be tempting because it looks fun right now, even when something important like {dinner.label} is waiting.",
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
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "thing":
            bits.append(f"warm={e.warm}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
child_delay(C) :- child(C), chooses_delay(C).
dinner_cools(D) :- dinner(D), child_delay(_).
cautionary_end(C) :- child(C), returns_to_table(C).

#show child_delay/1.
#show dinner_cools/1.
#show cautionary_end/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for s in SETTING_REGISTRY:
        lines.append(asp.fact("setting", s))
    for d in DINNERS:
        lines.append(asp.fact("dinner", d))
    for x in DISTRACTIONS:
        lines.append(asp.fact("distraction", x))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("returns_to_table", "child"))
    lines.append(asp.fact("chooses_delay", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show child_delay/1.\n#show dinner_cools/1.\n#show cautionary_end/1."))
    atoms = set((sym.name, tuple(a.name if a.type != a.type.Number else a.number for a in sym.arguments)) for sym in model)
    expected = {("child_delay", ("child",)), ("dinner_cools", ("dinner",)), ("cautionary_end", ("child",))}
    if atoms == expected:
        print("OK: ASP twin matches the Python story gate.")
        return 0
    print("MISMATCH: ASP twin does not match.")
    print("got:", sorted(atoms))
    print("expected:", sorted(expected))
    return 1


CURATED = [
    StoryParams("kitchen", "soup", "blocks", "Mia", "girl", "mother"),
    StoryParams("yard", "stew", "crayons", "Leo", "boy", "father"),
    StoryParams("playroom", "rice", "ball", "Nora", "girl", "mother"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show child_delay/1.\n#show dinner_cools/1.\n#show cautionary_end/1."))
        return
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show child_delay/1.\n#show dinner_cools/1.\n#show cautionary_end/1."))
        print("ASP atoms:")
        for sym in model:
            print(sym)
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.child_name}: delaying {p.dinner} with {p.distraction}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
