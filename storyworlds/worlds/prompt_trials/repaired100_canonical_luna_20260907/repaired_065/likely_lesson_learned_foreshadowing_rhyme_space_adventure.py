#!/usr/bin/env python3
"""A child-safe space adventure about noticing clues, helping friends, and learning a lesson."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


HERO_NAMES = ["Luna", "Milo", "Zara", "Finn", "Nova", "Aya", "Theo", "Pip"]
HERO_TYPES = {
    "Luna": "girl", "Zara": "girl", "Nova": "girl", "Aya": "girl",
    "Milo": "boy", "Finn": "boy", "Theo": "boy", "Pip": "boy",
}
COMPANIONS = ["Rex", "Tala", "Orin", "Mira", "Bex", "Sol"]
COMPANION_TYPES = {
    "Tala": "girl", "Mira": "girl", "Bex": "girl",
    "Rex": "boy", "Orin": "boy", "Sol": "boy",
}
PLACES = ["the moon station", "the little starship", "the red planet camp", "the comet observatory"]
CARETAKERS = ["Captain Imani", "Commander Vale", "Dr. Sato", "Auntie Jo"]

OPENINGS = [
    "The little starship hummed beside the moon station while silver dust danced past its windows.",
    "Luna woke to a soft ping from the comet observatory and saw three bright stars trembling outside.",
    "On the red planet camp, the morning sky glowed peach around the children's rover.",
    "The moon station was quiet except for the tick of the oxygen clock and the gentle thrum of the launch pad.",
    "A ribbon of starlight crossed the little starship just as the crew prepared for a short adventure.",
    "Beyond the observatory dome, a blue comet curved like a smile above the sleeping planet.",
]

RHYME_LINES = [
    ("Look for a clue before you fly;", "careful stars can guide the sky."),
    ("When warning lights begin to gleam;", "slow hands protect the space-team dream."),
    ("Ask, then listen, check, and see;", "a wise crew keeps both friends free."),
    ("If a strange sound shakes the floor;", "pause and find what makes it roar."),
    ("Share the map and share the view;", "a helping crew knows what to do."),
    ("Bright or dark, near or far;", "kindness is a guiding star."),
]

DIALOGUE_LINES = [
    ("The panel is blinking. Should we launch?", "Not yet. Let us find out why it blinks."),
    ("I see the blue mark near the hatch.", "Then I will hold the lamp while you read it."),
    ("The map points toward the shadowed moon.", "We can go together and keep the beacon on."),
    ("My scanner says the signal is small.", "Small signals still deserve careful listening."),
    ("I want to press the bright button.", "Please wait until we know what it does."),
]

ENDING_IMAGES = [
    "The repaired beacon painted a warm golden path across the stars.",
    "The rover rolled home beneath a sky full of steady blue lights.",
    "The starship's windows shone like little moons as the crew returned safely.",
    "The comet drifted past, and its tail glittered over the grateful explorers.",
    "The station bell chimed once, softly, while the new map glowed on the wall.",
]

OBSTACLES = [
    {
        "key": "beacon",
        "premise": "They planned to deliver a crystal beacon to a lonely moon.",
        "foreshadow": "Before they left, a tiny amber lamp blinked twice beside the navigation panel.",
        "problem": "Halfway there, the beacon stopped shining and the ship began to drift toward a ring of rocks.",
        "clue": "the amber lamp had been warning them that the beacon's power cord was loose",
        "action": "They turned off the thrusters, clipped the cord firmly into place, and waited for the beacon to shine steadily before steering away.",
        "result": "The navigation path returned, and the ship reached the moon with a bright signal for its waiting rover.",
        "lesson": "A small warning is worth noticing before a big problem grows.",
        "object": "a crystal beacon",
        "risk": "a ring of rocks",
    },
    {
        "key": "moon_map",
        "premise": "They were carrying a map to a hidden moon garden.",
        "foreshadow": "At the launch gate, one corner of the map fluttered even though the cabin was still.",
        "problem": "A burst of cabin air tore the map from its holder and sent it spinning toward the open loading hatch.",
        "clue": "the fluttering corner was caught under a loose silver clip",
        "action": "They sealed the hatch, secured the clip, and used the slow-reel handle to bring the map safely back.",
        "result": "The garden route stayed clear, and the crew found rows of moon flowers waiting under glass.",
        "lesson": "Noticing a little change early can protect something important.",
        "object": "a moon map",
        "risk": "the open loading hatch",
    },
    {
        "key": "signal",
        "premise": "They were searching for a friendly signal from a small comet.",
        "foreshadow": "The radio gave one soft chirp whenever the ship passed the blue window.",
        "problem": "The crew almost followed a noisy false signal into a dark cloud.",
        "clue": "the true signal repeated softly only when the blue window faced the comet",
        "action": "They muted the noisy channel, turned the window toward the comet, and answered the gentle chirp with three careful beeps.",
        "result": "A tiny comet drone appeared and guided them back to the clear route.",
        "lesson": "Careful listening helps us tell a true clue from a distracting sound.",
        "object": "a comet radio",
        "risk": "a dark cloud",
    },
    {
        "key": " rover",
        "premise": "They were taking a small rover to check a bright hill on the red planet.",
        "foreshadow": "A yellow wheel mark appeared on the sand and then vanished beneath a loose stone.",
        "problem": "The rover's front wheel caught under the stone near a steep dusty slope.",
        "clue": "the yellow mark showed that the wheel needed to roll backward, not forward",
        "action": "They stopped the motor, moved the stone with the rover's safe lifter, and guided the wheel backward onto firm ground.",
        "result": "The rover climbed the hill slowly and found a warm patch where space beans could grow.",
        "lesson": "Stopping to read a clue can turn a risky push into a safe plan.",
        "object": "a small rover",
        "risk": "a steep dusty slope",
    },
]


@dataclass
class Entity:
    id: str
    type: str
    label: str
    owner: Optional[str] = None
    holder: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    companion_name: str
    companion_type: str
    caretaker: str
    obstacle_key: str
    opening_index: int = 0
    rhyme_index: int = 0
    dialogue_index: int = 0
    ending_index: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple[str, str]] = set()

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


def get_obstacle(key: str) -> dict[str, str]:
    normalized = key.strip()
    for obstacle in OBSTACLES:
        if obstacle["key"] == normalized:
            return obstacle
    raise StoryError(f"Unknown obstacle: {key}")


def speak(world: World, speaker: Entity, line: str) -> None:
    world.say(f'"{line}" {speaker.label} said.')


def build_world(params: StoryParams) -> World:
    obstacle = get_obstacle(params.obstacle_key)
    world = World(Setting(params.place))
    hero = world.add(Entity("hero", params.hero_type, params.hero_name))
    companion = world.add(Entity("companion", params.companion_type, params.companion_name))
    caretaker = world.add(Entity("caretaker", "caretaker", params.caretaker))
    craft = world.add(Entity("craft", "spacecraft", "the explorer craft"))
    tool = world.add(Entity("mission_object", "mission_object", obstacle["object"], owner="hero"))

    hero.memes.update(curiosity=1.0, courage=1.0, caution=1.0, kindness=1.0)
    companion.memes.update(curiosity=1.0, courage=1.0, caution=1.0, kindness=1.0)
    caretaker.memes.update(guidance=1.0, trust=1.0)
    craft.meters.update(fuel=1.0, control=1.0, safe_route=0.0)
    tool.meters.update(importance=1.0, secure=0.0)

    opening = OPENINGS[params.opening_index % len(OPENINGS)]
    rhyme = RHYME_LINES[params.rhyme_index % len(RHYME_LINES)]
    dialogue = DIALOGUE_LINES[params.dialogue_index % len(DIALOGUE_LINES)]
    ending = ENDING_IMAGES[params.ending_index % len(ENDING_IMAGES)]

    world.say(opening)
    world.say(
        f"{params.hero_name} and {params.companion_name} were young space explorers at {params.place}. "
        f"They were ready to carry {obstacle['object']} across the stars. {obstacle['premise']}"
    )
    world.say(obstacle["foreshadow"])
    world.say(
        f"It seemed like a tiny detail, but it was foreshadowing: a clue about what might happen next."
    )
    world.para()

    speak(world, companion, dialogue[0])
    speak(world, hero, dialogue[1])
    world.say(obstacle["problem"])
    world.say(f"The crew faced {obstacle['risk']}, so rushing would have been dangerous.")
    world.para()

    world.say(
        f"{params.hero_name} wanted to act quickly, but {params.companion_name} remembered the earlier clue. "
        f"Together they discovered that {obstacle['clue']}."
    )
    speak(world, caretaker, "A careful crew checks a warning before choosing its next move.")
    world.say(f'The explorers repeated a rhyme: "{rhyme[0]} {rhyme[1]}"')
    world.para()

    world.say(obstacle["action"])
    world.say(obstacle["result"])
    world.say(
        f"{params.hero_name} smiled because the lesson learned was clear: {obstacle['lesson']}"
    )
    world.say(f"{ending}")

    craft.meters["safe_route"] = 1.0
    tool.meters["secure"] = 1.0
    hero.memes["confidence"] = 1.0
    companion.memes["confidence"] = 1.0
    world.fired.update({
        ("foreshadowing", obstacle["key"]),
        ("danger", obstacle["key"]),
        ("clue_found", obstacle["key"]),
        ("lesson_learned", obstacle["key"]),
        ("resolution", obstacle["key"]),
    })
    world.facts.update(
        hero=hero,
        companion=companion,
        caretaker=caretaker,
        craft=craft,
        tool=tool,
        obstacle=obstacle,
        rhyme=rhyme,
        dialogue=dialogue,
        ending=ending,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    obstacle: dict[str, str] = world.facts["obstacle"]  # type: ignore[assignment]
    return [
        f"Write a gentle space adventure about {params.hero_name} and {params.companion_name} at {params.place}.",
        f"Use foreshadowing when {obstacle['foreshadow'].lower()} Then let a careful clue solve the danger.",
        f"Include a dialogue exchange, a rhyme, and a lesson learned about this mission.",
    ]


def story_questions(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    obstacle: dict[str, str] = world.facts["obstacle"]  # type: ignore[assignment]
    rhyme: tuple[str, str] = world.facts["rhyme"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What mission were {params.hero_name} and {params.companion_name} doing?",
            answer=f"They were carrying {obstacle['object']} across space from {params.place}.",
        ),
        QAItem(
            question="What foreshadowing appeared before the trouble?",
            answer=f"{obstacle['foreshadow']} This early detail foreshadowed the later danger.",
        ),
        QAItem(
            question="What danger did the explorers face?",
            answer=f"{obstacle['problem']} The danger involved {obstacle['risk']}.",
        ),
        QAItem(
            question="What clue helped them make a safe choice?",
            answer=f"They discovered that {obstacle['clue']}.",
        ),
        QAItem(
            question="What rhyme did the crew use?",
            answer=f'They said, "{rhyme[0]} {rhyme[1]}"',
        ),
        QAItem(
            question="What lesson was learned at the end?",
            answer=f"They learned that {obstacle['lesson']}",
        ),
    ]


def world_knowledge_questions(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is an early clue that hints at something important that may happen later.",
        ),
        QAItem(
            question="Why should a space crew notice warning lights?",
            answer="A warning light can reveal a problem early, allowing the crew to pause and choose a safer action.",
        ),
        QAItem(
            question="What makes a helpful teammate?",
            answer="A helpful teammate listens, shares information, and works calmly with others.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type} label={entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A mission has a hero, a companion, and a mission object.
mission(H,C,O) :- hero(H), companion(C), object(O).

% Foreshadowing gives a clue before danger.
foreshadowing(H,C,O) :- mission(H,C,O), clue(O).

% A clue can reveal a danger.
danger(H,C,O) :- foreshadowing(H,C,O), risk(O).

% Careful action resolves the danger.
safe_resolution(H,C,O) :- danger(H,C,O), careful(H), careful(C).
"""


def asp_facts(world: Optional[World] = None) -> str:
    import asp

    obstacle_key = "beacon"
    if world is not None:
        obstacle = world.facts.get("obstacle")
        if isinstance(obstacle, dict):
            obstacle_key = str(obstacle["key"])
    return "\n".join([
        asp.fact("hero", "hero"),
        asp.fact("companion", "companion"),
        asp.fact("object", obstacle_key),
        asp.fact("clue", obstacle_key),
        asp.fact("risk", obstacle_key),
        asp.fact("careful", "hero"),
        asp.fact("careful", "companion"),
    ])


def asp_program(world: Optional[World] = None, show: str = "#show safe_resolution/3.") -> str:
    return f"{asp_facts(world)}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A child-safe space adventure about noticing clues.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--name", choices=HERO_NAMES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--caretaker", choices=CARETAKERS)
    parser.add_argument("--obstacle", choices=[item["key"] for item in OBSTACLES])
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.name or rng.choice(HERO_NAMES)
    companion = args.companion or rng.choice([name for name in COMPANIONS if name != hero])
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        hero_name=hero,
        hero_type=HERO_TYPES[hero],
        companion_name=companion,
        companion_type=COMPANION_TYPES[companion],
        caretaker=args.caretaker or rng.choice(CARETAKERS),
        obstacle_key=args.obstacle or rng.choice([item["key"] for item in OBSTACLES]),
        opening_index=rng.randrange(len(OPENINGS)),
        rhyme_index=rng.randrange(len(RHYME_LINES)),
        dialogue_index=rng.randrange(len(DIALOGUE_LINES)),
        ending_index=rng.randrange(len(ENDING_IMAGES)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_questions(world),
        world_qa=world_knowledge_questions(world),
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


def asp_verify() -> int:
    import asp

    for obstacle in OBSTACLES:
        params = StoryParams(
            place=PLACES[0],
            hero_name="Luna",
            hero_type="girl",
            companion_name="Rex",
            companion_type="boy",
            caretaker=CARETAKERS[0],
            obstacle_key=obstacle["key"],
        )
        world = build_world(params)
        if "lesson_learned" not in {name for name, _ in world.fired}:
            raise StoryError("Python story did not record its lesson learned.")
        model = asp.one_model(asp_program(world))
        if not asp.atoms(model, "safe_resolution"):
            raise StoryError(f"ASP model did not find a safe resolution for {obstacle['key']}.")
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            raise StoryError("Generated verification story was incomplete.")
        if "likely" not in generation_prompts(world)[1].lower() and obstacle["key"] == "beacon":
            pass
    return 0


CURATED = [
    StoryParams(
        place="the moon station",
        hero_name="Luna",
        hero_type="girl",
        companion_name="Rex",
        companion_type="boy",
        caretaker="Captain Imani",
        obstacle_key="beacon",
        rhyme_index=0,
    ),
    StoryParams(
        place="the red planet camp",
        hero_name="Milo",
        hero_type="boy",
        companion_name="Tala",
        companion_type="girl",
        caretaker="Dr. Sato",
        obstacle_key="rover",
        opening_index=2,
        rhyme_index=3,
        dialogue_index=2,
        ending_index=1,
    ),
    StoryParams(
        place="the comet observatory",
        hero_name="Nova",
        hero_type="girl",
        companion_name="Sol",
        companion_type="boy",
        caretaker="Commander Vale",
        obstacle_key="signal",
        opening_index=1,
        rhyme_index=5,
        dialogue_index=3,
        ending_index=3,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show foreshadowing/3.\n#show danger/3.\n#show safe_resolution/3."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program(show="#show foreshadowing/3.\n#show danger/3.\n#show safe_resolution/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(max(0, args.n)):
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
        if len(samples) > 1:
            print(f"### variant {index + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
