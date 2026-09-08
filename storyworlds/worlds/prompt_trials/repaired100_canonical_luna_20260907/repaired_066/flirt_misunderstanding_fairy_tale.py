#!/usr/bin/env python3
"""
A standalone fairy-tale storyworld about a harmless flirt misunderstood as a spell.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)


@dataclass
class CastleWorld:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    royal_name: str
    messenger_name: str
    setting: str = "the moonlit castle garden"
    scenario_id: int = 0
    opening_id: int = 0
    dialogue_id: int = 0
    turn_id: int = 0
    ending_id: int = 0
    seed: Optional[int] = None


HERO_NAMES = ["Luna", "Mira", "Elian", "Tessa", "Rowan", "Nia"]
ROYAL_NAMES = ["Prince Alder", "Princess Celeste", "Prince Rowan", "Princess Marigold"]
MESSENGERS = ["the silver fox", "the little page", "the blue jay"]

SCENARIOS = [
    {
        "signal": "the royal starlight ribbons fluttered toward the tower",
        "guess": "the stranger was casting a charm to steal the prince's heart",
        "clue": "the ribbons were tied into a welcome sign, not a spell",
        "truth": "I was trying to flirt with the prince by sending him a pretty greeting",
        "action": "read the ribbon knots and found that each one formed a friendly compliment",
        "resolution": "the prince answered with a ribbon of his own and invited the stranger to speak plainly",
        "image": "two bright ribbons curled together above the garden gate",
        "lesson": "a playful signal can be misunderstood when people do not ask what it means",
    },
    {
        "signal": "a rosy bird kept dropping flower petals on the prince's balcony",
        "guess": "the bird carried a love spell meant to make the prince obey",
        "clue": "each petal formed a heart beside a tiny written greeting",
        "truth": "I was flirting with the prince, but I was too shy to knock on the door",
        "action": "gathered the petals and read the greeting aloud",
        "resolution": "the prince laughed kindly and replied that a direct hello would be clearer",
        "image": "a heart-shaped petal rested beside an open balcony door",
        "lesson": "clear words help a sweet joke become a respectful invitation",
    },
    {
        "signal": "the castle fountain sang whenever a masked traveler passed",
        "guess": "the traveler had enchanted the water to lure the royal family away",
        "clue": "the song repeated the traveler's cheerful compliment about the fountain",
        "truth": "I flirted with the fountain keeper because I admired her music",
        "action": "asked the traveler to explain the song instead of blaming the mask",
        "resolution": "the keeper accepted the compliment and asked the traveler to remove the mask before talking",
        "image": "the fountain sparkled while the mask hung safely from a rosebush",
        "lesson": "curiosity and honest conversation can untangle a frightening guess",
    },
    {
        "signal": "golden footprints appeared around the throne room before breakfast",
        "guess": "a suitor had sneaked in to claim the kingdom",
        "clue": "the footprints ended at a note praising the queen's dancing shoes",
        "truth": "I was flirting with the queen's wonderful sense of rhythm, not plotting a takeover",
        "action": "followed the footprints to the note and showed it to the queen",
        "resolution": "the queen invited the suitor to a morning dance where everyone could meet openly",
        "image": "golden footprints made a neat circle around the breakfast hall",
        "lesson": "a bold gesture needs a truthful explanation before others can understand it",
    },
    {
        "signal": "a shy dragon breathed heart-shaped clouds above the village",
        "guess": "the dragon was preparing a fiery attack on the castle",
        "clue": "the clouds carried compliments about the baker's warm bread",
        "truth": "I was flirting with the baker and did not know how to say hello",
        "action": "asked the dragon to land beside the bakery and use words",
        "resolution": "the baker thanked the dragon and offered bread after hearing the honest greeting",
        "image": "a warm loaf cooled beneath one pink cloud shaped like a heart",
        "lesson": "kind listening can turn a confusing display into a friendly beginning",
    },
]

OPENINGS = [
    "Once, beneath a silver moon, {hero} lived near {setting}, where {signal}.",
    "In a kingdom of bells and roses, {hero} noticed something strange: {signal}.",
    "At dawn, {hero} looked toward {setting} and saw that {signal}.",
    "The fairy-tale morning began with a puzzle, for {signal}.",
    "While the castle slept, {hero} discovered that {signal}.",
]

DIALOGUES = [
    '"Do not turn a mystery into a monster before asking a question," said {messenger}.',
    '"Let us listen before we accuse," said {messenger}.',
    '"A smile can mean many things," said {messenger}. "We should ask which one this means."',
    '"The truth may be gentler than the guess," said {messenger}.',
]

TURNS = [
    "“Tell us what you meant,” {hero} said.",
    "“Please explain the greeting,” {hero} asked.",
    "“Were you trying to frighten anyone?” {hero} asked.",
    "“Say it in ordinary words,” {hero} invited.",
]

ENDINGS = [
    "By sunset, {resolution}. Then {image}.",
    "At last, {resolution}. In the quiet evening, {image}.",
    "The misunderstanding melted away when {resolution}. Above them, {image}.",
    "Everyone smiled because {resolution}. The final sight was this: {image}.",
]


def valid_combo(params: StoryParams) -> bool:
    if not params.hero_name.strip():
        raise StoryError("hero name cannot be empty")
    if not params.royal_name.strip():
        raise StoryError("royal name cannot be empty")
    if not params.messenger_name.strip():
        raise StoryError("messenger name cannot be empty")
    if not params.setting.strip():
        raise StoryError("setting cannot be empty")
    if params.hero_name == params.royal_name:
        raise StoryError("hero and royal must be different characters")
    return True


def tell(params: StoryParams) -> CastleWorld:
    valid_combo(params)
    scene = SCENARIOS[params.scenario_id % len(SCENARIOS)]
    world = CastleWorld()
    hero = world.add(Entity(
        params.hero_name, "traveler", params.hero_name,
        meters={"courage": 1.0, "clarity": 0.2},
        memes={"worry": 0.7, "kindness": 0.6},
    ))
    royal = world.add(Entity(
        "royal", "royal", params.royal_name,
        meters={"trust": 0.3},
        memes={"curiosity": 0.8, "relief": 0.0},
    ))
    messenger = world.add(Entity(
        "messenger", "helper", params.messenger_name,
        memes={"wisdom": 1.0, "kindness": 1.0},
    ))
    world.facts.update(
        hero=hero,
        royal=royal,
        messenger=messenger,
        scene=scene,
        setting=params.setting,
        resolved=False,
    )

    world.say(OPENINGS[params.opening_id % len(OPENINGS)].format(
        hero=params.hero_name, setting=params.setting, signal=scene["signal"]
    ))
    world.say(
        f"{params.hero_name} wondered whether {scene['guess']}. "
        f"The unusual flirt looked like a dangerous enchantment."
    )
    hero.memes["worry"] += 0.5
    world.para()

    world.say(DIALOGUES[params.dialogue_id % len(DIALOGUES)].format(
        messenger=params.messenger_name
    ))
    world.say(
        f'“I saw the sign,” {params.hero_name} said. '
        f'“Could it be a flirt, or could it truly be a spell?”'
    )
    world.say(
        f'“You may ask me,” {params.royal_name} replied. '
        f'“Guessing alone will not tell us.”'
    )
    world.para()

    world.say(f"The helpful clue was that {scene['clue']}.")
    world.say(TURNS[params.turn_id % len(TURNS)].format(hero=params.hero_name))
    world.say(
        f"The stranger stepped into the moonlight and said, “{scene['truth']}.”"
    )
    world.say(
        f"{params.royal_name} listened, and {scene['resolution']}."
    )
    hero.meters["clarity"] = 1.0
    royal.meters["trust"] = 1.0
    royal.memes["relief"] = 1.0
    world.para()

    world.say(ENDINGS[params.ending_id % len(ENDINGS)].format(
        resolution=scene["resolution"], image=scene["image"]
    ))
    world.say(
        f"{params.hero_name} learned that {scene['lesson']}"
    )
    world.facts["resolved"] = True
    return world


ASP_RULES = r"""
misunderstanding :- signal, guessed_spell, asks_question.
clear_meaning :- misunderstanding, honest_answer.
resolved :- clear_meaning, kind_response.
#show misunderstanding/0.
#show clear_meaning/0.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("signal"),
        asp.fact("guessed_spell"),
        asp.fact("asks_question"),
        asp.fact("honest_answer"),
        asp.fact("kind_response"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
        names = {symbol.name for symbol in model}
        required = {"misunderstanding", "clear_meaning", "resolved"}
        if required.issubset(names):
            print("OK: ASP and Python both resolve the misunderstanding.")
            return 0
        print("MISMATCH: ASP model did not resolve the misunderstanding.")
        return 1
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1


def generation_prompts(world: CastleWorld) -> list[str]:
    scene = world.facts["scene"]
    hero = world.facts["hero"].label
    return [
        f"Write a fairy tale in which {hero} sees {scene['signal']} and mistakes a flirt for a spell.",
        "Tell a child-friendly story where a misunderstanding is solved through dialogue and a concrete clue.",
        "Write a complete fairy tale with a playful flirt, a worried guess, an honest explanation, and a peaceful ending image.",
    ]


def story_qa(world: CastleWorld) -> list[QAItem]:
    scene = world.facts["scene"]
    hero = world.facts["hero"].label
    royal = world.facts["royal"].label
    messenger = world.facts["messenger"].label
    return [
        QAItem(
            f"Why did {hero} misunderstand the flirt?",
            f"{hero} misunderstood it because {scene['signal']}, and {hero} first wondered whether {scene['guess']}.",
        ),
        QAItem(
            "What clue helped reveal the truth?",
            f"The clue was that {scene['clue']}. It showed that the strange signal had a friendly meaning.",
        ),
        QAItem(
            f"How did {hero} and {messenger} handle the mystery?",
            f"{messenger} urged everyone to ask instead of accuse. Then {hero} asked for an explanation and listened to the answer.",
        ),
        QAItem(
            f"What did {royal} learn?",
            f"{royal} learned that {scene['truth']}. The royal character responded openly instead of treating the flirt as a threat.",
        ),
        QAItem(
            "What lesson does the ending show?",
            f"The story teaches that {scene['lesson']} The ending image is that {scene['image']}.",
        ),
    ]


def world_knowledge_qa(world: CastleWorld) -> list[QAItem]:
    return [
        QAItem(
            "What is a fairy tale?",
            "A fairy tale is an imaginative story with wonders such as castles, enchanted creatures, brave travelers, or magical events.",
        ),
        QAItem(
            "What is a misunderstanding?",
            "A misunderstanding happens when someone gives an action or message a meaning that was not intended.",
        ),
        QAItem(
            "What does flirt mean in this story?",
            "Here, flirt means a playful or admiring signal meant to show interest, not a spell or a threat.",
        ),
        QAItem(
            "Why is asking a question helpful?",
            "Asking a question lets people explain their intentions, so a frightened guess can be replaced by understanding.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A fairy tale about a misunderstood flirt.")
    parser.add_argument("--name")
    parser.add_argument("--royal")
    parser.add_argument("--messenger")
    parser.add_argument("--setting")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
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
    royal = args.royal or rng.choice([name for name in ROYAL_NAMES if name != hero])
    messenger = args.messenger or rng.choice(MESSENGERS)
    setting = args.setting or "the moonlit castle garden"
    return StoryParams(
        hero_name=hero,
        hero_type="girl" if hero in {"Luna", "Mira", "Tessa", "Nia"} else "boy",
        royal_name=royal,
        messenger_name=messenger,
        setting=setting,
        scenario_id=rng.randrange(len(SCENARIOS)),
        opening_id=rng.randrange(len(OPENINGS)),
        dialogue_id=rng.randrange(len(DIALOGUES)),
        turn_id=rng.randrange(len(TURNS)),
        ending_id=rng.randrange(len(ENDINGS)),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: CastleWorld) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label}: kind={entity.kind}; "
            f"meters={entity.meters}; memes={entity.memes}; props={entity.props}"
        )
    lines.append(f"  resolved={world.facts.get('resolved')}")
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
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        if asp_verify() != 0:
            sys.exit(1)
        rng = random.Random(17)
        sample = generate(resolve_params(args, rng))
        if not sample.story or not sample.story_qa:
            print("MISMATCH: generated story or QA is empty.")
            sys.exit(1)
        print("OK: generated story exercised.")
        return
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        presets = [
            StoryParams("Luna", "girl", "Prince Alder", "the silver fox", scenario_id=0),
            StoryParams("Elian", "boy", "Princess Celeste", "the little page", scenario_id=1, opening_id=1, dialogue_id=2, turn_id=1, ending_id=1),
            StoryParams("Mira", "girl", "Prince Rowan", "the blue jay", scenario_id=4, opening_id=3, dialogue_id=3, turn_id=3, ending_id=3),
        ]
        samples = [generate(params) for params in presets]
    else:
        seen: set[str] = set()
        for index in range(max(1, args.n) * 20):
            if len(samples) >= max(1, args.n):
                break
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
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
        header = ""
        if args.all:
            header = f"### {sample.params.hero_name}: the misunderstood flirt"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
