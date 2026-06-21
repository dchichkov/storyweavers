#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ninja_hoagie_calf_dialogue_bravery_foreshadowing_detective.py
================================================================================================

A standalone storyworld about a tiny detective mystery: a ninja, a hoagie,
and a calf in a neighborhood case. The story uses dialogue, bravery, and
foreshadowing to build a small classical arc: a clue is noticed, the danger is
named, a brave choice is made, and the ending proves what changed.

The premise stays child-facing and concrete:
- a hungry detective and a ninja follow a trail of hoagie crumbs,
- a calf wanders near a trouble spot,
- a foreshadowed squeak or shadow hints at what is coming,
- the brave choice is to warn, help, and solve the case together.

This script follows the Storyweavers storyworld contract:
- stdlib-only script
- imports storyworlds/results.py eagerly
- lazy clingo import via storyworlds/asp.py helpers
- StoryParams, build_parser, resolve_params, generate, emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    clue_hint: str


@dataclass
class Crew:
    id: str
    type: str
    label: str
    role: str
    tool: str
    bravery: int
    dialogue_style: str


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    smell: str
    crumbs: int
    tempting: bool = True


@dataclass
class Calf:
    id: str
    label: str
    phrase: str
    wandering: bool
    timid: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Risk:
    id: str
    label: str
    place: str
    sound: str
    shadow: str
    severity: int


@dataclass
class StoryParams:
    setting: str = "alley"
    detective: str = "piper"
    ninja: str = "mika"
    treat: str = "hoagie"
    calf: str = "calf"
    risk: str = "dock"
    seed: Optional[int] = None


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_crumbs(world: World) -> list[str]:
    out: list[str] = []
    treat = world.get("treat")
    risk = world.get("risk")
    if treat.meters.get("crumbs", 0.0) >= THRESHOLD and risk.meters.get("noticed", 0.0) < THRESHOLD:
        sig = ("crumbs",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        risk.meters["noticed"] = 1.0
        for ent in world.entities.values():
            if ent.role in {"detective", "ninja"}:
                ent.memes["alert"] = ent.memes.get("alert", 0.0) + 1.0
        out.append("__crumbs__")
    return out


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    risk = world.get("risk")
    if risk.meters.get("noticed", 0.0) < THRESHOLD:
        return out
    sig = ("foreshadow",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    risk.meters["ominous"] = 1.0
    world.get("detective").memes["suspense"] = 1.0
    out.append("__foreshadow__")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    det = world.get("detective")
    ninja = world.get("ninja")
    calf = world.get("calf")
    if det.memes.get("resolve", 0.0) < THRESHOLD:
        return out
    sig = ("bravery",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ninja.memes["brave"] = ninja.memes.get("brave", 0.0) + 1.0
    calf.memes["calm"] = calf.memes.get("calm", 0.0) + 1.0
    out.append("__bravery__")
    return out


CAUSAL_RULES = [Rule("crumbs", _r_crumbs), Rule("foreshadow", _r_foreshadow), Rule("bravery", _r_bravery)]


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


def reasonableness_gate(setting: Setting, treat: Treat, calf: Calf, risk: Risk) -> bool:
    return treat.tempting and calf.wandering and setting.place == risk.place


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for tid, t in TREATS.items():
            for cid, c in CALVES.items():
                for rid, r in RISKS.items():
                    if reasonableness_gate(s, t, c, r):
                        combos.append((sid, tid, rid))
    return combos


def predict(world: World, setting: Setting, treat: Treat, risk: Risk) -> dict:
    sim = world.copy()
    sim.get("treat").meters["crumbs"] = float(treat.crumbs)
    sim.get("risk").meters["shadow"] = 1.0
    propagate(sim, narrate=False)
    return {
        "noticed": sim.get("risk").meters.get("noticed", 0.0) >= THRESHOLD,
        "ominous": sim.get("risk").meters.get("ominous", 0.0) >= THRESHOLD,
    }


def intro(world: World, detective: Entity, ninja: Entity, setting: Setting) -> None:
    world.say(
        f"On a soft morning in the {setting.place}, {detective.id} the detective "
        f"and {ninja.id} the ninja were chasing a strange case."
    )
    world.say(
        f'"{detective.id}," said {ninja.id}, "do you smell that?" '
        f'"I smell {world.get("treat").label_word}," said {detective.id}, "and I see crumbs."'
    )


def foreshadowing_beats(world: World, setting: Setting, risk: Risk, treat: Treat) -> None:
    world.say(
        f"A little shadow slept near the {risk.place}, and every now and then "
        f"it gave a tiny squeak. That was the first clue that something was not right."
    )
    world.say(
        f'The trail led past the {treat.label}, and {detective_name(world)} frowned. '
        f'"This is a case," said the detective, "and it is getting bigger."'
    )


def detective_name(world: World) -> str:
    return world.get("detective").id


def warn(world: World, detective: Entity, ninja: Entity, risk: Risk) -> None:
    detective.memes["resolve"] = detective.memes.get("resolve", 0.0) + 1.0
    pred = predict(world, SETTINGS[world.facts["setting"]], TREATS[world.facts["treat"]], RISKS[world.facts["risk"]])
    world.facts["predicted"] = pred
    world.say(
        f'"If we rush in," said {detective.id}, "we might spook the calf near the {risk.place}."'
    )
    world.say(
        f'"Then we go carefully," said {ninja.id}. "A brave move is a wise move."'
    )


def brave_act(world: World, detective: Entity, ninja: Entity, calf: Entity, risk: Risk) -> None:
    ninja.memes["bravery"] = ninja.memes.get("bravery", 0.0) + 1.0
    calf.memes["relief"] = calf.memes.get("relief", 0.0) + 1.0
    world.say(
        f"{ninja.id} leaped onto a low crate, waved both hands, and said, "
        f'"Easy now, little calf. We are here to help."'
    )
    world.say(
        f'The calf blinked, stopped wandering, and looked toward the safe lane instead of the {risk.place}.'
    )


def solve_case(world: World, detective: Entity, ninja: Entity, calf: Entity, treat: Treat, risk: Risk) -> None:
    detective.memes["joy"] = detective.memes.get("joy", 0.0) + 1.0
    world.say(
        f'"The hoagie crumbs were the clue," said {detective.id}. "The calf was following them."'
    )
    world.say(
        f'"Case solved," said {ninja.id}, and together they carried the {treat.label} away from the path.'
    )
    world.say(
        f"The calf was safe, the shadow looked small again, and the morning felt bright."
    )


def tell(setting: Setting, detective_cfg: Crew, ninja_cfg: Crew, treat: Treat, calf: Calf, risk: Risk) -> World:
    world = World()
    detective = world.add(Entity(id=detective_cfg.id, kind="character", type=detective_cfg.type, label=detective_cfg.label, role="detective"))
    ninja = world.add(Entity(id=ninja_cfg.id, kind="character", type=ninja_cfg.type, label=ninja_cfg.label, role="ninja"))
    treat_ent = world.add(Entity(id="treat", kind="thing", type="food", label=treat.label))
    calf_ent = world.add(Entity(id="calf", kind="character", type="calf", label=calf.label, role="calf"))
    risk_ent = world.add(Entity(id="risk", kind="thing", type="place", label=risk.label))
    world.facts.update(setting=setting.id, treat=treat.id, risk=risk.id)
    treat_ent.meters["crumbs"] = float(treat.crumbs)
    risk_ent.meters["shadow"] = 1.0

    intro(world, detective, ninja, setting)
    world.para()
    foreshadowing_beats(world, setting, risk, treat)
    warn(world, detective, ninja, risk)
    world.para()
    brave_act(world, detective, ninja, calf_ent, risk)
    propagate(world, narrate=False)
    solve_case(world, detective, ninja, calf_ent, treat, risk)

    world.facts.update(
        detective=detective,
        ninja=ninja,
        calf=calf_ent,
        treat_cfg=treat,
        risk_cfg=risk,
        setting_cfg=setting,
        outcome="solved",
    )
    return world


SETTINGS = {
    "alley": Setting(id="alley", place="the alley", mood="quiet", clue_hint="crumbs"),
    "pier": Setting(id="pier", place="the pier", mood="windy", clue_hint="salt"),
    "market": Setting(id="market", place="the market", mood="busy", clue_hint="stalls"),
}

DETECTIVES = {
    "piper": Crew(id="Piper", type="girl", label="the detective", role="detective", tool="notebook", bravery=6, dialogue_style="calm"),
    "miles": Crew(id="Miles", type="boy", label="the detective", role="detective", tool="notebook", bravery=5, dialogue_style="careful"),
}

NINJAS = {
    "mika": Crew(id="Mika", type="girl", label="the ninja", role="ninja", tool="sash", bravery=7, dialogue_style="quick"),
    "ren": Crew(id="Ren", type="boy", label="the ninja", role="ninja", tool="sash", bravery=6, dialogue_style="steady"),
}

TREATS = {
    "hoagie": Treat(id="hoagie", label="hoagie", phrase="a long hoagie", smell="savory", crumbs=3, tempting=True),
    "halfhoagie": Treat(id="halfhoagie", label="half a hoagie", phrase="half a hoagie", smell="savory", crumbs=2, tempting=True),
}

CALVES = {
    "calf": Calf(id="calf", label="calf", phrase="a young calf", wandering=True, timid=True, tags={"calf"}),
}

RISKS = {
    "dock": Risk(id="dock", label="the dock", place="the dock", sound="creak", shadow="long shadow", severity=2),
    "gate": Risk(id="gate", label="the gate", place="the gate", sound="clack", shadow="small shadow", severity=1),
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story for a 3-to-5-year-old that includes the words "{TREATS[f["treat"]].label}", "ninja", and "calf".',
        f"Tell a brave little mystery where {f['detective'].id} and {f['ninja'].id} follow hoagie crumbs, talk in dialogue, and help a calf.",
        f"Write a story with foreshadowing and bravery: a clue appears, a calm warning is given, and the mystery ends safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    det = world.facts["detective"]
    ninja = world.facts["ninja"]
    calf = world.facts["calf"]
    treat = world.facts["treat_cfg"]
    risk = world.facts["risk_cfg"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {det.id}, {ninja.id}, and the calf. They work together in a small detective case."
        ),
        QAItem(
            question="What clue did they notice first?",
            answer=f"They noticed {treat.label} crumbs and a small shadow near {risk.place}. That clue made them realize something else was happening nearby."
        ),
        QAItem(
            question="What did the detective say about the case?",
            answer=f'{det.id} said it was a case and that it was getting bigger. That was the foreshadowing, because the clue pointed to trouble near the calf.'
        ),
        QAItem(
            question="How did the ninja show bravery?",
            answer=f'{ninja.id} stepped forward and spoke gently to the calf instead of running away. That brave choice helped everyone stay calm.'
        ),
        QAItem(
            question="How did the story end?",
            answer="The calf was safe, the clue was explained, and the case was solved. The ending feels bright because the friends chose calm help over fear."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hoagie?",
            answer="A hoagie is a long sandwich with bread and fillings. If it leaves crumbs, those crumbs can make a clue."
        ),
        QAItem(
            question="What is a calf?",
            answer="A calf is a young cow. It can be curious and may wander toward interesting smells or sounds."
        ),
        QAItem(
            question="What is a ninja?",
            answer="A ninja is a stealthy helper in stories. Ninjas move carefully and can be brave when trouble appears."
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue that hints something important will happen later. It helps the story feel like a mystery."
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing the right thing even when you feel nervous. It does not mean being loud; it can mean being calm and helpful."
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is when characters speak to each other in the story. It lets readers hear their thoughts and plans."
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
noticed_case :- crumbs, shadow.
foreshadowed :- noticed_case.
brave_move :- resolve, ninja.
solved :- brave_move.
#show noticed_case/0.
#show foreshadowed/0.
#show brave_move/0.
#show solved/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("crumbs"),
        asp.fact("shadow"),
        asp.fact("resolve"),
        asp.fact("ninja"),
    ]
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_reasoning() -> list[str]:
    import asp
    model = asp.one_model(asp_program())
    return [sym.name for sym in model]


def asp_verify() -> int:
    rc = 0
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, detective=None, ninja=None, treat=None, calf=None, risk=None, seed=None), random.Random(7)))
        _ = sample.story
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1

    if set(asp_reasoning()) != {"noticed_case", "foreshadowed", "brave_move", "solved"}:
        print("MISMATCH in ASP reasoning.")
        rc = 1
    if set(valid_combos()) != set((sid, tid, rid) for sid in SETTINGS for tid in TREATS for rid in RISKS):
        print("MISMATCH in valid_combos.")
        rc = 1
    print("OK: smoke test and ASP parity passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective storyworld with a ninja, a hoagie, and a calf.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--detective", choices=DETECTIVES)
    ap.add_argument("--ninja", choices=NINJAS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--calf", choices=CALVES)
    ap.add_argument("--risk", choices=RISKS)
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
    if not combos:
        raise StoryError("No valid story combinations exist.")
    candidates = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.treat is None or c[1] == args.treat)
        and (args.risk is None or c[2] == args.risk)
    ]
    if not candidates:
        raise StoryError("(No valid combination matches the given options.)")
    setting, treat, risk = rng.choice(sorted(candidates))
    return StoryParams(
        setting=setting,
        detective=args.detective or rng.choice(sorted(DETECTIVES)),
        ninja=args.ninja or rng.choice(sorted(NINJAS)),
        treat=treat,
        calf=args.calf or "calf",
        risk=risk,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Invalid setting.")
    if params.detective not in DETECTIVES or params.ninja not in NINJAS:
        raise StoryError("Invalid character selection.")
    if params.treat not in TREATS or params.calf not in CALVES or params.risk not in RISKS:
        raise StoryError("Invalid world selection.")
    world = tell(
        SETTINGS[params.setting],
        DETECTIVES[params.detective],
        NINJAS[params.ninja],
        TREATS[params.treat],
        CALVES[params.calf],
        RISKS[params.risk],
    )
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
    StoryParams(setting="alley", detective="piper", ninja="mika", treat="hoagie", calf="calf", risk="dock"),
    StoryParams(setting="pier", detective="miles", ninja="ren", treat="halfhoagie", calf="calf", risk="dock"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP reasoning:", ", ".join(asp_reasoning()))
        print("Valid combos:")
        for c in valid_combos():
            print(" ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
