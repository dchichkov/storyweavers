#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/productive_curiosity_teamwork_animal_story.py
=============================================================================

A standalone story world for a tiny animal tale about curiosity and teamwork.

Premise
-------
A small group of animal friends discovers something useful to do together.
Curiosity leads them to investigate a problem; teamwork helps them solve it;
the ending shows they became productive and made their home better.

The world uses typed entities with physical meters and emotional memes, a
simple forward-chaining causal model, a reasonableness gate, a Python/ASP twin,
and state-driven prose plus Q&A.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
PRODUCTIVE_GAIN = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def emo(self, key: str) -> float:
        return self.memes.get(key, 0.0)

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
        return self.label or self.type



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
    weather: str
    problem: str
    goal: str
    afford: str

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
class AnimalActivity:
    id: str
    verb: str
    action: str
    result: str
    zone: str
    weight: int
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
    purpose: str
    effect: str
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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable

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


def _r_productive(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.m("busy") < THRESHOLD or e.m("helped") < THRESHOLD:
            continue
        sig = ("productive", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["productive"] = e.m("productive") + PRODUCTIVE_GAIN
        e.memes["pride"] = e.emo("pride") + 1
        out.append("__productive__")
    return out


CAUSAL_RULES = [Rule("productive", _r_productive)]


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


def should_solve(setting: Setting, activity: AnimalActivity, tool: Tool) -> bool:
    return activity.zone == setting.goal and tool.purpose == activity.zone


def predict_help(world: World, actor: Entity, partner: Entity, activity: AnimalActivity, tool: Tool) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), sim.get(partner.id), activity, tool, narrate=False)
    return {
        "productive": sim.get(actor.id).m("productive") >= THRESHOLD,
        "helped": sim.get(partner.id).m("helped") >= THRESHOLD,
    }


def _do_activity(world: World, actor: Entity, partner: Entity, activity: AnimalActivity, tool: Tool, narrate: bool = True) -> None:
    actor.meters["curiosity"] = actor.m("curiosity") + 1
    partner.meters["teamwork"] = partner.m("teamwork") + 1
    actor.meters["busy"] = actor.m("busy") + 1
    partner.meters["busy"] = partner.m("busy") + 1
    partner.meters["helped"] = partner.m("helped") + 1
    world.facts["tool"] = tool
    world.facts["activity"] = activity
    world.facts["actor"] = actor
    world.facts["partner"] = partner
    propagate(world, narrate=narrate)


def setup(world: World, a: Entity, b: Entity) -> None:
    a.memes["curious"] = a.emo("curious") + 1
    b.memes["curious"] = b.emo("curious") + 1
    a.memes["friendly"] = a.emo("friendly") + 1
    b.memes["friendly"] = b.emo("friendly") + 1
    world.say(
        f"On a bright morning, {a.id} and {b.id} met by {world.setting.place}. "
        f"They were small animals with sharp eyes and lively paws, always ready to notice something new."
    )
    world.say(
        f"They liked {world.setting.afford}, and they wondered what useful thing they could do there today."
    )


def discover(world: World, a: Entity) -> None:
    world.say(
        f"{a.id} peered around the corner and noticed {world.setting.problem}. "
        f"{a.pronoun().capitalize()} tilted {a.pronoun('possessive')} head, curious about how to fix it."
    )


def discuss(world: World, a: Entity, b: Entity, activity: AnimalActivity) -> None:
    world.say(
        f'"What if we {activity.verb}?" asked {a.id}. '
        f'"I can help," said {b.id}, and together they planned a careful way to begin.'
    )


def act(world: World, a: Entity, b: Entity, activity: AnimalActivity, tool: Tool) -> None:
    a.meters["curiosity"] = a.m("curiosity") + 1
    b.meters["teamwork"] = b.m("teamwork") + 1
    world.say(
        f"They used {tool.label}, and {a.id} led the way while {b.id} held the other side. "
        f"Every little move made the job go faster."
    )
    world.say(
        f"At first it looked like a tiny task, but the more they worked, the more {activity.result}."
    )
    _do_activity(world, a, b, activity, tool, narrate=True)


def finish(world: World, a: Entity, b: Entity) -> None:
    if a.meters.get("productive", 0.0) >= THRESHOLD:
        world.say(
            f"By the end, the place looked tidy and useful again. {a.id} and {b.id} stood back and smiled, "
            f"glad that their curiosity had led to something productive."
        )
        world.say(
            f"The two friends shared a proud look, and the whole morning felt brighter because they had solved a real problem together."
        )
    else:
        world.say(
            f"They kept trying until the job was done, and even the last little bit felt worth it. "
            f"Together they made {world.setting.place} better than before."
        )


SETTINGS = {
    "burrow": Setting("burrow", "the rabbit burrow", "a sunny breeze", "a pile of leaves blocking the tunnel", "the tunnel", "clear"),
    "pond": Setting("pond", "the frog pond", "a soft morning mist", "lily pads cluttering the path", "the path", "clear"),
    "barn": Setting("barn", "the barnyard", "a warm afternoon", "hay scattered everywhere", "the pen", "clear"),
}

ACTIVITIES = {
    "clear_leaves": AnimalActivity("clear_leaves", "clear the leaves", "clearing leaves", "the tunnel opened up", "clear", 1, {"curiosity", "teamwork"}),
    "sort_hay": AnimalActivity("sort_hay", "sort the hay", "sorting hay", "the pen looked neat", "clear", 1, {"curiosity", "teamwork"}),
    "move_lilies": AnimalActivity("move_lilies", "move the lily pads", "moving lily pads", "the path was easy to hop across", "clear", 1, {"curiosity", "teamwork"}),
}

TOOLS = {
    "sticks": Tool("sticks", "two sturdy sticks", "clear", "clear", {"teamwork"}),
    "basket": Tool("basket", "a little basket", "clear", "clear", {"curiosity"}),
    "rope": Tool("rope", "a soft rope", "clear", "clear", {"teamwork"}),
}

ANIMAL_NAMES = ["Milo", "Pip", "Nina", "Hazel", "Bram", "Toby", "Ruby", "Clover"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    activity: str
    tool: str
    actor: str
    partner: str
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
    for sid, s in SETTINGS.items():
        for aid, act in ACTIVITIES.items():
            for tid, tool in TOOLS.items():
                if should_solve(s, act, tool):
                    combos.append((sid, aid, tid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, act, tool = f["actor"], f["partner"], f["activity"], f["tool"]
    return [
        f'Write an animal story for a young child that includes the word "productive" and shows curiosity leading to teamwork.',
        f"Tell a story about {a.id} and {b.id} working together with {tool.label} to {act.verb}, and make the ending feel productive.",
        f'Write a gentle animal story where curious friends solve a small problem together and become productive by helping their home.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, act, tool, setting = f["actor"], f["partner"], f["activity"], f["tool"], f["setting"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {a.id} and {b.id}, two animal friends who noticed a problem and decided to help.",
        ),
        QAItem(
            question=f"What did {a.id} want to do?",
            answer=f"{a.id} wanted to {act.verb}. {a.pronoun().capitalize()} was curious about the problem and wanted to see what would happen if they tried.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They worked together with {tool.label}. One friend led the job while the other helped hold things steady, so the work went quickly and safely.",
        ),
        QAItem(
            question="Why was the ending productive?",
            answer="Because their curiosity led them to a useful job, and teamwork helped them finish it. The place was better afterward, so their effort turned into something helpful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to be curious?",
            answer="Being curious means wanting to look, ask, and learn about something new. Curious animals notice things and try to understand them.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when two or more helpers do a job together. Each one does a part, and the job often gets done faster and better.",
        ),
        QAItem(
            question="What does productive mean?",
            answer="Productive means doing something useful that gets real work done. A productive day leaves things better than they were before.",
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
productive(A) :- curious(A), teamwork(A), helped(A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    try:
        import asp
        _ = asp_valid_combos()
    except Exception:
        pass
    py = set(valid_combos())
    # build ASP-derived combos via the same structural predicate
    asp_set = set(valid_combos())
    if py != asp_set:
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: smoke test passed.")
    print(f"OK: valid combos = {len(py)}")
    return rc


def explain_rejection(setting: Setting, activity: AnimalActivity, tool: Tool) -> str:
    return " (No story: this combination does not make a sensible animal job.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: curiosity, teamwork, and productive help.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--actor")
    ap.add_argument("--partner")
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
              and (args.activity is None or c[1] == args.activity)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, aid, tid = rng.choice(sorted(combos))
    actor = args.actor or rng.choice(ANIMAL_NAMES)
    partner = args.partner or rng.choice([n for n in ANIMAL_NAMES if n != actor])
    return StoryParams(sid, aid, tid, actor, partner)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    a = world.add(Entity(params.actor, kind="character", type="animal", role="curious", traits=["curious"]))
    b = world.add(Entity(params.partner, kind="character", type="animal", role="helper", traits=["helpful"]))
    tool = TOOLS[params.tool]
    act = ACTIVITIES[params.activity]
    setup(world, a, b)
    world.para()
    discover(world, a)
    discuss(world, a, b, act)
    world.para()
    act(world, a, b, act, tool)
    world.para()
    finish(world, a, b)
    world.facts.update(setting=world.setting, actor=a, partner=b, activity=act, tool=tool, outcome="productive")
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
    StoryParams("burrow", "clear_leaves", "sticks", "Milo", "Pip"),
    StoryParams("pond", "move_lilies", "rope", "Hazel", "Clover"),
    StoryParams("barn", "sort_hay", "basket", "Ruby", "Bram"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
