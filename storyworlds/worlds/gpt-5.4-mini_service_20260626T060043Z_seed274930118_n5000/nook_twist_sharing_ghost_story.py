#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/nook_twist_sharing_ghost_story.py
=============================================================================================================

A small storyworld inspired by a gentle ghost story in a cozy nook:
a child hears a spooky twist, learns to share, and discovers the "ghost"
was not scary at all.

The world is intentionally tiny and constraint-checked:
- a child likes a quiet nook
- a second child arrives with a toy, blanket, or book to share
- a spooky misunderstanding creates tension
- a twist reveals the ghostly clue was only a reflection, a shadow, or a
  soft sound from the nook
- sharing helps everyone feel safe and happy

The prose is driven by a simulated world model with meters and memes.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["spook", "warmth", "curiosity", "comfort", "share", "fear"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the nook"
    detail: str = "a cozy reading nook by the window"
    sound: str = "a tiny creak"
    shadow_source: str = "the curtain"


@dataclass
class StoryThing:
    id: str
    label: str
    phrase: str
    type: str
    kind: str = "thing"


@dataclass
class StoryParams:
    name: str
    gender: str
    friend_name: str
    friend_gender: str
    shared_item: str
    twist: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _spook(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.chars():
        if ent.memes["fear"] < THRESHOLD:
            continue
        sig = ("spook", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["curiosity"] += 1
        out.append(f"{ent.id} felt a chilly shiver and looked harder at the nook.")
    return out


def _share(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    friend = world.get("friend")
    item = world.get("shared")
    if child.memes["share"] < THRESHOLD:
        return out
    sig = ("share", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.shared_with.update({"child", "friend"})
    child.memes["comfort"] += 1
    friend.memes["comfort"] += 1
    out.append(f"They both held {item.phrase} together.")
    return out


def _twist(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["curiosity"] < THRESHOLD or child.meters["spook"] < THRESHOLD:
        return []
    sig = ("twist",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] = 0.0
    child.memes["comfort"] += 1
    return ["__twist__"]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_spook, _share, _twist):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__twist__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTING = Setting(
    place="the nook",
    detail="a cozy reading nook with a cushion, a lamp, and a little shelf",
    sound="a soft thump from behind the curtain",
    shadow_source="the rocking chair",
)

SHARED_ITEMS = {
    "book": StoryThing(id="book", label="book", phrase="the picture book", type="book"),
    "blanket": StoryThing(id="blanket", label="blanket", phrase="the blue blanket", type="blanket"),
    "toy": StoryThing(id="toy", label="toy", phrase="the plush rabbit", type="toy"),
}

TWISTS = {
    "shadow": "a shadow",
    "reflection": "a reflection",
    "creak": "a creak",
}

GIRL_NAMES = ["Maya", "Nora", "Lily", "Zoe", "Ava", "Ivy", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Theo", "Finn", "Max", "Noah", "Eli"]
TRAITS = ["curious", "gentle", "brave", "quiet", "wary", "kind"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for item in SHARED_ITEMS:
        for twist in TWISTS:
            combos.append((SETTING.place, item, twist))
    return combos


def reasonableness_gate(shared_item: str, twist: str) -> None:
    if shared_item not in SHARED_ITEMS:
        raise StoryError("Unknown shared item.")
    if twist not in TWISTS:
        raise StoryError("Unknown twist.")
    if shared_item == "toy" and twist == "reflection":
        raise StoryError("This twist is too weak for the toy story; use a shadow or creak.")
    if shared_item == "blanket" and twist == "creak":
        raise StoryError("A creak does not reasonably motivate a blanket-sharing resolution here.")


def introduce(world: World, child: Entity) -> None:
    trait = next((t for t in child.traits if t != "little"), "quiet")
    world.say(
        f"{child.id} was a little {trait} {child.type} who loved the nook."
    )


def love_nook(world: World, child: Entity) -> None:
    child.memes["comfort"] += 1
    world.say(
        f"{child.pronoun().capitalize()} liked the soft lamp glow and the calm air in the nook."
    )


def bring_item(world: World, friend: Entity, item: Entity) -> None:
    item.carried_by = friend.id
    world.say(
        f"One day, {friend.id} came with {item.phrase} to share."
    )


def spooky_sound(world: World, child: Entity) -> None:
    child.meters["spook"] += 1
    child.memes["fear"] += 1
    world.say(
        f"Then {world.setting.sound} came from behind {world.setting.shadow_source}."
    )


def worry(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} hugged {child.pronoun('possessive')} arms and stared at the dark corner."
    )
    child.memes["curiosity"] += 1


def twist_reveal(world: World, child: Entity, twist: str) -> None:
    child.memes["fear"] = 0.0
    if twist == "shadow":
        world.say(
            f"But the ghostly shape was only a shadow from the lamp."
        )
    elif twist == "reflection":
        world.say(
            f"Then {child.id} saw that the ghostly flicker was only a reflection in the window."
        )
    else:
        world.say(
            f"Then {child.id} heard that the spooky sound was only a creak in the old chair."
        )


def share_and_finish(world: World, child: Entity, friend: Entity, item: Entity) -> None:
    child.memes["share"] += 1
    child.memes["comfort"] += 1
    friend.memes["comfort"] += 1
    world.say(
        f"{child.id} smiled, moved over, and said they could share {item.phrase}."
    )
    propagate(world, narrate=False)
    world.say(
        f"{child.id} and {friend.id} sat together in the nook, sharing {item.phrase} until the scary feeling was gone."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.gender,
        traits=["little", params.name.lower(), "curious"],
    ))
    child.id = params.name
    world.entities[params.name] = child
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=params.friend_gender,
        traits=["little", params.friend_name.lower(), "kind"],
    ))
    friend.id = params.friend_name
    world.entities[params.friend_name] = friend
    item_cfg = SHARED_ITEMS[params.shared_item]
    item = world.add(Entity(
        id="shared",
        type=item_cfg.type,
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        owner=friend.id,
    ))

    world.facts.update(params=params, child=child, friend=friend, item=item, twist=params.twist)

    introduce(world, child)
    love_nook(world, child)
    bring_item(world, friend, item)

    world.para()
    spooky_sound(world, child)
    worry(world, child)
    propagate(world, narrate=False)

    world.para()
    twist_reveal(world, child, params.twist)
    share_and_finish(world, child, friend, item)

    world.facts["shared_item"] = item
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a gentle ghost story for a young child that happens in a nook and includes "{p.twist}".',
        f"Tell a short story where {p.name} feels spooked in the nook, then learns to share {p.shared_item}.",
        f"Write a cozy spooky story about a nook, a surprise twist, and two children sharing a quiet moment.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child: Entity = world.facts["child"]
    friend: Entity = world.facts["friend"]
    item: Entity = world.facts["item"]
    qa = [
        QAItem(
            question=f"Where did {p.name} first notice the spooky thing?",
            answer=f"{p.name} noticed it in the nook, where the lamp and cushion made the room feel quiet.",
        ),
        QAItem(
            question=f"What did {p.friend_name} bring to share?",
            answer=f"{p.friend_name} brought {item.phrase} to share with {p.name}.",
        ),
        QAItem(
            question=f"How did {p.name} feel at the end?",
            answer=f"{p.name} felt safe and cozy at the end, because the scary thing was solved and they shared together.",
        ),
    ]
    qa.append(
        QAItem(
            question=f"What was the ghostly twist really?",
            answer=f"The ghostly twist was really {world.facts['twist']} in the nook, not a real ghost.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a nook?",
            answer="A nook is a small cozy corner, often made for sitting, reading, or resting.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something with you.",
        ),
        QAItem(
            question="Why can shadows look spooky?",
            answer="Shadows can look spooky because they change shape when light moves, even though they are not dangerous.",
        ),
    ]
    return out


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
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.shared_with:
            bits.append(f"shared_with={sorted(e.shared_with)}")
        if e.kind == "character":
            bits.append("character")
        lines.append(f"  {e.id:8} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


@dataclass
class StoryParamsCLI:
    place: Optional[str] = None
    name: Optional[str] = None
    gender: Optional[str] = None
    friend_name: Optional[str] = None
    friend_gender: Optional[str] = None
    shared_item: Optional[str] = None
    twist: Optional[str] = None
    n: int = 1
    seed: Optional[int] = None
    all: bool = False
    trace: bool = False
    qa: bool = False
    json: bool = False
    asp: bool = False
    verify: bool = False
    show_asp: bool = False


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny ghost-story world about a nook, a twist, and sharing.")
    ap.add_argument("--place", choices=[SETTING.place], default=None)
    ap.add_argument("--name", default=None)
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--friend-name", default=None)
    ap.add_argument("--friend-gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--shared-item", choices=list(SHARED_ITEMS), default=None)
    ap.add_argument("--twist", choices=list(TWISTS), default=None)
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
    shared_item = args.shared_item or rng.choice(list(SHARED_ITEMS))
    twist = args.twist or rng.choice(list(TWISTS))
    reasonableness_gate(shared_item, twist)

    gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != name])

    return StoryParams(
        name=name,
        gender=gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        shared_item=shared_item,
        twist=twist,
    )


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
place(nook).
shared_item(book).
shared_item(blanket).
shared_item(toy).
twist(shadow).
twist(reflection).
twist(creak).

valid(Place, Item, Twist) :- place(Place), shared_item(Item), twist(Twist), reasonable(Item, Twist).

reasonable(book, shadow).
reasonable(book, reflection).
reasonable(book, creak).
reasonable(blanket, shadow).
reasonable(blanket, reflection).
reasonable(toy, shadow).
reasonable(toy, creak).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "nook")]
    for item in SHARED_ITEMS:
        lines.append(asp.fact("shared_item", item))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
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


CURATED = [
    StoryParams(name="Maya", gender="girl", friend_name="Leo", friend_gender="boy", shared_item="book", twist="shadow"),
    StoryParams(name="Noah", gender="boy", friend_name="Ivy", friend_gender="girl", shared_item="blanket", twist="reflection"),
    StoryParams(name="Lily", gender="girl", friend_name="Ben", friend_gender="boy", shared_item="toy", twist="creak"),
]


def explain_rejection(shared_item: str, twist: str) -> str:
    if shared_item == "toy" and twist == "reflection":
        return "(No story: this toy-and-reflection pairing is too weak for a true twist; choose a shadow or creak.)"
    if shared_item == "blanket" and twist == "creak":
        return "(No story: a creak does not make a good spooky twist for a blanket-sharing nook story.)"
    return "(No story: the chosen pair does not make a reasonable nook twist story.)"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
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
            header = f"### {p.name}: {p.shared_item} + {p.twist}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
