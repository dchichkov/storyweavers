#!/usr/bin/env python3
"""
A gentle bedtime storyworld about recognizing a distant magical call.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    helper: str = "Milo"
    creature: str = "the moon fox"
    place: str = "a quiet hill above the sleeping village"
    object_name: str = "silver bell"
    task: str = "listen for the bell that guided lost dreamers home"


@dataclass(frozen=True)
class Calling:
    name: str
    first_sound: str
    confusion: str
    clue: str
    mistake: str
    cause: str
    helper_job: str
    hero_job: str
    repair: str
    lesson: str
    ending: str


CALLINGS = [
    Calling(
        "The Faraway Chime",
        "a soft ting-ting floated from beyond the dark pine trees",
        "Luna thought the distant sound was only the wind teasing the night",
        "the sound came in three careful notes, then paused for an answer",
        "she pulled the blanket higher and decided to wait until morning",
        "the moon fox was ringing a tiny bell beside a lost child's dream",
        "counted the pauses and followed the safe lantern path",
        "answered with the silver bell and walked slowly toward the call",
        "recognized the fox's signal and led the dream safely back to the village",
        "A quiet voice can still matter when we take time to recognize it.",
        "the moon fox curled beside the bell while a warm dream-light returned to every window",
    ),
    Calling(
        "The Whispering Remote",
        "a whisper seemed to come from a little remote resting on the bedside table",
        "Milo believed the remote was broken because its buttons made no bright picture",
        "one button caused a tiny blue star to blink whenever the whisper sounded",
        "he pressed every button at once and made the room flash wildly",
        "the remote was a magic finder calling Luna toward a hidden kindness",
        "covered the buttons and listened for the pattern",
        "recognized the blue star and carried the remote to the moonlit window",
        "used the remote to guide a wandering night bird back to its nest",
        "Magic works best when curiosity is gentler than hurry.",
        "the remote rested quietly beside the pillow, its one blue star glowing like a promise",
    ),
    Calling(
        "The Little Come-Back Song",
        "a small voice called, 'Come,' from behind the garden wall",
        "Luna thought the voice belonged to a scary shadow",
        "the caller repeated Luna's name and hummed the tune her grandmother used",
        "she hid behind the rosebush and told Milo to answer for her",
        "a frightened starling had fallen into a soft basket and needed a familiar voice",
        "held the lantern low and asked the caller to sing again",
        "recognized the bird's song and opened the basket carefully",
        "A brave heart can come closer without becoming careless.",
        "the starling flew free, calling good night as the garden settled into silver sleep",
    ),
    Calling(
        "The Remote Doorbell",
        "a bell rang from the remote mountain path though no house stood there",
        "Milo guessed that the sound was an echo and not a real invitation",
        "the echo answered only when Luna said, 'We hear you'",
        "they shouted toward the mountain until their voices grew tired",
        "a magic door had opened for a weary cloud shepherd",
        "listened for the answering echo and marked the safe stones",
        "recognized the true bell beneath the echo and called back kindly",
        "showed the shepherd the path to the warm observatory",
        "When we recognize another's need, kindness gives our words a direction.",
        "the mountain door closed softly after the shepherd's lantern joined the stars",
    ),
    Calling(
        "The Sound Under Snow",
        "a muffled hum came from beneath the snow near the old spruce",
        "Luna believed the snow was only settling",
        "the hum matched the rhythm of a small wooden drum",
        "she stamped the snow flat, making the sound harder to hear",
        "a magic drum had slipped from the moon fox's pack",
        "brushed snow aside with a branch and kept the path clear",
        "recognized the drumbeat and answered with two taps",
        "returned the drum so the fox could call its family",
        "Listening carefully is a form of kindness.",
        "three gentle drumbeats traveled across the snow, and fox lights appeared in reply",
    ),
]

OPENINGS = [
    "At bedtime, when the village lamps were turning gold",
    "One sleepy evening beneath a round white moon",
    "In a little room overlooking the quiet hills",
    "Just as the stars began their slow night dance",
    "On a soft night when even the trees seemed to whisper",
]

DIALOGUE = [
    "“Did you hear that?” Luna asked. “I heard it too,” Milo replied.",
    "“Should we come closer?” Milo whispered. “Yes, but slowly,” Luna said.",
    "“What does the sound want?” Luna asked. “Perhaps it wants us to recognize it,” Milo said.",
    "“I am afraid,” Milo admitted. “Then we will be careful together,” Luna answered.",
    "“Call once more,” Luna said. “Come safely, little friend,” Milo called back.",
]

ENDING_THOUGHTS = [
    "Milo remembered that night whenever a small sound seemed easy to ignore.",
    "Luna kept the lesson close: kindness begins by paying attention.",
    "After that, the children listened before they guessed.",
    "The moon fox taught them that courage can be quiet and patient.",
    "Even the remote hills seemed friendlier after that bedtime adventure.",
]


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class World:
    params: StoryParams
    hero: Entity
    helper: Entity
    creature: Entity
    calling: Calling
    recognized: bool = False
    came_closer: bool = False
    repaired: bool = False
    magic_active: bool = False
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A bedtime story about recognizing a remote magical call.")
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--creature")
    parser.add_argument("--place")
    parser.add_argument("--object-name")
    parser.add_argument("--task")
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
    return StoryParams(
        seed=args.seed,
        hero=args.hero or rng.choice(["Luna", "Nora", "Iris", "Tessa"]),
        helper=args.helper or rng.choice(["Milo", "Theo", "Pip", "Arlo"]),
        creature=args.creature or rng.choice(["the moon fox", "a sleepy starling", "the cloud shepherd"]),
        place=args.place or rng.choice([
            "a quiet hill above the sleeping village",
            "a little room beside the remote pine forest",
            "the moonlit garden behind the cottage",
        ]),
        object_name=args.object_name or rng.choice(["silver bell", "little remote", "wooden drum"]),
        task=args.task or "listen for the sound that guided lost dreamers home",
    )


def _validate(params: StoryParams) -> None:
    if not params.hero.strip() or not params.helper.strip():
        raise StoryError("The bedtime story needs both a hero and a helper.")
    if params.hero.casefold() == params.helper.casefold():
        raise StoryError("The hero and helper should have different names.")
    forbidden = {"poison", "weapon", "blood", "dangerous"}
    if any(word in params.object_name.lower().split() for word in forbidden):
        raise StoryError("The magical object must be gentle and bedtime-safe.")
    if not params.place.strip():
        raise StoryError("The story needs a remote place to explore.")


def _rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0xC0ME)
    text = "|".join([
        params.hero, params.helper, params.creature, params.place,
        params.object_name, params.task,
    ])
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big"))


def _setup(world: World, opening: str) -> None:
    p = world.params
    world.say(
        f"{opening}, {p.hero} and {p.helper} were together at {p.place}. "
        f"They had promised to {p.task}, using a {p.object_name} that shimmered with gentle magic."
    )
    world.say(
        f"The night was quiet except for the sound effects of crickets, rustling leaves, and a faraway "
        f"“whoosh” from the sleeping hills. Then {p.creature} appeared beside the window."
    )


def _trouble(world: World, dialogue: str) -> None:
    p = world.params
    c = world.calling
    world.para()
    world.magic_active = True
    world.creature.add_meme("hope", 1)
    world.hero.add_meme("uncertainty", 1)
    world.say(f"Then the trouble began: {c.first_sound}.")
    world.say(f"{c.confusion.capitalize()}. {c.mistake.capitalize()}.")
    world.say(dialogue)


def _turn(world: World) -> None:
    p = world.params
    c = world.calling
    world.para()
    world.hero.add_meme("courage", 1)
    world.helper.add_meme("patience", 1)
    world.say(f"{p.helper} placed one hand over the {p.object_name} and whispered, “Let us listen before we guess.”")
    world.say(f"They noticed that {c.clue}. The remote sound was not random after all.")
    world.say(f"{p.hero} said, “{c.first_sound.capitalize()} I recognize that this is a call for help.”")
    world.say(f"Together, they decided to come closer, carefully and kindly.")
    world.came_closer = True


def _resolution(world: World, thought: str) -> None:
    p = world.params
    c = world.calling
    world.para()
    world.recognized = True
    world.repaired = True
    world.say(f"They discovered the truth: {c.cause}.")
    world.say(f"{p.helper} {c.helper_job}; {p.hero} {c.hero_job}.")
    world.say(f"Their repair was simple and brave: they {c.repair}.")
    world.say(f"{_capitalize(c.lesson)}")
    world.say(f"At last, {c.ending} {thought}")


def _capitalize(text: str) -> str:
    return text[:1].upper() + text[1:]


def tell(params: StoryParams) -> World:
    _validate(params)
    rng = _rng(params)
    hero = Entity(params.hero, "hero")
    helper = Entity(params.helper, "helper")
    creature = Entity(params.creature, "magical caller")
    calling = rng.choice(CALLINGS)
    world = World(params, hero, helper, creature, calling)
    _setup(world, rng.choice(OPENINGS))
    _trouble(world, rng.choice(DIALOGUE))
    _turn(world)
    _resolution(world, rng.choice(ENDING_THOUGHTS))
    world.facts = {
        "hero": params.hero,
        "helper": params.helper,
        "creature": params.creature,
        "place": params.place,
        "object": params.object_name,
        "calling": calling.name,
        "clue": calling.clue,
        "cause": calling.cause,
        "repair": calling.repair,
        "lesson": calling.lesson,
        "recognized": world.recognized,
        "came_closer": world.came_closer,
        "resolved": world.repaired,
        "magic": world.magic_active,
    }
    return world


ASP_RULES = r"""
hero(X) :- hero_name(X).
helper(X) :- helper_name(X).
remote_call :- distant_sound, pattern_found.
recognized :- remote_call, listens(hero), names_need(hero).
came_closer :- recognized, chooses_care(hero).
repaired :- came_closer, helps(helper), magic_guides(caller).
moral_value :- recognized, repaired.
#show remote_call/0.
#show recognized/0.
#show came_closer/0.
#show repaired/0.
#show moral_value/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero_name", "luna"),
        asp.fact("helper_name", "milo"),
        asp.fact("distant_sound"),
        asp.fact("pattern_found"),
        asp.fact("listens", "hero"),
        asp.fact("names_need", "hero"),
        asp.fact("chooses_care", "hero"),
        asp.fact("helps", "helper"),
        asp.fact("magic_guides", "caller"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _asp_available() -> bool:
    try:
        import clingo  # noqa: F401
        return True
    except Exception:
        return False


def asp_verify() -> int:
    if not _asp_available():
        print("ASP verification unavailable: clingo is not installed.")
        return 1
    import asp
    model = asp.one_model(asp_program())
    got = {str(atom) for atom in model}
    expected = {"remote_call", "recognized", "came_closer", "repaired", "moral_value"}
    if expected.issubset(got):
        print("OK: ASP and Python story states agree.")
        sample = generate(StoryParams(seed=17))
        if sample.world is None or not sample.world.repaired:
            print("MISMATCH: generated story did not resolve.")
            return 1
        return 0
    print("MISMATCH: ASP twin did not reach the repaired state.")
    return 1


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a bedtime story about {p.hero} recognizing a remote magical sound.",
        f"Tell a gentle story where {p.hero} and {p.helper} come closer carefully when {p.creature} calls.",
        f"Write a child-friendly tale using a {p.object_name}, sound effects, magic, and a moral value.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    c = world.calling
    return [
        QAItem(
            question=f"What did {p.hero} and {p.helper} hear?",
            answer=f"They heard {c.first_sound}. It came from a remote place and seemed to be a call.",
        ),
        QAItem(
            question="What clue helped them understand the sound?",
            answer=f"They noticed that {c.clue}. The repeated pattern showed that the sound had meaning.",
        ),
        QAItem(
            question="Why did the children come closer?",
            answer="They came closer carefully because they recognized that someone or something might need help.",
        ),
        QAItem(
            question="How was the problem repaired?",
            answer=f"They discovered that {c.cause}, and then they {c.repair}.",
        ),
        QAItem(
            question="What moral value did the story teach?",
            answer=c.lesson,
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to recognize something?",
            answer="To recognize something means to know or identify it because it seems familiar or its clues make sense.",
        ),
        QAItem(
            question="What does remote mean?",
            answer="Remote means far away or difficult to reach.",
        ),
        QAItem(
            question="Why should someone come closer carefully?",
            answer="Coming closer carefully helps a person learn more while staying safe and respectful.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are noises that help listeners imagine actions, places, or feelings, such as a chime, rustle, or whoosh.",
        ),
        QAItem(
            question="What is magic in a bedtime story?",
            answer="Magic is a wondrous power that makes an imagined story feel surprising and possible.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in [world.hero, world.helper, world.creature]:
        lines.append(f"{entity.kind}: {entity.name} meters={entity.meters} memes={entity.memes}")
    lines.append(
        "state: "
        f"recognized={world.recognized} came_closer={world.came_closer} "
        f"magic={world.magic_active} repaired={world.repaired}"
    )
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(seed=101, hero="Luna", helper="Milo", creature="the moon fox"),
    StoryParams(seed=202, hero="Nora", helper="Theo", creature="a sleepy starling"),
    StoryParams(seed=303, hero="Iris", helper="Pip", creature="the cloud shepherd"),
]


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
        print(asp_program("#show remote_call/0.\n#show recognized/0.\n#show came_closer/0.\n#show repaired/0.\n#show moral_value/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        if not _asp_available():
            print("ASP mode unavailable: clingo is not installed.")
            return
        import asp
        model = asp.one_model(asp_program())
        print("ASP model:", ", ".join(sorted(str(atom) for atom in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for offset in range(max(50, args.n * 20)):
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
            header = f"### {sample.params.hero} and {sample.params.helper}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
