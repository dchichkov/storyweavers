#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pitcher_cautionary_heartwarming.py
===================================================================

A small storyworld about a child, a pitcher, a warning, and a kinder safer
choice. The tone aims for heartwarming, while the plot stays cautionary:
someone is tempted to carry or pour a heavy pitcher in an unsafe way, a wiser
helper predicts the problem, and the family chooses a safer method that still
keeps the moment warm and happy.

The world is intentionally tiny:
- a child wants to serve drinks,
- a pitcher can be glass or ceramic and can spill or break,
- a caregiver warns about the danger,
- the child either listens or, in a harsher variant, does not,
- the ending proves what changed in the world state.

It supports the shared Storyweavers interface:
- build_parser
- resolve_params
- generate
- emit
- main

and also includes:
- a Python reasonableness gate,
- inline ASP rules with facts from registries,
- --verify parity checks,
- JSON / QA / trace / ASP modes.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    fragile: bool = False
    full: bool = False
    safe_tool: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    light: str
    mood: str
    table: str
    spill_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PitcherKind:
    id: str
    label: str
    material: str
    heavy: bool
    fragile: bool
    spill_risk: int
    theme: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Drink:
    id: str
    label: str
    color: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeMethod:
    id: str
    label: str
    sense: int
    safety: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["spilled"] < THRESHOLD:
            continue
        sig = ("spill", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "floor" in world.entities:
            world.get("floor").meters["mess"] += 1
        for c in world.entities.values():
            if c.kind == "character":
                c.memes["worry"] += 1
        out.append("__spill__")
    return out


def _r_break(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["broken"] < THRESHOLD:
            continue
        sig = ("break", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "floor" in world.entities:
            world.get("floor").meters["danger"] += 1
        out.append("__break__")
    return out


CAUSAL_RULES = [Rule("spill", "physical", _r_spill), Rule("break", "physical", _r_break)]


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


def is_reasonable(pitcher: PitcherKind, method: SafeMethod) -> bool:
    return method.sense >= SENSE_MIN and pitcher.spill_risk >= 1


def predict_mishap(world: World, pitcher_id: str, method_id: str) -> dict:
    sim = world.copy()
    pitcher = sim.get(pitcher_id)
    pitcher.meters["spilled"] += 1
    if sim.get(pitcher_id).fragile:
        pitcher.meters["broken"] += 1
    propagate(sim, narrate=False)
    floor = sim.get("floor")
    return {"mess": floor.meters["mess"], "danger": floor.meters["danger"]}


def build_scene(world: World, kid: Entity, helper: Entity, setting: Setting, pitcher: PitcherKind, drink: Drink) -> None:
    kid.memes["joy"] += 1
    helper.memes["care"] += 1
    world.say(
        f"On a bright afternoon at {setting.place}, {kid.id} and {helper.id} "
        f"set the table near {setting.light}. {setting.mood.capitalize()}, the room felt ready for a small treat."
    )
    world.say(
        f"There was a {pitcher.label} on the table, full of {drink.label}."
    )
    world.say(
        f'"Let’s pour it carefully," {kid.id} said, hoping everyone could share.'
    )


def warning(world: World, helper: Entity, kid: Entity, pitcher: PitcherKind, setting: Setting) -> None:
    pred = predict_mishap(world, "pitcher", "tray")
    helper.memes["warning"] += 1
    world.facts["predicted_mess"] = pred["mess"]
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f"{helper.id} noticed the pitcher was {pitcher.material} and said, "
        f'"Hold on. If that slips by {setting.spill_spot}, it could make a mess."'
    )
    if pitcher.fragile:
        world.say(
            f'"And if it hits the floor, the {pitcher.label} might break," '
            f"{helper.id} added softly."
        )


def carry_unsafe(world: World, kid: Entity, pitcher: PitcherKind) -> None:
    kid.memes["defiance"] += 1
    world.say(
        f"{kid.id} tried to lift the {pitcher.label} with one hand anyway."
    )


def spill(world: World, pitcher_ent: Entity, pitcher: PitcherKind, drink: Drink) -> None:
    pitcher_ent.meters["spilled"] += 1
    if pitcher.fragile:
        pitcher_ent.meters["broken"] += 1
    propagate(world, narrate=False)
    if pitcher.fragile:
        world.say(
            f"The {pitcher.label} tipped, the juice splashed, and a crack went "
            f"through the pitcher."
        )
    else:
        world.say(
            f"The {pitcher.label} tipped, and {drink.label} sloshed across the table."
        )


def alarm(world: World, helper: Entity, kid: Entity, pitcher: PitcherKind) -> None:
    helper.memes["worry"] += 1
    world.say(
        f'"Oh, dear!" {helper.id} said, hurrying over to help.'
    )


def safe_choice(world: World, helper: Entity, kid: Entity, method: SafeMethod, pitcher: PitcherKind, drink: Drink) -> None:
    kid.memes["relief"] += 1
    helper.memes["relief"] += 1
    if method.id == "both_hands":
        kid.meters["steady"] += 1
    if method.id == "tray":
        kid.meters["steady"] += 1
    world.say(
        f"{helper.id} smiled and showed {kid.id} a better way: {method.text}."
    )
    world.say(
        f"Together they cleaned up, then poured the {drink.label} again without a spill."
    )
    world.say(
        f"This time the {pitcher.label} stayed safe, and the table stayed dry."
    )


def lesson(world: World, helper: Entity, kid: Entity, pitcher: PitcherKind) -> None:
    kid.memes["lesson"] += 1
    helper.memes["love"] += 1
    world.say(
        f'{helper.id} gave {kid.id} a hug and said, "Careful hands keep the good things safe."'
    )
    world.say(
        f"{kid.id} nodded. {kid.id} liked that the day was still warm and kind, only safer now."
    )


def tell(setting: Setting, pitcher: PitcherKind, drink: Drink, method: SafeMethod,
         kid_name: str = "Mia", kid_gender: str = "girl",
         helper_name: str = "Mom", helper_gender: str = "girl") -> World:
    world = World()
    kid = world.add(Entity(id=kid_name, kind="character", type=kid_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    world.add(Entity(id="floor", type="floor"))
    pitcher_ent = world.add(Entity(id="pitcher", type="pitcher", label=pitcher.label, fragile=pitcher.fragile))
    world.facts.update(setting=setting, pitcher=pitcher, drink=drink, method=method, kid=kid, helper=helper)

    build_scene(world, kid, helper, setting, pitcher, drink)
    world.para()
    warning(world, helper, kid, pitcher, setting)
    if method.id == "ignore":
        carry_unsafe(world, kid, pitcher)
        world.para()
        spill(world, pitcher_ent, pitcher, drink)
        alarm(world, helper, kid, pitcher)
        lesson(world, helper, kid, pitcher)
        world.say("They sat together after that, slower and wiser, with the fresh drink shared in small cups.")
        outcome = "cautionary"
    else:
        if method.id == "listen":
            world.say(f"{kid.id} listened right away and set the pitcher down.")
        else:
            carry_unsafe(world, kid, pitcher)
            world.say(f"But this time {kid.id} used the {method.label} and kept both hands on the {pitcher.label}.")
        world.para()
        safe_choice(world, helper, kid, method, pitcher, drink)
        lesson(world, helper, kid, pitcher)
        world.say("At the end, everyone laughed softly, and the pitcher sat steady in the middle of the table.")
        outcome = "heartwarming"
    world.facts["outcome"] = outcome
    return world


SETTINGS = {
    "kitchen": Setting(id="kitchen", place="the kitchen", light="the sunny window", mood="warm and busy", table="kitchen table", spill_spot="the edge"),
    "porch": Setting(id="porch", place="the porch", light="the afternoon light", mood="quiet and golden", table="small porch table", spill_spot="the railing"),
    "grandma": Setting(id="grandma", place="Grandma’s house", light="the lace-curtained window", mood="soft and cozy", table="tea table", spill_spot="the front of the table"),
}

PITCHERS = {
    "glass": PitcherKind(id="glass", label="glass pitcher", material="glass", heavy=True, fragile=True, spill_risk=2, theme="careful hands", tags={"pitcher", "glass"}),
    "ceramic": PitcherKind(id="ceramic", label="ceramic pitcher", material="ceramic", heavy=True, fragile=False, spill_risk=2, theme="steady hands", tags={"pitcher", "ceramic"}),
}

DRINKS = {
    "lemonade": Drink(id="lemonade", label="lemonade", color="yellow", tags={"drink", "sweet"}),
    "juice": Drink(id="juice", label="apple juice", color="golden", tags={"drink", "sweet"}),
}

METHODS = {
    "tray": SafeMethod(id="tray", label="tray", sense=3, safety=3, text="carry it on a tray with two careful hands", fail="could not keep it steady", qa_text="carried it on a tray with two careful hands", tags={"safe"}),
    "both_hands": SafeMethod(id="both_hands", label="two hands", sense=3, safety=3, text="hold the pitcher with both hands and walk slowly", fail="lost balance", qa_text="held the pitcher with both hands and walked slowly", tags={"safe"}),
    "listen": SafeMethod(id="listen", label="listening", sense=3, safety=3, text="set it down and ask for help", fail="did not help", qa_text="set it down and asked for help", tags={"safe"}),
    "ignore": SafeMethod(id="ignore", label="one hand", sense=1, safety=0, text="do it that way", fail="was too late to help", qa_text="did not choose a safe way", tags={"unsafe"}),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe"]
BOY_NAMES = ["Theo", "Ben", "Eli", "Finn", "Max"]
TRAITS = ["careful", "kind", "curious", "gentle", "thoughtful"]


@dataclass
class StoryParams:
    setting: str
    pitcher: str
    drink: str
    method: str
    kid: str
    kid_gender: str
    helper: str
    helper_gender: str
    trait: str = "kind"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PITCHERS:
            for d in DRINKS:
                for m in METHODS:
                    if is_reasonable(PITCHERS[p], METHODS[m]):
                        combos.append((s, p, d, m))
    return combos


def explain_rejection(pitcher: PitcherKind, method: SafeMethod) -> str:
    if method.sense < SENSE_MIN:
        return f"(No story: '{method.id}' is too unsafe for a gentle storyworld.)"
    return "(No story: this combination does not support a meaningful pitcher warning.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small cautionary, heartwarming pitcher storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--pitcher", choices=PITCHERS)
    ap.add_argument("--drink", choices=DRINKS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--kid")
    ap.add_argument("--kid-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_rejection(PITCHERS[args.pitcher] if args.pitcher else next(iter(PITCHERS.values())), METHODS[args.method]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.pitcher is None or c[1] == args.pitcher)
              and (args.drink is None or c[2] == args.drink)
              and (args.method is None or c[3] == args.method)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, pitcher, drink, method = rng.choice(sorted(combos))
    pitcher_cfg = PITCHERS[pitcher]
    kid_gender = args.kid_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    kid = args.kid or rng.choice(GIRL_NAMES if kid_gender == "girl" else BOY_NAMES)
    helper = args.helper or ("Mom" if helper_gender == "girl" else "Dad")
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, pitcher=pitcher, drink=drink, method=method, kid=kid, kid_gender=kid_gender, helper=helper, helper_gender=helper_gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.pitcher not in PITCHERS or params.drink not in DRINKS or params.method not in METHODS:
        raise StoryError("Invalid parameters.")
    world = tell(SETTINGS[params.setting], PITCHERS[params.pitcher], DRINKS[params.drink], METHODS[params.method], params.kid, params.kid_gender, params.helper, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming but cautionary story for a 3-to-5-year-old that includes the word "pitcher" and shows a child learning to carry it safely.',
        f"Tell a gentle family story where {f['kid'].id} worries about a pitcher on the table and learns a safer way to pour drinks.",
        f"Write a short story about a child, a pitcher, and a careful warning that ends with everyone feeling warm and safe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid = f["kid"]
    helper = f["helper"]
    pitcher = f["pitcher"]
    method = f["method"]
    qa = [
        ("Who is the story about?", f"It is about {kid.id} and {helper.id}, who are trying to serve drinks together."),
        ("Why did the helper warn the child?", f"{helper.id} warned {kid.id} because the {pitcher.label} could slip or break if it was carried the wrong way. The helper wanted the drink to stay in the pitcher and the floor to stay dry."),
    ]
    if f.get("outcome") == "cautionary":
        qa.append(("What happened when the child ignored the warning?", f"The pitcher tipped, the drink spilled, and the fragile one broke. After that, everyone had to slow down and clean up before trying again."))
    else:
        qa.append(("How did they solve the problem?", f"They used {method.qa_text} instead. That kept the {pitcher.label} steady and let them share the drink without a spill."))
        qa.append(("How did the ending feel?", f"It felt warm and happy because the child listened, the helper smiled, and the pitcher stayed safe on the table."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["pitcher"].tags) | set(world.facts["drink"].tags) | set(world.facts["method"].tags)
    out = []
    if "pitcher" in tags:
        out.append(("What is a pitcher?", "A pitcher is a container with a handle and a spout that people use to pour drinks. Some pitchers are fragile, so they need careful hands."))
    if "glass" in tags:
        out.append(("Why can a glass pitcher be dangerous?", "A glass pitcher can break if it falls. Broken glass can hurt hands, so it is better to carry it slowly and carefully."))
    if "safe" in tags:
        out.append(("Why is a tray useful?", "A tray helps keep things balanced while you carry them. It gives the pitcher a steadier place to ride."))
    if "sweet" in tags:
        out.append(("Why do people share lemonade or juice?", "People share drinks at the table because it is a kind way to enjoy something together. It can make a family moment feel cheerful."))
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.fragile:
            bits.append("fragile")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,D,M) :- setting(S), pitcher(P), drink(D), method(M), sense(M,SN), sense_min(Min), SN >= Min.
"""
# separate names: sense(M,SN) fact uses method id and score

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PITCHERS.items():
        lines.append(asp.fact("pitcher", pid))
        if p.fragile:
            lines.append(asp.fact("fragile", pid))
        lines.append(asp.fact("spill_risk", pid, p.spill_risk))
    for did in DRINKS:
        lines.append(asp.fact("drink", did))
    for mid, m in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, m.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, pitcher=None, drink=None, method=None, kid=None, kid_gender=None, helper=None, helper_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"FAIL: generation smoke test crashed: {e}")
        rc = 1
    return rc


CURATED = [
    StoryParams(setting="kitchen", pitcher="glass", drink="lemonade", method="tray", kid="Mia", kid_gender="girl", helper="Mom", helper_gender="girl", trait="kind"),
    StoryParams(setting="porch", pitcher="ceramic", drink="juice", method="both_hands", kid="Theo", kid_gender="boy", helper="Dad", helper_gender="boy", trait="careful"),
    StoryParams(setting="grandma", pitcher="glass", drink="juice", method="ignore", kid="Ava", kid_gender="girl", helper="Grandma", helper_gender="girl", trait="curious"),
]


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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a heartwarming cautionary story that includes the word "pitcher".',
        'Tell a child-sized story about a pitcher on a table, a warning, and a safer way to share drinks.',
        'Write a gentle story where a child learns to respect a pitcher and avoid a spill.',
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["pitcher"].tags) | set(world.facts["method"].tags)
    out = []
    if "pitcher" in tags:
        out.append(("What is a pitcher?", "A pitcher is a container used for pouring drinks. It often has a handle and a spout."))
    if "safe" in tags:
        out.append(("Why do careful hands matter?", "Careful hands help stop slips and spills. That keeps the drink where it belongs and helps everyone stay calm."))
    if "unsafe" in tags:
        out.append(("Why is a one-handed carry risky?", "A one-handed carry can wobble. If the pitcher falls, the drink can spill and the pitcher can break."))
    return out


if __name__ == "__main__":
    main()
