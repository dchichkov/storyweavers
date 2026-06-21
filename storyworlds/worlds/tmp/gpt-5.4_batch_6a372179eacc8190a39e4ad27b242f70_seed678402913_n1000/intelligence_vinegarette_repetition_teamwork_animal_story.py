#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/intelligence_vinegarette_repetition_teamwork_animal_story.py
========================================================================================

A standalone storyworld about small animals trying to open a bottle of berry
vinegarette for a picnic salad. The domain is intentionally narrow and
constraint-checked: repeated solo tries fail, a smart teamwork plan succeeds,
and the ending image shows the animals sharing the salad they made together.

The required seed words appear naturally in the story:
- intelligence
- vinegarette

Run it
------
    python storyworlds/worlds/gpt-5.4/intelligence_vinegarette_repetition_teamwork_animal_story.py
    python storyworlds/worlds/gpt-5.4/intelligence_vinegarette_repetition_teamwork_animal_story.py --host owl --bowl wooden
    python storyworlds/worlds/gpt-5.4/intelligence_vinegarette_repetition_teamwork_animal_story.py --plan pull_only
    python storyworlds/worlds/gpt-5.4/intelligence_vinegarette_repetition_teamwork_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/intelligence_vinegarette_repetition_teamwork_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/intelligence_vinegarette_repetition_teamwork_animal_story.py --verify
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
        if self.type in {"owl", "rabbit", "mouse", "hedgehog", "squirrel", "duck", "turtle", "fox"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.attrs.get("plural") else "it"


@dataclass
class Host:
    id: str
    label: str
    home: str
    opening_line: str
    closing_pose: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Bottle:
    id: str
    label: str
    phrase: str
    seal: str
    slip: str
    strength_need: int
    grip_need: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Bowl:
    id: str
    label: str
    phrase: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    sense: int
    teamwork: int
    strength: int
    grip: int
    smart: bool
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    host: str
    bottle: str
    bowl: str
    plan: str
    rabbit_name: str
    squirrel_name: str
    hedgehog_name: str
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
        return self.entities[eid]

    def animals(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_stuck_frustrates(world: World) -> list[str]:
    bottle = world.get("bottle")
    out: list[str] = []
    if bottle.meters["stuck"] < THRESHOLD:
        return out
    for animal in world.animals():
        sig = ("frustrated", animal.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        animal.memes["worry"] += 1
    return out


def _r_open_relief(world: World) -> list[str]:
    bottle = world.get("bottle")
    if bottle.meters["open"] < THRESHOLD:
        return []
    sig = ("open_relief", "group")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for animal in world.animals():
        animal.memes["relief"] += 1
        animal.memes["joy"] += 1
    bowl = world.get("bowl")
    bowl.meters["dressed"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="stuck_frustrates", tag="emotion", apply=_r_stuck_frustrates),
    Rule(name="open_relief", tag="emotion", apply=_r_open_relief),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


HOSTS = {
    "owl": Host(
        id="owl",
        label="Old Owl",
        home="a mossy stump kitchen",
        opening_line="Old Owl had invited everyone for a leaf-and-berry picnic.",
        closing_pose="Old Owl blinked proudly from the top of the stump",
        tags={"owl", "picnic"},
    ),
    "turtle": Host(
        id="turtle",
        label="Turtle Auntie",
        home="a shady patch beside the pond",
        opening_line="Turtle Auntie had spread a little cloth for a slow, happy picnic.",
        closing_pose="Turtle Auntie smiled under the shady reeds",
        tags={"turtle", "picnic"},
    ),
    "duck": Host(
        id="duck",
        label="Duck",
        home="a flat stone by the stream",
        opening_line="Duck had laid out crunchy leaves beside the sparkling water.",
        closing_pose="Duck fluffed their feathers by the stream",
        tags={"duck", "picnic"},
    ),
}

BOTTLES = {
    "berry": Bottle(
        id="berry",
        label="berry vinegarette bottle",
        phrase="a little bottle of berry vinegarette",
        seal="a cork twisted in too tight",
        slip="the glass kept slipping in small paws",
        strength_need=2,
        grip_need=2,
        tags={"vinegarette", "bottle"},
    ),
    "herb": Bottle(
        id="herb",
        label="herb vinegarette jar",
        phrase="a round jar of herb vinegarette",
        seal="a lid screwed on stubbornly",
        slip="the smooth jar tickled away whenever someone pulled",
        strength_need=2,
        grip_need=1,
        tags={"vinegarette", "jar"},
    ),
    "flower": Bottle(
        id="flower",
        label="flower-honey vinegarette flask",
        phrase="a tiny flask of flower-honey vinegarette",
        seal="a little cap stuck with dried dressing",
        slip="the neck was narrow and hard to hold still",
        strength_need=1,
        grip_need=2,
        tags={"vinegarette", "flask"},
    ),
}

BOWLS = {
    "wooden": Bowl(
        id="wooden",
        label="wooden bowl",
        phrase="a wooden bowl of torn lettuce, carrot coins, and bright berries",
        sound="tok-tok",
        tags={"salad", "wood"},
    ),
    "leaf": Bowl(
        id="leaf",
        label="leaf bowl",
        phrase="a leaf bowl filled with clover curls and radish moons",
        sound="fuff-fuff",
        tags={"salad", "leaf"},
    ),
    "stone": Bowl(
        id="stone",
        label="stone bowl",
        phrase="a cool stone bowl full of greens and little tomato halves",
        sound="tap-tap",
        tags={"salad", "stone"},
    ),
}

PLANS = {
    "brace_twist_pull": Plan(
        id="brace_twist_pull",
        sense=3,
        teamwork=3,
        strength=2,
        grip=2,
        smart=True,
        text="Rabbit braced the bottle between two smooth stones, Hedgehog held the middle steady with careful paws, and Squirrel twisted the top while everyone counted, \"One, two, three—twist!\"",
        qa_text="They braced the bottle, held it steady, and twisted together on the count of three",
        tags={"teamwork", "counting", "problem_solving"},
    ),
    "cloth_twist": Plan(
        id="cloth_twist",
        sense=3,
        teamwork=2,
        strength=2,
        grip=2,
        smart=True,
        text="Hedgehog wrapped a napkin around the slippery top, Rabbit hugged the bottle still, and Squirrel twisted with both paws while the others counted, \"One, two, three—turn!\"",
        qa_text="They used a cloth for grip while two friends held and one friend twisted",
        tags={"teamwork", "cloth", "problem_solving"},
    ),
    "tap_then_turn": Plan(
        id="tap_then_turn",
        sense=2,
        teamwork=2,
        strength=1,
        grip=2,
        smart=True,
        text="Rabbit gave the lid a gentle tap-tap with a wooden spoon, Hedgehog steadied the bottle, and Squirrel turned the top as everyone whispered, \"Again, again, now turn.\"",
        qa_text="They loosened the top with a gentle tap and then turned it together",
        tags={"teamwork", "tap", "problem_solving"},
    ),
    "pull_only": Plan(
        id="pull_only",
        sense=1,
        teamwork=1,
        strength=1,
        grip=1,
        smart=False,
        text="All three pulled at once without stopping to plan, but the bottle wriggled and nobody could get a good hold.",
        qa_text="They only pulled at the bottle without a smart plan",
        tags={"impulsive"},
    ),
}

RABBIT_NAMES = ["Pip", "Mimi", "Clover", "Dot", "Nibbles", "Poppy"]
SQUIRREL_NAMES = ["Nutmeg", "Tizzy", "Acorn", "Skip", "Hazel", "Pecan"]
HEDGEHOG_NAMES = ["Bramble", "Pin", "Thistle", "Pebble", "Quill", "Moss"]


def sensible_plans() -> list[Plan]:
    return [plan for plan in PLANS.values() if plan.sense >= SENSE_MIN]


def bottle_can_open(bottle: Bottle, plan: Plan) -> bool:
    return plan.teamwork >= 2 and plan.strength >= bottle.strength_need and plan.grip >= bottle.grip_need


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for host_id in HOSTS:
        for bottle_id, bottle in BOTTLES.items():
            for bowl_id in BOWLS:
                for plan_id, plan in PLANS.items():
                    if plan.sense >= SENSE_MIN and bottle_can_open(bottle, plan):
                        combos.append((host_id, bottle_id, bowl_id, plan_id))
    return combos


def explain_plan(plan_id: str) -> str:
    plan = PLANS[plan_id]
    better = ", ".join(sorted(p.id for p in sensible_plans()))
    return (
        f"(Refusing plan '{plan_id}': it is too weak or careless for this world "
        f"(sense={plan.sense} < {SENSE_MIN}). The animals should use a smarter teamwork plan. "
        f"Try: {better}.)"
    )


def explain_bottle_plan(bottle: Bottle, plan: Plan) -> str:
    return (
        f"(No story: {plan.id} cannot reasonably open {bottle.phrase}. "
        f"The bottle needs grip {bottle.grip_need} and strength {bottle.strength_need}, "
        f"but the plan only provides grip {plan.grip} and strength {plan.strength}.)"
    )


def predict_plan_success(world: World, plan: Plan) -> bool:
    sim = world.copy()
    bottle_cfg = sim.facts["bottle_cfg"]
    if bottle_can_open(bottle_cfg, plan):
        sim.get("bottle").meters["open"] += 1
        sim.get("bottle").meters["stuck"] = 0.0
    propagate(sim, narrate=False)
    return sim.get("bottle").meters["open"] >= THRESHOLD


def introduce(world: World, host_cfg: Host, bowl_cfg: Bowl, bottle_cfg: Bottle) -> None:
    world.say(
        f"In {host_cfg.home}, {host_cfg.opening_line} On the table waited {bowl_cfg.phrase} "
        f"and {bottle_cfg.phrase}."
    )


def meet_friends(world: World, rabbit: Entity, squirrel: Entity, hedgehog: Entity) -> None:
    for animal in (rabbit, squirrel, hedgehog):
        animal.memes["joy"] += 1
    world.say(
        f"{rabbit.id} the rabbit twitched a hopeful nose. {squirrel.id} the squirrel flicked a bright tail. "
        f"{hedgehog.id} the hedgehog patted the napkins into a neat stack."
    )


def notice_problem(world: World, bottle_cfg: Bottle) -> None:
    bottle = world.get("bottle")
    bottle.meters["stuck"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when Rabbit nudged the top, nothing moved. {bottle_cfg.seal} and {bottle_cfg.slip}."
    )
    world.say('"We need the vinegarette," Squirrel said. "Without it, the salad will taste plain."')


def solo_try_rabbit(world: World, rabbit: Entity) -> None:
    rabbit.memes["effort"] += 1
    world.facts["tries"].append("rabbit")
    world.say(
        f"{rabbit.id} tugged once. {rabbit.id} tugged twice. {rabbit.id} tugged three times, and still the top would not budge."
    )


def solo_try_squirrel(world: World, squirrel: Entity) -> None:
    squirrel.memes["effort"] += 1
    world.facts["tries"].append("squirrel")
    world.say(
        f"Then {squirrel.id} twisted once. {squirrel.id} twisted twice. {squirrel.id} twisted three times, but the bottle only squeaked in {squirrel.pronoun('possessive')} paws."
    )


def solo_try_hedgehog(world: World, hedgehog: Entity, bowl_cfg: Bowl) -> None:
    hedgehog.memes["effort"] += 1
    world.facts["tries"].append("hedgehog")
    bowl = world.get("bowl")
    bowl.meters["rattle"] += 1
    world.say(
        f"{hedgehog.id} pushed against the bottom once, then again, then once more. {bowl_cfg.sound} went the {bowl_cfg.label}, but the stubborn top stayed shut."
    )


def group_pause(world: World, host_cfg: Host) -> None:
    for animal in world.animals():
        animal.memes["think"] += 1
    world.say(
        f"The three friends sat back and looked at one another. {host_cfg.label} did not hurry them. "
        f'"Slow paws can still use quick minds," {host_cfg.label} said.'
    )


def smart_plan(world: World, plan: Plan) -> None:
    for animal in world.animals():
        animal.memes["teamwork"] += 1
    world.say(
        "Rabbit said, \"Pulling and pulling is not enough.\" "
        "Squirrel said, \"Let us use our intelligence and make a real plan.\" "
        "Hedgehog nodded."
    )
    world.say(plan.text)


def open_bottle(world: World, bottle_cfg: Bottle) -> None:
    bottle = world.get("bottle")
    bottle.meters["open"] += 1
    bottle.meters["stuck"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"Pop! At last the {bottle_cfg.label} opened, and a sweet, tangy smell floated out."
    )


def dress_salad(world: World, bowl_cfg: Bowl) -> None:
    bowl = world.get("bowl")
    bowl.meters["served"] += 1
    world.say(
        f"They poured the vinegarette over the salad and tossed it until every leaf shone."
    )
    world.say(
        f"No one said the bowl was plain now. No one said the top was too hard now. No one pulled alone now."
    )


def closing_image(world: World, host_cfg: Host) -> None:
    for animal in world.animals():
        animal.memes["pride"] += 1
    world.say(
        f"Soon crunches and happy little hums filled the air, and {host_cfg.closing_pose} while the friends shared the bright salad together."
    )


def tell(host_cfg: Host, bottle_cfg: Bottle, bowl_cfg: Bowl, plan: Plan,
         rabbit_name: str, squirrel_name: str, hedgehog_name: str) -> World:
    world = World()
    rabbit = world.add(Entity(id=rabbit_name, kind="character", type="rabbit", role="rabbit"))
    squirrel = world.add(Entity(id=squirrel_name, kind="character", type="squirrel", role="squirrel"))
    hedgehog = world.add(Entity(id=hedgehog_name, kind="character", type="hedgehog", role="hedgehog"))
    world.add(Entity(id="host", kind="character", type=host_cfg.id, label=host_cfg.label, role="host"))
    world.add(Entity(id="bottle", type="bottle", label=bottle_cfg.label, phrase=bottle_cfg.phrase, tags=set(bottle_cfg.tags)))
    world.add(Entity(id="bowl", type="bowl", label=bowl_cfg.label, phrase=bowl_cfg.phrase, tags=set(bowl_cfg.tags)))
    world.facts["host_cfg"] = host_cfg
    world.facts["bottle_cfg"] = bottle_cfg
    world.facts["bowl_cfg"] = bowl_cfg
    world.facts["plan"] = plan
    world.facts["tries"] = []

    introduce(world, host_cfg, bowl_cfg, bottle_cfg)
    meet_friends(world, rabbit, squirrel, hedgehog)

    world.para()
    notice_problem(world, bottle_cfg)
    solo_try_rabbit(world, rabbit)
    solo_try_squirrel(world, squirrel)
    solo_try_hedgehog(world, hedgehog, bowl_cfg)

    world.para()
    group_pause(world, host_cfg)
    smart_plan(world, plan)

    if not predict_plan_success(world, plan):
        raise StoryError(explain_bottle_plan(bottle_cfg, plan))

    open_bottle(world, bottle_cfg)
    dress_salad(world, bowl_cfg)

    world.para()
    closing_image(world, host_cfg)

    world.facts.update(
        rabbit=rabbit,
        squirrel=squirrel,
        hedgehog=hedgehog,
        opened=world.get("bottle").meters["open"] >= THRESHOLD,
        dressed=world.get("bowl").meters["dressed"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "vinegarette": [
        (
            "What is vinegarette?",
            "Vinegarette is a tangy dressing people pour on salad. It helps plain leaves taste brighter and more lively."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people or animals work together on the same job. One friend can do a part that helps another friend finish the rest."
        )
    ],
    "intelligence": [
        (
            "What does intelligence mean in a story like this?",
            "Intelligence means using your mind to notice what the problem really is and to choose a smart way to fix it. It is not only knowing facts; it is also thinking carefully."
        )
    ],
    "rabbit": [
        (
            "What are rabbits good at?",
            "Rabbits are good at quick hopping and noticing things around them. In stories, they are often curious and fast."
        )
    ],
    "squirrel": [
        (
            "What are squirrels good at?",
            "Squirrels are good climbers and often use nimble paws. In stories, they can be quick and clever with little objects."
        )
    ],
    "hedgehog": [
        (
            "What are hedgehogs like?",
            "Hedgehogs are small animals with spines on their backs. In stories, they are often careful and steady."
        )
    ],
    "salad": [
        (
            "Why do animals in stories share food together?",
            "Sharing food is a simple way to show friendship and peace. Eating together can prove that the problem is over."
        )
    ],
}
KNOWLEDGE_ORDER = ["vinegarette", "teamwork", "intelligence", "rabbit", "squirrel", "hedgehog", "salad"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    rabbit, squirrel, hedgehog = f["rabbit"], f["squirrel"], f["hedgehog"]
    bottle_cfg, host_cfg = f["bottle_cfg"], f["host_cfg"]
    return [
        'Write a short animal story for a 3-to-5-year-old that includes the words "intelligence" and "vinegarette".',
        f"Tell a gentle teamwork story where {rabbit.id} the rabbit, {squirrel.id} the squirrel, and {hedgehog.id} the hedgehog cannot open {bottle_cfg.phrase} until they think together.",
        f"Write an animal picnic story with repetition, where three friends try again and again, then solve the problem wisely at {host_cfg.home}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    rabbit, squirrel, hedgehog = f["rabbit"], f["squirrel"], f["hedgehog"]
    host_cfg, bottle_cfg, bowl_cfg, plan = f["host_cfg"], f["bottle_cfg"], f["bowl_cfg"], f["plan"]
    tries = f["tries"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {rabbit.id} the rabbit, {squirrel.id} the squirrel, and {hedgehog.id} the hedgehog. They were helping {host_cfg.label} get a picnic salad ready."
        ),
        (
            "What problem did the friends have?",
            f"They could not open {bottle_cfg.phrase}. The top was stuck, so the salad could not have its vinegarette yet."
        ),
        (
            "What repeated tries happened before the answer?",
            f"First {rabbit.id} pulled again and again, then {squirrel.id} twisted again and again, and then {hedgehog.id} pushed again and again. The repetition shows that trying harder in the same way was not enough."
        ),
        (
            "Why did the animals start talking about intelligence?",
            f"They saw that their paws were busy but the bottle was still shut. So they decided intelligence meant making a better plan, not just repeating the same mistake."
        ),
        (
            "How did teamwork help them open the bottle?",
            f"{plan.qa_text}. Each friend did a different job, and those jobs fit together better than any one try alone."
        ),
        (
            "How did the story end?",
            f"The bottle opened, the friends poured vinegarette over {bowl_cfg.phrase}, and everyone shared the salad together. The happy meal proves that the problem was truly solved."
        ),
    ]
    if tries:
        qa.append(
            (
                "Did one animal solve the problem alone?",
                f"No. {rabbit.id}, {squirrel.id}, and {hedgehog.id} each tried alone first, and none of those tries worked. The bottle opened only after they worked as a team."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"vinegarette", "teamwork", "intelligence", "rabbit", "squirrel", "hedgehog", "salad"}
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        host="owl",
        bottle="berry",
        bowl="wooden",
        plan="brace_twist_pull",
        rabbit_name="Pip",
        squirrel_name="Nutmeg",
        hedgehog_name="Bramble",
    ),
    StoryParams(
        host="turtle",
        bottle="herb",
        bowl="leaf",
        plan="cloth_twist",
        rabbit_name="Mimi",
        squirrel_name="Hazel",
        hedgehog_name="Pebble",
    ),
    StoryParams(
        host="duck",
        bottle="flower",
        bowl="stone",
        plan="tap_then_turn",
        rabbit_name="Clover",
        squirrel_name="Acorn",
        hedgehog_name="Thistle",
    ),
]


ASP_RULES = r"""
sensible(P) :- plan(P), sense(P, S), sense_min(M), S >= M.
opens(B, P) :- bottle(B), plan(P), teamwork(P, T), T >= 2,
               strength(P, PS), need_strength(B, BS), PS >= BS,
               grip(P, PG), need_grip(B, BG), PG >= BG.
valid(H, B, Bw, P) :- host(H), bottle(B), bowl(Bw), sensible(P), opens(B, P).

#show valid/4.
#show sensible/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for host_id in HOSTS:
        lines.append(asp.fact("host", host_id))
    for bottle_id, bottle in BOTTLES.items():
        lines.append(asp.fact("bottle", bottle_id))
        lines.append(asp.fact("need_strength", bottle_id, bottle.strength_need))
        lines.append(asp.fact("need_grip", bottle_id, bottle.grip_need))
    for bowl_id in BOWLS:
        lines.append(asp.fact("bowl", bowl_id))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("sense", plan_id, plan.sense))
        lines.append(asp.fact("teamwork", plan_id, plan.teamwork))
        lines.append(asp.fact("strength", plan_id, plan.strength))
        lines.append(asp.fact("grip", plan_id, plan.grip))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(p for (p,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: ASP gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))

    py_sensible = {p.id for p in sensible_plans()}
    asp_sense = set(asp_sensible())
    if py_sensible == asp_sense:
        print(f"OK: sensible plans match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible plans: asp={sorted(asp_sense)} python={sorted(py_sensible)}")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "vinegarette" not in sample.story or "intelligence" not in sample.story:
            rc = 1
            print("SMOKE TEST FAILED: generated story missed required seed words or was empty.")
        else:
            print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal storyworld: repeated failed tries, then smart teamwork opens a bottle of vinegarette."
    )
    ap.add_argument("--host", choices=HOSTS)
    ap.add_argument("--bottle", choices=BOTTLES)
    ap.add_argument("--bowl", choices=BOWLS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plan and PLANS[args.plan].sense < SENSE_MIN:
        raise StoryError(explain_plan(args.plan))
    if args.bottle and args.plan:
        bottle = BOTTLES[args.bottle]
        plan = PLANS[args.plan]
        if not bottle_can_open(bottle, plan):
            raise StoryError(explain_bottle_plan(bottle, plan))

    combos = [
        combo for combo in valid_combos()
        if (args.host is None or combo[0] == args.host)
        and (args.bottle is None or combo[1] == args.bottle)
        and (args.bowl is None or combo[2] == args.bowl)
        and (args.plan is None or combo[3] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    host_id, bottle_id, bowl_id, plan_id = rng.choice(sorted(combos))

    rabbit_name = rng.choice(RABBIT_NAMES)
    squirrel_name = rng.choice([n for n in SQUIRREL_NAMES if n != rabbit_name])
    hedgehog_name = rng.choice([n for n in HEDGEHOG_NAMES if n not in {rabbit_name, squirrel_name}])

    return StoryParams(
        host=host_id,
        bottle=bottle_id,
        bowl=bowl_id,
        plan=plan_id,
        rabbit_name=rabbit_name,
        squirrel_name=squirrel_name,
        hedgehog_name=hedgehog_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.host not in HOSTS:
        raise StoryError(f"(Unknown host '{params.host}'.)")
    if params.bottle not in BOTTLES:
        raise StoryError(f"(Unknown bottle '{params.bottle}'.)")
    if params.bowl not in BOWLS:
        raise StoryError(f"(Unknown bowl '{params.bowl}'.)")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan '{params.plan}'.)")

    bottle_cfg = BOTTLES[params.bottle]
    plan = PLANS[params.plan]
    if plan.sense < SENSE_MIN:
        raise StoryError(explain_plan(params.plan))
    if not bottle_can_open(bottle_cfg, plan):
        raise StoryError(explain_bottle_plan(bottle_cfg, plan))

    world = tell(
        host_cfg=HOSTS[params.host],
        bottle_cfg=bottle_cfg,
        bowl_cfg=BOWLS[params.bowl],
        plan=plan,
        rabbit_name=params.rabbit_name,
        squirrel_name=params.squirrel_name,
        hedgehog_name=params.hedgehog_name,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible plans: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (host, bottle, bowl, plan) combos:\n")
        for host_id, bottle_id, bowl_id, plan_id in combos:
            print(f"  {host_id:8} {bottle_id:8} {bowl_id:8} {plan_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.rabbit_name}, {p.squirrel_name}, and {p.hedgehog_name}: {p.bottle} at {p.host} with {p.plan}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
