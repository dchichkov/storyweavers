#!/usr/bin/env python3
"""
A tiny folk-tale storyworld about a nectarine shoot, a bout of flu, and a
humorous remedy that helps the little garden recover.

The world is built as a small simulation:
- a young caretaker tends a nectarine shoot
- a sneezing flu makes work harder
- a neighbor offers a funny but sensible cure
- the shoot survives, the caretaker rests, and the garden ends warmer

This file is standalone and follows the Storyweavers storyworld contract.
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
    planted: bool = False
    growing: bool = False
    recovered: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "sister", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "brother", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str
    features: set[str] = field(default_factory=set)


@dataclass
class Seedling:
    label: str
    phrase: str
    needs: set[str] = field(default_factory=set)


@dataclass
class HumorousFix:
    id: str
    label: str
    method: str
    effect: str
    requires: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather: str = ""
        self.trace_log: list[str] = []

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
            self.trace_log.append(text)

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
        clone.weather = self.weather
        return clone


def _r_flu_saps(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters.get("flu", 0.0) < THRESHOLD:
            continue
        sig = ("saps", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["energy"] = max(0.0, ent.meters.get("energy", 0.0) - 1.0)
        ent.memes["miserable"] = ent.memes.get("miserable", 0.0) + 1.0
        out.append(f"{ent.pronoun().capitalize()} felt weak and sniffly.")
    return out


def _r_laugh_helps(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes.get("mirth", 0.0) < THRESHOLD:
            continue
        sig = ("laugh", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["miserable"] = max(0.0, ent.memes.get("miserable", 0.0) - 1.0)
        ent.meters["energy"] = ent.meters.get("energy", 0.0) + 0.5
        out.append(f"A little laugh warmed {ent.pronoun('possessive')} chest.")
    return out


def _r_tray_supports_shoot(world: World) -> list[str]:
    out: list[str] = []
    shoot = world.entities.get("shoot")
    if not shoot or not shoot.planted:
        return out
    if shoot.meters.get("care", 0.0) < THRESHOLD:
        return out
    sig = ("grow", shoot.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    shoot.meters["growth"] = shoot.meters.get("growth", 0.0) + 1.0
    shoot.growing = True
    out.append("The nectarine shoot stood straighter in the soft earth.")
    return out


CAUSAL_RULES = [
    _r_flu_saps,
    _r_laugh_helps,
    _r_tray_supports_shoot,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule(world)
            if sent:
                changed = True
                produced.extend(sent)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    seedling: str
    fix: str
    seed: Optional[int] = None


SETTINGS = {
    "orchard": Setting(place="the orchard", features={"trees", "soil", "breeze"}),
    "cottage": Setting(place="the cottage garden", features={"soil", "bench", "sun"}),
    "lane": Setting(place="the old lane garden", features={"hedge", "soil", "well"}),
}

SEEDLINGS = {
    "nectarine": Seedling(label="nectarine shoot", phrase="a tender nectarine shoot", needs={"soil", "water", "care"}),
}

FIXES = {
    "pillow": HumorousFix(
        id="pillow",
        label="a pillow on the garden bench",
        method="rest on the pillow and sip warm tea",
        effect="help the sniffles and make room for a nap",
        requires={"bench"},
    ),
    "hat": HumorousFix(
        id="hat",
        label="a wool hat with a tiny feather",
        method="wear the feathered hat and tell a silly rhyme",
        effect="keep the head warm and bring back a smile",
        requires={"breeze"},
    ),
    "lantern": HumorousFix(
        id="lantern",
        label="a lantern and a spoon",
        method="tap the spoon on the lantern like a drum and laugh",
        effect="chase gloom away with noisy cheer",
        requires=set(),
    ),
}

HEROES = [
    ("Milo", "boy"),
    ("Mara", "girl"),
    ("Owen", "boy"),
    ("Tessa", "girl"),
    ("Pip", "child"),
]
HELPERS = [
    ("Grandma Reed", "woman"),
    ("Old Bram", "man"),
    ("Aunt Juniper", "woman"),
    ("Uncle Moss", "man"),
]

ASP_RULES = r"""
#show valid/4.

flu_risks(H, S) :- has_flu(H), tending(H, S).
helpful(F, S) :- fix(F), requires(F, R), setting_feature(S, R).
valid(P, H, S, F) :- place(P), hero(H), setting(P, S), has_flu(H), tending(H, shoot), seedling_ok(shoot), helpful(F, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("setting", pid, pid))
        for feat in sorted(setting.features):
            lines.append(asp.fact("setting_feature", pid, feat))
    for sid in SEEDLINGS:
        lines.append(asp.fact("seedling_ok", sid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for req in sorted(fix.requires):
            lines.append(asp.fact("requires", fid, req))
    for hid, _ in HEROES:
        lines.append(asp.fact("hero", hid))
        lines.append(asp.fact("tending", hid, "shoot"))
        lines.append(asp.fact("has_flu", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def reasonableness_gate(place: str, hero: str, seedling: str, fix: str) -> bool:
    if place not in SETTINGS:
        return False
    if hero not in {h for h, _ in HEROES}:
        return False
    if seedling not in SEEDLINGS:
        return False
    if fix not in FIXES:
        return False
    setting = SETTINGS[place]
    return bool(FIXES[fix].requires.issubset(setting.features))


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in SETTINGS:
        for hero, _ in HEROES:
            for seedling in SEEDLINGS:
                for fix in FIXES:
                    if reasonableness_gate(place, hero, seedling, fix):
                        combos.append((place, hero, seedling, fix))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny folk-tale world about a nectarine shoot and flu.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--seedling", choices=SEEDLINGS)
    ap.add_argument("--fix", choices=FIXES)
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
    if args.hero:
        combos = [c for c in combos if c[1] == args.hero]
    if args.seedling:
        combos = [c for c in combos if c[2] == args.seedling]
    if args.fix:
        combos = [c for c in combos if c[3] == args.fix]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, hero, seedling, fix = rng.choice(sorted(combos))
    helper = args.helper or rng.choice([h for h, _ in HELPERS])
    return StoryParams(place=place, hero=hero, helper=helper, seedling=seedling, fix=fix)


def make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    world.weather = "misty"

    hero = world.add(Entity(id="hero", kind="character", type="child", label=params.hero))
    helper = world.add(Entity(id="helper", kind="character", type="adult", label=params.helper))
    shoot = world.add(Entity(
        id="shoot",
        type="plant",
        label="nectarine shoot",
        phrase="a tender nectarine shoot",
        owner="garden",
        caretaker="hero",
        planted=True,
        growing=False,
    ))
    remedy = world.add(Entity(id="fix", type="thing", label=FIXES[params.fix].label))
    hero.meters["flu"] = 1.0
    hero.meters["energy"] = 1.0
    hero.memes["worry"] = 1.0
    shoot.meters["care"] = 1.0

    world.say(f"Long ago, in {world.setting.place}, {params.hero} kept watch over {shoot.phrase}.")
    world.say(f"{params.hero} loved the little shoot, for it promised sweet fruit one far-off summer.")
    world.para()
    world.say(f"Then a sneaky flu crept in with the mist, and {params.hero} began to sneeze like a tiny trumpet.")
    propagate(world)
    world.say(f"{params.helper} came by carrying {FIXES[params.fix].label}.")
    world.para()
    if params.fix == "lantern":
        world.say(f'{params.helper} said, "When the nose is a waterfall, a spoon-drumming lantern song can still lift the heart."')
    else:
        world.say(f'{params.helper} said, "Rest first, and let the old joke do the job."')
    hero.memes["mirth"] = 1.0
    world.say(f"{params.helper} helped {params.hero} {FIXES[params.fix].method}.")
    if params.fix == "pillow":
        hero.meters["rest"] = 1.0
        hero.recovered = True
    elif params.fix == "hat":
        hero.meters["warmth"] = 1.0
        hero.recovered = True
    else:
        hero.meters["joy"] = 1.0
        hero.recovered = True
    shoot.meters["care"] = 1.0
    propagate(world)
    world.para()
    world.say(f"By dusk, {params.hero} was smiling again, and the nectarine shoot stood upright in its patch of soft earth.")
    world.say(f"The old folk in the lane said that even flu can lose its grip when laughter and rest travel together.")
    world.facts.update(hero=hero, helper=helper, shoot=shoot, fix=remedy, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts["params"]
    return [
        f'Write a short folk tale for children about a nectarine shoot, a sudden flu, and a funny kindness in {f.place}.',
        f"Tell a humorous village story where {f.hero} tends a nectarine shoot but must rest because of the flu.",
        f'Write a gentle story that includes the words "nectarine", "shoot", and "flu" and ends with laughter helping the garden.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    qa = [
        QAItem(
            question=f"What was {p.hero} watching over in {world.setting.place}?",
            answer=f"{p.hero} was watching over a tender nectarine shoot that was planted in the garden.",
        ),
        QAItem(
            question=f"Why did {p.hero} start to feel so miserable?",
            answer=f"{p.hero} caught a flu, so the sneezes made the day feel weak and wobbly.",
        ),
        QAItem(
            question=f"Who came with a funny kind of help?",
            answer=f"{p.helper} came by with a humorous little remedy and helped {p.hero} rest.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {p.hero} was smiling again and the nectarine shoot was standing upright and cared for.",
        ),
    ]
    if hero.meters.get("flu", 0.0) >= THRESHOLD:
        qa.append(QAItem(
            question=f"What did the flu do to {p.hero}'s energy?",
            answer=f"The flu sapped {p.hero}'s energy and made {p.hero} feel weak and sniffly.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a nectarine?",
            answer="A nectarine is a sweet fruit with smooth skin, like a peach without fuzz.",
        ),
        QAItem(
            question="What is a shoot in a garden?",
            answer="A shoot is a new little piece of a plant that is growing up from the soil or branch.",
        ),
        QAItem(
            question="What is the flu?",
            answer="The flu is an illness that can cause fever, sneezing, coughing, and tiredness.",
        ),
        QAItem(
            question="Why can laughter help when someone is sick?",
            answer="Laughter can make a person feel happier and a bit braver, even while they are resting.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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


def explain_rejection(place: str, hero: str, seedling: str, fix: str) -> str:
    if place not in SETTINGS:
        return "(No story: that place does not exist in this little folk tale world.)"
    if seedling not in SEEDLINGS:
        return "(No story: that seedling is not part of the garden.)"
    if fix not in FIXES:
        return "(No story: that remedy is not part of the tale.)"
    return "(No story: the remedy does not fit the setting well enough for a believable tale.)"


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid()
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="orchard", hero="Milo", helper="Grandma Reed", seedling="nectarine", fix="pillow"),
            StoryParams(place="cottage", hero="Mara", helper="Aunt Juniper", seedling="nectarine", fix="hat"),
            StoryParams(place="lane", hero="Tessa", helper="Old Bram", seedling="nectarine", fix="lantern"),
        ]
        samples = [generate(p) for p in curated]
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
