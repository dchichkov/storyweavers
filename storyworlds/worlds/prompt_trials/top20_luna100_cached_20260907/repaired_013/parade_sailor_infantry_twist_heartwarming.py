#!/usr/bin/env python3
"""
A heartwarming story world about a parade, a sailor, and infantry friends whose
planned twist becomes a gift of courage.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    setting: str = "Harbor Square"
    hero: str = "Mara"
    sailor: str = "Sailor Finn"
    infantry_friend: str = "Corporal June"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity


SETTING_REGISTRY = {
    "Harbor Square": {
        "tags": {"parade", "harbor", "community"},
        "mood": "bright with bells and sea wind",
    },
    "Lantern Pier": {
        "tags": {"parade", "sailor", "lanterns"},
        "mood": "golden beneath the evening sky",
    },
    "Maple Barracks Green": {
        "tags": {"parade", "infantry", "garden"},
        "mood": "warm with flags and falling leaves",
    },
}


@dataclass(frozen=True)
class TwistArc:
    title: str
    premise: str
    problem: str
    dialogue: str
    twist: str
    action: str
    result: str
    ending: str
    problem_answer: str
    twist_answer: str
    result_answer: str


ARCS = [
    TwistArc(
        "The Parade That Turned Around",
        "The town prepared a parade to thank its returning sailor and infantry company.",
        "Sailor Finn arrived quietly, carrying a weathered compass and looking toward the empty end of the route.",
        '"Why are you watching the road behind us?" Mara asked. Finn answered, "Because someone else should lead today."',
        "At the first drumbeat, the parade made its twist: every marcher turned around and walked toward the lonely lighthouse keeper who had guided ships through the storm.",
        "Corporal June raised the infantry banner, and Finn used his compass to mark a safe path while children carried lanterns beside him.",
        "The keeper saw the surprise, came down from the lighthouse, and found the whole town waiting with music and warm bread.",
        "the sailor, the infantry, and the lighthouse keeper sharing the front step while the parade flags fluttered behind them",
        "Sailor Finn felt uneasy because the parade honored him while the lighthouse keeper stood forgotten at the end of the road.",
        "The parade turned around so the lighthouse keeper, who had guided ships safely, could receive the town's thanks.",
        "The keeper joined the celebration, and the sailor, infantry, and townspeople shared the honor together.",
    ),
    TwistArc(
        "The Missing Drum",
        "A bright parade was planned for the first spring morning after the infantry returned from helping at the harbor.",
        "The lead drum vanished, and the drummer, a young sailor, was too worried to tell anyone he had lost it.",
        '"We can search together," said Corporal June. The sailor replied, "But the parade will wait for me?"',
        "Instead of marching past him, the parade changed its rhythm into soft claps and humming, giving the sailor time to follow a trail of red ribbons.",
        "The infantry searched the pier while Mara asked shopkeepers about the ribbons; they found the drum beside an old boat where a child had been practicing.",
        "The child returned it, and the sailor invited the child to beat the first rhythm of the parade.",
        "a small hand beating the drum while the sailor and infantry marchers smile on either side",
        "The lead drum was missing, and the young sailor feared that the parade would be ruined because of his mistake.",
        "The parade became quiet claps and humming so the sailor could search without shame or hurry.",
        "The drum was found beside an old boat, and the sailor welcomed the child who had found it into the celebration.",
    ),
    TwistArc(
        "The Flag in the Rain",
        "The town's parade promised bright flags, but rain began just before the sailor's ship reached shore.",
        "The infantry banner tore on a sharp gate, leaving Corporal June certain that the march should be canceled.",
        '"A torn flag still tells a true story," Mara said. "Then let us carry the story together," June answered.',
        "The twist was that each group gave up its finest cloth: sailors offered blue neckerchiefs, infantry offered red sashes, and children offered yellow scarves.",
        "They tied the pieces into one wide flag while the band played under awnings and the parade moved slowly around the puddles.",
        "When the ship arrived, the sailor saw a flag made from everyone's small sacrifice and saluted it with shining eyes.",
        "one many-colored flag drying above the square, stitched from sailor blue, infantry red, and children's gold",
        "Rain tore the infantry banner, and Corporal June thought the parade had to be canceled.",
        "Everyone donated a small piece of cloth, turning the broken banner into a shared flag.",
        "The sailor understood that the new flag represented the whole town, and the parade continued despite the rain.",
    ),
    TwistArc(
        "The Sailor's Quiet Salute",
        "A parade gathered to welcome a sailor who had returned after many months at sea.",
        "The sailor stood at the back because he had learned that his younger brother was too shy to walk with the infantry band.",
        '"You do not have to stand alone," Mara told him. He whispered, "Could the band walk slowly for him?"',
        "The planned surprise changed: the infantry band lowered its instruments and marched at the brother's gentle pace.",
        "Finn walked beside his brother, while Corporal June handed him a tiny flag and let him choose the next turn.",
        "The shy child led the parade around the square, and the sailor's welcome became a welcome for every quiet heart.",
        "the little flag held high by the child as his sailor brother walks beside him under a shower of paper stars",
        "The sailor stayed at the back because his shy younger brother was afraid to join the infantry band.",
        "The parade slowed down and let the shy child lead instead of forcing him to keep the usual pace.",
        "The child gained confidence, and the sailor's homecoming became a celebration that included everyone.",
    ),
    TwistArc(
        "The Lanterns for Home",
        "At sunset, the parade would guide a sailor's boat into the harbor while infantry families waited on shore.",
        "A thick fog hid the pier lights, and nobody could see the safe channel.",
        '"If we cannot shine from the pier," said Finn, "we can shine from the people." June answered, "Then we will make a moving harbor."',
        "The parade twisted into a line of lanterns: infantry stood along the bank, sailors carried lights in small boats, and children filled the gaps.",
        "Mara counted the spaces and called each lantern forward until a glowing path curved through the fog.",
        "The boat followed the human lights home, and every waiting family recognized a familiar face before the ship touched shore.",
        "a ribbon of lanterns reflected in the harbor as the sailor steps onto land and embraces his family",
        "Fog hid the pier lights and made it unsafe for the sailor's boat to find the harbor.",
        "People became a moving harbor by carrying lanterns along the bank and across small boats.",
        "The sailor followed the living chain of lights safely home to his waiting family.",
    ),
    TwistArc(
        "The Empty Front Row",
        "The parade's front row was reserved for honored guests, including a sailor and the returning infantry.",
        "Mara noticed that the front row had no place for the people who had repaired nets, cooked meals, and cared for children.",
        '"Who kept the town ready?" she asked. June smiled. "Perhaps the front row belongs to more feet than we planned."',
        "The twist moved the chairs aside and made the front row a walking circle, so helpers could enter the parade one by one.",
        "The sailor carried a net mender's basket, infantry members carried soup pots, and children thanked each helper by name.",
        "The people who usually watched from doorways became the parade's center, and the honored guests walked behind them proudly.",
        "a circle of chairs around the square, each holding a thank-you card while the parade winds gently around them",
        "The planned front row excluded the quiet helpers who kept the town safe and cared for its families.",
        "The front row became a walking circle that welcomed every helper into the parade.",
        "The helpers received public thanks, and the sailor and infantry gladly followed them.",
    ),
]


OPENINGS = [
    "On the morning of the parade, bells rang over {setting} while {hero} watched the harbor road.",
    "The flags were ready in {setting}, and {hero} could hear the sea before the first parade drum.",
    "Everyone in {setting} knew that day would bring a sailor home and welcome the infantry.",
    "A warm wind crossed {setting} as {hero} helped the town prepare its heartwarming parade.",
]


def stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join(
        (params.setting, params.hero, params.sailor, params.infantry_friend)
    )
    return sum((i + 1) * ord(char) for i, char in enumerate(text))


def fill(text: str, facts: dict[str, object]) -> str:
    return text.format(**facts)


def cap(text: str) -> str:
    return text[:1].upper() + text[1:]


def generate(params: StoryParams) -> StorySample:
    if params.hero == params.sailor or params.hero == params.infantry_friend:
        raise StoryError("The hero, sailor, and infantry friend must have different names.")
    if params.sailor == params.infantry_friend:
        raise StoryError("The sailor and infantry friend must be different characters.")

    seed = stable_seed(params)
    arc = ARCS[seed % len(ARCS)]
    world = World(setting=params.setting)

    hero = world.add(
        Entity(
            params.hero,
            "town helper",
            meters={"walking": 1.0, "lantern": 1.0},
            memes={"care": 1.0, "curiosity": 1.0},
        )
    )
    sailor = world.add(
        Entity(
            params.sailor,
            "sailor",
            meters={"travel": 1.0, "sea": 1.0},
            memes={"humility": 1.0, "belonging": 0.5},
        )
    )
    infantry = world.add(
        Entity(
            params.infantry_friend,
            "infantry member",
            meters={"marching": 1.0, "banner": 1.0},
            memes={"courage": 1.0, "welcome": 1.0},
        )
    )
    world.add(Entity("the parade", "community event", meters={"rhythm": 1.0}, memes={"joy": 1.0}))
    world.add(Entity("the shared flag", "symbol", meters={"cloth": 1.0}, memes={"belonging": 1.0}))
    world.add(Entity("the harbor road", "place", meters={"distance": 1.0}, memes={"memory": 1.0}))

    facts = {
        "hero": hero.name,
        "sailor": sailor.name,
        "infantry_friend": infantry.name,
        "setting": params.setting,
        "arc": arc,
    }
    world.facts.update(
        facts,
        title=arc.title,
        problem=fill(arc.problem, facts),
        twist=fill(arc.twist, facts),
        action=fill(arc.action, facts),
        result=fill(arc.result, facts),
        ending=fill(arc.ending, facts),
        opening_variant=(seed // len(ARCS)) % len(OPENINGS),
        structure_variant=(seed // (len(ARCS) * len(OPENINGS))) % 3,
    )

    opening = fill(OPENINGS[world.facts["opening_variant"]], facts)
    premise = fill(arc.premise, facts)
    problem = fill(arc.problem, facts)
    dialogue = fill(arc.dialogue, facts)
    twist = fill(arc.twist, facts)
    action = fill(arc.action, facts)
    result = fill(arc.result, facts)
    ending = fill(arc.ending, facts)

    structures = [
        [
            f"{opening} This was the day called \"{arc.title}.\"",
            f"{premise} {problem}",
            dialogue,
            twist,
            f"{action} {result}",
            f"At sunset, {ending}.",
        ],
        [
            opening,
            f"\"Will the parade go as planned?\" asked {params.hero}. {premise} Then {problem[0].lower() + problem[1:]}",
            dialogue,
            f"The answer was a heartwarming twist. {twist}",
            action,
            f"{result} At the end of the road, {ending}.",
        ],
        [
            f"The oldest picture of \"{arc.title}\" shows this: {ending}.",
            f"Before that picture was painted, {opening[0].lower() + opening[1:]} {premise}",
            f"The trouble came first. {problem}",
            dialogue,
            f"Nobody expected what happened next. {twist}",
            f"{action} {result}",
        ],
    ]
    story = "\n\n".join(structures[world.facts["structure_variant"]])

    prompts = [
        f"Write a heartwarming parade story in {params.setting} with {params.sailor} and {params.infantry_friend}.",
        "Create a child-facing story where a parade takes an unexpected but kind twist.",
        f"Tell a warm homecoming tale for a sailor and infantry friends in which everyone belongs.",
    ]
    story_qa = [
        QAItem(
            question=f"What problem did the sailor and infantry face in \"{arc.title}\"?",
            answer=arc.problem_answer,
        ),
        QAItem(
            question="What was the heartwarming twist in the parade?",
            answer=arc.twist_answer,
        ),
        QAItem(
            question=f"How did {params.hero}, the sailor, and the infantry help?",
            answer=arc.result_answer,
        ),
        QAItem(
            question=f"What final image closes \"{arc.title}\"?",
            answer=f"The story closes with {ending}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized group that moves together while people watch, often with music, flags, or costumes.",
        ),
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works or travels on the sea and helps care for a boat or ship.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers who serve and move on foot.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is an unexpected change that gives the story a new direction.",
        ),
        QAItem(
            question="Why can a parade feel heartwarming?",
            answer="A parade can feel heartwarming when people use it to welcome, thank, or include others.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


ASP_RULES = r"""
place(harbor_square).
place(lantern_pier).
place(maple_barracks_green).
feature(parade).
feature(sailor).
feature(infantry).
feature(twist).
heartwarming(P) :- place(P), feature(parade), feature(sailor), feature(infantry), feature(twist).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for setting in SETTING_REGISTRY:
        key = setting.lower().replace(" ", "_")
        lines.append(asp.fact("place", key))
    for feature in ("parade", "sailor", "infantry", "twist"):
        lines.append(asp.fact("feature", feature))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming parade story about a sailor and infantry friends."
    )
    parser.add_argument("--setting", choices=list(SETTING_REGISTRY))
    parser.add_argument("--hero")
    parser.add_argument("--sailor")
    parser.add_argument("--infantry-friend")
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
    hero = args.hero or rng.choice(["Mara", "Leo", "Nia", "Tess", "Owen"])
    sailor = args.sailor or rng.choice(["Sailor Finn", "Sailor Ada", "Sailor Tomas"])
    infantry_friend = args.infantry_friend or rng.choice(
        ["Corporal June", "Corporal Bea", "Sergeant Eli"]
    )
    if len({hero, sailor, infantry_friend}) != 3:
        raise StoryError("The hero, sailor, and infantry friend must have different names.")
    return StoryParams(
        setting=args.setting or rng.choice(list(SETTING_REGISTRY)),
        hero=hero,
        sailor=sailor,
        infantry_friend=infantry_friend,
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
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"{entity.name}: kind={entity.kind}, "
                f"meters={dict(entity.meters)}, memes={dict(entity.memes)}"
            )
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def python_places() -> list[str]:
    return sorted(setting.lower().replace(" ", "_") for setting in SETTING_REGISTRY)


def asp_places() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show heartwarming/1."))
    return sorted(set(asp.atoms(model, "heartwarming")))


def asp_verify() -> int:
    expected = {(place,) for place in python_places()}
    actual = set(asp_places())
    if expected == actual:
        print(f"OK: clingo gate matches python ({len(expected)} settings).")
        for index, params in enumerate(
            (
                StoryParams(setting=setting, hero="Mara", sailor="Sailor Finn", infantry_friend="Corporal June", seed=index)
                for index, setting in enumerate(SETTING_REGISTRY)
            )
        ):
            sample = generate(params)
            if not sample.story or "parade" not in sample.story.lower():
                print("Generation check failed.")
                return 1
        print("OK: generated stories passed.")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(expected - actual))
    print("clingo only:", sorted(actual - expected))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show heartwarming/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for item in asp_places():
            print(item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, setting in enumerate(SETTING_REGISTRY):
            samples.append(
                generate(
                    StoryParams(
                        setting=setting,
                        hero="Mara",
                        sailor="Sailor Finn",
                        infantry_friend="Corporal June",
                        seed=base_seed + index,
                    )
                )
            )
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as error:
                print(error)
                return
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
