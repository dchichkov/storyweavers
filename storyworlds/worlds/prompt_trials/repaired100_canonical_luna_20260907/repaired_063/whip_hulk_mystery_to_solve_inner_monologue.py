#!/usr/bin/env python3
"""
A standalone mythic storyworld about a whip, a hulk, and a transformation.

The seed tale behind this world:
A young keeper found a broken whip beside an ancient hulk of stone and wood.
The hulk seemed to guard a mystery: why did its great heart no longer move?
By listening to an inner voice, the keeper learned that the whip was not a
weapon but a bell-rope for waking courage. When the keeper used it gently,
the hulk transformed into a bridge for the village.
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

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the valley beneath the sleeping mountain"


@dataclass
class StoryParams:
    name: str
    village_name: str
    spirit_name: str
    mystery_id: int = 0
    omen_mode: int = 0
    thought_mode: int = 0
    turning_mode: int = 0
    ending_mode: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


SETTING = Setting()

NAMES = ["Luna", "Eira", "Tavi", "Mara", "Niko", "Suri", "Orin", "Pia"]
VILLAGES = ["the reed village", "the hill village", "the village of blue roofs"]
SPIRITS = ["Aster", "Moss", "Ilyra", "Tovan"]

MYSTERIES = [
    {
        "object": "a cracked whip of silver grass",
        "hulk": "a toppled hulk of cedar and black stone",
        "question": "why the hulk's stone heart was cold when the village well had begun to dry",
        "danger": "The river gorge lay below the hulk, so nobody climbed its broken ribs or pulled at its stones.",
        "false": "Some villagers believed the hulk was angry and that the whip had been left to punish anyone who came near.",
        "clue": "small water marks beneath the hulk, seed husks inside its hollow chest, and a faded sun carved on the whip handle",
        "cause": "The hulk had once turned an underground water wheel; fallen roots had jammed its heart, while the whip had been a keeper's signal rope.",
        "action": "Luna cleared only the loose seed husks from the safe opening and tied the whip to the old signal post while the elders loosened the buried roots.",
        "result": "The wheel turned, the well filled, and the hulk's great stones settled into a strong crossing over the gorge.",
        "lesson": "A frightening shape may be waiting for care, not battle.",
        "image": "At sunset, children crossed the new stone bridge while the silver whip rang softly in the warm wind.",
    },
    {
        "object": "a red leather whip braided with golden thread",
        "hulk": "a rusted hulk of an ancient river boat",
        "question": "why the boat hulk groaned each night though no river touched its dry resting place",
        "danger": "The hulk's ribs were sharp and unstable, so the villagers watched from the meadow beyond the warning stones.",
        "false": "The elders first feared that a river giant was trapped inside and wanted the whip to call it out.",
        "clue": "mud in the hulk's lowest beam, fish scales far from the river, and a bell mark on the whip's clasp",
        "cause": "A flood had carried the boat onto the hill, and the whip had belonged to the ferryman who rang the boat bell.",
        "action": "Luna spoke with the ferryman's descendants, who used the whip to pull the bell cord while builders braced the hulk from outside.",
        "result": "The bell's call guided workers to turn the hulk into a sheltered storehouse for grain.",
        "lesson": "Remembering an object's purpose can change fear into help.",
        "image": "Golden grain filled the old boat while its bell answered the evening stars.",
    },
    {
        "object": "a blue cord called a whip by the mountain clans",
        "hulk": "a moss-covered hulk of a fallen statue",
        "question": "why the statue's enormous hand pointed toward the cloud forest",
        "danger": "Rain made the statue's slope slippery, so Luna stayed on the marked path and used a spyglass.",
        "false": "The villagers guessed that the stone giant was demanding a treasure from the clouds.",
        "clue": "lichen arrows, a dry channel beneath the pointing hand, and the cord's matching blue knots",
        "cause": "The statue marked an old water route, and the blue whip was a guide line for travelers crossing the wet slope.",
        "action": "Luna followed the clues with the mountain guide and stretched the cord along the safe route while workers reopened the channel.",
        "result": "Cloud water flowed into the village gardens, and the fallen statue became a sheltering shade wall.",
        "lesson": "A mystery becomes kinder when we ask what a sign once meant.",
        "image": "Morning vines climbed the statue's hand as blue water ran beside the bright guide cord.",
    },
]

OPENINGS = [
    "Before the first rooster called,",
    "On the morning when the mountain wore a crown of cloud,",
    "At the edge of the long summer drought,",
    "When the moon still shone over the valley,",
    "On a day remembered by every village elder,",
]

INNER_THOUGHTS = [
    '"A whip can frighten," Luna thought, "but perhaps it can also carry a message."',
    '"The hulk looks like a monster," Luna thought, "yet monsters do not leave careful clues."',
    '"If I listen before I act, the mountain may tell me what it needs," Luna thought.',
    '"Fear is loud," Luna told herself, "but the small facts are quieter and truer."',
]

OMEN_LINES = [
    "A raven circled once, then flew toward the safest path.",
    "The mountain wind lifted dust from the old marks but left the useful clues clear.",
    "A pale moth rested on the handle, as if guarding a memory.",
    "The clouds opened above the hulk, and a narrow beam showed its hidden shape.",
]

TURNING_LINES = [
    "Luna did not strike the hulk. She tested the old signal and waited.",
    "She laid the whip down like a bridge between the past and the present.",
    "The keeper asked the elders what they remembered before touching anything.",
    "Instead of fighting the hulk, Luna searched for the work it had once done.",
]

ENDING_REFLECTIONS = [
    "From that day onward, the villagers called wisdom a kind of courage.",
    "The people learned that a mystery could be solved without making an enemy.",
    "Luna understood that transformation begins when fear is given a patient question.",
    "The old hulk had not needed a hero with a weapon; it had needed a keeper with ears.",
]

WORLD_FACTS = [
    ("What is a hulk?", "A hulk is a large, heavy, or ruined structure, vehicle, or body."),
    ("Why should people study clues?", "People study clues because careful evidence can reveal what happened and prevent a hasty mistake."),
    ("What is a transformation?", "A transformation is a meaningful change from one form, state, or purpose into another."),
    ("Why can an inner thought help in a story?", "An inner thought lets us hear a character consider choices before deciding what to do."),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mythic storyworld about a whip, a hulk, and a transformation."
    )
    parser.add_argument("--name")
    parser.add_argument("--village-name")
    parser.add_argument("--spirit-name")
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
    village = args.village_name or rng.choice(VILLAGES)
    spirit = args.spirit_name or rng.choice(SPIRITS)
    if not name.strip():
        raise StoryError("name must not be empty")
    return StoryParams(
        name=name,
        village_name=village,
        spirit_name=spirit,
        mystery_id=rng.randrange(len(MYSTERIES)),
        omen_mode=rng.randrange(len(OMEN_LINES)),
        thought_mode=rng.randrange(len(INNER_THOUGHTS)),
        turning_mode=rng.randrange(len(TURNING_LINES)),
        ending_mode=rng.randrange(len(ENDING_REFLECTIONS)),
    )


def _build_world(params: StoryParams) -> World:
    if params.mystery_id < 0 or params.mystery_id >= len(MYSTERIES):
        raise StoryError("mystery_id must select a known mystery")
    world = World(SETTING)
    hero = world.add(Entity("hero", "character", "keeper", params.name))
    village = world.add(Entity("village", "community", "village", params.village_name))
    spirit = world.add(Entity("spirit", "character", "mountain-spirit", params.spirit_name))
    whip = world.add(Entity("whip", "object", "whip", "the old whip"))
    hulk = world.add(Entity("hulk", "structure", "hulk", "the ancient hulk"))
    heart = world.add(Entity("heart", "mechanism", "stone-heart", "the hulk's heart"))

    hero.memes.update(courage=1, curiosity=1, patience=0)
    village.memes.update(hope=1, trust=0)
    spirit.memes.update(wisdom=1)
    whip.meters.update(signal=0, meaning=0)
    hulk.meters.update(still=1, changed=0, safe=0)
    heart.meters.update(jammed=1, moving=0)

    world.facts.update(
        hero=hero,
        village=village,
        spirit=spirit,
        whip=whip,
        hulk=hulk,
        heart=heart,
        mystery=MYSTERIES[params.mystery_id],
        params=params,
        mystery_solved=False,
        transformed=False,
    )
    return world


def tell(world: World) -> None:
    facts = world.facts
    params: StoryParams = facts["params"]
    hero: Entity = facts["hero"]
    village: Entity = facts["village"]
    spirit: Entity = facts["spirit"]
    whip: Entity = facts["whip"]
    hulk: Entity = facts["hulk"]
    mystery = facts["mystery"]

    world.say(
        f"{OPENINGS[params.omen_mode % len(OPENINGS)]} {hero.label}, keeper of {village.label}, "
        f"walked to {SETTING.place}."
    )
    world.say(
        f"There she found {mystery['object']} beside {mystery['hulk']}, a great shape "
        f"the villagers called a hulk."
    )
    world.say(f"The mystery was {mystery['question']}.")

    world.para()
    world.say(mystery["danger"])
    world.say(mystery["false"])
    world.say(OMEN_LINES[params.omen_mode % len(OMEN_LINES)])
    world.say(INNER_THOUGHTS[params.thought_mode % len(INNER_THOUGHTS)])
    world.say(
        f'{spirit.label} appeared beside the path and said, "Do not name the hulk a monster '
        f'until you know what work it remembers."'
    )
    world.say(
        f'{hero.label} answered, "Then tell me what the whip was meant to do."'
    )
    world.say(
        f'{spirit.label} replied, "Its cord carried a signal. A gentle hand may wake an old promise."'
    )

    world.para()
    world.say(
        f"{hero.label} studied {mystery['clue']} before taking one careful step."
    )
    world.say(TURNING_LINES[params.turning_mode % len(TURNING_LINES)])
    world.say(
        f"The clues showed that {mystery['cause']} {hero.label} understood that the mystery "
        f"was not a curse but a forgotten duty."
    )
    world.say(
        f'{hero.label} whispered, "I hear you now, old hulk. We will mend what can be mended."'
    )

    world.para()
    world.say(mystery["action"])
    world.say(mystery["result"])
    world.say(
        f"The {whip.type} became a signal of cooperation, and the hulk changed from a danger "
        f"into a gift for {village.label}."
    )
    world.say(ENDING_REFLECTIONS[params.ending_mode % len(ENDING_REFLECTIONS)])
    world.say(mystery["image"])

    whip.meters["signal"] = 1
    whip.meters["meaning"] = 1
    hulk.meters["still"] = 0
    hulk.meters["changed"] = 1
    hulk.meters["safe"] = 1
    facts["mystery_solved"] = True
    facts["transformed"] = True
    hero.memes["patience"] = 1
    village.memes["trust"] = 1


def generation_prompts(world: World) -> list[str]:
    mystery = world.facts["mystery"]
    return [
        f"Write a myth about {world.facts['hero'].label}, a whip, and {mystery['hulk']}.",
        "Tell a child-friendly mystery in which an inner monologue leads to a wise choice.",
        "Write a mythic transformation where a frightening hulk becomes useful through careful investigation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    params: StoryParams = facts["params"]
    mystery = facts["mystery"]
    return [
        QAItem(
            question=f"What did {params.name} find beside the hulk?",
            answer=f"{params.name} found {mystery['object']} beside {mystery['hulk']}.",
        ),
        QAItem(
            question="What mystery did the keeper need to solve?",
            answer=f"The keeper had to learn {mystery['question']}.",
        ),
        QAItem(
            question="What clues helped solve the mystery?",
            answer=f"The clues were {mystery['clue']}.",
        ),
        QAItem(
            question="What was the whip really for?",
            answer=mystery["cause"],
        ),
        QAItem(
            question="How did the keeper avoid danger?",
            answer=mystery["action"],
        ),
        QAItem(
            question="How did the hulk transform?",
            answer=mystery["result"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in WORLD_FACTS]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {entity.id:8} ({entity.type:14}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
mystery_present :- whip(found), hulk(waiting).
inner_voice :- keeper(thoughtful).
transformation_ready :- mystery_present, inner_voice, clues(checked).
good_story :- transformation_ready, hulk(changed).
#show good_story/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("whip", "found"),
            asp.fact("hulk", "waiting"),
            asp.fact("keeper", "thoughtful"),
            asp.fact("clues", "checked"),
            asp.fact("hulk", "changed"),
        ]
    )


def asp_program(show: str = "#show good_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    good = any(symbol.name == "good_story" for symbol in model)
    if good:
        print("OK: ASP twin agrees that the whip, inner voice, clues, and transformation form a sound myth.")
        return 0
    print("MISMATCH: ASP twin did not find good_story.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    tell(world)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "the reed village", "Aster", mystery_id=0),
    StoryParams("Eira", "the hill village", "Moss", mystery_id=1),
    StoryParams("Tavi", "the village of blue roofs", "Ilyra", mystery_id=2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("good_story" if any(symbol.name == "good_story" for symbol in model) else "(none)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1")
        seen: set[str] = set()
        for offset in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
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
        header = ""
        if args.all:
            header = f"### {sample.params.name} and the hulk"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
