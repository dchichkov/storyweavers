#!/usr/bin/env python3
"""
A gentle bedtime-story world about a furry friend, sound effects, and an
annotated picture book that helps a sleepy listener find a lost goodnight song.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    listener: str = "Milo"
    companion: str = "Fuzz"
    place: str = "the little attic bedroom"
    book: str = "The Moonlit Meadow"
    sound: str = "a soft chime"
    task: str = "finish the bedtime story"


@dataclass(frozen=True)
class Trouble:
    title: str
    problem: str
    mistaken_belief: str
    clue: str
    failed_attempt: str
    cause: str
    companion_job: str
    hero_job: str
    repair: str
    lesson: str
    ending: str


TROUBLES = [
    Trouble(
        "The Missing Whisper",
        "the final page of the bedtime book had lost its whispering sound effect",
        "Milo believed the story could not end without that exact sound",
        "a pencil mark curled beside the moon picture",
        "they tried three loud noises, but each one made Milo sit up wider awake",
        "Luna had written the sound effect in the margin, then tucked the page beneath a pillow",
        "followed the pencil trail around the rug and under the blanket",
        "read the annotated margin and chose a quiet breathy 'whoosh'",
        "returned the page, read the last lines softly, and added the missing sound beside the moon",
        "A gentle sound can be found by careful looking, not by making the room louder.",
        "the book closed with a tiny 'whoosh' while sleepy eyes folded shut",
    ),
    Trouble(
        "The Noisy Night",
        "a sudden 'CLANG!' startled everyone just before the goodnight page",
        "Milo thought the moon in the story had fallen from the sky",
        "the annotation beside the picture said 'turn the silver bell slowly'",
        "they shook the bell again, which made an even bigger clang",
        "the bell was being swung instead of tipped gently with one finger",
        "demonstrated a slow touch and placed a cushion beneath the bell",
        "read the annotation aloud and tried the sound at whisper volume",
        "changed the note to 'tip softly: ting'",
        "Instructions can turn a startling noise into a peaceful one.",
        "the silver bell gave one small 'ting' and rested beside the closed book",
    ),
    Trouble(
        "The Fur on the Page",
        "a tuft of furry fluff covered the sound-effect words",
        "Luna thought the story had lost its magic sounds forever",
        "the fluff was warm and shaped like the sleeping companion's tail",
        "they brushed the page quickly and smudged one tiny star",
        "Fuzz had curled on the open book while dreaming",
        "lifted the fluff gently and fetched a soft brush",
        "copied the clear sound words onto a fresh bookmark",
        "made a bookmark that read 'rustle, hush, twinkle' in neat letters",
        "Careful hands protect stories when sleepy accidents happen.",
        "the furry bookmark rested in the book while Fuzz dreamed beside it",
    ),
    Trouble(
        "The Wrong Rustle",
        "a rustling sound came from the story basket instead of the moon meadow",
        "Milo believed a night creature was hiding inside",
        "the annotation showed a bent paper corner near the basket's loose ribbon",
        "they peeked inside with a lamp and scattered the picture cards",
        "the ribbon was brushing the basket whenever the window breeze moved it",
        "held the basket steady and tied the ribbon into a quiet bow",
        "read the page's real 'rustle' sound with the window safely closed",
        "marked the ribbon as a decoration rather than a story sound",
        "Checking the source of a sound can make a frightening guess feel small.",
        "the basket made no more noise except for one friendly paper 'rustle'",
    ),
    Trouble(
        "The Sleepy Smudge",
        "a blue ink smudge hid the note for the final sound effect",
        "Milo thought Luna had forgotten how the story ended",
        "the smudge stopped exactly before the word 'hush'",
        "they guessed different endings and kept turning the same page",
        "a damp cup had rested on the annotation",
        "placed the page beneath a clean cloth and read the visible letters",
        "remembered that the picture itself showed a quiet sleeping owl",
        "wrote 'hush' beside the owl after the page dried",
        "When a message is unclear, patient clues are better than impatient guesses.",
        "the owl's page ended with a shared, peaceful 'hush'",
    ),
    Trouble(
        "The Wandering Bookmark",
        "the annotated bookmark was missing from the bedtime book",
        "Luna believed the bookmark had been carried away by a dream",
        "a trail of silver stars led toward the pillow basket",
        "they searched every shelf while the bedtime lamp grew dim",
        "Fuzz had moved the bookmark to make a soft nest",
        "followed the stars and asked Fuzz to move gently",
        "read the sound effects from the recovered bookmark",
        "folded a cloth pocket into the cover for the bookmark",
        "A lost thing may have a simple home when we look with care.",
        "the bookmark slept in its new pocket as quietly as everyone else",
    ),
    Trouble(
        "The Echoing Room",
        "the sound effect 'tap, tap' echoed around the room",
        "Milo thought someone outside was answering the story",
        "the annotation pointed toward the bare wooden wall",
        "they tapped faster and made the echo louder",
        "the wall was reflecting the sound because a curtain had been pulled aside",
        "hung the curtain and tested one gentle tap",
        "changed the sound effect to a soft fingertip pat",
        "closed the curtain and placed a rug beneath the reading chair",
        "A small change in the room can help a sound become kind and quiet.",
        "one soft 'pat' faded into the warm hush of bedtime",
    ),
    Trouble(
        "The Unheard Chime",
        "the little chime made no sound during the starry page",
        "Luna believed the bedtime magic had disappeared",
        "the annotation showed a felt cover wrapped around the chime",
        "they struck it harder, but the covered note stayed dull",
        "the felt cover was meant for storing the chime, not playing it",
        "removed the cover and held the chime by its wooden handle",
        "rang it once, then placed it far enough away to stay gentle",
        "added a drawing showing when the cover belonged on the chime",
        "Good tools need the right use, and gentle testing can reveal it.",
        "the uncovered chime sang one clear 'ting' before the lamp dimmed",
    ),
    Trouble(
        "The Backward Ending",
        "the last three annotated sounds were written in the wrong order",
        "Milo thought the moon meadow was supposed to wake up instead of sleep",
        "the page numbers showed 'rustle' before 'hush' and 'hush' before 'dream'",
        "they read the sounds backward and ended with a surprising bang",
        "the pages had been stacked in reverse after a daytime craft",
        "sorted the pages by their small silver numbers",
        "read the corrected order slowly from top to bottom",
        "added a moon sticker to the front of the page stack",
        "An orderly sequence helps a story arrive safely at its ending.",
        "rustle, hush, and dream followed one another beneath the moon sticker",
    ),
]

OPENINGS = [
    "When the first stars appeared",
    "At the quiet edge of evening",
    "Beneath a round and sleepy moon",
    "After the last cup was washed",
    "In a little room warmed by lamplight",
    "When the garden shadows grew long",
    "Just as the sky turned deep blue",
    "At the gentle beginning of night",
]

DIALOGUE = [
    "What does the page really show?",
    "Let us listen softly and look closely.",
    "Could the note be telling us how to help?",
    "We can solve this without waking the whole house.",
    "Tell me what you noticed, and I will tell you what I noticed.",
    "A quiet test may give us the answer.",
]

TEAMWORK = [
    "They divided the work: one held the book while the other followed the marks.",
    "They made a tiny plan and checked each step in a whisper.",
    "They listened first, then placed every clue beside the matching picture.",
    "They worked slowly so the sleepy room could remain peaceful.",
    "They compared the page, the sound, and the object before deciding.",
]

PERSPECTIVES = [
    "Milo remembered that the softest solution had been the bravest one.",
    "Luna kept the annotated page open until everyone understood the ending.",
    "Fuzz curled nearby, pleased that even furry paws could help carefully.",
    "The little room seemed calmer because every sound now had a gentle place.",
    "The next night, they began by checking the notes before touching the sound effects.",
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
    listener: Entity
    companion: Entity
    trouble: Trouble
    worried: bool = False
    understood: bool = False
    repaired: bool = False
    sound_effect_used: bool = False
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world of furry friends and sound effects.")
    ap.add_argument("--hero")
    ap.add_argument("--listener")
    ap.add_argument("--companion")
    ap.add_argument("--place")
    ap.add_argument("--book")
    ap.add_argument("--sound")
    ap.add_argument("--task")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        hero=args.hero or rng.choice(["Luna", "Nora", "Ari", "Sage"]),
        listener=args.listener or rng.choice(["Milo", "Tess", "Pip", "Eli"]),
        companion=args.companion or rng.choice(["Fuzz", "Mittens", "Bramble", "Cloud"]),
        place=args.place or rng.choice([
            "the little attic bedroom",
            "the room beside the moonlit garden",
            "a cozy corner under the stairs",
        ]),
        book=args.book or rng.choice([
            "The Moonlit Meadow",
            "The Owl Who Counted Stars",
            "The Sleepy Forest",
        ]),
        sound=args.sound or rng.choice(["a soft chime", "a tiny bell", "a whispering shaker"]),
        task=args.task or "finish the bedtime story",
    )


def _validate(params: StoryParams) -> None:
    if not params.hero.strip() or not params.listener.strip() or not params.companion.strip():
        raise StoryError("The bedtime story needs a hero, a listener, and a furry companion.")
    if not params.book.strip() or not params.place.strip():
        raise StoryError("The bedtime story needs a book and a peaceful place.")
    forbidden = {"poison", "weapon", "war", "dangerous"}
    if any(word in params.book.lower() for word in forbidden):
        raise StoryError("The bedtime book must be gentle enough for sleepy listeners.")


def _stable_rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0xB37D91)
    key = "|".join([
        params.hero, params.listener, params.companion, params.place,
        params.book, params.sound, params.task,
    ])
    return random.Random(int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big"))


def _setup(world: World, opening: str) -> None:
    p = world.params
    world.say(
        f"{opening}, {p.hero} settled beside {p.listener} in {p.place}. "
        f"A furry friend named {p.companion} curled on the rug, warm as a little cloud."
    )
    world.say(
        f"They were ready to {p.task} by reading {p.book}. Luna had added annotations in the margins "
        f"so every sound effect would be soft enough for bedtime."
    )


def _trouble(world: World) -> None:
    t = world.trouble
    world.para()
    world.worried = True
    world.listener.add_meme("worry", 1)
    world.hero.add_meme("patience", 1)
    world.companion.add_meme("curiosity", 1)
    world.say(f"Then came {t.title}. {t.problem.capitalize()}.")
    world.say(f"In the sleepy confusion, {t.mistaken_belief}.")
    world.say(f"At first, {t.failed_attempt}. The room felt less and less ready for dreams.")


def _turn(world: World, question: str, teamwork: str) -> None:
    p = world.params
    t = world.trouble
    world.para()
    world.understood = True
    world.hero.add_meme("resolve", 1)
    world.listener.add_meme("curiosity", 1)
    world.say(f'{p.hero} whispered to {p.listener}, "{question}"')
    world.say(f"{teamwork} They followed the annotation and found this clue: {t.clue}.")
    world.say(f"That clue revealed the real cause: {t.cause}.")
    world.say(
        f"{p.companion} {t.companion_job}; {p.hero} {t.hero_job}. "
        f"{p.listener} watched closely and learned why the sound needed to stay gentle."
    )


def _resolution(world: World, perspective: str) -> None:
    p = world.params
    t = world.trouble
    world.para()
    world.repaired = True
    world.sound_effect_used = True
    world.say(f"Their quiet teamwork worked: they {t.repair}.")
    world.say(
        f"At last, {p.hero} read the final page of {p.book}. The sound effect was no louder "
        f"than a breath, and {p.companion}'s furry tail made a soft circle on the rug."
    )
    world.say(f"{p.listener} smiled and said, '{t.lesson}'")
    world.say(f"When the bedtime story ended, {t.ending}. {perspective} Then the lamp went dark.")


def tell(params: StoryParams) -> World:
    _validate(params)
    world = World(
        params=params,
        hero=Entity(params.hero, "hero"),
        listener=Entity(params.listener, "listener"),
        companion=Entity(params.companion, "furry companion"),
        trouble=Troubles := TROUBLES[0],
    )
    rng = _stable_rng(params)
    world.trouble = rng.choice(TROUBLES)
    _setup(world, rng.choice(OPENINGS))
    _trouble(world)
    _turn(world, rng.choice(DIALOGUE), rng.choice(TEAMWORK))
    _resolution(world, rng.choice(PERSPECTIVES))
    world.facts = {
        "hero": params.hero,
        "listener": params.listener,
        "companion": params.companion,
        "place": params.place,
        "book": params.book,
        "sound": params.sound,
        "trouble": world.trouble.title,
        "problem": world.trouble.problem,
        "clue": world.trouble.clue,
        "cause": world.trouble.cause,
        "repair": world.trouble.repair,
        "lesson": world.trouble.lesson,
        "ending": world.trouble.ending,
        "worried": world.worried,
        "understood": world.understood,
        "repaired": world.repaired,
    }
    return world


ASP_RULES = r"""
hero(X) :- hero_name(X).
listener(X) :- listener_name(X).
furry_companion(X) :- companion_name(X).
worried :- missing_sound.
understood :- annotated_clue, listens(hero, listener).
repaired :- understood, gentle_sound, furry_companion(companion).
#show worried/0.
#show understood/0.
#show repaired/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero_name", "luna"),
        asp.fact("listener_name", "milo"),
        asp.fact("companion_name", "fuzz"),
        asp.fact("missing_sound"),
        asp.fact("annotated_clue"),
        asp.fact("listens", "hero", "listener"),
        asp.fact("gentle_sound"),
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
    actual = {str(atom) for atom in model}
    expected = {"worried", "understood", "repaired"}
    if expected.issubset(actual):
        sample = generate(StoryParams(seed=17))
        if not sample.story or not sample.story_qa:
            print("MISMATCH: generated story verification failed.")
            return 1
        print("OK: ASP and Python bedtime states agree.")
        return 0
    print("MISMATCH: ASP did not reach the repaired bedtime state.")
    return 1


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a gentle bedtime story about {p.hero}, {p.listener}, and furry {p.companion}.",
        f"Include sound effects and annotations in a story set in {p.place}.",
        f"Tell how a small bedtime problem is solved through careful listening and quiet teamwork.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    t = world.trouble
    return [
        QAItem(
            question=f"What problem interrupted {p.hero}'s bedtime story?",
            answer=f"{t.problem.capitalize()}. This made the bedtime reading confusing or startling.",
        ),
        QAItem(
            question="What clue helped the characters understand the problem?",
            answer=f"They noticed that {t.clue}. The annotation helped them follow a real clue instead of guessing.",
        ),
        QAItem(
            question=f"How did {p.companion} help?",
            answer=f"{p.companion} {t.companion_job}. The furry companion took part in the quiet repair.",
        ),
        QAItem(
            question="What did the characters learn?",
            answer=t.lesson,
        ),
        QAItem(
            question="How could readers tell the problem was solved?",
            answer=f"At the end, {t.ending}. The gentle sound and peaceful room showed that bedtime was safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a written or performed sound that helps people imagine what is happening in a story.",
        ),
        QAItem(
            question="What does it mean to annotate a book?",
            answer="To annotate a book means to add helpful notes, marks, or explanations beside the words or pictures.",
        ),
        QAItem(
            question="Why should bedtime sounds be gentle?",
            answer="Gentle sounds help listeners enjoy the story without startling them or making it harder to fall asleep.",
        ),
        QAItem(
            question=f"What is a furry companion?",
            answer=f"A furry companion is a soft animal friend, such as {p.companion}, who can offer comfort and company.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people and friends share helpful jobs to solve a problem together.",
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
    for entity in [world.hero, world.listener, world.companion]:
        lines.append(f"{entity.kind}: {entity.name} meters={entity.meters} memes={entity.memes}")
    lines.append(
        f"state: worried={world.worried} understood={world.understood} "
        f"repaired={world.repaired} sound_effect_used={world.sound_effect_used}"
    )
    return "\n".join(lines)


CURATED = [
    StoryParams(seed=101, hero="Luna", listener="Milo", companion="Fuzz"),
    StoryParams(seed=202, hero="Nora", listener="Tess", companion="Mittens"),
    StoryParams(seed=303, hero="Ari", listener="Eli", companion="Bramble"),
]


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
        print(asp_program("#show worried/0.\n#show understood/0.\n#show repaired/0."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

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
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            seed = base_seed + index
            index += 1
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
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.listener} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
