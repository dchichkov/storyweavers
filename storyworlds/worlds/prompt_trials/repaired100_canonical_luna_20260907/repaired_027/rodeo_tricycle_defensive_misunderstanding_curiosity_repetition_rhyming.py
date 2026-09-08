#!/usr/bin/env python3
"""
A gentle rhyming rodeo story about a child, a tricycle, and a defensive
misunderstanding. Curiosity and repetition turn a noisy scare into friendship.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

for _parent in Path(__file__).resolve().parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        sys.path.insert(0, str(_parent / "storyworlds"))
        break
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def __post_init__(self) -> None:
        for key in ("speed", "balance", "noise", "distance", "safe"):
            self.meters.setdefault(key, 0.0)
        for key in ("curiosity", "worry", "defensiveness", "trust", "relief"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    rider: str = "Luna"
    rodeo_name: str = "Sunbeam Rodeo"
    tricycle_color: str = "red"
    animal: str = "pony"
    rhyme: bool = True
    defensive: bool = True


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


NAMES = ["Luna", "Milo", "Nora", "Pip", "Tessa", "Remy"]
RODEOS = ["Sunbeam Rodeo", "Clover Rodeo", "Moon-Dust Rodeo", "Golden Gate Rodeo"]
COLORS = ["red", "blue", "yellow", "green"]
ANIMALS = ["pony", "goat", "calf", "donkey"]


@dataclass(frozen=True)
class Arc:
    opening: str
    warning: str
    action: str
    noise: str
    clue: str
    question: str
    discovery: str
    repair: str
    lesson: str
    ending: str


ARCS = [
    Arc(
        opening="At the county rodeo, bright flags snapped above the dusty ring.",
        warning="Please keep your tricycle behind the white rail while the pony passes.",
        action="rolled the tricycle toward the ring to get a closer look",
        noise="The tricycle bell rang again and again: ring-ring, ring-ring!",
        clue="the pony's ears flattened whenever the bell rang",
        question="Why did you keep ringing when I asked you to stop?",
        discovery="the pony was not angry at Luna at all; the pony was frightened by the bright bell",
        repair="Luna parked the tricycle, covered its bell with a soft scarf, and practiced quiet rolling beside the rail",
        lesson="Curiosity should ask what a frightened friend needs before it asks for another show",
        ending="When the pony trotted past, the tricycle stayed still, and one calm hoofbeat answered one quiet smile.",
    ),
    Arc(
        opening="The rodeo band played a bouncy tune while the little tricycle waited near the gate.",
        warning="Leave the gate clear until the riders have finished their turn.",
        action="pedaled in circles beside the gate to copy the band",
        noise="The front wheel squeaked, squeaked, squeaked across the boards.",
        clue="the rider kept looking toward the narrow gate",
        question="Did you think I wanted you to race through the gate?",
        discovery="the rider was protecting a tired calf, not scolding Luna",
        repair="Luna repeated the warning aloud, backed her tricycle away, and helped place a bright cone by the gate",
        lesson="Repeating a warning can make its meaning clearer when a busy place feels confusing",
        ending="The gate stood wide and clear, and the calf walked through as the band played a softer tune.",
    ),
    Arc(
        opening="Sunset painted the rodeo fence orange while a small donkey practiced gentle turns.",
        warning="Watch from the fence, because sudden wheels can startle a careful animal.",
        action="zigzagged her tricycle to show how quickly its wheels could turn",
        noise="The tires bumped the boards with a thump-thump-thump.",
        clue="the donkey stepped backward each time the tricycle came near",
        question="Are you trying to chase me away?",
        discovery="the donkey believed the zigzagging wheels were chasing it",
        repair="Luna stopped, set both feet down, and repeated the same slow turn far from the fence",
        lesson="A curious experiment becomes kinder when we repeat it slowly enough for others to understand",
        ending="The donkey lowered its head, and Luna's tricycle made one peaceful circle beneath the orange sky.",
    ),
    Arc(
        opening="Before the rodeo began, a blue ribbon fluttered from the tricycle's handlebar.",
        warning="The ribbon is for decoration, so do not wave it near the pony's face.",
        action="lifted the ribbon high whenever the pony came around",
        noise="The ribbon snapped like a tiny flag in the wind.",
        clue="the pony watched the ribbon instead of watching the safe path",
        question="Why are you waving that thing at me?",
        discovery="the pony thought the ribbon was a signal to run, not a decoration",
        repair="Luna lowered the ribbon, explained its purpose, and repeated a quiet hand wave from behind the rail",
        lesson="Curiosity is safest when we explain our signals instead of expecting everyone to guess",
        ending="The ribbon rested on the handlebar, while the pony and Luna shared the same slow wave.",
    ),
]


def make_world(params: StoryParams) -> World:
    world = World()
    rider = world.add(Entity("rider", "character", "child", params.rider, location="rodeo yard"))
    pony = world.add(Entity("animal", "animal", params.animal, f"the {params.animal}", location="rodeo ring"))
    cycle = world.add(Entity("cycle", "vehicle", "tricycle", f"{params.tricycle_color} tricycle", location="rodeo rail"))
    rider.memes["curiosity"] = 1.0
    rider.memes["trust"] = 1.0
    pony.memes["defensiveness"] = 1.0
    pony.memes["worry"] = 1.0
    cycle.meters["balance"] = 1.0
    cycle.meters["safe"] = 1.0
    return world


def tell(params: StoryParams) -> World:
    if not params.rider.strip():
        raise StoryError("rider must not be empty")
    if params.tricycle_color not in COLORS:
        raise StoryError("tricycle_color must be one of the registered colors")
    if params.animal not in ANIMALS:
        raise StoryError("animal must be one of the registered rodeo animals")

    world = make_world(params)
    rider = world.get("rider")
    animal = world.get("animal")
    cycle = world.get("cycle")

    value = params.seed
    if value is None:
        value = sum(ord(ch) for ch in f"{params.rider}|{params.rodeo_name}|{params.tricycle_color}|{params.animal}")
    arc = ARCS[value % len(ARCS)]
    pattern = value % 3

    world.say(
        f"At the {params.rodeo_name}, {params.rider} brought a {params.tricycle_color} "
        f"tricycle and a pocket full of curiosity."
    )
    world.say(f"{arc.opening} {params.rider} wanted to understand every hoofbeat, wheel-turn, and waving flag.")
    world.para()
    world.say(f"A rodeo helper called, \"{arc.warning}\"")
    rider.memes["curiosity"] += 1.0
    rider.memes["defensiveness"] += 1.0

    if pattern == 0:
        world.say(f"But {params.rider} misunderstood and {arc.action}.")
        world.say(arc.noise)
    elif pattern == 1:
        world.say(f"{params.rider} repeated the warning softly, then misunderstood it and {arc.action}.")
        world.say(f"{arc.noise} The busy rodeo made the meaning hard to hear.")
    else:
        world.say(f"Curiosity tugged harder than caution. {params.rider} {arc.action}, and {arc.noise.lower()}")
    rider.meters["noise"] = 1.0
    rider.meters["distance"] = 0.0
    animal.meters["distance"] = 0.0
    animal.memes["defensiveness"] += 1.0
    animal.memes["worry"] += 1.0

    world.para()
    world.say(f"Then {params.rider} noticed that {arc.clue}.")
    world.say(f"The {animal.type} stood defensive, not mean, with worry tucked beneath its guard.")
    world.say(f"{animal.label} asked, \"{arc.question}\"")
    world.say(f"{params.rider} answered, \"I thought you wanted me to come closer. Now I see that {arc.clue}.\"")
    world.say(f"That back-and-forth changed the plan: {params.rider} decided to stop, listen, and learn.")
    rider.memes["curiosity"] += 1.0
    rider.memes["defensiveness"] = 0.0
    rider.memes["trust"] += 1.0

    world.para()
    world.say(f"With a calm breath, {params.rider} discovered that {arc.discovery}.")
    world.say(f"{params.rider} {arc.repair}.")
    cycle.meters["noise"] = 0.0
    cycle.meters["distance"] = 1.0
    cycle.meters["safe"] = 2.0
    animal.memes["worry"] = 0.0
    animal.memes["defensiveness"] = 0.0
    animal.memes["trust"] += 1.0
    rider.memes["relief"] = 1.0
    world.say(f"Once more, {params.rider} repeated the safe choice: \"Stop, listen, then roll.\"")
    world.say(arc.lesson)
    world.say(arc.ending)

    world.facts.update(
        params=params,
        rider=rider,
        animal=animal,
        cycle=cycle,
        arc=arc,
        resolved=True,
        misunderstanding=True,
        repeated=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    rider: Entity = world.facts["rider"]
    animal: Entity = world.facts["animal"]
    cycle: Entity = world.facts["cycle"]
    arc: Arc = world.facts["arc"]
    return [
        QAItem(
            f"Who rode the {cycle.label} at the {p.rodeo_name}?",
            f"{rider.label} rode the {cycle.label} at the {p.rodeo_name} and wanted to understand the busy rodeo.",
        ),
        QAItem(
            f"What misunderstanding caused trouble between {rider.label} and {animal.label}?",
            f"{rider.label} misunderstood the warning and {arc.action}. The repeated movement or sound made {animal.label} feel chased or frightened.",
        ),
        QAItem(
            f"Why was {animal.label} defensive?",
            f"{animal.label} was defensive because {arc.clue}. The animal was worried, not trying to be unkind.",
        ),
        QAItem(
            f"What did {rider.label} notice through curiosity?",
            f"{rider.label} noticed that {arc.clue}, which helped explain the animal's defensive behavior.",
        ),
        QAItem(
            f"How did repetition help solve the problem at the rodeo?",
            f"{rider.label} repeated the safe choice and the words \"Stop, listen, then roll.\" Repetition made the new plan clear and helped everyone stay calm.",
        ),
        QAItem(
            f"What did {rider.label} do to repair the misunderstanding?",
            f"{rider.label} {arc.repair}. This gave {animal.label} space and replaced the confusing action with a gentle one.",
        ),
        QAItem(
            f"What lesson did {rider.label} learn?",
            f"{arc.lesson} The lesson mattered because curiosity became kind only after {rider.label} listened to the worried animal.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a rodeo?", "A rodeo is an event where people and animals demonstrate riding, roping, or other careful skills in a fenced arena."),
        QAItem("What is a tricycle?", "A tricycle is a small cycle with three wheels, which helps a young rider balance while learning to pedal."),
        QAItem("What does defensive mean?", "Defensive means ready to protect oneself because something feels threatening or unsafe."),
        QAItem("Why is curiosity useful?", "Curiosity is useful because it encourages people to ask questions and learn what is really happening."),
        QAItem("Why can repetition help?", "Repetition can help because hearing or practicing something again makes a rule or skill easier to remember."),
    ]


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    arc: Arc = world.facts["arc"]
    return [
        f"Write a rhyming rodeo story about {p.rider}'s {p.tricycle_color} tricycle and a defensive {p.animal}.",
        f"Tell a child-friendly story where a misunderstanding at the {p.rodeo_name} is solved through curiosity and repetition.",
        f"Write a rhyming tale using this clue: {arc.clue}. Show how listening changes the action.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {text}" for i, text in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id:8} ({entity.type:10}) location={entity.location!r} meters={meters} memes={memes}")
    lines.append(f"  misunderstanding={world.facts.get('misunderstanding')} repeated={world.facts.get('repeated')} resolved={world.facts.get('resolved')}")
    return "\n".join(lines)


ASP_RULES = r"""
misunderstanding(rider) :- curious(rider), defensive(animal), noisy(tricycle).
questioned(rider) :- misunderstanding(rider), notices_clue(rider).
resolved(rider) :- questioned(rider), repeats_safe_choice(rider), listens(rider).
#show misunderstanding/1.
#show questioned/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("curious", "rider"),
        asp.fact("defensive", "animal"),
        asp.fact("noisy", "tricycle"),
        asp.fact("notices_clue", "rider"),
        asp.fact("repeats_safe_choice", "rider"),
        asp.fact("listens", "rider"),
    ])


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    found = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    expected = {"misunderstanding/1", "questioned/1", "resolved/1"}
    if found == expected:
        for seed in range(8):
            sample = generate(StoryParams(seed=seed))
            if not sample.story or "tricycle" not in sample.story or "rodeo" not in sample.story:
                print("MISMATCH: generated story exercise failed")
                return 1
        print("OK: ASP twin matches the rodeo tricycle story logic.")
        return 0
    print("MISMATCH:", sorted(found), "expected", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A rhyming rodeo tricycle story world.")
    parser.add_argument("--rider", choices=NAMES)
    parser.add_argument("--rodeo-name", choices=RODEOS)
    parser.add_argument("--tricycle-color", choices=COLORS)
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--seed", type=int, default=None)
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
    return StoryParams(
        seed=args.seed,
        rider=args.rider or rng.choice(NAMES),
        rodeo_name=args.rodeo_name or rng.choice(RODEOS),
        tricycle_color=args.tricycle_color or rng.choice(COLORS),
        animal=args.animal or rng.choice(ANIMALS),
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


CURATED = [
    StoryParams(seed=0, rider="Luna", rodeo_name="Sunbeam Rodeo", tricycle_color="red", animal="pony"),
    StoryParams(seed=1, rider="Milo", rodeo_name="Clover Rodeo", tricycle_color="blue", animal="calf"),
    StoryParams(seed=2, rider="Nora", rodeo_name="Moon-Dust Rodeo", tricycle_color="yellow", animal="donkey"),
    StoryParams(seed=3, rider="Pip", rodeo_name="Golden Gate Rodeo", tricycle_color="green", animal="goat"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        print(" ".join(str(symbol) for symbol in asp.one_model(asp_program())))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(args.n, 1) * 50):
            if len(samples) >= args.n:
                break
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
