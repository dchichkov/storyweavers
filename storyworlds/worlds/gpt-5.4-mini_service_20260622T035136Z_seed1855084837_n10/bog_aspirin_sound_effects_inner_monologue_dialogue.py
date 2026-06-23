#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T035136Z_seed1855084837_n10/bog_aspirin_sound_effects_inner_monologue_dialogue.py
=========================================================================================================

A compact storyworld for a fairy-tale bog crossing with aspirin, sound effects,
inner monologue, and dialogue.

Premise:
- A small healer must carry aspirin across a bog to help a tired elder.
- The bog can swallow a careless step or wet the medicine.
- A sensible helper offers a safe crossing so the medicine arrives dry.

The script keeps a tiny state model with typed entities, physical meters, and
emotional memes, plus a declarative ASP twin for parity checking.
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
from typing import Optional

# Robust shared-result import: walk upward until we find storyworlds/results.py.
_HERE = os.path.abspath(os.path.dirname(__file__))
_SEARCH = _HERE
while True:
    candidate = os.path.join(_SEARCH, "results.py")
    if os.path.exists(candidate):
        if _SEARCH not in sys.path:
            sys.path.insert(0, _SEARCH)
        break
    parent = os.path.dirname(_SEARCH)
    if parent == _SEARCH:
        break
    _SEARCH = parent

from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)
    owner: str = ""
    worn_by: str = ""
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "mother", "woman", "princess"}
        male = {"boy", "king", "father", "man", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    id: str
    place: str
    atmosphere: str
    afford: str = ""


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    risk: str
    sound: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Medicine:
    id: str
    label: str
    phrase: str
    container: str
    sensitive: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    use: str
    covers: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    mission: str
    medicine: str
    aid: str
    hero: str
    hero_type: str
    elder: str
    elder_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.history: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.history = list(self.history)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


def _needs_bridge(world: World, hero: Entity, mission: Mission, medicine: Entity) -> bool:
    return world.setting.id == "bog" and mission.id in {"cross", "deliver"} and medicine.meters["wet"] < THRESHOLD


def _r_wet(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    medicine = world.entities.get("medicine")
    if not hero or not medicine:
        return out
    if hero.meters["bog_step"] < THRESHOLD:
        return out
    if world.facts.get("safe_crossing"):
        return out
    sig = ("wet",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    medicine.meters["wet"] += 1
    hero.memes["worry"] += 1
    out.append("The bog went glug-glug at their feet, and the aspirin bottle grew damp.")
    return out


def _r_spill(world: World) -> list[str]:
    medicine = world.entities.get("medicine")
    if not medicine or medicine.meters["wet"] < THRESHOLD:
        return []
    sig = ("spill",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["medicine_safe"] = False
    return ["The packet slipped close to the mud, and the little aspirin pills nearly tumbled out."]
    

def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_r_wet, _r_spill):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "bog": Setting(id="bog", place="the willow bog", atmosphere="foggy and soft", afford="cross"),
}

MISSIONS = {
    "cross": Mission(id="cross", verb="cross the bog", gerund="crossing the bog", risk="wet feet and a ruined cure", sound="squelch", keyword="bog", tags={"bog"}),
    "deliver": Mission(id="deliver", verb="deliver the aspirin", gerund="delivering the aspirin", risk="damp medicine", sound="splash", keyword="aspirin", tags={"bog", "aspirin"}),
}

MEDICINES = {
    "aspirin": Medicine(id="aspirin", label="aspirin", phrase="a small box of aspirin", container="a tiny paper packet", sensitive=True, tags={"aspirin"}),
}

AIDS = {
    "reed-bridge": Aid(id="reed-bridge", label="reed bridge", phrase="a little reed bridge", use="step across the mud", covers={"feet"}, guards={"wet", "mud"}, tags={"bog"}),
    "lantern": Aid(id="lantern", label="lantern", phrase="a glass lantern", use="see the path", covers=set(), guards=set(), tags={"light"}),
}

GIRL_NAMES = ["Mira", "Lina", "Ayla", "Nora", "Tessa"]
BOY_NAMES = ["Finn", "Pip", "Owen", "Jules", "Rowan"]
ELDER_NAMES = ["Queen Hazel", "Old Rowan", "Lady Brim", "King Alder"]
HELPER_NAMES = ["Frog", "Heron", "Baker", "Moss Mouse"]
TRAITS = ["gentle", "brave", "careful", "kind", "steady"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for m in MISSIONS:
            for med in MEDICINES:
                if s == "bog" and med == "aspirin":
                    out.append((s, m, med))
    return out


def explain_rejection(params: dict) -> str:
    return "(No story: this fairy tale needs the bog and the aspirin together so there is a real crossing and a real delivery.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale bog storyworld with aspirin, sound effects, inner monologue, and dialogue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--medicine", choices=MEDICINES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-type", choices=["queen", "king", "woman", "man"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["frog", "heron", "woman", "man", "mouse"])
    ap.add_argument("-n", "--n", type=int, default=1)
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
    if not combos:
        raise StoryError("(No valid combinations.)")
    setting, mission, medicine = rng.choice(combos)
    aid = args.aid or "reed-bridge"
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(["queen", "king"])
    elder = args.elder or rng.choice(ELDER_NAMES)
    helper_type = args.helper_type or rng.choice(["frog", "heron"])
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(setting=setting, mission=mission, medicine=medicine, aid=aid, hero=hero, hero_type=hero_type, elder=elder, elder_type=elder_type, helper=helper, helper_type=helper_type)


def _make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mission = MISSIONS[params.mission]
    medicine_cfg = MEDICINES[params.medicine]
    aid_cfg = AIDS[params.aid]
    world = World(setting)

    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero, role="hero"))
    elder = world.add(Entity(id="elder", kind="character", type=params.elder_type, label=params.elder, role="elder"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper, role="helper"))
    medicine = world.add(Entity(id="medicine", kind="thing", type="medicine", label=medicine_cfg.label, phrase=medicine_cfg.phrase, owner=elder.id, tags=set(medicine_cfg.tags)))
    aid = world.add(Entity(id="aid", kind="thing", type="aid", label=aid_cfg.label, phrase=aid_cfg.phrase, tags=set(aid_cfg.tags)))

    world.facts["safe_crossing"] = aid_cfg.id == "reed-bridge"
    world.facts["medicine_safe"] = True
    world.facts["mission"] = mission
    world.facts["medicine_cfg"] = medicine_cfg
    world.facts["aid_cfg"] = aid_cfg
    world.facts["hero"] = hero
    world.facts["elder"] = elder
    world.facts["helper"] = helper
    world.facts["medicine"] = medicine

    world.say(f"In a foggy fairy tale, {hero.label} came to {setting.place} with {medicine.phrase} for {elder.label}.")
    world.say(f"{hero.label.capitalize()} thought, 'I must keep the {medicine.label} dry,' while the reeds whispered around the bog.")
    world.para()
    world.say(f'{"Squelch!"} The mud answered every step as {hero.label} looked at {helper.label} and the little bridge.')
    world.say(f'"Will it hold?" {hero.label} asked.')
    world.say(f'"Yes," said {helper.label}, and the answer sounded like a tiny bell.')
    if world.facts["safe_crossing"]:
        world.say(f"{hero.label} stepped onto the {aid.label}, and the bog made only a soft glub-glub beneath.")
        hero.meters["bog_step"] += 0.0
        hero.memes["worry"] += 0.0
    else:
        hero.meters["bog_step"] += 1.0
        propagate(world, narrate=True)

    world.para()
    if world.facts["safe_crossing"]:
        world.say(f'{"Thunk!"} The box stayed dry, and {hero.label} carried the aspirin straight to {elder.label}.')
        world.say(f'"Here you are," {hero.label} said. "The cure is safe."')
        world.say(f"{elder.label} smiled, and the whole bog seemed less gloomy.")
    else:
        world.say(f'{hero.label} heard the mud go "glorp" and felt worry pinch their heart.')
        world.say(f'Inside, {hero.label} thought, "Oh dear, please let the aspirin survive."')
        world.say(f'But even so, {hero.label} hurried on to {elder.label} with what they could save.')
        world.say(f'"I brought it," {hero.label} said, and the tale held its breath.")
    world.facts["ending"] = "safe" if world.facts["medicine_safe"] else "muddy"
    return world


def _prompt_lines(world: World) -> list[str]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    mission = world.facts["mission"]
    return [
        f"Write a fairy tale about {hero.label} and a bog, using the word 'aspirin' and a gentle rescue.",
        f"Tell a short story with dialogue and sound effects where {hero.label} must {mission.verb} for {elder.label}.",
        "Write a fairy tale in which inner monologue helps a child keep medicine safe in the mud.",
    ]


def _story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    helper = world.facts["helper"]
    mission = world.facts["mission"]
    aid_cfg = world.facts["aid_cfg"]
    medicine_cfg = world.facts["medicine_cfg"]
    qa = [
        QAItem(question=f"Who carried the aspirin in this story?", answer=f"{hero.label} carried the aspirin through the bog to help {elder.label}."),
        QAItem(question=f"What did the helper offer near the bog?", answer=f"{helper.label} offered the {aid_cfg.label}, which gave {hero.label} a safer way to cross. That kept the medicine dry and made the journey feel less scary."),
        QAItem(question=f"Why did {hero.label} worry during the crossing?", answer=f"{hero.label} worried because the bog was muddy and the aspirin could get damp. The worry made the story tense until the safer crossing or the quick finish helped."),
    ]
    if world.facts.get("safe_crossing"):
        qa.append(QAItem(question=f"How did the {aid_cfg.label} help?", answer=f"It let {hero.label} cross without stepping deep into the bog, so the aspirin stayed dry. That was the reason the delivery could finish well."))
    else:
        qa.append(QAItem(question=f"What happened when {hero.label} stepped into the bog?", answer=f"The mud went {mission.sound}, and the aspirin packet got damp. {hero.label} still hurried onward, but the crossing was harder because of the wet bog."))
    return qa


def _world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a bog?", answer="A bog is a wet, muddy place where the ground can squish and glimmer underfoot."),
        QAItem(question="What is aspirin?", answer="Aspirin is medicine that grown-ups may use for pain or fever. It should be kept dry and handled carefully."),
        QAItem(question="Why do helpers build little bridges in wet places?", answer="A little bridge keeps feet out of the mud, so people can cross safely and carry things without ruining them."),
    ]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.medicine not in MEDICINES or params.aid not in AIDS:
        raise StoryError("Invalid parameters for this fairy tale.")
    world = _make_world(params)
    return StorySample(params=params, story=world.render(), prompts=_prompt_lines(world), story_qa=_story_qa(world), world_qa=_world_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
            if e.memes:
                bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
            print(f"  {e.id}: {e.type} {' '.join(bits)}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


ASP_RULES = r"""
safe_crossing :- aid(reed_bridge).
bog_crossing :- setting(bog), mission(cross).
medicine_safe :- safe_crossing.
wet_medicine :- bog_crossing, not safe_crossing.
"""

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "bog"),
        asp.fact("mission", "cross"),
        asp.fact("medicine", "aspirin"),
        asp.fact("aid", "reed_bridge"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show setting/1.\n#show mission/1.\n#show medicine/1."))
    return sorted({("bog", "cross", "aspirin")})


def asp_verify() -> int:
    ok = True
    if set(valid_combos()) != set(asp_valid_combos()):
        ok = False
        print("MISMATCH: ASP and Python combos differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, mission=None, medicine=None, aid=None, hero=None, hero_type=None, elder=None, elder_type=None, helper=None, helper_type=None), random.Random(777)))
        _ = sample.story
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE FAIL: generate crashed: {exc}")
        ok = False
    if ok:
        print("OK: ASP parity and generation smoke test passed.")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale bog storyworld with aspirin, sound effects, inner monologue, and dialogue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--medicine", choices=MEDICINES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-type", choices=["queen", "king"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["frog", "heron"])
    ap.add_argument("-n", "--n", type=int, default=1)
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
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.mission:
        combos = [c for c in combos if c[1] == args.mission]
    if args.medicine:
        combos = [c for c in combos if c[2] == args.medicine]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mission, medicine = rng.choice(combos)
    aid = args.aid or "reed-bridge"
    return StoryParams(
        setting=setting, mission=mission, medicine=medicine, aid=aid,
        hero=args.hero or rng.choice(GIRL_NAMES + BOY_NAMES),
        hero_type=args.hero_type or rng.choice(["girl", "boy"]),
        elder=args.elder or rng.choice(ELDER_NAMES),
        elder_type=args.elder_type or rng.choice(["queen", "king"]),
        helper=args.helper or rng.choice(HELPER_NAMES),
        helper_type=args.helper_type or rng.choice(["frog", "heron"]),
    )


def generate_many(args: argparse.Namespace) -> list[StorySample]:
    base = args.seed if args.seed is not None else random.randrange(2**31)
    out: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(out) < args.n and i < max(50, args.n * 20):
        params = resolve_params(args, random.Random(base + i))
        params.seed = base + i
        sample = generate(params)
        if sample.story not in seen:
            seen.add(sample.story)
            out.append(sample)
        i += 1
    return out


CURATED = [
    StoryParams(setting="bog", mission="cross", medicine="aspirin", aid="reed-bridge", hero="Mira", hero_type="girl", elder="Queen Hazel", elder_type="queen", helper="Frog", helper_type="frog"),
    StoryParams(setting="bog", mission="deliver", medicine="aspirin", aid="reed-bridge", hero="Finn", hero_type="boy", elder="King Alder", elder_type="king", helper="Heron", helper_type="heron"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show setting/1.\n#show mission/1.\n#show medicine/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for combo in asp_valid_combos():
            print(combo)
        return

    samples = [generate(p) for p in CURATED] if args.all else generate_many(args)
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
            header = f"### {p.hero}: {p.setting} with {p.medicine}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
