#!/usr/bin/env python3
"""
A standalone mystery storyworld about a small mechanism, friendship,
a cautionary clue, and a twist.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
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


ASP_RULES = r"""
mystery_story(S) :- setting(S), friendship(S), cautionary(S), twist(S).
safe_mechanism(M) :- mechanism(M), checked(M), guarded(M).
solved(S) :- mystery_story(S), safe_mechanism(M), used_in(S,M).
"""

PLACE = "the old clock tower"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def bump_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def bump_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class StoryParams:
    name: str
    friend: str
    mechanism: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    key: str
    opening: str
    trouble: str
    first_clue: str
    warning: str
    friend_line: str
    twist: str
    repair: str
    result: str
    ending: str


@dataclass
class World:
    place: str = PLACE
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for entity in self.entities.values():
            details = []
            if entity.meters:
                details.append(f"meters={entity.meters}")
            if entity.memes:
                details.append(f"memes={entity.memes}")
            lines.append(
                f"  {entity.id:10} ({entity.kind:10}) "
                f"label={entity.label!r} {' '.join(details)}"
            )
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)


CASES = [
    Case(
        key="silent_bell",
        opening="was helping inspect the clock tower before the town's evening bell",
        trouble="the bell's small striking mechanism clicked once and then fell silent",
        first_clue="a brass tooth lay beneath the gear, but its edge was polished instead of broken",
        warning="a faded sign said, 'Never turn the red key while the counterweight is raised'",
        friend_line='"The missing tooth may be a message, not a failure," the friend said.',
        twist="the tooth belonged to a second, hidden mechanism that opened a narrow drawer behind the clock face",
        repair="lowered the counterweight, kept clear of the gears, and turned only the safe blue key",
        result="the drawer opened to reveal the proper replacement tooth wrapped in cloth",
        ending="the bell rang softly at dusk, while the mysterious brass tooth rested in their evidence box",
    ),
    Case(
        key="backward_hands",
        opening="was dusting the clock tower's observation room with a trusted friend",
        trouble="the hands began moving backward whenever the wind struck the tower",
        first_clue="fresh scratches circled the blue winding knob",
        warning="a paper label warned, 'Do not force a clock that is telling you to wait'",
        friend_line='"Maybe the clock is pointing away from the danger," the friend whispered.',
        twist="the backward hands were not broken at all; they were guiding them toward a loose panel",
        repair="stopped the pendulum, marked the safe path, and opened the panel with a wooden pick",
        result="they found a wind latch that had been catching the gear whenever the gusts arrived",
        ending="the hands moved forward again, and their shadows pointed together toward the sunset",
    ),
    Case(
        key="hidden_click",
        opening="was searching the tower for the source of a strange midnight clicking",
        trouble="the click vanished each time the lantern was brought near the clock",
        first_clue="a thread of red dust ran from the clock base to the locked supply cabinet",
        warning="their caretaker had written, 'A locked door is a clue, not an invitation to pry'",
        friend_line='"Let us listen before we touch anything," the friend said.',
        twist="the sound came from a tiny wind-up beetle placed there to test whether anyone would rush",
        repair="kept the cabinet closed, followed the dust trail, and waited for the beetle to stop",
        result="a hidden note slid from beneath it and explained that the caretaker was checking their caution",
        ending="the beetle clicked its final click, as if the tower itself approved of their patience",
    ),
    Case(
        key="missing_weight",
        opening="was preparing the tower clock for the village history festival",
        trouble="one heavy weight had vanished, leaving the timing mechanism dangerously uneven",
        first_clue="a muddy footprint stopped beside the locked balcony door",
        warning="a chalk mark on the floor showed where the weight could safely rest",
        friend_line='"The footprint points outward, but the dust points inward," the friend noticed.',
        twist="the weight had not been stolen; a spring release had moved it into a hidden safety cradle",
        repair="secured the spring, used the marked lifting hook, and returned the weight without standing below it",
        result="the clock balanced itself and revealed a loose floorboard beneath the cradle",
        ending="under the board they found a map, and friendship made the secret feel safer than frightening",
    ),
    Case(
        key="false_shadow",
        opening="was showing a friend the tower's oldest lantern room",
        trouble="a tall shadow crossed the clock face even though nobody stood outside",
        first_clue="the shadow repeated exactly whenever the minute hand passed twelve",
        warning="the caretaker's note said, 'A shadow may move, but never chase one near a ledge'",
        friend_line='"If it repeats, it may belong to the mechanism," the friend said.',
        twist="a bent mirror inside the clock was casting the shadow of a hidden lever",
        repair="stayed behind the railing, covered the bright lantern, and used a long wooden handle to reset the mirror",
        result="the shadow shrank, and the lever opened a safe inspection hatch",
        ending="the tower's face showed only moonlight, while their joined shadows stood safely on the floor",
    ),
    Case(
        key="three_chimes",
        opening="was waiting with a friend for the tower's first spring chime",
        trouble="the mechanism struck three times when it should have struck once",
        first_clue="each extra chime matched a tiny notch on the winding drum",
        warning="a copper tag read, 'Count twice before touching a moving part'",
        friend_line='"The clock is counting something," the friend said.',
        twist="the chimes marked three loose bolts hidden behind the inspection plate",
        repair="stopped the mechanism, counted the bolts, and tightened them with the short wrench",
        result="the next test produced one clear chime and no dangerous wobble",
        ending="one bright note floated over the town, carrying a secret that two friends had solved carefully",
    ),
]

NAMES = ["Luna", "Mira", "Niko", "Sana", "Tavi", "Iris", "Owen", "Pia"]
FRIENDS = ["Jun", "Milo", "Ada", "Remy", "Kite", "Bea", "Sol", "Tess"]
MECHANISMS = ["gear train", "winding drum", "counterweight", "pendulum latch"]


def valid_mechanisms() -> list[str]:
    return list(MECHANISMS)


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("The investigator needs a name.")
    if not params.friend.strip():
        raise StoryError("The mystery needs a friend who can notice clues and speak.")
    if params.mechanism not in valid_mechanisms():
        raise StoryError("The mechanism must be a small clock mechanism that can be inspected safely.")
    if params.name.strip().lower() == params.friend.strip().lower():
        raise StoryError("The investigator and friend must be different people.")


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("setting", "clock_tower"),
        asp.fact("friendship", "clock_tower"),
        asp.fact("cautionary", "clock_tower"),
        asp.fact("twist", "clock_tower"),
        asp.fact("mechanism", "gear_train"),
        asp.fact("mechanism", "winding_drum"),
        asp.fact("mechanism", "counterweight"),
        asp.fact("mechanism", "pendulum_latch"),
        asp.fact("checked", "gear_train"),
        asp.fact("checked", "winding_drum"),
        asp.fact("checked", "counterweight"),
        asp.fact("checked", "pendulum_latch"),
        asp.fact("guarded", "gear_train"),
        asp.fact("guarded", "winding_drum"),
        asp.fact("guarded", "counterweight"),
        asp.fact("guarded", "pendulum_latch"),
        asp.fact("used_in", "clock_tower", "gear_train"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_params(rng: random.Random) -> StoryParams:
    return StoryParams(
        name=rng.choice(NAMES),
        friend=rng.choice(FRIENDS),
        mechanism=rng.choice(MECHANISMS),
        seed=rng.randrange(2**31),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Clock tower mystery storyworld.")
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--mechanism", choices=valid_mechanisms())
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = valid_params(rng)
    if args.name:
        params.name = args.name
    if args.friend:
        params.friend = args.friend
    if args.mechanism:
        params.mechanism = args.mechanism
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World()
    investigator = world.add(Entity("investigator", "character", params.name))
    friend = world.add(Entity("friend", "character", params.friend))
    mechanism = world.add(Entity("mechanism", "device", params.mechanism))
    world.facts.update(
        investigator=investigator,
        friend=friend,
        mechanism=mechanism,
        place=PLACE,
        friendship=True,
        cautionary=True,
        twist=True,
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    rng = random.Random(params.seed if params.seed is not None else 0)
    case = rng.choice(CASES)
    investigator = world.get("investigator")
    friend = world.get("friend")
    mechanism = world.get("mechanism")

    investigator.bump_meme("curiosity")
    friend.bump_meme("trust")
    mechanism.bump_meter("tension", 1.0)

    world.say(f"At the old clock tower, {investigator.label} {case.opening}.")
    world.say(
        f"The {mechanism.label} seemed harmless from the outside, but its careful clicks "
        f"made {investigator.label} and {friend.label} stop at the bottom step."
    )
    world.para()

    world.say(f"Then {case.trouble}.")
    world.say(f"The first clue was clear: {case.first_clue}.")
    world.say(case.warning)
    world.say(f"{investigator.label} reached toward the mechanism, but {friend.label} said {case.friend_line[1:]}")
    world.para()

    friend.bump_meme("caution")
    investigator.bump_meme("patience")
    mechanism.bump_meter("checked", 1.0)
    world.say(
        f"They did not guess or tug. Together, {investigator.label} and {friend.label} "
        f"watched the {mechanism.label} from behind the safety line."
    )
    world.say(f"That was when the mystery turned: {case.twist}.")
    world.say(
        f'"Friendship means we can tell each other when to stop," '
        f"{investigator.label} said."
    )
    world.say(
        f'"And when to look again," {friend.label} replied.'
    )
    world.para()

    mechanism.bump_meter("repaired", 1.0)
    investigator.bump_meme("trust")
    friend.bump_meme("trust")
    world.say(f"Carefully, they {case.repair}.")
    world.say(case.result)
    world.para()

    world.facts.update(
        case=case.key,
        trouble=case.trouble,
        first_clue=case.first_clue,
        warning=case.warning,
        twist=case.twist,
        repair=case.repair,
        result=case.result,
        ending=case.ending,
        resolved=True,
    )
    world.say(
        f"The mystery was solved, but the cautionary lesson stayed with them: "
        f"a mechanism should be understood before it is moved."
    )
    world.say(
        f"As evening settled over the town, {case.ending}. "
        f"{investigator.label} and {friend.label} climbed down together, "
        f"each listening for the other's careful footsteps."
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a mystery about {facts['investigator'].label} and {facts['friend'].label} "
        f"investigating a {facts['mechanism'].label} in an old clock tower.",
        "Include friendship, a cautionary warning, a mechanism, and a surprising twist.",
        f"Tell a child-friendly mystery where the clue is {facts['first_clue']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    investigator = facts["investigator"].label
    friend = facts["friend"].label
    mechanism = facts["mechanism"].label
    return [
        QAItem(
            "Where did the mystery take place?",
            "It took place in the old clock tower.",
        ),
        QAItem(
            "What problem did the friends discover?",
            f"They discovered that {facts['trouble']}.",
        ),
        QAItem(
            f"What warning helped {investigator} and {friend} stay safe?",
            facts["warning"],
        ),
        QAItem(
            "What was the surprising twist?",
            f"The surprising twist was that {facts['twist']}.",
        ),
        QAItem(
            f"How did the friends solve the problem with the {mechanism}?",
            f"They {facts['repair']}, and then {facts['result']}.",
        ),
        QAItem(
            "What showed that the ending was safe and hopeful?",
            facts["ending"].capitalize() + ".",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a mechanism?",
            "A mechanism is a group of moving parts that work together to do a job.",
        ),
        QAItem(
            "Why should someone be cautious around a machine?",
            "A person should be cautious because moving parts can pinch, pull, or shift unexpectedly.",
        ),
        QAItem(
            "How can friendship help during a mystery?",
            "A friend can notice a clue, share a different idea, and remind someone to make a safe choice.",
        ),
        QAItem(
            "What is a twist in a story?",
            "A twist is a surprising change in what the characters thought was happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def asp_verify() -> int:
    import asp

    program = asp_program(
        "#show mystery_story/1.\n"
        "#show safe_mechanism/1.\n"
        "#show solved/1."
    )
    model = asp.one_model(program)
    actual = {
        (symbol.name, tuple(
            arg.number if arg.type.name == "Number"
            else arg.string if arg.type.name == "String"
            else arg.name
            for arg in symbol.arguments
        ))
        for symbol in model
        if symbol.name in {"mystery_story", "safe_mechanism", "solved"}
    }
    expected = {
        ("mystery_story", ("clock_tower",)),
        ("safe_mechanism", ("gear_train",)),
        ("safe_mechanism", ("winding_drum",)),
        ("safe_mechanism", ("counterweight",)),
        ("safe_mechanism", ("pendulum_latch",)),
        ("solved", ("clock_tower",)),
    }
    if actual != expected:
        print("MISMATCH between ASP and Python expectations.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1

    for params in [
        StoryParams("Luna", "Jun", "gear train", 1),
        StoryParams("Mira", "Ada", "pendulum latch", 2),
        StoryParams("Niko", "Bea", "counterweight", 3),
    ]:
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("MISMATCH: generated story was incomplete.")
            return 1
    print("OK: ASP twin and generated stories passed verification.")
    return 0


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show solved/1."))
    return sorted(asp.atoms(model, "solved"))


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        print()
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "Jun", "gear train", 11),
    StoryParams("Mira", "Ada", "winding drum", 29),
    StoryParams("Niko", "Bea", "counterweight", 47),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery_story/1.\n#show safe_mechanism/1.\n#show solved/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("ASP-compatible clock tower mystery:")
        for item in asp_list():
            print(item)
        return

    rng = random.Random(
        args.seed if args.seed is not None else random.randrange(2**31)
    )

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempts += 1

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
