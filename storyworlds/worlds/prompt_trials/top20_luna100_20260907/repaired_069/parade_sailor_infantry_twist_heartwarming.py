#!/usr/bin/env python3
"""Heartwarming parade stories about a sailor, infantry helpers, and a kind twist."""

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
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    sailor: str = "Mara"
    infantry_leader: str = "Jon"
    child: str = "Lina"
    parade_place: str = "harbor square"
    event: int = 0
    opening: int = 0
    dialogue: int = 0
    twist: int = 0
    ending: int = 0


SAILORS = ["Mara", "Nell", "Ivo", "Rae", "Tessa"]
INFANTRY = ["Jon", "Ada", "Bo", "Cora", "Milo"]
CHILDREN = ["Lina", "Pip", "Noah", "Mina", "Sol"]
PLACES = ["harbor square", "the sunny quay", "the old waterfront", "the town green"]

EVENTS = [
    {
        "title": "the little sail",
        "problem": "A bright parade sail tore just before the marching band reached the square.",
        "clue": "The sailor noticed that the tear followed an old seam rather than the strong cloth.",
        "action": "The infantry formed a windbreak while the sailor stitched a small golden patch over the seam.",
        "result": "The sail opened again and cast a warm patch of shade over the waiting children.",
        "object": "parade sail",
        "lesson": "A small repair can carry a great deal of hope.",
    },
    {
        "title": "the missing drum",
        "problem": "The parade drum rolled beneath the pier when a gust tugged its strap loose.",
        "clue": "The sailor saw its red ribbon caught on a low post beside the water.",
        "action": "The infantry made a safe human chain while the sailor reached with a boat hook and drew the drum back.",
        "result": "The drummer found the beat, and every marcher stepped together again.",
        "object": "parade drum",
        "lesson": "Careful teamwork can bring back a lost rhythm.",
    },
    {
        "title": "the tangled flags",
        "problem": "A string of flags twisted around the parade arch and blocked the entrance.",
        "clue": "The sailor saw that the knot began where one blue flag had been tied backward.",
        "action": "The infantry held the arch steady while the sailor loosened the first knot and retied each flag in order.",
        "result": "The flags fluttered freely, and the crowd could pass beneath them.",
        "object": "parade flags",
        "lesson": "Finding the first small cause can untangle a large trouble.",
    },
    {
        "title": "the quiet trumpet",
        "problem": "The lead trumpeter lost her voice before the parade's final song.",
        "clue": "The sailor remembered a hand signal used aboard ships when waves swallowed every sound.",
        "action": "The infantry carried bright signal cards while the sailor taught the band a silent pattern for the marching beat.",
        "result": "The band played softly, and the crowd joined by clapping the missing rhythm.",
        "object": "signal cards",
        "lesson": "A celebration can change its tune without losing its joy.",
    },
]

OPENINGS = [
    "Morning sun shone on {place}, where {sailor} the sailor polished a brass compass before the parade.",
    "At {place}, bunting danced above the road as {sailor} the sailor helped prepare the town parade.",
    "The parade morning began with bells, bright shoes, and {sailor} the sailor checking every rope twice.",
    "Families gathered at {place}, while {sailor} the sailor watched the wind and smiled at the waiting marchers.",
]

DIALOGUES = [
    "\"The parade must go on,\" said {sailor}. \"Not by rushing,\" replied {leader}. \"By helping one another.\"",
    "\"Can you fix it?\" asked {child}. \"I can try,\" said {sailor}. \"And we can hold everything steady,\" promised {leader}.",
    "\"The crowd is waiting,\" whispered {child}. \"Then let us give them care, not panic,\" said {sailor}.",
    "\"I thought soldiers only marched,\" said {child}. \"Today we protect a celebration,\" answered {leader}.",
]

TWISTS = [
    "Then came the twist: the grand parade surprise was not a new float at all, but the repaired object, carried proudly by the people who had saved it.",
    "Then came the twist: the sailor had expected to lead the parade, but the infantry invited the smallest helper to walk at the front.",
    "Then came the twist: the crowd's loudest cheer was saved for the helpers who had worked quietly behind the scenes.",
    "Then came the twist: the broken part became a keepsake, sewn into a banner so everyone would remember how the parade was rescued.",
]

ENDINGS = [
    "When evening arrived, the repaired colors glowed above the square, and everyone walked home feeling included.",
    "The last drumbeat faded over the water, but the kindness of the day stayed bright in every smiling face.",
    "Children waved from the curb as the sailor and infantry marched together beneath the shining flags.",
    "At sunset, the town placed the rescued treasure in the parade hall, where its little repair became a beloved story.",
]


ASP_RULES = r"""
#show parade_ready/1.
#show helped/2.
parade_ready(O) :- repaired(O), protected(O).
helped(A, B) :- cooperated(A, B).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("repaired", "parade_sail"),
            asp.fact("protected", "parade_sail"),
            asp.fact("cooperated", "sailor", "infantry"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Heartwarming parade storyworld.")
    parser.add_argument("--sailor", choices=SAILORS)
    parser.add_argument("--infantry-leader", choices=INFANTRY)
    parser.add_argument("--child", choices=CHILDREN)
    parser.add_argument("--parade-place", choices=PLACES)
    parser.add_argument("--event", type=int, choices=range(len(EVENTS)))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        sailor=args.sailor or rng.choice(SAILORS),
        infantry_leader=args.infantry_leader or rng.choice(INFANTRY),
        child=args.child or rng.choice(CHILDREN),
        parade_place=args.parade_place or rng.choice(PLACES),
        event=args.event if args.event is not None else rng.randrange(len(EVENTS)),
        opening=rng.randrange(len(OPENINGS)),
        dialogue=rng.randrange(len(DIALOGUES)),
        twist=rng.randrange(len(TWISTS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    if params.sailor == params.infantry_leader:
        raise StoryError("The sailor and infantry leader must have different names.")
    if params.sailor == params.child or params.infantry_leader == params.child:
        raise StoryError("The sailor, infantry leader, and child must have different names.")

    event = EVENTS[params.event % len(EVENTS)]
    world = World()

    sailor = world.add(Entity(params.sailor, "sailor", params.sailor))
    leader = world.add(Entity(params.infantry_leader, "infantry", params.infantry_leader))
    child = world.add(Entity(params.child, "child", params.child))
    parade = world.add(Entity("parade", "event", "town parade"))
    object_entity = world.add(Entity("parade_object", "object", event["object"]))

    sailor.meters.update(balance=0.8, reach=0.7)
    sailor.memes.update(courage=1.0, kindness=1.0)
    leader.meters.update(strength=0.9, steadiness=1.0)
    leader.memes.update(duty=1.0, warmth=0.8)
    child.memes.update(hope=1.0, belonging=0.5)
    parade.memes["joy"] = 0.8

    values = {
        "place": params.parade_place,
        "sailor": params.sailor,
        "leader": params.infantry_leader,
        "child": params.child,
    }

    world.say(OPENINGS[params.opening % len(OPENINGS)].format(**values))
    world.say("The sailor stood beside the infantry, ready to help the town make a joyful memory.")
    world.say(event["problem"])
    world.say(DIALOGUES[params.dialogue % len(DIALOGUES)].format(**values))
    world.say(event["clue"])
    world.say(event["action"])
    world.say(event["result"])

    object_entity.memes["repaired"] = 1.0
    object_entity.memes["shared"] = 1.0
    sailor.memes["confidence"] = 1.0
    leader.memes["pride"] = 0.5
    child.memes["belonging"] = 1.0
    world.facts.update(
        sailor=sailor,
        infantry=leader,
        child=child,
        parade=parade,
        object=object_entity,
        event=event,
        place=params.parade_place,
        repaired=True,
        cooperation=True,
    )

    world.say(TWISTS[params.twist % len(TWISTS)])
    world.say(f"{params.child} clapped and said, \"This is the best part of the parade!\"")
    world.say(f"{params.sailor} smiled. \"The best part is that we made it together.\"")
    world.say(f"Everyone learned that {event['lesson'].lower()}")
    world.say(ENDINGS[params.ending % len(ENDINGS)])

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    event = world.facts["event"]
    sailor = world.facts["sailor"]
    return [
        f"Write a heartwarming parade story about {sailor.label}, a sailor who helps repair {event['object']}.",
        "Tell a child-friendly story where a sailor and infantry work together before a parade.",
        f"Create a story with a gentle twist involving {event['object']} and a final image of shared joy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    event = world.facts["event"]
    sailor = world.facts["sailor"]
    infantry = world.facts["infantry"]
    child = world.facts["child"]
    return [
        QAItem(
            question=f"What problem did {sailor.label} face before the parade?",
            answer=event["problem"],
        ),
        QAItem(
            question=f"How did {sailor.label} and the infantry led by {infantry.label} help?",
            answer=event["action"],
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=TWISTS[world.params.twist % len(TWISTS)] if hasattr(world, "params") else "The helpers became the heart of the parade surprise.",
        ),
        QAItem(
            question=f"How did {child.label} feel at the end?",
            answer=f"{child.label} felt included and joyful because the parade was saved through kindness and teamwork.",
        ),
        QAItem(
            question="What lesson did the characters learn?",
            answer=f"They learned that {event['lesson'].lower()}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized procession in which people, vehicles, music, or flags move together for others to watch and enjoy.",
        ),
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works on or around a boat or ship and learns skills such as handling ropes, reading weather, and staying steady near water.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers trained to travel and work on foot. In this story, the infantry use their strength to protect and support the parade.",
        ),
        QAItem(
            question="Why can a twist make a story heartwarming?",
            answer="A heartwarming twist can reveal an unexpected kindness or show that people who seemed to need help also helped one another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label:16} ({entity.type:9}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show parade_ready/1.\n#show helped/2."))
    ready = set(asp.atoms(model, "parade_ready"))
    helped = set(asp.atoms(model, "helped"))
    if ready == {("parade_sail",)} and helped == {("sailor", "infantry")}:
        print("OK: ASP parity matches the Python story gate.")
        return 0
    print("MISMATCH between ASP and Python story gate.")
    print("  parade_ready:", sorted(ready))
    print("  helped:", sorted(helped))
    return 1


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show parade_ready/1."))
    return sorted(asp.atoms(model, "parade_ready"))


CURATED = [
    StoryParams(sailor="Mara", infantry_leader="Jon", child="Lina", parade_place="harbor square", event=0),
    StoryParams(sailor="Nell", infantry_leader="Ada", child="Pip", parade_place="the sunny quay", event=1, opening=2, dialogue=1, twist=1, ending=2),
    StoryParams(sailor="Ivo", infantry_leader="Cora", child="Noah", parade_place="the town green", event=2, opening=3, dialogue=3, twist=3, ending=1),
]


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
        print(asp_program("#show parade_ready/1.\n#show helped/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        facts = asp_valid()
        print(f"{len(facts)} ASP-approved parade state(s)")
        for fact in facts:
            print(fact)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 30):
            params = resolve_params(args, random.Random(base_seed + index))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.sailor}: parade by {sample.params.parade_place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
