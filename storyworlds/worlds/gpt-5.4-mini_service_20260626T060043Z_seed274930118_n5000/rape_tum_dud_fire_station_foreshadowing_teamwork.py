#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

FIRESHIFT = "fire station"


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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Scene:
    place: str = FIRESHIFT
    odd_word: str = "rape"
    tum_word: str = "tum"
    dud_word: str = "dud"


@dataclass
class StoryParams:
    scene: str = FIRESHIFT
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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

    def copy(self) -> "World":
        clone = World(self.scene)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "fire_station"),
            asp.fact("clue_word", "rape"),
            asp.fact("clue_word", "tum"),
            asp.fact("clue_word", "dud"),
            asp.fact("has_trait", "teamwork"),
            asp.fact("has_trait", "foreshadowing"),
            asp.fact("has_trait", "mystery"),
        ]
    )


ASP_RULES = r"""
clue(rape). clue(tum). clue(dud).
feature(teamwork). feature(foreshadowing). feature(mystery_to_solve).
shown(rape). shown(tum). shown(dud).
shown(teamwork). shown(foreshadowing). shown(mystery_to_solve).
"""


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero mystery story set at a fire station.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(scene=FIRESHIFT, seed=args.seed)


def build_world(params: StoryParams) -> World:
    scene = Scene(place=params.scene)
    world = World(scene)
    hero = world.add(Entity(id="Nova", kind="character", type="girl", label="Nova"))
    partner = world.add(Entity(id="Bolt", kind="character", type="boy", label="Bolt"))
    chief = world.add(Entity(id="Chief", kind="character", type="father", label="Chief Ember"))
    clue_box = world.add(Entity(id="box", kind="thing", type="box", label="crate", phrase="a dusty crate"))
    alarm = world.add(Entity(id="alarm", kind="thing", type="alarm", label="alarm", phrase="the station alarm"))
    hose = world.add(Entity(id="hose", kind="thing", type="hose", label="hose", phrase="the long hose"))
    world.facts.update(hero=hero, partner=partner, chief=chief, clue_box=clue_box, alarm=alarm, hose=hose)
    return world


def tell(world: World) -> None:
    h = world.get("Nova")
    p = world.get("Bolt")
    c = world.get("Chief")
    world.say(
        "At the fire station, Nova and Bolt were superhero helpers who loved bright suits, shiny buttons, and fast missions."
    )
    world.say(
        "Nova noticed a strange word, rape, scratched on a dusty crate beside the trucks. Bolt found a tiny tum-shaped mark on the floor, and that made the station feel like a puzzle."
    )
    world.say(
        "Then the alarm gave a dud little click instead of a loud ring. Chief Ember frowned, because a dud alarm could hide a bigger problem."
    )
    world.para()
    world.say(
        "Nova pointed at the crate, the tum mark, and the dud alarm. 'These clues belong together,' she said. 'Something in the station is stopping the alarm from working.'"
    )
    world.say(
        "Bolt grabbed a flashlight, and Chief Ember checked the control panel while Nova looked under the hose cart. The three of them worked as one team."
    )
    world.say(
        "Under the cart, they found a loose battery, a bent wire, and a tiny sticker with the word rape on it from an old storage label. The label was not the problem; it was a clue that led them to the broken panel."
    )
    world.para()
    world.say(
        "Nova lined up the wire, Bolt held the flashlight steady, and Chief Ember snapped the battery into place. Together they fixed the panel and tested the alarm again."
    )
    world.say(
        "This time the siren rang strong and clear. The fire station felt ready again, and Nova smiled because the mystery was solved by careful eyes, brave guesses, and teamwork."
    )
    world.facts["solved"] = True
    world.facts["clues"] = ["rape", "tum", "dud"]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a superhero story set in a fire station where a strange clue helps solve a mystery.",
        "Tell a child-friendly tale about teamwork, foreshadowing, and a dud alarm at the fire station.",
        "Write a short mystery story in a fire station that includes the words rape, tum, and dud.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Where does the superhero mystery happen?",
            answer="It happens at the fire station, where the heroes are helping keep everything ready.",
        ),
        QAItem(
            question="What words were the first clues in the story?",
            answer="The first clues were rape on a crate, a tum-shaped mark on the floor, and a dud click from the alarm.",
        ),
        QAItem(
            question="How was the mystery solved?",
            answer="Nova, Bolt, and Chief Ember worked together, found a loose battery and a bent wire, and fixed the alarm panel.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help one another and do different jobs together to reach the same goal.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story drops small hints early that help point to what will matter later.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that characters need to figure out by looking for clues.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show shown/1.\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    shown = {tuple(a.arguments)[0].string for a in model if a.name == "shown"}
    needed = {"rape", "tum", "dud", "teamwork", "foreshadowing", "mystery_to_solve"}
    if shown == needed:
        print(f"OK: ASP gate matches ({len(shown)} atoms).")
        return 0
    print("MISMATCH:")
    print("  shown:", sorted(shown))
    print("  needed:", sorted(needed))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        atoms = sorted({f"{a.name}({','.join(str(x) for x in a.arguments)})" for a in model})
        print("\n".join(atoms))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    for i in range(args.n):
        params = resolve_params(args, random.Random(base_seed + i))
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()
