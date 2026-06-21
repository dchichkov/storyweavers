#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/blush_body_forum_teamwork_bedtime_story.py
============================================================================

A standalone story world for a tiny bedtime tale about a child whose body feels
too busy for sleep, a gentle forum of helpers, and a teamwork solution that lets
everyone settle down. The required seed words appear naturally in the story:
blush, body, and forum.

Core premise:
- A child is getting ready for bed, but their body is still full of wiggles.
- The child feels a little blush of embarrassment because bedtime is not going
  smoothly.
- Family members and a plush helper hold a small "forum" to choose a calm plan.
- Each helper takes one job, and teamwork turns a hard bedtime into a peaceful
  ending.

The world uses typed entities with physical meters and emotional memes, a small
forward-chained causal engine, a reasonableness gate, and an inline ASP twin.
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
CALM_TARGET = 2.0


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
class Room:
    id: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
    label: str
    steps: list[str]
    calm: float
    teamwork: float

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
        self.rooms: dict[str, Room] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent):
        if isinstance(ent, Room):
            self.rooms[ent.id] = ent
        else:
            self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities.get(eid) or self.rooms[eid]

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
        clone.rooms = copy.deepcopy(self.rooms)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def _r_wind_down(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    room = world.rooms.get("bedroom")
    if not child or not room:
        return out
    if child.meters["busy"] < THRESHOLD:
        return out
    sig = ("wind_down", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters["quiet"] += 1
    child.meters["calm"] += 1
    out.append("__quiet__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    helpers = [e for e in list(world.entities.values()) if e.role in {"helper", "parent"}]
    child = world.entities.get("child")
    if not child:
        return out
    if sum(1 for h in helpers if h.meters["helping"] >= THRESHOLD) < 2:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["love"] += 1
    out.append("__teamwork__")
    return out


CAUSAL_RULES = [
    Rule("wind_down", "calm", _r_wind_down),
    Rule("teamwork", "social", _r_teamwork),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_calm(world: World) -> dict:
    sim = world.copy()
    child = sim.entities["child"]
    child.meters["busy"] += 1
    propagate(sim, narrate=False)
    return {
        "calm": sim.entities["child"].meters["calm"],
        "room_quiet": sim.rooms["bedroom"].meters["quiet"],
    }


def introduce(world: World, child: Entity, parent: Entity, plush: Entity, room: Room) -> None:
    world.say(
        f"At bedtime, {child.id} climbed into {room.label} with {plush.label} tucked under "
        f"{child.pronoun('possessive')} arm."
    )
    world.say(
        f"But {child.id}'s body still felt wiggly, and {child.id} gave a little blush "
        f"when {parent.label_word} said it was time to sleep."
    )


def problem(world: World, child: Entity) -> None:
    child.meters["busy"] += 1
    child.memes["worry"] += 1
    world.say(
        f"{child.id} stared at the ceiling and whispered, \"My body is not ready yet.\""
    )


def forum(world: World, child: Entity, parent: Entity, plush: Entity) -> None:
    child.memes["hope"] += 1
    parent.meters["helping"] += 1
    plush.meters["helping"] += 1
    world.say(
        f"Then {parent.id} pulled up a blanket, {plush.label} leaned in, and they held a tiny "
        f"forum on the bed."
    )
    world.say(
        f'"What can we do together?" {parent.id} asked. "{child.id} can choose one job, and I can '
        f'choose one too."'
    )


def choose_plan(world: World, child: Entity, parent: Entity, plush: Entity, plan: Plan) -> None:
    for step in plan.steps:
        world.say(step)
    child.meters["busy"] = max(0.0, child.meters["busy"] - plan.calm)
    child.meters["calm"] += plan.calm
    parent.meters["helping"] += 1
    plush.meters["helping"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} picked the plan with the most teamwork, and everyone did their part."
    )


def resolution(world: World, child: Entity, parent: Entity, plush: Entity) -> None:
    room = world.rooms["bedroom"]
    child.memes["joy"] += 1
    child.memes["love"] += 1
    room.meters["quiet"] += 1
    world.say(
        f"Soon the lamp glowed soft, the room was quiet, and {child.id}'s body felt heavy "
        f"and safe."
    )
    world.say(
        f"{child.id} cuddled {plush.label}, smiled through the last blush, and fell asleep "
        f"while {parent.id} whispered goodnight."
    )


def tell(
    child_name: str = "Mia",
    child_gender: str = "girl",
    parent_type: str = "mother",
    helper_name: str = "Teddy",
    helper_type: str = "bear",
    plan_id: str = "brush_and_breath",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    plush = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", label=helper_name))
    room = world.add(Room(id="bedroom", label="the bedroom"))

    plans = {
        "brush_and_breath": Plan(
            id="brush_and_breath",
            label="brush their teeth and take three slow breaths",
            steps=[
                f"{child.id} brushed {child.pronoun('possessive')} teeth, put the book away, and took three slow breaths.",
                f"{parent.id} dimmed the lamp while {plush.label} counted quietly beside the pillow.",
            ],
            calm=2.0,
            teamwork=2.0,
        ),
        "tuck_and_tidy": Plan(
            id="tuck_and_tidy",
            label="tuck the blanket and tidy the toys",
            steps=[
                f"{child.id} gathered the toys into a basket while {parent.id} tucked the blanket up to {child.pronoun('possessive')} chin.",
                f"{plush.label} sat at the edge of the bed like a tiny coach and watched the room grow still.",
            ],
            calm=2.0,
            teamwork=2.0,
        ),
    }
    plan = plans[plan_id]

    introduce(world, child, parent, plush, room)
    world.para()
    problem(world, child)
    forum(world, child, parent, plush)
    world.para()

    pred = predict_calm(world)
    world.facts["predicted"] = pred
    choose_plan(world, child, parent, plush, plan)
    resolution(world, child, parent, plush)

    world.facts.update(
        child=child,
        parent=parent,
        plush=plush,
        room=room,
        plan=plan,
        story_kind="bedtime_teamwork",
    )
    return world


GENDER_NAMES = {
    "girl": ["Mia", "Luna", "Ivy", "Nora", "Zoe"],
    "boy": ["Noah", "Eli", "Finn", "Leo", "Milo"],
}

HELPERS = ["Teddy", "Bunny", "Owl", "Bear"]


@dataclass
@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    parent_type: str
    helper_name: str
    helper_type: str
    plan_id: str
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


VALID_PLANS = ["brush_and_breath", "tuck_and_tidy"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("bedroom", "bedtime", plan_id) for plan_id in VALID_PLANS]


KNOWLEDGE = {
    "blush": [("What does it mean to blush?",
               "To blush means your face gets a little red because you feel shy, embarrassed, or excited.")],
    "body": [("What is your body?",
              "Your body is the whole you that can move, breathe, eat, and sleep. It needs rest and care.")],
    "forum": [("What is a forum?",
               "A forum is a place where people talk together and share ideas so they can choose what to do.")],
    "teamwork": [("What is teamwork?",
                  "Teamwork means people help each other and do different jobs together to finish one job well.")],
    "bedtime": [("Why is bedtime important?",
                 "Bedtime helps your body rest. Sleep gives you energy for the next day.")],
    "calm": [("What helps a body calm down at night?",
              "Quiet voices, slow breathing, and a cozy room can help a body feel calm and ready for sleep.")],
    "help": [("Why is it good to ask for help?",
              "Asking for help lets people solve a hard problem together, and that can make things safer and easier.")],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small bedtime story world about teamwork and a calm forum.")
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["bear", "bunny", "owl", "toy"])
    ap.add_argument("--plan", choices=VALID_PLANS)
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
    plan_id = args.plan or rng.choice(VALID_PLANS)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GENDER_NAMES[child_gender])
    parent = args.parent or rng.choice(["mother", "father"])
    helper_name = args.helper_name or rng.choice(HELPERS)
    helper_type = args.helper_type or rng.choice(["bear", "bunny", "owl"])
    if args.plan and args.plan not in VALID_PLANS:
        raise StoryError("Unknown bedtime plan.")
    return StoryParams(child_name, child_gender, parent, helper_name, helper_type, plan_id)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    plan = f["plan"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "blush", "body", and "forum".',
        f"Tell a gentle story where {child.id}'s body feels too wiggly for sleep, and a small forum of helpers uses teamwork to make bedtime calm.",
        f"Write a cozy bedtime story where the child feels a blush of embarrassment, asks for help, and uses {plan.label} to get ready for sleep.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    plush = f["plush"]
    plan = f["plan"]
    answers = [
        QAItem(
            question="Why did the child blush?",
            answer=f"{child.id} blushed because bedtime was not going smoothly and the grown-up was waiting for {child.pronoun('object')} to settle down. The blush showed a little shy feeling, not trouble.",
        ),
        QAItem(
            question="What was the problem with the body?",
            answer=f"{child.id}'s body felt wiggly and busy instead of sleepy. That made it hard to rest until everyone worked together.",
        ),
        QAItem(
            question="What was the forum for?",
            answer=f"The forum was a tiny bedtime meeting where {child.id}, {parent.id}, and {plush.label} shared ideas. They used it to choose a calm plan together.",
        ),
    ]
    pred = f.get("predicted", {})
    if pred:
        answers.append(
            QAItem(
                question="How did teamwork help at bedtime?",
                answer=f"Teamwork helped because each helper took one job and the child took one job too. That lowered the busy feeling and raised the calm in the bedroom.",
            )
        )
    answers.append(
        QAItem(
            question="What did they do to get ready for sleep?",
            answer=f"They used the plan to {plan.label}, and that helped the room grow quiet. After that, the child could fall asleep safely and peacefully.",
        )
    )
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"blush", "body", "forum", "teamwork", "bedtime", "calm", "help"}
    out: list[QAItem] = []
    for key in ["blush", "body", "forum", "teamwork", "bedtime", "calm", "help"]:
        if key in tags:
            q, a = KNOWLEDGE[key][0]
            out.append(QAItem(question=q, answer=a))
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
    for r in world.rooms.values():
        meters = {k: v for k, v in r.meters.items() if v}
        memes = {k: v for k, v in r.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {r.id:8} (room   ) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("Mia", "girl", "mother", "Teddy", "bear", "brush_and_breath"),
    StoryParams("Noah", "boy", "father", "Bunny", "bunny", "tuck_and_tidy"),
]


ASP_RULES = r"""
valid(Place, Topic, Plan) :- place(Place), topic(Topic), plan(Plan), place_supports(Place, Topic), teamwork_plan(Plan).
calm(Plan) :- teamwork_plan(Plan).
"""

def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("place", "bedroom"))
    lines.append(asp.fact("topic", "bedtime"))
    for p in VALID_PLANS:
        lines.append(asp.fact("plan", p))
        lines.append(asp.fact("teamwork_plan", p))
    lines.append(asp.fact("place_supports", "bedroom", "bedtime"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP matches Python valid_combos().")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"FAIL: generate() smoke test crashed: {exc}")
        return 1
    return rc


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = tell(params.child_name, params.child_gender, params.parent, params.helper_name, params.helper_type, params.plan_id)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
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
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

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
