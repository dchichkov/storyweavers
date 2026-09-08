#!/usr/bin/env python3
"""
A standalone storyworld: a small space adventure about a spreading moon-base,
a drifting sphere, and a careful repair.

The seed tale behind this world:
---
Luna and her friend Orin were exploring a new space-station sprawl when they
found a silver sphere floating beside a loose batten. Luna thought Orin had
moved the batten and caused the sphere to drift away. Orin felt hurt because
he had only followed the station map. They listened to each other, discovered
that a tiny robot had nudged the batten while mapping a new corridor, and
reconciled by repairing the station together.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the growing Luna station"


@dataclass
class StoryParams:
    hero_name: str
    partner_name: str
    robot_name: str
    incident_id: int = 0
    opening_mode: int = 0
    dialogue_mode: int = 0
    repair_mode: int = 0
    ending_mode: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


SETTING = Setting()

HERO_NAMES = ["Luna", "Nova", "Mira", "Tala", "Zee", "Ari"]
PARTNER_NAMES = ["Orin", "Pax", "Kito", "Sol", "Remy", "Ivo"]
ROBOT_NAMES = ["Pip", "Button", "Dot", "Mica", "Beep", "Wisp"]

INCIDENTS = [
    {
        "sphere": "a silver survey sphere",
        "problem": "The sphere had drifted toward an open maintenance hatch.",
        "risk": "The hatch led to a dark service tunnel, so Luna clipped a safety line to the rail before anyone reached for the sphere.",
        "misunderstanding": "Luna thought Orin had moved the batten and sent the sphere floating away.",
        "truth": "Orin had followed the station map; the mapping robot had bumped the batten while scanning a new corridor.",
        "clue": "a row of fresh wheel marks, a blinking map light, and the batten's soft scrape against the floor",
        "action": "They asked the robot to pause, secured the sphere with a tether, and fastened the batten across the loose edge.",
        "result": "The hatch was covered, the sphere returned to its charging cradle, and the corridor became safe for travelers.",
        "image": "At bedtime, the silver sphere shone beside the repaired batten while tiny stars moved across the station window.",
    },
    {
        "sphere": "a blue weather sphere",
        "problem": "The sphere had rolled beneath a bridge in the station's expanding garden ring.",
        "risk": "The bridge floor was still being tested, so the children stayed behind a yellow line.",
        "misunderstanding": "Luna believed Orin had hidden the sphere as a joke and ignored the garden warning.",
        "truth": "Orin had placed a marker by the bridge, but a service cart had pushed the sphere when its batten bumper came loose.",
        "clue": "a wheel-shaped dust trail, a crooked batten bumper, and Orin's marker still standing by the bridge",
        "action": "They told the gardener, blocked the bridge with a second batten, and used a long grabber to bring the sphere back.",
        "result": "The weather sphere was safe, and the garden ring stayed closed until the bridge was checked.",
        "image": "The repaired bumper gleamed near the moon garden, where blue flowers curled toward the station lights.",
    },
    {
        "sphere": "a warm orange practice sphere",
        "problem": "The sphere had floated into the wide central sprawl of the station.",
        "risk": "Busy air carts crossed the central space, so the children watched from a marked platform.",
        "misunderstanding": "Luna thought Orin had taken the sphere without asking and felt ready to report him.",
        "truth": "Orin had left it in the practice bay; a loose batten had opened the bay curtain when the air fan started.",
        "clue": "the open curtain, a bent batten latch, and a practice-bay timer still blinking",
        "action": "They stopped the fan with the teacher's help, repaired the latch, and guided the sphere back along the floor.",
        "result": "The practice bay closed properly, and Luna learned that a missing object did not always mean a friend's mistake.",
        "image": "The orange sphere rested under its net while the central station lights glowed like a gentle sunrise.",
    },
    {
        "sphere": "a tiny green message sphere",
        "problem": "The sphere had stopped beside a new wall in the station sprawl.",
        "risk": "The wall panels were not fully locked, so nobody leaned against them or squeezed through.",
        "misunderstanding": "Luna thought Orin had changed the route without telling her.",
        "truth": "Orin had followed the old signs, while a construction crew had shifted a batten and built the new wall around it.",
        "clue": "two different route arrows, fresh wall dust, and the batten's numbered repair tag",
        "action": "They compared the old map with the new one, called the station builder, and placed a clear arrow beside the safe route.",
        "result": "The message sphere reached its receiver, and every traveler could tell which corridor was open.",
        "image": "A bright arrow pointed through the finished corridor as the green sphere sent one cheerful ping.",
    },
]

OPENINGS = [
    "On a bright orbit around the Moon,",
    "During the quiet morning shift,",
    "As the Luna station stretched into a larger sprawl,",
    "Just after the stars faded from the station windows,",
    "While the crew practiced careful space walking,",
    "Near the end of a busy repair day,",
]

DIALOGUES = [
    ('"Did you move the batten?" Luna asked. "The sphere is drifting!"',
     '"No," said Orin. "I followed the map. Let us check what happened before we blame anyone."'),
    ('"I thought you sent it away," Luna said. "I felt worried."',
     '"I understand," Orin replied. "But I did not touch it. We can look for clues together."'),
    ('"The sphere was here a moment ago," Luna said. "Did you change the route?"',
     '"I changed nothing," said Orin. "Please hear my side, and then we will inspect the station."'),
    ('"I was sure you had moved the batten," Luna admitted.',
     '"I was sure you were angry with me," Orin said. "Let us trade guesses for evidence."'),
]

REPAIR_LEADS = [
    "Instead of arguing,",
    "Once they had listened to both sides,",
    "With the misunderstanding named aloud,",
    "After Luna apologized for her quick guess,",
    "Orin accepted Luna's apology, and",
    "They made a shared plan:",
]

ENDINGS = [
    "Their friendship felt steadier because both friends had made room for the truth.",
    "The station grew larger, but their trust grew stronger too.",
    "They learned that a calm question can open a door that blame would keep shut.",
    "The repair fixed more than a loose part; it repaired the space between them.",
    "Together they turned a confusing moment into a useful station lesson.",
    "No one had to win the argument. They only had to find the truth and help one another.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Space adventure storyworld about a sprawl, sphere, batten, misunderstanding, and reconciliation."
    )
    parser.add_argument("--hero-name")
    parser.add_argument("--partner-name")
    parser.add_argument("--robot-name")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    partner_name = args.partner_name or rng.choice(PARTNER_NAMES)
    robot_name = args.robot_name or rng.choice(ROBOT_NAMES)
    if hero_name == partner_name:
        raise StoryError("hero and partner must have different names")
    return StoryParams(
        hero_name=hero_name,
        partner_name=partner_name,
        robot_name=robot_name,
        incident_id=rng.randrange(len(INCIDENTS)),
        opening_mode=rng.randrange(len(OPENINGS)),
        dialogue_mode=rng.randrange(len(DIALOGUES)),
        repair_mode=rng.randrange(len(REPAIR_LEADS)),
        ending_mode=rng.randrange(len(ENDINGS)),
    )


def _build_world(params: StoryParams) -> World:
    incident = INCIDENTS[params.incident_id % len(INCIDENTS)]
    world = World(SETTING)
    hero = world.add(Entity("hero", "character", "child-explorer", params.hero_name))
    partner = world.add(Entity("partner", "character", "child-explorer", params.partner_name))
    robot = world.add(Entity("robot", "machine", "mapping-robot", params.robot_name))
    sphere = world.add(Entity("sphere", "object", "sphere", incident["sphere"]))
    batten = world.add(Entity("batten", "object", "batten", "a silver batten"))
    station = world.add(Entity("station", "place", "space-station", "Luna station"))

    hero.memes.update(curiosity=1, trust=0)
    partner.memes.update(calm=1, hurt=1)
    robot.memes.update(helpful=1)
    sphere.meters.update(drifting=1, secured=0)
    batten.meters.update(loose=1, repaired=0)
    station.meters.update(sprawl=1, safe=0)

    world.facts.update(
        hero=hero,
        partner=partner,
        robot=robot,
        sphere=sphere,
        batten=batten,
        station=station,
        incident=incident,
        params=params,
        misunderstanding=True,
        reconciliation=False,
    )
    return world


def tell(world: World) -> None:
    facts = world.facts
    params: StoryParams = facts["params"]
    hero: Entity = facts["hero"]
    partner: Entity = facts["partner"]
    robot: Entity = facts["robot"]
    sphere: Entity = facts["sphere"]
    incident: dict[str, str] = facts["incident"]

    world.say(
        f"{OPENINGS[params.opening_mode % len(OPENINGS)]} {hero.label} and {partner.label} explored {world.setting.place}, whose new halls made a shining sprawl beneath the stars."
    )
    world.say(f"They found {sphere.label}. {incident['problem']}")

    world.para()
    world.say(incident["risk"])
    first, second = DIALOGUES[params.dialogue_mode % len(DIALOGUES)]
    world.say(first.replace("Luna", hero.label).replace("Orin", partner.label))
    world.say(second.replace("Luna", hero.label).replace("Orin", partner.label))
    world.say(f"{robot.label}, the little mapping robot, blinked near the scattered tools.")

    world.para()
    world.say(f"They listened instead of interrupting. The real clue was {incident['clue']}.")
    world.say(incident["truth"])
    world.say(
        f"{hero.label} lowered their eyes. “I am sorry I guessed,” they said. {partner.label} answered, “Thank you for saying that. I am sorry I sounded cross.”"
    )
    world.say(
        f"The misunderstanding began to fade because each friend had shared what they knew and had listened to the other."
    )

    world.para()
    lead = REPAIR_LEADS[params.repair_mode % len(REPAIR_LEADS)]
    world.say(f"{lead} {incident['action']}")
    world.say(incident["result"])

    world.para()
    world.say(ENDINGS[params.ending_mode % len(ENDINGS)])
    world.say(incident["image"])

    sphere.meters["drifting"] = 0
    sphere.meters["secured"] = 1
    batten.meters["loose"] = 0
    batten.meters["repaired"] = 1
    world.facts["misunderstanding"] = False
    world.facts["reconciliation"] = True
    world.facts["station_safe"] = True
    hero.memes["trust"] = 1
    partner.memes["hurt"] = 0
    partner.memes["trust"] = 1


def generation_prompts(world: World) -> list[str]:
    incident = world.facts["incident"]
    return [
        "Write a gentle Space Adventure for a child using the words sprawl, sphere, and batten.",
        f"Tell how {world.facts['hero'].label} and {world.facts['partner'].label} solve this problem: {incident['problem']}",
        "Write a story with a misunderstanding, honest dialogue, reconciliation, safe teamwork, and a visible repaired ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    incident = facts["incident"]
    hero = facts["hero"].label
    partner = facts["partner"].label
    robot = facts["robot"].label
    return [
        QAItem(
            question=f"What did {hero} and {partner} find in the station sprawl?",
            answer=f"They found {incident['sphere']}.",
        ),
        QAItem(
            question=f"What misunderstanding did {hero} have about {partner}?",
            answer=incident["misunderstanding"],
        ),
        QAItem(
            question="What evidence revealed what really happened?",
            answer=f"The evidence was {incident['clue']}.",
        ),
        QAItem(
            question=f"How did {hero} and {partner} reconcile?",
            answer=f"They listened to each other, apologized for their quick guesses, and worked together to repair the station. {partner} accepted the apology, so their trust returned.",
        ),
        QAItem(
            question=f"What did {robot} do in the adventure?",
            answer=f"{robot} was mapping the expanding station and accidentally nudged the batten while scanning a new corridor.",
        ),
        QAItem(
            question="How was the space station made safer?",
            answer=incident["action"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sphere?",
            answer="A sphere is a round solid shape in which every point on its surface is the same distance from its center.",
        ),
        QAItem(
            question="What is a batten?",
            answer="A batten is a narrow strip of wood or another material used to support, fasten, or cover something.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the wrong meaning or explanation from a situation or another person's words.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is making peace after a disagreement by listening, telling the truth, apologizing when needed, and rebuilding trust.",
        ),
        QAItem(
            question="Why should explorers use safety lines near an open hatch?",
            answer="A safety line helps keep explorers from drifting or falling into a dangerous opening while they work.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
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
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        state = []
        if meters:
            state.append(f"meters={meters}")
        if memes:
            state.append(f"memes={memes}")
        lines.append(f"  {entity.id:8} ({entity.type:16}) {' '.join(state)}")
    lines.append(f"  misunderstanding={world.facts.get('misunderstanding')}")
    lines.append(f"  reconciliation={world.facts.get('reconciliation')}")
    return "\n".join(lines)


ASP_RULES = r"""
% ASP twin for the story's central causal structure.
problem(sphere_drifting).
misunderstanding(friend_guess).
evidence(listened_and_observed).
repair(batten_and_hatch).
reconciliation(apology_and_trust).

solvable :- problem(sphere_drifting), evidence(listened_and_observed).
safe_station :- solvable, repair(batten_and_hatch).
good_story :- safe_station, reconciliation(apology_and_trust).

#show good_story/0.
#show safe_station/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("problem", "sphere_drifting"),
            asp.fact("misunderstanding", "friend_guess"),
            asp.fact("evidence", "listened_and_observed"),
            asp.fact("repair", "batten_and_hatch"),
            asp.fact("reconciliation", "apology_and_trust"),
        ]
    )


def asp_program(show: str = "#show good_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show good_story/0.\n#show safe_station/0."))
    names = {symbol.name for symbol in model}
    if {"good_story", "safe_station"} <= names:
        print("OK: ASP twin agrees that evidence, repair, and reconciliation make the station safe.")
        return 0
    print("MISMATCH: ASP twin did not find the expected safe story.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    tell(world)
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    return sample


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "Orin", "Pip", incident_id=0, opening_mode=0, dialogue_mode=0, repair_mode=0, ending_mode=0),
    StoryParams("Nova", "Pax", "Button", incident_id=1, opening_mode=2, dialogue_mode=1, repair_mode=1, ending_mode=1),
    StoryParams("Mira", "Sol", "Dot", incident_id=2, opening_mode=4, dialogue_mode=2, repair_mode=2, ending_mode=2),
    StoryParams("Tala", "Remy", "Mica", incident_id=3, opening_mode=5, dialogue_mode=3, repair_mode=3, ending_mode=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/0.\n#show safe_station/0."))
        return

    if args.verify:
        exit_code = asp_verify()
        if exit_code:
            sys.exit(exit_code)
        for seed in (3, 19, 77):
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip() or sample.world is None:
                print("MISMATCH: generated story was empty.")
                sys.exit(1)
        print("OK: generated stories exercise the repaired state.")
        return

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show good_story/0.\n#show safe_station/0."))
        shown = sorted(symbol.name for symbol in model if symbol.name in {"good_story", "safe_station"})
        print("\n".join(shown) if shown else "(none)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1")
        seen: set[str] = set()
        for offset in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero_name} and {sample.params.partner_name} on Luna station"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
