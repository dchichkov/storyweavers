#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/contestant_happy_ending_superhero_story.py
=========================================================================

A standalone storyworld for a small superhero contest domain.

Premise:
- A child contestant wants to shine in a superhero contest.
- A mishap threatens the contest moment.
- A calm helper uses the right gear or clever move.
- The contestant ends with a happy ending and a clear proof of change.

This world keeps the prose child-facing, state-driven, and complete.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
class Contest:
    id: str
    scene: str
    stage: str
    title: str
    event: str
    prize: str
    ending_image: str
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
class Hazard:
    id: str
    label: str
    phrase: str
    mess: str
    causes: str
    risk: int
    dangerous: bool = True
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
class HelperMove:
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


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.meters["mess"] < THRESHOLD:
            continue
        sig = ("mess", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["worry"] += 1
        out.append("__mess__")
    return out


def _r_spark(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["sparked"] < THRESHOLD:
            continue
        sig = ("spark", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("stage").meters["danger"] += 1
        for hero in world.characters():
            hero.memes["fear"] += 1
        out.append("__spark__")
    return out


CAUSAL_RULES = [Rule("mess", "social", _r_mess), Rule("spark", "physical", _r_spark)]


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


def hazard_risk(hazard: Hazard, contest: Contest) -> bool:
    return hazard.dangerous and contest.id in {"finale", "parade"} and hazard.risk >= 1


def sensible_moves() -> list[HelperMove]:
    return [m for m in MOVES.values() if m.sense >= SENSE_MIN]


def fire_severity(hazard: Hazard, delay: int) -> int:
    return hazard.risk + delay


def is_saved(move: HelperMove, hazard: Hazard, delay: int) -> bool:
    return move.power >= fire_severity(hazard, delay)


def contest_role(hero: str) -> str:
    return "contestant"


def would_hold_together(hero_mood: float, teammate_mood: float) -> bool:
    return hero_mood + teammate_mood >= 6.0


def _do_hazard(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["sparked"] += 1
    target.meters["scorched"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, hero: Entity, partner: Entity, contest: Contest) -> None:
    hero.memes["hope"] += 1
    partner.memes["support"] += 1
    world.say(
        f"On a bright afternoon, {hero.id} and {partner.id} stepped into {contest.scene}. "
        f"The {contest.stage} glowed with banners, cheers, and a shiny {contest.title} sign."
    )
    world.say(
        f"{hero.id} was the {contest_role(hero.id)} for the day, and {hero.id} wanted to win the {contest.prize}."
    )


def dare(world: World, hero: Entity, contest: Contest) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f'"I can do it!" {hero.id} said, standing tall like a superhero on the {contest.stage}. '
        f"{contest.event.capitalize()} was about to begin."
    )


def warn(world: World, helper: Entity, hero: Entity, hazard: Hazard, contest: Contest) -> None:
    helper.memes["care"] += 1
    world.say(
        f"{helper.id} frowned and pointed at the {hazard.label}. "
        f'"That {hazard.label} can make a real {hazard.causes}, and it could ruin the contest," {helper.id} said.'
    )
    world.say(
        f'"Let\'s use a safer plan before the crowd notices."'
    )


def meddle(world: World, hero: Entity, hazard: Hazard) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"But {hero.id} felt a little too proud to stop. "
        f"{hero.id} reached for {hazard.phrase}, hoping it would make the act look more powerful."
    )


def spark_accident(world: World, hazard: Hazard, stage_item: Entity) -> None:
    _do_hazard(world, stage_item)
    world.say(
        f"With a quick flash, the {hazard.label} sent a tiny spark onto the {stage_item.label}. "
        f"For one breath it looked exciting, and then a small orange line began to creep."
    )


def alarm(world: World, helper: Entity, hero: Entity, stage_item: Entity) -> None:
    world.say(f'"{hero.id}! Stop!" {helper.id} shouted. "The {stage_item.label} is catching!"')
    world.say(f"The crowd gasped, and the superhero music cut off in a snap.")


def rescue(world: World, adult: Entity, move: HelperMove, stage_item: Entity, contest: Contest) -> None:
    stage_item.meters["sparked"] = 0.0
    world.get("stage").meters["danger"] = 0.0
    world.say(
        f"{adult.id} hurried over and {move.text.replace('{target}', stage_item.label)}."
    )
    world.say(
        f"The small flame disappeared at once, and the {contest.stage} stayed safe for the rest of the show."
    )


def happy_finish(world: World, hero: Entity, partner: Entity, contest: Contest) -> None:
    hero.memes["joy"] += 2
    partner.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say("For a moment, everyone was quiet.")
    world.say(
        f"Then {partner.id} laughed and clapped {partner.pronoun('possessive')} hands, "
        f"and {hero.id} took a deep breath and smiled."
    )
    world.say(
        f"The announcer handed {hero.id} the {contest.prize}, and the two heroes posed under the lights."
    )
    world.say(
        f"At the end, {contest.ending_image}."
    )


def tell(contest: Contest, hazard: Hazard, move: HelperMove,
         hero_name: str = "Mila", hero_gender: str = "girl",
         partner_name: str = "Jules", partner_gender: str = "boy",
         adult_name: str = "Coach", adult_gender: str = "woman",
         delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="contestant"))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_gender, role="helper"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult"))
    stage_item = world.add(Entity(id="stage_item", type="thing", label="cape", role="prop"))

    setup(world, hero, partner, contest)
    world.para()
    dare(world, hero, contest)
    warn(world, partner, hero, hazard, contest)
    meddle(world, hero, hazard)

    if not hazard_risk(hazard, contest):
        world.say("Nothing dangerous happened, so the show stayed calm from start to finish.")
        happy_finish(world, hero, partner, contest)
        outcome = "safe"
    else:
        world.para()
        spark_accident(world, hazard, stage_item)
        alarm(world, partner, hero, stage_item)
        if is_saved(move, hazard, delay):
            world.para()
            rescue(world, adult, move, stage_item, contest)
            world.say(
                f"{adult.id} nodded and said, '{hazard.label.capitalize()} was never a toy, but you both did the right thing by calling for help.'"
            )
            happy_finish(world, hero, partner, contest)
            outcome = "saved"
        else:
            world.para()
            world.say(
                f"{adult.id} tried to help, but the {hazard.label} had already made too big a mess for that move."
            )
            world.say(
                f"The heroes rushed everyone away, and the contest ended with smoke and tears instead of applause."
            )
            world.say(
                f"Still, {hero.id} and {partner.id} stayed safe, and they learned to ask for help sooner next time."
            )
            outcome = "near_miss"

    world.facts.update(
        contest=contest, hazard=hazard, move=move, hero=hero, partner=partner,
        adult=adult, stage_item=stage_item, delay=delay, outcome=outcome,
        sparked=stage_item.meters["scorched"] >= THRESHOLD,
    )
    return world


CONTESTS = {
    "finale": Contest(
        "finale", "a packed hall", "stage", "Super Star Cup", "hero show", "gold medal",
        "bright red capes waving overhead", tags={"contest", "happy"}),
    "parade": Contest(
        "parade", "a city parade", "float", "Hero Parade Trophy", "float ride", "silver ribbon",
        "streets shining with streamers", tags={"contest", "happy"}),
    "fair": Contest(
        "fair", "a school fair", "stage", "Little Hero Ribbon", "talent turn", "blue ribbon",
        "kids cheering beside paper stars", tags={"contest", "happy"}),
}

HAZARDS = {
    "confetti_cannon": Hazard(
        "confetti_cannon", "confetti cannon", "the confetti cannon", "confetti everywhere",
        "made a loud pop", 2, True, tags={"spark", "contest"}),
    "spark_shoes": Hazard(
        "spark_shoes", "spark shoes", "the spark shoes", "a bright flash", "crackled",
        1, True, tags={"spark", "contest"}),
    "smoke_gadget": Hazard(
        "smoke_gadget", "smoke gadget", "the smoke gadget", "a cloud of smoke", "hissed",
        2, True, tags={"smoke", "contest"}),
}

MOVES = {
    "shield": HelperMove(
        "shield", 3, 3, "pulled the cape down and covered the tiny spark with a thick shield",
        "tried to cover the spark, but the mess was already too big",
        "pulled the cape down and covered the tiny spark"),
    "spray": HelperMove(
        "spray", 3, 4, "grabbed the water sprayer and sprayed the spark until it vanished",
        "sprayed, but the spark kept jumping",
        "grabbed the water sprayer and sprayed the spark"),
    "blanket": HelperMove(
        "blanket", 2, 2, "threw a heavy blanket over the flashing prop and pressed the heat down",
        "threw the blanket, but the flame was already too fierce",
        "threw a heavy blanket over the flashing prop"),
}

GIRL_NAMES = ["Mila", "Nora", "Ava", "Zoe", "Lena", "Ruby", "Iris", "Maya"]
BOY_NAMES = ["Jules", "Theo", "Finn", "Leo", "Noah", "Ezra", "Milo", "Ari"]


@dataclass
@dataclass
class StoryParams:
    contest: str
    hazard: str
    move: str
    hero: str
    hero_gender: str
    partner: str
    partner_gender: str
    adult: str
    adult_gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for cid, contest in CONTESTS.items():
        for hid, hazard in HAZARDS.items():
            if hazard_risk(hazard, contest):
                for mid, move in MOVES.items():
                    if is_saved(move, hazard, 0):
                        out.append((cid, hid, mid))
    return out


def explain_rejection(hazard: Hazard, contest: Contest) -> str:
    return (
        f"(No story: the {hazard.label} would not create a real danger in {contest.title}, "
        f"so there is no honest superhero rescue to tell. Pick a more dangerous contest prop.)"
    )


def explain_move(rid: str) -> str:
    r = MOVES[rid]
    good = ", ".join(sorted(m.id for m in sensible_moves()))
    return (
        f"(Refusing move '{rid}': it is too weak for the problem (sense={r.sense} < {SENSE_MIN}). "
        f"Try: {good}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if is_saved(MOVES[params.move], HAZARDS[params.hazard], params.delay):
        return "saved"
    return "near_miss"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    contest, hazard = f["contest"], f["hazard"]
    return [
        f'Write a happy superhero story for a 3-to-5-year-old that includes the word "contest" and ends with a cheering crowd.',
        f"Tell a superhero story where {f['hero'].id} the contestant gets into trouble with {hazard.label} at {contest.title}, but the team fixes it and everyone is safe.",
        f"Write a short story about a contestant, a risky prop, and a kind helper who saves the day in a bright happy ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, partner, adult = f["hero"], f["partner"], f["adult"]
    contest, hazard, move = f["contest"], f["hazard"], f["move"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, the contestant, and {partner.id}, who helped at the show. {adult.id} also came to help when the trouble started.",
        ),
        (
            "What did the contestant want?",
            f"{hero.id} wanted to shine in the {contest.title} and win the {contest.prize}. {hero.id} wanted the act to look brave and exciting.",
        ),
        (
            "What went wrong?",
            f"The {hazard.label} made a real spark and the {hero.id}'s cape prop started to catch. That was dangerous because the contest stage could have been ruined.",
        ),
    ]
    if f["outcome"] == "saved":
        qa.append(
            (
                "How did they fix the problem?",
                f"{adult.id} used {move.qa_text} and stopped the danger quickly. That kept the {contest.stage} safe and let the happy ending happen.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily. {hero.id} still got the {contest.prize}, the crowd cheered, and the heroes stood under the lights.",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"The heroes escaped safely, but the contest got messy and the show could not continue right away. Even so, {hero.id} learned to ask for help sooner.",
            )
        )
    return qa


KNOWLEDGE = {
    "contest": [("What is a contest?", "A contest is an event where people try their best and someone may win a prize.")],
    "spark": [("Why can sparks be dangerous?", "A spark can start a fire or make something burn if it lands on the wrong thing.")],
    "cape": [("What is a cape?", "A cape is a piece of clothing that hangs from your shoulders and can make play feel heroic.")],
    "hero": [("What is a superhero?", "A superhero is a pretend hero who is brave, helpful, and uses special gear or powers to save the day.")],
    "help": [("What should you do when something goes wrong?", "Call a grown-up right away and stay calm so everyone can get safe.")],
}
KNOWLEDGE_ORDER = ["contest", "hero", "cape", "spark", "help"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["contest"].tags) | set(world.facts["hazard"].tags)
    if world.facts["outcome"] == "saved":
        tags.add("help")
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("finale", "confetti_cannon", "spray", "Mila", "girl", "Jules", "boy", "Coach", "woman", 0),
    StoryParams("parade", "spark_shoes", "shield", "Theo", "boy", "Ava", "girl", "Dad", "man", 0),
    StoryParams("fair", "smoke_gadget", "blanket", "Nora", "girl", "Leo", "boy", "Mom", "woman", 1),
]


def asp_facts() -> str:
    import asp
    lines = []
    for cid in CONTESTS:
        lines.append(asp.fact("contest", cid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if h.dangerous:
            lines.append(asp.fact("dangerous", hid))
        lines.append(asp.fact("risk", hid, h.risk))
    for mid, m in MOVES.items():
        lines.append(asp.fact("move", mid))
        lines.append(asp.fact("sense", mid, m.sense))
        lines.append(asp.fact("power", mid, m.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
hazard_risk(H, C) :- hazard(H), contest(C), dangerous(H), risk(H, R), R >= 1.
sensible(M) :- move(M), sense(M, S), sense_min(N), S >= N.
valid(C, H, M) :- contest(C), hazard(H), move(M), hazard_risk(H, C), sensible(M).
saved(H, M, D) :- move(M), power(M, P), risk(H, R), P >= R + D.
outcome(saved) :- chosen_hazard(H), chosen_move(M), delay(D), saved(H, M, D).
outcome(near_miss) :- chosen_hazard(H), chosen_move(M), delay(D), not saved(H, M, D).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen_hazard", params.hazard), asp.fact("chosen_move", params.move), asp.fact("delay", params.delay)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos.")
    cases = list(CURATED)
    for s in range(20):
        try:
            cases.append(resolve_params(build_parser().parse_args([]), random.Random(100 + s)))
        except StoryError:
            pass
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad} outcomes differ.")
    try:
        sample = generate(CURATED[0])
        assert sample.story.strip()
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero contest story world.")
    ap.add_argument("--contest", choices=CONTESTS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--hero")
    ap.add_argument("--partner")
    ap.add_argument("--adult")
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
    if args.hazard and args.contest:
        if not hazard_risk(HAZARDS[args.hazard], CONTESTS[args.contest]):
            raise StoryError(explain_rejection(HAZARDS[args.hazard], CONTESTS[args.contest]))
    if args.move and MOVES[args.move].sense < SENSE_MIN:
        raise StoryError(explain_move(args.move))
    combos = [c for c in valid_combos()
              if (args.contest is None or c[0] == args.contest)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.move is None or c[2] == args.move)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    contest, hazard, move = rng.choice(sorted(combos))
    hero_gender = rng.choice(["girl", "boy"])
    partner_gender = "boy" if hero_gender == "girl" else "girl"
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    partner = args.partner or rng.choice(BOY_NAMES if partner_gender == "boy" else GIRL_NAMES)
    adult = args.adult or rng.choice(["Coach", "Mom", "Dad", "Aunt Rae"])
    adult_gender = "woman" if adult in {"Coach", "Mom", "Aunt Rae"} else "man"
    return StoryParams(contest, hazard, move, hero, hero_gender, partner, partner_gender, adult, adult_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(CONTESTS[params.contest], HAZARDS[params.hazard], MOVES[params.move],
                 params.hero, params.hero_gender, params.partner, params.partner_gender,
                 params.adult, params.adult_gender, params.delay)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
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
