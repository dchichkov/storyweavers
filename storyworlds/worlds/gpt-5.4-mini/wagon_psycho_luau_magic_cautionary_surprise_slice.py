#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/wagon_psycho_luau_magic_cautionary_surprise_slice.py
====================================================================================

A small standalone storyworld for a slice-of-life tale about a backyard luau,
a wagon, a little bit of magic, and a cautionary surprise.

The world model keeps one child-led day from drifting into a risky idea:
someone wants to use a magic spark near delicate decorations, another person
foresees the trouble, and the ending turns into a safer, brighter surprise.

This file is self-contained and stdlib-only.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

# Make the shared result containers importable when this script is run directly.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)



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
    mood: str
    details: str

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
class ChildPlan:
    id: str
    verb: str
    want: str
    sparkle: str
    risk: str
    zone: str
    mess: str
    keyword: str
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
class Decoration:
    id: str
    label: str
    phrase: str
    fragile: bool = True
    catches_spark: bool = True
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
class SafeSurprise:
    id: str
    label: str
    phrase: str
    glow: str
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
        import copy

        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_scatter(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters.get("sparked", 0.0) < THRESHOLD:
            continue
        sig = ("scatter", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "decor" in world.entities:
            world.get("decor").meters["frayed"] = world.get("decor").meters.get("frayed", 0.0) + 1
        for ent in list(world.entities.values()):
            if ent.role in {"instigator", "cautioner"}:
                ent.memes["worry"] = ent.memes.get("worry", 0.0) + 1
        out.append("__spark__")
    return out


CAUSAL_RULES = [_r_scatter]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(plan: ChildPlan, decor: Decoration) -> bool:
    return plan.catches_spark and decor.fragile


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def is_contained(response: Response, delay: int) -> bool:
    return response.power >= (1 + delay)


def predict(world: World, decor_id: str) -> dict:
    sim = world.copy()
    _do_magic(sim, sim.get("spark"), narrate=False)
    return {"sparked": sim.get(decor_id).meters.get("sparked", 0.0) >= THRESHOLD}


def _do_magic(world: World, spark: Entity, narrate: bool = True) -> None:
    spark.meters["sparked"] = spark.meters.get("sparked", 0.0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, child: Entity, other: Entity, setting: Setting) -> None:
    world.say(
        f"On a warm evening, {child.id} and {other.id} rolled a little wagon into "
        f"{setting.place}. {setting.details}"
    )
    world.say(
        f"They were getting ready for a luau, with flowers, fruit, and a silly "
        f"pet named Psycho riding along in the wagon."
    )


def want_magic(world: World, child: Entity, plan: ChildPlan, decor: Decoration) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    world.say(
        f'{child.id} pointed at the decorations. "{plan.want}," {child.pronoun()} said. '
        f'"I can make them {plan.sparkle} with magic."'
    )
    world.say(f"It sounded exciting for one tiny moment.")


def warn(world: World, other: Entity, child: Entity, plan: ChildPlan, decor: Decoration) -> None:
    pred = predict(world, "decor")
    other.memes["caution"] = other.memes.get("caution", 0.0) + 1
    if pred["sparked"]:
        world.say(
            f'{other.id} bit {other.pronoun("possessive")} lip. "{child.id}, the '
            f'{decor.label} could get {plan.risk}. Magic is lovely, but not right '
            f"next to something so delicate."
        )
    else:
        world.say(f'{other.id} still looked unsure and asked {child.id} to pause first.')


def choose_pause(world: World, child: Entity, other: Entity, plan: ChildPlan) -> None:
    child.memes["restraint"] = child.memes.get("restraint", 0.0) + 1
    world.say(
        f"{child.id} glanced at {other.id}, then at the wagon, and decided not to rush."
    )
    world.say(
        f'"Okay," {child.id} said. "I can save the magic for a safer place."'
    )


def do_spark(world: World, spark: Entity, plan: ChildPlan, decor: Decoration) -> None:
    world.say(
        f"{plan.keyword.capitalize()}-bright magic flickered from the spark, and the air "
        f"felt warm and shiny."
    )
    _do_magic(world, spark)


def alarm(world: World, other: Entity, child: Entity, decor: Decoration) -> None:
    world.say(f'"{child.id}!" {other.id} cried. "{decor.label}!"')


def rescue(world: World, parent: Entity, response: Response, decor: Decoration) -> None:
    decor_ent = world.get("decor")
    decor_ent.meters["sparked"] = 0.0
    body = response.text.replace("{target}", decor.label)
    world.say(
        f"{parent.label_word.capitalize()} came over right away and {body}."
    )
    world.say(
        "The little glow settled down, and the luau decorations stayed safe and tidy."
    )


def lesson(world: World, parent: Entity, child: Entity, other: Entity, plan: ChildPlan) -> None:
    for kid in (child, other):
        kid.memes["relief"] = kid.memes.get("relief", 0.0) + 1
        kid.memes["love"] = kid.memes.get("love", 0.0) + 1
    world.say("For a second, everyone was quiet.")
    world.say(
        f"Then {parent.label_word.capitalize()} smiled and knelt down by the wagon. "
        f'"Magic is wonderful," {parent.pronoun()} said, "but caution keeps the fun kind."'
    )
    world.say(f'"We can do that," whispered {child.id} and {other.id}.')


def surprise_end(world: World, parent: Entity, child: Entity, other: Entity, surprise: SafeSurprise) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    other.memes["joy"] = other.memes.get("joy", 0.0) + 1
    world.say(
        f"The next moment, {parent.label_word.capitalize()} had a surprise: {surprise.phrase} "
        f"that {surprise.glow}."
    )
    world.say(
        f"{child.id} hung it on the wagon, {other.id} laughed, and Psycho bounced beside them."
    )
    world.say(
        "That evening, the luau looked extra bright, and the wagon rolled around the yard like a tiny parade."
    )


def tell(setting: Setting, plan: ChildPlan, decor: Decoration, response: Response,
         child_name: str = "Mina", child_gender: str = "girl",
         other_name: str = "Niko", other_gender: str = "boy",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="instigator"))
    other = world.add(Entity(id=other_name, kind="character", type=other_gender, role="cautioner"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    spark = world.add(Entity(id="spark", type="magic", label="spark"))
    deco = world.add(Entity(id="decor", type="thing", label=decor.label))
    intro(world, child, other, setting)
    world.para()
    want_magic(world, child, plan, decor)
    warn(world, other, child, plan, decor)
    if plan.id == "avert":
        choose_pause(world, child, other, plan)
        world.para()
        surprise_end(world, parent, child, other, SURPRISES["lantern"])
        outcome = "averted"
    else:
        do_spark(world, spark, plan, decor)
        alarm(world, other, child, decor)
        contained = is_contained(response, delay)
        outcome = "contained" if contained else "burst"
        world.para()
        if contained:
            rescue(world, parent, response, decor)
            lesson(world, parent, child, other, plan)
            world.para()
            surprise_end(world, parent, child, other, SURPRISES["lantern"])
        else:
            world.say(
                f"{parent.label_word.capitalize()} hurried over, but {response.fail.replace('{target}', decor.label)}."
            )
            world.say("The decorations had to be moved away before the little spark could spread further.")
            lesson(world, parent, child, other, plan)
    world.facts.update(
        child=child, other=other, parent=parent, plan=plan, decor_cfg=decor,
        response=response, setting=setting, outcome=outcome, delay=delay
    )
    return world


SENSE_MIN = 2


SETTINGS = {
    "backyard": Setting("backyard", "the backyard", "calm", "The string lights were already blinking, and the table had pineapple slices and folded napkins."),
    "patio": Setting("patio", "the patio", "cozy", "A paper lantern swayed from the porch, and the music was soft."),
}

PLANS = {
    "magic": ChildPlan("magic", "make the luau banners shimmer", "make the luau banners shimmer", "sparkle", "get singed", "banners", "magic", "magic", {"magic"}),
    "cautionary": ChildPlan("cautionary", "wave the spark near the flowers", "wave the spark near the flowers", "twinkle", "frayed", "flowers", "caution", "cautionary", {"cautionary"}),
    "surprise": ChildPlan("surprise", "tap the wagon lantern with a spark", "tap the wagon lantern with a spark", "glow", "wobbly", "lantern", "surprise", "surprise", {"surprise"}),
    "avert": ChildPlan("avert", "show the magic from a distance", "show the magic from a distance", "glimmer", "safe", "air", "safe", "caution", {"cautionary"}),
}

DECORATIONS = {
    "banners": Decoration("banners", "paper banners", "the paper banners"),
    "flowers": Decoration("flowers", "paper flowers", "the paper flowers"),
    "lei": Decoration("lei", "a lei", "the flower lei"),
}

SURPRISES = {
    "lantern": SafeSurprise("lantern", "lantern", "a battery lantern", "glowed soft gold", {"surprise"}),
    "shells": SafeSurprise("shells", "shells", "a basket of shiny shells", "sparkled like small moons", {"surprise"}),
}

RESPONSES = {
    "fan": Response("fan", 3, 3, "used a big fan to blow the tiny spark away from {target}", "used a fan, but the spark was already too lively", "blew the spark away from {target}", {"fan"}),
    "cover": Response("cover", 3, 4, "covered {target} with a thick tray and snuffed the spark out", "covered {target}, but the little spark hopped too far", "covered {target} and snuffed the spark out", {"cover"}),
    "water": Response("water", 1, 1, "splashed a cup of water over {target}", "splashed a cup of water, but it was too small to help", "splashed water over {target}", {"water"}),
}


GIVEN_WORDS = ["wagon", "psycho", "luau", "Magic", "Cautionary", "Surprise"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, plan in PLANS.items():
            for did, decor in DECORATIONS.items():
                if reasonableness_gate(plan, decor):
                    combos.append((sid, pid, did))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    plan: str
    decor: str
    response: str
    child: str
    child_gender: str
    other: str
    other_gender: str
    parent: str
    delay: int = 0
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
    "wagon": [("What is a wagon?", "A wagon is a little cart with wheels that you can pull or push. Kids often use it for toys, picnic things, or pretend adventures.")],
    "luau": [("What is a luau?", "A luau is a party with music, food, flowers, and a happy island-style feeling.")],
    "magic": [("What is magic in a story?", "Magic in a story is something special or surprising that seems a little impossible, like a sparkle, glow, or charm.")],
    "cautionary": [("What does cautionary mean?", "Cautionary means a story gives a warning and helps you learn to be careful.")],
    "surprise": [("What is a surprise?", "A surprise is something you did not expect. It can make a story extra fun or sweet.")],
    "spark": [("What is a spark?", "A spark is a tiny flash of light or heat. It can be pretty, but it can also be risky near dry things.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story that includes the words "wagon", "psycho", and "luau", with a small magical moment and a careful warning.',
        f'Tell a child-friendly story where {f["child"].id} wants to use magic near luau decorations, but {f["other"].id} gives a cautionary warning before the surprise ending.',
        f'Write a gentle backyard story about a wagon at a luau, a risky spark, and a happy surprise at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, other, parent = f["child"], f["other"], f["parent"]
    plan, decor, response = f["plan"], f["decor_cfg"], f["response"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {other.id}, with {parent.label_word.capitalize()} nearby to help. They are getting ready for a little luau and rolling a wagon around the yard."
        ),
        QAItem(
            question="What did the child want to do?",
            answer=f"{child.id} wanted to {plan.want}. That seemed magical, but it could trouble {decor.label} because the spark was too close."
        ),
        QAItem(
            question="Why did the other child warn them?",
            answer=f"{other.id} warned {child.id} because the plan could leave {decor.label} {plan.risk}. The warning was a kind, careful pause before anything went wrong."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(QAItem(
            question="How did the story avoid trouble?",
            answer=f"{child.id} listened, backed up, and saved the magic for a safer moment. Then the family could enjoy the luau without any damaged decorations."
        ))
    else:
        body = response.qa_text.replace("{target}", decor.label)
        qa.append(QAItem(
            question="How was the spark stopped?",
            answer=f"{parent.label_word.capitalize()} came quickly and {body}. That stopped the tiny trouble before it could grow into a bigger mess."
        ))
    qa.append(QAItem(
        question="What was the surprise at the end?",
        answer=f"{parent.label_word.capitalize()} brought out {SURPRISES['lantern'].phrase} that {SURPRISES['lantern'].glow}. It made the wagon, the luau table, and even Psycho feel bright and special."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    topics = set(world.facts["plan"].tags) | set(world.facts["decor_cfg"].tags) | set(world.facts["response"].tags) | {"wagon", "luau", "surprise"}
    out: list[QAItem] = []
    for key, items in KNOWLEDGE.items():
        if key in topics:
            for q, a in items:
                out.append(QAItem(q, a))
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
        parts = []
        if e.meters:
            parts.append(f"meters={dict(e.meters)}")
        if e.memes:
            parts.append(f"memes={dict(e.memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        if e.label:
            parts.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("backyard", "magic", "banners", "cover", "Mina", "girl", "Niko", "boy", "mother", 0),
    StoryParams("patio", "cautionary", "flowers", "fan", "Ada", "girl", "Ben", "boy", "grandmother", 0),
    StoryParams("backyard", "surprise", "lei", "cover", "Leo", "boy", "Mia", "girl", "father", 0),
]


def explain_rejection(plan: ChildPlan, decor: Decoration) -> str:
    return f"(No story: {plan.id} does not create a meaningful risk for {decor.label}, so there is no honest cautionary turn.)"


def outcome_of(params: StoryParams) -> str:
    return "averted" if params.plan == "avert" else ("contained" if RESPONSES[params.response].sense >= 2 else "burst")


ASP_RULES = r"""
risk(P, D) :- plan(P), decor(D), catches_spark(P), fragile(D).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, P, D) :- setting(S), plan(P), decor(D), risk(P, D).
outcome(averted) :- chosen_plan(avert).
outcome(contained) :- chosen_plan(P), response(R), sensible(R), P != avert.
outcome(burst) :- chosen_plan(P), response(R), not sensible(R), P != avert.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PLANS.items():
        lines.append(asp.fact("plan", pid))
        if "cautionary" in p.tags:
            lines.append(asp.fact("catches_spark", pid))
    for did in DECORATIONS:
        lines.append(asp.fact("decor", did))
        lines.append(asp.fact("fragile", did))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    clingo = set(asp.atoms(model, "valid"))
    python = set(valid_combos())
    ok = clingo == python
    print("OK: ASP gate matches valid_combos()." if ok else f"MISMATCH: {clingo ^ python}")
    sample = generate(CURATED[0])
    print("OK: generate() smoke test passed." if sample.story else "MISMATCH: empty story")
    return 0 if ok and sample.story else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life luau wagon storyworld with a cautionary magical turn and a surprise ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--decor", choices=DECORATIONS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--other")
    ap.add_argument("--other-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
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
              and (args.plan is None or c[1] == args.plan)
              and (args.decor is None or c[2] == args.decor)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, plan, decor = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    other_gender = args.other_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(["Mina", "Ada", "Leo", "Nina", "Ira"])
    other = args.other or rng.choice([n for n in ["Niko", "Ben", "Mia", "Owen", "Tess"] if n != child])
    parent = args.parent or rng.choice(["mother", "father", "grandmother"])
    return StoryParams(setting, plan, decor, response, child, child_gender, other, other_gender, parent, args.delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PLANS[params.plan], DECORATIONS[params.decor], RESPONSES[params.response],
                 params.child, params.child_gender, params.other, params.other_gender, params.parent, params.delay)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
