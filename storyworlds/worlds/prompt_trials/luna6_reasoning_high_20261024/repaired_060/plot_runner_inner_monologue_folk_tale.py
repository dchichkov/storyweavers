#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


_REPO_ROOT = None
for _parent in Path(__file__).resolve().parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        _REPO_ROOT = _parent
        break
if _REPO_ROOT is not None:
    sys.path.insert(0, str(_REPO_ROOT))
    sys.path.insert(0, str(_REPO_ROOT / "storyworlds"))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
% A runner can finish the seed-delivery tale when the chosen route is safe,
% observation supplies a clue, and a helper is available for that route.
ready :- task(seed_delivery), destination(community_plot),
         selected_route(R), safe_route(R), clue_for(R), helper_for(R).
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    runner: str = "Mira"
    helper: str = "Brindle"
    seed_name: str = "moonbean seed"
    plot: str = "Moon Plot"
    village: str = "Greenhollow"


PARAM_REGISTRIES = {
    "runner": ["Mira", "Tavi", "Nell", "Pip", "Oren", "Lark"],
    "helper": ["Brindle", "Clover", "Redtail", "Pippin", "Hazel"],
    "seed_name": ["moonbean seed", "silver bean seed", "star-bean seed"],
    "plot": ["Moon Plot", "Clover Plot", "Lantern Plot"],
    "village": ["Greenhollow", "Willowmere", "Thistlewick"],
}


SCENARIOS = [
    {
        "key": "wind",
        "title": "the wind-swept lane",
        "obstacle": "A gust snatched the wool cover from the seed pouch and sent it skittering toward the rocky slope.",
        "clue": "The willow leaves bent toward a low stone wall, where the air was calm.",
        "thought": "I could chase the cover, but a seed is not worth a fall. I should look for shelter first.",
        "fox_line": "The ridge wind is strong. What did the willows tell you?",
        "runner_line": "They bend toward the low wall. Let us keep to its sheltered side.",
        "action": "Brindle pinned the cover with a paw, and the runner tucked the pouch safely inside a coat before following the wall.",
        "route_length": 5,
        "ending_detail": "a corner of the old wool cover fluttered like a tiny flag beside the new shoot",
    },
    {
        "key": "stream",
        "title": "the rising stream",
        "obstacle": "The evening stream had covered the stepping stones that crossed the runner's usual path.",
        "clue": "A dry stripe beneath the alder roots marked a higher footpath along the bank.",
        "thought": "The quick stones are gone beneath the water. If I watch carefully, another way may still be waiting.",
        "fox_line": "The crossing is hidden. Shall we hurry through the water?",
        "runner_line": "No. That dry mark leads above the current. Let us follow the roots.",
        "action": "Brindle tested the bank path, then guided the runner along its firm, raised ground.",
        "route_length": 7,
        "ending_detail": "a string of bright raindrops shone on the alder leaves above the plot",
    },
    {
        "key": "fog",
        "title": "the foggy fork",
        "obstacle": "A thick fog swallowed the path where it split into three lanes.",
        "clue": "From the hill, the little bell beside the plot rang three slow notes through the fog.",
        "thought": "If I run before I know the direction, I will only get lost faster. I can stop and listen.",
        "fox_line": "I can smell the wet grass, but not which lane reaches the hill.",
        "runner_line": "Listen: the plot bell is sounding from that way. We will follow its notes, one bend at a time.",
        "action": "Brindle stayed close while the runner listened for each bell note before taking the next turn.",
        "route_length": 6,
        "ending_detail": "the last threads of fog curled away from the plot like a sleepy gray blanket",
    },
    {
        "key": "goat",
        "title": "the goat at the gate",
        "obstacle": "A shaggy goat stood across the narrow gate and stamped whenever the runner came near.",
        "clue": "Its little bell grew quiet when it lowered its head toward a patch of clover.",
        "thought": "A frightened goat is not a monster. I can make room for both of us.",
        "fox_line": "The gate is blocked. Should we squeeze past?",
        "runner_line": "No. The goat is hungry, not wicked. I will offer clover and give it space.",
        "action": "The runner laid a handful of clover well away from the seed pouch, and Brindle waited quietly while the goat stepped aside.",
        "route_length": 4,
        "ending_detail": "the goat's bell gave one soft note as it nibbled clover beyond the gate",
    },
    {
        "key": "bridge",
        "title": "the creaking bridge",
        "obstacle": "The small bridge groaned beneath the evening wind, and one plank had split down the middle.",
        "clue": "A row of old white stones continued along the bank toward the longer mill road.",
        "thought": "One brave leap could break the bridge and spill the seed. I should choose a sound road, not a showy one.",
        "fox_line": "The bridge looks shorter. Shall we try it?",
        "runner_line": "Those white stones mark the mill road. The longer way is the one we can trust.",
        "action": "Brindle led the runner along the white stones, leaving the broken bridge untouched.",
        "route_length": 8,
        "ending_detail": "one white road stone gleamed under the first drop of morning dew",
    },
    {
        "key": "brambles",
        "title": "the bramble shortcut",
        "obstacle": "A thorny hedge had swallowed the narrow shortcut to the hill.",
        "clue": "Berry birds fluttered from the brambles to a broad, clear track beyond them.",
        "thought": "The short way scratches, but the long way still leads to the plot. I can choose the kinder path.",
        "fox_line": "I could dart through those thorns, but the pouch might snag.",
        "runner_line": "The birds showed us a clear track. Let us take it without tearing the hedge.",
        "action": "Brindle and the runner followed the wide track, leaving the thorny hedge and its berries undisturbed.",
        "route_length": 6,
        "ending_detail": "a berry bird perched near the plot, its beak bright with red juice",
    },
]


OPENINGS = [
    "Long ago, when the moon still listened at windows, the runner {runner} lived in {village}.",
    "In {village}, where the hills wore green shawls, {runner} was known as a swift and thoughtful runner.",
    "Once, in the village of {village}, {runner} could carry a message faster than the evening wind.",
    "Beyond the old willow road stood {village}, and there lived a runner named {runner}.",
    "The people of {village} told many tales, but they trusted {runner} to carry the most precious one.",
    "In the days when seeds were said to remember kind hands, {runner} ran the lanes of {village}.",
    "At the edge of {village}, beneath a moon as round as a bowl, the runner {runner} began an important journey.",
    "There was once a small village called {village}, and its quickest runner was {runner}.",
]


FOLK_TALE_CLOSINGS = [
    "And folk still say that quick feet are wisest when a listening heart guides them.",
    "From then on, the villagers said that a careful step can carry a hope farther than a hurried leap.",
    "So the old story teaches: a good runner carries kindness as carefully as any precious seed.",
    "The elders remembered that night whenever they saw a path: the safest way can still be a brave one.",
    "And that is why, in {village}, every new shoot is greeted with a story and a song.",
    "The moon smiled down, for patience had brought the seed home before morning.",
]


@dataclass
class Entity:
    name: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, delta: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + delta

    def add_meme(self, key: str, delta: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + delta


@dataclass
class Character(Entity):
    role: str = "neighbor"


@dataclass
class ObjectThing(Entity):
    kind: str = "object"


@dataclass
class Place(Entity):
    place_kind: str = "place"


@dataclass
class World:
    params: StoryParams
    characters: dict[str, Character] = field(default_factory=dict)
    objects: dict[str, ObjectThing] = field(default_factory=dict)
    places: dict[str, Place] = field(default_factory=dict)
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

    def add_place(self, place: Place) -> Place:
        self.places[place.name] = place
        return place

    def render(self) -> str:
        return "\n\n".join(self.trace)


def _validate_text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StoryError(f"{label} must be a non-empty name.")
    if len(value) > 60 or "\n" in value or "\r" in value or "{" in value or "}" in value:
        raise StoryError(f"{label} must be a short, single-line name without template braces.")
    return value.strip()


def validate_params(params: StoryParams) -> None:
    for field_name in ("runner", "helper", "seed_name", "plot", "village"):
        value = _validate_text(getattr(params, field_name), field_name.replace("_", " "))
        setattr(params, field_name, value)
    for field_name in ("seed_name", "plot", "village"):
        if getattr(params, field_name) not in PARAM_REGISTRIES[field_name]:
            choices = ", ".join(PARAM_REGISTRIES[field_name])
            raise StoryError(f"Unknown {field_name.replace('_', ' ')} {getattr(params, field_name)!r}; choose from: {choices}.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A folk-tale storyworld about a thoughtful runner carrying a seed to the village plot."
    )
    parser.add_argument("--runner")
    parser.add_argument("--helper")
    parser.add_argument("--seed-name")
    parser.add_argument("--plot")
    parser.add_argument("--village")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true", help="Generate one story for each route challenge.")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        seed=None,
        runner=args.runner or rng.choice(PARAM_REGISTRIES["runner"]),
        helper=args.helper or rng.choice(PARAM_REGISTRIES["helper"]),
        seed_name=args.seed_name or rng.choice(PARAM_REGISTRIES["seed_name"]),
        plot=args.plot or rng.choice(PARAM_REGISTRIES["plot"]),
        village=args.village or rng.choice(PARAM_REGISTRIES["village"]),
    )
    validate_params(params)
    return params


def scenario_for(seed: Optional[int]) -> dict[str, object]:
    return SCENARIOS[(seed or 0) % len(SCENARIOS)]


def python_reasonable_story(scenario: Optional[dict[str, object]] = None) -> bool:
    chosen = scenario or SCENARIOS[0]
    return bool(
        chosen.get("key")
        and chosen.get("safe", True)
        and chosen.get("clue")
        and chosen.get("fox_line")
        and chosen.get("runner_line")
        and chosen.get("action")
        and chosen.get("route_length")
    )


def asp_facts(scenario: Optional[dict[str, object]] = None) -> str:
    import asp

    chosen = scenario or SCENARIOS[0]
    lines = [
        asp.fact("task", "seed_delivery"),
        asp.fact("destination", "community_plot"),
        asp.fact("feature", "inner_monologue"),
        asp.fact("style", "folk_tale"),
    ]
    for item in SCENARIOS:
        lines.append(asp.fact("route_option", item["key"]))
    lines.append(asp.fact("selected_route", chosen["key"]))
    if chosen.get("safe", True):
        lines.append(asp.fact("safe_route", chosen["key"]))
    if chosen.get("clue"):
        lines.append(asp.fact("clue_for", chosen["key"]))
    if chosen.get("fox_line") and chosen.get("runner_line"):
        lines.append(asp.fact("helper_for", chosen["key"]))
    return "\n".join(lines)


def asp_program(scenario: Optional[dict[str, object]] = None) -> str:
    return f"{asp_facts(scenario)}\n{ASP_RULES}\n#show ready/0.\n"


def asp_verify() -> int:
    try:
        import asp
    except ModuleNotFoundError as err:
        print(f"ASP verification needs clingo via storyworlds/asp.py: {err}")
        return 2

    for index, scenario in enumerate(SCENARIOS):
        model = asp.one_model(asp_program(scenario))
        asp_ok = bool(asp.atoms(model, "ready"))
        py_ok = python_reasonable_story(scenario)
        if asp_ok != py_ok:
            print(f"MISMATCH for {scenario['key']}: asp={asp_ok} python={py_ok}")
            return 1

        params = StoryParams(
            seed=index,
            runner=PARAM_REGISTRIES["runner"][index % len(PARAM_REGISTRIES["runner"])],
            helper=PARAM_REGISTRIES["helper"][index % len(PARAM_REGISTRIES["helper"])],
            seed_name=PARAM_REGISTRIES["seed_name"][index % len(PARAM_REGISTRIES["seed_name"])],
            plot=PARAM_REGISTRIES["plot"][index % len(PARAM_REGISTRIES["plot"])],
            village=PARAM_REGISTRIES["village"][index % len(PARAM_REGISTRIES["village"])],
        )
        sample = generate(params)
        if not sample.story or params.plot not in sample.story or "{" in sample.story or "}" in sample.story:
            print(f"Generated-story check failed for route {scenario['key']}.")
            return 1
        if not sample.story_qa or not sample.world_qa or sample.world is None:
            print(f"Sample-container check failed for route {scenario['key']}.")
            return 1

    print(f"OK: ASP and Python agree across {len(SCENARIOS)} routes; generated stories passed.")
    return 0


def generate_story(world: World) -> None:
    p = world.params
    validate_params(p)
    seed = p.seed or 0
    scenario = scenario_for(seed)
    opening = OPENINGS[(seed // len(SCENARIOS)) % len(OPENINGS)]
    closing = FOLK_TALE_CLOSINGS[(seed // (len(SCENARIOS) * len(OPENINGS))) % len(FOLK_TALE_CLOSINGS)]
    values = {
        "runner": p.runner,
        "helper": p.helper,
        "seed_name": p.seed_name,
        "plot": p.plot,
        "village": p.village,
    }

    runner = world.add_character(Character(
        name=p.runner,
        role="runner",
        meters={"distance": 0.0, "safe_choices": 0.0},
        memes={"curiosity": 0.8, "worry": 0.4, "confidence": 0.2},
    ))
    fox = world.add_character(Character(
        name=p.helper,
        role="fox helper",
        meters={"route_knowledge": 1.0, "distance": 0.0},
        memes={"trust": 0.4, "patience": 0.7},
    ))
    elder = world.add_character(Character(
        name="Grandmother Rowan",
        role="seed keeper",
        meters={"seed_store": 1.0},
        memes={"hope": 0.8, "care": 1.0},
    ))
    pouch = world.add_object(ObjectThing(
        name="the wool seed pouch",
        kind="seed container",
        meters={"secure": 1.0, "seeds": 1.0},
        memes={"hope": 0.6},
    ))
    plot = world.add_place(Place(
        name=p.plot,
        place_kind="community garden plot",
        meters={"moisture": 0.2, "planted_seeds": 0.0},
        memes={"hope": 0.3},
    ))
    world.add_place(Place(
        name=p.village,
        place_kind="village",
        meters={"neighbors": 1.0},
        memes={"belonging": 1.0},
    ))

    if not python_reasonable_story(scenario):
        raise StoryError("This route has no safe, clue-guided way to carry the seed.")

    world.say(opening.format(**values))
    world.say(
        f"That evening, the village's {p.plot} lay dark and bare after a long dry spell. "
        f"Grandmother Rowan had saved one {p.seed_name} for its waiting soil."
    )
    world.say(
        f"“Carry this to the {p.plot} before dawn,” said Grandmother Rowan. "
        f"“The earth is ready, but it needs a seed.” “I will carry it with care,” replied {p.runner}. "
        f"“My feet can be swift, and my thoughts can be patient.”"
    )
    world.say(
        f"{p.helper}, a red fox who knew the hill paths, trotted beside the runner. "
        f"Grandmother Rowan settled the precious seed pouch into {p.runner}'s hands."
    )
    world.say(f"At the first bend, {scenario['obstacle']} {scenario['clue']}")
    world.say(f"Inside, {p.runner} thought, “{scenario['thought']}”")
    world.say(
        f"“{scenario['fox_line']}” asked {p.helper}. "
        f"“{scenario['runner_line']}” answered {p.runner}."
    )

    route_distance = float(scenario["route_length"])
    runner.add_meter("distance", route_distance)
    fox.add_meter("distance", route_distance)
    runner.add_meter("safe_choices", 1.0)
    runner.add_meme("confidence", 0.7)
    runner.add_meme("patience", 0.6)
    fox.add_meme("trust", 0.5)
    pouch.add_meter("secure", 0.0)
    world.say(str(scenario["action"]))

    if runner.meters["safe_choices"] < 1 or pouch.meters["secure"] < 1:
        raise StoryError("The seed pouch did not stay secure on a safe route.")
    runner.add_meter("distance", 1.0)
    plot.add_meter("planted_seeds", 1.0)
    plot.add_meter("moisture", 0.8)
    plot.add_meme("hope", 0.8)
    elder.add_meter("seed_store", -1.0)
    elder.add_meme("joy", 0.8)
    world.say(
        f"By starlight, the runner and the fox reached the {p.plot}. "
        f"Grandmother Rowan had left a little furrow ready, and {p.runner} tucked the one {p.seed_name} into it."
    )
    world.say(
        f"A gentle rain began, soft as a lullaby. At dawn, a green curl rose from the dark soil; "
        f"{scenario['ending_detail']}."
    )
    world.say(
        f"The villagers gathered around the living green tip, and {p.helper} curled beside the plot "
        f"while {p.runner} smiled. {closing.format(**values)}"
    )

    world.facts = {
        "scenario": str(scenario["title"]),
        "obstacle": str(scenario["obstacle"]),
        "clue": str(scenario["clue"]),
        "thought": str(scenario["thought"]),
        "action": str(scenario["action"]),
        "route": str(scenario["key"]),
        "plot": p.plot,
        "village": p.village,
        "seed_name": p.seed_name,
        "ending_image": f"a green curl rose from the dark soil; {scenario['ending_detail']}.",
    }


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    facts = world.facts
    return [
        QAItem(
            question=f"What trouble did {p.runner} meet on the way to the plot?",
            answer=f"{facts['obstacle']} The challenge could have spoiled the journey, so the runner paused instead of rushing.",
        ),
        QAItem(
            question=f"What clue helped {p.runner} choose a way forward?",
            answer=f"{facts['clue']} {p.runner} used that detail to choose a safer route with {p.helper}.",
        ),
        QAItem(
            question=f"What did {p.runner} think before deciding what to do?",
            answer=f"{p.runner} thought, “{facts['thought']}” That quiet thought helped turn worry into a careful choice.",
        ),
        QAItem(
            question=f"How did {p.runner} and {p.helper} get the seed to the plot?",
            answer=f"{facts['action']} They kept the seed pouch safe and reached the {facts['plot']} together.",
        ),
        QAItem(
            question="What image shows that the journey made a difference?",
            answer=f"At dawn, {facts['ending_image']} The new green curl shows that the seed reached the soil safely.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a runner do?",
            answer="A runner travels on foot to carry a message, a small object, or help from one place to another.",
        ),
        QAItem(
            question="Why can an inner thought help someone make a choice?",
            answer="An inner thought lets someone pause, notice what matters, and choose what to do before acting.",
        ),
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is a story passed from person to person, often with memorable characters, a touch of wonder, and a lesson about how to live.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    facts = world.facts
    return [
        f"Tell a child-facing folk tale about runner {p.runner} carrying a {p.seed_name} to the {p.plot} in {p.village}.",
        f"Include this obstacle and clue: {facts['obstacle']} {facts['clue']}",
        f"Show {p.runner}'s inner monologue guiding a safe choice, include spoken dialogue with {p.helper}, and end with this image: {facts['ending_image']}",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.extend(["", "== (2) Story questions =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== (3) World knowledge =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for character in world.characters.values():
        lines.append(
            f"  {character.name} ({character.role}) "
            f"meters={character.meters} memes={character.memes}"
        )
    for obj in world.objects.values():
        lines.append(f"  {obj.name} ({obj.kind}) meters={obj.meters} memes={obj.memes}")
    for place in world.places.values():
        lines.append(
            f"  {place.name} ({place.place_kind}) "
            f"meters={place.meters} memes={place.memes}"
        )
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
            base_seed = args.seed if args.seed is not None else 0
            params = resolve_params(args, random.Random(base_seed))
            params.seed = base_seed
            scenario = scenario_for(params.seed)
            model = asp.one_model(asp_program(scenario))
        except (ModuleNotFoundError, StoryError) as err:
            print(f"Could not run the ASP story gate: {err}")
            sys.exit(2)
        print("ready" if asp.atoms(model, "ready") else "(no ready route)")
        return

    if args.n < 1 and not args.all:
        print("The number of stories must be at least 1.")
        sys.exit(2)

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    count = len(SCENARIOS) if args.all else args.n
    for index in range(count):
        seed = base_seed + index
        try:
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            samples.append(generate(params))
        except StoryError as err:
            print(err)
            sys.exit(2)

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
