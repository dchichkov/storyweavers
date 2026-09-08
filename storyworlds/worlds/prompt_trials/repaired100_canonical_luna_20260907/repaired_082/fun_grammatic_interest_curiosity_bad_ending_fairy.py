#!/usr/bin/env python3
"""
A small fairy-tale storyworld about Luna's curiosity, a grammatic puzzle,
and a bad ending that teaches a careful lesson.
"""

from __future__ import annotations

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

    def pronoun(self, case: str = "subject") -> str:
        if self.kind in {"girl", "fairy", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

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


@dataclass(frozen=True)
class Incident:
    title: str
    riddle: str
    warning: str
    tempting_action: str
    consequence: str
    clue: str
    repair: str
    lesson: str
    ending: str


INCIDENTS = [
    Incident(
        "the silver sentence",
        "Which little word joins two thoughts without changing either one?",
        "the silver sentence was still being checked by the moon librarian",
        "rubbed the glittering word from the page before asking anyone",
        "The two thoughts broke apart, and the castle's friendly directions became nonsense.",
        "a tiny silver comma lay under Luna's shoe, exactly where the missing pause had been",
        "told the librarian the truth and helped copy the sentence carefully onto a fresh scroll",
        "curiosity is bright, but questions should come before tampering",
        "The ruined sentence curled into a blank ribbon while the moon librarian locked the ink away",
    ),
    Incident(
        "the upside-down question",
        "Where does a question mark sleep when a question is finished?",
        "the queen's message needed to be read before its punctuation was moved",
        "turned the question mark upside down to see whether it would become a tiny crown",
        "The message sounded like a command, and the queen sent the messenger to the wrong tower.",
        "the upside-down mark pointed toward the tower named in the mistaken message",
        "read words first and change marks only with permission",
        "An empty message tube rested beside the quiet tower while the real queen waited indoors",
    ),
    Incident(
        "the runaway verb",
        "What makes a sentence move: a naming word or an action word?",
        "the magic verb was safely tied to its sentence with a red thread",
        "snipped the thread to watch the action word dance through the air",
        "The sentence stopped moving, and the village bridge forgot how to rise.",
        "the red thread trailed from the loose verb to the bridge's silent lifting bell",
        "use gentle hands around language that helps other things work",
        "The bridge stayed lowered beneath the stars, and the runaway verb slept in a jar",
    ),
    Incident(
        "the goblin's missing apostrophe",
        "Can a tiny mark show that something belongs to someone?",
        "the goblin's name needed its little mark before the invitation was sealed",
        "borrowed the apostrophe and tucked it into her crown for fun",
        "The invitation looked as if the goblin had vanished, so he missed the moon feast.",
        "a curved ink mark gleamed on Luna's crown beside the missing name",
        "a small mark can carry a large meaning",
        "The feast candles burned low beside an unopened invitation and an empty goblin chair",
    ),
]


NAMES = ["Luna", "Mira", "Nell", "Tessa"]
FAIRY_NAMES = ["Iris", "Pip", "Aster", "Wren"]
TRAITS = ["bright", "playful", "clever", "restless"]
PLACES = {
    "moon_garden": "the moon garden",
    "whispering_castle": "the whispering castle",
}
CURIOSITIES = {
    "grammar": {"label": "grammar", "tags": {"grammatic", "language", "interest"}},
}
INTERESTS = {
    "grammar": {"label": "grammar", "tags": {"grammatic", "interest", "curiosity"}},
}


@dataclass(frozen=True)
class StoryParams:
    setting: str
    interest: str
    curiosity: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("moon_garden", "grammar", "grammar", "Luna", "Iris", "bright", 0),
    StoryParams("whispering_castle", "grammar", "grammar", "Mira", "Pip", "playful", 1),
]


ASP_RULES = r"""
valid(S,I,C) :- setting(S), interest(I), curiosity(C), affords(S,I), matches(I,C).
"""


def _valid(params: StoryParams) -> None:
    if params.setting not in PLACES:
        raise StoryError(f"unknown setting: {params.setting}")
    if params.interest not in INTERESTS:
        raise StoryError(f"unknown interest: {params.interest}")
    if params.curiosity not in CURIOSITIES:
        raise StoryError(f"unknown curiosity: {params.curiosity}")
    if params.interest != params.curiosity:
        raise StoryError("the interest and curiosity must concern the same subject")
    if not params.name.strip() or not params.helper.strip():
        raise StoryError("the fairy and helper need names")


def build_story(params: StoryParams) -> World:
    _valid(params)
    seed = params.seed if params.seed is not None else 0
    incident = INCIDENTS[seed % len(INCIDENTS)]
    world = World(PLACES[params.setting])

    luna = world.add(Entity(
        params.name,
        "girl",
        params.name,
        meters={"attention": 1.0, "care": 0.0},
        memes={"curiosity": 1.0, "confidence": 1.0},
    ))
    helper = world.add(Entity(
        params.helper,
        "fairy",
        params.helper,
        meters={"wisdom": 1.0},
        memes={"patience": 1.0},
    ))
    scroll = world.add(Entity(
        "scroll",
        "thing",
        "the enchanted grammar scroll",
        meters={"delicate": 1.0},
        memes={"meaning": 1.0},
    ))

    world.facts.update(
        hero=luna,
        helper=helper,
        scroll=scroll,
        incident=incident,
        interest=params.interest,
        curiosity=params.curiosity,
    )

    world.say(
        f"Once, in {world.place}, {params.name} was a {params.trait} young fairy "
        f"who found grammar as interesting as fireflies dancing in a jar."
    )
    world.say(
        f"One moonlit evening, a grammatic scroll shimmered beside the fountain. "
        f"It held a puzzle: “{incident.riddle}”"
    )
    world.say(
        f"“Curiosity is fun,” said {params.name}, “but I want to know the answer right now.” "
        f"“Ask before touching the magic,” said {params.helper}. "
        f"The helper warned that {incident.warning}."
    )

    world.para()
    luna.memes["impatience"] = 1.0
    luna.meters["care"] = 0.0
    world.say(
        f"But {params.name} {incident.tempting_action}. "
        f"The scroll gave a sad little shiver, and {incident.consequence}"
    )
    luna.meters["attention"] = 2.0
    luna.memes["surprise"] = 1.0
    world.say(
        f"“Stop and look,” said {params.helper}. Together they noticed that {incident.clue}. "
        f"{params.name} understood that an interesting mystery was not permission to meddle."
    )

    world.para()
    luna.meters["care"] = 1.0
    luna.memes["honesty"] = 1.0
    world.say(
        f"{params.name} admitted the mistake and {incident.repair}. "
        f"Then she said, “My lesson is that {incident.lesson}.”"
    )
    world.say(
        f"It was a bad ending for the evening's magic, though not for the fairies: "
        f"everyone was safe, and the truth was clear. {incident.ending}."
    )
    world.say(
        "From that night onward, Luna kept her questions bright, her hands gentle, "
        "and her fun close to kindness."
    )

    world.fired.add("curiosity_turn")
    world.fired.add("bad_ending")
    scroll.meters["damaged"] = 1.0
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
    incident: Incident = world.facts["incident"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a fairy tale about {hero.id}'s curiosity about grammar in {world.place}.",
            f"Include a fun but unsafe choice: {hero.id} {incident.tempting_action}.",
            f"End with the bad-ending image: {incident.ending}.",
        ],
        story_qa=[
            QAItem(
                f"What was {hero.id} curious about?",
                f"{hero.id} was curious about grammar and wanted to solve the enchanted puzzle on the scroll.",
            ),
            QAItem(
                f"What warning did {helper.id} give?",
                f"{helper.id} warned that {incident.warning}. The warning meant that {hero.id} should ask before touching the magic.",
            ),
            QAItem(
                "What went wrong?",
                f"{incident.consequence} The trouble began when {hero.id} {incident.tempting_action}.",
            ),
            QAItem(
                "What clue explained the trouble?",
                f"They noticed that {incident.clue}. That clue connected the damaged magic to the choice.",
            ),
            QAItem(
                "What lesson did the fairy learn?",
                f"{hero.id} learned that {incident.lesson}. Curiosity remained valuable, but it needed care.",
            ),
        ],
        world_qa=[
            QAItem(
                "Why can grammar be interesting?",
                "Grammar is interesting because small words and marks help people show how ideas fit together.",
            ),
            QAItem(
                "What is curiosity?",
                "Curiosity is the wish to learn or discover something that seems mysterious.",
            ),
            QAItem(
                "Why should someone ask before changing a magical scroll?",
                "They should ask first because an enchanted scroll may be delicate, useful, or dangerous to alter.",
            ),
        ],
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id}: kind={entity.kind}, meters={meters}, memes={memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for setting in PLACES:
        lines.append(asp.fact("setting", setting))
        lines.append(asp.fact("affords", setting, "grammar"))
    lines.append(asp.fact("interest", "grammar"))
    lines.append(asp.fact("curiosity", "grammar"))
    lines.append(asp.fact("matches", "grammar", "grammar"))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (setting, "grammar", "grammar")
        for setting in PLACES
    ]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    expected = set(valid_combos())
    actual = set(asp_valid_combos())
    if expected != actual:
        print("MISMATCH:")
        print("python only:", sorted(expected - actual))
        print("clingo only:", sorted(actual - expected))
        return 1
    for params in CURATED:
        generate(params)
    print(f"OK: ASP/Python parity and {len(CURATED)} generated stories verified.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fairy-tale world of fun, grammar, interest, and curiosity."
    )
    parser.add_argument("--setting", choices=sorted(PLACES))
    parser.add_argument("--interest", choices=sorted(INTERESTS))
    parser.add_argument("--curiosity", choices=sorted(CURIOSITIES))
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        setting=args.setting or rng.choice(list(PLACES)),
        interest=args.interest or "grammar",
        curiosity=args.curiosity or "grammar",
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(FAIRY_NAMES),
        trait=args.trait or rng.choice(TRAITS),
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(args.n, 1) and attempt < max(args.n * 30, 30):
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
            params = StoryParams(**{**params.__dict__, "seed": seed})
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
