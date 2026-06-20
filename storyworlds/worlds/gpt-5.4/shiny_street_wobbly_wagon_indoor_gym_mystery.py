#!/usr/bin/env python3
"""A folk-tale mystery in an indoor gym with a shiny street and a wobbly wagon.

Seed:
    Words: shiny street, wobbly wagon
    Setting: indoor gym
    Features: Mystery to Solve
    Style: Folk Tale

Internal source tale:
    Rain drives a village procession indoors. A child must discover why the
    parade treasure vanished from a wobbly wagon beside a shiny street laid
    across the gym floor. The clues prove there was no thief at all; the wagon
    itself, tilted by a small physical fault, shook the treasure into a hiding
    place. The child solves the mystery by reading the room, not by guessing,
    and the ending image shows the wagon repaired and the indoor procession
    ready to begin.
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
class Treasure:
    id: str
    label: str
    role: str
    risks: tuple[str, ...]
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
    treasure: str
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
            f"treasure={self.params.treasure}",
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
    "silver_tape": Street(
        id="silver_tape",
        label="silver tape road",
        description="a shiny street of silver tape running between stacked mats and a low climbing rope",
        reveal_problems=("axle_pin", "slick_wheel"),
        ending_image="The silver tape held the lamp-glow so neatly that the whole gym looked like a small moon road.",
        tags=("street", "silver", "gym"),
    ),
    "chalk_moons": Street(
        id="chalk_moons",
        label="chalk moon road",
        description="a shiny street dusted with pearl chalk crescents from the door to the hoop arch",
        reveal_problems=("crooked_load", "axle_pin"),
        ending_image="The chalk moons lay straight again, each one pointing toward the waiting arch.",
        tags=("street", "chalk", "gym"),
    ),
    "tin_ribbon": Street(
        id="tin_ribbon",
        label="tin ribbon road",
        description="a shiny street braided from tin-bright ribbon across the waxed floorboards",
        reveal_problems=("crooked_load", "slick_wheel"),
        ending_image="The tin ribbon gave a soft bright flutter whenever the high windows breathed.",
        tags=("street", "ribbon", "gym"),
    ),
}


TREASURES = {
    "moon_bell": Treasure(
        id="moon_bell",
        label="the moon bell",
        role="the bell that should ring at the head of the procession",
        risks=("axle_pin", "slick_wheel"),
        tags=("bell", "sound", "festival"),
    ),
    "star_lantern": Treasure(
        id="star_lantern",
        label="the star lantern",
        role="the paper lantern that should glow over the arch",
        risks=("crooked_load", "slick_wheel"),
        tags=("lantern", "light", "festival"),
    ),
    "harvest_crown": Treasure(
        id="harvest_crown",
        label="the harvest crown",
        role="the tin crown that should rest above the leading seat",
        risks=("crooked_load", "axle_pin"),
        tags=("crown", "tin", "festival"),
    ),
}


PROBLEMS = {
    "axle_pin": Problem(
        id="axle_pin",
        label="a loose axle pin",
        clue_text="A bright little pin lay near the jump-rope basket, and the floor carried tiny ringing scratches toward it.",
        hiding_place="the jump-rope basket",
        truth_text="The axle pin had slipped free, so every bounce of the wagon shook the treasure down into the basket.",
        repair_skill="peg",
        risk_text="the wagon would keep knocking its burden loose with every turn",
        tags=("wagon", "metal", "clue"),
    ),
    "crooked_load": Problem(
        id="crooked_load",
        label="a load stacked too far to one side",
        clue_text="One row of pearl chalk bent away from the road and curved under the folded tumbling mat.",
        hiding_place="the pocket under the folded tumbling mat",
        truth_text="The load leaned too far to one side, and the treasure slid quietly under the mat instead of staying on its hook.",
        repair_skill="balance",
        risk_text="the wagon would tip its burden again before the procession crossed the gym",
        tags=("wagon", "balance", "clue"),
    ),
    "slick_wheel": Problem(
        id="slick_wheel",
        label="a wheel polished too smooth",
        clue_text="A pale wheel streak curved away from the road and ended behind the drum crate, where a faint glimmer waited.",
        hiding_place="the space behind the drum crate",
        truth_text="The smooth wheel skidded on the waxed floor, and the treasure bumped away when the wagon lurched.",
        repair_skill="wrap",
        risk_text="the wagon would slide off the road each time the floor turned glossy under the lamps",
        tags=("wagon", "wheel", "clue"),
    ),
}


GUIDES = {
    "neri": Guide(
        id="neri",
        name="Old Neri",
        role="the keeper of the gym keys",
        repair_skill="peg",
        repair_text="Old Neri tapped a cedar peg through the axle and tested the wheel with both calm hands.",
        proverb="In old houses and old tales, the floor tells the truth before the mouth does.",
        tags=("elder", "repair", "wagon"),
    ),
    "sima": Guide(
        id="sima",
        name="Grandmother Sima",
        role="the ribbon weaver of the harvest walk",
        repair_skill="balance",
        repair_text="Grandmother Sima shifted the bundles to the center and tied them with a flat red cord until the wagon sat level.",
        proverb="What leans in secret will confess itself when the road is watched with patient eyes.",
        tags=("elder", "repair", "balance"),
    ),
    "olek": Guide(
        id="olek",
        name="Drum-master Olek",
        role="the musician who woke the fair each year",
        repair_skill="wrap",
        repair_text="Drum-master Olek bound the slick wheel with a band of soft felt so it could grip the floor instead of skating on it.",
        proverb="A true riddle is not chased by shouting feet but answered by listening hands.",
        tags=("elder", "repair", "music"),
    ),
}


HEROES = {
    "mara": Hero(id="mara", name="Mara", kind="girl", trait="careful"),
    "timo": Hero(id="timo", name="Timo", kind="boy", trait="bright-eyed"),
    "sela": Hero(id="sela", name="Sela", kind="girl", trait="steadfast"),
}


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.street not in STREETS:
        return False, f"unknown street: {params.street}"
    if params.treasure not in TREASURES:
        return False, f"unknown treasure: {params.treasure}"
    if params.problem not in PROBLEMS:
        return False, f"unknown problem: {params.problem}"
    if params.guide not in GUIDES:
        return False, f"unknown guide: {params.guide}"
    if params.hero not in HEROES:
        return False, f"unknown hero: {params.hero}"

    street = STREETS[params.street]
    treasure = TREASURES[params.treasure]
    problem = PROBLEMS[params.problem]
    guide = GUIDES[params.guide]

    if params.problem not in street.reveal_problems:
        return False, f"{street.label} does not leave a readable trail for {problem.label}"
    if params.problem not in treasure.risks:
        return False, f"{problem.label} cannot plausibly hide {treasure.label}"
    if guide.repair_skill != problem.repair_skill:
        return False, f"{guide.name} cannot repair {problem.label}"
    return True, ""


def all_params() -> list[StoryParams]:
    combos: list[StoryParams] = []
    for street in sorted(STREETS):
        for treasure in sorted(TREASURES):
            for problem in sorted(PROBLEMS):
                for guide in sorted(GUIDES):
                    for hero in sorted(HEROES):
                        params = StoryParams(street, treasure, problem, guide, hero)
                        if valid_params(params)[0]:
                            combos.append(params)
    return combos


def build_world(params: StoryParams) -> GymWorld:
    street = STREETS[params.street]
    treasure = TREASURES[params.treasure]
    problem = PROBLEMS[params.problem]
    guide = GUIDES[params.guide]
    hero = HEROES[params.hero]

    world = GymWorld(params=params)
    world.add_entity(
        Entity(
            id="gym",
            name="the indoor gym",
            kind="place",
            location="hill school",
            meters={"echo": 1.0, "lamplight": 2.0},
            memes={"welcome": 1.0},
            tags=("gym", "place"),
        )
    )
    world.add_entity(
        Entity(
            id="street",
            name=street.label,
            kind="road",
            location="gym floor",
            meters={"shine": 3.0, "straightness": 2.0},
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
            id="treasure",
            name=treasure.label,
            kind="treasure",
            location="missing",
            meters={"hiddenness": 3.0, "readiness": 0.0},
            memes={"importance": 3.0},
            tags=treasure.tags,
        )
    )
    world.add_entity(
        Entity(
            id="hero",
            name=hero.name,
            kind=hero.kind,
            location="gym floor",
            meters={"clues_seen": 0.0, "steps": 0.0},
            memes={"curiosity": 2.0, "worry": 1.0, "relief": 0.0},
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
            memes={"wisdom": 2.0, "patience": 2.0},
            tags=guide.tags,
        )
    )
    world.facts["street_description"] = street.description
    world.facts["mystery"] = f"Why had {treasure.label} vanished from the head of the procession?"
    world.facts["risk"] = problem.risk_text
    world.facts["hiding_place"] = problem.hiding_place
    world.facts["truth"] = problem.truth_text
    world.facts["repair"] = guide.repair_text
    world.facts["proverb"] = guide.proverb
    world.facts["ending_image"] = street.ending_image
    return world


def opening(world: GymWorld) -> None:
    hero = HEROES[world.params.hero]
    street = STREETS[world.params.street]
    treasure = TREASURES[world.params.treasure]
    text = (
        f"When rain chased the village fair from the square, the people carried it into the indoor gym. "
        f"Across the floor they laid {street.description}, and {hero.name}, a {hero.trait} child, was asked to watch over {treasure.role}."
    )
    world.record(
        "opening",
        text,
        "gym",
        "hero",
        meter_delta={"steps": ("hero", 1.0)},
        meme_delta={"curiosity": ("hero", 0.5)},
    )
    world.say(text)


def set_mystery(world: GymWorld) -> None:
    treasure = TREASURES[world.params.treasure]
    text = (
        f"Beside the road stood a wobbly wagon draped in red cloth. "
        f"But when the lamps were lit, {treasure.label} was gone from its place, and the whole gym seemed to hold its breath."
    )
    world.get("treasure").location = "unknown"
    world.record(
        "mystery",
        text,
        "wagon",
        "treasure",
        meme_delta={"worry": ("hero", 1.0), "trouble": ("wagon", 1.0)},
    )
    world.say(text)


def speak_proverb(world: GymWorld) -> None:
    guide = GUIDES[world.params.guide]
    text = f'{guide.name} said, "{guide.proverb}"'
    world.record(
        "proverb",
        text,
        "guide",
        "hero",
        meme_delta={"patience": ("guide", 0.5), "curiosity": ("hero", 0.5)},
    )
    world.say(text)


def follow_clue(world: GymWorld) -> None:
    problem = PROBLEMS[world.params.problem]
    text = problem.clue_text
    world.record(
        "clue",
        text,
        "hero",
        "street",
        meter_delta={"clues_seen": ("hero", 1.0), "straightness": ("street", -0.5)},
        meme_delta={"curiosity": ("hero", 1.0)},
    )
    world.say(text)


def imagine_wrong_guess(world: GymWorld) -> str:
    imagined = copy.deepcopy(world)
    imagined.get("hero").memes["worry"] += 1.0
    imagined.get("hero").meters["steps"] += 2.0
    if imagined.get("hero").memes["worry"] > imagined.get("hero").memes["curiosity"]:
        return (
            "For a blink, the child almost ran to the door to hunt for an unseen thief, "
            "but that path smelled of hurry instead of truth."
        )
    return (
        "For a blink, the child almost shouted a wild guess, "
        "but the marks on the floor were speaking more wisely than a quick tongue."
    )


def reveal_truth(world: GymWorld) -> None:
    problem = PROBLEMS[world.params.problem]
    treasure = TREASURES[world.params.treasure]
    text = (
        f"{HEROES[world.params.hero].name} followed the trail to {problem.hiding_place} and found {treasure.label} there. "
        f"{problem.truth_text}"
    )
    world.get("treasure").location = problem.hiding_place
    world.record(
        "reveal",
        text,
        "hero",
        "treasure",
        meter_delta={"hiddenness": ("treasure", -3.0), "steps": ("hero", 1.0)},
        meme_delta={"relief": ("hero", 1.5), "worry": ("hero", -1.0)},
    )
    world.say(text)


def repair_wagon(world: GymWorld) -> None:
    guide = GUIDES[world.params.guide]
    text = f"{guide.repair_text} After that, the wagon no longer shook at the edge of the road."
    world.record(
        "repair",
        text,
        "guide",
        "wagon",
        meter_delta={"stability": ("wagon", 2.0), "wobble": ("wagon", -3.0), "safety": ("wagon", 2.0), "repairs": ("guide", 1.0)},
        meme_delta={"trouble": ("wagon", -3.0), "relief": ("hero", 0.5)},
    )
    world.say(text)


def restore_procession(world: GymWorld) -> None:
    treasure = TREASURES[world.params.treasure]
    street = STREETS[world.params.street]
    hero = HEROES[world.params.hero]
    world.get("treasure").location = "wagon hook"
    text = (
        f"{hero.name} hung {treasure.label} in its proper place once more. "
        f"{street.ending_image} Then the repaired wagon rolled true, and the waiting children followed it as if they were following a promise kept."
    )
    world.record(
        "ending",
        text,
        "hero",
        "wagon",
        meter_delta={"readiness": ("treasure", 3.0), "straightness": ("street", 1.0), "shine": ("street", 0.5)},
        meme_delta={"promise": ("street", 1.0), "relief": ("hero", 1.0), "worry": ("hero", -1.0)},
    )
    world.say(text)


def tell(world: GymWorld) -> str:
    opening(world)
    set_mystery(world)
    world.break_paragraph()
    speak_proverb(world)
    follow_clue(world)
    world.say(imagine_wrong_guess(world))
    world.break_paragraph()
    reveal_truth(world)
    repair_wagon(world)
    restore_procession(world)
    return world.render()


def generation_prompts(params: StoryParams) -> list[str]:
    return [
        "Write a TinyStories-style folk tale.",
        "Set the mystery in an indoor gym with a shiny street and a wobbly wagon.",
        "Make the answer come from physical clues and a repaired world state rather than from a villain confession.",
    ]


def story_qa(world: GymWorld) -> list[QAItem]:
    hero = HEROES[world.params.hero]
    treasure = TREASURES[world.params.treasure]
    problem = PROBLEMS[world.params.problem]
    guide = GUIDES[world.params.guide]
    return [
        QAItem(
            "What mystery did the child need to solve?",
            f"{hero.name} needed to solve why {treasure.label} had vanished from the head of the procession. "
            f"The clues in the indoor gym showed that the answer was hidden in the wagon's movement, not in a thief's footsteps.",
        ),
        QAItem(
            f"How did {hero.name} solve the mystery?",
            f"{hero.name} solved it by reading the marks on the shiny street and following them to {problem.hiding_place}. "
            f"That trail proved {problem.truth_text[0].lower() + problem.truth_text[1:]}",
        ),
        QAItem(
            f"Why did {guide.name} tell the child to slow down?",
            f"{guide.name} wanted the child to notice the floor clues before making a wild guess. "
            f"If they had hurried, {problem.risk_text}.",
        ),
        QAItem(
            "How does the ending prove that the problem was truly fixed?",
            f"The ending proves it because {treasure.label} is returned to its place and the wagon rolls straight again. "
            "The final procession image shows a changed world instead of a promise to fix things later.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "gym": QAItem(
        "Why can an indoor gym become part of a folk tale?",
        "A folk tale can grow anywhere people gather and remember old sayings. If the place carries a ritual, a mystery, and a lesson, even a gym can feel storied.",
    ),
    "wagon": QAItem(
        "Why should a wagon be balanced before a parade?",
        "A wagon that leans or shakes can drop what it is carrying. Fixing the balance protects both the treasure and the people following behind.",
    ),
    "clue": QAItem(
        "Why are floor clues useful in a mystery?",
        "Floor clues show where something actually moved. They help a careful person follow cause and effect instead of trusting a frightened guess.",
    ),
    "patience": QAItem(
        "What lesson does patience teach in this storyworld?",
        "Patience makes room for true noticing. In these stories, the child solves trouble by reading the world carefully before speaking.",
    ),
    "repair": QAItem(
        "Why is repairing the cause better than only finding the lost object?",
        "Finding the object ends the first worry, but repairing the cause prevents the trouble from returning. A good ending changes the world so the same mistake cannot happen in the next minute.",
    ),
}


def world_qa(world: GymWorld) -> list[QAItem]:
    tags = {"gym", "wagon", "clue", "patience", "repair"}
    tags.update(STREETS[world.params.street].tags)
    tags.update(TREASURES[world.params.treasure].tags)
    tags.update(PROBLEMS[world.params.problem].tags)
    tags.update(GUIDES[world.params.guide].tags)
    ordered = ["gym", "wagon", "clue", "patience", "repair"]
    return [WORLD_KNOWLEDGE[key] for key in ordered if key in tags][:4]


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
    parser.add_argument("--treasure", choices=sorted(TREASURES))
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
        and (args.treasure is None or combo.treasure == args.treasure)
        and (args.problem is None or combo.problem == args.problem)
        and (args.guide is None or combo.guide == args.guide)
        and (args.hero is None or combo.hero == args.hero)
    ]
    if not choices:
        params = StoryParams(
            street=args.street or sorted(STREETS)[0],
            treasure=args.treasure or sorted(TREASURES)[0],
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
        treasure=picked.treasure,
        problem=picked.problem,
        guide=picked.guide,
        hero=picked.hero,
        seed=args.seed,
    )


ASP_RULES = r"""
valid(S,T,P,G,H) :-
    street(S),
    treasure(T),
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
    for treasure in TREASURES.values():
        facts.append(asp.fact("treasure", treasure.id))
        for problem_id in treasure.risks:
            facts.append(asp.fact("risks", treasure.id, problem_id))
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
            street, treasure, problem, guide, hero = (str(part) for part in atom)
            combos.append(StoryParams(street, treasure, problem, guide, hero))
    return sorted(combos, key=lambda p: (p.street, p.treasure, p.problem, p.guide, p.hero))


def verify() -> str:
    py = set(all_params())
    lp = set(asp_valid_params())
    if py != lp:
        missing = sorted(py - lp, key=lambda p: (p.street, p.treasure, p.problem, p.guide, p.hero))
        extra = sorted(lp - py, key=lambda p: (p.street, p.treasure, p.problem, p.guide, p.hero))
        raise StoryError(f"ASP mismatch; missing={missing[:5]} extra={extra[:5]}")

    for params in sorted(py, key=lambda p: (p.street, p.treasure, p.problem, p.guide, p.hero)):
        sample = generate(params)
        if len(sample.story_qa) < 3 or len(sample.world_qa) < 3:
            raise StoryError(f"QA generation too thin for {params}")
        if not sample.story.endswith("promise kept."):
            raise StoryError(f"ending image too weak for {params}")
    return f"OK: Python and ASP agree on {len(py)} valid shiny-street mysteries, and all generated stories passed the smoke check."


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
