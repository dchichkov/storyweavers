#!/usr/bin/env python3
"""
storyworlds/worlds/system_caterpillar_small_kindness_rhyme_fable.py
===================================================================

A small fable world about a caterpillar, a little system of paths and leaves,
and the gentle turns made by Kindness and Rhyme.

Seed image:
---
A small caterpillar lived inside a tiny garden system of moss paths, leaf
bridges, and dew drops. The caterpillar liked to hum rhymes while it worked,
and it believed kindness could make even a small world feel roomy.

One day the system grew tangled after the wind bent a leaf bridge and a little
neighbor got stuck. The caterpillar could hurry past, or stop and help. It
chose kindness, sang a rhyme to keep time, and mended the path with patient
steps. In the end the small system felt brighter, and everyone had a better way
to travel.

World model:
---
- The garden is a small system of connected places.
- The caterpillar has physical meters like tired, wet, carried, and safe.
- Emotional memes track kindness, worry, hope, and pride.
- Rhyme is not decoration; it is a method that steadies helpers and guides work.
- Kindness is not abstract either; it causes shared labor, lowered worry, and a
  more open path through the system.
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
    place: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"caterpillar"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"snail", "ant", "beetle"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    supports: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    rhyme_line: str
    method: str
    risk: str
    outcome: str
    requires: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _get_meters(e: Entity) -> dict[str, float]:
    return e.meters


def _get_memes(e: Entity) -> dict[str, float]:
    return e.memes


def meter_inc(e: Entity, key: str, amount: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amount


def meme_inc(e: Entity, key: str, amount: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amount


def meme_set(e: Entity, key: str, value: float) -> None:
    e.memes[key] = value


def meter_get(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def meme_get(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


@dataclass
class Rule:
    name: str
    apply: callable


def _r_kindness_spreads(world: World) -> list[str]:
    out: list[str] = []
    cat = world.get("caterpillar")
    if meter_get(cat, "helped") < THRESHOLD:
        return out
    for ent in world.entities.values():
        if ent.id == "caterpillar":
            continue
        sig = ("kindness", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        meme_inc(ent, "hope", 1)
        meme_inc(ent, "calm", 1)
        out.append(f"The little system grew calmer where help had been given.")
    return out


def _r_rhyme_guides(world: World) -> list[str]:
    out: list[str] = []
    cat = world.get("caterpillar")
    if meter_get(cat, "sang") < THRESHOLD:
        return out
    if ("rhyme", cat.id) in world.fired:
        return out
    world.fired.add(("rhyme", cat.id))
    meme_inc(cat, "pride", 1)
    out.append("The rhyme kept the work steady and the steps in order.")
    return out


def _r_fix_path(world: World) -> list[str]:
    out: list[str] = []
    cat = world.get("caterpillar")
    bridge = world.get("leaf_bridge")
    if meter_get(cat, "helped") < THRESHOLD:
        return out
    if meter_get(bridge, "mended") >= THRESHOLD:
        return out
    if ("mend", bridge.id) in world.fired:
        return out
    world.fired.add(("mend", bridge.id))
    meter_inc(bridge, "mended", 1)
    out.append("The leaf bridge settled back into place.")
    return out


CAUSAL_RULES = [
    Rule("kindness_spreads", _r_kindness_spreads),
    Rule("rhyme_guides", _r_rhyme_guides),
    Rule("fix_path", _r_fix_path),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_outcome(world: World, task: Task) -> dict:
    sim = world.copy()
    caterpillar = sim.get("caterpillar")
    apply_task(sim, caterpillar, task, narrate=False)
    bridge = sim.get("leaf_bridge")
    stuck = sim.get("snail")
    return {
        "mended": meter_get(bridge, "mended") >= THRESHOLD,
        "calm": meme_get(stuck, "calm") > 0 or meme_get(sim.get("caterpillar"), "pride") > 0,
    }


def apply_task(world: World, cat: Entity, task: Task, narrate: bool = True) -> None:
    if task.id not in world.setting.supports:
        return
    if task.requires and not task.requires.issubset({world.setting.id, "kindness", "rhyme"}):
        return
    if task.id == "mend":
        meter_inc(cat, "helped", 1)
        meme_inc(cat, "kindness", 1)
        meter_inc(world.get("leaf_bridge"), "mended", 1)
        meme_inc(world.get("snail"), "calm", 1)
        propagate(world, narrate=narrate)
    elif task.id == "guide":
        meter_inc(cat, "sang", 1)
        meme_inc(cat, "kindness", 1)
        meme_inc(cat, "hope", 1)
        propagate(world, narrate=narrate)
    elif task.id == "share":
        meter_inc(cat, "shared", 1)
        meme_inc(cat, "kindness", 1)
        meter_inc(world.get("crumb"), "used", 1)
        meme_inc(world.get("ant"), "hope", 1)
        propagate(world, narrate=narrate)


def intro(world: World, cat: Entity) -> None:
    world.say(
        f"In {world.setting.place}, a small caterpillar lived in a tidy little system of leaves, moss, and narrow paths."
    )
    world.say(
        f"{cat.id.capitalize()} loved Kindness, and {cat.pronoun('subject')} liked Rhyme as a way to keep work gentle and steady."
    )


def describe_setting(world: World) -> None:
    world.say(world.setting.detail)


def establish(world: World, cat: Entity, task: Task) -> None:
    world.say(
        f"Each day {cat.id} had a job: to {task.verb}. When {cat.pronoun('subject')} worked, {task.rhyme_line}"
    )


def trouble(world: World, cat: Entity, task: Task) -> None:
    snail = world.get("snail")
    bridge = world.get("leaf_bridge")
    world.say(
        f"One windy morning, the leaf bridge bent the wrong way, and the little snail got stuck beside it."
    )
    world.say(
        f"{cat.id} wanted to hurry past, but {cat.pronoun('subject')} saw that the path would stay blocked unless someone gave time and care."
    )
    if task.id == "mend":
        world.say(
            f"The bent bridge could hurt tiny feet, and the snail looked worried under the leaf shadow."
        )
    elif task.id == "guide":
        world.say(
            f"The route was confused, and even the moss markers looked mixed up."
        )
    else:
        world.say(
            f"The crumb cache lay scattered, and the ant waited with an empty basket."
        )


def turn(world: World, cat: Entity, task: Task) -> None:
    world.say(
        f"{cat.id} chose Kindness instead of speed, and {cat.pronoun('subject')} began to {task.method}."
    )
    world.say(
        f"{cat.id} sang softly: \"{task.rhyme_line}\""
    )
    apply_task(world, cat, task, narrate=True)


def resolve(world: World, cat: Entity, task: Task) -> None:
    bridge = world.get("leaf_bridge")
    snail = world.get("snail")
    ant = world.get("ant")
    if task.id == "mend":
        world.say(
            f"The bridge straightened, the snail could glide on, and the path opened again."
        )
    elif task.id == "guide":
        world.say(
            f"The rhyme pointed the way, and the small system of paths felt clear again."
        )
    else:
        world.say(
            f"The crumb was shared, the ant smiled, and no one went hungry on the tiny trail."
        )
    world.say(
        f"By evening, {cat.id} was not bigger, but the little world was kinder, and that made it roomier than before."
    )


SETTINGS = {
    "moss_lane": Setting(
        id="moss_lane",
        place="the moss lane",
        detail="The moss lane was soft, and the stone edges made a neat little border for each step.",
        supports={"mend", "guide", "share"},
    ),
    "leaf_bridge": Setting(
        id="leaf_bridge",
        place="the leaf bridge",
        detail="The leaf bridge crossed a shallow drip of water, and every breeze made it wobble a little.",
        supports={"mend", "guide"},
    ),
    "dew_circle": Setting(
        id="dew_circle",
        place="the dew circle",
        detail="The dew circle shone like a tiny mirror, and the air felt fresh enough to hum in.",
        supports={"guide", "share"},
    ),
}

TASKS = {
    "mend": Task(
        id="mend",
        verb="mend the leaf bridge",
        rhyme_line="one leaf, two leaf, back to place, a steady path for every face",
        method="press the stem flat and tuck the leaf edge under the moss",
        risk="the bridge stays bent",
        outcome="the bridge is safe again",
        requires={"kindness", "rhyme"},
    ),
    "guide": Task(
        id="guide",
        verb="guide the little travelers",
        rhyme_line="left step, right step, gentle and small, follow the song and you won't fall",
        method="sing a clear tune and tap the path stones in time",
        risk="the path stays confusing",
        outcome="the path is clear again",
        requires={"kindness", "rhyme"},
    ),
    "share": Task(
        id="share",
        verb="share the crumb",
        rhyme_line="a crumb for you, a crumb for me, that's how a small feast ought to be",
        method="divide the crumb and pass the pieces in turn",
        risk="someone stays hungry",
        outcome="everyone gets a bite",
        requires={"kindness", "rhyme"},
    ),
}

NAMES = ["Pip", "Milo", "Tansy", "Pippa", "Clover"]
NEIGHBORS = {
    "snail": "a patient snail",
    "ant": "a busy ant",
    "beetle": "a careful beetle",
}


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid, task in TASKS.items():
            if tid in setting.supports:
                combos.append((sid, tid))
    return combos


@dataclass
class StoryParams:
    setting: str
    task: str
    name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small fable about a caterpillar, a system of paths, Kindness, and Rhyme."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name", choices=NAMES)
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
              if (args.setting is None or c[0] == args.setting)
              and (args.task is None or c[1] == args.task)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(setting=setting, task=task, name=name)


def generate_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    cat = world.add(Entity(
        id="caterpillar",
        kind="character",
        type="caterpillar",
        label="small caterpillar",
        phrase="a small caterpillar",
        meters={"helped": 0.0, "sang": 0.0, "shared": 0.0},
        memes={"kindness": 1.0, "worry": 0.0, "hope": 1.0, "pride": 0.0},
    ))
    world.add(Entity(
        id="snail",
        kind="character",
        type="snail",
        label="snail",
        phrase="a patient snail",
        meters={"stuck": 1.0},
        memes={"worry": 1.0, "calm": 0.0, "hope": 0.0},
    ))
    world.add(Entity(
        id="ant",
        kind="character",
        type="ant",
        label="ant",
        phrase="a busy ant",
        meters={"hungry": 1.0},
        memes={"hope": 0.0},
    ))
    world.add(Entity(
        id="leaf_bridge",
        type="bridge",
        label="leaf bridge",
        phrase="a green leaf bridge",
        meters={"mended": 0.0},
        memes={},
    ))
    world.add(Entity(
        id="crumb",
        type="crumb",
        label="crumb",
        phrase="a tiny crumb",
        meters={"used": 0.0},
        memes={},
    ))
    world.facts.update(params=params, cat=cat, task=TASKS[params.task], setting=SETTINGS[params.setting])
    return world


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    cat = world.get("caterpillar")
    task = TASKS[params.task]
    intro(world, cat)
    describe_setting(world)
    establish(world, cat, task)
    world.para()
    trouble(world, cat, task)
    world.para()
    turn(world, cat, task)
    resolve(world, cat, task)
    world.facts.update(task=task, cat=cat, bridge=world.get("leaf_bridge"), snail=world.get("snail"), ant=world.get("ant"))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    task = world.facts["task"]
    return [
        f'Write a short fable for a small child about a {p.name.lower()}-like caterpillar in {world.setting.place} that uses Kindness and Rhyme.',
        f"Tell a small story where a caterpillar must {task.verb}, and a gentle rhyme helps the work get done.",
        f"Write a simple moral tale set in a tiny garden system, with a bent path and a kinder ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    task = world.facts["task"]
    cat = world.facts["cat"]
    bridge = world.facts["bridge"]
    snail = world.facts["snail"]
    ant = world.facts["ant"]
    return [
        QAItem(
            question=f"What kind of little story is this one about {p.name} and the caterpillar?",
            answer="It is a small fable about a caterpillar, a tiny garden system, and the good things that happen when Kindness and Rhyme are used together.",
        ),
        QAItem(
            question=f"What did the caterpillar want to do in {world.setting.place}?",
            answer=f"The caterpillar wanted to {task.verb}.",
        ),
        QAItem(
            question="What problem made the caterpillar stop and think?",
            answer="The leaf bridge bent the wrong way, and the snail was stuck nearby, so the path needed help before anyone could pass safely.",
        ),
        QAItem(
            question="How did the caterpillar help?",
            answer=f"The caterpillar chose Kindness, sang a rhyme, and {task.method}. That helped the little system become safe again.",
        ),
        QAItem(
            question="What changed by the end?",
            answer="The bridge was set right, the travelers could move again, and the small world felt kinder and roomier.",
        ),
        QAItem(
            question="Why was the rhyme useful?",
            answer="The rhyme kept the work steady and the steps in order, so the helping did not feel rushed or tangled.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a caterpillar?",
            answer="A caterpillar is a small crawling creature that eats leaves and later changes into a butterfly or moth.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing to help, share, or be gentle so another creature feels safer and happier.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a line of words that sounds musical because the ending sounds match, like when a song or poem has a beat.",
        ),
    ]


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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.place:
            bits.append(f"place={e.place}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="leaf_bridge", task="mend", name="Pip"),
    StoryParams(setting="moss_lane", task="guide", name="Clover"),
    StoryParams(setting="dew_circle", task="share", name="Tansy"),
]


ASP_RULES = r"""
setting(S) :- setting_fact(S).
task(T) :- task_fact(T).

valid(S,T) :- setting_fact(S), task_fact(T), supports(S,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting_fact", sid))
        for t in sorted(s.supports):
            lines.append(asp.fact("supports", sid, t))
    for tid in TASKS:
        lines.append(asp.fact("task_fact", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def explain_rejection(setting: Setting, task: Task) -> str:
    return (
        f"(No story: {task.verb} does not fit {setting.place}. "
        f"This small fable needs a setting that truly supports that kind of helping.)"
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, task) combos:\n")
        for s, t in combos:
            print(f"  {s:12} {t}")
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
            header = f"### {p.name}: {p.task} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        if header:
            print(header)
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
