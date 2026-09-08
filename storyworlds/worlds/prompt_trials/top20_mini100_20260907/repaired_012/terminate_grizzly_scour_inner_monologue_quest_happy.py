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

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))),
)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class City:
    name: str
    setting: str = "the bright city"
    alarm_active: bool = False
    threat_level: float = 0.0
    hope_level: float = 0.0
    grime_level: float = 0.0
    cleaned_blocks: int = 0
    quest_done: bool = False
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str
    sidekick_name: str
    city_name: str
    seed: Optional[int] = None


NAMES = ["Ava", "Jules", "Mina", "Kai", "Nova", "Bea", "Rae", "Tobin"]
CITY_NAMES = ["Sunset City", "Skyline Harbor", "Metro Meadow", "Brightbridge"]


class World:
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _rng_for(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    stable = "|".join((params.hero_name, params.sidekick_name, params.city_name))
    seed = int.from_bytes(hashlib.sha256(stable.encode("utf-8")).digest()[:8], "big")
    return random.Random(seed)


ARCS = [
    {
        "premise": [
            "At sunrise, superhero {hero} watched {city} sparkle from the roof of a clock tower. {sidekick} held a map, and both of them were ready for a new quest.",
            "The quest began in {city}, where superhero {hero} tightened their cape while {sidekick} checked the city map for trouble and hidden clues.",
        ],
        "problem": [
            "A greasy gray smudge had spread across every street sign. It was the Grizzly Scour, a sly villainous mess that made the roads unreadable and the city tense.",
            "The Grizzly Scour crawled over the park paths and train stops, leaving the city blurry and sad. Without clear signs, the next rescue would be hard to finish.",
        ],
        "conflict": [
            "\"We can blast it away now,\" said {hero}. {sidekick} shook their head and said, \"If we rush, we might miss the source.\" Their voices bounced across the roof in a small but real conflict.",
            "\"The cleaner beam will fix everything,\" {hero} said. \"Maybe,\" replied {sidekick}, \"but the grime might come back unless we find where it starts.\" Their conflict slowed the quest for a moment.",
        ],
        "turn": [
            "{hero} paused to listen to an inner monologue: first clean the streets, then find the source. That quiet thought gave them calm energy and a smarter plan.",
            "In a quiet inner monologue, {hero} admitted the city needed more than strength. The thought steadied their heart and showed them the quest had to end at the source.",
        ],
        "action": [
            "{hero} and {sidekick} traced the grime to a broken vent beneath the museum. \"You hold the lamp,\" said {hero}, and {sidekick} answered, \"I will guide the brush.\"",
            "They followed the gray trail block by block until it led to a clogged tunnel grate. {sidekick} said, \"Now we scour it clean together,\" and {hero} nodded.",
        ],
        "resolution": [
            "With one careful sweep, they cleared the vent and stopped the Grizzly Scour from spreading. The city lights came back one by one, and the quest felt complete.",
            "The filthy trail broke apart and drifted away like smoke. The villainous mess could not return, because the source had been sealed and cleaned.",
        ],
        "ending": [
            "By nightfall, the streets shone gold again, and the people of {city} cheered their heroes from the sidewalks.",
            "The last cleaned sign gleamed under the moon, and {hero} smiled at {sidekick} as the happy ending settled over the whole city.",
        ],
    },
    {
        "premise": [
            "At the edge of {city}, superhero {hero} heard the emergency siren and leaped from a balcony. {sidekick} rushed beside them with a flashlight for the quest.",
            "The sky over {city} was clear, but the hero team knew trouble could still hide below. {hero} and {sidekick} set out on a city-saving quest.",
        ],
        "problem": [
            "A giant brown smear had coated the community mural. Everyone called it the Grizzly Scour because it spread like a grumpy bear paw across the wall.",
            "The Grizzly Scour had stained the fountain steps and the bus stop benches. It made the whole block look tired, and it would not stop growing.",
        ],
        "conflict": [
            "{hero} wanted to terminate the mess with a blast of foam. {sidekick} said, \"Wait, if we spray too hard, we may damage the mural.\"",
            "\"We need speed,\" said {hero}. \"We need care,\" said {sidekick}. Their conflict was short, but it mattered, because the wall was precious.",
        ],
        "turn": [
            "A brief inner monologue told {hero} to slow down and think like a helper, not just a fighter. That thought changed the whole plan.",
            "{hero} breathed in, listened to an inner monologue, and remembered that a true hero finishes a quest by protecting what people love.",
        ],
        "action": [
            "{hero} used a soft brush while {sidekick} mixed gentle soap. Together they worked from the top corner down, scouring only the dirty parts.",
            "They agreed to terminate the grime one thin layer at a time. \"Brush left,\" said {sidekick}. \"Brush right,\" said {hero}, and the stain peeled away.",
        ],
        "resolution": [
            "The mural's bright colors returned, and the Grizzly Scour could not hide them anymore. The crowd clapped because the heroes had won without breaking anything.",
            "When the last brown streak vanished, the wall looked cheerful again. The quest ended in relief, and the city breathed easier.",
        ],
        "ending": [
            "Children pointed at the repaired mural while the two heroes stood below it, tired but happy.",
            "The painted sun on the wall looked almost as bright as the real one, and that made the ending feel warm.",
        ],
    },
    {
        "premise": [
            "On a windy evening, {hero} and {sidekick} raced to the power station in {city}. Their quest was to keep the lights on before sunset.",
            "Superhero {hero} landed beside {sidekick} on a rooftop, where the city map fluttered in the wind and the next quest began.",
        ],
        "problem": [
            "The Grizzly Scour had jammed the station vents, and the machines groaned under a layer of gray dust. The dark corners of {city} were spreading fast.",
            "Dirty foam was creeping through the subway grates and into the station hall. People nearby worried the city would dim before dinner.",
        ],
        "conflict": [
            "\"Terminate the dust with the big fan,\" said {hero}. {sidekick} replied, \"Not yet. We should scour the vents first.\"",
            "The two heroes argued over the fastest fix, and the conflict made the humming station shake a little harder.",
        ],
        "turn": [
            "While waiting, {hero} had an inner monologue about patience. The thought turned worry into a calm plan.",
            "{sidekick} noticed {hero} go quiet, then heard the answer in an inner monologue: first uncover the source, then clear the path.",
        ],
        "action": [
            "{hero} held the flashlight while {sidekick} scrubbed the vent filter clean. Then they used the fan to blow the dust into a safe bin.",
            "Working side by side, they scoured the filters, opened the vents, and guided the gray mess away from the controls.",
        ],
        "resolution": [
            "The power station lights turned steady and bright again. The Grizzly Scour lost its grip on the machines, and the city kept glowing.",
            "The alarms stopped, the vents breathed freely, and the heroes finished the quest with the station safe.",
        ],
        "ending": [
            "Outside, store windows shimmered back to life, and {city} looked like a row of happy stars.",
            "The last switch clicked into place, and the two heroes shared a smile under the bright control room lamps.",
        ],
    },
]


def _render_beat(template: str, hero: Entity, sidekick: Entity, city: City) -> str:
    return template.format(hero=hero.id, sidekick=sidekick.id, city=city.name)


def tell_path(world: World, hero: Entity, sidekick: Entity, mop: Entity, params: StoryParams) -> dict:
    rng = _rng_for(params)
    arc_index = (params.seed if params.seed is not None else rng.randrange(len(ARCS))) % len(ARCS)
    arc = ARCS[arc_index]
    beats = ("premise", "problem", "conflict", "turn", "action", "resolution", "ending")
    if params.seed is None:
        chosen = {beat: rng.choice(arc[beat]) for beat in beats}
    else:
        variant_code = (params.seed // len(ARCS)) % (2 ** len(beats))
        chosen = {
            beat: arc[beat][(variant_code >> bit) % len(arc[beat])]
            for bit, beat in enumerate(beats)
        }

    rendered = {beat: _render_beat(chosen[beat], hero, sidekick, world.city) for beat in beats}
    for index, beat in enumerate(beats):
        if index:
            world.para()
        world.say(rendered[beat])

    world.city.alarm_active = False
    world.city.threat_level = 0.0
    world.city.hope_level = 1.0
    world.city.grime_level = 0.0
    world.city.cleaned_blocks = 3
    world.city.quest_done = True
    hero.meters["energy"] = 4.0
    sidekick.meters["energy"] = 3.0
    hero.memes["hope"] = 1.0
    sidekick.memes["hope"] = 1.0
    mop.meters["used"] = 1.0
    return {"arc": arc, "rendered": rendered}


def tell(params: StoryParams) -> World:
    city = City(name=params.city_name)
    world = World(city)
    hero = world.add(Entity(id=params.hero_name, kind="character", type="hero", label="superhero"))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", type="sidekick", label="sidekick"))
    mop = world.add(Entity(id="cleaner_mop", kind="thing", type="tool", label="cleaning mop", phrase="a bright cleaning mop"))
    mop.meters["wet"] = 1.0

    path = tell_path(world, hero, sidekick, mop, params)
    arc = path["arc"]
    rendered = path["rendered"]

    world.city.facts = {
        "hero": hero,
        "sidekick": sidekick,
        "mop": mop,
        "city": city,
        "problem": "The Grizzly Scour spread dirty gray grime through the city.",
        "turn": rendered["turn"],
        "action": rendered["action"],
        "resolution": rendered["resolution"],
        "ending": rendered["ending"],
        "quest": "The heroes had to clean the city and stop the grime at its source.",
    }
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.city.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    return [
        "Write a superhero story about a city cleaning quest with an inner monologue and a happy ending.",
        f"Tell a child-friendly quest story where {hero.id} and {sidekick.id} argue briefly, then work together to stop the Grizzly Scour.",
        "Write a short heroic tale that ends with the city shining again after the grime is removed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.city.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    return [
        QAItem(
            question=f"Who was the story about in {world.city.name}?",
            answer=f"It was about {hero.id}, a superhero, and {sidekick.id}, their helper, working together in {world.city.name}.",
        ),
        QAItem(
            question="What was the problem in the story?",
            answer="The Grizzly Scour spread dirty gray grime across the city and made the streets hard to read.",
        ),
        QAItem(
            question=f"What changed after {hero.id} had an inner monologue?",
            answer=f["turn"],
        ),
        QAItem(
            question="How did the heroes finish the quest?",
            answer=f"{f['action']} {f['resolution']} {f['ending']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a brave character who helps people and solves big problems.",
        ),
        QAItem(
            question="What does a quest mean?",
            answer="A quest is a mission or journey to reach an important goal.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem is solved and things finish in a good, warm way.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  city.alarm_active={world.city.alarm_active}")
    lines.append(f"  city.threat_level={world.city.threat_level}")
    lines.append(f"  city.hope_level={world.city.hope_level}")
    lines.append(f"  city.grime_level={world.city.grime_level}")
    lines.append(f"  city.cleaned_blocks={world.city.cleaned_blocks}")
    lines.append(f"  city.quest_done={world.city.quest_done}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(heroic_quest, inner_monologue, grime_cleared, happy_ending).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("theme", "terminate"),
            asp.fact("theme", "grizzly"),
            asp.fact("theme", "scour"),
            asp.fact("feature", "inner_monologue"),
            asp.fact("feature", "quest"),
            asp.fact("feature", "happy_ending"),
            asp.fact("style", "superhero_story"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/4."))
    ok = any(sym.name == "valid_story" for sym in model)
    if ok:
        print("OK: ASP twin recognizes the superhero quest story.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected story fact.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: terminate, grizzly, scour, quest, and happy ending.")
    ap.add_argument("--hero-name")
    ap.add_argument("--sidekick-name")
    ap.add_argument("--city-name", choices=CITY_NAMES)
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
    hero = args.hero_name or rng.choice(NAMES)
    sidekick = args.sidekick_name or rng.choice([n for n in NAMES if n != hero])
    city = args.city_name or rng.choice(CITY_NAMES)
    return StoryParams(hero_name=hero, sidekick_name=sidekick, city_name=city)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible superhero story pattern: terminate + grizzly + scour + inner_monologue + quest + happy_ending")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Ava", "Jules", "Sunset City"),
            StoryParams("Mina", "Kai", "Skyline Harbor"),
            StoryParams("Nova", "Bea", "Brightbridge"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
