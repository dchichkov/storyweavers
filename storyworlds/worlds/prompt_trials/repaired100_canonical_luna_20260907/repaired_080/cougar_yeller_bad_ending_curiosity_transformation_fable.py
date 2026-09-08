#!/usr/bin/env python3
"""
Standalone storyworld: the cougar and the yeller.

A small fable about a curious cougar who learns that a bad ending can change
when someone pauses, asks a question, and transforms a noisy habit into useful
care.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cougar", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            raise StoryError(f"Unknown story entity: {eid}")
        return self.entities[eid]

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
    cougar_name: str
    yeller_name: str
    valley: str = "the blue-thistle valley"
    scenario: int = 0
    opening: int = 0
    dialogue: int = 0
    ending: int = 0
    seed: Optional[int] = None


COUGAR_NAMES = ["Luma", "Kito", "Suri", "Mika", "Tala", "Nori", "Pax", "Cedar"]
YELLER_NAMES = ["Bram", "Pip", "Rollo", "Tansy", "Moss", "Bibi", "Otto", "Wren"]

OPENINGS = [
    "In a green valley where echoes lived longer than rabbits, a young cougar watched the morning fog unroll.",
    "At the edge of a forest bright with berries, a cougar heard one sharp cry bounce from hill to hill.",
    "Near a quiet stream, the animals woke to a voice so loud that even the pebbles seemed to listen.",
    "Once, beneath a moon as round as a silver bowl, a cougar followed a curious sound into the woods.",
    "In a valley of tall grass and sleepy stones, every creature knew when the yeller opened his mouth.",
    "One warm afternoon, the forest was peaceful until a shout startled three finches from one branch.",
]

DIALOGUES = [
    '"Why do you yell when no one is chasing you?" asked {cougar}. "I want to know what your voice is for."',
    '"Does your shout warn us, or only frighten us?" asked {cougar}. The yeller blinked and said, "I have never stopped to ask."',
    '"What would happen if you listened first?" asked {cougar}. "Then perhaps I would hear what needs saying," replied {yeller}.',
    '"Your voice is strong," said {cougar}, "but strength needs a direction." The yeller answered, "Show me one."',
    '"Can a yeller become a helper?" asked {cougar}. "Only if a helper may practice," said the yeller.',
    '"I thought loud meant brave," admitted the yeller. "Sometimes curiosity is braver," said the cougar.',
]

SCENARIOS = [
    {
        "trouble": "The yeller shouted at every rustle, so the rabbits fled from harmless leaves and missed the ripe clover.",
        "clue": "the cougar noticed that the true danger left three paw marks beside the creek",
        "question": "which sounds belonged to danger and which belonged only to wind",
        "action": "the yeller listened for the creek, the wind, and the careful pause between them",
        "result": "when a fallen branch really blocked the stream, his clear warning guided every animal around it",
        "image": "the animals drinking together while the yeller called softly from the safe bank",
        "lesson": "Curiosity can transform a frightening habit when it asks what a sound is meant to do.",
    },
    {
        "trouble": "The yeller announced every berry he found, and his booming calls sent the birds away before they could help spread the seeds.",
        "clue": "the cougar saw that the quietest berry patch had the most new green shoots",
        "question": "whether a useful message always had to be loud",
        "action": "the yeller practiced a whisper for nearby friends and a single bright call for faraway ones",
        "result": "the birds returned, and the berry bushes grew thick enough to feed the whole valley",
        "image": "small birds carrying seeds while the transformed yeller guarded the patch with one gentle call",
        "lesson": "Transformation begins when curiosity notices that a better way may already be growing nearby.",
    },
    {
        "trouble": "The yeller challenged the mountain echo every dawn, and the echo answered until the animals could not hear the approaching rain.",
        "clue": "the cougar felt cool drops before the clouds became dark",
        "question": "what the forest needed to hear before the storm",
        "action": "the yeller stopped competing with the echo and gave three measured calls for shelter",
        "result": "the animals reached the hollow tree before the rain poured down",
        "image": "the yeller and the cougar watching the storm from safety as one small call traveled clearly",
        "lesson": "A voice becomes wiser when curiosity teaches it to leave room for other sounds.",
    },
    {
        "trouble": "The yeller cried wolf whenever he felt lonely, and soon the goats stopped looking up.",
        "clue": "the cougar found real wolf tracks near the old stone wall",
        "question": "how to make the goats trust a warning again",
        "action": "the yeller admitted his false alarms and promised to call only when he had checked the ground",
        "result": "the goats listened, moved together, and escaped the real wolf before sunset",
        "image": "the goats safe behind the wall while the former yeller stood quietly beside the tracks",
        "lesson": "Curiosity asks for evidence, and honest change can repair trust after a bad ending seems near.",
    },
    {
        "trouble": "The yeller shouted directions at everyone, but his hurried commands sent the mice toward the thorn hedge.",
        "clue": "the cougar noticed a narrow path marked by smooth stones",
        "question": "where the small creatures could travel without being pushed",
        "action": "the yeller asked the mice what they could see and repeated their answer in a calm voice",
        "result": "the mice crossed the meadow safely and taught the yeller a path he had never noticed",
        "image": "tiny mice leading the way while the transformed yeller followed instead of ordering",
        "lesson": "A curious question can turn a bossy voice into a listening heart.",
    },
]

ENDINGS = [
    "From that day on, the forest called him the yeller only when telling the old story; in daily life, they called him the careful caller.",
    "The valley kept its echoes, but it no longer feared them.",
    "And if a loud voice rose among the trees, the cougar smiled and asked, 'What is it for?'",
    "The animals learned that a bad ending is not always the last page if someone is willing to change.",
    "Even the stones seemed happier, for they heard warnings, welcomes, and questions instead of needless noise.",
    "So the yeller's voice did not become smaller; it became kinder, and that was the true transformation.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A fable about a curious cougar and a yeller who transforms a bad ending."
    )
    parser.add_argument("--cougar-name")
    parser.add_argument("--yeller-name")
    parser.add_argument("--valley", default="the blue-thistle valley")
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
    cougar_name = args.cougar_name or rng.choice(COUGAR_NAMES)
    yeller_name = args.yeller_name or rng.choice(YELLER_NAMES)
    if cougar_name == yeller_name:
        raise StoryError("The cougar and yeller must have different names.")
    return StoryParams(
        cougar_name=cougar_name,
        yeller_name=yeller_name,
        valley=args.valley or "the blue-thistle valley",
        scenario=rng.randrange(len(SCENARIOS)),
        opening=rng.randrange(len(OPENINGS)),
        dialogue=rng.randrange(len(DIALOGUES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def build_world(params: StoryParams) -> World:
    if not params.cougar_name.strip() or not params.yeller_name.strip():
        raise StoryError("Both the cougar and yeller need names.")
    world = World()
    cougar = world.add(
        Entity(
            id="Cougar",
            kind="character",
            type="cougar",
            label=params.cougar_name,
            phrase="a young cougar",
            memes={"curiosity": 1.0},
        )
    )
    yeller = world.add(
        Entity(
            id="Yeller",
            kind="character",
            type="person",
            label=params.yeller_name,
            phrase="the yeller",
            memes={"noise": 1.0},
        )
    )
    valley = world.add(
        Entity(
            id="Valley",
            kind="place",
            type="valley",
            label=params.valley,
            phrase=params.valley,
        )
    )
    world.facts.update(cougar=cougar, yeller=yeller, valley=valley, params=params)
    return world


def tell(world: World) -> None:
    params: StoryParams = world.facts["params"]
    cougar: Entity = world.get("Cougar")
    yeller: Entity = world.get("Yeller")
    valley: Entity = world.get("Valley")
    scenario = SCENARIOS[params.scenario % len(SCENARIOS)]
    world.facts["scenario"] = scenario

    world.say(OPENINGS[params.opening % len(OPENINGS)])
    world.say(
        f"In {valley.phrase} lived {cougar.label}, a thoughtful cougar, and {yeller.label}, "
        f"who was known simply as the yeller."
    )
    world.say(f"{scenario['trouble']}")

    world.para()
    world.say(
        f"At first, the story seemed headed for a bad ending: {scenario['trouble']} "
        "The animals hid, the useful work stopped, and nobody trusted the next sound."
    )
    world.say(
        f"But {cougar.label} was curious. Instead of covering his ears, "
        f"{cougar.pronoun('subject')} followed the sound and found that {scenario['clue']}."
    )
    world.say(
        DIALOGUES[params.dialogue % len(DIALOGUES)].format(
            cougar=cougar.label,
            yeller=yeller.label,
        )
    )

    world.para()
    world.say(
        f"The question changed the yeller. He did not throw away his strong voice; "
        f"he transformed it by asking {scenario['question']}."
    )
    world.say(f"Together, the cougar and the yeller {scenario['action']}.")
    yeller.memes["noise"] = 0.0
    yeller.memes["care"] = 1.0
    yeller.meters["transformed"] = 1.0
    cougar.memes["curiosity"] = 2.0
    world.say(f"Then the trouble turned: {scenario['result']}.")

    world.para()
    world.say(f"The ending image was clear: {scenario['image']}.")
    world.say(scenario["lesson"])
    world.say(ENDINGS[params.ending % len(ENDINGS)])
    world.facts.update(
        resolved=True,
        bad_ending_avoided=True,
        transformation=True,
        clue=scenario["clue"],
        question=scenario["question"],
        action=scenario["action"],
        result=scenario["result"],
        ending_image=scenario["image"],
    )


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    scenario = world.facts["scenario"]
    return [
        f"Write a child-facing fable about a cougar named {params.cougar_name} and a yeller named {params.yeller_name}.",
        f"Tell a story set in {params.valley} where curiosity prevents a bad ending.",
        f"Show how the yeller transforms after learning to ask {scenario['question']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    scenario = world.facts["scenario"]
    yeller: Entity = world.get("Yeller")
    return [
        QAItem(
            question="Who were the two main characters?",
            answer=f"The two main characters were {params.cougar_name}, a curious cougar, and {params.yeller_name}, the yeller.",
        ),
        QAItem(
            question="Why did the story seem headed for a bad ending?",
            answer=f"It seemed headed for a bad ending because {scenario['trouble']} The animals were frightened and the useful work stopped.",
        ),
        QAItem(
            question="What did the cougar's curiosity discover?",
            answer=f"The cougar discovered that {scenario['clue']}. That clue helped the animals understand the real problem.",
        ),
        QAItem(
            question=f"How did {params.yeller_name} transform?",
            answer=f"{params.yeller_name} transformed when {scenario['action']}. He kept his strong voice but used it with care.",
        ),
        QAItem(
            question="How was the bad ending changed?",
            answer=f"The bad ending changed because {scenario['result']}. The animals became safe, and they could trust the yeller again.",
        ),
        QAItem(
            question="What lesson does the fable teach?",
            answer=f"The fable teaches that {scenario['lesson']}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cougar?",
            answer="A cougar is a large wild cat with a long tail that can live in forests, hills, and other habitats.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to learn or understand something by noticing, asking, and exploring.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation is a meaningful change from one condition or behavior into another.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story, often with animals, that teaches a lesson about how to live.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        parts = []
        if entity.meters:
            parts.append(f"meters={entity.meters}")
        if entity.memes:
            parts.append(f"memes={entity.memes}")
        lines.append(f"{entity.id}: {' '.join(parts) if parts else '(quiet)'}")
    lines.append(f"facts={world.facts.get('resolved', False)} resolved")
    return "\n".join(lines)


ASP_RULES = r"""
curious(cougar).
has_voice(yeller).
bad_ending :- loud_noise, fear.
asks_question :- curious(cougar), has_voice(yeller).
transformed :- asks_question, listens(yeller).
safe :- transformed.
good_ending :- safe.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("curious", "cougar"),
            asp.fact("has_voice", "yeller"),
            asp.fact("loud_noise"),
            asp.fact("fear"),
            asp.fact("listens", "yeller"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> str:
    return asp_program(
        "#show bad_ending/0. #show asks_question/0. "
        "#show transformed/0. #show safe/0. #show good_ending/0."
    )


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_valid())
    except Exception as exc:
        print(f"ASP verification failed: {exc}", file=sys.stderr)
        return 1
    names = {f"{atom.name}/{len(atom.arguments)}" for atom in model}
    required = {"bad_ending/0", "asks_question/0", "transformed/0", "safe/0", "good_ending/0"}
    if not required.issubset(names):
        print(f"ASP parity failed; expected {sorted(required)}, got {sorted(names)}", file=sys.stderr)
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("transformation"):
            print("Python story verification failed.", file=sys.stderr)
            return 1
        if "bad ending" not in sample.story.lower() or "transform" not in sample.story.lower():
            print("Generated story does not exercise the required narrative turn.", file=sys.stderr)
            return 1
    print("OK: ASP and Python story parity verified.")
    return 0


CURATED = [
    StoryParams(cougar_name="Luma", yeller_name="Bram", valley="the blue-thistle valley", scenario=0, opening=0, dialogue=0, ending=0),
    StoryParams(cougar_name="Kito", yeller_name="Pip", valley="the red-stone valley", scenario=1, opening=2, dialogue=3, ending=4),
    StoryParams(cougar_name="Suri", yeller_name="Rollo", valley="the echoing valley", scenario=3, opening=4, dialogue=5, ending=2),
]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
        print(asp_valid())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
            model = asp.one_model(asp_valid())
        except Exception as exc:
            raise SystemExit(f"ASP mode unavailable: {exc}")
        print("\n".join(str(atom) for atom in model))
        return

    if args.n < 1:
        raise SystemExit("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(args.n * 50, 50):
            current_seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(current_seed))
            params.seed = current_seed
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
        if args.all:
            params = sample.params
            header = f"### {params.cougar_name} and {params.yeller_name} in {params.valley}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
