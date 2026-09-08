#!/usr/bin/env python3
"""A child-facing mystery about a helpful mechanism, friendship, and a careful twist."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Scene:
    place: str
    mood: str
    weather: str


@dataclass
class StoryParams:
    place: str
    mechanism: str
    name: str
    friend: str
    witness: str
    case: str = ""
    route: str = ""
    seed: Optional[int] = None


@dataclass(frozen=True)
class MechanismCase:
    missing: str
    suspicion: str
    test: str
    failed: str
    clue: str
    truth: str
    repair: str
    lesson: str
    ending: str


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "clocktower": Scene("the clock tower", "echoing", "a cool morning breeze"),
    "workshop": Scene("the village workshop", "sawdusty", "bright afternoon light"),
    "boathouse": Scene("the boathouse", "watery", "a restless lake wind"),
    "greenhouse": Scene("the greenhouse", "leafy", "soft rain on the glass"),
}

MECHANISMS = {
    "counterweight": "a wooden counterweight that lifted the bell rope",
    "waterwheel": "a small waterwheel that turned a garden pump",
    "gearbox": "a brass gearbox that opened a painted gate",
    "wind_vane": "a wind vane that pointed a weather flag",
    "pulley": "a rope-and-pulley lift for baskets",
    "ratchet": "a clicking ratchet that held a loading ramp",
}

FRIENDS = {"Mina": "girl", "Theo": "boy", "Iris": "girl", "Ned": "boy"}
WITNESSES = {"goat": "goat", "crow": "crow", "puppy": "puppy", "otter": "otter"}

CASES = {
    "bell_rope": MechanismCase(
        "the brass bell's blue ribbon",
        "the goat had been beside the bell when the ribbon vanished",
        "counted the rope pulls and watched the counterweight rise",
        "the weight rose even when the bell rope was untouched",
        "a fresh scrape marked the pulley groove above the beam",
        "a loose peg had caught the ribbon and pulled it upward when the counterweight moved",
        "lowered the weight safely, freed the ribbon, and replaced the worn peg",
        "a nearby witness is not proof of blame",
        "the blue ribbon fluttered below a bell that rang only when a friend pulled its rope",
    ),
    "waterwheel_key": MechanismCase(
        "the tiny key that unlocked the pump box",
        "the otter's wet tracks circled the box",
        "blocked the wheel briefly and checked whether the key still moved",
        "the key slid farther when the wheel stopped",
        "a bright thread was wound around the wheel's hidden axle",
        "the thread had turned the axle and carried the key beneath the floor grate",
        "lifted the grate with a hook, recovered the key, and covered the axle",
        "a test should change one part of a mechanism at a time",
        "the waterwheel turned freely while the key rested in its labeled wooden cup",
    ),
    "painted_gate": MechanismCase(
        "the painted gate's welcome sign",
        "the crow had been perched on the gate before the sign fell",
        "matched the sign's scratches with the gearbox teeth",
        "the scratches did not match the smooth teeth",
        "a bent spring sat behind the lower hinge",
        "the spring had snapped back and nudged the sign loose when the gate closed",
        "straightened the hinge with an adult's help and fitted a new spring",
        "a familiar suspect can distract from a hidden mechanical cause",
        "the welcome sign swung gently above the gate as friends entered together",
    ),
    "weather_flag": MechanismCase(
        "the red weather flag",
        "the puppy had carried a red cloth near the wind vane",
        "turned the vane by hand and watched the flag's cord",
        "the cord slipped even when the vane stood still",
        "a shiny burr had snagged the cord inside the wooden housing",
        "the burr had been left by a hurried repair and slowly unraveled the knot",
        "smoothed the housing, retied the cord, and checked the flag in two winds",
        "a quick repair can create a later mystery",
        "the red flag pointed east while the repaired vane clicked calmly in the breeze",
    ),
    "basket_lift": MechanismCase(
        "the basket of ripe pears",
        "the goat's horn marks appeared beside the pulley platform",
        "lifted an empty basket and measured where the rope changed direction",
        "the empty basket stopped halfway, so the rope was not being pulled evenly",
        "a small stone was wedged in the pulley wheel",
        "the stone had tipped the basket toward the goat's pen and spilled the pears",
        "removed the stone, tied a guide rope, and shared the pears with the goat",
        "a small hidden obstacle can make a large problem",
        "the pulley raised a full basket smoothly while pear leaves rustled below",
    ),
    "loading_ramp": MechanismCase(
        "the wooden loading ramp",
        "the crow's feathers lay beside the ramp's clicking handle",
        "tested the ratchet with a short board before moving the heavy ramp",
        "the handle clicked backward instead of locking forward",
        "a missing tooth lay beneath a folded work cloth",
        "the broken tooth had let the ramp slide when the cloth caught the handle",
        "blocked the ramp, replaced the tooth, and marked the safe testing line",
        "safe testing protects both friends and tools",
        "the ramp held firm as friends rolled the empty cart across its new safe line",
    ),
}

ROUTES = (
    "clue_first",
    "dialogue_first",
    "test_first",
    "map_first",
    "quiet_first",
    "two_theories",
)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mystery world about friendship and a tricky mechanism.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--mechanism", choices=sorted(MECHANISMS))
    ap.add_argument("--name")
    ap.add_argument("--friend", choices=sorted(FRIENDS))
    ap.add_argument("--witness", choices=sorted(WITNESSES))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        ap.add_argument(f"--{flag}", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str]]:
    return [(place, mechanism) for place in sorted(PLACES) for mechanism in sorted(MECHANISMS)]


ASP_RULES = """
valid(Place, Mechanism) :- place(Place), mechanism(Mechanism).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            *(asp.fact("place", place) for place in PLACES),
            *(asp.fact("mechanism", mechanism) for mechanism in MECHANISMS),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo_combos = set(asp_valid_combos())
    if py == clingo_combos:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:", sorted(py - clingo_combos), sorted(clingo_combos - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo for combo in valid_combos()
        if not args.place or combo[0] == args.place
        if not args.mechanism or combo[1] == args.mechanism
    ]
    if not combos:
        raise StoryError("No valid friendship mystery fits those options.")
    place, mechanism = rng.choice(combos)
    name = args.name or "Luna"
    friends = [friend for friend in sorted(FRIENDS) if friend != name] or sorted(FRIENDS)
    return StoryParams(
        place=place,
        mechanism=mechanism,
        name=name,
        friend=args.friend or rng.choice(friends),
        witness=args.witness or rng.choice(sorted(WITNESSES)),
        case=rng.choice(sorted(CASES)),
        route=rng.choice(ROUTES),
    )


def story_rng(params: StoryParams) -> random.Random:
    values = (
        params.seed,
        params.place,
        params.mechanism,
        params.name,
        params.friend,
        params.witness,
        params.case,
        params.route,
    )
    text = "|".join(str(value) for value in values)
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big"))


def tell(params: StoryParams) -> World:
    scene = PLACES[params.place]
    mechanism = MECHANISMS[params.mechanism]
    case = CASES[params.case]
    rng = story_rng(params)
    world = World(scene)

    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type="girl" if params.name in {"Luna", "Mina", "Iris"} else "boy",
        )
    )
    friend = world.add(Entity(id=params.friend, kind="character", type=FRIENDS[params.friend]))
    witness = world.add(
        Entity(
            id=params.witness,
            kind="character",
            type=WITNESSES[params.witness],
            label=params.witness,
        )
    )
    device = world.add(
        Entity(
            id=params.mechanism,
            kind="mechanism",
            type="machine",
            label=mechanism,
            meters={"working": 1.0, "safety": 0.7},
        )
    )

    openings = {
        "clue_first": (
            f"The first thing {hero.id} noticed at {scene.place} was {case.clue}. "
            f"Then {friend.id} discovered that {case.missing} was gone."
        ),
        "dialogue_first": (
            f'"Let us not blame anyone yet," {hero.id} said at {scene.place}. '
            f"{case.missing.capitalize()} had vanished, and {mechanism} stood strangely still."
        ),
        "test_first": (
            f"At {scene.place}, {hero.id} began with a safe test of {mechanism}. "
            f"Only afterward did the friends learn that {case.missing} had disappeared."
        ),
        "map_first": (
            f"{hero.id} drew a map of {scene.place}, marking {mechanism}, the doorway, and {case.clue}. "
            f"In the corner, {friend.id} wrote what was missing: {case.missing}."
        ),
        "quiet_first": (
            f"The quiet at {scene.place} felt unusual. {friend.id} found an empty space where "
            f"{case.missing} should have been, beside {mechanism}."
        ),
        "two_theories": (
            f"Two ideas appeared at {scene.place}: perhaps the {witness.label} had moved {case.missing}, "
            f"or perhaps {mechanism} had done something unexpected. {hero.id} found {case.clue}."
        ),
    }
    world.say(openings[params.route])
    world.say(
        rng.choice(
            [
                f"{hero.id} and {friend.id} promised to protect one another while they investigated.",
                f"{friend.id} held the notebook, and {hero.id} checked that everyone stayed outside the moving parts.",
                f"Together, the friends agreed that a mystery should never be solved by frightening a witness.",
                f"{hero.id} noticed that {friend.id} looked worried, so they searched side by side.",
            ]
        )
    )
    world.para()

    world.say(f"Suspicion fell on the {witness.label} because {case.suspicion}.")
    world.say(
        rng.choice(
            [
                f'"The {witness.label} must have done it," someone said. {hero.id} stepped between the witness and the angry voices.',
                f"{friend.id} frowned when people blamed the {witness.label}; {case.suspicion.capitalize()} was only a circumstance.",
                f"The {witness.label} backed away as the argument grew, but {hero.id} remembered their promise to be a careful friend.",
            ]
        )
    )
    witness.memes["blamed"] = 1.0
    hero.memes["friendship"] = 1.0
    world.say(
        rng.choice(
            [
                f'"Being nearby is not proof," {hero.id} said. "We will test the mechanism safely."',
                f'"I believe you," {friend.id} told the {witness.label}. "We can look for a cause without blaming you."',
                f'{hero.id} raised a hand. "Friends protect one another, and evidence must explain the whole mystery."',
            ]
        )
    )
    world.para()

    world.say(f"First, {hero.id} {case.test}. But {case.failed}.")
    world.say(
        rng.choice(
            [
                f"The failed test changed their plan, and {friend.id} drew a fresh diagram instead of arguing.",
                f'"That result tells us where not to look," {friend.id} said, moving the notebook closer to {hero.id}.',
                f"Because the test was safe, the friends could learn from it without damaging the mechanism.",
            ]
        )
    )
    world.say(f"Then they found the turning clue: {case.clue}.")
    world.say(
        rng.choice(
            [
                f"{hero.id} followed the clue through the mechanism while {friend.id} watched from the safety line.",
                "The friends compared the mark with the moving parts and saw a hidden chain of small events.",
                f"The clue made a twist in the mystery: the mechanism, not the witness, had started the trouble.",
            ]
        )
    )
    world.para()

    world.say(f"The truth was that {case.truth}. The {witness.label} had not caused the loss.")
    witness.memes["blamed"] = 0.0
    hero.meters["safe_tests"] = 2.0
    device.meters["working"] = 1.0
    device.meters["safety"] = 1.0
    world.say(
        rng.choice(
            [
                f"The group apologized to the {witness.label}, and then {hero.id} and {friend.id} {case.repair}.",
                f'"We guessed too quickly," {friend.id} admitted. After making peace, everyone {case.repair}.',
                f"The conflict ended with an apology and careful work: together they {case.repair}.",
            ]
        )
    )
    world.say(f"{hero.id} wrote the lesson: {case.lesson}.")
    world.say(
        rng.choice(
            [
                f"At sunset, {case.ending}.",
                f"When the mystery was over, {case.ending}",
                f"Before leaving, the friends looked back. {case.ending.capitalize()}",
            ]
        )
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        witness=witness,
        device=device,
        scene=scene,
        mechanism=mechanism,
        case=case,
        truth=case.truth,
        repair=case.repair,
        lesson=case.lesson,
        ending=case.ending,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    case = facts["case"]
    return [
        f"Write a gentle mystery for a young child about {facts['hero'].id}, {facts['friend'].id}, and {facts['mechanism']}.",
        f"Tell a friendship story in which a safe test reveals that the {facts['witness'].label} was blamed unfairly.",
        f"Write a cautionary mechanism mystery that reveals {case['truth'] if isinstance(case, dict) else case.truth} and ends with {facts['ending']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    case = facts["case"]
    return [
        QAItem(
            question=f"What disappeared near {facts['mechanism']} at {facts['scene'].place}?",
            answer=f"{case.missing.capitalize()} disappeared near {facts['mechanism']} at {facts['scene'].place}.",
        ),
        QAItem(
            question=f"Why was the {facts['witness'].label} blamed?",
            answer=f"The {facts['witness'].label} was blamed because {case.suspicion}. That detail showed where the witness had been, but it did not prove responsibility.",
        ),
        QAItem(
            question=f"How did {facts['hero'].id} and {facts['friend'].id} investigate safely?",
            answer=f"They {case.test}, learned that {case.failed}, and stayed outside the dangerous moving parts while they searched for another clue.",
        ),
        QAItem(
            question=f"What twist explained the mystery?",
            answer=f"The decisive clue was that {case.clue}. The truth was that {case.truth}.",
        ),
        QAItem(
            question=f"How did the friends repair both the mechanism and their friendship?",
            answer=f"They apologized to the {facts['witness'].label}, then they {case.repair}. They remembered that {case.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should children stay away from moving mechanisms?",
            answer="Moving parts can pinch, pull, or crush fingers. Children should watch from a marked safe place and ask an adult for help before repairing anything.",
        ),
        QAItem(
            question="Why is a nearby witness not automatically guilty?",
            answer="A witness may have been close when a problem happened without causing it. Fair investigators test evidence and look for a complete explanation.",
        ),
        QAItem(
            question="How does friendship help during a mystery?",
            answer="Friends can listen calmly, protect one another from unfair blame, and compare clues until they discover what really happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1)), "", "== story qa =="]
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.extend(("", "== world qa =="))
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id} ({entity.kind}/{entity.type}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  truth={world.facts['truth']}")
    return "\n".join(lines)


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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams(
        place="clocktower",
        mechanism="counterweight",
        name="Luna",
        friend="Mina",
        witness="goat",
        case="bell_rope",
        route="clue_first",
        seed=101,
    ),
    StoryParams(
        place="boathouse",
        mechanism="waterwheel",
        name="Luna",
        friend="Theo",
        witness="otter",
        case="waterwheel_key",
        route="test_first",
        seed=202,
    ),
    StoryParams(
        place="workshop",
        mechanism="gearbox",
        name="Luna",
        friend="Iris",
        witness="crow",
        case="painted_gate",
        route="dialogue_first",
        seed=303,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, mechanism in combos:
            print(f"  {place:11} {mechanism}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
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

    for index, sample in enumerate(samples):
        header = "### curated story" if args.all else (
            f"### variant {index + 1}" if len(samples) > 1 else ""
        )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
