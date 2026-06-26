#!/usr/bin/env python3
"""
A small storyworld for a gentle ghost story with repetition and a happy ending.

Premise:
- A child hears repeated ghostly sounds at night.
- The child is afraid at first and tries to verify what is making the noise.
- The "ghost" turns out to be a friendly helper or misunderstood presence.
- The ending is safe, warm, and happy.

This world keeps the prose child-facing and concrete, while the simulation
tracks physical state (meters) and feelings (memes).
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
REPETITION_COUNT = 3


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    room: str = ""
    friendly: bool = False
    transparent: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.id.endswith("s") else "it"


@dataclass
class Setting:
    place: str = "the old house"
    spooky: str = "the hallway"
    hideout: str = "the closet"


@dataclass
class StoryParams:
    seed: Optional[int] = None
    place: str = "old_house"
    child_name: str = "Mia"
    child_type: str = "girl"
    parent_type: str = "mother"
    ghost_kind: str = "friendly"
    repetition: int = REPETITION_COUNT


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "old_house": Setting(place="the old house", spooky="the hallway", hideout="the closet"),
    "attic_house": Setting(place="the attic house", spooky="the attic stairs", hideout="the trunk"),
    "moon_house": Setting(place="the moonlit house", spooky="the back stairs", hideout="the curtain"),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Zoe", "Ava", "Ivy"]
BOY_NAMES = ["Ben", "Leo", "Finn", "Max", "Noah", "Eli"]
PARENTS = ["mother", "father"]
GHOST_KINDS = ["friendly", "shy", "helpful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost storyworld with repetition and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--ghost-kind", choices=GHOST_KINDS)
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
    place = args.place or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(PARENTS)
    ghost_kind = args.ghost_kind or rng.choice(GHOST_KINDS)
    return StoryParams(
        place=place,
        child_name=name,
        child_type=gender,
        parent_type=parent,
        ghost_kind=ghost_kind,
    )


def setting_detail(setting: Setting) -> str:
    return f"{setting.place.capitalize()} was quiet, and {setting.spooky} looked dark."


def _repeat_sound(world: World, ghost: Entity, count: int) -> None:
    world.facts["repetition_count"] = count
    for i in range(count):
        sig = ("knock", i)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ghost.meters["sound"] = ghost.meters.get("sound", 0.0) + 1
        world.say("Tap. Tap. Tap.")


def verify_sound(world: World, child: Entity, ghost: Entity) -> bool:
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    world.say(f"{child.id} listened hard and decided to verify the sound.")
    if ghost.friendly:
        world.say(
            f"It was not a scary ghost after all. It was {ghost.label}, a friendly helper hiding in {ghost.room}."
        )
        return True
    world.say(f"The sound stayed strange, and {child.id} still felt uneasy.")
    return False


def calm_resolution(world: World, child: Entity, parent: Entity, ghost: Entity) -> None:
    child.memes["worry"] = 0.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    ghost.meters["seen"] = ghost.meters.get("seen", 0.0) + 1
    world.say(
        f"{child.id} smiled and carried a warm lamp to {ghost.room}. "
        f"{parent.label or parent.type} smiled too, and the little ghost waved back."
    )
    world.say(
        f"That night, the tapping stopped, the room felt safe, and {child.id} fell asleep feeling brave."
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        label=params.child_name,
        meters={"distance": 0.0},
        memes={"worry": 0.0, "joy": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent_type,
        label=f"the {params.parent_type}",
        memes={"calm": 1.0},
    ))
    ghost = world.add(Entity(
        id="Ghost",
        kind="character",
        type="ghost",
        label="the little ghost",
        room=setting.hideout,
        friendly=params.ghost_kind in {"friendly", "helpful"},
        transparent=True,
        meters={"sound": 0.0},
        memes={"mischief": 0.0},
    ))

    world.say(f"One night at {setting.place}, {child.id} heard something in the dark.")
    world.say(setting_detail(setting))
    world.para()

    world.say(
        f"Then the sound came again and again: "
        f"{' '.join(['Tap.' for _ in range(params.repetition)])}"
    )
    _repeat_sound(world, ghost, params.repetition)
    world.para()

    world.say(
        f"{child.id} held close to {child.pronoun('possessive')} blanket and called for {parent.label}."
    )
    verified = verify_sound(world, child, ghost)
    world.para()

    if verified:
        calm_resolution(world, child, parent, ghost)
    else:
        world.say(
            f"{parent.label} checked the room with a lamp, and at last {child.id} saw the shadow was only a coat on a chair."
        )
        world.say(f"{child.id} laughed, because the scary ghost was just a sleepy old room.")
        world.say(f"Then {child.id} and {parent.label} tucked the blanket in and went to bed safe and warm.")

    world.facts.update(
        child=child,
        parent=parent,
        ghost=ghost,
        verified=verified,
        setting=setting,
        params=params,
    )
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    return [
        f'Write a gentle ghost story for a young child named {child.id} that uses repetition and ends happily.',
        f"Tell a short nighttime story where {child.id} hears a repeated sound, verifies it, and learns the ghost is safe.",
        f"Write a cozy spooky story in which {parent.label} helps {child.id} check the dark room.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    ghost: Entity = f["ghost"]
    verified = f["verified"]
    rep = f["repetition_count"]
    qas = [
        QAItem(
            question=f"Who heard the tapping sound at {world.setting.place}?",
            answer=f"{child.id} heard the tapping sound first, and {parent.label} came to help.",
        ),
        QAItem(
            question="How many times did the tapping repeat?",
            answer=f"It repeated {rep} times, which made the spooky sound feel extra noticeable.",
        ),
        QAItem(
            question="What did the child do to check the strange noise?",
            answer=f"{child.id} listened closely and decided to verify it instead of only guessing.",
        ),
    ]
    if verified:
        qas.append(
            QAItem(
                question="What was the ghost really like?",
                answer=f"The ghost was friendly, and it was only hiding in {ghost.room}."
            )
        )
    else:
        qas.append(
            QAItem(
                question="What made the sound if it was not the ghost?",
                answer=f"It turned out to be a harmless room object, so the scary idea was wrong."
            )
        )
    qas.append(
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt brave and happy, because the story ended safely and softly.",
        )
    )
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is often a pretend spooky character in a story, and sometimes it turns out to be friendly.",
        ),
        QAItem(
            question="Why do repeated sounds feel spooky at night?",
            answer="Repeated sounds feel spooky at night because the dark makes people pay extra attention to tiny noises.",
        ),
        QAItem(
            question="What does it mean to verify something?",
            answer="To verify something means to check it carefully so you know what is really true.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.room:
            bits.append(f"room={e.room}")
        if e.friendly:
            bits.append("friendly=True")
        if e.transparent:
            bits.append("transparent=True")
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
room_spooky(R) :- setting_room(R).
repetition_ok(N) :- N >= 3.
friendly_ghost(G) :- ghost(G), ghost_kind(G,friendly).
verified_story :- repetition_ok(N), repetition(N), friendly_ghost(G), helper(G).
happy_ending :- verified_story.
#show happy_ending/0.
#show repetition_ok/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("setting_room", setting.spooky))
        lines.append(asp.fact("hideout", setting.hideout))
    for k in GHOST_KINDS:
        lines.append(asp.fact("ghost_kind_label", k))
    lines.append(asp.fact("repetition", REPETITION_COUNT))
    lines.append(asp.fact("ghost", "Ghost"))
    lines.append(asp.fact("ghost_kind", "Ghost", "friendly"))
    lines.append(asp.fact("helper", "Ghost"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/0.\n#show repetition_ok/1."))
    atoms = {str(a) for a in model}
    if "happy_ending" in atoms and "repetition_ok(3)" in atoms:
        print("OK: ASP rules confirm the happy ending and repetition.")
        return 0
    print("MISMATCH: ASP rules did not confirm the expected outcome.")
    return 1


def asp_report() -> None:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/0.\n#show repetition_ok/1."))
    for atom in model:
        print(atom)


def resolve_explicit(args: argparse.Namespace) -> None:
    if args.ghost_kind and args.ghost_kind not in GHOST_KINDS:
        raise StoryError("unknown ghost kind")
    if args.place and args.place not in SETTINGS:
        raise StoryError("unknown place")


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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
    StoryParams(place="old_house", child_name="Mia", child_type="girl", parent_type="mother", ghost_kind="friendly"),
    StoryParams(place="attic_house", child_name="Ben", child_type="boy", parent_type="father", ghost_kind="helpful"),
    StoryParams(place="moon_house", child_name="Nora", child_type="girl", parent_type="father", ghost_kind="shy"),
]


def main() -> None:
    args = build_parser().parse_args()
    resolve_explicit(args)

    if args.show_asp:
        print(asp_program("#show happy_ending/0.\n#show repetition_ok/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp_report()
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
        if len(samples) > 1 and not args.all:
            print(f"### variant {i + 1}")
        elif args.all:
            p = sample.params
            print(f"### {p.child_name}: {p.place} / {p.ghost_kind}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
