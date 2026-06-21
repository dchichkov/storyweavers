#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/coast_humor_comedy.py
================================================

A standalone story world for a child-sized coast comedy: two children make a
grand seaside game, one insists on wearing a wonderfully silly hat, the coast
wind turns the hat into a runaway joke, and a grown-up helps them solve the
problem sensibly.

The world prefers a few strong, state-driven variants over broad coverage:
some hats truly catch the wind, some coast spots are breezier than others, some
ways of catching a runaway hat are sensible, and in one branch an older,
careful sibling talks the younger child into tying the hat down before the
funny disaster happens at all.

Run it
------
    python storyworlds/worlds/gpt-5.4/coast_humor_comedy.py
    python storyworlds/worlds/gpt-5.4/coast_humor_comedy.py --theme parade --spot beach --hat paper_crown
    python storyworlds/worlds/gpt-5.4/coast_humor_comedy.py --hat swim_cap
    python storyworlds/worlds/gpt-5.4/coast_humor_comedy.py --response stomp
    python storyworlds/worlds/gpt-5.4/coast_humor_comedy.py --all
    python storyworlds/worlds/gpt-5.4/coast_humor_comedy.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/coast_humor_comedy.py --qa --json
    python storyworlds/worlds/gpt-5.4/coast_humor_comedy.py --verify
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    catches_wind: bool = False
    can_help: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    title_a: str
    title_b: str
    goal: str
    ending: str


@dataclass
class CoastSpot:
    id: str
    label: str
    phrase: str
    detail: str
    gust: int
    water_edge: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hat:
    id: str
    label: str
    phrase: str
    catch: int
    comic_line: str
    safe_fix: str
    risky: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_runaway(world: World) -> list[str]:
    out: list[str] = []
    hat = world.entities.get("hat")
    if hat is None or hat.meters["flying"] < THRESHOLD:
        return out
    sig = ("runaway", "hat")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["surprise"] += 1
        kid.memes["laughter"] += 1
    if "shore" in world.entities:
        world.get("shore").meters["risk"] += 1
    out.append("__runaway__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="runaway", tag="physical", apply=_r_runaway),
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


def hazard_at_risk(spot: CoastSpot, hat: Hat) -> bool:
    return spot.gust >= 2 and hat.risky and hat.catch > 0


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def gust_severity(spot: CoastSpot, hat: Hat, delay: int) -> int:
    return spot.gust + hat.catch + delay - 1


def is_caught(response: Response, spot: CoastSpot, hat: Hat, delay: int) -> bool:
    return response.power >= gust_severity(spot, hat, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_runaway(world: World) -> dict:
    sim = world.copy()
    hat = sim.get("hat")
    hat.meters["flying"] += 1
    propagate(sim, narrate=False)
    return {
        "runaway": hat.meters["flying"] >= THRESHOLD,
        "risk": sim.get("shore").meters["risk"],
    }


def play_setup(world: World, a: Entity, b: Entity, theme: Theme, spot: CoastSpot) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a bright day at the coast, {a.id} and {b.id} turned {spot.phrase} into "
        f"{theme.scene}. {theme.rig}"
    )
    world.say(
        f"{spot.detail} "
        f'"{theme.title_a} {a.id} and {theme.title_b} {b.id}!" {a.id} said. '
        f'"Today we reach {theme.goal}."'
    )


def crown_hat(world: World, a: Entity, hat: Hat) -> None:
    a.memes["pride"] += 1
    world.say(
        f"To make the game feel extra grand, {a.id} put on {hat.phrase}. "
        f"{hat.comic_line}"
    )


def feel_wind(world: World, b: Entity, spot: CoastSpot) -> None:
    world.say(
        f"Then a coast breeze came skipping along {spot.label}, tugging at towels "
        f"and making the air taste like salt."
    )
    world.say(f'{b.id} squinted up at the fluttering brim. "That wind is busy today," {b.pronoun()} said.')


def tempt(world: World, a: Entity, hat: Hat) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} grinned. "Busy wind or not, I need {hat.the}. A grand game needs a grand hat."'
    )


def warn(world: World, b: Entity, a: Entity, hat: Hat, parent: Entity) -> None:
    pred = predict_runaway(world)
    world.facts["predicted_risk"] = pred["risk"]
    b.memes["caution"] += 1
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.pronoun().capitalize()} was already picturing everyone running after it."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, tie it first. '
        f'{parent.label_word.capitalize()} said coast wind loves loose hats, and that one could zip away."{extra}'
    )


def back_down(world: World, a: Entity, b: Entity, hat: Hat, theme: Theme) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked at {hat.the}, looked at the dancing breeze, and laughed first. '
        f'"All right," {a.pronoun()} said. "I do not want to chase my own hat down the coast."'
    )
    world.say(
        f"They tied {hat.safe_fix}, and from then on the hat stayed put, bobbing politely while "
        f"the game marched on toward {theme.goal}."
    )


def defy(world: World, a: Entity, b: Entity, hat: Hat) -> None:
    a.memes["defiance"] += 1
    if a.attrs.get("relation") == "siblings" and a.age > b.age:
        world.say(
            f'"Do not fuss," {a.id} said. "I am the big one, and {hat.the} likes me." '
            f"That turned out not to be true."
        )
    else:
        world.say(
            f'"Do not fuss," {a.id} said. "{hat.the.capitalize()} knows who it belongs to." '
            f"That turned out not to be true."
        )


def gust(world: World, hat_ent: Entity, hat: Hat, spot: CoastSpot) -> None:
    hat_ent.meters["flying"] += 1
    hat_ent.meters["lostness"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The very next gust puffed under {hat.the} and lifted it right off {world.get('instigator').id}'s head. "
        f"It cartwheeled across {spot.label} like a silly pancake with ambition."
    )
    world.say(
        f"It bounced past a bucket, startled a crab, and headed for {spot.water_edge}."
    )


def chase(world: World, a: Entity, b: Entity, hat: Hat) -> None:
    a.memes["fear"] += 1
    a.memes["laughter"] += 1
    b.memes["laughter"] += 1
    world.say(f'"My hat!" {a.id} yelped, already laughing and running after {hat.pronoun("object") if False else "it"}.')
    world.say(f"{b.id} ran too, with knees pumping and giggles wobbling all over the words.")


def rescue(world: World, parent: Entity, response: Response, hat_ent: Entity, hat: Hat) -> None:
    hat_ent.meters["flying"] = 0.0
    hat_ent.meters["saved"] += 1
    world.get("shore").meters["risk"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} stepped in just in time and {response.text.replace('{hat}', hat.label)}."
    )
    world.say(
        f"In one more second, the runaway hat would have gone splashing off without its owner."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, hat: Hat) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f'{parent.label_word.capitalize()} handed {hat.the} back and smiled instead of scolding. '
        f'"Funny hats are welcome," {parent.pronoun()} said, "but at the coast they need help staying put."'
    )
    world.say(
        f'{a.id} nodded. "{hat.the.capitalize()} is brave," {a.pronoun()} said, "but not as brave as the wind."'
    )


def safer_ending(world: World, a: Entity, b: Entity, hat: Hat, theme: Theme) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"After that, they tied {hat.safe_fix}. The hat still bobbed and flapped, "
        f"but now it stayed with its own head."
    )
    world.say(
        f"Then the two friends went on with {theme.ending}, and every time the brim wiggled, "
        f"they laughed before marching on."
    )


def rescue_fail(world: World, parent: Entity, response: Response, hat_ent: Entity, hat: Hat, spot: CoastSpot) -> None:
    hat_ent.meters["flying"] += 1
    hat_ent.meters["wet"] += 1
    world.get("shore").meters["risk"] += 1
    world.say(
        f"{parent.label_word.capitalize()} {response.fail.replace('{hat}', hat.label)}."
    )
    world.say(
        f"But the gust was quicker. {hat.the.capitalize()} skipped once on a rock, then plopped into the water by {spot.water_edge}."
    )


def soggy_end(world: World, parent: Entity, a: Entity, b: Entity, hat: Hat, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["sad"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"{parent.label_word.capitalize()} fished the hat out at last, dripping and droopy like a tired jelly pancake."
    )
    world.say(
        f"{a.id} sighed, but even {a.pronoun()} had to laugh at how small and soggy it looked. "
        f"After that, they finished {theme.ending} with no hat at all and a much better plan for windy days."
    )


def tell(
    theme: Theme,
    spot: CoastSpot,
    hat: Hat,
    response: Response,
    instigator: str = "Max",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    trait: str = "careful",
    parent_type: str = "mother",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
) -> World:
    world = World()
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation},
        traits=["bold"],
    ))
    a.id = instigator
    world.entities[instigator] = world.entities.pop("instigator")
    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner,
        role="cautioner",
        age=cautioner_age,
        attrs={"relation": relation},
        traits=[trait],
    ))
    b.id = cautioner
    world.entities[cautioner] = world.entities.pop("cautioner")
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    shore = world.add(Entity(id="shore", type="place", label=spot.label))
    hat_ent = world.add(Entity(
        id="hat",
        type="hat",
        label=hat.label,
        phrase=hat.phrase,
        catches_wind=hat.risky,
        tags=set(hat.tags),
    ))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)

    play_setup(world, a, b, theme, spot)
    crown_hat(world, a, hat)
    feel_wind(world, b, spot)

    world.para()
    tempt(world, a, hat)
    warn(world, b, a, hat, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, hat, theme)
        world.para()
        safer_ending(world, a, b, hat, theme)
        contained = True
        severity = 0
    else:
        defy(world, a, b, hat)
        world.para()
        gust(world, hat_ent, hat, spot)
        chase(world, a, b, hat)
        severity = gust_severity(spot, hat, delay)
        contained = is_caught(response, spot, hat, delay)
        world.para()
        if contained:
            rescue(world, parent, response, hat_ent, hat)
            lesson(world, parent, a, b, hat)
            world.para()
            safer_ending(world, a, b, hat, theme)
        else:
            rescue_fail(world, parent, response, hat_ent, hat, spot)
            soggy_end(world, parent, a, b, hat, theme)

    outcome = "averted" if averted else ("caught" if contained else "soaked")
    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        theme=theme,
        spot=spot,
        hat_cfg=hat,
        hat=hat_ent,
        response=response,
        relation=relation,
        delay=delay,
        severity=severity,
        outcome=outcome,
        escaped=not averted,
    )
    return world


THEMES = {
    "parade": Theme(
        id="parade",
        scene="a royal coast parade",
        rig="A driftwood stick became a baton, a bucket became the grand drum, and every shell on the sand looked like part of the crowd.",
        title_a="Marshal",
        title_b="Captain",
        goal="the cheering finish line by the dunes",
        ending="their parade along the shore",
    ),
    "cafe": Theme(
        id="cafe",
        scene="the fanciest snack café on the coast",
        rig="A flat rock became the counter, shells became tiny plates, and a gull-shaped cloud looked almost like the first customer.",
        title_a="Chef",
        title_b="Server",
        goal="the grand opening",
        ending="their seaside café game",
    ),
    "band": Theme(
        id="band",
        scene="a coast marching band",
        rig="A pail became the drum, two shells became cymbals, and a long piece of seaweed was declared a very serious ribbon.",
        title_a="Leader",
        title_b="Drummer",
        goal="the loudest song on the beach",
        ending="their band all the way down the sand",
    ),
}

SPOTS = {
    "beach": CoastSpot(
        id="beach",
        label="the beach",
        phrase="the beach",
        detail="The waves kept clapping at the shore as if they were an audience.",
        gust=2,
        water_edge="the foamy edge of the waves",
        tags={"coast", "wind", "beach"},
    ),
    "cliff_path": CoastSpot(
        id="cliff_path",
        label="the cliff path",
        phrase="the cliff path above the coast",
        detail="Far below, the sea flashed silver, and the wind ran around with no manners at all.",
        gust=3,
        water_edge="the tide pool below the path",
        tags={"coast", "wind", "cliff"},
    ),
    "harbor_walk": CoastSpot(
        id="harbor_walk",
        label="the harbor walk",
        phrase="the harbor walk by the coast",
        detail="Ropes tapped the masts, and the breeze darted between the boats like it had important news.",
        gust=2,
        water_edge="the little harbor steps",
        tags={"coast", "wind", "harbor"},
    ),
    "sheltered_cove": CoastSpot(
        id="sheltered_cove",
        label="the sheltered cove",
        phrase="the sheltered cove on the coast",
        detail="The rocks made a quiet pocket where even the gulls seemed sleepy.",
        gust=1,
        water_edge="the gentle water",
        tags={"coast", "cove"},
    ),
}

HATS = {
    "floppy_sunhat": Hat(
        id="floppy_sunhat",
        label="floppy sunhat",
        phrase="a floppy sunhat with a brim like a yellow pancake",
        catch=2,
        comic_line="It made the top half of the child look important and the bottom half look surprised.",
        safe_fix="the little chin ribbon under it",
        risky=True,
        tags={"hat", "wind"},
    ),
    "paper_crown": Hat(
        id="paper_crown",
        label="paper crown",
        phrase="a paper crown with three wiggly points",
        catch=3,
        comic_line="Every point quivered as if it were trying to think its own thoughts.",
        safe_fix="a soft band around the paper crown",
        risky=True,
        tags={"hat", "paper", "wind"},
    ),
    "captain_hat": Hat(
        id="captain_hat",
        label="captain hat",
        phrase="a captain hat with a shiny button at the front",
        catch=1,
        comic_line="The shiny button winked so proudly that even the sand seemed impressed.",
        safe_fix="the snug strap at the back",
        risky=True,
        tags={"hat", "wind"},
    ),
    "swim_cap": Hat(
        id="swim_cap",
        label="swim cap",
        phrase="a snug swim cap",
        catch=0,
        comic_line="It sat there so firmly that even a frown would have had trouble moving it.",
        safe_fix="nothing at all, because it already fit perfectly",
        risky=False,
        tags={"cap"},
    ),
}

RESPONSES = {
    "net": Response(
        id="net",
        sense=3,
        power=5,
        text="scooped the {hat} out of the air with the long beach net",
        fail="swung the beach net at the {hat}, but the gust skipped it past the rim",
        qa_text="caught the hat with a long beach net",
        tags={"net", "wind"},
    ),
    "towel_trap": Response(
        id="towel_trap",
        sense=3,
        power=4,
        text="spread a towel wide and trapped the {hat} neatly against the sand",
        fail="threw a towel at the {hat}, but the breeze only made it dance higher",
        qa_text="trapped the hat with a wide towel",
        tags={"towel", "wind"},
    ),
    "hand_grab": Response(
        id="hand_grab",
        sense=2,
        power=3,
        text="took two quick steps and grabbed the {hat} before it reached the water",
        fail="lunged for the {hat}, but the wind whisked it just past those fingers",
        qa_text="grabbed the hat by hand before it reached the water",
        tags={"grab", "wind"},
    ),
    "stomp": Response(
        id="stomp",
        sense=1,
        power=2,
        text="stamped on the {hat}",
        fail="tried to stomp on the {hat}, but that only puffed it farther away",
        qa_text="stamped on the hat",
        tags={"stomp", "wind"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "cautious", "thoughtful", "sensible", "curious", "cheerful"]


@dataclass
class StoryParams:
    theme: str
    spot: str
    hat: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme in THEMES:
        for spot_id, spot in SPOTS.items():
            for hat_id, hat in HATS.items():
                if hazard_at_risk(spot, hat):
                    combos.append((theme, spot_id, hat_id))
    return combos


KNOWLEDGE = {
    "coast": [(
        "What is a coast?",
        "A coast is the place where land meets the sea. You can find beaches, rocks, and windy paths there."
    )],
    "wind": [(
        "Why can wind carry things away?",
        "Wind is moving air, and when it pushes on light, loose things, it can slide or lift them. Hats, paper, and towels can all skitter away."
    )],
    "hat": [(
        "Why do some hats blow off more easily than others?",
        "Loose hats and hats with wide brims catch more wind, so the air can push under them. A snug hat stays on better because the wind has less to grab."
    )],
    "paper": [(
        "Why is paper bad in strong wind?",
        "Paper is light and easy to push around, so wind can bend it, flap it, and carry it away. That is why paper crowns are funny but not very sturdy."
    )],
    "net": [(
        "What is a net good for?",
        "A net is good for scooping or catching something without squeezing it too hard. It can help catch a runaway thing quickly."
    )],
    "towel": [(
        "How can a towel stop something from blowing away?",
        "A wide towel can cover a light object and press it to the ground. Once the wind cannot get under it, the object stops skittering."
    )],
}
KNOWLEDGE_ORDER = ["coast", "wind", "hat", "paper", "net", "towel"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    theme = f["theme"]
    hat = f["hat_cfg"]
    spot = f["spot"]
    outcome = f["outcome"]
    base = (
        f'Write a funny seaside story for a 3-to-5-year-old set on the coast, where children play a big pretend game and a silly hat meets a windy problem. Include the word "coast".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle comedy where {a.id} wants to wear {hat.the}, but {b.id} convinces {a.pronoun('object')} to tie it first, so the game stays funny and nobody has to chase anything.",
            f'Write a child-facing story about a careful older sibling stopping a hat disaster before it starts on {spot.label}.'
        ]
    if outcome == "soaked":
        return [
            base,
            f"Tell a coast comedy where {a.id} ignores a warning about {hat.the}, the wind runs off with it, and the hat ends up soggy by the sea.",
            f"Write a funny-but-cautionary story where a grand game on {spot.label} is interrupted by a runaway hat that cannot quite be saved in time."
        ]
    return [
        base,
        f"Tell a comedy where {a.id} ignores a warning about {hat.the}, the coast wind steals it, and a calm grown-up catches it just in time.",
        f"Write a playful story with a big gust, a runaway hat, and a happy ending where the children learn a smarter way to keep playing."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    theme = f["theme"]
    spot = f["spot"]
    hat = f["hat_cfg"]
    response = f["response"]
    relation = f["relation"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b, relation)}, {a.id} and {b.id}, playing a big game at the coast. {a.id}'s {parent.label_word} also helps when the windy trouble begins."
        ),
        (
            "What were the children pretending?",
            f"They turned {spot.phrase} into {theme.scene}. The pretend game made the hat feel extra important, which is why {a.id} wanted to keep wearing it."
        ),
        (
            f"Why did {b.id} warn {a.id} about the hat?",
            f"{b.id} saw the coast wind picking up and knew {hat.the} was loose enough to fly away. The warning came before the trouble, because the breeze was already tugging at it."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What did {a.id} do after the warning?",
            f"{a.id} laughed and changed course, then tied {hat.safe_fix}. That let the game stay funny without turning into a chase down the coast."
        ))
        qa.append((
            "How did the story end?",
            f"It ended safely and cheerfully. The hat stayed put, and the children went on with {theme.ending} instead of running after runaway clothes."
        ))
    elif f["outcome"] == "caught":
        qa.append((
            "What happened when the gust came?",
            f"The wind lifted {hat.the} right off {a.id}'s head and sent it cartwheeling toward the water. The funny part is that it looked almost alive, but the danger was that it could be lost."
        ))
        qa.append((
            f"How did {a.id}'s {parent.label_word} help?",
            f"{parent.label_word.capitalize()} {response.qa_text}. That quick move stopped the runaway hat before it reached the sea."
        ))
        qa.append((
            "What changed at the end?",
            f"After the rescue, they tied {hat.safe_fix} and kept playing. The same hat was still part of the joke, but now it was under control."
        ))
    else:
        qa.append((
            f"Could {a.id}'s {parent.label_word} save the hat in time?",
            f"No. {parent.label_word.capitalize()} tried, but the gust beat everyone to the water. The hat was recovered later, though it came back soggy and floppy."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with a wet, droopy hat and a better idea for next time. The children still finished {theme.ending}, but now they understood that coast wind can turn a joke into a chase very fast."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["spot"].tags) | set(f["hat_cfg"].tags)
    if f["outcome"] == "caught":
        tags |= set(f["response"].tags)
    out: list[tuple[str, str]] = []
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.catches_wind:
            bits.append("catches_wind=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="parade",
        spot="beach",
        hat="paper_crown",
        response="net",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
    ),
    StoryParams(
        theme="cafe",
        spot="harbor_walk",
        hat="floppy_sunhat",
        response="towel_trap",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="father",
        trait="curious",
        delay=0,
        instigator_age=5,
        cautioner_age=5,
        relation="friends",
    ),
    StoryParams(
        theme="band",
        spot="cliff_path",
        hat="paper_crown",
        response="hand_grab",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        parent="mother",
        trait="thoughtful",
        delay=1,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
    ),
    StoryParams(
        theme="parade",
        spot="harbor_walk",
        hat="captain_hat",
        response="net",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Theo",
        cautioner_gender="boy",
        parent="father",
        trait="careful",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
    ),
]


def explain_rejection(spot: CoastSpot, hat: Hat) -> str:
    if spot.gust < 2:
        return (
            f"(No story: {spot.label} is too sheltered for a runaway-hat problem. "
            f"The breeze there is too gentle to carry {hat.the} off, so the comedy turn never happens.)"
        )
    if not hat.risky or hat.catch <= 0:
        return (
            f"(No story: {hat.phrase} fits too snugly to blow away. "
            f"This world needs a hat the coast wind can actually grab.)"
        )
    return "(No story: this spot and hat do not make a runaway-hat problem.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a more sensible catch like {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "caught" if is_caught(RESPONSES[params.response], SPOTS[params.spot], HATS[params.hat], params.delay) else "soaked"


ASP_RULES = r"""
hazard(S, H) :- gusty(S), risky_hat(H).
valid(T, S, H) :- theme(T), spot(S), hat(H), hazard(S, H).

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

severity(G + C + D - 1) :- chosen_spot(S), gust(S, G), chosen_hat(H), catch(H, C), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
caught :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(caught) :- not averted, caught.
outcome(soaked) :- not averted, not caught.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        lines.append(asp.fact("gust", sid, spot.gust))
        if spot.gust >= 2:
            lines.append(asp.fact("gusty", sid))
    for hid, hat in HATS.items():
        lines.append(asp.fact("hat", hid))
        lines.append(asp.fact("catch", hid, hat.catch))
        if hat.risky and hat.catch > 0:
            lines.append(asp.fact("risky_hat", hid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for t in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", t))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_spot", params.spot),
        asp.fact("chosen_hat", params.hat),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(s)))
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a windy coast comedy about a runaway hat."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--hat", choices=HATS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spot and args.hat:
        spot = SPOTS[args.spot]
        hat = HATS[args.hat]
        if not hazard_at_risk(spot, hat):
            raise StoryError(explain_rejection(spot, hat))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.spot is None or c[1] == args.spot)
        and (args.hat is None or c[2] == args.hat)
    ]
    if not combos:
        if args.spot and args.hat:
            raise StoryError(explain_rejection(SPOTS[args.spot], HATS[args.hat]))
        raise StoryError("(No valid combination matches the given options.)")

    theme, spot, hat = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    return StoryParams(
        theme=theme,
        spot=spot,
        hat=hat,
        response=response,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.hat not in HATS:
        raise StoryError(f"(Unknown hat: {params.hat})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not hazard_at_risk(SPOTS[params.spot], HATS[params.hat]):
        raise StoryError(explain_rejection(SPOTS[params.spot], HATS[params.hat]))

    world = tell(
        theme=THEMES[params.theme],
        spot=SPOTS[params.spot],
        hat=HATS[params.hat],
        response=RESPONSES[params.response],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        parent_type=params.parent,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
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
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, spot, hat) combos:\n")
        for theme, spot, hat in combos:
            print(f"  {theme:8} {spot:14} {hat}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.instigator} & {p.cautioner}: {p.hat} at {p.spot} ({p.theme}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
