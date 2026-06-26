#!/usr/bin/env python3
"""
storyworlds/worlds/sissie_bravery_nursery_rhyme.py
===================================================

A small storyworld about Sissie and a brave little rhyme-like journey.

Seed tale:
---
Sissie was a tiny child with a big beating heart.
She liked soft songs, warm mittens, and counting stars before bed.
One dusk, a little lamb lost its blue bell in the grass.
The path to the bell was dim and a bit scary, but Sissie wanted to help.

Her granny held up a lantern and said, “Bravery is not being without fear.
Bravery is taking a small step anyway.”
So Sissie took Granny's hand, walked past the dark hedge, found the bell,
and smiled when the lamb rang it all the way home.

World shape:
- Sissie has fear, then bravery, then relief and pride.
- A small object is at risk in a dim place.
- A helper offers a gentle lantern-and-hand compromise.
- The ending proves change by showing the recovered object and a brighter heart.

This world keeps the style close to a nursery rhyme: short lines, soft images,
repetition, and child-friendly concrete nouns.
"""

from __future__ import annotations

import argparse
import dataclasses
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
        if self.type in {"girl", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    dim: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    verb: str
    gerund: str
    rush: str
    fear: str
    zone: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_fear(world: World) -> list[str]:
    out = []
    sissie = world.get("sissie")
    if sissie.memes.get("fear", 0.0) >= THRESHOLD and "fear_spoke" not in world.fired:
        world.fired.add("fear_spoke")
        out.append("Sissie felt a little wobble in her knees.")
    return out


def _r_brave_step(world: World) -> list[str]:
    out = []
    sissie = world.get("sissie")
    helper = world.get("granny")
    if sissie.memes.get("bravery", 0.0) >= THRESHOLD and "brave_step" not in world.fired:
        world.fired.add("brave_step")
        out.append(f"Sissie took {helper.pronoun('possessive')} hand and went on.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(challenge: Challenge) -> bool:
    return challenge.zone in {"dark_path", "hedge", "bridge"}


def select_aid(challenge: Challenge) -> Optional[Aid]:
    for aid in AID_CATALOG:
        if challenge.id in aid.helps:
            return aid
    return None


def _do_challenge(world: World, hero: Entity, challenge: Challenge, narrate: bool = True) -> None:
    if challenge.id not in world.setting.affords:
        raise StoryError("That setting does not fit that bravery challenge.")
    hero.meters["distance"] = hero.meters.get("distance", 0.0) + 1
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    propagate(world, narrate=narrate)


def predict(world: World, challenge: Challenge) -> dict:
    sim = world.copy()
    _do_challenge(sim, sim.get("sissie"), challenge, narrate=False)
    return {"brave": sim.get("sissie").memes.get("bravery", 0.0) >= THRESHOLD}


SETTINGS = {
    "lantern_lane": Setting(place="the lantern lane", dim=True, affords={"lost_bell", "bridge_cross"}),
    "hedge_path": Setting(place="the hedge path", dim=True, affords={"lost_bell"}),
    "meadow": Setting(place="the meadow", dim=False, affords={"lost_bell"}),
}

CHALLENGES = {
    "lost_bell": Challenge(
        id="lost_bell",
        verb="find the little bell",
        gerund="looking for the little bell",
        rush="hurry down the dim path",
        fear="the dark hedge",
        zone="dark_path",
        risk="lost in the grass",
        keyword="bell",
        tags={"bell", "dark", "help"},
    ),
    "bridge_cross": Challenge(
        id="bridge_cross",
        verb="cross the little bridge",
        gerund="crossing the little bridge",
        rush="step onto the swaying boards",
        fear="the wobbly plank",
        zone="bridge",
        risk="too scary to cross",
        keyword="bridge",
        tags={"bridge", "dark", "help"},
    ),
}

AID_CATALOG = [
    Aid(id="lantern", label="a warm lantern", prep="hold up a warm lantern", tail="walked on in the glow", helps={"lost_bell", "bridge_cross"}),
    Aid(id="hand", label="Granny's hand", prep="take Granny's hand", tail="went on together hand in hand", helps={"lost_bell", "bridge_cross"}),
]

CURATED = [
    ("lantern_lane", "lost_bell"),
    ("hedge_path", "lost_bell"),
    ("lantern_lane", "bridge_cross"),
]


@dataclass
class StoryParams:
    place: str
    challenge: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Sissie and a small bravery rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
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
    combos = [c for c in CURATED if (args.place is None or c[0] == args.place) and (args.challenge is None or c[1] == args.challenge)]
    if not combos:
        raise StoryError("No valid bravery story matches those choices.")
    place, challenge = rng.choice(combos)
    return StoryParams(place=place, challenge=challenge)


def tell(setting: Setting, challenge: Challenge) -> World:
    world = World(setting)
    sissie = world.add(Entity(id="sissie", kind="character", type="girl", label="Sissie"))
    granny = world.add(Entity(id="granny", kind="character", type="grandmother", label="Granny"))
    bell = world.add(Entity(id="bell", type="thing", label="blue bell", phrase="a blue bell", owner="lamb", caretaker="granny"))
    lamb = world.add(Entity(id="lamb", kind="character", type="thing", label="little lamb"))

    world.say("Sissie was a small child with a bright, brave smile, and she liked songs that went soft and slow.")
    world.say(f"She was {challenge.gerund}, and the dim air made her heart beat thumpety-thump.")
    world.say(f"A little lamb had lost {bell.pronoun('possessive')} blue bell, and {challenge.fear} waited near the grass.")

    world.para()
    sissie.memes["fear"] = 1
    world.say(f"Then Granny said, “Bravery is not the same as never being scared.”")
    world.say(f"“Bravery is choosing to go on when the path feels hard.”")

    aid = select_aid(challenge)
    if aid is None:
        raise StoryError("No gentle aid exists for this bravery challenge.")
    world.facts["aid"] = aid
    world.facts["challenge"] = challenge

    if predict(world, challenge)["brave"]:
        world.say(f"Granny lifted {aid.label} and said, “Let us {aid.prep}.”")
        sissie.memes["bravery"] = 1
        sissie.memes["fear"] = max(0.0, sissie.memes.get("fear", 0.0) - 1)
        _do_challenge(world, sissie, challenge)
        world.para()
        world.say(f"Sissie {aid.tail}, and soon she found the bell in the grass.")
        world.say(f"The lamb gave one happy ring-rang-rung, and Sissie stood taller than before.")
        world.say("Her knees were still tiny, but her brave heart felt bigger.")
    else:
        raise StoryError("The world model could not find a brave resolution.")
    world.facts.update(sissie=sissie, granny=granny, bell=bell, lamb=lamb, setting=setting, challenge=challenge)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    ch: Challenge = f["challenge"]
    return [
        f'Write a short nursery-rhyme story about Sissie being brave and {ch.gerund}.',
        f'Write a gentle child story where Sissie meets {ch.fear} but keeps going with help from Granny.',
        f'Write a rhyming story for a small child about Sissie, a blue bell, and a brave little step.',
    ]


def story_qa(world: World) -> list[QAItem]:
    ch: Challenge = world.facts["challenge"]
    aid: Aid = world.facts["aid"]
    return [
        QAItem(
            question="Who was the story about?",
            answer="The story was about Sissie, a small girl with a brave heart, and Granny who helped her."
        ),
        QAItem(
            question=f"What was Sissie trying to do while {ch.gerund}?",
            answer=f"Sissie was trying to {ch.verb}, even though {ch.fear} made the path feel scary."
        ),
        QAItem(
            question=f"What did Granny do to help Sissie {ch.verb}?",
            answer=f"Granny held up {aid.label} and helped Sissie go on safely."
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="Sissie found the blue bell, the lamb was happy, and Sissie felt braver than before."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing something kind or important even when you feel scared."
        ),
        QAItem(
            question="What does a lantern do?",
            answer="A lantern gives light, so people can see better in a dark place."
        ),
        QAItem(
            question="Why might a little bell be easy to lose?",
            answer="A little bell is small, so it can slip into grass or hide under leaves."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    parts.extend(sample.prompts)
    parts.append("== Story QA ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("== World QA ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
challenge_valid(C) :- challenge(C).
has_aid(C) :- challenge(C), aid(A), helps(A,C).
valid_story(P,C) :- setting(P), challenge(C), has_aid(C).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge", cid))
    for aid in AID_CATALOG:
        lines.append(asp.fact("aid", aid.id))
        for c in sorted(aid.helps):
            lines.append(asp.fact("helps", aid.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for p, setting in SETTINGS.items():
        for c in setting.affords:
            if select_aid(CHALLENGES[c]) is not None:
                combos.append((p, c))
    return combos


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CHALLENGES[params.challenge])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, (place, challenge) in enumerate(CURATED):
            params = StoryParams(place=place, challenge=challenge, seed=base_seed + i)
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
