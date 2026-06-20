#!/usr/bin/env python3
"""A folk-tale mystery in an indoor gym with a shiny street and a wobbly wagon.

Seed:
    Words: shiny street, wobbly wagon
    Setting: indoor gym
    Features: Mystery to Solve
    Style: Folk Tale

Internal source tale:
    On a rainy feast night, villagers carry their small procession into an
    indoor gym and lay down a shiny street across the floor. A child is asked
    to watch a treasured festival token resting on a wobbly wagon. When the
    token vanishes, the child is tempted to blame an unseen thief, but careful
    reading of the room shows a physical cause: the wagon's fault tossed the
    token into a nearby hiding place. An elder repairs the true cause, and the
    ending image proves the world changed because the wagon rolls straight and
    the procession can begin.
"""

from __future__ import annotations

import argparse
import copy
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class Street:
    id: str
    label: str
    description: str
    reveal_problems: tuple[str, ...]
    ending_image: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class Token:
    id: str
    label: str
    role: str
    risks: tuple[str, ...]
    material: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class Problem:
    id: str
    label: str
    clue_text: str
    hiding_place: str
    truth_text: str
    repair_skill: str
    risk_text: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class Guide:
    id: str
    name: str
    role: str
    repair_skill: str
    repair_text: str
    proverb: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class Hero:
    id: str
    name: str
    kind: str
    trait: str


@dataclass(frozen=True)
class StoryParams:
    street: str
    token: str
    problem: str
    guide: str
    hero: str
    seed: int = 0


@dataclass
class Entity:
    id: str
    name: str
    kind: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: tuple[str, ...] = ()


@dataclass
class Event:
    id: str
    text: str
    subject: str
    target: str | None = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class GymWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add_entity(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, sentence: str) -> None:
        sentence = sentence.strip()
        if sentence:
            self.paragraphs[-1].append(sentence)

    def break_paragraph(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(block) for block in self.paragraphs if block)

    def record(
        self,
        event_id: str,
        text: str,
        subject: str,
        target: str | None = None,
        *,
        meter_delta: dict[str, tuple[str, float]] | None = None,
        meme_delta: dict[str, tuple[str, float]] | None = None,
    ) -> None:
        meter_delta = meter_delta or {}
        meme_delta = meme_delta or {}
        self.history.append(
            Event(
                id=event_id,
                text=text,
                subject=subject,
                target=target,
                meters={k: v for k, (_, v) in meter_delta.items()},
                memes={k: v for k, (_, v) in meme_delta.items()},
            )
        )
        for key, (entity_id, delta) in meter_delta.items():
            entity = self.get(entity_id)
            entity.meters[key] = entity.meters.get(key, 0.0) + delta
        for key, (entity_id, delta) in meme_delta.items():
            entity = self.get(entity_id)
            entity.memes[key] = entity.memes.get(key, 0.0) + delta

    def trace(self) -> str:
        lines = [
            f"street={self.params.street}",
            f"token={self.params.token}",
            f"problem={self.params.problem}",
            f"guide={self.params.guide}",
            f"hero={self.params.hero}",
        ]
        for event in self.history:
            lines.append(f"event {event.id}: {event.text}")
        for entity in self.entities.values():
            lines.append(f"{entity.id}: {entity.name} | {entity.kind} | location={entity.location}")
            lines.append(f"  meters={entity.meters}")
            lines.append(f"  memes={entity.memes}")
        return "\n".join(lines)


STREETS = {
    "mirror_lane": Street(
        id="mirror_lane",
        label="mirror lane",
        description="a shiny street of mirror-paper tiles running between rope ladders and folded blue mats",
        reveal_problems=("latch_slip", "wheel_wrap"),
        ending_image="The mirror tiles held the lamplight so gently that the path looked like a river made for dancing feet.",
        tags=("street", "mirror", "gym"),
    ),
    "brass_path": Street(
        id="brass_path",
        label="brass path",
        description="a shiny street of brass-bright tape curving from the wall bars to the hoop arch",
        reveal_problems=("chalk_ridge", "latch_slip"),
        ending_image="The brass path lay smooth beneath the rafters, bright as if it remembered every step it had promised to carry.",
        tags=("street", "brass", "gym"),
    ),
    "foil_road": Street(
        id="foil_road",
        label="foil road",
        description="a shiny street of silver foil stars pressed along the waxed floor toward the drum stand",
        reveal_problems=("wheel_wrap", "chalk_ridge"),
        ending_image="The foil stars shone in one true line, and even the high rings seemed to watch them with quiet approval.",
        tags=("street", "foil", "gym"),
    ),
}


TOKENS = {
    "sun_medal": Token(
        id="sun_medal",
        label="the sun medal",
        role="the bright medal that should hang at the wagon's front bow",
        risks=("latch_slip", "chalk_ridge"),
        material="brass",
        tags=("token", "metal", "festival"),
    ),
    "reed_whistle": Token(
        id="reed_whistle",
        label="the reed whistle",
        role="the whistle that should sing when the first march begins",
        risks=("wheel_wrap", "latch_slip"),
        material="reed",
        tags=("token", "music", "festival"),
    ),
    "dawn_ribbon": Token(
        id="dawn_ribbon",
        label="the dawn ribbon",
        role="the long ribbon that should flutter above the children at the start",
        risks=("wheel_wrap", "chalk_ridge"),
        material="silk",
        tags=("token", "cloth", "festival"),
    ),
}


PROBLEMS = {
    "latch_slip": Problem(
        id="latch_slip",
        label="a loosened side latch",
        clue_text="A tiny brass tongue glittered by the springboard, and beside it a line of dust marks led under the folded blue mat.",
        hiding_place="the pocket beneath the folded blue mat",
        truth_text="The side latch had slipped loose, so the wagon's box gaped open and tossed the token under the mat when the wagon shivered.",
        repair_skill="latch",
        risk_text="the wagon would keep spilling its burden whenever it rattled over the gym floor",
        tags=("wagon", "metal", "clue"),
    ),
    "chalk_ridge": Problem(
        id="chalk_ridge",
        label="a chalk ridge across the road",
        clue_text="A white curl of chalk crossed the road near the hoop arch, and the wheel line bent away from it toward the bench of beanbags.",
        hiding_place="the beanbag bench",
        truth_text="A ridge of chalk had nudged one wheel aside, and the sudden tilt slid the token onto the beanbag bench instead of leaving it on the wagon.",
        repair_skill="smooth",
        risk_text="the wagon would lurch again before the procession reached the arch",
        tags=("wagon", "chalk", "clue"),
    ),
    "wheel_wrap": Problem(
        id="wheel_wrap",
        label="a frayed wheel wrap",
        clue_text="A strip of red cloth dragged beside the wheel, and a soft trail pointed behind the drum stand where something light had settled.",
        hiding_place="the space behind the drum stand",
        truth_text="The wrap around the wheel had frayed loose, and the wobble flung the token behind the drum stand when the wagon lurched.",
        repair_skill="bind",
        risk_text="the wagon would wobble harder with each turn until someone stumbled after it",
        tags=("wagon", "cloth", "clue"),
    ),
}


GUIDES = {
    "vesna": Guide(
        id="vesna",
        name="Aunt Vesna",
        role="the keeper of feast boxes",
        repair_skill="latch",
        repair_text="Aunt Vesna pressed the latch flat, set a small wooden pin through it, and tested the side of the wagon until it no longer sighed open.",
        proverb="When a thing is lost, ask first what the floor has witnessed.",
        tags=("elder", "repair", "wagon"),
    ),
    "bojan": Guide(
        id="bojan",
        name="Old Bojan",
        role="the chalk sweeper of the winter games",
        repair_skill="smooth",
        repair_text="Old Bojan brushed the chalk ridge away with careful strokes and rubbed the lane smooth with a folded towel.",
        proverb="A crooked mark on the road can tell a straighter tale than frightened tongues.",
        tags=("elder", "repair", "chalk"),
    ),
    "rina": Guide(
        id="rina",
        name="Grandmother Rina",
        role="the ribbon binder of feast mornings",
        repair_skill="bind",
        repair_text="Grandmother Rina wrapped the wheel with fresh red cloth and tied it snugly so the rim could grip the floor instead of skittering across it.",
        proverb="A patient hand hears what a shaking wheel is trying to say.",
        tags=("elder", "repair", "cloth"),
    ),
}


HEROES = {
    "luka": Hero(id="luka", name="Luka", kind="boy", trait="watchful"),
    "mira": Hero(id="mira", name="Mira", kind="girl", trait="gentle-eyed"),
    "teo": Hero(id="teo", name="Teo", kind="boy", trait="steady-hearted"),
}


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.street not in STREETS:
        return False, f"unknown street: {params.street}"
    if params.token not in TOKENS:
        return False, f"unknown token: {params.token}"
    if params.problem not in PROBLEMS:
        return False, f"unknown problem: {params.problem}"
    if params.guide not in GUIDES:
        return False, f"unknown guide: {params.guide}"
    if params.hero not in HEROES:
        return False, f"unknown hero: {params.hero}"

    street = STREETS[params.street]
    token = TOKENS[params.token]
    problem = PROBLEMS[params.problem]
    guide = GUIDES[params.guide]

    if params.problem not in street.reveal_problems:
        return False, f"{street.label} does not leave a fair clue trail for {problem.label}"
    if params.problem not in token.risks:
        return False, f"{problem.label} cannot plausibly hide {token.label}"
    if guide.repair_skill != problem.repair_skill:
        return False, f"{guide.name} cannot repair {problem.label}"
    return True, ""


def all_params() -> list[StoryParams]:
    combos: list[StoryParams] = []
    for street in sorted(STREETS):
        for token in sorted(TOKENS):
            for problem in sorted(PROBLEMS):
                for guide in sorted(GUIDES):
                    for hero in sorted(HEROES):
                        params = StoryParams(street, token, problem, guide, hero)
                        if valid_params(params)[0]:
                            combos.append(params)
    return combos


def build_world(params: StoryParams) -> GymWorld:
    street = STREETS[params.street]
    token = TOKENS[params.token]
    problem = PROBLEMS[params.problem]
    guide = GUIDES[params.guide]
    hero = HEROES[params.hero]

    world = GymWorld(params=params)
    world.add_entity(
        Entity(
            id="gym",
            name="the indoor gym",
            kind="place",
            location="rainy village school",
            meters={"echo": 2.0, "lamplight": 2.0},
            memes={"shelter": 2.0, "ritual": 2.0},
            tags=("gym", "place"),
        )
    )
    world.add_entity(
        Entity(
            id="street",
            name=street.label,
            kind="road",
            location="gym floor",
            meters={"shine": 3.0, "clarity": 2.0},
            memes={"promise": 2.0},
            tags=street.tags,
        )
    )
    world.add_entity(
        Entity(
            id="wagon",
            name="the wobbly wagon",
            kind="wagon",
            location="head of the street",
            meters={"stability": 1.0, "wobble": 3.0, "safety": 1.0},
            memes={"trouble": 2.0},
            tags=("wagon", "physical"),
        )
    )
    world.add_entity(
        Entity(
            id="token",
            name=token.label,
            kind="festival token",
            location="wagon bow",
            meters={"hiddenness": 0.0, "readiness": 1.0},
            memes={"importance": 3.0},
            tags=token.tags,
        )
    )
    world.add_entity(
        Entity(
            id="hero",
            name=hero.name,
            kind=hero.kind,
            location="gym floor",
            meters={"clues_seen": 0.0, "steps": 0.0},
            memes={"curiosity": 2.0, "worry": 1.0, "relief": 0.0, "patience": 1.0},
            tags=("hero", hero.trait),
        )
    )
    world.add_entity(
        Entity(
            id="guide",
            name=guide.name,
            kind=guide.role,
            location="wagon side",
            meters={"repairs": 0.0},
            memes={"wisdom": 2.0, "calm": 2.0},
            tags=guide.tags,
        )
    )
    world.facts["street_description"] = street.description
    world.facts["mystery"] = f"Where had {token.label} gone when no one saw a thief?"
    world.facts["risk"] = problem.risk_text
    world.facts["hiding_place"] = problem.hiding_place
    world.facts["truth"] = problem.truth_text
    world.facts["repair"] = guide.repair_text
    world.facts["proverb"] = guide.proverb
    world.facts["ending_image"] = street.ending_image
    world.facts["token_role"] = token.role
    world.facts["token_material"] = token.material
    return world


def lower_lead(text: str) -> str:
    if not text:
        return text
    return text[:1].lower() + text[1:]


def opening(world: GymWorld) -> None:
    hero = HEROES[world.params.hero]
    token = TOKENS[world.params.token]
    text = (
        f"On the night when rain chased the feast indoors, the villagers gathered in the indoor gym and made a shiny street from lamps and careful hands. "
        f"It ran as {world.facts['street_description']}, and {hero.name}, a {hero.trait} child, was asked to watch {token.role}."
    )
    world.record(
        "opening",
        text,
        "gym",
        "hero",
        meter_delta={"steps": ("hero", 1.0)},
        meme_delta={"curiosity": ("hero", 0.5), "promise": ("street", 0.5)},
    )
    world.say(text)


def set_mystery(world: GymWorld) -> None:
    token = TOKENS[world.params.token]
    text = (
        f"Beside the road stood a wobbly wagon dressed in ribbons. "
        f"When the drum gave its first soft call, {token.label} was gone from the wagon bow, and the room fell still around the mystery."
    )
    world.get("token").location = "unknown"
    world.record(
        "mystery",
        text,
        "wagon",
        "token",
        meter_delta={"hiddenness": ("token", 3.0), "readiness": ("token", -1.0)},
        meme_delta={"worry": ("hero", 1.0), "trouble": ("wagon", 1.0)},
    )
    world.say(text)


def guide_warning(world: GymWorld) -> None:
    guide = GUIDES[world.params.guide]
    text = f'{guide.name} murmured, "{guide.proverb}"'
    world.record(
        "warning",
        text,
        "guide",
        "hero",
        meme_delta={"patience": ("hero", 1.0), "calm": ("guide", 0.5)},
    )
    world.say(text)


def false_guess_line(world: GymWorld) -> str:
    imagined = copy.deepcopy(world)
    imagined.get("hero").memes["worry"] += 1.0
    imagined.get("hero").meters["steps"] += 2.0
    if imagined.get("hero").memes["worry"] > imagined.get("hero").memes["patience"]:
        return (
            f"For one quick breath, {imagined.get('hero').name} almost blamed a wandering thief. "
            "But the gym had left a plainer answer under its own bright hush."
        )
    return (
        f"For one quick breath, {imagined.get('hero').name} nearly called out a wild guess. "
        "But guessing would only have trampled the marks that were already telling the truth."
    )


def follow_clue(world: GymWorld) -> None:
    problem = PROBLEMS[world.params.problem]
    text = problem.clue_text
    world.record(
        "clue",
        text,
        "hero",
        "street",
        meter_delta={"clues_seen": ("hero", 1.0), "clarity": ("street", 1.0), "steps": ("hero", 1.0)},
        meme_delta={"curiosity": ("hero", 1.0), "worry": ("hero", -0.5)},
    )
    world.say(text)


def reveal_truth(world: GymWorld) -> None:
    hero = HEROES[world.params.hero]
    token = TOKENS[world.params.token]
    problem = PROBLEMS[world.params.problem]
    text = (
        f"{hero.name} followed the sign to {problem.hiding_place} and found {token.label} there. "
        f"{problem.truth_text}"
    )
    world.get("token").location = problem.hiding_place
    world.record(
        "reveal",
        text,
        "hero",
        "token",
        meter_delta={"hiddenness": ("token", -3.0), "steps": ("hero", 1.0)},
        meme_delta={"relief": ("hero", 1.5), "worry": ("hero", -1.0), "trouble": ("wagon", -0.5)},
    )
    world.say(text)


def repair_cause(world: GymWorld) -> None:
    guide = GUIDES[world.params.guide]
    text = (
        f"{guide.repair_text} "
        "After that, the wagon stood still long enough to look almost proud of learning better manners."
    )
    world.record(
        "repair",
        text,
        "guide",
        "wagon",
        meter_delta={"stability": ("wagon", 2.5), "wobble": ("wagon", -3.0), "safety": ("wagon", 2.0), "repairs": ("guide", 1.0)},
        meme_delta={"trouble": ("wagon", -2.5), "relief": ("hero", 0.5)},
    )
    world.say(text)


def ending(world: GymWorld) -> None:
    hero = HEROES[world.params.hero]
    token = TOKENS[world.params.token]
    world.get("token").location = "wagon bow"
    text = (
        f"{hero.name} fastened {token.label} back in its place, and {lower_lead(str(world.facts['ending_image']))} "
        "Then the wagon rolled steady down the shiny street, and every child in the indoor gym knew the mystery had been answered by honest clues."
    )
    world.record(
        "ending",
        text,
        "hero",
        "wagon",
        meter_delta={"readiness": ("token", 2.0), "shine": ("street", 0.5), "clarity": ("street", 0.5)},
        meme_delta={"relief": ("hero", 1.0), "promise": ("street", 1.0), "worry": ("hero", -0.5)},
    )
    world.say(text)


def tell(world: GymWorld) -> str:
    opening(world)
    set_mystery(world)
    world.break_paragraph()
    guide_warning(world)
    world.say(false_guess_line(world))
    follow_clue(world)
    world.break_paragraph()
    reveal_truth(world)
    repair_cause(world)
    ending(world)
    return world.render()


def generation_prompts(params: StoryParams) -> list[str]:
    return [
        "Write a TinyStories-style folk tale with a clear mystery to solve.",
        "Set it in an indoor gym and include the exact phrases shiny street and wobbly wagon.",
        "Let physical clues and a repaired cause solve the problem instead of blaming a villain.",
    ]


def story_qa(world: GymWorld) -> list[QAItem]:
    hero = HEROES[world.params.hero]
    token = TOKENS[world.params.token]
    guide = GUIDES[world.params.guide]
    problem = PROBLEMS[world.params.problem]
    return [
        QAItem(
            "What mystery did the child have to solve?",
            f"{hero.name} had to discover where {token.label} had gone when it vanished from the wagon bow. "
            "The story makes the mystery fair because the answer is hidden in the room's physical traces, not in a secret confession.",
        ),
        QAItem(
            f"How did {hero.name} find {token.label}?",
            f"{hero.name} found it by following the clue trail to {problem.hiding_place}. "
            f"That path showed that {problem.truth_text[0].lower() + problem.truth_text[1:]}",
        ),
        QAItem(
            f"Why did {guide.name} tell the child to look at the floor first?",
            f"{guide.name} wanted the child to trust patient noticing before blaming anyone. "
            f"If the real cause had stayed unfixed, {problem.risk_text}.",
        ),
        QAItem(
            "How does the ending prove the world changed?",
            f"The ending proves it because {token.label} is fastened back in place and the wagon rolls steady instead of wobbling. "
            "The final image shows the procession moving at last, so the story ends with a repaired world rather than an unfinished promise.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "gym": QAItem(
        "Why can an indoor gym belong in a folk tale?",
        "A folk tale needs a shared place where people gather, remember, and learn. If a gym holds a ritual, a puzzle, and a lesson, it can feel as storied as a village square.",
    ),
    "wagon": QAItem(
        "Why should a wagon be repaired before a procession starts?",
        "A shaking wagon can lose what it carries and frighten the people behind it. Repairing it changes the danger itself instead of only patching the first accident.",
    ),
    "clue": QAItem(
        "Why are physical clues better than quick guesses in this storyworld?",
        "Physical clues show what truly moved in the world. They help a child follow cause and effect without hurting anyone through careless blame.",
    ),
    "patience": QAItem(
        "What lesson does patience teach in these mysteries?",
        "Patience keeps the child close to the truth. In this world, a calm look at the room is wiser than a fast shout.",
    ),
    "repair": QAItem(
        "Why does the story repair the cause after finding the missing object?",
        "Finding the object ends the first fear, but repairing the cause prevents the trouble from returning. A good ending changes tomorrow's path as well as today's feeling.",
    ),
}


def world_qa(world: GymWorld) -> list[QAItem]:
    ordered = ["gym", "wagon", "clue", "patience", "repair"]
    return [WORLD_KNOWLEDGE[key] for key in ordered][:4]


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = build_world(params)
    story = tell(world)
    if "shiny street" not in story or "wobbly wagon" not in story or "indoor gym" not in story:
        raise StoryError("generated story missed one of the required seed phrases")
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(params),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--street", choices=sorted(STREETS))
    parser.add_argument("--token", choices=sorted(TOKENS))
    parser.add_argument("--problem", choices=sorted(PROBLEMS))
    parser.add_argument("--guide", choices=sorted(GUIDES))
    parser.add_argument("--hero", choices=sorted(HEROES))
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        combo
        for combo in all_params()
        if (args.street is None or combo.street == args.street)
        and (args.token is None or combo.token == args.token)
        and (args.problem is None or combo.problem == args.problem)
        and (args.guide is None or combo.guide == args.guide)
        and (args.hero is None or combo.hero == args.hero)
    ]
    if not choices:
        params = StoryParams(
            street=args.street or sorted(STREETS)[0],
            token=args.token or sorted(TOKENS)[0],
            problem=args.problem or sorted(PROBLEMS)[0],
            guide=args.guide or sorted(GUIDES)[0],
            hero=args.hero or sorted(HEROES)[0],
            seed=args.seed,
        )
        ok, reason = valid_params(params)
        raise StoryError(reason if not ok else "no parameter choices matched the requested filters")
    picked = rng.choice(choices)
    return StoryParams(
        street=picked.street,
        token=picked.token,
        problem=picked.problem,
        guide=picked.guide,
        hero=picked.hero,
        seed=args.seed,
    )


ASP_RULES = r"""
valid(S,T,P,G,H) :-
    street(S),
    token(T),
    problem(P),
    guide(G),
    hero(H),
    reveals(S,P),
    risks(T,P),
    guide_skill(G,K),
    repair_skill(P,K).
#show valid/5.
"""


def asp_facts() -> str:
    import asp

    facts: list[str] = []
    for street in STREETS.values():
        facts.append(asp.fact("street", street.id))
        for problem_id in street.reveal_problems:
            facts.append(asp.fact("reveals", street.id, problem_id))
    for token in TOKENS.values():
        facts.append(asp.fact("token", token.id))
        for problem_id in token.risks:
            facts.append(asp.fact("risks", token.id, problem_id))
    for problem in PROBLEMS.values():
        facts.append(asp.fact("problem", problem.id))
        facts.append(asp.fact("repair_skill", problem.id, problem.repair_skill))
    for guide in GUIDES.values():
        facts.append(asp.fact("guide", guide.id))
        facts.append(asp.fact("guide_skill", guide.id, guide.repair_skill))
    for hero in HEROES.values():
        facts.append(asp.fact("hero", hero.id))
    return "\n".join(facts) + "\n"


def asp_program() -> str:
    return asp_facts() + ASP_RULES


def asp_valid_params() -> list[StoryParams]:
    import asp

    combos: list[StoryParams] = []
    for model in asp.solve(asp_program(), models=1):
        for atom in asp.atoms(model, "valid"):
            street, token, problem, guide, hero = (str(part) for part in atom)
            combos.append(StoryParams(street, token, problem, guide, hero))
    return sorted(combos, key=lambda p: (p.street, p.token, p.problem, p.guide, p.hero))


def verify() -> str:
    py = set(all_params())
    lp = set(asp_valid_params())
    if py != lp:
        missing = sorted(py - lp, key=lambda p: (p.street, p.token, p.problem, p.guide, p.hero))
        extra = sorted(lp - py, key=lambda p: (p.street, p.token, p.problem, p.guide, p.hero))
        raise StoryError(f"ASP mismatch; missing={missing[:5]} extra={extra[:5]}")

    for params in sorted(py, key=lambda p: (p.street, p.token, p.problem, p.guide, p.hero)):
        sample = generate(params)
        world = sample.world
        if world is None:
            raise StoryError(f"missing world for {params}")
        if len(sample.story_qa) < 4 or len(sample.world_qa) < 4:
            raise StoryError(f"QA generation too thin for {params}")
        if world.get("wagon").meters["stability"] <= world.get("wagon").meters["wobble"]:
            raise StoryError(f"wagon was not truly repaired for {params}")
        if world.get("token").location != "wagon bow":
            raise StoryError(f"token did not return to the wagon for {params}")
        if not sample.story.endswith("the mystery had been answered by honest clues."):
            raise StoryError(f"ending image too weak for {params}")
    return f"OK: Python and ASP agree on {len(py)} valid indoor-gym mysteries, and all generated stories passed the smoke check."


def iter_samples(args: argparse.Namespace) -> Iterable[StorySample]:
    if args.all:
        for params in all_params():
            yield generate(params)
        return
    rng = random.Random(args.seed)
    for _ in range(max(1, args.n)):
        yield generate(resolve_params(args, rng))


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\nTrace:")
        print(sample.world.trace())
    if qa:
        print("\nPrompts:")
        for prompt in sample.prompts:
            print(f"- {prompt}")
        print("\nStory QA:")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\nWorld QA:")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            import asp

            print(asp.solve(asp_program()))
            return 0
        for index, sample in enumerate(iter_samples(args)):
            if args.json:
                print(sample.to_json())
            else:
                if index:
                    print("\n---\n")
                emit(sample, trace=args.trace, qa=args.qa)
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
