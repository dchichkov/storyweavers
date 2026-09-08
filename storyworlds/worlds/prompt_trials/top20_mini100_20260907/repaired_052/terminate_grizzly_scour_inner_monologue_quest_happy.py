#!/usr/bin/env python3
"""
A compact superhero storyworld about a heroic quest, an inner monologue,
a grizzly problem, and a happy ending.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[3]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "heroine"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "hero"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    hero: str
    sidekick: str
    city: str
    seed: Optional[int] = None
    scenario: Optional[str] = None
    tone: Optional[str] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    premise: str
    trouble: str
    rash_move: str
    consequence: str
    clue: str
    careful_move: str
    reveal: str
    apology: str
    repair: str
    ending: str
    lesson: str


HERO_NAMES = ["Nova", "Beacon", "Flash", "Comet", "Aurora", "Vector"]
SIDEKICK_NAMES = ["Zip", "Penny", "Scout", "Milo", "Juno", "Rex"]
CITIES = [
    "Maple Harbor",
    "Sunset City",
    "Metro Bay",
    "River Gate",
]

TONE_MODES = ["alert", "thoughtful", "dialogue", "countdown", "mystery", "promise"]


SCENARIOS = [
    Scenario(
        key="bear_alarm",
        premise="was on a quest to protect the city park before sunrise",
        trouble="a grizzly drone had jammed the park gates and scared the morning crowd",
        rash_move="hit the emergency terminate switch without checking the lock pattern",
        consequence="the gates clanged shut and the crowd backed up near the picnic path",
        clue="the drone kept pausing whenever the music from the fountain grew soft",
        careful_move="scouted the gate panel and matched the lock pattern with a humming rescue tune",
        reveal="the grizzly drone was guarding a trapped cub-sized delivery pod",
        apology="admitted that a quick fix could have made the trouble worse",
        repair="opened the pod, freed the path, and reset the gates by hand",
        ending="the park filled with smiling families under a warm gold sky",
        lesson="a hero should look closely before trying to terminate a problem",
    ),
    Scenario(
        key="roof_scour",
        premise="was racing across the rooftops to recover a missing lightning beacon",
        trouble="a grizzly gust from the storm had scattered metal shreds all over the roof",
        rash_move="scoured the roof by blasting the debris off with a power beam",
        consequence="the beam tossed the beacon toward a water tower and nearly cracked it",
        clue="the shreds formed an arrow when the wind dropped for one heartbeat",
        careful_move="followed the arrow, then used a gentle grappling line to lift the beacon free",
        reveal="the grizzly-looking debris was a protective nest of storm foil around the beacon",
        apology="told the sidekick that speed had nearly broken the very thing they came for",
        repair="repacked the foil nest and restored the beacon to its rooftop stand",
        ending="the beacon flashed safely over the city while rain slid off the towers",
        lesson="speed is useful, but care keeps a rescue from becoming a new mess",
    ),
    Scenario(
        key="cave_monologue",
        premise="was exploring a dark service tunnel beneath the library",
        trouble="a grizzly shadow blocked the exit and made every echo sound like a growl",
        rash_move="tried to terminate the shadow by switching on every lamp at once",
        consequence="the light startled a flock of pigeons and sent papers swirling through the tunnel",
        clue="the growl repeated only when the tunnel fan shook the loose vent cover",
        careful_move="paused, listened, and used a quiet flashlight to trace the sound to the vent",
        reveal="the grizzly shadow was only a statue's shape cast by a bent vent grate",
        apology="murmured that fear had turned a normal shape into a monster in the mind",
        repair="straightened the grate and gathered the scattered papers back into order",
        ending="the library lights glowed softly above a calm, ordinary tunnel",
        lesson="an inner monologue can be brave when it helps a hero notice the truth",
    ),
    Scenario(
        key="quest_festival",
        premise="was carrying a silver ribbon needed for the city's hero festival",
        trouble="a grizzly kite had tangled the ribbon high between two towers",
        rash_move="scoured at the rope with a cutting gadget",
        consequence="the ribbon snapped loose and fell into a fountain before the parade arrived",
        clue="the kite's tail pointed straight toward the fountain whenever the drums paused",
        careful_move="climbed with a harness and used the kite's tail as a guide rope",
        reveal="the grizzly kite was protecting a lost child who had been hiding on a balcony",
        apology="said the cutting gadget had nearly ruined the celebration",
        repair="returned the ribbon, escorted the child down, and tied the festival colors together",
        ending="the parade began on time with bright flags waving over the square",
        lesson="a quest can end happy when the hero remembers to help everyone caught in the problem",
    ),
    Scenario(
        key="train_bridge",
        premise="was escorting a rescue train across a cracked bridge",
        trouble="a grizzly pile of broken track bars blocked the last rail car",
        rash_move="used the train's engine to scour the bars aside",
        consequence="the force bent the bridge rail and shook the rescue car",
        clue="one bar carried a fresh scratch shaped like a warning mark",
        careful_move="slowed the train, then lifted each bar with a magnetic clamp",
        reveal="the grizzly pile was not rubble at all but a hidden support kit from the old bridge crew",
        apology="confessed that the forceful move had threatened the very crossing they needed",
        repair="reassembled the support kit and secured the bridge for the train",
        ending="the rescue train rolled into the station with every passenger safe and smiling",
        lesson="a hero wins the day by understanding what a pile of trouble really is",
    ),
    Scenario(
        key="museum_mask",
        premise="was on a quest to return a stolen mask to the city museum",
        trouble="a grizzly display case had locked itself and set off an alarm",
        rash_move="tried to terminate the alarm by smashing the lock with a baton",
        consequence="the case glass rang like a bell and the museum guards rushed in",
        clue="the mask's reflection lined up only when the case was turned toward the moonlight",
        careful_move="turned the case slowly and used a museum passcode whispered by the curator",
        reveal="the grizzly alarm was a security test left behind by the museum founder",
        apology="told the guards that impatience had made a small test look like a theft",
        repair="reset the case, returned the mask, and thanked the curator for the warning",
        ending="the museum went quiet again, and the mask rested safely on its velvet stand",
        lesson="the best heroes ask what a thing is before they try to stop it",
    ),
    Scenario(
        key="bridge_message",
        premise="was trying to deliver a warning to a scientist on the far riverbank",
        trouble="a grizzly tugboat had jammed the only bridge cable with muddy rope",
        rash_move="scoured the rope away with a spinning cutter",
        consequence="the cutter nicked the cable and the bridge swayed over the water",
        clue="the muddy rope carried flags from the scientist's own lab team",
        careful_move="used a rescue drone to lift the rope without touching the cable",
        reveal="the grizzly tugboat was carrying supplies for the scientist, not blocking the bridge on purpose",
        apology="said the cutting tool had nearly stranded the people they were helping",
        repair="repaired the cable clamp and guided the tugboat to the correct dock",
        ending="the warning reached the scientist just in time, and the lab lights blinked back in thanks",
        lesson="even a heroic quest needs patience when the answer is hidden in plain sight",
    ),
    Scenario(
        key="roar_tower",
        premise="was climbing a radio tower to restore the city's night signal",
        trouble="a grizzly roar came from the top and made the technicians flee",
        rash_move="terminated the tower's speaker system to silence the roar",
        consequence="without the speaker, the tower lost its guide signal and the lights flickered out",
        clue="the roar rose and fell with the rhythm of a broken fan",
        careful_move="opened the fan housing and used an oil pen to quiet the blades",
        reveal="the grizzly roar was only a loose fan cover shaking in the wind",
        apology="admitted that fear had made them switch off the wrong machine",
        repair="fixed the fan cover and restarted the guide signal",
        ending="the night signal spread across the city like a steady silver blanket",
        lesson="sometimes the loudest monster is only a broken part asking for repair",
    ),
]

ASP_RULES = r"""
#show feature/1.
#show setting/1.
#show seedword/1.
#show tone/1.
"""


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with an inner monologue and a happy ending.")
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICK_NAMES)
    ap.add_argument("--city", choices=CITIES)
    ap.add_argument("--scenario", choices=[s.key for s in SCENARIOS])
    ap.add_argument("--tone", choices=TONE_MODES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice([n for n in SIDEKICK_NAMES if n != hero])
    city = args.city or rng.choice(CITIES)
    scenario = args.scenario or rng.choice(SCENARIOS).key
    tone = args.tone or rng.choice(TONE_MODES)
    return StoryParams(hero=hero, sidekick=sidekick, city=city, seed=None, scenario=scenario, tone=tone)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("feature", "InnerMonologue"),
            asp.fact("feature", "Quest"),
            asp.fact("feature", "HappyEnding"),
            asp.fact("seedword", "terminate"),
            asp.fact("seedword", "grizzly"),
            asp.fact("seedword", "scour"),
            asp.fact("setting", "city"),
            asp.fact("tone", "superhero"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    feats = sorted(set(asp.atoms(model, "feature")))
    wanted = [("HappyEnding",), ("InnerMonologue",), ("Quest",)]
    if feats != wanted:
        print("MISMATCH: ASP feature facts are wrong.")
        print(feats)
        return 1
    print("OK: ASP facts include the required features.")
    return 0


@dataclass
class World:
    city: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _opening(params: StoryParams, scenario: Scenario) -> list[str]:
    return [
        f"In {params.city}, {params.hero} was on a quest while the night wind slipped between the towers.",
        f"{scenario.premise.capitalize()}, and {params.sidekick} stayed close beside the cape and the signal belt.",
    ]


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    scenario = next((s for s in SCENARIOS if s.key == params.scenario), SCENARIOS[0])

    world = World(city=params.city)
    hero = world.add(Entity(id=params.hero, kind="character", type="hero", label="hero", phrase=params.hero, location="skyline", traits=["brave", "kind"]))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="sidekick", label="sidekick", phrase=params.sidekick, location="street", traits=["alert", "loyal"]))
    problem = world.add(Entity(id="problem", kind="thing", type="device", label="grizzly problem", phrase="a grizzly problem", location="scene", meters={"danger": 1.0}, memes={"worry": 1.0}))
    world.facts.update(city=params.city, scenario=scenario.key, lesson=scenario.lesson)

    for line in _opening(params, scenario):
        world.say(line)

    world.say(f'“We can handle this,” {params.sidekick} said.')
    world.say(f'“I hope so,” {params.hero} replied, and {hero.pronoun("subject")} took a deep breath while an inner monologue whispered, “Stay calm. Look first. Be the hero this city needs.”')

    world.para()
    world.say(f"Then the trouble hit: {scenario.trouble}.")
    world.say(f"At first, {params.hero} made the wrong move and {scenario.rash_move}.")
    world.say(f"The result was immediate: {scenario.consequence}.")
    world.say(f'“That made it worse,” {params.sidekick} said. “Should we still keep going?”')
    world.say(f'“Yes,” {params.hero} answered, “but not the same way.”')

    world.para()
    world.say(f"Now the hero listened to the scene instead of the fear. {scenario.clue.capitalize()}.")
    world.say(f"That clue sent {params.hero} into a careful plan: {scenario.careful_move}.")
    world.say(f"The truth came into view: {scenario.reveal}.")
    world.say(f'“So it was not a real monster,” {params.sidekick} said.')
    world.say(f'“No,” {params.hero} said. “Just a grizzly-looking mistake that needs help.”')

    world.para()
    world.say(f"{params.hero} and {params.sidekick} worked together to make things right.")
    world.say(f"{scenario.apology.capitalize()}, and then they {scenario.repair}.")
    world.say(f"Because the problem was understood, the city was safe again.")
    world.say(f"At last came the happy ending: {scenario.ending}.")
    world.say(f"In the end, {scenario.lesson.lower()}.")
    world.say(f'The quest was finished, the inner monologue was quiet, and the heroes headed home smiling.')

    problem.location = "resolved"
    problem.meters["danger"] = 0.0
    problem.memes["worry"] = 0.0
    hero.memes["confidence"] = 1.0
    sidekick.memes["trust"] = 1.0

    prompts = [
        f"Write a superhero story about {params.hero} and {params.sidekick} in {params.city}. Include the seed words terminate, grizzly, and scour.",
        f"Tell a child-friendly quest story where an inner monologue helps the hero make a better choice.",
        f"Write a short story with a clear happy ending after a mistaken action causes trouble.",
    ]
    story_qa = [
        QAItem(
            question=f"What quest was {params.hero} on?",
            answer=f"{params.hero} was on a quest to solve a city problem in {params.city}.",
        ),
        QAItem(
            question="What went wrong first?",
            answer=f"The hero made a rushed mistake when {scenario.rash_move}. That caused more trouble instead of less.",
        ),
        QAItem(
            question="What clue helped the heroes understand the problem?",
            answer=f"They noticed that {scenario.clue}. That clue led them to the truth that {scenario.reveal}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily because {scenario.ending}.",
        ),
        QAItem(
            question="What lesson did the hero learn?",
            answer=f"The hero learned that {scenario.lesson.lower()}.",
        ),
    ]
    world_qa = [
        QAItem(question="What is an inner monologue?", answer="An inner monologue is a character's private thoughts, like a quiet voice in the mind."),
        QAItem(question="What does a quest mean in a superhero story?", answer="A quest is an important mission or journey to help someone, fix a problem, or protect a place."),
        QAItem(question="What is a happy ending?", answer="A happy ending is when the problem is solved and the story closes on a positive, safe note."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            bits = []
            if e.location:
                bits.append(f"location={e.location}")
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            print(f"  {e.id}: {e.type} {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(hero="Nova", sidekick="Zip", city="Maple Harbor", seed=101, scenario="bear_alarm", tone="dialogue"),
            StoryParams(hero="Beacon", sidekick="Scout", city="Sunset City", seed=202, scenario="cave_monologue", tone="thoughtful"),
            StoryParams(hero="Comet", sidekick="Juno", city="Metro Bay", seed=303, scenario="quest_festival", tone="promise"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            attempt_seed = base_seed + i
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.sidekick} in {p.city}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
