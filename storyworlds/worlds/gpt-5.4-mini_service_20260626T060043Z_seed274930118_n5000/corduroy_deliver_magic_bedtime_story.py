#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/corduroy_deliver_magic_bedtime_story.py
===============================================================================================================

A small bedtime-story world about a child, a missing cozy thing, and a magic
delivery that arrives just in time for sleep.

Premise:
- A sleepy child loves a corduroy bedtime item.
- The item is expected to be delivered before lights-out.
- Something delays the ordinary delivery.
- Magic helps the delivery arrive gently and safely.

World model:
- Physical meters track whether an object is present, hidden, ready, or tucked in.
- Emotional memes track worry, hope, relief, and sleepiness.
- The story is generated from state changes, not from a fixed paragraph with
  swapped names.

The tale style stays close to a bedtime story: calm, concrete, and reassuring.
"""

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


# ---------------------------------------------------------------------------
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"           # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Room:
    name: str = "the nursery"
    quiet: bool = True
    bedtime: bool = True
    magic: bool = True


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.room)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Story registries
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    name: str
    detail: str


@dataclass
class ItemSpec:
    label: str
    phrase: str
    type: str
    owner_type: str = "child"


@dataclass
class DeliveryMethod:
    id: str
    name: str
    magic: bool
    gentle: bool
    reason: str
    arrives_in: str


SETTINGS = {
    "nursery": Setting(name="the nursery", detail="A little lamp made the room look like honey."),
    "bedroom": Setting(name="the bedroom", detail="A soft moonbeam lay across the blanket."),
    "attic": Setting(name="the attic", detail="The old room was quiet and full of sleepy shadows."),
}

ITEMS = {
    "corduroy_bear": ItemSpec(
        label="corduroy bear",
        phrase="a soft corduroy bear with tiny stitched paws",
        type="bear",
    ),
    "corduroy_blanket": ItemSpec(
        label="corduroy blanket",
        phrase="a cozy corduroy blanket with striped ribs",
        type="blanket",
    ),
    "corduroy_pajamas": ItemSpec(
        label="corduroy pajamas",
        phrase="little corduroy pajamas with wooden buttons",
        type="pajamas",
    ),
}

DELIVERIES = {
    "doorstep": DeliveryMethod(
        id="doorstep",
        name="the doorstep",
        magic=False,
        gentle=True,
        reason="the ordinary delivery cart got stuck in the rain",
        arrives_in="at the door",
    ),
    "moonbeam": DeliveryMethod(
        id="moonbeam",
        name="a moonbeam",
        magic=True,
        gentle=True,
        reason="the moonbeam could slip through the dark and bring the package softly",
        arrives_in="on a moonbeam",
    ),
    "pillow_path": DeliveryMethod(
        id="pillow_path",
        name="a pillow path",
        magic=True,
        gentle=True,
        reason="the pillow path could carry the package right to the bed",
        arrives_in="along a pillow path",
    ),
    "star_mail": DeliveryMethod(
        id="star_mail",
        name="star mail",
        magic=True,
        gentle=True,
        reason="the stars could carry the parcel without waking anyone",
        arrives_in="by star mail",
    ),
}

NAMES = ["Maya", "Nora", "Leo", "Finn", "Luna", "Iris", "Eli", "Zoe"]
PARENT_NAMES = ["Mom", "Dad"]
TRAITS = ["sleepy", "gentle", "curious", "patient", "cozy", "brave"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    item: str
    delivery: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Simulation rules
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


def _narrate_item_arrival(world: World) -> None:
    child = world.get("child")
    item = world.get("gift")
    method = world.facts["delivery_spec"]
    if item.meters.get("delivered", 0) < THRESHOLD:
        return
    sig = ("arrived",)
    if sig in world.fired:
        return
    world.fired.add(sig)
    child.memes["hope"] = child.memes.get("hope", 0) + 1
    world.say(f"At last, the parcel came {method.arrives_in}, wrapped in silver paper.")
    world.say(f"Inside was {item.phrase}.")
    world.say(f"{child.id} held {item.it()} close and smiled at its cozy corduroy ribs.")


def _narrate_sleep(world: World) -> None:
    child = world.get("child")
    item = world.get("gift")
    sig = ("sleep",)
    if sig in world.fired:
        return
    if child.memes.get("relief", 0) < THRESHOLD:
        return
    world.fired.add(sig)
    child.memes["sleepy"] = child.memes.get("sleepy", 0) + 1
    world.say(f"Then {child.id} tucked {item.it()} in beside the pillow and grew very sleepy.")
    world.say(f"The little room was quiet, and bedtime felt safe again.")


def _apply_magic(world: World) -> None:
    child = world.get("child")
    item = world.get("gift")
    delivery = world.facts["delivery_spec"]
    if not delivery.magic:
        return
    sig = ("magic", delivery.id)
    if sig in world.fired:
        return
    if child.memes.get("worry", 0) < THRESHOLD:
        return
    world.fired.add(sig)
    child.memes["worry"] = max(0.0, child.memes.get("worry", 0) - 1)
    child.memes["relief"] = child.memes.get("relief", 0) + 1
    item.meters["delivered"] = 1
    item.meters["near_bed"] = 1
    world.say(f"Magic listened to the worry and answered with a soft bright hum.")
    world.say(f"It carried the parcel gently {delivery.arrives_in}, just as if the stars had mailed it themselves.")


def propagate(world: World) -> None:
    _apply_magic(world)
    _narrate_item_arrival(world)
    _narrate_sleep(world)


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def tell(setting: Setting, item_spec: ItemSpec, delivery: DeliveryMethod, name: str, parent: str, trait: str) -> World:
    world = World(Room(name=setting.name, quiet=True, bedtime=True, magic=delivery.magic))
    child = world.add(Entity(id="child", kind="character", type="girl" if name in {"Maya", "Nora", "Luna", "Iris", "Zoe"} else "boy"))
    child.label = name
    child.meters["awake"] = 1
    child.memes["worry"] = 1

    grownup = world.add(Entity(id="parent", kind="character", type="mother" if parent == "Mom" else "father"))
    grownup.label = parent

    item = world.add(Entity(id="gift", kind="thing", type=item_spec.type, label=item_spec.label, phrase=item_spec.phrase, owner="child"))
    item.meters["waiting"] = 1

    world.facts.update(
        setting=setting,
        item_spec=item_spec,
        delivery_spec=delivery,
        name=name,
        parent=parent,
        trait=trait,
        child=child,
        grownup=grownup,
        item=item,
    )

    world.say(f"{name} was a {trait} little child in {setting.name}.")
    world.say(setting.detail)
    world.say(f"Before bedtime, {name} waited for a {item_spec.label} to be delivered.")
    world.say(f"{name}'s {parent.lower()} promised it would come soon, but the ordinary delivery was late.")
    world.say(f"That made {name} feel a little worried, because bedtime was near and the room was getting dim.")

    world.para()
    if delivery.magic:
        world.say(f"Then {parent} whispered, 'I know a magic way to deliver it.'")
        world.say(f"The magic worked because {delivery.reason}.")
    else:
        world.say(f"Then {parent} looked outside and saw why the delivery was late: {delivery.reason}.")
        world.say("So they waited by the door together and listened for the wheels.")

    propagate(world)

    if item.meters.get("delivered", 0) >= THRESHOLD and child.memes.get("relief", 0) >= THRESHOLD:
        world.para()
        world.say(f"{name} cuddled the {item_spec.label} and lay back in bed.")
        world.say(f"{parent} turned down the lamp, and the nursery went soft and still.")
        world.say(f"With the corduroy treasure beside {name}, sleep came easily.")
    else:
        world.para()
        world.say(f"The package never arrived, and {name} kept waiting under the blanket.")
    return world


# ---------------------------------------------------------------------------
# Validity and ASP twin
# ---------------------------------------------------------------------------
def reasonable_pair(item_id: str, delivery_id: str) -> bool:
    item = ITEMS[item_id]
    delivery = DELIVERIES[delivery_id]
    return item.label.startswith("corduroy") and (delivery.magic or delivery.gentle)


ASP_RULES = r"""
#show valid/2.
item(corduroy_bear).
item(corduroy_blanket).
item(corduroy_pajamas).

delivery(doorstep).
delivery(moonbeam).
delivery(pillow_path).
delivery(star_mail).

magic_delivery(moonbeam).
magic_delivery(pillow_path).
magic_delivery(star_mail).

corduroy(Item) :- item(Item), corduroy_name(Item).
corduroy_name(corduroy_bear).
corduroy_name(corduroy_blanket).
corduroy_name(corduroy_pajamas).

reasonable(Item, Delivery) :- corduroy_name(Item), delivery(Delivery), magic_delivery(Delivery).
valid(Item, Delivery) :- reasonable(Item, Delivery).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("corduroy_name", item_id))
    for delivery_id, delivery in DELIVERIES.items():
        lines.append(asp.fact("delivery", delivery_id))
        if delivery.magic:
            lines.append(asp.fact("magic_delivery", delivery_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(item, delivery) for item in ITEMS for delivery in DELIVERIES if reasonable_pair(item, delivery)}
    ac = set(asp_valid_pairs())
    if py == ac:
        print(f"OK: clingo gate matches Python reasonableness ({len(py)} pairs).")
        return 0
    print("MISMATCH between Python and clingo:")
    if py - ac:
        print("  only in python:", sorted(py - ac))
    if ac - py:
        print("  only in clingo:", sorted(ac - py))
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle bedtime story about a child named {f["name"]} waiting for a corduroy {f["item_spec"].label}.',
        f"Tell a cozy story where magic helps deliver {f['item_spec'].phrase} before sleep.",
        f"Write a bedtime tale in which {f['name']} worries, then smiles when the parcel arrives softly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["grownup"]
    item_spec: ItemSpec = f["item_spec"]
    delivery: DeliveryMethod = f["delivery_spec"]

    return [
        QAItem(
            question=f"What was {child.label} waiting for at bedtime?",
            answer=f"{child.label} was waiting for {item_spec.phrase} to be delivered.",
        ),
        QAItem(
            question=f"Why did {child.label} feel worried before the package arrived?",
            answer=f"{child.label} felt worried because the delivery was late and bedtime was getting close.",
        ),
        QAItem(
            question=f"How did {parent.label} help?",
            answer=f"{parent.label} explained the delay and, when magic was available, used a magic way to deliver the parcel gently.",
        ),
        QAItem(
            question=f"What happened when the magic delivery worked?",
            answer=f"The parcel came softly {delivery.arrives_in}, and {child.label} held the corduroy item close and felt relieved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is corduroy?",
            answer="Corduroy is a fabric with raised ridges, so it often feels soft, warm, and a little bumpy to the touch.",
        ),
        QAItem(
            question="What does deliver mean?",
            answer="To deliver something means to bring it to the person or place it is meant for.",
        ),
        QAItem(
            question="What does magic do in a bedtime story?",
            answer="Magic can do surprising kind things, like moving a parcel gently or making a wish feel possible.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"{e.id}: {e.type} label={e.label!r} meters={meters} memes={memes}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    item: str
    delivery: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="nursery", item="corduroy_bear", delivery="moonbeam", name="Maya", parent="Mom", trait="sleepy"),
    StoryParams(setting="bedroom", item="corduroy_blanket", delivery="pillow_path", name="Leo", parent="Dad", trait="gentle"),
    StoryParams(setting="attic", item="corduroy_pajamas", delivery="star_mail", name="Luna", parent="Mom", trait="curious"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about a corduroy delivery and a little magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--delivery", choices=DELIVERIES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--parent", choices=PARENT_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    item = args.item or rng.choice(list(ITEMS))
    delivery = args.delivery or rng.choice(list(DELIVERIES))
    if args.item and args.delivery and not reasonable_pair(args.item, args.delivery):
        raise StoryError("That delivery is not a reasonable magic bedtime match for the corduroy item.")
    setting = args.setting or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, item=item, delivery=delivery, name=name, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        ITEMS[params.item],
        DELIVERIES[params.delivery],
        params.name,
        params.parent,
        params.trait,
    )
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


def asp_valid_pairs_text() -> None:
    pairs = asp_valid_pairs()
    for item, delivery in pairs:
        print(f"{item:18} {delivery}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp_valid_pairs_text()
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
