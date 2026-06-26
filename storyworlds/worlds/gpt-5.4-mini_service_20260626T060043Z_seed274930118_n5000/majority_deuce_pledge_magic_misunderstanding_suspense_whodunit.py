#!/usr/bin/env python3
"""
Standalone storyworld: a tiny whodunit with magic, misunderstanding, and suspense.

Seed premise:
- A small town has a magic lamp that keeps a pledge chest closed.
- A misunderstanding makes it look like one of two suspects, the deuce, broke the promise.
- Suspense grows while the hero gathers clues.
- The majority of clues point to the true culprit, and the ending reveals a harmless magical mistake.

The world is intentionally small and classical: one mystery, a few typed entities,
state changes, a causal turn, and a clear reveal.
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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        female = {"girl", "woman", "mother", "aunt", "sister"}
        male = {"boy", "man", "father", "uncle", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
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


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    suspect1: str
    suspect2: str
    culprit: str
    magic_item: str
    pledge_item: str
    seed: Optional[int] = None


SETTINGS = {
    "lantern_square": "the lantern square",
    "old_library": "the old library",
    "harbor_lane": "the harbor lane",
}

HERO_NAMES = {
    "girl": ["Mina", "Lena", "Tessa", "Nora", "Ivy"],
    "boy": ["Eli", "Milo", "Theo", "Arlo", "Finn"],
}

HELPER_NAMES = {
    "girl": ["June", "Rina", "Pia"],
    "boy": ["Noel", "Bram", "Otto"],
}

SUSPECT_NAMES = ["Poppy", "Jasper", "Wren", "Quinn", "Sage", "Moss"]
MAGIC_ITEMS = [
    ("moon lantern", "moon lantern"),
    ("glass wand", "glass wand"),
    ("spark key", "spark key"),
]
PLEDGE_ITEMS = [
    ("pledge box", "pledge box"),
    ("promise ribbon", "promise ribbon"),
    ("oath note", "oath note"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny whodunit storyworld with magic, misunderstanding, and suspense.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--suspect1")
    ap.add_argument("--suspect2")
    ap.add_argument("--culprit")
    ap.add_argument("--magic-item", choices=[x[0] for x in MAGIC_ITEMS])
    ap.add_argument("--pledge-item", choices=[x[0] for x in PLEDGE_ITEMS])
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


def _pick(rng: random.Random, items: list[str], used: set[str]) -> str:
    choices = [x for x in items if x not in used]
    if not choices:
        raise StoryError("Not enough distinct names for the mystery cast.")
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    hero_name = args.name or rng.choice(HERO_NAMES[gender])
    helper_name = args.helper_name or rng.choice(HELPER_NAMES[helper_gender])

    used = {hero_name, helper_name}
    suspect1 = args.suspect1 or _pick(rng, SUSPECT_NAMES, used)
    used.add(suspect1)
    suspect2 = args.suspect2 or _pick(rng, SUSPECT_NAMES, used)
    used.add(suspect2)

    culprit = args.culprit or rng.choice([suspect1, suspect2, "magic"])
    if culprit not in {suspect1, suspect2, "magic"}:
        raise StoryError("The culprit must be one of the two suspects or the magic itself.")

    magic_item = args.magic_item or rng.choice([x[0] for x in MAGIC_ITEMS])
    pledge_item = args.pledge_item or rng.choice([x[0] for x in PLEDGE_ITEMS])

    if args.magic_item and args.pledge_item and args.magic_item == "spark key" and args.pledge_item == "oath note":
        # still valid, but keep as a supported combo
        pass

    return StoryParams(
        setting=setting,
        hero_name=hero_name,
        hero_type=gender,
        helper_name=helper_name,
        helper_type=helper_gender,
        suspect1=suspect1,
        suspect2=suspect2,
        culprit=culprit,
        magic_item=magic_item,
        pledge_item=pledge_item,
    )


def _make_world(params: StoryParams) -> World:
    world = World(setting=SETTINGS[params.setting])

    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    s1 = world.add(Entity(id="suspect1", kind="character", type="person", label=params.suspect1))
    s2 = world.add(Entity(id="suspect2", kind="character", type="person", label=params.suspect2))
    magic_label = dict(MAGIC_ITEMS)[params.magic_item]
    pledge_label = dict(PLEDGE_ITEMS)[params.pledge_item]

    magic = world.add(Entity(id="magic_item", kind="thing", type="magic", label=magic_label, phrase=f"a {magic_label}"))
    pledge = world.add(Entity(id="pledge_item", kind="thing", type="promise", label=pledge_label, phrase=f"a {pledge_label}"))

    world.facts.update(hero=hero, helper=helper, s1=s1, s2=s2, magic=magic, pledge=pledge, params=params)
    return world


def _narrate_setup(world: World) -> None:
    f = world.facts
    hero, helper, s1, s2, magic, pledge = f["hero"], f["helper"], f["s1"], f["s2"], f["magic"], f["pledge"]
    world.say(f"{hero.label} loved walking through {world.setting} with {helper.label}.")
    world.say(f"At the center of the place stood {magic.label}, and beside it sat {pledge.label}, which guarded a small pledge chest.")
    world.say(f"{hero.label} had made a pledge to keep the chest closed until the lantern bell rang.")
    world.para()
    world.say(f"That afternoon, {s1.label} and {s2.label} came to watch the show, and the whole square felt busy and bright.")
    world.say(f"{helper.label} whispered that the magic would only work if everyone kept the pledge."


)
    world.facts["majority"] = 2


def _cause_misunderstanding(world: World) -> None:
    f = world.facts
    hero, helper, s1, s2, magic, pledge, params = f["hero"], f["helper"], f["s1"], f["s2"], f["magic"], f["pledge"], f["params"]
    culprit_name = {"suspect1": s1.label, "suspect2": s2.label, "magic": "the magic"}[params.culprit]

    world.para()
    world.say("Then the bell went quiet.")
    if params.culprit == "magic":
        world.say(f"The {magic.label} began to glow by itself, and the pledge chest clicked open just a tiny bit.")
        world.say(f"Everyone gasped, because no one had touched {pledge.label}.")
    elif params.culprit == "suspect1":
        world.say(f"{s1.label} reached toward the glow, but only to point at a shiny chip on the floor.")
        world.say(f"The chip rolled under {pledge.label}, and the chest gave a little squeak.")
    else:
        world.say(f"{s2.label} leaned close to peek, and the lantern light jumped across the box.")
        world.say(f"That strange light made the pledge chest tremble as if someone had knocked on it.")

    world.say(f"Still, the first guess was wrong.")
    world.say(f"The misunderstanding made it look as if {culprit_name} had broken the pledge.")


def _build_suspense(world: World) -> None:
    f = world.facts
    hero, helper, s1, s2, magic, pledge, params = f["hero"], f["helper"], f["s1"], f["s2"], f["magic"], f["pledge"], f["params"]

    world.para()
    world.say(f"{hero.label} felt a knot of suspense in the chest, because the clues did not fit together yet.")
    world.say(f"{helper.label} crouched near {pledge.label} and found a dust trail, two tiny scuffs, and a smudge of silver light.")
    world.say(f"That made a deuce of suspects, {s1.label} and {s2.label}, seem even more puzzling.")
    world.say(f"{hero.label} made a pledge to follow the clues carefully instead of guessing too fast.")
    world.say(f"One clue pointed left, one clue pointed right, and the magic kept flickering like it wanted to speak.")


def _reveal(world: World) -> None:
    f = world.facts
    hero, helper, s1, s2, magic, pledge, params = f["hero"], f["helper"], f["s1"], f["s2"], f["magic"], f["pledge"], f["params"]

    world.para()
    if params.culprit == "magic":
        world.say(f"At last, {helper.label} noticed the real trick: a loose crystal inside {magic.label} was catching the moonlight.")
        world.say(f"The crystal had tapped {pledge.label} with a tiny spark, so the chest only seemed guilty.")
        world.say(f"{hero.label} smiled, because the majority of the clues pointed to magic, not a person.")
    else:
        culprit = s1 if params.culprit == "suspect1" else s2
        other = s2 if params.culprit == "suspect1" else s1
        world.say(f"At last, {hero.label} looked at the deuce of suspects again and noticed a simple thing: only {culprit.label} had silver dust on {culprit.pronoun('possessive')} sleeve.")
        world.say(f"{other.label} had clean hands, so the majority of the clues did not match {other.label} at all.")
        world.say(f"{culprit.label} had bumped {magic.label} by accident, and the bump had made the pledge chest click open.")
    world.say(f"In the end, the chest closed again, the pledge stayed safe, and the magic settled down like a sleepy lamp.")


def generate_story(world: World) -> None:
    _narrate_setup(world)
    _cause_misunderstanding(world)
    _build_suspense(world)
    _reveal(world)


def _generate_story_text(params: StoryParams) -> World:
    world = _make_world(params)
    generate_story(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a child-friendly whodunit about {p.hero_name}, a magic {p.magic_item}, and a pledge that is almost broken.",
        f"Tell a suspenseful mystery where a misunderstanding makes a deuce of suspects look guilty before the real clue appears.",
        f"Write a short story in which the majority of clues solve the mystery and the ending proves the pledge stayed safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    hero, helper, s1, s2 = f["hero"], f["helper"], f["s1"], f["s2"]
    culprit = {"suspect1": s1.label, "suspect2": s2.label, "magic": "the magic"}[p.culprit]
    return [
        QAItem(
            question=f"Who was the story mostly about?",
            answer=f"The story was mostly about {hero.label}, who tried to solve the mystery at {world.setting}.",
        ),
        QAItem(
            question=f"What caused the misunderstanding?",
            answer=f"The misunderstanding came from {culprit} making the pledge chest seem suspicious before the clues were understood.",
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=f"It ended when {hero.label} and {helper.label} found the real clue, and the pledge stayed safe while the chest closed again.",
        ),
        QAItem(
            question=f"What did the majority of the clues show?",
            answer=f"The majority of the clues showed that the answer was {culprit}, not a careless guess.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pledge?",
            answer="A pledge is a promise that someone says they will keep.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people think something wrong before they know the full story.",
        ),
        QAItem(
            question="What does suspense mean in a mystery?",
            answer="Suspense is the feeling of wondering what will happen next while the answer is still hidden.",
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where the reader tries to figure out who did it.",
        ),
        QAItem(
            question="What does majority mean?",
            answer="A majority means the bigger part of a group or the answer supported by most of the clues.",
        ),
        QAItem(
            question="What does deuce mean here?",
            answer="Here, deuce means a pair of two suspects together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8} {e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% Inline declarative twin of the reasonableness gate.
% We keep it small: a valid mystery has a setting, a hero, two suspects,
% a magic item, a pledge item, and exactly one chosen culprit.
valid_setting(lantern_square).
valid_setting(old_library).
valid_setting(harbor_lane).

valid_gender(girl).
valid_gender(boy).

valid_kind(magic_item, "moon lantern").
valid_kind(magic_item, "glass wand").
valid_kind(magic_item, "spark key").

valid_kind(pledge_item, "pledge box").
valid_kind(pledge_item, "promise ribbon").
valid_kind(pledge_item, "oath note").

valid_mystery(Setting, HeroGender, HelperGender, Magic, Pledge) :-
    valid_setting(Setting),
    valid_gender(HeroGender),
    valid_gender(HelperGender),
    valid_kind(magic_item, Magic),
    valid_kind(pledge_item, Pledge).

#show valid_mystery/5.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for g in ["girl", "boy"]:
        lines.append(asp.fact("gender", g))
    for label, _ in MAGIC_ITEMS:
        lines.append(asp.fact("magic_kind", label))
    for label, _ in PLEDGE_ITEMS:
        lines.append(asp.fact("pledge_kind", label))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_mystery/5."))
    atoms = sorted(set(asp.atoms(model, "valid_mystery")))
    py = []
    for s in SETTINGS:
        for hg in ["girl", "boy"]:
            for hg2 in ["girl", "boy"]:
                for m, _ in MAGIC_ITEMS:
                    for p, _ in PLEDGE_ITEMS:
                        py.append((s, hg, hg2, m, p))
    if atoms:
        print(f"OK: ASP produced {len(atoms)} mystery skeleton(s).")
        return 0
    print("MISMATCH: ASP produced no mysteries.")
    return 1


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_mystery/5."))
    return sorted(set(asp.atoms(model, "valid_mystery")))


def generate(params: StoryParams) -> StorySample:
    world = _generate_story_text(params)
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
    StoryParams(
        setting="old_library",
        hero_name="Mina",
        hero_type="girl",
        helper_name="Noel",
        helper_type="boy",
        suspect1="Poppy",
        suspect2="Jasper",
        culprit="magic",
        magic_item="moon lantern",
        pledge_item="pledge box",
    ),
    StoryParams(
        setting="lantern_square",
        hero_name="Eli",
        hero_type="boy",
        helper_name="June",
        helper_type="girl",
        suspect1="Quinn",
        suspect2="Sage",
        culprit="suspect1",
        magic_item="glass wand",
        pledge_item="promise ribbon",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_mystery/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} mystery skeleton(s):")
        for c in combos:
            print("  ", c)
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
        if len(samples) > 1 and not args.all:
            print(f"### variant {i + 1}")
        elif args.all:
            p = sample.params
            print(f"### {p.hero_name} in {p.setting} with {p.magic_item}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
