#!/usr/bin/env python3
"""
A small whodunit-style storyworld about Curiosity, sympathy, quizzes, and an
approach to solving a puzzling little mystery.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Suspect:
    id: str
    label: str
    role: str
    clue: str
    alibi: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    atmosphere: str


@dataclass
class StoryParams:
    setting: str
    culprit: str
    detective: str
    witness: str
    quiz_topic: str
    approach: str
    seed: Optional[int] = None


SETTINGS = {
    "library": Setting(place="the library", atmosphere="quiet shelves and soft lamps"),
    "museum": Setting(place="the museum", atmosphere="bright rooms and careful footsteps"),
    "garden": Setting(place="the garden shed", atmosphere="damp air and scattered tools"),
    "kitchen": Setting(place="the kitchen", atmosphere="warm tiles and a humming kettle"),
}

SUSPECTS = {
    "cat": Suspect(
        id="cat",
        label="the sleepy cat",
        role="pet",
        clue="a pawprint on the quiz cards",
        alibi="it was napping on the sunny window ledge",
    ),
    "cook": Suspect(
        id="cook",
        label="the cook",
        role="helper",
        clue="a spoon left beside the quiz box",
        alibi="it was stirring soup the whole time",
    ),
    "child": Suspect(
        id="child",
        label="the little child",
        role="visitor",
        clue="a sticky ribbon on the quiz table",
        alibi="it was in the reading corner with a picture book",
    ),
    "gardener": Suspect(
        id="gardener",
        label="the gardener",
        role="worker",
        clue="muddy boots near the quiz stand",
        alibi="it was trimming hedges by the back gate",
    ),
}

DETECTIVES = [
    "Curiosity",
    "Mira",
    "Noel",
    "Pip",
    "Ada",
]

WITNESSES = [
    "the librarian",
    "the guide",
    "the neighbor",
    "the baker",
    "the janitor",
]

QUIZ_TOPICS = {
    "birds": "birds",
    "maps": "maps",
    "lanterns": "lanterns",
    "cookies": "cookies",
    "keys": "keys",
}

APPROACHES = {
    "ask": "asked gentle questions",
    "inspect": "looked closely at the clues",
    "compare": "compared the clue with the alibis",
    "follow": "followed the trail of small signs",
}


@dataclass
class World:
    setting: Setting
    detective: str
    witness: str
    culprit: Suspect
    quiz_topic: str
    approach: str
    entities: dict[str, Suspect] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"mystery": 0.0, "trust": 0.0, "certainty": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"curiosity": 0.0, "sympathy": 0.0, "unease": 0.0})
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

    def add_entity(self, suspect: Suspect) -> None:
        self.entities[suspect.id] = suspect


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit-style storyworld about curiosity, sympathy, and a quiz mystery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--culprit", choices=SUSPECTS)
    ap.add_argument("--detective", choices=DETECTIVES)
    ap.add_argument("--witness", choices=WITNESSES)
    ap.add_argument("--quiz-topic", choices=QUIZ_TOPICS)
    ap.add_argument("--approach", choices=APPROACHES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    culprit = args.culprit or rng.choice(list(SUSPECTS))
    detective = args.detective or rng.choice(DETECTIVES)
    witness = args.witness or rng.choice(WITNESSES)
    quiz_topic = args.quiz_topic or rng.choice(list(QUIZ_TOPICS))
    approach = args.approach or rng.choice(list(APPROACHES))

    if args.detective and args.detective == "Curiosity":
        pass

    if args.culprit == "cat" and setting == "museum":
        raise StoryError("The sleepy cat is not a good culprit for the museum story here.")
    if args.quiz_topic == "keys" and setting == "garden":
        raise StoryError("The keys quiz does not fit this garden mystery well enough.")

    return StoryParams(
        setting=setting,
        culprit=culprit,
        detective=detective,
        witness=witness,
        quiz_topic=quiz_topic,
        approach=approach,
    )


def _play(world: World) -> None:
    s = world.setting.place
    culprit = world.culprit
    world.memes["curiosity"] += 1
    world.meters["mystery"] += 1

    world.say(
        f"At {s}, {world.detective} arrived with a careful look and a notebook, "
        f"while {world.witness} pointed at the clue table under {world.setting.atmosphere}."
    )
    world.say(
        f"A small quiz had been set out about {QUIZ_TOPICS[world.quiz_topic]}, but one card was missing, "
        f"and that made everyone whisper."
    )
    world.para()

    world.say(
        f"{world.detective} {APPROACHES[world.approach]} and listened first. "
        f"{world.detective} also showed sympathy, because the missing card had worried the others."
    )
    world.memes["sympathy"] += 1
    world.meters["trust"] += 1

    world.say(
        f"Near the quiz box, there was {culprit.clue}. That clue did not fit the witness's story, "
        f"because {culprit.alibi}."
    )
    world.meters["certainty"] += 1

    world.para()
    world.say(
        f"Then {world.detective} asked the right quiz question, and the answer led to the truth: "
        f"{culprit.label} had not stolen anything at all; it had only brushed past the table while following crumbs."
    )
    world.say(
        f"The missing card had slipped under a chair, and {world.witness} found it at last."
    )
    world.say(
        f"The room grew calm, the quiz could begin, and everyone smiled when {world.detective} returned the card with a gentle apology."
    )

    world.facts.update(
        setting=world.setting.place,
        culprit=culprit.label,
        detective=world.detective,
        witness=world.witness,
        quiz_topic=world.quiz_topic,
        approach=world.approach,
        clue=culprit.clue,
        alibi=culprit.alibi,
        solved=True,
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    culprit = SUSPECTS[params.culprit]
    world = World(setting=setting, detective=params.detective, witness=params.witness, culprit=culprit, quiz_topic=params.quiz_topic, approach=params.approach)
    world.add_entity(culprit)
    _play(world)

    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a child-friendly whodunit set in {world.setting.place} where Curiosity solves a quiz mystery.",
        f"Tell a short mystery story with sympathy, a quiz, and an approach to finding out who caused the trouble.",
        f"Write a gentle detective tale where {world.detective} follows clues about {QUIZ_TOPICS[world.quiz_topic]}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.culprit
    return [
        QAItem(
            question="Who solved the mystery?",
            answer=f"{world.detective} solved it by using {world.approach} and staying curious.",
        ),
        QAItem(
            question="What was the missing thing in the story?",
            answer=f"The missing thing was a quiz card about {QUIZ_TOPICS[world.quiz_topic]}.",
        ),
        QAItem(
            question="What clue made the detective look more closely?",
            answer=f"The clue was {c.clue}, which did not match {c.alibi}.",
        ),
        QAItem(
            question="Why did the detective show sympathy?",
            answer="Because the missing card had made everyone worry, and the detective wanted to help gently instead of blaming anyone too quickly.",
        ),
        QAItem(
            question="Who turned out to be innocent?",
            answer=f"{c.label} turned out to be innocent; the story revealed that it had only brushed past the table while following crumbs.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to know more and keep asking careful questions.",
        ),
        QAItem(
            question="What does sympathy mean?",
            answer="Sympathy means caring about how someone feels and wanting to help them feel better.",
        ),
        QAItem(
            question="What is a quiz?",
            answer="A quiz is a set of questions that asks people to think and answer about a topic.",
        ),
        QAItem(
            question="What is an approach?",
            answer="An approach is the way someone begins a task or tries to solve a problem.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"setting={world.setting.place}")
    lines.append(f"detective={world.detective}")
    lines.append(f"witness={world.witness}")
    lines.append(f"culprit={world.culprit.label}")
    lines.append(f"quiz_topic={world.quiz_topic}")
    lines.append(f"approach={world.approach}")
    lines.append(f"meters={world.meters}")
    lines.append(f"memes={world.memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- fact(setting,S).
culprit(C) :- fact(culprit,C).
detected(S) :- fact(solved), fact(setting,S).
show_story(S,C) :- setting(S), culprit(C), detected(S).
#show show_story/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for key in SETTINGS:
        lines.append(asp.fact("fact", "setting", key))
    for key in SUSPECTS:
        lines.append(asp.fact("fact", "culprit", key))
    lines.append(asp.fact("fact", "solved"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program())
    atoms = asp.atoms(model, "show_story")
    if not atoms:
        print("MISMATCH: ASP twin did not derive a story.")
        return 1
    print("OK: ASP twin derived a story.")
    return 0


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="library", culprit="cat", detective="Curiosity", witness="the librarian", quiz_topic="birds", approach="inspect"),
    StoryParams(setting="museum", culprit="child", detective="Curiosity", witness="the guide", quiz_topic="maps", approach="compare"),
    StoryParams(setting="kitchen", culprit="cook", detective="Curiosity", witness="the baker", quiz_topic="cookies", approach="ask"),
]


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
        sys.exit(asp_verify())
    if args.asp:
        try:
            import storyworlds.asp as asp
        except Exception as err:
            raise SystemExit(str(err))
        model = asp.one_model(asp_program())
        print(f"{len(asp.atoms(model, 'show_story'))} ASP-derived story signature(s).")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective} at {p.setting} (culprit: {p.culprit}, topic: {p.quiz_topic})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
