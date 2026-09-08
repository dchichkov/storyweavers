#!/usr/bin/env python3
"""The Famous Author and the Careful Reader.

A small fable about fame, analysis, and the quiet work of an author.
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
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    label: str
    kind: str = "thing"
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Luna"
    author: str = "Ari"
    subject: str = "fame"
    method: str = "careful_analysis"
    seed: int = 777


PROMPT = (
    "Write a fable about Luna learning that a famous author needs a careful "
    "reader, using dialogue and an inner monologue."
)

HERO_NAMES = ("Luna", "Mira", "Nia", "Tess", "Pia")
AUTHOR_NAMES = ("Ari", "Eli", "Oren", "Sage", "Ivo")
SUBJECTS = {
    "fame": ("fame", "a golden bell", "A name may ring loudly and still need a true listener."),
    "courage": ("courage", "a red thread", "A brave heart can tremble and still take one step."),
    "kindness": ("kindness", "a warm loaf", "A small kindness grows when it is passed along."),
}
METHODS = ("careful_analysis", "quick_guess")


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(
        self,
        kind: str,
        text: str,
        *,
        question: str = "",
        cause: str = "",
        result: str = "",
    ):
        self.history.append(
            Event(
                kind=kind,
                text=text,
                question=question,
                cause=cause,
                result=result,
                state=self.snapshot(),
            )
        )

    def speak(self, speaker: str, text: str):
        self.history.append(
            Event(kind="speech", text=f'{self.entities[speaker].label} said, "{text}"',
                  state=self.snapshot())
        )

    def think(self, speaker: str, text: str):
        self.history.append(
            Event(kind="inner_monologue",
                  text=f"{self.entities[speaker].label} thought, “{text}”",
                  state=self.snapshot())
        )


def validate_params(params: StoryParams):
    if params.hero == params.author:
        raise StoryError("The reader and author must have different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name)
           for name in (params.hero, params.author)):
        raise StoryError("Names must be simple capitalized words, such as Luna and Ari.")
    if params.subject not in SUBJECTS:
        raise StoryError("Unknown fable subject.")
    if params.method not in METHODS:
        raise StoryError("Unknown reading method.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    subject, object_name, moral = SUBJECTS[params.subject]
    world.entities["hero"] = Entity(
        id="hero",
        label=params.hero,
        kind="reader",
        location="hilltop garden",
        meters={"attention": 0.4, "understanding": 0.0},
        memes={"pride": 0.7, "patience": 0.3},
    )
    world.entities["author"] = Entity(
        id="author",
        label=params.author,
        kind="author",
        location="hilltop garden",
        meters={"fame": 1.0, "story_truth": 0.0},
        memes={"hope": 0.6, "humility": 0.4},
    )
    world.entities["fable"] = Entity(
        id="fable",
        label=f"the fable about {subject}",
        kind="story",
        location="stone bench",
        meters={"clues_found": 0, "meaning_found": 0, "read_aloud": 0},
        memes={"moral": 0.0},
    )
    world.entities["symbol"] = Entity(
        id="symbol",
        label=object_name,
        kind="symbol",
        location="inside the fable",
        meters={"noticed": 0},
    )
    world.entities["moral"] = Entity(
        id="moral",
        label="the lesson",
        kind="idea",
        location="not yet spoken",
        meters={"shared": 0},
    )
    return world


def check_ending(world: World):
    fable = world.entities["fable"]
    moral = world.entities["moral"]
    hero = world.entities["hero"]
    author = world.entities["author"]
    if fable.meters["clues_found"] < 2:
        raise StoryError("The reader must notice enough story clues.")
    if fable.meters["meaning_found"] != 1:
        raise StoryError("The fable's meaning must be discovered.")
    if moral.meters["shared"] != 1:
        raise StoryError("The meaning must be shared aloud.")
    if fable.meters["read_aloud"] != 1:
        raise StoryError("The story must be read aloud at the ending.")
    if hero.memes["patience"] < 1 or author.memes["humility"] < 1:
        raise StoryError("The final lesson has not changed both characters.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.entities["hero"]
    author = world.entities["author"]
    fable = world.entities["fable"]
    symbol = world.entities["symbol"]
    moral = world.entities["moral"]
    h, a = hero.label, author.label
    subject, object_name, lesson = SUBJECTS[params.subject]

    world.narrate(
        "beginning",
        f"{h} climbed the hilltop garden carrying a notebook. "
        f"There sat {a}, a famous author, beside a fable about {subject}.",
    )
    world.speak("hero", f"May I analyze your new fable?")
    world.speak("author", "You may, but please read it as carefully as you read my name.")
    world.think(
        "hero",
        f"{a} is famous, so the answer must be grand. I will find something grand.",
    )

    world.speak("hero", f"The fable must be about being famous. Everyone knows your stories.")
    world.speak("author", "That is a quick guess. What happens inside the story?")
    if params.method == "quick_guess":
        hero.memes["pride"] += 0.2
        world.speak("hero", "The title and your name are enough clues for me.")
        world.think(
            "hero",
            "Perhaps a famous author does not need to explain anything to a reader like me.",
        )
        world.narrate(
            "misread",
            f"{h} hurried past the fable's small details and pointed only at {a}'s fame.",
            question="Why did Luna misunderstand the fable?",
            cause=f"{h} guessed from the author's fame instead of examining the story's clues.",
            result="The important meaning remained hidden.",
        )
    else:
        world.speak("hero", "I will look at the story before I decide.")
        world.think(
            "hero",
            "A name can glitter, but a story leaves footprints. I should follow those.",
        )
        world.narrate(
            "promise",
            f"{h} opened the fable and placed the notebook beneath the page.",
            question="What did Luna decide to do before judging the fable?",
            cause=f"{h} chose to analyze the story's details rather than rely on {a}'s fame.",
            result="The reader began looking for clues inside the fable.",
        )

    world.speak("author", f"Then notice what the {object_name} does.")
    world.speak("hero", f"It appears whenever the story changes.")
    symbol.meters["noticed"] = 1
    fable.meters["clues_found"] += 1
    world.narrate(
        "first_clue",
        f"{h} noticed that {object_name} appeared beside every difficult choice in the fable.",
        question="What was the first clue Luna noticed?",
        cause=f"The {object_name} appeared whenever the story's choice changed.",
        result=f"{h} marked the {object_name} as an important clue.",
    )

    world.speak("author", "And what do the characters do when nobody praises them?")
    world.speak("hero", "They keep helping one another, even in the quiet parts.")
    fable.meters["clues_found"] += 1
    hero.memes["patience"] = 0.8
    world.narrate(
        "second_clue",
        f"{h} read the quiet middle again. The characters helped each other when no crowd was watching.",
        question="What second clue helped Luna understand the fable?",
        cause="The characters continued helping even when nobody praised them.",
        result=f"{h} saw that the fable cared about deeds, not applause.",
    )

    world.think(
        "hero",
        f"The {object_name} is not a crown. It points to the choice, and the quiet help gives that choice its meaning.",
    )
    world.speak("hero", f"I think the fable says that {lesson[0].lower()}.")
    world.speak("author", "You have found its heart. Can you say the lesson in your own words?")
    world.speak(
        "hero",
        f"Being {subject} is not about a loud name. It is about what someone does when no one is clapping.",
    )
    fable.meters["meaning_found"] = 1
    moral.location = "spoken between the reader and author"
    moral.meters["shared"] = 1
    author.meters["story_truth"] = 1
    author.memes["humility"] = 1.0
    hero.memes["patience"] = 1.0
    world.narrate(
        "turn",
        f"{a} bowed to the notebook, and {h} understood that even a famous author could need a careful reader.",
        question="How did Luna discover the fable's meaning?",
        cause=f"{h} connected the recurring {object_name} with the characters' quiet helpfulness.",
        result="The reader understood that true worth comes from actions, not applause.",
    )

    world.speak("author", "Will you read the fable aloud now?")
    world.speak("hero", "Yes. I will let every small clue have a voice.")
    fable.meters["read_aloud"] = 1
    world.narrate(
        "ending",
        f"{h} read the fable aloud beneath the trees. The famous author's name still shone, "
        f"but the little {object_name} shone brighter in the story.",
        question="What changed at the end of the story?",
        cause=f"{h} read the fable aloud after understanding its small clues.",
        result=f"The author and reader valued the fable's meaning more than fame alone.",
    )

    sample = StorySample(
        params=params,
        story="\n\n".join(event.text for event in world.history),
        prompts=[PROMPT],
        story_qa=[
            QAItem(question=event.question, answer=f"{event.cause} {event.result}")
            for event in world.history
            if event.question
        ],
        world_qa=[
            QAItem(
                question="What does an author do?",
                answer="An author creates stories and chooses details that can carry meaning.",
            ),
            QAItem(
                question="Why should a reader analyze a story?",
                answer="A reader can analyze a story to notice clues and understand what its characters and events mean.",
            ),
            QAItem(
                question="What is the fable's general lesson about fame?",
                answer="Fame can make a name loud, but careful actions and true understanding matter more.",
            ),
        ],
        world=world,
    )
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    check_ending(sample.world)
    speech = [event for event in sample.world.history if event.kind == "speech"]
    thoughts = [event for event in sample.world.history if event.kind == "inner_monologue"]
    if len(speech) < 10:
        raise StoryError("The story needs a sustained exchange of dialogue.")
    if not thoughts:
        raise StoryError("The story must include an inner monologue.")
    if len(sample.story_qa) < 4:
        raise StoryError("The story needs grounded questions and answers.")
    if any(not item.answer.strip() for item in sample.story_qa):
        raise StoryError("Every story question needs a natural answer.")


ASP_RULES = """
clue(symbol).
clue(quiet_deed).
meaning(actions_over_applause).
understood(X) :- clue(symbol), clue(quiet_deed), meaning(X).
shared(X) :- understood(X).
valid_story :- shared(actions_over_applause).
#show valid_story/0.
#show understood/1.
#show shared/1.
"""


def asp_facts() -> str:
    from asp import fact

    return "\n".join(
        [
            fact("clue", "symbol"),
            fact("clue", "quiet_deed"),
            fact("meaning", "actions_over_applause"),
        ]
    )


def asp_state() -> set[tuple]:
    from asp import atoms, one_model

    symbols = one_model(asp_facts() + "\n" + ASP_RULES)
    return {
        ("valid_story",),
        *{("understood", value) for value in atoms(symbols, "understood")},
        *{("shared", value) for value in atoms(symbols, "shared")},
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--author")
    parser.add_argument("--subject", choices=tuple(SUBJECTS))
    parser.add_argument("--method", choices=METHODS)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HERO_NAMES)
    author = args.author or rng.choice([name for name in AUTHOR_NAMES if name != hero])
    params = StoryParams(
        hero=hero,
        author=author,
        subject=args.subject or rng.choice(tuple(SUBJECTS)),
        method=args.method or rng.choice(METHODS),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if asp_state() != {
        ("valid_story",),
        ("understood", "actions_over_applause"),
        ("shared", "actions_over_applause"),
    }:
        raise StoryError("Python and ASP disagree about the fable's reasoning.")
    tested = 0
    for subject in SUBJECTS:
        for method in METHODS:
            sample = generate(
                StoryParams(hero="Luna", author="Ari", subject=subject, method=method)
            )
            check_sample(sample)
            tested += 1
    print(f"OK: {tested} story states; ASP/Python reasoning agrees.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = ""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(
            json.dumps(
                {
                    "entities": sample.world.snapshot(),
                    "history": [asdict(event) for event in sample.world.history],
                },
                ensure_ascii=False,
                indent=2,
            )
        )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.n < 1:
            raise StoryError("-n must be positive.")
        if args.show_asp:
            print(asp_facts() + "\n" + ASP_RULES)
            return 0
        if args.verify:
            verify()
            return 0
        if args.asp:
            print(json.dumps(sorted(asp_state()), ensure_ascii=False))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            combinations = [
                (subject, method)
                for subject in SUBJECTS
                for method in METHODS
                if args.subject is None or subject == args.subject
                if args.method is None or method == args.method
            ]
            if not combinations:
                raise StoryError("No combinations match the selected options.")
            params_list = [
                StoryParams(
                    hero=args.hero or "Luna",
                    author=args.author or "Ari",
                    subject=subject,
                    method=method,
                    seed=args.seed,
                )
                for subject, method in combinations
            ]
            for params in params_list:
                validate_params(params)
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(
                json.dumps(
                    payload[0] if len(payload) == 1 else payload,
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            for index, sample in enumerate(samples):
                emit(
                    sample,
                    trace=args.trace,
                    qa=args.qa,
                    header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
