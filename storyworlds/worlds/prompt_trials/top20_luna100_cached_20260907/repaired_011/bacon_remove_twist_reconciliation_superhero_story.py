#!/usr/bin/env python3
"""
A small stand-alone superhero storyworld about bacon, a surprising twist,
and reconciliation.

Seed premise:
A young superhero must remove a runaway bacon banner from a city tower.
The rescue goes wrong when a rival hero appears, but an honest conversation
turns the twist into teamwork and repairs their friendship.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    hero: str
    partner: str
    rival: str
    city: str
    bacon: str
    problem: int = 0
    premise: int = 0
    twist: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


HEROES = ["Luna", "Bolt", "Comet", "Nova", "Mira", "Zip"]
PARTNERS = ["Pip", "Rex", "Daisy", "Tess", "Kiko", "Sunny"]
RIVALS = ["Captain Crinkle", "Shadow Spark", "Dr. Whirl", "The Velvet Viper"]
CITIES = ["Moonbeam City", "Star Harbor", "Brighton Heights", "Rocket Square"]
BACONS = ["a giant bacon banner", "a flying bacon sign", "a bacon-shaped rescue flag", "a bundle of crispy bacon balloons"]

PREMISES = [
    "{hero} was the newest superhero in {city}, where even breakfast could become an emergency.",
    "At sunrise, {hero} and {partner} patrolled {city} beneath a sky pink as warm toast.",
    "{hero} had promised {partner} a quiet morning, but a bacon-shaped alarm began flapping above the tallest tower.",
    "The people of {city} were preparing a breakfast parade when {hero} heard a loud, buttery whoosh.",
    "{hero} loved saving the day, but {partner} knew that the hero still needed practice listening before leaping.",
    "A friendly breakfast festival filled {city} with music, napkins, and the smell of sizzling bacon.",
]

PROBLEMS = [
    {
        "lead": "A gust had lifted {bacon} onto the clock tower, where it wrapped around the hands.",
        "trigger": "When {hero} flew closer, the banner snapped loose and dragged a string of parade lights behind it.",
        "risk": "If the lights fell, the festival crowd below could be frightened and the tower clock could stop.",
        "action": "{hero} slowed down while {partner} pointed to a safe knot near the banner's corner.",
        "resolution": "{hero} removed the banner one careful loop at a time and lowered the lights into {partner}'s waiting arms.",
        "cause": "a gust wrapped the bacon banner around the clock hands and pulled parade lights loose",
        "deed": "slowed down and followed the safe knot that the partner spotted",
        "result": "the bacon banner was removed without dropping the parade lights",
    },
    {
        "lead": "Someone had tied {bacon} to a flock of helium balloons above the town square.",
        "trigger": "The balloons tugged toward a rooftop chimney, and one string began to wind around a weather vane.",
        "risk": "A hard tug might tear the banner or send the balloons into the busy street.",
        "action": "{hero} asked {partner} to clear the square while {hero} guided the balloons toward an empty rooftop.",
        "resolution": "Once the rooftop was clear, {hero} removed the tangled string and brought the banner back to the breakfast stage.",
        "cause": "the bacon banner's balloons tangled with a rooftop weather vane",
        "deed": "cleared the square and guided the balloons toward an empty rooftop",
        "result": "the tangled string was removed and the banner returned safely",
    },
    {
        "lead": "{hero} found {bacon} caught on the city's giant welcome arch.",
        "trigger": "A passing delivery drone pulled the banner tight and began carrying the arch's loose ribbon away.",
        "risk": "The banner could tear, and the drone might lose its path over the crowd.",
        "action": "{hero} used a gentle breeze to turn the drone toward an empty park while {partner} waved people back.",
        "resolution": "{hero} removed the banner from the arch, and the drone landed safely beside a quiet fountain.",
        "cause": "a delivery drone pulled the bacon banner tight against the welcome arch",
        "deed": "guided the drone away while the partner kept people back",
        "result": "the banner came free and the drone landed safely",
    },
    {
        "lead": "{hero} discovered {bacon} stuck to the side of a slow-moving parade float.",
        "trigger": "The float's wheels rolled toward a puddle, and the banner began soaking up water.",
        "risk": "The heavy banner might pull the float off course and splash the musicians.",
        "action": "{hero} called for a pause, and {partner} placed bright cones around the float.",
        "resolution": "Together they removed the wet banner, and the musicians restarted with a cheerful drumbeat.",
        "cause": "the bacon banner became wet and heavy on a moving parade float",
        "deed": "called for a pause while the partner marked a safe space",
        "result": "the banner was removed before it could pull the float off course",
    },
]

TWISTS = [
    {
        "line": "{rival} swooped down and shouted, 'I was trying to help! I tied the banner there so the wind could dry it.'",
        "truth": "The twist was that {rival} had not meant to cause trouble; they had misunderstood the festival plan.",
        "reply": "{hero} lowered their shield and said, 'You should have told us. Helping works better when we share the plan.'",
    },
    {
        "line": "{rival} stepped from behind a chimney and admitted, 'I moved the banner because I thought everyone wanted a surprise.'",
        "truth": "The surprising truth was that the rival wanted to make the festival special, but had chosen a dangerous place.",
        "reply": "{partner} said, 'A surprise is only good when people are safe.' {rival} nodded and offered both hands.",
    },
    {
        "line": "At the last moment, {rival} caught the loose end and called, 'Wait! The banner is hiding a message.'",
        "truth": "The twist revealed a thank-you note from the festival cooks, who had asked the rival to decorate the tower.",
        "reply": "{hero} said, 'We can save the note and still remove the banner.' The rival agreed and held the corner steady.",
    },
    {
        "line": "{rival} looked embarrassed and said, 'I thought you blamed me for every silly accident, so I tried to fix this alone.'",
        "truth": "The twist was not a villain's trick but a lonely mistake caused by a friendship that had grown quiet.",
        "reply": "{hero} answered, 'I should have asked what happened instead of guessing.' The rival's shoulders finally relaxed.",
    },
]

ENDINGS = [
    "At the breakfast festival, {hero}, {partner}, and {rival} hung the cleaned banner low enough for everyone to see. The first slice of bacon on the stage was shared three ways.",
    "The clock struck noon, and the repaired parade lights blinked like friendly stars. {hero} gave {rival} the safest job: holding the ladder.",
    "Before the crowd went home, {partner} painted a small heart on the banner. It floated over {city} as a sign that a mistake could become a new beginning.",
    "{hero} and {rival} marched together behind the breakfast float. Whenever the banner flapped, they checked the knots together.",
    "The festival ended with a warm plate of bacon and a promise from all three heroes: next time, they would ask first and leap second.",
    "As sunset colored the tower gold, {rival} returned the spare rope and {hero} returned a smile. The city cheered for teamwork, not just super speed.",
]

ASP_RULES = r"""
#show valid/4.
#show valid_story/5.

hero(H) :- hero_name(H).
partner(P) :- partner_name(P).
rival(R) :- rival_name(R).
city(C) :- city_name(C).
bacon(B) :- bacon_name(B).

valid(H, P, R, C) :- hero_name(H), partner_name(P), rival_name(R), city_name(C), H != P, H != R, P != R.
valid_story(H, P, R, C, B) :- valid(H, P, R, C), bacon_name(B).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for value in HEROES:
        lines.append(asp.fact("hero_name", value))
    for value in PARTNERS:
        lines.append(asp.fact("partner_name", value))
    for value in RIVALS:
        lines.append(asp.fact("rival_name", value))
    for value in CITIES:
        lines.append(asp.fact("city_name", value))
    for value in BACONS:
        lines.append(asp.fact("bacon_name", value))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    return [
        (hero, partner, rival, city, bacon)
        for hero in HEROES
        for partner in PARTNERS
        for rival in RIVALS
        for city in CITIES
        for bacon in BACONS
        if len({hero, partner, rival}) == 3
    ]


def asp_valid_count() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/5."))
    return len(asp.atoms(model, "valid_story"))


def asp_verify() -> int:
    expected = len(valid_combos())
    actual = asp_valid_count()
    if expected == actual:
        print(f"OK: clingo gate matches valid_combos() ({expected} combinations).")
        return 0
    print(f"MISMATCH: Python found {expected}; clingo found {actual}.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero storyworld about bacon, a twist, and reconciliation."
    )
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--partner", choices=PARTNERS)
    parser.add_argument("--rival", choices=RIVALS)
    parser.add_argument("--city", choices=CITIES)
    parser.add_argument("--bacon", choices=BACONS)
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
    hero = args.hero or rng.choice(HEROES)
    partner = args.partner or rng.choice(PARTNERS)
    rival = args.rival or rng.choice(RIVALS)
    if len({hero, partner, rival}) != 3:
        raise StoryError("The hero, partner, and rival must have different names.")
    return StoryParams(
        hero=hero,
        partner=partner,
        rival=rival,
        city=args.city or rng.choice(CITIES),
        bacon=args.bacon or rng.choice(BACONS),
        problem=rng.randrange(len(PROBLEMS)),
        premise=rng.randrange(len(PREMISES)),
        twist=rng.randrange(len(TWISTS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def apply_seeded_structure(params: StoryParams, seed: int) -> None:
    params.problem = seed % len(PROBLEMS)
    params.premise = (seed // len(PROBLEMS)) % len(PREMISES)
    params.twist = (seed // 3) % len(TWISTS)
    params.ending = (seed // 5) % len(ENDINGS)


def generate(params: StoryParams) -> StorySample:
    values = {
        "hero": params.hero,
        "partner": params.partner,
        "rival": params.rival,
        "city": params.city,
        "bacon": params.bacon,
    }
    problem = PROBLEMS[params.problem % len(PROBLEMS)]
    twist = TWISTS[params.twist % len(TWISTS)]

    world = World()
    hero = world.add(Entity(params.hero, "character", params.hero, memes={"courage": 0.0}))
    partner = world.add(Entity(params.partner, "character", params.partner, memes={"trust": 0.0}))
    rival = world.add(Entity(params.rival, "character", params.rival, memes={"loneliness": 0.0}))
    banner = world.add(
        Entity(
            "bacon_banner",
            "object",
            params.bacon,
            meters={"height": 1.0, "tangle": 1.0},
            memes={"danger": 1.0},
        )
    )
    city = world.add(Entity("city", "place", params.city, memes={"cheer": 0.0}))

    world.say(PREMISES[params.premise % len(PREMISES)].format(**values))
    world.say(
        f"{hero.label} wore a bright cape, while {partner.label} carried a rescue rope and watched the crowded streets below."
    )
    world.say(problem["lead"].format(**values))

    world.para()
    world.say(problem["trigger"].format(**values))
    world.say(problem["risk"].format(**values))
    world.say(f'"Stay back!" called {partner.label}. "{hero.label}, wait for my signal."')
    world.say(f'"I can remove it quickly," said {hero.label}. "{partner.label}, what do you see?"')
    world.say(f'"The knot is safer on the left," answered {partner.label}. "Follow my voice."')
    world.say(problem["action"].format(**values))

    banner.meters["tangle"] = 0.5
    hero.memes["courage"] = 1.0
    partner.memes["trust"] = 1.0

    world.para()
    world.say(twist["line"].format(**values))
    world.say(twist["truth"].format(**values))
    world.say(twist["reply"].format(**values))
    world.say(problem["resolution"].format(**values))
    world.say(
        f'"I am sorry I guessed instead of asking," said {hero.label}. "{rival.label}, will you help us finish the festival?"'
    )
    world.say(
        f'"Yes," said {rival.label}. "{partner.label}, {hero.label}, and I can make a safer plan together."'
    )

    banner.meters["height"] = 0.0
    banner.meters["tangle"] = 0.0
    banner.memes["danger"] = 0.0
    rival.memes["loneliness"] = 0.0
    partner.memes["trust"] = 1.0
    city.memes["cheer"] = 1.0

    world.say(ENDINGS[params.ending % len(ENDINGS)].format(**values))

    world.facts.update(
        hero=params.hero,
        partner=params.partner,
        rival=params.rival,
        city=params.city,
        bacon=params.bacon,
        problem=params.problem % len(PROBLEMS),
        cause=problem["cause"],
        helpful_action=problem["deed"],
        result=problem["result"],
        twist=twist["truth"].format(**values),
        reconciliation=True,
        resolved=True,
    )

    prompts = [
        "Write a child-friendly superhero story involving bacon, a dangerous problem, a surprising twist, and reconciliation.",
        f"Tell a superhero story in which {params.hero} must remove {params.bacon} while working with {params.partner} and {params.rival}.",
        f"Write a story about {params.hero} learning that honest conversation can turn a bacon rescue into reconciliation.",
    ]

    story_qa = [
        QAItem(
            question="Who tried to solve the bacon problem?",
            answer=f"{params.hero} tried to solve the problem with help from {params.partner}, and {params.rival} joined them after the twist.",
        ),
        QAItem(
            question="Why was the bacon object dangerous?",
            answer=f"It was dangerous because {problem['cause']}. The heroes had to protect the people and equipment below.",
        ),
        QAItem(
            question="What did the hero do to help?",
            answer=f"{params.hero} {problem['deed']}. This careful choice made it possible to remove the bacon object safely.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {twist['truth'].format(**values)}",
        ),
        QAItem(
            question="How did reconciliation happen?",
            answer=f"{params.hero} admitted that guessing had caused trouble, and {params.rival} agreed to help make a safer plan together.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a character with unusual abilities or courage who uses those gifts to help others.",
        ),
        QAItem(
            question="What does it mean to remove something?",
            answer="To remove something means to take it away from where it is or separate it from another thing.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change or discovery that makes the story turn in a new direction.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is the process of making peace and repairing a relationship after people have been hurt or disagreed.",
        ),
        QAItem(
            question="Why should rescuers communicate?",
            answer="Rescuers should communicate so they can share what they know, avoid dangerous guesses, and choose safe actions together.",
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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        pieces = []
        if entity.meters:
            pieces.append(f"meters={entity.meters}")
        if entity.memes:
            pieces.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id:16} ({entity.kind:9}) {' '.join(pieces)}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(
            hero="Luna",
            partner="Pip",
            rival="Captain Crinkle",
            city="Moonbeam City",
            bacon="a giant bacon banner",
            problem=0,
            premise=0,
            twist=0,
            ending=0,
        ),
        StoryParams(
            hero="Bolt",
            partner="Tess",
            rival="Shadow Spark",
            city="Star Harbor",
            bacon="a flying bacon sign",
            problem=1,
            premise=2,
            twist=1,
            ending=2,
        ),
        StoryParams(
            hero="Comet",
            partner="Rex",
            rival="Dr. Whirl",
            city="Brighton Heights",
            bacon="a bacon-shaped rescue flag",
            problem=2,
            premise=3,
            twist=2,
            ending=3,
        ),
        StoryParams(
            hero="Nova",
            partner="Daisy",
            rival="The Velvet Viper",
            city="Rocket Square",
            bacon="a bundle of crispy bacon balloons",
            problem=3,
            premise=5,
            twist=3,
            ending=5,
        ),
    ]


CURATED = build_curated()


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
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{asp_valid_count()} compatible hero-team combinations.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            apply_seeded_structure(params, seed)
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
            header = f"### {sample.params.hero}: bacon rescue in {sample.params.city}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
