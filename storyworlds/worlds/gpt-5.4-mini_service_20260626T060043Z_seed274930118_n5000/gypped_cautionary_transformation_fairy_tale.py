#!/usr/bin/env python3
"""
storyworlds/worlds/gypped_cautionary_transformation_fairy_tale.py
==================================================================

A small fairy-tale story world about a tempting bargain, a gypped promise,
and a warning that arrives before a transformation gets too far.

Premise:
- A child or young traveler wants a lovely magical trinket.
- A stranger offers a bargain that sounds generous but is actually crooked.
- The bargain quietly raises a "gypped" feeling and a "transformed" danger.
- A wise helper spots the trick, breaks the spell, and the child changes back
  from the edge of the transformation.

This script keeps the world tiny on purpose: one classical cautionary tale,
with the state changes driving the prose rather than a frozen paragraph.
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
    keeper: Optional[str] = None
    worn_by: Optional[str] = None
    planted_in: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "princess"}
        male = {"boy", "father", "man", "king", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    light: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Temptation:
    id: str
    gift: str
    promise: str
    trick: str
    cost: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Talisman:
    id: str
    label: str
    phrase: str
    protects: str
    breaks: str
    risk: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_gypped(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.entities.values():
        if hero.kind != "character":
            continue
        if hero.memes.get("bewildered", 0.0) < THRESHOLD:
            continue
        if hero.memes.get("suspicion", 0.0) < THRESHOLD:
            continue
        sig = ("gypped", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["gypped"] = hero.memes.get("gypped", 0.0) + 1
        out.append(f"{hero.pronoun().capitalize()} felt gypped by the glittering promise.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.entities.values():
        if hero.kind != "character":
            continue
        if hero.memes.get("gypped", 0.0) < THRESHOLD:
            continue
        if hero.meters.get("curse", 0.0) < THRESHOLD:
            continue
        sig = ("transform", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.meters["transform"] = hero.meters.get("transform", 0.0) + 1
        out.append(f"A strange change began to run through {hero.pronoun('possessive')} bones.")
    return out


def _r_mend(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.entities.values():
        if hero.kind != "character":
            continue
        if hero.meters.get("curse", 0.0) < THRESHOLD:
            continue
        if hero.meters.get("shielded", 0.0) < THRESHOLD:
            continue
        sig = ("mend", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.meters["curse"] = 0.0
        hero.meters["transform"] = 0.0
        hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0.0) - 1)
        out.append(f"The old spell cracked and loosened like a knot in wet thread.")
    return out


CAUSAL_RULES = [
    Rule("gypped", _r_gypped),
    Rule("transform", _r_transform),
    Rule("mend", _r_mend),
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


def _do_temptation(world: World, hero: Entity, temptation: Temptation, narrate: bool = True) -> None:
    if temptation.id not in world.setting.affords:
        raise StoryError("That temptation does not belong in this setting.")
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    hero.memes["bewildered"] = hero.memes.get("bewildered", 0.0) + 1
    hero.memes["suspicion"] = hero.memes.get("suspicion", 0.0) + 1
    hero.meters["curse"] = hero.meters.get("curse", 0.0) + 1
    if narrate:
        world.say(
            f"A stranger offered {hero.pronoun('object')} {temptation.gift} and whispered "
            f'it would "{temptation.promise}".'
        )
        world.say(
            f"But the bargain had a crooked seam: it would {temptation.trick}, and the true cost was {temptation.cost}."
        )
    propagate(world, narrate=narrate)


def _do_warning(world: World, helper: Entity, hero: Entity, talisman: Talisman, narrate: bool = True) -> None:
    hero.meters["shielded"] = hero.meters.get("shielded", 0.0) + 1
    hero.memes["suspicion"] = hero.memes.get("suspicion", 0.0) + 1
    if narrate:
        world.say(
            f"{helper.pronoun().capitalize()} lifted a small {talisman.label} and said, "
            f'"Do not trust the shining thing that asks for your name."'
        )
        world.say(
            f'"A real charm {talisman.protects}, but that bargain only {talisman.breaks}."'
        )
    propagate(world, narrate=narrate)


def _do_resolution(world: World, hero: Entity, helper: Entity, talisman: Talisman, narrate: bool = True) -> None:
    if hero.meters.get("curse", 0.0) < THRESHOLD:
        return
    hero.meters["shielded"] = hero.meters.get("shielded", 0.0) + 1
    if narrate:
        world.say(
            f"{hero.id} flung the false gift into the stream and held the {talisman.label} tight."
        )
    propagate(world, narrate=narrate)
    if narrate:
        world.say(
            f"The glitter faded, {hero.id} breathed again, and {hero.pronoun('possessive')} hands and feet returned to their old shape."
        )


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "young"), "brave")
    world.say(
        f"{hero.id} was a young {trait} {hero.type} who lived in {world.setting.place}."
    )
    world.say(
        f"The days there were {world.setting.light} and {world.setting.mood}, and every path seemed to hold a secret."
    )


def desire(world: World, hero: Entity, temptation: Temptation) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(
        f"{hero.id} longed for the {temptation.keyword}, because it looked as lovely as moonlight on glass."
    )


def caution(world: World, helper: Entity, hero: Entity, talisman: Talisman) -> None:
    _do_warning(world, helper, hero, talisman, narrate=True)


def cautionary_turn(world: World, hero: Entity, temptation: Temptation) -> None:
    world.say(f"{hero.id} nearly accepted the offer, then remembered the warning too late.")
    _do_temptation(world, hero, temptation, narrate=True)


def ending(world: World, hero: Entity, helper: Entity) -> None:
    if hero.meters.get("transform", 0.0) >= THRESHOLD:
        world.say(
            f"That night, {hero.id} slept safely beside {helper.pronoun('object')}, wiser than before."
        )
    else:
        world.say(
            f"{hero.id} kept the lesson close and never again followed a smile that hid a hook."
        )


SETTINGS = {
    "forest": Setting(place="the whispering forest", light="green-gold", mood="still", affords={"mirrorflower"}),
    "cottage": Setting(place="the little cottage by the lane", light="soft", mood="cozy", affords={"mirrorflower"}),
    "river": Setting(place="the silver riverbank", light="bright", mood="windy", affords={"mirrorflower"}),
    "market": Setting(place="the old market square", light="busy", mood="noisy", affords={"mirrorflower"}),
}

TEMPTATIONS = {
    "mirrorflower": Temptation(
        id="mirrorflower",
        gift="a mirrorflower that sparkled like a tiny star",
        promise="make wishes come true",
        trick="steal the wish and leave only an empty smile",
        cost="a little bit of the hero's true shape",
        keyword="mirrorflower",
        tags={"gypped", "transform", "cautionary"},
    ),
}

TALISMANS = {
    "thorn": Talisman(
        id="thorn",
        label="silver thorn",
        phrase="a silver thorn from the old briar",
        protects="keeps a spell from settling on the skin",
        breaks="cannot be fooled by pretty lies",
        risk="false enchantment",
    ),
}

GIRL_NAMES = ["Elin", "Mara", "Tilda", "Nina", "Rosalind", "Wren", "Anya"]
BOY_NAMES = ["Hugo", "Perrin", "Rowan", "Bram", "Cedric", "Albie", "Finn"]
TRAITS = ["curious", "gentle", "stubborn", "bright-eyed", "hopeful", "careful"]


@dataclass
class StoryParams:
    place: str
    temptation: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="forest", temptation="mirrorflower", name="Elin", gender="girl", helper="grandmother", trait="curious"),
    StoryParams(place="cottage", temptation="mirrorflower", name="Hugo", gender="boy", helper="aunt", trait="hopeful"),
    StoryParams(place="river", temptation="mirrorflower", name="Mara", gender="girl", helper="sister", trait="careful"),
]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, tempt) for place in SETTINGS for tempt in TEMPTATIONS if tempt in SETTINGS[place].affords]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale cautionary transformation world with a gypped bargain.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["grandmother", "aunt", "sister"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.temptation is None or c[1] == args.temptation)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, temptation = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["grandmother", "aunt", "sister"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, temptation=temptation, name=name, gender=gender, helper=helper, trait=trait)


def tell(setting: Setting, temptation: Temptation, hero_name: str, hero_type: str, helper_kind: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["young", trait]))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_kind, label=helper_kind))
    talisman = world.add(Entity(id="talisman", type="talisman", label="silver thorn", phrase="a silver thorn"))
    world.facts.update(hero=hero, helper=helper, talisman=talisman, temptation=temptation, setting=setting)

    intro(world, hero)
    world.para()
    desire(world, hero, temptation)
    caution(world, helper, hero, TALISMANs["thorn"] if False else TALISMAN_BY_ID("thorn"))
    cautionary_turn(world, hero, temptation)
    world.para()
    _do_resolution(world, hero, helper, TALISMAN_BY_ID("thorn"), narrate=True)
    ending(world, hero, helper)
    return world


def TALISMAN_BY_ID(tid: str) -> Talisman:
    return TALISMANS[tid]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TEMPTATIONS[params.temptation], params.name, params.gender, params.helper, params.trait)
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
    hero = f["hero"]
    temptation = f["temptation"]
    return [
        f'Write a fairy tale for a young child about a {hero.type} who is nearly {temptation.cost} by a magical bargain.',
        f"Tell a cautionary transformation story in which {hero.id} meets a stranger offering {temptation.keyword}.",
        f'Write a gentle story that includes the word "gypped" and ends with a warning saving the day.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    temptation = f["temptation"]
    return [
        QAItem(
            question=f"What did {hero.id} almost accept in the story?",
            answer=f"{hero.id} almost accepted {temptation.gift}, but it was a crooked bargain that would gypped {hero.pronoun('object')} and steal part of {hero.pronoun('possessive')} true shape.",
        ),
        QAItem(
            question=f"Who warned {hero.id} about the trick?",
            answer=f"{helper.label_word.capitalize()} warned {hero.id} that the shining gift could hide a spell.",
        ),
        QAItem(
            question=f"What happened after {hero.id} threw away the false gift?",
            answer=f"The curse loosened, the transformation stopped, and {hero.id} returned to {hero.pronoun('possessive')} own shape.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does gypped mean in a cautionary story?",
            answer="Gypped means being cheated or tricked so that someone does not get the fair thing they were promised.",
        ),
        QAItem(
            question="What is a transformation in a fairy tale?",
            answer="A transformation is a big magical change, like turning a person partly into an animal or making them look different.",
        ),
    ]


ASP_RULES = r"""
tempted(H) :- wants(H, T), shiny(T).
gypped(H) :- tempted(H), warning_ignored(H).
transforming(H) :- gypped(H), cursed(H).
rescued(H) :- warned(H), shielded(H).
resolved(H) :- transforming(H), rescued(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for t in SETTINGS[sid].affords:
            lines.append(asp.fact("affords", sid, t))
    for tid in TEMPTATIONS:
        lines.append(asp.fact("temptation", tid))
    for tid in TALISMANS:
        lines.append(asp.fact("talisman", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1."))
    return sorted(set(asp.atoms(model, "setting")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_combos())
    python_set = {(place,) for place, setting in SETTINGS.items() for t in setting.affords if t in TEMPTATIONS}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("clingo:", sorted(clingo_set))
    print("python:", sorted(python_set))
    return 1


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
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
        print(asp_program("#show setting/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show setting/1."))
        print(sorted(set(asp.atoms(model, "setting"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
