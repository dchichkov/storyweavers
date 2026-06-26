#!/usr/bin/env python3
"""
Standalone storyworld: specter + surgical + friendship in a bedtime-story tone.

A small child-friendly world about a sleepy house, a shy specter friend, and a
careful fix that feels more like kindness than fright.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

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
    place: str = "the little house"
    bedtime: bool = True


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Fix:
    id: str
    label: str
    covers: set[str]
    tool: str
    action: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    item: str
    fix: str
    name: str
    gender: str
    friend_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.events: list[str] = []

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
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "house": Setting(place="the little house", bedtime=True),
    "nursery": Setting(place="the nursery", bedtime=True),
    "attic": Setting(place="the attic room", bedtime=True),
}

ITEMS = {
    "lantern": Thing(
        id="lantern",
        label="lantern",
        phrase="a tiny lantern with a warm glass door",
        region="hand",
    ),
    "blanket": Thing(
        id="blanket",
        label="blanket",
        phrase="a soft bedtime blanket",
        region="shoulders",
    ),
    "crown": Thing(
        id="crown",
        label="paper crown",
        phrase="a glittery paper crown",
        region="head",
    ),
}

FIXES = {
    "stitch": Fix(
        id="stitch",
        label="surgical stitches",
        covers={"hand"},
        tool="needle",
        action="carefully stitch up the tear",
    ),
    "wrap": Fix(
        id="wrap",
        label="a gentle wrap",
        covers={"shoulders"},
        tool="soft cloth",
        action="wrap it warm and snug",
    ),
    "tape": Fix(
        id="tape",
        label="a careful tape patch",
        covers={"head"},
        tool="paper tape",
        action="patch the bent edge",
    ),
}

GENDERS = ["girl", "boy"]
NAMES = ["Maya", "Nora", "Liam", "Eli", "Sana", "Theo", "Iris", "Noah"]
FRIENDS = ["Pip", "Juno", "Toby", "Milo", "Luna", "Rae", "Bea", "Finn"]
TRAITS = ["gentle", "sleepy", "kind", "curious", "brave"]


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------

def item_at_risk(item: Thing, fix: Fix) -> bool:
    return item.region in fix.covers


def select_fix(item: Thing) -> Optional[Fix]:
    for fx in FIXES.values():
        if item_at_risk(item, fx):
            return fx
    return None


def explain_rejection(item: Thing, fix: Fix) -> str:
    return (
        f"(No story: {fix.label} would not honestly help a {item.label}. "
        f"The at-risk part is the {item.region}, but this fix covers "
        f"{sorted(fix.covers)}.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def intro_line(hero: Entity, friend: Entity) -> str:
    return (
        f"{hero.id} was a little {next((t for t in hero.traits if t != 'little'), 'kind')} "
        f"{hero.type} who liked quiet nights. "
        f"{friend.id} was a shy specter who liked being near friends more than being spooky."
    )


def bedtime_line(world: World) -> str:
    return f"At bedtime, {world.setting.place} felt soft and still, with moonlight on the walls."


def friendship_line(hero: Entity, friend: Entity) -> str:
    return (
        f"{hero.id} and {friend.id} had a small friendship that made the room feel less dark. "
        f"They shared whispers, pillow corners, and careful smiles."
    )


def need_line(hero: Entity, item: Entity) -> str:
    return (
        f"{hero.id} loved {item.phrase}, but one little tear and one bent edge made everyone worry."
    )


def problem_line(hero: Entity, friend: Entity, item: Entity) -> str:
    return (
        f"That night, {friend.id} noticed {hero.id}'s {item.label} was too fragile for sleep and play. "
        f"The little specter held up {friend.pronoun('possessive')} glowing hands and blinked sadly."
    )


def fix_line(hero: Entity, friend: Entity, item: Entity, fix: Fix) -> str:
    return (
        f"Then {hero.id} got the idea to use {fix.label}. "
        f"{friend.id} helped {fix.action}, and the room felt brave and tidy again."
    )


def ending_line(hero: Entity, friend: Entity, item: Entity) -> str:
    return (
        f"After that, {item.label} rested safely by the pillow, {hero.id} yawned, and "
        f"{friend.id} floated beside the bed like a tiny moonbeam. "
        f"Friendship made the whole night feel warm."
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
item_at_risk(I,F) :- item(I), fix(F), region(I,R), covers(F,R).
has_fix(I) :- item_at_risk(I,F).
valid_story(P,I,F,G) :- place(P), item(I), fix(F), gender(G), item_at_risk(I,F), has_fix(I), wears(G,I).
"""

def asp_facts() -> str:
    import asp
    out = []
    for pid in SETTINGS:
        out.append(asp.fact("place", pid))
    for iid, item in ITEMS.items():
        out.append(asp.fact("item", iid))
        out.append(asp.fact("region", iid, item.region))
        if item.plural:
            out.append(asp.fact("item_plural", iid))
        for g in GENDERS:
            out.append(asp.fact("wears", g, iid))
    for fid, fx in FIXES.items():
        out.append(asp.fact("fix", fid))
        for r in sorted(fx.covers):
            out.append(asp.fact("covers", fid, r))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    import asp
    cl = set(asp.atoms(asp.one_model(asp_program("#show valid_story/4. | #show valid/3.")), "valid_story"))
    if py == {(p, i, f, g) for (p, i, f, g) in cl}:
        print(f"OK: ASP matches Python ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("python-only:", sorted(py - {(p, i, f, g) for (p, i, f, g) in cl}))
    print("asp-only:", sorted({(p, i, f, g) for (p, i, f, g) in cl} - py))
    return 1


# ---------------------------------------------------------------------------
# Story building
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in SETTINGS:
        for item_id, item in ITEMS.items():
            fx = select_fix(item)
            if not fx:
                continue
            for g in GENDERS:
                combos.append((place, item_id, fx.id, g))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime storyworld about a specter, surgical care, and friendship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=GENDERS)
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
    if args.item and args.fix:
        item = ITEMS[args.item]
        fix = FIXES[args.fix]
        if not item_at_risk(item, fix):
            raise StoryError(explain_rejection(item, fix))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.fix is None or c[2] == args.fix)
              and (args.gender is None or c[3] == args.gender)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item_id, fix_id, gender = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    friend_name = args.friend_name or rng.choice([n for n in FRIENDS if n != name])
    return StoryParams(place=place, item=item_id, fix=fix_id, name=name, gender=gender, friend_name=friend_name)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", rng_trait(params.seed)]))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="specter", label="specter", traits=["shy", "kind"]))
    item = world.add(Entity(id="item", type=ITEMS[params.item].label, label=ITEMS[params.item].label, phrase=ITEMS[params.item].phrase, owner=hero.id, caretaker=hero.id, region=ITEMS[params.item].region))
    fix = FIXES[params.fix]

    hero.memes["friendship"] = 1.0
    friend.memes["friendship"] = 1.0
    world.say(intro_line(hero, friend))
    world.say(friendship_line(hero, friend))
    world.para()
    world.say(bedtime_line(world))
    world.say(need_line(hero, item))
    world.say(problem_line(hero, friend, item))
    world.para()
    world.say(fix_line(hero, friend, item, fix))
    world.say(ending_line(hero, friend, item))

    world.facts.update(hero=hero, friend=friend, item=item, fix=fix, params=params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def rng_trait(seed: Optional[int]) -> str:
    r = random.Random(seed)
    return r.choice(TRAITS)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item"]
    fix = f["fix"]
    return [
        f'Write a gentle bedtime story about a specter friend who helps {hero.id} with {item.label}.',
        f'Tell a child-friendly story where friendship leads to using {fix.label} to care for a fragile {item.label}.',
        f'Write a sleepy, warm story with a specter, a small problem, and a kind fix at bedtime.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item"]
    fix = f["fix"]
    return [
        QAItem(
            question=f"Who was the sleepy child in the story?",
            answer=f"The sleepy child was {hero.id}.",
        ),
        QAItem(
            question=f"Who was the specter friend?",
            answer=f"The specter friend was {friend.id}, who was shy but kind.",
        ),
        QAItem(
            question=f"What was wrong with the {item.label}?",
            answer=f"It had a little problem and needed careful help before bedtime.",
        ),
        QAItem(
            question=f"How did they fix the {item.label}?",
            answer=f"They used {fix.label} and worked together gently, so it could be safe again.",
        ),
        QAItem(
            question=f"What helped the story end happily?",
            answer="Friendship helped. The child and the specter stayed kind to each other while they fixed the small problem.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a specter?",
            answer="In this story, a specter is a gentle ghost-like friend who can float and glow softly.",
        ),
        QAItem(
            question="What does surgical mean?",
            answer="Surgical means careful and precise, the way a grown-up doctor or helper might make a tiny neat fix.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and feel safer together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.region:
            bits.append(f"region={e.region}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories:")
        for s in stories:
            print(" ", s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, item, fix, gender in valid_combos():
            params = StoryParams(place=place, item=item, fix=fix, name="Maya", gender=gender, friend_name="Specter")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
