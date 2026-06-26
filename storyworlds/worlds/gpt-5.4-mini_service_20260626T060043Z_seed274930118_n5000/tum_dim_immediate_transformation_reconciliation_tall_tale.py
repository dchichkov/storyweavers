#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tum_dim_immediate_transformation_reconciliation_tall_tale.py
==============================================================================================

A standalone tall-tale story world about a small, dim place where an immediate
transformation forces a fast reconciliation.

Seed image:
- In Tum-Dim, a boastful troublemaker and a patient helper both reach for a
  strange, bright talisman.
- The talisman works at once: a sour quarrel turns into a useful transformation.
- The ending shows a changed shape, a mended friendship, and a new shared job.

This script keeps the domain tight on purpose:
- a small cast
- one magical transformation
- one reconciliation
- a child-facing tall-tale tone with exaggerated but causal events
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    touched_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "group":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    dimness: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Power:
    id: str
    label: str
    transformation: str
    recoil: str
    requirement: str
    consequence: str


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    type: str
    cherished: bool = True


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.transformed: bool = False
        self.reconciled: bool = False

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.transformed = self.transformed
        w.reconciled = self.reconciled
        return w


@dataclass
class StoryParams:
    place: str
    hero: str
    rival: str
    gift: str
    power: str
    seed: Optional[int] = None


PLACES = {
    "tum_dim": Place(name="Tum-Dim", dimness="dim", affords={"transformation", "reconciliation"}),
}

POWERS = {
    "lantern": Power(
        id="lantern",
        label="old lantern",
        transformation="burst into a sun-bright lantern bird",
        recoil="flashed so bright that everybody had to blink",
        requirement="be touched at the same time by two quarrelers",
        consequence="forces a quick apology and a useful new shape",
    ),
    "hoop": Power(
        id="hoop",
        label="silver hoop",
        transformation="turn into a round bridge of shining iron",
        recoil="rang like a dinner bell across the hills",
        requirement="be held while two friends speak the truth",
        consequence="joins a split pair into one shared crossing",
    ),
}

GIFTS = {
    "bell": Gift(id="bell", label="tin bell", phrase="a tiny tin bell with a long blue string", type="bell"),
    "spoon": Gift(id="spoon", label="wooden spoon", phrase="a polished wooden spoon with a carved handle", type="spoon"),
}

HERO_NAMES = ["Mabel", "Jeb", "Hank", "Lula", "Clem", "Nell"]
RIVAL_NAMES = ["Rusty", "Ivy", "Boone", "Mina", "Otis", "Pearl"]
TRAITS = ["stout-hearted", "quick-footed", "big-voiced", "clever", "stubborn", "bright-eyed"]


def _metered(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def _memed(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def transform(world: World, hero: Entity, rival: Entity, power: Power, gift: Entity) -> None:
    if world.transformed:
        return
    if hero.meters.get("touch") < THRESHOLD or rival.meters.get("touch") < THRESHOLD:
        return
    sig = ("transform", power.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    world.transformed = True
    gift.type = "magical_creature" if power.id == "lantern" else "bridge"
    gift.label = "lantern bird" if power.id == "lantern" else "iron bridge"
    gift.phrase = f"the {gift.label}"
    hero.memes["astonishment"] = hero.memes.get("astonishment", 0) + 1
    rival.memes["astonishment"] = rival.memes.get("astonishment", 0) + 1


def reconcile(world: World, hero: Entity, rival: Entity) -> None:
    if world.reconciled:
        return
    if not world.transformed:
        return
    sig = ("reconcile", hero.id, rival.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    world.reconciled = True
    hero.memes["grudge"] = 0.0
    rival.memes["grudge"] = 0.0
    hero.memes["warmth"] = hero.memes.get("warmth", 0) + 1
    rival.memes["warmth"] = rival.memes.get("warmth", 0) + 1


def narrate_setup(world: World, hero: Entity, rival: Entity, gift: Entity, power: Power) -> None:
    world.say(
        f"In Tum-Dim, where the dusk always sat a little crooked over the chimneys, "
        f"there lived {hero.id}, a {hero.traits[0]} {hero.type}, and {rival.id}, a {rival.traits[0]} {rival.type}."
    )
    world.say(
        f"They both coveted {gift.phrase}, because every child in Tum-Dim knew it was the kind of thing that could "
        f"change a story without asking permission."
    )
    world.say(
        f"Old folks called {power.label} a wonder that would {power.consequence}, but only if it met {power.requirement}."
    )


def narrate_conflict(world: World, hero: Entity, rival: Entity, gift: Entity, power: Power) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    rival.memes["desire"] = rival.memes.get("desire", 0) + 1
    hero.memes["grudge"] = hero.memes.get("grudge", 0) + 1
    rival.memes["grudge"] = rival.memes.get("grudge", 0) + 1
    hero.meters["touch"] = 1
    rival.meters["touch"] = 1
    world.say(
        f"One evening, the two of them reached for it at once, and their hands bumped like two hammers in a tiny shed."
    )
    world.say(
        f"\"I saw it first,\" said {hero.id}. \"I held it first,\" said {rival.id}, and the dim street got dimmer with the fuss."
    )
    transform(world, hero, rival, power, gift)


def narrate_turn(world: World, hero: Entity, rival: Entity, gift: Entity, power: Power) -> None:
    if not world.transformed:
        raise StoryError("The transformation failed to happen; the premise needs both characters to touch the power.")
    world.para()
    world.say(
        f"Then, immediate as a blink, {power.label} sprang alive and {gift.label} took a new shape."
    )
    world.say(
        f"It flashed so hard that the whole lane went white for a heartbeat, and when the light slipped away, the wonder had changed."
    )
    world.say(
        f"Neither of them could keep quarreling and staring at the same time, so the grudge in their chests began to melt."
    )
    reconcile(world, hero, rival)


def narrate_resolution(world: World, hero: Entity, rival: Entity, gift: Entity, power: Power) -> None:
    if not world.reconciled:
        raise StoryError("The reconciliation did not resolve; the transformed world must lead to a mended relationship.")
    world.para()
    world.say(
        f"{hero.id} rubbed {hero.pronoun('possessive')} eyes, laughed, and said, \"Well, I'll be!\""
    )
    world.say(
        f"{rival.id} grinned back and answered, \"I'll share the road if you'll share the tale.\""
    )
    world.say(
        f"So they used the new {gift.label} together: if it was a bird, it carried their thanks over the rooftops; if it was a bridge, it carried their feet over the creek."
    )
    world.say(
        f"By sundown, Tum-Dim had one less quarrel and one more marvel, and the two rivals walked home side by side like old friends who had been baked in the same bright oven."
    )


def tell_story(place: Place, hero_name: str, rival_name: str, gift: Gift, power: Power, hero_trait: str, rival_trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy" if hero_name in {"Jeb", "Hank", "Clem"} else "girl", traits=[hero_trait, "stubborn"]))
    rival = world.add(Entity(id=rival_name, kind="character", type="boy" if rival_name in {"Boone", "Otis"} else "girl", traits=[rival_trait, "proud"]))
    relic = world.add(Entity(id="relic", kind="thing", type=gift.type, label=gift.label, phrase=gift.phrase, owner=None))

    world.facts.update(hero=hero, rival=rival, gift=relic, power=power, place=place)
    narrate_setup(world, hero, rival, relic, power)
    narrate_conflict(world, hero, rival, relic, power)
    narrate_turn(world, hero, rival, relic, power)
    narrate_resolution(world, hero, rival, relic, power)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    return [("tum_dim", "lantern", "bell"), ("tum_dim", "hoop", "spoon")]


@dataclass
class Registry:
    world: str
    power: str
    gift: str


REGISTRY = Registry(world="tum_dim", power="lantern", gift="bell")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: Tum-Dim, immediate transformation, reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--hero")
    ap.add_argument("--rival")
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
    place = args.place or "tum_dim"
    power = args.power or rng.choice(list(POWERS))
    gift = args.gift or ("bell" if power == "lantern" else "spoon")
    if (place, power, gift) not in valid_combos():
        raise StoryError("No valid Tum-Dim tale matches those choices; this world needs a real transformation and a real reconciliation.")
    hero = args.hero or rng.choice(HERO_NAMES)
    rival = args.rival or rng.choice([n for n in RIVAL_NAMES if n != hero])
    return StoryParams(place=place, hero=hero, rival=rival, gift=gift, power=power)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(
        PLACES[params.place],
        params.hero,
        params.rival,
        GIFTS[params.gift],
        POWERS[params.power],
        random.choice(TRAITS),
        random.choice(TRAITS),
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a tall tale about "Tum-Dim" where an immediate transformation ends a quarrel.',
        f"Tell a child-friendly story in which {f['hero'].id} and {f['rival'].id} both touch a magical object and the result changes at once.",
        "Write a short, homespun story with a dim town, a sudden wonder, and a friendship made whole again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    rival: Entity = f["rival"]
    gift: Entity = f["gift"]
    power: Power = f["power"]
    qa = [
        QAItem(
            question=f"Where does the story take place?",
            answer=f"It takes place in Tum-Dim, a dim little place where the streets seem to hold their breath before a wonder happens.",
        ),
        QAItem(
            question=f"What did {hero.id} and {rival.id} argue about?",
            answer=f"They argued about who got to hold {gift.phrase} first, because both of them wanted the same marvel at the same time.",
        ),
        QAItem(
            question=f"What happened when both children touched {power.label}?",
            answer=f"The change happened immediately: {gift.label} sprang into a new shape, and the quarrel could not keep standing after that bright shock.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {rival.id}?",
            answer=f"They reconciled, shared the transformed wonder, and walked home together like friends who had finally remembered the same song.",
        ),
    ]
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a transformation?",
            answer="A transformation is when something changes into a different form, like a plain thing becoming a magical one.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop fighting, make peace, and begin to treat each other kindly again.",
        ),
        QAItem(
            question="What makes a tall tale a tall tale?",
            answer="A tall tale is a story that tells of very big, wild happenings in a playful way, as if the world can stretch for a joke and a lesson.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
    out = ["--- world trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    out.append(f"transformed={world.transformed} reconciled={world.reconciled}")
    return "\n".join(out)


ASP_RULES = r"""
place(tum_dim).
power(lantern).
power(hoop).
gift(bell).
gift(spoon).

compatible(tum_dim, lantern, bell).
compatible(tum_dim, hoop, spoon).

#show compatible/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for p in POWERS:
        lines.append(asp.fact("power", p))
    for g in GIFTS:
        lines.append(asp.fact("gift", g))
    for place, power, gift in valid_combos():
        lines.append(asp.fact("compatible", place, power, gift))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
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


CURATED = [
    StoryParams(place="tum_dim", hero="Mabel", rival="Boone", gift="bell", power="lantern"),
    StoryParams(place="tum_dim", hero="Jeb", rival="Ivy", gift="spoon", power="hoop"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show compatible/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
