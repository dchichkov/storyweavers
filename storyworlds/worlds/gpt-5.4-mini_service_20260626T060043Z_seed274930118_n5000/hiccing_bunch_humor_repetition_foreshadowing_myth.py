#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/hiccing_bunch_humor_repetition_foreshadowing_myth.py
=====================================================================================================

A small myth-like story world about a noisy hiccing spell, a helpful bunch of
herbs, and a laughter-shaped cure.

The tale premise:
- A child of the hearth is trying to speak at a village rite.
- A troublesome hiccing spell keeps breaking their words.
- A wise elder foretells that a certain bunch of herbs by the river can help.
- Humor and repetition come from the hiccing interruptions.
- Foreshadowing appears as the elder's earlier hint about the river bunch.

The world is intentionally tiny and constraint-checked: only reasonable stories
are generated, and explicit invalid choices raise StoryError.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Troublemaker:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    symptom: str
    keyword: str = "hiccing"
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    target_mess: str = "hicc"
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_hiccup(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters.get("hicc", 0.0) < THRESHOLD:
            continue
        sig = ("hiccup", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["embarrassment"] = ent.memes.get("embarrassment", 0.0) + 1
        out.append(f"{ent.id} hicced again.")
    return out


def _r_laughter(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters.get("laugh", 0.0) < THRESHOLD:
            continue
        sig = ("laugh", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["joy"] = ent.memes.get("joy", 0.0) + 1
        ent.meters["hicc"] = max(0.0, ent.meters.get("hicc", 0.0) - 1.0)
        out.append(f"{ent.id} laughed so hard that the hiccing eased.")
    return out


def _r_remedy(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    remedy_id = world.facts.get("remedy")
    if not hero or not remedy_id:
        return out
    h = world.get(hero.id)
    if h.meters.get("hicc", 0.0) >= THRESHOLD and h.meters.get("herb", 0.0) >= THRESHOLD:
        sig = ("cure", h.id)
        if sig not in world.fired:
            world.fired.add(sig)
            h.meters["hicc"] = 0.0
            h.memes["relief"] = h.memes.get("relief", 0.0) + 1
            out.append(f"The old trouble was broken, and the hiccing fell silent.")
    return out


RULES = [
    _r_hiccup,
    _r_laughter,
    _r_remedy,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_hicc(world: World, hero: Entity) -> bool:
    sim = world.copy()
    sim.get(hero.id).meters["hicc"] = sim.get(hero.id).meters.get("hicc", 0.0) + 1
    propagate(sim, narrate=False)
    return sim.get(hero.id).meters.get("hicc", 0.0) >= THRESHOLD


def setting_line(setting: Setting) -> str:
    return {
        "grove": "The grove stood green beneath the older stars.",
        "river": "The river went silver under the moon.",
        "hall": "The hall waited with its stone eyes open wide.",
    }.get(setting.place, f"The {setting.place} waited like a patient old thing.")


def foreshadow_line() -> str:
    return "The elder had said, \"When the moon is high, look to the river bunch.\""


def build_story(world: World, hero: Entity, elder: Entity, remedy: Entity, trouble: Troublemaker) -> None:
    world.say(f"{hero.id} was a little {hero.type} of the hearth, quick to grin and quick to listen.")
    world.say(f"Each dusk {hero.id} loved to speak the old words at the village rite, because the people smiled when {hero.pronoun('subject')} did.")
    world.say(setting_line(world.setting))
    world.say("But on this night a foolish hiccing spell had snared {0}'s voice.".format(hero.id))
    world.say(f"{hero.id} tried to {trouble.verb}, but each brave start came out as a {trouble.symptom}.")
    world.say("\"Hic, hic,\" went the child, and the gathered folk gave a tiny, respectful laugh.")
    world.say(foreshadow_line())
    world.say(f"The elder pointed toward the {remedy.label} by the water and nodded once.")
    world.say(f"\"Fetch the {remedy.phrase},\" {elder.id} said. \"A bunch like that can hush a noisy curse.\"")
    world.para()
    world.say(f"{hero.id} hurried to the river and found the {remedy.label}, just where the elder had foretold.")
    hero.meters["hicc"] = 1.0
    hero.meters["herb"] = 1.0
    world.facts["hero"] = hero
    world.facts["elder"] = elder
    world.facts["remedy"] = remedy
    propagate(world, narrate=False)
    world.say(f"{hero.id} tucked the {remedy.label} under {hero.pronoun('possessive')} nose and breathed in the sharp green scent.")
    world.say("The hiccing hopped once, then twice, then stopped, as if embarrassed by the herb's brave smell.")
    world.say(f"{hero.id} laughed, and the laugh made the whole tale warmer.")
    hero.meters["laugh"] = 1.0
    propagate(world, narrate=False)
    world.para()
    world.say(f"At last {hero.id} stood before the people and spoke the old words in one clean line.")
    world.say(f"The village cheered, the elder smiled, and the {remedy.label} sat in a happy little bunch beside the hearth.")


SETTINGS = {
    "grove": Setting(place="grove", affords={"rite", "fetch"}),
    "river": Setting(place="river", affords={"fetch"}),
    "hall": Setting(place="hall", affords={"rite"}),
}

TROUBLES = {
    "hiccing": Troublemaker(
        id="hiccing",
        verb="speak the old words",
        gerund="speaking the old words",
        rush="rush through the rite",
        mess="hicc",
        symptom="hic, hic",
        keyword="hiccing",
        tags={"hiccing", "humor", "repetition", "foreshadowing", "myth"},
    ),
}

REMEDIES = {
    "bunch": Remedy(
        id="bunch",
        label="bunch of river herbs",
        phrase="a bunch of river herbs",
        prep="fetch the bunch of river herbs",
        tail="carried the bunch of river herbs home",
        target_mess="hicc",
    ),
}

HERO_NAMES = ["Ari", "Nila", "Oren", "Sera", "Tavi", "Mira"]
ELDER_NAMES = ["Elder Rowan", "Grandmother Vale", "Old Neris"]
HERO_TYPES = ["girl", "boy"]
TRAITS = ["bold", "gentle", "curious", "spirited"]


@dataclass
class StoryParams:
    place: str
    trouble: str
    remedy: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for trouble in TROUBLES.values():
            for remedy in REMEDIES.values():
                if place in {"river", "grove", "hall"} and trouble.id == "hiccing" and remedy.id == "bunch":
                    combos.append((place, trouble.id, remedy.id))
    return combos


def explain_rejection() -> str:
    return "(No story: this myth needs the hiccing trouble and the river bunch cure to match the foreshadowed turn.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mythic world of hiccing, humor, repetition, and foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=[e.split()[-1] for e in ELDER_NAMES])
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.trouble and args.remedy and (args.trouble, args.remedy) != ("hiccing", "bunch"):
        raise StoryError(explain_rejection())
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.trouble:
        combos = [c for c in combos if c[1] == args.trouble]
    if args.remedy:
        combos = [c for c in combos if c[2] == args.remedy]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, trouble, remedy = rng.choice(combos)
    gender = args.gender or rng.choice(HERO_TYPES)
    name = args.name or rng.choice(HERO_NAMES)
    elder = args.elder or rng.choice([e.split()[-1] for e in ELDER_NAMES])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, trouble=trouble, remedy=remedy, name=name, gender=gender, elder=elder, trait=trait)


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    remedy = world.facts["remedy"]
    return [
        QAItem(
            question=f"Why did {hero.id} keep stopping while trying to speak at the rite?",
            answer=f"{hero.id} kept hiccing, so each brave start came out broken and funny. That was the trouble the story had to mend.",
        ),
        QAItem(
            question=f"What did the elder say would help with the hiccing?",
            answer=f"The elder said to look for {remedy.phrase} by the river, because a bunch like that could hush the noisy curse.",
        ),
        QAItem(
            question=f"What changed at the end after {hero.id} used the bunch?",
            answer=f"The hiccing stopped, {hero.id} spoke the old words clearly, and the village cheered with relief.",
        ),
        QAItem(
            question=f"Where had the elder pointed before the hero went to fetch the cure?",
            answer=f"{elder.id} pointed toward the river and warned that the needed bunch would be found there.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bunch?",
            answer="A bunch is a group of things gathered together, like leaves tied close or flowers held in one handful.",
        ),
        QAItem(
            question="What does hiccing mean?",
            answer="Hiccing means the voice keeps jumping in little stops, like hic, hic, hic.",
        ),
        QAItem(
            question="Why do old stories repeat sounds?",
            answer="Old stories repeat sounds to make them easy to remember, musical to hear, and fun to tell aloud.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    remedy = world.facts["remedy"]
    return [
        f"Write a short myth about {hero.id} and the hiccing curse, with a humorous repeating refrain.",
        f"Tell a child-friendly legend where a bunch of river herbs helps stop hiccing at the village rite.",
        f"Compose a small myth that includes foreshadowing about {remedy.label} before the cure is found.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
trouble(hiccing).
remedy(bunch).
valid(Place, hiccing, bunch) :- place(Place).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    lines.append(asp.fact("trouble", "hiccing"))
    lines.append(asp.fact("remedy", "bunch"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
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


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    elder = world.add(Entity(id=f"Elder {params.elder}", kind="character", type="elder"))
    remedy = world.add(Entity(id=params.remedy, type="thing", label="bunch", phrase="a bunch of river herbs", plural=True))
    hero.meters["hicc"] = 1.0
    world.facts.update(hero=hero, elder=elder, remedy=remedy)
    build_story(world, hero, elder, remedy, TROUBLES[params.trouble])
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, trouble, remedy in valid_combos():
            params = StoryParams(
                place=place,
                trouble=trouble,
                remedy=remedy,
                name=random.Random(base_seed).choice(HERO_NAMES),
                gender=random.Random(base_seed + 1).choice(HERO_TYPES),
                elder="Rowan",
                trait="bold",
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
