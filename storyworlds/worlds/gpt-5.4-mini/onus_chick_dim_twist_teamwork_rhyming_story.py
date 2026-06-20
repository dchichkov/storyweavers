#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/onus_chick_dim_twist_teamwork_rhyming_story.py
===============================================================================

A standalone story world for a tiny rhyming farm tale: a young chick faces an
onus, the coop grows dim, a twist changes the plan, and teamwork saves the day.

The domain is built to satisfy the seed words and features:
- onus
- chick-dim
- Twist
- Teamwork
- Rhyming Story

The storyworld simulates a small world with typed entities, physical meters,
and emotional memes. The plot is driven by world state, not by swapping nouns in
a frozen paragraph.
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
RHYME_TAG = "rhyming"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    dim_phrase: str
    rhyme_end: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Task:
    id: str
    onus: str
    action: str
    risk: str
    twist: str
    done_line: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Tool:
    id: str
    label: str
    use: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_dark(world: World) -> list[str]:
    out: list[str] = []
    if world.get("coop").meters["dim"] < THRESHOLD:
        return out
    if ("dark",) in world.fired:
        return out
    world.fired.add(("dark",))
    for ch in world.characters():
        ch.memes["worry"] += 1
    out.append("__dark__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if world.get("crew").memes["teamwork"] < THRESHOLD:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("coop").meters["bright"] += 1
    out.append("__bright__")
    return out


CAUSAL_RULES = [Rule("dark", _r_dark), Rule("teamwork", _r_teamwork)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(x for x in sents if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_task(world: World, chick: Entity, task: Task, helper: Entity, tool: Tool, narrate: bool = True) -> None:
    chick.meters["onus"] += 1
    chick.memes["brave"] += 1
    if tool.safe:
        helper.memes["helpful"] += 1
    world.get("coop").meters["dim"] += 1
    propagate(world, narrate=narrate)


def setup_story(world: World, chick: Entity, helper: Entity, setting: Setting, task: Task) -> None:
    world.say(
        f"In a {setting.place}, a little chick named {chick.id} peeped with a sigh. "
        f"The day had a soft hush, and the coop was {setting.dim_phrase}."
    )
    world.say(
        f"{chick.id} had an {task.onus} to {task.action}, but the shadows were long and the work felt big."
    )
    helper.memes["kindness"] += 1
    world.say(
        f"{helper.id} came near and said, \"Little chick, don't fret and don't flee; "
        f"we can solve this with you and me.\""
    )


def present_problem(world: World, chick: Entity, helper: Entity, task: Task) -> None:
    world.say(
        f"{chick.id} looked at the {task.risk} and felt the twist in the plan: "
        f"the first idea would not do, and the coop still looked dim and wan."
    )


def twist(world: World, chick: Entity, helper: Entity, task: Task, tool: Tool) -> None:
    chick.memes["surprise"] += 1
    world.say(
        f"Then came a twist in the light: {helper.id} found {tool.label} in a bright little shelf. "
        f'\"That tool will do,\" {helper.id} said, \"and you can help too.\"'
    )


def teamwork(world: World, chick: Entity, helper: Entity, task: Task, tool: Tool) -> None:
    chick.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    world.get("crew").memes["teamwork"] += 1
    world.say(
        f"Together they moved with cheer: {chick.id} held the eggs, {helper.id} held the tray, "
        f"and the safe {tool.use} made the hard work light as day."
    )
    world.say(task.done_line)


def ending(world: World, chick: Entity, helper: Entity) -> None:
    coop = world.get("coop")
    coop.meters["dim"] = max(0.0, coop.meters["dim"] - 1.0)
    coop.meters["bright"] += 1
    chick.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"By the end, the coop was no longer dim; it glowed and hummed with a gentle beam. "
        f"{chick.id} felt proud of the onus done, and {helper.id} smiled at the teamwork dream."
    )
    world.say(
        f"The little chick chirped, \"What once felt grim now feels like a trim little hymn!\""
    )


def tell(setting: Setting, task: Task, tool: Tool, chick_name: str, helper_name: str) -> World:
    world = World()
    chick = world.add(Entity(id=chick_name, kind="character", type="chick", role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type="hen", role="helper", traits=["kind"]))
    coop = world.add(Entity(id="coop", type="coop", label="the coop"))
    crew = world.add(Entity(id="crew", type="group", label="the little crew"))
    world.add(Entity(id="tool", type="thing", label=tool.label))
    chick.memes["curious"] += 1
    helper.memes["care"] += 1
    setup_story(world, chick, helper, setting, task)
    world.para()
    present_problem(world, chick, helper, task)
    twist(world, chick, helper, task, tool)
    world.para()
    _do_task(world, chick, task, helper, tool, narrate=False)
    teamwork(world, chick, helper, task, tool)
    world.para()
    ending(world, chick, helper)
    world.facts.update(
        chick=chick,
        helper=helper,
        setting=setting,
        task=task,
        tool=tool,
        outcome="bright",
    )
    return world


SETTINGS = {
    "coop": Setting("coop", "small farm coop", "a chick-dim little nook", "dim"),
    "barn": Setting("barn", "barn corner", "a chick-dim shadow", "barn"),
    "yard": Setting("yard", "sunny yard", "a chick-dim patch", "yard"),
}

TASKS = {
    "eggs": Task(
        "eggs",
        onus="onus",
        action="gather the eggs",
        risk="wobbly basket",
        twist="a cracked egg",
        done_line="The eggs were gathered, snug and neat, and none were cracked at all.",
        tags={RHYME_TAG, "eggs", "teamwork"},
    ),
    "feed": Task(
        "feed",
        onus="onus",
        action="carry the feed",
        risk="heavy sack",
        twist="a torn bag",
        done_line="The feed was shared, the path was clear, and no grain spilled near.",
        tags={RHYME_TAG, "feed", "teamwork"},
    ),
    "lights": Task(
        "lights",
        onus="onus",
        action="set the lanterns right",
        risk="low shelves",
        twist="a blown-out wick",
        done_line="The lights all shone, soft and sweet, with every lantern in its seat.",
        tags={RHYME_TAG, "light", "teamwork"},
    ),
}

TOOLS = {
    "lantern": Tool("lantern", "a little lantern", "lantern", True, tags={"light"}),
    "cart": Tool("cart", "a little cart", "cart", True, tags={"teamwork"}),
    "basket": Tool("basket", "a woven basket", "basket", True, tags={"eggs"}),
}

CHICK_NAMES = ["Pip", "Dot", "Nip", "Tilly", "Peep"]
HELPER_NAMES = ["Henna", "Nora", "Mabel", "June", "Bess"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    task: str
    tool: str
    chick: str
    helper: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TASKS:
            for u in TOOLS:
                combos.append((s, t, u))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld about an onus, a dim coop, a twist, and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--chick")
    ap.add_argument("--helper")
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
    if not combos:
        raise StoryError("No valid stories.")
    setting, task, tool = rng.choice(combos)
    chick = args.chick or rng.choice(CHICK_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != chick])
    return StoryParams(args.setting or setting, args.task or task, args.tool or tool, chick, helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story that includes the words "{f["task"].onus}" and "chick-dim".',
        f"Tell a small farm tale where {f['chick'].id} has an onus to {f['task'].action} in a dim coop, then a twist changes the plan and teamwork helps.",
        f"Write a child-friendly rhyme about a little chick, a helper, and a bright teamwork ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    chick, helper, task = f["chick"], f["helper"], f["task"]
    return [
        QAItem(
            question=f"What onus did {chick.id} have?",
            answer=f"{chick.id} had the onus to {task.action}. It was a real job, and it felt harder because the coop was dim."
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {helper.id} found a safe tool and a new idea. That changed the plan and let them finish the job together."
        ),
        QAItem(
            question="How did teamwork help at the end?",
            answer=f"They split the work and helped each other step by step. Because they worked as a team, the task got done and the coop grew bright again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does teamwork mean?", "Teamwork means people help each other and share the work so the job is easier."),
        QAItem("What does dim mean?", "Dim means not very bright. A dim place has only a little light."),
        QAItem("What is a chick?", "A chick is a baby bird, and baby birds often need help and care."),
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
dim(coop) :- coop_dim(C), C >= 1.
teamwork_ready :- teamwork(C), C >= 1.
bright_end :- dim(coop), teamwork_ready.
valid_story(S, T, U) :- setting(S), task(T), tool(U).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for uid in TOOLS:
        lines.append(asp.fact("tool", uid))
    lines.append(asp.fact("coop_dim", 1))
    lines.append(asp.fact("teamwork", 1))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import io
    import contextlib

    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(StoryParams("coop", "eggs", "lantern", "Pip", "Henna"))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True)
        _ = buf.getvalue()
        print("OK: smoke test generate/emit succeeded.")
    except Exception as e:
        ok = False
        print(f"SMOKE TEST FAILED: {e}")
    return 0 if ok else 1


CURATED = [
    StoryParams("coop", "eggs", "basket", "Pip", "Henna"),
    StoryParams("barn", "feed", "cart", "Dot", "Mabel"),
    StoryParams("yard", "lights", "lantern", "Peep", "June"),
]


def explain_rejection() -> str:
    return "(No story: this world keeps the task, the dim place, and the team-up nicely aligned.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TASKS[params.task], TOOLS[params.tool], params.chick, params.helper)
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
        print(asp_program("", "#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
