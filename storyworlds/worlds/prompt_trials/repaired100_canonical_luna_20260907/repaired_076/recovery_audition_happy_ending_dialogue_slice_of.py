#!/usr/bin/env python3
"""A gentle Slice-of-Life StoryWorld about recovery and an audition."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    helper: str = "Mara"
    instrument: str = "violin"
    setting: str = "the community music room"
    challenge: str = "returning_after_illness"
    ending: str = "happy"
    variant: int = 0


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, key: str) -> Entity:
        return self.entities[key]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass(frozen=True)
class Challenge:
    key: str
    rehearsal: str
    problem: str
    clue: str
    temptation: str
    action: str
    dialogue: tuple[str, str]
    performance: str
    result: str
    lesson: str
    ending_image: str


CHALLENGES = (
    Challenge(
        "returning_after_illness",
        "Luna had missed several rehearsals while her body recovered",
        "the audition was only two days away",
        "her bow hand tired after one careful song",
        "hide the tired hand and practice until midnight",
        "made a smaller practice plan with Mara, resting between short songs",
        ("You do not have to prove everything today," Mara said.",
         "Then I can return one little step at a time," Luna replied.),
        "played the opening melody softly, then let the final note shine",
        "the listener heard both care and courage and invited Luna to join the beginner ensemble",
        "recovery is not a race; steady steps can lead back to music",
        "Luna placed her violin beside the warm tea while the new ensemble's music drifted through the hallway",
    ),
    Challenge(
        "lost_confidence",
        "Luna had recovered physically but still felt nervous about playing again",
        "the audition room looked larger than it had in her memory",
        "her stomach tightened whenever she imagined a wrong note",
        "pretend she was not scared and rush through the piece",
        "asked for one quiet minute, breathed with Mara, and chose the familiar song",
        ("What if I miss a note?" Luna asked.",
         "We will hear the whole song, not just one note," Mara said.),
        "began slowly and found the melody waiting under her fingers",
        "the teacher smiled and offered Luna a place in the relaxed afternoon group",
        "confidence can return through patient practice and honest words",
        "Luna walked home with the music folder under her arm and a lighter step",
    ),
    Challenge(
        "voice_recovery",
        "Luna's voice was almost ready after a long cold",
        "the audition asked for a short song and a spoken introduction",
        "her voice grew scratchy when she talked too long",
        "force every high note to sound perfect",
        "drank water, chose a comfortable song, and told the teacher what her voice could do that day",
        ("I can sing gently, but not loudly today," Luna said.",
         "Gently is still music," the teacher answered.),
        "sang the warm middle notes clearly and spoke her introduction with care",
        "the teacher invited Luna to return for a small singing circle",
        "honest limits can protect recovery while leaving room for joy",
        "A paper cup rested by the piano as Luna hummed the new circle's welcome song",
    ),
)


NAMES = ("Luna", "Nia", "Sora", "Mina")
HELPERS = ("Mara", "Auntie Jo", "Ben", "Tess")
INSTRUMENTS = ("violin", "flute", "piano", "guitar")
SETTINGS = (
    "the community music room",
    "the little arts center",
    "the library rehearsal room",
)
CHALLENGE_KEYS = tuple(item.key for item in CHALLENGES)


def challenge_for(key: str) -> Challenge:
    for challenge in CHALLENGES:
        if challenge.key == key:
            return challenge
    raise StoryError(f"unknown recovery challenge: {key}")


def build_world(params: StoryParams) -> World:
    if params.challenge not in CHALLENGE_KEYS:
        raise StoryError(f"unsupported challenge {params.challenge!r}")
    if params.ending != "happy":
        raise StoryError("this storyworld supports only the happy ending")
    world = World(params)
    child = world.add(Entity(
        id="child",
        kind="character",
        label=params.name,
        meters={"energy": 0.65, "confidence": 0.55},
        memes={"hope": 0.7, "belonging": 0.6},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        label=params.helper,
        meters={"patience": 1.0},
        memes={"care": 1.0},
    ))
    world.add(Entity(
        id="instrument",
        kind="instrument",
        label=f"the {params.instrument}",
        owner=child.id,
        meters={"readiness": 0.7},
        memes={"comfort": 0.8},
    ))
    world.facts.update(child=child.label, helper=helper.label, recovered=False)
    return world


def simulate(world: World) -> World:
    p = world.params
    child = world.get("child")
    instrument = world.get("instrument")
    challenge = challenge_for(p.challenge)

    world.say(
        f"On a quiet afternoon, {child.label} carried {instrument.label} "
        f"to {p.setting} for an audition."
    )
    world.say(
        f"{child.label} had been recovering, and the familiar instrument felt "
        f"like both a friend and a small question."
    )
    world.say(f"{challenge.rehearsal}.")
    world.para()

    world.say(f"At the first practice, {challenge.problem}.")
    world.say(f"The important clue was that {challenge.clue}.")
    world.say(f"For a moment, it seemed tempting to {challenge.temptation}.")
    world.say("But recovery needed kindness more than a brave-looking shortcut.")
    world.para()

    world.say(f"{p.helper} sat beside {child.label}.")
    world.say(f"“{challenge.dialogue[0]}”")
    world.say(f"“{challenge.dialogue[1]}”")
    world.say(f"Together, they {challenge.action}.")
    world.say(
        f"The short plan gave {child.label} room to notice how the body felt "
        "instead of turning the audition into a test of toughness."
    )
    world.para()

    world.say(f"At the audition, {challenge.performance}.")
    world.say(
        f"{challenge.result.capitalize()}. "
        f"{child.label} did not need to be exactly as strong as before; "
        "being present and honest was enough for that day."
    )
    world.say(f"{challenge.lesson.capitalize()}.")
    world.say(challenge.ending_image)

    child.meters.update(energy=0.82, confidence=0.88)
    child.memes.update(hope=1.0, belonging=0.95)
    instrument.meters["readiness"] = 0.9
    world.fired.update({"paused", "spoke_honestly", "rested", "auditioned", "recovered"})
    world.facts.update(
        challenge=challenge.key,
        problem=challenge.problem,
        clue=challenge.clue,
        action=challenge.action,
        result=challenge.result,
        lesson=challenge.lesson,
        audition=True,
        recovery_plan_used=True,
        happy_ending=True,
        recovered=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    challenge = challenge_for(p.challenge)
    return [
        f"Write a Slice-of-Life story about {p.name}'s recovery before an audition with a {p.instrument}.",
        f"Show how the clue '{challenge.clue}' changes the plan.",
        "Include a brief back-and-forth dialogue and end with a concrete happy image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    challenge = challenge_for(p.challenge)
    return [
        QAItem(
            question=f"Why was {p.name} worried about the audition?",
            answer=f"{p.name} was worried because {challenge.problem}, and {challenge.clue}.",
        ),
        QAItem(
            question="What tempting choice did the character reject?",
            answer=f"The tempting choice was to {challenge.temptation}, but that could have made recovery harder.",
        ),
        QAItem(
            question=f"How did {p.name} and {p.helper} prepare?",
            answer=f"They {challenge.action}. Their smaller plan respected recovery while keeping the audition possible.",
        ),
        QAItem(
            question="What did the dialogue change?",
            answer=f"{p.name} admitted a real worry, and the reply helped {p.name} choose a patient, familiar approach instead of rushing.",
        ),
        QAItem(
            question="What happened at the audition?",
            answer=f"{challenge.result.capitalize()} {p.name} performed honestly and stayed within the day's limits.",
        ),
        QAItem(
            question="What final image shows the happy ending?",
            answer=f"{challenge.ending_image}. The image shows that recovery and music could continue together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does recovery mean in this story?",
            answer="Recovery means gradually returning to an activity while noticing the body's needs and allowing time, rest, and support.",
        ),
        QAItem(
            question="Why can a smaller practice plan help?",
            answer="A smaller plan can conserve energy, make warning signs easier to notice, and build confidence without forcing a person to overdo an activity.",
        ),
        QAItem(
            question="Why is honest dialogue useful before an audition?",
            answer="Honest dialogue lets a performer explain what feels possible, so a trusted helper or teacher can adjust expectations and support a safe choice.",
        ),
        QAItem(
            question="Does a happy audition require a perfect performance?",
            answer="No. A happy ending can come from participating honestly, caring for recovery, and finding a welcoming next step.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


ASP_RULES = """auditioner(X) :- recovery_plan_used(X), audition(X).
ready(X) :- auditioner(X), rested(X), spoke_honestly(X).
happy(X) :- ready(X), invited_back(X).
"""


def asp_facts(params: Optional[StoryParams] = None) -> str:
    import asp

    atom = (params or StoryParams()).name.lower()
    facts = (
        ("recovery_plan_used", atom),
        ("audition", atom),
        ("rested", atom),
        ("spoke_honestly", atom),
        ("invited_back", atom),
    )
    return "\n".join(asp.fact(name, value) for name, value in facts)


def asp_program(show: str, params: Optional[StoryParams] = None) -> str:
    return f"{asp_facts(params)}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    symbols = asp.one_model(asp_program("#show happy/1."))
    found = set(asp.atoms(symbols, "happy"))
    if not found:
        print("ASP verification failed.")
        return 1
    print("OK: ASP twin confirms patient recovery can lead to a happy audition.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Slice-of-Life recovery and audition StoryWorld."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--instrument", choices=INSTRUMENTS)
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--challenge", choices=CHALLENGE_KEYS)
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
    return StoryParams(
        seed=args.seed,
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        instrument=args.instrument or rng.choice(INSTRUMENTS),
        setting=args.setting or rng.choice(SETTINGS),
        challenge=args.challenge or rng.choice(CHALLENGE_KEYS),
        ending="happy",
        variant=rng.randrange(1, 2**31),
    )


def generate(params: StoryParams) -> StorySample:
    world = simulate(build_world(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world is not None:
        print(f"\n--- trace ---\nfacts: {sample.world.facts}")
        print(f"fired: {sorted(sample.world.fired)}")
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy/1."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import asp

        symbols = asp.one_model(asp_program("#show happy/1."))
        print("\n".join(str(symbol) for symbol in symbols))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [
            generate(
                StoryParams(
                    name="Luna",
                    helper="Mara",
                    instrument="violin",
                    setting="the community music room",
                    challenge=key,
                    ending="happy",
                    variant=index + 17,
                )
            )
            for index, key in enumerate(CHALLENGE_KEYS)
        ]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1")
        samples = [
            generate(resolve_params(args, random.Random(base_seed + index)))
            for index in range(args.n)
        ]

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps(
                [sample.to_dict() for sample in samples],
                indent=2,
                ensure_ascii=False,
            ))
        return

    for index, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {index + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
