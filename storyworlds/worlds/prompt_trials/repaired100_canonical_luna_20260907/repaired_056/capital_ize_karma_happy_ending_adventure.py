#!/usr/bin/env python3
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = {
    "whispering pass": {
        "setting": "the Whispering Pass",
        "hazard": "a loose stone bridge",
        "landmark": "a red pennant",
    },
    "moonlit canyon": {
        "setting": "the Moonlit Canyon",
        "hazard": "a narrow ledge",
        "landmark": "a silver bell",
    },
    "sunrise marsh": {
        "setting": "the Sunrise Marsh",
        "hazard": "deep mud",
        "landmark": "a blue lantern",
    },
    "cloudstep hill": {
        "setting": "Cloudstep Hill",
        "hazard": "a rushing stream",
        "landmark": "an old wooden sign",
    },
}

CHARACTERS = ("Luna", "Milo", "Nia", "Tavi", "Arlo", "Suri", "Pip", "Mara")
MOODS = ("brave", "curious", "careful", "hopeful")
CAPITAL_WORDS = ("Moonstone", "Starbell", "Sunseed", "Cloudberry")
KARMA_DEEDS = (
    "returned a lost compass",
    "shared the last dry blanket",
    "helped a tired traveler",
    "freed a bird from a thorny vine",
    "carried water to a thirsty goat",
)

ADVENTURES = (
    {
        "name": "the vanished capital",
        "opening": "Luna was following an old trail when the letters on her map faded into tiny marks.",
        "clue": "a carved stone showed the word Moonstone with its first letter shining brightly",
        "mistake": "thought capital-ize meant shouting every word to make the mountain listen",
        "turn": "capital-ize meant to give the important name a capital letter, not to make a loud noise",
        "action": "wrote Moonstone correctly on the map",
        "help": "a small trail fox appeared and led them around the broken bridge",
        "ending": "At sunset, the Moonstone gate opened, and warm lanterns welcomed every traveler home.",
    },
    {
        "name": "the karma trail",
        "opening": "Luna and her companion reached a fork where three paths vanished beneath silver grass.",
        "clue": "a grateful goat nudged a dropped compass toward the path marked with a painted K",
        "mistake": "wondered whether karma was a spell that would choose the safest road without any kind action",
        "turn": "karma was the good that returned after someone had helped another being",
        "action": "followed the compass and stopped to mend the goat's loose bell strap",
        "help": "the goat then tugged a vine away from a hidden stepping stone",
        "ending": "They reached the bright campfire, and the goat's bell rang like a tiny cheer for their happy ending.",
    },
    {
        "name": "the stormy summit",
        "opening": "A sudden storm trapped Luna below a summit where the adventure's final flag waited.",
        "clue": "the flag's sign said Starbell, but the first letter had been rubbed away",
        "mistake": "believed capital-ize was a secret mountain command that required a dangerous climb",
        "turn": "the missing capital letter mattered because Starbell was the proper name of the summit",
        "action": "restored the capital S on the trail sign",
        "help": "a climber Luna had earlier helped returned with a strong rope",
        "ending": "Together they reached Starbell after the rain, and the repaired flag danced above a clear valley.",
    },
    {
        "name": "the marsh of return",
        "opening": "Luna crossed a marsh searching for the Sunseed, a tiny treasure said to glow at dawn.",
        "clue": "a duck pointed with its beak toward a sign reading Sunseed",
        "mistake": "thought karma meant waiting for luck while leaving the duck to struggle in the reeds",
        "turn": "karma began when Luna chose to help before asking for a reward",
        "action": "pulled the duck free and rewrote sunseed as Sunseed on the treasure map",
        "help": "the duck led her through shallow water to a dry patch",
        "ending": "At dawn, the Sunseed glowed in Luna's hands, and the grateful duck splashed beside her.",
    },
    {
        "name": "the cloudstep rescue",
        "opening": "High on Cloudstep Hill, Luna heard a traveler calling from beside a rushing stream.",
        "clue": "the traveler carried a sign labeled Cloudberry, with its capital C scratched out",
        "mistake": "thought capital-ize was only a fancy word for climbing higher",
        "turn": "capital-ize meant fixing the first letter of a special name so everyone could recognize it",
        "action": "repaired the sign and tied a safe line across the stream",
        "help": "the traveler had a second rope and helped Luna secure the line",
        "ending": "They crossed safely, and the Cloudberry camp greeted them with hot soup and bright songs.",
    },
)

DIALOGUES = (
    ("“I can guess what this word means,” Luna said.", "“A guess is a beginning,” her friend replied, “but the trail can give us proof.”"),
    ("“Should we rush ahead?” Luna asked.", "“Not before we see who might need our help,” said her companion."),
    ("“Capital-ize sounds like a spell,” Luna said.", "“Maybe it is a clue,” answered her friend, “so let us use it carefully.”"),
    ("“Will good choices really come back to us?” Luna asked.", "“We cannot demand a reward,” said her companion, “but kindness can change the path.”"),
    ("“The mountain looks too difficult,” Luna whispered.", "“Then we will solve one safe step at a time,” her friend said."),
)

OPENINGS = (
    "The adventure began beneath a sky full of traveling clouds.",
    "Before breakfast, Luna found a strange mark on the edge of her map.",
    "A distant bell called from beyond the familiar trail.",
    "The old path promised a surprise to anyone who watched carefully.",
    "Luna packed a rope, a notebook, and enough courage for one more ridge.",
)

ASP_RULES = r"""
kind(capital_ize).
kind(karma).
kind(adventure).
kind(happy_ending).

feature(capital_ize) :- kind(capital_ize).
feature(karma) :- kind(karma).
feature(adventure) :- kind(adventure).
feature(happy_ending) :- kind(happy_ending).

setting(whispering_pass).
setting(moonlit_canyon).
setting(sunrise_marsh).
setting(cloudstep_hill).

supports(P, capital_ize) :- setting(P).
supports(P, karma) :- setting(P).
safe_resolution(P, happy_ending) :- setting(P).
complete_adventure(P) :- supports(P, capital_ize), supports(P, karma), safe_resolution(P, happy_ending).

#show supports/2.
#show safe_resolution/2.
#show complete_adventure/1.
"""


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    location: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    carried_by: Optional[str] = None


@dataclass
class StoryParams:
    place: str
    hero: str
    companion: str
    mood: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
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
    parser = argparse.ArgumentParser(description="An adventure about capital-ize, karma, and a happy ending.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--hero")
    parser.add_argument("--companion")
    parser.add_argument("--mood", choices=MOODS)
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


def asp_facts() -> str:
    import asp
    return "\n".join(
        asp.fact("setting", place.replace(" ", "_"))
        for place in PLACES
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show complete_adventure/1."))
    actual = set(asp.atoms(model, "complete_adventure"))
    expected = {(place.replace(" ", "_"),) for place in PLACES}
    if actual != expected:
        print("MISMATCH:")
        print("only in clingo:", sorted(actual - expected))
        print("only in Python:", sorted(expected - actual))
        return 1
    for params in curated_params():
        sample = generate(params)
        if not sample.story or "happy ending" not in sample.story.lower():
            print("Generated story verification failed.")
            return 1
    print(f"OK: ASP/Python parity and generated stories verified ({len(actual)} settings).")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(CHARACTERS)
    companion = args.companion or rng.choice([name for name in CHARACTERS if name != hero])
    mood = args.mood or rng.choice(MOODS)
    if place not in PLACES:
        raise StoryError(f"Unknown place: {place}")
    if hero == companion:
        raise StoryError("The hero and companion must have different names.")
    return StoryParams(place=place, hero=hero, companion=companion, mood=mood, seed=args.seed)


def story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    raw = "|".join((params.place, params.hero, params.companion, params.mood))
    return int.from_bytes(hashlib.blake2b(raw.encode(), digest_size=8).digest(), "big")


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.hero == params.companion:
        raise StoryError("The hero and companion must have different names.")

    seed = story_seed(params)
    rng = random.Random(seed)
    place = PLACES[params.place]
    adventure = ADVENTURES[seed % len(ADVENTURES)]
    dialogue = DIALOGUES[(seed // len(ADVENTURES)) % len(DIALOGUES)]
    opening = OPENINGS[(seed // (len(ADVENTURES) * len(DIALOGUES))) % len(OPENINGS)]
    deed = KARMA_DEEDS[(seed // 17) % len(KARMA_DEEDS)]
    capital_word = CAPITAL_WORDS[(seed // 31) % len(CAPITAL_WORDS)]

    hero = Entity(
        id=params.hero,
        kind="character",
        label="adventurer",
        location=params.place,
        meters={"energy": 1.0, "safety": 0.7},
        memes={"courage": 0.8, "kindness": 0.5},
    )
    companion = Entity(
        id=params.companion,
        kind="character",
        label="companion",
        location=params.place,
        meters={"energy": 0.9, "safety": 0.7},
        memes={"caution": 0.8, "kindness": 0.6},
    )
    map_entity = Entity(
        id="map",
        kind="tool",
        label="an old trail map",
        location=params.place,
        carried_by=params.hero,
        meters={"condition": 0.8},
        memes={"guidance": 0.7},
    )
    world = World(place=place["setting"], entities={
        hero.id: hero,
        companion.id: companion,
        map_entity.id: map_entity,
    })

    world.say(opening)
    world.say(
        f"{params.hero}, a {params.mood} adventurer, entered {place['setting']} with "
        f"{params.companion} and a map marked with the word {capital_word}."
    )
    world.say(f"The trail led toward {place['hazard']}, where the {place['landmark']} could be seen beyond the danger.")
    world.say(adventure["opening"])

    world.para()
    world.say(f"{params.hero} had recently {deed}, so the pair promised to notice anyone who needed help.")
    world.say(adventure["clue"])
    world.say(adventure["mistake"] + ".")
    world.say(f"{dialogue[0]} {dialogue[1]}")
    world.say(f"They tested the map instead of rushing, and the first safe route became clear.")

    world.para()
    world.say(f"Then the turning clue arrived: {adventure['turn']}.")
    world.say(f"With that knowledge, {params.hero} {adventure['action']}.")
    world.say(f"At the same moment, {adventure['help']}.")
    world.say("That was karma in action: an earlier kindness had become help on the difficult trail, not by magic, but because kindness had built trust.")
    world.say(f"Together, the adventurers moved safely past {place['hazard']}.")

    world.para()
    world.say(f"They reached the landmark and found the path beyond it open.")
    world.say(adventure["ending"])
    world.say("The adventure ended happily because careful thinking and kindness had changed what seemed like an impossible journey.")

    hero.meters.update(energy=0.65, safety=1.0)
    companion.meters.update(energy=0.7, safety=1.0)
    hero.memes.update(courage=1.0, understanding=1.0, karma=1.0)
    companion.memes.update(trust=1.0, understanding=1.0)
    map_entity.memes["corrected_name"] = 1.0

    world.trace = [
        f"entered:{params.place}",
        f"noticed:{adventure['clue']}",
        f"misunderstood:{adventure['mistake']}",
        f"learned:{adventure['turn']}",
        f"help_received:{adventure['help']}",
        "resolved:happy ending",
    ]
    world.facts = {
        "place": params.place,
        "hero": params.hero,
        "companion": params.companion,
        "adventure": adventure["name"],
        "capital_ize": adventure["turn"],
        "karma": "kindness returned through trust and helpful action",
        "resolution": "happy ending",
    }

    prompts = [
        f"Write an Adventure story in {place['setting']} using capital-ize and karma.",
        f"Show how {params.hero} learns what capital-ize means and reaches a Happy Ending.",
        f"Write a child-friendly adventure where an earlier kindness creates karma during a dangerous moment.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {params.hero} first misunderstand about capital-ize?",
            answer=f"{params.hero} {adventure['mistake']}. The later clue showed that {adventure['turn']}.",
        ),
        QAItem(
            question="How did karma appear in the adventure?",
            answer=f"Karma appeared when {adventure['help']}. Earlier kindness had created trust, so help returned when it was needed.",
        ),
        QAItem(
            question=f"What did {params.hero} do after understanding the clue?",
            answer=f"{params.hero} {adventure['action']}. This made the trail clearer and allowed the adventurers to continue safely.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily: {adventure['ending']} The adventurers were safe and their goal was reached.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What does capital-ize mean in this storyworld?",
            answer="Capital-ize means writing the first letter of an important name as a capital letter so readers can recognize that special name.",
        ),
        QAItem(
            question="What is karma?",
            answer="Karma is the idea that helpful or harmful actions can lead to consequences that return later, often through the trust or trouble those actions create.",
        ),
        QAItem(
            question="Why should an adventurer slow down near a hazard?",
            answer="An adventurer should slow down near a hazard to inspect the route, protect companions, and choose a safe action instead of rushing.",
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
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            details = [f"kind={entity.kind}", f"label={entity.label}"]
            if entity.location:
                details.append(f"location={entity.location}")
            if entity.carried_by:
                details.append(f"carried_by={entity.carried_by}")
            if entity.meters:
                details.append(f"meters={entity.meters}")
            if entity.memes:
                details.append(f"memes={entity.memes}")
            print(f"  {entity.id}: " + ", ".join(details))
        for event in sample.world.trace:
            print(f"  event: {event}")
    if qa:
        print("\n== prompts ==")
        for number, prompt in enumerate(sample.prompts, 1):
            print(f"{number}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def curated_params() -> list[StoryParams]:
    return [
        StoryParams("whispering pass", "Luna", "Milo", "brave", 11),
        StoryParams("moonlit canyon", "Nia", "Arlo", "careful", 23),
        StoryParams("sunrise marsh", "Suri", "Pip", "hopeful", 37),
        StoryParams("cloudstep hill", "Mara", "Tavi", "curious", 49),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show complete_adventure/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show supports/2.\n#show safe_resolution/2.\n#show complete_adventure/1."))
        print(asp.atoms(model, "supports"))
        print(asp.atoms(model, "safe_resolution"))
        print(asp.atoms(model, "complete_adventure"))
        return

    if args.all:
        samples = [generate(params) for params in curated_params()]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index * 7919)
            params = resolve_params(args, rng)
            params.seed = base_seed + index * 7919
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
