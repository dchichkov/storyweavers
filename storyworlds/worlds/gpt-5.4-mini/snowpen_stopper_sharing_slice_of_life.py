#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/snowpen_stopper_sharing_slice_of_life.py
=========================================================================

A small, standalone story world for a slice-of-life winter sharing tale.

Core premise:
- Two children are making a tiny winter scene outside.
- One child has a special tool called a snowpen for drawing in snow.
- Another child has a stopper that keeps their little jar of colored water from spilling.
- They want to share the tools, take turns, and finish a cheerful snow picture together.
- If the stopper is loose, the colored water can leak and make a mess; a calm parent
  shows how to seal it and the children continue sharing.

The world uses typed entities with physical meters and emotional memes, a tiny
forward-chaining rule engine, a reasonableness gate, and an inline ASP twin.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
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
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    helps: set[str] = field(default_factory=set)
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


@dataclass
@dataclass
class StoryParams:
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str
    snowpen: str
    stopper: str
    response: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

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


def _r_leak(world: World) -> list[str]:
    out: list[str] = []
    jar = world.entities.get("jar")
    if not jar or jar.meters["leaking"] < THRESHOLD:
        return out
    sig = ("leak", "jar")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if "table" in world.entities:
        world.get("table").meters["sticky"] += 1
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.memes["worry"] += 1
    out.append("__leak__")
    return out


CAUSAL_RULES = [Rule("leak", "physical", _r_leak)]


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


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combo(snowpen: Item, stopper: Item, response: Response) -> bool:
    return bool(snowpen and stopper and response.sense >= SENSE_MIN)


def leak_risk(stopper: Item) -> bool:
    return "seal" in stopper.helps


def leak_severity(stopper: Item) -> int:
    return 2 if "loose" in stopper.tags else 1


def can_hold(response: Response, stopper: Item) -> bool:
    return response.power >= leak_severity(stopper)


def predict_leak(world: World) -> dict:
    sim = world.copy()
    sim.get("jar").meters["leaking"] += 1
    propagate(sim, narrate=False)
    return {
        "leaking": sim.get("jar").meters["leaking"] >= THRESHOLD,
        "sticky": sim.get("table").meters["sticky"] if "table" in sim.entities else 0,
    }


def _do_leak(world: World) -> None:
    world.get("jar").meters["leaking"] += 1
    propagate(world, narrate=True)


def opening(world: World, a: Entity, b: Entity) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a bright cold morning, {a.id} and {b.id} met at the little patio table. "
        f"They had a jar of colored snow water, a scrap of paper, and time to make something pretty."
    )


def introduce_tools(world: World, a: Entity, b: Entity, snowpen: Item, stopper: Item) -> None:
    world.say(
        f"{a.id} held up the {snowpen.label}, a tiny {snowpen.kind} for drawing clean lines in snow. "
        f"{b.id} showed the {stopper.label}, which helped keep the jar closed tight."
    )
    world.say(
        f'"Can we share?" {b.id} asked. {a.id} nodded right away, because sharing made the project feel more fun.'
    )


def start_scene(world: World, a: Entity, b: Entity) -> None:
    world.say(
        f"They crouched beside the snow and began to plan a picture together: a little house, a star, and two mitten prints."
    )
    world.say(
        f"{a.id} drew the roof with the snowpen while {b.id} held the paper steady and counted the turns."
    )


def warn(world: World, parent: Entity, b: Entity, stopper: Item) -> None:
    pred = predict_leak(world)
    if not pred["leaking"]:
        return
    world.facts["predicted_sticky"] = pred["sticky"]
    world.say(
        f'{b.id} frowned at the jar. "{parent.label_word.capitalize()} said the stopper has to stay snug," '
        f'{b.pronoun()} said. "If it loosens, the table will get sticky."'
    )


def loosen(world: World, b: Entity, stopper: Item) -> None:
    b.memes["care"] += 1
    world.say(
        f"{b.id} checked the top and saw the stopper wobble a little. "
        f'That made {b.pronoun("object")} careful, so {b.pronoun()} set the jar down gently.'
    )


def share_turns(world: World, a: Entity, b: Entity, snowpen: Item) -> None:
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    world.say(
        f"They took turns with the snowpen: {a.id} drew a window, then {b.id} added a chimney and two round snowflakes."
    )


def leak(world: World, stopper: Item) -> None:
    world.say(
        f"Then the stopper slipped just enough for a drip to escape. The colored water slid down the jar and spotted the table."
    )
    _do_leak(world)


def calm_fix(world: World, parent: Entity, stopper: Item, response: Response) -> None:
    body = response.text.replace("{stopper}", stopper.label)
    world.say(f"{parent.label_word.capitalize()} came over, smiled, and {body}.")
    world.say(
        "The jar settled down again. No more dripping, just a neat lid and a clean tabletop."
    )


def finish_art(world: World, a: Entity, b: Entity, snowpen: Item) -> None:
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.memes["joy"] += 1
            ent.memes["safety"] += 1
    world.say(
        f"After that, they kept sharing the snowpen and finished the picture together. "
        f"The last thing they made was a bright star above the little house, and both children smiled at the same drawing."
    )


def tell(params: StoryParams) -> World:
    world = World()
    a = world.add(Entity(id=params.child1, kind="character", type=params.child1_gender, role="child"))
    b = world.add(Entity(id=params.child2, kind="character", type=params.child2_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, role="parent", label="the parent"))
    snowpen = world.add(Entity(id="snowpen", type="tool", label="snowpen"))
    stopper = world.add(Entity(id="stopper", type="tool", label="stopper"))
    jar = world.add(Entity(id="jar", type="thing", label="little jar"))
    table = world.add(Entity(id="table", type="thing", label="table"))

    a.memes["trust"] = 4
    b.memes["trust"] = 4
    stopper.meters["snug"] = 1

    opening(world, a, b)
    introduce_tools(world, a, b, Item("snowpen", "snowpen", "snowpen", "tool"), Item("stopper", "stopper", "stopper", "tool"))
    world.para()
    start_scene(world, a, b)
    warn(world, parent, b, Item("stopper", "stopper", "stopper", "tool", helps={"seal"}, tags={"loose"}))
    loosen(world, b, Item("stopper", "stopper", "stopper", "tool"))
    share_turns(world, a, b, Item("snowpen", "snowpen", "snowpen", "tool"))
    world.para()
    leak(world, Item("stopper", "stopper", "stopper", "tool", helps={"seal"}, tags={"loose"}))
    calm_fix(world, parent, Item("stopper", "stopper", "stopper", "tool", helps={"seal"}, tags={"loose"}), RESPONSES[params.response])
    finish_art(world, a, b, Item("snowpen", "snowpen", "snowpen", "tool"))
    world.facts.update(
        child1=a, child2=b, parent=parent, snowpen=snowpen, stopper=stopper,
        response=RESPONSES[params.response], outcome="fixed"
    )
    return world


THEMES = ["slice_of_life"]
CHILDREN = {
    "girls": [("Mia", "girl"), ("Zoe", "girl"), ("Lina", "girl"), ("Ava", "girl")],
    "boys": [("Noah", "boy"), ("Eli", "boy"), ("Finn", "boy"), ("Leo", "boy")],
    "mixed": [("Mia", "girl"), ("Noah", "boy"), ("Ava", "girl"), ("Eli", "boy")],
}

ITEMS = {
    "snowpen": Item("snowpen", "snowpen", "a bright snowpen", "tool", helps={"draw"}, tags={"snow"}),
    "stopper": Item("stopper", "stopper", "a rubber stopper", "tool", helps={"seal"}, tags={"seal", "loose"}),
}

RESPONSES = {
    "tighten": Response("tighten", 3, 3, "tightened the stopper with a careful twist", "could not tighten it enough", "tightened the stopper with a careful twist", tags={"seal"}),
    "press": Response("press", 2, 2, "pressed the stopper down until it sat snugly", "pressed it, but it still wobbled", "pressed the stopper down until it sat snugly", tags={"seal"}),
    "replace": Response("replace", 3, 4, "swapped in a fresh stopper and closed the jar", "swapped it, but the jar still dripped", "swapped in a fresh stopper and closed the jar", tags={"seal"}),
}

GENTLE_NAMES = ["Mia", "Zoe", "Lina", "Ava", "Noah", "Eli", "Finn", "Leo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life sharing story world with a snowpen and a stopper.")
    ap.add_argument("--child1")
    ap.add_argument("--child1-gender", choices=["girl", "boy"])
    ap.add_argument("--child2")
    ap.add_argument("--child2-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--snowpen", choices=["snowpen"])
    ap.add_argument("--stopper", choices=["stopper"])
    ap.add_argument("--response", choices=RESPONSES)
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("response too weak")
    c1 = args.child1 or rng.choice(GENTLE_NAMES)
    c2 = args.child2 or rng.choice([n for n in GENTLE_NAMES if n != c1])
    g1 = args.child1_gender or rng.choice(["girl", "boy"])
    g2 = args.child2_gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    return StoryParams(c1, g1, c2, g2, parent, args.snowpen or "snowpen", args.stopper or "stopper", response)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life winter story that includes the words "{f["snowpen"].label}" and "{f["stopper"].label}" and is about sharing.',
        f"Tell a gentle story about {f['child1'].id} and {f['child2'].id} taking turns with a {f['snowpen'].label} and keeping a {f['stopper'].label} snug.",
        "Write a calm, child-friendly story where friends share tools, notice a small problem, and fix it together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, parent = f["child1"], f["child2"], f["parent"]
    return [
        ("Who is the story about?",
         f"It is about {a.id} and {b.id}, two children who were spending a winter morning together. Their {parent.label_word} helped them keep things calm and shared."),
        ("What did they share?",
         f"They shared the snowpen and the stopper. They took turns so both of them could help make the picture."),
        ("What problem happened?",
         f"The stopper loosened a little, so a few drops of colored water escaped from the jar. That made the table get a little sticky."),
        ("How did the problem get fixed?",
         f"{parent.label_word.capitalize()} came over and {f['response'].qa_text}. After that, the jar was safe again and they could keep drawing."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a snowpen?",
         "A snowpen is a small tool you can use to draw or write in snow. It makes the marks easy to see in a white winter scene."),
        ("What is a stopper?",
         "A stopper is a piece that helps close a jar or bottle tightly. It keeps the liquid inside from spilling out."),
        ("Why is sharing nice?",
         "Sharing lets more than one person use the same thing. It helps people work together and have fun together."),
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("Mia", "girl", "Noah", "boy", "mother", "snowpen", "stopper", "tighten"),
    StoryParams("Ava", "girl", "Eli", "boy", "father", "snowpen", "stopper", "press"),
]


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


ASP_RULES = r"""
leak_risk(stopper) :- stopper(stopper).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("sense_min", SENSE_MIN)]
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("snowpen", "snowpen"))
    lines.append(asp.fact("stopper", "stopper"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(", ".join(asp_sensible()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
