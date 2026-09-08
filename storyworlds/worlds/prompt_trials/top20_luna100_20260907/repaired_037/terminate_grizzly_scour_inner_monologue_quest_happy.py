#!/usr/bin/env python3
"""
A bright superhero quest about a grizzly bear, a dangerous machine, and the
choice to terminate a problem without hurting anyone.
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

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    indoor: bool = False


@dataclass
class StoryState:
    setting: Setting
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    bear_name: str
    seed: Optional[int] = None
    incident: int = 0
    opening: int = 0
    thought: int = 0
    turn: int = 0
    ending: int = 0


SETTINGS = {
    "mountain_valley": Setting("the mountain valley", {"forest", "stream", "cave"}),
    "city_park": Setting("the city park", {"trail", "pond", "garden"}),
    "snowy_forest": Setting("the snowy forest", {"trail", "cabin", "stream"}),
}

HERO_NAMES = ["Luna", "Mara", "Nova", "Skye", "Ari", "Zara"]
BEAR_NAMES = ["Bruno", "Bramble", "Honey", "Koda", "Maple", "Tundra"]

OPENINGS = [
    "At sunrise, {hero} fastened her silver cape and looked across {place}.",
    "When the town's warning bell rang over {place}, {hero} lifted her shining shield.",
    "A red signal blinked above {place}, and superhero {hero} knew a quest had begun.",
    "The morning was peaceful in {place} until a deep rumble shook the trail.",
    "{hero} was practicing a brave landing beside {place} when a worried roar echoed nearby.",
]

INCIDENTS = [
    {
        "threat": "a runaway logging robot",
        "clue": "its broad wheels were chewing up the meadow while its warning light flashed",
        "urge": "blast the machine into pieces",
        "method": "follow the muddy wheel tracks around the meadow",
        "truth": "the robot was trapped in a loop because a pine branch had jammed its turning arm",
        "repair": "she lifted away the branch and pressed the yellow pause button",
        "lesson": "a hero should stop a danger carefully, not merely smash it",
        "ending": "The meadow grew quiet, and tiny flowers stood safely beside the resting robot.",
    },
    {
        "threat": "a storm-scrubbing drone",
        "clue": "it was sucking leaves, feathers, and loose ribbons into a whirling basket",
        "urge": "chase it into the sky",
        "method": "scour the ground for the drone's control tag",
        "truth": "a gust had carried its control tag beneath a fallen bench",
        "repair": "she found the tag, switched the drone to gentle mode, and guided it home",
        "lesson": "looking closely can solve a loud problem faster than rushing after it",
        "ending": "The drone floated like a sleepy bubble while birds returned to the clean branches.",
    },
    {
        "threat": "a glowing tunnel digger",
        "clue": "it was burrowing toward the bear's winter cave",
        "urge": "block the tunnel with a giant rock",
        "method": "scour the tunnel entrance for a safer path",
        "truth": "the digger's map had mistaken a warm spring for an empty tunnel",
        "repair": "she placed bright markers around the spring and guided the machine toward a harmless hillside",
        "lesson": "a clear map and a kind warning can protect a home",
        "ending": "The spring shimmered beside the cave, while the digger worked safely far away.",
    },
    {
        "threat": "a noisy crystal crusher",
        "clue": "its metal jaws were shaking the stones near the bear's favorite berry patch",
        "urge": "cover its gears with a cape",
        "method": "scour the fence line for the missing safety sign",
        "truth": "the crusher had crossed a marked boundary after a gate blew open",
        "repair": "she closed the gate, replaced the sign, and terminated the crusher's cycle",
        "lesson": "boundaries help strong machines and wild friends share one valley",
        "ending": "The berry patch rested behind its bright sign, ready for a sunny new season.",
    },
]

THOUGHTS = [
    '"I feel my courage buzzing," {hero} thought, "but courage must carry a careful plan."',
    '"A superhero does not need the loudest answer," {hero} told herself. "I need the safest useful one."',
    '"The grizzly is frightened too," {hero} thought. "First I will listen, then I will act."',
    '"If I understand the trouble, I can terminate it without making a new trouble," {hero} decided.',
]

TURNS = [
    '"Please do not roar at it," {hero} said. "Can you show me what changed?" {bear} pointed with one huge paw.',
    '"Stand behind me," said {hero}. "I will scour the trail for a clue." "I can sniff for one," replied {bear}.',
    '"What does the flashing light mean?" asked {hero}. "It means the machine is confused," said {bear}.',
    '"Together?" asked {hero}. The grizzly nodded, and they began the quest side by side.',
]

ENDINGS = [
    '"You saved my home," said {bear}. {hero} smiled. "You helped save it by telling me the truth."',
    '"The quest worked because we used our eyes and our words," said {hero}. The grizzly gave a happy, gentle growl.',
    '"I thought heroes were strongest alone," said {bear}. "The happiest heroes have helpers," replied {hero}.',
    '"The danger is finished," said {hero}. The grizzly hugged her cape, and both friends laughed beneath the bright sky.',
]


ASP_RULES = r"""
#show valid/2.
setting(mountain_valley). setting(city_park). setting(snowy_forest).
affords(mountain_valley,forest). affords(mountain_valley,stream). affords(mountain_valley,cave).
affords(city_park,trail). affords(city_park,pond). affords(city_park,garden).
affords(snowy_forest,trail). affords(snowy_forest,cabin). affords(snowy_forest,stream).
valid(P,A) :- setting(P), affords(P,A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name, setting in SETTINGS.items():
        lines.append(asp.fact("setting", name))
        for affordance in sorted(setting.affords):
            lines.append(asp.fact("affords", name, affordance))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid() -> list[tuple[str, str]]:
    return sorted((place, affordance) for place, setting in SETTINGS.items() for affordance in setting.affords)


def asp_valid() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program()), "valid")))


def asp_verify() -> int:
    expected = set(python_valid())
    actual = set(asp_valid())
    if expected == actual:
        print(f"OK: clingo gate matches python gate ({len(expected)} combinations).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(actual - expected))
    print("only in python:", sorted(expected - actual))
    return 1


def build_world(params: StoryParams) -> StoryState:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    setting = SETTINGS[params.place]
    incident = INCIDENTS[params.incident % len(INCIDENTS)]
    world = StoryState(setting)

    hero = world.add(Entity(
        params.hero_name, "character", "superhero",
        traits=["brave", "thoughtful"],
        meters={"energy": 8.0, "focus": 9.0},
        memes={"hope": 1.0, "responsibility": 1.0},
    ))
    bear = world.add(Entity(
        params.bear_name, "character", "grizzly",
        traits=["large", "worried", "kind"],
        meters={"strength": 10.0, "fear": 6.0},
        memes={"trust": 0.0},
    ))
    threat = world.add(Entity(
        "machine", "thing", "machine",
        label=incident["threat"],
        traits=["loud", "confused"],
        meters={"danger": 7.0, "motion": 8.0},
        memes={"confusion": 1.0},
    ))

    world.say(OPENINGS[params.opening % len(OPENINGS)].format(hero=hero.id, place=setting.place))
    world.say(f"Near the trail, {hero.id} saw {incident['threat']} blocking the way.")
    world.say(f"A grizzly named {bear.id} stood nearby, trembling because {incident['clue']}.")
    world.say(THOUGHTS[params.thought % len(THOUGHTS)].format(hero=hero.id))

    world.para()
    world.say(f'"I want to {incident["urge"]}," {hero.id} said. "But I will understand the danger first."')
    world.say(f'"The machine is near my home," said {bear.id}. "Please help me."')
    world.say(TURNS[params.turn % len(TURNS)].format(hero=hero.id, bear=bear.id))
    world.say(f"Together, they began their quest to {incident['method']}.")
    world.say(f"They discovered that {incident['truth']}.")
    world.say(f"{hero.id} took a slow breath, and her plan became clear: {incident['repair']}.")
    world.say(f"The dangerous motion stopped. The grizzly's fear faded, and his trust grew.")

    world.para()
    world.say(ENDINGS[params.ending % len(ENDINGS)].format(hero=hero.id, bear=bear.id))
    world.say(f"The quest ended happily in {setting.place}.")
    world.say(incident["ending"])

    world.facts.update(
        hero=hero,
        bear=bear,
        threat=threat,
        incident=incident,
        place=setting.place,
        resolved=True,
    )
    return world


def generation_prompts(world: StoryState) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story in {f['place']} where {f['hero'].id} helps a grizzly named {f['bear'].id}.",
        f"Tell a quest story about how {f['hero'].id} terminates a dangerous machine problem through careful investigation.",
        "Write a child-friendly story with inner monologue, spoken dialogue, a brave turn, and a happy ending.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    f = world.facts
    incident = f["incident"]
    hero = f["hero"].id
    bear = f["bear"].id
    return [
        QAItem(
            f"Who was the superhero in the story?",
            f"The superhero was {hero}. {hero} used courage and careful thinking to protect {bear}'s home.",
        ),
        QAItem(
            f"Why was {bear} worried?",
            f"{bear} was worried because {incident['clue']}. The machine's behavior threatened a place that mattered to the grizzly.",
        ),
        QAItem(
            "What did the hero discover during the quest?",
            f"The hero discovered that {incident['truth']}. That clue showed how to solve the problem safely.",
        ),
        QAItem(
            "How did the hero terminate the danger?",
            incident["repair"].capitalize() + ". This stopped the machine without hurting the grizzly or destroying the valley.",
        ),
        QAItem(
            "Why did the quest have a happy ending?",
            f"The quest ended happily because {hero} and {bear} worked together, and {incident['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            "What is a grizzly?",
            "A grizzly is a large brown bear. Grizzlies are wild animals and should be watched from a safe distance.",
        ),
        QAItem(
            "What does terminate mean?",
            "Terminate means to bring something to an end or stop it.",
        ),
        QAItem(
            "What does scour mean?",
            "Scour means to search an area carefully, often looking for a particular clue.",
        ),
        QAItem(
            "What makes a superhero story happy?",
            "A superhero story has a happy ending when courage, kindness, and good choices help protect others and restore peace.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:12} ({entity.type:10}) "
            f"traits={entity.traits} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  setting: {world.setting.place}")
    lines.append(f"  facts: resolved={world.facts.get('resolved')}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    hero_name = args.name or rng.choice(HERO_NAMES)
    bear_name = args.bear or rng.choice(BEAR_NAMES)
    if hero_name == bear_name:
        bear_name = rng.choice([name for name in BEAR_NAMES if name != hero_name])
    return StoryParams(
        place=place,
        hero_name=hero_name,
        bear_name=bear_name,
        incident=rng.randrange(len(INCIDENTS)),
        opening=rng.randrange(len(OPENINGS)),
        thought=rng.randrange(len(THOUGHTS)),
        turn=rng.randrange(len(TURNS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero storyworld about a grizzly, a quest, and a happy ending."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--name")
    parser.add_argument("--bear")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for place, affordance in asp_valid():
            print(f"{place:18} {affordance}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(
                place=place,
                hero_name=f"{place.title()}Hero",
                bear_name=f"{place.title()}Bear",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(1, args.n) and attempt < max(50, args.n * 20):
            rng = random.Random(base_seed + attempt)
            attempt += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
