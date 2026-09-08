#!/usr/bin/env python3
"""
A small space-adventure storyworld about a correction that changes a magical
mission. The crew first trusts a faulty star map, then learns that a careful
correction can reveal the safe path home.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE)))))
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
    captain: str
    navigator: str
    helper: str
    mystery: str
    correction: str
    twist: str
    magic: str
    ending: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Mystery:
    opening: str
    danger: str
    false_answer: str
    clue: str
    solution: str
    changed_fact: str


@dataclass(frozen=True)
class Correction:
    mistake: str
    admission: str
    advice: str
    repair: str
    lesson: str


@dataclass(frozen=True)
class Twist:
    reveal: str
    meaning: str


@dataclass(frozen=True)
class Ending:
    image: str
    final_line: str


NAMES = ["Luna", "Orin", "Mira", "Tavi", "Niko", "Sela", "Pax", "Rhea"]
HELPERS = ["the moon fox", "the old star keeper", "a silver robot"]

MYSTERIES = {
    "singing_comet": Mystery(
        opening="a blue comet began singing outside the ship",
        danger="the song pulled the ship toward a field of dark rocks",
        false_answer="the comet was calling them to a hidden treasure",
        clue="the song repeated one bright note whenever the ship turned away",
        solution="the crew matched the note to the ship's gentle steering bell",
        changed_fact="the singing comet became a guide instead of a danger",
    ),
    "sleeping_planet": Mystery(
        opening="a tiny planet blinked like a sleeping eye",
        danger="the ship's landing path led straight toward a storm of crystal dust",
        false_answer="the blinking planet wanted them to land at once",
        clue="its light went dark whenever the crystal storm crossed its sky",
        solution="the crew waited for the planet's dark signal before crossing",
        changed_fact="the crystal storm was crossed during a safe quiet moment",
    ),
    "glass_moon": Mystery(
        opening="a glass moon appeared where no moon had been marked",
        danger="the moon's bright pull began to drain the ship's magic fuel",
        false_answer="the moon was empty and harmless",
        clue="a tiny shadow moved inside its shining center",
        solution="the crew dimmed their lamps and followed the shadow's slow orbit",
        changed_fact="the moon's hidden path restored the ship's magic fuel",
    ),
    "lost_beacon": Mystery(
        opening="an old beacon flashed three different colors",
        danger="each color pointed the ship toward a different, dangerous route",
        false_answer="the fastest color must be the right one",
        clue="the beacon flashed fastest when someone spoke kindly to it",
        solution="the crew answered with calm voices until one steady green path appeared",
        changed_fact="the beacon opened a calm route through space",
    ),
    "whispering_ring": Mystery(
        opening="a ring of stars whispered the crew's names",
        danger="the whispers made every instrument show a different direction",
        false_answer="the loudest whisper knew the way",
        clue="the quietest star repeated the same word: home",
        solution="the crew followed the quiet star and ignored the noisy echoes",
        changed_fact="the quiet star led them toward home",
    ),
    "crystal_river": Mystery(
        opening="a river of floating crystals curled across the sky",
        danger="the crystals began orbiting the ship faster and faster",
        false_answer="more engine power would break the circle",
        clue="the crystals slowed whenever the crew shared one clear plan",
        solution="the crew shut down the noisy engine and guided the river with one clear plan",
        changed_fact="the crystal river carried the ship safely onward",
    ),
}

CORRECTIONS = {
    "map": Correction(
        mistake="They had trusted a star map without checking its newest mark",
        admission='"I read the map too quickly," {captain} said. "We need a correction."',
        advice='"A map can be old even when the stars are new," {helper} warned.',
        repair="compare the map with the sky, the instruments, and the repeated clue",
        lesson="a brave correction is better than a proud mistake",
    ),
    "signal": Correction(
        mistake="They had mistaken a warning signal for an invitation",
        admission='"We guessed instead of listening," {navigator} admitted. "Let us correct our guess."',
        advice='"A signal tells you to look again, not always to rush ahead," {helper} said.',
        repair="test the signal from three safe distances before changing course",
        lesson="careful listening can turn confusion into wisdom",
    ),
    "count": Correction(
        mistake="They had counted the magic stars incorrectly",
        admission='"There is one star missing from my count," {captain} said. "That changes everything."',
        advice='"Small corrections can open very large doors," {helper} replied.',
        repair="count the stars together and use the missing one as their guide",
        lesson="checking small details can protect a whole crew",
    ),
    "voice": Correction(
        mistake="They had followed the loudest voice instead of the clearest idea",
        admission='"I spoke loudly, but I was not certain," {navigator} confessed.',
        advice='"The best answer does not need to shout," {helper} said.',
        repair="let each crew member explain one clue before choosing a route",
        lesson="humility helps a team hear the truth",
    ),
    "clock": Correction(
        mistake="They had read the ship clock upside down after the magic lights flickered",
        admission='"Our time reading was backward," {captain} said. "We must correct it now."',
        advice='"When the lights change, check the clock before you hurry," {helper} explained.',
        repair="reset the clock by matching it with the slow pulse of a nearby star",
        lesson="patience makes room for accurate choices",
    ),
}

TWISTS = {
    "home": Twist(
        reveal="the mysterious signal was not calling them outward at all; it was the ship's own home beacon reflected from a hidden moon",
        meaning="the safest adventure sometimes begins by noticing what has been near you all along",
    ),
    "friend": Twist(
        reveal="the magical star was not a treasure but a tiny lost star creature asking for help",
        meaning="what looks like a prize may really be a friend in need",
    ),
    "mirror": Twist(
        reveal="the strange planet was a mirror, showing the crew the route they had already traveled",
        meaning="their first path was not wasted because it carried the clue to the next one",
    ),
    "song": Twist(
        reveal="the space song was made by the ship's own engine, which had learned the crew's hopes",
        meaning="the magic was strongest when the crew worked together",
    ),
    "door": Twist(
        reveal="the glowing portal was not a doorway to a new world but a doorway back to a place that needed them",
        meaning="returning to help can be a courageous part of an adventure",
    ),
}

MAGIC_LINES = {
    "moon_dust": "Luna sprinkled a pinch of moon dust over the compass, and its needle began to glow.",
    "star_lantern": "Orin lifted the star lantern, whose little flame shone without heat.",
    "kind_word": "The crew spoke one kind word together, and a silver path appeared between the stars.",
    "crystal_chime": "A crystal chime rang beside the controls, making the truthful direction sparkle.",
    "sleeping_spell": "They whispered a gentle sleeping spell, and the wild lights settled like quiet snow.",
}

ENDINGS = {
    "harbor": Ending(
        "At dawn, the ship floated into the bright harbor above their home world",
        "Luna placed the corrected map beside the window so every traveler could learn from it",
    ),
    "garden": Ending(
        "The crew landed in a moon garden where small stars grew like flowers",
        "They watered the stars and told them that careful corrections could help anyone find the way",
    ),
    "bell": Ending(
        "The ship's gentle steering bell rang once as the crew reached safe space",
        "This time, everyone listened before choosing the next direction",
    ),
    "bridge": Ending(
        "A rainbow bridge unfolded from the rescued magic and led them back to their station",
        "The crew crossed it together, carrying the corrected chart between them",
    ),
    "window": Ending(
        "Through the round window, the stars formed a bright arrow pointing home",
        "Luna smiled because the arrow had appeared only after they admitted the mistake",
    ),
}

REFLECTIONS = (
    "They wrote the correction in large letters on the ship's chart.",
    "They asked every member of the crew to check the new course.",
    "They thanked the clue that had seemed too small to notice.",
    "They slowed the engines so nobody would mistake hurry for courage.",
    "They left a bright note for the next traveler who might meet the same mystery.",
)

VALID_PLACES = {"orbit"}
VALID_ACTIVITIES = {"correction"}
VALID_PRIZES = {"home_beacon"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Magical space-adventure storyworld.")
    parser.add_argument("--place", choices=sorted(VALID_PLACES))
    parser.add_argument("--activity", choices=sorted(VALID_ACTIVITIES))
    parser.add_argument("--prize", choices=sorted(VALID_PRIZES))
    parser.add_argument("--captain")
    parser.add_argument("--navigator")
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    supplied = [args.place, args.activity, args.prize]
    if any(value is not None for value in supplied):
        if args.place not in (None, "orbit"):
            raise StoryError("This adventure takes place in orbit around a magical home world.")
        if args.activity not in (None, "correction"):
            raise StoryError("The ship's central activity must be a careful correction.")
        if args.prize not in (None, "home_beacon"):
            raise StoryError("The story's guiding prize is the home beacon.")
    captain = args.captain or rng.choice(NAMES)
    navigator = args.navigator or rng.choice([name for name in NAMES if name != captain])
    if captain == navigator:
        raise StoryError("The captain and navigator need different names.")
    return StoryParams(
        captain=captain,
        navigator=navigator,
        helper=args.helper or rng.choice(HELPERS),
        mystery=rng.choice(tuple(MYSTERIES)),
        correction=rng.choice(tuple(CORRECTIONS)),
        twist=rng.choice(tuple(TWISTS)),
        magic=rng.choice(tuple(MAGIC_LINES)),
        ending=rng.choice(tuple(ENDINGS)),
    )


def tell(params: StoryParams) -> World:
    mystery = MYSTERIES[params.mystery]
    correction = CORRECTIONS[params.correction]
    twist = TWISTS[params.twist]
    ending = ENDINGS[params.ending]

    world = World()
    captain = world.add(Entity("captain", "character", params.captain, "ship"))
    navigator = world.add(Entity("navigator", "character", params.navigator, "ship"))
    helper = world.add(Entity("helper", "helper", params.helper, "orbit"))
    ship = world.add(Entity("ship", "ship", "the little starship", "orbit"))
    beacon = world.add(Entity("beacon", "beacon", "the home beacon", "hidden moon"))

    world.facts.update(
        captain=captain,
        navigator=navigator,
        helper=helper,
        ship=ship,
        beacon=beacon,
        mystery=mystery,
        correction=correction,
        twist=twist,
        ending=ending,
        resolved=False,
    )

    world.say(
        f"Once, Captain {captain.label} and Navigator {navigator.label} sailed a little starship through orbit, "
        f"looking for the home beacon that guided brave travelers."
    )
    world.say(f"Then {mystery.opening}.")
    world.say(f"At first, {mystery.false_answer}.")
    world.say(f"But soon {mystery.danger}.")
    world.para()

    world.say(f"{captain.label} gripped the controls while {navigator.label} studied the flickering chart.")
    world.say(f'"Which way should we fly?" {captain.label} asked.')
    world.say(f'"The bright path must be right," {navigator.label} answered, "but the instruments disagree."')
    world.say(f"{correction.mistake}.")
    world.say(f"{params.helper.capitalize()} appeared in a shimmer of silver light and said, {correction.advice}")
    world.say(correction.admission.format(captain=captain.label, navigator=navigator.label, helper=params.helper))
    world.say(f'"Then let us {correction.repair}," {navigator.label} said.')
    world.para()

    world.say(f"They noticed that {mystery.clue}.")
    world.say(params.magic)
    world.say(f"The crew followed the corrected clue, and {mystery.solution}.")
    world.say(f"That was when the great twist appeared: {twist.reveal}.")
    world.say(f"They understood that {twist.meaning}.")
    world.para()

    world.say(f"{captain.label} turned the ship gently while {navigator.label} called out each safe star.")
    world.say(f'"Do you see the beacon now?" {captain.label} asked.')
    world.say(f'"Yes," {navigator.label} replied. "The correction made the hidden path clear."')
    world.say(f"{mystery.changed_fact}.")
    world.say(REFLECTIONS[sum(ord(c) for c in params.correction) % len(REFLECTIONS)])
    world.say(f"They learned that {correction.lesson}.")
    world.say(f"{ending.image}.")
    world.say(ending.final_line + ".")

    captain.meters["fuel"] = 0.7
    captain.memes["humility"] = 1.0
    navigator.meters["attention"] = 1.0
    navigator.memes["trust"] = 1.0
    ship.meters["distance_home"] = 0.0
    beacon.memes["guidance"] = 1.0
    world.facts["resolved"] = True
    world.facts["changed_fact"] = mystery.changed_fact
    world.facts["lesson"] = correction.lesson
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    mystery = world.facts["mystery"]
    correction = world.facts["correction"]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a magical space adventure about {params.captain} and {params.navigator}.",
            f"Include a correction after this danger: {mystery.danger}.",
            f"Use a twist in which {world.facts['twist'].reveal}.",
        ],
        story_qa=[
            QAItem(
                question=f"What danger did {params.captain} and {params.navigator} face?",
                answer=f"They faced this danger: {mystery.danger}. Their first guess was wrong because {mystery.false_answer}.",
            ),
            QAItem(
                question="What correction did the crew make?",
                answer=f"They admitted that {correction.mistake.lower()} and decided to {correction.repair}.",
            ),
            QAItem(
                question="What clue helped them find the safe route?",
                answer=f"They noticed that {mystery.clue}. The magical clue led them to {mystery.solution}.",
            ),
            QAItem(
                question="What changed by the end of the adventure?",
                answer=f"{mystery.changed_fact.capitalize()}. The crew also learned that {correction.lesson}.",
            ),
        ],
        world_qa=[
            QAItem(
                question="What is a home beacon?",
                answer="A home beacon is a light or signal that helps travelers find their way back to a safe place.",
            ),
            QAItem(
                question="Why is a correction useful?",
                answer="A correction is useful because it fixes a mistake before the mistake causes greater trouble.",
            ),
            QAItem(
                question="What makes a space adventure magical?",
                answer="A space adventure can feel magical when the crew meets unusual stars, mysterious signals, or helpful forces beyond ordinary machines.",
            ),
        ],
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} kind={entity.kind:10} location={entity.location:12} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  resolved={world.facts.get('resolved')}")
    lines.append(f"  changed_fact={world.facts.get('changed_fact')}")
    return "\n".join(lines)


def show_qa_item(item: QAItem) -> str:
    return f"Q: {item.question}\nA: {item.answer}"


ASP_RULES = r"""
place(orbit).
activity(correction).
prize(home_beacon).
affords(orbit,correction).
valid(orbit,correction,home_beacon).
safe_after_correction(home_beacon).
twist(magic).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "orbit"),
            asp.fact("activity", "correction"),
            asp.fact("prize", "home_beacon"),
            asp.fact("affords", "orbit", "correction"),
        ]
    )


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [("orbit", "correction", "home_beacon")]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_values = set(valid_combos())
    asp_values = set(asp_valid_combos())
    if python_values != asp_values:
        print("MISMATCH between Python and ASP compatibility gates.")
        print("Python only:", sorted(python_values - asp_values))
        print("ASP only:", sorted(asp_values - python_values))
        return 1
    sample = generate(
        StoryParams(
            captain="Luna",
            navigator="Orin",
            helper="the moon fox",
            mystery="singing_comet",
            correction="map",
            twist="home",
            magic="moon_dust",
            ending="harbor",
        )
    )
    if not sample.story or "correction" not in sample.story.lower():
        print("Generated-story verification failed.")
        return 1
    print("OK: ASP/Python parity and generated-story checks passed.")
    return 0


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"[Prompt {index}] {prompt}")
        for item in sample.story_qa + sample.world_qa:
            print()
            print(show_qa_item(item))


CURATED = [
    StoryParams(
        captain="Luna",
        navigator="Orin",
        helper="the moon fox",
        mystery="singing_comet",
        correction="map",
        twist="home",
        magic="moon_dust",
        ending="harbor",
    ),
    StoryParams(
        captain="Mira",
        navigator="Tavi",
        helper="the old star keeper",
        mystery="glass_moon",
        correction="signal",
        twist="friend",
        magic="star_lantern",
        ending="garden",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
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
        while len(samples) < max(1, args.n) and attempt < max(100, args.n * 30):
            seed = base_seed + attempt
            attempt += 1
            try:
                params = resolve_params(args, random.Random(seed))
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
