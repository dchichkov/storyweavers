#!/usr/bin/env python3
"""
A small story world for a mythic director tale with flashback and friendship.

The world premise:
A young director prepares a sacred performance for the village, but a broken
prop threatens the rite. The director remembers an old friend from an earlier
journey, and that memory changes what kind of help the director is willing to
accept. The story resolves when friendship, not pride, becomes the guiding force.

This script follows the Storyweavers world contract:
- typed entities with meters and memes
- state-driven narration
- explicit invalid options raise StoryError
- inline ASP twin plus Python reasonableness gate
- generate / emit / main / parser helpers
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

REGIONS = {"hands", "head", "heart", "voice"}


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
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["dust", "break", "fear", "repair"]:
            self.meters.setdefault(k, 0.0)
        for k in ["hope", "pride", "warmth", "memory", "trust", "joy", "lonely"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "queen", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "king", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the hill temple"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool = True
    repairable: bool = False
    plural: bool = False


@dataclass
class Aid:
    id: str
    label: str
    prep: str
    effect: str
    guards: set[str]
    regions: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

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
        w.facts = copy.deepcopy(self.facts)
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    place: str
    prop: str
    aid: str
    name: str
    friend_name: str
    seed: Optional[int] = None


SETTINGS = {
    "hill": Setting("the hill temple", False, {"chant", "drama"}),
    "courtyard": Setting("the temple courtyard", False, {"chant", "drama"}),
    "stage": Setting("the moonlit stage", False, {"chant", "drama"}),
}

PROPS = {
    "mask": Prop("mask", "sun mask", "a painted sun mask", "head", fragile=True, repairable=True),
    "drum": Prop("drum", "bronze drum", "a bronze drum with a cracked rim", "hands", fragile=True, repairable=True),
    "scroll": Prop("scroll", "song scroll", "a long song scroll tied with blue string", "hands", fragile=True, repairable=True),
}

AIDS = {
    "glue": Aid("glue", "pine glue", "use pine glue", "seal cracks", {"break"}, {"hands"}, False),
    "cord": Aid("cord", "silver cord", "bind it with silver cord", "hold it together", {"break"}, {"hands"}, False),
    "mask-cloth": Aid("mask-cloth", "soft cloth wrap", "wrap it in soft cloth", "protect the paint", {"dust", "break"}, {"head"}, False),
}

HERO_NAMES = ["Ari", "Mira", "Soren", "Lina", "Taro", "Nia"]
FRIEND_NAMES = ["Bela", "Oren", "Kaia", "Darin", "Yuna", "Pavel"]
TRAITS = ["patient", "bold", "gentle", "restless", "wise", "quiet"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for aid in setting.affords:
            for prop_id, prop in PROPS.items():
                if prop.region in {"hands", "head"} and aid in {"glue", "cord", "mask-cloth"}:
                    if prop_id == "mask" and aid == "mask-cloth":
                        combos.append((place, aid, prop_id))
                    elif prop_id in {"drum", "scroll"} and aid in {"glue", "cord"}:
                        combos.append((place, aid, prop_id))
    return combos


def reason_ok(aid: Aid, prop: Prop) -> bool:
    if prop.region not in aid.regions:
        return False
    if "break" not in aid.guards and prop.fragile:
        return False
    return True


def select_aid(prop: Prop) -> Optional[Aid]:
    for aid in AIDS.values():
        if reason_ok(aid, prop):
            return aid
    return None


def predict(world: World, hero: Entity, prop_id: str) -> dict:
    sim = world.copy()
    prop = sim.get(prop_id)
    prop.meters["break"] += 1
    return {"broken": prop.meters["break"] >= THRESHOLD}


def _rule_break(world: World) -> list[str]:
    out = []
    for prop in [e for e in world.entities.values() if e.kind == "prop"]:
        if prop.meters["break"] < THRESHOLD:
            continue
        sig = ("break", prop.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"The {prop.label} had cracked like a dry reed.")
    return out


def _rule_memory(world: World) -> list[str]:
    out = []
    hero = world.facts.get("hero")
    friend = world.facts.get("friend")
    if not hero or not friend:
        return out
    if hero.memes["memory"] >= THRESHOLD and ("memory", hero.id) not in world.fired:
        world.fired.add(("memory", hero.id))
        out.append(f"{hero.id} remembered the old road where {friend.id} once shared water and light.")
    return out


def _rule_friendship(world: World) -> list[str]:
    out = []
    hero = world.facts.get("hero")
    friend = world.facts.get("friend")
    if not hero or not friend:
        return out
    if hero.memes["trust"] >= THRESHOLD and friend.memes["warmth"] >= THRESHOLD:
        sig = ("friendship", hero.id, friend.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        out.append("The air itself seemed softer when they stood together.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_rule_break, _rule_memory, _rule_friendship):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "young"), "wise")
    world.say(f"{hero.id} was a young {trait} director who listened to the hush before every scene.")


def setup(world: World, hero: Entity, friend: Entity, prop: Entity) -> None:
    world.say(f"{hero.id} loved the old rites, and {hero.pronoun('possessive')} heart grew strong when a story was well told.")
    world.say(f"{friend.id} was {hero.id}'s oldest friend, the one who had once laughed with {hero.id} under rain and stars.")
    world.say(f"That season, the village gave {hero.id} {prop.phrase} for the sacred performance.")


def flashback(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["memory"] += 1
    hero.memes["lonely"] += 1
    world.say(f"Long before this night, {hero.id} had stumbled in fear at a stormy crossing.")
    world.say(f"Then {friend.id} had stayed beside {hero.id}, sharing bread, courage, and the path home.")
    friend.memes["warmth"] += 1
    hero.memes["trust"] += 1


def ask_for_help(world: World, hero: Entity, friend: Entity, prop: Entity, aid: Aid) -> None:
    hero.memes["pride"] += 1
    world.say(f"Now the {prop.label} cracked just as the moon rose, and {hero.id} feared the rite would fail.")
    world.say(f"{hero.id} wanted to fix it alone, but the crack spoke too loudly for pride.")
    if predict(world, hero, prop.id)["broken"]:
        world.say(f"{hero.id} turned to {friend.id} and asked for help before the damage could deepen.")


def accept_help(world: World, hero: Entity, friend: Entity, prop: Entity, aid: Aid) -> None:
    hero.memes["trust"] += 1
    friend.memes["warmth"] += 1
    prop.meters["repair"] += 1
    world.say(f"{friend.id} came at once and used {aid.label}, because old friendship knew the shape of trouble.")
    world.say(f"Together they {aid.effect} on the {prop.label}, and the crack began to close like a wound healed by song.")
    world.say(f"{hero.id} bowed not in shame, but in gratitude, and the rite could breathe again.")


def ending(world: World, hero: Entity, friend: Entity, prop: Entity) -> None:
    world.say(
        f"By dawn, {hero.id} led the performance beneath the brightening sky, "
        f"{prop.label} gleaming whole, while {friend.id} stood nearby like a steady star."
    )


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(params.name, kind="character", type="person", traits=["young", random.choice(TRAITS)]))
    friend = world.add(Entity(params.friend_name, kind="character", type="person", traits=["old", "kind"]))
    prop_cfg = PROPS[params.prop]
    prop = world.add(Entity(prop_cfg.id, kind="prop", type="prop", label=prop_cfg.label, phrase=prop_cfg.phrase, region=prop_cfg.region))
    aid = select_aid(prop_cfg)
    if aid is None:
        raise StoryError("No reasonable aid exists for this prop.")
    world.facts.update(hero=hero, friend=friend, prop=prop, aid=aid, setting=world.setting)

    introduce(world, hero)
    setup(world, hero, friend, prop)
    world.para()
    flashback(world, hero, friend)
    world.para()
    ask_for_help(world, hero, friend, prop, aid)
    accept_help(world, hero, friend, prop, aid)
    propagate(world, narrate=True)
    world.para()
    ending(world, hero, friend, prop)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, prop, aid = f["hero"], f["friend"], f["prop"], f["aid"]
    return [
        f'Write a short mythic story for a child about a director named {hero.id} who remembers a friendship from long ago.',
        f"Tell a gentle myth where {hero.id} faces a cracked {prop.label} and learns to accept help from {friend.id}.",
        f"Write a story with a flashback, friendship, and a sacred performance that ends with the {prop.label} repaired.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prop, aid = f["hero"], f["friend"], f["prop"], f["aid"]
    return [
        QAItem(
            question=f"Who was the director in the story?",
            answer=f"The director was {hero.id}, a young {hero.traits[-1]} guide of the sacred performance.",
        ),
        QAItem(
            question=f"Why did {hero.id} remember {friend.id} while the {prop.label} was broken?",
            answer=f"{hero.id} remembered how {friend.id} had helped during an older hard time, so the friendship gave {hero.id} courage.",
        ),
        QAItem(
            question=f"What did {friend.id} do to help with the {prop.label}?",
            answer=f"{friend.id} used {aid.label} and worked with {hero.id} to repair the {prop.label}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the {prop.label} repaired, the performance saved, and {hero.id} and {friend.id} standing together in trust.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a director?",
            answer="A director is a person who helps guide a performance so the people know what to do and when to do it.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a memory of something that happened earlier, told inside the present story.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and stay kind through trouble.",
        ),
        QAItem(
            question="Why do myths often feel big and ancient?",
            answer="Myths often use grand language, brave choices, and old memories so the story feels larger than one day.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"{e.id} [{e.kind}/{e.type}] meters={meters} memes={memes}")
    return "\n".join(out)


ASP_RULES = r"""
% A prop is at risk if the aid works on the same region.
risk(A,P) :- prop(P), aid(A), prop_region(P,R), aid_region(A,R).

% A compatible aid must also address breakage for fragile props.
fix(A,P) :- risk(A,P), prop_fragile(P), aid_guards(A,break).

valid(P,A) :- fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("prop_region", pid, p.region))
        if p.fragile:
            lines.append(asp.fact("prop_fragile", pid))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        for r in sorted(a.regions):
            lines.append(asp.fact("aid_region", aid, r))
        for g in sorted(a.guards):
            lines.append(asp.fact("aid_guards", aid, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set()
    for prop_id, prop in PROPS.items():
        aid = select_aid(prop)
        if aid is not None:
            py.add((prop_id, aid.id))
    ax = set(asp_valid())
    if py == ax:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - ax))
    print("asp-only:", sorted(ax - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic director story world with flashback and friendship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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
    if args.prop and args.place:
        prop = PROPS[args.prop]
        if select_aid(prop) is None:
            raise StoryError("That prop has no reasonable aid in this world.")
    place = args.place or rng.choice(list(SETTINGS))
    prop = args.prop or rng.choice(list(PROPS))
    name = args.name or rng.choice(HERO_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in FRIEND_NAMES if n != name])
    return StoryParams(place=place, prop=prop, aid="", name=name, friend_name=friend_name)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    f = world.facts
    params = StoryParams(params.place, params.prop, f["aid"].id, params.name, params.friend_name, params.seed)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(f"{len(asp_valid())} valid prop/aid pairs")
        for prop_id, aid_id in asp_valid():
            print(f"{prop_id} {aid_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, prop in enumerate(PROPS):
            params = StoryParams(place="hill", prop=prop, aid="", name=HERO_NAMES[i % len(HERO_NAMES)], friend_name=FRIEND_NAMES[i % len(FRIEND_NAMES)], seed=base_seed + i)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
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
