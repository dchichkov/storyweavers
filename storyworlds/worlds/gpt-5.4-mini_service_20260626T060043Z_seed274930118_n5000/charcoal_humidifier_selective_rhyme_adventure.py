#!/usr/bin/env python3
"""
A small adventure world about charcoal, a humidifier, and a selective misting
device that can help one thirsty thing without soaking everything else.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    selective: bool = False
    target: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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


def rhyming_line(topic: str) -> str:
    return {
        "charcoal": "With charcoal in hand, she drew a bold band.",
        "humidifier": "The humidifier hummed, but the room stayed glummed.",
        "selective": "The selective mist was neat: one plant got a treat.",
    }.get(topic, "The day felt bright, and the path felt right.")


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    parent_type: str
    seed: Optional[int] = None


PLACES = {
    "attic": {
        "place": "the attic room",
        "needs": "dry",
        "risk": "dusty",
        "adventure": "search for a hidden map",
    },
    "greenhouse": {
        "place": "the little greenhouse",
        "needs": "humid",
        "risk": "dry",
        "adventure": "find a rare fern",
    },
    "workshop": {
        "place": "the old workshop",
        "needs": "steady",
        "risk": "dry",
        "adventure": "trace a secret door",
    },
}

HEROES = [
    ("Mila", "girl"),
    ("Owen", "boy"),
    ("Lina", "girl"),
    ("Theo", "boy"),
]

PARENTS = ["mother", "father"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world: charcoal, humidifier, selective mist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    lines.append(asp.fact("topic", "charcoal"))
    lines.append(asp.fact("topic", "humidifier"))
    lines.append(asp.fact("topic", "selective"))
    for pid, cfg in PLACES.items():
        lines.append(asp.fact("has_need", pid, cfg["needs"]))
    lines.append(asp.fact("device", "humidifier"))
    lines.append(asp.fact("device", "selective_mister"))
    lines.append(asp.fact("device_feature", "selective_mister", "selective"))
    lines.append(asp.fact("device_feature", "humidifier", "humid"))
    return "\n".join(lines)


ASP_RULES = r"""
needs_device(P, humidifier) :- has_need(P, humid).
needs_device(P, selective_mister) :- has_need(P, dry).
compatible(P, D) :- needs_device(P, D), device(D).
valid(P) :- compatible(P, _).
#show valid/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(pid,) for pid in PLACES}
    cl = set(asp_valid_places())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} places).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    name, gender = rng.choice(HEROES)
    if args.gender:
        candidates = [n for n in HEROES if n[1] == args.gender]
        if not candidates:
            raise StoryError("No hero matches that gender.")
        name, gender = rng.choice(candidates)
    if args.name:
        name = args.name
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(place=place, hero_name=name, hero_type=gender, parent_type=parent)


def generate(params: StoryParams) -> StorySample:
    cfg = PLACES[params.place]
    world = World(place=cfg["place"])

    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_type))
    charcoal = world.add(Entity(
        id="charcoal",
        label="charcoal sticks",
        phrase="a small pouch of charcoal sticks",
        owner=hero.id,
        caretaker=parent.id,
        meters={"dust": 1.0},
    ))
    humidifier = world.add(Entity(
        id="humidifier",
        label="humidifier",
        phrase="a tiny humming humidifier",
        protective=True,
        meters={"mist": 0.0},
    ))
    selective = world.add(Entity(
        id="selective",
        label="selective mist wand",
        phrase="a selective mist wand with a careful nozzle",
        protective=True,
        selective=True,
        target="plant",
        meters={"mist": 0.0},
    ))
    plant = world.add(Entity(
        id="plant",
        label="fern",
        phrase="a thirsty fern in a clay pot",
        caretaker=parent.id,
        meters={"dry": 1.0},
        memes={"thirst": 1.0},
    ))
    map_piece = world.add(Entity(
        id="map",
        label="map page",
        phrase="a folded map page",
        caretaker=parent.id,
        meters={"dry": 1.0},
    ))

    world.facts.update(place=params.place, cfg=cfg, hero=hero, parent=parent,
                       charcoal=charcoal, humidifier=humidifier, selective=selective,
                       plant=plant, map_piece=map_piece)

    world.say(f"{params.hero_name} was a little {params.hero_type} who loved adventure.")
    world.say(f"{rhyming_line('charcoal')} {params.hero_name} used charcoal to mark a path on {map_piece.label}.")
    world.say(f"In {cfg['place']}, {params.hero_name} wanted to {cfg['adventure']}.")

    world.para()
    world.say(f"The air there felt {cfg['risk']}, so {parent.pronoun('possessive')} {parent.type} brought a humidifier.")
    world.say(f"{rhyming_line('humidifier')} That worried {params.hero_name}, because the map page and charcoal could smear.")
    world.say(f"{params.hero_name} still wanted the fern to look lively, not shriveled and sad.")

    world.para()
    world.say(f"Then {parent.pronoun().capitalize()} lifted the selective mist wand and smiled.")
    world.say(f"{rhyming_line('selective')} It could water the fern without soaking the map.")
    plant.meters["dry"] = 0.0
    plant.memes["thirst"] = 0.0
    charcoal.meters["dust"] = 1.0
    map_piece.meters["dry"] = 1.0
    world.say(f"So the fern stood fresh, the charcoal stayed sharp, and {params.hero_name} followed the map into adventure.")
    world.say(f"At the end, the room had the right kind of air, and the little trail on the page still pointed forward.")

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
        f'Write a short adventure story for a young child that includes "{f["hero"].label if False else "charcoal"}", "{ "humidifier" }", and "{ "selective" }".',
        f"Tell a child-friendly adventure where a {f['hero'].type} uses charcoal to make a map, worries about a humidifier, and finds a selective fix.",
        "Write a small story with a rhyme or two, a careful mist, and a brave next step.",
    ]


def storyqa_lines(hero: Entity, parent: Entity, place: str, cfg: dict) -> list[QAItem]:
    return [
        QAItem(
            question=f"What did the child use to make marks on the map?",
            answer="The child used charcoal sticks to draw dark marks on the map page.",
        ),
        QAItem(
            question=f"Why did the humidifier worry the child?",
            answer=f"It worried the child because too much humid air could make the charcoal smudge and spoil the map.",
        ),
        QAItem(
            question=f"What did the selective mist wand do?",
            answer="It watered only the fern, so the map and charcoal stayed dry and useful.",
        ),
        QAItem(
            question=f"What kind of ending did the story have?",
            answer="It ended with the fern fresh, the map still clear, and the child ready to follow the path into adventure.",
        ),
    ]


def story_qa(world: World) -> list[QAItem]:
    return storyqa_lines(world.facts["hero"], world.facts["parent"], world.place, PLACES[next(k for k, v in PLACES.items() if v["place"] == world.place)])


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is charcoal used for?",
            answer="Charcoal can make dark marks and drawings, like sketching a map or outlining shapes.",
        ),
        QAItem(
            question="What does a humidifier do?",
            answer="A humidifier adds moisture to the air to make a room less dry.",
        ),
        QAItem(
            question="What does selective mean here?",
            answer="Selective means it chooses one target carefully, so only the plant gets the mist.",
        ),
        QAItem(
            question="Why is careful misting helpful in this world?",
            answer="It helps a thirsty plant without making the map wet or ruining the charcoal lines.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.selective:
            bits.append("selective=True")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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


CURATED = [
    StoryParams(place="attic", hero_name="Mila", hero_type="girl", parent_type="mother"),
    StoryParams(place="greenhouse", hero_name="Owen", hero_type="boy", parent_type="father"),
    StoryParams(place="workshop", hero_name="Lina", hero_type="girl", parent_type="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for item in asp_valid_places():
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
