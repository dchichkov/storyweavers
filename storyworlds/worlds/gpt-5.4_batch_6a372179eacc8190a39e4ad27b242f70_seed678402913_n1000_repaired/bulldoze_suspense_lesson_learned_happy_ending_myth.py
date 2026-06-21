#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bulldoze_suspense_lesson_learned_happy_ending_myth.py
=================================================================================

A standalone storyworld for a tiny myth-shaped tale:

A proud ruler wants to bulldoze a sacred place to build something grander.
A child or elder notices a warning in the living world, suspense grows through
the night, and the ruler must choose whether to force the land or listen.
When the warning is heeded, the place is spared, the plan changes, and the
ending image proves that wisdom became part of the kingdom.

Run it
------
    python storyworlds/worlds/gpt-5.4/bulldoze_suspense_lesson_learned_happy_ending_myth.py
    python storyworlds/worlds/gpt-5.4/bulldoze_suspense_lesson_learned_happy_ending_myth.py --site hill_shrine
    python storyworlds/worlds/gpt-5.4/bulldoze_suspense_lesson_learned_happy_ending_myth.py --plan road
    python storyworlds/worlds/gpt-5.4/bulldoze_suspense_lesson_learned_happy_ending_myth.py --machine hand_cart
    python storyworlds/worlds/gpt-5.4/bulldoze_suspense_lesson_learned_happy_ending_myth.py --all
    python storyworlds/worlds/gpt-5.4/bulldoze_suspense_lesson_learned_happy_ending_myth.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "queen", "mother", "goddess", "priestess"}
        male = {"boy", "man", "king", "father", "god", "shepherd"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Site:
    id: str
    label: str
    phrase: str
    spirit: str
    omen: str
    gift: str
    stubborn_cost: str
    plan_image: str
    tags: set[str] = field(default_factory=set)
    sacred: bool = True


@dataclass
class Plan:
    id: str
    label: str
    phrase: str
    boast: str
    gentle_fix: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Machine:
    id: str
    label: str
    phrase: str
    power: int
    sense: int
    verb: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Sign:
    id: str
    first: str
    second: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    site: str
    plan: str
    machine: str
    sign: str
    ruler_name: str
    ruler_type: str
    witness_name: str
    witness_type: str
    helper_name: str
    helper_type: str
    relation: str
    seed: Optional[int] = None


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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_unrest(world: World) -> list[str]:
    out: list[str] = []
    site = world.entities.get("site")
    machine = world.entities.get("machine")
    if not site or not machine:
        return out
    if site.meters["threat"] < THRESHOLD or machine.meters["near"] < THRESHOLD:
        return out
    sig = ("unrest", site.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    site.meters["danger"] += 1
    for eid in ("ruler", "witness", "helper"):
        if eid in world.entities:
            world.get(eid).memes["fear"] += 1
    out.append("__unrest__")
    return out


def _r_blessing(world: World) -> list[str]:
    out: list[str] = []
    site = world.entities.get("site")
    if not site:
        return out
    if site.meters["honored"] < THRESHOLD:
        return out
    sig = ("blessing", site.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    site.meters["peace"] += 1
    for eid in ("ruler", "witness", "helper"):
        if eid in world.entities:
            world.get(eid).memes["relief"] += 1
            world.get(eid).memes["joy"] += 1
    out.append("__blessing__")
    return out


CAUSAL_RULES = [
    Rule(name="unrest", tag="physical", apply=_r_unrest),
    Rule(name="blessing", tag="spiritual", apply=_r_blessing),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SITES = {
    "hill_shrine": Site(
        id="hill_shrine",
        label="hill shrine",
        phrase="a white shrine on a windy hill",
        spirit="the hill's old spirit",
        omen="the shrine bell rang though nobody touched it",
        gift="wild thyme and bright spring water",
        stubborn_cost="the wind would howl through broken stones",
        plan_image="steps of pale stone curling up the hill",
        tags={"shrine", "hill", "sacred"},
        sacred=True,
    ),
    "olive_grove": Site(
        id="olive_grove",
        label="olive grove",
        phrase="an ancient olive grove beside the city wall",
        spirit="the grove's quiet guardian",
        omen="silver leaves turned their pale sides all at once",
        gift="cool shade and bowls of olives",
        stubborn_cost="the oldest trunks would split and bleed bitter sap",
        plan_image="a shaded court woven through the trees",
        tags={"grove", "olive", "sacred"},
        sacred=True,
    ),
    "river_stone": Site(
        id="river_stone",
        label="river stone",
        phrase="a broad moon-marked stone beside the river",
        spirit="the river's listening spirit",
        omen="the water drew back from the stone and then rushed in again",
        gift="clear fish pools and a safe crossing",
        stubborn_cost="the ford would turn wild and treacherous",
        plan_image="an arched path that bent around the stone",
        tags={"river", "stone", "sacred"},
        sacred=True,
    ),
    "empty_field": Site(
        id="empty_field",
        label="empty field",
        phrase="an empty field outside the grain barns",
        spirit="no old spirit at all",
        omen="nothing strange happened there",
        gift="plain grass and open dirt",
        stubborn_cost="nothing sacred would be lost",
        plan_image="straight furrows and fresh storehouses",
        tags={"field"},
        sacred=False,
    ),
}

PLANS = {
    "road": Plan(
        id="road",
        label="road",
        phrase="a king's road for chariots and traders",
        boast="The road will make my name run farther than the river.",
        gentle_fix="curve the road around the holy place",
        ending="travelers followed the new road and lifted their hands in thanks when they saw the sacred place still standing",
        tags={"road", "travel"},
    ),
    "palace_gate": Plan(
        id="palace_gate",
        label="palace gate",
        phrase="a grand gate faced with blue stone",
        boast="My gate will shine before dawn itself.",
        gentle_fix="raise the gate lower on the slope and leave the holy place untouched",
        ending="the blue gate gleamed below, while lamps still burned softly at the sacred place above",
        tags={"gate", "city"},
    ),
    "market_square": Plan(
        id="market_square",
        label="market square",
        phrase="a market square with carved fountains",
        boast="My square will gather every voice in the kingdom.",
        gentle_fix="set the market beside the holy place instead of over it",
        ending="the fountains splashed nearby, and sellers left flowers at the sacred place each morning",
        tags={"market", "city"},
    ),
}

MACHINES = {
    "bronze_bulldozer": Machine(
        id="bronze_bulldozer",
        label="bronze bulldozer",
        phrase="a bronze bulldozer pulled by snorting oxen",
        power=3,
        sense=3,
        verb="bulldoze",
        tags={"machine", "bulldoze"},
    ),
    "stone_ram": Machine(
        id="stone_ram",
        label="stone ram",
        phrase="a stone ram on thick wooden wheels",
        power=2,
        sense=2,
        verb="bulldoze",
        tags={"machine", "ram"},
    ),
    "hand_cart": Machine(
        id="hand_cart",
        label="hand cart",
        phrase="a hand cart with two squeaky wheels",
        power=1,
        sense=1,
        verb="push",
        tags={"cart"},
    ),
}

SIGNS = {
    "bell": Sign(
        id="bell",
        first="At sunset the air grew still, and then the bell rang by itself.",
        second="Everyone in the courtyard went quiet, because even the swallows stopped in the sky.",
        lesson="Some places are older than a ruler's hurry.",
        tags={"bell", "omen"},
    ),
    "owl": Sign(
        id="owl",
        first="An owl flew in bright daylight and settled on the sacred place.",
        second="It stared without blinking until even the oxen stamped and backed away.",
        lesson="Wisdom can arrive softly, but it should still be heard.",
        tags={"owl", "omen"},
    ),
    "spring": Sign(
        id="spring",
        first="A hidden spring burst from the earth and ran in a shining line around the sacred place.",
        second="The water circled it like a silver finger saying, Not here.",
        lesson="The living earth speaks before it breaks.",
        tags={"spring", "water", "omen"},
    ),
}


def hazard_at_risk(site: Site, machine: Machine) -> bool:
    return site.sacred and machine.power >= 2


def sensible_machine(machine: Machine) -> bool:
    return machine.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for site_id, site in SITES.items():
        for plan_id in PLANS:
            for machine_id, machine in MACHINES.items():
                if hazard_at_risk(site, machine) and sensible_machine(machine):
                    combos.append((site_id, plan_id, machine_id))
    return combos


def explain_rejection(site: Site, machine: Machine) -> str:
    if not site.sacred:
        return (
            f"(No story: {site.phrase} is not sacred in this world, so trying to bulldoze it "
            f"would not awaken suspense, warning, or a mythic lesson. Pick a shrine, grove, or sacred stone.)"
        )
    if machine.power < 2:
        return (
            f"(No story: a {machine.label} is too weak to truly threaten {site.phrase}, "
            f"so the warning has no real weight. Pick a stronger machine.)"
        )
    if machine.sense < SENSE_MIN:
        return (
            f"(Refusing machine '{machine.id}': it scores too low on common sense "
            f"(sense={machine.sense} < {SENSE_MIN}) for this mythic domain. "
            f"Use a stronger, story-shaping machine instead.)"
        )
    return "(No story: this combination does not create a reasonable sacred-place threat.)"


def chooses_mercy(relation: str, sign: Sign) -> bool:
    return relation == "child" or sign.id in {"spring", "bell"}


def predict_anger(world: World, site_id: str, machine_id: str) -> dict:
    sim = world.copy()
    site = sim.get(site_id)
    machine = sim.get(machine_id)
    site.meters["threat"] += 1
    machine.meters["near"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": site.meters["danger"],
        "fear": sim.get("ruler").memes["fear"] + sim.get("witness").memes["fear"],
    }


def opening(world: World, ruler: Entity, witness: Entity, helper: Entity, site: Site, plan: Plan) -> None:
    world.say(
        f"In the days when hills were said to remember footsteps and rivers listened to vows, "
        f"{ruler.id} ruled a bright stone city."
    )
    world.say(
        f"Below the palace lay {site.phrase}. It gave the people {site.gift}, and they treated it with quiet respect."
    )
    world.say(
        f"But {ruler.id} dreamed of {plan.phrase}, and {ruler.pronoun()} said, "
        f'"{plan.boast}"'
    )
    world.say(
        f"{helper.id}, the builder, measured the ground, while {witness.id} watched the sacred place and felt a small knot of worry."
    )


def decree(world: World, ruler: Entity, site: Site, plan: Plan, machine: Machine) -> None:
    world.say(
        f'"At dawn we will {machine.verb} this place and make room for {plan.label}," '
        f"{ruler.id} declared."
    )
    world.say(
        f"{ruler.pronoun().capitalize()} pointed toward {site.label}, and the workers rolled out {machine.phrase}."
    )
    world.get("site").meters["threat"] += 1
    world.get("machine").meters["near"] += 1
    propagate(world, narrate=False)


def warning(world: World, ruler: Entity, witness: Entity, helper: Entity, site: Site, sign: Sign) -> None:
    pred = predict_anger(world, "site", "machine")
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_fear"] = pred["fear"]
    witness.memes["courage"] += 1
    world.say(sign.first)
    world.say(sign.second)
    world.say(
        f'{witness.id} stepped forward and whispered, "{sign.lesson} '
        f'Please do not break {site.label}."'
    )
    world.say(
        f"{helper.id} looked from the machine to the sacred place and said nothing, which made the night feel even more tense."
    )


def night_suspense(world: World, ruler: Entity, site: Site) -> None:
    if world.get("site").meters["danger"] >= THRESHOLD:
        world.say(
            f"That night {ruler.id} could not sleep. Each gust of wind sounded like a warning moving through the stones."
        )
        world.say(
            f"When dawn's first light touched {site.label}, the whole court waited to see whether pride or wisdom would rise first."
        )


def relent(world: World, ruler: Entity, witness: Entity, helper: Entity, site: Site, plan: Plan, sign: Sign) -> None:
    ruler.memes["humility"] += 1
    ruler.memes["fear"] = 0.0
    world.get("site").meters["threat"] = 0.0
    world.get("site").meters["honored"] += 1
    world.get("machine").meters["near"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"At last {ruler.id} lifted {ruler.pronoun('possessive')} hand. "
        f'"No," {ruler.pronoun()} said. "We will not bulldoze what the old powers have guarded."'
    )
    world.say(
        f"{helper.id} bowed low. Together they chose to {plan.gentle_fix}, and the workers turned the machine away."
    )
    world.say(
        f"{witness.id} touched the cool stone of {site.label}, and the morning air no longer felt sharp with fear."
    )
    world.say(
        f"From that day on, {ruler.id} remembered {sign.lesson.lower()}"
    )


def blessing(world: World, site: Site, plan: Plan) -> None:
    world.say(
        f"The sacred place seemed to answer. A soft brightness lay over it, and the people said {site.spirit} was pleased."
    )
    world.say(
        f"Soon {plan.ending}. Children played nearby, but nobody crossed the old boundary with careless feet."
    )
    world.say(
        f"And whenever strangers asked why the holy place still stood, the elders smiled and told how a kingdom grew wiser without breaking what was ancient."
    )


def tell(
    site: Site,
    plan: Plan,
    machine: Machine,
    sign: Sign,
    ruler_name: str = "King Oran",
    ruler_type: str = "king",
    witness_name: str = "Tala",
    witness_type: str = "girl",
    helper_name: str = "Master Ivo",
    helper_type: str = "man",
    relation: str = "child",
) -> World:
    world = World()
    ruler = world.add(Entity(id="ruler", kind="character", type=ruler_type, label="the ruler"))
    ruler.attrs["name"] = ruler_name
    witness = world.add(Entity(id="witness", kind="character", type=witness_type, label="the witness"))
    witness.attrs["name"] = witness_name
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label="the builder"))
    helper.attrs["name"] = helper_name

    world.entities["ruler"].id = ruler_name
    del world.entities["ruler"]
    world.entities[ruler_name] = ruler
    world.entities["witness"] = witness
    world.entities["helper"] = helper
    witness.id = witness_name
    helper.id = helper_name
    del world.entities["witness"]
    del world.entities["helper"]
    world.entities[witness_name] = witness
    world.entities[helper_name] = helper

    world.add(Entity(id="site", type="place", label=site.label, phrase=site.phrase, tags=set(site.tags)))
    world.add(Entity(id="machine", type="machine", label=machine.label, phrase=machine.phrase, tags=set(machine.tags)))

    ruler.role = "ruler"
    witness.role = "witness"
    helper.role = "helper"
    ruler.memes["pride"] = 1
    if relation == "child":
        witness.attrs["relation"] = "child of the city"
    else:
        witness.attrs["relation"] = "temple keeper"

    opening(world, ruler, witness, helper, site, plan)
    world.para()
    decree(world, ruler, site, plan, machine)
    warning(world, ruler, witness, helper, site, sign)
    world.para()
    night_suspense(world, ruler, site)
    if not chooses_mercy(relation, sign):
        raise StoryError("(No story: this setup does not reach the happy ending required by the seed.)")
    relent(world, ruler, witness, helper, site, plan, sign)
    world.para()
    blessing(world, site, plan)

    world.facts.update(
        site=site,
        plan=plan,
        machine=machine,
        sign=sign,
        ruler=ruler,
        witness=witness,
        helper=helper,
        relation=relation,
        outcome="happy",
        threatened=True,
        honored=world.get("site").meters["honored"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "bulldoze": [
        (
            "What does bulldoze mean?",
            "To bulldoze means to push down earth or buildings with a powerful machine. It can change land very quickly, so it must be used carefully."
        )
    ],
    "sacred": [
        (
            "What is a sacred place?",
            "A sacred place is a place people treat with special honor. They believe it should be cared for, not used carelessly."
        )
    ],
    "omen": [
        (
            "What is an omen in a myth?",
            "An omen is a strange sign that warns people something important is happening. In myths, an omen often asks someone to listen and change."
        )
    ],
    "wisdom": [
        (
            "Why is listening wise in myths?",
            "Listening can keep a proud person from making a harmful choice. In myths, wisdom often means stopping before damage is done."
        )
    ],
    "road": [
        (
            "Why do roads matter in old stories?",
            "Roads help people travel, trade, and visit one another. A good ruler builds them in ways that help people without harming what matters."
        )
    ],
    "grove": [
        (
            "What is a grove?",
            "A grove is a small group of trees growing together. In many myths, groves feel peaceful and important."
        )
    ],
    "river": [
        (
            "Why are rivers special in myths?",
            "Rivers bring water, food, and travel, so many stories treat them as living powers. People in myths often show rivers respect."
        )
    ],
}

KNOWLEDGE_ORDER = ["bulldoze", "sacred", "omen", "wisdom", "road", "grove", "river"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    ruler = f["ruler"]
    witness = f["witness"]
    site = f["site"]
    plan = f["plan"]
    return [
        f'Write a short myth for a 3-to-5-year-old that includes the word "bulldoze" and ends happily.',
        f"Tell a myth where {ruler.id} wants to bulldoze {site.phrase} to make {plan.phrase}, but a warning sign creates suspense and changes {ruler.pronoun('possessive')} heart.",
        f"Write a gentle lesson-learned story in myth style where {witness.id} helps save a sacred place and the kingdom becomes wiser."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    ruler = f["ruler"]
    witness = f["witness"]
    helper = f["helper"]
    site = f["site"]
    plan = f["plan"]
    machine = f["machine"]
    sign = f["sign"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {ruler.id}, who wanted a grand new {plan.label}, {witness.id}, who noticed the warning first, and {helper.id}, who helped change the plan."
        ),
        (
            f"Why did {ruler.id} want to bulldoze {site.label}?",
            f"{ruler.id} wanted room for {plan.phrase}. {ruler.pronoun().capitalize()} was thinking about glory and building, not yet about the old sacred place."
        ),
        (
            "What made the story feel suspenseful?",
            f"The strange sign came after the order to bring {machine.phrase}, and everyone had to wait through the night to see what {ruler.id} would do. That waiting, mixed with fear that the sacred place might be broken, made the story tense."
        ),
        (
            f"What warning appeared at {site.label}?",
            f"{sign.first} {sign.second} The sign made people feel that the place was alive and should not be harmed."
        ),
        (
            f"What lesson did {ruler.id} learn?",
            f"{ruler.id} learned that pride should not rush over wisdom. {ruler.pronoun().capitalize()} understood that old, sacred things deserve care, even when a new plan sounds grand."
        ),
        (
            "How did the story end?",
            f"It ended happily because the workers turned the machine away and the new plan was changed instead of forced. After that, {plan.ending}."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"bulldoze", "sacred", "omen", "wisdom"}
    if f["plan"].id == "road":
        tags.add("road")
    if "grove" in f["site"].tags:
        tags.add("grove")
    if "river" in f["site"].tags:
        tags.add("river")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(S, M) :- sacred(S), power(M, P), P >= 2.
sensible(M)  :- machine(M), sense(M, S), sense_min(Min), S >= Min.
valid(S, P, M) :- site(S), plan(P), machine(M), hazard(S, M), sensible(M).

chooses_mercy(child, _) :- sign(_).
chooses_mercy(elder, bell).
chooses_mercy(elder, spring).

happy_outcome(R, Sg) :- relation(R), chosen_sign(Sg), chooses_mercy(R, Sg).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for site_id, site in SITES.items():
        lines.append(asp.fact("site", site_id))
        if site.sacred:
            lines.append(asp.fact("sacred", site_id))
    for plan_id in PLANS:
        lines.append(asp.fact("plan", plan_id))
    for machine_id, machine in MACHINES.items():
        lines.append(asp.fact("machine", machine_id))
        lines.append(asp.fact("power", machine_id, machine.power))
        lines.append(asp.fact("sense", machine_id, machine.sense))
    for sign_id in SIGNS:
        lines.append(asp.fact("sign", sign_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(item[0] for item in asp.atoms(model, "sensible"))


def asp_happy(relation: str, sign_id: str) -> bool:
    import asp

    extra = "\n".join([
        asp.fact("relation", relation),
        asp.fact("chosen_sign", sign_id),
    ])
    model = asp.one_model(asp_program(extra, "#show happy_outcome/2."))
    return bool(asp.atoms(model, "happy_outcome"))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sensible = set(asp_sensible())
    p_sensible = {mid for mid, machine in MACHINES.items() if sensible_machine(machine)}
    if c_sensible == p_sensible:
        print(f"OK: sensible machines match ({sorted(c_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible machines: clingo={sorted(c_sensible)} python={sorted(p_sensible)}")

    for relation in ("child", "elder"):
        for sign_id in SIGNS:
            if asp_happy(relation, sign_id) != chooses_mercy(relation, SIGNS[sign_id]):
                rc = 1
                print(f"MISMATCH in happy outcome for relation={relation} sign={sign_id}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as exc:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


CURATED = [
    StoryParams(
        site="hill_shrine",
        plan="road",
        machine="bronze_bulldozer",
        sign="bell",
        ruler_name="King Oran",
        ruler_type="king",
        witness_name="Tala",
        witness_type="girl",
        helper_name="Master Ivo",
        helper_type="man",
        relation="child",
    ),
    StoryParams(
        site="olive_grove",
        plan="market_square",
        machine="stone_ram",
        sign="owl",
        ruler_name="Queen Sera",
        ruler_type="queen",
        witness_name="Neri",
        witness_type="boy",
        helper_name="Old Daman",
        helper_type="man",
        relation="child",
    ),
    StoryParams(
        site="river_stone",
        plan="palace_gate",
        machine="bronze_bulldozer",
        sign="spring",
        ruler_name="King Teren",
        ruler_type="king",
        witness_name="Mira",
        witness_type="girl",
        helper_name="Stonehand",
        helper_type="man",
        relation="elder",
    ),
]


RULER_NAMES = {
    "king": ["King Oran", "King Teren", "King Alon", "King Brin"],
    "queen": ["Queen Sera", "Queen Elia", "Queen Maren", "Queen Thysa"],
}
CHILD_GIRLS = ["Tala", "Mira", "Lysa", "Eliya"]
CHILD_BOYS = ["Neri", "Pavo", "Ilan", "Soren"]
HELPERS = ["Master Ivo", "Old Daman", "Stonehand", "Bram"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic storyworld: a ruler wants to bulldoze a sacred place, a warning rises, and wisdom leads to a happy ending."
    )
    ap.add_argument("--site", choices=SITES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--machine", choices=MACHINES)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--relation", choices=["child", "elder"])
    ap.add_argument("--ruler", choices=["king", "queen"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.site and args.machine:
        site = SITES[args.site]
        machine = MACHINES[args.machine]
        if not (hazard_at_risk(site, machine) and sensible_machine(machine)):
            raise StoryError(explain_rejection(site, machine))
    if args.machine and not sensible_machine(MACHINES[args.machine]):
        machine = MACHINES[args.machine]
        raise StoryError(
            f"(Refusing machine '{machine.id}': it scores too low on common sense "
            f"(sense={machine.sense} < {SENSE_MIN}).)"
        )

    combos = [
        combo for combo in valid_combos()
        if (args.site is None or combo[0] == args.site)
        and (args.plan is None or combo[1] == args.plan)
        and (args.machine is None or combo[2] == args.machine)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    site_id, plan_id, machine_id = rng.choice(sorted(combos))
    relation = args.relation or rng.choice(["child", "elder"])
    ruler_type = args.ruler or rng.choice(["king", "queen"])
    ruler_name = rng.choice(RULER_NAMES[ruler_type])
    if relation == "child":
        witness_type = rng.choice(["girl", "boy"])
        witness_name = rng.choice(CHILD_GIRLS if witness_type == "girl" else CHILD_BOYS)
    else:
        witness_type = rng.choice(["woman", "man"])
        witness_name = rng.choice(["Priestess Lina", "Elder Noma"] if witness_type == "woman" else ["Keeper Arin", "Elder Savo"])
    helper_name = rng.choice(HELPERS)
    helper_type = "man"
    sign_id = args.sign or rng.choice(sorted(SIGNS))
    if not chooses_mercy(relation, SIGNS[sign_id]):
        if relation == "elder":
            sign_id = rng.choice(["bell", "spring"])
    return StoryParams(
        site=site_id,
        plan=plan_id,
        machine=machine_id,
        sign=sign_id,
        ruler_name=ruler_name,
        ruler_type=ruler_type,
        witness_name=witness_name,
        witness_type=witness_type,
        helper_name=helper_name,
        helper_type=helper_type,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.site not in SITES:
        raise StoryError(f"(Unknown site: {params.site})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")
    if params.machine not in MACHINES:
        raise StoryError(f"(Unknown machine: {params.machine})")
    if params.sign not in SIGNS:
        raise StoryError(f"(Unknown sign: {params.sign})")

    site = SITES[params.site]
    machine = MACHINES[params.machine]
    if not (hazard_at_risk(site, machine) and sensible_machine(machine)):
        raise StoryError(explain_rejection(site, machine))
    if not chooses_mercy(params.relation, SIGNS[params.sign]):
        raise StoryError("(No story: these choices do not reach the required happy ending.)")

    world = tell(
        site=site,
        plan=PLANS[params.plan],
        machine=machine,
        sign=SIGNS[params.sign],
        ruler_name=params.ruler_name,
        ruler_type=params.ruler_type,
        witness_name=params.witness_name,
        witness_type=params.witness_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        relation=params.relation,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible machines: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (site, plan, machine) combos:\n")
        for site_id, plan_id, machine_id in combos:
            print(f"  {site_id:12} {plan_id:13} {machine_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.ruler_name}: {p.machine} at {p.site} for {p.plan}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
