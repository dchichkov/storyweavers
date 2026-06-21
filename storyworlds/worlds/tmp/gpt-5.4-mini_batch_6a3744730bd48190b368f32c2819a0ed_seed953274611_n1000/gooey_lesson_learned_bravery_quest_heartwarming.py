#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gooey_lesson_learned_bravery_quest_heartwarming.py
===================================================================================

A small heartwarming storyworld about a child, a gooey mess, a brave quest, and a
lesson learned.

Premise
-------
A child and a helper set out on a tiny quest to deliver something sweet and
gooey to someone who needs cheering up. On the way, the goo can wobble, spill,
and make a mess. The child may be tempted to give up, but a brave choice, a calm
helper, and a simple lesson turn the trip into a warm ending.

The world is intentionally modest: one child, one helper, one goal, a few
possible routes, and a small amount of state that changes the story. The prose
is driven by the simulation, not by a frozen template.
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
BRAVERY_START = 4.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

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
class Place:
    id: str
    name: str
    path_word: str
    weather_word: str
    comfort_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class GooItem:
    id: str
    label: str
    phrase: str
    gooey: bool = True
    spillable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class QuestGoal:
    id: str
    recipient: str
    reason: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    calm: int
    brave: int
    advice: str
    rescue: str
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
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    goo = world.get("goo")
    if child.meters["jostled"] >= THRESHOLD and goo.meters["carried"] >= THRESHOLD:
        sig = ("spill",)
        if sig not in world.fired:
            world.fired.add(sig)
            goo.meters["spilled"] += 1
            child.memes["worry"] += 1
            out.append("__spill__")
    return out


def _r_smile(world: World) -> list[str]:
    out: list[str] = []
    if world.get("helper").memes["comfort"] >= THRESHOLD and world.get("child").memes["bravery"] >= THRESHOLD:
        sig = ("smile",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("child").memes["joy"] += 1
            world.get("helper").memes["joy"] += 1
            out.append("__smile__")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill), Rule("smile", _r_smile)]


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


def reasonableness_ok(place: Place, goo: GooItem, helper: Helper, goal: QuestGoal) -> bool:
    return goo.gooey and goo.spillable and "carry" in helper.tags and place.id in ROUTES and goal.id in GOALS


def choose_route(world: World, place: Place, helper: Helper, goal: QuestGoal) -> None:
    world.say(
        f"{place.name} was quiet that day, with {place.comfort_word} tucked beside the path."
    )
    world.say(
        f"{world.get('child').id} and {helper.label} began their quest to reach {goal.recipient} with a sweet treat."
    )


def tempt(world: World, child: Entity, goo: GooItem) -> None:
    child.memes["desire"] += 1
    world.say(
        f'In {child.pronoun("possessive")} hands was {goo.phrase}, all soft and gooey and warm.'
    )
    world.say(f'{child.id} hoped the treat could stay perfect all the way there.')


def brave_choice(world: World, child: Entity, helper: Entity) -> None:
    child.memes["bravery"] += 1
    helper.memes["comfort"] += 1
    world.say(
        f'{helper.label} gave {child.id} a steady smile. "{helper.advice}"'
    )
    world.say(
        f"{child.id} took a slow breath and held on more carefully."
    )


def stumble(world: World, child: Entity, goo: GooItem) -> None:
    child.meters["jostled"] += 1
    goo.meters["carried"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the path dipped, and the goo gave a little wobble in {child.pronoun('possessive')} box."
    )


def spill_event(world: World, goo: GooItem) -> None:
    if goo.meters["spilled"] >= THRESHOLD:
        world.say(
            f"A spoonful slipped out and made a gooey spot on the ground, shiny like a little puddle of jam."
        )


def find_fix(world: World, child: Entity, helper: Entity, goal: QuestGoal) -> None:
    world.say(
        f"{child.id} frowned for one tiny moment, then {helper.label} showed {child.pronoun('object')} how to tuck the box flat."
    )
    world.say(
        f'Together they kept going, because {goal.reason}.'
    )


def resolve(world: World, child: Entity, helper: Entity, goal: QuestGoal) -> None:
    child.memes["lesson"] += 1
    child.memes["love"] += 1
    helper.memes["love"] += 1
    world.say("When they arrived, everyone laughed in a soft, happy way.")
    world.say(
        f"{goal.ending_image} The sweet gift was still a little messy, but it was shared with a warm smile."
    )


def tell(place: Place, goo: GooItem, goal: QuestGoal, helper: Helper,
         child_name: str = "Mina", child_gender: str = "girl", parent_type: str = "mother") -> World:
    if not reasonableness_ok(place, goo, helper, goal):
        raise StoryError("This combination does not support a believable gooey quest.")

    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    helper_ent = world.add(Entity(id=helper.id, kind="character", type="helper", label=helper.label, role="helper"))
    goo_ent = world.add(Entity(id=goo.id, type="thing", label=goo.label, tags=set(goo.tags)))
    world.add(Entity(id=goal.id, type="thing", label=goal.recipient, tags=set(goal.tags)))

    child.memes["bravery"] = BRAVERY_START
    world.facts["place"] = place
    world.facts["goo"] = goo
    world.facts["goal"] = goal
    world.facts["helper"] = helper
    world.facts["parent"] = parent

    choose_route(world, place, helper, goal)
    tempt(world, child, goo)
    world.para()
    brave_choice(world, child, helper_ent)
    stumble(world, child, goo_ent)
    spill_event(world, goo_ent)
    find_fix(world, child, helper_ent, goal)
    world.para()
    resolve(world, child, helper_ent, goal)

    world.facts.update(child=child, helper_ent=helper_ent, goo_ent=goo_ent)
    return world


def _greet_story(world: World) -> str:
    place: Place = world.facts["place"]
    goo: GooItem = world.facts["goo"]
    goal: QuestGoal = world.facts["goal"]
    return (
        f'Write a heartwarming story for a 3-to-5-year-old about {place.name}, '
        f'a gooey treat, and a small quest to help {goal.recipient}. Include the word "{goo.label}".'
    )


def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]
    helper: Helper = world.facts["helper"]
    goal: QuestGoal = world.facts["goal"]
    place: Place = world.facts["place"]
    return [
        _greet_story(world),
        f"Tell a warm story where {child.id} and {helper.label} go on a quest through {place.name} to cheer up {goal.recipient}.",
        f'Write a heartwarming tale that includes "gooey" and ends with a lesson learned and a brave choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper_ent"]
    goo: GooItem = world.facts["goo"]
    goal: QuestGoal = world.facts["goal"]
    place: Place = world.facts["place"]
    return [
        QAItem(
            question="What were the child and helper trying to do?",
            answer=f"They were on a little quest to bring something sweet to {goal.recipient}. They wanted to finish the trip with kindness and care."
        ),
        QAItem(
            question="Why did the child need bravery?",
            answer=f"The treat was gooey and could spill on the path, so {child.id} had to hold it carefully. Bravery helped {child.pronoun()} keep going even after the wobble."
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The goo stayed mostly together, the child learned to carry it flatter, and everyone shared a warm ending. The quest became a happy memory instead of a worry."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does gooey mean?",
            answer="Gooey means soft, sticky, and a little wet, like a treat that can wobble or smear if you are not careful."
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something a little hard or scary while staying calm and trying your best."
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a little mission or journey to reach a goal, often with a helper and a problem to solve."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


PLACEMENTS = {
    "kitchen": Place(id="kitchen", name="the kitchen", path_word="hallway", weather_word="rainy", comfort_word="sunlit table", tags={"indoor"}),
    "garden": Place(id="garden", name="the garden path", path_word="stone path", weather_word="breezy", comfort_word="little bench", tags={"outdoor"}),
    "bakery": Place(id="bakery", name="the bakery", path_word="front step", weather_word="warm", comfort_word="cozy window", tags={"indoor"}),
}

GOODS = {
    "pudding": GooItem(id="pudding", label="gooey pudding", phrase="a cup of gooey pudding", tags={"gooey"}),
    "jamjar": GooItem(id="jamjar", label="gooey jam jar", phrase="a tiny jar of gooey jam", tags={"gooey"}),
    "custard": GooItem(id="custard", label="gooey custard tart", phrase="a gooey custard tart", tags={"gooey"}),
}

GOALS = {
    "grandma": QuestGoal(id="grandma", recipient="Grandma", reason="Grandma had been feeling lonely", ending_image="Grandma's eyes sparkled as she took a spoonful.", tags={"heartwarming"}),
    "neighbor": QuestGoal(id="neighbor", recipient="the neighbor", reason="the neighbor had helped them before", ending_image="The neighbor smiled and clapped softly.", tags={"heartwarming"}),
    "littlebrother": QuestGoal(id="littlebrother", recipient="the little brother", reason="the little brother had a hard day", ending_image="The little brother giggled and licked a sticky drop from his lip.", tags={"heartwarming"}),
}

HELPERS = {
    "mom": Helper(id="mom", label="Mom", calm=5, brave=5, advice="Let's carry it flat and steady.", rescue="Mom warmed a towel and cleaned the spill with care.", tags={"carry"}),
    "dad": Helper(id="dad", label="Dad", calm=6, brave=4, advice="We can take our time.", rescue="Dad knelt down and helped keep the treat safe.", tags={"carry"}),
    "aunt": Helper(id="aunt", label="Aunt May", calm=7, brave=5, advice="Slow steps are brave steps.", rescue="Aunt May smiled and steadied the box with both hands.", tags={"carry"}),
}

CURATED = [
    StoryParams(place="kitchen", goo="pudding", goal="grandma", helper="mom", child_name="Mina", child_gender="girl", parent_type="mother"),
    StoryParams(place="garden", goo="jamjar", goal="neighbor", helper="dad", child_name="Owen", child_gender="boy", parent_type="father"),
    StoryParams(place="bakery", goo="custard", goal="littlebrother", helper="aunt", child_name="Ivy", child_gender="girl", parent_type="mother"),
]


@dataclass
class StoryParams:
    place: str
    goo: str
    goal: str
    helper: str
    child_name: str = "Mina"
    child_gender: str = "girl"
    parent_type: str = "mother"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for p in PLACEMENTS:
        for g in GOODS:
            for goal in GOALS:
                for h in HELPERS:
                    out.append((p, g, goal, h))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming gooey quest storyworld.")
    ap.add_argument("--place", choices=PLACEMENTS)
    ap.add_argument("--goo", choices=GOODS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
              and (args.goo is None or c[1] == args.goo)
              and (args.goal is None or c[2] == args.goal)
              and (args.helper is None or c[3] == args.helper)]
    if not combos:
        raise StoryError("No valid combination matches the requested options.")
    place, goo, goal, helper = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(["Mina", "Nia", "Theo", "Luca", "Iris", "Finn"])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, goo=goo, goal=goal, helper=helper,
                       child_name=child_name, child_gender=child_gender, parent_type=parent)


def generate(params: StoryParams) -> StorySample:
    for field_name, table in [("place", PLACEMENTS), ("goo", GOODS), ("goal", GOALS), ("helper", HELPERS)]:
        if getattr(params, field_name) not in table:
            raise StoryError(f"Invalid {field_name}: {getattr(params, field_name)}")
    world = tell(PLACEMENTS[params.place], GOODS[params.goo], GOALS[params.goal], HELPERS[params.helper],
                 child_name=params.child_name, child_gender=params.child_gender, parent_type=params.parent_type)
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


ASP_RULES = r"""
valid(P,G,L,H) :- place(P), goo(G), goal(L), helper(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACEMENTS:
        lines.append(asp.fact("place", p))
    for g in GOODS:
        lines.append(asp.fact("goo", g))
    for l in GOALS:
        lines.append(asp.fact("goal", l))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    old = sys.stdout
    try:
        buf = io.StringIO()
        sys.stdout = buf
        sample = generate(CURATED[0])
        emit(sample)
    finally:
        sys.stdout = old
    if not sample.story.strip():
        print("Smoke test failed: empty story.")
        return 1
    if set(asp_valid_combos()) != set(valid_combos()):
        print("ASP parity mismatch.")
        return 1
    print("OK: smoke test and ASP parity passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} at {p.place} with {p.helper} ({p.goo} -> {p.goal})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
