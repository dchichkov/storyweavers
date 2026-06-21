#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/assure_ornery_whinny_curiosity_suspense_cautionary_fable.py
===========================================================================================

A small fable-like storyworld about an inquisitive child, an ornery pony, and a
careful lesson. The story uses a tiny simulated world with meters for physical
state and memes for emotional state, produces grounded QA, and supports an inline
ASP twin for parity checking.

Seed words and tone:
- assure
- ornery
- whinny
- Curiosity
- Suspense
- Cautionary
- Fable
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class StoryParams:
    setting: str
    child: str
    child_gender: str
    pony: str
    pony_color: str
    adult: str
    bait: str
    warning: str
    soothe: str
    outcome: str = "safe"
    seed: Optional[int] = None


@dataclass
class Setting:
    id: str
    place: str
    features: set[str] = field(default_factory=set)


@dataclass
class CharacterSpec:
    id: str
    gender: str
    kind: str
    label: str
    traits: set[str] = field(default_factory=set)


@dataclass
class PonySpec:
    id: str
    color: str
    label: str
    ornery: bool = True


@dataclass
class TreatSpec:
    id: str
    label: str
    smell: str
    attracts: set[str] = field(default_factory=set)


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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


SETTINGS = {
    "barnyard": Setting(id="barnyard", place="a little barnyard", features={"hay", "curiosity"}),
    "orchard": Setting(id="orchard", place="an apple orchard", features={"fruit", "curiosity"}),
    "lane": Setting(id="lane", place="a quiet country lane", features={"dust", "curiosity"}),
}

CHILDREN = {
    "Mina": CharacterSpec(id="Mina", gender="girl", kind="character", label="the child", traits={"curious"}),
    "Toby": CharacterSpec(id="Toby", gender="boy", kind="character", label="the child", traits={"curious"}),
    "June": CharacterSpec(id="June", gender="girl", kind="character", label="the child", traits={"thoughtful"}),
}

PONIES = {
    "Pip": PonySpec(id="Pip", color="gray", label="the pony", ornery=True),
    "Brindle": PonySpec(id="Brindle", color="brown", label="the pony", ornery=True),
    "Moss": PonySpec(id="Moss", color="black", label="the pony", ornery=False),
}

TREATS = {
    "apple": TreatSpec(id="apple", label="an apple slice", smell="sweet", attracts={"pony"}),
    "carrot": TreatSpec(id="carrot", label="a carrot stick", smell="bright", attracts={"pony"}),
}

ACTIONS = {"talk", "touch", "offer"}
RESPONSES = {"calm", "patient", "loud"}


def hazard_possible(pony: PonySpec, treat: TreatSpec) -> bool:
    return pony.ornery and "pony" in treat.attracts


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for p in PONIES:
            for t in TREATS:
                if hazard_possible(PONIES[p], TREATS[t]):
                    out.append((s, p, t))
    return out


def reason_rejection(pony: PonySpec, treat: TreatSpec) -> str:
    return (
        f"(No story: {pony.label_word if hasattr(pony, 'label_word') else pony.label} "
        f"must be ornery enough for suspense, and {treat.label} must tempt the pony.)"
    )


def choose_child(rng: random.Random) -> CharacterSpec:
    return CHILDREN[rng.choice(list(CHILDREN.keys()))]


def choose_action(rng: random.Random) -> str:
    return rng.choice(sorted(ACTIONS))


def choose_response(rng: random.Random) -> str:
    return rng.choice(sorted(RESPONSES))


def predict_whinny(world: World, pony_id: str) -> bool:
    sim = world.copy()
    sim.get(pony_id).memes["suspense"] += 1
    return sim.get(pony_id).memes["suspense"] >= THRESHOLD


def _r_whinny(world: World) -> list[str]:
    pony = world.get("pony")
    if pony.meters["teased"] < THRESHOLD:
        return []
    sig = ("whinny",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pony.meters["whinny"] += 1
    pony.memes["alarm"] += 1
    return ["__whinny__"]


def _r_calm(world: World) -> list[str]:
    pony = world.get("pony")
    child = world.get("child")
    if child.memes["assured"] < THRESHOLD or pony.memes["alarm"] < THRESHOLD:
        return []
    sig = ("calm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pony.memes["calmer"] += 1
    return ["__calm__"]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    lines: list[str] = []
    while changed:
        changed = False
        for rule in (_r_whinny, _r_calm):
            out = rule(world)
            if out:
                changed = True
                lines.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for line in lines:
            world.say(line)


def tell(setting: Setting, child: CharacterSpec, pony: PonySpec, treat: TreatSpec,
         adult_name: str, soothe: str, action: str) -> World:
    world = World()
    c = world.add(Entity(id=child.id, kind="character", type=child.gender, role="child",
                         label="the child", traits=sorted(child.traits)))
    p = world.add(Entity(id="pony", kind="character", type="thing", role="pony",
                         label="the pony", traits=["ornery"] if pony.ornery else []))
    a = world.add(Entity(id=adult_name, kind="character", type="adult", role="adult",
                         label="the adult", traits=["calm"]))
    world.add(Entity(id="treat", kind="thing", type="thing", label=treat.label))
    c.memes["curiosity"] += 1
    c.memes["suspense"] += 1
    p.memes["ornery"] += 1 if pony.ornery else 0

    world.say(
        f"Once in {setting.place}, {c.id} met {pony.label} named {pony.id}, and "
        f"the pony gave a small whinny from the pen."
    )
    world.say(
        f"{c.id} loved Curiosity and leaned closer, because the treat smelled {treat.smell}."
    )
    world.para()
    world.say(
        f"{c.id} tried to {action} {treat.label} and said, \"I will be careful.\""
    )
    if predict_whinny(world, "pony"):
        world.say(
            f"The pony's ears flicked back, and the suspense grew as the pony turned ornery."
        )
    if action == "offer":
        c.meters["teased"] += 1
    elif action == "touch":
        c.meters["teased"] += 1
    else:
        c.meters["teased"] += 1
    propagate(world, narrate=False)
    if world.get("pony").meters["whinny"] >= THRESHOLD:
        world.say(
            f"The pony tossed its head and let out an ornery whinny, loud as a little trumpet."
        )
    if action != "talk":
        world.para()
    world.say(
        f"{c.id} looked at {a.id} and asked for help."
    )
    c.memes["assured"] += 1
    world.say(
        f"{a.id} smiled and said, \"I assure you, a kind voice works better than a quick hand.\""
    )
    if soothe == "calm":
        world.say(f"{a.id} stood by the gate and spoke softly until the pony settled.")
    elif soothe == "patient":
        world.say(f"{a.id} waited with patient hands, and the pony stopped tossing its mane.")
    else:
        world.say(f"{a.id} used a loud shout, which only made the pony stomp and snort.")
    if soothe in {"calm", "patient"}:
        world.get("pony").memes["calmer"] += 1
        world.get("pony").meters["whinny"] = 0.0
        world.say(
            f"In the end, the pony took the treat gently, and {c.id} learned that caution and kindness make the safest path."
        )
    else:
        world.say(
            f"That day ended with a lesson: an ornery creature listens best to calm care, not noisy haste."
        )
    world.facts.update(setting=setting, child=c, pony=world.get("pony"), adult=a,
                        treat=treat, soothe=soothe, action=action,
                        outcome="safe" if soothe in {"calm", "patient"} else "scary")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for a child that includes the words "assure", "ornery", and "whinny".',
        f"Tell a cautionary story where {f['child'].id} meets an ornery pony in {f['setting'].place} and learns to be patient.",
        f"Write a suspenseful fable about curiosity and a pony that whinnies, ending with a calm lesson from an adult.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, pony, adult, treat = f["child"], f["pony"], f["adult"], f["treat"]
    soothe = f["soothe"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id}, {pony.id} the pony, and {adult.id} the adult. The story follows {child.id}'s curiosity and the pony's stubborn mood."
        ),
        QAItem(
            question="Why did the pony whinny?",
            answer=f"The pony whinnied because the child came too close with a tempting treat and the pony was ornery. That made the moment suspenseful until the adult stepped in."
        ),
        QAItem(
            question="How did the adult help?",
            answer=f"{adult.id} spoke calmly and said it was best to use care instead of rushing. That gentle approach settled the pony and gave the child a safer way to act."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean when a pony whinnies?",
            answer="A whinny is a pony's voice. It can mean the pony is calling out, excited, or uneasy."
        ),
        QAItem(
            question="What does ornery mean?",
            answer="Ornery means stubborn, grumpy, or hard to please. An ornery animal may not want to cooperate right away."
        ),
        QAItem(
            question="What does it mean to assure someone?",
            answer="To assure someone is to tell them something kindly and clearly so they feel safe or confident. It is a comforting promise."
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
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="barnyard",
        child="Mina",
        child_gender="girl",
        pony="Pip",
        pony_color="gray",
        adult="Grandma",
        bait="apple",
        warning="calm",
        soothe="calm",
    ),
    StoryParams(
        setting="orchard",
        child="Toby",
        child_gender="boy",
        pony="Brindle",
        pony_color="brown",
        adult="Uncle",
        bait="carrot",
        warning="patient",
        soothe="patient",
    ),
    StoryParams(
        setting="lane",
        child="June",
        child_gender="girl",
        pony="Pip",
        pony_color="gray",
        adult="Father",
        bait="apple",
        warning="calm",
        soothe="loud",
    ),
]


def valid_story(params: StoryParams) -> bool:
    if params.setting not in SETTINGS or params.child not in CHILDREN or params.pony not in PONIES or params.bait not in TREATS:
        return False
    return hazard_possible(PONIES[params.pony], TREATS[params.bait])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.pony and args.bait:
        if not hazard_possible(PONIES[args.pony], TREATS[args.bait]):
            raise StoryError("This pony and treat combination is too calm for a fable; pick an ornery pony and a tempting treat.")
    combos = [c for c in valid_combos()
              if args.setting is None or c[0] == args.setting
              and (args.pony is None or c[1] == args.pony)
              and (args.bait is None or c[2] == args.bait)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, pony, bait = rng.choice(sorted(combos))
    child = args.child or rng.choice(list(CHILDREN.keys()))
    adult = args.adult or rng.choice(["Mother", "Father", "Grandmother", "Uncle"])
    warning = rng.choice(sorted(RESPONSES))
    soothe = args.soothe or rng.choice(["calm", "patient"])
    return StoryParams(
        setting=setting,
        child=child,
        child_gender=CHILDREN[child].gender,
        pony=pony,
        pony_color=PONIES[pony].color,
        adult=adult,
        bait=bait,
        warning=warning,
        soothe=soothe,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.child not in CHILDREN:
        raise StoryError(f"Unknown child: {params.child}")
    if params.pony not in PONIES:
        raise StoryError(f"Unknown pony: {params.pony}")
    if params.bait not in TREATS:
        raise StoryError(f"Unknown treat: {params.bait}")
    if not valid_story(params):
        raise StoryError("These choices do not create a tense fable.")
    world = tell(
        SETTINGS[params.setting],
        CHILDREN[params.child],
        PONIES[params.pony],
        TREATS[params.bait],
        params.adult,
        params.soothe,
        action="offer",
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


ASP_RULES = r"""
ornery_pony(P) :- pony(P), ornery(P).
tempting_treat(T) :- treat(T), attracts_pony(T).
hazard(P, T) :- ornery_pony(P), tempting_treat(T).
valid(S, P, T) :- setting(S), hazard(P, T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PONIES.items():
        lines.append(asp.fact("pony", pid))
        if p.ornery:
            lines.append(asp.fact("ornery", pid))
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat", tid))
        if "pony" in t.attracts:
            lines.append(asp.fact("attracts_pony", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print(" only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print(" only in Python:", sorted(python_set - clingo_set))
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small cautionary fable about curiosity and an ornery pony.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--pony", choices=PONIES)
    ap.add_argument("--bait", choices=TREATS)
    ap.add_argument("--soothe", choices=["calm", "patient", "loud"])
    ap.add_argument("--adult")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, p, t in combos:
            print(f"  {s:10} {p:8} {t}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
