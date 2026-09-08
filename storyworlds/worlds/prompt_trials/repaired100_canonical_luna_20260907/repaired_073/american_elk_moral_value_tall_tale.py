#!/usr/bin/env python3
"""
A small tall-tale storyworld about an American elk, a boastful plan, and the
moral value of honest teamwork.
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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


SETTINGS = {
    "mountain_valley": {
        "place": "a high American mountain valley",
        "detail": "The valley was so wide that morning sunlight needed nearly an hour to reach the far wall.",
        "affords": {"travel", "gathering"},
    },
}

NAMES = ["Luna", "Milo", "Tess", "Ari", "June", "Cal", "Nora", "Beau"]
NAME_GENDERS = {
    "Luna": "girl",
    "Milo": "boy",
    "Tess": "girl",
    "Ari": "boy",
    "June": "girl",
    "Cal": "boy",
    "Nora": "girl",
    "Beau": "boy",
}
TRAITS = ["bold", "curious", "patient", "cheerful", "clever", "hopeful"]
GUIDES = ["Grandma Rose", "Uncle Sam", "Aunt Bea", "Grandpa Tom"]

EPISODES = [
    {
        "id": "cloud_bridge",
        "arrival": "An American elk herd needed to cross a roaring stream before snow covered the lower trail.",
        "problem": "The old log bridge had washed away, and the smallest elk could not leap the rushing water.",
        "boast": "Luna announced that one enormous jump would solve everything, though her knees immediately disagreed.",
        "clue": "The elk noticed flat stones rising in a line beneath the water.",
        "plan": "The herd worked in turns: strong elk pushed fallen branches aside, smaller elk carried willow ties, and the guide tested each stone.",
        "exchange": (
            '"I can leap the whole stream!" Luna cried.',
            '"A bridge made by many feet is stronger than one boast," said the guide.'
        ),
        "result": "Together they built a short branch bridge and crossed safely, one careful hoof at a time.",
        "lesson": "true courage means helping others instead of pretending to be able to do everything alone",
        "ending": "By sunset, the new crossing trembled beneath dozens of hooves, but it held like a promise.",
        "object": "a branch bridge",
    },
    {
        "id": "moonlit_bell",
        "arrival": "An American elk calf wandered toward a moonlit meadow where a ranch bell had gone silent.",
        "problem": "The herd could not tell which trail led back to the safe pine grove.",
        "boast": "Milo claimed he could hear the grove from a mile away, but he followed his own echo toward a thorn bush.",
        "clue": "The oldest elk heard a faint bell whenever the wind moved through one narrow pass.",
        "plan": "The herd stood quietly, sharing what each animal heard, while two adults checked the ground for familiar hoofprints.",
        "exchange": (
            '"My ears are the finest in the whole valley!" Milo said.',
            '"Then use them to listen to everyone," answered the oldest elk.'
        ),
        "result": "Their shared observations led the herd along the safe pass and back to the pine grove.",
        "lesson": "wisdom grows when a proud voice makes room for quieter voices",
        "ending": "The bell rang once behind them, and every elk answered with a gentle rustle of antlers.",
        "object": "a ranch bell",
    },
    {
        "id": "giant_snowball",
        "arrival": "A spring storm dropped a snowball on the American elk trail.",
        "problem": "The snowball was so large that it blocked the valley road and trapped a supply wagon.",
        "boast": "Tess promised to roll it away with one mighty shove, then slid backward three body lengths.",
        "clue": "Warm sunlight had hollowed a tunnel beneath the snowball.",
        "plan": "The elk widened the tunnel with their antlers while the wagon crew placed sturdy poles beneath the lower edge.",
        "exchange": (
            '"Stand aside! I have the strength of ten storms!" Tess shouted.',
            '"Then lend us one storm-sized push after we make it safe," said the wagon driver.'
        ),
        "result": "The careful plan freed the wagon without sending the snowball tumbling down the slope.",
        "lesson": "strength is most valuable when it follows patience and a safe plan",
        "ending": "The snowball rolled into a sunny hollow, where it became a pond large enough to reflect every antler.",
        "object": "a supply wagon",
    },
    {
        "id": "rainbow_fence",
        "arrival": "An American elk herd reached a meadow enclosed by a fence bright with rainbows.",
        "problem": "A young calf had slipped through a gap and could not find the opening again.",
        "boast": "Ari said he could memorize every rainbow stripe, but he mixed red with sunset and blue with a puddle.",
        "clue": "The fence posts were marked with tiny hoof-shaped scratches near the safe gap.",
        "plan": "The herd followed the scratches together, keeping the calf between two calm adults.",
        "exchange": (
            '"I know every color!" Ari declared.',
            '"Good," said the guide. "Now notice the marks made by feet."'
        ),
        "result": "The calf returned through the real opening, and the herd left the fence undisturbed.",
        "lesson": "careful evidence is better than a confident guess",
        "ending": "The rainbow fence shone behind them, while the calf wore a stripe of grass on its nose.",
        "object": "a meadow fence",
    },
    {
        "id": "thunder_horn",
        "arrival": "A summer storm rolled across the American range with thunder loud enough to wake stones.",
        "problem": "A young elk mistook a hollow tree's booming sound for a dangerous animal.",
        "boast": "June declared that she would challenge the thunder creature herself.",
        "clue": "Each boom arrived after lightning flashed beside the hollow tree.",
        "plan": "The herd counted the flashes and booms together while the adults guided the young elk toward open ground.",
        "exchange": (
            '"I will chase the thunder beast away!" June cried.',
            '"First let us learn whether it has feet," said her mother.'
        ),
        "result": "The herd discovered the sound was an echoing tree and waited safely until the storm passed.",
        "lesson": "bravery includes asking questions before rushing toward danger",
        "ending": "When the sky cleared, the hollow tree made one tiny creak, as if apologizing for its enormous voice.",
        "object": "a hollow tree",
    },
    {
        "id": "golden_grass",
        "arrival": "A dry summer left the American elk meadow with only one patch of golden grass.",
        "problem": "Every elk wanted the patch first, and their hoofprints began to tear it apart.",
        "boast": "Cal said he could guard the whole meadow alone by standing in the middle of it.",
        "clue": "The grass grew beside a spring that could refill several small pools.",
        "plan": "The herd shared the water, took turns grazing, and marked a quiet resting place away from the grass.",
        "exchange": (
            '"I will be the meadow boss!" Cal announced.',
            '"A meadow has no boss," replied the herd leader. "It has neighbors."'
        ),
        "result": "The grass survived because the elk used the spring and rested in turns.",
        "lesson": "fair sharing protects a gift better than claiming it for yourself",
        "ending": "Weeks later, the golden patch waved like a little sun beneath the enormous mountain.",
        "object": "a patch of golden grass",
    },
]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        return "\n\n".join(" ".join(paragraph) for paragraph in self.paragraphs if paragraph)


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    guide: str
    trait: str
    seed: Optional[int] = None
    episode: int = 0
    route: int = 0
    exaggeration: int = 0
    cadence: int = 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A tall tale about an American elk and the moral value of honest teamwork."
    )
    parser.add_argument("--place", choices=SETTINGS.keys())
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--guide", choices=GUIDES)
    parser.add_argument("--trait", choices=TRAITS)
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
    name = args.name or rng.choice(NAMES)
    return StoryParams(
        place=args.place or "mountain_valley",
        name=name,
        gender=args.gender or NAME_GENDERS[name],
        guide=args.guide or rng.choice(GUIDES),
        trait=args.trait or rng.choice(TRAITS),
        seed=None,
        episode=rng.randrange(len(EPISODES)),
        route=rng.randrange(4),
        exaggeration=rng.randrange(5),
        cadence=rng.randrange(8),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("Unknown setting for this storyworld.")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("The elk protagonist must be identified as a girl or boy.")
    if not 0 <= params.episode < len(EPISODES):
        raise StoryError("The selected elk episode does not exist.")


def _build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    setting = SETTINGS[params.place]
    episode = EPISODES[params.episode]
    world = World(place=setting["place"])

    elk = world.add(Entity(
        id="Elk",
        kind="character",
        type="elk",
        label=params.name,
        phrase=f"young American elk named {params.name}",
        meters={"courage": 1.0, "pride": 0.9},
        memes={"honesty": 0.4, "cooperation": 0.4},
    ))
    guide = world.add(Entity(
        id="Guide",
        kind="character",
        type="guide",
        label=params.guide,
        phrase=f"the wise elk guide {params.guide}",
        meters={"patience": 1.0, "judgment": 1.0},
        memes={"trust": 1.0},
    ))
    herd = world.add(Entity(
        id="Herd",
        kind="group",
        type="elk_herd",
        label="the American elk herd",
        phrase="the American elk herd",
        meters={"strength": 1.0, "safety": 0.2},
        memes={"community": 0.5},
    ))
    obstacle = world.add(Entity(
        id="Obstacle",
        kind="thing",
        type="obstacle",
        label=episode["object"],
        phrase=episode["object"],
        meters={"blocking": 1.0},
    ))

    openings = [
        f"Long ago in {world.place}, {params.name}, a {params.trait} young American elk, believed that every problem had one enormous answer.",
        f"On a morning so bright it polished the peaks, {params.name}, a {params.trait} American elk, trotted through {world.place}.",
        f"In the days when elk tracks were mistaken for roads, {params.name}, a {params.trait} young elk, followed the herd across {world.place}.",
        f"Once, beneath mountains tall enough to tickle the moon, {params.name}, a {params.trait} American elk, found trouble on the trail.",
    ]
    exaggerations = [
        "The mountains leaned closer because they enjoy a good tall tale.",
        "Even the clouds stopped drifting so they could hear what happened next.",
        "A nearby pine tree counted the hoofbeats and gave up at three hundred.",
        "The echo repeated the boast until it became embarrassed.",
        "The sun rose twice, just to see whether the story was true.",
    ]
    route_lines = [
        "First, the herd stared at the trouble.",
        "At first, everyone offered a different idea.",
        "For one long moment, the trail seemed to hold its breath.",
        "The problem looked larger whenever someone looked at it alone.",
    ]
    ending_notes = [
        "From then on, the herd measured greatness by the help an elk gave, not by the size of a boast.",
        "That day, even the smallest calf understood that a shared plan can carry a very large hope.",
        "The valley remembered the lesson long after the hoofprints faded.",
        "And that is how an ordinary herd made an extraordinary difference.",
    ]

    world.say(openings[params.route])
    world.say(setting["detail"])
    world.say(exaggerations[params.exaggeration])
    world.say(episode["arrival"])
    world.say(episode["problem"])
    world.para()

    world.say(episode["boast"])
    world.say(f"{params.guide} watched {params.name} carefully and did not laugh.")
    world.say(route_lines[params.cadence % len(route_lines)])
    world.say(
        f'{episode["exchange"][0]} {episode["exchange"][1]}'
    )
    world.say(
        f"{params.name} lowered their head. For the first time, the young elk admitted that being brave did not mean being the only one with an answer."
    )
    world.para()

    world.say(f"Then the herd noticed that {episode['clue'][0].lower() + episode['clue'][1:]}")
    world.say(episode["plan"])
    world.say(
        f"The work was so well shared that even the valley's biggest echo had to admit that {params.name} was no longer pretending."
    )
    world.say(
        f"{episode['result']} The danger eased because the elk listened, checked, and helped one another."
    )
    world.para()

    world.say(
        f"{params.name} said, 'I thought a tall tale needed one giant hero. Now I know it can have a whole herd.'"
    )
    world.say(
        f"{params.guide} answered, 'That is the moral value of honesty: when we tell the truth about what we need, others can help us make it right.'"
    )
    world.say(f"{params.name} learned that {episode['lesson']}.")
    world.say(episode["ending"])
    world.say(ending_notes[params.cadence % len(ending_notes)])

    elk.meters["pride"] = 0.2
    elk.memes["honesty"] = 1.0
    elk.memes["cooperation"] = 1.0
    herd.meters["safety"] = 1.0
    herd.memes["community"] = 1.0
    obstacle.meters["blocking"] = 0.0

    world.facts.update(
        elk=elk,
        guide=guide,
        herd=herd,
        obstacle=obstacle,
        params=params,
        episode=episode,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    episode = world.facts["episode"]
    return [
        f"Write a child-friendly American tall tale about {params.name}, a {params.trait} elk, facing {episode['object']}.",
        "Tell a funny tall tale in which an American elk learns a moral value through honest teamwork and dialogue.",
        f"Write a complete story about an elk who learns that {episode['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    episode = world.facts["episode"]
    return [
        QAItem(
            question="Who is the main character?",
            answer=f"The main character is {params.name}, a {params.trait} young American elk.",
        ),
        QAItem(
            question="What problem did the elk herd face?",
            answer=episode["problem"],
        ),
        QAItem(
            question="What clue helped the herd make a better plan?",
            answer=episode["clue"],
        ),
        QAItem(
            question="How did the herd solve the problem?",
            answer=f"{episode['plan']} {episode['result']}",
        ),
        QAItem(
            question="What moral value did the elk learn?",
            answer=f"The elk learned that {episode['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an American elk?",
            answer="An American elk is a large North American deer with long legs and antlers on adult males.",
        ),
        QAItem(
            question="What is a herd?",
            answer="A herd is a group of animals that travel, rest, or find food together.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a belief about a good way to act, such as being honest, kind, brave, or fair.",
        ),
        QAItem(
            question="What is a tall tale?",
            answer="A tall tale is a humorous story that begins with something possible and then stretches it with wild exaggeration.",
        ),
        QAItem(
            question="Why can teamwork help?",
            answer="Teamwork can help because people or animals share observations, effort, and responsibility.",
        ),
    ]


ASP_RULES = r"""
#show compatible/1.
compatible(story) :- american_elk, moral_value, tall_tale, honest_dialogue, herd_solution.
"""


def asp_facts() -> str:
    return "\n".join([
        "american_elk.",
        "moral_value.",
        "tall_tale.",
        "honest_dialogue.",
        "herd_solution.",
    ])


def asp_program(show: str = "#show compatible/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        from storyworlds import asp
        models = asp.solve(asp_program(), models=1)
        atoms = asp.atoms(models[0], "compatible") if models else []
        if ("story",) not in atoms:
            return 1
    except Exception:
        return 1

    for params in CURATED:
        sample = generate(params)
        if not sample.story or "American elk" not in sample.story:
            return 1
        if not sample.story_qa:
            return 1
    return 0


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:9} ({entity.type:10}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="mountain_valley",
        name="Luna",
        gender="girl",
        guide="Grandma Rose",
        trait="bold",
        episode=0,
        route=0,
        exaggeration=1,
        cadence=2,
    ),
    StoryParams(
        place="mountain_valley",
        name="Milo",
        gender="boy",
        guide="Uncle Sam",
        trait="clever",
        episode=1,
        route=1,
        exaggeration=3,
        cadence=5,
    ),
    StoryParams(
        place="mountain_valley",
        name="Tess",
        gender="girl",
        guide="Aunt Bea",
        trait="hopeful",
        episode=5,
        route=2,
        exaggeration=4,
        cadence=1,
    ),
]


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
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
            from storyworlds import asp
            models = asp.solve(asp_program(), models=1)
            for atom in asp.atoms(models[0], "compatible") if models else []:
                print(f"compatible({atom[0]})")
        except Exception as exc:
            raise SystemExit(f"ASP mode unavailable: {exc}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        for index in range(args.n):
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
        header = ""
        if args.all:
            header = f"### {sample.params.name}: American elk tall tale"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
