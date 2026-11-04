#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Optional

_ROOT = Path(__file__).resolve()
for _parent in _ROOT.parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        sys.path.insert(0, str(_parent))
        break

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
% A runner's tale is reasonable when it has a real clue, a helpful neighbor,
% a safe method, and a repair that restores the spring without harming anyone.
reasonable_plot(S) :-
    plot(S),
    has_clue(S),
    has_helper(S),
    safe_method(S),
    restores_spring(S).
#show reasonable_plot/1.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Tavi"
    companion: str = "Pip the fox"
    village: str = "Hazelbrook"
    vessel: str = "a blue clay pitcher"
    plot_id: str = "alder_bridge"


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class Thing:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class Place:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    people: dict[str, Person] = field(default_factory=dict)
    things: dict[str, Thing] = field(default_factory=dict)
    places: dict[str, Place] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)

    def say(self, sentence: str) -> None:
        self.trace.append(sentence)

    def render(self) -> str:
        return "\n\n".join(self.trace)


NAMES = ["Tavi", "Mira", "Niko", "Lina", "Rumi", "Oren"]
COMPANIONS = ["Pip the fox", "Mallow the magpie", "Bram the badger"]
VILLAGES = ["Hazelbrook", "Cloverfield", "Willowmere"]
VESSELS = ["a blue clay pitcher", "a little copper pail", "a wooden water flask"]

PLOTS = [
    {
        "id": "alder_bridge",
        "title": "the alder bridge",
        "obstacle": "A young alder had fallen across the brook, and the hill spring's water was spilling into the bracken instead of reaching the village channel",
        "clue": "The moss on the stones was wet only on the upstream side of the fallen trunk",
        "helper_role": "the careful bridge keeper",
        "helper_name": "Keeper Sella",
        "helper_line": "“That trunk is holding the bank together; we must not yank it loose.”",
        "runner_line": "“Then show me where a small channel can carry the water safely.”",
        "thought": "If I pull hard, I may break the bank; if I watch the water, it may show us another way.",
        "action": "Tavi and Keeper Sella laid smooth stones into a shallow side channel, leaving the alder and its mossy bank undisturbed",
        "resolution": "The spring flowed around the trunk and rejoined the village channel",
        "ending": "by evening the blue pitcher stood full beside the village well, while a clear ribbon of water winked between the stones",
        "lesson": "a quick runner is most useful when a thoughtful heart chooses the path",
        "safe": True,
    },
    {
        "id": "beaver_meadow",
        "title": "the beaver meadow",
        "obstacle": "A beaver's twig dam had raised the stream, leaving the old channel to the village dry",
        "clue": "Tiny pawprints crossed the wet mud beside a narrow trickle that still slipped past the dam",
        "helper_role": "the meadow keeper",
        "helper_name": "Aunt Fen",
        "helper_line": "“The beaver built this pool for its family; we should leave its home standing.”",
        "runner_line": "“Could we guide a little of the overflow toward the thirsty well?”",
        "thought": "The water is not lost, and neither is the beaver's home; perhaps both can have what they need.",
        "action": "Tavi and Aunt Fen shaped a small grass-lined channel from the overflow, well away from the beaver's dam",
        "resolution": "A gentle stream reached the village while the beaver's pool stayed full",
        "ending": "the pitcher brimmed beside the well, and a beaver's nose bobbed happily in the shining meadow pool",
        "lesson": "a kind answer can make room for more than one neighbor",
        "safe": True,
    },
    {
        "id": "the_stone_turn",
        "title": "the stone turn",
        "obstacle": "Three round stones had rolled into the spring's narrow channel and sent the water toward a thorny hollow",
        "clue": "A line of bright, damp clover marked the channel the spring used before the stones shifted",
        "helper_role": "the stone mason",
        "helper_name": "Mason Orla",
        "helper_line": "“Those stones are heavy, and the bank is slick. Let me set them safely.”",
        "runner_line": "“I can clear the little twigs and keep the clover path visible.”",
        "thought": "My legs can hurry, but they cannot make a slippery stone light; I should help in a way that is safe.",
        "action": "Tavi marked the old waterway with clover while Mason Orla moved the stones with a wooden lever",
        "resolution": "The stones settled firmly, and the spring returned to its old channel",
        "ending": "at sunset, the pitcher gleamed full beside the well, and a green clover line followed the water home",
        "lesson": "knowing when to ask a skilled helper is a kind of courage",
        "safe": True,
    },
    {
        "id": "the_reed_gate",
        "title": "the reed gate",
        "obstacle": "A loose reed gate had swung shut across the spring's little channel",
        "clue": "One pale feather caught in the gate showed which way the breeze had pushed it",
        "helper_role": "the spring keeper",
        "helper_name": "Grandmother Eda",
        "helper_line": "“The gate is tangled in reeds; a sharp tug could tear the whole bank.”",
        "runner_line": "“I will hold the reeds aside while you free its hinge.”",
        "thought": "I wanted to be the hero who opened it alone, but the spring matters more than my pride.",
        "action": "Tavi held the reeds gently aside while Grandmother Eda eased the gate's hinge free",
        "resolution": "The gate swung open without tearing the bank, and water slipped down the channel again",
        "ending": "the pitcher rested full at the village well as the reed gate stood open beneath a drifting feather",
        "lesson": "a good runner knows that shared work can be stronger than a grand gesture",
        "safe": True,
    },
    {
        "id": "the_rooted_spring",
        "title": "the rooted spring",
        "obstacle": "A mat of fallen leaves covered the spring's little opening, and its water had begun to seep beneath the path",
        "clue": "A thin silver thread of water appeared wherever the leaves were thinnest",
        "helper_role": "the hill gardener",
        "helper_name": "Moss",
        "helper_line": "“The spring is breathing through those leaves. We should lift them gently, not dig.”",
        "runner_line": "“I can gather the loose leaves into a basket while you watch the opening.”",
        "thought": "The smallest trickle is a promise; I must not smother it by rushing in with my hands.",
        "action": "Tavi gathered the loose leaves while the hill gardener lifted the damp mat from the spring's opening",
        "resolution": "The spring bubbled freely again without a spade ever touching its roots",
        "ending": "clear water filled the pitcher, and a silver thread ran beside the path under a crown of bright leaves",
        "lesson": "patient care can uncover a way forward without causing new harm",
        "safe": True,
    },
    {
        "id": "the_moonlit_flume",
        "title": "the moonlit flume",
        "obstacle": "A wooden flume had slipped sideways, and the spring was pouring over its edge onto the hillside",
        "clue": "A wet stripe on the flume's post showed where its edge had rested before",
        "helper_role": "the millwright",
        "helper_name": "Master Jun",
        "helper_line": "“The flume is too high for you to lift, little runner.”",
        "runner_line": "“I can bring your wedges and keep everyone clear while you mend it.”",
        "thought": "I can run for the tools instead of pretending I can lift what is too heavy.",
        "action": "Tavi fetched Master Jun's wooden wedges and marked a clear space while the millwright reset the flume",
        "resolution": "The flume rested level again, carrying the spring water toward the thirsty village",
        "ending": "the pitcher shone full under the moon, and the repaired flume carried a bright thread of water home",
        "lesson": "a runner's speed shines brightest when it brings the right help",
        "safe": True,
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A folk-tale storyworld about a runner, a thirsty village, and a thoughtful choice."
    )
    parser.add_argument("--name")
    parser.add_argument("--companion")
    parser.add_argument("--village")
    parser.add_argument("--vessel")
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


def _choice(value: Optional[str], choices: list[str], label: str, rng: random.Random) -> str:
    if value is None:
        return rng.choice(choices)
    if value not in choices:
        raise StoryError(f"Unknown {label} {value!r}. Choose one of: {', '.join(choices)}.")
    return value


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=None,
        name=_choice(args.name, NAMES, "runner name", rng),
        companion=_choice(args.companion, COMPANIONS, "companion", rng),
        village=_choice(args.village, VILLAGES, "village", rng),
        vessel=_choice(args.vessel, VESSELS, "water vessel", rng),
        plot_id=PLOTS[rng.randrange(len(PLOTS))]["id"],
    )


def asp_facts() -> str:
    from storyworlds import asp

    facts: list[str] = []
    for plot in PLOTS:
        sid = plot["id"]
        facts.extend(
            [
                asp.fact("plot", sid),
                asp.fact("has_clue", sid),
                asp.fact("has_helper", sid),
                asp.fact("safe_method", sid) if plot["safe"] else "",
                asp.fact("restores_spring", sid),
            ]
        )
    return "\n".join(fact for fact in facts if fact)


def asp_program(show: str = "#show reasonable_plot/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable_plots() -> set[str]:
    return {
        plot["id"]
        for plot in PLOTS
        if plot["safe"]
        and plot["clue"]
        and plot["helper_name"]
        and plot["action"]
        and plot["resolution"]
    }


def asp_verify() -> int:
    from storyworlds import asp

    symbols = asp.one_model(asp_program())
    asp_plots = {row[0] for row in asp.atoms(symbols, "reasonable_plot")}
    py_plots = python_reasonable_plots()
    if asp_plots != py_plots:
        print(f"MISMATCH: ASP plots={sorted(asp_plots)} Python plots={sorted(py_plots)}")
        return 1

    for index, plot in enumerate(PLOTS):
        params = StoryParams(
            seed=index,
            name=NAMES[index % len(NAMES)],
            companion=COMPANIONS[index % len(COMPANIONS)],
            village=VILLAGES[index % len(VILLAGES)],
            vessel=VESSELS[index % len(VESSELS)],
            plot_id=plot["id"],
        )
        sample = generate(params)
        if (
            plot["title"] not in sample.story
            or params.name not in sample.story
            or "thought" not in sample.story.lower()
            or sample.world.facts["plot_id"] != plot["id"]
            or not sample.story_qa
            or not any(mark in sample.story for mark in ("“", "”"))
        ):
            print(f"FAIL: generated story did not exercise plot {plot['id']}")
            return 1
    print("OK: ASP and Python agree; every registered plot generates a grounded story.")
    return 0


def generate(params: StoryParams) -> StorySample:
    plot = next((item for item in PLOTS if item["id"] == params.plot_id), None)
    if plot is None:
        raise StoryError(f"Unknown plot {params.plot_id!r}; choose a registered runner's tale.")

    world = World(params=params)
    runner = Person(params.name, "runner")
    companion_name = params.companion.split(" the ")[0]
    companion = Person(companion_name, params.companion.split(" the ")[-1])
    vessel = Thing(params.vessel, "water vessel")
    well = Place(f"{params.village} village well", "village well")
    spring = Place("the hill spring", "spring")

    world.people[runner.name] = runner
    world.people[companion.name] = companion
    world.things[vessel.name] = vessel
    world.places[well.name] = well
    world.places[spring.name] = spring

    runner.add_meter("distance_to_spring", 3)
    runner.add_meter("water_carried", 0)
    runner.add_meme("hope", 1)
    runner.add_meme("worry", 1)
    companion.add_meme("trust", 1)
    vessel.add_meter("water", 0)
    spring.meters["flow"] = 0.25
    well.meters["water"] = 0

    p = params
    world.say(
        f"In the old days, when hills still whispered to the streams, the well at {p.village} ran dry."
    )
    world.say(
        f"The village elders gave {p.name}, their swift young runner, {p.vessel} and asked for water from the spring beyond the hill."
    )
    world.say(
        f"{p.name} set out with {p.companion} padding close behind, but on the path they found {plot['obstacle']}."
    )
    world.say(f"{plot['clue']}. The little stream was telling them where to look.")
    world.say(
        f"At first {p.name} wanted to race ahead. Inside, the runner thought, “{plot['thought']}”"
    )
    world.say(
        f"{p.name} called, “{plot['runner_line'][1:-1]}” {plot['helper_name']} answered, {plot['helper_line']}"
    )
    world.say(
        f"“We can do it together,” said {p.companion}. The kind words changed the plan: {plot['action']}."
    )

    runner.add_meter("distance_to_spring", -3)
    runner.add_meter("helpful_steps", 1)
    runner.add_meme("care", 1)
    runner.add_meme("courage", 1)
    runner.add_meme("worry", -1)
    companion.add_meme("trust", 1)
    spring.meters["flow"] = 1
    vessel.add_meter("water", 1)
    well.meters["water"] = 1

    world.say(
        f"{plot['resolution']}. {p.name} filled {p.vessel} and carried the water back to {p.village}."
    )
    world.say(
        f"{p.village} shared the spring water with every neighbor. {plot['lesson'].capitalize()}."
    )
    world.say(f"That night, {plot['ending']}.")

    world.facts = {
        "plot_id": plot["id"],
        "title": plot["title"],
        "obstacle": plot["obstacle"],
        "clue": plot["clue"],
        "helper": plot["helper_name"],
        "action": plot["action"],
        "resolution": plot["resolution"],
        "ending": plot["ending"],
        "lesson": plot["lesson"],
    }

    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Tell a folk tale about {p.name}, a runner from {p.village}, carrying {p.vessel} to a dry well.",
            f"Show how this clue changes the runner's plan: {plot['clue']}. Include an inner thought and a helpful exchange.",
            f"End with this concrete image: {plot['ending']}.",
        ],
        story_qa=[
            QAItem(
                question=f"What trouble did {p.name} find on the way to the spring?",
                answer=f"{plot['obstacle']}. This kept the spring water from reaching {p.village}, so the village well remained dry.",
            ),
            QAItem(
                question="What clue helped the runner understand the trouble?",
                answer=f"{plot['clue']}. The runner treated that small sign as evidence and changed the plan instead of rushing ahead.",
            ),
            QAItem(
                question="How did the runner and the helper solve the problem?",
                answer=f"{plot['action']}. They used the clue, shared the work, and chose a method that left the spring and its surroundings safe.",
            ),
            QAItem(
                question="What changed by the end of the tale?",
                answer=f"{plot['resolution']}. The runner then carried water back to {p.village}, whose well had been dry at the beginning.",
            ),
            QAItem(
                question="What picture closes the story?",
                answer=f"The closing picture is this: {plot['ending']}. It shows the water safely reaching the village and the change the runner helped make.",
            ),
        ],
        world_qa=[
            QAItem(
                question="What does a runner do in a folk tale?",
                answer="A runner carries a message or useful thing from one place to another, often meeting a challenge along the way.",
            ),
            QAItem(
                question="What is an inner monologue?",
                answer="An inner monologue is a character's private thought. It lets readers hear how the character weighs a choice before acting.",
            ),
            QAItem(
                question="Why can a clue matter in a story?",
                answer="A clue gives a character evidence about a problem, so the character can choose a wiser action instead of guessing.",
            ),
        ],
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.extend(["", "== (2) Story questions =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== (3) World knowledge =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for person in world.people.values():
        lines.append(f"  {person.name} ({person.role}) meters={person.meters} memes={person.memes}")
    for thing in world.things.values():
        lines.append(f"  {thing.name} ({thing.kind}) meters={thing.meters} memes={thing.memes}")
    for place in world.places.values():
        lines.append(f"  {place.name} ({place.kind}) meters={place.meters} memes={place.memes}")
    return "\n".join(lines)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.n < 1 and not args.all and not args.verify and not args.show_asp and not args.asp:
        raise SystemExit("-n must be at least 1")

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        from storyworlds import asp

        symbols = asp.one_model(asp_program())
        for plot_id, in sorted(asp.atoms(symbols, "reasonable_plot")):
            print(plot_id)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        base_params = resolve_params(args, random.Random(base_seed))
        samples = [
            generate(replace(base_params, seed=base_seed + index, plot_id=plot["id"]))
            for index, plot in enumerate(PLOTS)
        ]
    else:
        for index in range(args.n):
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
