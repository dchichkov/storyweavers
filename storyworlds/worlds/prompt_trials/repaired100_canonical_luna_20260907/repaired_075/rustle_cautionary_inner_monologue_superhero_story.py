#!/usr/bin/env python3
"""
A small superhero storyworld about a brave child, a mysterious rustle, and
the courage to pause before rushing into danger.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""
    protected: bool = False

    def __post_init__(self) -> None:
        for key in ("distance", "danger", "visibility", "noise"):
            self.meters.setdefault(key, 0.0)
        for key in ("fear", "courage", "curiosity", "trust", "relief"):
            self.memes.setdefault(key, 0.0)


@dataclass
class Setting:
    name: str
    affordances: set[str]
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

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


@dataclass
class StoryParams:
    name: str
    animal: str
    mentor: str
    setting: str = "the moonlit city park"
    threat: str = "a lost firefly drone"
    telling: int = 0
    seed: Optional[int] = None


HERO_NAMES = ["Luna", "Mara", "Zoe", "Nia", "Tess"]
ANIMALS = ["rabbit", "fox", "cat", "mouse", "squirrel"]
MENTORS = ["Captain Sol", "Aunt Nova", "Coach Ray", "Grandma Star"]

SCENARIOS = [
    {
        "place": "the moonlit city park",
        "premise": "Luna had promised to watch the park's tiny beacon while the grown-up heroes repaired the fountain lights",
        "goal": "bring the beacon back to its charging station",
        "problem": "a rustle moved inside the dark hedge beside the shortcut",
        "warning": "A hero does not leap toward a sound before finding out what made it",
        "clue": "the leaves rustled in a steady rhythm, and a faint blue blink shone beneath them",
        "memory": "last month, a frightened hero had chased a rustling cape and nearly knocked over a sleeping gardener's cart",
        "action": "raised her lantern, called out, and waited behind the bright path marker",
        "reveal": "a little service robot had become tangled in a vine and was trying to signal for help",
        "result": "freed the robot without stepping into the thorny hedge",
        "lesson": "bravery is not charging first; bravery is staying calm long enough to choose a safe way to help",
        "ending": "The repaired beacon glowed above the park, while the once-scary hedge gave one friendly rustle in the breeze",
    },
    {
        "place": "the rooftop rescue garden",
        "premise": "Mara was guarding a tray of superhero seedlings during a windy evening patrol",
        "goal": "carry the seedlings to the warm greenhouse door",
        "problem": "a sharp rustle came from behind the tall solar panels",
        "warning": "A cape can make a hero fast, but it cannot make an unknown place safe",
        "clue": "the rustle came in short bursts, followed by the soft clink of a metal buckle",
        "memory": "once, Mara had rushed after a rustling banner and slipped on a loose roof tile",
        "action": "stopped at the painted safety line, switched on her beacon, and asked her mentor what the sound might mean",
        "reveal": "a delivery pigeon had caught its harness on a loose panel strap",
        "result": "guided the pigeon out with a long garden pole instead of climbing behind the panels",
        "lesson": "a careful pause can protect both the rescuer and the creature being rescued",
        "ending": "The seedlings stood safely under glass, and the pigeon fluttered away beneath a sky full of patient stars",
    },
    {
        "place": "the old subway hero station",
        "premise": "Zoe was carrying the emergency map when the station lights flickered during a practice drill",
        "goal": "deliver the map to the waiting rescue team",
        "problem": "a rustle echoed through the supply tunnel, making the shortest route seem dangerous",
        "warning": "Do not run into a tunnel just because someone needs you quickly",
        "clue": "the rustle repeated whenever the ventilation fan turned on",
        "memory": "Zoe remembered a time when she had followed a strange sound and found only a loose curtain flapping near an open stairwell",
        "action": "stood still, counted the echoes, and asked the rescue team to shine their lamp down the tunnel",
        "reveal": "a stack of paper training capes was wobbling beside the fan",
        "result": "secured the capes and delivered the map along the well-lit platform",
        "lesson": "understanding a sound is often safer than fighting the fear it creates",
        "ending": "The drill ended with every hero accounted for, and the paper capes rested quietly in their box",
    },
    {
        "place": "the rainbow bridge lookout",
        "premise": "Tess was keeping watch over the bridge while a storm rolled beyond the hills",
        "goal": "warn travelers about a fallen branch near the crossing",
        "problem": "a rustle rose from the tall grass beside the warning bell",
        "warning": "A real hero checks the ground before stepping into a hidden place",
        "clue": "the grass bent in a narrow line toward the bell, but no footprints led away",
        "memory": "Tess remembered mistaking a rolling trash can for a villain during her first patrol",
        "action": "used the bridge mirror to inspect the grass from the path and called for her mentor",
        "reveal": "a family of hedgehogs was moving beneath the grass toward a dry stone wall",
        "result": "waited until the hedgehogs crossed and then rang the bell from the clear path",
        "lesson": "being cautious gives every small traveler room to be safe",
        "ending": "The warning bell rang across the rainbow bridge, and the hedgehogs disappeared into their cozy wall",
    },
]

OPENINGS = [
    "{name} was a young {animal} with a silver mask, a bright cape, and a promise to protect people without pretending to know everything.",
    "Every superhero in the city admired {name}, the young {animal} who could hear a pin drop beneath a parade drum.",
    "{name} the {animal} wore a red cape, but the strongest part of {name}'s hero gear was a habit of careful listening.",
    "At sunset, {name} checked the mask strap, the lantern battery, and the promise every hero made before patrol.",
]

INNER_THOUGHTS = [
    '"That rustle sounds scary," {name} thought, "but scary does not tell me what to do. I need more evidence."',
    '"My cape wants to rush," {name} told herself, "but my best hero choice is to pause and look."',
    '"If I charge in, I may become part of the problem," {name} thought. "A safe helper notices first."',
    '"I can be brave and careful at the same time," {name} reminded herself.',
]

@dataclass
class Gear:
    label: str
    purpose: str
    protects: set[str]


GEAR = [
    Gear("a signal lantern", "show what was nearby without entering danger", {"darkness", "distance"}),
    Gear("a bridge mirror", "look around a corner from the safe path", {"hidden_space", "distance"}),
    Gear("a long garden pole", "help from outside a risky area", {"thorns", "height"}),
]


def validate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("A hero needs a name.")
    if params.animal not in ANIMALS:
        raise StoryError(f"Unknown hero animal: {params.animal}.")
    if not 0 <= params.telling < len(SCENARIOS):
        raise StoryError("The telling must select a real cautionary scenario.")


def tell(params: StoryParams) -> World:
    validate(params)
    incident = SCENARIOS[params.telling]
    setting = Setting(
        name=incident["place"],
        affordances={"listen", "wait", "signal", "ask_for_help"},
        meters={"visibility": 0.4, "danger": 0.7},
        memes={"mystery": 1.0},
    )
    world = World(setting)
    hero = world.add(Entity("hero", "character", params.name, params.animal, location=incident["place"]))
    mentor = world.add(Entity("mentor", "character", params.mentor, "mentor", location=incident["place"]))
    threat = world.add(Entity("rustle_source", "thing", params.threat, "unknown", location=incident["place"]))
    lantern = world.add(Entity("lantern", "gear", "signal lantern", "tool", location="hero"))
    lantern.protected = True

    rng = random.Random(params.seed if params.seed is not None else 0)
    opening = OPENINGS[params.telling % len(OPENINGS)].format(name=params.name, animal=params.animal)
    thought = INNER_THOUGHTS[rng.randrange(len(INNER_THOUGHTS))].format(name=params.name)

    world.say(opening)
    world.say(
        f"In {incident['place']}, {incident['premise']}. "
        f"The goal was to {incident['goal']}."
    )
    world.para()
    world.say(f"Then {incident['problem']}.")
    world.say(f"{params.name} took one quick step toward the sound, but {params.mentor} called, \"{incident['warning']}\"")
    world.say(f'"I hear you," {params.name} answered. "I will not rush in."')
    world.say(thought)
    hero.memes["fear"] = 1.0
    hero.memes["curiosity"] = 1.0
    hero.meters["danger"] = 1.0
    world.para()
    world.say(f"{params.name} remembered how {incident['memory']}.")
    world.say(f"That memory did not make {params.name} helpless. It made {params.name} notice that {incident['clue']}.")
    world.say(f'"Can you help me check from here?' {params.name} asked.')
    world.say(f'"Yes," said {params.mentor}. "A question can be superhero gear too."')
    hero.memes["trust"] = 1.0
    world.para()
    world.say(f"{params.name} {incident['action']}.")
    world.say(f"The careful check revealed that {incident['reveal']}.")
    world.say(f"{params.name} {incident['result']}.")
    hero.memes["fear"] = 0.0
    hero.memes["courage"] = 1.0
    hero.memes["relief"] = 1.0
    hero.meters["danger"] = 0.0
    world.say(f"The lesson was clear: {incident['lesson']}.")
    world.say(f"{incident['ending']}.")

    world.facts.update({
        "hero": hero,
        "mentor": mentor,
        "threat": threat,
        "incident": incident,
        "gear": lantern,
        "safe_resolution": True,
        "rustle": True,
        "inner_monologue": thought,
    })
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    incident = f["incident"]
    return [
        f"Write a cautionary superhero story about {hero.label} hearing this rustle: {incident['problem']}.",
        f"Include an inner monologue in which {hero.label} pauses, gathers evidence, and chooses a safe rescue.",
        f"End with the concrete image: {incident['ending']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mentor: Entity = f["mentor"]
    incident = f["incident"]
    return [
        QAItem("Who was the superhero in the story?", f"The superhero was {hero.label}, a young {hero.type} who used careful listening as part of hero work."),
        QAItem("What caused the rustle?", f"The rustle came from {incident['reveal']}."),
        QAItem("What did the mentor warn?", f"{mentor.label} warned, \"{incident['warning']}\""),
        QAItem("What did the hero remember?", f"{hero.label} remembered how {incident['memory']}."),
        QAItem("How did the hero solve the problem?", f"{hero.label} {incident['action']} Then {hero.label} {incident['result']}."),
        QAItem("What lesson did the hero learn?", f"The lesson was that {incident['lesson']}."),
        QAItem("What ending image proves the plan worked?", f"{incident['ending']}"),
    ]


KNOWLEDGE = [
    QAItem("What is a rustle?", "A rustle is a soft, quick sound made when leaves, cloth, paper, or grass moves."),
    QAItem("What is a cautionary story?", "A cautionary story shows a danger or mistake and teaches a safer choice."),
    QAItem("What is an inner monologue?", "An inner monologue is a character's private thoughts written inside the story."),
    QAItem("Why should a hero pause before rushing toward a strange sound?", "Pausing gives the hero time to gather evidence, avoid danger, and choose a helpful action."),
    QAItem("What makes someone brave?", "Someone is brave when they face a difficult moment and make a wise, caring choice."),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id}: type={entity.type}, location={entity.location}, "
            f"meters={meters}, memes={memes}"
        )
    lines.append(f"  setting={world.setting.name}")
    lines.append(f"  affordances={sorted(world.setting.affordances)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("sound", "rustle"),
        asp.fact("hero", "listener"),
        asp.fact("skill", "pause"),
        asp.fact("skill", "signal"),
        asp.fact("skill", "ask_for_help"),
        asp.fact("danger", "unknown_source"),
        asp.fact("requires", "unknown_source", "pause"),
        asp.fact("safe_action", "pause"),
        asp.fact("safe_action", "signal"),
        asp.fact("safe_action", "ask_for_help"),
    ])


ASP_RULES = r"""
cautious_response(S) :- sound(S), requires(unknown_source, pause), safe_action(pause).
cautious_response(S) :- sound(S), safe_action(signal).
cautious_response(S) :- sound(S), safe_action(ask_for_help).
valid :- hero(listener), cautious_response(rustle).
#show cautious_response/1.
#show valid/0.
"""


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    cautious = set(asp.atoms(model, "cautious_response"))
    valid = bool(asp.atoms(model, "valid"))
    if cautious == {("rustle",)} and valid:
        print("OK: ASP gate agrees with Python reasonableness.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    print("ASP cautious responses:", sorted(cautious))
    print("ASP valid:", valid)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rustle cautionary superhero storyworld")
    parser.add_argument("--name", choices=HERO_NAMES)
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--mentor", choices=MENTORS)
    parser.add_argument("--setting")
    parser.add_argument("--threat")
    parser.add_argument("--telling", type=int, choices=range(len(SCENARIOS)))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(HERO_NAMES),
        animal=args.animal or rng.choice(ANIMALS),
        mentor=args.mentor or rng.choice(MENTORS),
        setting=args.setting or "the moonlit city park",
        threat=args.threat or "a lost firefly drone",
        telling=args.telling if args.telling is not None else rng.randrange(len(SCENARIOS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index in range(len(SCENARIOS)):
            params = StoryParams(
                name=HERO_NAMES[index % len(HERO_NAMES)],
                animal=ANIMALS[index % len(ANIMALS)],
                mentor=MENTORS[index % len(MENTORS)],
                telling=index,
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
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
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
