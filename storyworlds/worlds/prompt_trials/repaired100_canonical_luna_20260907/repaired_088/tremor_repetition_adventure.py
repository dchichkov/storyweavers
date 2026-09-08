#!/usr/bin/env python3
"""
A small adventure storyworld about Luna, a tremor, and the courage to repeat
a safe path until a lost bell is found.

The world state tracks physical meters and emotional memes. Repetition is not
empty copying: each careful return teaches Luna something, steadies her hands,
and reveals another part of the mountain trail.
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
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the mountain trail"


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
    luna_name: str
    guide_name: str
    trail_id: Optional[str] = None
    telling_mode: Optional[str] = None
    seed: Optional[int] = None


@dataclass(frozen=True)
class Trail:
    id: str
    landmark: str
    obstacle: str
    clue: str
    discovery: str
    repair: str
    ending: str


TRAILS = [
    Trail(
        "echo_bridge",
        "an old rope bridge",
        "a tremor shook the bridge just as the path narrowed",
        "three blue ribbons tied to the safe posts",
        "the repeated ribbon pattern showed a side path around the broken plank",
        "They crossed one post at a time and tied a bright safety ribbon around the loose plank",
        "At sunset, the repaired bridge hummed softly while Luna crossed it with steady steps",
    ),
    Trail(
        "cedar_pass",
        "a giant cedar tree",
        "a tremor rattled the stones and hid the trail markers under dust",
        "the same crescent mark scratched on three flat stones",
        "repeating the crescent marks led them to a sheltered route beneath the cedar",
        "They placed the stones in a clear line and swept the dust away from the trail",
        "The cedar stood like a green tower, and the clear stone line welcomed the next traveler",
    ),
    Trail(
        "silver_cave",
        "a silver cave",
        "a tremor sent pebbles ticking down from the cave roof",
        "a small bell ringing once at every safe turn",
        "the repeated bell sound led them away from a loose ceiling and toward the open exit",
        "They marked the safe turns with chalk arrows and left the cave before dark",
        "Moonlight shone on the arrows, and the little bell rang safely in the cool air",
    ),
    Trail(
        "cloud_ladder",
        "a wooden ladder above the clouds",
        "a tremor made the ladder sway while Luna carried the expedition map",
        "a red knot repeated on every third rung",
        "the knots revealed a firm resting platform halfway up",
        "They secured the map, paused at each red knot, and climbed only when the ladder was still",
        "The map fluttered on the platform, and Luna touched the clouds without rushing",
    ),
    Trail(
        "waterfall_gate",
        "a waterfall gate",
        "a tremor shifted the stones beside the roaring water",
        "two white shells repeated beside each safe stepping stone",
        "the shell pattern showed where the water was shallow enough to cross",
        "They moved loose stones aside and built a clear stepping line with the guide",
        "The waterfall thundered behind them, while the safe shell path gleamed in front",
    ),
]

TRAIL_BY_ID = {t.id: t for t in TRAILS}
LUNA_NAMES = ["Luna", "Mira", "Tess", "Nia", "Sora"]
GUIDE_NAMES = ["Pax", "Ari", "Grandma Sol", "Kai", "Rin"]
TELLING_MODES = ["bold_open", "question_open", "quiet_open", "map_open", "sound_open"]
FOLLOW_THROUGHS = [
    "They copied the safe route onto a card for the next explorer",
    "They practiced the three-step pause before beginning another climb",
    "They tied a bright marker where the trail could be seen from far away",
    "They promised to tell the village what the tremor had changed",
    "They packed the loose tools more securely for the journey home",
]


def _rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0x7A3E)
    text = "|".join([params.luna_name, params.guide_name, params.trail_id or ""])
    return random.Random(sum((i + 1) * ord(ch) for i, ch in enumerate(text)))


def build_world(params: StoryParams) -> World:
    rng = _rng(params)
    trail = TRAIL_BY_ID.get(params.trail_id or "")
    if trail is None:
        trail = rng.choice(TRAILS)
    mode = params.telling_mode if params.telling_mode in TELLING_MODES else rng.choice(TELLING_MODES)
    follow = rng.choice(FOLLOW_THROUGHS)

    world = World(Setting())
    luna = world.add(Entity(params.luna_name, "character", "girl"))
    guide = world.add(Entity(params.guide_name, "character", "guide"))
    bell = world.add(Entity("trail_bell", "thing", "bell", "trail bell"))
    map_item = world.add(Entity("map", "thing", "map", "expedition map"))

    luna.meters.update(balance=1.0, courage=0.0, fatigue=0.0)
    luna.memes.update(curiosity=1.0, worry=1.0)
    guide.memes.update(trust=1.0, patience=1.0)
    bell.meters["lost"] = 1.0
    map_item.meters["clear"] = 0.0

    openings = {
        "bold_open": f"{luna.id} stepped onto the mountain trail with an expedition map tucked under her arm.",
        "question_open": f"Could {luna.id} find the lost trail bell before sunset? She and {guide.id} began along the mountain trail.",
        "quiet_open": f"The mountain trail was quiet until {luna.id} heard a faint metal note far ahead.",
        "map_open": f"On the expedition map, {luna.id} circled {trail.landmark} and set off with {guide.id}.",
        "sound_open": f"Clink, clink, pause. A tiny sound called {luna.id} toward {trail.landmark}.",
    }
    world.say(openings[mode])
    world.say(f"They had not gone far when {trail.obstacle}.")
    world.say(f"The tremor made Luna's hands wobble, and the expedition map slipped toward the trail dust.")

    world.para()
    world.say(f'"We can stop and notice what changed," said {guide.id}.')
    world.say(f'"Then we will repeat the safe part," {luna.id} answered. "One careful try can teach us."')
    world.say(f"They found their first clue: {trail.clue}.")
    world.facts["repetitions"] = 0

    for step in range(1, 4):
        world.facts["repetitions"] += 1
        luna.meters["fatigue"] += 0.2
        luna.meters["balance"] += 0.5
        luna.memes["worry"] = max(0.0, luna.memes["worry"] - 0.3)
        luna.memes["courage"] += 0.5
        world.say(
            f"On repetition {step}, Luna followed the marked safe steps, paused, and looked back at what the tremor had moved."
        )
        if step == 1:
            world.say("The first return showed a cracked stone that they had almost trusted.")
        elif step == 2:
            world.say("The second return showed a safer turn hidden behind a fern.")
        else:
            world.say(f"The third return made the pattern clear: {trail.discovery}.")

    world.para()
    bell.meters["lost"] = 0.0
    map_item.meters["clear"] = 1.0
    luna.memes["courage"] += 1.0
    guide.memes["trust"] += 1.0
    world.say(f"The repetition had worked. They found the trail bell beside {trail.landmark}.")
    world.say(f"{luna.id} lifted it gently, and its bright ring answered the distant echo.")
    world.say(f'"We did not defeat the tremor by pretending it was not there," said {guide.id}.')
    world.say(f'"We learned its new path by repeating the safe one," {luna.id} replied.')

    world.para()
    luna.meters["fatigue"] = 0.0
    luna.meters["balance"] = 2.0
    world.say(f"{trail.repair}.")
    world.say(f"{follow}.")
    world.say(f"{trail.ending}.")

    world.facts.update(
        luna=luna,
        guide=guide,
        bell=bell,
        map=map_item,
        trail=trail,
        place=world.setting.place,
        repetitions=3,
        actual_cause="the tremor changed the trail",
        repair=trail.repair,
        follow_through=follow,
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write an adventurous child-friendly story about {f['luna'].id} exploring {f['place']} after a tremor changes the path.",
        f"Use repetition as a meaningful method: {f['luna'].id} repeats the safe steps three times with {f['guide'].id} and learns from each return.",
        f"End with the lost trail bell found, the path repaired, and a concrete image proving that the mountain adventure changed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    trail = f["trail"]
    return [
        QAItem(
            question=f"What happened to the trail when {f['luna'].id} began the adventure?",
            answer=f"A tremor changed the trail near {trail.landmark}; {trail.obstacle}.",
        ),
        QAItem(
            question=f"Why did {f['luna'].id} repeat the safe steps?",
            answer=f"{f['luna'].id} repeated the safe steps to learn what the tremor had moved and to find a safer route instead of rushing forward.",
        ),
        QAItem(
            question="What clue helped the explorers?",
            answer=f"The useful clue was {trail.clue}. Repeating it across the trail led them to the discovery that {trail.discovery.lower()}.",
        ),
        QAItem(
            question="What did the explorers find?",
            answer=f"They found the lost trail bell beside {trail.landmark}, then used its location and the repeated safe route to understand the changed path.",
        ),
        QAItem(
            question="How did the adventure end?",
            answer=f"{trail.repair}. {trail.ending}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tremor?",
            answer="A tremor is a small shaking movement of the ground or another object.",
        ),
        QAItem(
            question="Why can repetition help during an adventure?",
            answer="Repetition can help because carefully doing something again lets a traveler notice patterns, remember safe steps, and improve.",
        ),
        QAItem(
            question="What is a trail?",
            answer="A trail is a path through a natural place that people or animals can follow.",
        ),
        QAItem(
            question="What does courage mean?",
            answer="Courage means doing something careful and worthwhile even when you feel afraid or uncertain.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.type} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  repetitions: {world.facts.get('repetitions', 0)}")
    lines.append(f"  solved: {world.facts.get('solved', False)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "mountain_trail"),
            asp.fact("event", "tremor"),
            asp.fact("method", "repetition"),
            asp.fact("repeated", "safe_steps", 3),
            asp.fact("goal", "find_bell"),
            asp.fact("action", "repair_path"),
        ]
    )


ASP_RULES = r"""
tremor_present :- event(tremor).
repetition_used :- method(repetition), repeated(safe_steps,3).
bell_recovered :- goal(find_bell), repetition_used.
path_repaired :- action(repair_path), bell_recovered.
valid_story :- tremor_present, repetition_used, path_repaired.
#show valid_story/0.
"""


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    valid = any(symbol.name == "valid_story" for symbol in model)
    if not valid:
        print("MISMATCH: ASP twin did not confirm validity.")
        return 1
    for params in CURATED:
        sample = generate(params)
        world = sample.world
        if world is None or not world.facts.get("solved") or world.facts.get("repetitions") != 3:
            print("MISMATCH: generated story failed the Python reasonableness gate.")
            return 1
        if "tremor" not in sample.story.lower() or "repeat" not in sample.story.lower():
            print("MISMATCH: generated story omitted required narrative instruments.")
            return 1
    print("OK: ASP twin and generated stories confirm the adventure world.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tremor repetition adventure storyworld.")
    parser.add_argument("--name")
    parser.add_argument("--guide")
    parser.add_argument("--trail")
    parser.add_argument("--mode")
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
    trail_id = args.trail or rng.choice(TRAILS).id
    if trail_id not in TRAIL_BY_ID:
        raise StoryError(f"Unknown trail '{trail_id}'. Choose one of: {', '.join(TRAIL_BY_ID)}.")
    mode = args.mode or rng.choice(TELLING_MODES)
    if mode not in TELLING_MODES:
        raise StoryError(f"Unknown telling mode '{mode}'. Choose one of: {', '.join(TELLING_MODES)}.")
    return StoryParams(
        luna_name=args.name or rng.choice(LUNA_NAMES),
        guide_name=args.guide or rng.choice(GUIDE_NAMES),
        trail_id=trail_id,
        telling_mode=mode,
    )


def generate(params: StoryParams) -> StorySample:
    if not params.luna_name.strip() or not params.guide_name.strip():
        raise StoryError("Luna and guide names must not be empty.")
    world = build_world(params)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "Pax", "echo_bridge", "bold_open", 101),
    StoryParams("Mira", "Grandma Sol", "silver_cave", "sound_open", 202),
    StoryParams("Tess", "Kai", "cloud_ladder", "map_open", 303),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

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
