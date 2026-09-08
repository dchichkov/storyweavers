#!/usr/bin/env python3
"""A child-facing superhero quest about a grizzly, a vanished signal, and courage."""

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
class Creature:
    name: str
    species: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class Quest:
    title: str
    hazard: str
    solved: bool = False


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Luna"
    hero_species: str = "fox"
    grizzly_name: str = "Bruno"
    place_name: str = "Moonlight Valley"
    quest: str = "beacon"
    route: str = "signal_first"


@dataclass(frozen=True)
class QuestCase:
    missing: str
    risk: str
    first_action: str
    failed_reason: str
    clue: str
    cause: str
    brave_action: str
    repair: str
    lesson: str
    ending: str


@dataclass
class World:
    valley: Place
    hero: Creature
    grizzly: Creature
    quest: Quest
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "Moonlight Valley": Place("Moonlight Valley", "mountain valley"),
    "Silver Pine Park": Place("Silver Pine Park", "forest park"),
    "Starfall Harbor": Place("Starfall Harbor", "quiet harbor"),
}

HEROES = [
    ("Luna", "fox"),
    ("Mira", "rabbit"),
    ("Kai", "raccoon"),
    ("Nova", "wolf"),
]

GRIZZLIES = ["Bruno", "Moss", "Honey"]

CASES = {
    "beacon": QuestCase(
        "the valley beacon had gone dark",
        "travelers might lose the safe trail home",
        "turned the beacon switch off and on",
        "the switch clicked, but the lamp stayed dark",
        "silver dust glittered beneath the beacon's cracked glass",
        "a tiny meteor pebble had fallen onto the solar panel and blocked its light",
        "climbed only to the marked safe platform while Bruno held the safety rope",
        "removed the pebble with a long wooden pole, cleaned the panel, and tested the beacon",
        "a hero uses courage with a plan instead of rushing toward danger",
        "the beacon painted a bright path across the valley while Luna and Bruno cheered",
    ),
    "bridge": QuestCase(
        "the rainbow bridge hummed loudly",
        "the bridge might fail when families crossed it",
        "placed a wooden block beneath the nearest rail",
        "the hum continued because the rail was not carrying the sound",
        "a loose metal sign swung against a post in the wind",
        "the sign was making the bridge sound shaky even though its supports were firm",
        "kept everyone behind the yellow line while Bruno checked the support beams",
        "tightened the sign, inspected every beam, and opened the bridge after a safe test",
        "a superhero protects others by checking facts before making a dramatic move",
        "children crossed the quiet bridge beneath a rainbow of morning light",
    ),
    "storm": QuestCase(
        "the storm warning bell would not stop ringing",
        "the village might panic and miss an important shelter message",
        "counted the bell rings beside the control box",
        "the count changed whenever the wind turned, so the box was not the whole problem",
        "a red kite string curled around the bell's clapper",
        "a kite caught in the tower was tugging the bell whenever the breeze shifted",
        "asked Bruno to watch the tower while Luna stayed on the ground and followed the rope line",
        "lowered the kite with a rescue hook and tested the bell during three calm breaths",
        "help is part of heroic strength, especially when the high place is unsafe",
        "the bell rang once for all clear, and the rescued kite danced beside the shelter",
    ),
    "garden": QuestCase(
        "the community garden's water pump had stopped",
        "the young plants could wilt before sunset",
        "filled the pump cup and listened for the first gurgle",
        "the cup drained normally, so the pump was not sealed shut",
        "a blue ribbon was caught beneath the handle",
        "a celebration ribbon had slipped into the pump joint and stopped its motion",
        "read the warning tag aloud and waited for Bruno before opening the mechanism",
        "removed the ribbon, rinsed the joint, and watered each garden row",
        "pausing to understand a problem can protect the very people a hero wants to save",
        "fresh water sparkled between green leaves as the neighbors shared the harvest",
    ),
}

QUESTS = [
    ("beacon", "a dark valley beacon"),
    ("bridge", "a humming rainbow bridge"),
    ("storm", "a ringing storm bell"),
    ("garden", "a silent garden pump"),
]

ROUTES = ("signal_first", "dialogue_first", "thought_first", "map_first", "danger_first")

ASP_RULES = r"""
hero(luna).
grizzly(bruno).
quest(Q) :- beacon_quest(Q).
beacon_quest(beacon).
safe_plan :- hero(luna), grizzly(bruno).
solved(beacon) :- safe_plan.
valid_story :- solved(beacon), safe_plan.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero", "hero"),
        asp.fact("grizzly", "grizzly"),
        asp.fact("safe_plan"),
    ]
    for key, _ in QUESTS:
        lines.append(asp.fact("quest", key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/1."))
    found = set(asp.atoms(model, "solved"))
    expected = {("beacon",)}
    if found == expected:
        print("OK: clingo gate matches python reasoning.")
        return 0
    print("MISMATCH between clingo and python reasoning.")
    print("clingo:", sorted(found))
    print("python:", sorted(expected))
    return 1


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(
        str(value)
        for value in (
            params.seed,
            params.hero_name,
            params.hero_species,
            params.grizzly_name,
            params.place_name,
            params.quest,
            params.route,
        )
    )
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def build_world(params: StoryParams) -> World:
    if params.place_name not in PLACES:
        raise StoryError(f"Unknown place: {params.place_name}")
    if params.quest not in CASES:
        raise StoryError(f"Unknown quest: {params.quest}")
    template = PLACES[params.place_name]
    clue = dict(QUESTS)[params.quest]
    return World(
        valley=Place(template.name, template.kind),
        hero=Creature(params.hero_name, params.hero_species, "young superhero"),
        grizzly=Creature(params.grizzly_name, "grizzly bear", "helpful guardian"),
        quest=Quest(clue, CASES[params.quest].risk),
    )


def tell_story(world: World, params: StoryParams) -> None:
    rng = story_rng(params)
    hero, grizzly, valley, quest = world.hero, world.grizzly, world.valley, world.quest
    case = CASES[params.quest]

    hero.memes.update(courage=0, curiosity=1)
    grizzly.memes.update(patience=1, kindness=1)

    openings = {
        "signal_first": (
            f"The {quest.title} waited in {valley.name}, where {quest.hazard}. "
            f"{hero.name} the {hero.species} superhero hurried to investigate."
        ),
        "dialogue_first": (
            f'"A hero listens before leaping," {grizzly.name} said in {valley.name}. '
            f'Then they saw that {quest.hazard}.'
        ),
        "thought_first": (
            f"{hero.name} felt a brave thought flutter inside: helping mattered more than looking fearless. "
            f"In {valley.name}, {quest.hazard}."
        ),
        "map_first": (
            f"With a map spread on a flat stone, {hero.name} traced the safe paths through {valley.name}. "
            f"The map marked one urgent quest: {quest.hazard}."
        ),
        "danger_first": (
            f"People stopped at the edge of {valley.name} when they learned that {quest.hazard}. "
            f"{hero.name} arrived with a cape, a notebook, and a careful plan."
        ),
    }
    world.say(openings[params.route])
    world.say(f"It mattered because {case.risk}.")
    world.say(
        rng.choice(
            [
                f'"I want to help," {hero.name} said. "Tell me what you notice."',
                f'"Do not terminate the quest with a guess," {grizzly.name} advised. "We will scour the scene safely."',
                f'{hero.name} whispered, "I am nervous, but I can still choose the next careful step."',
            ]
        )
    )
    world.para()
    world.say(f"First, {hero.name} {case.first_action}.")
    world.say(f"The idea did not solve the problem because {case.failed_reason}.")
    world.say(f"Then {grizzly.name} pointed from behind the safety line. {case.clue.capitalize()}.")
    world.say(f"That clue showed the real cause: {case.cause}.")
    world.say(
        f'"Now I know what to do," {hero.name} said. {grizzly.name} answered, '
        f'"Knowing the danger helps us make a safe rescue."'
    )
    world.para()
    world.say(f"{hero.name} {case.brave_action}.")
    world.say(f"Together, the superhero and the grizzly {case.repair}.")
    hero.memes["courage"] = 1
    hero.meters["safe_steps"] = 3
    grizzly.meters["helpful_checks"] = 2
    quest.solved = True
    world.say(rng.choice(
        [
            f"The lesson was clear: {case.lesson}.",
            f"{hero.name} wrote in the quest book, \"{case.lesson.capitalize()}.\"",
            f'"That was heroic," said {grizzly.name}. "You used courage carefully."',
        ]
    ))
    world.say(f"At last, {case.ending}")
    world.facts.update(
        hero=hero,
        grizzly=grizzly,
        valley=valley,
        quest=quest,
        case=case,
        cause=case.cause,
        repair=case.repair,
        lesson=case.lesson,
        ending=case.ending,
    )


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    return [
        f"Write a superhero story about {world.hero.name}, a {world.hero.species}, and {world.grizzly.name}, a grizzly, helping in {world.valley.name}.",
        f"Show an inner monologue in which {world.hero.name} feels nervous but chooses a safe heroic action because {case.risk}.",
        f"Tell a quest story where the heroes scour the scene, discover that {case.cause}, and reach a happy ending: {case.ending}",
    ]


def story_qa(world: World) -> list[QAItem]:
    case = world.facts["case"]
    hero, grizzly, valley, quest = world.hero, world.grizzly, world.valley, world.quest
    return [
        QAItem(
            question=f"What quest did {hero.name} and {grizzly.name} undertake in {valley.name}?",
            answer=f"They undertook a quest to solve why {quest.hazard}. It mattered because {case.risk}.",
        ),
        QAItem(
            question=f"Why did {hero.name}'s first action fail?",
            answer=f"{hero.name} {case.first_action}, but that failed because {case.failed_reason}.",
        ),
        QAItem(
            question="What clue revealed the real cause?",
            answer=f"They noticed that {case.clue}. This showed that {case.cause}.",
        ),
        QAItem(
            question=f"How did {hero.name} show courage?",
            answer=f"{hero.name} {case.brave_action}. The choice was brave because it followed a safe plan.",
        ),
        QAItem(
            question="How did the quest end happily?",
            answer=f"Together, the heroes {case.repair}. Then {case.ending}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is someone who uses special abilities, courage, and wise choices to help others.",
        ),
        QAItem(
            question="What does scour mean in this story?",
            answer="Here, scour means to search an area carefully for useful clues.",
        ),
        QAItem(
            question="What does terminate mean?",
            answer="Terminate means to bring something to an end, such as ending a dangerous plan or finishing a quest.",
        ),
        QAItem(
            question="Why is an inner monologue useful?",
            answer="An inner monologue lets readers hear a character's private thoughts and understand how the character makes a decision.",
        ),
        QAItem(
            question="Why did the grizzly help the superhero?",
            answer="The grizzly helped by noticing evidence, guarding the safe boundary, and sharing patient advice.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero quest with Luna, a grizzly, and a happy ending."
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--hero-name")
    parser.add_argument("--grizzly-name")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--quest", choices=sorted(CASES))
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_name, hero_species = rng.choice(HEROES)
    grizzly_name = rng.choice(GRIZZLIES)
    place_name = args.place or rng.choice(sorted(PLACES))
    quest = args.quest or rng.choice(sorted(CASES))
    return StoryParams(
        seed=args.seed,
        hero_name=args.hero_name or hero_name,
        hero_species=hero_species,
        grizzly_name=args.grizzly_name or grizzly_name,
        place_name=place_name,
        quest=quest,
        route=rng.choice(ROUTES),
    )


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world trace ---",
            f"{world.valley.name}: meters={world.valley.meters}",
            f"{world.hero.name}: meters={world.hero.meters} memes={world.hero.memes}",
            f"{world.grizzly.name}: meters={world.grizzly.meters} memes={world.grizzly.memes}",
            f"quest: title={world.quest.title!r} hazard={world.quest.hazard!r} solved={world.quest.solved}",
        ]
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solved/1."))
        print(sorted(set(asp.atoms(model, "solved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 3 if args.all else args.n
    samples: list[StorySample] = []
    for index in range(count):
        params = resolve_params(args, random.Random(base_seed + index))
        params.seed = base_seed + index
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
