#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/intrigue_spatula_art_room_sharing_whodunit.py
===============================================================================================================

A small story world about sharing art-room tools, a missing spatula, and a
gentle child-friendly whodunit.

Seed tale premise:
- In an art room, kids are sharing paint, glue, and paper.
- A spatula that helps scrape and spread paint goes missing.
- The room feels full of intrigue until the children notice clues.
- The mystery ends when they discover the spatula was borrowed for a shared
  collage and returned clean, with a helpful explanation.

This world keeps the action concrete:
- Physical meters track paint, glue, tidiness, and whether the spatula is
  misplaced or stained.
- Emotional memes track curiosity, worry, guilt, relief, and generosity.
- A forward simulation predicts whether the spatula will get messy or hidden.
- The whodunit turn is driven by clues in the world, not by canned prose.
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
    held_by: Optional[str] = None
    shared: bool = False
    cleanable: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        gender = self.type
        if gender == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the art room"


@dataclass
class StoryParams:
    name: str
    friend: str
    gender: str
    friend_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def meter_get(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def meme_get(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def meter_add(ent: Entity, key: str, amount: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def meme_add(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _r_misplace_spatula(world: World) -> list[str]:
    out: list[str] = []
    spatula = world.get("spatula")
    if spatula.held_by is None and meter_get(spatula, "misplaced") >= THRESHOLD:
        sig = ("missing",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        out.append("The art room felt a little strange without the spatula on the table.")
        return out
    return []


def _r_paint_smudge(world: World) -> list[str]:
    out: list[str] = []
    spatula = world.get("spatula")
    if meter_get(spatula, "painted") < THRESHOLD:
        return out
    sig = ("smudge",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("A bright paint smear clung to the spatula's handle.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_misplace_spatula, _r_paint_smudge):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_after_borrow(world: World, borrower: Entity) -> dict:
    sim = world.copy()
    spatula = sim.get("spatula")
    meter_add(spatula, "used", 1)
    meter_add(spatula, "painted", 1)
    spatula.held_by = borrower.id
    if borrower.id != sim.facts["hero"].id:
        meter_add(spatula, "misplaced", 1)
    propagate(sim, narrate=False)
    return {
        "misplaced": meter_get(spatula, "misplaced") >= THRESHOLD,
        "painted": meter_get(spatula, "painted") >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} and {friend.id} were two children in {world.setting.place}, "
        f"where the shelves held paper, jars of paint, and shared tools."
    )
    world.say(
        f"They liked to share because one small idea could become a bigger picture "
        f"when both sets of hands helped."
    )


def mystery_starts(world: World, hero: Entity) -> None:
    world.say(
        f"Then {hero.id} looked at the work table and frowned. The spatula was gone."
    )
    meme_add(hero, "intrigue", 1)
    meme_add(hero, "worry", 1)
    world.say(
        f"{hero.pronoun().capitalize()} felt a little intrigue, because the spatula "
        f"had been there just a moment ago."
    )


def clue_one(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{friend.id} said they had seen a shiny streak of blue paint near the collage board."
    )
    meme_add(hero, "curiosity", 1)
    meme_add(friend, "helpfulness", 1)


def clue_two(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} noticed a paint smear on the spatula tray and a paper star stuck to the floor."
    )
    world.say(
        f"That did not sound like theft. It sounded like someone had hurried while sharing supplies."
    )


def reveal(world: World, hero: Entity, friend: Entity) -> None:
    spatula = world.get("spatula")
    spoiler = world.get("spatula_user")
    world.say(
        f"At last, they found the answer: {spoiler.id} had borrowed the spatula to spread glue on a shared collage."
    )
    world.say(
        f"{spoiler.id} had cleaned it, but then set it on the drying rack instead of the table."
    )
    meme_add(hero, "relief", 1)
    meme_add(hero, "trust", 1)
    meme_add(spoiler, "guilt", 1 if spoiler.id != hero.id else 0)
    spatula.held_by = "table"
    meter_add(spatula, "misplaced", -1 if meter_get(spatula, "misplaced") >= THRESHOLD else 0)
    world.say(
        f"{hero.id} smiled, because the mystery was not mean at all. It was only a mix-up in a busy room."
    )


def ending(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"After that, they put the spatula back where everyone could reach it, and they kept sharing the art table."
    )
    world.say(
        f"The last picture on the page showed {hero.id} and {friend.id} working side by side, "
        f"with the spatula back in its cup like a helpful little tool."
    )


def tell(params: StoryParams) -> World:
    world = World(Setting())
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_gender))
    spatula = world.add(Entity(
        id="spatula",
        kind="thing",
        type="spatula",
        label="spatula",
        phrase="a shared paint spatula",
        owner=hero.id,
        held_by="table",
        shared=True,
    ))
    world.add(Entity(id="spatula_user", kind="character", type=params.friend_gender, label=params.friend))

    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["spatula"] = spatula
    world.facts["spatula_user"] = friend

    introduce(world, hero, friend)
    world.para()
    mystery_starts(world, hero)
    clue_one(world, hero, friend)
    clue_two(world, hero, friend)

    meter_add(spatula, "used", 1)
    meter_add(spatula, "painted", 1)
    meter_add(spatula, "misplaced", 1)
    spatula.held_by = None
    propagate(world, narrate=True)

    world.para()
    reveal(world, hero, friend)
    ending(world, hero, friend)
    return world


KNOWLEDGE = {
    "spatula": [
        QAItem(
            question="What is a spatula used for in art rooms?",
            answer="In an art room, a spatula can spread glue or paint and help move sticky materials around."
        ),
        QAItem(
            question="Why is a shared tool important?",
            answer="A shared tool is important because more than one person can use it, so everyone can keep making art."
        ),
    ],
    "sharing": [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use something too, so people can take turns and work together."
        ),
    ],
    "art_room": [
        QAItem(
            question="What do children do in an art room?",
            answer="Children in an art room paint, draw, cut paper, glue pieces together, and make pictures."
        ),
    ],
    "whodunit": [
        QAItem(
            question="What is a whodunit story?",
            answer="A whodunit story is a mystery story where readers try to figure out who did something."
        ),
    ],
    "intrigue": [
        QAItem(
            question="What does intrigue mean in a story?",
            answer="Intrigue means a feeling that makes you curious and eager to find out what is going on."
        ),
    ],
}


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    return [
        f"Write a child-friendly whodunit in an art room about {hero.id}, {friend.id}, and a missing spatula.",
        f"Tell a story about sharing art supplies, where the missing spatula creates intrigue but ends kindly.",
        f"Create a short mystery story set in the art room that explains who borrowed the spatula and why.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    spatula = world.facts["spatula"]
    return [
        QAItem(
            question=f"Who started to feel intrigue when the spatula was missing?",
            answer=f"{hero.id} started to feel intrigue when {spatula.label} was missing from the art table."
        ),
        QAItem(
            question=f"What clue helped {hero.id} and {friend.id} solve the mystery?",
            answer="A blue paint smear and the drying rack showed that the spatula had been borrowed for art, not stolen."
        ),
        QAItem(
            question="What happened to the spatula at the end?",
            answer="The spatula was put back where everyone could reach it, so the children could keep sharing it."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in ("art_room", "sharing", "spatula", "intrigue", "whodunit"):
        out.extend(KNOWLEDGE.get(tag, []))
    return out


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.shared:
            bits.append("shared=True")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


NAMES_GIRL = ["Mia", "Luna", "Ivy", "Nora", "Zoe", "Ada"]
NAMES_BOY = ["Theo", "Leo", "Finn", "Owen", "Max", "Noah"]


CURATED = [
    StoryParams(name="Mia", friend="Theo", gender="girl", friend_gender="boy"),
    StoryParams(name="Leo", friend="Nora", gender="boy", friend_gender="girl"),
    StoryParams(name="Ivy", friend="Noah", gender="girl", friend_gender="boy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Art-room whodunit about sharing a spatula.")
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    friend = args.friend or rng.choice(NAMES_BOY if friend_gender == "boy" else NAMES_GIRL)
    if name == friend:
        raise StoryError("Hero and friend must be different children.")
    return StoryParams(name=name, friend=friend, gender=gender, friend_gender=friend_gender)


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
{ borrow(H,F) } :- hero(H), friend(F), H != F.
missing_spatula :- borrow(_,F), friend(F).
shared_tool(spatula).
intrigue(H) :- missing_spatula, hero(H).
clue(blue_smear) :- borrow(H,F), hero(H), friend(F).
solved :- clue(blue_smear), shared_tool(spatula).
#show missing_spatula/0.
#show intrigue/1.
#show solved/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero", "hero"),
        asp.fact("friend", "friend"),
        asp.fact("tool", "spatula"),
        asp.fact("setting", "art_room"),
        asp.fact("theme", "sharing"),
        asp.fact("style", "whodunit"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show missing_spatula/0.\n#show intrigue/1.\n#show solved/0."))
    atoms = {(s.name, len(s.arguments)) for s in model}
    expected = {("missing_spatula", 0), ("intrigue", 1), ("solved", 0)}
    if expected.issubset(atoms):
        print("OK: ASP program is loadable and produces the expected predicates.")
        return 0
    print("ASP verification failed.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show missing_spatula/0.\n#show intrigue/1.\n#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name} and {p.friend} in the art room"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
