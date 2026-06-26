#!/usr/bin/env python3
"""
storyworlds/worlds/berg_lesson_learned_problem_solving_slice_of.py
===================================================================

A small slice-of-life storyworld about a child, a little berg, and a practical
lesson learned through problem solving.

Seed story premise:
- A child is playing near a chilly little berg made of packed snow and ice.
- The berg is useful for play, but it can block a toy boat and make a wet mess.
- A grownup helps the child think through the problem instead of just removing it.
- The child learns that slow, careful fixes can work better than pushing harder.

This world aims for:
- Lesson Learned: the child changes how they handle the problem.
- Problem Solving: the solution is chosen by reasoning about the world state.
- Slice of Life: a small domestic or neighborhood moment with concrete details.

The model is intentionally modest: fewer, stronger combinations instead of many
thin ones.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "ice": 0.0, "stuck": 0.0, "clean": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "patience": 0.0, "pride": 0.0, "lesson": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    plural: bool = False


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
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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
        return clone


def _r_wet(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            sig = ("wet_item", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] += 1
            item.meters["clean"] = 0
            out.append(f"{actor.id}'s {item.label} got damp.")
    return out


def _r_stuck(world: World) -> list[str]:
    out: list[str] = []
    berg = world.entities.get("berg")
    boat = world.entities.get("boat")
    if not berg or not boat:
        return out
    if berg.meters["stuck"] < THRESHOLD:
        return out
    sig = ("boat_stuck",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    boat.meters["stuck"] += 1
    out.append("The little boat could not move around the berg.")
    return out


def _r_lesson(world: World) -> list[str]:
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if not child or not helper:
        return []
    if child.memes["patience"] < THRESHOLD or helper.memes["calm"] < THRESHOLD:
        return []
    sig = ("lesson",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["lesson"] += 1
    child.memes["pride"] += 1
    return ["__lesson__"]


CAUSAL_RULES = [_r_wet, _r_stuck, _r_lesson]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__lesson__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_problem(world: World, child: Entity, activity: Activity, prize: Entity) -> dict:
    sim = world.copy()
    sim.get(child.id).meters[activity.mess] += 1
    sim.get("berg").meters["stuck"] += 1
    propagate(sim, narrate=False)
    return {
        "boat_stuck": sim.get(prize.id).meters["stuck"] >= THRESHOLD,
        "wet": sim.get(child.id).meters["wet"] >= THRESHOLD,
    }


def can_fix(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_tool(activity: Activity, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS:
        if activity.mess in tool.guards and prize.region in tool.covers:
            return tool
    return None


def intro(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.type} who liked quiet play near {world.setting.place}."
    )
    world.say("The best part was watching the tiny berg glitter in the cold light.")


def love(world: World, child: Entity, activity: Activity) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} loved {activity.gerund}, because {activity.keyword} felt like a small winter game."
    )


def setup(world: World, child: Entity, prize: Entity) -> None:
    world.say(
        f"One morning, {child.id} carried {child.pronoun('possessive')} {prize.label} to the water's edge."
    )
    prize.worn_by = child.id


def start_problem(world: World, child: Entity, activity: Activity, prize: Entity) -> None:
    child.meters[activity.mess] += 1
    child.memes["worry"] += 1
    world.say(
        f"{child.id} wanted to {activity.verb}, but the little berg got in the way of {child.pronoun('possessive')} {prize.label}."
    )
    world.say(
        f"{child.id} tried to {activity.rush}, and the cold splash made everything feel trickier."
    )
    propagate(world)


def notice(world: World, helper: Entity, child: Entity, prize: Entity) -> None:
    helper.memes["calm"] += 1
    world.say(
        f"{helper.id} knelt beside {child.id} and said, \"Let's look first and solve it gently.\""
    )
    world.say(
        f"Together they saw that moving too fast would only make {child.pronoun('possessive')} {prize.label} wetter."
    )


def solve(world: World, child: Entity, helper: Entity, activity: Activity, prize: Entity) -> Optional[Tool]:
    tool = select_tool(activity, prize)
    if tool is None:
        return None
    if build_problem(world, child, activity, prize)["boat_stuck"]:
        world.say(
            f"{helper.id} pointed at {tool.label} and showed {child.id} how to use it without bumping the berg."
        )
        return tool
    return None


def resolve(world: World, child: Entity, helper: Entity, activity: Activity, prize: Entity, tool: Tool) -> None:
    child.memes["patience"] += 1
    child.memes["joy"] += 1
    child.memes["worry"] = 0.0
    world.say(
        f"{child.id} took a breath, used {tool.label}, and gently guided the boat around the berg."
    )
    world.say(
        f"Then {child.id} wiped {child.pronoun('possessive')} {prize.label} dry and smiled at the neat little fix."
    )
    world.say(
        f"{helper.id} laughed softly, and {child.id} learned that slow hands could solve a stubborn problem."
    )


def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    hero_name: str = "Mina",
    hero_type: str = "girl",
    helper_type: str = "mother",
) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="mom"))
    berg = world.add(Entity(id="berg", type="thing", label="berg", phrase="a tiny berg", meters={"wet": 0.0, "ice": 1.0, "stuck": 0.0, "clean": 1.0}, memes={"joy": 0.0, "worry": 0.0, "patience": 0.0, "pride": 0.0, "lesson": 0.0}))
    prize = world.add(Entity(id="boat", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=child.id, region=prize_cfg.region))
    intro(world, child)
    love(world, child, activity)
    setup(world, child, prize)
    world.para()
    start_problem(world, child, activity, prize)
    notice(world, helper, child, prize)
    world.para()
    tool = solve(world, child, helper, activity, prize)
    if tool is not None:
        resolve(world, child, helper, activity, prize, tool)
    world.facts.update(child=child, helper=helper, berg=berg, prize=prize, activity=activity, tool=tool, setting=setting)
    return world


SETTINGS = {
    "pond": Setting(place="the little pond", affords={"push_boat"}),
    "dock": Setting(place="the dock", affords={"push_boat"}),
    "yard": Setting(place="the backyard puddle", affords={"push_boat"}),
}

ACTIVITIES = {
    "push_boat": Activity(
        id="push_boat",
        verb="push the boat",
        gerund="pushing the boat",
        rush="push the boat harder",
        mess="wet",
        soil="wet",
        zone={"hands", "feet", "torso"},
        keyword="berg",
        tags={"berg", "water", "boat"},
    )
}

PRIZES = {
    "boat": Prize(label="boat", phrase="a little toy boat", type="toy", region="hands")
}

TOOLS = [
    Tool(
        id="stick",
        label="a long stick",
        prep="use a long stick",
        tail="nudged the boat around the berg",
        covers={"hands"},
        guards={"wet"},
    ),
    Tool(
        id="bucket",
        label="an empty bucket",
        prep="use the bucket as a scoop",
        tail="lifted the boat free",
        covers={"hands"},
        guards={"wet"},
    ),
]

NAMES = ["Mina", "Luca", "Noah", "Iris", "Ada", "Theo"]
HELPERS = ["mother", "father"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    helper: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if can_fix(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


KNOWLEDGE = {
    "berg": [(
        "What is a berg?",
        "A berg is a large piece of ice or packed snow. In a small story, it can be a little icy bump that changes where a toy can go."
    )],
    "boat": [(
        "What does a toy boat do?",
        "A toy boat floats or slides along water, especially when the water is calm."
    )],
    "wet": [(
        "Why do wet things need drying?",
        "Wet things are dried so they do not stay cold or slippery for too long."
    )],
    "stick": [(
        "Why can a stick help with a problem?",
        "A stick can help you reach or nudge something carefully without putting your hands right in the middle of the problem."
    )],
}

KNOWLEDGE_ORDER = ["berg", "boat", "wet", "stick"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        f'Write a short slice-of-life story for a young child where {child.id} notices a berg and solves a small problem.',
        f"Tell a gentle story about {child.id} learning patience while moving a toy boat around a berg.",
        f'Write a simple story that includes the word "berg" and ends with a child learning a useful lesson.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, prize, act = f["child"], f["helper"], f["prize"], f["activity"]
    tool = f.get("tool")
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {child.id}, a little {child.type} who was playing near {world.setting.place}.",
        ),
        QAItem(
            question=f"What problem did {child.id} have with the berg?",
            answer=f"The tiny berg got in the way of {child.pronoun('possessive')} {prize.label}, so the boat could not move easily.",
        ),
        QAItem(
            question=f"Who helped {child.id} think through the problem?",
            answer=f"{helper.id} helped by staying calm and suggesting a careful solution.",
        ),
    ]
    if tool is not None:
        qa.append(
            QAItem(
                question=f"How did {tool.label} help?",
                answer=f"{tool.label} helped {child.id} nudge the boat around the berg without making the mess worse.",
            )
        )
    qa.append(
        QAItem(
            question=f"What lesson did {child.id} learn?",
            answer=f"{child.id} learned that slowing down and using a simple tool can solve a stubborn problem.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("tool"):
        tags.add(world.facts["tool"].id)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
boat_stuck :- berg(stuck), prize(boat).
lesson_learned :- calm(helper), patient(child), boat_stuck.
valid_story(Place, Act, Prize) :- setting(Place), affords(Place, Act), prize(Prize), can_fix(Act, Prize).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", t.id, c))
        for g in sorted(t.guards):
            lines.append(asp.fact("guards", t.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: berg, lesson learned, problem solving, slice of life.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
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
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, "girl" if params.name in {"Mina", "Iris", "Ada"} else "boy", params.helper)
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
    StoryParams(place="pond", activity="push_boat", prize="boat", name="Mina", helper="mother"),
    StoryParams(place="dock", activity="push_boat", prize="boat", name="Theo", helper="father"),
    StoryParams(place="yard", activity="push_boat", prize="boat", name="Iris", helper="mother"),
]


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
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print("  ", combo)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
