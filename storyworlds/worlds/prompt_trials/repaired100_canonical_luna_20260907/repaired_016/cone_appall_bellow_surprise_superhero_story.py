#!/usr/bin/env python3
"""
A small superhero story world about a surprising cone, a frightening bellow,
and a careful rescue that turns alarm into understanding.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve()
STORYWORLDS_ROOT = next(parent for parent in HERE.parents if (parent / "results.py").is_file())
sys.path.insert(0, str(STORYWORLDS_ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    id: str
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Location:
    name: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str
    helper_name: str
    keeper_name: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Incident:
    place: str
    surprise: str
    danger: str
    clue: str
    hero_action: str
    helper_action: str
    keeper_action: str
    result: str
    lesson: str
    ending: str


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Character] = {}
        self.location = Location("the city discovery fair")
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.dialogue_turns: list[tuple[str, str]] = []

    def add(self, character: Character) -> Character:
        self.entities[character.id] = character
        return character

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


INCIDENTS = [
    Incident(
        place="the thunder-drum tent",
        surprise="a bright orange cone began rolling in circles beneath the biggest drum",
        danger="the drum's loose pedal could swing into the crowd",
        clue="each roll of the cone stopped whenever a low rumble shook the floor",
        hero_action="caught the cone in a soft loop of shining wind",
        helper_action="counted the safe spaces between the drum and the visitors",
        keeper_action="lifted the pedal away and tied it securely to the drum frame",
        result="the drum was quiet, the cone stood upright, and everyone could watch safely",
        lesson="a surprising sound is a reason to look closely, not a reason to panic",
        ending="the orange cone wore a little paper star while the drum tapped a gentle beat",
    ),
    Incident(
        place="the robot parade lane",
        surprise="a yellow cone flashed its light and gave a mighty bellow",
        danger="the startled parade robots were turning toward a barrier",
        clue="the bellow came each time the cone's hidden button touched the lane rope",
        hero_action="held the robots still with a careful ribbon of blue light",
        helper_action="moved the rope away from the button and marked a clear path",
        keeper_action="opened the cone's panel and switched its test horn to a quiet chime",
        result="the robots returned to their path and the cone warned visitors without frightening them",
        lesson="finding the cause of a problem can make a solution kinder",
        ending="the robots marched past the cone as it chimed like a tiny bell",
    ),
    Incident(
        place="the cloud-painting booth",
        surprise="a silver cone released a sudden bellow that made the painted clouds tremble",
        danger="wet paint might spill onto the children gathered around the table",
        clue="the cone shook whenever air rushed through a cracked hose",
        hero_action="raised a calm shield over the paint trays",
        helper_action="closed the nearby air valve and guided children behind the blue line",
        keeper_action="replaced the cracked hose before restarting the booth",
        result="the colors stayed on the paper and the cone made only a soft puff",
        lesson="protecting a creative space begins with noticing what makes it shake",
        ending="a purple cloud floated on a clean sheet beneath the quiet cone",
    ),
    Incident(
        place="the rescue-gear display",
        surprise="a red cone gave a booming bellow when a cape brushed its sensor",
        danger="the noise could appall the youngest visitors and send them running",
        clue="the bellow stopped when the cape was lifted above the sensor",
        hero_action="caught the loose cape before it tangled another child",
        helper_action="showed visitors how to step around the marked sensor line",
        keeper_action="lowered the sensor and changed its warning to a gentle flash",
        result="the display became easy to explore and no one had to flee from the sound",
        lesson="a good warning should keep people safe without making them feel helpless",
        ending="the red cone blinked kindly while a child tried on a rescue cape",
    ),
    Incident(
        place="the moon-bug garden",
        surprise="a green cone let out a deep bellow beside a nest of paper moon bugs",
        danger="the sudden sound could scatter the delicate bug models",
        clue="a loose pebble was trapped beneath the cone's wide base",
        hero_action="lifted the cone without jarring the nest",
        helper_action="held a paper shield around the moon bugs",
        keeper_action="removed the pebble and placed the cone on a level mat",
        result="the moon bugs stayed together and the cone stood quietly on steady ground",
        lesson="a tiny hidden cause can create a very large surprise",
        ending="paper moon bugs glittered beneath the cone as if they were stars under a roof",
    ),
    Incident(
        place="the superhero signal stage",
        surprise="a blue cone began to bellow just as the signal lights went dark",
        danger="the audience could not see the steps beside the stage",
        clue="the cone's power cord was pinched beneath a rolling equipment box",
        hero_action="made a bright trail of light along the steps",
        helper_action="blocked the wheels and moved the box away from the cord",
        keeper_action="repaired the cord and tested every signal before reopening the stage",
        result="the audience saw the steps clearly and the signal shone again",
        lesson="a safe rescue checks both the loud warning and the quiet danger nearby",
        ending="the blue cone pointed at the glowing signal while everyone clapped",
    ),
    Incident(
        place="the giant-kite yard",
        surprise="a striped cone gave a bellow when the giant kite tugged its string",
        danger="the kite string was pulling toward a row of small spectators",
        clue="the cone's base had caught the string and was sliding across the grass",
        hero_action="anchored the cone with a gentle circle of force",
        helper_action="led the spectators behind the fence",
        keeper_action="lowered the kite and freed the string from the cone",
        result="the kite rose again only after the yard was clear and secure",
        lesson="surprise can reveal where a safe boundary is needed",
        ending="the giant kite sailed above the anchored cone like a bright whale",
    ),
    Incident(
        place="the friendly-monster exhibit",
        surprise="a purple cone made a bellow that sounded exactly like a monster",
        danger="the children might appall themselves and crowd the narrow exit",
        clue="the sound matched the exhibit's demonstration button, not a real creature",
        hero_action="stood between the crowd and the narrow exit while keeping everyone calm",
        helper_action="invited the children to take three slow steps backward",
        keeper_action="labeled the button and changed the recording to a friendly roar",
        result="the children learned the sound was pretend and left through the wide doorway",
        lesson="clear information can turn fear into curiosity",
        ending="the purple cone gave a friendly roar, and the children roared back",
    ),
]

OPENINGS = [
    "The city discovery fair was full of bright flags and curious families.",
    "At the afternoon superhero fair, every booth promised a new surprise.",
    "The fairground buzzed with music, questions, and inventions.",
    "Just before the parade began, the young heroes visited the safety displays.",
    "Sunlight warmed the fair while helpers prepared one last demonstration.",
]

DIALOGUES = [
    (
        "Stop at the blue line. Nobody needs to rush.",
        "We can listen first and learn what the cone is telling us.",
        "I found a clue. The bellow changes when something nearby moves.",
    ),
    (
        "That sound startled me, but I will keep everyone safe.",
        "Then I will watch the visitors while you inspect the cone.",
        "The surprise has a cause, and the cause can guide our plan.",
    ),
    (
        "Please step back from the danger and stay where I can see you.",
        "A calm team can solve a loud problem.",
        "I know what to test first. Look at what changes the sound.",
    ),
    (
        "No one crosses the marked line until we understand the warning.",
        "We will protect people and the fair equipment together.",
        "The cone is not the whole mystery; something is touching it.",
    ),
]


ASP_RULES = r"""
#show risk/1.
#show fix/1.
risk(bellow) :- signal(cone), surprise(bellow).
fix(bellow) :- hero_ready, helper_ready, keeper_ready.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("signal", "cone"),
            asp.fact("surprise", "bellow"),
            asp.fact("hero_ready"),
            asp.fact("helper_ready"),
            asp.fact("keeper_ready"),
        ]
    )


def asp_program(show: str = "#show risk/1.\n#show fix/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


HERO_NAMES = ["Luna", "Nova", "Spark", "Comet", "River"]
HELPER_NAMES = ["Milo", "Zara", "Theo", "Pip", "Iris"]
KEEPER_NAMES = ["Nia", "Mara", "June", "Tess", "Ari"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Superhero story world about a surprising cone and bellow.")
    parser.add_argument("--hero-name", choices=HERO_NAMES)
    parser.add_argument("--helper-name", choices=HELPER_NAMES)
    parser.add_argument("--keeper-name", choices=KEEPER_NAMES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero_name or rng.choice(HERO_NAMES)
    helper_choices = [name for name in HELPER_NAMES if name != hero]
    helper = args.helper_name or rng.choice(helper_choices)
    keeper = args.keeper_name or rng.choice(KEEPER_NAMES)
    return StoryParams(hero_name=hero, helper_name=helper, keeper_name=keeper)


def _setup_world(params: StoryParams) -> World:
    world = World()
    hero = world.add(
        Character(
            id="hero",
            name=params.hero_name,
            role="young superhero",
            memes={"bravery": 1.0, "calm": 1.0},
        )
    )
    helper = world.add(
        Character(
            id="helper",
            name=params.helper_name,
            role="helper",
            memes={"attention": 1.0, "kindness": 1.0},
        )
    )
    keeper = world.add(
        Character(
            id="keeper",
            name=params.keeper_name,
            role="fair keeper",
            memes={"care": 1.0, "knowledge": 1.0},
        )
    )
    world.facts.update(hero=hero, helper=helper, keeper=keeper)
    return world


def _dialogue(world: World, speaker: Character, line: str) -> None:
    world.dialogue_turns.append((speaker.name, line))
    world.say(f'{speaker.name} said, "{line}"')


def _variation_key(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum(ord(ch) for ch in f"{params.hero_name}:{params.helper_name}:{params.keeper_name}")


def generate_story(world: World, params: StoryParams) -> None:
    hero: Character = world.facts["hero"]
    helper: Character = world.facts["helper"]
    keeper: Character = world.facts["keeper"]

    key = _variation_key(params)
    incident = INCIDENTS[key % len(INCIDENTS)]
    opening = OPENINGS[(key // len(INCIDENTS)) % len(OPENINGS)]
    warning, hero_line, clue_line = DIALOGUES[(key // 3) % len(DIALOGUES)]

    world.facts.update(
        incident=incident,
        opening=opening,
        warning=warning,
        hero_line=hero_line,
        clue_line=clue_line,
        incident_index=key % len(INCIDENTS),
        resolved=False,
    )
    world.location.meters["crowd_risk"] = 1.0
    world.location.memes["surprise"] = 1.0

    world.say(opening)
    world.say(
        f"At {incident.place}, {hero.name}, a young superhero, was helping {helper.name} "
        f"and Fair Keeper {keeper.name} prepare the next attraction."
    )
    world.say(f"Suddenly, {incident.surprise}. The unexpected bellow made some visitors appalled, and {incident.danger.capitalize()}.")

    world.para()
    _dialogue(world, hero, warning)
    _dialogue(world, helper, hero_line)
    world.say(f"{helper.name} watched instead of guessing. {incident.clue.capitalize()}.")
    _dialogue(world, keeper, clue_line)

    world.para()
    world.say(f"First, {hero.name} {incident.hero_action}.")
    world.say(f"Next, {helper.name} {incident.helper_action}.")
    world.say(f"Then Fair Keeper {keeper.name} {incident.keeper_action}.")
    world.location.meters["crowd_risk"] = 0.0
    world.location.memes["surprise"] = 0.0
    _dialogue(world, hero, "The warning helped us notice the problem. Now the fair is safe again.")
    _dialogue(world, keeper, "And now everyone understands what caused the bellow.")
    world.say(
        f"The team had not ignored the surprise or let it frighten the crowd. Instead, {incident.result}. "
        f"They learned that {incident.lesson}."
    )
    world.say(f"Before the next visitors arrived, {incident.ending}")
    world.facts["resolved"] = True


def story_qa(world: World) -> list[QAItem]:
    hero: Character = world.facts["hero"]
    helper: Character = world.facts["helper"]
    keeper: Character = world.facts["keeper"]
    incident: Incident = world.facts["incident"]
    return [
        QAItem(
            question=f"Who helped at {incident.place}, and what surprising event began the story?",
            answer=f"{hero.name}, {helper.name}, and Fair Keeper {keeper.name} helped there. {incident.surprise.capitalize()}.",
        ),
        QAItem(
            question=f"Why did the bellow create a danger at {incident.place}?",
            answer=f"The bellow was dangerous because {incident.danger}.",
        ),
        QAItem(
            question=f"What clue did {helper.name} notice?",
            answer=f"{helper.name} noticed that {incident.clue}.",
        ),
        QAItem(
            question=f"How did the superhero team solve the problem?",
            answer=(
                f"{hero.name} {incident.hero_action}; {helper.name} {incident.helper_action}; "
                f"and Fair Keeper {keeper.name} {incident.keeper_action}. As a result, {incident.result}."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cone?",
            answer="A cone is a shape or object with a round base that narrows to a point.",
        ),
        QAItem(
            question="Why can a sudden bellow surprise people?",
            answer="A sudden bellow is loud and unexpected, so people may need a moment to understand where it came from.",
        ),
        QAItem(
            question="What should people do when a warning sounds?",
            answer="People should stay calm, move away from danger, and listen for clear instructions.",
        ),
        QAItem(
            question="How can a clue help solve a problem?",
            answer="A clue gives information about what changes, so people can find the cause and choose a safer solution.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    hero: Character = world.facts["hero"]
    helper: Character = world.facts["helper"]
    keeper: Character = world.facts["keeper"]
    incident: Incident = world.facts["incident"]
    return [
        f"Write a child-friendly superhero story about {hero.name}, {helper.name}, and Fair Keeper {keeper.name} "
        f"responding safely when {incident.surprise}.",
        f"Tell a dialogue-rich adventure in which a cone gives a bellow, the clue is that {incident.clue}, "
        "and a surprising danger is solved without panic.",
        f"Create a complete superhero tale that ends with this concrete image: {incident.ending}",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: name={entity.name} role={entity.role} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  location: {world.location.name} meters={world.location.meters} memes={world.location.memes}")
    lines.append(f"  dialogue turns: {len(world.dialogue_turns)}")
    lines.append(f"  resolved: {world.facts.get('resolved')}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if not params.hero_name or not params.helper_name or not params.keeper_name:
        raise StoryError("Every story needs a hero, a helper, and a fair keeper.")
    if params.hero_name == params.helper_name:
        raise StoryError("The hero and helper must have different names.")
    world = _setup_world(params)
    generate_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(hero_name="Luna", helper_name="Milo", keeper_name="Nia"),
    StoryParams(hero_name="Nova", helper_name="Zara", keeper_name="Mara"),
    StoryParams(hero_name="Spark", helper_name="Theo", keeper_name="June"),
    StoryParams(hero_name="Comet", helper_name="Pip", keeper_name="Tess"),
    StoryParams(hero_name="River", helper_name="Iris", keeper_name="Ari"),
]


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    risks = asp.atoms(model, "risk")
    fixes = asp.atoms(model, "fix")
    if ("bellow",) not in risks or ("bellow",) not in fixes:
        print("MISMATCH: ASP did not identify the bellow risk and fix.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("resolved"):
            print("MISMATCH: generated story did not resolve.")
            return 1
        if len(sample.world.dialogue_turns) < 4:
            print("MISMATCH: generated story lacks dialogue.")
            return 1
        if "cone" not in sample.story.lower() or "bellow" not in sample.story.lower():
            print("MISMATCH: generated story lost required seed words.")
            return 1
    print("OK: ASP and Python parity verified; generated stories resolve.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("risk:", asp.atoms(model, "risk"))
        print("fix:", asp.atoms(model, "fix"))
        return

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            index += 1
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
