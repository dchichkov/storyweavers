#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bagel_teamwork_bad_ending_fable.py
===================================================================

A standalone story world for a tiny fable-like domain: a few small animals try
to work together around a bagel, but a bad choice turns their teamwork into a
loss.  The world is built to produce short, complete, child-facing stories with
clear cause and effect, plus grounded QA and an inline ASP twin.

Seed idea:
- Word: bagel
- Style: fable
- Features: teamwork, bad ending

The domain is intentionally small:
- A leader wants to carry a bagel to a shared place.
- Helpers can use sensible teamwork gear: a tray, a napkin, a basket.
- A risky shortcut can cause the bagel to fall, get muddy or soggy, and be lost.
- The ending proves what changed: they lose the bagel and learn to share jobs
  more carefully next time.

This file follows the Storyweavers contract and is standalone stdlib Python.
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
SENSE_MIN = 2


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
        mapping = {
            "subject": "they",
            "object": "them",
            "possessive": "their",
        }
        if self.type in {"girl", "mother", "woman"}:
            mapping = {"subject": "she", "object": "her", "possessive": "her"}
        elif self.type in {"boy", "father", "man"}:
            mapping = {"subject": "he", "object": "him", "possessive": "his"}
        return mapping[case]

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
class Place:
    id: str
    label: str
    scene: str
    shared_goal: str
    risky_surface: str
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
    helps: str
    safe: bool = True
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
class Risk:
    id: str
    label: str
    phrase: str
    can_spoil: bool = True
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
class OutcomePlan:
    id: str
    sense: int
    power: int
    success: str
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    if world.get("bagel").meters["soggy"] >= THRESHOLD:
        sig = ("tension", "bagel")
        if sig not in world.fired:
            world.fired.add(sig)
            for eid in ("Milo", "Pia"):
                world.get(eid).memes["sad"] += 1
            out.append("__tension__")
    return out


def _r_loss(world: World) -> list[str]:
    out: list[str] = []
    if world.get("bagel").meters["lost"] >= THRESHOLD:
        sig = ("loss", "bagel")
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("field").meters["empty"] += 1
            out.append("__loss__")
    return out


CAUSAL_RULES = [
    Rule("tension", "social", _r_tension),
    Rule("loss", "physical", _r_loss),
]


def teamwork_needed(place: Place, risk: Risk) -> bool:
    return risk.can_spoil and "share" in place.tags


def sensible_plans() -> list[OutcomePlan]:
    return [p for p in PLANS.values() if p.sense >= SENSE_MIN]


def bad_or_good(plan: OutcomePlan, delay: int) -> bool:
    return plan.power >= (1 + delay)


def aversion(place: Place, helper_age: int, leader_age: int) -> bool:
    return helper_age > leader_age and "wise" in place.tags


def _do_risky(world: World, risk: Risk, narrate: bool = True) -> None:
    bagel = world.get("bagel")
    bagel.meters["soggy"] += 1
    bagel.meters["crumbly"] += 1
    propagate(world, narrate=narrate)


def predict_loss(world: World, risk: Risk) -> dict:
    sim = world.copy()
    _do_risky(sim, risk, narrate=False)
    return {
        "soggy": sim.get("bagel").meters["soggy"] >= THRESHOLD,
        "lost": sim.get("bagel").meters["lost"] >= THRESHOLD,
    }


def begin(world: World, leader: Entity, helper: Entity, place: Place, risk: Risk) -> None:
    leader.memes["hope"] += 1
    helper.memes["hope"] += 1
    world.say(
        f"Once in a little meadow by the mill, {leader.id} and {helper.id} "
        f"planned a small task at {place.label}. {place.scene}"
    )
    world.say(
        f"They both wanted to carry one warm bagel to {place.shared_goal}, "
        f"so the day began with friendly work."
    )


def need_teamwork(world: World, leader: Entity, helper: Entity, tool1: Tool, tool2: Tool) -> None:
    world.say(
        f"But the bagel was round and slippery, and {leader.id} knew two paws "
        f"would do better than one. {helper.id} brought {tool1.phrase}, and "
        f"{leader.id} reached for {tool2.phrase}."
    )


def tempt_shortcut(world: World, leader: Entity, risk: Risk) -> None:
    leader.memes["bold"] += 1
    world.say(
        f'"We can go faster this way," {leader.id} said, and pointed toward '
        f"{risk.phrase}."
    )
    world.say("For a moment, the shortcut looked clever.")


def warn_helper(world: World, helper: Entity, leader: Entity, risk: Risk, place: Place) -> None:
    pred = predict_loss(world, risk)
    helper.memes["caution"] += 1
    world.facts["predicted_soggy"] = pred["soggy"]
    world.say(
        f'{helper.id} blinked and said, "{leader.id}, that path will make the '
        f"bagel {risk.label}. It could fall before we reach {place.shared_goal}."
    )


def choose_shortcut(world: World, leader: Entity, helper: Entity, risk: Risk) -> None:
    leader.memes["defiance"] += 1
    world.say(
        f'"No, no," {leader.id} said, and hurried on before {helper.id} could '
        f"slow them down."
    )


def slip(world: World, risk: Risk) -> None:
    _do_risky(world, risk)
    bagel = world.get("bagel")
    bagel.meters["lost"] += 1
    world.say(
        f"The ground was slick, the tray tipped, and the bagel fell into the "
        f"mud. It came up soggy, split, and sad."
    )


def ending_bad(world: World, leader: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"They reached {place.shared_goal} with empty paws and quiet hearts. "
        f"The bagel was gone, and their shared breakfast never happened."
    )
    world.say(
        f"{helper.id} and {leader.id} sat still under the trees, learning that "
        f"teamwork only helps when everyone listens to the careful voice."
    )


def tell(place: Place, risk: Risk, tool1: Tool, tool2: Tool, plan: OutcomePlan,
         leader_name: str = "Milo", leader_gender: str = "boy",
         helper_name: str = "Pia", helper_gender: str = "girl",
         leader_age: int = 5, helper_age: int = 6, seed_tag: str = "") -> World:
    world = World()
    leader = world.add(Entity(id=leader_name, kind="character", type=leader_gender,
                              role="leader", traits=["eager"], attrs={"age": leader_age}))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender,
                              role="helper", traits=["careful"], attrs={"age": helper_age}))
    world.add(Entity(id="bagel", type="thing", label="bagel"))
    world.add(Entity(id="field", type="place", label="the field"))

    begin(world, leader, helper, place, risk)
    world.para()
    need_teamwork(world, leader, helper, tool1, tool2)
    tempt_shortcut(world, leader, risk)
    warn_helper(world, helper, leader, risk, place)
    choose_shortcut(world, leader, helper, risk)
    world.para()
    slip(world, risk)
    ending_bad(world, leader, helper, place)

    world.facts.update(
        leader=leader, helper=helper, place=place, risk=risk, tool1=tool1, tool2=tool2,
        plan=plan, outcome="bad", seed_tag=seed_tag, lost=world.get("bagel").meters["lost"] >= THRESHOLD
    )
    return world


PLACES = {
    "bridge": Place("bridge", "the old bridge", "The bridge crossed a little creek and creaked under each careful step.", "the picnic table", "the creek", tags={"share", "wise"}),
    "hill": Place("hill", "the sunny hill", "The hill looked easy from far away, but the wind was stronger near the top.", "the garden bench", "the grass path", tags={"share"}),
    "bakery": Place("bakery", "the bakery porch", "The bakery smelled sweet, and the porch stayed busy with crumbs and chatter.", "the warm window seat", "the wet stones", tags={"share"}),
}

RISKS = {
    "mud": Risk("mud", "muddy", "a muddy shortcut through the ditch", tags={"mud"}),
    "stream": Risk("stream", "soggy", "the stream bank after rain", tags={"water"}),
    "stones": Risk("stones", "slippery", "the slippery stones by the gate", tags={"slip"}),
}

TOOLS = {
    "tray": Tool("tray", "a tray", "a flat tray", "keeps the bagel steady"),
    "napkin": Tool("napkin", "a napkin", "a clean napkin", "wraps the bagel gently"),
    "basket": Tool("basket", "a basket", "a little basket", "holds things together"),
}

PLANS = {
    "carry": OutcomePlan("carry", 3, 3, "carried the bagel carefully together", "could not keep the bagel steady", "carried the bagel together", tags={"team"}),
    "rush": OutcomePlan("rush", 1, 1, "ran with the bagel and made trouble", "ran too fast and lost the bagel", "rushed with the bagel", tags={"team"}),
}

LEADER_NAMES = ["Milo", "Toby", "Robin", "Otis", "Pip"]
HELPER_NAMES = ["Pia", "Luna", "Tess", "Nia", "June"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for rid, risk in RISKS.items():
            if teamwork_needed(place, risk):
                combos.append((pid, rid))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    risk: str
    tool1: str
    tool2: str
    plan: str
    leader: str
    leader_gender: str
    helper: str
    helper_gender: str
    leader_age: int = 5
    helper_age: int = 6
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


KNOWLEDGE = {
    "bagel": [("What is a bagel?", "A bagel is a round bread roll with a hole in the middle. People often eat it for breakfast.")],
    "team": [("What does teamwork mean?", "Teamwork means people work together and share the jobs. Good teamwork also means listening to each other.")],
    "mud": [("Why is mud messy?", "Mud sticks to things and makes them dirty. It can also make paths slippery.")],
    "water": [("Why can water make bread soggy?", "Water softens bread and makes it lose its shape and chewiness, so it can turn soggy.")],
    "slip": [("Why do people slip on wet stones?", "Wet stones can be slippery because water makes them less grippy under your feet.")],
    "listen": [("Why is it important to listen to a careful friend?", "A careful friend may notice danger sooner. Listening can help everyone stay safe.")],
    "share": [("What is sharing work?", "Sharing work means each person does part of the job. That can make the job easier and kinder.")],
}
KNOWLEDGE_ORDER = ["bagel", "team", "mud", "water", "slip", "listen", "share"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for a young child that includes the word "{f["risk"].label}" and the word "bagel".',
        f"Tell a story about {f['leader'].id} and {f['helper'].id} trying to work together, but a shortcut ruins the bagel.",
        "Write a simple fable where teamwork goes wrong because one character will not listen to the careful helper.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader, helper, place, risk = f["leader"], f["helper"], f["place"], f["risk"]
    qa = [
        ("Who was the story about?",
         f"It was about {leader.id} and {helper.id}, two small friends who wanted to work together. They were carrying a bagel for a shared meal."),
        ("What did they want to do?",
         f"They wanted to carry the bagel to {place.shared_goal}. The job began as teamwork, with both of them helping."),
        ("Why did the helper warn about the shortcut?",
         f"{helper.id} could see that {risk.phrase} would make the bagel {risk.label}. That kind of path was too risky for something round and slippery."),
        ("What happened at the end?",
         f"The bagel fell, got soggy, and was lost. The ending is sad because the shortcut ruined the job and the meal never happened."),
    ]
    if f.get("lost"):
        qa.append((
            "Why was this a bad ending?",
            f"It was a bad ending because the bagel was gone by the time they arrived. They had worked together at first, but not in a careful way, so their plan failed."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"bagel", "team", "share", "listen"}
    if world.facts["risk"].id == "mud":
        tags.add("mud")
    elif world.facts["risk"].id == "stream":
        tags.add("water")
    else:
        tags.add("slip")
    out = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
    StoryParams("bridge", "mud", "tray", "napkin", "carry", "Milo", "boy", "Pia", "girl", 5, 6),
    StoryParams("hill", "stones", "basket", "tray", "rush", "Toby", "boy", "Luna", "girl", 6, 5),
    StoryParams("bakery", "stream", "napkin", "basket", "carry", "Robin", "boy", "June", "girl", 5, 6),
]


def explain_rejection(place: Place, risk: Risk) -> str:
    return f"(No story: the chosen place and risk do not make a believable teamwork problem for a bagel.)"


def outcome_of(params: StoryParams) -> str:
    return "bad"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: teamwork around a bagel, with a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--tool1", choices=TOOLS)
    ap.add_argument("--tool2", choices=TOOLS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--leader")
    ap.add_argument("--leader-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
              and (args.risk is None or c[1] == args.risk)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, risk = rng.choice(sorted(combos))
    tool1 = args.tool1 or rng.choice(sorted(TOOLS))
    tool2 = args.tool2 or rng.choice(sorted(t for t in TOOLS if t != tool1))
    plan = args.plan or rng.choice(sorted(PLANS))
    leader_gender = args.leader_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if leader_gender == "girl" else "girl")
    leader = args.leader or rng.choice(LEADER_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != leader])
    return StoryParams(place, risk, tool1, tool2, plan, leader, leader_gender, helper, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], RISKS[params.risk], TOOLS[params.tool1], TOOLS[params.tool2], PLANS[params.plan], params.leader, params.leader_gender, params.helper, params.helper_gender, params.leader_age, params.helper_age, seed_tag=str(params.seed or ""))
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


ASP_RULES = r"""
teamwork_problem(P,R) :- place(P), risk(R).
bad_ending(P,R) :- teamwork_problem(P,R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for r in RISKS:
        lines.append(asp.fact("risk", r))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show teamwork_problem/2."))
    return sorted(set(asp.atoms(model, "teamwork_problem")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, risk=None, tool1=None, tool2=None, plan=None, leader=None, leader_gender=None, helper=None, helper_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show teamwork_problem/2.\n#show bad_ending/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for p, r in asp_valid_combos():
            print(f"  {p:8} {r}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
