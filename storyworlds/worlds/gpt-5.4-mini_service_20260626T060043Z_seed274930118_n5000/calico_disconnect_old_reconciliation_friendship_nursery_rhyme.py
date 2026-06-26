#!/usr/bin/env python3
"""
storyworlds/worlds/calico_disconnect_old_reconciliation_friendship_nursery_rhyme.py
===================================================================================

A tiny nursery-rhyme storyworld about a calico helper, an old broken connection,
and a warm reconciliation between friends.

Seed image:
- A calico kitten and a small friend are working with an old cart, ribbon, or
  toy line.
- Something disconnects or comes loose.
- The friends feel a little apart, then speak kindly, fix the link, and end
  together again.

The world keeps the story small and classical: a few typed entities, a clear
tension, a repair, and a closing image that proves friendship changed the state.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    connected_to: Optional[str] = None
    connector: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Relationship:
    """A small thing that can be disconnected and reconnected."""
    id: str
    label: str
    phrase: str
    connector: str
    fixed_with: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    relationship: str
    name: str
    friend_name: str
    trait: str
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


def _r_disconnect(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters.get("pull", 0.0) < THRESHOLD:
            continue
        if not ent.connected_to:
            continue
        sig = ("disconnect", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.connected_to = None
        ent.meters["broken"] = 1.0
        out.append(f"The old {ent.label} came loose with a little pop.")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    cat = world.entities.get("Calico")
    friend = world.entities.get("Friend")
    if not cat or not friend:
        return out
    if cat.memes.get("hurt", 0.0) < THRESHOLD and friend.memes.get("hurt", 0.0) < THRESHOLD:
        return out
    if cat.memes.get("warmth", 0.0) < THRESHOLD or friend.memes.get("warmth", 0.0) < THRESHOLD:
        return out
    sig = ("friendship",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cat.memes["hurt"] = 0.0
    friend.memes["hurt"] = 0.0
    cat.memes["friendship"] = cat.memes.get("friendship", 0.0) + 1.0
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1.0
    out.append("Their friendship grew soft and bright again.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    cat = world.entities.get("Calico")
    friend = world.entities.get("Friend")
    if not cat or not friend:
        return out
    if cat.memes.get("sorry", 0.0) < THRESHOLD or friend.memes.get("sorry", 0.0) < THRESHOLD:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cat.memes["peace"] = 1.0
    friend.memes["peace"] = 1.0
    out.append("They said sorry, and the little space between them disappeared.")
    return out


CAUSAL_RULES = [_r_disconnect, _r_reconcile, _r_friendship]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "nursery": Setting(place="the nursery", indoor=True, affords={"play"}),
    "yard": Setting(place="the old yard", indoor=False, affords={"play"}),
    "porch": Setting(place="the porch", indoor=False, affords={"play"}),
}

RELATIONSHIPS = {
    "ribbon": Relationship(
        id="ribbon",
        label="ribbon tie",
        phrase="a bright ribbon tie",
        connector="ribbon",
        fixed_with="a neat knot",
        keyword="ribbon",
        tags={"calico", "old", "friendship"},
    ),
    "string": Relationship(
        id="string",
        label="string link",
        phrase="an old string link",
        connector="string",
        fixed_with="fresh twine",
        keyword="string",
        tags={"old", "disconnect"},
    ),
    "hook": Relationship(
        id="hook",
        label="hook clasp",
        phrase="an old hook clasp",
        connector="hook",
        fixed_with="a small latch",
        keyword="hook",
        tags={"old"},
    ),
}

HERO_TRAITS = ["gentle", "cheerful", "curious", "playful", "merry"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for rel_id in setting.affords and RELATIONSHIPS:
            combos.append((place, rel_id))
    return combos


def prize_at_risk(rel: Relationship) -> bool:
    return True


def select_fix(rel: Relationship) -> Optional[str]:
    return rel.fixed_with


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for rid, r in RELATIONSHIPS.items():
        lines.append(asp.fact("relationship", rid))
        lines.append(asp.fact("connector", rid, r.connector))
        lines.append(asp.fact("fix", rid, r.fixed_with))
        for t in sorted(r.tags):
            lines.append(asp.fact("tagged", rid, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Rel) :- affords(Place, play), relationship(Rel).
reconcile(Place, Rel) :- valid(Place, Rel), connector(Rel, _), fix(Rel, _).
"""


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
    ap = argparse.ArgumentParser(
        description="A nursery-rhyme storyworld about a calico helper, an old disconnect, and friendship."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--relationship", choices=RELATIONSHIPS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--trait", choices=HERO_TRAITS)
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.relationship:
        combos = [c for c in combos if c[1] == args.relationship]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, rel_id = rng.choice(combos)
    name = args.name or rng.choice(["Mimi", "Nina", "Pip", "Luna", "Penny"])
    friend_name = args.friend_name or rng.choice(["Toby", "Theo", "Milo", "Bea", "Poppy"])
    trait = args.trait or rng.choice(HERO_TRAITS)
    return StoryParams(place=place, relationship=rel_id, name=name, friend_name=friend_name, trait=trait)


def _do_play(world: World, hero: Entity, rel: Relationship) -> None:
    hero.meters["pull"] = 1.0
    propagate(world, narrate=True)


def tell(setting: Setting, rel: Relationship, hero_name: str, friend_name: str, trait: str) -> World:
    world = World(setting)
    calico = world.add(Entity(
        id="Calico",
        kind="character",
        type="cat",
        label="calico kitten",
        traits=["calico", trait, "little"],
        meters={"pull": 0.0},
        memes={"friendship": 1.0, "warmth": 1.0},
    ))
    friend = world.add(Entity(
        id="Friend",
        kind="character",
        type="child",
        label="small friend",
        traits=["little", "kind"],
        meters={},
        memes={"friendship": 1.0, "warmth": 1.0},
    ))
    old_item = world.add(Entity(
        id="OldLink",
        kind="thing",
        type=rel.connector,
        label=f"old {rel.label}",
        phrase=rel.phrase,
        connected_to=friend.id,
        connector=rel.connector,
        meters={"pull": 0.0},
        memes={},
    ))

    world.say(
        f"In {setting.place}, a {trait} calico kitten named {hero_name} went patter, patter by."
    )
    world.say(
        f"{hero_name} loved the little play, and {friend_name} loved to stay nearby."
    )
    world.say(
        f"They held an old {rel.label} between them, bright as a thread in the sky."
    )

    world.para()
    world.say(
        f"Then {hero_name} tugged with a tiny hop, and the old {rel.label} gave a sigh."
    )
    _do_play(world, calico, rel)
    world.say(
        f"{friend_name} frowned, for the connection had slipped away and made them both feel shy."
    )
    calico.memes["hurt"] = 1.0
    friend.memes["hurt"] = 1.0

    world.para()
    world.say(
        f"But {hero_name} said, 'I'm sorry, dear friend, for the tug I did too spry.'"
    )
    friend.memes["sorry"] = 1.0
    calico.memes["sorry"] = 1.0
    world.say(
        f"{friend_name} said, 'I'll help you mend it now; we need not let it lie.'"
    )
    old_item.connected_to = friend.id
    old_item.meters["broken"] = 0.0
    calico.memes["warmth"] = 1.0
    friend.memes["warmth"] = 1.0
    world.say(
        f"They tied a neat {rel.fixed_with}, and the old {rel.label} sang low and sigh."
    )
    propagate(world, narrate=True)
    world.say(
        f"Then calico and friend went side by side, with friendship up on high."
    )

    world.facts.update(
        hero=calico,
        friend=friend,
        old_item=old_item,
        setting=setting,
        relationship=rel,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    rel: Relationship = f["relationship"]
    return [
        f'Write a short nursery-rhyme story about a calico kitten and a friend who mend an old {rel.keyword} connection.',
        f"Tell a gentle story where a calico helper causes a disconnect, then friendship and reconciliation bring things back together.",
        f"Write a rhyme-like story for a small child about an old broken link being fixed by two friends.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    rel: Relationship = f["relationship"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who was the calico kitten in the story?",
            answer=f"The calico kitten was {hero.id}, and {hero.pronoun('subject')} lived in {setting.place}.",
        ),
        QAItem(
            question=f"What old thing came loose when the friends played?",
            answer=f"An old {rel.label} came loose, and that made the two friends pause and look at each other.",
        ),
        QAItem(
            question=f"How did {friend.id} and the calico kitten feel at the end?",
            answer=f"They felt glad and close again, because they fixed the old link and chose friendship over fussing.",
        ),
        QAItem(
            question=f"What did they use to mend the broken connection?",
            answer=f"They used {rel.fixed_with} to mend the old {rel.label}, so it could stay together again.",
        ),
        QAItem(
            question=f"What changed after the reconciliation?",
            answer=f"After the reconciliation, the hurt feelings went away and the friends stood side by side once more.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    rel: Relationship = f["relationship"]
    out = [
        QAItem(
            question="What is a calico cat?",
            answer="A calico cat is a cat with a patchwork coat of different colors, often with orange, black, and white patches.",
        ),
        QAItem(
            question="What does disconnect mean?",
            answer="To disconnect means to come apart or stop being joined together.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind way of caring about someone, helping them, and liking to be with them.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making peace after a disagreement so people can be friends again.",
        ),
    ]
    if rel.keyword == "old":
        out.append(QAItem(
            question="What does old mean?",
            answer="Old means something has been around for a long time.",
        ))
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.connected_to is not None:
            bits.append(f"connected_to={e.connected_to}")
        if e.connector:
            bits.append(f"connector={e.connector}")
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(place="nursery", relationship="ribbon", name="Mimi", friend_name="Toby", trait="cheerful"),
    StoryParams(place="yard", relationship="string", name="Pip", friend_name="Bea", trait="playful"),
    StoryParams(place="porch", relationship="hook", name="Luna", friend_name="Milo", trait="gentle"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        RELATIONSHIPS[params.relationship],
        params.name,
        params.friend_name,
        params.trait,
    )
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


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def build_arg_parser() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible (place, relationship) combos:\n")
        for place, rel in combos:
            print(f"  {place:8} {rel}")
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
            header = f"### {p.name}: {p.relationship} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.relationship:
        combos = [c for c in combos if c[1] == args.relationship]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, relationship = rng.choice(combos)
    name = args.name or rng.choice(["Mimi", "Pip", "Luna", "Nia", "Dot"])
    friend_name = args.friend_name or rng.choice(["Toby", "Milo", "Bea", "Poppy", "Finn"])
    trait = args.trait or rng.choice(HERO_TRAITS)
    return StoryParams(place=place, relationship=relationship, name=name, friend_name=friend_name, trait=trait)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny nursery-rhyme storyworld about calico, disconnect, old, reconciliation, and friendship."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--relationship", choices=RELATIONSHIPS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--trait", choices=HERO_TRAITS)
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for rel_id in RELATIONSHIPS:
            combos.append((place, rel_id))
    return combos


if __name__ == "__main__":
    main()
