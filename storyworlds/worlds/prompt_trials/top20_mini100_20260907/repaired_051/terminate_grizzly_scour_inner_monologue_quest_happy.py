#!/usr/bin/env python3
"""
A tiny superhero-style storyworld about a hero who must terminate a problem,
a grizzly who complicates the quest, and a careful scour through the city to
reach a happy ending.

The simulation tracks:
- physical meters: distance, size, weight, mess, damage, reach, brightness
- emotional memes: fear, resolve, hope, trust, relief, pride

Every story is driven by state changes: a quest begins with a problem, the
hero thinks through the next move, the hero and allies scour a place, and the
ending proves what changed.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


CITY_NAME = "Bright Harbor"


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    location: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: {
        "distance": 0.0,
        "size": 0.0,
        "weight": 0.0,
        "mess": 0.0,
        "damage": 0.0,
        "reach": 0.0,
        "brightness": 0.0,
    })
    memes: dict[str, float] = field(default_factory=lambda: {
        "fear": 0.0,
        "resolve": 0.0,
        "hope": 0.0,
        "trust": 0.0,
        "relief": 0.0,
        "pride": 0.0,
    })

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "hero": {"subject": "he", "object": "him", "possessive": "his"},
            "villain": {"subject": "he", "object": "him", "possessive": "his"},
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "woman": {"subject": "she", "object": "her", "possessive": "her"},
            "person": {"subject": "they", "object": "them", "possessive": "their"},
            "grizzly": {"subject": "he", "object": "him", "possessive": "his"},
            "sidekick": {"subject": "she", "object": "her", "possessive": "her"},
            "robot": {"subject": "it", "object": "it", "possessive": "its"},
        }
        return mapping.get(self.type, mapping["person"])[case]


@dataclass
class Setting:
    city: str = CITY_NAME
    place: str = "the old clock tower district"


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    sidekick_name: str
    sidekick_type: str
    grizzly_name: str
    grizzly_type: str
    terminate_target: str
    scour_place: str
    quest_title: str
    seed: Optional[int] = None
    scenario_index: int = 0
    detail_index: int = 0


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace_log: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def log(self, text: str) -> None:
        self.trace_log.append(text)


SCENARIOS = [
    {
        "problem": "a masked drone had dropped magnetic trash across the train bridge",
        "turn": "The magnets kept dragging the trash back together, making the bridge unsafe.",
        "inner": "If I rush, I'll make it worse. If I think first, I can terminate the mess.",
        "scour": "scour the bridge beams for the hidden controller",
        "mistake": "The hero tried to grab the biggest pile, but the metal snapped toward the wrong side of the bridge.",
        "clue": "The grizzly sniffed out a tiny blinking light under a bench plank.",
        "action": "The hero and sidekick lifted the plank, found the controller, and wrapped it in a thick scarf.",
        "result": "The magnetic pull stopped at once, and the bridge grew quiet and safe again.",
        "image": "trash bags fluttered neatly beside a clean bridge while gulls circled above",
    },
    {
        "problem": "stormwater had flooded the museum basement and trapped the power fuse",
        "turn": "The water kept rising whenever someone pulled the wrong lever.",
        "inner": "I need a plan, not a panic. The quest is to terminate the flood before it reaches the exhibits.",
        "scour": "scour the basement shelves for the red fuse box",
        "mistake": "The first lever opened a back valve and sent more water sloshing into the room.",
        "clue": "The grizzly pointed to a trail of paint chips leading behind a broken crate.",
        "action": "The hero followed the trail, pried open the crate, and shut the fuse box door with a strong click.",
        "result": "The pumps woke up and drained the basement before any ancient mask got wet.",
        "image": "museum lights glowed over dry stone floors and one safe glass case",
    },
    {
        "problem": "a wind machine had tangled the city festival banners in the radio tower",
        "turn": "If the banners stayed stuck, the parade signal would never reach the streets.",
        "inner": "I can terminate this tangle if I stay calm and search every rung.",
        "scour": "scour the tower stairs for the loose spool",
        "mistake": "A quick tug tightened the knot and nearly tore a blue banner in half.",
        "clue": "The grizzly saw that one banner edge was hooked around a tiny brass spool.",
        "action": "The hero climbed carefully, unwound the spool, and handed the banner down to the sidekick.",
        "result": "The banners swung free, and the parade signal flashed across the whole city.",
        "image": "red and blue banners waved high above rooftops like victory ribbons",
    },
    {
        "problem": "a sneaky slime trail had covered the library steps and frightened the readers",
        "turn": "The slime kept spreading whenever shoes stepped on it.",
        "inner": "A hero should not slip, shout, or give up. I can terminate this spill.",
        "scour": "scour the reading hall for the cleaning gel",
        "mistake": "The first wipe only smeared the slime into a wider green ribbon.",
        "clue": "The grizzly noticed the gel under a toppled ladder by the index cards.",
        "action": "The hero and sidekick spread the gel, scraped the slime into buckets, and mopped the steps dry.",
        "result": "Readers came back, and the library smelled like soap instead of swamp.",
        "image": "children climbed the steps with books held high and dry",
    },
    {
        "problem": "a runaway toy robot had locked itself inside the fireworks shed",
        "turn": "The robot was pressing buttons at random, and sparks were starting to pop.",
        "inner": "I need to terminate the danger before the night show begins.",
        "scour": "scour the shed wall for the emergency switch",
        "mistake": "The hero yelled a command, but the robot only spun in a tighter circle.",
        "clue": "The grizzly heard a faint beep behind a crate of safe sparklers.",
        "action": "The hero opened the crate, found the emergency switch, and calmly shut the robot down.",
        "result": "The shed went still, and the fireworks stayed ready for the sky.",
        "image": "golden sparks waited in neat boxes under a silent roof",
    },
    {
        "problem": "the river gate had jammed and pushed water toward the harbor market",
        "turn": "If the gate broke loose, the stalls would flood.",
        "inner": "This is my quest: terminate the jam, protect the market, and keep everyone dry.",
        "scour": "scour the gatehouse for the missing latch pin",
        "mistake": "A strong shove made the gate clang, but it stayed stuck.",
        "clue": "The grizzly found muddy pawprints leading to a tiny latch pin under a barrel.",
        "action": "The hero slipped the pin back into place while the sidekick held the wheel steady.",
        "result": "The gate opened slowly, and the river moved away from the market instead of into it.",
        "image": "fishmongers smiled beside a dry boardwalk and a calm green river",
    },
]

OPENINGS = [
    "At sunrise",
    "Before lunch",
    "On a bright afternoon",
    "As thunder rolled far away",
    "Just after the city bells rang",
    "When the streetlamps were still on",
]


@dataclass
class Runtime:
    world: World
    params: StoryParams


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero Story: terminate a problem, scour for clues, and reach a happy ending.")
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type")
    ap.add_argument("--sidekick-name")
    ap.add_argument("--sidekick-type")
    ap.add_argument("--grizzly-name")
    ap.add_argument("--grizzly-type")
    ap.add_argument("--terminate-target")
    ap.add_argument("--scour-place")
    ap.add_argument("--quest-title")
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
    hero_name = args.hero_name or rng.choice(["Nova", "Blaze", "Comet", "Spark", "Ruby"])
    hero_type = args.hero_type or rng.choice(["hero", "woman", "girl", "person"])
    sidekick_name = args.sidekick_name or rng.choice(["Mica", "Dale", "Sunny", "Pip", "Echo"])
    sidekick_type = args.sidekick_type or rng.choice(["person", "girl", "hero", "robot"])
    grizzly_name = args.grizzly_name or rng.choice(["Grizzle", "Bearfax", "Bruno", "Moss", "Hank"])
    grizzly_type = args.grizzly_type or "grizzly"
    scenario = SCENARIOS[rng.randrange(len(SCENARIOS))]
    terminate_target = args.terminate_target or rng.choice(["the mess", "the threat", "the jam", "the spill", "the danger"])
    scour_place = args.scour_place or rng.choice(["the bridge", "the basement", "the tower", "the steps", "the shed", "the gatehouse"])
    quest_title = args.quest_title or rng.choice([
        "the city rescue quest",
        "the bright harbor quest",
        "the sky-high cleanup quest",
        "the midnight save quest",
    ])
    return StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        sidekick_name=sidekick_name,
        sidekick_type=sidekick_type,
        grizzly_name=grizzly_name,
        grizzly_type=grizzly_type,
        terminate_target=terminate_target,
        scour_place=scour_place,
        quest_title=quest_title,
        scenario_index=SCENARIOS.index(scenario),
        detail_index=rng.randrange(10_000),
    )


def _article(name: str) -> str:
    low = name.lower()
    if low.startswith(("a ", "an ", "the ")):
        return name
    return f"the {name}"


def tell(params: StoryParams) -> World:
    w = World(Setting())
    scenario = SCENARIOS[params.scenario_index % len(SCENARIOS)]

    hero = w.add(Entity("hero", "hero", params.hero_type, params.hero_name, location=w.setting.place))
    sidekick = w.add(Entity("sidekick", "sidekick", params.sidekick_type, params.sidekick_name, location=w.setting.place))
    grizzly = w.add(Entity("grizzly", "animal", "grizzly", params.grizzly_name, location=w.setting.place))
    problem = w.add(Entity("problem", "thing", "thing", params.terminate_target, location=w.setting.place))
    clue = w.add(Entity("clue", "thing", "thing", "clue", location=w.setting.place))
    quest = w.add(Entity("quest", "thing", "thing", params.quest_title, location=w.setting.place))

    w.facts.update({
        "hero": hero,
        "sidekick": sidekick,
        "grizzly": grizzly,
        "problem": problem,
        "clue": clue,
        "quest": quest,
        "scenario": scenario,
    })

    hero.memes["hope"] += 1
    sidekick.memes["trust"] += 1
    grizzly.memes["fear"] += 1

    opening = OPENINGS[params.detail_index % len(OPENINGS)]
    w.say(f"{opening}, {_article(hero.label)} and {_article(sidekick.label)} met {_article(grizzly.label)} at {w.setting.city}'s {w.setting.place}.")
    w.say(f'"This is our {params.quest_title}," {hero.label} said. "We have to {params.terminate_target}."')
    w.say(f'"Then we will need to {scenario["scour"]}," {sidekick.label} said, and the grizzly nodded because the city felt too big to search alone.')
    w.para()

    hero.memes["resolve"] += 1
    sidekick.memes["fear"] += 1
    w.say(scenario["problem"].capitalize() + ".")
    w.say(f"The danger made everyone stop. {hero.label} looked at the scene and thought, \"{scenario['inner']}\"")
    w.say(f'The first try went wrong: {scenario["mistake"]}')
    w.para()

    grizzly.memes["trust"] += 1
    grizzly.memes["hope"] += 1
    w.say(f'"Wait," said {grizzly.label}. "{scenario["clue"]}"')
    w.say(f"The clue changed the plan. Instead of forcing the problem, the team decided to {scenario['scour']} together.")
    w.say(scenario["action"])
    w.para()

    problem.meters["damage"] = 0.0
    problem.meters["mess"] = 0.0
    problem.meters["brightness"] += 1.0
    hero.memes["hope"] += 1
    hero.memes["pride"] += 1
    sidekick.memes["relief"] += 1
    grizzly.memes["relief"] += 1

    w.say(f"{scenario['result']} {hero.label} smiled and said, \"We did it. We terminated the problem without hurting the city.\"")
    w.say(f'{sidekick.label} laughed, and {grizzly.label} answered, "That was a real quest."')
    w.para()

    w.say(f"By evening, the city had a happy ending: {scenario['image']}.")
    w.say(f"{hero.label} knew the lesson now. A hero could win by searching carefully, listening to friends, and trusting a good clue.")
    w.log(f"scenario={params.scenario_index % len(SCENARIOS)}")
    w.log("ending=happy")
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    sidekick: Entity = f["sidekick"]  # type: ignore[assignment]
    grizzly: Entity = f["grizzly"]  # type: ignore[assignment]
    quest: Entity = f["quest"]  # type: ignore[assignment]
    scenario: dict[str, str] = f["scenario"]  # type: ignore[assignment]
    return [
        f"Write a superhero story about {hero.label}, {sidekick.label}, and {grizzly.label} on a quest to {scenario['problem']}.",
        f"Tell a child-friendly story that uses the words terminate, grizzly, scour, Quest, Inner Monologue, and Happy Ending.",
        f"Write a short superhero rescue tale where the heroes must {scenario['scour']} and finish with a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    sidekick: Entity = f["sidekick"]  # type: ignore[assignment]
    grizzly: Entity = f["grizzly"]  # type: ignore[assignment]
    quest: Entity = f["quest"]  # type: ignore[assignment]
    scenario: dict[str, str] = f["scenario"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What was the quest in the story?",
            answer=f"The quest was {quest.label}, and it required the heroes to face the city's problem instead of ignoring it.",
        ),
        QAItem(
            question=f"What did the hero think in the inner monologue?",
            answer=f"The hero thought, \"{scenario['inner']}\" That thought helped the hero slow down and make a better plan.",
        ),
        QAItem(
            question=f"What clue did the grizzly give the team?",
            answer=f"{scenario['clue']} That clue showed where to search next.",
        ),
        QAItem(
            question=f"How did the team terminate the problem?",
            answer=f"{scenario['action']} {scenario['result']}",
        ),
        QAItem(
            question=f"What made the ending happy?",
            answer=f"The danger was removed, the city became safe again, and everyone felt relief and pride at the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest in a superhero story?",
            answer="A quest is a mission or important goal that heroes try to complete, often by solving a problem and helping others.",
        ),
        QAItem(
            question="What does it mean to scour a place?",
            answer="To scour a place means to search it carefully and thoroughly, looking in many spots instead of only one.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thoughts, spoken in the mind rather than out loud.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the main problem is solved and the characters finish with safety, relief, or joy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for p in sample.prompts:
        parts.append(p)
    parts.append("")
    parts.append("== story qa ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in world.entities.values():
        meters = {k: round(v, 2) for k, v in ent.meters.items() if v}
        memes = {k: round(v, 2) for k, v in ent.memes.items() if v}
        bits = [f"type={ent.type}", f"loc={ent.location}"]
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{ent.id}: " + ", ".join(bits))
    for item in world.trace_log:
        lines.append(f"* {item}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H).
sidekick(S).
grizzly(G).
quest(Q).

problem_solved :- found_clue, planned, acted.
happy_ending :- problem_solved, city_safe.
city_safe :- not danger_left.

#show problem_solved/0.
#show happy_ending/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("found_clue"),
        asp.fact("planned"),
        asp.fact("acted"),
        asp.fact("city_safe"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show problem_solved/0. #show happy_ending/0."))
    atoms = {f"{sym.name}/{len(sym.arguments)}" for sym in model}
    expected = {"problem_solved/0", "happy_ending/0"}
    if atoms != expected:
        print(f"MISMATCH: {sorted(atoms)} != {sorted(expected)}")
        return 1
    sample = generate(CURATED[0])
    if "happy ending" not in sample.story.lower():
        print("MISMATCH: generated story did not include a happy ending.")
        return 1
    print("OK: ASP parity and story verification passed.")
    return 0


CURATED = [
    StoryParams(
        hero_name="Nova",
        hero_type="hero",
        sidekick_name="Mica",
        sidekick_type="person",
        grizzly_name="Grizzle",
        grizzly_type="grizzly",
        terminate_target="the magnetic trash storm",
        scour_place="the bridge",
        quest_title="the city rescue quest",
        scenario_index=0,
        detail_index=101,
    ),
    StoryParams(
        hero_name="Spark",
        hero_type="hero",
        sidekick_name="Dale",
        sidekick_type="person",
        grizzly_name="Bearfax",
        grizzly_type="grizzly",
        terminate_target="the flooded basement",
        scour_place="the museum",
        quest_title="the bright harbor quest",
        scenario_index=1,
        detail_index=202,
    ),
    StoryParams(
        hero_name="Ruby",
        hero_type="woman",
        sidekick_name="Echo",
        sidekick_type="robot",
        grizzly_name="Bruno",
        grizzly_type="grizzly",
        terminate_target="the tangled banner trap",
        scour_place="the tower",
        quest_title="the sky-high cleanup quest",
        scenario_index=2,
        detail_index=303,
    ),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show problem_solved/0. #show happy_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show problem_solved/0. #show happy_ending/0."))
        print("ASP model:", " ".join(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        limit = max(args.n * 20, 20)
        while len(samples) < args.n and i < limit:
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
