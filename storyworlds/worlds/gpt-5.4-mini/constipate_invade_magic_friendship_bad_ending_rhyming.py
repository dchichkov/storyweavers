#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/constipate_invade_magic_friendship_bad_ending_rhyming.py
=========================================================================================

A standalone storyworld for a tiny rhyming tale about magic, friendship, and a
bad ending: two friends try to protect a little spell-garden, but an invader
pushes in anyway, the magic goes wrong, and the final image proves the loss.

This world is intentionally narrow. It generates only a few plausible variants:
- a child-friendly magic friendship setup,
- a warning about an invade/incursion,
- a spell attempt involving the word "constipate" as a silly rhyming charm,
- a bad ending where the spell fails and the invader changes the place.

The prose is state-driven, with meters/memes controlling the narration. The
story is not a frozen paragraph with swapped nouns; the world model decides
which beats can happen and how the ending looks.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    image: str
    rhyme: str
    has_magic: bool = True


@dataclass
class Spell:
    id: str
    chant: str
    effect: str
    power: int
    sense: int
    rhyme: str


@dataclass
class Invader:
    id: str
    label: str
    entry: str
    spread: str
    damage: str
    tags: set[str] = field(default_factory=set)


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    intruder = world.get("intruder")
    gate = world.get("gate")
    if intruder.meters["inside"] >= THRESHOLD and ("spread", intruder.id) not in world.fired:
        world.fired.add(("spread", intruder.id))
        gate.meters["trampled"] += 1
        gate.meters["ruined"] += 1
        world.get("garden").meters["changed"] += 1
        out.append("__spread__")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    for kid in (world.get("a"), world.get("b")):
        if kid.memes["fear"] >= THRESHOLD and ("fear", kid.id) not in world.fired:
            world.fired.add(("fear", kid.id))
            kid.memes["hurt"] += 1
            out.append("__fear__")
    return out


CAUSAL_RULES = [
    Rule("spread", "physical", _r_spread),
    Rule("fear", "social", _r_friendship),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(spell: Spell, invader: Invader, setting: Setting) -> bool:
    return spell.sense >= 2 and setting.has_magic and "invade" in invader.tags


def would_stop(invader: Invader, spell: Spell) -> bool:
    return spell.power >= 4


def predict_intrusion(world: World, spell: Spell, invader: Invader) -> dict:
    sim = world.copy()
    sim.get("intruder").meters["inside"] += 1
    propagate(sim, narrate=False)
    return {
        "spread": sim.get("gate").meters["ruined"] >= THRESHOLD,
        "hurt": sim.get("a").memes["hurt"] + sim.get("b").memes["hurt"],
    }


def setup(world: World, a: Entity, b: Entity) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"In moonlit rows of petal and green, {a.id} and {b.id} made a magic scene. "
        f"{world.setting.image}"
    )


def friendship(world: World, a: Entity, b: Entity) -> None:
    a.memes["love"] += 1
    b.memes["love"] += 1
    world.say(
        f"They laughed in the breeze and rhymed with delight, "
        f"for friendship felt cozy and warm in the night."
    )


def warn(world: World, a: Entity, b: Entity, intruder: Invader) -> None:
    a.memes["worry"] += 1
    pred = predict_intrusion(world, world.facts["spell"], intruder)
    world.facts["predicted"] = pred
    world.say(
        f'{a.id} frowned and spoke low, "That {intruder.label} will invade our little glade. '
        f'If it slips past the gate, our magic may fade."'
    )
    world.say(
        f'{b.id} nodded, "{world.facts["spell"].chant} is silly and bright, but a real stopping spell would need more might."'
    )


def cast_fail(world: World, a: Entity, spell: Spell, invader: Invader) -> None:
    a.memes["determination"] += 1
    world.say(
        f'{a.id} cried, "{spell.chant}!" with a hop and a spin, '
        f'but the rhyme only rang; it could not hold him in.'
    )
    world.say(
        f"The {invader.label} pushed in with a smirk and a shove, "
        f"and little blue flowers bowed out of the grove."
    )


def invade(world: World, intruder: Entity, invader: Invader) -> None:
    intruder.meters["inside"] += 1
    intruder.meters["damage"] += 1
    world.get("gate").meters["open"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{invader.entry} Then in came the {invader.label}, trampling the lane, "
        f"and the tiny brass gate was never the same."
    )


def bad_ending(world: World, a: Entity, b: Entity, invader: Invader) -> None:
    a.memes["sad"] += 1
    b.memes["sad"] += 1
    world.say(
        f"For friendship can bend, but it may still break; the friends held each other for comfort's sake."
    )
    world.say(
        f"They watched their small garden grow lopsided and bare, "
        f"with muddy footprints and nettles everywhere."
    )
    world.say(
        f"The moon kept on shining, so silver and still, "
        f"over a friendship that lost to a bigger will."
    )


def tell(setting: Setting, spell: Spell, invader: Invader,
         a_name: str = "Mina", b_name: str = "Jules",
         a_gender: str = "girl", b_gender: str = "boy") -> World:
    world = World(setting)
    a = world.add(Entity(id=a_name, kind="character", type=a_gender, role="friend"))
    b = world.add(Entity(id=b_name, kind="character", type=b_gender, role="friend"))
    gate = world.add(Entity(id="gate", type="thing", label="gate"))
    intruder = world.add(Entity(id="intruder", type="thing", label=invader.label))
    world.facts.update(a=a, b=b, gate=gate, intruder=intruder, spell=spell, invader=invader)
    setup(world, a, b)
    friendship(world, a, b)
    world.para()
    warn(world, a, b, invader)
    cast_fail(world, a, spell, invader)
    world.para()
    invade(world, intruder, invader)
    bad_ending(world, a, b, invader)
    return world


SETTINGS = {
    "garden": Setting("garden", "the garden", "The roses wore dew like tiny pearls, and the path gleamed like glass.", "soft and green", True),
    "courtyard": Setting("courtyard", "the courtyard", "The courtyard held a fountain song, with lantern light around every stone.", "bright and round", True),
    "meadow": Setting("meadow", "the meadow", "The meadow hummed with bees and clover, and a small stone arch stood proud.", "sweet and wide", True),
}

SPELLS = {
    "constipate": Spell("constipate", "Constipate, glow and hesitate!", "to jam the gate and slow the way", 1, 2, "light and bright"),
    "friendspell": Spell("friendspell", "Friendship, shimmer, friendship, sing!", "to make the flowers ring", 2, 3, "soft and sweet"),
    "littleshield": Spell("littleshield", "Little shield, please grow and cling!", "to guard a tiny thing", 1, 2, "small and neat"),
}

INVADERS = {
    "invade": Invader("invade", "invader", "At dusk he came along the track,", "He pushed through petals, crack by crack,", "He left the daisies bent and black.", tags={"invade"}),
    "moth": Invader("moth", "moth swarm", "From under the moon, the moths flew in,", "They whirled and swirled in a silvery din,", "They dusted the blooms with a sleepy gray skin.", tags={"invade"}),
    "bramble": Invader("bramble", "bramble vine", "Then bramble tendrils crept from the wall,", "They curled through the fence with a thorny sprawl,", "They snagged every ribbon and shadowed it all.", tags={"invade"}),
}

GIRL_NAMES = ["Mina", "Luna", "Poppy", "Iris", "Nina", "Tessa"]
BOY_NAMES = ["Jules", "Arlo", "Benji", "Milo", "Ravi", "Toby"]


@dataclass
class StoryParams:
    setting: str
    spell: str
    invader: str
    a_name: str
    a_gender: str
    b_name: str
    b_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for sp in SPELLS:
            for iv in INVADERS:
                if reasonableness_gate(SPELLS[sp], INVADERS[iv], SETTINGS[s]):
                    combos.append((s, sp, iv))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming magic friendship storyworld with a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--invader", choices=INVADERS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--gender-b", choices=["girl", "boy"])
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
    if args.setting and args.spell and args.invader:
        if not reasonableness_gate(SPELLS[args.spell], INVADERS[args.invader], SETTINGS[args.setting]):
            raise StoryError("No story: that spell and invader don't make a sensible rhyming magic danger.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.spell is None or c[1] == args.spell)
              and (args.invader is None or c[2] == args.invader)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    s, sp, iv = rng.choice(sorted(combos))
    ga = args.gender_a or rng.choice(["girl", "boy"])
    gb = args.gender_b or ("boy" if ga == "girl" else "girl")
    na = args.name_a or rng.choice(GIRL_NAMES if ga == "girl" else BOY_NAMES)
    nb = args.name_b or rng.choice([n for n in (GIRL_NAMES if gb == "girl" else BOY_NAMES) if n != na] or (GIRL_NAMES if gb == "girl" else BOY_NAMES))
    return StoryParams(s, sp, iv, na, ga, nb, gb)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SPELLS[params.spell], INVADERS[params.invader],
                 params.a_name, params.b_name, params.a_gender, params.b_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a 3-to-5-year-old about magic friendship in {f["spell"].rhyme} words, and include the word "constipate".',
        f'Tell a rhyming bad-ending story where {f["a"].id} and {f["b"].id} try to stop a(n) {f["invader"].label} that will invade their {world.setting.place}.',
        f'Write a short magic friendship rhyme that ends sadly when a small place is invaded and the friends cannot fix it.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    return [
        ("Who is the story about?",
         f"It is about {f['a'].id} and {f['b'].id}, two friends who loved magic and each other. Their friendship is the warm heart of the story."),
        ("What spell did they try?",
         f"They tried the spell '{f['spell'].chant}'. It was meant to be a silly rhyming charm, but it was too small to stop the invasion."),
        ("What happened to the garden?",
         f"The {f['invader'].label} invaded it and trampled the gate. After that, the garden looked muddy and bent, which is why the ending is sad."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a friendship?", "A friendship is when people care about each other, share, and try to help each other feel safe and happy."),
        QAItem("What is a magic spell?", "A magic spell is a special saying or action in a story that is supposed to make something happen."),
        QAItem("What does invade mean?", "To invade means to push into a place and take over space that was not meant for you."),
        QAItem("What kind of ending is a bad ending?", "A bad ending is when the problem does not get fixed and the characters are left sad or stuck."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(SP, IV, ST) :- spell(SP), invader(IV), setting(ST), sense(SP, N), N >= 2, has_tag(IV, invade).
outcome(bad) :- valid(_, _, _).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for spid, sp in SPELLS.items():
        lines.append(asp.fact("spell", spid))
        lines.append(asp.fact("sense", spid, sp.sense))
    for iid, iv in INVADERS.items():
        lines.append(asp.fact("invader", iid))
        for t in sorted(iv.tags):
            lines.append(asp.fact("has_tag", iid, t))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams("garden", "constipate", "invade", "Mina", "girl", "Jules", "boy"),
    StoryParams("courtyard", "friendspell", "moth", "Luna", "girl", "Toby", "boy"),
    StoryParams("meadow", "littleshield", "bramble", "Poppy", "girl", "Arlo", "boy"),
]


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = cl == py
    smoke = generate(CURATED[0])
    _ = smoke.story
    if ok:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
    else:
        print("MISMATCH between ASP and Python gate.")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))
        return 1
    print("OK: story generation smoke test passed.")
    return 0


def explain_rejection(spell: Spell, invader: Invader) -> str:
    return f"(No story: '{spell.id}' is too weak to reasonably stop an {invader.label}; the bad ending needs a real conflict.)"


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    pool = [n for n in pool if n != avoid]
    return rng.choice(pool)


def valid_story_choice(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
                params = valid_story_choice(args, random.Random(seed))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming magic friendship story that includes the word "constipate" and ends in a bad ending.',
        f'Tell a story where {f["a"].id} and {f["b"].id} try to stop an invader with a silly spell, but the invader still invade{s if False else ""}s their {world.setting.place}.',
        f'Write a child-friendly rhyme about friendship, magic, and a sad ending when a place is invaded.',
    ]


if __name__ == "__main__":
    main()
