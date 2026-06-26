#!/usr/bin/env python3
"""
storyworlds/worlds/liar_misunderstanding_superhero_story.py
===========================================================

A small superhero storyworld about a brave kid hero, a liar, and a
misunderstanding that gets fixed by showing the truth.

Premise:
- A young superhero loves helping around the city.
- A sneaky liar tells a false story about the hero.
- A misunderstanding spreads fast because people want to believe the lie.

Turn:
- The hero uses a simple rescue, a visible clue, or a helper's witness to prove
  what really happened.

Resolution:
- The liar is exposed, the misunderstanding clears, and the hero ends the day
  trusted again.

This world is intentionally small and constraint-driven. It generates only
stories where the misunderstanding is plausible and the resolution is earned by
a concrete, world-state change.
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
    knows_truth: bool = False
    trusted: bool = False
    visible_clue: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def name_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    scene: str
    false_claim: str
    real_event: str
    clue: str
    spread: str
    cleared_by: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Proof:
    id: str
    label: str
    phrase: str
    explains: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trust_broken: bool = False
        self.misunderstanding: bool = False
        self.cleared: bool = False

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
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.trust_broken = self.trust_broken
        clone.misunderstanding = self.misunderstanding
        clone.cleared = self.cleared
        return clone


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    liar = world.get("liar")
    crowd = world.get("crowd")
    if hero.memes.get("rumor", 0.0) < THRESHOLD:
        return out
    if world.misunderstanding:
        return out
    sig = ("misunderstanding",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.misunderstanding = True
    crowd.memes["confused"] = 1.0
    crowd.memes["doubt"] = 1.0
    out.append(
        f"The people looked at {hero.name_word} and the liar's story felt true enough to worry them."
    )
    return out


def _r_expose(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    liar = world.get("liar")
    proof = world.get("proof")
    if world.cleared:
        return out
    if hero.meters.get("proof", 0.0) < THRESHOLD:
        return out
    if not world.misunderstanding:
        return out
    sig = ("expose",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.cleared = True
    liar.memes["shame"] = liar.memes.get("shame", 0.0) + 1.0
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1.0
    out.append(f"The clue at last matched {proof.label}, and the liar could not keep the false story alive.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_misunderstanding, _r_expose):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combo(setting: Setting, trouble: Trouble, proof: Proof) -> bool:
    return trouble.id in setting.affords and trouble.id in proof.tags


def build_story(hero_name: str, hero_type: str, helper_type: str, setting: Setting,
                trouble: Trouble, proof: Proof) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        traits=["brave", "helpful"],
        knows_truth=True,
        trusted=True,
    ))
    liar = world.add(Entity(
        id="liar",
        kind="character",
        type="person",
        label="the liar",
        traits=["sly", "noisy"],
        knows_truth=False,
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label="the helper",
        traits=["careful", "fair"],
        knows_truth=True,
        trusted=True,
    ))
    crowd = world.add(Entity(
        id="crowd",
        kind="character",
        type="people",
        label="the crowd",
        traits=["curious"],
        knows_truth=False,
    ))
    proof_ent = world.add(Entity(
        id="proof",
        kind="thing",
        type="clue",
        label=proof.label,
        phrase=proof.phrase,
        visible_clue=proof.explains,
    ))
    world.facts.update(hero=hero, liar=liar, helper=helper, crowd=crowd,
                       proof=proof_ent, trouble=trouble, setting=setting)

    world.say(
        f"{hero.name_word} was a small superhero who loved helping in {setting.place}."
    )
    world.say(
        f"One day, {trouble.scene}. {hero.name_word} wanted to help, but {liar.name_word} told a fake story: {trouble.false_claim}"
    )
    hero.memes["sad"] = 1.0
    hero.memes["worry"] = 1.0
    hero.memes["rumor"] = 1.0
    world.trust_broken = True
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{hero.name_word} did not shout back. {helper.name_word} stayed close and said the liar should be checked against the real clue."
    )
    world.say(
        f"Then {hero.name_word} did the careful thing that matched the truth: {trouble.real_event}"
    )
    hero.meters["proof"] = 1.0
    proof_ent.meters["proof"] = 1.0
    world.say(
        f"That showed {proof.label} in the open, and it meant {proof.explains}"
    )
    propagate(world, narrate=True)

    world.para()
    if world.cleared:
        crowd.trusted = True
        world.say(
            f"At last, everyone understood the misunderstanding. {liar.name_word} had to admit the lie, and {hero.name_word} went home as the city's trusted hero."
        )
    else:
        raise StoryError("the story did not reach a clear resolution")

    return world


SETTINGS = {
    "rooftop": Setting(place="the rooftop", affords={"alarm"}),
    "plaza": Setting(place="the plaza", affords={"alarm"}),
    "train_station": Setting(place="the train station", affords={"alarm"}),
    "museum": Setting(place="the museum steps", affords={"alarm"}),
}

TROUBLES = {
    "stolen_alarm": Trouble(
        id="alarm",
        scene="the city alarm suddenly rang from the rooftop",
        false_claim="that the hero had set off the alarm on purpose",
        real_event="the hero had pulled a cat out of the broken sign before the alarm rang",
        clue="a bent sign hook and a rescued cat",
        spread="people thought the hero was careless",
        cleared_by="the rescue happened first",
        tags={"alarm"},
    ),
    "spilled_paint": Trouble(
        id="alarm",
        scene="bright paint splashed across the museum steps",
        false_claim="that the hero made the mess and ran away",
        real_event="the hero had blocked the spill from reaching a baby stroller",
        clue="paint on the hero's gloves from the stroller shield",
        spread="people thought the hero was clumsy",
        cleared_by="the shielded stroller was seen",
        tags={"alarm"},
    ),
    "broken_lamp": Trouble(
        id="alarm",
        scene="a lamp cracked in the plaza during the crowd rush",
        false_claim="that the hero broke it while showing off",
        real_event="the hero had caught the falling lamp before it hit anyone",
        clue="a dented glove and a saved child scarf",
        spread="people thought the hero was reckless",
        cleared_by="the saved scarf was found",
        tags={"alarm"},
    ),
}

PROOFS = {
    "cat": Proof(
        id="cat",
        label="the rescued cat",
        phrase="a rescued cat under the sign",
        explains="the hero was busy saving someone, not causing trouble",
        tags={"alarm"},
    ),
    "stroller": Proof(
        id="stroller",
        label="the shielded stroller",
        phrase="a stroller with a clean cover",
        explains="the hero had blocked the spill on purpose to help",
        tags={"alarm"},
    ),
    "scarf": Proof(
        id="scarf",
        label="the saved scarf",
        phrase="a child scarf caught before it fell",
        explains="the hero stopped the danger before it hurt anyone",
        tags={"alarm"},
    ),
}

HERO_NAMES = ["Nina", "Leo", "Maya", "Eli", "Zoe", "Ava", "Noah", "Ivy"]
HELPER_TYPES = ["captain", "reporter", "nurse", "guard", "robot"]


@dataclass
class StoryParams:
    place: str
    trouble: str
    proof: str
    name: str
    hero_type: str
    helper_type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero storyworld about a liar and a misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--proof", choices=PROOFS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
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
    if args.place and args.trouble and args.proof:
        if not valid_combo(SETTINGS[args.place], TROUBLES[args.trouble], PROOFS[args.proof]):
            raise StoryError("that place, trouble, and proof do not fit together")
    combos = [
        (p, t, pr)
        for p in SETTINGS
        for t in TROUBLES
        for pr in PROOFS
        if valid_combo(SETTINGS[p], TROUBLES[t], PROOFS[pr])
        and (args.place is None or args.place == p)
        and (args.trouble is None or args.trouble == t)
        and (args.proof is None or args.proof == pr)
    ]
    if not combos:
        raise StoryError("no valid story matches those choices")
    place, trouble, proof = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    return StoryParams(place=place, trouble=trouble, proof=proof, name=name, hero_type=hero_type, helper_type=helper_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a child about a liar and a misunderstanding at {f["setting"].place}.',
        f"Tell a gentle story where {f['hero'].label} must clear up a false claim from {f['liar'].name_word}.",
        f"Write a simple story where a hero proves the truth with {f['proof'].label} and the crowd learns what really happened.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    liar = f["liar"]
    helper = f["helper"]
    proof = f["proof"]
    trouble = f["trouble"]
    return [
        QAItem(
            question=f"Why did people misunderstand {hero.label}?",
            answer=f"They heard {liar.name_word}'s false story and did not know the real event yet.",
        ),
        QAItem(
            question=f"What did {helper.name_word} do when the liar spread the false claim?",
            answer=f"{helper.name_word.capitalize()} stayed close to {hero.label} and said the story should be checked against the real clue.",
        ),
        QAItem(
            question=f"How was the misunderstanding fixed in the story?",
            answer=f"{hero.label} showed the truth by doing the real event: {trouble.real_event}. That matched {proof.label} and exposed the lie.",
        ),
        QAItem(
            question=f"How did the story end for {hero.label}?",
            answer=f"{hero.label} ended the day trusted again after everyone understood the liar had told a false story.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a liar?",
            answer="A liar is a person who says something that is not true.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people believe the wrong idea because they do not have the full truth.",
        ),
        QAItem(
            question="What does a superhero do?",
            answer="A superhero helps people, protects others, and tries to do the right thing.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.knows_truth:
            bits.append("knows_truth=True")
        if e.trusted:
            bits.append("trusted=True")
        if e.visible_clue:
            bits.append(f"clue={e.visible_clue!r}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  misunderstanding={world.misunderstanding} cleared={world.cleared}")
    return "\n".join(lines)


ASP_RULES = r"""
misunderstanding :- rumor(hero), false_claim(liar), not cleared.
cleared :- proof_seen(hero), truth_matches(proof), rumor(hero).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("rumor", "hero"),
        asp.fact("false_claim", "liar"),
        asp.fact("truth_matches", "proof"),
        asp.fact("proof_seen", "hero"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show misunderstanding/0.\n#show cleared/0."))
    atoms = {sym.name for sym in model}
    expected = {"misunderstanding", "cleared"}
    if atoms >= expected:
        print("OK: ASP twin reaches misunderstanding and clearing facts.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected atoms.")
    return 1


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    trouble = TROUBLES[params.trouble]
    proof = PROOFS[params.proof]
    world = build_story(params.name, params.hero_type, params.helper_type, setting, trouble, proof)
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
    StoryParams(place="rooftop", trouble="stolen_alarm", proof="cat", name="Nina", hero_type="girl", helper_type="reporter"),
    StoryParams(place="plaza", trouble="broken_lamp", proof="scarf", name="Leo", hero_type="boy", helper_type="guard"),
    StoryParams(place="museum", trouble="spilled_paint", proof="stroller", name="Maya", hero_type="girl", helper_type="nurse"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show misunderstanding/0.\n#show cleared/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show misunderstanding/0.\n#show cleared/0."))
        print(sorted({sym.name for sym in model}))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.trouble} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
