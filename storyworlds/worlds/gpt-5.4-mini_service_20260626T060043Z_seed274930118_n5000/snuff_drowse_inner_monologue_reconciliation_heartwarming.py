#!/usr/bin/env python3
"""
A standalone storyworld about a tired child, a tiny snuffing task, and a gentle
reconciliation after a small misunderstanding.

Seed tale imagined from the prompt:
- A child grows drowsy near bedtime.
- They want to snuff a candle or lantern to make the room cozy.
- A worried caregiver initially thinks they are causing trouble.
- The child quietly thinks to themself, explains their plan, and the two make up.
- The story ends with a warm, shared bedtime scene.
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

THRESHOLD = 1.0


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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    place: str = "the living room"
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    safe: bool = False


@dataclass
class StoryParams:
    place: str
    action: str
    item: str
    name: str
    child_type: str
    caregiver_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone = World(self.room)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


ACTIONS = {
    "snuff": {
        "verb": "snuff the candle",
        "gerund": "snuffing the candle",
        "prompt": "snuff",
        "risk": "go out",
        "effect": "dim and cozy",
    },
    "drowse": {
        "verb": "curl up and drowse",
        "gerund": "drowsing on the couch",
        "prompt": "drowse",
        "risk": "miss bedtime",
        "effect": "sleepy and soft",
    },
}

PLACES = {
    "living_room": Room(place="the living room", affords={"snuff", "drowse"}),
    "nursery": Room(place="the nursery", affords={"snuff", "drowse"}),
    "bedroom": Room(place="the bedroom", affords={"drowse"}),
}

ITEMS = {
    "candle": Item(id="candle", label="candle", phrase="a little beeswax candle", kind="light"),
    "nightlight": Item(id="nightlight", label="nightlight", phrase="a small nightlight", kind="light", safe=True),
    "blanket": Item(id="blanket", label="blanket", phrase="a soft blue blanket", kind="comfort"),
}

CHILD_NAMES = ["Mia", "Luna", "Noah", "Ivy", "Theo", "Mila", "Penny", "Eli"]
CAREGIVERS = ["mother", "father"]


def _do_action(world: World, child: Entity, action: str, item: Entity, narrate: bool = True) -> None:
    if action not in world.room.affords:
        raise StoryError(f"(No story: the {world.room.place} does not support {action}.)")
    if action == "snuff":
        child.meters["carefulness"] = child.meters.get("carefulness", 0.0) + 1.0
        item.meters["lit"] = max(0.0, item.meters.get("lit", 1.0) - 1.0)
        if narrate:
            world.say(f"{child.id} reached for the candle and gently snuffed it.")
    else:
        child.memes["sleepiness"] = child.memes.get("sleepiness", 0.0) + 1.0
        if narrate:
            world.say(f"{child.id} settled down and began to drowse.")


def predict(world: World, child: Entity, action: str, item: Entity) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(child.id), action, sim.get(item.id), narrate=False)
    return {
        "calm": sim.get(child.id).memes.get("calm", 0.0),
        "lit": sim.get(item.id).meters.get("lit", 0.0),
    }


def setup(world: World, child: Entity, caregiver: Entity, item: Entity, action: str) -> None:
    world.say(f"{child.id} was a little {child.type} who looked extra sleepy that evening.")
    if action == "snuff":
        world.say(f"{child.id} liked how the candle made {world.room.place} feel warm and kind.")
        world.say(f"{child.id} also knew that {item.label} was meant to be handled carefully.")
    else:
        world.say(f"{child.id} liked to drowse when the house was quiet and the lights were soft.")
    world.say(f"{caregiver.id} was nearby, folding blankets and watching over the room.")


def conflict(world: World, child: Entity, caregiver: Entity, item: Entity, action: str) -> None:
    pred = predict(world, child, action, item)
    if action == "snuff":
        world.say(
            f"{child.id} quietly thought, 'If I snuff the candle now, the room will feel sleepy and safe.'"
        )
        world.say(
            f"But when {child.id} reached out, {caregiver.id} worried it was too soon and said, "
            f'"Careful, {child.id}!"'
        )
        child.memes["startled"] = child.memes.get("startled", 0.0) + 1.0
        caregiver.memes["worry"] = caregiver.memes.get("worry", 0.0) + 1.0
    else:
        world.say(
            f"{child.id} thought, 'I am so drowsey I could fold into a pillow right here.'"
        )
        world.say(
            f"{caregiver.id} thought {child.id} might need help getting to bed and asked a gentle question."
        )
        child.memes["guarded"] = child.memes.get("guarded", 0.0) + 1.0
        caregiver.memes["worry"] = caregiver.memes.get("worry", 0.0) + 1.0
    world.facts["prediction"] = pred


def reconciliation(world: World, child: Entity, caregiver: Entity, item: Entity, action: str) -> None:
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1.0
    caregiver.memes["calm"] = caregiver.memes.get("calm", 0.0) + 1.0
    if action == "snuff":
        world.say(
            f"{child.id} took a slow breath and explained, 'I just wanted to snuff the candle so we could rest.'"
        )
        world.say(
            f"{caregiver.id} listened, then smiled with relief. 'Oh,' {caregiver.pronoun('subject')} said, "
            f"'you were being thoughtful.'"
        )
        world.say(
            f"Together they chose the safer nightlight, and the little flame was snuffed with care."
        )
        item.meters["lit"] = 0.0
    else:
        world.say(
            f"{child.id} whispered, 'I am not upset. I am only drowsy.'"
        )
        world.say(
            f"{caregiver.id} understood at once and tucked the blanket around {child.pronoun('object')}."
        )
        world.say(
            f"They sat together for a moment, both calm, until {child.id} grew warm and ready for sleep."
        )


def ending(world: World, child: Entity, caregiver: Entity, item: Entity, action: str) -> None:
    if action == "snuff":
        world.say(
            f"In the end, {world.room.place} glowed softly from the nightlight, and {child.id} rested beside "
            f"{caregiver.pronoun('object')} without any more worry."
        )
    else:
        world.say(
            f"In the end, {child.id} was drowsing under the blanket while {caregiver.id} sat nearby, smiling."
        )


def tell(room: Room, action: str, item_cfg: Item, name: str, child_type: str, caregiver_type: str) -> World:
    world = World(room)
    child = world.add(Entity(id=name, kind="character", type=child_type))
    caregiver = world.add(Entity(id="Caregiver", kind="character", type=caregiver_type))
    item = world.add(Entity(id=item_cfg.id, type=item_cfg.kind, label=item_cfg.label, phrase=item_cfg.phrase))

    setup(world, child, caregiver, item, action)
    world.para()
    conflict(world, child, caregiver, item, action)
    world.para()
    reconciliation(world, child, caregiver, item, action)
    ending(world, child, caregiver, item, action)

    world.facts.update(child=child, caregiver=caregiver, item=item, action=action, room=room)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, room in PLACES.items():
        for action in room.affords:
            for item_id, item in ITEMS.items():
                if action == "snuff" and item.safe:
                    continue
                combos.append((place, action, item_id))
    return combos


def explain_rejection(place: str, action: str, item: str) -> str:
    if action == "snuff" and ITEMS[item].safe:
        return "(No story: a nightlight is not the kind of light that needs to be snuffed.)"
    if action not in PLACES[place].affords:
        return f"(No story: the {PLACES[place].place} does not fit the action {action}.)"
    return "(No story: that combination is not reasonable.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story about a child who feels {f["action"]} and wants to {ACTIONS[f["action"]]["verb"]}.',
        f"Tell a gentle story where {f['child'].id} and a caregiver first misunderstand each other, then reconcile kindly.",
        f'Write a simple bedtime story that includes the words "snuff" and "drowse" and ends with a calm, cozy image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    item = f["item"]
    action = f["action"]
    room = f["room"]
    if action == "snuff":
        qs = [
            QAItem(
                question=f"What did {child.id} want to do with the {item.label} in {room.place}?",
                answer=f"{child.id} wanted to snuff the {item.label} so the room could feel soft and ready for sleep.",
            ),
            QAItem(
                question=f"Why did {caregiver.id} worry when {child.id} reached for the {item.label}?",
                answer=f"{caregiver.id} worried because the candle still had to be handled carefully, even though {child.id} meant well.",
            ),
            QAItem(
                question=f"What changed after {child.id} explained the plan?",
                answer=f"They chose the safer nightlight, made up with each other, and the room became calm and cozy.",
            ),
        ]
    else:
        qs = [
            QAItem(
                question=f"Why was {child.id} so quiet and sleepy in {room.place}?",
                answer=f"{child.id} was drowsing and ready for bed, so everything felt slow and gentle.",
            ),
            QAItem(
                question=f"What did {caregiver.id} do after realizing {child.id} was only drowsy?",
                answer=f"{caregiver.id} tucked the blanket around {child.id} and sat nearby with a warm smile.",
            ),
            QAItem(
                question=f"How did the story end for {child.id} and {caregiver.id}?",
                answer=f"They reconciled kindly, and {child.id} settled into a peaceful bedtime rest.",
            ),
        ]
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does snuff mean when talking about a candle?",
            answer="To snuff a candle means to put out its flame gently.",
        ),
        QAItem(
            question="What does it mean to drowse?",
            answer="To drowse means to feel sleepy and drift toward rest.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people make up after a small disagreement and feel friendly again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


@dataclass
class Registry:
    pass


ASP_RULES = r"""
% A story is compatible when the place affords the action.
valid(Place, Action, Item) :- affords(Place, Action), item(Item).

% Snuffing a candle is only reasonable for the non-safe candle item.
compatible(Place, snuff, candle) :- valid(Place, snuff, candle).

% Drowsing works in any place that affords it and can pair with any item.
compatible(Place, drowse, Item) :- valid(Place, drowse, Item).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, room in PLACES.items():
        lines.append(asp.fact("place", place))
        for action in sorted(room.affords):
            lines.append(asp.fact("affords", place, action))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        if item.safe:
            lines.append(asp.fact("safe", item_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming story world about snuff, drowse, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = valid_combos()
    combos = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.action is None or c[1] == args.action)
        and (args.item is None or c[2] == args.item)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, item = rng.choice(sorted(combos))
    if args.action == "snuff" and item == "nightlight":
        raise StoryError("(No story: a nightlight is not meant to be snuffed.)")
    gender = args.gender or rng.choice(["girl", "boy"])
    caregiver = args.caregiver or rng.choice(CAREGIVERS)
    name = args.name or rng.choice(CHILD_NAMES)
    return StoryParams(place=place, action=action, item=item, name=name, child_type=gender, caregiver_type=caregiver)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], params.action, ITEMS[params.item], params.name, params.child_type, params.caregiver_type)
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
    StoryParams(place="living_room", action="snuff", item="candle", name="Mia", child_type="girl", caregiver_type="mother"),
    StoryParams(place="bedroom", action="drowse", item="blanket", name="Theo", child_type="boy", caregiver_type="father"),
    StoryParams(place="nursery", action="snuff", item="candle", name="Ivy", child_type="girl", caregiver_type="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, action, item in combos:
            print(f"  {place:12} {action:8} {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.action} at {p.place} ({p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
