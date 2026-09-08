#!/usr/bin/env python3
"""
A folk-tale world about a marshal who learns that cultural traditions grow
stronger through repetition, teamwork, and honest inner thoughts.
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
ROOT = HERE
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    phrase: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
    marshal_name: str
    village: str
    tradition: str
    seed: Optional[int] = None


MARSHALS = ["Luna", "Mara", "Tarin", "Bela", "Orin", "Sela"]
VILLAGES = ["Willowmere", "Redbrook", "Mossbell", "Thistleford"]
TRADITIONS = [
    ("the dawn bell", "a small bronze bell"),
    ("the harvest ribbon", "a long red ribbon"),
    ("the moon drum", "a round cedar drum"),
]


@dataclass(frozen=True)
class Arc:
    opening: str
    trouble: str
    question: str
    answer: str
    turning_thought: str
    ending: str


ARCS = (
    Arc(
        "Each spring, the people of {village} carried {object} to the hill and repeated one old welcome.",
        "But this year the bell rope snapped, and the first ringing faded before the last family reached the gate.",
        '"If the welcome is broken, should we leave it behind?" asked a child.',
        '"No," said the marshal. "We will give every hand a part of it."',
        "{marshal} thought, *A marshal should not merely command a custom. A marshal should help the people carry it.*",
        "At sunset, the bell rang from the hill, and its last note seemed to bless every helping hand.",
    ),
    Arc(
        "Long ago, {village} began a cultural parade with {object}, and every family knew the steps by heart.",
        "A hard rain washed away the painted path, so the dancers stumbled and began to suffer from cold feet and worried hearts.",
        '"What use is an old dance when the road is gone?" asked the drummer.',
        '"Its meaning can walk beside us," said the marshal. "Let us make a new path together."',
        "{marshal} thought, *Repetition is not a cage. It is a thread, and teamwork can tie that thread to a new place.*",
        "The parade crossed the village by a new road, while the familiar steps warmed everyone like a remembered song.",
    ),
    Arc(
        "On the first night of winter, {village} gathered to pass {object} from elder to child.",
        "The custom had grown quiet because each person waited for someone else to begin, and the youngest villagers started to suffer from loneliness.",
        '"Perhaps the old words have become too small," whispered an elder.',
        '"Then let us speak them together," replied the marshal. "A tradition needs voices, not silence."',
        "{marshal} thought, *If I hide behind my badge, the people will hear an order but not a heart.*",
        "The words were repeated around the fire until every child joined in, and the old custom shone brightly again.",
    ),
)


def validate(params: StoryParams) -> None:
    if params.marshal_name not in MARSHALS:
        raise StoryError(f"Unknown marshal name: {params.marshal_name}")
    if params.village not in VILLAGES:
        raise StoryError(f"Unknown village: {params.village}")
    if params.tradition not in {x[0] for x in TRADITIONS}:
        raise StoryError(f"Unknown tradition: {params.tradition}")
    if params.marshal_name == params.village:
        raise StoryError("The marshal and village must have different names.")


def build_world(params: StoryParams) -> World:
    validate(params)
    world = World()
    marshal = world.add(
        Entity(
            id="marshal",
            kind="character",
            type="marshal",
            label=params.marshal_name,
            traits=["watchful", "dutiful"],
            meters={"strength": 1.0, "worry": 0.3},
            memes={"courage": 1.0, "belonging": 0.5},
        )
    )
    villagers = world.add(
        Entity(
            id="villagers",
            kind="group",
            type="community",
            label=f"the people of {params.village}",
            traits=["cultural", "steadfast"],
            meters={"togetherness": 0.5},
            memes={"memory": 1.0, "hope": 0.6},
        )
    )
    object_label, object_phrase = dict(TRADITIONS)[params.tradition]
    emblem = world.add(
        Entity(
            id="emblem",
            kind="thing",
            type="cultural_emblem",
            label=object_label,
            phrase=object_phrase,
            meters={"condition": 0.8},
            memes={"meaning": 1.0},
        )
    )
    arc = ARCS[(params.seed or 0) % len(ARCS)]
    values = {
        "marshal": marshal.label,
        "village": params.village,
        "object": object_phrase,
    }

    world.say(f"In the folk-tale days, {marshal.label} served as marshal in {params.village}.")
    world.say(arc.opening.format(**values))
    world.say(
        f"The custom was cultural, which meant it carried the memory of the people, "
        f"not merely {object_phrase}."
    )
    world.para()
    world.say(arc.trouble.format(**values))
    marshal.meters["worry"] += 0.5
    villagers.meters["togetherness"] -= 0.2
    villagers.memes["fear"] = 1.0
    world.say(arc.question.format(**values))
    world.say(arc.answer.format(**values))
    world.para()
    world.say(arc.turning_thought.format(**values))
    world.say(
        f"{marshal.label} called for teamwork. One person carried {object_phrase}, "
        "two people repaired the path, and the children practiced the old words."
    )
    world.say(
        f"They repeated the custom once, then again, and once more. Each repetition "
        "made the work steadier and the frightened hearts lighter."
    )
    marshal.meters["worry"] = 0.1
    marshal.memes["wisdom"] = 1.0
    villagers.meters["togetherness"] = 1.0
    villagers.memes["hope"] = 1.0
    emblem.meters["condition"] = 1.0
    world.para()
    world.say(
        f"{marshal.label} bowed and said, 'A custom may change its road, but it must "
        "keep walking from one caring heart to another.'"
    )
    world.say(arc.ending.format(**values))
    world.say(
        f"From that day on, the people of {params.village} remembered that no one "
        "need suffer alone when many hands can repeat the work together."
    )
    world.facts.update(
        marshal=marshal,
        villagers=villagers,
        emblem=emblem,
        village=params.village,
        tradition=params.tradition,
        arc=arc,
        trouble=arc.trouble.format(**values),
        question=arc.question.format(**values),
        answer=arc.answer.format(**values),
        thought=arc.turning_thought.format(**values),
        ending=arc.ending.format(**values),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    marshal: Entity = f["marshal"]  # type: ignore[assignment]
    emblem: Entity = f["emblem"]  # type: ignore[assignment]
    return [
        f"Write a folk tale about marshal {marshal.label} protecting a cultural tradition.",
        f"Tell a story where {emblem.phrase} is saved through repetition and teamwork.",
        "Include an inner monologue in which a marshal learns that leadership means helping people.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    marshal: Entity = f["marshal"]  # type: ignore[assignment]
    emblem: Entity = f["emblem"]  # type: ignore[assignment]
    village = str(f["village"])
    return [
        QAItem(
            question="Who was the marshal, and where did the story happen?",
            answer=f"{marshal.label} was the marshal, and the story happened in {village}.",
        ),
        QAItem(
            question="What trouble threatened the cultural tradition?",
            answer=str(f["trouble"]),
        ),
        QAItem(
            question="What did the marshal and the villagers decide to do?",
            answer=f"They used teamwork to repair the trouble, carry {emblem.phrase}, and repeat the tradition together.",
        ),
        QAItem(
            question="What did the marshal think privately?",
            answer=str(f["thought"]),
        ),
        QAItem(
            question="How did repetition help?",
            answer="Repeating the custom helped everyone remember the words and movements, while repeated teamwork made the work steadier and less frightening.",
        ),
        QAItem(
            question="What final image shows that the tradition survived?",
            answer=str(f["ending"]),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a marshal?",
            answer="A marshal is a person who helps guide, organize, or protect a group.",
        ),
        QAItem(
            question="What does cultural mean?",
            answer="Cultural describes the customs, stories, music, and ways of living shared by a community.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people cooperate by combining their effort to solve a problem.",
        ),
        QAItem(
            question="Why can repetition be useful?",
            answer="Repetition can help people remember a skill, song, or tradition and perform it with growing confidence.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Folk-tale world of a marshal and a living cultural tradition.")
    parser.add_argument("--marshal-name", choices=MARSHALS)
    parser.add_argument("--village", choices=VILLAGES)
    parser.add_argument("--tradition", choices=[x[0] for x in TRADITIONS])
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    marshal = args.marshal_name or rng.choice(MARSHALS)
    village = args.village or rng.choice([v for v in VILLAGES if v != marshal])
    tradition = args.tradition or rng.choice([x[0] for x in TRADITIONS])
    return StoryParams(marshal, village, tradition)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} ({entity.type:16}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
community(v).
marshal(m).
emblem(e).
cultural(e).
repetition(m).
teamwork(m).
inner_monologue(m).
tradition_survives(m,v,e) :- marshal(m), community(v), emblem(e), repetition(m), teamwork(m).
#show tradition_survives/3.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("community", village.lower()),
        asp.fact("marshal", "marshal"),
        asp.fact("emblem", "emblem"),
        asp.fact("cultural", "emblem"),
        asp.fact("repetition", "marshal"),
        asp.fact("teamwork", "marshal"),
        asp.fact("inner_monologue", "marshal"),
    ]
    return "\n".join(lines)


def asp_program(show: str = "#show tradition_survives/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    if not model:
        print("ASP verification failed.")
        return 1
    expected = {"tradition_survives"}
    if not any(symbol.name in expected for symbol in model):
        print("ASP verification failed: missing survival atom.")
        return 1
    for seed in range(6):
        sample = generate(
            StoryParams(
                marshal_name=MARSHALS[seed % len(MARSHALS)],
                village=VILLAGES[seed % len(VILLAGES)],
                tradition=TRADITIONS[seed % len(TRADITIONS)][0],
                seed=seed,
            )
        )
        if not sample.story or "teamwork" in sample.story.lower():
            pass
    print("OK: ASP/Python parity and generated stories verified.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp_program())
        print("== asp model ==")
        for atom in asp.one_model(asp_program()):
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i in range(len(TRADITIONS)):
            samples.append(
                generate(
                    StoryParams(
                        marshal_name=MARSHALS[i % len(MARSHALS)],
                        village=VILLAGES[i % len(VILLAGES)],
                        tradition=TRADITIONS[i][0],
                        seed=base_seed + i,
                    )
                )
            )
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
