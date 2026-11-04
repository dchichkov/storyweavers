#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Optional


_REPO_ROOT = next(
    (
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "storyworlds" / "results.py").is_file()
    ),
    None,
)
if _REPO_ROOT is not None and str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
plot_rescue(S) :-
    registered_scenario(S),
    has_problem(S),
    has_clue(S),
    safe_choice(S),
    helper_method(S),
    reflective_turn(S),
    completed_resolution(S),
    ending_image(S).

reasonable_story :-
    selected(S),
    plot_rescue(S),
    feature(inner_monologue),
    feature(spoken_dialogue),
    goal(moon_bean_planted).

#show plot_rescue/1.
#show reasonable_story/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    runner: str = "Liora"
    keeper: str = "Keeper Brindle"
    village: str = "Thistlewick"
    plot: str = "the shared moon-bean plot"
    token: str = "blue thread"


PARAMETER_REGISTRIES = {
    "runner": ("Liora", "Perrin", "Safi", "Tavi", "Anwen"),
    "keeper": ("Keeper Brindle", "Aunt Marigold", "Old Tansy"),
    "village": ("Thistlewick", "Mallowmere", "Hazel Vale"),
    "plot": (
        "the shared moon-bean plot",
        "the village garden plot",
        "the moonlit bean plot",
    ),
    "token": ("blue thread", "green ribbon", "red wool cord"),
}
REGISTRIES = PARAMETER_REGISTRIES


SCENARIOS = [
    {
        "id": "leaf_sluice",
        "title": "The Leaf in the Sluice",
        "obstacle": (
            "A broad willow leaf had lodged across the narrow sluice, "
            "so spring water curled away from the rows."
        ),
        "clue": (
            "A bright thread of water slipped beneath the leaf, while the "
            "furrow beyond it stayed dusty."
        ),
        "mistake": "At first, {runner} reached to yank the leaf out of the sluice.",
        "thought": (
            "If I pull too hard, the sluice may close tighter. "
            "The water is showing me where to begin."
        ),
        "question": (
            "The water curls beneath that leaf, but the row is dry. "
            "How can we open the sluice gently?"
        ),
        "answer": (
            "Slip this straight reed under its stem; a careful lift will free "
            "the water without tearing the channel."
        ),
        "reply": (
            "I will hold the reed low while you guide the leaf to the bank."
        ),
        "tool": "a straight reed",
        "action": (
            "Together, {runner} held a straight reed while {keeper} lifted "
            "the willow leaf by its stem and laid it on the bank."
        ),
        "resolution": (
            "At once, the spring ran down the open furrow. "
            "{runner} planted the moon-bean seed in soil softened by water."
        ),
        "ending": (
            "At moonrise, a bright drop trembled on the bean row while the "
            "clear channel sang softly beside it."
        ),
        "lesson": (
            "A runner's surest speed begins with a thoughtful pause."
        ),
    },
    {
        "id": "fieldstone",
        "title": "The Stone That Turned the Water",
        "obstacle": (
            "A round fieldstone had rolled into the channel and sent spring "
            "water toward the footpath."
        ),
        "clue": (
            "The stone's wet side faced the empty furrow, and a shining trail "
            "crossed the path."
        ),
        "mistake": (
            "At first, {runner} put both hands on the heavy stone and tried to shove it."
        ),
        "thought": (
            "That stone is heavier than haste. I should find a lever and keep "
            "my feet on the dry bank."
        ),
        "question": (
            "The water is running across the path. Can we move the stone "
            "without stepping into the slippery channel?"
        ),
        "answer": (
            "A forked willow branch makes a lever. Set its end under the stone "
            "and push from the bank."
        ),
        "reply": (
            "I will brace the branch while you guide the stone onto firm ground."
        ),
        "tool": "a forked willow branch",
        "action": (
            "Together, {runner} braced a forked willow branch from the dry bank "
            "while {keeper} eased the stone onto firm ground."
        ),
        "resolution": (
            "The spring returned to its proper furrow, and {runner} planted "
            "the moon-bean seed in the damp first row."
        ),
        "ending": (
            "At moonrise, the bean row glimmered with a ribbon of water, and "
            "the fieldstone rested harmlessly on the bank."
        ),
        "lesson": (
            "A careful plan can move what hurried strength cannot."
        ),
    },
    {
        "id": "mole_furrow",
        "title": "The Mole's Small Doorway",
        "obstacle": (
            "A fresh molehill had risen across one furrow and diverted the "
            "spring water away from the bean beds."
        ),
        "clue": (
            "The little mound quivered, and a mole's whiskers appeared at a "
            "small side hole."
        ),
        "mistake": (
            "At first, {runner} raised a hoe toward the mound to flatten it."
        ),
        "thought": (
            "If I strike the mound, I could bury its small maker. "
            "Water can take another road."
        ),
        "question": (
            "Would it be quicker to flatten the mound and send the water straight through?"
        ),
        "answer": (
            "A narrow side-furrow will carry the water around the mound and "
            "leave the mole's doorway whole."
        ),
        "reply": (
            "Then I will help shape the side-furrow, not disturb the little home."
        ),
        "tool": "a wooden scoop",
        "action": (
            "Together, {runner} used a wooden scoop to cut a narrow side-furrow, "
            "and {keeper} checked that it curved around the mole's doorway."
        ),
        "resolution": (
            "The side-furrow carried spring water around the mole's home to "
            "the bean row, where {runner} planted the moon-bean seed."
        ),
        "ending": (
            "At moonrise, a shining stream curved around the mole's untouched "
            "doorway and into the newly planted row."
        ),
        "lesson": (
            "Kindness makes room for a neighbor, even a very small one."
        ),
    },
    {
        "id": "loose_gate",
        "title": "The Gate Without Its Peg",
        "obstacle": (
            "The little water gate swung loose on its hinge because its wooden "
            "peg had gone missing."
        ),
        "clue": (
            "A narrow scrape in the mud led from the empty hinge to a spare "
            "peg beneath the elderberry bush."
        ),
        "mistake": (
            "At first, {runner} tugged at the gate, hoping to force it straight."
        ),
        "thought": (
            "Pulling may bend the hinge. The scrape shows me where the missing "
            "peg rolled."
        ),
        "question": (
            "Should I pull the gate straight, or can we find what is missing?"
        ),
        "answer": (
            "Follow the scrape beneath the elderberry for our spare peg; then "
            "we can set the gate safely."
        ),
        "reply": (
            "I will fetch it without wrenching the hinge."
        ),
        "tool": "a spare wooden peg",
        "action": (
            "Together, {runner} fetched the spare peg from beneath the elderberry "
            "while {keeper} held the gate level, and they fitted it into the hinge."
        ),
        "resolution": (
            "The gate stood straight and let spring water enter the channel, "
            "so {runner} planted the moon-bean seed in the first row."
        ),
        "ending": (
            "At moonrise, the gate stood firm with its peg snug in place, and "
            "water filled the bean furrow."
        ),
        "lesson": (
            "A good runner follows the clue instead of fighting the trouble."
        ),
    },
]


OPENINGS = [
    (
        "Long ago, in {village}, spring water ran from a hill spring to {plot}. "
        "The villagers saved one moon-bean seed for planting before moonrise. "
        "{runner}, the village runner, carried it in a pouch tied with a {token}."
    ),
    (
        "Once, the people of {village} kept a moon-bean seed for {plot}. "
        "They said it would wake only if spring water reached it before the "
        "moon appeared. This year, {runner} carried the seed in a pouch tied "
        "with a {token}."
    ),
    (
        "In the old days, a hill spring watered {plot} in {village}. "
        "Each year, one moon-bean seed was planted there before moonrise, and "
        "{runner} had been chosen to carry it in a pouch tied with a {token}."
    ),
    (
        "People in {village} said a moon-bean listened for the sound of running "
        "water. {runner}, the village runner, hurried toward {plot} with the "
        "year's seed in a pouch tied with a {token}."
    ),
]


TURN_LINES = [
    "The pause turned a quick reach into a careful question.",
    "The clue became useful when {runner} stopped long enough to study it.",
    "A listening mind found a safer path than hurried hands could find.",
    "Instead of guessing alone, {runner} brought the clue to someone who knew the garden.",
]


@dataclass
class Character:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, delta: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + delta

    def add_meme(self, key: str, delta: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + delta


@dataclass
class ObjectThing:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, delta: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + delta

    def add_meme(self, key: str, delta: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + delta


@dataclass
class GardenPlot:
    name: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, delta: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + delta

    def add_meme(self, key: str, delta: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + delta


@dataclass
class World:
    params: StoryParams
    characters: dict[str, Character] = field(default_factory=dict)
    objects: dict[str, ObjectThing] = field(default_factory=dict)
    plot: Optional[GardenPlot] = None
    trace: list[str] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)

    def say(self, line: str) -> None:
        self.trace.append(line)

    def add_character(self, character: Character) -> Character:
        self.characters[character.name] = character
        return character

    def add_object(self, obj: ObjectThing) -> ObjectThing:
        self.objects[obj.name] = obj
        return obj

    def render(self) -> str:
        return "\n\n".join(self.trace)


def _scenario_for_seed(seed: Optional[int]) -> dict[str, str]:
    index = (seed or 0) % len(SCENARIOS)
    return SCENARIOS[index]


def _scenario_by_id(scenario_id: str) -> Optional[dict[str, str]]:
    return next((scenario for scenario in SCENARIOS if scenario["id"] == scenario_id), None)


def _validate_params(params: StoryParams) -> None:
    for field_name, choices in PARAMETER_REGISTRIES.items():
        value = getattr(params, field_name)
        if value not in choices:
            allowed = ", ".join(repr(choice) for choice in choices)
            raise StoryError(
                f"Unknown {field_name} {value!r}; choose one of: {allowed}."
            )
    if params.seed is not None and not isinstance(params.seed, int):
        raise StoryError("The story seed must be an integer.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=(
            "A folk-tale storyworld about a village runner, a thirsty garden plot, "
            "and the thoughts that make a safe solution possible."
        )
    )
    ap.add_argument("--runner")
    ap.add_argument("--keeper")
    ap.add_argument("--village")
    ap.add_argument("--plot")
    ap.add_argument("--token")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    values: dict[str, str] = {}
    for field_name, choices in PARAMETER_REGISTRIES.items():
        supplied = getattr(args, field_name, None)
        values[field_name] = supplied if supplied is not None else rng.choice(choices)

    params = StoryParams(seed=None, **values)
    _validate_params(params)
    return params


def python_reasonable_story(
    params: Optional[StoryParams] = None,
    scenario_id: Optional[str] = None,
) -> bool:
    if params is not None:
        try:
            _validate_params(params)
        except StoryError:
            return False

    if scenario_id is None:
        scenario_id = _scenario_for_seed(params.seed if params is not None else None)["id"]

    scenario = _scenario_by_id(scenario_id)
    if scenario is None:
        return False

    required_text = (
        "obstacle",
        "clue",
        "thought",
        "question",
        "answer",
        "reply",
        "action",
        "resolution",
        "ending",
        "lesson",
    )
    return (
        all(isinstance(scenario.get(key), str) and scenario[key].strip() for key in required_text)
        and bool(scenario.get("safe_method", True))
        and bool(scenario.get("reflective_turn", True))
        and bool(scenario.get("has_dialogue", True))
    )


def asp_facts(scenario_id: Optional[str] = None) -> str:
    from storyworlds import asp

    selected_id = scenario_id or SCENARIOS[0]["id"]
    if _scenario_by_id(selected_id) is None:
        raise StoryError(f"Unknown story scenario {selected_id!r}.")

    lines = [
        asp.fact("feature", "inner_monologue"),
        asp.fact("feature", "spoken_dialogue"),
        asp.fact("goal", "moon_bean_planted"),
    ]
    for scenario in SCENARIOS:
        sid = scenario["id"]
        lines.append(asp.fact("registered_scenario", sid))
        if scenario.get("obstacle"):
            lines.append(asp.fact("has_problem", sid))
        if scenario.get("clue"):
            lines.append(asp.fact("has_clue", sid))
        if scenario.get("safe_method", True):
            lines.append(asp.fact("safe_choice", sid))
        if scenario.get("action"):
            lines.append(asp.fact("helper_method", sid))
        if scenario.get("thought"):
            lines.append(asp.fact("reflective_turn", sid))
        if scenario.get("resolution"):
            lines.append(asp.fact("completed_resolution", sid))
        if scenario.get("ending"):
            lines.append(asp.fact("ending_image", sid))
    lines.append(asp.fact("selected", selected_id))
    return "\n".join(lines)


def asp_program(scenario_id: Optional[str] = None) -> str:
    return f"{asp_facts(scenario_id)}\n\n{ASP_RULES.strip()}\n"


def asp_verify() -> int:
    try:
        from storyworlds import asp
    except ImportError as err:
        print(f"ERROR: ASP verification needs the shared ASP helper and clingo: {err}")
        return 1

    for index, scenario in enumerate(SCENARIOS):
        sid = scenario["id"]
        py_ok = python_reasonable_story(scenario_id=sid)
        model = asp.one_model(asp_program(sid))
        asp_ok = bool(asp.atoms(model, "reasonable_story"))
        rescue_ok = (sid,) in asp.atoms(model, "plot_rescue")
        if asp_ok != py_ok or rescue_ok != py_ok:
            print(
                f"MISMATCH: scenario={sid} asp={asp_ok} "
                f"rescue={rescue_ok} python={py_ok}"
            )
            return 1

        sample = generate(StoryParams(seed=index))
        if sample.world is None or sample.world.plot is None:
            print(f"ERROR: generated story {sid} has no live garden plot.")
            return 1
        if sample.world.facts.get("scenario_id") != sid:
            print(f"ERROR: generated story selected the wrong scenario for {sid}.")
            return 1
        if not python_reasonable_story(sample.params):
            print(f"ERROR: generated story {sid} failed the Python reasonableness gate.")
            return 1
        if "Inside," not in sample.story or sample.story.count("“") < 4:
            print(f"ERROR: generated story {sid} is missing reflection or spoken dialogue.")
            return 1
        if (
            sample.world.plot.meters.get("water_flow", 0.0) <= 0.0
            or sample.world.plot.meters.get("soil_moisture", 0.0) <= 0.5
            or sample.world.plot.meters.get("seed_planted", 0.0) < 1.0
        ):
            print(f"ERROR: generated story {sid} did not resolve its garden problem.")
            return 1
        qa_text = " ".join(
            [item.question + " " + item.answer for item in sample.story_qa]
        )
        if "{" in sample.story or "}" in sample.story or "meters=" in qa_text:
            print(f"ERROR: generated story {sid} contains scaffold text.")
            return 1

    print(
        f"OK: ASP and Python agree across {len(SCENARIOS)} scenarios; "
        "all generated stories include a reflective turn, dialogue, and a resolved plot."
    )
    return 0


def generate_story(world: World) -> None:
    p = world.params
    _validate_params(p)
    seed = p.seed or 0
    scenario = _scenario_for_seed(seed)
    if not python_reasonable_story(p, scenario["id"]):
        raise StoryError("This combination does not have a safe, complete garden resolution.")

    values = {
        "runner": p.runner,
        "keeper": p.keeper,
        "village": p.village,
        "plot": p.plot,
        "token": p.token,
    }
    scenario_text = {
        key: value.format(**values) if isinstance(value, str) else value
        for key, value in scenario.items()
    }
    opening = OPENINGS[(seed // len(SCENARIOS)) % len(OPENINGS)].format(**values)
    turn_line = TURN_LINES[(seed // 3) % len(TURN_LINES)].format(**values)

    runner = world.add_character(
        Character(
            name=p.runner,
            role="village runner",
            meters={"energy": 1.0, "distance_run": 0.0},
            memes={"determination": 0.5, "worry": 0.0, "hope": 0.5},
        )
    )
    keeper = world.add_character(
        Character(
            name=p.keeper,
            role="garden keeper",
            meters={"garden_knowledge": 1.0},
            memes={"patience": 1.0, "trust": 0.4},
        )
    )
    world.plot = GardenPlot(
        name=p.plot,
        meters={
            "water_flow": 0.0,
            "soil_moisture": 0.1,
            "channel_open": 0.0,
            "seed_planted": 0.0,
        },
        memes={"hope": 0.4, "welcome": 0.5},
    )
    seed_object = world.add_object(
        ObjectThing(
            name="the moon-bean seed",
            kind="folk-tale seed",
            meters={"planted": 0.0, "dry": 1.0},
            memes={"promise": 1.0},
        )
    )
    token_object = world.add_object(
        ObjectThing(
            name=f"a {p.token}",
            kind="runner's row marker",
            meters={"marks_row": 0.0},
            memes={"familiarity": 1.0},
        )
    )
    tool_object = world.add_object(
        ObjectThing(
            name=scenario_text["tool"],
            kind="garden tool",
            meters={"used_safely": 0.0},
            memes={"usefulness": 0.5},
        )
    )

    world.say(opening)
    runner.add_meter("distance_run", 3.0)
    runner.add_meter("energy", -0.2)
    world.say(
        f"When {p.runner} reached {p.plot}, the first row lay dusty. "
        f"{scenario_text['obstacle']}"
    )
    runner.add_meme("worry", 0.6)
    world.plot.add_meme("hope", -0.2)
    world.say(
        f"{scenario_text['clue']} The moon-bean could not wake in dry earth, "
        "and the moon was already climbing toward the hill."
    )

    world.say(scenario_text["mistake"])
    world.say(
        f"Inside, {p.runner} thought, “{scenario_text['thought']}” "
        f"{turn_line}"
    )
    runner.add_meme("reflection", 1.0)
    runner.add_meme("worry", -0.25)
    runner.add_meme("attention", 1.0)

    world.say(f"{p.runner} called to {p.keeper}, “{scenario_text['question']}”")
    world.say(f"{p.keeper} answered, “{scenario_text['answer']}”")
    world.say(f"“{scenario_text['reply']}” replied {p.runner}.")
    runner.add_meme("trust", 0.5)
    runner.add_meme("confidence", 0.5)
    keeper.add_meter("guidance_given", 1.0)
    keeper.add_meme("trust", 0.3)

    world.say(scenario_text["action"])
    tool_object.add_meter("used_safely", 1.0)
    tool_object.add_meme("usefulness", 0.5)
    runner.add_meter("energy", -0.15)
    runner.add_meme("care", 1.0)

    world.plot.add_meter("channel_open", 1.0)
    world.plot.add_meter("water_flow", 1.0)
    world.plot.add_meter("soil_moisture", 0.85)
    world.plot.add_meter("seed_planted", 1.0)
    world.plot.add_meme("hope", 0.8)
    world.plot.add_meme("welcome", 0.5)
    seed_object.add_meter("planted", 1.0)
    seed_object.add_meter("dry", -1.0)
    seed_object.add_meme("promise", 0.5)
    token_object.add_meter("marks_row", 1.0)
    token_object.add_meme("familiarity", 0.5)
    runner.add_meme("hope", 0.5)
    runner.add_meme("joy", 0.7)

    if (
        world.plot.meters["water_flow"] <= 0.0
        or world.plot.meters["soil_moisture"] <= 0.5
        or world.plot.meters["seed_planted"] < 1.0
    ):
        raise StoryError("The garden plot is still too dry for the moon-bean.")

    world.say(scenario_text["resolution"])
    world.say(
        f"Before moonrise, {p.runner} untied the {p.token} from the pouch and "
        "knotted it to a slender stake, so no one would tread on the new row."
    )
    world.say(
        f"The elders of {p.village} kept a saying from that night: "
        f"{scenario_text['lesson']} {scenario_text['ending']}"
    )

    world.facts = {
        "scenario_id": scenario["id"],
        "scenario_title": scenario["title"],
        "obstacle": scenario_text["obstacle"],
        "clue": scenario_text["clue"],
        "mistake": scenario_text["mistake"],
        "thought": scenario_text["thought"],
        "question": scenario_text["question"],
        "answer": scenario_text["answer"],
        "reply": scenario_text["reply"],
        "action": scenario_text["action"],
        "resolution": scenario_text["resolution"],
        "ending_image": scenario_text["ending"],
        "lesson": scenario_text["lesson"],
        "tool": scenario_text["tool"],
    }


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    facts = world.facts
    return [
        QAItem(
            question=f"What kept spring water from reaching the moon-bean row?",
            answer=(
                f"{facts['obstacle']} The soil stayed too dry for the moon-bean "
                f"that {p.runner} had brought to {p.plot}."
            ),
        ),
        QAItem(
            question=f"What clue helped {p.runner} understand where to look?",
            answer=(
                f"{facts['clue']} That small sign gave {p.runner} a reason to "
                f"pause and ask {p.keeper} for help instead of guessing."
            ),
        ),
        QAItem(
            question=f"How did {p.runner}'s inner thought change the plan?",
            answer=(
                f"At first, {facts['mistake'].removeprefix('At first, ')} "
                f"Inside, {p.runner} thought, “{facts['thought']}” The thought "
                "led to a careful question rather than a hurried action."
            ),
        ),
        QAItem(
            question="How did the runner and the keeper solve the problem together?",
            answer=(
                f"{p.runner} asked, “{facts['question']}” {p.keeper} answered, "
                f"“{facts['answer']}” {p.runner} replied, “{facts['reply']}” "
                f"{facts['action']} {facts['resolution']}"
            ),
        ),
        QAItem(
            question="What concrete image closes the tale?",
            answer=(
                f"{facts['ending_image']} The repaired channel and planted row "
                "show that the runner's careful choice changed the garden."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a village runner do in a folk tale?",
            answer=(
                "A village runner carries an important message or object from "
                "one place to another, using quick feet and good judgment."
            ),
        ),
        QAItem(
            question="What is an inner monologue?",
            answer=(
                "An inner monologue is a character's private thought. It lets "
                "readers hear how the character understands a problem and chooses "
                "what to do next."
            ),
        ),
        QAItem(
            question="What is a garden plot?",
            answer=(
                "A garden plot is a small piece of ground where people grow plants "
                "and care for the soil, seeds, and water."
            ),
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    facts = world.facts
    return [
        (
            f"Tell a child-facing folk tale about {p.runner}, the village runner, "
            f"bringing a moon-bean seed to {p.plot}."
        ),
        (
            f"Show how this clue changes the runner's choice: {facts['clue']} "
            "Include a clear inner thought and spoken dialogue with the keeper."
        ),
        (
            f"Resolve the garden trouble safely and end with this image: "
            f"{facts['ending_image']}"
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.extend(["", "== (2) Story questions =="])
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.extend(["", "== (3) World knowledge =="])
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for character in world.characters.values():
        lines.append(
            f"  {character.name} ({character.role}) "
            f"meters={character.meters} memes={character.memes}"
        )
    if world.plot is not None:
        lines.append(
            f"  {world.plot.name} (garden plot) "
            f"meters={world.plot.meters} memes={world.plot.memes}"
        )
    for obj in world.objects.values():
        lines.append(
            f"  {obj.name} ({obj.kind}) meters={obj.meters} memes={obj.memes}"
        )
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = World(params=params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        selected = _scenario_for_seed(args.seed)["id"]
        print(asp_program(selected))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        from storyworlds import asp

        selected = _scenario_for_seed(args.seed)["id"]
        model = asp.one_model(asp_program(selected))
        print("reasonable_story" if asp.atoms(model, "reasonable_story") else "(no reasonable_story)")
        return

    if args.n < 1 and not args.all:
        print("StoryError: -n must be at least 1.", file=sys.stderr)
        raise SystemExit(2)

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    try:
        if args.all:
            base_params = resolve_params(args, random.Random(base_seed))
            count = len(SCENARIOS)
            start_index = base_seed % count
            for index in range(count):
                scenario_index = (start_index + index) % count
                story_seed = base_seed + ((scenario_index - start_index) % count)
                samples.append(generate(replace(base_params, seed=story_seed)))
        else:
            for offset in range(args.n):
                story_seed = base_seed + offset
                params = resolve_params(args, random.Random(story_seed))
                params.seed = story_seed
                samples.append(generate(params))
    except StoryError as err:
        print(f"StoryError: {err}", file=sys.stderr)
        raise SystemExit(2)

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
