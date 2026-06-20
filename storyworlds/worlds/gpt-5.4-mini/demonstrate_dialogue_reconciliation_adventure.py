#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/demonstrate_dialogue_reconciliation_adventure.py
================================================================================

A small standalone storyworld for an adventure tale with dialogue and
reconciliation.

Premise:
- Two children are on a little adventure trail.
- They disagree about how to cross or proceed.
- One child demonstrates a safe way or useful skill.
- They talk, reconcile, and end the day together with a clear changed state.

The story is built from simulated world state rather than a frozen template.
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
from typing import Optional

# Make shared result containers importable when run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
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
    trail: str
    view: str
    ending_image: str
    hazards: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Objective:
    id: str
    goal: str
    approach: str
    keyword: str
    outcome_phrase: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    phrase: str
    helps_with: set[str]
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def _safe_name(name: str) -> str:
    return name


def would_reconcile(relation: str, guide_age: int, eager_age: int, trait: str) -> bool:
    if relation != "siblings":
        return False
    if guide_age <= eager_age:
        return False
    return trait in {"calm", "patient", "thoughtful", "wise"}


def path_danger(objective: Objective, setting: Setting) -> bool:
    return objective.keyword in setting.hazards


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def is_success(response: Response, objective: Objective, delay: int) -> bool:
    return response.power >= (objective_power(objective) + delay)


def objective_power(objective: Objective) -> int:
    return 2 if objective.id in {"cross_bridge", "find_cave"} else 1


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        # reconciliation reduces conflict if both children have listened
        a = world.entities.get("guide")
        b = world.entities.get("eager")
        if a and b:
            sig = ("reconcile", a.id, b.id)
            if sig not in world.fired and a.memes["reconcile"] >= THRESHOLD and b.memes["reconcile"] >= THRESHOLD:
                world.fired.add(sig)
                a.memes["conflict"] = 0.0
                b.memes["conflict"] = 0.0
                a.memes["joy"] += 1
                b.memes["joy"] += 1
                out.append("__reconcile__")
                changed = True
    if narrate:
        for s in out:
            if s != "__reconcile__":
                world.say(s)
    return out


def predict(world: World, objective: Objective) -> bool:
    sim = world.copy()
    sim.get("eager").meters["risk"] += 1
    sim.get("guide").meters["proof"] += 1
    return path_danger(objective, world.get("setting").attrs["setting_obj"])


def setup(world: World, setting: Setting, guide: Entity, eager: Entity, objective: Objective) -> None:
    guide.memes["curiosity"] += 1
    eager.memes["curiosity"] += 1
    world.say(
        f"On a bright morning, {guide.id} and {eager.id} set out along {setting.trail}. "
        f"{setting.view.capitalize()} waited ahead, and the two children felt the pull of adventure."
    )
    world.say(
        f'"Look!" {eager.id} said. "We can {objective.goal} and see what is on the other side!"'
    )


def argue(world: World, eager: Entity, guide: Entity, objective: Objective, setting: Setting) -> None:
    eager.memes["defiance"] += 1
    world.say(
        f'"I want to go first," {eager.id} said. "{objective.approach} sounds faster."'
    )
    world.say(
        f'"Wait," {guide.id} replied. "{setting.ending_image} could hide a problem. Let me demonstrate a safer way."'
    )


def demonstrate(world: World, guide: Entity, tool: Tool, objective: Objective, setting: Setting) -> None:
    guide.memes["reconcile"] += 1
    guide.meters["proof"] += 1
    world.say(
        f"{guide.id} knelt down and used {tool.phrase} to demonstrate a careful step. "
        f"{guide.pronoun().capitalize()} showed how the tool helped without rushing."
    )
    world.say(
        f'"See?" {guide.id} said. "When we use {tool.label}, we can keep moving and still stay safe."'
    )


def reconcile(world: World, eager: Entity, guide: Entity) -> None:
    eager.memes["reconcile"] += 1
    world.say(
        f'{eager.id} looked at {guide.id} and nodded. "I was too eager," {eager.id} admitted. '
        f'"Thanks for showing me."'
    )
    world.say(
        f'{guide.id} smiled back. "We can do this together."'
    )
    propagate(world, narrate=True)


def venture(world: World, setting: Setting, objective: Objective) -> None:
    world.say(
        f"Together they followed the trail, and the {setting.place} opened wide in front of them."
    )
    world.say(
        f"They reached the place where they needed to {objective.goal}, and the little challenge was no longer scary."
    )


def ending(world: World, setting: Setting, objective: Objective, tool: Tool) -> None:
    world.say(
        f"In the end, the children kept {tool.label} ready, crossed with steady steps, and reached the {setting.ending_image}."
    )
    world.say(
        f"{objective.outcome_phrase.capitalize()}, and their friendship felt stronger than before."
    )


def tell(setting: Setting, objective: Objective, tool: Tool, response: Response,
         guide_name: str = "Mara", guide_gender: str = "girl",
         eager_name: str = "Leo", eager_gender: str = "boy",
         guide_trait: str = "calm", relation: str = "siblings",
         delay: int = 0, guide_age: int = 7, eager_age: int = 5) -> World:
    world = World()
    guide = world.add(Entity(id=_safe_name(guide_name), kind="character", type=guide_gender,
                             role="guide", traits=[guide_trait], age=guide_age,
                             attrs={"relation": relation}))
    eager = world.add(Entity(id=_safe_name(eager_name), kind="character", type=eager_gender,
                             role="eager", traits=["bold"], age=eager_age,
                             attrs={"relation": relation}))
    world.add(Entity(id="setting", type="setting", label=setting.place, attrs={"setting_obj": setting}))
    world.facts.update(setting=setting, objective=objective, tool=tool, response=response,
                       guide=guide, eager=eager, relation=relation, delay=delay)

    setup(world, setting, guide, eager, objective)
    world.para()
    argue(world, eager, guide, objective, setting)

    if would_reconcile(relation, guide_age, eager_age, guide_trait):
        world.para()
        reconcile(world, eager, guide)
        world.para()
        demonstrate(world, guide, tool, objective, setting)
        world.para()
        venture(world, setting, objective)
        ending(world, setting, objective, tool)
        outcome = "reconciled"
    else:
        world.para()
        eager.memes["defiance"] += 1
        if is_success(response, objective, delay):
            world.say(
                f'{eager.id} listened after the warning, and {response.text.replace("{target}", objective.keyword)}.'
            )
            outcome = "safe"
        else:
            world.say(
                f'{eager.id} rushed ahead, and {response.fail.replace("{target}", objective.keyword)}.'
            )
            outcome = "stuck"

    world.facts["outcome"] = outcome
    return world


THEMES = {
    "bridge": Setting(
        "bridge",
        "the old rope bridge",
        "the narrow path toward the hill",
        "the river sparkled below, and a cave mouth waited past the trees",
        "far side of the hill",
        hazards={"bridge"},
        tags={"bridge", "adventure"},
    ),
    "cave": Setting(
        "cave",
        "the forest trail",
        "the rocky ridge",
        "a dark cave waited under the roots",
        "cave entrance",
        hazards={"drop"},
        tags={"cave", "adventure"},
    ),
    "island": Setting(
        "island",
        "the sandy path",
        "the shell path",
        "the bay glittered ahead, and a little lookout tower stood beyond the palms",
        "lookout tower",
        hazards={"water"},
        tags={"island", "adventure"},
    ),
}

OBJECTIVES = {
    "cross_bridge": Objective("cross_bridge", "cross the bridge", "run across the bridge", "bridge", "they crossed the bridge safely", tags={"bridge"}),
    "find_cave": Objective("find_cave", "find the cave", "dash into the cave", "cave", "they found the cave and explored it together", tags={"cave"}),
    "reach_tower": Objective("reach_tower", "reach the tower", "climb the hill quickly", "tower", "they reached the tower with brave hearts", tags={"tower"}),
}

TOOLS = {
    "pole": Tool("pole", "a walking pole", "a walking pole", {"bridge", "drop"}, tags={"pole"}),
    "rope": Tool("rope", "a short rope", "a short rope", {"bridge", "water"}, tags={"rope"}),
    "lamp": Tool("lamp", "a little lantern", "a little lantern", {"cave"}, tags={"lamp"}),
}

RESPONSES = {
    "helpful": Response("helpful", 3, 3, "kept the children steady and calm", "was too small to help", "kept them steady and calm", tags={"help"}),
    "rope_help": Response("rope_help", 2, 2, "tied the rope to the rail and made a secure handhold", "could not make the crossing safe", "tied the rope to the rail", tags={"rope"}),
    "lamp_help": Response("lamp_help", 2, 2, "lit the way with a lantern", "did not shine far enough", "lit the way with a lantern", tags={"lamp"}),
}


@dataclass
@dataclass
class StoryParams:
    theme: str
    objective: str
    tool: str
    response: str
    guide_name: str
    guide_gender: str
    eager_name: str
    eager_gender: str
    guide_trait: str
    relation: str = "siblings"
    delay: int = 0
    guide_age: int = 7
    eager_age: int = 5
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    for tid, setting in THEMES.items():
        for oid, obj in OBJECTIVES.items():
            for tool_id, tool in TOOLS.items():
                if obj.keyword in setting.tags and any(t in tool.helps_with for t in setting.hazards | {obj.keyword}):
                    combos.append((tid, oid, tool_id))
    return combos


def explain_rejection(setting: Setting, objective: Objective, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not fit this adventure well enough to demonstrate a safe choice for {objective.goal}. "
        f"Pick a tool that genuinely helps with the danger in {setting.place}.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with dialogue and reconciliation.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--objective", choices=OBJECTIVES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--guide-name")
    ap.add_argument("--eager-name")
    ap.add_argument("--guide-gender", choices=["girl", "boy"])
    ap.add_argument("--eager-gender", choices=["girl", "boy"])
    ap.add_argument("--guide-trait")
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
              if (args.theme is None or c[0] == args.theme)
              and (args.objective is None or c[1] == args.objective)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, objective, tool = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    guide_gender = args.guide_gender or rng.choice(["girl", "boy"])
    eager_gender = args.eager_gender or ("boy" if guide_gender == "girl" else "girl")
    guide_name = args.guide_name or rng.choice(["Mara", "Nia", "Iris", "Tess"])
    eager_name = args.eager_name or rng.choice(["Leo", "Kai", "Milo", "Jude"])
    guide_trait = args.guide_trait or rng.choice(["calm", "patient", "thoughtful", "wise"])
    return StoryParams(theme, objective, tool, response, guide_name, guide_gender,
                       eager_name, eager_gender, guide_trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story that includes the word "demonstrate" and a moment of dialogue between {f["guide"].id} and {f["eager"].id}.',
        f"Tell a small adventure where one child wants to rush ahead, but the other child demonstrates a safer way and they reconcile.",
        f"Write a story with dialogue, a demonstration, and reconciliation set on a little adventure trail.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    guide, eager, setting, objective, tool = f["guide"], f["eager"], f["setting"], f["objective"], f["tool"]
    return [
        QAItem(
            question="Who are the story about?",
            answer=f"The story is about {guide.id} and {eager.id}, two children on a small adventure."
        ),
        QAItem(
            question="What did the careful child do?",
            answer=f"{guide.id} used {tool.phrase} to demonstrate a safer way to keep going. "
                   f"That helped turn the argument into reconciliation."
        ),
        QAItem(
            question="How did they end the story?",
            answer=f"They ended the day together, having reconciled and reached the {setting.ending_image}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a demonstration?", "A demonstration is when someone shows how to do something step by step."),
        QAItem("What does reconciliation mean?", "Reconciliation means people stop arguing and make peace again."),
        QAItem("What is an adventure?", "An adventure is an exciting trip or task where something new is waiting ahead."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("bridge", "cross_bridge", "pole", "helpful", "Mara", "girl", "Leo", "boy", "calm"),
    StoryParams("cave", "find_cave", "lamp", "lamp_help", "Nia", "girl", "Kai", "boy", "patient"),
    StoryParams("island", "reach_tower", "rope", "helpful", "Tess", "girl", "Milo", "boy", "thoughtful"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], OBJECTIVES[params.objective], TOOLS[params.tool],
                 RESPONSES[params.response], params.guide_name, params.guide_gender,
                 params.eager_name, params.eager_gender, params.guide_trait,
                 params.relation, params.delay, params.guide_age, params.eager_age)
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


def asp_facts() -> str:
    import asp
    lines = []
    for k in THEMES:
        lines.append(asp.fact("theme", k))
    for k in OBJECTIVES:
        lines.append(asp.fact("objective", k))
    for k in TOOLS:
        lines.append(asp.fact("tool", k))
    for k in RESPONSES:
        lines.append(asp.fact("response", k))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(T, O, U) :- theme(T), objective(O), tool(U).
sensible(R) :- response(R).
outcome(reconciled) :- theme(T), objective(O), tool(U), valid(T,O,U).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid-combo gate.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(theme=None, objective=None, tool=None, response=None, guide_name=None, eager_name=None, guide_gender=None, eager_gender=None, guide_trait=None), random.Random(777)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"FAIL: generation smoke test crashed: {exc}")
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos.")
        for t in asp_valid_combos():
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
