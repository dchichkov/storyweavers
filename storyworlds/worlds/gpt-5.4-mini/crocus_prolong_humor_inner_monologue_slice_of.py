#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/crocus_prolong_humor_inner_monologue_slice_of.py
=================================================================================

A small standalone storyworld about a child, a spring crocus, and the wish to
prolong a tiny moment of bloom. The stories are slice-of-life, lightly funny, and
often narrated through the child's inner monologue as they fuss over a flower,
a clock, a snack, or a visitor who is almost here.

Core premise:
- A child notices a crocus in an ordinary home setting.
- The child wants the bright moment to last longer.
- Their first idea is a little too much or a little too fussy.
- A grown-up or sibling suggests a calmer, practical way to enjoy it.
- The ending proves the moment was not frozen, only appreciated.

Includes:
- physical meters and emotional memes on typed entities
- a Python reasonableness gate plus inline ASP twin
- prompts, story-grounded QA, and world-knowledge QA
- --verify smoke test that exercises story generation
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


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
    detail: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)

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
class Flower:
    id: str
    label: str
    phrase: str
    color: str
    fragile: bool = True
    bloom_power: int = 1
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
class Plan:
    id: str
    sense: int
    text: str
    fail: str
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
        return c


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_wilt(world: World) -> list[str]:
    out = []
    flower = world.get("flower")
    if flower.meters["dryness"] >= THRESHOLD and ("wilt", flower.id) not in world.fired:
        world.fired.add(("wilt", flower.id))
        flower.meters["droop"] += 1
        world.get("child").memes["worry"] += 1
        out.append("__wilt__")
    return out


def _r_calm(world: World) -> list[str]:
    out = []
    if world.get("child").memes["worry"] >= THRESHOLD and ("calm", "child") not in world.fired:
        world.fired.add(("calm", "child"))
        world.get("adult").memes["calm"] += 1
        out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("wilt", "physical", _r_wilt), Rule("calm", "social", _r_calm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def flower_at_risk(plan: Plan, flower: Flower, setting: Setting) -> bool:
    return flower.fragile and "flower" in setting.affords


def sensible_plans() -> list[Plan]:
    return [p for p in PLANS.values() if p.sense >= 2]


def best_plan() -> Plan:
    return max(PLANS.values(), key=lambda p: p.sense)


def is_helpful(plan: Plan, flower: Flower) -> bool:
    return plan.sense >= 2 and flower.fragile


def _do_worry(world: World, child: Entity, flower: Flower, narrate: bool = True) -> None:
    child.memes["worry"] += 1
    flower.meters["dryness"] += 1
    propagate(world, narrate=narrate)


def watch(world: World, child: Entity, flower: Flower) -> None:
    child.memes["joy"] += 1
    world.say(
        f"On a quiet morning, {child.id} spotted a crocus on the table by the window. "
        f"It looked like a tiny purple trumpet that had wandered into the kitchen."
    )
    world.say(
        f"{child.id} leaned in and thought, in the serious voice of {f'{child.id} inside {child.pronoun('possessive')} own head'}: "
        f'"Please last longer. The crocus is doing such an excellent job of being a crocus."'
    )


def explain(world: World, child: Entity, flower: Flower, adult: Entity) -> None:
    world.say(
        f"But the petals were starting to curl a little, and {child.id} noticed that "
        f"{adult.label_word} would be home soon."
    )
    world.say(
        f'"If the crocus fades before then," {child.id} thought, "all this brightness will be over before the good part is finished."'
    )


def try_prolong(world: World, child: Entity, plan: Plan, flower: Flower) -> None:
    child.memes["determination"] += 1
    world.say(
        f'{child.id} decided to {plan.text}. In {child.pronoun("possessive")} mind, this sounded perfectly scientific and only slightly heroic.'
    )
    world.say(
        f'"Maybe flowers are like cookies," {child.id} thought. "If I am extra careful, I can make the good moment stretch."'
    )


def warn(world: World, adult: Entity, child: Entity, flower: Flower) -> bool:
    sim = world.copy()
    _do_worry(sim, sim.get("child"), sim.get("flower"))
    if sim.get("flower").meters["droop"] < THRESHOLD:
        return False
    world.facts["predicted_droop"] = sim.get("flower").meters["droop"]
    world.say(
        f'{adult.label_word.capitalize()} glanced over and said, "You are very kind to the crocus, but too much fuss can make a flower tired."'
    )
    return True


def overdo(world: World, child: Entity, plan: Plan, flower: Flower) -> None:
    child.memes["embarrassment"] += 1
    _do_worry(world, child, flower)
    world.say(
        f"{child.id} gave the crocus one more little fix, then another. The poor flower sat there looking like it had heard the joke and was not sure whether to laugh."
    )


def redirect(world: World, adult: Entity, child: Entity, flower: Flower, plan: Plan) -> None:
    adult.memes["calm"] += 1
    world.say(
        f"{adult.label_word.capitalize()} came over with a smile and a paper cup of water. "
        f'"How about we give it one careful sip, move it out of the sun, and take a picture?" {adult.pronoun()} said.'
    )
    world.say(
        f'{child.id} paused. "A photo cannot wilt," {child.id} thought, which felt like a very clever thought for a Tuesday.'
    )


def settle(world: World, child: Entity, adult: Entity, flower: Flower) -> None:
    child.memes["joy"] += 1
    child.memes["worry"] = 0
    flower.meters["dryness"] = max(0.0, flower.meters["dryness"] - 1)
    flower.meters["freshness"] += 1
    world.say(
        f"They moved the crocus to a cooler spot by the sink, where the light stayed gentle. "
        f"{child.id} took a quick photo, and the flower kept glowing in the picture even as the real petals relaxed."
    )
    world.say(
        f'By afternoon, {child.id} was telling the crocus, "You do not have to perform forever. One bright minute can be enough."'
    )


def tell(setting: Setting, flower: Flower, plan: Plan,
         child_name: str = "Mina", child_gender: str = "girl",
         adult_name: str = "Mom", adult_gender: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult"))
    fl = world.add(Entity(id="flower", kind="thing", type="flower", label=flower.label))
    child.memes["wonder"] = 1
    world.facts["setting"] = setting
    world.facts["flower_cfg"] = flower
    world.facts["plan"] = plan
    world.facts["child"] = child
    world.facts["adult"] = adult
    world.facts["flower"] = fl

    watch(world, child, flower)
    explain(world, child, flower, adult)
    world.para()
    try_prolong(world, child, plan, flower)
    warn(world, adult, child, flower)
    overdo(world, child, plan, flower)
    world.para()
    redirect(world, adult, child, flower, plan)
    settle(world, child, adult, flower)

    world.facts.update(
        outcome="softened",
        cared_for=True,
        worry=child.memes["worry"],
        freshness=fl.meters["freshness"],
        dryness=fl.meters["dryness"],
    )
    return world


SETTINGS = {
    "kitchen": Setting(
        "kitchen",
        "the kitchen",
        "The table was near the window, and the room smelled faintly of toast.",
        indoors=True,
        affords={"flower"},
    ),
    "hallway": Setting(
        "hallway",
        "the hallway",
        "The little shelf by the door caught the morning light.",
        indoors=True,
        affords={"flower"},
    ),
    "balcony": Setting(
        "balcony",
        "the balcony",
        "The balcony had a bright patch of sun and a railing with a missing paint chip.",
        indoors=False,
        affords={"flower"},
    ),
}

FLOWERS = {
    "purple_crocus": Flower(
        "purple_crocus", "crocus", "a little crocus", "purple", fragile=True, bloom_power=1, tags={"crocus", "flower"},
    ),
    "yellow_crocus": Flower(
        "yellow_crocus", "crocus", "a yellow crocus", "yellow", fragile=True, bloom_power=1, tags={"crocus", "flower"},
    ),
}

PLANS = {
    "gaze": Plan("gaze", 2, "move the cup a little farther from the window and keep watch", "watched it too hard and made it feel like homework", tags={"care"}),
    "water": Plan("water", 3, "give the crocus one careful sip of water and turn the cup a little", "poured so much water that the saucer became a pond", tags={"water", "care"}),
    "shade": Plan("shade", 3, "draw the curtain halfway and let the light soften", "closed the curtain so much that the poor flower felt forgotten", tags={"shade", "care"}),
    "fuss": Plan("fuss", 1, "keep checking the crocus every minute and whisper encouragement at it", "checked so often that even the clock started feeling judged", tags={"humor"}),
}

CHILD_NAMES = ["Mina", "Leo", "Nora", "Ava", "Ben", "Milo", "Ivy", "June"]
ADULT_NAMES = ["Mom", "Dad", "Aunt Em", "Grandma", "Papa"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for f in FLOWERS:
            for p in PLANS:
                if flower_at_risk(PLANS[p], FLOWERS[f], SETTINGS[s]):
                    combos.append((s, f, p))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    flower: str
    plan: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_gender: str
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


KNOWLEDGE = {
    "crocus": [("What is a crocus?", "A crocus is a small spring flower that can pop up early in the year, often with bright purple, yellow, or white petals.")],
    "flower": [("What does a flower need to stay fresh?", "A flower usually needs a little water, gentle light, and not too much heat or fuss.")],
    "water": [("Why do plants need water?", "Plants use water to stay alive and healthy. Water helps them keep their stems and petals from drying out.")],
    "sun": [("Why can strong sun make a flower wilt faster?", "Strong sun can warm a flower and dry it out, so the petals droop sooner.")],
    "photo": [("Why do people take photos of pretty things?", "People take photos so they can remember a nice moment later, even after the moment has passed.")],
    "care": [("What does it mean to care for something?", "Caring means paying attention, being gentle, and giving something what it needs without overdoing it.")],
}
KNOWLEDGE_ORDER = ["crocus", "flower", "water", "sun", "photo", "care"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    plan = f["plan"]
    flower = f["flower_cfg"]
    return [
        f'Write a slice-of-life story for a young child that includes the word "{flower.label}" and the word "prolong".',
        f"Tell a humorous story where {child.id} tries to prolong a crocus bloom and thinks about it in a funny inner monologue.",
        f"Write a gentle everyday story about caring for a crocus without overdoing it, ending with a small solution that feels practical and kind.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, adult, flower, plan = f["child"], f["adult"], f["flower_cfg"], f["plan"]
    qa = [
        ("Who is the story about?", f"It is about {child.id} and {flower.label}. {adult.id} helps when the child gets too fussy about keeping the bloom going."),
        ("What did the child want to do?", f"{child.id} wanted to prolong the crocus bloom. In the child's mind, that meant making the bright moment last just a little longer."),
        ("Why did the child fuss over the flower?", f"{child.id} was worried the crocus would fade before {adult.id} got home. The worry made the child act a bit too carefully, which was funny and a little stressful."),
        ("How did the grown-up help?", f"{adult.id} suggested a calmer way: one careful sip of water, a cooler spot, and a photo. That changed the story from frantic fussing into gentle care."),
        ("How did the story end?", f"It ended with the crocus rested in a better spot and a photo saved the bright moment. The flower did not stay frozen forever, but the child learned how to enjoy it without making it tired."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["flower_cfg"].tags) | set(world.facts["plan"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "purple_crocus", "water", "Mina", "girl", "Mom", "mother"),
    StoryParams("hallway", "yellow_crocus", "shade", "Leo", "boy", "Dad", "father"),
    StoryParams("balcony", "purple_crocus", "gaze", "Nora", "girl", "Grandma", "woman"),
]


def explain_rejection(setting: Setting, flower: Flower, plan: Plan) -> str:
    if not flower_at_risk(plan, flower, setting):
        return "(No story: this combination does not create any real crocus worry, so there is nothing to prolong or mend.)"
    return "(No story: this plan is too nonsensical for the little crocus storyworld.)"


def outcome_of(params: StoryParams) -> str:
    return "softened"


def explain_plan(rid: str) -> str:
    return f"(Refusing plan '{rid}': it is not a sensible care move for this storyworld.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for fid, f in FLOWERS.items():
        lines.append(asp.fact("flower", fid))
        if f.fragile:
            lines.append(asp.fact("fragile", fid))
        lines.append(asp.fact("tag", fid, "crocus"))
    for pid, p in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("sense", pid, p.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, F, P) :- setting(S), flower(F), plan(P), affords(S, flower), fragile(F), sense(P, N), sense_min(M), N >= M.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, flower=None, plan=None, child_name=None, child_gender=None, adult_name=None, adult_gender=None, seed=None), random.Random(7)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life crocus storyworld with humor and inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--flower", choices=FLOWERS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--child-name", dest="child_name")
    ap.add_argument("--child-gender", dest="child_gender", choices=["girl", "boy"])
    ap.add_argument("--adult-name", dest="adult_name")
    ap.add_argument("--adult-gender", dest="adult_gender", choices=["mother", "father", "woman", "man"])
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
              and (args.flower is None or c[1] == args.flower)
              and (args.plan is None or c[2] == args.plan)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, flower, plan = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(["Mina", "Leo", "Nora", "Ava", "Ben", "Milo"])
    adult_gender = args.adult_gender or rng.choice(["mother", "father"])
    adult_name = args.adult_name or rng.choice(["Mom", "Dad", "Grandma", "Aunt Em", "Papa"])
    return StoryParams(setting, flower, plan, child_name, child_gender, adult_name, adult_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], FLOWERS[params.flower], PLANS[params.plan],
                 params.child_name, params.child_gender, params.adult_name, params.adult_gender)
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, f, p in asp_valid_combos():
            print(f"  {s:10} {f:16} {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: crocus / {p.plan}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
