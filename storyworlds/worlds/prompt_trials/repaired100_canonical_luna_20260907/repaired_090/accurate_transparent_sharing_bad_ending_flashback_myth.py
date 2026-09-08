#!/usr/bin/env python3
"""
A small mythic storyworld about accurate, transparent sharing.

Luna discovers that a clear account of a village's moon pearls matters more
than a glittering claim.  A flashback reveals how the claim was made, sharing
repairs the mistake, and a bad ending shows what happens when truth is hidden.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
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


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    trait: str
    ending: str
    incident: str
    telling_mode: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Incident:
    title: str
    beginning: str
    problem: str
    flashback: str
    mistake: str
    clue: str
    action: str
    sharing: str
    bad_ending: str
    resolution: str
    ending_image: str
    question: str
    answer: str


INCIDENTS = [
    Incident(
        "the moon-pearl basket",
        "Each spring, the Moon River gave the village one basket of pale pearls.",
        "Luna was asked to share them, but the count on the glittering banner said there were twelve while the basket held only ten.",
        "The night before, Luna remembered, two pearls had rolled beneath the reed mat when the basket was carried inside.",
        "She could have repeated the larger number and let the missing pearls become someone else's worry.",
        "A careful count beside the river stone showed ten pearls, and two round hollows marked the reed mat.",
        "Luna lifted the mat, found the missing pearls, and counted the whole basket again in front of everyone.",
        "She shared the accurate count and gave each family an equal share, explaining every step transparently.",
        "If she had hidden the mistake, two families would have gone home empty-handed and the village feast would have ended in angry silence.",
        "The village scratched out the wrong number and wrote twelve only after the two pearls were returned to the basket.",
        "Moonlight shone through twelve clean spaces in the sharing tray, and every family carried one small cup home.",
        "What did Luna find beneath the reed mat?",
        "Luna found the two moon pearls that had rolled beneath the reed mat before the sharing began.",
    ),
    Incident(
        "the divided spring",
        "A clear spring rose beneath an old fig tree and belonged to every traveler.",
        "A painted sign claimed that the spring had filled three jars, but one jar was dry.",
        "Luna recalled seeing the youngest shepherd carry the empty jar away to help a thirsty lamb.",
        "The steward wanted to keep the sign unchanged so nobody would ask where the water had gone.",
        "Luna followed damp hoofprints from the spring to the lamb's pen.",
        "She invited the shepherd to return, measured the water again, and told the whole village what had happened.",
        "The shepherd shared the water with the lamb first, then poured the remaining amount into the village jars.",
        "Had Luna hidden the dry jar, the lamb would have thirsted and the villagers would have blamed one another.",
        "The steward repainted the sign with the true amount and added a note about the lamb.",
        "The spring's reflection held one lamb, three jars, and a sign no longer hiding its honest marks.",
        "Why was one spring jar empty?",
        "The youngest shepherd had carried the jar to give water to a thirsty lamb.",
    ),
    Incident(
        "the silver fig",
        "At harvest time, the oldest fig tree bore one silver fruit for the village meal.",
        "The fruit looked large enough for everyone, but a split in its skin made the first weighing inaccurate.",
        "Luna remembered that a squirrel had nibbled the fruit while the scale was being carried from the shrine.",
        "The cook could have sliced it secretly and pretended each portion was equal.",
        "A second weighing, made on a steady stone, showed exactly how much fruit remained.",
        "Luna shared the accurate portions and gave the squirrel the fallen peel instead of hiding the loss.",
        "She explained the change openly, so no child thought another child had taken more.",
        "If the cook had concealed the split, the meal would have ended with jealous whispers and no trust.",
        "The silver fig became many small, honest tastes around the warm cooking fire.",
        "What made the first weighing inaccurate?",
        "A squirrel had nibbled the silver fig while the scale was being moved.",
    ),
    Incident(
        "the star-map promise",
        "An old star map promised a bright star over the village well.",
        "The star appeared over the eastern hill instead, and the children feared the map had lied.",
        "Luna recalled that the map had been drawn before the hill's tall cedar grew.",
        "The keeper wanted to cover the map's old marks and declare the children mistaken.",
        "Luna compared the cedar's shadow with the map and showed how the view had changed.",
        "She shared the corrected map, leaving the old lines visible beside the new ones.",
        "If the keeper had hidden the old drawing, the children would have learned to doubt both maps and promises.",
        "The map became more useful because its history was written clearly beside its correction.",
        "Two star paths glimmered on the parchment, and the cedar stood between them like a patient teacher.",
        "Why did the star seem to be in the wrong place?",
        "The map was drawn before the cedar grew tall, so the view of the star had changed.",
    ),
]


OPENINGS = [
    "In the first age, when the moon still listened to village bells, Luna served the people.",
    "Long ago, truth was kept in a clay bowl beneath the village fig tree.",
    "The old people say that every shared gift carries an invisible thread of trust.",
    "Before the river learned its silver song, Luna guarded the village records.",
    "On a night when the stars leaned close, a small mistake became a large question.",
]

TRAITS = ["careful", "curious", "patient", "truthful", "bright"]
NAMES = ["Luna", "Mira", "Tala", "Nia", "Suri"]


def can_story(place: str, activity: str, prize: str) -> bool:
    return place == "village" and activity == "share" and prize == "moon_pearls"


ASP_RULES = r"""
place(village).
activity(share).
prize(moon_pearls).
feature(sharing).
feature(bad_ending).
feature(flashback).

compatible(P,A,R) :-
    place(P), activity(A), prize(R),
    P = village, A = share, R = moon_pearls.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("place", "village"),
        asp.fact("activity", "share"),
        asp.fact("prize", "moon_pearls"),
        asp.fact("feature", "sharing"),
        asp.fact("feature", "bad_ending"),
        asp.fact("feature", "flashback"),
    ])


def asp_program(show: str = "#show compatible/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [("village", "share", "moon_pearls")]


def tell(params: StoryParams) -> World:
    incident = INCIDENTS[int(params.incident.rsplit("_", 1)[1])]
    opening = OPENINGS[int(params.telling_mode.rsplit("_", 1)[1])]

    world = World()
    luna = world.add(Entity(
        id="hero",
        kind="character",
        type="girl",
        label=params.name,
        memes={"care": 1.0, "honesty": 1.0},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type="elder",
        label="the keeper",
        memes={"pride": 1.0},
    ))
    gift = world.add(Entity(
        id="gift",
        kind="object",
        type="moon_pearls",
        label="the moon pearls",
        meters={"count": 10.0},
    ))
    record = world.add(Entity(
        id="record",
        kind="object",
        type="record",
        label="the village record",
        memes={"clarity": 1.0},
    ))
    world.facts.update(
        hero=luna,
        elder=elder,
        gift=gift,
        record=record,
        incident=incident,
    )

    world.say(opening)
    world.say(
        f"{params.name}, a {params.trait} keeper of small truths, was chosen to share "
        "the village's moon gift."
    )
    world.say(
        "The gift belonged to everyone, so its count had to be accurate and its path "
        "from basket to hand had to be transparent."
    )
    world.para()
    world.say(incident.beginning)
    world.say(incident.problem)
    world.say(
        f'"The banner must be right," said the keeper. '
        f'"Read its number aloud, {params.name}."'
    )
    world.say(
        f'"A bright number is not enough," {params.name} replied. '
        '"Let us count what is truly here."'
    )
    world.fired.add("question_raised")
    world.para()
    world.say("Then Luna remembered an earlier moment, and the village entered a flashback.")
    world.say(incident.flashback)
    world.say(incident.mistake)
    world.say(
        f'"Why did you not tell us sooner?" the keeper asked. '
        f'"I feared the gift would seem smaller," {params.name} answered.'
    )
    world.say(
        '"A hidden gap grows wider," said the keeper. '
        '"Show us the truth, and we can repair it together."'
    )
    world.para()
    world.say(incident.clue)
    world.say(incident.action)
    world.say(incident.sharing)
    world.fired.add("transparent_sharing")
    world.entities["hero"].memes["trust"] = 2.0
    world.entities["gift"].meters["count"] = 12.0
    world.para()
    world.say("The elders also named the bad ending that honesty had prevented.")
    world.say(incident.bad_ending)
    world.say(incident.resolution)
    world.say(
        f'"A true share is not only what each person receives," {params.name} said. '
        '"It is also the truth everyone can see."'
    )
    world.say(incident.ending_image)
    world.facts.update(
        title=incident.title,
        clue=incident.clue,
        sharing=incident.sharing,
        bad_ending=incident.bad_ending,
        ending_image=incident.ending_image,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    incident = world.facts["incident"]
    hero = world.facts["hero"]
    return [
        "Write a child-friendly myth about accurate, transparent sharing.",
        f"Tell a myth in which {hero.label} uses a flashback to repair a village mistake.",
        f"Include a bad ending that honesty prevents, then end with this image: {incident.ending_image}",
    ]


def story_qa(world: World) -> list[QAItem]:
    incident = world.facts["incident"]
    hero = world.facts["hero"]
    return [
        QAItem(
            question=f"What was {hero.label} asked to share?",
            answer=f"{hero.label} was asked to share the village's moon gift accurately and transparently with every family.",
        ),
        QAItem(
            question=incident.question,
            answer=incident.answer,
        ),
        QAItem(
            question=f"What did the flashback help {hero.label} understand?",
            answer=f"The flashback helped {hero.label} remember the earlier event that explained the apparent mistake: {incident.flashback}",
        ),
        QAItem(
            question="How did transparent sharing repair the problem?",
            answer=incident.sharing,
        ),
        QAItem(
            question="What bad ending did honesty prevent?",
            answer=incident.bad_ending,
        ),
        QAItem(
            question="What final image showed that trust had returned?",
            answer=incident.ending_image,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does accurate mean?",
            answer="Accurate means correct and matching the facts.",
        ),
        QAItem(
            question="What does transparent sharing mean?",
            answer="Transparent sharing means explaining what is being shared and how it was divided so others can understand and check it.",
        ),
        QAItem(
            question="Why can a flashback help in a story?",
            answer="A flashback can reveal an earlier event that explains a present problem.",
        ),
        QAItem(
            question="What is a bad ending in a story?",
            answer="A bad ending is an unhappy result that characters may avoid through wiser choices.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id:8} ({entity.type:12}) {' '.join(details)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random, seed: int) -> StoryParams:
    if args.place and args.place != "village":
        raise StoryError("This storyworld uses the village setting.")
    if args.activity and args.activity != "share":
        raise StoryError("This storyworld centers on sharing.")
    if args.prize and args.prize != "moon_pearls":
        raise StoryError("This storyworld's shared gift is moon pearls.")
    if args.name and not args.name.strip():
        raise StoryError("The name must not be empty.")
    if args.trait and args.trait not in TRAITS:
        raise StoryError("Trait must be one of: " + ", ".join(TRAITS))
    if args.ending and args.ending != "hopeful":
        raise StoryError("The repaired story must end with hope.")

    return StoryParams(
        place="village",
        activity="share",
        prize="moon_pearls",
        name=args.name or rng.choice(NAMES),
        trait=args.trait or rng.choice(TRAITS),
        ending="hopeful",
        incident=f"incident_{seed % len(INCIDENTS):02d}",
        telling_mode=f"mode_{(seed // len(INCIDENTS)) % len(OPENINGS):02d}",
        seed=seed,
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A mythic storyworld about accurate and transparent sharing."
    )
    parser.add_argument("--place", choices=["village"])
    parser.add_argument("--activity", choices=["share"])
    parser.add_argument("--prize", choices=["moon_pearls"])
    parser.add_argument("--name")
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--ending", choices=["hopeful"])
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    python_combos = set(valid_combos())
    asp_combos = set(asp_valid_combos())
    if python_combos != asp_combos:
        print("MISMATCH between Python and ASP compatibility gates.")
        if python_combos - asp_combos:
            print("  only in Python:", sorted(python_combos - asp_combos))
        if asp_combos - python_combos:
            print("  only in ASP:", sorted(asp_combos - python_combos))
        return 1

    for seed in range(8):
        params = resolve_params(
            argparse.Namespace(
                place=None,
                activity=None,
                prize=None,
                name=None,
                trait=None,
                ending=None,
            ),
            random.Random(seed),
            seed,
        )
        sample = generate(params)
        if not sample.story or len(sample.story_qa) < 4:
            print("Generated-story verification failed.")
            return 1
    print("OK: ASP/Python parity and generated-story checks passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = resolve_params(args, random.Random(base_seed), base_seed)
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        for index in range(max(args.n, 1)):
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed), seed)
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
