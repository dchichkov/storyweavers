#!/usr/bin/env python3
"""
A small space-adventure storyworld about a thrush, a volley, and a guardian.

The simulation follows a young space explorer and a guardian drone as they
protect a traveling thrush from a drifting volley of moon-ice. Suspense grows
when the navigation beacon fails, and teamwork turns the volley into a safe
signal path.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from storyworlds.results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Scene:
    station: str
    sector: str
    beacon: str
    danger: str


class World:
    def __init__(self, scene: Scene):
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class Arc:
    id: str
    need: str
    opening: str
    obstacle: str
    turn: str
    action: str
    reveal: str
    result: str
    ending: str


@dataclass
class StoryParams:
    station: str
    sector: str
    astronaut_name: str
    astronaut_type: str
    guardian_name: str
    guardian_type: str
    thrush_name: str
    seed: Optional[int] = None


STATIONS = {
    "orion_gate": Scene(
        station="Orion Gate",
        sector="the blue comet sector",
        beacon="the north beacon",
        danger="a volley of moon-ice",
    ),
    "lumen_dock": Scene(
        station="Lumen Dock",
        sector="the violet ring sector",
        beacon="the old signal tower",
        danger="a volley of silver stones",
    ),
    "starling_outpost": Scene(
        station="Starling Outpost",
        sector="the quiet nebula",
        beacon="the amber landing beacon",
        danger="a volley of frozen dust",
    ),
}

ASTRONAUTS = {
    "Luna": "girl",
    "Milo": "boy",
    "Ari": "girl",
    "Tess": "girl",
    "Jon": "boy",
    "Niko": "boy",
}

GUARDIANS = {
    "Guardian Sol": "woman",
    "Guardian Pax": "man",
    "Guardian Vega": "woman",
    "Guardian Flint": "man",
}

THRUSHES = ("Bluewing", "Pip", "Comet", "Echo")

ARCS = (
    Arc(
        id="beacon_in_the_storm",
        need="was guiding a small thrush toward a safe nesting dome",
        opening="{astronaut} watched the thrush circle the observation window above {station}.",
        obstacle="Without warning, the navigation beacon blinked out as {danger} swept across the sector.",
        turn="{astronaut} noticed that the thrush was not fleeing; it was tapping its beak in the same rhythm as the weak beacon.",
        action="{astronaut} counted the taps while {guardian} turned the shield panels one at a time, making a bright path through the darkness.",
        reveal="The thrush flew along the new path and led them to a hidden relay crystal beneath the station.",
        result="When the relay crystal was placed in the beacon, the safe route shone again and the thrush reached its nest.",
        ending="The guardian held one quiet shield overhead while the thrush sang from the warm dome.",
    ),
    Arc(
        id="ice_ring_rescue",
        need="was carrying a message to a lonely research crew",
        opening="{astronaut} and {guardian} were crossing {sector} when the thrush flew beside their little shuttle.",
        obstacle="A volley of ice fragments spun around the shuttle, and the message beacon began to tumble away.",
        turn="{astronaut} saw the thrush dip left each time the safest gap opened.",
        action="{astronaut} called the turns while {guardian} fired short, careful puffs that matched the thrush's flight.",
        reveal="Together they reached the beacon before it vanished into the ice ring.",
        result="The message went through, and the distant crew answered with three grateful flashes.",
        ending="The thrush perched on the shuttle antenna as the answered lights blinked like friendly stars.",
    ),
    Arc(
        id="silent_moon",
        need="was searching for a place where the thrush could rest",
        opening="Near a silent moon, {astronaut} found the thrush shivering beside a cracked landing marker.",
        obstacle="A volley of pebbles rose from the moon's shadow and covered the only trail to shelter.",
        turn="{guardian} heard a hollow note under the stones, while {astronaut} saw tiny thrush footprints leading toward it.",
        action="{astronaut} marked the footprints and {guardian} lifted the stones with a gentle beam.",
        reveal="Under the last stone lay a warm cave with a working air lamp.",
        result="The thrush settled inside, and the two travelers repaired the marker so other creatures could find shelter too.",
        ending="The repaired marker cast a gold arrow across the moon dust while the thrush tucked in its wings.",
    ),
    Arc(
        id=" comet_signal",
        need="was hoping to send a welcome signal to a returning friend",
        opening="{astronaut} prepared a welcome signal at {station}, and a curious thrush watched from the antenna.",
        obstacle="A volley of sparks scattered the signal mirrors before the returning ship could see them.",
        turn="The thrush carried one fallen mirror to a place where its feathers caught the starlight.",
        action="{astronaut} followed the thrush's flight while {guardian} held the mirrors steady in the magnetic wind.",
        reveal="The mirrors formed a shining arrow that pointed directly toward the station.",
        result="The returning ship saw the arrow, and the welcome signal reached its friend in time.",
        ending="The thrush sang as the ship came home beneath a river of reflected stars.",
    ),
)


DIALOGUES = (
    '"The dark is getting wider," {astronaut} said. "Then we will make our own path," replied {guardian}.',
    '"Can you see a safe gap?" asked {astronaut}. "Not yet," said {guardian}, "but I can follow your count."',
    '"The thrush knows something," whispered {astronaut}. "Then we should listen together," answered {guardian}.',
    '"I am scared," admitted {astronaut}. "{guardian} replied, "Being scared means we must be careful, not alone."',
)


def simulate(params: StoryParams) -> World:
    scene = STATIONS[params.station]
    world = World(scene)
    astronaut = world.add(
        Entity(params.astronaut_name, "character", params.astronaut_type, params.astronaut_name)
    )
    guardian = world.add(
        Entity(params.guardian_name, "character", params.guardian_type, params.guardian_name)
    )
    thrush = world.add(
        Entity(
            params.thrush_name,
            "animal",
            "thrush",
            f"the thrush {params.thrush_name}",
            meters={"flying": 1.0},
            memes={"alert": 1.0},
        )
    )
    volley = world.add(
        Entity(
            "volley",
            "hazard",
            "space_debris",
            scene.danger,
            meters={"moving": 1.0, "danger": 1.0},
        )
    )

    rng = random.Random(params.seed if params.seed is not None else 0)
    arc = rng.choice(ARCS)
    dialogue = rng.choice(DIALOGUES)

    world.facts.update(
        astronaut=astronaut,
        guardian=guardian,
        thrush=thrush,
        volley=volley,
        arc=arc,
        dialogue=dialogue,
    )

    fmt = {
        "astronaut": astronaut.id,
        "guardian": guardian.id,
        "thrush": thrush.label,
        "station": scene.station,
        "sector": scene.sector,
        "danger": scene.danger,
    }

    world.say(f"At {scene.station}, {astronaut.id} {arc.need}.")
    world.say(arc.opening.format(**fmt))
    world.say(
        f"The guardian stood watch while the thrush fluttered near {scene.beacon}, "
        "where distant stars shone through the glass."
    )
    world.para()

    astronaut.memes["worried"] = 1.0
    volley.meters["approaching"] = 1.0
    world.say(arc.obstacle.format(**fmt))
    world.say("The station trembled, and the safe route disappeared from the screen.")
    world.para()

    thrush.memes["helpful"] = 1.0
    world.say(arc.turn.format(**fmt))
    world.say(dialogue.format(**fmt))
    world.say(arc.action.format(**fmt))
    guardian.memes["trusting"] = 1.0
    astronaut.memes["brave"] = 1.0
    volley.meters["redirected"] = 1.0
    world.para()

    thrush.meters["safe"] = 1.0
    world.say(arc.reveal.format(**fmt))
    world.say(arc.result.format(**fmt))
    astronaut.memes["relieved"] = 1.0
    guardian.memes["proud"] = 1.0
    volley.meters["safe"] = 1.0
    world.para()

    world.say(arc.ending.format(**fmt))
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    arc: Arc = f["arc"]
    astronaut: Entity = f["astronaut"]
    guardian: Entity = f["guardian"]
    scene = world.scene
    return [
        f"Write a suspenseful space adventure about {astronaut.id}, a thrush, and {guardian.id} at {scene.station}.",
        f"Tell a teamwork story in which a volley of space debris threatens a safe route and a guardian helps.",
        f"Write a child-friendly adventure where careful listening to a thrush solves a space danger.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    astronaut: Entity = f["astronaut"]
    guardian: Entity = f["guardian"]
    thrush: Entity = f["thrush"]
    arc: Arc = f["arc"]
    fmt = {
        "astronaut": astronaut.id,
        "guardian": guardian.id,
        "thrush": thrush.label,
        "station": world.scene.station,
        "sector": world.scene.sector,
        "danger": world.scene.danger,
    }
    return [
        QAItem(
            question=f"Why was {astronaut.id} traveling with the thrush?",
            answer=f"{astronaut.id} {arc.need}. The thrush needed the safe route that the adventure restored.",
        ),
        QAItem(
            question=f"What danger interrupted {astronaut.id}'s mission?",
            answer=arc.obstacle.format(**fmt),
        ),
        QAItem(
            question=f"How did {astronaut.id} and {guardian.id} work together?",
            answer=arc.action.format(**fmt),
        ),
        QAItem(
            question="How did the adventure end?",
            answer=arc.result.format(**fmt),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a thrush?",
            answer="A thrush is a small songbird known for its clear, often musical calls.",
        ),
        QAItem(
            question="What is a volley?",
            answer="A volley is a group of things sent or moving together, such as sparks, stones, or signals.",
        ),
        QAItem(
            question="What does a guardian do?",
            answer="A guardian watches over someone or something and helps keep it safe.",
        ),
        QAItem(
            question="Why is teamwork useful during a dangerous mission?",
            answer="Teamwork lets people combine different skills, notice more clues, and make careful decisions together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(A, G, T) :- astronaut(A), guardian(G), thrush(T), travels(A, T).
safe_route(T) :- thrush(T), protected(T), beacon_active.
teamwork(A, G) :- astronaut(A), guardian(G), listens(A), guards(G).
resolved(T) :- safe_route(T), teamwork(_, _).
#show reasonable/3.
#show safe_route/1.
#show teamwork/2.
#show resolved/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for station in STATIONS:
        lines.append(asp.fact("station", station))
    lines.extend(
        [
            asp.fact("astronaut", "traveler"),
            asp.fact("guardian", "guardian"),
            asp.fact("thrush", "thrush"),
            asp.fact("travels", "traveler", "thrush"),
            asp.fact("protected", "thrush"),
            asp.fact("beacon_active"),
            asp.fact("listens", "traveler"),
            asp.fact("guards", "guardian"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: Optional[str] = None) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show or ''}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        names = {symbol.name for symbol in model}
        required = {"reasonable", "safe_route", "teamwork", "resolved"}
        if not required.issubset(names):
            print("ASP verification failed: missing expected atoms.")
            return 1
        print("OK: ASP program solved and produced the expected safety relations.")
        return 0
    except Exception as exc:
        print(f"ASP verification failed: {exc}")
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Thrush volley guardian space-adventure world.")
    parser.add_argument("--station", choices=STATIONS)
    parser.add_argument("--astronaut-name", choices=list(ASTRONAUTS))
    parser.add_argument("--guardian-name", choices=list(GUARDIANS))
    parser.add_argument("--thrush-name", choices=list(THRUSHES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    station = args.station or rng.choice(list(STATIONS))
    astronaut_name = args.astronaut_name or rng.choice(list(ASTRONAUTS))
    guardian_name = args.guardian_name or rng.choice(list(GUARDIANS))
    if astronaut_name == guardian_name:
        raise StoryError("The astronaut and guardian must be different characters.")
    return StoryParams(
        station=station,
        sector=STATIONS[station].sector,
        astronaut_name=astronaut_name,
        astronaut_type=ASTRONAUTS[astronaut_name],
        guardian_name=guardian_name,
        guardian_type=GUARDIANS[guardian_name],
        thrush_name=args.thrush_name or rng.choice(THRUSHES),
        seed=rng.randrange(2**31),
    )


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
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
        print("\n--- trace ---")
        for entity in sample.world.entities.values():
            print(
                f"{entity.id}: type={entity.type}; "
                f"meters={dict(entity.meters)}; memes={dict(entity.memes)}"
            )
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                station="orion_gate",
                sector=STATIONS["orion_gate"].sector,
                astronaut_name="Luna",
                astronaut_type="girl",
                guardian_name="Guardian Sol",
                guardian_type="woman",
                thrush_name="Bluewing",
                seed=101,
            ),
            StoryParams(
                station="lumen_dock",
                sector=STATIONS["lumen_dock"].sector,
                astronaut_name="Milo",
                astronaut_type="boy",
                guardian_name="Guardian Pax",
                guardian_type="man",
                thrush_name="Pip",
                seed=202,
            ),
            StoryParams(
                station="starling_outpost",
                sector=STATIONS["starling_outpost"].sector,
                astronaut_name="Ari",
                astronaut_type="girl",
                guardian_name="Guardian Vega",
                guardian_type="woman",
                thrush_name="Comet",
                seed=303,
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        for index in range(args.n):
            params = resolve_params(args, random.Random(seed + index))
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### story {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
