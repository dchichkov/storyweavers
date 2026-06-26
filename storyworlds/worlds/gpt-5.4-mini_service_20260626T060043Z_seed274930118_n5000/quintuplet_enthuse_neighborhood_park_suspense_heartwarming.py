#!/usr/bin/env python3
"""
storyworlds/worlds/quintuplet_enthuse_neighborhood_park_suspense_heartwarming.py
================================================================================

A small heartwarming suspense world set in a neighborhood park.

Premise:
- Five quintuplet siblings visit the neighborhood park with a shared picnic and
  a handmade banner.
- They are enthusiastic about performing a little cheer for the community garden
  club.
- One of them briefly goes missing, creating gentle suspense.
- The group searches, stays together, and finds that the missing sibling was
  helping a younger child with a stuck kite.
- The ending is warm: everyone reunites, the cheer gets shared, and the park
  feels friendlier than before.

The world uses both physical meters and emotional memes, and the narrative is
state-driven rather than a frozen template.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        gender = self.type
        if gender in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    seed: Optional[int] = None
    park_name: str = "the neighborhood park"
    sibling_name: str = "Mia"
    sibling_kind: str = "girl"
    parent_kind: str = "mother"
    missing_name: str = "Nia"
    prop: str = "banner"
    snack: str = "lemon cookies"


@dataclass
class Setting:
    place: str
    benches: int = 2
    trees: int = 3
    affords: set[str] = field(default_factory=lambda: {"picnic", "search", "kites"})


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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _all_quintuplets(world: World) -> list[Entity]:
    return [e for e in world.characters() if e.memes.get("quintuplet", 0) >= THRESHOLD]


def _search_strength(world: World) -> float:
    return sum(e.memes.get("search", 0) for e in world.characters())


def _foster_help(world: World) -> list[str]:
    out: list[str] = []
    for child in _all_quintuplets(world):
        if child.memes.get("helping", 0) < THRESHOLD:
            continue
        sig = ("help", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["love"] = child.memes.get("love", 0) + 1
        out.append(f"{child.id} stayed close and helped with a small problem instead of making it bigger.")
    return out


def _reunion(world: World) -> list[str]:
    out: list[str] = []
    for child in _all_quintuplets(world):
        if child.memes.get("found", 0) < THRESHOLD:
            continue
        sig = ("reunion", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["joy"] = child.memes.get("joy", 0) + 1
        out.append(f"{child.id} ran back with a bright smile.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_foster_help, _reunion):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(params: StoryParams) -> World:
    setting = Setting(place=params.park_name)
    world = World(setting)

    parent = world.add(Entity(
        id="Parent", kind="character", type=params.parent_kind, label="their parent"
    ))
    siblings = []
    names = ["Ari", "Mia", "Noa", "Zoe", "Nia"]
    for idx, name in enumerate(names):
        child = world.add(Entity(
            id=name,
            kind="character",
            type="girl",
            label=name,
            plural=False,
        ))
        child.memes["quintuplet"] = 1
        child.memes["enthuse"] = 1
        child.memes["joy"] = 0.5
        child.memes["care"] = 1
        if idx == 0:
            child.memes["leader"] = 1
        siblings.append(child)

    banner = world.add(Entity(
        id="Banner",
        type="thing",
        label=params.prop,
        phrase=f"a hand-painted {params.prop}",
        owner="Ari",
    ))
    snack = world.add(Entity(
        id="Snack",
        type="thing",
        label=params.snack,
        phrase=f"some {params.snack}",
        owner="Parent",
    ))
    kite = world.add(Entity(
        id="Kite",
        type="thing",
        label="kite",
        phrase="a red kite with a long string",
        owner="LittleKid",
    ))
    littlekid = world.add(Entity(
        id="LittleKid",
        kind="character",
        type="boy",
        label="a little boy",
    ))

    world.facts.update(
        parent=parent,
        siblings=siblings,
        banner=banner,
        snack=snack,
        kite=kite,
        littlekid=littlekid,
        missing="Nia",
    )
    return world


def tell(world: World) -> None:
    p = world.facts["parent"]
    siblings: list[Entity] = world.facts["siblings"]  # type: ignore[assignment]
    banner: Entity = world.facts["banner"]  # type: ignore[assignment]
    snack: Entity = world.facts["snack"]  # type: ignore[assignment]
    missing: str = world.facts["missing"]  # type: ignore[assignment]
    littlekid: Entity = world.facts["littlekid"]  # type: ignore[assignment]
    kite: Entity = world.facts["kite"]  # type: ignore[assignment]

    world.say(
        f"At the neighborhood park, five quintuplet siblings arrived with a cheerful bounce, "
        f"carrying {banner.phrase} and a little basket of {snack.phrase}."
    )
    world.say(
        f"They loved to enthuse together, and today they wanted to cheer for everyone by the pond path."
    )
    world.para()

    for sib in siblings:
        sib.memes["enthuse"] += 1
        sib.memes["joy"] += 0.5
    world.say(
        f"Their parent smiled because the whole group was bright and busy, but one seat on the bench stayed empty."
    )
    world.say(
        f"{missing} had gone to look at the swings a moment ago, and then nobody could see {missing.lower()}."
    )
    world.say(
        f"The cheer stopped. The banner string twisted in the wind, and the siblings felt a small knot of suspense in their chests."
    )
    world.para()

    for sib in siblings:
        if sib.id != missing:
            sib.memes["search"] = sib.memes.get("search", 0) + 1
    p.memes["worry"] = p.memes.get("worry", 0) + 1
    world.say(
        f"The parent did not panic. Instead, {p.pronoun('subject')} pointed to the paths and said, "
        f'"One of you check the benches, one check the big oak tree, and one check the kite field."'
    )
    world.say(
        f"The quintuplets spread out, calling softly so they would not scare {missing.lower()} away."
    )

    world.facts["searched"] = True
    world.facts["suspense"] = True

    hidden_answer = False
    if littlekid.memes.get("stuck", 0) == 0:
        littlekid.memes["stuck"] = 1
    if kite.owner == "LittleKid":
        hidden_answer = True
    if hidden_answer:
        world.say(
            f"Near the far grass, {missing} was crouched beside a little boy whose red kite had snagged on a low branch."
        )
        world.say(
            f"{missing} had heard the boy sniffle and stayed to help tug the string free."
        )
        missing_ent = world.get(missing)
        missing_ent.memes["helping"] = 1
        missing_ent.memes["found"] = 1
        missing_ent.memes["relief"] = 1
        littlekid.memes["safe"] = 1
        littlekid.memes["gratitude"] = 1
        kite.owner = "LittleKid"
        world.facts["found_by_helping"] = True
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"When the others reached the grass, they saw that {missing} was not lost at all; {missing.lower()} was being kind."
    )
    world.say(
        f"The siblings laughed with relief, and their parent said it was a brave thing to help first and call second."
    )
    world.say(
        f"They all carried the banner back to the center path, and {missing} took the middle so nobody would lose sight of {missing.lower()} again."
    )
    world.say(
        f"Then the quintuplets proudly shared {snack.phrase} with the little boy, and the park felt warm and close, like one big friendly hug."
    )
    world.facts["resolved"] = True


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a heartwarming suspense story for young children set in a neighborhood park with five quintuplet siblings.',
        'Tell a gentle story where the word "enthuse" appears and a missing sibling is found helping someone else.',
        'Write a short, cozy park story about a worried search, a kind discovery, and a happy reunion.',
    ]


def story_qa(world: World) -> list[QAItem]:
    missing = world.facts["missing"]
    return [
        QAItem(
            question="How many siblings were at the park?",
            answer="Five quintuplet siblings were at the neighborhood park together.",
        ),
        QAItem(
            question=f"Why did the others feel suspense when {missing} was not on the bench?",
            answer=f"They felt suspense because {missing} had wandered away, and they could not see {missing.lower()} for a moment.",
        ),
        QAItem(
            question=f"What was {missing} doing when the others found {missing.lower()}?",
            answer=f"{missing} was helping a little boy with a kite that had gotten stuck in a low branch.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="Everyone was reunited, the missing sibling was safe, and the park felt warm and friendly again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quintuplet?",
            answer="Quintuplets are five siblings born at the same time.",
        ),
        QAItem(
            question="What does it mean to enthuse?",
            answer="To enthuse means to show excited, happy energy about something.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next, especially when something important is uncertain.",
        ),
        QAItem(
            question="What is a neighborhood park?",
            answer="A neighborhood park is a shared outdoor place where people can walk, play, and meet nearby neighbors.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{ent.id}: {ent.kind}/{ent.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
quintuplet(C) :- child(C), quintuplet_member(C).
all_quintuplets_present :- 5 { quintuplet_member(C) : child(C) } 5.
searching(C) :- child(C), search_role(C).
suspense :- missing(M), child(M), not found(M).
found(M) :- helping(M).
resolved :- found(M), all_quintuplets_present.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("park", "neighborhood_park"))
    for c in ["Ari", "Mia", "Noa", "Zoe", "Nia"]:
        lines.append(asp.fact("child", c))
        lines.append(asp.fact("quintuplet_member", c))
    lines.append(asp.fact("missing", "Nia"))
    lines.append(asp.fact("prop", "banner"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming suspense storyworld in a neighborhood park.")
    ap.add_argument("--park-name", default="the neighborhood park")
    ap.add_argument("--name")
    ap.add_argument("--missing-name")
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
    return StoryParams(
        seed=args.seed,
        park_name=args.park_name,
        sibling_name=args.name or rng.choice(["Mia", "Ari", "Zoe", "Noa", "Lia"]),
        sibling_kind="girl",
        parent_kind=rng.choice(["mother", "father"]),
        missing_name=args.missing_name or "Nia",
        prop=rng.choice(["banner", "poster", "sign"]),
        snack=rng.choice(["lemon cookies", "apple slices", "berry muffins"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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


def valid_story_count() -> int:
    return 1


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/0. #show suspense/0."))
    atoms = {(sym.name, len(sym.arguments)) for sym in model}
    if ("resolved", 0) in atoms and ("suspense", 0) in atoms:
        print("OK: ASP program can derive suspense and resolution.")
        return 0
    print("MISMATCH: ASP program failed to derive expected atoms.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show suspense/0. #show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show child/1. #show quintuplet_member/1. #show missing/1."))
        print("ASP facts:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = resolve_params(args, random.Random(base_seed))
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(20, args.n * 20):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
