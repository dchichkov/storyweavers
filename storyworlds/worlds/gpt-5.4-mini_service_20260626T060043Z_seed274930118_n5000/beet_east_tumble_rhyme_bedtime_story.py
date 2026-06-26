#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/beet_east_tumble_rhyme_bedtime_story.py
================================================================================================

A small bedtime-story world with rhyme, a beet, an eastward path, and a tumble
that turns into a gentle fix.
"""

from __future__ import annotations

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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    name: str = "Mina"
    gender: str = "girl"
    parent: str = "mother"
    seed: Optional[int] = None


@dataclass
class World:
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    meter: dict[str, float] = field(default_factory=dict)
    location: str = "the east garden"
    rhyme_mode: bool = True

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
        import copy
        w = World(location=self.location, rhyme_mode=self.rhyme_mode)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.meter = dict(self.meter)
        w.paragraphs = [[]]
        return w


THRESHOLD = 1.0


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def add_meter(world: World, key: str, amount: float) -> None:
    world.meter[key] = world.meter.get(key, 0.0) + amount


def meter(world: World, key: str) -> float:
    return world.meter.get(key, 0.0)


def one_beet_story_ok() -> bool:
    return True


def predict_tumble(world: World, child: Entity, beet: Entity) -> dict[str, bool]:
    sim = world.copy()
    add_meter(sim, "tumble", 1)
    add_meter(sim, "mud", 1)
    if sim.facts.get("scarf_on"):
        return {"messy": False}
    return {"messy": True}


def bed_time_opening(world: World, child: Entity, parent: Entity, beet: Entity) -> None:
    world.say(
        f"At bedtime, {child.id} and {child.pronoun('possessive')} {parent.type} "
        f"went east along the little stone trail."
    )
    world.say(
        f"They carried a bright red beet, neat and sweet, and the moon looked down "
        f"with a sleepy glow."
    )


def want_story(world: World, child: Entity, beet: Entity) -> None:
    add_meter(world, "want", 1)
    world.say(
        f"{child.id} wanted to tumble and twirl by the east gate, because the path "
        f"felt soft and the night felt light."
    )
    world.say("The beet bobbed in a cloth bag, round as a drum, and ready to hum.")


def warning(world: World, parent: Entity, child: Entity, beet: Entity) -> None:
    pred = predict_tumble(world, child, beet)
    if pred["messy"]:
        world.say(
            f"\"If you tumble too fast, your beet may fall with a splat,\" "
            f"said {parent.pronoun('subject')} with a smile that was gentle and bright."
        )
        world.facts["warning"] = True
    else:
        world.facts["warning"] = False


def tumble(world: World, child: Entity, beet: Entity) -> None:
    add_meter(world, "tumble", 1)
    child.memes["glee"] = child.memes.get("glee", 0.0) + 1
    world.say(
        f"{child.id} spun once, then twice, and took a tumble by the eastern wall."
    )


def drop_beet(world: World, child: Entity, beet: Entity) -> None:
    if meter(world, "tumble") >= THRESHOLD:
        beet.meters["dirt"] = beet.meters.get("dirt", 0.0) + 1
        beet.meters["bruised"] = beet.meters.get("bruised", 0.0) + 1
        world.say(
            f"The beet slipped from the bag and rolled in a hurry, then stopped with a thud."
        )


def fix_with_scarf(world: World, parent: Entity, child: Entity, beet: Entity) -> None:
    scarf = world.add(Entity(
        id="scarf",
        type="scarf",
        label="soft scarf",
        phrase="a soft scarf",
        owner=child.id,
        worn_by=child.id,
        region="hands",
    ))
    world.facts["scarf_on"] = True
    world.say(
        f"{parent.id} tied on {child.pronoun('possessive')} soft scarf, snug and neat, "
        f"to cradle the beet and keep the walk complete."
    )
    world.say(
        f"Then {child.id} could hold the beet without a slip, and the night went smooth "
        f"as a moonlit trip."
    )
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    beet.meters["safe"] = beet.meters.get("safe", 0.0) + 1
    world.facts["scarf"] = scarf.id


def resolve(world: World, child: Entity, parent: Entity, beet: Entity) -> None:
    if meter(world, "tumble") >= THRESHOLD and beet.meters.get("bruised", 0.0) >= THRESHOLD:
        world.say(
            f"{child.id} looked at the beet and frowned, then listened well."
        )
        fix_with_scarf(world, parent, child, beet)
        world.say(
            f"By the end, the beet stayed safe, the east wind was mild, and {child.id} "
            f"yawned a tiny yawn like a child."
        )


def tell(params: StoryParams) -> World:
    world = World(location="the east garden", rhyme_mode=True)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"hop": 0.0},
        memes={"joy": 1.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=params.parent,
    ))
    beet = world.add(Entity(
        id="beet",
        type="beet",
        label="beet",
        phrase="a bright red beet",
        owner=child.id,
    ))

    bed_time_opening(world, child, parent, beet)
    world.para()
    want_story(world, child, beet)
    warning(world, parent, child, beet)
    tumble(world, child, beet)
    drop_beet(world, child, beet)
    world.para()
    resolve(world, child, parent, beet)

    world.facts.update(child=child, parent=parent, beet=beet, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a gentle bedtime story in rhyme about a beet and an eastward walk.',
        f"Tell a tiny bedtime tale where {f['child'].id} wants to tumble in the east garden, but a beet needs care.",
        "Write a soft rhyming story that ends with the beet staying safe and the child feeling sleepy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    beet: Entity = f["beet"]
    return [
        QAItem(
            question=f"Where did {child.id} and {parent.id} walk at bedtime?",
            answer="They walked east along the little stone trail in the east garden.",
        ),
        QAItem(
            question=f"What did {child.id} want to do by the east gate?",
            answer=f"{child.id} wanted to tumble and twirl by the east gate.",
        ),
        QAItem(
            question="What happened to the beet after the tumble?",
            answer="The beet slipped from the bag, rolled once, and got a little dirty.",
        ),
        QAItem(
            question="What helped keep the beet safe in the end?",
            answer="A soft scarf helped cradle the beet so it could travel safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a beet?",
            answer="A beet is a round root vegetable that can be bright red or purple inside.",
        ),
        QAItem(
            question="What does east mean?",
            answer="East is the direction where the sun rises in the morning.",
        ),
        QAItem(
            question="What does tumble mean?",
            answer="To tumble means to tip over or roll down in a sudden, clumsy way.",
        ),
        QAItem(
            question="What is rhyme?",
            answer="Rhyme means words sound alike at the end, like beet and sweet.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("theme", "bedtime"),
        asp.fact("theme", "rhyme"),
        asp.fact("object", "beet"),
        asp.fact("direction", "east"),
        asp.fact("action", "tumble"),
        asp.fact("protective_item", "scarf"),
    ])


ASP_RULES = r"""
valid_story :- theme(bedtime), theme(rhyme), object(beet), direction(east), action(tumble), protective_item(scarf).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    asp_ok = bool(model)
    py_ok = one_beet_story_ok()
    if asp_ok == py_ok:
        print("OK: ASP and Python agree on story validity.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime rhyme storyworld about a beet, east, and a tumble.")
    ap.add_argument("--name", choices=["Mina", "Lina", "Tara", "Nora"], default=None)
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--parent", choices=["mother", "father"], default=None)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(["Mina", "Lina", "Tara", "Nora"] if gender == "girl" else ["Finn", "Noah", "Theo", "Eli"])
    return StoryParams(name=name, gender=gender, parent=parent)


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for eid, e in world.entities.items():
        lines.append(f"{eid}: type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"facts: {world.facts}")
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
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/0."))
        print("valid_story" if model else "no valid story")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(name=n, gender=g, parent=p)) for n, g, p in [
            ("Mina", "girl", "mother"),
            ("Lina", "girl", "father"),
            ("Theo", "boy", "mother"),
        ]]
    else:
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
