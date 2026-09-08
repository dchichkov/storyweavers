#!/usr/bin/env python3
"""
A child-friendly mystery storyworld about a tempting con, careful evidence,
and foreshadowing that helps friends dissuade a neighbor from a risky deal.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_repo_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_repo_root))
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class MysteryPlace:
    name: str
    kind: str = "place"
    safe: bool = True


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    neighbor_name: str
    seed: Optional[int] = None


@dataclass
class World:
    place: MysteryPlace
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "lantern_lane": MysteryPlace("Lantern Lane"),
    "old_station": MysteryPlace("the Old Station"),
    "rainy_market": MysteryPlace("the Rainy Market"),
}

NAMES = ["Luna", "Milo", "Nia", "Theo", "Suri", "Pip", "Ada", "Jasper"]

CASES = [
    {
        "key": "silver_ticket",
        "premise": "a stranger arrived with a silver ticket that promised a treasure map",
        "offer": "one shiny coin today would unlock a chest tomorrow",
        "clue": "the ticket's moon stamp was printed upside down",
        "foreshadow": "earlier that morning, Luna had noticed the same crooked moon mark on a torn scrap near the rubbish bin",
        "truth": "the ticket was copied from an old poster and led nowhere",
        "action": "placed the ticket beside the old poster and compared the marks",
        "repair": "persuaded the neighbor to keep the coin and report the false offer to the station keeper",
        "ending": "the copied silver ticket rested behind the keeper's desk while the real map stayed safely locked away",
    },
    {
        "key": "whistling_key",
        "premise": "a peddler offered a brass key said to open a hidden room",
        "offer": "a small payment would buy a secret shortcut to a room full of jewels",
        "clue": "the key had fresh blue paint on its teeth",
        "foreshadow": "a blue paint fleck had appeared on the neighbor's doorstep before the peddler ever arrived",
        "truth": "the key was made to look old but had been painted that same day",
        "action": "followed the blue flecks and found a matching paint tin behind the market stall",
        "repair": "dissuaded the neighbor by showing the matching paint and asking the market keeper to intervene",
        "ending": "the false key became a harmless bell charm above the market door",
    },
    {
        "key": "vanishing_parcel",
        "premise": "a sealed parcel appeared with a note promising a rare clock inside",
        "offer": "a quick fee would release the parcel before another buyer claimed it",
        "clue": "the parcel was tied with string that still carried fresh flour dust",
        "foreshadow": "Luna had seen the same floury string around empty boxes behind the bakery",
        "truth": "the parcel held a brick wrapped in paper, not a clock",
        "action": "asked the baker to compare the string and opened the parcel with a trusted adult",
        "repair": "dissuaded the neighbor from paying and helped return the empty boxes to the bakery",
        "ending": "the pretend parcel sat open beside a real ticking clock that everyone could inspect",
    },
    {
        "key": "golden_feather",
        "premise": "a visitor claimed a golden feather could make wishes come true",
        "offer": "a coin would buy the feather before its supposed magic faded",
        "clue": "gold dust stopped exactly at the edge of the feather's paper backing",
        "foreshadow": "a glittering trail had led from the alley to the visitor's bag at breakfast",
        "truth": "the feather was an ordinary paper feather painted gold",
        "action": "held the feather under a lantern and checked the glitter trail without touching the bag",
        "repair": "dissuaded the neighbor and invited the visitor to explain the trick to the town watch",
        "ending": "the paper feather hung in the mystery club as a reminder to check claims",
    },
    {
        "key": "midnight_bell",
        "premise": "a stranger promised a midnight bell that would reveal hidden wishes",
        "offer": "a payment would reserve the bell before the moon rose",
        "clue": "the reservation card used ink that smudged whenever it touched rain",
        "foreshadow": "a wet black thumbprint had appeared on three other blank cards near the fountain",
        "truth": "the cards were made to look official but had no keeper's seal",
        "action": "showed the cards to the station keeper and compared them with a real reservation",
        "repair": "dissuaded the neighbor from paying and returned the false cards to the keeper",
        "ending": "the true station bell rang at noon, with its honest brass seal shining in daylight",
    },
]

OPENINGS = [
    "On a misty afternoon",
    "Just before the evening lanterns were lit",
    "While rain tapped the market roof",
    "At the quiet edge of the Old Station",
]

DIALOGUE_CONCERNS = [
    "This sounds exciting, but what proof do we have?",
    "Please wait. A promise is not the same as evidence.",
    "I want to understand the offer before you pay.",
    "Could we check one small detail first?",
]

DIALOGUE_REPLIES = [
    "You are right. I was listening to the promise instead of checking the clue.",
    "I nearly paid because I wanted the mystery to be real.",
    "Show me what you found, and I will look carefully.",
    "Let us ask someone trustworthy before we decide.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A mystery storyworld about spotting a con.")
    parser.add_argument("--setting", choices=PLACES.keys())
    parser.add_argument("--name")
    parser.add_argument("--neighbor")
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
    setting = args.setting or rng.choice(list(PLACES))
    hero = args.name or rng.choice(NAMES)
    choices = [name for name in NAMES if name != hero]
    neighbor = args.neighbor or rng.choice(choices)
    return StoryParams(setting=setting, hero_name=hero, neighbor_name=neighbor)


def tell(params: StoryParams) -> World:
    if params.setting not in PLACES:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.hero_name == params.neighbor_name:
        raise StoryError("The hero and neighbor must have different names.")

    rng = random.Random(params.seed if params.seed is not None else 0)
    place_template = PLACES[params.setting]
    place = MysteryPlace(place_template.name, safe=place_template.safe)
    world = World(place)

    hero = world.add(Entity(params.hero_name, "character", "child detective", params.hero_name))
    neighbor = world.add(Entity(params.neighbor_name, "character", "neighbor", params.neighbor_name))
    stranger = world.add(Entity("visitor", "character", "peddler", "the visitor"))

    case = rng.choice(CASES)
    concern = rng.choice(DIALOGUE_CONCERNS)
    reply = rng.choice(DIALOGUE_REPLIES)

    hero.meters.update(attention=1.0, courage=1.0)
    hero.memes.update(curiosity=1.0, care=1.0)
    neighbor.meters.update(trust=1.0, caution=0.0)
    neighbor.memes.update(hope=1.0, temptation=1.0)
    stranger.meters.update(deception=1.0)
    stranger.memes.update(greed=1.0)

    world.say(
        f"{OPENINGS[rng.randrange(len(OPENINGS))]}, {hero.label} was watching the shadows around "
        f"{world.place.name}. {neighbor.label} hurried over, carrying a worried smile."
    )
    world.say(f"That was when {case['premise']}. The visitor said that {case['offer']}.")
    world.para()

    world.say(
        f"{neighbor.label} reached for a coin. {hero.label} gently raised a hand and said, "
        f"“{concern}”"
    )
    world.say(
        f"“{reply}” {neighbor.label} answered. The visitor frowned and urged them to hurry."
    )
    world.say(
        f"Then {hero.label} remembered an earlier sign: {case['foreshadow']}."
    )
    world.say(
        f"Now a second clue appeared: {case['clue']}. The two clues pointed toward the same answer."
    )
    world.para()

    world.say(
        f"{hero.label} did not call anyone a thief without checking. Instead, {hero.label} "
        f"{case['action']}. The test showed that {case['truth']}."
    )
    world.say(
        f"“A con can sound like a wish,” said {hero.label}, “but a careful question can keep us safe.”"
    )
    world.say(
        f"{neighbor.label} nodded. Together they {case['repair']}."
    )
    world.para()

    hero.meters["attention"] = 2.0
    hero.memes["courage"] = 2.0
    neighbor.meters["caution"] = 2.0
    neighbor.memes["temptation"] = 0.0
    neighbor.memes["trust"] = 2.0
    stranger.meters["deception"] = 0.0
    world.say(
        f"The mystery was solved without a chase because the foreshadowing had taught them to "
        f"notice small details. {neighbor.label} decided to pause before trusting a grand promise."
    )
    world.say(f"At last, {case['ending']}.")

    world.facts.update(
        hero=hero,
        neighbor=neighbor,
        stranger=stranger,
        case=case,
        concern=concern,
        reply=reply,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    return [
        f"Write a child-friendly mystery in which a character must dissuade a neighbor from a con involving {case['premise']}.",
        f"Use foreshadowing: {case['foreshadow']}",
        "Show dialogue changing a decision, followed by a concrete clue and a safe resolution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    case = facts["case"]
    hero = facts["hero"]
    neighbor = facts["neighbor"]
    return [
        QAItem(
            f"What con was offered to {neighbor.label}?",
            f"The visitor claimed that {case['offer']}. It was a tempting promise designed to make {neighbor.label} pay quickly.",
        ),
        QAItem(
            f"How did {hero.label} dissuade {neighbor.label}?",
            f"{hero.label} asked {neighbor.label} to slow down, remembered the foreshadowing, and checked the clue that {case['clue']}.",
        ),
        QAItem(
            "What did the investigation reveal?",
            f"It revealed that {case['truth']}. The offer was not trustworthy.",
        ),
        QAItem(
            "Why was the earlier detail important?",
            f"The earlier detail was that {case['foreshadow']}. It foreshadowed the later clue and helped the friends recognize the con.",
        ),
        QAItem(
            "How did the story end?",
            f"The friends stayed safe and {case['repair']}. The ending image was that {case['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a con?",
            "A con is a dishonest trick used to make someone give away money, belongings, or trust.",
        ),
        QAItem(
            "What does dissuade mean?",
            "To dissuade someone means to gently persuade them not to do something risky or unwise.",
        ),
        QAItem(
            "What is foreshadowing?",
            "Foreshadowing is an earlier clue or detail that hints at something important later in a story.",
        ),
        QAItem(
            "What should someone do when an offer feels too good to be true?",
            "They should pause, ask questions, check evidence, and speak with a trusted adult before paying or sharing private information.",
        ),
    ]


ASP_RULES = r"""
feature(foreshadowing).
feature(dialogue).
feature(mystery).
safe_choice(check_evidence).
safe_choice(delay_payment).
con_kind(dishonest_offer).
story_rule(small_clue_supports_later_discovery).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("feature", "foreshadowing"),
            asp.fact("feature", "dialogue"),
            asp.fact("feature", "mystery"),
            asp.fact("safe_choice", "check_evidence"),
            asp.fact("safe_choice", "delay_payment"),
            asp.fact("con_kind", "dishonest_offer"),
        ]
    )


def asp_program(show: str = "#show feature/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show feature/1."))
    features = set(asp.atoms(model, "feature"))
    expected = {("foreshadowing",), ("dialogue",), ("mystery",)}
    if features != expected:
        print(f"Mismatch in ASP features: expected {expected}, got {features}")
        return 1

    rng = random.Random(91)
    for _ in range(5):
        params = resolve_params(build_parser().parse_args([]), rng)
        params.seed = rng.randrange(100000)
        sample = generate(params)
        if not sample.story or "con" not in sample.story.lower():
            print("Generated story verification failed.")
            return 1
    print("OK: ASP/Python parity and generated stories verified.")
    return 0


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---", f"place: {world.place.name}"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.label}: meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
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

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show feature/1."))
        print(sorted(set(asp.atoms(model, "feature"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, case in enumerate(CASES):
            params = StoryParams(
                setting=list(PLACES)[index % len(PLACES)],
                hero_name="Luna",
                neighbor_name="Milo",
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 20)
        while len(samples) < args.n and index < limit:
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
            if sample.story in seen:
                continue
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
