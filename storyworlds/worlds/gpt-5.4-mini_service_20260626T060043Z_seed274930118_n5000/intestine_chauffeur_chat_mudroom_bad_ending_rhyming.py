#!/usr/bin/env python3
"""
A standalone story world for a tiny rhyming tale set in a mudroom.

Premise:
- A child meets a chauffeur in the mudroom.
- They chat by the coat hooks and a science prop called an intestine model.
- A muddy slip ruins the model, and the story ends badly.

The world is deliberately small, classical, and state-driven:
entities have physical meters and emotional memes, the narration is built from
simulated state, and the ending reflects the damage that happened.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import re
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
    carried_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "chauffeur"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def is_dirty(self) -> bool:
        return self.meter("muddy") >= THRESHOLD or self.meter("broken") >= THRESHOLD


@dataclass
class Setting:
    place: str = "the mudroom"
    affords: set[str] = field(default_factory=lambda: {"chat"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    damage: str
    keyword: str = "chat"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    fragility: str
    owner_kind: str = "child"


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    chauffeur_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


ACTIVITIES = {
    "chat": Activity(
        id="chat",
        verb="chat",
        gerund="chatting",
        mess="mud",
        damage="smeared with mud",
        keyword="chat",
        tags={"chat", "mud"},
    )
}

PRIZES = {
    "intestine": Prize(
        id="intestine",
        label="intestine model",
        phrase="a long red intestine model for class",
        fragility="soft and squishy",
        owner_kind="child",
    )
}

SETTINGS = {
    "mudroom": Setting(place="the mudroom", affords={"chat"})
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Nora"]
BOY_NAMES = ["Leo", "Finn", "Max", "Theo"]
CHAUFFEUR_NAMES = ["Marl", "Bert", "Otto", "Jules"]


def rhyme(a: str, b: str) -> str:
    return f"{a} {b}"


def _step_chat(world: World, child: Entity, chauffeur: Entity, prize: Entity) -> list[str]:
    out: list[str] = []
    if world.fired:
        return out
    world.fired.add(("chat",))
    child.memes["curious"] = child.memes.get("curious", 0.0) + 1
    chauffeur.memes["kind"] = chauffeur.memes.get("kind", 0.0) + 1
    out.append(
        f"In the mudroom bright, where boots lined tight, {child.id} met {chauffeur.id} in a chatty light."
    )
    out.append(
        f"They talked by the rack in a sing-song way, while {prize.label} waited there for the school-day display."
    )
    return out


def _step_slip(world: World, child: Entity, chauffeur: Entity, prize: Entity) -> list[str]:
    out: list[str] = []
    if ("slip",) in world.fired:
        return out
    world.fired.add(("slip",))
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    chauffeur.memes["alarm"] = chauffeur.memes.get("alarm", 0.0) + 1
    child.meters["muddy"] = child.meters.get("muddy", 0.0) + 1
    chauffeur.meters["muddy"] = chauffeur.meters.get("muddy", 0.0) + 1
    prize.meters["muddy"] = prize.meters.get("muddy", 0.0) + 1
    out.append(
        f"But a drip-dip slip made the floor slick quick, and the little one skidded with a muddy kick."
    )
    out.append(
        f"The model bounced once, then sank in the muck; its red little shape had some very bad luck."
    )
    return out


def _step_break(world: World, child: Entity, chauffeur: Entity, prize: Entity) -> list[str]:
    out: list[str] = []
    if ("break",) in world.fired:
        return out
    if prize.meter("muddy") < THRESHOLD:
        return out
    world.fired.add(("break",))
    prize.meters["broken"] = prize.meters.get("broken", 0.0) + 1
    child.memes["sad"] = child.memes.get("sad", 0.0) + 1
    chauffeur.memes["regret"] = chauffeur.memes.get("regret", 0.0) + 1
    out.append(
        f"It smushed in the slush with a soggy thud; the neat red belly turned into mud."
    )
    out.append(
        f"No cloth could save it, no careful hand; the class-day treasure was ruined and bland."
    )
    return out


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for fn in (_step_chat, _step_slip, _step_break):
            before = len(world.fired)
            extra = fn(world, world.get("child"), world.get("chauffeur"), world.get("prize"))
            if extra:
                changed = True
                for line in extra:
                    world.say(line)
            if len(world.fired) != before:
                changed = True


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, gender: str,
         chauffeur_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=gender, label=name))
    chauffeur = world.add(Entity(id="chauffeur", kind="character", type="chauffeur", label=chauffeur_name))
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        type=prize_cfg.id,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=child.id,
        caretaker=chauffeur.id,
    ))

    world.say(
        f"{name} wore a grin in the mudroom dim, and {chauffeur_name} came in with a chatty hymn."
    )
    world.say(
        f"{name} had {prize_cfg.phrase}, soft and neat, and held it close as a class-time treat."
    )
    world.para()
    world.say(
        f"In the mudroom nook, they started to chat; the words went round like a kitten on a mat."
    )
    propagate(world)
    world.para()
    if prize.meter("broken") >= THRESHOLD:
        world.say(
            f"So the day went wrong in a rhyming blur: the model was ruined, and that was sure."
        )
        world.say(
            f"{name} got quiet, and {chauffeur_name} sighed low; the muddy red pieces could not be made to glow."
        )

    world.facts.update(
        child=child,
        chauffeur=chauffeur,
        prize=prize,
        activity=activity,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    chauffeur = f["chauffeur"]
    prize = f["prize"]
    return [
        f'Write a short rhyming story for a young child set in {world.setting.place} about {child.label}, {chauffeur.label}, and a {prize.label}.',
        f'Write a bad-ending rhyming story where a child named {child.label} and a chauffeur named {chauffeur.label} chat in the mudroom.',
        f'Write a simple rhyming tale that includes the words "intestine", "chauffeur", and "chat" and ends sadly in the mudroom.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    chauffeur: Entity = f["chauffeur"]  # type: ignore[assignment]
    prize: Entity = f["prize"]  # type: ignore[assignment]
    qs = [
        QAItem(
            question=f"Who was chatting in the mudroom?",
            answer=f"{child.label} was chatting with {chauffeur.label} in the mudroom."
        ),
        QAItem(
            question=f"What fragile thing did {child.label} have with them?",
            answer=f"{child.label} had a {prize.label}, a long red intestine model for class."
        ),
        QAItem(
            question=f"What happened to the intestine model?",
            answer="It fell into the mud, got smeared and broken, and could not be saved."
        ),
    ]
    return qs


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a chauffeur?",
            answer="A chauffeur is a person who drives someone else in a car."
        ),
        QAItem(
            question="What is a mudroom?",
            answer="A mudroom is a small room for shoes, coats, and wet, muddy things."
        ),
        QAItem(
            question="What does chat mean?",
            answer="To chat means to talk in a friendly, easy way."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        out.append(
            f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}"
        )
    out.append(f"fired={sorted(world.fired)}")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming bad-ending story world in a mudroom.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--chauffeur-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place != "mudroom":
        raise StoryError("This storyworld only supports the mudroom.")
    if args.activity and args.activity != "chat":
        raise StoryError("This storyworld only supports the chat activity.")
    if args.prize and args.prize != "intestine":
        raise StoryError("This storyworld only supports the intestine model prize.")
    if args.gender is None:
        gender = rng.choice(["girl", "boy"])
    else:
        gender = args.gender
    if args.name is None:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    else:
        name = args.name
    chauffeur_name = args.chauffeur_name or rng.choice(CHAUFFEUR_NAMES)
    return StoryParams(
        place="mudroom",
        activity="chat",
        prize="intestine",
        name=name,
        gender=gender,
        chauffeur_name=chauffeur_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        params.chauffeur_name,
    )
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


ASP_RULES = r"""
place(mudroom).
activity(chat).
prize(intestine).

affords(mudroom,chat).

narrative_ok(P,A,R) :- place(P), activity(A), prize(R), affords(P,A).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("place", "mudroom"),
        asp.fact("activity", "chat"),
        asp.fact("prize", "intestine"),
        asp.fact("affords", "mudroom", "chat"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show narrative_ok/3."))
    atoms = set(asp.atoms(model, "narrative_ok"))
    want = {("mudroom", "chat", "intestine")}
    if atoms == want:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH:", atoms, want)
    return 1


CURATED = [
    StoryParams(place="mudroom", activity="chat", prize="intestine", name="Mia", gender="girl", chauffeur_name="Jules"),
    StoryParams(place="mudroom", activity="chat", prize="intestine", name="Leo", gender="boy", chauffeur_name="Marl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show narrative_ok/3."))
        return
    if args.asp:
        print("1 compatible story combo: mudroom / chat / intestine")
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
