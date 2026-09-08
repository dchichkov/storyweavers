#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402

WORLD_NAME = "terminate_grizzly_scour_inner_monologue_quest_happy"

PLACES = {
    "river city": {
        "setting": "River City",
        "feature": "bright rooftops and a windy riverwalk",
        "grizzly_spots": ["old zoo hill", "the riverside tunnel", "the clocktower alley"],
    },
    "sunset square": {
        "setting": "Sunset Square",
        "feature": "a glowing plaza with comic-book billboards",
        "grizzly_spots": ["the fountain stage", "the train steps", "the arcade roof"],
    },
    "pine harbor": {
        "setting": "Pine Harbor",
        "feature": "a harbor of docks, gulls, and salty air",
        "grizzly_spots": ["the fish market dock", "the ferry shed", "the lighthouse path"],
    },
}

HEROES = ["Nova", "Comet Kid", "Captain Bright", "Spark", "Ruby Ray", "Vector", "Starling", "Pulse"]
SIDEKICKS = ["Mica", "Lumen", "Pogo", "Wren", "Tally", "Juniper", "Orbit", "Bee"]
COSTUME_DETAILS = ["a blue cape", "a silver mask", "glowing gloves", "a red scarf", "a star belt"]
MOODS = ["bold", "careful", "cheerful", "steady", "hopeful"]
VILLAINS = ["the Sneer", "Professor Morrow", "Mist Coil", "Captain Creak", "the Grin Goblin"]
QUEST_GOALS = [
    "return the missing city bell",
    "find the stolen parade banner",
    "rescue the bakery kitten",
    "bring back the broken radio relay",
    "deliver medicine to the hill clinic",
]
INNER_MONOLOGUES = [
    "If I rush, I may miss the real clue, so I need to think like a hero, not a storm.",
    "A grizzly shadow sounds scary, but shadows can lie, and the city needs facts.",
    "My powers are useful, but my questions are sharper than my fists.",
    "I can be brave and still pause to listen.",
    "This is a quest, not a race. The best ending begins with careful eyes.",
]
OPENINGS = [
    "The city woke up to sirens, sunlight, and one very strange clue.",
    "By noon, the streets buzzed with a superhero problem that needed a calm mind.",
    "A small emergency turned into a quest before the first pigeon finished breakfast.",
    "The trouble started with a noisy message on the hero radio.",
    "Everyone in the district looked up when the shadow crossed the plaza.",
]
TURN_LINES = [
    "Then the hero noticed that the word 'grizzly' did not point to a bear at all.",
    "A closer look showed the city was not facing a beast, but a misunderstanding.",
    "The clues changed when the hero stopped scouring the wrong alley and followed the right trail.",
    "The whole quest turned on a single detail hidden in plain sight.",
    "What looked like danger was really a code word from a worried helper.",
]
ENDINGS = [
    "With the real problem solved, the city sighed in relief and the sun looked a little warmer.",
    "The streets settled down, and the hero stood smiling beside a happy crowd.",
    "By evening, the quest was finished, and the city sparkled like it had been polished by hope.",
    "The danger passed, the friends laughed, and the whole block felt safer and brighter.",
    "At the end, the hero had not just won the day; they had helped everyone feel happy again.",
]
DIALOGUE_PAIRS = [
    ("I think the grizzly is nearby", "Maybe, but let's scour the clues before we leap"),
    ("Should we terminate the search here", "No, the quest is just beginning"),
    ("That sounds scary", "Then we move carefully and stay kind"),
    ("What if we're wrong", "Then we learn fast and keep everyone safe"),
    ("I found a clue", "Great. Tell me exactly what it says"),
    ("This city needs a hero", "Then let's be the team it needs"),
]

ASP_RULES = r"""
place(river_city).
place(sunset_square).
place(pine_harbor).

hero(nova).
hero(comet_kid).
hero(captain_bright).
hero(spark).
hero(ruby_ray).
hero(vector).
hero(starling).
hero(pulse).

sidekick(mica).
sidekick(lumen).
sidekick(pogo).
sidekick(wren).
sidekick(tally).
sidekick(juniper).
sidekick(orbit).
sidekick(bee).

quest_goal(return_city_bell).
quest_goal(find_banner).
quest_goal(rescue_kitten).
quest_goal(restore_radio_relay).
quest_goal(deliver_medicine).

compatible(P) :- place(P), hero(nova), sidekick(mica).
compatible(P) :- place(P), hero(spark), sidekick(wren).

#show compatible/1.
"""

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    carried_by: Optional[str] = None
    location: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    place: str
    hero: str
    sidekick: str
    mood: str
    goal: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    trace: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero quest storyworld about terminate, grizzly, and scour.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--goal", choices=QUEST_GOALS)
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


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p.replace(" ", "_")))
    for h in HEROES:
        lines.append(asp.fact("hero", h.replace(" ", "_")))
    for s in SIDEKICKS:
        lines.append(asp.fact("sidekick", s.replace(" ", "_")))
    for g in QUEST_GOALS:
        lines.append(asp.fact("quest_goal", g.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(HEROES)
    sidekick = args.sidekick or rng.choice([s for s in SIDEKICKS if s != hero])
    mood = args.mood or rng.choice(MOODS)
    goal = args.goal or rng.choice(QUEST_GOALS)
    return StoryParams(place=place, hero=hero, sidekick=sidekick, mood=mood, goal=goal)


def _story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    key = "|".join((params.place, params.hero, params.sidekick, params.mood, params.goal))
    return int.from_bytes(hashlib.blake2b(key.encode("utf-8"), digest_size=8).digest(), "big")


def asp_verify() -> int:
    import asp
    expected = {(p.replace(" ", "_"),) for p in PLACES}
    model = asp.one_model(asp_program("#show compatible/1."))
    got = set(asp.atoms(model, "compatible"))
    if got == {("river_city",), ("sunset_square",), ("pine_harbor",)}:
        print("OK: ASP gate matches Python reasoning.")
        return 0
    print("MISMATCH:", sorted(got), sorted(expected))
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.hero not in HEROES or params.sidekick not in SIDEKICKS:
        raise StoryError("Unknown hero or sidekick.")
    if params.hero == params.sidekick:
        raise StoryError("The hero and sidekick must be different characters.")
    if params.goal not in QUEST_GOALS:
        raise StoryError("Unknown quest goal.")

    story_seed = _story_seed(params)
    rng = random.Random(story_seed)
    place_meta = PLACES[params.place]
    hero_title = params.hero
    sidekick_title = params.sidekick
    opening = OPENINGS[story_seed % len(OPENINGS)]
    turn = TURN_LINES[(story_seed // 7) % len(TURN_LINES)]
    ending = ENDINGS[(story_seed // 13) % len(ENDINGS)]
    dialogue = DIALOGUE_PAIRS[(story_seed // 29) % len(DIALOGUE_PAIRS)]
    inner = INNER_MONOLOGUES[story_seed % len(INNER_MONOLOGUES)]
    costume = rng.choice(COSTUME_DETAILS)
    villain = rng.choice(VILLAINS)

    world = World(place=place_meta["setting"])
    hero = Entity(id=hero_title, kind="character", label="hero", type="hero", meters={"courage": 0.8, "speed": 0.7}, memes={"hope": 0.9, "focus": 0.6})
    sidekick = Entity(id=sidekick_title, kind="character", label="sidekick", type="sidekick", meters={"courage": 0.5, "speed": 0.5}, memes={"hope": 0.7, "focus": 0.8})
    radio = Entity(id="radio", kind="device", label="hero radio", type="radio", location=params.place, carried_by=hero.id, meters={"noise": 0.2}, memes={"signal": 1.0})
    clue = Entity(id="clue", kind="object", label="scratched clue card", type="clue", location=place_meta["grizzly_spots"][0], memes={"mystery": 1.0})
    grizzly = Entity(id="grizzly", kind="animal", label="grizzly", type="animal", location=place_meta["grizzly_spots"][1], meters={"size": 0.9, "distance": 0.4}, memes={"danger": 0.2})
    world.entities = {e.id: e for e in [hero, sidekick, radio, clue, grizzly]}

    world.say(opening)
    world.say(f"{hero.id}, wearing {costume}, and {sidekick.id} arrived in {world.place} on a quest to {params.goal}.")
    world.say(f"They were a {params.mood} team, the kind that saved time by listening before leaping.")
    world.say(f"Somebody on the radio had shouted about '{villain}' and a grizzly, so the city needed a clean answer fast.")

    world.para()
    world.say(f"'{dialogue[0]},' said {sidekick.id}.")
    world.say(f"'{dialogue[1]},' replied {hero.id}.")
    world.say(f"In {world.place}, {hero.id} began the search while thinking, {inner}")
    world.say(f"They scoured the {place_meta['feature']} until they found {clue.label} near {clue.location}.")

    world.para()
    world.say(turn)
    world.say(f"The clue showed that the word grizzly meant the lookout's nickname for {place_meta['grizzly_spots'][1]}, not a beast attacking anyone.")
    world.say(f"'{dialogue[2]},' {sidekick.id} said.")
    world.say(f"'{dialogue[3]},' answered {hero.id}, and that calm reply helped them terminate the panic, not the search.")
    world.say(f"Together they followed the trail to the real problem: {villain} had jammed the radio relay and scattered the route markers.")

    world.para()
    world.say(f"{hero.id} and {sidekick.id} used their powers to {params.goal} and clear the path without hurting anyone.")
    world.say(f"They restored the relay, warned the crowd, and made sure the grizzly was only a harmless sign on the map.")
    world.say(f"'{dialogue[4]},' said {sidekick.id}.")
    world.say(f"'{dialogue[5]},' said {hero.id}.")
    world.say(ending)
    world.say("The happy ending came when the city cheered, the quest was complete, and the misunderstood grizzly turned out to be only a place name on a map.")

    hero.meters["courage"] = 1.0
    sidekick.meters["courage"] = 0.8
    radio.memes["signal"] = 0.0
    clue.memes["mystery"] = 0.0
    grizzly.meters["distance"] = 1.0
    world.trace = [
        f"quest:{params.goal}",
        f"misread:grizzly",
        f"scour:{clue.location}",
        f"terminate:panic",
        f"happy_ending:{world.place}",
    ]

    story_qa = [
        QAItem(
            question=f"What quest were {hero.id} and {sidekick.id} on?",
            answer=f"They were trying to {params.goal} in {world.place}.",
        ),
        QAItem(
            question="What did the word grizzly really mean in this story?",
            answer=f"It was a nickname for {place_meta['grizzly_spots'][1]}, not a dangerous bear.",
        ),
        QAItem(
            question="What helped the hero stop the confusion?",
            answer="They scoured the clues carefully, listened to the radio, and used inner monologue to slow down before guessing.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The team solved the real problem, finished the quest, and the city had a happy ending.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a quest?",
            answer="A quest is a goal-driven journey where characters search, solve, or rescue something important.",
        ),
        QAItem(
            question="What does terminate mean here?",
            answer="It means to end or stop the panic once the real problem is found.",
        ),
        QAItem(
            question="Why is a happy ending important in a superhero story?",
            answer="A happy ending shows the hero protected people and made the city safer.",
        ),
    ]

    prompts = [
        f"Write a superhero story set in {world.place} where {hero.id} and {sidekick.id} scour clues, face a grizzly misunderstanding, and finish with a happy ending.",
        f"Tell a child-friendly quest story that includes inner monologue, spoken dialogue, the word terminate, and the word grizzly used as a mistaken clue.",
        f"Make a short superhero adventure about a radio clue, a city quest, and a calm hero who learns to scour before acting.",
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for e in sample.world.entities.values():
            bits = []
            if e.label:
                bits.append(f"label={e.label}")
            if e.location:
                bits.append(f"location={e.location}")
            if e.carried_by:
                bits.append(f"carried_by={e.carried_by}")
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            print(f"  {e.id}: {e.kind} {(' '.join(bits))}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
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


CURATED = [
    StoryParams(place="river city", hero="Nova", sidekick="Mica", mood="hopeful", goal="rescue the bakery kitten"),
    StoryParams(place="sunset square", hero="Spark", sidekick="Wren", mood="bold", goal="return the missing city bell"),
    StoryParams(place="pine harbor", hero="Captain Bright", sidekick="Tally", mood="steady", goal="deliver medicine to the hill clinic"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/1."))
        print(asp.atoms(model, "compatible"))
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
        samples = [generate(resolve_params(args, rng)) for _ in range(args.n)]

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
