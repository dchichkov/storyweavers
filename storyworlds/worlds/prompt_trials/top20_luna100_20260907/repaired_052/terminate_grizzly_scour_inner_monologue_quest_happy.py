#!/usr/bin/env python3
"""
A small standalone superhero storyworld about a grizzly threat, a brave quest,
and the choice to terminate danger without destroying what can be saved.
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
    kind: str
    type: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
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


@dataclass
class StoryParams:
    hero: str
    partner: str
    city: str
    quest: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    opening: str
    threat: str
    clue: str
    wrong_turn: str
    consequence: str
    inner_choice: str
    method: str
    reveal: str
    repair: str
    ending: str
    lesson: str


HEROES = ["Luna", "Mara", "Sol", "Nova", "Iris", "Tessa"]
PARTNERS = ["Pip", "Jo", "Milo", "Kira", "Beau", "Nia"]
CITIES = ["Moonbridge City", "Silver Harbor", "Starfall Town", "Aurora Heights"]

SCENARIOS = [
    Scenario(
        "clocktower",
        "the city clocktower began ringing at midnight even though its hands were still",
        "a grizzly shadow-beast was scouring the tower for the lost bell-heart",
        "the beast paused whenever it heard a child singing below",
        "chased the beast across the roof with a burst of bright power",
        "the frightened creature dropped the bell-heart into a storm drain",
        "followed the singing sound into the drain instead of attacking",
        "the shadow-beast was a lonely guardian trying to return the heart to its nest",
        "carried the heart together and built the guardian a safe nest beneath the tower",
        "the clock rang gently, and the guardian curled beside the warm bell-light",
        "a hero can terminate danger without terminating hope",
    ),
    Scenario(
        "river_lantern",
        "the river lanterns went dark before the town's night parade",
        "a grizzly river monster was scouring the banks and swallowing every blue flame",
        "one lantern glowed again when the monster heard its name",
        "fired a net of lightning to trap the monster",
        "the net tangled the parade bridge and stranded the children",
        "lowered the lightning and called to the creature by the name painted on its fin",
        "the monster was protecting a nest of tiny river lights under the bridge",
        "moved the nest to a quiet reed pool and relit the lanterns with moonwater",
        "the parade crossed a shining bridge while the little lights danced downstream",
        "listening can turn a frightening quest toward a happy ending",
    ),
    Scenario(
        "garden_roof",
        "the rooftop gardens began losing their golden flowers",
        "a grizzly cloud giant was scouring the roofs and pulling up every bright vine",
        "the giant always left one flower untouched beside a cracked skylight",
        "flew straight at the giant and ordered it to stop",
        "the wind from the hero's cape broke the skylight and chilled the gardens",
        "entered the quiet roof garden and examined the single flower",
        "the giant was gathering flowers to cover a nest of storm-birds",
        "helped make a flower shelter on an empty roof and repaired the skylight",
        "the storm-birds chirped above a city of blooming roofs",
        "careful courage can protect both a town and the creature that seems to threaten it",
    ),
    Scenario(
        "train_tunnel",
        "the silver train stopped before reaching the mountain tunnel",
        "a grizzly metal bear was scouring the tracks and tearing up signal lights",
        "its pawprints circled the one working signal instead of crossing it",
        "used a power beam to terminate the broken signals all at once",
        "the tunnel went dark and the train rolled toward a blocked rail",
        "read the pawprints and followed the bear to the old signal room",
        "the metal bear was an emergency machine trying to warn everyone about a cave-in",
        "repaired its warning bell and guided the train to a safe platform",
        "the bear rang three bright notes as passengers stepped into the sunrise",
        "a strange guardian may be asking for help through the damage it causes",
    ),
    Scenario(
        "museum_star",
        "the museum's tiny star vanished from its glass case on the morning of the school visit",
        "a grizzly comet creature was scouring the halls for the star",
        "dusty starprints led away from the case but never crossed the museum doors",
        "sealed every exit before asking why the creature had come",
        "the creature curled beneath a display and the frightened children could not leave",
        "opened one safe door and followed the starprints with the children",
        "the comet creature had carried the star away because it was its lost egg",
        "returned the egg to a warm sky nest and placed a harmless replica in the case",
        "the children watched the real star hatch above the museum dome",
        "the best victory protects a living promise instead of merely guarding a treasure",
    ),
    Scenario(
        "market_roar",
        "a deep roar shook the market just as the town's food carts opened",
        "a grizzly rock giant was scouring the stalls and knocking over empty crates",
        "it never touched a basket containing fresh apples",
        "rushed in and tried to terminate the roar with a sonic blast",
        "the blast scattered apples into the street and made the giant cry louder",
        "offered the giant one apple and waited for its answer",
        "the giant had a cracked stone tooth and was searching for fruit to soothe it",
        "used a gentle strength beam to mend the tooth and rebuild the stalls",
        "the market opened with apple pies, music, and a grateful stone smile",
        "kindness can be the strongest superhero power",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero Story world with a grizzly quest and happy ending."
    )
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--partner", choices=PARTNERS)
    parser.add_argument("--city", choices=CITIES)
    parser.add_argument("--quest", choices=[s.key for s in SCENARIOS])
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
    partner = args.partner or rng.choice([p for p in PARTNERS if p != hero])
    city = args.city or rng.choice(CITIES)
    quest = args.quest or rng.choice(SCENARIOS).key
    return StoryParams(hero=hero, partner=partner, city=city, quest=quest)


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("style", "superhero_story"),
            asp.fact("feature", "inner_monologue"),
            asp.fact("feature", "quest"),
            asp.fact("feature", "happy_ending"),
            asp.fact("seed_word", "terminate"),
            asp.fact("seed_word", "grizzly"),
            asp.fact("seed_word", "scour"),
            asp.fact("rule", "protect_life"),
        ]
    )


ASP_RULES = r"""
safe_choice :- feature(inner_monologue), feature(quest), rule(protect_life).
#show style/1.
#show feature/1.
#show seed_word/1.
#show safe_choice/0.
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    features = sorted(asp.atoms(model, "feature"))
    words = sorted(asp.atoms(model, "seed_word"))
    if features == [("happy_ending",), ("inner_monologue",), ("quest",)] and words == [
        ("grizzly",),
        ("scour",),
        ("terminate",),
    ]:
        print("OK: ASP twin contains the required features and seed words.")
        return 0
    print("MISMATCH: ASP twin is missing required facts.")
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.hero not in HEROES:
        raise StoryError(f"Unknown hero: {params.hero}")
    if params.partner not in PARTNERS:
        raise StoryError(f"Unknown partner: {params.partner}")
    if params.hero == params.partner:
        raise StoryError("The hero and partner must have different names.")
    scenario = next((s for s in SCENARIOS if s.key == params.quest), None)
    if scenario is None:
        raise StoryError(f"Unknown quest: {params.quest}")

    world = World()
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type="superhero",
            label=params.hero,
            location=params.city,
            meters={"courage": 0.7, "power": 0.8},
            memes={"responsibility": 0.8, "doubt": 0.2},
        )
    )
    partner = world.add(
        Entity(
            id="partner",
            kind="character",
            type="helper",
            label=params.partner,
            location=params.city,
            meters={"speed": 0.6, "observation": 0.9},
            memes={"trust": 0.7, "worry": 0.3},
        )
    )
    threat = world.add(
        Entity(
            id="grizzly_threat",
            kind="creature",
            type="grizzly_guardian",
            label="the grizzly guardian",
            location=params.city,
            meters={"danger": 0.8, "fear": 0.7},
            memes={"loneliness": 0.8, "purpose": 0.6},
        )
    )
    world.facts.update(
        quest=scenario.key,
        city=params.city,
        feature="Inner Monologue, Quest, Happy Ending",
        seed_words=["terminate", "grizzly", "scour"],
        threat=scenario.threat,
    )

    world.say(
        f"In {params.city}, {params.hero} wore a bright cape and watched over the streets."
    )
    world.say(f"One evening, {scenario.opening}.")
    world.say(
        f'"There is a grizzly trail over there," {params.partner} said. '
        f'"Then our quest begins," {params.hero} replied.'
    )

    world.para()
    world.say(f"The trail led to a frightening sight: {scenario.threat}.")
    world.say(
        f"The guardian was scouring the place, and its growl made windows tremble."
    )
    world.say(
        f"{params.hero} raised a glowing hand. Inside, {hero.label} thought, "
        f'"I can terminate this danger now. But if I strike first, who might I hurt?"'
    )
    world.say(f'"Look at the clues," {params.partner} urged. "{scenario.clue}."')

    world.para()
    world.say(f"At first, {params.hero} {scenario.wrong_turn}.")
    world.say(f"Then {scenario.consequence}.")
    world.say(
        f'"Stop!" {params.partner} called. "A hero protects people, even when the answer is hard."'
    )
    world.say(
        f"{params.hero} lowered the power and chose to {scenario.method}."
    )
    world.say(f"The careful choice revealed that {scenario.reveal}.")

    world.para()
    world.say(f"{params.hero} and {params.partner} worked side by side to {scenario.repair}.")
    world.say(f"The grizzly guardian's danger faded, and the city grew quiet.")
    world.say(
        f'"You did not give up your strength," {params.partner} said. '
        f'"You gave it a wiser purpose," {params.hero} answered.'
    )
    world.say(f"At last, {scenario.ending}.")
    world.say(f"The quest taught them that {scenario.lesson}")

    hero.meters["courage"] = 1.0
    hero.memes["responsibility"] = 1.0
    hero.memes["doubt"] = 0.0
    partner.memes["trust"] = 1.0
    threat.meters["danger"] = 0.0
    threat.meters["fear"] = 0.1
    threat.memes["loneliness"] = 0.0
    world.facts.update(resolution="happy ending", danger_terminated=True)

    prompts = [
        f"Write a Superhero Story about {params.hero} protecting {params.city} from a grizzly threat.",
        f"Tell a quest where a hero must scour clues before deciding whether to terminate danger.",
        "Include Inner Monologue and end with a Happy Ending that protects everyone.",
    ]
    story_qa = [
        QAItem(
            question=f"What quest did {params.hero} and {params.partner} begin?",
            answer=f"They began a quest in {params.city} after learning that {scenario.opening}.",
        ),
        QAItem(
            question="What made the grizzly guardian seem dangerous?",
            answer=f"It was dangerous because {scenario.threat}, and its actions made people afraid.",
        ),
        QAItem(
            question="What did the hero think before acting?",
            answer=f"The hero wondered whether using power immediately would hurt someone, so the hero looked for clues before choosing.",
        ),
        QAItem(
            question="How did the heroes solve the problem?",
            answer=f"They noticed that {scenario.clue}, then chose to {scenario.method}. They discovered that {scenario.reveal} and {scenario.repair}.",
        ),
        QAItem(
            question="Why was the ending happy?",
            answer=f"It was happy because {scenario.ending}. The heroes protected the city without destroying a creature that needed help.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a superhero quest?",
            answer="A superhero quest is a difficult mission in which a brave character follows clues, faces danger, and protects others.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is a character's private thought shown to the reader, such as a careful question before making a choice.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending shows that the main danger has been resolved and that people or creatures are safer, wiser, or reunited.",
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for entity in sample.world.entities.values():
            print(
                f"  {entity.id}: {entity.type} location={entity.location} "
                f"meters={entity.meters} memes={entity.memes}"
            )
        print(f"  facts: {sample.world.facts}")
    if qa:
        print("\n== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show feature/1."))
        return
    if args.asp:
        import asp

        print("\n".join(str(atom) for atom in asp.one_model(asp_program())))
        if not args.verify:
            return
    if args.verify:
        code = asp_verify()
        if code:
            sys.exit(code)
        test = generate(
            StoryParams(
                hero="Luna",
                partner="Pip",
                city="Moonbridge City",
                quest="clocktower",
                seed=1,
            )
        )
        if not test.story or "Happy Ending" in test.story:
            print("MISMATCH: generated story validation failed.")
            sys.exit(1)
        print("OK: generated story validation passed.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "Pip", "Moonbridge City", "clocktower", 101),
            StoryParams("Mara", "Jo", "Silver Harbor", "river_lantern", 202),
            StoryParams("Sol", "Kira", "Aurora Heights", "market_roar", 303),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        attempt = 0
        target = max(1, args.n)
        while len(samples) < target:
            attempt += 1
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero} in {sample.params.city}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
