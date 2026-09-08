#!/usr/bin/env python3
"""
A small heartwarming story world about a parade sailor, a careful infantry
helper, and a twist that turns a quiet problem into a shared celebration.
"""

from __future__ import annotations

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
    type: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"sailor", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"infantry", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Parade:
    name: str
    route: str
    purpose: str
    banner: str
    weather: str


class World:
    def __init__(self, parade: Parade) -> None:
        self.parade = parade
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


@dataclass
class StoryParams:
    sailor: str
    infantry: str
    parade_name: str
    route: str
    seed: Optional[int] = None
    scenario: Optional[str] = None
    telling_mode: Optional[str] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    opening: str
    problem: str
    rushed_action: str
    consequence: str
    clue: str
    careful_action: str
    twist: str
    apology: str
    repair: str
    outcome: str
    lesson: str
    ending: str


SAILOR_NAMES = ["Mara", "Lina", "Nell", "Suri", "Ada", "Tess"]
INFANTRY_NAMES = ["Ben", "Owen", "Cal", "Rafi", "Jon", "Milo"]
PARADE_NAMES = ["the Lantern Parade", "the Harbor Parade", "the Welcome Parade", "the Sunrise Parade"]
ROUTES = [
    "the town square",
    "the riverside road",
    "the harbor lane",
    "the hilltop avenue",
]
TELLING_MODES = ["arrival", "dialogue", "mystery", "promise", "countdown", "memory"]

SCENARIOS = [
    Scenario(
        key="small_banner",
        opening="was carrying the parade's largest blue banner",
        problem="the banner would not rise above the first street",
        rushed_action="pulled hard on the wet rope",
        consequence="the rope snapped and the banner slid into a muddy puddle",
        clue="a tiny silver button was caught in the pulley",
        careful_action="held the pulley still while the infantry helper examined the button",
        twist="the button belonged to a shy child who had sewn a secret star onto the banner",
        apology="said that rushing had torn the banner and hidden the child's special work",
        repair="washed the cloth, stitched the tear, and sewed the silver button back beside the star",
        outcome="the banner lifted higher than any other flag",
        lesson="a small detail can carry a big feeling",
        ending="the child marched beneath the banner, touching the silver star with a proud smile",
    ),
    Scenario(
        key="lost_drum",
        opening="was leading the sailors who carried the parade drum",
        problem="the drum vanished just before the opening song",
        rushed_action="blamed the infantry line for moving it",
        consequence="the musicians stopped speaking and the parade grew quiet",
        clue="soft drumbeats came from behind the old bakery",
        careful_action="followed the sound with the infantry helper instead of arguing",
        twist="a baker had borrowed the drum to soothe a baby who would not sleep",
        apology="admitted that the quick accusation had hurt the infantry line",
        repair="thanked the baker, carried the sleeping baby outside, and invited the whole family to lead the first beat",
        outcome="the baby woke to the gentlest parade in town",
        lesson="asking kindly can find what blaming only hides",
        ending="the baby waved from the bakery door while every drummer answered with one soft boom",
    ),
    Scenario(
        key="rainy_ribbon",
        opening="was tying bright ribbons along the parade route",
        problem="a sudden rainstorm soaked the decorations",
        rushed_action="ordered the infantry to pull every ribbon down",
        consequence="the children who had made them thought their work was unwanted",
        clue="the wet ribbons shone like little streams of color",
        careful_action="asked the children whether the ribbons could become rain flags",
        twist="the soggy decorations were safer and brighter when they danced in the rain",
        apology="told the children that protecting things without asking had made them sad",
        repair="tied the ribbons to short poles and gave each maker a place in the marching line",
        outcome="the rain flags guided everyone safely along the slippery road",
        lesson="a mistake can become useful when the people affected help decide",
        ending="rainbow ribbons fluttered above the marchers as puddles reflected every color",
    ),
    Scenario(
        key="quiet_trumpet",
        opening="was preparing to play the first trumpet call",
        problem="the trumpet made no sound at the parade's starting bell",
        rushed_action="blew harder and harder into the silent instrument",
        consequence="the mouthpiece popped loose and rolled under a wagon",
        clue="the wagon carried a basket of flowers with one empty place",
        careful_action="looked beneath the wagon with the infantry helper",
        twist="the missing mouthpiece had been used as a tiny flower cup by a young gardener",
        apology="explained that impatience had scattered flowers and delayed the call",
        repair="returned the mouthpiece, replanted the flowers, and asked the gardener to choose the opening note",
        outcome="the first trumpet call sounded warm and clear",
        lesson="careful listening can reveal a caring purpose",
        ending="the gardener lifted one flower as the trumpet sang above the smiling crowd",
    ),
    Scenario(
        key="empty_chair",
        opening="was escorting an old sailor's empty chair in the parade",
        problem="the chair's ribbon came loose and the chair rolled away",
        rushed_action="chased it alone through the crowd",
        consequence="the parade line broke apart and several children became frightened",
        clue="the chair stopped beside a quiet porch covered in family photographs",
        careful_action="asked the infantry helper to slow the crowd while she spoke with the people on the porch",
        twist="the chair belonged to a sailor who had once promised to watch the parade from that very porch",
        apology="admitted that chasing the chair had made the tribute feel like a race",
        repair="secured the ribbon and invited the family to walk beside the chair",
        outcome="the missing sailor's memory became part of the parade",
        lesson="honoring someone means making room for the people who remember them",
        ending="the chair rolled gently past the porch while a family waved from behind its flowers",
    ),
    Scenario(
        key="backward_flag",
        opening="was teaching the infantry line to carry a bright community flag",
        problem="the flag kept facing backward in the wind",
        rushed_action="scolded the youngest marcher for holding it wrong",
        consequence="the child lowered the flag and stepped out of line",
        clue="the flag's stitched picture looked clearer from the opposite side",
        careful_action="turned the pole around and asked the child what the picture meant",
        twist="the flag was designed to show welcome to people walking behind the parade",
        apology="said the child had understood the flag better than the grown-ups",
        repair="placed the child at the front and let the flag welcome both sides of the street",
        outcome="the whole crowd could see the picture as the march passed",
        lesson="a different view may reveal the purpose everyone missed",
        ending="the youngest marcher led the line, and the backward flag welcomed people on every side",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming parade storyworld with a sailor, infantry helper, and twist."
    )
    parser.add_argument("--sailor", choices=SAILOR_NAMES)
    parser.add_argument("--infantry", choices=INFANTRY_NAMES)
    parser.add_argument("--parade-name", choices=PARADE_NAMES)
    parser.add_argument("--route", choices=ROUTES)
    parser.add_argument("--scenario", choices=[s.key for s in SCENARIOS])
    parser.add_argument("--telling-mode", choices=TELLING_MODES)
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
    sailor = args.sailor or rng.choice(SAILOR_NAMES)
    infantry_choices = [name for name in INFANTRY_NAMES if name != sailor]
    infantry = args.infantry or rng.choice(infantry_choices)
    return StoryParams(
        sailor=sailor,
        infantry=infantry,
        parade_name=args.parade_name or rng.choice(PARADE_NAMES),
        route=args.route or rng.choice(ROUTES),
        scenario=args.scenario or rng.choice(SCENARIOS).key,
        telling_mode=args.telling_mode or rng.choice(TELLING_MODES),
    )


def _opening(params: StoryParams, scenario: Scenario) -> list[str]:
    sailor = params.sailor
    infantry = params.infantry
    parade = params.parade_name
    route = params.route
    mode = params.telling_mode or "arrival"
    if mode == "dialogue":
        return [
            f'"Ready for the {parade}?" {sailor} asked.',
            f'"Ready to help," {infantry} replied as they reached {route}. The sailor {scenario.opening}.',
        ]
    if mode == "mystery":
        return [
            f"Something unusual waited at {route before the {parade} began.",
            f"{sailor} and {infantry} were there because the sailor {scenario.opening}.",
        ]
    if mode == "promise":
        return [
            f"{sailor} had promised to make the {parade} welcoming for everyone.",
            f"With {infantry} beside her, she reached {route} because she {scenario.opening}.",
        ]
    if mode == "countdown":
        return [
            f"The parade bell would ring in ten minutes at {route}.",
            f"{sailor} hurried to prepare the {parade}; she {scenario.opening}, while {infantry} checked the marching line.",
        ]
    if mode == "memory":
        return [
            f"Years later, people remembered the {parade} as the kindest march they had seen.",
            f"It began at {route}, when {sailor} {scenario.opening} and {infantry} stood ready to help.",
        ]
    return [
        f"The {parade} gathered bright footsteps along {route}.",
        f"{sailor}, a cheerful sailor, {scenario.opening}, while {infantry} kept the line safe.",
    ]


def generate(params: StoryParams) -> StorySample:
    if not params.sailor or not params.infantry:
        raise StoryError("A parade story needs both a sailor and an infantry helper.")
    if params.sailor == params.infantry:
        raise StoryError("The sailor and infantry helper must have different names.")
    scenario = next((s for s in SCENARIOS if s.key == params.scenario), None)
    if scenario is None:
        raise StoryError(f"Unknown parade scenario: {params.scenario}")

    rng = random.Random(params.seed)
    parade = Parade(
        name=params.parade_name,
        route=params.route,
        purpose="to welcome neighbors and remember kindness",
        banner="a gold-and-blue banner",
        weather=rng.choice(["clear", "cool", "fresh after rain"]),
    )
    world = World(parade)

    sailor = world.add(
        Entity(
            id=params.sailor,
            type="sailor",
            label="parade sailor",
            location="parade route",
            meters={"energy": 0.8, "balance": 0.8},
            memes={"hope": 0.8, "care": 0.7},
            traits=["brave", "warmhearted"],
        )
    )
    infantry = world.add(
        Entity(
            id=params.infantry,
            type="infantry",
            label="infantry helper",
            location="parade route",
            meters={"alertness": 0.9, "patience": 0.8},
            memes={"duty": 0.9, "kindness": 0.8},
            traits=["steady", "observant"],
        )
    )
    object_entity = world.add(
        Entity(
            id="parade_object",
            type="parade_object",
            label="parade object",
            location="parade route",
            meters={"condition": 0.7, "usefulness": 0.6},
            memes={"mystery": 0.8},
            traits=["bright", "important"],
        )
    )
    world.facts.update(
        parade=parade.name,
        route=parade.route,
        sailor=sailor,
        infantry=infantry,
        object=object_entity,
        scenario=scenario.key,
        problem=scenario.problem,
        twist=scenario.twist,
        repair=scenario.repair,
        outcome=scenario.outcome,
    )

    for sentence in _opening(params, scenario):
        world.say(sentence)
    world.say(f"Then they discovered that {scenario.problem}.")

    world.para()
    world.say(
        f'"I can fix this quickly," {sailor.id} said, and {sailor.pronoun()} {scenario.rushed_action}.'
    )
    world.say(f"But {scenario.consequence}.")
    world.say(
        f'"Wait," {infantry.id} said gently. "Let us find out what this object needs before we change it."'
    )
    world.say(f"{sailor.id} looked at {infantry.id}. The kind warning changed her plan.")

    world.para()
    world.say(f"Together they noticed that {scenario.clue}.")
    world.say(f"{infantry.id} {scenario.careful_action}.")
    world.say(f"That was the twist: {scenario.twist}.")
    world.say(
        f'"Then this is not just a parade problem," {sailor.id} said. "It is someone\'s special story."'
    )
    world.say(
        f'"And we can help the story continue," {infantry.id} answered.'
    )

    world.para()
    world.say(f"{sailor.id} {scenario.apology}.")
    world.say(f"{infantry.id} smiled and said, \"An apology is a good first step.\"")
    world.say(f"Together they {scenario.repair}.")
    world.say(f"At last, {scenario.outcome}.")

    world.para()
    world.say(f"The parade moved onward with one lesson: {scenario.lesson}.")
    world.say(f"As the {parade.name.lower()} passed {parade.route}, {scenario.ending}.")

    object_entity.location = "repaired parade line"
    object_entity.meters["condition"] = 1.0
    object_entity.meters["usefulness"] = 1.0
    object_entity.memes["mystery"] = 0.0
    object_entity.memes["shared_meaning"] = 1.0
    sailor.memes["patience"] = 1.0
    infantry.memes["trust"] = 1.0
    world.facts.update(resolved=True, twist_revealed=True, parade_continued=True)

    prompts = [
        f"Write a heartwarming parade story about sailor {params.sailor} and infantry helper {params.infantry}.",
        f"Tell a child-friendly tale in {params.route} with a surprising twist: {scenario.twist}.",
        f"Write a parade story whose ending shows that {scenario.lesson}.",
    ]
    story_qa = [
        QAItem(
            question=f"What problem did {params.sailor} meet during the parade?",
            answer=f"The problem was that {scenario.problem}. This interrupted the parade preparations at {params.route}.",
        ),
        QAItem(
            question="What did the infantry helper notice?",
            answer=f"The infantry helper noticed that {scenario.clue}. That clue helped them understand the object's purpose.",
        ),
        QAItem(
            question="What was the story's twist?",
            answer=f"The twist was that {scenario.twist}. The object had a caring meaning instead of being an ordinary nuisance.",
        ),
        QAItem(
            question=f"How did {params.sailor} and {params.infantry} repair the problem?",
            answer=f"They listened, apologized, and then {scenario.repair}. Their teamwork allowed the parade to continue.",
        ),
        QAItem(
            question="What lesson did the parade teach?",
            answer=f"It taught that {scenario.lesson}. The repaired parade showed this lesson in action.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized procession in which people walk, carry decorations, make music, or celebrate together.",
        ),
        QAItem(
            question="What does a sailor do in this storyworld?",
            answer="A sailor is a brave parade character who helps carry the celebration forward and learns to act with patience.",
        ),
        QAItem(
            question="What does infantry mean here?",
            answer="Infantry means a group or helper who travels and works on foot. In this storyworld, the infantry helper protects the parade and notices useful clues.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a new discovery that changes how the characters understand an earlier problem.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def asp_facts() -> str:
    from asp import fact

    return "\n".join(
        [
            fact("theme", "parade"),
            fact("character", "sailor"),
            fact("character", "infantry"),
            fact("feature", "twist"),
            fact("style", "heartwarming"),
            fact("requires", "kind_repair"),
        ]
    )


ASP_RULES = r"""
kind_story :- theme(parade), character(sailor), character(infantry),
              feature(twist), style(heartwarming), requires(kind_repair).
#show kind_story/0.
#show theme/1.
#show character/1.
#show feature/1.
#show style/1.
#show requires/1.
"""


def asp_program(show: str = "#show kind_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    if not model:
        print("MISMATCH: ASP produced no model.")
        return 1
    required = {
        ("theme", ("parade",)),
        ("character", ("sailor",)),
        ("character", ("infantry",)),
        ("feature", ("twist",)),
        ("style", ("heartwarming",)),
        ("kind_story", ()),
    }
    actual = {(symbol.name, tuple(str(arg).strip('"') for arg in symbol.arguments)) for symbol in model}
    if not required.issubset(actual):
        print("MISMATCH: ASP model is missing required story facts.")
        return 1
    sample = generate(
        StoryParams(
            sailor="Mara",
            infantry="Ben",
            parade_name="the Lantern Parade",
            route="the town square",
            seed=17,
            scenario="small_banner",
            telling_mode="dialogue",
        )
    )
    if "twist" not in sample.story.lower() and "surprise" not in sample.story.lower():
        print("MISMATCH: generated story does not exercise the twist.")
        return 1
    if "apolog" not in sample.story.lower():
        print("MISMATCH: generated story lacks repair.")
        return 1
    print("OK: ASP parity and generated-story checks passed.")
    return 0


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
        print("--- world model state ---")
        for entity in sample.world.entities.values():
            bits = [f"location={entity.location}"]
            if entity.meters:
                bits.append(f"meters={entity.meters}")
            if entity.memes:
                bits.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {entity.type} {' '.join(bits)}")
    if qa:
        print()
        print("== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("\n".join(str(symbol) for symbol in model))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.n < 1:
        raise SystemExit("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                sailor="Mara",
                infantry="Ben",
                parade_name="the Lantern Parade",
                route="the town square",
                seed=101,
                scenario="small_banner",
                telling_mode="dialogue",
            ),
            StoryParams(
                sailor="Lina",
                infantry="Owen",
                parade_name="the Harbor Parade",
                route="the harbor lane",
                seed=202,
                scenario="lost_drum",
                telling_mode="mystery",
            ),
            StoryParams(
                sailor="Nell",
                infantry="Cal",
                parade_name="the Sunrise Parade",
                route="the riverside road",
                seed=303,
                scenario="backward_flag",
                telling_mode="promise",
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 30):
            attempt += 1
            attempt_seed = base_seed + attempt
            params = resolve_params(args, random.Random(attempt_seed))
            params.seed = attempt_seed
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
            header = f"### {params.sailor} and {params.infantry} in {params.parade_name}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
