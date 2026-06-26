#!/usr/bin/env python3
"""
storyworlds/worlds/hour_surprise_transformation_flashback_slice_of_life.py
===========================================================================

A small slice-of-life storyworld about one careful hour:
a child prepares a surprise, remembers an old moment, and watches
something plain become something special.

Premise:
- A child has one hour before a loved one arrives.
- They want to make a surprise with a plain object in a quiet home setting.
- A flashback explains why the surprise matters.
- The ending shows a real transformation in the world, not just in wording.

The story engine keeps a live world model with physical meters and emotional
memes. The narrative is driven by state changes:
- time_left_minutes ticks down,
- plain items become decorated / filled / ready,
- excitement, worry, and pride shift as the surprise is assembled,
- a flashback is triggered by an old keepsake or scent,
- the final image proves the change.

This file follows the Storyweavers storyworld contract:
- standalone stdlib script
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily in ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    hidden: bool = False
    opened: bool = False
    decorated: bool = False
    filled: bool = False
    transformed: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["tidy", "sweet", "warm", "ready", "kept", "time_left"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "surprise", "nostalgia", "pride", "love"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    quiet: bool = True


@dataclass
class Plan:
    id: str
    title: str
    verb: str
    material: str
    surprise_kind: str
    transformation: str
    clue: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    type: str
    container: str
    transformation: str
    hidden_ready: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class MemoryTrigger:
    id: str
    scent: str
    object_name: str
    flashback_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.time_left = 60
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def tick(self, minutes: int, narrate: bool = True) -> None:
        self.time_left = max(0, self.time_left - minutes)
        for e in self.characters():
            e.meters["time_left"] = self.time_left
        if narrate:
            self.say(f"{minutes} minutes slipped by.")

    def copy(self) -> "World":
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.time_left = self.time_left
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def _item_text(label: str, phrase: str) -> str:
    return phrase or label


def _make_sentence_start(minutes_left: int) -> str:
    if minutes_left >= 45:
        return "At the start of the hour,"
    if minutes_left >= 30:
        return "Half an hour later,"
    if minutes_left >= 15:
        return "With only a little time left,"
    return "In the last few minutes,"


def _decorate(world: World, child: Entity, gift: Entity, plan: Plan) -> None:
    sig = ("decorate", gift.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    gift.decorated = True
    gift.transformed = True
    child.memes["pride"] += 1
    child.memes["joy"] += 1
    world.say(
        f"{child.pronoun('possessive').capitalize()} plain {gift.label} changed as {child.pronoun()} "
        f"added small decorations and made {gift.it()} match the surprise."
    )


def _fill(world: World, child: Entity, gift: Entity, plan: Plan) -> None:
    sig = ("fill", gift.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    gift.filled = True
    child.meters["ready"] += 1
    child.memes["joy"] += 0.5
    world.say(
        f"{child.pronoun().capitalize()} filled {gift.it()} with {plan.result}, and the gift began to feel real."
    )


def _flashback(world: World, child: Entity, memory: MemoryTrigger) -> None:
    sig = ("flashback", memory.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    child.memes["nostalgia"] += 1
    child.memes["love"] += 1
    world.say(
        f"Then the scent of {memory.scent} brought back a flashback: {memory.flashback_line}"
    )


def _hide(world: World, child: Entity, gift: Entity, container: Entity) -> None:
    sig = ("hide", gift.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    gift.hidden = True
    child.memes["surprise"] += 1
    world.say(
        f"{child.pronoun().capitalize()} tucked {gift.it()} into {container.label} so the surprise could stay secret."
    )


def _wait(world: World, child: Entity, loved_one: Entity) -> None:
    sig = ("wait", loved_one.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    child.memes["worry"] += 1
    world.say(
        f"{child.pronoun().capitalize()} kept glancing at the door and hoped {loved_one.pronoun('subject')} would not arrive too soon."
    )


def _arrive(world: World, loved_one: Entity, child: Entity, gift: Entity) -> None:
    sig = ("arrive", loved_one.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    loved_one.memes["surprise"] += 1
    child.memes["worry"] = 0
    child.memes["pride"] += 1
    world.say(
        f"At last, the door opened, and {loved_one.label} stepped in just as the surprise was ready."
    )
    world.say(
        f"{child.pronoun('possessive').capitalize()} smile grew wide when {loved_one.label} saw {gift.label} and laughed softly."
    )


def _finish(world: World, child: Entity, loved_one: Entity, gift: Entity) -> None:
    sig = ("finish", gift.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    child.memes["joy"] += 1
    child.memes["pride"] += 1
    gift.meters["kept"] = 1
    world.say(
        f"By the end, the once-plain {gift.label} was decorated, filled, and safely handed over."
    )
    world.say(
        f"The hour had turned into a small happy moment, and the room felt warmer than before."
    )


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"baking", "decorating", "waiting"}, quiet=True),
    "living_room": Setting(place="the living room", affords={"decorating", "waiting"}, quiet=True),
    "table": Setting(place="the table by the window", affords={"decorating", "waiting"}, quiet=True),
}

PLANS = {
    "tea_box": Plan(
        id="tea_box",
        title="a tea surprise",
        verb="make tea-time surprise",
        material="paper stars",
        surprise_kind="tea",
        transformation="plain box to a bright tea gift",
        clue="the smell of cinnamon tea",
        result="a little tea set and a note",
        tags={"tea", "warm", "surprise", "flashback"},
    ),
    "cookie_tin": Plan(
        id="cookie_tin",
        title="a cookie surprise",
        verb="make cookie surprise",
        material="sprinkles",
        surprise_kind="cookie",
        transformation="plain tin to a cheerful cookie tin",
        clue="the smell of sugar and butter",
        result="cookies and a folded message",
        tags={"cookie", "sweet", "surprise", "flashback"},
    ),
    "flower_basket": Plan(
        id="flower_basket",
        title="a flower surprise",
        verb="make flower surprise",
        material="ribbon",
        surprise_kind="flower",
        transformation="plain basket to a bright flower basket",
        clue="the smell of fresh stems",
        result="flowers and a thank-you card",
        tags={"flower", "bright", "surprise", "flashback"},
    ),
}

GIFTS = {
    "box": Gift(
        id="box",
        label="plain box",
        phrase="a plain box",
        type="box",
        container="box",
        transformation="decorated with paper and ribbon",
        hidden_ready="hidden under a tea towel",
        tags={"surprise"},
    ),
    "tin": Gift(
        id="tin",
        label="plain tin",
        phrase="a plain tin",
        type="tin",
        container="tin",
        transformation="covered in stickers and a bright bow",
        hidden_ready="closed with care",
        tags={"sweet", "surprise"},
    ),
    "basket": Gift(
        id="basket",
        label="plain basket",
        phrase="a plain basket",
        type="basket",
        container="basket",
        transformation="tied with ribbon and paper flowers",
        hidden_ready="set on the shelf",
        tags={"flower", "surprise"},
    ),
}

MEMORIES = {
    "tea_memory": MemoryTrigger(
        id="tea_memory",
        scent="cinnamon",
        object_name="the little blue cup",
        flashback_line="the child was sitting beside grandma at the table, learning how to stir gently without spilling a drop.",
        tags={"tea", "flashback"},
    ),
    "cookie_memory": MemoryTrigger(
        id="cookie_memory",
        scent="vanilla",
        object_name="the wooden spoon",
        flashback_line="the child was standing on a stool while grandpa showed how to press cookie dough flat with a careful palm.",
        tags={"cookie", "flashback"},
    ),
    "flower_memory": MemoryTrigger(
        id="flower_memory",
        scent="fresh flowers",
        object_name="the green ribbon spool",
        flashback_line="the child was in the garden with auntie, making a tiny bouquet and laughing when a petal floated away.",
        tags={"flower", "flashback"},
    ),
}

CHILD_NAMES = ["Mina", "Lila", "Ari", "Noa", "Pia", "Sora", "Ivy", "Nina"]
LOVED_ONES = ["grandma", "mom", "dad", "aunt"]
TRAITS = ["quiet", "thoughtful", "gentle", "careful", "cheerful"]


@dataclass
class StoryParams:
    setting: str
    plan: str
    gift: str
    memory: str
    name: str
    loved_one: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s, setting in SETTINGS.items():
        for p, plan in PLANS.items():
            if p not in setting.affords and "decorating" not in setting.affords:
                continue
            for g, gift in GIFTS.items():
                if p == "tea_box" and g != "box":
                    continue
                if p == "cookie_tin" and g != "tin":
                    continue
                if p == "flower_basket" and g != "basket":
                    continue
                for m, mem in MEMORIES.items():
                    if p.split("_")[0] in mem.tags:
                        combos.append((s, p, g, m))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: one hour, a surprise, a flashback, and a gentle transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--loved-one", choices=LOVED_ONES, dest="loved_one")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.plan and args.gift:
        if args.plan == "tea_box" and args.gift != "box":
            raise StoryError("This plan needs a plain box.")
        if args.plan == "cookie_tin" and args.gift != "tin":
            raise StoryError("This plan needs a plain tin.")
        if args.plan == "flower_basket" and args.gift != "basket":
            raise StoryError("This plan needs a plain basket.")

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.plan is None or c[1] == args.plan)
              and (args.gift is None or c[2] == args.gift)
              and (args.memory is None or c[3] == args.memory)]
    if not combos:
        raise StoryError("(No valid story matches the given options.)")

    setting, plan, gift, memory = rng.choice(sorted(combos))
    name = args.name or rng.choice(CHILD_NAMES)
    loved_one = args.loved_one or rng.choice(LOVED_ONES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, plan=plan, gift=gift, memory=memory, name=name, loved_one=loved_one, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(id=params.name, kind="character", type="girl", label=params.name))
    if params.name in {"Ari", "Noa"}:
        child.type = "boy"
    loved_one = world.add(Entity(id=params.loved_one, kind="character", type=params.loved_one, label=params.loved_one))
    plan = PLANS[params.plan]
    gift_def = GIFTS[params.gift]
    memory = MEMORIES[params.memory]
    gift = world.add(Entity(
        id="gift",
        type=gift_def.type,
        label=gift_def.label,
        phrase=gift_def.phrase,
        owner=child.id,
        caretaker=child.id,
        hidden=True,
    ))
    container = world.add(Entity(
        id="container",
        type="container",
        label=gift_def.container,
        phrase=gift_def.hidden_ready,
    ))

    child.memes["love"] += 1
    child.memes["joy"] += 0.5

    world.say(
        f"At the start of the hour, {child.label} was in {world.setting.place} with a careful idea in mind: {plan.title}."
    )
    world.say(
        f"{child.pronoun().capitalize()} wanted to make a surprise for {loved_one.label}, using a {gift.label} and some {plan.material}."
    )

    world.para()
    world.say(
        f"{_make_sentence_start(world.time_left)} {child.pronoun().capitalize()} spread out the supplies and worked quietly."
    )
    _decorate(world, child, gift, plan)
    world.tick(15, narrate=False)

    world.say(
        f"Half an hour later, the room was a little brighter, and the {gift.label} already looked different."
    )
    _flashback(world, child, memory)
    world.tick(15, narrate=False)

    world.say(
        f"With only a little time left, {child.label} checked the door, then checked the gift again."
    )
    _fill(world, child, gift, plan)
    _hide(world, child, gift, container)
    _wait(world, child, loved_one)
    world.tick(20, narrate=False)

    world.para()
    _arrive(world, loved_one, child, gift)
    _finish(world, child, loved_one, gift)

    world.facts = {
        "child": child,
        "loved_one": loved_one,
        "plan": plan,
        "gift": gift,
        "memory": memory,
        "setting": world.setting,
    }
    return world


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    plan = f["plan"]
    loved = f["loved_one"]
    return [
        f'Write a gentle slice-of-life story about one hour of quiet preparation for {loved.label}.',
        f"Tell a short story where {child.label} makes {plan.title}, remembers an older moment, and ends with a happy surprise.",
        f'Write a child-facing story that includes a flashback and a transformation from plain to special.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    loved = f["loved_one"]
    plan = f["plan"]
    gift = f["gift"]
    memory = f["memory"]
    return [
        QAItem(
            question=f"What was {child.label} trying to make during the hour?",
            answer=f"{child.label} was trying to make {plan.title} for {loved.label}.",
        ),
        QAItem(
            question=f"What changed about the {gift.label} by the end?",
            answer=f"The {gift.label} changed from plain and hidden to decorated, filled, and ready to give.",
        ),
        QAItem(
            question=f"What brought on the flashback in the middle of the story?",
            answer=f"The smell of {memory.scent} brought on the flashback and reminded {child.label} of an older moment with family.",
        ),
        QAItem(
            question=f"Why did the surprise stay secret until the end?",
            answer=f"{child.label} kept it hidden so {loved.label} would only see it after it was finished and ready.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    plan = f["plan"]
    out = []
    if "tea" in plan.tags:
        out.append(QAItem("What is tea usually like?", "Tea is a warm drink made by soaking leaves or herbs in hot water."))
    if "cookie" in plan.tags:
        out.append(QAItem("Why do cookies smell good when they bake?", "Cookies smell good because warm ingredients release sweet-smelling scents as they bake."))
    if "flower" in plan.tags:
        out.append(QAItem("What are flowers for?", "Flowers are the colorful parts of many plants, and they can make a room or garden feel bright and cheerful."))
    out.append(QAItem("What is a surprise?", "A surprise is something you do not tell someone about ahead of time, so they do not expect it."))
    out.append(QAItem("What is a flashback?", "A flashback is a memory in a story that goes back to something that happened before."))
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden:
            bits.append("hidden=True")
        if e.decorated:
            bits.append("decorated=True")
        if e.filled:
            bits.append("filled=True")
        if e.transformed:
            bits.append("transformed=True")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  time_left={world.time_left}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "tea_box", "box", "tea_memory", "Mina", "grandma", "gentle"),
    StoryParams("living_room", "cookie_tin", "tin", "cookie_memory", "Lila", "dad", "thoughtful"),
    StoryParams("table", "flower_basket", "basket", "flower_memory", "Noa", "aunt", "careful"),
]


def explain_rejection(plan: Plan, gift: Gift) -> str:
    return f"(No story: {plan.title} needs a {plan.container}, not a {gift.label}.)"


ASP_RULES = r"""
% A story is reasonable when the plan matches the gift container.
compatible(P, G) :- plan(P), gift(G), plan_needs(P, C), gift_is(G, C).
valid_story(S, P, G, M) :- setting(S), compatible(P, G), memory_ok(P, M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p, plan in PLANS.items():
        lines.append(asp.fact("plan", p))
        lines.append(asp.fact("plan_needs", p, plan.container))
    for g, gift in GIFTS.items():
        lines.append(asp.fact("gift", g))
        lines.append(asp.fact("gift_is", g, gift.container))
    for m, mem in MEMORIES.items():
        lines.append(asp.fact("memory", m))
        for tag in sorted(mem.tags):
            lines.append(asp.fact("memory_ok", tag, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(s, p, g, m) for (s, p, g, m) in valid_combos()}
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_program_for_show() -> str:
    return asp_program("#show valid_story/4.")


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
        print(build_program_for_show())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print(" ", row)
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
            header = f"### {p.name}: {p.plan} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
