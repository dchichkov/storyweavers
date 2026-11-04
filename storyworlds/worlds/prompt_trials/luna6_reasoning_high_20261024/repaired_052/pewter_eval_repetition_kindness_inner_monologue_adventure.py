#!/usr/bin/env python3
"""
A small Adventure storyworld about two trail scouts, a fading rescue beacon,
and a pewter bell that helps them find the kind way forward.
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
    if (_parent / "results.py").is_file():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Scenario:
    key: str
    obstacle: str
    animal: str
    animal_problem: str
    kind_action: str
    animal_signal: str
    animal_guide: str
    route: str
    safe_crossing: str
    ending_image: str


@dataclass
class StoryParams:
    scout: str = "Mara"
    companion: str = "Tavi"
    trail: str = "Frostglass Pass"
    seed: Optional[int] = None
    scenario: str = "fog_hare"
    telling_mode: str = "arrival"


class World:
    def __init__(self, setting: str) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


SCOUT_NAMES = ["Mara", "Tavi", "Niko", "Sela", "Rowan", "Jun"]
TRAIL_NAMES = ["Frostglass Pass", "Pinewhistle Ridge", "Red Fern Mountain"]
TELLING_MODES = ["arrival", "warning", "question", "memory"]

SCENARIOS = [
    Scenario(
        key="fog_hare",
        obstacle="a bank of fog swallowed the fork and hid the path to the lookout",
        animal="a snow hare",
        animal_problem="a loop of red trail ribbon had caught one back paw",
        kind_action=(
            "{scout} eased the ribbon free while {companion} held a scarf "
            "as a little windbreak"
        ),
        animal_signal="tapped its paw three times against a flat stone",
        animal_guide="hopped beside the low stone wall",
        route="the low stone wall",
        safe_crossing="the wall kept them well away from the unseen drop",
        ending_image=(
            "the snow hare sat safely beside the wall as the beacon's golden "
            "light brushed its ears"
        ),
    ),
    Scenario(
        key="snow_goat",
        obstacle="new snow buried the trail markers and blurred the ridge edge",
        animal="a young goat",
        animal_problem="one front hoof was wedged between two rocks",
        kind_action=(
            "{scout} cleared the snow while {companion} gently eased the "
            "goat's hoof free"
        ),
        animal_signal="stamped three times on a line of firm stones",
        animal_guide="stepped onto a row of firm stones",
        route="the row of firm stones",
        safe_crossing="the firm stones carried them across a buried turn in the trail",
        ending_image=(
            "the young goat stood on the safe stones while golden light settled "
            "across the new snow"
        ),
    ),
    Scenario(
        key="wind_owl",
        obstacle="the wind had spun every trail arrow backward",
        animal="a little owl",
        animal_problem="a loose strip of red ribbon was tangled around one wing",
        kind_action=(
            "{scout} carefully unwound the ribbon while {companion} shielded "
            "the owl from the gusts"
        ),
        animal_signal="gave three soft hoots from the lee side of a ridge",
        animal_guide="glided along the sheltered lee side",
        route="the sheltered lee side of the ridge",
        safe_crossing="the ridge itself blocked the strongest gusts",
        ending_image=(
            "the little owl perched on a dry branch as the beacon's gold beam "
            "swept over the wind-tossed signs"
        ),
    ),
]

SCENARIO_BY_KEY = {scenario.key: scenario for scenario in SCENARIOS}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld about kindness, repetition, and a pewter bell."
    )
    ap.add_argument("--scout", choices=SCOUT_NAMES)
    ap.add_argument("--companion", choices=SCOUT_NAMES)
    ap.add_argument("--trail", choices=TRAIL_NAMES)
    ap.add_argument("--scenario", choices=list(SCENARIO_BY_KEY))
    ap.add_argument("--telling-mode", choices=TELLING_MODES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def reasonableness_gate(params: StoryParams) -> None:
    """Reject combinations that do not describe a reasonable trail adventure."""
    if params.scout not in SCOUT_NAMES:
        raise StoryError(f"Unknown scout {params.scout!r}; choose a registered scout name.")
    if params.companion not in SCOUT_NAMES:
        raise StoryError(
            f"Unknown companion {params.companion!r}; choose a registered scout name."
        )
    if params.scout == params.companion:
        raise StoryError("The scout and companion must be two different people.")
    if params.trail not in TRAIL_NAMES:
        raise StoryError(f"Unknown trail {params.trail!r}; choose a registered trail.")
    if params.scenario not in SCENARIO_BY_KEY:
        raise StoryError(
            f"Unknown scenario {params.scenario!r}; choose one of "
            f"{', '.join(SCENARIO_BY_KEY)}."
        )
    if params.telling_mode not in TELLING_MODES:
        raise StoryError(
            f"Unknown telling mode {params.telling_mode!r}; choose one of "
            f"{', '.join(TELLING_MODES)}."
        )
    if params.seed is not None and (
        isinstance(params.seed, bool) or not isinstance(params.seed, int)
    ):
        raise StoryError("The seed must be an integer or None.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    scout = args.scout or rng.choice(SCOUT_NAMES)
    companion_choices = [name for name in SCOUT_NAMES if name != scout]
    companion = args.companion or rng.choice(companion_choices)
    params = StoryParams(
        scout=scout,
        companion=companion,
        trail=args.trail or rng.choice(TRAIL_NAMES),
        seed=None,
        scenario=args.scenario or rng.choice(SCENARIOS).key,
        telling_mode=args.telling_mode or rng.choice(TELLING_MODES),
    )
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    rng = random.Random(params.seed)
    scenario = SCENARIO_BY_KEY[params.scenario]
    scout_name = params.scout
    companion_name = params.companion
    world = World(params.trail)

    scout = world.add(
        Entity(
            id=scout_name,
            kind="character",
            type="trail_scout",
            label="scout",
            location="lower trail",
            meters={"stamina": 0.9, "route_confidence": 0.0},
            memes={"courage": 0.7, "kindness": 0.5},
            traits=["curious", "steady"],
        )
    )
    companion = world.add(
        Entity(
            id=companion_name,
            kind="character",
            type="trail_scout",
            label="companion",
            location="lower trail",
            meters={"stamina": 0.9, "route_confidence": 0.0},
            memes={"patience": 0.7, "kindness": 0.6},
            traits=["observant", "helpful"],
        )
    )
    animal = world.add(
        Entity(
            id="trail_animal",
            kind="animal",
            type="wild_animal",
            label=scenario.animal,
            location="at the hidden fork",
            meters={"distress": 1.0, "safety": 0.1},
            memes={"trust": 0.1},
            traits=["small", "frightened"],
        )
    )
    bell = world.add(
        Entity(
            id="pewter_bell",
            kind="object",
            type="handbell",
            label="pewter handbell",
            location="scout's pack",
            meters={"condition": 1.0, "sound_reach": 0.2},
            memes={"purpose": 0.8},
            traits=["bright-toned", "sturdy"],
        )
    )
    beacon = world.add(
        Entity(
            id="rescue_beacon",
            kind="place",
            type="beacon",
            label="hilltop rescue beacon",
            location="lookout",
            meters={"light": 0.15, "bell_installed": 0.0},
            memes={"welcome": 0.4},
            traits=["fading", "important"],
        )
    )

    world.facts.update(
        scenario=scenario.key,
        trail=params.trail,
        goal="replace the lookout's cracked bell before the storm arrives",
        obstacle=scenario.obstacle,
        repeated_clue=scenario.animal_signal,
        safe_route=scenario.route,
        kindness_action=scenario.kind_action.format(
            scout=scout_name, companion=companion_name
        ),
        ending_image=scenario.ending_image,
        seed_words=["pewter", "eval"],
        features=["Repetition", "Kindness", "Inner Monologue"],
    )

    if params.telling_mode == "warning":
        world.say(
            f'"Those clouds are moving fast," {companion_name} said as the two '
            f'scouts climbed {params.trail}.'
        )
        world.say(
            f"They had to carry a new pewter handbell to the hilltop rescue "
            f"beacon before the storm reached it."
        )
    elif params.telling_mode == "question":
        world.say(
            f'"Will the rescue beacon still be shining when we get there?" '
            f'{scout_name} asked as the two scouts started up {params.trail}.'
        )
        world.say(
            "Its lamp was fading, and they carried a new pewter handbell to "
            "replace the cracked one before dusk."
        )
    elif params.telling_mode == "memory":
        world.say(
            f"Later, {scout_name} would remember the first quiet steps along "
            f"{params.trail}, before the mountain wind rose."
        )
        world.say(
            "The two scouts were carrying a new pewter handbell to the hilltop "
            "rescue beacon, whose lamp was fading before a storm."
        )
    else:
        world.say(
            f"Just after sunrise, {scout_name} and {companion_name} set off "
            f"along {params.trail} with a new pewter handbell for the lookout."
        )
        world.say(
            "The rescue beacon's lamp was fading, and the storm would reach "
            "the mountain by dusk."
        )

    world.say(
        "A faded note in their map key explained that “eval” was an old "
        "ranger's shorthand for “echo vale”; three little rings marked the "
        "listening path."
    )

    world.para()
    world.say(f"Then {scenario.obstacle}.")
    world.say(
        f"Beside the fork, {scenario.animal} was in trouble: "
        f"{scenario.animal_problem}."
    )
    world.say(
        f'"We could scramble up the steep ridge," {companion_name} said. '
        f'"It looks faster."'
    )
    world.say(
        f'{scout_name} wanted to hurry. In a quiet inner voice, {scout_name} '
        f'thought, *A fast step is no good if it leaves someone frightened '
        f'behind.*'
    )
    world.say(
        f'"You are right," {scout_name} replied. "Let us help first, then '
        f'listen for the trail."'
    )
    world.say(
        f"{scenario.kind_action.format(scout=scout_name, companion=companion_name)}."
    )

    animal.meters["distress"] = 0.0
    animal.meters["safety"] = 1.0
    animal.memes["trust"] = 1.0
    animal.location = "beside the safe trail"
    scout.memes["kindness"] = 1.0
    companion.memes["kindness"] = 1.0

    world.para()
    world.say(
        f"Once free, the {scenario.animal} calmed and "
        f"{scenario.animal_signal}."
    )
    world.say(f"Then it {scenario.animal_guide}.")
    world.say(
        f'"That matches the three rings on the map," {companion_name} said. '
        f'"Let us test the echo before we choose."'
    )
    world.say(
        f"{scout_name} rang the pewter bell once, twice, three times, "
        f"pausing to listen after each clear note."
    )
    world.say(
        f"The last ring came back from {scenario.route}, just where the "
        f"{scenario.animal} had pointed."
    )

    scout.meters["route_confidence"] = 0.95
    companion.meters["route_confidence"] = 0.95
    bell.meters["sound_reach"] = 0.9
    world.facts["route_confirmed_by"] = "repeated bell echoes and the animal's signal"

    world.para()
    world.say(
        f"The scouts followed the animal's lead; {scenario.safe_crossing}."
    )
    world.say(
        f"They reached the lookout before dusk, fitted the pewter bell beside "
        f"the rescue beacon, and lit its waiting lamp."
    )

    beacon.location = "lit lookout"
    beacon.meters["light"] = 1.0
    beacon.meters["bell_installed"] = 1.0
    beacon.memes["welcome"] = 1.0
    bell.location = "rescue beacon"
    scout.location = "lookout"
    companion.location = "lookout"
    world.facts.update(
        storm_beaten=True,
        beacon_lit=True,
        bell_installed=True,
        animal_safe=True,
        story_end="the rescue beacon shines and its bell can guide travelers",
    )

    world.say(
        f"Three bright notes rang across the valley, and the beacon painted "
        f"the trail gold. Below, {scenario.ending_image}."
    )

    prompts = [
        (
            f"Write an Adventure about {scout_name} and {companion_name} carrying "
            f"a pewter bell along {params.trail}. Include repetition, kindness, "
            "and a clear inner monologue."
        ),
        (
            f"Tell a child-friendly mountain adventure in which the scouts "
            f"discover what the map's “eval” mark means and help {scenario.animal}."
        ),
        (
            "Write a complete story with a spoken exchange, a careful choice, "
            "and an ending image that shows the rescue beacon is working."
        ),
    ]
    story_qa = [
        QAItem(
            question="What were the scouts carrying, and why?",
            answer=(
                "They carried a new pewter handbell to replace the cracked bell "
                "at the hilltop rescue beacon. Its lamp was fading before the "
                "storm arrived."
            ),
        ),
        QAItem(
            question="What did the word “eval” mean on the map?",
            answer=(
                "The map's old ranger shorthand “eval” meant “echo vale.” The "
                "three rings showed the scouts where listening for an echo could "
                "help them choose a trail."
            ),
        ),
        QAItem(
            question=f"How did the scouts show kindness to the {scenario.animal}?",
            answer=(
                f"They stopped instead of rushing past and "
                f"{scenario.kind_action.format(scout=scout_name, companion=companion_name)}. "
                "The animal was safe enough to show them the route it knew."
            ),
        ),
        QAItem(
            question="How did repetition help the scouts find the safe route?",
            answer=(
                f"The {scenario.animal} gave a repeated signal, and the scouts "
                f"rang the pewter bell three times. The returning sound came "
                f"from {scenario.route}, confirming the animal's lead."
            ),
        ),
        QAItem(
            question="What changed by the end of the adventure?",
            answer=(
                "The scouts installed the pewter bell and lit the rescue beacon "
                "before dusk. Its golden light and clear notes could now guide "
                "travelers along the mountain trail."
            ),
        ),
    ]
    world_qa = [
        QAItem(
            question="Why can repeating a sound help someone find a way?",
            answer=(
                "A repeated sound gives a traveler more than one chance to "
                "notice where an echo comes from. Comparing the echoes can help "
                "show which direction is open."
            ),
        ),
        QAItem(
            question="What does kindness look like during an adventure?",
            answer=(
                "Kindness can mean stopping to help someone who is frightened "
                "or hurt, even when the journey feels urgent. That care can help "
                "everyone make a safer choice."
            ),
        ),
        QAItem(
            question="What is an inner monologue?",
            answer=(
                "An inner monologue is a character's private thought. It can "
                "show a character weighing a choice before deciding what to do."
            ),
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
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
        print("--- world model state ---")
        for entity in sample.world.entities.values():
            bits = [f"location={entity.location}"]
            if entity.meters:
                bits.append(f"meters={entity.meters}")
            if entity.memes:
                bits.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {entity.type} {' '.join(bits)}")
        print(f"  facts: {sample.world.facts}")
    if qa:
        print()
        print("== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def asp_facts() -> str:
    import asp

    lines = []
    for scenario in SCENARIOS:
        lines.append(asp.fact("scenario", scenario.key))
    for name in SCOUT_NAMES:
        lines.append(asp.fact("person", name))
    for trail in TRAIL_NAMES:
        lines.append(asp.fact("trail", trail))
    for mode in TELLING_MODES:
        lines.append(asp.fact("telling_mode", mode))
    for feature in ("Repetition", "Kindness", "Inner Monologue"):
        lines.append(asp.fact("feature", feature))
    for word in ("pewter", "eval"):
        lines.append(asp.fact("seed_word", word))
    return "\n".join(lines)


ASP_RULES = r"""
valid_choice(S,A,B,T,M) :-
    candidate(S,A,B,T,M),
    scenario(S),
    person(A),
    person(B),
    A != B,
    trail(T),
    telling_mode(M).

#show feature/1.
#show seed_word/1.
#show valid_choice/5.
"""


def asp_program(candidates: Optional[list[tuple[str, str, str, str, str]]] = None) -> str:
    import asp

    lines = [asp_facts()]
    if candidates:
        lines.extend(
            asp.fact("candidate", scenario, scout, companion, trail, mode)
            for scenario, scout, companion, trail, mode in candidates
        )
    lines.append(ASP_RULES)
    return "\n".join(lines)


def _is_reasonable_without_raising(params: StoryParams) -> bool:
    try:
        reasonableness_gate(params)
    except StoryError:
        return False
    return True


def asp_check(params: StoryParams) -> bool:
    import asp

    reasonableness_gate(params)
    candidate = (
        params.scenario,
        params.scout,
        params.companion,
        params.trail,
        params.telling_mode,
    )
    model = asp.one_model(asp_program([candidate]))
    accepted = set(asp.atoms(model, "valid_choice"))
    return candidate in accepted


def asp_verify() -> int:
    import asp

    cases: set[tuple[str, str, str, str, str]] = set()
    for scenario_index, scenario in enumerate(SCENARIOS):
        for scout_index, scout in enumerate(SCOUT_NAMES):
            for companion_index, companion in enumerate(SCOUT_NAMES):
                trail = TRAIL_NAMES[(scout_index + companion_index) % len(TRAIL_NAMES)]
                mode = TELLING_MODES[
                    (scenario_index + scout_index + companion_index) % len(TELLING_MODES)
                ]
                cases.add((scenario.key, scout, companion, trail, mode))

    first = SCENARIOS[0].key
    cases.update(
        {
            (first, SCOUT_NAMES[0], SCOUT_NAMES[0], TRAIL_NAMES[0], TELLING_MODES[0]),
            ("unknown_scenario", SCOUT_NAMES[0], SCOUT_NAMES[1], TRAIL_NAMES[0], TELLING_MODES[0]),
            (first, "Unknown", SCOUT_NAMES[1], TRAIL_NAMES[0], TELLING_MODES[0]),
            (first, SCOUT_NAMES[0], SCOUT_NAMES[1], "Unknown Trail", TELLING_MODES[0]),
            (first, SCOUT_NAMES[0], SCOUT_NAMES[1], TRAIL_NAMES[0], "unknown_mode"),
        }
    )

    candidates = sorted(cases)
    model = asp.one_model(asp_program(candidates))
    asp_valid = set(asp.atoms(model, "valid_choice"))
    python_valid = set()
    for candidate in candidates:
        params = StoryParams(
            scout=candidate[1],
            companion=candidate[2],
            trail=candidate[3],
            scenario=candidate[0],
            telling_mode=candidate[4],
            seed=1,
        )
        if _is_reasonable_without_raising(params):
            python_valid.add(candidate)

    if python_valid != asp_valid:
        print("MISMATCH: ASP and Python reasonableness gates disagree.")
        print("Python only:", sorted(python_valid - asp_valid))
        print("ASP only:", sorted(asp_valid - python_valid))
        return 1

    features = set(asp.atoms(model, "feature"))
    words = set(asp.atoms(model, "seed_word"))
    if features != {
        ("Repetition",),
        ("Kindness",),
        ("Inner Monologue",),
    }:
        print("MISMATCH: ASP feature facts are wrong.")
        print(sorted(features))
        return 1
    if words != {("pewter",), ("eval",)}:
        print("MISMATCH: ASP seed-word facts are wrong.")
        print(sorted(words))
        return 1

    for index, scenario in enumerate(SCENARIOS):
        params = StoryParams(
            scout=SCOUT_NAMES[index],
            companion=SCOUT_NAMES[index + 1],
            trail=TRAIL_NAMES[index],
            seed=100 + index,
            scenario=scenario.key,
            telling_mode=TELLING_MODES[index],
        )
        sample = generate(params)
        if (
            "pewter" not in sample.story
            or "eval" not in sample.story
            or "once, twice, three times" not in sample.story
            or "inner voice" not in sample.story
            or sample.world is None
            or sample.world.facts.get("beacon_lit") is not True
            or not sample.story_qa
        ):
            print(f"MISMATCH: generated story failed its checks for {scenario.key}.")
            return 1
        if not asp_check(params):
            print(f"MISMATCH: ASP rejected the valid story parameters for {scenario.key}.")
            return 1

    print("OK: ASP and Python gates agree, and generated adventures pass their story checks.")
    return 0


def _curated_params() -> list[StoryParams]:
    return [
        StoryParams(
            scout="Mara",
            companion="Tavi",
            trail="Frostglass Pass",
            seed=101,
            scenario="fog_hare",
            telling_mode="arrival",
        ),
        StoryParams(
            scout="Niko",
            companion="Sela",
            trail="Pinewhistle Ridge",
            seed=202,
            scenario="snow_goat",
            telling_mode="question",
        ),
        StoryParams(
            scout="Rowan",
            companion="Jun",
            trail="Red Fern Mountain",
            seed=303,
            scenario="wind_owl",
            telling_mode="warning",
        ),
    ]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.n < 1 and not args.all:
        raise SystemExit("The number of stories must be at least one.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = _curated_params()
    else:
        params_list = []
        seen: set[str] = set()
        attempt = 0
        limit = max(100, args.n * 50)
        while len(params_list) < args.n and attempt < limit:
            attempt += 1
            attempt_seed = base_seed + attempt
            params = resolve_params(args, random.Random(attempt_seed))
            params.seed = attempt_seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            params_list.append(params)
        if len(params_list) != args.n:
            raise SystemExit("Could not produce the requested number of distinct stories.")

    samples = [generate(params) for params in params_list]

    if args.asp:
        for sample in samples:
            if not asp_check(sample.params):
                raise SystemExit("ASP rejected a story that passed the Python reasonableness gate.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if args.asp:
            print("ASP check: valid story parameters.")
        header = ""
        if args.all:
            header = (
                f"### {sample.params.scout} and {sample.params.companion} "
                f"on {sample.params.trail}"
            )
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except StoryError as exc:
        print(f"Story error: {exc}", file=sys.stderr)
        raise SystemExit(2)
