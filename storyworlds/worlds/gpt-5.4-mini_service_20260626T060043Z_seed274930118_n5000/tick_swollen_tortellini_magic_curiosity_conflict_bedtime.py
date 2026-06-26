#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tick_swollen_tortellini_magic_curiosity_conflict_bedtime.py
===============================================================================================================================

A small bedtime-story world about a curious child, a little bit of magic, and
a dinner-table conflict that settles softly before sleep.

Seed tale:
---
At bedtime, a curious child found a bowl of tortellini that had gone a little
swollen after the pot was touched by magic. Every tick of the little kitchen
clock made the noodles wobble and glow. The child wanted one more taste, but a
parent worried the magic might make the child's tummy ache. After a gentle
conversation, they used the magic to cool the bowl, saved the rest for morning,
and the child fell asleep feeling safe and full.

World model:
---
- meters: physical amounts and conditions like heat, fullness, swelling, glow
- memes: feelings like curiosity, comfort, conflict, trust

This world is intentionally tiny and constraint-checked: the magic only creates
a reasonable bedtime problem when the child is curious, the food is swollen, and
the parent can offer a calm fix.
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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
    bedtime: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    warmth: str
    swelling: str
    glow: str
    tasty: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.clock_ticks: int = 0
        self.magic: bool = False

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.clock_ticks = self.clock_ticks
        clone.magic = self.magic
        return clone


@dataclass
class Rule:
    name: str
    apply


def _rule_warm_swelling(world: World) -> list[str]:
    out: list[str] = []
    for treat in world.entities.values():
        if treat.type != "food":
            continue
        if treat.meters.get("warm", 0.0) < THRESHOLD:
            continue
        sig = ("warm_swelling", treat.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        treat.meters["swollen"] = treat.meters.get("swollen", 0.0) + 1
        out.append(f"The {treat.label} puffed up a little more.")
    return out


def _rule_magic_glow(world: World) -> list[str]:
    out: list[str] = []
    if not world.magic:
        return out
    for treat in world.entities.values():
        if treat.type != "food":
            continue
        sig = ("magic_glow", treat.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        treat.meters["glow"] = treat.meters.get("glow", 0.0) + 1
        out.append(f"A soft shimmer moved over the bowl.")
    return out


def _rule_curious_conflict(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.characters() if e.type in {"girl", "boy"}), None)
    parent = next((e for e in world.characters() if e.type in {"mother", "father"}), None)
    treat = next((e for e in world.entities.values() if e.type == "food"), None)
    if not child or not parent or not treat:
        return out
    if child.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    if treat.meters.get("swollen", 0.0) < THRESHOLD:
        return out
    sig = ("conflict", child.id, treat.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["conflict"] = child.memes.get("conflict", 0.0) + 1
    parent.memes["worry"] = parent.memes.get("worry", 0.0) + 1
    out.append(f"{child.id} wanted one more taste, and {parent.id} worried softly.")
    return out


CAUSAL_RULES = [
    Rule("warm_swelling", _rule_warm_swelling),
    Rule("magic_glow", _rule_magic_glow),
    Rule("curious_conflict", _rule_curious_conflict),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    place: str
    treat: str
    hero_name: str
    hero_gender: str
    parent_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen", bedtime=True, affords={"tortellini"}),
    "table": Setting(place="the little table", bedtime=True, affords={"tortellini"}),
}

TREATS = {
    "tortellini": Treat(
        id="tortellini",
        label="tortellini",
        phrase="a warm bowl of tortellini",
        warmth="warm",
        swelling="swollen",
        glow="glowing",
        tasty="tasty",
        keyword="tortellini",
        tags={"tortellini", "magic", "swollen"},
    ),
}

FIXES = [
    Fix(
        id="cooling_spell",
        label="a cooling spell",
        prep="close the lid and whisper a cooling spell",
        tail="waited for the noodles to rest",
        guards={"heat", "swelling", "glow"},
    ),
    Fix(
        id="save_for_morning",
        label="a bedtime cover",
        prep="cover the bowl and save the rest for morning",
        tail="set the bowl on the counter for breakfast",
        guards={"swelling", "glow"},
    ),
]

NAMES_GIRL = ["Mina", "Lily", "Nora", "Ivy", "Ella"]
NAMES_BOY = ["Theo", "Ben", "Finn", "Leo", "Owen"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: magic, curiosity, and a gentle conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def reasonableness_gate(place: str, treat: str) -> bool:
    return place in SETTINGS and treat in TREATS


def select_fix(treat: Treat) -> Optional[Fix]:
    for fx in FIXES:
        if "swelling" in fx.guards:
            return fx
    return None


def tell(setting: Setting, treat: Treat, hero_name: str, hero_gender: str, parent_gender: str) -> World:
    world = World(setting)
    world.magic = True
    child = world.add(Entity(id=hero_name, kind="character", type=hero_gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_gender))
    bowl = world.add(Entity(id=treat.id, kind="thing", type="food", label="tortellini", phrase=treat.phrase))
    bowl.meters["warm"] = 1
    bowl.meters["swollen"] = 1
    bowl.meters["glow"] = 1
    child.memes["curiosity"] = 1
    child.memes["comfort"] = 0
    child.memes["conflict"] = 0
    parent.memes["worry"] = 0

    world.say(f"At bedtime, {child.id} sat by {setting.place} and watched the {bowl.label} tick with tiny magic.")
    world.say(f"The little bowl held {treat.phrase}, and the noodles looked swollen and bright.")
    world.para()
    world.say(f"{child.id} leaned closer, because curiosity made {child.pronoun('object')} wonder how magic tasted.")
    world.say(f"{child.id} wanted one more bite, but {parent.pronoun().capitalize()} saw the swollen tortellini and grew careful.")
    propagate(world, narrate=True)
    world.para()

    parent = world.get("Parent")
    if child.memes.get("conflict", 0) >= THRESHOLD:
        world.say(f'"Let\'s be gentle," {parent.pronoun("subject").capitalize()} said. "Magic can wait until morning."')
        fix = select_fix(treat)
        if fix is None:
            raise StoryError("No reasonable bedtime fix for this treat.")
        world.say(f"Together they {fix.prep}, and the kitchen grew quiet.")
        child.memes["curiosity"] = 0
        child.memes["comfort"] = 1
        child.memes["conflict"] = 0
        parent.memes["worry"] = 0
        world.say(f"Then {fix.tail}. The magic settled, the tortellini stayed safe, and {child.id} felt sleepy and snug.")
        world.say(f"At last, {child.id} climbed into bed with a full heart and a calm tummy.")
    else:
        world.say(f"{child.id} smiled, and the sleepy kitchen stayed peaceful.")

    world.facts.update(
        child=child,
        parent=parent,
        bowl=bowl,
        setting=setting,
        treat=treat,
        fix=select_fix(treat),
        conflict=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    treat = f["treat"]
    return [
        f'Write a bedtime story for a small child about {child.id}, a magic bowl of {treat.keyword}, and a gentle conflict.',
        f"Tell a quiet story where curiosity makes {child.id} lean toward swollen tortellini, but a parent helps choose the safe way.",
        f'Write a cozy story that includes the words "tick", "swollen", and "{treat.keyword}", and ends with sleep and comfort.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    bowl = f["bowl"]
    fix = f["fix"]
    return [
        QAItem(
            question=f"Why did {child.id} lean closer to the bowl at bedtime?",
            answer=f"{child.id} was curious about the magic and wanted to taste the tortellini.",
        ),
        QAItem(
            question=f"Why was the parent careful about the swollen tortellini?",
            answer=f"The parent saw that the tortellini was swollen and did not want bedtime magic to upset {child.pronoun('possessive')} tummy.",
        ),
        QAItem(
            question=f"What did they do so the tortellini could stay safe until morning?",
            answer=f"They used {fix.label if fix else 'a gentle fix'} and saved the bowl for morning.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does tortellini mean?",
            answer="Tortellini are small stuffed pasta shapes, often served in a warm bowl.",
        ),
        QAItem(
            question="What does swollen mean?",
            answer="Swollen means puffed up or bigger than usual.",
        ),
        QAItem(
            question="What can magic do in a bedtime story?",
            answer="Magic can make ordinary things glow, move, or change in a gentle way.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={e.meters}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  clock_ticks={world.clock_ticks}")
    lines.append(f"  magic={world.magic}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
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


ASP_RULES = r"""
swollen(T) :- treat(T), warm(T), magic(T).
conflict(C,T) :- child(C), curious(C), swollen(T), parent(P), worries(P,T).
valid_story(P,T) :- place(P), affords(P,T), treat(T), swollen(T), has_fix(T).
has_fix(T) :- fix(F), guards(F, swelling), treat(T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.bedtime:
            lines.append(asp.fact("bedtime", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat", tid))
        lines.append(asp.fact("warm", tid))
        lines.append(asp.fact("magic", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact(tag, tid))
    for i, fx in enumerate(FIXES):
        lines.append(asp.fact("fix", fx.id))
        for g in sorted(fx.guards):
            lines.append(asp.fact("guards", fx.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2.\n#show conflict/2.\n"))
    facts = set(asp.atoms(model, "valid_story"))
    python_ok = {(p, t) for p in SETTINGS for t in TREATS if reasonableness_gate(p, t)}
    if facts:
        print(f"OK: ASP produced {len(facts)} valid_story atoms.")
        return 0
    print("MISMATCH: ASP produced no valid_story atoms.")
    print("python candidates:", sorted(python_ok))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.treat and not reasonableness_gate(args.place, args.treat):
        raise StoryError("That place cannot host that bedtime treat.")
    places = [args.place] if args.place else list(SETTINGS)
    treats = [args.treat] if args.treat else list(TREATS)
    combos = [(p, t) for p in places for t in treats if reasonableness_gate(p, t)]
    if not combos:
        raise StoryError("No valid bedtime story matches the given options.")
    place, treat = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, treat=treat, hero_name=name, hero_gender=gender, parent_gender=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TREATS[params.treat], params.hero_name, params.hero_gender, params.parent_gender)
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


CURATED = [
    StoryParams(place="kitchen", treat="tortellini", hero_name="Mina", hero_gender="girl", parent_gender="mother"),
    StoryParams(place="table", treat="tortellini", hero_name="Theo", hero_gender="boy", parent_gender="father"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/2.\n"))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(vals)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
