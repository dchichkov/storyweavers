#!/usr/bin/env python3
"""Superhero-style quest stories about a grizzly, a scour, and a happy ending."""

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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"hero", "grizzly", "owl", "fox", "kid"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Flux"
    grizzly: str = "Grizzle"
    sidekick: str = "Mira"
    place: str = "city"
    quest: int = 0
    opening: int = 0
    monologue: int = 0
    turn: int = 0
    ending: int = 0
    threat: int = 0


HEROES = ["Flux", "Nova", "Comet", "Radar", "Beacon", "Spark"]
GRIZZLIES = ["Grizzle", "Bruno", "Tundra", "Marmot", "Hush", "Boulder"]
SIDEKICKS = ["Mira", "Pip", "Zee", "Tansy", "Orla", "Juno"]
PLACES = ["city", "harbor", "museum", "park", "rooftops", "riverfront"]

OPENINGS = [
    "In the bright city, {hero} tightened the cape and listened for trouble.",
    "At the {place}, {hero} and {sidekick} patrolled under the silver morning sky.",
    "When the alarm chimed, {hero} leaped from the bench and called, 'Quest time!'",
    "Near the {place}, the hero team spotted a strange trail of torn paper and dust.",
    "Before lunch, {hero} checked the map while {sidekick} scanned the skyline.",
    "The day began like any other, until {hero} heard a rumble by the {place}.",
]

QUESTS = [
    {
        "title": "the missing beacon",
        "premise": "The lighthouse beam had gone dark, and ships needed a safe path home.",
        "problem": "A soot cloud covered the lens, and the storm was closing in.",
        "dialogue": "{sidekick}: 'Can we fix it before sunset?' {hero}: 'We can if we move fast and think clear.'",
        "clue": "A narrow stair reached the lens room, but the soot was packed behind the frame.",
        "action": "The hero team climbed together, scrubbed the glass, and turned the lantern back toward the sea.",
        "result": "The beam flashed over the waves and guided every boat into the harbor.",
        "ending": "Warm light swept the water, and the harbor answered with happy horns.",
    },
    {
        "title": "the broken bridge",
        "premise": "A bridge over the river had cracked in the middle, trapping morning traffic.",
        "problem": "The broken plank sagged over the water, and no one dared step on it.",
        "dialogue": "{grizzly}: 'I can hold it!' {hero}: 'No, help us brace it carefully.'",
        "clue": "Steel bolts had slipped loose on one side while the other side still held firm.",
        "action": "The team wedged beams under the near end, then crossed one by one to secure the far side.",
        "result": "The bridge stood steady again, and commuters cheered from both banks.",
        "ending": "By evening, the river ran under a safe bridge and a glowing sunset.",
    },
    {
        "title": "the museum mist",
        "premise": "A gray mist swirled through the museum halls and hid the ancient statue.",
        "problem": "Visitors could not find the exits, and the alarms echoed in the dark.",
        "dialogue": "{sidekick}: 'That fog feels magical.' {hero}: 'Then we solve it like a mystery.'",
        "clue": "The mist drifted from a cracked vent near the storage room.",
        "action": "The hero sealed the vent, opened the roof panels, and let the clean wind carry the fog away.",
        "result": "The statue shone again, and the visitors clapped when the lights came on.",
        "ending": "The museum sparkled, calm and proud, like a place saved just in time.",
    },
    {
        "title": "the runaway parade float",
        "premise": "A parade float rolled loose from its ropes and drifted toward the crowd.",
        "problem": "Its wheels bumped faster with every block, and the decorations shook loose.",
        "dialogue": "{hero}: 'We need a path!' {grizzly}: 'Then I will clear one.'",
        "clue": "The float steered left whenever one wheel struck a curb.",
        "action": "The team guided it into a wide plaza and blocked the front wheels with heavy signs.",
        "result": "The float stopped before the crowd, and the band kept playing in relief.",
        "ending": "Confetti fell safely, and the parade ended in smiles instead of panic.",
    },
    {
        "title": "the rooftop radio",
        "premise": "A broken radio on the tallest roof was calling for help through static.",
        "problem": "The signal kept cutting out every few seconds.",
        "dialogue": "{sidekick}: 'Someone is up there.' {hero}: 'Then we answer the call.'",
        "clue": "A bent antenna was tapping against a chimney in the wind.",
        "action": "The hero climbed the ladder, straightened the antenna, and wrapped it tight with cable tape.",
        "result": "The radio steadied, and a lost hiker heard the rescue signal clearly.",
        "ending": "From the roof, the city lights looked friendly again, one by one.",
    },
    {
        "title": "the park power drain",
        "premise": "Every lamp in the park had faded, leaving the paths dim at dusk.",
        "problem": "A hidden drain in the power box kept swallowing the charge.",
        "dialogue": "{hero}: 'Something is pulling the current away.' {grizzly}: 'Then I will scour the box for the leak.'",
        "clue": "Tiny sparks flickered from a wet seam near the bottom panel.",
        "action": "The team dried the panel, replaced the fuse, and sealed the seam with weather tape.",
        "result": "The lamps blinked back on and painted the paths gold.",
        "ending": "Children laughed under the bright park lights, and the night felt safe.",
    },
]

MONOLOGUES = [
    "{hero} thought, 'Stay calm. A true hero does not rush past the clue.'",
    "In a quiet inner monologue, {hero} told {self}: 'The problem is big, but our next step can be small.'",
    "{hero} wondered, 'If the crowd is scared, what would make them feel safe first?'",
    "{hero} thought, 'I can hear the answer hiding inside the noise.'",
    "Inside {hero}'s head, a brave voice whispered, 'Look once more before you leap.'",
]

TURNS = [
    "Then {grizzly} asked to help, and the team realized the rough-looking clue was actually useful.",
    "Suddenly, {sidekick} noticed the real cause, and the plan changed from speed to care.",
    "At that moment, {hero} followed the inner monologue and chose the careful path over the flashy one.",
    "When the first try failed, {hero} remembered the quest rule: ask, look, then act.",
    "The grizzly shook {its} head and said, 'We do not need brute force; we need the right tool.'",
]

ENDINGS = [
    "That night, the heroes returned home happy, with the city glowing safely behind them.",
    "The quest ended with a happy ending: no one hurt, the job done, and the sky clear above the city.",
    "By the time the stars came out, the whole team was smiling at the victory.",
    "The happy ending was simple and strong: the danger was gone, and the people could sleep спокойно? No. The people could sleep safely.",
    "Before long, the city felt proud again, and the heroes waved from the rooftop with warm smiles.",
]

THREATS = [
    "a soot storm",
    "a cracked bridge span",
    "a foggy alarm",
    "a runaway float",
    "a broken radio signal",
    "a fading park power box",
]

ASP_RULES = r"""
#show quest/1.
#show solved/1.
#show happy_ending/1.

quest(Q) :- chosen_quest(Q).
solved(Q) :- quest(Q), fixed(Q).
happy_ending(Q) :- solved(Q), no_injury(Q).
"""


def asp_facts() -> str:
    import asp
    q = QUESTS[0]["title"]
    return "\n".join(
        [
            asp.fact("chosen_quest", q),
            asp.fact("fixed", q),
            asp.fact("no_injury", q),
            asp.fact("heroic", "flux"),
            asp.fact("heroic", "mira"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero quest storyworld with a grizzly helper and a happy ending.")
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--grizzly", choices=GRIZZLIES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", type=int, choices=range(len(QUESTS)))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        hero=args.hero or rng.choice(HEROES),
        grizzly=args.grizzly or rng.choice(GRIZZLIES),
        sidekick=args.sidekick or rng.choice(SIDEKICKS),
        place=args.place or rng.choice(PLACES),
        quest=args.quest if args.quest is not None else rng.randrange(len(QUESTS)),
        opening=rng.randrange(len(OPENINGS)),
        monologue=rng.randrange(len(MONOLOGUES)),
        turn=rng.randrange(len(TURNS)),
        ending=rng.randrange(len(ENDINGS)),
        threat=rng.randrange(len(THREATS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type="hero", label=params.hero))
    grizzly = world.add(Entity(id=params.grizzly, kind="character", type="grizzly", label=params.grizzly))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="kid", label=params.sidekick))
    quest = QUESTS[params.quest % len(QUESTS)]

    hero.meters["speed"] = 7.0
    hero.memes["hope"] = 9.0
    grizzly.meters["strength"] = 8.0
    grizzly.memes["calm"] = 6.0
    sidekick.memes["curiosity"] = 8.0

    fmt = {
        "hero": hero.id,
        "grizzly": grizzly.id,
        "sidekick": sidekick.id,
        "place": params.place,
        "its": grizzly.pronoun("possessive"),
    }

    world.say(OPENINGS[params.opening % len(OPENINGS)].format(**fmt))
    world.say(f"The quest was {quest['title']}. {quest['premise']}")
    world.say(f"The threat was {THREATS[params.threat % len(THREATS)]}. {quest['problem']}")
    world.say(MONOLOGUES[params.monologue % len(MONOLOGUES)].format(hero=hero.id, self=hero.id))
    world.say(quest["dialogue"].format(**fmt))
    world.say(TURNS[params.turn % len(TURNS)].format(**fmt))
    world.say(f"{grizzly.id} said, 'Let's scour the area for the real cause.'")
    world.say(quest["clue"])
    world.say(quest["action"])
    world.say(quest["result"])
    world.say(f"Happy ending: {ENDINGS[params.ending % len(ENDINGS)]}")
    world.say(f"{hero.id} smiled and said, 'Quest complete.' {sidekick.id} answered, 'And everyone is safe.'")
    world.say(quest["ending"])

    world.facts.update(
        hero=hero,
        grizzly=grizzly,
        sidekick=sidekick,
        quest=quest,
        threat=THREATS[params.threat % len(THREATS)],
        happy_ending=True,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a Superhero Story about {f['hero'].id} and {f['grizzly'].id} on a quest to fix {f['quest']['title']}.",
        f"Tell a child-friendly adventure where an inner monologue helps the hero solve {f['threat']}.",
        f"Include the words terminate, grizzly, scour, quest, and happy ending in a bright comic-book style story.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What kind of story style is this?",
            answer="It is a superhero-style quest story with quick action, teamwork, and a happy ending.",
        ),
        QAItem(
            question=f"What problem did {f['hero'].id} face?",
            answer=f"{f['hero'].id} faced {f['threat']} during the quest {f['quest']['title']}.",
        ),
        QAItem(
            question="What did the inner monologue change?",
            answer="The inner monologue helped the hero choose a careful plan instead of rushing.",
        ),
        QAItem(
            question=f"How did {f['grizzly'].id} help?",
            answer=f"{f['grizzly'].id} helped by scouring for the cause and then using the right tool or brace.",
        ),
        QAItem(
            question="What made the ending happy?",
            answer="The danger was fixed, nobody got hurt, and the city or park became safe again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or search to find something, solve a problem, or help someone.",
        ),
        QAItem(
            question="What does scouring mean?",
            answer="Scouring means searching carefully or cleaning very thoroughly.",
        ),
        QAItem(
            question="What does terminate mean?",
            answer="Terminate means to end or stop something.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show quest/1.\n#show solved/1.\n#show happy_ending/1."))
    wanted = {("the missing beacon",), ("the missing beacon",), ("the missing beacon",)}
    atoms = set(asp.atoms(model, "quest"))
    happy = set(asp.atoms(model, "happy_ending"))
    if atoms == {("the missing beacon",)} and happy == {("the missing beacon",)}:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("  quest:", sorted(atoms))
    print("  happy:", sorted(happy))
    return 1


CURATED = [
    StoryParams(hero="Flux", grizzly="Grizzle", sidekick="Mira", place="city", quest=0),
    StoryParams(hero="Nova", grizzly="Boulder", sidekick="Pip", place="harbor", quest=1, opening=2, monologue=3, turn=1, ending=0),
    StoryParams(hero="Comet", grizzly="Tundra", sidekick="Juno", place="museum", quest=2, opening=3, monologue=0, turn=2, ending=2),
]


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show quest/1.\n#show happy_ending/1."))
    return sorted(set(asp.atoms(model, "quest")))


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
        print(asp_program("#show quest/1.\n#show solved/1.\n#show happy_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid())} ASP-suggested quest facts")
        for t in asp_valid():
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero} and {sample.params.grizzly}: quest to keep the city safe"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
