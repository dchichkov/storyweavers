#!/usr/bin/env python3
"""
A heartwarming little parade storyworld about a sailor, infantry friends, and a Twist.

Seed words:
- parade
- sailor
- infantry

The world is a small, concrete, child-facing simulation with physical meters and emotional memes.
A sailor helps a parade line up, infantry friends keep order and carry props, and a Twist turns
a problem into a kinder ending.
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


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    location: str = ""
    carried: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: {
        "distance": 0.0,
        "weight": 0.0,
        "brightness": 0.0,
        "order": 0.0,
    })
    memes: dict[str, float] = field(default_factory=lambda: {
        "worry": 0.0,
        "pride": 0.0,
        "trust": 0.0,
        "joy": 0.0,
        "relief": 0.0,
    })


@dataclass
class Setting:
    place: str
    weather: str
    time: str


@dataclass
class StoryParams:
    sailor_name: str
    infantry_name: str
    twist_name: str
    parade_name: str
    setting_name: str
    scenario_index: int = 0
    flavor_index: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace_log: list[str] = []
        self.facts: dict[str, object] = {}

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

    def log(self, text: str) -> None:
        self.trace_log.append(text)


SCENARIOS = [
    {
        "problem": "the parade ribbon had tangled around the mayor's brass bell",
        "misstep": "The first tug only made the knot tighter and jangled the bell so much that the children covered their ears.",
        "clue": "The sailor noticed that the ribbon had a loose end hidden under a paper flower.",
        "action": "He asked the infantry friends to hold the float still while he eased the loose end free with two careful fingers.",
        "result": "The ribbon slipped open, and the parade line could move again without scraping the bell.",
        "twist": "Instead of marching past the bell, the children decided to ring it once for the tired volunteers waiting at the curb.",
        "lesson": "a slow hand can help more than a strong pull",
        "ending": "The repaired ribbon streamed behind the float like a soft red smile.",
    },
    {
        "problem": "the parade drum cart had lost one wheel near the fountain",
        "misstep": "Pushing it harder made the cart wobble and nearly tip the drum onto the stones.",
        "clue": "The sailor saw a round crate lid nearby that fit the wheel axle just right.",
        "action": "The infantry friends lifted the cart, the sailor slipped the lid in place, and together they rolled it gently.",
        "result": "The drum cart moved safely, and the beat came back stronger than before.",
        "twist": "The tiny repair turned the cart into the parade's luckiest float, so everyone tapped the new wheel and laughed.",
        "lesson": "good help can come from noticing what already fits",
        "ending": "The drum beat bounced over the square like a happy heartbeat.",
    },
    {
        "problem": "the parade lanterns were too dim for the cloudy afternoon",
        "misstep": "Trying to light them all at once only wasted the matches and made everyone more worried.",
        "clue": "The sailor found a shiny tin tray that could reflect the gray light into the lantern glass.",
        "action": "The infantry friends held the tray steady while the sailor angled it toward each lantern one by one.",
        "result": "The lanterns glowed warm and gold without any extra flame.",
        "twist": "When the clouds opened for a moment, the reflected light made the parade look as if the sun had joined the march.",
        "lesson": "kind teamwork can brighten a cloudy day",
        "ending": "Each lantern swayed like a small sun above the walking crowd.",
    },
    {
        "problem": "the parade banner had fallen in a puddle and gone heavy with water",
        "misstep": "Lifting it by one corner made the wet cloth sag and splash the shoes of the front row.",
        "clue": "The sailor remembered that a dry rope line ran along the fence beside the street.",
        "action": "He and the infantry friends spread the banner across the rope so it could dry while they walked.",
        "result": "The banner dried enough to wave clean and high again.",
        "twist": "A little girl in the crowd pointed out that the banner's drips had made a new pattern shaped like a heart.",
        "lesson": "sometimes a mistake can become part of the beauty",
        "ending": "The heart-shaped water mark dried into the cloth like a secret blessing.",
    },
    {
        "problem": "the parade's toy horses had lost their painted eyes",
        "misstep": "The first painted dots looked crooked and made the horses seem sleepy instead of proud.",
        "clue": "The sailor borrowed a neat circle stamp from the ticket booth.",
        "action": "The infantry friends held the horses still while he stamped each eye in the same bright spot.",
        "result": "The toy horses looked lively again and seemed ready to trot.",
        "twist": "The smallest horse turned out to be the bravest, and the children named it Captain Pebble on the spot.",
        "lesson": "careful work can bring joy back to old things",
        "ending": "The toy horses gleamed as if they were smiling at the whole street.",
    },
]


OPENINGS = [
    "On a bright morning by the town square,",
    "Just before the parade began,",
    "Under a sky that could not decide between sun and cloud,",
    "As the bells in the square gave one gentle chime,",
    "At the edge of the harbor road,",
    "When the marching drums were still warming up,",
]


CLOSINGS = [
    "The crowd went home smiling, and the square felt warmer for it.",
    "Everybody waved one last time, glad the day had turned out so kindly.",
    "By sunset, even the tired helpers were smiling at one another.",
    "The parade ended softly, with more thank-yous than footsteps.",
]


ASP_RULES = r"""
need_help(parade).
has_sailor.
has_infantry.
twist_happens :- need_help(parade), has_sailor, has_infantry.
happy_end :- twist_happens.
#show twist_happens/0.
#show happy_end/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("need_help", "parade"),
        asp.fact("has_sailor"),
        asp.fact("has_infantry"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming parade storyworld with a sailor, infantry, and a Twist.")
    ap.add_argument("--sailor")
    ap.add_argument("--infantry")
    ap.add_argument("--twist")
    ap.add_argument("--parade")
    ap.add_argument("--setting")
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
    sailor_name = args.sailor or rng.choice(["Sailor Finn", "Captain Rowe", "Nina the Sailor", "Sailor June"])
    infantry_name = args.infantry or rng.choice(["Infantry Team", "Private Poppy", "Corporal Hale", "Infantry Friends"])
    twist_name = args.twist or rng.choice(["Twist", "Twister", "Little Twist", "Twist the Helper"])
    parade_name = args.parade or rng.choice(["parade", "harbor parade", "street parade", "sunny parade"])
    setting_name = args.setting or rng.choice(["the town square", "the harbor road", "the fountain street", "the market lane"])
    return StoryParams(
        sailor_name=sailor_name,
        infantry_name=infantry_name,
        twist_name=twist_name,
        parade_name=parade_name,
        setting_name=setting_name,
        scenario_index=rng.randrange(len(SCENARIOS)),
        flavor_index=rng.randrange(10_000),
    )


def _article(name: str) -> str:
    return name if name.lower().startswith(("a ", "an ", "the ")) else f"the {name}"


def tell(params: StoryParams) -> World:
    scenario = SCENARIOS[params.scenario_index % len(SCENARIOS)]
    setting = Setting(place=params.setting_name, weather="mild", time="morning")
    world = World(setting)

    sailor = world.add(Entity(id="sailor", kind="person", label=params.sailor_name, type="sailor", location=setting.place))
    infantry = world.add(Entity(id="infantry", kind="group", label=params.infantry_name, type="infantry", location=setting.place))
    twist = world.add(Entity(id="twist", kind="helper", label=params.twist_name, type="twist", location=setting.place))
    parade = world.add(Entity(id="parade", kind="event", label=params.parade_name, type="parade", location=setting.place))

    world.facts.update(sailor=sailor, infantry=infantry, twist=twist, parade=parade, scenario=scenario)

    sailor.memes["trust"] += 1
    infantry.memes["joy"] += 1
    parade.meters["order"] = 0.3
    parade.memes["worry"] += 1

    opening = OPENINGS[params.flavor_index % len(OPENINGS)]
    world.say(f"{opening} {params.sailor_name} and {params.infantry_name} were helping the {params.parade_name} get ready at {setting.place}.")
    world.say(f"The trouble was that {scenario['problem']}.")
    world.say(f'{params.sailor_name} said, "We can still save the day."')
    world.say(f'{params.infantry_name} replied, "Then let us start gently, not wildly."')
    world.para()

    parade.memes["worry"] += 1
    world.say(scenario["misstep"])
    world.say(f"{params.twist_name} walked over with a small smile. \"Look closer,\" {params.twist_name} said. {scenario['clue']}")
    world.say(scenario["action"])
    world.say(scenario["result"])
    world.para()

    sailor.memes["pride"] += 1
    infantry.memes["trust"] += 1
    parade.meters["order"] = 1.0
    parade.memes["joy"] += 1
    parade.memes["relief"] += 1
    twist.memes["joy"] += 1

    world.say(f"Then came the Twist: {scenario['twist']}")
    world.say(f'{params.infantry_name} laughed, "That made the whole parade feel kinder."')
    world.say(f'{params.sailor_name} nodded, "Yes, and now everyone has something to cheer for."')
    world.say(f"{scenario['lesson'].capitalize()}.")
    world.say(f"{CLOSINGS[params.flavor_index % len(CLOSINGS)]} {scenario['ending']}")
    world.log(f"scenario={params.scenario_index}")
    return world


def generation_prompts(world: World) -> list[str]:
    scenario: dict[str, str] = world.facts["scenario"]  # type: ignore[assignment]
    sailor: Entity = world.facts["sailor"]  # type: ignore[assignment]
    infantry: Entity = world.facts["infantry"]  # type: ignore[assignment]
    twist: Entity = world.facts["twist"]  # type: ignore[assignment]
    parade: Entity = world.facts["parade"]  # type: ignore[assignment]
    return [
        f"Write a heartwarming story about {sailor.label}, {infantry.label}, and {twist.label} helping a {parade.label}.",
        f"Tell a child-friendly parade story where {scenario['problem']} and the helpers find a kind solution.",
        f"Write a short story that includes the words parade, sailor, infantry, and Twist.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scenario: dict[str, str] = world.facts["scenario"]  # type: ignore[assignment]
    sailor: Entity = world.facts["sailor"]  # type: ignore[assignment]
    infantry: Entity = world.facts["infantry"]  # type: ignore[assignment]
    twist: Entity = world.facts["twist"]  # type: ignore[assignment]
    parade: Entity = world.facts["parade"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What problem did the parade have at the start?",
            answer=f"The parade had a problem because {scenario['problem']}.",
        ),
        QAItem(
            question=f"Why did the first attempt fail?",
            answer=f"The first attempt failed because {scenario['misstep'][0].lower() + scenario['misstep'][1:]}",
        ),
        QAItem(
            question=f"What clue did {twist.label} share?",
            answer=f"{scenario['clue']}",
        ),
        QAItem(
            question=f"How did {sailor.label} and {infantry.label} fix the problem?",
            answer=f"{scenario['action']} {scenario['result']}",
        ),
        QAItem(
            question="What was the Twist in the story?",
            answer=f"{scenario['twist']}",
        ),
        QAItem(
            question="What lesson did the characters learn?",
            answer=f"They learned that {scenario['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is a cheerful procession of people, music, or decorated things moving together for others to see.",
        ),
        QAItem(
            question="What is a sailor?",
            answer="A sailor is a person who works on a boat or ship and knows how to travel on water.",
        ),
        QAItem(
            question="What does infantry mean?",
            answer="Infantry means soldiers who move on foot instead of riding in vehicles.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that turns the story in a new direction.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        parts = [f"type={entity.type}"]
        if entity.location:
            parts.append(f"location={entity.location}")
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"{entity.id}: " + ", ".join(parts))
    return "\n".join(lines)


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show twist_happens/0. #show happy_end/0.")
    model = asp.one_model(program)
    atoms = {f"{sym.name}/{len(sym.arguments)}" for sym in model}
    expected = {"twist_happens/0", "happy_end/0"}
    if atoms != expected:
        print(f"MISMATCH: {sorted(atoms)} != {sorted(expected)}")
        return 1
    print("OK: ASP parity check passed.")
    return 0


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


CURATED = [
    StoryParams(
        sailor_name="Sailor Finn",
        infantry_name="Infantry Friends",
        twist_name="Twist",
        parade_name="parade",
        setting_name="the town square",
    ),
    StoryParams(
        sailor_name="Captain Rowe",
        infantry_name="Corporal Hale",
        twist_name="Little Twist",
        parade_name="harbor parade",
        setting_name="the harbor road",
    ),
    StoryParams(
        sailor_name="Nina the Sailor",
        infantry_name="Private Poppy",
        twist_name="Twister",
        parade_name="sunny parade",
        setting_name="the fountain street",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show twist_happens/0. #show happy_end/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show twist_happens/0. #show happy_end/0."))
        print("ASP model:", " ".join(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
