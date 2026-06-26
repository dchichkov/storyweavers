#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/puke_bob_rhyme_sound_effects_kindness_heartwarming.py
================================================================================================

A small heartwarming story world about Bob, a sudden puke scare, gentle
kindness, and a few cheerful rhyme-and-sound-effect beats.

The domain premise:
- Bob is a little character who feels a tummy rumble.
- A meal, a ride, or a busy moment can make nausea worse.
- A caring helper notices, offers a bucket, water, and a quiet place.
- The emotional turn is kindness: Bob goes from embarrassed and shaky to
  relieved and grateful.
- The prose includes light rhyme and sound effects, but remains child-facing
  and complete.

This file follows the Storyworld contract:
- self-contained stdlib script under storyworlds/worlds/
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
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

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Trigger:
    id: str
    noun: str
    verb: str
    gerund: str
    cue: str
    mess: str
    warning: str
    sound: str
    rhyme: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ComfortItem:
    id: str
    label: str
    phrase: str
    fix: str
    supports: set[str]
    plural: bool = False


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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_bob_embarrassed(world: World) -> list[str]:
    out: list[str] = []
    bob = world.entities.get("Bob")
    if not bob:
        return out
    if bob.memes.get("puke", 0.0) >= THRESHOLD and ("embarrassed",) not in world.fired:
        world.fired.add(("embarrassed",))
        bob.memes["embarrassed"] = 1.0
        out.append("Bob felt hot-faced and wanted to hide for a second.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("Helper")
    bob = world.entities.get("Bob")
    if not helper or not bob:
        return out
    if helper.memes.get("kindness", 0.0) < THRESHOLD:
        return out
    if bob.memes.get("puke", 0.0) >= THRESHOLD and ("comfort",) not in world.fired:
        world.fired.add(("comfort",))
        bob.memes["safe"] = 1.0
        helper.memes["care"] = 1.0
        out.append("The helper stayed calm, and Bob felt safe enough to breathe again.")
    return out


CAUSAL_RULES = [
    Rule("embarrassed", _r_bob_embarrassed),
    Rule("kindness", _r_kindness),
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


SETTINGS = {
    "home": Setting(place="at home", indoor=True, affords={"snack", "ride", "bed"}),
    "car": Setting(place="in the car", indoor=True, affords={"ride"}),
    "park": Setting(place="the park", indoor=False, affords={"play", "snack"}),
    "clinic": Setting(place="the clinic", indoor=True, affords={"wait"}),
}

TRIGGERS = {
    "snack": Trigger(
        id="snack",
        noun="snack",
        verb="eat a snack",
        gerund="eating a snack",
        cue="munch, munch",
        mess="puke",
        warning="That snack might feel like a wobble in the tummy",
        sound="munch-munch",
        rhyme="A nibble can wobble a tummy a little",
        tags={"food", "tummy"},
    ),
    "ride": Trigger(
        id="ride",
        noun="bumpy ride",
        verb="go for a bumpy ride",
        gerund="bumping along",
        cue="bump-bump",
        mess="puke",
        warning="Those bumps can shake a queasy tummy",
        sound="bumpity-bump",
        rhyme="A bumpy ride can make a tummy slide",
        tags={"car", "motion", "tummy"},
    ),
    "spinning": Trigger(
        id="spinning",
        noun="spinning game",
        verb="spin in circles",
        gerund="spinning around",
        cue="whoooosh",
        mess="puke",
        warning="Too much spinning can tip a wobbling stomach",
        sound="swish-swish",
        rhyme="A twirly whirl may curl a girl or boy",
        tags={"play", "motion", "tummy"},
    ),
}

COMFORTS = {
    "bucket": ComfortItem(
        id="bucket",
        label="bucket",
        phrase="a little blue bucket",
        fix="held it close just in case",
        supports={"puke"},
    ),
    "water": ComfortItem(
        id="water",
        label="water cup",
        phrase="a cool cup of water",
        fix="offered a sip",
        supports={"puke"},
    ),
    "blanket": ComfortItem(
        id="blanket",
        label="blanket",
        phrase="a soft blanket",
        fix="wrapped it around Bob's shoulders",
        supports={"safe"},
    ),
    "towel": ComfortItem(
        id="towel",
        label="towel",
        phrase="a clean towel",
        fix="cleaned up the spill",
        supports={"puke"},
    ),
}

BOY_NAMES = ["Bob", "Ben", "Max", "Sam", "Leo"]
GIRL_NAMES = ["Mia", "Lily", "Ava"]


@dataclass
class StoryParams:
    setting: str
    trigger: str
    helper: str
    name: str = "Bob"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming story world: Bob, puke, rhyme, sound effects, kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trigger", choices=TRIGGERS)
    ap.add_argument("--helper", choices=["mother", "father", "friend", "nurse"])
    ap.add_argument("--name")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    trigger = args.trigger or rng.choice(list(TRIGGERS))
    helper = args.helper or rng.choice(["mother", "father", "friend", "nurse"])
    name = args.name or "Bob"
    return StoryParams(setting=setting, trigger=trigger, helper=helper, name=name)


def make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    bob = world.add(Entity(id="Bob", kind="character", type="boy", label="Bob", traits=["little", "gentle"]))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label=params.helper))
    trigger = TRIGGERS[params.trigger]
    bucket = world.add(Entity(id="Bucket", type="bucket", label="bucket", phrase=COMFORTS["bucket"].phrase))
    water = world.add(Entity(id="Water", type="water", label="water", phrase=COMFORTS["water"].phrase))
    towel = world.add(Entity(id="Towel", type="towel", label="towel", phrase=COMFORTS["towel"].phrase))
    world.facts.update(bob=bob, helper=helper, trigger=trigger, bucket=bucket, water=water, towel=towel)
    return world


def _start(world: World, params: StoryParams) -> None:
    trigger = world.facts["trigger"]
    bob = world.facts["bob"]
    helper = world.facts["helper"]
    world.say(f"Bob was a little boy with a brave smile and a tummy that sometimes went wobble-wobble.")
    world.say(f"He was {trigger.gerund} {world.setting.place}, and everything felt fine at first.")
    world.say(f"{trigger.rhyme}. {trigger.sound}! The words jingled like a tiny song.")
    world.para()
    world.say(f"Then Bob's face went pale. His tummy gave a twist, and he whispered, \"Uh-oh.\"")
    world.say(f"{trigger.warning}, the helper thought, so {helper.label_word if helper.type in {'mother','father'} else helper.label} hurried over kindly.")


def _turn(world: World) -> None:
    bob = world.facts["bob"]
    helper = world.facts["helper"]
    trigger = world.facts["trigger"]
    bob.memes["puke"] = 1.0
    bob.memes["fear"] = 1.0
    propagate(world)
    world.say(f"\"Pitter-pat, don't panic,\" {helper.label_word if helper.type in {'mother','father'} else helper.label} said. \"We'll handle the hiccupy part.\"")
    world.say(f"{helper.label_word if helper.type in {'mother','father'} else helper.label} brought the bucket: plink, plink, plonk.")
    world.say(f"Bob leaned over the bucket just in time. Ploof! He puked, and the bucket caught the mess.")
    world.say(f"No one laughed. That made Bob feel much, much better.")


def _resolve(world: World) -> None:
    bob = world.facts["bob"]
    helper = world.facts["helper"]
    world.facts["helper"].memes["kindness"] = 1.0
    propagate(world)
    world.say(f"{helper.label_word if helper.type in {'mother','father'} else helper.label} cleaned the splash with a towel: wipe, wipe, swish.")
    world.say(f"Then {helper.label_word if helper.type in {'mother','father'} else helper.label} offered water and a soft blanket.")
    world.say(f"Bob took one small sip. Sip-sip. His breathing slowed, and his shoulders stopped shaking.")
    world.say(f"\"Kind hands, kind words,\" {helper.label_word if helper.type in {'mother','father'} else helper.label} said, \"and a little rest can help a lot.\"")
    world.say(f"Bob smiled weakly, then truly. The yucky moment passed, but the kindness stayed.")


def tell(params: StoryParams) -> World:
    world = make_world(params)
    _start(world, params)
    _turn(world)
    world.para()
    _resolve(world)
    bob = world.facts["bob"]
    helper = world.facts["helper"]
    world.facts["resolved"] = True
    world.facts["comforts"] = ["bucket", "water", "towel", "blanket"]
    world.say(f"At the end, Bob was safe, the room was clean, and {helper.label_word if helper.type in {'mother','father'} else helper.label} stayed right beside him like a warm little umbrella.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    trigger = f["trigger"]
    return [
        f'Write a short heartwarming story for preschoolers about Bob, a tummy wobble, and {trigger.noun}.',
        f"Tell a gentle story that includes the sound effect \"{trigger.sound}\" and shows kindness after a puke scare.",
        f"Write a simple story with rhyme and sound effects where Bob feels sick, gets help, and ends feeling safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    trigger = f["trigger"]
    helper = f["helper"]
    helper_name = helper.label_word if helper.type in {"mother", "father"} else helper.label
    return [
        QAItem(
            question="Who is the story mainly about?",
            answer="The story is mainly about Bob, a little boy whose tummy gets wobbly and who needs kind help.",
        ),
        QAItem(
            question=f"What happened after Bob started {trigger.gerund}?",
            answer="Bob got queasy, leaned over a bucket, and puked into it before the mess could spread.",
        ),
        QAItem(
            question="How did the helper respond?",
            answer=f"{helper_name.capitalize()} stayed calm, brought a bucket, cleaned the spill, and offered water and a blanket.",
        ),
        QAItem(
            question="How did Bob feel at the end?",
            answer="Bob felt safe, relieved, and grateful because the helper was gentle and kind.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is puke?",
            answer="Puke is vomit that comes up from a stomach when someone feels very sick or too queasy.",
        ),
        QAItem(
            question="Why can a bucket help when someone feels sick?",
            answer="A bucket can catch the puke so it does not spill all over the floor.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means helping gently, using caring words, and making someone feel safe.",
        ),
        QAItem(
            question="Why do people clean up after puke?",
            answer="They clean it up so the place stays neat, fresh, and safe to use again.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="home", trigger="snack", helper="mother", name="Bob"),
    StoryParams(setting="car", trigger="ride", helper="father", name="Bob"),
    StoryParams(setting="park", trigger="spinning", helper="friend", name="Bob"),
]


ASP_RULES = r"""
setting(home).
setting(car).
setting(park).
setting(clinic).

trigger(snack).
trigger(ride).
trigger(spinning).

helper(mother).
helper(father).
helper(friend).
helper(nurse).

can_happen(home, snack).
can_happen(home, ride).
can_happen(home, spinning).
can_happen(car, ride).
can_happen(park, snack).
can_happen(park, spinning).
can_happen(clinic, snack).
can_happen(clinic, ride).

heartwarming(S, T, H) :- can_happen(S, T), helper(H).
#show heartwarming/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TRIGGERS:
        lines.append(asp.fact("trigger", tid))
    for hid in ["mother", "father", "friend", "nurse"]:
        lines.append(asp.fact("helper", hid))
    for sid, setting in SETTINGS.items():
        for tid in setting.affords:
            lines.append(asp.fact("can_happen", sid, tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_combos() -> list[tuple[str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show heartwarming/3."))
    return sorted(set(asp.atoms(model, "heartwarming")))


def asp_verify() -> int:
    py = {(p.setting, p.trigger, p.helper) for p in CURATED}
    cl = set(asp_combos())
    expected = {
        ("home", "snack", "mother"),
        ("home", "snack", "father"),
        ("home", "snack", "friend"),
        ("home", "snack", "nurse"),
        ("home", "ride", "mother"),
        ("home", "ride", "father"),
        ("home", "ride", "friend"),
        ("home", "ride", "nurse"),
        ("home", "spinning", "mother"),
        ("home", "spinning", "father"),
        ("home", "spinning", "friend"),
        ("home", "spinning", "nurse"),
        ("car", "ride", "mother"),
        ("car", "ride", "father"),
        ("car", "ride", "friend"),
        ("car", "ride", "nurse"),
        ("park", "snack", "mother"),
        ("park", "snack", "father"),
        ("park", "snack", "friend"),
        ("park", "snack", "nurse"),
        ("park", "spinning", "mother"),
        ("park", "spinning", "father"),
        ("park", "spinning", "friend"),
        ("park", "spinning", "nurse"),
        ("clinic", "snack", "mother"),
        ("clinic", "snack", "father"),
        ("clinic", "snack", "friend"),
        ("clinic", "snack", "nurse"),
        ("clinic", "ride", "mother"),
        ("clinic", "ride", "father"),
        ("clinic", "ride", "friend"),
        ("clinic", "ride", "nurse"),
    }
    if cl != expected:
        print("MISMATCH between clingo and expected combos:")
        if cl - expected:
            print("  only in clingo:", sorted(cl - expected))
        if expected - cl:
            print("  missing from clingo:", sorted(expected - cl))
        return 1
    print(f"OK: clingo gate matches expected combos ({len(cl)} combos).")
    return 0


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show heartwarming/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for row in combos:
            print("  ", row)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.trigger} at {p.setting} (helper: {p.helper})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
