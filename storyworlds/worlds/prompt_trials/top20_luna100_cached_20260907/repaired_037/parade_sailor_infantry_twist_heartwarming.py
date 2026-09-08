#!/usr/bin/env python3
"""
A small heartwarming storyworld about a parade, a sailor, and an infantry
musician whose unexpected twist brings a whole town together.
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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    label: str
    affords: set[str]


@dataclass
class StoryState:
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
    place: str
    sailor_name: str
    infantry_name: str
    seed: Optional[int] = None
    incident: int = 0
    opening: int = 0
    exchange: int = 0
    twist: int = 0
    ending: int = 0


SETTINGS = {
    "harbor_square": Setting(
        "harbor_square", "the harbor square", {"parade", "sailor", "infantry"}
    ),
    "river_road": Setting(
        "river_road", "the riverside road", {"parade", "sailor", "infantry"}
    ),
    "town_green": Setting(
        "town_green", "the town green", {"parade", "sailor", "infantry"}
    ),
}

SAILOR_NAMES = ["Mara", "Jonah", "Sela", "Finn", "Nora", "Cal"]
INFANTRY_NAMES = ["Iris", "Theo", "June", "Mateo", "Lena", "Sam"]

OPENINGS = [
    "On a bright morning, {sailor} the sailor polished a brass whistle before the town parade.",
    "Flags fluttered above {place} as sailor {sailor} joined the waiting parade.",
    "The town woke to drums and gulls while {sailor}, a cheerful sailor, marched toward the parade.",
    "At {place}, families gathered for the parade, and {sailor} checked every ribbon on the sailors' banner.",
    "The parade was ready to begin when {sailor} carried a small blue flag toward the front.",
]

EXCHANGES = [
    '"The music is ready," said infantry {infantry}. "But why are you looking at the empty wagon?"\n'
    '"Because someone should be riding in it," {sailor} replied.',
    '"I hear a missing beat," said {infantry}.\n'
    '"Maybe it is waiting for the right person," answered {sailor}.',
    '"The parade can still go on," {infantry} said gently.\n'
    '"Yes," said {sailor}, "but it can also make room."',
    '"What is inside that quiet wagon?" asked {infantry}.\n'
    '"A surprise we have not understood yet," said {sailor}.',
]

INCIDENTS = [
    {
        "problem": "the oldest parade drum had split along its wooden rim",
        "risk": "march without a steady beat and leave the smallest children behind",
        "clue": "a soft tapping came from the empty wagon behind the band",
        "action": "walked over to listen instead of starting the parade",
        "helper": "a shy child who had learned a rhythm by tapping on the kitchen table",
        "twist": "the child was the retired drummer's granddaughter, carrying his repaired drum",
        "repair": "The band made room for her, and the sailor tied a blue ribbon around the drum.",
        "ending": "The new drummer led the parade with a bright beat, and the old drummer smiled from the front porch.",
        "lesson": "a parade grows stronger when it makes room for a new marcher",
    },
    {
        "problem": "the flag rope snapped just before the parade began",
        "risk": "let the town banner fall into a muddy puddle",
        "clue": "a pair of careful hands had already gathered the loose ends",
        "action": "stop the marching line and ask who had found the rope",
        "helper": "a quiet harbor cleaner who knew every knot on the waterfront",
        "twist": "the cleaner had once sailed with the sailor's grandmother",
        "repair": "Together they tied a strong sailor's knot and raised the banner high.",
        "ending": "The flag waved above the parade, carrying two generations of harbor memories.",
        "lesson": "help can arrive from people whose stories we have not yet heard",
    },
    {
        "problem": "the infantry horn player lost her voice",
        "risk": "make the band turn around before the veterans could hear its welcome",
        "clue": "a small paper horn answered from the edge of the crowd",
        "action": "follow the tiny sound and invite its maker closer",
        "helper": "a child who had built the paper horn from an old program",
        "twist": "the child was the horn player's brother, practicing her favorite call",
        "repair": "The sailor held the music sheet while the child played the opening notes beside his sister.",
        "ending": "The sister conducted with her hands, and the paper horn answered like a bright little bird.",
        "lesson": "love can carry a song even when a voice needs to rest",
    },
    {
        "problem": "rain soaked the parade route",
        "risk": "send the marching children onto slippery stones",
        "clue": "shopkeepers were quietly moving benches beneath the covered market",
        "action": "change the route and ask the crowd to help",
        "helper": "the town baker, who had a cart with broad wooden wheels",
        "twist": "the baker had planned a secret indoor parade for the nursing home",
        "repair": "The sailor guided the flags through the market while infantry musicians played from the dry steps.",
        "ending": "Rain drummed on the roof as the parade danced safely between warm tables and smiling faces.",
        "lesson": "a changed plan can uncover a kinder celebration",
    },
    {
        "problem": "the lead carriage wheel came loose",
        "risk": "make the carriage wobble into the marching line",
        "clue": "a silver toolbox appeared from beneath a nearby blanket",
        "action": "halt the parade and ask for a careful inspection",
        "helper": "an elderly mechanic who had been watching from the crowd",
        "twist": "he had repaired the sailor's first toy boat when she was small",
        "repair": "The mechanic fixed the wheel, and the sailor thanked him before inviting him to ride at the front.",
        "ending": "The repaired carriage rolled smoothly, with the old mechanic waving beside the town banner.",
        "lesson": "remembered kindness can return at exactly the right moment",
    },
]

TWISTS = [
    "Then the crowd discovered that the quiet helper had been preparing a gift for someone else all along.",
    "The surprise was not a rescue from outside the parade; it was a forgotten piece of the town's own history.",
    "Instead of replacing the missing part, the helper showed everyone how many hands could share it.",
    "The person who seemed least ready to join became the one who gave the parade its heart.",
]

ENDINGS = [
    "By sunset, the flags were folded, but the new friendship kept marching through the town.",
    "When the last drum faded, people stayed together to tell stories and share warm bread.",
    "The parade ended at the harbor, where every helper received a ribbon and a thankful cheer.",
    "The town remembered that day not for the trouble, but for the way everyone made room.",
]


ASP_RULES = r"""
#show valid/2.
setting(harbor_square). setting(river_road). setting(town_green).
affords(harbor_square,parade).
affords(harbor_square,sailor).
affords(harbor_square,infantry).
affords(river_road,parade).
affords(river_road,sailor).
affords(river_road,infantry).
affords(town_green,parade).
affords(town_green,sailor).
affords(town_green,infantry).
valid(P, F) :- setting(P), affords(P, F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for feature in sorted(setting.affords):
            lines.append(asp.fact("affords", place, feature))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid() -> list[tuple[str, str]]:
    return sorted((place, feature) for place, s in SETTINGS.items() for feature in s.affords)


def asp_valid() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program()), "valid")))


def asp_verify() -> int:
    py = set(python_valid())
    clingo = set(asp_valid())
    if py == clingo:
        print(f"OK: clingo gate matches Python gate ({len(py)} combinations).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  only in clingo:", sorted(clingo - py))
    print("  only in Python:", sorted(py - clingo))
    return 1


def build_world(params: StoryParams) -> StoryState:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown parade setting: {params.place}")
    setting = SETTINGS[params.place]
    incident = INCIDENTS[params.incident % len(INCIDENTS)]
    world = StoryState(setting)

    sailor = world.add(Entity(
        params.sailor_name, "character", "sailor", "the sailor",
        ["steady", "kind"], {"balance": 1.0}, {"belonging": 0.6}
    ))
    infantry = world.add(Entity(
        params.infantry_name, "character", "infantry", "the infantry musician",
        ["brave", "attentive"], {"marching": 1.0}, {"care": 0.7}
    ))
    parade = world.add(Entity(
        "parade", "thing", "parade", "the parade",
        ["joyful", "public"], {"order": 0.8}, {"hope": 0.8}
    ))
    helper = world.add(Entity(
        "helper", "character", "helper", incident["helper"],
        ["quiet", "useful"], {"readiness": 0.7}, {"belonging": 0.4}
    ))

    world.say(OPENINGS[params.opening % len(OPENINGS)].format(
        sailor=sailor.id, place=setting.label
    ))
    world.say(f"{infantry.id} stood beside the band, ready to play, when they learned that {incident['problem']}.")
    world.say(EXCHANGES[params.exchange % len(EXCHANGES)].format(
        sailor=sailor.id, infantry=infantry.id
    ))

    world.para()
    world.say(f"The trouble could {incident['risk']}.")
    world.say(f"Then {incident['clue']}. {sailor.id} chose to {incident['action']}.")
    world.say(f'{infantry.id} called, "Let us listen before we hurry." {sailor.id} nodded and held the parade in place.')
    world.facts["tension"] = incident["problem"]
    world.facts["risk"] = incident["risk"]
    world.facts["choice"] = incident["action"]
    world.say(f"{helper.label.capitalize()} stepped forward. {incident['twist']}.")
    world.say(TWISTS[params.twist % len(TWISTS)])
    world.say(f'"I can help," said {helper.label}. "{incident["lesson"].capitalize()}."')

    world.para()
    world.say(incident["repair"])
    world.say(
        f'"You changed the parade," {infantry.id} told {sailor.id}. '
        f'"We changed it together," replied {sailor.id}.'
    )
    world.say(incident["ending"])
    world.say(ENDINGS[params.ending % len(ENDINGS)])

    world.facts.update(
        sailor=sailor,
        infantry=infantry,
        helper=helper,
        parade=parade,
        incident=incident,
        place=setting.label,
    )
    return world


def generation_prompts(world: StoryState) -> list[str]:
    f = world.facts
    return [
        f"Write a heartwarming parade story in {f['place']} featuring a sailor and an infantry musician.",
        f"Tell a child-friendly story where a parade problem is solved through listening, kindness, and an unexpected twist.",
        f"Write a gentle story about {f['sailor'].id} and {f['infantry'].id} making room for a surprising helper.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    f = world.facts
    incident = f["incident"]
    sailor = f["sailor"].id
    infantry = f["infantry"].id
    helper = f["helper"].label
    return [
        QAItem(
            "Who helped lead the parade?",
            f"{sailor} the sailor and {infantry} the infantry musician helped lead the parade and kept everyone working together.",
        ),
        QAItem(
            "What problem interrupted the parade?",
            f"The parade was interrupted because {incident['problem']}. That could {incident['risk']}.",
        ),
        QAItem(
            "What did the sailor and infantry musician do first?",
            f"They paused the parade and chose to {incident['action']}. They listened for clues instead of rushing.",
        ),
        QAItem(
            "What was the story's twist?",
            f"The twist was that {incident['twist']}. The unexpected connection made the solution especially meaningful.",
        ),
        QAItem(
            "How did the parade end?",
            f"{incident['ending']} The town learned that {incident['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            "What is a parade?",
            "A parade is an organized procession in which people walk or ride together while music, flags, or decorations make a public celebration.",
        ),
        QAItem(
            "What does a sailor do?",
            "A sailor works or travels on a boat or ship and learns skills for staying safe and useful at sea.",
        ),
        QAItem(
            "What is infantry?",
            "Infantry are soldiers who serve and move on foot, often working together as a coordinated group.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:12} ({entity.type:10}) "
            f"traits={entity.traits} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    if place not in SETTINGS:
        raise StoryError(f"Unknown place: {place}")
    sailor = args.sailor or rng.choice(SAILOR_NAMES)
    infantry = args.infantry or rng.choice(INFANTRY_NAMES)
    if sailor == infantry:
        alternatives = [name for name in INFANTRY_NAMES if name != sailor]
        infantry = rng.choice(alternatives)
    return StoryParams(
        place=place,
        sailor_name=sailor,
        infantry_name=infantry,
        incident=rng.randrange(len(INCIDENTS)),
        opening=rng.randrange(len(OPENINGS)),
        exchange=rng.randrange(len(EXCHANGES)),
        twist=rng.randrange(len(TWISTS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming parade world with a sailor, infantry musician, and twist."
    )
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--sailor")
    parser.add_argument("--infantry")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        for place, feature in asp_valid():
            print(f"{place:14} {feature}")
        return
    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, place in enumerate(SETTINGS):
            params = StoryParams(
                place=place,
                sailor_name=SAILOR_NAMES[i % len(SAILOR_NAMES)],
                infantry_name=INFANTRY_NAMES[i % len(INFANTRY_NAMES)],
                incident=i % len(INCIDENTS),
                opening=i % len(OPENINGS),
                exchange=i % len(EXCHANGES),
                twist=i % len(TWISTS),
                ending=i % len(ENDINGS),
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                params.incident = (params.incident + 1) % len(INCIDENTS)
                sample = generate(params)
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
