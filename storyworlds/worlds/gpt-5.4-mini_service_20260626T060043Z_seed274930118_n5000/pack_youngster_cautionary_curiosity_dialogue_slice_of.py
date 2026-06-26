#!/usr/bin/env python3
"""
A small storyworld about a youngster, a pack, and a cautious curious choice.

Premise:
- A youngster is preparing a small pack for an ordinary day.
- Curiosity tempts them to add one more thing.
- A cautionary voice helps them notice what truly belongs inside.
- Dialogue carries the turn from "maybe" to "yes, that's enough."

The simulated world tracks:
- physical load in the pack
- whether items are fragile, useful, or unnecessary
- emotional pressure from curiosity and caution
- the final, calmer feeling when the pack is just right
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
    contents: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class PackItem:
    id: str
    label: str
    phrase: str
    weight: float
    useful: bool
    fragile: bool = False
    mood: str = "plain"


@dataclass
class Scene:
    place: str
    reason: str
    caution: str
    weather: str
    goal: str


@dataclass
class StoryParams:
    place: str
    reason: str
    pack_item: str
    name: str
    gender: str
    cautioner: str
    mood: str
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene):
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        clone = World(self.scene)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SCENES = {
    "park": Scene(place="the park", reason="a small walk", caution="not to forget the water", weather="bright", goal="a calm little outing"),
    "library": Scene(place="the library", reason="story time", caution="to keep things quiet", weather="soft", goal="a neat little visit"),
    "grandma": Scene(place="Grandma's house", reason="tea and a chat", caution="to bring only one careful choice", weather="warm", goal="a cozy afternoon"),
    "train": Scene(place="the station", reason="a short ride", caution="to keep the pack light", weather="breezy", goal="a tidy trip"),
}

PACK_ITEMS = {
    "book": PackItem("book", "picture book", "a picture book", 1.0, useful=True, mood="gentle"),
    "snack": PackItem("snack", "small snack", "a small snack in a paper wrapper", 0.5, useful=True, mood="tasty"),
    "toy": PackItem("toy", "tiny toy", "a tiny toy with bright paint", 0.7, useful=False, fragile=True, mood="curious"),
    "jumper": PackItem("jumper", "jumper", "a light jumper", 0.8, useful=True, mood="warm"),
    "stone": PackItem("stone", "shiny stone", "a shiny stone from the path", 1.4, useful=False, fragile=False, mood="interesting"),
    "note": PackItem("note", "note", "a folded note with a doodle", 0.2, useful=True, mood="kind"),
}

NAMES_GIRL = ["Mina", "Lina", "Sage", "Ivy", "Nora", "Tess"]
NAMES_BOY = ["Owen", "Milo", "Finn", "Eli", "Jude", "Theo"]
MOODS = ["curious", "quiet", "thoughtful", "bright", "restless"]
CAUTIONERS = ["mother", "father", "grandparent", "older sibling"]


def pack_capacity_ok(world: World, pack: Entity) -> bool:
    return pack.meters.get("load", 0.0) <= 3.0


def reasonableness_gate(scene: Scene, item: PackItem) -> bool:
    if scene.place == "the library" and item.id == "toy":
        return False
    if scene.place == "the station" and item.weight > 1.0:
        return False
    if scene.place == "Grandma's house" and item.id == "stone":
        return False
    return True


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, scene in SCENES.items():
        for item_id, item in PACK_ITEMS.items():
            if reasonableness_gate(scene, item):
                combos.append((place, item_id))
    return combos


def introduce(world: World, child: Entity, cautioner: Entity, item: PackItem) -> None:
    world.say(
        f"{child.id} was a little {child.type} who liked getting ready for ordinary days. "
        f"Today {child.pronoun()} wanted to pack {item.phrase} for {world.scene.reason}."
    )
    world.say(
        f"{cautioner.pronoun().capitalize()} kept a gentle eye on the bag and said, "
        f'"Let us pack slowly and keep the little things useful."'
    )


def gather(world: World, child: Entity, item: PackItem) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    world.say(
        f"{child.id} peered into the open pack and smiled. "
        f'"Can I bring this too?" {child.pronoun()} asked, holding up {item.phrase}.'
    )


def warn(world: World, cautioner: Entity, child: Entity, item: PackItem) -> bool:
    if item.fragile:
        world.say(
            f'"That one might get bumped around," {cautioner.pronoun()} said. '
            f'"A careful pack should hold things that can travel safely."'
        )
        child.memes["caution"] = child.memes.get("caution", 0) + 1
        return True
    if item.weight > 1.0:
        world.say(
            f'"That looks heavy for such a small pack," {cautioner.pronoun()} said. '
            f'"Let us not make your shoulders grumble."'
        )
        child.memes["caution"] = child.memes.get("caution", 0) + 1
        return True
    return False


def dialogue_turn(world: World, child: Entity, cautioner: Entity, item: PackItem) -> None:
    world.say(
        f'"But it is so interesting," {child.pronoun()} said. '
        f'"Do we have to leave it out?"'
    )
    world.say(
        f'"We do if it does not help the day," {cautioner.pronoun()} said. '
        f'"A pack is nicest when it is just right, not crowded and not empty."'
    )


def choose(world: World, child: Entity, cautioner: Entity, item: PackItem) -> None:
    if item.useful:
        world.say(
            f"{child.id} nodded and tucked {item.phrase} into the pack with care. "
            f"{cautioner.id} smiled because useful things belonged there."
        )
    else:
        world.say(
            f"{child.id} looked again, then set {item.phrase} back on the table. "
            f'"Maybe another day," {child.pronoun()} said, and the pack felt lighter at once.'
        )
    world.facts["packed"] = item.useful
    world.facts["item"] = item


def finish(world: World, child: Entity, cautioner: Entity, pack: Entity, item: PackItem) -> None:
    if item.useful:
        child.memes["joy"] = child.memes.get("joy", 0) + 1
        pack.contents.append(item.id)
        pack.meters["load"] = pack.meters.get("load", 0.0) + item.weight
        world.say(
            f"At last the pack was neat and ready. {child.id} felt proud carrying it, "
            f"and {cautioner.id} said the little bag was perfect for {world.scene.goal}."
        )
    else:
        child.memes["peace"] = child.memes.get("peace", 0) + 1
        world.say(
            f"The pack stayed light, with room for the things that really mattered. "
            f"{child.id} and {cautioner.id} left together, talking softly on the way."
        )


def tell(scene: Scene, item: PackItem, name: str, gender: str, cautioner_kind: str, mood: str) -> World:
    world = World(scene)
    child = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={"curiosity": 1.0, "mood": 1.0}))
    cautioner = world.add(Entity(id="Caretaker", kind="character", type=cautioner_kind, meters={}, memes={}))
    pack = world.add(Entity(id="Pack", kind="thing", type="pack", label="small pack", phrase="a small pack", meters={"load": 0.0}, memes={}))

    world.facts.update(scene=scene, item=item, mood=mood, child=child, cautioner=cautioner, pack=pack)

    introduce(world, child, cautioner, item)
    world.para()
    gather(world, child, item)
    warn(world, cautioner, child, item)
    dialogue_turn(world, child, cautioner, item)
    choose(world, child, cautioner, item)
    world.para()
    finish(world, child, cautioner, pack, item)
    return world


@dataclass
class StoryParams:
    place: str
    reason: str
    pack_item: str
    name: str
    gender: str
    cautioner: str
    mood: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    item = f["item"]
    scene = f["scene"]
    return [
        f'Write a slice-of-life story for a young child about packing for {scene.reason}.',
        f"Tell a gentle cautionary story where {child.id} wants to pack {item.phrase} for {scene.place}.",
        f'Write a short dialogue-heavy story about a youngster, a pack, and a careful choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    item = f["item"]
    cautioner = f["cautioner"]
    scene = f["scene"]
    pack = f["pack"]
    return [
        QAItem(
            question=f"What did {child.id} want to put in the pack?",
            answer=f"{child.id} wanted to put {item.phrase} in the pack.",
        ),
        QAItem(
            question=f"Who gave the cautious advice about the pack?",
            answer=f"{cautioner.id} gave the cautious advice and reminded {child.id} to keep the pack useful.",
        ),
        QAItem(
            question=f"What happened to the pack at the end of the story?",
            answer=(
                f"The pack ended up neat and ready for {scene.goal}."
                if item.useful
                else f"The pack stayed light because {child.id} left the extra thing out."
            ),
        ),
        QAItem(
            question=f"Why did the adult speak carefully about the pack?",
            answer=(
                f"The adult spoke carefully because {item.phrase} was either fragile or not a helpful choice for the day."
            ),
        ),
        QAItem(
            question=f"How did {child.id} feel after choosing what belonged in the pack?",
            answer=(
                f"{child.id} felt calm and proud after making a careful choice about the pack."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a pack?", answer="A pack is a bag you carry on your back or by a strap so you can bring things with you."),
        QAItem(question="Why do people pack lightly sometimes?", answer="People pack lightly so the bag is easier to carry and the important things do not get buried."),
        QAItem(question="What does cautious mean?", answer="Cautious means careful and not rushing into a choice."),
        QAItem(question="What does curiosity mean?", answer="Curiosity is the feeling that makes you want to look, ask, and learn about new things."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.contents:
            bits.append(f"contents={e.contents}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(scene: Scene, item: PackItem) -> str:
    return (
        f"(No story: {item.phrase} does not fit the ordinary slice-of-life situation at {scene.place}; "
        f"try another item or place.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.pack_item:
        if not reasonableness_gate(SCENES[args.place], PACK_ITEMS[args.pack_item]):
            raise StoryError(explain_rejection(SCENES[args.place], PACK_ITEMS[args.pack_item]))
    choices = [(p, i) for p, i in valid_combos()
               if (args.place is None or p == args.place)
               and (args.pack_item is None or i == args.pack_item)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    place, item_id = rng.choice(sorted(choices))
    scene = SCENES[place]
    item = PACK_ITEMS[item_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    cautioner = args.cautioner or rng.choice(CAUTIONERS)
    mood = args.mood or rng.choice(MOODS)
    return StoryParams(place=place, reason=scene.reason, pack_item=item_id, name=name, gender=gender, cautioner=cautioner, mood=mood)


def generate(params: StoryParams) -> StorySample:
    scene = SCENES[params.place]
    item = PACK_ITEMS[params.pack_item]
    world = tell(scene, item, params.name, params.gender, params.cautioner, params.mood)
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


ASP_RULES = r"""
% A pack choice is valid when the item is reasonable for the scene.
valid(Place, Item) :- place(Place), item(Item), reasonable(Place, Item).

% A choice is cautious if it is valid and the item is useful or harmless.
cautious(Place, Item) :- valid(Place, Item), safe(Item).

% In this world, fragile or too-heavy items are not a good fit for some places.
unsafe_choice(Place, Item) :- fragile(Item), place(Place), not library_place(Place).
unsafe_choice(Place, Item) :- heavy(Item), station_place(Place).

safe(Item) :- item(Item), not fragile(Item), not heavy(Item).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SCENES:
        lines.append(asp.fact("place", place))
        if place == "library":
            lines.append(asp.fact("library_place", place))
        if place == "train":
            lines.append(asp.fact("station_place", place))
    for item_id, item in PACK_ITEMS.items():
        lines.append(asp.fact("item", item_id))
        if item.fragile:
            lines.append(asp.fact("fragile", item_id))
        if item.weight > 1.0:
            lines.append(asp.fact("heavy", item_id))
    for place, item_id in valid_combos():
        lines.append(asp.fact("reasonable", place, item_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


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
    ap = argparse.ArgumentParser(description="A slice-of-life storyworld about a youngster packing a small bag.")
    ap.add_argument("--place", choices=SCENES)
    ap.add_argument("--pack-item", choices=PACK_ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--cautioner", choices=CAUTIONERS)
    ap.add_argument("--mood", choices=MOODS)
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


CURATED = [
    StoryParams(place="park", reason=SCENES["park"].reason, pack_item="book", name="Mina", gender="girl", cautioner="mother", mood="curious"),
    StoryParams(place="library", reason=SCENES["library"].reason, pack_item="note", name="Owen", gender="boy", cautioner="father", mood="thoughtful"),
    StoryParams(place="grandma", reason=SCENES["grandma"].reason, pack_item="snack", name="Lina", gender="girl", cautioner="grandparent", mood="bright"),
    StoryParams(place="train", reason=SCENES["train"].reason, pack_item="jumper", name="Theo", gender="boy", cautioner="older sibling", mood="restless"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} valid pack choices:\n")
        for place, item in combos:
            print(f"  {place:10} {item}")
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
            except StoryError as e:
                print(e)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
