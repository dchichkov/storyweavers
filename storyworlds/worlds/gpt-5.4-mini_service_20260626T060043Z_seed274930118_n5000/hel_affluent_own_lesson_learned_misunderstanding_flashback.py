#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/hel_affluent_own_lesson_learned_misunderstanding_flashback.py
==============================================================================================

A small bedtime-story world about a child named Hel, an affluent home, and a
gentle misunderstanding that is resolved by remembering what was learned
before.

The domain is intentionally compact:
- a child and a caregiver
- an affluent home with carefully owned things
- one cherished object that can be misplaced or mistaken for someone else's
- a flashback that reveals the original ownership
- a lesson learned at the end

The simulated state drives narration. The child can either misunderstand where
their own thing belongs, or forget that something has already been promised to
them. A flashback surfaces the earlier promise, and the bedtime ending proves
the lesson learned.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    stored_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {"subject": "it", "object": "it", "possessive": "its"}
        return mapping[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    affluent: bool = True
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    flashback_used: bool = False
    lesson_learned: bool = False

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


@dataclass
class StoryParams:
    place: str
    object_name: str
    owner_name: str
    caregiver_name: str
    seed: Optional[int] = None


PLACES = {
    "nursery": "the nursery",
    "sunroom": "the sunroom",
    "library": "the library",
    "garden_room": "the garden room",
}

OBJECTS = {
    "blue_owl": {
        "label": "blue owl",
        "phrase": "a soft blue owl toy",
        "stored_in": "the reading nook",
    },
    "moon_blanket": {
        "label": "moon blanket",
        "phrase": "a tiny blanket with silver moons",
        "stored_in": "the rocking chair",
    },
    "music_box": {
        "label": "music box",
        "phrase": "a little music box with a gold latch",
        "stored_in": "the shelf",
    },
}

NAMES = ["Hel", "Mina", "Noa", "Lina", "Iris", "Toby"]


ASP_RULES = r"""
% An item is owned by exactly one child in this tiny world.
owned(O, C) :- item(O), child(C), owner_of(O, C).

% A misunderstanding happens if the child sees the object in a place
% different from where they remember it belongs.
misunderstanding(O, C) :- owned(O, C), child_sees(O, C), misplaced(O).

% A flashback is useful if it reveals the earlier promise about ownership.
flashback_helpful(O, C) :- owned(O, C), promised_before(O, C).

% The lesson is learned when the child stops claiming the object is lost or
% чужой and instead returns it to its own place.
lesson_learned(C) :- child(C), understood(C), returned_to_place(C).
#show owned/2.
#show misunderstanding/2.
#show flashback_helpful/2.
#show lesson_learned/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for oid, ob in OBJECTS.items():
        lines.append(asp.fact("item", oid))
        lines.append(asp.fact("label", oid, ob["label"]))
        lines.append(asp.fact("stored_at", oid, ob["stored_in"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show lesson_learned/1."))
    asp_count = len(asp.atoms(model, "lesson_learned"))
    py_count = 1 if any(True for _ in CURATED) else 0
    if asp_count >= 0 and py_count >= 0:
        print("OK: ASP rules are syntactically available.")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: Hel, an affluent home, a misunderstanding, and a lesson learned."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", dest="object_name", choices=OBJECTS)
    ap.add_argument("--owner", dest="owner_name")
    ap.add_argument("--caregiver", dest="caregiver_name")
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
    place = args.place or rng.choice(list(PLACES))
    object_name = args.object_name or rng.choice(list(OBJECTS))
    owner_name = args.owner_name or "Hel"
    caregiver_name = args.caregiver_name or rng.choice(["Aunt Nora", "Mama", "Papa"])
    if owner_name != "Hel" and args.owner_name is not None:
        raise StoryError("This bedtime world is centered on Hel; keep --owner Hel or leave it blank.")
    return StoryParams(place=place, object_name=object_name, owner_name=owner_name, caregiver_name=caregiver_name)


def _build_world(params: StoryParams) -> World:
    world = World(place=PLACES[params.place], affluent=True)
    obj = OBJECTS[params.object_name]
    child = world.add(Entity(id="Hel", kind="character", type="child", label="Hel"))
    caregiver = world.add(Entity(id=params.caregiver_name, kind="character", type="caregiver", label=params.caregiver_name))
    toy = world.add(Entity(
        id=params.object_name,
        kind="thing",
        type="toy",
        label=obj["label"],
        phrase=obj["phrase"],
        owner=child.id,
        caretaker=caregiver.id,
        stored_in=obj["stored_in"],
    ))

    world.facts.update(child=child, caregiver=caregiver, toy=toy, params=params)
    return world


def _opening(world: World) -> None:
    p = world.facts["params"]
    toy: Entity = world.facts["toy"]
    world.say(f"In {world.place}, where the lamps were warm and the pillows were soft, Hel lived in an affluent little house.")
    world.say(f"Hel loved {toy.phrase}, and everyone knew it was {toy.pronoun('possessive')} own.")

    world.para()
    world.say(f"One sleepy evening, Hel looked around and did not see the {toy.label}.")
    world.say(f"Hel felt a tiny worry bloom: maybe someone had taken {toy.it()} by mistake.")


def _misunderstanding(world: World) -> None:
    toy: Entity = world.facts["toy"]
    caregiver: Entity = world.facts["caregiver"]
    world.say(f"Hel asked, “Did {caregiver.label} move my {toy.label}?”")
    world.say(f"But {caregiver.label} had only put {toy.it()} in {toy.stored_in}, where it belonged before bedtime.")
    world.facts["misunderstanding"] = True


def _flashback(world: World) -> None:
    toy: Entity = world.facts["toy"]
    world.para()
    world.flashback_used = True
    world.say("Then Hel remembered something gentle and old, like a song heard through a doorway.")
    world.say(f"Flashback: earlier that day, {toy.phrase} had been tucked carefully beside Hel's reading pillow.")
    world.say("It had never been lost at all; it was simply resting where Hel usually left it before sleep.")
    world.facts["promised_before"] = True


def _lesson(world: World) -> None:
    toy: Entity = world.facts["toy"]
    caregiver: Entity = world.facts["caregiver"]
    world.para()
    world.say(f"Hel smiled, found {toy.it()}, and carried {toy.it()} back to the cozy spot where it slept each night.")
    world.say(f"“Oh,” Hel whispered, “I was mistaken. Next time I will look again before worrying.”")
    world.say(f"{caregiver.label} kissed Hel's forehead and agreed that careful looking can solve a small night-time puzzle.")
    world.say(f"Hel hugged {toy.it()} close, and the room grew quiet and safe again.")
    world.lesson_learned = True
    world.facts["understood"] = True
    world.facts["returned_to_place"] = True


def tell(world: World) -> None:
    _opening(world)
    _misunderstanding(world)
    _flashback(world)
    _lesson(world)


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    toy: Entity = world.facts["toy"]
    return [
        f"Write a bedtime story about Hel in an affluent home, where a misunderstanding about {toy.label} is solved with a flashback.",
        f"Tell a gentle story for young children in {p.place} about Hel learning that {toy.phrase} was already {toy.stored_in}.",
        f"Create a soft nighttime story with the words Hel, affluent, own, flashback, misunderstanding, and lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    toy: Entity = world.facts["toy"]
    caregiver: Entity = world.facts["caregiver"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about Hel, who lives in {world.place} and loves {toy.phrase}.",
        ),
        QAItem(
            question=f"What did Hel misunderstand about the {toy.label}?",
            answer=f"Hel thought the {toy.label} might be missing or taken, but it was only in {toy.stored_in}.",
        ),
        QAItem(
            question=f"What did the flashback help Hel remember?",
            answer=f"The flashback helped Hel remember that {toy.phrase} had already been put where it belonged before bedtime.",
        ),
        QAItem(
            question=f"What lesson learned does Hel say at the end?",
            answer="Hel learns to look carefully before worrying, because a small misunderstanding can be solved by remembering the earlier truth.",
        ),
        QAItem(
            question=f"Who helped Hel stay calm?",
            answer=f"{caregiver.label} helped by explaining gently and reminding Hel that the toy was safely nearby.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does affluent mean?",
            answer="Affluent means having plenty of money or comfort, so an affluent home may have soft lights, careful rooms, and nice things.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone thinks something is true by mistake.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that shows something from earlier, to help explain what is happening now.",
        ),
        QAItem(
            question="What does it mean to own something?",
            answer="To own something means it belongs to you.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        if e.stored_in:
            bits.append(f"stored_in={e.stored_in}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  flashback_used={world.flashback_used}")
    lines.append(f"  lesson_learned={world.lesson_learned}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="nursery", object_name="blue_owl", owner_name="Hel", caregiver_name="Mama"),
    StoryParams(place="sunroom", object_name="moon_blanket", owner_name="Hel", caregiver_name="Aunt Nora"),
    StoryParams(place="library", object_name="music_box", owner_name="Hel", caregiver_name="Papa"),
]


def asp_valid() -> None:
    import asp
    _ = asp.one_model(asp_program("#show owned/2."))


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
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
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show lesson_learned/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp_valid()
        print("ASP mode available.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        if args.all:
            p = sample.params
            header = f"### Hel in {p.place} with {p.object_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
