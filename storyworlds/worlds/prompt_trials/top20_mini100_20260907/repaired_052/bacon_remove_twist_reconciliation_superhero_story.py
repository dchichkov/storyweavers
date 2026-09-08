#!/usr/bin/env python3
"""
A small superhero story world about bacon, a twist, and reconciliation.

The world simulates a tiny rescue mission in which a hero, a helper, and a
problem with bacon lead to a twist and end in reconciliation.
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
        if self.type in {"hero", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
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
    opening: str
    trouble: str
    bad_choice: str
    consequence: str
    clue: str
    twist: str
    repair: str
    reconciliation: str
    ending: str
    lesson: str


HERO_NAMES = ["Nova", "Blaze", "Comet", "Echo", "Pixel", "Storm"]
SIDEKICK_NAMES = ["Zip", "Milo", "Pip", "Rae", "Tess", "Vik"]
CITIES = ["Maple City", "Bright Harbor", "Sunstone Square", "Riverglass"]

TONE_MODES = ["urgent", "dialogue", "noisy", "calm", "mystery", "warning"]


SCENARIOS = [
    Scenario(
        key="bacon_blast",
        opening="was keeping watch above the city when the morning alarms began to chirp",
        trouble="a bacon cart had spun loose and rolled into the hero lane",
        bad_choice="tried to remove the cart with one fast shove",
        consequence="the cart tipped, and bacon strips scattered across the street like slippery ribbons",
        clue="the wheels had a tiny twist mark that matched the park fountain gate",
        twist="the cart was not a prank at all; it was being dragged by a stuck magnet under the gate",
        repair="used a rescue line and a careful pull to remove the magnet without breaking the cart",
        reconciliation="apologized to the vendor for the rough shove and helped gather every strip",
        ending="the vendor laughed, the lane was clean again, and the hero badge flashed over warm bacon stacks",
        lesson="a quick fix is not always a kind fix",
    ),
    Scenario(
        key="rooftop_twist",
        opening="was patrolling the rooftops when the wind brought a smoky smell from the bakery district",
        trouble="a bacon sign had twisted sideways and blocked the fire ladder",
        bad_choice="jumped up and yanked at the sign without checking the bolts",
        consequence="the sign swung free, and the ladder clanged down with a loud crash",
        clue="one bolt had been bent in a neat spiral, not snapped",
        twist="the sign had twisted because a hidden drone had looped the cable around it",
        repair="cut the cable, reset the sign, and remove the bent drone hook with a wrench",
        reconciliation="told the baker the truth and helped steady the ladder together",
        ending="the ladder stood straight again, and the bakery windows glowed safely behind it",
        lesson="truth can turn a problem into a team-up",
    ),
    Scenario(
        key="bacon_signal",
        opening="was answering a rooftop signal while the sidekick kept watch with a bright red scanner",
        trouble="the signal came from a bacon-shaped beacon on the city hall roof",
        bad_choice="thought the beacon was a joke and tried to remove its cover at once",
        consequence="the cover popped off, and the beacon went dark just as the rescue team arrived",
        clue="the cover held a hidden twist of wire linking it to the power relay",
        twist="the bacon shape was a coded warning from the mayor's office, not a prank",
        repair="reconnected the relay, replaced the cover, and used the scanner to verify the message",
        reconciliation="admitted the mistake to the rescue team and thanked the sidekick for the warning",
        ending="the beacon shone again, and the rescue team climbed the roof with clear directions",
        lesson="a strange shape may still carry an important message",
    ),
    Scenario(
        key="villain_misread",
        opening="was speeding through the plaza when a masked figure dropped a smoky bacon pouch",
        trouble="the hero thought the pouch came from a villain",
        bad_choice="leapt forward and tried to remove the pouch from the figure's hand",
        consequence="the pouch burst open, and the smoke made everyone cough and stumble",
        clue="the pouch tag read 'Lunch for the shelter' in tiny letters",
        twist="the masked figure was a volunteer carrying food, not a villain at all",
        repair="opened the windows, gathered the bacon packets, and helped sort them for delivery",
        reconciliation="said sorry for the grab and listened while the volunteer explained the route",
        ending="the shelter got its lunch on time, and the plaza filled with grateful cheers",
        lesson="not every mask hides danger",
    ),
    Scenario(
        key="twist_bridge",
        opening="was guarding a bridge when a low hum shook the railings",
        trouble="a bacon delivery drone had twisted around the bridge cables",
        bad_choice="snatched at the drone to remove it before it fell",
        consequence="the drone spun harder, and its lunch boxes bobbed over the river",
        clue="one cable hummed in the same rhythm as the drone's tiny motor",
        twist="the drone had twisted itself around the bridge while trying to avoid a flock of pigeons",
        repair="used a rescue hook to steady the drone and guide it back along the cable path",
        reconciliation="returned the lunch boxes to the driver and accepted a sheepish thank-you",
        ending="the bridge settled quiet again while the rescued drone blinked happily",
        lesson="steady hands solve what grabby hands worsen",
    ),
    Scenario(
        key="bacon_clock",
        opening="was checking the city clock tower when the noon bell stuck halfway",
        trouble="a bacon grease spill had coated the clock gears",
        bad_choice="tried to remove the grease with a hard brush",
        consequence="the brush jammed the gears even tighter and stopped the bell",
        clue="one gear had a twist in its teeth where the jam began",
        twist="the grease had come from a broken lunch box carried by the tower's own cleaner robot",
        repair="used a soft cloth, cleaned the gears, and fixed the twist with a tiny tool",
        reconciliation="forgave the cleaner robot and showed it how to carry the box better",
        ending="the clock bell rang out on time, and the cleaner robot gave a proud beep",
        lesson="gentle work keeps delicate things alive",
    ),
    Scenario(
        key="bakery_buddy",
        opening="was circling the bakery block when the sidekick smelled trouble before the sirens did",
        trouble="a bacon tray had slid behind the ovens and blocked the vent",
        bad_choice="reached through the heat and tried to remove the tray fast",
        consequence="the tray skidded farther in, and the kitchen filled with smoke",
        clue="the vent latch had a little twist that kept it from opening",
        twist="the tray was trapped because the latch spring had popped loose during the rush",
        repair="opened the side panel, reset the spring, and slid the tray out with tongs",
        reconciliation="apologized to the baker for rushing and helped fan the smoke away",
        ending="the bakery breathed again, and fresh bread rose while the bacon tray cooled",
        lesson="careful steps are the real superhero move",
    ),
    Scenario(
        key="signal_museum",
        opening="was visiting the city museum when the emergency lights flashed red",
        trouble="a bacon exhibit had been twisted inside its glass case",
        bad_choice="broke the latch to remove the exhibit quickly",
        consequence="the broken latch made the whole case wobble and the alarm screech louder",
        clue="the twist in the frame matched the museum's spare key notch",
        twist="the exhibit was actually a hidden key to the archive door",
        repair="used the spare key, fixed the latch, and removed only the loose casing",
        reconciliation="told the curator the truth and helped set the exhibit upright again",
        ending="the alarm stopped, and the archive door opened to a safe, quiet room",
        lesson="an object can be both surprising and important",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero storyworld about bacon and reconciliation.")
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

    lines = [
        asp.fact("feature", "twist"),
        asp.fact("feature", "reconciliation"),
        asp.fact("seed_word", "bacon"),
        asp.fact("seed_word", "remove"),
        asp.fact("style", "superhero_story"),
        asp.fact("setting", "city"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
#show feature/1.
#show seed_word/1.
#show style/1.
#show setting/1.
"""


def asp_program(show: str = "#show feature/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    feats = sorted(asp.atoms(model, "feature"))
    seeds = sorted(asp.atoms(model, "seed_word"))
    ok = feats == [("reconciliation",), ("twist",)] and seeds == [("bacon",), ("remove",)]
    if ok:
        print("OK: ASP facts match Python registries.")
        return 0
    print("MISMATCH: ASP facts do not match Python registries.")
    print("features:", feats)
    print("seed_words:", seeds)
    return 1


class World:
    def __init__(self, city: str) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


def _pick(rng: random.Random, *choices: str) -> str:
    return rng.choice(choices)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    scenario = next((s for s in SCENARIOS if s.key == params.scenario), SCENARIOS[0])
    world = World(params.city)

    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type="hero",
        label="hero",
        phrase=f"Hero {params.hero}",
        location="skyline",
        traits=["brave", "kind"],
        meters={"height": 1.0},
        memes={"responsibility": 1.0},
    ))
    sidekick = world.add(Entity(
        id=params.sidekick,
        kind="character",
        type="sidekick",
        label="sidekick",
        phrase=f"{params.sidekick}",
        location="rooftop",
        traits=["quick", "loyal"],
        memes={"curiosity": 1.0},
    ))
    bacon = world.add(Entity(
        id="bacon",
        kind="thing",
        type="food",
        label="bacon",
        phrase="bacon",
        location="street cart",
        meters={"slippery": 0.8, "warm": 0.9},
        memes={"importance": 0.7},
    ))
    world.facts.update(hero=hero, sidekick=sidekick, bacon=bacon, scenario=scenario.key)

    tone = params.tone or "calm"
    if tone == "urgent":
        world.say(f"Over {params.city}, Hero {params.hero} heard the siren and raced toward the morning trouble.")
    elif tone == "dialogue":
        world.say(f'"Did you smell that?" {params.sidekick} asked. "Bacon," said Hero {params.hero}, "and something is very wrong."')
    elif tone == "mystery":
        world.say(f"The first clue in {params.city} was a trail of bacon crumbs leading toward the rooftops.")
    elif tone == "warning":
        world.say(f'"Watch the lane!" {params.sidekick} shouted as Hero {params.hero} arrived above {params.city}.')
    elif tone == "noisy":
        world.say(f"Sirens, clanging signs, and a loud city crowd met Hero {params.hero} at dawn.")
    else:
        world.say(f"Hero {params.hero} watched over {params.city} when a small problem with bacon broke the quiet morning.")

    world.say(f"{scenario.opening}.")
    world.para()
    world.say(f"Then the hero spotted the trouble: {scenario.trouble}.")
    world.say(
        f'"I can fix it fast," said {params.sidekick}, but Hero {params.hero} warned, "Not until we know what it is."'
    )
    world.say(f"Still, {params.sidekick} {scenario.bad_choice}.")
    world.say(f"That mistake brought a bigger mess: {scenario.consequence}.")
    world.para()
    world.say(f"Hero {params.hero} knelt beside the scene and noticed that {scenario.clue}.")
    world.say(f'"That is a twist," {params.sidekick} whispered. "I thought it was junk."')
    world.say(f'"Not junk," said Hero {params.hero}. "A real rescue needs a careful hand."')
    world.say(f"With a steady breath, {params.hero} {scenario.repair}.")
    world.say(f"That was the twist: {scenario.twist}.")
    world.para()
    world.say(f"{scenario.reconciliation.capitalize()}, and the two heroes smiled again.")
    world.say(f"{scenario.ending}.")
    world.say(f"In the end, {scenario.lesson}.")

    bacon.location = "served safely"
    bacon.meters["slippery"] = 0.0
    bacon.meters["warm"] = 1.0
    bacon.memes["importance"] = 1.0
    hero.memes["reconciliation"] = 1.0
    sidekick.memes["reconciliation"] = 1.0

    prompts = [
        f"Write a short superhero story about Hero {params.hero} and a bacon problem in {params.city}.",
        f"Tell a child-friendly rescue tale where a twist changes the meaning of a bacon clue.",
        f"Write a story with reconciliation after someone tries to remove the wrong thing too fast.",
    ]
    story_qa = [
        QAItem(
            question="What problem started the story?",
            answer=f"The story started when {scenario.trouble}.",
        ),
        QAItem(
            question="What mistake made the problem worse?",
            answer=f"{params.sidekick} made it worse by trying to remove the bacon problem too quickly.",
        ),
        QAItem(
            question="What clue helped the hero understand the truth?",
            answer=f"The clue was that {scenario.clue}.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {scenario.twist}.",
        ),
        QAItem(
            question="How did the story end in reconciliation?",
            answer=f"Hero {params.hero} and {params.sidekick} talked, fixed the problem together, and made peace after the mistake.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a superhero story?",
            answer="A superhero story is a tale about a brave helper who uses courage and skill to solve a problem.",
        ),
        QAItem(
            question="What does twist mean in a story?",
            answer="A twist is a surprising change that makes the story turn in a new direction.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after a mistake, argument, or misunderstanding.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for ent in sample.world.entities.values():
            bits = []
            if ent.location:
                bits.append(f"location={ent.location}")
            if ent.meters:
                bits.append(f"meters={ent.meters}")
            if ent.memes:
                bits.append(f"memes={ent.memes}")
            print(f"  {ent.id}: {ent.type} {' '.join(bits)}")
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
            StoryParams(hero="Nova", sidekick="Zip", city="Maple City", seed=101, scenario="bacon_blast", tone="dialogue"),
            StoryParams(hero="Blaze", sidekick="Milo", city="Bright Harbor", seed=202, scenario="rooftop_twist", tone="urgent"),
            StoryParams(hero="Echo", sidekick="Pip", city="Sunstone Square", seed=303, scenario="villain_misread", tone="mystery"),
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
