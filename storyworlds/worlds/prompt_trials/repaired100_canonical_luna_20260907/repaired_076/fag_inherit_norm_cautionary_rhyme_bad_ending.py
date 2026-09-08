#!/usr/bin/env python3
"""A cautionary adventure rhyme about inheriting a dangerous family norm."""

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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    helper: str = "Aunt Mira"
    setting: str = "the old cliff trail"
    relic: str = "the brass lantern"
    scenario: str = "inherit_norm"
    rhyme_mode: str = "warning"
    variant: int = 0


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass(frozen=True)
class Scenario:
    key: str
    title: str
    premise: str
    inheritance: str
    norm: str
    temptation: str
    danger: str
    dialogue: str
    action: str
    result: str
    lesson: str
    ending: str


SCENARIOS = (
    Scenario(
        "inherit_norm",
        "the inherited rule",
        "Luna found a dusty brass lantern beneath a family map",
        "her grandfather had left her the lantern and a note calling it a family treasure",
        "old explorers had always carried a fag on the cliff trail, and everyone said brave hikers did the same",
        "copy the old custom so the adventure would feel official",
        "lighting the fag near dry grass and a windy cliff",
        "A family custom can be questioned; courage does not need a dangerous flame",
        "set the fag aside, told Aunt Mira about the risk, and used the lantern only after checking that it was safely empty and approved for the trail",
        "the dry grass stayed unburned, and the group reached the lookout with clear eyes and steady steps",
        "an inherited object may be kept while an unsafe norm is changed",
        "At sunset, the brass lantern shone with a clean battery light, while the forbidden fag rested sealed in a safe tin.",
    ),
    Scenario(
        "shortcut",
        "the smoky shortcut",
        "a shortcut curled through a brittle patch of summer grass",
        "Luna inherited a red scarf and an old family story about marking the path with a fag",
        "the story made the risky shortcut sound like a rule every adventurer must obey",
        "strike a match and leave a bright trail",
        "one spark could race through the grass toward the campers",
        "A story may guide our feet, but no story commands us to make a fire",
        "chose the longer stone path, tied the scarf to a signpost, and reported the unsafe custom",
        "the party arrived later but safely, and the grass remained green",
        "a tradition is not a safety rule merely because it is old",
        "The red scarf fluttered on the safe trail marker, far from every match.",
    ),
    Scenario(
        "cave_echo",
        "the cave warning",
        "echoes bounced from a cave where Luna's family had once explored",
        "she inherited a pocket case containing a fag and a proud explorer's badge",
        "the badge seemed to promise that real adventurers never asked for help",
        "hide the fag and enter the cave alone",
        "darkness, loose stones, and smoke could trap a lone explorer",
        "Real courage speaks up; the badge is not a command to ignore danger",
        "showed Aunt Mira the case, left the fag unopened, and explored only the marked entrance together",
        "the team found ancient footprints without entering the unstable passage",
        "bravery means making a careful choice, not obeying a harmful expectation",
        "The badge gleamed on Luna's pack as the cave echoed with the safe team's cheerful rhyme.",
    ),
)

SCENARIO_BY_KEY = {item.key: item for item in SCENARIOS}
NAMES = ("Luna", "Pip", "Mara", "Theo")
HELPERS = ("Aunt Mira", "Uncle Sol", "Rafi", "Captain Bea")
SETTINGS = ("the old cliff trail", "the pine ridge", "the moonlit valley")
RELICS = ("the brass lantern", "the red compass", "the explorer's badge")
MODES = ("warning", "echo", "march", "whisper")

OPENINGS = (
    "Luna packed a map and a snack and set off where the wild winds blew.",
    "Beyond the village gate, Luna began an adventure beneath a copper sky.",
    "Boots went crunch on the mountain track as Luna followed the family map.",
    "A rhyme rode the wind through the pines while Luna climbed toward the lookout.",
)

REFRAINS = {
    "warning": "Old words may point, but careful minds decide; a risky custom has no place on a mountain side.",
    "echo": "The cliffs cried back, and the clear words grew: ask, check, and choose what is safe to do.",
    "march": "Step by step, the hikers agreed: no inherited rule outranks a safety need.",
    "whisper": "The map spoke softly, the dry grass spoke too; Luna listened to the clue that was true.",
}


def build_world(params: StoryParams) -> World:
    world = World(params)
    child = world.add(Entity(params.name, "character", params.name, meters={"caution": 0.4}, memes={"curiosity": 0.9}))
    helper = world.add(Entity("helper", "character", params.helper, meters={"judgment": 1.0}, memes={"care": 1.0}))
    world.add(Entity("relic", "inheritance", params.relic, owner=params.name))
    world.add(Entity("fag", "hazard", "a fag", owner=params.name, meters={"flammability": 1.0}, memes={"danger": 1.0}))
    world.facts.update(child=child.label, helper=helper.label, inheritance=params.relic, has_fag=True)
    return world


def simulate(world: World) -> World:
    p = world.params
    case = SCENARIO_BY_KEY[p.scenario]
    child = world.entities[p.name]
    helper = world.entities["helper"]

    world.say(f"{random.Random(p.variant + 1).choice(OPENINGS)}")
    world.say(f"{p.name} was a young adventurer who loved riddles, maps, and daring climbs. {p.name} did not yet know that an inherited object could carry an unsafe norm with it.")
    world.say(f"{case.premise}.")
    world.para()
    world.say(f"{case.inheritance}. The family {case.norm}.")
    world.say(f"The old idea sounded grand, but {case.danger} stood nearby. {p.name} wondered whether to {case.temptation}.")
    world.say(f"{p.name} reached for the fag, then noticed the wind combing the dry grass.")
    world.para()
    world.say(f"{helper.label} called, \"{case.dialogue}.\"")
    world.say(f"{p.name} answered, \"Then I will keep the useful inheritance and leave the dangerous rule behind.\"")
    world.say(f"Together, they {case.action}.")
    world.say(REFRAINS[p.rhyme_mode])
    world.para()
    world.say(f"That careful turn changed the expedition: {case.result}.")
    world.say(f"{p.name} still carried the family map, but now the map marked a new rule: ask questions when an old custom could hurt someone.")
    world.say(f"{case.ending}")
    world.say(f"The adventure ended with a lesson, not a disaster: {case.lesson}.")
    world.fired.update({"noticed_hazard", "asked_helper", "rejected_norm", "protected_trail", "safe_resolution"})
    child.meters["caution"] = 1.0
    child.memes["confidence"] = 1.0
    world.facts.update(
        scenario=case.key,
        inherited_object=p.relic,
        unsafe_norm=case.norm,
        hazard=case.danger,
        rejected_action=case.temptation,
        dialogue_changed_choice=True,
        action=case.action,
        result=case.result,
        lesson=case.lesson,
        fag_used=False,
        safe=True,
    )
    return world


def prompts(world: World) -> list[str]:
    p = world.params
    case = SCENARIO_BY_KEY[p.scenario]
    return [
        f"Write an adventurous cautionary rhyme about {p.name} inheriting {p.relic} and questioning a dangerous norm.",
        f"Tell a child-friendly adventure in which the fag is recognized as a hazard rather than used.",
        f"End with a bad ending avoided through dialogue, careful judgment, and the image: {case.ending}",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    case = SCENARIO_BY_KEY[p.scenario]
    return [
        QAItem(f"What did {p.name} inherit?", f"{p.name} inherited {p.relic}, along with a family story connected to carrying a fag."),
        QAItem("What dangerous norm did the old story suggest?", f"It suggested that {case.norm}."),
        QAItem("What bad ending was avoided?", f"The group avoided the danger that {case.danger}. The fag was not used."),
        QAItem(f"What did {p.name} and {p.helper} do?", f"They {case.action}."),
        QAItem("How did the conversation change the adventure?", f"The helper's words made the danger visible, so the child rejected the inherited norm and chose a safer action."),
        QAItem("What proved that the ending was safe?", f"{case.ending}"),
        QAItem("What was the cautionary lesson?", f"{case.lesson}."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("Why can an inherited custom be questioned?", "Age and family history do not make a custom safe. People should examine its likely harm and choose safer behavior when needed."),
        QAItem("Why should a fag never be used near dry grass or a trail?", "A fag can ignite grass, clothing, or nearby materials, and wind can spread fire quickly."),
        QAItem("What should a child do when an old rule seems dangerous?", "The child should stop, move away from the hazard, and tell a trusted adult instead of copying the rule."),
        QAItem("What does courage mean in this adventure?", "Courage means noticing danger, asking for help, and changing an unsafe tradition rather than pretending to be fearless."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {text}" for i, text in enumerate(sample.prompts, 1))
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


ASP_RULES = """
inherited(X) :- child(X), has_relic(X).
unsafe_norm(X) :- inherited(X), carries_fag(X).
careful(X) :- child(X), helper_told(X), rejected_norm(X), fag_unused(X).
safe_adventure(X) :- careful(X), protected_trail(X).
"""


def asp_facts(params: Optional[StoryParams] = None) -> str:
    import asp
    name = (params or StoryParams()).name.lower().replace("-", "_")
    return "\n".join(
        (
            asp.fact("child", name),
            asp.fact("has_relic", name),
            asp.fact("carries_fag", name),
            asp.fact("helper_told", name),
            asp.fact("rejected_norm", name),
            asp.fact("fag_unused", name),
            asp.fact("protected_trail", name),
        )
    )


def asp_program(show: str, params: Optional[StoryParams] = None) -> str:
    return f"{asp_facts(params)}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    params = StoryParams()
    symbols = asp.one_model(asp_program("#show safe_adventure/1.", params))
    found = set(asp.atoms(symbols, "safe_adventure"))
    expected = {(params.name.lower().replace("-", "_"),)}
    if found == expected:
        print("OK: ASP twin confirms the inherited norm was rejected and the adventure stayed safe.")
        return 0
    print("ASP verification failed.")
    return 1


def validate(params: StoryParams) -> None:
    if params.scenario not in SCENARIO_BY_KEY:
        raise StoryError(f"Unknown scenario: {params.scenario}")
    if not params.name.strip():
        raise StoryError("A named adventurer is required.")
    if not params.helper.strip():
        raise StoryError("A trusted helper is required.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cautionary adventure rhyme about an inherited dangerous norm.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--relic", choices=RELICS)
    parser.add_argument("--scenario", choices=tuple(SCENARIO_BY_KEY))
    parser.add_argument("--rhyme-mode", choices=MODES)
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
    params = StoryParams(
        seed=args.seed,
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        setting=args.setting or rng.choice(SETTINGS),
        relic=args.relic or rng.choice(RELICS),
        scenario=args.scenario or rng.choice(tuple(SCENARIO_BY_KEY)),
        rhyme_mode=args.rhyme_mode or rng.choice(MODES),
        variant=rng.randrange(1, 2**31),
    )
    validate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    validate(params)
    world = simulate(build_world(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world is not None:
        print(f"\n--- trace ---\nfacts: {sample.world.facts}\nfired: {sorted(sample.world.fired)}")
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show safe_adventure/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.n < 1:
        raise StoryError("-n must be at least 1.")
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = []
        for index, scenario in enumerate(SCENARIO_BY_KEY):
            params = StoryParams(
                seed=base_seed,
                name=NAMES[index % len(NAMES)],
                helper=HELPERS[index % len(HELPERS)],
                setting=SETTINGS[index % len(SETTINGS)],
                relic=RELICS[index % len(RELICS)],
                scenario=scenario,
                rhyme_mode=MODES[index % len(MODES)],
                variant=index + 101,
            )
            samples.append(generate(params))
    else:
        samples = [generate(resolve_params(args, random.Random(base_seed + i))) for i in range(args.n)]
    if args.asp:
        import asp
        for sample in samples:
            atoms = asp.atoms(asp.one_model(asp_program("#show safe_adventure/1.", sample.params)), "safe_adventure")
            if not atoms:
                raise StoryError("ASP check found no safe adventure.")
    if args.json:
        payload = samples[0].to_json() if len(samples) == 1 else json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False)
        print(payload)
        return
    for index, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {index + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
