#!/usr/bin/env python3
"""
A small mythic storyworld about a phoneme, a moral value, and transformation.

A young keeper discovers that changing one sound in a sacred word can change
what a village believes about kindness. The world tracks spoken sounds,
physical tokens, and emotional values; the story turns when careful listening
reveals that a tiny phoneme carries a large moral lesson.
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
ROOT = next((p for p in HERE.parents if (p / "results.py").is_file()), HERE.parent)
sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


NAME_POOL = ["Luna", "Mira", "Orin", "Tavi", "Nera", "Suri", "Ari", "Pela"]
ELDER_POOL = ["the moon keeper", "Grandmother Yara", "the old bell-maker", "the river sage"]
PLACE_POOL = ["the hill of listening", "the cedar shrine", "the silver valley", "the temple of echoes"]
VALUE_POOL = ["mercy", "truth", "courage", "patience"]
TOKEN_POOL = ["a clay tablet", "a moonstone", "a bronze bell", "a woven oath-cord"]

TRIALS = [
    {
        "sacred_word": "mara",
        "changed_word": "bara",
        "phoneme": "m",
        "old_meaning": "mercy",
        "new_meaning": "bareness",
        "problem": "a careless echo replaced the gentle opening sound with a hard one",
        "sign": "the village kindness jars became empty",
        "clue": "the first breath of the word had changed",
        "action": "slowly spoke the soft m sound before the gathered people",
        "transformation": "the empty jars filled with warm golden light",
        "lesson": "a small sound can guard a great kindness when people listen carefully",
        "ending": "At dawn, every doorway held a jar glowing with the village's restored mercy.",
    },
    {
        "sacred_word": "sala",
        "changed_word": "tala",
        "phoneme": "s",
        "old_meaning": "peace",
        "new_meaning": "cutting",
        "problem": "a sharp tongue turned the opening breath into a careless t",
        "sign": "the peace ribbons around the shrine began to unravel",
        "clue": "the word broke before its first breath could soften it",
        "action": "breathed the quiet s sound and tied each ribbon again",
        "transformation": "the loose ribbons curled into silver birds",
        "lesson": "patience gives a word room to become peaceful",
        "ending": "By sunrise, silver birds circled the shrine and no ribbon lay loose.",
    },
    {
        "sacred_word": "dara",
        "changed_word": "tara",
        "phoneme": "d",
        "old_meaning": "courage",
        "new_meaning": "distance",
        "problem": "fear swallowed the first voiced sound and left the oath hollow",
        "sign": "the mountain path grew longer each time someone tried to climb it",
        "clue": "the brave sound needed a voice, not a whisper",
        "action": "stood tall and gave the d sound its full ringing voice",
        "transformation": "the long path folded into a bright stairway",
        "lesson": "courage is not the absence of fear but the choice to speak through it",
        "ending": "That evening, the stairway shone from the village to the mountaintop.",
    },
    {
        "sacred_word": "pala",
        "changed_word": "bala",
        "phoneme": "p",
        "old_meaning": "patience",
        "new_meaning": "weight",
        "problem": "rushing lips turned a light puff into a heavy b",
        "sign": "the village clocks stopped between every hurried beat",
        "clue": "the word needed one gentle pause before its next sound",
        "action": "held the first breath, then released the p sound like a seed",
        "transformation": "the clocks began ticking with calm golden hearts",
        "lesson": "patience is a pause that lets the right action arrive",
        "ending": "From then on, the clocks kept time with the slow, kind rhythm of breathing.",
    },
]


@dataclass
class StoryParams:
    name: str = "Luna"
    elder: str = "the moon keeper"
    place: str = "the hill of listening"
    value: str = "mercy"
    token: str = "a moonstone"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("clarity", "distance", "warmth", "sound"):
            self.meters.setdefault(key, 0.0)
        for key in ("fear", "wonder", "care", "hope", "wisdom"):
            self.memes.setdefault(key, 0.0)


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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _seed_number(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum((i + 1) * ord(c) for i, c in enumerate(
        f"{params.name}|{params.elder}|{params.place}|{params.value}|{params.token}"
    ))


def tell_world(params: StoryParams) -> World:
    seed = _seed_number(params)
    rng = random.Random(seed)
    trial = TRIALS[seed % len(TRIALS)]
    w = World(place=params.place)
    child = w.add(Entity(params.name, "character", params.name))
    elder = w.add(Entity("elder", "character", params.elder))
    token = w.add(Entity("token", "relic", params.token))
    child.memes["wonder"] = 1
    child.meters["clarity"] = 0
    elder.memes["wisdom"] = 3
    token.meters["warmth"] = 1
    w.facts.update(params=params, trial=trial, child=child, elder=elder, token=token)

    w.say(f"In the first age, when mountains still remembered every name, {params.name} kept the listening fire at {params.place}.")
    w.say(f"Each new moon, the people carried {params.token} to the shrine and spoke the sacred word {trial['sacred_word']}, whose old meaning was {trial['old_meaning']}.")
    w.say(f"The word was small, but its moral value was not.")
    w.para()

    child.memes["fear"] += 2
    child.meters["distance"] = 4
    w.say(f"One evening, {trial['problem']}.")
    w.say(f"The people began saying {trial['changed_word']} instead, and {trial['sign']}.")
    w.say(f"{params.name} tried to repeat the word quickly, but the moonstone grew cold in their hands.")
    w.say(f'"Why does one little sound matter?" {params.name} asked.')
    w.say(f'{params.elder.capitalize()} answered, "Because a phoneme is a small door. Open the wrong door, and the meaning walks somewhere else."')
    w.para()

    child.meters["clarity"] += 1
    child.memes["care"] += 2
    child.memes["fear"] = 1
    w.say(f"{params.name} listened again. {trial['clue'].capitalize()}.")
    w.say(f'"Then show me the sound that was forgotten," {params.name} said.')
    w.say(f'"Do not force it," said {params.elder}. "Let your breath carry it, and let your heart carry the {trial["old_meaning"]} it protects."')
    w.say(f"So {params.name} {trial['action']}.")
    w.say(f"The first phoneme rang across the shrine, and the sacred word became {trial['sacred_word']} once more.")
    w.para()

    child.meters["clarity"] += 2
    child.meters["sound"] += 1
    child.memes["hope"] += 2
    child.memes["wisdom"] += 1
    child.memes["fear"] = 0
    token.meters["warmth"] += 3
    w.say(f"At once, {trial['transformation']}.")
    w.say(f"The people understood that {trial['lesson']}.")
    w.say(f"{params.name} held the warm token and knew that transformation had begun not in the stone, but in the way everyone listened.")
    w.para()
    w.say(trial["ending"])

    w.facts.update(
        resolved=True,
        phoneme=trial["phoneme"],
        sacred_word=trial["sacred_word"],
        changed_word=trial["changed_word"],
        moral_value=trial["old_meaning"],
        transformation=trial["transformation"],
    )
    return w


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    t = world.facts["trial"]
    return [
        f"Write a myth about {p.name} discovering how the phoneme {t['phoneme']} protects {t['old_meaning']}.",
        f"Tell a transformation myth at {p.place} in which one changed sound threatens a moral value.",
        f"Create a child-friendly myth with {p.elder}, {p.token}, a sacred word, and a concrete ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    t = world.facts["trial"]
    return [
        QAItem(
            question=f"What sacred word did {p.name} need to restore?",
            answer=f"{p.name} needed to restore the sacred word {t['sacred_word']}, which carried the moral value of {t['old_meaning']}.",
        ),
        QAItem(
            question=f"What phoneme had changed the word?",
            answer=f"The opening phoneme had changed from the gentle {t['phoneme']} sound to a harder sound, turning {t['sacred_word']} into {t['changed_word']}.",
        ),
        QAItem(
            question=f"How did {p.elder} explain the importance of a phoneme?",
            answer=f"{p.elder.capitalize()} explained that a phoneme is a small door, and opening the wrong door can send a word's meaning somewhere else.",
        ),
        QAItem(
            question=f"What transformation happened after {p.name} spoke carefully?",
            answer=f"After {p.name} restored the sacred word, {t['transformation']}.",
        ),
        QAItem(
            question="What moral value does the myth teach?",
            answer=f"The myth teaches that {t['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a phoneme?",
            answer="A phoneme is a small sound unit that can help distinguish one spoken word from another.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a principle about how people should treat one another and choose their actions.",
        ),
        QAItem(
            question="What is transformation in a myth?",
            answer="Transformation in a myth is a meaningful change in a person, object, place, or way of seeing the world.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 3) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 3) for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id} ({entity.kind}) meters={meters} memes={memes}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
% A sacred word is restored when its phoneme is heard and its moral value returns.
restored(Word) :- sacred_word(Word), has_phoneme(Word, Sound), speaks(Sound).
transformed(Value) :- restored(Word), protects(Word, Value).
valid_myth(Place, Value) :- myth_place(Place), moral_value(Value), transformed(Value).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in PLACE_POOL:
        lines.append(asp.fact("myth_place", place.replace(" ", "_")))
    for value in VALUE_POOL:
        lines.append(asp.fact("moral_value", value))
    for trial in TRIALS:
        word = trial["sacred_word"]
        lines.extend([
            asp.fact("sacred_word", word),
            asp.fact("has_phoneme", word, trial["phoneme"]),
            asp.fact("protects", word, trial["old_meaning"]),
        ])
    return "\n".join(lines)


def asp_program(show: str) -> str:
    facts = asp_facts()
    active = "\n".join([
        asp_fact for asp_fact in [
            'speaks("m").',
            'speaks("s").',
            'speaks("d").',
            'speaks("p").',
        ]
    ])
    return f"{facts}\n{active}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show valid_myth/2."))
    found = set(asp.atoms(model, "valid_myth"))
    expected = {(place.replace(" ", "_"), value) for place in PLACE_POOL for value in VALUE_POOL}
    if found == expected:
        for i, trial in enumerate(TRIALS):
            params = StoryParams(
                name=NAME_POOL[i],
                elder=ELDER_POOL[i],
                place=PLACE_POOL[i],
                value=trial["old_meaning"],
                token=TOKEN_POOL[i],
                seed=i,
            )
            sample = generate(params)
            if not sample.story or not sample.world.facts.get("resolved"):
                print("Generated story exercise failed.")
                return 1
        print(f"OK: ASP parity matches ({len(found)} valid myth combinations); generated stories resolve.")
        return 0
    print("MISMATCH between ASP and Python facts:")
    print("  ASP:", sorted(found))
    print("  PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic phoneme and moral transformation storyworld.")
    ap.add_argument("--name", choices=NAME_POOL)
    ap.add_argument("--elder", choices=ELDER_POOL)
    ap.add_argument("--place", choices=PLACE_POOL)
    ap.add_argument("--value", choices=VALUE_POOL)
    ap.add_argument("--token", choices=TOKEN_POOL)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(NAME_POOL),
        elder=args.elder or rng.choice(ELDER_POOL),
        place=args.place or rng.choice(PLACE_POOL),
        value=args.value or rng.choice(VALUE_POOL),
        token=args.token or rng.choice(TOKEN_POOL),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
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
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_myth/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_myth/2."))
        print(sorted(asp.atoms(model, "valid_myth")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, trial in enumerate(TRIALS):
            samples.append(generate(StoryParams(
                name=NAME_POOL[i % len(NAME_POOL)],
                elder=ELDER_POOL[i % len(ELDER_POOL)],
                place=PLACE_POOL[i % len(PLACE_POOL)],
                value=trial["old_meaning"],
                token=TOKEN_POOL[i % len(TOKEN_POOL)],
                seed=base_seed + i,
            )))
    else:
        seen: set[str] = set()
        i = 0
        limit = max(args.n * 50, 50)
        while len(samples) < args.n and i < limit:
            seed = base_seed + i
            i += 1
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
