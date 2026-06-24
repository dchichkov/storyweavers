#!/usr/bin/env python3
"""
A tiny bedtime story world about four small friends, a little suspense, and a
gentle rhyming night-time turn.

Premise:
- Four children are at a sleepover in a quiet house.
- A storm makes the hallway look spooky.
- They want to find a lost blanket before bed.

World model:
- Physical meters: fear, noise, dark, cozy, found, tired.
- Emotional memes: courage, wonder, comfort, trust.

The story is driven by state changes: a spooky sound raises fear, a shared rhyme
gives courage, a lantern reveals the missing blanket, and the ending image proves
the room became cozy again.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old house"
    detail: str = "a narrow hallway, a quiet stair, and a warm bedroom"
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    friend_names: list[str]
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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


def _m(e: Entity, key: str, delta: float = 1.0) -> float:
    e.meters[key] = e.meters.get(key, 0.0) + delta
    return e.meters[key]


def _em(e: Entity, key: str, delta: float = 1.0) -> float:
    e.memes[key] = e.memes.get(key, 0.0) + delta
    return e.memes[key]


def rhyme_line(a: str, b: str) -> str:
    return f"{a} and {b} made a soft little rhyme."


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)

    hero = world.add(Entity(id=params.hero_name, kind="character", type="girl", label=params.hero_name))
    friends = [
        world.add(Entity(id=name, kind="character", type="boy" if i % 2 else "girl", label=name))
        for i, name in enumerate(params.friend_names)
    ]
    blanket = world.add(Entity(id="blanket", type="blanket", label="blue blanket", phrase="a blue blanket"))
    lantern = world.add(Entity(id="lantern", type="thing", label="little lantern", phrase="a little lantern"))
    storm = world.add(Entity(id="storm", type="thing", label="storm", phrase="a storm"))

    hero.meters["tired"] = 1
    for f in friends:
        f.memes["trust"] = 1

    world.say(
        f"Four friends were getting sleepy in {setting.place}, where {setting.detail} waited like a hush."
    )
    world.say(
        f"{hero.id} had the blue blanket, and the other three were already tucked in and whispering."
    )
    world.say("Outside, the wind went tap-tap-tap, and the window curtains swayed like shy white wings.")

    world.para()
    _m(storm, "noise", 1)
    _m(hero, "fear", 1)
    _m(hero, "dark", 1)
    _em(hero, "wonder", 1)
    world.say(
        f"Then the hallway gave a creak. {hero.id} paused, because the dark looked taller than before."
    )
    world.say(
        f"One friend said, 'That sound is loud,' and another said, 'But we are four, so we are brave and proud.'"
    )
    world.say("The rhyme was tiny, but it made the room feel less strange.")

    world.para()
    _em(hero, "courage", 1)
    for f in friends:
        _em(f, "courage", 1)
        _em(f, "comfort", 1)
    _m(hero, "fear", -0.5)
    world.say(
        f"{hero.id} held the lantern, and the four of them went down the hall in a careful line."
    )
    world.say(
        rhyme_line("soft feet", "neat beats")
    )

    world.para()
    _m(lantern, "light", 1)
    _m(blanket, "found", 1)
    _m(hero, "fear", -1)
    _m(hero, "cozy", 1)
    world.say(
        f"The lantern glowed beside the stairs, and there, curled under the little bench, was the blue blanket."
    )
    world.say(
        f"It had only slipped away, but it had made the whole house seem spooky for a moment."
    )
    world.say(
        f"{hero.id} laughed a tiny laugh, and the friends laughed too, because the mystery was solved."
    )

    world.para()
    _em(hero, "comfort", 1)
    _em(hero, "trust", 1)
    for f in friends:
        _em(f, "comfort", 1)
    _m(hero, "tired", 1)
    world.say(
        f"Back in the bedroom, {hero.id} tucked the blue blanket under {hero.pronoun('possessive')} chin."
    )
    world.say(
        f"The four friends listened to the storm, but now it sounded far away, like a drum behind a dream."
    )
    world.say(
        f"With the lantern dim and the blanket found, the room grew warm, small, and cozy, and everyone drifted to sleep."
    )

    world.facts.update(
        hero=hero,
        friends=friends,
        blanket=blanket,
        lantern=lantern,
        storm=storm,
        setting=setting,
    )
    return world


SETTINGS = {
    "house": Setting(place="the old house", detail="a narrow hallway, a quiet stair, and a warm bedroom"),
    "cabin": Setting(place="the little cabin", detail="a wooden hall, a tiny rug, and a crackling hearth"),
    "attic": Setting(place="the attic room", detail="a slanted ceiling, a sleepy window, and a stack of quilts"),
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a bedtime story about four friends in {f["setting"].place} where a small scare turns gentle.',
        f"Tell a rhyming bedtime story where {hero.id} and three friends look for a missing blanket at night.",
        "Write a soft suspense story for children that ends cozy and safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    names = ", ".join(x.id for x in f["friends"][:2])
    return [
        QAItem(
            question="How many friends were in the bedtime story?",
            answer="There were four friends, and they stayed together the whole time.",
        ),
        QAItem(
            question=f"What worried {hero.id} at first?",
            answer=f"{hero.id} worried when the hallway creaked and the dark looked spooky for a moment.",
        ),
        QAItem(
            question="What was the mystery they solved?",
            answer="They found the blue blanket that had slipped under the little bench.",
        ),
        QAItem(
            question=f"What did {names} help do?",
            answer="They helped carry the lantern, make a brave rhyme, and search the hall together.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The blanket was back where it belonged, and the room felt warm and cozy for sleep.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a lantern do?",
            answer="A lantern gives off light so people can see in a dark place.",
        ),
        QAItem(
            question="Why can a hallway feel spooky at night?",
            answer="A hallway can feel spooky at night because shadows look bigger and sounds seem louder.",
        ),
        QAItem(
            question="What helps children feel brave in a scary moment?",
            answer="Staying together, speaking kindly, and making a little plan can help children feel brave.",
        ),
    ]


ASP_RULES = r"""
scene(four_friends).
if_lantern_on(light).
if_searching(brave).
if_blanket_found(cozy).
resolved(cozy) :- if_blanket_found(cozy), if_lantern_on(light), if_searching(brave).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("scene", "four_friends"),
            asp.fact("light", "lantern"),
            asp.fact("searching", "brave"),
            asp.fact("blanket", "found"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny bedtime story world with rhyme and suspense.")
    ap.add_argument("--place", choices=SETTINGS)
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
    place = args.place or rng.choice(list(SETTINGS))
    hero_name = rng.choice(["Mina", "Luna", "Tia", "Nia", "Sera"])
    pool = ["Beck", "Ollie", "Milo", "Jasper", "Finn", "Theo", "Ira", "Noel"]
    rng.shuffle(pool)
    friend_names = pool[:3]
    if len(set([hero_name] + friend_names)) < 4:
        raise StoryError("Need four distinct friends for the story.")
    return StoryParams(place=place, hero_name=hero_name, friend_names=friend_names)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("\n== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}\nA: {q.answer}")
    out.append("\n== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}\nA: {q.answer}")
    return "\n".join(out)


def asp_verify() -> int:
    import storyworlds.asp as asp
    got = set(asp.atoms(asp.one_model(asp_program("#show resolved/1.")), "resolved"))
    want = {("cozy",)}
    if got == want:
        print("OK: ASP parity matches the Python reasoning gate.")
        return 0
    print("MISMATCH:")
    print("  asp:", sorted(got))
    print("  py :", sorted(want))
    return 1


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
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show resolved/1."))
        print(f"resolved: {asp.atoms(model, 'resolved')}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(place=place, hero_name="Mina", friend_names=["Beck", "Ollie", "Theo"])
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
