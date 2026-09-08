#!/usr/bin/env python3
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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class City:
    name: str
    danger: float = 0.0
    trust: float = 0.0
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str
    partner_name: str
    city_name: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Nova", "Jade", "Kai", "Pip", "Rhea", "Sol"]
CITY_NAMES = ["Brighton", "Starfall City", "Moonbridge", "Beacon Bay"]


ARCS = [
    {
        "key": "smoke_alarm",
        "premise": [
            "{hero} watched over {city} from a rooftop while {partner} carried a warm bacon sandwich up the stairs. The two heroes had promised to keep the night peaceful.",
            "At sunset, superhero {hero} and helper {partner} patrolled {city}. A little bacon cart below sent a delicious smell through the cool air.",
        ],
        "problem": [
            "A smoke monster rose from the bacon cart and covered the streets in gray clouds. The city lights vanished, and frightened people could not find their way home.",
            "The cart's alarm began shouting so loudly that everyone thought the city was on fire. Smoke curled around the towers while the streets filled with confusion.",
        ],
        "conflict": [
            "\"I will blast the smoke away,\" said {hero}. \"Wait,\" replied {partner}. \"Your wind power could spread it farther.\" Their argument kept both heroes from acting.",
            "{hero} pointed at the monster. \"We must chase it!\" {partner} answered, \"We must first remove the alarm's power.\" Neither hero moved while the smoke thickened.",
        ],
        "turn": [
            "Then {partner} noticed a twist: the smoke monster was not attacking. It was hiding a tiny robot that had accidentally turned the bacon cart's alarm too high.",
            "A bacon crumb landed on the alarm button, and the sound stopped for one breath. The twist became clear: the monster followed the noisy button instead of creating the smoke itself.",
        ],
        "action": [
            "\"You were right to look closely,\" {hero} said. Together they removed the bacon cart's loose battery, then guided the tiny robot out of the smoke.",
            "{hero} lowered the wind and {partner} reached the alarm safely. They removed the stuck button cover, and the smoke began to thin.",
        ],
        "resolution": [
            "The smoke monster shrank into a harmless puff. {hero} apologized for rushing, and {partner} forgave the mistake. Their reconciliation brought the city's lights back.",
            "Fresh air returned to the streets. The heroes shared the bacon sandwich with the tiny robot and agreed that listening was part of being brave.",
        ],
        "ending": [
            "Below them, every window in {city} glowed again, and the bacon cart's quiet bell rang once.",
            "The last gray puff curled into a heart above the rooftop while {hero} and {partner} watched the safe streets.",
        ],
        "problem_fact": "a smoke monster and a blaring bacon-cart alarm confused the city",
        "clue_fact": "the twist revealed that a tiny robot had caused the alarm",
        "action_fact": "the heroes removed the stuck alarm battery and helped the robot",
        "outcome_fact": "the smoke cleared and the heroes reconciled",
    },
    {
        "key": "runaway_signal",
        "premise": [
            "Superhero {hero} met {partner} beside a bacon breakfast truck in {city}. They were planning a quiet patrol before the morning crowds arrived.",
            "{hero} and {partner} stood beneath the shining tower of {city}. {partner} offered {hero} a strip of crispy bacon before they flew off to help people.",
        ],
        "problem": [
            "A bright rescue signal shot into the sky and pulled every hero toward the same empty alley. The signal kept repeating, while real trouble began elsewhere.",
            "The city's emergency beacon spun wildly, sending heroes in circles. Each time {hero} reached the beacon, it pointed back to the same alley.",
        ],
        "conflict": [
            "\"The signal must be trusted,\" said {hero}. {partner} shook their head. \"The people calling for help matter more than a blinking light.\" Their disagreement delayed the rescue.",
            "{hero} wanted to follow the beacon. {partner} wanted to remove its glowing cover and inspect it. Their sharp words made the bacon grow cold.",
        ],
        "turn": [
            "The twist appeared when a pigeon landed on the beacon. Its wing brushed a hidden switch, and the signal changed toward a real playground emergency.",
            "A bacon wrapper fluttered beneath the beacon and revealed a second wire. The heroes discovered the signal was not a villain's trap but a loose wire sending an old message.",
        ],
        "action": [
            "{hero} admitted the beacon could be wrong. {partner} carefully removed the loose wire while {hero} followed the new signal to the playground.",
            "\"Let us check before we chase,\" said {partner}. {hero} nodded, removed the glowing cover, and found the safe switch beneath it.",
        ],
        "resolution": [
            "The beacon stopped repeating, and the heroes rescued the children from a stuck playground lift. Their reconciliation began with a grateful high five.",
            "The false signal faded. {hero} thanked {partner} for questioning it, and together they repaired the beacon so future calls would be clear.",
        ],
        "ending": [
            "The repaired beacon shone a steady blue above {city}, while the breakfast truck served warm bacon to the rescuers.",
            "Children waved from the playground as the beacon sent one honest beam across the morning sky.",
        ],
        "problem_fact": "a repeating rescue beacon sent heroes to the wrong alley",
        "clue_fact": "a hidden wire revealed the beacon's message was faulty",
        "action_fact": "the heroes removed the loose wire and followed the true rescue call",
        "outcome_fact": "the children were rescued and the heroes reconciled",
    },
    {
        "key": "mirror_cape",
        "premise": [
            "At noon, {hero} and {partner} shared a bacon roll on the tallest roof in {city}. Their bright capes fluttered as they watched over the neighborhoods.",
            "{hero} polished a silver rooftop sign while {partner} delivered bacon to the watch station. The superheroes of {city} were ready for any call.",
        ],
        "problem": [
            "A mirror villain copied {hero}'s powers and made the city believe the two heroes were fighting. Every reflection showed a different battle.",
            "The rooftops filled with shining copies of the heroes. The mirror villain twisted their movements until friends could not tell truth from trickery.",
        ],
        "conflict": [
            "{hero} blamed {partner} for trusting the false reflection. {partner} answered, \"You never asked what I saw.\" Their hurt words made the mirror copies stronger.",
            "\"Stay behind me,\" ordered {hero}. \"No, we must stand together,\" said {partner}. Their disagreement gave the villain more time to scatter reflections.",
        ],
        "turn": [
            "Then came the twist: the villain could copy powers but not kindness. {partner} offered a piece of bacon to a frightened reflection, and only the real hero accepted it.",
            "A warm bacon smell crossed the roof. The heroes realized the mirrors copied faces and powers, but not the little sounds of real friendship.",
        ],
        "action": [
            "{hero} apologized for blaming {partner}. They stood side by side, removed the shiny sign that fed the reflections, and offered the villain a way to stop.",
            "{partner} called out a private joke, and the real {hero} laughed. Together they removed the sign's crystal core and ended the mirror trick.",
        ],
        "resolution": [
            "The false images vanished. The mirror villain lowered their hands, and the heroes chose reconciliation instead of revenge.",
            "The city saw one true pair of heroes again. {hero} and {partner} repaired their trust while the villain agreed to return the stolen crystal.",
        ],
        "ending": [
            "The quiet rooftop reflected two real capes and one shared bacon roll beneath the afternoon sun.",
            "Every window showed the same peaceful sky, and the heroes' shadows stood together on the roof.",
        ],
        "problem_fact": "a mirror villain copied the heroes and confused the city",
        "clue_fact": "the twist showed that kindness could not be copied",
        "action_fact": "the heroes removed the crystal that powered the false reflections",
        "outcome_fact": "the copies vanished and the heroes reconciled",
    },
]


class World:
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]

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


def _rng_for(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    raw = "|".join((params.hero_name, params.partner_name, params.city_name))
    seed = int.from_bytes(hashlib.sha256(raw.encode()).digest()[:8], "big")
    return random.Random(seed)


def tell(params: StoryParams) -> World:
    if params.hero_name == params.partner_name:
        raise StoryError("hero and partner must have different names")
    if params.city_name not in CITY_NAMES:
        raise StoryError(f"unknown city: {params.city_name}")

    rng = _rng_for(params)
    index = (params.seed if params.seed is not None else rng.randrange(len(ARCS))) % len(ARCS)
    arc = ARCS[index]
    beats = ("premise", "problem", "conflict", "turn", "action", "resolution", "ending")
    if params.seed is None:
        selected = {b: rng.choice(arc[b]) for b in beats}
    else:
        code = (params.seed // len(ARCS)) % (2 ** len(beats))
        selected = {b: arc[b][(code >> i) % len(arc[b])] for i, b in enumerate(beats)}

    city = City(params.city_name, danger=1.0, trust=0.2)
    world = World(city)
    hero = world.add(Entity(params.hero_name, kind="character", type="superhero"))
    partner = world.add(Entity(params.partner_name, kind="character", type="hero_partner"))
    bacon = world.add(Entity("bacon", type="food", label="bacon"))

    hero.meters.update({"energy": 5.0, "courage": 4.0})
    partner.meters.update({"energy": 4.0, "care": 5.0})
    hero.memes["trust"] = 0.2
    partner.memes["trust"] = 0.2
    bacon.meters["warm"] = 1.0

    values = {
        "hero": params.hero_name,
        "partner": params.partner_name,
        "city": params.city_name,
    }
    rendered = {b: selected[b].format(**values) for b in beats}
    for i, beat in enumerate(beats):
        if i:
            world.para()
        world.say(rendered[beat])

    city.danger = 0.0
    city.trust = 1.0
    hero.meters["energy"] = 3.0
    partner.meters["energy"] = 3.0
    hero.memes["trust"] = 1.0
    partner.memes["trust"] = 1.0
    bacon.meters["shared"] = 1.0
    city.facts = {
        "hero": hero,
        "partner": partner,
        "bacon": bacon,
        "arc": arc["key"],
        "problem": arc["problem_fact"],
        "clue": arc["clue_fact"],
        "action": arc["action_fact"],
        "outcome": arc["outcome_fact"],
        "events": rendered,
    }
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.city.facts
    return [
        "Write a child-friendly superhero story that includes bacon and a problem someone must remove.",
        f"Tell a superhero story about {f['hero'].id} and {f['partner'].id} discovering a twist and finding reconciliation.",
        "Write an adventure where listening changes how heroes save a city.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.city.facts
    hero = f["hero"].id
    partner = f["partner"].id
    return [
        QAItem(
            question=f"Who protected {world.city.name}?",
            answer=f"{hero} and {partner} protected {world.city.name} together.",
        ),
        QAItem(
            question="What caused the trouble?",
            answer=f["events"]["problem"],
        ),
        QAItem(
            question="What was the twist?",
            answer=f["events"]["turn"],
        ),
        QAItem(
            question="How did the heroes reach reconciliation?",
            answer=f"{f['events']['action']} {f['events']['resolution']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a brave character who uses special abilities and good choices to help others.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means repairing a relationship after people have disagreed and choosing to trust one another again.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change in what the characters or readers thought was happening.",
        ),
        QAItem(
            question="Why might someone remove something?",
            answer="Someone might remove an object or problem to make a place safer, clearer, or easier to use.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id:10} ({entity.type:14}) meters={meters} memes={memes}")
    lines.append(f"  city.danger={world.city.danger}")
    lines.append(f"  city.trust={world.city.trust}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story :-
    theme(bacon),
    action(remove),
    feature(twist),
    feature(reconciliation),
    style(superhero_story).
#show valid_story/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("theme", "bacon"),
            asp.fact("action", "remove"),
            asp.fact("feature", "twist"),
            asp.fact("feature", "reconciliation"),
            asp.fact("style", "superhero_story"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    if any(sym.name == "valid_story" for sym in model):
        params = StoryParams("Luna", "Milo", "Moonbridge", seed=17)
        sample = generate(params)
        if all(word in sample.story.lower() for word in ("bacon", "remove")):
            print("OK: ASP and Python story checks agree.")
            return 0
    print("MISMATCH: ASP or generated-story check failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Superhero story world with bacon, removal, twists, and reconciliation.")
    parser.add_argument("--hero-name", choices=NAMES)
    parser.add_argument("--partner-name", choices=NAMES)
    parser.add_argument("--city-name", choices=CITY_NAMES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero_name or rng.choice(NAMES)
    possible = [name for name in NAMES if name != hero]
    partner = args.partner_name or rng.choice(possible)
    city = args.city_name or rng.choice(CITY_NAMES)
    return StoryParams(hero, partner, city)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        raise SystemExit(asp_verify())
    if args.asp:
        print("1 compatible superhero story pattern: bacon + remove + twist + reconciliation")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "Milo", "Moonbridge", seed=3),
            StoryParams("Nova", "Jade", "Beacon Bay", seed=11),
            StoryParams("Kai", "Rhea", "Starfall City", seed=19),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
        header = f"### variant {index + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
