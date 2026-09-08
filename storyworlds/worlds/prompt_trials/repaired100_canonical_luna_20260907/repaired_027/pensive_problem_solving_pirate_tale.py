#!/usr/bin/env python3
"""
A small pensive pirate tale about solving a practical problem together.

The world tracks a pirate crew, a stranded boat, useful gear, and emotional
memes such as worry, patience, courage, and trust.  The story is driven by
state changes: a warning is missed, a problem appears, a clue suggests a
method, and careful problem solving restores a safe passage.
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
    region: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("distance", "tension", "secure", "wet", "blocked", "progress"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "patience", "courage", "trust", "relief", "pensive"):
            self.memes.setdefault(key, 0.0)


@dataclass
class Ship:
    name: str
    place: str
    weather: str


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    captain: str = "Captain Vale"
    ship: str = "the Thinking Star"
    problem: str = "free a small boat caught beyond the reef"
    pensive: bool = True
    problem_solving: bool = True
    pirate_tale: bool = True


NAMES = ["Luna", "Mara", "Pip", "Nell", "Tavi", "Bram", "Kiko", "Sable"]
CAPTAINS = ["Captain Vale", "Captain Reed", "Captain Sol", "Captain Mira"]
SHIPS = ["the Thinking Star", "the Blue Parrot", "the Salt Moon", "the Clever Gull"]
PROBLEMS = [
    "free a small boat caught beyond the reef",
    "carry a medicine chest across a flooded dock",
    "repair a torn signal sail before nightfall",
    "guide a drifting supply raft into the harbor",
]


@dataclass(frozen=True)
class Arc:
    premise: str
    warning: str
    mistake: str
    consequence: str
    clue: str
    question: str
    method: str
    result: str
    lesson: str
    ending: str


ARCS = [
    Arc(
        premise="The crew found a little rowboat wedged between two black reef stones.",
        warning="Do not pull against the tide until we know where the water is moving.",
        mistake="grab the nearest rope and haul with all her might",
        consequence="The rope tightened, but the boat swung sideways and its oar cracked against the reef.",
        clue="the seaweed on the stones leaned toward a narrow channel between the rocks",
        question="Which way is the water carrying the boat?",
        method="watch the seaweed, float a cork, and pull from the calm side with a second line",
        result="the boat slid through the narrow channel without another scrape",
        lesson="A hard problem often yields when a thoughtful sailor studies it before tugging.",
        ending="The rescued boat bobbed beside the ship, its unbroken oar shining in the sunset.",
    ),
    Arc(
        premise="A medicine chest stood on the far end of a dock covered by a rising sheet of rainwater.",
        warning="Test the boards before carrying anything heavy across.",
        mistake="dash onto the dock with the chest hugged tightly to her coat",
        consequence="One board dipped, and the chest nearly slipped into the brown water.",
        clue="three dry boards formed a straight path beside the thickest ropes",
        question="Where can the weight be shared safely?",
        method="lay a plank across the weak place, pass the chest hand to hand, and step only on the dry boards",
        result="the medicine reached the waiting villagers before the tide covered the dock",
        lesson="Problem solving means finding support instead of pretending a danger is not there.",
        ending="The chest rested dry beneath the village awning while rain tapped softly on the roof.",
    ),
    Arc(
        premise="The ship's signal sail tore just as a fishing crew searched for a safe harbor.",
        warning="Do not stitch the rip until the sail is held still.",
        mistake="climb into the whipping canvas with a needle and bright thread",
        consequence="The wind widened the tear and tangled the thread around the mast.",
        clue="the loose sail quieted whenever two crew members held its lower corners",
        question="How can we make the moving cloth still?",
        method="lower the sail, tie its corners, and patch the tear with a broad strip of spare canvas",
        result="the repaired signal rose clearly enough for the fishing crew to follow it home",
        lesson="A careful plan can turn a tangled task into a series of small safe steps.",
        ending="At dusk, the patched sail glowed like a red flag of welcome above the quiet harbor.",
    ),
    Arc(
        premise="A supply raft drifted toward the harbor wall with barrels of grain tied across its deck.",
        warning="Do not chase it from the bow; first learn what the wind and current are doing.",
        mistake="row straight after the raft while shouting for it to turn",
        consequence="The chase boat crossed the raft's path, and both boats began spinning in the current.",
        clue="a loose leaf circled slowly around the harbor marker before moving inward",
        question="Where will the current carry us if we stop fighting it?",
        method="wait outside the current, place a guiding line, and let the raft drift toward the calm water",
        result="the raft reached the pier without losing a single grain barrel",
        lesson="Patience is a tool: it gives a sailor time to see the path hidden by hurry.",
        ending="The grain barrels rolled onto the pier, and the quiet current carried the leaf away.",
    ),
]


def make_world(params: StoryParams) -> World:
    world = World(Ship(params.ship, "beside a small island", "a restless tide"))
    hero = world.add(Entity("hero", "character", "sailor", params.name, "main deck"))
    captain = world.add(Entity("captain", "character", "captain", params.captain, "quarterdeck"))
    boat = world.add(Entity("problem", "thing", "problem", "the waiting trouble", "near the reef"))
    rope = world.add(Entity("rope", "tool", "rope", "the spare rope", "coil locker", owner="crew"))
    cork = world.add(Entity("cork", "tool", "marker", "a floating cork", "galley shelf", owner="crew"))
    hero.memes["pensive"] = 1.0
    hero.memes["patience"] = 1.0
    captain.memes["trust"] = 1.0
    boat.meters["blocked"] = 1.0
    rope.meters["secure"] = 1.0
    cork.meters["secure"] = 1.0
    world.facts.update(hero=hero, captain=captain, problem=boat, rope=rope, cork=cork, params=params)
    return world


def tell(params: StoryParams) -> World:
    world = make_world(params)
    hero: Entity = world.facts["hero"]
    captain: Entity = world.facts["captain"]
    arc = ARCS[(params.seed or 0) % len(ARCS)]
    structure = ((params.seed or 0) // len(ARCS)) % 3

    world.say(
        f"On {world.ship.name}, a pirate ship anchored beside a small island, "
        f"{captain.label} trusted {hero.label} to watch the morning tide."
    )
    world.say(
        f"{hero.label} was pensive, which meant she was quiet and thinking carefully, "
        f"but she still wanted to prove she could {params.problem}."
    )
    world.para()
    world.say(arc.premise)
    world.say(f"{captain.label} called, \"{arc.warning}\"")

    hero.memes["worry"] += 1
    hero.memes["pensive"] += 1
    hero.meters["progress"] = 0.0
    if structure == 0:
        world.say(f"Before thinking it through, {hero.label} decided to {arc.mistake}.")
        world.say(arc.consequence)
    elif structure == 1:
        world.say(
            f"The warning made {hero.label} pause, but pride hurried her onward. "
            f"She chose to {arc.mistake}, and {arc.consequence}"
        )
    else:
        world.say(f"{hero.label} tried to {arc.mistake}. The result was plain: {arc.consequence}")

    hero.meters["blocked"] = 1.0
    hero.memes["worry"] += 1
    world.para()
    world.say(f"{hero.label} grew pensive again and noticed that {arc.clue}.")
    world.say(
        f"{captain.label} asked, \"{arc.question}\" "
        f"{hero.label} answered, \"I do not know yet, but I can look for the answer.\""
    )
    world.say(
        f"Instead of pushing harder, {hero.label} chose to {arc.method}."
    )

    hero.memes["patience"] += 2
    hero.memes["courage"] += 1
    hero.memes["trust"] += 1
    captain.memes["trust"] += 1
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 2.0)
    hero.meters["blocked"] = 0.0
    hero.meters["progress"] = 1.0
    hero.meters["secure"] = 1.0
    world.say(f"Step by step, the plan worked: {arc.result}.")
    world.say(
        f"{captain.label} smiled. \"You solved it by asking what the problem was telling you,\" "
        f"the captain said. \"And by listening,\" {hero.label} replied."
    )
    world.para()
    world.say(f"{hero.label} learned that {arc.lesson}")
    world.say(arc.ending)

    world.facts.update(arc=arc, resolved=True, clue=arc.clue, method=arc.method, result=arc.result)
    return world


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    hero: Entity = world.facts["hero"]
    captain: Entity = world.facts["captain"]
    arc: Arc = world.facts["arc"]
    return [
        QAItem(
            f"Who is the pensive sailor in the pirate tale aboard {params.ship}?",
            f"{hero.label} is the pensive sailor. She thinks carefully about a difficult problem while sailing with {captain.label} aboard {params.ship}.",
        ),
        QAItem(
            f"What problem did {hero.label} face near {params.ship}?",
            f"{arc.premise} The problem made the crew need a safe plan rather than a hurried guess.",
        ),
        QAItem(
            f"What mistake did {hero.label} make before using problem solving?",
            f"{hero.label} chose to {arc.mistake}. This made the situation worse because {arc.consequence}",
        ),
        QAItem(
            f"What clue helped {hero.label} solve the trouble?",
            f"{hero.label} noticed that {arc.clue}. That clue helped her ask, \"{arc.question}\"",
        ),
        QAItem(
            f"How did {hero.label} solve the problem with {captain.label}?",
            f"{hero.label} chose to {arc.method}. As a result, {arc.result}",
        ),
        QAItem(
            f"What lesson did {hero.label} learn about solving problems?",
            f"{arc.lesson} Her pensive pause helped her replace a rushed action with a careful plan.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does pensive mean?", "Pensive means quietly thoughtful, especially when someone is considering a problem."),
        QAItem("What is problem solving?", "Problem solving means understanding a difficulty, finding useful clues, choosing a plan, and checking whether the plan works."),
        QAItem("Why do sailors watch the tide?", "Sailors watch the tide because moving water can change where boats travel and how safely they can reach shore."),
        QAItem("Why is it useful to make a plan before pulling or carrying something?", "A plan helps people notice danger, share the work, and choose a safer method."),
    ]


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    arc: Arc = world.facts["arc"]
    return [
        f"Write a pensive pirate tale about {params.name} solving this problem: {params.problem}.",
        f"Tell a child-friendly pirate story aboard {params.ship} where a sailor notices that {arc.clue}.",
        f"Write a problem-solving adventure in which {params.name} replaces a hurried mistake with this method: {arc.method}.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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
        lines.append(
            f"  {entity.id:8} ({entity.type:9}) "
            f"meters={meters} memes={memes} region={entity.region}"
        )
    lines.append(f"  resolved={world.facts.get('resolved', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
problem(hero) :- stranded(hero).
clue_found(hero) :- problem(hero), observes(hero).
plan(hero) :- clue_found(hero), patient(hero).
resolved(hero) :- plan(hero), uses_safe_method(hero).
#show problem/1.
#show clue_found/1.
#show plan/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("stranded", "hero"),
            asp.fact("observes", "hero"),
            asp.fact("patient", "hero"),
            asp.fact("uses_safe_method", "hero"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    actual = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    expected = {"problem/1", "clue_found/1", "plan/1", "resolved/1"}
    if actual != expected:
        print("MISMATCH:", sorted(actual), "expected", sorted(expected))
        return 1
    for seed in range(8):
        sample = generate(StoryParams(seed=seed))
        if not sample.world or not sample.world.facts.get("resolved"):
            print("MISMATCH: generated story did not resolve", seed)
            return 1
        if "pensive" not in sample.story.lower():
            print("MISMATCH: pensive state missing", seed)
            return 1
    print("OK: ASP twin, generated stories, and resolutions agree.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A pensive pirate problem-solving tale.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--captain", choices=CAPTAINS)
    parser.add_argument("--ship", choices=SHIPS)
    parser.add_argument("--problem", choices=PROBLEMS)
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
        name=args.name or rng.choice(NAMES),
        captain=args.captain or rng.choice(CAPTAINS),
        ship=args.ship or rng.choice(SHIPS),
        problem=args.problem or rng.choice(PROBLEMS),
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
    StoryParams(seed=0, name="Luna", captain="Captain Vale", ship="the Thinking Star", problem=PROBLEMS[0]),
    StoryParams(seed=1, name="Mara", captain="Captain Reed", ship="the Blue Parrot", problem=PROBLEMS[1]),
    StoryParams(seed=2, name="Pip", captain="Captain Sol", ship="the Salt Moon", problem=PROBLEMS[2]),
    StoryParams(seed=3, name="Nell", captain="Captain Mira", ship="the Clever Gull", problem=PROBLEMS[3]),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(" ".join(str(symbol) for symbol in asp.one_model(asp_program())))
        return

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples: list[StorySample] = []
        seen: set[str] = set()
        for offset in range(max(50, args.n * 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if not samples:
        raise StoryError("No stories could be generated.")

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
